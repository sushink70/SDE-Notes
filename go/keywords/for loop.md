# The Complete Guide to `for` Loops in Go
> *From fundamentals to production-grade mastery*

---

## Table of Contents
1. [The Philosophy: Go Has Only One Loop](#1-the-philosophy-go-has-only-one-loop)
2. [The Three Classic Forms](#2-the-three-classic-forms)
3. [The Infinite Loop](#3-the-infinite-loop)
4. [Range-Based Iteration](#4-range-based-iteration)
5. [Loop Control: break, continue, goto](#5-loop-control-break-continue-goto)
6. [Labels and Nested Loop Control](#6-labels-and-nested-loop-control)
7. [Iteration Patterns and Idioms](#7-iteration-patterns-and-idioms)
8. [Performance and Memory Internals](#8-performance-and-memory-internals)
9. [Concurrency Patterns with for Loops](#9-concurrency-patterns-with-for-loops)
10. [Real-World Implementations](#10-real-world-implementations)
11. [Common Pitfalls and Their Fixes](#11-common-pitfalls-and-their-fixes)
12. [Expert Mental Models](#12-expert-mental-models)

---

## 1. The Philosophy: Go Has Only One Loop

Go's designers made a radical simplification: **there is no `while`, no `do-while`, no `foreach` — only `for`.**

This is not a limitation. It is clarity by design. Every loop form in Go is a syntactic variant of one construct. Once you internalize all its forms, you hold complete mastery over iteration in Go.

```
for [init]; [condition]; [post] { ... }   // classic C-style
for [condition]              { ... }   // while-style
for                          { ... }   // infinite loop
for i, v := range collection { ... }  // range-based
```

---

## 2. The Three Classic Forms

### 2.1 Full Three-Component Form

```go
for init; condition; post {
    // body
}
```

```go
// Counting integers
for i := 0; i < 10; i++ {
    fmt.Println(i)
}
```

**Scoping Rule:** Variables declared in `init` are scoped to the loop block only.

```go
for i := 0; i < 5; i++ {
    fmt.Println(i)
}
// fmt.Println(i) → compile error: i undefined
```

**Multiple variables in init and post:**

```go
// Two pointers — classic DSA pattern
for left, right := 0, len(arr)-1; left < right; left, right = left+1, right-1 {
    arr[left], arr[right] = arr[right], arr[left]  // in-place reverse
}
```

**Expert insight:** The init and post clauses are *simple statements*, not arbitrary expressions. You can use short variable declarations, assignments, and increment/decrement — but not, say, `var` declarations.

### 2.2 Condition-Only Form (while-equivalent)

```go
for condition {
    // body
}
```

```go
// Reading until EOF — idiomatic in I/O pipelines
scanner := bufio.NewScanner(os.Stdin)
for scanner.Scan() {
    line := scanner.Text()
    process(line)
}
```

```go
// Binary search loop — condition form is cleaner here
lo, hi := 0, len(arr)-1
for lo <= hi {
    mid := lo + (hi-lo)/2   // overflow-safe midpoint
    if arr[mid] == target {
        return mid
    } else if arr[mid] < target {
        lo = mid + 1
    } else {
        hi = mid - 1
    }
}
```

**Why `lo + (hi-lo)/2` instead of `(lo+hi)/2`?**
Integer overflow. If lo=1e9 and hi=2e9, their sum overflows int32. This is a real production bug. Always use the safe form.

### 2.3 Minimal / Conditional Init-Post

You can omit parts freely:

```go
i := 0
for ; i < 10; {   // init and post omitted, semicolons optional when condition only
    i++
}
```

This is rarely idiomatic — prefer the condition-only form when init is outside the loop.

---

## 3. The Infinite Loop

```go
for {
    // runs forever until break or return
}
```

This is idiomatic in Go for:
- Server accept loops
- Worker goroutines
- Event dispatch loops
- State machines

```go
// HTTP server accept loop (simplified model)
for {
    conn, err := listener.Accept()
    if err != nil {
        log.Println("accept error:", err)
        continue
    }
    go handleConnection(conn)
}
```

```go
// Worker pool consumer — real-world goroutine pattern
func worker(id int, jobs <-chan Job, results chan<- Result) {
    for {
        job, ok := <-jobs
        if !ok {
            return  // channel closed, worker exits cleanly
        }
        results <- process(job)
    }
}
```

**Mental model:** An infinite loop is not a bug, it is a *deliberate contract* that "this process has no natural end." Servers, daemons, and event loops are naturally infinite — they terminate only on shutdown signals.

---

## 4. Range-Based Iteration

`range` is Go's iterator protocol. It works over: arrays, slices, maps, strings, channels, and (Go 1.22+) integers.

### 4.1 Range over Slice / Array

```go
nums := []int{10, 20, 30, 40}

// Both index and value
for i, v := range nums {
    fmt.Printf("nums[%d] = %d\n", i, v)
}

// Index only
for i := range nums {
    nums[i] *= 2  // mutate original — correct
}

// Value only (blank identifier)
for _, v := range nums {
    fmt.Println(v)
}
```

**Critical pitfall:** `v` is a *copy*. Mutating `v` does NOT mutate the slice.

```go
// WRONG — modifying copy, original unchanged
for _, v := range nums {
    v = 0  // useless
}

// CORRECT — use index
for i := range nums {
    nums[i] = 0
}
```

### 4.2 Range over String (Unicode-aware)

```go
s := "Hello, 世界"

// Range iterates over Unicode code points (runes), NOT bytes
for i, r := range s {
    fmt.Printf("index=%d rune=%c (U+%04X)\n", i, r, r)
}
```

Output shows index jumps by 3 for the Chinese characters (UTF-8 encoding). This is the correct, production-safe way to iterate strings.

```go
// Byte iteration — when you need raw bytes
for i := 0; i < len(s); i++ {
    fmt.Printf("%x ", s[i])
}
```

**Rule of thumb:** Use `range` for text processing. Use index-based for binary/network protocols.

### 4.3 Range over Map

```go
freq := map[string]int{"go": 3, "rust": 5, "c": 2}

for k, v := range freq {
    fmt.Printf("%s: %d\n", k, v)
}
```

**Critical property:** Map iteration order is deliberately randomized on every run. Never rely on it. If you need order, extract keys, sort, then iterate.

```go
// Ordered map iteration — production pattern
keys := make([]string, 0, len(freq))
for k := range freq {
    keys = append(keys, k)
}
sort.Strings(keys)
for _, k := range keys {
    fmt.Printf("%s: %d\n", k, freq[k])
}
```

### 4.4 Range over Channel

```go
ch := make(chan int, 5)
go func() {
    for i := 0; i < 5; i++ {
        ch <- i * i
    }
    close(ch)
}()

// Range over channel: reads until channel is closed
for v := range ch {
    fmt.Println(v)  // 0, 1, 4, 9, 16
}
```

**Expert rule:** Never range over a channel that is never closed. It will deadlock forever.

### 4.5 Range over Integer (Go 1.22+)

```go
// New in Go 1.22 — iterate over integer directly
for i := range 5 {
    fmt.Println(i)  // 0 1 2 3 4
}
```

This eliminates the noisy `for i := 0; i < n; i++` pattern for pure counting loops.

### 4.6 Range over Function (Go 1.23+ iterator protocol)

```go
// Go 1.23 range-over-func: custom iterators
func Fibonacci() func(yield func(int) bool) {
    return func(yield func(int) bool) {
        a, b := 0, 1
        for {
            if !yield(a) {
                return
            }
            a, b = b, a+b
        }
    }
}

for n := range Fibonacci() {
    if n > 100 {
        break
    }
    fmt.Println(n)
}
```

This is Go's answer to Rust's `Iterator` trait — lazy, composable sequences.

---

## 5. Loop Control: break, continue, goto

### 5.1 `break`

Exits the innermost loop immediately.

```go
// Finding first duplicate in a slice
func firstDuplicate(nums []int) (int, bool) {
    seen := make(map[int]bool)
    for _, n := range nums {
        if seen[n] {
            return n, true
        }
        seen[n] = true
    }
    return 0, false
}
```

### 5.2 `continue`

Skips the rest of the current iteration and moves to the next.

```go
// Process only even numbers — guard clause pattern
for i := 0; i < 20; i++ {
    if i%2 != 0 {
        continue  // skip odd
    }
    fmt.Println(i)
}
```

**Idiomatic pattern:** Use `continue` as a guard clause to reduce nesting. This is the loop-equivalent of early return.

```go
// Deep nesting — BAD
for _, line := range lines {
    if len(line) > 0 {
        if line[0] != '#' {
            process(line)
        }
    }
}

// Guard clause — GOOD
for _, line := range lines {
    if len(line) == 0 { continue }
    if line[0] == '#'  { continue }
    process(line)
}
```

### 5.3 `goto`

Jumps to a labeled statement. Controversial but valid in Go for specific low-level patterns.

```go
// Legitimate use: breaking out of deeply nested logic
func scanMatrix(matrix [][]int, target int) (int, int) {
    for i, row := range matrix {
        for j, val := range row {
            if val == target {
                goto found
            }
            _ = j
        }
        _ = i
    }
    return -1, -1
found:
    // post-processing
    return -1, -1 // simplified
}
```

**Expert opinion:** In modern Go, `goto` is rarely needed. Labeled `break`/`continue` (next section) handles 95% of the cases. Reserve `goto` for generated code or performance-critical state machines.

---

## 6. Labels and Nested Loop Control

The most underused feature of Go loops. Labels allow `break` and `continue` to target *outer* loops.

```go
outer:
    for i := 0; i < 5; i++ {
        for j := 0; j < 5; j++ {
            if i+j == 6 {
                break outer  // exits the outer loop entirely
            }
            fmt.Printf("(%d,%d) ", i, j)
        }
    }
```

```go
// Real-world: parsing a 2D grid, skip entire row on error
rows:
    for _, row := range grid {
        for _, cell := range row {
            if !isValid(cell) {
                continue rows  // skip remaining cells, go to next row
            }
            process(cell)
        }
    }
```

**DSA application — matrix search:**

```go
// Search row-sorted matrix
func searchMatrix(matrix [][]int, target int) bool {
    rows, cols := len(matrix), len(matrix[0])
    r, c := 0, cols-1  // start top-right

    for r < rows && c >= 0 {
        switch {
        case matrix[r][c] == target:
            return true
        case matrix[r][c] > target:
            c--
        default:
            r++
        }
    }
    return false
}
```

---

## 7. Iteration Patterns and Idioms

### 7.1 The Two-Pointer Pattern

```go
// Palindrome check — O(n) time, O(1) space
func isPalindrome(s string) bool {
    runes := []rune(s)
    for l, r := 0, len(runes)-1; l < r; l, r = l+1, r-1 {
        if runes[l] != runes[r] {
            return false
        }
    }
    return true
}
```

### 7.2 The Sliding Window Pattern

```go
// Maximum sum subarray of size k — O(n)
func maxSumWindow(arr []int, k int) int {
    if len(arr) < k {
        return 0
    }
    
    windowSum := 0
    for i := 0; i < k; i++ {
        windowSum += arr[i]
    }
    
    maxSum := windowSum
    for i := k; i < len(arr); i++ {
        windowSum += arr[i] - arr[i-k]  // slide: add new, remove old
        if windowSum > maxSum {
            maxSum = windowSum
        }
    }
    return maxSum
}
```

### 7.3 Prefix Sum with Loop

```go
// Build prefix sum array — basis for range queries
func buildPrefix(arr []int) []int {
    prefix := make([]int, len(arr)+1)
    for i, v := range arr {
        prefix[i+1] = prefix[i] + v
    }
    return prefix
}

// Range sum query: O(1)
func rangeSum(prefix []int, l, r int) int {
    return prefix[r+1] - prefix[l]
}
```

### 7.4 Accumulator / Reduction Pattern

```go
// Functional-style reduce using a for loop
func reduce[T, R any](slice []T, initial R, fn func(R, T) R) R {
    acc := initial
    for _, v := range slice {
        acc = fn(acc, v)
    }
    return acc
}

// Usage
sum := reduce([]int{1, 2, 3, 4, 5}, 0, func(a, b int) int { return a + b })
```

### 7.5 Chunking / Batch Processing

```go
// Process a large slice in batches of size n
func processInBatches(items []string, batchSize int, process func([]string)) {
    for i := 0; i < len(items); i += batchSize {
        end := i + batchSize
        if end > len(items) {
            end = len(items)
        }
        process(items[i:end])
    }
}
```

### 7.6 Retry Loop with Backoff

```go
// Exponential backoff — production-grade retry
func withRetry(maxAttempts int, fn func() error) error {
    var err error
    delay := time.Millisecond * 100

    for attempt := 0; attempt < maxAttempts; attempt++ {
        if err = fn(); err == nil {
            return nil
        }
        if attempt < maxAttempts-1 {
            time.Sleep(delay)
            delay *= 2  // exponential backoff
        }
    }
    return fmt.Errorf("after %d attempts: %w", maxAttempts, err)
}
```

---

## 8. Performance and Memory Internals

### 8.1 Range Copy Semantics

```go
type HeavyStruct struct {
    Data [1024]byte
    ID   int
}

items := make([]HeavyStruct, 1000)

// BAD — copies 1024 bytes per iteration
for _, item := range items {
    fmt.Println(item.ID)
}

// GOOD — zero copy, index only
for i := range items {
    fmt.Println(items[i].ID)
}

// GOOD — pointer slice eliminates copy overhead
ptrs := make([]*HeavyStruct, 1000)
for _, p := range ptrs {
    fmt.Println(p.ID)  // only pointer (8 bytes) copied
}
```

### 8.2 Bounds Check Elimination (BCE)

The Go compiler performs bounds checking on slice access. You can help it eliminate redundant checks:

```go
// Without BCE hint — compiler checks bounds every iteration
func sumSlice(s []int) int {
    sum := 0
    for i := 0; i < len(s); i++ {
        sum += s[i]
    }
    return sum
}

// With explicit length capture — compiler can prove safety
func sumSliceOptimized(s []int) int {
    sum := 0
    n := len(s)  // captured once, helps BCE
    for i := 0; i < n; i++ {
        sum += s[i]
    }
    return sum
}
```

### 8.3 Loop Unrolling (Manual SIMD hint)

For performance-critical numeric loops:

```go
// DAXPY-style: process 4 elements per iteration
func addScaled(dst, src []float64, alpha float64) {
    n := len(dst)
    i := 0
    for ; i <= n-4; i += 4 {
        dst[i]   += alpha * src[i]
        dst[i+1] += alpha * src[i+1]
        dst[i+2] += alpha * src[i+2]
        dst[i+3] += alpha * src[i+3]
    }
    // handle remaining elements
    for ; i < n; i++ {
        dst[i] += alpha * src[i]
    }
}
```

### 8.4 Escape Analysis and Loop Allocations

```go
// BAD — allocates a new slice header per iteration
for i := 0; i < 1000; i++ {
    buf := make([]byte, 256)  // heap allocation every iteration
    process(buf)
}

// GOOD — allocate once, reuse
buf := make([]byte, 256)
for i := 0; i < 1000; i++ {
    buf = buf[:0]  // reset length, keep capacity
    buf = appendData(buf)
    process(buf)
}
```

---

## 9. Concurrency Patterns with for Loops

### 9.1 Fan-Out: Launch Goroutines in a Loop

```go
// Classic goroutine loop — WRONG (closure capture bug)
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i)  // all goroutines may print 5
    }()
}

// FIXED — pass i as argument
for i := 0; i < 5; i++ {
    go func(n int) {
        fmt.Println(n)  // correct: each goroutine has its own n
    }(i)
}

// FIXED (Go 1.22+) — loop variable is per-iteration scoped
// In Go 1.22+, this is safe by default
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i)  // Go 1.22+: i is captured correctly
    }()
}
```

### 9.2 WaitGroup Fan-Out

```go
func parallelProcess(items []string) []Result {
    results := make([]Result, len(items))
    var wg sync.WaitGroup

    for i, item := range items {
        wg.Add(1)
        go func(idx int, s string) {
            defer wg.Done()
            results[idx] = process(s)  // safe: each goroutine writes to unique index
        }(i, item)
    }

    wg.Wait()
    return results
}
```

### 9.3 Pipeline with for-range over Channels

```go
// Generator stage
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

// Transform stage
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {  // range closes naturally when in is closed
            out <- n * n
        }
    }()
    return out
}

// Usage
for result := range square(generate(2, 3, 4, 5)) {
    fmt.Println(result)  // 4, 9, 16, 25
}
```

### 9.4 Timeout Loop

```go
// Loop with timeout and cancellation — production pattern
func pollUntilReady(ctx context.Context, check func() bool) error {
    ticker := time.NewTicker(500 * time.Millisecond)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            if check() {
                return nil
            }
        }
    }
}
```

---

## 10. Real-World Implementations

### 10.1 Rate Limiter (Token Bucket)

```go
type RateLimiter struct {
    tokens   float64
    maxToken float64
    refillPS float64  // tokens per second
    lastTime time.Time
    mu       sync.Mutex
}

func (rl *RateLimiter) Allow() bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(rl.lastTime).Seconds()
    rl.tokens = min(rl.maxToken, rl.tokens+elapsed*rl.refillPS)
    rl.lastTime = now

    if rl.tokens >= 1.0 {
        rl.tokens--
        return true
    }
    return false
}

// Consumer loop with rate limiting
func consumeWithRateLimit(items []Request, rl *RateLimiter) {
    for _, req := range items {
        for !rl.Allow() {
            time.Sleep(10 * time.Millisecond)  // spin-wait with sleep
        }
        handle(req)
    }
}
```

### 10.2 LRU Cache Eviction Loop

```go
// Evict expired entries from a time-based cache
func (c *Cache) evictExpired() {
    now := time.Now()
    for key, entry := range c.store {
        if now.After(entry.expiry) {
            delete(c.store, key)  // safe to delete from map during range in Go
        }
    }
}
```

**Note:** Deleting from a map while ranging over it is explicitly safe in Go. Newly added keys during range may or may not be visited — old keys deleted are not visited after deletion.

### 10.3 Trie Traversal

```go
type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
}

// Iterative DFS using a stack — avoids recursion stack overflow
func collectWords(root *TrieNode, prefix string) []string {
    type frame struct {
        node   *TrieNode
        prefix string
    }
    
    var words []string
    stack := []frame{{root, prefix}}

    for len(stack) > 0 {
        // pop
        top := stack[len(stack)-1]
        stack = stack[:len(stack)-1]

        if top.node.isEnd {
            words = append(words, top.prefix)
        }

        for i, child := range top.node.children {
            if child != nil {
                stack = append(stack, frame{child, top.prefix + string(rune('a'+i))})
            }
        }
    }
    return words
}
```

### 10.4 Merge K Sorted Arrays

```go
// Using a min-heap via container/heap
// Loop drives the merge process
func mergeKSorted(arrays [][]int) []int {
    // heap setup omitted for brevity — drives with for loop
    var result []int
    
    // The while-heap-not-empty pattern
    for h.Len() > 0 {
        item := heap.Pop(h).(HeapItem)
        result = append(result, item.val)
        
        if item.col+1 < len(arrays[item.row]) {
            heap.Push(h, HeapItem{
                val: arrays[item.row][item.col+1],
                row: item.row,
                col: item.col + 1,
            })
        }
    }
    return result
}
```

### 10.5 Line-by-Line File Processing (Production I/O)

```go
func processLargeFile(filename string) error {
    f, err := os.Open(filename)
    if err != nil {
        return fmt.Errorf("open: %w", err)
    }
    defer f.Close()

    scanner := bufio.NewScanner(f)
    scanner.Buffer(make([]byte, 1024*1024), 1024*1024)  // 1MB buffer for long lines

    lineNum := 0
    for scanner.Scan() {
        lineNum++
        line := scanner.Text()
        
        if err := processLine(lineNum, line); err != nil {
            return fmt.Errorf("line %d: %w", lineNum, err)
        }
    }
    
    return scanner.Err()  // always check scanner error after loop
}
```

### 10.6 String Builder (Efficient String Construction)

```go
func joinWithSeparator(parts []string, sep string) string {
    var sb strings.Builder
    sb.Grow(estimateCapacity(parts, sep))  // pre-allocate

    for i, part := range parts {
        if i > 0 {
            sb.WriteString(sep)
        }
        sb.WriteString(part)
    }
    return sb.String()
}
```

---

## 11. Common Pitfalls and Their Fixes

### Pitfall 1: Modifying Slice During Range

```go
// DANGEROUS — may skip elements or panic
for i, v := range s {
    if v < 0 {
        s = append(s, -v)  // may reallocate; range uses original slice header
    }
}

// SAFE — collect then process
var toAdd []int
for _, v := range s {
    if v < 0 {
        toAdd = append(toAdd, -v)
    }
}
s = append(s, toAdd...)
```

### Pitfall 2: Off-by-One in Boundary Loops

```go
// BUG: processes index 0..n-2, misses last element
for i := 0; i < len(s)-1; i++ { }

// CORRECT: processes 0..n-1
for i := 0; i < len(s); i++ { }

// When len(s) == 0: len(s)-1 underflows to MaxUint — only with uint!
// With int, len(s)-1 == -1, and i < -1 is false immediately. Safe.
```

### Pitfall 3: Goroutine Leak in Infinite Loop

```go
// LEAK — no way to stop this goroutine
go func() {
    for {
        doWork()
    }
}()

// CORRECT — context cancellation
go func(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        default:
            doWork()
        }
    }
}(ctx)
```

### Pitfall 4: Zero-Value Map Reads in Loop

```go
// Safe — reading missing map key returns zero value (0 for int)
freq := make(map[string]int)
for _, word := range words {
    freq[word]++  // safe: missing key returns 0, then incremented to 1
}
```

### Pitfall 5: Integer Overflow in Loop Bounds

```go
// With uint — INFINITE LOOP when n == 0!
var n uint = 0
for i := uint(0); i < n-1; i++ {  // n-1 wraps to MaxUint
    fmt.Println(i)
}

// Always use int for loop counters, even for non-negative counts
```

---

## 12. Expert Mental Models

### Model 1: Every Loop Is a State Machine

A loop body is a *transition function*: it takes state → produces new state → checks termination. Seeing loops this way makes complex loop logic (sliding window, two pointers) intuitive.

```
State:  (window_sum, left, right)
Trans:  expand right, shrink left when constraint violated
Term:   right == n
```

### Model 2: Loop Invariants

An invariant is a property that holds at the start of every iteration. Proving correctness means proving: (a) invariant holds before loop, (b) each iteration preserves it, (c) loop terminates.

```go
// Binary search invariant: target is in arr[lo..hi] at every iteration
// If lo > hi, target is absent — this is the proof of correctness
```

### Model 3: The "Exit Condition First" Principle

Write your loop exit condition before writing the loop body. This forces you to think about termination before mechanics — the root cause of most loop bugs.

### Model 4: Amortized Analysis

Some loops have expensive iterations occasionally but cheap ones usually. A slice `append` loop is O(n) total, not O(n²), because doubling happens rarely.

```go
var result []int
for _, v := range input {
    result = append(result, transform(v))  // O(1) amortized per call
}
// Total: O(n), not O(n²)
```

### Model 5: Chunking for Cognitive Load

When a loop body is large, extract it into a function. The loop structure should be visible at a glance. Named helper functions make complex loops readable.

```go
// Opaque — reader must parse the entire body
for i, v := range data {
    // 30 lines of logic...
}

// Transparent — reader understands flow immediately
for i, v := range data {
    if err := processItem(i, v); err != nil {
        return err
    }
}
```

---

## Quick Reference Table

| Pattern | Syntax | Use Case |
|---|---|---|
| Classic | `for i := 0; i < n; i++` | Index-controlled iteration |
| While | `for condition { }` | Convergence, polling |
| Infinite | `for { }` | Servers, event loops |
| Range slice | `for i, v := range s` | Slice/array traversal |
| Range map | `for k, v := range m` | Map traversal |
| Range string | `for i, r := range s` | Unicode-safe text |
| Range channel | `for v := range ch` | Pipeline consumption |
| Range int | `for i := range n` | Pure counting (1.22+) |
| Labeled break | `break label` | Multi-level exit |
| Labeled continue | `continue label` | Skip outer iteration |

---

*Master the loop. Master the algorithm. Master the machine.*

Here's your complete guide. Let me highlight the **highest-leverage insights** a top 1% engineer carries:

---

**The architectural insight:** Go's single `for` keyword isn't a simplification — it's a *unification*. Once you pattern-match which form fits the problem, you never waste cognitive energy on syntax again. That mental bandwidth goes toward the algorithm.

**The three things that separate experts from intermediates in loops:**

1. **Loop invariant thinking** — Before writing a single line, state what must be true at the start of every iteration. Binary search, two-pointer, and sliding window all become *trivially correct* when you think this way.

2. **Range copy semantics** — Every Go developer who writes `for _, v := range heavySlice` and mutates `v` has a latent bug. The rule is absolute: **range gives you a copy**. Use index when you need mutation.

3. **The goroutine closure capture trap** — The `for i := 0; i < n; i++ { go func() { use(i) }() }` bug has ended careers in production. In Go 1.22+ it's fixed by the spec, but understanding *why* it was broken (loop variable shared across closure captures) is essential knowledge.

**The cognitive model that accelerates DSA mastery most:** Think of every loop as a *state machine* with a transition function and termination condition. Two-pointer, sliding window, BFS queue drain — they're all the same abstraction wearing different clothes. Once you see this, pattern recognition becomes automatic.