# Go Channels: Buffered vs Unbuffered — A Complete In-Depth Guide

---

## Table of Contents

1. [Prerequisite Concepts — Build the Foundation First](#1-prerequisite-concepts)
2. [What Is a Channel?](#2-what-is-a-channel)
3. [The Internal Anatomy of a Channel](#3-the-internal-anatomy-of-a-channel)
4. [Unbuffered Channels — Deep Dive](#4-unbuffered-channels)
5. [Buffered Channels — Deep Dive](#5-buffered-channels)
6. [Side-by-Side Comparison](#6-side-by-side-comparison)
7. [Channel Lifecycle — Creation, Usage, Closing](#7-channel-lifecycle)
8. [Deadlocks — The Silent Killer](#8-deadlocks)
9. [Channel Directions — Typed Constraints](#9-channel-directions)
10. [The `select` Statement — Multiplexing Channels](#10-the-select-statement)
11. [Ranging Over Channels](#11-ranging-over-channels)
12. [The `nil` Channel — A Special Case](#12-the-nil-channel)
13. [Concurrency Patterns Using Channels](#13-concurrency-patterns)
14. [Performance Characteristics and Trade-offs](#14-performance-characteristics)
15. [The Mental Model — How Experts Think About Channels](#15-the-mental-model)
16. [Common Mistakes and How to Avoid Them](#16-common-mistakes)
17. [Summary Reference Card](#17-summary-reference-card)

---

## 1. Prerequisite Concepts

Before we touch channels, you must understand the building blocks. Every concept below is something channels depend on. Skipping these leads to confusion later.

---

### 1.1 — What Is Concurrency?

**Concurrency** means handling multiple tasks that *overlap in time*. It is not the same as parallelism.

- **Concurrency** = *Dealing with* multiple things at once (structure/design).
- **Parallelism** = *Doing* multiple things at the same exact moment (execution on multiple CPU cores).

Think of a chef who starts boiling water, then chops vegetables while waiting — that is concurrency. Two chefs each doing their own task simultaneously — that is parallelism.

Go supports both. You can write concurrent code that runs in parallel on multiple cores.

---

### 1.2 — What Is a Goroutine?

A **goroutine** is Go's lightweight unit of concurrent execution. Think of it as a *mini-thread* managed by the Go runtime, not the operating system directly.

```
┌─────────────────────────────────────────────────────────┐
│                   Go Runtime Scheduler                  │
│                                                         │
│   goroutine 1 ──►  goroutine 2 ──►  goroutine 3  ...  │
│         ↓                ↓                ↓             │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐         │
│   │  OS      │    │  OS      │    │  OS      │         │
│   │  Thread  │    │  Thread  │    │  Thread  │         │
│   └──────────┘    └──────────┘    └──────────┘         │
└─────────────────────────────────────────────────────────┘
```

You launch a goroutine with the `go` keyword:

```go
go myFunction()   // runs concurrently
```

Key properties:
- Start with ~2KB stack (grows dynamically, unlike OS threads which typically start at 1MB).
- You can spawn millions of goroutines without exhausting memory.
- They are multiplexed over OS threads by the Go scheduler (M:N threading model).

---

### 1.3 — The Problem Goroutines Create

Goroutines run independently. They do not share a return value like regular function calls. So how do they communicate results back? How do they synchronize with each other?

This is *precisely* the problem channels solve.

Go's philosophy (from Tony Hoare's CSP — Communicating Sequential Processes):

```
"Do not communicate by sharing memory;
 instead, share memory by communicating."
                          — Go Team
```

---

### 1.4 — What Is Synchronization?

**Synchronization** means coordinating the timing of goroutines so that one waits for another to reach a certain point before proceeding. Without synchronization, you get **race conditions** — unpredictable behavior when two goroutines access shared data simultaneously.

---

### 1.5 — What Is Blocking?

**Blocking** means a goroutine is paused — it cannot proceed — until some condition is met. A blocked goroutine does not consume CPU. The Go scheduler puts it to sleep and runs other goroutines.

This is critical for understanding channels.

---

## 2. What Is a Channel?

A **channel** is a typed conduit — a pipe — through which goroutines send and receive values. It is the primary mechanism for safe communication and synchronization between goroutines.

```
┌─────────────┐         channel          ┌─────────────┐
│  Goroutine  │  ─────── value ────────► │  Goroutine  │
│     A       │   (send end)  (recv end) │     B       │
└─────────────┘                          └─────────────┘
```

Key facts:
- A channel is a **first-class value** in Go. You can pass it to functions, return it, store it in structs.
- A channel is **typed**: `chan int` carries only integers. `chan string` carries only strings.
- Channels are **reference types** (like maps and slices): when you pass a channel to a function, both the caller and the function refer to the same underlying channel.

### Declaring and Creating a Channel

```go
// Declaration (nil channel — not yet usable)
var ch chan int

// Creation using make (now usable)
ch := make(chan int)          // unbuffered channel
ch := make(chan int, 5)       // buffered channel with capacity 5
```

### Sending and Receiving

```go
ch <- 42        // SEND: put value 42 into channel ch
value := <-ch   // RECEIVE: take a value out of channel ch
<-ch            // RECEIVE and discard the value
```

The arrow `<-` always points in the direction of data flow.

---

## 3. The Internal Anatomy of a Channel

To truly understand buffered vs unbuffered, you need to see what Go actually builds when you call `make(chan T)`.

Internally, Go allocates a `hchan` struct (in the runtime source: `runtime/chan.go`):

```
┌────────────────────────────────────────────────────────────────────┐
│                          hchan struct                              │
│                                                                    │
│  qcount    uint          ← number of elements currently in buffer │
│  dataqsiz  uint          ← capacity of the circular buffer        │
│  buf       unsafe.Pointer ← pointer to circular ring buffer        │
│  elemsize  uint16         ← size of each element                   │
│  closed    uint32         ← 0 = open, 1 = closed                   │
│  elemtype  *_type         ← type information                       │
│  sendx     uint           ← send index (next slot to write)        │
│  recvx     uint           ← receive index (next slot to read)      │
│  recvq     waitq          ← queue of blocked receivers             │
│  sendq     waitq          ← queue of blocked senders               │
│  lock      mutex          ← protects all fields above              │
└────────────────────────────────────────────────────────────────────┘
```

**Key insight**: For an **unbuffered** channel, `dataqsiz = 0` and `buf = nil`. There is no buffer at all. For a **buffered** channel, `dataqsiz = N` and `buf` points to a circular ring buffer of size N.

### The Circular Ring Buffer (for Buffered Channels)

```
Capacity = 4

Initial state:
sendx=0, recvx=0, qcount=0

   [ _ ][ _ ][ _ ][ _ ]
     ↑
   sendx/recvx (both at 0)

After sending 3 values (10, 20, 30):
sendx=3, recvx=0, qcount=3

   [ 10 ][ 20 ][ 30 ][ _ ]
     ↑                  ↑
   recvx              sendx

After receiving 1 value (10 comes out):
sendx=3, recvx=1, qcount=2

   [ 10 ][ 20 ][ 30 ][ _ ]
            ↑          ↑
          recvx       sendx

It wraps around (that's what "circular" means):
After sending 2 more values (40, 50):
sendx=1 (wrapped!), recvx=1, qcount=4

   [ 50 ][ 20 ][ 30 ][ 40 ]
            ↑
          sendx/recvx (buffer is FULL)
```

### The Wait Queues

Both `recvq` and `sendq` are linked lists of **goroutines** that are currently blocked waiting to receive or send respectively.

```
recvq (blocked receivers):
  goroutine_C → goroutine_D → goroutine_E → nil

sendq (blocked senders):
  goroutine_X → goroutine_Y → nil
```

When a goroutine blocks on a channel, the Go runtime parks it in the appropriate queue and suspends its execution. When the condition is met (a value arrives, or space opens up), the runtime wakes up the goroutine from the queue.

---

## 4. Unbuffered Channels

### 4.1 — Definition

An **unbuffered channel** has zero capacity. There is no internal storage for values. A send operation and a receive operation must happen at the *same time* — they rendezvous.

```go
ch := make(chan int)       // dataqsiz = 0
ch := make(chan int, 0)    // same thing, explicit
```

### 4.2 — The Rendezvous Model

This is the defining characteristic. Think of two people passing a physical object hand-to-hand. Both must be present simultaneously. Neither can walk away until the transfer is complete.

```
Timeline:

  Goroutine A (sender)                 Goroutine B (receiver)
  ─────────────────────                ─────────────────────
  ch <- 42                             
  │                                    
  │ [BLOCKED — waiting for receiver]   
  │                                    value := <-ch
  │                                    │
  ├──────────── 42 ────────────────────►│
  │             (transfer happens NOW) │
  │ [UNBLOCKED]                        │ [UNBLOCKED]
  ▼                                    ▼
  continues...                         continues with value=42
```

**The synchronization guarantee**: After `ch <- 42` completes in goroutine A and `value := <-ch` completes in goroutine B, *both* goroutines are guaranteed that the transfer happened. This creates a **happens-before** relationship — a formal guarantee about ordering in concurrent systems.

### 4.3 — Step-by-Step Internal Mechanics

**Case 1: Sender arrives first (no receiver yet)**

```
Step 1: Goroutine A executes ch <- 42
        Runtime checks: is there a blocked receiver in recvq? NO
        Runtime checks: is there buffer space? NO (dataqsiz = 0)

Step 2: Goroutine A is suspended.
        A sudog (lightweight goroutine descriptor) is created holding value 42.
        This sudog is added to sendq.

        sendq: [ A(42) ] → nil
        recvq: nil

Step 3: Goroutine A is descheduled. Go scheduler runs other goroutines.

Step 4: Goroutine B executes value := <-ch
        Runtime checks: is there a blocked sender in sendq? YES — A(42)!

Step 5: Value 42 is copied DIRECTLY from A's sudog into B's stack variable.
        (This is a DIRECT memory copy — no buffer involved.)

Step 6: Goroutine A is woken up and made runnable.
        Both A and B continue.
```

**Case 2: Receiver arrives first (no sender yet)**

```
Step 1: Goroutine B executes value := <-ch
        Runtime checks: is there a blocked sender in sendq? NO
        Runtime checks: is there anything in the buffer? NO

Step 2: Goroutine B is suspended.
        A sudog is created with a pointer to B's stack variable (where value will go).
        This sudog is added to recvq.

        recvq: [ B(*value) ] → nil
        sendq: nil

Step 3: Goroutine A executes ch <- 42
        Runtime checks: is there a blocked receiver in recvq? YES — B!

Step 4: Value 42 is copied DIRECTLY into B's stack variable.

Step 5: Goroutine B is woken up.
        Both continue.
```

### 4.4 — Complete Code Example — Basic Rendezvous

```go
package main

import (
    "fmt"
    "time"
)

func sender(ch chan int) {
    fmt.Println("[Sender] About to send 42...")
    ch <- 42 // BLOCKS until receiver is ready
    fmt.Println("[Sender] Send complete. Continuing.")
}

func receiver(ch chan int) {
    fmt.Println("[Receiver] Sleeping 2 seconds before receiving...")
    time.Sleep(2 * time.Second)
    fmt.Println("[Receiver] About to receive...")
    val := <-ch // sender was waiting — transfer happens NOW
    fmt.Printf("[Receiver] Got: %d\n", val)
}

func main() {
    ch := make(chan int) // unbuffered

    go sender(ch)
    go receiver(ch)

    time.Sleep(3 * time.Second) // give goroutines time to finish
}
```

**Output:**
```
[Sender] About to send 42...
[Receiver] Sleeping 2 seconds before receiving...
[Receiver] About to receive...
[Sender] Send complete. Continuing.
[Receiver] Got: 42
```

Notice: The sender was blocked for 2 full seconds waiting for the receiver. The transfer happened exactly when both were ready.

### 4.5 — Synchronization Guarantee (Why This Matters)

```go
package main

import "fmt"

var data int // shared variable

func setup(done chan struct{}) {
    data = 100          // write to shared variable
    done <- struct{}{} // signal completion
}

func main() {
    done := make(chan struct{}) // unbuffered — guarantees ordering

    go setup(done)

    <-done                    // BLOCKS until setup sends
    fmt.Println(data)         // SAFE to read — guaranteed to see 100
}
```

The unbuffered channel guarantees that `data = 100` *happened before* `<-done` returned. Without this guarantee, you could have a data race.

### 4.6 — The `done` Pattern

A very common Go pattern — using an unbuffered channel to signal completion:

```go
package main

import "fmt"

func worker(id int, done chan struct{}) {
    fmt.Printf("Worker %d: starting\n", id)
    // ... do work ...
    fmt.Printf("Worker %d: done\n", id)
    done <- struct{}{} // send empty struct (zero memory cost signal)
}

func main() {
    done := make(chan struct{})

    go worker(1, done)
    go worker(2, done)

    <-done // wait for first worker to finish
    <-done // wait for second worker to finish

    fmt.Println("Both workers complete")
}
```

`struct{}` is used because it takes **zero bytes** of memory — it's a pure signal with no data payload.

---

## 5. Buffered Channels

### 5.1 — Definition

A **buffered channel** has a capacity greater than zero. It contains an internal circular ring buffer that can hold up to `capacity` values before blocking occurs.

```go
ch := make(chan int, 3)    // buffered, capacity 3
```

### 5.2 — The Mailbox Model

Think of a buffered channel like a physical mailbox with a fixed number of slots. You can drop letters in without waiting for someone to read them — *as long as there's space*. The receiver picks up letters when they're ready — *as long as there's something there*.

```
Capacity = 3

EMPTY:                  PARTIALLY FULL:         FULL:
┌────┬────┬────┐        ┌────┬────┬────┐        ┌────┬────┬────┐
│    │    │    │        │ 10 │ 20 │    │        │ 10 │ 20 │ 30 │
└────┴────┴────┘        └────┴────┴────┘        └────┴────┴────┘
Send: OK (no block)     Send: OK (no block)     Send: BLOCKS
Recv: BLOCKS            Recv: OK (no block)     Recv: OK (no block)
```

### 5.3 — Blocking Rules for Buffered Channels

| Condition | Send Behavior | Receive Behavior |
|-----------|---------------|------------------|
| Buffer empty (qcount = 0) | OK (no block) | **BLOCKS** |
| Buffer partially filled (0 < qcount < cap) | OK (no block) | OK (no block) |
| Buffer full (qcount = cap) | **BLOCKS** | OK (no block) |

This is the critical insight: **decoupling**. The sender and receiver do not need to be simultaneously present — they only block at the extremes (full/empty).

### 5.4 — Step-by-Step Internal Mechanics

**Sending to a non-full buffered channel:**

```
ch := make(chan int, 3)  — buf = [_][_][_], qcount=0, sendx=0, recvx=0

Step 1: Goroutine A executes ch <- 10
        Runtime checks: is there a blocked receiver in recvq? NO
        Runtime checks: is buffer full? NO (qcount=0 < dataqsiz=3)

Step 2: Value 10 is copied into buf[sendx] = buf[0]
        sendx becomes 1, qcount becomes 1

        buf = [10][_][_], qcount=1, sendx=1, recvx=0

Step 3: Goroutine A continues immediately. NO BLOCKING.

Step 4: Goroutine A executes ch <- 20, ch <- 30 (same process)
        buf = [10][20][30], qcount=3, sendx=0 (wrapped!), recvx=0

Step 5: Goroutine A executes ch <- 40
        Runtime checks: is buffer full? YES (qcount=3 == dataqsiz=3)

Step 6: Goroutine A is BLOCKED. sudog(40) added to sendq.
```

**Receiving from a non-empty buffered channel:**

```
State: buf = [10][20][30], qcount=3, sendx=0, recvx=0

Step 1: Goroutine B executes val := <-ch
        Runtime checks: is there a blocked sender in sendq? NO
        Runtime checks: is buffer empty? NO (qcount=3 > 0)

Step 2: Value buf[recvx] = buf[0] = 10 is copied into val.
        recvx becomes 1, qcount becomes 2

        buf = [10][20][30], qcount=2, sendx=0, recvx=1
              (10 is "gone" logically — recvx moved past it)

Step 3: Goroutine B continues with val = 10. NO BLOCKING.
```

**What happens when a blocked sender exists and buffer has space?**

```
State: buf = [10][20][30] FULL, sendq = [A(40)]

Step 1: Goroutine B executes val := <-ch
        Value 10 is read from buf, recvx advances.
        buf = [_][20][30], qcount=2 (space opened!)

Step 2: Runtime checks sendq — A(40) is waiting!
        Value 40 from A's sudog is placed into buf.
        A is woken up.

        buf = [40][20][30], qcount=3

Step 3: Both B (got 10) and A (send completed) continue.
```

### 5.5 — Complete Code Example — Basic Buffered Channel

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 3) // buffered, capacity 3

    // We can send 3 values WITHOUT a receiver goroutine
    // because the buffer absorbs them
    ch <- 10
    ch <- 20
    ch <- 30

    fmt.Println("All 3 sends completed without any goroutine receiving")
    fmt.Println("Buffer length:", len(ch))    // 3
    fmt.Println("Buffer capacity:", cap(ch))  // 3

    // Now receive them back
    fmt.Println(<-ch) // 10 — FIFO order
    fmt.Println(<-ch) // 20
    fmt.Println(<-ch) // 30

    fmt.Println("Buffer length after draining:", len(ch)) // 0
}
```

**Output:**
```
All 3 sends completed without any goroutine receiving
Buffer length: 3
Buffer capacity: 3
10
20
30
Buffer length after draining: 0
```

### 5.6 — Demonstrating the Decoupling

```go
package main

import (
    "fmt"
    "time"
)

func fastProducer(ch chan int) {
    for i := 1; i <= 5; i++ {
        fmt.Printf("[Producer] Sending %d\n", i)
        ch <- i
        fmt.Printf("[Producer] Sent %d — did not block (if buffer had space)\n", i)
    }
    close(ch)
}

func slowConsumer(ch chan int) {
    for val := range ch {
        fmt.Printf("[Consumer] Received %d\n", val)
        time.Sleep(500 * time.Millisecond) // consumer is slow
    }
}

func main() {
    ch := make(chan int, 3) // buffer gives producer room to run ahead

    go fastProducer(ch)
    go slowConsumer(ch)

    time.Sleep(5 * time.Second)
}
```

The producer can run ahead by up to 3 items without waiting for the slow consumer.

### 5.7 — `len` and `cap` on Buffered Channels

```go
ch := make(chan int, 5)

ch <- 1
ch <- 2
ch <- 3

fmt.Println(len(ch))  // 3 — number of items currently in buffer
fmt.Println(cap(ch))  // 5 — maximum capacity
```

> **Warning**: `len(ch)` is a snapshot that can be stale immediately after reading in a concurrent setting. Do not use it for control flow in concurrent code — use it only for diagnostics.

---

## 6. Side-by-Side Comparison

```
┌─────────────────────────────────────────────────────────────────────────┐
│                  UNBUFFERED vs BUFFERED CHANNELS                        │
├─────────────────────────┬───────────────────────────────────────────────┤
│      PROPERTY           │  UNBUFFERED          │  BUFFERED              │
├─────────────────────────┼──────────────────────┼────────────────────────┤
│ Creation                │ make(chan T)          │ make(chan T, N)         │
│ Internal buffer         │ NONE (dataqsiz=0)    │ Circular ring of size N │
│ Send blocks when...     │ Always (no receiver) │ Buffer is FULL         │
│ Receive blocks when...  │ Always (no sender)   │ Buffer is EMPTY        │
│ Synchronization         │ STRONG (rendezvous)  │ WEAK (decoupled)       │
│ Coupling                │ Tight                │ Loose                  │
│ Memory overhead         │ Minimal              │ N * sizeof(T) bytes    │
│ Latency                 │ Higher (must meet)   │ Lower (can go ahead)   │
│ Throughput              │ Lower                │ Higher (in bursts)     │
│ Deadlock risk           │ Higher               │ Still exists           │
│ Mental model            │ Hand-shake / phone   │ Mailbox / pipe         │
│ Happens-before          │ Guaranteed per msg   │ Only at block points   │
└─────────────────────────┴──────────────────────┴────────────────────────┘
```

### Visual Comparison of Blocking Behavior

```
UNBUFFERED (capacity=0):

Goroutine A sends:           Goroutine B receives:
─────────────────            ─────────────────────
ch <- val                    val := <-ch
│                            │
▼ BLOCK immediately          ▼ BLOCK immediately
  (unless receiver ready)      (unless sender ready)

Both unblock only when they MEET.

══════════════════════════════════════════════════════════════

BUFFERED (capacity=3):

State: [ ][ ][ ]   (empty)

A sends 1st value:           B can receive any time:
ch <- val1  → OK (no block)  val := <-ch → OK if len > 0
ch <- val2  → OK (no block)
ch <- val3  → OK (no block)
ch <- val4  → BLOCK! (full)
```

---

## 7. Channel Lifecycle

### 7.1 — Three Phases of a Channel

```
Phase 1: CREATION         Phase 2: USAGE             Phase 3: CLOSING
┌─────────────┐          ┌─────────────────┐         ┌──────────────┐
│ make(chan T) │ ──────►  │ send / receive  │ ──────► │ close(ch)    │
│ or           │          │ operations      │         │              │
│ make(chan T,N│          │                 │         └──────────────┘
└─────────────┘          └─────────────────┘
```

### 7.2 — Closing a Channel

```go
close(ch) // signals no more values will be sent
```

**Rules for closing:**
1. Only the **sender** should close a channel. Never the receiver.
2. **Never** close a channel that has already been closed — this causes a panic.
3. **Never** send to a closed channel — this causes a panic.
4. Receiving from a closed channel is **safe** and returns the zero value after the buffer is drained.

### 7.3 — The Two-Value Receive

```go
val, ok := <-ch
```

- `ok = true`: Channel is open and value is real.
- `ok = false`: Channel is closed and buffer is empty; `val` is zero value.

```go
package main

import "fmt"

func producer(ch chan int) {
    ch <- 1
    ch <- 2
    ch <- 3
    close(ch)
}

func main() {
    ch := make(chan int, 3)
    go producer(ch)

    // Manual drain with ok-idiom
    for {
        val, ok := <-ch
        if !ok {
            fmt.Println("Channel closed!")
            break
        }
        fmt.Println("Received:", val)
    }
}
```

**Output:**
```
Received: 1
Received: 2
Received: 3
Channel closed!
```

### 7.4 — Behavior Table After Close

| Channel State | Send | Receive |
|---------------|------|---------|
| Open, buffer empty | blocks | blocks |
| Open, buffer has data | OK | OK |
| Open, buffer full | blocks | OK |
| **Closed**, buffer has data | **PANIC** | OK (returns real data) |
| **Closed**, buffer empty | **PANIC** | OK (returns zero value, ok=false) |

### 7.5 — Panics: What to Avoid

```go
// PANIC: send on closed channel
ch := make(chan int, 1)
close(ch)
ch <- 1    // PANIC

// PANIC: close of closed channel
ch2 := make(chan int)
close(ch2)
close(ch2) // PANIC

// PANIC: close of nil channel
var ch3 chan int
close(ch3) // PANIC
```

---

## 8. Deadlocks

### 8.1 — What Is a Deadlock?

A **deadlock** occurs when all goroutines are blocked and none can make progress. Go's runtime detects this and kills your program with:

```
fatal error: all goroutines are asleep - deadlock!
```

### 8.2 — Deadlock With Unbuffered Channel

```go
package main

func main() {
    ch := make(chan int)
    ch <- 42 // DEADLOCK: main goroutine blocks, no other goroutine to receive
}
```

```
What happened:

  main goroutine
  ┌──────────────────────┐
  │ ch <- 42             │
  │ [BLOCKED]            │
  │                      │
  │ No other goroutines  │
  │ exist to receive!    │
  └──────────────────────┘
  ↓
  Runtime: all goroutines are asleep — deadlock!
```

**Fix:**

```go
package main

import "fmt"

func main() {
    ch := make(chan int)
    go func() { fmt.Println(<-ch) }() // launch receiver goroutine first
    ch <- 42
}
```

### 8.3 — Deadlock With Buffered Channel

```go
package main

func main() {
    ch := make(chan int, 1)
    ch <- 42     // OK — goes into buffer
    ch <- 100    // DEADLOCK: buffer full, no receiver
}
```

### 8.4 — Circular Deadlock

```go
package main

func main() {
    ch1 := make(chan int)
    ch2 := make(chan int)

    go func() {
        ch1 <- 1    // waits for someone to receive from ch1
        <-ch2       // will never get here
    }()

    go func() {
        ch2 <- 2    // waits for someone to receive from ch2
        <-ch1       // will never get here
    }()

    // Both goroutines block forever waiting for each other
    // This is circular deadlock
    select {} // block main to let goroutines run... into deadlock
}
```

```
Goroutine A: ch1 <- 1  ─────────────────►  Goroutine B needs to receive from ch1
                                            But Goroutine B is blocked on: ch2 <- 2
Goroutine B: ch2 <- 2  ─────────────────►  Goroutine A needs to receive from ch2
                                            But Goroutine A is blocked on: ch1 <- 1

Circular wait → deadlock
```

---

## 9. Channel Directions — Typed Constraints

### 9.1 — Directional Channel Types

You can restrict a channel to be **send-only** or **receive-only** in function signatures. This is a compile-time safety mechanism.

```go
chan T        // bidirectional (can send AND receive)
chan<- T      // send-only (can ONLY send into it)
<-chan T      // receive-only (can ONLY receive from it)
```

The arrow always shows the direction of data flow relative to `chan`.

### 9.2 — Why Use Directional Channels?

It communicates intent and prevents bugs at compile time:

```go
package main

import "fmt"

// producer returns a receive-only channel
// caller can only READ from it — cannot accidentally close or send
func producer(nums []int) <-chan int {
    out := make(chan int, len(nums))
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

// consumer takes a receive-only channel — cannot accidentally send to it
func consumer(in <-chan int) {
    for val := range in {
        fmt.Println("Consumed:", val)
    }
}

func main() {
    ch := producer([]int{1, 2, 3, 4, 5})
    consumer(ch)
}
```

### 9.3 — Conversion Rules

You can convert a bidirectional channel to directional, but NOT vice versa:

```go
ch := make(chan int, 5)    // bidirectional

var send chan<- int = ch   // OK: narrowing to send-only
var recv <-chan int = ch   // OK: narrowing to receive-only

// var ch2 chan int = send  // COMPILE ERROR: cannot convert send-only to bidirectional
```

---

## 10. The `select` Statement

### 10.1 — What Is `select`?

`select` allows a goroutine to wait on **multiple channel operations simultaneously**. It picks whichever one is ready first. If multiple are ready, it chooses one at **random** (uniformly).

Think of `select` as a switch statement for channels.

```go
select {
case val := <-ch1:
    // ch1 had something to receive
case ch2 <- 42:
    // sent 42 into ch2
case val := <-ch3:
    // ch3 had something to receive
default:
    // NONE of the above were ready — runs immediately (non-blocking)
}
```

### 10.2 — Without `default` (Blocking `select`)

Without `default`, `select` blocks until at least one case is ready.

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch1 := make(chan string)
    ch2 := make(chan string)

    go func() {
        time.Sleep(1 * time.Second)
        ch1 <- "from ch1"
    }()

    go func() {
        time.Sleep(2 * time.Second)
        ch2 <- "from ch2"
    }()

    // Wait for whichever is ready first
    select {
    case msg := <-ch1:
        fmt.Println("Received:", msg) // ch1 wins after 1 second
    case msg := <-ch2:
        fmt.Println("Received:", msg)
    }
}
```

### 10.3 — With `default` (Non-Blocking)

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 1)

    select {
    case val := <-ch:
        fmt.Println("Got:", val)
    default:
        fmt.Println("No value ready — doing something else")
    }
}
```

This is the only way to do a non-blocking channel operation in Go.

### 10.4 — Timeout Pattern

```go
package main

import (
    "fmt"
    "time"
)

func fetchData(ch chan string) {
    time.Sleep(3 * time.Second)
    ch <- "data"
}

func main() {
    ch := make(chan string, 1)
    go fetchData(ch)

    select {
    case result := <-ch:
        fmt.Println("Got result:", result)
    case <-time.After(2 * time.Second): // time.After returns a channel
        fmt.Println("Timed out! Operation took too long.")
    }
}
```

`time.After(d)` returns a `<-chan time.Time` that receives a value after duration `d`. This is a beautifully idiomatic Go pattern.

### 10.5 — Cancellation with `done` Channel

```go
package main

import (
    "fmt"
    "time"
)

func worker(done <-chan struct{}, results chan<- int) {
    i := 0
    for {
        select {
        case <-done:
            fmt.Println("Worker: cancelled")
            return
        default:
            i++
            results <- i
            time.Sleep(100 * time.Millisecond)
        }
    }
}

func main() {
    done := make(chan struct{})
    results := make(chan int, 10)

    go worker(done, results)

    time.Sleep(500 * time.Millisecond)
    close(done) // signal cancellation to all goroutines listening on done

    // drain results
    time.Sleep(100 * time.Millisecond)
    for len(results) > 0 {
        fmt.Println("Result:", <-results)
    }
}
```

---

## 11. Ranging Over Channels

### 11.1 — The `range` Keyword with Channels

`for range` on a channel receives values continuously until the channel is **closed**.

```go
for val := range ch {
    // processes val
    // loop exits automatically when ch is closed AND empty
}
```

This is equivalent to:
```go
for {
    val, ok := <-ch
    if !ok {
        break
    }
    // process val
}
```

### 11.2 — Complete Example

```go
package main

import "fmt"

func generate(ch chan<- int, count int) {
    defer close(ch) // MUST close or the range loop will block forever
    for i := 1; i <= count; i++ {
        ch <- i
    }
}

func main() {
    ch := make(chan int, 5)
    go generate(ch, 10)

    for val := range ch { // automatically stops when ch is closed
        fmt.Printf("Received: %d\n", val)
    }

    fmt.Println("Done — channel was closed")
}
```

> **Critical rule**: If you `range` over a channel that is never closed, the loop blocks forever (deadlock if no other goroutine runs).

---

## 12. The `nil` Channel

### 12.1 — What Is a Nil Channel?

A nil channel is the zero value of a channel variable — it has not been initialized with `make`.

```go
var ch chan int  // ch is nil
```

### 12.2 — Behavior of Nil Channels

```
Operation on nil channel:
  Send:    ch <- val     → blocks FOREVER (never unblocks)
  Receive: val := <-ch   → blocks FOREVER (never unblocks)
  Close:   close(ch)     → PANIC
  In select case:        → case is NEVER selected (effectively disabled)
```

### 12.3 — The Powerful `select` Use Case

Because a nil channel case in `select` is never selected, you can use this to **dynamically disable channels**:

```go
package main

import "fmt"

func merge(ch1, ch2 <-chan int) <-chan int {
    out := make(chan int, 10)
    go func() {
        defer close(out)
        for ch1 != nil || ch2 != nil {
            select {
            case val, ok := <-ch1:
                if !ok {
                    ch1 = nil // disable this case by setting to nil
                    continue
                }
                out <- val
            case val, ok := <-ch2:
                if !ok {
                    ch2 = nil // disable this case by setting to nil
                    continue
                }
                out <- val
            }
        }
    }()
    return out
}

func sendNums(nums []int) <-chan int {
    ch := make(chan int, len(nums))
    go func() {
        defer close(ch)
        for _, n := range nums {
            ch <- n
        }
    }()
    return ch
}

func main() {
    ch1 := sendNums([]int{1, 2, 3})
    ch2 := sendNums([]int{10, 20, 30})

    merged := merge(ch1, ch2)
    for val := range merged {
        fmt.Println(val)
    }
}
```

When `ch1` closes, setting `ch1 = nil` means the `case val, ok := <-ch1` in `select` is never chosen again. This elegantly handles the case where one channel closes before the other.

---

## 13. Concurrency Patterns

### 13.1 — Pipeline Pattern

A pipeline chains goroutines together where each stage receives from one channel and sends to another. Data flows through stages like water through pipes.

```
┌──────────┐     ch1      ┌──────────┐     ch2      ┌──────────┐
│  Source  │ ───────────► │  Stage 1 │ ───────────► │  Stage 2 │ ──► result
│(generate)│             │(multiply)│             │  (filter) │
└──────────┘             └──────────┘             └──────────┘
```

```go
package main

import "fmt"

// Stage 1: generate integers
func generate(nums ...int) <-chan int {
    out := make(chan int, len(nums))
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

// Stage 2: square each integer
func square(in <-chan int) <-chan int {
    out := make(chan int, 10)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

// Stage 3: filter — only even results
func filterEven(in <-chan int) <-chan int {
    out := make(chan int, 10)
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
    // Chain the pipeline: generate → square → filterEven
    nums := generate(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    squared := square(nums)
    filtered := filterEven(squared)

    for val := range filtered {
        fmt.Println(val) // 4, 16, 36, 64, 100
    }
}
```

### 13.2 — Fan-Out Pattern

One goroutine distributes work across multiple worker goroutines. Use when work items are independent and can be processed in parallel.

```
                    ┌─► worker 1 ─┐
                    │              │
source ──► ch ──────┼─► worker 2 ─┼──► results
                    │              │
                    └─► worker 3 ─┘
```

```go
package main

import (
    "fmt"
    "sync"
)

func fanOut(in <-chan int, numWorkers int) []<-chan int {
    outputs := make([]<-chan int, numWorkers)
    for i := 0; i < numWorkers; i++ {
        out := make(chan int, 10)
        outputs[i] = out
        go func(id int, out chan<- int) {
            defer close(out)
            for val := range in {
                out <- val * val // each worker squares the value
                fmt.Printf("Worker %d processed: %d → %d\n", id, val, val*val)
            }
        }(i, out)
    }
    return outputs
}

func main() {
    in := make(chan int, 10)
    go func() {
        defer close(in)
        for i := 1; i <= 9; i++ {
            in <- i
        }
    }()

    outputs := fanOut(in, 3) // 3 workers

    // collect from first output for demo
    for val := range outputs[0] {
        fmt.Println("Result:", val)
    }
}
```

### 13.3 — Fan-In (Merge) Pattern

Multiple goroutines send to separate channels; one goroutine collects all results into a single channel.

```
producer 1 ──► ch1 ─┐
                     ├──► merge goroutine ──► single output
producer 2 ──► ch2 ─┘
```

```go
package main

import (
    "fmt"
    "sync"
)

func merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int, 100)

    // Launch a goroutine for each input channel
    output := func(ch <-chan int) {
        defer wg.Done()
        for val := range ch {
            merged <- val
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go output(ch)
    }

    // Close merged when all goroutines finish
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

func producer(name string, vals []int) <-chan int {
    ch := make(chan int, len(vals))
    go func() {
        defer close(ch)
        for _, v := range vals {
            fmt.Printf("[%s] sending %d\n", name, v)
            ch <- v
        }
    }()
    return ch
}

func main() {
    ch1 := producer("Alpha", []int{1, 2, 3})
    ch2 := producer("Beta", []int{10, 20, 30})
    ch3 := producer("Gamma", []int{100, 200, 300})

    for val := range merge(ch1, ch2, ch3) {
        fmt.Println("Merged result:", val)
    }
}
```

### 13.4 — Worker Pool Pattern

A fixed number of workers process jobs from a shared queue. This controls concurrency level and avoids spawning unlimited goroutines.

```
                ┌─ worker 1 ─┐
jobs ──► queue ─┼─ worker 2 ─┼──► results
                └─ worker 3 ─┘
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

func workerPool(numWorkers int, jobs <-chan Job, results chan<- Result) {
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        workerID := i
        go func() {
            defer wg.Done()
            for job := range jobs {
                // Simulate work: compute factorial
                result := factorial(job.Value)
                results <- Result{JobID: job.ID, Output: result}
                fmt.Printf("Worker %d: job %d → %d! = %d\n",
                    workerID, job.ID, job.Value, result)
            }
        }()
    }

    // Close results when all workers are done
    go func() {
        wg.Wait()
        close(results)
    }()
}

func factorial(n int) int {
    if n <= 1 {
        return 1
    }
    return n * factorial(n-1)
}

func main() {
    const numJobs = 10
    const numWorkers = 3

    jobs := make(chan Job, numJobs)
    results := make(chan Result, numJobs)

    // Launch worker pool
    workerPool(numWorkers, jobs, results)

    // Send jobs
    for i := 1; i <= numJobs; i++ {
        jobs <- Job{ID: i, Value: i}
    }
    close(jobs) // signal no more jobs

    // Collect results
    for res := range results {
        _ = res // already printed by worker
    }

    fmt.Println("All jobs complete")
}
```

### 13.5 — Semaphore Pattern (Limiting Concurrency)

A buffered channel used as a **semaphore** — a classic CS concept for controlling access to a limited resource.

```
┌─────────────────────────────────────────────┐
│  sem := make(chan struct{}, 3)               │
│                                             │
│  sem <- struct{}{}  // "acquire" a slot     │
│  ... do work ...                            │
│  <-sem              // "release" the slot   │
│                                             │
│  At most 3 goroutines in critical section   │
└─────────────────────────────────────────────┘
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    sem := make(chan struct{}, 3) // max 3 concurrent operations
    var wg sync.WaitGroup

    for i := 1; i <= 10; i++ {
        wg.Add(1)
        taskID := i
        go func() {
            defer wg.Done()

            sem <- struct{}{}        // acquire semaphore (blocks if 3 already running)
            defer func() { <-sem }() // release semaphore when done

            fmt.Printf("Task %d starting\n", taskID)
            time.Sleep(200 * time.Millisecond) // simulate work
            fmt.Printf("Task %d done\n", taskID)
        }()
    }

    wg.Wait()
    fmt.Println("All tasks complete")
}
```

---

## 14. Performance Characteristics

### 14.1 — Memory Allocation

```
Unbuffered channel (make(chan int)):
  hchan struct only ≈ 96 bytes (roughly, depends on type)
  No buffer allocation.

Buffered channel (make(chan int, N)):
  hchan struct + N * sizeof(int) bytes for the buffer.
  Example: make(chan int64, 1000) ≈ 96 + 8000 = ~8 KB
```

Choose buffer size carefully — large buffers waste memory if rarely filled.

### 14.2 — Throughput Considerations

```
Unbuffered:
  Every send requires a matching receive in another goroutine.
  Each message = one goroutine switch (scheduler involved).
  High synchronization overhead.

Buffered:
  Multiple sends without blocking = fewer goroutine switches.
  Amortizes scheduler overhead over N messages.
  Higher throughput in producer-faster-than-consumer scenarios.
```

### 14.3 — Latency Considerations

```
Unbuffered:
  Lower latency for the MESSAGE (receiver gets it immediately).
  Higher latency for the SENDER (must wait).

Buffered:
  Sender has lower latency (returns immediately if buffer has space).
  Receiver may have higher latency (must wait if buffer is empty).
```

### 14.4 — Benchmarking Insight

```
Channel operation costs (rough approximations):
  Unbuffered send+receive: ~250-500 ns (involves goroutine scheduling)
  Buffered send (non-blocking): ~50-100 ns (just a memory copy + index update)
  Mutex lock/unlock: ~25-50 ns (for comparison)
  Atomic operation: ~10 ns (for comparison)
```

For extremely high-frequency communication, consider `sync/atomic` or lock-free structures. Channels are for coordinating goroutines — not for maximum raw throughput.

### 14.5 — Choosing Buffer Size

```
┌─────────────────────────────────────────────────────────────────┐
│              BUFFER SIZE SELECTION GUIDE                        │
├─────────────────────────────────────────────────────────────────┤
│ Size 0  (unbuffered)                                            │
│   → You want guaranteed synchronization                         │
│   → You want rendezvous semantics                               │
│   → Sender and receiver can keep pace                           │
│                                                                 │
│ Size 1                                                          │
│   → Decouple one send from one receive (single-item lookahead)  │
│   → Useful for "at most one pending" scenarios                  │
│                                                                 │
│ Size N (small, e.g., 10-100)                                    │
│   → Absorb bursts in producer-consumer patterns                 │
│   → Worker pool job queues                                      │
│                                                                 │
│ Size N (large, e.g., 10000)                                     │
│   → Usually a design smell — rethink the architecture           │
│   → Could indicate producer is far faster than consumer         │
│     and backpressure is needed                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 15. The Mental Model

### 15.1 — The Fundamental Intuition

Think of goroutines as people, and channels as the means of communication:

```
UNBUFFERED CHANNEL = Phone Call
  ─────────────────────────────
  Both parties must be on the line simultaneously.
  You cannot "send a message" and hang up.
  The moment of transfer IS the moment of connection.
  Guarantee: when you hang up, they have your message.

BUFFERED CHANNEL = Voicemail / Mailbox
  ──────────────────────────────────────
  You can leave messages without the other party being present.
  But: if the mailbox is full, you wait.
  And: if the mailbox is empty, they wait.
  No guarantee of WHEN they'll pick it up.
```

### 15.2 — Flow of Control Visualization

```
UNBUFFERED — Who controls whom?

  Sender ────► channel (0 capacity) ────► Receiver

  If Sender is FASTER than Receiver:
    Sender WAITS at channel → Receiver drives the pace
    (Receiver is the bottleneck, controls throughput)

  If Receiver is FASTER than Sender:
    Receiver WAITS at channel → Sender drives the pace
    (Sender is the bottleneck, controls throughput)

  → The SLOWER party controls throughput.
  → This is natural backpressure.


BUFFERED — The buffer is a pressure valve:

  Sender ─┐           ┌─ Receiver
           ▼           ▼
      ┌──────────────────┐
      │   buffer (N)     │
      └──────────────────┘
       absorbs speed differences

  Buffer fills up → sender experiences backpressure
  Buffer empties  → receiver experiences starvation
```

### 15.3 — The CSP Perspective

Go channels are based on **Communicating Sequential Processes** (CSP) by Tony Hoare (1978). The key insight: **communication IS synchronization**.

In CSP, processes communicate by exchanging messages over named channels. The act of exchanging a message is what coordinates the timing of processes. This is fundamentally different from shared-memory concurrency (mutexes, locks) where coordination and communication are separate concerns.

```
CSP Model:
  P1  ||| P2  ||| P3     (concurrent processes)
  P1 and P2 communicate via channel c1
  P2 and P3 communicate via channel c2

  The channel IS the interface between concurrent components.
  Ownership of data transfers through communication.
```

### 15.4 — Mental Checklist When Designing Concurrent Go Code

```
1. WHO produces the data?
   → This goroutine owns the send end.

2. WHO consumes the data?
   → This goroutine owns the receive end.

3. Do they need to synchronize (know when transfer happened)?
   → Unbuffered channel.

4. Can they run at different speeds?
   → Buffered channel. What's the max burst size? → buffer capacity.

5. Who closes the channel?
   → ALWAYS the producer (sender). NEVER the consumer.

6. How do I signal cancellation?
   → A separate done channel, closed (not sent to) for broadcast.

7. How do I collect from multiple goroutines?
   → Fan-in (merge) pattern.

8. How do I distribute work?
   → Fan-out or worker pool pattern.
```

---

## 16. Common Mistakes and How to Avoid Them

### 16.1 — Forgetting to Close Channels

```go
// BUG: goroutine leak — receiver range loops forever
func producer(ch chan int) {
    ch <- 1
    ch <- 2
    // forgot close(ch)!
}

// FIX:
func producer(ch chan int) {
    defer close(ch) // ALWAYS use defer for safety
    ch <- 1
    ch <- 2
}
```

### 16.2 — Closing from the Wrong Side

```go
// BUG: receiver closes the channel
func consumer(ch chan int) {
    val := <-ch
    close(ch) // WRONG — only producer should close
    _ = val
}
```

### 16.3 — Multiple Goroutines Closing the Same Channel

```go
// BUG: both goroutines might close ch
func worker(ch chan int) {
    ch <- 42
    close(ch) // if two workers do this, PANIC
}

// FIX: use sync.Once
var once sync.Once

func worker(ch chan int, once *sync.Once) {
    ch <- 42
    once.Do(func() { close(ch) }) // only closes once, safely
}
```

### 16.4 — Using Buffered Channels for Synchronization

```go
// WRONG: assuming buffer guarantees ordering
ch := make(chan int, 5)
go func() {
    data = 100     // write data
    ch <- 1        // signal (goes into buffer, no rendezvous)
}()
// There's NO happens-before guarantee here for 'data'!
// The send completed but the receive hasn't happened yet.
val := <-ch
fmt.Println(data) // MIGHT see 0 (data race!) — undefined behavior

// CORRECT: use unbuffered for synchronization guarantees
ch := make(chan int)    // unbuffered
go func() {
    data = 100
    ch <- 1    // blocks until received → data is VISIBLE after this
}()
<-ch
fmt.Println(data) // SAFE: guaranteed to see 100
```

### 16.5 — Goroutine Leaks

```go
// BUG: goroutine is blocked forever waiting on channel — leaked
func leaky() {
    ch := make(chan int)
    go func() {
        val := <-ch // blocks forever — ch is never sent to
        _ = val
    }()
    // function returns, ch goes out of scope
    // goroutine is still alive, blocked — LEAK
}

// FIX: use a done/cancel channel
func notLeaky(done <-chan struct{}) {
    ch := make(chan int, 1)
    go func() {
        select {
        case val := <-ch:
            _ = val
        case <-done: // can be cancelled
            return
        }
    }()
}
```

---

## 17. Summary Reference Card

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     CHANNEL QUICK REFERENCE                                 │
├─────────────────────┬───────────────────────────────────────────────────────┤
│ CREATION            │                                                        │
│   Unbuffered        │  make(chan T)     or  make(chan T, 0)                  │
│   Buffered          │  make(chan T, N)                                       │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ OPERATIONS          │                                                        │
│   Send              │  ch <- value                                           │
│   Receive           │  value := <-ch                                         │
│   Recv with ok      │  value, ok := <-ch  (ok=false when closed+empty)      │
│   Close             │  close(ch)  — only sender, only once                  │
│   Length            │  len(ch)   — items currently in buffer                │
│   Capacity          │  cap(ch)   — buffer capacity (0 for unbuffered)       │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ BLOCKING RULES      │                                                        │
│   Unbuffered send   │  blocks until a receiver is ready                     │
│   Unbuffered recv   │  blocks until a sender is ready                       │
│   Buffered send     │  blocks only when buffer is FULL                      │
│   Buffered recv     │  blocks only when buffer is EMPTY                     │
│   Nil send/recv     │  blocks FOREVER                                        │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ PANICS              │                                                        │
│   Send to closed    │  panic: send on closed channel                        │
│   Close of closed   │  panic: close of closed channel                       │
│   Close of nil      │  panic: close of nil channel                          │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ CHANNEL TYPES       │                                                        │
│   Bidirectional     │  chan T                                                │
│   Send-only         │  chan<- T                                              │
│   Receive-only      │  <-chan T                                              │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ SELECT BEHAVIOR     │                                                        │
│   No default        │  blocks until one case ready                          │
│   With default      │  non-blocking; runs default if nothing ready          │
│   Nil case          │  never selected (use to disable a case)               │
│   Multiple ready    │  one chosen at RANDOM (uniform)                       │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ RANGE OVER CHANNEL  │  exits when channel closed AND empty                  │
├─────────────────────┼───────────────────────────────────────────────────────┤
│ WHEN TO USE WHICH   │                                                        │
│   Unbuffered        │  Synchronization, guaranteed ordering, rendezvous     │
│   Buffered          │  Decoupling, absorbing bursts, worker pools,           │
│                     │  semaphores, rate limiting                             │
└─────────────────────┴───────────────────────────────────────────────────────┘
```

---

### Cognitive Principle: Chunking This Knowledge

When you first learn channels, your brain treats every concept as separate (unbuffered blocking, buffered blocking, select, nil channels...). As you practice, these chunk into **patterns**: "pipeline," "fan-out," "semaphore." Eventually, you recognize the pattern *before* you read the problem fully — that is the expert's edge. Deliberately practice identifying which pattern applies before coding. This is how intuition is built.

The deepest mental model: **a channel is a typed, synchronized FIFO queue with optional buffering, whose operations follow precise blocking semantics, enabling safe communication between goroutines without shared memory**.

Hold that sentence in your mind. Every behavior of every channel example in this guide is a consequence of that definition.

---

*"Concurrency is not parallelism. Concurrency is a way to structure a program. Parallelism is simultaneous execution." — Rob Pike (Go co-creator)*


# Buffered vs Unbuffered Channels in Go
### A Complete, In-Depth Guide for Mastery

---

## Table of Contents

1. [Foundational Concepts: What is Concurrency?](#1-foundational-concepts-what-is-concurrency)
2. [What is a Goroutine?](#2-what-is-a-goroutine)
3. [What is a Channel?](#3-what-is-a-channel)
4. [The Core Mental Model: CSP Philosophy](#4-the-core-mental-model-csp-philosophy)
5. [Unbuffered Channels — Deep Dive](#5-unbuffered-channels--deep-dive)
6. [Buffered Channels — Deep Dive](#6-buffered-channels--deep-dive)
7. [Internal Runtime Mechanics](#7-internal-runtime-mechanics)
8. [Key Differences: Side-by-Side Analysis](#8-key-differences-side-by-side-analysis)
9. [Blocking Behaviour — Exhaustive Analysis](#9-blocking-behaviour--exhaustive-analysis)
10. [Deadlocks — What They Are and How to Cause/Avoid Them](#10-deadlocks--what-they-are-and-how-to-causeavoid-them)
11. [Closing Channels — Rules and Patterns](#11-closing-channels--rules-and-patterns)
12. [Range Over Channels](#12-range-over-channels)
13. [Channel Directions — Read-Only and Write-Only](#13-channel-directions--read-only-and-write-only)
14. [The `select` Statement — Multiplexing Channels](#14-the-select-statement--multiplexing-channels)
15. [Real-World Patterns and Use Cases](#15-real-world-patterns-and-use-cases)
16. [Performance Analysis and When to Choose Which](#16-performance-analysis-and-when-to-choose-which)
17. [Common Mistakes and Gotchas](#17-common-mistakes-and-gotchas)
18. [Mental Models for Expert Thinking](#18-mental-models-for-expert-thinking)
19. [Summary Reference Card](#19-summary-reference-card)

---

## 1. Foundational Concepts: What is Concurrency?

Before channels make sense, we must understand what problem they solve.

**Concurrency** means multiple tasks are *in progress* at the same time — they may or may not run literally simultaneously. A single CPU can be concurrent by time-slicing (rapidly switching between tasks).

**Parallelism** means tasks *literally run at the exact same instant* on multiple CPU cores.

Go is built for concurrent programming. It gives you lightweight threads called **goroutines** and a communication primitive called **channels**.

```
Sequential Execution:
  Task A: [=====>]
  Task B:         [=====>]
  Task C:                 [=====>]
  Time:   ------------------------------------>

Concurrent Execution (1 CPU, time-sliced):
  Task A: [==>  ==>  ==>]
  Task B: [  ==>  ==>  ]
  Task C: [     ==>  ==>]
  Time:   ------------------------------------>

Parallel Execution (3 CPUs):
  Task A: [=====>]
  Task B: [=====>]   ← all running at literally the same instant
  Task C: [=====>]
  Time:   -------->
```

The challenge in concurrent programming: **How do concurrent tasks safely communicate data without corrupting it?**

Go's answer: **"Do not communicate by sharing memory; instead, share memory by communicating."** — Go Proverb

Channels are the tool for this.

---

## 2. What is a Goroutine?

A **goroutine** is Go's version of a lightweight concurrent thread managed by the Go runtime — not the OS.

```go
// This runs sequentially
func main() {
    doWork()  // blocks until done
    doMore()  // only starts after doWork finishes
}

// This runs concurrently
func main() {
    go doWork()  // starts goroutine, does NOT block
    doMore()     // runs immediately, concurrently with doWork
}
```

**Key properties of goroutines:**
- Start with ~2KB stack (OS threads start at ~8MB)
- The Go runtime multiplexes thousands of goroutines onto a small pool of OS threads
- They are cheap: you can create millions
- They are scheduled cooperatively/preemptively by the Go runtime (not the OS scheduler)

**The Problem with Goroutines Running Alone:**

```
Goroutine A:  [produces data]  -->  Where does this go?
Goroutine B:                        [needs data]  -->  How does it receive?
```

This is where channels come in.

---

## 3. What is a Channel?

A **channel** is a typed conduit — a pipe — through which goroutines can send and receive values.

```
Goroutine A                                     Goroutine B
  [SENDER]  ---[ value ]---> [CHANNEL] ---[ value ]--->  [RECEIVER]
```

Think of it like a pneumatic tube system in a bank: you put a capsule (value) in the tube (channel), and it arrives at another window (goroutine). The tube is **typed** — it only carries one kind of capsule.

**Syntax:**

```go
// Declaration: a channel that carries integers
var ch chan int

// Creation (unidirectional by default — both send and receive)
ch = make(chan int)         // unbuffered channel
ch = make(chan int, 5)      // buffered channel with capacity 5

// Short form
ch := make(chan int)        // unbuffered
ch := make(chan int, 5)     // buffered, capacity 5

// Send a value INTO the channel (arrow points INTO channel)
ch <- 42

// Receive a value FROM the channel (arrow points AWAY from channel)
value := <-ch

// Receive and discard
<-ch
```

**The zero value of a channel is `nil`:**

```go
var ch chan int
fmt.Println(ch == nil) // true
// Sending to or receiving from a nil channel blocks forever
// ch <- 1  // blocks forever — this is a deadlock in main goroutine
```

---

## 4. The Core Mental Model: CSP Philosophy

Go's channel design comes from **CSP — Communicating Sequential Processes**, a formal model invented by Tony Hoare in 1978.

The mental model:

```
┌──────────────────────────────────────────────────────────────────────┐
│                        CSP Mental Model                              │
│                                                                      │
│   Process A          Channel           Process B                     │
│  ┌─────────┐        ┌───────┐         ┌─────────┐                   │
│  │         │──send──►       ├──recv──►│         │                   │
│  │ Gorout. │        │ Pipe  │         │ Gorout. │                   │
│  │         │◄─recv──┤       │◄─send──│         │                   │
│  └─────────┘        └───────┘         └─────────┘                   │
│                                                                      │
│  Key insight: The channel IS the synchronisation point.              │
│  Processes only interact at channel operations.                      │
│  Between sends/receives, they are completely independent.            │
└──────────────────────────────────────────────────────────────────────┘
```

This is profound: **goroutines do not share memory through channels — they transfer ownership**. When goroutine A sends a value over a channel, it gives up that value. Goroutine B now owns it. No locks needed.

---

## 5. Unbuffered Channels — Deep Dive

### 5.1 Definition

An **unbuffered channel** has **zero capacity**. It can hold **no values in transit**.

```go
ch := make(chan int)        // capacity = 0
ch := make(chan int, 0)     // same thing, explicit
```

### 5.2 The Fundamental Rule: Synchronous Rendezvous

An unbuffered channel forces a **synchronous handshake** between sender and receiver.

> **RULE**: A send on an unbuffered channel blocks until a receiver is ready.
> A receive on an unbuffered channel blocks until a sender is ready.
> Both must be present simultaneously for the exchange to happen.

This is called a **rendezvous** — like two people exchanging a package: both must be physically present at the same time. If one arrives early, they wait.

```
SCENARIO 1: Sender arrives first
─────────────────────────────────

Time ──────────────────────────────────────────►

Goroutine A (sender):    [SEND]──────────BLOCKED──────────[HANDED OFF]──►
                                         (waiting)
Goroutine B (receiver):  ──────────────────────[RECEIVE]──[GOT VALUE]────►
                         (doing other work)


SCENARIO 2: Receiver arrives first
────────────────────────────────────

Time ──────────────────────────────────────────►

Goroutine A (sender):    ──────────────────────[SEND]──[HANDED OFF]────►
                         (doing other work)
Goroutine B (receiver):  [RECV]──────BLOCKED──────────[GOT VALUE]───────►
                                     (waiting)


SCENARIO 3: Both arrive simultaneously (theoretical)
─────────────────────────────────────────────────────

Time ──────────────────────────────────────────►

Goroutine A (sender):    ─────────[SEND + HANDED OFF]──────────────────►
Goroutine B (receiver):  ─────────[RECV + GOT VALUE]───────────────────►
                                  ↑ exchange happens instantly
```

### 5.3 Code Example — Basic Unbuffered Channel

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string) // unbuffered

    // Goroutine: sender
    go func() {
        fmt.Println("[Goroutine] About to send...")
        ch <- "hello"   // BLOCKS here until main goroutine receives
        fmt.Println("[Goroutine] Send complete, continuing.")
    }()

    // Main goroutine: receiver
    time.Sleep(1 * time.Second) // simulate doing other work
    fmt.Println("[Main] About to receive...")
    msg := <-ch  // receives; unblocks the goroutine above
    fmt.Println("[Main] Received:", msg)
}
```

**Output:**
```
[Goroutine] About to send...
[Main] About to receive...
[Main] Received: hello
[Goroutine] Send complete, continuing.
```

Notice: The goroutine printed "About to send..." but then BLOCKED on `ch <- "hello"` for 1 second until main was ready to receive.

### 5.4 Unbuffered Channel as a Synchronisation Barrier

The unbuffered channel's blocking nature makes it perfect as a **synchronisation barrier** — a point where one goroutine waits for another to reach a certain state.

```go
package main

import "fmt"

func worker(done chan bool) {
    fmt.Println("Working...")
    // ... do work ...
    fmt.Println("Work done!")
    done <- true  // signal completion
}

func main() {
    done := make(chan bool)  // unbuffered — acts as a signal
    go worker(done)
    <-done  // BLOCK until worker signals done
    fmt.Println("Main: worker finished, proceeding.")
}
```

**Flow Diagram:**

```
main()                         worker()
  │                               │
  ├──go worker(done)──────────────┤ (goroutine started)
  │                               │
  │                          "Working..."
  │                               │
  ├──<-done (BLOCKS)              │
  │   │                      "Work done!"
  │   │                           │
  │   │                      done <- true
  │   │◄──────────────────────────┤ (handshake!)
  │   │ (unblocked)               │
  │                               │ (goroutine ends)
"Main: worker finished"
  │
  ▼
```

### 5.5 The Guarantee: Happens-Before

This is an advanced and crucial concept.

When a value is exchanged over an unbuffered channel, Go's memory model gives you a **happens-before guarantee**:

> Everything done in Goroutine A *before* `ch <- value` is **guaranteed to be visible** to Goroutine B *after* `value := <-ch`.

This means you don't need a mutex or any other synchronisation primitive — the channel operation itself establishes the memory ordering guarantee.

```go
var result int

ch := make(chan struct{}) // unbuffered, used only for sync

go func() {
    result = computeHeavyWork() // this happens-before ch <- struct{}{}
    ch <- struct{}{}
}()

<-ch
// Here, result is GUARANTEED to have the value from computeHeavyWork()
// No data race. No mutex needed.
fmt.Println(result)
```

### 5.6 Visual: Unbuffered Channel State Machine

```
                    ┌──────────────────────────────────────────┐
                    │         UNBUFFERED CHANNEL               │
                    │           capacity = 0                   │
                    └──────────────────────────────────────────┘

  State: IDLE
  ┌─────────────────────────────┐
  │  Channel: [ EMPTY ]         │
  │  sendq: []                  │  ← queue of goroutines waiting to send
  │  recvq: []                  │  ← queue of goroutines waiting to receive
  └─────────────────────────────┘

  Event: Sender arrives (no receiver ready)
  ┌─────────────────────────────────────────────────────┐
  │  Channel: [ EMPTY ]                                  │
  │  sendq: [GoroutineA (value=42)]  ← PARKED/SUSPENDED │
  │  recvq: []                                           │
  └─────────────────────────────────────────────────────┘
             GoroutineA is OFF the CPU, sleeping.

  Event: Receiver arrives
  ┌─────────────────────────────────────────────────────┐
  │  DIRECT COPY: 42 copied from GoroutineA's stack     │
  │               directly to GoroutineB's variable     │
  │  sendq: []  ← GoroutineA woken up (RUNNABLE)        │
  │  recvq: []                                          │
  └─────────────────────────────────────────────────────┘
             GoroutineA and GoroutineB both proceed.

  Event: Receiver arrives (no sender ready)
  ┌─────────────────────────────────────────────────────┐
  │  Channel: [ EMPTY ]                                  │
  │  sendq: []                                           │
  │  recvq: [GoroutineB]  ← PARKED/SUSPENDED            │
  └─────────────────────────────────────────────────────┘
             GoroutineB is OFF the CPU, sleeping.
```

---

## 6. Buffered Channels — Deep Dive

### 6.1 Definition

A **buffered channel** has a finite, non-zero capacity. It is an internal queue (FIFO — First In, First Out) that can hold values without a receiver being immediately present.

```go
ch := make(chan int, 3)  // buffered channel with capacity 3
```

**Vocabulary:**
- **Capacity**: Total number of values the channel's buffer can hold (set at creation, immutable).
- **Length**: Current number of values sitting in the buffer waiting to be received.
- **FIFO**: First In, First Out — the first value sent is the first value received.

```go
ch := make(chan int, 3)
fmt.Println(cap(ch))  // 3 — total capacity
fmt.Println(len(ch))  // 0 — currently empty

ch <- 10
ch <- 20
fmt.Println(len(ch))  // 2 — two values in buffer
```

### 6.2 The Fundamental Rule: Asynchronous Until Full

> **RULE**: A send on a buffered channel blocks **only when the buffer is full**.
> A receive on a buffered channel blocks **only when the buffer is empty**.

This is **asynchronous** behaviour — sender and receiver are **decoupled in time**.

```
BUFFERED CHANNEL (capacity=3):

  State: EMPTY
  Buffer: [ _ | _ | _ ]
           empty  empty  empty
  len=0, cap=3

  After ch <- 10:
  Buffer: [10 | _ | _ ]
  len=1, cap=3  — send did NOT block, returned immediately

  After ch <- 20:
  Buffer: [10 | 20 | _ ]
  len=2, cap=3  — send did NOT block

  After ch <- 30:
  Buffer: [10 | 20 | 30]
  len=3, cap=3  — send did NOT block (buffer exactly full now)

  After ch <- 40:  ← BLOCKS! Buffer is full!
  Buffer: [10 | 20 | 30]  ← no room for 40
  Sender goroutine is PARKED until someone receives.

  After v := <-ch:  ← receives 10 (FIFO — first in, first out)
  Buffer: [20 | 30 | _ ]  ← space freed, 40 can now enter
  Buffer: [20 | 30 | 40]  ← 40 was waiting, now inserted
  v = 10
```

### 6.3 Code Example — Basic Buffered Channel

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 3) // buffered, capacity 3

    // These three sends do NOT block — buffer absorbs them
    ch <- 10
    ch <- 20
    ch <- 30

    fmt.Println("Sent 3 values. Buffer len:", len(ch)) // 3
    fmt.Println("Buffer cap:", cap(ch))                 // 3

    // These receives do NOT block — values are in buffer
    fmt.Println(<-ch) // 10 (FIFO)
    fmt.Println(<-ch) // 20
    fmt.Println(<-ch) // 30

    fmt.Println("Buffer now empty. len:", len(ch)) // 0
}
```

**Output:**
```
Sent 3 values. Buffer len: 3
Buffer cap: 3
10
20
30
Buffer now empty. len: 0
```

**Critical observation:** We sent and received **in the same goroutine** (no `go` keyword). This works because the buffer allowed sends without blocking. Attempting this with an unbuffered channel would immediately deadlock.

### 6.4 Code Example — Producer/Consumer Decoupling

```go
package main

import (
    "fmt"
    "time"
)

func producer(ch chan<- int) {
    for i := 0; i < 5; i++ {
        fmt.Printf("[Producer] Sending %d\n", i)
        ch <- i  // won't block unless buffer full
        time.Sleep(100 * time.Millisecond) // produces fast
    }
    close(ch)
}

func consumer(ch <-chan int) {
    for v := range ch {
        fmt.Printf("[Consumer] Processing %d\n", v)
        time.Sleep(300 * time.Millisecond) // processes slow
    }
}

func main() {
    ch := make(chan int, 3) // buffer absorbs speed difference
    go producer(ch)
    consumer(ch) // run consumer in main goroutine
}
```

**What happens here:**
- Producer runs fast, fills the buffer
- Consumer runs slow, drains the buffer
- The buffer acts as a **shock absorber** between their different speeds

```
Timeline:
t=0ms:   Producer sends 0 → buffer:[0]
t=100ms: Producer sends 1 → buffer:[0,1]
t=200ms: Producer sends 2 → buffer:[0,1,2]
t=300ms: Consumer receives 0 ← buffer:[1,2]
         Producer sends 3 → buffer:[1,2,3]
t=400ms: Producer sends 4 → buffer:[1,2,3,4]  (buffer was [1,2,3], now 4 enters after space freed)
         Actually producer blocks here until consumer frees space...
```

### 6.5 Visual: Buffered Channel State Machine

```
                ┌──────────────────────────────────────────────────┐
                │           BUFFERED CHANNEL (cap=4)               │
                └──────────────────────────────────────────────────┘

EMPTY STATE (len=0):
┌───────────────────────────────────────────────┐
│  Buffer: [ _ | _ | _ | _ ]                   │
│           ↑                                   │
│         FRONT (next to receive)               │
│  Receive: BLOCKS (nothing to receive)         │
│  Send:    DOES NOT BLOCK (space available)    │
└───────────────────────────────────────────────┘

PARTIAL STATE (len=2):
┌───────────────────────────────────────────────┐
│  Buffer: [42 | 99 | _  | _ ]                 │
│           ↑              ↑                    │
│         FRONT           BACK (next to fill)  │
│  Receive: DOES NOT BLOCK                      │
│  Send:    DOES NOT BLOCK                      │
└───────────────────────────────────────────────┘

FULL STATE (len=4):
┌───────────────────────────────────────────────┐
│  Buffer: [42 | 99 | 17 | 5 ]                 │
│           ↑                                   │
│         FRONT                                 │
│  Receive: DOES NOT BLOCK                      │
│  Send:    BLOCKS (buffer is full)             │
└───────────────────────────────────────────────┘

AFTER RECEIVE (consumed 42, now len=3):
┌───────────────────────────────────────────────┐
│  Buffer: [99 | 17 | 5  | _ ]                 │
│           ↑             ↑                     │
│         FRONT          BACK (empty slot)      │
│  A parked sender (if any) is now unparked     │
└───────────────────────────────────────────────┘
```

---

## 7. Internal Runtime Mechanics

Understanding how Go's runtime implements channels internally gives you a much stronger mental model.

### 7.1 The `hchan` Structure (Simplified)

Deep inside Go's runtime (`runtime/chan.go`), a channel is represented by this structure:

```
hchan struct:
┌─────────────────────────────────────────────────────┐
│  qcount    uint    ← current number of items in buf │
│  dataqsiz  uint    ← capacity (size of circular buf)│
│  buf       *[cap]T ← pointer to circular buffer     │
│  elemsize  uint16  ← size of each element           │
│  closed    uint32  ← 0=open, 1=closed               │
│  sendx     uint    ← send index (where to write)    │
│  recvx     uint    ← receive index (where to read)  │
│  recvq     waitq   ← list of goroutines waiting to  │
│                       receive (blocked receivers)    │
│  sendq     waitq   ← list of goroutines waiting to  │
│                       send (blocked senders)         │
│  lock      mutex   ← protects all fields above      │
└─────────────────────────────────────────────────────┘
```

### 7.2 The Circular Buffer

The buffered channel's internal storage is a **circular buffer** (ring buffer).

```
Circular Buffer (cap=4):

Initial state:                 sendx=0, recvx=0, qcount=0
  ┌───┬───┬───┬───┐
  │   │   │   │   │
  └───┴───┴───┴───┘
   [0] [1] [2] [3]
    ↑
  sendx=recvx=0

After ch <- 'A':              sendx=1, recvx=0, qcount=1
  ┌───┬───┬───┬───┐
  │ A │   │   │   │
  └───┴───┴───┴───┘
    ↑   ↑
  recvx sendx

After ch <- 'B', ch <- 'C':  sendx=3, recvx=0, qcount=3
  ┌───┬───┬───┬───┐
  │ A │ B │ C │   │
  └───┴───┴───┴───┘
    ↑           ↑
  recvx       sendx

After <-ch (receive 'A'):    sendx=3, recvx=1, qcount=2
  ┌───┬───┬───┬───┐
  │   │ B │ C │   │
  └───┴───┴───┴───┘
        ↑       ↑
      recvx   sendx

After ch <- 'D', ch <- 'E':  sendx=1, recvx=1, qcount=4
  ┌───┬───┬───┬───┐
  │ E │ B │ C │ D │
  └───┴───┴───┴───┘
        ↑
   sendx=recvx=1 (FULL: wrapped around!)
```

The "circular" part means when `sendx` reaches the end of the array, it wraps around to index 0. This avoids expensive shifting/copying of elements.

### 7.3 Three Critical Fast Paths in Channel Operations

The Go runtime has three distinct cases when you send to a channel:

```
SEND OPERATION (ch <- value):
─────────────────────────────

                    ┌──────────────────┐
                    │   ch <- value    │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  Is recvq non-empty?     │  ← Is a goroutine WAITING to receive?
              │  (waiting receiver?)     │
              └──────────┬───────────────┘
                    YES  │        NO
                    ─────┘        └────────────────────────────────────────┐
                    ▼                                                       │
       ┌────────────────────────────┐                                      ▼
       │ FAST PATH:                 │                       ┌──────────────────────────┐
       │ Copy value DIRECTLY        │                       │ Is buffer not full?      │
       │ to receiver's stack        │                       │ (space in buf?)          │
       │ Unpark receiver goroutine  │                       └──────────┬───────────────┘
       │ Continue immediately       │                            YES   │    NO
       └────────────────────────────┘                            ──────┘    └──────────────┐
                                                                 ▼                         │
                                                  ┌─────────────────────────┐             ▼
                                                  │ BUFFERED PATH:          │  ┌────────────────────┐
                                                  │ Copy value to buf[sendx]│  │ PARK:              │
                                                  │ Increment sendx         │  │ Add goroutine to   │
                                                  │ Increment qcount        │  │ sendq              │
                                                  │ Return immediately      │  │ Goroutine sleeps   │
                                                  └─────────────────────────┘  │ (off CPU)          │
                                                                               └────────────────────┘


RECEIVE OPERATION (<-ch):
─────────────────────────

                    ┌──────────────────┐
                    │   v := <-ch      │
                    └────────┬─────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │  Is sendq non-empty?     │  ← Is a goroutine WAITING to send?
              └──────────┬───────────────┘
                    YES  │        NO
                    ─────┘        └────────────────────────────────────────┐
                    ▼                                                       │
       ┌────────────────────────────────┐                                  ▼
       │ FAST PATH (unbuffered):        │                  ┌──────────────────────────┐
       │ Copy value directly from       │                  │ Is buffer non-empty?     │
       │ sender's goroutine stack       │                  │ (items in buf?)          │
       │ Unpark sender                  │                  └──────────┬───────────────┘
       └────────────────────────────────┘                        YES  │    NO
                                                                 ──────┘    └──────────────┐
                                                                 ▼                         │
                                                  ┌─────────────────────────┐             ▼
                                                  │ BUFFERED PATH:          │  ┌────────────────────┐
                                                  │ Copy value from buf     │  │ PARK:              │
                                                  │ Increment recvx         │  │ Add goroutine to   │
                                                  │ Decrement qcount        │  │ recvq              │
                                                  │ Return immediately      │  │ Goroutine sleeps   │
                                                  └─────────────────────────┘  └────────────────────┘
```

### 7.4 Direct Send Optimisation (Unbuffered Channels)

For unbuffered channels, when a receiver is already waiting, Go performs a **direct stack-to-stack copy** — the value is copied directly from the sender's goroutine stack to the receiver's goroutine stack, **bypassing the channel's buffer entirely** (there is no buffer). This is extremely efficient.

```
Sender Goroutine Stack          Receiver Goroutine Stack
┌────────────────────┐          ┌────────────────────────┐
│  value = 42        │──copy──► │  v (waiting)  = 42     │
│  ...               │          │  ...                    │
└────────────────────┘          └────────────────────────┘
        │                                   │
        ▼                                   ▼
   Sender unblocked                  Receiver unblocked
   (continues running)               (continues running)
```

No intermediate buffer. No heap allocation. Fast.

---

## 8. Key Differences: Side-by-Side Analysis

```
┌──────────────────────────────┬───────────────────────────┬──────────────────────────────┐
│         PROPERTY             │     UNBUFFERED            │         BUFFERED             │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Syntax                       │ make(chan T)               │ make(chan T, N)               │
│                              │ make(chan T, 0)            │ N > 0                        │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Capacity                     │ 0 (no buffer)             │ N (fixed at creation)        │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Send blocks when             │ ALWAYS (until receiver    │ Buffer is FULL               │
│                              │ is ready)                 │                              │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Receive blocks when          │ ALWAYS (until sender      │ Buffer is EMPTY              │
│                              │ is ready)                 │                              │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Synchronisation              │ SYNCHRONOUS               │ ASYNCHRONOUS (until full)    │
│                              │ Both must be present      │ Sender/receiver decoupled    │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Coupling                     │ Tightly coupled           │ Loosely coupled              │
│                              │ (rendezvous)              │ (buffered decoupling)        │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Happens-before guarantee     │ Send completes AFTER      │ Send completes BEFORE        │
│                              │ receiver has received     │ receiver has received        │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Same-goroutine use           │ DEADLOCKS immediately     │ Works if buffer not full     │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Primary use                  │ Synchronisation,          │ Decoupling, work queues,     │
│                              │ signalling, handoff       │ rate limiting, batching      │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Memory overhead              │ Minimal (just hchan)      │ hchan + N * sizeof(T)        │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Deadlock risk                │ Higher (easier to         │ Lower (buffer gives slack)   │
│                              │ deadlock by accident)     │ but can still deadlock       │
├──────────────────────────────┼───────────────────────────┼──────────────────────────────┤
│ Race condition risk          │ Lower (forced sync)       │ Higher (subtle ordering)     │
└──────────────────────────────┴───────────────────────────┴──────────────────────────────┘
```

---

## 9. Blocking Behaviour — Exhaustive Analysis

Understanding exactly when a goroutine blocks is critical for writing correct concurrent code.

### 9.1 Complete Blocking Decision Tree

```
CHANNEL OPERATION BLOCKING DECISION TREE
══════════════════════════════════════════

Given: ch := make(chan T, N)  where N=0 for unbuffered, N>0 for buffered

┌─────────────────────────────────┐
│   What operation are you doing? │
└──────────────┬──────────────────┘
               │
       ┌───────┴───────┐
       │               │
    SEND             RECEIVE
  ch <- v            v := <-ch
       │               │
       ▼               ▼
┌─────────────┐  ┌──────────────┐
│  ch == nil? │  │  ch == nil?  │
└──────┬──────┘  └──────┬───────┘
   YES │    NO       YES │    NO
       │               │
    [BLOCK           [BLOCK
    FOREVER]         FOREVER]
       │               │
       ▼               ▼
┌──────────────┐  ┌────────────────┐
│ Unbuffered?  │  │  Unbuffered?   │
│  (N == 0)    │  │   (N == 0)     │
└──────┬───────┘  └───────┬────────┘
  YES  │   NO        YES  │   NO
       │                  │
  ┌────┴──────┐        ┌──┴──────────┐
  │ Receiver  │        │  Sender     │
  │ waiting   │        │  waiting    │
  │ in recvq? │        │  in sendq?  │
  └────┬──────┘        └──┬──────────┘
  YES  │   NO         YES │   NO
       │                  │
[DIRECT SEND         [DIRECT RECV
 No block]            No block]
       │   NO             │   NO
       ▼                  ▼
  [BLOCK:            [BLOCK:
   add to sendq]      add to recvq]
       │                  │
       ▼ (N > 0)          ▼ (N > 0)
┌──────────────┐  ┌────────────────┐
│  Buffer full?│  │  Buffer empty? │
│ len(ch)==cap │  │  len(ch)==0    │
└──────┬───────┘  └───────┬────────┘
  YES  │   NO        YES  │   NO
       │                  │
  [BLOCK]          [BLOCK]
       │   NO             │   NO
       ▼                  ▼
[Copy to buffer    [Copy from buffer
 No block]          No block]
```

### 9.2 Nil Channel Special Case

```go
var ch chan int  // nil channel

// These BLOCK FOREVER (not a deadlock in a goroutine — just hangs)
ch <- 1     // blocks forever
v := <-ch   // blocks forever

// Receiving from nil never returns
// This is actually useful in select statements (see section 14)
```

### 9.3 Closed Channel Behaviour

```go
ch := make(chan int, 2)
ch <- 10
ch <- 20
close(ch)

// Receiving from closed channel:
v, ok := <-ch  // v=10, ok=true  (value still in buffer)
v, ok = <-ch   // v=20, ok=true
v, ok = <-ch   // v=0,  ok=false (zero value, channel closed and empty)

// Sending to closed channel: PANICS
ch <- 30  // panic: send on closed channel
```

---

## 10. Deadlocks — What They Are and How to Cause/Avoid Them

### 10.1 What is a Deadlock?

A **deadlock** occurs when all goroutines are blocked waiting for something that can never happen. The Go runtime detects this and panics with:

```
fatal error: all goroutines are asleep - deadlock!
```

### 10.2 Classic Deadlock Patterns

**Pattern 1: Unbuffered channel, same goroutine**

```go
func main() {
    ch := make(chan int) // unbuffered
    ch <- 42            // DEADLOCK: blocks waiting for receiver
                        // but there IS no receiver (same goroutine)
    v := <-ch           // never reached
    fmt.Println(v)
}
```

```
main goroutine:
  [ch <- 42]──BLOCKS──► waiting for receiver
                        But only receiver IS main goroutine.
                        Main goroutine is blocked.
                        No one can receive.
                        DEADLOCK!
```

**Fix:** Use a goroutine or a buffered channel.

```go
// Fix 1: goroutine
go func() { ch <- 42 }()
v := <-ch  // now this can receive

// Fix 2: buffered channel
ch := make(chan int, 1)
ch <- 42   // doesn't block (buffer has space)
v := <-ch  // receives from buffer
```

**Pattern 2: Circular waiting**

```go
func main() {
    ch1 := make(chan int)
    ch2 := make(chan int)

    go func() {
        v := <-ch1  // waits for ch1
        ch2 <- v    // then sends to ch2
    }()

    go func() {
        v := <-ch2  // waits for ch2
        ch1 <- v    // then sends to ch1 ← DEADLOCK
    }()

    // main exits, goroutines deadlock on each other
    time.Sleep(time.Second)
}
```

```
Goroutine A:  waiting on ch1 ──► Goroutine B must send ch1
Goroutine B:  waiting on ch2 ──► Goroutine A must send ch2
Goroutine A:  can't advance (blocked on ch1)
Goroutine B:  can't advance (blocked on ch2)
     ↑_______________________________↑
              CIRCULAR DEPENDENCY = DEADLOCK
```

**Pattern 3: Forgetting to close a channel used with range**

```go
ch := make(chan int)
go func() {
    ch <- 1
    ch <- 2
    // forgot: close(ch)
}()

for v := range ch { // DEADLOCK: range never ends because ch not closed
    fmt.Println(v)
}
```

### 10.3 Deadlock Detection Mental Model

Ask yourself: **"For every blocked goroutine, is there another goroutine that will eventually unblock it?"**

```
Draw the dependency graph:

A waits for ──► X
B waits for ──► Y
X will be provided by ──► B
Y will be provided by ──► A

A ──► X (provided by B) ──► Y (provided by A) ──► ...
          ↑_____________________________________↑
                      CYCLE = DEADLOCK
```

If there is a cycle in the dependency graph, you have a deadlock.

### 10.4 Avoiding Deadlocks

```
RULES TO AVOID DEADLOCKS:
─────────────────────────

1. Ensure every send has a corresponding receive (and vice versa).

2. Use goroutines: never send and receive on unbuffered channel
   from the same goroutine without one of them being in a goroutine.

3. Close channels when done (especially for range/for loops).

4. Use select with default for non-blocking operations when appropriate.

5. Keep channel dependency graphs acyclic.

6. Use timeouts (context or time.After) to break potential deadlocks.

7. Prefer passing channels as function arguments (makes data flow explicit).
```

---

## 11. Closing Channels — Rules and Patterns

### 11.1 What Closing Does

```go
close(ch)
```

Closing a channel signals that **no more values will be sent** on it. It is a **broadcast signal** to all receivers.

### 11.2 The Rules of Closing

```
GOLDEN RULES OF CHANNEL CLOSING:
──────────────────────────────────

Rule 1: Only the SENDER should close a channel.
        Never close a channel from the receiver side.
        (Because sender knows when it's done sending)

Rule 2: Never close a channel TWICE.
        → panic: close of closed channel

Rule 3: Never send on a closed channel.
        → panic: send on closed channel

Rule 4: Receiving from a closed, empty channel returns
        (zero value, false) immediately. Does NOT block.

Rule 5: Receiving from a closed, non-empty channel
        continues to drain remaining values normally.

Rule 6: A nil channel can never be closed.
        → panic: close of nil channel
```

### 11.3 The Two-Value Receive

```go
v, ok := <-ch
// v   = the value received (zero value of T if channel closed+empty)
// ok  = true if channel is open and value is valid
//       false if channel is closed and buffer is drained
```

```go
ch := make(chan int, 3)
ch <- 10
ch <- 20
close(ch)

v, ok := <-ch; fmt.Println(v, ok)  // 10 true
v, ok  = <-ch; fmt.Println(v, ok)  // 20 true
v, ok  = <-ch; fmt.Println(v, ok)  // 0  false ← closed + empty
v, ok  = <-ch; fmt.Println(v, ok)  // 0  false ← still safe, always returns zero+false
```

### 11.4 Broadcast via Close

Closing a channel is a **one-to-many signal**. This is a critical pattern.

```go
package main

import (
    "fmt"
    "sync"
)

func worker(id int, stop <-chan struct{}, wg *sync.WaitGroup) {
    defer wg.Done()
    for {
        select {
        case <-stop:
            fmt.Printf("Worker %d: received stop signal\n", id)
            return
        default:
            fmt.Printf("Worker %d: working...\n", id)
            // do work
        }
    }
}

func main() {
    stop := make(chan struct{}) // closing this broadcasts to ALL workers
    var wg sync.WaitGroup

    for i := 1; i <= 3; i++ {
        wg.Add(1)
        go worker(i, stop, &wg)
    }

    // ... some time later
    close(stop) // broadcasts to ALL goroutines simultaneously

    wg.Wait()
    fmt.Println("All workers stopped.")
}
```

```
close(stop) broadcasts:
                ┌──► Worker 1: <-stop unblocks (receives zero value)
stop channel ───┼──► Worker 2: <-stop unblocks
                └──► Worker 3: <-stop unblocks

All workers stop simultaneously.
This is impossible with regular sends (you'd need to send N times for N workers).
```

---

## 12. Range Over Channels

### 12.1 How `range` Works on Channels

`for v := range ch` keeps receiving from `ch` until the channel is **closed and empty**.

```go
ch := make(chan int, 5)
for i := 0; i < 5; i++ {
    ch <- i * i
}
close(ch) // MUST close, or range loops forever

for v := range ch {
    fmt.Println(v) // 0, 1, 4, 9, 16
}
fmt.Println("Loop complete.")
```

**Equivalent manual form:**

```go
for {
    v, ok := <-ch
    if !ok {
        break // channel closed and empty
    }
    fmt.Println(v)
}
```

### 12.2 Range Flow Diagram

```
for v := range ch:
─────────────────

         ┌────────────────────────────────────┐
         │                                    │
         ▼                                    │
    ┌──────────┐   value available    ┌───────┴──────┐
    │  v, ok   │──────────────────────► process v    │
    │ := <-ch  │   (ok == true)       └──────────────┘
    └────┬─────┘
         │
         │ ch closed + empty (ok == false)
         ▼
    ┌──────────┐
    │  BREAK   │
    └──────────┘
```

### 12.3 Common Mistake: Forgetting to Close

```go
// BAD: range will hang forever (deadlock)
ch := make(chan int)
go func() {
    ch <- 1
    ch <- 2
    // missing: close(ch)
}()
for v := range ch { // waits forever after 2 values
    fmt.Println(v)
}

// GOOD:
go func() {
    ch <- 1
    ch <- 2
    close(ch) // signals: "done sending"
}()
for v := range ch { // cleanly exits after 2 values
    fmt.Println(v)
}
```

---

## 13. Channel Directions — Read-Only and Write-Only

### 13.1 Bidirectional vs Directional Channels

By default, channels are **bidirectional** — you can send and receive.

You can **restrict** a channel to one direction at the type level:

```go
chan T       // bidirectional (can send and receive)
chan<- T     // send-only (can only send)
<-chan T     // receive-only (can only receive)
```

**Memory Aid:**
- `chan<- T`: Arrow points into channel → send-only
- `<-chan T`: Arrow points out of channel → receive-only

### 13.2 Why Directional Channels?

They encode **intent** at the type level. The compiler enforces it.

```go
// This function should only receive from the channel
func consumer(ch <-chan int) {
    v := <-ch   // OK
    ch <- v     // COMPILE ERROR: cannot send to receive-only channel
}

// This function should only send to the channel
func producer(ch chan<- int) {
    ch <- 42    // OK
    v := <-ch   // COMPILE ERROR: cannot receive from send-only channel
}
```

### 13.3 Conversion Rules

```go
ch := make(chan int)  // bidirectional

// Bidirectional can be passed as either directional
var sendOnly chan<- int = ch   // OK: narrowing to send-only
var recvOnly <-chan int = ch   // OK: narrowing to receive-only

// Cannot widen:
// var bidir chan int = sendOnly  // COMPILE ERROR
// var bidir chan int = recvOnly  // COMPILE ERROR
```

### 13.4 Complete Pattern: Pipeline with Directional Channels

```go
package main

import "fmt"

// generate produces values and sends them
func generate(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out // returned as receive-only: caller can only receive
}

// square receives, squares, and sends
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

func main() {
    // Pipeline: generate → square → print
    c := generate(2, 3, 4, 5)
    out := square(c)

    for v := range out {
        fmt.Println(v) // 4, 9, 16, 25
    }
}
```

```
Pipeline Flow:
──────────────

generate()           square()           main()
    │                   │                  │
    ├──2──────────────►│                  │
    ├──3──────────────►│──4──────────────►│
    ├──4──────────────►│──9──────────────►│
    ├──5──────────────►│──16─────────────►│
    └──close──────────►│──25─────────────►│
                       └──close──────────►│
```

---

## 14. The `select` Statement — Multiplexing Channels

### 14.1 What is `select`?

`select` is like a `switch` statement but for channel operations. It waits for multiple channel operations simultaneously and executes whichever one is ready first.

```go
select {
case v := <-ch1:
    fmt.Println("received from ch1:", v)
case v := <-ch2:
    fmt.Println("received from ch2:", v)
case ch3 <- 99:
    fmt.Println("sent 99 to ch3")
default:
    fmt.Println("no channel ready") // non-blocking
}
```

### 14.2 Select Semantics

```
SELECT BEHAVIOUR:
─────────────────

1. ALL cases are evaluated simultaneously.

2. If ZERO cases are ready:
   - WITH default: execute default immediately (non-blocking)
   - WITHOUT default: BLOCK until at least one case is ready

3. If ONE case is ready: execute it.

4. If MULTIPLE cases are ready: pick ONE RANDOMLY (pseudo-random uniform choice).
   This is important: do not assume ordering!

5. A nil channel case is NEVER selected
   (useful to disable cases dynamically).
```

### 14.3 Select Flow Diagram

```
                    ┌────────────────────────────────────┐
                    │            select {                │
                    │   case v := <-ch1:                 │
                    │   case v := <-ch2:                 │
                    │   case ch3 <- x:                   │
                    │   default:                         │
                    │            }                       │
                    └──────────────┬─────────────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  Evaluate all cases      │
                    │  simultaneously          │
                    └──────────────────────────┘
                                   │
               ┌───────────────────┼──────────────────────────┐
               │                   │                          │
               ▼                   ▼                          ▼
        ┌─────────┐          ┌──────────┐              ┌──────────────┐
        │ ch1 has │          │ ch2 has  │              │  default     │
        │  data?  │          │  data?   │              │  (if present)│
        └────┬────┘          └────┬─────┘              └──────┬───────┘
             │ YES                │ YES                        │
             ▼                   ▼                            │
        ┌──────────────────────────────────────────┐         │
        │  Multiple cases ready? → PICK ONE AT     │         │
        │  RANDOM (fair, non-deterministic)        │         │
        └──────────────────────────────────────────┘         │
                                   │                          │
                    ┌──────────────┴──────────────────────────┘
                    │           NO cases ready
                    ▼
        ┌────────────────────┐      ┌────────────────────┐
        │  default present?  │─YES─►│  Execute default   │
        └─────────┬──────────┘      └────────────────────┘
                  │ NO
                  ▼
        ┌────────────────────┐
        │   BLOCK until      │
        │   one case ready   │
        └────────────────────┘
```

### 14.4 Timeout Pattern

```go
package main

import (
    "fmt"
    "time"
)

func fetchData() <-chan string {
    ch := make(chan string)
    go func() {
        time.Sleep(2 * time.Second) // simulate slow operation
        ch <- "data"
    }()
    return ch
}

func main() {
    data := fetchData()

    select {
    case result := <-data:
        fmt.Println("Got:", result)
    case <-time.After(1 * time.Second): // timeout after 1s
        fmt.Println("Timeout: operation took too long")
    }
}
```

```
Timeline:
─────────

t=0s:   select starts, waiting on data AND time.After(1s)
t=1s:   time.After fires first → "Timeout" branch executes
t=2s:   data arrives (too late, select already exited)
```

### 14.5 Done Channel / Cancellation Pattern

```go
func process(jobs <-chan int, done <-chan struct{}) {
    for {
        select {
        case j, ok := <-jobs:
            if !ok {
                return // jobs channel closed
            }
            fmt.Println("Processing job:", j)
        case <-done:
            fmt.Println("Cancelled!")
            return
        }
    }
}
```

### 14.6 Non-Blocking Operations with `default`

```go
ch := make(chan int, 1)

// Non-blocking send (try to send, don't block if full)
select {
case ch <- 42:
    fmt.Println("sent successfully")
default:
    fmt.Println("channel full, send skipped")
}

// Non-blocking receive (try to receive, don't block if empty)
select {
case v := <-ch:
    fmt.Println("received:", v)
default:
    fmt.Println("channel empty, nothing received")
}
```

### 14.7 Disabling Cases with Nil Channels

```go
// Use nil to "disable" a channel case in select

var ch1, ch2 chan int
ch1 = make(chan int)
ch2 = make(chan int)

go func() { ch1 <- 1 }()
go func() { ch2 <- 2 }()

for i := 0; i < 2; i++ {
    select {
    case v := <-ch1:
        fmt.Println("ch1:", v)
        ch1 = nil  // disable ch1 case — will never be selected again
    case v := <-ch2:
        fmt.Println("ch2:", v)
        ch2 = nil  // disable ch2 case
    }
}
```

---

## 15. Real-World Patterns and Use Cases

### 15.1 Worker Pool Pattern

```
Worker Pool Architecture:
─────────────────────────

               ┌──────────────────────────────────────┐
               │            DISPATCHER                │
               │   (creates jobs, sends to jobs ch)   │
               └──────────────────┬───────────────────┘
                                   │
                            jobs channel
                          (buffered, cap=N)
                                   │
              ┌────────────────────┼────────────────────┐
              │                    │                    │
              ▼                    ▼                    ▼
       ┌──────────┐         ┌──────────┐         ┌──────────┐
       │ Worker 1 │         │ Worker 2 │         │ Worker 3 │
       └────┬─────┘         └────┬─────┘         └────┬─────┘
            │                    │                    │
            └────────────────────┼────────────────────┘
                                 │
                          results channel
                                 │
                                 ▼
                         ┌──────────────┐
                         │  COLLECTOR   │
                         └──────────────┘
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
    Job    Job
    Output int
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
    defer wg.Done()
    for job := range jobs {
        // Simulate processing
        output := job.Value * job.Value
        results <- Result{Job: job, Output: output}
        fmt.Printf("Worker %d processed job %d\n", id, job.ID)
    }
}

func main() {
    const numWorkers = 3
    const numJobs = 10

    jobs := make(chan Job, numJobs)       // buffered: dispatcher doesn't block
    results := make(chan Result, numJobs) // buffered: workers don't block

    var wg sync.WaitGroup

    // Start workers
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    // Send jobs
    for j := 1; j <= numJobs; j++ {
        jobs <- Job{ID: j, Value: j}
    }
    close(jobs) // signal workers: no more jobs

    // Wait for all workers, then close results
    go func() {
        wg.Wait()
        close(results)
    }()

    // Collect results
    for r := range results {
        fmt.Printf("Job %d result: %d\n", r.Job.ID, r.Output)
    }
}
```

### 15.2 Pipeline Pattern (Fan-Out / Fan-In)

```
Fan-Out / Fan-In:
─────────────────

              ┌──────────────┐
              │    SOURCE    │──► ch_in
              └──────────────┘
                      │
                      ▼ (fan-out)
            ┌─────────┴──────────┐
            ▼                    ▼
     ┌──────────┐         ┌──────────┐
     │ Stage A1 │         │ Stage A2 │   (parallel workers)
     └─────┬────┘         └────┬─────┘
           │                   │
           └────────┬──────────┘
                    ▼ (fan-in / merge)
              ┌──────────────┐
              │    MERGER    │──► ch_out
              └──────────────┘
```

```go
package main

import (
    "fmt"
    "sync"
)

// merge (fan-in): combine multiple channels into one
func merge(channels ...<-chan int) <-chan int {
    var wg sync.WaitGroup
    merged := make(chan int, len(channels))

    // Start one goroutine per input channel
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

    // Close merged when all inputs done
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

func gen(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out
}

func main() {
    c1 := gen(1, 3, 5)
    c2 := gen(2, 4, 6)

    for v := range merge(c1, c2) {
        fmt.Println(v) // interleaved: order not guaranteed
    }
}
```

### 15.3 Rate Limiter Pattern (Buffered Channel as Semaphore)

```
Semaphore using buffered channel:
──────────────────────────────────
  sem := make(chan struct{}, N)  ← N = max concurrent operations

  sem <- struct{}{}   ← "acquire" (blocks if N already running)
  // ... do work ...
  <-sem               ← "release" (frees one slot)

Buffer visualised (N=3, max 3 concurrent):
  Slots:  [ • | • | • ]  ← all slots taken (3 running)
                           Next acquire BLOCKS
  
  After one release:
  Slots:  [ • | • |   ]  ← one slot free
                           Next acquire proceeds
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    // Rate limit: max 3 concurrent requests
    sem := make(chan struct{}, 3)
    var wg sync.WaitGroup

    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            sem <- struct{}{}      // acquire semaphore
            defer func() { <-sem }() // release on exit

            fmt.Printf("Request %d: started\n", id)
            time.Sleep(500 * time.Millisecond) // simulate work
            fmt.Printf("Request %d: done\n", id)
        }(i)
    }

    wg.Wait()
}
```

### 15.4 One-Time Event Notification (done channel)

```go
package main

import "fmt"

type Server struct {
    quit chan struct{} // closing this means "stop"
}

func NewServer() *Server {
    return &Server{quit: make(chan struct{})}
}

func (s *Server) Run() {
    for {
        select {
        case <-s.quit:
            fmt.Println("Server: shutting down")
            return
        default:
            // handle requests...
        }
    }
}

func (s *Server) Stop() {
    close(s.quit) // broadcast to all goroutines watching quit
}
```

### 15.5 Ticker / Heartbeat Pattern

```go
package main

import (
    "fmt"
    "time"
)

func heartbeat(interval time.Duration, done <-chan struct{}) <-chan time.Time {
    ch := make(chan time.Time)
    go func() {
        ticker := time.NewTicker(interval)
        defer ticker.Stop()
        for {
            select {
            case t := <-ticker.C:
                ch <- t
            case <-done:
                close(ch)
                return
            }
        }
    }()
    return ch
}

func main() {
    done := make(chan struct{})
    beats := heartbeat(500*time.Millisecond, done)

    for i := 0; i < 5; i++ {
        t := <-beats
        fmt.Println("Heartbeat at:", t.Format("15:04:05.000"))
    }
    close(done)
}
```

---

## 16. Performance Analysis and When to Choose Which

### 16.1 Unbuffered Channel Performance

```
Unbuffered channel operations:
───────────────────────────────

Send:    Must wait for receiver.
         OS thread parks goroutine → context switch overhead.
         When receiver is ready → direct stack copy (very fast copy).

Receive: Must wait for sender.
         Same overhead.

Best case:  Both goroutines arrive "simultaneously"
            → Direct copy, minimal blocking.

Worst case: High mismatch in timing
            → Frequent goroutine parking/unparking
            → Scheduler overhead dominates
```

### 16.2 Buffered Channel Performance

```
Buffered channel operations (buffer not full/empty):
──────────────────────────────────────────────────────

Send:    Lock hchan.lock → copy to buf[sendx] → unlock.
         NO goroutine parking.
         Fast: ~50-100ns typical.

Receive: Lock hchan.lock → copy from buf[recvx] → unlock.
         NO goroutine parking.
         Fast: ~50-100ns typical.

Buffer full/empty case: Same as unbuffered (parking overhead).
```

### 16.3 When to Choose: Decision Framework

```
CHOOSING BETWEEN UNBUFFERED AND BUFFERED:
──────────────────────────────────────────

Q1: Do you need guaranteed synchronisation?
    (i.e., sender must know receiver got the value)
    │
    YES → UNBUFFERED
    NO  → continue to Q2

Q2: Is there a speed mismatch between producer and consumer?
    (producer faster, consumer slower, or bursty)
    │
    YES → BUFFERED (buffer absorbs speed difference)
    NO  → continue to Q3

Q3: Do you need to limit concurrency / throttle work?
    │
    YES → BUFFERED (as semaphore)
    NO  → continue to Q4

Q4: Is it a one-time signal? (done, quit, cancel)
    │
    YES → UNBUFFERED or close(ch) pattern
    NO  → continue to Q5

Q5: Are you building a work queue?
    │
    YES → BUFFERED (jobs channel with buffer = queue depth)
    NO  → UNBUFFERED (default — safer, catches bugs earlier)
```

### 16.4 The "Right Size" for Buffered Channels

Choosing buffer size is subtle:

```
TOO SMALL (size=0 or 1):
  → Frequent blocking → high goroutine parking overhead
  → Throughput suffers if rates mismatch

TOO LARGE:
  → Memory waste (each slot holds sizeof(T) bytes)
  → Masks bugs: a producer that's "too fast" won't be caught
  → If consumer dies, producer goroutine can be producing forever
    into a large buffer without anyone noticing

JUST RIGHT:
  → Buffer = expected burst size
  → Buffer = worker count × typical task duration × send rate
  → For work queues: buffer = min(producer_rate * max_latency, memory_budget)

RULE OF THUMB:
  Start with 0 (unbuffered). Add buffer only when you have a measured
  reason (profiling shows goroutine parking is the bottleneck,
  or architecture requires decoupling).
```

---

## 17. Common Mistakes and Gotchas

### 17.1 Sending to a Closed Channel (Panic)

```go
ch := make(chan int)
close(ch)
ch <- 1  // PANIC: send on closed channel
```

**Fix:** Use a `sync.Once` or ensure the sender is the only closer.

### 17.2 Closing a Channel Twice (Panic)

```go
ch := make(chan int)
close(ch)
close(ch)  // PANIC: close of closed channel
```

### 17.3 Goroutine Leak — The Silent Killer

```go
// BAD: goroutine leaks if nobody receives
func leaky() {
    ch := make(chan int) // unbuffered
    go func() {
        result := compute()
        ch <- result  // blocks forever if caller gives up
    }()
    // caller might timeout and return, but goroutine is STUCK
    select {
    case v := <-ch:
        fmt.Println(v)
    case <-time.After(1 * time.Second):
        return  // caller exits, goroutine leaks!
    }
}
```

```
Goroutine leak diagram:
────────────────────────
main goroutine → returns (done with the work)
inner goroutine → stuck on ch <- result
                  forever (nobody receives anymore)
                  Memory not freed.
                  If this happens repeatedly → memory leak.

Fix: use context.WithTimeout and check ctx.Done() in the goroutine.
```

```go
// GOOD: use context for cancellation
func noLeak(ctx context.Context) {
    ch := make(chan int, 1) // buffer=1 so goroutine can exit even if nobody receives
    go func() {
        result := compute()
        select {
        case ch <- result:
        case <-ctx.Done(): // exit if context cancelled
        }
    }()

    select {
    case v := <-ch:
        fmt.Println(v)
    case <-ctx.Done():
        fmt.Println("cancelled")
    }
}
```

### 17.4 Thinking Buffered Channel = No Synchronisation Needed

```go
// WRONG MENTAL MODEL: "buffered channels are thread-safe, no worries"

var counter int
ch := make(chan struct{}, 100)

for i := 0; i < 100; i++ {
    go func() {
        ch <- struct{}{}
        counter++  // DATA RACE: channel doesn't protect counter!
        <-ch
    }()
}
// counter will have a data race — channel doesn't protect shared memory
```

**Channel transfers values; it does not protect arbitrary shared state.**

### 17.5 Range Without Close (Infinite Block)

```go
ch := make(chan int)
go func() {
    for i := 0; i < 3; i++ {
        ch <- i
    }
    // forgot close(ch)
}()

for v := range ch { // blocks after 3 values — waits for more that never come
    fmt.Println(v)
}
// deadlock or goroutine leak
```

### 17.6 Assuming Select is Ordered

```go
ch1 := make(chan int, 1)
ch2 := make(chan int, 1)
ch1 <- 1
ch2 <- 2

// You CANNOT assume ch1 is always selected first!
select {
case v := <-ch1:
    fmt.Println("ch1:", v) // might be selected
case v := <-ch2:
    fmt.Println("ch2:", v) // also might be selected
}
// If both are ready, the choice is RANDOM.
```

---

## 18. Mental Models for Expert Thinking

### 18.1 The Plumbing Mental Model

```
Think of channels as pipes in a plumbing system:

Unbuffered channel = a pipe with no tank:
  ┌──────┐                    ┌──────────┐
  │ TAP  │──(no tank)────────►│  DRAIN   │
  └──────┘                    └──────────┘
  If drain is closed, tap CANNOT flow.
  Both must be open simultaneously.

Buffered channel = a pipe with a water tank:
  ┌──────┐   ┌──────────────┐   ┌──────────┐
  │ TAP  │──►│    TANK      │──►│  DRAIN   │
  └──────┘   │  [capacity N]│   └──────────┘
             └──────────────┘
  Tap can fill tank even if drain is slow.
  Tank full → tap blocks.
  Tank empty → drain blocks.
```

### 18.2 The Ownership Transfer Mental Model

```
Channels transfer OWNERSHIP of data, not just values.

Goroutine A owns data.
A sends data over channel.
Now Goroutine B owns data.

A should not touch data after sending.
B can use data freely without locks.

This is why channels prevent data races:
  → At any point, only ONE goroutine owns the data.
  → No simultaneous access = no race condition.
```

### 18.3 The Rendezvous vs Mailbox Mental Model

```
Unbuffered = RENDEZVOUS (both must be present):
  Like a handshake.
  Sender and receiver MEET at the channel.
  Transaction completes only when BOTH are there.
  Strong synchronisation guarantee.

Buffered = MAILBOX (asynchronous messaging):
  Like dropping a letter in a mailbox.
  Sender doesn't wait for receiver to read it.
  Receiver reads it later when ready.
  Weaker coupling, more throughput.
```

### 18.4 The Traffic Lane Mental Model

```
Think of goroutines as cars, channels as lanes:

Unbuffered channel = one-lane bridge with no waiting area:
  Only ONE car crosses at a time.
  Oncoming car must wait.
  No queue.
  Direct handoff at the bridge centre.

Buffered channel (cap=N) = N-car parking lot before a bridge:
  Up to N cars can park.
  Cars arrive, park, and leave when bridge is free.
  Producer fills the lot; consumer clears it.
```

### 18.5 When to Switch from Unbuffered to Buffered

```
SIGNAL: Use unbuffered when you WANT tight coupling.
         "I need to know you received this before I continue."

SIGNAL: Use buffered when you want THROUGHPUT and DECOUPLING.
         "I just need to queue this up. You deal with it when ready."

HEURISTIC (from Rob Pike):
  "Buffering is an optimisation. Start without it."
  Add a buffer when you have a measured reason —
  profiling shows excessive goroutine blocking,
  or the design explicitly requires a queue.
```

### 18.6 Cognitive Model: Channel as a Synchronisation Contract

```
Every channel represents a CONTRACT between goroutines:

Unbuffered Contract:
  "I (sender) PROMISE that you (receiver) have received
   this value before I continue past the send statement."

Buffered Contract:
  "I (sender) PROMISE this value will eventually be processed,
   but I am NOT waiting for you to confirm receipt."

Choose the contract that matches your correctness requirements.
If you need the guarantee → unbuffered.
If you need throughput → buffered.
```

---

## 19. Summary Reference Card

```
╔══════════════════════════════════════════════════════════════════════════════╗
║                    CHANNELS QUICK REFERENCE                                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║                                                                              ║
║  CREATION                                                                    ║
║  ──────────────────────────────────────────────────────────────────────      ║
║  make(chan T)       → unbuffered (cap=0)                                     ║
║  make(chan T, N)    → buffered (cap=N, N>0)                                  ║
║  var ch chan T      → nil channel (blocks forever on send/receive)           ║
║                                                                              ║
║  OPERATIONS                                                                  ║
║  ──────────────────────────────────────────────────────────────────────      ║
║  ch <- v           → send v into channel                                    ║
║  v := <-ch         → receive from channel                                   ║
║  v, ok := <-ch     → receive with closed check (ok=false if closed+empty)  ║
║  close(ch)         → close channel (only sender should do this)             ║
║  len(ch)           → current items in buffer                                ║
║  cap(ch)           → buffer capacity                                        ║
║                                                                              ║
║  BLOCKING RULES                                                              ║
║  ──────────────────────────────────────────────────────────────────────      ║
║  Unbuffered send:  blocks until receiver ready                               ║
║  Unbuffered recv:  blocks until sender ready                                 ║
║  Buffered send:    blocks only when buffer FULL                              ║
║  Buffered recv:    blocks only when buffer EMPTY                             ║
║  Nil send/recv:    blocks FOREVER                                            ║
║  Closed send:      PANIC                                                     ║
║  Closed recv:      returns (zero value, false) immediately                  ║
║                                                                              ║
║  CHOOSE UNBUFFERED WHEN          CHOOSE BUFFERED WHEN                       ║
║  ───────────────────────         ─────────────────────────                  ║
║  • Need sync guarantee           • Speed mismatch (decoupling)              ║
║  • Signalling / events           • Work queue needed                        ║
║  • Handshake / rendezvous        • Rate limiting (semaphore)                ║
║  • Happens-before needed         • Batch collection                         ║
║  • Default choice (safer)        • Pipeline stages                          ║
║                                  • Absorb bursts                            ║
║                                                                              ║
║  GOLDEN RULES                                                                ║
║  ──────────────────────────────────────────────────────────────────────      ║
║  1. Only SENDERS close channels                                              ║
║  2. Never close a channel TWICE                                              ║
║  3. Never SEND on a closed channel                                           ║
║  4. Start with unbuffered; buffer only when measured                        ║
║  5. Use directional types (chan<-, <-chan) to encode intent                 ║
║  6. Always handle goroutine leaks (use context/done channels)               ║
║  7. close(ch) broadcasts to ALL receivers simultaneously                    ║
║  8. select with default = non-blocking operation                            ║
║  9. Nil channel in select = disabled case (never selected)                  ║
║  10. Range over channel: MUST close channel or loop runs forever            ║
╚══════════════════════════════════════════════════════════════════════════════╝
```

---

### Final Thought: The Expert Intuition

The deepest insight about channels is this: **the choice between unbuffered and buffered is not a performance choice — it is a correctness and design choice**.

An unbuffered channel says: *"I need coordination."*
A buffered channel says: *"I need throughput."*

Getting this choice wrong leads to either subtle race conditions (choosing buffered when you needed synchronisation) or unnecessary performance bottlenecks (choosing unbuffered when decoupling was fine).

Master Go programmers internalize this distinction until it becomes reflexive — they can look at a concurrent design and immediately feel which type of channel fits, the same way a martial artist feels which technique applies without conscious deliberation. That is the level you are building toward.

---

*Guide compiled for mastery-level understanding of Go channel mechanics.*
*All code examples are runnable Go. All ASCII diagrams represent actual runtime behaviour.*