# Transfer Data Between Threads with Message Passing in Rust

Message passing is Rust's primary mechanism for safe concurrent communication, following the mantra: **"Do not communicate by sharing memory; instead, share memory by communicating."**

## Core Concepts

### Why Message Passing?

Message passing eliminates data races by ensuring only one thread owns data at a time. When you send data through a channel, ownership transfers to the receiving thread.

```rust
use std::sync::mpsc;
use std::thread;

fn main() {
    let (tx, rx) = mpsc::channel();
    
    thread::spawn(move || {
        let val = String::from("hello");
        tx.send(val).unwrap();
        // val is moved - can't use it here anymore
    });
    
    let received = rx.recv().unwrap();
    println!("Got: {}", received);
}
```

---

## 1. Standard Library Channels (`std::sync::mpsc`)

### MPSC: Multiple Producer, Single Consumer

The standard library provides **`mpsc`** (multiple producer, single consumer) channels.

```rust
use std::sync::mpsc;
use std::thread;
use std::time::Duration;

fn basic_channel_demo() {
    // Create a channel
    let (tx, rx) = mpsc::channel::<String>();
    
    // Spawn sender thread
    thread::spawn(move || {
        let messages = vec![
            "thread".to_string(),
            "message".to_string(),
            "passing".to_string(),
        ];
        
        for msg in messages {
            tx.send(msg).unwrap();
            thread::sleep(Duration::from_millis(100));
        }
    });
    
    // Receive in main thread
    for received in rx {
        println!("Received: {}", received);
    }
}
```

### Channel Semantics

**Unbounded vs Bounded:**

```rust
use std::sync::mpsc;

fn channel_types() {
    // Unbounded - can grow infinitely
    let (tx, rx) = mpsc::channel::<i32>();
    
    // Sync channel - bounded buffer
    let (tx_sync, rx_sync) = mpsc::sync_channel::<i32>(5);
    
    // sync_channel blocks sender when buffer is full
    for i in 0..10 {
        tx_sync.send(i).unwrap(); // Will block after 5 sends
    }
}
```

---

## 2. Multiple Producers

Clone the sender to create multiple producers:

```rust
use std::sync::mpsc;
use std::thread;

fn multiple_producers() {
    let (tx, rx) = mpsc::channel();
    
    // Clone sender for multiple threads
    let tx1 = tx.clone();
    let tx2 = tx.clone();
    
    thread::spawn(move || {
        tx1.send("from thread 1").unwrap();
    });
    
    thread::spawn(move || {
        tx2.send("from thread 2").unwrap();
    });
    
    // Drop original sender so rx knows when all senders are done
    drop(tx);
    
    // Receive from both senders
    for msg in rx {
        println!("{}", msg);
    }
}
```

**Key insight:** The receiver will continue blocking until ALL senders are dropped.

---

## 3. Error Handling

### Send Errors

```rust
use std::sync::mpsc::{self, SendError};
use std::thread;

fn send_error_handling() {
    let (tx, rx) = mpsc::channel::<i32>();
    
    // Drop receiver
    drop(rx);
    
    // Send will fail
    match tx.send(42) {
        Ok(_) => println!("Sent successfully"),
        Err(SendError(value)) => {
            println!("Failed to send: {}", value);
            // You get ownership back!
        }
    }
}
```

### Receive Errors

```rust
use std::sync::mpsc::{self, RecvError, TryRecvError};
use std::time::Duration;

fn recv_error_handling() {
    let (tx, rx) = mpsc::channel::<i32>();
    
    // Blocking receive
    match rx.recv() {
        Ok(val) => println!("Got: {}", val),
        Err(RecvError) => println!("All senders disconnected"),
    }
    
    // Non-blocking receive
    match rx.try_recv() {
        Ok(val) => println!("Got: {}", val),
        Err(TryRecvError::Empty) => println!("No data available"),
        Err(TryRecvError::Disconnected) => println!("Senders gone"),
    }
    
    // Timeout receive
    match rx.recv_timeout(Duration::from_secs(1)) {
        Ok(val) => println!("Got: {}", val),
        Err(_) => println!("Timeout or disconnected"),
    }
}
```

---

## 4. Sending Complex Data

### Owned Types

```rust
use std::sync::mpsc;
use std::thread;

#[derive(Debug)]
struct Task {
    id: usize,
    payload: Vec<u8>,
}

fn send_complex_types() {
    let (tx, rx) = mpsc::channel::<Task>();
    
    thread::spawn(move || {
        let task = Task {
            id: 1,
            payload: vec![1, 2, 3, 4],
        };
        tx.send(task).unwrap();
        // task is moved, can't use it here
    });
    
    let task = rx.recv().unwrap();
    println!("Received task: {:?}", task);
}
```

### Cloneable Types

```rust
use std::sync::mpsc;
use std::thread;

fn send_cloneable() {
    let (tx, rx) = mpsc::channel::<String>();
    
    thread::spawn(move || {
        let msg = String::from("hello");
        // Clone if you need to keep it
        tx.send(msg.clone()).unwrap();
        println!("Still have: {}", msg);
    });
    
    println!("Received: {}", rx.recv().unwrap());
}
```

### Shared Data with Arc

When you need shared **read-only** access:

```rust
use std::sync::{mpsc, Arc};
use std::thread;

fn send_arc() {
    let (tx, rx) = mpsc::channel::<Arc<Vec<u8>>>();
    
    let data = Arc::new(vec![1, 2, 3, 4, 5]);
    
    // Multiple threads can share read-only access
    for _ in 0..3 {
        let tx = tx.clone();
        let data = Arc::clone(&data);
        
        thread::spawn(move || {
            tx.send(data).unwrap();
        });
    }
    
    drop(tx);
    
    for shared_data in rx {
        println!("Received Arc with {} bytes", shared_data.len());
    }
}
```

---

## 5. Advanced Patterns

### Worker Pool Pattern

```rust
use std::sync::mpsc;
use std::thread;

struct Job(Box<dyn FnOnce() + Send + 'static>);

fn worker_pool() {
    let (tx, rx) = mpsc::channel::<Job>();
    let num_workers = 4;
    
    // Create workers
    for id in 0..num_workers {
        let rx = rx.clone(); // Clone receiver... wait, this won't work!
        // MPSC only allows one receiver
    }
}
```

**Problem:** `mpsc` only supports one receiver. Solution: Use `crossbeam` or share the receiver.

### Request-Response Pattern

```rust
use std::sync::mpsc;
use std::thread;

type RequestId = usize;
type Response = String;

fn request_response_pattern() {
    let (req_tx, req_rx) = mpsc::channel::<(RequestId, mpsc::Sender<Response>)>();
    
    // Worker thread
    thread::spawn(move || {
        for (id, response_tx) in req_rx {
            let result = format!("Processed request {}", id);
            response_tx.send(result).unwrap();
        }
    });
    
    // Make request
    let (resp_tx, resp_rx) = mpsc::channel();
    req_tx.send((1, resp_tx)).unwrap();
    
    let response = resp_rx.recv().unwrap();
    println!("Got response: {}", response);
}
```

### Fan-out / Fan-in

```rust
use std::sync::mpsc;
use std::thread;

fn fan_out_fan_in() {
    let (work_tx, work_rx) = mpsc::channel::<i32>();
    let (result_tx, result_rx) = mpsc::channel::<i32>();
    
    // Fan-out: distribute work to multiple workers
    let num_workers = 4;
    for _ in 0..num_workers {
        let work_rx = work_rx.clone();
        let result_tx = result_tx.clone();
        
        thread::spawn(move || {
            // This won't work - can't clone receiver!
            // See crossbeam solution below
        });
    }
    
    // Send work
    for i in 0..100 {
        work_tx.send(i).unwrap();
    }
    drop(work_tx);
    
    // Fan-in: collect results
    drop(result_tx); // Drop original
    for result in result_rx {
        println!("Result: {}", result);
    }
}
```

---

## 6. Crossbeam Channels (Production-Ready Alternative)

`crossbeam-channel` provides more powerful primitives:

```toml
[dependencies]
crossbeam-channel = "0.5"
```

### MPMC: Multiple Producer, Multiple Consumer

```rust
use crossbeam_channel as channel;
use std::thread;
use std::time::Duration;

fn crossbeam_mpmc() {
    // Unbounded channel
    let (tx, rx) = channel::unbounded::<i32>();
    
    // Multiple senders
    for i in 0..3 {
        let tx = tx.clone();
        thread::spawn(move || {
            tx.send(i).unwrap();
        });
    }
    
    // Multiple receivers (worker pool)
    for worker_id in 0..2 {
        let rx = rx.clone();
        thread::spawn(move || {
            while let Ok(val) = rx.recv() {
                println!("Worker {} got: {}", worker_id, val);
            }
        });
    }
    
    drop(tx);
    drop(rx);
    thread::sleep(Duration::from_secs(1));
}
```

### Bounded Channels

```rust
use crossbeam_channel as channel;

fn crossbeam_bounded() {
    // Bounded channel with capacity 5
    let (tx, rx) = channel::bounded::<i32>(5);
    
    // Will block after 5 sends
    for i in 0..10 {
        println!("Sending {}", i);
        tx.send(i).unwrap(); // Blocks when full
        println!("Sent {}", i);
    }
}
```

### Select Operation

Handle multiple channels:

```rust
use crossbeam_channel as channel;
use std::time::Duration;

fn select_demo() {
    let (tx1, rx1) = channel::unbounded::<String>();
    let (tx2, rx2) = channel::unbounded::<String>();
    
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(100));
        tx1.send("from channel 1".to_string()).unwrap();
    });
    
    thread::spawn(move || {
        thread::sleep(Duration::from_millis(200));
        tx2.send("from channel 2".to_string()).unwrap();
    });
    
    // Select from multiple channels
    channel::select! {
        recv(rx1) -> msg => println!("rx1: {:?}", msg),
        recv(rx2) -> msg => println!("rx2: {:?}", msg),
    }
}
```

### Timeout and Non-blocking

```rust
use crossbeam_channel as channel;
use std::time::Duration;

fn timeouts_and_tries() {
    let (tx, rx) = channel::unbounded::<i32>();
    
    // Try receive (non-blocking)
    match rx.try_recv() {
        Ok(val) => println!("Got: {}", val),
        Err(channel::TryRecvError::Empty) => println!("Empty"),
        Err(channel::TryRecvError::Disconnected) => println!("Disconnected"),
    }
    
    // Receive with timeout
    match rx.recv_timeout(Duration::from_secs(1)) {
        Ok(val) => println!("Got: {}", val),
        Err(channel::RecvTimeoutError::Timeout) => println!("Timed out"),
        Err(channel::RecvTimeoutError::Disconnected) => println!("Disconnected"),
    }
}
```

---

## 7. Real-World Worker Pool Implementation

```rust
use crossbeam_channel as channel;
use std::thread;
use std::sync::Arc;

pub struct WorkerPool {
    workers: Vec<thread::JoinHandle<()>>,
    job_sender: channel::Sender<Job>,
}

type Job = Box<dyn FnOnce() + Send + 'static>;

impl WorkerPool {
    pub fn new(num_threads: usize) -> Self {
        let (job_sender, job_receiver) = channel::unbounded::<Job>();
        let job_receiver = Arc::new(job_receiver);
        
        let mut workers = Vec::with_capacity(num_threads);
        
        for id in 0..num_threads {
            let receiver = Arc::clone(&job_receiver);
            
            let handle = thread::spawn(move || {
                loop {
                    match receiver.recv() {
                        Ok(job) => {
                            println!("Worker {} executing job", id);
                            job();
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
        
        WorkerPool { workers, job_sender }
    }
    
    pub fn execute<F>(&self, job: F) 
    where
        F: FnOnce() + Send + 'static,
    {
        self.job_sender.send(Box::new(job)).unwrap();
    }
}

impl Drop for WorkerPool {
    fn drop(&mut self) {
        // Drop sender to signal workers to exit
        drop(self.job_sender.clone());
        
        // Wait for all workers
        for worker in self.workers.drain(..) {
            worker.join().unwrap();
        }
    }
}

// Usage
fn worker_pool_example() {
    let pool = WorkerPool::new(4);
    
    for i in 0..10 {
        pool.execute(move || {
            println!("Job {} running", i);
            thread::sleep(std::time::Duration::from_millis(100));
        });
    }
    
    // Pool automatically shuts down when dropped
}
```

---

## 8. Performance Considerations

### Batching Messages

```rust
use crossbeam_channel as channel;

fn batching_pattern() {
    let (tx, rx) = channel::unbounded::<Vec<i32>>();
    
    thread::spawn(move || {
        let mut batch = Vec::new();
        
        for i in 0..1000 {
            batch.push(i);
            
            if batch.len() >= 100 {
                tx.send(batch).unwrap();
                batch = Vec::new();
            }
        }
        
        if !batch.is_empty() {
            tx.send(batch).unwrap();
        }
    });
    
    for batch in rx {
        println!("Processing batch of {} items", batch.len());
    }
}
```

### Zero-Copy with Arc

```rust
use std::sync::Arc;
use crossbeam_channel as channel;

fn zero_copy_pattern() {
    let (tx, rx) = channel::unbounded::<Arc<Vec<u8>>>();
    
    // Producer creates large data once
    let large_data = Arc::new(vec![0u8; 1_000_000]);
    
    // Share with multiple consumers without copying
    for _ in 0..10 {
        tx.send(Arc::clone(&large_data)).unwrap();
    }
    
    drop(tx);
    
    for data in rx {
        // Each consumer gets cheap Arc clone
        println!("Processing {} bytes", data.len());
    }
}
```

---

## 9. Common Patterns and Idioms

### Shutdown Signal

```rust
use crossbeam_channel as channel;
use std::thread;
use std::time::Duration;

fn shutdown_signal_pattern() {
    let (shutdown_tx, shutdown_rx) = channel::bounded::<()>(0);
    let (work_tx, work_rx) = channel::unbounded::<i32>();
    
    let handle = thread::spawn(move || {
        loop {
            channel::select! {
                recv(work_rx) -> msg => {
                    if let Ok(val) = msg {
                        println!("Processing: {}", val);
                    }
                }
                recv(shutdown_rx) -> _ => {
                    println!("Shutting down gracefully");
                    break;
                }
            }
        }
    });
    
    // Send work
    for i in 0..5 {
        work_tx.send(i).unwrap();
    }
    
    thread::sleep(Duration::from_millis(100));
    
    // Signal shutdown
    drop(shutdown_tx);
    
    handle.join().unwrap();
}
```

### Rate Limiting

```rust
use crossbeam_channel as channel;
use std::time::{Duration, Instant};
use std::thread;

fn rate_limiter() {
    let (tx, rx) = channel::unbounded::<i32>();
    
    thread::spawn(move || {
        let rate_limit = Duration::from_millis(100);
        let mut last_sent = Instant::now();
        
        for i in 0..100 {
            let elapsed = last_sent.elapsed();
            if elapsed < rate_limit {
                thread::sleep(rate_limit - elapsed);
            }
            
            tx.send(i).unwrap();
            last_sent = Instant::now();
        }
    });
    
    for msg in rx {
        println!("Received: {}", msg);
    }
}
```

---

## 10. Async Context with Tokio

Using channels with async/await:

```rust
use tokio::sync::mpsc;
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn async_channel_example() {
    let (tx, mut rx) = mpsc::channel::<String>(32);
    
    // Spawn async task
    tokio::spawn(async move {
        for i in 0..5 {
            let msg = format!("Message {}", i);
            tx.send(msg).await.unwrap();
            sleep(Duration::from_millis(100)).await;
        }
    });
    
    // Receive in async context
    while let Some(msg) = rx.recv().await {
        println!("Got: {}", msg);
    }
}
```

---

## Key Takeaways

1. **Ownership Transfer**: Message passing moves data, preventing data races
2. **MPSC Limitation**: Standard library only supports one receiver
3. **Crossbeam**: Production-grade alternative with MPMC and select
4. **Error Handling**: Always handle disconnection and send failures
5. **Performance**: Batch messages, use Arc for large data
6. **Patterns**: Worker pools, request-response, fan-out/fan-in
7. **Async**: Use Tokio's mpsc for async contexts

Message passing is idiomatic Rust for concurrent communication. It provides **compile-time safety**, **zero-cost abstractions**, and **fearless concurrency**.