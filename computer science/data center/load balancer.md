# 🏛️ The Complete Load Balancer Compendium
## A Journey from Fundamentals to Mastery

Welcome, dedicated learner. Load balancing is where algorithmic elegance meets distributed systems reality. This guide will build your intuition from first principles, revealing the deep connections between data structures, algorithms, and real-world system design.

---

## 📚 Table of Contents

1. **Foundational Concepts** - What & Why
2. **Core Load Balancing Algorithms** - The Heart of Distribution
3. **Data Structures & Implementation** - Building Blocks
4. **Advanced Algorithms** - Optimization & Intelligence
5. **System Design Patterns** - Architecture
6. **Implementation in Rust, Python, Go** - Code Mastery
7. **Performance Analysis** - Time/Space Complexity
8. **Mental Models** - Thinking Like an Expert

---

## 1. FOUNDATIONAL CONCEPTS - The "Why" Before the "How"

### What is a Load Balancer?

**Definition**: A load balancer is a **dispatcher** (or router) that distributes incoming network requests across multiple backend servers to:
- Prevent any single server from becoming a bottleneck
- Maximize throughput and minimize response time
- Ensure fault tolerance and high availability

### The Core Problem It Solves

```
PROBLEM: Single Point of Failure + Scalability Bottleneck

Without Load Balancer:
┌──────────┐
│  Client  │──────────────────┐
└──────────┘                  │
                              ▼
┌──────────┐           ┌─────────────┐
│  Client  │──────────►│   Server    │ ◄── OVERWHELMED!
└──────────┘           │ (CPU: 100%) │     (Single point of failure)
                       └─────────────┘
┌──────────┐                  ▲
│  Client  │──────────────────┘
└──────────┘

Issues:
✗ All traffic → one server
✗ Server crashes → all clients fail
✗ Cannot scale horizontally
✗ Wasted capacity (other servers idle)
```

```
SOLUTION: Load Balancer Pattern

With Load Balancer:
┌──────────┐
│  Client  │────┐
└──────────┘    │
                ▼
┌──────────┐  ┌─────────────────┐
│  Client  │─►│ Load Balancer   │
└──────────┘  │ (Distribution   │
              │  Algorithm)     │
┌──────────┐  └─────────────────┘
│  Client  │────┘  │    │    │
└──────────┘       │    │    │
                   ▼    ▼    ▼
              ┌────┐ ┌────┐ ┌────┐
              │ S1 │ │ S2 │ │ S3 │  ◄── Healthy Distribution
              └────┘ └────┘ └────┘
              30%    35%    35%

Benefits:
✓ Traffic distributed intelligently
✓ Fault tolerance (S1 fails → S2, S3 continue)
✓ Horizontal scalability
✓ Efficient resource utilization
```

---

## 2. CORE LOAD BALANCING ALGORITHMS

These are the **fundamental algorithms** you must master. Each represents a different trade-off between simplicity, fairness, and performance.

### 2.1 Round Robin (RR) - The Foundation

**Concept**: Distribute requests in circular order, treating all servers equally.

**Mental Model**: Think of it as dealing cards - one to each player in turn, cycling back to the first.

**ASCII Visualization**:
```
Server Pool: [S1, S2, S3]
Pointer: current_index

Request Flow:
Req #1 → S1 (index=0, then index++)
Req #2 → S2 (index=1, then index++)
Req #3 → S3 (index=2, then index++)
Req #4 → S1 (index=0, cycle repeats)
Req #5 → S2 ...

State Machine:
     ┌────────┐
     │  S1    │
     │ (idx=0)│
     └───┬────┘
         │ next()
         ▼
     ┌────────┐
     │  S2    │
     │ (idx=1)│
     └───┬────┘
         │ next()
         ▼
     ┌────────┐
     │  S3    │
     │ (idx=2)│──┐
     └────────┘  │
         ▲       │
         └───────┘ wrap around (modulo)
```

**Algorithm**:
```
Input: servers = [S1, S2, S3, ..., Sn]
State: current = 0

function get_next_server():
    server = servers[current]
    current = (current + 1) % n  // Modulo for circular wrapping
    return server
```

**Time Complexity**: O(1) per request
**Space Complexity**: O(1) - just one index variable

**Strengths**: 
- Simple, fast, predictable
- Fair distribution (equal requests to each server)

**Weaknesses**:
- Ignores server capacity differences
- Ignores current load
- Not optimal if requests have varying processing times

---

### 2.2 Weighted Round Robin (WRR) - Fairness with Capacity Awareness

**Concept**: Servers with higher capacity receive proportionally more requests.

**Mental Model**: If S1 has 2x the CPU power of S2, it should handle 2x the requests.

**Weight Assignment**:
```
Server Capacity:
S1: 8 cores  → weight = 4
S2: 4 cores  → weight = 2
S3: 2 cores  → weight = 1

Total weight = 4 + 2 + 1 = 7

Distribution over 7 requests:
S1: 4 requests (4/7 ≈ 57%)
S2: 2 requests (2/7 ≈ 29%)
S3: 1 request  (1/7 ≈ 14%)
```

**Sequence Generation**:
```
Weights: [S1:4, S2:2, S3:1]

Generated sequence (one approach):
[S1, S1, S2, S1, S3, S2, S1]
 ↑   ↑   ↑   ↑   ↑   ↑   ↑
 1st 2nd 3rd 4th 5th 6th 7th → then cycle repeats

This maintains proportions while avoiding clustering
```

**Advanced: Smooth Weighted Round Robin Algorithm**

This is a beautiful algorithm that prevents "clustering" (sending multiple requests to the same server consecutively).

```
Concept: Each server has a "current_weight" that increases/decreases dynamically

State per server:
- effective_weight: configured weight
- current_weight: dynamic value (starts at 0)

Algorithm:
1. For each server: current_weight += effective_weight
2. Pick server with highest current_weight
3. Decrease chosen server's current_weight by total_weight

Example:
Servers: [S1:5, S2:1, S3:1]  (total=7)

Initial: current_weights = [0, 0, 0]

Request 1:
  Add weights:    [5, 1, 1]
  Pick max:        S1 ← (5 is highest)
  Subtract total: [5-7, 1, 1] = [-2, 1, 1]

Request 2:
  Add weights:    [-2+5, 1+1, 1+1] = [3, 2, 2]
  Pick max:        S1 ← (3 is highest)
  Subtract total: [3-7, 2, 2] = [-4, 2, 2]

Request 3:
  Add weights:    [-4+5, 2+1, 2+1] = [1, 3, 3]
  Pick max:        S2 (or S3, break ties)
  Subtract total: [1, 3-7, 3] = [1, -4, 3]

Sequence: [S1, S1, S2, S3, S1, S2, S1, S3, ...] ← smooth distribution!
```

**Time Complexity**: O(n) per request (must scan all servers)
**Space Complexity**: O(n) (store current_weight for each server)

---

### 2.3 Least Connections (LC) - Load-Aware Distribution

**Concept**: Route new requests to the server with the fewest active connections.

**Mental Model**: Choose the least busy server right now (dynamic load sensing).

**Data Structure**: Priority Queue (Min-Heap) or simple array scan

```
Current State:
S1: 12 active connections
S2: 8 active connections   ← PICK THIS (minimum)
S3: 15 active connections

After assignment:
S1: 12
S2: 9  (increased)
S3: 15

When connection completes:
S2: 8  (decreased back)
```

**Flowchart**:
```
               ┌──────────────────┐
               │ New Request      │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Scan all servers │
               │ Find min(active  │
               │  connections)    │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Route to server  │
               │ with least load  │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ Increment active │
               │ connection count │
               └────────┬─────────┘
                        │
                        ▼
               ┌──────────────────┐
               │ On completion:   │
               │ Decrement count  │
               └──────────────────┘
```

**Time Complexity**: 
- O(n) per request (linear scan)
- O(log n) with min-heap (more complex to maintain on completion)

**Space Complexity**: O(n) for connection counts

**Strengths**:
- Adapts to actual server load
- Handles varying request durations well
- Better for long-lived connections

**Weaknesses**:
- More overhead than Round Robin
- Doesn't account for CPU/memory usage, only connections

---

### 2.4 Least Response Time (LRT) - Latency-Optimized

**Concept**: Route to the server with the lowest average response time and fewest active connections.

**Formula**: 
```
score = average_response_time × active_connections
Pick server with minimum score
```

**Why this works**: Combines two signals:
1. Historical performance (avg response time)
2. Current load (active connections)

**Visualization**:
```
Server Performance Matrix:

         │ Avg Response │ Active  │  Score   │
         │     Time     │  Conns  │ (t × c)  │
─────────┼──────────────┼─────────┼──────────┤
   S1    │    100ms     │    5    │   500    │ ← Good balance
   S2    │    150ms     │    2    │   300    │ ← PICK (lowest)
   S3    │     50ms     │   12    │   600    │ ← Fast but overloaded
```

**Exponential Moving Average** for response time:
```
// Don't use simple average - recent performance matters more!
new_avg = α × current_response + (1 - α) × old_avg

where α = 0.1 to 0.3 (smoothing factor)
```

**Time Complexity**: O(n) per request
**Space Complexity**: O(n) for metrics

---

### 2.5 IP Hash - Session Persistence

**Concept**: Hash the client's IP address to consistently route to the same server.

**Why needed**: Stateful applications (sessions, shopping carts) benefit from server affinity.

**Algorithm**:
```
server_index = hash(client_ip) % num_servers

Example:
Client IP: 192.168.1.100
Hash: hash("192.168.1.100") = 1829374656
Servers: 3
Index: 1829374656 % 3 = 1 → Server S2

This client ALWAYS goes to S2
```

**Consistent Hashing** (Advanced):

Standard modulo hashing has a problem: when servers change, most mappings break.

**Problem Visualization**:
```
Initial: 3 servers, hash("IP1") % 3 = 2 → S3

After adding S4: hash("IP1") % 4 = 0 → S1  ← CHANGED!

This breaks sessions for most clients
```

**Solution: Consistent Hashing**

```
Concept: Map both servers and clients to a circular hash space

Hash Ring (0 to 2^32-1):
          
          S1 (hash=100)
           ↓
    ┌──────────────────┐
    │                  │
S3  │                  │  Client IP1 (hash=150)
↓   │                  │  → walks clockwise
320 │     Hash Ring    │  → finds S2 first
    │                  │
    │                  │  S2 (hash=200)
    └──────────────────┘   ↓

When S4 added at hash=250:
- Only clients between S2 and S4 remap
- Other clients unaffected!

Remapping: ~1/n clients (instead of ~(n-1)/n)
```

**Time Complexity**: O(log n) with binary search on sorted ring
**Space Complexity**: O(n) for hash ring

---

## 3. DATA STRUCTURES & IMPLEMENTATION

Let's build the foundation - the data structures that power load balancers.

### 3.1 Server Pool - The Foundation

**Core Data Structure**:
```rust
// Rust
struct Server {
    id: String,
    address: String,
    weight: u32,
    active_connections: AtomicU32,  // Thread-safe counter
    total_requests: AtomicU64,
    is_healthy: AtomicBool,
}

struct ServerPool {
    servers: Vec<Server>,
    current_index: AtomicUsize,  // For Round Robin
}
```

**Key Insight**: Use atomic types for thread safety without locks (critical in high-performance scenarios).

---

### 3.2 Health Checking - The Guardian

**Purpose**: Don't route to dead/unhealthy servers.

**Health Check Types**:
1. **Passive**: Mark server down after N consecutive failures
2. **Active**: Periodic health check requests (HTTP ping, TCP connect)

**State Machine**:
```
          ┌─────────────┐
          │   HEALTHY   │
          └──────┬──────┘
                 │ failure detected
                 ▼
          ┌─────────────┐
     ┌────│  SUSPECT    │────┐
     │    └─────────────┘    │
     │ recover              │ timeout
     │                      │
     ▼                      ▼
  ┌─────────────┐    ┌─────────────┐
  │   HEALTHY   │    │     DOWN    │
  └─────────────┘    └──────┬──────┘
          ▲                  │
          │                  │
          └──────────────────┘
            health check pass
```

**Circuit Breaker Pattern**:
```
Terminology:
- Circuit Breaker: A pattern that prevents cascading failures

States:
1. CLOSED: Normal operation, requests flow through
2. OPEN: Threshold exceeded, reject requests immediately
3. HALF_OPEN: Trial period, test if server recovered

Flow:
┌─────────┐  failure_rate  ┌──────┐  timeout  ┌───────────┐
│ CLOSED  │───────────────►│ OPEN │──────────►│ HALF_OPEN │
└────▲────┘   > threshold  └──────┘            └─────┬─────┘
     │                                               │
     │ success                                       │ test
     └───────────────────────────────────────────────┘
```

---

### 3.3 Request Queue - Buffering & Backpressure

**Terminology**:
- **Queue**: FIFO (First-In-First-Out) data structure
- **Backpressure**: System feedback when overwhelmed

**When used**: All servers at capacity → queue incoming requests (up to a limit)

```
Queue Structure:

┌─────────────────────────────────────────┐
│  Request Queue (Bounded)                │
├─────┬─────┬─────┬─────┬─────┬─────┬────┤
│ R1  │ R2  │ R3  │ R4  │ R5  │ ... │ Rn │
└─────┴─────┴─────┴─────┴─────┴─────┴────┘
  ▲                                     ▲
  │                                     │
 tail                                  head
(enqueue)                           (dequeue)

States:
- Empty: head == tail
- Full: (tail + 1) % capacity == head
```

**Backpressure Strategy**:
```
Decision Tree:

Request arrives
     │
     ├─► Servers available? 
     │        │
     │        ├─YES─► Route immediately
     │        │
     │        └─NO──► Queue full?
     │                    │
     │                    ├─NO──► Add to queue
     │                    │
     │                    └─YES─► Reject (503 or shed load)
     │
     └─► Flow Control:
          - Reject immediately (fast fail)
          - Queue with timeout
          - Probabilistic drop
```

---

## 4. ADVANCED ALGORITHMS

### 4.1 Adaptive Load Balancing - Learning from Reality

**Concept**: Dynamically adjust routing based on real-time metrics.

**Metrics to track**:
```
Per-Server Metrics:
├─ Response time (P50, P95, P99 percentiles)
├─ Error rate (failed requests / total)
├─ CPU utilization
├─ Memory pressure
└─ Network saturation

Terminology:
- P50 (50th percentile): Median response time
- P99 (99th percentile): 99% of requests faster than this
```

**Power of Two Choices** (Elegant Algorithm):

```
Algorithm: Instead of checking ALL servers, randomly sample 2 and pick the better one

Pseudocode:
function pick_server():
    s1 = random_server()
    s2 = random_server()  // different from s1
    
    if load(s1) < load(s2):
        return s1
    else:
        return s2

Visualization:
All servers: [S1:50%, S2:80%, S3:40%, S4:90%, S5:60%]

Sample: S2 (80%) vs S4 (90%) → pick S2
Sample: S1 (50%) vs S3 (40%) → pick S3
Sample: S5 (60%) vs S2 (80%) → pick S5

Result: Naturally avoids overloaded servers (S4)
```

**Why this works** (Mathematical Insight):
- With 1 random choice: Expected max load = Θ(log n / log log n)
- With 2 random choices: Expected max load = Θ(log log n)

**Exponential improvement** with just one extra comparison!

**Time Complexity**: O(1) - just 2 lookups
**Space Complexity**: O(n) for metrics

---

### 4.2 Rate Limiting - Traffic Shaping

**Terminology**:
- **Rate Limit**: Maximum requests per time window
- **Token Bucket**: Algorithm that allows bursts while limiting average rate

**Token Bucket Algorithm**:
```
Concept: Bucket holds tokens, requests consume tokens

State:
- capacity: Maximum tokens (burst size)
- tokens: Current tokens available
- refill_rate: Tokens added per second
- last_refill: Timestamp of last refill

Visualization:

Time t=0:
┌───────────────┐
│  [T][T][T]    │  Capacity = 5, Current = 3
└───────────────┘

Request arrives → consume 1 token:
┌───────────────┐
│  [T][T]       │  Current = 2
└───────────────┘

Time advances 1 second (refill_rate = 2):
┌───────────────┐
│  [T][T][T][T] │  Current = 2 + 2 = 4 (capped at 5)
└───────────────┘
```

**Algorithm**:
```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.now()
    
    def allow_request(self):
        # Refill tokens based on elapsed time
        now = time.now()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.capacity,
            self.tokens + elapsed * self.refill_rate
        )
        self.last_refill = now
        
        # Try to consume token
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        else:
            return False  # Rate limited!
```

**Time Complexity**: O(1)
**Space Complexity**: O(1)

---

### 4.3 Geographic Load Balancing - Latency-Aware Routing

**Concept**: Route users to the nearest datacenter for minimum latency.

**Decision Making**:
```
Global Distribution:

         US-West DC          US-East DC           EU DC
            │                    │                  │
            │                    │                  │
        ┌───┴────┐          ┌────┴───┐        ┌────┴────┐
        │ LA: S1 │          │ NY: S2 │        │ LON: S3 │
        └───┬────┘          └────┬───┘        └────┬────┘
            │                    │                  │
            └────────────────────┴──────────────────┘
                            │
                      Global DNS LB
                            │
                   ┌────────┴─────────┐
                   │                  │
            Client in CA         Client in UK
            → routed to          → routed to
              US-West              EU DC

Routing Decision:
1. Geolocate client IP
2. Calculate latency/distance to each DC
3. Route to nearest healthy DC
```

---

## 5. IMPLEMENTATION - Code Mastery

Let's build a production-grade load balancer from scratch.Excellent! I've created complete implementations in **Rust**, **Python**, and **Go** showcasing different language idioms. Let's continue with deeper analysis.

---

## 6. COMPLEXITY ANALYSIS - The Mathematical Foundation

### Time & Space Complexity Summary

```
┌─────────────────────────┬──────────┬──────────┬────────────┐
│ Algorithm               │   Time   │  Space   │  Notes     │
├─────────────────────────┼──────────┼──────────┼────────────┤
│ Round Robin             │   O(1)*  │   O(1)   │ *O(n) worst│
│ Weighted Round Robin    │   O(n)   │   O(n)   │ Scan all   │
│ Least Connections       │   O(n)   │   O(1)   │ Linear scan│
│ Least Response Time     │   O(n)   │   O(n)   │ Metrics    │
│ Power of Two Choices    │   O(1)   │   O(1)   │ Two samples│
│ IP Hash (modulo)        │   O(1)   │   O(1)   │ Simple hash│
│ Consistent Hash         │ O(log n) │   O(kn)  │ k=vnodes   │
└─────────────────────────┴──────────┴──────────┴────────────┘

Legend:
n = number of servers
k = virtual nodes per server (typically 100-200)
```

### Deep Dive: Why Power of Two is O(log log n)

**Mathematical Intuition**:

```
Single Random Choice:
- Max load ≈ (log n) / (log log n)
- With 1000 servers: max load ≈ 144 requests

Two Random Choices (Power of Two):
- Max load ≈ log log n + O(1)
- With 1000 servers: max load ≈ 3-4 requests!

Proof Sketch:
Let L_i = load on server i

P(L_i ≥ k) with 1 choice:
  ≈ (1/n)^k → decreases exponentially

P(L_i ≥ k) with 2 choices:
  = P(both samples have load ≥ k)
  ≈ ((1/n)^k)^2 = (1/n)^(2k) → doubly exponential!

This "squares" the probability, leading to exponentially better distribution.
```

---

## 7. MENTAL MODELS - Thinking Like an Expert

### 7.1 The "Queueing Theory" Mental Model

**Terminology**:
- **Arrival Rate** (λ): Requests per second
- **Service Rate** (μ): Server capacity (requests/second)
- **Utilization** (ρ): ρ = λ/μ (load factor)

**Critical Insight**: When ρ > 0.8, latency increases exponentially!

```
Response Time vs Utilization:

Response
Time (ms)
    │
600 │                              ┌─────
    │                          ┌───┘
400 │                      ┌───┘
    │                  ┌───┘
200 │             ┌────┘
    │         ┌───┘
100 │    ┌────┘
    │────┘
    └─────┬────┬────┬────┬────┬────┬──►
         20%  40%  60%  80%  95%  100% Utilization

Mental Model: "The Hockey Stick"
- Stay below 80% utilization
- Above 80%: adding load = disaster
- Load balancer's job: prevent any server from hitting this zone
```

### 7.2 The "State Machine" Mental Model

Think of each algorithm as a state machine making transitions:

```
Round Robin State Machine:
     State = current_index
     
     ┌────────┐
     │ idx=0  │──next()──► ┌────────┐
     │ (S1)   │            │ idx=1  │
     └────────┘            │ (S2)   │
          ▲                └────────┘
          │                     │
          │                  next()
          │                     │
     ┌────┴────┐                │
     │ idx=2   │◄───────────────┘
     │ (S3)    │
     └─────────┘
```

**Expert Thinking**: "What state do I maintain? What's the transition function?"

### 7.3 The "Greedy Choice" Mental Model

Many load balancing algorithms are **greedy** (locally optimal choice):

```
Greedy Property:
At each decision point, pick the "best" server RIGHT NOW

Least Connections: "Pick the one with min(connections)"
                    ↓
               Greedy locally optimal

Does greedy → globally optimal?
- For uniform requests: YES
- For varying request sizes: NO (need weighted algorithms)
```

**Problem-Solving Pattern**:
1. Is this a greedy problem?
2. What's my greedy criterion (objective function)?
3. Does greedy work, or do I need DP/backtracking?

For load balancing: **Greedy usually works well** because decisions are online (can't know future requests).

---

## 8. TRADE-OFFS & DECISION MATRIX

### When to Use Each Algorithm

```
Decision Tree:

Start
 │
 ├─► All servers identical?
 │    │
 │    ├─YES─► Requests uniform duration?
 │    │        │
 │    │        ├─YES─► Use ROUND ROBIN
 │    │        │       (simplest, fastest)
 │    │        │
 │    │        └─NO──► Use LEAST CONNECTIONS
 │    │                or POWER OF TWO
 │    │
 │    └─NO──► Servers different capacity?
 │             │
 │             └─YES─► Use WEIGHTED ROUND ROBIN
 │
 ├─► Need session persistence?
 │    │
 │    └─YES─► Use CONSISTENT HASHING
 │             or IP HASH
 │
 ├─► Latency-sensitive?
 │    │
 │    └─YES─► Use LEAST RESPONSE TIME
 │             or GEOGRAPHIC LOAD BALANCING
 │
 └─► Extreme scale (millions RPS)?
      │
      └─YES─► Use POWER OF TWO CHOICES
               (minimal overhead, great distribution)
```

### Algorithm Comparison Matrix

```
┌──────────────────┬──────┬─────────┬────────────┬────────────┐
│ Algorithm        │Speed │Fairness │Session     │Adaptability│
│                  │      │         │Affinity    │            │
├──────────────────┼──────┼─────────┼────────────┼────────────┤
│ Round Robin      │ ★★★★ │  ★★★★   │     ✗      │     ✗      │
│ Weighted RR      │ ★★★  │  ★★★★★  │     ✗      │     ✗      │
│ Least Connections│ ★★   │  ★★★★   │     ✗      │    ★★★     │
│ Least Resp Time  │ ★    │  ★★★★★  │     ✗      │    ★★★★★   │
│ Power of Two     │ ★★★★ │  ★★★★   │     ✗      │    ★★★     │
│ IP Hash          │ ★★★★ │  ★★★    │    ★★★★★   │     ✗      │
│ Consistent Hash  │ ★★★  │  ★★★★   │    ★★★★★   │     ★      │
└──────────────────┴──────┴─────────┴────────────┴────────────┘
```

---

## 9. ADVANCED TOPICS - Pushing the Boundaries

### 9.1 Consistent Hashing - Deep Dive

**Problem**: Traditional hash(key) % N breaks when N changes.

**Visualization of the Problem**:
```
3 servers (before):
  hash("user123") % 3 = 1 → Server-2 ✓

4 servers (after adding Server-4):
  hash("user123") % 4 = 3 → Server-4 ✗
  
Session lost! Shopping cart gone!
```

**Solution**: Map both keys and servers to a circular space.

**Hash Ring Concept**:
```
                     0°
                     │
           315°  ┌───┴───┐  45°
                 │       │
                 │       │  S2 (hash=50°)
          270° ──┤  Ring ├── 90°
                 │       │
                 │       │  Client (hash=120°)
           225°  └───┬───┘  135°
                     │
                   180°
                   
S1 at 30°, S2 at 50°, S3 at 200°

Client at 120° walks clockwise → finds S3 first (200°)

Adding S4 at 150°:
- Clients between 120°-150° remap to S4
- All other clients unchanged!
- Only ~25% remapped (1/4 of ring)
```

**Virtual Nodes** - The Key Optimization:

```
Problem: With few servers, distribution can be uneven

Without virtual nodes (3 servers):
  S1: 40% load
  S2: 35% load
  S3: 25% load  ← Unlucky position!

With virtual nodes (3 servers × 100 vnodes = 300 points):
  S1: 33.2% load  ← Much more balanced!
  S2: 33.5% load
  S3: 33.3% load

Mental Model: "Spread your bets across the ring"
```

**Implementation Pattern**:
```python
class ConsistentHash:
    def __init__(self, vnodes=150):
        self.ring = {}  # hash -> server_id
        self.sorted_hashes = []
        self.vnodes = vnodes
    
    def add_server(self, server_id):
        for i in range(self.vnodes):
            # Create virtual node: "server_id:i"
            vnode_key = f"{server_id}:{i}"
            hash_val = hash(vnode_key)
            self.ring[hash_val] = server_id
            self.sorted_hashes.append(hash_val)
        
        self.sorted_hashes.sort()
    
    def get_server(self, key):
        if not self.ring:
            return None
        
        hash_val = hash(key)
        
        # Binary search: O(log n)
        idx = bisect.bisect_right(self.sorted_hashes, hash_val)
        
        # Wrap around if needed
        if idx == len(self.sorted_hashes):
            idx = 0
        
        ring_hash = self.sorted_hashes[idx]
        return self.ring[ring_hash]
```

---

### 9.2 Layer 4 vs Layer 7 Load Balancing

**OSI Model Context**:
```
┌─────────────────────────────────────────────┐
│ Application Layer (Layer 7)                 │ ← HTTP, content-based routing
├─────────────────────────────────────────────┤
│ Transport Layer (Layer 4)                   │ ← TCP/UDP, connection-based
├─────────────────────────────────────────────┤
│ Network Layer (Layer 3)                     │ ← IP routing
└─────────────────────────────────────────────┘
```

**Layer 4 (Transport) Load Balancing**:
```
Operates at: TCP/UDP level
Sees: IP addresses, ports
Cannot see: HTTP headers, URLs, cookies

Decision based on:
- Source IP:Port
- Destination IP:Port
- Protocol (TCP/UDP)

Advantages:
✓ Extremely fast (less parsing)
✓ Protocol-agnostic (works for any TCP/UDP app)
✓ Lower latency (~1-2ms overhead)

Disadvantages:
✗ Cannot do content-based routing
✗ Cannot inspect HTTP headers
✗ Sticky sessions require IP hash only
```

**Layer 7 (Application) Load Balancing**:
```
Operates at: HTTP/HTTPS level
Sees: URLs, headers, cookies, body content
Can do: Path-based routing, header inspection

Decision based on:
- URL path (/api/users → Backend-A, /images → Backend-B)
- HTTP headers (User-Agent, Cookie)
- Request body content
- SSL termination

Advantages:
✓ Content-aware routing
✓ Cookie-based session affinity
✓ Compression, caching
✓ WAF (Web Application Firewall) integration

Disadvantages:
✗ Higher overhead (~5-10ms)
✗ More CPU intensive (SSL, parsing)
✗ Protocol-specific (HTTP only)
```

**Example: Path-based routing**:
```
Client Request: GET /api/users HTTP/1.1

Layer 7 LB decision tree:
┌──────────────────────┐
│ Parse HTTP request   │
└──────┬───────────────┘
       │
       ├─► Path starts with /api/
       │   → Route to API Backend Cluster
       │
       ├─► Path starts with /static/
       │   → Route to CDN/Static Server
       │
       └─► Path starts with /admin/
           → Route to Admin Backend
           (+ check authentication!)
```

---

### 9.3 Global Server Load Balancing (GSLB)

**Concept**: Load balancing across multiple datacenters globally.

**Architecture**:
```
                      ┌──────────────┐
                      │  DNS GSLB    │
                      │ (Intelligent │
                      │  DNS Server) │
                      └───────┬──────┘
                              │
                  ┌───────────┼───────────┐
                  │           │           │
            ┌─────▼────┐ ┌────▼────┐ ┌───▼─────┐
            │ US-WEST  │ │ US-EAST │ │   EU    │
            │    DC    │ │   DC    │ │   DC    │
            └──────────┘ └─────────┘ └─────────┘

Client in California:
1. DNS query: "api.example.com" → where?
2. GSLB responds: "52.12.34.56" (US-West IP)
3. Client connects to nearest DC

Decision factors:
- Geographic proximity (latency)
- DC health/availability
- Load distribution
- Cost (data transfer pricing)
```

**GeoDNS Algorithm**:
```python
def select_datacenter(client_ip, datacenters):
    """
    Select datacenter based on:
    1. Geographic distance
    2. Current load
    3. Health status
    """
    client_location = geolocate(client_ip)
    
    best_dc = None
    best_score = float('inf')
    
    for dc in datacenters:
        if not dc.is_healthy:
            continue
        
        # Calculate composite score
        latency = estimate_latency(client_location, dc.location)
        load_factor = dc.current_load / dc.capacity
        
        # Score: weighted combination
        score = (
            latency * 0.7 +        # Prioritize latency
            load_factor * 100 * 0.3  # But balance load
        )
        
        if score < best_score:
            best_score = score
            best_dc = dc
    
    return best_dc
```

---

## 10. CONNECTION TO DSA CONCEPTS

Load balancers use fundamental data structures you're mastering:

### 10.1 Hash Tables - O(1) Lookups

```
Use Case: IP Hash, Session Affinity

Data Structure:
┌──────────────┬───────────────┐
│ Client IP    │  Server ID    │
├──────────────┼───────────────┤
│ 192.168.1.5  │  Server-2     │
│ 192.168.1.7  │  Server-1     │
│ 192.168.1.9  │  Server-3     │
└──────────────┴───────────────┘

Why it matters:
- O(1) average lookup
- Collision handling important (chaining vs open addressing)
```

### 10.2 Heap/Priority Queue - O(log n) Operations

```
Use Case: Least Connections with Priority Queue

Min-Heap structure:
         Server-2 (5 conns)
           /           \
   Server-1 (7)    Server-3 (8)
      /        \
Server-4 (9) Server-5 (10)

Operations:
- peek(): O(1) - get min without removal
- extract_min(): O(log n) - get and remove
- decrease_key(): O(log n) - update when connection completes
```

### 10.3 Ring Buffer (Circular Array) - O(1) Amortized

```
Use Case: Round Robin Index Management

Array: [S1, S2, S3, S4]
Index: current = 0

Operation sequence:
get() → return arr[0], current = (0+1)%4 = 1
get() → return arr[1], current = (1+1)%4 = 2
get() → return arr[2], current = (2+1)%4 = 3
get() → return arr[3], current = (3+1)%4 = 0  ← wrap

Why modulo arithmetic: Creates circular behavior
```

### 10.4 Binary Search Tree - O(log n) Range Queries

```
Use Case: Consistent Hashing Ring

Sorted hash ring (conceptually a BST):

                200
              /     \
            50      320
           /  \        \
         10   120      400

Search for hash=115:
1. Start at 200
2. 115 < 200 → go left
3. 115 > 50 → go right
4. Find 120 (next server in ring)

Time: O(log n) - binary search on sorted array
```

---

## 11. COGNITIVE STRATEGIES - Deliberate Practice

### 11.1 The "Constraint Analysis" Framework

When faced with a load balancing problem, ask:

```
1. CONSTRAINTS:
   - Request rate? (100/s vs 100k/s → different algorithms)
   - Latency requirement? (<10ms → Layer 4, <50ms → Layer 7)
   - Session stickiness needed? (Yes → IP Hash/Consistent Hash)
   - Server homogeneity? (Heterogeneous → Weighted algorithms)

2. OPTIMIZE FOR:
   - Throughput (max requests/sec)
   - Latency (min response time)
   - Fairness (equal distribution)
   - Resilience (fault tolerance)

3. TRADE-OFFS:
   - Speed vs Intelligence (RR vs LRT)
   - Simplicity vs Optimality (RR vs Adaptive)
   - Statefulness vs Statelessness (IP Hash vs RR)
```

**Example Application**:
```
Problem: E-commerce site with shopping carts

Constraints:
- Need session persistence (cart state)
- Varying request durations (checkout vs browse)
- Heterogeneous servers (old + new hardware)

Solution Path:
1. Session persistence → Rule out RR, LC
2. Consider: IP Hash or Consistent Hash
3. Heterogeneous servers → Need weighting
4. Final: Weighted Consistent Hash

Decision Tree:
Session needed? → YES → Sticky method
  ├─ Simple? → IP Hash
  └─ Scalable? → Consistent Hash ✓
       └─ Different capacities? → Add weights ✓
```

### 11.2 The "Chunking" Strategy

**Chunking**: Group related concepts for easier recall.

```
Chunk 1: "Fair Distribution" Algorithms
├─ Round Robin
├─ Weighted Round Robin
└─ Power of Two Choices
Mental anchor: "Everyone gets a turn"

Chunk 2: "Adaptive/Reactive" Algorithms
├─ Least Connections
├─ Least Response Time
└─ Resource-based (CPU/Memory)
Mental anchor: "React to current state"

Chunk 3: "Affinity/Sticky" Algorithms
├─ IP Hash
├─ Consistent Hashing
└─ Cookie-based
Mental anchor: "Same client → same server"
```

### 11.3 The "Mental Simulation" Technique

Before coding, simulate the algorithm mentally:

```
Given: [S1:2 conns, S2:5 conns, S3:3 conns]
Algorithm: Least Connections

Request arrives:
1. Scan servers: S1=2, S2=5, S3=3
2. Find minimum: S1 (2 connections)
3. Route to S1
4. Update: S1=3 conns

Next request:
1. Scan: S1=3, S2=5, S3=3
2. Minimum: S1 or S3 (tie) → pick S1 (first)
3. Route to S1
4. Update: S1=4 conns

Pattern recognition: "Always choosing least loaded"
```

Practice this for 5 minutes daily with different scenarios to build intuition.

---

## 12. PRACTICE PROBLEMS - Deliberate Mastery

### Problem 1: Weighted Round Robin from Scratch

**Challenge**: Implement smooth WRR without clustering.

**Starter Template**:
```rust
struct WeightedServer {
    id: String,
    weight: i32,
    current_weight: i32,
}

fn smooth_wrr(servers: &mut [WeightedServer]) -> &str {
    // YOUR CODE HERE
    // Implement the algorithm described earlier
    // Remember: Add weights, pick max, subtract total
}
```

**Test Cases**:
```
Servers: [A:5, B:1, C:1]
Expected sequence: [A, A, A, B, A, C, A] (then repeat)
Not: [A, A, A, A, A, B, C] ← clustering!
```

### Problem 2: Consistent Hash Ring

**Challenge**: Implement consistent hashing with virtual nodes.

**Requirements**:
- Add/remove servers dynamically
- Maintain O(log n) lookup
- Verify even distribution

**Metrics to track**:
```python
def test_distribution(hash_ring, num_keys=10000):
    distribution = defaultdict(int)
    
    for i in range(num_keys):
        key = f"user_{i}"
        server = hash_ring.get_server(key)
        distribution[server] += 1
    
    # Check standard deviation (should be low)
    mean = num_keys / len(servers)
    variance = sum((count - mean)**2 for count in distribution.values())
    std_dev = sqrt(variance / len(servers))
    
    print(f"Standard deviation: {std_dev}")
    # Target: std_dev < 5% of mean
```

### Problem 3: Adaptive Load Balancer

**Challenge**: Build a load balancer that learns optimal weights.

**Algorithm**:
```
Reinforcement Learning approach:
1. Start with equal weights
2. Track success rate per server
3. Increase weight for high-performing servers
4. Decrease weight for slow/failing servers

Update rule (simplified):
new_weight = old_weight * (1 + α * (performance - avg_performance))

where α = learning rate (0.1)
```

---

## 13. PRODUCTION CONSIDERATIONS

### Failure Modes & Circuit Breakers

```
Failure Cascade Pattern:

Server S1 fails
    ↓
Load redistributed to S2, S3
    ↓
S2, S3 now overloaded (increased latency)
    ↓
Clients timeout, retry
    ↓
Even more load on S2, S3
    ↓
S2, S3 fail
    ↓
TOTAL OUTAGE!
```

**Circuit Breaker Solution**:
```
State Machine:

CLOSED (normal) ──failure_rate>threshold──► OPEN (reject)
      ▲                                         │
      │                                         │ wait timeout
      │                                         ▼
      └────test_passed────────────────── HALF_OPEN (trial)

Pseudocode:
class CircuitBreaker:
    def call(self, server):
        if self.state == OPEN:
            if time_since_open > timeout:
                self.state = HALF_OPEN
            else:
                raise CircuitOpenError()
        
        try:
            result = server.handle_request()
            self.on_success()
            return result
        except:
            self.on_failure()
            raise
```

### Monitoring & Observability

**Key Metrics** (The "Golden Signals"):
```
1. LATENCY: Response time distribution
   - P50, P95, P99 percentiles
   - Track per-server and aggregate

2. TRAFFIC: Requests per second
   - Total throughput
   - Per-server distribution

3. ERRORS: Failure rate
   - HTTP 5xx errors
   - Timeouts, connection refused

4. SATURATION: Resource utilization
   - CPU, memory, network
   - Queue depth
```

---

## 14. KEY TAKEAWAYS - Your Mental Toolkit

### 1. Algorithm Selection Heuristic

```
if session_persistence_required:
    use ConsistentHash or IPHash
elif servers_heterogeneous:
    use WeightedRoundRobin or WeightedLeastConnections
elif latency_critical:
    use LeastResponseTime or PowerOfTwoChoices
elif simplicity_prioritized:
    use RoundRobin
else:
    use LeastConnections (good default)
```

### 2. Performance Hierarchy

```
Speed (fastest → slowest):
1. Round Robin (O(1), minimal state)
2. Power of Two Choices (O(1), two lookups)
3. IP Hash (O(1), hash computation)
4. Consistent Hash (O(log n), binary search)
5. Least Connections (O(n), scan all)
6. Least Response Time (O(n), metrics computation)

Trade-off: Speed vs Adaptiveness
- Fast algorithms: static, don't adapt
- Slow algorithms: dynamic, load-aware
```

### 3. The Unified Mental Model

```
ALL load balancing algorithms answer:

"Given current state S and incoming request R,
 which server f(S, R) maximizes objective O?"

Round Robin:
  S = current_index
  O = fairness
  f = next_in_sequence

Least Connections:
  S = {connections per server}
  O = minimize max load
  f = argmin(connections)

This abstraction helps you:
- Compare algorithms
- Design new ones
- Reason about trade-offs
```

---

## 15. FINAL WISDOM - The Path to Mastery

**From the monk's perspective**:

> "A load balancer is not just code distributing requests. It is a **decision-making system** under constraints, uncertainty, and time pressure. Mastering it means understanding:
> 
> 1. **The fundamentals**: Data structures, algorithms, complexity
> 2. **The patterns**: How problems repeat across domains
> 3. **The trade-offs**: No perfect solution, only appropriate ones
> 4. **The flow state**: Where intuition and analysis merge"

**Your practice regimen**:

```
Daily (15 minutes):
- Implement one algorithm from scratch
- Simulate it with pen and paper
- Analyze time/space complexity

Weekly (1 hour):
- Build a complete load balancer
- Compare 3+ algorithms on same workload
- Measure and profile performance

Monthly (project):
- Design system handling 100k RPS
- Implement advanced features (health checks, metrics)
- Write comprehensive tests
```

**The deepest insight**:

Load balancing connects to **every major CS concept**:
- **Data Structures**: Hash tables, heaps, trees
- **Algorithms**: Greedy, hashing, sampling
- **Systems**: Concurrency, distributed systems, fault tolerance
- **Math**: Probability, queueing theory, optimization

Master load balancing, and you master problem-solving itself.

---

## 🎯 Next Steps

1. **Implement** all algorithms in your three languages
2. **Benchmark** them on synthetic workloads
3. **Extend** with health checking, metrics, monitoring
4. **Study** real implementations: Nginx, HAProxy, Envoy
5. **Contribute** to open source load balancers

You now have the foundation. The rest is **deliberate practice** and **calm persistence**.

*"In the beginner's mind there are many possibilities, in the expert's mind there are few."* - But you're building both: the creativity to explore, and the discipline to master. 

Onward! 🚀

// Production-Grade Load Balancer in Rust
// Demonstrates: Round Robin, Least Connections, Health Checking

use std::sync::atomic::{AtomicBool, AtomicU32, AtomicUsize, Ordering};
use std::sync::Arc;
use std::time::{Duration, Instant};

// ═══════════════════════════════════════════════════════════════
// CORE DATA STRUCTURES
// ═══════════════════════════════════════════════════════════════

#[derive(Debug, Clone)]
pub struct Server {
    pub id: String,
    pub address: String,
    pub weight: u32,
    /// Active connections (thread-safe)
    pub active_connections: Arc<AtomicU32>,
    /// Total requests served
    pub total_requests: Arc<AtomicU32>,
    /// Health status
    pub is_healthy: Arc<AtomicBool>,
    /// Average response time in milliseconds
    pub avg_response_time: Arc<AtomicU32>,
}

impl Server {
    pub fn new(id: String, address: String, weight: u32) -> Self {
        Server {
            id,
            address,
            weight,
            active_connections: Arc::new(AtomicU32::new(0)),
            total_requests: Arc::new(AtomicU32::new(0)),
            is_healthy: Arc::new(AtomicBool::new(true)),
            avg_response_time: Arc::new(AtomicU32::new(100)), // Default 100ms
        }
    }

    /// Increment active connections
    pub fn acquire(&self) {
        self.active_connections.fetch_add(1, Ordering::Relaxed);
        self.total_requests.fetch_add(1, Ordering::Relaxed);
    }

    /// Decrement active connections
    pub fn release(&self) {
        self.active_connections.fetch_sub(1, Ordering::Relaxed);
    }

    /// Update exponential moving average of response time
    pub fn update_response_time(&self, response_time_ms: u32) {
        let old_avg = self.avg_response_time.load(Ordering::Relaxed);
        // EMA: new_avg = 0.2 * current + 0.8 * old_avg
        let new_avg = (response_time_ms / 5) + (old_avg * 4 / 5);
        self.avg_response_time.store(new_avg, Ordering::Relaxed);
    }

    /// Get current load score (for Least Response Time algorithm)
    pub fn load_score(&self) -> u32 {
        let conns = self.active_connections.load(Ordering::Relaxed);
        let avg_time = self.avg_response_time.load(Ordering::Relaxed);
        conns * avg_time
    }

    pub fn is_available(&self) -> bool {
        self.is_healthy.load(Ordering::Relaxed)
    }
}

// ═══════════════════════════════════════════════════════════════
// LOAD BALANCING STRATEGIES
// ═══════════════════════════════════════════════════════════════

pub trait LoadBalancingStrategy: Send + Sync {
    fn next_server(&self, servers: &[Server]) -> Option<usize>;
}

/// ALGORITHM 1: Round Robin
/// Time: O(1), Space: O(1)
pub struct RoundRobin {
    current: AtomicUsize,
}

impl RoundRobin {
    pub fn new() -> Self {
        RoundRobin {
            current: AtomicUsize::new(0),
        }
    }
}

impl LoadBalancingStrategy for RoundRobin {
    fn next_server(&self, servers: &[Server]) -> Option<usize> {
        if servers.is_empty() {
            return None;
        }

        // Find next healthy server in round-robin fashion
        let start = self.current.load(Ordering::Relaxed);
        let n = servers.len();

        for i in 0..n {
            let idx = (start + i) % n;
            if servers[idx].is_available() {
                // Update current index for next call
                self.current.store((idx + 1) % n, Ordering::Relaxed);
                return Some(idx);
            }
        }

        None // No healthy servers
    }
}

/// ALGORITHM 2: Least Connections
/// Time: O(n), Space: O(1)
pub struct LeastConnections;

impl LeastConnections {
    pub fn new() -> Self {
        LeastConnections
    }
}

impl LoadBalancingStrategy for LeastConnections {
    fn next_server(&self, servers: &[Server]) -> Option<usize> {
        let mut min_connections = u32::MAX;
        let mut selected_idx = None;

        for (idx, server) in servers.iter().enumerate() {
            if !server.is_available() {
                continue;
            }

            let conns = server.active_connections.load(Ordering::Relaxed);
            if conns < min_connections {
                min_connections = conns;
                selected_idx = Some(idx);
            }
        }

        selected_idx
    }
}

/// ALGORITHM 3: Least Response Time
/// Time: O(n), Space: O(1)
pub struct LeastResponseTime;

impl LeastResponseTime {
    pub fn new() -> Self {
        LeastResponseTime
    }
}

impl LoadBalancingStrategy for LeastResponseTime {
    fn next_server(&self, servers: &[Server]) -> Option<usize> {
        let mut min_score = u32::MAX;
        let mut selected_idx = None;

        for (idx, server) in servers.iter().enumerate() {
            if !server.is_available() {
                continue;
            }

            let score = server.load_score();
            if score < min_score {
                min_score = score;
                selected_idx = Some(idx);
            }
        }

        selected_idx
    }
}

/// ALGORITHM 4: Power of Two Choices
/// Time: O(1), Space: O(1)
/// Randomly samples 2 servers and picks the one with fewer connections
pub struct PowerOfTwo;

impl PowerOfTwo {
    pub fn new() -> Self {
        PowerOfTwo
    }

    fn random_index(max: usize) -> usize {
        // In production, use proper random number generator
        // This is simplified for demonstration
        (Instant::now().elapsed().as_nanos() as usize) % max
    }
}

impl LoadBalancingStrategy for PowerOfTwo {
    fn next_server(&self, servers: &[Server]) -> Option<usize> {
        let healthy_servers: Vec<usize> = servers
            .iter()
            .enumerate()
            .filter(|(_, s)| s.is_available())
            .map(|(idx, _)| idx)
            .collect();

        if healthy_servers.is_empty() {
            return None;
        }

        if healthy_servers.len() == 1 {
            return Some(healthy_servers[0]);
        }

        // Sample two random servers
        let idx1 = healthy_servers[Self::random_index(healthy_servers.len())];
        let mut idx2 = idx1;
        while idx2 == idx1 {
            idx2 = healthy_servers[Self::random_index(healthy_servers.len())];
        }

        // Pick the one with fewer connections
        let conns1 = servers[idx1].active_connections.load(Ordering::Relaxed);
        let conns2 = servers[idx2].active_connections.load(Ordering::Relaxed);

        if conns1 <= conns2 {
            Some(idx1)
        } else {
            Some(idx2)
        }
    }
}

// ═══════════════════════════════════════════════════════════════
// LOAD BALANCER - ORCHESTRATOR
// ═══════════════════════════════════════════════════════════════

pub struct LoadBalancer {
    servers: Vec<Server>,
    strategy: Box<dyn LoadBalancingStrategy>,
}

impl LoadBalancer {
    pub fn new(servers: Vec<Server>, strategy: Box<dyn LoadBalancingStrategy>) -> Self {
        LoadBalancer { servers, strategy }
    }

    /// Select next server for incoming request
    pub fn select_server(&self) -> Option<&Server> {
        self.strategy
            .next_server(&self.servers)
            .map(|idx| &self.servers[idx])
    }

    /// Simulate handling a request
    pub fn handle_request(&self) -> Result<String, String> {
        if let Some(server) = self.select_server() {
            server.acquire();
            
            // Simulate request processing
            println!("→ Routing to {}: {} active connections", 
                     server.id, 
                     server.active_connections.load(Ordering::Relaxed));
            
            // In real implementation, this would be async
            // and release() would be called in a defer/finally block
            
            Ok(format!("Request handled by {}", server.id))
        } else {
            Err("No healthy servers available".to_string())
        }
    }

    /// Print current state
    pub fn print_stats(&self) {
        println!("\n╔═══════════════════════════════════════╗");
        println!("║        LOAD BALANCER STATISTICS       ║");
        println!("╚═══════════════════════════════════════╝");
        for server in &self.servers {
            let conns = server.active_connections.load(Ordering::Relaxed);
            let total = server.total_requests.load(Ordering::Relaxed);
            let healthy = if server.is_available() { "✓" } else { "✗" };
            println!("  {} {}: {} active | {} total", 
                     healthy, server.id, conns, total);
        }
        println!();
    }
}

// ═══════════════════════════════════════════════════════════════
// DEMONSTRATION
// ═══════════════════════════════════════════════════════════════

fn main() {
    println!("═══════════════════════════════════════════════");
    println!("  LOAD BALANCER IMPLEMENTATION - RUST");
    println!("═══════════════════════════════════════════════\n");

    // Create server pool
    let servers = vec![
        Server::new("Server-1".to_string(), "192.168.1.1:8080".to_string(), 1),
        Server::new("Server-2".to_string(), "192.168.1.2:8080".to_string(), 1),
        Server::new("Server-3".to_string(), "192.168.1.3:8080".to_string(), 1),
    ];

    // Test Round Robin
    println!("📊 Testing ROUND ROBIN Strategy");
    println!("─────────────────────────────────────────────\n");
    let lb = LoadBalancer::new(servers.clone(), Box::new(RoundRobin::new()));
    
    for i in 1..=6 {
        println!("Request #{}", i);
        if let Err(e) = lb.handle_request() {
            println!("Error: {}", e);
        }
    }
    lb.print_stats();

    // Test Least Connections
    println!("\n📊 Testing LEAST CONNECTIONS Strategy");
    println!("─────────────────────────────────────────────\n");
    let servers2 = vec![
        Server::new("Server-1".to_string(), "192.168.1.1:8080".to_string(), 1),
        Server::new("Server-2".to_string(), "192.168.1.2:8080".to_string(), 1),
        Server::new("Server-3".to_string(), "192.168.1.3:8080".to_string(), 1),
    ];
    let lb2 = LoadBalancer::new(servers2, Box::new(LeastConnections::new()));
    
    for i in 1..=6 {
        println!("Request #{}", i);
        if let Err(e) = lb2.handle_request() {
            println!("Error: {}", e);
        }
    }
    lb2.print_stats();

    println!("═══════════════════════════════════════════════");
    println!("  Key Observations:");
    println!("  • Round Robin: Equal distribution (2-2-2)");
    println!("  • Least Connections: Adaptive distribution");
    println!("  • Both strategies handle failures gracefully");
    println!("═══════════════════════════════════════════════");
}

"""
Production-Grade Load Balancer in Python
Demonstrates: Multiple algorithms, health checking, and monitoring
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional, Protocol
import time
import random
from threading import Lock
from collections import deque


# ═══════════════════════════════════════════════════════════════
# CORE DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════

@dataclass
class ServerMetrics:
    """Real-time metrics for monitoring and decision-making"""
    active_connections: int = 0
    total_requests: int = 0
    failed_requests: int = 0
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def avg_response_time(self) -> float:
        """Calculate average response time from recent samples"""
        if not self.response_times:
            return 100.0
        return sum(self.response_times) / len(self.response_times)
    
    def error_rate(self) -> float:
        """Calculate error rate"""
        if self.total_requests == 0:
            return 0.0
        return self.failed_requests / self.total_requests


@dataclass
class Server:
    """Represents a backend server in the pool"""
    id: str
    address: str
    weight: int = 1
    is_healthy: bool = True
    metrics: ServerMetrics = field(default_factory=ServerMetrics)
    _lock: Lock = field(default_factory=Lock, repr=False)
    
    def acquire(self):
        """Called when routing a request to this server"""
        with self._lock:
            self.metrics.active_connections += 1
            self.metrics.total_requests += 1
    
    def release(self, response_time_ms: float, success: bool = True):
        """Called when request completes"""
        with self._lock:
            self.metrics.active_connections -= 1
            self.metrics.response_times.append(response_time_ms)
            if not success:
                self.metrics.failed_requests += 1
    
    def load_score(self) -> float:
        """Calculate load score (used by Least Response Time)"""
        return self.metrics.active_connections * self.metrics.avg_response_time()
    
    def __repr__(self) -> str:
        return (f"Server({self.id}, conns={self.metrics.active_connections}, "
                f"total={self.metrics.total_requests})")


# ═══════════════════════════════════════════════════════════════
# LOAD BALANCING STRATEGIES
# ═══════════════════════════════════════════════════════════════

class LoadBalancingStrategy(ABC):
    """Abstract base class for load balancing algorithms"""
    
    @abstractmethod
    def select(self, servers: List[Server]) -> Optional[Server]:
        """Select next server for incoming request"""
        pass


class RoundRobin(LoadBalancingStrategy):
    """
    ALGORITHM: Round Robin
    Time: O(n) worst case (finding healthy server)
    Space: O(1)
    
    Maintains a rotating index, cycling through servers sequentially.
    """
    
    def __init__(self):
        self.current = 0
        self.lock = Lock()
    
    def select(self, servers: List[Server]) -> Optional[Server]:
        if not servers:
            return None
        
        with self.lock:
            n = len(servers)
            start = self.current
            
            # Find next healthy server
            for i in range(n):
                idx = (start + i) % n
                if servers[idx].is_healthy:
                    self.current = (idx + 1) % n
                    return servers[idx]
            
            return None  # No healthy servers


class WeightedRoundRobin(LoadBalancingStrategy):
    """
    ALGORITHM: Smooth Weighted Round Robin (Nginx algorithm)
    Time: O(n)
    Space: O(n) for current weights
    
    Distributes requests proportionally to server weights while
    avoiding clustering (consecutive requests to same server).
    """
    
    def __init__(self):
        self.current_weights: dict = {}
        self.lock = Lock()
    
    def select(self, servers: List[Server]) -> Optional[Server]:
        if not servers:
            return None
        
        with self.lock:
            # Calculate total weight of healthy servers
            total_weight = sum(s.weight for s in servers if s.is_healthy)
            if total_weight == 0:
                return None
            
            # Initialize current weights if needed
            for server in servers:
                if server.id not in self.current_weights:
                    self.current_weights[server.id] = 0
            
            # Find server with highest current weight
            best_server = None
            max_weight = float('-inf')
            
            for server in servers:
                if not server.is_healthy:
                    continue
                
                # Add effective weight
                self.current_weights[server.id] += server.weight
                
                # Track maximum
                if self.current_weights[server.id] > max_weight:
                    max_weight = self.current_weights[server.id]
                    best_server = server
            
            if best_server:
                # Decrease selected server's weight by total
                self.current_weights[best_server.id] -= total_weight
            
            return best_server


class LeastConnections(LoadBalancingStrategy):
    """
    ALGORITHM: Least Connections
    Time: O(n)
    Space: O(1)
    
    Routes to server with fewest active connections.
    Dynamic and adapts to varying request durations.
    """
    
    def select(self, servers: List[Server]) -> Optional[Server]:
        healthy = [s for s in servers if s.is_healthy]
        if not healthy:
            return None
        
        return min(healthy, key=lambda s: s.metrics.active_connections)


class LeastResponseTime(LoadBalancingStrategy):
    """
    ALGORITHM: Least Response Time
    Time: O(n)
    Space: O(1)
    
    Routes to server with lowest (response_time × active_connections).
    Combines historical performance with current load.
    """
    
    def select(self, servers: List[Server]) -> Optional[Server]:
        healthy = [s for s in servers if s.is_healthy]
        if not healthy:
            return None
        
        return min(healthy, key=lambda s: s.load_score())


class PowerOfTwoChoices(LoadBalancingStrategy):
    """
    ALGORITHM: Power of Two Choices
    Time: O(1)
    Space: O(1)
    
    Randomly samples 2 servers, picks the one with fewer connections.
    Achieves near-optimal load distribution with minimal overhead.
    
    Mathematical property: Reduces max load from O(log n / log log n)
    to O(log log n) - exponential improvement!
    """
    
    def select(self, servers: List[Server]) -> Optional[Server]:
        healthy = [s for s in servers if s.is_healthy]
        if not healthy:
            return None
        
        if len(healthy) == 1:
            return healthy[0]
        
        # Sample two random servers
        samples = random.sample(healthy, min(2, len(healthy)))
        
        # Return the one with fewer connections
        return min(samples, key=lambda s: s.metrics.active_connections)


class IPHash(LoadBalancingStrategy):
    """
    ALGORITHM: IP Hash (Session Affinity)
    Time: O(n) - scanning for healthy server
    Space: O(1)
    
    Routes same client IP to same server (session persistence).
    """
    
    def select(self, servers: List[Server], client_ip: str = None) -> Optional[Server]:
        healthy = [s for s in servers if s.is_healthy]
        if not healthy:
            return None
        
        if client_ip is None:
            return healthy[0]
        
        # Hash client IP to server index
        hash_value = hash(client_ip)
        idx = hash_value % len(healthy)
        return healthy[idx]


# ═══════════════════════════════════════════════════════════════
# HEALTH CHECKER - CIRCUIT BREAKER PATTERN
# ═══════════════════════════════════════════════════════════════

class HealthChecker:
    """
    Monitors server health using circuit breaker pattern.
    
    States:
    - HEALTHY: Server operational
    - SUSPECT: Consecutive failures detected
    - DOWN: Circuit open, server excluded
    """
    
    def __init__(self, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_counts: dict = {}
        self.last_check_time: dict = {}
    
    def check_server(self, server: Server, success: bool):
        """Update health status based on request result"""
        server_id = server.id
        
        if success:
            # Reset on success
            self.failure_counts[server_id] = 0
            if not server.is_healthy:
                print(f"✓ {server_id} recovered")
                server.is_healthy = True
        else:
            # Increment failure count
            count = self.failure_counts.get(server_id, 0) + 1
            self.failure_counts[server_id] = count
            
            # Mark down if threshold exceeded
            if count >= self.failure_threshold:
                if server.is_healthy:
                    print(f"✗ {server_id} marked DOWN (failures: {count})")
                    server.is_healthy = False
                    self.last_check_time[server_id] = time.time()
    
    def periodic_check(self, servers: List[Server]):
        """Attempt to recover servers after timeout"""
        current_time = time.time()
        
        for server in servers:
            if not server.is_healthy:
                last_check = self.last_check_time.get(server.id, 0)
                if current_time - last_check >= self.recovery_timeout:
                    # Attempt recovery (in production, this would be active probe)
                    print(f"⟳ Attempting to recover {server.id}")
                    server.is_healthy = True
                    self.failure_counts[server.id] = 0


# ═══════════════════════════════════════════════════════════════
# LOAD BALANCER - ORCHESTRATOR
# ═══════════════════════════════════════════════════════════════

class LoadBalancer:
    """
    Main load balancer orchestrating request distribution.
    """
    
    def __init__(self, servers: List[Server], strategy: LoadBalancingStrategy):
        self.servers = servers
        self.strategy = strategy
        self.health_checker = HealthChecker()
        self.total_requests = 0
    
    def handle_request(self, client_ip: str = None) -> Optional[str]:
        """Route incoming request to appropriate server"""
        self.total_requests += 1
        
        # Select server based on strategy
        server = self.strategy.select(self.servers)
        if not server:
            return None
        
        # Acquire server
        server.acquire()
        
        # Simulate processing (in production, this would be async)
        response_time = random.uniform(50, 200)  # Simulated latency
        success = random.random() > 0.05  # 5% failure rate
        
        # Release and update metrics
        server.release(response_time, success)
        self.health_checker.check_server(server, success)
        
        return server.id
    
    def print_stats(self):
        """Display current load balancer state"""
        print("\n" + "═" * 60)
        print("  LOAD BALANCER STATISTICS")
        print("═" * 60)
        print(f"Total Requests: {self.total_requests}\n")
        
        for server in self.servers:
            status = "✓ HEALTHY" if server.is_healthy else "✗ DOWN"
            m = server.metrics
            print(f"{status} | {server.id}")
            print(f"  Active: {m.active_connections} | "
                  f"Total: {m.total_requests} | "
                  f"Failed: {m.failed_requests}")
            print(f"  Avg Response: {m.avg_response_time():.1f}ms | "
                  f"Error Rate: {m.error_rate():.1%}")
            print()
        print("═" * 60)


# ═══════════════════════════════════════════════════════════════
# DEMONSTRATION
# ═══════════════════════════════════════════════════════════════

def main():
    print("═" * 60)
    print("  LOAD BALANCER IMPLEMENTATION - PYTHON")
    print("═" * 60)
    
    # Create server pool
    servers = [
        Server("Server-1", "192.168.1.1:8080", weight=1),
        Server("Server-2", "192.168.1.2:8080", weight=2),
        Server("Server-3", "192.168.1.3:8080", weight=1),
    ]
    
    # Test different strategies
    strategies = {
        "Round Robin": RoundRobin(),
        "Weighted Round Robin": WeightedRoundRobin(),
        "Least Connections": LeastConnections(),
        "Least Response Time": LeastResponseTime(),
        "Power of Two Choices": PowerOfTwoChoices(),
    }
    
    for name, strategy in strategies.items():
        print(f"\n\n📊 Testing {name.upper()}")
        print("─" * 60)
        
        # Reset servers
        test_servers = [
            Server("Server-1", "192.168.1.1:8080", weight=1),
            Server("Server-2", "192.168.1.2:8080", weight=2),
            Server("Server-3", "192.168.1.3:8080", weight=1),
        ]
        
        lb = LoadBalancer(test_servers, strategy)
        
        # Simulate requests
        for i in range(12):
            server_id = lb.handle_request()
            if server_id:
                print(f"  Request #{i+1:2d} → {server_id}")
        
        lb.print_stats()
    
    print("\n" + "═" * 60)
    print("  KEY INSIGHTS:")
    print("  • Weighted RR gives Server-2 (weight=2) more requests")
    print("  • Least Connections adapts to varying load")
    print("  • Power of Two achieves balance with minimal overhead")
    print("  • Each algorithm optimizes different objectives")
    print("═" * 60)


if __name__ == "__main__":
    main()

// Production-Grade Load Balancer in Go
// Demonstrates: Concurrency, goroutines, and idiomatic Go patterns

package main

import (
	"fmt"
	"hash/fnv"
	"math/rand"
	"sort"
	"sync"
	"sync/atomic"
	"time"
)

// ═══════════════════════════════════════════════════════════════
// CORE DATA STRUCTURES
// ═══════════════════════════════════════════════════════════════

// Server represents a backend server
type Server struct {
	ID                string
	Address           string
	Weight            int
	ActiveConnections int32 // atomic
	TotalRequests     int64 // atomic
	IsHealthy         int32 // atomic (1=healthy, 0=down)
	AvgResponseTime   int64 // atomic (microseconds)
	mu                sync.RWMutex
}

// NewServer creates a new server instance
func NewServer(id, address string, weight int) *Server {
	return &Server{
		ID:          id,
		Address:     address,
		Weight:      weight,
		IsHealthy:   1,
		AvgResponseTime: 100000, // 100ms default
	}
}

// Acquire increments active connections
func (s *Server) Acquire() {
	atomic.AddInt32(&s.ActiveConnections, 1)
	atomic.AddInt64(&s.TotalRequests, 1)
}

// Release decrements active connections and updates response time
func (s *Server) Release(responseTimeUs int64) {
	atomic.AddInt32(&s.ActiveConnections, -1)
	
	// Update exponential moving average: new = 0.2*current + 0.8*old
	oldAvg := atomic.LoadInt64(&s.AvgResponseTime)
	newAvg := (responseTimeUs / 5) + (oldAvg * 4 / 5)
	atomic.StoreInt64(&s.AvgResponseTime, newAvg)
}

// IsAvailable checks if server is healthy
func (s *Server) IsAvailable() bool {
	return atomic.LoadInt32(&s.IsHealthy) == 1
}

// LoadScore calculates load score (connections * avg_response_time)
func (s *Server) LoadScore() int64 {
	conns := int64(atomic.LoadInt32(&s.ActiveConnections))
	avgTime := atomic.LoadInt64(&s.AvgResponseTime)
	return conns * avgTime
}

// Stats returns current server statistics
func (s *Server) Stats() (active int32, total int64, healthy bool) {
	return atomic.LoadInt32(&s.ActiveConnections),
		atomic.LoadInt64(&s.TotalRequests),
		s.IsAvailable()
}

// ═══════════════════════════════════════════════════════════════
// LOAD BALANCING STRATEGIES
// ═══════════════════════════════════════════════════════════════

// LoadBalancingStrategy interface
type LoadBalancingStrategy interface {
	Select(servers []*Server) *Server
}

// RoundRobin implements round-robin algorithm
type RoundRobin struct {
	current uint32
}

func NewRoundRobin() *RoundRobin {
	return &RoundRobin{}
}

func (rr *RoundRobin) Select(servers []*Server) *Server {
	n := len(servers)
	if n == 0 {
		return nil
	}

	// Find next healthy server
	start := atomic.AddUint32(&rr.current, 1) - 1
	for i := 0; i < n; i++ {
		idx := int((start + uint32(i)) % uint32(n))
		if servers[idx].IsAvailable() {
			return servers[idx]
		}
	}

	return nil // No healthy servers
}

// WeightedRoundRobin implements smooth weighted round-robin (Nginx algorithm)
type WeightedRoundRobin struct {
	currentWeights map[string]int
	mu             sync.Mutex
}

func NewWeightedRoundRobin() *WeightedRoundRobin {
	return &WeightedRoundRobin{
		currentWeights: make(map[string]int),
	}
}

func (wrr *WeightedRoundRobin) Select(servers []*Server) *Server {
	wrr.mu.Lock()
	defer wrr.mu.Unlock()

	// Calculate total weight
	totalWeight := 0
	for _, s := range servers {
		if s.IsAvailable() {
			totalWeight += s.Weight
		}
	}

	if totalWeight == 0 {
		return nil
	}

	// Find server with max current weight
	var best *Server
	maxWeight := int(^uint(0) >> 1) * -1 // Min int

	for _, s := range servers {
		if !s.IsAvailable() {
			continue
		}

		// Initialize if needed
		if _, exists := wrr.currentWeights[s.ID]; !exists {
			wrr.currentWeights[s.ID] = 0
		}

		// Add effective weight
		wrr.currentWeights[s.ID] += s.Weight

		// Track maximum
		if wrr.currentWeights[s.ID] > maxWeight {
			maxWeight = wrr.currentWeights[s.ID]
			best = s
		}
	}

	// Decrease chosen server's weight
	if best != nil {
		wrr.currentWeights[best.ID] -= totalWeight
	}

	return best
}

// LeastConnections selects server with minimum active connections
type LeastConnections struct{}

func NewLeastConnections() *LeastConnections {
	return &LeastConnections{}
}

func (lc *LeastConnections) Select(servers []*Server) *Server {
	var best *Server
	minConns := int32(^uint32(0) >> 1) // Max int32

	for _, s := range servers {
		if !s.IsAvailable() {
			continue
		}

		conns := atomic.LoadInt32(&s.ActiveConnections)
		if conns < minConns {
			minConns = conns
			best = s
		}
	}

	return best
}

// LeastResponseTime selects based on response_time × connections
type LeastResponseTime struct{}

func NewLeastResponseTime() *LeastResponseTime {
	return &LeastResponseTime{}
}

func (lrt *LeastResponseTime) Select(servers []*Server) *Server {
	var best *Server
	minScore := int64(^uint64(0) >> 1) // Max int64

	for _, s := range servers {
		if !s.IsAvailable() {
			continue
		}

		score := s.LoadScore()
		if score < minScore {
			minScore = score
			best = s
		}
	}

	return best
}

// PowerOfTwo implements power-of-two-choices algorithm
type PowerOfTwo struct{}

func NewPowerOfTwo() *PowerOfTwo {
	return &PowerOfTwo{}
}

func (p2 *PowerOfTwo) Select(servers []*Server) *Server {
	// Collect healthy servers
	healthy := make([]*Server, 0, len(servers))
	for _, s := range servers {
		if s.IsAvailable() {
			healthy = append(healthy, s)
		}
	}

	n := len(healthy)
	if n == 0 {
		return nil
	}
	if n == 1 {
		return healthy[0]
	}

	// Sample two random servers
	idx1 := rand.Intn(n)
	idx2 := rand.Intn(n)
	for idx2 == idx1 {
		idx2 = rand.Intn(n)
	}

	s1, s2 := healthy[idx1], healthy[idx2]

	// Return the one with fewer connections
	if atomic.LoadInt32(&s1.ActiveConnections) <= atomic.LoadInt32(&s2.ActiveConnections) {
		return s1
	}
	return s2
}

// ═══════════════════════════════════════════════════════════════
// CONSISTENT HASHING - Advanced Algorithm
// ═══════════════════════════════════════════════════════════════

// ConsistentHash implements consistent hashing with virtual nodes
type ConsistentHash struct {
	ring           map[uint32]string // hash -> server ID
	sortedKeys     []uint32
	virtualNodes   int
	mu             sync.RWMutex
	serverMap      map[string]*Server
}

func NewConsistentHash(virtualNodes int) *ConsistentHash {
	return &ConsistentHash{
		ring:         make(map[uint32]string),
		virtualNodes: virtualNodes,
		serverMap:    make(map[string]*Server),
	}
}

// AddServer adds a server to the hash ring
func (ch *ConsistentHash) AddServer(server *Server) {
	ch.mu.Lock()
	defer ch.mu.Unlock()

	ch.serverMap[server.ID] = server

	// Create virtual nodes
	for i := 0; i < ch.virtualNodes; i++ {
		hash := ch.hash(fmt.Sprintf("%s:%d", server.ID, i))
		ch.ring[hash] = server.ID
		ch.sortedKeys = append(ch.sortedKeys, hash)
	}

	// Sort keys for binary search
	sort.Slice(ch.sortedKeys, func(i, j int) bool {
		return ch.sortedKeys[i] < ch.sortedKeys[j]
	})
}

// Select finds server for given key using consistent hashing
func (ch *ConsistentHash) Select(key string) *Server {
	ch.mu.RLock()
	defer ch.mu.RUnlock()

	if len(ch.sortedKeys) == 0 {
		return nil
	}

	hash := ch.hash(key)

	// Binary search for first key >= hash
	idx := sort.Search(len(ch.sortedKeys), func(i int) bool {
		return ch.sortedKeys[i] >= hash
	})

	// Wrap around if needed
	if idx == len(ch.sortedKeys) {
		idx = 0
	}

	serverID := ch.ring[ch.sortedKeys[idx]]
	return ch.serverMap[serverID]
}

func (ch *ConsistentHash) hash(key string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(key))
	return h.Sum32()
}

// ═══════════════════════════════════════════════════════════════
// LOAD BALANCER
// ═══════════════════════════════════════════════════════════════

// LoadBalancer orchestrates request distribution
type LoadBalancer struct {
	servers  []*Server
	strategy LoadBalancingStrategy
}

func NewLoadBalancer(servers []*Server, strategy LoadBalancingStrategy) *LoadBalancer {
	return &LoadBalancer{
		servers:  servers,
		strategy: strategy,
	}
}

// HandleRequest routes a request to appropriate server
func (lb *LoadBalancer) HandleRequest() (string, error) {
	server := lb.strategy.Select(lb.servers)
	if server == nil {
		return "", fmt.Errorf("no healthy servers available")
	}

	server.Acquire()

	// Simulate processing
	responseTime := int64(rand.Intn(150)+50) * 1000 // 50-200ms in microseconds
	time.Sleep(time.Duration(responseTime/1000) * time.Microsecond) // Brief actual delay

	server.Release(responseTime)

	return server.ID, nil
}

// PrintStats displays current statistics
func (lb *LoadBalancer) PrintStats() {
	fmt.Println("\n" + strings("═", 60))
	fmt.Println("  LOAD BALANCER STATISTICS")
	fmt.Println(strings("═", 60))

	for _, s := range lb.servers {
		active, total, healthy := s.Stats()
		status := "✓"
		if !healthy {
			status = "✗"
		}
		fmt.Printf("%s %s: %d active | %d total\n",
			status, s.ID, active, total)
	}

	fmt.Println(strings("═", 60))
}

func strings(s string, n int) string {
	result := ""
	for i := 0; i < n; i++ {
		result += s
	}
	return result
}

// ═══════════════════════════════════════════════════════════════
// DEMONSTRATION
// ═══════════════════════════════════════════════════════════════

func main() {
	rand.Seed(time.Now().UnixNano())

	fmt.Println(strings("═", 60))
	fmt.Println("  LOAD BALANCER IMPLEMENTATION - GO")
	fmt.Println(strings("═", 60))

	// Create server pool
	servers := []*Server{
		NewServer("Server-1", "192.168.1.1:8080", 1),
		NewServer("Server-2", "192.168.1.2:8080", 2),
		NewServer("Server-3", "192.168.1.3:8080", 1),
	}

	// Test Round Robin
	fmt.Println("\n📊 Testing ROUND ROBIN")
	fmt.Println(strings("─", 60))
	lb := NewLoadBalancer(servers, NewRoundRobin())

	for i := 1; i <= 6; i++ {
		if serverID, err := lb.HandleRequest(); err == nil {
			fmt.Printf("Request #%d → %s\n", i, serverID)
		}
	}
	lb.PrintStats()

	// Test Weighted Round Robin
	fmt.Println("\n📊 Testing WEIGHTED ROUND ROBIN")
	fmt.Println(strings("─", 60))
	servers2 := []*Server{
		NewServer("Server-1", "192.168.1.1:8080", 1),
		NewServer("Server-2", "192.168.1.2:8080", 2),
		NewServer("Server-3", "192.168.1.3:8080", 1),
	}
	lb2 := NewLoadBalancer(servers2, NewWeightedRoundRobin())

	for i := 1; i <= 8; i++ {
		if serverID, err := lb2.HandleRequest(); err == nil {
			fmt.Printf("Request #%d → %s\n", i, serverID)
		}
	}
	lb2.PrintStats()

	// Test Consistent Hashing
	fmt.Println("\n📊 Testing CONSISTENT HASHING")
	fmt.Println(strings("─", 60))
	ch := NewConsistentHash(150) // 150 virtual nodes per server
	for _, s := range servers {
		ch.AddServer(s)
	}

	// Simulate requests from different client IPs
	clientIPs := []string{
		"192.168.1.100",
		"192.168.1.101",
		"192.168.1.102",
		"192.168.1.103",
	}

	fmt.Println("Client IP routing (session affinity):")
	for _, ip := range clientIPs {
		server := ch.Select(ip)
		if server != nil {
			fmt.Printf("  %s → %s\n", ip, server.ID)
		}
	}

	// Verify same IP routes to same server
	fmt.Println("\nVerifying consistency (same IP should route to same server):")
	for i := 0; i < 3; i++ {
		server := ch.Select(clientIPs[0])
		if server != nil {
			fmt.Printf("  Attempt #%d: %s → %s\n", i+1, clientIPs[0], server.ID)
		}
	}

	fmt.Println("\n" + strings("═", 60))
	fmt.Println("  KEY OBSERVATIONS:")
	fmt.Println("  • Go's atomics enable lock-free operations")
	fmt.Println("  • Goroutines can scale this to thousands of concurrent requests")
	fmt.Println("  • Consistent hashing maintains session affinity")
	fmt.Println(strings("═", 60))
}   