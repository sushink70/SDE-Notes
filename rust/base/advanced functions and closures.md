# Advanced Functions and Closures in Rust

**One-line:** Functions are static code pointers; closures are anonymous functions that capture environment variables with zero-cost abstractions via compiler-generated structs.

**Analogy:** A function is like a vending machine—same behavior every time. A closure is like your personal assistant who remembers your preferences (captured variables) and acts accordingly.

---

## Table of Contents
1. [Function Pointers & Higher-Order Functions](#1-function-pointers--higher-order-functions)
2. [Closure Fundamentals & Capture Modes](#2-closure-fundamentals--capture-modes)
3. [Fn, FnMut, FnOnce Traits Deep Dive](#3-fn-fnmut-fnonce-traits-deep-dive)
4. [Returning Closures & Lifetime Elision](#4-returning-closures--lifetime-elision)
5. [Performance & Zero-Cost Abstractions](#5-performance--zero-cost-abstractions)
6. [Advanced Patterns](#6-advanced-patterns)
7. [Exercises](#7-exercises)

---

## 1. Function Pointers & Higher-Order Functions

### Minimal Example
```rust
// src/bin/function_pointers.rs
fn add(a: i32, b: i32) -> i32 { a + b }
fn multiply(a: i32, b: i32) -> i32 { a * b }

fn apply_op(x: i32, y: i32, op: fn(i32, i32) -> i32) -> i32 {
    op(x, y)
}

fn main() {
    println!("{}", apply_op(5, 3, add));       // 8
    println!("{}", apply_op(5, 3, multiply));  // 15
    
    // Function pointers can be stored
    let ops: [fn(i32, i32) -> i32; 2] = [add, multiply];
    println!("{}", ops[0](10, 2));  // 12
}
```

**Run:** `cargo run --bin function_pointers`

### Internal Breakdown

1. **Function pointer type:** `fn(i32, i32) -> i32` is a **concrete type**, not a trait
2. **Size:** Always 8 bytes (pointer to code)
3. **No capture:** Cannot capture environment (stateless)
4. **Coercion:** Non-capturing closures automatically coerce to function pointers

```rust
// src/bin/fn_coercion.rs
fn main() {
    let closure = |x: i32| x + 1;  // Non-capturing closure
    let fn_ptr: fn(i32) -> i32 = closure;  // Coercion works!
    
    let y = 5;
    let capturing = |x: i32| x + y;  // Captures 'y'
    // let bad: fn(i32) -> i32 = capturing;  // ❌ Compile error!
}
```

---

## 2. Closure Fundamentals & Capture Modes

### Three Capture Modes

```rust
// src/bin/capture_modes.rs
fn main() {
    let s = String::from("hello");
    let mut count = 0;
    let immutable = 42;

    // 1. IMMUTABLE BORROW (&T)
    let by_ref = || {
        println!("{}", s);        // Borrows &String
        println!("{}", immutable); // Borrows &i32
    };
    by_ref();
    println!("{}", s);  // ✅ Still valid

    // 2. MUTABLE BORROW (&mut T)
    let mut by_mut_ref = || {
        count += 1;  // Borrows &mut i32
    };
    by_mut_ref();
    // println!("{}", count);  // ❌ Can't use while closure lives

    // 3. MOVE (takes ownership)
    let by_move = move || {
        println!("{}", s);  // Takes ownership of String
    };
    by_move();
    // println!("{}", s);  // ❌ s was moved
}
```

**Rule of thumb:**
- Rust picks **smallest** capture mode that works
- Use `move` to force ownership transfer (common with threads)

### How Closures Work Internally

```rust
// What the compiler generates for:
let x = 5;
let add_x = |y| x + y;

// Roughly becomes:
struct ClosureEnv {
    x: i32,  // Captured by immutable reference or value
}

impl ClosureEnv {
    fn call(&self, y: i32) -> i32 {
        self.x + y
    }
}
```

**Key insight:** Closures are **anonymous structs** with a `call` method. Zero runtime overhead!

---

## 3. Fn, FnMut, FnOnce Traits Deep Dive

### The Trait Hierarchy

```
FnOnce  (can be called once)
  ↑
FnMut   (can mutate captures, callable multiple times)
  ↑
Fn      (immutable, callable any number of times)
```

**Every `Fn` is also `FnMut` and `FnOnce`, but not vice versa.**

```rust
// src/bin/fn_traits.rs
use std::collections::HashMap;

fn call_fn<F>(f: F) where F: Fn() {
    f();
    f();  // ✅ Can call multiple times
}

fn call_fn_mut<F>(mut f: F) where F: FnMut() {
    f();
    f();  // ✅ Can call multiple times
}

fn call_fn_once<F>(f: F) where F: FnOnce() {
    f();
    // f();  // ❌ Can only call once
}

fn main() {
    let s = String::from("data");
    
    // Fn - immutable borrow
    let fn_closure = || println!("{}", s);
    call_fn(fn_closure);
    
    // FnMut - mutable borrow
    let mut cache: HashMap<i32, i32> = HashMap::new();
    let mut fn_mut_closure = |x: i32| {
        cache.entry(x).or_insert(x * 2);
    };
    call_fn_mut(&mut fn_mut_closure);
    
    // FnOnce - consumes captured value
    let fn_once_closure = || drop(s);
    call_fn_once(fn_once_closure);
}
```

### When Each Trait is Required

| Trait    | Use Case | Example |
|----------|----------|---------|
| `Fn`     | Read-only operations, can be called concurrently | Filters, maps, predicates |
| `FnMut`  | Stateful operations, needs exclusive access | Accumulators, iterators with state |
| `FnOnce` | Consumes environment, transfers ownership | Thread spawning, resource cleanup |

---

## 4. Returning Closures & Lifetime Elision

### Problem: Unknown Size

```rust
// ❌ DOESN'T COMPILE
fn returns_closure() -> impl Fn(i32) -> i32 {
    let num = 5;
    |x| x + num  // ❌ num doesn't live long enough!
}
```

### Solution 1: Move + impl Trait

```rust
// src/bin/return_closure.rs
fn make_adder(n: i32) -> impl Fn(i32) -> i32 {
    move |x| x + n  // ✅ Moves 'n' into closure
}

fn main() {
    let add_5 = make_adder(5);
    println!("{}", add_5(10));  // 15
}
```

### Solution 2: Box (dynamic dispatch)

```rust
// src/bin/boxed_closure.rs
fn make_multiplier(n: i32) -> Box<dyn Fn(i32) -> i32> {
    Box::new(move |x| x * n)
}

fn main() {
    let mult_3 = make_multiplier(3);
    println!("{}", mult_3(7));  // 21
}
```

**Trade-offs:**
- `impl Trait`: Zero-cost, monomorphization, single concrete type
- `Box<dyn Fn>`: Heap allocation, dynamic dispatch, can store mixed types

### Advanced: Lifetimes in Closures

```rust
// src/bin/closure_lifetimes.rs
fn apply_to_str<'a, F>(s: &'a str, f: F) -> String
where
    F: Fn(&'a str) -> String,
{
    f(s)
}

fn main() {
    let text = "hello";
    let result = apply_to_str(text, |s| s.to_uppercase());
    println!("{}", result);  // HELLO
}
```

---

## 5. Performance & Zero-Cost Abstractions

### Benchmark Setup

```rust
// benches/closure_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn direct_call(n: i32) -> i32 {
    n * 2
}

fn using_fn_pointer(n: i32, f: fn(i32) -> i32) -> i32 {
    f(n)
}

fn using_closure<F: Fn(i32) -> i32>(n: i32, f: F) -> i32 {
    f(n)
}

fn benchmark(c: &mut Criterion) {
    c.bench_function("direct", |b| b.iter(|| {
        black_box(direct_call(black_box(42)))
    }));

    c.bench_function("fn_pointer", |b| b.iter(|| {
        black_box(using_fn_pointer(black_box(42), direct_call))
    }));

    c.bench_function("closure", |b| b.iter(|| {
        let multiplier = |x| x * 2;
        black_box(using_closure(black_box(42), multiplier))
    }));
}

criterion_group!(benches, benchmark);
criterion_main!(benches);
```

**Cargo.toml:**
```toml
[dev-dependencies]
criterion = "0.5"

[[bench]]
name = "closure_bench"
harness = false
```

**Run:** `cargo bench`

**Expected results:** All three have **identical** performance after optimization. LLVM inlines everything.

### Profiling Closures

```bash
# Install flamegraph
cargo install flamegraph

# Profile with perf
cargo build --release
sudo perf record -g ./target/release/your_binary
sudo perf report
```

---

## 6. Advanced Patterns

### Pattern 1: Builder Pattern with Closures

```rust
// src/bin/builder_closure.rs
struct Request {
    url: String,
    timeout: u64,
    headers: Vec<(String, String)>,
}

impl Request {
    fn build<F>(url: &str, config: F) -> Self
    where
        F: FnOnce(&mut RequestBuilder),
    {
        let mut builder = RequestBuilder::new(url);
        config(&mut builder);
        builder.build()
    }
}

struct RequestBuilder {
    url: String,
    timeout: u64,
    headers: Vec<(String, String)>,
}

impl RequestBuilder {
    fn new(url: &str) -> Self {
        Self {
            url: url.to_string(),
            timeout: 30,
            headers: Vec::new(),
        }
    }

    fn timeout(&mut self, secs: u64) -> &mut Self {
        self.timeout = secs;
        self
    }

    fn header(&mut self, key: &str, value: &str) -> &mut Self {
        self.headers.push((key.to_string(), value.to_string()));
        self
    }

    fn build(self) -> Request {
        Request {
            url: self.url,
            timeout: self.timeout,
            headers: self.headers,
        }
    }
}

fn main() {
    let req = Request::build("https://api.example.com", |b| {
        b.timeout(60).header("Authorization", "Bearer token");
    });
    
    println!("URL: {}, Timeout: {}", req.url, req.timeout);
}
```

### Pattern 2: Retry Logic with Closures

```rust
// src/bin/retry_pattern.rs
use std::thread;
use std::time::Duration;

fn retry<F, T, E>(mut operation: F, max_attempts: u32) -> Result<T, E>
where
    F: FnMut() -> Result<T, E>,
{
    let mut attempts = 0;
    loop {
        attempts += 1;
        match operation() {
            Ok(result) => return Ok(result),
            Err(e) if attempts >= max_attempts => return Err(e),
            Err(_) => {
                println!("Attempt {} failed, retrying...", attempts);
                thread::sleep(Duration::from_millis(100 * attempts as u64));
            }
        }
    }
}

fn main() {
    let mut counter = 0;
    let result = retry(
        || {
            counter += 1;
            if counter < 3 {
                Err("Not ready")
            } else {
                Ok("Success!")
            }
        },
        5,
    );
    
    println!("{:?}", result);  // Ok("Success!")
}
```

### Pattern 3: Custom Iterator with State

```rust
// src/bin/stateful_iterator.rs
struct Fibonacci {
    curr: u64,
    next: u64,
}

impl Fibonacci {
    fn new() -> Self {
        Self { curr: 0, next: 1 }
    }

    fn take_while<F>(self, mut predicate: F) -> impl Iterator<Item = u64>
    where
        F: FnMut(&u64) -> bool + 'static,
    {
        self.take_while(move |x| predicate(x))
    }
}

impl Iterator for Fibonacci {
    type Item = u64;

    fn next(&mut self) -> Option<Self::Item> {
        let current = self.curr;
        self.curr = self.next;
        self.next = current + self.next;
        Some(current)
    }
}

fn main() {
    let fibs: Vec<u64> = Fibonacci::new()
        .take_while(|&x| x < 100)
        .collect();
    println!("{:?}", fibs);  // [0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]
}
```

### Pattern 4: Dependency Injection

```rust
// src/bin/dependency_injection.rs
trait Logger {
    fn log(&self, msg: &str);
}

struct Service<L: Logger> {
    logger: L,
}

impl<L: Logger> Service<L> {
    fn new(logger: L) -> Self {
        Self { logger }
    }

    fn do_work(&self) {
        self.logger.log("Working...");
    }
}

// Closure-based logger for testing
fn main() {
    let messages = std::sync::Arc::new(std::sync::Mutex::new(Vec::new()));
    let msg_clone = messages.clone();
    
    let logger = move |msg: &str| {
        msg_clone.lock().unwrap().push(msg.to_string());
    };

    // Can't use closure directly with trait, need wrapper
    struct ClosureLogger<F: Fn(&str)>(F);
    
    impl<F: Fn(&str)> Logger for ClosureLogger<F> {
        fn log(&self, msg: &str) {
            (self.0)(msg);
        }
    }

    let svc = Service::new(ClosureLogger(logger));
    svc.do_work();
    
    println!("{:?}", messages.lock().unwrap());  // ["Working..."]
}
```

---

## 7. Common Pitfalls

### Pitfall 1: Borrowing in Loops

```rust
// ❌ WRONG
let mut data = vec![1, 2, 3];
let mut closures = vec![];

for i in 0..3 {
    closures.push(|| data[i]);  // ❌ Captures mutable reference in loop
}

// ✅ CORRECT
let data = vec![1, 2, 3];
let closures: Vec<_> = (0..3)
    .map(|i| move || data[i])  // Each closure gets its own copy of 'i'
    .collect();
```

### Pitfall 2: Move vs Copy

```rust
let x = 5;  // i32 is Copy
let closure = move || x + 1;
println!("{}", x);  // ✅ Works! Copy types are copied, not moved

let s = String::from("hello");  // String is NOT Copy
let closure = move || println!("{}", s);
// println!("{}", s);  // ❌ s was moved
```

### Pitfall 3: Lifetime Issues with Threads

```rust
use std::thread;

// ❌ WRONG
fn spawn_wrong(s: &str) {
    thread::spawn(|| {
        println!("{}", s);  // ❌ 's' may not live long enough
    });
}

// ✅ CORRECT
fn spawn_correct(s: String) {
    thread::spawn(move || {
        println!("{}", s);  // ✅ Ownership transferred
    });
}
```

---

## Real-World Use Cases

### Use Case 1: Middleware Chain (Web Server)

```rust
// src/bin/middleware.rs
type Request = String;
type Response = String;
type Middleware = Box<dyn Fn(Request, &dyn Fn(Request) -> Response) -> Response>;

fn create_logger() -> Middleware {
    Box::new(|req, next| {
        println!("[LOG] Request: {}", req);
        let res = next(req);
        println!("[LOG] Response: {}", res);
        res
    })
}

fn create_auth(token: String) -> Middleware {
    Box::new(move |req, next| {
        if req.contains(&token) {
            next(req)
        } else {
            "Unauthorized".to_string()
        }
    })
}

fn apply_middleware(middlewares: Vec<Middleware>, handler: impl Fn(Request) -> Response) -> impl Fn(Request) -> Response {
    move |req| {
        fn apply(
            mws: &[Middleware],
            idx: usize,
            req: Request,
            handler: &dyn Fn(Request) -> Response,
        ) -> Response {
            if idx >= mws.len() {
                handler(req)
            } else {
                mws[idx](req, &|r| apply(mws, idx + 1, r, handler))
            }
        }
        apply(&middlewares, 0, req, &handler)
    }
}

fn main() {
    let handler = |req: Request| format!("Handled: {}", req);
    
    let app = apply_middleware(
        vec![create_logger(), create_auth("secret".to_string())],
        handler,
    );
    
    println!("{}", app("Request with secret".to_string()));
}
```

### Use Case 2: Memoization

```rust
// src/bin/memoization.rs
use std::collections::HashMap;
use std::hash::Hash;

fn memoize<A, R, F>(mut f: F) -> impl FnMut(A) -> R
where
    A: Eq + Hash + Clone,
    R: Clone,
    F: FnMut(A) -> R,
{
    let mut cache = HashMap::new();
    move |arg: A| {
        cache
            .entry(arg.clone())
            .or_insert_with(|| f(arg))
            .clone()
    }
}

fn main() {
    let mut expensive_computation = memoize(|x: i32| {
        println!("Computing for {}", x);
        x * x
    });

    println!("{}", expensive_computation(5));  // Prints "Computing for 5", then 25
    println!("{}", expensive_computation(5));  // Just returns 25 (cached)
    println!("{}", expensive_computation(3));  // Prints "Computing for 3", then 9
}
```

### Use Case 3: Plugin System

```rust
// src/bin/plugin_system.rs
type PluginFn = Box<dyn Fn(&str) -> String>;

struct PluginRegistry {
    plugins: Vec<PluginFn>,
}

impl PluginRegistry {
    fn new() -> Self {
        Self {
            plugins: Vec::new(),
        }
    }

    fn register<F>(&mut self, plugin: F)
    where
        F: Fn(&str) -> String + 'static,
    {
        self.plugins.push(Box::new(plugin));
    }

    fn execute(&self, input: &str) -> Vec<String> {
        self.plugins.iter().map(|p| p(input)).collect()
    }
}

fn main() {
    let mut registry = PluginRegistry::new();

    // Register plugins
    registry.register(|s| s.to_uppercase());
    registry.register(|s| s.chars().rev().collect());
    registry.register(|s| format!("Length: {}", s.len()));

    let results = registry.execute("hello");
    for result in results {
        println!("{}", result);
    }
    // Output:
    // HELLO
    // olleh
    // Length: 5
}
```

---

## Production-Ready Example with Tests

```rust
// src/lib.rs
use std::sync::{Arc, Mutex};
use std::collections::HashMap;

/// Thread-safe event bus using closures
pub struct EventBus<E> {
    handlers: Arc<Mutex<HashMap<String, Vec<Box<dyn Fn(&E) + Send + Sync>>>>>,
}

impl<E> EventBus<E> {
    pub fn new() -> Self {
        Self {
            handlers: Arc::new(Mutex::new(HashMap::new())),
        }
    }

    pub fn subscribe<F>(&self, event_type: &str, handler: F)
    where
        F: Fn(&E) + Send + Sync + 'static,
    {
        let mut handlers = self.handlers.lock().unwrap();
        handlers
            .entry(event_type.to_string())
            .or_insert_with(Vec::new)
            .push(Box::new(handler));
    }

    pub fn publish(&self, event_type: &str, event: &E) {
        let handlers = self.handlers.lock().unwrap();
        if let Some(handlers) = handlers.get(event_type) {
            for handler in handlers {
                handler(event);
            }
        }
    }
}

impl<E> Clone for EventBus<E> {
    fn clone(&self) -> Self {
        Self {
            handlers: Arc::clone(&self.handlers),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicUsize, Ordering};

    #[test]
    fn test_event_bus_basic() {
        let bus = EventBus::new();
        let counter = Arc::new(AtomicUsize::new(0));
        let counter_clone = counter.clone();

        bus.subscribe("test", move |_: &i32| {
            counter_clone.fetch_add(1, Ordering::SeqCst);
        });

        bus.publish("test", &42);
        bus.publish("test", &99);

        assert_eq!(counter.load(Ordering::SeqCst), 2);
    }

    #[test]
    fn test_multiple_handlers() {
        let bus = EventBus::new();
        let results = Arc::new(Mutex::new(Vec::new()));
        
        let results1 = results.clone();
        bus.subscribe("event", move |x: &i32| {
            results1.lock().unwrap().push(*x * 2);
        });

        let results2 = results.clone();
        bus.subscribe("event", move |x: &i32| {
            results2.lock().unwrap().push(*x + 10);
        });

        bus.publish("event", &5);

        let final_results = results.lock().unwrap();
        assert_eq!(*final_results, vec![10, 15]);
    }
}
```

---

## Security Checklist for Closures

- [ ] **Lifetime safety:** Ensure captured references don't outlive their data
- [ ] **Thread safety:** Use `Send + Sync` bounds for multi-threaded closures
- [ ] **Memory leaks:** Avoid cyclic references with `Rc<RefCell<Closure>>`
- [ ] **Panic safety:** Closures that panic can poison mutexes
- [ ] **Type confusion:** Be explicit with `dyn Fn` to prevent type erasure bugs
- [ ] **Sensitive data:** Use `move` to prevent accidental capture of secrets

---

## Exercises

### Exercise 1: Custom Filter Pipeline
**Goal:** Build a chainable filter system using closures.

```rust
// Implement this API:
let data = vec![1, 2, 3, 4, 5, 6];
let result = Pipeline::new(data)
    .filter(|x| x % 2 == 0)
    .map(|x| x * 2)
    .filter(|x| x > 5)
    .collect();
// Expected: [8, 12]
```

**Hints:**
- Store closures in struct fields
- Use generics with trait bounds
- Return `Self` for chaining

---

### Exercise 2: Rate Limiter
**Goal:** Create a rate-limiting wrapper for any function.

```rust
// Should allow only N calls per time window
let mut limited = rate_limit(|| println!("Called!"), 3, Duration::from_secs(1));
for _ in 0..5 {
    limited();  // Should only print 3 times
}
```

**Hints:**
- Use `std::time::Instant` for tracking
- Store state in closure's captured variables
- Return a closure that checks rate limit

---

### Exercise 3: Async Callback System
**Goal:** Build a callback registry that supports async handlers.

```rust
// Should support:
registry.on("user_login", |user_id| async move {
    // Perform async DB lookup
});
registry.trigger("user_login", 123).await;
```

**Hints:**
- Use `async fn` or `impl Future`
- Store `Pin<Box<dyn Future>>` in registry
- Consider using `tokio` for runtime

---

## Further Reading

**Articles:**
1. [Closures: Magic Functions - Rust Book](https://doc.rust-lang.org/book/ch13-01-closures.html)
2. [The Fn Traits - Rustonomicon](https://doc.rust-lang.org/nomicon/phantom-data.html)

**Books:**
1. *Programming Rust* by Jim Blandy (Chapter 14: Closures)
2. *Rust for Rustaceans* by Jon Gjengset (Chapter 5: Project Structure)

**Repositories:**
1. [rayon](https://github.com/rayon-rs/rayon) - Parallel iterators using closures
2. [tower](https://github.com/tower-rs/tower) - Service abstraction with middleware pattern

---

## Complete Project Structure

```
advanced-closures/
├── Cargo.toml
├── src/
│   ├── lib.rs                      # EventBus implementation
│   └── bin/
│       ├── function_pointers.rs
│       ├── capture_modes.rs
│       ├── fn_traits.rs
│       ├── return_closure.rs
│       ├── builder_closure.rs
│       ├── retry_pattern.rs
│       ├── middleware.rs
│       └── memoization.rs
├── benches/
│   └── closure_bench.rs
└── tests/
    └── integration_test.rs
```

**Run everything:**
```bash
cargo test
cargo bench
cargo run --bin middleware
```

---

**Next Steps:**
1. Implement all 3 exercises
2. Profile the EventBus with 10,000 events
3. Read tower's middleware implementation
4. Build a mini-framework using these patterns

You now have the complete mental model for closures in Rust. The key insight: closures are **zero-cost abstractions** that compile down to structs with methods. Master this, and you'll write idiomatic, performant Rust.

# Advanced Functions and Closures in Rust - DEEP DIVE

**One-line:** Closures are compiler-generated anonymous structs implementing Fn* traits, with capture analysis happening at MIR level, enabling zero-cost abstractions through monomorphization.

**Analogy:** Think of closures like custom-built robots. A function is a factory robot (same every time). A closure is a robot you build on-the-fly that "remembers" things from its construction environment (captured variables). The robot's memory slots (struct fields) are determined by analyzing what it needs to remember.

---

## Table of Contents
1. [Compiler Internals: How Closures Really Work](#1-compiler-internals-how-closures-really-work)
2. [Memory Layout & Performance](#2-memory-layout--performance)
3. [Capture Analysis & Borrow Checker Integration](#3-capture-analysis--borrow-checker-integration)
4. [Fn/FnMut/FnOnce: The Complete Picture](#4-fnfnmutfnonce-the-complete-picture)
5. [Advanced Lifetime Interactions](#5-advanced-lifetime-interactions)
6. [Hidden Knowledge & Edge Cases](#6-hidden-knowledge--edge-cases)
7. [Real-World Production Patterns](#7-real-world-production-patterns)
8. [Performance Engineering](#8-performance-engineering)
9. [Unsafe & FFI with Closures](#9-unsafe--ffi-with-closures)
10. [Exercises](#10-exercises)

---

## 1. Compiler Internals: How Closures Really Work

### The Desugaring Process

```rust
// src/bin/desugaring.rs

// What you write:
fn example() {
    let x = 5;
    let y = 10;
    let mut z = 15;
    
    let my_closure = |a: i32| {
        println!("{}", x);
        z += a;
        x + y + z
    };
    
    my_closure(20);
}

// What the compiler generates (pseudo-Rust):
struct ClosureEnvironment<'env> {
    x: &'env i32,      // Immutable borrow
    y: &'env i32,      // Immutable borrow  
    z: &'env mut i32,  // Mutable borrow
}

impl<'env> FnMut<(i32,)> for ClosureEnvironment<'env> {
    type Output = i32;
    
    extern "rust-call" fn call_mut(&mut self, args: (i32,)) -> i32 {
        let a = args.0;
        println!("{}", self.x);
        *self.z += a;
        *self.x + *self.y + *self.z
    }
}

fn example_desugared() {
    let x = 5;
    let y = 10;
    let mut z = 15;
    
    let mut my_closure = ClosureEnvironment {
        x: &x,
        y: &y,
        z: &mut z,
    };
    
    FnMut::call_mut(&mut my_closure, (20,));
}
```

### HIR → MIR → LLVM Pipeline

```rust
// src/bin/mir_analysis.rs

// Let's trace how rustc analyzes this:
fn analyze_closure() {
    let s = String::from("hello");
    let n = 42;
    
    let closure = || {
        println!("{}", s);  // Uses s
        n + 1              // Uses n
    };
    
    closure();
}

/*
STAGE 1: HIR (High-level Intermediate Representation)
- Closure is initially opaque
- Captures marked but not analyzed

STAGE 2: Type Inference
- Closure's type parameters get placeholder types
- Capture mode is UNKNOWN at this point

STAGE 3: MIR (Mid-level Intermediate Representation)
- Borrow checker runs here
- Captures analyzed:
  * s: needs &String (only read)
  * n: needs &i32 (only read)
- Determines trait: Fn (no mutation)

STAGE 4: Monomorphization
- Generic closure type becomes concrete
- Struct layout decided:
  struct Closure {
      s: &'a String,  // 8 bytes (pointer)
      n: &'a i32,     // 8 bytes (pointer)
  }
  Total: 16 bytes

STAGE 5: LLVM IR
- call_mut/call/call_once becomes direct function call
- Inlining happens here
- Result: Often ZERO overhead vs hand-written code
*/
}
```

### Proving Zero-Cost: Assembly Analysis

```rust
// src/bin/assembly_compare.rs

pub fn with_closure(v: Vec<i32>) -> i32 {
    v.iter().filter(|&&x| x > 5).map(|&x| x * 2).sum()
}

pub fn manual_loop(v: Vec<i32>) -> i32 {
    let mut sum = 0;
    for &x in &v {
        if x > 5 {
            sum += x * 2;
        }
    }
    sum
}

// Compile and check assembly:
// cargo rustc --release --bin assembly_compare -- --emit asm
// Look at assembly: both produce IDENTICAL code after optimization
```

**Run this:**
```bash
cargo rustc --release --bin assembly_compare -- --emit asm
cat target/release/deps/assembly_compare-*.s | grep -A 20 "with_closure"
cat target/release/deps/assembly_compare-*.s | grep -A 20 "manual_loop"
```

**Hidden Knowledge #1:** The Rust compiler's MIR-level analysis means closures are optimized BEFORE LLVM even sees them. This is why they can be faster than equivalent C++ lambdas in some cases.

---

## 2. Memory Layout & Performance

### Exact Memory Layout

```rust
// src/bin/memory_layout.rs
use std::mem;

fn main() {
    let a = 1u8;
    let b = 2u16;
    let c = 3u32;
    let d = String::from("test");
    
    // Closure capturing all variables
    let closure = || {
        println!("{} {} {} {}", a, b, c, d);
    };
    
    println!("Closure size: {}", mem::size_of_val(&closure));
    println!("Closure align: {}", mem::align_of_val(&closure));
    
    // Let's see what it actually captures:
    // Captures: &u8, &u16, &u32, &String
    // On 64-bit: 4 pointers = 32 bytes
    
    // Compare with move closure
    let move_closure = move || {
        println!("{} {} {} {}", a, b, c, d);
    };
    
    println!("Move closure size: {}", mem::size_of_val(&move_closure));
    // Captures: u8, u16, u32, String
    // With padding: 1 + 1(pad) + 2 + 4 + 24(String) = ~32 bytes
    // String = 3 * 8 bytes (ptr, cap, len)
}
```

### Cache Line Optimization

```rust
// src/bin/cache_optimization.rs
use std::time::Instant;

fn hot_closure_performance() {
    const ITERATIONS: usize = 100_000_000;
    
    // Small capture - fits in cache line
    let x = 42i32;
    let small = || x * 2;
    
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        std::hint::black_box(small());
    }
    println!("Small closure: {:?}", start.elapsed());
    
    // Large capture - doesn't fit well
    let data = vec![0u8; 1024];  // 1KB
    let large = || data.iter().sum::<u8>();
    
    let start = Instant::now();
    for _ in 0..ITERATIONS {
        std::hint::black_box(large());
    }
    println!("Large closure: {:?}", start.elapsed());
}

fn main() {
    hot_closure_performance();
}
```

**Hidden Knowledge #2:** Closures that capture large data structures by reference still pay cache-miss costs. Sometimes `move` + `Arc` is faster than borrowing a large struct.

### Stack vs Heap Allocation

```rust
// src/bin/stack_heap.rs
use std::hint::black_box;

fn stack_allocated() -> impl Fn() -> i32 {
    let x = 42;
    move || x  // Closure lives on stack in caller's frame
}

fn heap_allocated() -> Box<dyn Fn() -> i32> {
    let x = 42;
    Box::new(move || x)  // Closure moved to heap
}

fn compare_allocation() {
    // Stack version: zero allocation
    let stack_closure = stack_allocated();
    let result = black_box(stack_closure());
    
    // Heap version: one allocation
    let heap_closure = heap_allocated();
    let result = black_box(heap_closure());
    
    // Measure with criterion or dhat
}
```

**Benchmark this:**
```rust
// benches/allocation_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion};

fn stack_fn() -> impl Fn() -> i32 {
    let x = 42;
    move || x
}

fn heap_fn() -> Box<dyn Fn() -> i32> {
    let x = 42;
    Box::new(move || x)
}

fn benchmark(c: &mut Criterion) {
    c.bench_function("stack_closure_creation", |b| {
        b.iter(|| black_box(stack_fn()))
    });
    
    c.bench_function("heap_closure_creation", |b| {
        b.iter(|| black_box(heap_fn()))
    });
}

criterion_group!(benches, benchmark);
criterion_main!(benches);
```

**Expected results:** Stack allocation is ~50x faster (0.5ns vs 25ns on modern hardware).

---

## 3. Capture Analysis & Borrow Checker Integration

### Precise Capture Analysis

```rust
// src/bin/precise_capture.rs

struct Container {
    field1: String,
    field2: i32,
    field3: Vec<u8>,
}

fn demonstrate_precision() {
    let mut c = Container {
        field1: String::from("hello"),
        field2: 42,
        field3: vec![1, 2, 3],
    };
    
    // IMPORTANT: Rust captures at FIELD level, not struct level
    let closure1 = || {
        println!("{}", c.field1);  // Only captures &field1
    };
    
    // This works! We can still use field2 and field3
    c.field2 += 1;
    c.field3.push(4);
    
    closure1();
    
    // But this won't work:
    // c.field1.push_str("world");  // ❌ field1 is borrowed
}

fn main() {
    demonstrate_precision();
}
```

**Hidden Knowledge #3:** Rust's capture analysis happens at the *field* level, not the struct level. This is called "capture disjoint fields" and was improved in Rust 2021 edition.

### Edition Differences: 2018 vs 2021

```rust
// src/bin/edition_capture.rs

// Rust 2018 behavior:
#[allow(unused)]
fn rust_2018_style() {
    let mut data = (String::from("a"), String::from("b"));
    
    // In 2018: captures entire `data` tuple
    let closure = || {
        println!("{}", data.0);
    };
    
    // ❌ Would fail in 2018:
    // let x = data.1;
}

// Rust 2021 behavior:
#[allow(unused)]
fn rust_2021_style() {
    let mut data = (String::from("a"), String::from("b"));
    
    // In 2021: captures only `data.0`
    let closure = || {
        println!("{}", data.0);
    };
    
    // ✅ Works in 2021:
    let x = data.1;
    drop(x);
    
    closure();
}

fn main() {
    rust_2021_style();
}
```

### Move Semantics Deep Dive

```rust
// src/bin/move_semantics.rs

fn move_analysis() {
    let s1 = String::from("copy");
    let s2 = String::from("move");
    let n = 42i32;
    
    let closure = move || {
        // What gets moved?
        println!("{}", s1);  // String moved (not Copy)
        println!("{}", s2);  // String moved (not Copy)
        println!("{}", n);   // i32 copied (Copy trait)
    };
    
    // ❌ s1 and s2 are moved
    // println!("{}", s1);
    
    // ✅ n is still accessible (was copied)
    println!("{}", n);
    
    closure();
}

// Selective moving with explicit captures
fn selective_move() {
    let s1 = String::from("keep");
    let s2 = String::from("move");
    
    // Trick: create a scope to move only s2
    let s2_moved = s2;  // Explicit move
    let closure = move || {
        // Only s2_moved is in scope to be moved
        println!("{}", s2_moved);
    };
    
    // s1 is still accessible
    println!("{}", s1);
    
    closure();
}

fn main() {
    move_analysis();
    selective_move();
}
```

**Hidden Knowledge #4:** `move` doesn't actually "move everything" - it copies Copy types and moves non-Copy types. You can control what gets captured by controlling what's in scope.

---

## 4. Fn/FnMut/FnOnce: The Complete Picture

### Trait Definitions (Actual Source)

```rust
// From std::ops

pub trait FnOnce<Args> {
    type Output;
    extern "rust-call" fn call_once(self, args: Args) -> Self::Output;
}

pub trait FnMut<Args>: FnOnce<Args> {
    extern "rust-call" fn call_mut(&mut self, args: Args) -> Self::Output;
}

pub trait Fn<Args>: FnMut<Args> {
    extern "rust-call" fn call(&self, args: Args) -> Self::Output;
}
```

### Why Three Traits? The Design Rationale

```rust
// src/bin/trait_rationale.rs

// Scenario 1: Fn - Read-only, can be called concurrently
fn can_call_concurrently<F: Fn()>(f: &F) {
    use std::thread;
    
    let handles: Vec<_> = (0..4)
        .map(|_| {
            thread::spawn(|| {
                f();  // Multiple threads call same closure
            })
        })
        .collect();
    
    for h in handles {
        h.join().unwrap();
    }
}

// Scenario 2: FnMut - Needs exclusive access
fn needs_exclusive_access<F: FnMut()>(f: &mut F) {
    f();  // Only one caller at a time
    f();
}

// Scenario 3: FnOnce - Consumes resources
fn consumes_closure<F: FnOnce()>(f: F) {
    f();  // Closure is consumed
    // Can't call f() again
}

fn main() {
    let x = 5;
    
    // Fn example
    let read_only = || println!("{}", x);
    can_call_concurrently(&read_only);
    
    // FnMut example
    let mut count = 0;
    let mut incrementer = || count += 1;
    needs_exclusive_access(&mut incrementer);
    
    // FnOnce example
    let owned = String::from("data");
    let consumer = || drop(owned);
    consumes_closure(consumer);
}
```

### Automatic Trait Implementation

```rust
// src/bin/auto_trait_impl.rs

fn demonstrate_auto_impl() {
    // Case 1: Implements Fn + FnMut + FnOnce
    let x = 5;
    let fn_closure = || x + 1;
    
    // Can use as any trait
    call_fn(&fn_closure);
    call_fn_mut(&mut fn_closure.clone());
    call_fn_once(fn_closure);
    
    // Case 2: Implements FnMut + FnOnce (but NOT Fn)
    let mut y = 10;
    let mut fn_mut_closure = || {
        y += 1;
        y
    };
    
    // call_fn(&fn_mut_closure);  // ❌ Doesn't implement Fn
    call_fn_mut(&mut fn_mut_closure);
    call_fn_once(fn_mut_closure);
    
    // Case 3: Implements ONLY FnOnce
    let s = String::from("owned");
    let fn_once_closure = || drop(s);
    
    // call_fn(&fn_once_closure);      // ❌
    // call_fn_mut(&mut fn_once_closure);  // ❌
    call_fn_once(fn_once_closure);
}

fn call_fn<F: Fn() -> i32>(f: &F) -> i32 { f() }
fn call_fn_mut<F: FnMut() -> i32>(f: &mut F) -> i32 { f() }
fn call_fn_once<F: FnOnce() -> i32>(f: F) -> i32 { f() }

fn main() {
    demonstrate_auto_impl();
}
```

### The `move` Keyword's Effect on Traits

```rust
// src/bin/move_trait_interaction.rs

fn trait_with_move() {
    let mut x = 5;
    
    // Without move: borrows &mut x, implements FnMut
    let mut closure1 = || {
        x += 1;
        x
    };
    
    println!("{}", closure1());  // FnMut
    println!("{}", x);  // x still accessible
    
    // With move: owns x, still implements FnMut!
    let mut y = 5;
    let mut closure2 = move || {
        y += 1;
        y
    };
    
    println!("{}", closure2());  // Still FnMut because it mutates
    // println!("{}", y);  // ❌ y was moved
}

fn main() {
    trait_with_move();
}
```

**Hidden Knowledge #5:** `move` doesn't change which Fn* trait is implemented - it only changes ownership. A closure that mutates a moved value is still `FnMut`, not `Fn`.

---

## 5. Advanced Lifetime Interactions

### HRTB (Higher-Rank Trait Bounds) with Closures

```rust
// src/bin/hrtb_closures.rs

// This is the HRTB syntax: for<'a>
fn apply_to_any_lifetime<F>(f: F)
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    let s1 = String::from("hello");
    let result1 = f(&s1);
    println!("{}", result1);
    
    let s2 = String::from("world");
    let result2 = f(&s2);
    println!("{}", result2);
}

fn main() {
    // This closure works for ANY lifetime
    let uppercase = |s: &str| -> &str {
        // Can't actually return modified &str without allocation
        // This is a limitation - showing the concept
        s
    };
    
    apply_to_any_lifetime(uppercase);
}

// Real-world HRTB example: Iterator transformations
fn demonstrate_real_hrtb() {
    let data = vec!["a", "b", "c"];
    
    // This works because the closure is valid for any lifetime
    let transformed: Vec<_> = data
        .iter()
        .map(|s: &&str| s.to_uppercase())
        .collect();
    
    println!("{:?}", transformed);
}
```

### Lifetime Elision in Closures

```rust
// src/bin/lifetime_elision.rs

// Explicit lifetimes
fn explicit_lifetime<'a, F>(data: &'a str, f: F) -> &'a str
where
    F: Fn(&'a str) -> &'a str,
{
    f(data)
}

// Lifetime elision (compiler infers)
fn elided_lifetime<F>(data: &str, f: F) -> &str
where
    F: for<'a> Fn(&'a str) -> &'a str,
{
    f(data)
}

fn main() {
    let text = String::from("hello");
    
    let result = explicit_lifetime(&text, |s| {
        // Lifetime 'a is tied to `text`
        &s[0..2]
    });
    
    println!("{}", result);
}
```

### Capturing References with Different Lifetimes

```rust
// src/bin/multi_lifetime_capture.rs

fn complex_lifetimes<'a, 'b>(s1: &'a str, s2: &'b str) -> impl Fn() + 'a
where
    'b: 'a,  // 'b must outlive 'a
{
    move || {
        println!("{} {}", s1, s2);
    }
}

// The closure's lifetime is tied to the shortest input lifetime
fn main() {
    let long_lived = String::from("long");
    
    {
        let short_lived = String::from("short");
        let closure = complex_lifetimes(&long_lived, &short_lived);
        closure();
        // closure's lifetime ends here with short_lived
    }
    
    // Can't use closure here - it's tied to short_lived's lifetime
}
```

**Hidden Knowledge #6:** When a closure captures multiple references with different lifetimes, its own lifetime is bounded by the *shortest* lifetime it captures.

---

## 6. Hidden Knowledge & Edge Cases

### Edge Case 1: Closure Type Uniqueness

```rust
// src/bin/unique_types.rs

fn closure_types() {
    let c1 = || println!("hello");
    let c2 = || println!("hello");
    
    // Even though they're identical, they have DIFFERENT types!
    // let v: Vec<_> = vec![c1, c2];  // ❌ Type mismatch
    
    // Solution: use trait objects
    let v: Vec<Box<dyn Fn()>> = vec![Box::new(c1), Box::new(c2)];
    
    for f in v {
        f();
    }
}

fn main() {
    closure_types();
}
```

**Hidden Knowledge #7:** Every closure literal has a unique, anonymous type. Even identical closures are different types.

### Edge Case 2: Closure Size Optimization

```rust
// src/bin/size_optimization.rs
use std::mem;

fn size_optimization() {
    // Empty closure - optimized to zero bytes!
    let empty = || println!("static");
    println!("Empty closure size: {}", mem::size_of_val(&empty));
    
    // Closure capturing ZST (Zero-Sized Type)
    struct ZST;
    let zst = ZST;
    let zst_closure = || {
        let _ = zst;
    };
    println!("ZST closure size: {}", mem::size_of_val(&zst_closure));
    
    // Both are 0 bytes!
}

fn main() {
    size_optimization();
}
```

**Hidden Knowledge #8:** Closures that capture only ZSTs (zero-sized types) or nothing at all are themselves ZSTs. They have zero runtime cost.

### Edge Case 3: Recursive Closures

```rust
// src/bin/recursive_closure.rs
use std::rc::Rc;
use std::cell::RefCell;

fn recursive_closure() {
    // Can't do: let fib = |n| if n < 2 { n } else { fib(n-1) + fib(n-2) };
    // Because fib doesn't exist yet when defining the closure!
    
    // Solution: Use Rc + RefCell
    let fib: Rc<RefCell<Option<Box<dyn Fn(u32) -> u32>>>> = 
        Rc::new(RefCell::new(None));
    
    let fib_clone = fib.clone();
    *fib.borrow_mut() = Some(Box::new(move |n| {
        if n < 2 {
            n
        } else {
            let fib_inner = fib_clone.borrow();
            let f = fib_inner.as_ref().unwrap();
            f(n - 1) + f(n - 2)
        }
    }));
    
    let result = fib.borrow().as_ref().unwrap()(10);
    println!("Fibonacci(10) = {}", result);
}

// Better solution: use Y-combinator pattern
fn y_combinator<F, T>(f: F) -> impl Fn(T) -> T
where
    F: Fn(&dyn Fn(T) -> T, T) -> T,
    T: 'static,
{
    move |x| f(&|y| y_combinator(&f)(y), x)
}

fn main() {
    recursive_closure();
    
    // Y-combinator example
    let fib = y_combinator(|fib, n: u32| {
        if n < 2 { n } else { fib(n - 1) + fib(n - 2) }
    });
    
    println!("Fib(10) = {}", fib(10));
}
```

### Edge Case 4: Closure Coercion Rules

```rust
// src/bin/coercion_rules.rs

fn coercion_examples() {
    // Non-capturing closure → fn pointer
    let add = |x: i32, y: i32| x + y;
    let fn_ptr: fn(i32, i32) -> i32 = add;  // ✅ Coercion works
    
    // Capturing closure → CANNOT coerce to fn pointer
    let z = 5;
    let add_z = |x: i32| x + z;
    // let bad: fn(i32) -> i32 = add_z;  // ❌ Doesn't compile
    
    // But CAN coerce to trait object
    let good: &dyn Fn(i32) -> i32 = &add_z;  // ✅ Works
    
    // Fn → FnMut → FnOnce (always works)
    fn takes_fn_once<F: FnOnce()>(f: F) { f(); }
    fn takes_fn_mut<F: FnMut()>(mut f: F) { f(); }
    fn takes_fn<F: Fn()>(f: F) { f(); }
    
    let closure = || println!("test");
    takes_fn_once(closure);  // ✅
    takes_fn_mut(closure);   // ✅
    takes_fn(closure);       // ✅
}

fn main() {
    coercion_examples();
}
```

---

## 7. Real-World Production Patterns

### Pattern 1: Transactional Database Wrapper

```rust
// src/bin/transaction_pattern.rs
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

type Result<T> = std::result::Result<T, String>;

struct Database {
    data: Arc<Mutex<HashMap<String, String>>>,
}

impl Database {
    fn new() -> Self {
        Self {
            data: Arc::new(Mutex::new(HashMap::new())),
        }
    }
    
    // Execute operation in transaction with automatic rollback
    fn transaction<F, T>(&self, operation: F) -> Result<T>
    where
        F: FnOnce(&mut Transaction) -> Result<T>,
    {
        let mut snapshot = self.data.lock().unwrap().clone();
        let mut tx = Transaction {
            data: &mut snapshot,
            committed: false,
        };
        
        match operation(&mut tx) {
            Ok(result) => {
                if tx.committed {
                    *self.data.lock().unwrap() = snapshot;
                    Ok(result)
                } else {
                    Err("Transaction not committed".into())
                }
            }
            Err(e) => {
                // Automatic rollback - snapshot is dropped
                Err(e)
            }
        }
    }
}

struct Transaction<'a> {
    data: &'a mut HashMap<String, String>,
    committed: bool,
}

impl<'a> Transaction<'a> {
    fn set(&mut self, key: String, value: String) {
        self.data.insert(key, value);
    }
    
    fn get(&self, key: &str) -> Option<&String> {
        self.data.get(key)
    }
    
    fn commit(&mut self) {
        self.committed = true;
    }
}

fn main() {
    let db = Database::new();
    
    // Successful transaction
    let result = db.transaction(|tx| {
        tx.set("user:1".into(), "Alice".into());
        tx.set("user:2".into(), "Bob".into());
        tx.commit();
        Ok(())
    });
    println!("Transaction 1: {:?}", result);
    
    // Failed transaction (automatic rollback)
    let result = db.transaction(|tx| {
        tx.set("user:3".into(), "Charlie".into());
        // Simulate error - no commit
        Err("Validation failed".into())
    });
    println!("Transaction 2: {:?}", result);
    
    // Verify: user:3 should not exist
    db.transaction(|tx| {
        println!("user:1 = {:?}", tx.get("user:1"));
        println!("user:3 = {:?}", tx.get("user:3"));
        tx.commit();
        Ok(())
    }).unwrap();
}
```

### Pattern 2: Lazy Evaluation with Memoization

```rust
// src/bin/lazy_memo.rs
use std::cell::RefCell;
use std::collections::HashMap;
use std::hash::Hash;
use std::rc::Rc;

struct Lazy<T, F>
where
    F: FnOnce() -> T,
{
    value: RefCell<Option<T>>,
    init: RefCell<Option<F>>,
}

impl<T, F> Lazy<T, F>
where
    F: FnOnce() -> T,
{
    fn new(init: F) -> Self {
        Self {
            value: RefCell::new(None),
            init: RefCell::new(Some(init)),
        }
    }
    
    fn get(&self) -> std::cell::Ref<T> {
        if self.value.borrow().is_none() {
            let init = self.init.borrow_mut().take().unwrap();
            *self.value.borrow_mut() = Some(init());
        }
        
        std::cell::Ref::map(self.value.borrow(), |opt| opt.as_ref().unwrap())
    }
}

// Memoized function
struct Memoized<A, R, F>
where
    A: Eq + Hash + Clone,
    R: Clone,
    F: FnMut(A) -> R,
{
    cache: Rc<RefCell<HashMap<A, R>>>,
    func: Rc<RefCell<F>>,
}

impl<A, R, F> Memoized<A, R, F>
where
    A: Eq + Hash + Clone,
    R: Clone,
    F: FnMut(A) -> R,
{
    fn new(func: F) -> Self {
        Self {
            cache: Rc::new(RefCell::new(HashMap::new())),
            func: Rc::new(RefCell::new(func)),
        }
    }
    
    fn call(&self, arg: A) -> R {
        let mut cache = self.cache.borrow_mut();
        
        if let Some(result) = cache.get(&arg) {
            return result.clone();
        }
        
        let result = self.func.borrow_mut()(arg.clone());
        cache.insert(arg, result.clone());
        result
    }
}

fn main() {
    // Lazy example
    let expensive = Lazy::new(|| {
        println!("Computing expensive value...");
        42
    });
    
    println!("Lazy created");
    println!("Value: {}", *expensive.get());  // Prints "Computing..."
    println!("Value: {}", *expensive.get());  // Doesn't print (cached)
    
    // Memoized example
    let mut call_count = 0;
    let memo = Memoized::new(|x: i32| {
        call_count += 1;
        println!("Computing for {}", x);
        x * x
    });
    
    println!("{}", memo.call(5));  // Computes
    println!("{}", memo.call(5));  // Cached
    println!("{}", memo.call(3));  // Computes
}
```

### Pattern 3: Continuation-Passing Style (CPS)

```rust
// src/bin/cps_pattern.rs

// Traditional style
fn add_traditional(a: i32, b: i32) -> i32 {
    a + b
}

// CPS style - pass continuation (what to do with result)
fn add_cps<F>(a: i32, b: i32, cont: F)
where
    F: FnOnce(i32),
{
    cont(a + b)
}

// Complex computation with CPS
fn compute_cps<F>(x: i32, cont: F)
where
    F: FnOnce(i32),
{
    add_cps(x, 10, |result1| {
        add_cps(result1, 20, |result2| {
            add_cps(result2, 30, cont)
        })
    })
}

// Async-like pattern with CPS
struct AsyncTask<T> {
    executor: Box<dyn FnOnce(Box<dyn FnOnce(T)>)>,
}

impl<T: 'static> AsyncTask<T> {
    fn new<F>(f: F) -> Self
    where
        F: FnOnce(Box<dyn FnOnce(T)>) + 'static,
    {
        Self {
            executor: Box::new(f),
        }
    }
    
    fn then<U, F>(self, callback: F) -> AsyncTask<U>
    where
        F: FnOnce(T) -> U + 'static,
        U: 'static,
    {
        AsyncTask::new(move |cont| {
            (self.executor)(Box::new(move |result| {
                let next_result = callback(result);
                cont(next_result);
            }))
        })
    }
    
    fn run<F>(self, callback: F)
    where
        F: FnOnce(T) + 'static,
    {
        (self.executor)(Box::new(callback))
    }
}

fn main() {
    // CPS example
    compute_cps(5, |result| {
        println!("Result: {}", result);  // 65
    });
    
    // AsyncTask example
    let task = AsyncTask::new(|cont| {
        println!("Starting task");
        cont(42)
    });
    
    task.then(|x| {
        println!("First then: {}", x);
        x * 2
    })
    .then(|x| {
        println!("Second then: {}", x);
        x + 10
    })
    .run(|final_result| {
        println!("Final result: {}", final_result);
    });
}
```

### Pattern 4: State Machine with Closures

```rust
// src/bin/state_machine.rs
use std::collections::VecDeque;

type StateTransition<S> = Box<dyn FnOnce(&mut S) -> Option<Box<dyn FnOnce(&mut S) -> Option<StateTransition<S>>>>>;

struct StateMachine<S> {
    state: S,
    queue: VecDeque<StateTransition<S>>,
}

impl<S> StateMachine<S> {
    fn new(initial_state: S) -> Self {
        Self {
            state: initial_state,
            queue: VecDeque::new(),
        }
    }
    
    fn enqueue(&mut self, transition: StateTransition<S>) {
        self.queue.push_back(transition);
    }
    
    fn run(&mut self) {
        while let Some(transition) = self.queue.pop_front() {
            if let Some(next_transition) = transition(&mut self.state) {
                self.queue.push_front(next_transition);
            }
        }
    }
}

// Example: Traffic light
#[derive(Debug, Clone, Copy, PartialEq)]
enum Light {
    Red,
    Yellow,
    Green,
}

fn main() {
    let mut fsm = StateMachine::new(Light::Red);
    
    // Define transitions
    fsm.enqueue(Box::new(|state| {
        println!("State: {:?}", state);
        *state = Light::Green;
        Some(Box::new(|state| {
            println!("State: {:?}", state);
            *state = Light::Yellow;
            Some(Box::new(|state| {
                println!("State: {:?}", state);
                *state = Light::Red;
                None
            }))
        }))
    }));
    
    fsm.run();
}
```

---

## 8. Performance Engineering

### Benchmark Suite

```rust
// benches/comprehensive_bench.rs
use criterion::{black_box, criterion_group, criterion_main, Criterion, BenchmarkId};
use std::hint::black_box as bb;

// Different closure strategies
fn direct_call(n: i32) -> i32 {
    n * 2 + 1
}

fn with_fn_trait<F: Fn(i32) -> i32>(n: i32, f: F) -> i32 {
    f(n)
}

fn with_boxed_fn(n: i32, f: &Box<dyn Fn(i32) -> i32>) -> i32 {
    f(n)
}

fn benchmark_strategies(c: &mut Criterion) {
    let mut group = c.benchmark_group("closure_strategies");
    
    for size in [1, 10, 100, 1000].iter() {
        group.bench_with_input(BenchmarkId::new("direct", size), size, |b, &size| {
            b.iter(|| {
                (0..size).map(|n| direct_call(bb(n))).sum::<i32>()
            });
        });
        
        group.bench_with_input(BenchmarkId::new("closure_inline", size), size, |b, &size| {
            b.iter(|| {
                (0..size).map(|n| with_fn_trait(bb(n), |x| x * 2 + 1)).sum::<i32>()
            });
        });
        
        group.bench_with_input(BenchmarkId::new("boxed", size), size, |b, &size| {
            let f: Box<dyn Fn(i32) -> i32> = Box::new(|x| x * 2 + 1);
            b.iter(|| {
                (0..size).map(|n| with_boxed_fn(bb(n), &f)).sum::<i32>()
            });
        });
    }
    
    group.finish();
}

criterion_group!(benches, benchmark_strategies);
criterion_main!(benches);
```

### Memory Profiling with DHAT

```rust
// src/bin/memory_profile.rs
#[global_allocator]
static ALLOC: dhat::Alloc = dhat::Alloc;

fn allocating_closures() {
    let _profiler = dhat::Profiler::new_heap();
    
    // Stack allocation
    let stack_closures: Vec<_> = (0..1000)
        .map(|i| move || i * 2)
        .collect();
    
    // Heap allocation
    let heap_closures: Vec<Box<dyn Fn() -> i32>> = (0..1000)
        .map(|i| Box::new(move || i * 2) as Box<dyn Fn() -> i32>)
        .collect();
    
    // Execute
    for c in &stack_closures {
        std::hint::black_box(c());
    }
    
    for c in &heap_closures {
        std::hint::black_box(c());
    }
}

fn main() {
    allocating_closures();
}
```

**Run:**
```bash
cargo add dhat
cargo run --release --bin memory_profile
# Check dhat-heap.json
```

### Inlining Analysis

```rust
// src/bin/inline_analysis.rs

#[inline(always)]
fn always_inline<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}

#[inline(never)]
fn never_inline<F: Fn(i32) -> i32>(f: F, x: i32) -> i32 {
    f(x)
}

pub fn test_inlining() {
    let closure = |x: i32| x * 2;
    
    // Will be inlined
    let result1 = always_inline(closure, 42);
    
    // Won't be inlined
    let result2 = never_inline(closure, 42);
    
    println!("{} {}", result1, result2);
}

fn main() {
    test_inlining();
}
```

**Check assembly:**
```bash
cargo rustc --release --bin inline_analysis -- --emit asm
cat target/release/deps/inline_analysis-*.s | grep -A 30 "test_inlining"
```

---

## 9. Unsafe & FFI with Closures

### Calling C from Rust with Closures

```rust
// src/bin/ffi_callbacks.rs
use std::os::raw::{c_int, c_void};

// C signature: void qsort(void *base, size_t nel, size_t width,
//                         int (*compar)(const void *, const void *));
extern "C" {
    fn qsort(
        base: *mut c_void,
        nel: usize,
        width: usize,
        compar: extern "C" fn(*const c_void, *const c_void) -> c_int,
    );
}

// Trampoline function - bridge between Rust closure and C function pointer
extern "C" fn compare_wrapper(a: *const c_void, b: *const c_void) -> c_int {
    unsafe {
        let a = *(a as *const i32);
        let b = *(b as *const i32);
        a.cmp(&b) as c_int
    }
}

fn main() {
    let mut array = [5, 2, 8, 1, 9];
    
    unsafe {
        qsort(
            array.as_mut_ptr() as *mut c_void,
            array.len(),
            std::mem::size_of::<i32>(),
            compare_wrapper,
        );
    }
    
    println!("Sorted: {:?}", array);
}

// For closures with state, we need a different approach
unsafe extern "C" fn trampoline<F>(a: *const c_void, b: *const c_void, ctx: *mut c_void) -> c_int
where
    F: FnMut(*const c_void, *const c_void) -> c_int,
{
    let closure: &mut F = &mut *(ctx as *mut F);
    closure(a, b)
}

// This won't work with standard qsort, but shows the pattern for C APIs
// that accept a void* context parameter
```

### Unsafe Closure Shenanigans

```rust
// src/bin/unsafe_closures.rs
use std::mem;

fn dangerous_closure_manipulation() {
    let x = 42;
    let closure = || x + 1;
    
    // ⚠️ UNSAFE: Transmuting closure to raw bytes
    let closure_bytes: [u8; mem::size_of_val(&closure)] = unsafe {
        mem::transmute_copy(&closure)
    };
    
    println!("Closure as bytes: {:?}", closure_bytes);
    
    // ⚠️ EXTREMELY UNSAFE: Reconstructing closure from bytes
    let reconstructed: fn() -> i32 = unsafe {
        mem::transmute_copy(&closure_bytes)
    };
    
    // This might work, might segfault, might summon demons
    // DON'T DO THIS IN PRODUCTION
    println!("Reconstructed result: {}", reconstructed());
}

// Practical use case: Storing closure in C-compatible struct
#[repr(C)]
struct CallbackHolder {
    func: extern "C" fn(*mut u8),
    data: *mut u8,
}

impl CallbackHolder {
    fn new<F>(mut closure: F) -> Self
    where
        F: FnMut() + 'static,
    {
        extern "C" fn call_closure<F: FnMut()>(data: *mut u8) {
            unsafe {
                let closure = &mut *(data as *mut F);
                closure();
            }
        }
        
        let boxed = Box::new(closure);
        let data = Box::into_raw(boxed) as *mut u8;
        
        Self {
            func: call_closure::<F>,
            data,
        }
    }
    
    fn call(&self) {
        (self.func)(self.data);
    }
}

impl Drop for CallbackHolder {
    fn drop(&mut self) {
        unsafe {
            // Reconstruct Box to properly drop
            let _ = Box::from_raw(self.data);
        }
    }
}

fn main() {
    dangerous_closure_manipulation();
    
    let mut count = 0;
    let holder = CallbackHolder::new(move || {
        count += 1;
        println!("Called {} times", count);
    });
    
    holder.call();
    holder.call();
}
```

**Hidden Knowledge #9:** Closures can be transmuted and manipulated with unsafe, but their memory layout is compiler-specific and unstable. Only do this when interfacing with C APIs that require it.

---

## 10. Exercises

### Exercise 1: Thread Pool with Work-Stealing

**Goal:** Implement a thread pool that accepts closures, with work-stealing between threads.

**Requirements:**
```rust
let pool = ThreadPool::new(4);
pool.execute(|| println!("Task 1"));
pool.execute(|| println!("Task 2"));
pool.join();  // Wait for all tasks
```

**Hints:**
- Use `crossbeam::deque::Worker` and `Stealer`
- Store `Box<dyn FnOnce() + Send>`
- Handle thread panics gracefully

**Advanced:** Add priority queues and task dependencies.

---

### Exercise 2: Reactive Programming Library

**Goal:** Build a simple reactive system where values automatically update when dependencies change.

**API:**
```rust
let mut x = Signal::new(5);
let mut y = Signal::new(10);
let sum = computed(move || x.get() + y.get());

println!("{}", sum.get());  // 15
x.set(20);
println!("{}", sum.get());  // 30 (automatically recomputed)
```

**Hints:**
- Use `Rc<RefCell<>>` for shared ownership
- Track dependencies in a graph
- Implement a dirty-checking mechanism

---

### Exercise 3: Query Builder DSL

**Goal:** Create a type-safe SQL query builder using closures.

**API:**
```rust
let query = Query::table("users")
    .select(|u| (u.name, u.email))
    .where_(|u| u.age.gt(18))
    .order_by(|u| u.created_at.desc())
    .build();

println!("{}", query);  // SELECT name, email FROM users WHERE age > 18 ORDER BY created_at DESC
```

**Hints:**
- Use phantom types for compile-time SQL safety
- Closures capture column references
- Builder pattern with method chaining

---

## Production Security Checklist

- [ ] **Panic safety:** All closures used in critical paths handle panics
- [ ] **Send/Sync bounds:** Verified for multi-threaded closures
- [ ] **Lifetime auditing:** No dangling references possible
- [ ] **Memory leaks:** Checked for cycles with Rc<RefCell<Closure>>
- [ ] **FFI safety:** All C callbacks use proper trampolines
- [ ] **Type confusion:** Explicit trait objects instead of `impl Trait` in public APIs
- [ ] **Capture validation:** Sensitive data not accidentally captured
- [ ] **Clone implications:** Understand if captured data is cloned or moved

---

## Complete Project Structure

```
advanced-closures-deep/
├── Cargo.toml
├── src/
│   ├── lib.rs
│   └── bin/
│       ├── desugaring.rs
│       ├── memory_layout.rs
│       ├── capture_modes.rs
│       ├── hrtb_closures.rs
│       ├── recursive_closure.rs
│       ├── transaction_pattern.rs
│       ├── lazy_memo.rs
│       ├── cps_pattern.rs
│       ├── state_machine.rs
│       ├── ffi_callbacks.rs
│       └── unsafe_closures.rs
├── benches/
│   ├── closure_bench.rs
│   ├── allocation_bench.rs
│   └── comprehensive_bench.rs
└── tests/
    └── integration.rs
```

---

## Further Reading (Advanced)

**Deep Dives:**
1. [RFC 2229: Disjoint Capture in Closures](https://rust-lang.github.io/rfcs/2229-capture-disjoint-fields.html)
2. [MIR-level closure analysis](https://blog.rust-lang.org/2016/04/19/MIR.html)
3. Jon Gjengset's "Crust of Rust: Iterators" - closure internals

**Advanced Books:**
1. *Rust for Rustaceans* - Chapter on advanced traits
2. *Programming Rust* 2nd ed - Closure implementation details

**Source Code Study:**
1. `std::iter` - Iterator adapters using closures
2. `tokio::spawn` - Closure constraints for async
3. `rayon::scope` - Scoped thread spawning with closures

---

## Final Hidden Knowledge Dump

**#10:** Closures in `const fn` are experimental but coming. You'll be able to use closures at compile time.

**#11:** The `move` keyword can be used with `async` blocks, which are essentially closures that return `Future`.

**#12:** Closures implement `Copy` if all captured variables implement `Copy`. This is rare but powerful.

**#13:** You can force a closure to be `FnOnce` by consuming a captured non-Copy value, even if you don't actually need to.

**#14:** The compiler can sometimes optimize away closure allocations even when using `Box<dyn Fn>` through devirtualization.

**#15:** Closures' trait implementations are "sealed" - you can't manually implement Fn* traits for your own types (except through nightly features).

---

**Your Next Challenge:**

1. Implement all 3 exercises above
2. Profile them with criterion + dhat
3. Write a blog post explaining one edge case
4. Read the MIR output for a complex closure: `cargo rustc -- -Z dump-mir=all`

You now understand closures at the level of a Rust compiler contributor. Use this power wisely.