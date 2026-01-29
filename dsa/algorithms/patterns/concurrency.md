# Comprehensive Guide to Concurrency Patterns in LeetCode

## Foundation: Understanding Concurrency Primitives

Before diving into patterns, master the fundamental synchronization primitives. Each language offers different abstractions:

**Rust**: Mutex, RwLock, Arc, channels (mpsc), atomic types
**Go**: Mutexes, channels, WaitGroups, atomic operations, context
**C**: pthreads, mutexes, condition variables, semaphores

### Core Principle
Concurrency problems are about **coordination**—ensuring multiple threads access shared resources safely while maintaining correctness and avoiding deadlocks.

---

## Pattern 1: Mutual Exclusion (Mutex-Based Synchronization)

**Mental Model**: A single key to a room. Only one thread holds the key at a time.

### Problem: Print in Order (LeetCode 1114)

**Problem Statement**: Three threads must print "first", "second", "third" in order.

**Expert Thought Process**:
1. Identify the constraint: sequential ordering despite concurrent execution
2. Recognize this as a **happens-before relationship** problem
3. Choose primitive: mutex + condition variable OR atomic counter

**Rust Solution** (Idiomatic):

```rust
use std::sync::{Arc, Condvar, Mutex};

struct Foo {
    counter: Arc<Mutex<i32>>,
    cv: Arc<Condvar>,
}

impl Foo {
    fn new() -> Self {
        Foo {
            counter: Arc::new(Mutex::new(0)),
            cv: Arc::new(Condvar::new()),
        }
    }

    fn first(&self, print_first: impl Fn()) {
        print_first();
        let mut count = self.counter.lock().unwrap();
        *count = 1;
        self.cv.notify_all();
    }

    fn second(&self, print_second: impl Fn()) {
        let mut count = self.counter.lock().unwrap();
        while *count != 1 {
            count = self.cv.wait(count).unwrap();
        }
        print_second();
        *count = 2;
        self.cv.notify_all();
    }

    fn third(&self, print_third: impl Fn()) {
        let mut count = self.counter.lock().unwrap();
        while *count != 2 {
            count = self.cv.wait(count).unwrap();
        }
        print_third();
    }
}
```

**Go Solution** (Channel-based, more idiomatic):

```go
type Foo struct {
    ch1 chan struct{}
    ch2 chan struct{}
}

func NewFoo() *Foo {
    return &Foo{
        ch1: make(chan struct{}),
        ch2: make(chan struct{}),
    }
}

func (f *Foo) First(printFirst func()) {
    printFirst()
    close(f.ch1) // Signal completion
}

func (f *Foo) Second(printSecond func()) {
    <-f.ch1 // Wait for first to complete
    printSecond()
    close(f.ch2)
}

func (f *Foo) Third(printThird func()) {
    <-f.ch2 // Wait for second to complete
    printThird()
}
```

**Key Insights**:
- **Rust**: Ownership model prevents data races at compile time. Condvar requires while-loop (spurious wakeups).
- **Go**: Channels are first-class primitives. Closing a channel broadcasts to all receivers.
- **Pattern**: Transform ordering constraint into state machine transitions.

---

## Pattern 2: Producer-Consumer with Bounded Buffer

**Mental Model**: Assembly line with limited staging area. Producers must wait when full, consumers when empty.

### Problem: Print FooBar Alternately (LeetCode 1115)

**Advanced Thought Process**:
1. Two threads, strict alternation → **ping-pong pattern**
2. Need bidirectional signaling
3. Options: two semaphores, two condition variables, or channels

**Rust Solution** (Using Atomics + Spin):

```rust
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;

struct FooBar {
    n: i32,
    foo_turn: Arc<AtomicBool>,
}

impl FooBar {
    fn new(n: i32) -> Self {
        FooBar {
            n,
            foo_turn: Arc::new(AtomicBool::new(true)),
        }
    }

    fn foo(&self, print_foo: impl Fn()) {
        for _ in 0..self.n {
            while !self.foo_turn.load(Ordering::Acquire) {
                std::hint::spin_loop(); // CPU hint for spin-wait
            }
            print_foo();
            self.foo_turn.store(false, Ordering::Release);
        }
    }

    fn bar(&self, print_bar: impl Fn()) {
        for _ in 0..self.n {
            while self.foo_turn.load(Ordering::Acquire) {
                std::hint::spin_loop();
            }
            print_bar();
            self.foo_turn.store(true, Ordering::Release);
        }
    }
}
```

**Go Solution** (Channel Ping-Pong):

```go
type FooBar struct {
    n       int
    fooTurn chan struct{}
    barTurn chan struct{}
}

func NewFooBar(n int) *FooBar {
    fb := &FooBar{
        n:       n,
        fooTurn: make(chan struct{}, 1),
        barTurn: make(chan struct{}, 1),
    }
    fb.fooTurn <- struct{}{} // Initialize: foo goes first
    return fb
}

func (fb *FooBar) Foo(printFoo func()) {
    for i := 0; i < fb.n; i++ {
        <-fb.fooTurn
        printFoo()
        fb.barTurn <- struct{}{}
    }
}

func (fb *FooBar) Bar(printBar func()) {
    for i := 0; i < fb.n; i++ {
        <-fb.barTurn
        printBar()
        fb.fooTurn <- struct{}{}
    }
}
```

**Performance Analysis**:
- **Rust atomic version**: Lock-free, ~5-10ns per operation on modern CPUs
- **Go channel version**: ~100-200ns overhead per send/receive
- **Trade-off**: Rust's atomics are faster but spin-waiting wastes CPU cycles

**Optimization Insight**: For high-contention scenarios, replace spin-loop with `std::thread::yield_now()` or use proper mutexes.

---

## Pattern 3: Reader-Writer Lock Pattern

**Mental Model**: Library with many readers, occasional writer. Readers can share access, writers need exclusivity.

### Problem: Web Crawler Multithreaded (LeetCode 1242)

**Expert Analysis**:
1. Need thread-safe set to track visited URLs
2. High read frequency (checking if visited), low write frequency (marking visited)
3. Classic RwLock use case

**Rust Solution** (Using RwLock):

```rust
use std::collections::HashSet;
use std::sync::{Arc, RwLock};

struct HtmlParser;
impl HtmlParser {
    fn get_urls(&self, url: &str) -> Vec<String> {
        vec![] // Stub
    }
}

fn crawl(start_url: String, html_parser: HtmlParser) -> Vec<String> {
    let visited = Arc::new(RwLock::new(HashSet::new()));
    let results = Arc::new(RwLock::new(Vec::new()));
    
    // Extract hostname for same-domain check
    let hostname = extract_hostname(&start_url);
    
    visited.write().unwrap().insert(start_url.clone());
    
    fn dfs(
        url: String,
        hostname: &str,
        parser: &HtmlParser,
        visited: &Arc<RwLock<HashSet<String>>>,
        results: &Arc<RwLock<Vec<String>>>,
    ) {
        results.write().unwrap().push(url.clone());
        
        let neighbors = parser.get_urls(&url);
        let mut to_visit = Vec::new();
        
        {
            let mut v = visited.write().unwrap();
            for neighbor in neighbors {
                if extract_hostname(&neighbor) == hostname && !v.contains(&neighbor) {
                    v.insert(neighbor.clone());
                    to_visit.push(neighbor);
                }
            }
        }
        
        // Parallel crawling
        std::thread::scope(|s| {
            for next_url in to_visit {
                let visited = Arc::clone(visited);
                let results = Arc::clone(results);
                s.spawn(move || {
                    dfs(next_url, hostname, parser, &visited, &results);
                });
            }
        });
    }
    
    dfs(start_url, &hostname, &html_parser, &visited, &results);
    Arc::try_unwrap(results).unwrap().into_inner().unwrap()
}

fn extract_hostname(url: &str) -> String {
    url.split('/').nth(2).unwrap_or("").to_string()
}
```

**Go Solution** (Using sync.Map):

```go
import "sync"

type HtmlParser interface {
    GetUrls(url string) []string
}

func crawl(startUrl string, htmlParser HtmlParser) []string {
    hostname := extractHostname(startUrl)
    visited := &sync.Map{}
    var results []string
    var mu sync.Mutex
    var wg sync.WaitGroup
    
    var dfs func(url string)
    dfs = func(url string) {
        defer wg.Done()
        
        mu.Lock()
        results = append(results, url)
        mu.Unlock()
        
        for _, neighbor := range htmlParser.GetUrls(url) {
            if extractHostname(neighbor) != hostname {
                continue
            }
            
            if _, loaded := visited.LoadOrStore(neighbor, true); !loaded {
                wg.Add(1)
                go dfs(neighbor)
            }
        }
    }
    
    visited.Store(startUrl, true)
    wg.Add(1)
    go dfs(startUrl)
    wg.Wait()
    
    return results
}

func extractHostname(url string) string {
    // Implementation
    return ""
}
```

**Critical Insight**: `sync.Map` in Go is optimized for read-heavy workloads with amortized O(1) reads when keys are stable.

---

## Pattern 4: Semaphore Pattern (Resource Limiting)

**Mental Model**: Token pool. Take token to enter, return when done. Limited concurrency.

### Problem: Building H2O (LeetCode 1117)

**Problem**: Synchronize H and O threads to form H₂O molecules.

**Thought Process**:
1. Constraint: 2H + 1O → molecule formation
2. Need **counting mechanism** + **barrier synchronization**
3. Semaphores naturally model counting

**Rust Solution** (Channel-based Semaphore):

```rust
use std::sync::mpsc::{channel, Sender, Receiver};
use std::sync::{Arc, Barrier};

struct H2O {
    h_sem: Arc<(Sender<()>, Receiver<()>)>,
    o_sem: Arc<(Sender<()>, Receiver<()>)>,
}

impl H2O {
    fn new() -> Self {
        let h_sem = channel();
        let o_sem = channel();
        
        // Initialize with capacity for 2H
        h_sem.0.send(()).unwrap();
        h_sem.0.send(()).unwrap();
        
        H2O {
            h_sem: Arc::new(h_sem),
            o_sem: Arc::new(o_sem),
        }
    }

    fn hydrogen(&self, release_hydrogen: impl Fn()) {
        self.h_sem.1.recv().unwrap(); // Acquire H token
        release_hydrogen();
        self.o_sem.0.send(()).unwrap(); // Signal O can proceed
    }

    fn oxygen(&self, release_oxygen: impl Fn()) {
        // Wait for 2 H tokens
        self.o_sem.1.recv().unwrap();
        self.o_sem.1.recv().unwrap();
        
        release_oxygen();
        
        // Release 2 H tokens for next molecule
        self.h_sem.0.send(()).unwrap();
        self.h_sem.0.send(()).unwrap();
    }
}
```

**Go Solution** (Using Channels as Semaphores):

```go
type H2O struct {
    hSem chan struct{}
    oSem chan struct{}
}

func NewH2O() *H2O {
    h2o := &H2O{
        hSem: make(chan struct{}, 2),
        oSem: make(chan struct{}, 0),
    }
    // Initialize with 2 H permits
    h2o.hSem <- struct{}{}
    h2o.hSem <- struct{}{}
    return h2o
}

func (h2o *H2O) Hydrogen(releaseHydrogen func()) {
    <-h2o.hSem
    releaseHydrogen()
    h2o.oSem <- struct{}{}
}

func (h2o *H2O) Oxygen(releaseOxygen func()) {
    <-h2o.oSem
    <-h2o.oSem
    releaseOxygen()
    h2o.hSem <- struct{}{}
    h2o.hSem <- struct{}{}
}
```

**Advanced Optimization**: Use `std::sync::Semaphore` (unstable in Rust) or external crate like `tokio::sync::Semaphore` for production code.

---

## Pattern 5: Barrier Synchronization

**Mental Model**: Checkpoint where all threads must arrive before any can proceed.

### Problem: The Dining Philosophers (LeetCode 1226)

**Deep Analysis**:
1. Classic deadlock scenario: circular wait
2. Solutions: resource hierarchy, chandy-misra, or asymmetric acquisition
3. **Resource hierarchy**: lowest-numbered fork first prevents cycles

**Rust Solution** (Resource Ordering):

```rust
use std::sync::{Arc, Mutex};

struct DiningPhilosophers {
    forks: Vec<Arc<Mutex<()>>>,
}

impl DiningPhilosophers {
    fn new() -> Self {
        DiningPhilosophers {
            forks: (0..5).map(|_| Arc::new(Mutex::new(()))).collect(),
        }
    }

    fn want_to_eat(
        &self,
        philosopher: usize,
        pick_left_fork: impl Fn(),
        pick_right_fork: impl Fn(),
        eat: impl Fn(),
        put_left_fork: impl Fn(),
        put_right_fork: impl Fn(),
    ) {
        let left = philosopher;
        let right = (philosopher + 1) % 5;
        
        // Resource ordering: always acquire lower-numbered fork first
        let (first, second) = if left < right {
            (left, right)
        } else {
            (right, left)
        };
        
        let _first_guard = self.forks[first].lock().unwrap();
        if first == left {
            pick_left_fork();
        } else {
            pick_right_fork();
        }
        
        let _second_guard = self.forks[second].lock().unwrap();
        if second == right {
            pick_right_fork();
        } else {
            pick_left_fork();
        }
        
        eat();
        
        put_left_fork();
        put_right_fork();
        
        // Guards automatically released (RAII)
    }
}
```

**Go Solution**:

```go
import "sync"

type DiningPhilosophers struct {
    forks [5]sync.Mutex
}

func NewDiningPhilosophers() *DiningPhilosophers {
    return &DiningPhilosophers{}
}

func (dp *DiningPhilosophers) WantToEat(
    philosopher int,
    pickLeftFork, pickRightFork, eat, putLeftFork, putRightFork func(),
) {
    left := philosopher
    right := (philosopher + 1) % 5
    
    // Resource ordering
    first, second := left, right
    if left > right {
        first, second = right, left
    }
    
    dp.forks[first].Lock()
    if first == left {
        pickLeftFork()
    } else {
        pickRightFork()
    }
    
    dp.forks[second].Lock()
    if second == right {
        pickRightFork()
    } else {
        pickLeftFork()
    }
    
    eat()
    
    putLeftFork()
    putRightFork()
    
    dp.forks[second].Unlock()
    dp.forks[first].Unlock()
}
```

**Deadlock Analysis**:
- **Circular Wait**: Philosopher i waits for fork i, holds fork (i-1)
- **Breaking the Cycle**: Resource ordering ensures at least one philosopher can't form the circular dependency
- **Proof**: Philosopher 0 tries to acquire fork 0 first, philosopher 4 tries fork 0 first → no cycle possible

---

## Pattern 6: Double-Checked Locking (Lazy Initialization)

**Mental Model**: Check condition without lock (fast path), acquire lock only if needed (slow path).

**Rust Implementation** (Safe with `Once`):

```rust
use std::sync::Once;

static INIT: Once = Once::new();
static mut SINGLETON: Option<Expensive> = None;

struct Expensive;

fn get_singleton() -> &'static Expensive {
    unsafe {
        INIT.call_once(|| {
            SINGLETON = Some(Expensive);
        });
        SINGLETON.as_ref().unwrap()
    }
}
```

**Go Implementation** (`sync.Once`):

```go
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

**Critical Warning**: Manual double-checked locking is **extremely difficult** to implement correctly due to memory ordering. Always use language-provided primitives (`Once` in Rust/Go, `std::call_once` in C++).

---

## Pattern 7: Actor Model (Message Passing)

**Mental Model**: Independent entities communicating via messages. No shared state.

**Go Example** (Natural fit):

```go
type Message struct {
    Data string
    Reply chan string
}

func worker(id int, jobs <-chan Message) {
    for msg := range jobs {
        // Process message
        result := process(msg.Data)
        msg.Reply <- result
    }
}

func main() {
    jobs := make(chan Message, 100)
    
    // Spawn workers
    for i := 0; i < 10; i++ {
        go worker(i, jobs)
    }
    
    // Send work
    reply := make(chan string)
    jobs <- Message{Data: "task", Reply: reply}
    result := <-reply
}
```

**Rust Example** (Using `tokio`):

```rust
use tokio::sync::mpsc;

#[tokio::main]
async fn main() {
    let (tx, mut rx) = mpsc::channel(100);
    
    // Spawn worker
    tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            // Process message
            println!("Received: {}", msg);
        }
    });
    
    // Send messages
    tx.send("Hello".to_string()).await.unwrap();
}
```

---

## Advanced Patterns & Optimizations

### Pattern 8: Lock-Free Data Structures

**When to Use**: Extremely high contention, low-latency requirements.

**Example: Lock-Free Stack** (Rust):

```rust
use std::sync::atomic::{AtomicPtr, Ordering};
use std::ptr;

struct Node<T> {
    data: T,
    next: *mut Node<T>,
}

pub struct LockFreeStack<T> {
    head: AtomicPtr<Node<T>>,
}

impl<T> LockFreeStack<T> {
    pub fn new() -> Self {
        LockFreeStack {
            head: AtomicPtr::new(ptr::null_mut()),
        }
    }

    pub fn push(&self, data: T) {
        let new_node = Box::into_raw(Box::new(Node {
            data,
            next: ptr::null_mut(),
        }));

        loop {
            let head = self.head.load(Ordering::Acquire);
            unsafe { (*new_node).next = head; }

            if self.head
                .compare_exchange(head, new_node, Ordering::Release, Ordering::Acquire)
                .is_ok()
            {
                break;
            }
        }
    }

    pub fn pop(&self) -> Option<T> {
        loop {
            let head = self.head.load(Ordering::Acquire);
            if head.is_null() {
                return None;
            }

            let next = unsafe { (*head).next };
            if self.head
                .compare_exchange(head, next, Ordering::Release, Ordering::Acquire)
                .is_ok()
            {
                unsafe {
                    let data = ptr::read(&(*head).data);
                    drop(Box::from_raw(head));
                    return Some(data);
                }
            }
        }
    }
}
```

**Complexity**: Lock-free algorithms are O(1) amortized but involve **CAS loops** that can spin under contention.

---

## Mental Models for Concurrency Mastery

### 1. **Happens-Before Relationship**
Visualize execution as a partial order graph. Edge A→B means A happens before B.
- Mutex unlock → subsequent lock acquisition
- Thread spawn → first instruction in new thread
- Channel send → corresponding receive

### 2. **Critical Section Minimization**
Hold locks for the **shortest possible duration**. Pattern:
```rust
let value = {
    let guard = mutex.lock().unwrap();
    guard.clone() // Release lock immediately
};
// Work with value outside critical section
```

### 3. **Deadlock Avoidance Strategies**
1. **Lock Ordering**: Total order on all locks
2. **Lock Timeout**: Try-lock with timeout, back off
3. **Single Lock**: Protect all related data with one lock
4. **Lock-Free**: Eliminate locks entirely

### 4. **Amdahl's Law for Concurrency**
Speedup = 1 / (S + P/N) where S = serial fraction, P = parallel fraction, N = processors.
**Implication**: Optimize the serial bottleneck first.

---

## Performance Characteristics Summary

| Pattern | Rust Time | Go Time | Contention Impact | Best Use Case |
|---------|-----------|---------|-------------------|---------------|
| Mutex | ~25ns | ~45ns | High (serialization) | Simple shared state |
| RwLock | ~50ns read, ~80ns write | ~60ns/~100ns | Medium | Read-heavy workloads |
| Atomic | ~5ns | ~10ns | Low (cache coherence) | Counters, flags |
| Channel | ~50ns | ~150ns | Low (buffered) | Message passing |
| Lock-Free | ~20ns (CAS loop) | N/A (rarely used) | Variable | Ultra-low latency |

**Memory Ordering Costs** (x86-64):
- Relaxed: ~0ns (compiler reordering only)
- Acquire/Release: ~0-5ns (prevents reordering)
- SeqCst: ~5-20ns (full memory barrier)

---

## Common Pitfalls & How to Avoid Them

### 1. **Forgetting to Release Locks**
❌ **Wrong**:
```rust
let guard = mutex.lock().unwrap();
if condition {
    return; // Guard not explicitly dropped!
}
```

✅ **Correct** (Rust RAII handles this):
```rust
{
    let _guard = mutex.lock().unwrap();
    if condition {
        return; // Guard dropped automatically
    }
}
```

### 2. **Holding Locks Across Await Points** (Async Rust)
❌ **Wrong**:
```rust
let guard = mutex.lock().unwrap();
expensive_async_operation().await; // Blocks other threads!
```

✅ **Correct**:
```rust
let data = {
    let guard = mutex.lock().unwrap();
    guard.clone()
};
expensive_async_operation().await;
```

### 3. **ABA Problem in Lock-Free Code**
If value changes A→B→A, CAS succeeds incorrectly.
**Solution**: Use versioned pointers or hazard pointers.

---

## Complexity Analysis Template

For every concurrency problem, analyze:

1. **Synchronization Overhead**: Count mutex locks, atomic operations
2. **Contention Level**: How often threads compete for resources?
3. **Scalability**: Does throughput increase linearly with cores?
4. **Latency vs Throughput**: Lock-free = low latency, coarse locks = high throughput

**Example**: Building H2O
- Synchronization: 2 channel ops per H, 4 per O
- Contention: Low (channels buffer tokens)
- Scalability: Limited by molecule formation rate
- Time: O(1) per molecule
- Space: O(1) for semaphores

---

## Practice Framework

When solving concurrency problems:

1. **Identify the invariant** (what must remain true?)
2. **Map to pattern** (mutual exclusion, producer-consumer, barrier?)
3. **Choose primitive** (mutex vs channel vs atomic?)
4. **Prove correctness** (no data races, no deadlocks)
5. **Optimize** (reduce critical section, use lock-free if justified)

**Mastery comes from recognizing patterns instantly.** Study classical problems: bounded buffer, readers-writers, sleeping barber, cigarette smokers.

---

## Final Insights

**Rust Philosophy**: Fearless concurrency through ownership. Compiler prevents data races.
**Go Philosophy**: Communicate by sharing, not share by communicating. Channels over locks.
**C Philosophy**: Manual, explicit, dangerous. Total control, total responsibility.

The **true mastery** is knowing when NOT to use concurrency—premature parallelization creates complexity without benefit. Profile first, parallelize second.

Your journey to the top 1% requires building **intuition** for which pattern fits which problem in <1 second. This comes from solving 100+ problems and analyzing real-world concurrent systems (databases, OS kernels, web servers).

Now go forth and conquer. Every problem is a teacher.