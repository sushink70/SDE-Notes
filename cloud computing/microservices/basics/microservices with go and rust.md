# Goroutines/Async in Microservices & Database Engines

---

## 🧠 Big Picture First: Why Concurrency Matters Here

```
┌─────────────────────────────────────────────────────────────────┐
│           Where Concurrency Is The Core Problem                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  MICROSERVICES:                                                 │
│  • 1000s of HTTP requests arrive simultaneously                 │
│  • Each request: network I/O + DB query + response             │
│  • Without concurrency → requests queue up → latency spikes    │
│                                                                 │
│  DATABASE ENGINE:                                               │
│  • 100s of clients querying at same time                       │
│  • Disk I/O, buffer management, transaction isolation          │
│  • Without concurrency → one query blocks everyone             │
│                                                                 │
│  Both problems = "serve many clients, don't waste CPU waiting" │
└─────────────────────────────────────────────────────────────────┘
```

---

## PART 1: MICROSERVICES

---

### Concept: What is a Microservice?

> A **microservice** is a small, independently deployable program that does ONE thing (e.g., "UserService", "OrderService", "PaymentService"). They talk to each other over a network (HTTP/gRPC).

```
Traditional Monolith:          Microservices:
┌─────────────────────┐        ┌──────────┐  ┌──────────┐
│  Users + Orders +   │        │  Users   │  │  Orders  │
│  Payments + Auth    │        │ Service  │  │ Service  │
│  (one big program)  │        └────┬─────┘  └────┬─────┘
└─────────────────────┘             │              │
                                    └──────┬───────┘
                                    ┌──────┴───────┐
                                    │   Payments   │
                                    │   Service    │
                                    └──────────────┘
```

---

### Stack We'll Use

```
┌─────────────────────────────────────────────────────┐
│              Rust Microservice Stack                │
├──────────────────┬──────────────────────────────────┤
│  axum            │ HTTP web framework (like gin/chi) │
│  tokio           │ async runtime (goroutine engine)  │
│  sqlx            │ async database driver             │
│  serde           │ JSON serialization                │
│  tower           │ middleware (like Go's net/http)   │
│  reqwest         │ async HTTP client                 │
└──────────────────┴──────────────────────────────────┘
```

```toml
# Cargo.toml
[dependencies]
axum = "0.7"
tokio = { version = "1", features = ["full"] }
sqlx = { version = "0.8", features = ["postgres", "runtime-tokio"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
reqwest = { version = "0.12", features = ["json"] }
uuid = { version = "1", features = ["v4"] }
```

---

### Building a Complete User Microservice

```
Request Flow:

Client
  │
  │ HTTP POST /users
  ▼
┌─────────────────────────────────────────────┐
│              axum Router                    │
│  (each request = one tokio::spawn task)     │
└──────────────┬──────────────────────────────┘
               │
        ┌──────▼──────┐
        │   Handler   │  ← async fn, like goroutine per request
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  Service    │  ← business logic
        └──────┬──────┘
               │
        ┌──────▼──────┐
        │  Database   │  ← sqlx async query
        │   Pool      │
        └─────────────┘
```

```rust
// ── main.rs ──────────────────────────────────────────────────────

use axum::{
    extract::{Path, State},
    http::StatusCode,
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use sqlx::PgPool;
use uuid::Uuid;

// ── Data shapes ──────────────────────────────────────────────────

// What client sends to CREATE a user
#[derive(Deserialize)]
struct CreateUserRequest {
    name: String,
    email: String,
}

// What we store and return
#[derive(Serialize, sqlx::FromRow)]
struct User {
    id: Uuid,
    name: String,
    email: String,
}

// Shared state across all requests
// Arc = Atomic Reference Count — safe shared ownership
#[derive(Clone)]
struct AppState {
    db: PgPool, // connection pool — explained below
}

// ── Handlers (each runs as async task per request) ────────────────

// POST /users — create a new user
async fn create_user(
    State(state): State<AppState>,   // shared DB pool
    Json(body): Json<CreateUserRequest>, // parsed request body
) -> Result<(StatusCode, Json<User>), StatusCode> {

    // This query runs ASYNC — doesn't block other requests
    let user = sqlx::query_as::<_, User>(
        "INSERT INTO users (id, name, email)
         VALUES ($1, $2, $3)
         RETURNING id, name, email"
    )
    .bind(Uuid::new_v4())
    .bind(&body.name)
    .bind(&body.email)
    .fetch_one(&state.db)  // borrows from pool, non-blocking
    .await                 // ← YIELD POINT: other requests run here
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?;

    Ok((StatusCode::CREATED, Json(user)))
}

// GET /users/:id — fetch user by id
async fn get_user(
    Path(id): Path<Uuid>,
    State(state): State<AppState>,
) -> Result<Json<User>, StatusCode> {

    let user = sqlx::query_as::<_, User>(
        "SELECT id, name, email FROM users WHERE id = $1"
    )
    .bind(id)
    .fetch_optional(&state.db)
    .await
    .map_err(|_| StatusCode::INTERNAL_SERVER_ERROR)?
    .ok_or(StatusCode::NOT_FOUND)?;

    Ok(Json(user))
}

// ── Main ──────────────────────────────────────────────────────────

#[tokio::main]
async fn main() {
    // Connection pool: manages N DB connections shared across tasks
    let db = PgPool::connect("postgres://user:pass@localhost/mydb")
        .await
        .expect("Failed to connect to database");

    let state = AppState { db };

    let app = Router::new()
        .route("/users", post(create_user))
        .route("/users/:id", get(get_user))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:8080")
        .await
        .unwrap();

    println!("Listening on port 8080");

    // This loop handles THOUSANDS of concurrent connections
    // Each connection = one tokio task (like a goroutine)
    axum::serve(listener, app).await.unwrap();
}
```

---

### How axum Handles 10,000 Concurrent Requests

```
10,000 requests arrive simultaneously:

Request 1 ──▶┐
Request 2 ──▶┤
Request 3 ──▶┤  Tokio Runtime
  ...         │  ┌─────────────────────────────────┐
Request N ──▶┘  │  Work-Stealing Thread Pool      │
                │                                 │
                │  Task 1: await DB query...      │
                │  Task 2: await DB query...      │──▶ OS Threads
                │  Task 3: computing response     │    (= CPU cores)
                │  Task 4: await DB query...      │
                │  ...                            │
                └─────────────────────────────────┘

While Task 1 waits for DB → Task 3 uses the CPU
No thread is wasted waiting. Zero waste.
```

---

### Concept: Connection Pool

> A **connection pool** is a cache of pre-opened database connections. Opening a DB connection is expensive (~50ms). A pool keeps them alive and reuses them.

```
Without pool:                    With pool (sqlx PgPool):

Request 1: open conn (50ms)      Pool has 10 connections ready:
           query (5ms)           [C1][C2][C3][C4][C5][C6][C7][C8][C9][C10]
           close conn (10ms)
           Total: 65ms           Request 1: borrow C1 → query(5ms) → return C1
                                 Request 2: borrow C2 → query(5ms) → return C2
                                 Total: 5ms ← 13x faster
```

```rust
// Configure pool size based on workload
let db = sqlx::postgres::PgPoolOptions::new()
    .max_connections(20)         // max 20 concurrent DB connections
    .min_connections(5)          // keep 5 always warm
    .acquire_timeout(std::time::Duration::from_secs(3))
    .connect("postgres://...")
    .await?;
```

---

### Service-to-Service Communication (Async HTTP Client)

> In microservices, services call each other. This is I/O — perfect for async.

```
OrderService needs UserService to validate user:

OrderService                    UserService
     │                               │
     │── async HTTP GET /users/id ──▶│
     │                               │ (other tasks run here)
     │◀─────────── User JSON ────────│
     │
     │ continue processing order
```

```rust
use reqwest::Client;
use serde::Deserialize;

#[derive(Deserialize)]
struct User {
    id: String,
    name: String,
    email: String,
}

// Called inside an async handler
async fn validate_user(
    http: &Client,
    user_id: &str,
) -> Result<User, reqwest::Error> {

    let user = http
        .get(format!("http://user-service:8080/users/{}", user_id))
        .send()
        .await?           // yield: other tasks run during network wait
        .json::<User>()
        .await?;          // yield: other tasks run during body read

    Ok(user)
}

// Call MULTIPLE services CONCURRENTLY
async fn create_order_handler(/* ... */) {
    let http = Client::new();

    // Launch both calls AT THE SAME TIME — like 2 goroutines
    let (user_result, inventory_result) = tokio::join!(
        validate_user(&http, "user-123"),
        check_inventory(&http, "product-456"),
    );

    // Both complete in parallel — total time = max(t1, t2)
    // Not t1 + t2
}
```

```
tokio::join! parallelism:

t=0ms    validate_user   ──────────────────────▶ done at 80ms
         check_inventory ──────────────────────────────▶ done at 120ms

Total: 120ms  ✓

Without join! (sequential):
         validate_user   ──────────▶
                                    check_inventory ──────────────▶
Total: 200ms  ✗
```

---

### Background Workers (Goroutine-style Fire and Forget)

> Some work doesn't need to block the response: sending emails, logging, analytics.

```rust
use tokio::sync::mpsc;

// Email job definition
struct EmailJob {
    to: String,
    subject: String,
    body: String,
}

// Background worker — runs forever, processes jobs from channel
async fn email_worker(mut rx: mpsc::Receiver<EmailJob>) {
    while let Some(job) = rx.recv().await {
        // send email async — doesn't block main request flow
        send_email(job).await;
        println!("Email sent to {}", job.to);  // simplified
    }
}

// In main:
#[tokio::main]
async fn main() {
    let (email_tx, email_rx) = mpsc::channel::<EmailJob>(100);

    // Spawn background worker — like a goroutine daemon
    tokio::spawn(email_worker(email_rx));

    // email_tx is passed to handlers via AppState
    // Handlers just drop jobs into channel and return immediately
}

// In handler — fire and forget
async fn register_user(
    State(state): State<AppState>,
    Json(body): Json<CreateUserRequest>,
) -> StatusCode {
    // ... create user in DB ...

    // Send email job — non-blocking, returns instantly
    let _ = state.email_tx.send(EmailJob {
        to: body.email.clone(),
        subject: "Welcome!".into(),
        body: "Thanks for registering".into(),
    }).await;

    StatusCode::CREATED
    // Response sent immediately — email sends in background
}
```

```
Fire-and-Forget Pattern:

HTTP Request
     │
     ▼
  Handler
     │
     ├── Create user in DB (await)
     │
     ├── Drop EmailJob into channel ──▶ [channel buffer]
     │   (instant, non-blocking)              │
     │                                        ▼
     ├── Return 201 response          email_worker task
     │   (client gets response        processes it later
     │    in ~5ms)                    (doesn't affect user)
     ▼
  Done
```

---

## PART 2: DATABASE ENGINE INTERNALS

---

### Concept: What Does a DB Engine Need Concurrency For?

```
┌─────────────────────────────────────────────────────────────────┐
│           Database Engine Concurrency Requirements              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. CONNECTION HANDLER  — one task per client connection        │
│  2. BUFFER POOL MANAGER — shared page cache, concurrent access  │
│  3. WAL WRITER          — background thread flushing to disk    │
│  4. CHECKPOINT WORKER   — periodic background flusher           │
│  5. LOCK MANAGER        — coordinate concurrent transactions    │
│  6. QUERY EXECUTOR      — parallel query execution              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

> **WAL** = Write-Ahead Log. Before changing data on disk, write what you're ABOUT to do in a log first. If crash happens, replay the log to recover. Used by PostgreSQL, SQLite, MySQL.

> **Buffer Pool** = In-memory cache of disk pages. Database doesn't read disk directly — it reads pages into RAM (buffer pool) first.

> **Page** = Fixed-size block of data (usually 4KB or 8KB) that databases read/write atomically.

---

### Building a Mini Database Engine Core

```
Architecture of our mini DB engine:

┌────────────────────────────────────────────────────────────┐
│                    Mini DB Engine                          │
│                                                            │
│  ┌──────────────┐    ┌──────────────┐    ┌─────────────┐  │
│  │  Connection  │    │  Connection  │    │  Connection │  │
│  │  Handler 1   │    │  Handler 2   │    │  Handler 3  │  │
│  │  (async task)│    │  (async task)│    │ (async task)│  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬──────┘  │
│         │                  │                   │          │
│         └──────────────────┼───────────────────┘          │
│                            │                              │
│                   ┌────────▼────────┐                     │
│                   │  Query Engine   │                     │
│                   └────────┬────────┘                     │
│                            │                              │
│              ┌─────────────┼─────────────┐               │
│              │             │             │                │
│     ┌────────▼──┐  ┌───────▼───┐  ┌─────▼──────┐        │
│     │  Buffer   │  │   Lock    │  │    WAL     │        │
│     │   Pool    │  │  Manager  │  │   Writer   │        │
│     │ (RwLock)  │  │ (Mutex)   │  │ (channel)  │        │
│     └────────┬──┘  └───────────┘  └─────┬──────┘        │
│              │                          │                │
│           ┌──▼──────────────────────────▼──┐             │
│           │         Disk I/O               │             │
│           └────────────────────────────────┘             │
└────────────────────────────────────────────────────────────┘
```

---

### Core Concurrency Primitives Explained

> **Mutex** = Mutual Exclusion. Only ONE thread can hold it at a time. Like a bathroom key — only one person inside.

> **RwLock** = Read-Write Lock. MANY readers OR ONE writer at a time. Like a library — many people can read same book, but only one can write in it.

> **Arc** = Atomic Reference Counter. Lets multiple threads SHARE ownership of data safely.

```
Mutex vs RwLock:

Mutex:
  Thread A holds lock ──────────────┐
  Thread B waiting ─────────────────┤ blocked
  Thread C waiting ─────────────────┘

RwLock (Read):
  Thread A reading ─────────────────┐
  Thread B reading ─────────────────┤ all allowed simultaneously
  Thread C reading ─────────────────┘

RwLock (Write):
  Thread A writing ─────────────────┐
  Thread B waiting ─────────────────┤ blocked (exclusive)
  Thread C waiting ─────────────────┘
```

---

### 1. Buffer Pool Manager

```rust
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;

// PageId = which page on disk we're referring to
type PageId = u64;

// A page = 4KB block of raw data
#[derive(Clone)]
struct Page {
    id: PageId,
    data: Vec<u8>,  // 4096 bytes
    dirty: bool,    // dirty = modified in memory, not yet on disk
}

// Buffer Pool: cache of pages in memory
struct BufferPool {
    // RwLock: many readers can read pages at once
    //         only one writer can evict/load pages
    pages: RwLock<HashMap<PageId, Page>>,
    capacity: usize,
}

impl BufferPool {
    fn new(capacity: usize) -> Self {
        BufferPool {
            pages: RwLock::new(HashMap::new()),
            capacity,
        }
    }

    // Fetch page — read lock allows concurrent reads
    async fn fetch_page(&self, page_id: PageId) -> Page {
        // First try read lock (non-exclusive — many can hold)
        {
            let pages = self.pages.read().await; // read lock
            if let Some(page) = pages.get(&page_id) {
                return page.clone(); // cache hit — return immediately
            }
        } // read lock released here

        // Cache miss — need write lock to load from disk
        let mut pages = self.pages.write().await; // exclusive write lock

        // Double-check: another task may have loaded it while we waited
        if let Some(page) = pages.get(&page_id) {
            return page.clone();
        }

        // Load from disk (expensive I/O operation)
        let page = self.load_from_disk(page_id).await;
        pages.insert(page_id, page.clone());
        page
    }

    // Write to page — marks it dirty
    async fn write_page(&self, page_id: PageId, data: Vec<u8>) {
        let mut pages = self.pages.write().await;
        if let Some(page) = pages.get_mut(&page_id) {
            page.data = data;
            page.dirty = true; // needs to be flushed to disk later
        }
    }

    async fn load_from_disk(&self, page_id: PageId) -> Page {
        // tokio::fs for non-blocking file I/O
        // Simulated here
        tokio::time::sleep(tokio::time::Duration::from_micros(100)).await;
        Page {
            id: page_id,
            data: vec![0u8; 4096],
            dirty: false,
        }
    }
}
```

```
Buffer Pool Read Flow:

   Request for page 42
          │
          ▼
   Acquire READ lock
   (multiple tasks can do this simultaneously)
          │
          ▼
   Page in cache? ──YES──▶ return page (fast path ~1μs)
          │
          NO
          │
   Release read lock
          │
   Acquire WRITE lock (exclusive)
          │
   Check again (another task may have loaded it)
          │
   Load from disk (~100μs) ──▶ insert into cache
          │
   Release write lock
          │
   Return page
```

---

### 2. WAL Writer (Write-Ahead Log)

```rust
use tokio::sync::mpsc;
use tokio::io::AsyncWriteExt;
use tokio::fs::OpenOptions;

// A WAL record: describes one change
#[derive(Debug)]
struct WalRecord {
    transaction_id: u64,
    page_id: PageId,
    before_data: Vec<u8>,  // for rollback
    after_data: Vec<u8>,   // for redo
}

// WAL Writer: receives records via channel, batches them, flushes to disk
struct WalWriter {
    sender: mpsc::Sender<WalRecord>,
}

impl WalWriter {
    // Start background WAL writer task
    // Returns a handle to send records to it
    fn start() -> Self {
        let (tx, mut rx) = mpsc::channel::<WalRecord>(1000);

        // Background task — like a goroutine daemon
        tokio::spawn(async move {
            let mut file = OpenOptions::new()
                .create(true)
                .append(true)
                .open("wal.log")
                .await
                .unwrap();

            let mut batch = Vec::new();

            loop {
                // Collect records in batches for efficiency
                // recv() returns None when all Senders are dropped
                match tokio::time::timeout(
                    tokio::time::Duration::from_millis(10),
                    rx.recv()
                ).await {
                    Ok(Some(record)) => {
                        batch.push(record);

                        // Also drain any immediately available records
                        while let Ok(r) = rx.try_recv() {
                            batch.push(r);
                            if batch.len() >= 100 { break; }
                        }

                        // Flush batch to disk
                        for record in &batch {
                            let line = format!(
                                "TX:{} PAGE:{} \n",
                                record.transaction_id,
                                record.page_id
                            );
                            file.write_all(line.as_bytes()).await.unwrap();
                        }
                        file.flush().await.unwrap(); // fsync
                        batch.clear();
                    }
                    Ok(None) => break, // channel closed
                    Err(_) => {
                        // Timeout — flush what we have
                        if !batch.is_empty() {
                            file.flush().await.unwrap();
                            batch.clear();
                        }
                    }
                }
            }
        });

        WalWriter { sender: tx }
    }

    // Called by transaction code — non-blocking
    async fn log(&self, record: WalRecord) {
        self.sender.send(record).await.unwrap();
        // Returns immediately — WAL writer handles disk I/O async
    }
}
```

```
WAL Write Flow:

Transaction T1 ──log(record)──▶ channel [r1][r2][r3]
Transaction T2 ──log(record)──▶         [r4][r5]
Transaction T3 ──log(record)──▶              background WAL writer
                                              │
                              Every 10ms:    ▼
                              batch flush ──▶ wal.log (disk)

T1, T2, T3 return INSTANTLY
Disk write happens in background
= low latency + durability
```

---

### 3. Transaction Manager with Lock Manager

```rust
use std::collections::{HashMap, HashSet};
use tokio::sync::{Mutex, Notify};

type TransactionId = u64;

// Lock modes
#[derive(PartialEq, Clone, Debug)]
enum LockMode {
    Shared,    // Read lock — multiple transactions can hold
    Exclusive, // Write lock — only one transaction can hold
}

struct LockManager {
    // For each page, track who holds which lock
    locks: Mutex<HashMap<PageId, Vec<(TransactionId, LockMode)>>>,
    notify: Notify, // wake up waiting transactions when lock released
}

impl LockManager {
    fn new() -> Arc<Self> {
        Arc::new(LockManager {
            locks: Mutex::new(HashMap::new()),
            notify: Notify::new(),
        })
    }

    async fn acquire(&self, tx_id: TransactionId, page_id: PageId, mode: LockMode) {
        loop {
            let mut locks = self.locks.lock().await;
            let holders = locks.entry(page_id).or_default();

            let can_acquire = match &mode {
                // Shared: OK unless someone has exclusive
                LockMode::Shared => holders.iter()
                    .all(|(_, m)| *m == LockMode::Shared),

                // Exclusive: OK only if no one else holds any lock
                LockMode::Exclusive => holders.is_empty(),
            };

            if can_acquire {
                holders.push((tx_id, mode));
                return; // lock acquired
            }

            // Cannot acquire — release mutex and wait
            drop(locks);
            self.notify.notified().await; // sleep until notified
            // Loop back and try again
        }
    }

    async fn release(&self, tx_id: TransactionId, page_id: PageId) {
        let mut locks = self.locks.lock().await;
        if let Some(holders) = locks.get_mut(&page_id) {
            holders.retain(|(id, _)| *id != tx_id);
        }
        drop(locks);
        self.notify.notify_waiters(); // wake up all waiting transactions
    }
}
```

```
Lock Manager Flow (2 transactions):

T1 wants SHARED lock on page 5:
  ┌─ locks[5] is empty? YES ─▶ grant lock
  │  locks[5] = [(T1, Shared)]

T2 wants SHARED lock on page 5:
  ┌─ locks[5] has only Shared? YES ─▶ grant lock
  │  locks[5] = [(T1, Shared), (T2, Shared)]

T3 wants EXCLUSIVE lock on page 5:
  ┌─ locks[5] is empty? NO ─▶ WAIT
  │  T3 sleeps on notify.notified()

T1 releases:
  locks[5] = [(T2, Shared)]
  notify.notify_waiters() ─▶ T3 wakes up
  T3 checks again: NOT empty ─▶ waits again

T2 releases:
  locks[5] = []
  notify.notify_waiters() ─▶ T3 wakes up
  T3 checks again: empty ─▶ GRANT exclusive lock
```

---

### 4. Complete Transaction: Tying It Together

```rust
struct Database {
    buffer_pool: Arc<BufferPool>,
    wal: WalWriter,
    lock_mgr: Arc<LockManager>,
    next_tx_id: Mutex<u64>,
}

impl Database {
    async fn begin_transaction(&self) -> Transaction {
        let mut id = self.next_tx_id.lock().await;
        *id += 1;
        Transaction {
            id: *id,
            db: self,
            locked_pages: HashSet::new(),
        }
    }
}

struct Transaction<'a> {
    id: TransactionId,
    db: &'a Database,
    locked_pages: HashSet<PageId>,
}

impl<'a> Transaction<'a> {
    async fn read_page(&mut self, page_id: PageId) -> Page {
        // 1. Acquire shared lock
        self.db.lock_mgr
            .acquire(self.id, page_id, LockMode::Shared)
            .await;
        self.locked_pages.insert(page_id);

        // 2. Fetch from buffer pool
        self.db.buffer_pool.fetch_page(page_id).await
    }

    async fn write_page(&mut self, page_id: PageId, data: Vec<u8>) {
        // 1. Acquire exclusive lock
        self.db.lock_mgr
            .acquire(self.id, page_id, LockMode::Exclusive)
            .await;
        self.locked_pages.insert(page_id);

        // 2. Log to WAL BEFORE modifying (Write-Ahead!)
        let old_page = self.db.buffer_pool.fetch_page(page_id).await;
        self.db.wal.log(WalRecord {
            transaction_id: self.id,
            page_id,
            before_data: old_page.data,
            after_data: data.clone(),
        }).await;

        // 3. Modify buffer pool
        self.db.buffer_pool.write_page(page_id, data).await;
    }

    async fn commit(mut self) {
        // Release all locks
        for page_id in self.locked_pages.drain() {
            self.db.lock_mgr.release(self.id, page_id).await;
        }
        // WAL commit record
        self.db.wal.log(WalRecord {
            transaction_id: self.id,
            page_id: 0,
            before_data: vec![],
            after_data: b"COMMIT".to_vec(),
        }).await;
    }
}
```

```
Full Transaction Flow:

BEGIN
  │
  ├─ acquire lock ──▶ LockManager (Mutex-protected)
  │
  ├─ READ page ──▶ BufferPool (RwLock-protected)
  │                  └─ cache hit? return | cache miss? disk I/O
  │
  ├─ WRITE page ──▶ WAL log (channel ──▶ background writer)
  │                  └─ then modify BufferPool
  │
COMMIT
  │
  ├─ release all locks ──▶ wake waiting transactions
  │
  └─ WAL COMMIT record ──▶ durable on disk
```

---

## Full System: How It All Connects

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   Client 1 ──HTTP──▶ axum handler ──▶ tokio task 1             │
│   Client 2 ──HTTP──▶ axum handler ──▶ tokio task 2             │
│   Client N ──HTTP──▶ axum handler ──▶ tokio task N             │
│                                                                  │
│   Each task:                                                     │
│     1. sqlx ──▶ DB connection pool ──▶ postgres                 │
│     OR                                                           │
│     1. Begin transaction (mini DB engine)                        │
│     2. Acquire locks (LockManager)                               │
│     3. Read/Write pages (BufferPool + WAL)                       │
│     4. Commit (release locks + flush WAL)                        │
│                                                                  │
│   Background workers (always running):                           │
│     • WAL writer task (channel consumer)                         │
│     • Checkpoint task (periodically flush dirty pages)          │
│     • Lock timeout task (detect deadlocks)                       │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Comparison: Go vs Rust in This Architecture

```
┌───────────────────────┬────────────────────────────────────────┐
│      Go               │           Rust                         │
├───────────────────────┼────────────────────────────────────────┤
│ goroutine per conn    │ tokio task per connection              │
│ sync.Mutex            │ tokio::sync::Mutex (async-aware)       │
│ sync.RWMutex          │ tokio::sync::RwLock                    │
│ sync.WaitGroup        │ JoinHandle + join!                     │
│ chan (background work) │ mpsc::channel (WAL, email workers)    │
│ GC prevents races     │ ownership prevents races (compile time)│
│ net/http              │ axum + hyper                           │
│ database/sql          │ sqlx                                   │
└───────────────────────┴────────────────────────────────────────┘
```

---

## 🧘 Mentor's Insight

> You've just seen the **same three patterns** used everywhere:
> 1. **Task per connection** — async task/goroutine handles each client
> 2. **Shared state via locks** — Mutex/RwLock on buffer pool, lock manager
> 3. **Background workers via channels** — WAL writer, email sender, checkpointer

Every production system — PostgreSQL, TiKV (Rust DB), CockroachDB, Kafka — is built from **these exact primitives** at different scales.

**Deliberate practice target**: Implement the buffer pool + WAL writer from scratch. These two components alone will teach you 80% of what database engineers know about concurrency. That's the **Pareto principle** applied to systems learning.

# Lock-Free Database Engines: Complete Deep Dive

---

## 🧠 First: What Does "Lock-Free" Actually Mean?

> This is a **spectrum**, not a binary. "Lock-free" in databases means different things at different layers.

```
┌─────────────────────────────────────────────────────────────────┐
│              The Lock-Free Spectrum                             │
│                                                                 │
│  FULLY LOCKED          MVCC               TRUE LOCK-FREE        │
│  (old MySQL)      (PostgreSQL)            (atomic CAS only)     │
│       │                 │                      │                │
│  Writers block    Readers never          No thread ever         │
│  readers          block writers          blocks another         │
│  Readers block    Writers may still      Uses CPU atomics       │
│  writers          conflict               (CAS, fetch-add)       │
│                                                                 │
│  Most "lock-free" DBs are MVCC-based — not truly lock-free     │
│  at every layer, but readers NEVER block writers               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Core Concept: MVCC (Multi-Version Concurrency Control)

> **MVCC** = Instead of locking a row when writing, create a **new version** of it. Old readers see the old version. New readers see the new version. Nobody waits.

```
WITHOUT MVCC (Traditional Locking):

T1 writes row ──▶ LOCK row
                     │
T2 reads row  ──▶ BLOCKED ──── waiting ──── waiting ──────▶ reads
                     │
T1 commits    ──▶ UNLOCK row
                              ▲ T2 unblocked here

T2 waited the ENTIRE duration of T1's write. Bad.
```

```
WITH MVCC:

           Version 1 (price=100)    Version 2 (price=120)
           ┌─────────────────────┐  ┌──────────────────────┐
           │ txn_start=1         │  │ txn_start=11          │
           │ txn_end=11          │  │ txn_end=∞ (current)   │
           └─────────────────────┘  └──────────────────────┘

T1 (started at ts=10) sees ──▶ Version 1 (price=100)
T2 (started at ts=12) sees ──▶ Version 2 (price=120)

Both run SIMULTANEOUSLY. Neither waits. Zero blocking.
```

With MVCC, readers are never blocked by in-progress updates. Writers don't need to acquire exclusive row locks that would otherwise block reads. Multiple users can query or update the same data simultaneously with minimal contention.

---

## The Landscape of Lock-Free / MVCC DB Engines

```
┌────────────────────────────────────────────────────────────────────┐
│                   Lock-Free DB Engine Map                          │
│                                                                    │
│   CATEGORY 1: MVCC-based (reads never block)                       │
│   ┌─────────────┬────────────────────────────────────────┐         │
│   │ PostgreSQL  │ MVCC + SSI (Serializable Snapshot)     │         │
│   │ TiKV/TiDB   │ MVCC + Percolator 2PC (distributed)    │         │
│   │ FoundationDB│ MVCC + OCC (Optimistic)                │         │
│   │ CockroachDB │ MVCC + HLC (Hybrid Logical Clock)      │         │
│   │ sled (Rust) │ Lock-free B+ tree + MVCC               │         │
│   └─────────────┴────────────────────────────────────────┘         │
│                                                                    │
│   CATEGORY 2: OCC (Optimistic Concurrency Control)                 │
│   ┌─────────────┬────────────────────────────────────────┐         │
│   │ TigerBeetle │ Serial execution (truly sequential)    │         │
│   │ FoundationDB│ Optimistic — detect conflicts on commit│         │
│   └─────────────┴────────────────────────────────────────┘         │
│                                                                    │
│   CATEGORY 3: Atomic / True Lock-Free Structures                   │
│   ┌─────────────┬────────────────────────────────────────┐         │
│   │ sled        │ lock-free pagecache (Rust, CAS-based)  │         │
│   │ LevelDB/    │ LSM tree — lock-free reads via         │         │
│   │ RocksDB     │ immutable SSTables                     │         │
│   └─────────────┴────────────────────────────────────────┘         │
└────────────────────────────────────────────────────────────────────┘
```

---

## Engine 1: PostgreSQL — MVCC with SSI

PostgreSQL implements serializability via Serializable Snapshot Isolation.

```
How PostgreSQL MVCC Works Internally:

Each row has hidden system columns:
┌─────────┬────────────┬────────────┬──────────┐
│  data   │  xmin      │  xmax      │  ctid    │
│ (value) │ (created   │ (deleted   │ (pointer │
│         │  by tx ID) │  by tx ID) │  to row) │
└─────────┴────────────┴────────────┴──────────┘

INSERT row:   xmin = current_txid,  xmax = 0
UPDATE row:   old row: xmax = current_txid
              new row: xmin = current_txid, xmax = 0
DELETE row:   xmax = current_txid (not physically deleted yet)

Visibility check for transaction T:
  row is visible if:
    xmin committed AND xmin < T.snapshot_start
    AND (xmax = 0 OR xmax NOT committed OR xmax > T.snapshot_start)
```

```
Visibility Rule — Decision Tree:

   Is xmin committed?
        │
       NO ──▶ INVISIBLE (row created by uncommitted tx)
        │
       YES
        │
   Is xmin < my snapshot?
        │
       NO ──▶ INVISIBLE (row created after I started)
        │
       YES
        │
   Is xmax = 0?
        │
       YES ──▶ VISIBLE (row not deleted)
        │
       NO
        │
   Is xmax committed AND xmax < my snapshot?
        │
       YES ──▶ INVISIBLE (row deleted before I started)
        │
       NO  ──▶ VISIBLE (row deleted after I started = I see it)
```

---

## Engine 2: TiKV — Distributed MVCC in Rust

> **TiKV** is written entirely in Rust. It's the storage engine behind **TiDB** (distributed MySQL-compatible database). One of the most important Rust projects in production.

MVCC is an elegant solution where each update creates a new version of the data object instead of updating it in-place, so that concurrent readers can still see the old version while the update transaction proceeds. Such a strategy can prevent read-only transactions from waiting. In fact, locking is not required at all.

```
TiKV Architecture:

Client
  │
  ▼
┌──────────────────────────────────────┐
│         KV + Coprocessor API         │
├──────────────────────────────────────┤
│              MVCC Layer              │  ← lock-free reads
├──────────────────────────────────────┤
│           Raft Consensus             │  ← replication
├──────────────────────────────────────┤
│            RocksDB (LSM)             │  ← actual storage
└──────────────────────────────────────┘
```

TiKV uses column families (CF) in RocksDB to handle MVCC information. Specifically, TiKV stores Key-Values, Locks, and Writes information in CF_DEFAULT, CF_LOCK, and CF_WRITE.

```
TiKV's 3 Column Families:

CF_DEFAULT:  actual data values
  key@timestamp ──▶ value

CF_LOCK:     in-progress transaction locks
  key ──▶ {tx_id, lock_type, primary_key}

CF_WRITE:    committed transaction metadata
  key@commitTS ──▶ {write_type, startTS}

Read at timestamp T:
  1. Check CF_LOCK → any lock with startTS < T? → must wait or abort
  2. Find latest entry in CF_WRITE where commitTS ≤ T
  3. Use that startTS to look up actual value in CF_DEFAULT
```

### TiKV's Percolator 2-Phase Commit (Lock-Free Reads)

The core transaction model of TiKV is called 2-Phase Commit powered by MVCC. TiKV has a Timestamp Oracle (TSO) to provide globally unique timestamps. The default isolation level in TiKV is Repeatable Read. When a transaction starts, there will be a global read timestamp; when a transaction commits, there will be a global commit timestamp.

```
Percolator 2PC Flow:

PHASE 1 — PREWRITE:
  T1 wants to write keys A, B, C
  │
  ├── Pick A as PRIMARY key
  ├── Lock A in CF_LOCK (primary)
  ├── Lock B in CF_LOCK (secondary, points to A)
  └── Lock C in CF_LOCK (secondary, points to A)
  
  During this time: READERS check CF_LOCK
    └── see lock? → check if primary committed
        → not committed? → wait or push tx

PHASE 2 — COMMIT:
  ├── Write A to CF_WRITE with commitTS
  ├── Remove A from CF_LOCK  ← atomic! this is the commit point
  └── Async: clean up B, C locks (readers help clean up)

READS: never blocked during phase 1 (they read old version)
       only momentarily during phase 2 (microseconds)
```

---

## Engine 3: FoundationDB — OCC + MVCC

> **Optimistic Concurrency Control (OCC)** = Don't lock anything. Just try the transaction. At commit time, CHECK if anyone else touched your data. If yes → abort and retry. If no → commit.

Tigris provides lock-free concurrency control using FoundationDB, combining OCC and MVCC to order transactions. This is achieved by a sequencer which determines the serial order by assigning a read version and a commit version to each transaction.

```
OCC Flow (FoundationDB style):

Transaction T:
  1. READ PHASE (no locks at all):
     │
     ├── Record read_version = current_timestamp
     ├── Read keys K1, K2, K3 (add to read_set)
     └── Compute new values (add to write_set)

  2. VALIDATE PHASE (at commit):
     │
     ├── Has anyone written to K1, K2, K3
     │   since my read_version?
     │
     ├── YES ──▶ ABORT + RETRY (conflict detected)
     └── NO  ──▶ proceed to commit

  3. WRITE PHASE:
     └── Atomically apply write_set with new commit_version

BENEFIT: zero locks during execution
COST:    high-contention workloads cause many retries
```

```
OCC vs Pessimistic Locking:

OCC (FoundationDB):              Pessimistic (MySQL):
┌────────────────────┐           ┌────────────────────┐
│ T1: read A (free)  │           │ T1: read A (LOCK A)│
│ T2: read A (free)  │           │ T2: read A (WAIT)  │
│ T1: write A        │           │                    │
│ T2: ABORT (conflict│           │ T1: commit         │
│     retry)         │           │ T2: reads (now ok) │
└────────────────────┘           └────────────────────┘

OCC wins when: conflicts are RARE (read-heavy systems)
Pessimistic wins when: conflicts are FREQUENT (write-heavy)
```

---

## Engine 4: `sled` — Pure Rust Lock-Free B-Tree

> **sled** is an embedded database written in Rust that uses a **lock-free page cache** backed by atomic operations (CAS = Compare-And-Swap).

> **CAS (Compare-And-Swap)** = Hardware CPU instruction: "If this memory location still contains X, replace it with Y — atomically." No OS lock needed. The CPU itself guarantees atomicity.

```
CAS Mental Model:

Normal (locked):              CAS (lock-free):
┌──────────┐                 ┌──────────────────────────┐
│ lock()   │                 │ loop {                   │
│ read val │                 │   old = atomic_read(ptr) │
│ modify   │                 │   new = compute(old)     │
│ write    │                 │   if CAS(ptr, old, new)  │
│ unlock() │                 │     { break } // success │
└──────────┘                 │   // else: retry loop    │
                             │ }                        │
Uses OS mutex                └──────────────────────────┘
Blocks other threads         Uses CPU instruction only
                             Other threads never block
```

```rust
// sled usage — feels like a simple KV store
// but internally uses lock-free page cache

use sled::Db;

fn main() {
    let db: Db = sled::open("my_db").unwrap();

    // concurrent writes from many threads — no explicit locking needed
    db.insert(b"key1", b"value1").unwrap();
    db.insert(b"key2", b"value2").unwrap();

    // compare_and_swap — the core primitive
    // "only update if current value is old_value"
    let result = db.compare_and_swap(
        b"key1",              // key
        Some(b"value1"),      // expected current value
        Some(b"value_new"),   // new value
    ).unwrap();

    match result {
        Ok(()) => println!("CAS succeeded!"),
        Err(e) => println!("CAS failed: someone else changed it"),
    }

    // Transactions — uses optimistic approach internally
    db.transaction(|tx_db| {
        let val = tx_db.get(b"counter")?.unwrap_or(b"0".into());
        let n: i64 = std::str::from_utf8(&val)
            .unwrap()
            .parse()
            .unwrap();
        tx_db.insert(b"counter", (n + 1).to_string().as_bytes())?;
        Ok(())
    }).unwrap();
}
```

Sled uses a lock-free linked list for MVCC versions. The key design choice is between oldest-to-newest (O2N) ordering, which suffers from cache pollution due to scanning through old versions, and newest-to-oldest (N2O) ordering, which requires an indirection table.

---

## Engine 5: RocksDB / LevelDB — LSM Tree Lock-Free Reads

> **LSM Tree** = Log-Structured Merge Tree. Writes go to memory (MemTable), then are flushed to immutable sorted files (SSTables) on disk. Because SSTables are **immutable**, reads never need locks.

```
LSM Tree Structure:

WRITES:
  New data ──▶ MemTable (in-memory, mutable)
                  │
              (when full)
                  │
                  ▼
             L0 SSTable (immutable file on disk)
                  │
              (compaction)
                  │
             L1 SSTable ──▶ L2 ──▶ L3 (deeper = older, larger)

READS:
  Query ──▶ check MemTable
         ──▶ check L0 SSTables (newest first)
         ──▶ check L1, L2, L3...

SSTables are IMMUTABLE = reads need ZERO locks
Writers write to MemTable (separate from SSTables)
= reads and writes never conflict at storage level
```

---

## Engine 6: TigerBeetle — Serial Execution (Truly Lock-Free)

> **TigerBeetle** takes a radical approach: instead of MVCC or locks, it runs **one transaction at a time** but so fast (nanosecond-level operations) that the throughput beats lock-based systems.

Some systems, like SQLite and TigerBeetle, do actually serial execution where only one transaction runs at a time. But few databases implement serializable like this because it removes a number of fair concurrent execution histories.

```
TigerBeetle Model:

Traditional:                  TigerBeetle:
┌─────────────────────┐       ┌─────────────────────────────┐
│ Many concurrent     │       │ Single pipeline             │
│ transactions with   │       │                             │
│ complex locking =   │       │ T1 ──▶ T2 ──▶ T3 ──▶ T4   │
│ coordination        │       │                             │
│ overhead            │       │ Each tx takes ~100ns        │
└─────────────────────┘       │ No coordination overhead    │
                              │ 1M+ tx/second on 1 core     │
                              └─────────────────────────────┘
```

---

## Summary Comparison

```
┌───────────────┬──────────┬──────────┬───────────┬─────────────────┐
│  Engine       │ Language │ Model    │ Read-Lock │ Best For        │
├───────────────┼──────────┼──────────┼───────────┼─────────────────┤
│ PostgreSQL    │ C        │ MVCC+SSI │ Never     │ General OLTP    │
│ TiKV/TiDB    │ Rust     │ MVCC+2PC │ Never     │ Distributed     │
│ FoundationDB  │ C++/Flow │ MVCC+OCC │ Never     │ Low-conflict    │
│ CockroachDB   │ Go       │ MVCC+HLC │ Never     │ Global dist.    │
│ sled          │ Rust     │ Lock-free│ Never     │ Embedded Rust   │
│ RocksDB       │ C++      │ LSM      │ Never     │ Storage engine  │
│ TigerBeetle   │ Zig      │ Serial   │ Never     │ Financial tx    │
│ MongoDB WT    │ C        │ MVCC doc │ Never     │ Documents       │
└───────────────┴──────────┴──────────┴───────────┴─────────────────┘
```

---

## Implementing MVCC in Rust from Scratch

```rust
use std::collections::{BTreeMap, HashMap};
use std::sync::{Arc, RwLock};
use std::sync::atomic::{AtomicU64, Ordering};

// Transaction ID — monotonically increasing
type TxId = u64;

// Each version of a value
#[derive(Clone, Debug)]
struct Version {
    value: Vec<u8>,
    created_by: TxId,   // which transaction created this
    deleted_by: TxId,   // 0 = not deleted
}

// Global transaction counter
static TX_COUNTER: AtomicU64 = AtomicU64::new(1);

struct MvccStore {
    // key → list of versions (oldest first)
    data: RwLock<HashMap<Vec<u8>, Vec<Version>>>,
}

impl MvccStore {
    fn new() -> Arc<Self> {
        Arc::new(MvccStore {
            data: RwLock::new(HashMap::new()),
        })
    }

    // Read: find version visible to this transaction
    fn read(&self, key: &[u8], snapshot_tx: TxId) -> Option<Vec<u8>> {
        let data = self.data.read().unwrap(); // read lock (shared)
        let versions = data.get(key)?;

        // Walk versions newest to oldest
        // Return first version visible to snapshot_tx
        for version in versions.iter().rev() {
            let created_before = version.created_by < snapshot_tx;
            let not_deleted = version.deleted_by == 0
                || version.deleted_by >= snapshot_tx;

            if created_before && not_deleted {
                return Some(version.value.clone());
            }
        }
        None
    }

    // Write: add new version (doesn't touch existing versions)
    fn write(&self, key: Vec<u8>, value: Vec<u8>, tx_id: TxId) {
        let mut data = self.data.write().unwrap(); // write lock (exclusive)
        let versions = data.entry(key).or_default();
        versions.push(Version {
            value,
            created_by: tx_id,
            deleted_by: 0,
        });
    }

    // Garbage collect old versions no longer needed
    fn gc(&self, safe_point: TxId) {
        let mut data = self.data.write().unwrap();
        for versions in data.values_mut() {
            versions.retain(|v| {
                // Keep version if it might be visible to any active tx
                v.created_by >= safe_point
                || v.deleted_by == 0
                || v.deleted_by >= safe_point
            });
        }
    }
}

// Transaction abstraction
struct Transaction {
    id: TxId,
    store: Arc<MvccStore>,
    write_buffer: HashMap<Vec<u8>, Vec<u8>>, // local writes
}

impl Transaction {
    fn begin(store: Arc<MvccStore>) -> Self {
        let id = TX_COUNTER.fetch_add(1, Ordering::SeqCst);
        Transaction {
            id,
            store,
            write_buffer: HashMap::new(),
        }
    }

    fn read(&self, key: &[u8]) -> Option<Vec<u8>> {
        // Check local write buffer first
        if let Some(val) = self.write_buffer.get(key) {
            return Some(val.clone());
        }
        // Then check committed versions visible to us
        self.store.read(key, self.id)
    }

    fn write(&mut self, key: Vec<u8>, value: Vec<u8>) {
        // Buffer writes locally — not visible until commit
        self.write_buffer.insert(key, value);
    }

    fn commit(self) {
        // Flush all buffered writes to store at once
        for (key, value) in self.write_buffer {
            self.store.write(key, value, self.id);
        }
        println!("Transaction {} committed", self.id);
    }
}

fn main() {
    let store = MvccStore::new();

    // T1 writes initial value
    let mut t1 = Transaction::begin(store.clone());
    t1.write(b"balance".to_vec(), b"1000".to_vec());
    t1.commit(); // tx_id=1

    // T2 starts reading — gets snapshot at tx_id=2
    let t2 = Transaction::begin(store.clone()); // snapshot at tx_id=2

    // T3 writes new value concurrently
    let mut t3 = Transaction::begin(store.clone()); // tx_id=3
    t3.write(b"balance".to_vec(), b"2000".to_vec());
    t3.commit(); // committed at tx_id=3

    // T2 still sees OLD value (1000) — its snapshot is at tx_id=2
    let val = t2.read(b"balance");
    println!("T2 reads: {:?}", val); // b"1000" — not affected by T3!

    // T4 starts AFTER T3 commits — sees new value
    let t4 = Transaction::begin(store.clone()); // tx_id=4
    let val = t4.read(b"balance");
    println!("T4 reads: {:?}", val); // b"2000"
}
```

```
Execution Timeline:

tx_id:  1        2        3        4
        │        │        │        │
T1 write────commit│        │        │
        │        │        │        │
        │   T2 starts     │        │
        │   (snapshot=2)  │        │
        │        │        │        │
        │        │  T3 write──commit│
        │        │        │        │
        │        │        │  T4 starts
        │        │        │  (snapshot=4)
        │        │        │        │

T2.read(balance) → sees version created by tx=1 (< snapshot=2)
                 → NOT tx=3 (committed AFTER snapshot)
                 → returns "1000"  ✓

T4.read(balance) → sees version created by tx=3 (< snapshot=4)
                 → returns "2000"  ✓
```

---

## When To Use What

```
Decision Tree: Choosing a Lock-Free DB

What is your use case?
          │
    ┌─────┴───────┐
    │             │
Embedded       Distributed
(single node)  (cluster)
    │             │
    ▼             ├── Financial precision ──▶ TigerBeetle
  sled            │
  (Rust)          ├── MySQL compatible ────▶ TiDB/TiKV
                  │
                  ├── PostgreSQL compat ───▶ CockroachDB / YugabyteDB
                  │
                  ├── Low-level KV store ──▶ FoundationDB
                  │
                  └── Time series ────────▶ QuestDB
```

---

## 🧘 Mentor's Insight

> The deepest insight here is that **lock-free doesn't mean conflict-free**. It means conflicts are handled **without blocking threads**:
> - MVCC → readers see old snapshot, writers create new version
> - OCC → everyone works freely, conflicts detected at commit
> - CAS → retry loop at hardware level, no OS involvement

**Cognitive principle — First Principles Thinking**: Every "lock-free" technique reduces to one idea: **separate the concerns of reading and writing in time or space**. MVCC separates them in *time* (versions). LSM separates them in *space* (immutable files). Serial execution eliminates the problem entirely by removing concurrency.

Master one of these deeply (MVCC), and the others become variations. That's **chunking** at its finest.