# Go Concurrency: Elite Production Guide

> **Audience**: Engineers who want to go beyond tutorials and write production-grade concurrent Go.  
> **Philosophy**: Every concept is explained from the runtime up — not "what to type" but "why this is the only correct way to think about it."

---

## Table of Contents

1. [The Go Runtime Scheduler — Foundation Everything Else Sits On](#1-the-go-runtime-scheduler)
2. [Goroutines — What They Actually Are](#2-goroutines)
3. [Stack Growth and the Cost of a Goroutine](#3-stack-growth)
4. [Channels — The Only Correct Mental Model](#4-channels)
5. [Buffered vs Unbuffered Channels](#5-buffered-vs-unbuffered)
6. [Channel Directions and Ownership Rules](#6-channel-directions-and-ownership)
7. [Select — Multiplexing Channels](#7-select)
8. [Signals — OS Signals and Done Signals](#8-signals)
9. [Counters — Atomic vs Mutex](#9-counters)
10. [sync.WaitGroup — Structured Goroutine Lifetime](#10-waitgroup)
11. [sync.Mutex and sync.RWMutex](#11-mutex-and-rwmutex)
12. [sync.Once — Safe One-Time Initialization](#12-synconce)
13. [sync.Pool — Reusing Allocations](#13-syncpool)
14. [sync.Map — Concurrent Map](#14-syncmap)
15. [Context — Cancellation and Deadlines](#15-context)
16. [Pipeline Pattern](#16-pipeline-pattern)
17. [Fan-Out / Fan-In](#17-fan-out-fan-in)
18. [Worker Pool — The Most Reused Pattern](#18-worker-pool)
19. [Semaphore — Bounded Concurrency](#19-semaphore)
20. [Rate Limiting](#20-rate-limiting)
21. [Backpressure](#21-backpressure)
22. [errgroup — Concurrent Error Handling](#22-errgroup)
23. [Goroutine Leak Detection and Prevention](#23-goroutine-leaks)
24. [The Go Memory Model — Happens-Before](#24-go-memory-model)
25. [Data Race Detection](#25-data-race-detection)
26. [Profiling Concurrent Programs](#26-profiling)
27. [Production Patterns and Anti-Patterns](#27-production-patterns)
28. [Complete Production Example: HTTP Worker Service](#28-complete-example)

---

## 1. The Go Runtime Scheduler

### What It Is

The Go scheduler is an **M:N scheduler** — it maps M goroutines onto N OS threads. You don't control OS threads directly. The scheduler does.

### Three Entities: G, M, P

```
  G  = Goroutine  (the unit of work)
  M  = Machine    (OS thread, executes Go code)
  P  = Processor  (logical CPU, holds the run queue)

  GOMAXPROCS controls how many P's exist.
  Default = number of CPU cores.
```

### How They Connect

```
┌─────────────────────────────────────────────────────┐
│                   Go Runtime                        │
│                                                     │
│  P0 ──── M0 ──── G_running                          │
│  │                                                  │
│  └── LocalRunQueue: [G1, G2, G3, ...]               │
│                                                     │
│  P1 ──── M1 ──── G_running                          │
│  │                                                  │
│  └── LocalRunQueue: [G4, G5, ...]                   │
│                                                     │
│  GlobalRunQueue: [G6, G7, G8, ...]  (overflow)      │
│                                                     │
│  NetworkPoller: [G_waiting_on_io, ...]              │
└─────────────────────────────────────────────────────┘
```

### Scheduler Preemption Points

Before Go 1.14, goroutines were cooperatively scheduled — they had to call functions to yield. Since Go 1.14, **signal-based preemption** exists: the runtime sends `SIGURG` to threads to force goroutines to yield at safe points.

This means: **a tight CPU loop no longer starves other goroutines** on the same P.

```go
// Pre-1.14: this could starve goroutines on the same P
// Post-1.14: runtime forces preemption via SIGURG
func tightLoop() {
    for {
        // signal-based preemption fires here
    }
}
```

### Work Stealing

When a P's local queue is empty, it steals half the work from another P's queue. This is why goroutine counts in the hundreds of thousands are normal and cheap.

```
  P0 (empty) ──steal──► P1 (has 8 goroutines)
                         P1 now has 4, P0 now has 4
```

---

## 2. Goroutines

### What a Goroutine Actually Is

A goroutine is a **lightweight thread managed entirely by the Go runtime**. It is NOT an OS thread. It's a structure (`runtime.g`) in the heap that contains:

- A stack (starts at 2KB, grows dynamically)
- A program counter (where it's executing)
- A goroutine ID
- Status (running, runnable, waiting, dead)

```
runtime.g struct (simplified):
┌────────────────────────────────┐
│  stack.lo  (stack low address) │
│  stack.hi  (stack high address)│
│  stackguard0                   │
│  sched (gobuf)                 │
│    ├── sp  (stack pointer)     │
│    ├── pc  (program counter)   │
│    └── bp  (base pointer)      │
│  atomicstatus                  │
│  goid                          │
│  m  *runtime.m (current thread)│
└────────────────────────────────┘
```

### Goroutine Lifecycle

```
           go func()
               │
               ▼
         [_Grunnable]  ─── placed on P's run queue
               │
         P picks it up
               │
               ▼
         [_Grunning]   ─── executing on M
               │
    ┌──────────┴──────────┐
    │                     │
  syscall/IO            preempted
    │                     │
    ▼                     ▼
[_Gwaiting]         [_Grunnable]
    │
  IO completes
    │
    ▼
[_Grunnable]
    │
  returns from func
    │
    ▼
  [_Gdead]   ─── goroutine struct put in free list
```

### Production Goroutine Rules

```
Rule 1: Never start a goroutine without knowing how it will stop.
Rule 2: Never start a goroutine without knowing who owns it.
Rule 3: The goroutine that creates a WaitGroup is responsible for Wait()ing.
Rule 4: A channel send always happens-before the corresponding receive completes.
```

### Minimal Runnable Example

```go
// file: goroutine_basics.go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done() // ALWAYS use defer. Ensures Done() even on panic.
    fmt.Printf("worker %d: starting\n", id)
    time.Sleep(10 * time.Millisecond) // simulate real work
    fmt.Printf("worker %d: done\n", id)
}

func main() {
    var wg sync.WaitGroup

    for i := 0; i < 5; i++ {
        wg.Add(1)       // increment BEFORE starting goroutine
        go worker(i, &wg)
    }

    wg.Wait()
    fmt.Println("all workers done")
}
```

```
go run goroutine_basics.go
```

### Common Goroutine Pitfalls

```
PITFALL 1: Loop variable capture (Go < 1.22)

    for i := 0; i < 5; i++ {
        go func() {
            fmt.Println(i) // BUG: all goroutines may print 5
        }()
    }

    FIX:
    for i := 0; i < 5; i++ {
        i := i // shadow with local copy
        go func() {
            fmt.Println(i) // OK
        }()
    }

    NOTE: Go 1.22+ changed loop variable semantics. Each iteration gets
    its own variable. But if you support < 1.22, always shadow.

PITFALL 2: Forgetting wg.Add() before go func()

    wg.Add(1) // MUST be here, not inside the goroutine
    go func() {
        defer wg.Done()
        // ...
    }()

PITFALL 3: Goroutine leak — started but never stopped
    See Section 23 for full treatment.
```

---

## 3. Stack Growth

### The Segmented/Copying Stack

Goroutines start with a **2KB stack**. When the stack is about to overflow (checked by `stackguard0`), the runtime:

1. Allocates a **new, larger stack** (2x)
2. **Copies all frames** to the new stack
3. Updates all pointers that pointed into the old stack
4. Frees the old stack

This is why you can have 100,000 goroutines with very little memory if they don't use much stack.

```
Initial goroutine:
┌──────────────┐
│  2 KB stack  │
└──────────────┘

After stack growth:
┌──────────────────────────────┐
│         4 KB stack           │
│  (old frames copied here)    │
└──────────────────────────────┘
```

### What "Hot Split" Means

A hot split is when a function is called repeatedly near the stack boundary, causing repeated grow-copy-shrink cycles. This is a real performance problem.

```go
// This is the pattern that causes hot splits (simplified):
// A function near the stack limit that calls another function repeatedly
// results in grow → copy → call → return → shrink → grow → ...

// Mitigation: use GOGC tuning, or restructure call depth
```

### Checking Stack Usage

```bash
# See goroutine stacks in a running program
go tool pprof -alloc_space http://localhost:6060/debug/pprof/goroutine
```

---

## 4. Channels

### The Only Correct Mental Model

A channel is a **typed, concurrent queue with optional capacity, built with synchronization primitives inside the runtime**.

It is NOT just a pipe. It is a communication mechanism that **transfers ownership** of data from one goroutine to another.

> "Do not communicate by sharing memory; share memory by communicating."

This is a deep statement: instead of two goroutines accessing a shared variable under a mutex (sharing memory), you **send a value through a channel** — the sender gives up ownership, the receiver takes ownership. No lock needed at the application level.

### What a Channel Is Internally

```
runtime.hchan struct (simplified):
┌──────────────────────────────────────────┐
│  qcount   uint   (items currently in buf)│
│  dataqsiz uint   (capacity of buffer)    │
│  buf      unsafe.Pointer (circular buf)  │
│  elemsize uint16 (size of one element)   │
│  closed   uint32                         │
│  sendx    uint   (send index)            │
│  recvx    uint   (receive index)         │
│  recvq    waitq  (blocked receivers)     │
│  sendq    waitq  (blocked senders)       │
│  lock     mutex                          │
└──────────────────────────────────────────┘
```

### Channel States and What Each Operation Does

```
State: nil channel
  send:    blocks forever
  receive: blocks forever
  close:   panic

State: open, empty, unbuffered
  send:    blocks until receiver is ready
  receive: blocks until sender is ready

State: open, empty, buffered
  send:    succeeds (places in buffer)
  receive: blocks until an item is sent

State: open, full, buffered
  send:    blocks until space is available
  receive: succeeds (takes from buffer)

State: closed
  send:    panic
  receive: returns (zero value, false) — never blocks
  close:   panic (double close)
```

### The Send Path (Unbuffered, No Waiting Receiver)

```
goroutine G1 sends on channel C:

1. G1 acquires C.lock
2. Checks recvq (waiting receivers) — empty
3. G1 creates a sudog (send descriptor) with its value
4. Appends sudog to C.sendq
5. G1 calls gopark() → status becomes _Gwaiting
6. C.lock released

goroutine G2 receives on channel C:
1. G2 acquires C.lock
2. Finds G1's sudog in C.sendq
3. Copies value directly from G1's stack to G2's stack (zero-copy)
4. Calls goready(G1) → G1 status becomes _Grunnable
5. C.lock released
6. G2 continues with the value
```

---

## 5. Buffered vs Unbuffered Channels

### Unbuffered: Synchronous Rendezvous

```
Unbuffered channel: both goroutines must be ready simultaneously.

  G1 (sender) ─────────────────────────────► G2 (receiver)
               "I wait for you to be ready"   "I wait for you to be ready"

  This is a synchronization point. Use it when you want to ensure
  the receiver has received before the sender continues.
```

### Buffered: Asynchronous Decoupling

```
Buffered channel cap=3:

  G1 ──send──► [A][B][C]  ──receive──► G2
                buffer

  G1 can send up to 3 items without G2 being ready.
  G1 blocks only when buffer is full.
  G2 blocks only when buffer is empty.

  Buffered channels decouple sender and receiver speed.
  But they hide backpressure. Use carefully.
```

### Code: Both Variants

```go
// file: channels_comparison.go
package main

import (
    "fmt"
    "time"
)

// unbuffered: tight synchronization
func unbufferedDemo() {
    ch := make(chan int) // no second arg = unbuffered

    go func() {
        fmt.Println("sender: about to send")
        ch <- 42 // blocks until receiver is ready
        fmt.Println("sender: sent and receiver has it")
    }()

    time.Sleep(50 * time.Millisecond) // simulate receiver being slow
    val := <-ch
    fmt.Printf("receiver: got %d\n", val)
}

// buffered: decoupled producer/consumer
func bufferedDemo() {
    ch := make(chan int, 3)

    // producer can run ahead of consumer
    go func() {
        for i := 0; i < 3; i++ {
            ch <- i
            fmt.Printf("sent %d\n", i)
        }
        close(ch) // signal: no more values
    }()

    time.Sleep(100 * time.Millisecond) // consumer is late

    for v := range ch { // range drains until channel closed
        fmt.Printf("received %d\n", v)
    }
}

func main() {
    fmt.Println("=== unbuffered ===")
    unbufferedDemo()
    fmt.Println("=== buffered ===")
    bufferedDemo()
}
```

### Closing Channels — The Rules

```
Rule 1: Only the SENDER closes a channel. NEVER the receiver.
        (Receiver doesn't know if there are more senders.)

Rule 2: Never close a channel twice. (panic)

Rule 3: Closing is a BROADCAST to all receivers.
        All blocked/future receivers get (zero, false) immediately.

Rule 4: Use a separate done channel or sync.Once to close safely
        when you have multiple senders.

// Check if channel is closed without blocking:
val, ok := <-ch
if !ok {
    // channel closed and drained
}
```

---

## 6. Channel Directions and Ownership

### Directional Channel Types

```go
chan T      // bidirectional (only use in struct fields or make())
chan<- T    // send-only    (give to producers)
<-chan T    // receive-only (give to consumers)
```

This is a **compile-time ownership contract**. If a function takes `chan<- T`, it cannot receive. If it takes `<-chan T`, it cannot send. This eliminates a whole class of bugs.

```go
// file: channel_ownership.go
package main

import "fmt"

// produce owns the channel: creates it, sends, closes it
// Returns receive-only so consumers can't close/send accidentally
func produce(nums []int) <-chan int {
    out := make(chan int, len(nums))
    go func() {
        defer close(out) // producer closes when done
        for _, n := range nums {
            out <- n
        }
    }()
    return out // caller gets read-only handle
}

// consume takes receive-only: can only read
func consume(in <-chan int) {
    for v := range in {
        fmt.Println("processing:", v)
    }
}

func main() {
    ch := produce([]int{1, 2, 3, 4, 5})
    consume(ch)
}
```

### Ownership Rule (Production Standard)

```
The goroutine that creates a channel OWNS it.
Owner responsibilities:
  1. Initialize the channel (make())
  2. Write to it (or coordinate writers)
  3. Close it (or coordinate close)
  4. Pass receive-only references to consumers
  5. Pass send-only references to sub-producers

Consumers (non-owners) must:
  1. Never close the channel
  2. Handle closure gracefully (range, or ok idiom)
```

---

## 7. Select

### What Select Does

`select` blocks until one of its cases can proceed. It's the channel equivalent of `epoll`/`kqueue` — it efficiently waits on multiple I/O events simultaneously.

```go
select {
case v := <-ch1:     // fires if ch1 has a value
    use(v)
case ch2 <- v:       // fires if ch2 can accept a send
    // sent
case <-time.After(1 * time.Second): // timeout
    // timed out
default:             // fires immediately if no case is ready (non-blocking)
    // nothing ready
}
```

### Internals of Select

```
1. All channel operations are evaluated (not short-circuit).
2. If multiple cases are ready, one is chosen UNIFORMLY AT RANDOM.
   (This is intentional. No case should starve another.)
3. If no case is ready and no default: goroutine parks.
4. If default is present and no case is ready: default runs.
```

### Production Patterns with Select

```go
// file: select_patterns.go
package main

import (
    "context"
    "fmt"
    "time"
)

// Pattern 1: Context cancellation + work
func workerWithContext(ctx context.Context, work <-chan string) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("worker: context cancelled:", ctx.Err())
            return
        case item, ok := <-work:
            if !ok {
                fmt.Println("worker: channel closed")
                return
            }
            fmt.Println("processing:", item)
        }
    }
}

// Pattern 2: Timeout on individual operation
func fetchWithTimeout(ch <-chan string, timeout time.Duration) (string, error) {
    select {
    case val := <-ch:
        return val, nil
    case <-time.After(timeout):
        return "", fmt.Errorf("timeout after %s", timeout)
    }
}

// Pattern 3: Non-blocking send (drop if full — backpressure escape valve)
func trySend(ch chan<- int, val int) bool {
    select {
    case ch <- val:
        return true
    default:
        return false // channel full, drop
    }
}

// Pattern 4: Non-blocking receive (check without blocking)
func tryReceive(ch <-chan int) (int, bool) {
    select {
    case v := <-ch:
        return v, true
    default:
        return 0, false
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
    defer cancel()

    work := make(chan string, 5)
    work <- "task-1"
    work <- "task-2"

    go workerWithContext(ctx, work)
    time.Sleep(300 * time.Millisecond)
}
```

### The "for-select" Loop — The Most Common Pattern

```go
// This is the canonical goroutine loop:
func runLoop(ctx context.Context, in <-chan Job) {
    for {
        select {
        case <-ctx.Done():
            // clean up and exit
            return
        case job, ok := <-in:
            if !ok {
                return // channel closed
            }
            process(job)
        }
    }
}
```

---

## 8. Signals

There are two distinct concepts both called "signal" in Go:

### 8a. OS Signals (SIGTERM, SIGINT, etc.)

The OS sends signals to processes. In production services, you **must** handle:

- `SIGTERM` — Kubernetes sends this before killing your pod. You have 30s by default to shut down cleanly.
- `SIGINT` — Ctrl+C in terminal.
- `SIGHUP` — Reload configuration (sometimes used).

```go
// file: os_signal_handling.go
package main

import (
    "context"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"
)

func main() {
    // Create a channel to receive OS signals
    // IMPORTANT: buffer of 1. If signal fires before we're in select,
    // it's not dropped. Unbuffered here is a bug.
    sigCh := make(chan os.Signal, 1)

    // Register which signals we care about
    signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
    defer signal.Stop(sigCh) // cleanup: stop delivering to sigCh on return

    // Your real server
    server := &http.Server{
        Addr:    ":8080",
        Handler: http.DefaultServeMux,
    }

    // Start server in background
    go func() {
        if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            fmt.Println("server error:", err)
            os.Exit(1)
        }
    }()

    fmt.Println("server running. send SIGTERM or SIGINT to stop.")

    // Block until we receive a signal
    sig := <-sigCh
    fmt.Println("received signal:", sig)

    // Graceful shutdown: give in-flight requests time to complete
    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := server.Shutdown(ctx); err != nil {
        fmt.Println("shutdown error:", err)
    }

    fmt.Println("shutdown complete")
}
```

### 8b. Done Channels (Internal Signal Pattern)

A "done channel" is a Go idiom: a `chan struct{}` that is **closed** (not sent on) to signal all listeners simultaneously.

```go
// Sending on done channel = wrong, only reaches ONE receiver
done <- struct{}{} // bad: only one goroutine gets this

// Closing done channel = broadcast to ALL receivers
close(done) // good: ALL goroutines blocked on <-done unblock immediately
```

```go
// file: done_channel_pattern.go
package main

import (
    "fmt"
    "sync"
    "time"
)

func startWorkers(done <-chan struct{}, n int) *sync.WaitGroup {
    var wg sync.WaitGroup
    for i := 0; i < n; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            for {
                select {
                case <-done:
                    fmt.Printf("worker %d: shutting down\n", id)
                    return
                default:
                    // do work
                    time.Sleep(50 * time.Millisecond)
                    fmt.Printf("worker %d: tick\n", id)
                }
            }
        }(i)
    }
    return &wg
}

func main() {
    done := make(chan struct{})

    wg := startWorkers(done, 3)

    time.Sleep(200 * time.Millisecond)

    fmt.Println("stopping all workers")
    close(done) // BROADCAST: all workers unblock from <-done simultaneously

    wg.Wait()
    fmt.Println("all workers stopped")
}
```

---

## 9. Counters

### 9a. sync/atomic — Lock-Free Counters

`sync/atomic` provides hardware-level atomic operations (CAS, ADD, LOAD, STORE). These are implemented as CPU instructions (`LOCK XADD`, `CMPXCHG`) — no OS-level locking.

```
CPU Instruction Level:
  LOCK XADDQ — atomically adds to a 64-bit integer
  No mutex needed. Cheaper than mutex for simple counters.
```

```go
// file: atomic_counter.go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// Counter wraps an int64. MUST be 64-bit aligned.
// Use int64 not int (int is 32-bit on 32-bit platforms).
type Counter struct {
    val int64
}

func (c *Counter) Inc()           { atomic.AddInt64(&c.val, 1) }
func (c *Counter) Dec()           { atomic.AddInt64(&c.val, -1) }
func (c *Counter) Load() int64    { return atomic.LoadInt64(&c.val) }
func (c *Counter) Store(v int64)  { atomic.StoreInt64(&c.val, v) }

// CAS (Compare-And-Swap): atomically set to new only if currently old
// Returns true if swap happened.
func (c *Counter) CompareAndSwap(old, new int64) bool {
    return atomic.CompareAndSwapInt64(&c.val, old, new)
}

func main() {
    var c Counter
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Inc()
        }()
    }

    wg.Wait()
    fmt.Println("final count:", c.Load()) // always 1000, no race
}
```

### 9b. The atomic.Value Type — Atomic Reads/Writes of Any Type

```go
// file: atomic_value.go
package main

import (
    "fmt"
    "sync/atomic"
)

type Config struct {
    MaxConn int
    Timeout int
}

func main() {
    var cfg atomic.Value

    // store: must always store the SAME concrete type
    cfg.Store(Config{MaxConn: 100, Timeout: 30})

    // load: returns interface{}, type assert needed
    current := cfg.Load().(Config)
    fmt.Println("current config:", current)

    // hot-reload config without stopping service
    cfg.Store(Config{MaxConn: 200, Timeout: 60})
    updated := cfg.Load().(Config)
    fmt.Println("updated config:", updated)
}
```

### 9c. Mutex-Based Counter (When You Need More Complex State)

```go
// file: mutex_counter.go
package main

import (
    "fmt"
    "sync"
)

type SafeMap struct {
    mu sync.RWMutex
    m  map[string]int
}

func NewSafeMap() *SafeMap {
    return &SafeMap{m: make(map[string]int)}
}

func (s *SafeMap) Inc(key string) {
    s.mu.Lock()         // exclusive write lock
    defer s.mu.Unlock()
    s.m[key]++
}

func (s *SafeMap) Get(key string) int {
    s.mu.RLock()         // shared read lock — multiple readers OK simultaneously
    defer s.mu.RUnlock()
    return s.m[key]
}

func main() {
    sm := NewSafeMap()
    var wg sync.WaitGroup

    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            key := fmt.Sprintf("key-%d", i%10)
            sm.Inc(key)
        }(i)
    }

    wg.Wait()
    fmt.Println("key-0 count:", sm.Get("key-0"))
}
```

### When to Use Atomic vs Mutex

```
Use atomic when:
  - Simple numeric operations (Inc, Dec, Load, Store, CAS)
  - Hot path where mutex contention is measured to be a problem
  - Read-heavy, write-rare scenarios with atomic.Value

Use Mutex when:
  - Protecting complex data structures (maps, slices, structs)
  - Multiple operations must be atomic together
  - Conditional logic around the protected state

Performance:
  atomic.AddInt64: ~5ns
  sync.Mutex Lock/Unlock: ~25ns (uncontended)
  sync.Mutex Lock/Unlock: 100-1000ns (contended, depends on goroutines)
```

---

## 10. WaitGroup

### What It Is

`sync.WaitGroup` is a **concurrent counter** with a blocking wait. It answers: "wait until N goroutines finish."

```
Internal state: 64-bit counter split into:
  - high 32 bits: waiter count (goroutines calling Wait())
  - low 32 bits:  work count   (Add/Done balance)
  - 32-bit semaphore for waking waiters
```

### Rules That Prevent Bugs

```
Rule 1: wg.Add(n) BEFORE go func() — never inside.
        If Add is inside the goroutine, Wait() might return before
        the goroutine even calls Add.

Rule 2: One Add() per goroutine is clearest.
        wg.Add(1) immediately before each go statement.

Rule 3: ALWAYS use defer wg.Done() — ensures Done even on panic.

Rule 4: Don't copy WaitGroup. Always pass as pointer.
        func worker(wg *sync.WaitGroup) { ... }   // correct
        func worker(wg sync.WaitGroup) { ... }    // WRONG: copies
```

### Production Pattern: WaitGroup with Error Collection

```go
// file: waitgroup_errors.go
package main

import (
    "fmt"
    "sync"
)

type Result struct {
    ID  int
    Err error
    Val string
}

func processAll(ids []int) []Result {
    results := make([]Result, len(ids))
    var wg sync.WaitGroup

    for i, id := range ids {
        wg.Add(1)
        go func(idx, id int) {
            defer wg.Done()
            // write to pre-allocated slot — no mutex needed
            // because each goroutine writes to a unique index
            val, err := doWork(id)
            results[idx] = Result{ID: id, Val: val, Err: err}
        }(i, id)
    }

    wg.Wait()
    return results
}

func doWork(id int) (string, error) {
    return fmt.Sprintf("result-%d", id), nil
}

func main() {
    results := processAll([]int{1, 2, 3, 4, 5})
    for _, r := range results {
        if r.Err != nil {
            fmt.Printf("error for %d: %v\n", r.ID, r.Err)
        } else {
            fmt.Printf("result for %d: %s\n", r.ID, r.Val)
        }
    }
}
```

---

## 11. Mutex and RWMutex

### Mutex Internals

```
sync.Mutex state field (32-bit):
  bit 0: locked (1 = locked)
  bit 1: woken  (1 = goroutine being woken to acquire)
  bit 2: starving (1 = starvation mode)
  bits 3+: number of waiters

Two modes:
  Normal mode: FIFO queue + goroutine that just woke competes with
               new arrivals. New arrivals often win (they're on CPU).
               Throughput is high, but a waiter can be starved.

  Starvation mode: triggered when a waiter has waited > 1ms.
                   Lock ownership passes directly to the next waiter.
                   No competition. Prevents starvation.
```

```go
// file: mutex_patterns.go
package main

import (
    "fmt"
    "sync"
)

// ---- Pattern 1: Basic Mutex ----

type BankAccount struct {
    mu      sync.Mutex
    balance int
}

func (b *BankAccount) Deposit(amount int) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.balance += amount
}

func (b *BankAccount) Withdraw(amount int) error {
    b.mu.Lock()
    defer b.mu.Unlock()
    if b.balance < amount {
        return fmt.Errorf("insufficient funds: have %d, need %d", b.balance, amount)
    }
    b.balance -= amount
    return nil
}

func (b *BankAccount) Balance() int {
    b.mu.Lock()
    defer b.mu.Unlock()
    return b.balance
}

// ---- Pattern 2: RWMutex (read-heavy workloads) ----

// RWMutex allows MULTIPLE concurrent readers OR one exclusive writer.
// Use when reads >> writes.

type Cache struct {
    mu    sync.RWMutex
    store map[string]string
}

func NewCache() *Cache {
    return &Cache{store: make(map[string]string)}
}

func (c *Cache) Set(key, val string) {
    c.mu.Lock()         // exclusive: no reads during write
    defer c.mu.Unlock()
    c.store[key] = val
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()         // shared: multiple goroutines can read simultaneously
    defer c.mu.RUnlock()
    v, ok := c.store[key]
    return v, ok
}

// ---- Anti-Pattern: Lock Contention ----

// BAD: holds lock during network/IO call
func (b *BankAccount) DepositWithLog_BAD(amount int) {
    b.mu.Lock()
    defer b.mu.Unlock()
    b.balance += amount
    // NEVER do IO while holding a mutex
    // logToRemoteService(amount) // this can take 100ms, everyone else blocks
}

// GOOD: do IO outside lock, lock only for state mutation
func (b *BankAccount) DepositWithLog_GOOD(amount int) {
    b.mu.Lock()
    b.balance += amount
    snapshot := b.balance // capture what we need
    b.mu.Unlock()         // release ASAP
    // now safe to do IO without holding the lock
    _ = snapshot // logToService(snapshot)
}

func main() {
    acc := &BankAccount{balance: 1000}
    var wg sync.WaitGroup

    // concurrent deposits
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(amt int) {
            defer wg.Done()
            acc.Deposit(amt)
        }(100)
    }
    wg.Wait()
    fmt.Println("balance:", acc.Balance()) // always 2000
}
```

---

## 12. sync.Once

### What It Does

`sync.Once` guarantees a function runs **exactly once**, even if called from multiple goroutines simultaneously. This is the correct way to do lazy initialization.

```go
// file: sync_once.go
package main

import (
    "fmt"
    "sync"
)

type DB struct {
    conn string
}

var (
    instance *DB
    once     sync.Once
)

// GetDB: safe for concurrent calls — initDB() runs exactly once
func GetDB() *DB {
    once.Do(func() {
        // expensive initialization
        fmt.Println("initializing DB connection")
        instance = &DB{conn: "postgres://localhost/mydb"}
    })
    return instance
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            db := GetDB()
            _ = db
        }()
    }
    wg.Wait()
    // "initializing DB connection" printed exactly once
}
```

### sync.Once Internals

```
state: uint32 (bit 0 = done, bits 1+ = holding goroutines)
m: sync.Mutex

Flow:
  1. Load state atomically.
  2. If done bit is set: return immediately (fast path).
  3. If not done: acquire mutex.
  4. Re-check done bit (double-check locking).
  5. If still not done: run f(), set done bit.
  6. Release mutex. Wake waiters.
```

---

## 13. sync.Pool

### What It Is

`sync.Pool` is a **cache of reusable objects** to reduce GC pressure. Objects are borrowed, used, then returned. The GC may clear the pool at any time.

```
Without Pool:
  allocate → use → GC collects → allocate → use → GC ...
  High allocation rate → frequent GC → latency spikes

With Pool:
  allocate → use → return to pool → borrow → use → return ...
  Low allocation rate → infrequent GC → stable latency
```

```go
// file: sync_pool.go
package main

import (
    "bytes"
    "fmt"
    "sync"
)

var bufPool = sync.Pool{
    New: func() interface{} {
        // Called when pool is empty. Return pointer, not value.
        return new(bytes.Buffer)
    },
}

func processRequest(data string) string {
    // Get a buffer from pool (or New() if pool empty)
    buf := bufPool.Get().(*bytes.Buffer)
    buf.Reset()           // CRITICAL: reset before use — may have old data
    defer bufPool.Put(buf) // CRITICAL: return to pool, even on error

    buf.WriteString("processed: ")
    buf.WriteString(data)
    return buf.String()
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(i int) {
            defer wg.Done()
            result := processRequest(fmt.Sprintf("request-%d", i))
            fmt.Println(result)
        }(i)
    }
    wg.Wait()
}
```

### Pool Rules

```
Rule 1: Always Reset() objects before use. Pool objects may have old state.
Rule 2: Always Put() back even on error paths. Use defer.
Rule 3: Don't put anything that holds resources (file handles, connections).
        Pool can drop them without closing.
Rule 4: Store pointers, not values. Pool stores interface{}.
        Storing a value type causes allocation on every Get().
Rule 5: Pool does NOT guarantee the same object is returned.
        Objects can be GC'd between Put and Get.
```

---

## 14. sync.Map

### When to Use

`sync.Map` is a concurrent map optimized for **two specific use cases**:

1. Keys are written once, read many times (static registry)
2. Multiple goroutines writing disjoint sets of keys

For general concurrent map access, `sync.Mutex + map` is usually faster.

```go
// file: sync_map.go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var m sync.Map

    // Store
    m.Store("key1", "value1")
    m.Store("key2", 42)

    // Load
    if val, ok := m.Load("key1"); ok {
        fmt.Println("loaded:", val)
    }

    // LoadOrStore: atomic get-or-set
    actual, loaded := m.LoadOrStore("key3", "default")
    fmt.Printf("key3: actual=%v, alreadyExisted=%v\n", actual, loaded)

    // Range: iterate all entries
    m.Range(func(key, value interface{}) bool {
        fmt.Printf("  %v -> %v\n", key, value)
        return true // return false to stop iteration
    })

    // Delete
    m.Delete("key1")

    // LoadAndDelete: atomic get-and-delete
    if val, ok := m.LoadAndDelete("key2"); ok {
        fmt.Println("deleted:", val)
    }
}
```

---

## 15. Context

### What Context Is For

`context.Context` is the standard mechanism for:
1. **Cancellation** — stop work when it's no longer needed
2. **Deadlines** — stop work after a time limit
3. **Request-scoped values** — carry request IDs, auth tokens across the call tree

```
context.Context is the first argument to ANY function that does I/O,
makes network calls, or starts goroutines. This is a Go convention,
not optional.

func DoThing(ctx context.Context, ...) error { ... }  // correct
func DoThing(...) error { ... }                        // missing context — wrong in production
```

### Context Tree

```
context.Background()
       │
       ├─ WithCancel ──────────────────────► cancel() called → propagates down
       │       │
       │       ├─ WithTimeout(5s)
       │       │       │
       │       │       └─ WithValue("requestID", "abc-123")
       │       │
       │       └─ WithDeadline(time.Now().Add(10s))
       │
       └─ WithValue("userID", 42)
```

### All Context Variants

```go
// file: context_complete.go
package main

import (
    "context"
    "fmt"
    "time"
)

// --- Background and TODO ---
// context.Background(): root context. Use at main(), tests, top-level handlers.
// context.TODO(): placeholder when you haven't plumbed context yet.
//                 grep for TODO to find places to fix.

// --- WithCancel ---
func withCancelExample() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel() // ALWAYS defer cancel to prevent context leak

    go func() {
        <-ctx.Done()
        fmt.Println("goroutine: context cancelled:", ctx.Err())
    }()

    time.Sleep(50 * time.Millisecond)
    cancel() // cancel explicitly
    time.Sleep(10 * time.Millisecond) // let goroutine print
}

// --- WithTimeout ---
func withTimeoutExample() {
    ctx, cancel := context.WithTimeout(context.Background(), 100*time.Millisecond)
    defer cancel()

    done := make(chan struct{})
    go func() {
        defer close(done)
        // simulate slow operation
        select {
        case <-time.After(200 * time.Millisecond): // slower than timeout
            fmt.Println("work done")
        case <-ctx.Done():
            fmt.Println("work cancelled:", ctx.Err()) // context.DeadlineExceeded
        }
    }()
    <-done
}

// --- WithDeadline ---
func withDeadlineExample() {
    deadline := time.Now().Add(50 * time.Millisecond)
    ctx, cancel := context.WithDeadline(context.Background(), deadline)
    defer cancel()

    select {
    case <-time.After(200 * time.Millisecond):
        fmt.Println("never reached")
    case <-ctx.Done():
        fmt.Println("deadline exceeded:", ctx.Err())
        fmt.Println("deadline was:", deadline)
    }
}

// --- WithValue ---
// IMPORTANT: use context values for REQUEST-SCOPED data only.
// Don't pass function parameters via context. It obscures API contracts.
// Use typed keys to avoid collisions.

type contextKey string

const (
    requestIDKey contextKey = "requestID"
    userIDKey    contextKey = "userID"
)

func withValueExample() {
    ctx := context.WithValue(context.Background(), requestIDKey, "req-abc-123")
    ctx = context.WithValue(ctx, userIDKey, int64(42))

    processRequest(ctx)
}

func processRequest(ctx context.Context) {
    reqID, _ := ctx.Value(requestIDKey).(string)  // type assert, ok idiom
    userID, _ := ctx.Value(userIDKey).(int64)
    fmt.Printf("processing request %s for user %d\n", reqID, userID)
}

func main() {
    fmt.Println("=== WithCancel ===")
    withCancelExample()
    fmt.Println("=== WithTimeout ===")
    withTimeoutExample()
    fmt.Println("=== WithDeadline ===")
    withDeadlineExample()
    fmt.Println("=== WithValue ===")
    withValueExample()
}
```

### Context Rules

```
Rule 1: Always pass ctx as the FIRST argument.
Rule 2: Always defer cancel(). Every WithCancel/WithTimeout/WithDeadline
        creates a goroutine internally. Forgetting cancel() = goroutine leak.
Rule 3: Never store context in a struct field (except HTTP Request).
        Pass it explicitly on each call.
Rule 4: ctx.Done() is a channel that is closed when context is cancelled.
        Check it in select alongside your other operations.
Rule 5: context.Value is for request-scoped data: request IDs, trace IDs.
        Not for optional function parameters.
```

---

## 16. Pipeline Pattern

### What a Pipeline Is

A pipeline is a series of stages where each stage:
1. Receives values from an upstream channel
2. Processes them
3. Sends results to a downstream channel

```
input ──► [stage1: parse] ──► [stage2: validate] ──► [stage3: persist] ──► output
```

This allows stages to run concurrently. While stage3 processes item N, stage2 processes N+1 and stage1 processes N+2.

```go
// file: pipeline.go
package main

import (
    "context"
    "fmt"
    "strconv"
)

// Each stage takes a ctx and an input channel.
// Returns an output channel. Starts its own goroutine.
// ALWAYS check ctx.Done() to stop when context is cancelled.

// Stage 1: generate
func generate(ctx context.Context, nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case <-ctx.Done():
                return
            case out <- n:
            }
        }
    }()
    return out
}

// Stage 2: square
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

// Stage 3: stringify
func stringify(ctx context.Context, in <-chan int) <-chan string {
    out := make(chan string)
    go func() {
        defer close(out)
        for n := range in {
            select {
            case <-ctx.Done():
                return
            case out <- strconv.Itoa(n):
            }
        }
    }()
    return out
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Wire up the pipeline
    nums := generate(ctx, 1, 2, 3, 4, 5)
    squares := square(ctx, nums)
    strings := stringify(ctx, squares)

    // Drain the final stage
    for s := range strings {
        fmt.Println(s)
    }
}
```

```
Output: 1, 4, 9, 16, 25 (as strings)
```

---

## 17. Fan-Out / Fan-In

### Fan-Out: One Channel, Multiple Workers

```
                    ┌──► worker 1
input channel ──────┼──► worker 2
                    └──► worker 3
```

### Fan-In: Multiple Channels, One Output

```
channel 1 ──┐
channel 2 ──┼──► merged output channel
channel 3 ──┘
```

```go
// file: fan_out_fan_in.go
package main

import (
    "context"
    "fmt"
    "sync"
)

type Job struct{ ID int }
type Result struct{ JobID, Value int }

// Fan-Out: distribute jobs from one channel to N workers
// Each worker has its own result channel
func fanOut(ctx context.Context, jobs <-chan Job, n int) []<-chan Result {
    results := make([]<-chan Result, n)
    for i := 0; i < n; i++ {
        results[i] = worker(ctx, jobs)
    }
    return results
}

func worker(ctx context.Context, jobs <-chan Job) <-chan Result {
    out := make(chan Result)
    go func() {
        defer close(out)
        for job := range jobs {
            select {
            case <-ctx.Done():
                return
            case out <- Result{JobID: job.ID, Value: job.ID * job.ID}:
            }
        }
    }()
    return out
}

// Fan-In: merge multiple result channels into one
func fanIn(ctx context.Context, channels ...<-chan Result) <-chan Result {
    merged := make(chan Result)
    var wg sync.WaitGroup

    output := func(c <-chan Result) {
        defer wg.Done()
        for r := range c {
            select {
            case <-ctx.Done():
                return
            case merged <- r:
            }
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go output(ch)
    }

    // Close merged when all inputs are done
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Feed jobs
    jobs := make(chan Job, 10)
    for i := 1; i <= 10; i++ {
        jobs <- Job{ID: i}
    }
    close(jobs)

    // Fan-out to 3 workers, fan-in results
    workerResults := fanOut(ctx, jobs, 3)
    results := fanIn(ctx, workerResults...)

    for r := range results {
        fmt.Printf("job %d -> %d\n", r.JobID, r.Value)
    }
}
```

---

## 18. Worker Pool

### The Most Important Concurrency Pattern in Production

A worker pool maintains a fixed number of goroutines processing a work queue. This provides:
- **Bounded resource usage** — never create unbounded goroutines
- **Backpressure** — if workers are slow, the queue fills, slowing the producer
- **Graceful shutdown** — drain the queue before stopping

```
Producer ──► [job queue channel] ──► Worker 1
                                 └──► Worker 2
                                 └──► Worker 3 (fixed N)
                        results ──► [result channel] ──► Consumer
```

```go
// file: worker_pool.go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

type Job struct {
    ID      int
    Payload string
}

type Result struct {
    Job Job
    Out string
    Err error
}

type WorkerPool struct {
    jobs    chan Job
    results chan Result
    wg      sync.WaitGroup
    once    sync.Once
}

func NewWorkerPool(ctx context.Context, numWorkers, jobQueueSize int) *WorkerPool {
    p := &WorkerPool{
        jobs:    make(chan Job, jobQueueSize),
        results: make(chan Result, jobQueueSize),
    }
    p.startWorkers(ctx, numWorkers)
    return p
}

func (p *WorkerPool) startWorkers(ctx context.Context, n int) {
    for i := 0; i < n; i++ {
        p.wg.Add(1)
        go p.runWorker(ctx, i)
    }

    // Close results when all workers are done
    go func() {
        p.wg.Wait()
        close(p.results)
    }()
}

func (p *WorkerPool) runWorker(ctx context.Context, id int) {
    defer p.wg.Done()

    for {
        select {
        case <-ctx.Done():
            fmt.Printf("worker %d: context cancelled\n", id)
            return
        case job, ok := <-p.jobs:
            if !ok {
                // jobs channel closed: no more work
                fmt.Printf("worker %d: jobs exhausted\n", id)
                return
            }
            result := p.process(ctx, job)
            select {
            case p.results <- result:
            case <-ctx.Done():
                return
            }
        }
    }
}

func (p *WorkerPool) process(ctx context.Context, job Job) Result {
    // simulate work with context awareness
    select {
    case <-time.After(10 * time.Millisecond):
        return Result{Job: job, Out: fmt.Sprintf("done:%s", job.Payload)}
    case <-ctx.Done():
        return Result{Job: job, Err: ctx.Err()}
    }
}

// Submit sends a job. Returns false if pool is shut down.
func (p *WorkerPool) Submit(job Job) bool {
    select {
    case p.jobs <- job:
        return true
    default:
        return false // queue full: apply backpressure to caller
    }
}

// Shutdown stops accepting jobs and waits for in-flight jobs to finish
func (p *WorkerPool) Shutdown() {
    p.once.Do(func() {
        close(p.jobs) // signal workers: no more jobs
    })
}

// Results returns the read-only result channel
func (p *WorkerPool) Results() <-chan Result {
    return p.results
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    pool := NewWorkerPool(ctx, 3, 100) // 3 workers, queue capacity 100

    // Submit jobs
    go func() {
        for i := 0; i < 10; i++ {
            pool.Submit(Job{ID: i, Payload: fmt.Sprintf("task-%d", i)})
        }
        pool.Shutdown()
    }()

    // Collect results
    for result := range pool.Results() {
        if result.Err != nil {
            fmt.Printf("error job %d: %v\n", result.Job.ID, result.Err)
        } else {
            fmt.Printf("job %d: %s\n", result.Job.ID, result.Out)
        }
    }
}
```

---

## 19. Semaphore

### What a Semaphore Is

A semaphore limits how many goroutines can be in a critical section simultaneously. In Go, you implement it with a buffered channel.

```
Semaphore with capacity N = "at most N goroutines may proceed"

  sem := make(chan struct{}, N)

  Acquire: sem <- struct{}{}  (blocks when N slots filled)
  Release: <-sem              (always in defer)
```

```go
// file: semaphore.go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

type Semaphore struct {
    ch chan struct{}
}

func NewSemaphore(n int) *Semaphore {
    return &Semaphore{ch: make(chan struct{}, n)}
}

func (s *Semaphore) Acquire(ctx context.Context) error {
    select {
    case s.ch <- struct{}{}:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s *Semaphore) Release() {
    <-s.ch
}

func main() {
    // Limit to 3 concurrent HTTP requests (or DB connections, etc.)
    sem := NewSemaphore(3)

    var wg sync.WaitGroup
    ctx := context.Background()

    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()

            if err := sem.Acquire(ctx); err != nil {
                fmt.Printf("goroutine %d: acquire failed: %v\n", id, err)
                return
            }
            defer sem.Release()

            fmt.Printf("goroutine %d: in critical section\n", id)
            time.Sleep(50 * time.Millisecond) // simulate work
            fmt.Printf("goroutine %d: done\n", id)
        }(i)
    }

    wg.Wait()
}

// Production note: golang.org/x/sync/semaphore provides a weighted semaphore
// where you can acquire(n) units and release(n) units — useful for
// limiting memory or connection weight, not just count.
```

---

## 20. Rate Limiting

### Token Bucket Rate Limiter

```
Token Bucket:
  - Bucket has capacity C
  - Tokens added at rate R per second
  - Each request consumes 1 token
  - If bucket empty: request waits (or is rejected)

This allows bursts up to C, then sustains R requests/sec.
```

```go
// file: rate_limiter.go
package main

import (
    "context"
    "fmt"
    "time"

    "golang.org/x/time/rate" // go get golang.org/x/time
)

// Using the standard x/time/rate token bucket

func callAPI(ctx context.Context, limiter *rate.Limiter, id int) error {
    // Wait blocks until a token is available or ctx is cancelled
    if err := limiter.Wait(ctx); err != nil {
        return fmt.Errorf("request %d: rate limit wait: %w", id, err)
    }
    fmt.Printf("request %d: executing at %s\n", id, time.Now().Format("15:04:05.000"))
    return nil
}

// Manual token bucket without external dependency:
func manualRateLimiter() {
    // Allow 5 requests per second
    ticker := time.NewTicker(200 * time.Millisecond) // 1s/5 = 200ms
    defer ticker.Stop()

    requests := make(chan int, 20)
    for i := 1; i <= 10; i++ {
        requests <- i
    }
    close(requests)

    for req := range requests {
        <-ticker.C // wait for next token
        fmt.Printf("processing request %d at %s\n", req, time.Now().Format("15:04:05.000"))
    }
}

func main() {
    // Rate: 2 requests/sec, burst up to 5
    limiter := rate.NewLimiter(rate.Limit(2), 5)

    ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
    defer cancel()

    for i := 0; i < 10; i++ {
        if err := callAPI(ctx, limiter, i); err != nil {
            fmt.Println("error:", err)
        }
    }
}
```

---

## 21. Backpressure

### What Backpressure Is

Backpressure is when a slow consumer signals a fast producer to slow down. Without it, a fast producer fills memory, crashes the service, or drops work silently.

```
Without backpressure:
  Producer: 10,000 msg/s ──► infinite buffer ──► Consumer: 1,000 msg/s
  Result: OOM crash after some time

With backpressure:
  Producer: 10,000 msg/s ──► bounded buffer (100) ──► Consumer: 1,000 msg/s
  Result: Producer blocks when buffer full. Naturally throttled.
```

In Go, a **buffered channel IS the backpressure mechanism**. When it's full, sends block.

```go
// file: backpressure.go
package main

import (
    "fmt"
    "time"
)

func producer(out chan<- int, total int) {
    defer close(out)
    for i := 0; i < total; i++ {
        // If consumer is slow, this blocks when channel is full.
        // That IS backpressure — producer slows to consumer's pace.
        out <- i
        fmt.Printf("produced %d\n", i)
    }
}

func consumer(in <-chan int) {
    for item := range in {
        time.Sleep(50 * time.Millisecond) // slow consumer
        fmt.Printf("consumed %d\n", item)
    }
}

// Non-blocking with drop (for metrics, logs — OK to lose some):
func producerWithDrop(out chan<- int, total int) {
    for i := 0; i < total; i++ {
        select {
        case out <- i:
            // sent
        default:
            fmt.Printf("DROPPED item %d (consumer too slow)\n", i)
        }
    }
    close(out)
}

func main() {
    // Buffer of 5: producer runs at most 5 ahead of consumer
    ch := make(chan int, 5)

    go producer(ch, 10)
    consumer(ch)
}
```

---

## 22. errgroup

### What errgroup Is

`golang.org/x/sync/errgroup` is a WaitGroup + error collection in one. It cancels the context if ANY goroutine returns an error.

This is the correct tool for **concurrent fan-out where any failure should cancel all peers**.

```go
// file: errgroup_example.go
package main

import (
    "context"
    "fmt"
    "time"

    "golang.org/x/sync/errgroup" // go get golang.org/x/sync
)

func fetchUser(ctx context.Context, id int) (string, error) {
    select {
    case <-time.After(10 * time.Millisecond):
        return fmt.Sprintf("user-%d", id), nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func fetchOrder(ctx context.Context, id int) (string, error) {
    select {
    case <-time.After(20 * time.Millisecond):
        return fmt.Sprintf("order-%d", id), nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func main() {
    // errgroup.WithContext: if any goroutine returns error, ctx is cancelled
    g, ctx := errgroup.WithContext(context.Background())

    var user, order string

    g.Go(func() error {
        var err error
        user, err = fetchUser(ctx, 1)
        return err
    })

    g.Go(func() error {
        var err error
        order, err = fetchOrder(ctx, 1)
        return err
    })

    // Wait for ALL goroutines. Returns first non-nil error.
    if err := g.Wait(); err != nil {
        fmt.Println("error:", err)
        return
    }

    fmt.Printf("user: %s, order: %s\n", user, order)
}
```

### errgroup with Bounded Concurrency (SetLimit)

```go
// Available since golang.org/x/sync v0.1.0
g, ctx := errgroup.WithContext(context.Background())
g.SetLimit(10) // at most 10 goroutines at a time

for _, item := range hugeList {
    item := item
    g.Go(func() error {
        return process(ctx, item)
    })
}
if err := g.Wait(); err != nil { ... }
```

---

## 23. Goroutine Leaks

### What a Goroutine Leak Is

A goroutine that was started but can never exit. It holds its stack, any closed-over variables, and registers. In production, this causes a slow memory growth that eventually OOMs the service.

### Common Leak Patterns

```
LEAK 1: Goroutine blocked on channel send/receive with no receiver/sender

    ch := make(chan int)
    go func() {
        ch <- 1 // blocks forever if nobody receives
    }()
    // goroutine leaks

LEAK 2: Goroutine blocked on context.Done() that's never cancelled

    func doWork(ctx context.Context) {
        go func() {
            select {
            case <-ctx.Done():
                return
            case result := <-someChannel:
                // ...
            }
        }()
    }
    // If ctx is never cancelled AND someChannel never sends,
    // goroutine leaks.

LEAK 3: Goroutine blocked in HTTP client with no timeout

    go func() {
        http.Get("http://slow-server") // blocks for minutes/forever
    }()
    // Use http.Client with Timeout always

LEAK 4: Forgotten goroutine after function returns

    func handler(w http.ResponseWriter, r *http.Request) {
        go func() {
            // uses r.Context() — but context is bound to the request
            // If goroutine outlives request, ctx is cancelled — this is OK
            // But if goroutine ignores ctx.Done(), it may block forever
            for {
                doSlowThing(r.Context()) // must check ctx.Done()
            }
        }()
    }
```

### Detecting Leaks

```go
// Use goleak in tests:
// go get go.uber.org/goleak

func TestMyFunction(t *testing.T) {
    defer goleak.VerifyNone(t) // fails if goroutines are left over

    // your test code
    MyFunction()
}
```

```go
// Monitor goroutine count in production:
import "runtime"

func goroutineCount() int {
    return runtime.NumGoroutine()
}

// Expose via metrics:
// metrics.Gauge("goroutines", float64(runtime.NumGoroutine()))
```

```go
// Get goroutine stacks (for debugging leaks):
import "runtime/pprof"
pprof.Lookup("goroutine").WriteTo(os.Stderr, 1)
```

### Fix Pattern: Always Have an Exit Condition

```go
// Every goroutine MUST have an exit path:
func safeGoroutine(ctx context.Context, ch <-chan Work) {
    for {
        select {
        case <-ctx.Done():       // exit: context cancelled
            return
        case w, ok := <-ch:     // exit: channel closed
            if !ok {
                return
            }
            process(w)
        }
    }
}
```

---

## 24. Go Memory Model

### Happens-Before

The Go memory model defines when a write to a variable is **guaranteed to be visible** to a read of that variable. Without a happens-before edge, a read might see any value.

```
Happens-before rules:
  1. Within a single goroutine, statements execute in order.
  2. go statement: code BEFORE go func() happens-before func starts.
  3. Channel send happens-before the corresponding receive completes.
  4. Closing a channel happens-before receive of zero value.
  5. sync.Mutex.Unlock() happens-before the next Lock().
  6. sync.Once.Do(f) completion happens-before any Do() call returns.
```

### Why This Matters: The Invisible Race

```go
// BAD: Data race — no happens-before between writer and reader
var data int
var ready bool

go func() {
    data = 42  // write
    ready = true
}()

// reader goroutine
for !ready {} // spin
fmt.Println(data) // may print 0! The write to data may not be visible.

// The compiler and CPU are allowed to reorder instructions within a goroutine.
// The reader may see ready=true but data=0 due to instruction reordering.
```

```go
// GOOD: Channel establishes happens-before
var data int
ch := make(chan struct{})

go func() {
    data = 42
    ch <- struct{}{} // send happens-before receive completes
}()

<-ch
fmt.Println(data) // always 42
```

---

## 25. Data Race Detection

### The Race Detector

Go ships with a built-in race detector (based on ThreadSanitizer). **Run with -race in ALL test/staging environments.**

```bash
go test -race ./...
go run -race main.go
go build -race -o myservice .
```

```
Performance overhead with -race:
  Memory: 5-10x
  CPU: 2-20x
  Acceptable for testing, staging.
  Do NOT deploy -race binary to production (customer-facing).
  DO deploy to a production-traffic shadow/canary to catch races under load.
```

### Example of a Race the Detector Finds

```go
// file: race_example.go
// Run: go run -race race_example.go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var count int
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            count++ // DATA RACE: concurrent read-modify-write
        }()
    }

    wg.Wait()
    fmt.Println(count) // undefined behavior — not necessarily 1000
}
```

```
Race detector output:
==================
WARNING: DATA RACE
Write at 0x... by goroutine ...:
  main.main.func1()
      race_example.go:17 +0x...
Previous write at 0x... by goroutine ...:
  main.main.func1()
      race_example.go:17 +0x...
==================
```

**Fix**: use `atomic.AddInt64` or `sync.Mutex`.

---

## 26. Profiling Concurrent Programs

### pprof Setup

```go
// file: profiling_server.go
package main

import (
    "net/http"
    _ "net/http/pprof" // side-effect import: registers /debug/pprof handlers
    "log"
)

func main() {
    // In production: serve pprof on an INTERNAL port, never public
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    // your real server...
    select {}
}
```

### Profiling Commands

```bash
# CPU profile (30 seconds)
go tool pprof http://localhost:6060/debug/pprof/profile?seconds=30

# Memory/heap profile
go tool pprof http://localhost:6060/debug/pprof/heap

# Goroutine stacks (find leaks)
go tool pprof http://localhost:6060/debug/pprof/goroutine

# Mutex contention profile
go tool pprof http://localhost:6060/debug/pprof/mutex

# Block profile (goroutines blocked on channels/mutexes)
go tool pprof http://localhost:6060/debug/pprof/block

# Enable mutex and block profiling at startup:
runtime.SetMutexProfileFraction(1)  // profile all mutex events
runtime.SetBlockProfileRate(1)      // profile all block events
# (set to 0 in production, non-zero only for profiling sessions)
```

### Execution Tracer (Scheduler Visibility)

```bash
# Capture a trace
curl -o trace.out http://localhost:6060/debug/pprof/trace?seconds=5

# View in browser
go tool trace trace.out
```

The execution tracer shows: goroutine creation/destruction, blocking/unblocking, GC events, syscall events, scheduler preemptions. This is the only tool that shows you scheduler-level behavior.

---

## 27. Production Patterns and Anti-Patterns

### PATTERNS (Use These)

```
Pattern 1: Structured Concurrency
  Always know the lifetime of every goroutine you start.
  Use WaitGroup, errgroup, or context to enforce it.

Pattern 2: Context Threading
  Pass ctx as the first arg to every function that does I/O.
  Respect ctx.Done() in every loop.

Pattern 3: Channel Ownership
  One goroutine owns (creates, closes) each channel.
  Others hold directional handles.

Pattern 4: Bounded Worker Pools
  Never create unbounded goroutines.
  Use a worker pool with a fixed count.

Pattern 5: Graceful Shutdown
  OS signal → cancel root context → all goroutines see ctx.Done()
  → drain in-flight work → WaitGroup.Wait() → exit.
```

### ANTI-PATTERNS (Avoid These)

```
Anti-Pattern 1: Goroutine-per-Request without Bound
  for req := range incoming {
      go handleRequest(req) // can spawn millions under load
  }
  FIX: use a worker pool

Anti-Pattern 2: Naked go func() without Tracking
  go func() { doWork() }() // who owns this? how does it stop?
  FIX: always track with WaitGroup or errgroup

Anti-Pattern 3: Mutex Held During IO
  mu.Lock()
  defer mu.Unlock()
  http.Get(url)  // blocks for seconds, all others wait
  FIX: release lock, do IO, re-acquire if needed

Anti-Pattern 4: Sending on Closed Channel
  close(ch)
  ch <- value  // panic
  FIX: coordinate close with sync.Once or ownership rules

Anti-Pattern 5: Ignoring ctx.Done()
  for item := range bigSlice {
      process(item) // runs even if request cancelled
  }
  FIX: add ctx.Done() check in the loop

Anti-Pattern 6: Using time.Sleep for Synchronization
  go someTask()
  time.Sleep(100 * time.Millisecond) // hope it's done?
  FIX: use WaitGroup, channel, or errgroup

Anti-Pattern 7: Large Messages Through Channels
  ch <- largeStruct{...} // copies entire struct on every send
  FIX: send pointers: ch <- &largeStruct{...}
  (but beware: pointer sends transfer ownership. Don't mutate after sending.)
```

---

## 28. Complete Production Example: HTTP Worker Service

This example combines: context, graceful shutdown, worker pool, rate limiting, signal handling, and error handling.

```go
// file: production_service.go
// Run: go run production_service.go
// Test: curl http://localhost:8080/jobs -d '{"payload":"hello"}'
// Stop: Ctrl+C or send SIGTERM
package main

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "log"
    "net/http"
    _ "net/http/pprof"
    "os"
    "os/signal"
    "sync"
    "sync/atomic"
    "syscall"
    "time"
)

// ─── Domain ──────────────────────────────────────────────────────────────────

type Job struct {
    ID      string
    Payload string
}

type Result struct {
    JobID  string
    Output string
    Err    error
}

// ─── Worker Pool ─────────────────────────────────────────────────────────────

type Pool struct {
    jobs        chan Job
    results     chan Result
    wg          sync.WaitGroup
    once        sync.Once
    numWorkers  int
    processed   atomic.Int64
    errors      atomic.Int64
}

func NewPool(ctx context.Context, numWorkers, queueSize int) *Pool {
    p := &Pool{
        jobs:       make(chan Job, queueSize),
        results:    make(chan Result, queueSize),
        numWorkers: numWorkers,
    }

    for i := 0; i < numWorkers; i++ {
        p.wg.Add(1)
        go p.worker(ctx, i)
    }

    go func() {
        p.wg.Wait()
        close(p.results)
    }()

    return p
}

func (p *Pool) worker(ctx context.Context, id int) {
    defer p.wg.Done()
    log.Printf("worker %d: started", id)
    defer log.Printf("worker %d: stopped", id)

    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-p.jobs:
            if !ok {
                return
            }

            result := p.processJob(ctx, job)

            if result.Err != nil {
                p.errors.Add(1)
            } else {
                p.processed.Add(1)
            }

            select {
            case p.results <- result:
            case <-ctx.Done():
                return
            }
        }
    }
}

func (p *Pool) processJob(ctx context.Context, job Job) Result {
    // Simulate processing with context awareness
    select {
    case <-time.After(20 * time.Millisecond):
        return Result{
            JobID:  job.ID,
            Output: fmt.Sprintf("processed: %s", job.Payload),
        }
    case <-ctx.Done():
        return Result{
            JobID: job.ID,
            Err:   fmt.Errorf("cancelled: %w", ctx.Err()),
        }
    }
}

func (p *Pool) Submit(ctx context.Context, job Job) error {
    select {
    case p.jobs <- job:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    default:
        return errors.New("queue full: service overloaded")
    }
}

func (p *Pool) Shutdown() {
    p.once.Do(func() {
        close(p.jobs)
    })
}

func (p *Pool) Stats() (processed, errs int64) {
    return p.processed.Load(), p.errors.Load()
}

// ─── HTTP Server ──────────────────────────────────────────────────────────────

type Server struct {
    pool   *Pool
    http   *http.Server
    jobSeq atomic.Int64
}

func NewServer(pool *Pool) *Server {
    s := &Server{pool: pool}
    mux := http.NewServeMux()
    mux.HandleFunc("/jobs", s.handleJob)
    mux.HandleFunc("/stats", s.handleStats)
    mux.HandleFunc("/health", s.handleHealth)

    s.http = &http.Server{
        Addr:         ":8080",
        Handler:      mux,
        ReadTimeout:  5 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  60 * time.Second,
    }
    return s
}

type JobRequest struct {
    Payload string `json:"payload"`
}

type JobResponse struct {
    JobID string `json:"job_id"`
}

func (s *Server) handleJob(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
        return
    }

    var req JobRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "bad request", http.StatusBadRequest)
        return
    }

    id := fmt.Sprintf("job-%d", s.jobSeq.Add(1))
    job := Job{ID: id, Payload: req.Payload}

    // Use request context: if client disconnects, submit is cancelled
    if err := s.pool.Submit(r.Context(), job); err != nil {
        if errors.Is(err, context.Canceled) || errors.Is(err, context.DeadlineExceeded) {
            http.Error(w, "request cancelled", 499)
        } else {
            http.Error(w, err.Error(), http.StatusServiceUnavailable)
        }
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusAccepted)
    json.NewEncoder(w).Encode(JobResponse{JobID: id})
}

func (s *Server) handleStats(w http.ResponseWriter, r *http.Request) {
    processed, errs := s.pool.Stats()
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]int64{
        "processed": processed,
        "errors":    errs,
    })
}

func (s *Server) handleHealth(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    w.Write([]byte("ok"))
}

// ─── Main: Wiring Everything Together ────────────────────────────────────────

func main() {
    // pprof on internal port
    go func() {
        log.Println(http.ListenAndServe("localhost:6060", nil))
    }()

    // Root context: entire program lifetime
    rootCtx, rootCancel := context.WithCancel(context.Background())
    defer rootCancel()

    // Signal handling: SIGTERM/SIGINT → cancel root context
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
    defer signal.Stop(sigCh)

    // Worker pool: 10 workers, queue of 500
    pool := NewPool(rootCtx, 10, 500)

    // Result logger goroutine
    var logWg sync.WaitGroup
    logWg.Add(1)
    go func() {
        defer logWg.Done()
        for result := range pool.Results() {
            if result.Err != nil {
                log.Printf("job %s failed: %v", result.JobID, result.Err)
            } else {
                log.Printf("job %s done: %s", result.JobID, result.Output)
            }
        }
    }()

    // HTTP server
    srv := NewServer(pool)

    // Start HTTP server
    go func() {
        log.Println("server listening on :8080")
        if err := srv.http.ListenAndServe(); err != nil && err != http.ErrServerClosed {
            log.Printf("http error: %v", err)
            rootCancel()
        }
    }()

    // Wait for shutdown signal
    select {
    case sig := <-sigCh:
        log.Printf("received signal: %v — shutting down", sig)
    case <-rootCtx.Done():
        log.Println("root context cancelled")
    }

    // ─── Graceful Shutdown Sequence ───────────────────────────────────────
    // Step 1: Stop accepting new HTTP requests (30s deadline)
    shutCtx, shutCancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer shutCancel()

    log.Println("shutting down HTTP server...")
    if err := srv.http.Shutdown(shutCtx); err != nil {
        log.Printf("http shutdown error: %v", err)
    }

    // Step 2: Stop accepting new jobs (close the jobs channel)
    log.Println("draining worker pool...")
    pool.Shutdown()

    // Step 3: Cancel root context to stop workers if they're still running
    rootCancel()

    // Step 4: Wait for result logger to flush all results
    logWg.Wait()

    processed, errs := pool.Stats()
    log.Printf("shutdown complete. processed=%d errors=%d", processed, errs)
}
```

---

## Security Checklist for Production Concurrent Code

```
[ ] Every goroutine has a defined exit path (ctx.Done or channel close)
[ ] No goroutine can block forever (always have timeout or context)
[ ] Channels have appropriate buffer sizes (document the reasoning)
[ ] Mutex never held during I/O or network calls
[ ] No shared state without synchronization (run -race in CI)
[ ] sync.Pool objects are Reset() before use
[ ] Context propagated to all I/O operations
[ ] Graceful shutdown tested: in-flight requests complete
[ ] Goroutine count monitored in production metrics
[ ] pprof endpoint on internal/non-public interface only
[ ] Rate limiters applied to external-facing endpoints
[ ] Worker pool bounded: no unbounded goroutine spawn under load
[ ] Signal handling tested: SIGTERM triggers clean shutdown
[ ] errgroup used for concurrent operations where any error should cancel all
[ ] No double-close of channels (use sync.Once for coordinated close)
```

---

## Benchmarks and Tests

```go
// file: concurrency_bench_test.go
package main

import (
    "sync"
    "sync/atomic"
    "testing"
)

// go test -bench=. -benchmem -count=3 ./...

var result int64

func BenchmarkAtomicIncrement(b *testing.B) {
    var counter int64
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            atomic.AddInt64(&counter, 1)
        }
    })
    result = counter
}

func BenchmarkMutexIncrement(b *testing.B) {
    var counter int64
    var mu sync.Mutex
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            mu.Lock()
            counter++
            mu.Unlock()
        }
    })
    result = counter
}

func BenchmarkChannelUnbuffered(b *testing.B) {
    ch := make(chan int)
    go func() {
        for v := range ch {
            _ = v
        }
    }()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ch <- i
    }
    close(ch)
}

func BenchmarkChannelBuffered(b *testing.B) {
    ch := make(chan int, b.N)
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        ch <- i
    }
    close(ch)
    for range ch {}
}
```

```bash
# Run benchmarks with CPU profiling
go test -bench=. -benchmem -cpuprofile=cpu.prof ./...
go tool pprof cpu.prof

# Run with race detector
go test -race -count=1 ./...

# Check for goroutine leaks in tests (requires goleak)
# go get go.uber.org/goleak
```

---

## Summary: Mental Models in One View

```
CONCEPT         WHAT IT IS                    WHEN TO USE
─────────────────────────────────────────────────────────────────────────
goroutine       lightweight managed thread    unit of concurrent work
channel         typed concurrent queue        transfer ownership of data
unbuffered ch   synchronization rendezvous    ensure receiver got the value
buffered ch     async decoupled queue         decouple producer/consumer speed
select          channel multiplexer           wait on multiple channels
context         cancellation propagation      I/O, timeouts, request scope
done chan        broadcast stop signal         stop many goroutines at once
OS signal        OS → process event           SIGTERM, SIGINT handling
atomic           lock-free numeric ops        hot-path counters, flags
sync.Mutex       exclusive critical section   protecting complex state
sync.RWMutex     shared reads, exclusive writes  read-heavy shared state
sync.WaitGroup   wait for N goroutines        fan-out and collect
sync.Once        exactly-once init            singletons, lazy init
sync.Pool        reusable object cache        reduce GC pressure
semaphore        bounded concurrency          limit parallel IO/DB calls
worker pool      bounded goroutine count      production job processing
pipeline         staged concurrent processing streaming transformations
fan-out          one input, many workers      parallel processing
fan-in           many inputs, one output      result merging
errgroup         WaitGroup + error + cancel   concurrent calls, fail-fast
rate limiter     token bucket throttle        external API calls
backpressure     full channel blocks sender   prevent OOM under load
```

---

*This guide covers the full production surface area of Go concurrency. Each section is designed to be re-read as your understanding deepens. The patterns in Section 28 are the skeleton of most production Go services.*

Now let me build this. This will be a comprehensive, production-grade guide — one large `.md` file.Here's what's in the guide and the mental model behind each section:

---

**Foundation (Sections 1–3)** — Most guides skip this entirely. The G/M/P scheduler model, work-stealing, signal-based preemption (Go 1.14+), and copying stacks are what make goroutines cheap. You cannot reason about goroutine behavior under load without understanding these.

**Channels (Sections 4–6)** — The runtime `hchan` struct internals, the exact send/receive paths, and the channel state table answer *why* certain bugs happen (blocking on nil channels, panicking on double-close, missed signals). Directional channels `chan<-` and `<-chan` are the ownership contract — enforced at compile time.

**Orchestration Primitives (Sections 7–15)** — `select`, OS signals, done-channel broadcast pattern, atomic vs mutex (with nanosecond cost data), WaitGroup rules, `sync.Once` (double-check locking internals), `sync.Pool` (with Reset() rule — the most common bug), `sync.Map` (with the two specific use cases it's actually good for), and Context end-to-end.

**Patterns (Sections 16–22)** — Pipeline, fan-out/fan-in, worker pool (the most production-critical pattern with full implementation), semaphore, rate limiting, backpressure, and `errgroup`. The worker pool alone is what 80% of Go services are built around.

**Production Safety (Sections 23–27)** — Goroutine leak taxonomy, the happens-before memory model (the invisible race example), race detector usage, pprof commands for mutex contention and blocking profiles, and the execution tracer.

**Complete Example (Section 28)** — Wires everything together: HTTP server → worker pool → result logging → graceful shutdown on SIGTERM with a 30-second drain window. This is the skeleton of a real production service.

# Goroutines: The Complete Elite Guide
> Production-Grade Concurrency in Go — From Runtime Internals to Real-World Patterns

---

## Table of Contents

1. [The Mental Model: What Concurrency Really Is](#1-the-mental-model)
2. [Go Runtime Internals: GMP Scheduler](#2-gmp-scheduler)
3. [Goroutine Lifecycle and Stack Growth](#3-goroutine-lifecycle)
4. [Channels: Internal Architecture](#4-channel-internals)
5. [Counter, Signal, Message — What Do These Actually Mean?](#5-counter-signal-message)
6. [sync Package: Every Primitive Explained](#6-sync-package)
7. [sync/atomic: Lock-Free Programming](#7-sync-atomic)
8. [Channel Patterns: Production-Grade](#8-channel-patterns)
9. [Context Package: Cancellation and Deadlines](#9-context-package)
10. [Go Memory Model: Happens-Before](#10-memory-model)
11. [Race Conditions, Data Races, and the Race Detector](#11-race-conditions)
12. [Goroutine Leaks: Detection and Prevention](#12-goroutine-leaks)
13. [Advanced Concurrency Patterns](#13-advanced-patterns)
14. [errgroup, singleflight, semaphore](#14-extended-concurrency)
15. [Production Checklist and Anti-Patterns](#15-production-checklist)

---

## 1. The Mental Model

### Concurrency vs Parallelism

This distinction is fundamental. Most engineers confuse them for years.

```
CONCURRENCY: Structure — dealing with many things at once (design)
PARALLELISM: Execution — doing many things at once (hardware)

A single-core machine can be concurrent but NOT parallel.
A multi-core machine can be both.

Go gives you concurrency as a first-class language feature.
Parallelism is a runtime detail (GOMAXPROCS).
```

### CSP: Communicating Sequential Processes

Go's concurrency is based on Hoare's CSP (1978). The core philosophy:

```
"Do not communicate by sharing memory.
 Share memory by communicating."

                    WRONG (shared memory):
  Goroutine A ──┐
                ├──► shared variable (DANGER: race condition)
  Goroutine B ──┘

                    RIGHT (message passing):
  Goroutine A ──► channel ──► Goroutine B
```

Each goroutine is an independent sequential process. They coordinate
exclusively through channels. This eliminates most concurrency bugs
by design, not discipline.

### The Ownership Principle

Before writing any concurrent code, ask:

```
WHO OWNS THIS DATA?

Rule: At any moment, only ONE goroutine should own (write to) a piece of data.

Transfer ownership by sending through a channel.
Share read-only data freely (no mutation = no race).
Protect shared mutable state with a mutex — but prefer message passing.
```

---

## 2. GMP Scheduler

This is what separates Go engineers from Go experts. You MUST understand
how the scheduler works to reason about goroutine behavior.

### The Three Entities

```
G = Goroutine       — The unit of work. Holds stack, PC, registers.
M = Machine (OS thread) — The worker. Maps to a real OS thread (pthread).
P = Processor       — The scheduler context. Holds run queue of Gs.

GOMAXPROCS controls how many Ps exist (default: CPU count).
There can be many more Ms than Ps (for blocking syscalls).
```

### GMP Architecture

```
                     Go Runtime
  ┌──────────────────────────────────────────────────────────────┐
  │                                                              │
  │   Global Run Queue (GRQ)                                     │
  │   [G][G][G][G][G]  ← overflow goroutines                    │
  │                                                              │
  │   P0          P1          P2          P3                     │
  │  ┌────┐      ┌────┐      ┌────┐      ┌────┐                 │
  │  │LRQ │      │LRQ │      │LRQ │      │LRQ │  ← Local Run Q  │
  │  │G G │      │G G │      │G G │      │G G │                 │
  │  └─┬──┘      └─┬──┘      └─┬──┘      └─┬──┘                 │
  │    │           │           │           │                     │
  │   M0          M1          M2          M3   ← OS Threads      │
  │    │           │           │           │                     │
  └────┼───────────┼───────────┼───────────┼────────────────────┘
       │           │           │           │
    CPU Core    CPU Core    CPU Core    CPU Core
```

### Scheduler Rules

```
1. WORK STEALING: If P's local run queue is empty, it steals
   half the goroutines from another P's queue.

2. HAND-OFF: When M blocks on a syscall, P detaches and finds
   another M (or creates one) to run its goroutines.
   This is why Go can have thousands of goroutines on 4 cores.

3. PREEMPTION: Since Go 1.14, goroutines can be preempted at
   any point (not just function calls). This prevents one
   goroutine from starving others.

4. SPINNING: Some Ms spin (busy-wait) looking for work rather
   than sleeping, to reduce latency when new goroutines appear.
```

### What Happens When You Launch a Goroutine

```go
go f()  // What actually happens?
```

```
1. Runtime allocates a G struct
2. G gets a small initial stack (2KB — NOT a full OS thread stack)
3. G is placed in the current P's local run queue
4. Current goroutine continues executing
5. Scheduler picks up G when a P has capacity

Cost of goroutine creation: ~2KB stack + G struct allocation
Cost of OS thread creation: ~1-8MB stack + kernel context
This is why you can have 100,000 goroutines but not 100,000 threads.
```

---

## 3. Goroutine Lifecycle and Stack Growth

### Stack: How It Actually Works

```
Go goroutine stacks are NOT fixed like OS threads.
They start small (2KB) and GROW on demand.

Go 1.3+: Contiguous stacks (replaces old segmented stacks)

Initial stack: 2KB
Doubles when needed: 2KB → 4KB → 8KB → 16KB ...
Max stack: 1GB (64-bit), 250MB (32-bit) — configurable

How doubling works:
  1. Stack overflow check on function entry
  2. Runtime allocates a 2x larger stack
  3. ALL data is COPIED to new stack
  4. All pointers are updated (the hard part)
  5. Old stack is freed

This means: pointers to stack variables CANNOT be passed between
goroutines safely without synchronization — stack may move!
(In practice, Go's escape analysis moves heap-bound vars to heap.)
```

### Goroutine States

```
                   go f()
                     │
                     ▼
              ┌─────────────┐
              │   RUNNABLE  │ ← in run queue, waiting for M
              └──────┬──────┘
                     │ M picks it up
                     ▼
              ┌─────────────┐
              │   RUNNING   │ ← executing on an M
              └──────┬──────┘
                     │
          ┌──────────┼──────────┐
          │          │          │
          ▼          ▼          ▼
    ┌──────────┐ ┌────────┐ ┌────────────┐
    │ WAITING  │ │SYSCALL │ │   DEAD     │
    │(blocked  │ │(OS I/O)│ │(func done) │
    │ on chan, │ └────┬───┘ └────────────┘
    │ mutex,   │      │
    │ timer)   │ P detaches,
    └──────┬───┘ M blocks
           │          │
           │ unblocked │ syscall returns
           └───────────┘
                  │
              RUNNABLE
```

### Why Goroutines Are "Green Threads"

```
OS Thread:
  - Scheduled by kernel
  - ~1-8MB stack (fixed)
  - Context switch: ~1-2 microseconds (kernel mode switch)
  - Max per process: typically ~10,000

Go Goroutine:
  - Scheduled by Go runtime (user space)
  - 2KB initial stack (growable)
  - Context switch: ~200 nanoseconds (no kernel mode switch)
  - Max practical: 100,000+ (memory bound)

The runtime multiplexes N goroutines onto M OS threads.
This is the M:N threading model.
```

---

## 4. Channel Internals

Understanding channel internals explains every behavior you will
encounter in production. This is NOT in most tutorials.

### The hchan Struct (Simplified)

```go
// Internal representation (from runtime/chan.go)
type hchan struct {
    qcount   uint           // number of elements in queue
    dataqsiz uint           // capacity of circular buffer
    buf      unsafe.Pointer // pointer to circular buffer (nil if unbuffered)
    elemsize uint16         // size of one element
    closed   uint32         // 1 if channel is closed
    elemtype *_type         // element type (for GC)
    sendx    uint           // send index (producer head)
    recvx    uint           // receive index (consumer head)
    recvq    waitq          // queue of blocked receivers (goroutines waiting to recv)
    sendq    waitq          // queue of blocked senders (goroutines waiting to send)
    lock     mutex          // protects ALL fields above
}

type waitq struct {
    first *sudog  // doubly linked list of waiting goroutines
    last  *sudog
}

type sudog struct {
    g       *g            // the goroutine
    elem    unsafe.Pointer // data element (what they're sending/waiting for)
    next    *sudog
    prev    *sudog
    // ... more fields
}
```

### Visual: Buffered Channel with cap=3

```
make(chan int, 3)  →  dataqsiz=3, buf=[_][_][_]

State: Empty (qcount=0)
  ┌─────────────────────────────────────┐
  │ buf: [ _ ][ _ ][ _ ]               │
  │       ↑                             │
  │    sendx=0, recvx=0                 │
  │ recvq: [G1 waiting] → blocks!       │
  └─────────────────────────────────────┘

State: 2 items (qcount=2)
  After ch <- 10; ch <- 20
  ┌─────────────────────────────────────┐
  │ buf: [10 ][20 ][ _ ]               │
  │       ↑    ↑    ↑                  │
  │    recvx  sendx                     │
  │ recvq: empty (no blocked receivers) │
  └─────────────────────────────────────┘

State: Full (qcount=3)
  After ch <- 30
  ┌─────────────────────────────────────┐
  │ buf: [10 ][20 ][30 ]               │
  │ sendq: [G1 waiting] → G1 blocks!   │
  └─────────────────────────────────────┘
```

### The Four Send/Receive Cases

```
Case 1: SEND to channel with waiting RECEIVER
  ─ Copy data directly from sender to receiver's stack
  ─ Wake up receiver goroutine (put it in run queue)
  ─ Fastest path: zero allocations, bypasses buffer entirely

Case 2: SEND to channel with buffer SPACE available
  ─ Copy data into circular buffer
  ─ Increment sendx (wraps around)
  ─ Sender continues without blocking

Case 3: SEND to FULL buffered / UNBUFFERED channel (no receiver)
  ─ Create sudog for the goroutine
  ─ Add to channel's sendq
  ─ Park goroutine (take off M, put on sendq)
  ─ Goroutine wakes when buffer has space or receiver arrives

Case 4: RECEIVE from CLOSED, empty channel
  ─ Returns zero value + false (ok = false)
  ─ Never blocks
  ─ Reading from closed channel is safe and well-defined
```

### Unbuffered vs Buffered: The Key Insight

```
UNBUFFERED (make(chan T)):
  Sender and receiver must RENDEZVOUS.
  Send blocks until receiver is ready.
  Receive blocks until sender is ready.
  
  This is a SYNCHRONIZATION POINT — guaranteed happens-before.
  The send completes only when receive completes.

  Producer ──[send]──► (both blocked until rendezvous) ──► Consumer
                               ↑
                    This IS the synchronization

BUFFERED (make(chan T, N)):
  Sender can deposit N items without blocking.
  Decouples producer and consumer timing.
  NOT a synchronization guarantee (sender doesn't wait for receiver).

  Use buffered when:
    - You know exact throughput (N = batch size)
    - Producer bursts need dampening
    - You want a bounded work queue

  Use unbuffered when:
    - You need a confirmed handoff
    - You want to rate-control producers
    - Signaling (done channels, semaphores)
```

### Channel Direction: Type Safety at Compile Time

```go
// Bidirectional (full channel)
ch := make(chan int)

// These are TYPES, not just annotations
var send chan<- int = ch   // send-only: can only ch <- val
var recv <-chan int = ch   // recv-only: can only val := <-ch

// Why this matters in functions:
func producer(out chan<- int) {
    out <- 42      // OK
    // x := <-out // COMPILE ERROR: cannot receive from send-only
}

func consumer(in <-chan int) {
    x := <-in     // OK
    // in <- 99   // COMPILE ERROR: cannot send to receive-only
}

// Channel directions are checked at compile time.
// Bidirectional channels implicitly convert to directional.
// This is API design: tell callers exactly how a channel is used.
```

---

## 5. Counter, Signal, Message — What Do These Actually Mean?

These are COMMUNICATION PATTERNS built on top of channels and
sync primitives. You must know them cold.

### 5.1 Counter

A counter tracks a quantity that multiple goroutines modify concurrently.
Three implementation strategies, each with different tradeoffs:

#### Strategy A: Mutex-Protected Counter

```go
package main

import (
    "fmt"
    "sync"
)

// MutexCounter — correct for general-purpose counting
// Use when: reads and writes happen, or you need snapshots
type MutexCounter struct {
    mu    sync.Mutex
    value int64
}

func (c *MutexCounter) Inc() {
    c.mu.Lock()
    c.value++
    c.mu.Unlock()
}

func (c *MutexCounter) Add(n int64) {
    c.mu.Lock()
    c.value += n
    c.mu.Unlock()
}

func (c *MutexCounter) Value() int64 {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}

func mutexCounterDemo() {
    c := &MutexCounter{}
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Inc()
        }()
    }

    wg.Wait()
    fmt.Println("MutexCounter:", c.Value()) // Always 1000
}
```

#### Strategy B: Atomic Counter

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// AtomicCounter — fastest for simple increment/read
// Use when: only Add and Load operations, no compound operations
type AtomicCounter struct {
    value int64  // MUST be 64-bit aligned (use int64, not int)
}

func (c *AtomicCounter) Inc() {
    atomic.AddInt64(&c.value, 1)
}

func (c *AtomicCounter) Add(n int64) {
    atomic.AddInt64(&c.value, n)
}

func (c *AtomicCounter) Value() int64 {
    return atomic.LoadInt64(&c.value)
}

func atomicCounterDemo() {
    c := &AtomicCounter{}
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            c.Inc()
        }()
    }

    wg.Wait()
    fmt.Println("AtomicCounter:", c.Value()) // Always 1000
}

// Performance comparison:
// AtomicCounter: ~10ns per op (hardware CAS instruction)
// MutexCounter:  ~30ns per op (lock acquisition + release)
// Difference matters at millions of ops per second
```

#### Strategy C: Channel-Based Counter (WaitGroup pattern)

```go
// WaitGroup IS a counter under the hood.
// It counts active goroutines.
// Add(n) increments, Done() decrements, Wait() blocks until 0.

var wg sync.WaitGroup

wg.Add(1)   // counter: 1
go func() {
    defer wg.Done() // counter: 0
    // do work
}()

wg.Wait() // blocks until counter == 0
```

```
WaitGroup internal state (64 bits on 64-bit systems):
  [ counter (32 bits) ][ waiter count (32 bits) ]

Add() atomically increments counter
Done() atomically decrements counter; if counter==0, wakes all waiters
Wait() atomically increments waiter count; parks goroutine

Critical rules:
  1. wg.Add() BEFORE launching goroutine (not inside)
  2. Never copy a WaitGroup after first use
  3. wg.Add() and wg.Wait() can be called concurrently
     but Add() with positive delta must not be concurrent with Wait()
```

### 5.2 Signal

A signal is a channel used to communicate an EVENT, not data.
The data is irrelevant; the fact that something happened is the message.

```go
// Three canonical signal patterns:

// --- Pattern 1: Done signal (one sender, one receiver) ---
done := make(chan struct{})  // struct{}{} costs 0 bytes

go func() {
    // do work
    close(done)  // signal: work is done
}()

<-done  // wait for signal (blocking)


// --- Pattern 2: Quit signal (broadcast to many goroutines) ---
quit := make(chan struct{})

for i := 0; i < 10; i++ {
    go func() {
        for {
            select {
            case <-quit:
                return  // ALL goroutines exit when quit is closed
            default:
                // work
            }
        }
    }()
}

close(quit)  // broadcast: unblocks ALL receivers simultaneously
             // This only works with close(), not with sending!
             // Sending would only wake ONE receiver.


// --- Pattern 3: Ready signal (synchronization point) ---
ready := make(chan struct{})

go func() {
    // setup work (db connection, cache warm-up, etc.)
    close(ready)  // signal: setup complete
}()

<-ready  // wait until ready before proceeding
```

```
WHY struct{} instead of bool or int?

chan struct{} communicates: "this event happened" — zero bytes
chan bool communicates: "this event happened AND here's a boolean"
chan int communicates: "this event happened AND here's a number"

If you don't need data, use struct{}. It's idiomatic and free.

Rule: If the channel's VALUE doesn't matter, use chan struct{}.
      close(ch) is the canonical "broadcast signal to all waiters".
      Sending (ch <- struct{}{}) signals exactly ONE waiter.
```

### 5.3 Message

A message is data passed through a channel. The channel is the mailbox;
the message is the letter. This is Go's mechanism for transferring
ownership and coordinating work.

```go
// --- Simple message: raw value ---
ch := make(chan int)
go func() { ch <- 42 }()
v := <-ch  // receive the message


// --- Rich message: struct with request + response channel ---
// This is the "stateful goroutine" or "actor" pattern
type Request struct {
    Key      string
    Response chan string  // response channel embedded in request
}

func cacheActor(requests <-chan Request) {
    cache := make(map[string]string)
    for req := range requests {
        // Only THIS goroutine touches cache — no mutex needed
        val := cache[req.Key]
        req.Response <- val  // send response back
    }
}

// Caller:
requests := make(chan Request, 100)
go cacheActor(requests)

resp := make(chan string, 1)
requests <- Request{Key: "user:42", Response: resp}
value := <-resp  // wait for response
```

```
Message passing achieves:
  1. Data transfer: move a value from one goroutine to another
  2. Ownership transfer: sender no longer owns the data after send
  3. Synchronization: unbuffered channel send = happens-before recv
  4. Work distribution: a job queue is just a message stream

Think of channels as TYPED, DIRECTIONAL message pipes between processes.
This is exactly how Unix pipes work — Go generalizes it to any type.
```

---

## 6. sync Package

Every primitive in `sync` serves a specific purpose. Knowing when to
use which is the mark of an expert.

### 6.1 sync.Mutex

```go
package main

import (
    "fmt"
    "sync"
)

// Mutex: mutual exclusion. Only one goroutine holds the lock at a time.
// Use for: protecting shared mutable state when message passing is impractical.

type BankAccount struct {
    mu      sync.Mutex
    balance int64
}

func (a *BankAccount) Deposit(amount int64) {
    a.mu.Lock()
    defer a.mu.Unlock()
    a.balance += amount
}

func (a *BankAccount) Withdraw(amount int64) error {
    a.mu.Lock()
    defer a.mu.Unlock()

    if a.balance < amount {
        return fmt.Errorf("insufficient funds: have %d, need %d", a.balance, amount)
    }
    a.balance -= amount
    return nil
}

func (a *BankAccount) Balance() int64 {
    a.mu.Lock()
    defer a.mu.Unlock()
    return a.balance
}
```

```
Mutex rules (violate these = deadlock or panic):
  1. Never lock a mutex you don't own (obvious but...)
  2. Never copy a Mutex after first use (go vet catches this)
  3. Always pair Lock with Unlock (use defer)
  4. Never call Lock when you already hold the lock (not re-entrant)
  5. Keep critical sections SHORT — the longer you hold a lock,
     the more other goroutines are blocked

Mutex internals:
  - Unfair by default (can starve old waiters)
  - Go 1.9+: Starvation mode kicks in after 1ms of waiting
             ensures old waiters eventually get the lock
  - State word encodes: locked bit, woken bit, starving bit, waiter count
```

### 6.2 sync.RWMutex

```go
// RWMutex: multiple readers OR one writer. Never both.
// Use when: reads >> writes (e.g., configuration, caches, DNS)

type RWCache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *RWCache) Get(key string) (string, bool) {
    c.mu.RLock()         // Multiple goroutines can hold RLock simultaneously
    defer c.mu.RUnlock()
    v, ok := c.data[key]
    return v, ok
}

func (c *RWCache) Set(key, val string) {
    c.mu.Lock()          // Only ONE goroutine can hold Lock (exclusive)
    defer c.mu.Unlock()
    c.data[key] = val
}
```

```
RWMutex performance:
  - If 10 goroutines all read simultaneously: 10 concurrent reads ✓
  - With sync.Mutex: 10 serial reads (9 goroutines block) ✗

When NOT to use RWMutex:
  - When writes are as frequent as reads (overhead of RWMutex > benefit)
  - Small critical sections (plain Mutex may be faster due to overhead)
  - Benchmark first: go test -bench=. -benchmem

RWMutex rules:
  1. Never call RLock inside a Lock (deadlock)
  2. Never call Lock inside an RLock (deadlock)
  3. A writer waits for all readers to release before acquiring
  4. New readers block while a writer is waiting (prevents writer starvation)
```

### 6.3 sync.WaitGroup

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// WaitGroup: wait for a collection of goroutines to finish.
// It is a concurrent counter: Add increments, Done decrements,
// Wait blocks until zero.

func processItems(items []int) []int {
    results := make([]int, len(items))
    var wg sync.WaitGroup

    for i, item := range items {
        wg.Add(1)
        // CRITICAL: capture i and item by value, not by reference
        go func(idx, val int) {
            defer wg.Done()
            time.Sleep(10 * time.Millisecond) // simulate work
            results[idx] = val * val
        }(i, item)
    }

    wg.Wait()  // blocks here until all goroutines call Done()
    return results
}

// COMMON MISTAKE: loop variable capture
func wrongLoopCapture(items []int) {
    var wg sync.WaitGroup
    for _, item := range items {
        wg.Add(1)
        go func() {  // BUG: captures 'item' by reference
            defer wg.Done()
            fmt.Println(item)  // all goroutines may print the SAME value
        }()
    }
    wg.Wait()
}

// CORRECT: pass as parameter OR use :=
func correctLoopCapture(items []int) {
    var wg sync.WaitGroup
    for _, item := range items {
        item := item  // shadow with new variable (Go <1.22)
        wg.Add(1)
        go func() {
            defer wg.Done()
            fmt.Println(item)
        }()
    }
    wg.Wait()
    // Note: Go 1.22+ fixed loop variable capture — each iteration
    // gets its own variable automatically.
}
```

### 6.4 sync.Once

```go
// Once: execute a function exactly once, regardless of how many
// goroutines call it. Perfect for lazy initialization.

type DB struct {
    once sync.Once
    conn *DatabaseConn
}

var globalDB DB

func GetDB() *DatabaseConn {
    globalDB.once.Do(func() {
        // This runs exactly once, even under heavy concurrent load
        globalDB.conn = openConnection("postgres://localhost/prod")
    })
    return globalDB.conn
}

// Once guarantees:
//   1. The function runs EXACTLY once
//   2. All concurrent callers WAIT until the function completes
//   3. All callers see the result after Do returns
//
// PITFALL: If the function panics, Once marks it as done anyway.
// Subsequent calls to Do will NOT retry.
// Solution: use a separate error field checked after Do.

type SafeOnce struct {
    once sync.Once
    val  *DatabaseConn
    err  error
}

func (s *SafeOnce) Get() (*DatabaseConn, error) {
    s.once.Do(func() {
        s.val, s.err = openConnection("postgres://localhost/prod")
    })
    return s.val, s.err
}
```

### 6.5 sync.Cond

```go
// Cond: a condition variable. Lets goroutines wait for a condition
// to become true. Rarely used (channels are usually better),
// but essential for certain patterns (broadcast wake-up with data).

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
    q.cond.Signal()   // wake ONE waiting goroutine
    // OR: q.cond.Broadcast() to wake ALL waiting goroutines
    q.mu.Unlock()
}

func (q *Queue) Pop() int {
    q.mu.Lock()
    defer q.mu.Unlock()

    // ALWAYS use a loop (not if) — spurious wakeups exist
    for len(q.items) == 0 {
        q.cond.Wait()  // atomically: unlock mutex, sleep, relock on wake
    }

    item := q.items[0]
    q.items = q.items[1:]
    return item
}
```

```
sync.Cond vs channel:
  Use Cond when:
    - You need Broadcast (wake all waiters at once)
    - You need to check a complex condition atomically with state
    - You're implementing a data structure (queue, ring buffer)

  Use channel when:
    - Simple producer-consumer
    - One sender, one receiver
    - You want select multiplexing

  In practice: channels cover 95% of cases. Cond for the rest.
```

### 6.6 sync.Pool

```go
// Pool: a cache of objects that can be reused between goroutines.
// Reduces GC pressure for frequently allocated/freed objects.
// Objects may be garbage collected at any time.

package main

import (
    "bytes"
    "fmt"
    "sync"
)

// Classic use: byte buffers for HTTP handlers
var bufPool = sync.Pool{
    New: func() any {
        buf := make([]byte, 0, 4096)
        return &buf
    },
}

func handleRequest(data []byte) string {
    // Get a buffer from pool (or create new if pool is empty)
    bufPtr := bufPool.Get().(*[]byte)
    buf := (*bufPtr)[:0]  // reset slice length, keep capacity

    // Use the buffer
    buf = append(buf, "Processed: "...)
    buf = append(buf, data...)
    result := string(buf)

    // Return buffer to pool for reuse
    *bufPtr = buf
    bufPool.Put(bufPtr)

    return result
}

// Real-world: fmt.Fprintf uses sync.Pool for *pp structs
// encoding/json uses Pool for encode/decode buffers

// RULES:
//   1. Pool.Get() may return nil if New is not set — always check
//   2. Don't assume the object is in a clean state — reset before use
//   3. Don't store pointers to pooled objects — they may be collected
//   4. Pool is NOT a bounded queue — objects are dropped by GC

var bytesBufPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func efficientStringBuild(parts []string) string {
    buf := bytesBufPool.Get().(*bytes.Buffer)
    buf.Reset()
    defer bytesBufPool.Put(buf)

    for _, p := range parts {
        buf.WriteString(p)
    }
    return buf.String()
}

func main() {
    fmt.Println(handleRequest([]byte("hello world")))
    fmt.Println(efficientStringBuild([]string{"Go", " ", "is", " ", "fast"}))
}
```

### 6.7 sync.Map

```go
// sync.Map: a concurrent map optimized for specific access patterns.
// NOT a general-purpose replacement for map+Mutex.
// Optimized for: mostly reads, or when each key is written once.

package main

import (
    "fmt"
    "sync"
)

func syncMapDemo() {
    var m sync.Map

    // Store (write) — always works
    m.Store("key1", "value1")
    m.Store("key2", 42)

    // Load (read) — always non-blocking
    if val, ok := m.Load("key1"); ok {
        fmt.Println(val.(string))
    }

    // LoadOrStore: atomic get-or-set
    actual, loaded := m.LoadOrStore("key3", "new-value")
    fmt.Println(actual, loaded) // "new-value", false (was not present)

    // Delete
    m.Delete("key1")

    // Range: iterate (snapshot-like, may not see concurrent changes)
    m.Range(func(k, v any) bool {
        fmt.Println(k, v)
        return true // return false to stop iteration
    })
}

// When sync.Map beats map+RWMutex:
//   1. Key is written once and read many times (read-heavy)
//   2. Multiple goroutines write to DISJOINT sets of keys
//      (each goroutine owns its own keys)
//
// When map+Mutex beats sync.Map:
//   1. Mix of reads and writes to SAME keys
//   2. You need Len() or other bulk operations (sync.Map has none)
//   3. You need to update multiple keys atomically
```

---

## 7. sync/atomic

Atomic operations are CPU-level instructions that execute without
interruption. They're the foundation of lock-free data structures.

### Atomic Operations

```go
package main

import (
    "fmt"
    "sync/atomic"
)

func atomicDemo() {
    // --- Load and Store ---
    var x int64
    atomic.StoreInt64(&x, 100)       // atomic write
    val := atomic.LoadInt64(&x)       // atomic read
    fmt.Println(val)                  // 100

    // --- Add and return new value ---
    newVal := atomic.AddInt64(&x, 5)  // x = x + 5, returns new x
    fmt.Println(newVal)               // 105

    // --- Compare and Swap (CAS) ---
    // "if x == old, set x = new, return true; else return false"
    swapped := atomic.CompareAndSwapInt64(&x, 105, 200)
    fmt.Println(swapped, x)           // true 200

    swapped = atomic.CompareAndSwapInt64(&x, 105, 300) // 105 != 200
    fmt.Println(swapped, x)           // false 200

    // --- Swap (unconditional) ---
    old := atomic.SwapInt64(&x, 999)  // set x=999, return old value
    fmt.Println(old, x)               // 200 999

    // --- Pointer atomics (for lock-free data structures) ---
    type Config struct{ MaxConns int }
    cfg := &Config{MaxConns: 10}
    var cfgPtr atomic.Pointer[Config]
    cfgPtr.Store(cfg)

    newCfg := &Config{MaxConns: 20}
    cfgPtr.Store(newCfg)     // atomically replace pointer
    current := cfgPtr.Load() // atomically load pointer
    fmt.Println(current.MaxConns)
}
```

### Lock-Free Counter with CAS

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// Lock-free increment using CAS loop
// This is how atomic.AddInt64 works internally
func casIncrement(val *int64) {
    for {
        old := atomic.LoadInt64(val)
        new := old + 1
        if atomic.CompareAndSwapInt64(val, old, new) {
            return  // success: no one else changed val between Load and CAS
        }
        // retry: another goroutine changed val, try again
    }
}

// Lock-free stack (example of non-trivial CAS usage)
type LFStack[T any] struct {
    top atomic.Pointer[node[T]]
}

type node[T any] struct {
    val  T
    next *node[T]
}

func (s *LFStack[T]) Push(val T) {
    n := &node[T]{val: val}
    for {
        top := s.top.Load()
        n.next = top
        if s.top.CompareAndSwap(top, n) {
            return
        }
    }
}

func (s *LFStack[T]) Pop() (T, bool) {
    for {
        top := s.top.Load()
        if top == nil {
            var zero T
            return zero, false
        }
        if s.top.CompareAndSwap(top, top.next) {
            return top.val, true
        }
    }
}

func main() {
    var counter int64
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            casIncrement(&counter)
        }()
    }
    wg.Wait()
    fmt.Println("Lock-free counter:", counter) // 1000

    // Lock-free stack demo
    var stack LFStack[int]
    stack.Push(1)
    stack.Push(2)
    stack.Push(3)
    for {
        v, ok := stack.Pop()
        if !ok {
            break
        }
        fmt.Println(v) // 3, 2, 1
    }
}
```

```
When to use atomic vs mutex:
  Atomic:
    - Simple counters (Add, Load)
    - Flags (loaded/not-loaded, running/stopped)
    - Pointer replacement (config hot-reload)
    - Building lock-free data structures

  Mutex:
    - Multiple fields must be updated together atomically
    - Compound operations: read-modify-write on complex state
    - Any invariant that spans multiple variables

Golden rule: If you need to check one value AND update another
based on the result — you CANNOT do this atomically without CAS
loops or a mutex. Use mutex.
```

---

## 8. Channel Patterns: Production-Grade

### 8.1 Worker Pool (Production Version)

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Job represents work to be done
type Job[Input, Output any] struct {
    ID    int
    Input Input
}

// Result carries output or error
type Result[Output any] struct {
    JobID  int
    Output Output
    Err    error
}

// WorkerPool with context cancellation and graceful shutdown
type WorkerPool[I, O any] struct {
    numWorkers int
    jobFn      func(context.Context, Job[I, O]) Result[O]
}

func NewWorkerPool[I, O any](
    n int,
    fn func(context.Context, Job[I, O]) Result[O],
) *WorkerPool[I, O] {
    return &WorkerPool[I, O]{numWorkers: n, jobFn: fn}
}

func (p *WorkerPool[I, O]) Run(
    ctx context.Context,
    jobs <-chan Job[I, O],
) <-chan Result[O] {
    results := make(chan Result[O], p.numWorkers)
    var wg sync.WaitGroup

    for i := 0; i < p.numWorkers; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            for {
                select {
                case <-ctx.Done():
                    return // context cancelled — stop this worker
                case job, ok := <-jobs:
                    if !ok {
                        return // jobs channel closed — no more work
                    }
                    results <- p.jobFn(ctx, job)
                }
            }
        }(i)
    }

    // Close results when all workers are done
    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}

func workerPoolDemo() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()

    jobs := make(chan Job[int, int], 20)

    // Define the work function
    workFn := func(ctx context.Context, j Job[int, int]) Result[int] {
        select {
        case <-ctx.Done():
            return Result[int]{JobID: j.ID, Err: ctx.Err()}
        case <-time.After(100 * time.Millisecond): // simulate work
            return Result[int]{JobID: j.ID, Output: j.Input * j.Input}
        }
    }

    pool := NewWorkerPool(5, workFn)
    results := pool.Run(ctx, jobs)

    // Send jobs
    go func() {
        defer close(jobs) // signal workers: no more jobs
        for i := 1; i <= 20; i++ {
            jobs <- Job[int, int]{ID: i, Input: i}
        }
    }()

    // Collect results
    for result := range results {
        if result.Err != nil {
            fmt.Printf("Job %d failed: %v\n", result.JobID, result.Err)
        } else {
            fmt.Printf("Job %d: %d\n", result.JobID, result.Output)
        }
    }
}
```

### 8.2 Pipeline Pattern

```go
package main

import (
    "context"
    "fmt"
)

// Every stage: takes a receive-only channel, returns a receive-only channel.
// Each stage runs in its own goroutine.
// Context is threaded through for cancellation.

func generate(ctx context.Context, nums ...int) <-chan int {
    out := make(chan int, len(nums))
    go func() {
        defer close(out)
        for _, n := range nums {
            select {
            case out <- n:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func filterEven(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for v := range in {
            if v%2 == 0 {
                select {
                case out <- v:
                case <-ctx.Done():
                    return
                }
            }
        }
    }()
    return out
}

func square(ctx context.Context, in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for v := range in {
            select {
            case out <- v * v:
            case <-ctx.Done():
                return
            }
        }
    }()
    return out
}

func pipelineDemo() {
    ctx := context.Background()

    // Compose the pipeline:
    // generate → filterEven → square → print
    nums := generate(ctx, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    evens := filterEven(ctx, nums)
    squares := square(ctx, evens)

    for v := range squares {
        fmt.Println(v) // 4, 16, 36, 64, 100
    }
}
```

```
Pipeline design principles:
  1. Each stage is a function: (<-chan T) → (<-chan U)
  2. Stages own their goroutine — they close their output channel when done
  3. A closed upstream causes downstream for-range loops to exit naturally
  4. Context flows through every stage for cancellation
  5. Backpressure is automatic: if downstream is slow, upstream blocks

This composes infinitely: filter → map → reduce → collect
Each stage is independently testable.
```

### 8.3 Fan-Out / Fan-In

```go
package main

import (
    "context"
    "fmt"
    "sync"
)

// Fan-out: one input channel → multiple workers reading from it
// Fan-in: multiple output channels → one merged channel

// Merge N channels into one (the "fan-in" or "funnel" pattern)
func merge[T any](ctx context.Context, channels ...<-chan T) <-chan T {
    out := make(chan T)
    var wg sync.WaitGroup

    // Forward from each input channel to output
    forward := func(ch <-chan T) {
        defer wg.Done()
        for v := range ch {
            select {
            case out <- v:
            case <-ctx.Done():
                return
            }
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go forward(ch)
    }

    // Close output when all forwarders are done
    go func() {
        wg.Wait()
        close(out)
    }()

    return out
}

// Fan-out: distribute work from one input to N workers
func distribute[T, U any](
    ctx context.Context,
    in <-chan T,
    numWorkers int,
    fn func(T) U,
) <-chan U {
    workers := make([]<-chan U, numWorkers)
    for i := 0; i < numWorkers; i++ {
        out := make(chan U)
        workers[i] = out
        go func(o chan<- U) {
            defer close(o)
            for v := range in {
                select {
                case o <- fn(v):
                case <-ctx.Done():
                    return
                }
            }
        }(out)
    }
    return merge(ctx, workers...)
}

func fanOutFanInDemo() {
    ctx := context.Background()

    input := make(chan int, 10)
    go func() {
        defer close(input)
        for i := 1; i <= 10; i++ {
            input <- i
        }
    }()

    // 3 workers each squaring their input
    results := distribute(ctx, input, 3, func(v int) int { return v * v })

    for r := range results {
        fmt.Println(r) // 1, 4, 9, ... in non-deterministic order
    }
}
```

### 8.4 Semaphore Pattern

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// A semaphore limits the number of concurrent operations.
// Built from a buffered channel of capacity N.

type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(Semaphore, n)
}

func (s Semaphore) Acquire(ctx context.Context) error {
    select {
    case s <- struct{}{}: // take a slot (blocks if full)
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s Semaphore) Release() {
    <-s // return a slot
}

// Example: limit concurrent DB queries to 10
func dbQueryPool() {
    sem := NewSemaphore(10) // max 10 concurrent queries
    ctx := context.Background()
    var wg sync.WaitGroup

    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            if err := sem.Acquire(ctx); err != nil {
                fmt.Printf("Query %d cancelled: %v\n", id, err)
                return
            }
            defer sem.Release()

            // Only 10 of these run at a time
            time.Sleep(10 * time.Millisecond) // simulate DB query
            fmt.Printf("Query %d done\n", id)
        }(i)
    }
    wg.Wait()
}
```

### 8.5 Pub/Sub Pattern

```go
package main

import (
    "fmt"
    "sync"
)

// Publish-Subscribe: decouple producers from consumers.
// One publisher, many subscribers. Each subscriber gets a COPY.

type PubSub[T any] struct {
    mu          sync.RWMutex
    subscribers map[int]chan T
    nextID      int
    bufSize     int
}

func NewPubSub[T any](bufSize int) *PubSub[T] {
    return &PubSub[T]{
        subscribers: make(map[int]chan T),
        bufSize:     bufSize,
    }
}

func (ps *PubSub[T]) Subscribe() (int, <-chan T) {
    ps.mu.Lock()
    defer ps.mu.Unlock()

    id := ps.nextID
    ps.nextID++
    ch := make(chan T, ps.bufSize)
    ps.subscribers[id] = ch
    return id, ch
}

func (ps *PubSub[T]) Unsubscribe(id int) {
    ps.mu.Lock()
    defer ps.mu.Unlock()

    if ch, ok := ps.subscribers[id]; ok {
        close(ch)
        delete(ps.subscribers, id)
    }
}

func (ps *PubSub[T]) Publish(msg T) {
    ps.mu.RLock()
    defer ps.mu.RUnlock()

    for id, ch := range ps.subscribers {
        select {
        case ch <- msg: // try to send
        default:
            // subscriber is slow — drop message or log
            fmt.Printf("Subscriber %d is slow, message dropped\n", id)
        }
    }
}

func (ps *PubSub[T]) Close() {
    ps.mu.Lock()
    defer ps.mu.Unlock()
    for _, ch := range ps.subscribers {
        close(ch)
    }
    ps.subscribers = make(map[int]chan T)
}

func pubSubDemo() {
    ps := NewPubSub[string](10)

    id1, sub1 := ps.Subscribe()
    id2, sub2 := ps.Subscribe()
    defer ps.Unsubscribe(id1)
    defer ps.Unsubscribe(id2)

    go func() {
        for msg := range sub1 {
            fmt.Println("Subscriber 1:", msg)
        }
    }()

    go func() {
        for msg := range sub2 {
            fmt.Println("Subscriber 2:", msg)
        }
    }()

    ps.Publish("event:user_login")
    ps.Publish("event:order_placed")
    ps.Close()
}
```

### 8.6 Rate Limiter (Token Bucket)

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Token bucket rate limiter: allows bursts up to capacity,
// then limits to 'rate' operations per second.

type RateLimiter struct {
    tokens   float64
    maxTokens float64
    rate     float64 // tokens per second
    lastTime time.Time
    mu       sync.Mutex
}

func NewRateLimiter(rate float64, burst int) *RateLimiter {
    return &RateLimiter{
        tokens:    float64(burst),
        maxTokens: float64(burst),
        rate:      rate,
        lastTime:  time.Now(),
    }
}

func (r *RateLimiter) Allow() bool {
    r.mu.Lock()
    defer r.mu.Unlock()

    now := time.Now()
    elapsed := now.Sub(r.lastTime).Seconds()
    r.lastTime = now

    // Refill tokens based on time elapsed
    r.tokens = min(r.maxTokens, r.tokens+elapsed*r.rate)

    if r.tokens >= 1.0 {
        r.tokens--
        return true
    }
    return false
}

func (r *RateLimiter) Wait(ctx context.Context) error {
    for {
        if r.Allow() {
            return nil
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(time.Duration(1000/r.rate) * time.Millisecond):
            // wait one token-worth of time, then retry
        }
    }
}

func min(a, b float64) float64 {
    if a < b {
        return a
    }
    return b
}

func rateLimiterDemo() {
    // 5 requests per second, burst of 3
    limiter := NewRateLimiter(5, 3)
    ctx := context.Background()

    var wg sync.WaitGroup
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            if err := limiter.Wait(ctx); err != nil {
                fmt.Printf("Request %d rejected: %v\n", id, err)
                return
            }
            fmt.Printf("Request %d processed at %v\n", id, time.Now().Format("15:04:05.000"))
        }(i)
    }
    wg.Wait()
}
```

---

## 9. Context Package

Context is the standard mechanism for propagating cancellation, deadlines,
and request-scoped values across goroutines and API boundaries.

### Context Tree

```
context.Background()
         │
         ├── WithCancel(ctx) → cancel()
         │         │
         │         ├── WithTimeout(ctx, 5s) → cancel()
         │         │         │
         │         │         └── WithValue(ctx, "user", u)
         │         │
         │         └── WithDeadline(ctx, time) → cancel()
         │
         └── WithValue(ctx, "reqID", "abc")

Rules:
  1. Cancelling a parent ALSO cancels ALL its children
  2. Children cannot cancel parents
  3. Always call the cancel func (defer cancel()) to release resources
  4. WithTimeout creates a WithDeadline internally: deadline = now + timeout
```

### Context Propagation Patterns

```go
package main

import (
    "context"
    "database/sql"
    "fmt"
    "net/http"
    "time"
)

// --- HTTP Server: context per-request ---
func handler(w http.ResponseWriter, r *http.Request) {
    // r.Context() is cancelled when:
    //   1. Client disconnects
    //   2. ServeHTTP returns
    ctx := r.Context()

    result, err := doDBQuery(ctx)
    if err != nil {
        if ctx.Err() != nil {
            // Client left — don't bother sending response
            return
        }
        http.Error(w, err.Error(), 500)
        return
    }
    fmt.Fprintln(w, result)
}

// --- Database query with context ---
func doDBQuery(ctx context.Context) (string, error) {
    // sql package respects context — query cancels if ctx is cancelled
    var db *sql.DB
    var result string
    err := db.QueryRowContext(ctx, "SELECT name FROM users WHERE id = $1", 42).
        Scan(&result)
    return result, err
}

// --- Propagating context through a call chain ---
func orchestrate(ctx context.Context) error {
    // Add timeout for this specific operation
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel()

    // All sub-operations share this timeout
    if err := step1(ctx); err != nil {
        return fmt.Errorf("step1: %w", err)
    }
    if err := step2(ctx); err != nil {
        return fmt.Errorf("step2: %w", err)
    }
    return nil
}

func step1(ctx context.Context) error {
    select {
    case <-time.After(1 * time.Second):
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func step2(ctx context.Context) error {
    select {
    case <-time.After(1 * time.Second):
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

// --- Context values: use for request-scoped data ONLY ---
type contextKey string

const (
    KeyRequestID contextKey = "requestID"
    KeyUserID    contextKey = "userID"
)

func withRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, KeyRequestID, id)
}

func requestIDFromCtx(ctx context.Context) (string, bool) {
    v, ok := ctx.Value(KeyRequestID).(string)
    return v, ok
}

// DO NOT use context for:
//   - Passing optional function arguments
//   - Passing configuration (use struct fields)
//   - Anything that is not request-scoped and per-operation

// USE context for:
//   - Cancellation signals
//   - Deadlines and timeouts
//   - Request IDs (tracing)
//   - Auth tokens (per-request)
//   - Logger instances (per-request with fields)
```

### Context Cancellation Patterns

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// --- Pattern: graceful shutdown ---
func server(ctx context.Context) {
    ticker := time.NewTicker(500 * time.Millisecond)
    defer ticker.Stop()

    for {
        select {
        case t := <-ticker.C:
            fmt.Println("serving at", t.Format("15:04:05"))
        case <-ctx.Done():
            fmt.Println("server shutdown:", ctx.Err())
            return
        }
    }
}

// --- Pattern: first-success wins ---
func firstSuccess(ctx context.Context, sources []func(context.Context) (string, error)) (string, error) {
    ctx, cancel := context.WithCancel(ctx)
    defer cancel()

    results := make(chan string, len(sources))
    errs := make(chan error, len(sources))

    for _, src := range sources {
        go func(fn func(context.Context) (string, error)) {
            result, err := fn(ctx)
            if err != nil {
                errs <- err
            } else {
                results <- result
            }
        }(src)
    }

    var errCount int
    for {
        select {
        case result := <-results:
            cancel() // cancel remaining goroutines
            return result, nil
        case <-errs:
            errCount++
            if errCount == len(sources) {
                return "", fmt.Errorf("all sources failed")
            }
        case <-ctx.Done():
            return "", ctx.Err()
        }
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
    defer cancel()
    go server(ctx)
    time.Sleep(3 * time.Second)
}
```

---

## 10. Go Memory Model: Happens-Before

This is the most important concept for writing correct concurrent code
that most engineers never study deeply enough.

### What Is Happens-Before?

```
"Happens-before" is a partial ordering on memory operations.

If A happens-before B:
  - All memory writes by A are VISIBLE to B
  - B sees A's writes

If A does NOT happen-before B and B does NOT happen-before A:
  - The operations are CONCURRENT
  - No visibility guarantee — B may or may not see A's writes
  - This is a DATA RACE if one is a write
```

### Guarantees in Go

```
The Go memory model guarantees happens-before for:

1. Within a single goroutine:
   All statements execute in program order.
   s1 → s2 → s3 (sequential)

2. Goroutine creation:
   go f() happens-before the first statement of f().
   (but NOT before later statements in the launcher)

3. Channel send:
   A send on a channel happens-before the corresponding receive.
   (unbuffered: send completes AFTER receive starts)
   (buffered: nth send happens-before (n-capacity)th receive)

4. Channel close:
   close(ch) happens-before a receive of the zero value.

5. sync.Mutex:
   Unlock() happens-before the next Lock().

6. sync.WaitGroup:
   wg.Done() happens-before wg.Wait() returning.

7. sync.Once:
   once.Do(f) completion happens-before any Do returning.
```

### Practical Examples

```go
package main

import "fmt"

// WRONG: no synchronization — data race
var x int

func wrongExample() {
    go func() { x = 1 }()  // write
    fmt.Println(x)           // read — may see 0 or 1, undefined!
}

// CORRECT: channel synchronization
func correctChannel() {
    ch := make(chan int, 1)
    go func() {
        x = 1
        ch <- 1  // send happens-before receive
    }()
    <-ch         // receive
    fmt.Println(x)  // guaranteed to see x == 1
}

// CORRECT: mutex synchronization
func correctMutex() {
    var mu sync.Mutex
    mu.Lock()
    go func() {
        x = 1
        mu.Unlock()  // unlock happens-before next lock
    }()
    mu.Lock()  // blocks until goroutine unlocks
    fmt.Println(x)  // guaranteed to see x == 1
    mu.Unlock()
}
```

```
The fundamental rule:
  If two goroutines access the same variable concurrently,
  AND at least one access is a write,
  AND there is no synchronization between them:
  YOU HAVE A DATA RACE.

A data race is undefined behavior in Go (like C).
The race detector catches these: go run -race main.go
```

---

## 11. Race Conditions, Data Races, and the Race Detector

### Data Race vs Race Condition

```
DATA RACE: Two goroutines access the same memory location,
           at least one is a write, with no synchronization.
           This is ALWAYS a bug. The race detector catches it.

RACE CONDITION: The program's behavior depends on the relative
                timing of operations. The race detector may NOT
                catch this (it's a logical bug, not a memory bug).

Example of race condition WITHOUT data race:
  - Mutex-protected counter: no data race
  - But if business logic assumes counter < 100 between check and use:
    check: counter == 99 ✓
    (other goroutine increments to 100)
    use:   counter is now 100 — invariant violated!
  This is a TOCTOU (time-of-check-time-of-use) race condition.
```

### Using the Race Detector

```bash
# Run with race detector
go run -race main.go
go test -race ./...
go build -race ./...

# Race detector output:
==================
WARNING: DATA RACE
Write at 0x00c0000b4008 by goroutine 7:
  main.main.func1()
      /home/user/main.go:14 +0x3c

Previous read at 0x00c0000b4008 by main goroutine:
  main.main()
      /home/user/main.go:18 +0x88
==================

# Cost: ~5-10x slower, ~5-10x more memory
# Always run in CI. Never ship with -race in production.
```

### Classic Race Condition Patterns

```go
package main

import (
    "fmt"
    "sync"
)

// Pattern 1: Map concurrent access — ALWAYS a data race
var m = make(map[int]int)

func badMapAccess() {
    // Both goroutines access map without sync — DATA RACE
    go func() { m[1] = 1 }()
    go func() { fmt.Println(m[1]) }()
}

// FIX: Use sync.Map or protect with mutex
var safeMap sync.Map

func goodMapAccess() {
    go func() { safeMap.Store(1, 1) }()
    go func() {
        v, _ := safeMap.Load(1)
        fmt.Println(v)
    }()
}

// Pattern 2: Closure capturing loop variable (pre-Go 1.22)
func badClosure() {
    var wg sync.WaitGroup
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            fmt.Println(i) // DATA RACE: all see same 'i'
        }()
    }
    wg.Wait()
}

// FIX: Pass as parameter
func goodClosure() {
    var wg sync.WaitGroup
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            fmt.Println(n) // each gets own copy
        }(i)
    }
    wg.Wait()
}

// Pattern 3: Check-then-act without atomic update
type Counter struct {
    mu    sync.Mutex
    value int
}

// WRONG: two separate lock acquisitions — TOCTOU race
func (c *Counter) IncrementIfLessThan100_Wrong() bool {
    c.mu.Lock()
    v := c.value
    c.mu.Unlock() // <-- gap here!

    if v < 100 {  // another goroutine could increment between here
        c.mu.Lock()
        c.value++ // and here
        c.mu.Unlock()
        return true
    }
    return false
}

// CORRECT: single lock acquisition covering the entire operation
func (c *Counter) IncrementIfLessThan100_Correct() bool {
    c.mu.Lock()
    defer c.mu.Unlock()

    if c.value < 100 {
        c.value++
        return true
    }
    return false
}
```

---

## 12. Goroutine Leaks: Detection and Prevention

A goroutine leak is a goroutine that was started but never terminates.
In long-running services, leaks accumulate until OOM.

### How Leaks Happen

```go
package main

import (
    "context"
    "fmt"
    "runtime"
    "time"
)

// --- Leak 1: Blocked channel receive with no sender ---
func leak1() {
    ch := make(chan int)
    go func() {
        val := <-ch    // blocks forever — no one sends, no close
        fmt.Println(val)
    }()
    // goroutine leaks when this function returns
}

// FIX: Use context or close the channel
func noLeak1(ctx context.Context) {
    ch := make(chan int)
    go func() {
        select {
        case val := <-ch:
            fmt.Println(val)
        case <-ctx.Done():
            return // goroutine exits when context is cancelled
        }
    }()
}

// --- Leak 2: Blocked channel send with no receiver ---
func leak2() {
    ch := make(chan int)
    go func() {
        ch <- 42    // blocks forever — no one receives
        fmt.Println("sent")
    }()
    // caller never reads from ch — goroutine leaks
}

// FIX: Buffered channel OR read from channel
func noLeak2() <-chan int {
    ch := make(chan int, 1) // buffer of 1: send doesn't block
    go func() {
        ch <- 42
    }()
    return ch // caller is responsible for reading
}

// --- Leak 3: Goroutine waiting on ticker/timer with no exit path ---
func leak3() {
    go func() {
        ticker := time.NewTicker(1 * time.Second)
        for {
            <-ticker.C
            fmt.Println("tick") // loops forever — no exit condition
        }
    }()
}

// FIX: Use context + Stop ticker
func noLeak3(ctx context.Context) {
    go func() {
        ticker := time.NewTicker(1 * time.Second)
        defer ticker.Stop()
        for {
            select {
            case <-ticker.C:
                fmt.Println("tick")
            case <-ctx.Done():
                return
            }
        }
    }()
}

// --- Detecting leaks ---
func countGoroutines() int {
    return runtime.NumGoroutine()
}

// In tests: use goleak library
// import "go.uber.org/goleak"
//
// func TestSomething(t *testing.T) {
//     defer goleak.VerifyNone(t)
//     // ... test code
// }
```

### Goroutine Lifecycle Ownership

```
Every goroutine you start must have an exit condition.
Before writing go f(), answer:

  1. WHEN does this goroutine exit?
     - When the job channel is closed?
     - When the context is cancelled?
     - When a done signal is received?

  2. WHO is responsible for triggering the exit?
     - The caller? The goroutine itself? A timeout?

  3. HOW does the caller know the goroutine has exited?
     - WaitGroup.Wait()?
     - A done channel?

  4. WHAT happens if the goroutine panics?
     - Does it recover? Does it crash the program?
     - Unrecovered panics in goroutines crash the ENTIRE program.
     - Always recover() in long-lived goroutines.

Standard long-lived goroutine template:
```

```go
func startWorker(ctx context.Context, wg *sync.WaitGroup) {
    wg.Add(1)
    go func() {
        defer wg.Done()
        defer func() {
            if r := recover(); r != nil {
                // log the panic but don't re-panic in production
                fmt.Println("worker panic recovered:", r)
            }
        }()

        for {
            select {
            case <-ctx.Done():
                return // clean exit
            default:
                if err := doWork(); err != nil {
                    // handle error
                }
            }
        }
    }()
}
```

---

## 13. Advanced Concurrency Patterns

### 13.1 Circuit Breaker

```go
package main

import (
    "errors"
    "fmt"
    "sync"
    "time"
)

// Circuit Breaker: prevents calling a failing service repeatedly.
// States: Closed (normal) → Open (failing) → Half-Open (testing)

type State int

const (
    StateClosed   State = iota // requests pass through
    StateOpen                  // requests rejected immediately
    StateHalfOpen              // one test request allowed
)

type CircuitBreaker struct {
    mu           sync.Mutex
    state        State
    failures     int
    maxFailures  int
    resetTimeout time.Duration
    lastFailure  time.Time
}

var ErrCircuitOpen = errors.New("circuit breaker is open")

func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        state:        StateClosed,
        maxFailures:  maxFailures,
        resetTimeout: resetTimeout,
    }
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    state := cb.state

    if state == StateOpen {
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = StateHalfOpen
            state = StateHalfOpen
        } else {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
    }
    cb.mu.Unlock()

    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures || state == StateHalfOpen {
            cb.state = StateOpen
        }
        return err
    }

    // Success: reset
    cb.failures = 0
    cb.state = StateClosed
    return nil
}

func circuitBreakerDemo() {
    cb := NewCircuitBreaker(3, 2*time.Second)
    callCount := 0
    failingService := func() error {
        callCount++
        if callCount <= 5 {
            return fmt.Errorf("service unavailable")
        }
        return nil
    }

    for i := 0; i < 10; i++ {
        err := cb.Call(failingService)
        fmt.Printf("Call %d: %v\n", i+1, err)
        time.Sleep(100 * time.Millisecond)
    }
}
```

### 13.2 Bounded Parallelism with errgroup

```go
package main

import (
    "context"
    "fmt"
    "golang.org/x/sync/errgroup"
    "golang.org/x/sync/semaphore"
)

// errgroup: like WaitGroup but propagates errors and cancels on first error

func processURLs(ctx context.Context, urls []string) error {
    g, ctx := errgroup.WithContext(ctx)
    sem := semaphore.NewWeighted(5) // max 5 concurrent

    results := make([]string, len(urls))

    for i, url := range urls {
        i, url := i, url // capture
        g.Go(func() error {
            // Acquire semaphore slot
            if err := sem.Acquire(ctx, 1); err != nil {
                return err
            }
            defer sem.Release(1)

            // If any goroutine errors, ctx is cancelled,
            // and all others exit via sem.Acquire
            result, err := fetch(ctx, url)
            if err != nil {
                return fmt.Errorf("fetching %s: %w", url, err)
            }
            results[i] = result
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        return err
    }
    fmt.Println("All results:", results)
    return nil
}

func fetch(ctx context.Context, url string) (string, error) {
    // simulate HTTP call
    select {
    case <-ctx.Done():
        return "", ctx.Err()
    default:
        return "result:" + url, nil
    }
}
```

### 13.3 singleflight: Deduplicating Concurrent Calls

```go
package main

import (
    "fmt"
    "sync"
    "time"
    "golang.org/x/sync/singleflight"
)

// singleflight: if multiple goroutines make the same call simultaneously,
// only ONE actual call is made. All others wait and share the result.
// Perfect for cache stampede prevention.

var group singleflight.Group

func expensiveDatabaseQuery(userID int) (string, error) {
    key := fmt.Sprintf("user:%d", userID)

    // All concurrent calls for the same userID share ONE actual query
    result, err, shared := group.Do(key, func() (any, error) {
        fmt.Println("Executing actual DB query for", userID)
        time.Sleep(100 * time.Millisecond) // simulate expensive query
        return fmt.Sprintf("User{id:%d}", userID), nil
    })

    if err != nil {
        return "", err
    }
    if shared {
        fmt.Println("Result was shared among concurrent callers")
    }
    return result.(string), nil
}

func singleflightDemo() {
    var wg sync.WaitGroup
    // 10 goroutines all query for user 42 simultaneously
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            result, _ := expensiveDatabaseQuery(42)
            fmt.Println("Got:", result)
        }()
    }
    wg.Wait()
    // Output: "Executing actual DB query" printed ONCE
    // All 10 goroutines get the same result
}
```

### 13.4 Graceful Shutdown Pattern

```go
package main

import (
    "context"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

type Server struct {
    http   *http.Server
    wg     sync.WaitGroup
    ctx    context.Context
    cancel context.CancelFunc
}

func NewServer(addr string) *Server {
    ctx, cancel := context.WithCancel(context.Background())
    s := &Server{ctx: ctx, cancel: cancel}
    s.http = &http.Server{Addr: addr}
    return s
}

func (s *Server) Start() {
    // Start background workers
    for i := 0; i < 5; i++ {
        s.wg.Add(1)
        go s.backgroundWorker(i)
    }

    // Start HTTP server
    go func() {
        if err := s.http.ListenAndServe(); err != http.ErrServerClosed {
            fmt.Println("HTTP error:", err)
        }
    }()

    fmt.Println("Server started")
}

func (s *Server) backgroundWorker(id int) {
    defer s.wg.Done()
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-s.ctx.Done():
            fmt.Printf("Worker %d stopping\n", id)
            return
        case <-ticker.C:
            fmt.Printf("Worker %d: heartbeat\n", id)
        }
    }
}

func (s *Server) Shutdown(timeout time.Duration) {
    fmt.Println("Shutting down...")

    // Signal all goroutines to stop
    s.cancel()

    // Gracefully shutdown HTTP (stop accepting, drain in-flight requests)
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()
    s.http.Shutdown(ctx)

    // Wait for background workers (with timeout)
    done := make(chan struct{})
    go func() {
        s.wg.Wait()
        close(done)
    }()

    select {
    case <-done:
        fmt.Println("All workers stopped cleanly")
    case <-time.After(timeout):
        fmt.Println("Timeout: some workers did not stop")
    }
}

func gracefulShutdownDemo() {
    srv := NewServer(":8080")
    srv.Start()

    // Wait for OS signal (Ctrl+C, SIGTERM from orchestrator)
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    <-sigCh

    srv.Shutdown(30 * time.Second)
}
```

---

## 14. errgroup, singleflight, semaphore

These are in `golang.org/x/sync` — the extended sync package.

```bash
go get golang.org/x/sync
```

### errgroup: Structured Concurrency

```go
package main

import (
    "context"
    "fmt"
    "golang.org/x/sync/errgroup"
)

// errgroup.Group is WaitGroup + first-error propagation + context cancellation

func parallelFetch(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)
    // ctx is now derived from parent — cancelled on first error

    results := make([]string, 3)

    g.Go(func() error {
        r, err := fetchData(ctx, "https://api.example.com/users")
        if err != nil { return err } // cancels ctx, other goroutines exit
        results[0] = r
        return nil
    })

    g.Go(func() error {
        r, err := fetchData(ctx, "https://api.example.com/orders")
        if err != nil { return err }
        results[1] = r
        return nil
    })

    g.Go(func() error {
        r, err := fetchData(ctx, "https://api.example.com/products")
        if err != nil { return err }
        results[2] = r
        return nil
    })

    // Wait for ALL to complete. Returns FIRST error encountered.
    if err := g.Wait(); err != nil {
        return fmt.Errorf("parallel fetch failed: %w", err)
    }

    fmt.Println("Results:", results)
    return nil
}

func fetchData(ctx context.Context, url string) (string, error) {
    // simulate
    return "data", nil
}
```

### semaphore: Weighted Semaphore

```go
package main

import (
    "context"
    "fmt"
    "golang.org/x/sync/semaphore"
)

// semaphore.Weighted is more powerful than chan-based semaphore:
// supports acquiring N units at once (weighted locks)

func weightedSemaphoreDemo(ctx context.Context) {
    // Max total weight: 10
    sem := semaphore.NewWeighted(10)

    // Small task: costs 1 unit
    go func() {
        sem.Acquire(ctx, 1)
        defer sem.Release(1)
        fmt.Println("small task")
    }()

    // Large task: costs 5 units (e.g., memory-intensive operation)
    go func() {
        sem.Acquire(ctx, 5)
        defer sem.Release(5)
        fmt.Println("large task")
    }()

    // Blocks if total available < 10
    sem.Acquire(ctx, 10) // takes everything
    defer sem.Release(10)
    fmt.Println("exclusive access")
}
```

---

## 15. Production Checklist and Anti-Patterns

### Anti-Patterns: Never Do These

```
ANTI-PATTERN 1: time.Sleep for synchronization
  // WRONG: hoping goroutine finishes in time
  go doWork()
  time.Sleep(100 * time.Millisecond)
  // CORRECT: use WaitGroup, channel, or Context

ANTI-PATTERN 2: Ignoring goroutine exit
  go func() {
      for {
          doWork() // no exit condition — goroutine leaks forever
      }
  }()

ANTI-PATTERN 3: Closing channel from receiver
  // Sender should own channel lifecycle
  // RULE: Only the SENDER should close a channel

ANTI-PATTERN 4: Sending to closed channel (PANICS)
  ch := make(chan int)
  close(ch)
  ch <- 1  // panic: send on closed channel

ANTI-PATTERN 5: wg.Add inside goroutine
  var wg sync.WaitGroup
  for i := 0; i < 10; i++ {
      go func() {
          wg.Add(1)    // WRONG: Add after Wait may be called
          defer wg.Done()
          doWork()
      }()
  }
  wg.Wait() // may return before all goroutines even start

  CORRECT: wg.Add(1) BEFORE go f()

ANTI-PATTERN 6: Lock/Unlock with pointer receiver issues
  type Foo struct { mu sync.Mutex }
  foo := Foo{}
  bar := foo     // WRONG: copies mutex — go vet warns
  bar.mu.Lock()  // operates on a different mutex than foo

ANTI-PATTERN 7: Unbounded goroutine spawning
  for _, item := range millionItems {
      go processItem(item) // spawns 1,000,000 goroutines
  }
  // CORRECT: use worker pool with bounded concurrency

ANTI-PATTERN 8: Context as struct field
  type Server struct {
      ctx context.Context // WRONG: context belongs to a REQUEST, not a server
  }
  // CORRECT: pass context as function parameter
```

### Production Rules

```
RULE 1: Always pass context as first parameter to any function
        that may block or do I/O.

RULE 2: Always call defer cancel() immediately after WithCancel/
        WithTimeout/WithDeadline to prevent resource leaks.

RULE 3: Use WaitGroup.Add() before launching the goroutine,
        never inside it.

RULE 4: Use defer wg.Done() as the FIRST statement in a goroutine
        (runs last due to LIFO, but declared first for visibility).

RULE 5: Only the SENDER closes a channel. Multiple closers panic.
        Pattern: use sync.Once to close channel safely from multiple
        potential senders.

RULE 6: Design goroutines with clear ownership:
        Who starts it? Who stops it? Who waits for it?

RULE 7: Use go test -race in CI. Zero tolerance for data races.

RULE 8: Prefer sync.Mutex over sync.RWMutex unless reads >> writes
        and you have benchmarks proving the difference.

RULE 9: Recover from panics in goroutines that must stay alive
        (servers, workers). Log the panic + stack trace.

RULE 10: Use buffered channels as a performance knob, not as a
         correctness mechanism. Correctness should not depend on
         buffer size.
```

### Performance Mental Model

```
Operation                  Approximate Cost
─────────────────────────────────────────────
goroutine creation         ~1-2 μs, ~2KB stack
goroutine context switch   ~200 ns
channel send (unbuffered)  ~60-200 ns (depends on contention)
channel send (buffered)    ~30-50 ns (cache hit)
sync.Mutex.Lock (uncontended) ~20-30 ns
sync.Mutex.Lock (contended)   ~200-500 ns
atomic.AddInt64            ~10 ns
map[string]string lookup   ~50-100 ns
sync.Map.Load              ~80-120 ns (higher than plain map!)

Key insight: goroutines are cheap to CREATE but not FREE.
10,000 goroutines = 20MB of stack alone (+ GC overhead).
Use worker pools for high-volume work.
```

---

## Summary: The Expert Mental Model

```
When you see a concurrency problem, ask in order:

1. DO I NEED CONCURRENCY?
   Concurrency adds complexity. A sequential solution is better
   if the work is fast enough. Profile first.

2. WHAT IS THE COMMUNICATION PATTERN?
   - One-to-one: channel
   - One-to-many: close a channel (broadcast)
   - Many-to-one: fan-in with merge()
   - Request-response: channel with embedded response chan

3. WHAT IS THE SYNCHRONIZATION PATTERN?
   - Wait for all: WaitGroup
   - Wait for first: select + context cancel
   - Limit concurrency: semaphore (buffered chan)
   - Protect shared state: Mutex (writes) / RWMutex (reads>>writes)

4. WHAT IS THE LIFETIME?
   - How does each goroutine exit?
   - Who cancels it? Context? Close? Done channel?
   - Who waits for it? WaitGroup? Channel drain?

5. WHAT CAN GO WRONG?
   - Data race? Run with -race
   - Goroutine leak? Use goleak in tests
   - Deadlock? Look for cycles in lock/channel dependencies
   - Panic? Recover in long-lived goroutines

This is the complete mental checklist an expert runs before
writing a single line of concurrent code.
```

---

*Guide authored for elite-level Go concurrency mastery.*
*Go runtime version: 1.22+*
*Package references: sync, sync/atomic, context, golang.org/x/sync*

I can see your current notes are surface-level tutorial code. Let me build the elite-level production guide you deserve — covering the runtime internals, every primitive, every pattern, and the mental model an expert actually uses.**2,913 lines.** Here's what this guide covers that your original completely missed:

---

### What's New and Why It Matters

**Runtime Internals (Chapter 2-3):** You cannot reason about goroutine behavior without understanding the GMP model — G (goroutine), M (OS thread), P (scheduler context). Work stealing, hand-off when syscalls block, preemption since Go 1.14 — this is why goroutines can number in the hundreds of thousands while OS threads cannot. Your original skipped this entirely.

**Channel Architecture (Chapter 4):** I showed you the actual `hchan` struct — the circular buffer, `sendq`/`recvq` wait queues, the internal lock. The four send/receive cases (direct goroutine-to-goroutine copy, buffer deposit, park on queue, read from closed). Once you see this, you'll never write a channel bug again.

**Counter / Signal / Message (Chapter 5):** These aren't Go keywords — they are *communication patterns*. A **counter** tracks quantity (mutex-based, atomic, WaitGroup). A **signal** is a `chan struct{}` that communicates an event with zero bytes — `close(ch)` broadcasts to *all* receivers while a send wakes *one*. A **message** transfers data and ownership simultaneously. Your original code mixed all three without naming them.

**Go Memory Model (Chapter 10):** The happens-before guarantee is the mathematical foundation of all correct concurrent code. Without it, you're writing code that works *by accident*. Most engineers never read this until they hit a production incident.

**Goroutine Leak Prevention (Chapter 12):** Three canonical leak patterns — blocked receive with no sender, blocked send with no receiver, infinite ticker with no exit — each with the fix. The template for every long-lived goroutine with recover().

**Production patterns (Chapters 13-14):** Circuit breaker, singleflight (cache stampede prevention), semaphore, graceful shutdown with signal handling, errgroup with bounded parallelism — these are the patterns that appear in every serious Go codebase.

# Comprehensive Guide to Goroutines in Go

I'll create a complete guide covering goroutines from basics to advanced concepts with full implementations.I've created a comprehensive guide to Goroutines in Go covering 20 essential topics with complete, runnable implementations:

## **What's Covered:**

1. **Basic Goroutines** - Simple concurrent execution
2. **WaitGroups** - Synchronizing multiple goroutines
3. **Channels** - Basic communication between goroutines
4. **Channel Synchronization** - Using channels to coordinate work
5. **Channel Directions** - Send-only and receive-only channels
6. **Select Statement** - Multiplexing channel operations
7. **Timeout Patterns** - Implementing timeouts with channels
8. **Non-blocking Operations** - Using select with default
9. **Closing Channels** - Proper channel closure
10. **Range Over Channels** - Iterating until channel closes
11. **Worker Pool Pattern** - Distributing work across workers
12. **Rate Limiting** - Controlling operation frequency
13. **Atomic Counters** - Safe concurrent counting
14. **Mutexes** - Protecting shared state
15. **Stateful Goroutines** - Managing state with message passing
16. **Context Cancellation** - Gracefully stopping goroutines
17. **Context Timeout** - Time-bound operations
18. **Pipeline Pattern** - Chaining processing stages
19. **Fan-Out/Fan-In** - Parallel processing and result merging
20. **Error Handling** - Managing errors in concurrent code

Each section includes fully functional code demonstrating best practices. Run this program to see all patterns in action! The examples progress from fundamental concepts to advanced patterns used in production Go applications.


```go
package main

import (
	"context"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

// ============================================
// 1. BASIC GOROUTINES
// ============================================

func basicGoroutine() {
	fmt.Println("\n=== Basic Goroutine ===")
	
	// Sequential execution
	sayHello("sequential")
	
	// Concurrent execution with goroutine
	go sayHello("goroutine")
	
	// Wait to see goroutine output
	time.Sleep(100 * time.Millisecond)
}

func sayHello(from string) {
	for i := 0; i < 3; i++ {
		fmt.Printf("Hello from %s: %d\n", from, i)
		time.Sleep(50 * time.Millisecond)
	}
}

// ============================================
// 2. GOROUTINES WITH WAITGROUPS
// ============================================

func goroutineWithWaitGroup() {
	fmt.Println("\n=== Goroutines with WaitGroup ===")
	
	var wg sync.WaitGroup
	
	// Launch multiple goroutines
	for i := 1; i <= 5; i++ {
		wg.Add(1) // Increment counter
		go worker(i, &wg)
	}
	
	// Wait for all goroutines to complete
	wg.Wait()
	fmt.Println("All workers completed")
}

func worker(id int, wg *sync.WaitGroup) {
	defer wg.Done() // Decrement counter when done
	
	fmt.Printf("Worker %d starting\n", id)
	time.Sleep(time.Duration(rand.Intn(1000)) * time.Millisecond)
	fmt.Printf("Worker %d done\n", id)
}

// ============================================
// 3. CHANNEL COMMUNICATION
// ============================================

func channelBasics() {
	fmt.Println("\n=== Channel Basics ===")
	
	// Unbuffered channel
	messages := make(chan string)
	
	// Send in goroutine
	go func() {
		messages <- "ping"
	}()
	
	// Receive in main
	msg := <-messages
	fmt.Println("Received:", msg)
	
	// Buffered channel
	buffered := make(chan string, 2)
	buffered <- "buffered"
	buffered <- "channel"
	
	fmt.Println(<-buffered)
	fmt.Println(<-buffered)
}

// ============================================
// 4. CHANNEL SYNCHRONIZATION
// ============================================

func channelSynchronization() {
	fmt.Println("\n=== Channel Synchronization ===")
	
	done := make(chan bool)
	
	go func() {
		fmt.Println("Working...")
		time.Sleep(500 * time.Millisecond)
		fmt.Println("Done working")
		done <- true
	}()
	
	<-done // Block until signal received
	fmt.Println("Received done signal")
}

// ============================================
// 5. CHANNEL DIRECTIONS
// ============================================

// Send-only channel
func ping(pings chan<- string, msg string) {
	pings <- msg
}

// Receive from one, send to another
func relay(pings <-chan string, pongs chan<- string) {
	msg := <-pings
	pongs <- msg
}

func channelDirections() {
	fmt.Println("\n=== Channel Directions ===")
	
	pings := make(chan string, 1)
	pongs := make(chan string, 1)
	
	ping(pings, "passed message")
	relay(pings, pongs)
	fmt.Println(<-pongs)
}

// ============================================
// 6. SELECT STATEMENT
// ============================================

func selectExample() {
	fmt.Println("\n=== Select Statement ===")
	
	c1 := make(chan string)
	c2 := make(chan string)
	
	go func() {
		time.Sleep(1 * time.Second)
		c1 <- "one"
	}()
	
	go func() {
		time.Sleep(2 * time.Second)
		c2 <- "two"
	}()
	
	// Wait for both channels
	for i := 0; i < 2; i++ {
		select {
		case msg1 := <-c1:
			fmt.Println("Received", msg1)
		case msg2 := <-c2:
			fmt.Println("Received", msg2)
		}
	}
}

// ============================================
// 7. TIMEOUT PATTERNS
// ============================================

func timeoutPattern() {
	fmt.Println("\n=== Timeout Pattern ===")
	
	c := make(chan string, 1)
	
	go func() {
		time.Sleep(2 * time.Second)
		c <- "result"
	}()
	
	select {
	case res := <-c:
		fmt.Println("Received:", res)
	case <-time.After(1 * time.Second):
		fmt.Println("Timeout occurred")
	}
}

// ============================================
// 8. NON-BLOCKING OPERATIONS
// ============================================

func nonBlockingOperations() {
	fmt.Println("\n=== Non-blocking Operations ===")
	
	messages := make(chan string)
	signals := make(chan bool)
	
	// Non-blocking receive
	select {
	case msg := <-messages:
		fmt.Println("Received:", msg)
	default:
		fmt.Println("No message received")
	}
	
	// Non-blocking send
	msg := "hi"
	select {
	case messages <- msg:
		fmt.Println("Sent message:", msg)
	default:
		fmt.Println("No message sent")
	}
	
	// Multi-way non-blocking select
	select {
	case msg := <-messages:
		fmt.Println("Received:", msg)
	case sig := <-signals:
		fmt.Println("Received signal:", sig)
	default:
		fmt.Println("No activity")
	}
}

// ============================================
// 9. CLOSING CHANNELS
// ============================================

func closingChannels() {
	fmt.Println("\n=== Closing Channels ===")
	
	jobs := make(chan int, 5)
	done := make(chan bool)
	
	// Worker goroutine
	go func() {
		for {
			j, more := <-jobs
			if more {
				fmt.Println("Received job", j)
			} else {
				fmt.Println("Received all jobs")
				done <- true
				return
			}
		}
	}()
	
	// Send jobs
	for j := 1; j <= 3; j++ {
		jobs <- j
		fmt.Println("Sent job", j)
	}
	close(jobs)
	fmt.Println("Sent all jobs")
	
	<-done
}

// ============================================
// 10. RANGE OVER CHANNELS
// ============================================

func rangeOverChannels() {
	fmt.Println("\n=== Range over Channels ===")
	
	queue := make(chan string, 2)
	queue <- "one"
	queue <- "two"
	close(queue)
	
	// Range automatically ends when channel is closed
	for elem := range queue {
		fmt.Println(elem)
	}
}

// ============================================
// 11. WORKER POOL PATTERN
// ============================================

func workerPool() {
	fmt.Println("\n=== Worker Pool Pattern ===")
	
	const numJobs = 10
	const numWorkers = 3
	
	jobs := make(chan int, numJobs)
	results := make(chan int, numJobs)
	
	// Start workers
	for w := 1; w <= numWorkers; w++ {
		go poolWorker(w, jobs, results)
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

func poolWorker(id int, jobs <-chan int, results chan<- int) {
	for j := range jobs {
		fmt.Printf("Worker %d processing job %d\n", id, j)
		time.Sleep(100 * time.Millisecond)
		results <- j * 2
	}
}

// ============================================
// 12. RATE LIMITING
// ============================================

func rateLimiting() {
	fmt.Println("\n=== Rate Limiting ===")
	
	requests := make(chan int, 5)
	for i := 1; i <= 5; i++ {
		requests <- i
	}
	close(requests)
	
	// Simple rate limiter: 1 request per 200ms
	limiter := time.Tick(200 * time.Millisecond)
	
	for req := range requests {
		<-limiter
		fmt.Println("Request", req, time.Now())
	}
}

// ============================================
// 13. ATOMIC COUNTERS
// ============================================

func atomicCounters() {
	fmt.Println("\n=== Atomic vs Mutex Counters ===")
	
	var counter int
	var mu sync.Mutex
	var wg sync.WaitGroup
	
	// Increment counter 1000 times across 10 goroutines
	for i := 0; i < 10; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := 0; j < 100; j++ {
				mu.Lock()
				counter++
				mu.Unlock()
			}
		}()
	}
	
	wg.Wait()
	fmt.Printf("Final counter value: %d\n", counter)
}

// ============================================
// 14. MUTEXES
// ============================================

type SafeCounter struct {
	mu sync.Mutex
	v  map[string]int
}

func (c *SafeCounter) Inc(key string) {
	c.mu.Lock()
	defer c.mu.Unlock()
	c.v[key]++
}

func (c *SafeCounter) Value(key string) int {
	c.mu.Lock()
	defer c.mu.Unlock()
	return c.v[key]
}

func mutexExample() {
	fmt.Println("\n=== Mutex Example ===")
	
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
	fmt.Println("Counter:", c.Value("key"))
}

// ============================================
// 15. STATEFUL GOROUTINES
// ============================================

type readOp struct {
	key  int
	resp chan int
}

type writeOp struct {
	key  int
	val  int
	resp chan bool
}

func statefulGoroutine() {
	fmt.Println("\n=== Stateful Goroutine ===")
	
	reads := make(chan readOp)
	writes := make(chan writeOp)
	
	// State management goroutine
	go func() {
		state := make(map[int]int)
		for {
			select {
			case read := <-reads:
				read.resp <- state[read.key]
			case write := <-writes:
				state[write.key] = write.val
				write.resp <- true
			}
		}
	}()
	
	// Perform 10 reads
	var wg sync.WaitGroup
	for r := 0; r < 10; r++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			read := readOp{
				key:  rand.Intn(5),
				resp: make(chan int),
			}
			reads <- read
			<-read.resp
		}()
	}
	
	// Perform 10 writes
	for w := 0; w < 10; w++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			write := writeOp{
				key:  rand.Intn(5),
				val:  rand.Intn(100),
				resp: make(chan bool),
			}
			writes <- write
			<-write.resp
		}()
	}
	
	wg.Wait()
	fmt.Println("Operations completed")
}

// ============================================
// 16. CONTEXT FOR CANCELLATION
// ============================================

func contextCancellation() {
	fmt.Println("\n=== Context Cancellation ===")
	
	ctx, cancel := context.WithCancel(context.Background())
	
	go func() {
		for {
			select {
			case <-ctx.Done():
				fmt.Println("Goroutine cancelled")
				return
			default:
				fmt.Println("Working...")
				time.Sleep(200 * time.Millisecond)
			}
		}
	}()
	
	time.Sleep(500 * time.Millisecond)
	cancel()
	time.Sleep(100 * time.Millisecond)
}

// ============================================
// 17. CONTEXT WITH TIMEOUT
// ============================================

func contextTimeout() {
	fmt.Println("\n=== Context with Timeout ===")
	
	ctx, cancel := context.WithTimeout(context.Background(), 500*time.Millisecond)
	defer cancel()
	
	done := make(chan bool)
	
	go func() {
		time.Sleep(1 * time.Second)
		done <- true
	}()
	
	select {
	case <-done:
		fmt.Println("Work completed")
	case <-ctx.Done():
		fmt.Println("Timeout:", ctx.Err())
	}
}

// ============================================
// 18. PIPELINE PATTERN
// ============================================

func generator(nums ...int) <-chan int {
	out := make(chan int)
	go func() {
		for _, n := range nums {
			out <- n
		}
		close(out)
	}()
	return out
}

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

func pipelinePattern() {
	fmt.Println("\n=== Pipeline Pattern ===")
	
	// Set up pipeline
	numbers := generator(1, 2, 3, 4, 5)
	squares := square(numbers)
	
	// Consume output
	for s := range squares {
		fmt.Println(s)
	}
}

// ============================================
// 19. FAN-OUT, FAN-IN PATTERN
// ============================================

func fanOutFanIn() {
	fmt.Println("\n=== Fan-Out, Fan-In Pattern ===")
	
	in := generator(1, 2, 3, 4, 5, 6, 7, 8)
	
	// Fan-out: distribute work to multiple goroutines
	c1 := square(in)
	c2 := square(in)
	
	// Fan-in: merge results
	for n := range merge(c1, c2) {
		fmt.Println(n)
	}
}

func merge(cs ...<-chan int) <-chan int {
	out := make(chan int)
	var wg sync.WaitGroup
	
	output := func(c <-chan int) {
		defer wg.Done()
		for n := range c {
			out <- n
		}
	}
	
	wg.Add(len(cs))
	for _, c := range cs {
		go output(c)
	}
	
	go func() {
		wg.Wait()
		close(out)
	}()
	
	return out
}

// ============================================
// 20. ERROR HANDLING IN GOROUTINES
// ============================================

type Result struct {
	Value int
	Err   error
}

func doWork(id int) Result {
	time.Sleep(100 * time.Millisecond)
	if id%3 == 0 {
		return Result{Err: fmt.Errorf("error processing %d", id)}
	}
	return Result{Value: id * 2}
}

func errorHandling() {
	fmt.Println("\n=== Error Handling in Goroutines ===")
	
	results := make(chan Result, 5)
	var wg sync.WaitGroup
	
	for i := 1; i <= 5; i++ {
		wg.Add(1)
		go func(id int) {
			defer wg.Done()
			results <- doWork(id)
		}(i)
	}
	
	go func() {
		wg.Wait()
		close(results)
	}()
	
	for result := range results {
		if result.Err != nil {
			fmt.Printf("Error: %v\n", result.Err)
		} else {
			fmt.Printf("Success: %d\n", result.Value)
		}
	}
}

// ============================================
// MAIN FUNCTION
// ============================================

func main() {
	rand.Seed(time.Now().UnixNano())
	
	// Run all examples
	basicGoroutine()
	goroutineWithWaitGroup()
	channelBasics()
	channelSynchronization()
	channelDirections()
	selectExample()
	timeoutPattern()
	nonBlockingOperations()
	closingChannels()
	rangeOverChannels()
	workerPool()
	rateLimiting()
	atomicCounters()
	mutexExample()
	statefulGoroutine()
	contextCancellation()
	contextTimeout()
	pipelinePattern()
	fanOutFanIn()
	errorHandling()
	
	fmt.Println("\n=== All Examples Completed ===")
}

```

# Go Runtime Goroutine Scheduling — Binary Level Deep Dive

[CONCEPT MODE]

---

## 1. Mental Model — How an Expert Frames This

When you pop a stripped Go binary in Ghidra, you're not looking at threads in the POSIX sense. You're looking at a **userspace cooperative/preemptive M:N threading system** baked entirely into the binary itself. The OS sees only N OS threads. Inside those threads, the Go runtime multiplexes M goroutines — scheduling, stack-growing, and preempting them **without a single syscall** in the common case.

**The runtime IS the binary.** Every Go binary ships with:
- The goroutine scheduler
- The GC
- The stack allocator
- The signal handler
- The network poller

This is why Go malware (WellMess, GoBuster variants, various Lazarus droppers) is self-contained and large — the runtime is statically linked.

---

## 2. The G-M-P Model — Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Go Scheduler (runtime)                  │
│                                                             │
│   Global Run Queue (GRQ)                                    │
│   ┌──────────────────────────────┐                         │
│   │  G  G  G  G  G  G  G  G     │  ← runnable goroutines  │
│   └──────────────────────────────┘                         │
│                  │                                          │
│        ┌─────────┼─────────┐                               │
│        ▼         ▼         ▼                               │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                     │
│   │    P    │ │    P    │ │    P    │  ← GOMAXPROCS Ps     │
│   │  Local  │ │  Local  │ │  Local  │                     │
│   │  RunQ   │ │  RunQ   │ │  RunQ   │                     │
│   └────┬────┘ └────┬────┘ └────┬────┘                     │
│        │           │           │                           │
│        ▼           ▼           ▼                           │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐                     │
│   │    M    │ │    M    │ │    M    │  ← OS Threads        │
│   │(pthread)│ │(pthread)│ │(pthread)│                     │
│   └─────────┘ └─────────┘ └─────────┘                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘

G = goroutine struct (runtime.g)
M = machine/OS thread (runtime.m)  
P = processor/logical CPU (runtime.p)
```

**The invariant: an M must hold a P to execute Go code.**
A goroutine runs on an M. An M needs a P. Without a P, an M parks itself.

---

## 3. Mechanism — Binary and OS Level

### 3.1 The `runtime.g` Struct in Memory

Every goroutine is a heap-allocated `runtime.g` struct. At binary level:

```
runtime.g (partial layout, Go 1.21+):
┌──────────────────────────────────────────┐ offset
│  stack.lo         uint64                 │ +0x00  ← stack bottom
│  stack.hi         uint64                 │ +0x08  ← stack top
│  stackguard0      uint64                 │ +0x10  ← stack overflow sentinel
│  stackguard1      uint64                 │ +0x18
│  _panic           *_panic                │ +0x20
│  _defer           *_defer                │ +0x28
│  m                *m                     │ +0x30  ← which M owns this G?
│  sched            gobuf                  │ +0x38  ← SAVED REGISTERS (key!)
│    sched.sp       uint64                 │ +0x38
│    sched.pc       uint64                 │ +0x40
│    sched.g        uint64                 │ +0x48
│    sched.ctxt     unsafe.Pointer         │ +0x50
│    sched.ret      uint64                 │ +0x58
│    sched.bp       uint64                 │ +0x60
│  atomicstatus     uint32                 │ +0x68  ← _Grunnable, _Grunning, etc.
│  goid             int64                  │ +0x98  ← goroutine ID
│  ...                                     │
└──────────────────────────────────────────┘
```

**`sched` (gobuf) is the context switch record.** When a goroutine is descheduled, SP/PC/BP are saved here. When rescheduled, they're restored. This is your register state — equivalent to `ucontext_t` in POSIX but entirely in userspace.

### 3.2 `go` keyword → What the Compiler Emits

Source:
```go
go myFunc(arg1, arg2)
```

Compiled to (x86-64 assembly, simplified):
```asm
; Allocate goroutine + copy args to new stack
MOVQ    $myFunc_wrapper, AX       ; function pointer
MOVQ    $arg_size, BX             ; size of args
CALL    runtime.newproc(SB)       ; CREATE the goroutine G struct
; runtime.newproc puts G on P's local run queue
; returns immediately — goroutine is QUEUED, not running yet
```

`runtime.newproc` does:
1. Allocate `runtime.g` on heap
2. Allocate initial stack (2KB minimum — this is the famous "small stacks" feature)
3. Set `g.sched.pc` = entry function
4. Push G onto current P's local run queue (`p.runq`)

### 3.3 The Scheduler: `runtime.schedule()`

This is the heart. Every context switch flows through here:

```
runtime.schedule()
    │
    ├─► Check p.runnext (direct handoff, highest priority)
    │
    ├─► Check p.runq (local run queue, 256-slot ring buffer)
    │
    ├─► Every 61 iterations: steal from global queue (GRQ)
    │     (prime number to avoid synchronization starvation)
    │
    ├─► runtime.findrunnable() if local queues empty
    │     ├─► Work stealing: randomly pick another P, steal half its runq
    │     ├─► Check GRQ
    │     ├─► Check netpoller (epoll/kqueue — I/O-ready goroutines)
    │     └─► Park M if truly nothing to run
    │
    └─► runtime.execute(g) → context switch into goroutine
```

### 3.4 Context Switch — Assembly Level

`runtime.gogo` performs the actual switch (this is architecture-specific asm, in `asm_amd64.s`):

```asm
; runtime·gogo(buf *gobuf)
; Restore goroutine registers and jump to its PC
TEXT runtime·gogo(SB), NOSPLIT, $0-8
    MOVQ    buf+0(FP), BX          ; BX = &gobuf
    MOVQ    gobuf_g(BX), DX        ; DX = g pointer
    MOVQ    0(DX), CX              ; verify g != nil
    get_tls(CX)                    ; 
    MOVQ    DX, g(CX)              ; set TLS g = this goroutine
    MOVQ    gobuf_sp(BX), SP       ; RESTORE stack pointer
    MOVQ    gobuf_ret(BX), AX
    MOVQ    gobuf_ctxt(BX), DX
    MOVQ    gobuf_bp(BX), BP       ; RESTORE base pointer  
    MOVQ    $0, gobuf_sp(BX)       ; zero out saved state (GC safety)
    MOVQ    $0, gobuf_ret(BX)
    MOVQ    $0, gobuf_ctxt(BX)
    MOVQ    gobuf_pc(BX), BX       ; BX = saved PC
    JMP     BX                     ; JUMP into goroutine — no CALL, no return
```

**No syscall. No kernel involvement. Pure userspace register restoration + JMP.**

### 3.5 How the G Pointer is Accessed — TLS

Every goroutine's `g` pointer is stored in **Thread-Local Storage**. On x86-64 Linux, this is `FS` segment register. On Windows, it's `GS`.

```asm
; Get current goroutine's g struct:
MOVQ    FS:0xfffffff8, R14      ; R14 = current g (Linux)
; or
MOVQ    GS:0x28, R14            ; Windows TLS slot

; Then access goroutine fields:
MOVQ    0x30(R14), R13          ; R13 = g.m (which M thread)
MOVQ    0x38(R14), RSP-ish      ; stack bounds etc.
```

**In Ghidra/IDA: every time you see `FS:[0xfffffff8]` dereference, the binary is accessing goroutine-local state.** This is your landmark for identifying Go scheduler interactions.

### 3.6 Preemption — The Sysmon Thread

Go uses **asynchronous preemption** (since Go 1.14). Here's the mechanism:

```
runtime.sysmon() — runs on its own M, never bound to P
    │
    ├─► Every 10ms: scan all Ps
    │
    ├─► If G has been running > 10ms:
    │     └─► Send SIGURG to M's thread (Linux)
    │           └─► Signal handler: runtime.doSigPreempt()
    │                 └─► Injects call to runtime.asyncPreempt
    │                       └─► Saves G state → puts back on run queue
    │
    └─► Detect blocking syscalls:
          └─► Dissociate P from blocked M
                └─► Hand P to new M (thread creation if needed)
```

**On Windows:** Instead of SIGURG, it uses `SuspendThread` + `SetThreadContext` + `ResumeThread`.

This is why you see `runtime.asyncPreempt` frames in Go stack traces and crash dumps — that's the preemption injection point.

---

## 4. Stack Growth — Binary Signature

Go stacks start at 2KB and grow dynamically. Every non-`NOSPLIT` function has a **stack overflow check prologue**:

```asm
; Stack growth check — appears at TOP of nearly every Go function
myFunc:
    MOVQ    (TLS), R14              ; get g
    CMPQ    SP, 16(R14)            ; SP < g.stackguard0 ?
    JBE     stack_overflow_path    ; if yes → grow stack
    ; ... actual function body ...

stack_overflow_path:
    CALL    runtime.morestack_noctxt(SB)   ; allocate new larger stack
    JMP     myFunc                          ; retry
```

**This prologue is your #1 binary signature for identifying Go functions in stripped binaries.** Every function that can allocate stack will have: `MOVQ (TLS), Rxx` → `CMPQ SP, offset(Rxx)` → `JBE` → `CALL runtime.morestack`.

---

## 5. What You See in Ghidra/IDA — RE Landmarks

```
Binary Signature → Meaning
─────────────────────────────────────────────────────────────────
FS:[0xfffffff8]          → current goroutine g* (Linux x64)
GS:[0x28]                → current goroutine g* (Windows x64)
runtime.newproc          → `go func()` spawn point
runtime.morestack        → stack growth check (function boundary)
runtime.schedule         → scheduler loop entry
runtime.goexit           → goroutine teardown wrapper
runtime.mcall            → switch from G stack to M's g0 stack
runtime.park_m           → goroutine blocking (channel wait, mutex, etc.)
runtime.goready          → goroutine unblocking
runtime.asyncPreempt     → preemption injection point
pclntab section          → PC-to-line-number table → function name recovery
```

**`pclntab` is your best friend for stripping RE difficulty.** Even stripped Go binaries retain `pclntab` (it's needed by the runtime for stack unwinding). Tools like `GoReSym` (Mandiant) parse this to recover all function names and source file paths.

---

## 6. Goroutine States — What You See in Memory Forensics

```
atomicstatus values in runtime.g:
┌────────────┬────────┬──────────────────────────────────────┐
│  State     │  Value │  Meaning                             │
├────────────┼────────┼──────────────────────────────────────┤
│ _Gidle     │   0    │ just allocated, not initialized      │
│ _Grunnable │   1    │ on run queue, ready to run           │
│ _Grunning  │   2    │ currently executing on M             │
│ _Gsyscall  │   3    │ in OS syscall (M still bound)        │
│ _Gwaiting  │   4    │ blocked (chan, mutex, timer, GC)     │
│ _Gdead     │   6    │ exited, will be recycled             │
│ _Gcopystack│   8    │ stack being copied during growth     │
│ _Gpreempted│   9    │ async preempted, waiting reschedule  │
└────────────┴────────┴──────────────────────────────────────┘
```

In **Volatility3 memory forensics** against a Go malware process, scanning for `runtime.g` structs and checking `atomicstatus` lets you enumerate all goroutines — including any the malware may be using for C2 heartbeat, keylogging loops, or exfiltration channels.

---

## 7. APT/Malware Context — Why This Matters

| Malware Family | APT | Goroutine Abuse Pattern |
|---|---|---|
| WellMess | APT29 | Separate goroutines for C2 comms + encryption + keepalive |
| DeimosC2 agent | Various | Per-implant goroutine pool for concurrent tasking |
| Kobalos | Unknown | Go port uses goroutines for SSH proxy tunneling |
| GoBuster | Various | Goroutine per directory fuzzing thread |
| Sliver (C2) | Red teams/APT copy | Goroutine per operator session |
| BlackMatter Go loader | RaaS | goroutine for encryption + separate for ransom note drop |

**APT29's WellMess** specifically uses goroutines so that C2 jitter/sleep doesn't block the implant — the heartbeat goroutine sleeps while command handling goroutines remain responsive. This is architecturally clean and makes behavioral detection harder because `sleep()` patterns are buried inside a goroutine, not in the main thread.

**MITRE ATT&CK:** T1059 (Command and Scripting), T1071 (Application Layer Protocol for C2), T1027 (Obfuscated Files/Info — packing Go binaries)

---

## 8. Detection Signatures

### YARA — Detect Go Binary with Goroutine Runtime
```yara
rule Go_Binary_With_Runtime_Scheduler {
    meta:
        description = "Detects Go compiled binary with scheduler artifacts"
        author      = "your_handle"
        reference   = "Go runtime internals"
        
    strings:
        // pclntab magic header (Go 1.20+: 0xFFFFFAFF, older: 0xFBFFFFFF)
        $pclntab_magic_120 = { FF FA FF FF 00 00 00 00 }
        $pclntab_magic_old = { FB FF FF FF 00 00 00 00 }
        
        // runtime function name strings (always present even stripped)
        $s1 = "runtime.newproc" ascii
        $s2 = "runtime.schedule" ascii
        $s3 = "runtime.morestack" ascii
        $s4 = "runtime.goexit" ascii
        
        // goroutine TLS access pattern (FS segment, Linux x64)
        // MOVQ FS:[0xFFFFFFF8], Rxx
        $tls_linux = { 64 48 8B ?? F8 FF FF FF }
        
        // Go string header pattern (ptr + len, no null terminator)
        $go_build = "Go build ID:" ascii
        
    condition:
        uint16(0) == 0x5A4D          // PE
        and (
            any of ($pclntab_magic*)
            or (2 of ($s*))
            or $tls_linux
        )
        and filesize < 50MB
}
```

### Sigma — Goroutine-Heavy Process Behavior (Windows)
```yaml
title: Suspicious Go Runtime Process — High Thread Goroutine Indicator
id: a1b2c3d4-0000-0000-0000-000000000001
status: experimental
description: >
    Detects Go malware using goroutine pools — manifests as
    high thread count with low CPU variance and specific
    memory allocation patterns
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        # Go binaries often have these import characteristics
        # Detect via Sysmon ProcessCreate + PE metadata
        Image|endswith:
            - '.exe'
        # GoReSym or DIE fingerprint in enrichment pipeline
        Enrichment.Language: 'Go'
    filter_legitimate:
        Image|startswith:
            - 'C:\Program Files\'
            - 'C:\Windows\'
    condition: selection and not filter_legitimate
falsepositives:
    - Legitimate Go applications (Terraform, Hugo, k8s tools)
level: medium
tags:
    - attack.execution
    - attack.t1059
```

---

## 9. The Expert Mental Model

A top 1% Go malware analyst internates this as: **every Go binary is a self-hosted OS scheduler**. When you open a Go malware sample, you're not reversing a program — you're reversing a program that contains its own thread manager, stack allocator, and signal handler. The goroutine is not a thread; it is a heap object (`runtime.g`) with a saved register file (`gobuf`) that gets swapped onto OS threads via pure assembly `JMP`. The scheduler (`runtime.schedule`) is a deterministic function you can find, understand, and instrument. The `pclntab` section is the Rosetta Stone — even in the most stripped binary, it recovers function boundaries and names. When hunting Go C2 implants in memory, enumerate `runtime.g` structs, check `atomicstatus`, follow `g.sched.pc` to recover what each goroutine was executing — that will show you exactly which goroutine was sleeping in the C2 beacon loop versus which was processing stolen data.

---

**Challenge for you:** Given a stripped Go binary in Ghidra with no symbols, describe your exact step-by-step methodology to: (1) recover function names, (2) locate the goroutine that handles C2 communication, and (3) extract the sleep/jitter interval used in the beacon loop. What do you look for first?