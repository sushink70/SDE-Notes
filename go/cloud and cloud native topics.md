# Essential Cloud & Cloud Native Topics for Go Engineers

## 📚 Key Books (Go + Cloud Native)

1. **Cloud Native Go** – Matthew Titmus  
2. **Go in Action** – Kennedy, Ketelsen, Martin  
3. **Concurrency in Go** – Katherine Cox-Buday  
4. **Kubernetes Patterns** – Ibryam & Huss  
5. **Distributed Services with Go** – Travis Jeffery  
6. **Learning eBPF** – Liz Rice (Go examples)  
7. **Site Reliability Engineering** – Google  

---

## 🎯 MANDATORY TOPICS (Production Cloud Native)

### **1. Go Runtime & Concurrency Mastery**
- Goroutine scheduler (GOMAXPROCS, preemption, work stealing)
- Channel internals (buffered vs unbuffered, select, deadlock patterns)
- Context propagation (cancellation, timeouts, values)
- Memory model & happens-before guarantees
- Sync primitives: Mutex, RWMutex, WaitGroup, Once, Cond, atomic
- Worker pools & rate limiting patterns
- Graceful shutdown (signal handling, drain loops)

### **2. HTTP & Networking**
- `net/http` server internals (connection pooling, keep-alive)
- HTTP/2 multiplexing, server push
- Client configuration (timeouts, retries, exponential backoff)
- TLS 1.3 configuration & certificate management
- Load balancing strategies (round-robin, least-conn, consistent hashing)
- Service mesh concepts (Envoy, Istio, Linkerd)
- gRPC: streaming, interceptors, health checks, reflection

### **3. Observability (Three Pillars)**

**Logging:**
- Structured logging (JSON, logfmt)
- Log levels & sampling
- `slog` standard library (Go 1.21+)

**Metrics:**
- Prometheus metrics types (Counter, Gauge, Histogram, Summary)
- RED method (Rate, Errors, Duration)
- USE method (Utilization, Saturation, Errors)
- Custom exporters

**Tracing:**
- OpenTelemetry Go SDK
- Span context propagation
- Distributed tracing patterns
- Jaeger/Tempo integration

### **4. Containerization & Orchestration**

**Docker:**
- Multi-stage builds (minimize image size)
- Distroless/scratch base images
- Security: non-root users, read-only filesystems
- BuildKit & Docker Buildx

**Kubernetes:**
- Pod lifecycle & init containers
- Deployment strategies (rolling, blue/green, canary)
- ConfigMaps & Secrets management
- Resource requests/limits (CPU, memory)
- Probes: liveness, readiness, startup
- HPA (Horizontal Pod Autoscaler) & VPA
- Service types (ClusterIP, NodePort, LoadBalancer)
- Ingress controllers (nginx, traefik)
- StatefulSets & persistent volumes
- Operators & CRDs
- Network policies
- RBAC & service accounts

### **5. Distributed Systems Patterns**

**Consistency & Consensus:**
- CAP theorem practical implications
- Eventual consistency patterns
- Raft consensus (etcd internals)
- Two-phase commit vs Saga pattern

**Fault Tolerance:**
- Circuit breakers (gobreaker, hystrix-go)
- Retries with exponential backoff + jitter
- Bulkheads & rate limiting (golang.org/x/time/rate)
- Timeout budgets
- Health checks & self-healing

**Communication:**
- Request/response vs pub/sub
- At-most-once, at-least-once, exactly-once delivery
- Idempotency keys
- Message deduplication

### **6. Data Persistence**

**SQL:**
- `database/sql` connection pooling (SetMaxOpenConns, SetMaxIdleConns)
- Transactions & isolation levels
- Prepared statements
- GORM/sqlx patterns
- Query optimization & EXPLAIN

**NoSQL:**
- Redis: pipelines, pub/sub, Lua scripting
- MongoDB: aggregation pipelines
- Cassandra: partition keys, consistency levels

**Caching Strategies:**
- Cache-aside, read-through, write-through, write-behind
- TTL management
- Cache invalidation patterns

### **7. Message Queues & Event Streaming**
- Kafka: producers, consumers, consumer groups, partitions
- RabbitMQ: exchanges, queues, bindings
- NATS: subjects, queue groups, JetStream
- Event sourcing & CQRS basics

### **8. Security (Production Checklist)**
- Input validation & sanitization
- SQL injection prevention (parameterized queries)
- XSS/CSRF protection
- Secret management (Vault, Sealed Secrets)
- mTLS between services
- OWASP Top 10 awareness
- Dependency scanning (govulncheck, Trivy)
- SBOM generation

### **9. Performance & Profiling**
- pprof (CPU, memory, goroutine, mutex profiling)
- Flame graphs (go tool pprof -http)
- Benchmarking (`testing.B`, benchstat)
- Escape analysis (`-gcflags="-m"`)
- Memory pooling (sync.Pool)
- Zero-allocation techniques
- Load testing (k6, vegeta)

### **10. CI/CD & Release Engineering**
- GitOps (ArgoCD, Flux)
- Helm charts
- Semantic versioning
- Blue/green deployments
- Feature flags
- Rollback strategies
- Database migrations (golang-migrate, goose)

---

## 🧮 DATA STRUCTURES & ALGORITHMS (Go Context)

### **Core Data Structures**
```go
// Implement these from scratch:
1. Linked List (singly, doubly)
2. Stack (slice-based, linked-list-based)
3. Queue (circular buffer, channel-based)
4. Priority Queue (heap interface)
5. Hash Map (open addressing, separate chaining)
6. Binary Search Tree
7. AVL/Red-Black Tree
8. Trie (prefix tree)
9. Graph (adjacency list, adjacency matrix)
10. LRU Cache (doubly-linked list + map)
11. Bloom Filter
12. Skip List
```

### **Essential Algorithms**

**Sorting:**
- QuickSort, MergeSort, HeapSort
- Counting Sort, Radix Sort (for integers)
- TimSort concepts (Go's sort.Slice uses pdqsort)

**Searching:**
- Binary search variants
- Two pointers technique
- Sliding window

**Graph:**
- BFS, DFS (iterative & recursive)
- Dijkstra's shortest path
- Bellman-Ford
- Topological sort (Kahn's algorithm)
- Union-Find (disjoint set)

**Trees:**
- Preorder, inorder, postorder traversal
- Level-order traversal
- Lowest common ancestor

**Dynamic Programming:**
- Fibonacci, coin change, knapsack
- Longest common subsequence
- Edit distance

**String:**
- KMP pattern matching
- Rabin-Karp
- Trie-based search

### **Concurrency Algorithms**
- Producer-consumer (buffered channels)
- Fan-out/fan-in
- Pipeline pattern
- Worker pool with rate limiting
- Pub/sub with sync.Map
- Semaphore implementation (buffered channel)

---

## 🛠️ PRACTICAL PROJECTS (Progression)

### **Week 1-2: HTTP Service with Observability**
```bash
# Build a REST API with:
- OpenTelemetry tracing
- Prometheus metrics
- Structured logging
- Graceful shutdown
- Rate limiting middleware
```

### **Week 3-4: gRPC Microservice**
```bash
# Features:
- Bidirectional streaming
- Interceptors (auth, logging, metrics)
- Health checks & reflection
- Docker multi-stage build
- Kubernetes deployment
```

### **Week 5-6: Distributed Cache**
```bash
# Implement:
- Consistent hashing
- Replication (primary-replica)
- Gossip protocol for membership
- LRU eviction
- gRPC interface
```

### **Week 7-8: Event-Driven System**
```bash
# Components:
- Kafka producer/consumer
- Dead letter queue handling
- Saga pattern implementation
- Idempotency checks
- Circuit breaker integration
```

---

## 📖 LEARNING PATH (12 Weeks)

**Weeks 1-3:** Concurrency + HTTP mastery  
**Weeks 4-6:** Kubernetes + Docker deep dive  
**Weeks 7-9:** Distributed systems patterns  
**Weeks 10-12:** Observability + performance tuning  

**Daily:**
- 1 LeetCode problem (Go)
- 1 chapter from a book above
- Contribute to open-source Go cloud-native project

**Weekly:**
- Write 1 blog post on what you learned
- Review 3 PRs on GitHub (CNCF projects)

---

## 🔗 MUST-READ RESOURCES

**Articles:**
1. Go scheduler internals – Ardan Labs blog
2. Kubernetes networking demystified – Ivan Velichko
3. gRPC load balancing – gRPC blog

**Repos to Study:**
1. `kubernetes/kubernetes` – scheduler, controller patterns
2. `etcd-io/etcd` – Raft implementation
3. `grpc/grpc-go` – streaming, interceptors
4. `prometheus/client_golang` – metrics instrumentation
5. `uber-go/zap` – zero-allocation logging

**Courses:**
- Cloud Native Computing Foundation (CNCF) – CKA/CKAD path
- Go Concurrency Workshop – Ardan Labs

---

**NEXT STEPS:**  
Reply with:
1. Your current weak spots (e.g., "Kubernetes networking confuses me")
2. A specific project you want to build
3. Any production issue you're facing

I'll create a custom 4-week sprint plan with daily exercises, code reviews, and milestones.

# COMPREHENSIVE ELITE GUIDE: Go Cloud Native Deep Internals

## 🧠 PART 1: GO RUNTIME INTERNALS (Hidden Knowledge)

### **1.1 Goroutine Scheduler Deep Dive**

**Simple:** Go's scheduler multiplexes goroutines onto OS threads using a work-stealing algorithm.

**Analogy:** Imagine a restaurant with multiple chefs (OS threads) and a shared order queue. Each chef has their own prep station (P - processor), but can steal orders from other chefs when idle.

**Architecture:**
```
G (Goroutine) → M (Machine/OS Thread) → P (Processor/Context)

GMP Model:
- G: Goroutine (stack, program counter, waiting channel)
- M: OS thread (executes G)
- P: Scheduling context (local run queue, mcache for allocations)
- Sched: Global scheduler (global run queue, idle M list)
```

**Runnable Code:**
```go
// scheduler_internals.go
package main

import (
    "fmt"
    "runtime"
    "runtime/trace"
    "sync"
    "time"
)

// Demonstrate scheduler behavior
func main() {
    // Set GOMAXPROCS to see work stealing
    runtime.GOMAXPROCS(4)
    
    // Enable tracing
    trace.Start(os.Create("trace.out"))
    defer trace.Stop()
    
    var wg sync.WaitGroup
    
    // Create 100 goroutines to see work distribution
    for i := 0; i < 100; i++ {
        wg.Add(1)
        go func(id int) {
            defer wg.Done()
            
            // CPU-bound work
            sum := 0
            for j := 0; j < 1e7; j++ {
                sum += j
            }
            
            fmt.Printf("G%d on M%d P%d\n", 
                id, 
                runtime_getm(),  // Current M
                runtime_getg().m.p.id) // Current P
        }(i)
    }
    
    wg.Wait()
}

// Access internal scheduler state (use go:linkname)
//go:linkname runtime_getg runtime.getg
func runtime_getg() *g

//go:linkname runtime_getm runtime.getm  
func runtime_getm() *m
```

**Step-by-Step Internal Breakdown:**

1. **Goroutine Creation:**
   ```
   go func() {} 
   → runtime.newproc()
   → Allocate G struct (2KB stack initially)
   → Push to local P run queue (if space)
   → Or push to global run queue
   ```

2. **Scheduling Decision:**
   ```
   schedule() called every ~10ms or on blocking:
   → Check local run queue (P.runnext, P.runq)
   → If empty, steal from global queue (1/61 of time)
   → If still empty, steal from other P's (work stealing)
   → If still empty, check netpoller
   → If still empty, park M
   ```

3. **Work Stealing Algorithm:**
   ```go
   // Simplified work stealing logic
   func stealWork(p *p) *g {
       // Try half of other P's work
       for i := 0; i < 4; i++ {
           victim := &allp[fastrand() % len(allp)]
           if gp := runqsteal(p, victim, true); gp != nil {
               return gp
           }
       }
       return nil
   }
   ```

4. **Preemption Mechanisms:**
   - **Cooperative (Go < 1.14):** Check at function calls
   - **Asynchronous (Go ≥ 1.14):** Signal-based preemption every 10ms
   ```go
   // Trigger preemption
   runtime.Gosched() // Yield voluntarily
   ```

**Common Pitfalls:**

1. **Goroutine Leaks:**
   ```go
   // BAD: Goroutine never exits
   go func() {
       ch := make(chan int)
       <-ch // Blocks forever if channel never written
   }()
   
   // GOOD: Use context for cancellation
   func worker(ctx context.Context) {
       for {
           select {
           case <-ctx.Done():
               return
           case msg := <-ch:
               process(msg)
           }
       }
   }
   ```

2. **GOMAXPROCS Misconfiguration:**
   ```go
   // BAD: In containers, defaults to host CPU count
   runtime.GOMAXPROCS(runtime.NumCPU()) // Might be 96 in container with 2 CPU limit!
   
   // GOOD: Respect container limits
   import "go.uber.org/automaxprocs"
   automaxprocs.Set() // Reads cgroup limits
   ```

**Hands-On Exercises:**

1. **Scheduler Tracing:**
   ```bash
   go build -o app
   GODEBUG=schedtrace=1000 ./app
   # Output: SCHED 1000ms: gomaxprocs=4 idleprocs=2 threads=6 ...
   ```

2. **Visualize Work Stealing:**
   ```bash
   go test -trace trace.out
   go tool trace trace.out
   # View: "Goroutine analysis" → "Proc timelines"
   ```

3. **Build a Scheduler Simulator:**
   ```go
   // Implement simplified GMP model
   // Track goroutine migrations between Ps
   ```

**Further Reading:**
- Article: "Go Scheduler Internals" – Rakyll
- Repo: `golang/go/src/runtime/proc.go` (scheduler implementation)

---

### **1.2 Memory Management & Garbage Collector**

**Simple:** Go uses a concurrent, tri-color mark-and-sweep GC with write barriers.

**Analogy:** Like a librarian (GC) who marks books being read (gray), then checks referenced books (black), and discards unmarked books (white) – all while patrons keep reading.

**Memory Layout:**
```
┌─────────────────────────────────────┐
│  Stack (goroutine-local, grows)    │ ← Fast, no GC
├─────────────────────────────────────┤
│  Heap (shared, GC-managed)          │
│  ├─ Spans (8KB page groups)        │
│  ├─ MCaches (per-P caches)         │
│  └─ MCentral (per-size class)      │
└─────────────────────────────────────┘
```

**Runnable Code:**
```go
// gc_internals.go
package main

import (
    "fmt"
    "runtime"
    "runtime/debug"
    "time"
)

func main() {
    // Configure GC
    debug.SetGCPercent(100) // Default: trigger at 100% heap growth
    debug.SetMemoryLimit(500 << 20) // 500MB soft limit (Go 1.19+)
    
    // Monitor GC stats
    go func() {
        var m runtime.MemStats
        for {
            runtime.ReadMemStats(&m)
            fmt.Printf("Alloc=%vMB Sys=%vMB NumGC=%v PauseTotal=%vms\n",
                m.Alloc/1024/1024, m.Sys/1024/1024, m.NumGC, m.PauseTotalNs/1e6)
            time.Sleep(1 * time.Second)
        }
    }()
    
    // Trigger allocations
    for i := 0; i < 10; i++ {
        allocateMemory()
        time.Sleep(500 * time.Millisecond)
    }
}

func allocateMemory() {
    // Allocate 10MB
    data := make([]byte, 10<<20)
    _ = data
    // Goes out of scope → eligible for GC
}

// Force GC and print stats
func analyzeGC() {
    var before, after runtime.MemStats
    
    runtime.ReadMemStats(&before)
    runtime.GC()
    runtime.ReadMemStats(&after)
    
    fmt.Printf("Freed: %vMB\n", (before.Alloc-after.Alloc)/1024/1024)
}
```

**GC Algorithm Deep Dive:**

1. **Tri-Color Marking:**
   ```
   White: Not yet scanned (will be freed)
   Gray:  Scanned, but references not scanned
   Black: Fully scanned (kept)
   
   Process:
   1. Start: All objects white
   2. Mark roots (stack, globals) as gray
   3. Scan gray objects, mark references as gray, mark self black
   4. Repeat until no gray objects
   5. Free all white objects
   ```

2. **Write Barrier (Prevents Lost Objects):**
   ```go
   // Without write barrier:
   A (black) → B (white)
   A.ref = C (white)  // B becomes unreachable, but not marked!
   
   // With write barrier:
   func writePointer(slot *unsafe.Pointer, ptr unsafe.Pointer) {
       shade(ptr) // Mark ptr as gray if A is black
       *slot = ptr
   }
   ```

3. **GC Phases:**
   ```
   Off → Sweep Termination → Mark (STW) → Mark Assist (concurrent) 
   → Mark Termination (STW) → Sweep (concurrent) → Off
   
   STW pauses: ~100-500μs (target: <500μs)
   ```

**Escape Analysis:**
```go
// escape_analysis.go
package main

// Stack allocation (no escape)
func stackAlloc() int {
    x := 42
    return x // x doesn't escape
}

// Heap allocation (escapes)
func heapAlloc() *int {
    x := 42
    return &x // x escapes to heap
}

// Analyze with:
// go build -gcflags="-m -m" escape_analysis.go
```

**Output:**
```
./escape_analysis.go:10:2: x escapes to heap:
./escape_analysis.go:10:2:   flow: ~r0 = &x:
./escape_analysis.go:10:2:     from &x (address-of) at ./escape_analysis.go:11:9
./escape_analysis.go:10:2:     from return &x (return) at ./escape_analysis.go:11:2
```

**Memory Optimization Techniques:**

1. **Sync.Pool (Object Reuse):**
   ```go
   var bufferPool = sync.Pool{
       New: func() interface{} {
           return new(bytes.Buffer)
       },
   }
   
   func processData(data []byte) {
       buf := bufferPool.Get().(*bytes.Buffer)
       defer func() {
           buf.Reset()
           bufferPool.Put(buf)
       }()
       
       buf.Write(data)
       // Process...
   }
   ```

2. **Pre-Allocate Slices:**
   ```go
   // BAD: Multiple allocations
   var results []string
   for _, item := range items {
       results = append(results, process(item))
   }
   
   // GOOD: Single allocation
   results := make([]string, 0, len(items))
   for _, item := range items {
       results = append(results, process(item))
   }
   ```

3. **String Interning (Custom):**
   ```go
   type stringInterner struct {
       mu    sync.RWMutex
       cache map[string]string
   }
   
   func (s *stringInterner) Intern(str string) string {
       s.mu.RLock()
       if interned, ok := s.cache[str]; ok {
           s.mu.RUnlock()
           return interned
       }
       s.mu.RUnlock()
       
       s.mu.Lock()
       s.cache[str] = str
       s.mu.Unlock()
       return str
   }
   ```

**Exercises:**

1. **Measure GC Impact:**
   ```bash
   GODEBUG=gctrace=1 go run main.go
   # Output: gc 1 @0.005s 3%: 0.018+1.2+0.023 ms clock, ...
   ```

2. **Reduce Allocations:**
   ```bash
   go test -bench=. -benchmem -memprofile=mem.out
   go tool pprof -alloc_space mem.out
   ```

3. **Build Zero-Allocation JSON Parser:**
   ```go
   // Use unsafe and sync.Pool to parse without heap allocations
   ```

**Further Reading:**
- Article: "Go GC: Solving the Latency Problem" – Rick Hudson (Google)
- Repo: `golang/go/src/runtime/mgc.go`

---

### **1.3 Channel Internals**

**Simple:** Channels are thread-safe queues with sender/receiver goroutine wait lists.

**Analogy:** A pipe with a buffer. If buffer is full, senders wait. If empty, receivers wait.

**Internal Structure:**
```go
type hchan struct {
    qcount   uint           // Total data in queue
    dataqsiz uint           // Size of circular buffer
    buf      unsafe.Pointer // Circular buffer
    elemsize uint16
    closed   uint32
    sendx    uint   // Send index
    recvx    uint   // Receive index
    recvq    waitq  // List of waiting receivers (goroutines)
    sendq    waitq  // List of waiting senders
    lock     mutex  // Protects all fields
}
```

**Runnable Code:**
```go
// channel_internals.go
package main

import (
    "fmt"
    "runtime"
    "sync"
    "time"
)

func main() {
    demonstrateBuffering()
    demonstrateBlocking()
    demonstrateSelect()
}

func demonstrateBuffering() {
    // Buffered channel
    ch := make(chan int, 2)
    
    ch <- 1 // No blocking (buffer has space)
    ch <- 2 // No blocking
    // ch <- 3 // Would block! (buffer full)
    
    fmt.Println(<-ch, <-ch)
}

func demonstrateBlocking() {
    ch := make(chan int) // Unbuffered
    
    var wg sync.WaitGroup
    wg.Add(2)
    
    // Sender blocks until receiver ready
    go func() {
        defer wg.Done()
        fmt.Println("Sending...")
        ch <- 42 // Blocks here
        fmt.Println("Sent!")
    }()
    
    // Receiver blocks until sender ready
    go func() {
        defer wg.Done()
        time.Sleep(1 * time.Second)
        fmt.Println("Receiving...")
        v := <-ch // Unblocks sender
        fmt.Println("Received:", v)
    }()
    
    wg.Wait()
}

func demonstrateSelect() {
    ch1 := make(chan string)
    ch2 := make(chan string)
    
    go func() {
        time.Sleep(100 * time.Millisecond)
        ch1 <- "one"
    }()
    
    go func() {
        time.Sleep(200 * time.Millisecond)
        ch2 <- "two"
    }()
    
    for i := 0; i < 2; i++ {
        select {
        case msg1 := <-ch1:
            fmt.Println("Received", msg1)
        case msg2 := <-ch2:
            fmt.Println("Received", msg2)
        }
    }
}
```

**Send Operation Deep Dive:**
```
ch <- v

1. Lock channel
2. If recvq has waiting receivers:
   - Dequeue receiver goroutine
   - Copy v directly to receiver's stack (no buffer)
   - Wake receiver goroutine
   - Unlock and return
3. Else if buffer has space:
   - Copy v to buf[sendx]
   - sendx = (sendx + 1) % dataqsiz
   - qcount++
   - Unlock and return
4. Else (buffer full):
   - Create sudog (waiting sender)
   - Enqueue to sendq
   - Park current goroutine (gopark)
   - [Woken by receiver]
   - Unlock and return
```

**Receive Operation:**
```
v := <-ch

1. Lock channel
2. If closed and buffer empty:
   - Return zero value
3. If sendq has waiting senders:
   - If buffer empty: Copy directly from sender
   - Else: Take from buffer, copy sender's value to buffer
   - Wake sender goroutine
4. Else if buffer has data:
   - Copy buf[recvx] to v
   - recvx = (recvx + 1) % dataqsiz
   - qcount--
5. Else:
   - Park in recvq
```

**Select Internals:**
```go
// Pseudo-code for select
select {
case v := <-ch1:
case ch2 <- x:
default:
}

// Becomes:
1. Lock all channels
2. Check if any case is ready:
   - For recv: qcount > 0 or sendq not empty
   - For send: qcount < dataqsiz or recvq not empty
3. If multiple ready: random selection (fairness)
4. If default clause: execute and return
5. Else: Enqueue current G to all cases, park
6. [Woken by any case]
7. Dequeue from all other cases, execute winning case
```

**Common Pitfalls:**

1. **Goroutine Leak (No Receiver):**
   ```go
   // BAD
   func leak() {
       ch := make(chan int)
       go func() {
           ch <- 42 // Blocks forever!
       }()
   }
   
   // GOOD
   func noLeak() {
       ch := make(chan int, 1) // Buffered
       go func() {
           ch <- 42 // Won't block
       }()
   }
   ```

2. **Close Panics:**
   ```go
   // PANIC: Send on closed channel
   close(ch)
   ch <- 1
   
   // PANIC: Close of closed channel
   close(ch)
   close(ch)
   
   // OK: Receive from closed channel (returns zero value)
   close(ch)
   v, ok := <-ch // v=0, ok=false
   ```

3. **Select Deadlock:**
   ```go
   // DEADLOCK: All cases block, no default
   select {
   case <-ch1:
   case <-ch2:
   }
   // If both ch1 and ch2 never receive, deadlock!
   ```

**Advanced Patterns:**

1. **Non-Blocking Send/Recv:**
   ```go
   select {
   case ch <- value:
       fmt.Println("Sent")
   default:
       fmt.Println("Would block")
   }
   ```

2. **Timeout Pattern:**
   ```go
   select {
   case result := <-ch:
       return result
   case <-time.After(1 * time.Second):
       return errors.New("timeout")
   }
   ```

3. **Fan-In:**
   ```go
   func fanIn(chs ...<-chan int) <-chan int {
       out := make(chan int)
       var wg sync.WaitGroup
       
       for _, ch := range chs {
           wg.Add(1)
           go func(c <-chan int) {
               defer wg.Done()
               for v := range c {
                   out <- v
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

**Exercises:**

1. **Implement Semaphore with Channels:**
   ```go
   type Semaphore chan struct{}
   
   func NewSemaphore(n int) Semaphore {
       return make(chan struct{}, n)
   }
   
   func (s Semaphore) Acquire() { s <- struct{}{} }
   func (s Semaphore) Release() { <-s }
   ```

2. **Rate Limiter:**
   ```go
   func rateLimiter(rate int, burst int) <-chan time.Time {
       ticker := time.NewTicker(time.Second / time.Duration(rate))
       ch := make(chan time.Time, burst)
       
       go func() {
           for t := range ticker.C {
               select {
               case ch <- t:
               default:
               }
           }
       }()
       
       return ch
   }
   ```

3. **Bounded Worker Pool:**
   ```go
   func workerPool(jobs <-chan Job, workers int) <-chan Result {
       results := make(chan Result)
       sem := make(chan struct{}, workers)
       
       go func() {
           for job := range jobs {
               sem <- struct{}{}
               go func(j Job) {
                   defer func() { <-sem }()
                   results <- j.Process()
               }(job)
           }
           
           // Wait for all workers
           for i := 0; i < workers; i++ {
               sem <- struct{}{}
           }
           close(results)
       }()
       
       return results
   }
   ```

**Further Reading:**
- Article: "Go Channels Internals" – Jaana Dogan
- Repo: `golang/go/src/runtime/chan.go`

---

## 🔒 PART 2: ADVANCED CONCURRENCY PATTERNS

### **2.1 Memory Model & Happens-Before**

**Simple:** Go guarantees that certain operations happen before others, preventing data races.

**Analogy:** Like coordinating restaurant orders: "Cooking must happen before serving" is a happens-before relationship.

**Runnable Code:**
```go
// memory_model.go
package main

import (
    "fmt"
    "sync"
    "sync/atomic"
)

// DATA RACE EXAMPLE
var x int
var done bool

func racyCode() {
    // Goroutine 1
    go func() {
        x = 1        // Write x
        done = true  // Write done
    }()
    
    // Goroutine 2
    go func() {
        for !done {} // Spin until done (may never see true!)
        fmt.Println(x) // May print 0!
    }()
}

// FIX 1: Channel synchronization
func fixedWithChannel() {
    done := make(chan bool)
    
    go func() {
        x = 1
        done <- true // Send happens-before receive
    }()
    
    <-done // Receive guarantees x write is visible
    fmt.Println(x) // Always prints 1
}

// FIX 2: Mutex
func fixedWithMutex() {
    var mu sync.Mutex
    
    go func() {
        mu.Lock()
        x = 1
        mu.Unlock() // Unlock happens-before next Lock
    }()
    
    mu.Lock()
    fmt.Println(x) // Always prints 1
    mu.Unlock()
}

// FIX 3: Atomic operations
func fixedWithAtomic() {
    var x atomic.Int64
    var done atomic.Bool
    
    go func() {
        x.Store(1)
        done.Store(true) // Atomic store has release semantics
    }()
    
    for !done.Load() {} // Atomic load has acquire semantics
    fmt.Println(x.Load()) // Always prints 1
}
```

**Happens-Before Rules:**

1. **Initialization:**
   ```
   Package init() runs before main()
   All init() in imported packages run before importer's init()
   ```

2. **Goroutine Creation:**
   ```go
   x = 1
   go func() {
       fmt.Println(x) // Guaranteed to see 1
   }()
   ```

3. **Channel Communication:**
   ```
   Send happens-before corresponding receive completes
   Receive from unbuffered channel happens-before send completes
   Close happens-before receive that returns zero value
   ```

4. **Mutex/RWMutex:**
   ```
   Unlock happens-before next Lock
   ```

5. **Atomic Operations:**
   ```
   atomic.Store has "release" semantics
   atomic.Load has "acquire" semantics
   ```

**Common Pitfalls:**

1. **Double-Checked Locking:**
   ```go
   // WRONG (data race)
   var instance *Singleton
   
   func GetInstance() *Singleton {
       if instance == nil { // Check 1 (no lock)
           mu.Lock()
           if instance == nil { // Check 2
               instance = &Singleton{}
           }
           mu.Unlock()
       }
       return instance // May see partially initialized!
   }
   
   // RIGHT
   var (
       instance *Singleton
       once     sync.Once
   )
   
   func GetInstance() *Singleton {
       once.Do(func() {
           instance = &Singleton{}
       })
       return instance
   }
   ```

2. **Loop Variable Capture:**
   ```go
   // WRONG
   for i := 0; i < 10; i++ {
       go func() {
           fmt.Println(i) // All print 10!
       }()
   }
   
   // RIGHT
   for i := 0; i < 10; i++ {
       go func(i int) {
           fmt.Println(i)
       }(i)
   }
   ```

**Exercises:**

1. **Implement Lock-Free Stack:**
   ```go
   type LockFreeStack struct {
       head atomic.Pointer[node]
   }
   
   type node struct {
       value int
       next  *node
   }
   
   func (s *LockFreeStack) Push(value int) {
       // Use atomic.CompareAndSwap
   }
   ```

2. **Detect Data Races:**
   ```bash
   go test -race
   ```

3. **Build Sequentially Consistent Queue:**
   ```go
   // Use atomic operations for lock-free queue
   ```

---

### **2.2 Context Propagation Mastery**

**Simple:** Context carries deadlines, cancellation signals, and request-scoped values across API boundaries.

**Analogy:** Like a courier's delivery note that says "deliver by 5pm" and "cancel if customer calls."

**Runnable Code:**
```go
// context_patterns.go
package main

import (
    "context"
    "fmt"
    "time"
)

func main() {
    demonstrateCancellation()
    demonstrateTimeout()
    demonstrateValues()
}

func demonstrateCancellation() {
    ctx, cancel := context.WithCancel(context.Background())
    
    go func() {
        time.Sleep(2 * time.Second)
        cancel() // Trigger cancellation
    }()
    
    worker(ctx)
}

func worker(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            fmt.Println("Worker cancelled:", ctx.Err())
            return
        case <-time.After(500 * time.Millisecond):
            fmt.Println("Working...")
        }
    }
}

func demonstrateTimeout() {
    ctx, cancel := context.WithTimeout(context.Background(), 1*time.Second)
    defer cancel()
    
    result := make(chan string)
    
    go func() {
        time.Sleep(2 * time.Second)
        result <- "done"
    }()
    
    select {
    case <-ctx.Done():
        fmt.Println("Timeout:", ctx.Err())
    case res := <-result:
        fmt.Println("Result:", res)
    }
}

type contextKey string

const requestIDKey contextKey = "requestID"

func demonstrateValues() {
    ctx := context.WithValue(context.Background(), requestIDKey, "12345")
    
    handleRequest(ctx)
}

func handleRequest(ctx context.Context) {
    requestID := ctx.Value(requestIDKey).(string)
    fmt.Println("Handling request:", requestID)
    
    // Pass to nested calls
    fetchData(ctx)
}

func fetchData(ctx context.Context) {
    requestID := ctx.Value(requestIDKey).(string)
    fmt.Println("Fetching data for:", requestID)
}
```

**Context Internals:**
```go
type Context interface {
    Deadline() (deadline time.Time, ok bool)
    Done() <-chan struct{}
    Err() error
    Value(key interface{}) interface{}
}

// Implementation sketch
type cancelCtx struct {
    Context
    
    mu       sync.Mutex
    done     chan struct{}
    children map[canceler]struct{}
    err      error
}

func (c *cancelCtx) Done() <-chan struct{} {
    c.mu.Lock()
    if c.done == nil {
        c.done = make(chan struct{})
    }
    d := c.done
    c.mu.Unlock()
    return d
}

func (c *cancelCtx) cancel(removeFromParent bool, err error) {
    c.mu.Lock()
    if c.err != nil {
        c.mu.Unlock()
        return // Already cancelled
    }
    c.err = err
    if c.done == nil {
        c.done = closedchan
    } else {
        close(c.done) // Wake all waiters
    }
    for child := range c.children {
        child.cancel(false, err) // Propagate to children
    }
    c.children = nil
    c.mu.Unlock()
    
    if removeFromParent {
        removeChild(c.Context, c)
    }
}
```

**Best Practices:**

1. **Always Pass Context as First Parameter:**
   ```go
   func ProcessData(ctx context.Context, data []byte) error
   ```

2. **Never Store Context in Structs:**
   ```go
   // WRONG
   type Server struct {
       ctx context.Context
   }
   
   // RIGHT
   func (s *Server) Handle(ctx context.Context, req *Request)
   ```

3. **Use context.TODO() When Unsure:**
   ```go
   // During refactoring
   func legacyFunction() {
       ctx := context.TODO()
       newFunction(ctx)
   }
   ```

**Advanced Patterns:**

1. **Merge Multiple Contexts:**
   ```go
   func MergeContexts(ctx1, ctx2 context.Context) (context.Context, context.CancelFunc) {
       ctx, cancel := context.WithCancel(context.Background())
       
       go func() {
           select {
           case <-ctx1.Done():
               cancel()
           case <-ctx2.Done():
               cancel()
           case <-ctx.Done():
           }
       }()
       
       return ctx, cancel
   }
   ```

2. **Detached Context (Survive Parent Cancellation):**
   ```go
   func DetachedContext(ctx context.Context) context.Context {
       return detachedContext{ctx}
   }
   
   type detachedContext struct {
       context.Context
   }
   
   func (detachedContext) Done() <-chan struct{} {
       return nil // Never cancelled
   }
   
   func (detachedContext) Err() error {
       return nil
   }
   ```

3. **Context with Cause (Go 1.20+):**
   ```go
   ctx, cancel := context.WithCancelCause(context.Background())
   
   cancel(fmt.Errorf("user initiated cancellation"))
   
   err := context.Cause(ctx)
   // err = "user initiated cancellation"
   ```

**Exercises:**

1. **Build HTTP Client with Context:**
   ```go
   func FetchWithContext(ctx context.Context, url string) ([]byte, error) {
       req, _ := http.NewRequestWithContext(ctx, "GET", url, nil)
       // ...
   }
   ```

2. **Implement Retry with Backoff:**
   ```go
   func RetryWithBackoff(ctx context.Context, fn func() error) error {
       backoff := time.Second
       for {
           if err := fn(); err == nil {
               return nil
           }
           
           select {
           case <-ctx.Done():
               return ctx.Err()
           case <-time.After(backoff):
               backoff *= 2
           }
       }
   }
   ```

**Further Reading:**
- Article: "Context Propagation Best Practices" – Jack Lindamood
- Repo: `golang/go/src/context/context.go`

---

**[CONTINUED IN NEXT PART - THIS IS 1/4 OF THE COMPREHENSIVE GUIDE]**

Should I continue with:
- **Part 3:** Kubernetes Deep Internals (Scheduler, Networking, Storage)
- **Part 4:** Distributed Systems (Consensus, Replication, Partitioning)
- **Part 5:** Performance Engineering (Profiling, Optimization, Benchmarking)
- **Part 6:** Production Systems (Observability, Security, Incident Response)

Reply with which part you want next, or "continue all" for the complete guide.

# PART 3: KUBERNETES DEEP INTERNALS

## 🎯 3.1 KUBERNETES SCHEDULER INTERNALS

### **Simple Explanation**
The scheduler watches for unassigned pods and selects the best node based on filtering (remove unsuitable nodes) and scoring (rank remaining nodes).

### **Analogy**
Like a hotel manager assigning guests to rooms: first eliminate rooms that don't meet requirements (non-smoking, wheelchair accessible), then rank remaining rooms by amenities and price.

### **Architecture**
```
┌─────────────────────────────────────────────────────────┐
│                    Scheduling Cycle                      │
├─────────────────────────────────────────────────────────┤
│ 1. Queue Sort (Priority)                                │
│ 2. PreFilter (early checks)                             │
│ 3. Filter (predicates - node feasibility)               │
│ 4. PostFilter (if all nodes filtered out)               │
│ 5. PreScore (prepare scoring)                           │
│ 6. Score (rank nodes 0-100)                             │
│ 7. NormalizeScore (normalize across plugins)            │
│ 8. Reserve (claim resources)                            │
│ 9. Permit (final approval)                              │
│ 10. PreBind (setup before binding)                      │
│ 11. Bind (assign pod to node)                           │
│ 12. PostBind (cleanup)                                  │
└─────────────────────────────────────────────────────────┘
```

### **Runnable Code: Custom Scheduler**

```go
// custom-scheduler/main.go
package main

import (
    "context"
    "fmt"
    "math/rand"
    "time"

    corev1 "k8s.io/api/core/v1"
    metav1 "k8s.io/apimachinery/pkg/apis/meta/v1"
    "k8s.io/apimachinery/pkg/labels"
    "k8s.io/client-go/informers"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/rest"
    "k8s.io/client-go/tools/cache"
)

const schedulerName = "custom-scheduler"

type Scheduler struct {
    clientset  *kubernetes.Clientset
    podQueue   chan *corev1.Pod
    nodeLister cache.Indexer
}

func main() {
    config, err := rest.InClusterConfig()
    if err != nil {
        panic(err)
    }

    clientset, err := kubernetes.NewForConfig(config)
    if err != nil {
        panic(err)
    }

    scheduler := &Scheduler{
        clientset: clientset,
        podQueue:  make(chan *corev1.Pod, 100),
    }

    // Setup informers
    factory := informers.NewSharedInformerFactory(clientset, 10*time.Minute)

    // Watch pods
    podInformer := factory.Core().V1().Pods().Informer()
    podInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc: func(obj interface{}) {
            pod := obj.(*corev1.Pod)
            if pod.Spec.SchedulerName == schedulerName && pod.Spec.NodeName == "" {
                scheduler.podQueue <- pod
            }
        },
    })

    // Watch nodes
    nodeInformer := factory.Core().V1().Nodes().Informer()
    scheduler.nodeLister = nodeInformer.GetIndexer()

    // Start informers
    stopCh := make(chan struct{})
    defer close(stopCh)
    factory.Start(stopCh)
    factory.WaitForCacheSync(stopCh)

    // Start scheduling loop
    scheduler.Run(stopCh)
}

func (s *Scheduler) Run(stopCh <-chan struct{}) {
    fmt.Println("Starting custom scheduler...")
    
    for {
        select {
        case pod := <-s.podQueue:
            s.schedulePod(pod)
        case <-stopCh:
            return
        }
    }
}

func (s *Scheduler) schedulePod(pod *corev1.Pod) {
    ctx := context.Background()
    
    fmt.Printf("Scheduling pod: %s/%s\n", pod.Namespace, pod.Name)

    // 1. FILTERING PHASE
    nodes, err := s.clientset.CoreV1().Nodes().List(ctx, metav1.ListOptions{})
    if err != nil {
        fmt.Printf("Error listing nodes: %v\n", err)
        return
    }

    feasibleNodes := s.filterNodes(pod, nodes.Items)
    if len(feasibleNodes) == 0 {
        fmt.Printf("No feasible nodes for pod %s\n", pod.Name)
        s.emitEvent(pod, "FailedScheduling", "No nodes available")
        return
    }

    // 2. SCORING PHASE
    bestNode := s.scoreNodes(pod, feasibleNodes)

    // 3. BINDING PHASE
    if err := s.bindPod(pod, bestNode); err != nil {
        fmt.Printf("Failed to bind pod: %v\n", err)
        return
    }

    fmt.Printf("Successfully scheduled %s to %s\n", pod.Name, bestNode.Name)
    s.emitEvent(pod, "Scheduled", fmt.Sprintf("Assigned to %s", bestNode.Name))
}

// FILTER PHASE: Remove unsuitable nodes
func (s *Scheduler) filterNodes(pod *corev1.Pod, nodes []corev1.Node) []corev1.Node {
    var feasible []corev1.Node

    for _, node := range nodes {
        // Check 1: Node ready?
        if !s.isNodeReady(node) {
            continue
        }

        // Check 2: Node has enough resources?
        if !s.hasEnoughResources(node, pod) {
            continue
        }

        // Check 3: Node selector match?
        if !s.matchesNodeSelector(node, pod) {
            continue
        }

        // Check 4: Taints/Tolerations?
        if !s.toleratesTaints(node, pod) {
            continue
        }

        // Check 5: Affinity/Anti-affinity?
        if !s.satisfiesAffinity(node, pod) {
            continue
        }

        feasible = append(feasible, node)
    }

    return feasible
}

func (s *Scheduler) isNodeReady(node corev1.Node) bool {
    for _, condition := range node.Status.Conditions {
        if condition.Type == corev1.NodeReady {
            return condition.Status == corev1.ConditionTrue
        }
    }
    return false
}

func (s *Scheduler) hasEnoughResources(node corev1.Node, pod *corev1.Pod) bool {
    // Get allocatable resources
    allocatable := node.Status.Allocatable
    
    // Calculate requested resources
    var requestedCPU, requestedMemory int64
    for _, container := range pod.Spec.Containers {
        requestedCPU += container.Resources.Requests.Cpu().MilliValue()
        requestedMemory += container.Resources.Requests.Memory().Value()
    }

    availableCPU := allocatable.Cpu().MilliValue()
    availableMemory := allocatable.Memory().Value()

    // Get pods already on node
    podList, _ := s.clientset.CoreV1().Pods(corev1.NamespaceAll).List(
        context.Background(),
        metav1.ListOptions{
            FieldSelector: fmt.Sprintf("spec.nodeName=%s", node.Name),
        },
    )

    // Calculate used resources
    var usedCPU, usedMemory int64
    for _, p := range podList.Items {
        for _, container := range p.Spec.Containers {
            usedCPU += container.Resources.Requests.Cpu().MilliValue()
            usedMemory += container.Resources.Requests.Memory().Value()
        }
    }

    // Check if node has enough
    return (availableCPU-usedCPU) >= requestedCPU && 
           (availableMemory-usedMemory) >= requestedMemory
}

func (s *Scheduler) matchesNodeSelector(node corev1.Node, pod *corev1.Pod) bool {
    if pod.Spec.NodeSelector == nil {
        return true
    }

    nodeLabels := labels.Set(node.Labels)
    selector := labels.SelectorFromSet(pod.Spec.NodeSelector)
    
    return selector.Matches(nodeLabels)
}

func (s *Scheduler) toleratesTaints(node corev1.Node, pod *corev1.Pod) bool {
    for _, taint := range node.Spec.Taints {
        // Skip if taint has no effect
        if taint.Effect == "" {
            continue
        }

        tolerated := false
        for _, toleration := range pod.Spec.Tolerations {
            if toleration.ToleratesTaint(&taint) {
                tolerated = true
                break
            }
        }

        // If critical taint not tolerated, reject node
        if !tolerated && (taint.Effect == corev1.TaintEffectNoSchedule ||
            taint.Effect == corev1.TaintEffectNoExecute) {
            return false
        }
    }
    return true
}

func (s *Scheduler) satisfiesAffinity(node corev1.Node, pod *corev1.Pod) bool {
    // Simplified - real implementation is complex
    // Check pod affinity, pod anti-affinity, node affinity
    return true
}

// SCORING PHASE: Rank nodes 0-100
func (s *Scheduler) scoreNodes(pod *corev1.Pod, nodes []corev1.Node) corev1.Node {
    type nodeScore struct {
        node  corev1.Node
        score int
    }

    scores := make([]nodeScore, len(nodes))

    for i, node := range nodes {
        score := 0

        // Plugin 1: LeastResourceAllocation (prefer nodes with more free resources)
        score += s.scoreLeastResourceAllocation(node, pod)

        // Plugin 2: BalancedResourceAllocation (prefer balanced CPU/memory usage)
        score += s.scoreBalancedAllocation(node, pod)

        // Plugin 3: NodeResourcesFit (how well resources fit)
        score += s.scoreNodeResourcesFit(node, pod)

        // Plugin 4: ImageLocality (prefer nodes with images already pulled)
        score += s.scoreImageLocality(node, pod)

        scores[i] = nodeScore{node: node, score: score}
    }

    // Find highest score
    best := scores[0]
    for _, ns := range scores[1:] {
        if ns.score > best.score {
            best = ns
        } else if ns.score == best.score {
            // Tie-breaker: random selection
            if rand.Float32() < 0.5 {
                best = ns
            }
        }
    }

    return best.node
}

func (s *Scheduler) scoreLeastResourceAllocation(node corev1.Node, pod *corev1.Pod) int {
    allocatable := node.Status.Allocatable
    
    cpuCapacity := allocatable.Cpu().MilliValue()
    memCapacity := allocatable.Memory().Value()

    // Get used resources (simplified)
    podList, _ := s.clientset.CoreV1().Pods(corev1.NamespaceAll).List(
        context.Background(),
        metav1.ListOptions{FieldSelector: fmt.Sprintf("spec.nodeName=%s", node.Name)},
    )

    var usedCPU, usedMemory int64
    for _, p := range podList.Items {
        for _, c := range p.Spec.Containers {
            usedCPU += c.Resources.Requests.Cpu().MilliValue()
            usedMemory += c.Resources.Requests.Memory().Value()
        }
    }

    // Calculate free percentage
    cpuFree := float64(cpuCapacity-usedCPU) / float64(cpuCapacity) * 100
    memFree := float64(memCapacity-usedMemory) / float64(memCapacity) * 100

    // Average of free percentages
    return int((cpuFree + memFree) / 2)
}

func (s *Scheduler) scoreBalancedAllocation(node corev1.Node, pod *corev1.Pod) int {
    // Prefer nodes where CPU/Memory usage will be balanced after scheduling
    // Return 0-100 based on how balanced the allocation would be
    return 50 // Simplified
}

func (s *Scheduler) scoreNodeResourcesFit(node corev1.Node, pod *corev1.Pod) int {
    // Score based on how well the pod fits on the node
    return 50 // Simplified
}

func (s *Scheduler) scoreImageLocality(node corev1.Node, pod *corev1.Pod) int {
    // Prefer nodes that already have container images
    score := 0
    for _, container := range pod.Spec.Containers {
        for _, image := range node.Status.Images {
            for _, name := range image.Names {
                if name == container.Image {
                    score += 10
                }
            }
        }
    }
    return min(score, 100)
}

// BINDING PHASE
func (s *Scheduler) bindPod(pod *corev1.Pod, node corev1.Node) error {
    binding := &corev1.Binding{
        ObjectMeta: metav1.ObjectMeta{
            Name:      pod.Name,
            Namespace: pod.Namespace,
        },
        Target: corev1.ObjectReference{
            Kind: "Node",
            Name: node.Name,
        },
    }

    return s.clientset.CoreV1().Pods(pod.Namespace).Bind(
        context.Background(),
        binding,
        metav1.CreateOptions{},
    )
}

func (s *Scheduler) emitEvent(pod *corev1.Pod, reason, message string) {
    event := &corev1.Event{
        ObjectMeta: metav1.ObjectMeta{
            Name:      fmt.Sprintf("%s.%x", pod.Name, time.Now().UnixNano()),
            Namespace: pod.Namespace,
        },
        InvolvedObject: corev1.ObjectReference{
            Kind:      "Pod",
            Name:      pod.Name,
            Namespace: pod.Namespace,
            UID:       pod.UID,
        },
        Reason:  reason,
        Message: message,
        Source: corev1.EventSource{
            Component: schedulerName,
        },
        FirstTimestamp: metav1.Now(),
        LastTimestamp:  metav1.Now(),
        Count:          1,
        Type:           corev1.EventTypeNormal,
    }

    s.clientset.CoreV1().Events(pod.Namespace).Create(
        context.Background(),
        event,
        metav1.CreateOptions{},
    )
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}
```

### **Deployment Manifests**

```yaml
# deployment.yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: custom-scheduler
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: custom-scheduler
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: system:kube-scheduler
subjects:
- kind: ServiceAccount
  name: custom-scheduler
  namespace: kube-system
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: custom-scheduler
  namespace: kube-system
spec:
  replicas: 1
  selector:
    matchLabels:
      component: custom-scheduler
  template:
    metadata:
      labels:
        component: custom-scheduler
    spec:
      serviceAccountName: custom-scheduler
      containers:
      - name: scheduler
        image: custom-scheduler:latest
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi
```

```yaml
# test-pod.yaml
apiVersion: v1
kind: Pod
metadata:
  name: test-pod
spec:
  schedulerName: custom-scheduler  # Use our custom scheduler
  containers:
  - name: nginx
    image: nginx
    resources:
      requests:
        cpu: 100m
        memory: 128Mi
```

### **Build & Deploy**

```bash
# Dockerfile
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -o scheduler main.go

FROM alpine:latest
RUN apk --no-cache add ca-certificates
COPY --from=builder /app/scheduler /scheduler
ENTRYPOINT ["/scheduler"]
```

```bash
# Build and deploy
docker build -t custom-scheduler:latest .
docker push your-registry/custom-scheduler:latest

kubectl apply -f deployment.yaml
kubectl apply -f test-pod.yaml

# Watch scheduling
kubectl get events --watch | grep custom-scheduler
kubectl logs -n kube-system -l component=custom-scheduler -f
```

---

## 🌐 3.2 KUBERNETES NETWORKING DEEP DIVE

### **Simple Explanation**
Kubernetes networking ensures: (1) pod-to-pod communication without NAT, (2) nodes can talk to pods, (3) pods see their own IP.

### **Analogy**
Like a giant office building where every room (pod) has a direct phone line (IP) that anyone can dial without going through a switchboard (NAT).

### **Network Model Architecture**

```
┌────────────────────────────────────────────────────────────┐
│                    Kubernetes Network                       │
├────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────┐         ┌─────────────┐                   │
│  │   Node 1    │         │   Node 2    │                   │
│  │             │         │             │                   │
│  │  ┌───────┐  │         │  ┌───────┐  │                   │
│  │  │ Pod A │  │         │  │ Pod C │  │                   │
│  │  │10.1.1.2│◄─┼────────►│  │10.1.2.3│  │                   │
│  │  └───┬───┘  │         │  └───────┘  │                   │
│  │      │      │         │             │                   │
│  │  ┌───▼───┐  │         │             │                   │
│  │  │ Pod B │  │         │             │                   │
│  │  │10.1.1.3│  │         │             │                   │
│  │  └───────┘  │         │             │                   │
│  │      │      │         │      │      │                   │
│  │   ┌──▼────┐ │         │   ┌──▼────┐ │                   │
│  │   │ cni0  │ │         │   │ cni0  │ │                   │
│  │   │bridge │ │         │   │bridge │ │                   │
│  │   └───┬───┘ │         │   └───┬───┘ │                   │
│  │       │     │         │       │     │                   │
│  │   ┌───▼───┐ │         │   ┌───▼───┐ │                   │
│  │   │ eth0  │ │         │   │ eth0  │ │                   │
│  │   │192... │ │         │   │192... │ │                   │
│  └───┴───┬───┴─┘         └───┴───┬───┴─┘                   │
│          │                       │                         │
│          └───────────┬───────────┘                         │
│                      │                                     │
│              ┌───────▼────────┐                            │
│              │   Underlay     │                            │
│              │   Network      │                            │
│              └────────────────┘                            │
└────────────────────────────────────────────────────────────┘
```

### **CNI Plugin Implementation**

```go
// simple-cni/main.go
package main

import (
    "encoding/json"
    "fmt"
    "net"
    "os"
    "runtime"

    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/types"
    current "github.com/containernetworking/cni/pkg/types/100"
    "github.com/containernetworking/cni/pkg/version"
    "github.com/containernetworking/plugins/pkg/ip"
    "github.com/containernetworking/plugins/pkg/ns"
    "github.com/vishvananda/netlink"
)

type NetConf struct {
    types.NetConf
    Bridge string `json:"bridge"`
    Subnet string `json:"subnet"`
}

func init() {
    runtime.LockOSThread()
}

func main() {
    skel.PluginMain(cmdAdd, cmdCheck, cmdDel, version.All, "simple-cni v0.1.0")
}

// ADD: Setup networking for container
func cmdAdd(args *skel.CmdArgs) error {
    // 1. Parse config
    conf := NetConf{}
    if err := json.Unmarshal(args.StdinData, &conf); err != nil {
        return fmt.Errorf("failed to parse config: %v", err)
    }

    // 2. Create bridge if doesn't exist
    br, err := setupBridge(conf.Bridge)
    if err != nil {
        return err
    }

    // 3. Get network namespace
    netns, err := ns.GetNS(args.Netns)
    if err != nil {
        return err
    }
    defer netns.Close()

    // 4. Allocate IP address
    ipAddr, gateway, err := allocateIP(conf.Subnet)
    if err != nil {
        return err
    }

    // 5. Create veth pair
    hostVeth, containerVeth, err := createVethPair(args.IfName)
    if err != nil {
        return err
    }

    // 6. Attach host side to bridge
    if err := attachVethToBridge(hostVeth, br); err != nil {
        return err
    }

    // 7. Move container side to netns and configure
    if err := netns.Do(func(_ ns.NetNS) error {
        // Move veth to container namespace
        contVeth, err := netlink.LinkByName(containerVeth)
        if err != nil {
            return err
        }

        // Rename to eth0
        if err := netlink.LinkSetName(contVeth, args.IfName); err != nil {
            return err
        }

        // Assign IP address
        addr, err := netlink.ParseAddr(ipAddr)
        if err != nil {
            return err
        }
        if err := netlink.AddrAdd(contVeth, addr); err != nil {
            return err
        }

        // Bring up interface
        if err := netlink.LinkSetUp(contVeth); err != nil {
            return err
        }

        // Add default route
        gw := net.ParseIP(gateway)
        defaultRoute := &netlink.Route{
            LinkIndex: contVeth.Attrs().Index,
            Gw:        gw,
            Dst:       nil, // Default route
        }
        if err := netlink.RouteAdd(defaultRoute); err != nil {
            return err
        }

        return nil
    }); err != nil {
        return err
    }

    // 8. Enable IP forwarding on host
    if err := enableIPForwarding(); err != nil {
        return err
    }

    // 9. Setup iptables rules for NAT
    if err := setupIPTables(conf.Subnet); err != nil {
        return err
    }

    // 10. Return result
    result := &current.Result{
        CNIVersion: current.ImplementedSpecVersion,
        IPs: []*current.IPConfig{{
            Address: net.IPNet{
                IP:   net.ParseIP(ipAddr),
                Mask: net.CIDRMask(24, 32),
            },
            Gateway: net.ParseIP(gateway),
        }},
    }

    return types.PrintResult(result, conf.CNIVersion)
}

func setupBridge(bridgeName string) (*netlink.Bridge, error) {
    // Check if bridge exists
    br, err := netlink.LinkByName(bridgeName)
    if err == nil {
        return br.(*netlink.Bridge), nil
    }

    // Create bridge
    bridge := &netlink.Bridge{
        LinkAttrs: netlink.LinkAttrs{
            Name: bridgeName,
        },
    }

    if err := netlink.LinkAdd(bridge); err != nil {
        return nil, fmt.Errorf("failed to create bridge: %v", err)
    }

    // Assign IP to bridge
    addr, _ := netlink.ParseAddr("10.244.0.1/24")
    if err := netlink.AddrAdd(bridge, addr); err != nil {
        return nil, err
    }

    // Bring up bridge
    if err := netlink.LinkSetUp(bridge); err != nil {
        return nil, err
    }

    return bridge, nil
}

func allocateIP(subnet string) (string, string, error) {
    // Simplified: In production, use IPAM plugin
    // For demo, just assign .2
    return "10.244.0.2/24", "10.244.0.1", nil
}

func createVethPair(containerIfName string) (string, string, error) {
    hostVethName := "veth" + containerIfName
    containerVethName := "tmp" + containerIfName

    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{
            Name: hostVethName,
        },
        PeerName: containerVethName,
    }

    if err := netlink.LinkAdd(veth); err != nil {
        return "", "", err
    }

    // Bring up host side
    hostVeth, err := netlink.LinkByName(hostVethName)
    if err != nil {
        return "", "", err
    }
    if err := netlink.LinkSetUp(hostVeth); err != nil {
        return "", "", err
    }

    return hostVethName, containerVethName, nil
}

func attachVethToBridge(vethName string, bridge *netlink.Bridge) error {
    veth, err := netlink.LinkByName(vethName)
    if err != nil {
        return err
    }

    return netlink.LinkSetMaster(veth, bridge)
}

func enableIPForwarding() error {
    return os.WriteFile("/proc/sys/net/ipv4/ip_forward", []byte("1"), 0644)
}

func setupIPTables(subnet string) error {
    // Add SNAT rule for outgoing traffic
    // iptables -t nat -A POSTROUTING -s <subnet> ! -o cni0 -j MASQUERADE
    
    // Simplified - use github.com/coreos/go-iptables/iptables in production
    return nil
}

// DEL: Teardown networking
func cmdDel(args *skel.CmdArgs) error {
    conf := NetConf{}
    if err := json.Unmarshal(args.StdinData, &conf); err != nil {
        return err
    }

    // Get network namespace
    netns, err := ns.GetNS(args.Netns)
    if err != nil {
        return nil // Namespace might be gone already
    }
    defer netns.Close()

    // Delete veth pair
    return netns.Do(func(_ ns.NetNS) error {
        link, err := netlink.LinkByName(args.IfName)
        if err != nil {
            return nil // Interface might be gone
        }
        return netlink.LinkDel(link)
    })
}

// CHECK: Verify networking is still working
func cmdCheck(args *skel.CmdArgs) error {
    // Verify interface exists and has IP
    return nil
}
```

### **CNI Configuration**

```json
{
  "cniVersion": "1.0.0",
  "name": "simple-cni",
  "type": "simple-cni",
  "bridge": "cni0",
  "subnet": "10.244.0.0/16",
  "ipam": {
    "type": "host-local",
    "subnet": "10.244.0.0/16",
    "routes": [
      { "dst": "0.0.0.0/0" }
    ]
  }
}
```

---

### **Service & Kube-Proxy Deep Dive**

**Service Types:**
```
ClusterIP: Internal cluster IP (default)
NodePort: Exposes on each node's IP at a static port
LoadBalancer: External load balancer (cloud provider)
ExternalName: DNS CNAME record
```

**Kube-Proxy Modes:**

```go
// iptables mode (simplified implementation)
package main

import (
    "fmt"
    
    corev1 "k8s.io/api/core/v1"
    "k8s.io/client-go/informers"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/cache"
)

type ProxyServer struct {
    clientset *kubernetes.Clientset
}

func (p *ProxyServer) Run() {
    factory := informers.NewSharedInformerFactory(p.clientset, 0)
    
    // Watch services
    serviceInformer := factory.Core().V1().Services().Informer()
    serviceInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc:    p.onServiceAdd,
        UpdateFunc: p.onServiceUpdate,
        DeleteFunc: p.onServiceDelete,
    })
    
    // Watch endpoints
    endpointsInformer := factory.Core().V1().Endpoints().Informer()
    endpointsInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc:    p.onEndpointsAdd,
        UpdateFunc: p.onEndpointsUpdate,
        DeleteFunc: p.onEndpointsDelete,
    })
    
    factory.Start(nil)
    select {}
}

func (p *ProxyServer) onServiceAdd(obj interface{}) {
    svc := obj.(*corev1.Service)
    p.syncService(svc)
}

func (p *ProxyServer) syncService(svc *corev1.Service) {
    // Generate iptables rules for service
    
    clusterIP := svc.Spec.ClusterIP
    
    for _, port := range svc.Spec.Ports {
        // 1. Create chain for this service
        chainName := fmt.Sprintf("KUBE-SVC-%s-%s-%d", 
            svc.Namespace, svc.Name, port.Port)
        
        // iptables -t nat -N <chainName>
        
        // 2. Jump to chain from KUBE-SERVICES
        // iptables -t nat -A KUBE-SERVICES \
        //   -d <clusterIP>/32 -p tcp --dport <port> \
        //   -j <chainName>
        
        // 3. Get endpoints
        endpoints := p.getEndpoints(svc.Namespace, svc.Name)
        
        // 4. Create rules for each endpoint (load balancing)
        for i, ep := range endpoints {
            probability := 1.0 / float64(len(endpoints)-i)
            
            // iptables -t nat -A <chainName> \
            //   -m statistic --mode random --probability <prob> \
            //   -j KUBE-SEP-<endpoint-hash>
            
            // Create endpoint chain
            // iptables -t nat -N KUBE-SEP-<hash>
            // iptables -t nat -A KUBE-SEP-<hash> \
            //   -p tcp -j DNAT --to-destination <endpoint-ip>:<port>
            
            fmt.Printf("Rule: %s -> %s (prob: %.2f)\n", 
                chainName, ep, probability)
        }
    }
}

func (p *ProxyServer) getEndpoints(namespace, name string) []string {
    // Fetch endpoints for service
    return []string{"10.244.1.2:80", "10.244.2.3:80"}
}

func (p *ProxyServer) onServiceUpdate(oldObj, newObj interface{}) {
    p.syncService(newObj.(*corev1.Service))
}

func (p *ProxyServer) onServiceDelete(obj interface{}) {
    svc := obj.(*corev1.Service)
    // Delete iptables rules
    fmt.Printf("Deleting rules for service: %s/%s\n", svc.Namespace, svc.Name)
}

func (p *ProxyServer) onEndpointsAdd(obj interface{}) {
    ep := obj.(*corev1.Endpoints)
    p.syncEndpoints(ep)
}

func (p *ProxyServer) syncEndpoints(ep *corev1.Endpoints) {
    // Update iptables rules when endpoints change
    fmt.Printf("Syncing endpoints for: %s/%s\n", ep.Namespace, ep.Name)
}

func (p *ProxyServer) onEndpointsUpdate(oldObj, newObj interface{}) {
    p.syncEndpoints(newObj.(*corev1.Endpoints))
}

func (p *ProxyServer) onEndpointsDelete(obj interface{}) {
    ep := obj.(*corev1.Endpoints)
    fmt.Printf("Endpoints deleted: %s/%s\n", ep.Namespace, ep.Name)
}
```

**Generated iptables rules example:**
```bash
# Service ClusterIP rule
iptables -t nat -A KUBE-SERVICES -d 10.96.0.10/32 -p tcp --dport 80 \
  -j KUBE-SVC-ABCD1234

# Load balancing across endpoints (probability-based)
iptables -t nat -A KUBE-SVC-ABCD1234 \
  -m statistic --mode random --probability 0.5 \
  -j KUBE-SEP-ENDPOINT1

iptables -t nat -A KUBE-SVC-ABCD1234 \
  -j KUBE-SEP-ENDPOINT2

# DNAT to actual pod
iptables -t nat -A KUBE-SEP-ENDPOINT1 \
  -p tcp -j DNAT --to-destination 10.244.1.2:80

iptables -t nat -A KUBE-SEP-ENDPOINT2 \
  -p tcp -j DNAT --to-destination 10.244.2.3:80
```

**Common Pitfalls:**

1. **Pod-to-Service connectivity issues:**
   ```bash
   # Debug: Check if service has endpoints
   kubectl get endpoints <service-name>
   
   # Check iptables rules
   iptables-save | grep <service-name>
   
   # Test from pod
   kubectl exec -it <pod> -- curl <service-ip>:<port>
   ```

2. **ExternalTrafficPolicy: Local vs Cluster:**
   ```yaml
   # Local: Preserves source IP, but uneven load distribution
   spec:
     externalTrafficPolicy: Local
   
   # Cluster: Load balanced, but loses source IP (SNAT)
   spec:
     externalTrafficPolicy: Cluster
   ```

3. **DNS resolution delays:**
   ```go
   // Set DNS cache TTL
   import "net"
   
   r := &net.Resolver{
       PreferGo: true,
       Dial: func(ctx context.Context, network, address string) (net.Conn, error) {
           d := net.Dialer{Timeout: 1 * time.Second}
           return d.DialContext(ctx, network, "10.96.0.10:53") // CoreDNS
       },
   }
   ```

---

### **Network Policies Implementation**

```yaml
# Network policy example
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  podSelector:
    matchLabels:
      app: backend
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: frontend
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: database
    ports:
    - protocol: TCP
      port: 5432
```

```go
// Network policy controller (simplified)
package main

import (
    "fmt"
    
    networkingv1 "k8s.io/api/networking/v1"
    "k8s.io/client-go/informers"
    "k8s.io/client-go/kubernetes"
    "k8s.io/client-go/tools/cache"
)

type NetworkPolicyController struct {
    clientset *kubernetes.Clientset
}

func (c *NetworkPolicyController) Run() {
    factory := informers.NewSharedInformerFactory(c.clientset, 0)
    
    npInformer := factory.Networking().V1().NetworkPolicies().Informer()
    npInformer.AddEventHandler(cache.ResourceEventHandlerFuncs{
        AddFunc:    c.onNetworkPolicyAdd,
        UpdateFunc: c.onNetworkPolicyUpdate,
        DeleteFunc: c.onNetworkPolicyDelete,
    })
    
    factory.Start(nil)
    select {}
}

func (c *NetworkPolicyController) onNetworkPolicyAdd(obj interface{}) {
    np := obj.(*networkingv1.NetworkPolicy)
    c.syncNetworkPolicy(np)
}

func (c *NetworkPolicyController) syncNetworkPolicy(np *networkingv1.NetworkPolicy) {
    // Convert to iptables/eBPF rules
    
    fmt.Printf("Syncing NetworkPolicy: %s/%s\n", np.Namespace, np.Name)
    
    // 1. Get pods matching podSelector
    pods := c.getMatchingPods(np.Namespace, np.Spec.PodSelector.MatchLabels)
    
    for _, pod := range pods {
        // 2. Create iptables chains for this pod
        chainName := fmt.Sprintf("NP-%s-%s", np.Name, pod.Name)
        
        // 3. Default deny
        // iptables -A <chainName> -j DROP
        
        // 4. Process ingress rules
        for _, ingress := range np.Spec.Ingress {
            for _, from := range ingress.From {
                if from.PodSelector != nil {
                    // Allow from specific pods
                    sourcePods := c.getMatchingPods(np.Namespace, 
                        from.PodSelector.MatchLabels)
                    
                    for _, srcPod := range sourcePods {
                        // iptables -I <chainName> -s <srcPod.IP> -j ACCEPT
                        fmt.Printf("  Allow ingress: %s -> %s\n", 
                            srcPod.Name, pod.Name)
                    }
                }
            }
        }
        
        // 5. Process egress rules
        for _, egress := range np.Spec.Egress {
            for _, to := range egress.To {
                if to.PodSelector != nil {
                    destPods := c.getMatchingPods(np.Namespace, 
                        to.PodSelector.MatchLabels)
                    
                    for _, destPod := range destPods {
                        // iptables -I <chainName> -d <destPod.IP> -j ACCEPT
                        fmt.Printf("  Allow egress: %s -> %s\n", 
                            pod.Name, destPod.Name)
                    }
                }
            }
        }
    }
}

func (c *NetworkPolicyController) getMatchingPods(namespace string, labels map[string]string) []Pod {
    // Fetch pods matching labels
    return []Pod{{Name: "pod-1", IP: "10.244.1.2"}}
}

type Pod struct {
    Name string
    IP   string
}

func (c *NetworkPolicyController) onNetworkPolicyUpdate(oldObj, newObj interface{}) {
    c.syncNetworkPolicy(newObj.(*networkingv1.NetworkPolicy))
}

func (c *NetworkPolicyController) onNetworkPolicyDelete(obj interface{}) {
    np := obj.(*networkingv1.NetworkPolicy)
    fmt.Printf("Deleting NetworkPolicy: %s/%s\n", np.Namespace, np.Name)
    // Remove iptables rules
}
```

**Exercises:**

1. **Debug Service Connectivity:**
   ```bash
   # Create debug pod
   kubectl run debug --image=nicolaka/netshoot -it --rm
   
   # Test DNS
   nslookup kubernetes.default.svc.cluster.local
   
   # Test service connectivity
   curl http://my-service.default.svc.cluster.local:80
   
   # Trace route
   traceroute my-service.default.svc.cluster.local
   ```

2. **Capture Network Traffic:**
   ```bash
   # On host node
   tcpdump -i cni0 -nn port 80
   
   # Inside pod
   kubectl exec -it <pod> -- tcpdump -i eth0 -w /tmp/capture.pcap
   kubectl cp <pod>:/tmp/capture.pcap ./capture.pcap
   wireshark capture.pcap
   ```

3. **Build Service Mesh Data Plane (Sidecar Proxy):**
   ```go
   // Implement transparent proxy that intercepts pod traffic
   // Use iptables REDIRECT to route traffic through sidecar
   ```

**Further Reading:**
- Article: "Life of a Packet in Kubernetes" – Michael Rubin
- Repo: `kubernetes/kubernetes/pkg/proxy` (kube-proxy implementation)

---

**[PART 3 CONTINUES WITH STORAGE - Reply "continue" for Storage internals including CSI, PV/PVC lifecycle, and distributed storage patterns]**

Part 4: , yes.
Part 5: Performance Engineering (Profiling, Optimization, Benchmarking)
Part 6: Production Systems (Observability, Security, Incident Response)

# Comprehensive Guide to Distributed Systems: Consensus, Replication, and Partitioning

## Table of Contents
1. [Introduction](#introduction)
2. [Consensus Algorithms](#consensus-algorithms)
3. [Replication Strategies](#replication-strategies)
4. [Partitioning Techniques](#partitioning-techniques)
5. [Complete Examples](#complete-examples)

---

## Introduction

Distributed systems are collections of independent computers that appear to users as a single coherent system. Three fundamental challenges in distributed systems are:

- **Consensus**: Getting multiple nodes to agree on a single value or decision
- **Replication**: Maintaining copies of data across multiple nodes for availability and performance
- **Partitioning**: Dividing data across multiple nodes to scale beyond single-machine capacity

### Core Challenges

1. **Network Partitions**: Networks can split, causing nodes to become temporarily unreachable
2. **Node Failures**: Machines crash, processes die, or become unresponsive
3. **Timing Issues**: No global clock, message delays are unpredictable
4. **Concurrent Updates**: Multiple clients may update the same data simultaneously

### CAP Theorem

A distributed system can provide at most two of these three guarantees:
- **Consistency**: All nodes see the same data at the same time
- **Availability**: Every request receives a response
- **Partition Tolerance**: System continues despite network partitions

---

## Consensus Algorithms

Consensus is fundamental to building fault-tolerant distributed systems. Nodes must agree on values despite failures and network issues.

### 1. Raft Consensus Algorithm

Raft is designed to be understandable. It separates consensus into leader election, log replication, and safety.

#### Key Concepts

- **Leader Election**: One node becomes leader, others are followers
- **Log Replication**: Leader receives client requests, replicates to followers
- **Safety**: Committed entries are never lost
- **Terms**: Logical clock that increments with each election

#### Go Implementation

```go
package raft

import (
    "context"
    "math/rand"
    "sync"
    "time"
)

// State represents the current state of a Raft node
type State int

const (
    Follower State = iota
    Candidate
    Leader
)

// LogEntry represents a single entry in the replicated log
type LogEntry struct {
    Term    int
    Command interface{}
}

// RaftNode represents a single node in the Raft cluster
type RaftNode struct {
    mu sync.Mutex
    
    // Persistent state
    currentTerm int
    votedFor    *int
    log         []LogEntry
    
    // Volatile state
    state       State
    commitIndex int
    lastApplied int
    
    // Leader state
    nextIndex   map[int]int
    matchIndex  map[int]int
    
    // Configuration
    id          int
    peers       []int
    
    // Channels
    appendEntriesCh chan *AppendEntriesRequest
    requestVoteCh   chan *RequestVoteRequest
    heartbeatTimer  *time.Timer
    electionTimer   *time.Timer
}

// AppendEntriesRequest is sent by leaders to replicate log entries
type AppendEntriesRequest struct {
    Term         int
    LeaderId     int
    PrevLogIndex int
    PrevLogTerm  int
    Entries      []LogEntry
    LeaderCommit int
    ResponseCh   chan *AppendEntriesResponse
}

type AppendEntriesResponse struct {
    Term    int
    Success bool
}

// RequestVoteRequest is sent during elections
type RequestVoteRequest struct {
    Term         int
    CandidateId  int
    LastLogIndex int
    LastLogTerm  int
    ResponseCh   chan *RequestVoteResponse
}

type RequestVoteResponse struct {
    Term        int
    VoteGranted bool
}

// NewRaftNode creates a new Raft node
func NewRaftNode(id int, peers []int) *RaftNode {
    node := &RaftNode{
        id:              id,
        peers:           peers,
        currentTerm:     0,
        state:           Follower,
        log:             []LogEntry{{Term: 0}}, // dummy entry at index 0
        commitIndex:     0,
        lastApplied:     0,
        nextIndex:       make(map[int]int),
        matchIndex:      make(map[int]int),
        appendEntriesCh: make(chan *AppendEntriesRequest, 100),
        requestVoteCh:   make(chan *RequestVoteRequest, 100),
    }
    
    node.resetElectionTimer()
    return node
}

// Start begins the Raft protocol
func (rn *RaftNode) Start(ctx context.Context) {
    go rn.run(ctx)
}

func (rn *RaftNode) run(ctx context.Context) {
    for {
        select {
        case <-ctx.Done():
            return
        case <-rn.electionTimer.C:
            rn.startElection()
        case req := <-rn.appendEntriesCh:
            rn.handleAppendEntries(req)
        case req := <-rn.requestVoteCh:
            rn.handleRequestVote(req)
        }
    }
}

func (rn *RaftNode) startElection() {
    rn.mu.Lock()
    rn.state = Candidate
    rn.currentTerm++
    rn.votedFor = &rn.id
    currentTerm := rn.currentTerm
    lastLogIndex := len(rn.log) - 1
    lastLogTerm := rn.log[lastLogIndex].Term
    rn.resetElectionTimer()
    rn.mu.Unlock()
    
    votes := 1 // vote for self
    votesNeeded := (len(rn.peers) + 1) / 2 + 1
    
    var voteMu sync.Mutex
    
    for _, peerID := range rn.peers {
        go func(peer int) {
            respCh := make(chan *RequestVoteResponse, 1)
            req := &RequestVoteRequest{
                Term:         currentTerm,
                CandidateId:  rn.id,
                LastLogIndex: lastLogIndex,
                LastLogTerm:  lastLogTerm,
                ResponseCh:   respCh,
            }
            
            // Send request (would be RPC in real implementation)
            // For now, we'll simulate
            
            select {
            case resp := <-respCh:
                voteMu.Lock()
                defer voteMu.Unlock()
                
                if resp.VoteGranted {
                    votes++
                    if votes >= votesNeeded {
                        rn.becomeLeader()
                    }
                }
                
                if resp.Term > currentTerm {
                    rn.stepDown(resp.Term)
                }
            case <-time.After(100 * time.Millisecond):
                // Timeout
            }
        }(peerID)
    }
}

func (rn *RaftNode) becomeLeader() {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    if rn.state != Candidate {
        return
    }
    
    rn.state = Leader
    lastLogIndex := len(rn.log) - 1
    
    for _, peer := range rn.peers {
        rn.nextIndex[peer] = lastLogIndex + 1
        rn.matchIndex[peer] = 0
    }
    
    go rn.sendHeartbeats()
}

func (rn *RaftNode) sendHeartbeats() {
    ticker := time.NewTicker(50 * time.Millisecond)
    defer ticker.Stop()
    
    for {
        rn.mu.Lock()
        if rn.state != Leader {
            rn.mu.Unlock()
            return
        }
        
        for _, peerID := range rn.peers {
            go rn.sendAppendEntries(peerID)
        }
        rn.mu.Unlock()
        
        <-ticker.C
    }
}

func (rn *RaftNode) sendAppendEntries(peerID int) {
    rn.mu.Lock()
    nextIdx := rn.nextIndex[peerID]
    prevLogIndex := nextIdx - 1
    prevLogTerm := rn.log[prevLogIndex].Term
    
    entries := []LogEntry{}
    if nextIdx < len(rn.log) {
        entries = rn.log[nextIdx:]
    }
    
    req := &AppendEntriesRequest{
        Term:         rn.currentTerm,
        LeaderId:     rn.id,
        PrevLogIndex: prevLogIndex,
        PrevLogTerm:  prevLogTerm,
        Entries:      entries,
        LeaderCommit: rn.commitIndex,
        ResponseCh:   make(chan *AppendEntriesResponse, 1),
    }
    rn.mu.Unlock()
    
    // Send request (would be RPC)
    // Handle response
    select {
    case resp := <-req.ResponseCh:
        rn.handleAppendEntriesResponse(peerID, resp, len(entries))
    case <-time.After(100 * time.Millisecond):
        // Timeout
    }
}

func (rn *RaftNode) handleAppendEntries(req *AppendEntriesRequest) {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    resp := &AppendEntriesResponse{
        Term:    rn.currentTerm,
        Success: false,
    }
    
    // Reply false if term < currentTerm
    if req.Term < rn.currentTerm {
        req.ResponseCh <- resp
        return
    }
    
    // If RPC request or response contains term T > currentTerm
    if req.Term > rn.currentTerm {
        rn.currentTerm = req.Term
        rn.votedFor = nil
        rn.state = Follower
    }
    
    rn.resetElectionTimer()
    
    // Reply false if log doesn't contain an entry at prevLogIndex
    if req.PrevLogIndex >= len(rn.log) {
        req.ResponseCh <- resp
        return
    }
    
    // whose term matches prevLogTerm
    if rn.log[req.PrevLogIndex].Term != req.PrevLogTerm {
        req.ResponseCh <- resp
        return
    }
    
    // Append new entries
    for i, entry := range req.Entries {
        index := req.PrevLogIndex + 1 + i
        if index < len(rn.log) {
            if rn.log[index].Term != entry.Term {
                rn.log = rn.log[:index]
                rn.log = append(rn.log, entry)
            }
        } else {
            rn.log = append(rn.log, entry)
        }
    }
    
    // Update commit index
    if req.LeaderCommit > rn.commitIndex {
        rn.commitIndex = min(req.LeaderCommit, len(rn.log)-1)
    }
    
    resp.Success = true
    req.ResponseCh <- resp
}

func (rn *RaftNode) handleRequestVote(req *RequestVoteRequest) {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    resp := &RequestVoteResponse{
        Term:        rn.currentTerm,
        VoteGranted: false,
    }
    
    // Reply false if term < currentTerm
    if req.Term < rn.currentTerm {
        req.ResponseCh <- resp
        return
    }
    
    if req.Term > rn.currentTerm {
        rn.currentTerm = req.Term
        rn.votedFor = nil
        rn.state = Follower
    }
    
    lastLogIndex := len(rn.log) - 1
    lastLogTerm := rn.log[lastLogIndex].Term
    
    logIsUpToDate := req.LastLogTerm > lastLogTerm ||
        (req.LastLogTerm == lastLogTerm && req.LastLogIndex >= lastLogIndex)
    
    if (rn.votedFor == nil || *rn.votedFor == req.CandidateId) && logIsUpToDate {
        rn.votedFor = &req.CandidateId
        resp.VoteGranted = true
        rn.resetElectionTimer()
    }
    
    req.ResponseCh <- resp
}

func (rn *RaftNode) handleAppendEntriesResponse(peerID int, resp *AppendEntriesResponse, entriesLen int) {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    if resp.Term > rn.currentTerm {
        rn.stepDown(resp.Term)
        return
    }
    
    if rn.state != Leader {
        return
    }
    
    if resp.Success {
        rn.nextIndex[peerID] += entriesLen
        rn.matchIndex[peerID] = rn.nextIndex[peerID] - 1
        rn.updateCommitIndex()
    } else {
        rn.nextIndex[peerID] = max(1, rn.nextIndex[peerID]-1)
    }
}

func (rn *RaftNode) updateCommitIndex() {
    for n := rn.commitIndex + 1; n < len(rn.log); n++ {
        if rn.log[n].Term != rn.currentTerm {
            continue
        }
        
        count := 1
        for _, peer := range rn.peers {
            if rn.matchIndex[peer] >= n {
                count++
            }
        }
        
        if count > (len(rn.peers)+1)/2 {
            rn.commitIndex = n
        }
    }
}

func (rn *RaftNode) stepDown(term int) {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    rn.currentTerm = term
    rn.state = Follower
    rn.votedFor = nil
    rn.resetElectionTimer()
}

func (rn *RaftNode) resetElectionTimer() {
    timeout := time.Duration(150+rand.Intn(150)) * time.Millisecond
    if rn.electionTimer != nil {
        rn.electionTimer.Stop()
    }
    rn.electionTimer = time.NewTimer(timeout)
}

func min(a, b int) int {
    if a < b {
        return a
    }
    return b
}

func max(a, b int) int {
    if a > b {
        return a
    }
    return b
}

// Submit adds a new command to the log (leader only)
func (rn *RaftNode) Submit(command interface{}) bool {
    rn.mu.Lock()
    defer rn.mu.Unlock()
    
    if rn.state != Leader {
        return false
    }
    
    entry := LogEntry{
        Term:    rn.currentTerm,
        Command: command,
    }
    
    rn.log = append(rn.log, entry)
    return true
}
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use tokio::time::{sleep, interval};
use rand::Rng;

#[derive(Debug, Clone, Copy, PartialEq)]
enum State {
    Follower,
    Candidate,
    Leader,
}

#[derive(Debug, Clone)]
struct LogEntry {
    term: u64,
    command: Vec<u8>,
}

#[derive(Debug)]
struct AppendEntriesRequest {
    term: u64,
    leader_id: u64,
    prev_log_index: usize,
    prev_log_term: u64,
    entries: Vec<LogEntry>,
    leader_commit: usize,
}

#[derive(Debug)]
struct AppendEntriesResponse {
    term: u64,
    success: bool,
}

#[derive(Debug)]
struct RequestVoteRequest {
    term: u64,
    candidate_id: u64,
    last_log_index: usize,
    last_log_term: u64,
}

#[derive(Debug)]
struct RequestVoteResponse {
    term: u64,
    vote_granted: bool,
}

struct RaftNode {
    id: u64,
    peers: Vec<u64>,
    
    // Persistent state
    current_term: u64,
    voted_for: Option<u64>,
    log: Vec<LogEntry>,
    
    // Volatile state
    state: State,
    commit_index: usize,
    last_applied: usize,
    
    // Leader state
    next_index: HashMap<u64, usize>,
    match_index: HashMap<u64, usize>,
    
    // Timers
    election_deadline: Instant,
}

impl RaftNode {
    fn new(id: u64, peers: Vec<u64>) -> Self {
        let mut log = Vec::new();
        log.push(LogEntry {
            term: 0,
            command: vec![],
        });
        
        Self {
            id,
            peers,
            current_term: 0,
            voted_for: None,
            log,
            state: State::Follower,
            commit_index: 0,
            last_applied: 0,
            next_index: HashMap::new(),
            match_index: HashMap::new(),
            election_deadline: Self::new_election_deadline(),
        }
    }
    
    fn new_election_deadline() -> Instant {
        let timeout = rand::thread_rng().gen_range(150..300);
        Instant::now() + Duration::from_millis(timeout)
    }
    
    fn reset_election_timer(&mut self) {
        self.election_deadline = Self::new_election_deadline();
    }
    
    fn start_election(&mut self) {
        self.state = State::Candidate;
        self.current_term += 1;
        self.voted_for = Some(self.id);
        self.reset_election_timer();
        
        let last_log_index = self.log.len() - 1;
        let last_log_term = self.log[last_log_index].term;
        
        println!("Node {} starting election for term {}", self.id, self.current_term);
        
        // In a real implementation, send RequestVote RPCs to all peers
    }
    
    fn become_leader(&mut self) {
        println!("Node {} became leader for term {}", self.id, self.current_term);
        self.state = State::Leader;
        
        let last_log_index = self.log.len() - 1;
        for &peer in &self.peers {
            self.next_index.insert(peer, last_log_index + 1);
            self.match_index.insert(peer, 0);
        }
    }
    
    fn handle_append_entries(&mut self, req: AppendEntriesRequest) -> AppendEntriesResponse {
        let mut response = AppendEntriesResponse {
            term: self.current_term,
            success: false,
        };
        
        if req.term < self.current_term {
            return response;
        }
        
        if req.term > self.current_term {
            self.current_term = req.term;
            self.voted_for = None;
            self.state = State::Follower;
        }
        
        self.reset_election_timer();
        
        // Check if log contains entry at prev_log_index with matching term
        if req.prev_log_index >= self.log.len() {
            return response;
        }
        
        if self.log[req.prev_log_index].term != req.prev_log_term {
            return response;
        }
        
        // Append new entries
        for (i, entry) in req.entries.iter().enumerate() {
            let index = req.prev_log_index + 1 + i;
            if index < self.log.len() {
                if self.log[index].term != entry.term {
                    self.log.truncate(index);
                    self.log.push(entry.clone());
                }
            } else {
                self.log.push(entry.clone());
            }
        }
        
        // Update commit index
        if req.leader_commit > self.commit_index {
            self.commit_index = std::cmp::min(req.leader_commit, self.log.len() - 1);
        }
        
        response.success = true;
        response
    }
    
    fn handle_request_vote(&mut self, req: RequestVoteRequest) -> RequestVoteResponse {
        let mut response = RequestVoteResponse {
            term: self.current_term,
            vote_granted: false,
        };
        
        if req.term < self.current_term {
            return response;
        }
        
        if req.term > self.current_term {
            self.current_term = req.term;
            self.voted_for = None;
            self.state = State::Follower;
        }
        
        let last_log_index = self.log.len() - 1;
        let last_log_term = self.log[last_log_index].term;
        
        let log_is_up_to_date = req.last_log_term > last_log_term ||
            (req.last_log_term == last_log_term && req.last_log_index >= last_log_index);
        
        if (self.voted_for.is_none() || self.voted_for == Some(req.candidate_id)) 
            && log_is_up_to_date {
            self.voted_for = Some(req.candidate_id);
            response.vote_granted = true;
            self.reset_election_timer();
        }
        
        response
    }
    
    fn submit(&mut self, command: Vec<u8>) -> bool {
        if self.state != State::Leader {
            return false;
        }
        
        let entry = LogEntry {
            term: self.current_term,
            command,
        };
        
        self.log.push(entry);
        true
    }
}
```

### 2. Paxos Algorithm

Paxos is the foundational consensus algorithm, though more complex than Raft.

#### Key Concepts

- **Proposers**: Propose values
- **Acceptors**: Vote on proposals
- **Learners**: Learn the chosen value
- **Phases**: Prepare and Accept phases ensure safety

#### Go Implementation (Basic Paxos)

```go
package paxos

import (
    "sync"
)

type ProposalNumber struct {
    Number int
    NodeID int
}

func (p ProposalNumber) GreaterThan(other ProposalNumber) bool {
    if p.Number != other.Number {
        return p.Number > other.Number
    }
    return p.NodeID > other.NodeID
}

type PrepareRequest struct {
    ProposalNum ProposalNumber
    ResponseCh  chan *PrepareResponse
}

type PrepareResponse struct {
    Promise         bool
    AcceptedNum     *ProposalNumber
    AcceptedValue   interface{}
}

type AcceptRequest struct {
    ProposalNum ProposalNumber
    Value       interface{}
    ResponseCh  chan *AcceptResponse
}

type AcceptResponse struct {
    Accepted bool
}

type Acceptor struct {
    mu sync.Mutex
    
    promisedNum   *ProposalNumber
    acceptedNum   *ProposalNumber
    acceptedValue interface{}
}

func NewAcceptor() *Acceptor {
    return &Acceptor{}
}

func (a *Acceptor) HandlePrepare(req *PrepareRequest) {
    a.mu.Lock()
    defer a.mu.Unlock()
    
    resp := &PrepareResponse{
        Promise: false,
    }
    
    if a.promisedNum == nil || req.ProposalNum.GreaterThan(*a.promisedNum) {
        a.promisedNum = &req.ProposalNum
        resp.Promise = true
        resp.AcceptedNum = a.acceptedNum
        resp.AcceptedValue = a.acceptedValue
    }
    
    req.ResponseCh <- resp
}

func (a *Acceptor) HandleAccept(req *AcceptRequest) {
    a.mu.Lock()
    defer a.mu.Unlock()
    
    resp := &AcceptResponse{
        Accepted: false,
    }
    
    if a.promisedNum == nil || 
       req.ProposalNum.Number >= a.promisedNum.Number {
        a.promisedNum = &req.ProposalNum
        a.acceptedNum = &req.ProposalNum
        a.acceptedValue = req.Value
        resp.Accepted = true
    }
    
    req.ResponseCh <- resp
}

type Proposer struct {
    nodeID    int
    nextNum   int
    acceptors []*Acceptor
}

func NewProposer(nodeID int, acceptors []*Acceptor) *Proposer {
    return &Proposer{
        nodeID:    nodeID,
        nextNum:   0,
        acceptors: acceptors,
    }
}

func (p *Proposer) Propose(value interface{}) (bool, interface{}) {
    proposalNum := ProposalNumber{
        Number: p.nextNum,
        NodeID: p.nodeID,
    }
    p.nextNum++
    
    // Phase 1: Prepare
    promises := 0
    var highestAcceptedNum *ProposalNumber
    var highestAcceptedValue interface{}
    
    for _, acceptor := range p.acceptors {
        respCh := make(chan *PrepareResponse, 1)
        req := &PrepareRequest{
            ProposalNum: proposalNum,
            ResponseCh:  respCh,
        }
        
        go acceptor.HandlePrepare(req)
        
        resp := <-respCh
        if resp.Promise {
            promises++
            if resp.AcceptedNum != nil {
                if highestAcceptedNum == nil || 
                   resp.AcceptedNum.GreaterThan(*highestAcceptedNum) {
                    highestAcceptedNum = resp.AcceptedNum
                    highestAcceptedValue = resp.AcceptedValue
                }
            }
        }
    }
    
    // Need majority
    if promises <= len(p.acceptors)/2 {
        return false, nil
    }
    
    // Phase 2: Accept
    valueToPropose := value
    if highestAcceptedNum != nil {
        valueToPropose = highestAcceptedValue
    }
    
    accepts := 0
    for _, acceptor := range p.acceptors {
        respCh := make(chan *AcceptResponse, 1)
        req := &AcceptRequest{
            ProposalNum: proposalNum,
            Value:       valueToPropose,
            ResponseCh:  respCh,
        }
        
        go acceptor.HandleAccept(req)
        
        resp := <-respCh
        if resp.Accepted {
            accepts++
        }
    }
    
    if accepts > len(p.acceptors)/2 {
        return true, valueToPropose
    }
    
    return false, nil
}
```

---

## Replication Strategies

Replication maintains copies of data across multiple nodes for fault tolerance and performance.

### 1. Primary-Backup Replication

One primary handles all writes, backups replicate asynchronously or synchronously.

#### Go Implementation

```go
package replication

import (
    "context"
    "errors"
    "sync"
    "time"
)

type Operation struct {
    Type  string      // "set", "delete"
    Key   string
    Value interface{}
    SeqNum int64
}

type PrimaryNode struct {
    mu sync.RWMutex
    
    data       map[string]interface{}
    backups    []ReplicationClient
    seqNum     int64
    commitCh   chan int64
}

type ReplicationClient interface {
    Replicate(op Operation) error
}

func NewPrimaryNode(backups []ReplicationClient) *PrimaryNode {
    return &PrimaryNode{
        data:     make(map[string]interface{}),
        backups:  backups,
        seqNum:   0,
        commitCh: make(chan int64, 1000),
    }
}

func (p *PrimaryNode) Set(key string, value interface{}) error {
    p.mu.Lock()
    
    // Assign sequence number
    p.seqNum++
    op := Operation{
        Type:   "set",
        Key:    key,
        Value:  value,
        SeqNum: p.seqNum,
    }
    
    // Optimistically apply locally
    p.data[key] = value
    p.mu.Unlock()
    
    // Replicate to backups
    return p.replicateToBackups(op)
}

func (p *PrimaryNode) replicateToBackups(op Operation) error {
    // Synchronous replication (wait for majority)
    successCount := 1 // primary counts as success
    
    var wg sync.WaitGroup
    var mu sync.Mutex
    
    for _, backup := range p.backups {
        wg.Add(1)
        go func(b ReplicationClient) {
            defer wg.Done()
            
            if err := b.Replicate(op); err == nil {
                mu.Lock()
                successCount++
                mu.Unlock()
            }
        }(backup)
    }
    
    wg.Wait()
    
    // Require majority for commit
    majority := (len(p.backups) + 1) / 2 + 1
    if successCount >= majority {
        return nil
    }
    
    return errors.New("failed to replicate to majority")
}

func (p *PrimaryNode) Get(key string) (interface{}, bool) {
    p.mu.RLock()
    defer p.mu.RUnlock()
    
    val, ok := p.data[key]
    return val, ok
}

type BackupNode struct {
    mu sync.RWMutex
    
    data       map[string]interface{}
    lastSeqNum int64
}

func NewBackupNode() *BackupNode {
    return &BackupNode{
        data:       make(map[string]interface{}),
        lastSeqNum: 0,
    }
}

func (b *BackupNode) Replicate(op Operation) error {
    b.mu.Lock()
    defer b.mu.Unlock()
    
    // Ensure operations are applied in order
    if op.SeqNum != b.lastSeqNum+1 {
        return errors.New("sequence number mismatch")
    }
    
    switch op.Type {
    case "set":
        b.data[op.Key] = op.Value
    case "delete":
        delete(b.data, op.Key)
    }
    
    b.lastSeqNum = op.SeqNum
    return nil
}

func (b *BackupNode) Get(key string) (interface{}, bool) {
    b.mu.RLock()
    defer b.mu.RUnlock()
    
    val, ok := b.data[key]
    return val, ok
}

// Promote backup to primary
func (b *BackupNode) Promote() *PrimaryNode {
    b.mu.RLock()
    defer b.mu.RUnlock()
    
    primary := &PrimaryNode{
        data:     make(map[string]interface{}),
        backups:  []ReplicationClient{},
        seqNum:   b.lastSeqNum,
        commitCh: make(chan int64, 1000),
    }
    
    for k, v := range b.data {
        primary.data[k] = v
    }
    
    return primary
}
```

#### Rust Implementation

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use tokio::sync::mpsc;

#[derive(Debug, Clone)]
struct Operation {
    op_type: String,
    key: String,
    value: Option<Vec<u8>>,
    seq_num: i64,
}

#[async_trait::async_trait]
trait ReplicationClient: Send + Sync {
    async fn replicate(&self, op: Operation) -> Result<(), String>;
}

struct PrimaryNode {
    data: Arc<RwLock<HashMap<String, Vec<u8>>>>,
    backups: Vec<Arc<dyn ReplicationClient>>,
    seq_num: Arc<RwLock<i64>>,
}

impl PrimaryNode {
    fn new(backups: Vec<Arc<dyn ReplicationClient>>) -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
            backups,
            seq_num: Arc::new(RwLock::new(0)),
        }
    }
    
    async fn set(&self, key: String, value: Vec<u8>) -> Result<(), String> {
        // Get next sequence number
        let seq_num = {
            let mut seq = self.seq_num.write().unwrap();
            *seq += 1;
            *seq
        };
        
        let op = Operation {
            op_type: "set".to_string(),
            key: key.clone(),
            value: Some(value.clone()),
            seq_num,
        };
        
        // Apply locally first
        {
            let mut data = self.data.write().unwrap();
            data.insert(key, value);
        }
        
        // Replicate to backups
        self.replicate_to_backups(op).await
    }
    
    async fn replicate_to_backups(&self, op: Operation) -> Result<(), String> {
        let mut handles = vec![];
        
        for backup in &self.backups {
            let backup = backup.clone();
            let op = op.clone();
            
            let handle = tokio::spawn(async move {
                backup.replicate(op).await
            });
            
            handles.push(handle);
        }
        
        let mut success_count = 1; // Primary counts as success
        
        for handle in handles {
            if let Ok(Ok(_)) = handle.await {
                success_count += 1;
            }
        }
        
        // Require majority
        let majority = (self.backups.len() + 1) / 2 + 1;
        if success_count >= majority {
            Ok(())
        } else {
            Err("Failed to replicate to majority".to_string())
        }
    }
    
    fn get(&self, key: &str) -> Option<Vec<u8>> {
        let data = self.data.read().unwrap();
        data.get(key).cloned()
    }
}

struct BackupNode {
    data: Arc<RwLock<HashMap<String, Vec<u8>>>>,
    last_seq_num: Arc<RwLock<i64>>,
}

impl BackupNode {
    fn new() -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
            last_seq_num: Arc::new(RwLock::new(0)),
        }
    }
    
    fn get(&self, key: &str) -> Option<Vec<u8>> {
        let data = self.data.read().unwrap();
        data.get(key).cloned()
    }
}

#[async_trait::async_trait]
impl ReplicationClient for BackupNode {
    async fn replicate(&self, op: Operation) -> Result<(), String> {
        let mut last_seq = self.last_seq_num.write().unwrap();
        
        // Ensure sequential ordering
        if op.seq_num != *last_seq + 1 {
            return Err("Sequence number mismatch".to_string());
        }
        
        match op.op_type.as_str() {
            "set" => {
                if let Some(value) = op.value {
                    let mut data = self.data.write().unwrap();
                    data.insert(op.key, value);
                }
            }
            "delete" => {
                let mut data = self.data.write().unwrap();
                data.remove(&op.key);
            }
            _ => return Err("Unknown operation type".to_string()),
        }
        
        *last_seq = op.seq_num;
        Ok(())
    }
}
```

### 2. Multi-Master Replication with Conflict Resolution

Multiple nodes accept writes, conflicts are resolved using vector clocks or CRDTs.

#### Go Implementation with Vector Clocks

```go
package multimaster

import (
    "encoding/json"
    "sync"
)

type VectorClock map[string]int

func (vc VectorClock) Copy() VectorClock {
    copy := make(VectorClock)
    for k, v := range vc {
        copy[k] = v
    }
    return copy
}

func (vc VectorClock) Increment(nodeID string) {
    vc[nodeID]++
}

func (vc VectorClock) Merge(other VectorClock) {
    for nodeID, timestamp := range other {
        if timestamp > vc[nodeID] {
            vc[nodeID] = timestamp
        }
    }
}

func (vc VectorClock) HappensBefore(other VectorClock) bool {
    atLeastOneLess := false
    
    for nodeID, timestamp := range vc {
        otherTimestamp := other[nodeID]
        if timestamp > otherTimestamp {
            return false
        }
        if timestamp < otherTimestamp {
            atLeastOneLess = true
        }
    }
    
    return atLeastOneLess
}

func (vc VectorClock) ConcurrentWith(other VectorClock) bool {
    return !vc.HappensBefore(other) && !other.HappensBefore(vc)
}

type Versioned struct {
    Value interface{}
    Clock VectorClock
}

type MultiMasterNode struct {
    mu sync.RWMutex
    
    nodeID string
    data   map[string][]Versioned // Key -> versions
    peers  []ReplicationPeer
}

type ReplicationPeer interface {
    Replicate(key string, versioned Versioned) error
}

func NewMultiMasterNode(nodeID string, peers []ReplicationPeer) *MultiMasterNode {
    return &MultiMasterNode{
        nodeID: nodeID,
        data:   make(map[string][]Versioned),
        peers:  peers,
    }
}

func (m *MultiMasterNode) Put(key string, value interface{}) error {
    m.mu.Lock()
    
    // Get current versions
    versions := m.data[key]
    
    // Create new vector clock
    clock := make(VectorClock)
    
    // Merge all concurrent version clocks
    for _, v := range versions {
        clock.Merge(v.Clock)
    }
    
    // Increment our timestamp
    clock.Increment(m.nodeID)
    
    versioned := Versioned{
        Value: value,
        Clock: clock,
    }
    
    // Replace all versions with this new version
    m.data[key] = []Versioned{versioned}
    
    m.mu.Unlock()
    
    // Replicate to peers asynchronously
    for _, peer := range m.peers {
        go peer.Replicate(key, versioned)
    }
    
    return nil
}

func (m *MultiMasterNode) Get(key string) []Versioned {
    m.mu.RLock()
    defer m.mu.RUnlock()
    
    versions := m.data[key]
    result := make([]Versioned, len(versions))
    copy(result, versions)
    
    return result
}

func (m *MultiMasterNode) Merge(key string, versioned Versioned) {
    m.mu.Lock()
    defer m.mu.Unlock()
    
    versions := m.data[key]
    
    // Remove versions that this new version supersedes
    newVersions := []Versioned{}
    
    shouldAdd := true
    for _, existing := range versions {
        if existing.Clock.HappensBefore(versioned.Clock) {
            // New version supersedes this one, don't keep it
            continue
        } else if versioned.Clock.HappensBefore(existing.Clock) {
            // Existing version supersedes new one
            shouldAdd = false
            newVersions = append(newVersions, existing)
        } else {
            // Concurrent versions, keep both
            newVersions = append(newVersions, existing)
        }
    }
    
    if shouldAdd {
        newVersions = append(newVersions, versioned)
    }
    
    m.data[key] = newVersions
}

// Resolve conflicts by choosing the value with highest nodeID
func (m *MultiMasterNode) Resolve(key string) (interface{}, bool) {
    versions := m.Get(key)
    
    if len(versions) == 0 {
        return nil, false
    }
    
    if len(versions) == 1 {
        return versions[0].Value, true
    }
    
    // Multiple concurrent versions - pick one deterministically
    // (In practice, you'd use application-specific resolution)
    chosen := versions[0]
    chosenNodeID := m.getNodeIDFromClock(chosen.Clock)
    
    for _, v := range versions[1:] {
        nodeID := m.getNodeIDFromClock(v.Clock)
        if nodeID > chosenNodeID {
            chosen = v
            chosenNodeID = nodeID
        }
    }
    
    return chosen.Value, true
}

func (m *MultiMasterNode) getNodeIDFromClock(clock VectorClock) string {
    maxNodeID := ""
    maxTimestamp := 0
    
    for nodeID, timestamp := range clock {
        if timestamp > maxTimestamp {
            maxTimestamp = timestamp
            maxNodeID = nodeID
        }
    }
    
    return maxNodeID
}
```

---

## Partitioning Techniques

Partitioning (sharding) distributes data across multiple nodes to scale storage and throughput.

### 1. Consistent Hashing

Distributes keys evenly across nodes and minimizes redistribution when nodes are added/removed.

#### Go Implementation

```go
package partitioning

import (
    "crypto/sha256"
    "encoding/binary"
    "sort"
    "sync"
)

type ConsistentHash struct {
    mu sync.RWMutex
    
    ring         []uint32      // Sorted hash values
    ringMap      map[uint32]string // Hash -> Node
    nodes        map[string]bool
    virtualNodes int
}

func NewConsistentHash(virtualNodes int) *ConsistentHash {
    return &ConsistentHash{
        ring:         []uint32{},
        ringMap:      make(map[uint32]string),
        nodes:        make(map[string]bool),
        virtualNodes: virtualNodes,
    }
}

func (ch *ConsistentHash) hash(key string) uint32 {
    h := sha256.New()
    h.Write([]byte(key))
    hash := h.Sum(nil)
    return binary.BigEndian.Uint32(hash[:4])
}

func (ch *ConsistentHash) AddNode(node string) {
    ch.mu.Lock()
    defer ch.mu.Unlock()
    
    if ch.nodes[node] {
        return
    }
    
    ch.nodes[node] = true
    
    // Add virtual nodes
    for i := 0; i < ch.virtualNodes; i++ {
        virtualKey := node + "#" + string(rune(i))
        hash := ch.hash(virtualKey)
        
        ch.ring = append(ch.ring, hash)
        ch.ringMap[hash] = node
    }
    
    sort.Slice(ch.ring, func(i, j int) bool {
        return ch.ring[i] < ch.ring[j]
    })
}

func (ch *ConsistentHash) RemoveNode(node string) {
    ch.mu.Lock()
    defer ch.mu.Unlock()
    
    if !ch.nodes[node] {
        return
    }
    
    delete(ch.nodes, node)
    
    // Remove virtual nodes
    newRing := []uint32{}
    for _, hash := range ch.ring {
        if ch.ringMap[hash] != node {
            newRing = append(newRing, hash)
        } else {
            delete(ch.ringMap, hash)
        }
    }
    
    ch.ring = newRing
}

func (ch *ConsistentHash) GetNode(key string) string {
    ch.mu.RLock()
    defer ch.mu.RUnlock()
    
    if len(ch.ring) == 0 {
        return ""
    }
    
    hash := ch.hash(key)
    
    // Binary search for the first node >= hash
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })
    
    // Wrap around if necessary
    if idx == len(ch.ring) {
        idx = 0
    }
    
    return ch.ringMap[ch.ring[idx]]
}

func (ch *ConsistentHash) GetNodes(key string, count int) []string {
    ch.mu.RLock()
    defer ch.mu.RUnlock()
    
    if len(ch.nodes) == 0 {
        return []string{}
    }
    
    if count > len(ch.nodes) {
        count = len(ch.nodes)
    }
    
    hash := ch.hash(key)
    
    idx := sort.Search(len(ch.ring), func(i int) bool {
        return ch.ring[i] >= hash
    })
    
    if idx == len(ch.ring) {
        idx = 0
    }
    
    seen := make(map[string]bool)
    result := []string{}
    
    for len(result) < count {
        node := ch.ringMap[ch.ring[idx]]
        if !seen[node] {
            result = append(result, node)
            seen[node] = true
        }
        
        idx = (idx + 1) % len(ch.ring)
    }
    
    return result
}

type PartitionedStore struct {
    mu sync.RWMutex
    
    hash    *ConsistentHash
    shards  map[string]*Shard
    replicas int
}

type Shard struct {
    mu   sync.RWMutex
    data map[string]interface{}
}

func NewPartitionedStore(replicas int) *PartitionedStore {
    return &PartitionedStore{
        hash:     NewConsistentHash(150),
        shards:   make(map[string]*Shard),
        replicas: replicas,
    }
}

func (ps *PartitionedStore) AddShard(shardID string) {
    ps.mu.Lock()
    defer ps.mu.Unlock()
    
    ps.shards[shardID] = &Shard{
        data: make(map[string]interface{}),
    }
    ps.hash.AddNode(shardID)
}

func (ps *PartitionedStore) RemoveShard(shardID string) {
    ps.mu.Lock()
    defer ps.mu.Unlock()
    
    delete(ps.shards, shardID)
    ps.hash.RemoveNode(shardID)
}

func (ps *PartitionedStore) Put(key string, value interface{}) error {
    ps.mu.RLock()
    defer ps.mu.RUnlock()
    
    nodes := ps.hash.GetNodes(key, ps.replicas)
    
    for _, nodeID := range nodes {
        shard := ps.shards[nodeID]
        if shard != nil {
            shard.mu.Lock()
            shard.data[key] = value
            shard.mu.Unlock()
        }
    }
    
    return nil
}

func (ps *PartitionedStore) Get(key string) (interface{}, bool) {
    ps.mu.RLock()
    defer ps.mu.RUnlock()
    
    nodeID := ps.hash.GetNode(key)
    shard := ps.shards[nodeID]
    
    if shard == nil {
        return nil, false
    }
    
    shard.mu.RLock()
    defer shard.mu.RUnlock()
    
    value, ok := shard.data[key]
    return value, ok
}
```

#### Rust Implementation

```rust
use std::collections::{BTreeMap, HashMap, HashSet};
use std::sync::{Arc, RwLock};
use sha2::{Sha256, Digest};

struct ConsistentHash {
    ring: BTreeMap<u32, String>,
    nodes: HashSet<String>,
    virtual_nodes: usize,
}

impl ConsistentHash {
    fn new(virtual_nodes: usize) -> Self {
        Self {
            ring: BTreeMap::new(),
            nodes: HashSet::new(),
            virtual_nodes,
        }
    }
    
    fn hash(&self, key: &str) -> u32 {
        let mut hasher = Sha256::new();
        hasher.update(key.as_bytes());
        let result = hasher.finalize();
        u32::from_be_bytes([result[0], result[1], result[2], result[3]])
    }
    
    fn add_node(&mut self, node: String) {
        if self.nodes.contains(&node) {
            return;
        }
        
        self.nodes.insert(node.clone());
        
        for i in 0..self.virtual_nodes {
            let virtual_key = format!("{}#{}", node, i);
            let hash = self.hash(&virtual_key);
            self.ring.insert(hash, node.clone());
        }
    }
    
    fn remove_node(&mut self, node: &str) {
        if !self.nodes.contains(node) {
            return;
        }
        
        self.nodes.remove(node);
        
        for i in 0..self.virtual_nodes {
            let virtual_key = format!("{}#{}", node, i);
            let hash = self.hash(&virtual_key);
            self.ring.remove(&hash);
        }
    }
    
    fn get_node(&self, key: &str) -> Option<String> {
        if self.ring.is_empty() {
            return None;
        }
        
        let hash = self.hash(key);
        
        // Find first node with hash >= key hash
        for (_, node) in self.ring.range(hash..) {
            return Some(node.clone());
        }
        
        // Wrap around to first node
        self.ring.values().next().cloned()
    }
    
    fn get_nodes(&self, key: &str, count: usize) -> Vec<String> {
        if self.nodes.is_empty() {
            return vec![];
        }
        
        let count = count.min(self.nodes.len());
        let hash = self.hash(key);
        
        let mut result = Vec::new();
        let mut seen = HashSet::new();
        
        let mut iter = self.ring.range(hash..).chain(self.ring.range(..hash));
        
        while result.len() < count {
            if let Some((_, node)) = iter.next() {
                if !seen.contains(node) {
                    result.push(node.clone());
                    seen.insert(node.clone());
                }
            } else {
                break;
            }
        }
        
        result
    }
}

struct Shard {
    data: Arc<RwLock<HashMap<String, Vec<u8>>>>,
}

impl Shard {
    fn new() -> Self {
        Self {
            data: Arc::new(RwLock::new(HashMap::new())),
        }
    }
    
    fn put(&self, key: String, value: Vec<u8>) {
        let mut data = self.data.write().unwrap();
        data.insert(key, value);
    }
    
    fn get(&self, key: &str) -> Option<Vec<u8>> {
        let data = self.data.read().unwrap();
        data.get(key).cloned()
    }
}

struct PartitionedStore {
    hash: Arc<RwLock<ConsistentHash>>,
    shards: Arc<RwLock<HashMap<String, Arc<Shard>>>>,
    replicas: usize,
}

impl PartitionedStore {
    fn new(replicas: usize) -> Self {
        Self {
            hash: Arc::new(RwLock::new(ConsistentHash::new(150))),
            shards: Arc::new(RwLock::new(HashMap::new())),
            replicas,
        }
    }
    
    fn add_shard(&self, shard_id: String) {
        let mut shards = self.shards.write().unwrap();
        shards.insert(shard_id.clone(), Arc::new(Shard::new()));
        
        let mut hash = self.hash.write().unwrap();
        hash.add_node(shard_id);
    }
    
    fn remove_shard(&self, shard_id: &str) {
        let mut shards = self.shards.write().unwrap();
        shards.remove(shard_id);
        
        let mut hash = self.hash.write().unwrap();
        hash.remove_node(shard_id);
    }
    
    fn put(&self, key: String, value: Vec<u8>) {
        let hash = self.hash.read().unwrap();
        let nodes = hash.get_nodes(&key, self.replicas);
        
        let shards = self.shards.read().unwrap();
        for node_id in nodes {
            if let Some(shard) = shards.get(&node_id) {
                shard.put(key.clone(), value.clone());
            }
        }
    }
    
    fn get(&self, key: &str) -> Option<Vec<u8>> {
        let hash = self.hash.read().unwrap();
        let node_id = hash.get_node(key)?;
        
        let shards = self.shards.read().unwrap();
        let shard = shards.get(&node_id)?;
        shard.get(key)
    }
}
```

### 2. Range Partitioning

Data is partitioned based on key ranges, useful for range queries.

#### Go Implementation

```go
package partitioning

import (
    "bytes"
    "sort"
    "sync"
)

type RangePartition struct {
    StartKey []byte
    EndKey   []byte
    ShardID  string
}

type RangePartitioner struct {
    mu sync.RWMutex
    
    partitions []RangePartition
    shards     map[string]*Shard
}

func NewRangePartitioner() *RangePartitioner {
    return &RangePartitioner{
        partitions: []RangePartition{},
        shards:     make(map[string]*Shard),
    }
}

func (rp *RangePartitioner) AddPartition(startKey, endKey []byte, shardID string) {
    rp.mu.Lock()
    defer rp.mu.Unlock()
    
    partition := RangePartition{
        StartKey: startKey,
        EndKey:   endKey,
        ShardID:  shardID,
    }
    
    rp.partitions = append(rp.partitions, partition)
    
    // Keep partitions sorted by start key
    sort.Slice(rp.partitions, func(i, j int) bool {
        return bytes.Compare(rp.partitions[i].StartKey, rp.partitions[j].StartKey) < 0
    })
    
    if rp.shards[shardID] == nil {
        rp.shards[shardID] = &Shard{
            data: make(map[string]interface{}),
        }
    }
}

func (rp *RangePartitioner) GetShard(key []byte) string {
    rp.mu.RLock()
    defer rp.mu.RUnlock()
    
    for _, partition := range rp.partitions {
        if bytes.Compare(key, partition.StartKey) >= 0 &&
           (len(partition.EndKey) == 0 || bytes.Compare(key, partition.EndKey) < 0) {
            return partition.ShardID
        }
    }
    
    return ""
}

func (rp *RangePartitioner) Put(key []byte, value interface{}) bool {
    shardID := rp.GetShard(key)
    if shardID == "" {
        return false
    }
    
    rp.mu.RLock()
    shard := rp.shards[shardID]
    rp.mu.RUnlock()
    
    if shard == nil {
        return false
    }
    
    shard.mu.Lock()
    shard.data[string(key)] = value
    shard.mu.Unlock()
    
    return true
}

func (rp *RangePartitioner) Get(key []byte) (interface{}, bool) {
    shardID := rp.GetShard(key)
    if shardID == "" {
        return nil, false
    }
    
    rp.mu.RLock()
    shard := rp.shards[shardID]
    rp.mu.RUnlock()
    
    if shard == nil {
        return nil, false
    }
    
    shard.mu.RLock()
    value, ok := shard.data[string(key)]
    shard.mu.RUnlock()
    
    return value, ok
}

func (rp *RangePartitioner) RangeQuery(startKey, endKey []byte) map[string]interface{} {
    result := make(map[string]interface{})
    
    rp.mu.RLock()
    defer rp.mu.RUnlock()
    
    // Find all partitions that overlap with the query range
    for _, partition := range rp.partitions {
        overlaps := false
        
        if bytes.Compare(startKey, partition.EndKey) < 0 &&
           bytes.Compare(endKey, partition.StartKey) > 0 {
            overlaps = true
        }
        
        if !overlaps {
            continue
        }
        
        shard := rp.shards[partition.ShardID]
        if shard == nil {
            continue
        }
        
        shard.mu.RLock()
        for k, v := range shard.data {
            keyBytes := []byte(k)
            if bytes.Compare(keyBytes, startKey) >= 0 &&
               bytes.Compare(keyBytes, endKey) < 0 {
                result[k] = v
            }
        }
        shard.mu.RUnlock()
    }
    
    return result
}

// Split a partition into two
func (rp *RangePartitioner) SplitPartition(shardID string, splitKey []byte, newShardID string) bool {
    rp.mu.Lock()
    defer rp.mu.Unlock()
    
    // Find the partition to split
    idx := -1
    for i, partition := range rp.partitions {
        if partition.ShardID == shardID {
            idx = i
            break
        }
    }
    
    if idx == -1 {
        return false
    }
    
    oldPartition := rp.partitions[idx]
    
    // Create two new partitions
    partition1 := RangePartition{
        StartKey: oldPartition.StartKey,
        EndKey:   splitKey,
        ShardID:  shardID,
    }
    
    partition2 := RangePartition{
        StartKey: splitKey,
        EndKey:   oldPartition.EndKey,
        ShardID:  newShardID,
    }
    
    // Replace old partition with new ones
    rp.partitions[idx] = partition1
    rp.partitions = append(rp.partitions[:idx+1], append([]RangePartition{partition2}, rp.partitions[idx+1:]...)...)
    
    // Create new shard and migrate data
    rp.shards[newShardID] = &Shard{
        data: make(map[string]interface{}),
    }
    
    oldShard := rp.shards[shardID]
    newShard := rp.shards[newShardID]
    
    oldShard.mu.Lock()
    newShard.mu.Lock()
    
    for k, v := range oldShard.data {
        if bytes.Compare([]byte(k), splitKey) >= 0 {
            newShard.data[k] = v
            delete(oldShard.data, k)
        }
    }
    
    newShard.mu.Unlock()
    oldShard.mu.Unlock()
    
    return true
}
```

---

## Complete Examples

### Example 1: Distributed Key-Value Store with Raft

Here's a complete example combining Raft consensus with a replicated key-value store.

```go
package main

import (
    "context"
    "fmt"
    "time"
)

type KVCommand struct {
    Type  string // "set" or "delete"
    Key   string
    Value string
}

type KVStore struct {
    raft *RaftNode
    data map[string]string
}

func NewKVStore(nodeID int, peers []int) *KVStore {
    return &KVStore{
        raft: NewRaftNode(nodeID, peers),
        data: make(map[string]string),
    }
}

func (kv *KVStore) Start(ctx context.Context) {
    kv.raft.Start(ctx)
    go kv.applyCommittedEntries(ctx)
}

func (kv *KVStore) applyCommittedEntries(ctx context.Context) {
    ticker := time.NewTicker(10 * time.Millisecond)
    defer ticker.Stop()
    
    lastApplied := 0
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            kv.raft.mu.Lock()
            commitIndex := kv.raft.commitIndex
            log := kv.raft.log
            kv.raft.mu.Unlock()
            
            for lastApplied < commitIndex {
                lastApplied++
                entry := log[lastApplied]
                
                if cmd, ok := entry.Command.(KVCommand); ok {
                    switch cmd.Type {
                    case "set":
                        kv.data[cmd.Key] = cmd.Value
                    case "delete":
                        delete(kv.data, cmd.Key)
                    }
                }
            }
        }
    }
}

func (kv *KVStore) Set(key, value string) bool {
    cmd := KVCommand{
        Type:  "set",
        Key:   key,
        Value: value,
    }
    
    return kv.raft.Submit(cmd)
}

func (kv *KVStore) Get(key string) (string, bool) {
    value, ok := kv.data[key]
    return value, ok
}

func main() {
    ctx := context.Background()
    
    // Create 3-node cluster
    store1 := NewKVStore(1, []int{2, 3})
    store2 := NewKVStore(2, []int{1, 3})
    store3 := NewKVStore(3, []int{1, 2})
    
    store1.Start(ctx)
    store2.Start(ctx)
    store3.Start(ctx)
    
    // Wait for leader election
    time.Sleep(500 * time.Millisecond)
    
    // Perform operations
    store1.Set("key1", "value1")
    store1.Set("key2", "value2")
    
    time.Sleep(100 * time.Millisecond)
    
    // Read from any node
    if value, ok := store2.Get("key1"); ok {
        fmt.Printf("key1 = %s\n", value)
    }
}
```

### Example 2: Partitioned Store with Replication

```rust
use std::collections::HashMap;
use std::sync::Arc;

// Combining consistent hashing with replication
struct DistributedStore {
    partitioner: Arc<PartitionedStore>,
}

impl DistributedStore {
    fn new(num_shards: usize, replicas: usize) -> Self {
        let store = PartitionedStore::new(replicas);
        
        // Add shards
        for i in 0..num_shards {
            let shard_id = format!("shard-{}", i);
            store.add_shard(shard_id);
        }
        
        Self {
            partitioner: Arc::new(store),
        }
    }
    
    async fn put(&self, key: String, value: Vec<u8>) {
        self.partitioner.put(key, value);
    }
    
    async fn get(&self, key: &str) -> Option<Vec<u8>> {
        self.partitioner.get(key)
    }
}

#[tokio::main]
async fn main() {
    let store = DistributedStore::new(5, 3);
    
    store.put("user:123".to_string(), b"Alice".to_vec()).await;
    store.put("user:456".to_string(), b"Bob".to_vec()).await;
    
    if let Some(value) = store.get("user:123").await {
        println!("Found user: {:?}", String::from_utf8(value));
    }
}
```

## Best Practices

1. **Consensus**:
   - Use Raft for understandability and production systems
   - Ensure odd number of nodes (3, 5, 7) for proper majority
   - Monitor leader election frequency
   - Implement log compaction for long-running systems

2. **Replication**:
   - Choose synchronous for consistency, asynchronous for performance
   - Implement health checks and automatic failover
   - Use vector clocks or CRDTs for multi-master scenarios
   - Monitor replication lag

3. **Partitioning**:
   - Use consistent hashing for even distribution
   - Implement virtual nodes to handle heterogeneous hardware
   - Plan for rebalancing when adding/removing nodes
   - Consider data locality for performance

4. **General**:
   - Always handle network partitions gracefully
   - Implement proper monitoring and alerting
   - Use exponential backoff for retries
   - Test with chaos engineering tools
   - Document failure scenarios and recovery procedures

## Further Reading

- "Designing Data-Intensive Applications" by Martin Kleppmann
- Raft paper: "In Search of an Understandable Consensus Algorithm"
- "Paxos Made Simple" by Leslie Lamport
- Amazon's Dynamo paper
- Google's Spanner paper

# Distributed Systems Implementation Examples

This repository contains comprehensive implementations of distributed systems concepts in both Go and Rust, including consensus algorithms, replication strategies, and partitioning techniques.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Examples](#examples)
- [Testing](#testing)
- [Performance Considerations](#performance-considerations)
- [Production Considerations](#production-considerations)

## Overview

This guide demonstrates practical implementations of:

1. **Consensus Algorithms**
   - Raft (leader election, log replication)
   - Paxos (basic implementation)

2. **Replication Strategies**
   - Primary-Backup replication
   - Multi-Master with Vector Clocks

3. **Partitioning Techniques**
   - Consistent Hashing
   - Range Partitioning

## Prerequisites

### Go
- Go 1.19 or higher
- No external dependencies for core implementations

```bash
# Install Go
wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz
sudo tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz
export PATH=$PATH:/usr/local/go/bin
```

### Rust
- Rust 1.70 or higher
- Tokio for async runtime

```bash
# Install Rust
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Add dependencies to Cargo.toml
tokio = { version = "1.35", features = ["full"] }
async-trait = "0.1"
rand = "0.8"
sha2 = "0.10"
```

## Project Structure

```
distributed-systems/
├── go/
│   ├── consensus/
│   │   ├── raft.go
│   │   └── paxos.go
│   ├── replication/
│   │   ├── primary_backup.go
│   │   └── multi_master.go
│   ├── partitioning/
│   │   ├── consistent_hash.go
│   │   └── range_partition.go
│   ├── examples/
│   │   ├── kv_store.go
│   │   └── distributed_cache.go
│   └── tests/
│       └── *_test.go
│
├── rust/
│   ├── src/
│   │   ├── consensus/
│   │   │   └── raft.rs
│   │   ├── replication/
│   │   │   └── primary_backup.rs
│   │   ├── partitioning/
│   │   │   └── consistent_hash.rs
│   │   └── lib.rs
│   ├── examples/
│   │   └── kv_store.rs
│   └── tests/
│       └── integration_test.rs
│
└── docs/
    └── distributed-systems-guide.md
```

## Quick Start

### Go Example: Distributed Key-Value Store

```go
package main

import (
    "context"
    "fmt"
    "time"
)

func main() {
    ctx := context.Background()
    
    // Create a 3-node Raft cluster
    node1 := NewKVStore(1, []int{2, 3})
    node2 := NewKVStore(2, []int{1, 3})
    node3 := NewKVStore(3, []int{1, 2})
    
    // Start all nodes
    node1.Start(ctx)
    node2.Start(ctx)
    node3.Start(ctx)
    
    // Wait for leader election
    time.Sleep(500 * time.Millisecond)
    
    // Write to the cluster (will automatically go to leader)
    node1.Set("user:123", "Alice")
    node1.Set("user:456", "Bob")
    
    // Wait for replication
    time.Sleep(100 * time.Millisecond)
    
    // Read from any node
    if value, ok := node2.Get("user:123"); ok {
        fmt.Printf("Found user: %s\n", value)
    }
}
```

Run:
```bash
go run examples/kv_store.go
```

### Rust Example: Partitioned Store

```rust
use std::sync::Arc;

#[tokio::main]
async fn main() {
    // Create partitioned store with 3 replicas
    let store = Arc::new(PartitionedStore::new(3));
    
    // Add shards
    for i in 0..5 {
        store.add_shard(format!("shard-{}", i));
    }
    
    // Write data
    for i in 0..100 {
        let key = format!("user:{}", i);
        let value = format!("data-{}", i).into_bytes();
        store.put(key, value);
    }
    
    // Read data
    if let Some(value) = store.get("user:42") {
        println!("Found: {:?}", String::from_utf8(value));
    }
}
```

Run:
```bash
cargo run --example kv_store
```

## Examples

### 1. Simple Consensus with Raft

This example shows basic leader election and log replication:

```go
// Leader election happens automatically
nodes := []RaftNode{
    NewRaftNode(1, []int{2, 3}),
    NewRaftNode(2, []int{1, 3}),
    NewRaftNode(3, []int{1, 2}),
}

// Start all nodes
for _, node := range nodes {
    node.Start(context.Background())
}

// After election, submit commands to leader
leader.Submit(Command{Type: "SET", Key: "x", Value: "10"})
```

### 2. Primary-Backup Replication

```go
// Create backup nodes
backup1 := NewBackupNode()
backup2 := NewBackupNode()

// Create primary with backups
primary := NewPrimaryNode([]ReplicationClient{backup1, backup2})

// Writes go to primary, automatically replicated
primary.Set("key", "value")

// Reads can come from any node
value, _ := backup1.Get("key")
```

### 3. Consistent Hashing for Load Distribution

```go
// Create consistent hash ring
ch := NewConsistentHash(150) // 150 virtual nodes per server

// Add servers
ch.AddNode("server1")
ch.AddNode("server2")
ch.AddNode("server3")

// Route requests
server := ch.GetNode("user:12345")
fmt.Printf("Route to: %s\n", server)

// Add new server - minimal redistribution
ch.AddNode("server4")
```

### 4. Multi-Master with Conflict Detection

```go
// Create two master nodes
node1 := NewMultiMasterNode("node1", []ReplicationPeer{})
node2 := NewMultiMasterNode("node2", []ReplicationPeer{})

// Concurrent writes to same key
node1.Put("counter", 1)
node2.Put("counter", 2)

// Detect conflicts
versions := node1.Get("counter")
if len(versions) > 1 {
    fmt.Println("Conflict detected!")
    // Resolve using application logic
    resolved, _ := node1.Resolve("counter")
}
```

### 5. Range Partitioning with Auto-Splitting

```go
// Create range partitioner
rp := NewRangePartitioner()

// Initial partition
rp.AddPartition([]byte("a"), []byte("z"), "shard1")

// Add data
for i := 'a'; i <= 'z'; i++ {
    rp.Put([]byte{byte(i)}, i)
}

// Split when shard gets too large
rp.SplitPartition("shard1", []byte("m"), "shard2")

// Range queries span partitions automatically
results := rp.RangeQuery([]byte("d"), []byte("q"))
```

## Testing

### Go Tests

Run all tests:
```bash
cd go
go test ./...
```

Run specific tests:
```bash
go test -run TestRaftLeaderElection
go test -run TestConsistentHashing
```

Run with race detection:
```bash
go test -race ./...
```

Run benchmarks:
```bash
go test -bench=.
```

### Rust Tests

Run all tests:
```bash
cd rust
cargo test
```

Run specific tests:
```bash
cargo test test_raft_state_transitions
cargo test test_consistent_hash
```

Run with output:
```bash
cargo test -- --nocapture
```

Run benchmarks:
```bash
cargo bench
```

## Performance Considerations

### Raft Consensus
- **Throughput**: ~10K-50K ops/sec (depends on network latency)
- **Latency**: 1-2 RTTs for committed writes
- **Optimization**: Batch log entries, pipeline RPCs

```go
// Batching example
batch := []Command{}
for cmd := range commandQueue {
    batch = append(batch, cmd)
    if len(batch) >= 100 {
        leader.SubmitBatch(batch)
        batch = []Command{}
    }
}
```

### Consistent Hashing
- **Lookup**: O(log N) where N is number of virtual nodes
- **Virtual Nodes**: 100-200 per server for good balance
- **Memory**: ~100 bytes per virtual node

```go
// Tuning virtual nodes
ch := NewConsistentHash(150) // Good balance
ch := NewConsistentHash(500) // Better distribution, more memory
```

### Replication
- **Sync Replication**: Stronger consistency, higher latency
- **Async Replication**: Lower latency, eventual consistency
- **Quorum**: Read/Write from majority (R + W > N)

```go
// Quorum configuration
type QuorumConfig struct {
    N int // Total replicas
    W int // Write quorum
    R int // Read quorum
}

config := QuorumConfig{N: 5, W: 3, R: 3} // Strong consistency
config := QuorumConfig{N: 5, W: 1, R: 1} // High performance
```

## Production Considerations

### 1. Monitoring

Essential metrics to track:

```go
type Metrics struct {
    LeaderElections      int64
    LogReplicationLag    time.Duration
    CommitIndex          int64
    AppliedIndex         int64
    TermNumber           int64
    ClusterSize          int
    HeartbeatFailures    int64
}
```

### 2. Configuration Management

```yaml
# config.yaml
raft:
  election_timeout: 150ms-300ms
  heartbeat_interval: 50ms
  max_log_size: 10GB
  snapshot_interval: 1000 entries

replication:
  mode: synchronous  # or asynchronous
  quorum_size: 2
  timeout: 100ms

partitioning:
  strategy: consistent_hash
  virtual_nodes: 150
  replication_factor: 3
```

### 3. Failure Handling

```go
// Health checking
func (n *RaftNode) HealthCheck() error {
    if time.Since(n.lastHeartbeat) > heartbeatTimeout {
        return ErrNoLeader
    }
    
    if n.state == Leader && n.quorumReachable() < majority {
        return ErrLostQuorum
    }
    
    return nil
}

// Automatic recovery
func (n *RaftNode) MonitorHealth(ctx context.Context) {
    ticker := time.NewTicker(5 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            if err := n.HealthCheck(); err != nil {
                log.Errorf("Health check failed: %v", err)
                n.TriggerRecovery()
            }
        }
    }
}
```

### 4. Data Persistence

```go
// Snapshot for fast recovery
type Snapshot struct {
    LastIndex int64
    LastTerm  int64
    Data      []byte
}

func (n *RaftNode) CreateSnapshot() *Snapshot {
    n.mu.RLock()
    defer n.mu.RUnlock()
    
    return &Snapshot{
        LastIndex: n.lastApplied,
        LastTerm:  n.log[n.lastApplied].Term,
        Data:      n.serializeState(),
    }
}

func (n *RaftNode) RestoreSnapshot(snap *Snapshot) {
    n.mu.Lock()
    defer n.mu.Unlock()
    
    n.deserializeState(snap.Data)
    n.log = n.log[:1] // Keep only dummy entry
    n.lastApplied = snap.LastIndex
    n.commitIndex = snap.LastIndex
}
```

### 5. Network Optimization

```go
// Connection pooling
type ConnectionPool struct {
    pools map[int]*Pool
}

// Compression for large payloads
func CompressEntries(entries []LogEntry) []byte {
    // Use snappy or zstd for fast compression
}

// Batching RPCs
func (n *RaftNode) SendBatchAppendEntries() {
    for _, peer := range n.peers {
        entries := n.getPendingEntries(peer)
        if len(entries) > 0 {
            n.sendAppendEntries(peer, entries)
        }
    }
}
```

### 6. Security

```go
// TLS for inter-node communication
tlsConfig := &tls.Config{
    Certificates: []tls.Certificate{cert},
    ClientAuth:   tls.RequireAndVerifyClientCert,
    ClientCAs:    caPool,
}

// Authentication
func (n *RaftNode) AuthenticateRequest(req *AppendEntriesRequest) error {
    // Verify signature or token
    return verifyHMAC(req, n.sharedSecret)
}
```

## Common Pitfalls and Solutions

### 1. Split Brain

**Problem**: Network partition causes multiple leaders

**Solution**: Ensure proper quorum checks
```go
func (n *RaftNode) HasQuorum() bool {
    reachable := 1 // self
    for _, peer := range n.peers {
        if n.canReach(peer) {
            reachable++
        }
    }
    return reachable > len(n.peers)/2
}
```

### 2. Data Loss

**Problem**: Node fails before replication completes

**Solution**: Use fsync for durability
```go
func (n *RaftNode) AppendLog(entry LogEntry) error {
    // Write to disk
    if err := n.wal.Append(entry); err != nil {
        return err
    }
    
    // Force sync to disk
    if err := n.wal.Sync(); err != nil {
        return err
    }
    
    n.log = append(n.log, entry)
    return nil
}
```

### 3. Thundering Herd

**Problem**: All nodes timeout simultaneously

**Solution**: Randomized timeouts
```go
func randomTimeout() time.Duration {
    base := 150 * time.Millisecond
    jitter := time.Duration(rand.Intn(150)) * time.Millisecond
    return base + jitter
}
```

## Resources

### Papers
- [In Search of an Understandable Consensus Algorithm (Raft)](https://raft.github.io/raft.pdf)
- [Paxos Made Simple](https://lamport.azurewebsites.net/pubs/paxos-simple.pdf)
- [Amazon Dynamo](https://www.allthingsdistributed.com/files/amazon-dynamo-sosp2007.pdf)
- [Google Spanner](https://research.google/pubs/pub39966/)

### Books
- "Designing Data-Intensive Applications" by Martin Kleppmann
- "Distributed Systems" by Maarten van Steen and Andrew S. Tanenbaum
- "Database Internals" by Alex Petrov

### Online Resources
- [Raft Visualization](https://raft.github.io/)
- [Jepsen: Distributed Systems Safety Research](https://jepsen.io/)
- [Papers We Love](https://paperswelove.org/)

## Contributing

Contributions are welcome! Please ensure:
1. All tests pass
2. Code follows language idioms
3. Documentation is updated
4. Performance benchmarks are included

## License

MIT License - see LICENSE file for details

## Acknowledgments

These implementations are based on research papers and production systems from:
- Diego Ongaro and John Ousterhout (Raft)
- Leslie Lamport (Paxos)
- Amazon (Dynamo)
- Google (Spanner, Bigtable)

```go
package main

import (
    "context"
    "testing"
    "time"
)

// Test Raft consensus
func TestRaftLeaderElection(t *testing.T) {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    // Create 3-node cluster
    node1 := NewRaftNode(1, []int{2, 3})
    node2 := NewRaftNode(2, []int{1, 3})
    node3 := NewRaftNode(3, []int{1, 2})
    
    node1.Start(ctx)
    node2.Start(ctx)
    node3.Start(ctx)
    
    // Wait for leader election
    time.Sleep(500 * time.Millisecond)
    
    // Count leaders
    leaders := 0
    if node1.state == Leader {
        leaders++
    }
    if node2.state == Leader {
        leaders++
    }
    if node3.state == Leader {
        leaders++
    }
    
    if leaders != 1 {
        t.Errorf("Expected 1 leader, got %d", leaders)
    }
}

func TestRaftLogReplication(t *testing.T) {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    store1 := NewKVStore(1, []int{2, 3})
    store2 := NewKVStore(2, []int{1, 3})
    store3 := NewKVStore(3, []int{1, 2})
    
    store1.Start(ctx)
    store2.Start(ctx)
    store3.Start(ctx)
    
    time.Sleep(500 * time.Millisecond)
    
    // Submit command to leader
    success := store1.Set("key1", "value1")
    if !success {
        success = store2.Set("key1", "value1")
    }
    if !success {
        success = store3.Set("key1", "value1")
    }
    
    if !success {
        t.Fatal("Failed to submit command")
    }
    
    time.Sleep(200 * time.Millisecond)
    
    // Verify replication
    checks := 0
    if val, ok := store1.Get("key1"); ok && val == "value1" {
        checks++
    }
    if val, ok := store2.Get("key1"); ok && val == "value1" {
        checks++
    }
    if val, ok := store3.Get("key1"); ok && val == "value1" {
        checks++
    }
    
    if checks < 2 {
        t.Errorf("Expected at least 2 nodes to have replicated value, got %d", checks)
    }
}

// Test Consistent Hashing
func TestConsistentHashing(t *testing.T) {
    ch := NewConsistentHash(150)
    
    ch.AddNode("node1")
    ch.AddNode("node2")
    ch.AddNode("node3")
    
    // Test key distribution
    distribution := make(map[string]int)
    
    for i := 0; i < 10000; i++ {
        key := fmt.Sprintf("key%d", i)
        node := ch.GetNode(key)
        distribution[node]++
    }
    
    // Each node should get roughly 1/3 of keys (allow 20% variance)
    for node, count := range distribution {
        expected := 10000 / 3
        variance := float64(count-expected) / float64(expected)
        
        if variance > 0.2 || variance < -0.2 {
            t.Errorf("Node %s has poor distribution: %d keys (%.1f%% variance)", 
                     node, count, variance*100)
        }
    }
}

func TestConsistentHashingStability(t *testing.T) {
    ch := NewConsistentHash(150)
    
    ch.AddNode("node1")
    ch.AddNode("node2")
    ch.AddNode("node3")
    
    // Record initial assignments
    assignments := make(map[string]string)
    for i := 0; i < 1000; i++ {
        key := fmt.Sprintf("key%d", i)
        assignments[key] = ch.GetNode(key)
    }
    
    // Add a new node
    ch.AddNode("node4")
    
    // Count how many keys moved
    moved := 0
    for key, oldNode := range assignments {
        newNode := ch.GetNode(key)
        if oldNode != newNode {
            moved++
        }
    }
    
    // Should move approximately 1/4 of keys (new node takes 1/4 of load)
    expectedMove := 250
    variance := float64(moved-expectedMove) / float64(expectedMove)
    
    if variance > 0.5 || variance < -0.5 {
        t.Errorf("Expected ~%d keys to move, got %d (%.1f%% variance)", 
                 expectedMove, moved, variance*100)
    }
}

// Test Primary-Backup Replication
func TestPrimaryBackupReplication(t *testing.T) {
    backup1 := NewBackupNode()
    backup2 := NewBackupNode()
    
    backups := []ReplicationClient{backup1, backup2}
    primary := NewPrimaryNode(backups)
    
    // Set a value
    err := primary.Set("key1", "value1")
    if err != nil {
        t.Fatalf("Failed to set value: %v", err)
    }
    
    // Verify on primary
    val, ok := primary.Get("key1")
    if !ok || val != "value1" {
        t.Error("Value not found on primary")
    }
    
    // Verify on backups
    val, ok = backup1.Get("key1")
    if !ok || val != "value1" {
        t.Error("Value not replicated to backup1")
    }
    
    val, ok = backup2.Get("key1")
    if !ok || val != "value1" {
        t.Error("Value not replicated to backup2")
    }
}

func TestBackupPromotion(t *testing.T) {
    backup := NewBackupNode()
    
    // Simulate some replicated operations
    backup.Replicate(Operation{
        Type:   "set",
        Key:    "key1",
        Value:  "value1",
        SeqNum: 1,
    })
    
    backup.Replicate(Operation{
        Type:   "set",
        Key:    "key2",
        Value:  "value2",
        SeqNum: 2,
    })
    
    // Promote to primary
    primary := backup.Promote()
    
    // Verify data is preserved
    val, ok := primary.Get("key1")
    if !ok || val != "value1" {
        t.Error("Data lost during promotion")
    }
    
    val, ok = primary.Get("key2")
    if !ok || val != "value2" {
        t.Error("Data lost during promotion")
    }
}

// Test Vector Clocks and Multi-Master
func TestVectorClocks(t *testing.T) {
    vc1 := make(VectorClock)
    vc1["node1"] = 1
    vc1["node2"] = 2
    
    vc2 := make(VectorClock)
    vc2["node1"] = 2
    vc2["node2"] = 2
    
    // vc1 happens before vc2
    if !vc1.HappensBefore(vc2) {
        t.Error("Expected vc1 to happen before vc2")
    }
    
    if vc2.HappensBefore(vc1) {
        t.Error("vc2 should not happen before vc1")
    }
}

func TestConcurrentVectorClocks(t *testing.T) {
    vc1 := make(VectorClock)
    vc1["node1"] = 2
    vc1["node2"] = 1
    
    vc2 := make(VectorClock)
    vc2["node1"] = 1
    vc2["node2"] = 2
    
    // These are concurrent
    if !vc1.ConcurrentWith(vc2) {
        t.Error("Expected vc1 and vc2 to be concurrent")
    }
    
    if vc1.HappensBefore(vc2) || vc2.HappensBefore(vc1) {
        t.Error("Concurrent clocks should not have happens-before relationship")
    }
}

func TestMultiMasterReplication(t *testing.T) {
    node1 := NewMultiMasterNode("node1", []ReplicationPeer{})
    node2 := NewMultiMasterNode("node2", []ReplicationPeer{})
    
    // Both nodes write to same key
    node1.Put("key1", "value1")
    node2.Put("key1", "value2")
    
    // Get versions from node1
    versions := node1.Get("key1")
    if len(versions) != 1 {
        t.Errorf("Expected 1 version, got %d", len(versions))
    }
    
    // Simulate replication from node2
    versions2 := node2.Get("key1")
    if len(versions2) > 0 {
        node1.Merge("key1", versions2[0])
    }
    
    // Should now have 2 concurrent versions
    versions = node1.Get("key1")
    if len(versions) != 2 {
        t.Errorf("Expected 2 concurrent versions after merge, got %d", len(versions))
    }
}

// Test Range Partitioning
func TestRangePartitioning(t *testing.T) {
    rp := NewRangePartitioner()
    
    rp.AddPartition([]byte("a"), []byte("m"), "shard1")
    rp.AddPartition([]byte("m"), []byte("z"), "shard2")
    
    // Test key routing
    if shard := rp.GetShard([]byte("apple")); shard != "shard1" {
        t.Errorf("Expected shard1, got %s", shard)
    }
    
    if shard := rp.GetShard([]byte("zebra")); shard != "shard2" {
        t.Errorf("Expected shard2, got %s", shard)
    }
}

func TestRangeQuery(t *testing.T) {
    rp := NewRangePartitioner()
    
    rp.AddPartition([]byte("a"), []byte("m"), "shard1")
    rp.AddPartition([]byte("m"), []byte("z"), "shard2")
    
    // Add some data
    rp.Put([]byte("apple"), "fruit")
    rp.Put([]byte("banana"), "fruit")
    rp.Put([]byte("mango"), "fruit")
    rp.Put([]byte("orange"), "fruit")
    
    // Range query
    results := rp.RangeQuery([]byte("b"), []byte("n"))
    
    if len(results) != 2 {
        t.Errorf("Expected 2 results, got %d", len(results))
    }
    
    if _, ok := results["banana"]; !ok {
        t.Error("Expected to find banana")
    }
    
    if _, ok := results["mango"]; !ok {
        t.Error("Expected to find mango")
    }
}

func TestPartitionSplitting(t *testing.T) {
    rp := NewRangePartitioner()
    
    rp.AddPartition([]byte("a"), []byte("z"), "shard1")
    
    // Add data
    for i := byte('a'); i <= 'z'; i++ {
        key := []byte{i}
        rp.Put(key, i)
    }
    
    // Split partition
    success := rp.SplitPartition("shard1", []byte("m"), "shard2")
    if !success {
        t.Fatal("Failed to split partition")
    }
    
    // Verify data distribution
    shard1Count := 0
    shard2Count := 0
    
    for i := byte('a'); i <= 'z'; i++ {
        key := []byte{i}
        shard := rp.GetShard(key)
        
        if shard == "shard1" {
            shard1Count++
        } else if shard == "shard2" {
            shard2Count++
        }
        
        // Verify value still accessible
        val, ok := rp.Get(key)
        if !ok || val.(byte) != i {
            t.Errorf("Lost data for key %c after split", i)
        }
    }
    
    if shard1Count != 12 || shard2Count != 14 {
        t.Errorf("Unexpected distribution: shard1=%d, shard2=%d", shard1Count, shard2Count)
    }
}

// Benchmark tests
func BenchmarkConsistentHashGet(b *testing.B) {
    ch := NewConsistentHash(150)
    ch.AddNode("node1")
    ch.AddNode("node2")
    ch.AddNode("node3")
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        key := fmt.Sprintf("key%d", i%1000)
        ch.GetNode(key)
    }
}

func BenchmarkRaftSubmit(b *testing.B) {
    ctx, cancel := context.WithCancel(context.Background())
    defer cancel()
    
    store := NewKVStore(1, []int{2, 3})
    store.Start(ctx)
    
    time.Sleep(100 * time.Millisecond)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        key := fmt.Sprintf("key%d", i)
        store.Set(key, "value")
    }
}

func BenchmarkPrimaryBackupWrite(b *testing.B) {
    backup1 := NewBackupNode()
    backup2 := NewBackupNode()
    
    backups := []ReplicationClient{backup1, backup2}
    primary := NewPrimaryNode(backups)
    
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        key := fmt.Sprintf("key%d", i)
        primary.Set(key, "value")
    }
}

```

```rust

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use tokio::time::{sleep, Duration};

    #[test]
    fn test_raft_state_transitions() {
        let node = RaftNode::new(1, vec![2, 3]);
        assert_eq!(node.state, State::Follower);
        
        // Initial state should be follower
        assert_eq!(node.current_term, 0);
        assert_eq!(node.voted_for, None);
    }

    #[test]
    fn test_raft_log_operations() {
        let mut node = RaftNode::new(1, vec![2, 3]);
        
        // Become leader
        node.state = State::Leader;
        
        // Submit command
        let result = node.submit(b"test_command".to_vec());
        assert!(result);
        
        // Verify log entry
        assert_eq!(node.log.len(), 2); // Including dummy entry
        assert_eq!(node.log[1].command, b"test_command");
    }

    #[test]
    fn test_raft_append_entries_success() {
        let mut follower = RaftNode::new(1, vec![2, 3]);
        
        let request = AppendEntriesRequest {
            term: 1,
            leader_id: 2,
            prev_log_index: 0,
            prev_log_term: 0,
            entries: vec![LogEntry {
                term: 1,
                command: b"test".to_vec(),
            }],
            leader_commit: 0,
        };
        
        let response = follower.handle_append_entries(request);
        
        assert!(response.success);
        assert_eq!(follower.log.len(), 2);
        assert_eq!(follower.current_term, 1);
    }

    #[test]
    fn test_raft_append_entries_term_check() {
        let mut follower = RaftNode::new(1, vec![2, 3]);
        follower.current_term = 5;
        
        let request = AppendEntriesRequest {
            term: 3,
            leader_id: 2,
            prev_log_index: 0,
            prev_log_term: 0,
            entries: vec![],
            leader_commit: 0,
        };
        
        let response = follower.handle_append_entries(request);
        
        assert!(!response.success);
        assert_eq!(response.term, 5);
    }

    #[test]
    fn test_raft_request_vote() {
        let mut node = RaftNode::new(1, vec![2, 3]);
        
        let request = RequestVoteRequest {
            term: 2,
            candidate_id: 2,
            last_log_index: 0,
            last_log_term: 0,
        };
        
        let response = node.handle_request_vote(request);
        
        assert!(response.vote_granted);
        assert_eq!(node.voted_for, Some(2));
        assert_eq!(node.current_term, 2);
    }

    #[test]
    fn test_raft_vote_only_once() {
        let mut node = RaftNode::new(1, vec![2, 3]);
        
        // First vote request
        let request1 = RequestVoteRequest {
            term: 2,
            candidate_id: 2,
            last_log_index: 0,
            last_log_term: 0,
        };
        
        let response1 = node.handle_request_vote(request1);
        assert!(response1.vote_granted);
        
        // Second vote request in same term
        let request2 = RequestVoteRequest {
            term: 2,
            candidate_id: 3,
            last_log_index: 0,
            last_log_term: 0,
        };
        
        let response2 = node.handle_request_vote(request2);
        assert!(!response2.vote_granted);
    }

    #[test]
    fn test_consistent_hash_basic() {
        let mut ch = ConsistentHash::new(100);
        
        ch.add_node("node1".to_string());
        ch.add_node("node2".to_string());
        ch.add_node("node3".to_string());
        
        // Test that keys are assigned to nodes
        let node1 = ch.get_node("key1").unwrap();
        assert!(["node1", "node2", "node3"].contains(&node1.as_str()));
        
        // Same key should always map to same node
        let node2 = ch.get_node("key1").unwrap();
        assert_eq!(node1, node2);
    }

    #[test]
    fn test_consistent_hash_distribution() {
        let mut ch = ConsistentHash::new(150);
        
        ch.add_node("node1".to_string());
        ch.add_node("node2".to_string());
        ch.add_node("node3".to_string());
        
        let mut distribution = HashMap::new();
        
        for i in 0..10000 {
            let key = format!("key{}", i);
            let node = ch.get_node(&key).unwrap();
            *distribution.entry(node).or_insert(0) += 1;
        }
        
        // Each node should get roughly 1/3 of keys
        for (node, count) in distribution.iter() {
            let variance = (*count as f64 - 3333.0) / 3333.0;
            assert!(
                variance.abs() < 0.2,
                "Node {} has poor distribution: {} keys ({:.1}% variance)",
                node,
                count,
                variance * 100.0
            );
        }
    }

    #[test]
    fn test_consistent_hash_stability() {
        let mut ch = ConsistentHash::new(150);
        
        ch.add_node("node1".to_string());
        ch.add_node("node2".to_string());
        ch.add_node("node3".to_string());
        
        // Record initial assignments
        let mut assignments = HashMap::new();
        for i in 0..1000 {
            let key = format!("key{}", i);
            let node = ch.get_node(&key).unwrap();
            assignments.insert(key, node);
        }
        
        // Add new node
        ch.add_node("node4".to_string());
        
        // Count moved keys
        let mut moved = 0;
        for (key, old_node) in assignments.iter() {
            let new_node = ch.get_node(key).unwrap();
            if old_node != &new_node {
                moved += 1;
            }
        }
        
        // Should move approximately 1/4 of keys
        let expected_move = 250;
        let variance = (moved as f64 - expected_move as f64) / expected_move as f64;
        
        assert!(
            variance.abs() < 0.5,
            "Expected ~{} keys to move, got {} ({:.1}% variance)",
            expected_move,
            moved,
            variance * 100.0
        );
    }

    #[test]
    fn test_consistent_hash_get_nodes() {
        let mut ch = ConsistentHash::new(150);
        
        ch.add_node("node1".to_string());
        ch.add_node("node2".to_string());
        ch.add_node("node3".to_string());
        
        let nodes = ch.get_nodes("test_key", 2);
        
        assert_eq!(nodes.len(), 2);
        assert_ne!(nodes[0], nodes[1]); // Should be different nodes
    }

    #[tokio::test]
    async fn test_primary_backup_replication() {
        let backup1 = Arc::new(BackupNode::new());
        let backup2 = Arc::new(BackupNode::new());
        
        let backups: Vec<Arc<dyn ReplicationClient>> = vec![
            backup1.clone(),
            backup2.clone(),
        ];
        
        let primary = PrimaryNode::new(backups);
        
        // Set a value
        primary.set("key1".to_string(), b"value1".to_vec())
            .await
            .expect("Failed to set value");
        
        // Verify on primary
        let value = primary.get("key1").expect("Value not found on primary");
        assert_eq!(value, b"value1");
        
        // Verify on backups
        let value = backup1.get("key1").expect("Value not replicated to backup1");
        assert_eq!(value, b"value1");
        
        let value = backup2.get("key1").expect("Value not replicated to backup2");
        assert_eq!(value, b"value1");
    }

    #[tokio::test]
    async fn test_backup_sequential_ordering() {
        let backup = BackupNode::new();
        
        // Operations in order
        let op1 = Operation {
            op_type: "set".to_string(),
            key: "key1".to_string(),
            value: Some(b"value1".to_vec()),
            seq_num: 1,
        };
        
        let result = backup.replicate(op1).await;
        assert!(result.is_ok());
        
        // Try to apply out-of-order operation
        let op3 = Operation {
            op_type: "set".to_string(),
            key: "key2".to_string(),
            value: Some(b"value2".to_vec()),
            seq_num: 3,
        };
        
        let result = backup.replicate(op3).await;
        assert!(result.is_err());
    }

    #[test]
    fn test_partitioned_store() {
        let store = PartitionedStore::new(3);
        
        store.add_shard("shard1".to_string());
        store.add_shard("shard2".to_string());
        store.add_shard("shard3".to_string());
        
        // Put and get
        store.put("test_key".to_string(), b"test_value".to_vec());
        
        let value = store.get("test_key").expect("Value not found");
        assert_eq!(value, b"test_value");
    }

    #[test]
    fn test_partitioned_store_replication() {
        let store = PartitionedStore::new(2); // 2 replicas
        
        store.add_shard("shard1".to_string());
        store.add_shard("shard2".to_string());
        store.add_shard("shard3".to_string());
        
        store.put("key1".to_string(), b"value1".to_vec());
        
        // Value should be stored on 2 shards
        let hash = store.hash.read().unwrap();
        let nodes = hash.get_nodes("key1", 2);
        
        assert_eq!(nodes.len(), 2);
        
        // Both shards should have the value
        let shards = store.shards.read().unwrap();
        for node_id in nodes {
            let shard = shards.get(&node_id).unwrap();
            let value = shard.get("key1").expect("Value not replicated");
            assert_eq!(value, b"value1");
        }
    }

    #[test]
    fn test_shard_operations() {
        let shard = Shard::new();
        
        shard.put("key1".to_string(), b"value1".to_vec());
        
        let value = shard.get("key1").expect("Value not found");
        assert_eq!(value, b"value1");
        
        let missing = shard.get("missing_key");
        assert!(missing.is_none());
    }
}

// Benchmark tests
#[cfg(test)]
mod benches {
    use super::*;
    use std::time::Instant;

    #[test]
    fn bench_consistent_hash_get() {
        let mut ch = ConsistentHash::new(150);
        
        ch.add_node("node1".to_string());
        ch.add_node("node2".to_string());
        ch.add_node("node3".to_string());
        
        let start = Instant::now();
        let iterations = 100000;
        
        for i in 0..iterations {
            let key = format!("key{}", i % 1000);
            ch.get_node(&key);
        }
        
        let duration = start.elapsed();
        let ops_per_sec = iterations as f64 / duration.as_secs_f64();
        
        println!("Consistent hash get: {:.0} ops/sec", ops_per_sec);
    }

    #[tokio::test]
    async fn bench_primary_backup_write() {
        let backup1 = Arc::new(BackupNode::new());
        let backup2 = Arc::new(BackupNode::new());
        
        let backups: Vec<Arc<dyn ReplicationClient>> = vec![
            backup1.clone(),
            backup2.clone(),
        ];
        
        let primary = PrimaryNode::new(backups);
        
        let start = Instant::now();
        let iterations = 1000;
        
        for i in 0..iterations {
            let key = format!("key{}", i);
            primary.set(key, b"value".to_vec()).await.unwrap();
        }
        
        let duration = start.elapsed();
        let ops_per_sec = iterations as f64 / duration.as_secs_f64();
        
        println!("Primary-backup write: {:.0} ops/sec", ops_per_sec);
    }

    #[test]
    fn bench_partitioned_store_operations() {
        let store = PartitionedStore::new(3);
        
        store.add_shard("shard1".to_string());
        store.add_shard("shard2".to_string());
        store.add_shard("shard3".to_string());
        
        let start = Instant::now();
        let iterations = 10000;
        
        for i in 0..iterations {
            let key = format!("key{}", i);
            store.put(key.clone(), b"value".to_vec());
            store.get(&key);
        }
        
        let duration = start.elapsed();
        let ops_per_sec = (iterations * 2) as f64 / duration.as_secs_f64();
        
        println!("Partitioned store: {:.0} ops/sec", ops_per_sec);
    }
}

// Integration tests
#[cfg(test)]
mod integration {
    use super::*;

    #[tokio::test]
    async fn test_full_distributed_store() {
        // Create a complete distributed store with partitioning and replication
        let store = PartitionedStore::new(2);
        
        // Add multiple shards
        for i in 0..5 {
            store.add_shard(format!("shard{}", i));
        }
        
        // Write many keys
        for i in 0..100 {
            let key = format!("user:{}", i);
            let value = format!("data{}", i).into_bytes();
            store.put(key, value);
        }
        
        // Read all keys back
        for i in 0..100 {
            let key = format!("user:{}", i);
            let value = store.get(&key).expect("Key not found");
            let expected = format!("data{}", i).into_bytes();
            assert_eq!(value, expected);
        }
        
        // Verify distribution across shards
        let shards = store.shards.read().unwrap();
        let mut counts = HashMap::new();
        
        for (shard_id, shard) in shards.iter() {
            let data = shard.data.read().unwrap();
            counts.insert(shard_id.clone(), data.len());
        }
        
        println!("Shard distribution: {:?}", counts);
    }

    #[tokio::test]
    async fn test_node_failure_and_recovery() {
        let backup1 = Arc::new(BackupNode::new());
        let backup2 = Arc::new(BackupNode::new());
        
        let backups: Vec<Arc<dyn ReplicationClient>> = vec![
            backup1.clone(),
            backup2.clone(),
        ];
        
        let primary = PrimaryNode::new(backups);
        
        // Write data
        for i in 0..10 {
            let key = format!("key{}", i);
            primary.set(key, b"value".to_vec()).await.unwrap();
        }
        
        // Verify all nodes have data
        for i in 0..10 {
            let key = format!("key{}", i);
            assert!(primary.get(&key).is_some());
            assert!(backup1.get(&key).is_some());
            assert!(backup2.get(&key).is_some());
        }
        
        // Simulate primary failure - promote backup
        // In real system, would detect failure and trigger promotion
        println!("Primary node failed, backup taking over...");
        
        // Backup becomes new primary (would need to add new backups in real system)
        let new_primary = PrimaryNode::new(vec![]);
        
        // Copy data from backup to new primary (simplified)
        // In reality, would use the backup's data directly
        for i in 0..10 {
            let key = format!("key{}", i);
            if let Some(value) = backup1.get(&key) {
                new_primary.data.write().unwrap().insert(key, value);
            }
        }
        
        // Verify data preserved
        for i in 0..10 {
            let key = format!("key{}", i);
            assert!(new_primary.get(&key).is_some());
        }
    }
}
```