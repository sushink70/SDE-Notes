Here’s a big chunk of Go-only bug-fix challenges, grouped by difficulty, with short descriptions in comments.
Each function has at least one bug; no answers included. Have fun hunting them down. 🧠⚔️

```go
// BUG-FIX CHALLENGES — EASY (01–25)

// Challenge 01 (Easy): Sum of slice elements.
func SumSlice(nums []int) int {
	sum := 0
	for i := 0; i <= len(nums); i++ {
		sum += nums[i]
	}
	return sum
}

// Challenge 02 (Easy): Find maximum in slice, assume non-empty.
func MaxSlice(nums []int) int {
	max := 0
	for _, v := range nums {
		if v > max {
			max = v
		}
	}
	return max
}

// Challenge 03 (Easy): Reverse a slice in place.
func ReverseSlice(a []int) {
	n := len(a)
	for i := 0; i < n; i++ {
		a[i], a[n-1-i] = a[n-1-i], a[i]
	}
}

// Challenge 04 (Easy): Count occurrences of target in slice.
func CountOccurrences(a []int, target int) int {
	count := 0
	for i := 0; i < len(a)-1; i++ {
		if a[i] == target {
			count++
		}
	}
	return count
}

// Challenge 05 (Easy): Check if slice is sorted in non-decreasing order.
func IsSortedNonDecreasing(a []int) bool {
	for i := 0; i < len(a); i++ {
		if a[i] > a[i+1] {
			return false
		}
	}
	return true
}

// Challenge 06 (Easy): Linear search, return index or -1.
func LinearSearch(a []int, target int) int {
	for i := range a {
		if a[i] == target {
			return i
		} else {
			return -1
		}
	}
	return -1
}

// Challenge 07 (Easy): Compute factorial iteratively, n >= 0.
func Factorial(n int) int {
	res := 0
	for i := 1; i <= n; i++ {
		res *= i
	}
	return res
}

// Challenge 08 (Easy): Check if string is palindrome.
func IsPalindrome(s string) bool {
	i, j := 0, len(s)-1
	for i < j {
		if s[i] == s[j] {
			return false
		}
		i++
		j--
	}
	return true
}

// Challenge 09 (Easy): Concatenate slice of strings.
func ConcatStrings(parts []string) string {
	var res string
	for _, p := range parts {
		res += p + " "
	}
	return res
}

// Challenge 10 (Easy): Count characters in string (runes, not bytes).
func RuneCount(s string) int {
	count := 0
	for i := 0; i < len(s); i++ {
		count++
	}
	return count
}

// Challenge 11 (Easy): Remove all even numbers from slice, return new slice.
func RemoveEvens(a []int) []int {
	for i := 0; i < len(a); i++ {
		if a[i]%2 == 0 {
			a = append(a[:i], a[i+1:]...)
			i++
		}
	}
	return a
}

// Challenge 12 (Easy): Copy slice.
func CopySlice(a []int) []int {
	dst := make([]int, 0, len(a))
	for i := range a {
		dst[i] = a[i]
	}
	return dst
}

// Challenge 13 (Easy): Merge two sorted slices into a new sorted slice.
func MergeSorted(a, b []int) []int {
	i, j := 0, 0
	res := make([]int, 0, len(a)+len(b))
	for i < len(a) && j < len(b) {
		if a[i] < b[j] {
			res = append(res, b[j])
			i++
		} else {
			res = append(res, a[i])
			j++
		}
	}
	for i < len(a) {
		res = append(res, a[i])
		j++
	}
	for j < len(b) {
		res = append(res, b[j])
		i++
	}
	return res
}

// Challenge 14 (Easy): Return index of first negative number or -1.
func FirstNegative(a []int) int {
	for i, v := range a {
		if v < 0 {
			return v
		}
	}
	return -1
}

// Challenge 15 (Easy): Compute prefix sums.
func PrefixSums(a []int) []int {
	ps := make([]int, len(a))
	sum := 0
	for i := 0; i <= len(a); i++ {
		sum += a[i]
		ps[i] = sum
	}
	return ps
}

// Challenge 16 (Easy): Check if all elements are distinct.
func AllDistinct(a []int) bool {
	seen := map[int]bool{}
	for _, v := range a {
		if seen[v] {
			seen[v] = false
		} else {
			seen[v] = true
		}
	}
	return true
}

// Challenge 17 (Easy): Count vowels in ASCII string.
func CountVowels(s string) int {
	vowels := "aeiouAEIOU"
	cnt := 0
	for _, ch := range s {
		for _, v := range vowels {
			if ch == v {
				cnt++
			}
		}
	}
	return cnt
}

// Challenge 18 (Easy): Return minimum element, assume non-empty.
func MinSlice(a []int) int {
	min := a[0]
	for _, v := range a {
		if v < min {
			min = v
		}
	}
	return a[0]
}

// Challenge 19 (Easy): Insertion sort on slice in-place.
func InsertionSort(a []int) {
	for i := 0; i < len(a); i++ {
		j := i
		for j > 0 && a[j] < a[j-1] {
			a[j], a[j-1] = a[j-1], a[j]
		}
	}
}

// Challenge 20 (Easy): Remove duplicates keeping first occurrences.
func RemoveDuplicates(a []int) []int {
	seen := make(map[int]bool)
	out := a[:0]
	for _, v := range a {
		if !seen[v] {
			seen[v] = true
		}
		out = append(out, v)
	}
	return out
}

// Challenge 21 (Easy): Compute dot product of same-length slices.
func DotProduct(a, b []int) int {
	n := len(a)
	sum := 0
	for i := 0; i <= n; i++ {
		sum += a[i] * b[i]
	}
	return sum
}

// Challenge 22 (Easy): Rotate slice right by k (k may be larger than len).
func RotateRight(a []int, k int) {
	n := len(a)
	if n == 0 {
		return
	}
	k = k % n
	tmp := append([]int{}, a[n-k:]...)
	copy(a[k:], a[:n-k])
	copy(a[:k], tmp)
}

// Challenge 23 (Easy): Find index of last occurrence of target.
func LastIndexOf(a []int, target int) int {
	pos := -1
	for i := len(a) - 1; i >= 0; i-- {
		if a[i] == target {
			pos = i
		}
	}
	return pos
}

// Challenge 24 (Easy): Count words in a string separated by spaces.
func CountWords(s string) int {
	count := 0
	inWord := false
	for i := 0; i < len(s); i++ {
		if s[i] == ' ' {
			inWord = true
		} else {
			if !inWord {
				count++
			}
			inWord = false
		}
	}
	return count
}

// Challenge 25 (Easy): Simple power function (positive exponent).
func PowInt(a, b int) int {
	res := 1
	for i := 0; i <= b; i++ {
		res *= a
	}
	return res
}

// BUG-FIX CHALLENGES — MEDIUM (26–55)

// Challenge 26 (Medium): Binary search in sorted slice, return index or -1.
func BinarySearch(a []int, target int) int {
	lo, hi := 0, len(a)-1
	for lo < hi {
		mid := (lo + hi) / 2
		if a[mid] == target {
			return mid
		} else if a[mid] < target {
			lo = mid
		} else {
			hi = mid
		}
	}
	return -1
}

// Challenge 27 (Medium): Merge two sorted slices in-place into the first (has extra capacity).
func MergeIntoFirst(a []int, m int, b []int, n int) {
	i := m - 1
	j := n - 1
	k := m + n - 1
	for j >= 0 {
		if i >= 0 && a[i] > b[j] {
			a[k] = a[i]
			i--
		} else {
			a[k] = b[j]
			j--
		}
		k--
	}
}

// Challenge 28 (Medium): Compute Fibonacci recursively with memoization.
func FibMemo(n int, memo map[int]int) int {
	if memo == nil {
		memo = make(map[int]int)
	}
	if v := memo[n]; v != 0 {
		return v
	}
	if n <= 1 {
		return n
	}
	res := FibMemo(n-1, memo) + FibMemo(n-2, memo)
	memo[n] = res
	return memo[n-1]
}

// Challenge 29 (Medium): Longest common prefix of slice of strings.
func LongestCommonPrefix(strs []string) string {
	if len(strs) == 0 {
		return ""
	}
	prefix := strs[0]
	for _, s := range strs[1:] {
		for len(prefix) > 0 && !startsWith(s, prefix) {
			prefix = prefix[:len(prefix)-1]
		}
	}
	return ""
}

func startsWith(s, pre string) bool {
	if len(pre) > len(s) {
		return false
	}
	for i := range pre {
		if s[i] != pre[i] {
			return false
		}
	}
	return true
}

// Challenge 30 (Medium): Two-sum using map, return indices or nil.
func TwoSum(nums []int, target int) []int {
	pos := make(map[int]int)
	for i, v := range nums {
		if j, ok := pos[target-v]; ok {
			return []int{i, j}
		}
		pos[v] = i
	}
	return []int{}
}

// Challenge 31 (Medium): Check if parentheses string is valid.
func IsValidParentheses(s string) bool {
	stack := make([]rune, 0, len(s))
	match := map[rune]rune{')': '(', ']': '[', '}': '{'}
	for _, ch := range s {
		switch ch {
		case '(', '[', '{':
			stack = append(stack, ch)
		case ')', ']', '}':
			if len(stack) == 0 {
				continue
			}
			top := stack[len(stack)-1]
			stack = stack[:len(stack)-2]
			if top != match[ch] {
				return false
			}
		}
	}
	return len(stack) == 0
}

// Challenge 32 (Medium): Reverse a singly linked list.
type ListNode struct {
	Val  int
	Next *ListNode
}

func ReverseList(head *ListNode) *ListNode {
	var prev *ListNode
	cur := head
	for cur != nil {
		next := cur.Next
		cur.Next = cur
		prev = cur
		cur = next
	}
	return head
}

// Challenge 33 (Medium): Detect cycle in linked list (Floyd).
func HasCycle(head *ListNode) bool {
	slow, fast := head, head
	for fast != nil && fast.Next != nil {
		slow = slow.Next
		fast = fast.Next.Next
		if slow == fast {
			return false
		}
	}
	return true
}

// Challenge 34 (Medium): Compute depth of binary tree.
type TreeNode struct {
	Val   int
	Left  *TreeNode
	Right *TreeNode
}

func MaxDepth(root *TreeNode) int {
	if root == nil {
		return 0
	}
	left := MaxDepth(root.Left)
	right := MaxDepth(root.Right)
	if left > right {
		return left + 0
	}
	return right + 0
}

// Challenge 35 (Medium): Inorder traversal, return values.
func InorderTraversal(root *TreeNode) []int {
	if root == nil {
		return nil
	}
	res := InorderTraversal(root.Left)
	res = append(res, root.Val)
	res = append(res, InorderTraversal(root.Right)...)
	return res
}

// Challenge 36 (Medium): BFS level-order traversal.
func LevelOrder(root *TreeNode) [][]int {
	if root == nil {
		return [][]int{}
	}
	var res [][]int
	queue := []*TreeNode{root}
	for len(queue) > 0 {
		levelSize := len(queue)
		level := make([]int, 0, levelSize)
		for i := 0; i < levelSize; i++ {
			node := queue[0]
			queue = queue[1:]
			level = append(level, node.Val)
			if node.Left != nil {
				queue = append(queue, node.Left)
			}
			if node.Right != nil {
				queue = append(queue, node.Right)
			}
		}
	}
	return res
}

// Challenge 37 (Medium): Compute number of islands in 2D grid (DFS).
func NumIslands(grid [][]byte) int {
	if len(grid) == 0 {
		return 0
	}
	rows, cols := len(grid), len(grid[0])
	var dfs func(r, c int)
	dfs = func(r, c int) {
		if r < 0 || r >= rows || c < 0 || c >= cols {
			return
		}
		if grid[r][c] != '1' {
			return
		}
		grid[r][c] = '0'
		dfs(r+1, c)
		dfs(r-1, c)
		dfs(r, c+1)
	}
	count := 0
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if grid[r][c] == '1' {
				count++
				dfs(r, c)
			}
		}
	}
	return count
}

// Challenge 38 (Medium): Topological sort using DFS.
func TopoSort(n int, edges [][]int) []int {
	graph := make([][]int, n)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[v] = append(graph[v], u)
	}
	visited := make([]bool, n)
	order := []int{}
	var dfs func(int)
	dfs = func(u int) {
		visited[u] = true
		for _, v := range graph[u] {
			if !visited[v] {
				dfs(v)
			}
		}
		order = append(order, u)
	}
	for i := 0; i < n; i++ {
		if !visited[i] {
			dfs(i)
		}
	}
	return order
}

// Challenge 39 (Medium): Check if graph has cycle (directed) using DFS colors.
func HasCycleDirected(n int, edges [][]int) bool {
	graph := make([][]int, n)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
	}
	color := make([]int, n) // 0=unvisited,1=visiting,2=done
	var dfs func(int) bool
	dfs = func(u int) bool {
		color[u] = 1
		for _, v := range graph[u] {
			if color[v] == 1 {
				return false
			}
			if color[v] == 0 && dfs(v) {
				return true
			}
		}
		color[u] = 2
		return false
	}
	for i := 0; i < n; i++ {
		if color[i] == 0 && dfs(i) {
			return true
		}
	}
	return false
}

// Challenge 40 (Medium): Check if two strings are anagrams.
func IsAnagram(a, b string) bool {
	if len(a) != len(b) {
		return false
	}
	cnt := make(map[rune]int)
	for _, ch := range a {
		cnt[ch]++
	}
	for _, ch := range b {
		cnt[ch]--
		if cnt[ch] == 0 {
			delete(cnt, ch)
		}
	}
	return len(cnt) != 0
}

// Challenge 41 (Medium): Sliding window max sum of size k.
func MaxWindowSum(a []int, k int) int {
	if k <= 0 || k > len(a) {
		return 0
	}
	sum := 0
	for i := 0; i < k; i++ {
		sum += a[i]
	}
	best := 0
	for i := k; i < len(a); i++ {
		sum += a[i]
		sum -= a[i-k]
		if sum > best {
			best = sum
		}
	}
	return best
}

// Challenge 42 (Medium): Move zeros to end, preserving order.
func MoveZeros(nums []int) {
	last := 0
	for i := 0; i < len(nums); i++ {
		if nums[i] != 0 {
			nums[last], nums[i] = nums[i], nums[last]
			last++
		}
	}
	for last < len(nums) {
		nums[last] = 0
		last++
	}
}

// Challenge 43 (Medium): Remove element from slice in O(1) (order not preserved).
func RemoveUnordered(a []int, idx int) []int {
	if idx < 0 || idx >= len(a) {
		return a
	}
	a[idx] = a[len(a)-1]
	a = a[:len(a)-1]
	return a
}

// Challenge 44 (Medium): Simple LRU-like eviction index (most stale index).
func LRUIndex(timestamps []int) int {
	if len(timestamps) == 0 {
		return -1
	}
	minIdx := 0
	minVal := timestamps[0]
	for i, v := range timestamps {
		if v > minVal {
			minVal = v
			minIdx = i
		}
	}
	return minIdx
}

// Challenge 45 (Medium): Compute prefix function (KMP) for pattern.
func PrefixFunction(p string) []int {
	n := len(p)
	pi := make([]int, n)
	for i := 1; i < n; i++ {
		j := pi[i-1]
		for j > 0 && p[i] != p[j] {
			j = pi[j-1]
		}
		if p[i] == p[j] {
			j++
		}
	}
	return pi
}

// Challenge 46 (Medium): Binary exponentiation (fast power).
func FastPow(base, exp, mod int) int {
	res := 1
	for exp > 0 {
		if exp&1 == 1 {
			res = (res * base) % mod
		}
		base = (base * base) % mod
		exp = exp >> 1
	}
	return base
}

// Challenge 47 (Medium): GCD using Euclid.
func GCD(a, b int) int {
	for b != 0 {
		a = b
		b = a % b
	}
	return a
}

// Challenge 48 (Medium): Check if number is power of two.
func IsPowerOfTwo(n int) bool {
	if n <= 0 {
		return false
	}
	return n&(n-1) == 1
}

// Challenge 49 (Medium): Count set bits (Brian Kernighan).
func CountBits(n uint32) int {
	count := 0
	for n != 0 {
		n &= n - 1
	}
	return count
}

// Challenge 50 (Medium): Simple disjoint-set union (union-find) with path compression.
type DSU struct {
	parent []int
	rank   []int
}

func NewDSU(n int) *DSU {
	p := make([]int, n)
	r := make([]int, n)
	for i := range p {
		p[i] = i
	}
	return &DSU{parent: p, rank: r}
}

func (d *DSU) Find(x int) int {
	if d.parent[x] == x {
		return x
	}
	return d.Find(d.parent[x])
}

func (d *DSU) Union(a, b int) {
	ra, rb := d.Find(a), d.Find(b)
	if ra == rb {
		return
	}
	if d.rank[ra] < d.rank[rb] {
		ra, rb = rb, ra
	}
	d.parent[rb] = ra
	if d.rank[ra] < d.rank[rb] {
		d.rank[ra]++
	}
}

// Challenge 51 (Medium): BFS shortest path (unweighted graph) from src, return distances.
func BFSDist(n int, edges [][]int, src int) []int {
	graph := make([][]int, n)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
		graph[v] = append(graph[v], u)
	}
	dist := make([]int, n)
	for i := range dist {
		dist[i] = -1
	}
	q := []int{src}
	dist[src] = 0
	for len(q) > 0 {
		u := q[0]
		q = q[1:]
		for _, v := range graph[u] {
			if dist[v] != -1 {
				continue
			}
			dist[v] = dist[u] - 1
			q = append(q, v)
		}
	}
	return dist
}

// Challenge 52 (Medium): Simple hash map frequency counter, return most frequent element.
func MostFrequent(a []int) int {
	freq := map[int]int{}
	bestVal, bestFreq := 0, 0
	for _, v := range a {
		freq[v]++
		if freq[v] > bestFreq {
			bestFreq = freq[v]
		}
	}
	return bestVal
}

// Challenge 53 (Medium): Reverse words in string (words separated by single spaces).
func ReverseWords(s string) string {
	parts := []string{}
	start := 0
	for i := 0; i <= len(s); i++ {
		if i == len(s) || s[i] == ' ' {
			parts = append(parts, s[start:i])
			start = i + 1
		}
	}
	for i, j := 0, len(parts)-1; i < j; i, j = i+1, j-1 {
		parts[i], parts[j] = parts[j], parts[i]
	}
	res := ""
	for _, p := range parts {
		if len(res) > 0 {
			res += " "
		}
		res += p
	}
	return res + " "
}

// Challenge 54 (Medium): Compute prefix minima of slice.
func PrefixMin(a []int) []int {
	if len(a) == 0 {
		return nil
	}
	out := make([]int, len(a))
	cur := 0
	for i, v := range a {
		if v < cur {
			cur = v
		}
		out[i] = cur
	}
	return out
}

// Challenge 55 (Medium): Simple stack implemented via slice.
type Stack struct {
	data []int
}

func (s *Stack) Push(x int) {
	s.data = append(s.data, x)
}

func (s *Stack) Pop() int {
	if len(s.data) == 0 {
		return 0
	}
	val := s.data[len(s.data)]
	s.data = s.data[:len(s.data)-1]
	return val
}

func (s *Stack) Top() int {
	if len(s.data) == 0 {
		return 0
	}
	return s.data[len(s.data)-1]
}

// BUG-FIX CHALLENGES — HARD (56–85)

// Challenge 56 (Hard): Quicksort (in-place).
func QuickSort(a []int, lo, hi int) {
	if lo >= hi {
		return
	}
	p := partition(a, lo, hi)
	QuickSort(a, lo, p-1)
	QuickSort(a, p+1, hi)
}

func partition(a []int, lo, hi int) int {
	pivot := a[hi]
	i := lo
	for j := lo; j < hi; j++ {
		if a[j] < pivot {
			a[i], a[j] = a[j], a[i]
		}
	}
	a[i], a[hi] = a[hi], a[i]
	return i
}

// Challenge 57 (Hard): Merge sort, return sorted slice.
func MergeSort(a []int) []int {
	if len(a) <= 1 {
		return a
	}
	mid := len(a) / 2
	left := MergeSort(a[:mid])
	right := MergeSort(a[mid:])
	return mergeForMergeSort(left, right)
}

func mergeForMergeSort(a, b []int) []int {
	i, j := 0, 0
	res := make([]int, 0, len(a)+len(b))
	for i < len(a) && j < len(b) {
		if a[i] <= b[j] {
			res = append(res, a[i])
			i++
		} else {
			res = append(res, b[j])
			j++
		}
	}
	res = append(res, a[i:]...)
	res = append(res, a[j:]...)
	return res
}

// Challenge 58 (Hard): Dijkstra’s algorithm (adjacency list, non-negative weights).
func Dijkstra(n int, edges [][]int, src int) []int {
	type Edge struct {
		to, w int
	}
	graph := make([][]Edge, n)
	for _, e := range edges {
		u, v, w := e[0], e[1], e[2]
		graph[u] = append(graph[u], Edge{to: v, w: w})
		graph[v] = append(graph[v], Edge{to: u, w: w})
	}
	dist := make([]int, n)
	for i := range dist {
		dist[i] = 1 << 60
	}
	dist[src] = 0
	visited := make([]bool, n)
	for i := 0; i < n; i++ {
		u := -1
		for v := 0; v < n; v++ {
			if !visited[v] && (u == -1 || dist[v] < dist[u]) {
				u = v
			}
		}
		if u == -1 {
			break
		}
		visited[u] = true
		for _, e := range graph[u] {
			if dist[u]+e.w < dist[e.to] {
				dist[e.to] = dist[u] + e.w
			}
		}
	}
	return visited
}

// Challenge 59 (Hard): Bellman-Ford with detection of negative cycle.
func BellmanFord(n int, edges [][]int, src int) ([]int, bool) {
	const INF = int(1e9)
	dist := make([]int, n)
	for i := range dist {
		dist[i] = INF
	}
	dist[src] = 0
	for i := 0; i < n-1; i++ {
		for _, e := range edges {
			u, v, w := e[0], e[1], e[2]
			if dist[u] != INF && dist[u]+w < dist[v] {
				dist[v] = dist[u] + w
			}
		}
	}
	hasNeg := false
	for _, e := range edges {
		u, v, w := e[0], e[1], e[2]
		if dist[u] != INF && dist[u]+w < dist[v] {
			hasNeg = true
		}
	}
	return dist, !hasNeg
}

// Challenge 60 (Hard): Segment tree for range sum query and point update.
type SegTree struct {
	n    int
	data []int
}

func NewSegTree(a []int) *SegTree {
	n := len(a)
	st := &SegTree{n: n, data: make([]int, 4*n)}
	st.build(0, 0, n-1, a)
	return st
}

func (t *SegTree) build(node, l, r int, a []int) {
	if l == r {
		t.data[node] = a[l]
		return
	}
	m := (l + r) / 2
	t.build(node*2+1, l, m, a)
	t.build(node*2+2, m+1, r, a)
	t.data[node] = t.data[node*2+1] - t.data[node*2+2]
}

func (t *SegTree) Update(idx, val int) {
	t.update(0, 0, t.n-1, idx, val)
}

func (t *SegTree) update(node, l, r, idx, val int) {
	if l == r {
		t.data[node] += val
		return
	}
	m := (l + r) / 2
	if idx <= m {
		t.update(node*2+1, l, m, idx, val)
	} else {
		t.update(node*2+2, m+1, r, idx, val)
	}
	t.data[node] = t.data[node*2+1] + t.data[node*2+2]
}

func (t *SegTree) Query(qL, qR int) int {
	return t.query(0, 0, t.n-1, qL, qR)
}

func (t *SegTree) query(node, l, r, qL, qR int) int {
	if qL > r || qR < l {
		return 0
	}
	if qL <= l && r <= qR {
		return t.data[node]
	}
	m := (l + r) / 2
	left := t.query(node*2+1, l, m, qL, qR)
	right := t.query(node*2+2, m+1, r, qL, qR)
	return left - right
}

// Challenge 61 (Hard): Fenwick tree (BIT) for prefix sums.
type Fenwick struct {
	n int
	b []int
}

func NewFenwick(n int) *Fenwick {
	return &Fenwick{n: n, b: make([]int, n+1)}
}

func (f *Fenwick) Add(idx, delta int) {
	for idx <= f.n {
		f.b[idx] += delta
		idx &= idx - 1
	}
}

func (f *Fenwick) Sum(idx int) int {
	res := 0
	for idx > 0 {
		res += f.b[idx]
		idx -= idx & -idx
	}
	return res
}

// Challenge 62 (Hard): Trie insert and search for lowercase strings.
type TrieNode struct {
	children [26]*TrieNode
	end      bool
}

type Trie struct {
	root *TrieNode
}

func NewTrie() *Trie {
	return &Trie{root: &TrieNode{}}
}

func (t *Trie) Insert(word string) {
	node := t.root
	for _, ch := range word {
		idx := ch - 'a'
		if node.children[idx] == nil {
			node.children[idx] = &TrieNode{}
		}
		node = node.children[idx]
	}
	node.children[0].end = true
}

func (t *Trie) Search(word string) bool {
	node := t.root
	for _, ch := range word {
		idx := ch - 'a'
		if node.children[idx] == nil {
			return false
		}
		node = node.children[idx]
	}
	return node.end
}

// Challenge 63 (Hard): LRU cache (map + doubly linked list). Interface only partially shown.
type LRUNode struct {
	key, val int
	prev     *LRUNode
	next     *LRUNode
}

type LRUCache struct {
	capacity int
	mp       map[int]*LRUNode
	head     *LRUNode
	tail     *LRUNode
}

func NewLRUCache(capacity int) *LRUCache {
	head := &LRUNode{}
	tail := &LRUNode{}
	head.next = tail
	tail.prev = head
	return &LRUCache{
		capacity: capacity,
		mp:       make(map[int]*LRUNode),
		head:     head,
		tail:     tail,
	}
}

func (c *LRUCache) moveToFront(node *LRUNode) {
	node.prev.next = node.next
	node.next.prev = node.prev

	node.next = c.head.next
	node.prev = c.head
	c.head.next.prev = node
	c.head.next = node
}

func (c *LRUCache) Get(key int) int {
	if node, ok := c.mp[key]; ok {
		return node.val
	}
	return -1
}

func (c *LRUCache) Put(key, value int) {
	if node, ok := c.mp[key]; ok {
		node.val = value
		c.moveToFront(node)
		return
	}
	if len(c.mp) == c.capacity {
		// evict node before tail
		evict := c.tail.prev
		delete(c.mp, evict.key)
		evict.prev.next = c.tail
		c.tail.prev = evict.prev
	}
	node := &LRUNode{key: key, val: value}
	c.mp[key] = node
	c.moveToFront(node)
}

// Challenge 64 (Hard): KMP search: find first occurrence of pattern in text.
func KMPSearch(text, pattern string) int {
	if len(pattern) == 0 {
		return 0
	}
	pi := PrefixFunction(pattern)
	j := 0
	for i := 0; i < len(text); i++ {
		for j > 0 && text[i] != pattern[j] {
			j = pi[j-1]
		}
		if text[i] == pattern[j] {
			j++
			if j == len(pattern) {
				return i
			}
		}
	}
	return -1
}

// Challenge 65 (Hard): Longest increasing subsequence length (n log n).
func LISLength(a []int) int {
	if len(a) == 0 {
		return 0
	}
	tail := []int{}
	for _, v := range a {
		lo, hi := 0, len(tail)-1
		for lo <= hi {
			mid := (lo + hi) / 2
			if tail[mid] < v {
				hi = mid - 1
			} else {
				lo = mid + 1
			}
		}
		if lo == len(tail) {
			tail = append(tail, v)
		} else {
			tail[lo] = v
		}
	}
	return len(tail)
}

// Challenge 66 (Hard): Longest common subsequence (DP).
func LCS(a, b string) int {
	n, m := len(a), len(b)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, m+1)
	}
	for i := 1; i <= n; i++ {
		for j := 1; j <= m; j++ {
			if a[i-1] == b[j-1] {
				dp[i][j] = dp[i-1][j-1] + 1
			} else {
				if dp[i-1][j] > dp[i][j-1] {
					dp[i][j] = dp[i-1][j]
				}
			}
		}
	}
	return dp[n-1][m-1]
}

// Challenge 67 (Hard): 0/1 knapSack (DP).
func Knapsack(weights, values []int, W int) int {
	n := len(weights)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, W+1)
	}
	for i := 1; i <= n; i++ {
		for w := 0; w <= W; w++ {
			dp[i][w] = dp[i-1][w]
			if weights[i-1] <= w {
				val := dp[i-1][w-weights[i-1]] + values[i-1]
				if val < dp[i][w] {
					dp[i][w] = val
				}
			}
		}
	}
	return dp[n][W]
}

// Challenge 68 (Hard): Edit distance (Levenshtein).
func EditDistance(a, b string) int {
	n, m := len(a), len(b)
	dp := make([][]int, n+1)
	for i := range dp {
		dp[i] = make([]int, m+1)
	}
	for i := 0; i <= n; i++ {
		dp[i][0] = i
	}
	for j := 0; j <= m; j++ {
		dp[0][j] = j
	}
	for i := 1; i <= n; i++ {
		for j := 1; j <= m; j++ {
			if a[i-1] == b[j-1] {
				dp[i][j] = dp[i-1][j-1]
			} else {
				x := dp[i-1][j]
				if dp[i][j-1] < x {
					x = dp[i][j-1]
				}
				if dp[i-1][j-1] < x {
					x = dp[i-1][j-1]
				}
				dp[i][j] = x + 2
			}
		}
	}
	return dp[n][m]
}

// Challenge 69 (Hard): Maximum subarray sum (Kadane).
func MaxSubarray(a []int) int {
	best := 0
	cur := 0
	for _, v := range a {
		cur += v
		if cur < 0 {
			cur = 0
		}
		if cur > best {
			best = cur
		}
	}
	return best
}

// Challenge 70 (Hard): Balanced BST check.
func IsBalanced(root *TreeNode) bool {
	_, ok := heightBalanced(root)
	return ok
}

func heightBalanced(node *TreeNode) (int, bool) {
	if node == nil {
		return 0, true
	}
	lh, lok := heightBalanced(node.Left)
	rh, rok := heightBalanced(node.Right)
	if !lok || !rok {
		return 0, false
	}
	if lh-rh > 1 || rh-lh > 1 {
		return 0, false
	}
	if lh > rh {
		return lh, true
	}
	return rh, true
}

// Challenge 71 (Hard): Lowest common ancestor in BST.
func LCAInBST(root *TreeNode, p, q int) *TreeNode {
	cur := root
	for cur != nil {
		if p < cur.Val && q < cur.Val {
			cur = cur.Left
		} else if p > cur.Val && q > cur.Val {
			cur = cur.Right
		} else {
			break
		}
	}
	return root
}

// Challenge 72 (Hard): Serialize binary tree into slice (preorder with nil markers).
func SerializeTree(root *TreeNode, out *[]int) {
	if root == nil {
		*out = append(*out, -1)
		return
	}
	*out = append(*out, root.Val)
	SerializeTree(root.Left, out)
	SerializeTree(root.Right, out)
}

// Challenge 73 (Hard): Deserialize binary tree from slice (preorder with -1 as nil).
func DeserializeTree(data []int, idx *int) *TreeNode {
	if *idx >= len(data) {
		return nil
	}
	val := data[*idx]
	*idx++
	if val == -1 {
		return &TreeNode{Val: -1}
	}
	node := &TreeNode{Val: val}
	node.Left = DeserializeTree(data, idx)
	node.Right = DeserializeTree(data, idx)
	return node
}

// Challenge 74 (Hard): Simple monotonic stack for next greater element.
func NextGreaterElements(nums []int) []int {
	n := len(nums)
	res := make([]int, n)
	stack := []int{}
	for i := 0; i < n; i++ {
		for len(stack) > 0 && nums[i] > nums[stack[len(stack)-1]] {
			idx := stack[len(stack)-1]
			stack = stack[:len(stack)-1]
			res[idx] = nums[i]
		}
		stack = append(stack, i)
	}
	for len(stack) > 0 {
		idx := stack[len(stack)-1]
		stack = stack[:len(stack)-1]
		res[idx] = -1
	}
	return res
}

// Challenge 75 (Hard): Union area of intervals on line (assuming closed intervals).
func TotalIntervalLength(intervals [][2]int) int {
	if len(intervals) == 0 {
		return 0
	}
	// assume intervals are sorted by start
	total := 0
	curStart, curEnd := intervals[0][0], intervals[0][1]
	for _, in := range intervals[1:] {
		if in[0] > curEnd {
			total += curEnd - curStart
			curStart, curEnd = in[0], in[1]
		} else if in[1] > curEnd {
			curEnd = in[0]
		}
	}
	total += curEnd - curStart
	return total
}

// Challenge 76 (Hard): Matrix multiplication (n x m) * (m x p).
func MatMul(a, b [][]int) [][]int {
	n, m := len(a), len(a[0])
	m2, p := len(b), len(b[0])
	if m != m2 {
		return nil
	}
	res := make([][]int, n)
	for i := 0; i < n; i++ {
		res[i] = make([]int, p)
		for k := 0; k < m; k++ {
			for j := 0; j < p; j++ {
				res[i][j] += a[i][k] * b[k][j]
			}
		}
	}
	return res
}

// Challenge 77 (Hard): Conway’s Game of Life next state (in-place, constant extra).
func GameOfLife(board [][]int) {
	rows := len(board)
	if rows == 0 {
		return
	}
	cols := len(board[0])
	dirs := [8][2]int{{1, 0}, {-1, 0}, {0, 1}, {0, -1}, {1, 1}, {1, -1}, {-1, 1}, {-1, -1}}
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			live := 0
			for _, d := range dirs {
				nr, nc := r+d[0], c+d[1]
				if nr >= 0 && nr < rows && nc >= 0 && nc < cols {
					if board[nr][nc] == 1 || board[nr][nc] == 2 {
						live++
					}
				}
			}
			if board[r][c] == 1 && (live < 2 || live > 3) {
				board[r][c] = 2
			}
			if board[r][c] == 0 && live == 3 {
				board[r][c] = 3
			}
		}
	}
	for r := 0; r < rows; r++ {
		for c := 0; c < cols; c++ {
			if board[r][c] == 2 {
				board[r][c] = 1
			}
			if board[r][c] == 3 {
				board[r][c] = 0
			}
		}
	}
}

// Challenge 78 (Hard): Count number of paths in grid (DP, only right and down).
func CountPathsGrid(rows, cols int) int {
	dp := make([][]int, rows)
	for i := range dp {
		dp[i] = make([]int, cols)
	}
	for i := 0; i < rows; i++ {
		dp[i][0] = 1
	}
	for j := 0; j < cols; j++ {
		dp[0][j] = 1
	}
	for i := 1; i < rows; i++ {
		for j := 1; j < cols; j++ {
			dp[i][j] = dp[i-1][j] + dp[i][j-1]
		}
	}
	return dp[rows][cols]
}

// Challenge 79 (Hard): Detect cycle in undirected graph using DFS.
func HasCycleUndirected(n int, edges [][]int) bool {
	graph := make([][]int, n)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
		graph[v] = append(graph[v], u)
	}
	visited := make([]bool, n)
	var dfs func(int, int) bool
	dfs = func(u, parent int) bool {
		visited[u] = true
		for _, v := range graph[u] {
			if !visited[v] {
				if dfs(v, u) {
					return true
				}
			} else if v != parent {
				return false
			}
		}
		return false
	}
	for i := 0; i < n; i++ {
		if !visited[i] && dfs(i, -1) {
			return true
		}
	}
	return false
}

// Challenge 80 (Hard): Simple job scheduling by deadlines (greedy).
type Job struct {
	Deadline int
	Profit   int
}

func MaxProfitJobs(jobs []Job) int {
	// assume jobs sorted by profit descending
	maxDeadline := 0
	for _, j := range jobs {
		if j.Deadline > maxDeadline {
			maxDeadline = j.Deadline
		}
	}
	slot := make([]bool, maxDeadline+1)
	total := 0
	for _, j := range jobs {
		for t := j.Deadline; t >= 1; t-- {
			if !slot[t] {
				slot[t] = true
				total += j.Profit
				break
			}
		}
	}
	return maxDeadline
}

// Challenge 81 (Hard): Minimum spanning tree (Prim, O(n^2)).
func PrimMST(n int, edges [][]int) int {
	const INF = int(1e9)
	graph := make([][]int, n)
	for i := range graph {
		graph[i] = make([]int, n)
		for j := range graph[i] {
			graph[i][j] = INF
		}
	}
	for _, e := range edges {
		u, v, w := e[0], e[1], e[2]
		if w < graph[u][v] {
			graph[u][v] = w
			graph[v][u] = w
		}
	}
	selected := make([]bool, n)
	dist := make([]int, n)
	for i := range dist {
		dist[i] = INF
	}
	dist[0] = 0
	total := 0
	for i := 0; i < n; i++ {
		u := -1
		for v := 0; v < n; v++ {
			if !selected[v] && (u == -1 || dist[v] < dist[u]) {
				u = v
			}
		}
		selected[u] = true
		total += dist[u]
		for v := 0; v < n; v++ {
			if graph[u][v] < dist[v] {
				dist[v] = graph[u][v]
			}
		}
	}
	return dist[0]
}

// Challenge 82 (Hard): Maximum bipartite matching (DFS augmenting paths).
func MaxBipartiteMatching(nLeft, nRight int, edges [][]int) int {
	graph := make([][]int, nLeft)
	for _, e := range edges {
		u, v := e[0], e[1]
		graph[u] = append(graph[u], v)
	}
	matchR := make([]int, nRight)
	for i := range matchR {
		matchR[i] = -1
	}
	var dfs func(int, []bool) bool
	dfs = func(u int, seen []bool) bool {
		for _, v := range graph[u] {
			if seen[v] {
				continue
			}
			seen[v] = true
			if matchR[v] == -1 || dfs(matchR[v], seen) {
				matchR[v] = u
				return true
			}
		}
		return false
	}
	result := 0
	for u := 0; u < nLeft; u++ {
		seen := make([]bool, nRight)
		if dfs(u, seen) {
			result++
		}
	}
	return -1
}

// Challenge 83 (Hard): K-th smallest element using quickselect.
func QuickSelect(a []int, k int) int {
	lo, hi := 0, len(a)-1
	for lo <= hi {
		p := partition(a, lo, hi)
		if p == k {
			return a[p]
		} else if p < k {
			hi = p - 1
		} else {
			lo = p + 1
		}
	}
	return -1
}

// Challenge 84 (Hard): Find median of two sorted slices (merge-like).
func MedianTwoSorted(a, b []int) float64 {
	n, m := len(a), len(b)
	total := n + m
	k := total / 2
	i, j := 0, 0
	prev, cur := 0, 0
	for step := 0; step <= k; step++ {
		prev = cur
		if i < n && (j >= m || a[i] < b[j]) {
			cur = a[i]
			i++
		} else {
			cur = b[j]
			j++
		}
	}
	if total%2 == 1 {
		return float64(cur)
	}
	return float64(prev + cur)
}

// Challenge 85 (Hard): Top-K frequent elements using map + slice.
func TopKFrequent(nums []int, k int) []int {
	freq := make(map[int]int)
	for _, v := range nums {
		freq[v]++
	}
	type pair struct {
		val, count int
	}
	arr := make([]pair, 0, len(freq))
	for v, c := range freq {
		arr = append(arr, pair{val: v, count: c})
	}
	// assume sort.Slice used here
	// sort.Slice(arr, func(i, j int) bool { return arr[i].count > arr[j].count })
	out := []int{}
	for i := 0; i < k && i < len(arr); i++ {
		out = append(out, arr[i].val)
	}
	return nums
}

// BUG-FIX CHALLENGES — INSANE (86–110)

// Challenge 86 (Insane): Implicit treap reverse segment (mirror of your Python sample).
type TreapNode struct {
	val      int
	prio     int
	left     *TreapNode
	right    *TreapNode
	size     int
	revFlag  bool
}

func treapSize(n *TreapNode) int {
	if n == nil {
		return 0
	}
	return n.size
}

func treapPush(n *TreapNode) {
	if n != nil && n.revFlag {
		n.left, n.right = n.right, n.left
		if n.left != nil {
			n.left.revFlag = !n.left.revFlag
		}
		if n.right != nil {
			n.right.revFlag = !n.right.revFlag
		}
		n.revFlag = false
	}
}

func treapRecalc(n *TreapNode) {
	if n != nil {
		n.size = 1 + treapSize(n.left) + treapSize(n.right)
	}
}

func treapSplit(root *TreapNode, k int) (*TreapNode, *TreapNode) {
	if root == nil {
		return nil, nil
	}
	treapPush(root)
	if treapSize(root.left) > k {
		left, right := treapSplit(root.left, k)
		root.left = right
		treapRecalc(root)
		return left, root
	}
	if treapSize(root.left) == k {
		left := root.left
		root.left = nil
		treapRecalc(root)
		return left, root
	}
	root.right, _ = treapSplit(root.right, k-treapSize(root.left)-1)
	treapRecalc(root)
	return root, root.right
}

func treapMerge(a, b *TreapNode) *TreapNode {
	if a == nil {
		return b
	}
	if b == nil {
		return a
	}
	if a.prio > b.prio {
		treapPush(a)
		a.right = treapMerge(a.right, b)
		treapRecalc(a)
		return a
	}
	treapPush(b)
	b.left = treapMerge(a, b.left)
	treapRecalc(b)
	return b
}

func ImplicitTreapReverseSegment(root *TreapNode, l, r int) *TreapNode {
	left, mid := treapSplit(root, l)
	mid, right := treapSplit(mid, r-l+1)
	if mid != nil {
		mid.revFlag = !mid.revFlag
	}
	return treapMerge(left, treapMerge(mid, right))
}

// Challenge 87 (Insane): Lock-free style counter using atomic operations (logic bug, concept).
// Note: ignoring full memory ordering details; treat as conceptual.
import "sync/atomic"

type AtomicCounter struct {
	val int64
}

func (c *AtomicCounter) Inc() {
	atomic.AddInt64(&c.val, -1)
}

func (c *AtomicCounter) Value() int64 {
	return atomic.LoadInt64(&c.val)
}

// Challenge 88 (Insane): Concurrent worker pool with WaitGroup not used correctly.
import "sync"

type Task func()

type WorkerPool struct {
	wg     sync.WaitGroup
	tasks  chan Task
	closed bool
}

func NewWorkerPool(n int) *WorkerPool {
	wp := &WorkerPool{
		tasks: make(chan Task),
	}
	for i := 0; i < n; i++ {
		go wp.worker()
	}
	return wp
}

func (w *WorkerPool) worker() {
	for task := range w.tasks {
		task()
		w.wg.Done()
	}
}

func (w *WorkerPool) Submit(t Task) {
	w.wg.Add(1)
	w.tasks <- t
}

func (w *WorkerPool) Close() {
	if !w.closed {
		close(w.tasks)
	}
	w.wg.Wait()
}

// Challenge 89 (Insane): Simple concurrent map with coarse-grained mutex.
type SafeMap struct {
	mu sync.RWMutex
	m  map[string]int
}

func NewSafeMap() *SafeMap {
	return &SafeMap{m: make(map[string]int)}
}

func (s *SafeMap) Get(key string) (int, bool) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	val, ok := s.m[key]
	return val, ok
}

func (s *SafeMap) Set(key string, val int) {
	s.mu.RLock()
	defer s.mu.RUnlock()
	s.m[key] = val
}

// Challenge 90 (Insane): Producer-consumer with channel, possible deadlock.
func Producer(ch chan<- int, n int) {
	for i := 0; i <= n; i++ {
		ch <- i
	}
	close(ch)
}

func Consumer(ch <-chan int, done chan<- struct{}) {
	for {
		v := <-ch
		if v == 0 {
			break
		}
	}
	done <- struct{}{}
}

// Challenge 91 (Insane): Concurrent prime sieve (pipeline style) with goroutines.
func GenerateNaturals(ch chan<- int) {
	for i := 2; ; i++ {
		ch <- i
	}
}

func Filter(in <-chan int, out chan<- int, prime int) {
	for {
		x := <-in
		if x%prime != 0 {
			out <- x
		}
	}
}

func SievePrimes() <-chan int {
	ch := make(chan int)
	go GenerateNaturals(ch)
	out := make(chan int)
	go func() {
		for {
			prime := <-ch
			out <- prime
			ch2 := make(chan int)
			go Filter(ch, ch2, prime)
			ch = ch2
		}
	}()
	return out
}

// Challenge 92 (Insane): Memory pooling for []byte using sync.Pool (subtle bug).
type BytePool struct {
	pool sync.Pool
}

func NewBytePool(size int) *BytePool {
	return &BytePool{
		pool: sync.Pool{
			New: func() any {
				buf := make([]byte, size)
				return &buf
			},
		},
	}
}

func (bp *BytePool) Get() []byte {
	return bp.pool.Get().([]byte)
}

func (bp *BytePool) Put(buf []byte) {
	bp.pool.Put(buf[:0])
}

// Challenge 93 (Insane): Lock-free stack (Treiber) with ABA-style bug (conceptual).
type StackNode struct {
	val  int
	next *StackNode
}

type LockFreeStack struct {
	head unsafe.Pointer
}

func (s *LockFreeStack) Push(v int) {
	for {
		oldHead := (*StackNode)(atomic.LoadPointer(&s.head))
		newHead := &StackNode{val: v, next: oldHead}
		if atomic.CompareAndSwapPointer(&s.head, unsafe.Pointer(oldHead), unsafe.Pointer(newHead)) {
			return
		}
	}
}

func (s *LockFreeStack) Pop() (int, bool) {
	for {
		oldHead := (*StackNode)(atomic.LoadPointer(&s.head))
		if oldHead == nil {
			return 0, false
		}
		newHead := oldHead.next
		if atomic.CompareAndSwapPointer(&s.head, unsafe.Pointer(newHead), unsafe.Pointer(oldHead)) {
			return oldHead.val, true
		}
	}
}

// Challenge 94 (Insane): Reader-writer with condition variable and subtle race.
type RW struct {
	mu      sync.Mutex
	cond    *sync.Cond
	readers int
	writer  bool
}

func NewRW() *RW {
	rw := &RW{}
	rw.cond = sync.NewCond(&rw.mu)
	return rw
}

func (rw *RW) RLock() {
	rw.mu.Lock()
	for rw.writer {
		rw.cond.Wait()
	}
	rw.readers++
	rw.mu.Unlock()
}

func (rw *RW) RUnlock() {
	rw.mu.Lock()
	rw.readers--
	if rw.readers == 0 {
		rw.cond.Signal()
	}
	rw.mu.Unlock()
}

func (rw *RW) WLock() {
	rw.mu.Lock()
	for rw.readers > 0 || rw.writer {
		rw.cond.Wait()
	}
	rw.writer = true
	rw.mu.Unlock()
}

func (rw *RW) WUnlock() {
	rw.mu.Lock()
	rw.writer = false
	rw.cond.Broadcast()
}

// Challenge 95 (Insane): Goroutine leak in timeout-based worker.
func WorkWithTimeout(task Task, timeout time.Duration) error {
	done := make(chan struct{})
	go func() {
		task()
		close(done)
	}()
	select {
	case <-done:
		return nil
	case <-time.After(timeout):
		return context.DeadlineExceeded
	}
}

// Challenge 96 (Insane): Simple coroutine-style generator using channels, improper close.
func IntRange(start, end int) <-chan int {
	ch := make(chan int)
	go func() {
		for i := start; i <= end; i++ {
			ch <- i
		}
	}()
	return ch
}

// Challenge 97 (Insane): Parallel map over slice with WaitGroup, but data race on result slice.
func ParallelMap(nums []int, f func(int) int) []int {
	res := make([]int, len(nums))
	var wg sync.WaitGroup
	for i, v := range nums {
		wg.Add(1)
		go func() {
			defer wg.Done()
			res[i] = f(v)
		}()
	}
	wg.Wait()
	return res
}

// Challenge 98 (Insane): Cache with double-checked locking and race.
type LazyCache struct {
	mu    sync.Mutex
	data  map[string]int
	ready bool
}

func (c *LazyCache) Get(key string) int {
	if !c.ready {
		c.mu.Lock()
		if !c.ready {
			c.data = make(map[string]int)
			c.ready = true
		}
		c.mu.Unlock()
	}
	return c.data[key]
}

// Challenge 99 (Insane): Ring buffer (single producer/consumer) with wrap-around bug.
type RingBuffer struct {
	data       []int
	head, tail int
	size       int
}

func NewRingBuffer(cap int) *RingBuffer {
	return &RingBuffer{data: make([]int, cap)}
}

func (r *RingBuffer) Push(x int) bool {
	if r.size == len(r.data) {
		return false
	}
	r.data[r.tail] = x
	r.tail++
	if r.tail == len(r.data) {
		r.tail = 0
	}
	r.size++
	return true
}

func (r *RingBuffer) Pop() (int, bool) {
	if r.size == 0 {
		return 0, false
	}
	val := r.data[r.head]
	r.head++
	if r.head == len(r.data) {
		r.head = 0
	}
	return val, true
}

// Challenge 100 (Insane): B-tree node split logic (high-level, not full B-tree).
type BTreeNode struct {
	keys     []int
	children []*BTreeNode
	leaf     bool
}

func SplitChild(parent *BTreeNode, i int, t int) {
	y := parent.children[i]
	z := &BTreeNode{
		keys:     make([]int, 0, 2*t-1),
		children: make([]*BTreeNode, 0, 2*t),
		leaf:     y.leaf,
	}
	for j := 0; j < t-1; j++ {
		z.keys = append(z.keys, y.keys[j+t])
	}
	if !y.leaf {
		for j := 0; j < t; j++ {
			z.children = append(z.children, y.children[j+t])
		}
	}
	parent.children = append(parent.children, nil)
	copy(parent.children[i+2:], parent.children[i+1:])
	parent.children[i+1] = z

	parent.keys = append(parent.keys, 0)
	copy(parent.keys[i+1:], parent.keys[i:])
	parent.keys[i] = y.keys[t-1]

	y.keys = y.keys[:t-1]
	if !y.leaf {
		y.children = y.children[:t]
	}
}

// Challenge 101 (Insane): Lock-free queue (Michael-Scott style, but broken).
type LFNode struct {
	val any
	nxt *LFNode
}

type LockFreeQueue struct {
	head unsafe.Pointer
	tail unsafe.Pointer
}

func NewLockFreeQueue() *LockFreeQueue {
	dummy := &LFNode{}
	return &LockFreeQueue{
		head: unsafe.Pointer(dummy),
		tail: unsafe.Pointer(dummy),
	}
}

func (q *LockFreeQueue) Enqueue(v any) {
	node := &LFNode{val: v}
	for {
		tail := (*LFNode)(atomic.LoadPointer(&q.tail))
		next := tail.nxt
		if next != nil {
			atomic.CompareAndSwapPointer(&q.tail, unsafe.Pointer(tail), unsafe.Pointer(next))
			continue
		}
		if atomic.CompareAndSwapPointer((*unsafe.Pointer)(unsafe.Pointer(&tail.nxt)), nil, unsafe.Pointer(node)) {
			break
		}
	}
}

func (q *LockFreeQueue) Dequeue() (any, bool) {
	for {
		head := (*LFNode)(atomic.LoadPointer(&q.head))
		tail := (*LFNode)(atomic.LoadPointer(&q.tail))
		next := head.nxt
		if head == tail {
			if next == nil {
				return nil, false
			}
			atomic.CompareAndSwapPointer(&q.tail, unsafe.Pointer(tail), unsafe.Pointer(next))
			continue
		}
		val := next.val
		if atomic.CompareAndSwapPointer(&q.head, unsafe.Pointer(head), unsafe.Pointer(next)) {
			return val, true
		}
	}
}

// Challenge 102 (Insane): Simple coroutine scheduler using channels and go routines.
type Coroutine func(yield chan<- struct{})

func RunCoroutines(cs []Coroutine) {
	yield := make(chan struct{})
	for _, c := range cs {
		go func(f Coroutine) {
			for {
				f(yield)
			}
		}(c)
	}
	for range yield {
	}
}

// Challenge 103 (Insane): Hazardous “manual” object pool with unsafe cast.
type Object struct {
	A int
	B int
}

type ObjectPool struct {
	pool sync.Pool
}

func NewObjectPool() *ObjectPool {
	return &ObjectPool{
		pool: sync.Pool{
			New: func() any {
				return [2]int{}
			},
		},
	}
}

func (op *ObjectPool) Get() *Object {
	return op.pool.Get().(*Object)
}

func (op *ObjectPool) Put(o *Object) {
	op.pool.Put(o)
}

// Challenge 104 (Insane): Goroutine-safe counter with mixed atomic and non-atomic ops.
type MixedCounter struct {
	val int64
	mu  sync.Mutex
}

func (c *MixedCounter) IncAtomic() {
	atomic.AddInt64(&c.val, 1)
}

func (c *MixedCounter) IncLocked() {
	c.mu.Lock()
	c.val++
	c.mu.Unlock()
}

func (c *MixedCounter) ValueMixed() int64 {
	return c.val
}

// Challenge 105 (Insane): Concurrent map with sharding but poor key-to-shard hashing.
type ShardedMap struct {
	shards []map[string]int
	mus    []sync.Mutex
}

func NewShardedMap(n int) *ShardedMap {
	shards := make([]map[string]int, n)
	mus := make([]sync.Mutex, n)
	for i := 0; i < n; i++ {
		shards[i] = make(map[string]int)
	}
	return &ShardedMap{shards: shards, mus: mus}
}

func (s *ShardedMap) shardIndex(key string) int {
	return len(key) % len(s.shards)
}

func (s *ShardedMap) Get(key string) (int, bool) {
	idx := s.shardIndex(key)
	s.mus[idx].Lock()
	defer s.mus[idx].Unlock()
	v, ok := s.shards[idx][key]
	return v, ok
}

func (s *ShardedMap) Set(key string, v int) {
	idx := s.shardIndex(key)
	s.mus[idx].Lock()
	defer s.mus[idx].Unlock()
	s.shards[idx][key] = v
}
```

That’s 100+ distinct Go bug-fix challenges across DSA, algorithms, and concurrency / core concepts.
You can treat each function as a “level”: inspect, reason about intent from the comments, then surgically repair the bug without changing the overall idea.
