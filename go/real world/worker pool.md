# Worker Pool in Go — Complete In-Depth Guide
## Basic → Intermediate → Advanced

---

## Table of Contents

1. [Mental Model: Why Worker Pools Exist](#1-mental-model-why-worker-pools-exist)
2. [Go Concurrency Primitives — The Foundation](#2-go-concurrency-primitives--the-foundation)
3. [Basic Worker Pool](#3-basic-worker-pool)
4. [Intermediate Worker Pool](#4-intermediate-worker-pool)
5. [Advanced Worker Pool](#5-advanced-worker-pool)
6. [Patterns, Pitfalls, and Production Wisdom](#6-patterns-pitfalls-and-production-wisdom)

---

## 1. Mental Model: Why Worker Pools Exist

### The Core Problem

When you have many units of work, there are two naive strategies:

**Strategy A — Sequential Processing**
```
Job1 → done → Job2 → done → Job3 → done → Job4 → done
─────────────────────────────────────────────────────▶ time
```
Only one job runs at a time. CPU sits idle waiting for I/O. Throughput is terrible.

**Strategy B — Unlimited Goroutines (Goroutine-per-job)**
```
Job1 ──────────────▶
Job2 ──────────────▶
Job3 ──────────────▶
...
Job100000 ─────────▶   ← 100,000 goroutines, each ~2-8KB stack = up to 800MB RAM
```
You spawn one goroutine per job. Works fine for tens. Destroys the system at thousands. Each goroutine costs memory. Context-switching overhead grows. You get OOM kills, scheduler thrashing, or thundering herd effects on downstream services.

**The Worker Pool Solution**

A fixed set of goroutines (workers) share a channel of incoming work. You get:
- Bounded concurrency (predictable resource consumption)
- Natural backpressure (channel fills up → producer slows down)
- High throughput (workers stay busy, no startup cost per job)

```
                        ┌─────────────────────────────────────┐
                        │            WORKER POOL               │
                        │                                      │
Producer ──jobs──▶ [job queue channel]──▶ Worker 1            │
                        │            └──▶ Worker 2            │
                        │            └──▶ Worker 3            │
                        │            └──▶ Worker N            │
                        │                    │                 │
                        └────────────────────┼─────────────────┘
                                             │
                                             ▼
                                        Results / Side Effects
```

### The Mental Model: A Factory Floor

Think of a worker pool as a factory floor:

```
 LOADING DOCK          CONVEYOR BELT          WORKSTATIONS         SHIPPING
 (Producer)            (job channel)          (Workers)            (Results)

 ┌──────────┐         ┌──────────────┐       ┌──────────┐
 │ Foreman  │──box──▶│ [b][b][b][b] │──▶    │Worker  1 │──▶ result
 │ (your    │         │              │       ├──────────┤
 │  code)   │         │ capacity = N │──▶    │Worker  2 │──▶ result
 └──────────┘         │              │       ├──────────┤
                       │ if full,     │──▶    │Worker  3 │──▶ result
                       │ foreman      │       └──────────┘
                       │ waits        │
                       └──────────────┘
```

Key insight: **The channel IS the queue. The buffer size IS the queue depth. The workers ARE the concurrency limit.**

---

## 2. Go Concurrency Primitives — The Foundation

Before we build anything, you must have a deep mental model of the primitives. Shortcuts here create bugs later.

### 2.1 Goroutines

A goroutine is a lightweight, cooperatively-scheduled thread managed by the Go runtime. It starts with a ~2KB stack that grows as needed (up to ~1GB by default).

```go
go func() {
    // runs concurrently
}()
```

**Critical facts:**
- Goroutines are NOT OS threads. The Go scheduler (M:N scheduler) maps many goroutines (G) to fewer OS threads (M) on logical processors (P).
- A goroutine blocks on channel ops, syscalls, mutexes — the runtime transparently moves other goroutines onto free threads.
- **No goroutine has a built-in way to be killed from outside.** You must signal it via a channel or context.
- A goroutine that panics kills the entire program unless recovered.

### 2.2 Channels — Deep Dive

Channels are typed conduits for communication between goroutines. They are the primary synchronization mechanism in Go.

```
UNBUFFERED CHANNEL (capacity = 0)
─────────────────────────────────
make(chan T)

Send blocks until receiver is ready.
Receive blocks until sender is ready.
This is a synchronization point — a rendezvous.

Sender ──send──▶ [  ] ──recv──▶ Receiver
        blocks           blocks
        until            until
        recv ready       send ready
```

```
BUFFERED CHANNEL (capacity = N)
────────────────────────────────
make(chan T, N)

Send blocks ONLY when buffer is full.
Receive blocks ONLY when buffer is empty.
Decouples sender and receiver timing.

Sender ──send──▶ [item1][item2][item3] ──recv──▶ Receiver
        blocks                                    blocks
        only if full                             only if empty
```

**Channel directions in function signatures:**

```go
func producer(out chan<- Job) { ... }  // send-only
func consumer(in <-chan Job)  { ... }  // receive-only
func pipe(in <-chan Job, out chan<- Result) { ... }
```

This is enforced by the compiler — a powerful correctness tool.

**Closing channels — the signal protocol:**

```go
close(ch)   // signal: no more values will be sent

// Receiver can detect close:
v, ok := <-ch   // ok = false when closed and empty
// OR
for v := range ch { ... }  // loop exits when closed and empty
```

Rules:
- Only the **sender** should close a channel.
- Closing a nil channel panics.
- Closing an already-closed channel panics.
- Sending to a closed channel panics.
- Receiving from a closed channel returns zero value immediately.

### 2.3 sync.WaitGroup — Lifecycle Tracking

`sync.WaitGroup` tracks how many goroutines are still running. Essential for knowing when all workers are done.

```go
var wg sync.WaitGroup

wg.Add(1)      // before launching goroutine
go func() {
    defer wg.Done()  // when goroutine exits
    // work
}()

wg.Wait()  // blocks until counter reaches 0
```

**The invariant:** `Add` must happen before `go`, never inside the goroutine. Otherwise you have a race condition where `Wait` might return before `Add` is even called.

```
WRONG:                           CORRECT:
go func() {                      wg.Add(1)
    wg.Add(1)  ← RACE!          go func() {
    defer wg.Done()                  defer wg.Done()
    // work                          // work
}()                              }()
wg.Wait()  ← might return early wg.Wait()
```

### 2.4 sync.Mutex and sync.RWMutex

Protects shared state from concurrent access.

```go
var mu sync.Mutex
var counter int

// Writer
mu.Lock()
counter++
mu.Unlock()

// With RWMutex, many readers can hold simultaneously
var rmu sync.RWMutex
rmu.RLock()   // many goroutines can RLock simultaneously
val := counter
rmu.RUnlock()
```

**The pattern:** Always `defer mu.Unlock()` immediately after `mu.Lock()` to ensure unlock even on panic.

### 2.5 context.Context — Cancellation and Deadlines

`context.Context` is the standard mechanism for propagating cancellation, deadlines, and request-scoped values through a call graph.

```
context.Background()
    │
    ├── context.WithCancel(parent)     → returns ctx, cancelFunc
    ├── context.WithTimeout(parent, d) → returns ctx, cancelFunc
    └── context.WithDeadline(parent,t) → returns ctx, cancelFunc

ctx.Done()   → channel, closed when ctx is cancelled
ctx.Err()    → context.Canceled or context.DeadlineExceeded
ctx.Value(k) → retrieve values (use sparingly)
```

Workers check `ctx.Done()` to know when to stop:

```go
select {
case job := <-jobCh:
    process(job)
case <-ctx.Done():
    return  // graceful shutdown
}
```

### 2.6 sync/atomic — Lock-Free Counters

For simple counters shared across goroutines, `sync/atomic` operations are faster than mutexes:

```go
var count int64
atomic.AddInt64(&count, 1)
atomic.LoadInt64(&count)
atomic.StoreInt64(&count, 0)
```

These are implemented as CPU-level atomic instructions — no lock, no scheduler involvement.

---

## 3. Basic Worker Pool

### 3.1 Concept and Structure

The simplest worker pool has three actors:

```
┌─────────────────────────────────────────────────────────────┐
│                      BASIC WORKER POOL                       │
│                                                              │
│  ┌──────────┐    jobs channel     ┌──────────────────────┐  │
│  │          │  ──────────────▶    │ Worker 1             │  │
│  │ Producer │    (buffered)       │ Worker 2             │  │
│  │          │  ──────────────▶    │ Worker 3             │  │
│  │ (sends   │                     │ ...                  │  │
│  │  jobs,   │  results channel    │ Worker N             │  │
│  │  closes) │  ◀──────────────    └──────────────────────┘  │
│  └──────────┘    (buffered)                                  │
│                                                              │
│  main goroutine:                                             │
│    - launches workers                                        │
│    - sends all jobs                                          │
│    - closes jobs channel                                     │
│    - collects results                                        │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Complete Basic Implementation

```go
package main

import (
	"fmt"
	"math/rand"
	"time"
)

// Job represents a unit of work.
// In a real system this might be an HTTP request, a file path, a DB query, etc.
type Job struct {
	ID    int
	Input int
}

// Result holds the outcome of processing a Job.
type Result struct {
	JobID  int
	Output int
}

// worker is a function run as a goroutine.
// It reads jobs from the jobs channel, processes each one,
// and sends the result to the results channel.
// It exits naturally when the jobs channel is closed (range exits).
func worker(id int, jobs <-chan Job, results chan<- Result) {
	for job := range jobs {
		// Simulate work with a random sleep
		duration := time.Duration(rand.Intn(100)) * time.Millisecond
		time.Sleep(duration)

		result := Result{
			JobID:  job.ID,
			Output: job.Input * job.Input, // our "computation": square the number
		}

		fmt.Printf("Worker %d processed job %d (input=%d, output=%d)\n",
			id, job.ID, job.Input, result.Output)

		results <- result
	}
	fmt.Printf("Worker %d exiting\n", id)
}

func main() {
	const numWorkers = 3
	const numJobs = 10

	// Buffered channels. Buffer size = numJobs lets producer fill queue
	// without blocking even if no workers have started reading yet.
	jobs := make(chan Job, numJobs)
	results := make(chan Result, numJobs)

	// Launch workers. They immediately block on `range jobs`,
	// waiting for work to arrive.
	for i := 1; i <= numWorkers; i++ {
		go worker(i, jobs, results)
	}

	// Producer: send all jobs and close the channel.
	// Closing signals workers that no more jobs are coming.
	// Workers' `range jobs` loops will exit after draining the channel.
	for j := 1; j <= numJobs; j++ {
		jobs <- Job{ID: j, Input: j}
	}
	close(jobs)

	// Collect exactly numJobs results.
	// This is the simplest termination strategy: we know the exact count.
	for r := 0; r < numJobs; r++ {
		result := <-results
		fmt.Printf("Collected result: job=%d output=%d\n", result.JobID, result.Output)
	}

	fmt.Println("All jobs completed.")
}
```

### 3.3 What Happens Step by Step (Execution Trace)

```
main()
 │
 ├─ make(chan Job, 10)       → jobs channel created
 ├─ make(chan Result, 10)    → results channel created
 │
 ├─ go worker(1, jobs, results)  → Worker 1 starts, blocks on range
 ├─ go worker(2, jobs, results)  → Worker 2 starts, blocks on range
 ├─ go worker(3, jobs, results)  → Worker 3 starts, blocks on range
 │
 ├─ jobs <- Job{1, 1}    ─▶ buffered, no block (capacity = 10)
 ├─ jobs <- Job{2, 2}    ─▶ buffered
 ├─ ...
 ├─ jobs <- Job{10, 10}  ─▶ buffered
 ├─ close(jobs)          ─▶ signals end of work
 │
 │    Meanwhile, workers race to pick up jobs:
 │    Worker 1: picks Job{1}, processes, sends Result{1, 1}
 │    Worker 2: picks Job{2}, processes, sends Result{2, 4}
 │    Worker 3: picks Job{3}, processes, sends Result{3, 9}
 │    Worker 1: finishes, picks Job{4}, ...
 │    ...
 │    When jobs channel is empty + closed, all workers exit range loop
 │
 ├─ <-results  → collects result (order may vary!)
 ├─ ...  (10 times total)
 │
 └─ "All jobs completed."
```

### 3.4 Channel Buffer Sizing — The Trade-off

```
jobs := make(chan Job, bufferSize)

bufferSize = 0  (unbuffered)
  ─ Producer blocks on each send until a worker picks it up
  ─ No queue; zero memory overhead
  ─ Producer and worker must "meet" — tighter coupling
  ─ Good when you want maximum backpressure

bufferSize = numJobs (full buffer)
  ─ Producer can send all jobs without blocking
  ─ Uses memory upfront
  ─ Producer finishes fast, then waits for results
  ─ Good when producer is fast and you have bounded total jobs

bufferSize = numWorkers (common heuristic)
  ─ At most numWorkers pending jobs in queue
  ─ Producer can stay ahead of workers slightly
  ─ Good balance for streaming/infinite job sources

bufferSize → ∞  (unbounded)
  ─ DANGEROUS: memory grows without bound if workers are slower than producer
  ─ Never do this without explicit flow control
```

### 3.5 Termination Strategies

This is the most important concept in basic pools. How do workers know when to stop?

**Strategy 1: Close the jobs channel (cleanest)**
```go
// Producer closes after sending all jobs
close(jobs)

// Worker uses range — exits automatically when channel drained + closed
for job := range jobs {
    process(job)
}
```

**Strategy 2: Sentinel value (poison pill)**
```go
// Define a zero value or special value as "stop"
// Useful when you can't close the channel (multiple producers)
type Job struct {
    Stop bool
    Data int
}

// Worker checks for poison pill
for {
    job := <-jobs
    if job.Stop {
        return  // done
    }
    process(job)
}

// Producer sends N poison pills (one per worker)
for i := 0; i < numWorkers; i++ {
    jobs <- Job{Stop: true}
}
```

**Strategy 3: WaitGroup + goroutine to close results**
```go
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

// Close results when all workers done — lets collector use range
go func() {
    wg.Wait()
    close(results)
}()

for result := range results {
    handle(result)
}
```

This Strategy 3 pattern is the most composable and will be used extensively going forward.

### 3.6 Basic Pool — The Timing Diagram

```
TIME ──────────────────────────────────────────────────────────▶

main:    [send J1..J10][close jobs]──────────────────[collect 10 results]

Worker1: ──────[J1  ██████████][J4  █████][J7  ███████████]──────────
                    processing                                     exits when
Worker2: ──────[J2  ████][J5  ████████][J8  █████][J10 ████]───── jobs closed
                                                                   and empty
Worker3: ──────[J3  ███████████][J6  ███][J9  ██████████]──────────

Results ch: ──[R2][R3][R1][R5][R6][R4][R7][R8][R10][R9]──────────
                ▲
                Results arrive out of order! (depends on sleep duration)
```

**Key takeaway:** Results are NOT in order. If order matters, you must sort by job ID or use a different pattern.

---

## 4. Intermediate Worker Pool

The basic pool is correct but lacks features required for real systems:
- Error handling per job
- Graceful shutdown (timeout or signal)
- Result ordering
- Dynamic fan-out
- Job retries

### 4.1 Error Handling Per Job

Each job needs to report success or failure without crashing the worker.

```go
package main

import (
	"errors"
	"fmt"
	"math/rand"
	"sync"
	"time"
)

type Job struct {
	ID    int
	Input string
}

type Result struct {
	Job   Job
	Value string
	Err   error  // ← error is part of the result, not a panic
}

// processJob simulates work that can fail.
func processJob(job Job) Result {
	time.Sleep(time.Duration(rand.Intn(50)) * time.Millisecond)

	// Simulate 20% failure rate
	if rand.Float32() < 0.2 {
		return Result{
			Job: job,
			Err: fmt.Errorf("job %d failed: invalid input %q", job.ID, job.Input),
		}
	}

	return Result{
		Job:   job,
		Value: fmt.Sprintf("processed(%s)", job.Input),
	}
}

// worker processes jobs and sends Results (including errors).
// Errors never crash the worker — they're reported in the Result.
func worker(id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()

	for job := range jobs {
		// Recover from any panic in processJob — wrap in a closure
		func() {
			defer func() {
				if r := recover(); r != nil {
					results <- Result{
						Job: job,
						Err: fmt.Errorf("worker %d recovered from panic: %v", id, r),
					}
				}
			}()
			results <- processJob(job)
		}()
	}
}

func RunPool(jobs []Job, numWorkers int) []Result {
	jobCh := make(chan Job, len(jobs))
	resultCh := make(chan Result, len(jobs))

	var wg sync.WaitGroup
	for i := 1; i <= numWorkers; i++ {
		wg.Add(1)
		go worker(i, jobCh, resultCh, &wg)
	}

	for _, job := range jobs {
		jobCh <- job
	}
	close(jobCh)

	// Close results when all workers exit
	go func() {
		wg.Wait()
		close(resultCh)
	}()

	var results []Result
	for r := range resultCh {
		results = append(results, r)
	}
	return results
}

func main() {
	jobs := make([]Job, 20)
	for i := range jobs {
		jobs[i] = Job{ID: i + 1, Input: fmt.Sprintf("item-%d", i+1)}
	}

	results := RunPool(jobs, 4)

	var errs, ok int
	for _, r := range results {
		if r.Err != nil {
			fmt.Printf("ERROR: %v\n", r.Err)
			errs++
		} else {
			fmt.Printf("OK: job=%d value=%s\n", r.Job.ID, r.Value)
			ok++
		}
	}
	fmt.Printf("\nCompleted: %d ok, %d errors\n", ok, errs)
}
```

### 4.2 Graceful Shutdown with context.Context

A production pool must be cancellable. The standard Go idiom is `context.Context`.

```
SHUTDOWN SCENARIOS:
─────────────────────────────────────────────────────────────────

1. Normal completion: all jobs done, workers exit via range.

2. Timeout:
   ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
   → ctx.Done() fires after 30s
   → Workers detect and stop processing new jobs
   → In-flight jobs finish (or check ctx mid-work)

3. User cancellation:
   ctx, cancel := context.WithCancel(ctx)
   → Caller calls cancel() (e.g., on SIGINT)
   → Same propagation as timeout

4. Upstream cancellation:
   → Parent context cancelled (e.g., HTTP request context)
   → Automatically cancels child contexts
```

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

type Job struct{ ID int }
type Result struct {
	JobID int
	Err   error
}

// worker checks context on each iteration.
// If context is cancelled, it stops picking up new jobs.
// The current in-flight job can also check ctx if it's long-running.
func worker(ctx context.Context, id int, jobs <-chan Job, results chan<- Result, wg *sync.WaitGroup) {
	defer wg.Done()

	for {
		select {
		// Priority: check context first (optional; Go select is random)
		// Use a double-select pattern to give ctx.Done priority:
		case <-ctx.Done():
			fmt.Printf("Worker %d: context cancelled, stopping\n", id)
			return

		case job, ok := <-jobs:
			if !ok {
				// jobs channel was closed — no more work
				fmt.Printf("Worker %d: jobs channel closed, exiting\n", id)
				return
			}
			// Check context before starting expensive work
			if ctx.Err() != nil {
				// Send a cancellation result so caller knows job was not processed
				results <- Result{JobID: job.ID, Err: ctx.Err()}
				continue
			}
			// Simulate work that also respects context
			err := doWork(ctx, job)
			results <- Result{JobID: job.ID, Err: err}
		}
	}
}

// doWork simulates long-running work that can be interrupted.
func doWork(ctx context.Context, job Job) error {
	select {
	case <-time.After(50 * time.Millisecond): // normal completion
		return nil
	case <-ctx.Done(): // cancelled mid-work
		return fmt.Errorf("job %d cancelled: %w", job.ID, ctx.Err())
	}
}

func RunPoolWithContext(ctx context.Context, numWorkers int, jobList []Job) []Result {
	jobs := make(chan Job, len(jobList))
	results := make(chan Result, len(jobList))

	var wg sync.WaitGroup
	for i := 1; i <= numWorkers; i++ {
		wg.Add(1)
		go worker(ctx, i, jobs, results, &wg)
	}

	// Producer goroutine: also respects context
	go func() {
		defer close(jobs)
		for _, job := range jobList {
			select {
			case jobs <- job:
			case <-ctx.Done():
				fmt.Println("Producer: context cancelled, stopping dispatch")
				return
			}
		}
	}()

	// Close results when all workers done
	go func() {
		wg.Wait()
		close(results)
	}()

	var out []Result
	for r := range results {
		out = append(out, r)
	}
	return out
}

func main() {
	jobs := make([]Job, 20)
	for i := range jobs {
		jobs[i] = Job{ID: i + 1}
	}

	// Cancel after 200ms — some jobs won't complete
	ctx, cancel := context.WithTimeout(context.Background(), 200*time.Millisecond)
	defer cancel()

	results := RunPoolWithContext(ctx, 4, jobs)

	var completed, cancelled int
	for _, r := range results {
		if r.Err != nil {
			fmt.Printf("Job %d: %v\n", r.JobID, r.Err)
			cancelled++
		} else {
			completed++
		}
	}
	fmt.Printf("Completed: %d, Cancelled/Errored: %d\n", completed, cancelled)
}
```

**The select priority problem:**

Go's `select` chooses randomly when multiple cases are ready. To give `ctx.Done()` strict priority over incoming jobs:

```go
// Double-select pattern for priority cancellation
select {
case <-ctx.Done():
    return
default:
}
// Only if ctx not done, wait for a job
select {
case <-ctx.Done():
    return
case job, ok := <-jobs:
    if !ok { return }
    process(job)
}
```

### 4.3 Result Ordering

The basic pool returns results in arbitrary order. For ordered results:

**Approach A: Sort by ID after collection**
```go
sort.Slice(results, func(i, j int) bool {
    return results[i].JobID < results[j].JobID
})
```
Simple, but requires all results before you can use any.

**Approach B: Pre-allocated slice by index**
```go
// Job IDs are 0..N-1
results := make([]Result, numJobs)

// Worker writes directly to the right slot
results[job.ID] = processJob(job)  // RACE CONDITION if not synchronized!

// Safe version: use sync/atomic or separate per-index channels
```

**Approach C: Ordered fan-in via indexed result channels**

```go
package main

import (
	"fmt"
	"sync"
)

type Job struct {
	Index int   // position in input slice
	Data  int
}

type Result struct {
	Index int
	Value int
}

// OrderedPool processes jobs and returns results in the SAME order as inputs.
func OrderedPool(inputs []int, numWorkers int) []int {
	numJobs := len(inputs)
	jobs := make(chan Job, numJobs)
	results := make([]Result, numJobs)   // pre-allocated indexed storage

	// Use a mutex to safely write results at their index
	var mu sync.Mutex
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for job := range jobs {
				val := job.Data * job.Data // compute
				mu.Lock()
				results[job.Index] = Result{Index: job.Index, Value: val}
				mu.Unlock()
			}
		}()
	}

	for i, data := range inputs {
		jobs <- Job{Index: i, Data: data}
	}
	close(jobs)
	wg.Wait()

	// Extract ordered values
	out := make([]int, numJobs)
	for i, r := range results {
		out[i] = r.Value
	}
	return out
}

func main() {
	inputs := []int{5, 3, 8, 1, 9, 2, 7, 4, 6}
	outputs := OrderedPool(inputs, 3)
	fmt.Println("Input: ", inputs)
	fmt.Println("Output:", outputs) // each output[i] = inputs[i]^2, in order
}
```

### 4.4 Fan-Out / Fan-In Pipeline

A more powerful pattern connects multiple stages in a pipeline. Each stage is a pool. Data flows through channels.

```
                    PIPELINE ARCHITECTURE
────────────────────────────────────────────────────────────────

Stage 1: Read      Stage 2: Transform    Stage 3: Write
─────────────      ─────────────────     ──────────────
Reader goroutine   Worker pool           Writer goroutine
    │                   │                     │
    │    raw chan        │    processed chan    │
    └──────────────▶ [████████] ──────────▶ [████████]──▶ DB/File
                    Worker 1
                    Worker 2
                    Worker 3

Each arrow (─▶) is a Go channel.
Each stage is decoupled — runs at its own pace.
Backpressure flows backwards automatically via channel blocking.
```

```go
package main

import (
	"fmt"
	"strings"
)

// Stage 1: Generate raw items (simulates reading from a source)
func generate(items []string) <-chan string {
	out := make(chan string)
	go func() {
		defer close(out)
		for _, item := range items {
			out <- item
		}
	}()
	return out
}

// Stage 2: Transform with a worker pool. Returns a single merged output channel.
// This is the fan-out/fan-in pattern.
func transform(in <-chan string, numWorkers int) <-chan string {
	out := make(chan string, numWorkers)
	var wg sync.WaitGroup

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for item := range in {
				// Transform: uppercase and add suffix
				out <- strings.ToUpper(item) + "_processed"
			}
		}()
	}

	// Close out when all workers done
	go func() {
		wg.Wait()
		close(out)
	}()

	return out
}

// Stage 3: Sink — consumes results
func sink(in <-chan string) []string {
	var results []string
	for item := range in {
		results = append(results, item)
	}
	return results
}

func main() {
	import "sync" // (in real code, this is at top)
	
	items := []string{"alpha", "beta", "gamma", "delta", "epsilon", "zeta"}

	// Wire the pipeline
	stage1 := generate(items)
	stage2 := transform(stage1, 3)
	results := sink(stage2)

	fmt.Println("Results:", results)
}
```

```
Pipeline Channel Flow:
────────────────────────────────────────────────────────────────

generate()         stage1 chan        transform()       stage2 chan       sink()
──────────        ────────────       ────────────      ────────────      ──────
"alpha"    ──▶   ["alpha"]  ──▶     Worker1: "ALPHA_processed" ──▶ ["ALPHA_processed"] ──▶ results
"beta"     ──▶   ["beta"]   ──▶     Worker2: "BETA_processed"  ──▶
"gamma"    ──▶   ["gamma"]  ──▶     Worker3: "GAMMA_processed" ──▶
"delta"    ──▶   ["delta"]  ──▶     Worker1: ...
...
close()    ──▶   (closed)   ──▶     workers see closed, exit ──▶ (closed) ──▶ range exits
```

### 4.5 Job Retry Logic

Workers that fail a job should retry before reporting failure:

```go
package main

import (
	"fmt"
	"math/rand"
	"time"
)

type Job struct {
	ID      int
	Payload string
	Attempt int   // current attempt (0-indexed)
}

type Result struct {
	JobID   int
	Value   string
	Err     error
	Retries int
}

const maxRetries = 3

// workerWithRetry retries failed jobs up to maxRetries times.
// Uses exponential backoff between retries.
func workerWithRetry(id int, jobs <-chan Job, results chan<- Result) {
	for job := range jobs {
		var result Result
		result.JobID = job.ID

		backoff := 10 * time.Millisecond

		for attempt := 0; attempt <= maxRetries; attempt++ {
			result.Retries = attempt

			// Simulate flaky operation (50% failure rate for demo)
			if rand.Float32() < 0.5 {
				result.Err = fmt.Errorf("transient error on attempt %d", attempt)
				time.Sleep(backoff)
				backoff *= 2  // exponential backoff: 10ms, 20ms, 40ms, 80ms
				continue
			}

			// Success
			result.Value = fmt.Sprintf("success on attempt %d", attempt)
			result.Err = nil
			break
		}

		results <- result
	}
}
```

```
Retry with Exponential Backoff:
────────────────────────────────────────────────────────────────

Job arrives ──▶ Attempt 0 ──FAIL──▶ wait 10ms ──▶ Attempt 1 ──FAIL──▶ wait 20ms
              ──▶ Attempt 2 ──FAIL──▶ wait 40ms ──▶ Attempt 3 ──FAIL──▶ give up, return error

              OR:

Job arrives ──▶ Attempt 0 ──OK──▶ return result

              OR:

Job arrives ──▶ Attempt 0 ──FAIL──▶ wait 10ms ──▶ Attempt 1 ──OK──▶ return result
```

### 4.6 Semaphore Pattern (Alternative to Fixed Workers)

Sometimes you don't want persistent goroutines. Instead, you want to limit concurrent goroutines launched dynamically. A semaphore channel achieves this:

```go
package main

import (
	"fmt"
	"sync"
	"time"
)

// sem is a semaphore: a buffered channel used as a token bucket.
// To acquire: send to sem (blocks if full = maxConcurrency goroutines running)
// To release: receive from sem
type Semaphore chan struct{}

func NewSemaphore(maxConcurrency int) Semaphore {
	return make(Semaphore, maxConcurrency)
}

func (s Semaphore) Acquire() { s <- struct{}{} }
func (s Semaphore) Release() { <-s }

func processWithSemaphore(items []int, maxConcurrent int) {
	sem := NewSemaphore(maxConcurrent)
	var wg sync.WaitGroup

	for _, item := range items {
		sem.Acquire()   // blocks if maxConcurrent goroutines are running
		wg.Add(1)
		go func(v int) {
			defer wg.Done()
			defer sem.Release()

			time.Sleep(50 * time.Millisecond)
			fmt.Printf("Processed: %d\n", v)
		}(item)
	}

	wg.Wait()
}
```

```
Semaphore Visualization (maxConcurrent = 3):

sem channel: [●][●][●]  ← 3 tokens (slots)

Goroutine A: Acquire() ─▶ sem=[●][●][ ]  A running
Goroutine B: Acquire() ─▶ sem=[●][ ][ ]  B running
Goroutine C: Acquire() ─▶ sem=[ ][ ][ ]  C running
Goroutine D: Acquire() ─▶ BLOCKS (sem full)

A finishes: Release()  ─▶ sem=[●][ ][ ]  D unblocks
D: Acquire() ─▶ sem=[ ][ ][ ]  D running
```

**Difference from a fixed worker pool:**
- Semaphore: each job gets its own goroutine, limited by count. Good for short-lived goroutines.
- Fixed pool: reuses a fixed set of goroutines. No goroutine startup overhead per job.

---

## 5. Advanced Worker Pool

Production-grade pools need: dynamic scaling, priority queues, rate limiting, backpressure handling, metrics, and graceful drain on shutdown.

### 5.1 Architecture Overview

```
┌───────────────────────────────────────────────────────────────────────────┐
│                     ADVANCED WORKER POOL ARCHITECTURE                      │
│                                                                             │
│  External         Pool Manager                                              │
│  Callers    ┌─────────────────────────────────────────────────────────┐    │
│     │       │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │    │
│     │       │  │   Rate       │  │  Dispatcher  │  │  Scaler      │  │    │
│     ▼       │  │   Limiter    │  │              │  │  (dynamic    │  │    │
│  Submit()   │  │  (token      │  │  Priority    │  │   workers)   │  │    │
│  ─────────▶ │  │   bucket)    │  │  Queue       │  │              │  │    │
│             │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │    │
│             │         │                 │                  │          │    │
│             │         ▼                 ▼                  ▼          │    │
│             │  ┌──────────────────────────────────────────────────┐   │    │
│             │  │               Job Queue (heap/channel)           │   │    │
│             │  │  [HIGH][HIGH][MED][MED][MED][LOW][LOW]           │   │    │
│             │  └─────────────────────────┬────────────────────────┘   │    │
│             │                            │                             │    │
│             │              ┌─────────────┼─────────────┐              │    │
│             │              ▼             ▼             ▼              │    │
│             │         ┌────────┐   ┌────────┐   ┌────────┐           │    │
│             │         │Worker 1│   │Worker 2│   │Worker N│           │    │
│             │         │[busy] │   │[idle] │   │[busy] │           │    │
│             │         └───┬────┘   └────────┘   └───┬────┘           │    │
│             │             │                          │                │    │
│             └─────────────┼──────────────────────────┼────────────────┘    │
│                           │                          │                     │
│             ┌─────────────▼──────────────────────────▼────────────────┐    │
│             │                   Result Collector                        │    │
│             │  Metrics: processed/s, errors, latency p50/p95/p99       │    │
│             └─────────────────────────────────────────────────────────-┘    │
└───────────────────────────────────────────────────────────────────────────--┘
```

### 5.2 Priority Queue Worker Pool

Jobs with different urgency levels. High-priority jobs jump the queue.

```go
package main

import (
	"container/heap"
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// Priority levels
const (
	PriorityHigh   = 3
	PriorityMedium = 2
	PriorityLow    = 1
)

// Job represents work with a priority.
type Job struct {
	ID       int
	Priority int
	Payload  interface{}
	index    int // maintained by heap.Interface
}

// JobQueue implements heap.Interface for a max-priority queue.
// The job with the HIGHEST Priority value is dequeued first.
type JobQueue []*Job

func (jq JobQueue) Len() int { return len(jq) }

// Less: higher priority = "less" in heap terms (max-heap via negation)
func (jq JobQueue) Less(i, j int) bool {
	return jq[i].Priority > jq[j].Priority
}
func (jq JobQueue) Swap(i, j int) {
	jq[i], jq[j] = jq[j], jq[i]
	jq[i].index = i
	jq[j].index = j
}
func (jq *JobQueue) Push(x interface{}) {
	n := len(*jq)
	job := x.(*Job)
	job.index = n
	*jq = append(*jq, job)
}
func (jq *JobQueue) Pop() interface{} {
	old := *jq
	n := len(old)
	job := old[n-1]
	old[n-1] = nil
	job.index = -1
	*jq = old[:n-1]
	return job
}

// PriorityPool is a worker pool with a priority job queue.
type PriorityPool struct {
	mu       sync.Mutex
	queue    JobQueue
	cond     *sync.Cond     // signals workers when jobs arrive
	workers  int
	shutdown bool
	wg       sync.WaitGroup
	results  chan Result
}

type Result struct {
	JobID int
	Value interface{}
	Err   error
}

// NewPriorityPool creates and starts a pool with numWorkers workers.
func NewPriorityPool(numWorkers int) *PriorityPool {
	p := &PriorityPool{
		results: make(chan Result, 1000),
	}
	p.cond = sync.NewCond(&p.mu)
	heap.Init(&p.queue)

	for i := 0; i < numWorkers; i++ {
		p.wg.Add(1)
		go p.workerLoop(i)
	}
	return p
}

// Submit adds a job to the priority queue.
// Returns immediately; job will be processed when a worker is free.
func (p *PriorityPool) Submit(job *Job) {
	p.mu.Lock()
	defer p.mu.Unlock()

	if p.shutdown {
		p.results <- Result{JobID: job.ID, Err: fmt.Errorf("pool is shut down")}
		return
	}

	heap.Push(&p.queue, job)
	p.cond.Signal() // wake one sleeping worker
}

// workerLoop is the goroutine body for each worker.
// Workers sleep (on cond.Wait) when no jobs available.
func (p *PriorityPool) workerLoop(id int) {
	defer p.wg.Done()

	for {
		p.mu.Lock()

		// Wait until there's a job OR shutdown
		for p.queue.Len() == 0 && !p.shutdown {
			p.cond.Wait() // releases lock, sleeps, re-acquires on wakeup
		}

		if p.shutdown && p.queue.Len() == 0 {
			p.mu.Unlock()
			fmt.Printf("Worker %d shutting down\n", id)
			return
		}

		// Pop the highest-priority job
		job := heap.Pop(&p.queue).(*Job)
		p.mu.Unlock()

		// Process outside lock
		result := p.process(job)
		p.results <- result
	}
}

func (p *PriorityPool) process(job *Job) Result {
	time.Sleep(20 * time.Millisecond)
	return Result{
		JobID: job.ID,
		Value: fmt.Sprintf("priority=%d result", job.Priority),
	}
}

// Shutdown signals workers to drain and stop.
func (p *PriorityPool) Shutdown() {
	p.mu.Lock()
	p.shutdown = true
	p.cond.Broadcast() // wake ALL workers
	p.mu.Unlock()
	p.wg.Wait()
	close(p.results)
}

// Results returns the results channel.
func (p *PriorityPool) Results() <-chan Result {
	return p.results
}
```

```
Priority Queue State Visualization:
────────────────────────────────────────────────────────────────

After submitting: Job(LOW), Job(HIGH), Job(MED), Job(HIGH)

Heap internal state (max-heap):
                     Job(HIGH) ← root, dequeued first
                    /          \
             Job(HIGH)        Job(MED)
             /
          Job(LOW)

Dequeue order: HIGH → HIGH → MED → LOW
```

### 5.3 Dynamic Worker Scaling (Elastic Pool)

The pool grows/shrinks based on queue depth. This mimics how auto-scaling systems work.

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ElasticPool scales workers based on queue depth.
type ElasticPool struct {
	minWorkers    int
	maxWorkers    int
	scaleUpAt     int           // queue depth that triggers scale-up
	scaleDownAt   int           // idle seconds before scale-down
	activeWorkers int64         // atomic
	jobs          chan Job
	quit          chan struct{}
	workerQuits   chan chan struct{}
	wg            sync.WaitGroup
	mu            sync.Mutex
	workerCancels []context.CancelFunc
}

type Job struct {
	ID int
}

func NewElasticPool(min, max, scaleUpAt, scaleDownAt int) *ElasticPool {
	p := &ElasticPool{
		minWorkers:  min,
		maxWorkers:  max,
		scaleUpAt:   scaleUpAt,
		scaleDownAt: scaleDownAt,
		jobs:        make(chan Job, 1000),
		quit:        make(chan struct{}),
	}
	return p
}

func (p *ElasticPool) Start(ctx context.Context) {
	// Start minimum workers
	for i := 0; i < p.minWorkers; i++ {
		p.addWorker(ctx)
	}

	// Scaler goroutine: monitors queue and adjusts workers
	go p.scaler(ctx)
}

func (p *ElasticPool) addWorker(ctx context.Context) {
	workerCtx, cancel := context.WithCancel(ctx)
	p.mu.Lock()
	p.workerCancels = append(p.workerCancels, cancel)
	p.mu.Unlock()

	atomic.AddInt64(&p.activeWorkers, 1)
	p.wg.Add(1)

	go func() {
		defer func() {
			atomic.AddInt64(&p.activeWorkers, -1)
			p.wg.Done()
		}()

		idleTimer := time.NewTimer(time.Duration(p.scaleDownAt) * time.Second)
		defer idleTimer.Stop()

		for {
			select {
			case <-workerCtx.Done():
				fmt.Printf("Worker exiting (cancelled)\n")
				return

			case job, ok := <-p.jobs:
				if !ok {
					return
				}
				idleTimer.Reset(time.Duration(p.scaleDownAt) * time.Second)
				p.doWork(job)

			case <-idleTimer.C:
				// Too idle; only exit if above minimum
				if atomic.LoadInt64(&p.activeWorkers) > int64(p.minWorkers) {
					fmt.Printf("Worker idle too long, scaling down (active=%d)\n",
						atomic.LoadInt64(&p.activeWorkers))
					cancel()
					return
				}
				idleTimer.Reset(time.Duration(p.scaleDownAt) * time.Second)
			}
		}
	}()
}

func (p *ElasticPool) removeWorker() {
	p.mu.Lock()
	defer p.mu.Unlock()
	if len(p.workerCancels) > 0 {
		cancel := p.workerCancels[len(p.workerCancels)-1]
		p.workerCancels = p.workerCancels[:len(p.workerCancels)-1]
		cancel()
	}
}

// scaler periodically checks queue depth and adjusts worker count.
func (p *ElasticPool) scaler(ctx context.Context) {
	ticker := time.NewTicker(500 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			queueDepth := len(p.jobs)
			active := int(atomic.LoadInt64(&p.activeWorkers))

			if queueDepth > p.scaleUpAt && active < p.maxWorkers {
				fmt.Printf("Scaler: queue depth=%d > %d, scaling up (active=%d)\n",
					queueDepth, p.scaleUpAt, active)
				p.addWorker(ctx)
			}

			fmt.Printf("Scaler: queue=%d, active workers=%d\n", queueDepth, active)
		}
	}
}

func (p *ElasticPool) Submit(job Job) {
	p.jobs <- job
}

func (p *ElasticPool) doWork(job Job) {
	time.Sleep(100 * time.Millisecond)
	fmt.Printf("Processed job %d\n", job.ID)
}

func (p *ElasticPool) Shutdown() {
	close(p.jobs)
	p.wg.Wait()
}
```

```
Dynamic Scaling Diagram:
────────────────────────────────────────────────────────────────

Time ──────────────────────────────────────────────────────────▶

Queue depth:    2   5   12  20  18  10  5   2   1   0
               ─────────────────────────────────────────────────
Active workers: 2   2   4   6   6   5   3   2   2   2
                        ▲               ▲
                    scale-up        scale-down
                   (queue > 10)   (workers idle)

min=2, max=6, scaleUpAt=10

Workers:
W1: ████████████████████████████████████████████  (permanent)
W2: ████████████████████████████████████████████  (permanent)
W3:         ██████████████████████████            (spawned, then idle-killed)
W4:         ████████████████████████              (spawned, then idle-killed)
W5:              █████████████████                (spawned, then idle-killed)
W6:              ████████████████                 (spawned, then idle-killed)
```

### 5.4 Rate-Limited Worker Pool (Token Bucket)

Control how fast jobs are dispatched regardless of worker availability.

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// TokenBucket implements a simple rate limiter.
// It refills tokens at a constant rate.
// Each job consumes one token before proceeding.
type TokenBucket struct {
	tokens   float64
	capacity float64
	rate     float64    // tokens per second
	lastFill time.Time
	mu       sync.Mutex
}

func NewTokenBucket(capacity, ratePerSec float64) *TokenBucket {
	return &TokenBucket{
		tokens:   capacity,
		capacity: capacity,
		rate:     ratePerSec,
		lastFill: time.Now(),
	}
}

// Wait blocks until a token is available.
func (tb *TokenBucket) Wait(ctx context.Context) error {
	for {
		tb.mu.Lock()
		// Refill tokens based on elapsed time
		now := time.Now()
		elapsed := now.Sub(tb.lastFill).Seconds()
		tb.tokens = min(tb.capacity, tb.tokens+elapsed*tb.rate)
		tb.lastFill = now

		if tb.tokens >= 1.0 {
			tb.tokens--
			tb.mu.Unlock()
			return nil
		}

		// Calculate wait time for next token
		waitFor := time.Duration((1.0 - tb.tokens) / tb.rate * float64(time.Second))
		tb.mu.Unlock()

		select {
		case <-ctx.Done():
			return ctx.Err()
		case <-time.After(waitFor):
			// try again
		}
	}
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

// RateLimitedPool wraps a basic pool with a rate limiter on job dispatch.
type RateLimitedPool struct {
	jobs    chan Job
	results chan Result
	limiter *TokenBucket
	wg      sync.WaitGroup
}

type Job struct{ ID int }
type Result struct {
	JobID int
	Err   error
}

func NewRateLimitedPool(numWorkers int, ratePerSec float64) *RateLimitedPool {
	p := &RateLimitedPool{
		jobs:    make(chan Job, 100),
		results: make(chan Result, 100),
		limiter: NewTokenBucket(ratePerSec, ratePerSec),
	}
	for i := 0; i < numWorkers; i++ {
		p.wg.Add(1)
		go func() {
			defer p.wg.Done()
			for job := range p.jobs {
				time.Sleep(10 * time.Millisecond)
				p.results <- Result{JobID: job.ID}
			}
		}()
	}
	go func() {
		p.wg.Wait()
		close(p.results)
	}()
	return p
}

// Submit respects the rate limit before queuing the job.
func (p *RateLimitedPool) Submit(ctx context.Context, job Job) error {
	if err := p.limiter.Wait(ctx); err != nil {
		return fmt.Errorf("rate limiter: %w", err)
	}
	select {
	case p.jobs <- job:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}
```

```
Token Bucket Rate Limiter Visualization:
────────────────────────────────────────────────────────────────

capacity=5 tokens, rate=2 tokens/second

t=0s:   [●][●][●][●][●]  = 5 tokens  (full)
        Submit A: take 1 → [●][●][●][●][ ]
        Submit B: take 1 → [●][●][●][ ][ ]
        Submit C: take 1 → [●][●][ ][ ][ ]
        Submit D: take 1 → [●][ ][ ][ ][ ]
        Submit E: take 1 → [ ][ ][ ][ ][ ]
        Submit F: wait... (0 tokens)

t=0.5s: refill 1 token  → [●][ ][ ][ ][ ]
        Submit F: take 1 → [ ][ ][ ][ ][ ]

t=1.0s: refill 1 token  → [●][ ][ ][ ][ ]
        Submit G: take 1 → [ ][ ][ ][ ][ ]

Rate: exactly 2 jobs/sec after initial burst of 5
```

### 5.5 Backpressure and Bounded Queues

What happens when workers can't keep up with the producer? You need a policy.

```go
package main

import (
	"context"
	"errors"
	"fmt"
	"time"
)

var ErrPoolFull = errors.New("pool queue is full")

type Job struct{ ID int }
type Result struct {
	JobID int
	Err   error
}

// BackpressurePool has three submission strategies.
type BackpressurePool struct {
	jobs    chan Job
	results chan Result
}

func NewBackpressurePool(queueSize, numWorkers int) *BackpressurePool {
	p := &BackpressurePool{
		jobs:    make(chan Job, queueSize),
		results: make(chan Result, queueSize),
	}
	for i := 0; i < numWorkers; i++ {
		go func() {
			for job := range p.jobs {
				time.Sleep(50 * time.Millisecond)
				p.results <- Result{JobID: job.ID}
			}
		}()
	}
	return p
}

// Strategy 1: Block — caller waits until space available.
// Good for: pipelines where you want end-to-end backpressure.
func (p *BackpressurePool) SubmitBlocking(ctx context.Context, job Job) error {
	select {
	case p.jobs <- job:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

// Strategy 2: Drop — if queue is full, drop the job immediately.
// Good for: metrics, logging, non-critical side effects.
func (p *BackpressurePool) SubmitOrDrop(job Job) (dropped bool) {
	select {
	case p.jobs <- job:
		return false
	default:
		// non-blocking — if channel is full, the default case runs
		fmt.Printf("Job %d dropped (queue full)\n", job.ID)
		return true
	}
}

// Strategy 3: Timeout — wait up to a deadline, then return error.
// Good for: SLAs where you'd rather fail fast than queue indefinitely.
func (p *BackpressurePool) SubmitWithTimeout(job Job, timeout time.Duration) error {
	select {
	case p.jobs <- job:
		return nil
	case <-time.After(timeout):
		return fmt.Errorf("%w: job %d timed out after %v", ErrPoolFull, job.ID, timeout)
	}
}
```

```
Backpressure Flow Diagram:
────────────────────────────────────────────────────────────────

Producer rate:  ██████████████████████ (fast)
Queue:         [J1][J2][J3][J4][J5]   ← full (capacity=5)
Worker rate:   ██████  ██████  ██████  (slow)

When queue is full, what happens to J6?

BLOCK:    Producer ──J6──▶ [WAIT..........] ──▶ slot opens ──▶ [J6 queued]
          Backpressure propagates upstream. Producer naturally slows.

DROP:     Producer ──J6──▶ [FULL → DISCARD]
          Job lost. Counter incremented. Downstream protected.

TIMEOUT:  Producer ──J6──▶ [WAIT 100ms] ──▶ timeout ──▶ ErrPoolFull
          Caller can retry or log. Fast-fail SLA maintained.
```

### 5.6 Metrics and Observability

A production pool exposes metrics so you can monitor it:

```go
package main

import (
	"context"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// PoolMetrics holds atomic counters — safe to read from any goroutine.
type PoolMetrics struct {
	Submitted  int64         // total jobs submitted
	Completed  int64         // total jobs completed successfully
	Failed     int64         // total jobs that returned error
	Dropped    int64         // jobs dropped due to full queue
	InFlight   int64         // currently processing
	TotalTime  int64         // nanoseconds of total processing time (for avg)
	QueueDepth int64         // snapshot of current queue depth
}

func (m *PoolMetrics) Snapshot() PoolMetrics {
	return PoolMetrics{
		Submitted:  atomic.LoadInt64(&m.Submitted),
		Completed:  atomic.LoadInt64(&m.Completed),
		Failed:     atomic.LoadInt64(&m.Failed),
		Dropped:    atomic.LoadInt64(&m.Dropped),
		InFlight:   atomic.LoadInt64(&m.InFlight),
		TotalTime:  atomic.LoadInt64(&m.TotalTime),
		QueueDepth: atomic.LoadInt64(&m.QueueDepth),
	}
}

func (m *PoolMetrics) AvgLatencyMs() float64 {
	completed := atomic.LoadInt64(&m.Completed)
	if completed == 0 {
		return 0
	}
	totalNs := atomic.LoadInt64(&m.TotalTime)
	return float64(totalNs) / float64(completed) / 1e6
}

// InstrumentedPool wraps any pool to add metrics.
type InstrumentedPool struct {
	jobs    chan InstrumentedJob
	metrics PoolMetrics
	wg      sync.WaitGroup
}

type InstrumentedJob struct {
	ID      int
	payload interface{}
	enqueued time.Time
}

func NewInstrumentedPool(numWorkers, queueSize int) *InstrumentedPool {
	p := &InstrumentedPool{
		jobs: make(chan InstrumentedJob, queueSize),
	}

	for i := 0; i < numWorkers; i++ {
		p.wg.Add(1)
		go func(workerID int) {
			defer p.wg.Done()
			for job := range p.jobs {
				atomic.AddInt64(&p.metrics.QueueDepth, -1)
				atomic.AddInt64(&p.metrics.InFlight, 1)

				start := time.Now()
				err := p.doWork(job)
				elapsed := time.Since(start)

				atomic.AddInt64(&p.metrics.InFlight, -1)
				atomic.AddInt64(&p.metrics.TotalTime, int64(elapsed))

				if err != nil {
					atomic.AddInt64(&p.metrics.Failed, 1)
				} else {
					atomic.AddInt64(&p.metrics.Completed, 1)
				}
			}
		}(i)
	}
	return p
}

func (p *InstrumentedPool) doWork(job InstrumentedJob) error {
	time.Sleep(30 * time.Millisecond)
	return nil
}

func (p *InstrumentedPool) Submit(ctx context.Context, id int, payload interface{}) error {
	job := InstrumentedJob{ID: id, payload: payload, enqueued: time.Now()}
	select {
	case p.jobs <- job:
		atomic.AddInt64(&p.metrics.Submitted, 1)
		atomic.AddInt64(&p.metrics.QueueDepth, 1)
		return nil
	default:
		atomic.AddInt64(&p.metrics.Dropped, 1)
		return fmt.Errorf("queue full, job %d dropped", id)
	}
}

// MetricsLoop prints metrics periodically — in prod, export to Prometheus/Datadog.
func (p *InstrumentedPool) MetricsLoop(ctx context.Context, interval time.Duration) {
	ticker := time.NewTicker(interval)
	defer ticker.Stop()
	for {
		select {
		case <-ctx.Done():
			return
		case <-ticker.C:
			s := p.metrics.Snapshot()
			fmt.Printf("[METRICS] submitted=%d completed=%d failed=%d dropped=%d "+
				"inflight=%d queue=%d avg_latency=%.1fms\n",
				s.Submitted, s.Completed, s.Failed, s.Dropped,
				s.InFlight, s.QueueDepth, p.metrics.AvgLatencyMs())
		}
	}
}

func (p *InstrumentedPool) Shutdown() {
	close(p.jobs)
	p.wg.Wait()
}
```

### 5.7 Complete Production-Grade Pool

Now we combine everything into a single, reusable, production-ready implementation.

```go
package workerpool

import (
	"context"
	"errors"
	"fmt"
	"sync"
	"sync/atomic"
	"time"
)

// ─────────────────────────────────────────────────────────────
// Types
// ─────────────────────────────────────────────────────────────

// Task is the unit of work. Users implement this interface.
type Task interface {
	Execute(ctx context.Context) (interface{}, error)
}

// TaskResult holds the outcome of a Task.Execute call.
type TaskResult struct {
	Task   Task
	Value  interface{}
	Err    error
	Queued time.Time
	Start  time.Time
	End    time.Time
}

// Latency returns the processing duration.
func (r TaskResult) Latency() time.Duration { return r.End.Sub(r.Start) }

// QueueWait returns how long the task waited in the queue before a worker picked it up.
func (r TaskResult) QueueWait() time.Duration { return r.Start.Sub(r.Queued) }

// Config holds all pool parameters.
type Config struct {
	MinWorkers     int
	MaxWorkers     int
	QueueSize      int
	IdleTimeout    time.Duration // worker exits after this idle period (if above min)
	SubmitTimeout  time.Duration // Submit blocks at most this long (0 = non-blocking drop)
	MaxRetries     int
	RetryBackoff   time.Duration
}

// DefaultConfig provides sensible defaults.
func DefaultConfig() Config {
	return Config{
		MinWorkers:    2,
		MaxWorkers:    10,
		QueueSize:     100,
		IdleTimeout:   30 * time.Second,
		SubmitTimeout: 0, // drop on full
		MaxRetries:    0,
		RetryBackoff:  100 * time.Millisecond,
	}
}

// Errors
var (
	ErrPoolClosed = errors.New("pool is closed")
	ErrQueueFull  = errors.New("task queue is full")
	ErrSubmitTimeout = errors.New("submit timed out")
)

// ─────────────────────────────────────────────────────────────
// Pool
// ─────────────────────────────────────────────────────────────

// Pool is a production-grade, dynamically-scaling worker pool.
type Pool struct {
	cfg     Config
	ctx     context.Context
	cancel  context.CancelFunc
	queue   chan taskEnvelope
	results chan TaskResult
	closed  int32 // atomic bool: 1 = closed

	// Worker management
	workerMu      sync.Mutex
	activeWorkers int64 // atomic
	workerCancels []context.CancelFunc

	// Metrics (all atomic for lock-free reads)
	mSubmitted int64
	mCompleted int64
	mFailed    int64
	mDropped   int64
	mRetries   int64
	mInFlight  int64

	shutdownWg sync.WaitGroup
}

// taskEnvelope wraps a Task with metadata.
type taskEnvelope struct {
	task    Task
	queued  time.Time
	retries int
}

// New creates a Pool, starts minimum workers, and launches the auto-scaler.
func New(cfg Config) *Pool {
	ctx, cancel := context.WithCancel(context.Background())

	p := &Pool{
		cfg:     cfg,
		ctx:     ctx,
		cancel:  cancel,
		queue:   make(chan taskEnvelope, cfg.QueueSize),
		results: make(chan TaskResult, cfg.QueueSize),
	}

	// Start minimum workers
	for i := 0; i < cfg.MinWorkers; i++ {
		p.startWorker()
	}

	// Auto-scaler goroutine
	go p.scaler()

	return p
}

// startWorker launches a new worker goroutine.
func (p *Pool) startWorker() {
	workerCtx, workerCancel := context.WithCancel(p.ctx)

	p.workerMu.Lock()
	p.workerCancels = append(p.workerCancels, workerCancel)
	p.workerMu.Unlock()

	atomic.AddInt64(&p.activeWorkers, 1)
	p.shutdownWg.Add(1)

	go func() {
		defer func() {
			atomic.AddInt64(&p.activeWorkers, -1)
			p.shutdownWg.Done()
		}()

		idleTimer := time.NewTimer(p.cfg.IdleTimeout)
		defer idleTimer.Stop()

		for {
			select {
			case <-workerCtx.Done():
				return

			case env, ok := <-p.queue:
				if !ok {
					return
				}
				if !idleTimer.Stop() {
					select {
					case <-idleTimer.C:
					default:
					}
				}
				idleTimer.Reset(p.cfg.IdleTimeout)
				p.executeTask(workerCtx, env)

			case <-idleTimer.C:
				if atomic.LoadInt64(&p.activeWorkers) > int64(p.cfg.MinWorkers) {
					workerCancel()
					return
				}
				idleTimer.Reset(p.cfg.IdleTimeout)
			}
		}
	}()
}

// executeTask runs a task, handles retries, sends result.
func (p *Pool) executeTask(ctx context.Context, env taskEnvelope) {
	atomic.AddInt64(&p.mInFlight, 1)
	defer atomic.AddInt64(&p.mInFlight, -1)

	start := time.Now()

	var value interface{}
	var err error

	maxAttempts := p.cfg.MaxRetries + 1
	backoff := p.cfg.RetryBackoff

	for attempt := 0; attempt < maxAttempts; attempt++ {
		if attempt > 0 {
			atomic.AddInt64(&p.mRetries, 1)
			select {
			case <-ctx.Done():
				err = ctx.Err()
				goto done
			case <-time.After(backoff):
				backoff *= 2
			}
		}

		value, err = func() (v interface{}, e error) {
			defer func() {
				if r := recover(); r != nil {
					e = fmt.Errorf("panic: %v", r)
				}
			}()
			return env.task.Execute(ctx)
		}()

		if err == nil {
			break
		}
	}

done:
	end := time.Now()
	if err != nil {
		atomic.AddInt64(&p.mFailed, 1)
	} else {
		atomic.AddInt64(&p.mCompleted, 1)
	}

	result := TaskResult{
		Task:   env.task,
		Value:  value,
		Err:    err,
		Queued: env.queued,
		Start:  start,
		End:    end,
	}

	select {
	case p.results <- result:
	case <-ctx.Done():
		// Result discarded if pool shutting down; caller should drain results before shutdown.
	}
}

// scaler periodically checks queue depth and adds workers as needed.
func (p *Pool) scaler() {
	ticker := time.NewTicker(200 * time.Millisecond)
	defer ticker.Stop()

	for {
		select {
		case <-p.ctx.Done():
			return
		case <-ticker.C:
			qDepth := len(p.queue)
			active := int(atomic.LoadInt64(&p.activeWorkers))
			// Scale up: queue is getting full and we have headroom
			if qDepth > p.cfg.QueueSize/3 && active < p.cfg.MaxWorkers {
				p.startWorker()
			}
		}
	}
}

// Submit adds a task to the pool.
// Behavior on full queue is controlled by cfg.SubmitTimeout:
//   0 = drop immediately (non-blocking)
//   > 0 = block up to SubmitTimeout
//   use Submit with a context for cancellation
func (p *Pool) Submit(task Task) error {
	if atomic.LoadInt32(&p.closed) == 1 {
		return ErrPoolClosed
	}
	atomic.AddInt64(&p.mSubmitted, 1)

	env := taskEnvelope{task: task, queued: time.Now()}

	if p.cfg.SubmitTimeout == 0 {
		// Non-blocking drop
		select {
		case p.queue <- env:
			return nil
		default:
			atomic.AddInt64(&p.mDropped, 1)
			return ErrQueueFull
		}
	}

	// Blocking with timeout
	select {
	case p.queue <- env:
		return nil
	case <-time.After(p.cfg.SubmitTimeout):
		atomic.AddInt64(&p.mDropped, 1)
		return ErrSubmitTimeout
	case <-p.ctx.Done():
		return ErrPoolClosed
	}
}

// Results returns the channel on which completed TaskResults are sent.
// The caller MUST drain this channel to avoid blocking workers.
func (p *Pool) Results() <-chan TaskResult { return p.results }

// Metrics returns a snapshot of current pool metrics.
func (p *Pool) Metrics() Metrics {
	return Metrics{
		Submitted:     atomic.LoadInt64(&p.mSubmitted),
		Completed:     atomic.LoadInt64(&p.mCompleted),
		Failed:        atomic.LoadInt64(&p.mFailed),
		Dropped:       atomic.LoadInt64(&p.mDropped),
		Retries:       atomic.LoadInt64(&p.mRetries),
		InFlight:      atomic.LoadInt64(&p.mInFlight),
		QueueDepth:    int64(len(p.queue)),
		ActiveWorkers: atomic.LoadInt64(&p.activeWorkers),
	}
}

// Shutdown gracefully stops the pool.
// It stops accepting new tasks, waits for in-flight tasks to complete,
// then closes the results channel.
func (p *Pool) Shutdown(ctx context.Context) error {
	if !atomic.CompareAndSwapInt32(&p.closed, 0, 1) {
		return ErrPoolClosed // already closed
	}
	close(p.queue)     // signal workers: no more jobs
	p.cancel()         // cancel all worker contexts

	// Wait for workers with a deadline from caller's context
	done := make(chan struct{})
	go func() {
		p.shutdownWg.Wait()
		close(done)
	}()

	select {
	case <-done:
		close(p.results)
		return nil
	case <-ctx.Done():
		return fmt.Errorf("shutdown timed out: %w", ctx.Err())
	}
}

// Metrics is a point-in-time snapshot of pool health.
type Metrics struct {
	Submitted     int64
	Completed     int64
	Failed        int64
	Dropped       int64
	Retries       int64
	InFlight      int64
	QueueDepth    int64
	ActiveWorkers int64
}

func (m Metrics) SuccessRate() float64 {
	if m.Submitted == 0 {
		return 0
	}
	return float64(m.Completed) / float64(m.Submitted) * 100
}

func (m Metrics) String() string {
	return fmt.Sprintf(
		"workers=%d queue=%d submitted=%d completed=%d failed=%d dropped=%d retries=%d inflight=%d success=%.1f%%",
		m.ActiveWorkers, m.QueueDepth, m.Submitted, m.Completed,
		m.Failed, m.Dropped, m.Retries, m.InFlight, m.SuccessRate(),
	)
}
```

**Usage of the production pool:**

```go
package main

import (
	"context"
	"fmt"
	"math/rand"
	"time"

	"yourmodule/workerpool"
)

// HTTPTask simulates an HTTP request.
type HTTPTask struct {
	URL string
}

func (t HTTPTask) Execute(ctx context.Context) (interface{}, error) {
	// Simulate network latency
	select {
	case <-time.After(time.Duration(rand.Intn(100)) * time.Millisecond):
	case <-ctx.Done():
		return nil, ctx.Err()
	}
	if rand.Float32() < 0.1 {
		return nil, fmt.Errorf("HTTP 500 from %s", t.URL)
	}
	return fmt.Sprintf("200 OK from %s", t.URL), nil
}

func main() {
	cfg := workerpool.DefaultConfig()
	cfg.MinWorkers = 3
	cfg.MaxWorkers = 10
	cfg.QueueSize = 50
	cfg.MaxRetries = 2
	cfg.RetryBackoff = 50 * time.Millisecond
	cfg.SubmitTimeout = 100 * time.Millisecond

	pool := workerpool.New(cfg)

	// Drain results in a separate goroutine
	var wg sync.WaitGroup
	wg.Add(1)
	go func() {
		defer wg.Done()
		for result := range pool.Results() {
			if result.Err != nil {
				fmt.Printf("FAIL url=%v err=%v latency=%v\n",
					result.Task.(HTTPTask).URL, result.Err, result.Latency())
			} else {
				fmt.Printf("OK   result=%v latency=%v wait=%v\n",
					result.Value, result.Latency(), result.QueueWait())
			}
		}
	}()

	// Submit 100 tasks
	urls := []string{"api.example.com", "db.example.com", "cache.example.com"}
	for i := 0; i < 100; i++ {
		url := urls[i%len(urls)]
		if err := pool.Submit(HTTPTask{URL: url}); err != nil {
			fmt.Printf("Submit error: %v\n", err)
		}
	}

	// Print metrics
	fmt.Println("Metrics:", pool.Metrics())

	// Graceful shutdown: wait up to 5 seconds for in-flight tasks
	shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	if err := pool.Shutdown(shutdownCtx); err != nil {
		fmt.Printf("Shutdown error: %v\n", err)
	}

	// Wait for result drainer to finish
	wg.Wait()
	fmt.Println("Final metrics:", pool.Metrics())
}
```

### 5.8 Graceful Shutdown — The Full Lifecycle

This is the most nuanced part. Let's trace through every step:

```
GRACEFUL SHUTDOWN SEQUENCE:
────────────────────────────────────────────────────────────────

Step 1: Mark pool as closed (atomic CAS)
  ─ Prevents new Submit() calls from succeeding
  ─ Returns ErrPoolClosed to new callers

Step 2: close(queue channel)
  ─ Workers' range loops will drain existing jobs first
  ─ After queue is empty + closed, range exits automatically

Step 3: cancel() the pool context
  ─ Any task currently in Execute() will see ctx.Done()
  ─ Long-running tasks can abort mid-way

Step 4: Wait for all workers (WaitGroup)
  ─ Every worker calls wg.Done() on exit
  ─ wg.Wait() blocks until counter reaches 0

Step 5: close(results channel)
  ─ The result-draining goroutine's range loop exits
  ─ All results have been sent; no more will arrive

Timeline:
─────────────────────────────────────────────────────────────────

t=0:  Shutdown() called
      ┌─ close(queue)    ──▶ queue draining begins
      └─ cancel()        ──▶ ctx.Done() fires

t=1:  Workers:
      ├─ Worker 1: finishes current job, sees queue closed, exits (Done)
      ├─ Worker 2: mid-job, sees ctx.Done(), returns error result, exits (Done)
      └─ Worker 3: idle, sees queue closed, exits immediately (Done)

t=2:  wg.Wait() unblocks (all workers Done)
      close(results)
      Shutdown() returns nil

t=3:  Result drainer: range results exits (channel closed)
      main() proceeds

FORCED SHUTDOWN (ctx timeout):
      t=5s (timeout): Shutdown() returns error "shutdown timed out"
      ─ Workers may still be running
      ─ Caller may os.Exit() or force-kill
```

---

## 6. Patterns, Pitfalls, and Production Wisdom

### 6.1 Common Pitfalls

**Pitfall 1: Goroutine Leak**
```go
// BUG: if nobody reads from results, workers block forever
func badPool(jobs []Job) chan Result {
	results := make(chan Result) // unbuffered!
	go func() {
		for _, job := range jobs {
			results <- process(job)  // blocks if nobody reading
		}
	}()
	return results
}

// The goroutine leaks if caller doesn't drain results channel.
// RULE: Always buffer results OR always guarantee a drainer goroutine.
```

**Pitfall 2: Closing a channel twice**
```go
// If multiple goroutines could close, guard with sync.Once
var once sync.Once
closeResults := func() {
	once.Do(func() { close(results) })
}
```

**Pitfall 3: Sending to closed channel (panic)**
```go
// Worker should never send to results after it's closed.
// Pattern: use select with pool ctx:
select {
case results <- r:
case <-ctx.Done():
	return  // don't send, pool is shutting down
}
```

**Pitfall 4: WaitGroup counter race**
```go
// WRONG:
go func() {
	wg.Add(1)   // ← too late; wg.Wait() might have already returned
	defer wg.Done()
}()

// CORRECT:
wg.Add(1)   // ← before go statement
go func() {
	defer wg.Done()
}()
```

**Pitfall 5: Shared mutable state without synchronization**
```go
// WRONG: multiple workers write to map concurrently
results := map[int]int{}
go worker(jobs, func(id, val int) {
	results[id] = val  // DATA RACE
})

// CORRECT: use mutex, sync.Map, or per-channel results
var mu sync.Mutex
go worker(jobs, func(id, val int) {
	mu.Lock()
	results[id] = val
	mu.Unlock()
})
```

**Pitfall 6: Blocking inside a worker without context check**
```go
// WRONG: worker ignores ctx
func badWorker(job Job) Result {
	time.Sleep(1 * time.Hour)  // ignores ctx; pool can't shut down
	return process(job)
}

// CORRECT: every blocking operation must select on ctx.Done()
func goodWorker(ctx context.Context, job Job) (Result, error) {
	select {
	case <-time.After(1 * time.Hour):
		return process(job), nil
	case <-ctx.Done():
		return Result{}, ctx.Err()
	}
}
```

### 6.2 Pool Sizing — How to Choose numWorkers

This depends on whether work is CPU-bound or I/O-bound:

```
CPU-BOUND work (computation, image processing, crypto):
─────────────────────────────────────────────────────────
numWorkers = runtime.NumCPU()
OR
numWorkers = runtime.NumCPU() - 1  // leave one for runtime/GC

More workers than CPUs hurts: context switching overhead increases,
caches thrash, each worker gets less CPU time.

I/O-BOUND work (HTTP requests, DB queries, file reads):
──────────────────────────────────────────────────────────
numWorkers >> runtime.NumCPU()

Workers spend most time waiting. Many can be "running" concurrently
on the same CPU. A common starting point:

numWorkers = runtime.NumCPU() * multiplier

where multiplier = (wait_time + work_time) / work_time

Example: job takes 1ms CPU, 99ms waiting → multiplier = 100
numWorkers ≈ 100 * runtime.NumCPU()

EMPIRICAL APPROACH (best in practice):
─────────────────────────────────────────
1. Measure: baseline with numWorkers = runtime.NumCPU()
2. Load test: increase numWorkers until throughput plateaus
3. Watch: CPU %, memory, downstream service load, error rate
4. Set: numWorkers at ~80% of the plateau point (safety margin)
5. Tune: idle timeout and queue size based on traffic patterns
```

### 6.3 Queue Depth — How to Choose bufferSize

```
Queue is too small:
─────────────────────────────────────────────────────────────
Producer blocks frequently → low throughput
Workers are occasionally idle (producer couldn't refill fast enough)
Backpressure is strong → upstream feels it immediately
Good for: strict flow control, real-time systems

Queue is too large:
────────────────────────────────────────────────────────────
Memory bloat (each queued item holds references)
High latency variance (job queued for a long time before processing)
If workers go down, in-queue jobs are lost (no persistence)
Bad for: latency-sensitive workloads, large payloads

Rule of thumb:
──────────────────────────────────────────────────────────────
queueSize = numWorkers * 2 to numWorkers * 10

Start at numWorkers * 2 and increase if you see producers blocking.
Never exceed available memory / average job size.
```

### 6.4 The Three Core Patterns — Cheat Sheet

```
PATTERN 1: FIXED POOL
─────────────────────────────────────────────────────────────────
Use when: job count known ahead of time, bounded resources
Code:     make(chan Job, numJobs) + N workers + close(jobs) + range results
Shutdown: close(jobs) → workers exit naturally

PATTERN 2: STREAMING POOL
─────────────────────────────────────────────────────────────────
Use when: continuous job stream (server, event loop)
Code:     make(chan Job, bufSize) + N workers + context cancellation
Shutdown: cancel() → workers detect ctx.Done() → close(results) after WaitGroup

PATTERN 3: PIPELINE POOL
─────────────────────────────────────────────────────────────────
Use when: multi-stage processing (ETL, media processing)
Code:     chain of pools via channels: gen() → pool1 → pool2 → sink()
Shutdown: cancel root context → propagates through all stages automatically
```

### 6.5 Testing Worker Pools

```go
package workerpool_test

import (
	"context"
	"sync/atomic"
	"testing"
	"time"
)

func TestBasicPool(t *testing.T) {
	numJobs := 100
	jobs := make(chan int, numJobs)
	results := make(chan int, numJobs)
	var wg sync.WaitGroup

	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for j := range jobs {
				results <- j * j
			}
		}()
	}
	go func() {
		wg.Wait()
		close(results)
	}()

	for i := 0; i < numJobs; i++ {
		jobs <- i
	}
	close(jobs)

	var count int
	for range results {
		count++
	}

	if count != numJobs {
		t.Errorf("expected %d results, got %d", numJobs, count)
	}
}

func TestPoolCancellation(t *testing.T) {
	var executed int64
	ctx, cancel := context.WithCancel(context.Background())

	jobs := make(chan struct{}, 1000)
	for i := 0; i < 1000; i++ {
		jobs <- struct{}{}
	}
	close(jobs)

	var wg sync.WaitGroup
	for i := 0; i < 4; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			for range jobs {
				select {
				case <-ctx.Done():
					return
				default:
					atomic.AddInt64(&executed, 1)
					time.Sleep(time.Millisecond)
				}
			}
		}()
	}

	time.Sleep(10 * time.Millisecond)
	cancel()
	wg.Wait()

	if atomic.LoadInt64(&executed) >= 1000 {
		t.Error("expected cancellation to stop workers before processing all jobs")
	}
	t.Logf("Executed %d/1000 jobs before cancellation", executed)
}

func TestPoolNoLeaks(t *testing.T) {
	// Use goleak in real tests: go.uber.org/goleak
	// This manually checks goroutine count.
	before := runtime.NumGoroutine()

	pool := New(DefaultConfig())
	for i := 0; i < 10; i++ {
		pool.Submit(simpleTask{})
	}
	ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
	defer cancel()
	pool.Shutdown(ctx)

	time.Sleep(100 * time.Millisecond)
	after := runtime.NumGoroutine()

	if after > before+2 { // +2 for test framework goroutines
		t.Errorf("goroutine leak: before=%d after=%d", before, after)
	}
}

func BenchmarkPool(b *testing.B) {
	pool := New(DefaultConfig())
	defer pool.Shutdown(context.Background())

	go func() {
		for range pool.Results() {}
	}()

	b.ResetTimer()
	b.RunParallel(func(pb *testing.PB) {
		for pb.Next() {
			pool.Submit(noopTask{})
		}
	})
}
```

### 6.6 Advanced: Work Stealing

An optimization used by Go's runtime itself. When one worker's local queue is empty, it "steals" work from another worker's queue. This reduces contention on a shared global queue.

```
WORK STEALING ARCHITECTURE:
────────────────────────────────────────────────────────────────

           Global Queue (overflow)
           ┌──────────────────────┐
           │[J][J][J][J][J][J]   │
           └──────────┬───────────┘
                      │ steal (if local empty)
         ┌────────────┼───────────┐
         ▼            ▼           ▼
  ┌────────────┐ ┌────────────┐ ┌────────────┐
  │ Worker 1   │ │ Worker 2   │ │ Worker 3   │
  │ Local: [J] │ │ Local: [ ] │ │ Local: [J] │
  │            │ │            │ │            │
  │  [busy]    │ │   steal──▶ │ │  [busy]    │
  └────────────┘ └────────────┘ └────────────┘
                       │
                       ▼ steal from Worker 1 or Worker 3 half their queue
```

This is complex to implement correctly in Go (Go's own scheduler does this internally). For application-level pools, a shared buffered channel is usually sufficient.

### 6.7 Full System Diagram — Everything Together

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PRODUCTION WORKER POOL SYSTEM                        │
│                                                                           │
│  ┌──────────────────┐                                                    │
│  │  HTTP Handler /  │  Submit(task)                                      │
│  │  gRPC Handler /  │─────────────────────────┐                         │
│  │  CLI / Event Bus │                          │                         │
│  └──────────────────┘                          ▼                         │
│                                    ┌───────────────────────┐             │
│  ┌─────────────────┐               │  Rate Limiter         │             │
│  │  Config         │               │  (token bucket)       │             │
│  │  MinWorkers=3   │               └───────────┬───────────┘             │
│  │  MaxWorkers=10  │                           │                         │
│  │  QueueSize=100  │                           ▼                         │
│  │  IdleTimeout=30s│               ┌───────────────────────┐             │
│  │  MaxRetries=2   │               │  Bounded Queue        │             │
│  └─────────────────┘               │  [J][J][J][J][J]....  │             │
│                                    │  (buffered channel)   │             │
│  ┌─────────────────┐               └───────────┬───────────┘             │
│  │  Scaler         │                           │  Dispatch               │
│  │  (every 200ms)  │◀──────── queue depth ─────┤                         │
│  │  scale up if    │                           │                         │
│  │  queue > 33%    │               ┌───────────▼────────────────────┐    │
│  │  scale down if  │               │         Worker Pool             │    │
│  │  workers idle   │               │                                 │    │
│  └─────────────────┘               │  ┌──────────┐  ┌──────────┐    │    │
│                                    │  │ Worker 1 │  │ Worker 2 │    │    │
│                                    │  │[execute] │  │ [idle]   │    │    │
│                                    │  └────┬─────┘  └──────────┘    │    │
│  ┌─────────────────┐               │       │                         │    │
│  │  Metrics        │               │  ┌────▼─────┐  ┌──────────┐    │    │
│  │  (atomic)       │◀──────────────│  │ Worker 3 │  │ Worker N │    │    │
│  │  submitted=100  │               │  │[execute] │  │[execute] │    │    │
│  │  completed=90   │               │  └────┬─────┘  └────┬─────┘    │    │
│  │  failed=5       │               └───────┼─────────────┼───────────┘    │
│  │  dropped=5      │                       │             │               │
│  │  inflight=3     │               ┌───────▼─────────────▼───────────┐   │
│  │  p99=45ms       │               │        Results Channel           │   │
│  └─────────────────┘               │  [R][R][R][R][R]...             │   │
│                                    └────────────────┬────────────────┘   │
│                                                     │                    │
│  ┌──────────────────┐              ┌────────────────▼────────────────┐   │
│  │  context.Context │──cancel()──▶ │   Result Consumer               │   │
│  │  (shutdown       │              │   (separate goroutine)          │   │
│  │   trigger)       │              │   logs, metrics, DB writes      │   │
│  └──────────────────┘              └─────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 6.8 When NOT to Use a Worker Pool

- **Very few jobs** (< 10): overhead of pool setup exceeds benefit; just use goroutines.
- **Single-threaded I/O bottleneck**: if downstream (DB, API) can only handle 1 request at a time, a pool of N workers all contend on the same lock/connection — use a single worker instead.
- **Ordered streaming with no latency tolerance**: a pool introduces reordering; for ordered streaming, consider a sequential pipeline.
- **CPU-bound with GOMAXPROCS=1**: workers don't parallelize on a single CPU.

### 6.9 Summary Comparison Table

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    WORKER POOL COMPARISON                                │
├────────────────┬───────────────┬─────────────────┬──────────────────────┤
│ Aspect         │ Basic         │ Intermediate    │ Advanced             │
├────────────────┼───────────────┼─────────────────┼──────────────────────┤
│ Worker count   │ Fixed         │ Fixed           │ Dynamic (min/max)    │
│ Error handling │ None (panic!) │ Per-result err  │ Per-result + retry   │
│ Cancellation   │ None          │ context.Context │ Context + draining   │
│ Result order   │ Unordered     │ Optional sort   │ Ordered or unordered │
│ Backpressure   │ Channel block │ Timeout/drop    │ Configurable policy  │
│ Rate limiting  │ None          │ None            │ Token bucket         │
│ Metrics        │ None          │ Basic counters  │ Full observability   │
│ Shutdown       │ WaitGroup     │ ctx + WaitGroup │ Graceful drain + TL  │
│ Testing        │ Trivial       │ ctx injection   │ Benchmarks, goleak   │
│ Complexity     │ Low           │ Medium          │ High                 │
│ Lines of code  │ ~50           │ ~200            │ ~500+                │
│ Use case       │ Scripts       │ Services        │ High-traffic prod    │
└────────────────┴───────────────┴─────────────────┴──────────────────────┘
```

---

## Final Mental Models to Internalize

**1. A channel is a pipe. Buffer is the pipe's diameter. Closing is plugging one end.**

**2. Workers are factory workers. The channel is the conveyor belt. Buffer is in-tray depth.**

**3. Context is the fire alarm. When pulled, everyone stops what they're doing and exits.**

**4. WaitGroup is a headcount. You can only leave when the count hits zero.**

**5. The golden rule:** Producer closes the channel. Never the consumer. Never close twice.

**6. Backpressure is a feature, not a bug.** When downstream is slow, upstream feeling it is correct behavior. Design for it.

**7. Measure before optimizing.** Worker count, buffer size, and retry policy all need profiling data. Start with sensible defaults; instrument first; optimize second.

**8. Goroutine leaks are memory leaks.** Every goroutine you start must have a clear exit condition. Use `goleak` in tests.

**9. Panic is not an error.** Recover inside workers and convert panics to errors. Never let a bad job kill the whole pool.

**10. Graceful shutdown is a first-class concern.** Design for it from day one. A pool that can't be stopped cleanly will cause you pain in production.

---

*End of Guide — Worker Pools in Go: Basic → Intermediate → Advanced*

Here's what the guide covers end-to-end:

**Foundation (Section 2)** — Before any pool code, deep dives into the primitives that make pools possible: goroutine scheduling (M:N model), channel semantics (buffered vs unbuffered, direction types, close protocol), `sync.WaitGroup` invariants (why `Add` must precede `go`), `sync.Mutex`/`sync.RWMutex`, `context.Context` cancellation trees, and `sync/atomic` for lock-free counters.

**Basic Pool (Section 3)** — The factory floor mental model, execution trace step-by-step, channel buffer sizing trade-offs, all three termination strategies (close channel / poison pill / WaitGroup+goroutine), and a timing diagram showing why results arrive out of order.

**Intermediate Pool (Section 4)** — Per-job error handling with panic recovery, graceful shutdown via `context.Context` with the double-select priority pattern, result ordering (three approaches), fan-out/fan-in pipelines, and exponential backoff retry logic. Plus the semaphore pattern as an alternative.

**Advanced Pool (Section 5)** — Priority queue pool using `container/heap`, dynamic elastic scaling with idle-timeout scale-down, token bucket rate limiter, all three backpressure policies (block/drop/timeout), full atomic metrics system, and a complete production-grade reusable `Pool` struct implementing the `Task` interface. Includes the full graceful shutdown lifecycle trace.

**Section 6** — The 10 common pitfalls with wrong vs. correct code, CPU-bound vs I/O-bound worker sizing math, queue depth heuristics, work stealing concept, and a summary comparison table across all three levels. Ends with 10 mental models to internalize.