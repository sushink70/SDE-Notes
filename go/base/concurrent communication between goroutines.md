# Concurrent Communication Between Goroutines: A Comprehensive Guide

## Foundation: What Are We Building?

Before diving into communication mechanisms, let's establish the **mental model** of concurrent systems in Go.

**Concurrency vs Parallelism:**
- **Concurrency**: The *composition* of independently executing computations. Think of it as *structure* — juggling multiple tasks by switching between them.
- **Parallelism**: The *simultaneous execution* of computations. Think of it as *execution* — actually doing multiple things at once.

**Goroutine**: A lightweight thread managed by the Go runtime. Unlike OS threads (which consume ~1-2MB of stack space), goroutines start with only ~2KB, making it feasible to spawn thousands or even millions of them.

---

## Core Philosophy: "Don't communicate by sharing memory; share memory by communicating"

This is Go's mantra. Instead of multiple goroutines accessing shared variables (which requires locks), goroutines should send data through **channels**.

```
┌─────────────┐                    ┌─────────────┐
│ Goroutine A │──── channel ────→ │ Goroutine B │
└─────────────┘                    └─────────────┘
```

---

## Part 1: Channels — The Primary Communication Primitive

### What is a Channel?

A **channel** is a typed conduit through which you can send and receive values. Think of it as a **pipe** connecting goroutines.

**Syntax:**
```go
ch := make(chan int)        // unbuffered channel
ch := make(chan int, 100)   // buffered channel with capacity 100
```

### Mental Model: The Post Office Analogy

```
Sender Goroutine          Channel (Mailbox)       Receiver Goroutine
┌──────────┐             ┌──────────┐            ┌──────────┐
│  Write   │────────────→│  Queue   │───────────→│   Read   │
│  Letter  │             │  Letters │            │  Letter  │
└──────────┘             └──────────┘            └──────────┘
```

---

## Part 2: Channel Types & Behavior

### 2.1 Unbuffered Channels (Synchronous)

**Characteristic**: Send blocks until a receiver is ready. Receive blocks until a sender sends.

```
Timeline Visualization:

Sender Thread:              Receiver Thread:
    │                           │
    │ ch <- data                │
    │ [BLOCKED]                 │
    │   ...                     │
    │   ...                     │ <- ch
    │ [UNBLOCKED]               │ [receives data]
    ▼                           ▼
```

**Example:**
```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string) // unbuffered
    
    go func() {
        time.Sleep(2 * time.Second)
        fmt.Println("Goroutine: about to send")
        ch <- "Hello"  // This will block until main receives
        fmt.Println("Goroutine: sent successfully")
    }()
    
    fmt.Println("Main: about to receive")
    msg := <-ch  // This blocks until goroutine sends
    fmt.Println("Main: received", msg)
}
```

**Output:**
```
Main: about to receive
Goroutine: about to send
Main: received Hello
Goroutine: sent successfully
```

**Key Insight**: Unbuffered channels enforce **synchronization**. Both sender and receiver must meet at the same moment.

---

### 2.2 Buffered Channels (Asynchronous)

**Characteristic**: Send only blocks when buffer is full. Receive only blocks when buffer is empty.

```
Channel Buffer Visualization:

Capacity: 3
┌───┬───┬───┐
│ 1 │ 2 │ 3 │ ← Full (send blocks)
└───┴───┴───┘

┌───┬───┬───┐
│ 1 │ 2 │   │ ← Partially filled (send doesn't block)
└───┴───┴───┘

┌───┬───┬───┐
│   │   │   │ ← Empty (receive blocks)
└───┴───┴───┘
```

**Example:**
```go
func main() {
    ch := make(chan int, 2) // buffer size 2
    
    ch <- 1  // doesn't block
    ch <- 2  // doesn't block
    // ch <- 3  // would block (buffer full)
    
    fmt.Println(<-ch) // 1
    fmt.Println(<-ch) // 2
    // fmt.Println(<-ch) // would block (buffer empty)
}
```

**Decision Tree: Buffered vs Unbuffered**

```
                    Need synchronization?
                    /                  \
                 YES                   NO
                  |                     |
          Unbuffered Channel     Need to decouple
                                 sender/receiver pace?
                                     /         \
                                  YES          NO
                                   |            |
                            Buffered      Unbuffered
                            Channel       Channel
```

---

## Part 3: Channel Operations

### 3.1 Send Operation: `ch <- value`

```go
ch <- 42  // Send 42 to channel
```

**Blocking Behavior:**
- **Unbuffered**: Blocks until receiver reads
- **Buffered**: Blocks only if buffer is full

---

### 3.2 Receive Operation: `value := <-ch`

```go
value := <-ch     // Receive and assign
<-ch              // Receive and discard
```

**Blocking Behavior:**
- Blocks until a value is available

---

### 3.3 Close Operation: `close(ch)`

**Purpose**: Signal that no more values will be sent.

```go
close(ch)
```

**Important Rules:**
1. Only the **sender** should close channels
2. Sending on a closed channel causes **panic**
3. Receiving from a closed channel returns zero value + `false`

**Pattern: Check if channel is closed**
```go
value, ok := <-ch
if !ok {
    // Channel is closed
}
```

**Better Pattern: Range over channel**
```go
for value := range ch {
    // Automatically stops when channel closes
    fmt.Println(value)
}
```

---

## Part 4: Communication Patterns

### 4.1 Pipeline Pattern

**Concept**: Chain goroutines where output of one becomes input of next.

```
ASCII Visualization:

Input → [Stage 1] → [Stage 2] → [Stage 3] → Output
        Generate    Square       Filter
```

**Example: Number Processing Pipeline**

```go
package main

import "fmt"

// Stage 1: Generate numbers
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

// Stage 2: Square numbers
func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            out <- n * n
        }
        close(out)
    }()
    return out
}

// Stage 3: Filter even numbers
func filterEven(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        for n := range in {
            if n%2 == 0 {
                out <- n
            }
        }
        close(out)
    }()
    return out
}

func main() {
    // Set up pipeline
    numbers := generate(1, 2, 3, 4, 5)
    squared := square(numbers)
    evens := filterEven(squared)
    
    // Consume results
    for result := range evens {
        fmt.Println(result) // Output: 4, 16
    }
}
```

**Key Patterns:**
- **Direction indicators**: `<-chan` (receive-only), `chan<-` (send-only)
- Each stage closes its output channel when done
- Range loop automatically handles channel closure

---

### 4.2 Fan-Out, Fan-In Pattern

**Fan-Out**: Distribute work across multiple workers
**Fan-In**: Collect results from multiple workers

```
Fan-Out Visualization:

         ┌─→ Worker 1 ─┐
Input ───┼─→ Worker 2 ─┼─→ Merge → Output
         └─→ Worker 3 ─┘
```

**Example:**

```go
package main

import (
    "fmt"
    "sync"
)

// Worker function
func worker(id int, jobs <-chan int, results chan<- int) {
    for job := range jobs {
        fmt.Printf("Worker %d processing job %d\n", id, job)
        results <- job * 2 // Simulate work
    }
}

// Fan-in: Merge multiple channels
func merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    out := make(chan int)
    
    // Start goroutine for each input channel
    for _, ch := range channels {
        wg.Add(1)
        go func(c <-chan int) {
            defer wg.Done()
            for val := range c {
                out <- val
            }
        }(ch)
    }
    
    // Close output when all inputs are done
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}

func main() {
    jobs := make(chan int, 100)
    results := make(chan int, 100)
    
    // Fan-out: Start 3 workers
    for w := 1; w <= 3; w++ {
        go worker(w, jobs, results)
    }
    
    // Send jobs
    for j := 1; j <= 9; j++ {
        jobs <- j
    }
    close(jobs)
    
    // Collect results (Note: We know we'll get 9 results)
    for i := 0; i < 9; i++ {
        result := <-results
        fmt.Println("Result:", result)
    }
}
```

**Cognitive Principle**: **Work Distribution** — Like a manager delegating tasks to team members and collecting their outputs.

---

### 4.3 Select Statement — Multiplexing Channels

**Purpose**: Wait on multiple channel operations simultaneously.

**Syntax:**
```go
select {
case msg1 := <-ch1:
    // Handle msg1
case msg2 := <-ch2:
    // Handle msg2
case ch3 <- value:
    // Send value
default:
    // Non-blocking option
}
```

**Decision Flow:**

```
┌─────────────────────────────┐
│  Multiple channels ready?   │
└──────────┬──────────────────┘
           │
           ├─→ YES → Pick one randomly
           │
           └─→ NO  → Block until one ready
                     (or use default for non-blocking)
```

**Example: Timeout Pattern**

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string)
    
    go func() {
        time.Sleep(2 * time.Second)
        ch <- "result"
    }()
    
    select {
    case res := <-ch:
        fmt.Println("Received:", res)
    case <-time.After(1 * time.Second):
        fmt.Println("Timeout!")
    }
}
```

**Output**: `Timeout!` (because 1 second timeout expires before 2 second sleep)

---

### 4.4 Worker Pool Pattern

**Purpose**: Limit concurrency by using a fixed number of workers.

```
Flow Diagram:

Jobs Queue → [Worker 1] → Results
           → [Worker 2] →
           → [Worker 3] →
```

**Example:**

```go
package main

import (
    "fmt"
    "time"
)

func worker(id int, jobs <-chan int, results chan<- int) {
    for job := range jobs {
        fmt.Printf("Worker %d started job %d\n", id, job)
        time.Sleep(time.Second) // Simulate work
        fmt.Printf("Worker %d finished job %d\n", id, job)
        results <- job * 2
    }
}

func main() {
    const numJobs = 5
    const numWorkers = 3
    
    jobs := make(chan int, numJobs)
    results := make(chan int, numJobs)
    
    // Start workers
    for w := 1; w <= numWorkers; w++ {
        go worker(w, jobs, results)
    }
    
    // Send jobs
    for j := 1; j <= numJobs; j++ {
        jobs <- j
    }
    close(jobs)
    
    // Collect results
    for a := 1; a <= numJobs; a++ {
        <-results
    }
}
```

---

## Part 5: Advanced Synchronization with sync Package

### 5.1 WaitGroup — Waiting for Goroutines

**Purpose**: Wait for a collection of goroutines to finish.

**API:**
- `Add(delta int)`: Increment counter
- `Done()`: Decrement counter
- `Wait()`: Block until counter is zero

**Example:**

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done() // Decrement when function returns
    
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Second)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    var wg sync.WaitGroup
    
    for i := 1; i <= 5; i++ {
        wg.Add(1)
        go worker(i, &wg)
    }
    
    wg.Wait() // Block until all workers call Done()
    fmt.Println("All workers finished")
}
```

**Visualization:**

```
Counter: 5
┌───┬───┬───┬───┬───┐
│ W1│ W2│ W3│ W4│ W5│  All started (counter = 5)
└───┴───┴───┴───┴───┘

W1 finishes → counter = 4
W3 finishes → counter = 3
W2 finishes → counter = 2
W5 finishes → counter = 1
W4 finishes → counter = 0 → Wait() unblocks
```

---

### 5.2 Mutex — Mutual Exclusion

**Purpose**: Protect shared resources from concurrent access.

**When to use**: When you MUST share memory (e.g., updating a counter, modifying a map).

**API:**
- `Lock()`: Acquire lock (blocks if already locked)
- `Unlock()`: Release lock

**Example: Safe Counter**

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    mu sync.Mutex
    v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
    c.mu.Lock()
    c.v[key]++
    c.mu.Unlock()
}

func (c *SafeCounter) Value(key string) int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.v[key]
}

func main() {
    c := SafeCounter{v: make(map[string]int)}
    var wg sync.WaitGroup
    
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Inc("key")
        }()
    }
    
    wg.Wait()
    fmt.Println(c.Value("key")) // Always 1000 (with mutex)
}
```

**Without mutex**, the output would be unpredictable (race condition).

---

### 5.3 RWMutex — Read-Write Lock

**Optimization**: Multiple readers can hold lock simultaneously, but writers get exclusive access.

```go
var mu sync.RWMutex

// Multiple readers can call this concurrently
mu.RLock()
// ... read operation ...
mu.RUnlock()

// Only one writer at a time
mu.Lock()
// ... write operation ...
mu.Unlock()
```

---

## Part 6: Common Patterns & Idioms

### 6.1 Generator Pattern

```go
func fibonacci() <-chan int {
    ch := make(chan int)
    go func() {
        a, b := 0, 1
        for {
            ch <- a
            a, b = b, a+b
        }
    }()
    return ch
}

// Usage
for num := range fibonacci() {
    if num > 100 {
        break
    }
    fmt.Println(num)
}
```

---

### 6.2 Done Channel Pattern

**Purpose**: Signal cancellation/shutdown.

```go
func worker(done <-chan struct{}) {
    for {
        select {
        case <-done:
            return
        default:
            // Do work
        }
    }
}

done := make(chan struct{})
go worker(done)
// ... later ...
close(done) // Signal worker to stop
```

**Why `struct{}`?** It occupies zero bytes — most memory-efficient signal.

---

### 6.3 Context Package (Modern Approach)

**Purpose**: Carry deadlines, cancellation signals, and request-scoped values.

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func worker(ctx context.Context, id int) {
    for {
        select {
        case <-ctx.Done():
            fmt.Printf("Worker %d cancelled\n", id)
            return
        default:
            fmt.Printf("Worker %d working...\n", id)
            time.Sleep(500 * time.Millisecond)
        }
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    
    go worker(ctx, 1)
    go worker(ctx, 2)
    
    time.Sleep(3 * time.Second)
}
```

---

## Part 7: Performance & Best Practices

### 7.1 Channel Direction

**Always specify direction** when possible — enforces compile-time safety.

```go
func send(ch chan<- int) {  // Send-only
    ch <- 42
}

func receive(ch <-chan int) {  // Receive-only
    val := <-ch
}
```

---

### 7.2 Buffered vs Unbuffered Decision Tree

```
                Start
                  │
            Need strict ordering?
             /         \
          YES           NO
           │             │
      Unbuffered    Known burst size?
                      /         \
                   YES           NO
                    │             │
              Buffered      Start unbuffered,
              (size N)      measure, optimize
```

---

### 7.3 Avoid Goroutine Leaks

**Leak**: Goroutine that never terminates.

**Common causes:**
1. Channel never closed
2. No cancellation mechanism

**Solution**: Always provide exit path via `done` channel or `context`.

---

## Part 8: Comparison — Go vs Rust

| **Aspect**          | **Go (Channels)**                          | **Rust (mpsc, crossbeam)**                |
|---------------------|--------------------------------------------|--------------------------------------------|
| **Memory Model**    | GC-managed, channels copied                | Ownership-based, zero-copy possible        |
| **Safety**          | Runtime panics                             | Compile-time guarantees                    |
| **Performance**     | Good, slight GC overhead                   | Excellent, no GC overhead                  |
| **Ease of Use**     | Simple, intuitive                          | Steeper learning curve                     |
| **Concurrency**     | Goroutines (green threads)                 | OS threads + async                         |

---

## Mental Models for Mastery

1. **Chunking**: Group related channel operations (send-close, receive-check) as atomic mental units.
2. **Flow State**: Visualize data flowing through channels like water through pipes.
3. **Constraint-Based Thinking**: Buffered = flow control, Unbuffered = synchronization.

---

## Summary Flowchart

```
Need concurrent communication?
         │
    Use channels
         │
    ┌────┴────┐
    │         │
Sync?      Async?
│            │
Unbuffered   Buffered
    │         │
    └────┬────┘
         │
   Pattern needed?
    │    │    │
Pipeline Fan Worker
         -out Pool
         Fan
         -in
```

---

This guide provides the **foundational mastery** needed for goroutine communication. Practice these patterns deliberately, and you'll develop the intuition to architect complex concurrent systems with clarity and elegance.

What specific pattern would you like to implement or explore deeper?