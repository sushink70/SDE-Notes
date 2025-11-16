# Data Structures in Go

## Complete List of Data Structures:

### Built-in Types:
1. **Arrays** - Fixed-size collections
2. **Slices** - Dynamic arrays
3. **Maps** - Hash tables
4. **Structs** - Composite types

### Standard Library (container package):
5. **Linked List** - Doubly linked list
6. **Ring** - Circular list
7. **Heap** - Priority queue

### Custom Implementations:
8. **Stack** - LIFO structure
9. **Queue** - FIFO structure
10. **Set** - Unique elements
11. **Binary Search Tree** - Sorted tree
12. **Graph** - Adjacency list with BFS/DFS
13. **Trie** - Prefix tree for strings
14. **Bit Set** - Efficient boolean array
15. **Bloom Filter** - Probabilistic membership
16. **LRU Cache** - Least Recently Used cache

### Concurrent Structures:
17. **sync.Map** - Thread-safe map
18. **Channels** - Communication between goroutines
19. **Mutex-protected structures** - Safe concurrent access

### Additional Operations:
- **Sorting** - Multiple sorting algorithms
- **Advanced slice tricks** - Insert, delete, filter, partition, merge
- **Advanced map operations** - Invert, merge, filter, reduce

Each structure includes:
- Creation and initialization
- Common operations (add, remove, search)
- Iteration methods
- Practical examples

You can run this complete program to see all data structures in action!

```go
package main

import (
	"container/heap"
    "container/heap"
    "container/list"
    "container/ring"
    "fmt"
    "sort"
    "sync""container/list"
	"container/ring"
	"fmt"
	"sort"
	"sync"
)

// ============================================================================
// 1. ARRAYS - Fixed-size sequential collection
// ============================================================================

func arrayOperations() {
	fmt.Println("=== ARRAYS ===")
	
	// Declaration and initialization
	var arr1 [5]int                              // [0 0 0 0 0]
	arr2 := [5]int{1, 2, 3, 4, 5}               // Full initialization
	arr3 := [...]int{1, 2, 3}                    // Compiler counts
	arr4 := [5]int{1: 10, 3: 30}                // Sparse: [0 10 0 30 0]
	
	// Access and modify
	arr2[0] = 100
	value := arr2[0]
	fmt.Println("Array value:", value)
	
	// Length
	length := len(arr2)
	fmt.Println("Array length:", length)
	
	// Iterate
	for i := 0; i < len(arr2); i++ {
		fmt.Printf("arr2[%d] = %d\n", i, arr2[i])
	}
	
	for index, value := range arr2 {
		fmt.Printf("Index: %d, Value: %d\n", index, value)
	}
	
	// Multi-dimensional arrays
	var matrix [3][3]int
	matrix[0][0] = 1
	
	// Compare arrays (same type and size)
	a := [3]int{1, 2, 3}
	b := [3]int{1, 2, 3}
	fmt.Println("Arrays equal:", a == b)
	
	fmt.Println(arr1, arr3, arr4, matrix)
}

// ============================================================================
// 2. SLICES - Dynamic arrays with flexible size
// ============================================================================

func sliceOperations() {
	fmt.Println("\n=== SLICES ===")
	
	// Declaration and initialization
	var s1 []int                                 // nil slice
	s2 := []int{1, 2, 3, 4, 5}                  // Literal
	s3 := make([]int, 5)                         // length 5, cap 5
	s4 := make([]int, 5, 10)                     // length 5, cap 10
	
	// From array
	arr := [5]int{1, 2, 3, 4, 5}
	s5 := arr[1:4]                               // [2 3 4]
	s6 := arr[:]                                 // All elements
	s7 := arr[:3]                                // First 3
	s8 := arr[2:]                                // From index 2
	
	// Append
	s2 = append(s2, 6)                           // Append single
	s2 = append(s2, 7, 8, 9)                    // Append multiple
	s2 = append(s2, s3...)                       // Append slice
	
	// Length and capacity
	fmt.Printf("Len: %d, Cap: %d\n", len(s2), cap(s2))
	
	// Copy
	dest := make([]int, len(s2))
	n := copy(dest, s2)
	fmt.Println("Copied elements:", n)
	
	// Slice of slice
	subSlice := s2[2:5]
	fmt.Println("Sub-slice:", subSlice)
	
	// Remove element (no built-in function)
	// Remove at index i
	i := 2
	s2 = append(s2[:i], s2[i+1:]...)
	
	// Insert element at index
	i = 2
	value := 99
	s2 = append(s2[:i], append([]int{value}, s2[i:]...)...)
	
	// Clear slice
	s2 = s2[:0]
	
	// Filter slice
	original := []int{1, 2, 3, 4, 5, 6}
	filtered := original[:0]
	for _, v := range original {
		if v%2 == 0 {
			filtered = append(filtered, v)
		}
	}
	
	// Reverse slice
	for i, j := 0, len(original)-1; i < j; i, j = i+1, j-1 {
		original[i], original[j] = original[j], original[i]
	}
	
	// 2D slices
	matrix := make([][]int, 3)
	for i := range matrix {
		matrix[i] = make([]int, 4)
	}
	
	fmt.Println(s1, s3, s4, s5, s6, s7, s8, filtered, matrix)
}

// ============================================================================
// 3. MAPS - Key-value pairs (hash table)
// ============================================================================

func mapOperations() {
	fmt.Println("\n=== MAPS ===")
	
	// Declaration and initialization
	var m1 map[string]int                        // nil map
	m2 := make(map[string]int)                   // Empty map
	m3 := map[string]int{
		"one":   1,
		"two":   2,
		"three": 3,
	}
	
	// Add/Update
	m3["four"] = 4
	m3["one"] = 100  // Update
	
	// Get value
	value := m3["one"]
	fmt.Println("Value:", value)
	
	// Check existence
	value, exists := m3["five"]
	if exists {
		fmt.Println("Found:", value)
	} else {
		fmt.Println("Not found")
	}
	
	// Delete
	delete(m3, "two")
	
	// Length
	fmt.Println("Map size:", len(m3))
	
	// Iterate
	for key, value := range m3 {
		fmt.Printf("%s: %d\n", key, value)
	}
	
	// Iterate keys only
	for key := range m3 {
		fmt.Println("Key:", key)
	}
	
	// Clear map
	for key := range m3 {
		delete(m3, key)
	}
	// Or recreate
	m3 = make(map[string]int)
	
	// Map with struct values
	type Person struct {
		Name string
		Age  int
	}
	people := make(map[string]Person)
	people["alice"] = Person{"Alice", 30}
	
	// Map with slice values
	tags := make(map[string][]string)
	tags["go"] = []string{"programming", "backend"}
	
	// Nested maps
	nested := make(map[string]map[string]int)
	nested["group1"] = make(map[string]int)
	nested["group1"]["item1"] = 10
	
	// Concurrent map (use sync.Map for concurrency)
	var sm sync.Map
	sm.Store("key", "value")
	val, ok := sm.Load("key")
	sm.Delete("key")
	sm.Range(func(key, value interface{}) bool {
		fmt.Printf("%v: %v\n", key, value)
		return true // continue iteration
	})
	
	fmt.Println(m1, m2, people, tags, nested, val, ok)
}

// ============================================================================
// 4. STRUCTS - Composite data type
// ============================================================================

type Person struct {
	Name    string
	Age     int
	Address Address
}

type Address struct {
	Street string
	City   string
}

func structOperations() {
	fmt.Println("\n=== STRUCTS ===")
	
	// Declaration and initialization
	var p1 Person
	p2 := Person{Name: "Alice", Age: 30}
	p3 := Person{"Bob", 25, Address{"123 Main St", "NYC"}}
	
	// Access and modify fields
	p1.Name = "Charlie"
	p1.Age = 35
	fmt.Println(p1.Name)
	
	// Nested struct access
	p3.Address.City = "Boston"
	
	// Pointer to struct
	p4 := &Person{Name: "Dave", Age: 40}
	p4.Name = "David"  // Auto-dereferencing
	(*p4).Age = 41     // Explicit dereferencing
	
	// Anonymous struct
	config := struct {
		Host string
		Port int
	}{
		Host: "localhost",
		Port: 8080,
	}
	
	// Struct embedding
	type Employee struct {
		Person
		EmployeeID int
	}
	emp := Employee{
		Person:     Person{Name: "Eve", Age: 28},
		EmployeeID: 1001,
	}
	fmt.Println(emp.Name) // Promoted field
	
	// Struct tags (used in JSON, DB mapping)
	type User struct {
		ID    int    `json:"id" db:"user_id"`
		Email string `json:"email" validate:"required,email"`
	}
	
	// Compare structs (all fields must be comparable)
	a := Person{Name: "Test", Age: 30}
	b := Person{Name: "Test", Age: 30}
	fmt.Println("Structs equal:", a == b)
	
	fmt.Println(p2, config, emp)
}

// ============================================================================
// 5. LINKED LIST - container/list (doubly linked)
// ============================================================================

func linkedListOperations() {
	fmt.Println("\n=== LINKED LIST ===")
	
	// Create list
	l := list.New()
	
	// Add elements
	l.PushBack(1)                                // Add to back
	l.PushFront(0)                               // Add to front
	e := l.PushBack(2)                           // Returns element
	l.InsertBefore(1.5, e)                       // Insert before element
	l.InsertAfter(2.5, e)                        // Insert after element
	
	// Length
	fmt.Println("List length:", l.Len())
	
	// Access front and back
	front := l.Front()
	back := l.Back()
	if front != nil {
		fmt.Println("Front value:", front.Value)
	}
	if back != nil {
		fmt.Println("Back value:", back.Value)
	}
	
	// Iterate forward
	for e := l.Front(); e != nil; e = e.Next() {
		fmt.Println("Value:", e.Value)
	}
	
	// Iterate backward
	for e := l.Back(); e != nil; e = e.Prev() {
		fmt.Println("Value:", e.Value)
	}
	
	// Remove element
	l.Remove(e)
	
	// Move elements
	l.MoveToFront(l.Back())
	l.MoveToBack(l.Front())
	
	// Clear list
	l.Init()
}

// ============================================================================
// 6. RING - Circular list (container/ring)
// ============================================================================

func ringOperations() {
	fmt.Println("\n=== RING ===")
	
	// Create ring
	r := ring.New(5)
	
	// Initialize with values
	for i := 0; i < r.Len(); i++ {
		r.Value = i
		r = r.Next()
	}
	
	// Traverse
	r.Do(func(v interface{}) {
		fmt.Println("Ring value:", v)
	})
	
	// Move
	r = r.Move(2)  // Move 2 positions forward
	r = r.Move(-1) // Move 1 position backward
	
	// Link rings
	r2 := ring.New(3)
	for i := 0; i < r2.Len(); i++ {
		r2.Value = i + 10
		r2 = r2.Next()
	}
	r.Link(r2)  // Connect rings
	
	// Unlink
	removed := r.Unlink(3)  // Remove 3 elements
	fmt.Println("Removed length:", removed.Len())
}

// ============================================================================
// 7. HEAP - Priority queue (container/heap)
// ============================================================================

// IntHeap implements heap.Interface
type IntHeap []int

func (h IntHeap) Len() int           { return len(h) }
func (h IntHeap) Less(i, j int) bool { return h[i] < h[j] } // Min-heap
func (h IntHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }

func (h *IntHeap) Push(x interface{}) {
	*h = append(*h, x.(int))
}

func (h *IntHeap) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

func heapOperations() {
	fmt.Println("\n=== HEAP ===")
	
	// Create and initialize heap
	h := &IntHeap{2, 1, 5, 3, 4}
	heap.Init(h)
	
	// Push
	heap.Push(h, 0)
	
	// Pop (removes and returns minimum)
	min := heap.Pop(h).(int)
	fmt.Println("Minimum:", min)
	
	// Peek (without removing)
	if h.Len() > 0 {
		peek := (*h)[0]
		fmt.Println("Peek:", peek)
	}
	
	// Remove at index
	if h.Len() > 1 {
		heap.Remove(h, 1)
	}
	
	// Fix after modifying element
	(*h)[0] = 100
	heap.Fix(h, 0)
	
	// Drain heap
	for h.Len() > 0 {
		fmt.Println("Pop:", heap.Pop(h))
	}
}

// Max heap example
type MaxHeap []int

func (h MaxHeap) Len() int           { return len(h) }
func (h MaxHeap) Less(i, j int) bool { return h[i] > h[j] } // Max-heap
func (h MaxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MaxHeap) Push(x interface{}) {
	*h = append(*h, x.(int))
}
func (h *MaxHeap) Pop() interface{} {
	old := *h
	n := len(old)
	x := old[n-1]
	*h = old[0 : n-1]
	return x
}

// ============================================================================
// 8. STACK - Custom implementation using slice
// ============================================================================

type Stack struct {
	items []interface{}
}

func (s *Stack) Push(item interface{}) {
	s.items = append(s.items, item)
}

func (s *Stack) Pop() (interface{}, bool) {
	if len(s.items) == 0 {
		return nil, false
	}
	item := s.items[len(s.items)-1]
	s.items = s.items[:len(s.items)-1]
	return item, true
}

func (s *Stack) Peek() (interface{}, bool) {
	if len(s.items) == 0 {
		return nil, false
	}
	return s.items[len(s.items)-1], true
}

func (s *Stack) IsEmpty() bool {
	return len(s.items) == 0
}

func (s *Stack) Size() int {
	return len(s.items)
}

func stackOperations() {
	fmt.Println("\n=== STACK ===")
	
	stack := &Stack{}
	
	stack.Push(1)
	stack.Push(2)
	stack.Push(3)
	
	fmt.Println("Size:", stack.Size())
	
	if val, ok := stack.Peek(); ok {
		fmt.Println("Peek:", val)
	}
	
	for !stack.IsEmpty() {
		if val, ok := stack.Pop(); ok {
			fmt.Println("Pop:", val)
		}
	}
}

// ============================================================================
// 9. QUEUE - Custom implementation using slice
// ============================================================================

type Queue struct {
	items []interface{}
}

func (q *Queue) Enqueue(item interface{}) {
	q.items = append(q.items, item)
}

func (q *Queue) Dequeue() (interface{}, bool) {
	if len(q.items) == 0 {
		return nil, false
	}
	item := q.items[0]
	q.items = q.items[1:]
	return item, true
}

func (q *Queue) Front() (interface{}, bool) {
	if len(q.items) == 0 {
		return nil, false
	}
	return q.items[0], true
}

func (q *Queue) IsEmpty() bool {
	return len(q.items) == 0
}

func (q *Queue) Size() int {
	return len(q.items)
}

func queueOperations() {
	fmt.Println("\n=== QUEUE ===")
	
	queue := &Queue{}
	
	queue.Enqueue(1)
	queue.Enqueue(2)
	queue.Enqueue(3)
	
	fmt.Println("Size:", queue.Size())
	
	if val, ok := queue.Front(); ok {
		fmt.Println("Front:", val)
	}
	
	for !queue.IsEmpty() {
		if val, ok := queue.Dequeue(); ok {
			fmt.Println("Dequeue:", val)
		}
	}
}

// ============================================================================
// 10. SET - Custom implementation using map
// ============================================================================

type Set struct {
	items map[interface{}]struct{}
}

func NewSet() *Set {
	return &Set{items: make(map[interface{}]struct{})}
}

func (s *Set) Add(item interface{}) {
	s.items[item] = struct{}{}
}

func (s *Set) Remove(item interface{}) {
	delete(s.items, item)
}

func (s *Set) Contains(item interface{}) bool {
	_, exists := s.items[item]
	return exists
}

func (s *Set) Size() int {
	return len(s.items)
}

func (s *Set) Items() []interface{} {
	items := make([]interface{}, 0, len(s.items))
	for item := range s.items {
		items = append(items, item)
	}
	return items
}

func (s *Set) Union(other *Set) *Set {
	result := NewSet()
	for item := range s.items {
		result.Add(item)
	}
	for item := range other.items {
		result.Add(item)
	}
	return result
}

func (s *Set) Intersection(other *Set) *Set {
	result := NewSet()
	for item := range s.items {
		if other.Contains(item) {
			result.Add(item)
		}
	}
	return result
}

func (s *Set) Difference(other *Set) *Set {
	result := NewSet()
	for item := range s.items {
		if !other.Contains(item) {
			result.Add(item)
		}
	}
	return result
}

func setOperations() {
	fmt.Println("\n=== SET ===")
	
	set1 := NewSet()
	set1.Add(1)
	set1.Add(2)
	set1.Add(3)
	
	fmt.Println("Contains 2:", set1.Contains(2))
	fmt.Println("Size:", set1.Size())
	
	set1.Remove(2)
	
	set2 := NewSet()
	set2.Add(3)
	set2.Add(4)
	set2.Add(5)
	
	union := set1.Union(set2)
	intersection := set1.Intersection(set2)
	difference := set1.Difference(set2)
	
	fmt.Println("Union:", union.Items())
	fmt.Println("Intersection:", intersection.Items())
	fmt.Println("Difference:", difference.Items())
}

// ============================================================================
// 11. TREE - Binary Search Tree implementation
// ============================================================================

type TreeNode struct {
	Value int
	Left  *TreeNode
	Right *TreeNode
}

type BST struct {
	Root *TreeNode
}

func (t *BST) Insert(value int) {
	t.Root = insertNode(t.Root, value)
}

func insertNode(node *TreeNode, value int) *TreeNode {
	if node == nil {
		return &TreeNode{Value: value}
	}
	if value < node.Value {
		node.Left = insertNode(node.Left, value)
	} else if value > node.Value {
		node.Right = insertNode(node.Right, value)
	}
	return node
}

func (t *BST) Search(value int) bool {
	return searchNode(t.Root, value)
}

func searchNode(node *TreeNode, value int) bool {
	if node == nil {
		return false
	}
	if value == node.Value {
		return true
	}
	if value < node.Value {
		return searchNode(node.Left, value)
	}
	return searchNode(node.Right, value)
}

func (t *BST) InOrder(fn func(int)) {
	inOrderTraversal(t.Root, fn)
}

func inOrderTraversal(node *TreeNode, fn func(int)) {
	if node != nil {
		inOrderTraversal(node.Left, fn)
		fn(node.Value)
		inOrderTraversal(node.Right, fn)
	}
}

func (t *BST) PreOrder(fn func(int)) {
	preOrderTraversal(t.Root, fn)
}

func preOrderTraversal(node *TreeNode, fn func(int)) {
	if node != nil {
		fn(node.Value)
		preOrderTraversal(node.Left, fn)
		preOrderTraversal(node.Right, fn)
	}
}

func (t *BST) PostOrder(fn func(int)) {
	postOrderTraversal(t.Root, fn)
}

func postOrderTraversal(node *TreeNode, fn func(int)) {
	if node != nil {
		postOrderTraversal(node.Left, fn)
		postOrderTraversal(node.Right, fn)
		fn(node.Value)
	}
}

func treeOperations() {
	fmt.Println("\n=== BINARY SEARCH TREE ===")
	
	tree := &BST{}
	
	tree.Insert(5)
	tree.Insert(3)
	tree.Insert(7)
	tree.Insert(1)
	tree.Insert(4)
	
	fmt.Println("Search 4:", tree.Search(4))
	fmt.Println("Search 10:", tree.Search(10))
	
	fmt.Print("In-order: ")
	tree.InOrder(func(v int) { fmt.Print(v, " ") })
	fmt.Println()
	
	fmt.Print("Pre-order: ")
	tree.PreOrder(func(v int) { fmt.Print(v, " ") })
	fmt.Println()
	
	fmt.Print("Post-order: ")
	tree.PostOrder(func(v int) { fmt.Print(v, " ") })
	fmt.Println()
}

// ============================================================================
// 12. GRAPH - Adjacency list implementation
// ============================================================================

type Graph struct {
	vertices map[int][]int
}

func NewGraph() *Graph {
	return &Graph{vertices: make(map[int][]int)}
}

func (g *Graph) AddVertex(v int) {
	if _, exists := g.vertices[v]; !exists {
		g.vertices[v] = []int{}
	}
}

func (g *Graph) AddEdge(v1, v2 int) {
	g.AddVertex(v1)
	g.AddVertex(v2)
	g.vertices[v1] = append(g.vertices[v1], v2)
	g.vertices[v2] = append(g.vertices[v2], v1) // Undirected
}

func (g *Graph) BFS(start int, fn func(int)) {
	visited := make(map[int]bool)
	queue := []int{start}
	visited[start] = true
	
	for len(queue) > 0 {
		vertex := queue[0]
		queue = queue[1:]
		fn(vertex)
		
		for _, neighbor := range g.vertices[vertex] {
			if !visited[neighbor] {
				visited[neighbor] = true
				queue = append(queue, neighbor)
			}
		}
	}
}

func (g *Graph) DFS(start int, fn func(int)) {
	visited := make(map[int]bool)
	g.dfsHelper(start, visited, fn)
}

func (g *Graph) dfsHelper(vertex int, visited map[int]bool, fn func(int)) {
	visited[vertex] = true
	fn(vertex)
	
	for _, neighbor := range g.vertices[vertex] {
		if !visited[neighbor] {
			g.dfsHelper(neighbor, visited, fn)
		}
	}
}

func graphOperations() {
	fmt.Println("\n=== GRAPH ===")
	
	graph := NewGraph()
	
	graph.AddEdge(1, 2)
	graph.AddEdge(1, 3)
	graph.AddEdge(2, 4)
	graph.AddEdge(3, 4)
	graph.AddEdge(4, 5)
	
	fmt.Print("BFS: ")
	graph.BFS(1, func(v int) { fmt.Print(v, " ") })
	fmt.Println()
	
	fmt.Print("DFS: ")
	graph.DFS(1, func(v int) { fmt.Print(v, " ") })
	fmt.Println()
}

// ============================================================================
// 13. TRIE - Prefix tree for strings
// ============================================================================

type TrieNode struct {
	children map[rune]*TrieNode
	isEnd    bool
}

type Trie struct {
	root *TrieNode
}

func NewTrie() *Trie {
	return &Trie{root: &TrieNode{children: make(map[rune]*TrieNode)}}
}

func (t *Trie) Insert(word string) {
	node := t.root
	for _, ch := range word {
		if _, exists := node.children[ch]; !exists {
			node.children[ch] = &TrieNode{children: make(map[rune]*TrieNode)}
		}
		node = node.children[ch]
	}
	node.isEnd = true
}

func (t *Trie) Search(word string) bool {
	node := t.root
	for _, ch := range word {
		if _, exists := node.children[ch]; !exists {
			return false
		}
		node = node.children[ch]
	}
	return node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
	node := t.root
	for _, ch := range prefix {
		if _, exists := node.children[ch]; !exists {
			return false
		}
		node = node.children[ch]
	}
	return true
}

func trieOperations() {
	fmt.Println("\n=== TRIE ===")
	
	trie := NewTrie()
	
	trie.Insert("apple")
	trie.Insert("app")
	trie.Insert("application")
	
	fmt.Println("Search 'app':", trie.Search("app"))
	fmt.Println("Search 'appl':", trie.Search("appl"))
	fmt.Println("StartsWith 'app':", trie.StartsWith("app"))
	fmt.Println("StartsWith 'ban':", trie.StartsWith("ban"))
}

// ============================================================================
// 14. SORTING - Various sorting algorithms
// ============================================================================

func sortingOperations() {
	fmt.Println("\n=== SORTING ===")
	
	// Sort integers
	nums := []int{5, 2, 8, 1, 9, 3}
	sort.Ints(nums)
	fmt.Println("Sorted ints:", nums)
	
	// Sort strings
	strs := []string{"banana", "apple", "cherry"}
	sort.Strings(strs)
	fmt.Println("Sorted strings:", strs)
	
	// Sort in reverse
	sort.Sort(sort.Reverse(sort.IntSlice(nums)))
	fmt.Println("Reverse sorted:", nums)
	
	// Custom sorting
	people := []struct {
		Name string
		Age  int
	}{
		{"Alice", 30},
		{"Bob", 25},
		{"Charlie", 35},
	}
	
	sort.Slice(people, func(i, j int) bool {
		return people[i].Age < people[j].Age
	})
	fmt.Println("Sorted by age:", people)
	
	// Stable sort
	sort.SliceStable(people, func(i, j int) bool {
		return people[i].Name < people[j].Name
	})
	
	// Check if sorted
	fmt.Println("Is sorted:", sort.IntsAreSorted(nums))
	
	// Binary search (requires sorted slice)
	nums = []int{1, 2, 3, 5, 8, 9}
	index := sort.SearchInts(nums, 5)
	fmt.Println("Index of 5:", index)
}

// ============================================================================
// 15. CONCURRENT DATA STRUCTURES
// ============================================================================

func concurrentOperations() {
	fmt.Println("\n=== CONCURRENT DATA STRUCTURES ===")
	
	// sync.Map - concurrent map
	var sm sync.Map
	
	sm.Store("key1", "value1")
	sm.Store("key2", "value2")
	
	if val, ok := sm.Load("key1"); ok {
		fmt.Println("sync.Map value:", val)
	}
	
	sm.Delete("key2")
	
	sm.Range(func(key, value interface{}) bool {
		fmt.Printf("Key: %v, Value: %v\n", key, value)
		return true
	})
	
	// LoadOrStore
	actual, loaded := sm.LoadOrStore("key3", "value3")
	fmt.Println("Loaded:", loaded, "Value:", actual)
	
	// Channel-based queue
	ch := make(chan int, 10)
	go func() {
		for i := 0; i < 5; i++ {
			ch <- i
		}
		close(ch)
	}()
	
	for val := range ch {
		fmt.Println("Channel value:", val)
	}
	
	// Mutex-protected data structure
	type SafeCounter struct {
		mu    sync.Mutex
		count int
	}
	
	counter := &SafeCounter{}
	
	var wg sync.WaitGroup
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			counter.mu.Lock()
			counter.count++
			counter.mu.Unlock()
		}()
	}
	wg.Wait()
	fmt.Println("Final count:", counter.count)
	
	// RWMutex for read-heavy workloads
	type SafeCache struct {
		mu    sync.RWMutex
		cache map[string]string
	}
	
	cache := &SafeCache{cache: make(map[string]string)}
	
	// Write
	cache.mu.Lock()
	cache.cache["key"] = "value"
	cache.mu.Unlock()
	
	// Read (multiple readers allowed)
	cache.mu.RLock()
	val := cache.cache["key"]
	cache.mu.RUnlock()
	fmt.Println("Cache value:", val)
}

// ============================================================================
// 16. ADVANCED SLICE OPERATIONS
// ============================================================================

func advancedSliceOperations() {
	fmt.Println("\n=== ADVANCED SLICE OPERATIONS ===")
	
	// Slice tricks
	nums := []int{1, 2, 3, 4, 5}
	
	// Prepend
	nums = append([]int{0}, nums...)
	
	// Insert at index
	index := 3
	value := 99
	nums = append(nums[:index], append([]int{value}, nums[index:]...)...)
	
	// Delete element at index
	index = 2
	nums = append(nums[:index], nums[index+1:]...)
	
	// Delete range
	start, end := 1, 3
	nums = append(nums[:start], nums[end:]...)
	
	// Cut (remove and get)
	cut := nums[1]
	nums = append(nums[:1], nums[2:]...)
	fmt.Println("Cut value:", cut)
	
	// Expand at index
	index = 2
	nums = append(nums[:index], append(make([]int, 3), nums[index:]...)...)
	
	// Extend capacity
	nums = append(nums, make([]int, 5)...)[:len(nums)]
	
	// Filter in place
	n := 0
	for _, val := range nums {
		if val != 0 {
			nums[n] = val
			n++
		}
	}
	nums = nums[:n]
	
	// Deduplicate
	seen := make(map[int]bool)
	unique := nums[:0]
	for _, v := range nums {
		if !seen[v] {
			seen[v] = true
			unique = append(unique, v)
		}
	}
	
	// Rotate slice
	k := 2
	nums = append(nums[k:], nums[:k]...)
	
	// Shuffle (Fisher-Yates)
	// for i := len(nums) - 1; i > 0; i-- {
	// 	j := rand.Intn(i + 1)
	// 	nums[i], nums[j] = nums[j], nums[i]
	// }
	
	// Partition
	pivot := 5
	left := 0
	for right := 0; right < len(nums); right++ {
		if nums[right] < pivot {
			nums[left], nums[right] = nums[right], nums[left]
			left++
		}
	}
	
	// Merge two sorted slices
	a := []int{1, 3, 5}
	b := []int{2, 4, 6}
	merged := make([]int, 0, len(a)+len(b))
	i, j := 0, 0
	for i < len(a) && j < len(b) {
		if a[i] < b[j] {
			merged = append(merged, a[i])
			i++
		} else {
			merged = append(merged, b[j])
			j++
		}
	}
	merged = append(merged, a[i:]...)
	merged = append(merged, b[j:]...)
	fmt.Println("Merged:", merged)
	
	// Sliding window
	windowSize := 3
	for i := 0; i <= len(nums)-windowSize; i++ {
		window := nums[i : i+windowSize]
		fmt.Println("Window:", window)
	}
}

// ============================================================================
// 17. ADVANCED MAP OPERATIONS
// ============================================================================

func advancedMapOperations() {
	fmt.Println("\n=== ADVANCED MAP OPERATIONS ===")
	
	// Map of slices
	groups := make(map[string][]int)
	groups["even"] = append(groups["even"], 2, 4, 6)
	groups["odd"] = append(groups["odd"], 1, 3, 5)
	
	// Map of maps
	matrix := make(map[int]map[int]string)
	matrix[0] = make(map[int]string)
	matrix[0][0] = "a"
	
	// Map with custom key type
	type Point struct {
		X, Y int
	}
	pointMap := make(map[Point]string)
	pointMap[Point{1, 2}] = "location1"
	
	// Get keys
	m := map[string]int{"a": 1, "b": 2, "c": 3}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	fmt.Println("Keys:", keys)
	
	// Get values
	values := make([]int, 0, len(m))
	for _, v := range m {
		values = append(values, v)
	}
	fmt.Println("Values:", values)
	
	// Invert map
	inverted := make(map[int]string)
	for k, v := range m {
		inverted[v] = k
	}
	
	// Merge maps
	m1 := map[string]int{"a": 1, "b": 2}
	m2 := map[string]int{"b": 3, "c": 4}
	for k, v := range m2 {
		m1[k] = v
	}
	
	// Filter map
	filtered := make(map[string]int)
	for k, v := range m {
		if v > 1 {
			filtered[k] = v
		}
	}
	
	// Map reduce
	sum := 0
	for _, v := range m {
		sum += v
	}
	fmt.Println("Sum:", sum)
	
	// Default value with function
	getOrDefault := func(m map[string]int, key string, def int) int {
		if val, ok := m[key]; ok {
			return val
		}
		return def
	}
	fmt.Println("Default:", getOrDefault(m, "z", 100))
}

// ============================================================================
// 18. BIT SET - Efficient boolean array
// ============================================================================

type BitSet struct {
	bits []uint64
}

func NewBitSet(size int) *BitSet {
	return &BitSet{bits: make([]uint64, (size+63)/64)}
}

func (bs *BitSet) Set(pos int) {
	bs.bits[pos/64] |= 1 << (pos % 64)
}

func (bs *BitSet) Clear(pos int) {
	bs.bits[pos/64] &^= 1 << (pos % 64)
}

func (bs *BitSet) Test(pos int) bool {
	return (bs.bits[pos/64] & (1 << (pos % 64))) != 0
}

func (bs *BitSet) Flip(pos int) {
	bs.bits[pos/64] ^= 1 << (pos % 64)
}

func bitSetOperations() {
	fmt.Println("\n=== BIT SET ===")
	
	bs := NewBitSet(100)
	
	bs.Set(5)
	bs.Set(10)
	bs.Set(50)
	
	fmt.Println("Test 5:", bs.Test(5))
	fmt.Println("Test 7:", bs.Test(7))
	
	bs.Clear(5)
	fmt.Println("After clear 5:", bs.Test(5))
	
	bs.Flip(10)
	fmt.Println("After flip 10:", bs.Test(10))
}

// ============================================================================
// 19. BLOOM FILTER - Probabilistic data structure
// ============================================================================

type BloomFilter struct {
	bits []bool
	size int
	hash func(string, int) int
}

func NewBloomFilter(size int) *BloomFilter {
	return &BloomFilter{
		bits: make([]bool, size),
		size: size,
		hash: func(s string, seed int) int {
			h := seed
			for _, c := range s {
				h = h*31 + int(c)
			}
			return (h & 0x7FFFFFFF) % size
		},
	}
}

func (bf *BloomFilter) Add(item string) {
	for i := 0; i < 3; i++ {
		pos := bf.hash(item, i)
		bf.bits[pos] = true
	}
}

func (bf *BloomFilter) Contains(item string) bool {
	for i := 0; i < 3; i++ {
		pos := bf.hash(item, i)
		if !bf.bits[pos] {
			return false
		}
	}
	return true
}

func bloomFilterOperations() {
	fmt.Println("\n=== BLOOM FILTER ===")
	
	bf := NewBloomFilter(1000)
	
	bf.Add("apple")
	bf.Add("banana")
	bf.Add("cherry")
	
	fmt.Println("Contains 'apple':", bf.Contains("apple"))
	fmt.Println("Contains 'grape':", bf.Contains("grape"))
}

// ============================================================================
// 20. LRU CACHE - Least Recently Used cache
// ============================================================================

type LRUNode struct {
	key   string
	value interface{}
	prev  *LRUNode
	next  *LRUNode
}

type LRUCache struct {
	capacity int
	cache    map[string]*LRUNode
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
		cache:    make(map[string]*LRUNode),
		head:     head,
		tail:     tail,
	}
}

func (lru *LRUCache) Get(key string) (interface{}, bool) {
	if node, exists := lru.cache[key]; exists {
		lru.moveToFront(node)
		return node.value, true
	}
	return nil, false
}

func (lru *LRUCache) Put(key string, value interface{}) {
	if node, exists := lru.cache[key]; exists {
		node.value = value
		lru.moveToFront(node)
		return
	}
	
	if len(lru.cache) >= lru.capacity {
		lru.removeLRU()
	}
	
	node := &LRUNode{key: key, value: value}
	lru.cache[key] = node
	lru.addToFront(node)
}

func (lru *LRUCache) moveToFront(node *LRUNode) {
	lru.removeNode(node)
	lru.addToFront(node)
}

func (lru *LRUCache) addToFront(node *LRUNode) {
	node.next = lru.head.next
	node.prev = lru.head
	lru.head.next.prev = node
	lru.head.next = node
}

func (lru *LRUCache) removeNode(node *LRUNode) {
	node.prev.next = node.next
	node.next.prev = node.prev
}

func (lru *LRUCache) removeLRU() {
	node := lru.tail.prev
	lru.removeNode(node)
	delete(lru.cache, node.key)
}

func lruCacheOperations() {
	fmt.Println("\n=== LRU CACHE ===")
	
	cache := NewLRUCache(2)
	
	cache.Put("a", 1)
	cache.Put("b", 2)
	
	if val, ok := cache.Get("a"); ok {
		fmt.Println("Got 'a':", val)
	}
	
	cache.Put("c", 3) // Evicts "b"
	
	if _, ok := cache.Get("b"); !ok {
		fmt.Println("'b' was evicted")
	}
}

// ============================================================================
// MAIN FUNCTION
// ============================================================================

func main() {
	arrayOperations()
	sliceOperations()
	mapOperations()
	structOperations()
	linkedListOperations()
	ringOperations()
	heapOperations()
	stackOperations()
	queueOperations()
	setOperations()
	treeOperations()
	graphOperations()
	trieOperations()
	sortingOperations()
	concurrentOperations()
	advancedSliceOperations()
	advancedMapOperations()
	bitSetOperations()
	bloomFilterOperations()
	lruCacheOperations()
	
	fmt.Println("\n=== ALL DATA STRUCTURES COVERED ===")
}
```