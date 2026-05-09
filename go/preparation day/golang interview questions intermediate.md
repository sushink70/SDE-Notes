# Golang Intermediate Interview Questions — Complete & In-Depth Guide

> **Purpose:** Build a strong mental model for thinking about Go programs efficiently, correctly, and idiomatically. Every concept here is explained from first principles with ASCII architecture diagrams and real Go implementations.

---

## Table of Contents

1. [Go Runtime & Scheduler (GMP Model)](#1-go-runtime--scheduler-gmp-model)
2. [Goroutines — Deep Dive](#2-goroutines--deep-dive)
3. [Channels — Every Detail](#3-channels--every-detail)
4. [Select Statement](#4-select-statement)
5. [sync Package — Mutexes, WaitGroups, Once, Cond](#5-sync-package)
6. [sync/atomic — Lock-Free Programming](#6-syncatomic--lock-free-programming)
7. [Context Package](#7-context-package)
8. [Memory Model & Happens-Before](#8-go-memory-model--happens-before)
9. [Interfaces & Embedding](#9-interfaces--embedding)
10. [Error Handling — Wrapping, Unwrapping, Sentinel Errors](#10-error-handling)
11. [Defer, Panic, Recover](#11-defer-panic-recover)
12. [Closures & Function Values](#12-closures--function-values)
13. [Slices — Internals & Gotchas](#13-slices--internals--gotchas)
14. [Maps — Internals & Gotchas](#14-maps--internals--gotchas)
15. [Pointers, Value vs Reference Semantics](#15-pointers-value-vs-reference-semantics)
16. [Structs — Methods, Embedding, Promotion](#16-structs--methods-embedding-promotion)
17. [Generics (Go 1.18+)](#17-generics-go-118)
18. [Reflection](#18-reflection)
19. [Memory Management & Garbage Collector](#19-memory-management--garbage-collector)
20. [Escape Analysis & Stack vs Heap](#20-escape-analysis--stack-vs-heap)
21. [HTTP Server Patterns](#21-http-server-patterns)
22. [Testing — Unit, Table-Driven, Benchmarks, Fuzz](#22-testing)
23. [Concurrency Patterns](#23-concurrency-patterns)
24. [Race Conditions & the Race Detector](#24-race-conditions--the-race-detector)
25. [Package Design & init()](#25-package-design--init)
26. [Build Tags & Conditional Compilation](#26-build-tags--conditional-compilation)
27. [Common Pitfalls & Gotchas](#27-common-pitfalls--gotchas)

---

## 1. Go Runtime & Scheduler (GMP Model)

### What Is the GMP Model?

Go uses a **cooperative + preemptive** scheduler based on the GMP model. Understanding this is the foundation for reasoning about goroutine performance, deadlocks, and concurrency bugs.

```
┌─────────────────────────────────────────────────────────────────┐
│                        GO RUNTIME                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │                   Global Run Queue (GRQ)                  │   │
│  │        [G] [G] [G] [G] [G] [G] [G] [G]                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│           │              │              │                        │
│           ▼              ▼              ▼                        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │      P 0     │ │      P 1     │ │      P 2     │  ...        │
│  │  Local RQ:   │ │  Local RQ:   │ │  Local RQ:   │            │
│  │  [G][G][G]   │ │  [G][G][G]   │ │  [G][G][G]   │            │
│  │              │ │              │ │              │            │
│  │  Running: M0─┼─│  Running: M1─┼─│  Running: M2─┼─          │
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘            │
│         │                │                │                     │
│  ┌──────▼──┐      ┌──────▼──┐      ┌──────▼──┐                 │
│  │  M (OS  │      │  M (OS  │      │  M (OS  │                 │
│  │ Thread) │      │ Thread) │      │ Thread) │                 │
│  └─────────┘      └─────────┘      └─────────┘                 │
│                                                                 │
│  G = Goroutine    P = Processor (logical)   M = Machine/Thread  │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Blocking Syscall Scenario                       │   │
│  │                                                           │   │
│  │  P0──►M0 (blocked in syscall)                            │   │
│  │   │                                                       │   │
│  │   └──►M3 (new/idle thread) ◄── P0 detaches & reattaches  │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

### G — Goroutine
- A lightweight user-space thread managed by the Go runtime.
- Starts with ~2–8 KB stack (grows/shrinks dynamically up to 1 GB by default).
- Has its own stack, program counter, and state (runnable, running, blocked, dead).

### P — Processor
- An abstract resource that represents a "context" for running Go code.
- Number of Ps = `GOMAXPROCS` (defaults to number of CPU cores).
- Each P has a **Local Run Queue (LRQ)** holding up to 256 goroutines.
- P acts as the scheduler — it picks goroutines and hands them to M for execution.

### M — Machine (OS Thread)
- The actual OS-level thread that executes goroutines.
- Can be more Ms than Ps (blocked syscalls create new Ms).
- Default max = 10,000 (configurable via `runtime/debug.SetMaxThreads`).

### Work Stealing

```
  P0 LRQ: [G1, G2, G3, G4]        P1 LRQ: [] (empty!)
                                        │
                                        │  P1 steals half from P0
                                        ▼
  P0 LRQ: [G1, G2]                P1 LRQ: [G3, G4]
```

When a P's local queue is empty, it steals goroutines from:
1. Another P's local run queue (steals half).
2. The global run queue.
3. The network poller (goroutines waiting on I/O).

### Preemption (Go 1.14+)

Before 1.14, preemption only happened at function call sites. Since 1.14, the runtime uses **asynchronous preemption** via OS signals (`SIGURG`), allowing any goroutine to be preempted even in tight loops.

```go
// Before Go 1.14, this could starve other goroutines:
func main() {
    runtime.GOMAXPROCS(1)
    go func() {
        for {} // infinite loop with no function calls — blocked scheduler
    }()
    time.Sleep(time.Second) // might never run before 1.14
}
// After 1.14: preemption via SIGURG fixes this
```

### Interview Questions

**Q: What happens when a goroutine makes a blocking syscall?**

The M is handed to the OS and blocks. The runtime **detaches the P** from that M and attaches it to a free or new M so other goroutines keep running. When the syscall returns, the goroutine is put back in the run queue and the old M either parks or exits.

**Q: How does GOMAXPROCS affect performance?**

`GOMAXPROCS` controls how many Ps (and thus OS threads) actively execute Go code in parallel. Setting it to 1 makes the program effectively single-threaded at the Go level. For CPU-bound work, match it to core count. For I/O-bound work, it matters less since blocked goroutines don't consume a P.

---

## 2. Goroutines — Deep Dive

### Goroutine Stack Growth

```
  Initial goroutine stack: 2KB
         │
         │ function call needs more space
         ▼
  Stack too small → runtime allocates new, larger stack
  Copies all data to new stack
  Updates all pointers to point to new locations
  Old stack is freed
         │
         ▼
  New stack: 4KB, 8KB, 16KB... (doubles each time)
  
  Maximum: 1GB (adjustable via runtime/debug.SetMaxStack)
```

Goroutine stacks are contiguous and use **stack copying** (not segmented stacks, which were used prior to Go 1.4). This means pointers into the stack must be updated when a stack grows — Go's GC knows all stack pointer locations.

### Goroutine States

```
             ┌──────────────────┐
    NEW  ───►│    _Grunnable    │◄──────────────────────┐
             │  (in run queue)  │                       │
             └────────┬─────────┘                       │
                      │ P picks it up                   │
                      ▼                                 │
             ┌──────────────────┐      preempted /      │
             │    _Grunning     │──── yield / chan ──────┘
             │  (on M/P pair)   │     send/recv
             └────────┬─────────┘
                      │
              ┌───────┴────────┐
              ▼                ▼
    ┌─────────────────┐  ┌─────────────────┐
    │   _Gwaiting     │  │   _Gsyscall     │
    │ (blocked on ch, │  │ (in OS syscall) │
    │  mutex, timer)  │  └────────┬────────┘
    └────────┬────────┘           │
             │                   │ syscall returns
             │ condition met      ▼
             └──────────► _Grunnable
             
             _Gdead ← goroutine function returns
```

### Goroutine Lifecycle Example

```go
package main

import (
    "fmt"
    "runtime"
    "sync"
)

func main() {
    var wg sync.WaitGroup

    // Print goroutine count before
    fmt.Printf("Goroutines before: %d\n", runtime.NumGoroutine())

    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            fmt.Printf("Goroutine %d running\n", id)
        }(i)
    }

    fmt.Printf("Goroutines during: %d\n", runtime.NumGoroutine())
    wg.Wait()
    fmt.Printf("Goroutines after: %d\n", runtime.NumGoroutine())
}
```

### Goroutine Leak — The Silent Killer

A goroutine leak occurs when goroutines are spawned but never terminate. They consume memory and CPU forever.

```go
// BAD: goroutine leaks if no one reads from ch
func leak() {
    ch := make(chan int)
    go func() {
        val := <-ch // blocks forever if nobody sends
        fmt.Println(val)
    }()
    // function returns, ch goes out of scope, goroutine leaks
}

// GOOD: use context for cancellation
func noLeak(ctx context.Context) {
    ch := make(chan int)
    go func() {
        select {
        case val := <-ch:
            fmt.Println(val)
        case <-ctx.Done():
            return // exits cleanly
        }
    }()
}
```

**Detecting leaks:** Use `runtime.NumGoroutine()` in tests, or the `goleak` package.

---

## 3. Channels — Every Detail

### Channel Internals

A channel is a **typed, thread-safe queue** implemented as a `hchan` struct in the runtime.

```
  hchan struct layout (simplified):

  ┌─────────────────────────────────────────────────────────┐
  │  qcount   uint   — number of elements in queue          │
  │  dataqsiz uint   — capacity (0 for unbuffered)          │
  │  buf      *array — pointer to circular buffer           │
  │  elemsize uint16 — size of each element                 │
  │  closed   uint32 — 0=open, 1=closed                    │
  │  sendx    uint   — send index into buf                  │
  │  recvx    uint   — receive index into buf               │
  │  recvq    waitq  — list of blocked receivers            │
  │  sendq    waitq  — list of blocked senders              │
  │  lock     mutex  — protects all fields                  │
  └─────────────────────────────────────────────────────────┘

  Circular Buffer (buffered channel cap=4):

  buf: [ E0 | E1 | E2 | E3 ]
              ▲              ▲
           recvx           sendx
           (read here)   (write here)
```

### Unbuffered Channel — Synchronous Rendezvous

```
  Sender goroutine                 Receiver goroutine
       │                                  │
       │ ch <- value                      │
       │ (blocks until receiver ready)    │
       ├──────────────────────────────────►│
       │           value transferred       │
       │◄──────────────────────────────────┤
       │ (both unblock simultaneously)     │
       │                                  │
```

```go
ch := make(chan int) // unbuffered

go func() {
    ch <- 42 // blocks until someone receives
}()

val := <-ch // blocks until someone sends
fmt.Println(val) // 42
```

### Buffered Channel — Asynchronous up to Capacity

```
  Buffered channel: make(chan int, 3)

  State: empty
  ┌────┬────┬────┐
  │    │    │    │   len=0, cap=3
  └────┴────┴────┘

  After ch <- 1
  ┌────┬────┬────┐
  │ 1  │    │    │   len=1, cap=3
  └────┴────┴────┘

  After ch <- 2, ch <- 3
  ┌────┬────┬────┐
  │ 1  │ 2  │ 3  │   len=3, cap=3 (FULL)
  └────┴────┴────┘

  ch <- 4 ← BLOCKS here until someone reads
```

```go
ch := make(chan int, 3)
ch <- 1 // non-blocking
ch <- 2 // non-blocking
ch <- 3 // non-blocking
ch <- 4 // BLOCKS — buffer full

// receive unblocks
fmt.Println(<-ch) // 1 (FIFO order)
```

### Directional Channels

```go
// Send-only channel
func producer(out chan<- int) {
    out <- 42
    // <-out  // compile error: cannot receive from send-only channel
}

// Receive-only channel
func consumer(in <-chan int) {
    val := <-in
    // in <- 1 // compile error: cannot send to receive-only channel
    fmt.Println(val)
}

func main() {
    ch := make(chan int, 1)
    producer(ch) // bidirectional implicitly converts to chan<- int
    consumer(ch) // bidirectional implicitly converts to <-chan int
}
```

### Closing Channels — Rules & Behavior

```
  Channel behaviors:

  ┌────────────────┬─────────────────┬──────────────────────────┐
  │  Operation     │  Open Channel   │  Closed Channel          │
  ├────────────────┼─────────────────┼──────────────────────────┤
  │  Send          │  Normal         │  PANIC                   │
  │  Receive       │  Normal/block   │  Returns zero+false      │
  │  Close         │  Normal         │  PANIC                   │
  │  Nil send      │  BLOCK forever  │  —                       │
  │  Nil receive   │  BLOCK forever  │  —                       │
  │  Nil close     │  PANIC          │  —                       │
  └────────────────┴─────────────────┴──────────────────────────┘
```

```go
ch := make(chan int, 2)
ch <- 1
ch <- 2
close(ch)

// Range over closed channel — safe, stops when drained
for v := range ch {
    fmt.Println(v) // prints 1, then 2, then loop ends
}

// Two-value receive — detect if channel is closed
v, ok := <-ch
fmt.Println(v, ok) // 0, false (channel closed and empty)
```

**Golden Rules:**
1. Only the **sender** should close a channel, never the receiver.
2. Never close a channel twice (panic).
3. Never send on a closed channel (panic).
4. A nil channel blocks forever on both send and receive (useful in select).

### Channel Patterns

**Done channel for signaling:**
```go
done := make(chan struct{}) // zero-size struct — no memory allocation

go func() {
    // do work
    close(done) // signal completion
}()

<-done // wait for signal
```

**Fan-out: one sender, multiple receivers:**
```go
func fanOut(in <-chan int, numWorkers int) []<-chan int {
    outputs := make([]<-chan int, numWorkers)
    for i := 0; i < numWorkers; i++ {
        out := make(chan int)
        outputs[i] = out
        go func(ch chan<- int) {
            for v := range in {
                ch <- v
            }
            close(ch)
        }(out)
    }
    return outputs
}
```

**Fan-in: multiple senders, one receiver:**
```go
func fanIn(channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup

    output := func(ch <-chan int) {
        defer wg.Done()
        for v := range ch {
            merged <- v
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go output(ch)
    }

    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}
```

**Pipeline:**
```go
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

func square(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

func main() {
    // Pipeline: generate → square → print
    for n := range square(square(generate(2, 3, 4))) {
        fmt.Println(n) // 16, 81, 256
    }
}
```

---

## 4. Select Statement

`select` lets a goroutine wait on **multiple channel operations simultaneously**. It picks a ready case at random if multiple are ready.

### How select Works Internally

```
  select {
      case v := <-ch1:   ─── register recv on ch1's recvq
      case ch2 <- val:   ─── register send on ch2's sendq
      default:           ─── if none ready, execute immediately
  }

  Runtime algorithm:
  1. Lock all channels involved (deterministic order to avoid deadlock)
  2. Check each case for readiness
  3a. If one is ready → execute it, unlock all, done
  3b. If multiple ready → pick one uniformly at random
  3c. If none ready and default → execute default, unlock all
  3d. If none ready and no default → park goroutine on ALL channel queues
  4. When any channel becomes ready, wake goroutine, dequeue from all others
```

```go
// Basic select
select {
case msg := <-ch1:
    fmt.Println("received from ch1:", msg)
case ch2 <- "hello":
    fmt.Println("sent to ch2")
case <-time.After(1 * time.Second):
    fmt.Println("timeout!")
default:
    fmt.Println("no channel ready")
}
```

### Nil Channel in Select — A Power Pattern

A nil channel **never becomes ready**. This lets you disable cases dynamically:

```go
func merge(a, b <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for a != nil || b != nil {
            select {
            case v, ok := <-a:
                if !ok {
                    a = nil // disable this case
                    continue
                }
                out <- v
            case v, ok := <-b:
                if !ok {
                    b = nil // disable this case
                    continue
                }
                out <- v
            }
        }
    }()
    return out
}
```

### Timeout and Cancellation Patterns

```go
func fetchWithTimeout(url string, timeout time.Duration) (string, error) {
    resultCh := make(chan string, 1)
    errCh := make(chan error, 1)

    go func() {
        // simulate HTTP call
        time.Sleep(200 * time.Millisecond)
        resultCh <- "data"
    }()

    select {
    case result := <-resultCh:
        return result, nil
    case err := <-errCh:
        return "", err
    case <-time.After(timeout):
        return "", fmt.Errorf("request timed out after %v", timeout)
    }
}
```

---

## 5. sync Package

### sync.Mutex

A mutual exclusion lock. Only one goroutine can hold the lock at a time.

```
  Goroutine A          Goroutine B
      │                    │
      │  mu.Lock()         │  mu.Lock()
      │  (acquired!)       │  (BLOCKED — waits)
      │                    │
      │  critical section  │    ...waiting...
      │                    │
      │  mu.Unlock()       │
      │                    │  mu.Lock()
      │                    │  (acquired!)
      │                    │  critical section
      │                    │  mu.Unlock()
```

```go
type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock() // always use defer to avoid forgetting unlock
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}
```

**Critical Rules:**
- Always lock/unlock in the same goroutine.
- Never copy a `sync.Mutex` after first use (embed a pointer or use `go vet`).
- Prefer `defer mu.Unlock()` immediately after `mu.Lock()`.

### sync.RWMutex — Read/Write Lock

Multiple readers can hold the lock simultaneously. Only one writer at a time, and a writer blocks all readers.

```
  RWMutex states:
  
  ─ No lock held ──────────────────────────────────────
  
  ─ RLock held ────────────────────────────────────────
  │  RLock A │  RLock B │  RLock C │  (all concurrent)
  
  ─ Lock (write) requested ────────────────────────────
  │  Existing readers finish... │  BLOCKS new RLock    │
  │  Writer acquires lock       │                      │
  
  ─ Lock held ─────────────────────────────────────────
  │  ONLY writer goroutine │  All others blocked       │
```

```go
type Cache struct {
    mu    sync.RWMutex
    items map[string]string
}

// Multiple goroutines can call Get concurrently
func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    val, ok := c.items[key]
    return val, ok
}

// Set is exclusive
func (c *Cache) Set(key, value string) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = value
}
```

### sync.WaitGroup

Wait for a collection of goroutines to finish.

```
  wg.Add(3)          ──► internal counter = 3

  go work()          wg.Done() ──► counter = 2
  go work()          wg.Done() ──► counter = 1
  go work()          wg.Done() ──► counter = 0

  wg.Wait()          ──► blocks until counter = 0
```

```go
func processItems(items []string) {
    var wg sync.WaitGroup

    for _, item := range items {
        wg.Add(1)
        go func(it string) {
            defer wg.Done()
            // process it
            fmt.Println("processing:", it)
        }(item) // pass item as argument — avoids closure capture bug
    }

    wg.Wait()
    fmt.Println("all done")
}
```

**Common Mistake:** Calling `wg.Add(1)` inside the goroutine can race with `wg.Wait()`.

```go
// WRONG: Add is inside goroutine — wg.Wait() may return before Add is called
go func() {
    wg.Add(1)    // race!
    defer wg.Done()
}()
wg.Wait()

// CORRECT: Add before launching goroutine
wg.Add(1)
go func() {
    defer wg.Done()
}()
wg.Wait()
```

### sync.Once

Ensures a function is called **exactly once**, regardless of how many goroutines call it.

```go
var (
    instance *Database
    once     sync.Once
)

func GetDatabase() *Database {
    once.Do(func() {
        instance = &Database{
            conn: openConnection(), // expensive, called once only
        }
    })
    return instance
}
```

**How it works internally:** Uses an atomic flag + mutex. After first call completes, subsequent calls see the flag and return immediately without locking.

### sync.Cond — Condition Variable

Used when goroutines need to wait for a specific condition, not just mutual exclusion.

```go
type Queue struct {
    mu    sync.Mutex
    cond  *sync.Cond
    items []int
}

func NewQueue() *Queue {
    q := &Queue{}
    q.cond = sync.NewCond(&q.mu)
    return q
}

func (q *Queue) Push(item int) {
    q.mu.Lock()
    q.items = append(q.items, item)
    q.cond.Signal() // wake one waiting goroutine
    q.mu.Unlock()
}

func (q *Queue) Pop() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == 0 { // loop — re-check condition after wakeup
        q.cond.Wait() // atomically releases lock and waits
    }
    item := q.items[0]
    q.items = q.items[1:]
    return item
}
```

**Why the `for` loop?** `Wait()` can return spuriously (rare but possible). Always re-check the condition after waking.

### sync.Map — Concurrent Map

Optimized for cases where entries are written once and read many times, or when goroutines work on disjoint sets of keys.

```go
var m sync.Map

// Store
m.Store("key", "value")

// Load
val, ok := m.Load("key")

// LoadOrStore (atomic get-or-set)
actual, loaded := m.LoadOrStore("key", "default")

// Delete
m.Delete("key")

// Range (iterate — snapshot not guaranteed)
m.Range(func(k, v interface{}) bool {
    fmt.Println(k, v)
    return true // return false to stop iteration
})
```

**When to use sync.Map vs map+RWMutex:**
- `sync.Map` is better when: mostly reads with occasional writes, or when goroutines touch different keys.
- `map+RWMutex` is usually better when: frequent writes, or when you need `len()`.

---

## 6. sync/atomic — Lock-Free Programming

Atomic operations are CPU-level instructions that are indivisible. They avoid the overhead of mutexes for simple operations.

```go
import "sync/atomic"

var counter int64

// Increment atomically
atomic.AddInt64(&counter, 1)

// Load atomically (safe read)
val := atomic.LoadInt64(&counter)

// Store atomically
atomic.StoreInt64(&counter, 100)

// Compare-And-Swap (CAS) — the foundation of lock-free algorithms
// Sets new value only if current value == old
swapped := atomic.CompareAndSwapInt64(&counter, old, new)
```

### Lock-Free Stack (CAS-based)

```go
type node struct {
    val  int
    next *node
}

type LockFreeStack struct {
    head atomic.Pointer[node]
}

func (s *LockFreeStack) Push(val int) {
    n := &node{val: val}
    for {
        old := s.head.Load()
        n.next = old
        if s.head.CompareAndSwap(old, n) { // atomic CAS
            return
        }
        // CAS failed — another goroutine changed head; retry
    }
}

func (s *LockFreeStack) Pop() (int, bool) {
    for {
        old := s.head.Load()
        if old == nil {
            return 0, false
        }
        if s.head.CompareAndSwap(old, old.next) {
            return old.val, true
        }
    }
}
```

**Go 1.19+ `atomic.Pointer[T]`** is the type-safe way to do atomic pointer operations.

---

## 7. Context Package

Context carries deadlines, cancellation signals, and request-scoped values across API boundaries and goroutines.

### Context Tree

```
  context.Background()
         │
         ├── WithCancel(bg)           → cancel() kills this subtree
         │        │
         │        ├── WithTimeout(ctx, 5s)  → auto-cancel after 5s
         │        │        │
         │        │        └── WithValue(ctx, "userID", 42)
         │        │
         │        └── WithDeadline(ctx, t)  → cancel at absolute time t
         │
         └── context.TODO()           → placeholder (same as Background)

  When a parent is cancelled → ALL children are immediately cancelled
```

### Context Interface

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool) // when will it expire?
    Done() <-chan struct{}                    // closed when cancelled
    Err() error                              // why cancelled? (nil if not yet)
    Value(key any) any                       // get a value by key
}
```

### WithCancel — Manual Cancellation

```go
func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel() // always defer cancel to avoid context leak

    go worker(ctx)
    go worker(ctx)

    time.Sleep(2 * time.Second)
    cancel() // signal all workers to stop
    time.Sleep(100 * time.Millisecond)
}

func worker(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("worker stopping:", ctx.Err())
            return
        default:
            // do work
            time.Sleep(100 * time.Millisecond)
        }
    }
}
```

### WithTimeout and WithDeadline

```go
// Timeout: relative duration from now
ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
defer cancel()

// Deadline: absolute point in time
deadline := time.Now().Add(3 * time.Second)
ctx, cancel = context.WithDeadline(context.Background(), deadline)
defer cancel()

// Check in a blocking call
req, _ := http.NewRequestWithContext(ctx, "GET", "https://example.com", nil)
resp, err := http.DefaultClient.Do(req)
if err != nil {
    if errors.Is(err, context.DeadlineExceeded) {
        fmt.Println("request timed out")
    }
}
```

### WithValue — Request-Scoped Values

```go
// Use unexported type for keys to avoid collisions across packages
type contextKey string

const userIDKey contextKey = "userID"

func withUserID(ctx context.Context, userID int) context.Context {
    return context.WithValue(ctx, userIDKey, userID)
}

func getUserID(ctx context.Context) (int, bool) {
    id, ok := ctx.Value(userIDKey).(int)
    return id, ok
}
```

**Rules for WithValue:**
- Use only for request-scoped data (auth tokens, request IDs), NOT for passing function parameters.
- Always use an unexported custom key type to prevent collisions.
- Values must be safe for concurrent access.

### Context Propagation Pattern

```go
func HandleRequest(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // HTTP handler gets context from request

    userID, _ := getUserID(ctx)
    data, err := fetchData(ctx, userID) // pass ctx down the call chain
    if err != nil {
        if errors.Is(err, context.Canceled) {
            // client disconnected
            return
        }
        http.Error(w, err.Error(), 500)
        return
    }
    json.NewEncoder(w).Encode(data)
}

func fetchData(ctx context.Context, userID int) ([]byte, error) {
    // Always check ctx before expensive operations
    select {
    case <-ctx.Done():
        return nil, ctx.Err()
    default:
    }
    
    // Pass ctx to database calls, HTTP calls, etc.
    return db.QueryContext(ctx, "SELECT ...", userID)
}
```

---

## 8. Go Memory Model & Happens-Before

The Go Memory Model defines when one goroutine's write to a variable is **guaranteed to be visible** to a read in another goroutine.

### The Core Rule

> **"If event A happens-before event B, then A's effects are visible to B."**

Without a happens-before relationship, reads may see stale values, zero values, or partially written values — even on modern hardware.

### Happens-Before Guarantees

```
  ┌─────────────────────────────────────────────────────────────┐
  │  SYNCHRONIZED EVENTS (establish happens-before):            │
  │                                                             │
  │  1. Channel send BEFORE receive on same channel             │
  │     ch <- x ─HB─► v := <-ch                               │
  │                                                             │
  │  2. Closing a channel BEFORE receive returns zero           │
  │     close(ch) ─HB─► v, ok := <-ch (ok=false)              │
  │                                                             │
  │  3. sync.Mutex: Unlock BEFORE next Lock                     │
  │     mu.Unlock() ─HB─► mu.Lock()                            │
  │                                                             │
  │  4. sync.Once: once.Do completion BEFORE any return         │
  │     f() inside Do ─HB─► once.Do returns                    │
  │                                                             │
  │  5. goroutine start: go statement BEFORE goroutine starts   │
  │     go f() ─HB─► f() begins                                │
  │                                                             │
  │  6. goroutine finish (via WaitGroup/channel signal)         │
  └─────────────────────────────────────────────────────────────┘
```

### Data Race Example

```go
// DATA RACE: no happens-before between goroutines
var x int

go func() { x = 1 }()       // write
fmt.Println(x)               // read — MAY see 0 or 1, undefined behavior!

// FIXED: use channel to synchronize
done := make(chan struct{})
go func() {
    x = 1
    close(done) // write happens-before close
}()
<-done         // close happens-before receive
fmt.Println(x) // guaranteed to see x=1
```

---

## 9. Interfaces & Embedding

### Interface Internals — iface and eface

In Go, an interface value is a **two-word data structure**:

```
  Non-empty interface (iface):        Empty interface (eface / any):
  ┌────────────────────┐              ┌────────────────────┐
  │  *itab             │              │  *_type            │
  │  (type + method    │              │  (concrete type    │
  │   table pointer)   │              │   descriptor)      │
  ├────────────────────┤              ├────────────────────┤
  │  data pointer      │              │  data pointer      │
  │  (to concrete val) │              │  (to concrete val) │
  └────────────────────┘              └────────────────────┘

  itab:
  ┌──────────────────────────────────┐
  │  inter  *interfacetype           │  ← which interface
  │  type   *_type                   │  ← which concrete type
  │  hash   uint32                   │  ← for type assertions
  │  fun    [1]uintptr               │  ← method pointers (vtable)
  └──────────────────────────────────┘
```

### Interface Satisfaction — Implicit

```go
type Writer interface {
    Write(p []byte) (n int, err error)
}

// *os.File satisfies Writer because it has Write method
var w Writer = os.Stdout // no "implements" keyword needed

// Compile-time check (idiomatic Go):
var _ Writer = (*MyWriter)(nil) // if MyWriter doesn't implement Writer, compile error
```

### Nil Interface vs Interface Holding Nil

One of Go's most famous gotchas:

```go
type MyError struct{ msg string }
func (e *MyError) Error() string { return e.msg }

func mayFail(fail bool) error {
    var err *MyError = nil // typed nil pointer
    if fail {
        err = &MyError{"something failed"}
    }
    return err // RETURNS non-nil interface wrapping a nil pointer!
}

func main() {
    err := mayFail(false)
    if err != nil { // THIS IS TRUE — interface is non-nil!
        fmt.Println("unexpected error:", err) // prints: <nil>
    }
}
```

```
  Interface value when returning typed nil:
  ┌────────────────────┐
  │  *itab = *MyError  │  ← non-nil! has type info
  ├────────────────────┤
  │  data = nil        │  ← nil data pointer
  └────────────────────┘
  
  This interface != nil because the type field is set.

  Correct fix:
  ┌────────────────────┐
  │  *itab = nil       │  ← nil interface
  ├────────────────────┤
  │  data = nil        │
  └────────────────────┘
```

```go
// CORRECT: return untyped nil
func mayFail(fail bool) error {
    if fail {
        return &MyError{"something failed"}
    }
    return nil // untyped nil → both itab and data are nil
}
```

### Type Assertions and Type Switches

```go
var i interface{} = "hello"

// Type assertion — panics if wrong type
s := i.(string)

// Safe type assertion — never panics
s, ok := i.(string)
if ok {
    fmt.Println(s)
}

// Type switch
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int: %d", v)
    case string:
        return fmt.Sprintf("string: %q", v)
    case []byte:
        return fmt.Sprintf("bytes: %d long", len(v))
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
}
```

### Embedding Interfaces

```go
// ReadWriter embeds Reader and Writer
type Reader interface {
    Read(p []byte) (n int, err error)
}

type Writer interface {
    Write(p []byte) (n int, err error)
}

type ReadWriter interface {
    Reader // promoted
    Writer // promoted
}

// A struct embedding an interface (useful for mocking)
type MockReadWriter struct {
    io.ReadWriter // embed the interface — zero value gives nil panic on call
}
```

### Struct Embedding & Method Promotion

```go
type Animal struct {
    Name string
}

func (a Animal) Speak() string {
    return a.Name + " speaks"
}

type Dog struct {
    Animal        // embedded — Dog "inherits" Animal's methods
    Breed  string
}

func (d Dog) Fetch() string {
    return d.Name + " fetches!" // can access Animal.Name directly
}

d := Dog{Animal: Animal{"Rex"}, Breed: "Lab"}
fmt.Println(d.Speak())  // promoted method — same as d.Animal.Speak()
fmt.Println(d.Name)     // promoted field
fmt.Println(d.Fetch())
```

**Embedding is NOT inheritance.** There's no polymorphism through embedding alone — only through interfaces. The embedded type can be accessed directly as `d.Animal`.

---

## 10. Error Handling

### Error Interface

```go
type error interface {
    Error() string
}
```

Any type with an `Error() string` method satisfies the `error` interface.

### Custom Errors

```go
// Simple custom error
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error on field %q: %s", e.Field, e.Message)
}

// Error with additional context
type HTTPError struct {
    StatusCode int
    Status     string
    Body       string
}

func (e *HTTPError) Error() string {
    return fmt.Sprintf("HTTP %d: %s", e.StatusCode, e.Status)
}
```

### Sentinel Errors

Predefined, package-level error values that callers check for identity.

```go
var (
    ErrNotFound   = errors.New("not found")
    ErrPermission = errors.New("permission denied")
    ErrTimeout    = errors.New("operation timed out")
)

func findUser(id int) (*User, error) {
    if id <= 0 {
        return nil, ErrNotFound
    }
    // ...
}

// Caller checks:
user, err := findUser(0)
if errors.Is(err, ErrNotFound) {
    // handle not found
}
```

### Error Wrapping (Go 1.13+)

```
  Error chain:
  
  database error: "connection refused"
          │
          │ fmt.Errorf("query failed: %w", err)
          ▼
  "query failed: database error: connection refused"
          │
          │ fmt.Errorf("getUserByID(%d) failed: %w", id, err)
          ▼
  "getUserByID(42) failed: query failed: database error: connection refused"
  
  errors.Is(err, originalErr) → true (searches the whole chain)
  errors.As(err, &target)     → true (finds first matching type in chain)
```

```go
// Wrap an error with context
func queryDB(sql string) error {
    err := db.Exec(sql)
    if err != nil {
        return fmt.Errorf("queryDB(%q): %w", sql, err) // %w wraps
    }
    return nil
}

func getUser(id int) (*User, error) {
    err := queryDB("SELECT ...")
    if err != nil {
        return nil, fmt.Errorf("getUser(%d): %w", id, err)
    }
    return &User{}, nil
}

// At the call site:
err := getUser(42)

// errors.Is unwraps until it finds the target
if errors.Is(err, sql.ErrNoRows) {
    fmt.Println("user not found")
}

// errors.As unwraps until it finds a matching type
var dbErr *DBError
if errors.As(err, &dbErr) {
    fmt.Println("DB error code:", dbErr.Code)
}

// Unwrap manually
fmt.Println(errors.Unwrap(err)) // one level up
```

### errors.Join (Go 1.20+)

```go
err1 := errors.New("first error")
err2 := errors.New("second error")

// Join multiple errors into one
combined := errors.Join(err1, err2)
fmt.Println(combined) // "first error\nsecond error"

errors.Is(combined, err1) // true
errors.Is(combined, err2) // true
```

### Custom Unwrap (multiple errors)

```go
type MultiError struct {
    Errors []error
}

func (m *MultiError) Error() string {
    msgs := make([]string, len(m.Errors))
    for i, err := range m.Errors {
        msgs[i] = err.Error()
    }
    return strings.Join(msgs, "; ")
}

// Implement Unwrap for errors.Is/As traversal
func (m *MultiError) Unwrap() []error {
    return m.Errors
}
```

---

## 11. Defer, Panic, Recover

### Defer — Execution Order and Semantics

```
  func example() {
      defer fmt.Println("first deferred")   ─── pushed to defer stack
      defer fmt.Println("second deferred")  ─── pushed to defer stack
      defer fmt.Println("third deferred")   ─── pushed to defer stack
      fmt.Println("function body")
  }

  LIFO execution order:
  function body
  third deferred
  second deferred
  first deferred
```

### Defer with Named Return Values

```go
// Defer can modify named return values!
func readFile(path string) (content string, err error) {
    f, err := os.Open(path)
    if err != nil {
        return
    }
    defer func() {
        closeErr := f.Close()
        if err == nil { // only set err if no prior error
            err = closeErr
        }
    }()

    data, err := io.ReadAll(f)
    if err != nil {
        return
    }
    content = string(data)
    return
}
```

### Defer Argument Evaluation

```go
x := 10
defer fmt.Println(x) // x is evaluated NOW (=10), not at defer execution
x = 20
// prints: 10 (not 20)

// If you want deferred evaluation, use a closure:
defer func() {
    fmt.Println(x) // captured by reference — prints 20
}()
```

### Panic and Recover

```
  Normal execution:
  main() → funcA() → funcB() → funcC()
  
  Panic in funcC():
  funcC() panics
      │ unwinds to funcB(), runs funcB()'s defers
      │ unwinds to funcA(), runs funcA()'s defers
      │ unwinds to main(), runs main()'s defers
      │ process exits with stack trace
      
  Recover in funcA():
  funcC() panics
      │ unwinds to funcB(), runs funcB()'s defers
      │ unwinds to funcA(), runs funcA()'s defers
          │ defer calls recover() → catches panic value
          │ funcA() returns normally (with zero values)
      │ continues in main()
```

```go
func safeDiv(a, b int) (result int, err error) {
    defer func() {
        if r := recover(); r != nil {
            err = fmt.Errorf("panic recovered: %v", r)
        }
    }()
    return a / b, nil // panics if b == 0
}

func main() {
    result, err := safeDiv(10, 0)
    fmt.Println(result, err) // 0, "panic recovered: runtime error: integer divide by zero"
}
```

**Rules:**
- `recover()` only works inside a `defer` function.
- `recover()` returns `nil` if not called during a panic.
- Panics propagate across goroutine boundaries — each goroutine needs its own recover.
- Use panic/recover sparingly; prefer returning errors.

```go
// Pattern: recover at goroutine boundary to prevent crash
func safeGo(f func()) {
    go func() {
        defer func() {
            if r := recover(); r != nil {
                log.Printf("goroutine panicked: %v\n%s", r, debug.Stack())
            }
        }()
        f()
    }()
}
```

---

## 12. Closures & Function Values

### What Is a Closure?

A closure is a function value that captures variables from its surrounding scope. The captured variables are stored on the heap (escape analysis ensures this).

```
  func adder() func(int) int {
      sum := 0                     ← captured variable (lives on heap)
      return func(x int) int {     ← closure closes over sum
          sum += x
          return sum
      }
  }

  pos := adder()
  pos(1) → 1
  pos(2) → 3
  pos(3) → 6

  neg := adder()   ← new closure, new sum variable
  neg(10) → 10
```

```go
func adder() func(int) int {
    sum := 0
    return func(x int) int {
        sum += x
        return sum
    }
}

func main() {
    pos, neg := adder(), adder()
    for i := 0; i < 3; i++ {
        fmt.Println(pos(i), neg(-2*i))
    }
    // Output:
    // 0 0
    // 1 -2
    // 3 -6
}
```

### The Loop Variable Capture Bug

```go
// BUG: all goroutines capture the SAME variable i
funcs := make([]func(), 5)
for i := 0; i < 5; i++ {
    funcs[i] = func() {
        fmt.Println(i) // all print 5 (loop's final value)
    }
}
for _, f := range funcs { f() }

// FIX 1: pass i as argument (creates a new copy)
for i := 0; i < 5; i++ {
    i := i // shadow i with a new variable
    funcs[i] = func() {
        fmt.Println(i) // captures the new i
    }
}

// FIX 2: Go 1.22+ — loop variables are per-iteration
// (go 1.22 changed the semantics, each iteration has its own i)
```

### Closures as Middleware / Decorators

```go
type HandlerFunc func(http.ResponseWriter, *http.Request)

func withLogging(next HandlerFunc) HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        log.Printf("→ %s %s", r.Method, r.URL.Path)
        next(w, r)
        log.Printf("← %s %s (%v)", r.Method, r.URL.Path, time.Since(start))
    }
}

func withAuth(next HandlerFunc) HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        token := r.Header.Get("Authorization")
        if !validateToken(token) {
            http.Error(w, "Unauthorized", 401)
            return
        }
        next(w, r)
    }
}

// Chain middlewares:
handler := withLogging(withAuth(myHandler))
```

---

## 13. Slices — Internals & Gotchas

### Slice Header

A slice is a **three-word struct** — not an array.

```
  Slice header (on stack or in struct):
  ┌─────────────────────────────┐
  │  ptr  *T  (pointer to array)│
  │  len  int (number of elems) │
  │  cap  int (allocated space) │
  └─────────────────────────────┘
        │
        ▼
  Underlying array (on heap):
  ┌────┬────┬────┬────┬────┬────┐
  │  0 │  1 │  2 │  3 │  4 │  5 │   capacity = 6
  └────┴────┴────┴────┴────┴────┘
        ▲────────────┘
        len = 3 (visible elements)
```

### Slice Operations & Their Behavior

```go
a := []int{1, 2, 3, 4, 5}

// Reslicing shares underlying array
b := a[1:3]    // [2, 3], len=2, cap=4, shares array with a
b[0] = 99      // modifies a! a = [1, 99, 3, 4, 5]

// Append — may or may not allocate new array
c := append(a, 6)  // if cap > len: no allocation, uses same array
                   // if cap == len: allocates new (bigger) array, copies

// Three-index slice — limits capacity, prevents sharing
d := a[1:3:3]  // len=2, cap=2 — append will always allocate new array
```

### Append Growth Strategy

```
  len=0, cap=0
  append 1 elem → allocates cap=1
  append 1 elem → allocates cap=2
  append 1 elem → allocates cap=4
  append 1 elem → cap=4 (fits)
  append 1 elem → allocates cap=8
  ...
  (roughly doubles until large, then ~1.25x growth — Go 1.18+ uses smoother growth)
```

```go
// Pre-allocate when length is known — avoids repeated allocations
n := 1000
s := make([]int, 0, n) // len=0, cap=1000
for i := 0; i < n; i++ {
    s = append(s, i) // no allocation during loop
}
```

### Copy Semantics

```go
src := []int{1, 2, 3}
dst := make([]int, len(src))
copy(dst, src) // deep copy — independent arrays

dst[0] = 99
fmt.Println(src) // [1, 2, 3] — unchanged
fmt.Println(dst) // [99, 2, 3]
```

### Slice Tricks

```go
// Delete element at index i (preserves order)
s = append(s[:i], s[i+1:]...)

// Delete element at index i (O(1), changes order)
s[i] = s[len(s)-1]
s = s[:len(s)-1]

// Insert element at index i
s = append(s[:i+1], s[i:]...)
s[i] = newElem

// Reverse in place
for left, right := 0, len(s)-1; left < right; left, right = left+1, right-1 {
    s[left], s[right] = s[right], s[left]
}

// Filter without allocating new slice
n := 0
for _, x := range s {
    if keep(x) {
        s[n] = x
        n++
    }
}
s = s[:n]
```

---

## 14. Maps — Internals & Gotchas

### Map Internals

Go maps use **hash tables** with chaining via buckets (buckets hold 8 key-value pairs each).

```
  map[string]int internals:

  hmap struct:
  ┌──────────────────────────────────────────────────┐
  │  count     int      — number of elements         │
  │  B         uint8    — log2 of #buckets            │
  │  hash0     uint32   — random hash seed            │
  │  buckets   *bmap    — array of 2^B buckets        │
  │  oldbuckets *bmap   — old buckets during growth   │
  └──────────────────────────────────────────────────┘

  bucket (bmap) — holds up to 8 key/value pairs:
  ┌─────────────────────────────────────────────────┐
  │  tophash [8]uint8   — high 8 bits of hash       │
  │  keys    [8]keytype                              │
  │  values  [8]valuetype                            │
  │  overflow *bmap     — pointer to overflow bucket │
  └─────────────────────────────────────────────────┘

  Lookup process:
  key → hash(key) → low B bits = bucket index
                 → high 8 bits = tophash (fast compare)
                 → linear scan bucket for key match
```

### Map Operations

```go
// Creation
m := make(map[string]int)
m := map[string]int{"a": 1, "b": 2} // literal

// Set
m["key"] = 42

// Get — always returns zero value if key missing
val := m["key"]           // 0 if missing
val, ok := m["key"]       // ok=false if missing (idiomatic)

// Delete
delete(m, "key")          // safe even if key doesn't exist

// Check existence
if _, ok := m["key"]; ok {
    // key exists
}

// Iteration — RANDOM ORDER (not insertion order)
for k, v := range m {
    fmt.Println(k, v)
}

// Length
n := len(m)
```

### Map Gotchas

**1. Nil map — read is fine, write panics:**
```go
var m map[string]int
_ = m["key"]  // ok — returns zero value
m["key"] = 1  // PANIC: assignment to entry in nil map
```

**2. Map is not safe for concurrent access:**
```go
// WRONG — concurrent reads and writes are a data race
go func() { m["a"] = 1 }()
go func() { _ = m["a"] }()

// CORRECT: use sync.RWMutex or sync.Map
```

**3. You cannot take the address of a map value:**
```go
m := map[string]int{"a": 1}
// ptr := &m["a"] // compile error
// Reason: map may grow/rehash, invalidating the address
```

**4. Struct values in maps must be replaced entirely:**
```go
type Point struct{ X, Y int }
m := map[string]Point{"a": {1, 2}}
// m["a"].X = 10 // compile error: cannot assign to struct field in map
// Fix: copy, modify, replace:
p := m["a"]
p.X = 10
m["a"] = p
```

---

## 15. Pointers, Value vs Reference Semantics

### Stack vs Heap (Quick Preview)

```
  Stack (per goroutine, fast):       Heap (global, GC managed):
  ┌─────────────────────┐            ┌─────────────────────────┐
  │  local variables    │            │  objects allocated with  │
  │  function args      │            │  new(), &T{}, make()     │
  │  return values      │            │  or any var that escapes │
  │  fast alloc/dealloc │            │  GC tracks and frees     │
  └─────────────────────┘            └─────────────────────────┘
```

### Value Semantics — Copies

```go
type Point struct{ X, Y int }

func moveX(p Point, dx int) Point {
    p.X += dx  // modifies local copy
    return p   // caller gets new value
}

p1 := Point{1, 2}
p2 := moveX(p1, 5)
fmt.Println(p1) // {1, 2} — unchanged
fmt.Println(p2) // {6, 2}
```

### Pointer Semantics — Shared State

```go
func moveXPtr(p *Point, dx int) {
    p.X += dx  // modifies through pointer — affects caller's value
}

p := Point{1, 2}
moveXPtr(&p, 5)
fmt.Println(p) // {6, 2} — modified!
```

### When to Use Pointers

```
  Use pointer receivers/arguments when:
  ┌─────────────────────────────────────────────────────────┐
  │  1. Method mutates the receiver                         │
  │  2. Struct is large (avoid copying overhead)            │
  │  3. Consistency — if any method uses pointer, use all   │
  │  4. Need to represent "absence" (nil pointer)           │
  └─────────────────────────────────────────────────────────┘

  Use value receivers/arguments when:
  ┌─────────────────────────────────────────────────────────┐
  │  1. Type is small and naturally immutable (int, time)   │
  │  2. Type is a map, channel, slice (already reference)   │
  │  3. Implementing interfaces like fmt.Stringer           │
  └─────────────────────────────────────────────────────────┘
```

### new() vs make()

```go
// new(T) — allocates zero value of T, returns *T
p := new(int)     // *int pointing to 0
s := new([]int)   // *[]int pointing to nil slice (NOT useful)

// make(T, ...) — allocates and initializes reference types
// Only for: slice, map, channel
sl := make([]int, 5, 10)        // len=5, cap=10
m := make(map[string]int)       // initialized, ready to use
ch := make(chan int, 5)         // buffered channel
```

---

## 16. Structs — Methods, Embedding, Promotion

### Value vs Pointer Receivers — Consistency Rule

```go
type Counter struct {
    count int
}

// Pointer receiver — can mutate
func (c *Counter) Increment() {
    c.count++
}

// Value receiver — read-only copy
func (c Counter) Value() int {
    return c.count
}

// Interface satisfaction: if any method uses pointer receiver,
// only *Counter satisfies interfaces that require those methods.
var _ fmt.Stringer = (*Counter)(nil) // check at compile time
```

### Method Sets

```
  Type T:    method set = { value receiver methods }
  Type *T:   method set = { value AND pointer receiver methods }

  Consequence for interfaces:
  If interface requires a pointer receiver method → only *T satisfies it
  If interface requires only value receiver methods → both T and *T satisfy it
```

```go
type Stringer interface{ String() string }

type A struct{}
func (a A) String() string { return "A" }    // value receiver

type B struct{}
func (b *B) String() string { return "B" }  // pointer receiver

var _ Stringer = A{}  // OK
var _ Stringer = &A{} // OK
// var _ Stringer = B{} // ERROR: B does not implement Stringer
var _ Stringer = &B{} // OK
```

### Struct Tags

```go
type User struct {
    ID       int    `json:"id" db:"user_id" validate:"required"`
    Name     string `json:"name" db:"name" validate:"min=2,max=50"`
    Password string `json:"-"`                // excluded from JSON
    Email    string `json:"email,omitempty"`  // omit if empty
}

// Access tags via reflection:
t := reflect.TypeOf(User{})
field, _ := t.FieldByName("Name")
fmt.Println(field.Tag.Get("json")) // "name"
```

---

## 17. Generics (Go 1.18+)

### Why Generics?

Before generics, Go code was either:
1. Type-specific (duplicated code for each type).
2. Using `interface{}` / `any` (no compile-time type safety, requires type assertions).

Generics allow writing type-safe, reusable algorithms.

### Type Parameters

```go
// Generic function
func Min[T constraints.Ordered](a, b T) T {
    if a < b {
        return a
    }
    return b
}

Min(3, 5)           // int — inferred
Min(3.14, 2.71)     // float64 — inferred
Min("apple", "banana") // string — inferred
```

### Type Constraints

```go
import "golang.org/x/exp/constraints"

// Built-in constraints:
// constraints.Ordered = integer | float | string (anything with <, >, ==)
// constraints.Integer = all integer types
// constraints.Float = all float types

// Custom constraint:
type Number interface {
    ~int | ~int32 | ~int64 | ~float32 | ~float64
    // ~ means "any type whose underlying type is int" etc.
}

func Sum[T Number](nums []T) T {
    var total T
    for _, n := range nums {
        total += n
    }
    return total
}

fmt.Println(Sum([]int{1, 2, 3}))         // 6
fmt.Println(Sum([]float64{1.1, 2.2}))   // 3.3
```

### Generic Data Structures

```go
// Generic Stack
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(item T) {
    s.items = append(s.items, item)
}

func (s *Stack[T]) Pop() (T, bool) {
    var zero T
    if len(s.items) == 0 {
        return zero, false
    }
    n := len(s.items) - 1
    item := s.items[n]
    s.items = s.items[:n]
    return item, true
}

func (s *Stack[T]) Len() int {
    return len(s.items)
}

// Usage:
s := Stack[int]{}
s.Push(1)
s.Push(2)
v, _ := s.Pop() // 2
```

### Generic Map, Filter, Reduce

```go
func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

func Filter[T any](s []T, pred func(T) bool) []T {
    var result []T
    for _, v := range s {
        if pred(v) {
            result = append(result, v)
        }
    }
    return result
}

func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
    acc := init
    for _, v := range s {
        acc = f(acc, v)
    }
    return acc
}

// Usage:
nums := []int{1, 2, 3, 4, 5}
doubled := Map(nums, func(n int) int { return n * 2 })
evens := Filter(nums, func(n int) bool { return n%2 == 0 })
sum := Reduce(nums, 0, func(acc, n int) int { return acc + n })
```

### Type Inference

```go
// Go infers type parameters from arguments — no need to specify explicitly
Map(nums, func(n int) string { return fmt.Sprintf("%d", n) }) // inferred [int, string]
```

### Limitations of Go Generics

- Cannot use type parameters as map keys unless constrained with `comparable`.
- Cannot use parameterized methods (only functions and types).
- No operator overloading.
- Cannot specialize behavior per concrete type (no template specialization).

```go
// Must constrain to comparable for map keys
func Contains[T comparable](slice []T, item T) bool {
    for _, v := range slice {
        if v == item {
            return true
        }
    }
    return false
}
```

---

## 18. Reflection

Reflection allows inspecting and manipulating types and values at runtime.

### reflect.Type vs reflect.Value

```
  reflect package:
  
  reflect.TypeOf(x)   → reflect.Type  (describes the type)
  reflect.ValueOf(x)  → reflect.Value (describes the value)

  reflect.Type:
  ├── Kind()      → what kind of type (struct, ptr, int, slice, map, ...)
  ├── Name()      → type name
  ├── NumField()  → number of fields (for structs)
  └── Field(i)    → StructField descriptor

  reflect.Value:
  ├── Kind()      → same as Type.Kind()
  ├── Int()       → value as int64
  ├── String()    → value as string
  ├── Field(i)    → Value of i-th struct field
  ├── CanSet()    → can we modify this value?
  └── Set(v)      → set the value (must be addressable)
```

```go
import "reflect"

type Person struct {
    Name string `json:"name"`
    Age  int    `json:"age"`
}

func inspectStruct(v interface{}) {
    t := reflect.TypeOf(v)
    val := reflect.ValueOf(v)

    // If pointer, dereference
    if t.Kind() == reflect.Ptr {
        t = t.Elem()
        val = val.Elem()
    }

    fmt.Printf("Type: %s\n", t.Name())
    for i := 0; i < t.NumField(); i++ {
        field := t.Field(i)
        value := val.Field(i)
        tag := field.Tag.Get("json")
        fmt.Printf("  Field: %-10s Type: %-10s Value: %-10v Tag: %s\n",
            field.Name, field.Type, value.Interface(), tag)
    }
}

p := Person{Name: "Alice", Age: 30}
inspectStruct(&p)
```

### Modifying Values via Reflection

```go
func setField(obj interface{}, fieldName string, value interface{}) error {
    v := reflect.ValueOf(obj)
    if v.Kind() != reflect.Ptr || v.IsNil() {
        return fmt.Errorf("obj must be a non-nil pointer")
    }
    v = v.Elem()

    f := v.FieldByName(fieldName)
    if !f.IsValid() {
        return fmt.Errorf("field %q not found", fieldName)
    }
    if !f.CanSet() {
        return fmt.Errorf("field %q cannot be set (unexported?)", fieldName)
    }

    newVal := reflect.ValueOf(value)
    if f.Type() != newVal.Type() {
        return fmt.Errorf("type mismatch: %v vs %v", f.Type(), newVal.Type())
    }

    f.Set(newVal)
    return nil
}

p := Person{Name: "Bob", Age: 25}
setField(&p, "Name", "Alice")
fmt.Println(p.Name) // Alice
```

### When to Use Reflection

- Marshaling/unmarshaling (json, yaml, xml packages).
- Dependency injection frameworks.
- ORM libraries (mapping structs to DB tables).
- Testing utilities.

**When NOT to use reflection:**
- Performance-critical paths (reflection is 10–100x slower than direct access).
- Anywhere type safety can be achieved at compile time (use generics instead).

---

## 19. Memory Management & Garbage Collector

### Go's GC — Tricolor Mark-and-Sweep (Concurrent)

```
  Three phases:
  
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 1: MARK START (STW — stop-the-world, very brief)      │
  │  - Scan goroutine stacks, globals → mark roots as grey       │
  └──────────────────────────────────────────────────────────────┘
                              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 2: MARK (concurrent with program execution)           │
  │                                                              │
  │  Object states:                                              │
  │  ● White: not yet visited (initially all objects)            │
  │  ● Grey:  discovered but children not yet scanned            │
  │  ● Black: fully scanned, all children visited               │
  │                                                              │
  │  Algorithm:                                                  │
  │  1. Move roots from white to grey                           │
  │  2. Pick a grey object → scan its pointers                  │
  │  3. Move referenced white objects to grey                   │
  │  4. Move current object to black                            │
  │  5. Repeat until no grey objects remain                     │
  │                                                              │
  │  Write barrier: ensures new pointers during GC are tracked  │
  └──────────────────────────────────────────────────────────────┘
                              │
  ┌──────────────────────────────────────────────────────────────┐
  │  Phase 3: SWEEP (concurrent)                                 │
  │  - White objects remaining are unreachable → free their mem  │
  │  - Reclaim memory spans for reuse                            │
  └──────────────────────────────────────────────────────────────┘
```

### GOGC — GC Trigger

`GOGC` (default=100) means: trigger GC when heap size doubles from previous collection.

```
  GOGC=100:
  After GC, live heap = 100MB
  Next GC triggers when heap reaches 200MB (100MB * (1 + 100/100))

  GOGC=200: GC runs less often (less CPU, more memory)
  GOGC=50:  GC runs more often (more CPU, less memory)
  GOGC=off: disable GC (dangerous — only for benchmarks)

  Go 1.19+: GOMEMLIMIT — soft memory limit
  Sets target max heap; GC adjusts aggressively to stay under limit
```

### GC-Friendly Coding Practices

```go
// 1. Reuse allocations with sync.Pool
var bufPool = sync.Pool{
    New: func() interface{} {
        return new(bytes.Buffer)
    },
}

func processRequest(data []byte) string {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()
    buf.Write(data)
    return buf.String()
}

// 2. Pre-allocate slices
result := make([]int, 0, expectedSize)

// 3. Avoid allocating in hot loops
// BAD: allocates a new string each iteration
for _, item := range items {
    key := fmt.Sprintf("prefix_%s", item)
    // ...
}

// BETTER: build with strings.Builder
var sb strings.Builder
for _, item := range items {
    sb.Reset()
    sb.WriteString("prefix_")
    sb.WriteString(item)
    key := sb.String()
    // ...
}
```

---

## 20. Escape Analysis & Stack vs Heap

The compiler uses **escape analysis** to decide whether a variable lives on the stack or heap. Stack is faster (no GC pressure). Heap is needed when a variable's lifetime outlives the function.

### When Variables Escape to Heap

```
  Variable escapes to heap when:
  ┌────────────────────────────────────────────────────────────────┐
  │  1. Returned pointer: func f() *int { x := 1; return &x }     │
  │  2. Stored in interface: var i interface{} = myStruct{}        │
  │  3. Too large for stack                                        │
  │  4. Closure captures it: func() { _ = x } (captured by ref)   │
  │  5. Sent to channel: ch <- &x                                  │
  │  6. Dynamic size at runtime: make([]int, n) where n is unknown │
  └────────────────────────────────────────────────────────────────┘
```

### Inspecting Escape Analysis

```bash
go build -gcflags="-m" ./...
# Output example:
# ./main.go:10:12: &x escapes to heap
# ./main.go:15:14: inlining call to fmt.Sprintf
# ./main.go:20:6:  moved to heap: s
```

```go
// Does NOT escape — lives on stack
func noEscape() int {
    x := 42
    return x // value copy returned, x stays on stack
}

// ESCAPES to heap
func escapes() *int {
    x := 42
    return &x // address of x returned — x must live on heap
}

// Interface boxing causes escape
func boxing() {
    x := 42
    var i interface{} = x // x is boxed — copy goes to heap
}
```

---

## 21. HTTP Server Patterns

### Standard Library Server

```go
package main

import (
    "encoding/json"
    "log"
    "net/http"
    "time"
)

type Response struct {
    Message string    `json:"message"`
    Time    time.Time `json:"time"`
}

func helloHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodGet {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(Response{
        Message: "Hello, World!",
        Time:    time.Now(),
    })
}

func main() {
    mux := http.NewServeMux()
    mux.HandleFunc("/hello", helloHandler)

    server := &http.Server{
        Addr:         ":8080",
        Handler:      mux,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  120 * time.Second,
    }

    log.Printf("Starting server on :8080")
    if err := server.ListenAndServe(); err != nil {
        log.Fatal(err)
    }
}
```

### Middleware Pattern

```go
type Middleware func(http.Handler) http.Handler

func Chain(h http.Handler, middlewares ...Middleware) http.Handler {
    for i := len(middlewares) - 1; i >= 0; i-- {
        h = middlewares[i](h)
    }
    return h
}

func LoggingMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        // wrap ResponseWriter to capture status
        rw := &responseWriter{ResponseWriter: w, status: 200}
        next.ServeHTTP(rw, r)
        log.Printf("%s %s %d %v", r.Method, r.URL.Path, rw.status, time.Since(start))
    })
}

type responseWriter struct {
    http.ResponseWriter
    status int
}

func (rw *responseWriter) WriteHeader(status int) {
    rw.status = status
    rw.ResponseWriter.WriteHeader(status)
}

func RecoveryMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        defer func() {
            if err := recover(); err != nil {
                log.Printf("panic: %v\n%s", err, debug.Stack())
                http.Error(w, "Internal Server Error", 500)
            }
        }()
        next.ServeHTTP(w, r)
    })
}

// Wire up:
mux := http.NewServeMux()
mux.HandleFunc("/api/users", usersHandler)
handler := Chain(mux, LoggingMiddleware, RecoveryMiddleware)
http.ListenAndServe(":8080", handler)
```

### Graceful Shutdown

```go
func main() {
    server := &http.Server{Addr: ":8080", Handler: buildRoutes()}

    // Start server in goroutine
    go func() {
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            log.Fatalf("server error: %v", err)
        }
    }()

    // Wait for interrupt signal
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGINT, syscall.SIGTERM)
    <-quit

    log.Println("Shutting down server...")
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        log.Fatal("forced shutdown:", err)
    }
    log.Println("Server stopped")
}
```

---

## 22. Testing

### Table-Driven Tests

```go
func Add(a, b int) int { return a + b }

func TestAdd(t *testing.T) {
    tests := []struct {
        name     string
        a, b     int
        expected int
    }{
        {"positive", 1, 2, 3},
        {"negative", -1, -2, -3},
        {"zero", 0, 0, 0},
        {"mixed", -1, 1, 0},
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            result := Add(tc.a, tc.b)
            if result != tc.expected {
                t.Errorf("Add(%d, %d) = %d; want %d", tc.a, tc.b, result, tc.expected)
            }
        })
    }
}
```

### Subtests and Sub-benchmarks

```go
// Run only a specific subtest:
// go test -run TestAdd/positive

// Parallel subtests:
func TestParallel(t *testing.T) {
    tests := []struct{ name string }{{"a"}, {"b"}, {"c"}}
    for _, tc := range tests {
        tc := tc // capture
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel() // run this subtest in parallel
            // test code
        })
    }
}
```

### Benchmarks

```go
func BenchmarkAdd(b *testing.B) {
    for i := 0; i < b.N; i++ { // b.N is adjusted by the runner
        Add(1, 2)
    }
}

// With setup:
func BenchmarkSort(b *testing.B) {
    data := generateRandomSlice(10000)
    b.ResetTimer() // don't count setup time
    for i := 0; i < b.N; i++ {
        tmp := make([]int, len(data))
        copy(tmp, data)
        sort.Ints(tmp)
    }
}

// Run: go test -bench=. -benchmem -benchtime=5s
// Output:
// BenchmarkSort-8    1000    1234567 ns/op    81920 B/op    1 allocs/op
```

### Fuzz Testing (Go 1.18+)

```go
func FuzzParseDate(f *testing.F) {
    // Seed corpus
    f.Add("2024-01-15")
    f.Add("2024-12-31")
    f.Add("")

    f.Fuzz(func(t *testing.T, s string) {
        // Should never panic — test for robustness
        _, err := parseDate(s)
        if err == nil {
            // If no error, validate the result is sensible
        }
        // No panic = test passes
    })
}
// Run: go test -fuzz=FuzzParseDate -fuzztime=30s
```

### Testing with Mocks and Interfaces

```go
// Production code uses interface
type UserRepository interface {
    GetUser(ctx context.Context, id int) (*User, error)
    SaveUser(ctx context.Context, u *User) error
}

type UserService struct {
    repo UserRepository
}

func (s *UserService) GetUserName(ctx context.Context, id int) (string, error) {
    user, err := s.repo.GetUser(ctx, id)
    if err != nil {
        return "", fmt.Errorf("GetUserName: %w", err)
    }
    return user.Name, nil
}

// Test with mock
type MockUserRepo struct {
    users map[int]*User
    err   error
}

func (m *MockUserRepo) GetUser(_ context.Context, id int) (*User, error) {
    if m.err != nil {
        return nil, m.err
    }
    return m.users[id], nil
}

func (m *MockUserRepo) SaveUser(_ context.Context, u *User) error {
    return m.err
}

func TestGetUserName(t *testing.T) {
    mock := &MockUserRepo{
        users: map[int]*User{1: {Name: "Alice"}},
    }
    svc := &UserService{repo: mock}

    name, err := svc.GetUserName(context.Background(), 1)
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
    if name != "Alice" {
        t.Errorf("got %q, want %q", name, "Alice")
    }
}
```

### testify — Assertion Library

```go
import "github.com/stretchr/testify/assert"

func TestSomething(t *testing.T) {
    assert.Equal(t, expected, actual)
    assert.NoError(t, err)
    assert.Contains(t, slice, item)
    assert.Panics(t, func() { panic("!") })
}
```

---

## 23. Concurrency Patterns

### Worker Pool

```
  Dispatcher          Workers                    Results
  ──────────          ────────                   ───────
  
  jobs ──► ┌─────┐   ┌─────────┐  ┌─────────┐
           │ job │──►│ worker 1│──►│         │
           │ ch  │   └─────────┘  │ results │
           │     │   ┌─────────┐  │  chan   │
           │     │──►│ worker 2│──►│         │
           │     │   └─────────┘  └─────────┘
           │     │   ┌─────────┐
           │     │──►│ worker 3│──►
           └─────┘   └─────────┘
```

```go
func workerPool(numWorkers int, jobs <-chan int) <-chan int {
    results := make(chan int, numWorkers)
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                results <- process(job)
            }
        }()
    }

    // Close results when all workers done
    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}

func main() {
    jobs := make(chan int, 100)
    results := workerPool(5, jobs)

    // Send jobs
    go func() {
        for i := 0; i < 100; i++ {
            jobs <- i
        }
        close(jobs)
    }()

    // Collect results
    for r := range results {
        fmt.Println(r)
    }
}
```

### Rate Limiter (Token Bucket)

```go
// Using time.Ticker for basic rate limiting
func rateLimitedWorker(requests <-chan Request, ratePerSec int) {
    limiter := time.NewTicker(time.Second / time.Duration(ratePerSec))
    defer limiter.Stop()

    for req := range requests {
        <-limiter.C // wait for token
        go process(req)
    }
}

// Burst-capable rate limiter using channel as token bucket
func newTokenBucket(rate int, burst int) chan struct{} {
    tokens := make(chan struct{}, burst)

    // Fill up to burst capacity initially
    for i := 0; i < burst; i++ {
        tokens <- struct{}{}
    }

    // Refill at rate tokens/second
    go func() {
        ticker := time.NewTicker(time.Second / time.Duration(rate))
        defer ticker.Stop()
        for range ticker.C {
            select {
            case tokens <- struct{}{}:
            default: // bucket full
            }
        }
    }()

    return tokens
}
```

### Semaphore (Limit Concurrency)

```go
// Semaphore using buffered channel
type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(Semaphore, n)
}

func (s Semaphore) Acquire() { s <- struct{}{} }
func (s Semaphore) Release() { <-s }

func main() {
    sem := NewSemaphore(3) // max 3 concurrent operations
    var wg sync.WaitGroup

    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            sem.Acquire()
            defer sem.Release()
            // at most 3 goroutines here at once
            doWork(id)
        }(i)
    }
    wg.Wait()
}
```

### Pub/Sub (Event Bus)

```go
type EventBus struct {
    mu          sync.RWMutex
    subscribers map[string][]chan interface{}
}

func NewEventBus() *EventBus {
    return &EventBus{subscribers: make(map[string][]chan interface{})}
}

func (b *EventBus) Subscribe(topic string) <-chan interface{} {
    ch := make(chan interface{}, 10)
    b.mu.Lock()
    b.subscribers[topic] = append(b.subscribers[topic], ch)
    b.mu.Unlock()
    return ch
}

func (b *EventBus) Publish(topic string, event interface{}) {
    b.mu.RLock()
    subs := b.subscribers[topic]
    b.mu.RUnlock()

    for _, ch := range subs {
        select {
        case ch <- event:
        default: // drop if subscriber is slow
        }
    }
}
```

### Circuit Breaker Pattern

```
  States:
  
  CLOSED ────────── too many failures ──────────► OPEN
    ▲                                               │
    │                                     timeout  │
    │    success              ┌───────────────────► │
    │                         │                     │
    └── half-open success ◄── HALF-OPEN ◄───────────┘
                              (test request)
```

```go
type State int
const (
    StateClosed   State = iota // normal operation
    StateOpen                  // failing, reject all
    StateHalfOpen             // testing if recovered
)

type CircuitBreaker struct {
    mu           sync.Mutex
    state        State
    failures     int
    maxFailures  int
    resetTimeout time.Duration
    lastFailure  time.Time
}

func (cb *CircuitBreaker) Call(f func() error) error {
    cb.mu.Lock()
    switch cb.state {
    case StateOpen:
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = StateHalfOpen
        } else {
            cb.mu.Unlock()
            return fmt.Errorf("circuit open")
        }
    }
    cb.mu.Unlock()

    err := f()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures {
            cb.state = StateOpen
        }
        return err
    }

    cb.failures = 0
    cb.state = StateClosed
    return nil
}
```

---

## 24. Race Conditions & the Race Detector

### What Is a Data Race?

A data race occurs when two goroutines access the same memory location **concurrently**, and at least one access is a write, **without synchronization**.

```
  Goroutine A          Goroutine B        counter (memory)
      │                    │                  │
      │ read counter(=0)   │                  │ = 0
      │                    │ read counter(=0) │
      │ compute 0+1        │ compute 0+1      │
      │ write counter=1    │                  │ = 1
      │                    │ write counter=1  │ = 1 ← LOST UPDATE!
  
  Expected: counter = 2
  Actual:   counter = 1 (or any value — undefined behavior!)
```

### The Race Detector

```bash
go test -race ./...      # test with race detection
go run -race main.go     # run with race detection
go build -race -o app    # build with race detection (production testing only)
```

The race detector uses **ThreadSanitizer** (TSan) under the hood. It instruments memory accesses and reports races at runtime.

```
  DATA RACE output example:
  
  ==================
  WARNING: DATA RACE
  Write at 0x00c000012090 by goroutine 7:
    main.main.func1()
        /tmp/main.go:10 +0x30

  Previous read at 0x00c000012090 by goroutine 6:
    main.main.func2()
        /tmp/main.go:15 +0x28

  Goroutine 7 created at:
    main.main()
        /tmp/main.go:8 +0x58
  ==================
```

### Fixing Race Conditions

```go
// WRONG
var counter int
go func() { counter++ }()
go func() { counter++ }()

// FIX 1: Mutex
var mu sync.Mutex
var counter int
go func() { mu.Lock(); counter++; mu.Unlock() }()

// FIX 2: Atomic
var counter int64
go func() { atomic.AddInt64(&counter, 1) }()

// FIX 3: Channel (communicate, don't share)
ch := make(chan int, 1)
ch <- 0
go func() { ch <- <-ch + 1 }()
go func() { ch <- <-ch + 1 }()
```

---

## 25. Package Design & init()

### init() Function

`init()` is called **after all variable declarations** in the package are initialized, and **before `main()`**. A package can have multiple `init()` functions, even in the same file.

```
  Package initialization order:
  
  1. Import all packages (recursively)
  2. Initialize package-level variables (in order of declaration)
  3. Run init() functions (in order they appear in source)
  
  main.go imports:
    ├── package A
    │    ├── imports package B
    │    │    └── B's vars → B's init()
    │    └── A's vars → A's init()
    └── main's vars → main's init() → main.main()
```

```go
package mypackage

import "database/sql"

var db *sql.DB // package-level var

func init() {
    var err error
    db, err = sql.Open("postgres", "connection-string")
    if err != nil {
        panic(fmt.Sprintf("failed to init DB: %v", err))
    }
}

// Multiple init() in same package (all run):
func init() {
    registerMetrics()
}
```

**Use init() sparingly:**
- Hard to test (runs automatically on import).
- Hard to control execution order.
- Prefer explicit initialization functions.

### Side-Effect Imports

```go
// Import only for init() side effects (driver registration):
import _ "github.com/lib/pq"         // registers postgres driver
import _ "image/png"                  // registers PNG decoder
import _ "net/http/pprof"            // registers pprof HTTP handlers
```

### Package Organization Best Practices

```
  project/
  ├── cmd/
  │    └── myapp/
  │         └── main.go          ← thin, wires everything together
  ├── internal/
  │    ├── user/
  │    │    ├── user.go          ← domain types
  │    │    ├── repository.go    ← data access interface
  │    │    └── service.go       ← business logic
  │    └── database/
  │         └── postgres.go      ← infrastructure
  ├── pkg/                       ← public reusable packages
  │    └── validator/
  └── go.mod
  
  Rules:
  - internal/ — only importable from within the module
  - One package per directory
  - Package name = directory name (usually)
  - No circular imports (Go compiler enforces this)
```

---

## 26. Build Tags & Conditional Compilation

### Modern Build Tags (Go 1.17+)

```go
//go:build linux && amd64

package main

// This file only compiled on Linux/AMD64
```

**Tag expressions:**
```go
//go:build linux || darwin          // OR
//go:build !windows                 // NOT
//go:build linux && (amd64 || arm64) // complex
//go:build ignore                   // never compile
//go:build integration              // custom tag
```

### Running with Custom Tags

```bash
go test -tags integration ./...
go build -tags "linux production" ./...
```

### Platform-Specific Files

```
  os_linux.go      ← compiled only on Linux
  os_windows.go    ← compiled only on Windows
  os_darwin.go     ← compiled only on macOS
  os_linux_amd64.go ← compiled only on Linux/AMD64
```

```go
// file: platform_unix.go
//go:build linux || darwin || freebsd

package main

func getPlatformName() string { return "unix-like" }

// file: platform_windows.go
//go:build windows

package main

func getPlatformName() string { return "windows" }
```

### go:generate

```go
//go:generate stringer -type=Weekday
//go:generate mockgen -source=interfaces.go -destination=mocks/mocks.go

type Weekday int
const (
    Sunday Weekday = iota
    Monday
    // ...
)

// Run: go generate ./...
```

---

## 27. Common Pitfalls & Gotchas

### 1. Goroutine Closure Capture

```go
// BUG: all goroutines see the same (final) value of i
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i) // prints 5,5,5,5,5 (or some variation)
    }()
}

// FIX: pass as argument
for i := 0; i < 5; i++ {
    go func(n int) {
        fmt.Println(n) // correct: 0,1,2,3,4
    }(i)
}
```

### 2. Slice Sharing After Append

```go
a := []int{1, 2, 3}
b := a[:2]          // shares array with a
b = append(b, 99)   // may overwrite a[2]!
fmt.Println(a)      // [1, 2, 99] — a was modified!

// FIX: use three-index slice to prevent sharing
b := a[:2:2]        // cap=2; append always allocates new array
b = append(b, 99)
fmt.Println(a)      // [1, 2, 3] — a unchanged
```

### 3. Defer in a Loop

```go
// BUG: files are opened but not closed until function returns
for _, path := range paths {
    f, _ := os.Open(path)
    defer f.Close() // defer stacks up — all close at function end!
    process(f)
}

// FIX: wrap in a function
for _, path := range paths {
    func() {
        f, _ := os.Open(path)
        defer f.Close() // runs when inner function returns
        process(f)
    }()
}
```

### 4. Interface Method Sets & Pointer Receivers

```go
type Doer interface{ Do() }
type MyType struct{}
func (m *MyType) Do() {} // pointer receiver

var d Doer = MyType{}    // COMPILE ERROR: MyType doesn't implement Doer
var d Doer = &MyType{}   // OK: *MyType implements Doer
```

### 5. Range Loop Value Copies

```go
type Item struct{ value int }
items := []Item{{1}, {2}, {3}}

// BUG: v is a copy
for _, v := range items {
    v.value *= 2 // modifies copy, not original
}
fmt.Println(items) // [{1} {2} {3}] — unchanged!

// FIX 1: use index
for i := range items {
    items[i].value *= 2
}

// FIX 2: slice of pointers
pItems := []*Item{{1}, {2}, {3}}
for _, v := range pItems {
    v.value *= 2 // v is pointer — modifies original
}
```

### 6. Map Iteration Order

```go
m := map[string]int{"b": 2, "a": 1, "c": 3}
for k, v := range m {
    fmt.Println(k, v) // order is RANDOM each run
}
// Go intentionally randomizes map iteration order since 1.0
// To sort: extract keys → sort → iterate
```

### 7. Sending to a Closed Channel

```go
ch := make(chan int)
close(ch)
ch <- 1 // PANIC: send on closed channel
```

### 8. String vs []byte Conversions

```go
s := "hello"
b := []byte(s)  // COPY — modifying b doesn't affect s

// For zero-copy (unsafe, advanced):
import "unsafe"
b := unsafe.Slice(unsafe.StringData(s), len(s)) // Go 1.20+
// WARNING: b and s share memory — don't modify b while s is in use
```

### 9. Integer Overflow

```go
var x int8 = 127
x++ // x becomes -128 (overflow — no panic in Go)
fmt.Println(x) // -128
```

### 10. Goroutine Panic Crashes the Whole Program

```go
go func() {
    panic("boom") // crashes entire program, not just this goroutine
}()

// Always recover in goroutines:
go func() {
    defer func() {
        if r := recover(); r != nil {
            log.Println("recovered:", r)
        }
    }()
    panic("boom")
}()
```

### 11. time.After Leak in select

```go
// BUG: time.After creates a new timer every iteration; old timers leak
for {
    select {
    case v := <-ch:
        process(v)
    case <-time.After(5 * time.Second): // new timer every loop!
        fmt.Println("timeout")
        return
    }
}

// FIX: create timer once outside loop
timer := time.NewTimer(5 * time.Second)
defer timer.Stop()
for {
    timer.Reset(5 * time.Second) // reuse
    select {
    case v := <-ch:
        process(v)
    case <-timer.C:
        fmt.Println("timeout")
        return
    }
}
```

### 12. Struct Comparison

```go
// Structs are comparable only if all fields are comparable
type Point struct{ X, Y int }
p1, p2 := Point{1, 2}, Point{1, 2}
fmt.Println(p1 == p2) // true

// Struct with map — NOT comparable
type Bad struct{ Data map[string]int }
// b1 == b2 // COMPILE ERROR: invalid operation: cannot compare

// Use reflect.DeepEqual for deep comparison:
reflect.DeepEqual(b1, b2)
```

---

## Quick Reference: Mental Model Checklist

```
  When writing Go, ask yourself:

  CONCURRENCY:
  □ Do I need synchronization? (shared mutable state → mutex/atomic/channel)
  □ Am I using channels correctly? (right direction, buffering, closing)
  □ Could this goroutine leak? (always provide exit path)
  □ Am I checking ctx.Done() in long-running operations?

  MEMORY:
  □ Does this variable escape? (pointer returned, captured by closure, interface)
  □ Can I reuse allocations? (sync.Pool for frequent allocs)
  □ Am I pre-allocating slices/maps when size is known?

  ERRORS:
  □ Am I wrapping errors with context using %w?
  □ Am I using errors.Is/As instead of == for wrapped errors?
  □ Do my sentinel errors live at package scope?

  INTERFACES:
  □ Could this interface hold a typed nil? (return concrete nil, not typed nil)
  □ Does my interface require pointer receivers? (only *T satisfies it then)
  □ Am I defining interfaces at the consumer, not the producer?

  TESTING:
  □ Are my tests table-driven?
  □ Am I injecting dependencies via interfaces (for mocking)?
  □ Have I run go test -race?
  □ Do I have benchmarks for performance-critical code?

  GENERAL:
  □ Am I closing channels from the sender only?
  □ Am I using defer for cleanup (unlock, close, cancel)?
  □ Have I handled the two-value map/channel read?
  □ Am I passing loop variables correctly into goroutines/closures?
```

---

*This guide covers the core intermediate Go concepts expected in technical interviews and real production systems. Master these, and you'll think in Go naturally.*

I'll build this comprehensive guide now — it'll be a large, in-depth markdown file covering every intermediate Go concept with ASCII diagrams and real implementations.Here's your complete guide — **27 topics**, fully in-depth. Here's what it covers and why each builds your mental model:

**Runtime & Concurrency Foundation (§1–6)**
GMP scheduler, goroutine lifecycle, every channel behavior (with `hchan` internals), `select` algorithm, all `sync` primitives, and lock-free atomics. Understanding *why* the runtime works this way lets you reason about scheduling, blocking, and performance without guessing.

**Coordination & Safety (§7–8)**
`context` propagation tree with cancellation semantics, and the Go Memory Model's happens-before rules — the formal basis for knowing when concurrent code is actually safe.

**Type System Depth (§9–10)**
Interface internals (`iface`/`eface` two-word layout), the typed-nil gotcha (one of Go's most famous bugs), embedding vs inheritance distinction, and complete error handling — wrapping, unwrapping, `errors.Is`/`As`, `errors.Join`.

**Language Mechanics (§11–16)**
Defer LIFO semantics, named return modification, panic/recover across goroutine boundaries, closure capture rules, and deep slice/map internals (circular buffer, bucket layout, growth strategy).

**Advanced Features (§17–20)**
Generics with type constraints and `~` underlying types, reflection internals, the tricolor GC algorithm, and escape analysis (with `gcflags=-m` diagnostics).

**Practical Patterns (§21–25)**
HTTP server with middleware chaining, graceful shutdown, table-driven tests, fuzz testing, worker pools, circuit breaker, semaphore, pub/sub, and the race detector.

**The closing checklist** gives you a systematic way to audit any Go code you write in an interview or at work.