# Go Concurrency Patterns in the Wild
### How Kubernetes, etcd, Docker & Prometheus actually use WaitGroups, channels, mutexes, context, and more

Each section below: **what the primitive does → a real-world-style example based on the pattern used in that project → why they chose it → how to reuse the pattern yourself.**

> Note: the snippets are simplified, representative versions of the real patterns (renamed/trimmed for teaching), not verbatim pastes of current source files — real files change across versions and carry license headers. The *structure and idiom* shown is exactly what you'll find if you read the actual source.

---

## 1. `sync.WaitGroup` — fan-out and wait for completion

**Used for:** starting N goroutines and blocking until all of them finish. Kubernetes uses this constantly in its controllers to run per-item work in parallel and wait for the batch to drain.

**Pattern (from `client-go` / controller-manager style code, e.g. syncing multiple pods per node):**

```go
func syncAllNodes(nodes []*Node, syncFn func(*Node) error) []error {
    var wg sync.WaitGroup
    errCh := make(chan error, len(nodes))

    for _, node := range nodes {
        wg.Add(1)
        go func(n *Node) {
            defer wg.Done()
            if err := syncFn(n); err != nil {
                errCh <- fmt.Errorf("node %s: %w", n.Name, err)
            }
        }(node)
    }

    wg.Wait()
    close(errCh)

    var errs []error
    for err := range errCh {
        errs = append(errs, err)
    }
    return errs
}
```

**Why this shape:**
- `wg.Add(1)` happens **before** the goroutine starts, never inside it — avoids a race where `Wait()` returns early.
- The loop variable `node` is passed as a parameter (`n *Node`) instead of captured by the closure — classic Go loop-variable-capture bug avoided (pre Go 1.22 semantics; still good habit).
- Errors are collected via a buffered channel sized to `len(nodes)` so no goroutine ever blocks trying to send — this is the trick that lets you not need a mutex just to collect results.

**Reuse it when:** you need to run independent work concurrently and must not proceed until *all* of it is done (batch reconciliation, parallel health checks, fan-out API calls to multiple backends).

---

## 2. Buffered vs unbuffered channels — the workqueue pattern

**Used for:** Kubernetes' `client-go` has a `workqueue` package that every controller (Deployment controller, ReplicaSet controller, etc.) is built on. It's a channel-backed queue with de-duplication and rate limiting.

**Pattern (simplified core idea of `workqueue.Interface`):**

```go
type Queue struct {
    mu      sync.Mutex
    cond    *sync.Cond
    items   []string
    dirty   map[string]struct{} // set of items waiting to be processed
    processing map[string]struct{} // set of items currently being processed
}

func (q *Queue) Add(item string) {
    q.mu.Lock()
    defer q.mu.Unlock()
    if _, exists := q.dirty[item]; exists {
        return // already queued, de-dupe
    }
    q.dirty[item] = struct{}{}
    if _, isProcessing := q.processing[item]; isProcessing {
        return // will be re-queued when done
    }
    q.items = append(q.items, item)
    q.cond.Signal()
}

func (q *Queue) Get() (item string, shutdown bool) {
    q.mu.Lock()
    defer q.mu.Unlock()
    for len(q.items) == 0 {
        q.cond.Wait()
    }
    item, q.items = q.items[0], q.items[1:]
    q.processing[item] = struct{}{}
    delete(q.dirty, item)
    return item, false
}
```

**Why not just a plain channel?** A raw `chan string` can't de-duplicate ("Pod X changed twice" shouldn't mean "process Pod X twice"), and it can't easily support "requeue this item only after it's done processing." So Kubernetes builds a **condition-variable-backed queue with set semantics** instead of relying on channel buffering alone. This is the single most important lesson from reading `client-go`: **channels are great for signaling and pipelines, but for anything needing de-dup/priority/rate-limiting, people build a small structure around a mutex + `sync.Cond` or channel instead.**

**Reuse it when:** you're building any kind of reconciliation loop — "keep retrying this key until it succeeds, but don't process the same key twice in parallel."

---

## 3. `select` — multiplexing channels and cancellation

**Used for:** almost every long-running goroutine in Kubernetes and etcd needs to stop cleanly when told to. `select` is how you race "new work arrived" against "I've been told to stop."

**Pattern (typical controller run-loop, seen throughout `k8s.io/controller-manager` and etcd's `raft` node loop):**

```go
func (c *Controller) Run(stopCh <-chan struct{}) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-stopCh:
            klog.Info("controller shutting down")
            return
        case <-ticker.C:
            c.resync()
        case event := <-c.eventCh:
            c.handleEvent(event)
        }
    }
}
```

etcd's Raft node (`raft.node.run`) is the canonical example of this at scale — one giant `select` multiplexing: proposals coming in, incoming messages from peers, tick signals, config changes, and a done/stop channel, all in a single loop so there's exactly one goroutine mutating Raft state (no locks needed for the state machine itself — the single-goroutine-owns-the-state pattern).

**Why:** `select` lets one goroutine service multiple event sources without polling, and adding a `stopCh`/`ctx.Done()` case to every `select` is the idiomatic way to make a loop cancellable.

**Reuse it when:** you have a loop reading from more than one channel, or any goroutine that must be stoppable from outside.

---

## 4. `context.Context` — cancellation, deadlines, and request-scoped values

**Used for:** every API server handler in Kubernetes, every gRPC call in etcd, and every HTTP client call in these projects thread a `context.Context` as the first argument. It's how "the client hung up" or "we hit our timeout" propagates down through a whole call tree of goroutines instantly.

**Pattern (typical apiserver storage layer, simplified from `k8s.io/apiserver/pkg/storage/etcd3`):**

```go
func (s *Store) Get(ctx context.Context, key string) (*Object, error) {
    ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
    defer cancel()

    resp, err := s.client.Get(ctx, key)
    if err != nil {
        if ctx.Err() == context.DeadlineExceeded {
            return nil, fmt.Errorf("etcd get timed out: %w", err)
        }
        return nil, err
    }
    ...
}
```

And propagating cancellation into a fan-out:

```go
func fetchAll(ctx context.Context, keys []string) ([]*Object, error) {
    g, ctx := errgroup.WithContext(ctx)
    results := make([]*Object, len(keys))

    for i, key := range keys {
        i, key := i, key
        g.Go(func() error {
            obj, err := store.Get(ctx, key) // ctx cancelled if ANY goroutine errors
            if err != nil {
                return err
            }
            results[i] = obj
            return nil
        })
    }
    if err := g.Wait(); err != nil {
        return nil, err
    }
    return results, nil
}
```

**Why `errgroup` instead of a raw `WaitGroup` here:** `golang.org/x/sync/errgroup` gives you a `WaitGroup` *plus* a shared cancellable `context` *plus* "return the first error." The moment one fetch fails, `ctx` is cancelled, so the other in-flight `Get` calls abort immediately instead of wasting work. This exact pattern — `errgroup.WithContext` for parallel fan-out with early-exit — is everywhere in Kubernetes' apiserver and in Docker's image-pulling code (pulling image layers in parallel, aborting all if one fails).

**Reuse it when:** you're calling multiple downstream services/goroutines in parallel and want "if one fails, cancel the rest" instead of waiting for stragglers that no longer matter.

---

## 5. `sync.Mutex` / `sync.RWMutex` — protecting shared state

**Used for:** Kubernetes' informer cache (`k8s.io/client-go/tools/cache`) is an in-memory store of cluster objects that's read constantly by many goroutines and written occasionally by the watch goroutine. Classic `RWMutex` use case.

**Pattern (simplified `ThreadSafeStore`):**

```go
type ThreadSafeStore struct {
    mu    sync.RWMutex
    items map[string]interface{}
}

func (c *ThreadSafeStore) Get(key string) (item interface{}, exists bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()
    item, exists = c.items[key]
    return item, exists
}

func (c *ThreadSafeStore) Add(key string, obj interface{}) {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.items[key] = obj
}

func (c *ThreadSafeStore) List() []interface{} {
    c.mu.RLock()
    defer c.mu.RUnlock()
    list := make([]interface{}, 0, len(c.items))
    for _, item := range c.items {
        list = append(list, item)
    }
    return list
}
```

**Why `RWMutex` and not `Mutex`:** reads (`Get`/`List`) vastly outnumber writes (a handful of watch events per second vs. thousands of controller goroutines reading the cache every reconcile). `RWMutex` lets unlimited readers proceed concurrently and only blocks for the rare writer — a plain `Mutex` would serialize all those reads for no reason.

**Reuse it when:** you have a read-heavy, write-light shared data structure (caches, config that's hot-reloaded, in-memory indexes).

---

## 6. `sync.Once` — one-time initialization

**Used for:** lazy, thread-safe singleton setup — e.g., initializing a shared HTTP client, a metrics registry, or a TLS config exactly once no matter how many goroutines ask for it concurrently. Prometheus's client library and Kubernetes' `klog` logging package both use this to lazily set up global state safely.

**Pattern:**

```go
var (
    defaultRegistryOnce sync.Once
    defaultRegistry     *Registry
)

func DefaultRegistry() *Registry {
    defaultRegistryOnce.Do(func() {
        defaultRegistry = newRegistry()
        defaultRegistry.MustRegister(processCollector, goCollector)
    })
    return defaultRegistry
}
```

**Why:** without `sync.Once`, you'd need a mutex plus a "did we already init" boolean, and get it wrong under concurrent first-calls. `Once.Do` guarantees exactly one caller runs the function and every other concurrent caller blocks until it's done, then proceeds — for free.

**Reuse it when:** any "compute/connect once, cache forever" scenario touched by multiple goroutines.

---

## 7. `sync/atomic` — lock-free counters and flags

**Used for:** high-frequency counters where taking a mutex would be measurably slower than the operation itself — request counters, in-flight request gauges, "is shutting down" flags. Kubernetes' apiserver max-in-flight limiter and Prometheus's internal counters use atomics.

**Pattern (in-flight request limiter, simplified from `k8s.io/apiserver/pkg/server/filters`):**

```go
type maxInFlightLimiter struct {
    current int64
    max     int64
}

func (l *maxInFlightLimiter) TryAcquire() bool {
    for {
        cur := atomic.LoadInt64(&l.current)
        if cur >= l.max {
            return false
        }
        if atomic.CompareAndSwapInt64(&l.current, cur, cur+1) {
            return true
        }
        // someone else changed it between Load and CAS — retry
    }
}

func (l *maxInFlightLimiter) Release() {
    atomic.AddInt64(&l.current, -1)
}
```

Modern code (Go 1.19+) would instead use the typed `atomic.Int64`:

```go
type maxInFlightLimiter struct {
    current atomic.Int64
    max     int64
}

func (l *maxInFlightLimiter) TryAcquire() bool {
    for {
        cur := l.current.Load()
        if cur >= l.max {
            return false
        }
        if l.current.CompareAndSwap(cur, cur+1) {
            return true
        }
    }
}
```

**Why atomics over a mutex here:** this function runs on the hot path of *every single API request* the cluster receives. A mutex lock/unlock is cheap but not free, and under heavy contention it causes goroutines to park and get rescheduled. A CAS loop degrades more gracefully under contention for a single integer.

**Reuse it when:** you have one or two primitive values (int64, bool, pointer) updated extremely frequently from many goroutines, and the logic around them is simple enough to express as load/compare-and-swap.

---

## 8. Worker pools — bounded concurrency

**Used for:** you never want unbounded goroutines processing unbounded work (e.g., pulling every image layer or syncing every pod at once could exhaust file descriptors / API rate limits). Docker's layer-pulling and Kubernetes' image garbage collector use a fixed-size pool of workers pulling off one channel.

**Pattern:**

```go
func processInParallel(ctx context.Context, items []string, workers int, fn func(context.Context, string) error) error {
    itemCh := make(chan string)
    g, ctx := errgroup.WithContext(ctx)

    // producer
    g.Go(func() error {
        defer close(itemCh)
        for _, item := range items {
            select {
            case itemCh <- item:
            case <-ctx.Done():
                return ctx.Err()
            }
        }
        return nil
    })

    // fixed pool of consumers
    for w := 0; w < workers; w++ {
        g.Go(func() error {
            for item := range itemCh {
                if err := fn(ctx, item); err != nil {
                    return err
                }
            }
            return nil
        })
    }

    return g.Wait()
}
```

**Why:** this caps concurrency at exactly `workers` regardless of how many `items` you have, while still letting one failure cancel the whole pipeline via `ctx`. It's the combination of pattern #2 (channel as work queue) + pattern #4 (`errgroup` for cancellation) + pattern #1 (waiting for completion) — real code usually composes these primitives rather than using one in isolation.

**Reuse it when:** the number of tasks is large/unbounded but you need to cap simultaneous work (rate-limited external APIs, limited file descriptors, limited DB connections).

---

## 9. `sync.Cond` — waiting for a condition on shared state

**Used for:** the `workqueue` example in section 2 actually uses `sync.Cond` under the hood for `Get()` to block until an item is available, without busy-waiting or needing a channel with unknown capacity. etcd's internal buffer/watch dispatch also uses condition variables where a plain channel doesn't fit (multiple readers needing to wake on the same event, with shared mutable state to inspect first).

**Pattern:**

```go
type Barrier struct {
    mu    sync.Mutex
    cond  *sync.Cond
    ready bool
}

func NewBarrier() *Barrier {
    b := &Barrier{}
    b.cond = sync.NewCond(&b.mu)
    return b
}

func (b *Barrier) Wait() {
    b.mu.Lock()
    defer b.mu.Unlock()
    for !b.ready {
        b.cond.Wait() // atomically unlocks mu and sleeps; re-locks on wake
    }
}

func (b *Barrier) Open() {
    b.mu.Lock()
    b.ready = true
    b.mu.Unlock()
    b.cond.Broadcast() // wake every waiter
}
```

**Why `sync.Cond` over a channel here:** you need to both (a) check/modify protected state and (b) sleep until it changes, atomically. A channel close can broadcast "done" once, but `sync.Cond` supports repeated broadcast/signal cycles tied to arbitrary mutex-protected state — which is exactly what a work queue needs ("wake up, check if the slice is non-empty, otherwise sleep again").

**Reuse it when:** you're about to reach for "channel of size 1 as a signal" and find yourself also needing a mutex around other state anyway — that's usually the moment `sync.Cond` is the cleaner tool. (It's less common than channels, so most Go style guides say "prefer channels unless you clearly need this.")

---

## 10. Graceful shutdown — closing channels as a broadcast signal

**Used for:** telling an arbitrary number of goroutines "stop now" simultaneously. Kubernetes controllers universally take a `<-chan struct{}` (older style) or `context.Context` (newer style) as a stop signal, and the *caller* closes it once.

**Pattern:**

```go
func RunControllers(stopCh <-chan struct{}, controllers []Controller) {
    var wg sync.WaitGroup
    for _, c := range controllers {
        wg.Add(1)
        go func(ctrl Controller) {
            defer wg.Done()
            ctrl.Run(stopCh) // every controller's select includes case <-stopCh
        }(c)
    }
    wg.Wait() // block until every controller has actually stopped
}

func main() {
    stopCh := make(chan struct{})
    go RunControllers(stopCh, myControllers)

    sigCh := make(chan os.Signal, 1)
    signal.Notify(sigCh, syscall.SIGTERM, syscall.SIGINT)
    <-sigCh
    close(stopCh) // closing (not sending!) wakes every goroutine's select at once
}
```

**Why `close()` instead of sending a value:** receiving from a closed channel never blocks and always returns the zero value immediately — so `close(stopCh)` is a broadcast to an unlimited number of goroutines with zero coordination, whereas sending a value only reaches one receiver. This is one of the most-repeated idioms in Go systems code.

**Reuse it when:** you need to signal "stop"/"done" to a variable and possibly unknown number of goroutines. (Modern code increasingly uses `context.WithCancel` instead — cancelling the context has the same broadcast-via-close semantics, `ctx.Done()` is literally a channel that gets closed.)

---

## Quick reference: which tool for which job

| Need | Reach for |
|---|---|
| Wait for N known goroutines to finish | `sync.WaitGroup` |
| Wait for N goroutines, want first error + auto-cancel the rest | `errgroup.WithContext` |
| Pass a single value between exactly one sender/receiver, or build a pipeline | unbuffered/buffered `chan` |
| Multiplex several channels / make a loop cancellable | `select` + a `stop`/`ctx.Done()` case |
| Propagate cancellation, deadlines, or request-scoped values through a call chain | `context.Context` |
| Protect a read-heavy shared map/struct | `sync.RWMutex` |
| Protect a write-heavy or simple shared struct | `sync.Mutex` |
| Run setup exactly once, thread-safely | `sync.Once` |
| Update a single counter/flag at very high frequency | `sync/atomic` |
| Bound concurrency over an unbounded task list | worker pool (channel + fixed goroutines) |
| Sleep until arbitrary shared-state condition changes, with repeated wakeups | `sync.Cond` |
| Broadcast "stop" to unknown number of goroutines at once | `close(ch)` or `context.WithCancel` |

## Where to go read the real thing

- **`k8s.io/client-go/util/workqueue`** — the queue pattern in full, with rate limiting added on top.
- **`k8s.io/apiserver/pkg/server/filters/maxinflight.go`** — real atomic-based in-flight limiter.
- **`etcd-io/etcd`, package `raft`** — `node.run()` is the best `select`-driven single-goroutine-owns-state example in the Go ecosystem.
- **`golang.org/x/sync/errgroup`** — short enough to read end-to-end in five minutes; do it once.
- **`moby/moby` (Docker), `distribution/distribution`** — layer pull/push worker pools.
- **`prometheus/client_golang`** — `sync.Once` and atomics for metrics registration/collection.

The single biggest thing that distinguishes this "real" code from tutorial code: **almost nothing uses a concurrency primitive in isolation.** Production code composes them — a worker pool is a channel *and* an errgroup *and* a WaitGroup; a workqueue is a mutex *and* a cond *and* a map for de-dup. Once you can read each primitive individually, the way to level up is reading how 2–3 of them get combined to solve one concrete problem (rate-limited retries, graceful shutdown, bounded parallel fetch).

Good question — this is really a story about a specific set of engineering pains at Google in the mid-2000s, plus an idea borrowed from academic computer science, and it's worth walking through in order because each primitive exists to answer one concrete problem.

## The problem Go was built to solve (2007–2009)

Rob Pike, Robert Griesemer, and Ken Thompson designed Go at Google while dealing with a very specific set of frustrations:

- **Multicore hardware had arrived, but mainstream languages hadn't caught up.** C++ and Java concurrency meant OS threads — each one costing roughly 1–8 MB of stack and real kernel scheduling overhead. You simply could not spin up 100,000 of them to handle 100,000 connections. Servers at Google's scale needed *massive* concurrency, not the "dozens of threads" model most languages were built around.
- **Shared-memory concurrency was a constant source of bugs.** Getting locking right across large C++ codebases, maintained by thousands of engineers with varying experience, produced a steady stream of data races, deadlocks, and subtle bugs that were brutal to reproduce and debug.
- **Build times and language complexity were slowing everyone down.** C++ compile times at Google's scale were legendary. Go's simplicity (few keywords, fast compiler) was as much a design goal as concurrency — they wanted something a large engineering org could actually use correctly under time pressure.
- **Callback-based async (the alternative popular at the time)** turns your code inside out — "callback hell" — and makes it very hard to reason about ordering, error handling, and cancellation. They wanted concurrent code that still *reads* like sequential code.

So the requirement wasn't "add threads" — it was: **give ordinary engineers a way to write highly concurrent, correct network services without needing to be concurrency experts, and without paying OS-thread costs.**

## Where the actual idea came from

This is the part people often miss: Go's concurrency model isn't new. It's a direct descendant of **Tony Hoare's 1978 paper "Communicating Sequential Processes" (CSP)** — and Pike had already spent decades experimenting with CSP-influenced languages at Bell Labs (Newsqueak, Alef, and the Plan 9 operating system). Go's famous slogan —

> "Don't communicate by sharing memory; share memory by communicating."

— is literally the CSP philosophy restated. Go didn't invent channels; it made a 30-year-old idea practical and mainstream by baking it into a systems language with a runtime that could make it cheap.

## Each primitive, and the specific requirement behind it

**Goroutines** — *requirement: concurrency has to be cheap enough to use liberally.* A goroutine starts with a ~2KB growable stack (not megabytes) and is scheduled by Go's own runtime, not the OS, using an M:N scheduler (many goroutines multiplexed onto few OS threads — the "GMP model"). This is *why* Kubernetes controllers can spawn a goroutine per object being reconciled without a second thought — that would be unthinkable with OS threads.

**Channels + the `go` keyword** — *requirement: goroutines need a safe way to communicate without manual locking.* Instead of "here's shared memory, protect it yourself," Go gives you a typed pipe: ownership of data transfers through the channel, so by convention only one goroutine touches a piece of data at a time. This is what let the workqueue/pipeline patterns you saw earlier exist without every function needing a mutex.

**`select`** — *requirement: real programs wait on more than one thing at once* (new work, a timeout, a shutdown signal). Once you have channels, you immediately need a way to multiplex them — CSP had this too (guarded commands), and Go surfaced it directly as a language statement rather than a library function, which is why `select` feels as natural as `switch`.

**The `sync` package (Mutex, WaitGroup, Once, atomic)** — *requirement: not everything fits the message-passing model, and Google needed both correctness and raw performance.* CSP purity is elegant but a global counter incremented a million times a second doesn't want the overhead of channel sends. The Go team was pragmatic: they kept traditional shared-memory primitives available for the hot-path cases (like the apiserver's in-flight request counter you saw), while making channels the *idiomatic default* for structuring concurrent logic.

**`context.Context`** (added ~2014, a few years after Go's public release) — *requirement: Google's internal services had grown into deep call trees of RPCs calling RPCs calling RPCs, and there was no way to say "the original client disconnected, stop all this downstream work."* Without it, goroutines quietly leaked forever waiting on work nobody needed anymore. Google had already solved this internally with a `context.Context` convention before Go was even public, and it became clear every service needed it, so it was added to the standard library. This is precisely why it's the first argument in nearly every function across Kubernetes and etcd today — it's solving the exact problem it was invented for.

**The race detector, and later, fully preemptive scheduling (Go 1.14)** — *requirement: correctness at scale needed tooling, not just discipline.* Once you have millions of goroutines running across Google's fleet, "be careful" isn't a strategy. The race detector (built on Google's ThreadSanitizer work) let teams catch data races in CI instead of production. And early Go schedulers were cooperative, meaning a tight loop with no function calls could starve other goroutines on the same OS thread — a real bug pattern found in production Go services — which is why the runtime was reworked to preempt goroutines even mid-loop.

## How this chain of requirements produced a whole ecosystem

Here's the causal chain to the "wide variety of technologies" part of your question:

1. Go made it *cheap and safe* to write software that juggles thousands of concurrent network connections, timers, and background tasks.
2. That's *exactly* the shape of problem cloud infrastructure software has: a container runtime managing many processes/streams (Docker, 2013), a coordination service handling many concurrent RPCs and consensus rounds (etcd), an orchestrator watching and reconciling thousands of objects in parallel (Kubernetes, 2014), a monitoring system scraping thousands of targets concurrently (Prometheus).
3. Docker's early success made Go the "default" choice for the next wave of infra tools being built around it — engineers already knew Go, the concurrency idioms transferred directly, and shared libraries emerged (`client-go`'s workqueue, `golang.org/x/sync/errgroup`) because everyone was solving the same reconciliation/fan-out problems.
4. That created a flywheel: the CNCF (Cloud Native Computing Foundation) ecosystem — Kubernetes, etcd, Prometheus, containerd, Helm, Terraform, CockroachDB, and dozens more — converged on Go not by coincidence but because Go's concurrency model was purpose-built for exactly the class of problem "cloud infrastructure" turned out to be: lots of independent, communicating, cancellable units of work.

So the short version: **every Go concurrency primitive exists because a specific, painful problem at Google's scale demanded it** — cheap concurrency (goroutines), safe communication (channels), waiting on multiple events (select), raw performance where needed (sync/atomic), and cancellation across deep call trees (context). And because cloud infrastructure software is fundamentally "manage huge numbers of concurrent, cancellable things," Go's answers to Google's problems turned out to be almost exactly the right answers for the entire industry's next generation of infrastructure tooling.

Kubernetes itself is interesting here because the core API server does **not** use gRPC for its main API — that's REST over HTTP with JSON or protobuf as the wire encoding. gRPC shows up specifically at the *boundaries* where Kubernetes talks to pluggable backends, and in one place underneath it all: etcd.

## 1. CRI — Container Runtime Interface (the big one)

This is the most important gRPC usage in Kubernetes. The **kubelet** doesn't talk to Docker/containerd/CRI-O directly with runtime-specific code — it speaks a standard gRPC service called CRI, over a Unix domain socket, and any runtime that implements the same `.proto` contract can plug in.

```protobuf
// simplified from k8s.io/cri-api
service RuntimeService {
  rpc RunPodSandbox(RunPodSandboxRequest) returns (RunPodSandboxResponse) {}
  rpc StopPodSandbox(StopPodSandboxRequest) returns (StopPodSandboxResponse) {}
  rpc CreateContainer(CreateContainerRequest) returns (CreateContainerResponse) {}
  rpc StartContainer(StartContainerRequest) returns (StartContainerResponse) {}
  rpc ListContainers(ListContainersRequest) returns (ListContainersResponse) {}
}

service ImageService {
  rpc PullImage(PullImageRequest) returns (PullImageResponse) {}
  rpc ListImages(ListImagesRequest) returns (ListImagesResponse) {}
}
```

Kubelet connects like this (real pattern, simplified):

```go
conn, err := grpc.Dial(
    "unix:///run/containerd/containerd.sock",
    grpc.WithTransportCredentials(insecure.NewCredentials()),
    grpc.WithContextDialer(dialer),
)
client := runtimeapi.NewRuntimeServiceClient(conn)
resp, err := client.RunPodSandbox(ctx, &runtimeapi.RunPodSandboxRequest{...})
```

**Why gRPC specifically:** before CRI existed, the kubelet had runtime-specific code baked in for Docker, then rkt, then others — every new runtime meant patching kubelet itself. Defining the contract as a `.proto` file meant: strongly-typed, versioned, language-agnostic RPCs; runtime authors implement a server, kubelet only ever knows the interface. This single decision is *why* containerd, CRI-O, and others can all work as drop-in kubelet backends today.

## 2. CSI — Container Storage Interface

Same idea, applied to storage. Volume plugins (AWS EBS, GCE PD, Ceph, Portworx, etc.) implement a gRPC service (`Identity`, `Controller`, `Node` services), and kubelet / external-attacher / external-provisioner sidecars talk to them over a Unix socket.

```protobuf
service Node {
  rpc NodeStageVolume(NodeStageVolumeRequest) returns (NodeStageVolumeResponse) {}
  rpc NodePublishVolume(NodePublishVolumeRequest) returns (NodePublishVolumeResponse) {}
}
```

Same motivation as CRI: before CSI, storage vendors had to get code merged directly into Kubernetes ("in-tree" volume plugins). gRPC + a stable interface let storage vendors ship and version their own plugins completely out-of-tree.

## 3. Device Plugins (GPUs, FPGAs, etc.)

Kubelet exposes a gRPC server, and device plugins (e.g. NVIDIA's k8s-device-plugin) *register themselves* with kubelet and then respond to `ListAndWatch`/`Allocate` RPCs so kubelet can hand specific GPUs to specific containers.

```protobuf
service DevicePlugin {
  rpc ListAndWatch(Empty) returns (stream ListAndWatchResponse) {}
  rpc Allocate(AllocateRequest) returns (AllocateResponse) {}
}
```

Notice `stream` here — this is a **server-streaming RPC**: the device plugin keeps pushing updated device health/availability to kubelet over a long-lived connection instead of kubelet having to poll. That streaming capability is something a REST/JSON API can't do cleanly, and it's a real reason gRPC was chosen over CRI/CSI's original REST alternatives that were considered.

## 4. Plugin registration (Plugin Watcher)

CSI drivers and device plugins both need to announce "I'm here, here's my socket" to kubelet. Kubelet runs a **Plugin Watcher** — itself a small gRPC service — that watches a directory for new Unix sockets and does a `GetInfo` RPC handshake to register the plugin. This is the common bootstrap mechanism both CSI and device plugins build on.

## 5. Underneath everything: etcd

The apiserver's connection to **etcd** is gRPC — etcd's v3 API (`etcdserverpb`) is defined entirely in protobuf/gRPC:

```protobuf
service KV {
  rpc Range(RangeRequest) returns (RangeResponse) {}
  rpc Put(PutRequest) returns (PutResponse) {}
  rpc Txn(TxnRequest) returns (TxnResponse) {}
}
service Watch {
  rpc Watch(stream WatchRequest) returns (stream WatchResponse) {}
}
```

That last one — `Watch` — is **bidirectional streaming**: the apiserver opens one long-lived gRPC stream to etcd and both sides keep sending messages over it (watch requests going in, change events coming out) without reopening connections. This is the literal mechanism underneath Kubernetes' entire "watch" model — when your controller does `kubectl get pods --watch` or client-go's informer streams pod updates, that's ultimately backed by an etcd gRPC stream the apiserver maintains and fans out to many HTTP watch clients.

## What the API server itself uses instead — and why that matters

The **kube-apiserver's own API** (the one `kubectl` and controllers hit) is deliberately REST-style HTTP, not gRPC, even though it supports a protobuf content-type for internal component-to-component calls (faster to marshal than JSON). The reasoning: the API needed to be usable by literally anything — `curl`, browsers, any language without a gRPC client, API gateways, `kubectl` — so ubiquity and tooling compatibility outweighed gRPC's performance/streaming advantages at that specific boundary.

## The underlying pattern

| Boundary | Protocol | Why |
|---|---|---|
| kubectl/clients ↔ apiserver | REST (HTTP+JSON, optional protobuf) | Maximum compatibility, human-debuggable, huge existing tooling |
| apiserver ↔ etcd | gRPC (bidirectional streaming) | Long-lived Watch streams, strong typing, high internal throughput |
| kubelet ↔ container runtime (CRI) | gRPC | Pluggable, versioned, language-agnostic backend contract |
| kubelet ↔ storage plugins (CSI) | gRPC | Same — vendor plugins out-of-tree |
| kubelet ↔ device plugins | gRPC (with server streaming) | Plugins push live device health without polling |

The consistent rule: **wherever Kubernetes needed a strongly-typed, versioned, pluggable contract between two pieces of infrastructure software (not a human or arbitrary client), it reached for gRPC + protobuf. Wherever the audience is "anything that speaks HTTP," it stayed with REST.**