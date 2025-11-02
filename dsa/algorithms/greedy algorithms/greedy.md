# Comprehensive Guide to Greedy Algorithm Implementation in Go

## 1. Core Concepts

**Greedy algorithms** make locally optimal choices at each step, hoping to find a global optimum. They work when:
- Local optimal choices lead to global optimum (greedy choice property)
- Optimal solution contains optimal solutions to subproblems (optimal substructure)

**Key characteristics:**
- Irrevocable decisions at each step
- No backtracking
- Fast but not always optimal
- Prove correctness before implementation

## 2. Fundamental Patterns

### 2.1 Activity Selection Pattern
Choose activities that don't overlap, maximizing count.

```go
type Activity struct {
    start, end int
}

func maxActivities(activities []Activity) []Activity {
    sort.Slice(activities, func(i, j int) bool {
        return activities[i].end < activities[j].end
    })
    
    result := []Activity{activities[0]}
    lastEnd := activities[0].end
    
    for i := 1; i < len(activities); i++ {
        if activities[i].start >= lastEnd {
            result = append(result, activities[i])
            lastEnd = activities[i].end
        }
    }
    return result
}
```

### 2.2 Fractional Knapsack Pattern
Maximize value with weight constraint, items divisible.

```go
type Item struct {
    value, weight float64
}

func fractionalKnapsack(items []Item, capacity float64) float64 {
    sort.Slice(items, func(i, j int) bool {
        return items[i].value/items[i].weight > items[j].value/items[j].weight
    })
    
    totalValue := 0.0
    for _, item := range items {
        if capacity >= item.weight {
            totalValue += item.value
            capacity -= item.weight
        } else {
            totalValue += item.value * (capacity / item.weight)
            break
        }
    }
    return totalValue
}
```

## 3. Classic Problems

### 3.1 Huffman Coding
Optimal prefix-free encoding for compression.

```go
type HuffmanNode struct {
    char      rune
    freq      int
    left, right *HuffmanNode
}

type MinHeap []*HuffmanNode

func (h MinHeap) Len() int           { return len(h) }
func (h MinHeap) Less(i, j int) bool { return h[i].freq < h[j].freq }
func (h MinHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *MinHeap) Push(x interface{}) { *h = append(*h, x.(*HuffmanNode)) }
func (h *MinHeap) Pop() interface{} {
    old, n := *h, len(*h)
    x := old[n-1]
    *h = old[0 : n-1]
    return x
}

func buildHuffmanTree(freq map[rune]int) *HuffmanNode {
    h := &MinHeap{}
    heap.Init(h)
    
    for char, f := range freq {
        heap.Push(h, &HuffmanNode{char: char, freq: f})
    }
    
    for h.Len() > 1 {
        left := heap.Pop(h).(*HuffmanNode)
        right := heap.Pop(h).(*HuffmanNode)
        merged := &HuffmanNode{
            freq:  left.freq + right.freq,
            left:  left,
            right: right,
        }
        heap.Push(h, merged)
    }
    return heap.Pop(h).(*HuffmanNode)
}
```

### 3.2 Dijkstra's Algorithm
Shortest path in weighted graph (non-negative weights).

```go
type Edge struct {
    to, weight int
}

func dijkstra(graph [][]Edge, start int) []int {
    n := len(graph)
    dist := make([]int, n)
    for i := range dist {
        dist[i] = math.MaxInt32
    }
    dist[start] = 0
    
    pq := &PriorityQueue{}
    heap.Init(pq)
    heap.Push(pq, &Item{node: start, priority: 0})
    
    for pq.Len() > 0 {
        current := heap.Pop(pq).(*Item)
        u := current.node
        
        if current.priority > dist[u] {
            continue
        }
        
        for _, edge := range graph[u] {
            if newDist := dist[u] + edge.weight; newDist < dist[edge.to] {
                dist[edge.to] = newDist
                heap.Push(pq, &Item{node: edge.to, priority: newDist})
            }
        }
    }
    return dist
}
```

### 3.3 Minimum Spanning Tree (Kruskal's)
Connect all nodes with minimum total edge weight.

```go
type UnionFind struct {
    parent, rank []int
}

func NewUnionFind(n int) *UnionFind {
    parent, rank := make([]int, n), make([]int, n)
    for i := range parent {
        parent[i] = i
    }
    return &UnionFind{parent, rank}
}

func (uf *UnionFind) Find(x int) int {
    if uf.parent[x] != x {
        uf.parent[x] = uf.Find(uf.parent[x])
    }
    return uf.parent[x]
}

func (uf *UnionFind) Union(x, y int) bool {
    px, py := uf.Find(x), uf.Find(y)
    if px == py {
        return false
    }
    if uf.rank[px] < uf.rank[py] {
        uf.parent[px] = py
    } else if uf.rank[px] > uf.rank[py] {
        uf.parent[py] = px
    } else {
        uf.parent[py] = px
        uf.rank[px]++
    }
    return true
}

func kruskalMST(n int, edges [][3]int) int {
    sort.Slice(edges, func(i, j int) bool {
        return edges[i][2] < edges[j][2]
    })
    
    uf := NewUnionFind(n)
    totalWeight := 0
    
    for _, edge := range edges {
        if uf.Union(edge[0], edge[1]) {
            totalWeight += edge[2]
        }
    }
    return totalWeight
}
```

## 4. Interval Problems

### 4.1 Minimum Platforms
Find minimum platforms needed for trains.

```go
func minPlatforms(arrivals, departures []int) int {
    sort.Ints(arrivals)
    sort.Ints(departures)
    
    platforms, maxPlatforms := 0, 0
    i, j := 0, 0
    
    for i < len(arrivals) {
        if arrivals[i] <= departures[j] {
            platforms++
            maxPlatforms = max(maxPlatforms, platforms)
            i++
        } else {
            platforms--
            j++
        }
    }
    return maxPlatforms
}
```

### 4.2 Merge Intervals
Combine overlapping intervals.

```go
func mergeIntervals(intervals [][]int) [][]int {
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i][0] < intervals[j][0]
    })
    
    merged := [][]int{intervals[0]}
    
    for i := 1; i < len(intervals); i++ {
        last := merged[len(merged)-1]
        if intervals[i][0] <= last[1] {
            last[1] = max(last[1], intervals[i][1])
        } else {
            merged = append(merged, intervals[i])
        }
    }
    return merged
}
```

### 4.3 Non-overlapping Intervals
Remove minimum intervals to make rest non-overlapping.

```go
func eraseOverlapIntervals(intervals [][]int) int {
    sort.Slice(intervals, func(i, j int) bool {
        return intervals[i][1] < intervals[j][1]
    })
    
    count, end := 0, intervals[0][1]
    
    for i := 1; i < len(intervals); i++ {
        if intervals[i][0] < end {
            count++
        } else {
            end = intervals[i][1]
        }
    }
    return count
}
```

## 5. Optimization Problems

### 5.1 Job Sequencing with Deadlines
Maximize profit by scheduling jobs before deadlines.

```go
type Job struct {
    id, deadline, profit int
}

func jobSequencing(jobs []Job, maxDeadline int) int {
    sort.Slice(jobs, func(i, j int) bool {
        return jobs[i].profit > jobs[j].profit
    })
    
    slots := make([]bool, maxDeadline+1)
    totalProfit := 0
    
    for _, job := range jobs {
        for j := job.deadline; j > 0; j-- {
            if !slots[j] {
                slots[j] = true
                totalProfit += job.profit
                break
            }
        }
    }
    return totalProfit
}
```

### 5.2 Gas Station Circuit
Find starting station to complete circular route.

```go
func canCompleteCircuit(gas, cost []int) int {
    totalGas, totalCost, tank, start := 0, 0, 0, 0
    
    for i := range gas {
        totalGas += gas[i]
        totalCost += cost[i]
        tank += gas[i] - cost[i]
        
        if tank < 0 {
            start = i + 1
            tank = 0
        }
    }
    
    if totalGas < totalCost {
        return -1
    }
    return start
}
```

### 5.3 Jump Game II
Minimum jumps to reach end.

```go
func minJumps(nums []int) int {
    jumps, currentEnd, farthest := 0, 0, 0
    
    for i := 0; i < len(nums)-1; i++ {
        farthest = max(farthest, i+nums[i])
        
        if i == currentEnd {
            jumps++
            currentEnd = farthest
        }
    }
    return jumps
}
```

## 6. String & Array Problems

### 6.1 Minimum Coins (Coin Change Greedy)
Works only for canonical coin systems.

```go
func minCoins(coins []int, amount int) int {
    sort.Sort(sort.Reverse(sort.IntSlice(coins)))
    count := 0
    
    for _, coin := range coins {
        if amount >= coin {
            count += amount / coin
            amount %= coin
        }
    }
    
    if amount != 0 {
        return -1
    }
    return count
}
```

### 6.2 Partition Labels
Partition string into maximum parts where each letter appears in at most one part.

```go
func partitionLabels(s string) []int {
    last := make(map[byte]int)
    for i := range s {
        last[s[i]] = i
    }
    
    result := []int{}
    start, end := 0, 0
    
    for i := range s {
        end = max(end, last[s[i]])
        if i == end {
            result = append(result, end-start+1)
            start = i + 1
        }
    }
    return result
}
```

### 6.3 Reorganize String
Rearrange so no two adjacent characters are same.

```go
func reorganizeString(s string) string {
    freq := make(map[rune]int)
    for _, ch := range s {
        freq[ch]++
    }
    
    pq := &MaxHeap{}
    heap.Init(pq)
    for ch, f := range freq {
        heap.Push(pq, CharFreq{ch, f})
    }
    
    result := []rune{}
    var prev CharFreq
    
    for pq.Len() > 0 {
        current := heap.Pop(pq).(CharFreq)
        result = append(result, current.char)
        
        if prev.freq > 0 {
            heap.Push(pq, prev)
        }
        
        current.freq--
        prev = current
    }
    
    if len(result) != len(s) {
        return ""
    }
    return string(result)
}
```

## 7. Advanced Patterns

### 7.1 Two-Pass Greedy (Candy Distribution)
Each child gets candy, more candy for higher rating than neighbors.

```go
func candy(ratings []int) int {
    n := len(ratings)
    candies := make([]int, n)
    for i := range candies {
        candies[i] = 1
    }
    
    // Left to right
    for i := 1; i < n; i++ {
        if ratings[i] > ratings[i-1] {
            candies[i] = candies[i-1] + 1
        }
    }
    
    // Right to left
    for i := n - 2; i >= 0; i-- {
        if ratings[i] > ratings[i+1] {
            candies[i] = max(candies[i], candies[i+1]+1)
        }
    }
    
    total := 0
    for _, c := range candies {
        total += c
    }
    return total
}
```

### 7.2 Greedy with State (Best Time to Buy/Sell Stock)
Multiple transactions allowed.

```go
func maxProfit(prices []int) int {
    profit := 0
    for i := 1; i < len(prices); i++ {
        if prices[i] > prices[i-1] {
            profit += prices[i] - prices[i-1]
        }
    }
    return profit
}
```

### 7.3 Greedy with Sorting (Boats to Save People)
Minimum boats for people with weight limit.

```go
func numRescueBoats(people []int, limit int) int {
    sort.Ints(people)
    left, right := 0, len(people)-1
    boats := 0
    
    for left <= right {
        if people[left]+people[right] <= limit {
            left++
        }
        right--
        boats++
    }
    return boats
}
```

## 8. Proving Correctness

**Three-step approach:**
1. **Greedy choice property**: Show local optimum leads to global optimum
2. **Optimal substructure**: Prove problem has overlapping subproblems
3. **Exchange argument**: Show swapping greedy choice with other choice doesn't improve solution

**Example (Activity Selection):**
- Always choosing earliest finishing activity is optimal
- If optimal solution doesn't include earliest finishing, swap it in
- This creates more room for remaining activities

## 9. Common Pitfalls

- **Not all problems have greedy solutions** (0/1 Knapsack needs DP)
- **Sorting is often required** but adds O(n log n) complexity
- **Proving correctness is essential** - greedy looks right but may fail
- **Counter-examples expose flaws** in greedy approach

## 10. When NOT to Use Greedy

- **0/1 Knapsack**: Items indivisible (use DP)
- **Longest Common Subsequence**: No greedy property
- **Edit Distance**: Requires considering all possibilities
- **Subset Sum**: Exponential possibilities

## 11. Complexity Analysis

Most greedy algorithms:
- **Time**: O(n log n) for sorting + O(n) for greedy choices
- **Space**: O(1) to O(n) depending on auxiliary structures

## 12. Testing Strategy

```go
func TestGreedy(t *testing.T) {
    tests := []struct {
        name     string
        input    interface{}
        expected interface{}
    }{
        {"empty", []int{}, 0},
        {"single", []int{1}, 1},
        {"optimal", []int{1, 2, 3}, 6},
        {"edge_case", []int{-1, 0, 1}, 1},
    }
    
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            // Test implementation
        })
    }
}
```

**Summary**: Greedy algorithms excel when local optimality guarantees global optimality. Master pattern recognition, prove correctness, and know when to pivot to DP or other approaches.