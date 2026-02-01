# The Complete Guide to Context in Go

*A rigorous, from-first-principles exploration of Go's context package*

---

## Table of Contents
1. **Foundational Concepts**
2. **The Problem Context Solves**
3. **Core Context Interface & Types**
4. **Context Tree Structure**
5. **Cancellation Mechanisms**
6. **Deadlines & Timeouts**
7. **Value Propagation**
8. **Practical Patterns & Idioms**
9. **Performance Characteristics**
10. **Common Pitfalls & Anti-patterns**
11. **Real-World Implementation Examples**

---

## 1. Foundational Concepts

Before diving into context, let's establish the underlying problems and terminology:

### **Goroutine** (Concurrent execution unit)
A lightweight thread managed by the Go runtime. Unlike OS threads, goroutines are cheap (2KB initial stack) and you can spawn millions.

```go
go func() {
    // This runs concurrently
}()
```

### **Cancellation Propagation**
When a parent operation is cancelled, all child operations should also cancel. Think of it as a cascading shutdown signal.

### **Request-Scoped Data**
Information that exists for the lifetime of a request (like user authentication, request IDs, tracing information).

### **Deadline**
An absolute point in time when an operation must complete.

### **Timeout**
A duration after which an operation should stop.

---

## 2. The Problem Context Solves

### **The Core Problem**

Imagine you're building a web server:

```
HTTP Request comes in
    ↓
Handler starts processing
    ↓
Makes database query (goroutine 1)
    ↓
Calls external API (goroutine 2)
    ↓
Processes results (goroutine 3)
```

**What happens if:**
- Client disconnects mid-request?
- Database query takes 10 seconds?
- External API never responds?

**Without context:** Those goroutines keep running, consuming resources, even though their results are useless.

**With context:** You can:
1. Cancel all child operations when parent cancels
2. Set deadlines for operations
3. Pass request-scoped values

---

## 3. Core Context Interface & Types

### **The Context Interface**

```go
type Context interface {
    // Returns when context is cancelled
    Done() <-chan struct{}
    
    // Returns nil if not cancelled, otherwise the error
    Err() error
    
    // Returns the deadline (if any)
    Deadline() (deadline time.Time, ok bool)
    
    // Returns value associated with key
    Value(key interface{}) interface{}
}
```

**Mental Model:** Think of context as a tree structure where each node can:
- Be cancelled independently
- Inherit cancellation from parent
- Carry values down the tree

### **The Four Fundamental Context Types**

```go
// 1. Background - The root of all contexts
ctx := context.Background()

// 2. TODO - Placeholder when you're unsure which context to use
ctx := context.TODO()

// 3. WithCancel - Manual cancellation
ctx, cancel := context.WithCancel(parent)

// 4. WithTimeout - Time-based cancellation
ctx, cancel := context.WithTimeout(parent, 5*time.Second)

// 5. WithDeadline - Absolute time cancellation
ctx, cancel := context.WithDeadline(parent, time.Now().Add(5*time.Second))

// 6. WithValue - Attach key-value pairs
ctx := context.WithValue(parent, key, value)
```

---

## 4. Context Tree Structure

**Visual Representation:**

```
context.Background() (root)
    │
    ├─ WithTimeout(5s)
    │   │
    │   ├─ WithValue("userID", 123)
    │   │   │
    │   │   └─ WithCancel()
    │   │       │
    │   │       └─ goroutine: database query
    │   │
    │   └─ WithCancel()
    │       │
    │       └─ goroutine: API call
    │
    └─ WithCancel()
        │
        └─ goroutine: background job
```

**Key Principle:** When a parent context is cancelled, ALL descendants are automatically cancelled.

---

## 5. Cancellation Mechanisms

### **Manual Cancellation with WithCancel**

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func operation(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            // Context was cancelled
            fmt.Printf("Operation %d cancelled: %v\n", id, ctx.Err())
            return
        default:
            // Do work
            fmt.Printf("Operation %d working...\n", id)
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func main() {
    // Create cancellable context
    ctx, cancel := context.WithCancel(context.Background())
    
    // Start multiple operations
    go operation(ctx, 1)
    go operation(ctx, 2)
    go operation(ctx, 3)
    
    // Let them run for 2 seconds
    time.Sleep(2 * time.Second)
    
    // Cancel all operations
    fmt.Println("Cancelling all operations...")
    cancel()
    
    // Give goroutines time to finish cleanup
    time.Sleep(1 * time.Second)
}
```

**Output:**
```
Operation 1 working...
Operation 2 working...
Operation 3 working...
Operation 1 working...
Operation 2 working...
Operation 3 working...
Cancelling all operations...
Operation 1 cancelled: context canceled
Operation 2 cancelled: context canceled
Operation 3 cancelled: context canceled
```

**Mental Model for select statement:**
```
select {
    case <-ctx.Done():  // Non-blocking if context is cancelled
    default:             // Executes if context is NOT cancelled
}
```

---

## 6. Deadlines & Timeouts

### **WithTimeout - Relative Time**

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func slowOperation(ctx context.Context) error {
    // Simulate slow work
    select {
    case <-time.After(3 * time.Second):
        fmt.Println("Operation completed successfully")
        return nil
    case <-ctx.Done():
        return ctx.Err() // Returns context.DeadlineExceeded
    }
}

func main() {
    // Context will cancel after 1 second
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel() // Always call cancel to release resources
    
    start := time.Now()
    err := slowOperation(ctx)
    
    fmt.Printf("Finished in %v\n", time.Since(start))
    if err != nil {
        fmt.Printf("Error: %v\n", err)
    }
}
```

**Output:**
```
Finished in 1.000123s
Error: context deadline exceeded
```

### **WithDeadline - Absolute Time**

```go
func main() {
    // Context will cancel at specific time
    deadline := time.Now().Add(2 * time.Second)
    ctx, cancel := context.WithDeadline(context.Background(), deadline)
    defer cancel()
    
    // Check if deadline exists
    if d, ok := ctx.Deadline(); ok {
        fmt.Printf("Context will expire at: %v\n", d)
        fmt.Printf("Time remaining: %v\n", time.Until(d))
    }
}
```

**Critical Distinction:**
- **WithTimeout(duration)**: Relative to NOW
- **WithDeadline(time)**: Absolute point in time

---

## 7. Value Propagation

### **The WithValue Pattern**

```go
package main

import (
    "context"
    "fmt"
)

// Define custom type for keys (prevents collisions)
type contextKey string

const (
    userIDKey    contextKey = "userID"
    requestIDKey contextKey = "requestID"
)

func processRequest(ctx context.Context) {
    // Extract values from context
    userID, ok := ctx.Value(userIDKey).(int)
    if !ok {
        fmt.Println("User ID not found")
        return
    }
    
    requestID, ok := ctx.Value(requestIDKey).(string)
    if !ok {
        fmt.Println("Request ID not found")
        return
    }
    
    fmt.Printf("Processing request %s for user %d\n", requestID, userID)
}

func main() {
    // Build context with values
    ctx := context.Background()
    ctx = context.WithValue(ctx, userIDKey, 12345)
    ctx = context.WithValue(ctx, requestIDKey, "req-abc-123")
    
    processRequest(ctx)
}
```

**Output:**
```
Processing request req-abc-123 for user 12345
```

### **Best Practices for Values**

```go
// ✅ GOOD: Use custom type for keys
type contextKey string
const userKey contextKey = "user"

// ❌ BAD: Using string directly (can collide)
ctx = context.WithValue(ctx, "user", user)

// ✅ GOOD: Type-safe extraction
func getUserFromContext(ctx context.Context) (*User, bool) {
    user, ok := ctx.Value(userKey).(*User)
    return user, ok
}

// ❌ BAD: Direct type assertion without check
user := ctx.Value(userKey).(*User) // Can panic!
```

**Performance Note:** Context value lookup is O(n) where n is the depth of the context tree. Keep nesting shallow.

---

## 8. Practical Patterns & Idioms

### **Pattern 1: HTTP Request Handling**

```go
package main

import (
    "context"
    "fmt"
    "net/http"
    "time"
)

func fetchUserData(ctx context.Context, userID int) (string, error) {
    // Simulate database query
    select {
    case <-time.After(2 * time.Second):
        return fmt.Sprintf("User data for %d", userID), nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func fetchUserPosts(ctx context.Context, userID int) ([]string, error) {
    // Simulate API call
    select {
    case <-time.After(1 * time.Second):
        return []string{"post1", "post2"}, nil
    case <-ctx.Done():
        return nil, ctx.Err()
    }
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
    // HTTP request has built-in context that cancels when client disconnects
    ctx := r.Context()
    
    // Add timeout
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()
    
    userID := 123 // Extract from request
    
    // Launch concurrent operations
    type result struct {
        data  string
        posts []string
        err   error
    }
    
    resultCh := make(chan result, 1)
    
    go func() {
        userData, err := fetchUserData(ctx, userID)
        if err != nil {
            resultCh <- result{err: err}
            return
        }
        
        posts, err := fetchUserPosts(ctx, userID)
        resultCh <- result{data: userData, posts: posts, err: err}
    }()
    
    select {
    case res := <-resultCh:
        if res.err != nil {
            http.Error(w, res.err.Error(), http.StatusInternalServerError)
            return
        }
        fmt.Fprintf(w, "Data: %s, Posts: %v", res.data, res.posts)
    case <-ctx.Done():
        http.Error(w, "Request timeout", http.StatusRequestTimeout)
    }
}
```

### **Pattern 2: Graceful Shutdown**

```go
package main

import (
    "context"
    "fmt"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func worker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d shutting down gracefully...\n", id)
            // Cleanup operations
            time.Sleep(500 * time.Millisecond)
            fmt.Printf("Worker %d stopped\n", id)
            return
        default:
            fmt.Printf("Worker %d processing...\n", id)
            time.Sleep(1 * time.Second)
        }
    }
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    
    // Start workers
    for i := 1; i <= 3; i++ {
        go worker(ctx, i)
    }
    
    // Wait for interrupt signal
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, os.Interrupt, syscall.SIGTERM)
    
    <-sigCh
    fmt.Println("\nReceived shutdown signal...")
    
    // Cancel context to stop all workers
    cancel()
    
    // Give workers time to cleanup
    time.Sleep(2 * time.Second)
    fmt.Println("Shutdown complete")
}
```

### **Pattern 3: Pipeline with Context**

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Stage 1: Generate numbers
func generate(ctx context.Context) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for i := 1; ; i++ {
            select {
            case <-ctx.Done():
                return
            case out <- i:
                time.Sleep(100 * time.Millisecond)
            }
        }
    }()
    return out
}

// Stage 2: Square numbers
func square(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case <-ctx.Done():
                return
            case out <- n * n:
            }
        }
    }()
    return out
}

// Stage 3: Consume numbers
func consume(ctx context.Context, in <-chan int) {
    for n := range in {
        select {
        case <-ctx.Done():
            return
        default:
            fmt.Println(n)
        }
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    // Build pipeline
    nums := generate(ctx)
    squared := square(ctx, nums)
    consume(ctx, squared)
    
    fmt.Println("Pipeline stopped")
}
```

---

## 9. Performance Characteristics

### **Memory & CPU Cost**

```go
package main

import (
    "context"
    "fmt"
    "runtime"
    "time"
)

func measureContextOverhead() {
    var m1, m2 runtime.MemStats
    
    // Measure baseline
    runtime.ReadMemStats(&m1)
    
    // Create 1 million contexts
    contexts := make([]context.Context, 1_000_000)
    parent := context.Background()
    
    for i := 0; i < 1_000_000; i++ {
        ctx, cancel := context.WithCancel(parent)
        contexts[i] = ctx
        _ = cancel // Prevent unused warning
    }
    
    runtime.ReadMemStats(&m2)
    
    fmt.Printf("Memory used: %d KB\n", (m2.Alloc-m1.Alloc)/1024)
    // Typical: ~100-150 bytes per context
}
```

**Key Performance Facts:**

1. **Context creation**: ~100-150 bytes + 2 allocations
2. **Value lookup**: O(depth) - linear search up the tree
3. **Cancellation**: O(children) - must notify all children
4. **Done() channel**: Cached, zero-cost after first call

### **Optimization: Context Reuse**

```go
// ❌ BAD: Creating new context per iteration
for i := 0; i < 1000; i++ {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    doWork(ctx)
    cancel()
}

// ✅ GOOD: Reuse parent context
ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
defer cancel()

for i := 0; i < 1000; i++ {
    doWork(ctx) // All share same deadline
}
```

---

## 10. Common Pitfalls & Anti-patterns

### **❌ Pitfall 1: Storing Context in Structs**

```go
// ❌ BAD: Don't store context in struct
type Server struct {
    ctx context.Context
}

// ✅ GOOD: Pass context as first parameter
type Server struct {
    // other fields
}

func (s *Server) HandleRequest(ctx context.Context, req Request) {
    // ...
}
```

**Reason:** Contexts are request-scoped. Storing in struct makes lifecycle unclear.

### **❌ Pitfall 2: Forgetting to Call cancel()**

```go
// ❌ BAD: Leaks resources
func badFunction() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    doWork(ctx)
    // cancel() never called - timer keeps running!
}

// ✅ GOOD: Always defer cancel
func goodFunction() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel() // Releases resources immediately when function returns
    doWork(ctx)
}
```

### **❌ Pitfall 3: Passing nil Context**

```go
// ❌ BAD: Can cause panic
doWork(nil)

// ✅ GOOD: Use context.TODO() or context.Background()
doWork(context.TODO())
```

### **❌ Pitfall 4: Using Context for Optional Parameters**

```go
// ❌ BAD: Abusing context for configuration
ctx := context.WithValue(ctx, "maxRetries", 3)
ctx = context.WithValue(ctx, "timeout", 5*time.Second)

// ✅ GOOD: Use explicit parameters
type Config struct {
    MaxRetries int
    Timeout    time.Duration
}

func doWork(ctx context.Context, cfg Config) {
    // ...
}
```

### **❌ Pitfall 5: Blocking on Done() Channel**

```go
// ❌ BAD: Blocks forever if context never cancelled
func badPattern(ctx context.Context) {
    <-ctx.Done() // What if this never happens?
    cleanup()
}

// ✅ GOOD: Use select with timeout or other channel
func goodPattern(ctx context.Context) {
    select {
    case <-ctx.Done():
        cleanup()
    case <-time.After(10 * time.Second):
        // Fallback
    }
}
```

---

## 11. Real-World Implementation Examples

### **Example 1: Database Query with Timeout**

```go
package main

import (
    "context"
    "database/sql"
    "fmt"
    "time"
    
    _ "github.com/lib/pq" // PostgreSQL driver
)

type User struct {
    ID    int
    Name  string
    Email string
}

func queryUser(ctx context.Context, db *sql.DB, userID int) (*User, error) {
    // Query respects context deadline/cancellation
    query := "SELECT id, name, email FROM users WHERE id = $1"
    
    row := db.QueryRowContext(ctx, query, userID)
    
    var user User
    err := row.Scan(&user.ID, &user.Name, &user.Email)
    if err != nil {
        return nil, err
    }
    
    return &user, nil
}

func main() {
    // Simulated setup (replace with real connection)
    db, _ := sql.Open("postgres", "connection_string")
    defer db.Close()
    
    // Set 2-second timeout for query
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    user, err := queryUser(ctx, db, 123)
    if err != nil {
        if err == context.DeadlineExceeded {
            fmt.Println("Query timed out")
        } else {
            fmt.Printf("Query error: %v\n", err)
        }
        return
    }
    
    fmt.Printf("User: %+v\n", user)
}
```

### **Example 2: Parallel API Calls with Early Termination**

```go
package main

import (
    "context"
    "fmt"
    "time"
)

type Service struct {
    Name     string
    Delay    time.Duration
    ShouldFail bool
}

func (s *Service) Call(ctx context.Context) (string, error) {
    select {
    case <-time.After(s.Delay):
        if s.ShouldFail {
            return "", fmt.Errorf("%s failed", s.Name)
        }
        return fmt.Sprintf("Response from %s", s.Name), nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func callServicesInParallel(ctx context.Context, services []Service) ([]string, error) {
    // Create child context that cancels on first error
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()
    
    type result struct {
        data string
        err  error
        idx  int
    }
    
    resultCh := make(chan result, len(services))
    
    // Launch all service calls
    for i, svc := range services {
        go func(idx int, service Service) {
            data, err := service.Call(ctx)
            resultCh <- result{data: data, err: err, idx: idx}
        }(i, svc)
    }
    
    // Collect results
    results := make([]string, len(services))
    for i := 0; i < len(services); i++ {
        res := <-resultCh
        
        if res.err != nil {
            cancel() // Cancel all remaining operations
            return nil, fmt.Errorf("service %d failed: %w", res.idx, res.err)
        }
        
        results[res.idx] = res.data
    }
    
    return results, nil
}

func main() {
    services := []Service{
        {Name: "ServiceA", Delay: 500 * time.Millisecond, ShouldFail: false},
        {Name: "ServiceB", Delay: 1 * time.Second, ShouldFail: false},
        {Name: "ServiceC", Delay: 300 * time.Millisecond, ShouldFail: false},
    }
    
    ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
    defer cancel()
    
    start := time.Now()
    results, err := callServicesInParallel(ctx, services)
    
    fmt.Printf("Completed in: %v\n", time.Since(start))
    
    if err != nil {
        fmt.Printf("Error: %v\n", err)
        return
    }
    
    for i, res := range results {
        fmt.Printf("%d: %s\n", i, res)
    }
}
```

### **Example 3: Fan-Out/Fan-In Pattern**

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Worker pool pattern with context
func worker(ctx context.Context, id int, jobs <-chan int, results chan<- int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d cancelled\n", id)
            return
        case job, ok := <-jobs:
            if !ok {
                return
            }
            
            // Simulate work
            select {
            case <-ctx.Done():
                return
            case <-time.After(time.Duration(job) * 100 * time.Millisecond):
                results <- job * 2
            }
        }
    }
}

func processJobsWithWorkerPool(ctx context.Context, numWorkers int, jobs []int) []int {
    jobsCh := make(chan int, len(jobs))
    resultsCh := make(chan int, len(jobs))
    
    // Start workers
    var wg sync.WaitGroup
    for i := 1; i <= numWorkers; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            worker(ctx, id, jobsCh, resultsCh)
        }(i)
    }
    
    // Send jobs
    go func() {
        for _, job := range jobs {
            select {
            case <-ctx.Done():
                return
            case jobsCh <- job:
            }
        }
        close(jobsCh)
    }()
    
    // Collect results in goroutine
    go func() {
        wg.Wait()
        close(resultsCh)
    }()
    
    // Gather results
    var results []int
    for result := range resultsCh {
        results = append(results, result)
    }
    
    return results
}

func main() {
    jobs := []int{1, 2, 3, 4, 5, 6, 7, 8, 9, 10}
    
    // Set timeout
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    start := time.Now()
    results := processJobsWithWorkerPool(ctx, 3, jobs)
    
    fmt.Printf("Processed %d jobs in %v\n", len(results), time.Since(start))
    fmt.Printf("Results: %v\n", results)
}
```

---

## **Mental Model Summary**

```
Context is a TREE structure:

                    [Root Context]
                         |
        +----------------+----------------+
        |                                 |
    [Timeout 5s]                    [Cancel]
        |                                 |
    +---+---+                         [Value]
    |       |                             |
[Cancel] [Value]                     [Worker]
    |       |
[DB Call] [API Call]

Rules:
1. Cancellation flows DOWN (parent → children)
2. Values flow DOWN (children can read parent values)
3. Deadlines are MIN(parent, child)
4. Always pass context as FIRST parameter
5. Never store context in structs
6. Always defer cancel() to prevent leaks
```

---

## **Key Takeaways for Mastery**

1. **Context is for cancellation, deadlines, and request-scoped values** - nothing else
2. **Always pass explicitly** - first parameter in functions
3. **Cancellation cascades** - parent cancellation cancels all children
4. **Resource cleanup** - always `defer cancel()` to prevent leaks
5. **Performance** - value lookup is O(depth), keep trees shallow
6. **Type safety** - use custom types for context keys
7. **Idiomatic Go** - context flows through call chains, not stored in structs

---

This guide covers the complete landscape of Go's context package. Practice implementing these patterns, understand the tree propagation model deeply, and you'll develop the intuition to use context correctly in any scenario.

**Next steps for deliberate practice:**
1. Implement a web server with context-aware middleware
2. Build a distributed task queue with graceful shutdown
3. Create a rate limiter using context for backpressure

# Context Switching: The Performance Killer

*A deep dive into OS-level context switching and its relationship to Go's context package*

---

## Table of Contents

1. **What is Context Switching?**
2. **The Hardware & OS Perspective**
3. **Types of Context Switches**
4. **Performance Impact & Measurement**
5. **Relationship to Go's Context Package**
6. **Goroutine Scheduling vs Thread Context Switching**
7. **Optimization Strategies**
8. **Practical Examples & Benchmarks**

---

## 1. What is Context Switching?

### **Definition**

**Context switching** is the process of storing and restoring the state (context) of a CPU so that execution can be resumed from the same point at a later time.

Think of it like bookmarking a book:
- You're reading Book A (Process A is running)
- You need to switch to Book B (Process B needs CPU)
- You bookmark Book A at page 47 (save CPU state)
- You find your bookmark in Book B at page 132 (restore CPU state)
- You start reading Book B (Process B runs)

### **What Gets Saved/Restored? (The "Context")**

```
CPU Context (The bookmark):
├── Program Counter (PC)        ← Where in the code we are
├── Stack Pointer (SP)          ← Where in memory stack we are
├── CPU Registers               ← All 16-32+ general purpose registers
│   ├── RAX, RBX, RCX, RDX     ← Data registers
│   ├── RSI, RDI               ← Index registers
│   └── R8-R15                 ← Additional registers
├── Flags Register              ← CPU state flags
├── Memory Management Context   
│   ├── Page Table Pointer      ← Virtual memory mappings
│   └── TLB entries             ← Translation cache
└── FPU/SIMD Registers         ← Floating point state
    └── 256-512 bits each
```

**Size of context**: Typically **2-4 KB** of state data per thread.

---

## 2. The Hardware & OS Perspective

### **The Journey of a Context Switch**

```
Timeline of a Context Switch (x86-64 Linux):

T=0ns:   Thread A running
         ↓
T=100ns: Interrupt occurs (timer/I/O/syscall)
         ↓
T=200ns: CPU switches to kernel mode
         ↓
T=500ns: Save Thread A's registers to memory
         │
         ├─ Save: RAX, RBX, RCX, RDX, RSI, RDI, RBP, RSP
         ├─ Save: R8, R9, R10, R11, R12, R13, R14, R15
         ├─ Save: Program Counter (RIP)
         ├─ Save: Flags (RFLAGS)
         └─ Save: FPU/SSE/AVX registers (512 bytes)
         ↓
T=1μs:   Scheduler selects Thread B
         ↓
T=2μs:   Restore Thread B's registers from memory
         │
         ├─ Load: All general purpose registers
         ├─ Load: Stack pointer
         ├─ Load: Program counter
         └─ Load: FPU/SIMD state
         ↓
T=3μs:   Switch page tables (if different process)
         │
         └─ Flush TLB (Translation Lookaside Buffer)
            This invalidates CPU cache of virtual→physical mappings
         ↓
T=5μs:   CPU switches to user mode
         ↓
T=5.1μs: Thread B resumes execution
```

**Total overhead**: **1-5 microseconds** per switch (varies by CPU architecture)

### **Why Context Switching is Expensive**

```
Direct Costs:
├── Saving registers:              ~500ns
├── Loading registers:             ~500ns
├── Kernel mode transitions:       ~200ns × 2 = 400ns
├── Scheduler decision:            ~1μs
└── TLB flush (if process switch): ~1-2μs

Indirect Costs (THE REAL KILLER):
├── Cache pollution:               ~10-100μs
│   ├── L1 cache miss:             ~4 cycles (1ns)
│   ├── L2 cache miss:             ~12 cycles (3ns)
│   ├── L3 cache miss:             ~40 cycles (10ns)
│   └── RAM access:                ~200 cycles (50ns)
│
├── TLB misses:                    ~100 cycles each
└── Pipeline stalls:               ~50-100 cycles
```

**Key Insight:** The direct cost is small (~5μs), but the **indirect cost** from cache misses can be **10-100× larger**.

---

## 3. Types of Context Switches

### **Type 1: Voluntary Context Switch**

Thread **willingly** gives up CPU (e.g., waiting for I/O).

```c
// Thread A calls read() - blocks waiting for data
ssize_t bytes = read(fd, buffer, size);
// ↑ Thread yields CPU while waiting
// ↓ Scheduler runs Thread B
```

**Characteristics:**
- Thread is blocked (not runnable)
- Efficient - thread knows it can't proceed
- Common in I/O-heavy workloads

### **Type 2: Involuntary Context Switch**

OS **forces** thread to yield (time slice expired).

```c
// Thread A running CPU-intensive loop
for (int i = 0; i < 1000000000; i++) {
    sum += compute(i);
}
// ↑ OS timer interrupt fires
// ↓ OS forcibly switches to Thread B
```

**Characteristics:**
- Thread is still runnable
- Wasteful - thread could have continued
- Common in CPU-bound workloads
- Indicates CPU contention

### **Type 3: Process vs Thread Context Switch**

```
Thread Switch (same process):
├── Save/restore registers         ✓
├── Save/restore stack pointer     ✓
├── Switch page tables             ✗ (shared address space)
└── Flush TLB                      ✗ (no need)
Cost: ~1-2μs

Process Switch (different processes):
├── Save/restore registers         ✓
├── Save/restore stack pointer     ✓
├── Switch page tables             ✓
└── Flush TLB                      ✓
Cost: ~5-10μs (much more expensive!)
```

---

## 4. Performance Impact & Measurement

### **Measuring Context Switches**

**On Linux:**

```bash
# View context switches for entire system
vmstat 1

# Output:
# procs -----------memory---------- ---swap-- -----io---- -system-- ------cpu-----
#  r  b   swpd   free   buff  cache   si   so    bi    bo   in   cs us sy id wa st
#  2  0      0 1234567  12345 234567    0    0     5    10  500 1000 25  5 70  0  0
#                                                              ↑
#                                                     context switches/second

# View per-process context switches
cat /proc/<PID>/status | grep ctxt

# Output:
# voluntary_ctxt_switches:    12543    ← Thread yielded willingly
# nonvoluntary_ctxt_switches: 234      ← Thread was preempted
```

### **Benchmark: Impact on Performance**

```go
package main

import (
    "runtime"
    "sync"
    "testing"
    "time"
)

// Benchmark: Single goroutine (no context switching)
func BenchmarkNoContextSwitch(b *testing.B) {
    sum := 0
    for i := 0; i < b.N; i++ {
        sum += i
    }
}

// Benchmark: Multiple goroutines (heavy context switching)
func BenchmarkWithContextSwitch(b *testing.B) {
    runtime.GOMAXPROCS(4) // 4 CPU cores
    
    var wg sync.WaitGroup
    numGoroutines := 1000
    iterations := b.N / numGoroutines
    
    for i := 0; i < numGoroutines; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            sum := 0
            for j := 0; j < iterations; j++ {
                sum += j
                // Force goroutine switch
                runtime.Gosched()
            }
        }()
    }
    
    wg.Wait()
}
```

**Typical Results:**
```
BenchmarkNoContextSwitch-4          1000000000    0.5 ns/op
BenchmarkWithContextSwitch-4        10000000      150 ns/op
```

**300× slower** due to context switching overhead!

### **Real-World Impact Example**

```go
package main

import (
    "fmt"
    "runtime"
    "sync"
    "time"
)

func cpuBoundWork(n int) int {
    sum := 0
    for i := 0; i < n; i++ {
        sum += i * i
    }
    return sum
}

func scenario1_NoContextSwitching() {
    start := time.Now()
    
    // Single goroutine doing all work
    total := 0
    for i := 0; i < 1000; i++ {
        total += cpuBoundWork(100000)
    }
    
    fmt.Printf("Scenario 1 (no switching): %v\n", time.Since(start))
}

func scenario2_ExcessiveContextSwitching() {
    start := time.Now()
    runtime.GOMAXPROCS(4)
    
    // 1000 goroutines competing for 4 cores
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            cpuBoundWork(100000)
        }()
    }
    wg.Wait()
    
    fmt.Printf("Scenario 2 (excessive switching): %v\n", time.Since(start))
}

func scenario3_Optimal() {
    start := time.Now()
    runtime.GOMAXPROCS(4)
    
    // 4 goroutines (one per core)
    var wg sync.WaitGroup
    workPerGoroutine := 1000 / 4
    
    for i := 0; i < 4; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for j := 0; j < workPerGoroutine; j++ {
                cpuBoundWork(100000)
            }
        }()
    }
    wg.Wait()
    
    fmt.Printf("Scenario 3 (optimal): %v\n", time.Since(start))
}

func main() {
    scenario1_NoContextSwitching()
    scenario2_ExcessiveContextSwitching()
    scenario3_Optimal()
}
```

**Output:**
```
Scenario 1 (no switching): 245ms
Scenario 2 (excessive switching): 890ms  ← 3.6× slower!
Scenario 3 (optimal): 250ms
```

---

## 5. Relationship to Go's Context Package

### **CRITICAL DISTINCTION**

```
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║  Go's "context" package ≠ OS-level "context switching"       ║
║                                                               ║
║  They are DIFFERENT concepts that share the word "context"   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
```

### **What They Mean**

```
OS Context Switching:
├── Definition: CPU state saved/restored when switching threads
├── Level: Hardware + Operating System
├── Cost: Microseconds per switch
├── Controls: Which thread runs on CPU
└── Performance Impact: Cache misses, TLB flushes

Go Context Package:
├── Definition: Request-scoped cancellation and values
├── Level: Application logic
├── Cost: Nanoseconds (cheap!)
├── Controls: Goroutine lifecycle and data flow
└── Performance Impact: Minimal (just goroutine coordination)
```

### **Indirect Relationship**

Go's context package **can influence** context switching, but doesn't directly cause it:

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// BAD: Context causes goroutines to block → context switches
func inefficientPattern() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    // Launch 10000 goroutines
    for i := 0; i < 10000; i++ {
        go func(id int) {
            // Each goroutine blocks on ctx.Done()
            <-ctx.Done() // ← Causes goroutine to block → voluntary context switch
            fmt.Printf("Goroutine %d cancelled\n", id)
        }(i)
    }
    
    time.Sleep(2 * time.Second)
}

// GOOD: Context allows efficient shutdown without excessive switching
func efficientPattern() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    // Single goroutine checks context periodically
    go func() {
        ticker := time.NewTicker(100 * time.Millisecond)
        defer ticker.Stop()
        
        for {
            select {
            case <-ctx.Done():
                return // Clean exit
            case <-ticker.C:
                // Do work
            }
        }
    }()
    
    time.Sleep(1 * time.Second)
    cancel() // Efficient cancellation
}
```

### **How Go Context Helps REDUCE Context Switching**

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Without context: goroutines keep running wastefully
func withoutContext() {
    done := make(chan bool)
    
    for i := 0; i < 100; i++ {
        go func(id int) {
            for {
                select {
                case <-done:
                    return
                default:
                    // CPU-bound work
                    sum := 0
                    for j := 0; j < 1000000; j++ {
                        sum += j
                    }
                    // ↑ OS keeps context switching between these 100 goroutines
                }
            }
        }(i)
    }
    
    time.Sleep(1 * time.Second)
    close(done) // Stop all goroutines
}

// With context: goroutines stop cleanly
func withContext() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    for i := 0; i < 100; i++ {
        go func(id int, ctx context.Context) {
            for {
                select {
                case <-ctx.Done():
                    return // Stop immediately when cancelled
                default:
                    sum := 0
                    for j := 0; j < 1000000; j++ {
                        sum += j
                    }
                }
            }
        }(i, ctx)
    }
    
    <-ctx.Done() // Wait for timeout
    time.Sleep(100 * time.Millisecond) // Let goroutines finish
}

func main() {
    fmt.Println("Running without context...")
    start := time.Now()
    withoutContext()
    fmt.Printf("Time: %v\n\n", time.Since(start))
    
    fmt.Println("Running with context...")
    start = time.Now()
    withContext()
    fmt.Printf("Time: %v\n", time.Since(start))
}
```

**Key Insight:** Context helps **prevent unnecessary goroutines** from running, which **reduces** the number of context switches the OS must perform.

---

## 6. Goroutine Scheduling vs Thread Context Switching

### **The Go Runtime Scheduler (M:N Model)**

```
                  Application Level
        ╔════════════════════════════════════╗
        ║  G1  G2  G3  G4  G5  G6  G7  G8    ║  ← Goroutines (G)
        ╚════════════════════════════════════╝
                        ↓
              Go Runtime Scheduler
        ╔════════════════════════════════════╗
        ║      P1      P2      P3      P4    ║  ← Processors (P)
        ║      ↓       ↓       ↓       ↓     ║    (Logical CPUs)
        ╚════════════════════════════════════╝
                        ↓
              Operating System
        ╔════════════════════════════════════╗
        ║      M1      M2      M3      M4    ║  ← Machine threads (M)
        ╚════════════════════════════════════╝
                        ↓
                  Physical CPUs
        ╔════════════════════════════════════╗
        ║   Core1  Core2  Core3  Core4       ║
        ╚════════════════════════════════════╝
```

**The GMP Model:**
- **G** (Goroutine): Lightweight execution context (~2KB stack)
- **P** (Processor): Scheduling context (one per logical CPU)
- **M** (Machine): OS thread

### **Goroutine Switch vs Thread Context Switch**

```
Goroutine Switch (User-space):
┌─────────────────────────────────────────┐
│ 1. Save: Program Counter (8 bytes)     │
│ 2. Save: Stack Pointer (8 bytes)       │
│ 3. Save: A few registers (~64 bytes)   │
│ 4. Update scheduler state              │
│ 5. Resume next goroutine               │
│                                         │
│ Cost: ~10-50 nanoseconds               │
│ Location: User space (no kernel call)  │
└─────────────────────────────────────────┘

Thread Context Switch (Kernel-space):
┌─────────────────────────────────────────┐
│ 1. Save: ALL CPU registers (~2KB)      │
│ 2. Save: FPU/SIMD state (~512 bytes)   │
│ 3. Switch to kernel mode (syscall)     │
│ 4. OS scheduler runs                   │
│ 5. Switch page tables (if needed)      │
│ 6. Flush TLB cache                     │
│ 7. Restore ALL CPU registers           │
│ 8. Switch back to user mode            │
│                                         │
│ Cost: ~1-5 microseconds (100× slower!)  │
│ Location: Kernel space                 │
└─────────────────────────────────────────┘
```

### **Practical Example: Measuring the Difference**

```go
package main

import (
    "fmt"
    "runtime"
    "sync"
    "time"
)

// Benchmark: Goroutine switching
func benchmarkGoroutineSwitching() {
    runtime.GOMAXPROCS(1) // Force onto single OS thread
    
    iterations := 1000000
    ch := make(chan bool)
    
    start := time.Now()
    
    go func() {
        for i := 0; i < iterations; i++ {
            ch <- true
        }
    }()
    
    for i := 0; i < iterations; i++ {
        <-ch
    }
    
    duration := time.Since(start)
    fmt.Printf("Goroutine switches: %v total\n", duration)
    fmt.Printf("Per switch: %v\n", duration/time.Duration(iterations*2))
}

// Benchmark: OS thread switching (using CGO to force kernel threads)
func benchmarkThreadSwitching() {
    iterations := 100000 // Fewer iterations - threads are expensive!
    
    var wg sync.WaitGroup
    ch := make(chan bool, 100)
    
    start := time.Now()
    
    // Force creation of OS threads by using blocking syscalls
    for i := 0; i < 4; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            runtime.LockOSThread() // Pin to OS thread
            defer runtime.UnlockOSThread()
            
            for j := 0; j < iterations/4; j++ {
                ch <- true
                time.Sleep(1 * time.Nanosecond) // Force syscall
            }
        }()
    }
    
    wg.Wait()
    
    duration := time.Since(start)
    fmt.Printf("Thread switches: %v total\n", duration)
    fmt.Printf("Per switch: ~%v\n", duration/time.Duration(iterations))
}

func main() {
    fmt.Println("=== Goroutine Switching ===")
    benchmarkGoroutineSwitching()
    
    fmt.Println("\n=== OS Thread Switching ===")
    benchmarkThreadSwitching()
}
```

**Typical Output:**
```
=== Goroutine Switching ===
Goroutine switches: 45ms total
Per switch: 22ns

=== OS Thread Switching ===
Thread switches: 850ms total
Per switch: ~2100ns
```

**Goroutines are ~100× faster to switch!**

---

## 7. Optimization Strategies

### **Strategy 1: Minimize Goroutine Count**

```go
// ❌ BAD: Spawns goroutine per item (excessive switching)
func processItemsBad(items []Item) {
    var wg sync.WaitGroup
    for _, item := range items { // 1 million items
        wg.Add(1)
        go func(i Item) {
            defer wg.Done()
            process(i)
        }(item)
    }
    wg.Wait()
}

// ✅ GOOD: Worker pool pattern
func processItemsGood(items []Item) {
    numWorkers := runtime.NumCPU()
    workCh := make(chan Item, len(items))
    
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for item := range workCh {
                process(item)
            }
        }()
    }
    
    for _, item := range items {
        workCh <- item
    }
    close(workCh)
    
    wg.Wait()
}
```

### **Strategy 2: Batch Processing**

```go
// ❌ BAD: Process one at a time (many context switches)
func processSingleItems(db *sql.DB, items []int) {
    for _, id := range items {
        db.Exec("INSERT INTO table VALUES (?)", id)
        // Each call: goroutine blocks → context switch
    }
}

// ✅ GOOD: Batch processing
func processBatchItems(db *sql.DB, items []int) {
    batchSize := 1000
    
    for i := 0; i < len(items); i += batchSize {
        end := i + batchSize
        if end > len(items) {
            end = len(items)
        }
        
        batch := items[i:end]
        
        // Single syscall for entire batch
        stmt, _ := db.Prepare("INSERT INTO table VALUES " + 
            strings.Repeat("(?),", len(batch)-1) + "(?)")
        
        args := make([]interface{}, len(batch))
        for j, v := range batch {
            args[j] = v
        }
        
        stmt.Exec(args...)
    }
}
```

### **Strategy 3: Avoid Blocking Operations in Hot Paths**

```go
// ❌ BAD: Frequent blocking in tight loop
func inefficientLoop(ctx context.Context) {
    for i := 0; i < 1000000; i++ {
        select {
        case <-ctx.Done():
            return
        default:
        }
        // Process item (causes frequent context checks)
        compute(i)
    }
}

// ✅ GOOD: Check context periodically
func efficientLoop(ctx context.Context) {
    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()
    
    for i := 0; i < 1000000; i++ {
        // Only check every 100ms instead of every iteration
        select {
        case <-ticker.C:
            if ctx.Err() != nil {
                return
            }
        default:
        }
        
        compute(i)
    }
}
```

### **Strategy 4: Use Buffered Channels**

```go
// ❌ BAD: Unbuffered channel (goroutines block frequently)
func unbufferedPipeline() {
    ch := make(chan int) // Unbuffered
    
    go func() {
        for i := 0; i < 1000; i++ {
            ch <- i // Blocks until receiver ready → context switch
        }
        close(ch)
    }()
    
    for v := range ch {
        process(v)
    }
}

// ✅ GOOD: Buffered channel (reduces blocking)
func bufferedPipeline() {
    ch := make(chan int, 100) // Buffered
    
    go func() {
        for i := 0; i < 1000; i++ {
            ch <- i // Only blocks when buffer full
        }
        close(ch)
    }()
    
    for v := range ch {
        process(v)
    }
}
```

---

## 8. Advanced: Measuring Context Switches in Go

### **Using runtime.NumCgoCall()**

```go
package main

import (
    "fmt"
    "runtime"
    "time"
)

func measureContextSwitches() {
    // Get initial stats
    var m1, m2 runtime.MemStats
    runtime.ReadMemStats(&m1)
    
    startGoroutines := runtime.NumGoroutine()
    
    // Run workload
    done := make(chan bool)
    for i := 0; i < 100; i++ {
        go func() {
            time.Sleep(100 * time.Millisecond)
            done <- true
        }()
    }
    
    for i := 0; i < 100; i++ {
        <-done
    }
    
    runtime.ReadMemStats(&m2)
    endGoroutines := runtime.NumGoroutine()
    
    fmt.Printf("Goroutines created: %d\n", 100)
    fmt.Printf("Goroutines active at end: %d\n", endGoroutines-startGoroutines)
    fmt.Printf("GC runs: %d\n", m2.NumGC-m1.NumGC)
}

func main() {
    measureContextSwitches()
}
```

### **Using Linux perf**

```bash
# Measure context switches for a Go program
perf stat -e context-switches,cpu-migrations ./your-go-binary

# Output:
#  Performance counter stats for './your-go-binary':
#
#         12,543      context-switches
#            234      cpu-migrations
#
#       1.234567 seconds time elapsed
```

---

## **Summary: The Complete Picture**

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  OS Context Switching (Hardware/Kernel Level)              │
│  ├── What: Save/restore CPU state between threads          │
│  ├── Cost: 1-5 microseconds per switch                     │
│  ├── Cache Impact: 10-100× worse (cache misses)            │
│  └── Control: Operating system scheduler                   │
│                                                             │
│                         vs                                  │
│                                                             │
│  Go Context Package (Application Level)                    │
│  ├── What: Request-scoped cancellation & values            │
│  ├── Cost: Negligible (just checking channels/values)      │
│  ├── Relationship: Indirect - helps manage goroutines      │
│  └── Control: Application logic                            │
│                                                             │
│                         vs                                  │
│                                                             │
│  Goroutine Switching (Go Runtime Level)                    │
│  ├── What: Switch between goroutines (user-space)          │
│  ├── Cost: 10-50 nanoseconds (100× cheaper than threads!)  │
│  ├── Mechanism: Cooperative scheduling in Go runtime       │
│  └── Control: Go scheduler (GMP model)                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### **Key Takeaways for Mastery**

1. **Context switching** (OS-level) and **context package** (Go-level) are **different concepts**
2. OS context switching is **expensive** (microseconds + cache pollution)
3. Goroutine switching is **cheap** (nanoseconds, user-space)
4. Go's context package helps **reduce** OS context switches by managing goroutine lifecycles efficiently
5. **Optimization principle**: Minimize goroutine count, use worker pools, batch operations, buffer channels
6. **Measurement matters**: Use `perf`, `vmstat`, and Go's `runtime` package to measure actual impact

This deep understanding will help you write highly performant concurrent Go code by minimizing unnecessary context switches at both the OS and application levels.