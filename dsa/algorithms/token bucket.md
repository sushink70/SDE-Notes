# Token Bucket — A Comprehensive Deep-Dive Guide

> *"Mastery is not about doing a thousand things. It's about doing one thing a thousand times — deeper each time."*

---

## Table of Contents

1. [Foundational Concepts — Before We Begin](#1-foundational-concepts--before-we-begin)
2. [What Is a Token Bucket?](#2-what-is-a-token-bucket)
3. [Core Terminology Decoded](#3-core-terminology-decoded)
4. [The Mental Model — Think Like a Bank](#4-the-mental-model--think-like-a-bank)
5. [Algorithm Mechanics — Step by Step](#5-algorithm-mechanics--step-by-step)
6. [ASCII Visualizations & Diagrams](#6-ascii-visualizations--diagrams)
7. [Mathematical Model](#7-mathematical-model)
8. [Algorithm Flowcharts (ASCII)](#8-algorithm-flowcharts-ascii)
9. [Decision Trees](#9-decision-trees)
10. [Token Bucket vs. Other Rate Limiters](#10-token-bucket-vs-other-rate-limiters)
11. [Implementation in C](#11-implementation-in-c)
12. [Implementation in Go](#12-implementation-in-go)
13. [Implementation in Rust](#13-implementation-in-rust)
14. [Thread-Safe / Concurrent Implementations](#14-thread-safe--concurrent-implementations)
15. [Distributed Token Bucket](#15-distributed-token-bucket)
16. [Edge Cases & Pitfalls](#16-edge-cases--pitfalls)
17. [Time & Space Complexity Analysis](#17-time--space-complexity-analysis)
18. [Real-World Applications](#18-real-world-applications)
19. [Testing Strategies](#19-testing-strategies)
20. [Advanced Variants](#20-advanced-variants)
21. [Mental Models & Cognitive Strategies](#21-mental-models--cognitive-strategies)

---

## 1. Foundational Concepts — Before We Begin

### What Is Rate Limiting?

Imagine you run a restaurant. If 1000 customers storm in simultaneously, the kitchen collapses. You set a rule: **serve at most 50 orders per minute**. That rule is **rate limiting**.

In software systems:
- A **client** sends **requests** to a **server**
- Without limits, a single bad actor (or bug) can send millions of requests, crashing the server
- **Rate limiting** enforces a maximum request throughput

```
WITHOUT RATE LIMITING:
Client ----XXXXXXXXXXXXXXXXXXXXXXX----> Server (OVERLOADED, CRASHES)

WITH RATE LIMITING:
Client ----X--X--X--X--X-----------> Server (Healthy, controlled load)
```

### Why Do We Need It?

| Problem               | Rate Limiting Solution                     |
|-----------------------|--------------------------------------------|
| DoS / DDoS attacks    | Throttle excess traffic per IP             |
| API abuse             | Enforce per-user quotas                    |
| Resource exhaustion   | Protect DB, CPU, memory                    |
| Fair usage            | Ensure all users get equal access          |
| Cost control          | Limit expensive downstream API calls       |

### Key Vocabulary (Plain English First)

| Term        | Plain Meaning                                              |
|-------------|------------------------------------------------------------|
| **Throughput** | How many requests pass per unit of time                |
| **Burst**      | A sudden spike of many requests at once               |
| **Token**      | A permission slip to make one request                 |
| **Bucket**     | A container that holds tokens (has a maximum capacity)|
| **Refill**     | Tokens being added to the bucket over time            |
| **Consume**    | Using one (or more) tokens to allow a request         |
| **Throttle**   | Reject or delay a request when bucket is empty        |

---

## 2. What Is a Token Bucket?

The **Token Bucket** is one of the oldest and most elegant rate-limiting algorithms. It was originally designed for **network traffic shaping** (controlling data flow in networks) but is now used everywhere from APIs to operating system schedulers.

### The Analogy

```
  +------------------------------------------+
  |           TOKEN BUCKET                   |
  |                                          |
  |   Drip tap adds tokens at rate R        |
  |           |                              |
  |           v                              |
  |   [T][T][T][T][T][T][ ][ ][ ][ ]        |
  |   ^-- tokens --^    ^-- empty --^        |
  |                                          |
  |   Capacity = C (max tokens bucket holds) |
  |                                          |
  |   Each request CONSUMES tokens           |
  |   Request rejected if bucket empty       |
  +------------------------------------------+
```

Think of it like this:
- You have a **bucket** with a **hole at the bottom**
- Water (tokens) **drips in** at a fixed rate from the top tap
- The bucket has a **maximum capacity** — excess water overflows and is lost
- Each **request** scoops out **some water**
- If the bucket is **dry**, the request is **denied**

This models two things simultaneously:
1. **Average rate** → controlled by the drip rate
2. **Burst allowance** → controlled by the bucket capacity

---

## 3. Core Terminology Decoded

### Token
A **token** is the unit of permission. Typically, each request needs **1 token**. But for weighted requests (e.g., uploading a 10MB file costs 10 tokens), you can consume more.

### Bucket Capacity (C)
The **maximum number of tokens** the bucket can hold. This defines the **maximum burst size** — the most requests that can be served instantly.

```
Capacity = 10

[T][T][T][T][T][T][T][T][T][T]  ← Full bucket (10 tokens)
 |
 10 requests can fire instantly (burst)
```

### Refill Rate (R)
Tokens are added at rate **R tokens per second**. This defines the **sustained throughput**.

```
R = 5 tokens/second

t=0s:  [T][T][T][T][T][ ][ ][ ][ ][ ]  (5 tokens)
t=1s:  [T][T][T][T][T][T][T][T][T][T]  (5+5=10, capped at 10)
t=2s:  [T][T][T][T][T][T][T][T][T][T]  (still 10, bucket full)
```

### Refill Interval
How often tokens are added. There are two sub-models:
- **Discrete refill**: Add R tokens every T seconds (batch)
- **Continuous refill**: Add tokens fractionally every millisecond (smooth)

The continuous model is more accurate and fair. We will implement both.

### Conforming / Non-Conforming Packets
- **Conforming**: Request that finds enough tokens → **allowed**
- **Non-conforming**: Request that finds insufficient tokens → **dropped or delayed**

---

## 4. The Mental Model — Think Like a Bank

Here is a powerful analogy: **Token Bucket is like a savings account.**

| Banking Concept     | Token Bucket Equivalent        |
|---------------------|-------------------------------|
| Account balance     | Current token count           |
| Salary (income)     | Token refill rate             |
| Spending            | Token consumption per request |
| Account limit       | Bucket capacity               |
| Overdraft denied    | Request rejected              |
| Saving up           | Burst allowance               |

Key insight: **you can "save up" tokens.** If traffic is quiet for 2 seconds and your rate is 5/sec, you accumulate 10 tokens (up to capacity). Then you can spend them all in a burst.

This is the fundamental difference from **Leaky Bucket** (which smooths output, no burst) and **Fixed Window** (which resets abruptly).

---

## 5. Algorithm Mechanics — Step by Step

### The Two Operations

**Operation 1: Refill**
```
Every Δt seconds have passed:
  new_tokens = Δt × refill_rate
  tokens = min(tokens + new_tokens, capacity)
```

**Operation 2: Consume**
```
When a request arrives:
  if tokens >= cost:
    tokens -= cost
    ALLOW request
  else:
    DENY request (or WAIT)
```

### The Lazy Refill Trick (Critical Insight)

Instead of a background thread constantly adding tokens, we use **lazy evaluation**:

> We don't actually add tokens continuously. Instead, we **remember the last time** we were checked, and when a new request arrives, we **calculate how many tokens should have accumulated** since then.

```
last_check_time = T₀
tokens          = 5

--- Request arrives at time T₁ ---

elapsed      = T₁ - T₀
earned       = elapsed × refill_rate
tokens       = min(tokens + earned, capacity)
last_check_time = T₁

--- Now check if tokens >= cost ---
```

This avoids a background goroutine/thread entirely. This is the **token bucket as a calculation**, not a running process.

---

## 6. ASCII Visualizations & Diagrams

### State Over Time

```
Bucket Capacity = 10, Refill Rate = 2 tokens/sec

Time  Tokens  Event
----  ------  ----------------------------------------
0s    10      [FULL] System starts
1s    10      No requests, would be 12 but capped at 10
2s     8      2 requests arrive, consume 2 tokens
3s     9      +1 token refilled (0.5s passed → 1 token)
      ...
4s     7      3 requests arrive
5s     9      2 tokens refilled (1s × 2/s)
6s     0      9 requests arrive — all succeed (burst!)
7s     2      2 tokens refilled, 0 requests
8s     0      2 requests arrive — succeed
8.1s   0      3 requests arrive — REJECTED (0 tokens)
9s     2      2 tokens refilled
```

### Burst Behavior Visualized

```
SCENARIO: Capacity=5, Rate=1/sec, 5 quiet seconds then flood

Tokens:
5 |████████████████|
4 |          ████  |         (consuming slowly here)
3 |               ░|
2 |                ░░        (fast burst depletes quickly)
1 |                  ░
0 |                   XXXXXXX (rejected after burst exhausted)
  +----+----+----+----+----+-----> time
  0    1    2    3    4    5
        ^ quiet period ^  ^ burst ^
```

### Two Clients Sharing One Bucket

```
CLIENT A ──┐
           ├──→ [BUCKET: 10 tokens] ──→ ALLOW/DENY
CLIENT B ──┘

Time=0: Bucket=10
  A requests 3 tokens → Bucket=7, ALLOW
  B requests 5 tokens → Bucket=2, ALLOW
  A requests 3 tokens → Bucket=-1? NO → DENY (only 2 left)
  B requests 2 tokens → Bucket=0, ALLOW
  A requests 1 token  → Bucket=-1? NO → DENY
  ...1 second passes...
  Bucket = min(0 + refill_rate × 1, 10) = refill_rate
```

### Per-User Buckets

```
USER_1 → [Bucket_1: capacity=100] → rate limit 100 req/min
USER_2 → [Bucket_2: capacity=100] → rate limit 100 req/min
USER_3 → [Bucket_3: capacity=100] → rate limit 100 req/min

HashMap<user_id, TokenBucket>
```

---

## 7. Mathematical Model

### Formal Definition

Let:
- `C` = bucket capacity (tokens)
- `R` = refill rate (tokens per second)
- `T(t)` = token count at time `t`
- `tₗ` = time of last update
- `n` = cost of current request (tokens)

**Refill equation:**
```
T(t) = min(T(tₗ) + R × (t - tₗ), C)
```

**Consume predicate:**
```
ALLOW(t, n) = T(t) >= n
T(t) := T(t) - n   if ALLOW
```

### Maximum Burst

```
Max burst = C tokens (consumed instantly, if bucket was full)
```

### Sustained Rate

```
Sustained throughput = R requests/second (long-term average)
```

### Wait Time for Next Token

When denied with current `T(t)` tokens and need `n`:

```
deficit = n - T(t)
wait_time = deficit / R   (seconds)
```

This is useful for "retry-after" headers in HTTP APIs.

```
Example:
  T(t) = 2 tokens, need n = 5 tokens, R = 1 token/sec
  deficit = 5 - 2 = 3
  wait_time = 3 / 1 = 3 seconds
```

### Invariant

The token count is always bounded:
```
0 ≤ T(t) ≤ C    for all t
```

---

## 8. Algorithm Flowcharts (ASCII)

### Main Flow: Request Arrives

```
                    +------------------+
                    |  Request Arrives |
                    +--------+---------+
                             |
                             v
                    +------------------+
                    | Get current time |
                    |       t_now      |
                    +--------+---------+
                             |
                             v
                    +---------------------------+
                    | elapsed = t_now - t_last  |
                    | earned  = elapsed × rate  |
                    | tokens  = min(tokens +    |
                    |           earned, capacity)|
                    | t_last  = t_now           |
                    +--------+------------------+
                             |
                             v
                    +---------------------------+
                    |    tokens >= cost?        |
                    +--------+------------------+
                             |
               +-------------+------------+
               | YES                      | NO
               v                          v
    +-------------------+      +----------------------+
    | tokens -= cost    |      | REJECT request       |
    | ALLOW request     |      | (optionally compute  |
    | return true       |      |  wait_time)          |
    +-------------------+      | return false         |
                               +----------------------+
```

### Refill Loop (Discrete Mode, Background Thread)

```
  +---------------------+
  | Start Refill Thread |
  +----------+----------+
             |
             v
  +---------------------+
  |     LOOP FOREVER    |<-----------+
  +----------+----------+            |
             |                       |
             v                       |
  +---------------------+            |
  | sleep(refill_interval)|          |
  +----------+----------+            |
             |                       |
             v                       |
  +-------------------------------------+
  | LOCK bucket mutex                   |
  | tokens = min(tokens + R, capacity)  |
  | UNLOCK mutex                        |
  +----------+--------------------------+
             |                       |
             +------------------------+
             (loop back)
```

### Consume (Thread-Safe)

```
  +-------------------------+
  |  acquire(mutex)         |
  +----------+--------------+
             |
             v
  +---------------------+
  |  lazy_refill(t_now) |
  +----------+----------+
             |
             v
  +----------------------------+
  |  if tokens >= cost:        |
  |    tokens -= cost          |
  |    release(mutex)          |
  |    return ALLOW            |
  |  else:                     |
  |    release(mutex)          |
  |    return DENY             |
  +----------------------------+
```

---

## 9. Decision Trees

### "Which Rate Limiter Should I Use?"

```
START: What do you need?
|
+-- Do you need BURST tolerance?
|   |
|   +-- YES --> Token Bucket ✓ (allows burst up to capacity)
|   |
|   +-- NO  --> Do you need smooth output?
|               |
|               +-- YES --> Leaky Bucket ✓ (constant output rate)
|               +-- NO  --> Fixed Window Counter (simplest)
|
+-- Do you need precise fairness across time windows?
    |
    +-- YES --> Sliding Window Log or Sliding Window Counter
    +-- NO  --> Token Bucket is usually fine
```

### "What to Do When Request is Denied?"

```
Request DENIED
|
+-- Is this a real-time interactive API?
|   |
|   +-- YES --> Return 429 Too Many Requests
|               Set Retry-After header = wait_time
|
+-- Is this a background batch job?
|   |
|   +-- YES --> Wait (sleep) for wait_time, then retry
|
+-- Is this a streaming service?
    |
    +-- YES --> Queue the request, dequeue when tokens available
                (Leaky Bucket behavior on top of Token Bucket)
```

---

## 10. Token Bucket vs. Other Rate Limiters

### Side-by-Side Comparison

```
ALGORITHM          | Burst | Smooth | Fairness | Complexity | Memory
-------------------|-------|--------|----------|------------|-------
Token Bucket       |  YES  |  ~YES  |  MEDIUM  |   LOW      |  O(1)
Leaky Bucket       |  NO   |  YES   |  HIGH    |   LOW      |  O(1)
Fixed Window       |  YES* |  NO    |  LOW     |   LOWEST   |  O(1)
Sliding Window Log |  NO   |  YES   |  HIGHEST |   HIGH     |  O(N)
Sliding Window Cnt |  NO   |  ~YES  |  HIGH    |   MEDIUM   |  O(1)
```

*Fixed Window allows burst at boundary (double the rate for an instant)

### Token Bucket vs Leaky Bucket

```
TOKEN BUCKET:
  Input:  bursty ──→ [Bucket holds tokens] ──→ Output: bursty but bounded

  t=0: 10 requests → all 10 pass instantly (tokens available)
  Characteristic: ABSORBS bursts

LEAKY BUCKET:
  Input:  bursty ──→ [Queue] ──→ leak at fixed rate ──→ Output: smooth

  t=0: 10 requests → only 1 passes per interval regardless
  Characteristic: SMOOTHS bursts into steady stream
```

### The Boundary Attack on Fixed Window

```
Fixed Window: 100 req per minute

Attacker sends 100 req at 11:59:59
Window resets at 12:00:00
Attacker sends 100 req at 12:00:01

Result: 200 requests in 2 seconds! ← VULNERABILITY

Token Bucket: No such boundary. Tokens are tracked continuously.
```

---

## 11. Implementation in C

### Basic Token Bucket (Single-Threaded)

```c
/*
 * token_bucket.c
 * Single-threaded Token Bucket implementation in C
 *
 * Design:
 *   - Uses lazy refill (no background thread)
 *   - Floating point tokens for sub-second precision
 *   - struct timespec for high-resolution time
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <time.h>
#include <math.h>

/* ─────────────────────────────────────────────
   DATA STRUCTURE
   ──────────────────────────────────────────── */

typedef struct {
    double   capacity;       /* Max tokens the bucket can hold       */
    double   tokens;         /* Current token count (fractional OK)  */
    double   refill_rate;    /* Tokens added per second              */
    struct timespec last_refill; /* Wall-clock time of last refill   */
} TokenBucket;

/* ─────────────────────────────────────────────
   HELPER: Get seconds since epoch as double
   ──────────────────────────────────────────── */

static double now_seconds(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ─────────────────────────────────────────────
   INIT
   ──────────────────────────────────────────── */

/*
 * tb_init: Initialize a token bucket.
 *
 * @capacity    : Max tokens (also the initial fill level)
 * @refill_rate : Tokens per second to add
 *
 * Note: We start FULL (capacity tokens) to allow initial burst.
 *       Some implementations start at 0 — choice depends on use case.
 */
void tb_init(TokenBucket *tb, double capacity, double refill_rate) {
    tb->capacity    = capacity;
    tb->tokens      = capacity;   /* Start full */
    tb->refill_rate = refill_rate;
    clock_gettime(CLOCK_MONOTONIC, &tb->last_refill);
}

/* ─────────────────────────────────────────────
   REFILL (LAZY)
   ──────────────────────────────────────────── */

/*
 * tb_refill: Calculate and apply token accumulation since last call.
 *
 * This is the "lazy refill" technique:
 *   - No background thread required
 *   - Called inside tb_consume before checking token count
 *   - Time delta is computed from wall clock
 *
 * Invariant: tokens is always in [0, capacity]
 */
static void tb_refill(TokenBucket *tb) {
    struct timespec now_ts;
    clock_gettime(CLOCK_MONOTONIC, &now_ts);

    /* Compute elapsed time in seconds (high precision) */
    double now  = (double)now_ts.tv_sec  + (double)now_ts.tv_nsec  * 1e-9;
    double last = (double)tb->last_refill.tv_sec
                + (double)tb->last_refill.tv_nsec * 1e-9;
    double elapsed = now - last;

    if (elapsed > 0.0) {
        double earned = elapsed * tb->refill_rate;
        tb->tokens    = fmin(tb->tokens + earned, tb->capacity);
        tb->last_refill = now_ts;
    }
}

/* ─────────────────────────────────────────────
   CONSUME
   ──────────────────────────────────────────── */

/*
 * tb_consume: Attempt to consume `cost` tokens.
 *
 * Returns: true  if allowed (tokens deducted)
 *          false if denied  (tokens unchanged)
 *
 * @cost: Number of tokens required. Usually 1 for simple requests.
 *        Use >1 for weighted requests (e.g., large uploads).
 */
bool tb_consume(TokenBucket *tb, double cost) {
    tb_refill(tb);   /* Always refill before checking */

    if (tb->tokens >= cost) {
        tb->tokens -= cost;
        return true;   /* ALLOWED */
    }
    return false;      /* DENIED  */
}

/* ─────────────────────────────────────────────
   WAIT TIME QUERY
   ──────────────────────────────────────────── */

/*
 * tb_wait_time: How many seconds until `cost` tokens are available?
 *
 * Returns 0.0 if tokens are already sufficient.
 * Used for Retry-After headers or sleep-and-retry patterns.
 *
 * Formula:
 *   deficit   = cost - current_tokens
 *   wait_time = deficit / refill_rate
 */
double tb_wait_time(TokenBucket *tb, double cost) {
    tb_refill(tb);
    if (tb->tokens >= cost) return 0.0;

    double deficit = cost - tb->tokens;
    return deficit / tb->refill_rate;
}

/* ─────────────────────────────────────────────
   STATUS
   ──────────────────────────────────────────── */

void tb_print_status(const TokenBucket *tb) {
    printf("Bucket Status: tokens=%.2f / %.2f  refill_rate=%.2f/s\n",
           tb->tokens, tb->capacity, tb->refill_rate);
}

/* ─────────────────────────────────────────────
   DEMO / TEST DRIVER
   ──────────────────────────────────────────── */

int main(void) {
    TokenBucket tb;
    tb_init(&tb, /*capacity=*/10.0, /*refill_rate=*/2.0);

    printf("=== Token Bucket Demo ===\n");
    printf("Capacity: 10, Refill Rate: 2/sec\n\n");

    /* Simulate 15 requests immediately (burst test) */
    printf("--- Burst Test: 15 requests immediately ---\n");
    for (int i = 1; i <= 15; i++) {
        bool allowed = tb_consume(&tb, 1.0);
        tb_print_status(&tb);
        printf("Request %2d: %s\n\n", i, allowed ? "ALLOWED ✓" : "DENIED  ✗");
    }

    /* Simulate waiting 3 seconds */
    printf("--- Waiting 3 seconds... ---\n");
    struct timespec sleep_ts = { .tv_sec = 3, .tv_nsec = 0 };
    nanosleep(&sleep_ts, NULL);

    /* After refill, send 5 more */
    printf("\n--- After 3s wait: 5 requests ---\n");
    for (int i = 1; i <= 5; i++) {
        bool allowed = tb_consume(&tb, 1.0);
        tb_print_status(&tb);
        printf("Request %2d: %s\n\n", i, allowed ? "ALLOWED ✓" : "DENIED  ✗");
    }

    /* Weighted request (cost = 3) */
    printf("--- Weighted Request: cost=3 ---\n");
    double wt = tb_wait_time(&tb, 3.0);
    if (wt > 0.0) {
        printf("Need to wait %.2f seconds for 3 tokens\n", wt);
    } else {
        tb_consume(&tb, 3.0);
        printf("Weighted request: ALLOWED\n");
    }

    return 0;
}
```

### Thread-Safe Version with POSIX Mutex (C)

```c
/*
 * token_bucket_mt.c
 * Multi-threaded Token Bucket with POSIX mutex
 *
 * Compile: gcc -o tb_mt token_bucket_mt.c -lpthread -lm
 */

#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <pthread.h>
#include <time.h>
#include <math.h>

typedef struct {
    double           capacity;
    double           tokens;
    double           refill_rate;
    struct timespec  last_refill;
    pthread_mutex_t  mutex;       /* Protects all fields above */
} TokenBucketMT;

/* ── Helpers ── */

static double ts_to_sec(struct timespec ts) {
    return (double)ts.tv_sec + (double)ts.tv_nsec * 1e-9;
}

/* ── Init / Destroy ── */

int tb_mt_init(TokenBucketMT *tb, double capacity, double refill_rate) {
    tb->capacity    = capacity;
    tb->tokens      = capacity;
    tb->refill_rate = refill_rate;
    clock_gettime(CLOCK_MONOTONIC, &tb->last_refill);

    if (pthread_mutex_init(&tb->mutex, NULL) != 0) {
        return -1;   /* mutex init failed */
    }
    return 0;
}

void tb_mt_destroy(TokenBucketMT *tb) {
    pthread_mutex_destroy(&tb->mutex);
}

/* ── Internal Refill (call with lock held) ── */

static void _refill_locked(TokenBucketMT *tb) {
    struct timespec now_ts;
    clock_gettime(CLOCK_MONOTONIC, &now_ts);

    double elapsed = ts_to_sec(now_ts) - ts_to_sec(tb->last_refill);
    if (elapsed > 0.0) {
        tb->tokens = fmin(tb->tokens + elapsed * tb->refill_rate,
                          tb->capacity);
        tb->last_refill = now_ts;
    }
}

/* ── Consume (Thread-Safe) ── */

/*
 * Critical section analysis:
 *
 *   We LOCK → refill → check → consume → UNLOCK
 *   This is an atomic "read-modify-write" operation.
 *
 *   Without the lock, two threads could both see tokens=1,
 *   both think they can consume, and both subtract 1,
 *   leaving tokens=-1 (invariant violated!).
 *
 *   This is a classic TOCTOU (Time-of-Check Time-of-Use) race condition.
 */
bool tb_mt_consume(TokenBucketMT *tb, double cost) {
    pthread_mutex_lock(&tb->mutex);

    _refill_locked(tb);

    bool allowed = (tb->tokens >= cost);
    if (allowed) {
        tb->tokens -= cost;
    }

    pthread_mutex_unlock(&tb->mutex);
    return allowed;
}

double tb_mt_wait_time(TokenBucketMT *tb, double cost) {
    pthread_mutex_lock(&tb->mutex);
    _refill_locked(tb);
    double wait = (tb->tokens >= cost) ? 0.0 : (cost - tb->tokens) / tb->refill_rate;
    pthread_mutex_unlock(&tb->mutex);
    return wait;
}

/* ── Demo: Concurrent Clients ── */

typedef struct {
    TokenBucketMT *tb;
    int            client_id;
    int            num_requests;
} WorkerArgs;

void *worker_thread(void *arg) {
    WorkerArgs *args = (WorkerArgs *)arg;
    int allowed = 0, denied = 0;

    for (int i = 0; i < args->num_requests; i++) {
        if (tb_mt_consume(args->tb, 1.0)) {
            allowed++;
        } else {
            denied++;
        }
    }

    printf("Client %d: allowed=%d  denied=%d\n",
           args->client_id, allowed, denied);
    return NULL;
}

int main(void) {
    TokenBucketMT tb;
    tb_mt_init(&tb, 20.0, 5.0);

    const int NUM_CLIENTS = 4;
    pthread_t threads[NUM_CLIENTS];
    WorkerArgs args[NUM_CLIENTS];

    printf("=== Multi-threaded Token Bucket ===\n");
    printf("Capacity: 20, Refill: 5/s, Clients: %d\n\n", NUM_CLIENTS);

    for (int i = 0; i < NUM_CLIENTS; i++) {
        args[i] = (WorkerArgs){ &tb, i + 1, 10 };
        pthread_create(&threads[i], NULL, worker_thread, &args[i]);
    }

    for (int i = 0; i < NUM_CLIENTS; i++) {
        pthread_join(threads[i], NULL);
    }

    tb_mt_destroy(&tb);
    return 0;
}
```

---

## 12. Implementation in Go

### Basic Token Bucket

```go
// token_bucket.go
// Token Bucket implementation in Go — idiomatic, zero-dependency
//
// Go idioms used:
//   - sync.Mutex for thread safety
//   - time.Now() and time.Duration for precision
//   - Method receivers on struct
//   - Multiple return values for (allowed, waitDuration)

package tokenbucket

import (
	"sync"
	"time"
)

// ─────────────────────────────────────────────
// TokenBucket structure
// ─────────────────────────────────────────────

// TokenBucket implements the token bucket algorithm.
// It is safe for concurrent use.
//
// Fields:
//   capacity    — max tokens the bucket can hold
//   tokens      — current token count (float64 for sub-second precision)
//   refillRate  — tokens per second
//   lastRefill  — wall clock time of last lazy refill
//   mu          — mutex protecting all mutable state
type TokenBucket struct {
	capacity   float64
	tokens     float64
	refillRate float64
	lastRefill time.Time
	mu         sync.Mutex
}

// New creates a new TokenBucket that starts full.
//
// Parameters:
//   capacity   : max tokens (e.g., 100 = burst up to 100 requests)
//   refillRate : tokens per second (e.g., 10 = 10 requests/sec sustained)
//
// Design note: Starting full means the first user gets the benefit of
// burst immediately. Alternatively, start at 0 for "cold start" behavior.
func New(capacity, refillRate float64) *TokenBucket {
	return &TokenBucket{
		capacity:   capacity,
		tokens:     capacity, // start full
		refillRate: refillRate,
		lastRefill: time.Now(),
	}
}

// ─────────────────────────────────────────────
// Refill (internal, call with lock held)
// ─────────────────────────────────────────────

// refill performs lazy token refill based on elapsed time.
//
// Called internally before any consume check.
// MUST be called with tb.mu locked.
//
// Algorithm:
//   elapsed = now - lastRefill
//   earned  = elapsed.Seconds() * refillRate
//   tokens  = min(tokens + earned, capacity)
func (tb *TokenBucket) refill() {
	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()

	if elapsed > 0 {
		earned := elapsed * tb.refillRate
		tb.tokens = min64(tb.tokens+earned, tb.capacity)
		tb.lastRefill = now
	}
}

// ─────────────────────────────────────────────
// Consume
// ─────────────────────────────────────────────

// Allow attempts to consume `cost` tokens from the bucket.
//
// Returns:
//   (true, 0)          — request allowed, no wait needed
//   (false, waitDur)   — request denied, retry after waitDur
//
// Thread-safety: uses mutex lock for atomicity of refill+check+consume.
func (tb *TokenBucket) Allow(cost float64) (bool, time.Duration) {
	tb.mu.Lock()
	defer tb.mu.Unlock()

	tb.refill()

	if tb.tokens >= cost {
		tb.tokens -= cost
		return true, 0
	}

	// Calculate how long until enough tokens accumulate
	deficit  := cost - tb.tokens
	waitSecs := deficit / tb.refillRate
	waitDur  := time.Duration(waitSecs * float64(time.Second))

	return false, waitDur
}

// AllowN is syntactic sugar: consume exactly N tokens.
// Equivalent to Allow(float64(n)).
func (tb *TokenBucket) AllowN(n int) (bool, time.Duration) {
	return tb.Allow(float64(n))
}

// AllowOne consumes 1 token. Most common case.
func (tb *TokenBucket) AllowOne() bool {
	ok, _ := tb.Allow(1)
	return ok
}

// ─────────────────────────────────────────────
// Blocking Wait
// ─────────────────────────────────────────────

// Wait blocks until `cost` tokens are available, then consumes them.
//
// Use case: background workers that should throttle, not fail.
//
// Warning: This holds no lock while sleeping, which is correct.
// After waking, it re-acquires the lock and re-checks.
// This avoids priority inversion and thundering herd.
func (tb *TokenBucket) Wait(cost float64) {
	for {
		ok, wait := tb.Allow(cost)
		if ok {
			return
		}
		time.Sleep(wait)
		// Re-loop and re-check — another goroutine might have consumed
		// tokens while we slept (no guarantee of success after wake)
	}
}

// ─────────────────────────────────────────────
// Inspection
// ─────────────────────────────────────────────

// Tokens returns the current token count (approximation — may be stale).
// This is a non-modifying snapshot.
func (tb *TokenBucket) Tokens() float64 {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	tb.refill()
	return tb.tokens
}

// Capacity returns the bucket's max capacity.
func (tb *TokenBucket) Capacity() float64 {
	return tb.capacity // immutable after construction
}

// ─────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────

func min64(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}
```

### Usage Example & HTTP Middleware

```go
// main.go — demonstrates token bucket + HTTP middleware

package main

import (
	"fmt"
	"net/http"
	"sync"
	"time"

	tb "path/to/tokenbucket"
)

// ─────────────────────────────────────────────
// Basic Usage
// ─────────────────────────────────────────────

func basicDemo() {
	bucket := tb.New(10, 2) // capacity=10, 2 tokens/sec

	fmt.Println("=== Basic Token Bucket Demo ===")
	fmt.Printf("Capacity: 10, Refill: 2/s\n\n")

	// Burst test
	for i := 1; i <= 15; i++ {
		allowed, wait := bucket.Allow(1)
		if allowed {
			fmt.Printf("Request %2d: ALLOWED  (tokens: %.2f)\n", i, bucket.Tokens())
		} else {
			fmt.Printf("Request %2d: DENIED   (retry in %v)\n", i, wait.Round(time.Millisecond))
		}
	}
}

// ─────────────────────────────────────────────
// Per-IP Rate Limiter
// ─────────────────────────────────────────────

// RateLimiter manages per-client token buckets.
//
// Design:
//   - One bucket per IP address
//   - Lazily created on first request from that IP
//   - Protected by RWMutex (multiple readers OK, one writer)
type RateLimiter struct {
	buckets map[string]*tb.TokenBucket
	mu      sync.RWMutex

	capacity   float64
	refillRate float64
}

func NewRateLimiter(capacity, refillRate float64) *RateLimiter {
	return &RateLimiter{
		buckets:    make(map[string]*tb.TokenBucket),
		capacity:   capacity,
		refillRate: refillRate,
	}
}

// getBucket returns (creating if necessary) the bucket for a given key.
//
// Two-phase locking pattern:
//   1. Try RLock first (fast path if bucket exists)
//   2. If not found, upgrade to full Lock and create
func (rl *RateLimiter) getBucket(key string) *tb.TokenBucket {
	// Fast path: bucket already exists
	rl.mu.RLock()
	if b, ok := rl.buckets[key]; ok {
		rl.mu.RUnlock()
		return b
	}
	rl.mu.RUnlock()

	// Slow path: create new bucket (write lock)
	rl.mu.Lock()
	defer rl.mu.Unlock()

	// Double-check: another goroutine may have created it
	if b, ok := rl.buckets[key]; ok {
		return b
	}

	b := tb.New(rl.capacity, rl.refillRate)
	rl.buckets[key] = b
	return b
}

func (rl *RateLimiter) Allow(key string) bool {
	return rl.getBucket(key).AllowOne()
}

// ─────────────────────────────────────────────
// HTTP Middleware
// ─────────────────────────────────────────────

// RateLimitMiddleware wraps an http.Handler with per-IP rate limiting.
//
// On deny: responds with HTTP 429 Too Many Requests
//          sets Retry-After header
func RateLimitMiddleware(rl *RateLimiter, next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		ip := r.RemoteAddr

		bucket := rl.getBucket(ip)
		allowed, wait := bucket.Allow(1)

		if !allowed {
			// Set standard Retry-After header (seconds as integer)
			retrySecs := int(wait.Seconds()) + 1
			w.Header().Set("Retry-After", fmt.Sprintf("%d", retrySecs))
			w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%.0f", rl.capacity))
			w.Header().Set("X-RateLimit-Remaining", "0")

			http.Error(w, "429 Too Many Requests", http.StatusTooManyRequests)
			return
		}

		// Pass through with rate-limit info headers
		remaining := bucket.Tokens()
		w.Header().Set("X-RateLimit-Limit", fmt.Sprintf("%.0f", rl.capacity))
		w.Header().Set("X-RateLimit-Remaining", fmt.Sprintf("%.0f", remaining))

		next.ServeHTTP(w, r)
	})
}

func main() {
	basicDemo()

	// HTTP server with rate limiting
	rl := NewRateLimiter(10, 2) // 10 burst, 2/sec sustained per IP

	mux := http.NewServeMux()
	mux.HandleFunc("/api/data", func(w http.ResponseWriter, r *http.Request) {
		fmt.Fprintln(w, `{"status":"ok"}`)
	})

	handler := RateLimitMiddleware(rl, mux)
	fmt.Println("\nServer starting on :8080")
	http.ListenAndServe(":8080", handler)
}
```

### Concurrent Test

```go
// token_bucket_test.go

package tokenbucket_test

import (
	"sync"
	"testing"
	"time"

	tb "path/to/tokenbucket"
)

// TestBurst verifies that a full bucket allows exactly `capacity` requests.
func TestBurst(t *testing.T) {
	bucket := tb.New(10, 1) // capacity 10, slow refill

	allowed := 0
	for i := 0; i < 20; i++ {
		if bucket.AllowOne() {
			allowed++
		}
	}

	if allowed != 10 {
		t.Errorf("Expected 10 allowed in burst, got %d", allowed)
	}
}

// TestRefill verifies that tokens refill over time.
func TestRefill(t *testing.T) {
	bucket := tb.New(10, 10) // 10 tokens/sec

	// Drain completely
	for i := 0; i < 10; i++ {
		bucket.AllowOne()
	}

	if bucket.AllowOne() {
		t.Fatal("Bucket should be empty after draining")
	}

	time.Sleep(200 * time.Millisecond) // should earn ~2 tokens

	if !bucket.AllowOne() {
		t.Fatal("Expected token after 200ms refill at 10/sec")
	}
}

// TestConcurrency checks no race conditions with -race flag.
func TestConcurrency(t *testing.T) {
	bucket := tb.New(100, 50)

	var wg sync.WaitGroup
	for i := 0; i < 1000; i++ {
		wg.Add(1)
		go func() {
			defer wg.Done()
			bucket.AllowOne()
		}()
	}
	wg.Wait()

	// Tokens should still be in valid range
	tokens := bucket.Tokens()
	if tokens < 0 || tokens > 100 {
		t.Errorf("Token count %.2f out of valid range [0, 100]", tokens)
	}
}
```

---

## 13. Implementation in Rust

### Core Library (No External Dependencies)

```rust
//! token_bucket.rs
//! 
//! A precise, thread-safe Token Bucket implementation in Rust.
//!
//! Design philosophy:
//!   - Zero unsafe code
//!   - Arc<Mutex<_>> for shared ownership across threads
//!   - std::time::Instant for monotonic, high-precision time
//!   - f64 tokens for sub-second fractional accumulation
//!   - Builder pattern for ergonomic construction
//!
//! Rust-specific notes:
//!   - We use `Instant` (monotonic) NOT `SystemTime` (wall clock)
//!     Monotonic clocks never go backward — critical for rate limiting
//!   - `Mutex<TokenBucketInner>` separates the public API from the
//!     locked mutable state (interior mutability pattern)

use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

// ─────────────────────────────────────────────
// Inner state (held behind Mutex)
// ─────────────────────────────────────────────

/// Inner mutable state of the token bucket.
/// This struct is intentionally private — accessed only through the lock.
#[derive(Debug)]
struct TokenBucketInner {
    /// Maximum tokens the bucket can hold (burst limit)
    capacity: f64,
    /// Current token level
    tokens: f64,
    /// Tokens added per second
    refill_rate: f64,
    /// When the last refill calculation was performed
    last_refill: Instant,
}

impl TokenBucketInner {
    /// Perform lazy refill based on elapsed time.
    ///
    /// This is called on every consume/check operation.
    /// The key insight: we don't need a background task.
    /// Time is continuous — we compute what WOULD have accumulated.
    fn refill(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();

        if elapsed > 0.0 {
            let earned = elapsed * self.refill_rate;
            // f64::min keeps us within capacity
            self.tokens = (self.tokens + earned).min(self.capacity);
            self.last_refill = now;
        }
    }
}

// ─────────────────────────────────────────────
// Public API
// ─────────────────────────────────────────────

/// A thread-safe token bucket rate limiter.
///
/// Can be cloned cheaply (Arc-based) to share across threads:
/// ```rust
/// let limiter = TokenBucket::new(10.0, 2.0);
/// let limiter2 = limiter.clone(); // shared, not copied
/// ```
#[derive(Clone, Debug)]
pub struct TokenBucket {
    inner: Arc<Mutex<TokenBucketInner>>,
}

/// Result of a consume attempt
#[derive(Debug, PartialEq)]
pub enum ConsumeResult {
    /// Request is allowed. Tokens have been deducted.
    Allowed,
    /// Request is denied. Contains how long to wait before retrying.
    Denied { wait: Duration },
}

impl TokenBucket {
    /// Create a new token bucket, starting at full capacity.
    ///
    /// # Arguments
    /// * `capacity`    — maximum tokens (burst size)
    /// * `refill_rate` — tokens per second (sustained rate)
    ///
    /// # Panics
    /// Panics if capacity <= 0 or refill_rate <= 0.
    pub fn new(capacity: f64, refill_rate: f64) -> Self {
        assert!(capacity > 0.0, "capacity must be positive");
        assert!(refill_rate > 0.0, "refill_rate must be positive");

        TokenBucket {
            inner: Arc::new(Mutex::new(TokenBucketInner {
                capacity,
                tokens: capacity, // start full
                refill_rate,
                last_refill: Instant::now(),
            })),
        }
    }

    /// Attempt to consume `cost` tokens.
    ///
    /// This is the core operation. Thread-safe: uses mutex internally.
    ///
    /// # Returns
    /// - `ConsumeResult::Allowed`       if cost ≤ available tokens
    /// - `ConsumeResult::Denied{wait}`  otherwise, with retry duration
    ///
    /// # Panics
    /// Panics if the mutex is poisoned (another thread panicked holding it).
    pub fn try_consume(&self, cost: f64) -> ConsumeResult {
        let mut inner = self.inner.lock().expect("mutex poisoned");
        inner.refill();

        if inner.tokens >= cost {
            inner.tokens -= cost;
            ConsumeResult::Allowed
        } else {
            let deficit = cost - inner.tokens;
            let wait_secs = deficit / inner.refill_rate;
            let wait = Duration::from_secs_f64(wait_secs);
            ConsumeResult::Denied { wait }
        }
    }

    /// Consume exactly 1 token. Returns `true` if allowed.
    ///
    /// This is the most common operation and the most ergonomic API.
    pub fn allow(&self) -> bool {
        self.try_consume(1.0) == ConsumeResult::Allowed
    }

    /// Block the current thread until `cost` tokens are available.
    ///
    /// Uses spin-wait with sleep. Appropriate for background tasks.
    ///
    /// Warning: Do NOT call from async contexts — use async variant instead.
    pub fn wait_and_consume(&self, cost: f64) {
        loop {
            match self.try_consume(cost) {
                ConsumeResult::Allowed => return,
                ConsumeResult::Denied { wait } => {
                    std::thread::sleep(wait);
                    // Re-check: another thread may have consumed tokens
                }
            }
        }
    }

    /// Return current token count (snapshot — may be immediately stale).
    pub fn tokens(&self) -> f64 {
        let mut inner = self.inner.lock().expect("mutex poisoned");
        inner.refill();
        inner.tokens
    }

    /// Return the bucket's maximum capacity.
    pub fn capacity(&self) -> f64 {
        self.inner.lock().expect("mutex poisoned").capacity
    }
}

// ─────────────────────────────────────────────
// Builder Pattern
// ─────────────────────────────────────────────

/// Ergonomic builder for TokenBucket with named parameters.
///
/// # Example
/// ```rust
/// let bucket = TokenBucketBuilder::new()
///     .capacity(100.0)
///     .refill_rate(10.0)
///     .initial_tokens(0.0)  // cold start
///     .build();
/// ```
pub struct TokenBucketBuilder {
    capacity: f64,
    refill_rate: f64,
    initial_tokens: Option<f64>,
}

impl TokenBucketBuilder {
    pub fn new() -> Self {
        TokenBucketBuilder {
            capacity: 10.0,
            refill_rate: 1.0,
            initial_tokens: None,
        }
    }

    pub fn capacity(mut self, c: f64) -> Self {
        self.capacity = c;
        self
    }

    pub fn refill_rate(mut self, r: f64) -> Self {
        self.refill_rate = r;
        self
    }

    /// Override initial token count.
    /// Default: starts full (= capacity).
    pub fn initial_tokens(mut self, t: f64) -> Self {
        self.initial_tokens = Some(t);
        self
    }

    pub fn build(self) -> TokenBucket {
        let init = self.initial_tokens.unwrap_or(self.capacity);
        TokenBucket {
            inner: Arc::new(Mutex::new(TokenBucketInner {
                capacity: self.capacity,
                tokens: init.min(self.capacity),
                refill_rate: self.refill_rate,
                last_refill: Instant::now(),
            })),
        }
    }
}

// ─────────────────────────────────────────────
// Per-Key Rate Limiter (HashMap-backed)
// ─────────────────────────────────────────────

use std::collections::HashMap;

/// Manages one TokenBucket per unique string key (e.g., user ID, IP).
///
/// Buckets are lazily created on first access.
pub struct KeyedRateLimiter {
    buckets: Mutex<HashMap<String, TokenBucket>>,
    capacity: f64,
    refill_rate: f64,
}

impl KeyedRateLimiter {
    pub fn new(capacity: f64, refill_rate: f64) -> Self {
        KeyedRateLimiter {
            buckets: Mutex::new(HashMap::new()),
            capacity,
            refill_rate,
        }
    }

    /// Attempt to allow one request for `key`.
    pub fn allow(&self, key: &str) -> bool {
        let mut map = self.buckets.lock().expect("mutex poisoned");
        let bucket = map
            .entry(key.to_string())
            .or_insert_with(|| TokenBucket::new(self.capacity, self.refill_rate));
        bucket.allow()
    }

    /// Get wait time for `key` to get `cost` tokens.
    pub fn wait_time(&self, key: &str, cost: f64) -> Option<Duration> {
        let mut map = self.buckets.lock().expect("mutex poisoned");
        let bucket = map
            .entry(key.to_string())
            .or_insert_with(|| TokenBucket::new(self.capacity, self.refill_rate));
        match bucket.try_consume(cost) {
            ConsumeResult::Allowed => None,
            ConsumeResult::Denied { wait } => Some(wait),
        }
    }
}

// ─────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;

    #[test]
    fn test_burst_limited_by_capacity() {
        let bucket = TokenBucket::new(5.0, 1.0);
        let mut allowed = 0;

        for _ in 0..10 {
            if bucket.allow() {
                allowed += 1;
            }
        }
        assert_eq!(allowed, 5, "Should allow exactly capacity (5) in burst");
    }

    #[test]
    fn test_refill_over_time() {
        let bucket = TokenBucket::new(10.0, 10.0); // 10/sec
        // Drain completely
        for _ in 0..10 { bucket.allow(); }
        assert!(!bucket.allow(), "Should be empty");

        thread::sleep(Duration::from_millis(150)); // ~1.5 tokens at 10/sec

        assert!(bucket.allow(), "Should have at least 1 token after 150ms");
    }

    #[test]
    fn test_wait_time_calculation() {
        let bucket = TokenBucket::new(5.0, 2.0); // 2 tokens/sec
        for _ in 0..5 { bucket.allow(); } // drain

        match bucket.try_consume(4.0) {
            ConsumeResult::Denied { wait } => {
                // Need 4 tokens, have 0, rate=2/sec → wait = 2.0s
                let secs = wait.as_secs_f64();
                assert!(
                    (secs - 2.0).abs() < 0.05,
                    "Wait time should be ~2s, got {}s",
                    secs
                );
            }
            ConsumeResult::Allowed => panic!("Should have been denied"),
        }
    }

    #[test]
    fn test_concurrent_no_overdraft() {
        let bucket = Arc::new(TokenBucket::new(100.0, 50.0));
        let mut handles = vec![];

        for _ in 0..20 {
            let b = bucket.clone();
            handles.push(thread::spawn(move || {
                for _ in 0..10 {
                    b.allow();
                }
            }));
        }

        for h in handles { h.join().unwrap(); }

        // Tokens should never go negative (invariant check)
        assert!(
            bucket.tokens() >= 0.0,
            "Token count must never be negative"
        );
    }

    #[test]
    fn test_clone_shares_state() {
        let b1 = TokenBucket::new(5.0, 1.0);
        let b2 = b1.clone(); // Same underlying bucket!

        for _ in 0..5 { b1.allow(); } // drain via b1
        assert!(!b2.allow(), "b2 shares state with b1, should be empty");
    }

    #[test]
    fn test_builder() {
        let bucket = TokenBucketBuilder::new()
            .capacity(20.0)
            .refill_rate(5.0)
            .initial_tokens(0.0) // cold start
            .build();

        // Should start with 0 tokens (cold start)
        assert!(!bucket.allow(), "Cold start bucket should be empty initially");
    }
}
```

### Async Token Bucket (Tokio)

```rust
//! async_token_bucket.rs
//! 
//! Async-aware Token Bucket using Tokio.
//!
//! Key difference from sync version:
//!   - tokio::sync::Mutex instead of std::sync::Mutex
//!   - tokio::time::sleep instead of thread::sleep
//!   - async fn signatures

use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::sync::Mutex;

struct Inner {
    capacity: f64,
    tokens: f64,
    refill_rate: f64,
    last_refill: Instant,
}

impl Inner {
    fn refill(&mut self) {
        let now = Instant::now();
        let elapsed = now.duration_since(self.last_refill).as_secs_f64();
        if elapsed > 0.0 {
            self.tokens = (self.tokens + elapsed * self.refill_rate).min(self.capacity);
            self.last_refill = now;
        }
    }
}

#[derive(Clone)]
pub struct AsyncTokenBucket {
    inner: Arc<Mutex<Inner>>,
}

impl AsyncTokenBucket {
    pub fn new(capacity: f64, refill_rate: f64) -> Self {
        AsyncTokenBucket {
            inner: Arc::new(Mutex::new(Inner {
                capacity,
                tokens: capacity,
                refill_rate,
                last_refill: Instant::now(),
            })),
        }
    }

    /// Non-blocking attempt to consume tokens.
    pub async fn try_consume(&self, cost: f64) -> Option<Duration> {
        let mut inner = self.inner.lock().await;
        inner.refill();

        if inner.tokens >= cost {
            inner.tokens -= cost;
            None // allowed, no wait
        } else {
            let deficit = cost - inner.tokens;
            Some(Duration::from_secs_f64(deficit / inner.refill_rate))
        }
    }

    /// Async-blocking wait until tokens available.
    ///
    /// Unlike thread::sleep, this yields to the async runtime,
    /// allowing other tasks to run while waiting.
    pub async fn wait_and_consume(&self, cost: f64) {
        loop {
            match self.try_consume(cost).await {
                None => return,
                Some(wait) => tokio::time::sleep(wait).await,
            }
        }
    }
}

// ─────────────────────────────────────────────
// Usage with Axum HTTP framework (example)
// ─────────────────────────────────────────────

/*
use axum::{extract::State, http::StatusCode, response::IntoResponse};

pub async fn rate_limited_handler(
    State(limiter): State<AsyncTokenBucket>,
) -> impl IntoResponse {
    match limiter.try_consume(1.0).await {
        None => (StatusCode::OK, "Request processed"),
        Some(wait) => {
            let secs = wait.as_secs() + 1;
            (
                StatusCode::TOO_MANY_REQUESTS,
                format!("Rate limited. Retry after {}s", secs),
            )
        }
    }
}
*/
```

---

## 14. Thread-Safe / Concurrent Implementations

### The Race Condition Problem

Without synchronization, two threads can corrupt the bucket:

```
Thread 1: reads tokens = 1
Thread 2: reads tokens = 1
Thread 1: 1 >= 1 → TRUE → tokens = 0
Thread 2: 1 >= 1 → TRUE → tokens = 0
                              ↑
               Both allowed! But only 1 token existed.
               Invariant violated: effectively served 2 requests for 1 token.
```

This is a **TOCTOU (Time-of-Check Time-of-Use)** race.

### Synchronization Strategies Compared

```
STRATEGY          | Language  | Notes
------------------|-----------|-----------------------------------------------
Mutex (std)       | C/Rust/Go | Simple, correct, small critical section
RWMutex           | Go/Rust   | reads don't need write lock (read-heavy)
Atomic CAS loop   | All       | Lock-free but complex; suitable for integers
Channel-based     | Go        | Single goroutine owns state, others send msgs
Actor model       | Rust      | Tokio actors — messages rather than shared mem
```

### Lock-Free Token Bucket (Atomic CAS Approach)

For integer tokens (no fractional), atomic compare-and-swap:

```c
// lock_free_tb.c (C11 atomics)
#include <stdatomic.h>
#include <stdbool.h>
#include <time.h>

typedef struct {
    atomic_long tokens;     /* integer tokens for atomicity */
    long        capacity;
    long        refill_rate;/* tokens per second */
    atomic_long last_refill_ns; /* nanoseconds since epoch */
} LockFreeTokenBucket;

static long get_ns(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec * 1000000000L + ts.tv_nsec;
}

bool lf_consume(LockFreeTokenBucket *tb) {
    /* Lazy refill using CAS on last_refill_ns */
    long old_ns = atomic_load(&tb->last_refill_ns);
    long now_ns = get_ns();
    long elapsed_ns = now_ns - old_ns;
    long earned = (elapsed_ns * tb->refill_rate) / 1000000000L;

    if (earned > 0) {
        /* CAS: update last_refill only if it hasn't changed */
        if (atomic_compare_exchange_strong(&tb->last_refill_ns, &old_ns, now_ns)) {
            long cur = atomic_load(&tb->tokens);
            long capped = cur + earned;
            if (capped > tb->capacity) capped = tb->capacity;
            atomic_store(&tb->tokens, capped);
        }
        /* If CAS failed, another thread updated — that's OK, tokens already updated */
    }

    /* Consume: decrement if > 0 using CAS loop */
    long cur;
    do {
        cur = atomic_load(&tb->tokens);
        if (cur <= 0) return false;
    } while (!atomic_compare_exchange_weak(&tb->tokens, &cur, cur - 1));

    return true;
}
```

### Go Channel-Based (Actor Model)

```go
// actor_bucket.go — Single goroutine owns all state
// Other goroutines communicate via channels
// This eliminates all locking — ownership is transferred, not shared

package tokenbucket

import "time"

type request struct {
    cost     float64
    response chan bool
}

type ActorBucket struct {
    requests chan request
}

func NewActor(capacity, refillRate float64) *ActorBucket {
    ab := &ActorBucket{
        requests: make(chan request, 256), // buffered to reduce blocking
    }
    go ab.run(capacity, refillRate)
    return ab
}

// run is the single goroutine that owns token state.
// No locks needed — only this goroutine touches tokens/lastRefill.
func (ab *ActorBucket) run(capacity, refillRate float64) {
    tokens := capacity
    lastRefill := time.Now()

    for req := range ab.requests {
        // Lazy refill
        now := time.Now()
        elapsed := now.Sub(lastRefill).Seconds()
        tokens = min64(tokens+elapsed*refillRate, capacity)
        lastRefill = now

        // Serve request
        if tokens >= req.cost {
            tokens -= req.cost
            req.response <- true
        } else {
            req.response <- false
        }
    }
}

func (ab *ActorBucket) Allow(cost float64) bool {
    resp := make(chan bool, 1)
    ab.requests <- request{cost: cost, response: resp}
    return <-resp
}
```

---

## 15. Distributed Token Bucket

### The Problem: Multiple Servers

```
                ┌─────────────┐
USER ──→ LB ──→ │   Server 1  │ ← has its own in-memory bucket
                │   Server 2  │ ← has its OWN in-memory bucket
                │   Server 3  │ ← has its OWN in-memory bucket
                └─────────────┘

Problem: User sends 30 requests.
  Server 1 sees 10 → allows (bucket has 20 tokens)
  Server 2 sees 10 → allows (bucket has 20 tokens)
  Server 3 sees 10 → allows (bucket has 20 tokens)
  Total: 30 requests allowed, limit should be 20!
```

### Solution: Centralized Token Store (Redis)

```
USER ──→ Server 1 ──→ Redis (shared token bucket) ──→ ALLOW/DENY
USER ──→ Server 2 ──→ Redis (shared token bucket) ──→ ALLOW/DENY
USER ──→ Server 3 ──→ Redis (shared token bucket) ──→ ALLOW/DENY
         ↑
         All servers query same Redis instance
```

### Redis Lua Script (Atomic Token Bucket)

```lua
-- token_bucket.lua
-- Executed as a Redis EVAL command (atomic — no race conditions in Redis)
--
-- KEYS[1]        = bucket key (e.g., "ratelimit:user:42")
-- ARGV[1]        = capacity (max tokens)
-- ARGV[2]        = refill_rate (tokens per second)
-- ARGV[3]        = cost (tokens needed for this request)
-- ARGV[4]        = current Unix timestamp (fractional seconds)
--
-- Returns: {allowed (0/1), current_tokens, wait_seconds}

local key         = KEYS[1]
local capacity    = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local cost        = tonumber(ARGV[3])
local now         = tonumber(ARGV[4])

-- Load existing state (or initialize)
local data        = redis.call("HMGET", key, "tokens", "last_refill")
local tokens      = tonumber(data[1]) or capacity
local last_refill = tonumber(data[2]) or now

-- Lazy refill
local elapsed = math.max(0, now - last_refill)
local earned  = elapsed * refill_rate
tokens        = math.min(tokens + earned, capacity)

-- Consume
local allowed = 0
local wait    = 0.0

if tokens >= cost then
    tokens  = tokens - cost
    allowed = 1
else
    local deficit = cost - tokens
    wait = deficit / refill_rate
end

-- Persist state with TTL (expire after 2× full refill time to save memory)
local ttl = math.ceil(capacity / refill_rate * 2)
redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
redis.call("EXPIRE", key, ttl)

return {allowed, tokens, wait}
```

### Go Client Using Redis Lua Script

```go
// redis_rate_limiter.go

package ratelimit

import (
    "context"
    "fmt"
    "time"

    "github.com/redis/go-redis/v9"
)

const luaScript = `
local key         = KEYS[1]
local capacity    = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local cost        = tonumber(ARGV[3])
local now         = tonumber(ARGV[4])

local data        = redis.call("HMGET", key, "tokens", "last_refill")
local tokens      = tonumber(data[1]) or capacity
local last_refill = tonumber(data[2]) or now

local elapsed = math.max(0, now - last_refill)
tokens        = math.min(tokens + elapsed * refill_rate, capacity)

local allowed, wait = 0, 0
if tokens >= cost then
    tokens  = tokens - cost
    allowed = 1
else
    wait = (cost - tokens) / refill_rate
end

local ttl = math.ceil(capacity / refill_rate * 2)
redis.call("HMSET", key, "tokens", tokens, "last_refill", now)
redis.call("EXPIRE", key, ttl)
return {allowed, tokens, wait}
`

type RedisRateLimiter struct {
    rdb        *redis.Client
    capacity   float64
    refillRate float64
    script     *redis.Script
}

func NewRedisRateLimiter(rdb *redis.Client, capacity, refillRate float64) *RedisRateLimiter {
    return &RedisRateLimiter{
        rdb:        rdb,
        capacity:   capacity,
        refillRate: refillRate,
        script:     redis.NewScript(luaScript),
    }
}

func (r *RedisRateLimiter) Allow(ctx context.Context, key string, cost float64) (bool, time.Duration, error) {
    now := float64(time.Now().UnixNano()) / 1e9

    result, err := r.script.Run(ctx, r.rdb,
        []string{fmt.Sprintf("ratelimit:%s", key)},
        r.capacity, r.refillRate, cost, now,
    ).Slice()

    if err != nil {
        return false, 0, err
    }

    allowed := result[0].(int64) == 1
    waitSecs := result[2].(float64)
    wait := time.Duration(waitSecs * float64(time.Second))

    return allowed, wait, nil
}
```

---

## 16. Edge Cases & Pitfalls

### Pitfall 1: Clock Drift / Non-Monotonic Time

```
WRONG:
  Use wall clock (time.Now() / SystemTime)
  → System clock can go BACKWARD (NTP sync, leap seconds)
  → elapsed < 0 → earned < 0 → tokens DECREASE on refill!

CORRECT:
  Use monotonic clock:
  - C:    CLOCK_MONOTONIC
  - Go:   time.Now() (Go's time.Now() is monotonic-aware)
  - Rust: std::time::Instant (always monotonic)
```

### Pitfall 2: Thundering Herd After Wait

```
SCENARIO:
  Bucket empty. 1000 goroutines all call Wait().
  All compute wait_time = 1s.
  All sleep 1s.
  All wake simultaneously.
  All try to consume 1 token.
  Only 2 tokens refilled in 1s!

SOLUTION:
  After waking from sleep, RE-CHECK and RE-TRY in a loop.
  Do NOT assume tokens will be there after sleep.
  
  // Correct pattern:
  loop {
    ok, wait = try_consume(1)
    if ok { break }
    sleep(wait)
    // Re-try — someone else may have taken the token
  }
```

### Pitfall 3: Integer Overflow in Token Arithmetic

```
Scenario:
  Server was down for 1 week (604800 seconds).
  Refill rate = 1,000,000 tokens/sec.
  Earned = 604800 × 1,000,000 = 604,800,000,000 tokens

Without capacity cap:
  tokens = HUGE number → integer overflow → negative tokens

CORRECT:
  tokens = min(tokens + earned, capacity)
  Always cap at capacity BEFORE storing.
```

### Pitfall 4: Floating Point Precision

```
Over millions of operations, f64 errors accumulate.

Example:
  tokens += 0.1 (ten times) ≠ exactly 1.0 in floating point

For high-precision applications:
  - Use integer milliseconds instead of f64 seconds
  - Scale: store tokens as microtokens (×1,000,000)
  - This converts float ops to integer ops
```

### Pitfall 5: Very High Refill Rate

```
If refill_rate = 1,000,000 tokens/sec and the bucket is checked
every millisecond:

  elapsed = 0.001s
  earned  = 1000 tokens per check

This is fine mathematically but:
  - If elapsed has any jitter, tokens can temporarily dip
  - Use a minimum elapsed threshold to avoid sub-microsecond checks

if elapsed < 1e-9 { return; } // ignore sub-nanosecond intervals
```

### Pitfall 6: Mutex Contention at Scale

```
High-traffic scenario: 100,000 requests/sec to one bucket

All threads must serialize through the mutex:
  → Heavy lock contention
  → Performance bottleneck
  
SOLUTIONS:
  1. Shard the bucket (N sub-buckets, each with capacity/N and rate/N)
  2. Use per-thread local buckets with periodic sync to global
  3. Use atomic CAS loop (lock-free)
  4. Use actor model (single owner goroutine)
```

---

## 17. Time & Space Complexity Analysis

### Per-Operation Complexity

| Operation    | Time   | Space | Notes                             |
|--------------|--------|-------|-----------------------------------|
| `new()`      | O(1)   | O(1)  | Simple struct allocation          |
| `refill()`   | O(1)   | O(1)  | One clock read + arithmetic       |
| `consume()`  | O(1)   | O(1)  | Refill + comparison + decrement   |
| `wait_time()`| O(1)   | O(1)  | One division                      |

The token bucket is essentially **O(1) time and O(1) space** per operation. This is its greatest strength.

Compare with:
- **Sliding Window Log**: O(N) time and O(N) space (N = requests in window)
- **Fixed Window Counter**: O(1) time and O(1) space (no burst control)

### Memory for Keyed (Per-User) Rate Limiter

```
N = number of active users
Memory = N × sizeof(TokenBucket)

sizeof(TokenBucket) ≈ 40-64 bytes (capacity + tokens + rate + timestamp + mutex)

Example:
  1,000,000 users × 64 bytes = 64 MB   — totally manageable
```

### Throughput Under Contention

```
Single mutex token bucket under high concurrency:
  - Throughput limited by mutex contention (serialization)
  - Typical: ~5-20M operations/sec on modern hardware

Lock-free (atomic CAS):
  - Better under moderate contention
  - Degrades with high contention (CAS retries)
  - Typical: ~30-100M operations/sec

Sharded (N buckets):
  - Linear scale-up with N shards
  - N=8 shards → ~8× throughput of single mutex
```

---

## 18. Real-World Applications

### 1. API Gateway Rate Limiting
```
AWS API Gateway, Nginx, Kong — all use token bucket variants.

Config example (Nginx):
  limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
  limit_req zone=api burst=20 nodelay;
  # burst=20 → bucket capacity
  # rate=10r/s → refill rate
```

### 2. TCP/IP Network Traffic Shaping
```
Linux traffic control (tc) uses token bucket filter (TBF):
  tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms

This ensures:
  - Sustained bandwidth ≤ 1 Mbit/s
  - Burst up to 32 KB
  - Max packet queuing delay ≤ 400ms
```

### 3. Database Connection Pool Throttling
```
Each connection request costs N tokens based on query complexity.
Complex queries (joins, aggregations) cost more tokens.
This prevents expensive queries from dominating the pool.
```

### 4. Retry Mechanisms with Backoff
```
Service A calls Service B.
Service B rate limits with token bucket.
On 429, Service A reads Retry-After and waits.
This prevents retry storms (thundering herd).
```

### 5. Cryptocurrency Transaction Rate Limiting
```
Blockchain nodes limit transaction broadcast rate per peer.
Token bucket prevents spam transactions from flooding the mempool.
```

### 6. Operating System Disk I/O Throttling
```
Linux cgroups blkio throttling uses token bucket:
  echo "8:0 1048576" > /sys/fs/cgroup/blkio/.../blkio.throttle.read_bps_device
```

---

## 19. Testing Strategies

### Test Dimensions

```
1. UNIT TESTS
   ├── Burst limit (consume exactly capacity tokens immediately)
   ├── Refill over time (sleep and verify tokens increase)
   ├── Wait time accuracy (mathematical formula check)
   ├── Capacity cap (never exceed capacity)
   ├── Empty bucket behavior (deny with correct wait)
   └── Weighted cost (cost > 1)

2. CONCURRENCY TESTS (with race detector)
   ├── No overdraft (tokens never negative)
   ├── No lost updates (all operations atomic)
   ├── Correct total allowed count
   └── High contention (1000 goroutines, 1 token)

3. TIME-BASED TESTS
   ├── Clock monotonicity (tokens never decrease on refill)
   ├── Long idle (large elapsed time, tokens cap at capacity)
   └── Sub-millisecond (fractional token accumulation)

4. PROPERTY-BASED TESTS (fuzzing)
   ├── Invariant: 0 ≤ tokens ≤ capacity always
   ├── Invariant: allowed count ≤ capacity + elapsed × rate
   └── Invariant: denied always returns wait > 0
```

### Deterministic Testing (Mock Clock)

Real token buckets depend on wall time, making tests flaky. Use a mock clock:

```go
// mock_clock.go — inject fake time for deterministic tests

type Clock interface {
    Now() time.Time
}

type RealClock struct{}
func (RealClock) Now() time.Time { return time.Now() }

type MockClock struct {
    current time.Time
}
func (mc *MockClock) Now() time.Time { return mc.current }
func (mc *MockClock) Advance(d time.Duration) { mc.current = mc.current.Add(d) }

// TokenBucket accepts a Clock interface:
type TokenBucket struct {
    // ... other fields
    clock Clock // inject real or mock
}

// In tests:
func TestRefillExact(t *testing.T) {
    mc := &MockClock{current: time.Unix(1000, 0)}
    bucket := NewWithClock(10, 5, mc) // capacity=10, rate=5/s

    for i := 0; i < 10; i++ { bucket.AllowOne() } // drain

    mc.Advance(2 * time.Second)         // advance mock clock by 2s
    // Should have earned exactly 10 tokens (5/s × 2s), capped at 10

    allowed := 0
    for i := 0; i < 12; i++ {
        if bucket.AllowOne() { allowed++ }
    }
    // Exactly 10 should be allowed (not 11 or 9)
    assert.Equal(t, 10, allowed)
}
```

---

## 20. Advanced Variants

### Variant 1: Token Bucket with Queue (Leaky Bucket Hybrid)

Instead of rejecting denied requests, queue them:

```
Request → [Token Bucket Check]
              |         |
           ALLOWED   DENIED
              |         |
           Serve    → [Queue] → Wait for tokens → Serve
                       |
                    If queue full → REJECT
```

This provides **backpressure** rather than hard rejection.

### Variant 2: Multi-Level Token Bucket (Hierarchical)

Two-tier: global + per-user. Both must pass.

```
Request → [Global Bucket: 10000 req/s] → [User Bucket: 100 req/s] → ALLOW
              |                                   |
           DENIED                             DENIED
           (system wide)                     (user specific)
```

### Variant 3: Token Bucket with Priority

Different request classes get different costs:

```rust
pub enum RequestClass {
    Critical,  // cost = 0.5 (half price)
    Normal,    // cost = 1.0 (standard)
    Bulk,      // cost = 5.0 (expensive)
}

fn cost_of(class: RequestClass) -> f64 {
    match class {
        RequestClass::Critical => 0.5,
        RequestClass::Normal   => 1.0,
        RequestClass::Bulk     => 5.0,
    }
}
```

### Variant 4: Sliding Window + Token Bucket (Hybrid)

Use token bucket for burst tolerance + sliding window for fairness at boundaries:

```
[Sliding Window Counter: 1000 req/min]
          +
[Token Bucket: burst=50, rate=16.67/s]

Both must ALLOW the request.
This prevents both:
  - Fixed window boundary double-spending
  - Unlimited burst beyond short-term budget
```

### Variant 5: Adaptive Token Bucket

Dynamically adjust rate based on system health:

```
CPU usage < 50%  → refill_rate = base_rate × 1.5  (generous)
CPU usage 50-80% → refill_rate = base_rate         (normal)
CPU usage > 80%  → refill_rate = base_rate × 0.5  (conservative)
CPU usage > 95%  → refill_rate = 0                 (circuit breaker)
```

---

## 21. Mental Models & Cognitive Strategies

### The Three Laws of Token Bucket Mastery

```
LAW 1: CAPACITY = BURST SURFACE
  Capacity controls how much punishment one client can land instantly.
  Always ask: "What is the worst-case burst I can tolerate?"

LAW 2: RATE = LONG-TERM SHAPE
  Refill rate determines the steady-state throughput.
  Bursts are temporary — rate is permanent.

LAW 3: LAZY IS CORRECT
  Lazy refill (compute on access) is equivalent to continuous refill.
  Prefer lazy: it's simpler, faster, and needs no background task.
```

### Abstraction Ladder

When solving problems, use this mental progression:

```
LEVEL 1: "I need to limit requests"
  → Rate limiting problem

LEVEL 2: "Do I need burst tolerance?"
  → YES → Token Bucket family
  → NO  → Leaky Bucket or Fixed Window

LEVEL 3: "Is it distributed?"
  → YES → Redis Lua atomic script
  → NO  → In-memory with mutex

LEVEL 4: "Is it high-contention?"
  → YES → Lock-free CAS or sharding or actor model
  → NO  → Simple mutex is fine

LEVEL 5: "Is it weighted?"
  → YES → Variable cost per request
  → NO  → cost = 1 always
```

### Chunking the Algorithm (Cognitive Science)

**Chunking** (from cognitive psychology) means grouping related details into a single mental unit. For Token Bucket:

| Chunk Name       | What It Contains                                              |
|------------------|---------------------------------------------------------------|
| **State**        | capacity, tokens, rate, last_time                            |
| **Refill Step**  | elapsed = now - last; earned = elapsed × rate; tokens = min(tokens+earned, cap); last = now |
| **Consume Step** | if tokens >= cost: tokens -= cost; return ALLOW; else DENY   |
| **Wait Formula** | deficit / rate                                               |

Once these 4 chunks are automatic, you can implement token bucket in any language in minutes.

### Deliberate Practice Schedule

To reach top 1% in algorithm fluency:

```
WEEK 1: Implement from scratch in C (no help, no reference)
  → Goal: understand the math, fight the bugs yourself

WEEK 2: Implement in Go + full test suite + benchmark
  → Goal: understand concurrency implications

WEEK 3: Implement in Rust with builder + async variant
  → Goal: understand ownership and type system alignment

WEEK 4: Implement distributed version (Redis Lua)
  → Goal: understand CAP theorem and atomic operations

MONTH 2: Build a real HTTP API server with the rate limiter
  → Goal: connect theory to production systems

MONTH 3: Read the Linux kernel TBF implementation
  → Goal: see how experts handle nanosecond precision
```

### Metacognition Checkpoint

Before implementing any algorithm, ask yourself:

```
1. What is the INVARIANT? (What must ALWAYS be true?)
   → Token Bucket: 0 ≤ tokens ≤ capacity, always.

2. What is the STATE? (What do I need to store?)
   → capacity, tokens, refill_rate, last_check_time

3. What are the OPERATIONS? (What can I do to the state?)
   → refill(), consume(cost), wait_time(cost)

4. What can go WRONG? (What are the failure modes?)
   → Race conditions, clock drift, overflow, thundering herd

5. What does CORRECT look like? (How do I verify it?)
   → Unit tests, concurrency tests, property-based invariants
```

### The Flow State Framework

To enter deep focus while coding algorithms:

```
PREPARATION (10 min):
  - Write the invariant on paper
  - Draw the data structure with ASCII
  - Write pseudocode in plain English

EXECUTION (90 min deep work block):
  - Code the data structure first
  - Code the pure functions (no concurrency)
  - Add concurrency last
  - Write tests alongside, not after

REVIEW (20 min):
  - Read your own code like a stranger
  - Check every edge case from Section 16
  - Run with race detector enabled
```

---

## Summary Reference Card

```
┌────────────────────────────────────────────────────────────────┐
│                    TOKEN BUCKET QUICK REF                      │
├────────────────────────────────────────────────────────────────┤
│  State:    capacity, tokens, refill_rate, last_time            │
│                                                                │
│  Refill:   elapsed = now - last_time                           │
│            earned  = elapsed × refill_rate                     │
│            tokens  = min(tokens + earned, capacity)            │
│            last_time = now                                     │
│                                                                │
│  Consume:  if tokens >= cost:                                  │
│              tokens -= cost; ALLOW                             │
│            else:                                               │
│              DENY; wait = (cost - tokens) / refill_rate        │
│                                                                │
│  Burst:    = capacity (max instant requests)                   │
│  Sustained = refill_rate (requests/sec long-term)              │
│  Wait:     = deficit / refill_rate (seconds)                   │
│                                                                │
│  Invariant: 0 ≤ tokens ≤ capacity                             │
│  Complexity: O(1) time, O(1) space per operation               │
├────────────────────────────────────────────────────────────────┤
│  Use when: burst OK, simple state, O(1) needed                 │
│  Avoid when: strict constant output rate needed (→ leaky)      │
└────────────────────────────────────────────────────────────────┘
```

---

*"The algorithm is not the hard part. Understanding WHY it is the way it is — that is mastery."*

Here's your complete Token Bucket guide — 21 sections, ~1,400 lines, battle-ready.

---

## What's Inside — A Map

The guide is structured as a **knowledge pyramid**: each layer builds on the one below.

```
[Mental Models & Mastery]          ← Section 21
[Advanced Variants]                ← Section 20
[Testing, Distributed, Pitfalls]   ← Sections 15–19
[C · Go · Rust Implementations]    ← Sections 11–13
[Math + Flowcharts + Diagrams]      ← Sections 7–9
[Core Concepts & Mechanics]        ← Sections 1–6
```

---

## The 3 Insights That Separate Experts

**1. Lazy Refill is Equivalent to Continuous Refill**
You don't need a background thread ticking away. The math `earned = elapsed × rate` computed *on demand* is perfectly identical to real-time accumulation — and far cheaper.

**2. Burst ≠ Bug — It's a Design Parameter**
The capacity is your deliberate tolerance for traffic spikes. Leaky Bucket forces smooth output; Token Bucket *absorbs* spikes. Neither is wrong — they solve different problems.

**3. TOCTOU Is the Only Real Danger**
The entire multi-threading challenge reduces to one race: "check then act" without atomicity. Every sync strategy (mutex, CAS, actor) is just a different way to make that check-and-consume atomic.

---

## Implementation Priority for You

| Phase | Goal |
|-------|------|
| This week | Implement the C version from memory, no reference |
| Next week | Port to Rust, add the Builder + full test suite |
| Week 3 | Add the Go actor model + HTTP middleware |
| Month 2 | Wire up the Redis Lua distributed version |