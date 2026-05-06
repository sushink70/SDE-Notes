# Go Concurrency: The Complete, In-Depth Guide
## Goroutines, Channels, Scheduler, Patterns, and Mental Models

---

> *"Do not communicate by sharing memory; instead, share memory by communicating."*
> — Rob Pike, Go Co-creator

---

## Table of Contents

1. [Foundation: What is Concurrency?](#1-foundation-what-is-concurrency)
2. [CSP: The Philosophy Behind Go Concurrency](#2-csp-the-philosophy-behind-go-concurrency)
3. [Goroutines: Lightweight Threads](#3-goroutines-lightweight-threads)
4. [The Go Scheduler: GMP Model](#4-the-go-scheduler-gmp-model)
5. [Goroutine Stack and Memory Layout](#5-goroutine-stack-and-memory-layout)
6. [Channels: The Communication Backbone](#6-channels-the-communication-backbone)
7. [Unbuffered Channels: Synchronous Rendezvous](#7-unbuffered-channels-synchronous-rendezvous)
8. [Buffered Channels: Asynchronous Communication](#8-buffered-channels-asynchronous-communication)
9. [Channel Directions: Type Safety](#9-channel-directions-type-safety)
10. [The `select` Statement: Multiplexing Channels](#10-the-select-statement-multiplexing-channels)
11. [Channel Ownership and Lifecycle](#11-channel-ownership-and-lifecycle)
12. [Range Over Channels](#12-range-over-channels)
13. [The `sync` Package](#13-the-sync-package)
14. [The `sync/atomic` Package](#14-the-syncatomic-package)
15. [The `context` Package](#15-the-context-package)
16. [Concurrency Patterns](#16-concurrency-patterns)
17. [Race Conditions: Detection and Prevention](#17-race-conditions-detection-and-prevention)
18. [Deadlocks: Causes and Avoidance](#18-deadlocks-causes-and-avoidance)
19. [Memory Model: Happens-Before](#19-memory-model-happens-before)
20. [Error Handling in Concurrent Code](#20-error-handling-in-concurrent-code)
21. [Testing Concurrent Code](#21-testing-concurrent-code)
22. [Performance Tuning and GOMAXPROCS](#22-performance-tuning-and-gomaxprocs)
23. [Mental Models and Expert Thinking](#23-mental-models-and-expert-thinking)

---

## 1. Foundation: What is Concurrency?

### Terminology Primer

Before diving into Go, let's define every term precisely — because fuzzy terminology causes fuzzy thinking.

| Term | Definition |
|------|-----------|
| **Concurrency** | The *composition* of independently executing processes. About *structure*. |
| **Parallelism** | The *simultaneous* execution of computations. About *execution*. |
| **Process** | An OS-level isolated execution unit with its own memory space. |
| **Thread** | An OS-level unit of execution within a process, sharing memory with siblings. |
| **Goroutine** | A Go-managed, user-space lightweight execution unit. |
| **Scheduler** | The entity that assigns goroutines to OS threads. |
| **Synchronization** | Coordinating goroutines so they operate correctly together. |
| **Race Condition** | A bug where program behavior depends on non-deterministic execution order. |
| **Deadlock** | All goroutines are blocked waiting for each other — program stalls forever. |
| **Livelock** | Goroutines are actively responding to each other but making no progress. |
| **Starvation** | A goroutine cannot get resources it needs because others monopolize them. |
| **Critical Section** | Code that accesses shared resources — must run exclusively. |
| **Mutex** | Mutual Exclusion lock — only one goroutine enters the critical section. |
| **Semaphore** | A generalized counter-based lock limiting concurrent access. |
| **Channel** | A typed conduit for communication and synchronization between goroutines. |

---

### Concurrency vs Parallelism — The Visual Distinction

```
CONCURRENCY (Single CPU Core — Interleaved)
===========================================

Time ──────────────────────────────────────────────────────►

CPU:  [goroutine A]──[goroutine B]──[goroutine A]──[goroutine C]──[goroutine B]
       ^context switch^              ^context switch^

Only ONE thing runs at a time, but multiple things are "in progress."
This handles I/O-bound work efficiently (waiting doesn't waste CPU).


PARALLELISM (Multiple CPU Cores — Simultaneous)
===============================================

Time ──────────────────────────────────────────────────────►

Core 1: [goroutine A]────────────────────[goroutine A]───────
Core 2: [goroutine B]────────────────────[goroutine B]───────
Core 3: [goroutine C]────────────────────[goroutine C]───────
Core 4: [goroutine D]────────────────────[goroutine D]───────

Multiple things run SIMULTANEOUSLY. Requires multiple CPUs.
This handles CPU-bound work efficiently.

IMPORTANT: Go gives you BOTH.
Concurrency is the design. Parallelism is the execution (via GOMAXPROCS).
```

---

### Why Threads Are Expensive

Traditional OS threads have:
- **Stack size**: ~1–8 MB per thread (fixed or grows large)
- **Creation cost**: syscall overhead (~10,000 ns)
- **Context switch**: kernel mode switch (~1,000–10,000 ns)
- **Limit**: ~10,000 threads max before OS degrades

Go goroutines:
- **Stack size**: ~2 KB initial (grows dynamically)
- **Creation cost**: ~300 ns
- **Context switch**: user-space only (~100–200 ns)
- **Limit**: hundreds of thousands to millions

---

## 2. CSP: The Philosophy Behind Go Concurrency

### Communicating Sequential Processes

Go's concurrency model is based on **CSP** (Communicating Sequential Processes), a formal language designed by Tony Hoare in 1978. The core insight:

> Independent processes communicate by **passing messages**, not by sharing and locking memory.

```
TRADITIONAL SHARED-MEMORY MODEL (e.g., Java, C++)
==================================================

         Goroutine A           Goroutine B
              |                     |
              |    SHARED MEMORY    |
              |  ┌─────────────┐    |
              └──►  variable x ◄────┘
                 └─────────────┘
                       ▲
                  RACE CONDITION!
                  Who writes first?

Solution: Add locks (Mutex) — complex, error-prone.


CSP MODEL (Go's philosophy)
============================

         Goroutine A           Goroutine B
              |                     |
              |   ┌─────────────┐   |
              └───►   channel   ├───┘
                  └─────────────┘
                  
No shared state. Data ownership transferred via message.
The channel IS the synchronization mechanism.
```

### Two Pillars of Go Concurrency

```
             Go Concurrency
            ┌──────┴──────┐
            │             │
      Goroutines       Channels
      (execution)   (communication)
            │             │
      "Do work      "Talk to each
       concurrently"   other safely"
```

---

## 3. Goroutines: Lightweight Threads

### What is a Goroutine?

A goroutine is a **function executing concurrently** with other goroutines in the same address space. It is managed by the Go runtime, NOT the OS.

Think of it as: *a function that you launch and say "run this, I don't need to wait for you."*

### Basic Goroutine Syntax

```go
package main

import (
    "fmt"
    "time"
)

func sayHello(name string) {
    fmt.Printf("Hello from %s\n", name)
}

func main() {
    // Normal function call — blocks until done
    sayHello("main")

    // Goroutine — does NOT block, returns immediately
    go sayHello("goroutine-1")
    go sayHello("goroutine-2")
    go sayHello("goroutine-3")

    // WARNING: If main() returns, ALL goroutines are killed instantly!
    // This sleep is a BAD practice for sync (just for demo):
    time.Sleep(100 * time.Millisecond)
}
```

### The Lifecycle of a Goroutine

```
GOROUTINE LIFECYCLE
===================

  main()
    │
    ├── go func()  ──────────────────────────────────────────────────┐
    │              created & added to run queue                       │
    │                                                                 ▼
    │                                                    ┌─────────────────────┐
    │                                                    │      RUNNABLE       │
    │                                                    │  (waiting for CPU)  │
    │                                                    └──────────┬──────────┘
    │                                                               │
    │                                                    Scheduler assigns to M
    │                                                               │
    │                                                    ┌──────────▼──────────┐
    │                                                    │       RUNNING       │
    │                                                    │  (executing code)   │
    │                                                    └──────────┬──────────┘
    │                                                               │
    │                                                    ┌──────────▼──────────┐
    │                                                    │  Blocking I/O OR    │◄──┐
    │                                                    │  channel wait OR    │   │ preempted
    │                                                    │  syscall            │   │ by scheduler
    │                                                    └──────────┬──────────┘   │
    │                                                               │               │
    │                                                    ┌──────────▼──────────┐   │
    │                                                    │       WAITING       │───┘
    │                                                    │  (parked, off CPU)  │
    │                                                    └──────────┬──────────┘
    │                                                               │ condition met
    │                                                    ┌──────────▼──────────┐
    │                                                    │       DEAD          │
    │                                                    │  (function returns) │
    └───────────────────────────────────────────────────└─────────────────────┘
```

### Anonymous Goroutines (Closures)

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    var wg sync.WaitGroup // explained in section 13

    for i := 0; i < 5; i++ {
        wg.Add(1)
        
        // CRITICAL: Capture loop variable correctly
        i := i  // Shadow i — creates new variable per iteration
        
        go func() {
            defer wg.Done()
            fmt.Printf("Worker %d running\n", i)
        }()
    }
    
    wg.Wait()
    fmt.Println("All workers done")
}
```

**The Classic Closure Trap — MUST UNDERSTAND:**

```go
// BUG: All goroutines capture the SAME variable i
for i := 0; i < 5; i++ {
    go func() {
        fmt.Println(i)  // prints 5,5,5,5,5 — NOT 0,1,2,3,4!
    }()
}

// WHY? Goroutines close over the variable i (a pointer to i),
// not the VALUE of i at creation time.
// By the time goroutines run, the loop has finished, i==5.

// FIX 1: Shadow the variable
for i := 0; i < 5; i++ {
    i := i  // new variable, captured by value
    go func() { fmt.Println(i) }()
}

// FIX 2: Pass as argument
for i := 0; i < 5; i++ {
    go func(n int) { fmt.Println(n) }(i)  // i copied at call time
}
```

---

## 4. The Go Scheduler: GMP Model

This is the most important internals concept for understanding Go's performance.

### G, M, P — The Three Entities

| Entity | Name | What it is |
|--------|------|------------|
| **G** | Goroutine | The unit of work. Contains stack, program counter, state. |
| **M** | Machine (OS Thread) | The actual OS thread. Runs goroutines. |
| **P** | Processor | A logical CPU. Holds a run queue of goroutines. |

### GMP Architecture

```
GMP MODEL — COMPLETE PICTURE
==============================

  GLOBAL RUN QUEUE
  ┌──────────────────────────────────────────┐
  │  G  G  G  G  G  G  G  G  G  G  G  G    │
  └──────────────────────────────────────────┘
         │           ▲
         │ steal      │ overflow
         ▼           │

  P0               P1               P2               P3
  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
  │LocalQueue│    │LocalQueue│    │LocalQueue│    │LocalQueue│
  │ G G G G  │    │ G G G G  │    │ G G G G  │    │ G G G G  │
  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘
       │               │               │               │
       ▼               ▼               ▼               ▼
  ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
  │   M0   │      │   M1   │      │   M2   │      │   M3   │
  │OS Thread│     │OS Thread│     │OS Thread│     │OS Thread│
  └────┬───┘      └────┬───┘      └────┬───┘      └────┬───┘
       │               │               │               │
       ▼               ▼               ▼               ▼
  ┌────────┐      ┌────────┐      ┌────────┐      ┌────────┐
  │  CPU 0 │      │  CPU 1 │      │  CPU 2 │      │  CPU 3 │
  └────────┘      └────────┘      └────────┘      └────────┘

NOTES:
- Number of P's == GOMAXPROCS (default: number of CPU cores)
- Number of M's can exceed number of P's (blocked threads need new M's)
- Each P has a local run queue (LRQ) of up to 256 goroutines
- Global run queue (GRQ) handles overflow and new goroutines
```

### Work Stealing

When a P's local queue is empty, it **steals** goroutines from other P's:

```
WORK STEALING
=============

P0: [G1 G2 G3 G4]    P1: [G5 G6 G7 G8]    P2: []  (idle!)
                                                  │
                                            P2 steals half
                                            of P1's queue
                                                  │
P0: [G1 G2 G3 G4]    P1: [G5 G6]    P2: [G7 G8]
                                          │
                                     P2 can now work!

This ensures all CPUs stay busy — no idle time wasted.
```

### Blocking System Calls

When a goroutine makes a blocking syscall (disk I/O, network, etc.):

```
BLOCKING SYSCALL HANDLING
==========================

BEFORE SYSCALL:
  P0 ── M0 ── G_syscall  (G is about to block)

DURING SYSCALL:
  P0 ── M1 ── G_next     (P detaches from M0, binds to new M1)
       M0 ── G_syscall   (M0 + G blocked in kernel — no P)

AFTER SYSCALL:
  G_syscall tries to re-acquire a P
  If P available → continue on that P
  If no P available → G put in global run queue, M0 goes to thread cache
```

### Goroutine Preemption (Go 1.14+)

Before Go 1.14, goroutines were only preempted at function calls (cooperative). This caused CPU-bound goroutines to starve others.

Go 1.14+ introduced **asynchronous preemption**: every 10ms, a signal is sent to preempt any running goroutine, even in tight loops.

```go
// Pre Go 1.14: This would starve other goroutines!
// Post Go 1.14: Runtime preempts this via SIGURG signal.
go func() {
    for {
        // tight loop with no function calls
        // runtime can now forcibly preempt this
    }
}()
```

---

## 5. Goroutine Stack and Memory Layout

### Dynamic Stack Growth

```
GOROUTINE STACK GROWTH
=======================

Initial State:
  Stack: [  2 KB  ]
  Used:  [■■      ]

After deep recursion or large locals:
  Stack: [  4 KB  ]  ← doubled
  Used:  [■■■■    ]

Stack grows by allocating new, larger stack and COPYING everything.
This is why you can have millions of goroutines — they start tiny.

Max default stack: 1 GB (configurable via runtime/debug.SetMaxStack)

CONTRAST with OS threads:
  OS Thread stack: 1–8 MB FIXED at creation
  Goroutine stack: 2 KB initial, grows on demand up to 1 GB
```

### Stack vs Heap

```
MEMORY LAYOUT PER GOROUTINE
============================

┌─────────────────────────────────────────┐
│              HEAP (shared)              │
│  Objects that escape to heap live here  │
│  Managed by GC                          │
│                                         │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │  G1     │  │  G2     │  │  G3     │ │
│  │ objects │  │ objects │  │ objects │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘

┌───────────┐  ┌───────────┐  ┌───────────┐
│  G1 Stack │  │  G2 Stack │  │  G3 Stack │
│  (private)│  │  (private)│  │  (private)│
│           │  │           │  │           │
│ local vars│  │ local vars│  │ local vars│
│ func args │  │ func args │  │ func args │
│ return ptr│  │ return ptr│  │ return ptr│
└───────────┘  └───────────┘  └───────────┘

Each goroutine has its OWN stack — no sharing of stack frames.
```

### Escape Analysis

Go's compiler decides whether a variable lives on stack or heap via **escape analysis**:

```go
package main

// This stays on the stack — doesn't escape
func stackAlloc() int {
    x := 42      // x lives on stack
    return x     // value copied, x destroyed when function returns
}

// This escapes to heap — pointer outlives function
func heapAlloc() *int {
    x := 42      // x must live on heap because we return a pointer to it
    return &x    // after return, x still needs to exist
}

// Check escape analysis:
// go build -gcflags="-m" main.go
```

---

## 6. Channels: The Communication Backbone

### What is a Channel?

A channel is a **typed pipe** through which goroutines send and receive values. It provides both communication AND synchronization.

**Mental model:** A channel is like a conveyor belt in a factory:
- One goroutine places items on it (send)
- Another goroutine picks items off it (receive)
- The belt enforces order and prevents collisions

```
CHANNEL ANATOMY
===============

         Sender Goroutine          Receiver Goroutine
              │                           │
              │  ch <- value              value := <-ch
              │                           │
              ▼                           ▼
         ┌────────────────────────────────────┐
         │              CHANNEL               │
         │  ┌───┐ ┌───┐ ┌───┐ ┌───┐ ┌───┐   │
         │  │ v1│ │ v2│ │ v3│ │ v4│ │   │   │
         │  └───┘ └───┘ └───┘ └───┘ └───┘   │
         │  ← items flow this way →           │
         │  type: chan int                     │
         │  buffer: 0 (unbuffered) or N        │
         └────────────────────────────────────┘
```

### Channel Operations

```go
package main

import "fmt"

func main() {
    // ── CREATION ──────────────────────────────────────

    // Unbuffered channel (capacity 0)
    ch1 := make(chan int)

    // Buffered channel (capacity 5)
    ch2 := make(chan string, 5)

    // Zero value of channel is nil — always use make()
    var ch3 chan int  // ch3 == nil


    // ── SEND ──────────────────────────────────────────

    // Send to buffered channel (non-blocking if space available)
    ch2 <- "hello"
    ch2 <- "world"

    // Send to nil channel — BLOCKS FOREVER (deadlock)
    // ch3 <- 42  // would deadlock


    // ── RECEIVE ───────────────────────────────────────

    // Receive value
    val := <-ch2        // "hello"
    fmt.Println(val)

    // Receive with ok — checks if channel is open
    val2, ok := <-ch2   // ok == true if value received, false if channel closed & empty
    fmt.Println(val2, ok)

    // Receive from nil channel — BLOCKS FOREVER
    // _ = <-ch3  // would deadlock


    // ── CLOSE ─────────────────────────────────────────

    close(ch2)  // Signal no more values will be sent

    // Receive from closed channel returns zero value + ok=false
    val3, ok2 := <-ch2
    fmt.Println(val3, ok2)  // "", false

    // ── INSPECT ───────────────────────────────────────

    ch4 := make(chan int, 10)
    ch4 <- 1
    ch4 <- 2
    fmt.Println(len(ch4))  // 2  — current items in buffer
    fmt.Println(cap(ch4))  // 10 — total capacity

    _ = ch1
}
```

### Channel Operation Truth Table

```
CHANNEL OPERATION BEHAVIOR
============================

Operation          │ nil channel   │ Empty/Open  │ Non-empty/Open │ Closed
───────────────────┼───────────────┼─────────────┼────────────────┼──────────────
Send (ch <- v)     │ blocks forever│ blocks(unb) │ blocks(unb)    │ PANIC
                   │               │ succeeds(b) │ blocks if full │
Receive (<-ch)     │ blocks forever│ blocks      │ returns value  │ returns zero
                   │               │             │ (+ ok=true)    │ (+ ok=false)
Close (close(ch))  │ PANIC         │ succeeds    │ succeeds       │ PANIC
len(ch)            │ 0             │ 0           │ n items        │ n remaining
cap(ch)            │ 0             │ capacity    │ capacity       │ capacity

(unb) = unbuffered, (b) = buffered
```

---

## 7. Unbuffered Channels: Synchronous Rendezvous

### The Rendezvous Principle

An unbuffered channel forces **synchronized hand-off**. The sender blocks until a receiver is ready, and the receiver blocks until a sender is ready. They meet at the channel — this is called a **rendezvous**.

```
UNBUFFERED CHANNEL — STEP BY STEP
===================================

ch := make(chan int)  // capacity = 0

STEP 1: Goroutine A tries to send
─────────────────────────────────
   G_A: ch <- 42
         │
         └── No receiver ready → G_A BLOCKS (parked by scheduler)

   Timeline: G_A: ████BLOCKED████
             G_B: (not started yet)


STEP 2: Goroutine B starts and receives
────────────────────────────────────────
   G_B: val := <-ch
         │
         └── Sender (G_A) is waiting! → RENDEZVOUS occurs
              → 42 is transferred directly G_A → G_B
              → Both goroutines unblock simultaneously

   Timeline: G_A: ████BLOCKED████|──RUNNING──►
             G_B:                |──RUNNING──►
                                 ▲
                            rendezvous point


STEP 3: Both continue
──────────────────────
   G_A: continues after ch <- 42
   G_B: val == 42, continues
```

### Complete Unbuffered Channel Example

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    ch := make(chan string) // unbuffered

    // Goroutine that sends after 1 second
    go func() {
        fmt.Println("Sender: preparing message...")
        time.Sleep(1 * time.Second)
        fmt.Println("Sender: sending 'hello'")
        ch <- "hello"                        // blocks here until receiver ready
        fmt.Println("Sender: send complete") // continues after rendezvous
    }()

    fmt.Println("Receiver: waiting for message...")
    msg := <-ch  // blocks here until sender sends
    fmt.Printf("Receiver: got '%s'\n", msg)
}

// Output:
// Receiver: waiting for message...
// Sender: preparing message...
// Sender: sending 'hello'
// Sender: send complete
// Receiver: got 'hello'

// KEY INSIGHT:
// Receiver blocks first (channel empty, no sender yet).
// After 1s, sender sends → rendezvous → both unblock.
// "send complete" and "got 'hello'" happen concurrently after.
```

### Using Channels as Signals (Struct{})

For pure signaling (no data needed), use `chan struct{}` — it allocates **zero bytes**:

```go
package main

import "fmt"

func worker(done chan struct{}) {
    fmt.Println("Worker: doing work...")
    // ... do work ...
    fmt.Println("Worker: done")
    done <- struct{}{} // signal completion, zero allocation
}

func main() {
    done := make(chan struct{})
    go worker(done)
    <-done // wait for signal
    fmt.Println("Main: worker finished")
}
```

---

## 8. Buffered Channels: Asynchronous Communication

### Buffered Channel Mechanics

A buffered channel holds up to N items. Sends are non-blocking as long as buffer has space. Receives are non-blocking as long as buffer has items.

```
BUFFERED CHANNEL — CAPACITY 3
================================

ch := make(chan int, 3)
BUFFER: [ _ | _ | _ ]   len=0, cap=3

Send 1: ch <- 10
BUFFER: [10 | _ | _ ]   len=1, cap=3  (non-blocking — space available)

Send 2: ch <- 20
BUFFER: [10 |20 | _ ]   len=2, cap=3  (non-blocking)

Send 3: ch <- 30
BUFFER: [10 |20 |30 ]   len=3, cap=3  (non-blocking — last slot)

Send 4: ch <- 40
BUFFER: [10 |20 |30 ]   SENDER BLOCKS — buffer full!
         ▲
         │ Waiting to put 40 in

Receive: val := <-ch  → val = 10
BUFFER: [20 |30 | _ ]   len=2 — space freed → 40 can now be added
BUFFER: [20 |30 |40 ]   len=3

Direction of data: FIFO (First In, First Out)
```

### Complete Buffered Channel Example

```go
package main

import (
    "fmt"
    "time"
)

func producer(ch chan<- int, count int) {
    for i := 0; i < count; i++ {
        fmt.Printf("Producer: sending %d\n", i)
        ch <- i  // non-blocking if buffer has space
        time.Sleep(100 * time.Millisecond)
    }
    close(ch) // always close when done producing
}

func consumer(ch <-chan int) {
    for val := range ch { // range closes automatically when channel closed
        fmt.Printf("Consumer: received %d\n", val)
        time.Sleep(300 * time.Millisecond) // slower than producer
    }
    fmt.Println("Consumer: channel closed, exiting")
}

func main() {
    // Buffer size 3: producer can be 3 steps ahead of consumer
    ch := make(chan int, 3)

    go producer(ch, 8)
    consumer(ch) // run consumer in main goroutine
}
```

### When to Use Buffered vs Unbuffered

```
DECISION TREE: Buffered or Unbuffered?
========================================

          Do you need strict synchronization?
          (sender must wait for receiver acknowledgment)
                        │
            ┌───────────┴──────────┐
           YES                     NO
            │                      │
     UNBUFFERED                    │
     ch := make(chan T)             │
                         Can bursts of sends happen
                         before receiver processes?
                                   │
                      ┌────────────┴───────────┐
                     YES                        NO
                      │                         │
               BUFFERED                   Either works,
           ch := make(chan T, N)          prefer unbuffered
                                          for simplicity
```

```
USE UNBUFFERED WHEN:                USE BUFFERED WHEN:
═══════════════════                 ══════════════════
• Signaling (done, quit)            • Rate matching (fast producer,
• Request/response patterns           slow consumer)
• Strict ordering required          • Decoupling goroutine timing
• Simple goroutine coordination     • Batching work
• Ping-pong patterns                • Timeout handling
```

---

## 9. Channel Directions: Type Safety

### Directional Channel Types

Go allows you to restrict channel usage at the type level:

```go
chan T       // bidirectional: can send AND receive
chan<- T     // send-only: can only send (the arrow "goes into" chan)
<-chan T     // receive-only: can only receive (the arrow "comes out of" chan)
```

**Memory aid:** Think of the `<-` as a small arrow pointing toward the channel (send) or away from it (receive).

### Why Use Directional Channels?

```
WITHOUT DIRECTION (bad — error-prone)
========================================
func producer(ch chan int) {
    ch <- 1          // OK
    val := <-ch      // Also compiles! But wrong — producer shouldn't receive
    close(ch)        // OK
}

WITH DIRECTION (good — enforced by compiler)
============================================
func producer(ch chan<- int) {   // send-only
    ch <- 1                      // OK
    // val := <-ch               // COMPILE ERROR: cannot receive from send-only
    // close(ch)                 // OK — sender should close
}

func consumer(ch <-chan int) {   // receive-only
    val := <-ch                  // OK
    // ch <- 1                   // COMPILE ERROR: cannot send to receive-only
    // close(ch)                 // COMPILE ERROR: cannot close receive-only
}
```

### Conversion Rules

```go
ch := make(chan int, 5)   // bidirectional

// A bidirectional channel can be assigned to directional types
var sendOnly chan<- int = ch   // OK: bidirectional → send-only
var recvOnly <-chan int = ch   // OK: bidirectional → receive-only

// Directional → bidirectional: COMPILE ERROR
// var bidir chan int = sendOnly  // ERROR: cannot convert
```

### Real-World Pattern

```go
package main

import "fmt"

// Returns receive-only channel — caller can only read from it
// This enforces ownership: only this function can send/close
func generate(nums ...int) <-chan int {
    out := make(chan int)  // internal bidirectional
    go func() {
        for _, n := range nums {
            out <- n
        }
        close(out)
    }()
    return out  // returned as <-chan int (receive-only)
}

// Takes receive-only, returns receive-only
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
    nums := generate(2, 3, 4, 5)
    squares := square(nums)

    for n := range squares {
        fmt.Println(n)  // 4, 9, 16, 25
    }
}
```

---

## 10. The `select` Statement: Multiplexing Channels

### What is `select`?

`select` waits on **multiple channel operations simultaneously** and proceeds with whichever one is ready first. If multiple are ready, it picks one **uniformly at random** (to avoid starvation).

Think of it as a **switch statement for channels**.

```
SELECT MECHANICS
=================

select {
    case v := <-ch1:   // case 1: ready if ch1 has data
    case v := <-ch2:   // case 2: ready if ch2 has data
    case ch3 <- v:     // case 3: ready if ch3 can accept data
    default:           // case 4: ready ALWAYS (non-blocking)
}

DECISION FLOW:
──────────────
                     Enter select
                          │
             Check all cases simultaneously
                          │
          ┌───────────────┼───────────────┐
          │               │               │
       ch1 ready?      ch2 ready?      ch3 ready?
          │               │               │
          └───────────────┼───────────────┘
                          │
                  Any case ready?
                     │         │
                    YES        NO
                     │         │
              Pick one at       │
              random from    default case?
              ready cases        │
                     │       YES │  NO
                     │       proceed  block until
                     │               one becomes ready
                  Execute
                  chosen case
```

### Basic Select Example

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
        ch1 <- "one"
    }()
    go func() {
        time.Sleep(2 * time.Second)
        ch2 <- "two"
    }()

    // Receive from whichever channel is ready first
    for i := 0; i < 2; i++ {
        select {
        case msg1 := <-ch1:
            fmt.Println("Received from ch1:", msg1)
        case msg2 := <-ch2:
            fmt.Println("Received from ch2:", msg2)
        }
    }
}
// Output:
// (after 1s) Received from ch1: one
// (after 2s) Received from ch2: two
```

### Non-Blocking Operations with `default`

```go
package main

import "fmt"

func main() {
    ch := make(chan int, 1)

    // Non-blocking send attempt
    select {
    case ch <- 42:
        fmt.Println("Sent 42")
    default:
        fmt.Println("Channel full, skipped send")
    }

    // Non-blocking receive attempt
    select {
    case val := <-ch:
        fmt.Println("Received:", val)
    default:
        fmt.Println("No data available")
    }

    // Try receive again — channel now empty
    select {
    case val := <-ch:
        fmt.Println("Received:", val)
    default:
        fmt.Println("No data available") // this prints
    }
}
```

### Timeout Pattern with `select`

```go
package main

import (
    "fmt"
    "time"
)

func slowOperation() <-chan string {
    ch := make(chan string)
    go func() {
        time.Sleep(3 * time.Second)
        ch <- "result"
    }()
    return ch
}

func main() {
    resultCh := slowOperation()

    select {
    case result := <-resultCh:
        fmt.Println("Got result:", result)
    case <-time.After(2 * time.Second): // time.After returns a channel that sends after duration
        fmt.Println("Operation timed out!")
    }
}
```

### Quit/Done Signal Pattern

```go
package main

import (
    "fmt"
    "time"
)

func fibonacci(n int, ch chan<- int, quit <-chan struct{}) {
    a, b := 0, 1
    for i := 0; i < n; i++ {
        select {
        case ch <- a:         // try to send next fib number
            a, b = b, a+b
        case <-quit:          // gracefully stop if quit signal received
            fmt.Println("fibonacci: stopping")
            return
        }
    }
    close(ch)
}

func main() {
    ch := make(chan int)
    quit := make(chan struct{})

    go fibonacci(100, ch, quit)

    // Receive 5 fibonacci numbers then quit
    for i := 0; i < 5; i++ {
        fmt.Println(<-ch)
    }

    quit <- struct{}{} // send quit signal
    time.Sleep(10 * time.Millisecond)
}
```

### Select with Nil Channels (Disabling Cases)

A `nil` channel **never** becomes ready — you can use this to dynamically disable select cases:

```go
package main

import "fmt"

func merge(ch1, ch2 <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for ch1 != nil || ch2 != nil {
            select {
            case v, ok := <-ch1:
                if !ok {
                    ch1 = nil // disable this case — will never be selected again
                    continue
                }
                out <- v
            case v, ok := <-ch2:
                if !ok {
                    ch2 = nil // disable this case
                    continue
                }
                out <- v
            }
        }
    }()
    return out
}

func main() {
    c1 := make(chan int, 3)
    c2 := make(chan int, 3)
    c1 <- 1; c1 <- 3; c1 <- 5; close(c1)
    c2 <- 2; c2 <- 4; c2 <- 6; close(c2)

    for v := range merge(c1, c2) {
        fmt.Print(v, " ") // some ordering of 1,2,3,4,5,6
    }
    fmt.Println()
}
```

---

## 11. Channel Ownership and Lifecycle

### The Golden Rule

> **The goroutine that creates a channel should own it: it sends to it and closes it. Other goroutines only receive from it.**

This prevents:
- Double-close panics
- Send-on-closed-channel panics
- Unclear responsibility

```
CHANNEL OWNERSHIP MODEL
========================

Creator/Owner Goroutine        Consumer Goroutine(s)
──────────────────────         ─────────────────────
  ch := make(chan T)
                │
          Writes/sends          Reads/receives
                │                     │
          close(ch)             Detects close via
          (when done)           ok=false or range


WRONG (multiple writers + close):      RIGHT (single owner):
─────────────────────────────────      ────────────────────────
  go func() { ch <- 1 }()             owner goroutine controls
  go func() { ch <- 2 }()             all sends and close
  go func() { close(ch) }()           consumers only read
  // WHO CLOSES? WHEN?
  // PANIC: send on closed channel
```

### When Multiple Goroutines Must Send

Use a separate "done" goroutine pattern:

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    ch := make(chan int)
    var wg sync.WaitGroup

    // Multiple senders
    for i := 0; i < 5; i++ {
        wg.Add(1)
        i := i
        go func() {
            defer wg.Done()
            ch <- i * i // multiple goroutines send
        }()
    }

    // Closer goroutine — waits for all senders to finish
    go func() {
        wg.Wait()
        close(ch) // safe: called exactly once, after all sends done
    }()

    // Receiver
    for val := range ch {
        fmt.Println(val)
    }
}
```

---

## 12. Range Over Channels

### How `range` Works with Channels

`range` on a channel **blocks and receives values** until the channel is **closed**. It terminates cleanly — no need to check `ok`.

```go
package main

import "fmt"

func counter(max int) <-chan int {
    ch := make(chan int)
    go func() {
        for i := 0; i < max; i++ {
            ch <- i
        }
        close(ch) // MUST close — otherwise range blocks forever (deadlock)
    }()
    return ch
}

func main() {
    for n := range counter(5) {
        fmt.Println(n) // 0, 1, 2, 3, 4
    }
    fmt.Println("Done")
}
```

### Range vs Manual Receive

```go
// Using range (clean)
for val := range ch {
    process(val)
}

// Equivalent manual form (verbose)
for {
    val, ok := <-ch
    if !ok {
        break // channel closed and empty
    }
    process(val)
}
```

---

## 13. The `sync` Package

The `sync` package provides classical synchronization primitives. Use these when sharing memory is unavoidable or when channels feel awkward (e.g., protecting a shared data structure).

### 13.1 WaitGroup — Waiting for Goroutines

`WaitGroup` is a counter for tracking goroutines. Think of it as a "group of workers, wait for all to finish."

```
WAITGROUP MECHANICS
====================

   main goroutine                worker goroutines
        │                               │
    wg.Add(3)  ──── counter = 3        │
        │                               │
    go worker1()                    wg.Done() ─── counter = 2
    go worker2()                    wg.Done() ─── counter = 1
    go worker3()                    wg.Done() ─── counter = 0
        │                               │               │
    wg.Wait() ─── blocks here ─────────────────────────┘
    (unblocks when counter = 0)
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func worker(id int, wg *sync.WaitGroup) {
    defer wg.Done() // ALWAYS defer Done() first line — prevents forgetting
    fmt.Printf("Worker %d starting\n", id)
    time.Sleep(time.Duration(id) * 100 * time.Millisecond)
    fmt.Printf("Worker %d done\n", id)
}

func main() {
    var wg sync.WaitGroup

    for i := 1; i <= 5; i++ {
        wg.Add(1)          // increment BEFORE launching goroutine
        go worker(i, &wg)  // pass pointer — WaitGroup must not be copied
    }

    wg.Wait() // blocks until counter == 0
    fmt.Println("All workers completed")
}

// CRITICAL RULES:
// 1. wg.Add(n) BEFORE launching goroutine (not inside it)
// 2. wg.Done() exactly once per Add() — defer ensures this
// 3. Always pass *sync.WaitGroup (pointer), never copy
// 4. Don't reuse a WaitGroup while Wait() is still running
```

### 13.2 Mutex — Mutual Exclusion Lock

A `Mutex` ensures only one goroutine executes a critical section at a time.

```
MUTEX MECHANICS
================

                 Critical Section
                 ┌──────────────┐
  G1 ──Lock()──►│              │──Unlock()──►  G1 continues
                 │   balance += │
                 │   amount     │
                 └──────────────┘
                       ▲
                       │ BLOCKED while G1 inside
  G2 ──Lock()──────────┘ (waiting for G1 to Unlock)


STATE MACHINE:
──────────────
    ┌─────────────────────────────────────────┐
    │                                         │
  UNLOCKED ──── Lock() ────► LOCKED ─── Unlock() ──► UNLOCKED
    ▲                           │
    │                           │ Another goroutine calls Lock()
    │                           ▼
    │                        BLOCKED goroutine
    │                        (in lock wait queue)
    └──────────────── Unlock() awakens next waiter
```

```go
package main

import (
    "fmt"
    "sync"
)

type SafeCounter struct {
    mu    sync.Mutex
    count int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock() // ALWAYS defer Unlock() to prevent deadlock on panic
    c.count++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.count
}

func main() {
    counter := &SafeCounter{}
    var wg sync.WaitGroup

    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            counter.Increment()
        }()
    }

    wg.Wait()
    fmt.Println("Final count:", counter.Value()) // Always 1000
}
```

### 13.3 RWMutex — Reader-Writer Lock

When reads are frequent and writes are rare, `RWMutex` improves performance. Multiple goroutines can read simultaneously, but writes are exclusive.

```
RWMUTEX STATES
===============

Multiple readers:
  G1 ──RLock()──► reading ──RUnlock()──►
  G2 ──RLock()──► reading ──RUnlock()──►   ALL concurrent — OK!
  G3 ──RLock()──► reading ──RUnlock()──►

Writer arrives:
  G1 ──RLock()──► reading...
  G2 ──RLock()──► reading...
  Gw ──Lock()───► BLOCKED (waits for all readers to finish)

After readers done:
  Gw ──Lock()──► writing exclusively ──Unlock()──►
  G3 ──RLock()── BLOCKED while writer active

RULE: Many readers OR one writer. Never both.
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Cache struct {
    mu   sync.RWMutex
    data map[string]string
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()         // multiple goroutines can read simultaneously
    defer c.mu.RUnlock()
    val, ok := c.data[key]
    return val, ok
}

func (c *Cache) Set(key, value string) {
    c.mu.Lock()          // exclusive write access
    defer c.mu.Unlock()
    c.data[key] = value
}

func main() {
    cache := &Cache{data: make(map[string]string)}
    var wg sync.WaitGroup

    // Many concurrent readers
    for i := 0; i < 10; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            cache.Get("key") // safe concurrent reads
        }()
    }

    // Occasional writer
    wg.Add(1)
    go func() {
        defer wg.Done()
        time.Sleep(1 * time.Millisecond)
        cache.Set("key", "value") // exclusive write
    }()

    wg.Wait()
    val, _ := cache.Get("key")
    fmt.Println("Cached:", val)
}
```

### 13.4 Once — Single Initialization

`sync.Once` ensures a function is called **exactly once**, regardless of how many goroutines call it. Useful for lazy initialization.

```go
package main

import (
    "fmt"
    "sync"
)

type Singleton struct {
    data string
}

var (
    instance *Singleton
    once     sync.Once
)

func GetInstance() *Singleton {
    once.Do(func() {
        fmt.Println("Creating singleton (only once!)")
        instance = &Singleton{data: "initialized"}
    })
    return instance
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            s := GetInstance()
            _ = s
        }()
    }
    wg.Wait()
    // "Creating singleton" prints exactly ONCE
}
```

### 13.5 Cond — Condition Variable

`sync.Cond` allows goroutines to wait until a condition becomes true. Rarely used directly (channels usually cleaner), but essential for some patterns.

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

func main() {
    var mu sync.Mutex
    cond := sync.NewCond(&mu)
    ready := false

    // Waiter goroutine
    go func() {
        mu.Lock()
        for !ready {           // MUST use loop (spurious wakeups possible)
            cond.Wait()        // releases lock, suspends goroutine
                               // when woken: re-acquires lock, re-checks condition
        }
        fmt.Println("Waiter: condition is true!")
        mu.Unlock()
    }()

    // Signaler
    time.Sleep(100 * time.Millisecond)
    mu.Lock()
    ready = true
    cond.Signal()  // wake ONE waiter (or Broadcast() for ALL waiters)
    mu.Unlock()

    time.Sleep(100 * time.Millisecond)
}
```

### 13.6 Pool — Object Reuse

`sync.Pool` provides a cache of reusable objects to reduce GC pressure. Objects may be collected by GC at any time.

```go
package main

import (
    "bytes"
    "fmt"
    "sync"
)

var bufPool = sync.Pool{
    New: func() any {
        return new(bytes.Buffer) // called when pool is empty
    },
}

func process(data string) string {
    // Get buffer from pool (or create new if pool empty)
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()          // MUST reset before returning to pool
        bufPool.Put(buf)     // return to pool for reuse
    }()

    buf.WriteString(data)
    buf.WriteString(" processed")
    return buf.String()
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 5; i++ {
        wg.Add(1)
        i := i
        go func() {
            defer wg.Done()
            result := process(fmt.Sprintf("item-%d", i))
            fmt.Println(result)
        }()
    }
    wg.Wait()
}
```

---

## 14. The `sync/atomic` Package

Atomic operations are **lock-free, CPU-level instructions** for simple operations on integers and pointers. Faster than mutexes for simple counters.

```
WHY ATOMICS?
=============

Non-atomic increment (WRONG):
  val++ is actually THREE operations:
    1. READ:  tmp = val
    2. ADD:   tmp = tmp + 1
    3. WRITE: val = tmp

  G1: READ(val=5)
  G2: READ(val=5)        ← race! both read same value
  G1: WRITE(val=6)
  G2: WRITE(val=6)       ← both write 6, lost one increment!
  Expected: val=7, Actual: val=6

Atomic increment (CORRECT):
  atomic.AddInt64(&val, 1) is a SINGLE uninterruptible CPU instruction
  No other goroutine can interleave.
```

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

func main() {
    var counter int64 // must be int32, int64, uint32, uint64, or pointer

    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            atomic.AddInt64(&counter, 1)           // atomic increment
        }()
    }
    wg.Wait()
    fmt.Println("Counter:", atomic.LoadInt64(&counter)) // atomic read

    // Other atomic operations:
    atomic.StoreInt64(&counter, 0)                          // atomic write
    old := atomic.SwapInt64(&counter, 100)                  // atomic swap, returns old
    fmt.Println("Old:", old)                                 // 0

    // Compare-And-Swap (CAS) — foundation of lock-free algorithms
    // "If current value == old, set it to new, return success"
    swapped := atomic.CompareAndSwapInt64(&counter, 100, 200)
    fmt.Println("Swapped:", swapped, "Value:", atomic.LoadInt64(&counter))
    // swapped=true, Value=200

    // atomic.Value — store/load any type atomically
    var v atomic.Value
    v.Store(map[string]int{"key": 42}) // Store (must always store same type)
    m := v.Load().(map[string]int)     // Load with type assertion
    fmt.Println("Map:", m)
}
```

### When to Use What

```
SYNCHRONIZATION DECISION TREE
================================

          Is the operation SIMPLE?
          (increment, compare-and-swap, flag)
                    │
           ┌────────┴────────┐
          YES                 NO
           │                  │
      sync/atomic          More complex?
      (fastest)                │
                    ┌──────────┴──────────┐
                   YES                    NO
                    │                      │
          Are reads much more         sync.Mutex
          frequent than writes?       (general purpose)
                    │
           ┌────────┴────────┐
          YES                 NO
           │                  │
      sync.RWMutex        sync.Mutex
      (read-heavy)        (balanced)
```

---

## 15. The `context` Package

`context.Context` carries **deadlines, cancellation signals, and request-scoped values** across goroutines. It is the standard way to manage lifecycle of goroutines in production code.

### Why Context?

```
THE PROBLEM WITHOUT CONTEXT
============================

HTTP Request arrives
        │
        ├── go databaseQuery()     ─────────────────────────┐
        │         │                                          │
        │         ├── go cacheQuery()      ─────────────────┤
        │         │                                         │
        │         └── go externalAPI()     ─────────────────┤
        │                                                    │
   Client CANCELS request                                    │
        │                                                    │
   Handler returns                                           │
        │                                                    │
        └── But these goroutines keep running! ──────────────┘
             Wasting CPU, memory, DB connections.

WITH CONTEXT:
  All goroutines receive cancel signal → they stop immediately.
```

### Context Types

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func main() {
    // ── BACKGROUND ─────────────────────────────────────────────
    // Root context — never cancelled, no deadline, no values.
    // Use at top level (main, server start)
    ctx := context.Background()


    // ── TODO ────────────────────────────────────────────────────
    // Placeholder for "I'll add context later." Same as Background.
    // Use when you're not sure which context to use yet.
    ctx2 := context.TODO()
    _ = ctx2


    // ── WithCancel ──────────────────────────────────────────────
    // Returns context + cancel function.
    // Calling cancel() sends cancellation signal to ctx and children.
    cancelCtx, cancel := context.WithCancel(ctx)
    defer cancel() // ALWAYS defer cancel to free resources

    go func(ctx context.Context) {
        select {
        case <-time.After(2 * time.Second):
            fmt.Println("Work completed")
        case <-ctx.Done():
            fmt.Println("Cancelled:", ctx.Err()) // context.Canceled
        }
    }(cancelCtx)

    time.Sleep(500 * time.Millisecond)
    cancel() // cancel early
    time.Sleep(100 * time.Millisecond)


    // ── WithTimeout ─────────────────────────────────────────────
    // Automatically cancels after duration.
    // ctx.Err() == context.DeadlineExceeded
    timeoutCtx, cancel2 := context.WithTimeout(ctx, 1*time.Second)
    defer cancel2()

    go func(ctx context.Context) {
        select {
        case <-time.After(2 * time.Second):
            fmt.Println("Work completed")
        case <-ctx.Done():
            fmt.Println("Timeout:", ctx.Err())
        }
    }(timeoutCtx)

    time.Sleep(2 * time.Second)


    // ── WithDeadline ────────────────────────────────────────────
    // Cancels at absolute time point.
    deadline := time.Now().Add(500 * time.Millisecond)
    deadlineCtx, cancel3 := context.WithDeadline(ctx, deadline)
    defer cancel3()
    _ = deadlineCtx


    // ── WithValue ───────────────────────────────────────────────
    // Attach request-scoped values (NOT for passing function parameters!)
    // Use typed keys (not strings) to avoid collisions
    type contextKey string
    const userKey contextKey = "user"

    valueCtx := context.WithValue(ctx, userKey, "alice")
    user := valueCtx.Value(userKey).(string)
    fmt.Println("User:", user)
}
```

### Context in HTTP Handlers (Production Pattern)

```go
package main

import (
    "context"
    "database/sql"
    "fmt"
    "net/http"
    "time"
)

// Simulated DB query that respects context cancellation
func queryDB(ctx context.Context, db *sql.DB, id int) (string, error) {
    // Create query with timeout
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    // Most DB drivers accept context — they cancel query if ctx cancelled
    // db.QueryRowContext(ctx, "SELECT name FROM users WHERE id = ?", id)
    
    // Simulate work with context check
    select {
    case <-time.After(2 * time.Second):
        return fmt.Sprintf("user-%d", id), nil
    case <-ctx.Done():
        return "", ctx.Err()
    }
}

func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // HTTP request already carries a context!
                       // It's cancelled when client disconnects.

    result, err := queryDB(ctx, nil, 42)
    if err != nil {
        http.Error(w, "Query cancelled or timed out", http.StatusServiceUnavailable)
        return
    }
    fmt.Fprintln(w, result)
}

func main() {
    http.HandleFunc("/", handler)
    // http.ListenAndServe(":8080", nil)
}
```

### Context Tree Visualization

```
CONTEXT TREE (parent cancellation propagates to children)
==========================================================

context.Background()
        │
        ├── WithCancel(bg) ───────────────────────────────────────┐
        │        │                                                 │
        │        ├── WithTimeout(1s)                          cancel()
        │        │        │                                        │
        │        │        └── WithValue("user", "alice")          │
        │        │                                                 │
        │        └── WithDeadline(t+2s)                           │
        │                 │                                        │
        │                 └── WithCancel()                         │
        │                                                          │
        └── Background (never cancelled) ──────────────────────────
        
When cancel() is called on a node:
  - That node is cancelled
  - ALL descendants are cancelled recursively
  - Parent is NOT affected
```

---

## 16. Concurrency Patterns

These are the battle-tested patterns that expert Go programmers use. Learn them deeply — they are the vocabulary of concurrent systems.

### 16.1 Pipeline Pattern

Chain goroutines where each stage processes data and passes to the next.

```
PIPELINE
=========

  Source ──ch1──► Stage1 ──ch2──► Stage2 ──ch3──► Sink
  (gen)          (transform)    (transform)     (collect)

Data flows left to right. Each stage is independent.
```

```go
package main

import "fmt"

// Stage 1: Generate numbers
func gen(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

// Stage 2: Square numbers
func sq(in <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            out <- n * n
        }
    }()
    return out
}

// Stage 3: Filter (only even results)
func filter(in <-chan int) <-chan int {
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
    // Build pipeline
    nums := gen(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    squares := sq(nums)
    evens := filter(squares)

    // Consume pipeline
    for n := range evens {
        fmt.Print(n, " ") // 4 16 36 64 100
    }
    fmt.Println()
}
```

### 16.2 Fan-Out / Fan-In Pattern

**Fan-out:** One channel, multiple goroutines reading (distributing work).
**Fan-in:** Multiple channels, one goroutine merging (collecting results).

```
FAN-OUT:                         FAN-IN:
─────────                        ───────

                                 G1 ──ch1──┐
source ──ch──► G1                          │
         │                       G2 ──ch2──┤──► merged ──► consumer
         ├───► G2                          │
         │                       G3 ──ch3──┘
         └───► G3
```

```go
package main

import (
    "fmt"
    "sync"
)

// Fan-out: distribute work to N workers
func fanOut(in <-chan int, workers int) []<-chan int {
    channels := make([]<-chan int, workers)
    for i := 0; i < workers; i++ {
        channels[i] = func() <-chan int {
            out := make(chan int)
            go func() {
                defer close(out)
                for n := range in {
                    out <- n * n // each worker squares the number
                }
            }()
            return out
        }()
    }
    return channels
}

// Fan-in: merge multiple channels into one
func fanIn(channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup

    // Start a goroutine for each input channel
    forward := func(ch <-chan int) {
        defer wg.Done()
        for n := range ch {
            merged <- n
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go forward(ch)
    }

    // Close merged channel when all input channels are done
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}

func gen(nums ...int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for _, n := range nums {
            out <- n
        }
    }()
    return out
}

func main() {
    in := gen(1, 2, 3, 4, 5, 6, 7, 8)

    // Fan-out to 3 workers — NOTE: each worker reads from SAME channel
    // Go handles the distribution: each item goes to one worker
    c1, c2, c3 := make(chan int), make(chan int), make(chan int)
    
    // Simpler: single input channel shared among workers
    shared := gen(1, 2, 3, 4, 5, 6, 7, 8)
    var wg sync.WaitGroup
    results := make(chan int, 8)
    
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for n := range shared {
                results <- n * n
            }
        }()
    }
    
    go func() { wg.Wait(); close(results) }()
    
    for r := range results {
        fmt.Print(r, " ")
    }
    fmt.Println()
    
    _ = in; _ = c1; _ = c2; _ = c3
}
```

### 16.3 Worker Pool Pattern

Control the number of concurrent goroutines. Essential for limiting resource usage.

```
WORKER POOL
============

Jobs Queue     Workers (N)      Results Queue
──────────     ───────────      ─────────────
[job1]                          
[job2]  ──►   [worker1]  ──►   [result1]
[job3]         [worker2]  ──►   [result2]
[job4]  ──►   [worker3]  ──►   [result3]
[...]          (fixed count)

Unlike fan-out where each job creates a goroutine,
worker pool reuses a FIXED number of goroutines.
```

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

type Job struct {
    ID    int
    Input int
}

type Result struct {
    JobID  int
    Output int
}

func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
    defer wg.Done()
    for job := range jobs { // worker loops until jobs channel closed
        fmt.Printf("Worker %d processing job %d\n", id, job.ID)
        time.Sleep(100 * time.Millisecond) // simulate work
        results <- Result{
            JobID:  job.ID,
            Output: job.Input * job.Input,
        }
    }
    fmt.Printf("Worker %d exiting\n", id)
}

func main() {
    const numWorkers = 3
    const numJobs = 10

    jobs := make(chan Job, numJobs)
    results := make(chan Result, numJobs)
    var wg sync.WaitGroup

    // Start fixed number of workers
    for w := 1; w <= numWorkers; w++ {
        wg.Add(1)
        go worker(w, jobs, results, &wg)
    }

    // Send jobs
    for j := 1; j <= numJobs; j++ {
        jobs <- Job{ID: j, Input: j}
    }
    close(jobs) // signal: no more jobs

    // Wait for workers, then close results
    go func() {
        wg.Wait()
        close(results)
    }()

    // Collect results
    for r := range results {
        fmt.Printf("Job %d → Result: %d\n", r.JobID, r.Output)
    }
}
```

### 16.4 Done Channel / Cancellation Pattern

```go
package main

import (
    "fmt"
    "time"
)

// generator that respects done signal
func naturals(done <-chan struct{}) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for i := 0; ; i++ {
            select {
            case out <- i:
            case <-done:
                fmt.Println("generator: cancelled")
                return
            }
        }
    }()
    return out
}

func main() {
    done := make(chan struct{})

    nums := naturals(done)

    // Consume 5 numbers
    for i := 0; i < 5; i++ {
        fmt.Println(<-nums)
    }

    // Cancel
    close(done) // broadcast to ALL receivers via close

    time.Sleep(10 * time.Millisecond)
    fmt.Println("Main: done")
}
```

### 16.5 Semaphore Pattern (Limiting Concurrency)

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// Semaphore using a buffered channel
// Only N goroutines can proceed at once
type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(Semaphore, n)
}

func (s Semaphore) Acquire() { s <- struct{}{} }  // blocks if full
func (s Semaphore) Release() { <-s }               // frees one slot

func main() {
    sem := NewSemaphore(3) // at most 3 concurrent
    var wg sync.WaitGroup

    for i := 0; i < 10; i++ {
        wg.Add(1)
        i := i
        go func() {
            defer wg.Done()
            sem.Acquire()
            defer sem.Release()
            
            fmt.Printf("Task %d running\n", i)
            time.Sleep(500 * time.Millisecond)
            fmt.Printf("Task %d done\n", i)
        }()
    }

    wg.Wait()
    fmt.Println("All tasks complete")
}
```

### 16.6 Publish-Subscribe (Pub/Sub) Pattern

```go
package main

import (
    "fmt"
    "sync"
)

type PubSub struct {
    mu          sync.RWMutex
    subscribers map[string][]chan string
}

func NewPubSub() *PubSub {
    return &PubSub{
        subscribers: make(map[string][]chan string),
    }
}

func (ps *PubSub) Subscribe(topic string) <-chan string {
    ps.mu.Lock()
    defer ps.mu.Unlock()
    ch := make(chan string, 10)
    ps.subscribers[topic] = append(ps.subscribers[topic], ch)
    return ch
}

func (ps *PubSub) Publish(topic, msg string) {
    ps.mu.RLock()
    defer ps.mu.RUnlock()
    for _, ch := range ps.subscribers[topic] {
        select {
        case ch <- msg:
        default:
            // subscriber too slow — skip (or use blocking send)
        }
    }
}

func main() {
    ps := NewPubSub()

    sub1 := ps.Subscribe("news")
    sub2 := ps.Subscribe("news")
    sub3 := ps.Subscribe("sports")

    var wg sync.WaitGroup
    for i, sub := range []<-chan string{sub1, sub2, sub3} {
        wg.Add(1)
        i, sub := i, sub
        go func() {
            defer wg.Done()
            msg := <-sub
            fmt.Printf("Subscriber %d got: %s\n", i, msg)
        }()
    }

    ps.Publish("news", "Breaking: Go 2 released!")
    ps.Publish("sports", "Team wins championship!")

    wg.Wait()
}
```

### 16.7 Rate Limiter Pattern

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    requests := make(chan int, 10)
    for i := 1; i <= 10; i++ {
        requests <- i
    }
    close(requests)

    // Basic rate limiter: 1 request per 200ms
    limiter := time.Tick(200 * time.Millisecond)

    for req := range requests {
        <-limiter // block until tick
        fmt.Println("Request", req, "at", time.Now().Format("15:04:05.000"))
    }

    // Bursty rate limiter: allow bursts of 3, then throttle
    burstyLimiter := make(chan time.Time, 3)
    
    // Pre-fill with 3 tokens (allow initial burst)
    for i := 0; i < 3; i++ {
        burstyLimiter <- time.Now()
    }
    
    // Replenish 1 token per 200ms
    go func() {
        for t := range time.Tick(200 * time.Millisecond) {
            burstyLimiter <- t
        }
    }()

    requests2 := make(chan int, 10)
    for i := 1; i <= 10; i++ {
        requests2 <- i
    }
    close(requests2)

    for req := range requests2 {
        <-burstyLimiter
        fmt.Println("Bursty request", req, "at", time.Now().Format("15:04:05.000"))
    }
}
```

### 16.8 Future/Promise Pattern

```go
package main

import (
    "fmt"
    "time"
)

// Future represents a value that will be available later
type Future[T any] struct {
    ch <-chan T
}

func NewFuture[T any](fn func() T) *Future[T] {
    ch := make(chan T, 1) // buffered: sender doesn't block even if no receiver yet
    go func() {
        ch <- fn()
    }()
    return &Future[T]{ch: ch}
}

func (f *Future[T]) Await() T {
    return <-f.ch
}

func expensiveComputation(n int) int {
    time.Sleep(time.Duration(n) * 100 * time.Millisecond)
    return n * n
}

func main() {
    // Start computations asynchronously
    f1 := NewFuture(func() int { return expensiveComputation(5) })
    f2 := NewFuture(func() int { return expensiveComputation(3) })
    f3 := NewFuture(func() int { return expensiveComputation(7) })

    // Await results (all running concurrently!)
    r1 := f1.Await()
    r2 := f2.Await()
    r3 := f3.Await()

    fmt.Printf("Results: %d, %d, %d\n", r1, r2, r3) // 25, 9, 49
    fmt.Printf("Sum: %d\n", r1+r2+r3)
}
```

---

## 17. Race Conditions: Detection and Prevention

### What is a Race Condition?

A race condition occurs when **two goroutines access shared data concurrently**, and at least one access is a write, and they are not synchronized.

```
RACE CONDITION EXAMPLE
=======================

Shared variable: balance = 100

G1 (deposit 50):             G2 (deposit 50):
  READ:  tmp1 = balance=100    READ:  tmp2 = balance=100
  ADD:   tmp1 = 100+50=150     ADD:   tmp2 = 100+50=150
  WRITE: balance = 150         WRITE: balance = 150

Expected: balance = 200
Actual:   balance = 150   ← LOST UPDATE! One deposit vanished!

The two goroutines "raced" to update balance.
The winner (last writer) sets the value — the loser's work is lost.
```

### Go's Race Detector

Go ships with a built-in race detector based on ThreadSanitizer:

```bash
# Run with race detector
go run -race main.go
go test -race ./...
go build -race myapp

# Output example:
# ==================
# WARNING: DATA RACE
# Write at 0x00c0000b4010 by goroutine 7:
#   main.main.func1()
#       /tmp/main.go:12 +0x3c
# 
# Previous read at 0x00c0000b4010 by main goroutine:
#   main.main()
#       /tmp/main.go:18 +0x5e
# ==================
```

```go
package main

import (
    "fmt"
    "sync"
)

// BUGGY — has race condition
func buggyCounter() {
    count := 0
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            count++ // DATA RACE: concurrent read+write
        }()
    }
    wg.Wait()
    fmt.Println("Buggy count:", count) // could be anything < 1000
}

// FIXED — using mutex
func safeCounterMutex() {
    var (
        count int
        mu    sync.Mutex
        wg    sync.WaitGroup
    )
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            mu.Lock()
            count++
            mu.Unlock()
        }()
    }
    wg.Wait()
    fmt.Println("Mutex count:", count) // always 1000
}

// FIXED — using atomic
func safeCounterAtomic() {
    var count int64
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            atomic.AddInt64(&count, 1)
        }()
    }
    wg.Wait()
    fmt.Println("Atomic count:", count) // always 1000
}

// FIXED — using channel (CSP style)
func safeCounterChannel() {
    countCh := make(chan int)
    doneCh := make(chan int)

    // Single goroutine owns the counter
    go func() {
        count := 0
        for range countCh {
            count++
        }
        doneCh <- count
    }()

    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            countCh <- 1
        }()
    }
    wg.Wait()
    close(countCh)
    fmt.Println("Channel count:", <-doneCh) // always 1000
}
```

---

## 18. Deadlocks: Causes and Avoidance

### What is a Deadlock?

All goroutines are permanently blocked — no goroutine can make progress. Go runtime detects all-goroutine deadlocks and panics with: `all goroutines are asleep - deadlock!`

```
DEADLOCK SCENARIOS
==================

1. CHANNEL DEADLOCK (send to unbuffered, no receiver):

   ch := make(chan int)
   ch <- 42    // main goroutine blocks here waiting for receiver
               // but main IS the only goroutine — nobody to receive
   // fatal error: all goroutines are asleep - deadlock!


2. CIRCULAR WAIT (classic deadlock):

   G1 holds Lock1, wants Lock2
   G2 holds Lock2, wants Lock1
   
   G1: Lock1.Lock() ──────────────────────────────► waiting for Lock2
                                                          ▲
   G2: Lock2.Lock() ──────────────────────────────► waiting for Lock1
   
   Neither can proceed. DEADLOCK.


3. FORGOTTEN CLOSE:

   ch := make(chan int)
   go func() { ch <- 1; ch <- 2 }() // sends 2 items but never closes
   for n := range ch { fmt.Println(n) } // range blocks after receiving 2, waiting for more
   // DEADLOCK: range never terminates


4. WRONG WAITGROUP USAGE:

   var wg sync.WaitGroup
   wg.Add(1)
   go func() {
       // forgot wg.Done()
   }()
   wg.Wait() // blocks forever — counter never reaches 0
```

### Deadlock Prevention Rules

```
DEADLOCK PREVENTION CHECKLIST
================================

Channel Rules:
  ✓ Always have a receiver before a sender (or use buffered channel)
  ✓ Always close channels when done sending
  ✓ Never send to a closed channel
  ✓ Avoid circular channel dependencies

Mutex Rules:
  ✓ Lock ordering: always acquire locks in the SAME order
  ✓ Always use defer Unlock() to ensure lock release
  ✓ Minimize lock scope — unlock as soon as possible
  ✓ Never call external functions while holding a lock

WaitGroup Rules:
  ✓ wg.Add() BEFORE launching goroutine
  ✓ wg.Done() inside goroutine (use defer)
  ✓ Count Add/Done calls — they must match exactly

Context Rules:
  ✓ Always cancel contexts (defer cancel())
  ✓ Check ctx.Done() in long-running goroutines
```

```go
package main

import (
    "fmt"
    "sync"
)

// DEADLOCK example with mutex — wrong lock ordering
type Account struct {
    mu      sync.Mutex
    balance int
}

func transferDeadlock(from, to *Account, amount int) {
    from.mu.Lock()
    // if two transfers happen simultaneously:
    // T1: from=A.lock, waiting for B.lock
    // T2: from=B.lock, waiting for A.lock
    // DEADLOCK!
    to.mu.Lock()
    from.balance -= amount
    to.balance += amount
    to.mu.Unlock()
    from.mu.Unlock()
}

// FIXED — lock ordering by address (always lock lower address first)
func transferSafe(a, b *Account, amount int) {
    // Impose consistent lock ordering to prevent circular wait
    first, second := a, b
    if uintptr(second.mu.(unsafe.Pointer)) < uintptr(first.mu.(unsafe.Pointer)) {
        first, second = second, first
    }
    first.mu.Lock()
    defer first.mu.Unlock()
    second.mu.Lock()
    defer second.mu.Unlock()
    
    a.balance -= amount
    b.balance += amount
}

// SIMPLER FIX — use a single global mutex for all transfers
var transferMu sync.Mutex

func transferSimple(from, to *Account, amount int) {
    transferMu.Lock()
    defer transferMu.Unlock()
    from.balance -= amount
    to.balance += amount
}

// CHANNEL-BASED APPROACH — no locks needed
type TransferRequest struct {
    from, to *Account
    amount   int
    done     chan struct{}
}

func accountManager(requests <-chan TransferRequest) {
    for req := range requests {
        req.from.balance -= req.amount
        req.to.balance += req.amount
        close(req.done)
    }
}

func main() {
    a := &Account{balance: 1000}
    b := &Account{balance: 500}
    fmt.Println(a.balance, b.balance)
    
    // Channel approach
    reqCh := make(chan TransferRequest, 10)
    go accountManager(reqCh)
    
    done := make(chan struct{})
    reqCh <- TransferRequest{from: a, to: b, amount: 100, done: done}
    <-done
    
    fmt.Println(a.balance, b.balance) // 900, 600
}
```

---

## 19. Memory Model: Happens-Before

### The Go Memory Model

The **Go Memory Model** defines when one goroutine's write to a variable is **guaranteed to be visible** to another goroutine's read.

**Key concept: Happens-Before**

Operation A *happens-before* operation B means:
- All memory writes visible to A are also visible to B.
- A's effects are ordered before B's.

```
HAPPENS-BEFORE GUARANTEES
===========================

Within a single goroutine:
  All operations happen in the order written (sequential consistency).

Across goroutines — these establish happens-before:
  1. Goroutine creation:
     go f() happens-before f() begins

  2. Channel send/receive (unbuffered):
     ch <- v  happens-before  v := <-ch
     The RECEIVE happens-before the SEND COMPLETES

  3. Channel close:
     close(ch) happens-before receive that returns zero value

  4. Buffered channel:
     The kth receive happens-before the kth send COMPLETES
     (capacity C: receive k h-b send k+C)

  5. sync.Mutex:
     The nth Unlock() happens-before the nth+1 Lock()

  6. sync.WaitGroup:
     wg.Done() happens-before wg.Wait() returns

  7. sync.Once:
     f() in once.Do(f) happens-before once.Do() returns (anywhere)
```

### Practical Example

```go
// SAFE: channel establishes happens-before
var data string
done := make(chan struct{})

go func() {
    data = "hello"    // write
    done <- struct{}{}
}()

<-done        // receive from done happens-after send
fmt.Println(data) // SAFE: data write happens-before here

// UNSAFE: no happens-before guarantee
var unsafeData string
go func() {
    unsafeData = "hello" // write
}()
time.Sleep(1 * time.Second)
fmt.Println(unsafeData) // TECHNICALLY a data race! (even with sleep!)
                        // CPU reordering / compiler reordering can still happen
```

---

## 20. Error Handling in Concurrent Code

### The errgroup Package

`golang.org/x/sync/errgroup` combines WaitGroup with error propagation:

```go
package main

import (
    "context"
    "fmt"
    "net/http"

    "golang.org/x/sync/errgroup"
)

func fetchURL(ctx context.Context, url string) error {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return err
    }
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    fmt.Printf("Fetched %s: %d\n", url, resp.StatusCode)
    return nil
}

func main() {
    urls := []string{
        "https://go.dev",
        "https://pkg.go.dev",
        "https://golang.org",
    }

    // errgroup.WithContext: if ANY goroutine returns error,
    // context is cancelled, all other goroutines get signal
    g, ctx := errgroup.WithContext(context.Background())

    for _, url := range urls {
        url := url
        g.Go(func() error {
            return fetchURL(ctx, url)
        })
    }

    // Wait for all and collect first error
    if err := g.Wait(); err != nil {
        fmt.Println("Error:", err)
        return
    }
    fmt.Println("All fetches successful")
}
```

### Custom Error Channel Pattern

```go
package main

import (
    "errors"
    "fmt"
    "sync"
)

type WorkResult struct {
    ID    int
    Value int
    Err   error
}

func doWork(id int) WorkResult {
    if id == 3 {
        return WorkResult{ID: id, Err: errors.New("work failed for id 3")}
    }
    return WorkResult{ID: id, Value: id * id}
}

func main() {
    const numTasks = 7
    results := make(chan WorkResult, numTasks)
    var wg sync.WaitGroup

    for i := 0; i < numTasks; i++ {
        wg.Add(1)
        i := i
        go func() {
            defer wg.Done()
            results <- doWork(i)
        }()
    }

    go func() { wg.Wait(); close(results) }()

    var errs []error
    for r := range results {
        if r.Err != nil {
            errs = append(errs, r.Err)
        } else {
            fmt.Printf("Task %d: %d\n", r.ID, r.Value)
        }
    }

    if len(errs) > 0 {
        fmt.Printf("%d errors occurred:\n", len(errs))
        for _, err := range errs {
            fmt.Println(" -", err)
        }
    }
}
```

---

## 21. Testing Concurrent Code

### Using `-race` Flag

```bash
# Always run tests with race detector during development
go test -race ./...
go test -race -count=10 ./...  # run 10 times to catch rare races
```

### Table-Driven Concurrent Tests

```go
package main

import (
    "sync"
    "testing"
)

func TestSafeCounter(t *testing.T) {
    tests := []struct {
        name      string
        goroutines int
        expected  int
    }{
        {"single goroutine", 1, 1},
        {"ten goroutines", 10, 10},
        {"thousand goroutines", 1000, 1000},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            counter := &SafeCounter{}
            var wg sync.WaitGroup

            for i := 0; i < tt.goroutines; i++ {
                wg.Add(1)
                go func() {
                    defer wg.Done()
                    counter.Increment()
                }()
            }
            wg.Wait()

            if got := counter.Value(); got != tt.expected {
                t.Errorf("expected %d, got %d", tt.expected, got)
            }
        })
    }
}

// Testing with channels — use timeouts to avoid hanging tests
func TestChannel(t *testing.T) {
    ch := make(chan int)
    
    go func() {
        ch <- 42
    }()

    select {
    case val := <-ch:
        if val != 42 {
            t.Errorf("expected 42, got %d", val)
        }
    case <-time.After(1 * time.Second):
        t.Error("test timed out waiting for channel")
    }
}
```

---

## 22. Performance Tuning and GOMAXPROCS

### GOMAXPROCS — Controlling Parallelism

```go
package main

import (
    "fmt"
    "runtime"
)

func main() {
    // Query current GOMAXPROCS
    current := runtime.GOMAXPROCS(0)  // 0 = query without changing
    fmt.Println("CPU cores:", runtime.NumCPU())
    fmt.Println("GOMAXPROCS:", current) // defaults to runtime.NumCPU() since Go 1.5

    // Set to 1 (single-threaded concurrency, no parallelism)
    runtime.GOMAXPROCS(1)

    // Set to all CPUs (default)
    runtime.GOMAXPROCS(runtime.NumCPU())

    // Also settable via environment variable:
    // GOMAXPROCS=4 ./myapp
}
```

### Profiling Concurrent Programs

```go
package main

import (
    _ "net/http/pprof" // import for side effects — registers /debug/pprof endpoints
    "net/http"
    "runtime"
)

func init() {
    // Enable block profiling (goroutine blocking events)
    runtime.SetBlockProfileRate(1)
    // Enable mutex profiling
    runtime.SetMutexProfileFraction(1)
}

func main() {
    // Expose pprof endpoints
    go func() {
        http.ListenAndServe("localhost:6060", nil)
    }()

    // Your program logic...
    
    // Profile goroutines: go tool pprof http://localhost:6060/debug/pprof/goroutine
    // Profile blocking:   go tool pprof http://localhost:6060/debug/pprof/block
    // Profile mutexes:    go tool pprof http://localhost:6060/debug/pprof/mutex
}
```

### Number of Goroutines Monitoring

```go
package main

import (
    "fmt"
    "runtime"
    "time"
)

func main() {
    // Monitor goroutine count
    go func() {
        for {
            fmt.Printf("Goroutines: %d\n", runtime.NumGoroutine())
            time.Sleep(1 * time.Second)
        }
    }()

    // ... rest of program
    time.Sleep(5 * time.Second)
}
```

---

## 23. Mental Models and Expert Thinking

### The Four Questions Before Concurrency

Before writing concurrent code, an expert asks:

```
EXPERT'S CONCURRENCY DECISION TREE
=====================================

1. DO I NEED CONCURRENCY AT ALL?
   └── Is there a simpler sequential solution?
       Sequential code is always easier to reason about.

2. WHAT IS THE DATA FLOW?
   └── Who creates data? Who consumes it? Who transforms it?
       Draw the pipeline before writing any code.

3. WHO OWNS WHAT?
   └── For each piece of shared state: which goroutine owns it?
       Channel direction enforces this at compile time.

4. WHAT CAN GO WRONG?
   └── Where can goroutines block?
       Where is there shared state? → race conditions
       Are there circular dependencies? → deadlocks
       Can any goroutine leak? → goroutine leak
```

### The Channel vs Mutex Decision

```
CHANNEL vs MUTEX: HOW TO DECIDE
================================

Use CHANNELS when:
  ┌─────────────────────────────────────────────────────┐
  │ • Transferring data ownership between goroutines    │
  │ • Distributing units of work                        │
  │ • Communicating async results                       │
  │ • Signaling events (done, quit, error)              │
  │ • Building pipelines                                │
  │ • The problem is naturally producer-consumer        │
  └─────────────────────────────────────────────────────┘

Use MUTEXES when:
  ┌─────────────────────────────────────────────────────┐
  │ • Protecting a shared data structure (map, slice)   │
  │ • Simple state flags (ready bool, count int)        │
  │ • High-frequency, short critical sections           │
  │ • Caching / memoization                             │
  │ • The shared data has multiple readers (RWMutex)    │
  └─────────────────────────────────────────────────────┘

Heuristic: Channels model BEHAVIOR. Mutexes protect STATE.
```

### Goroutine Leak Prevention

A goroutine leak is when a goroutine is created but **never terminates** — it just sits there consuming memory forever.

```
GOROUTINE LEAK PATTERNS AND FIXES
===================================

LEAK 1: Goroutine blocked on channel send (no receiver)
   go func() {
       ch <- result  // nobody receives → blocked forever
   }()
   
   FIX: Use buffered channel, or ensure receiver always runs.

LEAK 2: Goroutine blocked on channel receive (no sender)
   go func() {
       val := <-ch  // nobody sends → blocked forever
   }()
   
   FIX: Ensure sender always closes channel.

LEAK 3: Goroutine running infinite loop without exit condition
   go func() {
       for {
           // no quit signal → runs forever
       }
   }()
   
   FIX: Add done/quit channel with select.

DETECTION:
   runtime.NumGoroutine() — if this grows indefinitely, you have a leak.
   goleak package: checks goroutines in tests.
```

```go
// goleak usage in tests
package main

import (
    "testing"
    "go.uber.org/goleak"
)

func TestNoLeaks(t *testing.T) {
    defer goleak.VerifyNone(t) // fails test if goroutines leaked after test
    
    // Your test code here
    // goleak will report any goroutines that didn't terminate
}
```

### The Complete Mental Model Map

```
GO CONCURRENCY — COMPLETE MENTAL MODEL
=========================================

         PROBLEM SPACE
              │
    ┌─────────┴──────────┐
    │                    │
I/O BOUND           CPU BOUND
    │                    │
Many goroutines     GOMAXPROCS goroutines
waiting for I/O     actually parallel
    │                    │
    └─────────┬──────────┘
              │
         COORDINATION
              │
    ┌─────────┼─────────┐
    │         │         │
CHANNELS   MUTEXES   ATOMICS
    │         │         │
Transfer   Protect   Simple
ownership  state     counters/flags
    │
    ├── Unbuffered (sync rendezvous)
    ├── Buffered (async, rate matching)
    └── Directional (type safety)

         PATTERNS
              │
    ┌────────┬┴──────────┬──────────┐
    │        │           │          │
Pipeline  Worker     Fan-Out/   Pub-Sub
          Pool       Fan-In
    
         LIFECYCLE MANAGEMENT
              │
    ┌─────────┴─────────┐
    │                   │
  context            WaitGroup
  (cancellation)     (completion)
    │                   │
  WithCancel         Add/Done/Wait
  WithTimeout
  WithDeadline
  WithValue

         SAFETY NET
              │
    ┌─────────┼─────────┐
    │         │         │
go -race  goleak   pprof
(data races) (goroutine leaks) (profiling)
```

---

## Complete Real-World Example: Concurrent Web Scraper

This example uses goroutines, channels, context, WaitGroup, and multiple patterns together:

```go
package main

import (
    "context"
    "fmt"
    "math/rand"
    "sync"
    "time"
)

// ─── Types ───────────────────────────────────────────────────────────────────

type URL = string

type ScrapeResult struct {
    URL     URL
    Content string
    Err     error
}

// ─── Scraper Worker ──────────────────────────────────────────────────────────

func scrapeWorker(ctx context.Context, id int, jobs <-chan URL, results chan<- ScrapeResult, wg *sync.WaitGroup) {
    defer wg.Done()
    for {
        select {
        case url, ok := <-jobs:
            if !ok {
                fmt.Printf("Worker %d: job queue closed, exiting\n", id)
                return
            }
            result := scrapeURL(ctx, url)
            select {
            case results <- result:
            case <-ctx.Done():
                fmt.Printf("Worker %d: context cancelled\n", id)
                return
            }
        case <-ctx.Done():
            fmt.Printf("Worker %d: context cancelled\n", id)
            return
        }
    }
}

// ─── Simulate HTTP scraping ───────────────────────────────────────────────────

func scrapeURL(ctx context.Context, url URL) ScrapeResult {
    // Simulate variable latency
    delay := time.Duration(rand.Intn(500)) * time.Millisecond
    
    select {
    case <-time.After(delay):
        if rand.Float32() < 0.1 { // 10% failure rate
            return ScrapeResult{URL: url, Err: fmt.Errorf("timeout scraping %s", url)}
        }
        return ScrapeResult{URL: url, Content: fmt.Sprintf("content of %s", url)}
    case <-ctx.Done():
        return ScrapeResult{URL: url, Err: ctx.Err()}
    }
}

// ─── Rate Limited URL Dispatcher ──────────────────────────────────────────────

func dispatch(ctx context.Context, urls []URL, rateLimit time.Duration) <-chan URL {
    jobs := make(chan URL, len(urls))
    
    go func() {
        defer close(jobs)
        ticker := time.NewTicker(rateLimit)
        defer ticker.Stop()
        
        for _, url := range urls {
            select {
            case <-ticker.C:
                select {
                case jobs <- url:
                case <-ctx.Done():
                    return
                }
            case <-ctx.Done():
                return
            }
        }
    }()
    
    return jobs
}

// ─── Result Aggregator ────────────────────────────────────────────────────────

type Stats struct {
    Total   int
    Success int
    Failed  int
}

func aggregate(results <-chan ScrapeResult) ([]ScrapeResult, Stats) {
    var (
        all   []ScrapeResult
        stats Stats
    )
    for r := range results {
        all = append(all, r)
        stats.Total++
        if r.Err != nil {
            stats.Failed++
        } else {
            stats.Success++
        }
    }
    return all, stats
}

// ─── Main Orchestrator ────────────────────────────────────────────────────────

func main() {
    // Configuration
    const (
        numWorkers = 5
        timeout    = 3 * time.Second
        rateLimit  = 50 * time.Millisecond  // 20 requests/second max
    )

    urls := []URL{
        "https://example.com/1", "https://example.com/2",
        "https://example.com/3", "https://example.com/4",
        "https://example.com/5", "https://example.com/6",
        "https://example.com/7", "https://example.com/8",
        "https://example.com/9", "https://example.com/10",
    }

    // Context with overall timeout
    ctx, cancel := context.WithTimeout(context.Background(), timeout)
    defer cancel()

    // Pipeline:
    //   dispatch (rate-limited) → jobs channel
    //   jobs channel → N workers (fan-out)
    //   workers → results channel (fan-in)
    //   results → aggregate

    jobs := dispatch(ctx, urls, rateLimit)
    results := make(chan ScrapeResult, len(urls))

    var wg sync.WaitGroup
    for i := 1; i <= numWorkers; i++ {
        wg.Add(1)
        go scrapeWorker(ctx, i, jobs, results, &wg)
    }

    // Close results when all workers done
    go func() {
        wg.Wait()
        close(results)
    }()

    // Collect results
    all, stats := aggregate(results)

    // Report
    fmt.Printf("\n═══ Scraping Complete ═══\n")
    fmt.Printf("Total:   %d\n", stats.Total)
    fmt.Printf("Success: %d\n", stats.Success)
    fmt.Printf("Failed:  %d\n", stats.Failed)
    
    for _, r := range all {
        if r.Err != nil {
            fmt.Printf("  ✗ %s: %v\n", r.URL, r.Err)
        } else {
            fmt.Printf("  ✓ %s\n", r.URL)
        }
    }
}
```

---

## Quick Reference: Concurrency Patterns Cheat Sheet

```
PATTERN             │ USE CASE                          │ KEY TOOL
────────────────────┼───────────────────────────────────┼────────────────────
Pipeline            │ Data transformation stages        │ Channels + goroutines
Worker Pool         │ Limit concurrent work             │ Buffered channel + WaitGroup
Fan-Out             │ Parallel processing               │ Multiple goroutines, 1 input ch
Fan-In              │ Merge multiple sources            │ WaitGroup closes merged channel
Done Channel        │ Cancellation broadcast            │ close(done) + select
Rate Limiter        │ Throttle request rate             │ time.Tick + buffered channel
Semaphore           │ Limit concurrency by N            │ Buffered channel capacity
Future/Promise      │ Async computation                 │ Buffered channel + goroutine
Pub/Sub             │ Event broadcasting                │ Map of subscriber channels
Timeout             │ Give up after duration            │ select + time.After
Heartbeat           │ Health check goroutines           │ Timed channel sends
Retry               │ Resilient operations              │ Loop + backoff + context

SYNCHRONIZATION     │ USE CASE                          │ KEY TOOL
────────────────────┼───────────────────────────────────┼────────────────────
Completion Wait     │ Wait for N goroutines             │ sync.WaitGroup
Mutual Exclusion    │ Protect shared state              │ sync.Mutex
Read-Heavy State    │ Many readers, few writers         │ sync.RWMutex
One-Time Init       │ Singleton, lazy init              │ sync.Once
Object Reuse        │ Reduce GC pressure                │ sync.Pool
Simple Counter      │ Atomic increment/decrement        │ sync/atomic
Lifecycle Mgmt      │ Cancellation + deadlines          │ context.Context
```

---

## Closing: The Zen of Go Concurrency

```
THE THREE PILLARS
=================

1. Don't communicate by sharing memory.
   Share memory by communicating.
   → Prefer channels over mutexes for data ownership transfer.

2. Make the zero value useful.
   → var ch chan int is nil (never use without make())
   → var wg sync.WaitGroup is ready to use
   → var mu sync.Mutex is ready (unlocked) to use

3. Design for failure.
   → Every goroutine needs an exit condition.
   → Every channel needs an owner responsible for closing.
   → Every context must be cancelled.
   → Always check for errors from concurrent operations.


EXPERT'S MANTRA:
================
  "Which goroutine is responsible for this channel?"
  "How does this goroutine know when to stop?"
  "What is the order of happens-before here?"
  "Where can this deadlock?"
  "Where can this leak?"

Answer these five questions for every concurrent function you write,
and you will write correct concurrent code.
```

---

*Guide complete. Build with clarity. Ship with confidence.*

Here is the complete guide. Here's what's covered across all 23 sections:

**Foundations**
- Precise definitions of every term (concurrency, parallelism, goroutine, channel, deadlock, livelock, etc.)
- ASCII diagrams showing concurrency vs parallelism on CPU timelines
- Why goroutines are 100–1000x cheaper than OS threads

**The Scheduler (GMP Model)**
- Every entity (G, M, P) explained with a full ASCII architecture diagram
- Work stealing: how idle CPUs steal goroutines from busy ones
- How blocking syscalls are handled without freezing the runtime
- Go 1.14+ asynchronous preemption via signals

**Goroutines In-Depth**
- Full lifecycle state machine (Runnable → Running → Waiting → Dead)
- The classic closure capture trap and two correct fixes
- Stack growth mechanics (2KB → dynamic growth)
- Escape analysis (stack vs heap)

**Channels — Every Nuance**
- Complete operation truth table (nil, empty, full, closed — all combinations)
- Unbuffered rendezvous mechanics step-by-step
- Buffered channel FIFO mechanics
- Directional types (`chan<-`, `<-chan`) for compile-time ownership enforcement
- `select` statement — multiplexing, timeouts, `default`, nil channel disabling

**sync & atomic Packages** — WaitGroup, Mutex, RWMutex, Once, Cond, Pool, all atomic operations

**context Package** — Full tree propagation diagram, production HTTP handler pattern

**8 Production Patterns** — Pipeline, Fan-Out/Fan-In, Worker Pool, Semaphore, Pub/Sub, Rate Limiter, Future/Promise, Done Channel

**Safety** — Race detector usage, deadlock causes + prevention checklist, happens-before memory model, goroutine leak patterns

**Complete Real-World Example** — A concurrent rate-limited web scraper using every concept together