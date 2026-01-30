# Extensible Concurrency with `Send` and `Sync` in Rust

## Introduction

Rust's concurrency model is built on **fearless concurrency** — the ability to write concurrent code without data races at compile time. At the heart of this system are two marker traits: `Send` and `Sync`. These traits enable Rust's type system to enforce thread safety guarantees automatically.

This guide covers everything from fundamentals to advanced patterns.

---

## Core Concepts

### What are `Send` and `Sync`?

```rust
// Marker traits - they have no methods
pub unsafe auto trait Send {}
pub unsafe auto trait Sync {}
```

**`Send`**: A type is `Send` if it can be **transferred** across thread boundaries.
- "I can move this value to another thread safely"
- Ownership transfer between threads

**`Sync`**: A type is `Sync` if it can be **shared** across thread boundaries (via references).
- "Multiple threads can access `&T` simultaneously"
- `T: Sync` means `&T: Send`

### Key Rule
```rust
// If T is Sync, then &T is Send
// This means shared references can be sent to other threads
```

---

## Auto-Implementation

Most types automatically implement `Send` and `Sync`:

```rust
struct Point {
    x: i32,
    y: i32,
}
// Automatically Send + Sync because i32 is Send + Sync

struct Container<T> {
    value: T,
}
// Container<T> is Send if T: Send
// Container<T> is Sync if T: Sync
```

### Types that are NOT `Send` or `Sync`

```rust
use std::rc::Rc;
use std::cell::RefCell;

// Rc<T> is neither Send nor Sync
// (reference counting not atomic)
let rc = Rc::new(5);

// RefCell<T> is Send (if T: Send) but NOT Sync
// (interior mutability without synchronization)
let cell = RefCell::new(5);

// Raw pointers are neither Send nor Sync by default
let ptr: *const i32 = &5;
```

---

## Practical Examples

### Example 1: Thread Boundaries

```rust
use std::thread;

fn main() {
    let data = vec![1, 2, 3];
    
    // This works - Vec<i32> is Send
    thread::spawn(move || {
        println!("{:?}", data);
    });
    
    // This won't compile - Rc is not Send
    use std::rc::Rc;
    let rc_data = Rc::new(vec![1, 2, 3]);
    
    // ERROR: `Rc<Vec<i32>>` cannot be sent between threads safely
    // thread::spawn(move || {
    //     println!("{:?}", rc_data);
    // });
}
```

### Example 2: Shared State with Arc

```rust
use std::sync::Arc;
use std::thread;

fn main() {
    // Arc is Send + Sync when T: Send + Sync
    let data = Arc::new(vec![1, 2, 3]);
    let mut handles = vec![];
    
    for i in 0..3 {
        let data_clone = Arc::clone(&data);
        let handle = thread::spawn(move || {
            println!("Thread {}: {:?}", i, data_clone);
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

### Example 3: Mutable Shared State

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
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

---

## Advanced Patterns

### Pattern 1: Implementing Send/Sync Manually

```rust
use std::marker::PhantomData;

// A type that contains a raw pointer
struct MyBox<T> {
    ptr: *mut T,
    _marker: PhantomData<T>,
}

// Manually implement Send/Sync
// SAFETY: We ensure exclusive access through our API
unsafe impl<T: Send> Send for MyBox<T> {}
unsafe impl<T: Sync> Sync for MyBox<T> {}

impl<T> MyBox<T> {
    fn new(value: T) -> Self {
        Self {
            ptr: Box::into_raw(Box::new(value)),
            _marker: PhantomData,
        }
    }
    
    fn get(&self) -> &T {
        unsafe { &*self.ptr }
    }
}

impl<T> Drop for MyBox<T> {
    fn drop(&mut self) {
        unsafe {
            drop(Box::from_raw(self.ptr));
        }
    }
}
```

### Pattern 2: Negative Implementations (Opt-out)

```rust
// Explicitly mark a type as NOT Send/Sync
struct NotThreadSafe {
    data: i32,
    _marker: PhantomData<*const ()>, // *const () is !Send + !Sync
}

// Alternative: use negative impl (nightly only)
// #![feature(negative_impls)]
// impl !Send for NotThreadSafe {}
// impl !Sync for NotThreadSafe {}
```

### Pattern 3: Conditional Send/Sync

```rust
use std::sync::Arc;

// This type is only Send if T is Send
struct Wrapper<T> {
    inner: Arc<T>,
}

// Compiler automatically derives:
// impl<T: Send> Send for Wrapper<T> {}
// impl<T: Sync> Sync for Wrapper<T> {}

// You can override if needed:
struct CustomWrapper<T> {
    inner: T,
}

// Only Send when T is both Send and Sync
unsafe impl<T: Send + Sync> Send for CustomWrapper<T> {}
// Never Sync
// (no Sync implementation)
```

---

## Common Concurrency Patterns

### Pattern 4: Message Passing (MPSC)

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn main() {
    let (tx, rx) = mpsc::channel();
    
    // Spawn producer threads
    for i in 0..3 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(format!("Message from thread {}", i)).unwrap();
        });
    }
    drop(tx); // Close the channel
    
    // Consumer
    for received in rx {
        println!("Got: {}", received);
    }
}
```

### Pattern 5: Scoped Threads (No Lifetime Issues)

```rust
use std::thread;

fn main() {
    let mut data = vec![1, 2, 3];
    
    thread::scope(|s| {
        // Can borrow `data` without move
        s.spawn(|| {
            println!("Read: {:?}", data);
        });
        
        s.spawn(|| {
            data.push(4);
        });
    }); // All threads guaranteed to complete here
    
    println!("Final: {:?}", data);
}
```

### Pattern 6: RwLock for Read-Heavy Workloads

```rust
use std::sync::{Arc, RwLock};
use std::thread;

fn main() {
    let data = Arc::new(RwLock::new(vec![1, 2, 3]));
    let mut handles = vec![];
    
    // Multiple readers
    for i in 0..5 {
        let data = Arc::clone(&data);
        handles.push(thread::spawn(move || {
            let read_guard = data.read().unwrap();
            println!("Reader {}: {:?}", i, *read_guard);
        }));
    }
    
    // One writer
    let data = Arc::clone(&data);
    handles.push(thread::spawn(move || {
        let mut write_guard = data.write().unwrap();
        write_guard.push(4);
        println!("Writer: pushed 4");
    }));
    
    for handle in handles {
        handle.join().unwrap();
    }
}
```

---

## Lock-Free Patterns with Atomics

### Pattern 7: Atomic Operations

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

fn main() {
    let counter = Arc::new(AtomicUsize::new(0));
    let mut handles = vec![];
    
    for _ in 0..10 {
        let counter = Arc::clone(&counter);
        let handle = thread::spawn(move || {
            for _ in 0..1000 {
                counter.fetch_add(1, Ordering::SeqCst);
            }
        });
        handles.push(handle);
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Counter: {}", counter.load(Ordering::SeqCst));
}
```

### Memory Ordering Explained

```rust
use std::sync::atomic::{AtomicBool, Ordering};

static FLAG: AtomicBool = AtomicBool::new(false);
static mut VALUE: i32 = 0;

// Relaxed: No ordering guarantees, fastest
fn relaxed_example() {
    FLAG.store(true, Ordering::Relaxed);
}

// Acquire/Release: Synchronization between threads
fn acquire_release_example() {
    // Thread 1: Release
    unsafe { VALUE = 42; }
    FLAG.store(true, Ordering::Release); // All writes before are visible
    
    // Thread 2: Acquire
    if FLAG.load(Ordering::Acquire) { // Synchronizes with Release
        unsafe { println!("{}", VALUE); } // Guaranteed to see 42
    }
}

// SeqCst: Strongest guarantee, total ordering
fn seqcst_example() {
    FLAG.store(true, Ordering::SeqCst);
}
```

---

## Advanced Type System Interactions

### Pattern 8: PhantomData for Variance

```rust
use std::marker::PhantomData;

// Invariant over T (can't substitute T with subtype/supertype)
struct Invariant<T> {
    ptr: *mut T,
    _marker: PhantomData<T>,
}

// Covariant over T (can substitute T with subtype)
struct Covariant<T> {
    ptr: *const T,
    _marker: PhantomData<T>,
}

// Contravariant over T (can substitute T with supertype)
struct Contravariant<T> {
    _marker: PhantomData<fn(T)>,
}
```

### Pattern 9: Higher-Kinded Thread Safety

```rust
use std::sync::Mutex;

// Thread-safe wrapper for any type
struct ThreadSafe<T> {
    inner: Mutex<T>,
}

impl<T> ThreadSafe<T> {
    fn new(value: T) -> Self {
        Self {
            inner: Mutex::new(value),
        }
    }
    
    fn with<F, R>(&self, f: F) -> R
    where
        F: FnOnce(&mut T) -> R,
    {
        let mut guard = self.inner.lock().unwrap();
        f(&mut *guard)
    }
}

// Automatically Send + Sync if T: Send
unsafe impl<T: Send> Send for ThreadSafe<T> {}
unsafe impl<T: Send> Sync for ThreadSafe<T> {}
```

---

## Real-World Architectures

### Pattern 10: Actor Model

```rust
use std::sync::mpsc::{self, Sender, Receiver};
use std::thread;

enum ActorMessage {
    Increment,
    Get(Sender<i32>),
    Stop,
}

struct Actor {
    receiver: Receiver<ActorMessage>,
    counter: i32,
}

impl Actor {
    fn new(receiver: Receiver<ActorMessage>) -> Self {
        Self { receiver, counter: 0 }
    }
    
    fn run(mut self) {
        loop {
            match self.receiver.recv() {
                Ok(ActorMessage::Increment) => {
                    self.counter += 1;
                }
                Ok(ActorMessage::Get(reply)) => {
                    reply.send(self.counter).ok();
                }
                Ok(ActorMessage::Stop) | Err(_) => break,
            }
        }
    }
}

struct ActorHandle {
    sender: Sender<ActorMessage>,
}

impl ActorHandle {
    fn spawn() -> Self {
        let (sender, receiver) = mpsc::channel();
        let actor = Actor::new(receiver);
        
        thread::spawn(move || {
            actor.run();
        });
        
        Self { sender }
    }
    
    fn increment(&self) {
        self.sender.send(ActorMessage::Increment).ok();
    }
    
    fn get(&self) -> i32 {
        let (tx, rx) = mpsc::channel();
        self.sender.send(ActorMessage::Get(tx)).ok();
        rx.recv().unwrap_or(0)
    }
}

fn main() {
    let actor = ActorHandle::spawn();
    
    let mut handles = vec![];
    for _ in 0..10 {
        let actor = ActorHandle { sender: actor.sender.clone() };
        handles.push(thread::spawn(move || {
            for _ in 0..100 {
                actor.increment();
            }
        }));
    }
    
    for handle in handles {
        handle.join().unwrap();
    }
    
    println!("Counter: {}", actor.get());
}
```

### Pattern 11: Work Stealing Queue

```rust
use std::sync::{Arc, Mutex};
use std::collections::VecDeque;
use std::thread;

struct WorkQueue<T> {
    queue: Arc<Mutex<VecDeque<T>>>,
}

impl<T: Send + 'static> WorkQueue<T> {
    fn new() -> Self {
        Self {
            queue: Arc::new(Mutex::new(VecDeque::new())),
        }
    }
    
    fn push(&self, item: T) {
        self.queue.lock().unwrap().push_back(item);
    }
    
    fn pop(&self) -> Option<T> {
        self.queue.lock().unwrap().pop_front()
    }
    
    fn spawn_workers<F>(&self, num_workers: usize, work_fn: F)
    where
        F: Fn(T) + Send + 'static + Clone,
    {
        for _ in 0..num_workers {
            let queue = self.queue.clone();
            let work_fn = work_fn.clone();
            
            thread::spawn(move || {
                loop {
                    let item = queue.lock().unwrap().pop_front();
                    match item {
                        Some(item) => work_fn(item),
                        None => thread::yield_now(),
                    }
                }
            });
        }
    }
}
```

---

## Common Pitfalls and Solutions

### Pitfall 1: Deadlocks

```rust
use std::sync::Mutex;

// WRONG: Can deadlock
fn deadlock_example() {
    let lock1 = Mutex::new(1);
    let lock2 = Mutex::new(2);
    
    // Thread 1: lock1 -> lock2
    // Thread 2: lock2 -> lock1
    // DEADLOCK!
}

// RIGHT: Consistent lock ordering
fn no_deadlock() {
    let lock1 = Mutex::new(1);
    let lock2 = Mutex::new(2);
    
    // Always acquire locks in the same order
    let _g1 = lock1.lock().unwrap();
    let _g2 = lock2.lock().unwrap();
}
```

### Pitfall 2: Poisoned Locks

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn handle_poison() {
    let data = Arc::new(Mutex::new(vec![1, 2, 3]));
    let data_clone = Arc::clone(&data);
    
    let handle = thread::spawn(move || {
        let mut guard = data_clone.lock().unwrap();
        guard.push(4);
        panic!("Oops!"); // Lock becomes poisoned
    });
    
    handle.join().ok();
    
    // Handle poisoned lock
    match data.lock() {
        Ok(guard) => println!("Data: {:?}", *guard),
        Err(poisoned) => {
            // Can still access the data
            let guard = poisoned.into_inner();
            println!("Recovered: {:?}", *guard);
        }
    }
}
```

### Pitfall 3: False Sharing

```rust
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;

// WRONG: False sharing (cache line bouncing)
struct BadCounters {
    counter1: AtomicUsize,
    counter2: AtomicUsize, // On same cache line!
}

// RIGHT: Pad to separate cache lines
#[repr(align(64))] // Cache line size
struct GoodCounters {
    counter1: AtomicUsize,
    _pad: [u8; 56],
    counter2: AtomicUsize,
}
```

---

## Testing Concurrent Code

```rust
use std::sync::{Arc, Mutex};
use std::thread;

#[cfg(test)]
mod tests {
    use super::*;
    
    #[test]
    fn test_concurrent_increment() {
        let counter = Arc::new(Mutex::new(0));
        let mut handles = vec![];
        
        for _ in 0..100 {
            let counter = Arc::clone(&counter);
            handles.push(thread::spawn(move || {
                let mut num = counter.lock().unwrap();
                *num += 1;
            }));
        }
        
        for handle in handles {
            handle.join().unwrap();
        }
        
        assert_eq!(*counter.lock().unwrap(), 100);
    }
    
    // Use loom for more thorough testing
    #[test]
    #[cfg(loom)]
    fn test_with_loom() {
        loom::model(|| {
            // Test concurrent scenarios
        });
    }
}
```

---

## Summary Table

| Type | Send | Sync | Use Case |
|------|------|------|----------|
| `i32`, `String`, `Vec<T>` | ✅ | ✅ | Most types |
| `Rc<T>` | ❌ | ❌ | Single-threaded RC |
| `Arc<T>` | ✅* | ✅* | Thread-safe RC |
| `RefCell<T>` | ✅* | ❌ | Interior mutability (not thread-safe) |
| `Mutex<T>` | ✅* | ✅* | Mutable shared state |
| `RwLock<T>` | ✅* | ✅* | Read-heavy workloads |
| `Cell<T>` | ✅* | ❌ | Copy types only |
| `*const T`, `*mut T` | ❌ | ❌ | Raw pointers |

\* Depends on `T`

---

## Key Takeaways

1. **`Send`** = Can move between threads
2. **`Sync`** = Can share references between threads
3. **Most types are automatically `Send + Sync`**
4. **Use `Arc<Mutex<T>>` for shared mutable state**
5. **Use `Arc<RwLock<T>>` for read-heavy workloads**
6. **Use atomics for lock-free operations**
7. **Always consider lock ordering to prevent deadlocks**
8. **Test concurrent code thoroughly (consider `loom`)**

This covers the full spectrum from basics to production-grade concurrent Rust architectures.