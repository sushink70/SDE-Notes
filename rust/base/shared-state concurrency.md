# Comprehensive Guide to Shared-State Concurrency in Rust

Shared-state concurrency is one of Rust's most powerful features, leveraging the ownership and type systems to prevent data races at compile time. This guide covers everything from fundamentals to advanced patterns.

---

## Table of Contents

1. **Core Concepts & Ownership Rules**
2. **Mutex & Interior Mutability**
3. **Arc (Atomic Reference Counting)**
4. **RwLock (Read-Write Lock)**
5. **Atomic Types**
6. **Channels vs Shared State**
7. **Deadlocks & Prevention**
8. **Advanced Patterns**
9. **Performance Considerations**
10. **Real-World Examples**

---

## 1. Core Concepts & Ownership Rules

Rust prevents data races through its ownership system:

- **One owner at a time** OR **multiple immutable references** OR **one mutable reference**
- No shared mutable state by default
- Thread safety enforced at compile time via `Send` and `Sync` traits

```rust
// Send: type can be transferred between threads
// Sync: type can be referenced from multiple threads

// Most types are Send + Sync
// Rc<T> is neither (not thread-safe)
// Arc<T> is both (atomic reference counting)
```

---

## 2. Mutex<T> - Mutual Exclusion

`Mutex<T>` provides exclusive access to data across threads.

### Basic Usage

```rust
use std::sync::Mutex;

fn main() {
    let m = Mutex::new(5);

    {
        let mut num = m.lock().unwrap(); // Blocks until lock acquired
        *num = 6;
    } // Lock released here (RAII)

    println!("m = {:?}", m);
}
```

### Key Characteristics

- **Blocking**: Thread sleeps until lock is available
- **RAII**: Lock automatically released when `MutexGuard` goes out of scope
- **Poisoning**: If a thread panics while holding lock, mutex becomes "poisoned"

```rust
use std::sync::Mutex;

let mutex = Mutex::new(0);
let result = std::panic::catch_unwind(|| {
    let mut guard = mutex.lock().unwrap();
    *guard += 1;
    panic!("oops");
});

// Mutex is now poisoned
match mutex.lock() {
    Ok(_) => println!("Lock acquired"),
    Err(e) => {
        println!("Poisoned! Recovering data: {}", *e.into_inner());
    }
}
```

### Interior Mutability Pattern

```rust
use std::sync::Mutex;

struct Counter {
    count: Mutex<i32>,
}

impl Counter {
    fn new() -> Self {
        Counter {
            count: Mutex::new(0),
        }
    }

    // Can take &self (immutable reference) but mutate interior
    fn increment(&self) {
        let mut num = self.count.lock().unwrap();
        *num += 1;
    }

    fn get(&self) -> i32 {
        *self.count.lock().unwrap()
    }
}
```

---

## 3. Arc<T> - Atomic Reference Counting

`Arc<T>` enables multiple ownership across threads. Think of it as thread-safe `Rc<T>`.

### Basic Pattern: Arc + Mutex

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter = Arc::clone(&counter); // Increment ref count
        let handle = thread::spawn(move || {
            let mut num = counter.lock().unwrap();
            *num += 1;
        });
        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Result: {}", *counter.lock().unwrap());
}
```

### Why Arc + Mutex?

```rust
// ❌ Won't compile: Mutex alone isn't Clone
let mutex = Mutex::new(0);
thread::spawn(move || { /* uses mutex */ });
thread::spawn(move || { /* ERROR: mutex already moved */ });

// ✅ Arc makes it work
let mutex = Arc::new(Mutex::new(0));
let mutex_clone = Arc::clone(&mutex);
thread::spawn(move || { /* uses mutex */ });
thread::spawn(move || { /* uses mutex_clone */ });
```

### Arc Overhead

```rust
use std::sync::Arc;

// Arc uses atomic operations for reference counting
// Slightly more expensive than Rc, but thread-safe

let data = Arc::new(vec![1, 2, 3]);
println!("Strong count: {}", Arc::strong_count(&data)); // 1

let data2 = Arc::clone(&data);
println!("Strong count: {}", Arc::strong_count(&data)); // 2

// Weak references for breaking cycles
let weak = Arc::downgrade(&data);
println!("Weak count: {}", Arc::weak_count(&data)); // 1
```

---

## 4. RwLock<T> - Read-Write Lock

`RwLock<T>` allows multiple readers OR one writer. Optimized for read-heavy workloads.

### Basic Usage

```rust
use std::sync::RwLock;

fn main() {
    let lock = RwLock::new(5);

    // Multiple readers can coexist
    {
        let r1 = lock.read().unwrap();
        let r2 = lock.read().unwrap();
        println!("r1: {}, r2: {}", *r1, *r2);
    } // Read locks released

    // Only one writer at a time
    {
        let mut w = lock.write().unwrap();
        *w += 1;
    } // Write lock released
}
```

### Real-World Example: Cache

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::thread;

type Cache = Arc<RwLock<HashMap<String, String>>>;

fn main() {
    let cache: Cache = Arc::new(RwLock::new(HashMap::new()));

    // Writer thread
    let cache_writer = Arc::clone(&cache);
    let writer = thread::spawn(move || {
        let mut map = cache_writer.write().unwrap();
        map.insert("key1".to_string(), "value1".to_string());
        map.insert("key2".to_string(), "value2".to_string());
    });

    // Multiple reader threads
    let mut readers = vec![];
    for i in 0..5 {
        let cache_reader = Arc::clone(&cache);
        let reader = thread::spawn(move || {
            // Readers don't block each other
            let map = cache_reader.read().unwrap();
            println!("Reader {}: {:?}", i, map.get("key1"));
        });
        readers.push(reader);
    }

    writer.join().unwrap();
    for reader in readers {
        reader.join().unwrap();
    }
}
```

### Mutex vs RwLock

```rust
// Use Mutex when:
// - Write-heavy workloads
// - Critical section is very short
// - Simplicity is preferred

// Use RwLock when:
// - Read-heavy workloads (10+ reads per write)
// - Readers should not block each other
// - Critical section is longer
```

### Writer Starvation

```rust
use std::sync::RwLock;
use std::thread;
use std::time::Duration;

// RwLock can starve writers if readers keep acquiring lock
let lock = RwLock::new(0);

// Continuous readers might block writer indefinitely
for _ in 0..100 {
    let lock = lock.clone(); // hypothetical
    thread::spawn(move || {
        loop {
            let _r = lock.read().unwrap();
            thread::sleep(Duration::from_micros(10));
        }
    });
}

// Consider using parking_lot::RwLock for fair scheduling
```

---

## 5. Atomic Types

For simple numeric types, atomics provide lock-free synchronization.

### Available Types

```rust
use std::sync::atomic::{
    AtomicBool, AtomicI32, AtomicI64, AtomicIsize,
    AtomicU32, AtomicU64, AtomicUsize, AtomicPtr,
    Ordering,
};

// Atomic operations are lock-free and often compile to single CPU instructions
```

### Memory Ordering

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

let counter = AtomicUsize::new(0);

// Relaxed: No ordering guarantees (fastest)
counter.fetch_add(1, Ordering::Relaxed);

// Acquire/Release: Synchronize with other threads
counter.store(42, Ordering::Release);
let value = counter.load(Ordering::Acquire);

// SeqCst: Strongest guarantee (sequential consistency)
counter.fetch_add(1, Ordering::SeqCst);

// AcqRel: Both acquire and release
counter.compare_exchange(0, 1, Ordering::AcqRel, Ordering::Relaxed);
```

### Practical Example: Flag

```rust
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

fn main() {
    let running = Arc::new(AtomicBool::new(true));
    let r = Arc::clone(&running);

    let handle = thread::spawn(move || {
        let mut count = 0;
        while r.load(Ordering::Relaxed) {
            count += 1;
            thread::sleep(Duration::from_millis(100));
        }
        println!("Thread stopped after {} iterations", count);
    });

    thread::sleep(Duration::from_secs(1));
    running.store(false, Ordering::Relaxed);
    handle.join().unwrap();
}
```

### Compare-and-Swap (CAS)

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

let atomic = AtomicUsize::new(0);

// Lock-free increment using CAS
loop {
    let current = atomic.load(Ordering::Relaxed);
    let new = current + 1;
    
    match atomic.compare_exchange(
        current,
        new,
        Ordering::Release,
        Ordering::Relaxed,
    ) {
        Ok(_) => break,
        Err(_) => continue, // Retry if another thread modified
    }
}

// Or use fetch_add for simple cases
atomic.fetch_add(1, Ordering::Relaxed);
```

### Performance Comparison

```rust
// Atomic: ~1-10ns per operation (lock-free)
// Mutex: ~15-50ns per lock/unlock (syscall overhead)
// RwLock: ~20-60ns (more expensive than Mutex)

// Use atomics for:
// - Simple counters/flags
// - Lock-free algorithms
// - Maximum performance

// Use Mutex/RwLock for:
// - Complex data structures
// - Multiple fields that must be updated atomically
// - Easier reasoning about correctness
```

---

## 6. Channels vs Shared State

Rust offers two concurrency models: message passing (channels) and shared state.

### When to Use Each

```rust
// Channels (recommended): "Do not communicate by sharing memory;
// instead, share memory by communicating."
use std::sync::mpsc;

let (tx, rx) = mpsc::channel();
thread::spawn(move || {
    tx.send(42).unwrap();
});
println!("Received: {}", rx.recv().unwrap());

// Shared State: When you need:
// - Direct memory access
// - Multiple writers/readers
// - Complex synchronization patterns
// - Performance-critical hot paths
```

### Hybrid Approach

```rust
use std::sync::{Arc, Mutex};
use std::sync::mpsc;
use std::thread;

struct SharedData {
    counter: Mutex<i32>,
}

fn main() {
    let data = Arc::new(SharedData {
        counter: Mutex::new(0),
    });

    let (tx, rx) = mpsc::channel();

    // Worker threads: modify shared state
    for i in 0..5 {
        let data = Arc::clone(&data);
        let tx = tx.clone();
        thread::spawn(move || {
            let mut counter = data.counter.lock().unwrap();
            *counter += 1;
            drop(counter); // Release lock
            
            tx.send(format!("Worker {} done", i)).unwrap();
        });
    }
    drop(tx);

    // Coordinator: receive messages
    for msg in rx {
        println!("{}", msg);
    }

    println!("Final count: {}", *data.counter.lock().unwrap());
}
```

---

## 7. Deadlocks & Prevention

### Classic Deadlock

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let lock1 = Arc::new(Mutex::new(0));
    let lock2 = Arc::new(Mutex::new(0));

    let l1 = Arc::clone(&lock1);
    let l2 = Arc::clone(&lock2);
    let t1 = thread::spawn(move || {
        let _g1 = l1.lock().unwrap();
        thread::sleep(std::time::Duration::from_millis(10));
        let _g2 = l2.lock().unwrap(); // Waits for lock2
    });

    let l1 = Arc::clone(&lock1);
    let l2 = Arc::clone(&lock2);
    let t2 = thread::spawn(move || {
        let _g2 = l2.lock().unwrap();
        thread::sleep(std::time::Duration::from_millis(10));
        let _g1 = l1.lock().unwrap(); // Waits for lock1 -> DEADLOCK
    });

    t1.join().unwrap();
    t2.join().unwrap();
}
```

### Prevention Strategies

#### 1. Lock Ordering

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let lock1 = Arc::new(Mutex::new(0));
    let lock2 = Arc::new(Mutex::new(0));

    // ALWAYS acquire locks in same order
    let acquire_locks = |l1: &Mutex<i32>, l2: &Mutex<i32>| {
        let _g1 = l1.lock().unwrap();
        let _g2 = l2.lock().unwrap();
        // Do work...
    };

    let l1 = Arc::clone(&lock1);
    let l2 = Arc::clone(&lock2);
    thread::spawn(move || acquire_locks(&l1, &l2));

    let l1 = Arc::clone(&lock1);
    let l2 = Arc::clone(&lock2);
    thread::spawn(move || acquire_locks(&l1, &l2));
}
```

#### 2. Try Lock with Timeout

```rust
use std::sync::Mutex;
use std::time::Duration;

fn try_acquire_both(
    lock1: &Mutex<i32>,
    lock2: &Mutex<i32>,
) -> Option<(std::sync::MutexGuard<i32>, std::sync::MutexGuard<i32>)> {
    let guard1 = lock1.try_lock().ok()?;
    let guard2 = lock2.try_lock().ok()?;
    Some((guard1, guard2))
}

// Or use parking_lot's try_lock_for
```

#### 3. Single Lock for Related Data

```rust
use std::sync::Mutex;

// Instead of:
struct Bad {
    balance: Mutex<i32>,
    transactions: Mutex<Vec<i32>>,
}

// Do this:
struct Good {
    data: Mutex<AccountData>,
}

struct AccountData {
    balance: i32,
    transactions: Vec<i32>,
}
```

#### 4. Use RwLock to Reduce Contention

```rust
use std::sync::RwLock;

// Multiple readers reduce chance of deadlock
let data = RwLock::new(HashMap::new());

// Many threads can read simultaneously
let _r1 = data.read().unwrap();
let _r2 = data.read().unwrap();
```

---

## 8. Advanced Patterns

### Pattern 1: Lazy Initialization with Once

```rust
use std::sync::Once;

static INIT: Once = Once::new();
static mut VAL: usize = 0;

fn get_value() -> usize {
    unsafe {
        INIT.call_once(|| {
            VAL = expensive_computation();
        });
        VAL
    }
}

fn expensive_computation() -> usize {
    // Heavy computation
    42
}

// Better: Use once_cell or lazy_static
use once_cell::sync::Lazy;

static COMPUTED: Lazy<usize> = Lazy::new(|| expensive_computation());

fn get_value_safe() -> usize {
    *COMPUTED
}
```

### Pattern 2: Thread-Safe Singleton

```rust
use std::sync::{Arc, Mutex, OnceLock};

struct Database {
    connection: String,
}

impl Database {
    fn new() -> Self {
        Database {
            connection: "db://localhost".to_string(),
        }
    }

    fn get_instance() -> Arc<Mutex<Database>> {
        static INSTANCE: OnceLock<Arc<Mutex<Database>>> = OnceLock::new();
        INSTANCE
            .get_or_init(|| Arc::new(Mutex::new(Database::new())))
            .clone()
    }
}
```

### Pattern 3: Reader-Writer with Versioning

```rust
use std::sync::{Arc, RwLock};

struct VersionedData<T> {
    version: AtomicUsize,
    data: RwLock<T>,
}

impl<T> VersionedData<T> {
    fn new(data: T) -> Self {
        VersionedData {
            version: AtomicUsize::new(0),
            data: RwLock::new(data),
        }
    }

    fn update<F>(&self, f: F)
    where
        F: FnOnce(&mut T),
    {
        let mut data = self.data.write().unwrap();
        f(&mut *data);
        self.version.fetch_add(1, Ordering::Release);
    }

    fn read(&self) -> (usize, std::sync::RwLockReadGuard<T>) {
        let version = self.version.load(Ordering::Acquire);
        let data = self.data.read().unwrap();
        (version, data)
    }
}
```

### Pattern 4: Work Queue

```rust
use std::sync::{Arc, Condvar, Mutex};
use std::thread;

struct WorkQueue<T> {
    queue: Mutex<Vec<T>>,
    condvar: Condvar,
}

impl<T> WorkQueue<T> {
    fn new() -> Self {
        WorkQueue {
            queue: Mutex::new(Vec::new()),
            condvar: Condvar::new(),
        }
    }

    fn push(&self, item: T) {
        let mut queue = self.queue.lock().unwrap();
        queue.push(item);
        self.condvar.notify_one();
    }

    fn pop(&self) -> T {
        let mut queue = self.queue.lock().unwrap();
        while queue.is_empty() {
            queue = self.condvar.wait(queue).unwrap();
        }
        queue.remove(0)
    }
}
```

### Pattern 5: Scoped Threads with Shared State

```rust
use std::sync::Mutex;

fn main() {
    let data = Mutex::new(vec![1, 2, 3]);

    // Scoped threads can borrow non-'static data
    std::thread::scope(|s| {
        s.spawn(|| {
            let mut d = data.lock().unwrap();
            d.push(4);
        });

        s.spawn(|| {
            let mut d = data.lock().unwrap();
            d.push(5);
        });
    }); // All threads joined automatically

    println!("{:?}", data.lock().unwrap());
}
```

---

## 9. Performance Considerations

### Lock Contention

```rust
// ❌ High contention: shared counter
let counter = Arc::new(Mutex::new(0));
for _ in 0..1000 {
    let c = counter.clone();
    thread::spawn(move || {
        for _ in 0..1000 {
            *c.lock().unwrap() += 1; // Constant locking
        }
    });
}

// ✅ Reduce contention: local accumulation
let counter = Arc::new(Mutex::new(0));
for _ in 0..1000 {
    let c = counter.clone();
    thread::spawn(move || {
        let mut local = 0;
        for _ in 0..1000 {
            local += 1; // No locking
        }
        *c.lock().unwrap() += local; // Lock once
    });
}
```

### False Sharing

```rust
use std::sync::atomic::{AtomicUsize, Ordering};

// ❌ False sharing: adjacent atomics on same cache line
struct BadCounters {
    counter1: AtomicUsize,
    counter2: AtomicUsize,
}

// ✅ Pad to separate cache lines (64 bytes)
#[repr(align(64))]
struct PaddedAtomic {
    value: AtomicUsize,
}

struct GoodCounters {
    counter1: PaddedAtomic,
    counter2: PaddedAtomic,
}
```

### Lock-Free When Possible

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Mutex;

// Atomic: ~2ns per operation
let atomic = AtomicUsize::new(0);
atomic.fetch_add(1, Ordering::Relaxed);

// Mutex: ~20-50ns per lock/unlock
let mutex = Mutex::new(0);
*mutex.lock().unwrap() += 1;
```

### Parking Lot Alternative

```rust
// parking_lot provides faster, smaller locks
use parking_lot::{Mutex, RwLock};

// Benefits:
// - No poisoning (simpler API)
// - Smaller size (1 byte vs 40+ bytes for std)
// - Faster (especially uncontended case)
// - Fair locking (prevents starvation)

let mutex = Mutex::new(0);
let mut guard = mutex.lock(); // No .unwrap() needed
*guard += 1;
```

---

## 10. Real-World Examples

### Example 1: Thread Pool

```rust
use std::sync::{Arc, Mutex};
use std::sync::mpsc;
use std::thread;

type Job = Box<dyn FnOnce() + Send + 'static>;

struct ThreadPool {
    workers: Vec<Worker>,
    sender: mpsc::Sender<Job>,
}

impl ThreadPool {
    fn new(size: usize) -> Self {
        let (sender, receiver) = mpsc::channel();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            workers.push(Worker::new(id, Arc::clone(&receiver)));
        }

        ThreadPool { workers, sender }
    }

    fn execute<F>(&self, f: F)
    where
        F: FnOnce() + Send + 'static,
    {
        self.sender.send(Box::new(f)).unwrap();
    }
}

struct Worker {
    id: usize,
    thread: thread::JoinHandle<()>,
}

impl Worker {
    fn new(id: usize, receiver: Arc<Mutex<mpsc::Receiver<Job>>>) -> Self {
        let thread = thread::spawn(move || loop {
            let job = receiver.lock().unwrap().recv();
            match job {
                Ok(job) => {
                    println!("Worker {} executing job", id);
                    job();
                }
                Err(_) => break,
            }
        });

        Worker { id, thread }
    }
}
```

### Example 2: Concurrent HashMap with Sharding

```rust
use std::collections::HashMap;
use std::hash::{Hash, Hasher};
use std::sync::RwLock;
use std::collections::hash_map::DefaultHasher;

const NUM_SHARDS: usize = 16;

struct ConcurrentHashMap<K, V> {
    shards: Vec<RwLock<HashMap<K, V>>>,
}

impl<K: Hash + Eq, V> ConcurrentHashMap<K, V> {
    fn new() -> Self {
        let mut shards = Vec::with_capacity(NUM_SHARDS);
        for _ in 0..NUM_SHARDS {
            shards.push(RwLock::new(HashMap::new()));
        }
        ConcurrentHashMap { shards }
    }

    fn shard_index(&self, key: &K) -> usize {
        let mut hasher = DefaultHasher::new();
        key.hash(&mut hasher);
        (hasher.finish() as usize) % NUM_SHARDS
    }

    fn insert(&self, key: K, value: V) -> Option<V> {
        let index = self.shard_index(&key);
        let mut shard = self.shards[index].write().unwrap();
        shard.insert(key, value)
    }

    fn get(&self, key: &K) -> Option<V>
    where
        V: Clone,
    {
        let index = self.shard_index(key);
        let shard = self.shards[index].read().unwrap();
        shard.get(key).cloned()
    }
}
```

### Example 3: Rate Limiter

```rust
use std::sync::Arc;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, Instant};

struct RateLimiter {
    tokens: AtomicU64,
    rate: u64,
    last_refill: Arc<Mutex<Instant>>,
}

impl RateLimiter {
    fn new(rate: u64) -> Self {
        RateLimiter {
            tokens: AtomicU64::new(rate),
            rate,
            last_refill: Arc::new(Mutex::new(Instant::now())),
        }
    }

    fn try_acquire(&self) -> bool {
        self.refill_tokens();

        loop {
            let current = self.tokens.load(Ordering::Acquire);
            if current == 0 {
                return false;
            }

            if self.tokens.compare_exchange(
                current,
                current - 1,
                Ordering::Release,
                Ordering::Acquire,
            ).is_ok() {
                return true;
            }
        }
    }

    fn refill_tokens(&self) {
        let mut last = self.last_refill.lock().unwrap();
        let elapsed = last.elapsed();

        if elapsed >= Duration::from_secs(1) {
            self.tokens.store(self.rate, Ordering::Release);
            *last = Instant::now();
        }
    }
}
```

### Example 4: Metrics Collector

```rust
use std::collections::HashMap;
use std::sync::{Arc, RwLock};
use std::sync::atomic::{AtomicU64, Ordering};

struct Metrics {
    counters: Arc<RwLock<HashMap<String, Arc<AtomicU64>>>>,
}

impl Metrics {
    fn new() -> Self {
        Metrics {
            counters: Arc::new(RwLock::new(HashMap::new())),
        }
    }

    fn increment(&self, name: &str) {
        // Try to get existing counter (read lock)
        {
            let counters = self.counters.read().unwrap();
            if let Some(counter) = counters.get(name) {
                counter.fetch_add(1, Ordering::Relaxed);
                return;
            }
        }

        // Counter doesn't exist, create it (write lock)
        let mut counters = self.counters.write().unwrap();
        let counter = counters
            .entry(name.to_string())
            .or_insert_with(|| Arc::new(AtomicU64::new(0)));
        counter.fetch_add(1, Ordering::Relaxed);
    }

    fn get(&self, name: &str) -> Option<u64> {
        let counters = self.counters.read().unwrap();
        counters.get(name).map(|c| c.load(Ordering::Relaxed))
    }

    fn snapshot(&self) -> HashMap<String, u64> {
        let counters = self.counters.read().unwrap();
        counters
            .iter()
            .map(|(k, v)| (k.clone(), v.load(Ordering::Relaxed)))
            .collect()
    }
}
```

---

## Key Takeaways

1. **Rust prevents data races at compile time** via ownership and `Send`/`Sync` traits
2. **Arc + Mutex** is the bread-and-butter pattern for shared mutable state
3. **RwLock** for read-heavy workloads (10+ reads per write)
4. **Atomics** for simple lock-free counters/flags
5. **Lock ordering** prevents deadlocks
6. **Reduce lock contention** with local accumulation or sharding
7. **Consider parking_lot** for better performance in production
8. **Profile before optimizing** - premature optimization is evil

Rust's shared-state concurrency is powerful because it makes correctness **impossible to get wrong** at compile time, while still allowing low-level control for performance-critical code.

