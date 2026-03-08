# The `move` Keyword in Rust — A Comprehensive Deep-Dive

---

## Mental Model Before We Begin

Before touching syntax, engrave this into your mind:

> **Rust's ownership system is a compile-time region-based memory model. The `move` keyword is a *semantic declaration* that changes how the compiler resolves variable capture — from borrow-by-default to own-by-transfer.**

Think of closures as functions with an invisible struct that captures their environment. `move` dictates *how* that struct is populated — by reference or by value.

---

## 1. Ownership & Capture: The Foundation

### How Closures Capture Their Environment

Rust closures are desugared by the compiler into anonymous structs implementing one or more of these traits:

| Trait | Condition | Closure Can... |
|-------|-----------|----------------|
| `FnOnce` | Takes ownership of captured vars | Be called once |
| `FnMut` | Mutably borrows captured vars | Be called multiple times (mutably) |
| `Fn` | Immutably borrows captured vars | Be called multiple times (immutably) |

Without `move`, the compiler *infers* the minimal capture mode. With `move`, you *force* ownership transfer for **all** captured variables.

```rust
fn main() {
    let data = vec![1, 2, 3];

    // Without move: compiler infers borrow
    // The closure holds &Vec<i32>, not Vec<i32>
    let print_data = || println!("{:?}", data);
    print_data();
    println!("{:?}", data); // data still valid — borrow was released

    // With move: closure takes ownership of data
    let owned_print = move || println!("{:?}", data);
    owned_print();
    // println!("{:?}", data); // ERROR: value moved into closure
}
```

### The Invisible Struct Desugaring

```rust
// This closure:
let x = 5;
let add_x = move |n| n + x;

// Desugars to approximately:
struct AddXClosure {
    x: i32,  // owned copy, not reference
}

impl FnOnce<(i32,)> for AddXClosure {
    type Output = i32;
    fn call_once(self, (n,): (i32,)) -> i32 { n + self.x }
}

impl FnMut<(i32,)> for AddXClosure {
    fn call_mut(&mut self, (n,): (i32,)) -> i32 { n + self.x }
}

impl Fn<(i32,)> for AddXClosure {
    fn call(&self, (n,): (i32,)) -> i32 { n + self.x }
}
```

This is not just conceptual — understanding this struct is the key to reasoning about lifetimes, trait bounds, and `Send`/`Sync` implications.

---

## 2. Where `move` Appears in Rust

`move` is valid in exactly **three** syntactic positions:

```
1. move || { ... }        — move closure
2. move |args| expr       — move closure (expression body)
3. move async { ... }     — move async block
```

That's it. `move` is not a standalone expression, not a function, not a type — it is a *closure/async modifier*.

---

## 3. The Lifetime Problem `move` Solves

### Problem: Closures Outliving Their Environment

```rust
fn make_adder_broken(x: i32) -> impl Fn(i32) -> i32 {
    // ERROR: cannot return closure that borrows local variable `x`
    // `x` is dropped when make_adder returns
    |n| n + x
    //  ^ x would be a dangling reference
}

fn make_adder_fixed(x: i32) -> impl Fn(i32) -> i32 {
    // CORRECT: closure owns x, no lifetime issue
    move |n| n + x
}

fn main() {
    let add5 = make_adder_fixed(5);
    println!("{}", add5(10)); // 15
    println!("{}", add5(20)); // 25
}
```

The compiler's error without `move` is:
```
error[E0597]: `x` does not live long enough
```

`move` is the *only* solution here because you need the closure's lifetime to be independent of the stack frame that created it.

---

## 4. `move` with Threads — The Critical Use Case

### Why Threads Require `move`

Threads in Rust must be `'static` — they cannot borrow data from the spawning thread because:
- The spawning thread might finish before the spawned thread
- This would leave the spawned thread with a dangling pointer

```rust
use std::thread;

fn main() {
    let message = String::from("Hello from main thread");

    // ERROR without move:
    // closure may outlive current function, but it borrows `message`
    // thread::spawn(|| println!("{}", message));

    // CORRECT: ownership of message transfers to new thread
    let handle = thread::spawn(move || {
        println!("{}", message);
        // message is now owned by this thread
    });

    // println!("{}", message); // ERROR: moved into thread
    handle.join().unwrap();
}
```

### Thread Safety & `Send` Bound

`thread::spawn` requires `F: Send + 'static`. When you `move` into a closure:
- `'static` is satisfied because no borrows remain
- `Send` is satisfied if all captured types are `Send`

```rust
use std::thread;
use std::rc::Rc;        // NOT Send
use std::sync::Arc;    // IS Send

fn main() {
    let rc_data = Rc::new(42);
    let arc_data = Arc::new(42);

    // ERROR: Rc<i32> is not Send
    // thread::spawn(move || println!("{}", rc_data));

    // CORRECT: Arc<i32> is Send
    thread::spawn(move || println!("{}", arc_data))
        .join()
        .unwrap();
}
```

This is not just a `move` rule — it's the compiler enforcing *data race freedom at compile time*. No other systems language does this.

---

## 5. `move` with Async/Await

### The Async Lifetime Problem

```rust
use tokio::task;

async fn process_data_broken(data: Vec<i32>) {
    // ERROR: async block borrows data but task requires 'static
    task::spawn(async {
        println!("{:?}", data); // borrows data from outer scope
    });
}

async fn process_data_fixed(data: Vec<i32>) {
    // CORRECT: data moved into async block
    task::spawn(async move {
        println!("{:?}", data);
    });
}
```

### move async blocks in Tokio Tasks

```rust
use tokio::sync::mpsc;
use std::time::Duration;

#[tokio::main]
async fn main() {
    let (tx, mut rx) = mpsc::channel::<String>(32);

    // Producer task: moves tx into async block
    let producer = tokio::spawn(async move {
        for i in 0..5 {
            tx.send(format!("message {}", i)).await.unwrap();
            tokio::time::sleep(Duration::from_millis(100)).await;
        }
        // tx dropped here, channel closes
    });

    // Consumer task
    let consumer = tokio::spawn(async move {
        while let Some(msg) = rx.recv().await {
            println!("Received: {}", msg);
        }
    });

    let _ = tokio::join!(producer, consumer);
}
```

The `move` here is *mandatory* — without it, `tx` and `rx` would be borrowed from `main`'s scope, but the spawned tasks need to own them to be `'static`.

---

## 6. Selective Capture — A Critical Nuance

`move` moves **all** captured variables. But you can be selective by *pre-cloning*:

```rust
use std::thread;

fn main() {
    let expensive_data = vec![1, 2, 3, 4, 5]; // large, don't want to move
    let id = 42;                               // Copy type — clone is free

    // Strategy: clone only what the thread needs
    let data_for_thread = expensive_data.clone();

    let handle = thread::spawn(move || {
        // data_for_thread and id are moved in
        // expensive_data stays in main
        println!("Thread {}: {:?}", id, data_for_thread);
    });

    // expensive_data still available here
    println!("Main still owns: {:?}", expensive_data);
    handle.join().unwrap();
}
```

### Capturing by Reference Inside move Closures

A subtle technique: capture an *Arc* or *reference-counted* type to simulate shared ownership:

```rust
use std::sync::{Arc, Mutex};
use std::thread;

fn main() {
    let shared_counter = Arc::new(Mutex::new(0));
    let mut handles = vec![];

    for i in 0..5 {
        // Clone the Arc, not the data — cheap pointer copy
        let counter_clone = Arc::clone(&shared_counter);

        let handle = thread::spawn(move || {
            let mut count = counter_clone.lock().unwrap();
            *count += 1;
            println!("Thread {} incremented, count = {}", i, *count);
        });

        handles.push(handle);
    }

    for handle in handles {
        handle.join().unwrap();
    }

    println!("Final count: {}", *shared_counter.lock().unwrap());
}
```

This is the canonical Rust pattern for shared mutable state across threads.

---

## 7. `move` with `Copy` Types

For `Copy` types (`i32`, `f64`, `bool`, `char`, raw pointers, etc.), `move` semantically copies:

```rust
fn main() {
    let x: i32 = 42;

    // move with Copy type: x is *copied*, not invalidated
    let closure = move || println!("{}", x);

    closure();
    println!("{}", x); // x is still valid! Copy types are duplicated
}
```

This is why `move` with integer captures doesn't invalidate the original. The compiler uses `Copy` semantics — bitwise duplication.

```rust
fn main() {
    let x = 42i32;
    let y = String::from("hello");

    let c = move || {
        println!("{}", x); // x copied (Copy type)
        println!("{}", y); // y moved (non-Copy type)
    };

    println!("{}", x);  // OK: x was copied
    // println!("{}", y); // ERROR: y was moved
    c();
}
```

---

## 8. Real-World Implementations

### 8.1 — Iterator Adapters with `move`

```rust
fn make_filter_gt(threshold: i32) -> impl Fn(&i32) -> bool {
    move |&x| x > threshold
}

fn make_multiplier(factor: i32) -> impl Fn(i32) -> i32 {
    move |x| x * factor
}

fn main() {
    let data = vec![1, 5, 2, 8, 3, 9, 4];

    let filter_gt_4 = make_filter_gt(4);
    let triple = make_multiplier(3);

    let result: Vec<i32> = data.iter()
        .filter(|x| filter_gt_4(x))
        .map(|&x| triple(x))
        .collect();

    println!("{:?}", result); // [15, 24, 27]
}
```

### 8.2 — Event-Driven Callback System

```rust
use std::collections::HashMap;

type Handler = Box<dyn Fn(&str) + Send>;

struct EventBus {
    handlers: HashMap<String, Vec<Handler>>,
}

impl EventBus {
    fn new() -> Self {
        Self { handlers: HashMap::new() }
    }

    fn subscribe(&mut self, event: &str, handler: Handler) {
        self.handlers
            .entry(event.to_string())
            .or_default()
            .push(handler);
    }

    fn emit(&self, event: &str, data: &str) {
        if let Some(handlers) = self.handlers.get(event) {
            for handler in handlers {
                handler(data);
            }
        }
    }
}

fn main() {
    let mut bus = EventBus::new();
    let prefix = String::from("[LOG]");

    // move captures prefix into the closure
    bus.subscribe("user_login", Box::new(move |data| {
        println!("{} User logged in: {}", prefix, data);
    }));

    bus.subscribe("user_login", Box::new(|data| {
        println!("Metrics: login event for {}", data);
    }));

    bus.emit("user_login", "alice");
    bus.emit("user_login", "bob");
}
```

### 8.3 — Thread Pool with `move` Tasks

```rust
use std::sync::{mpsc, Arc, Mutex};
use std::thread;

type Job = Box<dyn FnOnce() + Send + 'static>;

struct ThreadPool {
    workers: Vec<thread::JoinHandle<()>>,
    sender: mpsc::Sender<Job>,
}

impl ThreadPool {
    fn new(size: usize) -> Self {
        let (sender, receiver) = mpsc::channel::<Job>();
        let receiver = Arc::new(Mutex::new(receiver));
        let mut workers = Vec::with_capacity(size);

        for id in 0..size {
            let rx = Arc::clone(&receiver);
            let handle = thread::spawn(move || {
                // This move captures: id, rx
                println!("Worker {} started", id);
                loop {
                    let job = rx.lock().unwrap().recv();
                    match job {
                        Ok(task) => {
                            println!("Worker {} executing task", id);
                            task(); // FnOnce called here
                        }
                        Err(_) => {
                            println!("Worker {} shutting down", id);
                            break;
                        }
                    }
                }
            });
            workers.push(handle);
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

fn main() {
    let pool = ThreadPool::new(4);

    for i in 0..8 {
        // move captures i into each job closure
        pool.execute(move || {
            println!("Task {} running on thread {:?}", i, thread::current().id());
            thread::sleep(std::time::Duration::from_millis(100));
        });
    }

    thread::sleep(std::time::Duration::from_secs(2));
}
```

### 8.4 — Async Web Handler (Actix-Web Pattern)

```rust
use std::sync::Arc;

// Simulating web framework handler pattern
struct AppState {
    db_pool: String, // imagine this is a real DB pool
    config: Config,
}

struct Config {
    max_connections: usize,
}

// Handler factory — returns async closure capturing shared state
fn create_handler(state: Arc<AppState>) -> impl Fn(String) -> String {
    move |request: String| {
        // state is moved into this closure (Arc clone, cheap)
        format!(
            "Handling '{}' with pool '{}', max_conn={}",
            request,
            state.db_pool,
            state.config.max_connections
        )
    }
}

fn main() {
    let state = Arc::new(AppState {
        db_pool: "postgres://localhost/mydb".to_string(),
        config: Config { max_connections: 100 },
    });

    // Multiple handlers share the same underlying state via Arc
    let handler1 = create_handler(Arc::clone(&state));
    let handler2 = create_handler(Arc::clone(&state));

    println!("{}", handler1("/api/users".to_string()));
    println!("{}", handler2("/api/posts".to_string()));
}
```

### 8.5 — State Machine with `move` Transitions

```rust
#[derive(Debug)]
enum State {
    Idle,
    Processing(String),
    Done(Vec<u8>),
    Error(String),
}

fn make_processor(config: String) -> impl FnMut(State) -> State {
    let mut call_count = 0usize;

    // config and call_count are moved into the closure
    move |state: State| {
        call_count += 1;
        println!("Transition #{} with config: {}", call_count, config);

        match state {
            State::Idle => State::Processing("started".to_string()),
            State::Processing(data) => State::Done(data.into_bytes()),
            State::Done(_) => State::Idle,
            State::Error(e) => {
                eprintln!("Recovering from error: {}", e);
                State::Idle
            }
        }
    }
}

fn main() {
    let mut process = make_processor("v2-config".to_string());

    let mut state = State::Idle;
    for _ in 0..3 {
        println!("Before: {:?}", state);
        state = process(state);
        println!("After: {:?}", state);
        println!("---");
    }
}
```

---

## 9. `move` and `FnOnce` vs `FnMut` vs `Fn`

```rust
fn call_once<F: FnOnce()>(f: F) { f(); }
fn call_mut<F: FnMut()>(mut f: F) { f(); f(); }
fn call_ref<F: Fn()>(f: F) { f(); f(); }

fn main() {
    let data = vec![1, 2, 3];

    // FnOnce: consumes captured data
    let consume = move || {
        drop(data); // data is consumed; closure can only be called once
    };
    call_once(consume);
    // call_once(consume); // ERROR: use of moved value

    // FnMut: mutates captured state
    let mut count = 0;
    let mut increment = move || { count += 1; println!("{}", count); };
    call_mut(increment); // prints 1, then 2

    // Fn: only reads captured state
    let prefix = "Item";
    let printer = move || println!("{}", prefix);
    call_ref(printer); // can call multiple times
}
```

### The Trait Hierarchy

```
FnOnce  ⊇  FnMut  ⊇  Fn
```

Every `Fn` is `FnMut`, every `FnMut` is `FnOnce`. The compiler infers the *most permissive* trait your closure qualifies for.

---

## 10. Advanced: `move` with Scoped Threads (Rayon/Crossbeam)

```rust
use std::thread;

fn main() {
    let data = vec![1, 2, 3, 4, 5, 6, 7, 8];

    // std::thread::scope: threads can borrow from outer scope
    // because they're guaranteed to finish before scope exits
    thread::scope(|s| {
        let (left, right) = data.split_at(4);

        // These closures BORROW, no move needed
        // because scoped threads can't outlive the scope
        s.spawn(|| {
            println!("Left half: {:?}", left);
        });

        s.spawn(|| {
            println!("Right half: {:?}", right);
        });
    });
    // All threads finished, data still valid
    println!("All done: {:?}", data);
}
```

Scoped threads eliminate the need for `move` + `Arc` in many cases — but they require knowing the lifetime at compile time. Regular `thread::spawn` with `move` is for unbounded lifetime tasks.

---

## 11. Common Mistakes and Compiler Errors Decoded

### Mistake 1: Forgetting `move` in thread::spawn
```
error[E0373]: closure may outlive the current function, but it borrows `x`,
which is owned by the current function
help: to force the closure to take ownership of `x`, use the `move` keyword
```
**Fix:** Add `move` before `||`.

### Mistake 2: Moving a non-Clone value into multiple closures
```rust
let data = vec![1, 2, 3];
let c1 = move || println!("{:?}", data);
let c2 = move || println!("{:?}", data); // ERROR: use of moved value
```
**Fix:** Clone before capture:
```rust
let c1 = { let d = data.clone(); move || println!("{:?}", d) };
let c2 = move || println!("{:?}", data);
```

### Mistake 3: Expecting `move` to clone non-Copy types
```rust
let s = String::from("hello");
let c = move || println!("{}", s);
println!("{}", s); // ERROR: s was moved, not copied
```
**Fix:** Either clone `s` before the closure, or restructure ownership.

### Mistake 4: `Rc` across thread boundaries
```rust
use std::rc::Rc;
let data = Rc::new(42);
thread::spawn(move || println!("{}", data)); // ERROR: Rc is not Send
```
**Fix:** Use `Arc` instead of `Rc`.

---

## 12. Performance Considerations

### `move` vs borrow performance

| Scenario | Without `move` | With `move` |
|----------|---------------|-------------|
| `Copy` types | Copy on borrow read | Copy on capture |
| `Clone`-able types | Zero-cost borrow | Full allocation if cloned |
| `Arc<T>` | Borrow of Arc | Arc clone (atomic increment) |
| `String` | Reference to str | Pointer move (no allocation) |

**Key insight:** Moving a `String` or `Vec` is **not** a copy of the heap data — it's a move of the *fat pointer* (ptr, len, cap). This is O(1) regardless of data size.

```rust
fn main() {
    let big_vec = vec![0u8; 1_000_000]; // 1MB on heap

    // Moving big_vec into closure: only moves the 24-byte struct
    // (pointer + length + capacity). Heap data stays in place.
    let closure = move || big_vec.len();

    println!("{}", closure()); // 1000000, no memcpy of 1MB
}
```

---

## 13. Mental Models for Mastery

### Model 1: "The Capture Bag"
A closure is a bag that collects variables from its environment. Without `move`, it puts *references* in the bag. With `move`, it puts the *actual values* in the bag. The bag lives as long as the closure lives.

### Model 2: "Lifetime Independence"
Ask: "Does this closure need to outlive the scope where its environment exists?" If yes → `move` is mandatory. The lifetimes must be decoupled.

### Model 3: "Thread Boundary = Ownership Boundary"
Every thread boundary is an ownership boundary. Data cannot cross without being owned. `move` is the *visa* that authorizes data to cross.

### Model 4: "The Compiler as a Borrow Checker Oracle"
When the compiler rejects your closure, read the error as a *logical argument*: "If thread A can outlive thread B, and B holds a reference to B's local data, A could use a dangling pointer." `move` resolves this by making A *own* the data.

---

## 14. Summary — Decision Tree

```
Do you need a closure?
├── Will the closure outlive the scope that created the variables?
│   └── YES → Use `move` (returning closures, spawning threads/tasks)
├── Are you spawning an OS thread with thread::spawn?
│   └── YES → Use `move` (required for 'static bound)
├── Are you spawning a tokio/async-std task?
│   └── YES → Use `move async { }` (required for 'static bound)
├── Are all captured variables Copy types?
│   └── YES → `move` is optional but harmless (values are duplicated)
├── Do you need to mutate captured state across calls?
│   └── YES → Consider `move` + `FnMut`
└── Are you using scoped threads (thread::scope)?
    └── NO → Borrows are fine without `move`
```

---

The `move` keyword is ultimately an expression of Rust's core philosophy: **explicit ownership semantics, zero implicit costs, no hidden copies, no undefined behavior**. Every time you write `move`, you are making a conscious architectural decision about who owns data and how long it lives.

Master this, and you master one of the deepest aspects of Rust's type system. The patterns here — thread pools, event buses, async tasks, state machines — are the exact patterns found in production Rust codebases like Tokio, Actix, Rayon, and the Rust compiler itself.

Exactly 💡 — in Rust, the **`move` keyword** changes how a **closure** captures variables.

By default, closures **borrow** values from the environment (`&` or `&mut`).
With `move`, the closure instead **takes ownership** of the captured values.

---

## 1. Default Closure Capture (borrowing)

```rust
fn main() {
    let s = String::from("hello");

    let closure = || {
        println!("Borrowed: {}", s); // 👈 borrows `s` immutably
    };

    closure();
    println!("Still usable: {}", s); // ✅ still usable
}
```

Here, `s` is borrowed, not moved, so you can still use it after calling the closure.

---

## 2. `move` Closure Capture (ownership)

```rust
fn main() {
    let s = String::from("hello");

    let closure = move || {
        println!("Moved: {}", s); // 👈 takes ownership
    };

    closure();
    // println!("{}", s); // ❌ Error: `s` moved into closure
}
```

* The `move` keyword forces the closure to **take ownership** of `s`.
* After that, `s` is no longer accessible in the outer scope.

---

## 3. Why `move` is Useful

### a) In Threads

Closures used with `std::thread::spawn` **must be `'static`**, meaning they can’t borrow local variables. `move` fixes this by transferring ownership.

```rust
use std::thread;

fn main() {
    let s = String::from("hello");

    let handle = thread::spawn(move || {
        println!("From thread: {}", s);
    });

    handle.join().unwrap();
}
```

Without `move`, the closure would borrow `s`, which doesn’t live long enough for the thread.

---

### b) In `async` / Futures

Async tasks may outlive the scope they’re created in, so `move` ensures all captured variables are owned by the closure.

```rust
async fn example() {
    let data = String::from("async data");

    let fut = async move {
        println!("Inside future: {}", data);
    };

    fut.await;
}
```

---

## 4. Key Rules

* **Without `move`** → closure borrows environment (`&` or `&mut`).
* **With `move`** → closure takes ownership (`T`).
* `Copy` types (like integers) behave the same in both cases, because ownership copying is trivial.

---

## 🌳 Summary

* **`|| { ... }`** → captures by reference (borrow).
* **`move || { ... }`** → captures by ownership (move).
* Needed when closures may **outlive their scope** (threads, async tasks).

---

👉 Quick mental model:

* **Normal closure** = “I’ll borrow your stuff while I run.”
* **`move` closure** = “I’ll take your stuff with me, you can’t use it anymore.”

---

Would you like me to also illustrate this with an **ASCII diagram showing ownership flow (stack vs heap)** so you can see *where the values go* in `move` vs normal closures?
