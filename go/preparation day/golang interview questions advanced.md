# Advanced Go Engineering: Complete Interview & Mastery Guide

> **Audience:** Staff-level engineers, system architects, senior Go practitioners.  
> **Philosophy:** Mental models first, code second, trivia never.  
> Every section builds a durable thinking framework — not just interview answers.

---

## Table of Contents

1. [Go Runtime Architecture & GMP Scheduler](#1-go-runtime-architecture--gmp-scheduler)
2. [Goroutines — Internals & Lifecycle](#2-goroutines--internals--lifecycle)
3. [Channels — Implementation Deep Dive](#3-channels--implementation-deep-dive)
4. [Go Memory Model & Happens-Before](#4-go-memory-model--happens-before)
5. [Garbage Collector — Tri-Color Concurrent GC](#5-garbage-collector--tri-color-concurrent-gc)
6. [Escape Analysis & Stack vs Heap](#6-escape-analysis--stack-vs-heap)
7. [Interfaces — Fat Pointers, Dynamic Dispatch, nil traps](#7-interfaces--fat-pointers-dynamic-dispatch-nil-traps)
8. [Generics — Type Parameters, Constraints, Internals](#8-generics--type-parameters-constraints-internals)
9. [sync, atomic & Low-Level Concurrency](#9-sync-atomic--low-level-concurrency)
10. [Context Package — Internals & Patterns](#10-context-package--internals--patterns)
11. [Error Handling — Patterns, Wrapping, Sentinel, Custom](#11-error-handling--patterns-wrapping-sentinel-custom)
12. [Reflection & the reflect Package](#12-reflection--the-reflect-package)
13. [unsafe Package — Memory Layout & Tricks](#13-unsafe-package--memory-layout--tricks)
14. [Memory Alignment, Struct Padding, Data Races](#14-memory-alignment-struct-padding-data-races)
15. [Profiling, Benchmarking & Performance Tuning](#15-profiling-benchmarking--performance-tuning)
16. [Concurrency Patterns — Production Patterns](#16-concurrency-patterns--production-patterns)
17. [Networking — HTTP/2, gRPC, TLS Internals](#17-networking--http2-grpc-tls-internals)
18. [Testing — Unit, Integration, Fuzzing, Race Detection](#18-testing--unit-integration-fuzzing-race-detection)
19. [Distributed Systems Patterns in Go](#19-distributed-systems-patterns-in-go)
20. [CGo & FFI Basics](#20-cgo--ffi-basics)
21. [Build System, Toolchain & Release Engineering](#21-build-system-toolchain--release-engineering)
22. [Security Checklist & Production Hardening](#22-security-checklist--production-hardening)
23. [Tricky Interview Questions & Brain Teasers](#23-tricky-interview-questions--brain-teasers)

---

## 1. Go Runtime Architecture & GMP Scheduler

### One-Line Explanation
Go's scheduler multiplexes millions of lightweight goroutines onto a fixed pool of OS threads using a work-stealing M:N scheduler called GMP.

### The Mental Model

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Go Process                                    │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                    Global Run Queue (GRQ)                     │   │
│  │   [G] [G] [G] [G] [G] ← goroutines waiting for a P          │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌───────────┐    ┌───────────┐    ┌───────────┐                   │
│  │     P0    │    │     P1    │    │     P2    │  ← GOMAXPROCS Ps  │
│  │  ┌─────┐  │    │  ┌─────┐  │    │  ┌─────┐  │                   │
│  │  │LRQ  │  │    │  │LRQ  │  │    │  │LRQ  │  │  ← Local queues  │
│  │  │[G][G]│  │    │  │[G][G]│  │    │  │[G]  │  │                   │
│  │  └──┬──┘  │    │  └──┬──┘  │    │  └──┬──┘  │                   │
│  │     │     │    │     │     │    │     │     │                   │
│  │  ┌──▼──┐  │    │  ┌──▼──┐  │    │  ┌──▼──┐  │                   │
│  │  │  M0 │  │    │  │  M1 │  │    │  │  M2 │  │  ← OS Threads    │
│  │  └─────┘  │    │  └─────┘  │    │  └─────┘  │                   │
│  └───────────┘    └───────────┘    └───────────┘                   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Blocking Ms (syscall/CGo) — P detached, new M spawned      │   │
│  │        [M-blocked] [M-blocked]                               │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Idle Ms — parked, waiting to be woken                       │   │
│  └──────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘

G = Goroutine   M = Machine (OS Thread)   P = Processor (logical CPU)
```

### GMP Components — Deep Dive

#### G (Goroutine)
```go
// Simplified runtime.g struct (runtime/runtime2.go)
type g struct {
    stack         stack          // [lo, hi] address range
    stackguard0   uintptr        // stack overflow check
    _panic        *_panic        // innermost panic
    _defer        *_defer        // innermost defer
    m             *m             // current M (nil if not running)
    sched         gobuf          // saved registers (SP, PC, BP)
    atomicstatus  atomic.Uint32  // status: idle/runnable/running/syscall/waiting/dead
    goid          uint64         // goroutine ID (race detector uses this)
    waitsince     int64          // when did G become blocked
    waitreason    waitReason     // why is G waiting (chanrecv, sleep, etc.)
    preempt       bool           // preemption signal
    lockedm       muintptr       // if set, G is locked to this M
}

// gobuf — what the scheduler saves/restores on context switch
type gobuf struct {
    sp   uintptr  // stack pointer
    pc   uintptr  // program counter
    g    guintptr // goroutine pointer
    ret  uintptr  // return value from syscall
    bp   uintptr  // base pointer (frame pointer)
}
```

Key goroutine states:
```
_Gidle       → just allocated, not yet initialized
_Grunnable   → on run queue, waiting to run
_Grunning    → executing on an M+P
_Gsyscall    → blocked in a syscall (no P held)
_Gwaiting    → blocked: chan, select, GC, sleep
_Gdead       → finished, can be recycled
_Gcopystack  → stack is being grown/shrunk
_Gpreempted  → preempted at safe-point
```

#### M (Machine — OS Thread)
```
Each M has:
  - A reference to the current G it's running
  - A reference to its associated P (nil when in syscall)
  - A g0 goroutine — special goroutine with a larger stack used
    for scheduler logic, signal handling, GC work
  - gsignal — goroutine for signal handling

M count is not bounded by GOMAXPROCS.
When a goroutine blocks in a syscall, the P is handed off
to a new or idle M so compute continues.
```

#### P (Processor — logical CPU context)
```go
// Simplified runtime.p struct
type p struct {
    id          int32
    status      uint32      // pidle, prunning, psyscall, pgcstop, pdead
    m           muintptr    // current M (nil if idle)
    runqhead    uint32      // local run queue (lock-free ring buffer)
    runqtail    uint32
    runq        [256]guintptr  // capacity: 256 goroutines
    runnext     guintptr    // next G to run (cache-hot)
    gFree       gList       // dead goroutines for reuse
    mcache      *mcache     // per-P memory allocator cache
    pcache      pageCache   // page cache
    // ... timers, tracing state, GC work buffers
}
```

**P count = GOMAXPROCS** (default: number of logical CPUs).  
**P is the key**: a G can only run when it has both an M and a P.

### Scheduler Algorithm — Step by Step

```
schedule() in runtime/proc.go — called by M in a tight loop:

1. Every 61 iterations: check Global Run Queue (GRQ) to prevent starvation
2. Check runnext on current P → run it (hottest path, L1-cache friendly)
3. Check local run queue (LRQ) — lock-free ring buffer, 256 cap
4. Check GRQ (with lock)
5. Check network poller (netpoll) — goroutines ready after I/O
6. WORK STEALING: pick a random P, steal half its LRQ
7. If nothing found: try GRQ again, netpoll again
8. Return P to idle pool, park M
```

### Work Stealing — ASCII Diagram

```
P0 (empty LRQ) wants work:

  P0            P1
  LRQ=[]        LRQ=[G1,G2,G3,G4,G5,G6]

  P0 steals half from P1:
  P0            P1
  LRQ=[G4,G5,G6]  LRQ=[G1,G2,G3]

Work stealing uses atomic CAS on runqhead/runqtail.
Stealing is done from the HEAD of victim's queue,
P runs from its own TAIL — this spatial separation
minimizes cache line contention.
```

### Preemption — From Cooperative to Asynchronous

**Go ≤ 1.13: Cooperative preemption**
- Goroutine yield points: function call prologues, channel ops, `runtime.Gosched()`
- Problem: tight loops without calls (e.g., `for {}`) could starve the scheduler

**Go 1.14+: Asynchronous preemption (signal-based)**
```
sysmon goroutine (runs without a P):
  - Polls every 10ms
  - Finds Gs running > 10ms
  - Sends SIGURG to the M running that G
  - Signal handler injects a preemption point via asyncPreempt()
  - G is suspended at the next safe-point (stack scan point)
```

```go
// Demonstration: async preemption working
package main

import (
    "fmt"
    "runtime"
    "time"
)

func busyLoop() {
    // In Go 1.13: this would starve other goroutines
    // In Go 1.14+: SIGURG preempts this at safe points
    for {
        // tight loop — no explicit yield
    }
}

func main() {
    runtime.GOMAXPROCS(1) // single P to make starvation visible
    go busyLoop()
    
    // This will actually print in Go 1.14+ (async preemption works)
    // It would NOT print in Go 1.13 (cooperative only)
    time.Sleep(10 * time.Millisecond)
    fmt.Println("main goroutine still runs — preemption works!")
}
```

### Syscall Handling — The P Handoff Protocol

```
Goroutine G calls a blocking syscall (e.g., read()):

  BEFORE syscall:
  ┌──────┐     ┌──────┐
  │  M0  │ ←── │  P0  │   M0 holds P0
  │  G   │     └──────┘
  └──────┘

  entersyscall():
    - G.status = _Gsyscall
    - M saves P reference but RELEASES P
    - P.status = _Psyscall

  DURING syscall (OS blocks M0):
  ┌──────┐      ┌──────┐     ┌──────┐
  │  M0  │      │  P0  │ ←── │  M1  │  (M1 acquired P0 — work continues!)
  │  G   │      └──────┘     └──────┘
  │(block)│
  └──────┘

  exitsyscall():
    - Try to reacquire any idle P
    - If no P available: G placed on GRQ, M parks
    - If retransition fast path (< 20µs): M reacquires original P
```

### sysmon — The Background Watchdog

```
sysmon runs in its own OS thread (no P required):

Responsibilities:
  1. Retract Ps from syscall-blocked Ms (handoff)
  2. Preempt long-running Gs (> 10ms) via SIGURG
  3. Force GC if > 2min since last GC
  4. Process network I/O ready events (netpoll)
  5. Unblock timers whose deadline has passed
  6. Handle expired finalizers

Poll interval: starts at 20µs, backs off to 10ms
```

### runnable code: Scheduler Observation

```go
// file: scheduler_demo.go
package main

import (
    "fmt"
    "runtime"
    "sync"
    "time"
)

func cpuBound(id int, wg *sync.WaitGroup) {
    defer wg.Done()
    sum := 0
    for i := 0; i < 1_000_000; i++ {
        sum += i
    }
    fmt.Printf("G%d done: sum=%d on thread %d\n", id, sum, getThreadID())
}

// Use runtime.LockOSThread to observe M binding
func getThreadID() int {
    // Not directly accessible — use debug/pprof in real code
    return 0
}

func main() {
    procs := runtime.GOMAXPROCS(0)
    fmt.Printf("GOMAXPROCS=%d, NumCPU=%d\n", procs, runtime.NumCPU())

    var wg sync.WaitGroup
    start := time.Now()
    
    // Launch 10x more goroutines than Ps to observe scheduling
    for i := 0; i < procs*10; i++ {
        wg.Add(1)
        go cpuBound(i, &wg)
    }
    
    wg.Wait()
    fmt.Printf("All goroutines done in %v\n", time.Since(start))
    
    // Observe scheduler stats
    var stats runtime.MemStats
    runtime.ReadMemStats(&stats)
    fmt.Printf("GC cycles: %d\n", stats.NumGC)
}
```

```bash
# Run with scheduler tracing
GODEBUG=schedtrace=1000 go run scheduler_demo.go

# Output format:
# SCHED 1000ms: gomaxprocs=8 idleprocs=3 threads=10 spinningthreads=1 
#               idlethreads=3 runqueue=2 [1 0 0 0 1 0 0 0]
#                                                ↑ LRQ lengths per P
```

### Common Interview Questions on GMP

**Q: What happens when GOMAXPROCS=1 and you have 1000 goroutines?**  
A: Single P, single M running at a time. All 1000 Gs share one P. Context switching is purely in userspace (no OS involvement). Goroutines cooperate via scheduler yield points + async preemption. Total M count can still grow if Gs make blocking syscalls.

**Q: Why does Go use M:N threading instead of 1:1?**  
A: 1:1 (one OS thread per goroutine, like Java threads pre-virtual threads) costs 1–8 MB stack per thread, ~1µs context switch via OS. Go goroutines start at 2–8 KB, switch in nanoseconds in userspace. M:N lets you run millions of concurrent goroutines.

**Q: Can goroutines migrate between Ps?**  
A: Yes — when a G is stolen from P1's run queue by P0's work stealer. Also when a G exits a syscall and must reacquire any available P. A G is NOT pinned to a P unless `runtime.LockOSThread()` is called (which locks G's M to the current OS thread).

**Q: What is `runtime.LockOSThread()` and when do you use it?**  
A: Locks the calling goroutine to its current OS thread (M). Used when: calling C libraries that use thread-local storage (e.g., OpenGL, some database drivers), OS-level thread affinity, signal handlers. Must be balanced with `runtime.UnlockOSThread()`.

**Q: What is `runnext` field on P?**  
A: A single-slot cache on P for the "next" goroutine to run, bypassing the LRQ. When a goroutine spawns another (`go f()`), the new G often goes into `runnext` to exploit temporal locality — the spawner likely left data the spawned goroutine will use hot in cache.

---

## 2. Goroutines — Internals & Lifecycle

### Stack Growth — Segmented vs Contiguous

**Go ≤ 1.3: Segmented stacks**
```
Problem: Hot split — function near stack boundary called in tight loop
         → constant stack segment allocation/deallocation
```

**Go 1.4+: Contiguous stacks (copy-on-grow)**
```
Initial size: 2KB (was 8KB before 1.4)
Stack check: Every function prologue checks if SP < stackguard0

Growth algorithm:
  1. Allocate new stack 2x the current size
  2. Copy all frames to new stack
  3. Adjust all pointers within stack (stack scanning)
  4. Update all goroutine references
  5. Release old stack

Shrink: After GC, if stack is 1/4 used → shrink to half
```

```
Initial:  [──2KB──]
Overflow: [────4KB────]   (copied + adjusted)
Overflow: [────────8KB────────]
Max:      1GB (configurable via runtime/debug.SetMaxStack)
```

### Goroutine Creation — newproc()

```
go f(arg1, arg2) compiles to:

1. runtime.newproc(siz int32, fn *funcval) called
2. Goroutine struct (g) allocated:
   - From P's gFree list (dead goroutine pool) — reuse
   - Or from heap if pool empty
3. Arguments copied to new goroutine's stack
4. G.sched.pc = fn address
5. G.sched.sp = top of new stack
6. G placed in runnext of current P (or GRQ if P full)
7. If there's an idle P with no M: wake or create M

Cost: ~2-4µs goroutine creation (vs 1ms+ for OS thread)
```

### Goroutine Parking & Waking

```go
// How channel receive parks a goroutine (simplified):

// 1. G calls chanrecv()
// 2. Channel is empty → need to wait
// 3. gopark() called:
//    - G.status = _Gwaiting
//    - G.waitreason = "chan receive"
//    - G recorded in channel's recvq (sudog)
//    - schedule() called → M picks next runnable G

// 4. Sender arrives, calls chansend()
// 5. Finds waiting G in recvq
// 6. goready(g) called:
//    - G.status = _Grunnable
//    - G placed in P's runnext (direct wake-up, no queue hop)
//    - If sender's P has no M: try to start one
```

### sudog — The Waiting Goroutine Descriptor

```go
// runtime.sudog — represents a G in a wait list
type sudog struct {
    g          *g         // the goroutine
    next       *sudog     // linked list
    prev       *sudog
    elem       unsafe.Pointer  // data being sent/received
    acquiretime int64
    releasetime int64
    ticket      uint32
    isSelect    bool       // participating in select
    success     bool       // whether chan op succeeded
    c           *hchan     // channel
}
// sudogs are pooled to avoid GC pressure
```

### Goroutine Leak Detection

```go
// file: goroutine_leak_test.go
package main

import (
    "fmt"
    "runtime"
    "time"
)

// LEAK: goroutine blocked forever on channel nobody writes to
func leakyFunc() {
    ch := make(chan int)
    go func() {
        <-ch // blocks forever — goroutine leaked!
    }()
    // ch goes out of scope, nobody closes it
    // goroutine is alive until program exits
}

// FIX: use context for cancellation
func fixedFunc(done <-chan struct{}) {
    ch := make(chan int)
    go func() {
        select {
        case v := <-ch:
            fmt.Println(v)
        case <-done:
            return // clean exit
        }
    }()
}

func countGoroutines() int {
    return runtime.NumGoroutine()
}

func main() {
    before := countGoroutines()
    
    for i := 0; i < 100; i++ {
        leakyFunc()
    }
    
    time.Sleep(10 * time.Millisecond)
    after := countGoroutines()
    
    fmt.Printf("Before: %d goroutines\n", before)
    fmt.Printf("After:  %d goroutines\n", after)
    fmt.Printf("Leaked: %d goroutines\n", after-before)
    
    // In production: use goleak library
    // import "go.uber.org/goleak"
    // defer goleak.VerifyNone(t)
}
```

```bash
go run goroutine_leak_test.go
# Output:
# Before: 1 goroutines
# After:  101 goroutines
# Leaked: 100 goroutines
```

### g0 — The Scheduler's Own Stack

```
Every M has a g0 goroutine with a much larger stack (8KB on Linux → grows to system limit).

g0 is used for:
  - schedule() — the scheduler loop itself
  - GC root scanning
  - Stack copying during growth
  - signal handling
  - defer unwinding during panic

Execution alternates between:
  g0 stack (scheduler work) ←→ goroutine stack (user code)

mcall(fn) — switch from goroutine stack to g0 stack
gogo(buf) — switch from g0 stack to goroutine stack
```

---

## 3. Channels — Implementation Deep Dive

### Mental Model
A channel is a **typed, thread-safe, optionally-buffered queue** backed by a mutex, two waiting queues (senders & receivers), and a circular buffer.

### hchan struct — The Real Implementation

```go
// runtime/chan.go — simplified
type hchan struct {
    qcount   uint           // total elements in queue
    dataqsiz uint           // buffer size (cap)
    buf      unsafe.Pointer // circular buffer pointer
    elemsize uint16         // element size in bytes
    closed   uint32         // 0 = open, 1 = closed
    elemtype *_type         // element type (for GC)
    sendx    uint           // send index (write head)
    recvx    uint           // recv index (read tail)
    recvq    waitq          // goroutines waiting to receive (sudog list)
    sendq    waitq          // goroutines waiting to send (sudog list)
    lock     mutex          // protects all fields
}

type waitq struct {
    first *sudog
    last  *sudog
}
```

### Channel Memory Layout

```
Unbuffered channel (make(chan T)):
  dataqsiz = 0, buf = nil
  ┌─────────────────────────┐
  │ lock │ recvq │ sendq    │
  └─────────────────────────┘
  Every send blocks until a receiver is ready (rendezvous)

Buffered channel (make(chan T, 3)):
  ┌──────────────────────────────────────────────────────┐
  │ lock │ qcount=1 │ dataqsiz=3 │ sendx=1 │ recvx=0   │
  │ buf → [T0][ ][ ]   (circular ring buffer)            │
  │        ↑recvx  ↑sendx                                │
  └──────────────────────────────────────────────────────┘
```

### Send Operation — chansend() State Machine

```
chansend(c *hchan, ep unsafe.Pointer, block bool):

Case 1: Receiver waiting in recvq (recvq.first != nil)
  → Direct copy: sender's data → receiver's stack (NO buffer involved!)
  → goready(receiver) — wake receiver
  → Return immediately (fastest path, no lock needed for data copy)
  
  This is called "direct send" — avoids buffering entirely.
  Even in buffered channels, if a receiver is already blocked,
  data goes directly to receiver's stack.

Case 2: Buffer has space (qcount < dataqsiz)
  → Copy data into buf[sendx]
  → Increment sendx (mod dataqsiz)
  → Increment qcount
  → Return

Case 3: No receiver, buffer full (or unbuffered)
  → If non-blocking (select): return false
  → Create sudog for current G
  → Add to sendq
  → gopark() — suspend current G
  → When woken: data was consumed, return

Case 4: Channel closed
  → panic("send on closed channel")
```

### Receive Operation — chanrecv() State Machine

```
chanrecv(c *hchan, ep unsafe.Pointer, block bool):

Case 1: Sender waiting in sendq
  Subcase A: Buffered channel (buf not empty)
    → Copy buf[recvx] to receiver (the old data)
    → Copy sender's data into buf[sendx] (maintain order)
    → Advance recvx, wake sender
  Subcase B: Unbuffered channel OR empty buffer
    → Direct copy: sender's stack → receiver's memory
    → goready(sender)

Case 2: Buffer has data (qcount > 0)
  → Copy buf[recvx] to ep
  → Advance recvx, decrement qcount

Case 3: Channel empty, no sender
  → If closed: return zero value, ok=false
  → If non-blocking: return false
  → Create sudog, add to recvq, gopark()

Case 4: Channel closed and empty
  → Return zero value, ok=false (no panic)
```

### Channel Direction — Type System Enforcement

```go
// Bidirectional (read/write)
ch := make(chan int, 10)

// Send-only — compiler enforces, zero runtime cost
var sendOnly chan<- int = ch

// Receive-only  
var recvOnly <-chan int = ch

// Conversion: bidirectional → directional (implicit)
// Directional → bidirectional: NOT ALLOWED (compile error)

// Why? Enforces producer/consumer contracts at compile time
// Pattern: return <-chan T from constructors
func producer() <-chan int {
    ch := make(chan int, 10)
    go func() {
        for i := 0; i < 10; i++ {
            ch <- i
        }
        close(ch)
    }()
    return ch // caller can only receive
}
```

### Select — Implementation

```go
// select compiles to runtime.selectgo()
// selectgo algorithm:
// 1. Gather all cases into a slice of scase structs
// 2. Lock ALL involved channels (sorted by address to prevent deadlock)
// 3. Poll each case (ready to proceed without blocking?)
//    - Found ready case: execute it, unlock all, return
// 4. If default: execute it
// 5. All channels blocked: add G to ALL channels' send/recvq
// 6. gopark() — sleep
// 7. When any channel becomes ready: G woken, remove from all other queues
// 8. Execute the ready case

// Important: case selection among multiple ready cases is PSEUDO-RANDOM
// This is intentional — prevents starvation

select {
case v := <-ch1:
    // handle ch1
case ch2 <- v:
    // handle ch2
case <-time.After(1 * time.Second):
    // timeout
default:
    // non-blocking poll
}
```

### Channel Pitfalls & Patterns

```go
// file: channel_patterns.go
package main

import (
    "fmt"
    "sync"
    "time"
)

// ── PITFALL 1: Ranging over channel — must close ──────────────────────
func rangeExample() {
    ch := make(chan int, 5)
    go func() {
        for i := 0; i < 5; i++ {
            ch <- i
        }
        close(ch) // MUST close — otherwise range blocks forever
    }()
    for v := range ch {
        fmt.Println(v)
    }
}

// ── PITFALL 2: Closing from multiple goroutines → panic ───────────────
// FIX: use sync.Once
type SafeChan[T any] struct {
    ch   chan T
    once sync.Once
}

func (sc *SafeChan[T]) Close() {
    sc.once.Do(func() { close(sc.ch) })
}

// ── PITFALL 3: nil channel blocks forever ─────────────────────────────
// BUT: nil channel in select is ignored (never selected)
// This is a useful pattern!
func mergeChannels(ch1, ch2 <-chan int) <-chan int {
    out := make(chan int)
    go func() {
        defer close(out)
        for ch1 != nil || ch2 != nil {
            select {
            case v, ok := <-ch1:
                if !ok {
                    ch1 = nil // nil channel → ignored in future selects
                    continue
                }
                out <- v
            case v, ok := <-ch2:
                if !ok {
                    ch2 = nil
                    continue
                }
                out <- v
            }
        }
    }()
    return out
}

// ── PATTERN: Done channel (broadcast) ────────────────────────────────
func broadcastDone() {
    done := make(chan struct{})
    
    for i := 0; i < 5; i++ {
        go func(id int) {
            select {
            case <-done:
                fmt.Printf("worker %d: stopping\n", id)
            case <-time.After(1 * time.Second):
                fmt.Printf("worker %d: timed out\n", id)
            }
        }(i)
    }
    
    time.Sleep(100 * time.Millisecond)
    close(done) // BROADCAST: all goroutines receive from closed channel
}

// ── PATTERN: Pipeline ────────────────────────────────────────────────
func pipeline() {
    gen := func(nums ...int) <-chan int {
        out := make(chan int)
        go func() {
            defer close(out)
            for _, n := range nums {
                out <- n
            }
        }()
        return out
    }
    
    square := func(in <-chan int) <-chan int {
        out := make(chan int)
        go func() {
            defer close(out)
            for n := range in {
                out <- n * n
            }
        }()
        return out
    }
    
    for n := range square(square(gen(2, 3, 4))) {
        fmt.Println(n) // 16, 81, 256
    }
}

func main() {
    rangeExample()
    broadcastDone()
    time.Sleep(200 * time.Millisecond)
    pipeline()
}
```

---

## 4. Go Memory Model & Happens-Before

### Why This Matters
The Go memory model defines **when a write to a variable in one goroutine is guaranteed to be observed by a read of that variable in another goroutine**. Without this understanding, you write code that works on your machine but fails in production due to CPU reordering or compiler optimization.

### Happens-Before (HB) Relation

```
A happens-before B (A → B) means:
  All memory writes done by A are visible to B.

If A does NOT happen-before B:
  B may see a stale value, even if A ran "before" B in wall-clock time.
  CPUs and compilers reorder instructions freely unless synchronization prevents it.
```

### Guaranteed HB Edges in Go

```
1. Within a goroutine: sequential order is preserved
   x = 1    → (happens before) → y = x
   
2. Goroutine creation:
   go stmt happens-before goroutine body starts
   x = 1; go f()  → f() sees x==1
   
3. Goroutine completion:
   goroutine exit does NOT happen-before anything by default
   Must use sync.WaitGroup or channel to synchronize

4. Channel send happens-before corresponding receive completes:
   ch <- v  → (happens before) → v := <-ch
   
5. Channel close happens-before receive of zero value:
   close(ch)  → (happens before) → <-ch returns (zero, false)
   
6. Receive from UNBUFFERED channel happens-before send completes:
   <-ch  → (happens before) → ch <- v  (rendezvous guarantee)
   
7. sync.Mutex:
   l.Unlock() → (happens before) → l.Lock() (next lock acquisition)
   
8. sync.Once:
   f() in once.Do(f) → (happens before) → any once.Do(f) return
   
9. sync/atomic:
   atomic.Store → (happens before) → atomic.Load (if sequentially consistent)
```

### Race Condition Examples

```go
// file: memory_model.go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// ── DATA RACE (undefined behavior) ───────────────────────────────────
var counter int // shared, no synchronization

func badIncrement() {
    for i := 0; i < 1000; i++ {
        counter++ // READ-MODIFY-WRITE: not atomic!
        // compiles to: LOAD counter; ADD 1; STORE counter
        // two goroutines can both load the same value
    }
}

// ── FIX 1: Mutex ─────────────────────────────────────────────────────
var (
    mu      sync.Mutex
    counter2 int
)

func safeIncrement() {
    mu.Lock()
    counter2++
    mu.Unlock()
}

// ── FIX 2: atomic ────────────────────────────────────────────────────
var counter3 atomic.Int64

func atomicIncrement() {
    counter3.Add(1)
}

// ── SUBTLE RACE: double-checked locking (WRONG) ───────────────────────
type Singleton struct{ value int }
var instance *Singleton

func badGetInstance() *Singleton {
    if instance == nil {   // read without lock — DATA RACE
        mu.Lock()
        if instance == nil {
            instance = &Singleton{value: 42}  // write
        }
        mu.Unlock()
    }
    return instance
}
// Problem: CPU/compiler may reorder: instance ptr stored BEFORE struct fully written
// Another goroutine sees non-nil instance but reads uninitialized struct fields

// ── FIX: sync.Once (uses memory barrier internally) ───────────────────
var (
    once     sync.Once
    instance2 *Singleton
)

func goodGetInstance() *Singleton {
    once.Do(func() {
        instance2 = &Singleton{value: 42}
    })
    return instance2
}

// ── SUBTLE: goroutine sees stale value ───────────────────────────────
func staleRead() {
    done := false
    
    go func() {
        // Compiler might cache `done` in register
        // CPU might read stale value from cache
        for !done { } // BUG: might loop forever
    }()
    
    done = true // Write without synchronization
}

// FIX: use atomic or channel
func fixedStaleRead() {
    var done atomic.Bool
    
    go func() {
        for !done.Load() { }
        fmt.Println("done!")
    }()
    
    done.Store(true)
}

func main() {
    var wg sync.WaitGroup
    
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func() {
            defer wg.Done()
            atomicIncrement()
        }()
    }
    wg.Wait()
    fmt.Println("Counter:", counter3.Load()) // Always 100
}
```

```bash
# Detect races at runtime
go run -race memory_model.go
go test -race ./...
```

### Memory Barriers — What They Actually Do

```
Modern CPUs (x86, ARM) reorder memory operations for performance.
A memory barrier (fence) tells the CPU: 
  "Complete all pending loads/stores before this point"

Go's sync primitives insert barriers automatically:
  - sync.Mutex.Lock/Unlock: full memory fence
  - atomic operations: at minimum acquire/release semantics
  - channel operations: full fence via runtime lock

On x86: TSO (Total Store Order) — writes are not reordered with other writes,
         so many races only manifest on ARM/POWER.
Always test with -race flag. Never rely on "it works on x86".
```

---

## 5. Garbage Collector — Tri-Color Concurrent GC

### One-Line Explanation
Go's GC uses a concurrent, tri-color, mark-sweep algorithm that runs mostly alongside your application with very short stop-the-world pauses.

### Tri-Color Invariant

```
Three sets of objects:

  WHITE: Not yet reached — will be collected if still white at end
  GRAY:  Reached but children not yet scanned (worklist)
  BLACK: Reached and all children scanned — definitely live

Invariant: No black object points DIRECTLY to a white object.
           (If it did, white object would be incorrectly collected)

This invariant is maintained by the WRITE BARRIER.
```

### GC Phases

```
┌─────────────────────────────────────────────────────────────────────┐
│  GC Cycle Timeline                                                   │
│                                                                      │
│  ┌─────────┐ ┌────────────────────────────┐ ┌───────┐ ┌──────────┐ │
│  │  Mark   │ │     Concurrent Marking     │ │ Mark  │ │  Sweep   │ │
│  │  Setup  │ │  (runs alongside mutators) │ │Termin │ │(concurr.)│ │
│  │  STW    │ │                            │ │  STW  │ │          │ │
│  └─────────┘ └────────────────────────────┘ └───────┘ └──────────┘ │
│      ↑               ↑                           ↑                  │
│    ~0.1ms          majority                    ~0.1ms               │
│                   of GC time                                        │
│                                                                      │
│  STW = Stop The World (all goroutines paused)                       │
│  Total STW target: < 500µs per cycle                                │
└─────────────────────────────────────────────────────────────────────┘
```

### Phase 1: Mark Setup (STW)

```
- All goroutines paused (STW)
- Enable write barrier on ALL goroutines
- Initialize GC work queues
- Scan stack roots of all goroutines
- Duration: O(goroutines) — typically < 0.1ms
- Why STW? Write barrier must be atomic across all goroutines
```

### Phase 2: Concurrent Marking

```
Write barrier is active. Mutators (your code) keep running.

Mark workers (goroutines) scan the heap:
  1. Start with gray set (roots: globals, stacks)
  2. For each gray object:
     a. Scan its pointers
     b. Add any white objects found to gray set
     c. Color this object black
  3. Repeat until gray set is empty

Mark worker modes:
  - Dedicated: 25% of Ps dedicated to GC (GOGC controls this)
  - Fractional: background workers stealing time
  - Idle: workers that run when P has no user goroutines

Mutator assist:
  If your goroutine allocates faster than GC can mark,
  your goroutine is "taxed" and must do GC work itself.
  This prevents runaway allocation during GC.
```

### The Write Barrier — Dijkstra + Yuasa Hybrid

```
Go 1.7+ uses a hybrid write barrier (Dijkstra insertion + Yuasa deletion):

On pointer write: *ptr = new_value

  // Shade the old value gray (Yuasa deletion barrier)
  shade(*ptr)    // old pointer target → gray
  
  // Shade the new value gray (Dijkstra insertion barrier)  
  shade(new_value)  // new pointer target → gray
  
  // Perform the write
  *ptr = new_value

Why both?
  Yuasa: handles "object removed from graph" race
  Dijkstra: handles "object added to black object" race
  
  Together: no scanning of stacks needed at Mark Termination
  (Before Go 1.7: stacks had to be re-scanned STW — much slower)

Cost of write barrier: ~10-15ns per pointer write
                       Only active during GC mark phase
```

### Phase 3: Mark Termination (STW)

```
- Pause all goroutines (STW again)
- Flush all local work queues
- Disable write barrier
- Perform final mark of any remaining gray objects
- Duration: typically < 0.1ms
```

### Phase 4: Concurrent Sweep

```
- Goroutines resume immediately
- Sweeper goroutine runs concurrently
- Sweeps span by span: any white object → return to allocator
- Free memory is added to size-class free lists
- Lazy sweeping: next allocation triggers sweep of needed spans
```

### GOGC — The Knob

```
GOGC=100 (default):
  GC triggers when heap has grown 100% beyond live set after last GC.
  Example: 50MB live → GC at 100MB total heap

GOGC=200: GC less frequently, more memory used
GOGC=50:  GC more frequently, less memory (more CPU overhead)
GOGC=off: Disable GC entirely (use only if you know what you're doing)

Go 1.19+: GOMEMLIMIT=500MiB
  Soft memory limit — GC will run more aggressively to stay under limit
  More useful than GOGC for memory-constrained environments
```

```go
// file: gc_tuning.go
package main

import (
    "fmt"
    "runtime"
    "runtime/debug"
    "time"
)

func allocateHeavily() {
    // Allocate many short-lived objects
    for i := 0; i < 1000; i++ {
        _ = make([]byte, 1024*1024) // 1MB each, immediately eligible for GC
    }
}

func measureGC(label string, fn func()) {
    var before, after runtime.MemStats
    runtime.ReadMemStats(&before)
    
    start := time.Now()
    fn()
    elapsed := time.Since(start)
    
    runtime.ReadMemStats(&after)
    
    fmt.Printf("%s:\n", label)
    fmt.Printf("  Duration:      %v\n", elapsed)
    fmt.Printf("  GC cycles:     %d\n", after.NumGC-before.NumGC)
    fmt.Printf("  GC pause (ns): %d\n", after.PauseTotalNs-before.PauseTotalNs)
    fmt.Printf("  Heap after:    %d KB\n", after.HeapAlloc/1024)
}

func main() {
    // Default GOGC=100
    measureGC("Default (GOGC=100)", allocateHeavily)
    
    // Aggressive GC
    debug.SetGCPercent(25)
    measureGC("Aggressive (GOGC=25)", allocateHeavily)
    
    // Lazy GC
    debug.SetGCPercent(500)
    measureGC("Lazy (GOGC=500)", allocateHeavily)
    
    // Set memory limit (Go 1.19+)
    debug.SetMemoryLimit(100 * 1024 * 1024) // 100MB
    measureGC("With MemLimit=100MB", allocateHeavily)
    
    // Force GC
    runtime.GC()
    
    // Read detailed GC stats
    var stats debug.GCStats
    debug.ReadGCStats(&stats)
    fmt.Printf("\nGC Stats:\n")
    fmt.Printf("  Last GC: %v\n", stats.LastGC)
    fmt.Printf("  Num GC:  %d\n", stats.NumGC)
    fmt.Printf("  Pause:   %v\n", stats.PauseTotal)
}
```

```bash
# Enable GC trace
GODEBUG=gctrace=1 go run gc_tuning.go

# Output format:
# gc 1 @0.001s 5%: 0.012+0.58+0.019 ms clock, 0.049+0/0.58/0+0.076 ms cpu, 4->4->0 MB, 5 MB goal, 0 MB stacks, 0 MB globals, 8 P
#    ↑              ↑               ↑                   ↑              ↑          ↑
#  cycle#         STW+conc       STW+conc           heap sizes      GOGC goal  procs
```

### Finalizers

```go
// Finalizers run when object is about to be GC'd
// WARNING: Finalizers are NOT guaranteed to run, and run in arbitrary order

type Resource struct {
    handle uintptr
}

func NewResource() *Resource {
    r := &Resource{handle: allocHandle()}
    runtime.SetFinalizer(r, func(r *Resource) {
        freeHandle(r.handle) // cleanup when GC collects r
    })
    return r
}

// Problems with finalizers:
// 1. May delay GC (object survives one extra cycle)
// 2. Not called if program exits normally
// 3. Not called in deterministic order
// 4. Can cause memory/resource leaks if objects form cycles

// Prefer: explicit Close() methods + defer + io.Closer interface
```

---

## 6. Escape Analysis & Stack vs Heap

### One-Line Explanation
The Go compiler decides at compile time whether a variable lives on the goroutine's stack (cheap, no GC pressure) or the heap (GC-managed, more expensive).

### Stack vs Heap Tradeoffs

```
Stack allocation:
  ✓ O(1) cost — just decrement SP
  ✓ No GC pressure — cleaned up with stack frame
  ✓ Cache-friendly — linear memory
  ✗ Must not outlive the function (or stack frame)
  Max size: limited by goroutine stack (grows to ~1GB)

Heap allocation:
  ✓ Can outlive any function
  ✓ Shared between goroutines
  ✗ GC pressure — scanner must trace it
  ✗ Fragmentation
  ✗ malloc overhead (~20-100ns vs ~1ns for stack)
```

### When Does Escape Happen?

```
1. Variable's address taken AND returned:
   func f() *int { x := 42; return &x }  → x escapes to heap

2. Variable stored in interface:
   var i interface{} = myStruct{}  → myStruct may escape
   
3. Variable stored in slice/map/channel that escapes:
   s := []int{1, 2, 3}
   global = s  → s escapes

4. Variable too large for stack:
   x := [10000]int{}  → may escape to heap

5. Variable captured by closure AND closure escapes:
   f := func() { use(x) }
   go f()  → x may escape

6. reflect operations:
   reflect.ValueOf(x)  → x may escape

7. send on channel:
   ch <- largeStruct{}  → largeStruct may escape

8. fmt.Println and similar:
   fmt.Println(x)  → x ALWAYS escapes (interface{} parameter)
```

### Analyzing Escape with -gcflags

```go
// file: escape_analysis.go
package main

import "fmt"

// Stack allocated — returned by value
func stackAlloc() int {
    x := 42      // stack
    return x     // value copy — x stays on stack
}

// Heap allocated — returned by pointer
func heapAlloc() *int {
    x := 42      // escapes to heap
    return &x    // address returned — must outlive function
}

// Escape via interface
func escapeViaInterface(v interface{}) {
    fmt.Println(v) // v escapes because fmt.Println is opaque to compiler
}

// Does NOT escape — compiler inlines and sees no escape
func noEscape() {
    x := 42
    y := &x     // y points to x
    *y = 100    // through pointer, but...
    _ = x       // x never escapes — compiler proves this
}

// Large array — may escape
func largeArray() *[1000000]int {
    arr := [1000000]int{} // too large for stack → heap
    return &arr
}

// Closure captures — does x escape?
func closureEscape() func() int {
    x := 42
    return func() int {
        return x // x captured by closure → escapes to heap
    }
}

// Closure captures — x doesn't escape
func closureNoEscape() {
    x := 42
    f := func() int { return x }
    _ = f // f doesn't escape (not returned/stored) → x may stay on stack
    // (compiler-dependent optimization)
}

func main() {
    fmt.Println(stackAlloc())
    p := heapAlloc()
    fmt.Println(*p)
}
```

```bash
# See escape analysis decisions
go build -gcflags="-m -m" escape_analysis.go 2>&1 | head -40

# Output examples:
# ./escape_analysis.go:10:2: x does not escape
# ./escape_analysis.go:16:2: moved to heap: x
# ./escape_analysis.go:22:14: v does not escape (if inlined)
# ./escape_analysis.go:22:14: ... argument does not escape
```

### Reducing Allocations — Practical Techniques

```go
// file: alloc_reduction.go
package main

import (
    "bytes"
    "fmt"
    "strings"
    "sync"
)

// ── Technique 1: sync.Pool for reusable objects ───────────────────────
var bufPool = sync.Pool{
    New: func() interface{} {
        return &bytes.Buffer{}
    },
}

func processWithPool(data string) string {
    buf := bufPool.Get().(*bytes.Buffer)
    defer func() {
        buf.Reset()
        bufPool.Put(buf)
    }()
    
    buf.WriteString("processed: ")
    buf.WriteString(data)
    return buf.String()
}

// ── Technique 2: Pre-allocate slices ──────────────────────────────────
func badAppend(items []string) []string {
    var result []string // starts with cap=0
    for _, item := range items {
        result = append(result, item) // repeated allocations + copies
    }
    return result
}

func goodAppend(items []string) []string {
    result := make([]string, 0, len(items)) // pre-allocate exact capacity
    for _, item := range items {
        result = append(result, item) // no reallocations
    }
    return result
}

// ── Technique 3: Avoid interface boxing of small types ────────────────
type Processor interface {
    Process(int) int
}

type square struct{}
func (s square) Process(x int) int { return x * x }

// Interface call: stores type pointer + value → may allocate if value > pointer size
// For concrete types ≤ pointer size: no allocation (fits in interface word)
// For structs: allocation on interface conversion

// ── Technique 4: strings.Builder vs concatenation ─────────────────────
func badConcat(parts []string) string {
    s := ""
    for _, p := range parts {
        s += p  // O(n²): each += allocates new string
    }
    return s
}

func goodConcat(parts []string) string {
    var b strings.Builder
    b.Grow(estimateLen(parts)) // pre-allocate
    for _, p := range parts {
        b.WriteString(p)
    }
    return b.String()
}

func estimateLen(parts []string) int {
    n := 0
    for _, p := range parts {
        n += len(p)
    }
    return n
}

// ── Technique 5: Value receivers vs pointer receivers ─────────────────
type SmallStruct struct{ x, y int } // 16 bytes — fits in registers

// Value receiver: copy of struct (16 bytes) — may be more cache-friendly
func (s SmallStruct) Sum() int { return s.x + s.y }

type LargeStruct struct{ data [1024]byte }

// Pointer receiver: no copy — correct for large structs
func (ls *LargeStruct) Process() { _ = ls.data }

func main() {
    parts := []string{"hello", " ", "world", "!"}
    fmt.Println(goodConcat(parts))
    fmt.Println(processWithPool("data"))
}
```

```bash
# Benchmark to see allocation counts
go test -bench=. -benchmem ./...

# Output:
# BenchmarkBadConcat-8    100000    15234 ns/op    12480 B/op    19 allocs/op
# BenchmarkGoodConcat-8   500000     2890 ns/op      512 B/op     2 allocs/op
```

---

## 7. Interfaces — Fat Pointers, Dynamic Dispatch, nil traps

### Interface Internal Representation

```
Non-empty interface (interface with methods):
  ┌──────────────────────────────────────────┐
  │  iface                                    │
  │  ┌─────────────┬──────────────────────┐  │
  │  │   *itab     │    data pointer       │  │
  │  │  (type info │    (or value if       │  │
  │  │  + methods) │     fits in word)     │  │
  │  └─────────────┴──────────────────────┘  │
  └──────────────────────────────────────────┘

Empty interface (interface{}  / any):
  ┌──────────────────────────────────────────┐
  │  eface                                    │
  │  ┌─────────────┬──────────────────────┐  │
  │  │   *_type    │    data pointer       │  │
  │  │  (type desc)│    (or value)         │  │
  │  └─────────────┴──────────────────────┘  │
  └──────────────────────────────────────────┘
```

### itab — The Method Table

```go
// runtime/iface.go
type itab struct {
    inter  *interfacetype  // interface type descriptor
    _type  *_type          // concrete type descriptor
    hash   uint32          // copy of _type.hash (for type switches)
    _      [4]byte
    fun    [1]uintptr      // variable-length: method pointers
    // fun[0] == 0: concrete type does NOT implement interface
}

// itabs are cached in a global hash table keyed by (interface, concrete type)
// First call: compute + cache. Subsequent calls: O(1) lookup
```

### Dynamic Dispatch Cost

```
Interface method call:
  1. Load itab pointer from interface
  2. Load method pointer from itab.fun[offset]
  3. Call method via pointer

Concrete type call (devirtualized):
  Direct call — single instruction

Cost:
  Interface call: ~2-5ns extra (pointer indirection + no inlining)
  Compiler can devirtualize if concrete type is provable at compile time
  
Why no inlining?
  Method is called via pointer — compiler can't inline at call site
  (unless it can prove the concrete type at compile time)
```

### The nil Interface Trap — Most Common Go Bug

```go
// file: nil_interface_trap.go
package main

import "fmt"

type MyError struct {
    msg string
}

func (e *MyError) Error() string {
    if e == nil {
        return "<nil MyError>"
    }
    return e.msg
}

// TRAP: returns (*MyError)(nil) — a non-nil interface!
func dangerous() error {
    var err *MyError = nil
    // err has:
    //   type  = *MyError  (non-nil!)
    //   value = nil
    return err  // interface IS non-nil even though value is nil!
}

// CORRECT: return untyped nil
func safe() error {
    var err *MyError = nil
    if err != nil {
        return err
    }
    return nil  // type=nil, value=nil → interface IS nil
}

func main() {
    err := dangerous()
    fmt.Println(err == nil)       // false! (trap!)
    fmt.Println(err)              // <nil MyError>
    
    err2 := safe()
    fmt.Println(err2 == nil)      // true
    
    // Inspecting the interface internals
    printInterface(dangerous())
    printInterface(safe())
}

func printInterface(err error) {
    if err == nil {
        fmt.Println("nil interface: type=nil, value=nil")
        return
    }
    fmt.Printf("non-nil interface: type=%T, value=%v\n", err, err)
}

// Rule: NEVER return a concrete nil pointer as an interface type.
// Always either return (nil) directly or check and return typed nil only if intended.
```

### Interface Satisfaction — Compile-Time Checks

```go
// Compile-time assertion that Type implements Interface
var _ io.Reader = (*MyReader)(nil)
var _ io.Writer = (*MyWriter)(nil)

// More explicit:
var _ fmt.Stringer = MyStruct{} // value receiver
var _ fmt.Stringer = &MyStruct{} // pointer receiver

// Why useful?
// Without this, you find out at runtime (type assertion failure)
// With this: compile error immediately
```

### Type Assertions & Type Switches

```go
// Type assertion — panics if wrong type
v := iface.(ConcreteType)

// Safe type assertion — never panics
v, ok := iface.(ConcreteType)
if !ok {
    // iface does not hold ConcreteType
}

// Type switch — efficient multi-type dispatch
func describe(i interface{}) string {
    switch v := i.(type) {
    case int:
        return fmt.Sprintf("int: %d", v)
    case string:
        return fmt.Sprintf("string: %q", v)
    case []byte:
        return fmt.Sprintf("[]byte len=%d", len(v))
    case nil:
        return "nil"
    default:
        return fmt.Sprintf("unknown: %T", v)
    }
    // Compiled to: compare hash field in itab against known hashes
    // Much faster than sequential type assertions
}
```

### Embedding vs Inheritance

```go
// Go has NO inheritance. It has embedding (composition).

type Animal struct {
    Name string
}

func (a Animal) Speak() string { return a.Name + " speaks" }

type Dog struct {
    Animal          // embedded — Dog "inherits" Animal's methods
    Breed string
}

// Dog promotes Animal's methods:
d := Dog{Animal: Animal{Name: "Rex"}, Breed: "Lab"}
d.Speak()      // calls Animal.Speak() via promotion
d.Animal.Speak() // explicit

// Embedding is NOT inheritance:
// - No polymorphism via embedded type
// - You cannot pass *Dog where *Animal is expected (no IS-A)
// - But *Dog implements any interface *Animal implements (promoted methods)
// - Override: define Speak() on Dog → shadows Animal.Speak()
```

---

## 8. Generics — Type Parameters, Constraints, Internals

### One-Line Explanation
Generics (Go 1.18+) allow writing type-safe, reusable functions and data structures without interface boxing, while constraints encode what operations are valid on a type.

### Syntax & Terminology

```go
// Type parameter syntax:
// func FuncName[TypeParam Constraint](args) ReturnType

func Map[T, U any](s []T, f func(T) U) []U {
    result := make([]U, len(s))
    for i, v := range s {
        result[i] = f(v)
    }
    return result
}

// Multiple constraints:
func Min[T constraints.Ordered](a, b T) T {
    if a < b { return a }
    return b
}

// Generic type:
type Stack[T any] struct {
    items []T
}

func (s *Stack[T]) Push(v T) { s.items = append(s.items, v) }
func (s *Stack[T]) Pop() (T, bool) {
    if len(s.items) == 0 {
        var zero T
        return zero, false
    }
    v := s.items[len(s.items)-1]
    s.items = s.items[:len(s.items)-1]
    return v, true
}
```

### Constraints — Deep Dive

```go
// file: generics_deep.go
package main

import (
    "fmt"
    "golang.org/x/exp/constraints"
)

// ── Constraint: interface with type set ───────────────────────────────
type Numeric interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64 |
    ~uint | ~uint8 | ~uint16 | ~uint32 | ~uint64 |
    ~float32 | ~float64
}

// ~ means: any type whose UNDERLYING type is int (includes type MyInt int)
type MyInt int // underlying type is int → satisfies ~int

func Sum[T Numeric](s []T) T {
    var total T
    for _, v := range s {
        total += v
    }
    return total
}

// ── Constraint with methods ───────────────────────────────────────────
type Stringer interface {
    String() string
}

// Combined: method AND type set
type PrintableNumber interface {
    Numeric
    fmt.Stringer
}

// ── Union types in constraints ─────────────────────────────────────────
type Signed interface {
    ~int | ~int8 | ~int16 | ~int32 | ~int64
}

// ── comparable — for map keys, == operator ────────────────────────────
func Contains[T comparable](s []T, target T) bool {
    for _, v := range s {
        if v == target {
            return true
        }
    }
    return false
}

// ── any = interface{} — least restrictive ────────────────────────────
func First[T any](s []T) (T, bool) {
    if len(s) == 0 {
        var zero T
        return zero, false
    }
    return s[0], true
}

// ── Generic map/filter/reduce ────────────────────────────────────────
func Filter[T any](s []T, pred func(T) bool) []T {
    var out []T
    for _, v := range s {
        if pred(v) {
            out = append(out, v)
        }
    }
    return out
}

func Reduce[T, U any](s []T, init U, f func(U, T) U) U {
    acc := init
    for _, v := range s {
        acc = f(acc, v)
    }
    return acc
}

// ── Generic Result type (like Rust's Result) ──────────────────────────
type Result[T any] struct {
    value T
    err   error
}

func Ok[T any](v T) Result[T]      { return Result[T]{value: v} }
func Err[T any](e error) Result[T] { return Result[T]{err: e} }

func (r Result[T]) Unwrap() (T, error) { return r.value, r.err }
func (r Result[T]) IsOk() bool          { return r.err == nil }

// ── Generic cache with expiry ─────────────────────────────────────────
import "sync"

type Cache[K comparable, V any] struct {
    mu    sync.RWMutex
    items map[K]V
}

func NewCache[K comparable, V any]() *Cache[K, V] {
    return &Cache[K, V]{items: make(map[K]V)}
}

func (c *Cache[K, V]) Set(key K, val V) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = val
}

func (c *Cache[K, V]) Get(key K) (V, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    v, ok := c.items[key]
    return v, ok
}

func main() {
    ints := []int{1, 2, 3, 4, 5}
    fmt.Println(Sum(ints))                    // 15 (inferred type)
    fmt.Println(Sum[float64]([]float64{1.1, 2.2})) // explicit
    
    evens := Filter(ints, func(x int) bool { return x%2 == 0 })
    fmt.Println(evens) // [2 4]
    
    total := Reduce(ints, 0, func(acc, x int) int { return acc + x })
    fmt.Println(total) // 15
    
    cache := NewCache[string, int]()
    cache.Set("age", 30)
    if v, ok := cache.Get("age"); ok {
        fmt.Println(v) // 30
    }
}
```

### Generics Internals — GCShape Stenciling

```
Go generics use GCShape stenciling (NOT full monomorphization like C++/Rust,
NOT boxing like Java's type erasure).

GCShape groups:
  All pointer types share ONE stencil (same shape to GC)
  All int types might share ONE stencil
  Custom-shaped types get their own stencil

Example:
  Map[*int, *string]  ─┐
  Map[*Dog, *Cat]     ─┼─ Same GCShape stencil: Map[*T, *U]
  Map[*Foo, *Bar]     ─┘     (one machine-code copy)

  Map[int, string]    → Different stencil (different GC shape)
  Map[float64, bool]  → Different stencil

Implication:
  - Less code bloat than full monomorphization
  - Pointer types: NO boxing, but all share one dictionary-based dispatch
  - Value types: may get own stencil → better optimization
  - Dictionaries: runtime type descriptors passed to shared stencils
```

### Generics Limitations (Go 1.22)

```
1. No generic methods on generic types:
   type Foo[T any] struct{}
   func (f Foo[T]) Bar[U any]() {} // COMPILE ERROR

2. No parameterized type aliases (yet — coming):
   type MySlice[T any] = []T  // works in 1.24+

3. Cannot use type params as type arguments to non-generic types:
   func f[T any]() { var m map[T]int } // ONLY if T is comparable

4. Type inference has limits — sometimes need explicit type params

5. Cannot range over generic integer:
   func f[T int|int64](n T) {
     for i := T(0); i < n; i++ {} // works
     // range n  // NOT supported (Go 1.22+ adds range-over-integer but not generic)
   }
```

---

## 9. sync, atomic & Low-Level Concurrency

### sync.Mutex — Implementation

```go
// runtime/lock_futex.go / lock_sema.go
// Mutex uses futex on Linux, semaphore on macOS/Windows

type Mutex struct {
    state int32  // 0=unlocked, bit0=locked, bit1=woken, bit2=starving
    sema  uint32 // semaphore for parking/waking
}

// State bit layout:
// bit 0: mutexLocked   — mutex is held
// bit 1: mutexWoken    — at least one waiter has been woken
// bit 2: mutexStarving — starvation mode
// bits 3+: waiter count

// Lock() fast path (no contention):
//   CAS(state, 0, 1) — atomic compare-and-swap
//   If succeeds: lock acquired, no OS involvement

// Lock() slow path (contention):
//   Spin for ~4 iterations (on multi-core, check if holder runs)
//   If still locked: park goroutine via semaphore (OS call)
//   When woken: retry CAS

// Starvation mode (Go 1.9+):
//   If a goroutine waits > 1ms: mutex enters starvation mode
//   In starvation mode: new Lock() callers go directly to queue end
//   Prevents indefinite starvation of waiting goroutines
```

### sync.RWMutex — Readers-Writer Lock

```go
// Multiple concurrent readers OR one exclusive writer

type RWMutex struct {
    w           Mutex  // held if there are pending writers
    writerSem   uint32 // semaphore for writers to wait for readers
    readerSem   uint32 // semaphore for readers to wait for writers
    readerCount atomic.Int32 // number of pending readers
    readerWait  atomic.Int32 // number of departing readers
}

// RLock: atomic increment of readerCount
//   If writer waiting: park reader
// RUnlock: atomic decrement
//   If last reader and writer waiting: wake writer

// Lock: set negative flag on readerCount (signals writer wants lock)
//   Wait for all current readers to finish (readerWait counter)
//   Then hold exclusive lock

// When to use RWMutex vs Mutex:
//   Read-heavy workloads (many goroutines reading, few writing)
//   RWMutex is slower than Mutex when write-heavy (more bookkeeping)
//   Rule: profile before assuming RWMutex is faster
```

### sync.WaitGroup — Internals

```go
type WaitGroup struct {
    noCopy noCopy    // vet checker: prevents copying after first use
    state  atomic.Uint64 // high 32 bits: counter, low 32 bits: waiter count
    sema   uint32
}

// Add(delta):
//   Atomically add delta to counter (high 32 bits)
//   If counter goes to 0 AND there are waiters: release all via semaphore

// Done() == Add(-1)

// Wait():
//   If counter == 0: return immediately
//   Else: increment waiter count, park via semaphore

// RULES:
// 1. Add() before launching goroutine (not inside goroutine)
// 2. Never copy WaitGroup after first use
// 3. Add(-N) all at once OR Add(1) before each go stmt
```

### sync.Once — Memory-Safe Singleton

```go
type Once struct {
    done atomic.Uint32  // 0 = not done, 1 = done
    m    Mutex
}

func (o *Once) Do(f func()) {
    // Fast path: atomic load (no lock)
    if o.done.Load() == 0 {
        o.doSlow(f)
    }
}

func (o *Once) doSlow(f func()) {
    o.m.Lock()
    defer o.m.Unlock()
    if o.done.Load() == 0 {
        defer o.done.Store(1) // store AFTER f() returns
        f()
    }
}
// done.Store(1) is deferred: if f() panics, done stays 0
// Next call will try again (different behavior than sync.Once in some languages)
// Actually no — in Go 1.14+: if f panics, Once stays "not done"
// In Go: sync.Once considers f "done" only on normal return
```

### sync.Map — Concurrent Map

```go
// sync.Map is NOT a general-purpose concurrent map.
// Optimized for two specific patterns:
//   1. Write once, read many times (cache-like)
//   2. Keys are mostly disjoint per goroutine

// Internal structure:
type Map struct {
    mu Mutex
    read atomic.Pointer[readOnly]  // read-only copy, accessed lock-free
    dirty map[any]*entry           // mutable copy, requires lock
    misses int                     // count of read misses
}

// Read path (hot): atomic load of read map — no lock
// Write path (cold): acquire lock, update dirty map
// After enough misses: promote dirty → read map (amortized)

// When to use:
//   ✓ Mostly reads, occasional writes to different keys
//   ✓ Each goroutine has its own subset of keys (shard-like)
//   ✗ General concurrent map → use map+RWMutex or sharded maps
//   ✗ High write contention

// Example:
var m sync.Map

m.Store("key", 42)
v, ok := m.Load("key")      // lock-free on hot path
m.LoadOrStore("key", 99)    // atomic load-or-store
m.Delete("key")
m.Range(func(k, v any) bool { // iterate — locks during promotion
    fmt.Println(k, v)
    return true // return false to stop
})
```

### atomic Package — Complete Reference

```go
// file: atomic_patterns.go
package main

import (
    "fmt"
    "sync/atomic"
    "time"
    "unsafe"
)

// ── Basic atomics ────────────────────────────────────────────────────
func basicAtomics() {
    var i atomic.Int64
    i.Store(42)
    fmt.Println(i.Load())        // 42
    fmt.Println(i.Add(10))       // 52 (returns new value)
    fmt.Println(i.Swap(100))     // 52 (returns old value)
    
    // Compare-And-Swap: fundamental building block
    ok := i.CompareAndSwap(100, 200) // if current==100, set to 200
    fmt.Println(ok, i.Load())    // true, 200
}

// ── Lock-free counter ────────────────────────────────────────────────
type Counter struct {
    val atomic.Int64
}

func (c *Counter) Inc()        { c.val.Add(1) }
func (c *Counter) Dec()        { c.val.Add(-1) }
func (c *Counter) Get() int64  { return c.val.Load() }

// ── Lock-free stack (Treiber stack) ──────────────────────────────────
type node[T any] struct {
    val  T
    next *node[T]
}

type LockFreeStack[T any] struct {
    head atomic.Pointer[node[T]]
}

func (s *LockFreeStack[T]) Push(val T) {
    n := &node[T]{val: val}
    for {
        n.next = s.head.Load()
        if s.head.CompareAndSwap(n.next, n) {
            return
        }
        // CAS failed: another goroutine modified head → retry
    }
}

func (s *LockFreeStack[T]) Pop() (T, bool) {
    for {
        h := s.head.Load()
        if h == nil {
            var zero T
            return zero, false
        }
        if s.head.CompareAndSwap(h, h.next) {
            return h.val, true
        }
    }
}

// ── atomic.Pointer — type-safe pointer atomics (Go 1.19+) ────────────
type Config struct {
    Timeout time.Duration
    MaxConn int
}

type Service struct {
    cfg atomic.Pointer[Config]
}

func (s *Service) UpdateConfig(c *Config) {
    s.cfg.Store(c) // atomic pointer swap — no lock needed
}

func (s *Service) GetConfig() *Config {
    return s.cfg.Load() // consistent snapshot
}

// ── atomic.Value — any type, but must be same type always ────────────
var globalConfig atomic.Value

func updateConfig(c *Config) {
    globalConfig.Store(c) // all callers get consistent view
}

func readConfig() *Config {
    return globalConfig.Load().(*Config)
}

// ── Memory ordering: why atomics prevent races ────────────────────────
// atomic.Store has RELEASE semantics:
//   All writes BEFORE Store are visible to anyone who sees the stored value
// atomic.Load has ACQUIRE semantics:
//   All writes visible at the time of Store are visible after Load
// Together: forms a happens-before edge

// unsafe atomic operations (when you need raw pointer manipulation):
func unsafeAtomicLoad(p *int32) int32 {
    return atomic.LoadInt32((*int32)(unsafe.Pointer(p)))
}

func main() {
    basicAtomics()
    
    var stack LockFreeStack[int]
    stack.Push(1)
    stack.Push(2)
    stack.Push(3)
    
    for {
        v, ok := stack.Pop()
        if !ok { break }
        fmt.Println(v) // 3, 2, 1
    }
}
```

### sync.Cond — Condition Variable

```go
// sync.Cond: goroutines wait for a condition to become true
// Rarely needed in modern Go (channels usually better)
// USE CASE: multiple goroutines waiting for one signal with complex state

type WorkQueue struct {
    mu    sync.Mutex
    cond  *sync.Cond
    items []int
}

func NewWorkQueue() *WorkQueue {
    q := &WorkQueue{}
    q.cond = sync.NewCond(&q.mu)
    return q
}

func (q *WorkQueue) Enqueue(item int) {
    q.mu.Lock()
    q.items = append(q.items, item)
    q.mu.Unlock()
    q.cond.Signal()    // wake ONE waiting goroutine
    // q.cond.Broadcast() // wake ALL waiting goroutines
}

func (q *WorkQueue) Dequeue() int {
    q.mu.Lock()
    defer q.mu.Unlock()
    
    // MUST use for loop — not if! (spurious wakeups)
    for len(q.items) == 0 {
        q.cond.Wait() // atomically: release lock + park goroutine
        // When woken: reacquire lock, recheck condition
    }
    
    item := q.items[0]
    q.items = q.items[1:]
    return item
}
```

---

## 10. Context Package — Internals & Patterns

### Mental Model
Context is an **immutable, tree-structured chain** that propagates cancellation, deadlines, and request-scoped values across API boundaries and goroutine calls.

### Context Tree Structure

```
context.Background()          ← root (never cancelled)
         │
         ├── WithCancel()     ← returns CancelFunc, child cancelled when called
         │         │
         │         ├── WithTimeout(5s)   ← auto-cancelled after 5s
         │         │
         │         └── WithValue("userID", 123)
         │
         └── WithDeadline(time.Now().Add(30s))
                   │
                   └── WithCancel()  ← cancelled by parent OR when parent deadline expires
```

### Context Interface

```go
type Context interface {
    Deadline() (deadline time.Time, ok bool) // zero if no deadline
    Done() <-chan struct{}                    // closed when cancelled/timed out
    Err() error                              // nil, Canceled, or DeadlineExceeded
    Value(key any) any                       // returns value for key
}
```

### cancelCtx — The Core Implementation

```go
// context/context.go
type cancelCtx struct {
    Context                    // parent context
    mu       sync.Mutex
    done     atomic.Value      // chan struct{}, created lazily
    children map[canceler]struct{} // child contexts to cancel
    err      error             // set on cancellation
    cause    error             // Go 1.20+: cause of cancellation
}

// cancel() — called by CancelFunc:
// 1. Acquire mu
// 2. If already cancelled: return
// 3. Set err = Canceled (or DeadlineExceeded for timer)
// 4. Close done channel (broadcasts to all receivers)
// 5. Cancel all children recursively
// 6. Remove self from parent's children map
// 7. Release mu

// Propagation is DOWNWARD only:
// Cancelling parent → cancels all children
// Cancelling child → does NOT affect parent
```

### Production Patterns

```go
// file: context_patterns.go
package main

import (
    "context"
    "errors"
    "fmt"
    "net/http"
    "time"
)

// ── Pattern 1: HTTP handler with context propagation ──────────────────
func handler(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context() // already has cancellation from HTTP server
    
    result, err := fetchData(ctx, "https://api.example.com/data")
    if err != nil {
        if errors.Is(err, context.Canceled) {
            // Client disconnected
            return
        }
        http.Error(w, err.Error(), 500)
        return
    }
    fmt.Fprintln(w, result)
}

func fetchData(ctx context.Context, url string) (string, error) {
    req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
    // If ctx is cancelled, req.Do() returns immediately
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return "", fmt.Errorf("fetchData: %w", err)
    }
    defer resp.Body.Close()
    return "data", nil
}

// ── Pattern 2: Timeout wrapping ───────────────────────────────────────
func withTimeout(parent context.Context, d time.Duration, fn func(context.Context) error) error {
    ctx, cancel := context.WithTimeout(parent, d)
    defer cancel() // ALWAYS defer cancel — prevent leak even if deadline fires
    return fn(ctx)
}

// ── Pattern 3: Context-aware goroutine pool ───────────────────────────
func fanOut(ctx context.Context, tasks []string) []string {
    results := make([]string, len(tasks))
    errCh := make(chan error, len(tasks))
    
    for i, task := range tasks {
        i, task := i, task // capture loop vars
        go func() {
            select {
            case <-ctx.Done():
                errCh <- ctx.Err()
                return
            default:
            }
            
            // Do work
            results[i] = "result:" + task
            errCh <- nil
        }()
    }
    
    for range tasks {
        if err := <-errCh; err != nil {
            // context cancelled — remaining goroutines will self-stop
            return nil
        }
    }
    return results
}

// ── Pattern 4: Context values — typed keys ────────────────────────────
// NEVER use primitive types as context keys (collision risk)
type contextKey struct{ name string }

var (
    requestIDKey = contextKey{"requestID"}
    userIDKey    = contextKey{"userID"}
)

func WithRequestID(ctx context.Context, id string) context.Context {
    return context.WithValue(ctx, requestIDKey, id)
}

func RequestIDFrom(ctx context.Context) (string, bool) {
    id, ok := ctx.Value(requestIDKey).(string)
    return id, ok
}

// ── Pattern 5: Propagate cancellation via channel ─────────────────────
func worker(ctx context.Context, jobs <-chan int) <-chan int {
    results := make(chan int)
    go func() {
        defer close(results)
        for {
            select {
            case <-ctx.Done():
                fmt.Println("worker: context cancelled:", ctx.Err())
                return
            case job, ok := <-jobs:
                if !ok {
                    return
                }
                select {
                case results <- job * 2:
                case <-ctx.Done():
                    return
                }
            }
        }
    }()
    return results
}

// ── Pattern 6: context.WithCause (Go 1.20+) ──────────────────────────
func withCause() {
    ctx, cancel := context.WithCancelCause(context.Background())
    
    go func() {
        cancel(fmt.Errorf("database connection lost")) // custom cause
    }()
    
    <-ctx.Done()
    fmt.Println("cancelled:", context.Cause(ctx)) // custom error
}

// ── ANTI-PATTERNS ────────────────────────────────────────────────────

// WRONG: storing context in struct (contexts should flow through call chains)
type BadService struct {
    ctx context.Context // WRONG
}

// CORRECT: pass context as first parameter
type GoodService struct{}
func (s *GoodService) DoWork(ctx context.Context) error { return nil }

// WRONG: passing nil context
func badCall() {
    fetchData(nil, "url") // panic if fetchData uses ctx
}

// CORRECT: use context.TODO() or context.Background()
func goodCall() {
    fetchData(context.Background(), "url")
}

func main() {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    jobs := make(chan int, 10)
    results := worker(ctx, jobs)
    
    for i := 0; i < 5; i++ {
        jobs <- i
    }
    close(jobs)
    
    for r := range results {
        fmt.Println(r)
    }
}
```

---

## 11. Error Handling — Patterns, Wrapping, Sentinel, Custom

### The Error Interface

```go
type error interface {
    Error() string
}
// Smallest interface in the stdlib — just one method
```

### Error Wrapping (Go 1.13+)

```go
// file: error_patterns.go
package main

import (
    "errors"
    "fmt"
    "net"
    "os"
)

// ── Wrapping with %w ──────────────────────────────────────────────────
func readConfig(path string) error {
    _, err := os.ReadFile(path)
    if err != nil {
        return fmt.Errorf("readConfig(%q): %w", path, err)
        //                                    ↑ %w wraps for errors.Is/As
    }
    return nil
}

// ── errors.Is — sentinel value check (traverses chain) ────────────────
func checkSentinel() {
    err := readConfig("/nonexistent")
    
    // Traverses chain: readConfig error → *os.PathError → os.ErrNotExist
    if errors.Is(err, os.ErrNotExist) {
        fmt.Println("file not found")
    }
    
    // errors.Is uses == for sentinel values
    // AND calls Unwrap() to traverse the chain
}

// ── errors.As — type check (traverses chain) ─────────────────────────
func checkType() {
    err := readConfig("/nonexistent")
    
    var pathErr *os.PathError
    if errors.As(err, &pathErr) {
        fmt.Println("op:", pathErr.Op)       // "open"
        fmt.Println("path:", pathErr.Path)   // "/nonexistent"
    }
}

// ── Custom error types ────────────────────────────────────────────────
type ValidationError struct {
    Field   string
    Message string
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("validation error on %s: %s", e.Field, e.Message)
}

// Multiple wrapped errors (Go 1.20+: errors.Join)
func validate(name string, age int) error {
    var errs []error
    if name == "" {
        errs = append(errs, &ValidationError{Field: "name", Message: "required"})
    }
    if age < 0 || age > 150 {
        errs = append(errs, &ValidationError{Field: "age", Message: "out of range"})
    }
    return errors.Join(errs...) // nil if slice is empty
}

// ── Sentinel errors ───────────────────────────────────────────────────
// Package-level, immutable, comparable with ==
var (
    ErrNotFound   = errors.New("not found")
    ErrPermission = errors.New("permission denied")
    ErrConflict   = errors.New("conflict")
)

// Wrapping sentinel:
func getUser(id int) error {
    // ...
    return fmt.Errorf("getUser(%d): %w", id, ErrNotFound)
}

// Checking: errors.Is(err, ErrNotFound) // true even through wrapping

// ── Error groups (Go 1.21+: errgroup with context) ────────────────────
import "golang.org/x/sync/errgroup"

func parallelWork(ctx context.Context) error {
    g, ctx := errgroup.WithContext(ctx)
    
    g.Go(func() error {
        return doTask1(ctx)
    })
    g.Go(func() error {
        return doTask2(ctx)
    })
    
    // Waits for all; if any returns error, ctx is cancelled for others
    return g.Wait()
}

// ── Production error pattern ──────────────────────────────────────────
// Structured error with code, message, details
type AppError struct {
    Code    int
    Op      string // operation that failed
    Kind    Kind   // category of error
    Err     error  // wrapped original error
}

type Kind int
const (
    KindOther      Kind = iota
    KindNotFound
    KindPermission
    KindConflict
    KindValidation
    KindInternal
)

func (e *AppError) Error() string {
    if e.Err != nil {
        return fmt.Sprintf("[%s] %v", e.Op, e.Err)
    }
    return fmt.Sprintf("[%s] error code %d", e.Op, e.Code)
}

func (e *AppError) Unwrap() error { return e.Err }

func E(op string, args ...interface{}) error {
    ae := &AppError{Op: op}
    for _, arg := range args {
        switch a := arg.(type) {
        case Kind:    ae.Kind = a
        case error:   ae.Err = a
        case string:  ae.Err = errors.New(a)
        case int:     ae.Code = a
        }
    }
    return ae
}

// Usage:
func findUser(id int) (*User, error) {
    // ...
    return nil, E("findUser", KindNotFound, fmt.Errorf("id=%d", id))
}

// ── Never discard errors ───────────────────────────────────────────────
// WRONG:
// f, _ := os.Open(path)

// CORRECT or at minimum log:
func openFile(path string) (*os.File, error) {
    f, err := os.Open(path)
    if err != nil {
        return nil, fmt.Errorf("openFile: %w", err)
    }
    return f, nil
}
```

### Network Error Handling

```go
func handleNetworkError(err error) {
    var netErr *net.OpError
    if errors.As(err, &netErr) {
        if netErr.Timeout() {
            fmt.Println("timeout — retry with backoff")
            return
        }
        if netErr.Temporary() {
            fmt.Println("temporary error — retry")
            return
        }
    }
    fmt.Println("permanent error:", err)
}
```

---

## 12. Reflection & the reflect Package

### One-Line Explanation
Reflection lets you inspect and manipulate types and values at runtime, but at significant cost — use it only when compile-time generics cannot solve the problem.

### Core Types

```go
// Two fundamental types:
reflect.Type  — describes the type  (interface)
reflect.Value — holds and manipulates values

// Entry points:
t := reflect.TypeOf(x)   // needs an interface value — may escape to heap
v := reflect.ValueOf(x)  // same

// From Type to Value and back:
zero := reflect.Zero(t)   // zero value of type t
x2 := v.Interface()       // get interface{} from Value
concrete := x2.(MyType)   // type assert
```

### Deep Dive

```go
// file: reflection.go
package main

import (
    "fmt"
    "reflect"
    "strings"
)

type Person struct {
    Name    string `json:"name" validate:"required"`
    Age     int    `json:"age"  validate:"min=0,max=150"`
    private string // unexported
}

func (p Person) Greet() string { return "Hello, " + p.Name }

// ── Type inspection ───────────────────────────────────────────────────
func inspectType(x interface{}) {
    t := reflect.TypeOf(x)
    
    fmt.Println("Type:", t)
    fmt.Println("Kind:", t.Kind()) // struct, ptr, slice, map, func, chan, ...
    
    if t.Kind() == reflect.Ptr {
        t = t.Elem() // dereference pointer
    }
    
    if t.Kind() == reflect.Struct {
        for i := 0; i < t.NumField(); i++ {
            f := t.Field(i)
            fmt.Printf("  Field: %s (%s) tags: %s\n", 
                f.Name, f.Type, f.Tag)
            
            // Parse struct tags
            jsonTag := f.Tag.Get("json")
            validateTag := f.Tag.Get("validate")
            fmt.Printf("    json=%q validate=%q\n", jsonTag, validateTag)
        }
        
        for i := 0; i < t.NumMethod(); i++ {
            m := t.Method(i)
            fmt.Printf("  Method: %s %s\n", m.Name, m.Type)
        }
    }
}

// ── Value inspection and mutation ─────────────────────────────────────
func mutate(x interface{}) {
    v := reflect.ValueOf(x)
    
    // Must pass pointer to mutate
    if v.Kind() != reflect.Ptr || v.Elem().Kind() != reflect.Struct {
        panic("need pointer to struct")
    }
    
    v = v.Elem() // dereference
    
    nameField := v.FieldByName("Name")
    if nameField.IsValid() && nameField.CanSet() {
        nameField.SetString("Modified")
    }
}

// ── Build a simple validator using reflection ─────────────────────────
type Rule struct {
    Min, Max int
    Required bool
}

func validateStruct(s interface{}) []string {
    v := reflect.ValueOf(s)
    t := reflect.TypeOf(s)
    
    if v.Kind() == reflect.Ptr {
        v = v.Elem()
        t = t.Elem()
    }
    
    var errs []string
    
    for i := 0; i < t.NumField(); i++ {
        field := t.Field(i)
        value := v.Field(i)
        
        if !field.IsExported() {
            continue
        }
        
        tag := field.Tag.Get("validate")
        if tag == "" {
            continue
        }
        
        for _, rule := range strings.Split(tag, ",") {
            if rule == "required" && value.IsZero() {
                errs = append(errs, fmt.Sprintf("%s is required", field.Name))
            }
        }
    }
    return errs
}

// ── Dynamic function calling ───────────────────────────────────────────
func callMethod(obj interface{}, method string, args ...interface{}) []reflect.Value {
    v := reflect.ValueOf(obj)
    m := v.MethodByName(method)
    if !m.IsValid() {
        panic("method not found: " + method)
    }
    
    in := make([]reflect.Value, len(args))
    for i, arg := range args {
        in[i] = reflect.ValueOf(arg)
    }
    
    return m.Call(in)
}

// ── reflect.DeepEqual — structural equality ───────────────────────────
// Used in testing and frameworks
// Handles cycles, unexported fields (partially), nil vs empty slice
// WARNING: reflect.DeepEqual([]int{}, []int(nil)) == false!

// ── Building a generic deep copy ──────────────────────────────────────
func deepCopy(src interface{}) interface{} {
    t := reflect.TypeOf(src)
    v := reflect.ValueOf(src)
    
    if t.Kind() == reflect.Ptr {
        // Allocate new value of same type
        newV := reflect.New(t.Elem())
        newV.Elem().Set(v.Elem()) // shallow copy of fields
        return newV.Interface()
    }
    
    // Value types: just return copy
    return v.Interface()
}

func main() {
    p := Person{Name: "Alice", Age: 30}
    
    inspectType(p)
    
    errs := validateStruct(&Person{Name: "", Age: -1})
    fmt.Println("Validation errors:", errs)
    
    result := callMethod(p, "Greet")
    fmt.Println(result[0].String())
    
    mutate(&p)
    fmt.Println("After mutation:", p.Name)
}
```

### When NOT to Use Reflection

```
Prefer:                 Over:
Generics                reflect for type-parametric code
Interface methods       reflect.Value.MethodByName()
Code generation         reflect in hot paths
json.Marshal (stdlib)   manual reflect for serialization

Costs:
  - 10-100x slower than direct code
  - No compile-time type safety
  - Panics instead of compile errors
  - Prevents inlining and optimization
  - Increases escape to heap
```

---

## 13. unsafe Package — Memory Layout & Tricks

### One-Line Explanation
`unsafe` bypasses Go's type system to perform pointer arithmetic, read memory layout, and do zero-copy conversions — powerful but dangerous.

### unsafe.Pointer Rules

```
Only safe conversions:
  1. *T1 → unsafe.Pointer → *T2  (reinterpret cast)
  2. unsafe.Pointer → uintptr (get numeric address)
  3. uintptr → unsafe.Pointer ONLY within same expression (not stored!)
     BECAUSE: GC may move objects, making stored uintptr stale

These CANNOT be split across lines:
  // WRONG:
  p := unsafe.Pointer(&x)
  addr := uintptr(p)
  // ... GC runs here, x moved ...
  // addr is now stale — use would corrupt memory
  
  // CORRECT (single expression):
  p2 := (*int)(unsafe.Pointer(uintptr(unsafe.Pointer(&x)) + 8))
```

```go
// file: unsafe_patterns.go
package main

import (
    "fmt"
    "reflect"
    "unsafe"
)

// ── Struct field access via offset ────────────────────────────────────
type Header struct {
    Version uint8
    Flags   uint8
    Length  uint16
    ID      uint32
}

func readFieldUnsafe() {
    h := Header{Version: 1, Flags: 0xFF, Length: 100, ID: 42}
    
    // Get address of specific field using offsetof
    idOffset := unsafe.Offsetof(h.ID)
    idPtr := (*uint32)(unsafe.Pointer(uintptr(unsafe.Pointer(&h)) + idOffset))
    fmt.Println("ID:", *idPtr) // 42
    
    // Sizes
    fmt.Println("Sizeof Header:", unsafe.Sizeof(h))   // 8 bytes
    fmt.Println("Alignof ID:", unsafe.Alignof(h.ID))  // 4 bytes
}

// ── Zero-copy string ↔ []byte conversion ──────────────────────────────
// WARNING: Only safe if []byte is NOT modified after conversion
func stringToBytes(s string) []byte {
    // string header: {ptr *byte, len int}
    // []byte header: {ptr *byte, len int, cap int}
    
    sh := (*reflect.StringHeader)(unsafe.Pointer(&s))
    bh := reflect.SliceHeader{
        Data: sh.Data,
        Len:  sh.Len,
        Cap:  sh.Len,
    }
    return *(*[]byte)(unsafe.Pointer(&bh))
}

// Go 1.20+ preferred way:
func stringToBytes120(s string) []byte {
    return unsafe.Slice(unsafe.StringData(s), len(s))
}

func bytesToString(b []byte) string {
    return unsafe.String(unsafe.SliceData(b), len(b))
}

// ── Struct padding inspection ─────────────────────────────────────────
type Padded struct {
    A bool    // 1 byte
    // 7 bytes padding
    B float64 // 8 bytes (alignment: 8)
    C bool    // 1 byte
    // 7 bytes padding
}  // Total: 24 bytes!

type Packed struct {
    B float64 // 8 bytes first
    A bool    // 1 byte
    C bool    // 1 byte
    // 6 bytes padding
}  // Total: 16 bytes

func showPadding() {
    fmt.Println("Padded size:", unsafe.Sizeof(Padded{}))  // 24
    fmt.Println("Packed size:", unsafe.Sizeof(Packed{}))  // 16
}

// ── Reading C structs / network packets ──────────────────────────────
// When you receive a byte slice that matches a struct layout:
type Packet struct {
    Magic   [4]byte
    Version uint16
    Size    uint32
}  // MUST match wire format exactly

func parsePacket(data []byte) *Packet {
    if len(data) < int(unsafe.Sizeof(Packet{})) {
        return nil
    }
    return (*Packet)(unsafe.Pointer(&data[0]))
    // Zero copy — reads directly from slice backing array
    // WARNING: endianness — use encoding/binary for portable code
}

// ── Noescape hack — prevent unnecessary heap escape ───────────────────
//go:nosplit
func noescape(p unsafe.Pointer) unsafe.Pointer {
    x := uintptr(p)
    return unsafe.Pointer(x ^ 0)
}
// Used in stdlib for performance-critical paths
// Tells compiler "this pointer does not escape"
// USE VERY CAREFULLY — incorrect use causes memory corruption

func main() {
    readFieldUnsafe()
    showPadding()
    
    s := "hello world"
    b := stringToBytes(s)
    fmt.Println(b[:5]) // [104 101 108 108 111]
    
    // DO NOT modify b — s is immutable!
    // b[0] = 'H' // would corrupt string table — undefined behavior
    
    back := bytesToString(b)
    fmt.Println(back)
}
```

---

## 14. Memory Alignment, Struct Padding, Data Races

### CPU Alignment Requirements

```
Every type has an alignment requirement:
  bool, byte: 1-byte aligned
  int16, uint16: 2-byte aligned
  int32, uint32, float32: 4-byte aligned
  int64, uint64, float64, pointer: 8-byte aligned (on 64-bit)

Struct alignment = max alignment of any field
The compiler inserts padding to satisfy alignment:

type Example struct {
  A byte    // offset 0, size 1
  // 1 byte padding (B needs 2-byte alignment)
  B int16   // offset 2, size 2
  // 0 padding (C needs 4-byte alignment, offset 4 ✓)
  C int32   // offset 4, size 4
  D byte    // offset 8, size 1
  // 7 bytes padding (struct must be multiple of largest alignment=8)
}
// Total: 16 bytes (not 8!)
```

### Optimal Struct Layout

```
Rule: Order fields largest to smallest to minimize padding.

BEFORE (wasted memory):
type Bad struct {
  A bool    // 1
  // 7 pad
  B int64   // 8
  C bool    // 1
  // 7 pad
  D int64   // 8
}  // = 32 bytes

AFTER:
type Good struct {
  B int64   // 8
  D int64   // 8
  A bool    // 1
  C bool    // 1
  // 6 pad
}  // = 24 bytes

Tools:
  go vet -structtag  (basic)
  betteralign linter (https://github.com/dkorunic/betteralign)
  fieldalignment (golang.org/x/tools/go/analysis/passes/fieldalignment)
```

### False Sharing — Cache Line Problem

```
CPU cache line = 64 bytes (x86, ARM)
If two goroutines write to different fields in same cache line:
  → CACHE LINE BOUNCING: CPUs invalidate each other's caches
  → 10-100x slowdown despite no logical data sharing

Example:
type BadCounter struct {
  CountA int64  // offset 0-7  ─┐ same 64-byte cache line!
  CountB int64  // offset 8-15 ─┘
}

type GoodCounter struct {
  CountA int64
  _      [56]byte  // padding to push B to next cache line
  CountB int64
}
```

```go
// file: false_sharing.go
package main

import (
    "fmt"
    "sync"
    "testing"
)

// Demonstrates cache line effect
type PaddedInt struct {
    val int64
    _   [56]byte // cache line padding
}

func BenchmarkWithFalseSharing(b *testing.B) {
    type Counters struct{ a, c int64 }
    var c Counters
    var wg sync.WaitGroup
    
    b.ResetTimer()
    wg.Add(2)
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ { c.a++ }
    }()
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ { c.c++ }
    }()
    wg.Wait()
}

func BenchmarkWithoutFalseSharing(b *testing.B) {
    type Counters struct {
        a int64
        _ [56]byte
        c int64
    }
    var c Counters
    var wg sync.WaitGroup
    
    b.ResetTimer()
    wg.Add(2)
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ { c.a++ }
    }()
    go func() {
        defer wg.Done()
        for i := 0; i < b.N; i++ { c.c++ }
    }()
    wg.Wait()
}

func main() {
    fmt.Println("Run: go test -bench=. -cpu=2 false_sharing.go")
    // WithFalseSharing typically 3-10x slower than WithoutFalseSharing
}
```

### 64-bit atomic on 32-bit systems

```go
// TRAP: int64/uint64 in struct must be 64-bit aligned for atomic ops
// On 32-bit platforms, struct fields may be 32-bit aligned

type Bad32 struct {
    flag int32
    val  int64  // may be at offset 4 → 32-bit aligned → atomic ops UB!
}

// FIX: put 64-bit fields first
type Good32 struct {
    val  int64  // offset 0 → always 64-bit aligned
    flag int32
}

// Or: use sync/atomic consistently and keep int64 at offset%8==0
```

---

## 15. Profiling, Benchmarking & Performance Tuning

### pprof — The Complete Workflow

```go
// file: profiling_server.go
package main

import (
    "net/http"
    _ "net/http/pprof"  // registers /debug/pprof/* handlers
    "log"
    "runtime"
    "os"
    "runtime/pprof"
    "runtime/trace"
)

// ── Option A: HTTP server (for long-running services) ─────────────────
func startProfilingServer() {
    go func() {
        // Access via: go tool pprof http://localhost:6060/debug/pprof/heap
        log.Println(http.ListenAndServe(":6060", nil))
    }()
}

// ── Option B: File-based profiling (for CLI tools / benchmarks) ───────
func profileCPU(filename string) func() {
    f, err := os.Create(filename)
    if err != nil { panic(err) }
    
    if err := pprof.StartCPUProfile(f); err != nil { panic(err) }
    
    return func() {
        pprof.StopCPUProfile()
        f.Close()
    }
}

func profileHeap(filename string) {
    runtime.GC() // get accurate heap profile
    f, _ := os.Create(filename)
    defer f.Close()
    pprof.WriteHeapProfile(f)
}

func profileTrace(filename string) func() {
    f, _ := os.Create(filename)
    trace.Start(f)
    return func() {
        trace.Stop()
        f.Close()
    }
}

// ── Custom profiling labels ───────────────────────────────────────────
import "runtime/pprof"

func labeledWork(ctx context.Context) {
    // Labels appear in pprof output — invaluable for attributing time
    pprof.Do(ctx, pprof.Labels("service", "payment", "op", "charge"), func(ctx context.Context) {
        doPaymentWork()
    })
}

func main() {
    stopCPU := profileCPU("cpu.prof")
    defer stopCPU()
    
    stopTrace := profileTrace("trace.out")
    defer stopTrace()
    
    // ... do work ...
    
    profileHeap("heap.prof")
}
```

```bash
# ── CPU profiling workflow ────────────────────────────────────────────
go test -bench=. -cpuprofile=cpu.prof -benchtime=10s
go tool pprof cpu.prof

# Inside pprof:
# (pprof) top10         — top 10 functions by CPU time
# (pprof) top10 -cum    — cumulative (includes callees)
# (pprof) list FuncName — annotated source
# (pprof) web           — interactive flame graph in browser
# (pprof) svg > out.svg — static flame graph

# ── Heap profiling ────────────────────────────────────────────────────
go test -bench=. -memprofile=heap.prof -benchmem
go tool pprof -alloc_space heap.prof   # total allocations
go tool pprof -inuse_space heap.prof   # live heap

# ── Goroutine profiling ───────────────────────────────────────────────
curl http://localhost:6060/debug/pprof/goroutine?debug=2 > goroutines.txt
# Shows all goroutines with full stack traces — diagnose leaks

# ── Mutex profiling (Go 1.8+) ─────────────────────────────────────────
runtime.SetMutexProfileFraction(1) // sample every mutex event
go tool pprof http://localhost:6060/debug/pprof/mutex

# ── Block profiling ───────────────────────────────────────────────────
runtime.SetBlockProfileRate(1)
go tool pprof http://localhost:6060/debug/pprof/block

# ── Execution tracer ─────────────────────────────────────────────────
go test -bench=. -trace=trace.out
go tool trace trace.out
# Shows: goroutine scheduling, GC, network I/O, syscalls, per-P execution
```

### Benchmark Writing

```go
// file: bench_test.go
package perf

import (
    "strings"
    "testing"
)

// ── Basic benchmark ───────────────────────────────────────────────────
func BenchmarkStringConcat(b *testing.B) {
    parts := []string{"hello", " ", "world", " ", "from", " ", "Go"}
    
    b.ResetTimer() // don't count setup time
    for i := 0; i < b.N; i++ {
        _ = strings.Join(parts, "")
    }
}

// ── Table-driven benchmarks ───────────────────────────────────────────
func BenchmarkStringMethods(b *testing.B) {
    parts := []string{"hello", " ", "world"}
    
    b.Run("strings.Join", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            _ = strings.Join(parts, "")
        }
    })
    
    b.Run("strings.Builder", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            var sb strings.Builder
            for _, p := range parts {
                sb.WriteString(p)
            }
            _ = sb.String()
        }
    })
    
    b.Run("concatenation", func(b *testing.B) {
        for i := 0; i < b.N; i++ {
            s := ""
            for _, p := range parts {
                s += p
            }
            _ = s
        }
    })
}

// ── Parallel benchmark ────────────────────────────────────────────────
func BenchmarkConcurrentMap(b *testing.B) {
    m := make(map[string]int)
    var mu sync.Mutex
    
    b.RunParallel(func(pb *testing.PB) {
        for pb.Next() {
            mu.Lock()
            m["key"]++
            mu.Unlock()
        }
    })
}

// ── Alloc counting ────────────────────────────────────────────────────
func BenchmarkAllocations(b *testing.B) {
    b.ReportAllocs()
    for i := 0; i < b.N; i++ {
        _ = fmt.Sprintf("hello %d", i) // will show allocs/op
    }
}

// ── Benchmark with setup per iteration ───────────────────────────────
func BenchmarkWithSetup(b *testing.B) {
    for i := 0; i < b.N; i++ {
        b.StopTimer()  // pause timing
        data := generateTestData(1000)
        b.StartTimer() // resume timing
        
        process(data)
    }
}
```

```bash
# Run specific benchmark
go test -bench=BenchmarkStringMethods -benchmem -count=5

# Compare before/after: benchstat
go test -bench=. -count=10 > old.txt
# make changes
go test -bench=. -count=10 > new.txt
benchstat old.txt new.txt
# Output shows p-value and % change

# CPU-pinned benchmark (more stable numbers)
taskset -c 0 go test -bench=. -cpu=1
```

### Performance Anti-Patterns

```
1. fmt.Sprintf in hot path → allocates, use strconv
2. map[string]T when string is never mutated → consider []struct{key,val}
3. append in inner loop without pre-allocate → repeated copying
4. sync.Mutex where atomic suffices → unnecessary OS involvement  
5. interface{} parameters → boxing, prevents inlining
6. defer in tight loop → small but measurable overhead
7. String concatenation with + → O(n²) allocations
8. bytes.Equal vs == on strings → bytes.Equal doesn't alloc
9. net.LookupHost in hot path → no caching, DNS per call
10. time.Now() in hot path → syscall, cache if sub-ms precision OK
```

---

## 16. Concurrency Patterns — Production Patterns

### Worker Pool

```go
// file: worker_pool.go
package main

import (
    "context"
    "fmt"
    "sync"
)

type Job struct {
    ID      int
    Payload string
}

type Result struct {
    JobID  int
    Output string
    Err    error
}

type WorkerPool struct {
    workers int
    jobs    chan Job
    results chan Result
    wg      sync.WaitGroup
}

func NewWorkerPool(workers, bufSize int) *WorkerPool {
    return &WorkerPool{
        workers: workers,
        jobs:    make(chan Job, bufSize),
        results: make(chan Result, bufSize),
    }
}

func (p *WorkerPool) Start(ctx context.Context, process func(Job) Result) {
    for i := 0; i < p.workers; i++ {
        p.wg.Add(1)
        go func(workerID int) {
            defer p.wg.Done()
            for {
                select {
                case <-ctx.Done():
                    return
                case job, ok := <-p.jobs:
                    if !ok {
                        return
                    }
                    result := process(job)
                    select {
                    case p.results <- result:
                    case <-ctx.Done():
                        return
                    }
                }
            }
        }(i)
    }
    
    // Close results when all workers done
    go func() {
        p.wg.Wait()
        close(p.results)
    }()
}

func (p *WorkerPool) Submit(job Job) {
    p.jobs <- job
}

func (p *WorkerPool) Close() {
    close(p.jobs)
}

func (p *WorkerPool) Results() <-chan Result {
    return p.results
}

func main() {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    pool := NewWorkerPool(5, 100)
    
    pool.Start(ctx, func(j Job) Result {
        return Result{
            JobID:  j.ID,
            Output: fmt.Sprintf("processed: %s", j.Payload),
        }
    })
    
    // Submit jobs
    go func() {
        for i := 0; i < 20; i++ {
            pool.Submit(Job{ID: i, Payload: fmt.Sprintf("job-%d", i)})
        }
        pool.Close()
    }()
    
    // Collect results
    for result := range pool.Results() {
        if result.Err != nil {
            fmt.Printf("Job %d failed: %v\n", result.JobID, result.Err)
            continue
        }
        fmt.Printf("Job %d: %s\n", result.JobID, result.Output)
    }
}
```

### Rate Limiter — Token Bucket

```go
// file: rate_limiter.go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Token bucket rate limiter
type RateLimiter struct {
    tokens   float64
    maxTokens float64
    rate     float64 // tokens per second
    lastTime time.Time
    mu       sync.Mutex
}

func NewRateLimiter(ratePerSec, burst float64) *RateLimiter {
    return &RateLimiter{
        tokens:    burst,
        maxTokens: burst,
        rate:      ratePerSec,
        lastTime:  time.Now(),
    }
}

func (r *RateLimiter) Allow() bool {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    now := time.Now()
    elapsed := now.Sub(r.lastTime).Seconds()
    r.lastTime = now
    
    r.tokens += elapsed * r.rate
    if r.tokens > r.maxTokens {
        r.tokens = r.maxTokens
    }
    
    if r.tokens >= 1 {
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
        case <-time.After(time.Millisecond):
        }
    }
}

// Or use golang.org/x/time/rate (production-grade)
// import "golang.org/x/time/rate"
// limiter := rate.NewLimiter(rate.Limit(100), 10) // 100 rps, burst 10
// err := limiter.Wait(ctx)
```

### Circuit Breaker

```go
// file: circuit_breaker.go
package main

import (
    "errors"
    "sync"
    "time"
)

type State int

const (
    StateClosed   State = iota // Normal — requests pass through
    StateOpen                  // Failure threshold exceeded — requests fail fast
    StateHalfOpen              // Testing if service recovered
)

var ErrCircuitOpen = errors.New("circuit breaker is open")

type CircuitBreaker struct {
    mu            sync.Mutex
    state         State
    failures      int
    successes     int
    lastFailure   time.Time
    
    maxFailures   int
    resetTimeout  time.Duration
    halfOpenMax   int
}

func NewCircuitBreaker(maxFail int, resetTO time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        maxFailures:  maxFail,
        resetTimeout: resetTO,
        halfOpenMax:  1,
    }
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()
    
    switch cb.state {
    case StateOpen:
        if time.Since(cb.lastFailure) > cb.resetTimeout {
            cb.state = StateHalfOpen
            cb.successes = 0
        } else {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
    case StateHalfOpen:
        if cb.successes >= cb.halfOpenMax {
            cb.mu.Unlock()
            return ErrCircuitOpen // still testing
        }
    }
    
    cb.mu.Unlock()
    
    err := fn()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.maxFailures || cb.state == StateHalfOpen {
            cb.state = StateOpen
        }
        return err
    }
    
    // Success
    cb.failures = 0
    if cb.state == StateHalfOpen {
        cb.successes++
        if cb.successes >= cb.halfOpenMax {
            cb.state = StateClosed
        }
    }
    return nil
}
```

### Fan-Out Fan-In

```go
// file: fan_out_fan_in.go
package main

import (
    "context"
    "sync"
)

// Fan-out: distribute work to N workers
func fanOut[T, R any](
    ctx context.Context,
    input <-chan T,
    n int,
    fn func(context.Context, T) R,
) []<-chan R {
    outputs := make([]<-chan R, n)
    for i := 0; i < n; i++ {
        ch := make(chan R)
        outputs[i] = ch
        go func() {
            defer close(ch)
            for {
                select {
                case <-ctx.Done():
                    return
                case v, ok := <-input:
                    if !ok {
                        return
                    }
                    select {
                    case ch <- fn(ctx, v):
                    case <-ctx.Done():
                        return
                    }
                }
            }
        }()
    }
    return outputs
}

// Fan-in: merge N channels into one
func fanIn[T any](ctx context.Context, inputs ...<-chan T) <-chan T {
    out := make(chan T)
    var wg sync.WaitGroup
    
    for _, ch := range inputs {
        wg.Add(1)
        go func(c <-chan T) {
            defer wg.Done()
            for {
                select {
                case <-ctx.Done():
                    return
                case v, ok := <-c:
                    if !ok {
                        return
                    }
                    select {
                    case out <- v:
                    case <-ctx.Done():
                        return
                    }
                }
            }
        }(ch)
    }
    
    go func() {
        wg.Wait()
        close(out)
    }()
    
    return out
}
```

### Semaphore Pattern

```go
// Limit concurrent goroutines using buffered channel
type Semaphore chan struct{}

func NewSemaphore(n int) Semaphore {
    return make(Semaphore, n)
}

func (s Semaphore) Acquire(ctx context.Context) error {
    select {
    case s <- struct{}{}: // acquire slot
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (s Semaphore) Release() {
    <-s // release slot
}

// Usage:
func limitedConcurrency(ctx context.Context, tasks []string) {
    sem := NewSemaphore(10) // max 10 concurrent
    var wg sync.WaitGroup
    
    for _, task := range tasks {
        wg.Add(1)
        go func(t string) {
            defer wg.Done()
            if err := sem.Acquire(ctx); err != nil {
                return
            }
            defer sem.Release()
            // do work
        }(task)
    }
    wg.Wait()
}
```

---

## 17. Networking — HTTP/2, gRPC, TLS Internals

### HTTP/2 in Go

```go
// file: http2_server.go
package main

import (
    "crypto/tls"
    "fmt"
    "log"
    "net/http"
    "time"
    
    "golang.org/x/net/http2"
    "golang.org/x/net/http2/h2c"
)

// HTTP/2 key features:
// - Multiplexing: multiple streams over single TCP connection
// - Header compression (HPACK)
// - Server push
// - Binary framing (not text like HTTP/1.1)
// - Stream prioritization

func http2Server() {
    mux := http.NewServeMux()
    mux.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
        fmt.Fprintf(w, "Protocol: %s\n", r.Proto)
    })
    
    // HTTP/2 over TLS (standard)
    server := &http.Server{
        Addr:    ":8443",
        Handler: mux,
        TLSConfig: &tls.Config{
            MinVersion: tls.VersionTLS12,
            CurvePreferences: []tls.CurveID{
                tls.X25519, tls.CurveP256,
            },
            CipherSuites: []uint16{
                tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
                tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
                tls.TLS_AES_128_GCM_SHA256, // TLS 1.3
            },
        },
        ReadTimeout:       5 * time.Second,
        WriteTimeout:      10 * time.Second,
        IdleTimeout:       120 * time.Second,
        ReadHeaderTimeout: 2 * time.Second,
    }
    
    // Go automatically enables HTTP/2 when serving HTTPS
    log.Fatal(server.ListenAndServeTLS("cert.pem", "key.pem"))
}

// HTTP/2 cleartext (h2c) — for service mesh / internal
func h2cServer() {
    h2s := &http2.Server{}
    handler := h2c.NewHandler(http.DefaultServeMux, h2s)
    
    server := &http.Server{
        Addr:    ":8080",
        Handler: handler,
    }
    log.Fatal(server.ListenAndServe())
}

// HTTP/2 server push
func pushHandler(w http.ResponseWriter, r *http.Request) {
    if pusher, ok := w.(http.Pusher); ok {
        // Push /style.css before client requests it
        if err := pusher.Push("/style.css", &http.PushOptions{
            Header: http.Header{"Content-Type": {"text/css"}},
        }); err != nil {
            log.Printf("Push failed: %v", err)
        }
    }
    fmt.Fprintln(w, "<html>...</html>")
}
```

### HTTP Client — Production Configuration

```go
// file: http_client.go
package main

import (
    "context"
    "crypto/tls"
    "net"
    "net/http"
    "time"
)

func NewProductionClient() *http.Client {
    transport := &http.Transport{
        // Connection pooling
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 20,
        MaxConnsPerHost:     100,
        IdleConnTimeout:     90 * time.Second,
        
        // Timeouts
        DialContext: (&net.Dialer{
            Timeout:   5 * time.Second,  // TCP connection timeout
            KeepAlive: 30 * time.Second, // TCP keepalive
        }).DialContext,
        TLSHandshakeTimeout:   10 * time.Second,
        ResponseHeaderTimeout: 10 * time.Second, // time to first response byte
        ExpectContinueTimeout: 1 * time.Second,
        
        // TLS config
        TLSClientConfig: &tls.Config{
            MinVersion: tls.VersionTLS12,
        },
        
        // Compression
        DisableCompression: false,
        
        // HTTP/2 (enabled automatically with TLS)
        ForceAttemptHTTP2: true,
    }
    
    return &http.Client{
        Transport: transport,
        Timeout:   30 * time.Second, // TOTAL request timeout (incl. body read)
    }
}

// Retry with exponential backoff
func doWithRetry(ctx context.Context, client *http.Client, req *http.Request, maxRetries int) (*http.Response, error) {
    var (
        resp *http.Response
        err  error
    )
    
    backoff := 100 * time.Millisecond
    
    for attempt := 0; attempt <= maxRetries; attempt++ {
        if attempt > 0 {
            select {
            case <-ctx.Done():
                return nil, ctx.Err()
            case <-time.After(backoff):
                backoff *= 2
                if backoff > 30*time.Second {
                    backoff = 30 * time.Second
                }
            }
        }
        
        // Clone request for retry (body consumed)
        clonedReq := req.Clone(ctx)
        resp, err = client.Do(clonedReq)
        
        if err != nil {
            continue
        }
        
        if resp.StatusCode == http.StatusTooManyRequests ||
            resp.StatusCode >= 500 {
            resp.Body.Close()
            continue
        }
        
        return resp, nil
    }
    
    return nil, fmt.Errorf("all %d retries failed: %w", maxRetries, err)
}
```

### gRPC in Go

```
gRPC frame format over HTTP/2:
┌────────────────────────────────────────────────────┐
│  HTTP/2 Frame                                       │
│  ┌────────────────────────────────────────────┐    │
│  │  DATA Frame payload:                        │    │
│  │  ┌────┬────────────────────────────────┐   │    │
│  │  │ 5B │     Protobuf message           │   │    │
│  │  │ hdr│  (length-prefixed)             │   │    │
│  │  └────┴────────────────────────────────┘   │    │
│  │  Byte 0: Compressed flag (0/1)              │    │
│  │  Bytes 1-4: Message length (big-endian)     │    │
│  └────────────────────────────────────────────┘    │
└────────────────────────────────────────────────────┘
```

```go
// file: grpc_server.go  (requires: google.golang.org/grpc)
package main

import (
    "context"
    "log"
    "net"
    "time"
    
    "google.golang.org/grpc"
    "google.golang.org/grpc/codes"
    "google.golang.org/grpc/keepalive"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"
    pb "mypackage/proto"
)

type UserService struct {
    pb.UnimplementedUserServiceServer
}

func (s *UserService) GetUser(ctx context.Context, req *pb.GetUserRequest) (*pb.User, error) {
    // Extract metadata (like HTTP headers)
    md, ok := metadata.FromIncomingContext(ctx)
    if !ok {
        return nil, status.Error(codes.InvalidArgument, "missing metadata")
    }
    
    token := md.Get("authorization")
    if len(token) == 0 {
        return nil, status.Error(codes.Unauthenticated, "missing token")
    }
    
    // Return gRPC status errors (not Go errors)
    if req.Id == "" {
        return nil, status.Errorf(codes.InvalidArgument, "id is required")
    }
    
    return &pb.User{Id: req.Id, Name: "Alice"}, nil
}

// Streaming RPC
func (s *UserService) ListUsers(req *pb.ListUsersRequest, stream pb.UserService_ListUsersServer) error {
    for i := 0; i < 10; i++ {
        if err := stream.Context().Err(); err != nil {
            return err // client disconnected
        }
        
        if err := stream.Send(&pb.User{Id: fmt.Sprintf("%d", i)}); err != nil {
            return err
        }
    }
    return nil
}

func main() {
    lis, _ := net.Listen("tcp", ":50051")
    
    // Interceptors (middleware)
    loggingInterceptor := func(ctx context.Context, req interface{}, info *grpc.UnaryServerInfo, handler grpc.UnaryHandler) (interface{}, error) {
        start := time.Now()
        resp, err := handler(ctx, req)
        log.Printf("RPC: %s duration=%v err=%v", info.FullMethod, time.Since(start), err)
        return resp, err
    }
    
    server := grpc.NewServer(
        grpc.UnaryInterceptor(loggingInterceptor),
        grpc.KeepaliveParams(keepalive.ServerParameters{
            MaxConnectionIdle:     15 * time.Minute,
            MaxConnectionAge:      30 * time.Minute,
            MaxConnectionAgeGrace: 5 * time.Second,
            Time:                  5 * time.Minute,
            Timeout:               1 * time.Minute,
        }),
        grpc.MaxRecvMsgSize(4 * 1024 * 1024), // 4MB
        grpc.MaxSendMsgSize(4 * 1024 * 1024),
    )
    
    pb.RegisterUserServiceServer(server, &UserService{})
    log.Fatal(server.Serve(lis))
}
```

---

## 18. Testing — Unit, Integration, Fuzzing, Race Detection

### Test Structure & Table-Driven Tests

```go
// file: user_test.go
package user_test

import (
    "context"
    "errors"
    "testing"
    "time"
    
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
    "go.uber.org/goleak"
)

// ── Table-driven tests ────────────────────────────────────────────────
func TestValidateAge(t *testing.T) {
    tests := []struct {
        name    string
        age     int
        wantErr bool
        errMsg  string
    }{
        {name: "valid age", age: 25, wantErr: false},
        {name: "zero age", age: 0, wantErr: false},
        {name: "negative age", age: -1, wantErr: true, errMsg: "age cannot be negative"},
        {name: "too old", age: 200, wantErr: true, errMsg: "age out of range"},
    }
    
    for _, tc := range tests {
        tc := tc // capture loop variable (Go < 1.22)
        t.Run(tc.name, func(t *testing.T) {
            t.Parallel() // run subtests in parallel
            
            err := validateAge(tc.age)
            
            if tc.wantErr {
                require.Error(t, err)
                assert.Contains(t, err.Error(), tc.errMsg)
            } else {
                require.NoError(t, err)
            }
        })
    }
}

// ── Goroutine leak detection ──────────────────────────────────────────
func TestMain(m *testing.M) {
    goleak.VerifyTestMain(m) // fails if goroutines leak after tests
}

// ── Test with timeout ─────────────────────────────────────────────────
func TestLongOperation(t *testing.T) {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    done := make(chan error, 1)
    go func() {
        done <- longOperation(ctx)
    }()
    
    select {
    case err := <-done:
        require.NoError(t, err)
    case <-ctx.Done():
        t.Fatal("test timed out")
    }
}

// ── Test doubles: interface-based mocking ────────────────────────────
type UserRepository interface {
    FindByID(ctx context.Context, id int) (*User, error)
    Save(ctx context.Context, u *User) error
}

type MockUserRepo struct {
    users map[int]*User
    err   error
}

func (m *MockUserRepo) FindByID(_ context.Context, id int) (*User, error) {
    if m.err != nil { return nil, m.err }
    u, ok := m.users[id]
    if !ok { return nil, ErrNotFound }
    return u, nil
}

func (m *MockUserRepo) Save(_ context.Context, u *User) error {
    if m.err != nil { return m.err }
    m.users[u.ID] = u
    return nil
}

func TestUserService(t *testing.T) {
    repo := &MockUserRepo{
        users: map[int]*User{
            1: {ID: 1, Name: "Alice"},
        },
    }
    
    svc := NewUserService(repo)
    
    t.Run("found", func(t *testing.T) {
        user, err := svc.GetUser(context.Background(), 1)
        require.NoError(t, err)
        assert.Equal(t, "Alice", user.Name)
    })
    
    t.Run("not found", func(t *testing.T) {
        _, err := svc.GetUser(context.Background(), 999)
        assert.True(t, errors.Is(err, ErrNotFound))
    })
    
    t.Run("repo error", func(t *testing.T) {
        repo.err = errors.New("database down")
        defer func() { repo.err = nil }()
        
        _, err := svc.GetUser(context.Background(), 1)
        require.Error(t, err)
    })
}

// ── Golden file testing ───────────────────────────────────────────────
func TestRenderTemplate(t *testing.T) {
    got := renderTemplate("welcome", map[string]string{"Name": "Alice"})
    
    goldenFile := "testdata/welcome.golden"
    if *update { // flag: -update
        os.WriteFile(goldenFile, []byte(got), 0644)
    }
    
    want, _ := os.ReadFile(goldenFile)
    assert.Equal(t, string(want), got)
}
```

### Fuzzing (Go 1.18+)

```go
// file: fuzz_test.go
package parse_test

import (
    "testing"
    "unicode/utf8"
)

// Fuzz test: find inputs that crash or produce wrong output
func FuzzParseJSON(f *testing.F) {
    // Seed corpus — valid inputs to start from
    f.Add(`{"name":"Alice","age":30}`)
    f.Add(`{}`)
    f.Add(`{"key":null}`)
    
    f.Fuzz(func(t *testing.T, data string) {
        // Properties that should ALWAYS hold:
        result, err := parseJSON(data)
        
        if err != nil {
            return // errors are OK
        }
        
        // 1. If parse succeeds, re-serializing should be valid UTF-8
        reserialized := result.String()
        if !utf8.ValidString(reserialized) {
            t.Errorf("output is not valid UTF-8: %q", reserialized)
        }
        
        // 2. Idempotency: parsing twice gives same result
        result2, err2 := parseJSON(reserialized)
        if err2 != nil {
            t.Errorf("re-parse failed: %v", err2)
        }
        if result.String() != result2.String() {
            t.Errorf("not idempotent: %q != %q", result.String(), result2.String())
        }
    })
}
```

```bash
# Run fuzzer (keeps running until timeout or crash)
go test -fuzz=FuzzParseJSON -fuzztime=60s

# After crash, run the failing input:
go test -run=FuzzParseJSON/testdata/corpus/xxx

# Regression: all corpus files run on normal test
go test -run=FuzzParseJSON
```

### Race Detector

```bash
# Always test with race detector in CI
go test -race ./...
go run -race main.go
go build -race && ./myapp  # race detection in binary

# GORACE options:
GORACE="halt_on_error=1 history_size=7" go test -race ./...
# halt_on_error: crash on first race (default: report and continue)
# history_size: longer history = better diagnosis, more memory
```

### Integration Tests

```go
// file: integration_test.go
//go:build integration
// +build integration

// Run with: go test -tags=integration ./...

package db_test

import (
    "context"
    "os"
    "testing"
    
    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
)

func TestPostgresIntegration(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test in short mode")
    }
    
    ctx := context.Background()
    
    // Spin up real Postgres in Docker
    container, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:15"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
    )
    if err != nil {
        t.Fatal(err)
    }
    defer container.Terminate(ctx)
    
    connStr, _ := container.ConnectionString(ctx, "sslmode=disable")
    
    db, err := sql.Open("postgres", connStr)
    require.NoError(t, err)
    defer db.Close()
    
    // Run migrations
    runMigrations(db)
    
    repo := NewUserRepo(db)
    
    // Test against real database
    user := &User{Name: "Test User", Email: "test@example.com"}
    err = repo.Save(ctx, user)
    require.NoError(t, err)
    
    found, err := repo.FindByEmail(ctx, "test@example.com")
    require.NoError(t, err)
    assert.Equal(t, user.Name, found.Name)
}
```

---

## 19. Distributed Systems Patterns in Go

### Consistent Hashing

```go
// file: consistent_hash.go
package main

import (
    "crypto/sha256"
    "encoding/binary"
    "fmt"
    "sort"
    "sync"
)

// Consistent hashing ring — minimal key remapping when nodes added/removed
type Ring struct {
    mu       sync.RWMutex
    replicas int
    keys     []int            // sorted virtual node hashes
    nodes    map[int]string   // hash → node
}

func NewRing(replicas int) *Ring {
    return &Ring{
        replicas: replicas,
        nodes:    make(map[int]string),
    }
}

func (r *Ring) hash(key string) int {
    h := sha256.Sum256([]byte(key))
    return int(binary.BigEndian.Uint32(h[:4]))
}

func (r *Ring) Add(node string) {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    for i := 0; i < r.replicas; i++ {
        h := r.hash(fmt.Sprintf("%s:%d", node, i))
        r.keys = append(r.keys, h)
        r.nodes[h] = node
    }
    sort.Ints(r.keys)
}

func (r *Ring) Remove(node string) {
    r.mu.Lock()
    defer r.mu.Unlock()
    
    for i := 0; i < r.replicas; i++ {
        h := r.hash(fmt.Sprintf("%s:%d", node, i))
        delete(r.nodes, h)
        for j, k := range r.keys {
            if k == h {
                r.keys = append(r.keys[:j], r.keys[j+1:]...)
                break
            }
        }
    }
}

func (r *Ring) Get(key string) string {
    r.mu.RLock()
    defer r.mu.RUnlock()
    
    if len(r.keys) == 0 {
        return ""
    }
    
    h := r.hash(key)
    // Find first node with hash >= h (clockwise on ring)
    idx := sort.SearchInts(r.keys, h)
    if idx == len(r.keys) {
        idx = 0 // wrap around
    }
    return r.nodes[r.keys[idx]]
}
```

### Distributed Lock with Redis

```go
// file: dist_lock.go
package main

import (
    "context"
    "errors"
    "fmt"
    "math/rand"
    "time"
    
    "github.com/redis/go-redis/v9"
)

type DistributedLock struct {
    client  *redis.Client
    key     string
    token   string        // unique per lock acquisition
    ttl     time.Duration
}

var ErrLockNotAcquired = errors.New("lock not acquired")

func NewDistributedLock(client *redis.Client, key string, ttl time.Duration) *DistributedLock {
    return &DistributedLock{
        client: client,
        key:    "lock:" + key,
        token:  fmt.Sprintf("%d-%d", time.Now().UnixNano(), rand.Int63()),
        ttl:    ttl,
    }
}

func (l *DistributedLock) Acquire(ctx context.Context) error {
    // SET key token NX PX ttl_ms — atomic, only set if not exists
    ok, err := l.client.SetNX(ctx, l.key, l.token, l.ttl).Result()
    if err != nil {
        return fmt.Errorf("acquire lock: %w", err)
    }
    if !ok {
        return ErrLockNotAcquired
    }
    return nil
}

// Release: only delete if we own the lock (compare-and-delete via Lua)
var releaseScript = redis.NewScript(`
    if redis.call("GET", KEYS[1]) == ARGV[1] then
        return redis.call("DEL", KEYS[1])
    else
        return 0
    end
`)

func (l *DistributedLock) Release(ctx context.Context) error {
    result, err := releaseScript.Run(ctx, l.client, []string{l.key}, l.token).Result()
    if err != nil {
        return fmt.Errorf("release lock: %w", err)
    }
    if result.(int64) == 0 {
        return errors.New("lock not owned or expired")
    }
    return nil
}

// WithLock: acquire, execute, release — with automatic retry
func WithLock(ctx context.Context, lock *DistributedLock, fn func() error) error {
    backoff := 50 * time.Millisecond
    
    for {
        err := lock.Acquire(ctx)
        if err == nil {
            break
        }
        if !errors.Is(err, ErrLockNotAcquired) {
            return err
        }
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(backoff):
            backoff = min(backoff*2, 2*time.Second)
        }
    }
    
    defer lock.Release(ctx)
    return fn()
}
```

### Outbox Pattern (Guaranteed Message Delivery)

```
Problem: Write to DB and publish to message queue — one may fail.
Solution: Write message to DB in same transaction (outbox table),
          background process reads outbox and publishes to queue.

┌──────────────────────────────────────────────────────────────┐
│  Application                                                   │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Transaction:                                           │  │
│  │    INSERT INTO orders (...)                             │  │
│  │    INSERT INTO outbox (event, payload, status='pending')│  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │  Outbox Worker (runs every N seconds):                  │  │
│  │    SELECT * FROM outbox WHERE status='pending'          │  │
│  │    FOR EACH: publish to Kafka/RabbitMQ                  │  │
│  │    UPDATE outbox SET status='published'                 │  │
│  └────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
```

```go
// file: outbox.go
package main

import (
    "context"
    "database/sql"
    "encoding/json"
    "time"
)

type OutboxEvent struct {
    ID        int64
    EventType string
    Payload   json.RawMessage
    CreatedAt time.Time
    Status    string // pending, published, failed
}

type OutboxWorker struct {
    db        *sql.DB
    publisher MessagePublisher
    interval  time.Duration
}

func (w *OutboxWorker) Run(ctx context.Context) {
    ticker := time.NewTicker(w.interval)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            if err := w.processOutbox(ctx); err != nil {
                log.Printf("outbox error: %v", err)
            }
        }
    }
}

func (w *OutboxWorker) processOutbox(ctx context.Context) error {
    // Select with advisory lock to prevent concurrent workers
    rows, err := w.db.QueryContext(ctx, `
        SELECT id, event_type, payload
        FROM outbox
        WHERE status = 'pending'
        ORDER BY id
        LIMIT 100
        FOR UPDATE SKIP LOCKED  -- PostgreSQL: skip rows locked by other workers
    `)
    if err != nil {
        return err
    }
    defer rows.Close()
    
    for rows.Next() {
        var evt OutboxEvent
        if err := rows.Scan(&evt.ID, &evt.EventType, &evt.Payload); err != nil {
            return err
        }
        
        if err := w.publisher.Publish(ctx, evt.EventType, evt.Payload); err != nil {
            // Mark as failed, retry later
            w.db.ExecContext(ctx, `UPDATE outbox SET status='failed' WHERE id=$1`, evt.ID)
            continue
        }
        
        w.db.ExecContext(ctx, `UPDATE outbox SET status='published' WHERE id=$1`, evt.ID)
    }
    
    return rows.Err()
}
```

### Saga Pattern

```
Distributed transaction across microservices:

Order Service → Payment Service → Inventory Service → Shipping Service

If Inventory fails:
  → Rollback: Compensate Payment, Cancel Order

Choreography (event-driven):
  Each service listens for events and emits compensation events on failure

Orchestration (centralized):
  Saga orchestrator drives the workflow, knows each step, issues compensations

Go implementation: use state machine + durable execution (Temporal/Cadence)
```

---

## 20. CGo & FFI Basics

### How CGo Works

```go
// file: cgo_example.go
package main

/*
#include <stdlib.h>
#include <string.h>

// C function callable from Go
int add(int a, int b) {
    return a + b;
}

// String manipulation in C
char* greet(const char* name) {
    char* result = malloc(strlen(name) + 8);
    sprintf(result, "Hello, %s!", name);
    return result;
}
*/
import "C"

import (
    "fmt"
    "unsafe"
)

func main() {
    // Call C function
    result := C.add(3, 4)
    fmt.Println(int(result)) // 7
    
    // Pass Go string to C
    name := C.CString("Gopher") // allocates C memory!
    defer C.free(unsafe.Pointer(name)) // MUST free!
    
    // Call C function returning string
    greeting := C.greet(name)
    defer C.free(unsafe.Pointer(greeting))
    
    // Convert C string to Go string
    fmt.Println(C.GoString(greeting))
    
    // Go slice → C array
    goSlice := []int32{1, 2, 3, 4, 5}
    cArray := (*C.int)(unsafe.Pointer(&goSlice[0]))
    _ = cArray // pass to C function expecting int*
}
```

### CGo Rules & Gotchas

```
1. C code runs in C goroutine-unsafe context
   → CGo calls lock the goroutine to its OS thread temporarily
   → Expensive: ~100ns overhead per CGo call (vs ~1ns Go call)

2. Go pointers passed to C must follow rules:
   → C code may NOT store Go pointers beyond the call
   → C may NOT call back into Go with a stored Go pointer
   (GC moves objects; C would have stale pointer)

3. Memory ownership:
   → C.CString() → must C.free()
   → C.malloc()  → must C.free()
   → Go GC does NOT manage C heap memory

4. Goroutine pinning:
   → runtime.LockOSThread() if C library uses thread-local storage
   → Some C libraries (OpenGL, some database drivers) require this

5. CGo disables cross-compilation by default
   → Use CC=x86_64-linux-gnu-gcc with CGO_ENABLED=1 for cross-compile
   → Or: CGO_ENABLED=0 for pure Go (no CGo)

6. Stack switching overhead:
   → Every CGo call: switch from goroutine stack to OS thread stack
   → Then back on return
```

### Pure Go Alternative: syscall/x/sys

```go
// Prefer Go's syscall package over CGo for OS interactions
import "golang.org/x/sys/unix"

// Zero-copy file read via mmap
func mmapFile(path string) ([]byte, error) {
    f, err := os.Open(path)
    if err != nil { return nil, err }
    defer f.Close()
    
    stat, _ := f.Stat()
    size := int(stat.Size())
    
    data, err := unix.Mmap(int(f.Fd()), 0, size, unix.PROT_READ, unix.MAP_SHARED)
    if err != nil { return nil, err }
    
    // Remember to Munmap when done
    // defer unix.Munmap(data)
    return data, nil
}
```

---

## 21. Build System, Toolchain & Release Engineering

### Go Module System

```bash
# Module initialization
go mod init github.com/company/project

# go.mod: declares module path, Go version, dependencies
module github.com/company/project

go 1.22

require (
    github.com/pkg/errors v0.9.1
    golang.org/x/sync v0.6.0
)

require (
    // indirect dependencies
    github.com/some/transitive v1.0.0 // indirect
)

# Commands:
go mod tidy          # remove unused, add missing dependencies
go mod download      # download all to module cache
go mod verify        # verify checksums against go.sum
go mod vendor        # vendor dependencies (copy to ./vendor)
go mod graph         # print dependency graph
go list -m all       # list all modules

# Upgrade/downgrade:
go get github.com/pkg/errors@latest     # latest version
go get github.com/pkg/errors@v0.9.0    # specific version
go get github.com/pkg/errors@none      # remove dependency
```

### Build Tags & Conditional Compilation

```go
//go:build linux && amd64
// +build linux,amd64  (old syntax, still supported)

package main
// This file only compiled on Linux AMD64

//go:build !cgo
// Only when CGo is disabled

//go:build integration
// Only with: go test -tags=integration

// Platform-specific files (auto-selected by filename):
// _linux.go, _windows.go, _darwin.go
// _amd64.go, _arm64.go
// file_linux_amd64.go — both OS and arch
```

### ldflags — Injecting Build Info

```go
// file: version.go
package main

var (
    Version   = "dev"     // overridden at build time
    GitCommit = "unknown"
    BuildTime = "unknown"
)

func main() {
    fmt.Printf("Version: %s\nCommit: %s\nBuilt: %s\n",
        Version, GitCommit, BuildTime)
}
```

```bash
# Inject at build time:
go build -ldflags "\
  -X main.Version=v1.2.3 \
  -X main.GitCommit=$(git rev-parse --short HEAD) \
  -X main.BuildTime=$(date -u +%Y%m%dT%H%M%SZ) \
  -s -w" \    # -s: strip symbol table, -w: strip DWARF info
  -o myapp

# Cross-compilation:
GOOS=linux   GOARCH=amd64   go build -o app-linux-amd64
GOOS=windows GOARCH=amd64   go build -o app-windows.exe
GOOS=darwin  GOARCH=arm64   go build -o app-darwin-arm64

# All combinations:
GOOS=linux   GOARCH=arm64   go build
GOOS=linux   GOARCH=386     go build

# Supported platforms:
go tool dist list
```

### go generate

```bash
# go:generate directives run tools before build
//go:generate protoc --go_out=. --go-grpc_out=. proto/api.proto
//go:generate mockgen -source=interface.go -destination=mock_test.go
//go:generate stringer -type=Status

# Run all generates:
go generate ./...
```

### Minimal Docker Image

```dockerfile
# file: Dockerfile
# Stage 1: Build
FROM golang:1.22-alpine AS builder

WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download         # cache layer

COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build \
    -ldflags="-s -w -X main.Version=${VERSION}" \
    -o /app/server ./cmd/server

# Stage 2: Minimal runtime
FROM scratch                # absolutely minimal — no shell, no OS

# Copy TLS root certificates (needed for HTTPS calls)
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/

# Copy binary
COPY --from=builder /app/server /server

EXPOSE 8080
ENTRYPOINT ["/server"]

# Final image size: ~5-15MB (vs 300MB+ with debian base)
```

### Makefile for Go Projects

```makefile
# file: Makefile
.PHONY: all build test lint clean

VERSION := $(shell git describe --tags --always --dirty)
COMMIT  := $(shell git rev-parse --short HEAD)
DATE    := $(shell date -u +%Y%m%dT%H%M%SZ)
LDFLAGS := -ldflags "-X main.Version=$(VERSION) -X main.GitCommit=$(COMMIT) -X main.BuildTime=$(DATE) -s -w"

all: lint test build

build:
	CGO_ENABLED=0 go build $(LDFLAGS) -o bin/server ./cmd/server

test:
	go test -race -count=1 -timeout=120s ./...

test-integration:
	go test -race -tags=integration -timeout=300s ./...

fuzz:
	go test -fuzz=FuzzParseInput -fuzztime=60s ./internal/parser/...

lint:
	golangci-lint run --timeout=5m

bench:
	go test -bench=. -benchmem -count=5 ./...

profile-cpu:
	go test -bench=BenchmarkHot -cpuprofile=cpu.prof -benchtime=30s ./...
	go tool pprof -http=:8080 cpu.prof

cover:
	go test -coverprofile=coverage.out ./...
	go tool cover -html=coverage.out -o coverage.html

docker:
	docker build --build-arg VERSION=$(VERSION) -t myapp:$(VERSION) .

clean:
	rm -rf bin/ coverage.out *.prof *.out
```

---

## 22. Security Checklist & Production Hardening

### Input Validation

```go
// file: security.go
package main

import (
    "errors"
    "net/http"
    "regexp"
    "unicode/utf8"
)

// ── Input validation ──────────────────────────────────────────────────
var (
    emailRegex = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
    safeIDRegex = regexp.MustCompile(`^[a-zA-Z0-9\-_]{1,64}$`)
)

func validateInput(s string, maxLen int) error {
    if len(s) > maxLen {
        return errors.New("input too long")
    }
    if !utf8.ValidString(s) {
        return errors.New("invalid UTF-8")
    }
    return nil
}

// ── SQL injection prevention: always use parameterized queries ─────────
func getUser(db *sql.DB, id string) (*User, error) {
    // WRONG:
    // db.Query("SELECT * FROM users WHERE id = " + id)
    
    // CORRECT: parameterized
    row := db.QueryRow("SELECT id, name FROM users WHERE id = $1", id)
    var u User
    return &u, row.Scan(&u.ID, &u.Name)
}

// ── XSS prevention: html/template auto-escapes ───────────────────────
// Use html/template, NOT text/template for user-facing HTML
import "html/template"

var tmpl = template.Must(template.New("page").Parse(`
    <p>Hello, {{.Name}}!</p>
`))
// {{.Name}} is automatically HTML-escaped

// ── CSRF: use SameSite cookies + CSRF token ──────────────────────────
func setCookie(w http.ResponseWriter) {
    http.SetCookie(w, &http.Cookie{
        Name:     "session",
        Value:    generateToken(),
        HttpOnly: true,  // no JS access
        Secure:   true,  // HTTPS only
        SameSite: http.SameSiteStrictMode,
        Path:     "/",
        MaxAge:   3600,
    })
}

// ── Rate limiting ─────────────────────────────────────────────────────
// Use golang.org/x/time/rate or a middleware

// ── Secrets: never in code, use env vars or vault ────────────────────
import "os"

func getDatabaseURL() string {
    url := os.Getenv("DATABASE_URL")
    if url == "" {
        panic("DATABASE_URL not set")
    }
    return url
}

// ── TLS configuration ─────────────────────────────────────────────────
func secureTLSConfig() *tls.Config {
    return &tls.Config{
        MinVersion: tls.VersionTLS12,
        CurvePreferences: []tls.CurveID{
            tls.X25519,
            tls.CurveP256,
        },
        PreferServerCipherSuites: true,
        CipherSuites: []uint16{
            // TLS 1.3 ciphers (automatic, don't configure)
            // TLS 1.2 ciphers (AEAD only):
            tls.TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256,
            tls.TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256,
            tls.TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384,
            tls.TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305,
            tls.TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305,
        },
    }
}
```

### Security Checklist

```
[ ] Input validation on ALL external inputs (HTTP, gRPC, queues)
[ ] SQL: parameterized queries only — NEVER string concatenation
[ ] HTML: html/template, not text/template
[ ] Passwords: bcrypt/scrypt/argon2 — NEVER md5/sha1
[ ] Secrets: env vars or vault — NEVER in code or .env files in git
[ ] TLS: minimum 1.2, prefer 1.3 — disable weak ciphers
[ ] Cookies: HttpOnly, Secure, SameSite=Strict
[ ] CORS: explicit allowlist, not *
[ ] Rate limiting on all public endpoints
[ ] Request size limits (http.MaxBytesReader)
[ ] Timeouts on ALL outbound HTTP calls
[ ] File paths: filepath.Clean + validate no ../ traversal
[ ] Error messages: don't leak internal details to clients
[ ] Dependencies: go mod verify + govulncheck in CI
[ ] Run with govulncheck: go install golang.org/x/vuln/cmd/govulncheck@latest
[ ] Build with -trimpath to remove local paths from binary
[ ] Container: non-root user, read-only filesystem, no-new-privileges
```

---

## 23. Tricky Interview Questions & Brain Teasers

### Q1: What does this print?

```go
package main

import "fmt"

func main() {
    s := []int{1, 2, 3}
    
    for _, v := range s {
        go func() {
            fmt.Println(v) // Go < 1.22
        }()
    }
    
    // Answer (Go < 1.22): likely prints "3 3 3"
    // All goroutines capture the SAME variable v
    // By the time goroutines run, loop is done, v=3
    
    // Go 1.22+: each iteration creates new v → prints 1 2 3 (any order)
    
    // Fix (Go < 1.22):
    for _, v := range s {
        v := v // new variable per iteration
        go func() { fmt.Println(v) }()
    }
}
```

### Q2: What does this print?

```go
package main

import "fmt"

func main() {
    var wg sync.WaitGroup
    for i := 0; i < 3; i++ {
        wg.Add(1)
        go func(n int) {
            defer wg.Done()
            fmt.Println(n)
        }(i) // pass i as argument — correct!
    }
    wg.Wait()
    // Prints 0, 1, 2 in arbitrary order (correct approach)
}
```

### Q3: Nil interface vs nil pointer

```go
func makeError(fail bool) error {
    var p *os.PathError
    if fail {
        p = &os.PathError{Op: "open", Path: "/x"}
    }
    return p  // TRAP: always non-nil interface even when fail=false!
}

result := makeError(false)
fmt.Println(result == nil) // false! Trap!
```

### Q4: Goroutine stack growth in defer

```go
func f() {
    defer func() {
        if r := recover(); r != nil {
            fmt.Println("recovered:", r)
        }
    }()
    
    var s []int
    s[0] = 1 // panic: index out of range
    // defer recovers this — prints "recovered: ..."
}

// But: recover only works in DIRECT defer, not nested:
func g() {
    defer func() {
        go func() {
            recover() // does NOT work — different goroutine
        }()
    }()
    panic("boom") // NOT recovered — program crashes
}
```

### Q5: Closed channel behavior

```go
ch := make(chan int, 3)
ch <- 1
ch <- 2
close(ch)

// Reading from closed channel:
v1, ok1 := <-ch  // v1=1, ok1=true  (buffered data available)
v2, ok2 := <-ch  // v2=2, ok2=true
v3, ok3 := <-ch  // v3=0, ok3=false (zero value, channel empty+closed)
v4, ok4 := <-ch  // v4=0, ok4=false (always zero value after close)

// for range reads until closed:
for v := range ch { } // ok

// Sending to closed channel: PANIC
ch <- 3 // panic: send on closed channel
close(ch) // close twice: PANIC
```

### Q6: defer evaluation order

```go
func count() (result int) {
    defer func() {
        result++ // modifies named return value!
    }()
    return 1 // sets result=1, THEN runs defer → result=2
}

// Answer: count() returns 2

func sum() int {
    x := 0
    defer fmt.Println(x) // x evaluated NOW (0), not when defer runs
    x = 10
    return x
    // prints 0, returns 10
}
```

### Q7: Map iteration order

```go
m := map[string]int{"a": 1, "b": 2, "c": 3}

// Iteration order is RANDOMIZED deliberately (security: prevent hash DoS)
// NEVER depend on map iteration order
for k, v := range m {
    fmt.Println(k, v) // random order each run
}

// Sorted iteration:
import "sort"
keys := make([]string, 0, len(m))
for k := range m { keys = append(keys, k) }
sort.Strings(keys)
for _, k := range keys {
    fmt.Println(k, m[k])
}
```

### Q8: Interface comparison — when does it panic?

```go
// Interface comparison panics if underlying type is not comparable
type MySlice []int

var i interface{} = MySlice{1, 2, 3}
var j interface{} = MySlice{1, 2, 3}

fmt.Println(i == j) // PANIC: comparing uncomparable type []int

// Comparison is fine if underlying type IS comparable:
var a interface{} = 42
var b interface{} = 42
fmt.Println(a == b) // true, safe
```

### Q9: What's wrong with this mutex usage?

```go
type Counter struct {
    mu    sync.Mutex
    count int
}

func (c Counter) Inc() { // VALUE RECEIVER — copies the mutex!
    c.mu.Lock()          // locks the COPY, not the original
    defer c.mu.Unlock()
    c.count++            // modifies the COPY
}

// Fix: pointer receiver
func (c *Counter) Inc() {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.count++
}

// go vet catches this: "sync.Mutex copied"
```

### Q10: Select fairness and starvation

```go
// When multiple cases in select are ready simultaneously,
// Go picks ONE pseudo-randomly.
// This means: if ch1 is ALWAYS ready, ch2 might still run (eventually).

// To prioritize one channel:
func prioritizedSelect(high, low <-chan int) {
    for {
        select {
        case v := <-high:
            process(v)
        default:
        }
        // Only if high is empty, try low:
        select {
        case v := <-high:
            process(v)
        case v := <-low:
            process(v)
        }
    }
}
```

### Q11: String vs []byte internals

```go
// string: {ptr *byte, len int} — immutable, no cap
// []byte: {ptr *byte, len int, cap int} — mutable

// String literal: in read-only data segment, shared between copies
s1 := "hello"
s2 := "hello" // may share same underlying array (compiler optimization)

// Conversion string → []byte: ALWAYS allocates (must copy for mutability)
b := []byte(s1) // new allocation

// Conversion []byte → string: allocates (to ensure immutability)
s3 := string(b) // new allocation

// Exception: compiler can optimize string(b) and []byte(s) in certain
// contexts (comparison, map lookup) to avoid allocation
if string(b) == "hello" { } // NO allocation — compiler optimizes

// For zero-copy: use unsafe (see section 13)
```

### Q12: init() function semantics

```go
// Multiple init() per file: allowed
// Multiple files with init(): run in dependency order, then file order
// init() is called after all var declarations in the package

var x = compute()  // runs before init()

func init() {
    // x is already initialized
    // Called automatically, cannot be called manually
    // Cannot be referenced (no function pointer)
}

func init() {
    // Second init in same file — also runs
}

// Order: imported packages' inits → this package's vars → this package's inits
// Circular imports: not allowed (compile error)
```

### Q13: Goroutine vs OS thread — memory

```go
// Initial goroutine stack: 2KB (on most platforms)
// Initial OS thread stack: 1MB (Linux default) to 8MB
// Goroutine stack can grow up to 1GB
// OS thread stack: fixed at creation time

// How many goroutines can you have?
// Limited by: memory (each needs ≥2KB stack + runtime overhead)
// Practical: millions on a modern server
// 1M goroutines × 2KB = ~2GB stack space (if all minimal)

// How many OS threads?
// GOMAXPROCS Ps in use (default=NumCPU)
// Additional Ms for blocking syscalls
// runtime.NumGoroutine() — current goroutine count
// runtime/debug.Stack() — current goroutine's stack trace
```

### Q14: sync.Pool lifecycle — when are objects freed?

```go
// sync.Pool objects are freed at EACH GC cycle.
// There is NO guarantee of how long an object stays in the pool.
// Never store objects with finalizers in Pool.
// Never store large objects you depend on long-term.

// Use case: pools of buffers, scratch space — ok to recreate
// Anti-use: connection pools (use database/sql.DB instead)
// Anti-use: any state that must persist between calls

var pool = sync.Pool{New: func() interface{} { return make([]byte, 4096) }}

func processRequest(data []byte) {
    buf := pool.Get().([]byte)
    defer pool.Put(buf[:0]) // Reset before returning!
    
    // use buf...
}
```

### Common gotchas summary

```
1. Loop variable capture in goroutines (Go < 1.22)
2. nil interface != nil concrete pointer
3. Mutex with value receiver (copies the lock)
4. Closing channel multiple times (panic)
5. Sending on closed channel (panic)
6. defer in loop (deferred to function end, not loop iteration)
7. Named return values with defer modifications
8. Map read during write in concurrent code (panic: map write/read concurrent)
9. append may or may not create new slice (depending on capacity)
10. Type switch/assertion on nil interface panics (type assertion)
11. http.Get without context — no timeout, no cancellation
12. os.Exit bypasses defer
13. recover must be direct defer, not nested/goroutine
14. sync.WaitGroup: Add() must be called before go stmt
15. For-range copies value: modify slice elements use index, not value
```

---

## Appendix: Further Reading & Practice

### Books
- **"The Go Programming Language"** — Donovan & Kernighan (foundation)
- **"100 Go Mistakes"** — Teiva Harsanyi (exactly what interviews test)
- **"Learning Go"** — Jon Bodner (idiomatic patterns)
- **"Cloud Native Go"** — Matthew Titmus (distributed systems)

### Essential Repositories
- `golang/go` — read the runtime source: `src/runtime/`
- `uber-go/goleak` — goroutine leak detection
- `uber-go/zap` — production logger (study for interface design)
- `go-chi/chi` — minimal HTTP router (clean Go design)
- `etcd-io/etcd` — distributed KV (real-world Go)

### Tools
```bash
# Static analysis
go vet ./...
staticcheck ./...
golangci-lint run

# Security
govulncheck ./...
gosec ./...

# Performance
go test -bench=. -benchmem -cpuprofile=cpu.prof
go tool pprof cpu.prof
go tool trace trace.out

# Memory layout
go build -gcflags="-m -m" 2>&1  # escape analysis
betteralign -apply ./...         # struct field alignment

# Race detector
go test -race ./...
```

### Interview Mental Model

```
When answering Go questions, structure as:

1. What: The simplest correct answer
2. Why: The design reasoning / tradeoff
3. How: Implementation details (memory layout, algorithm)
4. Gotchas: What goes wrong if misused
5. Production: What you'd actually do in a real system

The interviewer is testing your mental model, not your ability
to recite API signatures. Always tie theory to real-world impact.
```

---
*Guide version: Go 1.22 — Last reviewed: 2025*