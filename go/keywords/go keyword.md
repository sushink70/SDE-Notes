# Comprehensive Guide to Goroutines and the `go` Keyword in Go

> **Philosophy:** Before writing concurrent code, understand the machine beneath it.
> Every abstraction in Go's concurrency model maps to a real kernel, CPU, and memory bus behavior.
> This guide peels back every layer — from the GMP scheduler internals to production-hardened patterns.

---

## Table of Contents

1. [The Problem: Why Concurrency?](#1-the-problem-why-concurrency)
2. [OS Threads vs Goroutines — The Fundamental Difference](#2-os-threads-vs-goroutines)
3. [The GMP Scheduler — Go's Runtime Heart](#3-the-gmp-scheduler)
4. [The `go` Keyword — What Actually Happens](#4-the-go-keyword)
5. [Goroutine Stack — Growable and Segmented](#5-goroutine-stack)
6. [Goroutine Lifecycle — State Machine](#6-goroutine-lifecycle)
7. [Channels — Communication Primitive](#7-channels)
8. [Select Statement — Non-Deterministic Multiplexing](#8-select-statement)
9. [sync Package — Low-Level Primitives](#9-sync-package)
10. [sync/atomic — Lock-Free Operations](#10-syncatomic)
11. [Context Package — Cancellation and Deadlines](#11-context-package)
12. [Concurrency Patterns — Production Blueprints](#12-concurrency-patterns)
13. [Goroutine Leaks — Detection and Prevention](#13-goroutine-leaks)
14. [Race Conditions and the Memory Model](#14-race-conditions-and-memory-model)
15. [Performance Characteristics — Hardware Reality](#15-performance-characteristics)
16. [Production Tips and Tricks](#16-production-tips-and-tricks)
17. [Common Pitfalls — What Experts Avoid](#17-common-pitfalls)

---

## 1. The Problem: Why Concurrency?

Before any code, you must understand *why* the problem exists.

Modern hardware has multiple CPU cores that can execute instructions simultaneously. A single-threaded
program uses only **one core at a time**, leaving the rest idle. Concurrency is the art of
structuring a program so that multiple computations can overlap — either:

- **Truly in parallel** (multiple cores executing simultaneously), or
- **Interleaved** (one core switching between tasks, especially when tasks are waiting for I/O)

### The Two Types of Waiting

```
CPU-Bound work:         I/O-Bound work:
  [CPU computing]         [CPU sends request]
  [CPU computing]         [  ........waiting........ ]  <-- CPU sits idle
  [CPU computing]         [CPU gets response]
  [CPU computing]         [CPU processes response]
```

For **CPU-bound** tasks: You need true parallelism (multiple goroutines on multiple cores).
For **I/O-bound** tasks: You need concurrency (one core handles thousands of waiting operations).

Go's goroutine model handles **both** efficiently. This is its superpower.

---

## 2. OS Threads vs Goroutines

### What is an OS Thread?

An OS thread is a unit of execution managed by the **operating system kernel**. When you create a
thread, the OS:

1. Allocates a **fixed-size stack** (typically 1MB–8MB on Linux)
2. Registers the thread in the kernel's scheduler
3. Manages context switching (saving/restoring CPU registers: ~100–1000 ns per switch)

### What is a Goroutine?

A goroutine is a unit of execution managed by **Go's runtime** (not the OS kernel).

```
                    +----------------------------------+
                    |         Go Program               |
                    |                                  |
                    |  goroutine  goroutine  goroutine  |
                    |  goroutine  goroutine  goroutine  |
                    |  goroutine  goroutine  goroutine  |
                    |         (thousands)              |
                    +----------------------------------+
                    |         Go Runtime               |
                    |      (GMP Scheduler)             |
                    +----------------------------------+
                    |         OS Threads               |
                    |    [M1]  [M2]  [M3]  [M4]        |
                    +----------------------------------+
                    |    Operating System Kernel       |
                    +----------------------------------+
                    |  CPU0  CPU1  CPU2  CPU3           |
                    +----------------------------------+
```

This is called **M:N threading** — M goroutines mapped onto N OS threads.

### Side-by-Side Comparison

| Property              | OS Thread                    | Goroutine                    |
|-----------------------|------------------------------|------------------------------|
| Stack size (initial)  | 1MB – 8MB (fixed)            | 2KB – 8KB (dynamic, growable)|
| Stack size (max)      | Fixed at creation            | 1GB (default, configurable)  |
| Creation cost         | ~10–100 µs (syscall)         | ~0.3 µs (no syscall)         |
| Context switch cost   | ~1–2 µs (kernel involvement) | ~100–200 ns (user-space)     |
| Managed by            | OS Kernel                    | Go Runtime                   |
| Scheduling            | Preemptive (by kernel)       | Cooperative + Preemptive     |
| Communication         | Shared memory + locks        | Channels (+ shared memory)   |
| Typical max count     | ~10,000 (memory-limited)     | ~1,000,000+ (2KB stacks)     |

### Why Does Initial Stack Size Matter?

```
OS Thread model (1MB per thread):
  1000 threads × 1MB = 1GB RAM just for stacks!

Goroutine model (2KB initial):
  1,000,000 goroutines × 2KB = 2GB (before growth)
  But most goroutines use very little stack → much less in practice
```

The 2KB initial stack is critical for Go's ability to run **hundreds of thousands** of goroutines
concurrently — enabling server models where each connection gets its own goroutine.

---

## 3. The GMP Scheduler

This is the most important internal model to understand. The GMP scheduler is implemented in
`runtime/proc.go` in Go's source.

### The Three Components

**G — Goroutine**
- Represents a goroutine (user-level thread of execution)
- Contains: stack, program counter, goroutine status, channel wait info
- Defined as `runtime.g` struct in the Go runtime

**M — Machine (OS Thread)**
- Represents an OS thread
- There is one M per real OS thread
- M executes goroutines by running their code on the CPU
- Defined as `runtime.m` struct

**P — Processor (Logical Processor)**
- A scheduling context — a resource required by M to execute Go code
- Contains a **local run queue** of goroutines ready to run
- Count is set by `GOMAXPROCS` (default: number of CPU cores)
- Defined as `runtime.p` struct
- **Key insight:** M needs a P to run Go code. Without a P, M is idle or blocked on syscall.

### GMP Architecture Diagram

```
  GOMAXPROCS=4 (4 logical processors)

  +--------+    +--------+    +--------+    +--------+
  |   P0   |    |   P1   |    |   P2   |    |   P3   |
  |--------|    |--------|    |--------|    |--------|
  | LRQ:   |    | LRQ:   |    | LRQ:   |    | LRQ:   |
  | [G3]   |    | [G6]   |    | [G9]   |    | [G12]  |
  | [G4]   |    | [G7]   |    | [G10]  |    | [G13]  |
  | [G5]   |    | [G8]   |    | [G11]  |    |        |
  |--------|    |--------|    |--------|    |--------|
  | M1 [G1]|    | M2 [G2]|    | M3 [G...]  | M4 idle|
  +--------+    +--------+    +--------+    +--------+
       |              |
  [executing]   [executing]

  Global Run Queue (GRQ): [G14] [G15] [G16] ...
  (overflow from local queues, or freshly spawned goroutines)
```

**Key Rules:**
- Each P has a **Local Run Queue (LRQ)** of up to 256 goroutines
- There is one **Global Run Queue (GRQ)** shared by all Ps
- An M can only run Go code when it has a P attached
- A syscall-blocking M releases its P so another M can use it

### Work Stealing — Load Balancing

When a P's local queue is empty, it doesn't sit idle. It **steals** work:

```
  P0 (empty)            P3 (busy: 8 goroutines in LRQ)
  +--------+            +--------+
  | LRQ:[] |            | LRQ:   |
  |        |  STEAL     | [G1]   |
  |  <----------+       | [G2]   |
  |        |   steal    | [G3]   |
  |        |   half     | [G4]   |   <-- P0 steals G5, G6, G7, G8
  |        |            | [G5]   |       (half of P3's queue)
  +--------+            | [G6]   |
                        | [G7]   |
                        | [G8]   |
                        +--------+

  After stealing:
  P0 LRQ: [G5][G6][G7][G8]     P3 LRQ: [G1][G2][G3][G4]
```

Work stealing algorithm (from `runtime/proc.go`):
1. Check own LRQ
2. Check GRQ (every 61st check to avoid starvation)
3. Check network poller (goroutines woken by netpoll)
4. Steal from another random P

### Syscall Handling — How Blocking I/O Works

When a goroutine makes a **blocking syscall** (e.g., reading a file):

```
  Before syscall:
  +--------+
  |   P0   |
  | M1 [G1]| --- G1 calls blocking read()
  +--------+

  During syscall (Go detects this via syscall wrapper):
  +--------+
  |   P0   | <-- P0 detaches from M1 (now "floating")
  | M2 [G2]| <-- P0 attaches to idle M2 (or creates new M)
  +--------+

  M1 still executing: blocked in kernel for read()
  M1 [G1 blocking in kernel] -- no P, cannot run Go code

  After syscall returns:
  - M1 tries to reclaim a P
  - If no P available: G1 put on GRQ, M1 goes to idle pool
  - If P available: M1 reclaims P, continues running G1
```

This is why **blocking syscalls don't block the entire program** in Go.
The scheduler hands off the P to a new/idle OS thread.

### Preemption — Ensuring Fairness

Go uses **asynchronous preemption** (since Go 1.14). Every 10ms, the runtime sends
a `SIGURG` signal to OS threads running goroutines. This forces a preemption point,
even in tight loops with no function calls.

```go
// Before Go 1.14: this could starve other goroutines
// After Go 1.14: preempted by SIGURG signal after ~10ms
for {
    // tight loop — signal handler will interrupt this
}
```

Before 1.14, preemption only happened at **safe points** (function call preambles).
Now it's truly preemptive, similar to OS thread scheduling.

---

## 4. The `go` Keyword

### Syntax

```go
go functionCall()
go func() { ... }()
go obj.Method()
```

The `go` keyword does **exactly one thing**: it creates a new goroutine and schedules it.
The calling goroutine continues immediately without waiting.

### What Happens Internally When You Write `go f()`

```
Source code:    go f(arg1, arg2)

Step 1: ARGUMENT EVALUATION (in calling goroutine's stack)
        arg1 and arg2 are evaluated NOW in the current goroutine.
        This is crucial — arguments are evaluated before the goroutine starts.

Step 2: GOROUTINE CREATION (newproc in runtime)
        - Allocate a new G struct
        - Allocate initial stack (2KB on 64-bit, grown from StackMin=2048 bytes)
        - Copy function pointer and evaluated args onto new goroutine's stack
        - Set PC (program counter) to the function entry point
        - Set status to _Grunnable

Step 3: SCHEDULING
        - Try to put on current P's local run queue
        - If LRQ is full (256 items), put half on GRQ
        - If available, wake an idle P/M pair to run it
```

### Argument Evaluation — Critical Detail

```go
package main

import (
    "fmt"
    "time"
)

func main() {
    x := 10

    // WRONG mental model: thinks x is captured by reference
    // CORRECT: x is EVALUATED now, its value (10) is passed to goroutine
    go fmt.Println(x) // passes 10, not a reference to x

    x = 20 // changing x does NOT affect the goroutine above

    // But closures capture by reference:
    go func() {
        fmt.Println(x) // might print 20 or anything — captures &x
    }()

    time.Sleep(time.Millisecond)
}
```

This is one of the most common goroutine bugs. Arguments to `go f(args)` are evaluated
**immediately** in the calling goroutine. But closure variables are captured **by reference**.

### The `go` Keyword Has No Return Value

```go
// You cannot do:
result := go compute() // COMPILE ERROR

// You must communicate via channels:
ch := make(chan int)
go func() {
    ch <- compute()
}()
result := <-ch
```

### go + Anonymous Function (Closure) Pattern

```go
// Common pattern: immediately invoked goroutine closure
go func(id int) {
    // id is passed as argument (by value) — safe
    fmt.Printf("goroutine %d\n", id)
}(42) // 42 is evaluated now, passed as id

// Loop variable capture (classic bug):
for i := 0; i < 5; i++ {
    // BUG: all goroutines may print 5
    go func() { fmt.Println(i) }()
}

// FIX 1: pass as argument
for i := 0; i < 5; i++ {
    go func(n int) { fmt.Println(n) }(i)
}

// FIX 2 (Go 1.22+): loop variable semantics changed — each iteration gets its own i
// In Go 1.22+, the above bug is fixed by the language spec
```

---

## 5. Goroutine Stack

### Growable Stacks (Contiguous)

Go goroutines start with a small stack (2KB) that **grows and shrinks** dynamically.
This is implemented using **contiguous stacks** (since Go 1.4, replacing the older segmented stack model).

```
Initial goroutine stack:
  +------------------+  <- top (high address)
  | stack guard      |  (triggers growth detection)
  +------------------+
  |                  |
  |   function       |
  |   frames         |
  |                  |
  +------------------+  <- SP (stack pointer, grows down)
  |   (free space)   |
  +------------------+  <- bottom (low address)

  2KB total initially
```

### Stack Growth Mechanism

Every function preamble (generated by the compiler) checks if the stack has enough room:

```
Assembly pseudo-code at function entry:
  CMPQ SP, stackguard0  ; compare stack pointer with guard
  JBE  morestack        ; if SP <= guard, call runtime.morestack
  ; ... function body ...
```

When `runtime.morestack` is called:
1. Allocate a **new, larger stack** (typically 2× the current size)
2. **Copy all frames** from old stack to new stack
3. **Update all pointers** (stack pointers, return addresses) to point to new locations
4. Free old stack
5. Continue execution

```
Stack growth:
  Before:                  After growth:
  [2KB stack]     -->      [4KB stack, old data copied]
  [frame1]                 [frame1]
  [frame2]                 [frame2]
  [frame3]  <overflow>     [frame3]
                           [frame4] <-- now fits
```

**Why this matters for performance:**
- Stack copying has a cost (all pointers must be updated)
- **Interior pointers to stack** are not allowed in Go (GC would need to update them)
- Avoid creating huge stack frames in hot paths (triggers growth/shrink thrashing)

### Stack Shrinking

After garbage collection, if a goroutine's stack is using less than 1/4 of its allocated space,
the runtime shrinks it. This prevents memory bloat from goroutines that had temporary large stacks.

```
Stack shrink trigger: usage < 1/4 of allocated
  [8KB allocated]   +---+
  [2KB in use    ]  | XX|  <- only 2KB used
  [6KB free      ]  |   |  <- 6KB wasted
                    +---+

  After shrink:
  [4KB allocated]   +--+
  [2KB in use   ]   |XX|
  [2KB free     ]   +--+
```

### Stack Size Limits

```go
import "runtime/debug"

// Default max stack size: 1GB (64-bit), 250MB (32-bit)
// You can change it:
debug.SetMaxStack(512 * 1024 * 1024) // 512MB max

// Stack overflow: goroutine stack exceeds max → panic: runtime: goroutine stack exceeds limit
// Common cause: infinite recursion
```

---

## 6. Goroutine Lifecycle

### State Machine

```
                   go f()
                     |
                     v
              +------------+
              |  _Gdead    |  (freshly allocated, being initialized)
              +------------+
                     |
                     v
              +------------+
              | _Grunnable |  <--- on run queue, waiting for M
              +------------+
                  ^     |
    preempted/    |     | scheduled onto M
    yield         |     v
                  |  +----------+
                  +--| _Grunning|  (has M and P, executing)
                     +----------+
                         |   |
               blocking  |   |  goroutine ends
               operation |   v
                         |  +--------+
                         |  | _Gdead |  (finished, G struct may be reused)
                         |  +--------+
                         v
                   +-----------+
                   | _Gwaiting |  (blocked: channel, syscall, sleep, lock)
                   +-----------+
                         |
                   condition met
                   (unblocked by runtime)
                         |
                         v
                   +------------+
                   | _Grunnable |  (back on run queue)
                   +------------+
```

**States:**
- `_Gdead` — not executing, stack may be nil (goroutine just created or terminated)
- `_Grunnable` — ready to run, on a run queue
- `_Grunning` — executing on an M+P pair
- `_Gsyscall` — executing a syscall (no P, but has M)
- `_Gwaiting` — blocked (channel recv/send, sync.Mutex, time.Sleep, etc.)
- `_Gcopystack` — stack is being grown/copied

### Goroutine Identity

Each goroutine has an internal **ID** (an integer), but Go intentionally **does not expose it**
in the public API. This is a design choice: goroutine-local storage (like thread-local storage)
is considered an anti-pattern in Go. The preferred alternative is passing context explicitly.

```go
// You can extract goroutine ID via runtime stack trace (hack, not for production):
import (
    "runtime"
    "strconv"
    "strings"
)

func goroutineID() int64 {
    var buf [64]byte
    n := runtime.Stack(buf[:], false)
    // Stack trace starts with: "goroutine 42 [running]:\n"
    idField := strings.Fields(strings.TrimPrefix(string(buf[:n]), "goroutine "))[0]
    id, _ := strconv.ParseInt(idField, 10, 64)
    return id
}
// NOTE: This is for debugging only — never use in production logic.
```

---

## 7. Channels

Channels are Go's primary mechanism for goroutine communication, based on Tony Hoare's
**Communicating Sequential Processes (CSP)** model.

> "Don't communicate by sharing memory; share memory by communicating." — Go Proverb

### Channel Internals: The `hchan` Struct

Understanding the internal structure of a channel unlocks intuition about its behavior.

```
hchan struct (simplified from runtime/chan.go):

  +------------------+
  | qcount  uint     |  number of elements currently in buffer
  | dataqsiz uint    |  size of buffer (capacity)
  | buf  *[n]T       |  pointer to circular buffer array
  | elemsize uint16  |  size of one element
  | closed uint32    |  1 if channel is closed
  | sendx   uint     |  send index (write position in circular buffer)
  | recvx   uint     |  receive index (read position in circular buffer)
  | recvq   waitq    |  list of goroutines waiting to receive
  | sendq   waitq    |  list of goroutines waiting to send
  | lock    mutex    |  protects all fields above
  +------------------+
```

### Channel as a Circular Buffer

```
Buffered channel make(chan int, 4):

  Initial state (empty):
  buf: [ _ ][ _ ][ _ ][ _ ]
        ^
        sendx = recvx = 0
  qcount = 0

  After ch <- 10, ch <- 20:
  buf: [10 ][20 ][ _ ][ _ ]
        ^    ^
        |    sendx = 2
        recvx = 0
  qcount = 2

  After <-ch (receives 10):
  buf: [__ ][20 ][ _ ][ _ ]
             ^    ^
             |    sendx = 2
             recvx = 1
  qcount = 1

  The buffer wraps around (circular):
  buf: [50 ][20 ][30 ][40 ]
        ^    ^
        |    recvx = 1
        sendx = 1 (wrapped around)
  qcount = 4  (FULL)
```

### Send and Receive — What Really Happens

```
CASE 1: Send on unbuffered channel (make(chan T, 0))
  - No buffer exists
  - If a receiver is waiting in recvq:
      → directly copy value from sender to receiver's stack (no buffer involved!)
      → wake up receiver goroutine
  - If no receiver waiting:
      → current goroutine blocks, added to sendq
      → scheduler runs another goroutine

CASE 2: Send on buffered channel (has space)
  - Copy value into buf[sendx]
  - Increment sendx (mod capacity)
  - Increment qcount
  - No blocking

CASE 3: Send on full buffered channel
  - Goroutine blocks, added to sendq
  - Scheduler picks another goroutine

CASE 4: Receive on non-empty buffered channel
  - Copy value from buf[recvx]
  - Increment recvx (mod capacity)
  - Decrement qcount
  - Check sendq: if sender waiting, move one element in from sendq
  - No blocking

CASE 5: Receive on empty channel
  - Goroutine blocks, added to recvq
  - Scheduler picks another goroutine
```

### Channel Creation

```go
// Unbuffered channel: synchronization point
// Send BLOCKS until receiver is ready
// Receive BLOCKS until sender is ready
ch := make(chan int)
ch := make(chan int, 0) // equivalent

// Buffered channel: capacity N
// Send blocks only when buffer is FULL
// Receive blocks only when buffer is EMPTY
ch := make(chan int, 128)

// Channel of channels (common in advanced patterns)
ch := make(chan chan int)

// Directional channel types (enforce at compile time):
var sendOnly chan<- int  // can only send
var recvOnly <-chan int  // can only receive

// Unidirectional channels are derived from bidirectional:
func producer(out chan<- int) { out <- 42 }
func consumer(in <-chan int)  { v := <-in; _ = v }

ch := make(chan int, 1)
producer(ch) // bidirectional implicitly converts to chan<- int
consumer(ch) // bidirectional implicitly converts to <-chan int
```

### Channel Operations and Their Behaviors

```go
// Send
ch <- value    // blocks if channel full (buffered) or no receiver (unbuffered)

// Receive (two forms)
value := <-ch              // blocks if channel empty
value, ok := <-ch          // ok=false if channel is closed AND empty

// Non-blocking send (using select)
select {
case ch <- value:
    // sent successfully
default:
    // channel full or no receiver — did NOT block
}

// Non-blocking receive
select {
case value := <-ch:
    // received
default:
    // channel empty — did NOT block
}
```

### Closing Channels — Rules and Behavior

```
Channel close semantics:

  close(ch)  ──→  sets closed=1 in hchan
                  wakes all goroutines in recvq (they receive zero value + ok=false)
                  future sends panic (runtime: send on closed channel)
                  future receives return (zero, false) immediately (no blocking)

  RULE 1: Only the SENDER should close a channel (not the receiver)
  RULE 2: Never close a channel that might be closed again → panic
  RULE 3: Never close from concurrent goroutines without synchronization
```

```go
package main

import "fmt"

func generator(nums ...int) <-chan int {
    out := make(chan int, len(nums))
    for _, n := range nums {
        out <- n
    }
    close(out) // sender closes
    return out
}

func main() {
    ch := generator(1, 2, 3, 4, 5)

    // Range over channel: stops when channel is closed AND empty
    for n := range ch {
        fmt.Println(n) // prints 1 2 3 4 5
    }

    // Draining after close: returns zero values immediately
    v, ok := <-ch
    fmt.Println(v, ok) // 0 false
}
```

### Nil Channel Behavior

```go
var ch chan int // nil channel (zero value)

// Sending to nil channel: BLOCKS FOREVER
ch <- 1 // deadlock

// Receiving from nil channel: BLOCKS FOREVER
<-ch    // deadlock

// Closing a nil channel: PANICS
close(ch) // panic: close of nil channel

// KEY TRICK: In select, nil channel cases are IGNORED
// This is used to disable channels dynamically:
select {
case v := <-ch: // if ch is nil, this case is never selected
    _ = v
case v := <-other:
    _ = v
}
```

---

## 8. Select Statement

`select` is Go's **non-deterministic multiplexing** over channel operations.

### Internals of Select

```
select evaluates all cases concurrently. Internally:

  1. All channel operations in cases are evaluated (lock all involved channels)
  2. If ONE or more cases are ready:
     → Pseudo-randomly pick one ready case (uniform random, NOT first-match)
  3. If NO cases are ready and there is a default:
     → Execute default (non-blocking)
  4. If NO cases are ready and NO default:
     → Block current goroutine (added to waitq of ALL channels in cases)
     → First channel that becomes ready wakes the goroutine
     → Remove goroutine from all other channels' waitq
```

```
select execution flow:

  select {         +------------------+
  case <-ch1:  --> | ch1 ready?  yes  | --> execute case 1
  case ch2<-v: --> | ch2 ready?  no   |
  case <-ch3:  --> | ch3 ready?  yes  | --> execute case 3 (random pick from {1,3})
  default:         | no ready?   ---  | --> execute default (if no case ready)
  }                +------------------+
```

### Select Patterns

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Pattern 1: Timeout on operation
func withTimeout(ch <-chan int, timeout time.Duration) (int, bool) {
    select {
    case v := <-ch:
        return v, true
    case <-time.After(timeout):
        return 0, false
    }
}

// Pattern 2: Done channel for cancellation
func worker(done <-chan struct{}, jobs <-chan int) {
    for {
        select {
        case <-done:
            return // cancelled
        case job, ok := <-jobs:
            if !ok {
                return // jobs channel closed
            }
            _ = job // process job
        }
    }
}

// Pattern 3: Context-aware select (production pattern)
func fetchWithContext(ctx context.Context, ch <-chan string) (string, error) {
    select {
    case <-ctx.Done():
        return "", ctx.Err()
    case result, ok := <-ch:
        if !ok {
            return "", fmt.Errorf("channel closed")
        }
        return result, nil
    }
}

// Pattern 4: Disabling a channel case dynamically (nil channel trick)
func merge(ch1, ch2 <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for ch1 != nil || ch2 != nil {
            select {
            case v, ok := <-ch1:
                if !ok {
                    ch1 = nil // disable this case by setting to nil
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

// Pattern 5: Priority select (first case has priority)
// WARNING: select does NOT guarantee priority — cases are random
// To implement priority:
func prioritySelect(high, low <-chan int) int {
    // Check high-priority channel first (non-blocking)
    select {
    case v := <-high:
        return v
    default:
    }
    // Fall through to both (random)
    select {
    case v := <-high:
        return v
    case v := <-low:
        return v
    }
}
```

---

## 9. sync Package

The `sync` package provides low-level synchronization primitives. These operate **below** channels
and are appropriate when shared state cannot be avoided.

### sync.WaitGroup

`WaitGroup` waits for a collection of goroutines to finish.

```
WaitGroup internal state:
  +----------+----------+----------+
  | counter  | waiters  | sema     |
  |  (int32) |  (int32) | (uint32) |
  +----------+----------+----------+

  Add(n): counter += n
  Done(): counter -= 1  (equivalent to Add(-1))
  Wait(): blocks until counter == 0
          uses semaphore to sleep/wake
```

```go
package main

import (
    "fmt"
    "sync"
)

func main() {
    const numWorkers = 5
    var wg sync.WaitGroup

    results := make([]int, numWorkers)

    for i := 0; i < numWorkers; i++ {
        wg.Add(1) // MUST call Add before launching goroutine
        go func(id int) {
            defer wg.Done() // always defer Done to handle panics
            results[id] = id * id
        }(i)
    }

    wg.Wait() // blocks until all Done() calls complete
    fmt.Println(results) // safe to access now
}
```

**Critical rules:**
- Call `Add` **before** launching the goroutine (not inside it)
- If you call `Add` inside the goroutine, `Wait` might return before `Add` is even called
- Use `defer wg.Done()` as the first statement inside the goroutine (handles panics)

### sync.Mutex and sync.RWMutex

A `Mutex` (mutual exclusion lock) ensures that only one goroutine accesses a critical section at a time.

```
Mutex state machine:

  Unlocked ────── Lock() ──→ Locked (by one goroutine)
     ^                            |
     |                            |
     └────────── Unlock() ────────┘
                                  |
         Other goroutines          | try Lock()
         block in waitq  ←─────────┘
         until Unlock
```

```go
package main

import (
    "fmt"
    "sync"
)

// SafeCounter demonstrates proper mutex usage
type SafeCounter struct {
    mu    sync.Mutex
    value int
}

func (c *SafeCounter) Increment() {
    c.mu.Lock()
    defer c.mu.Unlock() // always defer unlock
    c.value++
}

func (c *SafeCounter) Value() int {
    c.mu.Lock()
    defer c.mu.Unlock()
    return c.value
}

// RWMutex: multiple readers OR one writer (not both)
// Use when reads are far more frequent than writes
type Cache struct {
    mu    sync.RWMutex
    items map[string]string
}

func NewCache() *Cache {
    return &Cache{items: make(map[string]string)}
}

func (c *Cache) Set(key, value string) {
    c.mu.Lock()         // exclusive write lock
    defer c.mu.Unlock()
    c.items[key] = value
}

func (c *Cache) Get(key string) (string, bool) {
    c.mu.RLock()         // shared read lock (multiple goroutines can hold simultaneously)
    defer c.mu.RUnlock()
    v, ok := c.items[key]
    return v, ok
}

// RWMutex performance: RLock is cheaper than Lock when no writer is waiting
// Lock acquisition order:
//   RLock: granted if no Lock() holder or waiter
//   Lock:  waits for all RLock() holders to RUnlock()
//          new RLock() calls BLOCK while a Lock() is waiting (prevents writer starvation)
```

### Mutex Internals (Starvation Mode)

```
Mutex has two modes (Go 1.9+):

  Normal mode:
    - Goroutines compete for lock via CAS (compare-and-swap)
    - Recently unblocked goroutines compete with newly arriving goroutines
    - Newly arriving goroutine has CPU → often wins over sleeping goroutine
    - Can cause starvation for goroutines that waited long

  Starvation mode (triggered if goroutine waits > 1ms):
    - Lock is handed DIRECTLY to the first goroutine in waitq (FIFO)
    - No new goroutines can acquire the lock (even if it appears unlocked)
    - Prevents starvation at cost of throughput

  State transitions:
    Normal ──→ Starvation (if any goroutine waited > 1ms)
    Starvation ──→ Normal (if goroutine at front of queue acquired lock)
```

### sync.Once

`Once` ensures a function is executed **exactly once**, regardless of how many goroutines call it.

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
        // This runs exactly once, even if called from 1000 goroutines simultaneously
        instance = &Singleton{data: "initialized"}
        fmt.Println("Initialized!")
    })
    return instance
}

// Once internals:
// +----------+----------+
// | done uint32 | m Mutex |
// +----------+----------+
// Fast path: atomic load of done (0 → not done, 1 → done)
// If done == 1: return immediately (hot path, no lock)
// If done == 0: acquire mutex, check again (double-check locking), call f, set done=1
```

### sync.Cond

`Cond` is a condition variable: goroutines can wait for a condition to become true.

```go
package main

import (
    "fmt"
    "sync"
    "time"
)

// Bounded queue using Cond
type BoundedQueue struct {
    mu       sync.Mutex
    notFull  *sync.Cond
    notEmpty *sync.Cond
    items    []int
    capacity int
}

func NewBoundedQueue(cap int) *BoundedQueue {
    q := &BoundedQueue{capacity: cap, items: make([]int, 0, cap)}
    q.notFull = sync.NewCond(&q.mu)
    q.notEmpty = sync.NewCond(&q.mu)
    return q
}

func (q *BoundedQueue) Put(item int) {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == q.capacity {
        q.notFull.Wait() // releases lock, sleeps, reacquires lock when woken
    }
    q.items = append(q.items, item)
    q.notEmpty.Signal() // wake one waiting receiver
}

func (q *BoundedQueue) Get() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == 0 {
        q.notEmpty.Wait() // releases lock, sleeps, reacquires lock when woken
    }
    item := q.items[0]
    q.items = q.items[1:]
    q.notFull.Signal() // wake one waiting sender
    return item
}

// Cond.Wait() ALWAYS recheck condition in a for loop (not if):
// - Wait can return spuriously (rare but possible)
// - Another goroutine might consume the item before you acquire the lock
```

### sync.Pool

`Pool` provides a pool of reusable objects to reduce GC pressure.

```
Pool usage pattern:

  Without Pool:
    each request → allocate []byte → use → GC collects it
    High GC pressure with frequent large allocations

  With Pool:
    each request → Get from pool (reuse) → use → Put back to pool
    GC reclaims pool objects only during collection (not per-allocation)

  Pool lifecycle:
    Pool objects MAY be reclaimed by GC at any time
    Never assume object is in pool → always check if Get() returned nil
    Pool is NOT a permanent cache — use LRU/LFU caches for that
```

```go
package main

import (
    "bytes"
    "sync"
)

// Buffer pool to reduce allocations in hot paths
var bufPool = sync.Pool{
    New: func() any {
        // called when pool is empty
        buf := make([]byte, 0, 4096)
        return &buf
    },
}

func processData(data []byte) []byte {
    // Get buffer from pool
    bufPtr := bufPool.Get().(*[]byte)
    buf := (*bufPtr)[:0] // reset length, keep capacity

    defer func() {
        // Return to pool (reset first to avoid retaining references)
        *bufPtr = buf[:0]
        bufPool.Put(bufPtr)
    }()

    // Use buffer — no allocation if pool has one
    buf = append(buf, data...)
    buf = bytes.ToUpper(buf)

    result := make([]byte, len(buf))
    copy(result, buf)
    return result
}

// bytes.Buffer pool (common in HTTP servers)
var bytesPool = sync.Pool{
    New: func() any { return new(bytes.Buffer) },
}

func getBuffer() *bytes.Buffer {
    return bytesPool.Get().(*bytes.Buffer)
}

func putBuffer(buf *bytes.Buffer) {
    buf.Reset()
    bytesPool.Put(buf)
}
```

**Pool and GC interaction:**
```
GC cycle:
  1. Mark phase: Pool objects are NOT roots (may be reclaimed)
  2. Pool has a victim cache (added in Go 1.13):

     +-------------+      +-------------+
     | local cache |  --> | victim cache | --> GC reclaims
     +-------------+      +-------------+

     Get():  check local → check victim → call New
     Pool GC: local becomes victim, victim is cleared
     This means Pool items survive AT LEAST one GC cycle
```

### sync.Map

`sync.Map` is a concurrent map optimized for two specific use cases:
1. Write once, read many times (e.g., a registry)
2. Many goroutines accessing disjoint keys

```go
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
    if v, ok := m.Load("key1"); ok {
        fmt.Println(v.(string))
    }

    // LoadOrStore: atomic load-or-store
    actual, loaded := m.LoadOrStore("key3", "default")
    fmt.Println(actual, loaded) // "default", false (was not in map)

    // Delete
    m.Delete("key1")

    // Range: iterate (snapshot, not live view)
    m.Range(func(k, v any) bool {
        fmt.Printf("%v: %v\n", k, v)
        return true // return false to stop iteration
    })
}

// sync.Map internals:
// Two maps: read (atomic, no lock) + dirty (with lock)
//
//   read map (atomic.Pointer):    dirty map (with mutex):
//   +--------+--------+           +--------+--------+
//   | key1   | *entry | ←──────── | key1   | *entry |
//   | key2   | *entry |           | key3   | *entry | ← new keys go here
//   +--------+--------+           +--------+--------+
//
// Load(): check read first (no lock) → if miss, check dirty (with lock)
// Store(): if key in read: CAS update entry (no lock for existing keys!)
//          if key not in read: lock, update dirty
// After enough misses, dirty promoted to read
```

**When NOT to use sync.Map:**
- Frequent writes to same keys: regular `map` + `sync.Mutex` is faster
- You need range + delete atomically: use `sync.Mutex` + `map`
- You need `len()`: sync.Map has no Len() (expensive to compute concurrently)

---

## 10. sync/atomic

Atomic operations are **single-instruction** reads/writes guaranteed not to be interrupted.
They operate directly on CPU atomic instructions (e.g., `LOCK XCHG` on x86).

```
Normal operation (NOT atomic):
  Thread 1: LOAD counter (gets 5)
  Thread 2: LOAD counter (gets 5)   ← races with Thread 1
  Thread 1: STORE counter+1 = 6
  Thread 2: STORE counter+1 = 6    ← LOST UPDATE! should be 7

Atomic operation:
  Thread 1: LOCK; LOAD-ADD-STORE (6) atomically
  Thread 2: LOCK; LOAD-ADD-STORE (7) atomically — Thread 2 sees updated value
  Result: correctly 7
```

```go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// atomic.Int64 (Go 1.19+): typed atomic, preferred over raw functions
type AtomicCounter struct {
    value atomic.Int64
}

func (c *AtomicCounter) Increment() int64 {
    return c.value.Add(1)
}

func (c *AtomicCounter) Load() int64 {
    return c.value.Load()
}

func (c *AtomicCounter) CompareAndSwap(old, new int64) bool {
    return c.value.CompareAndSwap(old, new)
}

// Classic example: lock-free counter vs mutex counter
func benchmarkComparison() {
    const iterations = 1_000_000
    var wg sync.WaitGroup

    // Mutex approach
    var muCounter int64
    var mu sync.Mutex

    wg.Add(1)
    go func() {
        defer wg.Done()
        for i := 0; i < iterations; i++ {
            mu.Lock()
            muCounter++
            mu.Unlock()
        }
    }()

    // Atomic approach (faster, no lock contention)
    var atomicCounter atomic.Int64

    wg.Add(1)
    go func() {
        defer wg.Done()
        for i := 0; i < iterations; i++ {
            atomicCounter.Add(1)
        }
    }()

    wg.Wait()
}

// atomic.Pointer (Go 1.19+): lock-free pointer swap
// Use for "publish" pattern: writer creates new value, atomically publishes
type Config struct {
    MaxConns int
    Timeout  int
}

type ConfigHolder struct {
    config atomic.Pointer[Config]
}

func (h *ConfigHolder) Update(newConfig *Config) {
    h.config.Store(newConfig) // atomic publish
}

func (h *ConfigHolder) Get() *Config {
    return h.config.Load() // atomic read — always gets consistent Config
}
```

### Memory Ordering and atomic

```
CPU memory model: CPUs can reorder instructions for performance.
  Store to A, then store to B → another CPU might see B before A!

atomic provides memory ordering guarantees:
  All atomics in Go use "sequentially consistent" ordering
  (strongest ordering — both compiler and CPU prevented from reordering)

  After atomic.Store(x, 1):
    Any goroutine that subsequently atomic.Load(x) and sees 1
    is guaranteed to see all stores performed before Store(x, 1)

This is the basis of the "happens-before" relationship.
```

---

## 11. Context Package

`context.Context` carries **deadlines, cancellation signals, and request-scoped values**
across goroutines and API boundaries.

### Context Tree

```
context.Background()
         │
         ├── WithCancel(parent) ──→ cancelCtx
         │         │
         │         └── WithTimeout(parent, 5s) ──→ timerCtx
         │                   │
         │                   └── WithValue(parent, "key", val) ──→ valueCtx
         │
         └── WithDeadline(parent, time.Now().Add(10s)) ──→ timerCtx

When a parent is cancelled:
  ALL children are cancelled automatically (tree propagation)
  Each cancel propagates down but NOT up
```

### Context Internals

```go
// context.Context interface:
type Context interface {
    Deadline() (deadline time.Time, ok bool)  // when context expires
    Done() <-chan struct{}                     // closed when cancelled/expired
    Err() error                               // nil if not done; Canceled or DeadlineExceeded
    Value(key any) any                        // request-scoped values
}
```

### Context Usage Patterns

```go
package main

import (
    "context"
    "errors"
    "fmt"
    "net/http"
    "time"
)

// Pattern 1: HTTP handler with context propagation
func handleRequest(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // request's context (cancelled when client disconnects)

    result, err := fetchFromDB(ctx, "query")
    if err != nil {
        if errors.Is(err, context.Canceled) {
            // Client disconnected — stop processing
            return
        }
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    fmt.Fprintln(w, result)
}

// Pattern 2: Timeout for external call
func fetchFromDB(ctx context.Context, query string) (string, error) {
    // Create child context with timeout
    ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
    defer cancel() // ALWAYS defer cancel to free resources (timer leak prevention)

    resultCh := make(chan string, 1)
    errCh := make(chan error, 1)

    go func() {
        // simulate DB query
        time.Sleep(1 * time.Second)
        resultCh <- "result for: " + query
    }()

    select {
    case <-ctx.Done():
        return "", ctx.Err() // Canceled or DeadlineExceeded
    case result := <-resultCh:
        return result, nil
    case err := <-errCh:
        return "", err
    }
}

// Pattern 3: Context values (pass request-scoped data)
// KEY RULE: Use unexported types for keys to avoid collisions
type contextKey int

const (
    requestIDKey contextKey = iota
    userIDKey
)

func withRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, requestIDKey, id)
}

func requestIDFromContext(ctx context.Context) (string, bool) {
    id, ok := ctx.Value(requestIDKey).(string)
    return id, ok
}

// Pattern 4: Cancellation propagation through worker tree
func runWithCancellation() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Start workers that respect cancellation
    for i := 0; i < 5; i++ {
        go func(id int, ctx context.Context) {
            for {
                select {
                case <-ctx.Done():
                    fmt.Printf("worker %d shutting down: %v\n", id, ctx.Err())
                    return
                default:
                    // do work
                    time.Sleep(100 * time.Millisecond)
                }
            }
        }(i, ctx)
    }

    time.Sleep(500 * time.Millisecond)
    cancel() // cancels all workers simultaneously
    time.Sleep(100 * time.Millisecond) // wait for workers to print
}
```

### Context Rules (Production)

```
DO:
  ✓ Pass context as FIRST argument to every function that might block or do I/O
  ✓ Always defer cancel() immediately after WithCancel/WithTimeout/WithDeadline
  ✓ Check ctx.Done() in long-running loops
  ✓ Propagate context through goroutine call chains
  ✓ Use context.Background() for program-level roots (main, test setup)
  ✓ Use context.TODO() as a placeholder when unsure (searchable in codebase)

DO NOT:
  ✗ Store context in struct fields (pass explicitly instead)
  ✗ Pass nil context (use context.Background() or context.TODO())
  ✗ Use context for optional parameters
  ✗ Store large values in context (use for request-scoped metadata only)
  ✗ Use context.WithValue with string keys (collision risk — use unexported types)
```

---

## 12. Concurrency Patterns

### Pattern 1: Pipeline

A pipeline is a series of stages connected by channels, where each stage is a group of goroutines.

```
  [Generator] ──chan──→ [Stage 1] ──chan──→ [Stage 2] ──chan──→ [Sink]
   produces              transforms          transforms          consumes
```

```go
package main

import (
    "context"
    "fmt"
)

// Generator: produces values into a channel
func generate(ctx context.Context, nums ...int) <-chan int {
    out := make(chan int, len(nums))
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

// Square: transforms input channel to output channel
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

// Filter: passes only values matching predicate
func filter(ctx context.Context, in <-chan int, pred func(int) bool) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for n := range in {
            if pred(n) {
                select {
                case <-ctx.Done():
                    return
                case out <- n:
                }
            }
        }
    }()
    return out
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    // Build pipeline: generate → square → filter (even only) → print
    nums := generate(ctx, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10)
    squared := square(ctx, nums)
    evens := filter(ctx, squared, func(n int) bool { return n%2 == 0 })

    for n := range evens {
        fmt.Println(n) // 4, 16, 36, 64, 100
    }
}
```

### Pattern 2: Fan-Out / Fan-In

**Fan-Out**: Distribute work from one channel to multiple goroutines.
**Fan-In**: Merge results from multiple channels into one.

```
  Fan-Out:                    Fan-In:
  [Source] ──→ [Worker 1] ──→ \
          ──→ [Worker 2] ──→  [Merge] ──→ [Consumer]
          ──→ [Worker 3] ──→ /
```

```go
package main

import (
    "context"
    "sync"
)

// Fan-out: distribute jobs to N workers
func fanOut(ctx context.Context, jobs <-chan int, numWorkers int) []<-chan int {
    channels := make([]<-chan int, numWorkers)
    for i := 0; i < numWorkers; i++ {
        channels[i] = worker(ctx, jobs)
    }
    return channels
}

func worker(ctx context.Context, jobs <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for job := range jobs {
            select {
            case <-ctx.Done():
                return
            case out <- job * job: // process job
            }
        }
    }()
    return out
}

// Fan-in: merge multiple channels into one
func fanIn(ctx context.Context, channels ...<-chan int) <-chan int {
    merged := make(chan int)
    var wg sync.WaitGroup

    output := func(ch <-chan int) {
        defer wg.Done()
        for n := range ch {
            select {
            case <-ctx.Done():
                return
            case merged <- n:
            }
        }
    }

    wg.Add(len(channels))
    for _, ch := range channels {
        go output(ch)
    }

    // Close merged when all input channels are done
    go func() {
        wg.Wait()
        close(merged)
    }()

    return merged
}
```

### Pattern 3: Worker Pool

A fixed pool of goroutines processing a stream of jobs.
Use when you want to **bound concurrency** (e.g., limit DB connections, CPU threads).

```
  [Job Queue Channel]
        |
  ┌─────┴──────────────────────┐
  ↓           ↓           ↓    ↓
[Worker1] [Worker2] [Worker3] ...  (N workers)
  ↓           ↓           ↓
  └─────┬──────────────────────┘
        |
  [Result Channel]
```

```go
package main

import (
    "context"
    "fmt"
    "sync"
)

type Job struct {
    ID    int
    Input int
}

type Result struct {
    JobID  int
    Output int
    Err    error
}

const numWorkers = 4

func workerPool(
    ctx context.Context,
    jobs <-chan Job,
    process func(context.Context, Job) Result,
) <-chan Result {
    results := make(chan Result, numWorkers)
    var wg sync.WaitGroup

    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            for job := range jobs {
                select {
                case <-ctx.Done():
                    results <- Result{JobID: job.ID, Err: ctx.Err()}
                    return
                default:
                    results <- process(ctx, job)
                }
            }
        }()
    }

    go func() {
        wg.Wait()
        close(results)
    }()

    return results
}

func processJob(ctx context.Context, job Job) Result {
    // Simulate work
    return Result{JobID: job.ID, Output: job.Input * job.Input}
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()

    jobs := make(chan Job, 100)
    results := workerPool(ctx, jobs, processJob)

    // Submit jobs
    go func() {
        defer close(jobs)
        for i := 0; i < 20; i++ {
            jobs <- Job{ID: i, Input: i}
        }
    }()

    // Collect results
    for result := range results {
        if result.Err != nil {
            fmt.Printf("job %d error: %v\n", result.JobID, result.Err)
            continue
        }
        fmt.Printf("job %d: %d\n", result.JobID, result.Output)
    }
}
```

### Pattern 4: Semaphore (Bounded Concurrency)

Limit concurrent access to a resource using a buffered channel as a semaphore.

```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Semaphore using buffered channel
// Buffer size = max concurrent operations
type Semaphore struct {
    ch chan struct{}
}

func NewSemaphore(maxConcurrency int) *Semaphore {
    return &Semaphore{ch: make(chan struct{}, maxConcurrency)}
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

// Usage: limit to 10 concurrent HTTP requests
func fetchAll(ctx context.Context, urls []string) []string {
    sem := NewSemaphore(10) // max 10 concurrent
    var wg sync.WaitGroup
    results := make([]string, len(urls))

    for i, url := range urls {
        wg.Add(1)
        go func(idx int, u string) {
            defer wg.Done()
            if err := sem.Acquire(ctx); err != nil {
                results[idx] = "cancelled"
                return
            }
            defer sem.Release()

            // simulate HTTP fetch
            time.Sleep(10 * time.Millisecond)
            results[idx] = "result: " + u
        }(i, url)
    }

    wg.Wait()
    return results
}

func main() {
    ctx := context.Background()
    urls := make([]string, 100)
    for i := range urls {
        urls[i] = fmt.Sprintf("http://example.com/%d", i)
    }
    results := fetchAll(ctx, urls)
    fmt.Printf("Got %d results\n", len(results))
}
```

### Pattern 5: Error Group (golang.org/x/sync/errgroup)

A `WaitGroup` + error handling + cancellation combined.

```go
package main

import (
    "context"
    "fmt"

    "golang.org/x/sync/errgroup"
)

func fetchData(ctx context.Context, id int) (string, error) {
    // simulate work
    if id == 3 {
        return "", fmt.Errorf("item %d not found", id)
    }
    return fmt.Sprintf("data-%d", id), nil
}

func main() {
    ctx := context.Background()
    g, ctx := errgroup.WithContext(ctx) // ctx cancelled if any goroutine returns error

    results := make([]string, 5)

    for i := 0; i < 5; i++ {
        id := i
        g.Go(func() error {
            data, err := fetchData(ctx, id)
            if err != nil {
                return err // cancels ctx for all goroutines
            }
            results[id] = data
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        fmt.Printf("error: %v\n", err) // first error
        return
    }
    fmt.Println(results)
}
```

### Pattern 6: Done Channel (Signaling Shutdown)

```go
package main

import (
    "fmt"
    "time"
)

// done channel for signaling shutdown to multiple goroutines
// Close the done channel — it BROADCASTS to all receivers simultaneously
// Sending on done channel — only ONE receiver gets the signal

func worker(id int, done <-chan struct{}) {
    for {
        select {
        case <-done:
            fmt.Printf("worker %d shutting down\n", id)
            return
        default:
            fmt.Printf("worker %d working\n", id)
            time.Sleep(100 * time.Millisecond)
        }
    }
}

func main() {
    done := make(chan struct{})

    for i := 0; i < 3; i++ {
        go worker(i, done)
    }

    time.Sleep(300 * time.Millisecond)
    close(done) // broadcasts shutdown to ALL workers simultaneously

    time.Sleep(100 * time.Millisecond)
}
```

### Pattern 7: Rate Limiter

```go
package main

import (
    "context"
    "fmt"
    "time"
)

// Token bucket rate limiter using time.Ticker
type RateLimiter struct {
    tokens chan struct{}
    ticker *time.Ticker
    done   chan struct{}
}

func NewRateLimiter(ratePerSecond int) *RateLimiter {
    rl := &RateLimiter{
        tokens: make(chan struct{}, ratePerSecond),
        ticker: time.NewTicker(time.Second / time.Duration(ratePerSecond)),
        done:   make(chan struct{}),
    }
    go rl.refill()
    return rl
}

func (rl *RateLimiter) refill() {
    defer rl.ticker.Stop()
    for {
        select {
        case <-rl.done:
            return
        case <-rl.ticker.C:
            select {
            case rl.tokens <- struct{}{}: // add token
            default:                      // bucket full, discard token
            }
        }
    }
}

func (rl *RateLimiter) Wait(ctx context.Context) error {
    select {
    case <-rl.tokens:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (rl *RateLimiter) Stop() {
    close(rl.done)
}

func main() {
    ctx := context.Background()
    rl := NewRateLimiter(5) // 5 requests per second
    defer rl.Stop()

    for i := 0; i < 10; i++ {
        if err := rl.Wait(ctx); err != nil {
            fmt.Println("cancelled:", err)
            break
        }
        fmt.Printf("request %d at %v\n", i, time.Now().Format("15:04:05.000"))
    }
}
```

---

## 13. Goroutine Leaks

A goroutine leak occurs when a goroutine is created but **never terminates** — either blocked
forever on a channel or sleeping in an infinite loop. Leaked goroutines consume memory (stack)
and may hold resources (connections, file handles).

### How Leaks Happen

```
Scenario 1: Goroutine blocked on receive, nobody sends
  go func() {
      result := <-ch  // blocks forever if nobody sends on ch
      process(result)
  }()
  // ch goes out of scope — goroutine leaks

Scenario 2: Goroutine blocked on send, nobody receives
  go func() {
      ch <- expensiveComputation() // blocks if nobody receives
  }()
  // If caller times out and stops reading, goroutine leaks

Scenario 3: Goroutine in infinite loop without exit condition
  go func() {
      for {
          doWork()
          // no select with done channel → no way to stop
      }
  }()
```

### Detection with goleak

```go
package main_test

import (
    "testing"

    "go.uber.org/goleak"
)

func TestNoLeaks(t *testing.T) {
    defer goleak.VerifyNone(t) // fails test if any goroutines leaked

    // Run your code here
    // goleak captures goroutine count before/after
}
```

### Detection with runtime

```go
import "runtime"

func goroutineCount() int {
    return runtime.NumGoroutine()
}

// In tests: check count before and after
before := runtime.NumGoroutine()
// ... run code ...
after := runtime.NumGoroutine()
if after > before {
    t.Errorf("leaked %d goroutines", after-before)
}
```

### Prevention Rules

```go
// RULE 1: Always provide an exit path for every goroutine

// Bad: goroutine has no exit
go func() {
    for result := range resultCh { // what if resultCh is never closed?
        process(result)
    }
}()

// Good: goroutine exits on done or resultCh close
go func() {
    for {
        select {
        case <-done:
            return
        case result, ok := <-resultCh:
            if !ok {
                return // channel closed
            }
            process(result)
        }
    }
}()

// RULE 2: Use buffered channels when goroutine might not have a receiver
// Bad: goroutine blocks if timeout fires before result is consumed
func getResult() (string, error) {
    ch := make(chan string) // unbuffered
    go func() {
        ch <- doWork() // LEAKS if getResult returns early (timeout)
    }()

    select {
    case result := <-ch:
        return result, nil
    case <-time.After(1 * time.Second):
        return "", errors.New("timeout")
        // goroutine is now blocked forever trying to send on ch
    }
}

// Good: use buffered channel so goroutine can always send
func getResultFixed() (string, error) {
    ch := make(chan string, 1) // buffered — goroutine can always send
    go func() {
        ch <- doWork() // never blocks
    }()

    select {
    case result := <-ch:
        return result, nil
    case <-time.After(1 * time.Second):
        return "", errors.New("timeout")
        // goroutine will complete and send to ch (nobody reads, but it terminates)
    }
}
```

---

## 14. Race Conditions and Memory Model

### What is a Data Race?

A data race occurs when two goroutines access the same memory location **concurrently**,
and at least one access is a write, **without synchronization**.

```
Timeline of a data race:

  Goroutine 1:  READ x (value: 0)  │
  Goroutine 2:           WRITE x=1 │  ← concurrent with G1's read
  Goroutine 1:  WRITE x = READ+1=1 │  ← G1 writes based on stale read
  
  Expected: x = 2
  Actual: x = 1  (lost update)
```

### The Go Memory Model

The Go memory model specifies when one goroutine's writes are **guaranteed** to be visible to another goroutine's reads. It is based on the **happens-before** relationship.

```
Happens-Before Rules:
  1. Within a single goroutine: statements happen in order (sequentially consistent)
  
  2. Channel send happens-before the corresponding receive completes
     ch <- v  happens-before  v := <-ch
  
  3. Closing a channel happens-before a receive that returns zero value
     close(ch)  happens-before  <-ch (returns zero)
  
  4. sync.Mutex: Unlock() of call n happens-before Lock() of call n+1
  
  5. sync.Once: f() inside Do() happens-before any Do() returns
  
  6. goroutine creation: go f() happens-before f() starts
  
  7. goroutine completion: f() completion does NOT happen-before anything
     (you need WaitGroup or channel to synchronize on goroutine completion)
```

### Race Detector

Go has a built-in race detector (based on ThreadSanitizer):

```bash
# Run with race detector
go run -race main.go
go test -race ./...
go build -race -o binary .

# Output when race detected:
# ==================
# WARNING: DATA RACE
# Write at 0x... by goroutine 7:
#   main.increment()
#       /path/main.go:15
# 
# Previous read at 0x... by goroutine 6:
#   main.increment()
#       /path/main.go:14
# ==================

# Performance overhead: 5-20x slower, 5-10x more memory
# Use in tests and staging — not production builds
```

```go
package main

import (
    "fmt"
    "sync"
)

// Race condition example
var counter int

func badIncrement(wg *sync.WaitGroup) {
    defer wg.Done()
    counter++ // DATA RACE: unsynchronized read-modify-write
}

// Fixed with mutex
var (
    safeCounter int
    mu          sync.Mutex
)

func safeIncrement(wg *sync.WaitGroup) {
    defer wg.Done()
    mu.Lock()
    safeCounter++
    mu.Unlock()
}

// Fixed with atomic
var atomicCounter int64

func atomicIncrement(wg *sync.WaitGroup) {
    defer wg.Done()
    // atomic.AddInt64(&atomicCounter, 1) // lock-free
}

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 1000; i++ {
        wg.Add(1)
        go safeIncrement(&wg)
    }
    wg.Wait()
    fmt.Println(safeCounter) // always 1000
}
```

---

## 15. Performance Characteristics

### GOMAXPROCS — Setting Parallelism

```go
import "runtime"

// Default: number of logical CPUs
// Setting it lower limits parallelism (useful for testing)
runtime.GOMAXPROCS(4) // use 4 OS threads for goroutine scheduling

// Get current value
n := runtime.GOMAXPROCS(0) // 0 means "query without setting"

// In Docker containers: use automaxprocs library
// Default GOMAXPROCS uses host CPU count, not container quota!
// go.uber.org/automaxprocs sets it based on cgroup CPU limits
```

### Goroutine Creation Cost

```
Benchmark (approximate on modern hardware):
  Creating goroutine:          ~300 ns, ~2KB memory
  OS thread creation:          ~10 µs,  ~8MB memory
  Goroutine context switch:    ~100-200 ns
  OS thread context switch:    ~1-2 µs (kernel transition)
  Channel send (unbuffered):   ~100-500 ns (depends on contention)
  Mutex lock (uncontended):    ~20-30 ns
  Atomic add (uncontended):    ~5-10 ns (single CPU instruction)
```

### Cache Behavior

```
CPU Cache Hierarchy (typical modern CPU):
  L1 cache: ~64KB per core,  ~1 ns latency
  L2 cache: ~256KB per core, ~3-5 ns latency
  L3 cache: ~8-32MB shared,  ~10-30 ns latency
  RAM:      GBs,             ~60-100 ns latency
  Disk:     TBs,             ~100 µs (SSD) to ~10ms (HDD)

False sharing: two goroutines modify DIFFERENT variables
  that happen to be in the SAME cache line (64 bytes).
  Modifying one invalidates the other core's cache line.

  Example of false sharing:
  type Counters struct {
      a int64 // offset 0
      b int64 // offset 8, same cache line as a
  }
  G1 writes Counters.a, G2 writes Counters.b
  → cache line bounces between cores → SLOW

  Fix: pad to cache line boundary:
  const cacheLineSize = 64
  type Counters struct {
      a   int64
      _   [cacheLineSize - 8]byte // padding
      b   int64
      _   [cacheLineSize - 8]byte
  }
```

```go
package main

import (
    "sync"
    "sync/atomic"
    "testing"
)

// False sharing demonstration (bad)
type BadCounters struct {
    a int64
    b int64
}

// No false sharing (good — padded to cache lines)
const cacheLineSize = 64

type PaddedCounter struct {
    value int64
    _     [cacheLineSize - 8]byte // padding
}

type GoodCounters struct {
    a PaddedCounter
    b PaddedCounter
}

func BenchmarkFalseSharing(b *testing.B) {
    var wg sync.WaitGroup
    c := &BadCounters{}
    b.ResetTimer()
    wg.Add(2)
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ {
            atomic.AddInt64(&c.a, 1)
        }
    }()
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ {
            atomic.AddInt64(&c.b, 1)
        }
    }()
    wg.Wait()
}
```

### Goroutine Scheduling Latency

```
When should you use goroutines vs other approaches?

  Task takes < 1 µs:
    Goroutine overhead (300ns creation + scheduling) too expensive
    Use direct function call or tight loop

  Task takes 1 µs – 100 µs:
    Goroutines reasonable but consider goroutine pool
    Reuse goroutines via worker pool pattern

  Task takes > 100 µs (I/O, DB calls, HTTP requests):
    Goroutines are ideal — most time is spent waiting, not computing
    Each goroutine consumes very little CPU while waiting

  Rule of thumb:
    "If it blocks, give it a goroutine."
    "If it's purely computational, match goroutines to GOMAXPROCS."
```

---

## 16. Production Tips and Tricks

### Tip 1: Always Name Your Goroutines (via goroutine label + pprof)

```go
import "runtime/pprof"

// Label goroutines for profiling differentiation
// Appears in pprof goroutine profiles
go func() {
    labels := pprof.Labels("component", "worker", "id", "1")
    pprof.Do(context.Background(), labels, func(ctx context.Context) {
        // goroutine body
        runWorker(ctx)
    })
}()
```

### Tip 2: Instrument Goroutine Count

```go
import (
    "expvar"
    "runtime"
)

var goroutineGauge = expvar.NewInt("goroutines")

func trackGoroutines() {
    // Expose via /debug/vars endpoint
    go func() {
        for {
            goroutineGauge.Set(int64(runtime.NumGoroutine()))
            time.Sleep(5 * time.Second)
        }
    }()
}
```

### Tip 3: Channel Direction in APIs

Always use directional channels in function signatures. This documents intent and prevents
accidental misuse at compile time:

```go
// Bad: bidirectional — caller can accidentally close or send in wrong direction
func consumer(ch chan int) {}

// Good: receive-only — explicitly documents this function only reads
func consumer(ch <-chan int) {}

// Good: send-only — explicitly documents this function only writes
func producer(ch chan<- int) {}
```

### Tip 4: Select with Default for Non-Blocking Probing

```go
// Probe channel state without blocking (e.g., in a health check)
func isChannelEmpty(ch <-chan int) bool {
    select {
    case <-ch:
        return false // had a value
    default:
        return true  // was empty
    }
}

// Try-send pattern for backpressure handling
func trySend(ch chan<- Event, event Event) bool {
    select {
    case ch <- event:
        return true  // sent
    default:
        return false // channel full — apply backpressure
    }
}
```

### Tip 5: Avoid time.Sleep for Synchronization

```go
// Bad: timing-based synchronization (flaky in tests, wrong on slow systems)
go doWork()
time.Sleep(100 * time.Millisecond) // hope doWork is done?
checkResult()

// Good: channel or WaitGroup
var wg sync.WaitGroup
wg.Add(1)
go func() {
    defer wg.Done()
    doWork()
}()
wg.Wait() // deterministically wait
checkResult()
```

### Tip 6: Graceful Shutdown Pattern

```go
package main

import (
    "context"
    "fmt"
    "os"
    "os/signal"
    "sync"
    "syscall"
    "time"
)

type Server struct {
    wg     sync.WaitGroup
    cancel context.CancelFunc
}

func (s *Server) Start(ctx context.Context) {
    ctx, s.cancel = context.WithCancel(ctx)

    // Launch workers
    for i := 0; i < 5; i++ {
        s.wg.Add(1)
        go s.worker(ctx, i)
    }
}

func (s *Server) worker(ctx context.Context, id int) {
    defer s.wg.Done()
    fmt.Printf("worker %d started\n", id)
    defer fmt.Printf("worker %d stopped\n", id)

    ticker := time.NewTicker(100 * time.Millisecond)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            // do work
        }
    }
}

func (s *Server) Shutdown(timeout time.Duration) error {
    s.cancel() // signal all workers

    done := make(chan struct{})
    go func() {
        s.wg.Wait()
        close(done)
    }()

    select {
    case <-done:
        return nil
    case <-time.After(timeout):
        return fmt.Errorf("shutdown timeout after %v", timeout)
    }
}

func main() {
    srv := &Server{}
    srv.Start(context.Background())

    // Wait for OS signal
    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGINT, syscall.SIGTERM)
    <-sigCh

    fmt.Println("shutting down...")
    if err := srv.Shutdown(5 * time.Second); err != nil {
        fmt.Fprintln(os.Stderr, "shutdown error:", err)
        os.Exit(1)
    }
    fmt.Println("clean shutdown")
}
```

### Tip 7: Use errgroup for Concurrent Work with Error Handling

```go
// From golang.org/x/sync/errgroup
// Replaces WaitGroup + error channel boilerplate

g, ctx := errgroup.WithContext(context.Background())
g.SetLimit(10) // limit concurrent goroutines (Go 1.20+)

for _, item := range items {
    item := item // capture loop variable (Go <1.22)
    g.Go(func() error {
        return process(ctx, item)
    })
}

if err := g.Wait(); err != nil {
    // first non-nil error
}
```

### Tip 8: Detecting Deadlocks

```
Go runtime detects "all goroutines asleep" deadlock automatically:
  panic: all goroutines are asleep - deadlock!

  goroutine 1 [chan receive]:
  main.main()
      /path/main.go:10

But it cannot detect partial deadlocks (some goroutines deadlocked, others running).
Use: go tool trace, pprof goroutine dump, or goleak for partial deadlock detection.

Common deadlock causes:
  1. Goroutine waits to send on channel, nobody receives
  2. Goroutine waits to receive, nobody sends
  3. Lock acquired twice by same goroutine (sync.Mutex is NOT reentrant)
  4. Two goroutines each waiting for the other (classic circular wait)
```

### Tip 9: Profiling Goroutines

```bash
# Import net/http/pprof in your program
import _ "net/http/pprof"
go http.ListenAndServe(":6060", nil)

# Get goroutine dump
curl http://localhost:6060/debug/pprof/goroutine?debug=2

# Trace goroutine scheduling (shows GMP events)
go tool trace trace.out

# Visualize goroutine count over time with pprof
go tool pprof http://localhost:6060/debug/pprof/goroutine
```

### Tip 10: Channel Sizing Guidelines

```
Unbuffered (make(chan T)):
  Use for: synchronization points, handoffs where sender and receiver rendezvous
  Effect: sender always blocks until receiver is ready (and vice versa)
  Risk: easy to deadlock if not careful

Buffered small (make(chan T, 1)):
  Use for: "fire and forget" where goroutine must not block after sending once
  Classic pattern: error channel (send one error, return)

Buffered medium (make(chan T, N) where N = numWorkers):
  Use for: job queues matching number of workers
  Reduces goroutine scheduling overhead (batching)

Buffered large (make(chan T, 1000+)):
  Use for: rate decoupling between fast producer and slow consumer
  Risk: large buffers hide backpressure problems
  Production: instrument buffer fill level to detect backpressure
```

---

## 17. Common Pitfalls

### Pitfall 1: Goroutine Without Exit Path

```go
// BUG: goroutine leaks when nobody reads from results
func process() {
    results := make(chan int)
    go func() {
        for _, v := range data {
            results <- v // blocks forever if caller stops reading
        }
    }()
    // if we return here, goroutine is stuck forever
}

// FIX: pass done channel or context
func processFixed(ctx context.Context) {
    results := make(chan int, len(data)) // buffered OR
    go func() {
        for _, v := range data {
            select {
            case results <- v:
            case <-ctx.Done():
                return // can exit now
            }
        }
        close(results)
    }()
}
```

### Pitfall 2: Closing Channel from Multiple Goroutines

```go
// BUG: multiple goroutines closing same channel → panic
for i := 0; i < 3; i++ {
    go func() {
        // if multiple goroutines try to close: panic!
        close(ch)
    }()
}

// FIX: use sync.Once to guarantee exactly one close
var once sync.Once
for i := 0; i < 3; i++ {
    go func() {
        once.Do(func() { close(ch) })
    }()
}
```

### Pitfall 3: WaitGroup.Add Inside Goroutine

```go
// BUG: Add might happen AFTER Wait returns
var wg sync.WaitGroup
go func() {
    wg.Add(1) // too late — main goroutine might have already passed Wait
    defer wg.Done()
    doWork()
}()
wg.Wait() // might return before goroutine even starts

// FIX: always Add BEFORE launching
wg.Add(1)
go func() {
    defer wg.Done()
    doWork()
}()
wg.Wait()
```

### Pitfall 4: Sending on Closed Channel

```go
// Runtime panic: send on closed channel
close(ch)
ch <- value // panic!

// Pattern: use recover, or restructure so sender owns channel lifecycle
// The goroutine that CREATES the channel should be the one to CLOSE it
// Never close from the receiver side
```

### Pitfall 5: Mutex Copied by Value

```go
// BUG: copying a mutex (or struct containing mutex) invalidates it
type Counter struct {
    mu    sync.Mutex
    value int
}

func badCopy(c Counter) { // BUG: c is a COPY, mu state is not preserved
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++ // modifies copy, not original
}

// FIX: always pass by pointer
func goodCopy(c *Counter) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
}

// go vet detects this: "assignment copies lock value"
```

### Pitfall 6: Panic in Goroutine Not Recovered

```go
// Panic in a goroutine crashes the ENTIRE program (not just that goroutine)
go func() {
    panic("something went wrong") // crashes entire program!
}()

// FIX: recover inside every goroutine boundary in production services
func safeGo(f func()) {
    go func() {
        defer func() {
            if r := recover(); r != nil {
                // log the panic, don't propagate
                fmt.Fprintf(os.Stderr, "recovered panic: %v\n", r)
                // optionally: debug.PrintStack()
            }
        }()
        f()
    }()
}

safeGo(func() {
    panic("handled!") // program continues
})
```

### Pitfall 7: Range over Channel After Close

```go
// This is actually CORRECT behavior — understand it:
ch := make(chan int, 3)
ch <- 1
ch <- 2
ch <- 3
close(ch)

for v := range ch { // range receives 1, 2, 3 then exits (on close + empty)
    fmt.Println(v)
}
// After loop: range automatically detects closed + empty channel

// The pitfall: ranging over a channel nobody ever closes
for v := range ch { // INFINITE WAIT if nobody closes ch
    fmt.Println(v)
}
```

---

## Summary: Mental Model for Thinking in Goroutines

```
When you see a concurrent problem, ask:

  1. WHAT needs to happen concurrently?
     → Identify independent units of work (candidates for goroutines)

  2. HOW do they communicate?
     → Shared state → sync.Mutex / sync.RWMutex / sync/atomic
     → Passing data → channels (prefer this)

  3. WHO owns the channel lifecycle?
     → The creator/sender is responsible for closing
     → Only close when ALL senders are done

  4. HOW do goroutines stop?
     → Every goroutine must have a clear exit condition
     → context.Context for cancellation
     → done channel for broadcast shutdown
     → closed input channel for pipeline termination

  5. WHAT is the concurrency level?
     → Unbounded goroutines → risk OOM (use worker pool + semaphore)
     → Match CPU-bound goroutines to GOMAXPROCS

  6. WHAT are the error paths?
     → errgroup for concurrent error collection
     → Buffered error channels to avoid goroutine leaks

  7. HOW do you TEST it?
     → -race flag in all tests
     → goleak in TestMain
     → Inject delays with -count and -shuffle
```

```
The GMP Model in One Picture:

  [G] [G] [G] [G] [G] [G] [G] [G]  ← goroutines (user-level, lightweight)
   \   \   \   \   /   /   /   /
    \   \   +---+---+  /   /   /
     \   +--| P0| P1|--+   /   /     ← processors (scheduling contexts, = GOMAXPROCS)
      +-----| P2| P3|------+   /
            +---+---+
               |  |
            [M0][M1][M2][M3]          ← OS threads (real kernel threads)
               |  |  |  |
            [CPU0][CPU1][CPU2][CPU3]  ← hardware cores
```

> **Final Insight:** Goroutines are not magic — they are cooperative multiplexing on top of real
> OS threads. The GMP scheduler is a sophisticated user-space thread scheduler. Understanding
> it at this level lets you reason about why your program behaves the way it does under load,
> why adding more goroutines doesn't always help, and when to reach for channels vs mutexes.
> The expert Go programmer's mental model is always: "What is the goroutine doing right now?
> Is it runnable, running, or waiting? Who will wake it up? Will it ever wake up?"

Now I'll build the comprehensive guide. This will be extensive — covering every layer from hardware reality up to production patterns.~2,900 lines of deep material. Here's what the guide covers and **why it's structured the way it is**:

---

### What's Inside & The Reasoning

**GMP Scheduler (Section 3)** — This is the section most tutorials skip. Every performance decision in Go concurrency traces back here. You now know *why* goroutines are cheap (user-space scheduling), *why* blocking syscalls don't block your program (P handoff), and *why* work stealing prevents starvation. This is your mental CPU for reasoning about Go programs under load.

**`hchan` struct (Section 7)** — Channels are not black boxes. The circular buffer, `sendq`/`recvq` wait lists, and the direct-copy fast path for unbuffered channels — knowing this tells you *exactly* what happens at each send/receive and why nil channels behave the way they do in `select`.

**ASCII diagrams** show you actual runtime state transitions (stack growth, GMP topology, circular buffer indices) — not abstract concept boxes.

**Production patterns (Section 12)** — Every pattern includes the *context-aware* version, proper channel lifetime management, and the buffered channel trick to prevent goroutine leaks in timeout paths.

**The Final Mental Model** — The 7-question checklist at the end is the actual thought process expert Go engineers run through before writing any concurrent code. Internalize it and you'll stop making the classic mistakes.

> **Next depth level to explore:** Go's memory model (`sync/atomic` happens-before chains), `pprof` goroutine tracing in production, and the `netpoller` — how Go handles millions of network connections without blocking OS threads.