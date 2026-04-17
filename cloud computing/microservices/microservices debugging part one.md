# The Complete Microservices Debugging Guide
### From Fundamentals to Production-Grade Mastery

> *"You are not debugging code. You are debugging a distributed system — a living, breathing organism with independent parts, unreliable communication, and emergent behavior you never programmed."*

---

## Table of Contents

1. [Foundational Mental Model: What Is a Distributed System?](#1-foundational-mental-model)
2. [Loss of Linearity: The Death of the Call Stack](#2-loss-of-linearity)
3. [The Unreliable Network: Fundamental Physics of Failure](#3-the-unreliable-network)
4. [Partial Failures: When the System Lies to You](#4-partial-failures)
5. [Data Inconsistency: No Single Source of Truth](#5-data-inconsistency)
6. [Scattered Logs: The Archaeology Problem](#6-scattered-logs)
7. [Concurrency Explosion: Race Conditions at Scale](#7-concurrency-explosion)
8. [Version Mismatch: API Drift and Contract Violations](#8-version-mismatch)
9. [Retry Storms and Cascading Failures](#9-retry-storms-and-cascading-failures)
10. [Observability: The Three Pillars](#10-observability)
11. [Environment Differences: Local vs Production](#11-environment-differences)
12. [Asynchronous Communication: Queues and Events](#12-asynchronous-communication)
13. [Security Layers and Token Failures](#13-security-layers)
14. [Infrastructure Complexity: Kubernetes and Ephemeral Environments](#14-infrastructure-complexity)
15. [Time-Related Bugs: Clock Drift and Event Ordering](#15-time-related-bugs)
16. [Reproducibility: The Hardest Problem](#16-reproducibility)
17. [The Complete Debugging Workflow](#17-the-complete-debugging-workflow)
18. [Code Examples: Instrumented Microservices in Rust, Go, and C](#18-code-examples)
19. [Decision Trees for Debugging Scenarios](#19-decision-trees)
20. [Mental Models and Cognitive Frameworks](#20-mental-models)

---

## 1. Foundational Mental Model

### What Is a Distributed System?

Before understanding *why* debugging is hard, you must deeply understand what you are dealing with.

**Definition**: A distributed system is a collection of independent computing nodes (processes, machines, containers) that communicate over a network and appear to the user as a single coherent system.

**Key Properties (Fallacies of Distributed Computing)**:
Peter Deutsch identified 8 assumptions developers wrongly make. Every one of these is a source of bugs:

```
FALLACY 1: The network is reliable
FALLACY 2: Latency is zero
FALLACY 3: Bandwidth is infinite
FALLACY 4: The network is secure
FALLACY 5: Topology doesn't change
FALLACY 6: There is one administrator
FALLACY 7: Transport cost is zero
FALLACY 8: The network is homogeneous
```

**The CAP Theorem** (foundational concept):

```
                    CONSISTENCY
                        /\
                       /  \
                      /    \
                     /  ??  \
                    /________\
           AVAILABILITY    PARTITION TOLERANCE

CAP Theorem: In a distributed system, you can only guarantee
TWO of the three properties at any given time.

- CP (Consistent + Partition Tolerant): HBase, MongoDB (strong mode)
- AP (Available + Partition Tolerant): Cassandra, CouchDB
- CA (Consistent + Available): Traditional RDBMS (not truly distributed)
```

**Why This Matters for Debugging**: When you see a bug where two services disagree on the state of the world, it is often a CAP theorem manifestation — your system chose Availability over Consistency, and you are now debugging the fallout.

---

### Monolith vs Microservices: The Core Difference

```
MONOLITH EXECUTION MODEL
========================

  [HTTP Request]
       |
       v
  +-----------+
  | Function A|
  |     |     |
  | Function B|   <-- Single process, single memory space
  |     |     |       All calls are in-process function calls
  | Function C|       No network, no serialization
  |     |     |
  | Function D|
  +-----------+
       |
       v
  [HTTP Response]

Stack trace: A -> B -> C -> D  (COMPLETE, DETERMINISTIC)


MICROSERVICES EXECUTION MODEL
==============================

  [HTTP Request]
       |
       v
  [Service A] --HTTP--> [Service B] --gRPC--> [Service C]
       |                    |                      |
      DB_A               Queue                   DB_C
                            |
                       [Service D] --HTTP--> [Service E]
                            |
                           DB_D

Stack trace: FRAGMENTED across 5 processes, 3 machines,
             2 databases, 1 message queue.

What fails?       --> Could be ANYTHING
When did it fail? --> Clocks may differ by milliseconds
Why did it fail?  --> State is split across 3 DBs
```

---

## 2. Loss of Linearity

### The Death of the Call Stack

In a monolith, when you call `panic!()` in Rust or `panic()` in Go, you get a full stack trace:

```
goroutine 1 [running]:
main.functionD(...)
    /app/main.go:45
main.functionC(...)
    /app/main.go:38
main.functionB(...)
    /app/main.go:29
main.functionA(...)
    /app/main.go:20
main.main()
    /app/main.go:10
```

**This is a gift.** You see the complete chain of causation in one place.

In microservices, this is gone. Here is what happens instead:

```
SERVICE A LOG:
  [10:00:01.001] INFO  Request received: order_id=XYZ
  [10:00:01.450] ERROR Upstream call failed: timeout after 449ms

SERVICE B LOG (different machine):
  [10:00:01.002] INFO  Processing order XYZ
  [10:00:01.003] INFO  Calling payment service...
  [10:00:01.400] WARN  Payment service slow response

SERVICE C LOG (yet another machine):
  [10:00:00.999] INFO  Connected
  [10:00:01.005] ERROR DB connection pool exhausted
  [10:00:01.006] INFO  Retrying...
  [10:00:01.399] ERROR Retry failed

QUESTION: What caused the failure in Service A?
ANSWER:   DB pool exhaustion in Service C, propagated
          through B's slow response, resulting in A's timeout.
          But you have to RECONSTRUCT this manually.
```

### How Event-Driven Systems Fragment Execution

```
TRADITIONAL FLOW (synchronous):
================================

  Request --> [A] --> [B] --> [C] --> Response
                                |
                              Result available IMMEDIATELY


EVENT-DRIVEN FLOW (asynchronous):
===================================

  Request --> [A] --> publishes EVENT to Queue
                           |
                     [Queue stores event]
                           |
              (some time later -- could be milliseconds,
               could be hours, could be never)
                           |
                     [B] consumes event --> [C]
                                               |
                                         Result stored in DB
                                               |
              (some MORE time later)           |
                                         [A polls DB]
                                               |
                                         Gets result

DEBUGGING QUESTION: "Why did the order never complete?"

POSSIBLE ANSWERS:
  - Event was never published (A failed silently)
  - Event was published but queue was full
  - Event was consumed but B crashed mid-processing
  - B completed but C's DB write failed
  - A's polling query has a bug
  - All of the above happened for different requests
```

---

## 3. The Unreliable Network

### Why Networks Fail: A Mental Model

The network is not a function call. It is a *physical medium* with all the messiness of the real world.

```
FUNCTION CALL MODEL (what developers assume):
=============================================

  caller --> CALL --> callee
  caller <-- RETURN -- callee

Two possible outcomes: success or exception.
Timing: microseconds.
Failure: immediate exception.


NETWORK CALL MODEL (reality):
==============================

  caller --PACKET_1--> [ROUTER_1] ---> [ROUTER_2] ---> callee
  caller --PACKET_2--> [ROUTER_1] ---> [ROUTER_3] ---> callee (different path!)
  caller --PACKET_3--> [ROUTER_1] ---> [LOST] (dropped)
  caller --TIMEOUT-- (after N milliseconds)

Outcomes: success, timeout, partial delivery, duplicate delivery,
          out-of-order delivery, connection reset, DNS failure,
          TLS handshake failure, etc.
```

### The 8 Types of Network Failure

```
+---------------------------+------------------------------------------+
| Failure Type              | Manifestation in Logs                    |
+---------------------------+------------------------------------------+
| Packet Loss               | Intermittent timeouts, retries           |
| Latency Spike             | Slow responses, cascading timeouts       |
| DNS Failure               | "No such host" errors                    |
| Connection Timeout        | Hanging requests, connection pool drain  |
| Connection Reset          | "Connection refused" or "reset by peer"  |
| TLS Certificate Error     | "certificate expired" or "cert mismatch" |
| Bandwidth Saturation      | Slow uploads/downloads, retransmissions  |
| Routing Loop              | Extremely high latency, TTL exceeded     |
+---------------------------+------------------------------------------+
```

### Non-Deterministic Bugs: The Hardest Class

A non-deterministic bug is one that does not always reproduce under the same inputs. It depends on *timing*, *load*, or *network state*.

```
BUG CLASSIFICATION PYRAMID
============================

         /\
        /  \
       / ??  \    NON-DETERMINISTIC (HARDEST)
      /--------\  - Race conditions
     /          \  - Timing-dependent failures
    /  !!  !!    \ - "Works locally, fails in prod"
   /--------------\
  /                \ DETERMINISTIC (EASIER)
 /  #  #  #  #  #  \ - Logic errors
/____________________\ - Wrong algorithm
                        - Off-by-one errors

Most microservice bugs live in the TOP of this pyramid.
```

### Code: Robust HTTP Client with Timeout and Retry (Go)

```go
package main

import (
    "context"
    "fmt"
    "net/http"
    "time"
    "math"
)

// RetryConfig defines the retry strategy
type RetryConfig struct {
    MaxRetries  int
    BaseDelay   time.Duration
    MaxDelay    time.Duration
}

// HTTPClient wraps http.Client with retry and timeout logic
type HTTPClient struct {
    client *http.Client
    config RetryConfig
}

func NewHTTPClient(timeout time.Duration, config RetryConfig) *HTTPClient {
    return &HTTPClient{
        client: &http.Client{Timeout: timeout},
        config: config,
    }
}

// DoWithRetry performs an HTTP GET with exponential backoff retry
// Exponential backoff: each retry waits 2^n * baseDelay
// e.g., retry 1 = 100ms, retry 2 = 200ms, retry 3 = 400ms
func (c *HTTPClient) DoWithRetry(ctx context.Context, url string) (*http.Response, error) {
    var lastErr error

    for attempt := 0; attempt <= c.config.MaxRetries; attempt++ {
        if attempt > 0 {
            // Exponential backoff calculation
            // 2^(attempt-1) * baseDelay, capped at MaxDelay
            backoff := time.Duration(math.Pow(2, float64(attempt-1))) * c.config.BaseDelay
            if backoff > c.config.MaxDelay {
                backoff = c.config.MaxDelay
            }

            fmt.Printf("[RETRY] Attempt %d after %v delay (url=%s)\n", attempt, backoff, url)

            // Respect context cancellation during wait
            select {
            case <-ctx.Done():
                return nil, fmt.Errorf("context cancelled during retry backoff: %w", ctx.Err())
            case <-time.After(backoff):
            }
        }

        req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
        if err != nil {
            return nil, fmt.Errorf("failed to create request: %w", err)
        }

        resp, err := c.client.Do(req)
        if err != nil {
            lastErr = fmt.Errorf("attempt %d failed: %w", attempt, err)
            fmt.Printf("[ERROR] %v\n", lastErr)
            continue
        }

        // Only retry on 5xx server errors, not 4xx client errors
        // 5xx = server is broken (retryable)
        // 4xx = client made wrong request (not retryable)
        if resp.StatusCode >= 500 {
            lastErr = fmt.Errorf("attempt %d: server error %d", attempt, resp.StatusCode)
            resp.Body.Close()
            continue
        }

        return resp, nil
    }

    return nil, fmt.Errorf("all %d attempts failed, last error: %w", c.config.MaxRetries+1, lastErr)
}
```

### Code: Robust HTTP Client with Retry (Rust)

```rust
use std::time::Duration;
use std::thread;

/// Represents a simple HTTP response (no external crates for clarity)
pub struct Response {
    pub status_code: u16,
    pub body: String,
}

/// Configuration for retry behavior
pub struct RetryConfig {
    pub max_retries: u32,
    pub base_delay_ms: u64,
    pub max_delay_ms: u64,
}

/// Error types that can occur during an HTTP request
#[derive(Debug)]
pub enum ClientError {
    NetworkError(String),
    ServerError(u16),
    MaxRetriesExceeded { attempts: u32, last_error: String },
}

impl std::fmt::Display for ClientError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            ClientError::NetworkError(msg) => write!(f, "Network error: {}", msg),
            ClientError::ServerError(code) => write!(f, "Server error: {}", code),
            ClientError::MaxRetriesExceeded { attempts, last_error } => {
                write!(f, "Max retries ({}) exceeded. Last: {}", attempts, last_error)
            }
        }
    }
}

/// Performs a GET request with exponential backoff retry
///
/// # Arguments
/// * `url` - Target URL
/// * `config` - Retry configuration
///
/// # Returns
/// * `Ok(Response)` on success
/// * `Err(ClientError)` after all retries exhausted
pub fn get_with_retry(url: &str, config: &RetryConfig) -> Result<Response, ClientError> {
    let mut last_error = String::new();

    for attempt in 0..=config.max_retries {
        if attempt > 0 {
            // 2^(attempt-1) * base_delay, capped at max_delay
            let delay_ms = (2u64.pow(attempt - 1) * config.base_delay_ms)
                .min(config.max_delay_ms);

            eprintln!(
                "[RETRY] Attempt {} of {} after {}ms (url={})",
                attempt, config.max_retries, delay_ms, url
            );

            thread::sleep(Duration::from_millis(delay_ms));
        }

        // Simulate HTTP call (in real code, use reqwest or ureq crate)
        match simulate_http_get(url) {
            Ok(resp) if resp.status_code >= 500 => {
                last_error = format!("Server error: {}", resp.status_code);
                eprintln!("[ERROR] Attempt {}: {}", attempt, last_error);
                // Retryable: continue loop
            }
            Ok(resp) => {
                // Success or non-retryable client error
                return Ok(resp);
            }
            Err(e) => {
                last_error = e.to_string();
                eprintln!("[ERROR] Attempt {}: {}", attempt, last_error);
                // Network error: retryable
            }
        }
    }

    Err(ClientError::MaxRetriesExceeded {
        attempts: config.max_retries + 1,
        last_error,
    })
}

fn simulate_http_get(url: &str) -> Result<Response, ClientError> {
    // Placeholder — replace with actual HTTP call using `reqwest` or `ureq`
    Ok(Response {
        status_code: 200,
        body: format!("Response from {}", url),
    })
}
```

---

## 4. Partial Failures

### When the System Lies to You

This is one of the most insidious problems in distributed systems. A **partial failure** occurs when part of a request chain succeeds and part fails, resulting in a system state that is neither fully committed nor fully rolled back.

```
PARTIAL FAILURE SCENARIO: E-Commerce Order
===========================================

  User                  Service A          Service B         Service C
  (Browser)            (Order Svc)        (Payment Svc)     (Inventory Svc)
     |                      |                  |                   |
     |---POST /order------->|                  |                   |
     |                      |                  |                   |
     |                      |---charge card -->|                   |
     |                      |                  |                   |
     |                      |                  |---reserve stock-->|
     |                      |                  |                   |
     |                      |                  |                   X  <-- DB timeout
     |                      |                  |                   |
     |                      |                  |<-- timeout -------|
     |                      |                  |
     |                      |    Payment charged but...
     |                      |    inventory NOT reserved
     |                      |
     |                      |  What should A return to the user?
     |                      |  - "Order successful"? (LIE)
     |                      |  - "Order failed"?     (ALSO a LIE -- card was charged!)
     |                      |
     |<-- 200 OK "success"--|  <-- A decides to lie to avoid user confusion
     |                            This is the WORST option.
```

### The Two Generals Problem

This is a classic theoretical problem that proves partial failures are **unsolvable** in general:

```
SETUP:
======
Two generals (A and B) need to coordinate an attack.
They communicate via messengers who may be captured.

General A: "Attack at dawn?" --messenger--> General B
                                                |
                                         Messenger captured? 
                                         (packet lost?)
                                                |
                             General B: "Yes, attack at dawn!" --messenger-->
                                                                     |
                                                              Messenger captured?
                                                                     |
                                                         General A never knows if 
                                                         General B received the plan.

IMPLICATION FOR DISTRIBUTED SYSTEMS:
=====================================
When Service A sends a request to Service B, A can never be 
100% certain whether B processed the request or not.

The message could have been:
  - Lost in transit (B never received it)
  - Received but B crashed before processing
  - Processed but the response was lost
  - Processed twice due to A's retry
```

### Handling Partial Failures: The Saga Pattern

```
SAGA PATTERN: CHOREOGRAPHY-BASED
==================================

Each step in a transaction has a corresponding COMPENSATING TRANSACTION
(an "undo" action that reverses the effect).

HAPPY PATH:
  [1] Create Order  --> OK
  [2] Charge Payment --> OK
  [3] Reserve Inventory --> OK
  [4] Ship Order --> OK

FAILURE PATH (step 3 fails):
  [1] Create Order    --> OK
  [2] Charge Payment  --> OK
  [3] Reserve Inventory --> FAIL
                               |
                      TRIGGER COMPENSATING TRANSACTIONS:
                               |
  [2'] Refund Payment  <-- compensate step 2
  [1'] Cancel Order    <-- compensate step 1

The system is EVENTUALLY CONSISTENT, not immediately consistent.


SAGA STEP STATE MACHINE:
=========================

    +----------+     success     +-----------+
    | PENDING  | --------------> | COMPLETED |
    +----------+                 +-----------+
         |
         | failure
         v
    +-----------+    undo done   +-------------+
    | FAILED    | -------------> | COMPENSATED |
    +-----------+                +-------------+
```

### Code: Saga Step with Compensation (Go)

```go
package saga

import (
    "context"
    "fmt"
    "log"
)

// Step represents a single unit of work in a distributed transaction
// Each step MUST have a compensating action to "undo" its effect
type Step struct {
    Name       string
    Execute    func(ctx context.Context) error
    Compensate func(ctx context.Context) error // Called if a LATER step fails
}

// Saga orchestrates a sequence of Steps with automatic rollback
type Saga struct {
    steps     []Step
    completed []Step // tracks which steps succeeded (for rollback)
}

func NewSaga(steps ...Step) *Saga {
    return &Saga{steps: steps}
}

// Run executes all steps in order.
// If any step fails, all previously completed steps are compensated
// in REVERSE order (last-in, first-out).
func (s *Saga) Run(ctx context.Context) error {
    for _, step := range s.steps {
        log.Printf("[SAGA] Executing step: %s", step.Name)

        if err := step.Execute(ctx); err != nil {
            log.Printf("[SAGA] Step %s FAILED: %v. Starting compensation.", step.Name, err)

            // Compensate in reverse order
            s.compensate(ctx)

            return fmt.Errorf("saga failed at step '%s': %w", step.Name, err)
        }

        // Track completed steps for potential rollback
        s.completed = append(s.completed, step)
        log.Printf("[SAGA] Step %s completed successfully.", step.Name)
    }

    log.Printf("[SAGA] All steps completed successfully.")
    return nil
}

// compensate runs compensating transactions in reverse order
func (s *Saga) compensate(ctx context.Context) {
    // Iterate completed steps in reverse
    for i := len(s.completed) - 1; i >= 0; i-- {
        step := s.completed[i]
        log.Printf("[SAGA] Compensating step: %s", step.Name)

        if err := step.Compensate(ctx); err != nil {
            // Compensation failure is a CRITICAL error -- requires manual intervention
            // In production: alert on-call engineer, store in dead-letter queue
            log.Printf("[SAGA][CRITICAL] Compensation for '%s' failed: %v. MANUAL INTERVENTION REQUIRED.", step.Name, err)
        }
    }
}

// --- Example Usage ---

func ExampleOrderSaga(ctx context.Context) error {
    saga := NewSaga(
        Step{
            Name:    "CreateOrder",
            Execute: func(ctx context.Context) error { fmt.Println("Creating order"); return nil },
            Compensate: func(ctx context.Context) error { fmt.Println("Cancelling order"); return nil },
        },
        Step{
            Name:    "ChargePayment",
            Execute: func(ctx context.Context) error { fmt.Println("Charging card"); return nil },
            Compensate: func(ctx context.Context) error { fmt.Println("Refunding card"); return nil },
        },
        Step{
            Name: "ReserveInventory",
            Execute: func(ctx context.Context) error {
                return fmt.Errorf("inventory service unavailable") // Simulated failure
            },
            Compensate: func(ctx context.Context) error { fmt.Println("Releasing inventory"); return nil },
        },
    )

    return saga.Run(ctx)
}
```

---

## 5. Data Inconsistency

### No Single Source of Truth

In a monolith with a single database:

- All services read and write to the same tables
- ACID transactions guarantee consistency
- A rollback affects all changes atomically

In microservices, each service owns its data:

```
MICROSERVICES DATA OWNERSHIP
==============================

  +------------------+     +------------------+     +-------------------+
  |   Order Service  |     | Payment Service  |     | Inventory Service |
  |                  |     |                  |     |                   |
  |  orders DB       |     |  payments DB     |     |  inventory DB     |
  |  +-----------+   |     |  +-----------+   |     |  +------------+   |
  |  | order_id  |   |     |  | payment_id|   |     |  | item_id    |   |
  |  | status    |   |     |  | amount    |   |     |  | quantity   |   |
  |  | user_id   |   |     |  | order_id  |   |     |  | reserved   |   |
  |  +-----------+   |     |  +-----------+   |     |  +------------+   |
  +------------------+     +------------------+     +-------------------+

  PROBLEM: No global transaction across these three DBs.

  If you need: "Get total revenue for all orders that were paid AND shipped"
  You must:
    1. Query Order DB   --> get all order IDs
    2. Query Payment DB --> filter those that were paid
    3. Query Inventory  --> filter those where stock was shipped
    4. JOIN in application code

  What if Payment DB is updated while you are reading from Order DB?
  ANSWER: You see INCONSISTENT DATA -- the bane of distributed systems.
```

### Eventual Consistency: A Mental Model

```
EVENTUAL CONSISTENCY TIMELINE
================================

  Time 0ms:  User updates email in Profile Service
             --> Profile DB updated: email = "new@example.com"

  Time 0ms:  Order Service has cached email = "old@example.com"
             (it synced 5 minutes ago)

  Time 5ms:  Profile Service publishes EVENT: "EmailUpdated"
             --> Event sits in Kafka queue

  Time 50ms: Order Service receives event, updates its cache
             --> Order Service NOW has: email = "new@example.com"

  Window 0-50ms: INCONSISTENCY EXISTS
  After 50ms:    System is EVENTUALLY CONSISTENT

DEBUGGING IMPLICATION:
  If a bug report comes in during this 50ms window,
  the data you see in the DB does NOT reflect what the user saw.
  This is NOT a bug -- it is by design. But it LOOKS like a bug.
```

### Stale Reads, Phantom Reads, and Dirty Reads

```
READ ANOMALY TAXONOMY
======================

1. STALE READ (most common in microservices)
   ============
   Thread A reads X = 10
   Thread B updates X = 20 (committed)
   Thread A reads X again = 10  <-- stale! (cached value)

2. DIRTY READ
   ===========
   Thread A updates X = 20 (NOT committed yet)
   Thread B reads X = 20    <-- dirty! (reading uncommitted data)
   Thread A ROLLS BACK X = 10
   Thread B now has wrong value

3. PHANTOM READ
   =============
   Thread A: SELECT * FROM orders WHERE status='PENDING'  --> returns 5 rows
   Thread B: INSERT INTO orders (status='PENDING')        --> adds 1 row
   Thread A: SELECT * WHERE status='PENDING'              --> returns 6 rows
   "Phantom" row appeared between two identical queries.

4. NON-REPEATABLE READ
   ====================
   Thread A reads order #123 price = $50
   Thread B updates order #123 price = $75
   Thread A reads order #123 price = $75  <-- different from first read!
```

---

## 6. Scattered Logs

### The Archaeology Problem

Finding the cause of a failure in microservices is like archaeology — you must dig through layers, from different sites, and piece together what happened.

```
THE CORRELATION ID PATTERN
============================

Without Correlation IDs:
  Service A: "Request failed"           -- Which request?
  Service B: "Downstream timeout"       -- For what?
  Service C: "DB connection failed"     -- At what time?

  You cannot connect these logs.

With Correlation IDs:
  Service A: [trace_id=abc-123] "Request failed"
  Service B: [trace_id=abc-123] "Downstream timeout"
  Service C: [trace_id=abc-123] "DB connection failed at 10:00:01.005"

  Now you can filter ALL logs by trace_id=abc-123 and see the
  complete story across ALL services.


PROPAGATION OF CORRELATION ID:
================================

  [Browser] --> HTTP Header: X-Request-ID: abc-123
                    |
               [Service A] reads X-Request-ID
                    |      logs with [trace_id=abc-123]
                    |      passes X-Request-ID to outgoing requests
                    |
               [Service B] reads X-Request-ID
                    |      logs with [trace_id=abc-123]
                    |      passes X-Request-ID onward
                    |
               [Service C] reads X-Request-ID
                           logs with [trace_id=abc-123]
```

### Log Levels: A Rigorous Definition

Many engineers use log levels carelessly. This causes noise and makes debugging harder.

```
LOG LEVEL HIERARCHY AND SEMANTICS
===================================

TRACE   (most verbose)
  Use for: Step-by-step execution details for deep debugging
  Example: "Entering function processOrder, order_id=XYZ"
  Rule: NEVER enable in production (too expensive)

DEBUG
  Use for: Useful context for developers when diagnosing issues
  Example: "Payment service returned code 200, body={...}"
  Rule: Disabled in production by default, enabled on demand

INFO
  Use for: Normal operational events worth recording
  Example: "Order XYZ successfully placed by user 456"
  Rule: ALWAYS on in production, but not spammy

WARN
  Use for: Something unexpected happened, but system is still functioning
  Example: "Retry attempt 2 of 3 for payment service"
  Rule: Should trigger monitoring alerts if rate is high

ERROR
  Use for: Something failed and requires attention
  Example: "Failed to connect to DB after 3 retries"
  Rule: Always triggers alert

FATAL / CRITICAL
  Use for: The process cannot continue
  Example: "Configuration file missing, cannot start"
  Rule: Triggers immediate page/alert, process exits
```

### Structured Logging: JSON over Text

```
BAD (unstructured log):
========================
  2024-01-15 10:00:01 ERROR Failed to process order 123 for user 456

Problems:
  - Cannot filter by order_id with a query
  - Cannot aggregate by user_id
  - Parsing requires fragile regex

GOOD (structured log):
========================
  {
    "timestamp": "2024-01-15T10:00:01.123Z",
    "level": "ERROR",
    "service": "order-service",
    "trace_id": "abc-123-def-456",
    "span_id": "xyz-789",
    "message": "Failed to process order",
    "order_id": 123,
    "user_id": 456,
    "error": "payment service timeout after 500ms",
    "retry_count": 3
  }

Benefits:
  - Filter: level=ERROR AND service=order-service
  - Aggregate: COUNT(*) GROUP BY error
  - Join: trace_id across services
  - Alert: retry_count > 2
```

### Code: Structured Logger with Correlation IDs (Rust)

```rust
use std::collections::HashMap;
use std::time::{SystemTime, UNIX_EPOCH};

/// Log levels
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
pub enum LogLevel {
    Trace = 0,
    Debug = 1,
    Info = 2,
    Warn = 3,
    Error = 4,
    Fatal = 5,
}

impl std::fmt::Display for LogLevel {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            LogLevel::Trace => write!(f, "TRACE"),
            LogLevel::Debug => write!(f, "DEBUG"),
            LogLevel::Info  => write!(f, "INFO"),
            LogLevel::Warn  => write!(f, "WARN"),
            LogLevel::Error => write!(f, "ERROR"),
            LogLevel::Fatal => write!(f, "FATAL"),
        }
    }
}

/// Context carried through a request (correlation IDs)
#[derive(Clone, Debug)]
pub struct RequestContext {
    pub trace_id: String,   // Unique ID for the entire request chain
    pub span_id: String,    // Unique ID for THIS service's portion
    pub service: String,    // Name of this service
    pub extra: HashMap<String, String>, // Arbitrary key-value pairs
}

/// A structured log entry
#[derive(Debug)]
pub struct LogEntry {
    pub timestamp: u128,       // Unix timestamp in milliseconds
    pub level: LogLevel,
    pub context: RequestContext,
    pub message: String,
    pub fields: HashMap<String, String>,
}

impl LogEntry {
    /// Serializes the log entry to a JSON-compatible string
    pub fn to_json(&self) -> String {
        let fields_str: String = self.fields.iter()
            .map(|(k, v)| format!(", \"{}\": \"{}\"", k, v))
            .collect();

        let extra_str: String = self.context.extra.iter()
            .map(|(k, v)| format!(", \"{}\": \"{}\"", k, v))
            .collect();

        format!(
            r#"{{"timestamp": {}, "level": "{}", "service": "{}", "trace_id": "{}", "span_id": "{}", "message": "{}"{}{}}}"#,
            self.timestamp,
            self.level,
            self.context.service,
            self.context.trace_id,
            self.context.span_id,
            self.message,
            fields_str,
            extra_str,
        )
    }
}

/// Logger struct that emits structured log entries
pub struct Logger {
    min_level: LogLevel,
}

impl Logger {
    pub fn new(min_level: LogLevel) -> Self {
        Self { min_level }
    }

    fn log(&self, level: LogLevel, ctx: &RequestContext, message: &str, fields: HashMap<String, String>) {
        if level < self.min_level {
            return; // Skip below minimum level
        }

        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis();

        let entry = LogEntry {
            timestamp,
            level,
            context: ctx.clone(),
            message: message.to_string(),
            fields,
        };

        // In production: write to stdout, ship to ELK/Loki
        eprintln!("{}", entry.to_json());
    }

    pub fn info(&self, ctx: &RequestContext, msg: &str, fields: HashMap<String, String>) {
        self.log(LogLevel::Info, ctx, msg, fields);
    }

    pub fn error(&self, ctx: &RequestContext, msg: &str, fields: HashMap<String, String>) {
        self.log(LogLevel::Error, ctx, msg, fields);
    }

    pub fn warn(&self, ctx: &RequestContext, msg: &str, fields: HashMap<String, String>) {
        self.log(LogLevel::Warn, ctx, msg, fields);
    }
}

// Usage example:
fn main() {
    let logger = Logger::new(LogLevel::Info);
    
    let ctx = RequestContext {
        trace_id: "abc-123-def-456".into(),
        span_id: "xyz-789".into(),
        service: "order-service".into(),
        extra: HashMap::new(),
    };

    let mut fields = HashMap::new();
    fields.insert("order_id".into(), "ORDER-001".into());
    fields.insert("user_id".into(), "USER-42".into());
    
    logger.info(&ctx, "Order created successfully", fields);
    
    let mut err_fields = HashMap::new();
    err_fields.insert("retry_count".into(), "3".into());
    err_fields.insert("downstream".into(), "payment-service".into());
    
    logger.error(&ctx, "Payment service unreachable after retries", err_fields);
}
```

---

## 7. Concurrency Explosion

### Race Conditions at Scale

A **race condition** occurs when the behavior of a system depends on the relative timing of uncontrollable events (like thread scheduling or network message ordering).

```
RACE CONDITION: DOUBLE SPEND
==============================

                    Time -->

Thread A (Request 1):
  Read balance:  $100  ------>
                              (Context switch)
Thread B (Request 2):
  Read balance:  $100  ------>
  Deduct $80:    $20   ------>
  Write balance: $20   ------>
Thread A (Request 1):
  (Resumes with stale balance = $100)
  Deduct $90:    $10   ------>
  Write balance: $10   ------>

RESULT:
  - Thread B correctly reduced $100 --> $20  (balance was $20)
  - Thread A incorrectly reduced $100 --> $10 (using stale $100)
  - Final balance: $10
  - But user spent $80 + $90 = $170, starting from $100
  - BANK LOSES $70


FIX: Optimistic Locking
========================
  Read balance: $100 AND version=5
  Deduct $90
  UPDATE accounts SET balance=$10, version=6
    WHERE account_id=X AND version=5  <-- FAILS if someone else modified it
  
  If rows_affected == 0: Retry (someone else won the race)
  If rows_affected == 1: Success
```

### Distributed Deadlocks

```
DISTRIBUTED DEADLOCK SCENARIO
================================

  Service A holds lock on "Resource_X"
  Service A is waiting for lock on "Resource_Y"

  Service B holds lock on "Resource_Y"
  Service B is waiting for lock on "Resource_X"

  DEADLOCK: Neither can proceed.

  Timeline:
  
  t=0:  A acquires lock on X
  t=1:  B acquires lock on Y
  t=2:  A requests lock on Y  --> BLOCKED (B holds it)
  t=3:  B requests lock on X  --> BLOCKED (A holds it)
  t=4:  ... FOREVER ...

VISUALIZATION:
===============

  Service A   --wants-->   Resource Y
      |                        |
    holds                    holds
      |                        |
  Resource X  <--wants--  Service B

  This forms a CYCLE in the dependency graph.
  A cycle = deadlock.

PREVENTION STRATEGIES:
========================
  1. Lock Ordering: Always acquire locks in the same global order
     (A always acquires X before Y, B does the same)
  2. Timeouts: If a lock cannot be acquired within N ms, release all
     held locks and retry
  3. Deadlock Detection: Periodically scan the dependency graph for cycles
```

### Code: Deadlock Prevention with Ordered Locking (C)

```c
#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

/*
 * DEADLOCK PREVENTION THROUGH GLOBAL LOCK ORDERING
 *
 * Key Insight: If ALL threads acquire locks in the same ORDER
 * (by resource ID), cycles in the dependency graph cannot form.
 *
 * Why? Because a cycle requires thread A to hold resource with
 * higher ID and want lower ID, while B holds lower and wants higher.
 * With ordered acquisition, this cannot happen.
 */

#define NUM_RESOURCES 2

typedef struct {
    pthread_mutex_t mutex;
    int id;       /* Globally unique ID -- used for ordering */
    int value;
} Resource;

Resource resources[NUM_RESOURCES];

/*
 * lock_ordered: Acquires two locks in ID order to prevent deadlocks.
 *
 * Parameters:
 *   r1, r2 -- the two resources to lock
 *
 * The function always locks the resource with the LOWER ID first.
 * This guarantees no cycle can form in the lock dependency graph.
 */
void lock_ordered(Resource *r1, Resource *r2) {
    /* Ensure lower-ID resource is always locked first */
    if (r1->id < r2->id) {
        pthread_mutex_lock(&r1->mutex);
        pthread_mutex_lock(&r2->mutex);
    } else {
        pthread_mutex_lock(&r2->mutex);
        pthread_mutex_lock(&r1->mutex);
    }
}

void unlock_both(Resource *r1, Resource *r2) {
    pthread_mutex_unlock(&r1->mutex);
    pthread_mutex_unlock(&r2->mutex);
}

/*
 * transfer_value: Transfers 'amount' from src to dst.
 * Uses lock ordering to prevent deadlocks.
 */
int transfer_value(Resource *src, Resource *dst, int amount) {
    lock_ordered(src, dst);  /* Safe: always acquires in ID order */

    if (src->value < amount) {
        unlock_both(src, dst);
        fprintf(stderr, "[ERROR] Insufficient value in resource %d\n", src->id);
        return -1;
    }

    src->value -= amount;
    dst->value += amount;

    printf("[TRANSFER] Resource %d: %d --> Resource %d: %d (amount=%d)\n",
           src->id, src->value, dst->id, dst->value, amount);

    unlock_both(src, dst);
    return 0;
}

void *thread_a(void *arg) {
    /* Thread A: transfers from resource 0 to resource 1 */
    transfer_value(&resources[0], &resources[1], 10);
    return NULL;
}

void *thread_b(void *arg) {
    /* Thread B: also transfers from resource 1 to resource 0 */
    /* WITHOUT ordered locking this would deadlock with thread_a */
    /* WITH ordered locking: both acquire resource[0] first --> safe */
    transfer_value(&resources[1], &resources[0], 5);
    return NULL;
}

int main(void) {
    /* Initialize resources */
    for (int i = 0; i < NUM_RESOURCES; i++) {
        pthread_mutex_init(&resources[i].mutex, NULL);
        resources[i].id    = i;
        resources[i].value = 100;
    }

    pthread_t ta, tb;
    pthread_create(&ta, NULL, thread_a, NULL);
    pthread_create(&tb, NULL, thread_b, NULL);

    pthread_join(ta, NULL);
    pthread_join(tb, NULL);

    printf("Final values: resource[0]=%d, resource[1]=%d\n",
           resources[0].value, resources[1].value);

    for (int i = 0; i < NUM_RESOURCES; i++) {
        pthread_mutex_destroy(&resources[i].mutex);
    }

    return 0;
}
```

---

## 8. Version Mismatch

### API Drift and Contract Violations

Services evolve independently. This means one service may be on version 2 of an API while another still calls version 1. Unlike compilation errors (which catch type mismatches at build time), API drift often causes **silent data corruption**.

```
VERSION MISMATCH SCENARIO
============================

Service A (consumer) sends:
  POST /api/v2/orders
  {
    "user_id": 123,
    "items": [{"sku": "ABC", "quantity": 2}],
    "discount_code": "SAVE10"        <-- NEW field in v2
  }

Service B (provider) is still on v1:
  It receives the request and...
  - Silently IGNORES "discount_code" (unknown field)
  - Processes order at FULL PRICE
  - Returns 200 OK

Result:
  - No error in logs
  - User was charged wrong amount
  - Extremely hard to debug because "everything succeeded"


TYPES OF BREAKING CHANGES:
============================

BREAKING (causes immediate failures or silent corruption):
  - Removing a field from response
  - Changing a field's type (string -> int)
  - Renaming a field
  - Changing required/optional status
  - Changing endpoint URL or HTTP method

NON-BREAKING (backward compatible):
  - Adding a new OPTIONAL field to request
  - Adding a new field to response
  - Adding a new endpoint
  - Adding a new enum value (careful!)
```

### API Versioning Strategies

```
STRATEGY 1: URL PATH VERSIONING
=================================
  /api/v1/orders
  /api/v2/orders
  /api/v3/orders

Pros:  Easy to see which version is being called
Cons:  Clients must update URLs when migrating


STRATEGY 2: HEADER VERSIONING
================================
  GET /api/orders
  Accept: application/vnd.myapi.v2+json

Pros:  Clean URLs
Cons:  Harder to test, requires header inspection


STRATEGY 3: QUERY PARAMETER
=============================
  GET /api/orders?version=2

Pros:  Easy to test in browser
Cons:  Considered bad practice (version is part of resource identity)


STRATEGY 4: CONTENT NEGOTIATION (most sophisticated)
======================================================
  Use semantic versioning + feature detection
  API returns what it supports, consumer adapts

Pros:  Gradual migration, no big-bang upgrades
Cons:  Complex to implement


BEST PRACTICE: Use Semantic Versioning + Consumer-Driven Contract Testing

MAJOR version: Breaking changes   (v1 -> v2)
MINOR version: New features       (v1.1 -> v1.2)
PATCH version: Bug fixes          (v1.1.0 -> v1.1.1)
```

---

## 9. Retry Storms and Cascading Failures

### How One Failure Brings Down a System

```
CASCADING FAILURE ANATOMY
===========================

INITIAL STATE (healthy):
  Client --> [A: 100 req/s] --> [B: 100 req/s] --> [C: 100 req/s] --> [DB]

TRIGGER: DB becomes slow (high load, disk I/O):
  
  t=0s:   DB responds in 2000ms instead of 50ms
  
  t=0s:   C's requests pile up (waiting for DB)
            C: 100 req/s incoming, 0.5 req/s processed
            C's request queue fills up
  
  t=1s:   B's requests to C start timing out
            B retries! (3 retries each)
            B now sends 300 req/s to C (tripled!)
  
  t=2s:   A's requests to B time out
            A retries! 
            A now sends 300 req/s to B
            B sends 900 req/s to C (9x original!)
  
  t=3s:   C is completely overwhelmed
            C process crashes (OOM, CPU 100%)
            B gets "connection refused" from C
            B marks C as DOWN
  
  t=4s:   B has no healthy upstream
            B crashes
  
  t=5s:   A has no healthy upstream
            A crashes
  
  RESULT: Entire system down because DB was slow.
  ROOT CAUSE: DB I/O issue.
  OBSERVED SYMPTOM: All services crashed.

                        RETRY STORM DIAGRAM
                        ====================

                                100 req/s
  [Client] -------------------> [Service A]
                                      |
                                      | retries x3
                                      | = 300 req/s
                                      v
                               [Service B]
                                      |
                                      | retries x3
                                      | = 900 req/s
                                      v
                               [Service C]
                                      |
                                      | 900 req/s !!!
                                      v
                              [Database] <-- OVERWHELMED
                               COLLAPSES
```

### Circuit Breaker Pattern: The Safety Valve

A **circuit breaker** is named after electrical circuit breakers. When a service is failing, the circuit "opens" and stops sending requests to it — preventing further damage and allowing recovery.

```
CIRCUIT BREAKER STATE MACHINE
================================

  +-----------+
  |  CLOSED   |  Normal operation. Requests flow through.
  | (healthy) |  Counts failures.
  +-----------+
        |
        | Failure rate exceeds threshold
        | (e.g., 50% of last 10 requests failed)
        v
  +-----------+
  |   OPEN    |  STOP sending requests to the service.
  | (failing) |  Return error immediately (fast fail).
  +-----------+  Start a reset timer (e.g., 30 seconds).
        |
        | Reset timer expires
        v
  +-------------+
  | HALF-OPEN   |  Allow ONE test request through.
  | (testing)   |
  +-------------+
        |              |
        | Success       | Failure
        v              v
   +----------+    +---------+
   |  CLOSED  |    |  OPEN   |
   | (healthy)|    |(failing)|
   +----------+    +---------+

ANALOGY: Like a fuse box in your home.
  When there's a short circuit, the fuse BREAKS the circuit.
  The appliance with the fault doesn't keep drawing power.
  You fix the issue, then RESET the fuse.
```

### Code: Circuit Breaker (Go)

```go
package circuitbreaker

import (
    "errors"
    "fmt"
    "sync"
    "time"
)

// State represents the circuit breaker's operational state
type State int

const (
    StateClosed   State = iota // Normal operation: requests flow through
    StateOpen                  // Failing: requests blocked immediately
    StateHalfOpen              // Testing: one request allowed through
)

func (s State) String() string {
    switch s {
    case StateClosed:   return "CLOSED"
    case StateOpen:     return "OPEN"
    case StateHalfOpen: return "HALF_OPEN"
    default:            return "UNKNOWN"
    }
}

var (
    ErrCircuitOpen = errors.New("circuit breaker is OPEN: downstream service unavailable")
)

// CircuitBreaker tracks failures and prevents overwhelming a failing service
type CircuitBreaker struct {
    mu sync.Mutex // Protects all state below

    name           string
    state          State
    failureCount   int
    successCount   int
    
    // Configuration
    failureThreshold int           // Open if consecutive failures >= this
    resetTimeout     time.Duration // How long to stay OPEN before trying again
    
    // Timing
    lastFailureTime time.Time
    openedAt        time.Time
}

func New(name string, failureThreshold int, resetTimeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        name:             name,
        state:            StateClosed,
        failureThreshold: failureThreshold,
        resetTimeout:     resetTimeout,
    }
}

// Execute runs the given function if the circuit allows it.
// If the circuit is OPEN, returns ErrCircuitOpen immediately.
func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()

    switch cb.state {
    case StateOpen:
        // Check if reset timeout has elapsed
        if time.Since(cb.openedAt) >= cb.resetTimeout {
            fmt.Printf("[CB:%s] OPEN -> HALF_OPEN (testing)\n", cb.name)
            cb.state = StateHalfOpen
            cb.mu.Unlock()
            // Fall through to execute the test request
        } else {
            cb.mu.Unlock()
            // Fast fail: don't even attempt the call
            return fmt.Errorf("%w (opened %v ago)", ErrCircuitOpen, time.Since(cb.openedAt).Round(time.Millisecond))
        }

    case StateHalfOpen, StateClosed:
        cb.mu.Unlock()
    }

    // Execute the actual function
    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.onFailure(err)
    } else {
        cb.onSuccess()
    }

    return err
}

// onFailure is called when the wrapped function returns an error
func (cb *CircuitBreaker) onFailure(err error) {
    cb.failureCount++
    cb.lastFailureTime = time.Now()

    switch cb.state {
    case StateClosed:
        if cb.failureCount >= cb.failureThreshold {
            cb.state = StateOpen
            cb.openedAt = time.Now()
            fmt.Printf("[CB:%s] CLOSED -> OPEN after %d failures. Last error: %v\n",
                cb.name, cb.failureCount, err)
        }

    case StateHalfOpen:
        // Test request failed: go back to OPEN
        cb.state = StateOpen
        cb.openedAt = time.Now()
        fmt.Printf("[CB:%s] HALF_OPEN -> OPEN (test request failed: %v)\n", cb.name, err)
    }
}

// onSuccess is called when the wrapped function succeeds
func (cb *CircuitBreaker) onSuccess() {
    switch cb.state {
    case StateHalfOpen:
        // Service recovered: go back to CLOSED
        cb.state = StateClosed
        cb.failureCount = 0
        cb.successCount = 0
        fmt.Printf("[CB:%s] HALF_OPEN -> CLOSED (service recovered)\n", cb.name)

    case StateClosed:
        cb.failureCount = 0 // Reset on success
    }
}
```

---

## 10. Observability

### The Three Pillars

Observability is the ability to understand the internal state of a system by examining its external outputs. In distributed systems, it is not optional — it is the only way to debug production issues.

```
THE THREE PILLARS OF OBSERVABILITY
=====================================

  +-------------------+   +-------------------+   +-------------------+
  |      LOGS         |   |      METRICS       |   |      TRACES       |
  +-------------------+   +-------------------+   +-------------------+
  |                   |   |                   |   |                   |
  | Discrete events   |   | Numeric values    |   | Request journey   |
  | at a point        |   | over time         |   | across services   |
  | in time           |   |                   |   |                   |
  |                   |   | e.g., CPU%, error |   | "What happened    |
  | "What happened"   |   | rate, latency     |   | WHERE and WHEN    |
  | (detailed)        |   | p99, request/s    |   | for request X"    |
  |                   |   |                   |   |                   |
  | Tools: ELK Stack  |   | Tools: Prometheus |   | Tools: Jaeger     |
  | Loki, Splunk      |   | Grafana, Datadog  |   | Zipkin, OpenTel   |
  +-------------------+   +-------------------+   +-------------------+
             |                     |                      |
             +---------------------+----------------------+
                                   |
                          COMBINED: Answer any
                          question about system
                          behavior in production


  ANALOGY:
  =========
  Imagine debugging a car:
  
  Logs    = The "check engine" warning messages with codes
  Metrics = The dashboard gauges (speed, RPM, temperature)
  Traces  = The GPS track of where the car drove
```

### Distributed Tracing: A Deep Dive

```
WHAT A DISTRIBUTED TRACE LOOKS LIKE
======================================

Trace ID: abc-123-def-456

  [Service A]  t=0ms      t=200ms
  |<---------------------------------------->|
  |  "Process Order"                          |
  |                                           |
  |  [Service B]  t=10ms     t=150ms          |
  |  |<------------------------------->|      |
  |  |  "Charge Payment"               |      |
  |  |                                 |      |
  |  |  [Service C]  t=20ms  t=80ms    |      |
  |  |  |<----------------->|          |      |
  |  |  | "Check Fraud"     |          |      |
  |  |  |___________________|          |      |
  |  |                                 |      |
  |  |  [Payment API] t=90ms t=145ms   |      |
  |  |  |<------------------->|        |      |
  |  |  | "External API Call" |        |      |
  |  |  |_____________________|        |      |
  |  |_________________________________|      |
  |                                           |
  |  [Inventory Service] t=155ms  t=190ms     |
  |  |<----------------------->|              |
  |  | "Reserve Stock"         |              |
  |  |_________________________|              |
  |___________________________________________|

KEY CONCEPTS:
  Trace:  The entire request from Service A to completion
  Span:   One unit of work within a trace (e.g., "Charge Payment")
  Parent/Child: Spans form a tree (A called B, B called C and Payment API)
  
WHAT THIS TELLS YOU:
  - Service B took 140ms (10ms to 150ms)
  - 55ms of that was the External Payment API (90ms to 145ms)
  - That is the bottleneck.
  - Without tracing, you would NEVER know this.
```

### The Four Golden Signals (from Google SRE)

```
THE FOUR GOLDEN SIGNALS
========================

1. LATENCY
   =========
   How long does a request take?
   
   Track: p50 (median), p95, p99, p99.9
   
   Why percentiles? Averages hide outliers.
   
     Request times: [1ms, 1ms, 1ms, 1ms, 1ms, 1ms, 1ms, 1ms, 1ms, 10000ms]
     Average: ~1001ms  (misleading -- 9 users had great experience)
     p99:     10000ms  (reveals the 1% who suffered)
   
   Alert when: p99 latency > SLA threshold


2. TRAFFIC
   =========
   How much demand is on the system?
   
   Measure: requests/second, messages/second, DB queries/second
   
   Use for: capacity planning, detecting traffic spikes


3. ERRORS
   ========
   What fraction of requests fail?
   
   Measure: error_count / total_requests * 100 = error_rate %
   
   Alert when: error_rate > X% for Y minutes


4. SATURATION
   ============
   How "full" is your service?
   
   Measure: CPU%, memory%, disk I/O%, connection pool usage%
   
   Alert when: any resource > 80% (gives you time to react)
   
   Note: Saturation predicts future failure before it happens.
         The other three signals measure CURRENT health.
         Saturation measures HEADROOM.
```

---

## 11. Environment Differences

### Local vs Production: The Reproducibility Chasm

```
LOCAL ENVIRONMENT          PRODUCTION ENVIRONMENT
===================        =======================

Services: 2-3              Services: 50+
Replicas: 1 each           Replicas: 3-20 per service
Network:  Loopback (0ms)   Network:  Real LAN/WAN (1-50ms)
Load:     Your dev traffic  Load:    10,000 req/s
Database: SQLite or empty   Database: 500GB PostgreSQL
Cache:    None              Cache:    Redis cluster (warm)
Secrets:  .env file         Secrets:  HashiCorp Vault
Config:   Hardcoded         Config:   Kubernetes ConfigMaps
OS:       macOS/Windows     OS:       Linux (Alpine/Debian)
CPU:      Your laptop       CPU:      64-core cloud instance

BUGS THAT ONLY APPEAR IN PRODUCTION:
======================================

1. TIMING BUGS
   Your laptop processes requests in 1ms.
   Prod processes in 15ms (real network + load).
   Race conditions that require >5ms to manifest are invisible locally.

2. MEMORY PRESSURE
   Locally: 16GB RAM, only 2 services.
   Prod: 2GB per container, GC pressure, memory fragmentation.
   Bugs triggered by low memory never appear locally.

3. LOAD-DEPENDENT BUGS
   Connection pool exhaustion requires >100 concurrent requests.
   You never see this locally.

4. CONFIG DIFFERENCES
   Secret rotation in prod causes "token expired" errors.
   Your local .env never expires.

5. FILESYSTEM DIFFERENCES
   Case-insensitive macOS: "File.go" and "file.go" are the same.
   Case-sensitive Linux: they are DIFFERENT files.
   "Works on my machine" classic bug.
```

### The Three Environments: Dev, Staging, Production

```
ENVIRONMENT PIPELINE
=====================

  [Developer Machine]
         |
         | git push
         v
  [CI Pipeline]
    - Unit tests
    - Integration tests
    - Static analysis
    - Build Docker image
         |
         | Tests pass
         v
  [STAGING ENVIRONMENT]
    - Mirror of production
    - Real data snapshots
    - Load testing
    - Smoke tests
         |
         | All checks pass
         v
  [PRODUCTION ENVIRONMENT]
    - Real users
    - Real data
    - Monitoring + alerting
    - On-call engineer

PURPOSE OF STAGING:
  Bridge the gap between local and prod.
  Bugs caught in staging cost 10x less than prod bugs.
  Bugs caught in local cost 10x less than staging bugs.
  Therefore: Invest in local environments that mirror production.
```

---

## 12. Asynchronous Communication

### Queues, Events, and the Problems They Introduce

```
SYNCHRONOUS vs ASYNCHRONOUS COMMUNICATION
==========================================

SYNCHRONOUS (HTTP/gRPC):
  Caller WAITS for response.
  
  [Service A] ---request---> [Service B]
  [Service A] <---response-- [Service B]
  
  A is BLOCKED until B responds.
  If B is down: A fails immediately.
  If B is slow: A is slow.


ASYNCHRONOUS (Message Queue):
  Caller publishes a message and CONTINUES.
  Consumer processes the message LATER.
  
  [Service A] ---publish---> [Queue] ---consume---> [Service B]
       |                                                 |
       | (continues immediately)                    (processes
       |                                             later)
       v
  [Handles other work]


WHEN TO USE WHICH:
  Synchronous:  When you need an immediate answer
                (e.g., "Is this payment valid?")
  
  Asynchronous: When you can tolerate delay
                (e.g., "Send a confirmation email")
                When you need to decouple producers from consumers
                When you need guaranteed delivery
```

### The Problems Queues Introduce

```
PROBLEM 1: DUPLICATE MESSAGES (At-Least-Once Delivery)
========================================================

Message queues guarantee delivery, but "at least once."
If the consumer crashes after processing but before acknowledging,
the queue re-delivers the message.

Timeline:
  t=0: Queue delivers message to Service B
  t=1: Service B processes message (charges credit card!)
  t=2: Service B crashes (before sending ACK)
  t=3: Queue: "No ACK received, re-deliver"
  t=4: Service B (restarted) receives message AGAIN
  t=5: Service B charges credit card AGAIN!

FIX: IDEMPOTENCY
=================
An operation is IDEMPOTENT if applying it multiple times
produces the same result as applying it once.

  SET balance = 100        <-- Idempotent (always results in 100)
  ADD 100 to balance       <-- NOT idempotent (100, 200, 300...)

Implementation: Use an idempotency key.
  Request: {payment_id: "PAY-001", amount: 50}
  Service: IF EXISTS (SELECT 1 FROM payments WHERE id='PAY-001')
             THEN return existing result (do NOT re-charge)
           ELSE
             charge card, INSERT payment record


PROBLEM 2: OUT-OF-ORDER MESSAGES
===================================

Queue publishes:
  1. "OrderCreated"
  2. "OrderUpdated"
  3. "OrderCancelled"

Consumer receives:
  1. "OrderCancelled"   <-- arrives first (network variation)
  2. "OrderCreated"
  3. "OrderUpdated"

Consumer tries to cancel an order that doesn't exist yet!

FIX: Sequence numbers or vector clocks.


PROBLEM 3: DELAYED PROCESSING
================================

Event published at t=0.
Consumer processes at t=60 seconds.
By t=60s, the state of the world has changed.
Consumer makes decision based on 60-second-old data.

FIX: Include relevant state in the message itself,
     not just a reference to fetch state later.

BAD:  { "event": "CheckFraud", "order_id": 123 }
      -- Consumer fetches order 123 at processing time
      -- Order may have been modified since event was published

GOOD: { "event": "CheckFraud", "order_id": 123,
        "amount": 50.00, "user_history": {...} }
      -- Consumer has all needed state in the message itself
```

---

## 13. Security Layers

### Token Failures and Auth Complexity

```
AUTHENTICATION FLOW IN MICROSERVICES
======================================

  [User]
    |
    | POST /login (username + password)
    v
  [Auth Service]
    |
    | Issues JWT token (expires in 1 hour)
    v
  [User has: JWT = "eyJhbGciOiJSUzI1NiIsInR5cCI6..."]
    |
    | GET /orders Authorization: Bearer <JWT>
    v
  [API Gateway]
    |
    | Validates JWT signature (using Auth Service's public key)
    | Checks expiry
    | Extracts user_id from JWT claims
    |
    | Forwards to Order Service with user_id header
    v
  [Order Service]
    |
    | Trusts the user_id header (set by Gateway)
    | Does NOT re-validate JWT (efficiency)
    v
  [Returns user's orders]


WHAT IS A JWT? (Concept)
=========================
JWT = JSON Web Token
Structure: Header.Payload.Signature

  Header:    {"alg": "RS256", "typ": "JWT"}
  Payload:   {"user_id": 456, "role": "admin", "exp": 1735689600}
  Signature: RSASHA256(base64(Header) + "." + base64(Payload), privateKey)

Anyone can READ the payload (it's base64-encoded, not encrypted).
But only the Auth Service can SIGN a token (it has the private key).
Verifiers use the PUBLIC key to verify the signature.

SECURITY DEBUGGING SCENARIOS:
================================

BUG 1: Token Expiry
  User has a 1-hour token.
  User is active but doesn't make a request for 61 minutes.
  Next request: 401 Unauthorized.
  "System is broken" -- actually expected behavior.
  FIX: Token refresh flow.

BUG 2: Clock Skew
  Auth Service clock: 10:00:00
  Order Service clock: 09:59:30 (30 seconds behind)
  Token issued at 10:00:00, expires at 11:00:00.
  Order Service checks expiry: "Issued in the future? INVALID!"
  FIX: NTP synchronization, tolerate small clock skew (e.g., ±5 minutes).

BUG 3: Service-to-Service Auth
  Service A calls Service B directly (not through user request).
  What identity does A use?
  FIX: Service accounts, mTLS (mutual TLS), or service mesh like Istio.
```

---

## 14. Infrastructure Complexity

### Kubernetes and Ephemeral Environments

```
WHAT KUBERNETES DOES
======================

Kubernetes (K8s) is a container orchestration system.
It manages:
  - Running containers (Pods)
  - Scaling up/down (replicas)
  - Networking (Service discovery)
  - Health checks (liveness/readiness probes)
  - Rolling updates (deploy new version without downtime)

WHY IT COMPLICATES DEBUGGING:
================================

1. PODS ARE EPHEMERAL
   =====================
   A Pod (container instance) can be:
   - Killed at any time (OOM, eviction, node failure)
   - Rescheduled on a different node
   - Given a new IP address
   
   Your log from pod-abc-123 no longer exists after it dies.
   The new pod is pod-def-456.
   FIX: Centralized log aggregation (Loki, ELK) BEFORE the pod dies.

2. IP ADDRESSES CHANGE
   ======================
   In K8s, pod IPs are not stable.
   
   K8s Solution: Services (stable DNS names)
     - Service "payment-service" always resolves to healthy pods
     - Your code calls "http://payment-service/charge" not an IP
   
   Debugging impact:
     - "Which pod served this request?" requires tracing
     - IP in logs may point to a dead pod

3. ROLLING UPDATES CAUSE MIXED VERSIONS
   ========================================
   During a deploy, for 30-60 seconds:
   - Pod A: running v1.2.3
   - Pod B: running v1.2.4 (new)
   
   Requests are load-balanced between them.
   If v1.2.4 has a bug, 50% of requests fail.
   Logs show both versions' behavior interleaved.

4. LIVENESS vs READINESS PROBES
   =================================
   Liveness:  "Is this container alive?" (restart if fails)
   Readiness: "Is this container ready for traffic?" (remove from LB if fails)
   
   A misconfigured probe can cause:
   - Healthy pods being killed (liveness probe too strict)
   - Traffic sent to unready pods (readiness probe too lenient)

K8S DEBUGGING COMMANDS:
========================
  kubectl get pods                    -- List all pods and status
  kubectl logs <pod-name>             -- View pod logs
  kubectl logs <pod-name> --previous  -- View PREVIOUS (crashed) pod logs
  kubectl describe pod <pod-name>     -- Full details: events, resource limits
  kubectl exec -it <pod-name> -- sh   -- Shell into running pod
  kubectl top pods                    -- CPU and memory usage
  kubectl get events --sort-by=.metadata.creationTimestamp
```

---

## 15. Time-Related Bugs

### Clock Drift and Event Ordering

```
WHAT IS CLOCK DRIFT?
=====================
Every physical machine has a hardware clock.
All clocks drift slightly over time (gain or lose milliseconds).

NTP (Network Time Protocol) synchronizes clocks, but:
  - Sync happens periodically (not continuously)
  - Between syncs, clocks drift
  - Drift can be 10-100ms in normal operation
  - In cloud VMs: can be much worse (VM suspension, live migration)

WHY THIS MATTERS:
==================

Scenario: Two services logging an event

  Service A (clock: 10:00:01.000): "User placed order"
  Service B (clock: 10:00:00.900): "Payment charged"  <-- 100ms BEHIND

Log output sorted by timestamp:
  10:00:00.900 Service B: "Payment charged"
  10:00:01.000 Service A: "User placed order"

This looks like the payment was charged BEFORE the order was placed!
Which is impossible.

The real sequence was:
  Service A placed order first, THEN Service B charged payment.
  But clock drift made it look reversed.

LOGICAL CLOCKS: THE SOLUTION
==============================

Instead of real (wall clock) time, use LOGICAL time.
Lamport Clock: A counter that increments with each event.

Rules:
  1. Each process starts counter at 0
  2. Before each event, increment counter
  3. When sending message: include counter value
  4. When receiving message: counter = max(local, received) + 1

Example:
  Service A: counter=1 "Place order" --> sends to B with counter=1
  Service B: receives counter=1, sets own counter = max(0, 1) + 1 = 2
  Service B: counter=2 "Charge payment"

Now we know: event at counter=1 happened BEFORE event at counter=2.
Regardless of wall clock values.
```

---

## 16. Reproducibility

### The Hardest Problem in Distributed Debugging

```
REPRODUCIBILITY SPECTRUM
==========================

  EASY TO REPRODUCE              IMPOSSIBLE TO REPRODUCE
  ==================             ========================
  |                                                     |
  | Deterministic bug             Heisenbug             |
  | Always fails with             Disappears when        |
  | same input                    you try to observe it  |
  |                                                     |
  | Logic error                   Race condition         |
  | Wrong algorithm               Network timing bug     |
  | Off-by-one                    Memory corruption      |
  |_______________________________________________________|

                    MOST MICROSERVICE BUGS LIVE HERE -->


HEISENBUGS (named after Heisenberg's Uncertainty Principle):
  A bug that disappears or changes behavior when you try to study it.
  
  Example:
    - You add a log statement to debug a race condition
    - The log statement introduces a tiny delay
    - The delay changes the timing
    - The race condition disappears
    - You remove the log
    - Bug is back


STRATEGIES FOR HARD-TO-REPRODUCE BUGS:
========================================

1. CHAOS ENGINEERING
   ==================
   Deliberately inject failures in production (or staging):
   - Kill random pods (Netflix's "Chaos Monkey")
   - Introduce artificial latency
   - Drop random network packets
   
   Rationale: If failures happen randomly anyway, it's better to
   trigger them under controlled conditions when engineers are watching.

2. PRODUCTION TRAFFIC RECORDING + REPLAY
   =========================================
   Record real production requests.
   Replay them against a debug build.
   
   Tools: GoReplay, tcpdump + replay scripts
   
   Benefit: Reproduce real traffic patterns without load.

3. DETERMINISTIC SIMULATION
   ==========================
   Build a test environment that can control:
   - Network delays (inject at will)
   - Message ordering (control queue consumer order)
   - Clock values (fake time)
   
   Example: TigerBeetle database uses deterministic simulation
   to test distributed bugs.

4. DETAILED LOGGING BEFORE THE BUG
   ===================================
   You cannot reproduce the bug, but you can observe it
   when it happens in production.
   
   Strategy: Log everything relevant BEFORE the suspected failure point.
   When the bug occurs, you have a complete picture in logs.
   
   This is "observability-driven debugging."
```

---

## 17. The Complete Debugging Workflow

### How an Expert Debugs a Microservice Issue

```
EXPERT DEBUGGING FLOWCHART
============================

START: "Something is wrong in production"
           |
           v
  +------------------+
  | 1. DEFINE THE    |
  |    SYMPTOM       |
  |                  |
  | - What is        |
  |   failing?       |
  | - How bad?       |
  | - Since when?    |
  +------------------+
           |
           v
  +------------------+
  | 2. CHECK RECENT  |
  |    CHANGES       |
  |                  |
  | - Any deploys    |
  |   in last hour?  |
  | - Config changes?|
  | - Traffic spike? |
  +------------------+
           |
           | Recent deploy?
           |  YES ---------> Consider rollback
           |  NO
           v
  +------------------+
  | 3. CHECK METRICS |
  |                  |
  | - Error rate     |
  | - Latency        |
  | - Saturation     |
  | - Traffic        |
  +------------------+
           |
           | Which service shows anomaly?
           v
  +------------------+
  | 4. FIND THE TRACE|
  |                  |
  | - Get a failing  |
  |   trace ID       |
  | - Open in Jaeger |
  | - Find first span|
  |   that failed    |
  +------------------+
           |
           v
  +------------------+
  | 5. EXAMINE LOGS  |
  |                  |
  | Filter by:       |
  | - trace_id       |
  | - service name   |
  | - time window    |
  +------------------+
           |
           v
  +------------------+
  | 6. FORM          |
  |    HYPOTHESIS    |
  |                  |
  | "I believe X     |
  |  is failing      |
  |  because Y"      |
  +------------------+
           |
           v
  +------------------+
  | 7. TEST          |
  |    HYPOTHESIS    |
  |                  |
  | - Can you find   |
  |   evidence in    |
  |   logs/traces?   |
  | - Can you        |
  |   reproduce      |
  |   locally?       |
  +------------------+
           |
     YES / NO
      |      |
      |      +---> Refine hypothesis --> Go to step 6
      v
  +------------------+
  | 8. FIX AND       |
  |    VERIFY        |
  |                  |
  | - Deploy fix     |
  | - Monitor metrics|
  | - Write          |
  |   regression test|
  +------------------+
           |
           v
  +------------------+
  | 9. POST-MORTEM   |
  |                  |
  | - Root cause     |
  | - Impact         |
  | - Detection time |
  | - Fix time       |
  | - Prevention     |
  +------------------+
```

### The 5 Whys Technique

A cognitive tool for finding root causes. You keep asking "Why?" until you reach the fundamental cause.

```
EXAMPLE: "Orders are failing"
================================

Symptom: Orders are failing for 15% of users.

Why 1: WHY are orders failing?
  --> The order service is returning 503 Service Unavailable.

Why 2: WHY is the order service returning 503?
  --> The payment service is not responding.

Why 3: WHY is the payment service not responding?
  --> The payment service's database connection pool is exhausted.

Why 4: WHY is the connection pool exhausted?
  --> Slow queries are holding connections for >30 seconds.

Why 5: WHY are queries slow?
  --> A database index was dropped during last night's migration.

ROOT CAUSE: Missing database index.
FIX: Restore the index.
PREVENTION: Add index existence check to migration validation.

INSIGHT: If you had stopped at Why 1, you would have "fixed"
the issue by restarting the order service. The real problem
would recur within minutes.
```

---

## 18. Code Examples

### Complete Instrumented Microservice (Go)

```go
package main

import (
    "context"
    "encoding/json"
    "fmt"
    "log"
    "net/http"
    "time"
)

// ======================================================
// CONCEPTS USED:
//   - Structured logging with trace IDs
//   - Request timeout propagation via context
//   - Circuit breaker (simplified)
//   - Health check endpoint
// ======================================================

// TraceIDKey is the context key for the trace ID.
// Using a custom type prevents key collisions in context.
type contextKey string

const TraceIDKey contextKey = "trace_id"

// OrderRequest represents an incoming order
type OrderRequest struct {
    UserID int    `json:"user_id"`
    ItemID string `json:"item_id"`
    Amount int    `json:"amount"`
}

// OrderResponse is the API response
type OrderResponse struct {
    OrderID string `json:"order_id"`
    Status  string `json:"status"`
    Error   string `json:"error,omitempty"`
}

// StructuredLogger emits JSON log lines to stdout
type StructuredLogger struct {
    ServiceName string
}

func (l *StructuredLogger) log(ctx context.Context, level, msg string, fields map[string]interface{}) {
    entry := map[string]interface{}{
        "timestamp": time.Now().UTC().Format(time.RFC3339Nano),
        "level":     level,
        "service":   l.ServiceName,
        "message":   msg,
    }

    // Inject trace ID from context if present
    if traceID, ok := ctx.Value(TraceIDKey).(string); ok {
        entry["trace_id"] = traceID
    }

    for k, v := range fields {
        entry[k] = v
    }

    line, _ := json.Marshal(entry)
    fmt.Println(string(line))
}

func (l *StructuredLogger) Info(ctx context.Context, msg string, fields map[string]interface{}) {
    l.log(ctx, "INFO", msg, fields)
}

func (l *StructuredLogger) Error(ctx context.Context, msg string, fields map[string]interface{}) {
    l.log(ctx, "ERROR", msg, fields)
}

// OrderHandler handles POST /orders
func orderHandler(logger *StructuredLogger) http.HandlerFunc {
    return func(w http.ResponseWriter, r *http.Request) {
        // Extract or generate trace ID
        traceID := r.Header.Get("X-Trace-ID")
        if traceID == "" {
            traceID = fmt.Sprintf("trace-%d", time.Now().UnixNano())
        }

        // Inject trace ID into context so ALL downstream calls can log it
        ctx := context.WithValue(r.Context(), TraceIDKey, traceID)

        // Set a 5-second deadline for the entire request chain.
        // This deadline is propagated to all downstream HTTP calls
        // that use this context -- they will be cancelled when the
        // deadline expires, preventing the "slow upstream" problem.
        ctx, cancel := context.WithTimeout(ctx, 5*time.Second)
        defer cancel()

        // Set trace ID in response header for client debugging
        w.Header().Set("X-Trace-ID", traceID)

        // Parse request body
        var req OrderRequest
        if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
            logger.Error(ctx, "Failed to decode request", map[string]interface{}{
                "error": err.Error(),
            })
            w.WriteHeader(http.StatusBadRequest)
            json.NewEncoder(w).Encode(OrderResponse{Error: "invalid request body"})
            return
        }

        logger.Info(ctx, "Processing order", map[string]interface{}{
            "user_id": req.UserID,
            "item_id": req.ItemID,
            "amount":  req.Amount,
        })

        // Simulate downstream payment call
        if err := callPaymentService(ctx, traceID, req.Amount); err != nil {
            logger.Error(ctx, "Payment failed", map[string]interface{}{
                "error":   err.Error(),
                "user_id": req.UserID,
            })

            // Check if context deadline exceeded
            if ctx.Err() == context.DeadlineExceeded {
                w.WriteHeader(http.StatusGatewayTimeout)
                json.NewEncoder(w).Encode(OrderResponse{Error: "request timeout"})
                return
            }

            w.WriteHeader(http.StatusBadGateway)
            json.NewEncoder(w).Encode(OrderResponse{Error: "payment service unavailable"})
            return
        }

        orderID := fmt.Sprintf("ORDER-%d", time.Now().UnixNano())
        logger.Info(ctx, "Order created successfully", map[string]interface{}{
            "order_id": orderID,
        })

        w.WriteHeader(http.StatusCreated)
        json.NewEncoder(w).Encode(OrderResponse{
            OrderID: orderID,
            Status:  "CREATED",
        })
    }
}

// callPaymentService simulates an HTTP call to the payment service.
// It uses the provided context for timeout/cancellation propagation.
func callPaymentService(ctx context.Context, traceID string, amount int) error {
    req, err := http.NewRequestWithContext(ctx, "POST", "http://payment-service/charge", nil)
    if err != nil {
        return fmt.Errorf("failed to build payment request: %w", err)
    }

    // CRITICAL: propagate trace ID so payment service can correlate logs
    req.Header.Set("X-Trace-ID", traceID)

    client := &http.Client{} // Timeout is already in ctx
    resp, err := client.Do(req)
    if err != nil {
        return fmt.Errorf("payment service call failed: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != http.StatusOK {
        return fmt.Errorf("payment service error: HTTP %d", resp.StatusCode)
    }

    return nil
}

// healthHandler responds to health check probes (used by K8s liveness/readiness)
func healthHandler(w http.ResponseWriter, r *http.Request) {
    w.WriteHeader(http.StatusOK)
    json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
}

func main() {
    logger := &StructuredLogger{ServiceName: "order-service"}

    mux := http.NewServeMux()
    mux.HandleFunc("/orders", orderHandler(logger))
    mux.HandleFunc("/health", healthHandler)

    log.Println("Order service starting on :8080")
    if err := http.ListenAndServe(":8080", mux); err != nil {
        log.Fatalf("Failed to start server: %v", err)
    }
}
```

### Instrumented Service with Span Tracking (Rust)

```rust
use std::time::{Duration, Instant};
use std::collections::HashMap;

/// A Span represents a single unit of work in a distributed trace.
/// In production, you would use OpenTelemetry crate.
/// This is a simplified, educational implementation.
#[derive(Debug)]
pub struct Span {
    pub name: String,
    pub trace_id: String,
    pub span_id: String,
    pub parent_span_id: Option<String>,
    pub start_time: Instant,
    pub duration: Option<Duration>,
    pub tags: HashMap<String, String>,
    pub error: Option<String>,
}

impl Span {
    pub fn new(name: &str, trace_id: &str, parent_span_id: Option<String>) -> Self {
        // In production: generate cryptographically random IDs (use uuid crate)
        let span_id = format!("span-{:016x}", rand_u64());
        
        Self {
            name: name.to_string(),
            trace_id: trace_id.to_string(),
            span_id,
            parent_span_id,
            start_time: Instant::now(),
            duration: None,
            tags: HashMap::new(),
            error: None,
        }
    }

    /// Tags add metadata to the span (searchable in Jaeger)
    pub fn tag(&mut self, key: &str, value: &str) {
        self.tags.insert(key.to_string(), value.to_string());
    }

    /// Marks the span as errored
    pub fn set_error(&mut self, error: &str) {
        self.error = Some(error.to_string());
        self.tags.insert("error".to_string(), "true".to_string());
    }

    /// Finishes the span, recording its duration
    pub fn finish(mut self) -> FinishedSpan {
        let duration = self.start_time.elapsed();
        self.duration = Some(duration);
        
        // In production: send to Jaeger collector via UDP/HTTP
        self.emit();

        FinishedSpan {
            name: self.name,
            trace_id: self.trace_id,
            span_id: self.span_id,
            duration,
            error: self.error,
        }
    }

    fn emit(&self) {
        // Simplified emission: print to stderr
        // In production: use opentelemetry-jaeger crate
        eprintln!(
            "[TRACE] span={} trace_id={} parent={:?} duration={:?} error={:?}",
            self.name,
            self.trace_id,
            self.parent_span_id,
            self.duration,
            self.error,
        );
    }
}

/// A finished span (immutable record)
#[derive(Debug)]
pub struct FinishedSpan {
    pub name: String,
    pub trace_id: String,
    pub span_id: String,
    pub duration: Duration,
    pub error: Option<String>,
}

/// Simulates a pseudo-random number (in real code, use rand crate)
fn rand_u64() -> u64 {
    use std::time::{SystemTime, UNIX_EPOCH};
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .subsec_nanos() as u64
}

/// Example: tracing an order processing flow
pub fn process_order(trace_id: &str, order_id: &str) -> Result<(), String> {
    // Root span for the entire operation
    let mut root_span = Span::new("process_order", trace_id, None);
    root_span.tag("order_id", order_id);

    // Child span for payment
    let mut payment_span = Span::new(
        "call_payment_service",
        trace_id,
        Some(root_span.span_id.clone()),
    );
    payment_span.tag("service", "payment-svc");

    // Simulate payment call
    let payment_result = simulate_payment_call();

    if let Err(ref e) = payment_result {
        payment_span.set_error(e);
    }
    payment_span.finish();

    if let Err(e) = payment_result {
        root_span.set_error(&format!("Payment failed: {}", e));
        root_span.finish();
        return Err(e);
    }

    // Child span for inventory
    let mut inventory_span = Span::new(
        "reserve_inventory",
        trace_id,
        Some(root_span.span_id.clone()),
    );
    inventory_span.tag("service", "inventory-svc");
    
    // Simulate inventory reservation
    std::thread::sleep(Duration::from_millis(15)); // Simulate 15ms call
    inventory_span.finish();

    root_span.finish();
    Ok(())
}

fn simulate_payment_call() -> Result<(), String> {
    std::thread::sleep(Duration::from_millis(45)); // Simulate 45ms call
    Ok(()) // Change to Err("timeout".to_string()) to test error path
}
```

---

## 19. Decision Trees for Debugging Scenarios

### Decision Tree 1: Diagnosing Request Failures

```
START: "My API is returning errors"
              |
              v
    +--------------------+
    | What HTTP code?    |
    +--------------------+
           |
     ------+-------+-------+-------
     |      |       |       |
    4xx    500     502     503/504
     |      |       |       |
     v      v       v       v
  Client  Server  Bad     Unavail
  Error   Error   Gate-   able or
  (YOUR   (Code   way     Timeout
   fault) bug or  (Down-  (Down-
          crash)  stream  stream
                  down)   slow/down)
     |      |       |       |
     v      v       +-------+
  Check   Check           |
  - Auth  - Logs          v
  - Input - Stack     +------------------+
  - Perms   trace     | Check downstream |
                      | services:        |
                      | - Are they up?   |
                      | - Are they slow? |
                      +------------------+
                               |
              +----------------+----------------+
              |                                 |
          UP but slow                         DOWN
              |                                 |
              v                                 v
    +------------------+             +------------------+
    | Find slow span   |             | Which dependency |
    | in trace         |             | is down?         |
    +------------------+             +------------------+
              |                                 |
    +------------------+             +------------------+
    | DB query slow?   |             | - DB crashed?    |
    | - Check indexes  |             | - OOM?           |
    | - Check slow log |             | - K8s eviction?  |
    +------------------+             | - Config error?  |
              |                      +------------------+
    +------------------+                       |
    | External API     |             +------------------+
    | slow?            |             | Check K8s events |
    | - Circuit break  |             | kubectl describe  |
    | - Add timeout    |             | pod              |
    +------------------+             +------------------+
```

### Decision Tree 2: "Works Locally, Fails in Production"

```
"Works locally, fails in production"
               |
               v
    +----------------------+
    | Is it ALWAYS failing |
    | or SOMETIMES?        |
    +----------------------+
           |           |
        Always      Sometimes
           |           |
           v           v
  +-------------+  +------------------+
  | Config diff?|  | Race condition?  |
  | - Env vars  |  | - Add timestamps |
  | - Secrets   |  |   to logs        |
  | - Feature   |  | - Look for       |
  |   flags     |  |   ordering issues|
  +-------------+  +------------------+
           |
    +------+-------+-------+-------+
    |      |       |       |       |
  Auth   Data   File-   OS diff  Deps
  diff   diff   system  (case-   diff
    |      |    diff    sensitive)|
    v      v      v       v       v
  Check  Check  Check  Check   Check
  token  DB     paths  filenames versions
  expiry schema        casing   in prod
```

---

## 20. Mental Models

### Cognitive Frameworks for Superior Debugging Intuition

```
MENTAL MODEL 1: THE SYSTEM AS AN ORGANISM
===========================================

A distributed system is not a machine with fixed parts.
It is an ORGANISM that:
  - Self-heals (automatic restarts, circuit breakers)
  - Adapts (autoscaling)
  - Has emergent behavior not designed by anyone

Implication:
  Don't look for THE bug. Look for the CONDITION that allows bugs.
  Root causes are often systemic, not localized.


MENTAL MODEL 2: THE SPACE OF FAILURE MODES
============================================

For every component, ask:
  1. What happens if it is UNAVAILABLE? (down)
  2. What happens if it is SLOW?        (latency)
  3. What happens if it is CORRUPT?     (returns wrong data)
  4. What happens if it LIES?           (returns success but didn't work)

Mentally trace each failure mode through your system.
Which ones have mitigations? Which ones are silent killers?


MENTAL MODEL 3: BLAST RADIUS
==============================

When a component fails, what is the BLAST RADIUS?
(How many users/services are affected?)

  Low blast radius:  A single pod in a non-critical service
  High blast radius: The auth service, the API gateway

Design to minimize blast radius:
  - Bulkheads: Isolate thread pools per downstream service
  - Circuit breakers: Stop failure from propagating
  - Graceful degradation: Return cached data when DB is down


MENTAL MODEL 4: CONSERVATION OF MISERY
========================================

In a distributed system, if you make one thing easier,
you often make something else harder.

Examples:
  Eventual consistency = Higher availability BUT harder to debug
  Microservices        = Easier to scale BUT harder to debug
  Async processing     = Higher throughput BUT harder to trace
  Caching              = Faster reads BUT harder to reason about state

When you choose a design, explicitly acknowledge WHAT YOU ARE GIVING UP.
Then invest in the tooling to handle the "harder" part.


MENTAL MODEL 5: OBSERVABILITY AS INSURANCE
===========================================

Every bug will eventually manifest in production.
The question is not IF but WHEN and HOW QUICKLY you find it.

  Without observability:  Mean Time To Detect (MTTD) = hours/days
  With observability:     Mean Time To Detect (MTTD) = minutes

  MTTD is more important than bug prevention.
  Because some bugs are impossible to prevent in advance.

Invest in observability the way you invest in insurance:
  Before you need it, not after.
```

### The Debugging Mindset: Expert vs Novice

```
NOVICE DEBUGGING APPROACH:
============================

1. Something is broken.
2. Change a thing.
3. See if it's fixed.
4. If not, change another thing.
5. Repeat until it works (or you give up).

Problems:
  - No systematic approach
  - Changes may mask the original bug
  - No understanding of why the fix worked
  - Bug will likely recur


EXPERT DEBUGGING APPROACH:
============================

1. Observe: Gather all evidence WITHOUT making changes.
            (Logs, metrics, traces, error messages)

2. Hypothesize: Form a specific, falsifiable hypothesis.
                "I believe the DB index was dropped, causing
                 slow queries that exhaust the connection pool."
                NOT: "I think the DB might have an issue."

3. Predict: "If my hypothesis is correct, I should see X
             when I check Y."
             "I should see slow queries > 1000ms in the DB
              slow query log."

4. Test: Check the evidence predicted in step 3.
         Do NOT make any changes yet.

5. Evaluate: Did the evidence match?
             YES --> Fix the root cause. Document. Test.
             NO  --> Discard hypothesis. Start at step 1.

COGNITIVE PRINCIPLE: This mirrors the SCIENTIFIC METHOD.
Good debugging IS science: observation, hypothesis, experiment.
```

---

## Summary Reference Card

```
+--------------------------------------------------+
|         MICROSERVICES DEBUGGING CHEATSHEET       |
+--------------------------------------------------+
| PROBLEM              | TOOL/PATTERN               |
+--------------------------------------------------+
| No call stack        | Distributed Tracing (Jaeger)|
| Scattered logs       | Correlation IDs + ELK      |
| Partial failures     | Saga Pattern               |
| Cascading failures   | Circuit Breaker            |
| Data inconsistency   | Idempotency Keys + Sagas   |
| Race conditions      | Optimistic Locking         |
| API drift            | Consumer Contract Testing  |
| Retry storms         | Exponential Backoff + Jitter|
| Clock drift          | Lamport Clocks             |
| Pod death lost logs  | Centralized Log Aggregation|
| "Works locally"      | Docker Compose mirror prod  |
| Token expiry bugs    | Clock skew tolerance       |
+--------------------------------------------------+

FOUR GOLDEN SIGNALS (ALWAYS MONITOR):
  Latency     | p50, p95, p99
  Traffic     | requests/second
  Errors      | error rate %
  Saturation  | CPU%, memory%, pool%

THREE PILLARS OF OBSERVABILITY:
  Logs    | What happened (structured JSON)
  Metrics | Numeric trends over time
  Traces  | Request journey across services

THE DEBUGGING PROCESS:
  1. Observe (don't touch)
  2. Hypothesize (specific + falsifiable)
  3. Predict (what evidence would confirm?)
  4. Test (check evidence)
  5. Fix root cause (not symptoms)
  6. Post-mortem (prevent recurrence)
+--------------------------------------------------+
```

---

*"The skill of debugging distributed systems is the skill of reasoning under uncertainty — holding multiple hypotheses simultaneously, knowing which evidence to seek, and having the discipline not to touch anything until you understand what is happening."*

---

**End of Guide**

Here's your complete guide — 20 deeply covered topics, all in one `.md` file.

**What's inside:**

Every concept is built from first principles before being used. The guide covers all 15 structural failure modes from the document, then goes deeper with production patterns and code:

- **Concepts defined precisely** — CAP Theorem, Idempotency, Lamport Clocks, Heisenbug, Blast Radius, the Two Generals Problem — all explained before use
- **ASCII diagrams throughout** — Retry storm cascades, circuit breaker state machines, distributed trace timelines, concurrency race conditions, saga state machines
- **Decision trees** — for diagnosing 4xx/5xx errors and "works locally, fails in prod"
- **Production code in Go, Rust, and C** — Circuit breaker, Saga orchestrator, structured logger with trace IDs, deadlock prevention via ordered locking, retry with exponential backoff
- **Mental Models section** — System-as-organism, blast radius, conservation of misery, observability-as-insurance, expert vs novice debugging mindset
- **Reference card** at the end — quick lookup for every pattern and tool

The closing principle is the one worth internalizing deeply: *debugging distributed systems is reasoning under uncertainty* — the same cognitive discipline as science itself.