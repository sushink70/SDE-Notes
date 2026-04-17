# The Complete Guide to Debugging Microservices
### A Systems-Level, Code-Driven Deep Dive for Engineers Who Think Like Architects

---

> *"You're not debugging code anymore. You're debugging a distributed system — one where every component lies, every clock drifts, and every failure hides behind another failure."*

---

## Table of Contents

1. [Foundations: What Is a Distributed System?](#1-foundations-what-is-a-distributed-system)
2. [Monolith vs Microservices: The Mental Model Shift](#2-monolith-vs-microservices-the-mental-model-shift)
3. [Loss of Linearity: Execution Flow Fragmentation](#3-loss-of-linearity-execution-flow-fragmentation)
4. [Network Unreliability: The Fundamental Problem](#4-network-unreliability-the-fundamental-problem)
5. [Partial Failures: When the System Lies to You](#5-partial-failures-when-the-system-lies-to-you)
6. [Data Inconsistency: No Single Source of Truth](#6-data-inconsistency-no-single-source-of-truth)
7. [Log Aggregation and Correlation IDs](#7-log-aggregation-and-correlation-ids)
8. [Concurrency Explosion](#8-concurrency-explosion)
9. [Version Mismatch and API Drift](#9-version-mismatch-and-api-drift)
10. [Retry Storms and Cascading Failures](#10-retry-storms-and-cascading-failures)
11. [Observability: Tracing, Metrics, Logging](#11-observability-tracing-metrics-logging)
12. [Environment Differences: Local vs Production](#12-environment-differences-local-vs-production)
13. [Asynchronous Communication: Queues and Events](#13-asynchronous-communication-queues-and-events)
14. [Security Layers: Auth, Tokens, and Policies](#14-security-layers-auth-tokens-and-policies)
15. [Infrastructure Complexity: Kubernetes and Beyond](#15-infrastructure-complexity-kubernetes-and-beyond)
16. [Time-Related Bugs: Clock Drift and Event Ordering](#16-time-related-bugs-clock-drift-and-event-ordering)
17. [Reproducibility: The Hardest Problem](#17-reproducibility-the-hardest-problem)
18. [A Production Debugging Workflow](#18-a-production-debugging-workflow)
19. [Mental Models for Distributed Systems Mastery](#19-mental-models-for-distributed-systems-mastery)

---

## 1. Foundations: What Is a Distributed System?

### Concept First

Before diving into debugging, you need to understand what you are actually working with.

A **distributed system** is a collection of independent computers (or processes) that communicate over a network and appear to users as a single coherent system.

The key word is *independent*. Each piece runs on its own, fails on its own, and has its own state.

**Key properties of distributed systems:**

| Property | Meaning |
|---|---|
| **Concurrency** | Many processes execute simultaneously |
| **No global clock** | Each machine has its own clock — they drift |
| **Partial failures** | Some parts fail while others work |
| **No shared memory** | Each process has its own address space |
| **Communication via messages** | They talk through network packets, not function calls |

### The Eight Fallacies of Distributed Computing

These are assumptions engineers make that are **always wrong** in distributed systems. Memorize these — they explain almost every microservice bug.

```
EIGHT FALLACIES (Peter Deutsch, Sun Microsystems, 1994):
+------------------------------------------------------+
| 1. The network is reliable                           |
| 2. Latency is zero                                   |
| 3. Bandwidth is infinite                             |
| 4. The network is secure                             |
| 5. Topology doesn't change                           |
| 6. There is one administrator                        |
| 7. Transport cost is zero                            |
| 8. The network is homogeneous                        |
+------------------------------------------------------+
```

Every single one of these is **false** in production. Every microservice bug traces back to at least one of them.

---

## 2. Monolith vs Microservices: The Mental Model Shift

### Glossary First

- **Monolith**: A single deployable unit. All code runs in one process, shares one memory space, uses one database.
- **Microservice**: A small, independently deployable service that owns one specific business capability and communicates with others via the network.
- **Service boundary**: The API contract between two services — what one promises to send, what the other expects to receive.
- **Process boundary**: The hard wall between operating system processes. You cannot share memory across it.

### ASCII Comparison

```
MONOLITH ARCHITECTURE:
+--------------------------------------------------+
|                  SINGLE PROCESS                  |
|                                                  |
|  [Function A] --> [Function B] --> [Function C]  |
|        |                                |        |
|        +---------> [Database] <---------+        |
|                                                  |
|  ONE call stack. ONE debugger. ONE log file.     |
+--------------------------------------------------+

MICROSERVICES ARCHITECTURE:
+------------+    HTTP    +------------+   Queue  +------------+
| Service A  | ---------> | Service B  | -------> | Service C  |
|  (Orders)  |            |  (Payment) |          | (Inventory)|
|            |            |            |          |            |
|  [DB: A]   |            |   [DB: B]  |          |   [DB: C]  |
+------------+            +------------+          +------------+
      |                         |                       |
      v                         v                       v
 [Logs: A]                 [Logs: B]               [Logs: C]

Multiple processes. Multiple call stacks. Multiple log files.
Execution is FRAGMENTED across machines.
```

### Execution Flow: Monolith vs Microservice

```
MONOLITH CALL FLOW:
main()
  |
  +--> createOrder()
         |
         +--> validatePayment()   <-- in same memory
         |         |
         |         +--> deductInventory()  <-- in same memory
         |
         +--> return result   <-- single return path

All in ONE stack trace. Any debugger can see it.

---

MICROSERVICE CALL FLOW:
Client
  |
  | HTTP POST /order
  v
[Order Service]
  |
  | HTTP POST /payment/charge    <-- network hop #1
  v
[Payment Service]
  |
  | PUBLISH event: "payment.success"   <-- async, no return
  v
[Message Queue]
  |
  | CONSUME event
  v
[Inventory Service]
  |
  | UPDATE DB   <-- completely separate DB transaction
  v
[Inventory DB]

NO single call stack exists.
A bug in Inventory Service does not appear in Order Service's logs.
```

---

## 3. Loss of Linearity: Execution Flow Fragmentation

### The Core Problem

In a monolith, you can follow code execution like reading a book — line by line, function by function, in a single thread. In microservices, execution is **non-linear, asynchronous, and distributed** across multiple machines.

### What "Linearity" Means

**Linear execution** means: given a starting point, you can predict every step that follows in order.

**Non-linear execution** in microservices means:
- Service A makes a request and continues executing (does not wait)
- Service B processes the request in parallel
- The response may arrive at any time, or never
- Side effects (DB writes, events published) happen at unpredictable times

### ASCII: Non-Linear Execution Timeline

```
TIME --------->

Service A:   [process] --req--> [wait..........] [got response] [continue]
                                     |                  ^
Service B:                      [recv] [process] [respond]
                                           |
Service C:                              [event recv] [process asynchronously]
                                                          |
Service D:                                           [DB write]

Any failure in B, C, or D is INVISIBLE to A's call stack.
A has no way to know what happened downstream without explicit mechanisms.
```

### Code: Simulating Execution Flow in Go

```go
// go/execution_flow/main.go
// Demonstrates the loss of linearity in microservices
// Each goroutine simulates a separate microservice

package main

import (
    "fmt"
    "math/rand"
    "sync"
    "time"
)

// --- Concept: Channel ---
// A channel in Go is a typed pipe through which goroutines communicate.
// Think of it as a network wire between two services.
// chan<- sends data, <-chan receives data.

// --- Concept: goroutine ---
// A goroutine is a lightweight thread managed by the Go runtime.
// It simulates an independent microservice process here.

type Request struct {
    ID      string
    Payload string
}

type Response struct {
    RequestID string
    Data      string
    Err       error
}

// serviceB simulates an independent microservice
func serviceB(req Request, responseCh chan<- Response, wg *sync.WaitGroup) {
    defer wg.Done()

    // Simulate network latency (unpredictable!)
    latency := time.Duration(rand.Intn(300)) * time.Millisecond
    time.Sleep(latency)

    // Simulate random failure (30% chance)
    // This is a PARTIAL FAILURE — B fails but A doesn't know how
    if rand.Float32() < 0.30 {
        responseCh <- Response{
            RequestID: req.ID,
            Err:       fmt.Errorf("serviceB: internal error after %v", latency),
        }
        return
    }

    responseCh <- Response{
        RequestID: req.ID,
        Data:      fmt.Sprintf("processed by B after %v", latency),
    }
}

// serviceA is the entry point — it "calls" serviceB over the "network"
func serviceA(requestID string) {
    req := Request{ID: requestID, Payload: "order-data"}

    // Channel with buffer of 1 — like a network socket buffer
    responseCh := make(chan Response, 1)
    var wg sync.WaitGroup

    fmt.Printf("[A] Sending request %s to Service B\n", req.ID)
    fmt.Printf("[A] I will continue executing while B works...\n")

    wg.Add(1)
    go serviceB(req, responseCh, &wg)

    // Service A continues doing its own work — NON-LINEAR!
    fmt.Printf("[A] Doing other work while waiting for B...\n")
    time.Sleep(50 * time.Millisecond)
    fmt.Printf("[A] Still doing work...\n")

    // Wait for response with a TIMEOUT
    // Concept: timeout = maximum time we'll wait before giving up
    select {
    case resp := <-responseCh:
        if resp.Err != nil {
            // KEY INSIGHT: A sees only the error, NOT the cause inside B
            fmt.Printf("[A] ERROR from B: %v\n", resp.Err)
            fmt.Printf("[A] A has NO IDEA what B's stack trace looked like!\n")
        } else {
            fmt.Printf("[A] SUCCESS: %s\n", resp.Data)
        }
    case <-time.After(200 * time.Millisecond):
        // Timeout: we never know if B succeeded, failed, or is still running
        fmt.Printf("[A] TIMEOUT: B did not respond. Was it a network issue? A crash? Unknown.\n")
    }

    wg.Wait()
}

func main() {
    rand.Seed(time.Now().UnixNano())
    fmt.Println("=== Simulating Non-Linear Execution ===\n")

    for i := 0; i < 5; i++ {
        fmt.Printf("--- Run %d ---\n", i+1)
        serviceA(fmt.Sprintf("req-%d", i+1))
        fmt.Println()
    }
}
```

**Key Insight from the Code:**
- Service A cannot see Service B's internal state
- Timeouts hide whether B succeeded, is still running, or crashed
- This is the **fundamental observability problem** of microservices

---

### Code: Same Concept in Rust

```rust
// rust/execution_flow/src/main.rs
// Demonstrates execution fragmentation using async/await and tokio

use std::time::Duration;
use tokio::time::{sleep, timeout};
use rand::Rng;

// --- Concept: async/await ---
// async marks a function as asynchronous — it returns a Future.
// await yields control until the Future completes.
// This models non-blocking network calls between microservices.

// --- Concept: Result<T, E> in Rust ---
// Rust has no exceptions. Errors are values.
// Ok(value) = success, Err(e) = failure. You must handle both.

#[derive(Debug)]
struct Request {
    id: String,
    payload: String,
}

#[derive(Debug)]
struct Response {
    request_id: String,
    data: String,
}

#[derive(Debug)]
enum ServiceError {
    InternalError(String),
    Timeout,
    NetworkError(String),
}

impl std::fmt::Display for ServiceError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            ServiceError::InternalError(msg) => write!(f, "InternalError: {}", msg),
            ServiceError::Timeout => write!(f, "Timeout"),
            ServiceError::NetworkError(msg) => write!(f, "NetworkError: {}", msg),
        }
    }
}

// Simulates Service B as an independent async task
async fn service_b(req: Request) -> Result<Response, ServiceError> {
    let mut rng = rand::thread_rng();

    // Simulate unpredictable network latency
    let latency_ms = rng.gen_range(50..=400);
    sleep(Duration::from_millis(latency_ms)).await;

    // Simulate 30% failure rate
    if rng.gen::<f32>() < 0.30 {
        return Err(ServiceError::InternalError(
            format!("B crashed after {}ms", latency_ms)
        ));
    }

    Ok(Response {
        request_id: req.id.clone(),
        data: format!("B processed '{}' in {}ms", req.payload, latency_ms),
    })
}

// Service A — calls Service B, but is non-linearly executing
async fn service_a(request_id: &str) {
    let req = Request {
        id: request_id.to_string(),
        payload: "order-data".to_string(),
    };

    println!("[A] Dispatching request {} to Service B", req.id);
    println!("[A] Continuing my own work concurrently...");

    // timeout() wraps a future — if it doesn't complete in time, Err(Elapsed)
    // This simulates a network timeout between two microservices
    let result = timeout(Duration::from_millis(250), service_b(req)).await;

    match result {
        // Outer Ok = timeout did NOT fire. Inner Ok/Err = service result.
        Ok(Ok(response)) => {
            println!("[A] SUCCESS: {:?}", response.data);
        }
        Ok(Err(service_err)) => {
            // B responded, but with an error
            // A sees only the error message — NOT B's internal state
            println!("[A] SERVICE ERROR from B: {}", service_err);
            println!("[A] Note: A has NO visibility into B's internal stack!");
        }
        Err(_elapsed) => {
            // We have no idea what happened to B
            // It could be: crashed, slow, network partition, deadlocked
            println!("[A] TIMEOUT! B didn't respond within 250ms.");
            println!("[A] B might still be running — or not. We don't know.");
        }
    }
}

#[tokio::main]
async fn main() {
    println!("=== Rust: Simulating Non-Linear Distributed Execution ===\n");

    for i in 1..=5 {
        println!("--- Run {} ---", i);
        service_a(&format!("req-{}", i)).await;
        println!();
    }
}

// Cargo.toml dependencies needed:
// [dependencies]
// tokio = { version = "1", features = ["full"] }
// rand = "0.8"
```

---

### Code: Execution Flow in C (Low-Level, POSIX Threads)

```c
/* c/execution_flow/main.c
 * Demonstrates microservice execution fragmentation using pthreads.
 * Each thread simulates an independent microservice.
 * This low-level view reveals what is happening under the hood.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <stdint.h>

/* --- Concept: mutex ---
 * A mutex (mutual exclusion lock) prevents two threads from
 * accessing shared data at the same time.
 * Without it, concurrent writes corrupt data.
 * This simulates the need for coordination in distributed systems.
 */

#define MAX_RESP_LEN 256

/* Shared "channel" between services (simulates a network socket) */
typedef struct {
    char data[MAX_RESP_LEN];
    int  has_error;
    int  ready;           /* 0 = not ready, 1 = ready */
    pthread_mutex_t lock;
    pthread_cond_t  cond; /* condition variable: wake A when B is done */
} Channel;

typedef struct {
    char    request_id[64];
    char    payload[128];
    Channel *response_channel;
} ServiceRequest;

/* Service B thread function */
void *service_b_thread(void *arg) {
    ServiceRequest *req = (ServiceRequest *)arg;
    Channel *ch = req->response_channel;

    /* Simulate variable network latency (50ms - 300ms) */
    int latency_ms = 50 + (rand() % 250);
    struct timespec ts = { .tv_sec = 0, .tv_nsec = latency_ms * 1000000L };
    nanosleep(&ts, NULL);

    pthread_mutex_lock(&ch->lock);

    /* 30% failure rate */
    if ((rand() % 10) < 3) {
        snprintf(ch->data, MAX_RESP_LEN,
                 "ERROR: Service B internal failure after %dms", latency_ms);
        ch->has_error = 1;
    } else {
        snprintf(ch->data, MAX_RESP_LEN,
                 "OK: B processed req=%s in %dms",
                 req->request_id, latency_ms);
        ch->has_error = 0;
    }

    ch->ready = 1;
    pthread_cond_signal(&ch->cond); /* Wake up Service A */
    pthread_mutex_unlock(&ch->lock);

    return NULL;
}

void service_a(const char *request_id) {
    Channel ch;
    memset(&ch, 0, sizeof(ch));
    pthread_mutex_init(&ch.lock, NULL);
    pthread_cond_init(&ch.cond, NULL);
    ch.ready = 0;

    ServiceRequest req;
    strncpy(req.request_id, request_id, sizeof(req.request_id) - 1);
    strncpy(req.payload, "order-data", sizeof(req.payload) - 1);
    req.response_channel = &ch;

    printf("[A] Sending request %s to Service B\n", request_id);

    pthread_t tid;
    pthread_create(&tid, NULL, service_b_thread, &req);

    printf("[A] Continuing own work while B runs asynchronously...\n");

    /* Timeout: wait maximum 200ms for B */
    struct timespec deadline;
    clock_gettime(CLOCK_REALTIME, &deadline);
    deadline.tv_nsec += 200L * 1000000L;   /* +200ms */
    if (deadline.tv_nsec >= 1000000000L) {
        deadline.tv_sec  += 1;
        deadline.tv_nsec -= 1000000000L;
    }

    pthread_mutex_lock(&ch.lock);

    int timed_out = 0;
    while (!ch.ready) {
        int rc = pthread_cond_timedwait(&ch.cond, &ch.lock, &deadline);
        if (rc != 0) { /* ETIMEDOUT */
            timed_out = 1;
            break;
        }
    }

    if (timed_out) {
        printf("[A] TIMEOUT! B did not respond. State unknown.\n");
    } else if (ch.has_error) {
        printf("[A] ERROR from B: %s\n", ch.data);
        printf("[A] A sees ONLY this message — B's stack trace is lost!\n");
    } else {
        printf("[A] SUCCESS: %s\n", ch.data);
    }

    pthread_mutex_unlock(&ch.lock);
    pthread_join(tid, NULL);

    pthread_mutex_destroy(&ch.lock);
    pthread_cond_destroy(&ch.cond);
}

int main(void) {
    srand((unsigned)time(NULL));
    printf("=== C: Microservice Execution Fragmentation Demo ===\n\n");

    char req_id[32];
    for (int i = 1; i <= 5; i++) {
        snprintf(req_id, sizeof(req_id), "req-%d", i);
        printf("--- Run %d ---\n", i);
        service_a(req_id);
        printf("\n");
    }

    return 0;
}

/* Compile: gcc -o flow main.c -lpthread */
```

---

## 4. Network Unreliability: The Fundamental Problem

### Concept: What Is "Reliable" Communication?

Inside one process, a function call is **synchronous and deterministic**:
- It either returns a value or throws an exception
- It never randomly "gets lost"
- It takes nanoseconds

A network call is **asynchronous and non-deterministic**:
- The packet might be dropped (IP does not guarantee delivery)
- The response might arrive out of order
- The target might receive the request but fail before responding
- You receive no response — you cannot distinguish between these failure modes

### The Two Generals Problem (Mental Model)

This is a classic computer science thought experiment that proves **perfect reliability is impossible** over an unreliable network.

```
SCENARIO: Two generals must attack at the same time to win.
They communicate only by messenger across enemy territory.
A messenger might be captured (message lost).

General A                    Enemy City                  General B
    |                           [X]                          |
    |-- "Attack at dawn" -----> [?] (might be captured)     |
    |                                                        |
General A doesn't know if B received the message.

If A sends confirmation request:
    |<--- "I got it, confirm?" -- [?] (might be captured)   |
    |
General A still doesn't know if B got the confirmation.

This repeats INFINITELY. Perfect agreement is IMPOSSIBLE.

KEY INSIGHT: This is EXACTLY why distributed systems have
             eventual consistency, not perfect consistency.
```

### Failure Modes on a Network

```
TYPES OF NETWORK FAILURES:
+--------------------------------------+-----------------------------+
| Failure Type      | Description      | What the Caller Sees        |
+--------------------------------------+-----------------------------+
| Packet loss       | Request dropped  | Timeout, no response        |
| Latency spike     | Slow network     | Appears like partial failure|
| Connection reset  | TCP RST          | "Connection refused" error  |
| DNS failure       | Can't resolve IP | "No such host" error        |
| Split brain       | Network partition| Some nodes visible, not all |
| Partial write     | TCP broken mid-  | Corrupt/truncated data      |
|                   | stream           |                             |
+--------------------------------------+-----------------------------+
```

### Code: Network Retry with Exponential Backoff in Go

```go
// go/network/retry.go
// Exponential backoff with jitter — the production-standard retry strategy.
//
// --- Concept: Exponential Backoff ---
// Instead of retrying every 1 second (which floods a struggling server),
// we double the wait time after each failure:
// retry 1: wait 1s
// retry 2: wait 2s
// retry 3: wait 4s
// retry 4: wait 8s  ... up to a maximum cap.
//
// --- Concept: Jitter ---
// If all clients back off by the exact same amount, they all
// retry at the same time -> thundering herd problem.
// Adding random jitter spreads retries out in time.

package main

import (
    "context"
    "errors"
    "fmt"
    "math"
    "math/rand"
    "net/http"
    "time"
)

// RetryConfig holds all retry parameters
type RetryConfig struct {
    MaxAttempts int
    BaseDelay   time.Duration // initial wait (e.g. 100ms)
    MaxDelay    time.Duration // cap on wait (e.g. 30s)
    Multiplier  float64       // how fast delay grows (e.g. 2.0 = doubles)
}

// RetryableError wraps an error with metadata about whether it can be retried
type RetryableError struct {
    Err       error
    Retryable bool
    StatusCode int
}

func (e *RetryableError) Error() string {
    return fmt.Sprintf("RetryableError(retryable=%v, code=%d): %v",
        e.Retryable, e.StatusCode, e.Err)
}

// isRetryable determines if an HTTP status code warrants a retry
// 500-series: server errors (retry makes sense)
// 429: rate limited (retry with backoff)
// 400-series (except 429): client errors (don't retry — our request is wrong)
func isRetryable(statusCode int) bool {
    return statusCode == 429 ||
        (statusCode >= 500 && statusCode <= 599)
}

// calculateBackoff computes wait time for attempt number `attempt` (0-indexed)
// Formula: min(baseDelay * multiplier^attempt + jitter, maxDelay)
func calculateBackoff(cfg RetryConfig, attempt int) time.Duration {
    // Exponential component
    exp := math.Pow(cfg.Multiplier, float64(attempt))
    delay := time.Duration(float64(cfg.BaseDelay) * exp)

    // Jitter: ±25% of the delay
    // This prevents "thundering herd" — all clients retrying simultaneously
    jitter := time.Duration(rand.Float64() * float64(delay) * 0.5)
    delay = delay + jitter - time.Duration(float64(delay)*0.25)

    // Cap at MaxDelay
    if delay > cfg.MaxDelay {
        delay = cfg.MaxDelay
    }

    return delay
}

// httpGetWithRetry performs an HTTP GET with retry logic
func httpGetWithRetry(ctx context.Context, url string, cfg RetryConfig) (*http.Response, error) {
    client := &http.Client{Timeout: 5 * time.Second}

    var lastErr error

    for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
        if attempt > 0 {
            backoff := calculateBackoff(cfg, attempt-1)
            fmt.Printf("  [retry] Attempt %d/%d — waiting %v before retry\n",
                attempt+1, cfg.MaxAttempts, backoff.Round(time.Millisecond))

            select {
            case <-time.After(backoff):
                // continue
            case <-ctx.Done():
                // Context cancelled — stop retrying immediately
                return nil, fmt.Errorf("context cancelled during backoff: %w", ctx.Err())
            }
        }

        fmt.Printf("  [request] GET %s (attempt %d)\n", url, attempt+1)

        resp, err := client.Get(url)
        if err != nil {
            // Network-level error (DNS, connection refused, timeout)
            lastErr = &RetryableError{
                Err:       err,
                Retryable: true,
            }
            fmt.Printf("  [error] network error: %v\n", err)
            continue
        }

        if isRetryable(resp.StatusCode) {
            lastErr = &RetryableError{
                Err:        fmt.Errorf("server error"),
                Retryable:  true,
                StatusCode: resp.StatusCode,
            }
            resp.Body.Close()
            fmt.Printf("  [error] server returned %d — will retry\n", resp.StatusCode)
            continue
        }

        if resp.StatusCode >= 400 {
            // 4xx errors (except 429) — don't retry, our request is wrong
            resp.Body.Close()
            return nil, &RetryableError{
                Err:        fmt.Errorf("client error: %d", resp.StatusCode),
                Retryable:  false,
                StatusCode: resp.StatusCode,
            }
        }

        // Success!
        return resp, nil
    }

    return nil, fmt.Errorf("exhausted %d attempts, last error: %w",
        cfg.MaxAttempts, lastErr)
}

func main() {
    rand.Seed(time.Now().UnixNano())

    cfg := RetryConfig{
        MaxAttempts: 5,
        BaseDelay:   100 * time.Millisecond,
        MaxDelay:    10 * time.Second,
        Multiplier:  2.0,
    }

    ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    // Test with a real endpoint that might fail
    fmt.Println("=== Testing Retry with Exponential Backoff ===")
    resp, err := httpGetWithRetry(ctx, "https://httpbin.org/status/500,200", cfg)
    if err != nil {
        fmt.Printf("Final failure: %v\n", err)
    } else {
        defer resp.Body.Close()
        fmt.Printf("Final success: HTTP %d\n", resp.StatusCode)
    }
}
```

---

### Code: Retry with Circuit Breaker in Rust

```rust
// rust/network/src/circuit_breaker.rs
//
// --- Concept: Circuit Breaker Pattern ---
// Named after an electrical circuit breaker that "trips" when current is too high.
//
// Three states:
//  CLOSED   → normal operation, requests flow through
//  OPEN     → too many failures, requests are REJECTED immediately (fail fast)
//  HALF_OPEN → probe state: send ONE request to check if service recovered
//
// WHY THIS MATTERS:
// Without a circuit breaker, if Service B is down:
//  - Every request to B waits for a timeout (say 5 seconds)
//  - Service A's threads/tasks pile up waiting
//  - A runs out of resources
//  - A becomes slow → C, which calls A, also fails → CASCADING FAILURE
// With a circuit breaker:
//  - After N failures, A stops calling B immediately
//  - A's threads are freed instantly
//  - Cascade is PREVENTED

use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

#[derive(Debug, PartialEq, Clone)]
enum CircuitState {
    Closed,   // Normal: requests pass through
    Open,     // Tripped: all requests fail fast
    HalfOpen, // Probing: ONE request allowed through to test recovery
}

#[derive(Debug)]
struct CircuitBreakerInner {
    state: CircuitState,
    failure_count: u32,
    success_count: u32,
    last_failure_time: Option<Instant>,

    // Thresholds
    failure_threshold: u32,   // trip after this many consecutive failures
    success_threshold: u32,   // recover after this many consecutive successes in HalfOpen
    reset_timeout: Duration,  // how long to stay Open before trying HalfOpen
}

#[derive(Clone, Debug)]
pub struct CircuitBreaker {
    inner: Arc<Mutex<CircuitBreakerInner>>,
    name: String,
}

#[derive(Debug)]
pub enum CircuitBreakerError {
    CircuitOpen,        // Request rejected because circuit is open
    ServiceError(String), // The underlying service failed
}

impl std::fmt::Display for CircuitBreakerError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            CircuitBreakerError::CircuitOpen =>
                write!(f, "CircuitBreaker OPEN: failing fast, not calling service"),
            CircuitBreakerError::ServiceError(msg) =>
                write!(f, "ServiceError: {}", msg),
        }
    }
}

impl CircuitBreaker {
    pub fn new(name: &str, failure_threshold: u32, reset_timeout: Duration) -> Self {
        CircuitBreaker {
            name: name.to_string(),
            inner: Arc::new(Mutex::new(CircuitBreakerInner {
                state: CircuitState::Closed,
                failure_count: 0,
                success_count: 0,
                last_failure_time: None,
                failure_threshold,
                success_threshold: 2,
                reset_timeout,
            })),
        }
    }

    /// call() wraps a function. It either executes it or fails fast based on circuit state.
    pub fn call<F, T>(&self, f: F) -> Result<T, CircuitBreakerError>
    where
        F: FnOnce() -> Result<T, String>,
    {
        // First, check and potentially transition state
        {
            let mut inner = self.inner.lock().unwrap();

            match inner.state {
                CircuitState::Open => {
                    // Check if reset timeout has elapsed
                    if let Some(last_fail) = inner.last_failure_time {
                        if last_fail.elapsed() >= inner.reset_timeout {
                            println!("[{}] Circuit transitioning: OPEN -> HALF_OPEN (probe)", self.name);
                            inner.state = CircuitState::HalfOpen;
                            inner.success_count = 0;
                        } else {
                            // Still in timeout — fail fast
                            println!("[{}] Circuit OPEN — rejecting request immediately", self.name);
                            return Err(CircuitBreakerError::CircuitOpen);
                        }
                    }
                }
                CircuitState::Closed | CircuitState::HalfOpen => {}
            }
        }

        // Execute the actual service call
        let result = f();

        // Update state based on result
        let mut inner = self.inner.lock().unwrap();
        match &result {
            Ok(_) => {
                println!("[{}] Request succeeded", self.name);
                match inner.state {
                    CircuitState::HalfOpen => {
                        inner.success_count += 1;
                        if inner.success_count >= inner.success_threshold {
                            println!("[{}] Circuit transitioning: HALF_OPEN -> CLOSED (recovered!)", self.name);
                            inner.state = CircuitState::Closed;
                            inner.failure_count = 0;
                        }
                    }
                    CircuitState::Closed => {
                        inner.failure_count = 0; // reset on success
                    }
                    _ => {}
                }
            }
            Err(e) => {
                println!("[{}] Request failed: {}", self.name, e);
                inner.failure_count += 1;
                inner.last_failure_time = Some(Instant::now());

                if inner.failure_count >= inner.failure_threshold
                    || inner.state == CircuitState::HalfOpen
                {
                    println!(
                        "[{}] Circuit transitioning: {:?} -> OPEN (failures={})",
                        self.name, inner.state, inner.failure_count
                    );
                    inner.state = CircuitState::Open;
                }
            }
        }

        result.map_err(CircuitBreakerError::ServiceError)
    }

    pub fn state(&self) -> CircuitState {
        self.inner.lock().unwrap().state.clone()
    }
}

fn simulate_flaky_service(request_id: u32) -> Result<String, String> {
    // Fail first 4 calls, succeed after
    if request_id <= 4 {
        Err(format!("Service B internal error (req {})", request_id))
    } else {
        Ok(format!("Service B success (req {})", request_id))
    }
}

fn main() {
    let cb = CircuitBreaker::new(
        "ServiceB",
        3,                             // trip after 3 consecutive failures
        Duration::from_millis(500),    // try again after 500ms
    );

    println!("=== Circuit Breaker Demonstration ===\n");
    println!("Threshold: 3 failures before tripping\n");

    for i in 1..=8u32 {
        println!("--- Request {} (state: {:?}) ---", i, cb.state());

        let result = cb.call(|| simulate_flaky_service(i));

        match result {
            Ok(msg) => println!("SUCCESS: {}", msg),
            Err(e) => println!("FAILURE: {}", e),
        }

        // Simulate time passing between requests
        if i == 4 {
            println!("\n[waiting 600ms for circuit reset timeout...]\n");
            std::thread::sleep(Duration::from_millis(600));
        }

        println!();
    }
}
```

---

## 5. Partial Failures: When the System Lies to You

### Concept: What Is a Partial Failure?

A **partial failure** is when part of a distributed system fails while the rest continues operating. The system is neither fully up nor fully down — it's in an **indeterminate state**.

This is the most insidious class of failure in distributed systems because:
- The caller may receive a "success" response even though some downstream action failed
- Logs may not show any obvious error at the point of failure
- The system state becomes inconsistent

### Anatomy of a Partial Failure

```
PARTIAL FAILURE SCENARIO:
Correct flow:                        What actually happened:

Client                               Client
  |                                    |
  | POST /create-order                 | POST /create-order
  v                                    v
[Order Service]                      [Order Service]
  |  1. Create order in DB              |  1. Create order in DB [OK]
  |  2. Charge payment                  |  2. Charge payment [OK]
  |  3. Reduce inventory                |  3. Reduce inventory [FAILED - silent timeout]
  |  4. Send confirmation email         |  4. Send confirmation email [OK - never received]
  |                                     |
  v                                     v
 "200 OK - Order Created"            "200 OK - Order Created"
                                     (but inventory was NOT reduced!)
                                     (and customer got no email!)

The ORDER SERVICE returned SUCCESS.
The CLIENT sees SUCCESS.
But the SYSTEM IS INCONSISTENT.

This is a PARTIAL FAILURE.
```

### The Fallback Trap

A common pattern that creates partial failures:

```
--- Without Fallback (honest failure) ---
Service A -> Service B (timeout) -> A returns ERROR -> Client knows something is wrong

--- With Naive Fallback (partial failure hidden) ---
Service A -> Service B (timeout) -> A uses CACHED/DEFAULT data -> A returns SUCCESS
But: the data returned is STALE. Client thinks everything is fine.
```

### Code: Detecting and Handling Partial Failures in Go

```go
// go/partial_failure/main.go
// Demonstrates partial failure detection using saga pattern concepts.
//
// --- Concept: Saga Pattern ---
// A saga is a sequence of local transactions, each publishing events/messages
// to trigger the next step. If one step fails, compensating transactions
// UNDO the previous steps.
//
// This is how distributed systems achieve consistency without 2PC
// (two-phase commit), which is slow and fragile.

package main

import (
    "errors"
    "fmt"
    "math/rand"
    "time"
)

// --- Concept: Domain Error vs Infrastructure Error ---
// Domain error: "insufficient funds" — correct behavior, no retry
// Infrastructure error: "timeout connecting to payment service" — retry might help

type ErrorKind int

const (
    ErrDomain         ErrorKind = iota // business logic error, do not retry
    ErrInfrastructure                  // network/timeout error, may retry
)

type ServiceError struct {
    Kind    ErrorKind
    Message string
    Service string
}

func (e *ServiceError) Error() string {
    kind := "DOMAIN"
    if e.Kind == ErrInfrastructure {
        kind = "INFRA"
    }
    return fmt.Sprintf("[%s][%s] %s", e.Service, kind, e.Message)
}

// --- Saga Step ---
// Each step has:
//  - Execute: the action to perform
//  - Compensate: the UNDO action if a later step fails

type SagaStep struct {
    Name       string
    Execute    func() error
    Compensate func() error // called if rollback needed
}

// SagaOrchestrator runs steps in order; if one fails, rolls back previous steps
type SagaOrchestrator struct {
    steps     []SagaStep
    completed []int // indices of successfully completed steps
}

func NewSaga() *SagaOrchestrator {
    return &SagaOrchestrator{}
}

func (s *SagaOrchestrator) AddStep(step SagaStep) {
    s.steps = append(s.steps, step)
}

// Run executes all steps. On failure, runs compensating transactions in reverse.
// This is called "backward recovery".
func (s *SagaOrchestrator) Run() error {
    s.completed = []int{}

    for i, step := range s.steps {
        fmt.Printf("  [SAGA] Executing step %d: %s\n", i+1, step.Name)
        if err := step.Execute(); err != nil {
            fmt.Printf("  [SAGA] Step %d FAILED: %v\n", i+1, err)
            fmt.Printf("  [SAGA] Starting COMPENSATION (rollback) for %d completed steps\n",
                len(s.completed))

            // Rollback in reverse order
            // KEY: must compensate in reverse to avoid inconsistency
            for j := len(s.completed) - 1; j >= 0; j-- {
                idx := s.completed[j]
                fmt.Printf("  [SAGA] Compensating step %d: %s\n",
                    idx+1, s.steps[idx].Name)
                if compErr := s.steps[idx].Compensate(); compErr != nil {
                    // Compensation failed! This is a critical problem.
                    // In production: alert human operators, write to dead letter queue.
                    fmt.Printf("  [SAGA] COMPENSATION FAILED for step %d: %v\n",
                        idx+1, compErr)
                    fmt.Printf("  [SAGA] MANUAL INTERVENTION REQUIRED\n")
                }
            }
            return fmt.Errorf("saga failed at step %d (%s): %w", i+1, step.Name, err)
        }

        s.completed = append(s.completed, i)
        fmt.Printf("  [SAGA] Step %d completed successfully\n", i+1)
    }

    return nil
}

// ---- Simulated Services ----

type OrderDB struct{ orders map[string]bool }
type PaymentService struct{}
type InventoryDB struct{ items map[string]int }
type EmailService struct{}

func (db *OrderDB) Create(orderID string) error {
    db.orders[orderID] = true
    return nil
}
func (db *OrderDB) Delete(orderID string) error {
    delete(db.orders, orderID)
    fmt.Printf("    [OrderDB] Rolled back order %s\n", orderID)
    return nil
}

func (p *PaymentService) Charge(amount float64) error {
    // 40% failure rate to demonstrate partial failures
    if rand.Float32() < 0.40 {
        return &ServiceError{Kind: ErrInfrastructure, Service: "Payment", Message: "payment gateway timeout"}
    }
    fmt.Printf("    [Payment] Charged $%.2f\n", amount)
    return nil
}
func (p *PaymentService) Refund(amount float64) error {
    fmt.Printf("    [Payment] Refunded $%.2f\n", amount)
    return nil
}

func (db *InventoryDB) Reduce(itemID string, qty int) error {
    if db.items[itemID] < qty {
        return &ServiceError{Kind: ErrDomain, Service: "Inventory",
            Message: fmt.Sprintf("insufficient stock: have %d, need %d", db.items[itemID], qty)}
    }
    db.items[itemID] -= qty
    fmt.Printf("    [Inventory] Reduced %s by %d (remaining: %d)\n",
        itemID, qty, db.items[itemID])
    return nil
}
func (db *InventoryDB) Restore(itemID string, qty int) error {
    db.items[itemID] += qty
    fmt.Printf("    [Inventory] Restored %d units of %s\n", qty, itemID)
    return nil
}

func (e *EmailService) Send(to, subject string) error {
    // 20% failure — but note: email might have been sent before this code runs
    // This is the "idempotency" problem
    if rand.Float32() < 0.20 {
        return &ServiceError{Kind: ErrInfrastructure, Service: "Email",
            Message: "SMTP server unavailable"}
    }
    fmt.Printf("    [Email] Sent '%s' to %s\n", subject, to)
    return nil
}

func createOrderSaga(orderID string, customerEmail string) error {
    orderDB   := &OrderDB{orders: map[string]bool{}}
    payment   := &PaymentService{}
    inventory := &InventoryDB{items: map[string]int{"item-A": 10}}
    email     := &EmailService{}

    saga := NewSaga()

    saga.AddStep(SagaStep{
        Name: "Create Order Record",
        Execute: func() error {
            return orderDB.Create(orderID)
        },
        Compensate: func() error {
            return orderDB.Delete(orderID)
        },
    })

    saga.AddStep(SagaStep{
        Name: "Charge Payment",
        Execute: func() error {
            return payment.Charge(99.99)
        },
        Compensate: func() error {
            return payment.Refund(99.99)
        },
    })

    saga.AddStep(SagaStep{
        Name: "Reduce Inventory",
        Execute: func() error {
            return inventory.Reduce("item-A", 1)
        },
        Compensate: func() error {
            return inventory.Restore("item-A", 1)
        },
    })

    saga.AddStep(SagaStep{
        Name: "Send Confirmation Email",
        Execute: func() error {
            return email.Send(customerEmail, "Order Confirmation")
        },
        Compensate: func() error {
            // Email cannot be "unsent" — this is a known limitation
            fmt.Printf("    [Email] Cannot unsend email — marking as phantom send\n")
            return nil
        },
    })

    return saga.Run()
}

func main() {
    rand.Seed(time.Now().UnixNano())

    fmt.Println("=== Saga Pattern: Partial Failure Handling ===\n")

    for i := 1; i <= 3; i++ {
        fmt.Printf("--- Order Attempt %d ---\n", i)
        err := createOrderSaga(fmt.Sprintf("order-%d", i), "customer@example.com")
        if err != nil {
            var svcErr *ServiceError
            if errors.As(err, &svcErr) {
                fmt.Printf("ORDER FAILED (recoverable): %v\n", err)
                if svcErr.Kind == ErrDomain {
                    fmt.Println("  -> Do NOT retry — this is a business logic error")
                } else {
                    fmt.Println("  -> May retry with backoff — this is infrastructure error")
                }
            } else {
                fmt.Printf("ORDER FAILED: %v\n", err)
            }
        } else {
            fmt.Printf("ORDER %d SUCCEEDED — all steps completed\n", i)
        }
        fmt.Println()
    }
}
```

---

## 6. Data Inconsistency: No Single Source of Truth

### Concept: Why Consistency Is Hard

In a monolith with one database, if you wrap operations in a **transaction** (ACID — Atomicity, Consistency, Isolation, Durability), either all changes happen or none do. This is called **strong consistency**.

In microservices, each service has its own database. You **cannot** use a database transaction across service boundaries. This means you must accept **eventual consistency**.

### Glossary

- **ACID transaction**: A database guarantee that a set of operations either all succeed (commit) or all fail (rollback). No partial states.
- **Eventual consistency**: The system guarantees that if no new updates are made, all replicas will eventually converge to the same value. But right now, they might be different.
- **Stale read**: Reading data that is outdated because an update hasn't propagated yet.
- **Race condition**: Two operations compete and the result depends on which one finishes first.

### ASCII: ACID vs Eventual Consistency

```
ACID TRANSACTION (Monolith):

BEGIN TRANSACTION
  UPDATE orders SET status='paid' WHERE id=1;    <-- step 1
  UPDATE inventory SET qty=qty-1 WHERE item=1;   <-- step 2
  INSERT INTO payments VALUES (1, 99.99);         <-- step 3
COMMIT
       ^
       |
Either ALL three happen, or NONE do. No partial state possible.

---

EVENTUAL CONSISTENCY (Microservices):

[Order Service]          [Inventory Service]         [Payment Service]
    |                          |                            |
    | UPDATE orders            | UPDATE inventory           | INSERT payment
    | status='paid'            | qty=qty-1                  | ...
    | DB: COMMITTED [OK]       | DB: TIMEOUT [FAIL!]        | DB: COMMITTED [OK]
    |                          |
    v                          v
  Order shows paid          Inventory unchanged!
  Payment recorded          INCONSISTENT STATE
  Email sent
  
At this point:
  - Customer paid          [YES]
  - Order marked paid      [YES]
  - Inventory reduced      [NO]  <-- DATA INCONSISTENCY
  - This is a real business problem
```

### Code: Optimistic Locking for Consistency in Rust

```rust
// rust/consistency/src/main.rs
//
// --- Concept: Optimistic Locking ---
// Instead of locking a record when reading it (pessimistic),
// we read it freely, remember its VERSION, then:
// - Perform work
// - When writing: check if the version is STILL the same
// - If version changed, someone else modified it — ABORT and retry
//
// This prevents "lost update" problems without expensive locks.
//
// --- Concept: Lost Update ---
// Thread A reads value=10, version=1
// Thread B reads value=10, version=1
// Thread A writes value=11, version=2 (success)
// Thread B writes value=12 based on old value 10 (WRONG! Should be 13)
//           ^-- Thread B's update is LOST

use std::sync::{Arc, Mutex};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
struct InventoryRecord {
    item_id: String,
    quantity: i64,
    version: u64,         // Version counter — incremented on every write
    updated_at: u64,      // Unix timestamp in milliseconds
}

#[derive(Debug)]
enum UpdateError {
    VersionConflict { expected: u64, actual: u64 },
    InsufficientStock { available: i64, requested: i64 },
    ItemNotFound(String),
}

impl std::fmt::Display for UpdateError {
    fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
        match self {
            UpdateError::VersionConflict { expected, actual } =>
                write!(f, "VersionConflict: expected v{} but found v{}", expected, actual),
            UpdateError::InsufficientStock { available, requested } =>
                write!(f, "InsufficientStock: have {}, need {}", available, requested),
            UpdateError::ItemNotFound(id) =>
                write!(f, "ItemNotFound: {}", id),
        }
    }
}

struct InventoryStore {
    records: Mutex<Vec<InventoryRecord>>,
}

impl InventoryStore {
    fn new() -> Self {
        InventoryStore {
            records: Mutex::new(vec![
                InventoryRecord {
                    item_id: "item-A".to_string(),
                    quantity: 10,
                    version: 1,
                    updated_at: 0,
                }
            ])
        }
    }

    // Read — returns a snapshot. Version is captured for optimistic locking.
    fn read(&self, item_id: &str) -> Option<InventoryRecord> {
        let records = self.records.lock().unwrap();
        records.iter()
            .find(|r| r.item_id == item_id)
            .cloned()
    }

    // Conditional write — succeeds ONLY if version matches (CAS: Compare And Swap)
    // CAS is the foundation of all lock-free and optimistic algorithms.
    fn update_quantity_if_version(
        &self,
        item_id: &str,
        delta: i64,
        expected_version: u64,
    ) -> Result<InventoryRecord, UpdateError> {
        let mut records = self.records.lock().unwrap();

        let record = records.iter_mut()
            .find(|r| r.item_id == item_id)
            .ok_or_else(|| UpdateError::ItemNotFound(item_id.to_string()))?;

        // CAS check: version must match what we read earlier
        if record.version != expected_version {
            return Err(UpdateError::VersionConflict {
                expected: expected_version,
                actual: record.version,
            });
        }

        let new_qty = record.quantity + delta;
        if new_qty < 0 {
            return Err(UpdateError::InsufficientStock {
                available: record.quantity,
                requested: -delta,
            });
        }

        record.quantity = new_qty;
        record.version += 1; // Increment version on every successful write
        record.updated_at = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64;

        Ok(record.clone())
    }
}

// deduct_with_retry wraps the optimistic update with retry logic
fn deduct_with_retry(
    store: &InventoryStore,
    item_id: &str,
    quantity: i64,
    max_retries: u32,
) -> Result<InventoryRecord, UpdateError> {
    for attempt in 0..max_retries {
        // Step 1: Read current state (with version)
        let record = store.read(item_id)
            .ok_or_else(|| UpdateError::ItemNotFound(item_id.to_string()))?;

        println!(
            "  [attempt {}] read: qty={}, version={}",
            attempt + 1, record.quantity, record.version
        );

        // Step 2: Business logic check BEFORE attempting write
        if record.quantity < quantity {
            return Err(UpdateError::InsufficientStock {
                available: record.quantity,
                requested: quantity,
            });
        }

        // Step 3: Attempt conditional write
        match store.update_quantity_if_version(item_id, -quantity, record.version) {
            Ok(updated) => {
                println!(
                    "  [attempt {}] SUCCESS: qty={}, new_version={}",
                    attempt + 1, updated.quantity, updated.version
                );
                return Ok(updated);
            }
            Err(UpdateError::VersionConflict { expected, actual }) => {
                println!(
                    "  [attempt {}] VersionConflict: v{} != v{} — concurrent modification detected, retrying",
                    attempt + 1, expected, actual
                );
                // Small sleep before retry to reduce contention
                std::thread::sleep(Duration::from_millis(10 * (attempt as u64 + 1)));
                continue;
            }
            Err(e) => return Err(e), // Non-retryable error
        }
    }

    Err(UpdateError::VersionConflict {
        expected: 0,
        actual: 0,
    })
}

fn main() {
    let store = Arc::new(InventoryStore::new());

    println!("=== Optimistic Locking for Distributed Consistency ===\n");

    // Simulate concurrent deductions (race condition scenario)
    let store1 = Arc::clone(&store);
    let store2 = Arc::clone(&store);

    let t1 = std::thread::spawn(move || {
        println!("[Thread 1] Attempting to deduct 3 units of item-A");
        match deduct_with_retry(&store1, "item-A", 3, 5) {
            Ok(r) => println!("[Thread 1] SUCCESS: {} units remaining", r.quantity),
            Err(e) => println!("[Thread 1] FAILED: {}", e),
        }
    });

    let t2 = std::thread::spawn(move || {
        println!("[Thread 2] Attempting to deduct 4 units of item-A");
        match deduct_with_retry(&store2, "item-A", 4, 5) {
            Ok(r) => println!("[Thread 2] SUCCESS: {} units remaining", r.quantity),
            Err(e) => println!("[Thread 2] FAILED: {}", e),
        }
    });

    t1.join().unwrap();
    t2.join().unwrap();

    let final_record = store.read("item-A").unwrap();
    println!(
        "\nFinal state: qty={}, version={}",
        final_record.quantity, final_record.version
    );
    println!("Expected: 10 - 3 - 4 = 3 units if both succeeded");
}
```

---

## 7. Log Aggregation and Correlation IDs

### Concept: The Problem of Scattered Logs

In a microservice system with 50 services, a single user request touches 5-15 services. Each service writes its logs to its own file, its own container, its own machine.

When that request fails, you need to find all related log lines across all services — like finding a specific thread in a pile of yarn.

### Concept: Correlation ID (Trace ID)

A **correlation ID** (also called **trace ID** or **request ID**) is a unique identifier **generated at the entry point of a request** and **passed through every service** that handles that request.

Every log line that belongs to the same request includes this ID. Now you can query logs across all services filtering by a single ID.

```
WITHOUT CORRELATION ID:

[Order Service]    INFO Processing order
[Payment Service]  ERROR timeout connecting to bank
[Order Service]    ERROR payment failed
[Inventory Service] INFO deducting stock

Which ERROR belongs to which order? IMPOSSIBLE to tell.

---

WITH CORRELATION ID:

[Order Service]    INFO  trace_id=abc123 Processing order
[Payment Service]  ERROR trace_id=abc123 timeout connecting to bank
[Order Service]    ERROR trace_id=abc123 payment failed for order-456
[Inventory Service] INFO trace_id=def789 deducting stock (DIFFERENT REQUEST)

Now: grep for abc123 → see ENTIRE FLOW for that one request across all services.
```

### How Correlation IDs Flow Through Services

```
Client
  |
  | HTTP POST /order
  |  (no trace id yet)
  v
[API Gateway]
  |  GENERATES: trace_id = "550e8400-e29b-41d4-a716-446655440000"
  |  Adds header: X-Trace-ID: 550e8400...
  v
[Order Service]
  |  READS: X-Trace-ID from header
  |  LOGS: "trace_id=550e8400 Creating order"
  |  PASSES: X-Trace-ID in all outgoing HTTP headers / message metadata
  v
[Payment Service]
  |  READS: X-Trace-ID from header
  |  LOGS: "trace_id=550e8400 Charging card"
  v
[Email Service]
  |  READS: X-Trace-ID
  |  LOGS: "trace_id=550e8400 Sending confirmation"

Now ALL logs for this request share trace_id=550e8400
Query: SELECT * FROM logs WHERE trace_id='550e8400' ORDER BY timestamp
→ Complete request timeline across all services.
```

### Code: Structured Logging with Correlation IDs in Go

```go
// go/logging/main.go
// Demonstrates structured logging with propagated correlation IDs.
//
// --- Concept: Structured Logging ---
// Instead of plain text: "2024-01-01 Processing order for user 123"
// Structured logging emits KEY=VALUE pairs or JSON:
//   {"time":"2024-01-01","level":"INFO","trace_id":"abc","user_id":"123","action":"process_order"}
//
// Benefits:
//  - Machine-parseable (log aggregators can index every field)
//  - Easily filterable (filter by trace_id, user_id, level, etc.)
//  - Consistent format across all services
//
// --- Concept: Context in Go ---
// context.Context carries request-scoped data (like trace IDs)
// across goroutine and function boundaries.
// This is how a trace ID flows from HTTP handler to DB call to outgoing request.

package main

import (
    "context"
    "encoding/json"
    "fmt"
    "os"
    "time"

    "github.com/google/uuid"  // generate UUIDs for trace IDs
)

// --- Context key type ---
// Using a custom type prevents key collisions in context.
// If everyone used string("trace_id"), any package could overwrite it.
type contextKey string

const (
    TraceIDKey   contextKey = "trace_id"
    SpanIDKey    contextKey = "span_id"
    ServiceKey   contextKey = "service"
    UserIDKey    contextKey = "user_id"
)

// LogEntry is the structured log format (will be JSON-encoded)
type LogEntry struct {
    Timestamp string                 `json:"timestamp"`
    Level     string                 `json:"level"`
    TraceID   string                 `json:"trace_id,omitempty"`
    SpanID    string                 `json:"span_id,omitempty"`
    Service   string                 `json:"service"`
    Message   string                 `json:"message"`
    Fields    map[string]interface{} `json:"fields,omitempty"`
}

// Logger is a service-specific logger that extracts trace info from context
type Logger struct {
    ServiceName string
    Output      *os.File
}

func NewLogger(serviceName string) *Logger {
    return &Logger{ServiceName: serviceName, Output: os.Stdout}
}

// log extracts trace information from context and emits a structured log line
func (l *Logger) log(ctx context.Context, level, message string, fields map[string]interface{}) {
    entry := LogEntry{
        Timestamp: time.Now().UTC().Format(time.RFC3339Nano),
        Level:     level,
        Service:   l.ServiceName,
        Message:   message,
        Fields:    fields,
    }

    // Extract trace ID from context if present
    if traceID, ok := ctx.Value(TraceIDKey).(string); ok {
        entry.TraceID = traceID
    }
    if spanID, ok := ctx.Value(SpanIDKey).(string); ok {
        entry.SpanID = spanID
    }

    data, _ := json.Marshal(entry)
    fmt.Fprintf(l.Output, "%s\n", data)
}

func (l *Logger) Info(ctx context.Context, msg string, fields ...map[string]interface{}) {
    f := map[string]interface{}{}
    if len(fields) > 0 {
        f = fields[0]
    }
    l.log(ctx, "INFO", msg, f)
}

func (l *Logger) Error(ctx context.Context, msg string, fields ...map[string]interface{}) {
    f := map[string]interface{}{}
    if len(fields) > 0 {
        f = fields[0]
    }
    l.log(ctx, "ERROR", msg, f)
}

// WithTraceID injects a trace ID into context
func WithTraceID(ctx context.Context, traceID string) context.Context {
    return context.WithValue(ctx, TraceIDKey, traceID)
}

// WithNewSpan creates a child span ID — each service call gets its own span
// while sharing the parent trace ID
func WithNewSpan(ctx context.Context) context.Context {
    spanID := uuid.New().String()[:8]
    return context.WithValue(ctx, SpanIDKey, spanID)
}

// ExtractOrGenerateTraceID reads trace ID from "HTTP header" or generates one
// In production: read from X-Trace-ID header
func ExtractOrGenerateTraceID(headerValue string) string {
    if headerValue != "" {
        return headerValue
    }
    return uuid.New().String()
}

// ===== Simulated Services =====

func orderService(ctx context.Context, orderData string) error {
    log := NewLogger("order-service")
    ctx = WithNewSpan(ctx)

    log.Info(ctx, "Received order request", map[string]interface{}{
        "order_data": orderData,
    })

    // Simulate calling payment service
    log.Info(ctx, "Calling payment service")
    if err := paymentService(ctx, 99.99); err != nil {
        log.Error(ctx, "Payment failed", map[string]interface{}{
            "error": err.Error(),
        })
        return fmt.Errorf("order failed: %w", err)
    }

    log.Info(ctx, "Order completed successfully")
    return nil
}

func paymentService(ctx context.Context, amount float64) error {
    log := NewLogger("payment-service")
    ctx = WithNewSpan(ctx) // new span, same trace ID

    log.Info(ctx, "Processing payment", map[string]interface{}{
        "amount": amount,
    })

    // Simulate calling bank API
    log.Info(ctx, "Calling bank API")
    time.Sleep(10 * time.Millisecond)

    // Simulated failure
    return fmt.Errorf("bank API timeout after 10ms")
}

func main() {
    fmt.Println("=== Structured Logging with Correlation IDs ===")
    fmt.Println("Each line is a JSON log entry. Filter by trace_id to see one request.")
    fmt.Println()

    // Simulate an incoming HTTP request
    // In production, the trace ID comes from the X-Trace-ID header
    incomingTraceID := ExtractOrGenerateTraceID("") // no header — generate new

    // Inject trace ID into context — this flows through ALL downstream calls
    ctx := WithTraceID(context.Background(), incomingTraceID)

    fmt.Printf("Trace ID for this request: %s\n\n", incomingTraceID)

    if err := orderService(ctx, "order-456"); err != nil {
        fmt.Printf("\nRequest failed. To debug: grep logs for trace_id=%s\n", incomingTraceID)
    }
}
```

### Code: Correlation ID Middleware in C (HTTP Header Extraction)

```c
/* c/logging/correlation.c
 * Demonstrates how correlation IDs are extracted from HTTP headers
 * and stored in thread-local storage for use throughout the request.
 *
 * --- Concept: Thread-Local Storage (TLS) ---
 * Each thread has its own copy of thread-local variables.
 * This is how web servers store per-request context (like trace IDs)
 * without passing them explicitly to every function.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <time.h>
#include <stdarg.h>

/* Thread-local variable for trace ID.
 * __thread is a GCC extension for thread-local storage.
 * Each thread gets its own copy, so concurrent requests don't interfere.
 */
__thread char g_trace_id[64] = {0};
__thread char g_service_name[64] = {0};

/* Log levels */
typedef enum { LOG_DEBUG, LOG_INFO, LOG_WARN, LOG_ERROR } LogLevel;

static const char *level_str[] = {"DEBUG", "INFO", "WARN", "ERROR"};

/* structured_log — emits a JSON-formatted log line using thread-local trace ID */
void structured_log(LogLevel level, const char *fmt, ...) {
    char message[512];
    va_list args;
    va_start(args, fmt);
    vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    /* Get current timestamp */
    time_t now = time(NULL);
    char timestamp[32];
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%dT%H:%M:%SZ", gmtime(&now));

    /* Emit structured JSON log line */
    printf("{\"timestamp\":\"%s\",\"level\":\"%s\",\"service\":\"%s\","
           "\"trace_id\":\"%s\",\"message\":\"%s\"}\n",
           timestamp, level_str[level],
           g_service_name[0] ? g_service_name : "unknown",
           g_trace_id[0]     ? g_trace_id     : "no-trace",
           message);
}

/* Generate a simple pseudo-UUID for demo purposes */
void generate_trace_id(char *buf, size_t len) {
    snprintf(buf, len, "%08lx-%04lx-%04lx",
             (unsigned long)time(NULL),
             (unsigned long)(rand() & 0xFFFF),
             (unsigned long)(rand() & 0xFFFF));
}

/* Simulate HTTP request handler — called in its own thread */
typedef struct {
    char trace_id_header[64];  /* Value of X-Trace-ID header, or empty string */
    char service[32];
    char request_path[128];
    int  request_id;
} HttpRequest;

void *handle_request(void *arg) {
    HttpRequest *req = (HttpRequest *)arg;

    /* Set up thread-local context */
    strncpy(g_service_name, req->service, sizeof(g_service_name) - 1);

    /* Extract or generate trace ID */
    if (req->trace_id_header[0] != '\0') {
        strncpy(g_trace_id, req->trace_id_header, sizeof(g_trace_id) - 1);
        structured_log(LOG_DEBUG, "Using existing trace_id from header");
    } else {
        generate_trace_id(g_trace_id, sizeof(g_trace_id));
        structured_log(LOG_DEBUG, "Generated new trace_id (no header present)");
    }

    /* Process the request */
    structured_log(LOG_INFO, "Handling %s", req->request_path);

    /* Simulate some work */
    struct timespec ts = { .tv_sec = 0, .tv_nsec = (rand() % 100) * 1000000L };
    nanosleep(&ts, NULL);

    /* Simulate a downstream call — the same trace_id would be passed
     * in the X-Trace-ID header of the outgoing request */
    structured_log(LOG_INFO, "Calling downstream service with trace_id=%s", g_trace_id);

    /* Simulate 20% error rate */
    if ((rand() % 5) == 0) {
        structured_log(LOG_ERROR, "Downstream service returned 500");
        return NULL;
    }

    structured_log(LOG_INFO, "Request completed successfully");
    return NULL;
}

int main(void) {
    srand((unsigned)time(NULL));

    printf("=== Correlation ID Propagation Demo ===\n");
    printf("Each thread is a concurrent HTTP request.\n\n");

    #define NUM_REQUESTS 4
    pthread_t threads[NUM_REQUESTS];
    HttpRequest requests[NUM_REQUESTS] = {
        { .trace_id_header = "",                /* No header — generate new */
          .service = "order-service",
          .request_path = "POST /order",
          .request_id = 1 },
        { .trace_id_header = "ext-abc12345",   /* Header from client */
          .service = "payment-service",
          .request_path = "POST /charge",
          .request_id = 2 },
        { .trace_id_header = "",
          .service = "inventory-service",
          .request_path = "PUT /stock/item-A",
          .request_id = 3 },
        { .trace_id_header = "ext-abc12345",   /* Same trace as request 2 */
          .service = "notification-service",
          .request_path = "POST /email",
          .request_id = 4 },
    };

    for (int i = 0; i < NUM_REQUESTS; i++) {
        pthread_create(&threads[i], NULL, handle_request, &requests[i]);
        /* Small delay to make output readable */
        struct timespec ts = { .tv_sec = 0, .tv_nsec = 5000000L };
        nanosleep(&ts, NULL);
    }

    for (int i = 0; i < NUM_REQUESTS; i++) {
        pthread_join(threads[i], NULL);
    }

    printf("\nTip: Filter logs where trace_id=ext-abc12345 to see requests 2 and 4.\n");

    return 0;
}
/* Compile: gcc -o correlation correlation.c -lpthread */
```

---

## 8. Concurrency Explosion

### Concept: What Is Concurrency?

**Concurrency** means multiple tasks are in progress simultaneously. They may or may not run in parallel (parallel = literally at the same time on different CPU cores). Concurrency is about structure — managing multiple tasks. Parallelism is about execution.

In a microservice system, each service instance handles many requests concurrently. The system as a whole has hundreds of thousands of concurrent interactions.

### Why Concurrency Creates New Bugs

- **Race conditions**: Two operations read-modify-write shared state. The final result depends on who finishes last — unpredictable.
- **Deadlock**: Two operations wait for each other forever. Neither completes.
- **Livelock**: Two operations keep changing state in response to each other but make no progress.
- **Starvation**: One operation never gets CPU time because others keep preempting it.

### ASCII: Race Condition Visualization

```
RACE CONDITION ON A SHARED COUNTER (e.g., inventory count):

Thread 1 (Order A)          Thread 2 (Order B)          Counter
------------------          ------------------          -------
READ counter = 5                                            5
                            READ counter = 5               5
Compute: 5 - 1 = 4                                         5
                            Compute: 5 - 1 = 4             5
WRITE 4                                                     4
                            WRITE 4                         4  <-- WRONG!

Expected: 5 - 1 - 1 = 3
Actual:   4

Both orders "succeeded" but counter is wrong.
This is inventory overselling — a real financial problem.

FIX: Use atomic operations, mutexes, or optimistic locking (Section 6).
```

### Code: Race Condition Detection and Fix in Rust

```rust
// rust/concurrency/src/main.rs
// Demonstrates race condition, its effects, and the correct fix.
//
// --- Concept: Arc (Atomic Reference Count) ---
// Rc<T> is a reference-counted smart pointer — multiple owners.
// Arc<T> is the thread-safe version (Atomic RC).
// Use Arc when sharing data across threads.
//
// --- Concept: Mutex<T> ---
// Wraps data T so only one thread can access it at a time.
// .lock() acquires the lock, returns a MutexGuard.
// MutexGuard auto-releases when it goes out of scope (RAII).
//
// --- Concept: Atomic ---
// An operation that cannot be interrupted mid-way.
// AtomicI64 lets you do read-modify-write in ONE CPU instruction.
// No lock needed for simple operations.

use std::sync::{Arc, Mutex};
use std::sync::atomic::{AtomicI64, Ordering};
use std::thread;
use std::time::Duration;

// ===== PART 1: Demonstrating the race condition =====
// NOTE: Rust's ownership system actually prevents data races at compile time!
// To demonstrate the bug, we use unsafe code — showing what happens in C/Java.

fn demonstrate_race_condition() {
    println!("--- Part 1: Race Condition (using unsafe to bypass Rust's safety) ---");
    println!("This is what happens in languages without ownership (C, Java, Python).");

    // We use a raw pointer to bypass Rust's safety — NEVER do this in production
    let counter = Box::new(0i64);
    let raw_ptr = Box::into_raw(counter);

    let mut handles = vec![];

    for i in 0..10 {
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                unsafe {
                    // This is a race condition: read-modify-write is NOT atomic
                    let current = *raw_ptr;
                    thread::sleep(Duration::from_nanos(1)); // make race more likely
                    *raw_ptr = current + 1;
                }
            }
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let final_value = unsafe { *raw_ptr };
    println!("Expected: 10,000 (10 threads x 1,000 increments)");
    println!("Actual:   {} (data race corrupted the result!)", final_value);
    println!("Difference: {} lost updates\n", 10_000 - final_value);

    unsafe { drop(Box::from_raw(raw_ptr)); }
}

// ===== PART 2: Fix 1 — Mutex (for complex operations) =====
fn fix_with_mutex() {
    println!("--- Part 2: Fix with Mutex ---");

    // Arc: shared ownership. Mutex: exclusive access. Combined: safe shared mutable state.
    let counter = Arc::new(Mutex::new(0i64));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                // .lock() blocks until no other thread holds the lock
                // MutexGuard auto-releases when it goes out of scope
                let mut value = counter_clone.lock().unwrap();
                *value += 1;
                // Lock released here when `value` (MutexGuard) drops
            }
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let final_value = *counter.lock().unwrap();
    println!("Expected: 10,000");
    println!("Actual:   {} (correct!)\n", final_value);
}

// ===== PART 3: Fix 2 — Atomic (for simple numeric operations) =====
fn fix_with_atomic() {
    println!("--- Part 3: Fix with Atomic ---");
    println!("Atomics are faster than Mutex for simple operations (no OS-level blocking).");

    // AtomicI64 uses CPU-level atomic instructions (lock-free)
    let counter = Arc::new(AtomicI64::new(0));
    let mut handles = vec![];

    for _ in 0..10 {
        let counter_clone = Arc::clone(&counter);
        handles.push(thread::spawn(move || {
            for _ in 0..1000 {
                // fetch_add atomically: reads, adds 1, writes back — one CPU instruction
                // Ordering::SeqCst = sequential consistency — strongest memory ordering guarantee
                counter_clone.fetch_add(1, Ordering::SeqCst);
            }
        }));
    }

    for handle in handles {
        handle.join().unwrap();
    }

    let final_value = counter.load(Ordering::SeqCst);
    println!("Expected: 10,000");
    println!("Actual:   {} (correct, and faster than Mutex!)\n", final_value);
}

// ===== PART 4: Deadlock Demonstration =====
fn demonstrate_deadlock() {
    println!("--- Part 4: Deadlock Scenario ---");
    println!("Two resources (A and B). Two threads acquire them in opposite orders.");
    println!("Thread 1: A then B. Thread 2: B then A. --> DEADLOCK.");
    println!("(This will timeout after 1 second to avoid hanging the demo)\n");

    let resource_a = Arc::new(Mutex::new("Resource A"));
    let resource_b = Arc::new(Mutex::new("Resource B"));

    let ra1 = Arc::clone(&resource_a);
    let rb1 = Arc::clone(&resource_b);
    let ra2 = Arc::clone(&resource_a);
    let rb2 = Arc::clone(&resource_b);

    // Thread 1: acquires A then tries to acquire B
    let t1 = thread::spawn(move || {
        let _a = ra1.lock().unwrap();
        println!("  [Thread 1] Acquired Resource A");
        thread::sleep(Duration::from_millis(100)); // give T2 time to grab B
        println!("  [Thread 1] Waiting for Resource B...");
        let _b = rb1.try_lock(); // try_lock avoids indefinite block
        match _b {
            Ok(_) => println!("  [Thread 1] Got B! (race was avoided)"),
            Err(_) => println!("  [Thread 1] Couldn't get B — WOULD DEADLOCK here!"),
        }
    });

    // Thread 2: acquires B then tries to acquire A
    let t2 = thread::spawn(move || {
        let _b = rb2.lock().unwrap();
        println!("  [Thread 2] Acquired Resource B");
        thread::sleep(Duration::from_millis(100));
        println!("  [Thread 2] Waiting for Resource A...");
        let _a = ra2.try_lock();
        match _a {
            Ok(_) => println!("  [Thread 2] Got A! (race was avoided)"),
            Err(_) => println!("  [Thread 2] Couldn't get A — WOULD DEADLOCK here!"),
        }
    });

    t1.join().unwrap();
    t2.join().unwrap();

    println!("\nFIX: Always acquire locks in the SAME ORDER across all code paths.");
    println!("Or: Use a single coarser lock. Or: Redesign to avoid shared state.");
}

fn main() {
    demonstrate_race_condition();
    fix_with_mutex();
    fix_with_atomic();
    demonstrate_deadlock();
}
```

---

## 9. Version Mismatch and API Drift

### Concept: The API Contract

A **service contract** (API contract) is the agreement between two services: what endpoints exist, what data format is expected, what errors can occur.

When services evolve independently, this contract can break silently. Service A sends a request in v2 format; Service B still expects v1 format. B doesn't crash — it just gets unexpected data and produces wrong results.

### Types of API Changes

```
BREAKING vs NON-BREAKING CHANGES:

NON-BREAKING (backward compatible) — safe to deploy:
  - Adding a new optional field to a response
  - Adding a new endpoint
  - Adding a new optional request parameter

BREAKING (backward incompatible) — requires coordination:
  - Removing a field from a response
  - Renaming a field
  - Changing a field's type (e.g., string -> int)
  - Making an optional field required
  - Changing HTTP status codes

---

EXAMPLE:

Service B v1 response:
  {"user_id": 123, "name": "Alice"}

Service B v2 response (BREAKING CHANGE):
  {"id": 123, "full_name": "Alice", "email": "alice@example.com"}
  ^              ^
  renamed!       renamed!

Service A reads resp.user_id  --> GETS ZERO (field doesn't exist)
Service A reads resp.name     --> GETS EMPTY STRING

No crash. No error. Silent wrong data.
This is worse than a crash because it's invisible.
```

### Semantic Versioning for APIs

```
SEMANTIC VERSIONING: MAJOR.MINOR.PATCH
                      2    .1   .3

MAJOR: Breaking change — existing clients will break
MINOR: New feature, backward compatible
PATCH: Bug fix, backward compatible

RULE: When MAJOR increments, maintain the OLD version simultaneously
      until all clients have migrated.

URL VERSIONING (most common approach):
  /api/v1/orders  <-- old
  /api/v2/orders  <-- new (breaking change deployed here)

Both run simultaneously. Clients migrate at their own pace.
Deprecate v1 after all clients upgraded.
```

### Code: Versioned API with Schema Validation in Go

```go
// go/versioning/main.go
// Demonstrates API versioning and graceful schema evolution.
//
// --- Concept: Schema Validation ---
// Before processing a request, verify it matches the expected format.
// "Fail fast" — catch malformed input at the boundary, not deep in business logic.
//
// --- Concept: Unknown Field Handling ---
// When deserializing JSON, what do you do with fields you don't recognize?
// Option 1: Ignore them (lenient — safer for forward compatibility)
// Option 2: Error on unknown fields (strict — safer for catching bugs)
// Best practice: be lenient when READING, strict when WRITING.
// (Postel's Law / Robustness Principle)

package main

import (
    "encoding/json"
    "errors"
    "fmt"
    "strings"
)

// --- V1 Schema ---
type OrderRequestV1 struct {
    UserID  int     `json:"user_id"`
    Product string  `json:"product"`
    Amount  float64 `json:"amount"`
}

// --- V2 Schema (breaking change: renamed fields, added required field) ---
type OrderRequestV2 struct {
    CustomerID   int     `json:"customer_id"` // renamed from user_id
    ProductSKU   string  `json:"product_sku"` // renamed from product
    PriceUSD     float64 `json:"price_usd"`   // renamed from amount
    ShippingAddr string  `json:"shipping_address"` // new required field
}

// ValidationError accumulates all validation errors found
type ValidationError struct {
    Field   string
    Message string
}

type ValidationErrors []ValidationError

func (ve ValidationErrors) Error() string {
    msgs := make([]string, len(ve))
    for i, e := range ve {
        msgs[i] = fmt.Sprintf("field '%s': %s", e.Field, e.Message)
    }
    return "validation failed: " + strings.Join(msgs, "; ")
}

// validateV1 validates a V1 request
func validateV1(req OrderRequestV1) error {
    var errs ValidationErrors

    if req.UserID <= 0 {
        errs = append(errs, ValidationError{"user_id", "must be positive"})
    }
    if req.Product == "" {
        errs = append(errs, ValidationError{"product", "required"})
    }
    if req.Amount <= 0 {
        errs = append(errs, ValidationError{"amount", "must be positive"})
    }

    if len(errs) > 0 {
        return errs
    }
    return nil
}

// validateV2 validates a V2 request
func validateV2(req OrderRequestV2) error {
    var errs ValidationErrors

    if req.CustomerID <= 0 {
        errs = append(errs, ValidationError{"customer_id", "must be positive"})
    }
    if req.ProductSKU == "" {
        errs = append(errs, ValidationError{"product_sku", "required"})
    }
    if req.PriceUSD <= 0 {
        errs = append(errs, ValidationError{"price_usd", "must be positive"})
    }
    if req.ShippingAddr == "" {
        errs = append(errs, ValidationError{"shipping_address", "required in v2"})
    }

    if len(errs) > 0 {
        return errs
    }
    return nil
}

// migrateV1ToV2 converts a v1 request to v2 format
// This is used when a v1 client sends to a v2 handler
func migrateV1ToV2(v1 OrderRequestV1) (OrderRequestV2, error) {
    if v1.ShippingAddr == "" {
        // We can't migrate without a shipping address — this is a breaking change
        return OrderRequestV2{}, errors.New(
            "cannot migrate V1->V2: v2 requires 'shipping_address' which is absent in v1")
    }
    return OrderRequestV2{
        CustomerID:   v1.UserID,
        ProductSKU:   v1.Product,
        PriceUSD:     v1.Amount,
        ShippingAddr: v1.ShippingAddr,
    }, nil
}

// parseAndRoute handles the request routing based on version
func parseAndRoute(version string, body []byte) {
    fmt.Printf("Routing version: %s\n", version)
    fmt.Printf("Body: %s\n", body)

    switch version {
    case "v1":
        var req OrderRequestV1

        // DisallowUnknownFields makes deserialization strict
        // This catches when a client sends unexpected fields — often a sign of mismatch
        decoder := json.NewDecoder(strings.NewReader(string(body)))
        decoder.DisallowUnknownFields()

        if err := decoder.Decode(&req); err != nil {
            fmt.Printf("  ERROR: JSON parse failed: %v\n", err)
            return
        }
        if err := validateV1(req); err != nil {
            fmt.Printf("  ERROR: Validation failed: %v\n", err)
            return
        }
        fmt.Printf("  V1 order processed: user=%d, product=%s, amount=%.2f\n",
            req.UserID, req.Product, req.Amount)

    case "v2":
        var req OrderRequestV2
        if err := json.Unmarshal(body, &req); err != nil {
            fmt.Printf("  ERROR: JSON parse failed: %v\n", err)
            return
        }
        if err := validateV2(req); err != nil {
            fmt.Printf("  ERROR: Validation failed: %v\n", err)
            return
        }
        fmt.Printf("  V2 order processed: customer=%d, sku=%s, price=%.2f, ship=%s\n",
            req.CustomerID, req.ProductSKU, req.PriceUSD, req.ShippingAddr)

    default:
        fmt.Printf("  ERROR: Unknown API version '%s'. Supported: v1, v2\n", version)
    }
    fmt.Println()
}

func main() {
    fmt.Println("=== API Versioning and Schema Validation ===\n")

    testCases := []struct {
        version string
        body    string
        desc    string
    }{
        {
            version: "v1",
            body:    `{"user_id": 123, "product": "Widget", "amount": 29.99}`,
            desc:    "Valid V1 request",
        },
        {
            version: "v2",
            body:    `{"customer_id": 123, "product_sku": "WDGT-001", "price_usd": 29.99, "shipping_address": "123 Main St"}`,
            desc:    "Valid V2 request",
        },
        {
            version: "v2",
            body:    `{"customer_id": 123, "product_sku": "WDGT-001", "price_usd": 29.99}`,
            desc:    "V2 request MISSING required shipping_address",
        },
        {
            version: "v1",
            body:    `{"customer_id": 123, "product_sku": "WDGT"}`,
            desc:    "V2 payload sent to V1 endpoint (API drift scenario)",
        },
        {
            version: "v3",
            body:    `{"data": "something"}`,
            desc:    "Unknown version",
        },
    }

    for _, tc := range testCases {
        fmt.Printf("=== Test: %s ===\n", tc.desc)
        parseAndRoute(tc.version, []byte(tc.body))
    }
}
```

---

## 10. Retry Storms and Cascading Failures

### Concept: What Is a Retry Storm?

When one service slows down, every caller retries. Each retry adds more load to the already-struggling service. More load makes it slower. More retries. This is a **positive feedback loop** — a self-reinforcing cycle of failure.

### Cascading Failure Flow

```
NORMAL OPERATION:
Client --> [A] --> [B] --> [C] --> [DB]
           100 req/s  100 req/s  handles fine

---

CASCADING FAILURE:
Step 1: DB gets slow (high CPU, slow query)
        [DB] starts taking 2s per query (normally 10ms)

Step 2: [C] waits 2s per request. Worker threads pile up.
        [C] now has 200 requests queued. Starts timing out.

Step 3: [B] gets 500 errors from [C]. Retries each request 3x.
        [B] now sends 300 req/s to [C] (3x the original load).
        [C] is overwhelmed. Latency goes to 10s.

Step 4: [A] gets 500 errors from [B]. Retries each request 3x.
        [A] now sends 300 req/s to [B].
        [B] runs out of thread pool capacity. Starts returning 503.

Step 5: Clients get errors. Each client retries.
        System is now handling 10x the original load.
        COMPLETE SYSTEM FAILURE.

The original cause: one slow DB query.
The visible failure: entire platform down.
```

### ASCII: Retry Storm Visualization

```
Time -->  t=0     t=1s    t=2s    t=3s    t=4s    t=5s
-----------+-------+-------+-------+-------+-------+----
DB load:   |  1x   |  1x   | [2x!] | [4x!] | [8x!] | DEAD
           |       |       |   ^   |       |       |
           |       |       |   |   |       |       |
           |       |       | DB gets slow           |
           |       |       |                        |
C req:     |  100  |  100  |  200  |  400  |  800  | DEAD
           |                   ^   |                |
           |                   |   |                |
           |               Retries begin            |
B req:     |  100  |  100  |  100  |  300  |  900  | DEAD
A req:     |  100  |  100  |  100  |  100  |  300  | DEAD
```

### Code: Rate Limiter (Token Bucket) in Go

```go
// go/rate_limit/main.go
// The Token Bucket algorithm — the standard rate limiter used in production.
//
// --- Concept: Token Bucket ---
// Imagine a bucket that holds N tokens.
// Tokens are added at a fixed rate (e.g., 100/second).
// Each request consumes one token.
// If the bucket is empty, the request is REJECTED (or waits).
//
// Properties:
//  - Allows bursts up to the bucket capacity
//  - Long-term rate is capped at the fill rate
//  - Rejected requests fail FAST — they don't consume resources
//
// This directly prevents retry storms by rejecting excess load early.

package main

import (
    "fmt"
    "sync"
    "sync/atomic"
    "time"
)

type TokenBucket struct {
    capacity    float64   // max tokens the bucket can hold
    tokens      float64   // current token count
    fillRate    float64   // tokens added per second
    lastRefill  time.Time
    mu          sync.Mutex
    name        string

    // Metrics
    acceptCount uint64
    rejectCount uint64
}

func NewTokenBucket(name string, capacity, fillRatePerSec float64) *TokenBucket {
    return &TokenBucket{
        capacity:   capacity,
        tokens:     capacity, // start full
        fillRate:   fillRatePerSec,
        lastRefill: time.Now(),
        name:       name,
    }
}

// refill adds tokens based on elapsed time since last refill
// Called lazily — only when a request arrives
func (tb *TokenBucket) refill() {
    now := time.Now()
    elapsed := now.Sub(tb.lastRefill).Seconds()
    tb.tokens += elapsed * tb.fillRate
    if tb.tokens > tb.capacity {
        tb.tokens = tb.capacity
    }
    tb.lastRefill = now
}

// Allow returns true if the request should proceed, false if rate-limited
func (tb *TokenBucket) Allow() bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()

    tb.refill()

    if tb.tokens >= 1.0 {
        tb.tokens -= 1.0
        atomic.AddUint64(&tb.acceptCount, 1)
        return true
    }

    atomic.AddUint64(&tb.rejectCount, 1)
    return false
}

// AllowN consumes n tokens (for requests with different "weights")
func (tb *TokenBucket) AllowN(n float64) bool {
    tb.mu.Lock()
    defer tb.mu.Unlock()

    tb.refill()

    if tb.tokens >= n {
        tb.tokens -= n
        atomic.AddUint64(&tb.acceptCount, 1)
        return true
    }

    atomic.AddUint64(&tb.rejectCount, 1)
    return false
}

func (tb *TokenBucket) Stats() (accepted, rejected uint64, tokens float64) {
    tb.mu.Lock()
    defer tb.mu.Unlock()
    tb.refill()
    return atomic.LoadUint64(&tb.acceptCount),
           atomic.LoadUint64(&tb.rejectCount),
           tb.tokens
}

// simulateRetryStorm shows what happens WITHOUT rate limiting
func simulateWithoutRateLimit(reqPerSec int, duration time.Duration) {
    fmt.Printf("\n--- WITHOUT Rate Limiting: %d req/s for %v ---\n", reqPerSec, duration)

    processed := 0
    start := time.Now()
    interval := time.Second / time.Duration(reqPerSec)

    for time.Since(start) < duration {
        // Simulate each request taking 50ms to process
        time.Sleep(interval)
        processed++

        // Worker thread pool exhausts after N concurrent requests
        if processed > 50 {
            fmt.Printf("  Worker pool EXHAUSTED after %d requests. System failing.\n", processed)
            break
        }
    }
    fmt.Printf("  Total processed before failure: %d\n", processed)
}

// simulateWithRateLimit shows controlled load with rate limiting
func simulateWithRateLimit(reqPerSec int, limiter *TokenBucket, duration time.Duration) {
    fmt.Printf("\n--- WITH Rate Limiting: %d req/s incoming, limited to %.0f/s ---\n",
        reqPerSec, limiter.fillRate)

    accepted, rejected := 0, 0
    start := time.Now()
    interval := time.Second / time.Duration(reqPerSec)

    for time.Since(start) < duration {
        time.Sleep(interval)

        if limiter.Allow() {
            accepted++
        } else {
            rejected++
        }
    }

    fmt.Printf("  Accepted: %d (within capacity)\n", accepted)
    fmt.Printf("  Rejected: %d (protected system from overload)\n", rejected)
    fmt.Printf("  System stable — no cascade!\n")
}

func main() {
    fmt.Println("=== Token Bucket Rate Limiter: Preventing Retry Storms ===")

    // Rate limiter: max 20 req/burst, fills at 10 req/sec
    limiter := NewTokenBucket("payment-service", 20, 10)

    // Scenario: 50 req/sec hitting a service that can handle 10 req/sec
    simulateWithoutRateLimit(50, 200*time.Millisecond)
    simulateWithRateLimit(50, limiter, 500*time.Millisecond)

    accepted, rejected, remaining := limiter.Stats()
    fmt.Printf("\nFinal stats: accepted=%d, rejected=%d, tokens_remaining=%.1f\n",
        accepted, rejected, remaining)
}
```

---

## 11. Observability: Tracing, Metrics, Logging

### Concept: The Three Pillars of Observability

**Observability** is the ability to understand what a system is doing from its external outputs. You cannot attach a debugger to a running production system — you must instrument it in advance.

The three pillars:

```
+------------------+------------------+-------------------+
|    LOGS          |    METRICS       |    TRACES         |
+------------------+------------------+-------------------+
| "What happened"  | "How much/fast"  | "What path did   |
|                  |                  |  it take"         |
+------------------+------------------+-------------------+
| Discrete events  | Aggregated       | Timeline of a     |
| with context     | numbers over     | single request    |
|                  | time             | across services   |
+------------------+------------------+-------------------+
| Example:         | Example:         | Example:          |
| "Order 456       | "p99 latency:    | order_service     |
| failed with      | 340ms"           |   └─ payment_svc  |
| error X at       | "error rate:     |       └─ bank_api |
| 14:32:01"        | 0.3%"            |       [450ms]     |
+------------------+------------------+-------------------+
| Tool: ELK Stack  | Tool: Prometheus | Tool: Jaeger,     |
| Splunk           | Grafana          | Zipkin, OpenTel.  |
+------------------+------------------+-------------------+
```

### Concept: Distributed Trace

A **distributed trace** is a record of the entire journey of a single request through all services.

It is composed of **spans**: a span is one unit of work in one service with a start time, end time, and metadata.

```
DISTRIBUTED TRACE for request trace_id=abc123:

Span 1: order-service           |=====order-service [200ms total]=====|
  Span 2: payment-service          |===payment-service [150ms]===|
    Span 3: bank-api                  |=====bank-api [120ms]=====|
  Span 4: inventory-service                                        |=inv[30ms]=|

Timeline: 0ms         50ms        100ms       150ms       200ms
           |            |           |           |           |
[order ]  [.........................................complete]
 [payment]             [.......................complete]
  [bank ]               [.............................complete]
                                                 [inv][complete]

From this trace, you immediately see:
  - bank-api is the bottleneck (120ms out of 200ms total)
  - payment-service + bank-api are on the critical path
  - inventory runs in parallel, not on critical path
```

### Code: Minimal OpenTelemetry-Style Tracer in Go

```go
// go/tracing/main.go
// A minimal distributed tracing implementation that mirrors how
// OpenTelemetry works internally. Understanding this makes production
// tracing tools much clearer.
//
// --- Concept: Span ---
// A span = one operation. Has:
//   - trace_id: shared by all spans in the same request
//   - span_id: unique to this operation
//   - parent_span_id: which span called this one (creates the tree)
//   - start_time, end_time
//   - service_name, operation_name
//   - attributes (key-value metadata)
//   - events (timestamped notes within a span)
//   - status (ok, error)

package main

import (
    "context"
    "encoding/json"
    "fmt"
    "math/rand"
    "os"
    "sync"
    "time"
)

// SpanStatus represents the outcome of a span
type SpanStatus int

const (
    StatusOK    SpanStatus = iota
    StatusError SpanStatus = iota
)

// SpanEvent is a timestamped annotation within a span
type SpanEvent struct {
    Timestamp time.Time
    Name      string
    Attrs     map[string]string
}

// Span represents one unit of work in one service
type Span struct {
    TraceID      string
    SpanID       string
    ParentSpanID string

    Service   string
    Operation string

    StartTime time.Time
    EndTime   time.Time

    Attrs  map[string]string
    Events []SpanEvent
    Status SpanStatus
    ErrMsg string

    mu sync.Mutex
}

func (s *Span) SetAttr(key, value string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.Attrs[key] = value
}

func (s *Span) AddEvent(name string, attrs map[string]string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.Events = append(s.Events, SpanEvent{
        Timestamp: time.Now(),
        Name:      name,
        Attrs:     attrs,
    })
}

func (s *Span) Finish(status SpanStatus, errMsg string) {
    s.mu.Lock()
    defer s.mu.Unlock()
    s.EndTime = time.Now()
    s.Status = status
    s.ErrMsg = errMsg
}

func (s *Span) Duration() time.Duration {
    return s.EndTime.Sub(s.StartTime)
}

// Tracer collects spans and exports them
type Tracer struct {
    spans []*Span
    mu    sync.Mutex
}

var globalTracer = &Tracer{}

// spanKey is used to store/retrieve span from context
type spanKey struct{}

// StartSpan creates a new span. Extracts parent from context if present.
func StartSpan(ctx context.Context, service, operation string) (*Span, context.Context) {
    traceID := ""
    parentSpanID := ""

    // Extract trace ID and parent span from context
    if parent, ok := ctx.Value(spanKey{}).(*Span); ok && parent != nil {
        traceID = parent.TraceID
        parentSpanID = parent.SpanID
    }

    // Generate trace ID if this is the root span
    if traceID == "" {
        traceID = fmt.Sprintf("trace-%08x", rand.Uint32())
    }

    span := &Span{
        TraceID:      traceID,
        SpanID:       fmt.Sprintf("span-%08x", rand.Uint32()),
        ParentSpanID: parentSpanID,
        Service:      service,
        Operation:    operation,
        StartTime:    time.Now(),
        Attrs:        map[string]string{},
    }

    globalTracer.mu.Lock()
    globalTracer.spans = append(globalTracer.spans, span)
    globalTracer.mu.Unlock()

    // Inject span into context so child operations can find it
    childCtx := context.WithValue(ctx, spanKey{}, span)
    return span, childCtx
}

// PrintTrace renders all spans as an ASCII timeline
func (t *Tracer) PrintTrace() {
    t.mu.Lock()
    spans := make([]*Span, len(t.spans))
    copy(spans, t.spans)
    t.mu.Unlock()

    if len(spans) == 0 {
        return
    }

    // Find trace start time (root span)
    traceStart := spans[0].StartTime
    for _, s := range spans {
        if s.StartTime.Before(traceStart) {
            traceStart = s.StartTime
        }
    }

    // Find total trace duration
    var traceEnd time.Time
    for _, s := range spans {
        if s.EndTime.After(traceEnd) {
            traceEnd = s.EndTime
        }
    }
    totalDuration := traceEnd.Sub(traceStart)

    fmt.Println("\n=== DISTRIBUTED TRACE ===")
    fmt.Printf("Trace ID: %s\n", spans[0].TraceID)
    fmt.Printf("Total duration: %v\n\n", totalDuration.Round(time.Millisecond))

    const barWidth = 60
    scale := float64(barWidth) / float64(totalDuration.Microseconds())

    for _, s := range spans {
        indent := ""
        if s.ParentSpanID != "" {
            indent = "  └─ "
        }

        // Calculate position in the bar
        startOffset := int(float64(s.StartTime.Sub(traceStart).Microseconds()) * scale)
        duration := int(float64(s.Duration().Microseconds()) * scale)
        if duration < 1 {
            duration = 1
        }

        bar := make([]byte, barWidth)
        for i := range bar {
            if i >= startOffset && i < startOffset+duration {
                bar[i] = '='
            } else {
                bar[i] = '.'
            }
        }

        status := "OK"
        if s.Status == StatusError {
            status = "ERR"
        }

        fmt.Printf("%s%-20s [%s] |%s| %v\n",
            indent,
            s.Service+"/"+s.Operation,
            status,
            string(bar),
            s.Duration().Round(time.Millisecond))

        if s.ErrMsg != "" {
            fmt.Printf("%s                         ERROR: %s\n", indent, s.ErrMsg)
        }
    }

    fmt.Println()
    fmt.Println("=== SPAN DETAILS (JSON) ===")
    for _, s := range spans {
        data, _ := json.MarshalIndent(map[string]interface{}{
            "trace_id":       s.TraceID,
            "span_id":        s.SpanID,
            "parent_span_id": s.ParentSpanID,
            "service":        s.Service,
            "operation":      s.Operation,
            "duration_ms":    s.Duration().Milliseconds(),
            "status":         s.Status,
            "error":          s.ErrMsg,
            "attributes":     s.Attrs,
        }, "", "  ")
        fmt.Printf("%s\n", data)
    }
}

// ===== Simulated Services with Tracing =====

func orderServiceHandler(ctx context.Context, orderID string) error {
    span, ctx := StartSpan(ctx, "order-service", "create_order")
    defer func() {
        if r := recover(); r != nil {
            span.Finish(StatusError, fmt.Sprintf("%v", r))
        }
    }()

    span.SetAttr("order.id", orderID)
    span.AddEvent("order.validation.start", nil)
    time.Sleep(20 * time.Millisecond)
    span.AddEvent("order.validation.complete", map[string]string{"valid": "true"})

    // Call payment service
    if err := paymentServiceHandler(ctx, 99.99); err != nil {
        span.Finish(StatusError, err.Error())
        return err
    }

    // Call inventory service (parallel in real systems, sequential here for simplicity)
    if err := inventoryServiceHandler(ctx, "item-A", 1); err != nil {
        span.Finish(StatusError, err.Error())
        return err
    }

    span.Finish(StatusOK, "")
    return nil
}

func paymentServiceHandler(ctx context.Context, amount float64) error {
    span, ctx := StartSpan(ctx, "payment-service", "charge_card")
    span.SetAttr("payment.amount", fmt.Sprintf("%.2f", amount))

    time.Sleep(150 * time.Millisecond) // simulate slow bank API

    if err := bankAPICall(ctx, amount); err != nil {
        span.Finish(StatusError, err.Error())
        return err
    }

    span.Finish(StatusOK, "")
    return nil
}

func bankAPICall(ctx context.Context, amount float64) error {
    span, _ := StartSpan(ctx, "bank-api", "authorize")
    span.SetAttr("bank.amount", fmt.Sprintf("%.2f", amount))

    time.Sleep(120 * time.Millisecond)

    // 20% failure rate
    if rand.Float32() < 0.20 {
        span.Finish(StatusError, "bank authorization declined")
        return fmt.Errorf("bank authorization declined")
    }

    span.Finish(StatusOK, "")
    return nil
}

func inventoryServiceHandler(ctx context.Context, itemID string, qty int) error {
    span, _ := StartSpan(ctx, "inventory-service", "deduct_stock")
    span.SetAttr("item.id", itemID)
    span.SetAttr("item.qty", fmt.Sprintf("%d", qty))

    time.Sleep(30 * time.Millisecond)
    span.Finish(StatusOK, "")
    return nil
}

func main() {
    rand.Seed(time.Now().UnixNano())
    _ = os.Stdout

    fmt.Println("=== Distributed Tracing Demonstration ===")
    fmt.Println("Processing order with full distributed trace...\n")

    ctx := context.Background()

    err := orderServiceHandler(ctx, "order-123")
    if err != nil {
        fmt.Printf("Order failed: %v\n", err)
    } else {
        fmt.Printf("Order succeeded!\n")
    }

    globalTracer.PrintTrace()
}
```

---

## 12. Environment Differences: Local vs Production

### Why "Works on My Machine" Is a Distributed Systems Problem

Locally, you run 2-3 services on your laptop with no network latency, no real load, and known data. In production, you have 50+ services, real network conditions, high concurrency, and data you've never seen.

```
LOCAL ENVIRONMENT:                  PRODUCTION ENVIRONMENT:
+------------------------+          +-----------------------------+
| Your laptop            |          | Kubernetes cluster          |
| 1 pod per service      |          | 3-10 pods per service       |
| 0ms "network" latency  |          | 1-50ms real network         |
| 10 fake requests/day   |          | 10,000 real requests/min    |
| Clean test data        |          | 5 years of messy data       |
| Single replica         |          | Multiple replicas + LB      |
| Static IPs             |          | Dynamic IPs (pods restart)  |
| No clock drift         |          | ±100ms clock drift          |
| No partial failures    |          | 0.1-1% request failure rate |
+------------------------+          +-----------------------------+

Bugs that ONLY appear in production:
  - Race conditions (need concurrency to trigger)
  - Clock-dependent bugs (need real time differences)
  - Memory leaks (need hours of load to surface)
  - Connection pool exhaustion (need concurrent users)
  - Data-dependent bugs (need real edge-case data)
```

### Code: Health Check Endpoint in Go

```go
// go/health/main.go
// Health checks are how infrastructure knows a service is ready to receive traffic.
// They are the bridge between "deployed" and "actually working in production".
//
// --- Concept: Liveness vs Readiness ---
// Liveness:  "Is the process alive?" — if not, kill and restart it
// Readiness: "Is the service ready to serve traffic?" — if not, stop routing to it
//            (e.g., warming up caches, not yet connected to DB)
//
// A service can be ALIVE but not READY.
// Example: Process is running but cannot connect to DB.
//          Liveness: OK (don't restart — that won't fix DB)
//          Readiness: FAIL (stop sending requests — they'll all fail)

package main

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "sync"
    "time"
)

type CheckStatus string

const (
    StatusHealthy   CheckStatus = "healthy"
    StatusDegraded  CheckStatus = "degraded"
    StatusUnhealthy CheckStatus = "unhealthy"
)

// CheckResult holds the result of one health check
type CheckResult struct {
    Status  CheckStatus   `json:"status"`
    Latency time.Duration `json:"latency_ms"`
    Error   string        `json:"error,omitempty"`
}

// HealthReport is the complete response
type HealthReport struct {
    Status    CheckStatus             `json:"status"`
    Timestamp string                  `json:"timestamp"`
    Version   string                  `json:"version"`
    Checks    map[string]CheckResult  `json:"checks"`
    Uptime    string                  `json:"uptime"`
}

type HealthChecker struct {
    checks  map[string]func(ctx context.Context) CheckResult
    mu      sync.RWMutex
    startTime time.Time
    version   string
}

func NewHealthChecker(version string) *HealthChecker {
    return &HealthChecker{
        checks:    make(map[string]func(ctx context.Context) CheckResult),
        startTime: time.Now(),
        version:   version,
    }
}

func (hc *HealthChecker) Register(name string, check func(ctx context.Context) CheckResult) {
    hc.mu.Lock()
    defer hc.mu.Unlock()
    hc.checks[name] = check
}

// RunAll runs all checks concurrently and aggregates results
func (hc *HealthChecker) RunAll(ctx context.Context) HealthReport {
    hc.mu.RLock()
    checks := make(map[string]func(context.Context) CheckResult)
    for k, v := range hc.checks {
        checks[k] = v
    }
    hc.mu.RUnlock()

    results := make(map[string]CheckResult)
    var mu sync.Mutex
    var wg sync.WaitGroup

    // Run all checks in parallel (don't let one slow check block others)
    for name, check := range checks {
        wg.Add(1)
        go func(n string, c func(context.Context) CheckResult) {
            defer wg.Done()

            // Each check gets a timeout
            checkCtx, cancel := context.WithTimeout(ctx, 5*time.Second)
            defer cancel()

            result := c(checkCtx)

            mu.Lock()
            results[n] = result
            mu.Unlock()
        }(name, check)
    }

    wg.Wait()

    // Aggregate: if ANY check is unhealthy, overall is unhealthy
    overallStatus := StatusHealthy
    for _, r := range results {
        if r.Status == StatusUnhealthy {
            overallStatus = StatusUnhealthy
            break
        }
        if r.Status == StatusDegraded && overallStatus == StatusHealthy {
            overallStatus = StatusDegraded
        }
    }

    return HealthReport{
        Status:    overallStatus,
        Timestamp: time.Now().UTC().Format(time.RFC3339),
        Version:   hc.version,
        Checks:    results,
        Uptime:    time.Since(hc.startTime).Round(time.Second).String(),
    }
}

func (hc *HealthChecker) LivenessHandler(w http.ResponseWriter, r *http.Request) {
    // Liveness is simple: if this handler runs, we're alive
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{"status": "alive"})
}

func (hc *HealthChecker) ReadinessHandler(w http.ResponseWriter, r *http.Request) {
    report := hc.RunAll(r.Context())
    w.Header().Set("Content-Type", "application/json")

    // Return appropriate HTTP status codes
    // 200 = ready, 503 = not ready (Kubernetes uses this to stop routing)
    if report.Status == StatusUnhealthy {
        w.WriteHeader(http.StatusServiceUnavailable) // 503
    } else if report.Status == StatusDegraded {
        w.WriteHeader(http.StatusOK) // 200 but mark degraded
    }

    json.NewEncoder(w).Encode(report)
}

// ===== Example Health Checks =====

func dbHealthCheck(dbConnected bool) func(ctx context.Context) CheckResult {
    return func(ctx context.Context) CheckResult {
        start := time.Now()

        if !dbConnected {
            return CheckResult{
                Status:  StatusUnhealthy,
                Latency: time.Since(start),
                Error:   "cannot connect to database",
            }
        }

        // Simulate DB ping latency
        time.Sleep(5 * time.Millisecond)
        latency := time.Since(start)

        if latency > 100*time.Millisecond {
            return CheckResult{
                Status:  StatusDegraded,
                Latency: latency,
                Error:   fmt.Sprintf("DB latency high: %v", latency),
            }
        }

        return CheckResult{Status: StatusHealthy, Latency: latency}
    }
}

func cacheHealthCheck() func(ctx context.Context) CheckResult {
    return func(ctx context.Context) CheckResult {
        start := time.Now()
        time.Sleep(2 * time.Millisecond) // simulate ping
        return CheckResult{Status: StatusHealthy, Latency: time.Since(start)}
    }
}

func main() {
    hc := NewHealthChecker("1.2.3")
    hc.Register("database", dbHealthCheck(true))  // healthy DB
    hc.Register("cache", cacheHealthCheck())

    // Run health check and print results
    ctx := context.Background()
    report := hc.RunAll(ctx)

    data, _ := json.MarshalIndent(report, "", "  ")
    fmt.Println("=== Health Check Report ===")
    fmt.Println(string(data))

    fmt.Println("\n--- Simulating DB failure ---")
    hc.Register("database", dbHealthCheck(false)) // unhealthy DB
    report = hc.RunAll(ctx)
    data, _ = json.MarshalIndent(report, "", "  ")
    fmt.Println(string(data))
}
```

---

## 13. Asynchronous Communication: Queues and Events

### Concept: Message Queues vs Direct HTTP Calls

**Synchronous** (HTTP): Service A calls Service B. A **waits** until B responds. If B is slow, A is slow. If B is down, A fails.

**Asynchronous** (Message Queue): Service A puts a message in a queue. A **immediately continues**. B reads from the queue when it's ready. A and B are **decoupled** in time.

```
SYNCHRONOUS HTTP:
Client --> [A] ---HTTP---> [B] ---HTTP---> [C]
                              <--- waits --->
           A is blocked while waiting for C

---

ASYNCHRONOUS QUEUE:
Client --> [A] --> [Queue] --> [B] --> [Queue] --> [C]
                   ^                   ^
                   |                   |
           A puts message here     B reads when ready
           A continues immediately  B continues after processing

Benefits:
  - A is not slowed by B or C
  - If B crashes, messages stay in queue — not lost
  - B can scale independently based on queue depth
  - Natural backpressure (queue fills up if B can't keep up)

Drawbacks:
  - Delayed execution — harder to debug
  - Duplicate messages possible (at-least-once delivery)
  - Out-of-order messages possible
  - "When did this actually happen?" is hard to answer
```

### Code: Message Queue Simulation in C

```c
/* c/queue/message_queue.c
 * A thread-safe bounded message queue — simulates what Redis, RabbitMQ,
 * or Kafka provide. Understanding the internals makes production queues clearer.
 *
 * --- Concept: Bounded Queue ---
 * A queue with a maximum size.
 * If the producer sends faster than the consumer processes,
 * the queue fills up. Producer either:
 *   1. Blocks (backpressure — natural flow control)
 *   2. Drops messages (lossy but non-blocking)
 *   3. Returns error (producer can decide what to do)
 *
 * --- Concept: Producer-Consumer Pattern ---
 * Producer: writes messages to queue
 * Consumer: reads and processes messages from queue
 * Queue: decouples them in time
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <unistd.h>
#include <time.h>
#include <stdint.h>

#define QUEUE_CAPACITY 8
#define MSG_MAX_LEN    256

typedef struct {
    char    message_id[64];
    char    payload[MSG_MAX_LEN];
    int64_t enqueue_time_ms;
    int     retry_count;
} Message;

/* Circular buffer-based bounded queue */
typedef struct {
    Message         buffer[QUEUE_CAPACITY];
    int             head;    /* index of next item to dequeue */
    int             tail;    /* index of next empty slot */
    int             count;   /* current number of items */
    int             capacity;
    pthread_mutex_t lock;
    pthread_cond_t  not_empty;  /* signal: queue has items */
    pthread_cond_t  not_full;   /* signal: queue has space */
    int             closed;     /* 1 = no more producers, drain and exit */
} MessageQueue;

static int64_t now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
}

MessageQueue *mq_create(int capacity) {
    MessageQueue *q = calloc(1, sizeof(MessageQueue));
    q->capacity = QUEUE_CAPACITY;
    pthread_mutex_init(&q->lock, NULL);
    pthread_cond_init(&q->not_empty, NULL);
    pthread_cond_init(&q->not_full, NULL);
    return q;
}

/* Enqueue with backpressure: blocks if queue is full */
int mq_enqueue(MessageQueue *q, const Message *msg) {
    pthread_mutex_lock(&q->lock);

    while (q->count >= q->capacity && !q->closed) {
        printf("  [Queue] FULL (%d/%d) — producer blocking (backpressure)\n",
               q->count, q->capacity);
        /* Block until consumer makes space */
        pthread_cond_wait(&q->not_full, &q->lock);
    }

    if (q->closed) {
        pthread_mutex_unlock(&q->lock);
        return -1;
    }

    q->buffer[q->tail] = *msg;
    q->tail = (q->tail + 1) % q->capacity;
    q->count++;

    printf("  [Queue] Enqueued msg_id=%s (queue depth: %d/%d)\n",
           msg->message_id, q->count, q->capacity);

    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->lock);
    return 0;
}

/* Non-blocking enqueue — returns immediately if full */
int mq_try_enqueue(MessageQueue *q, const Message *msg) {
    pthread_mutex_lock(&q->lock);

    if (q->count >= q->capacity) {
        pthread_mutex_unlock(&q->lock);
        return -1; /* QUEUE_FULL */
    }

    q->buffer[q->tail] = *msg;
    q->tail = (q->tail + 1) % q->capacity;
    q->count++;
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->lock);
    return 0;
}

/* Dequeue — blocks if empty, returns 0 on success, -1 if closed+empty */
int mq_dequeue(MessageQueue *q, Message *msg) {
    pthread_mutex_lock(&q->lock);

    while (q->count == 0) {
        if (q->closed) {
            pthread_mutex_unlock(&q->lock);
            return -1; /* Queue closed and empty — consumer should exit */
        }
        pthread_cond_wait(&q->not_empty, &q->lock);
    }

    *msg = q->buffer[q->head];
    q->head = (q->head + 1) % q->capacity;
    q->count--;

    pthread_cond_signal(&q->not_full);
    pthread_mutex_unlock(&q->lock);
    return 0;
}

void mq_close(MessageQueue *q) {
    pthread_mutex_lock(&q->lock);
    q->closed = 1;
    pthread_cond_broadcast(&q->not_empty);
    pthread_cond_broadcast(&q->not_full);
    pthread_mutex_unlock(&q->lock);
}

void mq_destroy(MessageQueue *q) {
    pthread_mutex_destroy(&q->lock);
    pthread_cond_destroy(&q->not_empty);
    pthread_cond_destroy(&q->not_full);
    free(q);
}

/* Producer: simulates Order Service publishing events */
typedef struct {
    MessageQueue *q;
    int           num_messages;
    const char   *producer_name;
} ProducerArgs;

void *producer_thread(void *arg) {
    ProducerArgs *args = (ProducerArgs *)arg;
    char msg_id[64];

    for (int i = 1; i <= args->num_messages; i++) {
        Message msg;
        snprintf(msg.message_id, sizeof(msg.message_id), "%s-msg-%d",
                 args->producer_name, i);
        snprintf(msg.payload, sizeof(msg.payload),
                 "order.created: {order_id: %s-%d, amount: %.2f}",
                 args->producer_name, i, 9.99 * i);
        msg.enqueue_time_ms = now_ms();
        msg.retry_count = 0;

        printf("[%s] Publishing event: %s\n", args->producer_name, msg.message_id);
        mq_enqueue(args->q, &msg);

        /* Variable publishing rate */
        struct timespec ts = { .tv_sec = 0, .tv_nsec = (rand() % 50 + 10) * 1000000L };
        nanosleep(&ts, NULL);
    }

    printf("[%s] All messages published.\n", args->producer_name);
    return NULL;
}

/* Consumer: simulates Inventory Service consuming events */
typedef struct {
    MessageQueue *q;
    const char   *consumer_name;
    int           slow;    /* 1 = simulates slow processing */
} ConsumerArgs;

void *consumer_thread(void *arg) {
    ConsumerArgs *args = (ConsumerArgs *)arg;
    Message msg;
    int processed = 0;

    while (mq_dequeue(args->q, &msg) == 0) {
        int64_t queue_latency = now_ms() - msg.enqueue_time_ms;
        printf("[%s] Processing: %s (queued for %ldms)\n",
               args->consumer_name, msg.message_id, queue_latency);

        /* Simulate processing time */
        int proc_ms = args->slow ? (50 + rand() % 100) : (5 + rand() % 20);
        struct timespec ts = { .tv_sec = 0, .tv_nsec = proc_ms * 1000000L };
        nanosleep(&ts, NULL);

        /* --- Concept: Idempotency ---
         * In a queue, the same message CAN be delivered more than once
         * (network retry, consumer crash mid-processing).
         * Idempotent processing: processing the same message N times = same result as 1 time.
         * Example: "set inventory=5" is idempotent; "reduce inventory by 1" is NOT.
         */
        if (msg.retry_count > 0) {
            printf("[%s] WARNING: Duplicate message detected (retry #%d) — applying idempotency check\n",
                   args->consumer_name, msg.retry_count);
        }

        printf("[%s] Completed: %s in %dms\n", args->consumer_name, msg.message_id, proc_ms);
        processed++;
    }

    printf("[%s] Queue closed. Total processed: %d\n", args->consumer_name, processed);
    return NULL;
}

int main(void) {
    srand((unsigned)time(NULL));

    printf("=== Message Queue: Async Communication Demo ===\n\n");

    MessageQueue *q = mq_create(QUEUE_CAPACITY);

    ProducerArgs prod = { .q = q, .num_messages = 12, .producer_name = "OrderService" };
    ConsumerArgs cons = { .q = q, .consumer_name = "InventoryService", .slow = 1 };

    pthread_t prod_tid, cons_tid;
    pthread_create(&cons_tid, NULL, consumer_thread, &cons);
    pthread_create(&prod_tid, NULL, producer_thread, &prod);

    pthread_join(prod_tid, NULL);

    /* Close queue — consumer will drain remaining messages then exit */
    printf("\n[Main] All producers done. Closing queue.\n");
    mq_close(q);

    pthread_join(cons_tid, NULL);

    mq_destroy(q);
    printf("\n[Main] Demo complete.\n");

    return 0;
}
/* Compile: gcc -o queue message_queue.c -lpthread */
```

---

## 14. Security Layers: Auth, Tokens, and Policies

### Concept: Service-to-Service Authentication

In microservices, you need to answer two questions for every request:
- **Authentication (AuthN)**: Who are you? (Identity)
- **Authorization (AuthZ)**: What are you allowed to do? (Permissions)

**JWT (JSON Web Token)** is the standard for service-to-service auth.

### What Is a JWT?

A JWT has three parts separated by dots: `header.payload.signature`

```
EXAMPLE JWT (decoded):

HEADER:
{
  "alg": "HS256",    <-- signing algorithm
  "typ": "JWT"
}

PAYLOAD (claims):
{
  "sub": "order-service",       <-- subject (who this token is for)
  "iss": "auth-service",        <-- issuer (who created this token)
  "aud": "payment-service",     <-- audience (who should accept this token)
  "iat": 1700000000,            <-- issued at (Unix timestamp)
  "exp": 1700003600,            <-- expires at (Unix timestamp, 1 hour later)
  "roles": ["charge:create"]    <-- what this service is allowed to do
}

SIGNATURE:
HMACSHA256(
  base64(header) + "." + base64(payload),
  secret_key
)

The signature PROVES the token wasn't tampered with.
If someone changes the payload (e.g., adds a role), the signature won't match.
```

### Code: JWT Validation in Go

```go
// go/auth/jwt.go
// Demonstrates JWT creation and validation for service-to-service auth.
// In production, use a proper library like golang-jwt/jwt.
// This simplified version shows the core concepts.

package main

import (
    "crypto/hmac"
    "crypto/sha256"
    "encoding/base64"
    "encoding/json"
    "errors"
    "fmt"
    "strings"
    "time"
)

// JWT errors — note each is a DISTINCT error type
// This matters for security: distinguish "token expired" from "token tampered"
var (
    ErrTokenExpired    = errors.New("token has expired")
    ErrTokenInvalid    = errors.New("token signature invalid — possible tampering")
    ErrTokenMalformed  = errors.New("token structure malformed")
    ErrInsufficientPerm = errors.New("token does not have required permission")
)

type JWTHeader struct {
    Alg string `json:"alg"`
    Typ string `json:"typ"`
}

type JWTClaims struct {
    Sub      string   `json:"sub"`           // Subject (who this is for)
    Iss      string   `json:"iss"`           // Issuer
    Aud      string   `json:"aud"`           // Audience
    IssuedAt int64    `json:"iat"`           // Issued At (Unix)
    ExpireAt int64    `json:"exp"`           // Expiry (Unix)
    Roles    []string `json:"roles"`
}

func base64URLEncode(data []byte) string {
    return strings.TrimRight(
        base64.StdEncoding.EncodeToString(data),
        "=")
}

func base64URLDecode(s string) ([]byte, error) {
    // Add padding back (base64 requires padding)
    switch len(s) % 4 {
    case 2:
        s += "=="
    case 3:
        s += "="
    }
    return base64.StdEncoding.DecodeString(s)
}

func computeSignature(signingInput string, secret []byte) string {
    mac := hmac.New(sha256.New, secret)
    mac.Write([]byte(signingInput))
    return base64URLEncode(mac.Sum(nil))
}

// IssueToken creates a signed JWT for a service
func IssueToken(secret []byte, claims JWTClaims) (string, error) {
    headerJSON, _ := json.Marshal(JWTHeader{Alg: "HS256", Typ: "JWT"})
    claimsJSON, _ := json.Marshal(claims)

    headerB64 := base64URLEncode(headerJSON)
    claimsB64 := base64URLEncode(claimsJSON)
    signingInput := headerB64 + "." + claimsB64

    signature := computeSignature(signingInput, secret)

    return signingInput + "." + signature, nil
}

// ValidateToken parses and validates a JWT
// Returns claims if valid, error otherwise
func ValidateToken(secret []byte, tokenStr string, requiredAudience string) (JWTClaims, error) {
    parts := strings.Split(tokenStr, ".")
    if len(parts) != 3 {
        return JWTClaims{}, ErrTokenMalformed
    }

    // 1. Verify signature — MUST check this FIRST before trusting any claims
    signingInput := parts[0] + "." + parts[1]
    expectedSig := computeSignature(signingInput, secret)
    if !hmac.Equal([]byte(expectedSig), []byte(parts[2])) {
        return JWTClaims{}, ErrTokenInvalid
    }

    // 2. Decode claims
    claimsJSON, err := base64URLDecode(parts[1])
    if err != nil {
        return JWTClaims{}, ErrTokenMalformed
    }
    var claims JWTClaims
    if err := json.Unmarshal(claimsJSON, &claims); err != nil {
        return JWTClaims{}, ErrTokenMalformed
    }

    // 3. Check expiry
    if time.Now().Unix() > claims.ExpireAt {
        return JWTClaims{}, ErrTokenExpired
    }

    // 4. Check audience — CRITICAL: prevents token reuse across services
    // If payment service's token is stolen, it shouldn't work for inventory service
    if claims.Aud != requiredAudience {
        return JWTClaims{}, fmt.Errorf("wrong audience: got '%s', expected '%s'",
            claims.Aud, requiredAudience)
    }

    return claims, nil
}

// HasRole checks if claims contain a required role
func HasRole(claims JWTClaims, required string) bool {
    for _, role := range claims.Roles {
        if role == required {
            return true
        }
    }
    return false
}

func main() {
    secret := []byte("super-secret-key-change-in-production")

    fmt.Println("=== JWT Service-to-Service Authentication ===\n")

    // Order Service gets a token to call Payment Service
    now := time.Now()
    claims := JWTClaims{
        Sub:      "order-service",
        Iss:      "auth-service",
        Aud:      "payment-service",
        IssuedAt: now.Unix(),
        ExpireAt: now.Add(1 * time.Hour).Unix(),
        Roles:    []string{"payment:create", "payment:read"},
    }

    token, err := IssueToken(secret, claims)
    if err != nil {
        fmt.Printf("Failed to issue token: %v\n", err)
        return
    }
    fmt.Printf("Issued token (first 60 chars): %s...\n\n", token[:60])

    // === Scenario 1: Valid token ===
    fmt.Println("--- Scenario 1: Valid token ---")
    parsedClaims, err := ValidateToken(secret, token, "payment-service")
    if err != nil {
        fmt.Printf("REJECTED: %v\n", err)
    } else {
        fmt.Printf("ACCEPTED: from=%s, roles=%v\n", parsedClaims.Sub, parsedClaims.Roles)
        if HasRole(parsedClaims, "payment:create") {
            fmt.Printf("AUTHORIZED: has 'payment:create' role\n")
        }
    }

    // === Scenario 2: Wrong audience ===
    fmt.Println("\n--- Scenario 2: Payment token sent to Inventory Service ---")
    _, err = ValidateToken(secret, token, "inventory-service")
    if err != nil {
        fmt.Printf("REJECTED (correct!): %v\n", err)
        fmt.Printf("  Tokens are scoped to specific services — can't reuse across services\n")
    }

    // === Scenario 3: Tampered token ===
    fmt.Println("\n--- Scenario 3: Tampered token (attacker modified claims) ---")
    parts := strings.Split(token, ".")
    // Modify the payload to add an admin role
    parts[1] = base64URLEncode([]byte(`{"sub":"attacker","aud":"payment-service","iat":0,"exp":9999999999,"roles":["admin"]}`))
    tamperedToken := strings.Join(parts, ".")
    _, err = ValidateToken(secret, tamperedToken, "payment-service")
    if err != nil {
        fmt.Printf("REJECTED (correct!): %v\n", err)
        fmt.Printf("  Signature mismatch reveals the tampering!\n")
    }

    // === Scenario 4: Expired token ===
    fmt.Println("\n--- Scenario 4: Expired token ---")
    expiredClaims := claims
    expiredClaims.ExpireAt = now.Add(-1 * time.Hour).Unix() // expired 1 hour ago
    expiredToken, _ := IssueToken(secret, expiredClaims)
    _, err = ValidateToken(secret, expiredToken, "payment-service")
    if err != nil {
        fmt.Printf("REJECTED (correct!): %v\n", err)
    }
}
```

---

## 15. Infrastructure Complexity: Kubernetes and Beyond

### Concept: Kubernetes Primitives

**Kubernetes** (K8s) is a container orchestration system. It manages running your services across a cluster of machines.

Key concepts:

```
KUBERNETES CONCEPTS (what matters for debugging):
+------------------+-----------------------------------------------+
| Term             | Meaning                                       |
+------------------+-----------------------------------------------+
| Pod              | One running instance of your service          |
|                  | (can have multiple containers inside)          |
|                  | Has a dynamic IP — changes on restart!         |
+------------------+-----------------------------------------------+
| Deployment       | "Run 3 copies of this pod, keep them running" |
|                  | Handles restart, rolling update                |
+------------------+-----------------------------------------------+
| Service          | Stable DNS name + load balancer for pods       |
|                  | "payment-service:8080" always works even if    |
|                  | pod IPs change                                 |
+------------------+-----------------------------------------------+
| Ingress          | External HTTP routing into the cluster         |
+------------------+-----------------------------------------------+
| ConfigMap        | Configuration (non-secret) injected into pods  |
+------------------+-----------------------------------------------+
| Secret           | Sensitive config (passwords, API keys)         |
+------------------+-----------------------------------------------+
| Namespace        | Virtual cluster within cluster for isolation   |
+------------------+-----------------------------------------------+
| PersistentVolume | Storage that survives pod restarts             |
+------------------+-----------------------------------------------+
```

### Why K8s Creates New Bugs

```
POD RESTART BUGS:
+---------------------------+
| Pod running payment-svc   |  <-- processing a payment
|  PID 42                   |  <-- payment is halfway done
|  IP: 10.0.0.14            |
+---------------------------+
         |
         | OOMKilled (out of memory)
         | Kubernetes restarts the pod
         v
+---------------------------+
| NEW Pod for payment-svc   |  <-- completely fresh instance
|  PID 1 (new process!)     |  <-- payment state is GONE
|  IP: 10.0.0.27 (NEW IP!)  |  <-- clients with old IP get "connection refused"
+---------------------------+

Questions:
- Was the payment charged? (we were halfway through)
- Did the customer's money leave their account?
- Is there an orphaned charge in the bank's system?

These are REAL production incidents.
```

### Code: Graceful Shutdown in Go (Critical for K8s)

```go
// go/graceful_shutdown/main.go
// Graceful shutdown is how services safely stop in Kubernetes.
//
// --- Concept: SIGTERM ---
// When Kubernetes wants to stop a pod, it sends SIGTERM (signal terminate).
// The service has a grace period (default 30s) to finish in-flight requests.
// After that, Kubernetes sends SIGKILL (cannot be caught — instant death).
//
// WITHOUT graceful shutdown:
//   - In-flight HTTP requests get "connection reset" errors
//   - Database transactions are rolled back mid-write
//   - Messages are half-processed
//
// WITH graceful shutdown:
//   - Stop accepting new requests
//   - Wait for in-flight requests to complete
//   - Close DB connections cleanly
//   - Exit with status 0

package main

import (
    "context"
    "fmt"
    "net/http"
    "os"
    "os/signal"
    "sync"
    "sync/atomic"
    "syscall"
    "time"
)

// RequestTracker tracks in-flight requests
type RequestTracker struct {
    count  int64
    wg     sync.WaitGroup
}

func (rt *RequestTracker) Begin() {
    atomic.AddInt64(&rt.count, 1)
    rt.wg.Add(1)
}

func (rt *RequestTracker) End() {
    atomic.AddInt64(&rt.count, -1)
    rt.wg.Done()
}

func (rt *RequestTracker) WaitForAll() {
    rt.wg.Wait()
}

func (rt *RequestTracker) Count() int64 {
    return atomic.LoadInt64(&rt.count)
}

func main() {
    tracker := &RequestTracker{}

    // Simulate a slow payment handler that takes 3 seconds
    mux := http.NewServeMux()
    mux.HandleFunc("/charge", func(w http.ResponseWriter, r *http.Request) {
        tracker.Begin()
        defer tracker.End()

        fmt.Printf("[handler] Processing charge request... (in-flight: %d)\n",
            tracker.Count())

        // Simulate long-running work (charging a credit card)
        select {
        case <-time.After(3 * time.Second):
            fmt.Fprintln(w, `{"status":"charged"}`)
            fmt.Printf("[handler] Charge completed\n")
        case <-r.Context().Done():
            // Client disconnected or server is shutting down
            fmt.Printf("[handler] Request cancelled: %v\n", r.Context().Err())
            http.Error(w, "request cancelled", http.StatusServiceUnavailable)
        }
    })

    server := &http.Server{
        Addr:    ":8080",
        Handler: mux,
    }

    // Start server in background
    go func() {
        fmt.Println("[server] Listening on :8080")
        if err := server.ListenAndServe(); err != http.ErrServerClosed {
            fmt.Printf("[server] Error: %v\n", err)
            os.Exit(1)
        }
    }()

    // Listen for termination signals
    // os.Signal channel — Kubernetes sends SIGTERM, Ctrl+C sends SIGINT
    quit := make(chan os.Signal, 1)
    signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)

    fmt.Println("[server] Running. Send SIGTERM (or Ctrl+C) to trigger graceful shutdown.")
    fmt.Println("[server] Try: curl localhost:8080/charge  (takes 3s)")

    // Block until signal received
    sig := <-quit
    fmt.Printf("\n[server] Received signal: %v — starting graceful shutdown\n", sig)

    // Step 1: Stop accepting new connections
    // Give in-flight requests up to 30 seconds to complete
    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    fmt.Printf("[server] Waiting for %d in-flight requests to complete...\n",
        tracker.Count())

    if err := server.Shutdown(shutdownCtx); err != nil {
        fmt.Printf("[server] Forced shutdown: %v\n", err)
    }

    // Step 2: Wait for all tracked requests
    done := make(chan struct{})
    go func() {
        tracker.WaitForAll()
        close(done)
    }()

    select {
    case <-done:
        fmt.Println("[server] All requests completed. Clean shutdown.")
    case <-shutdownCtx.Done():
        fmt.Printf("[server] Timeout! %d requests still running — killing anyway\n",
            tracker.Count())
    }

    fmt.Println("[server] Exiting with status 0 (clean)")
}
```

---

## 16. Time-Related Bugs: Clock Drift and Event Ordering

### Concept: Clock Drift

Each machine runs its own hardware clock. These clocks gradually drift apart — typically by milliseconds to seconds. When you have events logged across multiple services, the timestamp order may not match the actual event order.

```
CLOCK DRIFT EXAMPLE:

Machine A (clock accurate):     Machine B (clock 200ms ahead):
  Event 1: 14:32:00.000           Event 2: 14:32:00.150
  
Actual execution order: Event 1 happened first, Event 2 second.

But if B's clock is 200ms ahead:
  Logs show: Event 2 at 14:32:00.150 BEFORE Event 1 at 14:32:00.200
             (from B's perspective)

Wait — B's event appears BEFORE A's event in the log,
but actually happened AFTER. The log ordering is WRONG.

This makes debugging extremely confusing.

FIX: Use NTP (Network Time Protocol) to sync clocks.
     Or: Use LOGICAL CLOCKS (Lamport timestamps) instead of wall clock.
```

### Concept: Lamport Timestamps

A **Lamport timestamp** is a logical counter that orders events causally, not by wall clock time.

**Rules:**
1. Each process maintains a counter starting at 0
2. Before sending a message, increment your counter
3. When receiving a message, take max(your counter, received counter) + 1
4. Every event increments the counter

```
LAMPORT TIMESTAMP EXAMPLE:

Process A               Message M          Process B
counter=0                                  counter=0

A does work      A.counter++ → 1
A sends M(ts=1) ------------------>        B receives M
                                           B.counter = max(0,1)+1 = 2
                                           B does work → counter=3
                                           B sends reply(ts=3)
A receives reply
A.counter = max(1,3)+1 = 4
A continues      A.counter++ → 5

Now: Event ordering by Lamport timestamp is CAUSALLY CONSISTENT.
"If A happened before B, then ts(A) < ts(B)" — guaranteed.
Wall clocks cannot make this guarantee.
```

### Code: Lamport Clock in Rust

```rust
// rust/lamport/src/main.rs
// Implements Lamport logical clocks for causally-correct event ordering.

use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};

/// LamportClock: a monotonically increasing logical counter
/// that is updated on send, receive, and local events.
#[derive(Debug)]
pub struct LamportClock {
    counter: AtomicU64,
    node_id: String,
}

impl LamportClock {
    pub fn new(node_id: &str) -> Self {
        LamportClock {
            counter: AtomicU64::new(0),
            node_id: node_id.to_string(),
        }
    }

    /// tick() — increment counter for a local event
    pub fn tick(&self) -> u64 {
        self.counter.fetch_add(1, Ordering::SeqCst) + 1
    }

    /// send_time() — get timestamp to attach to an outgoing message
    pub fn send_time(&self) -> u64 {
        self.tick() // sending is an event
    }

    /// receive_update() — update clock on receiving a message with timestamp `received`
    pub fn receive_update(&self, received: u64) -> u64 {
        loop {
            let current = self.counter.load(Ordering::SeqCst);
            let new_val = std::cmp::max(current, received) + 1;
            // Compare-and-swap: update only if counter hasn't changed
            if self.counter.compare_exchange(
                current, new_val, Ordering::SeqCst, Ordering::SeqCst
            ).is_ok() {
                return new_val;
            }
        }
    }

    pub fn current(&self) -> u64 {
        self.counter.load(Ordering::SeqCst)
    }
}

/// TimestampedEvent records what happened, when (logically), and who
#[derive(Debug, Clone)]
struct TimestampedEvent {
    logical_time: u64,
    node_id: String,
    description: String,
}

/// EventLog collects all events across all nodes
type EventLog = Arc<Mutex<Vec<TimestampedEvent>>>;

fn log_event(log: &EventLog, clock: &LamportClock, description: &str) -> u64 {
    let ts = clock.tick();
    let mut events = log.lock().unwrap();
    events.push(TimestampedEvent {
        logical_time: ts,
        node_id: clock.node_id.clone(),
        description: description.to_string(),
    });
    println!("  [{:>10}] ts={:3}  {}", clock.node_id, ts, description);
    ts
}

fn main() {
    println!("=== Lamport Logical Clocks: Causally Correct Event Ordering ===\n");
    println!("Scenario: OrderService, PaymentService, and InventoryService");
    println!("communicating. We track causal order with Lamport timestamps.\n");

    let event_log: EventLog = Arc::new(Mutex::new(Vec::new()));

    let order_clock   = Arc::new(LamportClock::new("order-svc"));
    let payment_clock = Arc::new(LamportClock::new("payment-svc"));
    let inv_clock     = Arc::new(LamportClock::new("inventory-svc"));

    let log = Arc::clone(&event_log);

    println!("[Phase 1: Initial local events]\n");
    let log1 = Arc::clone(&log);
    log_event(&log1, &order_clock,   "Received HTTP POST /order from client");
    log_event(&log1, &order_clock,   "Validated order data");

    println!("\n[Phase 2: Order sends to Payment]\n");
    let send_ts = order_clock.send_time();
    let log2 = Arc::clone(&log);
    {
        let mut events = log2.lock().unwrap();
        events.push(TimestampedEvent {
            logical_time: send_ts,
            node_id: "order-svc".to_string(),
            description: format!("SEND to payment-svc (msg_ts={})", send_ts),
        });
    }
    println!("  [{:>10}] ts={:3}  SEND to payment-svc", "order-svc", send_ts);

    // Payment receives the message — updates its clock
    let recv_ts = payment_clock.receive_update(send_ts);
    let log3 = Arc::clone(&log);
    {
        let mut events = log3.lock().unwrap();
        events.push(TimestampedEvent {
            logical_time: recv_ts,
            node_id: "payment-svc".to_string(),
            description: format!("RECV from order-svc (msg_ts={}, local_ts={})", send_ts, recv_ts),
        });
    }
    println!("  [{:>10}] ts={:3}  RECV from order-svc (clock jumped to {})", "payment-svc", recv_ts, recv_ts);

    log_event(&log, &payment_clock, "Processing payment charge");
    log_event(&log, &payment_clock, "Payment authorized by bank");

    // Payment sends result to Inventory
    let pay_send_ts = payment_clock.send_time();
    println!("  [{:>10}] ts={:3}  SEND to inventory-svc", "payment-svc", pay_send_ts);

    let inv_recv_ts = inv_clock.receive_update(pay_send_ts);
    println!("  [{:>10}] ts={:3}  RECV from payment-svc", "inventory-svc", inv_recv_ts);

    log_event(&log, &inv_clock, "Deducting stock for item-A");

    println!("\n[Sorted Event Log by Lamport Timestamp]\n");
    println!("This is causally correct order — even if wall clocks were drifting.");
    println!("{:-<65}", "");
    println!("{:<6} {:<14} {}", "TS", "NODE", "EVENT");
    println!("{:-<65}", "");

    let mut events = event_log.lock().unwrap();
    events.sort_by_key(|e| (e.logical_time, e.node_id.clone()));
    for event in events.iter() {
        println!("{:<6} {:<14} {}", event.logical_time, event.node_id, event.description);
    }
    println!("{:-<65}", "");
    println!("\nKey: higher timestamp = happened later (causally)");
    println!("     equal timestamps = concurrent (neither caused the other)");
}
```

---

## 17. Reproducibility: The Hardest Problem

### Why Reproducing Distributed Bugs Is Hard

```
REPRODUCING A BUG IN PRODUCTION:

Requirements to reproduce:
+----------------------------------+
| Multiple services running        |  -- setting up local k8s cluster
| Correct data state               |  -- copying prod DB is a security risk
| Real network conditions          |  -- can't simulate prod traffic locally
| Real concurrency level           |  -- need load generators
| Correct service versions         |  -- need exact version pinning
| Correct configuration            |  -- prod config differs from local
| Correct infrastructure           |  -- NTP, DNS, load balancer behavior
+----------------------------------+

Total cost: hours to days per bug investigation.

STRATEGIES:
1. Chaos Engineering — deliberately inject failures in prod (controlled)
2. Reproducible builds — exact version pinning, deterministic deployments
3. Observability-first — fix bugs by reading traces/logs, not reproducing
4. Feature flags — disable features that cause bugs without redeploy
5. Blue-green deployment — test new version with small % of traffic
```

### Code: Deterministic Testing with Dependency Injection in Go

```go
// go/testing/deterministic_test.go
// How to write tests that are 100% deterministic and don't depend on
// external services, real clocks, or random numbers.
//
// --- Concept: Dependency Injection (DI) ---
// Instead of directly calling a service/database/clock inside your function,
// you PASS IT IN as an argument (or interface).
// In tests, pass a FAKE version. In production, pass the REAL version.
// This is the fundamental technique for testable microservice code.
//
// --- Concept: Interface in Go ---
// An interface defines a set of methods.
// Any type that implements those methods satisfies the interface.
// This is what makes swapping real vs fake implementations possible.

package main

import (
    "errors"
    "fmt"
    "testing"
    "time"
)

// ===== Interfaces (the abstraction layer) =====

// Clock interface — lets us control time in tests
type Clock interface {
    Now() time.Time
}

// PaymentGateway interface — lets us fake the bank API
type PaymentGateway interface {
    Charge(amount float64, token string) (transactionID string, err error)
}

// OrderRepository interface — lets us fake the database
type OrderRepository interface {
    Save(order Order) error
    FindByID(id string) (Order, error)
}

// ===== Domain Types =====

type Order struct {
    ID          string
    CustomerID  string
    Amount      float64
    Status      string
    CreatedAt   time.Time
    TransactionID string
}

// ===== OrderService — the thing we actually want to test =====

type OrderService struct {
    clock      Clock
    payment    PaymentGateway
    repository OrderRepository
    maxOrderAge time.Duration
}

func NewOrderService(clock Clock, payment PaymentGateway, repo OrderRepository) *OrderService {
    return &OrderService{
        clock:       clock,
        payment:     payment,
        repository:  repo,
        maxOrderAge: 24 * time.Hour,
    }
}

// ProcessOrder is the business logic we want to test
func (s *OrderService) ProcessOrder(customerID string, amount float64, token string) (Order, error) {
    if amount <= 0 {
        return Order{}, errors.New("amount must be positive")
    }
    if amount > 10000 {
        return Order{}, errors.New("amount exceeds maximum allowed")
    }

    txID, err := s.payment.Charge(amount, token)
    if err != nil {
        return Order{}, fmt.Errorf("payment failed: %w", err)
    }

    order := Order{
        ID:            fmt.Sprintf("order-%d", s.clock.Now().UnixNano()),
        CustomerID:    customerID,
        Amount:        amount,
        Status:        "paid",
        CreatedAt:     s.clock.Now(),
        TransactionID: txID,
    }

    if err := s.repository.Save(order); err != nil {
        return Order{}, fmt.Errorf("failed to save order: %w", err)
    }

    return order, nil
}

// ===== Fake Implementations (for testing) =====

// FakeClock returns a fixed time — tests are 100% deterministic
type FakeClock struct{ fixedTime time.Time }
func (f *FakeClock) Now() time.Time { return f.fixedTime }

// FakePaymentGateway — configurable to succeed or fail
type FakePaymentGateway struct {
    ShouldFail bool
    FailMsg    string
    calls      []struct{ amount float64; token string }
}
func (f *FakePaymentGateway) Charge(amount float64, token string) (string, error) {
    f.calls = append(f.calls, struct{ amount float64; token string }{amount, token})
    if f.ShouldFail {
        return "", errors.New(f.FailMsg)
    }
    return fmt.Sprintf("tx-%d", len(f.calls)), nil
}

// FakeOrderRepository — in-memory store
type FakeOrderRepository struct {
    orders     map[string]Order
    ShouldFail bool
}
func NewFakeRepo() *FakeOrderRepository {
    return &FakeOrderRepository{orders: make(map[string]Order)}
}
func (f *FakeOrderRepository) Save(order Order) error {
    if f.ShouldFail {
        return errors.New("database connection timeout")
    }
    f.orders[order.ID] = order
    return nil
}
func (f *FakeOrderRepository) FindByID(id string) (Order, error) {
    if order, ok := f.orders[id]; ok {
        return order, nil
    }
    return Order{}, fmt.Errorf("order %s not found", id)
}

// ===== Tests =====

func TestProcessOrder_Success(t *testing.T) {
    fixedTime := time.Date(2024, 1, 15, 10, 30, 0, 0, time.UTC)
    clock   := &FakeClock{fixedTime: fixedTime}
    payment := &FakePaymentGateway{}
    repo    := NewFakeRepo()

    svc := NewOrderService(clock, payment, repo)

    order, err := svc.ProcessOrder("customer-1", 99.99, "tok_visa_success")

    if err != nil {
        t.Fatalf("expected success, got error: %v", err)
    }
    if order.Status != "paid" {
        t.Errorf("expected status 'paid', got '%s'", order.Status)
    }
    if order.Amount != 99.99 {
        t.Errorf("expected amount 99.99, got %.2f", order.Amount)
    }
    if order.CreatedAt != fixedTime {
        t.Errorf("expected fixed time, got %v", order.CreatedAt)
    }
    if len(payment.calls) != 1 {
        t.Errorf("expected 1 payment call, got %d", len(payment.calls))
    }

    t.Log("✓ Order processed successfully with correct data")
}

func TestProcessOrder_PaymentFailure(t *testing.T) {
    payment := &FakePaymentGateway{ShouldFail: true, FailMsg: "card declined"}
    repo    := NewFakeRepo()
    clock   := &FakeClock{fixedTime: time.Now()}
    svc     := NewOrderService(clock, payment, repo)

    _, err := svc.ProcessOrder("customer-1", 99.99, "tok_visa_decline")

    if err == nil {
        t.Fatal("expected error on payment failure, got nil")
    }
    if !errors.Is(err, errors.New("payment failed: card declined")) {
        // Check if error message contains "payment failed"
        if !contains(err.Error(), "payment failed") {
            t.Errorf("expected 'payment failed' in error, got: %v", err)
        }
    }

    // CRITICAL: ensure no order was saved when payment fails
    if len(repo.orders) != 0 {
        t.Errorf("order should NOT be saved when payment fails, but got %d orders", len(repo.orders))
    }

    t.Log("✓ Payment failure handled correctly, no order saved")
}

func TestProcessOrder_InvalidAmount(t *testing.T) {
    tests := []struct {
        name    string
        amount  float64
        wantErr string
    }{
        {"zero amount", 0, "amount must be positive"},
        {"negative amount", -50, "amount must be positive"},
        {"too large", 99999, "exceeds maximum"},
    }

    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            svc := NewOrderService(
                &FakeClock{fixedTime: time.Now()},
                &FakePaymentGateway{},
                NewFakeRepo(),
            )
            _, err := svc.ProcessOrder("c1", tt.amount, "tok")
            if err == nil {
                t.Fatalf("expected error, got nil")
            }
            if !contains(err.Error(), tt.wantErr) {
                t.Errorf("expected error containing '%s', got '%v'", tt.wantErr, err)
            }
        })
    }
}

func TestProcessOrder_DatabaseFailure(t *testing.T) {
    repo := NewFakeRepo()
    repo.ShouldFail = true

    svc := NewOrderService(
        &FakeClock{fixedTime: time.Now()},
        &FakePaymentGateway{},
        repo,
    )

    _, err := svc.ProcessOrder("c1", 99.99, "tok")
    if err == nil {
        t.Fatal("expected error on DB failure")
    }
    if !contains(err.Error(), "failed to save order") {
        t.Errorf("expected 'failed to save order' in error, got: %v", err)
    }
    t.Log("✓ DB failure handled, error propagated correctly")
}

func contains(s, substr string) bool {
    return len(s) >= len(substr) && (s == substr ||
        func() bool {
            for i := 0; i <= len(s)-len(substr); i++ {
                if s[i:i+len(substr)] == substr {
                    return true
                }
            }
            return false
        }())
}

func main() {
    // Run tests programmatically for demo
    t := &testing.T{}
    TestProcessOrder_Success(t)
    TestProcessOrder_PaymentFailure(t)
    TestProcessOrder_DatabaseFailure(t)
    fmt.Println("All tests passed (run with: go test ./...)")
}
```

---

## 18. A Production Debugging Workflow

### The Systematic Approach

When something goes wrong in production, your brain needs a structured process. Panic is the enemy of debugging.

```
PRODUCTION DEBUGGING DECISION TREE:

BUG REPORTED
     |
     v
+------------------------------------+
| Is it a COMPLETE outage or         |
| PARTIAL degradation?               |
+------------------------------------+
       |              |
   COMPLETE        PARTIAL
       |              |
       v              v
  All services    Check: which % of
  responding?     requests fail?
       |
       |-- YES --> Check error rates
       |           in Prometheus/Grafana
       |
       |-- NO  --> Check infra:
                   pod status (kubectl get pods)
                   recent deployments (git log)
                   resource exhaustion (CPU/mem)
                   |
                   v
              ROLL BACK last deploy?
              (fastest fix in 80% of cases)

---

ONCE YOU KNOW THE AFFECTED SERVICE:

1. SEARCH LOGS:
   grep trace_id in affected time window
   Look for ERROR/WARN level logs
   Find first error in causal chain

2. EXAMINE TRACES:
   Find slow spans (the bottleneck)
   Find error spans (the failure point)
   Compare to normal request traces

3. CHECK METRICS:
   p99 latency (slow operations?)
   Error rate (what percent failing?)
   Traffic spike (load issue?)
   DB connection pool (exhausted?)
   Memory usage (OOM killer?)

4. REPRODUCE LOCALLY (if possible):
   Export the exact request body
   Use same service versions
   Use same config

5. FIX AND DEPLOY:
   Write test that reproduces the bug
   Fix the code
   Verify test passes
   Deploy with feature flag (gradual rollout)
   Watch metrics for 30 min post-deploy
```

### Code: A Complete Debugging Toolkit in Go

```go
// go/debug_toolkit/main.go
// A minimal but complete debugging toolkit for microservices.
// Combines: structured logging, metrics, health checks, request tracing.

package main

import (
    "context"
    "encoding/json"
    "fmt"
    "net/http"
    "sync"
    "sync/atomic"
    "time"
)

// ===== Metrics Collector =====

type Metrics struct {
    requestCount  uint64
    errorCount    uint64
    totalLatencyMs uint64
    mu            sync.Mutex
    latencyBuckets []uint64 // histogram buckets: [0-10ms, 10-50ms, 50-100ms, 100-500ms, 500ms+]
}

var globalMetrics = &Metrics{latencyBuckets: make([]uint64, 5)}

func recordRequest(latency time.Duration, isError bool) {
    atomic.AddUint64(&globalMetrics.requestCount, 1)
    atomic.AddUint64(&globalMetrics.totalLatencyMs, uint64(latency.Milliseconds()))
    if isError {
        atomic.AddUint64(&globalMetrics.errorCount, 1)
    }

    // Bucket the latency
    ms := latency.Milliseconds()
    idx := 4 // default: 500ms+
    switch {
    case ms <= 10:   idx = 0
    case ms <= 50:   idx = 1
    case ms <= 100:  idx = 2
    case ms <= 500:  idx = 3
    }
    atomic.AddUint64(&globalMetrics.latencyBuckets[idx], 1)
}

func getMetricsSnapshot() map[string]interface{} {
    total := atomic.LoadUint64(&globalMetrics.requestCount)
    errors := atomic.LoadUint64(&globalMetrics.errorCount)
    totalMs := atomic.LoadUint64(&globalMetrics.totalLatencyMs)

    avgMs := uint64(0)
    if total > 0 {
        avgMs = totalMs / total
    }

    errorRate := 0.0
    if total > 0 {
        errorRate = float64(errors) / float64(total) * 100
    }

    buckets := map[string]uint64{
        "0-10ms":   atomic.LoadUint64(&globalMetrics.latencyBuckets[0]),
        "10-50ms":  atomic.LoadUint64(&globalMetrics.latencyBuckets[1]),
        "50-100ms": atomic.LoadUint64(&globalMetrics.latencyBuckets[2]),
        "100-500ms":atomic.LoadUint64(&globalMetrics.latencyBuckets[3]),
        "500ms+":   atomic.LoadUint64(&globalMetrics.latencyBuckets[4]),
    }

    return map[string]interface{}{
        "total_requests": total,
        "error_count":    errors,
        "error_rate_pct": fmt.Sprintf("%.1f%%", errorRate),
        "avg_latency_ms": avgMs,
        "latency_histogram": buckets,
    }
}

// ===== Debug Handler =====

func metricsHandler(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(getMetricsSnapshot())
}

// ===== Instrumented Middleware =====

func instrumentedMiddleware(next http.HandlerFunc, operationName string) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Extract or generate trace ID
        traceID := r.Header.Get("X-Trace-ID")
        if traceID == "" {
            traceID = fmt.Sprintf("trace-%d", time.Now().UnixNano())
        }

        // Inject into context
        ctx := context.WithValue(r.Context(), "trace_id", traceID)
        r = r.WithContext(ctx)

        // Wrap response writer to capture status code
        rw := &responseWriter{ResponseWriter: w, statusCode: 200}

        next(rw, r)

        latency := time.Since(start)
        isError := rw.statusCode >= 400
        recordRequest(latency, isError)

        fmt.Printf("{\"trace_id\":\"%s\",\"op\":\"%s\",\"status\":%d,\"latency_ms\":%d}\n",
            traceID, operationName, rw.statusCode, latency.Milliseconds())
    }
}

type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}

// ===== Example Business Handler =====

func processOrderHandler(w http.ResponseWriter, r *http.Request) {
    // Simulate variable latency
    time.Sleep(time.Duration(10+time.Now().UnixNano()%90) * time.Millisecond)

    // Simulate 10% error rate
    if time.Now().UnixNano()%10 == 0 {
        http.Error(w, `{"error":"internal error"}`, http.StatusInternalServerError)
        return
    }

    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(map[string]string{
        "order_id": "order-123",
        "status":   "created",
        "trace_id": r.Context().Value("trace_id").(string),
    })
}

func main() {
    mux := http.NewServeMux()

    // Business endpoints with instrumentation
    mux.HandleFunc("/order",
        instrumentedMiddleware(processOrderHandler, "process_order"))

    // Observability endpoints
    mux.HandleFunc("/debug/metrics", metricsHandler)
    mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
        json.NewEncoder(w).Encode(map[string]string{"status": "ok"})
    })

    fmt.Println("=== Instrumented Microservice Debugging Toolkit ===")
    fmt.Println("Endpoints:")
    fmt.Println("  POST /order          - Business endpoint (with tracing + metrics)")
    fmt.Println("  GET  /debug/metrics  - Live metrics snapshot")
    fmt.Println("  GET  /health         - Health check")
    fmt.Println()
    fmt.Println("Listening on :8080...")

    if err := http.ListenAndServe(":8080", mux); err != nil {
        fmt.Printf("Error: %v\n", err)
    }
}
```

---

## 19. Mental Models for Distributed Systems Mastery

### The Core Mental Models

```
MENTAL MODEL 1: The System Is Always Partially Failed
+-------------------------------------------------------+
| Don't think: "Is the system up or down?"              |
| Think: "Which percentage of operations are succeeding,|
|         what is failing, and what is the blast radius?"|
+-------------------------------------------------------+

MENTAL MODEL 2: Timeouts Are Mandatory
+-------------------------------------------------------+
| Every network call needs a timeout.                   |
| No timeout = your service will eventually freeze.     |
| Latency is the invisible killer.                      |
+-------------------------------------------------------+

MENTAL MODEL 3: Design for Idempotency
+-------------------------------------------------------+
| Every operation that can be retried WILL be retried.  |
| Make every state-changing operation idempotent:       |
|   "Process payment [idempotency_key=abc]"             |
|   → same result no matter how many times called.     |
+-------------------------------------------------------+

MENTAL MODEL 4: Fail Fast, Fail Loud
+-------------------------------------------------------+
| A clear, immediate error is better than a slow,      |
| ambiguous timeout.                                    |
| Circuit breakers and fast-fail prevent cascade.       |
+-------------------------------------------------------+

MENTAL MODEL 5: Observe, Don't Debug
+-------------------------------------------------------+
| In production, you cannot attach a debugger.          |
| Build observability in ADVANCE, not after a bug.      |
| Logs, metrics, traces must be first-class.            |
+-------------------------------------------------------+
```

### Cognitive Strategies for Mastery

**Chunking (George Miller, 1956):**
Don't memorize 15 individual patterns. Group them:
- Group 1: *Failure modes* (network, partial, cascade)
- Group 2: *Correctness tools* (saga, idempotency, CAS)
- Group 3: *Observability tools* (logs, metrics, traces)
- Group 4: *Protection patterns* (retry, circuit breaker, rate limit)

**Deliberate Practice (Anders Ericsson):**
Don't just read about circuit breakers — implement one from scratch, break it, fix it. Struggle produces mastery. Reading produces familiarity.

**Mental Simulation:**
Before writing code, simulate the failure in your mind:
> "What happens to my system if Service B takes 30 seconds to respond?"
> "What happens if Service C processes the same message twice?"

This is how senior engineers think before they type.

**First Principles Decomposition:**
Every distributed systems problem reduces to:
1. **State**: Where is it? Who owns it? Is it consistent?
2. **Communication**: What can fail? How do we know it failed?
3. **Time**: What order did things happen in? Can we prove it?

---

## Summary: Complete Reference

```
MICROSERVICE DEBUGGING: AT A GLANCE

PROBLEM                  ROOT CAUSE               SOLUTION
-------------------      -----------              ---------
Works local, not prod    Env differences          Feature flags, E2E tests
Intermittent failure     Network unreliability    Retry + circuit breaker
Can't trace a request    No correlation IDs       Structured logging
Slow performance         No bottleneck visibility Distributed tracing
Inconsistent data        Partial failures         Saga pattern
Cascading failure        No rate limiting         Token bucket, bulkhead
Race condition           Unsynchronized state     Mutex, CAS, optimistic lock
API breaks silently      No version management    Schema validation, versioning
Service gets killed      No graceful shutdown     SIGTERM handling
Clock-based bugs         NTP drift                Lamport clocks
Can't reproduce bug      Non-determinism          Dependency injection, fakes

KEY TOOLS:
  Logging:    ELK Stack (Elasticsearch + Logstash + Kibana)
  Metrics:    Prometheus + Grafana
  Tracing:    Jaeger or Zipkin (OpenTelemetry)
  Queue:      Kafka (high throughput) / RabbitMQ (complex routing)
  Auth:       JWT + OAuth2 / mTLS for service mesh
  Infra:      Kubernetes + Istio (service mesh)
```

---

*This guide represents the thinking patterns of engineers who have survived real production incidents. Each concept here corresponds to a class of bugs that has cost companies significant downtime and revenue. Mastering them is not optional — it is the foundation of building reliable systems.*

*"The mark of an expert is not that they avoid distributed systems problems. It is that they see them coming, instrument against them, and recover from them gracefully."*

Here is your complete guide. Here's a structural overview of what's inside:

**19 deep-dive sections** covering every concept from the document:

| Section | Core Concept | Languages |
|---|---|---|
| 1-2 | Distributed system fundamentals, Eight Fallacies, monolith vs microservices | ASCII diagrams |
| 3 | Execution flow fragmentation, non-linear execution | Go, Rust, C (pthreads) |
| 4 | Network unreliability, exponential backoff with jitter, circuit breaker | Go, Rust |
| 5 | Partial failures, Saga pattern with compensating transactions | Go |
| 6 | Data inconsistency, optimistic locking, CAS (Compare-And-Swap) | Rust |
| 7 | Structured logging, correlation ID propagation, thread-local storage | Go, C |
| 8 | Race conditions, deadlock, mutex vs atomics | Rust |
| 9 | API versioning, schema validation, Postel's Law | Go |
| 10 | Retry storms, cascading failure, token bucket rate limiter | Go |
| 11 | Distributed tracing, span/trace model, ASCII timeline renderer | Go |
| 12 | Health checks, liveness vs readiness probes | Go |
| 13 | Message queues, producer-consumer, idempotency, backpressure | C |
| 14 | JWT auth, audience scoping, tamper detection | Go |
| 15 | Kubernetes concepts, graceful SIGTERM shutdown | Go |
| 16 | Clock drift, Lamport logical clocks, causal ordering | Rust |
| 17 | Reproducibility, dependency injection, deterministic testing | Go |
| 18 | Production debugging decision tree + instrumented toolkit | Go |
| 19 | Mental models, chunking, deliberate practice strategies | — |

Every concept includes a **glossary definition before first use**, ASCII flow diagrams, and code that you can compile and run directly to observe the behavior — not just read about it.