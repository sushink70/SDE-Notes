# Go Channels — The Complete, In-Depth Guide

> **Goal**: Build a deep, accurate mental model of every channel concept in Go — not just syntax, but *why* things work the way they do at the scheduler and memory level. Read this once, understand it completely, and reason about concurrent Go programs with confidence.

---

## Table of Contents

1. [What Is a Channel?](#1-what-is-a-channel)
2. [Channel Internals — How Go Implements Channels](#2-channel-internals)
3. [Unbuffered Channels](#3-unbuffered-channels)
4. [Buffered Channels](#4-buffered-channels)
5. [Directional (One-Way) Channels](#5-directional-channels)
6. [Nil Channels](#6-nil-channels)
7. [Closed Channels](#7-closed-channels)
8. [The select Statement](#8-the-select-statement)
9. [Channel Axioms and Guarantees Table](#9-channel-axioms-table)
10. [Common Patterns and Architectures](#10-common-patterns)
    - Pipeline
    - Fan-Out / Fan-In
    - Done Channel / Cancellation
    - Semaphore
    - Worker Pool
    - Timeout and Deadline
    - Rate Limiter
    - Broadcast
    - Heartbeat
    - Error Channel
11. [Channel vs Mutex — When to Use Which](#11-channel-vs-mutex)
12. [Common Mistakes and Pitfalls](#12-common-mistakes)
13. [Garbage Collection and Channel Lifetime](#13-gc-and-lifetime)
14. [Testing Channels](#14-testing-channels)
15. [Quick Reference Cheat Sheet](#15-quick-reference)

---

## 1. What Is a Channel?

A **channel** is a typed conduit through which goroutines communicate by passing values. It is Go's primary mechanism for synchronisation and data transfer between concurrently-running goroutines.

The philosophy comes from Tony Hoare's **Communicating Sequential Processes (CSP)** — a formal model where independent processes communicate by exchanging messages through named channels rather than sharing memory.

> **Go's mantra**: *"Do not communicate by sharing memory; instead, share memory by communicating."*

This is not merely aesthetic. The channel model:
- Eliminates data races on the communicated data itself
- Makes ownership transfer explicit and visible
- Naturally encodes producer/consumer relationships
- Enables cancellation and backpressure as first-class patterns

### Basic Syntax at a Glance

```go
// Declaration
var ch chan int           // nil channel (zero value)
ch = make(chan int)       // unbuffered channel
ch = make(chan int, 10)   // buffered channel with capacity 10

// Send (blocks until receiver is ready for unbuffered, or buffer has space)
ch <- 42

// Receive (blocks until sender sends)
value := <-ch
value, ok := <-ch        // ok is false if channel is closed and drained

// Close (only the sender should close)
close(ch)

// Directional
var send chan<- int = ch  // send-only
var recv <-chan int = ch  // receive-only
```

---

## 2. Channel Internals

Understanding how Go implements channels internally helps you predict behaviour without guessing.

### The `hchan` Struct (runtime/chan.go)

Every `make(chan T, n)` allocates an `hchan` structure on the heap:

```
┌──────────────────────────────────────────────────────────────┐
│                         hchan                                │
├──────────────────────────────────────────────────────────────┤
│  qcount    uint          — current number of elements in buf │
│  dataqsiz  uint          — capacity (n from make)            │
│  buf       unsafe.Pointer— circular ring buffer              │
│  elemsize  uint16        — sizeof(T)                         │
│  closed    uint32        — 0=open, 1=closed                  │
│  elemtype  *_type        — type descriptor for T             │
│  sendx     uint          — send index into buf               │
│  recvx     uint          — receive index into buf            │
│  recvq     waitq         — list of blocked receivers         │
│  sendq     waitq         — list of blocked senders           │
│  lock      mutex         — protects all fields above         │
└──────────────────────────────────────────────────────────────┘
```

The `waitq` is a doubly-linked list of `sudog` structs. Each `sudog` wraps a goroutine (`g`) that is parked (sleeping) waiting for the channel operation to complete.

### The Three Send/Receive Paths

Every channel operation follows one of three paths:

```
SEND  ch <- v
      │
      ▼
  [lock hchan]
      │
      ├── recvq not empty? ──YES──► copy v directly into waiting goroutine's stack
      │                              unpark that goroutine (runnable immediately)
      │
      ├── buf has space?  ──YES──► copy v into buf[sendx]; sendx++; qcount++
      │
      └── else            ──────► park current goroutine on sendq
                                   (goroutine is blocked until space or receiver)


RECEIVE  v := <-ch
      │
      ▼
  [lock hchan]
      │
      ├── sendq not empty AND buf full?
      │        YES ──► dequeue sender, copy buf[recvx] to v,
      │                copy sender's value into buf, unpark sender
      │
      ├── sendq not empty AND buf empty (unbuffered)?
      │        YES ──► copy sender's value directly to v, unpark sender
      │
      ├── buf has data?   ──YES──► copy buf[recvx] to v; recvx++; qcount--
      │
      └── else            ──────► park current goroutine on recvq
```

### Memory and Copying

Go channels always **copy** the element being sent. This has important consequences:

- Sending a pointer shares the pointed-to memory (only the pointer is copied)
- Sending a value type (int, struct, array) creates a full copy — the sender and receiver own independent copies
- Large structs should be sent as pointers for performance

### The Scheduler Integration

When a goroutine parks on a channel's `sendq` or `recvq`, the Go scheduler (`runtime.gopark`) removes it from the run queue. The parking goroutine stores a pointer back to its `sudog` so that when the complementary operation happens, the runtime can directly unpark it via `runtime.goready`, placing it back on the local run queue of the current P (logical processor).

This is far cheaper than OS thread sleeping — no syscall, no kernel context switch.

---

## 3. Unbuffered Channels

### Definition

An unbuffered channel has **zero capacity**. Created with:

```go
ch := make(chan int)       // capacity = 0
fmt.Println(cap(ch))      // 0
```

### Synchronisation Guarantee

An unbuffered channel enforces a **rendezvous**: the send and receive must happen at the exact same instant from the perspective of the two goroutines involved. Neither the sender nor the receiver can proceed until the other is ready.

```
Goroutine A (sender)          Goroutine B (receiver)
────────────────────          ──────────────────────
...                           ...
ch <- 42  ─────────────────►  v := <-ch
[A blocked until B ready]     [B blocked until A ready]
           HANDSHAKE: value transferred
A continues                   B continues with v = 42
```

This makes unbuffered channels the **strongest synchronisation primitive** in Go. After `ch <- 42` returns, you know for a fact that a receiver has received the value.

### Happens-Before Guarantee

The Go memory model states:

> A send on a channel **happens before** the corresponding receive from that channel completes.
> The completion of a receive from an unbuffered channel **happens before** the send on that channel completes.

In plain terms:
- Everything A did *before* `ch <- 42` is visible to B *after* `v := <-ch`
- No extra `sync.Mutex` or `sync.WaitGroup` is needed for the communicated data

### Implementation Example

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string) // unbuffered

    go func() {
        time.Sleep(1 * time.Second)
        ch <- "hello" // sender parks until receiver is ready
        fmt.Println("sender: sent")
    }()

    fmt.Println("receiver: waiting")
    msg := <-ch // receiver parks until sender sends
    fmt.Println("receiver: got", msg)
    // Output:
    // receiver: waiting
    // receiver: got hello
    // sender: sent          ← sender unblocks AFTER receiver gets the value
}
```

### Use Cases

- Signalling completion (fire a signal, ensure it's picked up)
- Request/response pairs (ping-pong)
- Guaranteeing ordering between goroutines
- Mutex-like mutual exclusion (channel with capacity 1)

---

## 4. Buffered Channels

### Definition

A buffered channel has a **finite capacity ring buffer**. Created with:

```go
ch := make(chan int, 5)    // capacity = 5
fmt.Println(cap(ch))      // 5
fmt.Println(len(ch))      // 0 (current occupancy)
```

### Decoupled Synchronisation

A sender blocks only when the buffer is **full**. A receiver blocks only when the buffer is **empty**. Between those extremes, sender and receiver are decoupled — they can run at different speeds.

```
Buffer capacity = 3

Producer                      Buffer                 Consumer
────────────────              ─────────────────      ────────────────
ch <- A  ──────────────────►  [A][ ][ ]
ch <- B  ──────────────────►  [A][B][ ]
ch <- C  ──────────────────►  [A][B][C]
ch <- D  ─ BLOCKED (full) ─►  [A][B][C]              <-ch ──► A
                              [D][B][C]  ◄── D enters
ch <- D  unblocks ──────────► [D][B][C]
                                                      <-ch ──► B
                                                      <-ch ──► C
                                                      <-ch ──► D
```

### Happens-Before Guarantee

> The k-th receive on a channel with capacity C **happens before** the (k+C)-th send on that channel completes.

This is subtler than the unbuffered case. A send to a buffered channel does NOT guarantee the value has been received — only that it has been placed into the buffer. The consumer may pick it up much later.

### Choosing Buffer Size

The buffer size is a **design decision** that encodes assumptions about production and consumption rates.

| Buffer Size | Effect |
|-------------|--------|
| 0 | Synchronous rendezvous |
| 1 | Allows sender to get ahead by 1; often used to avoid deadlock in single-producer single-consumer |
| N | Absorbs bursts of up to N items; decouples producer/consumer by N items |
| Very large | Hides backpressure; can mask slow consumers; may indicate design smell |

**A common mistake** is picking an arbitrary large buffer to "avoid blocking". This can hide a slow consumer and cause unbounded memory growth. Buffer size should be chosen deliberately.

### Implementation Example

```go
package main

import "fmt"

func main() {
    jobs := make(chan int, 3)

    // Producer: non-blocking as long as buffer has space
    for i := 1; i <= 3; i++ {
        jobs <- i
        fmt.Printf("queued job %d\n", i)
    }
    close(jobs)

    // Consumer: range drains until closed and empty
    for job := range jobs {
        fmt.Printf("processing job %d\n", job)
    }
}
// Output:
// queued job 1
// queued job 2
// queued job 3
// processing job 1
// processing job 2
// processing job 3
```

### Semaphore with Buffered Channel

A buffered channel of capacity N acts as a counting semaphore — limiting N concurrent goroutines:

```go
sem := make(chan struct{}, 3) // max 3 concurrent

for _, task := range tasks {
    sem <- struct{}{} // acquire
    go func(t Task) {
        defer func() { <-sem }() // release
        process(t)
    }(task)
}
```

---

## 5. Directional Channels

### Definition

Go channels can be **restricted** to a single direction at the type level:

```go
chan T        // bidirectional (default)
chan<- T      // send-only  (can only send into it)
<-chan T      // receive-only (can only receive from it)
```

Directional channel types are obtained by converting a bidirectional channel. You cannot convert a directional channel back to bidirectional.

```go
ch := make(chan int)      // bidirectional

var sendOnly chan<- int = ch    // valid: narrowing
var recvOnly <-chan int = ch   // valid: narrowing

// var back chan int = sendOnly  // COMPILE ERROR: cannot convert
```

### Why This Exists

Directional channels allow the **compiler to enforce channel ownership** at the API boundary. A function that receives a `<-chan T` cannot accidentally send or close the channel. A function receiving a `chan<- T` cannot accidentally read from it.

This moves entire classes of bugs from runtime panics to compile-time errors.

### Classic Pattern: Producer / Consumer Separation

```go
package main

import "fmt"

// producer returns a receive-only channel
// callers CAN read from it, CANNOT send or close it
func producer(nums ...int) <-chan int {
    out := make(chan int, len(nums))
    go func() {
        defer close(out) // producer owns the close
        for _, n := range nums {
            out <- n
        }
    }()
    return out // narrows to <-chan int automatically
}

// consumer accepts a receive-only channel
// cannot accidentally send or close
func consumer(in <-chan int) {
    for v := range in {
        fmt.Println(v)
    }
}

func main() {
    ch := producer(1, 2, 3, 4, 5)
    consumer(ch)
}
```

### Directional Channels and close()

You **cannot** call `close()` on a receive-only channel — compile error. This is intentional: only the entity that sends into a channel should close it, because closing signals "no more data", and only the producer knows that.

```go
func badConsumer(in <-chan int) {
    close(in) // COMPILE ERROR: cannot close receive-only channel
}
```

### Internal Representation

Directional channels are **not a different type at runtime**. They have the same `hchan` representation. The direction restriction is purely a compile-time constraint applied by the type system. At runtime, `chan<- int`, `<-chan int`, and `chan int` all have the same underlying `*hchan` pointer.

---

## 6. Nil Channels

### Definition

The **zero value** of any channel type is `nil`.

```go
var ch chan int      // ch == nil
fmt.Println(ch)     // <nil>
```

### Behaviour Table

| Operation | On nil channel | Effect |
|-----------|---------------|--------|
| `ch <- v` | Send | Blocks forever |
| `<-ch` | Receive | Blocks forever |
| `close(ch)` | Close | **panic** |
| `len(ch)` | Len | 0 |
| `cap(ch)` | Cap | 0 |

A nil channel **never becomes ready** in a `select`. This is the key property that makes nil channels extremely useful.

### The Nil Channel select Trick

Because a nil channel blocks forever (is never selected), you can use nil channels to **dynamically disable** cases in a `select` statement:

```go
package main

import "fmt"

func merge(a, b <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for a != nil || b != nil {
            select {
            case v, ok := <-a:
                if !ok {
                    a = nil // disable this case permanently
                    continue
                }
                out <- v
            case v, ok := <-b:
                if !ok {
                    b = nil // disable this case permanently
                    continue
                }
                out <- v
            }
        }
    }()
    return out
}

func source(vals ...int) <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for _, v := range vals {
            ch <- v
        }
    }()
    return ch
}

func main() {
    merged := merge(source(1, 2, 3), source(4, 5))
    for v := range merged {
        fmt.Println(v)
    }
}
```

When `a` is closed, setting `a = nil` means the `case v, ok := <-a:` branch will **never fire again** — it's as if that case was removed. This avoids repeatedly receiving the zero value from a closed channel.

### Common Nil Channel Bugs

```go
// Bug: forgot to make
var results chan int
go func() {
    results <- compute() // blocks forever — deadlock
}()
v := <-results // also blocks — deadlock

// Fix:
results := make(chan int, 1)
```

---

## 7. Closed Channels

### What close() Does

`close(ch)` does **not** destroy the channel or discard buffered data. It sets a flag in `hchan.closed = 1` and **unparks all goroutines** currently blocked on receiving from `ch`. Those goroutines receive the zero value of the channel's element type with `ok = false`.

### Receiving from a Closed Channel

After closing:

```go
ch := make(chan int, 3)
ch <- 10
ch <- 20
ch <- 30
close(ch)

// Buffered values drain normally
v, ok := <-ch    // v=10, ok=true
v, ok = <-ch     // v=20, ok=true
v, ok = <-ch     // v=30, ok=true

// Buffer exhausted, channel closed
v, ok = <-ch     // v=0 (zero value), ok=false
v, ok = <-ch     // v=0, ok=false — same forever
```

**Closed channels return the zero value of the type infinitely** once drained. This will NOT block. Receiving from a closed, drained channel is always instant.

### Sending to a Closed Channel — Panic

```go
ch := make(chan int, 1)
close(ch)
ch <- 1  // panic: send on closed channel
```

This is a runtime panic, not a compile error. The rule is:

> **Only the sender closes the channel. Never close from the receiver side. Never close the same channel twice.**

### The range-over-channel Idiom

```go
for v := range ch {
    // process v
}
// loop exits when ch is closed AND drained
```

This is syntactic sugar for:

```go
for {
    v, ok := <-ch
    if !ok {
        break
    }
    // process v
}
```

### Closing as a Broadcast Signal

Closing a channel is the idiomatic way to **broadcast a signal to many goroutines simultaneously**. When `done` is closed, ALL goroutines blocking on `<-done` are unblocked at once:

```go
done := make(chan struct{})

// Many goroutines listen
for i := 0; i < 100; i++ {
    go func() {
        <-done           // all block here
        fmt.Println("shutting down")
    }()
}

// One signal wakes all 100
close(done)
```

Sending a value to `done` would only wake **one** of the 100. Closing wakes **all** of them. This is the foundation of Go's cancellation patterns.

### Who Should Close?

The canonical rule:

```
┌─────────────────────────────────────────────────────┐
│ The goroutine(s) that SEND into a channel own        │
│ the decision to close it. Receivers must never close │
│ a channel they don't own.                            │
│                                                      │
│ 1 sender  → that sender closes                       │
│ N senders → use a sync.WaitGroup; a coordinator      │
│             goroutine closes after all senders done  │
└─────────────────────────────────────────────────────┘
```

Multi-sender safe close pattern:

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    ch := make(chan int, 10)
    var wg sync.WaitGroup

    // Multiple producers
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            ch <- id * 10
        }(i)
    }

    // Close only after ALL senders are done
    go func() {
        wg.Wait()
        close(ch)
    }()

    for v := range ch {
        fmt.Println(v)
    }
}
```

---

## 8. The select Statement

### What select Does

`select` allows a goroutine to **wait on multiple channel operations simultaneously**. It picks whichever one is ready. If multiple are ready simultaneously, it picks **uniformly at random** (this is specified by the language, not implementation-defined).

### Syntax

```go
select {
case v := <-ch1:
    // ch1 had a value
case ch2 <- x:
    // sent x to ch2
case v, ok := <-ch3:
    // ch3 received; ok=false means closed
default:
    // none of the above were ready (non-blocking select)
}
```

### select with No Cases

```go
select {} // blocks forever — used to keep main alive
```

### select is Not Biased

This is critical to internalise. Given:

```go
select {
case v := <-a:
case v := <-b:
}
```

If **both `a` and `b` are ready at the same time**, Go picks one at random with equal probability (~50/50). This prevents starvation. It also means you should **never assume ordering** in a select.

### Default Case — Non-Blocking Operations

Adding a `default` case makes the `select` non-blocking:

```go
// Non-blocking send
select {
case ch <- value:
    fmt.Println("sent")
default:
    fmt.Println("channel full or no receiver — dropped")
}

// Non-blocking receive
select {
case v := <-ch:
    fmt.Println("got", v)
default:
    fmt.Println("nothing ready")
}
```

This is the only legitimate way to do a non-blocking channel operation in Go.

### Timeout with select and time.After

```go
select {
case result := <-compute():
    fmt.Println("result:", result)
case <-time.After(2 * time.Second):
    fmt.Println("timed out")
}
```

`time.After` returns a `<-chan time.Time` that receives once after the duration. Note: `time.After` creates a new timer that **is not garbage collected** until it fires, even if the `select` case it's in is taken by another case. For high-frequency code, use `time.NewTimer` and `defer timer.Stop()`.

### Proper Timeout with Timer Cleanup

```go
timer := time.NewTimer(2 * time.Second)
defer timer.Stop()

select {
case result := <-compute():
    fmt.Println("result:", result)
case <-timer.C:
    fmt.Println("timed out")
}
```

### select Internals

When `select` executes:

1. All channel expressions in case clauses are evaluated (left to right, top to bottom) — **before** any blocking
2. The runtime locks all channels involved (in a consistent global order to avoid deadlock)
3. It checks which cases are immediately satisfiable
4. If one or more are ready → pick one pseudo-randomly, execute it, unlock
5. If none are ready and no `default` → park the goroutine on ALL channel queues simultaneously
6. When any channel becomes ready → wake the goroutine, execute that case, dequeue from all other channels

This is why `select` properly handles the race: the locking of all channels happens atomically from the goroutine's perspective.

---

## 9. Channel Axioms Table

This table is the foundation of your mental model. Memorise it.

```
┌──────────────────┬────────────────┬──────────────────┬──────────────────┐
│ Operation        │ Nil Channel    │ Open Channel     │ Closed Channel   │
├──────────────────┼────────────────┼──────────────────┼──────────────────┤
│ Send  ch <- v    │ Block forever  │ Block or succeed │ PANIC            │
│ Receive <-ch     │ Block forever  │ Block or succeed │ Return zero, ok=false │
│ Close close(ch)  │ PANIC          │ OK (sets closed) │ PANIC            │
├──────────────────┼────────────────┼──────────────────┼──────────────────┤
│ len(ch)          │ 0              │ Current items    │ Remaining items  │
│ cap(ch)          │ 0              │ Buffer size      │ Buffer size      │
└──────────────────┴────────────────┴──────────────────┴──────────────────┘

Unbuffered-specific:
  Send blocks  → until a receiver is ready
  Recv blocks  → until a sender is ready

Buffered-specific:
  Send blocks  → only when buffer is FULL
  Recv blocks  → only when buffer is EMPTY
```

---

## 10. Common Patterns and Architectures

### 10.1 Pipeline

A pipeline is a series of stages connected by channels. Each stage consumes from an upstream channel, transforms, and produces to a downstream channel.

```
                    PIPELINE ARCHITECTURE

  Source          Stage 1           Stage 2         Sink
┌────────┐       ┌──────────┐      ┌──────────┐    ┌────────┐
│generate│──ch1─►│ double   │──ch2─►│  filter  │─ch3►│ print  │
└────────┘       └──────────┘      └──────────┘    └────────┘
                  (×2 each)        (only evens)
```

```go
package main

import "fmt"

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

func double(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * 2
        }
    }()
    return out
}

func filterEven(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            if n%2 == 0 {
                out <- n
            }
        }
    }()
    return out
}

func main() {
    nums := generate(1, 2, 3, 4, 5)
    doubled := double(nums)
    evens := filterEven(doubled)

    for v := range evens {
        fmt.Println(v) // 2, 4, 6, 8, 10
    }
}
```

**Key property**: each stage runs concurrently. Back-pressure propagates naturally — if the sink is slow, the pipeline stalls at the slowest stage.

---

### 10.2 Fan-Out / Fan-In

**Fan-Out**: distribute work from one channel across multiple goroutines.
**Fan-In**: merge results from multiple goroutines back into one channel.

```
                FAN-OUT / FAN-IN ARCHITECTURE

             ┌──► Worker 1 ──┐
             │               │
  Jobs ──────┼──► Worker 2 ──┼──► Results (merged)
             │               │
             └──► Worker 3 ──┘

  1 input channel → N goroutines → 1 output channel
```

```go
package main

import (
    "fmt"
    "sync"
)

// fanOut spawns n workers, each reading from the same jobs channel
func fanOut(jobs <-chan int, n int) []<-chan int {
    outputs := make([]<-chan int, n)
    for i := 0; i < n; i++ {
        out := make(chan int)
        outputs[i] = out
        go func(out chan<- int) {
            defer close(out)
            for j := range jobs {
                out <- j * j // process: square the number
            }
        }(out)
    }
    return outputs
}

// fanIn merges multiple channels into one
func fanIn(channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup

    output := func(c <-chan int) {
        defer wg.Done()
        for v := range c {
            merged <- v
        }
    }

    wg.Add(len(channels))
    for _, c := range channels {
        go output(c)
    }

    // Close merged when all inputs are done
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

func main() {
    jobs := make(chan int, 10)
    for i := 1; i <= 9; i++ {
        jobs <- i
    }
    close(jobs)

    workers := fanOut(jobs, 3)
    results := fanIn(workers...)

    for r := range results {
        fmt.Println(r)
    }
}
```

---

### 10.3 Done Channel / Cancellation

The done channel pattern propagates cancellation signals through a pipeline. Closing `done` cancels all goroutines that are listening to it.

```
                    CANCELLATION ARCHITECTURE

  main ──close(done)──────────────────────────────────────┐
                                                          │
  Stage 1                Stage 2               Stage N   │
  ┌────────────┐         ┌────────────┐         ┌────────┴───┐
  │select{     │         │select{     │         │select{     │
  │ case <-in  │──out──► │ case <-in  │──out──► │ case <-in  │
  │ case <-done│         │ case <-done│         │ case <-done│
  │}           │         │}           │         │}           │
  └────────────┘         └────────────┘         └────────────┘
  goroutine exits        goroutine exits         goroutine exits
```

```go
package main

import (
    "fmt"
    "time"
)

func producer(done <-chan struct{}) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        i := 0
        for {
            select {
            case <-done:
                fmt.Println("producer: cancelled")
                return
            case out <- i:
                i++
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})
    nums := producer(done)

    // Consume 5 items then cancel
    for i := 0; i < 5; i++ {
        fmt.Println(<-nums)
    }

    close(done) // broadcast cancellation
    time.Sleep(100 * time.Millisecond) // let goroutine clean up
}
```

The `context` package formalises this pattern (`context.WithCancel`, `context.WithTimeout`). Internally, `ctx.Done()` returns a `<-chan struct{}` that is closed when the context is cancelled.

---

### 10.4 Semaphore

A buffered channel of capacity N acts as a counting semaphore, controlling how many goroutines execute a section concurrently.

```
  Semaphore (capacity=3): only 3 goroutines in the critical section at once

  G1 ─► [acquire: sem<-struct{}{}] ─► critical section ─► [release: <-sem]
  G2 ─► [acquire: sem<-struct{}{}] ─► critical section ─► [release: <-sem]
  G3 ─► [acquire: sem<-struct{}{}] ─► critical section ─► [release: <-sem]
  G4 ─► [BLOCKED: buffer full] ────────────────────────────────────────────►
  G5 ─► [BLOCKED: buffer full] ────────────────────────────────────────────►
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    sem := make(chan struct{}, 3) // max 3 concurrent
    var wg sync.WaitGroup

    for i := 1; i <= 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()

            sem <- struct{}{}         // acquire
            defer func() { <-sem }() // release

            // Critical section
            fmt.Printf("goroutine %d running\n", id)
            time.Sleep(500 * time.Millisecond)
        }(i)
    }

    wg.Wait()
}
```

---

### 10.5 Worker Pool

A worker pool maintains a fixed number of goroutines that pull work from a shared jobs channel. This bounds resource usage (goroutines, memory, connections).

```
         WORKER POOL ARCHITECTURE

  ┌──────────────────────────────────────────────────────┐
  │                     Job Queue                        │
  │   [Job1][Job2][Job3][Job4][Job5][Job6][...]          │
  └───────────┬──────────────────────────────────────────┘
              │  jobs channel
    ┌─────────┼──────────┐
    ▼         ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐      results channel
│Worker 1│ │Worker 2│ │Worker 3│  ──────────────────► Collector
└────────┘ └────────┘ └────────┘
 (fixed N workers, goroutine-pool)
```

```go
package main

import (
    "fmt"
    "sync"
)

type Job struct {
    ID    int
    Value int
}

type Result struct {
    JobID  int
    Output int
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
    defer wg.Done()
    for job := range jobs {
        // Simulate work
        output := job.Value * job.Value
        results <- Result{JobID: job.ID, Output: output}
        fmt.Printf("worker %d: processed job %d\n", id, job.ID)
    }
}

func main() {
    const numWorkers = 3
    const numJobs = 10

    jobs := make(chan Job, numJobs)
    results := make(chan Result, numJobs)

    var wg sync.WaitGroup

    // Start fixed pool of workers
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    // Submit jobs
    for j := 1; j <= numJobs; j++ {
        jobs <- Job{ID: j, Value: j}
    }
    close(jobs) // signal workers no more jobs

    // Close results after all workers done
    go func() {
        wg.Wait()
        close(results)
    }()

    // Collect results
    for r := range results {
        fmt.Printf("result: job %d → %d\n", r.JobID, r.Output)
    }
}
```

---

### 10.6 Timeout and Deadline

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func slowOperation(ctx context.Context) (string, error) {
    result := make(chan string, 1)

    go func() {
        time.Sleep(2 * time.Second) // simulate work
        result <- "done"
    }()

    select {
    case r := <-result:
        return r, nil
    case <-ctx.Done():
        return "", ctx.Err() // context.DeadlineExceeded or Canceled
    }
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()

    result, err := slowOperation(ctx)
    if err != nil {
        fmt.Println("error:", err) // context deadline exceeded
        return
    }
    fmt.Println("result:", result)
}
```

---

### 10.7 Rate Limiter

Use a ticker to enforce a maximum operation rate:

```
  TIME ────────────────────────────────────────────────────────►
        │    │    │    │    │    │    │    │    │    │
  tick  1    2    3    4    5    6    7    8    9   10     (every 200ms)
        │    │    │    │    │    │
  req ──1────2────3────4────5────6──  (only 1 req per tick passes)
```

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    requests := make(chan int, 10)
    for i := 1; i <= 5; i++ {
        requests <- i
    }
    close(requests)

    // Allow 1 request per 200ms
    limiter := time.NewTicker(200 * time.Millisecond)
    defer limiter.Stop()

    for req := range requests {
        <-limiter.C // wait for tick
        fmt.Printf("request %d at %v\n", req, time.Now().Format("15:04:05.000"))
    }
}
```

**Burst-capable rate limiter** (token bucket):

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    // Allow bursts of up to 3, refill 1 per 200ms
    limiter := make(chan struct{}, 3)

    // Fill initial burst capacity
    for i := 0; i < 3; i++ {
        limiter <- struct{}{}
    }

    // Refill goroutine
    go func() {
        ticker := time.NewTicker(200 * time.Millisecond)
        for range ticker.C {
            select {
            case limiter <- struct{}{}:
            default: // already full
            }
        }
    }()

    // Use
    for i := 1; i <= 8; i++ {
        <-limiter // consume a token
        fmt.Printf("request %d served at %v\n", i, time.Now().Format("15:04:05.000"))
    }
}
```

---

### 10.8 Broadcast (Pub/Sub)

A single channel send only wakes ONE receiver. To wake MANY, use a struct of subscriber channels or close a `done` channel.

```
           BROADCAST ARCHITECTURE

  Publisher ──► Dispatcher ──► [sub1 chan]──► Subscriber 1
                           └──► [sub2 chan]──► Subscriber 2
                           └──► [sub3 chan]──► Subscriber 3

  Dispatcher fans-out to each subscriber's own channel
```

```go
package main

import (
    "fmt"
    "sync"
)

type Broker[T any] struct {
    mu   sync.RWMutex
    subs map[chan T]struct{}
}

func NewBroker[T any]() *Broker[T] {
    return &Broker[T]{subs: make(map[chan T]struct{})}
}

func (b *Broker[T]) Subscribe() <-chan T {
    ch := make(chan T, 16)
    b.mu.Lock()
    b.subs[ch] = struct{}{}
    b.mu.Unlock()
    return ch
}

func (b *Broker[T]) Unsubscribe(ch <-chan T) {
    b.mu.Lock()
    // find and delete
    for c := range b.subs {
        if c == ch {
            delete(b.subs, c)
            close(c)
            break
        }
    }
    b.mu.Unlock()
}

func (b *Broker[T]) Publish(v T) {
    b.mu.RLock()
    defer b.mu.RUnlock()
    for ch := range b.subs {
        select {
        case ch <- v:
        default: // drop if subscriber is slow
        }
    }
}

func main() {
    broker := NewBroker[string]()

    var wg sync.WaitGroup
    for i := 1; i <= 3; i++ {
        wg.Add(1)
        sub := broker.Subscribe()
        go func(id int, sub <-chan string) {
            defer wg.Done()
            for msg := range sub {
                fmt.Printf("subscriber %d: %s\n", id, msg)
            }
        }(i, sub)
    }

    broker.Publish("hello")
    broker.Publish("world")
}
```

---

### 10.9 Heartbeat

A goroutine signals liveness via a heartbeat channel. The supervisor detects if the goroutine stops sending heartbeats.

```go
package main

import (
    "fmt"
    "time"
)

func worker(done <-chan struct{}) (<-chan struct{}, <-chan int) {
    heartbeat := make(chan struct{}, 1)
    results := make(chan int)

    go func() {
        defer close(results)
        ticker := time.NewTicker(500 * time.Millisecond)
        defer ticker.Stop()
        i := 0
        for {
            select {
            case <-done:
                return
            case <-ticker.C:
                // send heartbeat (non-blocking)
                select {
                case heartbeat <- struct{}{}:
                default:
                }
                results <- i
                i++
            }
        }
    }()

    return heartbeat, results
}

func main() {
    done := make(chan struct{})
    heartbeat, results := worker(done)

    timeout := time.NewTimer(3 * time.Second)
    defer timeout.Stop()

    for {
        select {
        case _, ok := <-heartbeat:
            if !ok {
                fmt.Println("worker dead")
                return
            }
            fmt.Println("heartbeat received")
        case r := <-results:
            fmt.Println("result:", r)
        case <-timeout.C:
            fmt.Println("supervisor: timed out, stopping worker")
            close(done)
            return
        }
    }
}
```

---

### 10.10 Error Channel

Pair a results channel with an error channel, or use a result struct:

```go
package main

import "fmt"

type Result struct {
    Value int
    Err   error
}

func compute(in <-chan int) <-chan Result {
    out := make(chan Result)
    go func() {
        defer close(out)
        for v := range in {
            if v < 0 {
                out <- Result{Err: fmt.Errorf("negative input: %d", v)}
                continue
            }
            out <- Result{Value: v * v}
        }
    }()
    return out
}

func main() {
    in := make(chan int, 5)
    in <- 3
    in <- -1
    in <- 4
    close(in)

    for r := range compute(in) {
        if r.Err != nil {
            fmt.Println("error:", r.Err)
        } else {
            fmt.Println("result:", r.Value)
        }
    }
}
```

---

## 11. Channel vs Mutex

Both channels and mutexes address concurrent access to shared state. Choosing correctly matters.

```
┌─────────────────────────────────────┬──────────────────────────────────────┐
│ Use CHANNELS when…                  │ Use MUTEX when…                      │
├─────────────────────────────────────┼──────────────────────────────────────┤
│ Transferring ownership of data      │ Protecting internal state of a struct│
│ Coordinating goroutines (pipeline)  │ Simple read/write cache              │
│ Distributing work units             │ Performance-critical code (lower     │
│ Signalling events or completion     │ overhead than channel for plain       │
│ One goroutine produces, one consumes│ shared variable)                     │
│ Fan-out / Fan-in patterns           │ Primitive operations (inc/dec counter)│
│ Timeouts and cancellation           │ Locking a set of variables together  │
│ Rate limiting, throttling           │ sync.Map for concurrent map access   │
└─────────────────────────────────────┴──────────────────────────────────────┘
```

### Channel as Mutex (Capacity-1 Buffered Channel)

A buffered channel with capacity 1 can act as a mutex:

```go
mu := make(chan struct{}, 1)

// Lock
mu <- struct{}{}

// Critical section
balance += amount

// Unlock
<-mu
```

This is less efficient than `sync.Mutex` but demonstrates the equivalence. Don't use it in production — use `sync.Mutex` for mutual exclusion and channels for communication.

### The Rob Pike Rule

> Use whichever approach is clearest. Channels are not inherently better than mutexes. Use the right tool.

---

## 12. Common Mistakes and Pitfalls

### 12.1 Goroutine Leak

The most common production issue. A goroutine blocked on a channel send/receive that will never complete — keeping it alive forever.

```go
// BUG: goroutine leaks if no receiver ever reads
func leaky() {
    ch := make(chan int)
    go func() {
        ch <- compute() // if caller returns early, this goroutine is stuck forever
    }()
    // function returns, no one reads from ch, goroutine is leaked
}

// FIX: use buffered channel so goroutine can always send
func fixed() {
    ch := make(chan int, 1) // goroutine can send even if caller is gone
    go func() {
        ch <- compute()
    }()
}

// BETTER FIX: pass a done channel for explicit cancellation
func withCancel(done <-chan struct{}) <-chan int {
    ch := make(chan int, 1)
    go func() {
        select {
        case ch <- compute():
        case <-done:
        }
    }()
    return ch
}
```

### 12.2 Deadlock

All goroutines are asleep — everyone is waiting for someone else.

```go
// DEADLOCK: no goroutine ever sends to ch
func deadlock() {
    ch := make(chan int)
    v := <-ch // blocks forever — fatal error: all goroutines are asleep
    _ = v
}
```

The Go runtime detects global deadlocks (all goroutines blocked) and panics with `fatal error: all goroutines are asleep - deadlock!`. Partial deadlocks (some goroutines alive, some stuck) are NOT detected and are the dangerous kind.

### 12.3 Closing from Wrong End

```go
// PANIC: receiver closes the channel
func consumer(ch chan int) {
    v := <-ch
    close(ch) // BAD — sender may still be sending
    _ = v
}
```

### 12.4 Double Close

```go
ch := make(chan int)
close(ch)
close(ch) // panic: close of closed channel
```

### 12.5 Ignoring ok from Receive

```go
// Infinite loop on closed channel
for {
    v := <-ch   // if ch is closed, this returns 0 forever without blocking
    process(v)
}

// Fix:
for {
    v, ok := <-ch
    if !ok {
        return // channel closed
    }
    process(v)
}

// Idiomatic fix:
for v := range ch {
    process(v)
}
```

### 12.6 Sending to a Full Buffered Channel from the Same Goroutine

```go
ch := make(chan int, 1)
ch <- 1
ch <- 2 // DEADLOCK: buffer full, no other goroutine to receive
```

### 12.7 time.After Memory Leak in Loops

```go
// BUG: each iteration creates a new timer that leaks until it fires
for {
    select {
    case v := <-ch:
        process(v)
    case <-time.After(1 * time.Second): // new timer every iteration!
        fmt.Println("timeout")
    }
}

// FIX: create timer once, reset it
timer := time.NewTimer(1 * time.Second)
for {
    if !timer.Stop() {
        select {
        case <-timer.C:
        default:
        }
    }
    timer.Reset(1 * time.Second)

    select {
    case v := <-ch:
        process(v)
    case <-timer.C:
        fmt.Println("timeout")
    }
}
```

### 12.8 Range over Channel Without close

```go
// DEADLOCK: range blocks waiting for more values that never come
func main() {
    ch := make(chan int, 3)
    ch <- 1
    ch <- 2
    ch <- 3
    // forgot: close(ch)

    for v := range ch { // blocks after 3 values — deadlock
        fmt.Println(v)
    }
}
```

---

## 13. Garbage Collection and Channel Lifetime

A channel is garbage collected only when **no goroutines hold references to it** and **no goroutines are blocked on it**.

Key implications:

1. **A goroutine blocked on a channel prevents GC of the channel** — and the goroutine itself, since the runtime holds a reference via the `sudog` wait queue.

2. **Leaked goroutines cause memory leaks** — not just goroutine stack memory (~2-8KB initial, grows as needed), but also everything they reference.

3. **Closing a channel does not GC it** — it just sets the closed flag. The channel is GC'd when no more references exist.

4. **A channel with items still in its buffer holds references to those items** — preventing GC of anything the items point to.

### Detecting Goroutine Leaks

```go
import "runtime"

func goroutineCount() int {
    return runtime.NumGoroutine()
}

// In tests: use goleak package
import "go.uber.org/goleak"

func TestSomething(t *testing.T) {
    defer goleak.VerifyNone(t) // fails test if goroutines leak
    // ... test code
}
```

---

## 14. Testing Channels

### Testing Asynchronous Channel Communication

```go
package main

import (
    "testing"
    "time"
)

func producer() <-chan int {
    ch := make(chan int)
    go func() {
        defer close(ch)
        for i := 0; i < 3; i++ {
            ch <- i
        }
    }()
    return ch
}

func TestProducer(t *testing.T) {
    ch := producer()
    expected := []int{0, 1, 2}
    var got []int

    // Collect with timeout to avoid hanging test
    for {
        select {
        case v, ok := <-ch:
            if !ok {
                goto done
            }
            got = append(got, v)
        case <-time.After(1 * time.Second):
            t.Fatal("producer timed out")
        }
    }
done:
    if len(got) != len(expected) {
        t.Fatalf("expected %v, got %v", expected, got)
    }
}
```

### Table-Driven Channel Tests

```go
func TestPipeline(t *testing.T) {
    tests := []struct {
        name     string
        input    []int
        expected []int
    }{
        {"empty", []int{}, []int{}},
        {"single", []int{3}, []int{9}},
        {"multiple", []int{1, 2, 3}, []int{1, 4, 9}},
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            in := make(chan int, len(tc.input))
            for _, v := range tc.input {
                in <- v
            }
            close(in)

            out := squarePipeline(in)

            var got []int
            for v := range out {
                got = append(got, v)
            }

            // compare got and tc.expected
            _ = got
        })
    }
}
```

---

## 15. Quick Reference Cheat Sheet

```
╔══════════════════════════════════════════════════════════════════════════╗
║                      GO CHANNELS CHEAT SHEET                             ║
╠══════════════════════════════════════════════════════════════════════════╣
║ CREATION                                                                 ║
║   make(chan T)       — unbuffered (synchronous rendezvous)               ║
║   make(chan T, n)    — buffered capacity n                               ║
║                                                                          ║
║ DIRECTION                                                                ║
║   chan T             — bidirectional                                     ║
║   chan<- T           — send-only (narrowing from chan T)                 ║
║   <-chan T           — receive-only (narrowing from chan T)              ║
║                                                                          ║
║ OPERATIONS                                                               ║
║   ch <- v            — send v (blocks if full/no receiver)              ║
║   v := <-ch          — receive (blocks if empty/no sender)              ║
║   v, ok := <-ch      — receive with closed check                        ║
║   close(ch)          — close (sender only, never twice, never nil)      ║
║   len(ch)            — current items in buffer                          ║
║   cap(ch)            — buffer capacity                                  ║
║                                                                          ║
║ SELECT                                                                   ║
║   select { case ...: ... default: ... }                                 ║
║   default → non-blocking; no default → blocks until one case ready      ║
║   multiple ready cases → chosen uniformly at random                     ║
║   nil channel in case → that case never fires                           ║
║                                                                          ║
║ RANGE                                                                    ║
║   for v := range ch { } — exits when ch closed AND drained              ║
║                                                                          ║
║ BEHAVIOUR SUMMARY                                                        ║
║   nil channel send/recv → block forever                                 ║
║   nil channel close     → panic                                         ║
║   closed channel send   → panic                                         ║
║   closed channel recv   → zero value, ok=false (instant, no block)     ║
║   closed channel close  → panic                                         ║
║                                                                          ║
║ PATTERNS AT A GLANCE                                                     ║
║   Rendezvous         — unbuffered channel                               ║
║   Queue              — buffered channel                                 ║
║   Cancel/Done        — close(done) broadcasts to all                   ║
║   Semaphore          — make(chan struct{}, n) + acquire/release         ║
║   Pipeline           — chain of goroutines via channels                ║
║   Fan-out            — N goroutines read from 1 jobs channel           ║
║   Fan-in             — merge N channels into 1 via goroutine+WaitGroup ║
║   Worker pool        — fixed goroutines + jobs channel + results chan  ║
║   Timeout            — select + time.After/timer.C                     ║
║   Rate limit         — ticker drain pattern                             ║
║                                                                          ║
║ RULES                                                                    ║
║   Only the sender should close a channel                                ║
║   Never close a nil channel                                             ║
║   Never close a channel twice                                           ║
║   Never send to a closed channel                                        ║
║   Always provide a cancellation path (done channel or context)         ║
║   Prefer directional types at function boundaries                      ║
╚══════════════════════════════════════════════════════════════════════════╝
```

---

## Summary — Mental Model

Think of a channel as a **typed, concurrency-safe pipe** with a lock, a ring buffer, and two wait queues:

```
  SENDER ──[lock]──► [ring buffer 0..n] ──[lock]──► RECEIVER
                      ▲               ▲
                  sendq (parked     recvq (parked
                   goroutines)      goroutines)
```

- **Unbuffered (n=0)**: buffer doesn't exist. Send parks until a receiver is ready. Receive parks until a sender is ready. Transfer is a direct goroutine-to-goroutine copy. Maximum synchronisation.

- **Buffered (n>0)**: buffer holds items. Sender and receiver are decoupled while buffer is neither full nor empty. Blocking only at extremes.

- **Directional types**: same pipe, compiler-enforced direction. Ownership and intent made visible and verified at compile time.

- **Nil channel**: a pipe that's disconnected. Blocks all operations. Useful in `select` to dynamically disable cases.

- **Closed channel**: a pipe that's been sealed. Existing data drains normally. New sends panic. Empty-and-closed receives return zero value immediately. Closing is a broadcast to all current receivers.

- **select**: wait on many pipes simultaneously. Picks ready ones at random. `default` makes it non-blocking. Nil cases are never picked. The basis of all Go concurrency orchestration.

Internalise these seven facts and you can reason from first principles about any Go concurrent program.

Here's what's covered in the guide, organized for a strong mental model:

**Foundation & Internals**
- The `hchan` struct with every field explained — what the runtime actually allocates
- The three send/receive paths (direct goroutine handoff, buffer path, parking path)
- How the Go scheduler integrates with channels — why it's cheaper than OS thread sleeping
- Memory copying semantics and when to prefer pointers

**The Four Channel Types**
- **Unbuffered** — synchronous rendezvous, the strongest sync primitive
- **Buffered** — decoupled sender/receiver, ring buffer mechanics, how to choose capacity
- **Directional** (`chan<-`, `<-chan`) — compile-time ownership enforcement, why runtime representation is identical
- **Nil channels** — the select-disabling trick, why they block forever

**Closed Channels**
- What `close()` actually does to `hchan.closed` and the wait queues
- Drain semantics, the `ok` idiom, why closed channels return zero values instantly forever
- Who should close, multi-sender safe close with `sync.WaitGroup`

**select Statement**
- Internal locking mechanism across multiple channels
- Why multiple-ready cases are truly random (language spec, not implementation quirk)
- Non-blocking operations via `default`, `time.After` memory leak and the `NewTimer` fix

**10 Production Patterns** with full Go implementations and ASCII architecture diagrams:
Pipeline, Fan-out/Fan-in, Done/Cancellation, Semaphore, Worker Pool, Timeout/Deadline, Rate Limiter (including token bucket), Broadcast/Pub-Sub, Heartbeat, Error Channel

**Pitfalls section** covers the 8 most common bugs: goroutine leaks, deadlocks, double-close, wrong-end close, ignoring `ok`, `time.After` in loops, and more — each with the fix.