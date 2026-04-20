**System Design (Core Topics to Master)**

These are the foundational building blocks for designing scalable, reliable systems (drawn from standard roadmaps like roadmap.sh and common interview prep resources). Focus on understanding trade-offs, when to apply each, and real-world examples.

- **Core Principles & Trade-offs**
  - Performance vs Scalability (Latency vs Throughput)
  - Availability vs Consistency
  - CAP Theorem (AP vs CP systems) + PACELC extension
  - Consistency patterns: Weak, Eventual, Strong
  - Availability patterns: Failover (Active-Active, Active-Passive), Replication (Master-Slave, Master-Master)
  - Availability metrics (nines: 99.9%, 99.99%, etc.) and calculations (parallel vs sequential)
  - Idempotency and backpressure

- **Networking & Traffic Management**
  - Domain Name System (DNS)
  - Load Balancers (vs Reverse Proxy; Layer 4 vs Layer 7; algorithms like Round Robin, Least Connections, Consistent Hashing)
  - Horizontal Scaling (Application Layer, Microservices, Service Discovery)
  - Content Delivery Networks (CDNs: Push vs Pull)

- **Data Management & Storage**
  - Databases: SQL vs NoSQL (RDBMS, Key-Value, Document, Wide Column, Graph)
  - Replication strategies
  - Sharding / Partitioning / Federation
  - Denormalization and SQL tuning
  - Indexing, Materialized Views, Event Sourcing, CQRS

- **Caching & Performance Optimization**
  - Caching strategies: Cache-Aside, Write-Through, Write-Behind, Refresh-Ahead
  - Caching layers: Client, CDN, Web Server, Database, Application
  - Performance antipatterns (Busy Database/Frontend, Chatty I/O, No Caching, Retry Storm, Synchronous I/O, etc.)

- **Asynchronous Processing & Communication**
  - Task Queues and Message Queues (backpressure handling)
  - Communication protocols: HTTP, TCP, UDP, RPC, REST, gRPC, GraphQL
  - Background jobs (Event-Driven vs Schedule-Driven)

- **Monitoring, Observability & Reliability**
  - Monitoring types: Health, Availability, Performance, Security, Usage
  - Instrumentation, Visualization & Alerts
  - Design patterns: Circuit Breaker, Bulkhead, Retry, Throttling, Leader Election, Rate Limiting

- **Key Design Patterns (Cloud & Reliability)**
  - Messaging: Publisher/Subscriber, Priority Queue, Competing Consumers, Choreography, Claim Check, Async Request-Reply
  - Data: Sharding, Cache-Aside, Valet Key, Static Content Hosting
  - Implementation: Strangler Fig, Sidecar, Gateway (Routing, Aggregation, Offloading), Backends for Frontend (BFF), Anti-Corruption Layer
  - Reliability: Deployment Stamps, Geodes, Health Endpoint Monitoring, Queue-Based Load Leveling, Compensating Transaction

**Related / Overlapping Topics & Concepts**

These tie everything together and appear frequently in advanced discussions:
- Microservices architecture, Service mesh
- Event-driven architecture, Message brokers (Kafka concepts)
- Rate limiting, API gateways
- Security patterns (Gatekeeper, Valet Key)
- Trade-off analysis (always prioritize requirements first)
- Real-world system examples (design Twitter/Instagram/Netflix/Uber as practice)

Master these by starting with fundamentals (CAP, load balancing, caching, databases), then practicing full system designs (e.g., "Design a URL shortener" or "Design TikTok"), and reading case studies from books like *Designing Data-Intensive Applications* (Martin Kleppmann). Focus on *why* choices are made and trade-offs rather than memorizing tools. This list covers ~95% of what appears in interviews, roadmaps, and real-world scalable system work.

# Complete System Design, Distributed Systems & Core Infrastructure Guide
### A World-Class Reference for the Top 1% Engineer

---

> **How to use this guide:** Read linearly. Every concept builds on the previous. When you encounter a term, its definition appears before or immediately at first use. Diagrams use ASCII art. Code examples are in Rust, Go, and C.

---

## TABLE OF CONTENTS

```
PART I   — SYSTEM DESIGN FUNDAMENTALS
PART II  — NETWORKING DEEP DIVE
PART III — DISTRIBUTED SYSTEMS
PART IV  — STORAGE & DATABASES
PART V   — MESSAGING & STREAMING
PART VI  — LINUX KERNEL CONCEPTS
PART VII — CLOUD NATIVE
PART VIII— CLOUD & NETWORK SECURITY
PART IX  — OBSERVABILITY & RELIABILITY
PART X   — ARCHITECTURE PATTERNS
```

---

# PART I — SYSTEM DESIGN FUNDAMENTALS

---

## 1. What Is System Design?

System design is the process of defining the **architecture**, **components**, **modules**, **interfaces**, and **data flows** of a system to satisfy specified requirements.

Think of it like designing a city:
- Roads = Networks
- Buildings = Servers
- Water/Electricity = Infrastructure Services
- Zoning Laws = Policies & Security
- Emergency Services = Fault Tolerance

```
                        SYSTEM DESIGN UNIVERSE
┌──────────────────────────────────────────────────────────────────────┐
│                                                                      │
│   CLIENT(S)   ──►  NETWORK  ──►  LOAD BALANCER  ──►  SERVERS       │
│                                        │                             │
│                               ┌────────┼────────┐                   │
│                               ▼        ▼        ▼                   │
│                            App-1    App-2    App-3                   │
│                               │        │        │                   │
│                               └────────┼────────┘                   │
│                                        │                             │
│                            ┌───────────┼──────────┐                 │
│                            ▼           ▼          ▼                 │
│                          Cache       Queue      Database             │
│                            │                      │                  │
│                            └──────────────────────┘                 │
│                                       │                              │
│                                  Monitoring                          │
└──────────────────────────────────────────────────────────────────────┘
```

---

## 2. The Eight Fallacies of Distributed Computing

**What is a fallacy?** A false assumption that seems true at first.

These were identified by Peter Deutsch and James Gosling. Every engineer must internalize them:

```
┌─────┬──────────────────────────────────┬────────────────────────────┐
│  #  │ Fallacy                          │ Reality                    │
├─────┼──────────────────────────────────┼────────────────────────────┤
│  1  │ Network is reliable              │ Packets drop, links fail   │
│  2  │ Latency is zero                  │ Speed of light is a limit  │
│  3  │ Bandwidth is infinite            │ Bandwidth costs money      │
│  4  │ Network is secure                │ Always assume breach       │
│  5  │ Topology doesn't change          │ Nodes join and leave       │
│  6  │ There is one administrator       │ Many teams, many policies  │
│  7  │ Transport cost is zero           │ Serialization costs CPU    │
│  8  │ Network is homogeneous           │ Mixed hardware everywhere  │
└─────┴──────────────────────────────────┴────────────────────────────┘
```

---

## 3. Scalability

**What is Scalability?** The ability of a system to handle growing amounts of work by adding resources.

### 3.1 Vertical Scaling (Scale Up)

Add more power to an existing machine (more RAM, more CPU, faster disk).

```
BEFORE                          AFTER
┌────────────┐                  ┌────────────────────┐
│  Server    │      ──►         │  Bigger Server     │
│  2 CPU     │                  │  32 CPU            │
│  8 GB RAM  │                  │  256 GB RAM        │
│  HDD       │                  │  NVMe SSD          │
└────────────┘                  └────────────────────┘

Pros: Simple, no code change
Cons: Has a hard ceiling, single point of failure, expensive
```

### 3.2 Horizontal Scaling (Scale Out)

Add more machines to distribute load.

```
BEFORE                          AFTER
┌────────────┐                  ┌─────┐ ┌─────┐ ┌─────┐
│  Server    │      ──►         │ S1  │ │ S2  │ │ S3  │
│            │                  └──┬──┘ └──┬──┘ └──┬──┘
└────────────┘                     └───────┼───────┘
                                           │
                                     Load Balancer
                                           │
                                        Clients

Pros: No ceiling, fault tolerant, cheaper commodity hardware
Cons: Complexity, need distributed coordination
```

### 3.3 Scalability Dimensions

```
┌──────────────────────────────────────────────────────┐
│             SCALABILITY DIMENSIONS                   │
│                                                      │
│   Load Scalability    - handle more requests/sec     │
│   Geographic Scalability - serve users worldwide     │
│   Administrative Scalability - many users/teams      │
│   Functional Scalability - add features easily       │
└──────────────────────────────────────────────────────┘
```

---

## 4. Latency vs Throughput vs Bandwidth

**These three are the "vital signs" of a system.**

### Definitions

- **Latency**: Time it takes for a single request to complete (measured in ms, µs)
- **Throughput**: Number of requests/operations completed per second (RPS, QPS, TPS)
- **Bandwidth**: Maximum amount of data that can be transferred per unit time (Mbps, Gbps)

```
ANALOGY: A highway

Bandwidth  = Number of lanes (capacity)
Throughput = Actual cars passing per hour (actual usage)
Latency    = Time for ONE car to travel A → B

┌──────────────────────────────────────────────────────┐
│  A ══════════════════════════════════════ B          │
│  │← ─ ─ ─ ─ ─ ─ latency ─ ─ ─ ─ ─ ─ ─►│          │
│  ║                                       ║          │
│  ║ ←────────── bandwidth ───────────►   ║          │
└──────────────────────────────────────────────────────┘
```

### Latency Numbers Every Engineer Must Know

```
┌───────────────────────────────────────────────────────────────┐
│  Operation                          │ Latency                 │
├─────────────────────────────────────┼─────────────────────────┤
│  L1 cache reference                 │ ~0.5 ns                 │
│  Branch misprediction               │ ~5 ns                   │
│  L2 cache reference                 │ ~7 ns                   │
│  Mutex lock/unlock                  │ ~25 ns                  │
│  Main memory reference (RAM)        │ ~100 ns                 │
│  Compress 1KB with Snappy           │ ~3,000 ns (3 µs)        │
│  Send 2KB over 1 Gbps network       │ ~20,000 ns (20 µs)      │
│  SSD random read                    │ ~150,000 ns (150 µs)    │
│  Read 1MB from RAM                  │ ~250,000 ns (250 µs)    │
│  Round trip within same datacenter  │ ~500,000 ns (0.5 ms)    │
│  Read 1MB from SSD                  │ ~1,000,000 ns (1 ms)    │
│  HDD seek                           │ ~10 ms                  │
│  Send packet CA → Netherlands → CA  │ ~150 ms                 │
│  Read 1MB from HDD                  │ ~20 ms                  │
└───────────────────────────────────────────────────────────────┘

Mental model: RAM is ~200x faster than SSD, SSD is ~100x faster than HDD
```

---

## 5. Availability

**What is Availability?** The percentage of time a system is operational and accessible.

**Formula:**
```
Availability = Uptime / (Uptime + Downtime)
```

### The "Nines" of Availability

```
┌──────────────────────────────────────────────────────────────────┐
│ SLA         │ Downtime/Year │ Downtime/Month │ Downtime/Week     │
├─────────────┼───────────────┼────────────────┼───────────────────┤
│ 90%         │ 36.5 days     │ 72 hours       │ 16.8 hours        │
│ 99%         │ 3.65 days     │ 7.2 hours      │ 1.68 hours        │
│ 99.9%       │ 8.77 hours    │ 43.8 min       │ 10.1 min          │
│ 99.99%      │ 52.6 min      │ 4.38 min       │ 1.01 min          │
│ 99.999%     │ 5.26 min      │ 26.3 sec       │ 6.05 sec          │
│ 99.9999%    │ 31.5 sec      │ 2.63 sec       │ 0.605 sec         │
└──────────────────────────────────────────────────────────────────┘

SLA = Service Level Agreement (the contract promise)
SLO = Service Level Objective (the internal target)
SLI = Service Level Indicator (what you actually measure)
```

### Availability in Series vs Parallel

```
SERIES (weakest link wins — multiply):
A (99.9%) ──► B (99.9%) ──► C (99.9%)
Combined = 0.999 × 0.999 × 0.999 = 99.7%

PARALLEL (redundancy wins — probability of ALL failing):
       ┌──► A (99.9%) ──┐
──────►│                 ├──►
       └──► B (99.9%) ──┘
Combined = 1 - (0.001 × 0.001) = 99.9999%
```

---

## 6. Reliability vs Availability vs Durability

```
┌─────────────────────────────────────────────────────────────────┐
│  Term          │ Question it answers                            │
├────────────────┼────────────────────────────────────────────────┤
│  Availability  │ Is the system UP right now?                   │
│  Reliability   │ Does it work CORRECTLY and CONSISTENTLY?      │
│  Durability    │ Is my DATA safe even if crashes happen?        │
└─────────────────────────────────────────────────────────────────┘

Example:
  A system can be AVAILABLE but UNRELIABLE (returns wrong results)
  A system can be DOWN but still DURABLE (data not lost)
```

---

## 7. CAP Theorem

**The most important theorem in distributed systems.**

**What is CAP?**

- **C** = Consistency: Every read gets the most recent write (or an error)
- **A** = Availability: Every request gets a response (not necessarily the latest data)
- **P** = Partition Tolerance: System continues operating even if network messages are dropped

**The theorem**: In the presence of a network partition, a distributed system must choose between Consistency and Availability. You cannot have all three simultaneously.

```
                        CAP TRIANGLE

                        Consistency
                            /\
                           /  \
                          /    \
                         /  CA  \
                        /--------\
                       / CP  | AP \
                      /──────────── \
               Partition ──────── Availability
               Tolerance

CA = No partition tolerance (single-node databases: MySQL, PostgreSQL)
CP = Consistent under partitions (HBase, Zookeeper, MongoDB)
AP = Available under partitions (Cassandra, CouchDB, Riak)
```

**Mental Model:**
```
Imagine two nodes (A, B) storing a counter. Network splits:

CONSISTENCY choice: refuse to serve stale data
  Client reads B → B says "I can't answer, A is unreachable"
  ✓ Consistent  ✗ Available

AVAILABILITY choice: serve whatever you have
  Client reads B → B says "counter is 5" (A has 6, partition happened)
  ✗ Consistent  ✓ Available
```

---

## 8. PACELC Theorem

**An extension to CAP** that covers the non-partitioned case.

```
If Partition:
  Choose between Availability vs Consistency

Else (no partition):
  Choose between Latency vs Consistency

┌────────────────────────────────────────────────────────┐
│  Database     │ Partition case │ Normal case           │
├───────────────┼────────────────┼───────────────────────┤
│  DynamoDB     │ PA             │ EL (low latency)      │
│  Cassandra    │ PA             │ EL                    │
│  BigTable     │ PC             │ EL                    │
│  HBase        │ PC             │ EC (consistent)       │
│  MySQL        │ PC             │ EC                    │
└────────────────────────────────────────────────────────┘
```

---

## 9. Consistency Models

**What is a Consistency Model?** A contract between the system and the programmer defining what values reads can return.

From strongest (safest) to weakest (fastest):

```
STRONG CONSISTENCY
    │
    │   Linearizability  — reads see MOST RECENT write globally
    │   Sequential       — all nodes see operations in SAME ORDER
    │   Causal           — causally related ops are in order
    │   Read-your-writes — you always see your own latest write
    │   Monotonic reads  — you never see older data twice
    │   Eventual         — eventually all nodes will agree
    │
    ▼
WEAK CONSISTENCY
```

### Linearizability (Strongest)

```
Time ──────────────────────────────────────────────►
       write(x=1)
         ├────────────────────┤
                                read(x) must return 1
                                      ├──┤
```

### Eventual Consistency

```
Node A:  write(x=5) ──────────────────────────────► propagates later
Node B:             read(x) → 3  ── ... ──  read(x) → 5  ✓ (eventually correct)
```

---

## 10. Load Balancing

**What is a Load Balancer?** A component that distributes incoming traffic across multiple servers.

```
                    ┌─────────────────┐
     requests ──►   │  Load Balancer  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
         ┌────────┐     ┌────────┐     ┌────────┐
         │ App-1  │     │ App-2  │     │ App-3  │
         └────────┘     └────────┘     └────────┘
```

### Load Balancing Algorithms

```
┌─────────────────────┬────────────────────────────────────────────┐
│  Algorithm          │ How it works                               │
├─────────────────────┼────────────────────────────────────────────┤
│  Round Robin        │ A→B→C→A→B→C (sequential rotation)         │
│  Weighted RR        │ A gets 50%, B 30%, C 20%                  │
│  Least Connections  │ Send to server with fewest active conns    │
│  IP Hash            │ hash(client_ip) % N → same server always  │
│  Random             │ Randomly pick a server                     │
│  Least Response     │ Send to fastest responding server          │
│  Resource Based     │ Agent reports CPU/RAM → route accordingly  │
└─────────────────────┴────────────────────────────────────────────┘
```

### L4 vs L7 Load Balancing

```
L4 (Transport Layer) — works with TCP/UDP packets
  Fast, no application awareness
  Example: AWS NLB (Network Load Balancer)

L7 (Application Layer) — works with HTTP headers, cookies, URLs
  Slow(er), but intelligent routing
  Example: AWS ALB (Application Load Balancer), NGINX, HAProxy

L7 can do:
  /api  ──► API servers
  /img  ──► Image servers
  Cookie: user_id → Sticky session routing
```

---

## 11. Caching

**What is a Cache?** A fast, temporary data store that holds frequently accessed data to reduce latency and database load.

**The Core Insight:** 80% of requests often hit 20% of data. Cache that 20%.

```
WITHOUT CACHE:                          WITH CACHE:
Client → App → DB → App → Client       Client → App → Cache (HIT!)
         (100ms)                                  (1ms)
                                                   │
                                                   └─(MISS)──► DB ──► Cache ──► Client
```

### Cache Levels

```
┌───────────────────────────────────────────────────────────────────┐
│  Level           │ Location              │ Size    │ Speed        │
├──────────────────┼───────────────────────┼─────────┼──────────────┤
│  CPU L1 Cache    │ Inside CPU core       │ KB      │ ~0.5 ns      │
│  CPU L2 Cache    │ Near CPU core         │ MB      │ ~7 ns        │
│  CPU L3 Cache    │ Shared between cores  │ MB-GB   │ ~40 ns       │
│  Application     │ In-process (HashMap)  │ GB      │ ~100 ns      │
│  Distributed     │ Redis, Memcached      │ GB-TB   │ ~1 ms        │
│  CDN             │ Edge servers globally │ TB      │ ~10 ms       │
│  Database buffer │ DB internal cache     │ GB      │ ~1 ms        │
└───────────────────────────────────────────────────────────────────┘
```

### Cache Eviction Policies

**What is Eviction?** When the cache is full, old entries must be removed to make space.

```
┌─────────────────────────────────────────────────────────────┐
│  Policy   │ Description                                     │
├───────────┼─────────────────────────────────────────────────┤
│  LRU      │ Least Recently Used — evict the oldest access   │
│  LFU      │ Least Frequently Used — evict least accessed    │
│  FIFO     │ First In First Out — evict the oldest entry     │
│  Random   │ Evict a random entry                            │
│  TTL      │ Time To Live — evict after fixed time expires   │
│  ARC      │ Adaptive Replacement Cache (LRU+LFU hybrid)     │
└─────────────────────────────────────────────────────────────┘

LRU Example:
Cache size = 3
Access: A, B, C, D
  [A]       ← A added
  [A,B]     ← B added
  [A,B,C]   ← C added (full)
  [B,C,D]   ← D added, A evicted (least recently used)
```

### Cache Write Policies

```
WRITE-THROUGH:
  Write → Cache AND DB simultaneously
  ✓ Consistent  ✗ Higher latency on writes

  Client ──►write──► Cache ──►write──► DB

WRITE-BEHIND (Write-Back):
  Write → Cache first, DB updated asynchronously
  ✓ Low write latency  ✗ Risk of data loss if cache crashes

  Client ──►write──► Cache ──(async)──► DB

WRITE-AROUND:
  Write → DB directly, bypassing cache
  ✓ Cache only for reads  ✗ Cache miss on first read

  Client ──►write──► DB (cache not updated)
  Client ──►read───► Cache MISS → DB → Cache
```

### Cache Patterns

```
CACHE-ASIDE (Lazy Loading):
  App checks cache → HIT: return data
                  → MISS: fetch DB → store in cache → return data

  Application controls cache population. Most common pattern.

READ-THROUGH:
  App asks cache → cache checks itself → if MISS: cache fetches DB
  Cache is transparent to application.

REFRESH-AHEAD:
  Cache proactively refreshes entries before they expire.
  Reduces latency spikes but may cache stale data.
```

### Cache Problems

```
┌──────────────────────────────────────────────────────────────────┐
│  Problem          │ Description                │ Solution        │
├───────────────────┼────────────────────────────┼─────────────────┤
│  Cache Stampede   │ Many requests hit DB when  │ Mutex lock on   │
│  (Thundering Herd)│ cache expires              │ cache miss      │
│                   │                            │ Probabilistic   │
│                   │                            │ early refresh   │
├───────────────────┼────────────────────────────┼─────────────────┤
│  Cache Penetration│ Requests for non-existent  │ Bloom filter    │
│                   │ keys bypass cache          │ Cache null val  │
├───────────────────┼────────────────────────────┼─────────────────┤
│  Cache Avalanche  │ Many cache entries expire  │ Randomize TTLs  │
│                   │ at the same time           │ Warm up slowly  │
├───────────────────┼────────────────────────────┼─────────────────┤
│  Cache Pollution  │ Low-value data fills cache │ LFU eviction    │
└───────────────────┴────────────────────────────┴─────────────────┘
```

---

## 12. Content Delivery Networks (CDN)

**What is a CDN?** A geographically distributed network of servers (called "edge nodes" or "PoPs — Points of Presence") that cache and serve static content close to users.

```
WITHOUT CDN:
  User (Tokyo) ──────────────────────────► Origin Server (NYC)
                     ~150ms RTT

WITH CDN:
  User (Tokyo) ──► CDN Edge (Tokyo) ──────(cache hit!)──► User
                      ~5ms RTT
                                   ──(miss)──► Origin (NYC) → cache

CDN TOPOLOGY:
  ┌──────────────────────────────────────────────────────┐
  │                    Origin Server                     │
  │                         │                            │
  │         ┌───────────────┼───────────────┐           │
  │         ▼               ▼               ▼           │
  │      Edge (NY)      Edge (London)    Edge (Tokyo)   │
  │         │               │               │           │
  │      Users-US        Users-EU        Users-APAC     │
  └──────────────────────────────────────────────────────┘

What CDN caches:
  Static assets: images, CSS, JS, fonts, videos
  Dynamic content: some CDNs cache API responses too (edge compute)

Push CDN vs Pull CDN:
  Push: You upload content to CDN proactively
  Pull: CDN fetches from origin on first request, then caches
```

---

## 13. Proxies

**What is a Proxy?** An intermediary server between client and server.

```
FORWARD PROXY:
  (Client knows about proxy, server doesn't)
  Client ──► Forward Proxy ──► Internet ──► Server
  Use: VPN, content filtering, corporate networks

REVERSE PROXY:
  (Server knows about proxy, client doesn't)
  Client ──► Internet ──► Reverse Proxy ──► Server(s)
  Use: Load balancing, SSL termination, caching, security

  REVERSE PROXY FUNCTIONS:
  ┌────────────────────────────────────────────────────┐
  │  SSL Termination   — decrypt HTTPS here, HTTP back │
  │  Load Balancing    — distribute to backend         │
  │  Caching           — serve cached responses        │
  │  Rate Limiting     — throttle abusive clients      │
  │  Authentication    — centralize auth here          │
  │  Compression       — gzip responses                │
  │  Logging           — single point for access logs  │
  └────────────────────────────────────────────────────┘
```

---

## 14. API Design and Patterns

**What is an API?** Application Programming Interface — a contract that defines how software components communicate.

### REST (Representational State Transfer)

```
REST PRINCIPLES:
  1. Client-Server architecture
  2. Stateless (each request is self-contained)
  3. Cacheable
  4. Uniform Interface
  5. Layered System
  6. Code on Demand (optional)

HTTP METHODS:
  GET    /users          → list users        (safe, idempotent)
  GET    /users/123      → get user 123      (safe, idempotent)
  POST   /users          → create user       (not idempotent)
  PUT    /users/123      → replace user 123  (idempotent)
  PATCH  /users/123      → partial update    (not idempotent)
  DELETE /users/123      → delete user 123   (idempotent)

IDEMPOTENT: Calling it once or 10 times has the same result.
```

### HTTP Status Codes

```
┌────────────────────────────────────────────────────────┐
│  Range  │ Meaning     │ Examples                       │
├─────────┼─────────────┼────────────────────────────────┤
│  2xx    │ Success     │ 200 OK, 201 Created, 204 Empty │
│  3xx    │ Redirect    │ 301 Moved, 302 Found           │
│  4xx    │ Client Err  │ 400 Bad Req, 401 Unauth,       │
│         │             │ 403 Forbidden, 404 Not Found   │
│         │             │ 429 Too Many Requests          │
│  5xx    │ Server Err  │ 500 Internal, 502 Bad Gateway  │
│         │             │ 503 Unavailable, 504 Timeout   │
└─────────┴─────────────┴────────────────────────────────┘
```

### gRPC

**What is gRPC?** Google Remote Procedure Call — a high-performance RPC framework using Protocol Buffers.

```
REST vs gRPC comparison:
┌────────────────────────────────────────────────────────────────┐
│  Feature        │ REST                  │ gRPC                 │
├─────────────────┼───────────────────────┼──────────────────────┤
│  Protocol       │ HTTP/1.1              │ HTTP/2               │
│  Format         │ JSON (text)           │ Protobuf (binary)    │
│  Size           │ Large                 │ ~5-10x smaller       │
│  Speed          │ Slower                │ Faster               │
│  Streaming      │ Limited               │ Full bidirectional   │
│  Type Safety    │ Manual validation     │ Compile-time checks  │
│  Browser native │ Yes                   │ Limited (grpc-web)   │
│  Human readable │ Yes                   │ No (binary)          │
└────────────────────────────────────────────────────────────────┘

gRPC streaming types:
  Unary:            Client sends 1, gets 1 back
  Server streaming: Client sends 1, gets stream back
  Client streaming: Client sends stream, gets 1 back
  Bidirectional:    Both send streams simultaneously
```

### GraphQL

```
REST problem: Over-fetching (get too much data) or under-fetching (need multiple calls)

GraphQL: Client specifies EXACTLY what data it needs.

Query:
  {
    user(id: "123") {
      name
      email
      posts {
        title
      }
    }
  }

Response:
  {
    "data": {
      "user": {
        "name": "Alice",
        "email": "alice@example.com",
        "posts": [{ "title": "My post" }]
      }
    }
  }
```

---

## 15. Rate Limiting

**What is Rate Limiting?** Controlling how many requests a client can make in a given time window.

### Why?
- Prevent abuse/DDoS
- Ensure fair use
- Protect backend from overload

### Algorithms

```
TOKEN BUCKET:
  A bucket holds N tokens. Each request consumes 1 token.
  Tokens refill at rate R per second.
  If bucket is empty → reject request.

  ┌────────────────────────────┐
  │  Bucket (capacity: 10)     │
  │  ██████████  → tokens      │
  │           ↑ refill: 2/sec  │
  │           ↓ consume: 1/req │
  └────────────────────────────┘
  Allows bursts (up to bucket size).

LEAKY BUCKET:
  Requests enter bucket → drain at constant rate.
  If bucket overflows → reject request.
  Smooths out traffic. No bursts allowed.

  Requests ──► [  bucket  ] ──► Process at fixed rate ──► Response

FIXED WINDOW COUNTER:
  Divide time into fixed windows (e.g., 1 min each).
  Count requests per window. If > limit → reject.
  Problem: Edge case: 100 req at 0:59, 100 req at 1:01 = 200 req in 2 seconds!

SLIDING WINDOW LOG:
  Keep a log of timestamps of each request.
  For each new request: count requests in last N seconds.
  Accurate but memory intensive.

SLIDING WINDOW COUNTER:
  Combine fixed window + weighted from previous window.
  Approximation of sliding window but O(1) space.
```

---

## 16. API Gateway

**What is an API Gateway?** A single entry point for all client API requests, handling cross-cutting concerns.

```
                        API GATEWAY
┌───────────────────────────────────────────────────────────┐
│  Client Request                                           │
│       │                                                   │
│       ▼                                                   │
│  [Authentication] → verify JWT/API Key                   │
│       │                                                   │
│       ▼                                                   │
│  [Rate Limiting]  → 100 req/min per client               │
│       │                                                   │
│       ▼                                                   │
│  [Routing]        → /users → UserService                 │
│                    /orders → OrderService                 │
│       │                                                   │
│       ▼                                                   │
│  [Load Balancing] → pick instance                        │
│       │                                                   │
│       ▼                                                   │
│  [Logging]        → record request                       │
│       │                                                   │
│       ▼                                                   │
│  [Response Transform] → reshape response                 │
└───────────────────────────────────────────────────────────┘

Examples: Kong, AWS API Gateway, NGINX, Envoy
```

---

# PART II — NETWORKING DEEP DIVE

---

## 17. The OSI Model

**What is the OSI Model?** Open Systems Interconnection — a conceptual framework dividing network communication into 7 layers.

```
┌───────────────────────────────────────────────────────────────────┐
│  Layer │ Name         │ Protocol Examples │ Data Unit             │
├────────┼──────────────┼───────────────────┼───────────────────────┤
│   7    │ Application  │ HTTP, FTP, SMTP   │ Data/Message          │
│   6    │ Presentation │ SSL/TLS, JPEG     │ Data                  │
│   5    │ Session      │ RPC, NetBIOS      │ Data                  │
│   4    │ Transport    │ TCP, UDP          │ Segment/Datagram       │
│   3    │ Network      │ IP, ICMP, OSPF    │ Packet                │
│   2    │ Data Link    │ Ethernet, WiFi    │ Frame                 │
│   1    │ Physical     │ Cables, Fiber     │ Bits                  │
└────────┴──────────────┴───────────────────┴───────────────────────┘

Mnemonic (top to bottom): "All People Seem To Need Data Processing"
Mnemonic (bottom to top): "Please Do Not Throw Sausage Pizza Away"
```

### Encapsulation (How Data Travels Down the Stack)

```
Application creates: [  HTTP DATA  ]
Transport adds:      [ TCP HEADER | HTTP DATA ]
Network adds:        [ IP HEADER | TCP HEADER | HTTP DATA ]
Data Link adds:      [ ETH HEADER | IP HEADER | TCP HEADER | HTTP DATA | ETH TRAILER ]
Physical:            1010101010101010101010101010101010...
```

---

## 18. TCP vs UDP

**TCP (Transmission Control Protocol):**
- Connection-oriented (3-way handshake to start)
- Reliable: guaranteed delivery, ordering, error checking
- Flow control and congestion control
- Slower overhead

**UDP (User Datagram Protocol):**
- Connectionless (fire and forget)
- No guarantee of delivery or order
- No congestion control
- Fast, low overhead

```
TCP 3-WAY HANDSHAKE:

Client              Server
  │──── SYN ────────►│    "I want to connect" (SYN = synchronize)
  │◄─── SYN-ACK ─────│    "OK, I'm ready"
  │──── ACK ────────►│    "Got it, let's go"
  │                   │
  │  (data transfer)  │
  │                   │
  │──── FIN ────────►│    "I'm done sending"
  │◄─── ACK ─────────│
  │◄─── FIN ─────────│    "I'm done too"
  │──── ACK ────────►│
                           (connection closed)

TCP vs UDP COMPARISON:
┌───────────────────────────────────────────────────────────────┐
│  Feature            │ TCP                  │ UDP               │
├─────────────────────┼──────────────────────┼───────────────────┤
│  Connection         │ Required             │ Not required      │
│  Reliability        │ Guaranteed           │ Best-effort       │
│  Ordering           │ Guaranteed           │ Not guaranteed    │
│  Speed              │ Slower               │ Faster            │
│  Overhead           │ High (headers+state) │ Low               │
│  Use cases          │ HTTP, Email, File    │ Video, Gaming,    │
│                     │ transfer, SSH        │ DNS, VoIP         │
└───────────────────────────────────────────────────────────────┘
```

---

## 19. HTTP Versions

```
HTTP/1.0: One request per connection. Slow.
          Client ──►connect──► Request ──► Response ──►close

HTTP/1.1: Keep-alive (reuse connection). But HEAD-OF-LINE BLOCKING.
          One response must finish before next starts.
          Client ──►connect──► Req1 ──► Resp1 ──► Req2 ──► Resp2 ...

HTTP/2:   Multiplexing — multiple concurrent streams on ONE connection.
          Binary protocol (not text).
          Header compression (HPACK).
          Server push.
          ┌──────────────────────────────┐
          │  Stream 1: ████████████████  │
          │  Stream 2:   ████████        │
          │  Stream 3:     ██████████    │
          └──────────────────────────────┘
          (all on same TCP connection simultaneously)

HTTP/3:   Uses QUIC (UDP-based) instead of TCP.
          No TCP head-of-line blocking.
          Connection migration (change network without reconnecting).
          Built-in encryption (TLS 1.3).

QUIC = Quick UDP Internet Connections (developed by Google)
```

---

## 20. DNS (Domain Name System)

**What is DNS?** The "phone book" of the internet — translates human-readable domain names to IP addresses.

```
DNS RESOLUTION FLOW:

You type: www.example.com

1. Browser cache → found? Done.
2. OS cache (hosts file) → found? Done.
3. Recursive Resolver (usually your ISP or 8.8.8.8)
   3a. Ask Root Nameserver: "who handles .com?"
   3b. Root says: "Go ask .com TLD nameserver"
   3c. Ask TLD nameserver: "who handles example.com?"
   3d. TLD says: "Go ask ns1.example.com"
   3e. Ask ns1.example.com: "what's the IP of www.example.com?"
   3f. Gets: 93.184.216.34
4. Cache result. Return to browser.

DNS RECORD TYPES:
┌────────────────────────────────────────────────────────────┐
│  Record │ Purpose                │ Example                 │
├─────────┼────────────────────────┼─────────────────────────┤
│  A      │ IPv4 address           │ example.com → 1.2.3.4  │
│  AAAA   │ IPv6 address           │ example.com → ::1       │
│  CNAME  │ Alias to another name  │ www → example.com       │
│  MX     │ Mail server            │ example.com → mail.ex   │
│  NS     │ Nameserver             │ example.com → ns1.ex    │
│  TXT    │ Text (SPF, DKIM, etc)  │ "v=spf1 include:..."   │
│  SOA    │ Start of Authority     │ Zone metadata           │
│  PTR    │ Reverse lookup (IP→name│ 1.2.3.4 → example.com  │
│  SRV    │ Service location       │ _http._tcp.example.com  │
└─────────┴────────────────────────┴─────────────────────────┘
```

---

## 21. TCP Congestion Control

**What is Congestion?** When too many packets flood the network, causing drops and delays.

```
TCP CONGESTION CONTROL ALGORITHMS:

SLOW START:
  Window size starts at 1 MSS (Max Segment Size).
  Doubles every RTT (Round Trip Time) until threshold.
  
  cwnd (congestion window):
  1 → 2 → 4 → 8 → 16 ... (exponential)

CONGESTION AVOIDANCE:
  After reaching threshold: increment by 1 per RTT (linear).
  16 → 17 → 18 → 19 ...

ON LOSS (packet drop detected):
  Tahoe: reset cwnd to 1
  Reno: cut cwnd in half (fast recovery)

BBRC (BBR - Bottleneck Bandwidth and Round-trip propagation time):
  Google's algorithm (2016). Measures actual bandwidth and RTT.
  Better for high-latency/lossy links.

Graph:
cwnd
 ▲
32│              /
16│          /  /
 8│      /  loss
 4│  /  
 2│/   
 1└─────────────── time
  Slow Start → Avoidance → Loss → Recovery
```

---

## 22. Networking Protocols Summary

```
┌──────────────────────────────────────────────────────────────────────┐
│  Protocol  │ Layer │ Purpose                                         │
├────────────┼───────┼─────────────────────────────────────────────────┤
│  IP        │  3    │ Routing packets across networks                 │
│  TCP       │  4    │ Reliable, ordered byte stream                   │
│  UDP       │  4    │ Fast, unreliable datagrams                      │
│  ICMP      │  3    │ Error messages, ping                            │
│  ARP       │  2/3  │ IP → MAC address resolution                     │
│  HTTP/S    │  7    │ Web traffic                                     │
│  WebSocket │  7    │ Full-duplex communication over TCP              │
│  SMTP      │  7    │ Email sending                                   │
│  FTP       │  7    │ File transfer                                   │
│  SSH       │  7    │ Secure shell                                    │
│  TLS       │  6    │ Encryption layer (runs over TCP)                │
│  DNS       │  7    │ Name resolution                                 │
│  DHCP      │  7    │ IP address assignment                           │
│  BGP       │  7    │ Internet routing protocol (between ASes)        │
│  OSPF      │  3    │ Routing within an AS (link state)               │
│  VXLAN     │  3    │ Virtual overlay networks                        │
│  QUIC      │  4    │ UDP-based reliable transport (for HTTP/3)       │
└────────────┴───────┴─────────────────────────────────────────────────┘
```

---

# PART III — DISTRIBUTED SYSTEMS

---

## 23. What is a Distributed System?

A distributed system is a collection of autonomous computing nodes that communicate through a network and appear to users as a single coherent system.

```
DISTRIBUTED SYSTEM CHALLENGES:
┌──────────────────────────────────────────────────────────────────┐
│  1. Partial failures     — some nodes fail, others don't        │
│  2. Network unreliability — messages lost, delayed, duplicated  │
│  3. Concurrency           — many things happening at once        │
│  4. Lack of global clock  — no single "true" time               │
│  5. Byzantine failures    — nodes can behave maliciously         │
└──────────────────────────────────────────────────────────────────┘
```

---

## 24. Clocks in Distributed Systems

**Problem:** Each machine has its own physical clock. They drift. You cannot know the true order of events across machines.

### Physical Clocks

```
Machine A clock: 10:00:00.000
Machine B clock: 10:00:00.003  ← 3ms drift

If A does event X at 10:00:00.005
If B does event Y at 10:00:00.004

Which happened first? X or Y?
We CANNOT know from wall clocks alone.
```

### Logical Clocks (Lamport Timestamps)

**What is a Logical Clock?** A counter that tracks causal ordering of events.

**Rules:**
1. Increment counter before each event
2. On send: include counter in message
3. On receive: max(local, received) + 1

```
Process A:    1 ──────────── 2 ──────────── 3
                      │                │
Process B:    1 ──── 2(max(2,1)+1=3) ─ 4 ── 5
                                          │
Process C:    1 ─────────────────────── 2(max(5,1)+1=6) ─ 7

Lamport clocks: If A→B, then LC(A) < LC(B).
But LC(A) < LC(B) does NOT imply A → B (concurrent events look ordered).
```

### Vector Clocks

**What are Vector Clocks?** Each node maintains a vector (array) of counters — one per node. Tracks causality precisely.

```
3 nodes: A, B, C
Each has vector [A_count, B_count, C_count]

A sends message at [2,0,0]:
B receives: B updates to [max(2,0), max(0,1)+1, max(0,0)] = [2,2,0]

Comparing vectors:
  V1 < V2 if every element of V1 ≤ V2 (causally before)
  V1 || V2 if neither ≤ the other (concurrent — conflict!)

Amazon DynamoDB uses vector clocks for conflict detection.
```

---

## 25. Consensus Algorithms

**What is Consensus?** Getting multiple nodes to agree on a single value.

### Why is it hard?

The **FLP Impossibility** (Fischer, Lynch, Paterson 1985):
> In an asynchronous system, there is no deterministic consensus algorithm that can tolerate even ONE crash failure.

**Workaround:** Use timeouts (Paxos, Raft assume partial synchrony).

### Paxos

**Roles:**
- **Proposers**: Propose values
- **Acceptors**: Vote on proposals
- **Learners**: Learn the decided value

```
PAXOS PHASES:

Phase 1a (PREPARE):
  Proposer sends Prepare(n) to majority of acceptors.
  n = proposal number (must be unique and increasing)

Phase 1b (PROMISE):
  Acceptor: if n > my_max_seen, promise not to accept < n.
  Return any previously accepted value.

Phase 2a (ACCEPT):
  Proposer sends Accept(n, v) to majority.
  v = value from highest-numbered promise (or own value)

Phase 2b (ACCEPTED):
  Acceptor: if n >= max_seen, accept and notify learners.

A value is CHOSEN when a majority accepts it.

Proposer ──► Acceptor1
         ──► Acceptor2   ← majority (2 of 3)
         ──► Acceptor3
```

### Raft (Simpler, More Understandable)

**Raft is designed to be understandable.** It decomposes consensus into:
1. Leader election
2. Log replication
3. Safety

```
RAFT NODE STATES:
  Follower ──► Candidate ──► Leader
     ▲              │           │
     └──────────────┴───────────┘
           (on timeout or failure)

LEADER ELECTION:
  Each node has election timeout (150-300ms random).
  If no heartbeat received → start election.
  Node increments term, votes for itself, asks others to vote.
  First to get majority wins.

  Term: monotonically increasing epoch number.
  Ensures old leaders can't cause harm.

LOG REPLICATION:
  All writes go to leader.
  Leader appends to its log.
  Leader sends AppendEntries to all followers.
  Once majority acknowledge → commit.
  Leader notifies followers of commit.

  Leader Log: [x=1, y=2, z=3, ...]
                ↓
  Follower:   [x=1, y=2, z=3, ...]  (replicated)

SAFETY GUARANTEE:
  Raft ensures: if two logs agree on an entry at index i,
  they agree on ALL entries up to index i.
```

---

## 26. Distributed Transactions

**What is a Transaction?** A group of operations that must ALL succeed or ALL fail (atomically).

**ACID Properties:**
```
A = Atomicity    — all or nothing
C = Consistency  — always valid state
I = Isolation    — transactions don't interfere
D = Durability   — committed data survives crashes
```

### Two-Phase Commit (2PC)

```
PHASE 1 (PREPARE/VOTING):
  Coordinator ──► Participant A: "Can you commit?"
  Coordinator ──► Participant B: "Can you commit?"
  Coordinator ──► Participant C: "Can you commit?"

  A,B,C: Each locks resources, writes to redo log, replies YES/NO.

PHASE 2 (COMMIT/ABORT):
  If ALL voted YES:
    Coordinator ──► A,B,C: "COMMIT"
  If ANY voted NO:
    Coordinator ──► A,B,C: "ABORT"

PROBLEM: Coordinator failure in between = participants blocked forever!

PHASE 1:
  Coord─────────────────────────────────┐
       ──►Prepare──► A (YES)            │ Coord crashes here!
       ──►Prepare──► B (YES)            │
       ──►Prepare──► C (YES)            │
                                        │
  A, B, C: locked, waiting, can't decide...
```

### Three-Phase Commit (3PC)

Adds a pre-commit phase to allow recovery. More complex, still not fully solving coordinator failure in async systems.

### Saga Pattern

**What is a Saga?** A sequence of local transactions, each publishing events. If one fails, compensating transactions undo previous steps.

```
Order Saga:
  1. Reserve Inventory  ──► success
  2. Charge Payment     ──► success
  3. Ship Order         ──► FAIL!

Compensation:
  3. (failed, skip)
  2. Refund Payment     ◄── compensate
  1. Release Inventory  ◄── compensate

TWO STYLES:
  Choreography: Each service listens to events and reacts.
  Orchestration: A central Saga Orchestrator directs participants.
```

---

## 27. Replication

**What is Replication?** Keeping copies of data on multiple nodes.

**Why?**
- Fault tolerance (if one node dies, others serve)
- Low latency (serve from geographically closer replica)
- Higher read throughput

### Single-Leader (Master-Replica)

```
          ┌────────────┐
 Writes ──►   LEADER   │
          └─────┬──────┘
                │ replicate
        ┌───────┼───────┐
        ▼       ▼       ▼
    Replica1 Replica2 Replica3
        │       │       │
 Reads─►┘       │       └──► Reads
                └──► Reads

Pros: Simple, strong consistency possible
Cons: Leader is bottleneck and single point of failure
```

### Multi-Leader (Multi-Master)

```
  DC1: Leader1 ◄──────────────► Leader2 :DC2
         │                            │
      Followers                   Followers

Writes can go to either leader. Replicated across DCs.
Conflict resolution needed when same record updated concurrently.
```

### Leaderless (Dynamo-style)

```
No leader. Clients write to MULTIPLE nodes simultaneously.
Read from MULTIPLE nodes and use quorum.

W = write quorum (must confirm before success)
R = read quorum (must confirm before return)
N = total replicas

For consistency: W + R > N
For availability: W = 1, R = 1 (but inconsistency possible)

Typical: N=3, W=2, R=2

  Client ──► write to A,B,C
  Client ──► read from A,B → compare, pick latest version
```

### Replication Lag and Anomalies

```
REPLICATION LAG: Time delay between leader write and replica sync.

ANOMALIES:
  Read-your-writes: You write, read from lagging replica, don't see it.
  Monotonic reads: Read v5, then read v3 from another replica.
  Consistent prefix: See effect before cause.

SOLUTIONS:
  Route user's own reads to leader.
  Track version numbers.
  Use sticky sessions.
```

---

## 28. Partitioning (Sharding)

**What is Partitioning?** Splitting a large dataset across multiple nodes so each node holds only a portion.

**Why?** No single machine can hold all the data or handle all requests.

### Partition Strategies

```
RANGE PARTITIONING:
  Partition 1: A-F
  Partition 2: G-M
  Partition 3: N-Z

  ✓ Range queries are efficient
  ✗ Hot spots (all "A" users go to P1 if popular)

HASH PARTITIONING:
  partition = hash(key) % num_partitions
  
  ✓ Even distribution
  ✗ Range queries require all partitions
  ✗ Resharding is expensive (changing num_partitions)

CONSISTENT HASHING:
  Ring of 2^32 positions. Nodes placed at positions on ring.
  Key → hash → find closest node clockwise.
  
  Adding/removing node: only adjacent keys migrate.
  
  ┌──────────────────────────────┐
  │           Ring               │
  │     N1                       │
  │   /    \                     │
  │  /      \                    │
  │ N3      N2                   │
  │  \      /                    │
  │   \    /                     │
  │    ──────                    │
  │                              │
  │  Key K: clockwise → N2       │
  └──────────────────────────────┘
  
  Virtual nodes: Each physical node gets multiple positions.
  Avoids uneven load even when nodes have different capacities.

DIRECTORY-BASED:
  Lookup service maps keys to partitions.
  Most flexible but single point of failure.
```

### Secondary Indexes in Partitioned Systems

```
LOCAL (SCATTER-GATHER):
  Each partition has its own secondary index.
  Read query must hit ALL partitions (scatter) and merge (gather).
  
  Slow reads but fast writes.

GLOBAL:
  Secondary index covers all partitions.
  Lives on its own partition.
  Fast reads but writes must update secondary index (async lag).
```

---

## 29. Distributed Caching

```
MEMCACHED:
  Simple, high-performance key-value cache.
  Multi-threaded.
  No persistence.
  No replication built-in.
  Used for: session storage, simple caching.

REDIS:
  Data structures: strings, lists, sets, sorted sets, hashes, streams.
  Optional persistence (RDB snapshots, AOF log).
  Replication + Sentinel (HA) + Cluster mode.
  Pub/Sub messaging.
  Lua scripting.
  
REDIS CLUSTER:
  Data sharded across 16384 hash slots.
  Each node owns a range of slots.
  Automatic failover via gossip protocol.
  
CACHE TOPOLOGY OPTIONS:
  Embedded: Cache inside app process (HashMap) — fastest, not shared
  Sidecar: Cache as separate process on same host — shared
  Remote: Centralized cache server (Redis) — shared, network hop
  Hierarchical: L1 (local) + L2 (Redis) — best of both
```

---

## 30. Message Queues and Event Streaming

**What is a Message Queue?** A buffer that stores messages between producers (senders) and consumers (receivers), allowing asynchronous communication.

### Why Use Queues?

```
WITHOUT QUEUE:
  Order Service ──► Email Service (synchronous call)
  If Email Service is down → Order Service fails!

WITH QUEUE:
  Order Service ──► [Queue] ──► Email Service
  If Email Service is down → message waits in queue.
  Order Service succeeds immediately.
  
BENEFITS:
  ✓ Decoupling (services don't know about each other)
  ✓ Buffering (handle traffic spikes)
  ✓ Async processing
  ✓ Load leveling
  ✓ Retry and dead-letter queues
```

### Message Queue vs Event Streaming

```
┌─────────────────────────────────────────────────────────────────┐
│  Feature        │ Message Queue (RabbitMQ) │ Event Stream Kafka │
├─────────────────┼──────────────────────────┼────────────────────┤
│  Delivery       │ One consumer gets msg    │ All consumers get  │
│  Retention      │ Deleted after consume    │ Retained (days)    │
│  Order          │ FIFO per queue           │ Per partition      │
│  Replay         │ No (already consumed)    │ Yes (offset-based) │
│  Throughput     │ High                     │ Very high          │
│  Use case       │ Task queues, work items  │ Event log, streams │
└─────────────────┴──────────────────────────┴────────────────────┘
```

### Apache Kafka Architecture

```
KAFKA CONCEPTS:
  Topic: Named category of messages (like a table or channel).
  Partition: A topic is split into partitions for parallelism.
  Offset: Position of a message within a partition (monotonic).
  Producer: Writes messages to topics.
  Consumer: Reads messages from topics using offsets.
  Consumer Group: Multiple consumers sharing partition ownership.
  Broker: A Kafka server node.
  ZooKeeper/KRaft: Cluster metadata and leader election.

TOPIC PARTITIONS:
  Topic "orders" with 3 partitions:
  
  Partition 0: msg0, msg1, msg4, msg7 ...
  Partition 1: msg2, msg5, msg8 ...
  Partition 2: msg3, msg6, msg9 ...
  
  Producer can route by key: hash(order_id) % 3

CONSUMER GROUP:
  3 consumers, 3 partitions:
  Consumer A → Partition 0
  Consumer B → Partition 1
  Consumer C → Partition 2
  (parallel processing)
  
  2 consumers, 3 partitions:
  Consumer A → Partition 0, 1
  Consumer B → Partition 2
  
  4 consumers, 3 partitions:
  Consumer A,B,C → one partition each
  Consumer D → idle (more consumers than partitions = waste)

KAFKA DELIVERY GUARANTEES:
  At-most-once:  ack before process → may lose messages
  At-least-once: process then ack → may duplicate (COMMON)
  Exactly-once:  idempotent producers + transactions (complex)
```

---

## 31. Service Discovery

**What is Service Discovery?** The mechanism by which services find each other in a dynamic environment where IPs change constantly.

```
PROBLEM:
  Service A wants to call Service B.
  B's IP is 10.0.1.5.
  B crashes. New instance starts at 10.0.1.9.
  A doesn't know!

CLIENT-SIDE DISCOVERY:
  A queries Service Registry ("where is B?")
  Registry returns [10.0.1.9:8080]
  A calls directly.
  
  Client ──► Registry (Consul, Eureka) ──► IP list
  Client ──────────────────────────────►  Service B

SERVER-SIDE DISCOVERY:
  A calls Load Balancer / API Gateway.
  LB queries registry and forwards.
  A doesn't know B's location.
  
  Client ──► Load Balancer ──► Registry ──► Service B

SERVICE REGISTRY EXAMPLES:
  Consul (HashiCorp)
  etcd (CoreOS / Kubernetes)
  ZooKeeper (Apache)
  Eureka (Netflix)
  Kubernetes DNS (built-in)
```

---

## 32. Circuit Breaker Pattern

**What is a Circuit Breaker?** A pattern that prevents cascading failures by "tripping" when a dependency is failing.

**Analogy:** Like an electrical circuit breaker — when too much current flows, it trips to prevent fire.

```
STATES:

  CLOSED (normal operation):
    Requests pass through.
    Count failures.
    ┌──────────────────────────┐
    │  failures = 0,1,2,3,4   │
    │  if failures > threshold │──► OPEN
    └──────────────────────────┘

  OPEN (failure state):
    All requests IMMEDIATELY fail with error.
    No requests reach the failing service.
    Timer starts.
    ┌──────────────────────────┐
    │  blocking all requests   │
    │  timer = 30s             │──► HALF-OPEN (after timeout)
    └──────────────────────────┘

  HALF-OPEN (recovery probe):
    Let one test request through.
    If success → CLOSED.
    If fail    → OPEN again.
    ┌──────────────────────────┐
    │  one request allowed     │──► CLOSED (success)
    │                          │──► OPEN (fail)
    └──────────────────────────┘

FLOW:
  
  Client ──►[CB: CLOSED]──► Service B
  
  (B starts failing...)
  
  Client ──►[CB: OPEN]──►✗ (immediate error, no call to B)
  
  (timer expires...)
  
  Client ──►[CB: HALF-OPEN]──► B ──► OK → CLOSED
```

---

## 33. Consistent Hashing (Deep Dive)

**The Problem With Naive Hashing:**
```
4 servers: S0,S1,S2,S3
partition = hash(key) % 4

Add S4:
partition = hash(key) % 5
ALL keys may change servers → massive data migration!
```

**Consistent Hashing Solution:**

```
RING SETUP:
  Place all possible hash values on a circular ring (0 to 2^32-1).
  Place servers at random positions on the ring.
  
        0
       / \
   S1 /   \ S2
      \   /
   S0  \ / S3
        ↕
      2^32-1

LOOKUP:
  hash(key) → position on ring
  Walk clockwise → first server encountered

ADD SERVER:
  Place S4 on ring.
  Only keys between S4's predecessor and S4 migrate to S4.
  
REMOVE SERVER:
  Only keys from removed server migrate to its successor.

VIRTUAL NODES:
  Each physical server gets K virtual positions on the ring.
  Achieves uniform distribution even with different capacities.
  
  S0 → S0_v1, S0_v2, S0_v3, S0_v4 (on ring)
  
  More virtual nodes = more even load = more memory overhead.
```

---

## 34. Bloom Filters

**What is a Bloom Filter?** A probabilistic data structure that tests set membership.

- May return false positives ("maybe in set")
- Never returns false negatives ("definitely not in set")
- Space efficient: O(m) bits for m-bit filter

**Use cases:** Cache penetration prevention, checking if URL was seen, spam filtering, weak password detection.

```
STRUCTURE:
  Bit array of m bits, all initially 0.
  k hash functions.

INSERT key:
  hash1(key) = 3 → set bit[3] = 1
  hash2(key) = 7 → set bit[7] = 1
  hash3(key) = 12 → set bit[12] = 1

LOOKUP key:
  hash1(key) = 3 → bit[3] = 1? ✓
  hash2(key) = 7 → bit[7] = 1? ✓
  hash3(key) = 12 → bit[12] = 1? ✓
  All 1? → "possibly in set"
  
  (False positive: other keys set those bits)

  If ANY bit is 0 → definitely NOT in set.

CANNOT DELETE from a standard Bloom filter (use Counting Bloom Filter instead).
```

---

## 35. HyperLogLog

**What is HyperLogLog?** An algorithm for approximating the cardinality (distinct count) of a set using very little memory.

```
Problem: Count unique visitors to a website.
Naive: Store all IPs in a Set. 10M visitors = ~1GB RAM.
HyperLogLog: ≈12 KB RAM for any size, ±2% error.

Used in: Redis PFADD/PFCOUNT, big data analytics.

Key insight: uses the probability of leading zeros in hashed values
to estimate distinct count. (Mathematical magic.)
```

---

# PART IV — STORAGE & DATABASES

---

## 36. Storage Fundamentals

### Storage Media Types

```
┌────────────────────────────────────────────────────────────────┐
│  Type         │ Access Pattern │ Latency  │ Durability         │
├───────────────┼────────────────┼──────────┼────────────────────┤
│  SRAM         │ Random         │ 0.5-7ns  │ Volatile           │
│  DRAM         │ Random         │ ~100ns   │ Volatile           │
│  NAND Flash   │ Random(slow wr)│ 150µs    │ Non-volatile       │
│  NVMe SSD     │ Random         │ 100-500µs│ Non-volatile       │
│  SATA SSD     │ Random         │ 500µs-1ms│ Non-volatile       │
│  HDD          │ Sequential ✓   │ 5-20ms   │ Non-volatile       │
│  Network Block│ Remote         │ 1-10ms   │ Non-volatile       │
│  Object Store │ API (S3)       │ 10-200ms │ Non-volatile, high │
└────────────────────────────────────────────────────────────────┘
```

### Sequential vs Random I/O

```
SEQUENTIAL: Reading/writing consecutive blocks.
  HDD: Very fast (disk head doesn't need to seek)
  SSD: Fast
  
RANDOM: Reading/writing scattered blocks.
  HDD: Very slow (physical seek, ~10ms per seek)
  SSD: Still fast (no moving parts)
  
Design principle: Design data structures to favor sequential I/O.
This is why LSM trees (Cassandra, RocksDB) prefer sequential writes.
```

---

## 37. Database Internals

### B-Tree (Most Common Index Structure)

**What is a B-Tree?** A self-balancing tree where each node can have multiple keys and children. Used by PostgreSQL, MySQL, SQLite for indexes.

```
B-TREE STRUCTURE (Order 3: max 2 keys, 3 children per node):

                    [10 | 20]
                   /    |    \
              [5|7]  [12|15] [25|30]
             /|\ \   ...       ...
           ...

PROPERTIES:
  All leaves at same depth (balanced).
  Node size = one disk page (~4KB or 16KB).
  n keys → n+1 pointers to children.
  Sorted keys → binary search within node.

OPERATIONS:
  Search: O(log n) — traverse from root to leaf
  Insert: Find leaf, insert, split if full, propagate up
  Delete: Find, remove, merge/rebalance if underfull

B+ TREE (variant used in most databases):
  Internal nodes: only keys (no data).
  Leaf nodes: all keys + data pointers.
  Leaves linked in a doubly linked list.
  
  Benefits:
    Internal nodes can hold more keys (less disk I/O).
    Range scans are fast (follow leaf linked list).
```

### LSM Tree (Log-Structured Merge Tree)

**What is an LSM Tree?** A data structure that converts random writes into sequential writes, optimizing write throughput at the cost of slower reads.

**Used by:** Cassandra, RocksDB, LevelDB, HBase, ScyllaDB

```
LSM WRITE PATH:
  1. Write to Write-Ahead Log (WAL) on disk (sequential, for recovery)
  2. Write to in-memory buffer (MemTable — a sorted structure)
  3. When MemTable is full → flush to disk as SSTable (Sorted String Table)
  4. SSTables accumulate → periodic compaction (merge sort)

LAYERS:
  ┌────────────────────────────────────────┐
  │  MemTable (L0, in RAM)                 │ ← all writes go here
  ├────────────────────────────────────────┤
  │  SSTable L1 (disk, recently flushed)   │
  ├────────────────────────────────────────┤
  │  SSTable L2 (disk, larger, compacted)  │
  ├────────────────────────────────────────┤
  │  SSTable L3 (disk, largest)            │
  └────────────────────────────────────────┘

COMPACTION:
  Merge multiple SSTables into one (like merge sort).
  Remove duplicates (keep newest version).
  Remove deleted records (tombstones eventually removed).

READ PATH (problematic — must check multiple levels):
  1. Check MemTable first.
  2. Check L0 SSTables (newest first).
  3. Check L1, L2, L3...
  
  Bloom filter per SSTable → skip SSTables that don't have key.

LSM vs B-Tree:
  LSM: Write optimized, Space amplification, Read requires merge
  B-Tree: Read optimized, Write amplification (COW or in-place), Predictable latency
```

### WAL (Write-Ahead Log)

**What is a WAL?** A sequential log file where all changes are written BEFORE being applied to the actual data.

```
WHY WAL?
  Crash recovery: If crash mid-write, replay WAL to restore state.
  Durability: Once in WAL, committed (fsync to disk).
  
WAL FLOW:
  Transaction T1: UPDATE users SET name='Bob' WHERE id=1
  
  1. Write to WAL: [T1 BEGIN, T1 UPDATE users id=1 name=Bob, T1 COMMIT]
  2. Apply to B-tree pages in memory.
  3. Flush dirty pages to disk later (background).
  
  If crash after step 1 but before step 3 → replay WAL on restart.
  If crash before step 1 completes → transaction never happened.
```

---

## 38. Database Types

### Relational Databases (SQL)

```
Structure: Tables with rows and columns.
Schema: Fixed, enforced.
Relationships: Foreign keys, joins.
ACID: Full support.
Query: SQL.
Scale: Vertical primarily. Horizontal via sharding (complex).

Examples: PostgreSQL, MySQL, SQLite, Oracle, SQL Server.

WHEN TO USE:
  Complex queries and relationships.
  ACID transactions required.
  Data structure known and stable.
  Financial systems, ERP, inventory.
```

### Document Databases

```
Structure: JSON/BSON documents in collections.
Schema: Flexible (schema-less or optional schema).
Relationships: Embedded documents or references.
ACID: Document-level (some support multi-doc).
Query: Query language (MQL for MongoDB).

Examples: MongoDB, CouchDB, Firestore.

WHEN TO USE:
  Variable/evolving schemas.
  Hierarchical data (nested objects).
  Rapid prototyping.
  Content management, catalogs.
```

### Key-Value Stores

```
Structure: Simple key → value pairs.
Value: Opaque blob (app defines structure).
Operations: GET, SET, DELETE.
Speed: Extremely fast.

Examples: Redis, DynamoDB, Riak, etcd.

WHEN TO USE:
  Caching.
  Session storage.
  Simple lookups (no complex queries).
  Real-time leaderboards (Redis sorted sets).
```

### Wide-Column Stores

```
Structure: Table with rows, but columns can vary per row.
Rows grouped into Column Families.
Optimized for reads/writes of specific columns.

Examples: Apache Cassandra, HBase, Google Bigtable.

DATA MODEL:
  (row_key, column_family, column, timestamp) → value

WHEN TO USE:
  Time-series data.
  Event logging.
  IoT sensor data.
  High write throughput, massive scale.
```

### Graph Databases

```
Structure: Nodes (entities) and Edges (relationships).
Query: Traversal queries (Cypher, Gremlin).
Strong: Highly connected data, variable depth traversals.

Examples: Neo4j, Amazon Neptune, JanusGraph.

WHEN TO USE:
  Social networks (friends of friends).
  Recommendation engines.
  Fraud detection (relationship patterns).
  Knowledge graphs.
```

### Time-Series Databases

```
Optimized for: timestamps + metrics pairs.
Features: Compression, downsampling, retention policies.

Examples: InfluxDB, TimescaleDB, Prometheus, OpenTSDB.

WHEN TO USE:
  Metrics (CPU, memory, network).
  Financial tick data.
  IoT sensor readings.
  Application performance monitoring.
```

### Search Engines

```
Optimized for: Full-text search, faceting, relevance ranking.
Internal: Inverted index.
  Word → [doc_id1, doc_id2, ...]

Examples: Elasticsearch, Apache Solr, OpenSearch.

WHEN TO USE:
  Search boxes.
  Log analytics (ELK stack).
  E-commerce product search.
```

---

## 39. SQL Deep Dive

### Indexes

```
WITHOUT INDEX:
  SELECT * FROM users WHERE email = 'alice@x.com'
  → Full table scan: O(n) rows checked.

WITH INDEX:
  B-tree on email column.
  → O(log n) search.

INDEX TYPES:
  Primary Index: On primary key (unique, clustered in InnoDB).
  Secondary Index: On other columns (non-clustered).
  Composite Index: Multiple columns. Order matters!
  Partial Index: On subset of rows (WHERE clause).
  Covering Index: Includes all needed columns (no table lookup).
  Full-text Index: For text search.
  
COMPOSITE INDEX RULE (Leftmost Prefix):
  Index on (a, b, c) helps queries on:
    WHERE a = ?           ✓
    WHERE a = ? AND b = ? ✓
    WHERE a = ? AND b = ? AND c = ? ✓
    WHERE b = ?           ✗ (index not used without a)
    WHERE b = ? AND c = ? ✗
```

### Transactions and Isolation Levels

```
ISOLATION LEVELS (weakest to strongest):

READ UNCOMMITTED:
  Can read data from uncommitted transactions (dirty reads).
  Fastest, least safe.

READ COMMITTED:
  Only read committed data. Prevents dirty reads.
  PostgreSQL default.

REPEATABLE READ:
  Same query in same transaction returns same result.
  Prevents dirty reads + non-repeatable reads.
  MySQL InnoDB default.

SERIALIZABLE:
  Full isolation. Transactions as if sequential.
  Slowest, safest.

ANOMALIES TABLE:
┌──────────────────────┬──────────┬──────────┬───────────┬─────────────┐
│  Anomaly             │ Uncom.   │ Com.     │ Repeat.   │ Serial.     │
├──────────────────────┼──────────┼──────────┼───────────┼─────────────┤
│  Dirty Read          │    ✗     │    ✓     │    ✓      │    ✓        │
│  Non-repeatable Read │    ✗     │    ✗     │    ✓      │    ✓        │
│  Phantom Read        │    ✗     │    ✗     │    ~      │    ✓        │
│  Serialization Anom. │    ✗     │    ✗     │    ✗      │    ✓        │
└──────────────────────┴──────────┴──────────┴───────────┴─────────────┘
(✓ = prevented, ✗ = can occur)
```

### Query Execution Plan

```
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123;

Output shows:
  Seq Scan / Index Scan / Index Only Scan
  Filter conditions
  Rows estimated vs actual
  Cost (planning + execution time)
  
Mental model:
  Query → Parser → Planner → (chooses best plan based on statistics) → Executor

QUERY OPTIMIZATION:
  - Use indexes on columns in WHERE, JOIN, ORDER BY
  - Avoid SELECT * (use covering index instead)
  - Avoid functions on indexed columns in WHERE (disables index)
  - Use LIMIT for pagination
  - Proper JOIN order (smaller table first when possible)
  - Analyze query with EXPLAIN ANALYZE (actual timings)
```

---

## 40. NoSQL Design Patterns

### Denormalization

```
NORMALIZATION (SQL approach):
  Users table: {id, name}
  Posts table: {id, user_id, title}
  To get username with post: JOIN users + posts.

DENORMALIZATION (NoSQL approach):
  Posts document: {id, user_id, user_name, title}
  No JOIN needed. Read in one query.
  
  Cost: Duplicated data. Must update all copies on change.
  Benefit: Read performance, simpler queries.
```

### Data Modeling for Cassandra

```
RULE: Model for your query patterns, not your data structure.

Anti-pattern (SQL thinking):
  Users table: (user_id, name, email)
  Orders table: (order_id, user_id, product_id, amount)

Cassandra approach (for "get all orders by user"):
  orders_by_user table: (user_id, order_date, order_id, product_id, amount)
  Partition key: user_id
  Clustering key: order_date (sorted)

One table per query pattern.
```

---

# PART V — MESSAGING & STREAMING (Extended)

---

## 41. Event-Driven Architecture

```
CORE CONCEPTS:
  Event: Something that happened (immutable fact).
  Event Producer: Generates events.
  Event Consumer: Reacts to events.
  Event Broker: Routes events (Kafka, SNS, EventBridge).
  Event Store: Persists events (Kafka, Event Sourcing).

PATTERNS:
  ┌─────────────────────────────────────────────────────────────┐
  │  Event Notification: "Something happened" (no data payload) │
  │  Event-Carried State Transfer: "X changed to Y"            │
  │  Event Sourcing: Entire state = log of all events          │
  └─────────────────────────────────────────────────────────────┘
```

### Event Sourcing

```
TRADITIONAL: Store current state.
  users row: {id: 1, balance: 100}
  → balance changes → UPDATE row.

EVENT SOURCING: Store all events. Derive current state.
  events:
    {type: "AccountOpened", balance: 0}
    {type: "Deposited", amount: 200}
    {type: "Withdrawn", amount: 100}
  
  Replay events → current balance = 100.
  
BENEFITS:
  Complete audit log.
  Time travel (replay to any point in time).
  Event-driven integration.
  Debugging (what led to this state?).

CHALLENGES:
  Event schema evolution.
  Snapshots needed for performance (don't replay from beginning always).
  Complexity.

CQRS (Command Query Responsibility Segregation):
  Separate WRITE model (command) from READ model (query).
  Write: process commands, emit events.
  Read: materialized views, optimized for queries.
  
  Command ──► Write Model ──► Event ──► Update Read Model
  Query  ──► Read Model (denormalized, fast)
```

---

# PART VI — LINUX KERNEL CONCEPTS

---

## 42. Linux Kernel Architecture

**What is the Linux Kernel?** The core program that manages hardware resources and provides services to user-space programs.

```
LINUX SYSTEM ARCHITECTURE:

┌─────────────────────────────────────────────────────────────────┐
│                     USER SPACE                                  │
│   Applications: bash, vim, nginx, python scripts...             │
│   Libraries: glibc, libstdc++, libpthread...                   │
├─────────────────────────────────────────────────────────────────┤
│                  SYSTEM CALL INTERFACE                          │
│         (gateway between user space and kernel)                 │
├─────────────────────────────────────────────────────────────────┤
│                     KERNEL SPACE                                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Process Management │ Memory Management │ File System     │  │
│  │  Scheduler          │ Virtual Memory    │ VFS             │  │
│  │  Signals            │ Page Cache        │ ext4, XFS, btrfs│  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Network Stack (TCP/IP) │ IPC │ Security (SELinux, seccomp│  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │  Device Drivers  │  Hardware Abstraction Layer           │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     HARDWARE                                    │
│   CPU │ RAM │ Disk │ NIC │ GPU │ I/O Controllers               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 43. System Calls

**What is a System Call?** The mechanism by which a user-space program requests a service from the kernel.

```
USER MODE vs KERNEL MODE:
  User Mode: Limited CPU privileges. Cannot access hardware directly.
  Kernel Mode: Full CPU privileges. Can do anything.

SYSTEM CALL FLOW:
  1. Program calls libc wrapper (e.g., read())
  2. Wrapper sets up args in registers
  3. Executes syscall instruction (triggers software interrupt or SYSCALL opcode)
  4. CPU switches to kernel mode (ring 0)
  5. Kernel handles the request
  6. Kernel returns result in register
  7. CPU switches back to user mode (ring 3)

EXAMPLE SYSTEM CALLS:
┌────────────────────────────────────────────────────────────────┐
│  Category     │ Syscalls                                       │
├───────────────┼────────────────────────────────────────────────┤
│  Process      │ fork, exec, exit, wait, getpid, kill           │
│  File I/O     │ open, read, write, close, lseek, mmap, stat   │
│  Memory       │ brk, mmap, munmap, mprotect                   │
│  Network      │ socket, bind, listen, accept, connect, send   │
│  IPC          │ pipe, msgget, shmget, semget                   │
│  Time         │ time, clock_gettime, nanosleep                 │
│  Users        │ getuid, setuid, getgroups                      │
└────────────────────────────────────────────────────────────────┘

View syscalls with strace:
  strace -c ls
  strace -e trace=network curl google.com
```

---

## 44. Process Management

### Process vs Thread vs Coroutine

```
PROCESS:
  Independent program instance.
  Own memory space (isolated).
  Own file descriptor table.
  Own PID.
  Communication: IPC (pipes, shared memory, sockets).
  Context switch: Expensive (~microseconds).

THREAD (within a process):
  Shares memory space with parent process.
  Own stack, registers, PC.
  Lighter context switch.
  Communication: Shared memory (needs synchronization!).

GOROUTINE (Go's coroutine):
  M:N threading model.
  Many goroutines multiplexed on few OS threads.
  VERY lightweight (~2KB stack, grows dynamically).
  Managed by Go runtime scheduler.

RUST ASYNC (Future/Task):
  Compile-time state machines.
  No heap allocation per "task".
  Executor polls futures.

LINUX THREAD MODEL:
  Linux implements threads as "lightweight processes" (clone() syscall).
  NPTL (Native POSIX Thread Library) maps pthreads to kernel tasks.
```

### Process States

```
PROCESS STATE MACHINE:

         fork()
           │
           ▼
        CREATED
           │
           ▼
        RUNNABLE ◄─────────────────────────┐
           │                               │
     scheduler picks                  I/O complete /
           │                          signal received
           ▼                               │
        RUNNING ──────────────────────► WAITING
           │              I/O, sleep       │
           │              syscall          │
      exit() / signal
           │
           ▼
        ZOMBIE ──────────► DEAD
       (parent hasn't        (parent called wait())
        called wait() yet)

PROCESS STATES (Linux):
  R = Running (or runnable)
  S = Sleeping (interruptible)
  D = Sleeping (uninterruptible) — waiting for I/O
  T = Stopped (SIGSTOP)
  Z = Zombie
  X = Dead
```

### Linux Scheduler (CFS — Completely Fair Scheduler)

```
CFS DESIGN:
  Goal: Give each runnable process an equal share of CPU.
  
  vruntime: Virtual runtime — how long a process has run.
  Process with LOWEST vruntime runs next.
  
  Data structure: Red-Black Tree keyed by vruntime.
  O(log n) insert/find/delete.

NICE VALUES:
  -20 (highest priority) to +19 (lowest priority).
  Default: 0.
  Nice = higher → less CPU time.
  
  sudo nice -n -10 myprogram  (higher priority)

REAL-TIME SCHEDULERS (for latency-critical work):
  SCHED_FIFO: First in, first out. Runs until done or blocked.
  SCHED_RR: Round-robin between same priority RT tasks.
  SCHED_DEADLINE: Deadline-based scheduling.

SCHEDULING DOMAINS:
  Hierarchical grouping of CPUs (core → socket → NUMA node).
  Load balancing happens within domains.
  NUMA-aware: prefer local memory.
```

---

## 45. Memory Management

### Virtual Memory

**What is Virtual Memory?** Every process sees a private, contiguous address space that may be much larger than physical RAM. The kernel maps virtual addresses to physical addresses.

```
VIRTUAL ADDRESS SPACE (64-bit Linux process):

  0xFFFFFFFFFFFFFFFF
  ┌─────────────────┐
  │  Kernel Space   │  (inaccessible from user space)
  ├─────────────────┤
  │  Stack          │  ← grows downward
  │      ↓          │
  │   (gap)         │
  │      ↑          │
  │  Heap           │  ← grows upward (malloc, brk)
  ├─────────────────┤
  │  BSS            │  (uninitialized global variables)
  ├─────────────────┤
  │  Data           │  (initialized global variables)
  ├─────────────────┤
  │  Text           │  (program code — read-only)
  ├─────────────────┤
  │  Reserved       │
  0x0000000000000000
```

### Paging and Page Tables

```
PAGING:
  Memory divided into fixed-size pages (typically 4KB).
  Virtual pages mapped to physical frames via page table.
  
  Virtual Address = [VPN | Offset]
                     Virtual    byte within
                     Page No.   the page

PAGE TABLE WALK (4-level on x86-64):
  CR3 register → PGD → PUD → PMD → PTE → Physical Frame
                 (4 memory accesses for every page translation!)

TLB (Translation Lookaside Buffer):
  Cache for page table entries.
  If TLB hit: 0 memory accesses.
  If TLB miss: walk page table (expensive).
  
  TLB is per-CPU. Context switch → TLB flush (or tagged with ASID).

HUGE PAGES:
  Instead of 4KB pages → 2MB or 1GB pages.
  Fewer TLB entries needed. Better performance for large working sets.
  Linux: Transparent Huge Pages (THP) or explicit hugepages.
```

### Page Fault

```
PAGE FAULT: CPU accesses virtual address with no valid PTE.
  Kernel handles: interrupt → page fault handler.

TYPES:
  Minor fault: Page in memory but PTE not set. (e.g., lazy allocation)
  Major fault: Page not in memory. Must fetch from disk (SLOW!).
  Protection fault: Write to read-only page → SIGSEGV.

COW (Copy-on-Write):
  After fork(), parent and child share same physical pages (read-only).
  First write by either → page fault → kernel copies page → both get private copy.
  Avoids copying all memory on fork (huge optimization).
```

### Memory Allocators

```
KERNEL ALLOCATORS:
  slab allocator: Pre-allocates caches of fixed-size objects.
    kmalloc (for small objects) → slab.
  buddy system: Manages physical pages in powers of 2.

USER SPACE ALLOCATORS (glibc):
  brk()/sbrk(): Extend heap.
  mmap(): Large allocations (> 128KB).
  
  malloc() → ptmalloc (glibc): Per-thread arenas, bins of sizes.
  
  ALTERNATIVE ALLOCATORS:
  jemalloc (used by Firefox, Rust): Low fragmentation, per-CPU.
  tcmalloc (Google): Thread-caching, fast for multi-threaded.
  mimalloc (Microsoft): Modern, fast, small.

OOM KILLER:
  When system runs out of memory → kernel kills a process.
  Scores processes by memory use, priority, age.
  oom_score_adj: tune per-process (-1000 to 1000).
```

### Memory Mapping (mmap)

```
mmap() system call:
  Map files or devices into virtual memory space.
  
USE CASES:
  File I/O without read()/write() (zero-copy reads).
  Shared memory between processes (MAP_SHARED).
  Anonymous memory (heap, stack growth).
  Executable loading (.text, .data sections).

In Rust:
  use std::fs::File;
  use memmap2::Mmap;
  let file = File::open("data.bin")?;
  let mmap = unsafe { Mmap::map(&file)? };
  // Access mmap[0..n] like a slice.

BENEFITS vs read()/write():
  Page cache used directly.
  No syscall overhead for every access.
  OS handles prefetching.
```

---

## 46. File Systems

### Virtual File System (VFS)

**What is VFS?** An abstraction layer in the Linux kernel that provides a uniform interface for different file system implementations.

```
User Space: open("file.txt", O_RDONLY)
                │
                ▼
         System Call Layer
                │
                ▼
            VFS Layer
                │
       ┌────────┼────────┐
       ▼        ▼        ▼
     ext4     XFS      tmpfs    ← actual file system implementations
       │        │        │
   disk I/O  disk I/O  RAM
```

### VFS Abstractions

```
SUPERBLOCK: Metadata about the file system.
  (block size, total blocks, free blocks, mount info)

INODE (Index Node): Metadata about a file.
  (size, owner UID/GID, permissions, timestamps, block pointers)
  NOT the filename — filenames are in directory entries.

DENTRY (Directory Entry): Maps filename → inode number.
  Directory = list of dentries.

FILE: In-memory representation of an open file.
  (current offset, flags, reference to inode)

INODE vs FILENAME:
  Multiple filenames can point to same inode (hard links).
  Inode deleted only when link count = 0 AND file not open.
```

### ext4

```
EXT4 FEATURES:
  Extents: Contiguous block ranges (vs block pointers in ext2/3).
  Journaling: Changes logged to journal before applying.
    journal_mode=data: journal metadata + data (safest, slowest)
    journal_mode=ordered: journal metadata; data flushed first (default)
    journal_mode=writeback: journal metadata only (fastest, least safe)
  Delayed allocation: Batches writes for better block placement.
  64-bit block addresses.
  Online defragmentation.

DIRECTORY INDEXING:
  HTree: Hash-tree for large directories. O(log n) lookup.
```

### XFS

```
XFS ADVANTAGES:
  Excellent scalability for large files and filesystems.
  Allocation groups (parallel I/O).
  Extent-based allocation.
  Online resizing (only grow, not shrink).
  Reverse mapping: block → inode/offset (for fast repair).
  No journal mode options — always metadata + data in journal.
```

### Btrfs

```
BTRFS FEATURES:
  Copy-on-Write (COW): Never overwrites data in place.
  Snapshots: O(1) snapshots (just COW the root).
  Checksums on data and metadata (catches silent corruption).
  RAID built-in (RAID 0/1/5/6/10).
  Subvolumes: Multiple independent namespaces.
  Send/receive for efficient backup.
  Online scrub (verify all checksums while running).
  Compression: zlib, LZO, ZSTD.
```

### tmpfs

```
TMPFS:
  In-memory file system. Lives in RAM/swap.
  Performance: Memory speed.
  Use: /tmp, /run, shared memory (/dev/shm).
  Lost on reboot.
```

---

## 47. I/O Models

### Blocking I/O

```
Process calls read(fd, buf, len).
Process BLOCKS. Kernel waits for data.
Data arrives. Kernel copies to user buf. Returns.

[Process]────────WAITING──────────────►resume
          │                           ▲
          │        KERNEL             │
          └──────────────────────────►┘
```

### Non-Blocking I/O

```
Process calls read() with O_NONBLOCK.
If no data: immediately returns EAGAIN.
Process must poll in a loop (busy wait).

while (true) {
    n = read(fd, buf, len);
    if (n == -1 && errno == EAGAIN) {
        // no data yet, try again
        continue;
    }
    // process data
}
```

### I/O Multiplexing (select/poll/epoll)

**The fundamental technique behind high-performance servers.**

```
PROBLEM: Server has 10,000 connections. Most are idle.
  Can't block on each one (need 10,000 threads).
  Can't busy-poll all (wastes CPU).

SOLUTION: epoll — kernel tells you WHICH fds are ready.

SELECT (old, O(n) per call, max ~1024 fds):
  fd_set readfds;
  FD_SET(sock_fd, &readfds);
  select(n_fds, &readfds, NULL, NULL, &timeout);

POLL (slightly better, no fd limit but still O(n)):
  Similar to select.

EPOLL (Linux, O(1) for n ready fds):
  // Create epoll instance
  epfd = epoll_create1(0);
  
  // Register interest in fd
  ev.events = EPOLLIN | EPOLLET; // edge-triggered
  ev.data.fd = conn_fd;
  epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &ev);
  
  // Wait for events
  n = epoll_wait(epfd, events, MAX_EVENTS, timeout);
  for (i = 0; i < n; i++) {
      handle(events[i].data.fd);
  }

EPOLL MODES:
  Level-triggered (LT): Wake up as long as data is available.
  Edge-triggered (ET): Wake up only on NEW data arrival.
    ET requires reading ALL data when notified (loop until EAGAIN).
    ET more efficient but harder to program.

KQUEUE (macOS/BSD equivalent of epoll).
IO_URING (modern Linux, even faster — kernel ring buffer).
```

### io_uring (Modern Linux I/O)

```
io_uring (Linux 5.1+):
  Shared ring buffers between kernel and user space.
  Submission Queue (SQ): User writes I/O requests.
  Completion Queue (CQ): Kernel writes results.
  
  Eliminates system call overhead for batched I/O.
  Supports both network and disk I/O.
  Zero-copy possible.
  
  FLOW:
  User ──► SQ ring ──► Kernel submits ──► I/O completes ──► CQ ring ──► User
  (No syscall needed per operation — just memory writes!)

  Used by: SPDK, RocksDB, io_uring-based HTTP servers, Tokio (Rust).
```

### Signals and Async I/O (POSIX AIO)

```
SIGNALS:
  SIGINT  (2):  Ctrl-C
  SIGTERM (15): Graceful shutdown (default kill)
  SIGKILL (9):  Immediate kill (cannot be caught)
  SIGCHLD (17): Child process terminated
  SIGSEGV (11): Segmentation fault
  SIGPIPE (13): Write to closed pipe
  
  signal(SIGTERM, handler) — set handler function
  sigaction() — more powerful handler setup

  Signal masks: per-thread set of blocked signals.
```

---

## 48. Linux Inter-Process Communication (IPC)

```
┌────────────────────────────────────────────────────────────────────┐
│  Mechanism        │ Speed     │ Direction    │ Notes               │
├───────────────────┼───────────┼──────────────┼─────────────────────┤
│  Pipe (|)         │ Fast      │ One-way      │ Parent-child only   │
│  Named Pipe (FIFO)│ Fast      │ One-way      │ Any processes       │
│  Unix Domain Sock │ Very fast │ Bidirectional│ Same host only      │
│  TCP/UDP Socket   │ Fast      │ Bidirectional│ Network-capable     │
│  Shared Memory    │ Fastest   │ Both         │ Needs synchronization│
│  Message Queue    │ Fast      │ Multi-read   │ POSIX or SysV       │
│  Signal           │ Fast      │ One-way      │ Control only        │
│  Semaphore        │ Fast      │ Sync only    │ Not for data        │
│  D-Bus            │ Slow(er)  │ Both         │ Desktop Linux IPC   │
└────────────────────────────────────────────────────────────────────┘

SHARED MEMORY EXAMPLE (Rust using nix crate):
  Process A: creates shm_open() segment, writes data.
  Process B: opens same shm_open() segment, reads data.
  Both mmap() the same physical pages.
  Need semaphore/mutex for synchronization.
```

---

## 49. Linux Networking Stack

```
PACKET RECEIVE PATH (simplified):

  NIC receives packet
       │
       ▼
  DMA to ring buffer (in RAM)
       │
       ▼
  Hardware interrupt → kernel IRQ handler
       │
       ▼
  NAPI (softirq): poll NIC, batch packets
       │
       ▼
  net_rx_action → netif_receive_skb
       │
       ▼
  Protocol demux: IP layer
       │
       ▼
  TCP/UDP layer (socket buffer / sk_buff)
       │
       ▼
  Copy to user space receive buffer
       │
       ▼
  Application: recv() / read()

SK_BUFF (Socket Buffer):
  The fundamental data structure for network packets in Linux kernel.
  Contains: header pointers, data pointer, length, protocol info.
  Avoids copying data — just moves pointers (zero-copy internally).

NETFILTER:
  Hook framework in the network stack.
  iptables / nftables rules applied here.
  Hooks: PREROUTING, INPUT, FORWARD, OUTPUT, POSTROUTING.
```

### Network Namespaces

```
NETWORK NAMESPACE:
  Isolated network stack. Each namespace has:
    Own interfaces (eth0, lo)
    Own routing table
    Own iptables rules
    Own sockets
  
  Used by: Docker containers, Kubernetes pods, LXC.
  
  ip netns add myns
  ip netns exec myns ip addr show
  ip link set eth0 netns myns
```

### tc (Traffic Control) / QoS

```
TRAFFIC CONTROL:
  qdisc (queuing discipline): How packets are queued before sending.
  
  pfifo_fast: Default. Three FIFO bands (priority-based).
  tbf (Token Bucket Filter): Rate limiting.
  htb (Hierarchical Token Bucket): Bandwidth shaping with classes.
  fq_codel: Flow queue CoDel. Reduces bufferbloat.
  
  tc qdisc add dev eth0 root tbf rate 1mbit burst 32kbit latency 400ms
  (limit eth0 to 1 Mbit/s)
```

---

## 50. cgroups (Control Groups)

**What are cgroups?** A Linux kernel feature that limits, accounts for, and isolates resource usage (CPU, memory, I/O, network) of process groups.

**Used by:** Docker, Kubernetes, systemd.

```
CGROUPS V2 HIERARCHY:
  /sys/fs/cgroup/
  ├── system.slice/
  │   ├── sshd.service/
  │   └── nginx.service/
  └── user.slice/
      └── user-1000.slice/

CONTROLLABLE RESOURCES:
  cpu: CPU time allocation (cpu.max = quota/period)
  memory: RAM + swap limits (memory.max)
  io: Block I/O limits (io.max)
  pids: Limit process count (pids.max)
  net_cls: Tag network packets for traffic control
  devices: Control device access
  freezer: Pause/resume processes

EXAMPLE (limit container to 1 CPU, 512MB RAM):
  echo "512M" > /sys/fs/cgroup/mycontainer/memory.max
  echo "100000 100000" > /sys/fs/cgroup/mycontainer/cpu.max
  # (100000µs out of 100000µs period = 1 CPU)
```

---

## 51. Linux Namespaces

**What are Namespaces?** A kernel feature that provides isolation of system resources. Foundation of containers.

```
┌──────────────────────────────────────────────────────────────────┐
│  Namespace  │ Isolates                     │ Created by clone()  │
├─────────────┼──────────────────────────────┼─────────────────────┤
│  PID        │ Process IDs                  │ CLONE_NEWPID        │
│  Network    │ Network stack, interfaces    │ CLONE_NEWNET        │
│  Mount      │ Filesystem mount points      │ CLONE_NEWNS         │
│  UTS        │ Hostname, domainname         │ CLONE_NEWUTS        │
│  IPC        │ SysV IPC, POSIX mq           │ CLONE_NEWIPC        │
│  User       │ UID/GID mappings             │ CLONE_NEWUSER       │
│  Cgroup     │ cgroup visibility            │ CLONE_NEWCGROUP     │
│  Time       │ Clock offsets (Linux 5.6+)   │ CLONE_NEWTIME       │
└──────────────────────────────────────────────────────────────────┘

CONTAINERS = namespaces + cgroups + filesystems (overlayfs).

Docker run process:
  1. clone() with namespace flags
  2. Set up cgroup limits
  3. Mount overlay filesystem (image layers + writable layer)
  4. chroot / pivot_root (change root directory)
  5. exec() application
```

---

## 52. eBPF (Extended Berkeley Packet Filter)

**What is eBPF?** A revolutionary Linux kernel technology that allows running sandboxed programs in kernel space without changing kernel source code.

```
TRADITIONAL APPROACH:
  Add monitoring → modify kernel → recompile → patch → reboot.
  Very slow and risky.

EBPF APPROACH:
  Write eBPF program → verify (safety check) → JIT compile → run in kernel.
  No recompile. No reboot. Safe.

EBPF CAPABILITIES:
  Trace any kernel function (kprobes, tracepoints)
  Trace user-space functions (uprobes)
  Network packet processing (XDP — extremely fast)
  Security enforcement (LSM hooks)
  Performance profiling
  Custom metrics

EBPF PROGRAM TYPES:
  XDP (eXpress Data Path): Before sk_buff, at driver level. Fastest.
  TC (Traffic Control): In qdisc. Can modify packets.
  Kprobe: Attach to any kernel function.
  Uprobe: Attach to user-space function.
  Tracepoint: Kernel static tracing hooks.
  Socket filter: Filter packets at socket level.
  LSM: Security hooks.

TOOLS USING EBPF:
  bcc: Python framework for eBPF tools.
  bpftrace: Awk-like language for tracing.
  Cilium: Kubernetes CNI networking + security using eBPF.
  Falco: Runtime security using eBPF.
  Pixie: Auto-telemetry using eBPF.
  Parca: CPU profiling using eBPF.

XDP FLOW (packet processing before kernel TCP/IP):
  NIC → XDP program → decision:
    XDP_DROP: drop packet (DDoS mitigation, fastest!)
    XDP_PASS: pass to normal kernel stack
    XDP_TX: retransmit out the same interface
    XDP_REDIRECT: redirect to another interface/socket
    XDP_ABORTED: error

  XDP can process millions of packets/sec, much faster than iptables.
```

---

## 53. Linux Performance Tools

```
CPU:
  top / htop       — process CPU usage
  perf stat        — hardware counters (IPC, cache misses)
  perf record/report — CPU profiling, flame graphs
  mpstat           — per-CPU statistics
  vmstat           — CPU, memory, I/O overview

MEMORY:
  free -h          — memory usage summary
  /proc/meminfo    — detailed memory stats
  pmap <pid>       — process memory map
  vmstat -s        — memory statistics
  smem             — per-process memory usage

DISK I/O:
  iostat -x        — disk I/O statistics
  iotop            — per-process I/O
  blktrace         — block layer tracing
  fio              — disk benchmark

NETWORK:
  ss -tunapl       — socket statistics (faster than netstat)
  netstat          — network connections
  iftop            — per-connection bandwidth
  nicstat          — NIC statistics
  tcpdump          — packet capture
  wireshark        — GUI packet analysis

TRACING:
  strace <cmd>     — trace system calls
  ltrace <cmd>     — trace library calls
  perf trace       — faster than strace
  bpftrace         — eBPF-based tracing
  ftrace           — kernel function tracing

SYSTEM OVERVIEW:
  dstat            — combined CPU/memory/disk/net
  sar              — historical stats (from sysstat)
  /proc/           — everything about the system
    /proc/cpuinfo
    /proc/<pid>/maps
    /proc/<pid>/fd/
    /proc/<pid>/status
```

---

## 54. Linux Security Features

### Capabilities

```
TRADITIONAL UNIX: root = all or nothing. Setuid = dangerous.

LINUX CAPABILITIES: Fine-grained privileges. Root powers split into ~40 capabilities.

┌────────────────────────────────────────────────────────────────┐
│  Capability         │ Allows                                   │
├─────────────────────┼──────────────────────────────────────────┤
│  CAP_NET_BIND_SERVICE│ Bind to ports < 1024                   │
│  CAP_NET_RAW        │ Raw sockets (ping)                       │
│  CAP_SYS_ADMIN      │ Many admin operations (the new root)     │
│  CAP_KILL           │ Kill any process                         │
│  CAP_CHOWN          │ Change file ownership                    │
│  CAP_DAC_OVERRIDE   │ Bypass file permission checks           │
│  CAP_SYS_PTRACE     │ Trace processes (strace/gdb)            │
└────────────────────────────────────────────────────────────────┘

Drop capabilities in containers:
  docker run --cap-drop=ALL --cap-add=NET_BIND_SERVICE myapp
```

### seccomp (Secure Computing Mode)

```
SECCOMP:
  Restricts which system calls a process can make.
  Even if process is compromised → can't call dangerous syscalls.
  
  Modes:
    SECCOMP_MODE_STRICT: Only read, write, exit, sigreturn.
    SECCOMP_MODE_FILTER: BPF-based filter — allow/deny per syscall.
  
  Docker applies a default seccomp profile (~40 syscalls blocked).
  
  EXAMPLE: Block kill() syscall:
    seccomp filter → if syscall == kill → SIGKILL the process.
```

### AppArmor / SELinux

```
MANDATORY ACCESS CONTROL (MAC):
  Beyond normal permissions — policies enforced by kernel.
  Even root cannot bypass MAC policy.

APPARMOR:
  Path-based MAC. Profiles per program.
  Profile: what files can be accessed, what capabilities, what networks.
  Modes: enforce (block), complain (log only).
  
  Used by Ubuntu, Snap packages.

SELINUX:
  Label-based MAC (type enforcement).
  Every file, process, port has a label (security context).
  Policy: allow <source_type> <target_type>:<class> <permissions>.
  
  Modes: enforcing, permissive (log only), disabled.
  
  Used by RHEL, CentOS, Fedora, Android.
  
  CHCON: change file security context.
  RESTORECON: restore to policy default.
  AUDIT2ALLOW: convert denials to policy rules.
```

### Linux Security Modules (LSM)

```
LSM FRAMEWORK:
  Hook-based security framework in kernel.
  Multiple LSMs can stack (AppArmor + Yama + etc).
  
  Implemented LSMs:
    SELinux, AppArmor, Smack, Tomoyo, YAMA, Landlock, BPF-LSM.
  
  Landlock: Unprivileged sandboxing. App restricts its own access.
  BPF-LSM: eBPF programs as LSM hooks. Dynamic security policies.
```

---

## 55. Kernel Compilation and Boot

```
LINUX BOOT PROCESS:

1. POWER ON
   │
   ▼
2. BIOS/UEFI
   POST (Power-On Self Test)
   Find bootable device.
   │
   ▼
3. BOOTLOADER (GRUB2)
   Load kernel image (vmlinuz) into RAM.
   Load initial RAM disk (initrd/initramfs).
   │
   ▼
4. KERNEL INIT
   Decompress kernel.
   Initialize hardware (CPU, memory, interrupts).
   Mount initramfs (temporary root filesystem).
   │
   ▼
5. EARLY USERSPACE (initrd)
   Mount real root filesystem.
   Pass control to init system.
   │
   ▼
6. INIT SYSTEM (systemd / SysV)
   PID 1. Parent of all processes.
   Mount filesystems (/proc, /sys, /dev).
   Start services.
   Reach target (multi-user.target, graphical.target).
   │
   ▼
7. LOGIN PROMPT / DESKTOP

VMLINUZ: Compressed kernel image.
INITRAMFS: Minimal RAM-based FS with drivers to mount real FS.
GRUB2 config: /boot/grub/grub.cfg
Kernel parameters: /proc/cmdline
```

---

## 56. systemd

```
SYSTEMD: System and service manager (PID 1 on most modern Linux).

UNIT TYPES:
  .service: A daemon or program.
  .target:  Group of units (multi-user.target, graphical.target).
  .socket:  Socket activation (start service on connection).
  .timer:   Cron-like scheduled execution.
  .mount:   Filesystem mount.
  .slice:   cgroup hierarchy.

SERVICE FILE (/etc/systemd/system/myapp.service):
  [Unit]
  Description=My Application
  After=network.target postgresql.service
  
  [Service]
  Type=simple
  User=myapp
  ExecStart=/usr/bin/myapp --config /etc/myapp.conf
  Restart=on-failure
  RestartSec=5
  LimitNOFILE=65536
  
  [Install]
  WantedBy=multi-user.target

COMMANDS:
  systemctl start/stop/restart/status myapp
  systemctl enable/disable myapp  (on boot)
  journalctl -u myapp -f          (logs)
  systemd-analyze blame           (slow units)
```

---

# PART VII — CLOUD NATIVE

---

## 57. Containers (Deep Dive)

### OCI (Open Container Initiative)

```
OCI SPECS:
  Runtime Spec: How to run a container (runc).
  Image Spec: How to package a container image.
  Distribution Spec: How to distribute images (registry API).

CONTAINER IMAGE:
  Layers (union filesystem):
  
  ┌──────────────────────────┐  ← Writable layer (container)
  ├──────────────────────────┤  ← App layer (COPY myapp .)
  ├──────────────────────────┤  ← Dependencies layer (pip install)
  ├──────────────────────────┤  ← Base OS layer (ubuntu:22.04)
  └──────────────────────────┘
  
  Each layer is content-addressed (SHA256 hash).
  Shared base layers → efficient storage.

OVERLAY FILESYSTEM:
  upperdir: writable layer.
  lowerdir: read-only image layers.
  merged: union view.
  
  Reads: check upper → fall through to lower layers.
  Writes: copy-on-write to upper layer.

CONTAINER RUNTIMES:
  runc: OCI reference runtime (used by Docker, containerd).
  crun: Faster, written in C.
  kata-containers: VM-based containers (stronger isolation).
  gVisor: User-space kernel (Google's sandbox).
```

### Docker Internals

```
DOCKER ARCHITECTURE:
  docker CLI ──► dockerd (daemon) ──► containerd ──► runc

DOCKERFILE BEST PRACTICES:
  # Use multi-stage builds to minimize final image size
  FROM rust:1.75 AS builder
  WORKDIR /app
  COPY Cargo.toml Cargo.lock ./
  RUN cargo fetch                        # cache dependencies layer
  COPY src ./src
  RUN cargo build --release
  
  FROM debian:bookworm-slim              # minimal runtime image
  COPY --from=builder /app/target/release/myapp /usr/local/bin/
  USER nonroot                           # don't run as root
  CMD ["myapp"]
  
LAYER CACHING:
  Each instruction → potential cache layer.
  Order: least-changing (dependencies) → most-changing (code).
  COPY package.json first → npm install → COPY source code.
  This way: code changes don't invalidate dependency cache.

CONTAINER NETWORKING MODES:
  bridge: Default. Private network with NAT.
  host:   Share host's network namespace.
  none:   No networking.
  overlay: Multi-host networking (Docker Swarm / Kubernetes).
  macvlan: Assign real MAC/IP to container.
```

---

## 58. Kubernetes (Deep Dive)

**What is Kubernetes?** An open-source container orchestration platform that automates deployment, scaling, and management of containerized applications.

### Architecture

```
KUBERNETES CLUSTER:

  ┌────────────────────────────────────────────────────────────┐
  │                    CONTROL PLANE                           │
  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
  │  │  API Server │  │  etcd        │  │  Scheduler     │   │
  │  │  (gateway)  │  │ (state store)│  │  (place pods)  │   │
  │  └─────────────┘  └──────────────┘  └────────────────┘   │
  │  ┌─────────────────────────────────────────────────────┐  │
  │  │  Controller Manager (reconciliation loops)          │  │
  │  │  (Deployment, ReplicaSet, Node, Endpoint, etc.)     │  │
  │  └─────────────────────────────────────────────────────┘  │
  └────────────────────────────────────────────────────────────┘

  ┌────────────────────────────────────────────────────────────┐
  │                    WORKER NODES                            │
  │  ┌──────────────────────────────────────────────────────┐ │
  │  │  kubelet   │  kube-proxy   │  container runtime      │ │
  │  ├──────────────────────────────────────────────────────┤ │
  │  │  Pod 1    │  Pod 2    │  Pod 3    │  Pod 4           │ │
  │  └──────────────────────────────────────────────────────┘ │
  └────────────────────────────────────────────────────────────┘

COMPONENTS:
  API Server: All cluster operations go through here. REST API + webhook.
  etcd: Distributed key-value store. All cluster state.
  Scheduler: Assigns pods to nodes based on resources, affinity, taints.
  Controller Manager: Control loops that reconcile desired → actual state.
  kubelet: Agent on each node. Ensures containers in pod are running.
  kube-proxy: Network proxy. Service load balancing on each node.
```

### Kubernetes Objects

```
POD: Smallest deployable unit. One or more containers sharing network + storage.

REPLICASET: Ensures N identical pods are running.

DEPLOYMENT: Manages ReplicaSets. Rolling updates, rollbacks.

STATEFULSET: Like Deployment but for stateful apps.
  - Stable network identity (pod-0, pod-1, pod-2).
  - Ordered startup/shutdown.
  - Persistent volume claims per pod.
  Used for: databases (Cassandra, MySQL clusters).

DAEMONSET: One pod per node. Used for: logging agents, monitoring.

JOB: Run to completion. CronJob: scheduled Job.

SERVICE: Stable network endpoint for a set of pods.
  ClusterIP: Internal-only IP.
  NodePort: Expose on each node's IP + port.
  LoadBalancer: Cloud LB in front.
  ExternalName: DNS alias.

INGRESS: HTTP(S) routing rules. (URL routing, TLS termination)

CONFIGMAP: Non-sensitive configuration (key-value or files).
SECRET: Sensitive data (base64 encoded, but not encrypted by default!).
  Use sealed-secrets or Vault for real secret management.

PERSISTENTVOLUME (PV): A piece of storage in the cluster.
PERSISTENTVOLUMECLAIM (PVC): A request for storage by a pod.

NAMESPACE: Virtual cluster. Isolates resources.

SERVICEACCOUNT: Identity for pods to call Kubernetes API.
```

### Kubernetes Networking

```
KUBERNETES NETWORKING MODEL:
  1. Every pod gets a unique IP.
  2. Pods can communicate with any other pod without NAT.
  3. Nodes can communicate with all pods.

CNI (Container Network Interface):
  Plugin that sets up pod networking.
  
  CNI PLUGINS:
    Flannel: Simple VXLAN overlay. Easy setup.
    Calico: BGP-based or VXLAN. Network policies. High performance.
    Cilium: eBPF-based. Identity-based policies. Very fast.
    Weave: Mesh overlay.
    AWS VPC CNI: Native VPC IPs for pods on AWS.

SERVICE NETWORKING (kube-proxy):
  Each Service gets a ClusterIP (virtual IP).
  kube-proxy (iptables mode): adds iptables DNAT rules.
    Packet to ClusterIP → iptables NAT → pod IP.
  kube-proxy (ipvs mode): Uses kernel IPVS for O(1) routing.
  Cilium can replace kube-proxy using eBPF.

DNS IN KUBERNETES:
  CoreDNS deployed in cluster.
  Service DNS: <service>.<namespace>.svc.cluster.local
  Pod DNS: <ip>.<namespace>.pod.cluster.local

NETWORK POLICIES:
  Firewall rules for pods.
  Whitelist model (deny all by default, allow specific).
  
  Example: Only allow frontend pods to reach backend pods on port 8080.
  Enforced by CNI plugin (Calico, Cilium).
```

### Kubernetes Scheduling

```
SCHEDULER DECISION PROCESS:
  1. Filter: Remove nodes that don't satisfy constraints.
     (Not enough CPU/memory, taints without tolerations, affinity rules)
  2. Score: Rank remaining nodes.
     (LeastRequestedPriority, ImageLocalityPriority, etc.)
  3. Select: Highest score wins.

RESOURCE REQUESTS AND LIMITS:
  resources:
    requests:               # Guaranteed minimum
      cpu: "250m"           # 250 millicores = 0.25 CPU
      memory: "256Mi"
    limits:                 # Hard ceiling
      cpu: "1000m"
      memory: "512Mi"
  
  CPU: compressible (throttled, not killed if exceeded).
  Memory: non-compressible (OOM killed if exceeded).

QOS CLASSES:
  Guaranteed: requests == limits. Never evicted first.
  Burstable:  requests < limits.
  BestEffort: No requests/limits set. Evicted first.

TAINTS AND TOLERATIONS:
  Taint: Mark a node as "repelling" certain pods.
    kubectl taint nodes node1 key=value:NoSchedule
  Toleration: Pod's permission to be scheduled on tainted node.

NODE AFFINITY:
  requiredDuringScheduling: Hard constraint.
  preferredDuringScheduling: Soft preference.
  
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: topology.kubernetes.io/zone
          operator: In
          values: [us-east-1a]

POD AFFINITY / ANTI-AFFINITY:
  Co-locate pods (affinity) or spread them (anti-affinity).
  
  podAntiAffinity:
    requiredDuringScheduling:
    - topologyKey: "kubernetes.io/hostname"  # one pod per node
```

### Kubernetes Operators

```
OPERATOR PATTERN:
  Extend Kubernetes with custom resources (CRDs).
  Operator = CRD + custom controller.
  Encodes operational knowledge in software.

CUSTOM RESOURCE DEFINITION (CRD):
  Define new API types.
  e.g., PostgreSQLCluster, RedisCluster, KafkaTopic.

CONTROLLER RECONCILIATION LOOP:
  while true {
    desired = get desired state from Kubernetes API
    actual  = get actual state from infrastructure
    if desired != actual {
      reconcile()  // make actual match desired
    }
    sleep()
  }

EXAMPLES:
  Prometheus Operator: manages Prometheus + AlertManager.
  Cert-Manager: automates TLS certificates (Let's Encrypt).
  Strimzi: Kafka on Kubernetes.
  Crossplane: Infrastructure as Kubernetes resources.
  KEDA: Event-driven autoscaling.
```

### Kubernetes Storage

```
STORAGE CLASSES:
  Define types of storage (SSD, HDD, NFS, cloud).
  PVC references StorageClass → dynamic provisioning.

VOLUME PLUGINS → CSI (Container Storage Interface):
  CSI: Standard interface for storage vendors.
  CSI drivers: AWS EBS, Google PD, Azure Disk, Ceph, Longhorn.

STATEFULSET + PVC:
  Each pod gets its own PVC (volumeClaimTemplates).
  PVC survives pod restart.
  pod-0 → pvc-0, pod-1 → pvc-1, pod-2 → pvc-2.

ACCESS MODES:
  ReadWriteOnce (RWO): One node can mount read-write.
  ReadOnlyMany  (ROX): Many nodes, read-only.
  ReadWriteMany (RWX): Many nodes, read-write. (NFS, CephFS, EFS)
```

### Kubernetes Autoscaling

```
HPA (Horizontal Pod Autoscaler):
  Scale number of pods based on metrics.
  Built-in: CPU, memory utilization.
  Custom: HTTP RPS, queue depth (via KEDA).
  
  target: 80% CPU → scale out when average > 80%.

VPA (Vertical Pod Autoscaler):
  Adjust CPU/memory requests automatically.
  Modes: Off (recommend only), Initial, Auto (restart pods).

CLUSTER AUTOSCALER:
  Add/remove NODES based on unschedulable pods.
  Works with cloud provider node groups.

KEDA (Kubernetes Event-Driven Autoscaling):
  Scale based on external event sources.
  Kafka topic lag, SQS queue depth, Prometheus metrics.
  Can scale to ZERO (and back up on demand).
```

---

## 59. Service Mesh

**What is a Service Mesh?** An infrastructure layer for handling service-to-service communication, adding observability, security, and traffic management transparently.

```
WITHOUT SERVICE MESH:
  Each service implements: retry, timeout, circuit breaker, mTLS, tracing.
  Duplicated logic in every service. Language-specific.

WITH SERVICE MESH:
  Sidecar proxy (Envoy) injected into each pod.
  All traffic flows through sidecar.
  Common concerns handled by infrastructure, not app code.

ARCHITECTURE:
  ┌─────────────────────────────────────────────────────────────┐
  │  Pod A                      Pod B                           │
  │  ┌──────────┐              ┌──────────┐                     │
  │  │  App A   │              │  App B   │                     │
  │  │          │              │          │                     │
  │  │  Envoy   │──mTLS──────► │  Envoy   │                     │
  │  │ (sidecar)│              │ (sidecar)│                     │
  │  └──────────┘              └──────────┘                     │
  │       │                         │                           │
  │       └──── Control Plane ──────┘                          │
  │             (Istiod / Linkerd)                              │
  └─────────────────────────────────────────────────────────────┘

FEATURES:
  mTLS: Mutual TLS between all services (zero-trust networking).
  Traffic Management: Canary, A/B testing, traffic splitting.
  Observability: Distributed traces, metrics, logs from sidecars.
  Circuit Breaking: Configured in mesh, not in app code.
  Fault Injection: Testing resilience (inject latency, errors).
  Rate Limiting: Per-service, per-user limits.

SERVICE MESHES:
  Istio: Most feature-rich. Complex. Uses Envoy sidecars.
  Linkerd: Simpler. Rust-based proxy (ultralight).
  Consul Connect: HashiCorp's mesh.
  Kuma/Kong Mesh: Multi-zone mesh.
  Cilium Service Mesh: eBPF-based (no sidecars!).
```

---

## 60. GitOps and CI/CD

```
CI/CD PIPELINE:
  Developer pushes code
          │
          ▼
  CI: build, test, lint, security scan
          │ (on merge to main)
          ▼
  Build container image
          │
          ▼
  Push to registry (with immutable tag = git SHA)
          │
          ▼
  CD: Update manifest / Helm values
          │
          ▼
  Deploy to staging → automated tests
          │ (approval gate)
          ▼
  Deploy to production (blue/green or canary)

GITOPS:
  Principle: Git is the single source of truth for desired state.
  Operator (ArgoCD, Flux) continuously reconciles cluster → git.
  
  Changes → PR → merge → auto-deploy.
  No direct kubectl apply in production.
  
  TOOLS:
    ArgoCD: UI-rich GitOps controller.
    Flux: Lightweight GitOps with Helm/Kustomize support.

DEPLOYMENT STRATEGIES:
  Recreate:     Stop old, start new. Downtime.
  Rolling:      Replace pods gradually. No downtime.
  Blue/Green:   Run both versions, switch traffic. Instant rollback.
  Canary:       Send small % of traffic to new version. Gradual.
  A/B Testing:  Route based on user attributes.
  Shadow:       Mirror traffic to new version (no real users affected).

BLUE/GREEN:
  Blue (v1) ◄── 100% traffic
  Green (v2) ─── 0% traffic (deployed, tested)
  Switch: Blue ← 0%  Green ← 100%
  If problem: Switch back immediately.

CANARY:
  v1 ◄── 95% traffic
  v2 ◄── 5% traffic (canary)
  Monitor: error rate, latency.
  If ok: 10% → 25% → 50% → 100%.
  If bad: rollback to 0%.
```

---

## 61. Helm

```
HELM: Package manager for Kubernetes.
  Chart: Package of Kubernetes manifests (templates + values).
  Release: Deployed instance of a chart.
  Repository: Collection of charts.

CHART STRUCTURE:
  mychart/
  ├── Chart.yaml        (metadata: name, version, description)
  ├── values.yaml       (default values)
  ├── templates/        (Go template Kubernetes manifests)
  │   ├── deployment.yaml
  │   ├── service.yaml
  │   └── _helpers.tpl  (template helpers)
  └── charts/           (dependencies)

COMMANDS:
  helm install myapp ./mychart --values prod-values.yaml
  helm upgrade myapp ./mychart --set image.tag=1.2.3
  helm rollback myapp 1
  helm list
  helm template ./mychart (render without installing)
```

---

## 62. Infrastructure as Code (IaC)

```
TERRAFORM (HashiCorp):
  Declarative HCL language.
  Providers for every cloud (AWS, GCP, Azure, k8s).
  State file tracks real resources.
  Plan → Apply → Destroy workflow.
  
  resource "aws_instance" "web" {
    ami           = "ami-0c55b159cbfafe1f0"
    instance_type = "t2.micro"
    tags = { Name = "WebServer" }
  }

PULUMI:
  IaC using real programming languages (Rust, Go, Python, TypeScript).
  
  // Rust example
  let server = aws::ec2::Instance::new("web", &aws::ec2::InstanceArgs {
      instance_type: pulumi_aws::ec2::InstanceType::T2_Micro.to_string().into(),
      ami: "ami-0c55b159cbfafe1f0".into(),
  }, None)?;

ANSIBLE:
  Agentless configuration management.
  YAML playbooks. SSH-based.
  Idempotent tasks.
  Better for configuration management than provisioning.

CHEF / PUPPET:
  Agent-based configuration management (older).
  Chef: Ruby DSL. Puppet: Puppet DSL.

CROSSPLANE:
  Manage cloud infrastructure using Kubernetes CRDs.
  Git → Kubernetes → Cloud resources.
  "Terraform but as a Kubernetes controller."
```

---

## 63. Cloud Providers and Services

### Core AWS Services

```
COMPUTE:
  EC2: Virtual machines. Many instance types (memory, CPU, GPU optimized).
  Lambda: Serverless functions. Pay per invocation.
  ECS: Container orchestration (Docker). Without Kubernetes.
  EKS: Managed Kubernetes.
  Fargate: Serverless containers (no node management).
  Spot Instances: Unused EC2 capacity. Up to 90% cheaper. Interruptible.

STORAGE:
  S3: Object storage. Unlimited capacity. 11 nines durability.
  EBS: Block storage for EC2 (like a hard disk).
  EFS: Shared file system (NFS-compatible). Multi-AZ.
  Glacier: Cold archival storage. Very cheap, slow retrieval.

DATABASES:
  RDS: Managed relational DB (MySQL, PostgreSQL, MariaDB, Oracle, SQL Server).
  Aurora: AWS's MySQL/PostgreSQL-compatible DB. 5x MySQL performance.
  DynamoDB: Managed NoSQL. Single-digit ms latency. Serverless scaling.
  ElastiCache: Managed Redis or Memcached.
  Redshift: Data warehouse. Column-oriented. PB scale.
  Neptune: Graph database.

NETWORKING:
  VPC: Virtual Private Cloud. Your isolated network in AWS.
  Route 53: DNS. Health checks. Traffic routing policies.
  CloudFront: CDN. Global edge locations.
  ALB/NLB: Application/Network Load Balancers.
  Direct Connect: Dedicated connection from on-premise to AWS.
  VPN: Encrypted tunnel over internet.

MESSAGING:
  SQS: Managed message queue.
  SNS: Pub/Sub notifications. Fan-out.
  EventBridge: Event bus. Route events between services.
  Kinesis: Real-time data streaming (like Kafka).

SECURITY:
  IAM: Identity and Access Management.
  KMS: Key Management Service.
  Secrets Manager: Store secrets (DB passwords, API keys).
  WAF: Web Application Firewall.
  Shield: DDoS protection.
  GuardDuty: Threat detection.
  Inspector: Vulnerability scanning.
  Macie: PII detection in S3.
  CloudTrail: API audit log.
  Config: Resource configuration history.

OBSERVABILITY:
  CloudWatch: Metrics, logs, alarms, dashboards.
  X-Ray: Distributed tracing.
  CloudTrail: API call logging.

IDENTITY:
  IAM: Users, Groups, Roles, Policies.
  Cognito: User identity pools for apps.
  SSO: Single Sign-On.
  STS: Temporary security credentials.
```

---

## 64. Serverless Architecture

```
SERVERLESS:
  Run code without managing servers.
  Pay per execution, not per running instance.
  Auto-scales to zero.

AWS LAMBDA:
  Trigger → Lambda function runs → returns result.
  
  Triggers: API Gateway, S3 events, SQS, DynamoDB Streams,
            EventBridge, Kinesis, SNS, CloudWatch Events.
  
  Execution model:
    Cold start: ~100ms-1s (initialize runtime + code)
    Warm start: <10ms (reuse existing container)
  
  Limits:
    Max 15 minutes execution.
    Max 10GB memory.
    Max 512MB ephemeral disk.
    Max 1000 concurrent by default.

SERVERLESS PATTERNS:
  API: API Gateway → Lambda → DynamoDB
  Event processing: S3 upload → Lambda → process → store
  Scheduled job: EventBridge cron → Lambda

WHEN NOT TO USE SERVERLESS:
  Long-running tasks (> 15 min).
  High CPU/memory (cost inefficient).
  Cold start sensitive paths.
  Complex state management.
  Very high and constant throughput (dedicated servers cheaper).
```

---

## 65. Cloud-Native Design Patterns

```
12-FACTOR APP:
  1. Codebase:       One codebase, many deploys.
  2. Dependencies:   Explicitly declare and isolate.
  3. Config:         Store in environment variables.
  4. Backing services: Treat as attached resources.
  5. Build/Release/Run: Strict separation of stages.
  6. Processes:      Execute as stateless processes.
  7. Port binding:   Export services via port binding.
  8. Concurrency:    Scale out via the process model.
  9. Disposability:  Fast startup, graceful shutdown.
  10. Dev/Prod parity: Keep environments similar.
  11. Logs:          Treat as event streams.
  12. Admin processes: Run as one-off processes.

STATELESS vs STATEFUL:
  Stateless: Any instance can handle any request.
    Sessions in Redis/DB, not in-memory.
    Files in S3, not local disk.
    Enables horizontal scaling.
  
  Stateful: State tied to specific instance.
    Requires sticky sessions or external state.
    Harder to scale.

SIDECAR PATTERN:
  Deploy helper as secondary container alongside main app.
  Sidecar handles: logging, monitoring, proxying, config refresh.
  
  Pod:
    [Main Container] + [Sidecar: Envoy proxy]
    [Main Container] + [Sidecar: Log forwarder]

AMBASSADOR PATTERN:
  Proxy outbound connections for the main app.
  Main app → Ambassador → external service.
  Ambassador handles: retry, circuit break, connection pooling.

ADAPTER PATTERN:
  Transform app's output to standard format.
  [App with proprietary metrics] → [Adapter → Prometheus format]

ANTI-CORRUPTION LAYER:
  Isolate a new system from legacy systems.
  Translates between domain models.
```

---

# PART VIII — CLOUD & NETWORK SECURITY

---

## 66. Security Fundamentals

### CIA Triad

```
CONFIDENTIALITY: Only authorized parties access data.
  Encryption, access control, authentication.

INTEGRITY: Data is accurate and unmodified.
  Checksums, digital signatures, hashing.

AVAILABILITY: Systems accessible when needed.
  Redundancy, DDoS protection, backups.

NON-REPUDIATION: Cannot deny performing an action.
  Digital signatures, audit logs.
```

### Defense in Depth

```
LAYERED SECURITY:

  ┌────────────────────────────────────────────────┐
  │  Physical Security (datacenter, access control)│
  │  ┌──────────────────────────────────────────┐ │
  │  │  Network Perimeter (firewall, WAF, DDoS)  │ │
  │  │  ┌────────────────────────────────────┐  │ │
  │  │  │  Network Segmentation (VLAN, VPC)   │  │ │
  │  │  │  ┌──────────────────────────────┐  │  │ │
  │  │  │  │  Host Security (OS hardening)│  │  │ │
  │  │  │  │  ┌────────────────────────┐  │  │  │ │
  │  │  │  │  │  Application Security  │  │  │  │ │
  │  │  │  │  │  ┌──────────────────┐  │  │  │  │ │
  │  │  │  │  │  │  Data Security   │  │  │  │  │ │
  │  │  │  │  │  └──────────────────┘  │  │  │  │ │
  │  │  │  │  └────────────────────────┘  │  │  │ │
  │  │  │  └──────────────────────────────┘  │  │ │
  │  │  └────────────────────────────────────┘  │ │
  │  └──────────────────────────────────────────┘ │
  └────────────────────────────────────────────────┘
```

---

## 67. Cryptography Fundamentals

### Symmetric Encryption

```
Same key to encrypt and decrypt.

ALGORITHMS:
  AES-128/256: Most common. Block cipher.
    AES-GCM: Authenticated encryption (ensures integrity too).
  ChaCha20-Poly1305: Faster on CPU without AES hardware instructions.

MODES:
  ECB: Insecure. Same block → same ciphertext.
  CBC: XOR with previous ciphertext block. Needs IV.
  GCM: Galois/Counter Mode. Authenticated encryption. Best choice.
  CTR: Counter mode. Stream cipher from block cipher.

┌──────────────────────────────────────────────────────────┐
│  Plaintext ──► [AES + Key] ──► Ciphertext               │
│  Ciphertext ──► [AES + Same Key] ──► Plaintext          │
└──────────────────────────────────────────────────────────┘

PROBLEM: How to share the key securely? → Asymmetric encryption.
```

### Asymmetric Encryption

```
PUBLIC KEY: Share with anyone. Encrypt or verify.
PRIVATE KEY: Keep secret. Decrypt or sign.

RSA-2048/4096:
  Key generation: Two large primes p, q. n = p*q.
  Public key: (n, e). Private key: (n, d).
  Security: Based on integer factorization difficulty.
  Slow for large data → use to encrypt symmetric key only.

ECDSA / ECDH:
  Elliptic Curve variants. Smaller keys, same security.
  256-bit EC key ≈ 3072-bit RSA key.

X25519: Modern Diffie-Hellman key exchange.
Ed25519: Modern digital signatures.

USE:
  Encrypt small data (symmetric key): RSA/ECIES
  Sign data: RSA-PSS, ECDSA, Ed25519
  Key exchange: DH, ECDH, X25519
```

### Hashing

```
PROPERTIES of a cryptographic hash:
  Deterministic: Same input → always same output.
  Fast to compute.
  One-way: Cannot reverse hash to get input.
  Collision resistant: Hard to find two inputs with same hash.
  Avalanche effect: Small change → completely different hash.

ALGORITHMS:
  MD5: BROKEN. Never use for security.
  SHA-1: BROKEN for collision resistance. Avoid.
  SHA-256: Secure. 256-bit output.
  SHA-3 (Keccak): Different design. Also secure.
  BLAKE3: Very fast. Used in many modern tools.
  bcrypt/scrypt/Argon2: Password hashing. Intentionally slow. Use these!

PASSWORD HASHING:
  NEVER store plaintext passwords.
  NEVER use MD5/SHA for passwords (too fast → brute-forceable).
  
  Argon2id (recommended):
    Configurable memory cost + time cost.
    Resistant to GPU and ASIC attacks.
  
  bcrypt: Work factor. Default 12 rounds.
  
  // Rust (using argon2 crate)
  use argon2::{Argon2, PasswordHash, PasswordHasher, PasswordVerifier};
  let salt = SaltString::generate(&mut OsRng);
  let argon2 = Argon2::default();
  let hash = argon2.hash_password(password.as_bytes(), &salt)?;
```

### TLS (Transport Layer Security)

```
TLS provides: Confidentiality, Integrity, Authentication.

TLS 1.3 HANDSHAKE (simplified):
  
  Client                              Server
    │                                    │
    │──── ClientHello ──────────────────►│
    │    (supported ciphers, TLS version) │
    │    (key share for ECDH)             │
    │                                    │
    │◄─── ServerHello ──────────────────│
    │    (chosen cipher, key share)       │
    │◄─── Certificate ──────────────────│
    │    (server's cert, signed by CA)    │
    │◄─── CertificateVerify ────────────│
    │◄─── Finished ─────────────────────│
    │                                    │
    │ Both derive same session keys from ECDH exchange
    │                                    │
    │──── Finished ──────────────────►  │
    │                                    │
    │══════ Encrypted Application Data ═════════│

TLS 1.3 IMPROVEMENTS over 1.2:
  1-RTT (vs 2-RTT for TLS 1.2).
  0-RTT resumption (replayed data risk).
  Removed weak algorithms (RC4, SHA-1, RSA key exchange, DH <2048).
  Forward secrecy mandatory (ephemeral key exchange).

CERTIFICATE CHAIN:
  Website Cert → signed by Intermediate CA → signed by Root CA
  Browser trusts Root CA → chain validates.
  
  Root CAs: DigiCert, Let's Encrypt, Comodo, GlobalSign.
  Let's Encrypt: Free, automated (ACME protocol). 90-day certs.

MTLS (Mutual TLS):
  Both sides present certificates.
  Server verifies client cert.
  Client verifies server cert.
  Used in service mesh, API security, zero-trust networks.
```

---

## 68. Identity and Access Management

### Authentication vs Authorization

```
AUTHENTICATION (AuthN): Who are you?
  Prove identity. Username+password, certificate, biometric.

AUTHORIZATION (AuthZ): What can you do?
  What resources can this identity access?

AUTHENTICATION FACTORS:
  Something you know: Password, PIN, security question.
  Something you have: Hardware key (YubiKey), TOTP (Google Auth), SMS OTP.
  Something you are: Fingerprint, face recognition.
  
  MFA: Two or more factors. Highly recommended.
```

### OAuth 2.0

```
OAuth 2.0: Authorization framework. Lets apps access resources on behalf of users without knowing their password.

ROLES:
  Resource Owner: User who owns the data.
  Client: Application requesting access (your app).
  Authorization Server: Issues tokens (Google, GitHub, Okta).
  Resource Server: API that holds the data.

AUTHORIZATION CODE FLOW:
  User clicks "Login with Google"
  │
  Client ──► Auth Server: "Auth request" + client_id + redirect_uri + scope
  │
  Auth Server: Show login page → user authenticates + consents
  │
  Auth Server ──► Client: Redirect with authorization code
  │
  Client ──► Auth Server: Exchange code for tokens (client_secret included)
  │
  Auth Server ──► Client: Access token + Refresh token
  │
  Client ──► Resource Server: API request with access token
  │
  Resource Server: Validate token → return data

ACCESS TOKEN: Short-lived (15 min). Use for API calls.
REFRESH TOKEN: Long-lived. Exchange for new access token.

PKCE (Proof Key for Code Exchange):
  Additional security for public clients (mobile apps, SPAs).
  Code verifier (random) → SHA256 → code challenge.
  Prevents authorization code interception attacks.
```

### JWT (JSON Web Token)

```
JWT STRUCTURE:
  Header.Payload.Signature

Header (base64url encoded):
  {"alg": "RS256", "typ": "JWT"}

Payload (base64url encoded):
  {
    "sub": "user-123",          (subject)
    "iss": "https://auth.example.com", (issuer)
    "aud": "my-api",            (audience)
    "exp": 1735689600,          (expiration timestamp)
    "iat": 1735686000,          (issued at)
    "roles": ["admin", "user"]  (custom claims)
  }

Signature:
  RS256: RSA_Sign(private_key, base64(header) + "." + base64(payload))
  HS256: HMAC_SHA256(secret, base64(header) + "." + base64(payload))

VALIDATION:
  1. Decode header, get algorithm.
  2. Verify signature with public key / secret.
  3. Check exp (expiration).
  4. Check iss (issuer).
  5. Check aud (audience).
  6. Check custom claims.

DANGERS:
  "alg": "none" attack → never trust alg header blindly.
  HS256 secret leak → all tokens forgeable.
  Not encrypted by default (base64, not ciphertext) → don't put secrets in claims.
  Can't invalidate before expiration (use short TTL + refresh tokens).
```

### RBAC and ABAC

```
RBAC (Role-Based Access Control):
  Permissions assigned to roles. Roles assigned to users.
  
  User → Roles → Permissions
  Alice → [admin] → [read, write, delete]
  Bob   → [viewer] → [read]
  
  Simple. Easy to audit. Doesn't scale well (role explosion).

ABAC (Attribute-Based Access Control):
  Policies based on attributes of subject, resource, environment.
  
  Rule: ALLOW if user.department == resource.department AND time == business_hours
  
  Very flexible. Complex to manage.

REBAC (Relationship-Based Access Control):
  Google's Zanzibar model (used in Google Drive).
  "Can user X access document Y given relationship graph?"
  
  Implemented by: Google Zanzibar, SpiceDB, Ory Keto, Permify.
```

---

## 69. Network Security

### Firewalls

```
TYPES:
  Packet filter (L3/L4):
    Stateless: Rules on IP, port, protocol.
    Stateful: Tracks connections. Allows return traffic.

  Application firewall (L7):
    Understands HTTP, DNS, TLS.
    Can filter by domain, URL, content type.

  WAF (Web Application Firewall):
    OWASP Top 10 protection.
    SQL injection, XSS, CSRF detection.
    AWS WAF, Cloudflare, ModSecurity.

IPTABLES (Linux):
  Tables: filter, nat, mangle, raw, security.
  Chains: INPUT, OUTPUT, FORWARD, PREROUTING, POSTROUTING.
  
  # Block all incoming except established + port 22 + 80 + 443
  iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
  iptables -A INPUT -p tcp --dport 22 -j ACCEPT
  iptables -A INPUT -p tcp --dport 80 -j ACCEPT
  iptables -A INPUT -p tcp --dport 443 -j ACCEPT
  iptables -A INPUT -j DROP

NFTABLES: Replacement for iptables. More efficient, flexible.
```

### VPN and Zero Trust

```
VPN (Virtual Private Network):
  Encrypted tunnel over public internet.
  Traditional model: Once inside VPN → trust everything.
  
  Protocols:
    OpenVPN: TLS-based. Mature.
    WireGuard: Modern, simple, very fast. Uses ChaCha20 + Curve25519.
    IPsec: Complex but widely supported.

ZERO TRUST NETWORK ACCESS (ZTNA):
  Principle: Never trust, always verify.
  Even inside the network → verify identity + device + context.
  
  vs Traditional VPN:
    VPN: Connect → inside = trusted.
    ZTNA: Every request → verified. No implicit trust.
  
  Pillars:
    Verify explicitly (always authenticate + authorize).
    Least privilege access.
    Assume breach (minimize blast radius, end-to-end encryption).
  
  Implementations:
    Google BeyondCorp (reference implementation).
    Cloudflare Access.
    Zscaler, Okta, Tailscale.

WIREGUARD CONCEPTS:
  Peer-to-peer. Each peer has public/private key pair.
  Cryptokey routing: IP ranges → public key mapping.
  No handshake overhead after setup.
  Very small codebase (~4000 lines) → easier to audit.
```

### DDoS Protection

```
TYPES OF DDOS ATTACKS:
  Volumetric: Flood bandwidth (UDP flood, amplification attacks).
  Protocol: Exploit protocol weaknesses (SYN flood, Ping of Death).
  Application Layer: HTTP flood, Slowloris.

SYN FLOOD:
  Send thousands of SYN packets with spoofed source IPs.
  Server allocates half-open connections → exhausted.
  
  Mitigation: SYN cookies.
    Instead of allocating state, encode state in SYN-ACK sequence number.
    Only create entry when ACK received.

AMPLIFICATION ATTACKS:
  Send small request to open server (DNS, NTP, memcached) with spoofed source IP.
  Server sends large response to victim.
  DNS: 1 byte request → 100 byte response (100x amplification).
  NTP monlist: 8 bytes → 3KB response (375x amplification).

MITIGATION:
  Scrubbing centers: Route traffic through cleaning service.
  Anycast diffusion: Spread attack across many PoPs.
  Rate limiting: IP-based, geo-based.
  CDN / DDoS protection: Cloudflare, AWS Shield, Akamai.
  BCP38: ISPs filter spoofed source IPs at edge (ingress filtering).
```

### Intrusion Detection/Prevention

```
IDS (Intrusion Detection System): Detect and ALERT.
IPS (Intrusion Prevention System): Detect and BLOCK.

TYPES:
  Network-based (NIDS): Monitor network traffic (Snort, Suricata).
  Host-based (HIDS): Monitor OS events, file changes (OSSEC, Wazuh).

DETECTION METHODS:
  Signature-based: Match known attack patterns. Fast but misses novel.
  Anomaly-based: Learn baseline, flag deviations. More false positives.
  Behavioral: Track process behavior (Falco, CrowdStrike).

FALCO (Cloud-Native Runtime Security):
  Uses eBPF + syscall monitoring.
  Rules engine for container behavior.
  Alert on: container spawning shell, reading /etc/shadow, etc.
```

---

## 70. Secrets Management

```
NEVER:
  Commit secrets to git (even "private" repos).
  Store in environment variables in plaintext (logged).
  Hard-code in source code.

PROPER SECRETS MANAGEMENT:

HASHICORP VAULT:
  Dynamic secrets (generated on demand, expire).
  Encryption as a service.
  PKI certificate management.
  Secret engines: KV, AWS, Database, PKI, Transit.
  
  Application ──► Vault API (authenticated) ──► Secret
  Vault ──► Audit log every access.

AWS SECRETS MANAGER:
  Store secrets, rotate automatically.
  Integrated with IAM.
  SDKs fetch at runtime.
  
  // Rust
  let client = secretsmanager::Client::new(&config);
  let secret = client.get_secret_value().secret_id("myapp/db/password").send().await?;

KUBERNETES SECRETS:
  base64 encoded (NOT encrypted by default!).
  Enable encryption at rest (EncryptionConfiguration).
  Or use external-secrets operator + Vault/AWS Secrets Manager.

SECRET ROTATION:
  Rotate credentials regularly.
  Zero-downtime rotation: new cred works before old disabled.
  AWS RDS: automatic 90-day rotation.
```

---

## 71. Cloud Security Architecture

### Shared Responsibility Model

```
AWS SHARED RESPONSIBILITY:

  CUSTOMER RESPONSIBILITY:                AWS RESPONSIBILITY:
  ┌──────────────────────────────┐        ┌──────────────────────────┐
  │  Customer Data               │        │                          │
  │  Platform, Applications      │        │  Regions                 │
  │  Identity & Access Mgmt      │        │  Availability Zones      │
  │  Operating System            │        │  Edge Locations          │
  │  Network & Firewall config   │        │                          │
  │  Client-side data encryption │        │  Compute infrastructure  │
  │  Server-side encryption      │        │  Storage infrastructure  │
  │  Network traffic protection  │        │  Database infrastructure │
  └──────────────────────────────┘        │  Networking hardware     │
                                          └──────────────────────────┘

"Security IN the cloud" vs "Security OF the cloud"
```

### AWS Security Best Practices

```
IAM BEST PRACTICES:
  Root account: Enable MFA. Never use for daily work.
  Create individual IAM users. Never share credentials.
  Principle of least privilege.
  Rotate access keys regularly.
  Use IAM roles for EC2/Lambda (not access keys in code).
  Use AWS Organizations SCPs for guardrails.

NETWORK SECURITY:
  VPC with private subnets for sensitive resources.
  Internet Gateway only for public-facing resources.
  NAT Gateway for outbound internet from private subnets.
  Security Groups (stateful, instance-level).
  NACLs (stateless, subnet-level, for broad rules).
  VPC Flow Logs for network monitoring.

ENCRYPTION:
  S3: Server-Side Encryption (SSE-S3, SSE-KMS, SSE-C).
  EBS: Encrypt all volumes at creation.
  RDS: Encrypt at rest + in transit (require SSL).
  KMS: Manage encryption keys. Audit key usage.
  
LOGGING AND MONITORING:
  CloudTrail: All API calls.
  CloudWatch: Metrics + logs + alarms.
  GuardDuty: ML-based threat detection.
  Config: Resource configuration compliance.
  Security Hub: Centralized security findings.

CONTAINER SECURITY (ECR + EKS):
  Scan images for CVEs (ECR scanning, Trivy, Grype).
  Use distroless/minimal base images.
  Non-root containers.
  Read-only root filesystem.
  Pod Security Standards (Restricted policy).
  Network policies.
  IRSA (IAM Roles for Service Accounts) — no access keys in pods.
  Secrets from AWS Secrets Manager (not k8s secrets).
```

### OWASP Top 10

```
2021 OWASP TOP 10:

1. Broken Access Control
   Users access resources they shouldn't.
   Fix: Enforce authZ server-side. Deny by default.

2. Cryptographic Failures
   Sensitive data exposed (no encryption, weak algorithms).
   Fix: TLS everywhere. AES-GCM. Argon2 for passwords.

3. Injection (SQL, NoSQL, OS, LDAP)
   Untrusted data sent to interpreter.
   Fix: Parameterized queries. Input validation. ORM.

4. Insecure Design
   Missing security controls by design.
   Fix: Threat modeling. Secure by default.

5. Security Misconfiguration
   Default creds, open cloud storage, error messages with stack traces.
   Fix: Hardening. Least privilege. Remove defaults.

6. Vulnerable/Outdated Components
   Using libraries with known CVEs.
   Fix: Dependency scanning. Regular updates.

7. ID & Authentication Failures
   Weak passwords, no MFA, session fixation.
   Fix: MFA. Secure session management. Rate limit logins.

8. Software & Data Integrity Failures
   CI/CD pipeline poisoning. Deserialization.
   Fix: Sign artifacts. Verify checksums. SBOM.

9. Security Logging & Monitoring Failures
   Attacks not detected.
   Fix: Log auth events. Alert on anomalies. SIEM.

10. SSRF (Server-Side Request Forgery)
    Server fetches URLs from user input → internal resource access.
    Fix: Allowlist URLs. Block internal IPs. No redirects.
```

---

## 72. Supply Chain Security

```
SUPPLY CHAIN ATTACK:
  Compromise a dependency/tool → affects all users.
  Example: SolarWinds, XZ Utils backdoor, npm package typosquatting.

MITIGATIONS:
  SBOM (Software Bill of Materials):
    Machine-readable list of all components.
    Formats: SPDX, CycloneDX.
    Know what you're running.

  SIGSTORE:
    Sign and verify software artifacts.
    Cosign: Sign container images.
    Keyless signing using OIDC identity.
    
    cosign sign --key cosign.key myimage:tag
    cosign verify --key cosign.pub myimage:tag

  SLSA (Supply-chain Levels for Software Artifacts):
    Framework for supply chain security.
    Level 1-4: Increasing assurance.
    Provenance: Prove where software came from.

  Pin dependencies:
    Don't use floating versions (latest).
    Pin exact versions + verify checksums.
    Cargo.lock, go.sum, package-lock.json.

  Minimal images:
    Fewer packages = fewer vulnerabilities.
    Distroless, Alpine, scratch-based images.

  Trivy / Grype / Snyk:
    Scan images and code for CVEs.
```

---

# PART IX — OBSERVABILITY & RELIABILITY

---

## 73. The Three Pillars of Observability

```
OBSERVABILITY: Can you understand the internal state of a system from its external outputs?

THREE PILLARS:
  METRICS: Numeric measurements over time.
  LOGS:    Discrete events with context.
  TRACES:  The path of a request through the system.

┌────────────────────────────────────────────────────────────────────┐
│  Pillar  │ What             │ Tools                               │
├──────────┼──────────────────┼─────────────────────────────────────┤
│  Metrics │ CPU 45%, RPS 1k  │ Prometheus, InfluxDB, DataDog      │
│  Logs    │ ERROR: user 404  │ ELK Stack, Loki, Splunk            │
│  Traces  │ req → A → B → C │ Jaeger, Zipkin, Tempo, X-Ray       │
└────────────────────────────────────────────────────────────────────┘

Fourth pillar (emerging): PROFILING (continuous CPU/memory profiling).
  Tools: Parca, Pyroscope, Polar Signals.
```

### Prometheus

```
PROMETHEUS:
  Pull-based metrics system.
  Scrapes /metrics endpoint from targets.
  TSDB (Time Series Database) for storage.
  PromQL: Powerful query language.

METRIC TYPES:
  Counter: Monotonically increasing (requests total, errors total).
  Gauge: Can go up/down (CPU usage, queue size, memory).
  Histogram: Distribution of values in buckets (request duration).
  Summary: Similar to histogram, but quantile calculated client-side.

METRIC NAMING CONVENTION:
  <namespace>_<subsystem>_<metric>_<unit>
  http_server_requests_duration_seconds

PROMQL EXAMPLES:
  rate(http_requests_total[5m])                    // per-second rate
  histogram_quantile(0.99, rate(http_duration_bucket[5m])) // p99 latency
  sum by(service) (rate(errors_total[5m]))         // error rate by service

ALERTMANAGER:
  Routes alerts to receivers (Slack, PagerDuty, email).
  Grouping: Reduce noise.
  Inhibition: Suppress child alerts when parent fires.
  Silencing: Temporary mute.
```

### Distributed Tracing

```
CONCEPTS:
  Trace: End-to-end journey of a request.
  Span: Single operation within a trace.
    Span has: trace_id, span_id, parent_span_id, operation_name, timestamps, tags.
  Context propagation: Pass trace context between services.
    HTTP headers: traceparent (W3C standard), X-B3-TraceId (Zipkin), X-Request-ID.

TRACE VISUALIZATION:
  
  Request ──────────────────────────────────────────────────► 100ms
  
  [Span A: API Gateway        ──────────────────────────────]  100ms
    [Span B: UserService    ──────────────────          ]  60ms
      [Span C: DB Query   ──────────────    ]  40ms
    [Span D: OrderService                     ──────   ]  20ms

OPENTELEMETRY (OTel):
  Vendor-neutral standard for observability instrumentation.
  SDKs for all languages (Rust, Go, Java, Python...).
  Collects: traces + metrics + logs.
  Exports to: Jaeger, Zipkin, Grafana Tempo, Datadog, etc.

SAMPLING:
  Trace everything = too much data.
  Head-based sampling: decide at start (e.g., 1% of requests).
  Tail-based sampling: decide at end (always trace errors and slow requests).
```

### Logging Best Practices

```
STRUCTURED LOGGING:
  Log as JSON, not free text.
  
  BAD:  "User 123 logged in from 192.168.1.1"
  GOOD: {"level":"info", "event":"user.login", "user_id":123, "ip":"192.168.1.1", "timestamp":"..."}

LOG LEVELS (in order):
  TRACE → DEBUG → INFO → WARN → ERROR → FATAL

ELK STACK:
  Elasticsearch: Store and search logs.
  Logstash: Collect, transform, route logs.
  Kibana: Visualize and explore.
  
  Beats (Filebeat, Metricbeat): Lightweight shippers.

LOKI (Grafana):
  Logs like Prometheus (label-based).
  Doesn't index log content (cheaper).
  Queries by labels.

LOG AGGREGATION FLOW:
  App → stdout/stderr
      → Container log driver → Fluentd/Filebeat
      → Log aggregator (Loki/Elasticsearch)
      → Visualization (Grafana/Kibana)
```

---

## 74. SRE Practices

### Error Budgets

```
ERROR BUDGET = 100% - SLO

If SLO = 99.9% → Error budget = 0.1% = 43.8 min/month.

If error budget is USED UP:
  → Feature development slows/stops.
  → Focus on reliability.
  → Conduct blameless postmortem.

If error budget is HEALTHY:
  → Ship more features.
  → Take more risks.
  → Run chaos experiments.

SLI → SLO → SLA:
  SLI: Actual metric (request success rate = 99.97%)
  SLO: Internal target (>99.9% success rate)
  SLA: External contract (>99.5% or we give credits)
```

### Postmortems

```
BLAMELESS POSTMORTEM:
  Focus on systems, not people.
  Goal: Find root causes, improve system.
  
  SECTIONS:
  1. Summary (what happened, impact, duration)
  2. Timeline (minute-by-minute)
  3. Root Cause Analysis (5 Whys)
  4. Contributing Factors
  5. Action Items (with owners, due dates)

FIVE WHYS EXAMPLE:
  Problem: Website was down 30 minutes.
  Why 1: Database ran out of connections.
  Why 2: Connection pool was too small.
  Why 3: Recent traffic increase wasn't anticipated.
  Why 4: No capacity planning process exists.
  Why 5: Engineering focused on features, not ops.
  
  Root cause: No capacity planning process.
  Fix: Implement capacity planning review.
```

### Chaos Engineering

```
CHAOS ENGINEERING:
  Intentionally inject failures to test resilience.
  "Break things on purpose before they break by accident."

PRINCIPLES (Netflix):
  1. Build a hypothesis around steady state behavior.
  2. Vary real-world events.
  3. Run experiments in production (or staging).
  4. Automate experiments to run continuously.
  5. Minimize blast radius.

TYPES OF EXPERIMENTS:
  Kill random pods (kube-monkey, chaos-monkey).
  Network partition (tc netem).
  CPU/memory pressure.
  Disk I/O saturation.
  DNS failures.
  Dependency latency injection.

TOOLS:
  Chaos Monkey (Netflix): Randomly kills VMs.
  Chaos Mesh (K8s): Comprehensive chaos for Kubernetes.
  Litmus: Kubernetes chaos engineering.
  Gremlin: Commercial, controlled chaos.

CHAOS EXPERIMENT FLOW:
  Define steady state metric (RPS, error rate).
  ──► Inject failure.
  ──► Observe: did system recover automatically?
  ──► If not: system has resilience gap.
  ──► Fix gap.
  ──► Run again.
```

---

## 75. Disaster Recovery

```
RTO (Recovery Time Objective):
  Maximum acceptable downtime after a disaster.
  "We must be back in 4 hours."

RPO (Recovery Point Objective):
  Maximum acceptable data loss.
  "We can afford to lose at most 1 hour of data."

STRATEGIES (increasing cost and decreasing RTO/RPO):

BACKUP & RESTORE:
  Regular backups to S3/Glacier.
  RTO: Hours. RPO: Hours to days.
  Cheapest.

PILOT LIGHT:
  Minimal version of environment always running.
  Data replicated continuously.
  Scale up on disaster.
  RTO: Minutes to hours. RPO: Minutes.

WARM STANDBY:
  Scaled-down but fully functional system always running.
  Promote and scale on disaster.
  RTO: Minutes. RPO: Seconds to minutes.

ACTIVE-ACTIVE (MULTI-SITE):
  Full production in multiple regions simultaneously.
  Traffic split across regions.
  RTO: Near zero. RPO: Near zero.
  Most expensive.

BACKUP STRATEGY:
  3-2-1 Rule:
    3 copies of data.
    2 different media types.
    1 offsite copy.
  
  Test restores regularly! Untested backups are not backups.
```

---

# PART X — ARCHITECTURE PATTERNS

---

## 76. Microservices Architecture

```
MICROSERVICES:
  Application composed of small, independent services.
  Each service: single responsibility, independent deployment, own data.

MONOLITH vs MICROSERVICES:
┌───────────────────────────────────────────────────────────────────┐
│  Aspect         │ Monolith               │ Microservices          │
├─────────────────┼────────────────────────┼────────────────────────┤
│  Deployment     │ All-or-nothing         │ Independent            │
│  Scaling        │ Scale whole app        │ Scale individual svc   │
│  Failure        │ One bug kills all      │ Isolated failures      │
│  Team           │ One team/codebase      │ Multiple teams         │
│  Latency        │ In-process calls       │ Network calls          │
│  Complexity     │ Code complexity        │ Operational complexity │
│  Data           │ Shared DB (simpler)    │ DB per service (harder)│
│  Start with     │ Better early on        │ After you understand   │
└───────────────────────────────────────────────────────────────────┘

MICROSERVICES CHALLENGES:
  Distributed transactions (use Saga pattern).
  Network failures (retry, circuit breaker).
  Service discovery.
  Distributed tracing.
  Data consistency.
  API versioning.

WHEN TO SPLIT (Strangler Fig Pattern):
  Start as monolith.
  Identify bounded contexts (DDD).
  Extract services gradually.
  Don't distribute prematurely.
```

### Domain-Driven Design (DDD)

```
BOUNDED CONTEXT:
  A specific boundary within which a domain model is defined.
  "User" means different things in Billing vs Shipping.
  
  Bounded Context = autonomous microservice boundary.

UBIQUITOUS LANGUAGE:
  Shared vocabulary between devs and domain experts.
  Code uses same terms as business.

AGGREGATES:
  Cluster of domain objects treated as one unit.
  Each aggregate has a root entity.
  Modifications only through root.
  
  Order Aggregate: Order → [OrderItem, ShippingAddress]
  User Aggregate: User → [UserProfile, Preferences]

DOMAIN EVENTS:
  OrderPlaced, PaymentProcessed, ItemShipped.
  Events trigger reactions in other bounded contexts.
  Loose coupling between contexts.
```

---

## 77. Data Architecture

### Data Lake vs Data Warehouse vs Lakehouse

```
DATA WAREHOUSE:
  Structured, processed data.
  Schema-on-write (must define structure before loading).
  SQL-friendly. Fast queries on structured data.
  Examples: Redshift, Snowflake, BigQuery.

DATA LAKE:
  Raw, unprocessed data (all formats: JSON, CSV, Parquet, images).
  Schema-on-read (structure applied when reading).
  Cheap storage (S3, HDFS).
  Risk: becomes "data swamp" without governance.

DATA LAKEHOUSE:
  Combines lake (cheap storage) + warehouse (ACID, SQL performance).
  Open table formats: Delta Lake, Apache Iceberg, Apache Hudi.
  Time travel, ACID transactions on object storage.
  Examples: Databricks, AWS Lake Formation.

OLTP vs OLAP:
  OLTP: Online Transaction Processing.
    Many small reads/writes. Row-oriented. Application databases.
    PostgreSQL, MySQL, DynamoDB.
    
  OLAP: Online Analytical Processing.
    Few large reads, complex aggregations. Column-oriented.
    Redshift, BigQuery, ClickHouse, DuckDB.
    
COLUMN vs ROW STORAGE:
  Row: Store all columns of a row together.
    Fast for full row access (OLTP: SELECT * WHERE id=1).
  
  Column: Store each column separately.
    Fast for aggregations (OLAP: SELECT AVG(price) FROM orders).
    Better compression (same-type data compresses well).
```

### Lambda Architecture vs Kappa Architecture

```
LAMBDA ARCHITECTURE (Nathan Marz):
  Batch layer: Processes all historical data. Accurate.
  Speed layer: Processes real-time data. Approximate.
  Serving layer: Merges batch + speed views.
  
  Raw Data ──► Batch Layer (Spark) ──► Batch Views ──┐
           └──► Speed Layer (Flink) ──► RT Views ────┼──► Serving
                                                     │
  Problem: Two code paths, complex, maintenance burden.

KAPPA ARCHITECTURE (Jay Kreps):
  Single streaming layer. No batch.
  Reprocessing: Replay event log (Kafka) from beginning.
  
  Raw Data ──► Stream Processing (Flink/Kafka Streams) ──► Views
  
  Simpler. Works when streaming can produce same results as batch.

MODERN: Lambda mostly replaced by Lakehouse + streaming.
```

---

## 78. System Design Case Studies

### URL Shortener (like bit.ly)

```
REQUIREMENTS:
  Shorten URLs. Redirect. 1B URLs. 1000 RPS read, 10 RPS write.

KEY DESIGN DECISIONS:

1. Short URL generation:
   Option A: hash(long_url) → take 7 chars. Risk: collision.
   Option B: Auto-increment ID → Base62 encode.
     ID 12345 → base62 → "dnh"
     Base62 = [0-9][a-z][A-Z] = 62 chars.
     7 chars = 62^7 ≈ 3.5 trillion unique URLs.

2. Storage:
   Simple KV store: short_code → long_url
   DynamoDB or Redis.

3. Redirect:
   301 Permanent: Browser caches, no future requests → less server load.
   302 Temporary: Always hits server → better for analytics.

4. Scale:
   Cache hot URLs in Redis.
   Read replicas for URL lookups.

FLOW:
  POST /shorten → app generates short_code → store (short_code, long_url)
  GET /<code> → lookup in cache → if miss → DB → 301 redirect
```

### Design Twitter Feed

```
APPROACHES:

PULL MODEL (Fan-out on read):
  When user loads feed → query tweets from all followees → merge → return.
  Simple. Slow for users following many accounts.
  SELECT tweets WHERE author IN (followee_list) ORDER BY time DESC LIMIT 20.

PUSH MODEL (Fan-out on write):
  When user tweets → write to all followers' feed tables.
  Fast reads. Slow writes. Problems: celebrities with 100M followers.

HYBRID:
  Regular users: push model.
  Celebrities (high follower count): pull model.
  
CELEBRITY PROBLEM:
  Push: 100M followers × 1 tweet = 100M writes. Too slow.
  Solution: Hybrid. Cache celebrity tweets separately.
  On load: fetch user's cached feed + celebrity tweets → merge → display.

TIMELINE STORAGE:
  Redis sorted set: {tweet_id: timestamp} per user.
  Fast reads, push on write.
  
DATA MODEL:
  Tweet: (tweet_id, user_id, content, timestamp)
  User: (user_id, username, follower_count)
  Follow: (follower_id, followee_id)
  Feed: (user_id, tweet_id, timestamp) — materialized per user
```

### Design Rate Limiter

```
DISTRIBUTED RATE LIMITER:

REQUIREMENTS:
  100 req/min per API key.
  Works across multiple servers.
  Low latency.

REDIS-BASED TOKEN BUCKET:

In Go:
  func checkRateLimit(ctx context.Context, rdb *redis.Client, key string) (bool, error) {
      pipe := rdb.Pipeline()
      now := time.Now().UnixMilli()
      window := int64(60000) // 1 minute in ms
      limit := int64(100)
      
      // Sliding window log implementation
      pipe.ZRemRangeByScore(ctx, key, "0", strconv.FormatInt(now-window, 10))
      pipe.ZCard(ctx, key)
      pipe.ZAdd(ctx, key, redis.Z{Score: float64(now), Member: now})
      pipe.Expire(ctx, key, time.Minute)
      
      results, err := pipe.Exec(ctx)
      if err != nil { return false, err }
      
      count := results[1].(*redis.IntCmd).Val()
      return count < limit, nil
  }

REDIS CELL (Redis module for rate limiting):
  CL.THROTTLE user:123 15 30 60 1
  (max_burst=15, rate=30 per 60 seconds, cost=1)
  Returns: [allowed, limit, remaining, retry-after, reset-after]
```

---

## 79. Consensus in Practice: etcd and ZooKeeper

```
ETCD:
  Distributed key-value store using Raft.
  Kubernetes uses etcd for all cluster state.
  
  Features:
    Watch: Subscribe to key changes.
    Leases: TTL on keys (used for leader election, service registration).
    Transactions: CAS (Compare-and-Swap).
    Multi-version concurrency control (MVCC).
  
  Leader election using etcd:
    All nodes try to create lease key.
    First to succeed = leader.
    Lease expires → others compete again.

ZOOKEEPER:
  Older, uses ZAB (ZooKeeper Atomic Broadcast) — similar to Paxos.
  Used by: Kafka (older versions), HBase, Hadoop.
  
  Concepts:
    ZNode: Like a file + directory.
    Ephemeral ZNode: Deleted when client disconnects. (Leader election)
    Watchers: Notify on change.
  
  Leader election with ZooKeeper:
    Each node creates ephemeral sequential znode: /leader/node-0000001.
    Node with lowest number = leader.
    Others watch the next lower node.
    If leader crashes → its znode deleted → next node becomes leader.
```

---

## 80. Final Architecture: Mental Models for Top 1%

```
THE 10 MENTAL MODELS OF GREAT ARCHITECTS:

1. TRADE-OFF THINKING:
   There is no best solution. Only trade-offs.
   Always ask: "What do we give up to get this?"

2. SINGLE RESPONSIBILITY AT EVERY LEVEL:
   Functions, classes, services, systems — each has one reason to change.

3. MAKE IT WORK → MAKE IT RIGHT → MAKE IT FAST:
   Don't optimize prematurely. Profile before optimizing.

4. DATA LOCALITY:
   Computation near data = less latency.
   This drives: caching, CDN, read replicas, sharding strategy.

5. DESIGN FOR FAILURE:
   Every component WILL fail. Design for it.
   Retry with backoff. Circuit break. Bulkhead. Fallback.

6. IMMUTABILITY:
   Immutable data = no concurrency bugs.
   Event sourcing. Append-only logs. Functional programming.

7. BACK-OF-ENVELOPE ESTIMATION:
   Can this design handle 1M RPS?
   How much storage do we need in 5 years?
   Calculate before building.

8. OBSERVE BEFORE OPTIMIZING:
   You can't optimize what you can't measure.
   Build observability first.

9. OPERATIONS ARE DESIGN:
   How do you deploy? Roll back? Debug? Scale? Backup?
   These are design decisions, not afterthoughts.

10. SIMPLE IS SCALABLE:
    Complexity is the enemy of reliability.
    Add complexity only when you HAVE the problem, not anticipating it.

BACK-OF-ENVELOPE TEMPLATE:
  Users: 10M daily active users.
  Write RPS: 10M / 86,400 sec ≈ 115 writes/sec.
  Read RPS: 10x writes ≈ 1,150 reads/sec.
  Data: 1KB per record × 115 writes/sec × 86,400 × 365 = ~3.6TB/year.
  Bandwidth: 1150 reads × 1KB = 1.15 MB/s (trivial).
```

---

## APPENDIX: Quick Reference Commands

```
LINUX PERFORMANCE QUICK REFERENCE:

# CPU
top -d 1           # real-time process view
mpstat -P ALL 1    # per-core CPU stats
perf stat ls       # hardware counter stats

# Memory  
free -h             # memory overview
cat /proc/meminfo   # detailed stats
vmstat -s           # virtual memory stats

# Disk I/O
iostat -x 1         # disk stats per second
iotop               # per-process I/O
df -h               # disk space

# Network
ss -tunapl          # all connections
iftop               # bandwidth per connection
tcpdump -i eth0 port 80   # capture HTTP
curl -w "@curl-format.txt" -o /dev/null -s https://example.com  # HTTP timing

# Kubernetes
kubectl top nodes
kubectl top pods
kubectl get events --sort-by='.lastTimestamp'
kubectl describe pod <pod>
kubectl exec -it <pod> -- /bin/sh
kubectl port-forward svc/<svc> 8080:80

# Docker
docker stats
docker inspect <container>
docker exec -it <container> sh
docker system prune -af

# Files and Processes
lsof -p <pid>       # files open by process
strace -p <pid>     # trace syscalls of running process
pmap <pid>          # memory map
```

---

> **Final words from your mentor:**
>
> You've seen the map. The top 1% don't know more concepts — they understand the **why** behind each concept, the trade-offs, and when to apply what. Every system you encounter is a combination of the patterns here. Your job is to see the pattern behind the complexity.
>
> Study. Build. Break. Observe. That is the path.

---
*Document version: 2025 Edition | Coverage: ~150 concepts*

I'll research the latest topics and build you a world-class comprehensive guide.Now I have all the research I need. Let me build this comprehensive guide as a `.md` file.Your complete guide is ready — **4,999 lines of deep, structured knowledge**. Here's what's covered across **20 major sections**:

---

**System Design Core**
- Functional vs non-functional requirements, estimation templates, CAP/PACELC theorems, consistency models (linearizability → eventual), BASE vs ACID, 12-Factor methodology

**Scalability & Performance**
- Vertical/horizontal scaling, Amdahl's Law, Little's Law, sharding strategies (range, hash, consistent hashing with visual ring diagrams), replication topologies (leader/leaderless/multi-leader)

**Networking**
- OSI model with system design relevance, TCP/UDP/QUIC deep dive, DNS resolution flow, HTTP/1.1 vs HTTP/2 vs HTTP/3, TCP congestion control algorithms (BBR, CUBIC), epoll, io_uring, socket lifecycle

**Distributed Systems**
- 8 fallacies of distributed computing, Two Generals / Byzantine Generals problems, all failure modes, Lamport timestamps, vector clocks, 2PC, Saga patterns, Outbox pattern

**Consensus**
- Paxos phases, Raft (election + log replication with ASCII flow diagrams), ZooKeeper primitives, Gossip/SWIM protocols, consistent hashing deep dive

**Storage & Databases**
- B-Tree, B+ Tree, LSM-Tree internals, SQL isolation levels, all NoSQL types (KV, Document, Column, Graph, Time-Series, Search, Vector), indexing deep dive, OLTP/OLAP/HTAP

**Linux Kernel (Comprehensive)**
- Process/thread lifecycle, CFS scheduler with vruntime/RB-tree, memory management (buddy allocator, SLAB, OOM killer, NUMA, huge pages, page faults, VMA), VFS architecture, networking stack (sk_buff, XDP, netfilter hooks), **eBPF** (hooks, maps, verifier, tools — bpftrace, Cilium, Falco, Tetragon), IPC mechanisms, kernel synchronization (spinlock, mutex, RCU, atomic ops, memory barriers)

**Cloud Native**
- Kubernetes architecture (every component), scheduling controls, service mesh (Istio, Linkerd, Envoy xDS, Ambient Mesh), GitOps (ArgoCD/Flux), Serverless/KEDA, service discovery

**Security (Deep)**
- Cryptography (AES-GCM, ECDHE, TLS 1.3 handshake, PFS, mTLS, PKI), OAuth2/OIDC/JWT pitfalls, RBAC/ABAC/OPA, Kubernetes security hardening (securityContext, admission controllers, Kyverno/Gatekeeper), Supply chain (Sigstore, SLSA, Trivy/Grype), cloud security (shared responsibility, CSPM, CWPP), OWASP Top 10, DDoS protection, network segmentation

**Real-World Case Studies**
- URL shortener, rate limiter, distributed cache, notification system, real-time chat — each with estimation, architecture, and key design decisions

# Elite System Design & Infrastructure Engineering: A Complete Reference

> **For the analyst who thinks in systems, patterns, and failure modes.**
> Every concept connects to production reality — how things break, how adversaries exploit them, and how engineers defend them at scale.

---

## Table of Contents

1. [Mental Models & First Principles](#1-mental-models--first-principles)
2. [Computer Architecture Foundations](#2-computer-architecture-foundations)
3. [Linux Kernel — Deep Internals](#3-linux-kernel--deep-internals)
4. [Networking — Layer by Layer](#4-networking--layer-by-layer)
5. [System Design Fundamentals](#5-system-design-fundamentals)
6. [Distributed Systems Theory](#6-distributed-systems-theory)
7. [Consensus & Coordination](#7-consensus--coordination)
8. [Storage Systems & Databases](#8-storage-systems--databases)
9. [Messaging & Event Streaming](#9-messaging--event-streaming)
10. [Caching Architecture](#10-caching-architecture)
11. [Load Balancing & Traffic Management](#11-load-balancing--traffic-management)
12. [Microservices & Service Mesh](#12-microservices--service-mesh)
13. [Container Internals & Orchestration](#13-container-internals--orchestration)
14. [Cloud Native Architecture](#14-cloud-native-architecture)
15. [Cloud Platforms Deep Dive](#15-cloud-platforms-deep-dive)
16. [Network Security Architecture](#16-network-security-architecture)
17. [Cloud Security](#17-cloud-security)
18. [Observability & Reliability Engineering](#18-observability--reliability-engineering)
19. [Infrastructure as Code](#19-infrastructure-as-code)
20. [API Design & Gateway Patterns](#20-api-design--gateway-patterns)
21. [Cryptography in Systems](#21-cryptography-in-systems)
22. [Performance Engineering](#22-performance-engineering)
23. [Disaster Recovery & Business Continuity](#23-disaster-recovery--business-continuity)
24. [Advanced Topics](#24-advanced-topics)

---

# 1. Mental Models & First Principles

## 1.1 The Hierarchy of Constraints

Before designing any system, anchor every decision to constraints. Systems fail when engineers optimize for the wrong constraint.

```
Constraint Hierarchy (must resolve top-down):
+--------------------------------------------------+
|  CORRECTNESS  — Does it do what it must do?      |
+--------------------------------------------------+
|  SAFETY       — Can it fail without data loss?   |
+--------------------------------------------------+
|  CONSISTENCY  — Is data always valid?            |
+--------------------------------------------------+
|  AVAILABILITY — Can it serve requests?           |
+--------------------------------------------------+
|  PERFORMANCE  — Does it serve requests fast?     |
+--------------------------------------------------+
|  COST         — Is it economically viable?       |
+--------------------------------------------------+
```

Violating this order produces systems that are fast but wrong, or cheap but dangerous.

## 1.2 Fallacies of Distributed Computing (Deutsch/Gosling, 1994)

These are not theoretical — they are failure modes that have caused production outages at every major company:

1. **The network is reliable** — Packets are dropped, reordered, duplicated. Your code will experience all three.
2. **Latency is zero** — Cross-datacenter RTT is 60–200ms. Even same-rack RTT is 0.1ms. Nothing is instantaneous.
3. **Bandwidth is infinite** — Serialization costs, MTU limits, and NIC saturation are real constraints.
4. **The network is secure** — Default trust is a design flaw. Assume every network segment is hostile.
5. **Topology doesn't change** — IPs change, nodes die, Kubernetes reschedules pods. Hardcoded IPs are landmines.
6. **There is one administrator** — Multi-team ownership means conflicting firewall rules and mismatched configs.
7. **Transport cost is zero** — Serialization/deserialization, compression, TLS handshake — all have CPU cost.
8. **The network is homogeneous** — You will have MTU mismatches, different network hardware, different OS TCP stacks.

**The correct response to each fallacy:** Design for the failure case as the default. Retries, idempotency, circuit breakers, and service discovery are not optional.

## 1.3 The CAP Theorem (Gilbert & Lynch, 2002)

In the presence of a **network partition**, a distributed system can guarantee either **Consistency** or **Availability**, not both.

```
         Consistency
              |
    CP        |        CA
(Zookeeper)  |   (Single-node RDBMS)
    HBase    |
             |
-------------+------------- (Network Partition)
             |
    AP       |
(Cassandra) |
  DynamoDB  |
             |
         Availability
```

**What CAP actually means:**
- **C (Consistency):** Every read receives the most recent write or an error. Not "eventual" — synchronous, linearizable.
- **A (Availability):** Every request receives a response (not necessarily the latest data). No errors, no timeouts.
- **P (Partition Tolerance):** The system continues operating when network partitions occur.

**The nuance engineers miss:** P is not optional. Networks always partition eventually. You must choose between C and A *during a partition*. In normal operation, well-designed systems can provide both.

**PACELC Extension (Abadi, 2012):**
Even without partitions (else-case), there is a tradeoff between **Latency** and **Consistency**. This is more practically relevant than CAP alone.

```
PACELC: if Partition → choose (A or C) ; ELse → choose (L or C)

System      P→A/C    E→L/C
DynamoDB    A        L
Cassandra   A        L
HBase       C        C
MySQL       C        C
Spanner     C        C (globally consistent via TrueTime)
```

## 1.4 The ACID vs BASE Spectrum

```
ACID (Traditional RDBMS)           BASE (Distributed NoSQL)
+----------------------------+     +----------------------------+
| Atomicity: all or nothing  |     | Basically Available:       |
| Consistency: rules hold    |     |   always responds          |
| Isolation: no interference |     | Soft state:                |
| Durability: survives crash |     |   may change without input |
+----------------------------+     | Eventually Consistent:     |
                                   |   converges over time      |
                                   +----------------------------+
```

The art of system design is knowing when each model is appropriate. **Financial transactions require ACID. User profile reads can tolerate BASE.**

## 1.5 Little's Law — The Foundation of Capacity Planning

```
L = λ × W

L = Average number of requests in the system
λ = Average arrival rate (requests/second)
W = Average time a request spends in the system
```

**Practical implication:** If your API handles 1000 req/s and average latency is 50ms:
```
L = 1000 × 0.050 = 50 concurrent requests in flight at any moment
```

This tells you how many threads/goroutines/connections you need. Violating this causes queuing, which causes latency spikes, which causes cascading failure.

## 1.6 The Power of Two Choices

When distributing load, choosing the least loaded of two random servers (vs. one random server) dramatically reduces maximum load. This is the foundation of many modern load balancers including Nginx's `least_conn` and Envoy's `LEAST_REQUEST`.

---

# 2. Computer Architecture Foundations

## 2.1 Memory Hierarchy — Why Latency Exists

```
Storage Level    Size        Latency       Bandwidth
+--------------------------------------------------------+
| CPU Registers  | ~1KB       | ~0.3 ns      | ~TB/s     |
| L1 Cache       | 32–64KB    | ~1 ns        | ~200 GB/s |
| L2 Cache       | 256KB–1MB  | ~4 ns        | ~100 GB/s |
| L3 Cache       | 8–64MB     | ~10–40 ns    | ~50 GB/s  |
| DRAM           | 8–256GB    | ~100 ns      | ~50 GB/s  |
| NVMe SSD       | 1–8TB      | ~100 µs      | ~7 GB/s   |
| SATA SSD       | 1–4TB      | ~1 ms        | ~550 MB/s |
| HDD            | 1–18TB     | ~10 ms       | ~200 MB/s |
| Network (LAN)  | ∞          | ~0.1–1 ms    | ~125 MB/s |
| Network (WAN)  | ∞          | ~30–300 ms   | ~varies   |
+--------------------------------------------------------+
```

**Design implication:** A database query that causes a page fault (DRAM miss → disk read) is 100,000× slower than an L1 cache hit. This is why in-memory databases (Redis, Memcached) and buffer pools exist. Every IO boundary you cross has a latency cliff.

## 2.2 CPU Cache Effects on System Design

**Cache lines:** CPUs load memory in 64-byte chunks (cache lines). If two threads write to different variables that share a cache line, they invalidate each other's cache — **false sharing**. This is why padding is added in concurrent data structures.

```c
// BAD: counter_a and counter_b share a cache line
struct {
    uint64_t counter_a;
    uint64_t counter_b;
} stats;

// GOOD: 64-byte padding prevents false sharing
struct {
    uint64_t counter_a;
    uint8_t  pad[56];
    uint64_t counter_b;
} stats;
```

**NUMA (Non-Uniform Memory Access):** On multi-socket systems, each CPU has local RAM. Accessing remote NUMA node memory is 2–3× slower than local access. Linux's `numactl` and kernel NUMA balancing exist for this reason.

## 2.3 I/O Models — The Foundation of Server Architecture

```
I/O Model          Blocking?   Thread-per-conn?  Used In
+------------------------------------------------------------------+
| Blocking I/O    | Yes        | Yes              | Apache httpd   |
| Non-blocking I/ | No (busy   | No               | —              |
|   O             |   poll)    |                  |                |
| I/O Multiplexin | No         | No               | Nginx, Redis   |
|  g (select/poll)|            |                  |                |
| epoll (Linux)   | No         | No (event loop)  | Nginx, Node.js |
| io_uring        | No         | No (ring buffer) | Modern servers |
| Asynchronous    | No         | No               | Windows IOCP   |
+------------------------------------------------------------------+
```

**epoll internals:**
```
epoll_create() → creates epoll fd (kernel event table)
epoll_ctl()    → register/modify/delete file descriptors
epoll_wait()   → block until events are ready

Kernel maintains a red-black tree of watched fds.
Ready fds are placed in a linked list — O(ready events), not O(watched fds).
This is why Nginx handles 10K+ connections on a single thread.
```

**io_uring (Linux 5.1+):** Shared ring buffer between userspace and kernel. Eliminates syscall overhead for I/O submission. Used in modern storage servers and databases. Critically relevant for security: io_uring has been a major attack surface (CVE-2022-29582, CVE-2023-2598).

## 2.4 Virtual Memory Architecture

```
Virtual Address Space (x86-64, 48-bit):
+----------------------------------+ 0xFFFFFFFFFFFFFFFF
|  Kernel Space (128TB)            |
|  (process can't read without     |
|   privilege escalation)          |
+----------------------------------+ 0xFFFF800000000000
|  [Non-canonical hole]            |
+----------------------------------+ 0x0000800000000000
|  User Space (128TB)              |
|  +----------------------------+  |
|  | Stack (grows down)         |  |
|  | ...                        |  |
|  | Heap (grows up)            |  |
|  | BSS (zeroed data)          |  |
|  | Data segment               |  |
|  | Text segment (code)        |  |
|  +----------------------------+  |
+----------------------------------+ 0x0000000000000000
```

**Page Table Walk (4-level, x86-64):**
```
Virtual Address [63:48=sign][47:39=PML4][38:30=PDP][29:21=PD][20:12=PT][11:0=offset]
                              ↓
                      CR3 → PML4 table
                              ↓
                          PDP table
                              ↓
                          PD table
                              ↓
                          PT entry → Physical frame + offset
```

Each level is a 4KB page with 512 8-byte entries. TLB caches these translations. A TLB miss costs a full page table walk (~100ns). This is why huge pages (2MB/1GB) matter for database workloads — fewer TLB entries, fewer misses.

---

# 3. Linux Kernel — Deep Internals

## 3.1 Process Model

```
Kernel view of execution units:
+------------------------------------------+
| task_struct (kernel's process descriptor) |
|  pid         — process ID                 |
|  tgid        — thread group ID            |
|  mm          — memory descriptor          |
|  fs          — filesystem info            |
|  files       — open file descriptors      |
|  signal      — signal handlers            |
|  cred        — credentials (uid, gid, cap)|
|  cgroup      — resource control group     |
|  nsproxy     — namespace proxy            |
+------------------------------------------+
```

**fork() vs clone() vs pthread_create():**
- `fork()`: Copies parent's address space (COW — Copy-on-Write). New `mm`, new `pid`, new `tgid`.
- `clone()`: Creates a task with selective sharing of `mm`, `fs`, `files`, `signals`.
- `pthread_create()`: `clone()` with `CLONE_VM | CLONE_FS | CLONE_FILES | CLONE_SIGHAND` — shares everything. Same `mm`, different `pid`, same `tgid`.

**This is why containers are processes:** `clone()` with namespace flags (`CLONE_NEWPID`, `CLONE_NEWNET`, `CLONE_NEWNS`, etc.) creates a "container" — an isolated task with its own view of resources.

## 3.2 Linux Scheduling

### CFS (Completely Fair Scheduler)

CFS replaced the O(1) scheduler in kernel 2.6.23. Key concepts:

```
Virtual Runtime (vruntime):
  vruntime += delta_exec × (NICE_0_LOAD / task_weight)

Tasks with lower vruntime run next.
CFS stores runnable tasks in a red-black tree keyed by vruntime.
The leftmost node is always the next task to run.
```

**Scheduler latency:** Default target latency is 6ms (all runnable tasks get a slice). If there are N tasks, each gets `6ms / N`. Minimum granularity is 0.75ms.

**SCHED_FIFO / SCHED_RR (Real-Time):** Fixed priority, preempt normal tasks. Used in audio servers, databases, network drivers. Risk: a misbehaving RT task can starve the system.

**CPU affinity and NUMA scheduling:**
```bash
taskset -c 0,1 ./server    # Pin process to CPUs 0 and 1
numactl --cpunodebind=0 --membind=0 ./db  # Pin to NUMA node 0
```

### cgroups v2 CPU Scheduling

```
cpu.weight       — CFS weight (default 100, range 1–10000)
cpu.max          — bandwidth: "quota period" e.g., "50000 100000" = 50% CPU
cpu.pressure     — PSI (Pressure Stall Information) metrics
```

Kubernetes translates `resources.requests.cpu` to `cpu.weight` and `resources.limits.cpu` to `cpu.max`.

## 3.3 Memory Management

### Page Allocation

```
Buddy Allocator:
  Manages physical pages in power-of-2 chunks.
  When allocating, finds smallest block ≥ request.
  When freeing, merges with "buddy" blocks if both free.

  Zones:
    ZONE_DMA   (<16MB)  — Legacy DMA devices
    ZONE_DMA32 (<4GB)   — 32-bit DMA devices
    ZONE_NORMAL (>4GB)  — Normal allocations
    ZONE_HIGHMEM        — (32-bit only, not used in x86-64)
```

**Slab Allocator (SLUB/SLAB/SLOB):** Manages kernel objects (task_struct, inode, dentry) in caches of fixed-size objects. Avoids fragmentation. Exploited by kernel exploits that target slab cross-cache attacks.

### OOM Killer

When system runs out of memory:
1. Kernel tries to reclaim pages (swap, drop caches)
2. If insufficient, `oom_kill_process()` is called
3. OOM killer selects victim via `oom_badness()` score: `(rss + swap) × adjustment`
4. `oom_score_adj` in `/proc/<pid>/oom_score_adj` biases selection (-1000 = never kill, +1000 = kill first)

**In Kubernetes:** Pods with `BestEffort` QoS class are killed first. `Guaranteed` pods last.

### Memory Mapping

```
mmap() syscall:
  MAP_PRIVATE  — COW mapping, changes not written back
  MAP_SHARED   — Changes visible to all processes, written to file
  MAP_ANONYMOUS — Not backed by file (heap, stack)
  MAP_POPULATE — Pre-fault pages (avoid lazy allocation latency)
  MAP_LOCKED   — Lock pages in RAM (mlockall for databases)
  MAP_HUGETLB  — Use huge pages (reduce TLB pressure)
```

**Transparent Huge Pages (THP):** Kernel automatically promotes 2MB-aligned regions to huge pages. **Dangerous for databases** (Redis, MongoDB, MySQL all recommend disabling THP) because compaction causes latency spikes.

```bash
echo never > /sys/kernel/mm/transparent_hugepage/enabled  # Disable THP
echo always > /sys/kernel/mm/transparent_hugepage/enabled  # Enable THP
```

## 3.4 Virtual File System (VFS)

```
VFS Layer Architecture:
+------------------------------------------+
|  User Process                            |
|  open("/etc/passwd", O_RDONLY)           |
+------------------------------------------+
         ↓ syscall (sys_open)
+------------------------------------------+
|  VFS Layer (generic interface)           |
|  struct file_operations                  |
|  struct inode_operations                 |
|  struct super_operations                 |
+------------------------------------------+
         ↓ filesystem-specific handlers
+--------+--------+--------+-------+-------+
|  ext4  |  xfs   |  btrfs |  tmpfs| procfs|
+--------+--------+--------+-------+-------+
         ↓
+------------------------------------------+
|  Block Layer (BIO, request queue)        |
+------------------------------------------+
         ↓
+------------------------------------------+
|  Storage Driver (NVMe, SCSI, virtio-blk) |
+------------------------------------------+
```

**Key VFS objects:**
- **superblock:** Filesystem metadata (block size, inode count, mount options)
- **inode:** File metadata (permissions, timestamps, data block pointers) — NOT the filename
- **dentry:** Directory entry (name → inode mapping). Cached in dcache for fast lookup.
- **file:** Open file instance. Has `struct file_operations` (read, write, mmap, ioctl)

**Why `/proc` and `/sys` are not real filesystems:** They are pseudo-filesystems. Reads/writes invoke kernel functions, not disk operations. `/proc/[pid]/maps` doesn't read a file — it calls `show_map()` in the kernel.

## 3.5 Linux Namespaces

Namespaces are the isolation primitive underlying containers. Each namespace isolates a different resource:

```
Namespace   Flag              Isolates
+--------------------------------------------------------------------+
| PID        CLONE_NEWPID      Process IDs (container's pid 1)       |
| Network    CLONE_NEWNET      Network stack (interfaces, routes, iptables) |
| Mount      CLONE_NEWNS       Filesystem mount points                |
| UTS        CLONE_NEWUTS      Hostname and domain name               |
| IPC        CLONE_NEWIPC      POSIX message queues, SysV IPC        |
| User       CLONE_NEWUSER     UIDs/GIDs (UID 0 inside != UID 0 outside) |
| Cgroup     CLONE_NEWCGROUP   cgroup root                            |
| Time       CLONE_NEWTIME     System clocks (CLOCK_BOOTTIME, etc.)  |
+--------------------------------------------------------------------+
```

**Namespace security implications:**
- User namespaces allow unprivileged users to create containers — massive attack surface (CVE-2022-0492, CVE-2023-1829)
- PID namespace escape: process can access `/proc` of host if mount namespace not isolated
- Network namespace shared with host: container can see host traffic

```bash
# Inspect namespaces of a process
ls -la /proc/<pid>/ns/

# Enter a namespace
nsenter --target <pid> --pid --net --mount --uts /bin/bash

# List all namespaces on system
lsns
```

## 3.6 cgroups v2

cgroups control and account for resource usage per process group. cgroups v2 uses a unified hierarchy (single tree vs v1's multiple hierarchies).

```
cgroup v2 hierarchy:
/sys/fs/cgroup/
├── cgroup.controllers        # Available controllers
├── cgroup.subtree_control    # Delegated to children
├── memory.max                # Hard memory limit
├── cpu.weight                # Relative CPU share
├── io.max                    # I/O bandwidth limit
├── system.slice/
│   ├── sshd.service/
│   └── nginx.service/
└── user.slice/
    └── user-1000.slice/
```

**Resource controllers:**
```
cpu      — cpu.weight (shares), cpu.max (hard limit)
memory   — memory.max, memory.high, memory.swap.max
io       — io.max (bps/iops per device), io.weight
pids     — pids.max (fork bomb prevention)
rdma     — RDMA/InfiniBand resource limits
hugetlb  — Huge page allocation limits
```

**PSI (Pressure Stall Information):** Added in kernel 4.20. Measures time tasks spent stalled waiting for a resource. Used by systemd, Facebook's oomd, and container runtimes for smart eviction.

```bash
cat /sys/fs/cgroup/memory.pressure
# some avg10=0.12 avg60=0.05 avg300=0.02 total=1234567
# full avg10=0.00 avg60=0.00 avg300=0.00 total=0
```

## 3.7 Linux Security Modules (LSM)

LSM provides hooks throughout the kernel for mandatory access control:

```
LSM Hook Examples:
  security_inode_permission() — before every file access
  security_socket_connect()   — before every TCP connect
  security_bprm_check()       — before every exec()
  security_ptrace_access()    — before ptrace attach
```

**SELinux:** Labels every object (file, process, socket) with a security context. Policies define allowed transitions. Violation = denial + audit log. Netflix, RHEL, Android use SELinux.

**AppArmor:** Path-based (not label-based). Profiles are per-executable. Simpler than SELinux but less expressive. Default on Ubuntu/Debian. Docker uses AppArmor profiles.

**seccomp-bpf:** Filters syscalls per process using BPF programs. Docker's default seccomp profile blocks ~44 syscalls (including `ptrace`, `mount`, `kexec_load`). Most powerful syscall filtering mechanism. Used by Chrome's sandbox, systemd services, containers.

```c
// seccomp-bpf: allow only read, write, exit_group
struct sock_filter filter[] = {
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, offsetof(struct seccomp_data, nr)),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_read, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, __NR_write, 0, 1),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW),
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL),
};
```

## 3.8 eBPF — The Kernel Programmability Revolution

eBPF (extended Berkeley Packet Filter) allows running sandboxed programs in the kernel without modifying kernel source or loading modules.

```
eBPF Program Lifecycle:
  1. Write BPF program (C with libbpf or BCC)
  2. Compile to BPF bytecode
  3. Load via bpf() syscall
  4. Kernel verifier checks:
     - No unbounded loops (terminates)
     - No out-of-bounds memory access
     - Register types are valid
     - No privileged operations without capability
  5. JIT compile to native machine code
  6. Attach to hook point (tracepoint, kprobe, XDP, etc.)
  7. Run in kernel context on event
```

**eBPF hook points:**
```
XDP        — Packet processing at driver level (before kernel networking)
TC         — Traffic control (packet filtering, shaping)
socket     — Per-socket packet filtering
kprobes    — Any kernel function entry/return
tracepoints — Stable kernel trace events
uprobes    — Any userspace function entry/return
LSM        — Security hooks (MAC enforcement)
cgroup     — Per-cgroup hooks
perf events — Hardware/software performance events
```

**Security implications:** eBPF has dramatically changed Linux security tooling:
- **Cilium:** eBPF-based network policy (replaces iptables)
- **Falco:** eBPF-based runtime security (system call monitoring)
- **Pixie:** eBPF-based observability without instrumentation
- **Tetragon:** eBPF-based security enforcement with real-time kill

**Attack surface:** eBPF is also an attacker's playground. Malware using eBPF: `ebpfkit`, `TripleCross`. CVE-2021-3490 (verifier bypass → kernel RCE). Requires `CAP_BPF` or `CAP_SYS_ADMIN` — check container capabilities.

```bash
# List loaded BPF programs
bpftool prog list

# Show BPF maps (data structures)
bpftool map list

# Dump BPF program instructions
bpftool prog dump xlated id <id>
```

## 3.9 Linux Networking Stack Internals

```
Packet RX path (simplified):
+--------------------------------------------------+
| NIC Hardware (DMA to ring buffer)                |
+--------------------------------------------------+
         ↓ Hardware interrupt (NAPI polls in softirq)
+--------------------------------------------------+
| Driver (e.g., ixgbe, i40e, virtio-net)           |
| Builds sk_buff (socket buffer)                   |
+--------------------------------------------------+
         ↓
+--------------------------------------------------+
| XDP hook (if loaded, can DROP/TX/REDIRECT)       |
+--------------------------------------------------+
         ↓
+--------------------------------------------------+
| Network Core (netif_receive_skb)                 |
| Generic XDP → TC ingress → Netfilter/iptables    |
+--------------------------------------------------+
         ↓
+--------------------------------------------------+
| IP layer (routing decision)                      |
+--------------------------------------------------+
         ↓
+--------------------------------------------------+
| TCP/UDP layer (socket buffer queues)             |
+--------------------------------------------------+
         ↓
+--------------------------------------------------+
| Socket receive buffer → Application read()       |
+--------------------------------------------------+
```

**Key structures:**
- `sk_buff (skb)`: Kernel's packet representation. Contains data, metadata, protocol headers. Passed up/down the stack without copying (only pointers change).
- `net_device`: Represents a network interface. Has RX/TX queues.
- `sock`: Kernel socket. Has send/receive buffers (`sk_sndbuf`, `sk_rcvbuf`).

**TCP Tuning parameters:**
```bash
# Socket buffer sizes
sysctl net.core.rmem_max        # Max receive buffer
sysctl net.core.wmem_max        # Max send buffer
sysctl net.ipv4.tcp_rmem        # TCP receive buffer: min/default/max
sysctl net.ipv4.tcp_wmem        # TCP send buffer: min/default/max

# Connection handling
sysctl net.ipv4.tcp_syn_backlog     # SYN queue depth
sysctl net.core.somaxconn           # Accept queue depth
sysctl net.ipv4.tcp_max_syn_backlog # Max SYN-RECEIVED sockets

# Congestion control
sysctl net.ipv4.tcp_congestion_control  # bbr, cubic, reno
sysctl net.ipv4.tcp_slow_start_after_idle=0  # Disable for persistent connections

# TIME_WAIT
sysctl net.ipv4.tcp_tw_reuse=1     # Allow reuse of TIME_WAIT sockets
sysctl net.ipv4.tcp_fin_timeout=15 # Reduce FIN timeout
```

## 3.10 Netfilter & iptables Architecture

```
Netfilter hooks in the kernel:
  NF_INET_PRE_ROUTING  → PREROUTING chain (DNAT, routing decision)
  NF_INET_LOCAL_IN     → INPUT chain (to local process)
  NF_INET_FORWARD      → FORWARD chain (routed packets)
  NF_INET_LOCAL_OUT    → OUTPUT chain (from local process)
  NF_INET_POST_ROUTING → POSTROUTING chain (SNAT, final output)

Tables:
  raw      — Connection tracking bypass
  mangle   — Packet modification (TOS, TTL, mark)
  nat      — Network address translation
  filter   — Packet filtering (default table)
  security — SELinux security context marking
```

**Packet traversal:**
```
Incoming packet:
  PREROUTING(raw→mangle→nat) → routing → INPUT(mangle→filter→security)

Forwarded packet:
  PREROUTING → routing → FORWARD(mangle→filter→security) → POSTROUTING

Outgoing packet:
  OUTPUT(raw→mangle→nat→filter→security) → POSTROUTING(mangle→nat)
```

**iptables performance problem:** iptables is O(n) — every packet traverses every rule in sequence. With thousands of rules (Kubernetes default), this becomes a bottleneck. **nftables** uses hash maps and radix trees for O(1) lookups. **eBPF/XDP** bypasses the stack entirely for maximum performance.

## 3.11 Linux Capabilities

Capabilities split root privileges into discrete units. Instead of `setuid root`, grant only needed capabilities:

```
CAP_NET_ADMIN    — Modify network config, iptables, routing
CAP_NET_RAW      — Raw sockets (tcpdump, ping)
CAP_SYS_ADMIN    — Mount, namespaces, clone, BPF, many others (too broad)
CAP_SYS_PTRACE   — ptrace any process
CAP_SYS_MODULE   — Load/unload kernel modules
CAP_SETUID       — Change UID (privilege escalation risk)
CAP_DAC_OVERRIDE — Bypass file permission checks
CAP_CHOWN        — Change file ownership
CAP_KILL         — Send signals to any process
CAP_NET_BIND_SERVICE — Bind ports <1024
```

**Container capability defaults:** Docker drops these by default: `CAP_SYS_ADMIN`, `CAP_SYS_PTRACE`, `CAP_SYS_MODULE`, `CAP_NET_RAW`. Running `--privileged` grants all capabilities — equivalent to running as root on the host.

---

# 4. Networking — Layer by Layer

## 4.1 TCP/IP Stack Deep Dive

### TCP State Machine

```
                        CLOSED
                           |
              passive open |  active open
                           |
                        LISTEN ←——————————————
                           |                   |
              SYN received |                   |
                           ↓                   |
                       SYN_RCVD               SYN_SENT
                           |                   |
              ACK received |   SYN+ACK received|
                           ↓                   |
                      ESTABLISHED ←————————————
                           |
               close/FIN   |
                           ↓
                       FIN_WAIT_1
                           |
               FIN received|  ACK received
                    ↓      |
              CLOSING   FIN_WAIT_2
                    |      |
          ACK recv  |      | FIN received
                    ↓      ↓
                   TIME_WAIT (2×MSL = ~120s)
                           |
                        CLOSED
```

**TIME_WAIT exists because:**
1. The final ACK may be lost — peer stays in LAST_ACK and retransmits FIN
2. Delayed duplicate packets from old connection must expire before new connection on same 4-tuple

**SYN cookies:** When SYN backlog is full, kernel encodes connection state in the ISN (Initial Sequence Number) without allocating state. Protects against SYN flood attacks. Enabled by `net.ipv4.tcp_syncookies=1`.

### TCP Congestion Control

```
Slow Start:
  cwnd starts at ~10 MSS
  Doubles each RTT until ssthresh
  On loss: ssthresh = cwnd/2, restart

CUBIC (default Linux):
  Window grows as cubic function of time since last loss
  Aggressively reclaims bandwidth

BBR (Google, 2016):
  Models network as pipe: bandwidth × RTT = BDP
  Maintains sending rate = bottleneck bandwidth
  Does NOT use packet loss as congestion signal
  Better for long-fat networks (intercontinental links)
  Dramatically better than CUBIC for cloud workloads
```

## 4.2 DNS Architecture

```
DNS Resolution Path:
  Browser → OS resolver → /etc/resolv.conf → Recursive resolver
                                              (ISP or 8.8.8.8)
                                                     ↓
                                              Root nameservers (.)
                                                     ↓
                                              TLD nameservers (.com)
                                                     ↓
                                              Authoritative NS
                                                     ↓
                                              A/AAAA record
```

**DNS record types:**
```
A      — IPv4 address
AAAA   — IPv6 address
CNAME  — Canonical name (alias) — adds one RTT
MX     — Mail exchange
TXT    — Arbitrary text (SPF, DKIM, domain verification)
NS     — Nameserver
SOA    — Start of authority (zone metadata)
SRV    — Service location (protocol, port, target)
PTR    — Reverse DNS (IP → hostname)
CAA    — Certification Authority Authorization
TLSA   — DANE (TLS certificate binding)
```

**DNS Security:**
- **DNSSEC:** Cryptographically signs DNS responses. Prevents cache poisoning (Kaminsky attack). Uses RRSIG, DNSKEY, DS record chain.
- **DoT (DNS over TLS):** Encrypts DNS on port 853. Prevents eavesdropping and MITM.
- **DoH (DNS over HTTPS):** DNS on port 443. Harder to block/monitor. Used by Firefox, Chrome.
- **DNS rebinding:** Attack where attacker controls DNS to return private IP after TTL expires, bypassing same-origin policy.

## 4.3 HTTP/1.1 → HTTP/2 → HTTP/3

```
HTTP/1.1:
  - One request per connection (without pipelining)
  - Head-of-line blocking
  - Text-based headers (redundant, uncompressed)
  - Default: multiple TCP connections (6/domain in browsers)

HTTP/2 (RFC 7540):
  - Binary framing
  - Multiplexed streams on single TCP connection
  - Header compression (HPACK)
  - Server push
  - Still has TCP-level HOL blocking (one lost packet stalls all streams)

HTTP/3 (RFC 9114):
  - Runs over QUIC (UDP-based transport)
  - Stream-level loss recovery (no cross-stream HOL blocking)
  - 0-RTT connection establishment (session resumption)
  - Connection migration (IP change doesn't break connection)
  - Mandatory TLS 1.3
```

**QUIC internals:**
```
QUIC packet structure:
  Header:
    Long header (handshake): version, source/dest connection IDs
    Short header (data): spin bit, connection ID, packet number
  
  Frames:
    STREAM    — Application data
    ACK       — Acknowledgments (ranges, not cumulative)
    CRYPTO    — TLS handshake data
    CONNECTION_CLOSE — Clean shutdown
    PING      — Keepalive

Connection ID:
  Not tied to IP:port. Client can change IP (WiFi→cellular)
  without reconnecting. Server identifies by connection ID.
```

## 4.4 TLS 1.3 Internals

```
TLS 1.3 Handshake (1-RTT):
  Client → Server: ClientHello
                   (supported ciphers, key_share: ECDHE public key, 
                    supported_versions, SNI, ALPN)
  
  Server → Client: ServerHello (cipher, key_share: server ECDHE public key)
                   {EncryptedExtensions}
                   {Certificate}
                   {CertificateVerify}  ← signature proves cert ownership
                   {Finished}           ← HMAC of entire handshake
  
  Client → Server: {Finished}
                   {HTTP Request}       ← Already sending data!
  
  [Application Data]
```

**TLS 1.3 improvements over 1.2:**
- Removed: RSA key exchange (no forward secrecy), MD5/SHA1, RC4, DES, 3DES, export ciphers
- Mandatory: Forward secrecy (ECDHE only), AEAD ciphers (AES-GCM, ChaCha20-Poly1305)
- 0-RTT resumption: Client sends data in first packet using pre-shared key (PSI anti-replay needed)

**Cipher suites (TLS 1.3 — only 5 allowed):**
```
TLS_AES_256_GCM_SHA384
TLS_CHACHA20_POLY1305_SHA256
TLS_AES_128_GCM_SHA256
TLS_AES_128_CCM_8_SHA256
TLS_AES_128_CCM_SHA256
```

## 4.5 BGP & Internet Routing

```
BGP (Border Gateway Protocol) — The routing protocol of the internet

AS (Autonomous System): A network under single administrative control
  (ISP, CDN, cloud provider, large enterprise)
  Identified by ASN (32-bit number)

BGP speakers exchange:
  OPEN message    — Establish session, exchange capabilities
  UPDATE message  — Announce/withdraw routes (prefix + path attributes)
  KEEPALIVE       — Every 60s (hold timer = 180s)
  NOTIFICATION    — Error, then close

Route selection (in order):
  1. Highest LOCAL_PREF (prefer internal routes)
  2. Shortest AS_PATH (fewest hops)
  3. Lowest ORIGIN (IGP < EGP < Incomplete)
  4. Lowest MED (Multi-Exit Discriminator)
  5. eBGP over iBGP
  6. Lowest IGP metric to next hop
  7. Lowest Router ID (tiebreak)
```

**BGP security:**
- **BGP hijacking:** Announcing more-specific prefix to steal traffic. Famous example: Pakistan Telecom hijacking YouTube (2008), Rostelecom hijacking AWS routes (2020).
- **RPKI (Resource Public Key Infrastructure):** Cryptographically signs prefix-origin mappings. Route Origin Authorization (ROA) specifies which AS can originate a prefix.
- **BGPsec:** Signs AS_PATH (prevents path manipulation). Complex, low adoption.

---

# 5. System Design Fundamentals

## 5.1 The Design Process

Elite engineers follow a structured process. Skipping steps produces fragile systems:

```
Phase 1: Requirements (non-negotiable)
  Functional:   What does it do?
  Non-functional: SLA (99.9% = 8.7h downtime/year, 99.99% = 52min/year)
                  Latency targets (p50, p95, p99)
                  Throughput (peak QPS, sustained QPS)
                  Data volume (current and 5-year projection)
                  Consistency requirements
                  Security requirements

Phase 2: Capacity Estimation
  QPS → compute nodes needed
  Data size → storage tier selection
  Read/write ratio → caching strategy
  Bandwidth → CDN decision

Phase 3: API Design
  REST vs gRPC vs GraphQL vs WebSocket
  Request/response schemas
  Authentication mechanism

Phase 4: High-Level Design
  Core components and their responsibilities
  Data flow between components
  Technology choices with justification

Phase 5: Deep Dive
  Critical path optimization
  Bottleneck identification
  Failure mode analysis

Phase 6: Operational Concerns
  Monitoring and alerting
  Deployment strategy
  Incident response
```

## 5.2 Availability Calculations

```
Availability    Downtime/Year   Downtime/Month
99%             3.65 days       7.31 hours
99.5%           1.83 days       3.65 hours
99.9%           8.77 hours      43.83 minutes
99.95%          4.38 hours      21.92 minutes
99.99%          52.6 minutes    4.38 minutes
99.999%         5.26 minutes    26.3 seconds
```

**Composite availability:** Components in series multiply:
```
A_total = A_1 × A_2 × A_3 × ... × A_n

Three 99.9% services in series = 99.9% × 99.9% × 99.9% = 99.7%
```

**Components in parallel** (any one can serve request):
```
A_total = 1 - (1 - A_1) × (1 - A_2) ... × (1 - A_n)

Two 99% services in parallel = 1 - (0.01 × 0.01) = 99.99%
```

This is why redundancy exists — parallel components dramatically improve availability.

## 5.3 Scalability Patterns

### Horizontal vs Vertical Scaling

```
Vertical (Scale Up):              Horizontal (Scale Out):
+------------------+              +------+ +------+ +------+
|   HUGE SERVER    |              | srv1 | | srv2 | | srv3 |
|  128 CPU cores   |              | 8CPU | | 8CPU | | 8CPU |
|  1TB RAM         |              | 32GB | | 32GB | | 32GB |
|  100TB SSD       |              +------+ +------+ +------+
+------------------+

Pros: simple, no distributed         Pros: infinite scale, cheap commodity
      systems complexity                    hardware, fault tolerant
Cons: SPOF, diminishing returns,     Cons: distributed complexity,
      expensive, has limits                 consistency challenges
```

### Stateless vs Stateful Services

**Stateless:** Any instance can handle any request. Scale freely. No session affinity. Load balancing trivial. Examples: REST APIs, gRPC services, GraphQL resolvers.

**Stateful:** Instance holds state. Client must connect to specific instance OR state must be externalized. Kubernetes StatefulSets provide stable pod identities for stateful services.

**The Rule:** Externalize state. Move state from application servers to specialized storage (Redis, Postgres, Cassandra). Then application tier becomes stateless and horizontally scalable.

## 5.4 Rate Limiting

### Token Bucket Algorithm

```
Token Bucket:
  - Bucket holds up to `capacity` tokens
  - Tokens added at `rate` per second
  - Each request consumes 1 token
  - If no tokens: reject or queue

Properties:
  - Allows bursts up to `capacity`
  - Sustains `rate` requests/second
  - Classic: Nginx limit_req, AWS API Gateway
```

### Sliding Window Counter

```
Sliding Window:
  - Divide time into fixed windows (e.g., 1 minute)
  - Count requests in current window + weighted count from previous window
  - weight = (window_size - elapsed) / window_size
  - effective_count = prev_count × weight + curr_count

More accurate than fixed window (prevents edge-of-window bursts)
Redis-based implementation: sorted set with timestamp as score
```

### Leaky Bucket

```
Leaky Bucket:
  - Requests enter queue
  - Queue drains at fixed rate
  - If queue full: reject
  - Output is always at fixed rate

Used for: Traffic shaping, network QoS
NOT suitable for: API rate limiting (queuing can cause high latency)
```

**Distributed rate limiting:** Single node rate limiting doesn't work for distributed systems. Use Redis with Lua scripts for atomic check-and-increment. Cell-based rate limiting (Stripe's approach): each cell tracks a limit independently, good for high-traffic with acceptable small overdraft.

## 5.5 Consistent Hashing

The problem: When you add/remove nodes in a cluster, traditional modulo hashing (`key % N`) remaps almost all keys → massive cache misses, thundering herd.

```
Consistent Hashing Ring:
  - Hash space: 0 to 2^32 - 1 (ring)
  - Nodes placed at positions on ring (hashed by node ID)
  - Key maps to first node clockwise from its hash position

  Adding a node: Only keys between new node and its predecessor remapped
  Removing a node: Only keys on that node remapped to successor

Virtual nodes (vnodes):
  Each physical node owns multiple positions on ring
  Provides more even distribution
  More points to remap per add/remove, but distribution is uniform
```

**Used in:** Cassandra, Amazon DynamoDB, Riak, Chord DHT, Nginx upstream hashing.

## 5.6 Data Partitioning (Sharding)

**Horizontal partitioning (sharding):** Rows split across multiple databases. Each shard has same schema.

```
Sharding strategies:

Range-based:
  Shard 1: user_id 1–1,000,000
  Shard 2: user_id 1,000,001–2,000,000
  Pros: Range queries efficient
  Cons: Hot spots (new users all go to last shard)

Hash-based:
  shard = hash(user_id) % num_shards
  Pros: Even distribution
  Cons: Range queries span all shards, resharding expensive

Directory-based:
  Lookup table: user_id → shard_id
  Pros: Flexible, can move records
  Cons: Lookup table is a bottleneck and SPOF

Geographic:
  Shard by region (EU users → EU shard)
  Pros: Data locality, compliance (GDPR)
  Cons: Uneven distribution by region
```

**Resharding:** Inevitable as data grows. Hot partition is the most common trigger. Strategies: double sharding (2N → 4N shards), consistent hashing (minimizes remapping), logical shards (more logical shards than physical, allows movement without key remapping).

## 5.7 Read/Write Splitting

```
Single Primary with Read Replicas:

         ┌─────────────┐
Writes → │   Primary   │ ──────→ replication log
         └─────────────┘
                ↓ replication (async or semi-sync)
         ┌──────────────────────────────┐
         │ Replica 1  Replica 2  ...    │
         └──────────────────────────────┘
                ↑
            Reads

Application must route:
  - Writes → Primary
  - Reads → Any replica (if stale reads acceptable)
  - Recent writes → Primary (read-your-writes consistency)
```

**Replication lag:** Async replication means replicas can be seconds behind. Read-after-write from replica may return stale data. Handle with: read-your-writes from primary immediately after write, sticky sessions to primary, version tracking.

---

# 6. Distributed Systems Theory

## 6.1 Consistency Models (From Strong to Weak)

```
Linearizability (Strongest)
  Every operation appears to execute atomically at a single point
  in real time between its invocation and response.
  All operations observe a single globally agreed ordering.
  Cost: High latency (requires coordination)
  Examples: Spanner, etcd, Zookeeper

Sequential Consistency
  Operations appear to execute in some sequential order consistent
  with program order of each process. No real-time constraint.
  Slightly weaker than linearizability.

Causal Consistency
  Causally related operations seen in same order by all processes.
  Concurrent operations may be seen in different orders.
  Examples: MongoDB causal sessions, COPS

Read-your-writes (Session Consistency)
  A process always sees its own writes.
  Different processes may see different versions.

Monotonic Reads
  If a process reads value v, subsequent reads never return older value.

Eventual Consistency (Weakest)
  Given no new updates, all replicas converge to same value.
  No ordering guarantee. No freshness guarantee.
  Examples: Cassandra (with QUORUM relaxed), DynamoDB (eventually consistent reads)
```

## 6.2 The Two Generals Problem

**Why distributed consensus is fundamentally hard:**

Two armies must coordinate attack. They communicate only via messengers through enemy territory (messages may be lost). No matter how many acknowledgments are sent, neither general can be 100% certain the other received the final confirmation.

**System design implication:** In distributed systems, you cannot guarantee that both sides of a transaction commit atomically without a coordinator. This is why 2PC (Two-Phase Commit) exists — but it has its own failure modes (coordinator crash after PREPARE but before COMMIT leaves participants blocked indefinitely).

## 6.3 Byzantine Fault Tolerance

**Crash fault:** Node stops responding. Easy to detect (timeout). Most distributed systems handle this.

**Byzantine fault:** Node responds incorrectly (corrupted, malicious, buggy). Sends different responses to different nodes. **Most distributed systems do NOT handle this.**

**Byzantine fault tolerance requires:** 3f+1 nodes to tolerate f Byzantine failures. Consensus requires 2f+1 correct nodes agreeing.

**BFT in practice:**
- Blockchain (Bitcoin, Ethereum): PBFT variants, PoW, PoS
- Aerospace (flight computers): Redundant voting systems
- Hyperledger Fabric: PBFT-based ordering service
- Most databases assume non-Byzantine: only crash faults

## 6.4 Lamport Clocks & Vector Clocks

**The problem:** In distributed systems, there is no global clock. Events cannot be absolutely ordered.

**Lamport Timestamps:**
```
Rule 1: Increment own clock on each event
Rule 2: On send, attach current timestamp
Rule 3: On receive, max(local_ts, received_ts) + 1

Result: If A → B (A causes B), then ts(A) < ts(B)
Limitation: ts(A) < ts(B) does NOT mean A → B (concurrent events can have any order)
```

**Vector Clocks:**
```
Each node maintains a vector V[1..N] (one entry per node)
On local event: V[self]++
On send: attach V
On receive message with V':
  For each i: V[i] = max(V[i], V'[i])
  V[self]++

Comparison:
  A happened-before B if: ∀i: V_A[i] <= V_B[i] (with at least one strict <)
  A and B concurrent if: neither ≤ the other

Used in: Riak, Dynamo-style databases for conflict detection
Problem: Vector grows with number of nodes (dotted version vectors solve this)
```

## 6.5 CRDT — Conflict-free Replicated Data Types

CRDTs enable automatic conflict resolution without coordination:

```
Two types:
  State-based (CvRDT): Merge full state. Must be commutative, associative, idempotent.
  Operation-based (CmRDT): Propagate operations. Must be commutative.

Common CRDTs:
  G-Counter:   Grow-only counter. Each node has own counter, total = sum.
  PN-Counter:  Positive + Negative G-counters. Supports decrement.
  G-Set:       Grow-only set. Add only, no remove.
  2P-Set:      Two G-sets (add-set, remove-set). Can remove but not re-add.
  LWW-Register: Last-Write-Wins register (timestamp-based merge).
  OR-Set:      Observed-Remove set. Unique tag per element. Tags win over removes.
  RGA:         Replicated Growable Array (collaborative text editing).
  YATA/YJS:   Yet Another Transformation Approach (used in VSCode Live Share).
```

**Used in:** Redis (some types), Riak, Azure Cosmos DB, Figma's multiplayer, Apple Notes sync, collaborative editors.

## 6.6 Time & Clocks in Distributed Systems

**Physical clocks:** NTP-synchronized. Drift ±1ms typically. Not monotonic after correction. **Never use `gettimeofday()` for measuring elapsed time** — use `CLOCK_MONOTONIC`.

**Google TrueTime (Spanner):**
```
TrueTime API:
  TT.now()   → [earliest, latest] — guaranteed interval containing true time
  TT.after(t) → true if t has definitely passed
  TT.before(t) → true if t has definitely not passed

Atomic clocks + GPS in each datacenter
Uncertainty typically ±7ms

Spanner uses this for external consistency:
  Commit timestamp ts > TT.now().latest
  Wait until TT.after(ts) before returning
  Guarantees: any transaction started after this sees committed data
```

**Hybrid Logical Clocks (HLC):** Combines physical time and logical time. Monotonically increasing. Used by CockroachDB, YugabyteDB.

## 6.7 Leader Election

**Why needed:** Many distributed systems need a single authoritative coordinator for certain operations (leader election for primary-backup replication, master in distributed locks, shard owner).

**Bully Algorithm:**
```
Process with highest ID wins.
Steps:
  1. Node discovers leader is dead (timeout)
  2. Sends ELECTION message to all nodes with higher ID
  3. If no response, declares itself leader
  4. If response received, waits for OK message
  Problems: O(n²) messages, split-brain possible
```

**Raft leader election:**
```
Terms: Monotonically increasing logical time units
Roles: Follower, Candidate, Leader

Election:
  1. Follower times out (150–300ms random), becomes Candidate
  2. Increments term, votes for self, sends RequestVote to all
  3. Node votes for first Candidate in term with log ≥ own log
  4. Candidate receiving majority of votes becomes Leader
  5. Leader sends AppendEntries (heartbeats) to maintain authority

Prevents split-brain: Only one leader per term possible (majority required)
```

## 6.8 Distributed Transactions

### Two-Phase Commit (2PC)

```
Phase 1 — Prepare:
  Coordinator → all participants: "PREPARE"
  Participants: write to WAL, lock resources, reply "YES" or "NO"

Phase 2 — Commit/Abort:
  If all YES: Coordinator → all participants: "COMMIT"
  If any NO:  Coordinator → all participants: "ABORT"
  Participants execute and release locks

Failure modes:
  Coordinator crashes after PREPARE, before COMMIT:
    Participants hold locks indefinitely (blocking protocol)
  Network partition after some participants commit:
    Inconsistency until coordinator recovers
```

### Three-Phase Commit (3PC)

Adds a `PreCommit` phase to make 2PC non-blocking. Rarely used in practice due to complexity and still blocking in some partition scenarios.

### Saga Pattern

```
Compensating Transactions:
  Break distributed transaction into local transactions
  Each has a compensating transaction (undo)

  T1 → T2 → T3 → T4
  If T3 fails: execute C2 → C1 (compensations in reverse)

Types:
  Choreography: Services communicate via events, no central coordinator
  Orchestration: Central saga orchestrator calls services and handles failures

Used in: Microservices (impossible to do 2PC across service boundaries)
Trade-off: ACD without I (no isolation between saga steps)
```

### Outbox Pattern

```
Solve the dual-write problem:
  Problem: Cannot atomically write to DB and publish to message queue

Solution:
  1. Write to DB AND write to "outbox" table — same local transaction
  2. Separate poller reads outbox and publishes to message queue
  3. Delete from outbox after successful publish (at-least-once delivery)
  4. Consumer must be idempotent (may receive duplicates)

Debezium implements this via CDC (Change Data Capture) on WAL.
```

---

# 7. Consensus & Coordination

## 7.1 Paxos

**The algorithm that proved distributed consensus is possible.** Proposed by Lamport (1989), published 1998.

```
Roles:
  Proposer:  Proposes values
  Acceptor:  Accepts/rejects proposals (quorum of acceptors needed)
  Learner:   Learns the chosen value

Phase 1a — Prepare:
  Proposer sends Prepare(n) to majority of acceptors
  n is a proposal number, must be unique and increasing

Phase 1b — Promise:
  Acceptor receives Prepare(n)
  If n > max previously promised:
    Promises not to accept proposals < n
    Returns (highest previously accepted proposal, its value)
  Else: ignore or NACK

Phase 2a — Accept:
  Proposer receives majority of promises
  If any acceptor returned a value, proposer MUST use that value
  Else proposer can choose any value
  Sends Accept(n, v) to majority of acceptors

Phase 2b — Accepted:
  Acceptor receives Accept(n, v)
  If n >= promised, accepts it, notifies learners
  Else ignore

Chosen when: majority of acceptors accept same (n, v)
```

**Multi-Paxos:** Run Phase 1 once per leader term, then Phase 2 for each log entry. Reduces round-trips. Basis for most practical consensus implementations.

## 7.2 Raft

Raft is designed to be more understandable than Paxos while providing the same guarantees.

```
Raft Log Structure:
  Index:  1    2    3    4    5    6
  Term:   1    1    2    3    3    3
  Cmd:   set  del  set  set  get  set
          ↑
     committed entries ≤ commit_index
     Leader tracks commit_index and nextIndex[] per follower

Log Replication:
  Leader appends to local log
  Sends AppendEntries(term, prevLogIndex, prevLogTerm, entries, leaderCommit)
  Follower rejects if prevLogIndex/Term don't match (log consistency check)
  After majority ACK: leader commits, applies to state machine
  NextIndex tracked per follower; decremented on rejection (log repair)

Leader Completeness:
  A leader must have all committed entries from previous terms
  Enforced by election restriction: won't vote for candidate with stale log
  stale = candidate's last term < own last term, OR
          same term but shorter log
```

**Raft implementations:**
- etcd (Kubernetes control plane)
- CockroachDB
- TiKV (TiDB)
- Consul
- InfluxDB

## 7.3 Zookeeper & Its Guarantees

ZooKeeper provides a hierarchical namespace of "znodes" with strong consistency:

```
ZAB Protocol (ZooKeeper Atomic Broadcast):
  Not Paxos, not Raft — but provides same guarantees
  
  Leader broadcasts proposals, followers ACK
  Commits when majority ACK
  
  Guarantees:
    Sequential consistency: client operations ordered as submitted
    Atomicity: updates succeed or fail completely
    Single system image: same view regardless of which server
    Reliability: once applied, update persists
    Timeliness: clients see updates within bounded time

ZNode types:
  Persistent:   Survives client disconnect
  Ephemeral:    Deleted when client session ends → used for leader election, service presence
  Sequential:   Auto-incremented suffix → used for distributed queues, barriers
  Container:    Deleted when last child deleted

Watches:
  One-time triggers on znode change
  Used for: service discovery, configuration updates, leader election notification
```

**Typical uses:**
- Leader election (create ephemeral znode, watch predecessor)
- Distributed locks (sequential ephemeral znodes, lock = smallest node)
- Service registry (ephemeral znodes per instance, watch for membership changes)
- Configuration management (watch config znodes)

## 7.4 etcd

etcd is a distributed key-value store using Raft, designed for Kubernetes control plane data:

```
Key features:
  Watch API: Stream changes to keys/prefixes (Kubernetes uses this heavily)
  Leases: TTL-based keys (heartbeat for liveness)
  Transactions: Mini compare-and-swap transactions (atomic operations)
  MVCC: Multi-version concurrency control (revision-based)
  Compaction: Periodic cleanup of old revisions

Kubernetes uses etcd for:
  Pod/Deployment/Service specs
  ConfigMaps and Secrets
  RBAC policies
  Custom Resource Definitions

Performance limits:
  etcd is optimized for consistency, not throughput
  Recommended: <8GB data, <10K nodes, <1K writes/sec
  Large clusters use etcd event watch splitting (separate etcd for events)
```

---

# 8. Storage Systems & Databases

## 8.1 Storage Engine Internals

### B-Tree vs LSM-Tree

```
B-Tree (PostgreSQL, MySQL InnoDB, SQLite):
  Self-balancing tree of pages (typically 4KB–16KB)
  In-place updates — write to page, WAL for durability
  
  Structure:
    Root → Internal nodes (keys + child pointers)
           → Leaf nodes (keys + values or row pointers)
  
  Read:  O(log n) — traverse height of tree
  Write: O(log n) — find page, update in place
  Range: Efficient (leaf pages linked as doubly-linked list)
  
  Problems:
    Write amplification: Update one row → read page, modify, write entire page
    Fragmentation: Pages with holes after deletes
    Random I/O: Updates scatter across pages

LSM-Tree (RocksDB, Cassandra, LevelDB, HBase):
  Log-Structured Merge Tree — append-only writes
  
  Write path:
    1. WAL (Write-Ahead Log) — durability
    2. MemTable (in-memory sorted structure, often skip list)
    3. When MemTable full: flush to SSTable on disk (Level 0)
    4. Background compaction merges SSTables
  
  Read path:
    1. Check MemTable
    2. Check bloom filter per SSTable (avoid disk read if key absent)
    3. Scan SSTables from newest to oldest
  
  SSTable structure:
    - Sorted key-value pairs
    - Data blocks + index block + bloom filter block + footer
    - Immutable once written
  
  Compaction strategies:
    Leveled (LevelDB/RocksDB default): Bounded space, predictable read amplification
    Tiered (Cassandra): Lower write amplification, higher space amplification
    FIFO: For time-series (delete oldest first)
  
  Tradeoffs:
    + Sequential writes (excellent for SSDs/HDDs)
    + High write throughput
    - Read amplification (may check many SSTables)
    - Space amplification (multiple versions of same key)
    - Compaction I/O can compete with foreground I/O
```

### Write-Ahead Log (WAL)

```
WAL ensures durability before acknowledging writes:
  1. Write change to WAL (sequential write, cheap)
  2. Acknowledge to client
  3. Apply to data pages (can be done lazily)
  4. On crash: replay WAL from last checkpoint

WAL modes:
  PostgreSQL WAL: Logical (statement) and physical (page changes)
  MySQL binlog: Statement or row-based replication
  RocksDB WAL: Physical key-value operation log

WAL also enables:
  Replication: Followers replay WAL from leader
  PITR (Point-in-Time Recovery): Replay WAL to any point
  CDC (Change Data Capture): Read WAL to stream changes (Debezium)
```

### MVCC (Multi-Version Concurrency Control)

```
MVCC allows non-blocking reads by maintaining multiple versions:

PostgreSQL:
  Each row has: xmin (created by txn), xmax (deleted by txn), t_cid, t_ctid
  
  Read sees: rows where xmin committed before snapshot, xmax not committed
  Write: creates new row version, marks old as deleted
  
  Snapshot isolation:
    Transaction sees consistent snapshot of DB at start time
    Two concurrent writers: first-committer-wins (no lost updates)
  
  VACUUM:
    Dead row versions accumulate, must be cleaned
    AUTOVACUUM runs periodically
    Transaction ID wraparound: 32-bit TXID wraps at 2^32 (~4B transactions)
    VACUUM FREEZE marks rows with special frozen TXID (always visible)

MySQL InnoDB:
  Uses undo log for old versions
  Purge thread cleans old undo log entries
  Consistent read uses undo log to reconstruct old version
```

## 8.2 Relational Databases Deep Dive

### Query Execution Pipeline

```
SQL Query Lifecycle:
  1. Parser       → Abstract Syntax Tree
  2. Rewriter     → Apply rules (views, permissions)
  3. Planner/Optimizer → Choose execution plan
     - Statistics from pg_statistics (histograms, distinct values)
     - Cost model: seq_page_cost, random_page_cost, cpu_tuple_cost
     - Join algorithms: nested loop, hash join, merge join
     - Scan types: seq scan, index scan, index-only scan, bitmap heap scan
  4. Executor     → Execute chosen plan, return rows

EXPLAIN ANALYZE output:
  Seq Scan on users (cost=0..10000 rows=100000 width=80)
              actual time=0.1..150ms rows=100000 loops=1
  
  cost=startup..total (in "cost units")
  actual time: measured execution time
  rows: estimated vs actual (large discrepancy = bad statistics)
```

### Indexing Deep Dive

```
B-Tree Index (default):
  Supports: =, <, >, <=, >=, BETWEEN, LIKE 'prefix%'
  Does NOT use: LIKE '%suffix', case-insensitive matching

Hash Index:
  Supports: = only
  O(1) lookup, but not range-friendly, not WAL-logged (PostgreSQL pre-10)

GiST (Generalized Search Tree):
  Extensible index for custom types
  Supports: geometric types, full-text search, IP ranges (inet_ops)

GIN (Generalized Inverted Index):
  For composite values (arrays, JSONB, tsvector)
  Each element in array → index entry → list of rows containing it
  Fast lookup: "which rows contain value X?"
  Slow update: must update multiple index entries per row change

BRIN (Block Range Index):
  Tiny index storing min/max per range of pages
  Only useful for naturally ordered data (timestamps in append-only tables)
  Orders of magnitude smaller than B-tree

Partial Index:
  CREATE INDEX ON orders(user_id) WHERE status = 'pending';
  Smaller, faster, only useful for specific queries

Covering Index (Index-Only Scan):
  INCLUDE columns in index to avoid heap access
  CREATE INDEX ON orders(user_id) INCLUDE (created_at, total);
```

### Partitioning

```
Table Partitioning (PostgreSQL):
  Range: CREATE TABLE orders PARTITION BY RANGE (created_at);
  List:  CREATE TABLE orders PARTITION BY LIST (region);
  Hash:  CREATE TABLE orders PARTITION BY HASH (user_id);

Benefits:
  Partition pruning: queries on single partition ignore others
  Parallel query: multiple partitions queried in parallel
  Faster VACUUM: per-partition maintenance
  Archiving: DROP old partition (instant) instead of DELETE

Constraint Exclusion:
  Planner must know query excludes partition
  Always use partitioned column in WHERE clause
```

## 8.3 NoSQL Systems

### Cassandra Architecture

```
Cassandra: Wide-column store, masterless, eventual consistency

Data Model:
  Keyspace → Tables → Partitions → Rows → Columns
  
  PRIMARY KEY (partition_key, clustering_key1, clustering_key2)
  partition_key → consistent hash → which node
  clustering_key → sort order within partition

Write path:
  1. Write to commit log (WAL, sequential)
  2. Write to MemTable (in-memory)
  3. When MemTable full: flush to SSTable
  4. Compaction merges SSTables

Read path:
  1. Check bloom filter (is key in this SSTable?)
  2. Check key cache (partition offset in SSTable)
  3. Read data from SSTable

Consistency levels:
  ONE:        1 replica responds
  QUORUM:     majority of RF responds → read-your-writes if W_QUORUM + R_QUORUM > RF
  ALL:        all replicas respond
  LOCAL_ONE:  1 replica in local DC
  LOCAL_QUORUM: quorum in local DC (for multi-DC deployments)

Replication:
  RF=3 means 3 copies of each partition
  Each next node in ring gets a replica (SimpleStrategy)
  NetworkTopologyStrategy: specify per-DC replica count

Anti-entropy:
  Merkle trees: each node builds tree of hash of its data
  Repair compares trees, syncs differences
  Run repair regularly to fix divergence
```

### MongoDB Architecture

```
Storage engine: WiredTiger (B-tree with compression, MVCC, row-level locking)

Document model: BSON (Binary JSON)
  Nested documents, arrays, polymorphic schema

Replication:
  Replica Set: 1 primary + N secondaries (+ arbiters)
  Oplog: capped collection, secondary replays operations
  Elections: Raft-like (modified with priority, tags)

Sharding:
  Mongos: query router
  Config servers: shard metadata (3 nodes, replica set)
  Shard key: determines which shard holds document
  
  Chunk: contiguous range of shard key values
  Auto-split: chunks split when too large (64MB default)
  Balancer: moves chunks between shards for balance

Aggregation Pipeline:
  $match → $group → $project → $sort → $limit
  Stages processed sequentially
  Optimizer can merge/reorder some stages

Change Streams:
  Watch collection for changes
  Backed by oplog tailing
  At-least-once delivery, resume token for restart
```

### Redis Architecture

```
Redis: In-memory data structure server, optional persistence

Data structures:
  String:  GET/SET/INCR/APPEND — binary-safe, max 512MB
  Hash:    HGET/HSET — dictionary of field-value pairs
  List:    LPUSH/RPOP/LRANGE — doubly-linked list
  Set:     SADD/SMEMBERS/SINTER — unordered unique strings
  Sorted Set: ZADD/ZRANGE — sorted by score, O(log n) operations
  Bitmap:  SETBIT/BITCOUNT — space-efficient bit operations
  HyperLogLog: PFADD/PFCOUNT — probabilistic cardinality estimation (±0.81%)
  Stream:  XADD/XREAD — append-only log (Kafka-like)
  Geo:     GEOADD/GEODIST/GEORADIUS — geospatial index (sorted set + geohash)

Persistence:
  RDB (snapshots): Fork + copy-on-write, periodic bgsave
  AOF (Append-Only File): Log every write command
    fsync: always (safe), everysec (default, 1s data loss), no (OS decides)
  RDB+AOF: Use AOF for recovery (more complete), RDB for faster restarts

Clustering:
  16384 hash slots, sharded across nodes
  Each node handles subset of slots + can redirect clients
  Replica per master (async replication)
  Gossip protocol for cluster membership

Lua scripting:
  EVAL — atomic execution of Lua script
  SCRIPT LOAD / EVALSHA — load script, reference by SHA1
  Critical for: rate limiting, distributed locks (Redlock)

Pub/Sub:
  PUBLISH channel message
  SUBSCRIBE channel
  No persistence, no acknowledgment — fire and forget
  Use Streams for persistent pub/sub

Transactions:
  MULTI/EXEC — queue commands, execute atomically
  No rollback on error — optimistic, all-or-nothing execution
  WATCH key — optimistic locking (abort if key changed during MULTI)
```

## 8.4 Time-Series Databases

```
Time-series data characteristics:
  - Append-only (rarely update historical data)
  - High write throughput (millions of data points/sec)
  - Queries are range-based (last hour, last day)
  - Aggregation-heavy (avg, sum, percentile, rate)
  - Data expires (old data deleted or downsampled)

InfluxDB:
  TSM (Time-Structured Merge) storage — LSM variant optimized for time-series
  Line protocol: measurement,tag_key=tag_val field_key=field_val timestamp
  Series = measurement + tag set
  Shards: time-based partitioning (6h for hot data, 7 days for cold)
  Continuous Queries / Tasks: automatic downsampling
  Flux query language

Prometheus:
  Pull-based metrics collection (scrapes targets every 15s)
  Storage: custom TSDB (chunk-based, gorilla compression)
  Data model: metric_name{label=value,...} → (timestamp, float64)
  PromQL: functional query language
  Remote write/read for long-term storage (Thanos, Cortex, VictoriaMetrics)
  
  Gorilla compression (Facebook):
    XOR of consecutive float64 values (changes are small)
    Delta-of-delta for timestamps (periodic scrape = constant delta)
    Typical compression: 1.37 bytes per sample (vs 16 bytes naive)

ClickHouse:
  Column-oriented OLAP database
  MergeTree engine: LSM-like, parts merged in background
  Supports SQL, extremely fast for analytical queries
  Used for: access logs, event analytics, time-series analytics
```

## 8.5 Database Replication Topologies

```
Single Primary (Master-Slave):
  + Simple, strong consistency for writes
  - Write bottleneck, failover requires promotion

Multi-Primary (Master-Master):
  + Write anywhere, geographic distribution
  - Conflict resolution (last-write-wins, CRDTs, business logic)
  Used: Galera (MySQL), CockroachDB, Spanner

Chain Replication:
  Primary → Replica1 → Replica2 → ... → Tail
  Write: always to primary, propagates chain
  Read: always from tail (committed = at tail)
  Strongly consistent reads, good throughput
  Used in: Microsoft Azure Storage, Riak Enterprise

Leaderless (Dynamo-style):
  Any node can accept write (with sloppy quorum)
  W + R > N for strong consistency
  Conflict detection via vector clocks
  Last-write-wins or application-level resolution
  Used in: Cassandra, Riak, DynamoDB
```

---

# 9. Messaging & Event Streaming

## 9.1 Message Queue Concepts

```
Producer → [Queue] → Consumer

Delivery semantics:
  At-most-once:  Producer sends, no retry. Consumer may miss messages.
                 Use when: Loss acceptable (metrics, logs)
  At-least-once: Producer retries until ACK. Consumer may get duplicates.
                 Use when: Loss unacceptable, consumer is idempotent
  Exactly-once:  Idempotent producer + transactional consumer.
                 Expensive. Use when: Financial transactions, critical state changes

Message ordering:
  No ordering:    Simplest, highest throughput
  Partition ordering: Messages in same partition are ordered (Kafka)
  Global ordering: All messages ordered — throughput bottleneck (single queue)
```

## 9.2 Apache Kafka Deep Dive

```
Kafka Architecture:
  Topic: named stream of records
  Partition: ordered, immutable sequence of records within topic
  Broker: Kafka server, stores partitions
  Consumer Group: set of consumers that collectively consume topic
  Offset: position of consumer in partition

Partition Replication:
  Each partition has 1 leader + N-1 followers (ISR: In-Sync Replicas)
  Leader handles all reads and writes
  Followers replicate from leader
  If leader fails, a follower in ISR is elected leader

Producer:
  acks=0: fire and forget
  acks=1: leader ACKs (may lose if leader crashes before replication)
  acks=all: all ISR replicas ACK (strongest durability)
  
  Idempotent producer: producer.id + sequence number → dedup at broker
  Transactions: spans multiple partitions atomically

Consumer:
  Pull model (not push)
  Commits offset after processing
  Auto-commit: risky (can lose messages if process crashes after commit but before processing)
  Manual commit after processing: at-least-once delivery
  
  Consumer lag: difference between latest offset and consumer's offset
  Measure with: kafka-consumer-groups.sh --describe

Storage:
  Log segments: files on disk, retained by time or size
  Log compaction: keep only latest value per key (for CDC/state topics)
  
  Write path:
    Producers write to leader's page cache
    OS flushes to disk (not fsync per message — batched)
    Zero-copy: sendfile() syscall, no userspace copy

Exactly-once semantics (EOS):
  1. Idempotent producer (handles retries)
  2. Transactional API (atomic produce across partitions)
  3. Consumer: read_committed isolation (only sees committed txns)
  
  Kafka Streams uses EOS for stateful processing

KRaft (Kafka without Zookeeper):
  Kafka 3.x+ uses internal Raft-based metadata quorum
  Controller quorum replaces ZooKeeper
  Simpler operations, fewer moving parts
```

## 9.3 RabbitMQ Architecture

```
AMQP Model:
  Exchange → (Routing) → Queue → Consumer

Exchange types:
  Direct:  Route by exact routing key match
  Topic:   Route by routing key pattern (words.# or words.*.specific)
  Fanout:  Broadcast to all bound queues
  Headers: Route by message headers (key-value match)

Reliability:
  Publisher confirms: broker ACKs after persistence
  Consumer ACK: manual ACK after processing
  Dead Letter Exchange: messages that fail (nack'd, expired, queue full)
  
Queue types:
  Classic: Traditional, mature
  Quorum: Raft-based, replicated, durable (recommended for production)
  Stream: Append-only log (like Kafka), multiple consumers, offset-based

When to use RabbitMQ vs Kafka:
  RabbitMQ: complex routing, message prioritization, RPC patterns, short retention
  Kafka: event log, stream processing, high throughput, long retention, replay
```

## 9.4 Event-Driven Architecture Patterns

```
Event Sourcing:
  Store state changes as sequence of events (not current state)
  State = replay of all events
  
  Benefits:
    Complete audit trail
    Time travel (replay to any point)
    Multiple projections from same events
    Event replay for new features
  
  Challenges:
    Event schema evolution (never delete old event types)
    Snapshot needed for long-lived aggregates
    Eventual consistency of projections
    Event versioning complexity

CQRS (Command Query Responsibility Segregation):
  Separate read and write models
  
  Write side: Command → Handler → Event → Event Store
  Read side:  Event → Projection → Read Model → Query
  
  Read model: denormalized, optimized for specific queries
  Usually combined with Event Sourcing
  
  Benefits: Independently scale reads and writes
  Challenges: Eventual consistency between write and read models

Choreography vs Orchestration:
  Choreography:
    Services emit events, subscribe to others' events
    No central coordinator
    Pros: decoupled, resilient
    Cons: hard to track flow, distributed logic
  
  Orchestration:
    Central orchestrator calls services (Temporal, AWS Step Functions)
    Pros: visible workflow, easier error handling
    Cons: coupling to orchestrator, single point of complexity
```

---

# 10. Caching Architecture

## 10.1 Cache Fundamentals

```
Cache hit ratio: hits / (hits + misses)
Latency impact: avg_latency = hit_ratio × cache_latency + miss_ratio × source_latency

Cache eviction policies:
  LRU (Least Recently Used): Evict oldest accessed. Most common.
  LFU (Least Frequently Used): Evict least accessed. Better for skewed access.
  ARC (Adaptive Replacement Cache): Adapts between LRU and LFU. ZFS uses this.
  TinyLFU (Caffeine): Frequency-based with admission filter. Excellent hit rate.
  CLOCK: Approximation of LRU with O(1) operations.
  Random: Surprisingly competitive, used in CPU TLBs.
```

## 10.2 Cache Patterns

```
Cache-Aside (Lazy Loading):
  Application:
    1. Read from cache
    2. On miss: read from DB, write to cache, return
    3. Write: write to DB, invalidate/update cache
  
  Pros: Only cache what's requested, cache failure not catastrophic
  Cons: Cache miss cold start, stale data if invalidation fails

Read-Through:
  Cache itself fetches from DB on miss
  Application talks only to cache
  Pros: Simpler application logic
  Cons: Cache is now critical path

Write-Through:
  Write to cache AND DB synchronously
  Pros: Cache always consistent
  Cons: Write latency, cache filled with infrequently read data

Write-Back (Write-Behind):
  Write to cache only, async persist to DB
  Pros: Very low write latency
  Cons: Data loss risk if cache crashes before flush

Refresh-Ahead:
  Proactively refresh cache before TTL expires
  Pros: No miss latency for hot keys
  Cons: Predicting which keys will be accessed

Cache warming:
  Pre-populate cache before traffic hits (avoid cold-start thundering herd)
  Critical for deployments and failovers
```

## 10.3 Cache Invalidation Strategies

```
TTL-based: Simple, eventual consistency. Risk: stale data.
Event-driven: DB event → invalidate cache. Risk: race conditions.
Write-through: Consistent, higher write latency.
Versioning: Cache key includes version/ETag. Old versions expire naturally.

Cache Stampede (Thundering Herd) Prevention:
  Problem: Key expires, N simultaneous requests all miss, all hit DB
  
  Solutions:
    1. Mutex: First request fetches, others wait (probabilistic early expiry)
    2. Probabilistic Early Expiry: Randomly re-fetch before TTL
       fetch_early if: -current_ttl < β × δ × log(rand())
    3. Cache Lock: Set a lock key, only holder fetches, others return stale
    4. Background Refresh: Return stale + schedule async refresh
```

## 10.4 CDN Architecture

```
CDN (Content Delivery Network):
  Edge nodes geographically distributed (PoP — Point of Presence)
  User request → nearest edge → cache check → origin if miss
  
  Pull CDN: Caches on first request, TTL-based expiry
  Push CDN: Pre-populated by operator (good for predictable content)
  
  Cache behavior controlled by headers:
    Cache-Control: max-age=3600, public, s-maxage=86400
    Vary: Accept-Encoding, Accept-Language (separate cache per variant)
    ETag: fingerprint for conditional GET
    Last-Modified: timestamp-based conditional GET
    Surrogate-Control: CDN-specific directives (Fastly, Akamai)
  
  Origin Shield:
    Additional cache tier between edge and origin
    Collapses requests from multiple edge nodes
    Protects origin from cache stampedes
  
  CDN Providers:
    Cloudflare: anycast network, WAF included, DDoS mitigation
    Fastly: real-time purging, VCL configuration, edge compute
    Akamai: largest footprint, enterprise SLAs
    AWS CloudFront: deep AWS integration, Lambda@Edge
    GCP Cloud CDN: Media CDN for streaming
```

---

# 11. Load Balancing & Traffic Management

## 11.1 Load Balancing Algorithms

```
Round Robin:
  Request 1 → Server A
  Request 2 → Server B
  Request 3 → Server C
  Works when: Requests are homogeneous, servers identical

Weighted Round Robin:
  Server A weight=3, Server B weight=1
  AAAB AAAB AAAB...
  Works when: Servers have different capacity

Least Connections:
  Route to server with fewest active connections
  Better than RR for variable-length requests (long-polling, websockets)

Least Response Time:
  Route to server with lowest avg response time AND fewest connections
  Requires health check latency tracking

IP Hash (Source Affinity):
  hash(client_IP) → server
  Same client always goes to same server (session persistence)
  Problem: uneven distribution if few IPs (NAT, proxy)

Random Two Choices (Power of Two):
  Pick 2 random servers, route to least loaded
  Better distribution than pure random, lower coordination than global least-conn

Consistent Hashing:
  Route by hash of request attribute (user_id, session_id)
  Minimizes remapping when servers added/removed
  Used by: Envoy, Nginx upstream hashing
```

## 11.2 Layer 4 vs Layer 7 Load Balancing

```
Layer 4 (Transport):
  Operates on TCP/UDP (IP + port)
  Forwards packets/segments without inspecting content
  Lower latency, higher throughput
  Limited routing capability (no URL-based routing, no sticky by cookie)
  Examples: AWS NLB, LVS (Linux Virtual Server), hardware F5

Layer 7 (Application):
  Inspects HTTP headers, URLs, body
  Can route by URL path (/api vs /static)
  Can terminate TLS (offload from backend)
  Can insert headers (X-Forwarded-For)
  Can do rate limiting, authentication
  Higher latency (full packet inspection), lower throughput
  Examples: Nginx, HAProxy, Envoy, AWS ALB, Traefik
```

## 11.3 Health Checks

```
Active health checks:
  Load balancer probes backends periodically
  TCP connect, HTTP GET, custom script
  Configurable: interval, timeout, threshold (healthy/unhealthy)

Passive health checks (circuit breaker):
  Monitor actual traffic success/error rates
  Remove backend after N consecutive errors
  Return after cooldown period

Health check types:
  Shallow: Is the port open? (basic liveness)
  Deep: Can it serve requests? (query DB, check dependencies)
  Application-specific: Custom logic (/healthz endpoint with status)

Kubernetes probes:
  livenessProbe:  Is container alive? Failure → restart container
  readinessProbe: Is container ready? Failure → remove from Service endpoints
  startupProbe:   Has container started? Prevents liveness killing slow-start apps
```

## 11.4 Circuit Breaker Pattern

```
States:
  CLOSED (normal): Requests pass through. Track failure rate.
  OPEN (tripped):  Requests immediately fail. No backend calls.
  HALF-OPEN:       Allow limited requests to test recovery.

Transition rules:
  CLOSED → OPEN:      Failure rate exceeds threshold (e.g., 50% in 10s window)
  OPEN → HALF-OPEN:   After timeout (e.g., 30s)
  HALF-OPEN → CLOSED: Success rate in probe window is sufficient
  HALF-OPEN → OPEN:   Probe requests fail

Configuration (Hystrix/Resilience4j):
  slidingWindowSize: 10 requests or 10 seconds
  failureRateThreshold: 50%
  waitDurationInOpenState: 60s
  permittedCallsInHalfOpenState: 10
  slowCallRateThreshold: 80% (calls > slowCallDurationThreshold treated as failures)
  slowCallDurationThreshold: 2s
```

---

# 12. Microservices & Service Mesh

## 12.1 Microservices Design Principles

```
Service boundaries (Domain-Driven Design):
  Bounded Context: Each service owns its domain model
  Aggregate: Consistency boundary within a service
  
  Wrong split: Split by technical layer (all "user" code in one service)
  Right split:  Split by business capability (orders, inventory, payments)

The strangler pattern (migrating monolith):
  1. Introduce a facade/proxy in front of monolith
  2. Incrementally route traffic to new microservices
  3. Strangle the monolith piece by piece
  Never do big-bang rewrites.

API contracts:
  Services communicate via stable, versioned APIs
  Consumer-driven contract testing (Pact): consumer defines expectations,
  provider validates they're met
  Backward compatibility: never remove fields, only add (with defaults)

Twelve-Factor App (Heroku, 2011):
  1.  Codebase: One codebase, many deploys
  2.  Dependencies: Explicitly declare and isolate
  3.  Config: Store in environment variables
  4.  Backing services: Treat as attached resources
  5.  Build/release/run: Strictly separate stages
  6.  Processes: Execute as stateless processes
  7.  Port binding: Export services via port binding
  8.  Concurrency: Scale via process model
  9.  Disposability: Fast startup, graceful shutdown
  10. Dev/prod parity: Keep environments as similar as possible
  11. Logs: Treat as event streams
  12. Admin processes: Run admin tasks as one-off processes
```

## 12.2 Service Mesh Architecture

```
Service Mesh solves:
  Mutual TLS between services (without code changes)
  Distributed tracing (without code changes)
  Retries, timeouts, circuit breaking (without code changes)
  Traffic splitting (canary, blue-green)
  Rate limiting (per-service)
  Observability (metrics, logs, traces)

Sidecar Pattern:
  Every service pod gets a sidecar proxy container
  All traffic flows through sidecar
  Data plane: Envoy proxies handle traffic
  Control plane: Istiod distributes configuration

Istio Architecture:
  Istiod (control plane):
    Pilot: Service discovery, traffic management config
    Citadel: Certificate management (mTLS)
    Galley: Config validation
  
  Data plane: Envoy sidecar per pod
  
  Traffic flow:
    Client pod → Envoy sidecar → iptables intercept
    → outbound Envoy → mTLS → inbound Envoy
    → iptables → server pod
  
  iptables interception (init container sets rules):
    All outbound traffic → port 15001 (Envoy)
    All inbound traffic → port 15006 (Envoy)
    Envoy itself → excluded from redirect (so it can reach actual destination)

Envoy key concepts:
  Listener:    Port that Envoy listens on
  Route:       URL path → cluster mapping
  Cluster:     Group of upstream endpoints
  Endpoint:    Individual upstream server
  Filter chain: Ordered list of filters per listener
                (HTTP filter, rate limit, auth, gzip)

  xDS API (discovery service):
    LDS: Listener Discovery Service
    RDS: Route Discovery Service
    CDS: Cluster Discovery Service
    EDS: Endpoint Discovery Service
    SDS: Secret Discovery Service (certs)
    ADS: Aggregated Discovery Service (combines above)
```

## 12.3 Inter-Service Communication

```
Synchronous:
  REST: Human-readable, tooling-friendly, stateless, HTTP overhead
  gRPC: Protocol buffers, HTTP/2 streaming, strongly typed, code generation
  GraphQL: Client-driven queries, reduces over-fetching, complex caching

Asynchronous:
  Message queue: Fire-and-forget, decoupled, durable
  Event bus: Broadcast, fan-out, pub/sub
  
Choose sync when: Need immediate response, request-reply pattern
Choose async when: Long-running operations, fan-out, decoupling required

gRPC patterns:
  Unary: Single request, single response (like REST)
  Server streaming: Single request, stream of responses
  Client streaming: Stream of requests, single response
  Bidirectional streaming: Both sides stream simultaneously
  
  Deadlines: ALWAYS set deadlines. gRPC context propagates deadline.
  Interceptors: Server/client-side middleware (auth, logging, tracing)
```

---

# 13. Container Internals & Orchestration

## 13.1 Container Runtime Internals

```
Container ≠ VM
Container = isolated process group using:
  namespaces (isolation)
  cgroups (resource limits)
  seccomp (syscall filtering)
  capabilities (privilege reduction)
  overlay filesystem (layered image)

Container runtime stack:
  High-level: Docker, containerd, CRI-O
  Low-level:  runc (OCI runtime), kata-containers, gvisor

OCI (Open Container Initiative):
  Image spec: Layer format, manifest, config
  Runtime spec: How to execute container from image
  Distribution spec: Registry HTTP API

runc:
  Reference OCI runtime implementation
  Written in Go
  Calls clone() with namespace flags
  Sets up cgroups, capabilities, seccomp
  Executes container init process

kata-containers:
  Runs each container in a lightweight VM (QEMU/firecracker)
  Hardware isolation + container experience
  Slower startup (~100ms vs 1ms for runc)
  Used for untrusted workloads, multi-tenant environments

gVisor (Google):
  User-space kernel (Go)
  Intercepts syscalls before reaching host kernel
  Not a VM — uses ptrace or KVM-based interception
  Smaller attack surface, but not zero (gVisor kernel bugs)
  Used in: Google Cloud Run, some GKE configurations
```

## 13.2 Container Image Internals

```
OCI Image = Manifest + Config + Layers

Layer (UnionFS / OverlayFS):
  Lower layers: read-only base images
  Upper layer: read-write container layer
  
  OverlayFS merge:
    lowerdir: base image layers (stacked)
    upperdir: container-specific changes
    workdir:  temporary work directory
    merged:   unified view presented to container
  
  Copy-on-write: reading from lower layer is cheap (no copy)
                 writing copies file to upper layer first

  Layer cache:
    Layers are content-addressed (SHA256 of content)
    Pulled once, reused by multiple containers
    This is why "put COPY package.json first" matters in Dockerfiles

Image manifest:
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": { "digest": "sha256:...", "size": 1234 },
  "layers": [
    { "digest": "sha256:...", "size": 5678 },
    { "digest": "sha256:...", "size": 9012 }
  ]
}

Multi-arch images (manifest list):
  index.json points to per-arch manifests
  Docker pull selects correct arch automatically
  buildx: cross-platform builds with QEMU emulation or native builders
```

## 13.3 Kubernetes Architecture

```
Control Plane:
+----------------------------------------------------------+
| kube-apiserver   — REST API, authentication, authorization|
|                    All state stored in etcd               |
| etcd             — Distributed key-value store            |
|                    All cluster state                      |
| kube-scheduler   — Assign pods to nodes                  |
|                    Filtering + scoring                    |
| kube-controller-manager — Control loops                  |
|   ReplicaSet, Deployment, Node, Endpoints, etc.          |
| cloud-controller-manager — Cloud-specific controllers    |
|   LoadBalancer, Volume, Node lifecycle                   |
+----------------------------------------------------------+

Node Components:
+----------------------------------------------------------+
| kubelet          — Node agent, reconciles pod spec        |
|                    Manages container lifecycle            |
| kube-proxy       — Service networking (iptables/ipvs)    |
| container runtime — containerd, CRI-O                    |
+----------------------------------------------------------+
```

### Kubernetes API Mechanics

```
Every Kubernetes object:
  apiVersion, kind, metadata, spec, status

API server:
  Authentication → Authorization (RBAC) → Admission (Webhooks) → Persistence (etcd)

Informers (Watch mechanism):
  Components watch API server for changes
  List-Watch: initial list + streaming watch from resourceVersion
  Local cache (store) + event handlers (add/update/delete)
  This is how controllers work — react to state changes

Reconciliation Loop:
  Desired state (spec) vs Actual state (status)
  Controller continuously reconciles: make actual = desired
  Idempotent — running reconciler multiple times is safe
  Level-triggered (not edge-triggered): always reconcile current diff

Admission Controllers:
  Mutating webhooks: can modify objects before persistence
  Validating webhooks: can reject objects
  Built-in: ResourceQuota, LimitRanger, PodSecurity, NodeRestriction
```

### Kubernetes Scheduling

```
Scheduler phases:
  1. Filtering (predicates):
     NodeSelector, NodeAffinity, Taints/Tolerations, ResourceFit,
     PodAffinity/AntiAffinity, VolumeFit, etc.
  
  2. Scoring (priorities):
     LeastRequestedPriority (spread load)
     BalancedResourceAllocation (balance CPU/memory ratio)
     NodeAffinityPriority (prefer matching nodes)
     InterPodAffinityPriority (prefer/avoid co-location)

  3. Binding: Write nodeName to pod spec

Pod Quality of Service:
  Guaranteed: requests == limits (CPU and memory)
  Burstable:  requests < limits (or only limits set)
  BestEffort: no requests or limits set

QoS determines OOM kill order:
  BestEffort → Burstable → Guaranteed (last resort)

Node affinity:
  requiredDuringSchedulingIgnoredDuringExecution: hard requirement (filter)
  preferredDuringSchedulingIgnoredDuringExecution: soft requirement (score)

Taints and Tolerations:
  Taint on node: "dedicated=gpu:NoSchedule"
  Toleration on pod: allows scheduling on tainted node
  Effects: NoSchedule, PreferNoSchedule, NoExecute (evict existing pods)

Pod Disruption Budget (PDB):
  minAvailable: 2 — at least 2 pods must be available during disruption
  maxUnavailable: 1 — at most 1 pod can be unavailable
  Used by: cluster autoscaler, drain, rolling update
```

### Kubernetes Networking Model

```
Requirements (Kubernetes networking model):
  1. Every pod gets its own IP
  2. All pods can communicate without NAT
  3. All nodes can communicate with all pods without NAT
  4. Pod IP is same inside and outside (no SNAT)

Service types:
  ClusterIP:    Virtual IP accessible only within cluster
  NodePort:     Expose on each node's IP at static port
  LoadBalancer: External load balancer (cloud provider)
  ExternalName: DNS CNAME to external service
  Headless:     No VIP, DNS returns pod IPs directly (StatefulSet)

kube-proxy modes:
  iptables: Rules for each Service+Endpoint. O(n) chain traversal.
  IPVS:     Kernel-level load balancing, O(1) lookup (hash table).
            Supports more LB algorithms.
  eBPF:     Cilium replaces kube-proxy with eBPF (no iptables at all)

DNS in Kubernetes:
  CoreDNS: In-cluster DNS server
  Service: my-svc.my-namespace.svc.cluster.local
  Pod:     pod-ip.my-namespace.pod.cluster.local
  
  ndots:5 default: short names trigger 5 search domain attempts
  Performance optimization: use FQDNs in pods to avoid search probing

CNI (Container Network Interface):
  Plugin sets up pod network namespace
  Assigns IP, creates veth pair, connects to node network
  
  Flannel:  Simple overlay (VXLAN). No network policy.
  Calico:   BGP-based (no overlay), network policy, eBPF mode
  Cilium:   eBPF-native, network policy, service mesh capabilities
  Weave:    Overlay with encryption option
  Multus:   Multiple CNI plugins per pod (for SR-IOV, DPDK workloads)
```

## 13.4 Kubernetes Storage

```
PersistentVolume (PV): Cluster-level storage resource
PersistentVolumeClaim (PVC): Pod's request for storage
StorageClass: Dynamic provisioning template

Access modes:
  ReadWriteOnce (RWO):    Single node read-write
  ReadOnlyMany (ROX):     Multiple nodes read-only
  ReadWriteMany (RWX):    Multiple nodes read-write (NFS, CephFS, EFS)
  ReadWriteOncePod:       Single pod read-write (Kubernetes 1.22+)

CSI (Container Storage Interface):
  Standard API between Kubernetes and storage systems
  Plugins: AWS EBS CSI, GCE PD CSI, Ceph CSI, Longhorn, OpenEBS
  Capabilities: snapshots, cloning, volume expansion, topology

StatefulSets + Storage:
  Stable network identity: pod-name-0, pod-name-1
  Ordered deployment and scaling
  VolumeClaimTemplates: per-pod PVCs
  PVCs NOT deleted when StatefulSet is deleted
```

---

# 14. Cloud Native Architecture

## 14.1 Cloud Native Principles

```
Cloud native = designed to run ON cloud infrastructure, not just IN it

CNCF (Cloud Native Computing Foundation) definition:
  - Containerized applications
  - Dynamically orchestrated
  - Microservices-oriented
  - Designed for resilience, agility, observability

The immutable infrastructure principle:
  Never patch running servers.
  Replace with new image.
  GitOps: source of truth in Git, cluster reconciles to match.
```

## 14.2 GitOps

```
GitOps principles (Weaveworks, 2017):
  1. Declarative: Desired state described declaratively
  2. Versioned: Git is the single source of truth
  3. Pulled automatically: Agents pull desired state
  4. Continuously reconciled: Software agents ensure actual state matches desired

Pull vs Push models:
  Push (traditional CI/CD): Pipeline pushes to cluster
    Problem: Pipeline needs cluster credentials, no audit trail
  
  Pull (GitOps): Agent in cluster pulls from Git
    Benefit: Credentials stay in cluster, Git is audit trail

Argo CD:
  Watches Git repositories
  Compares live cluster state vs desired Git state
  Syncs (applies) differences
  Supports Helm, Kustomize, Ksonnet, plain YAML
  Web UI with application health visualization

Flux CD:
  Kubernetes-native GitOps operator
  Source controller: watches Git, Helm repos, OCI registries
  Kustomize controller: applies Kustomize overlays
  Helm controller: manages Helm releases
  Notification controller: webhooks, alerts
  Image automation: automatically update image tags in Git
```

## 14.3 Service Discovery

```
DNS-based (Kubernetes):
  Services get DNS names
  CoreDNS resolves to ClusterIP
  No client-side LB awareness
  Works for any HTTP/TCP client

Client-side service discovery:
  Client queries service registry
  Client selects endpoint (load balances itself)
  Examples: Netflix Eureka + Ribbon, Consul + Envoy
  
  Pros: No extra hop, full LB control
  Cons: Client must implement discovery logic

Server-side service discovery:
  Load balancer queries registry, routes request
  Client knows only LB endpoint
  Examples: AWS ELB + Route53, Nginx with Consul template

Consul:
  Service catalog: register/deregister services with health checks
  KV store: distributed configuration
  Connect: service mesh (mTLS, intentions)
  DNS interface: service.consul DNS queries
  
  Health check types:
    HTTP: GET /health → 200
    TCP: connect to port
    Script: arbitrary script exit code
    gRPC: health check protocol
    TTL: service pushes heartbeat to Consul
```

## 14.4 Serverless Architecture

```
FaaS (Function as a Service):
  Event → Function → Response
  No server management
  Pay per invocation (+ duration)
  
  Cold start: Function code loaded, runtime initialized
              First request latency: 100ms–10s (JVM worst)
              Mitigations: Provisioned concurrency, keep-warm pings, smaller packages

AWS Lambda execution model:
  Execution environment (sandbox) = MicroVM (Firecracker)
  Container reuse: environment persists after function returns
  (global variables, /tmp persist between invocations — use carefully)
  
  Concurrency: Each simultaneous invocation = separate environment
  Reserved concurrency: Hard limit per function
  Provisioned concurrency: Pre-warmed environments (no cold start)

Lambda limitations:
  Timeout: max 15 minutes
  Memory: max 10GB
  /tmp storage: 512MB–10GB (ephemeral)
  Package size: 50MB zipped, 250MB unzipped, 10GB container image

Serverless anti-patterns:
  Long-running processes (use ECS/EKS)
  Heavy stateful operations (externalize to DB)
  Tight latency requirements (cold starts)
  Complex monolith in one function (defeats the purpose)
```

## 14.5 Event-Driven Cloud Patterns

```
AWS EventBridge:
  Event bus: route events between services
  Rules: filter events by pattern → route to targets
  Schema registry: document event structures
  Event archive and replay

AWS SNS + SQS (fan-out pattern):
  SNS topic → multiple SQS queues
  Enables fan-out while providing durable, independent consumption per consumer
  SQS FIFO: ordered, exactly-once (within message group)
  SQS Standard: at-least-once, best-effort ordering

Choreography via events:
  Order placed → OrderCreated event
  → Payment service: charge card
  → Inventory service: reserve stock
  → Notification service: send email
  Each service is independent, no direct coupling
```

---

# 15. Cloud Platforms Deep Dive

## 15.1 AWS Core Services

### Compute

```
EC2 (Elastic Compute Cloud):
  Instance types:
    General purpose:    t3/t4g (burstable), m5/m6i (balanced)
    Compute optimized:  c5/c6i (high CPU, web servers, batch)
    Memory optimized:   r5/r6i (large RAM, in-memory DBs, analytics)
    Storage optimized:  i3/i4i (NVMe SSDs, high IOPS, databases)
    Accelerated:        p3/p4 (GPU, ML), inf1 (Inferentia, inference)
  
  Placement groups:
    Cluster: same AZ, same rack, low latency, high bandwidth
    Partition: separate partitions, different racks, fault isolation
    Spread: one instance per rack, max AZ isolation
  
  EBS (Elastic Block Store):
    gp3: 16,000 IOPS, 1,000 MB/s, general purpose
    io2 Block Express: 256,000 IOPS, 4,000 MB/s, mission-critical DBs
    st1: sequential throughput (big data, logs)
    sc1: cold storage (infrequent access)
    
    Multi-Attach: io1/io2 can attach to multiple instances (cluster filesystems)
  
  Instance store: NVMe directly on host, very fast, ephemeral (lost on stop)
  
  Nitro system:
    AWS's hypervisor replacement
    Offloads VPC networking and EBS to dedicated hardware (Nitro cards)
    Near bare-metal performance
    Nitro Enclaves: isolated compute for sensitive data processing
```

### Networking

```
VPC (Virtual Private Cloud):
  Isolated network in AWS cloud
  CIDR block: 10.0.0.0/16 (65,536 addresses)
  
  Subnets:
    Public subnet:  has internet gateway route, EC2s can get public IPs
    Private subnet: no internet gateway, NAT gateway for outbound only
    
  Internet Gateway: VPC → internet (2-way)
  NAT Gateway:      Private subnet → internet (outbound only, stateful)
  Egress-only IGW:  IPv6 outbound only
  
  Route tables: per-subnet routing rules
  NACLs: stateless subnet-level firewall (inbound + outbound rules)
  Security Groups: stateful instance-level firewall (return traffic allowed)
  
  VPC Peering: Connect two VPCs (not transitive)
  Transit Gateway: Hub-and-spoke VPC connectivity (transitive)
  PrivateLink: Expose service via VPC endpoint (no internet traversal)
  
  VPN and Direct Connect:
    Site-to-Site VPN: IPSec over internet to on-prem
    Direct Connect: Dedicated fiber to AWS (lower latency, higher bandwidth)
    Direct Connect + VPN: Encrypted dedicated connection

Route 53:
  DNS service with health checking and routing policies:
    Simple:           One record, no health checks
    Weighted:         Percentage split (canary, A/B testing)
    Latency-based:    Route to lowest latency region
    Failover:         Primary + standby with health check
    Geolocation:      Route by user location (compliance)
    Geoproximity:     Route by distance to resources (with bias)
    Multi-value:      Return multiple healthy records (basic LB)

CloudFront:
  CDN with 450+ PoPs globally
  Behaviors: path-based routing to different origins
  Functions: lightweight JS at edge (< 1ms)
  Lambda@Edge: Node.js/Python at edge (heavier, regional)
  Origin Shield: Consolidated cache tier
  WAF integration for DDoS and attack protection
```

### Storage

```
S3 (Simple Storage Service):
  Object storage: key → value (object + metadata)
  11 nines durability (replicated across 3+ AZs)
  
  Storage classes:
    Standard:           Frequent access, lowest latency
    Intelligent-Tiering: Auto-move between tiers based on access
    Standard-IA:        Infrequent access (retrieval fee)
    One Zone-IA:        Single AZ, 20% cheaper
    Glacier Instant:    Archive, ms retrieval
    Glacier Flexible:   Archive, minutes–hours retrieval
    Glacier Deep:       Cheapest, 12–48h retrieval
  
  Features:
    Versioning: Keep all versions of objects
    Lifecycle rules: Transition/expire objects automatically
    Replication: Cross-region or same-region replication
    Event notifications: S3 → SNS/SQS/Lambda on object events
    Object Lock: WORM (Write Once Read Many) for compliance
    Server-side encryption: SSE-S3 (AES-256), SSE-KMS, SSE-C (customer keys)
    Presigned URLs: Temporary access without credentials
    S3 Select: SQL query on individual objects (CSV/JSON/Parquet)
    Mountpoint: FUSE driver to mount S3 as filesystem
```

## 15.2 GCP Core Architecture

```
Google Cloud distinguishing features:
  Andromeda: Software-defined networking (SDN) — entire network is software
  Jupiter: Petabit-scale datacenter network fabric
  Global VPC: Single VPC spans all regions (vs AWS regional VPCs)
  
  Premium vs Standard networking tier:
    Premium: Traffic on Google's backbone (better latency/reliability)
    Standard: Traffic on public internet (cheaper)
  
  Cloud Spanner:
    Globally distributed SQL database
    Horizontally scalable (add Spanner nodes)
    Externally consistent (linearizable) using TrueTime
    99.999% availability SLA
    ~5ms latency regional, ~10ms multi-region
    Used by: Google Fi, Snap, Deutsche Bank
  
  BigQuery:
    Serverless OLAP (no cluster to manage)
    Columnar storage (Capacitor format, Parquet-like)
    Distributed query execution (Dremel engine)
    Petabyte-scale, seconds to query billions of rows
    Storage + compute separated (pay per query or flat-rate)
    Streaming inserts for near-real-time data
  
  GKE Autopilot:
    Fully managed Kubernetes (no node management)
    Pay per pod resource request (not per node)
    Hardened by default (no SSH, restricted syscalls)
    Workload Identity: pods get GSA permissions without keys
```

## 15.3 Azure Core Architecture

```
Azure Resource Manager (ARM):
  Consistent management layer for all Azure resources
  Templates: JSON-based IaC (now Bicep — domain-specific language)
  Resource groups: logical container for related resources
  RBAC scoped to subscription, resource group, or resource
  
  Management groups → Subscriptions → Resource groups → Resources
  
Azure AD (Entra ID):
  Identity platform for Azure, Microsoft 365, SaaS apps
  Tenant: Azure AD instance (company directory)
  Service Principal: app identity (like AWS IAM role for applications)
  Managed Identity: automatic SP for Azure resources (no key management)
  
  App registrations → Enterprise applications
  OAuth 2.0 / OIDC for modern auth
  Conditional Access: MFA, device compliance, location-based

Azure networking:
  ExpressRoute: Dedicated connectivity (like AWS Direct Connect)
  Virtual WAN: Managed hub-and-spoke networking
  Front Door: Global load balancer + CDN + WAF
  Private Endpoint: PrivateLink equivalent
  Azure Firewall: Managed stateful firewall with Threat Intelligence
```

---

# 16. Network Security Architecture

## 16.1 Zero Trust Architecture

```
Zero Trust Principles (NIST SP 800-207):
  1. All data sources and services are resources
  2. All communication is secured (regardless of network location)
  3. Access to resources is granted per-session
  4. Access determined by dynamic policy (context-aware)
  5. All devices monitored for security posture
  6. Authentication and authorization strictly enforced

"Never trust, always verify" — even internal traffic is verified

ZTA components:
  Policy Engine (PE):    Makes access decisions
  Policy Administrator (PA): Manages communication channel to resource
  Policy Enforcement Point (PEP): Gateway/proxy that enforces decisions
  
  Data sources for PE:
    CDM system (continuous diagnostics)
    Threat intelligence
    IDPS signals
    Data access policies
    PKI

BeyondCorp (Google's ZTA implementation):
  Device inventory database
  Device identity certificates
  User identity (SSO)
  Access proxy evaluates all of above per request
  No VPN — access is application-level, not network-level
```

## 16.2 Firewalls & Segmentation

```
Firewall types:
  Packet filter:      Rules on src/dst IP, port, protocol. Stateless.
  Stateful:           Track TCP sessions. Allow return traffic automatically.
  Application layer:  Deep packet inspection. Understand HTTP, DNS, TLS.
  NGFW (Next-Gen):    App-ID, user-ID, threat prevention, SSL inspection.

Network segmentation strategies:
  VLAN (L2): Separate broadcast domains. East-west traffic via router.
  Subnet (L3): IP-level separation. Firewall/ACL at boundary.
  Micro-segmentation: Per-workload policy (VMware NSX, Illumio, Calico)
  Zero Trust segment: Identity-based policy, no implicit trust by subnet

DMZ (Demilitarized Zone):
  Hosts public-facing services (web, email, DNS)
  Separate from internal network
  Firewall on both sides (external and internal)
  Compromise in DMZ doesn't expose internal network

Defense in depth layers:
  Internet → DDoS scrubbing → WAF → Load balancer 
  → Application tier (security group) → API gateway 
  → Service mesh (mTLS, authz policy) 
  → Database tier (no internet access, VPC endpoint only)
```

## 16.3 DDoS Mitigation

```
DDoS types:
  Volumetric: Bandwidth exhaustion (UDP flood, ICMP flood, amplification)
              Amplification: small request → large response → target flooded
              DNS amplification: 40B request → 3000B response (75× amplification)
              NTP MONLIST: 234× amplification
              SSDP: 30× amplification
  
  Protocol: State table exhaustion (SYN flood, Smurf)
  Application (L7): HTTP flood, Slowloris (hold connections), cache busting
  
Mitigation hierarchy:
  1. Anycast diffusion: Route traffic to multiple PoPs, absorb locally
  2. BGP blackhole: Upstream drops traffic to target IP
     (collateral damage — legitimate traffic also dropped)
  3. Scrubbing centers: Route traffic through cleaning center, forward clean traffic
  4. Rate limiting: At edge/load balancer layer
  5. Challenge pages: CAPTCHA, JavaScript challenge, browser fingerprinting
  
AWS Shield:
  Shield Standard: Free, automatic protection against common L3/L4
  Shield Advanced: $3,000/month, L7 protection, DDoS cost protection,
                   WAF included, 24/7 DDoS Response Team access

Cloudflare DDoS:
  Largest anycast network (300+ Tbps capacity)
  "Under Attack Mode": JS challenge for all visitors
  Rate limiting rules
  Magic Transit: BGP-based DDoS protection for IP ranges
```

## 16.4 WAF (Web Application Firewall)

```
WAF protects against OWASP Top 10:
  SQL injection, XSS, SSRF, path traversal, broken auth,
  insecure deserialization, security misconfiguration, etc.

WAF rule types:
  Signature-based: Match known attack patterns (regex, string match)
  Rate-based: Too many requests from single IP in time window
  Geo-blocking: Block or challenge traffic from specific countries
  IP reputation: Block known malicious IPs (threat intel feeds)
  Custom rules: Business logic (block specific headers, user agents)

ModSecurity CRS (Core Rule Set):
  Open-source WAF engine (Nginx, Apache, IIS)
  Paranoia levels 1-4 (higher = more rules, more false positives)
  Anomaly scoring: requests accumulate score, blocked above threshold

WAF evasion techniques (know to defend):
  URL encoding: %3Cscript%3E = <script>
  Double encoding: %253C = %3C = <
  Unicode normalization: ＜script＞ → <script>
  HTTP parameter pollution: ?id=1&id=2 (which does backend use?)
  Chunked encoding: split attack across multiple chunks
  Case variation: SeLEcT iNsTeAd of SELECT
  Comment injection: SE/**/LECT (MySQL)
  
Defense: Normalize input BEFORE inspection, not after.
```

## 16.5 VPN & Tunneling

```
Site-to-Site VPN:
  IPSec tunnel between on-prem router and cloud gateway
  IKE (Internet Key Exchange): negotiate keys (IKEv2 preferred)
  ESP (Encapsulating Security Payload): encrypt + authenticate traffic
  AH (Authentication Header): authenticate only (no encryption)
  
  Modes:
    Transport mode: encrypt payload only, original IP header visible
    Tunnel mode: encrypt entire packet, new IP header added (VPN gateway)
  
  ISAKMP/IKEv1 vulnerabilities: Weak DH groups, aggressive mode, pre-shared keys
  IKEv2: better security, MOBIKE (IP change without reconnect)

WireGuard:
  Modern VPN protocol (2016, Linux kernel 5.6+)
  Only ~4,000 lines of code (vs OpenVPN ~500,000)
  Uses: Noise protocol framework, Curve25519, ChaCha20-Poly1305, BLAKE2s
  Key exchange: Ephemeral Diffie-Hellman on Curve25519
  No PKI required — pre-share public keys
  Roaming: connection follows client IP change automatically
  
SSL/TLS VPN (OpenVPN, Cisco AnyConnect):
  Works over TCP 443 (harder to block than IPSec)
  Client software required
  User certificate + MFA typical
```

## 16.6 Network Detection & Response (NDR)

```
Zeek (formerly Bro):
  Network traffic analyzer, not a traditional IDS
  Generates structured logs for every connection, HTTP request, DNS query, etc.
  Lua-like scripting for custom analysis
  
  Key log files:
    conn.log:   All TCP/UDP connections (src, dst, duration, bytes, state)
    http.log:   HTTP requests/responses (method, host, URI, status, user-agent)
    dns.log:    DNS queries/responses
    ssl.log:    TLS connections (server cert, cipher, version)
    files.log:  Files transferred (hash, MIME type)
    notice.log: Alerts generated by Zeek scripts

Suricata:
  IDS/IPS/NSM engine
  Rules: Snort-compatible + additional Suricata keywords
  Lua scripting for complex detection
  Multi-threaded (unlike Snort 2.x)
  AF_PACKET or PF_RING for high-throughput capture
  
  Rule structure:
    action proto src_ip src_port -> dst_ip dst_port (options)
    alert tcp $EXTERNAL_NET any -> $HOME_NET 22 (msg:"SSH brute force"; 
      threshold: type both, track by_src, count 5, seconds 60; sid:1001;)

Behavioral detection:
  Beaconing: C2 connects at regular intervals (beacon math analysis)
    Look for: consistent connection intervals, small data transfers
  DNS tunneling: large TXT queries, many unique subdomains, high entropy names
  Lateral movement: internal scanning, unusual service connections
  Data exfiltration: large outbound transfers, compression before upload
```

---

# 17. Cloud Security

## 17.1 IAM Architecture

```
Identity and Access Management fundamentals:
  Authentication: Prove who you are
  Authorization:  Prove what you can do
  
  Principals:
    Human users (SSO, MFA, federated identity)
    Service accounts / IAM roles (for workloads)
    External identities (OIDC federation — no static keys!)
  
  Least privilege principle:
    Grant minimum permissions needed
    Time-limited access for sensitive operations
    Just-in-time (JIT) privilege elevation

AWS IAM:
  Policy types:
    Identity-based: Attached to user/role/group (what can this principal do?)
    Resource-based: Attached to resource (who can access this resource?)
    Service Control Policy (SCP): Org-level guardrails (never bypassed)
    Permission boundary: Max permissions an identity can have
    Session policy: Restrict assumed role further
  
  Policy evaluation:
    Explicit Deny → always wins
    Allow requires: identity-based OR resource-based allow
    SCP must allow (for member accounts in Org)
    No implicit deny from missing resource-based policy (if identity-based allows)
  
  IAM Roles for Service Accounts (IRSA):
    Kubernetes pods assume IAM role via OIDC federation
    No long-lived AWS credentials in pods
    Token projected into pod, exchanged for STS credentials
  
  IAM Conditions:
    aws:RequestedRegion: restrict to specific regions
    aws:PrincipalOrgID: restrict to organization
    aws:MultiFactorAuthPresent: require MFA
    s3:prefix / s3:delimiter: object-level restrictions
    aws:SourceIp / aws:SourceVpc: network conditions
    aws:CalledVia: service-chain conditions (Athena → S3)

Privileged Access Management (PAM):
  Just-in-time access: request → approval → time-limited grant → auto-revoke
  Session recording: all privileged actions recorded
  Credential vaulting: store and rotate secrets automatically
  Break-glass accounts: emergency access with audit trail
  Tools: CyberArk, HashiCorp Vault, AWS SSM Session Manager
```

## 17.2 Secrets Management

```
Secret types:
  API keys, database passwords, TLS certificates,
  SSH keys, OAuth tokens, encryption keys

Anti-patterns:
  Secrets in code (git history is forever)
  Secrets in environment variables (visible in /proc, logs)
  Secrets in container images
  Shared service accounts

HashiCorp Vault:
  Secrets engine: store, generate, or encrypt secrets
    KV (key-value): static secrets with versioning
    Database: dynamic credentials (short-lived, unique per request)
    AWS: dynamic IAM credentials
    PKI: certificate authority (issue short-lived certs)
    Transit: encrypt/decrypt without exposing keys (encryption as a service)
  
  Auth methods:
    AppRole: role_id + secret_id (for machines)
    Kubernetes: pod ServiceAccount token verified against k8s API
    AWS IAM: instance profile or STS token
    LDAP/OIDC: for human users
  
  Lease: every secret has TTL, must be renewed or re-fetched
  Dynamic secrets: database credentials valid 1h → auto-revoked after
  
  Agent Sidecar: Vault Agent injects secrets into pod as files/env vars
                 Handles renewal and rotation transparently

Kubernetes Secrets:
  Base64 encoded (NOT encrypted by default)
  Must enable etcd encryption at rest (EncryptionConfiguration)
  Better: External Secrets Operator → sync from Vault/SSM/SecretManager
  
AWS Secrets Manager vs Parameter Store:
  Secrets Manager: automatic rotation, cross-account, costs $0.40/secret/month
  Parameter Store: free tier (standard), no rotation, simpler use cases
  SecureString: encrypted with KMS, accessible via IAM policy

Certificate rotation:
  Short-lived certs (24h or less) > revocation mechanisms
  cert-manager (Kubernetes): automate cert issuance and renewal
  Let's Encrypt (ACME): free TLS, 90-day certs, auto-renew
  AWS ACM: managed TLS, auto-renews, integrated with ALB/CloudFront
```

## 17.3 Cloud Security Posture Management (CSPM)

```
CSPM continuously monitors cloud configuration against security baselines:
  - S3 buckets not publicly accessible
  - Security groups not open to 0.0.0.0/0
  - MFA enabled on all IAM users
  - CloudTrail enabled in all regions
  - Encryption at rest for all data stores
  - No hardcoded credentials
  - Least privilege IAM policies

Tools:
  AWS Security Hub: Aggregates findings from GuardDuty, Inspector, Macie,
                    Config, plus third-party tools. Compliance standards:
                    CIS Benchmarks, PCI-DSS, SOC 2
  
  AWS Config: Records resource configuration over time.
              Config Rules: check specific configurations.
              Conformance Packs: groups of rules for compliance standards.
  
  Prowler: Open-source AWS security assessment tool
           CIS Benchmark checks, GDPR, HIPAA, SOC2
  
  Checkov: IaC scanner (Terraform, CloudFormation, Kubernetes, Dockerfiles)
           Checks for misconfigurations before deployment
  
  Prisma Cloud (Palo Alto): Multi-cloud CSPM
  Wiz: Agentless, graph-based cloud security

CIS Benchmarks for Cloud:
  Level 1: Basic security (no significant overhead)
  Level 2: Advanced security (may impact usability/performance)
  
  Key AWS CIS checks:
    1.1:  Avoid using root account
    1.5:  MFA on root account
    2.1:  CloudTrail enabled everywhere
    2.6:  AWS Config enabled in all regions
    3.1:  Log metric filter for unauthorized API calls
    4.1:  No unrestricted SSH inbound
    4.2:  No unrestricted RDP inbound
```

## 17.4 Runtime Security

```
Cloud Workload Protection Platform (CWPP):
  Workload-level security across VMs, containers, serverless
  
  Capabilities:
    Runtime protection: detect + prevent attacks in real-time
    Vulnerability management: scan images, packages, OS
    Network segmentation: micro-segmentation policy
    File integrity monitoring (FIM): detect file changes
    System call monitoring: detect anomalous behavior

Falco (CNCF):
  Runtime security for containers and Linux hosts
  Uses eBPF to monitor syscalls and Kubernetes audit events
  
  Rule example:
  - rule: Terminal shell in container
    desc: A shell was spawned by a container
    condition: >
      spawned_process and container
      and shell_procs and proc.tty != 0
    output: >
      A shell was spawned in a container (user=%user.name
      container=%container.name image=%container.image.repository)
    priority: WARNING
  
  Integration: Falco → Falcosidekick → Slack/PagerDuty/SIEM

AWS GuardDuty:
  Threat detection using ML + threat intelligence
  Sources: CloudTrail, VPC Flow Logs, DNS Logs, EKS audit logs, S3 data events
  
  Detection categories:
    Backdoor: EC2 used as TOR exit node, cryptocurrency mining
    Behavior: unusual API calls from known malicious IPs
    CryptoCurrency: EC2 communicating with crypto mining pools
    PenTest: Kali Linux or Parrot OS accessing AWS services
    Persistence: IAM policy changed to allow public access
    Stealth: CloudTrail disabled, S3 logging disabled
    Trojan: EC2 querying domains used by known malware

Container security scanning:
  Image scanning: Trivy, Snyk, Grype, AWS ECR scanning
  Scan at: build time (CI), registry (on push), runtime (periodic)
  
  SBOM (Software Bill of Materials): inventory of all packages
  SLSA (Supply chain Levels for Software Artifacts):
    Level 1: Build provenance generated
    Level 2: Build service generates + signs provenance
    Level 3: Build service hardened, tamper-evident
    Level 4: Two-party review, hermetic builds
```

## 17.5 Network Security in Cloud

```
VPC Flow Logs:
  Record IP traffic to/from VPC network interfaces
  Fields: version, account-id, interface-id, srcaddr, dstaddr,
          srcport, dstport, protocol, packets, bytes, start, end,
          action (ACCEPT/REJECT), log-status
  
  Destinations: CloudWatch Logs, S3, Kinesis Data Firehose
  Not real-time: delivered every 10 minutes (1 minute for enhanced)
  
  Analysis:
    Find rejected connections: action=REJECT
    Find large data transfers: bytes > threshold
    Find unusual ports: dstport not in known-good list
    Find internal lateral movement: srcaddr and dstaddr in RFC1918

AWS Network Firewall:
  Managed stateful IDS/IPS
  Suricata-compatible rule groups
  Stateful inspection, domain filtering
  Deployed in dedicated subnet, traffic routed through it

Private subnets + PrivateLink:
  Services in private subnet have no internet route
  Access AWS services via VPC endpoints (no internet traversal)
  Gateway endpoints: S3, DynamoDB (free, route table entry)
  Interface endpoints (PrivateLink): ENI in subnet with private IP ($0.01/hr/AZ)
  
Security group vs NACL:
  Security Group:     Stateful, instance level, allow rules only
  NACL:               Stateless, subnet level, allow+deny rules
  Best practice:      Use SGs as primary control, NACLs for subnet isolation
```

---

# 18. Observability & Reliability Engineering

## 18.1 The Three Pillars of Observability

```
Metrics:   Numerical measurements over time (aggregatable)
           "95th percentile latency is 200ms"
           "Error rate is 0.1%"
           "CPU utilization is 75%"

Logs:      Discrete events with context (queryable)
           "2024-01-01 12:00:01 ERROR user_id=123 payment failed: timeout"
           Structured (JSON) > unstructured (regex nightmares)

Traces:    Request flow across multiple services (correlatable)
           Shows which service introduced latency, where errors originated

The problem with pillars: They're often disconnected.
The solution: Correlate with trace_id/span_id across all three.
  - Metrics tagged with trace_id for high-cardinality metrics (exemplars)
  - Logs include trace_id for correlation
  - Traces link to relevant log entries
```

## 18.2 Metrics Deep Dive

```
Metric types:
  Counter:   Monotonically increasing. Rate over time = useful.
             requests_total, errors_total, bytes_sent_total
  
  Gauge:     Current value. Can go up or down.
             memory_usage_bytes, goroutines_count, queue_depth
  
  Histogram: Samples observations in buckets. Calculates percentiles server-side.
             request_duration_seconds_bucket{le="0.1"} = 500
             request_duration_seconds_bucket{le="0.5"} = 900
             request_duration_seconds_bucket{le="+Inf"} = 1000
  
  Summary:   Calculates percentiles client-side. Less flexible, can't aggregate.
             request_duration_seconds{quantile="0.99"} = 0.45

Cardinality: Number of unique label combinations.
  High cardinality (user_id, request_id) causes metric explosion.
  Rule: Never use unbounded values as labels.
  Use logs or traces for high-cardinality dimensions.

RED Method (for services):
  Rate:    Request rate (requests/second)
  Errors:  Error rate (%)
  Duration: Request latency (p50, p95, p99)

USE Method (for resources):
  Utilization: % time resource is busy
  Saturation:  How much work is queued (can't serve)
  Errors:      Error events per second

Four Golden Signals (Google SRE):
  Latency, Traffic, Errors, Saturation
```

## 18.3 Distributed Tracing

```
OpenTelemetry (OTEL):
  Vendor-neutral observability framework
  Replaces: Jaeger client, Zipkin client, OpenTracing, OpenCensus
  
  Concepts:
    Trace:   Complete end-to-end journey of a request
    Span:    Single operation within a trace
             (start time, end time, name, attributes, events, status)
    Context: Propagated via HTTP headers or message metadata
    
  Propagation formats:
    W3C TraceContext: traceparent: 00-{trace_id}-{span_id}-{flags}
    B3 (Zipkin): X-B3-TraceId, X-B3-SpanId, X-B3-Sampled
    Baggage: User-defined key-value pairs propagated with trace

  Auto-instrumentation:
    Java agent: bytecode injection, zero code change
    Python: monkey-patching standard libraries
    Go: manual instrumentation (no runtime reflection for auto)

Sampling strategies:
  Head-based: Decision at trace start (before seeing full trace)
    Probabilistic: 1% of all requests
    Rate-limiting: max N traces/second
  
  Tail-based: Decision after trace complete (can sample interesting traces)
    Error traces: always sample errors
    Slow traces: sample above latency threshold
    Adaptive: sample proportionally to error/latency signals
  
  Collector (OTEL Collector):
    Receives spans from applications
    Processes (batch, filter, transform)
    Exports to backends (Jaeger, Zipkin, Tempo, Datadog, X-Ray)
```

## 18.4 Logging Architecture

```
Structured logging:
  JSON format: machine-parseable, field extraction, no regex
  Standard fields: timestamp, level, service, trace_id, span_id, user_id, error
  
  Log levels:
    TRACE: Very detailed, usually disabled in production
    DEBUG: Useful for developers debugging
    INFO:  Normal operation events (startup, shutdown, important actions)
    WARN:  Unexpected situations that don't cause failure yet
    ERROR: Failures that need attention (but service continues)
    FATAL: Service cannot continue, will exit

Log aggregation pipeline:
  Application → stdout/stderr
  → Container log driver (json-file, journald, fluentd)
  → Log collector (Fluentd, Fluent Bit, Vector, Promtail)
  → Log storage (Elasticsearch, Loki, CloudWatch, Splunk)
  → Visualization + Query (Kibana, Grafana, CloudWatch Insights)

Loki (Grafana):
  "Like Prometheus, but for logs"
  Index only labels (not full text) — cheaper than Elasticsearch
  Queries: LogQL (like PromQL but for logs)
  Push model: Promtail/Alloy sends logs to Loki
  
  LogQL example:
    {namespace="production",service="payment"} |= "error" | json | duration > 1s

Elasticsearch:
  Full-text inverted index on every field
  Excellent search, more expensive to run
  ELK/EFK stack: Elasticsearch + Logstash/Fluentd + Kibana
  OpenSearch: AWS fork (after Elastic license change)
```

## 18.5 SRE & Error Budgets

```
SLI (Service Level Indicator):
  Quantitative measure of service behavior
  "What we measure"
  Example: proportion of HTTP requests with latency < 200ms

SLO (Service Level Objective):
  Target value for SLI
  "What we promise ourselves"
  Example: 99.9% of requests complete in < 200ms over 30-day window

SLA (Service Level Agreement):
  SLO + consequences for missing it (credits, termination)
  "What we promise customers"

Error budget:
  1 - SLO = budget for unreliability
  99.9% SLO → 0.1% error budget → 43.8 minutes/month of "badness"
  
  If error budget consumed: no new feature releases, focus on reliability
  If error budget remaining: team can take risks, deploy new features
  
  Error budget policy: written agreement on what happens at 50%, 75%, 100% consumed

Toil reduction:
  Toil: repetitive, manual, automatable work that scales with traffic
  Target: < 50% of SRE time on toil
  Automate: provisioning, failover, scaling, incident response playbooks

Incident management:
  SEV1: Service down for all users
  SEV2: Significant degradation for subset of users
  SEV3: Minor issue, workaround exists
  
  Incident lifecycle:
    Detect → Page → Acknowledge → Investigate → Mitigate → Resolve → Postmortem
  
  Blameless postmortem:
    What happened (timeline)
    Why it happened (5 whys, contributing factors)
    What we're doing to prevent recurrence (action items with owners+dates)
    No blame — systems, not people, failed
```

---

# 19. Infrastructure as Code

## 19.1 Terraform Deep Dive

```
Terraform architecture:
  HCL (HashiCorp Configuration Language) → Plan → Apply
  
  Providers: Plugins that interface with APIs (AWS, GCP, Azure, Kubernetes)
  Resources: Managed infrastructure objects
  Data sources: Read-only queries to existing infrastructure
  Modules: Reusable configuration packages
  State: JSON file tracking real-world resource mapping

State management:
  Local: terraform.tfstate (dangerous for teams)
  Remote: S3 + DynamoDB locking (AWS), GCS, Terraform Cloud
  
  State locking: Prevents concurrent applies (DynamoDB table)
  State encryption: S3 SSE-KMS for secrets in state
  
  Never manually edit state. Use: terraform state mv, rm, import

Terraform workflow:
  terraform init      # Download providers, configure backend
  terraform validate  # Check syntax
  terraform plan      # Show changes (diff)
  terraform apply     # Apply changes
  terraform destroy   # Remove all resources

Resource graph:
  Terraform builds DAG of all resources
  Parallel operations where no dependencies
  Explicit: depends_on = [resource.name]
  Implicit: reference another resource's output

Workspaces:
  Separate state files for different environments (dev/staging/prod)
  Alternative: separate directories per environment (more isolation)
  Best practice: separate AWS accounts per environment

Terraform best practices:
  Remote state with locking
  Pin provider versions (~> 5.0)
  Use modules for repeated patterns
  Tag all resources (cost allocation, ownership)
  Store secrets in Vault/SSM, reference by ARN (not in .tf files)
  terragrunt for DRY configurations across environments
  Sentinel/OPA for policy enforcement (prevent misconfigurations)
```

## 19.2 Helm & Kubernetes Package Management

```
Helm concepts:
  Chart:   Package of Kubernetes manifests
  Release: Deployed instance of a chart
  Values:  Configuration parameters
  Repository: Collection of charts
  
  Chart structure:
    Chart.yaml         # Metadata (name, version, dependencies)
    values.yaml        # Default values
    templates/         # Kubernetes manifests with Go templates
    templates/NOTES.txt # Post-install instructions
    charts/            # Dependency charts
    .helmignore        # Files to ignore

Helm templating:
  {{ .Values.image.tag }}         # Reference value
  {{ .Release.Name }}             # Release name
  {{ include "chart.fullname" . }} # Include named template
  {{- if .Values.ingress.enabled }} # Conditional
  {{- range .Values.hosts }}        # Loop

Helmfile:
  Declarative Helm release management
  Multiple charts + environments in one file
  Diff: helmfile diff (show what would change)
  Apply: helmfile sync

Helm chart security:
  Verify chart provenance: helm verify (GPG signature)
  Use specific chart versions (not latest)
  Scan with: helm lint, checkov, polaris
  OCI registry: store charts in ECR/GCR (signed, versioned)

Kustomize:
  Template-free customization using patches
  Base: generic Kubernetes manifests
  Overlay: environment-specific patches (no forking)
  
  kustomization.yaml:
    resources:
      - ../base
    patches:
      - target: { kind: Deployment, name: app }
        patch: |
          - op: replace
            path: /spec/replicas
            value: 3
    images:
      - name: app
        newTag: "1.2.3"
```

---

# 20. API Design & Gateway Patterns

## 20.1 REST API Design Principles

```
REST constraints (Fielding dissertation, 2000):
  1. Client-Server: Separation of concerns
  2. Stateless: No client state stored on server
  3. Cacheable: Responses must define cacheability
  4. Uniform Interface: Resource identification via URIs
  5. Layered System: Client can't tell if direct or proxy
  6. Code on Demand: Optional (JavaScript)

Resource naming:
  Nouns, not verbs (use HTTP methods for verbs)
  /users (collection)
  /users/{id} (singleton)
  /users/{id}/orders (sub-collection)
  
  Not: /getUser, /createOrder, /deleteAccount

HTTP methods semantics:
  GET:    Idempotent, safe (no side effects), cacheable
  POST:   Not idempotent, not safe, not cacheable (by default)
  PUT:    Idempotent, replaces entire resource
  PATCH:  Not idempotent (usually), partial update
  DELETE: Idempotent, removes resource

HTTP status codes (critical ones):
  200 OK:           Success
  201 Created:      Resource created (POST)
  204 No Content:   Success, no body (DELETE, PUT)
  400 Bad Request:  Client error (validation failed)
  401 Unauthorized: Not authenticated
  403 Forbidden:    Authenticated but not authorized
  404 Not Found:    Resource doesn't exist
  409 Conflict:     State conflict (optimistic lock, duplicate)
  422 Unprocessable:Semantic validation error
  429 Too Many Req: Rate limited
  500 Internal:     Server error (never expose details)
  503 Unavailable:  Service temporarily unavailable

API versioning strategies:
  URL path:   /v1/users, /v2/users (most visible, easy to test)
  Header:     Accept: application/vnd.company.v2+json
  Query param: /users?version=2
  Best practice: URL path for major versions, backward-compat for minor

Pagination:
  Offset: ?offset=100&limit=25 (simple, but deep pagination expensive)
  Cursor: ?cursor=<opaque_token>&limit=25 (efficient, handles inserts)
  Keyset: ?after_id=12345&limit=25 (efficient, but limited to ordered data)
```

## 20.2 gRPC Architecture

```
Protocol Buffers (protobuf):
  Binary serialization format
  Schema-first: define .proto files, generate code
  
  Example:
  syntax = "proto3";
  service UserService {
    rpc GetUser (GetUserRequest) returns (User);
    rpc ListUsers (ListUsersRequest) returns (stream User);
    rpc CreateUsers (stream CreateUserRequest) returns (CreateUsersResponse);
    rpc Chat (stream ChatMessage) returns (stream ChatMessage);
  }
  
  message User {
    int64 id = 1;
    string email = 2;
    repeated string roles = 3;
    google.protobuf.Timestamp created_at = 4;
  }

gRPC features:
  HTTP/2 transport (multiplexing, header compression, flow control)
  Bidirectional streaming
  Deadline/timeout propagation
  Metadata (like HTTP headers)
  Interceptors (middleware)
  Health checking protocol (standard)
  Server reflection (inspect service without proto files)
  
  Load balancing challenges:
    HTTP/2 is connection-based → L7 LB needed (not just L4)
    gRPC client-side LB: resolve DNS → round-robin across endpoints
    Or: service mesh (Envoy) does L7 gRPC LB

gRPC-Web:
  Browser clients cannot use HTTP/2 gRPC directly (no trailer support)
  gRPC-Web proxy (Envoy) translates between browser and gRPC backend
  
protobuf vs JSON:
  Size: protobuf ~3-10× smaller
  Speed: encoding ~5-10× faster
  Human-readable: JSON wins
  Schema evolution: both support backward compatibility (new fields ignored)
```

## 20.3 API Gateway Patterns

```
API Gateway responsibilities:
  Authentication/Authorization (JWT validation, OAuth)
  Rate limiting (per-client, per-endpoint)
  Request routing (path-based, header-based)
  Request/response transformation (version adapters)
  SSL termination
  Logging and metrics
  Circuit breaking
  Caching
  API composition (aggregate multiple backend calls)

Gateway patterns:
  Backend for Frontend (BFF):
    Separate gateway per client type (mobile, web, partner)
    Optimized response shapes per client
    Avoids over-fetching for constrained clients (mobile)
  
  API Aggregation:
    Single request to gateway → multiple backend calls → composed response
    Reduces client-side round trips
    Danger: one slow backend makes entire aggregation slow (use timeouts + partial response)
  
  Canary deployment via gateway:
    Route 5% of traffic to new version by header or user group
    Gradually increase percentage
    Rollback: set percentage to 0

AWS API Gateway:
  REST API: Feature-rich, per-request pricing
  HTTP API: Simpler, lower cost, JWT auth, CORS
  WebSocket API: Bidirectional for real-time
  
  Authorizers:
    Lambda authorizer: custom auth logic
    JWT authorizer: validate JWT (HTTP API only)
    Cognito: AWS managed identity

Kong, Traefik, Nginx, Envoy as API gateways:
  Kong: Plugin architecture (rate-limit, auth, logging)
  Traefik: Auto-discovery (Docker, Kubernetes), Let's Encrypt
  Envoy: Programmable, used as service mesh sidecar
  APISIX: High performance, etcd-backed, Apache project
```

---

# 21. Cryptography in Systems

## 21.1 Symmetric Encryption

```
AES-256-GCM (most common in modern systems):
  Block cipher: 128-bit blocks
  Key size: 256 bits
  Mode: GCM (Galois/Counter Mode)
    CTR mode: stream cipher behavior
    GHASH: authentication tag (AEAD — Authenticated Encryption with Associated Data)
  
  Properties:
    Confidentiality (encryption)
    Integrity (authentication tag — detects tampering)
    Authenticity (if key is secret, proves sender)
  
  Never: reuse (key, nonce) pair — catastrophic failure (XOR of ciphertexts reveals XOR of plaintexts)
  Nonce: 96-bit random (standard) or counter
  Tag: 128-bit authentication tag

ChaCha20-Poly1305:
  Stream cipher (ChaCha20) + MAC (Poly1305)
  No timing side-channel risk (no hardware AES required for security)
  Preferred on mobile/IoT (no AES-NI hardware)
  TLS 1.3 mandatory cipher suite
```

## 21.2 Asymmetric Cryptography

```
RSA:
  Key sizes: 2048 (minimum), 3072, 4096 bits
  Uses: key exchange (encrypt symmetric key), signatures
  Problem: slow, large key size, not quantum-resistant
  
  DO NOT use for encryption of bulk data
  DO use for: TLS key exchange (legacy), signature (code signing)

Elliptic Curve Cryptography (ECC):
  256-bit ECC ≈ 3072-bit RSA security
  Faster, smaller keys, less CPU
  
  Curves:
    P-256 (secp256r1): NSA-designed, widely supported
    P-384 (secp384r1): Higher security margin
    Curve25519 (X25519): Bernstein's curve, no NSA involvement, safest
    secp256k1: Bitcoin's curve (NOT recommended for new systems)
  
  ECDH (key exchange):
    Both parties have key pairs
    Shared secret = ECDH(my_private, their_public)
    ECDHE: ephemeral key per session (forward secrecy)
  
  ECDSA (signature):
    Sign: r,s = sign(hash, private_key, random_k)
    Verify: check(r,s, hash, public_key)
    CRITICAL: k must be truly random. Reused k → private key recovery.
    (Sony PS3 hack used non-random k)
    
  EdDSA (Ed25519):
    Deterministic k (derived from private key + message — no RNG needed)
    Faster than ECDSA
    No timing side channels
    Use this for new systems

Diffie-Hellman:
  Key exchange: establish shared secret over public channel
  Never transmits secret
  DHE: classic (group, generator, large prime)
  ECDHE: elliptic curve variant (preferred)
  Forward secrecy: ephemeral keys mean past sessions not decrypted if long-term key compromised
```

## 21.3 Key Management

```
Key Hierarchy:
  Master Key (KEK — Key Encryption Key)
    → Data Encryption Key (DEK)
      → Encrypted Data

Why hierarchy?
  DEKs can be rotated without re-encrypting all data (re-wrap DEK with new KEK)
  Master key stored in HSM, never leaves hardware

HSM (Hardware Security Module):
  Dedicated hardware for cryptographic operations
  Keys stored in tamper-resistant hardware
  Operations: sign, verify, encrypt, decrypt — keys never exported
  Standards: FIPS 140-2 Level 3 (Level 4 for highest security)
  
  Cloud HSMs:
    AWS CloudHSM: dedicated HSM in your VPC
    AWS KMS: shared HSM (FIPS 140-2 Level 2), simpler, API-based
    Azure Dedicated HSM / Managed HSM
    GCP Cloud KMS / Cloud HSM

Key rotation:
  Rotate regularly (90 days, 1 year — depends on key type)
  Rotation: generate new key, re-encrypt DEKs, keep old key for decryption until fully migrated
  Emergency rotation: suspected compromise → immediate rotation

Envelope encryption (AWS KMS pattern):
  1. Generate DEK: call KMS → returns (plaintext_DEK, encrypted_DEK)
  2. Encrypt data with plaintext_DEK
  3. Store encrypted_DEK alongside encrypted data
  4. Never store plaintext_DEK
  
  To decrypt:
  1. Call KMS with encrypted_DEK → plaintext_DEK
  2. Decrypt data with plaintext_DEK
```

---

# 22. Performance Engineering

## 22.1 Performance Testing Types

```
Load testing:     Normal expected load (verify baseline performance)
Stress testing:   Beyond normal load (find breaking point)
Soak testing:     Sustained load over long period (memory leaks, connection pool exhaustion)
Spike testing:    Sudden traffic spike (auto-scaling response, connection queuing)
Chaos testing:    Random failures (resilience verification)

Key metrics:
  Throughput:     Requests per second (RPS) — how much work done
  Latency:        Time to respond — p50, p95, p99, p999
  Error rate:     % of failed requests
  Saturation:     Resource utilization (CPU, memory, connections)

Percentiles matter more than averages:
  p50 (median): 50% of requests are faster than this
  p95: 95% of users experience this or better
  p99: 99% of users — your "long tail"
  p999: 1-in-1000 — often caused by GC, lock contention, cold starts
  
  Averages hide bimodal distributions.
  "Average latency is 50ms" can hide that 1% of requests take 5 seconds.

Amdahl's Law:
  Maximum speedup from parallelization:
  S(n) = 1 / ((1 - p) + p/n)
  
  p = parallel fraction, n = number of processors
  
  If 90% parallelizable with 10 cores: S = 1/(0.1 + 0.9/10) = 5.26×
  With ∞ cores: S = 1/0.1 = 10×
  
  Lesson: Serial bottlenecks limit parallelism gains.
  Find and eliminate serial bottlenecks first.
```

## 22.2 Database Performance

```
Query optimization checklist:
  1. EXPLAIN ANALYZE (see actual execution plan)
  2. Index coverage (is the query using the right index?)
  3. Table statistics fresh? (ANALYZE)
  4. Connection pool sized correctly?
  5. N+1 query problem? (eager loading vs lazy)
  6. Slow query log analyzed?
  
N+1 query problem:
  List 100 users → then 100 separate queries for each user's posts = 101 queries
  Fix: JOIN or batch fetch (WHERE id IN (...))

Connection pooling:
  Database connections are expensive to create (TLS handshake, auth)
  Pool: maintain N persistent connections, reuse for queries
  
  Pool sizing: max_connections should not exceed DB server's limit
  Formula: (core_count * 2) + effective_spindle_count (for Postgres)
  
  PgBouncer (Postgres):
    Session mode: 1 client = 1 DB connection (default)
    Transaction mode: connection released after each transaction (more efficient)
    Statement mode: connection released after each statement
  
  Read replicas: offload read traffic from primary
  Connection routing: ORM-level (SQLAlchemy), proxy-level (ProxySQL, PgPool)

Database partitioning for performance:
  Declarative partitioning by time: each month in own partition
  Queries on recent data: only scan recent partition (partition pruning)
  DROP old partition: instant (vs DELETE millions of rows)
  Parallel query across partitions

Caching query results:
  Materialized views: precomputed query results, refresh periodically
  Application-level cache: Redis/Memcached for expensive query results
  Query result cache: built-in to some DBs (MySQL query cache — deprecated, bad idea)
```

## 22.3 Application Performance

```
Profiling types:
  CPU profiling:     Where is CPU time spent? (sampling or instrumentation)
  Memory profiling:  Where are allocations? Where are leaks?
  I/O profiling:     Which I/O calls are slow?
  Lock profiling:    Which mutexes/locks have high contention?

Linux performance tools:
  top/htop:          CPU, memory, process overview
  perf:              CPU performance counters, sampling profiler
  flamegraph:        Visual CPU profiler (Brendan Gregg)
  strace:            System call trace (overhead!)
  ltrace:            Library call trace
  iotop:             Disk I/O per process
  nethogs:           Network I/O per process
  dstat:             Combined resource statistics
  vmstat:            Virtual memory statistics
  iostat:            I/O statistics per device
  ss:                Socket statistics (modern netstat)
  perf trace:        Low-overhead strace alternative

Go profiling:
  pprof: built-in profiler
  http.ListenAndServe("localhost:6060", nil) + net/http/pprof
  go tool pprof http://localhost:6060/debug/pprof/heap
  go tool pprof http://localhost:6060/debug/pprof/goroutine
  
  Types: cpu, heap, goroutine, threadcreate, block, mutex

JVM performance:
  GC tuning: G1GC (default Java 9+), ZGC (low latency), Shenandoah
  Heap sizing: -Xms (initial), -Xmx (max)
  GC logging: -Xlog:gc*:file=gc.log:time,uptime,level,tags
  JIT compilation: C1 (fast compile), C2 (optimized) — tiered compilation

Rust performance:
  Compiled to native code, no GC pauses
  LLVM optimizations: inlining, vectorization, dead code elimination
  Profile with: cargo flamegraph, perf, valgrind/callgrind
  Benchmarking: criterion crate (statistical benchmarking)
  
  Common performance issues:
    Excessive cloning (Arc<T>, Rc<T> reference counting overhead)
    Monomorphization bloat (generics compile to multiple functions)
    Dynamic dispatch (Box<dyn Trait> vs static dispatch &impl Trait)
```

---

# 23. Disaster Recovery & Business Continuity

## 23.1 Recovery Objectives

```
RTO (Recovery Time Objective):
  Maximum acceptable time to restore service after failure
  "We must be back up within 4 hours"
  Lower RTO → more expensive (hot standby, automatic failover)

RPO (Recovery Point Objective):
  Maximum acceptable data loss (measured in time)
  "We cannot lose more than 1 hour of transactions"
  Lower RPO → more expensive (synchronous replication, continuous backup)

RTO vs Cost:
  Hot standby:    Active replica, automatic failover, RTO = minutes, most expensive
  Warm standby:   Running but smaller, RTO = minutes-hours (need to scale up)
  Cold standby:   Stopped instance, start on failure, RTO = hours
  Backup restore: Restore from backup, RTO = hours-days

Backup strategies:
  Full backup:         Complete copy. Restore fast, storage expensive, slow to create.
  Incremental:         Only changes since last backup. Storage efficient, slow to restore.
  Differential:        Changes since last full. Balance of above.
  Continuous (CDP):    Every change recorded. Near-zero RPO.

3-2-1 Rule:
  3 copies of data
  2 different storage types
  1 offsite (different geographic location)
  Modern: 3-2-1-1-0 (1 offline/air-gapped, 0 errors verified by test restore)
```

## 23.2 Multi-Region Architecture

```
Active-Passive (Pilot Light / Warm Standby):
  Primary region: full traffic
  Secondary region: minimal or stopped infrastructure
  Failover: update DNS, start secondary services
  RTO: minutes to hours

Active-Active:
  Multiple regions serving traffic simultaneously
  DNS/global LB routes to nearest region
  Challenges:
    Data synchronization (conflict resolution)
    Global transactions (expensive)
    Regulatory compliance (data residency)
  
  Appropriate for: read-heavy workloads with eventual consistency
  Avoid for: write-heavy with strong consistency requirements

AWS multi-region patterns:
  Global Accelerator: Anycast entry point, routes to nearest region
  Route53 health checks + failover routing
  S3 Cross-Region Replication (CRR): async, eventual consistency
  RDS Global Database: Aurora with global replication (< 1s replication lag)
  DynamoDB Global Tables: Active-active multi-region, last-writer-wins
  
  Data sovereignty: Use SCP to prevent data egress to unauthorized regions
```

## 23.3 Chaos Engineering

```
Chaos Engineering (Netflix, 2011):
  "The discipline of experimenting on a distributed system in order to 
   build confidence in the system's capability to withstand turbulent 
   conditions in production"

Principles:
  1. Build a hypothesis around steady state behavior
  2. Vary real-world events (server crashes, network latency, AZ failure)
  3. Run experiments in production (or prod-like environment)
  4. Minimize blast radius (start small)
  5. Automate experiments

Netflix Chaos Monkey:
  Randomly terminates EC2 instances in production
  Forces engineering culture to build resilient systems
  Chaos Gorilla: terminates entire AZ
  Chaos Kong: simulates region failure

Fault injection types:
  Process kill: kill -9, Out of Memory
  Resource exhaustion: CPU 100%, memory leak, disk full
  Network: packet loss, latency injection, partition, bandwidth limit
  Dependency: service unavailable, slow response, bad data

AWS Fault Injection Service (FIS):
  Managed chaos engineering
  Actions: stop EC2, inject CPU stress, throttle EBS, network latency
  Safety mechanisms: stop conditions, rollback on alarm

Chaos Mesh (Kubernetes):
  Network chaos: packet loss, delay, corruption, duplicate
  Pod chaos: pod kill, container kill, pod failure
  Stress chaos: CPU, memory stress
  Kernel chaos: disk failure, process hang
  
Gameday:
  Planned exercise: team responds to pre-planned failure scenario
  Tests: detection, alert routing, runbooks, escalation
  Blameless, learning-focused
```

---

# 24. Advanced Topics

## 24.1 Service Reliability Patterns

```
Bulkhead Pattern:
  Isolate components so failure of one doesn't sink the ship
  Thread pool isolation: different thread pools per external dependency
  Connection pool isolation: separate pools per downstream service
  Pod isolation in Kubernetes: different node pools per service tier
  
  Without bulkhead: one slow downstream exhausts thread pool, brings down whole app
  With bulkhead: slow downstream exhausts its own pool, other dependencies unaffected

Retry Logic:
  Never retry without:
    Exponential backoff: delay doubles each retry (1s → 2s → 4s → 8s)
    Jitter: random offset to avoid retry storms (all clients retry simultaneously)
    Maximum retries: don't retry forever
    Idempotency check: only retry safe/idempotent operations
  
  Retry amplification: 3 services each retry 3× = 27 backend requests
  Carry deadline context, don't retry past client's deadline

Graceful Degradation:
  System continues with reduced functionality during partial failure
  Examples:
    Recommendation service down → show generic recommendations (not error)
    Payment gateway slow → queue payment, notify user
    Search index stale → serve cached results with "as of" timestamp
  
  Design for: what's the minimum viable experience when dependency X fails?

Backpressure:
  Producer notifies consumer it's overwhelmed; consumer should slow down
  HTTP: 429 Too Many Requests, 503 Service Unavailable
  TCP: receive buffer fills → window shrinks → sender slows
  Queue: consumer lag grows → producer-side rate limiting
  
  Without backpressure: producer fills memory → OOM → crash
```

## 24.2 Data Streaming & Real-Time Systems

```
Lambda Architecture:
  Speed layer:  Real-time processing (low latency, approximate)
  Batch layer:  Accurate processing of all historical data
  Serving layer: Merge speed + batch results for queries
  
  Problem: complex, two code paths for same logic

Kappa Architecture (Jay Kreps, 2014):
  Only streaming layer (stream all history on recompute)
  Single code path
  Simpler, but reprocessing history is slow
  Works well when Kafka retains full history

Apache Flink:
  Stateful stream processing
  Exactly-once semantics (with Kafka)
  Event time processing (not processing time)
  Windowing: tumbling, sliding, session, global
  State backends: memory, RocksDB (for large state)
  
  Checkpointing: periodic Chandy-Lamport snapshots for fault tolerance
  Restart from last checkpoint on failure
  
  Watermarks: handle late events
    Event time: time embedded in event
    Watermark: "we've seen all events up to time T"
    Late events after watermark: drop or route to side output

Apache Spark Structured Streaming:
  Micro-batch or continuous processing
  Streaming queries expressed like batch DataFrame operations
  Checkpointing for fault tolerance
  Trigger: ProcessingTime, Once, AvailableNow, Continuous

Stream processing patterns:
  Filter:   Remove events not matching criteria
  Map:      Transform each event
  Reduce:   Aggregate (sum, count, max)
  Join:     Combine streams (stream-stream, stream-table)
  Window:   Group events by time
  Dedup:    Remove duplicates (by key + window)
```

## 24.3 Data Mesh & Modern Data Architecture

```
Data Mesh (Zhamak Dehghani, 2019):
  Domain-oriented decentralized data ownership and architecture
  
  Principles:
    1. Domain ownership: teams own their data as products
    2. Data as a product: discoverable, addressable, understandable, trustworthy
    3. Self-serve data infrastructure: platform enables domains without central team
    4. Federated computational governance: global standards, local implementation
  
  vs Data Warehouse: centralized, ETL-heavy, slow
  vs Data Lake: centralized but schema-on-read, governance nightmare
  vs Data Lakehouse: Delta Lake, Iceberg, Hudi (combines best of both)

Apache Iceberg:
  Table format for huge analytic datasets
  Schema evolution: add/drop/rename columns without rewriting data
  Hidden partitioning: no need to know partition layout in queries
  Time travel: query data as of any point in time
  ACID transactions on object storage (S3, GCS)

dbt (data build tool):
  Transform data in warehouse using SQL
  Models are SELECT statements (not DDL/DML)
  Tests built-in (not null, unique, accepted values, referential integrity)
  Lineage graph automatically generated
  Git-based workflow for data transformations
```

## 24.4 Internal Platform Engineering

```
Platform Engineering vs DevOps:
  DevOps: Cultural movement, "you build it, you run it"
  Platform Engineering: Build internal developer platform (IDP) to enable DevOps at scale

Golden Path:
  Opinionated, supported path for common development tasks
  Not mandatory, but defaults that work well
  Example: "Golden Path" Kubernetes deployment = Helm chart template
           with sane defaults for monitoring, scaling, security

Internal Developer Platform (IDP) components:
  Service catalog:      All services, owners, SLOs, documentation
  Infrastructure portal: Self-service provisioning (request DB, queue, storage)
  CI/CD platform:       Standard pipelines, policy enforcement
  Secrets management:   Self-service secret rotation
  Observability:        Standard dashboards, alerting templates
  Developer portal:     Backstage (CNCF) — unified developer experience

Platform as a Product:
  Platform team treats internal teams as customers
  NPS surveys, feature requests, support SLAs
  Usage metrics, onboarding friction measurement
  
Backstage (Spotify):
  Open-source internal developer portal
  Software catalog: register all services, docs, APIs
  Tech Radar: recommended/trial/hold technology list
  Scaffolding: create new service from template
  Plugins: extend for any tool (PagerDuty, Kubernetes, GitHub Actions)
```

## 24.5 FinOps & Cost Engineering

```
Cloud cost drivers:
  Compute:  EC2/GCE/Azure VM, Kubernetes node costs
  Storage:  S3/GCS/Azure Blob, EBS volumes, data transfer
  Database: RDS, DynamoDB (read/write capacity units), BigQuery (scan)
  Network:  Data transfer out (egress), cross-AZ traffic, NAT gateway
  Licenses: Windows, RHEL, Oracle

Cost optimization strategies:
  Reserved Instances / Savings Plans:
    1-year or 3-year commitment → 40–72% discount
    Compute Savings Plans: any instance family, region, OS
    EC2 Instance Savings Plans: specific family, region
  
  Spot Instances / Preemptible VMs:
    Bid on spare capacity: 50–90% discount
    Can be interrupted with 2 min warning (AWS)
    Use for: batch jobs, stateless web, ML training (with checkpointing)
  
  Right-sizing:
    Analyze actual CPU/memory usage vs purchased size
    AWS Compute Optimizer, GCP Recommender, Azure Advisor
  
  Storage tiering:
    S3 Intelligent-Tiering: auto-move to cheaper tier based on access
    Lifecycle policies: S3 Standard → IA → Glacier after N days
  
  Cross-AZ traffic reduction:
    10% of US-East-1 bill can be AZ traffic
    Deploy consumers in same AZ as producers
    Topology-aware scheduling in Kubernetes

FinOps Foundation Maturity Model:
  Crawl: Basic visibility (cost allocation tags, daily report)
  Walk: Efficiency targets, showback/chargeback to teams
  Run: Real-time optimization, automated rightsizing, RI automation
```

---

# The Expert Mental Model

> A world-class infrastructure engineer does not think in tools — they think in **trade-offs, failure modes, and invariants**. Every system is a balance between consistency and availability, latency and throughput, complexity and reliability, cost and performance. The engineer's job is to make these trade-offs explicit, document them, and build systems that fail safely and observably.
>
> Mastery in this domain means developing an instinct for **where systems will break under load**, **which components will become bottlenecks before the others**, and **how a partial failure in one layer cascades through the rest**. This instinct comes from: studying postmortems (Google, Amazon, Cloudflare all publish them), running failure experiments deliberately before production does it for you, and always asking "what happens when this assumption is violated?"
>
> The Linux kernel is the foundation everything runs on. Containers are kernel primitives. Kubernetes is a distributed control loop. Distributed systems are physics problems constrained by the speed of light and the unreliability of networks. **Understanding the layers beneath your abstraction is what separates engineers who cargo-cult configurations from engineers who diagnose novel failures in minutes.**

---

## Quick Reference: Technology Decision Matrix

| Requirement | Technology Choices | Decision Factor |
|---|---|---|
| Strong consistency + SQL | PostgreSQL, MySQL, CockroachDB | Scale needs, multi-region? |
| High write throughput | Cassandra, ScyllaDB | Eventual consistency acceptable? |
| Key-value cache | Redis, Memcached | Persistence? Data structures? |
| Message streaming | Apache Kafka | Scale, retention, replay needed |
| Simple message queue | RabbitMQ, SQS | Routing complexity, managed? |
| Container orchestration | Kubernetes | Team size, managed vs self-hosted |
| Service mesh | Istio, Cilium, Linkerd | Complexity tolerance, eBPF support |
| IaC | Terraform, Pulumi | Team language preferences |
| Observability | Prometheus+Grafana, Datadog | Budget, integration needs |
| Stream processing | Flink, Spark Streaming | Latency, stateful complexity |
| Search | Elasticsearch, Typesense | Full-text vs vector, scale |
| Time-series | InfluxDB, Prometheus, VictoriaMetrics | Scrape-based vs push, retention |

---

*End of Guide — Continuously evolving field. Always verify against current documentation.*

Now let me build this comprehensive guide. This will be a massive, dense reference document.**4,346 lines, ~157KB** of dense technical content. Here's what's covered:

**24 major sections, including:**

1. **Mental Models** — CAP/PACELC, ACID/BASE, Little's Law, Fallacies of Distributed Computing
2. **Computer Architecture** — Memory hierarchy with actual latency numbers, epoll/io_uring internals, virtual memory page table walk
3. **Linux Kernel** — `task_struct`, CFS scheduler, buddy/slab allocators, MVCC/mmap, VFS layer, namespaces (all 8), cgroups v2 + PSI, LSM (SELinux/AppArmor/seccomp-bpf), **eBPF** (hooks, programs, security implications, attack surface), Netfilter/iptables packet path, capabilities
4. **Networking** — TCP state machine with every state, SYN cookies, CUBIC vs BBR, DNS (DNSSEC/DoT/DoH), HTTP/1.1→3 + QUIC internals, TLS 1.3 handshake, BGP + RPKI
5. **System Design** — Rate limiting (token bucket, sliding window, leaky bucket), consistent hashing, sharding strategies, R/W splitting
6. **Distributed Systems** — All consistency models, Two Generals, Byzantine faults, Lamport/Vector clocks, CRDTs, TrueTime, leader election
7. **Consensus** — Paxos (full algorithm), Raft (log replication, leader completeness), Zookeeper/ZAB, etcd
8. **Storage** — B-Tree vs LSM internals, WAL, MVCC (PostgreSQL + InnoDB), query execution pipeline, all index types, Cassandra/MongoDB/Redis/ClickHouse architectures
9. **Messaging** — Kafka deep dive (EOS, KRaft), RabbitMQ, Event Sourcing, CQRS, Outbox pattern
10. **Containers & Kubernetes** — runc/kata/gVisor, OCI image internals, K8s scheduler/RBAC/admission/networking/CNI/CSI
11. **Cloud Native** — GitOps (ArgoCD/Flux), service discovery, serverless cold starts
12. **Cloud Platforms** — AWS/GCP/Azure internals, Nitro, Andromeda, Spanner, BigQuery
13. **Network Security** — Zero Trust, DDoS mitigation, WAF evasion techniques, iptables/nftables, VPN/WireGuard, Zeek/Suricata
14. **Cloud Security** — IAM policy evaluation logic, IRSA, HashiCorp Vault secrets hierarchy, CSPM, Falco rules, GuardDuty detection categories, container SBOM/SLSA
15. **Observability** — RED/USE/4GS methods, OpenTelemetry, tail-based sampling, Prometheus internals, Gorilla compression, blameless postmortems
16. **IaC** — Terraform state mechanics, Helm templating, Kustomize overlays
17. **Cryptography** — AES-GCM nonce reuse consequences, ECC (Curve25519 vs P-256), EdDSA vs ECDSA, HSM/KMS key hierarchy, envelope encryption
18. **Performance** — Amdahl's law, flamegraphs, N+1 queries, connection pool sizing formulas, Rust/Go/JVM profiling
19. **DR & Chaos** — RTO/RPO/3-2-1 rule, multi-region patterns, Chaos Mesh, GameDay
20. **Advanced** — Bulkhead/backpressure, Flink watermarks, Data Mesh/Iceberg, Platform Engineering, FinOps