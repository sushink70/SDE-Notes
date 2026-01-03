# ULTIMATE SPEED SHEETS - Career-Long Reference

## 🐍 PYTHON SPEED SHEET

```python

# ✅ All of these work on Leetcode
from collections import defaultdict, Counter, deque
from heapq import heappush, heappop
from bisect import bisect_left
import math
import re


# DATA STRUCTURES - INITIALIZATION

arr = []                              # Dynamic array
arr = [0] * n                         # Fixed size, O(n) init
matrix = [[0]*cols for _ in range(rows)]  # 2D array (CORRECT WAY)
# WRONG: [[0]*cols]*rows  # Creates shallow copies!

from collections import deque, defaultdict, Counter, OrderedDict
queue = deque()                       # Double-ended queue
stack = []                            # Use list as stack
hashmap = {}                          # Dictionary
hashmap = defaultdict(int)            # Auto-initialize to 0
hashmap = defaultdict(list)           # Auto-initialize to []
hashset = set()                       # Set
counter = Counter(arr)                # Frequency map

import heapq
min_heap = []                         # Min heap (default)
max_heap = []                         # Max heap (negate values)
heapq.heappush(max_heap, -val)        # For max heap


# COMMON OPERATIONS - TIME COMPLEXITY

# List
arr.append(x)                         # O(1) amortized
arr.pop()                             # O(1) - remove last
arr.pop(0)                            # O(n) - remove first (SLOW!)
arr.insert(i, x)                      # O(n)
arr[i]                                # O(1) - access
arr.reverse()                         # O(n) - in-place
reversed(arr)                         # O(1) - returns iterator

# Deque (use for queue operations)
queue.append(x)                       # O(1) - add right
queue.appendleft(x)                   # O(1) - add left
queue.pop()                           # O(1) - remove right
queue.popleft()                       # O(1) - remove left (QUEUE!)

# Dict
d[key] = val                          # O(1) average
d.get(key, default)                   # O(1) - safe access
key in d                              # O(1)
d.pop(key)                            # O(1)
d.items()                             # O(1) - returns view
d.keys()                              # O(1) - returns view
d.values()                            # O(1) - returns view

# Set
s.add(x)                              # O(1)
s.remove(x)                           # O(1) - KeyError if not exists
s.discard(x)                          # O(1) - no error
x in s                                # O(1)
s1 & s2                               # O(min(len(s1), len(s2))) - intersection
s1 | s2                               # O(len(s1) + len(s2)) - union
s1 - s2                               # O(len(s1)) - difference

# Heap
heapq.heappush(heap, x)               # O(log n)
heapq.heappop(heap)                   # O(log n) - pop min
heapq.heapify(arr)                    # O(n) - convert list to heap
heap[0]                               # O(1) - peek min (don't pop)


# SORTING & SEARCHING

arr.sort()                            # O(n log n) - in-place
sorted(arr)                           # O(n log n) - returns new list
sorted(arr, reverse=True)             # Descending
sorted(arr, key=lambda x: x[1])       # Custom key
arr.sort(key=lambda x: (x[0], -x[1])) # Multi-key (asc, desc)

import bisect
bisect.bisect_left(arr, x)            # O(log n) - leftmost insertion
bisect.bisect_right(arr, x)           # O(log n) - rightmost insertion
bisect.insort(arr, x)                 # O(n) - insert maintaining order


# ITERATION PATTERNS

for i in range(len(arr)):             # Index only
for val in arr:                       # Value only
for i, val in enumerate(arr):         # Index + value
for i in range(len(arr)-1, -1, -1):   # Reverse iteration
for key, val in d.items():            # Dict iteration
for k in d:                           # Dict keys only (faster)

# Two pointers
left, right = 0, len(arr) - 1
while left < right:
    # process
    left += 1
    right -= 1

# Sliding window
left = 0
for right in range(len(arr)):
    # expand window
    while condition:
        # shrink window
        left += 1


# STRING OPERATIONS
s.split()                             # O(n) - split by whitespace
s.split(',')                          # O(n) - split by delimiter
''.join(arr)                          # O(n) - join array of strings
s[start:end]                          # O(k) - slice, k = end-start
s[start:end:step]                     # Slice with step
s[::-1]                               # O(n) - reverse string
s.strip()                             # Remove leading/trailing whitespace
s.lower()                             # Lowercase
s.upper()                             # Uppercase
s.isalnum()                           # Check alphanumeric
s.isdigit()                           # Check if all digits
ord('a')                              # 97 - char to ASCII
chr(97)                               # 'a' - ASCII to char


# MATH & BIT OPERATIONS

import math
math.inf, -math.inf                   # Infinity
math.floor(x), math.ceil(x)           # Floor/ceiling
abs(x)                                # Absolute value
min(a, b, c), max(a, b, c)            # Min/max
pow(base, exp, mod)                   # (base^exp) % mod
divmod(a, b)                          # Returns (a//b, a%b)

# Bit operations
x & y                                 # AND
x | y                                 # OR
x ^ y                                 # XOR
~x                                    # NOT
x << k                                # Left shift (multiply by 2^k)
x >> k                                # Right shift (divide by 2^k)
bin(x)                                # Binary representation string
x.bit_count()                         # Count 1s (Python 3.10+)


# COMMON ALGORITHMS

# Binary Search Template
def binary_search(arr, target):
    left, right = 0, len(arr) - 1
    while left <= right:
        mid = left + (right - left) // 2  # Avoid overflow
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1

# DFS - Recursive
def dfs(node, visited):
    if node in visited:
        return
    visited.add(node)
    for neighbor in graph[node]:
        dfs(neighbor, visited)

# BFS - Iterative
def bfs(start):
    queue = deque([start])
    visited = {start}
    while queue:
        node = queue.popleft()
        for neighbor in graph[node]:
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)


# INPUT/OUTPUT (Competitive Programming)

# Fast input
import sys
input = sys.stdin.readline

n = int(input())                      # Single integer
arr = list(map(int, input().split())) # Array of integers
a, b = map(int, input().split())      # Multiple integers

# Output
print(ans)                            # Single value
print(*arr)                           # Array (space-separated)
print('\n'.join(map(str, arr)))       # Array (newline-separated)


# USEFUL BUILT-INS

all(iterable)                         # True if all elements True
any(iterable)                         # True if any element True
sum(iterable)                         # Sum of elements
len(iterable)                         # Length
zip(iter1, iter2)                     # Combine iterators
map(func, iterable)                   # Apply function
filter(func, iterable)                # Filter elements
```

---

## 🦀 RUST SPEED SHEET

```rust

// DATA STRUCTURES - INITIALIZATION

use std::collections::{HashMap, HashSet, BinaryHeap, VecDeque, BTreeMap};

let mut arr: Vec<i32> = Vec::new();              // Dynamic array
let mut arr = vec![0; n];                        // Fixed size with default
let mut matrix = vec![vec![0; cols]; rows];      // 2D array

let mut map: HashMap<i32, i32> = HashMap::new(); // Hash map
let mut set: HashSet<i32> = HashSet::new();      // Hash set
let mut min_heap: BinaryHeap<Reverse<i32>> = BinaryHeap::new(); // Min heap
let mut max_heap: BinaryHeap<i32> = BinaryHeap::new();          // Max heap
let mut queue: VecDeque<i32> = VecDeque::new();  // Double-ended queue
let mut btree: BTreeMap<i32, i32> = BTreeMap::new(); // Sorted map


// COMMON OPERATIONS

// Vec
arr.push(x);                    // O(1) amortized - add to end
arr.pop();                      // O(1) - remove from end, returns Option
arr[i];                         // O(1) - access (panics if out of bounds)
arr.get(i);                     // O(1) - safe access, returns Option
arr.len();                      // O(1) - length
arr.is_empty();                 // O(1) - check if empty
arr.reverse();                  // O(n) - in-place reverse
arr.insert(i, x);               // O(n) - insert at index
arr.remove(i);                  // O(n) - remove at index

// VecDeque (use for queue)
queue.push_back(x);             // O(1) - add to end
queue.push_front(x);            // O(1) - add to front
queue.pop_back();               // O(1) - remove from end
queue.pop_front();              // O(1) - remove from front (QUEUE!)

// HashMap
map.insert(k, v);               // O(1) average
map.get(&k);                    // O(1) - returns Option<&V>
map.contains_key(&k);           // O(1)
map.remove(&k);                 // O(1)
map.entry(k).or_insert(0);      // O(1) - get or create with default
*map.entry(k).or_insert(0) += 1; // Frequency counter pattern

// HashSet
set.insert(x);                  // O(1) average
set.contains(&x);               // O(1)
set.remove(&x);                 // O(1)

// BinaryHeap
use std::cmp::Reverse;
max_heap.push(x);               // O(log n)
max_heap.pop();                 // O(log n) - returns Option
max_heap.peek();                // O(1) - returns Option<&T>
min_heap.push(Reverse(x));      // For min heap


// SORTING & SEARCHING

arr.sort();                     // O(n log n) - ascending
arr.sort_by(|a, b| b.cmp(a));   // Descending
arr.sort_by_key(|x| x.0);       // Sort by key
arr.sort_unstable();            // Faster, not stable

// Binary search (arr must be sorted)
arr.binary_search(&x);          // Returns Result<usize, usize>
match arr.binary_search(&x) {
    Ok(i) => i,                 // Found at index i
    Err(i) => i,                // Not found, i is insertion point
}


// ITERATION PATTERNS

for val in &arr {}                    // Borrow elements
for val in &mut arr {}                // Mutable borrow
for val in arr {}                     // Consume (move) elements
for (i, val) in arr.iter().enumerate() {} // Index + value
for i in 0..n {}                      // Range [0, n)
for i in (0..n).rev() {}              // Reverse range

// Two pointers
let (mut left, mut right) = (0, arr.len() - 1);
while left < right {
    // process
    left += 1;
    right -= 1;
}

// Sliding window
let mut left = 0;
for right in 0..arr.len() {
    // expand
    while condition {
        left += 1; // shrink
    }
}


// STRING OPERATIONS

let s = String::from("hello");
let s: &str = "hello";                // String slice (immutable)

s.chars()                             // Iterator over chars
s.bytes()                             // Iterator over bytes
s.split_whitespace()                  // Split by whitespace
s.split(',')                          // Split by delimiter
s.lines()                             // Split by newlines
s.trim()                              // Remove leading/trailing whitespace
s.to_lowercase()                      // Lowercase (allocates new String)
s.to_uppercase()                      // Uppercase

// Collect
s.chars().collect::<Vec<char>>()      // String to Vec<char>
vec.iter().collect::<String>()        // Vec<char> to String
s.chars().rev().collect::<String>()   // Reverse string

// Character operations
c.is_alphabetic()
c.is_numeric()
c.to_digit(10)                        // Char to digit (returns Option)
(b'a' + 1) as char                    // 'b' - byte arithmetic


// MATH & BIT OPERATIONS

i32::MAX, i32::MIN                    // Max/min values
x.abs()                               // Absolute value
x.min(y), x.max(y)                    // Min/max
x.pow(exp)                            // Power
x.div_euclid(y)                       // Euclidean division
x.rem_euclid(y)                       // Euclidean remainder

// Bit operations
x & y                                 // AND
x | y                                 // OR
x ^ y                                 // XOR
!x                                    // NOT
x << k                                // Left shift
x >> k                                // Right shift
x.count_ones()                        // Count 1 bits
x.trailing_zeros()                    // Count trailing zeros


// COMMON ALGORITHMS

// Binary Search
fn binary_search(arr: &[i32], target: i32) -> Option<usize> {
    let (mut left, mut right) = (0, arr.len() as i32 - 1);
    while left <= right {
        let mid = left + (right - left) / 2;
        match arr[mid as usize].cmp(&target) {
            std::cmp::Ordering::Equal => return Some(mid as usize),
            std::cmp::Ordering::Less => left = mid + 1,
            std::cmp::Ordering::Greater => right = mid - 1,
        }
    }
    None
}

// DFS
fn dfs(node: i32, graph: &HashMap<i32, Vec<i32>>, visited: &mut HashSet<i32>) {
    if visited.contains(&node) { return; }
    visited.insert(node);
    if let Some(neighbors) = graph.get(&node) {
        for &neighbor in neighbors {
            dfs(neighbor, graph, visited);
        }
    }
}

// BFS
fn bfs(start: i32, graph: &HashMap<i32, Vec<i32>>) {
    let mut queue = VecDeque::new();
    let mut visited = HashSet::new();
    queue.push_back(start);
    visited.insert(start);
    while let Some(node) = queue.pop_front() {
        if let Some(neighbors) = graph.get(&node) {
            for &neighbor in neighbors {
                if !visited.contains(&neighbor) {
                    visited.insert(neighbor);
                    queue.push_back(neighbor);
                }
            }
        }
    }
}


// INPUT/OUTPUT

use std::io::{self, BufRead};

// Read single line
let mut input = String::new();
io::stdin().read_line(&mut input).unwrap();
let n: i32 = input.trim().parse().unwrap();

// Read array of integers
let arr: Vec<i32> = input.trim()
    .split_whitespace()
    .map(|x| x.parse().unwrap())
    .collect();

// Fast input (competitive programming)
let stdin = io::stdin();
let mut lines = stdin.lock().lines();
let line = lines.next().unwrap().unwrap();
```

---

## ⚡ C++ SPEED SHEET

```cpp
#include <iostream>
#include <vector>
#include <string>
#include <algorithm>
#include <map>
#include <unordered_map>
#include <set>
#include <unordered_set>
#include <queue>
#include <stack>
#include <deque>
#include <cmath>
using namespace std;


// DATA STRUCTURES - INITIALIZATION

vector<int> arr;                           // Dynamic array
vector<int> arr(n, 0);                     // Size n, init to 0
vector<vector<int>> matrix(rows, vector<int>(cols, 0)); // 2D array

map<int, int> ordered_map;                 // Ordered map (BST) O(log n)
unordered_map<int, int> hash_map;          // Hash map O(1) average
set<int> ordered_set;                      // Ordered set (BST) O(log n)
unordered_set<int> hash_set;               // Hash set O(1) average
priority_queue<int> max_heap;              // Max heap (default)
priority_queue<int, vector<int>, greater<int>> min_heap; // Min heap
queue<int> q;                              // Queue (FIFO)
stack<int> st;                             // Stack (LIFO)
deque<int> dq;                             // Double-ended queue


// COMMON OPERATIONS

// Vector
arr.push_back(x);              // O(1) amortized
arr.pop_back();                // O(1)
arr[i];                        // O(1) access
arr.size();                    // O(1)
arr.empty();                   // O(1)
arr.clear();                   // O(n)
arr.insert(arr.begin()+i, x);  // O(n) - insert at position
arr.erase(arr.begin()+i);      // O(n) - erase at position
arr.front();                   // O(1) - first element
arr.back();                    // O(1) - last element

// Deque (use for queue operations)
dq.push_back(x);               // O(1)
dq.push_front(x);              // O(1)
dq.pop_back();                 // O(1)
dq.pop_front();                // O(1) - QUEUE!

// Unordered Map (Hash Map)
hash_map[key] = val;           // O(1) average
hash_map.count(key);           // O(1) - returns 0 or 1
hash_map.find(key);            // O(1) - returns iterator
hash_map.erase(key);           // O(1)
hash_map[key]++;               // Auto-initialize to 0 for ints

// Unordered Set
hash_set.insert(x);            // O(1) average
hash_set.count(x);             // O(1) - returns 0 or 1
hash_set.erase(x);             // O(1)

// Priority Queue (Heap)
max_heap.push(x);              // O(log n)
max_heap.pop();                // O(log n)
max_heap.top();                // O(1) - peek

// Queue
q.push(x);                     // O(1)
q.pop();                       // O(1)
q.front();                     // O(1)

// Stack
st.push(x);                    // O(1)
st.pop();                      // O(1)
st.top();                      // O(1)


// SORTING & SEARCHING

sort(arr.begin(), arr.end());               // O(n log n) ascending
sort(arr.begin(), arr.end(), greater<int>()); // Descending
sort(arr.begin(), arr.end(), [](int a, int b) { 
    return a > b; 
}); // Custom comparator

reverse(arr.begin(), arr.end());            // O(n) reverse

// Binary search (arr must be sorted)
binary_search(arr.begin(), arr.end(), x);   // Returns true/false
lower_bound(arr.begin(), arr.end(), x);     // Iterator to first >= x
upper_bound(arr.begin(), arr.end(), x);     // Iterator to first > x


// ITERATION PATTERNS

for (int i = 0; i < n; i++) {}              // Index
for (int val : arr) {}                      // Value (copy)
for (int& val : arr) {}                     // Value (reference - can modify)
for (auto& [key, val] : map) {}             // Map iteration (C++17)

// Two pointers
int left = 0, right = arr.size() - 1;
while (left < right) {
    // process
    left++;
    right--;
}


// STRING OPERATIONS

string s = "hello";
s.length() or s.size();        // Length
s[i];                          // Access char
s.substr(start, len);          // Substring
s.find("sub");                 // Find substring (returns pos or string::npos)
s.append("world");             // Append
s += "world";                  // Append
s.erase(pos, len);             // Erase
s.insert(pos, "str");          // Insert

// String stream (for parsing)
#include <sstream>
stringstream ss(s);
string word;
while (ss >> word) {}          // Split by whitespace

// Character operations
isalpha(c), isdigit(c), isalnum(c)
tolower(c), toupper(c)
c - '0'                        // Char to int digit
'a' + 1                        // 'b'


// MATH & BIT OPERATIONS

INT_MAX, INT_MIN               // Max/min int
LLONG_MAX, LLONG_MIN           // Max/min long long
abs(x)                         // Absolute value
min(a, b), max(a, b)           // Min/max
pow(base, exp)                 // Power (returns double)
sqrt(x), ceil(x), floor(x)

// Bit operations
x & y                          // AND
x | y                          // OR
x ^ y                          // XOR
~x                             // NOT
x << k                         // Left shift
x >> k                         // Right shift
__builtin_popcount(x)          // Count 1 bits (GCC)
__builtin_clz(x)               // Count leading zeros


// COMMON ALGORITHMS

// Binary Search
int binary_search(vector<int>& arr, int target) {
    int left = 0, right = arr.size() - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// DFS
void dfs(int node, vector<vector<int>>& graph, vector<bool>& visited) {
    if (visited[node]) return;
    visited[node] = true;
    for (int neighbor : graph[node]) {
        dfs(neighbor, graph, visited);
    }
}

// BFS
void bfs(int start, vector<vector<int>>& graph) {
    queue<int> q;
    unordered_set<int> visited;
    q.push(start);
    visited.insert(start);
    while (!q.empty()) {
        int node = q.front();
        q.pop();
        for (int neighbor : graph[node]) {
            if (!visited.count(neighbor)) {
                visited.insert(neighbor);
                q.push(neighbor);
            }
        }
    }
}


// INPUT/OUTPUT (Fast I/O for Competitive Programming)

ios_base::sync_with_stdio(false);
cin.tie(NULL);

int n;
cin >> n;                              // Single integer

vector<int> arr(n);
for (int i = 0; i < n; i++) {
    cin >> arr[i];                     // Array input
}

cout << ans << "\n";                   // Output (use \n not endl)
```

---

## 🐹 GO SPEED SHEET

```go
package main
import (
    "fmt"
    "sort"
    "container/heap"
    "container/list"
    "strings"
    "math"
)


// DATA STRUCTURES - INITIALIZATION

arr := []int{}                         // Dynamic slice
arr := make([]int, n)                  // Slice size n, init to 0
matrix := make([][]int, rows)
for i := range matrix {
    matrix[i] = make([]int, cols)
}

hashMap := make(map[int]int)           // Map (hash table)
hashSet := make(map[int]bool)          // Set (use map[T]bool)
queue := list.New()                    // Doubly linked list (for queue)

// Min/Max Heap - requires custom implementation
type MinHeap []int
func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i] < h[j] }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(int)) }
func (h *MinHeap) Pop() interface{} {
    old := *h
    n := len(old)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

minHeap := &MinHeap{}
heap.Init(minHeap)


// COMMON OPERATIONS

// Slice
arr = append(arr, x)                   // O(1) amortized - add to end
arr = arr[:len(arr)-1]                 // O(1) - remove last (manual)
arr[i]                                 // O(1) - access
len(arr)                               // O(1) - length
cap(arr)                               // O(1) - capacity

// Map
hashMap[key] = val                     // O(1) average - insert/update
val, exists := hashMap[key]            // O(1) - check existence
delete(hashMap, key)                   // O(1) - delete

// Set (using map[T]bool)
hashSet[x] = true                      // O(1) - insert
_, exists := hashSet[x]                // O(1) - check membership
delete(hashSet, x)                     // O(1) - remove

// Heap
heap.Push(minHeap, x)                  // O(log n)
x := heap.Pop(minHeap).(int)           // O(log n)
(*minHeap)[0]                          // O(1) - peek min

// List (for queue/deque)
queue.PushBack(x)                      // O(1) - add to end
queue.PushFront(x)                     // O(1) - add to front
front := queue.Front()                 // O(1) - get front element
queue.Remove(front)                    // O(1) - remove element


// SORTING & SEARCHING

sort.Ints(arr)                         // O(n log n) - ascending
sort.Sort(sort.Reverse(sort.IntSlice(arr))) // Descending
sort.Slice(arr, func(i, j int) bool {  // Custom sort
    return arr[i] < arr[j]
})

// Binary search (arr must be sorted)
idx := sort.SearchInts(arr, x)         // Returns insertion index
if idx < len(arr) && arr[idx] == x {
    // found
}


// ITERATION PATTERNS

for i := 0; i < n; i++ {}              // Index
for i, val := range arr {}             // Index + value
for _, val := range arr {}             // Value only
for key, val := range hashMap {}       // Map iteration
for i := len(arr)-1; i >= 0; i-- {}    // Reverse

// Two pointers
left, right := 0, len(arr)-1
for left < right {
    // process
    left++
    right--
}


// STRING OPERATIONS

s := "hello"
len(s)                                 // Length
s[i]                                   // Access byte (not rune!)
runes := []rune(s)                     // Convert to runes for Unicode
string(runes)                          // Convert back

strings.Split(s, " ")                  // Split by delimiter
strings.Join(arr, " ")                 // Join slice
strings.Contains(s, "sub")             // Check substring
strings.ToLower(s)                     // Lowercase
strings.ToUpper(s)                     // Uppercase
strings.TrimSpace(s)                   // Trim whitespace

// String builder (efficient concatenation)
var sb strings.Builder
sb.WriteString("hello")
sb.WriteString(" world")
result := sb.String()

// Character operations
unicode.IsLetter(r)
unicode.IsDigit(r)
r >= 'a' && r <= 'z'                   // Check lowercase


// MATH & BIT OPERATIONS

math.MaxInt, math.MinInt               // Max/min int (Go 1.17+)
math.Abs(float64(x))                   // Absolute (converts to float)
math.Max(a, b), math.Min(a, b)         // Max/min (float64 only)
// For int max/min:
func min(a, b int) int { if a < b { return a }; return b }
func max(a, b int) int { if a > b { return a }; return b }

math.Pow(base, exp)                    // Power (float64)
math.Sqrt(x)                           // Square root
math.Floor(x), math.Ceil(x)            // Floor/ceiling

// Bit operations
x & y                                  // AND
x | y                                  // OR
x ^ y                                  // XOR
^x                                     // NOT
x << k                                 // Left shift
x >> k                                 // Right shift


// COMMON ALGORITHMS

// Binary Search
func binarySearch(arr []int, target int) int {
    left, right := 0, len(arr)-1
    for left <= right {
        mid := left + (right-left)/2
        if arr[mid] == target {
            return mid
        } else if arr[mid] < target {
            left = mid + 1
        } else {
            right = mid - 1
        }
    }
    return -1
}

// DFS
func dfs(node int, graph map[int][]int, visited map[int]bool) {
    if visited[node] {
        return
    }
    visited[node] = true
    for _, neighbor := range graph[node] {
        dfs(neighbor, graph, visited)
    }
}

// BFS
func bfs(start int, graph map[int][]int) {
    queue := []int{start}
    visited := map[int]bool{start: true}
    for len(queue) > 0 {
        node := queue[0]
        queue = queue[1:]
        for _, neighbor := range graph[node] {
            if !visited[neighbor] {
                visited[neighbor] = true
                queue = append(queue, neighbor)
            }
        }
    }
}


// INPUT/OUTPUT

var n int
fmt.Scan(&n)                           // Single integer

var arr []int
for i := 0; i < n; i++ {
    var x int
    fmt.Scan(&x)
    arr = append(arr, x)
}

fmt.Println(ans)                       // Output
```

---

## 🔧 C SPEED SHEET

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <limits.h>
#include <math.h>


// DATA STRUCTURES - INITIALIZATION (Manual Implementation Required)

// Dynamic array (manual)
int* arr = (int*)malloc(n * sizeof(int));
int** matrix = (int**)malloc(rows * sizeof(int*));
for (int i = 0; i < rows; i++) {
    matrix[i] = (int*)malloc(cols * sizeof(int));
}

// Remember to free!
free(arr);
for (int i = 0; i < rows; i++) free(matrix[i]);
free(matrix);

// Stack (array-based)
int stack[MAX_SIZE];
int top = -1;

// Queue (array-based)
int queue[MAX_SIZE];
int front = 0, rear = -1;


// COMMON OPERATIONS

// Array operations
arr[i]                         // O(1) - access
memset(arr, 0, n * sizeof(int)); // O(n) - initialize to 0
memcpy(dest, src, n * sizeof(int)); // O(n) - copy array

// Stack operations (manual)
stack[++top] = x;              // Push
int x = stack[top--];          // Pop
int x = stack[top];            // Peek
bool empty = (top == -1);      // Check empty

// Queue operations (circular, manual)
queue[++rear % MAX_SIZE] = x;  // Enqueue
int x = queue[front++ % MAX_SIZE]; // Dequeue


// SORTING & SEARCHING

// qsort (standard library)
int compare(const void* a, const void* b) {
    return (*(int*)a - *(int*)b); // Ascending
}
qsort(arr, n, sizeof(int), compare);

// Binary search (arr must be sorted)
int* found = (int*)bsearch(&key, arr, n, sizeof(int), compare);


// STRING OPERATIONS

char s[100];
strlen(s)                      // Length
strcpy(dest, src)              // Copy
strcat(dest, src)              // Concatenate
strcmp(s1, s2)                 // Compare (0 if equal)
strchr(s, 'c')                 // Find character
strstr(s, "sub")               // Find substring
strtok(s, " ")                 // Tokenize

// Character operations
#include <ctype.h>
isalpha(c), isdigit(c), isalnum(c)
tolower(c), toupper(c)
c - '0'                        // Char to int digit


// MATH & BIT OPERATIONS

INT_MAX, INT_MIN               // Max/min int
LLONG_MAX, LLONG_MIN           // Max/min long long
abs(x)                         // Absolute value
fabs(x)                        // Absolute (float/double)
pow(base, exp)                 // Power
sqrt(x), ceil(x), floor(x)

#define MAX(a,b) ((a) > (b) ? (a) : (b))
#define MIN(a,b) ((a) < (b) ? (a) : (b))

// Bit operations
x & y                          // AND
x | y                          // OR
x ^ y                          // XOR
~x                             // NOT
x << k                         // Left shift
x >> k                         // Right shift
__builtin_popcount(x)          // Count 1 bits (GCC)


// COMMON ALGORITHMS

// Binary Search
int binary_search(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        else if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}

// DFS (adjacency list with array of linked lists)
void dfs(int node, int** graph, int* graphSize, bool* visited) {
    if (visited[node]) return;
    visited[node] = true;
    for (int i = 0; i < graphSize[node]; i++) {
        dfs(graph[node][i], graph, graphSize, visited);
    }
}


// INPUT/OUTPUT

int n;
scanf("%d", &n);               // Single integer

int arr[100];
for (int i = 0; i < n; i++) {
    scanf("%d", &arr[i]);      // Array input
}

printf("%d\n", ans);           // Output integer
printf("%lld\n", ans);         // Output long long
```

---

## 🎯 QUICK REFERENCE SUMMARY

```
┌─────────────────────────────────────────────────────────────┐
│           OPERATION TIME COMPLEXITIES (Universal)           │
├─────────────────────────────────────────────────────────────┤
│ Array access:              O(1)                             │
│ Array search (unsorted):   O(n)                             │
│ Array search (sorted):     O(log n)  [binary search]        │
│ Array insert/delete:       O(n)      [need to shift]        │
│                                                             │
│ Hash map get/set/delete:   O(1) average, O(n) worst         │
│ Hash set operations:       O(1) average, O(n) worst         │
│                                                             │
│ Heap push/pop:             O(log n)                         │
│ Heap peek:                 O(1)                             │
│                                                             │
│ Sorting:                   O(n log n) [comparison-based]    │
│ BFS/DFS:                   O(V + E)   [V=vertices, E=edges] │
│ Dynamic Programming:       O(n²) or O(n) typically          │
└─────────────────────────────────────────────────────────────┘
```

**Save these sheets. They're your career toolkit. Print and keep near desk for first 3 months of practice.**

## DSA Speed Sheet: Comprehensive Quick Reference

This speed sheet covers core Data Structures and Algorithms (DSA) topics for interviews, revision, or quick lookups. It includes key concepts, operations with time/space complexities (assuming standard implementations), common patterns, and tips. Use Big O notation for asymptotics: **T(n)** for time, **S(n)** for space.

## 1. Big O Notation Basics

| Notation | Description | Example |
|----------|-------------|---------|
| O(1) | Constant | Array access |
| O(log n) | Logarithmic | Binary search |
| O(n) | Linear | Single loop |
| O(n log n) | Linearithmic | Merge sort |
| O(n²) | Quadratic | Nested loops |
| O(2ⁿ) | Exponential | Recursive Fibonacci (naive) |

**Tips**: Amortized analysis for dynamic arrays (e.g., resize in O(1) avg). Drop constants/low-order terms.

## 2. Arrays & Strings

**Arrays**: Contiguous memory, fixed/random access.  
**Strings**: Immutable arrays of chars (in many langs).

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Access (index i) | O(1) | O(1) | - |
| Insert/Delete (end) | O(1) amortized | O(n) | Dynamic arrays (e.g., Python lists) |
| Insert/Delete (middle) | O(n) | O(n) | Shift elements |
| Search (unsorted) | O(n) | O(1) | Linear scan |
| Search (sorted) | O(log n) | O(1) | Binary search |
| Subarray sum | O(n) | O(1) | Prefix sums for range queries |

**Common Patterns**:

- Two pointers (e.g., reverse, palindrome): O(n) time.
- Sliding window (e.g., max substring): O(n) time.
- Prefix/suffix arrays for hashing (e.g., string matching).

**Tips**: Use arrays for cache-friendly access. For strings, consider immutability (e.g., Java StringBuilder for mutations).

## 3. Linked Lists

**Singly/Doubly**: Nodes with value + pointer(s). Head/tail for access.

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Access (index i) | O(n) | O(1) | Traverse from head |
| Insert/Delete (head) | O(1) | O(1) | Update pointers |
| Insert/Delete (tail) | O(1) | O(1) | With tail pointer |
| Insert/Delete (middle) | O(n) | O(1) | Find node + update |
| Search | O(n) | O(1) | Linear |

**Common Patterns**:

- Cycle detection: Floyd's tortoise-hare (O(n) time, O(1) space).
- Reverse: Iterative (O(n) time) or recursive.
- Merge two sorted: Dummy node (O(n) time).

**Tips**: Use dummy nodes for edge cases (empty list). Space: O(n) total for list.

## 4. Stacks & Queues

**Stack**: LIFO (push/pop).  
**Queue**: FIFO (enqueue/dequeue). Deque for both.

| Operation | Stack Time | Queue Time | Space | Impl Notes |
|-----------|------------|------------|-------|------------|
| Push/Enqueue | O(1) | O(1) | O(1) | Array or linked list |
| Pop/Dequeue | O(1) | O(1) | O(1) | - |
| Peek/Front | O(1) | O(1) | O(1) | - |
| Search | O(n) | O(n) | O(1) | Not efficient |

**Common Patterns**:

- Stack: Valid parentheses (O(n)), next greater element (monotonic stack).
- Queue: BFS (level order), sliding window max (deque).
- Priority Queue (Heap): Min/max heap for Dijkstra, median finder.

**Tips**: Python: `list` for stack, `collections.deque` for queue (O(1) both ends). Heaps: `heapq` (min-heap).

## 5. Trees

**Binary Tree**: ≤2 children/node. BST: sorted, balanced ~O(log n).

| Operation | Unbalanced Time | Balanced Time | Space | Notes |
|-----------|-----------------|----------------|-------|-------|
| Traverse (in/pre/post/order) | O(n) | O(n) | O(h) | h=height (O(n) worst) |
| Insert (BST) | O(h) | O(log n) | O(1) | - |
| Delete (BST) | O(h) | O(log n) | O(1) | Handle 0/1/2 children |
| Search (BST) | O(h) | O(log n) | O(1) | - |
| Height/LCA | O(n) | O(log n) | O(h) | - |

**Common Patterns**:

- Level order: BFS queue (O(n)).
- Diameter: 2 DFS heights (O(n)).
- Serialize/Deserialize: Preorder + markers.
- Balanced Trees: AVL/Red-Black (self-balancing).

**Tips**: Recursion for traversal. Morris traversal: O(1) space inorder. h = O(log n) for balanced.

## 6. Graphs

**Adj List**: {node: [neighbors]}. Directed/Undirected, Weighted.

| Operation | Time | Space | Notes |
|-----------|------|-------|-------|
| Add Edge | O(1) | O(1) | - |
| Traverse (DFS/BFS) | O(V+E) | O(V) | V=vertices, E=edges |
| Shortest Path (unweighted) | O(V+E) | O(V) | BFS |
| Shortest Path (weighted) | O((V+E) log V) | O(V) | Dijkstra (PQ) |
| Detect Cycle | O(V+E) | O(V) | DFS (recursion stack) or topo sort |
| Topo Sort | O(V+E) | O(V) | Kahn's (indegrees) or DFS |

**Common Patterns**:

- Union-Find (DSU): For connectivity (O(α(n)) ~O(1) amortized).
- MST: Kruskal/Prim (O(E log V)).
- Bellman-Ford: Negative weights (O(VE)).

**Tips**: Adj list for sparse graphs (space O(V+E)). DFS recursion depth O(V). Handle disconnected components.

## 7. Sorting Algorithms

| Algorithm | Time (Avg/Worst) | Space | Stable? | Notes |
|-----------|------------------|-------|---------|-------|
| Bubble | O(n²)/O(n²) | O(1) | Yes | Simple, rarely used |
| Insertion | O(n²)/O(n²) | O(1) | Yes | Good for small/nearly sorted |
| Selection | O(n²)/O(n²) | O(1) | No | - |
| Merge | O(n log n)/O(n log n) | O(n) | Yes | Divide-conquer |
| Quick | O(n log n)/O(n²) | O(log n) | No | Pivot choice matters |
| Heap | O(n log n)/O(n log n) | O(1) | No | In-place |
| Counting/Radix | O(n+k)/O(n+k) | O(n+k) | Yes | k=range, non-comparison |

**Tips**: Use built-ins (e.g., `sorted()` in Python: Timsort, O(n log n)). Stable preserves order.

## 8. Searching Algorithms

| Algorithm | Time | Space | Prerequisites | Notes |
|-----------|------|-------|---------------|-------|
| Linear | O(n) | O(1) | None | Unsorted |
| Binary | O(log n) | O(1) | Sorted | Iterative/recursive |
| Ternary | O(log₃ n) | O(1) | Sorted | Divides into 3 |
| Jump | O(√n) | O(1) | Sorted | Block size √n |
| Exponential | O(log n) | O(1) | Sorted, unimodal | Double interval |

**Tips**: Binary for sorted arrays. Hash tables for avg O(1) search.

## 9. Hashing

**Hash Table**: Key-value, hash function + chaining/resize.

| Operation | Avg Time | Worst Time | Space |
|-----------|----------|------------|-------|
| Insert | O(1) | O(n) | O(n) |
| Delete | O(1) | O(n) | O(n) |
| Search | O(1) | O(n) | O(n) |

**Common Patterns**:

- Collision: Chaining (lists) or open addressing (linear probing).
- Substring anagram: Sliding window + freq map.
- LRU Cache: Hash + DLL (O(1) all ops).

**Tips**: Load factor ~0.7. Python: `dict`. Handle collisions for worst-case.

## 10. Dynamic Programming (DP)

**Memoization/Tabulation**: Overlapping subproblems + optimal substructure.

| Type | Time | Space | Optimization |
|------|------|-------|--------------|
| 0/1 Knapsack | O(nW) | O(nW) | O(W) space |
| Fibonacci | O(n) | O(n) | O(1) space |
| LCS | O(mn) | O(mn) | O(min(m,n)) |
| Matrix Chain | O(n³) | O(n²) | - |

**Common Patterns**:

- 1D DP: House robber (O(n) time/space).
- 2D DP: Edit distance (O(mn)).
- State: dp[i][j] = optimal for subproblem i,j.

**Tips**: Identify recurrence → memoize → tabulate bottom-up. Space optimize by using prev row.

## 11. Greedy Algorithms

**Local optimum → global**: No backtracking.

| Problem | Greedy Choice | Time |
|---------|---------------|------|
| Activity Selection | Earliest finish | O(n log n) |
| Huffman Coding | Min freq merge | O(n log n) |
| Fractional Knapsack | Value/weight ratio | O(n log n) |
| Dijkstra | Min dist edge | O((V+E) log V) |

**Tips**: Prove greedy works (exchange argument). Not for all (e.g., 0/1 knapsack).

## 12. Common Interview Patterns & Tips

| Pattern | Key Idea | Example Problems |
|---------|----------|------------------|
| Two Pointers | Slow/fast, left/right | Container with most water, Remove duplicates |
| Sliding Window | Expand/shrink | Longest substring without repeat, Max sum subarray |
| Backtracking | Try/undo | Subsets, N-Queens, Permutations |
| Bit Manipulation | Masks, shifts | Single number, Subsets (2^n) |
| Math/Number Theory | Primes, GCD | Sieve of Eratosthenes, Euclidean algo |
| Design | Scale, consistency | LRU Cache, TinyURL |

**General Tips**:

- **Complexity**: Always state T/S. Optimize space (in-place where possible).
- **Edge Cases**: Empty input, single element, duplicates, overflow.
- **Languages**: Python (easy), C++ (fast), Java (OOP).
- **Practice**: LeetCode (blind 75), Cracking the Coding Interview.
- **Debug**: Draw examples, dry-run code.

This sheet is concise yet comprehensive—print/fold for speed! For deeper dives, refer to CLRS or online resources.