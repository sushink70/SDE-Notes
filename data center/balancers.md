# The Complete, In-Depth Guide to Load Balancers
> *A world-class reference for engineers who want to understand load balancing from first principles to production mastery.*

---

## Table of Contents

1. [What Problem Does a Load Balancer Solve?](#1-what-problem-does-a-load-balancer-solve)
2. [Mental Model: The Fundamental Abstraction](#2-mental-model-the-fundamental-abstraction)
3. [Core Vocabulary — Know Every Term Cold](#3-core-vocabulary--know-every-term-cold)
4. [OSI Model & Where Load Balancers Live](#4-osi-model--where-load-balancers-live)
5. [Types of Load Balancers](#5-types-of-load-balancers)
6. [Load Balancing Algorithms — Deep Dive](#6-load-balancing-algorithms--deep-dive)
7. [Health Checks — The Heartbeat of a Load Balancer](#7-health-checks--the-heartbeat-of-a-load-balancer)
8. [Session Persistence (Sticky Sessions)](#8-session-persistence-sticky-sessions)
9. [SSL/TLS Termination](#9-ssltls-termination)
10. [Connection Draining & Graceful Shutdown](#10-connection-draining--graceful-shutdown)
11. [Load Balancer Architectures](#11-load-balancer-architectures)
12. [DNS Load Balancing](#12-dns-load-balancing)
13. [Global Server Load Balancing (GSLB)](#13-global-server-load-balancing-gslb)
14. [Software vs Hardware Load Balancers](#14-software-vs-hardware-load-balancers)
15. [Reverse Proxy vs Forward Proxy vs Load Balancer](#15-reverse-proxy-vs-forward-proxy-vs-load-balancer)
16. [Rate Limiting & Traffic Shaping](#16-rate-limiting--traffic-shaping)
17. [Load Balancer Failure Modes & High Availability](#17-load-balancer-failure-modes--high-availability)
18. [Real-World Load Balancers: HAProxy, NGINX, Envoy, AWS ALB/NLB](#18-real-world-load-balancers-haproxy-nginx-envoy-aws-albnlb)
19. [Consistent Hashing — The Elegant Algorithm](#19-consistent-hashing--the-elegant-algorithm)
20. [Load Balancing in Microservices & Service Mesh](#20-load-balancing-in-microservices--service-mesh)
21. [Observability: Metrics, Logs, Tracing](#21-observability-metrics-logs-tracing)
22. [Security Considerations](#22-security-considerations)
23. [Implementing a Simple Load Balancer in Go, Python, C, Rust, C++](#23-implementing-a-simple-load-balancer-in-go-python-c-rust-c)
24. [Interview-Level Questions & Expert Answers](#24-interview-level-questions--expert-answers)
25. [Mental Models & Summary Cheatsheet](#25-mental-models--summary-cheatsheet)

---

## 1. What Problem Does a Load Balancer Solve?

### The Core Problem

Imagine a single server receiving 1,000,000 HTTP requests per second. No single machine can handle this. Even if it could, what happens when that machine crashes? Every user experiences downtime.

Two fundamental problems emerge:
- **Scalability** — One machine has limited CPU, RAM, and network bandwidth.
- **Availability** — One machine is a *single point of failure* (SPOF).

A **load balancer** is the solution to both. It is a system that sits between clients and a pool of servers, **distributing incoming traffic across multiple backend servers** so that:

1. No single server is overwhelmed.
2. If one server dies, others continue serving traffic.
3. You can add/remove servers without downtime.

```
WITHOUT LOAD BALANCER:
  Client 1 ──┐
  Client 2 ──┤──► [Single Server]  ← SPOF, bottleneck
  Client 3 ──┘

WITH LOAD BALANCER:
  Client 1 ──┐                     ┌──► [Server A]
  Client 2 ──┤──► [Load Balancer] ─┼──► [Server B]
  Client 3 ──┘                     └──► [Server C]
```

### Why Not Just Use More DNS?

You might think: "Why not just add multiple IP addresses in DNS?" This is called **DNS Round Robin** and it exists, but it has severe limitations:

- DNS responses are *cached* — clients keep using the same IP for minutes/hours even if the server dies.
- No health checking — DNS will still return dead server IPs.
- No fine-grained control over traffic distribution.

A real load balancer solves all of these.

---

## 2. Mental Model: The Fundamental Abstraction

Think of a load balancer like a **dispatcher at a restaurant**:

```
[Restaurant Analogy]

Customer walks in
       │
       ▼
  [Dispatcher/Host]  ← Load Balancer
       │
  ┌────┴────────────────────────┐
  │    Looks at:                │
  │    - Which tables are free? │  ← Health Checks
  │    - Which waiter is busy?  │  ← Load Metrics
  │    - VIP reservation?       │  ← Session Persistence
  └────┬────────────────────────┘
       │
  ┌────▼────┐  ┌─────────┐  ┌─────────┐
  │Waiter A │  │Waiter B │  │Waiter C │  ← Backend Servers
  └─────────┘  └─────────┘  └─────────┘
```

The dispatcher (load balancer) never cooks food — it only **routes** customers to the right table/waiter. This is the essential abstraction: **decoupling the entry point from the processing unit**.

---

## 3. Core Vocabulary — Know Every Term Cold

Before going deeper, here is every important term defined precisely:

| Term | Definition |
|------|-----------|
| **Backend / Upstream** | The pool of servers that actually process requests |
| **Frontend / Downstream** | The client-facing side of the load balancer |
| **VIP (Virtual IP)** | The single IP address clients connect to (the load balancer's public face) |
| **Pool / Server Farm** | The group of backend servers managed by the LB |
| **Node / Member** | A single server within the pool |
| **Health Check** | A periodic probe to determine if a backend is alive |
| **Round Robin** | Cycling through servers one by one in order |
| **Sticky Session** | Forcing the same client to always hit the same server |
| **Session Affinity** | Another name for sticky sessions |
| **Connection Draining** | Gracefully finishing existing connections before removing a server |
| **Failover** | Automatically switching traffic to a healthy server when one fails |
| **Active-Passive HA** | One LB handles traffic, another is on standby |
| **Active-Active HA** | Multiple LBs share traffic simultaneously |
| **ECMP** | Equal-Cost Multi-Path routing — multiple paths of equal cost |
| **NAT** | Network Address Translation — rewriting IP headers |
| **DSR (Direct Server Return)** | Response goes directly from server to client, not through LB |
| **SSL Termination** | LB decrypts HTTPS, forwards plain HTTP to backends |
| **SSL Passthrough** | LB forwards encrypted traffic unchanged |
| **L4 LB** | Operates at TCP/UDP layer (Transport Layer) |
| **L7 LB** | Operates at HTTP/HTTPS layer (Application Layer) |
| **Least Connections** | Route to the server with fewest active connections |
| **Weighted Round Robin** | Some servers get proportionally more traffic |
| **Consistent Hashing** | Deterministic routing based on a hash, minimizes redistribution |
| **Throughput** | Requests or bytes processed per second |
| **Latency** | Time for a request to complete |
| **P99 Latency** | 99th percentile latency — 99% of requests are faster than this |
| **Canary Deployment** | Sending small % of traffic to new version |
| **Blue/Green Deployment** | Two environments, switch all traffic at once |
| **Rate Limiting** | Throttling requests per IP/user to prevent abuse |
| **Circuit Breaker** | Stops sending requests to a failing backend temporarily |
| **Graceful Degradation** | Serving reduced functionality instead of full failure |

---

## 4. OSI Model & Where Load Balancers Live

### What is the OSI Model?

The **OSI (Open Systems Interconnection) model** is a conceptual framework that divides network communication into 7 layers. Each layer has a specific role.

```
OSI LAYER STACK
┌───────────────────────────────────────────────────┐
│  Layer 7 │ Application  │ HTTP, HTTPS, FTP, DNS   │
│  Layer 6 │ Presentation │ SSL/TLS, Encoding        │
│  Layer 5 │ Session      │ Sessions, Sockets        │
│  Layer 4 │ Transport    │ TCP, UDP, Ports           │
│  Layer 3 │ Network      │ IP Addresses, Routing     │
│  Layer 2 │ Data Link    │ MAC Addresses, Ethernet   │
│  Layer 1 │ Physical     │ Cables, Signals           │
└───────────────────────────────────────────────────┘
```

**Key insight**: Load balancers operate at different layers, and the layer determines what information they can see and act upon.

### L4 Load Balancer (Transport Layer)

An **L4 Load Balancer** sees:
- Source IP address
- Destination IP address
- TCP/UDP port numbers
- Connection state (SYN, ACK, etc.)

It **cannot** see:
- HTTP headers
- URLs/paths
- Cookies
- Request body content

```
L4 LOAD BALANCER FLOW:

Client: 192.168.1.5:54321 → VIP: 10.0.0.1:443
                │
                ▼
        [L4 Load Balancer]
        Sees: SRC IP, DST IP, PORT, TCP flags
        Decision: Hash(192.168.1.5) → Server B
                │
                ▼
        Server B: 10.0.0.5:443
```

**Pros of L4:**
- Extremely fast (no need to parse HTTP)
- Very low latency
- Works with any TCP/UDP protocol (databases, game servers, etc.)

**Cons of L4:**
- Cannot route based on URL path or HTTP headers
- Cannot do HTTP-specific features (cookie-based stickiness, URL rewriting)

### L7 Load Balancer (Application Layer)

An **L7 Load Balancer** sees *everything* L4 sees, plus:
- Full HTTP headers
- URL paths
- HTTP methods (GET, POST, etc.)
- Cookies
- Request body
- Host header (for virtual hosting)

```
L7 LOAD BALANCER FLOW:

Client → GET /api/users HTTP/1.1
         Host: api.example.com
         Cookie: session=abc123
                │
                ▼
        [L7 Load Balancer]
        Parses entire HTTP request
        Decision Matrix:
        ┌─────────────────────────────────────────────┐
        │  /api/*          → API Server Pool          │
        │  /static/*       → CDN / Static Servers     │
        │  /admin/*        → Admin Server Pool        │
        │  Cookie present  → Sticky to same server    │
        └─────────────────────────────────────────────┘
                │
                ▼
        Routes to API Server Pool → Server A
```

**Pros of L7:**
- Content-based routing (path, headers, cookies)
- Can modify requests/responses
- Better observability (can log URLs, status codes)
- Supports canary deployments by routing % of traffic

**Cons of L7:**
- Higher CPU overhead (must parse HTTP)
- Slightly higher latency than L4
- Only works for HTTP/HTTPS (or the specific protocol it understands)

---

## 5. Types of Load Balancers

### 5.1 Hardware Load Balancers

Dedicated physical appliances. Examples: F5 BIG-IP, Citrix ADC (formerly NetScaler).

```
[HARDWARE LOAD BALANCER]

  ┌──────────────────────────────────────┐
  │         F5 BIG-IP Appliance          │
  │  ┌──────────┐    ┌────────────────┐  │
  │  │ ASIC/FPGA│    │ Routing Engine │  │
  │  │ Hardware │    │ Health Checks  │  │
  │  │ Offload  │    │ SSL Offload    │  │
  │  └──────────┘    └────────────────┘  │
  │       Throughput: 100Gbps+           │
  │       Cost: $50,000 - $500,000       │
  └──────────────────────────────────────┘
```

**Use case**: Large enterprises, financial institutions, telcos. High cost, high performance, vendor support contracts.

### 5.2 Software Load Balancers

Run as software on commodity hardware or VMs. Examples: HAProxy, NGINX, Envoy, Traefik.

```
[SOFTWARE LOAD BALANCER ON COMMODITY SERVER]

  ┌──────────────────────────────────────┐
  │     Linux Server (e.g., 32-core)     │
  │  ┌───────────────────────────────┐   │
  │  │      HAProxy / NGINX          │   │
  │  │   (user-space process)        │   │
  │  └───────────────────────────────┘   │
  │       Throughput: 10-100Gbps         │
  │       Cost: $500 - $5,000            │
  └──────────────────────────────────────┘
```

### 5.3 Cloud Load Balancers

Fully managed services from cloud providers. Examples: AWS ALB/NLB/CLB, GCP Load Balancer, Azure Load Balancer.

```
[CLOUD LOAD BALANCER]

  User ──► [AWS ALB] ──► [EC2 Auto Scaling Group]
                │
                ├── Managed by AWS (no ops burden)
                ├── Auto-scales the LB itself
                ├── Integrates with ACM (certificates)
                └── WAF integration possible
```

### 5.4 Client-Side Load Balancing

The client itself holds a list of servers and picks one. Used in microservices (Netflix Ribbon, gRPC client-side LB).

```
[CLIENT-SIDE LOAD BALANCING]

  Service A has:
  server_list = ["10.0.1.1", "10.0.1.2", "10.0.1.3"]
  
  On each request:
  chosen = round_robin(server_list)
  connect_to(chosen)
  
  No centralized LB needed!
  But: each client must know about server changes.
```

**Decision Tree: Which Type to Use?**

```
START
  │
  ▼
Need multi-cloud / zero-ops?
  │
  ├── YES → Cloud Load Balancer (AWS ALB, GCP LB)
  │
  └── NO
       │
       ▼
     Need 100Gbps+ and have budget?
       │
       ├── YES → Hardware LB (F5, Citrix)
       │
       └── NO
            │
            ▼
          Microservices / containers?
            │
            ├── YES → Service Mesh (Envoy/Istio) or Client-Side LB
            │
            └── NO → Software LB (HAProxy / NGINX)
```

---

## 6. Load Balancing Algorithms — Deep Dive

The **algorithm** is the decision logic: given N servers, which one gets the next request?

### 6.1 Round Robin

**Concept**: Cycle through servers in order. Request 1 → Server A, Request 2 → Server B, Request 3 → Server C, Request 4 → Server A again.

```
Round Robin State Machine:

Servers: [A, B, C]
index = 0

Request 1 → A  (index becomes 1)
Request 2 → B  (index becomes 2)
Request 3 → C  (index becomes 0)
Request 4 → A  (index becomes 1)
...

FLOW:
[New Request]
     │
     ▼
 next = servers[index % N]
 index++
     │
     ▼
[Route to next]
```

**Implementation in Go:**
```go
type RoundRobin struct {
    servers []string
    index   uint64
}

func (rr *RoundRobin) Next() string {
    // atomic increment for thread safety
    idx := atomic.AddUint64(&rr.index, 1)
    return rr.servers[idx % uint64(len(rr.servers))]
}
```

**Implementation in Rust:**
```rust
use std::sync::atomic::{AtomicUsize, Ordering};

struct RoundRobin {
    servers: Vec<String>,
    index: AtomicUsize,
}

impl RoundRobin {
    fn next(&self) -> &str {
        let idx = self.index.fetch_add(1, Ordering::Relaxed);
        &self.servers[idx % self.servers.len()]
    }
}
```

**Pros**: Simple, fair, even distribution.  
**Cons**: Ignores server capacity differences; ignores actual load.  
**Best for**: Homogeneous servers with similar request costs.

---

### 6.2 Weighted Round Robin

**Concept**: Assign weights to servers. A server with weight 3 gets 3x as many requests as a server with weight 1.

```
Weighted Round Robin:

Server A: weight=3
Server B: weight=1
Server C: weight=2
Total weight = 6

Request sequence:
A, A, A, B, C, C, A, A, A, B, C, C ...

INTERNAL REPRESENTATION:
expanded_list = [A, A, A, B, C, C]
index cycles through this list
```

**Why it matters**: Real-world servers are heterogeneous. A 32-core machine should get more traffic than a 4-core machine. Weighted RR lets you express this.

**Smooth Weighted Round Robin (NGINX algorithm)**:

Instead of grouping all of server A's requests together (which causes bursts), a *smooth* algorithm interleaves them:

```
Smooth WRR (weights: A=5, B=1, C=1):

Each server has: effective_weight, current_weight
Step:  current_weight += effective_weight
Pick:  server with highest current_weight
After: winner's current_weight -= total_weight

Round 1: A(5) B(1) C(1) → Pick A → A(5-7=-2) B(1) C(1)
Round 2: A(3) B(2) C(2) → Pick A → A(3-7=-4) B(2) C(2)
Round 3: A(1) B(3) C(3) → Pick B → A(1) B(3-7=-4) C(3)
...
Result: A, A, B, A, C, A, B, A, A, C ... (evenly spread)
```

---

### 6.3 Least Connections

**Concept**: Always route to the server with the fewest active (ongoing) connections.

```
State:
  Server A: 100 active connections
  Server B: 50 active connections   ← pick this one
  Server C: 75 active connections

New request → Server B

FLOW DIAGRAM:
[New Request]
     │
     ▼
Scan all servers
     │
     ▼
Find min(active_connections)
     │
     ▼
Route to that server
     │
     ▼
Increment connection count
     │
     ▼
When connection ends → Decrement count
```

**Why it's better than Round Robin for variable-cost requests**: If some requests take 10ms and others take 5 seconds (e.g., video transcoding), Round Robin will pile up long requests on unlucky servers. Least Connections naturally rebalances.

**Implementation in C:**
```c
typedef struct {
    char *addr;
    int   active_conns;
} Server;

Server* least_connections(Server *servers, int n) {
    Server *best = &servers[0];
    for (int i = 1; i < n; i++) {
        if (servers[i].active_conns < best->active_conns) {
            best = &servers[i];
        }
    }
    return best;
}
```

**Cons**: Requires maintaining state (connection counts); needs atomic operations or locks in multi-threaded LBs.

---

### 6.4 Least Response Time

**Concept**: Route to the server with the lowest *combination* of active connections AND response latency.

```
Score = active_connections × avg_response_time

Server A: 10 connections × 5ms  = 50  → least score!
Server B:  5 connections × 20ms = 100
Server C:  3 connections × 50ms = 150

Route to Server A despite having most connections
(because it's faster overall)
```

This is more sophisticated than least connections alone. NGINX Plus implements this.

---

### 6.5 IP Hash (Source IP Hashing)

**Concept**: Hash the client's IP address to deterministically select a server. Same IP always goes to same server.

```
IP Hash:

client_ip = "192.168.1.50"
hash_value = hash("192.168.1.50") = 2847163
server_index = hash_value % num_servers
             = 2847163 % 3
             = 1
→ Always route to Server B (index 1)

FLOW:
[Request from IP X]
        │
        ▼
  hash(X) % N
        │
        ▼
[Fixed Server for this IP]
```

**Pros**: Natural session stickiness without cookies.  
**Cons**: If a server goes down, all its IP-mapped clients are suddenly remapped to different servers (losing session). Also, if many clients are behind a NAT (e.g., an office), they all have the same source IP and all hit the same server.

---

### 6.6 Random

**Concept**: Pick a server at random.

Surprisingly, **Random with 2 choices** (Power of Two Choices) is better than pure random:

```
POWER OF TWO CHOICES:

1. Pick 2 servers at random: Server A and Server C
2. Compare their load (connections, response time)
3. Pick the less loaded of the two

This gives near-optimal load distribution with O(1) 
overhead, avoiding the need to scan all N servers!

Proven by theory: 
  - Random: max load = O(log N / log log N)
  - Power of Two: max load = O(log log N)    ← much better!
```

---

### 6.7 Resource-Based (Adaptive)

The load balancer **asks** each server what its current resource utilization is (CPU %, memory %, queue depth) via an agent, and routes accordingly.

```
Agent runs on each server:

Server A Agent: { cpu: 85%, mem: 60%, queue: 50 }
Server B Agent: { cpu: 20%, mem: 30%, queue: 5  }  ← pick this
Server C Agent: { cpu: 55%, mem: 45%, queue: 25 }
```

Used by F5 BIG-IP in production.

---

### Algorithm Comparison Table

```
┌───────────────────┬──────────┬────────────┬──────────────────────────────┐
│ Algorithm         │ Overhead │ Stickiness │ Best Use Case                │
├───────────────────┼──────────┼────────────┼──────────────────────────────┤
│ Round Robin       │ O(1)     │ None       │ Homogeneous, stateless       │
│ Weighted RR       │ O(1)     │ None       │ Mixed server capacities      │
│ Least Connections │ O(N)     │ None       │ Variable request duration    │
│ Least Response    │ O(N)     │ None       │ Mixed latency workloads      │
│ IP Hash           │ O(1)     │ IP-based   │ Stateful sessions, NAT aware │
│ Random 2 Choices  │ O(1)     │ None       │ Large clusters, distributed  │
│ Resource-Based    │ O(N)     │ None       │ CPU/memory sensitive jobs    │
│ Consistent Hash   │ O(log N) │ Key-based  │ Caches, distributed systems  │
└───────────────────┴──────────┴────────────┴──────────────────────────────┘
```

---

## 7. Health Checks — The Heartbeat of a Load Balancer

A **health check** is how the load balancer knows whether a backend server is alive and capable of serving traffic. Without health checks, the LB would blindly send requests to dead servers.

### Types of Health Checks

#### 7.1 TCP Health Check

Simply attempt to open a TCP connection. If it succeeds, the server is "up."

```
LB → TCP SYN → Server:80
LB ← SYN-ACK ← Server        ✓ Server is UP
LB → RST → Server (close)

OR

LB → TCP SYN → Server:80
    (no response, timeout)    ✗ Server is DOWN
```

**Limitation**: TCP connection succeeding only means the port is open. The application inside might be completely broken (e.g., database connection pool exhausted, deadlock in business logic).

#### 7.2 HTTP Health Check

Makes an actual HTTP request to a specific endpoint.

```
LB → GET /health HTTP/1.1
     Host: server-a.internal
     
Server → HTTP/1.1 200 OK
         Content-Type: application/json
         {"status": "healthy", "db": "connected"}
         
LB: Status 200 → Server A is HEALTHY

OR

Server → HTTP/1.1 503 Service Unavailable
LB: Status 503 → Server A is UNHEALTHY → remove from pool
```

Best practice: `/health` or `/healthz` endpoint that:
1. Returns 200 if all dependencies (DB, cache, etc.) are fine
2. Returns 503/500 if any critical dependency is down

#### 7.3 Active vs Passive Health Checks

```
ACTIVE HEALTH CHECK:
LB proactively sends pings every N seconds
  └── Pro: Detects failures even with no traffic
  └── Con: Extra network overhead

PASSIVE HEALTH CHECK:
LB monitors real traffic responses
  └── Pro: Zero overhead, uses real data
  └── Con: Needs real traffic to detect failure
          A server with zero traffic appears "healthy"
```

#### 7.4 Health Check State Machine

```
        ┌─────────────────────────────────────────┐
        │                                         │
        ▼                                         │
   [UNKNOWN]                                      │
        │                                         │
        │ First probe succeeds                    │
        ▼                                         │
    [HEALTHY] ◄──────────────────┐                │
        │                        │                │
        │ N consecutive failures  │                │
        ▼                        │                │
  [UNHEALTHY] ─────────────────► M successes ─────┘
  (removed from pool)

Typical values: N=2 failures before DOWN, M=3 successes before UP
This hysteresis prevents "flapping" (rapidly going up/down)
```

#### 7.5 Health Check Parameters

```
health_check {
    interval:           5s    # How often to check
    timeout:            2s    # How long to wait for response
    healthy_threshold:  3     # Successes needed to become healthy
    unhealthy_threshold: 2    # Failures needed to become unhealthy
    path:               /healthz
    expected_status:    200
    expected_body:      "ok"  # Optional body match
}
```

---

## 8. Session Persistence (Sticky Sessions)

### The Problem

HTTP is stateless. But many applications store state **in-memory on the server** (e.g., shopping cart, user session). If a user's requests go to different servers, the session data isn't found.

```
WITHOUT STICKY SESSIONS:
Request 1 → Server A  (login, session stored on A)
Request 2 → Server B  (session not found → logged out!)
Request 3 → Server A  (session found again)

WITH STICKY SESSIONS:
Request 1 → Server A  (login, session stored on A)
Request 2 → Server A  (same server, session found ✓)
Request 3 → Server A  (always Server A)
```

### Implementation Methods

#### Method 1: Cookie-Based Stickiness

The LB inserts a cookie into the HTTP response identifying which server the client should stick to.

```
Client → GET / HTTP/1.1
         Host: example.com

LB creates cookie: SERVERID=serverA

LB → 200 OK
     Set-Cookie: SERVERID=serverA; Path=/; HttpOnly

Next request from same client:
Client → GET /cart HTTP/1.1
         Cookie: SERVERID=serverA

LB reads cookie → routes to Server A
```

This is called **LB-generated cookies** (or "insert mode" in HAProxy). The application doesn't need to know about it.

#### Method 2: Application Cookie

The application itself sets a cookie (e.g., `JSESSIONID` in Java apps), and the LB is configured to read this cookie to determine routing.

```
DECISION FLOW:
[Incoming Request]
        │
        ▼
Does request have JSESSIONID cookie?
        │
   ┌────┴────┐
   │YES      │NO
   ▼         ▼
Read value  Use normal algorithm
Hash it     (e.g., Round Robin)
Map to      Set cookie in response
server      for future stickiness
        │
        ▼
   [Route Request]
```

#### Method 3: IP Hash (as discussed in algorithms)

Simple but problematic with NAT. Not recommended for modern deployments.

### The Problem with Sticky Sessions

```
SERVER FAILURE WITH STICKY SESSIONS:

        Session Map:
        client_1 → Server A  ←── Server A crashes!
        client_2 → Server B
        client_3 → Server A  ←── Lost session!

Result: All clients stuck to Server A lose their sessions.
```

**The real solution**: Move session state OUT of the server into a shared store (Redis, Memcached). Then sticky sessions are unnecessary — any server can serve any client.

```
STATELESS ARCHITECTURE (best practice):

Client → [LB] → Server A (no local state)
                    │
                    └── Reads/Writes session from [Redis]
                                     ▲
Client → [LB] → Server B (no local state)
                    │
                    └── Reads/Writes session from [Redis]
```

---

## 9. SSL/TLS Termination

### What is SSL/TLS?

**SSL (Secure Sockets Layer)** and its successor **TLS (Transport Layer Security)** are cryptographic protocols that encrypt communication between clients and servers. When you see `https://`, TLS is in use.

**TLS Handshake** (simplified):
```
Client                         Server
  │── ClientHello ──────────────► │
  │◄─ ServerHello + Certificate ──│
  │── Key Exchange ──────────────► │
  │◄─ Finished ────────────────── │
  │══════ Encrypted Channel ══════│
```

This handshake is computationally expensive (asymmetric cryptography). The bulk encryption (symmetric) is cheap.

### SSL Termination at the Load Balancer

The LB decrypts incoming HTTPS traffic and forwards plain HTTP to backends.

```
CLIENT                    LOAD BALANCER              BACKEND
  │                            │                        │
  │─── HTTPS (encrypted) ─────►│                        │
  │                            │ Decrypt TLS             │
  │                            │─── HTTP (plain) ───────►│
  │                            │◄─── HTTP response ──────│
  │                            │ Encrypt TLS             │
  │◄── HTTPS (encrypted) ──────│                        │
  │                            │                        │

Pros:
  - Backends don't need TLS certs or crypto overhead
  - LB can inspect/modify HTTP headers
  - Centralized certificate management

Cons:
  - Traffic between LB and backends is unencrypted
  - LB becomes a security boundary (must be trusted)
```

### SSL Passthrough

The LB forwards encrypted traffic without decrypting it.

```
CLIENT                    LOAD BALANCER              BACKEND
  │                            │                        │
  │─── HTTPS (encrypted) ─────►│                        │
  │                            │ (cannot inspect)        │
  │                            │─── HTTPS (encrypted) ──►│
  │                            │◄─── HTTPS (encrypted) ──│
  │◄── HTTPS (encrypted) ──────│                        │

Pros:
  - End-to-end encryption
  - Backend has full control of TLS

Cons:
  - LB cannot do L7 routing (can't see HTTP headers)
  - Cannot do cookie-based stickiness
  - Each backend needs its own cert
```

### SSL Re-encryption (End-to-End TLS)

```
CLIENT ─── HTTPS ──► [LB] ─── HTTPS ──► BACKEND

LB terminates TLS from client, then creates new TLS to backend.
Provides end-to-end encryption AND lets LB inspect/route.
Higher CPU overhead.
```

### Certificate Management

```
MANUAL (old way):
  Generate CSR → Submit to CA → Get cert → Copy to LB → Renew every year
  
AUTOMATED (modern way):
  Use Let's Encrypt + ACME protocol
  LB auto-renews certs every 90 days
  Zero downtime, zero manual work
  
AWS ACM (Amazon Certificate Manager):
  Free certs, auto-renew, one-click attach to ALB
```

---

## 10. Connection Draining & Graceful Shutdown

### The Problem

If you abruptly remove a server from the pool (e.g., for deployment), active connections are immediately killed. Users see errors.

```
WITHOUT CONNECTION DRAINING:
  Server A has 500 active connections
  You remove it from pool
  → All 500 connections instantly terminated
  → 500 users get errors/disconnections
```

### Connection Draining

When a server is marked for removal:
1. Stop sending **new** connections to it.
2. Allow **existing** connections to complete naturally.
3. After a timeout (e.g., 30s), forcefully terminate remaining connections.

```
CONNECTION DRAINING STATE MACHINE:

    [ACTIVE] ─── "remove from pool" ──► [DRAINING]
                                              │
                                    No new connections
                                    Wait for existing to finish
                                              │
                              ┌──────────────┴──────────────┐
                              │                             │
                    All connections closed           Timeout reached
                              │                             │
                              ▼                             ▼
                          [REMOVED]                 Force close all
                                                    connections
                                                        │
                                                        ▼
                                                    [REMOVED]

Timeline:
t=0s:   Mark server for removal
t=0s:   Stop routing new connections to server
t=5s:   50 connections completed naturally
t=20s:  490 connections completed
t=30s:  Timeout reached, 10 connections force-closed
t=30s:  Server removed from pool
```

### Zero-Downtime Deployment Pattern

```
ROLLING DEPLOYMENT WITH DRAINING:

Step 1: Pool = [A, B, C]  all serving traffic

Step 2: Remove C from pool with draining
        Pool = [A, B] active  +  [C] draining

Step 3: Deploy new version to C
        C comes up, health check passes
        
Step 4: Add C back to pool
        Pool = [A, B, C_new]

Step 5: Repeat for B, then A
        
Result: Zero downtime, zero errors
```

---

## 11. Load Balancer Architectures

### 11.1 Single Load Balancer (Naive)

```
[Client] → [LB] → [Server A]
                 → [Server B]
                 → [Server C]

Problem: LB itself is a SPOF!
```

### 11.2 Active-Passive High Availability

Two LBs. One is active, one is on standby. If the active one dies, the passive one takes over using **VRRP** (Virtual Router Redundancy Protocol).

```
VRRP / KEEPALIVED:

          VIP: 10.0.0.1 (clients connect here)
                     │
          ┌──────────┴──────────┐
          │                     │
  [LB-1 ACTIVE]          [LB-2 PASSIVE]
  10.0.0.2               10.0.0.3
  Owns the VIP           Monitoring LB-1
          │
          │ VRRP heartbeats
          │ every 1 second
          │
  LB-1 crashes!
  
  LB-2 detects no heartbeat
  LB-2 sends gratuitous ARP:
    "I now own VIP 10.0.0.1"
  
  All traffic now flows to LB-2
  Failover time: ~1-3 seconds

PROS:
  - Simple, well-understood
  - Only one LB consuming resources at a time

CONS:
  - Standby LB is waste during normal operation
  - Failover takes 1-3 seconds (some connections drop)
```

### 11.3 Active-Active High Availability

Both LBs are active and share traffic, typically via DNS round robin or ECMP routing.

```
                DNS: example.com → [10.0.0.2, 10.0.0.3]
                               │
              ┌────────────────┴──────────────┐
              │                               │
      [LB-1 ACTIVE]                   [LB-2 ACTIVE]
      10.0.0.2                        10.0.0.3
      Handles 50% traffic             Handles 50% traffic
              │                               │
              └──────────────┬────────────────┘
                             │
                    ┌────────┴────────┐
                    │                 │
               [Server A]        [Server B]

PROS:
  - No wasted standby resource
  - Higher total throughput (2x)
  - Automatic load distribution across LBs

CONS:
  - Session state must be shared between LBs
    (or use sticky routing at DNS level)
  - More complex
```

### 11.4 Multi-Tier Load Balancing

Large-scale systems often have multiple layers of LBs.

```
MULTI-TIER ARCHITECTURE:

Internet
   │
   ▼
[BGP Anycast / DNS GSLB]     ← Tier 0: Global routing
   │
   ▼
[L4 LB Cluster]              ← Tier 1: Connection-level distribution
(Hardware or kernel-bypass)
   │
   ▼
[L7 LB Cluster]              ← Tier 2: HTTP routing, SSL termination
(HAProxy / NGINX / Envoy)
   │
   ▼
[Application Server Pool]    ← Tier 3: Actual app servers

Each tier scales independently.
L4 handles raw packet throughput.
L7 handles HTTP intelligence.
```

---

## 12. DNS Load Balancing

### How DNS Load Balancing Works

DNS (Domain Name System) maps hostnames to IP addresses. By returning multiple IPs for the same hostname, the DNS server itself distributes load.

```
DNS ROUND ROBIN:

Client asks: "What's the IP for api.example.com?"

DNS Server Response:
  10.0.0.1   (Server A)
  10.0.0.2   (Server B)
  10.0.0.3   (Server C)

Request 1: Client picks first IP (10.0.0.1) → Server A
Request 2: Next client picks first IP again...

OS/DNS resolver often rotates the list:
Request 1: [10.0.0.1, 10.0.0.2, 10.0.0.3] → picks 10.0.0.1
Request 2: [10.0.0.2, 10.0.0.3, 10.0.0.1] → picks 10.0.0.2
Request 3: [10.0.0.3, 10.0.0.1, 10.0.0.2] → picks 10.0.0.3
```

### TTL (Time To Live) — The Critical Parameter

Every DNS record has a TTL: how long clients cache the answer.

```
TTL=300: Clients cache for 5 minutes
         If Server A dies at t=0, clients keep hitting it for 5 minutes!

TTL=10:  Clients cache for only 10 seconds
         Faster failure detection, but more DNS queries = more load on DNS
```

**The TTL dilemma**: Low TTL = faster failover, more DNS load. High TTL = slower failover, less DNS load.

### DNS Load Balancing Limitations

```
1. No health checking by default
   DNS doesn't know if your server is down.

2. Client-side caching
   Even with TTL=0, OS caches, browsers cache, 
   corporate proxies cache. Hard to control.

3. Granular control is impossible
   Can't say "send 10% of traffic to new version"
   without complex DNS trickery.

4. Geographic accuracy depends on recursive resolver
   Client in Singapore using Google DNS (8.8.8.8 in US)
   may get US server IPs.
```

---

## 13. Global Server Load Balancing (GSLB)

GSLB routes users to the **geographically nearest** or **healthiest** data center.

### How GSLB Works

```
GSLB DECISION FLOW:

User in Singapore queries: api.example.com

GSLB DNS Server:
  Check: Singapore DC health? ✓ Healthy
  Check: Singapore DC latency? ✓ Low
  Return: 10.10.1.1 (Singapore DC IP)
  
User in London queries: api.example.com

GSLB DNS Server:
  Check: London DC health? ✗ Degraded
  Check: Failover? Frankfurt DC is healthy
  Return: 10.20.1.1 (Frankfurt DC IP)
```

### GSLB Algorithms

```
1. GEOGRAPHIC (Proximity-based):
   User IP → GeoIP lookup → Nearest DC
   
2. LATENCY-BASED:
   Periodically measure latency from DNS probes to each DC
   Route user to DC with lowest observed latency
   
3. HEALTH-BASED:
   Only return IPs of healthy DCs
   
4. WEIGHTED:
   Primary DC gets 90%, secondary gets 10%
   
5. ACTIVE-ACTIVE:
   All DCs serve traffic, no preference
   
6. ACTIVE-PASSIVE (Disaster Recovery):
   Primary DC handles all traffic
   Secondary DC only used if primary fails
```

### Anycast — A Different Approach to Global LB

**Anycast** is a routing technique where multiple servers *share the same IP address* globally. BGP routing automatically sends each user to the "nearest" one.

```
ANYCAST:

Same IP: 1.2.3.4 announced from multiple locations:
  - Singapore: announces 1.2.3.4
  - Frankfurt: announces 1.2.3.4
  - New York:  announces 1.2.3.4

User in Singapore → BGP routes them to Singapore's 1.2.3.4
User in Germany   → BGP routes them to Frankfurt's 1.2.3.4

Used by: Cloudflare, Google DNS (8.8.8.8), CDNs
```

---

## 14. Software vs Hardware Load Balancers

### Comparison

```
┌─────────────────────┬──────────────────────┬─────────────────────┐
│ Dimension           │ Hardware LB          │ Software LB         │
├─────────────────────┼──────────────────────┼─────────────────────┤
│ Throughput          │ 100Gbps+             │ 10-100Gbps          │
│ Latency             │ Microseconds         │ Sub-millisecond     │
│ Cost                │ $50K-$500K           │ $500-$5K (server)   │
│ SSL Offload         │ Hardware ASICs       │ Software (CPU)      │
│ Flexibility         │ Low (vendor-locked)  │ High (open source)  │
│ Operations          │ Complex (vendor CLI) │ Config files, APIs  │
│ Scalability         │ Vertical only        │ Horizontal          │
│ Cloud-native        │ Poor                 │ Excellent           │
│ Community/ecosystem │ Small                │ Large               │
└─────────────────────┴──────────────────────┴─────────────────────┘
```

### Kernel Bypass Technologies

Modern software LBs can approach hardware speeds using:

**DPDK (Data Plane Development Kit)**: Bypasses the Linux kernel's network stack entirely, processing packets in user-space at wire speed.

```
NORMAL PACKET PATH:
  NIC → Kernel (interrupt) → Kernel TCP stack → User space app
  Latency: ~50-100μs
  
DPDK PACKET PATH:
  NIC → DPDK driver (polling, no interrupt) → User space app
  Latency: ~1-5μs
  (Kernel is completely bypassed)
```

**XDP (eXpress Data Path)**: Allows running eBPF programs at the earliest point in the kernel's network stack.

```
XDP PACKET PATH:
  NIC → XDP hook (in driver) → eBPF program → Drop/Redirect/Pass
  Latency: ~5-20μs
  Used by: Cilium, Cloudflare's load balancer
```

---

## 15. Reverse Proxy vs Forward Proxy vs Load Balancer

These concepts are related but distinct. Many engineers confuse them.

### Forward Proxy

Sits **in front of clients**, forwards their requests to the internet. The server sees the proxy's IP, not the client's.

```
FORWARD PROXY:

Corporate Network:
[Employee's browser]
        │
        │ "I want google.com"
        ▼
[Corporate Proxy / Squid]  ← Forward Proxy
        │
        │ Forwards request
        ▼
  [google.com server]
  
Use cases:
  - Content filtering (block social media)
  - Caching (common pages cached at proxy)
  - Anonymization
  - Bypassing geo-restrictions (VPN-like)
```

### Reverse Proxy

Sits **in front of servers**, receives client requests on behalf of servers. The client sees the proxy's IP, not the server's.

```
REVERSE PROXY:

[External Client]
        │
        │ "I want example.com"
        ▼
[Reverse Proxy / NGINX]  ← Reverse Proxy
        │
        │ Forwards to internal server
        ▼
[Internal Server at 10.0.0.5]

Use cases:
  - Hide internal server IPs
  - SSL termination
  - Static file serving / caching
  - Compression
  - Request buffering
```

### Load Balancer

A **specialized reverse proxy** that distributes traffic across multiple backend servers.

```
COMPARISON TABLE:
┌────────────────────┬────────────────┬────────────────┬─────────────────┐
│ Feature            │ Forward Proxy  │ Reverse Proxy  │ Load Balancer   │
├────────────────────┼────────────────┼────────────────┼─────────────────┤
│ Sits in front of   │ Clients        │ Servers        │ Servers         │
│ Multiple backends  │ No             │ Maybe          │ Yes (core)      │
│ Hides from client  │ Servers        │ Servers        │ Servers         │
│ Hides from server  │ Clients        │ Clients        │ Clients         │
│ Traffic dist.      │ No             │ Maybe          │ Yes (core)      │
│ Health checking    │ No             │ No             │ Yes             │
│ Common tools       │ Squid          │ NGINX, Caddy   │ HAProxy, NGINX  │
└────────────────────┴────────────────┴────────────────┴─────────────────┘
```

**Key insight**: Every load balancer IS a reverse proxy, but not every reverse proxy IS a load balancer.

---

## 16. Rate Limiting & Traffic Shaping

### Rate Limiting

Restrict how many requests a client (IP, user, API key) can make in a time window.

```
WITHOUT RATE LIMITING:
  Bot sends 100,000 req/sec from one IP
  → Overwhelms servers
  → DoS for legitimate users

WITH RATE LIMITING:
  Rule: Max 1,000 req/minute per IP
  Bot exceeds limit → receives 429 Too Many Requests
  Legitimate user (100 req/min) → unaffected
```

### Rate Limiting Algorithms

#### Token Bucket

```
TOKEN BUCKET ALGORITHM:

Bucket has capacity C (e.g., 100 tokens)
Tokens refill at rate R (e.g., 10 tokens/second)

On each request:
  If bucket has ≥1 token: consume 1 token, allow request
  Else: reject request (429)

State:
  bucket = 100  ← starts full
  
Request burst of 100 in 1 second:
  All 100 allowed (consumed tokens)
  bucket = 0
  
Next request: bucket = 0 → REJECTED

After 10 seconds: bucket = 100 again (refilled)

BENEFIT: Allows short bursts up to capacity C
```

#### Leaky Bucket

```
LEAKY BUCKET ALGORITHM:

Requests fill a queue (bucket) at any rate
Queue drains at a fixed rate R (e.g., 100 req/sec)

If queue is full → request is dropped

   Requests arrive      Queue           Output
   ─────────────►   ┌──────────┐   ──────────────►
   (any rate)       │          │   (fixed rate R)
                    │          │
                    │          │
                    └──────────┘
                     capacity C

BENEFIT: Smooths bursty traffic into a constant rate
DRAWBACK: Bursts are always delayed/dropped
```

#### Fixed Window Counter

```
FIXED WINDOW:
  Window: every 60 seconds
  Limit: 100 requests

  t=0:  window starts, count=0
  t=30: 100 requests → count=100 → LIMIT REACHED
  t=60: New window, count=0 → 100 more allowed

PROBLEM:
  t=59: 100 requests in 1 second (just before window resets)
  t=60: 100 requests in 1 second (new window)
  = 200 requests in 2 seconds! Doubles the rate.
```

#### Sliding Window Log / Counter

```
SLIDING WINDOW:
  Limit: 100 requests per minute
  
  Instead of a fixed window, maintain a log of timestamps
  At each request:
    Remove timestamps older than 1 minute
    Count remaining timestamps
    If count < 100: allow, add timestamp
    Else: reject
    
BENEFIT: No boundary exploitation
DRAWBACK: Memory overhead (store all timestamps)

SLIDING WINDOW COUNTER (approximation):
  count ≈ (prev_window_count × overlap_ratio) + curr_window_count
  where overlap_ratio = remaining_seconds / window_size
  
  Very memory efficient, small error margin (~0.1%)
  Used by Redis + Lua in production
```

---

## 17. Load Balancer Failure Modes & High Availability

### Common Failure Modes

```
FAILURE MODE 1: Backend Server Crash
  Detection: Health check fails
  Response:  Remove from pool within 1-2 health check intervals
  Impact:    In-flight requests to that server fail

FAILURE MODE 2: Backend Server Slowdown (not crash)
  Detection: Harder! Server is "up" but slow
  Response:  Circuit breaker, timeout + retry elsewhere
  Impact:    Latency spike

FAILURE MODE 3: Load Balancer Crash
  Detection: VRRP heartbeat missed by passive LB
  Response:  Passive takes over (Active-Passive HA)
  Impact:    ~1-3s downtime for existing connections

FAILURE MODE 4: Network Partition
  Some clients can't reach LB, or LB can't reach some servers
  Detection: LB may mark healthy servers as down (false positive)
  Response:  Timeout tuning, multiple health check paths

FAILURE MODE 5: Thundering Herd
  LB restarts, all connections rush in simultaneously
  Response:  Slow start, connection rate limiting on LB itself

FAILURE MODE 6: Cascade Failure
  Server A is slow → LB queues more requests to it
  Queue grows → A is even slower → eventually crashes
  Other servers get overloaded too → cascade
  Response:  Circuit breaker pattern
```

### Circuit Breaker Pattern

Named after an electrical circuit breaker. Stops sending requests to a failing service to allow it to recover.

```
CIRCUIT BREAKER STATE MACHINE:

      error_rate < threshold        error_rate > threshold
           │                                │
           │                                │
    ┌──────▼──────┐    too many errors ┌────▼─────┐
    │   CLOSED    │─────────────────────►   OPEN   │
    │  (normal)   │                    │ (failing) │
    └─────────────┘◄───────────────────└─────┬─────┘
           ▲        some success               │
           │                                  │ timer expires
           │                           ┌──────▼──────┐
           └────── success ────────────│  HALF-OPEN  │
                                       │  (testing)  │
                                       └─────────────┘

CLOSED state:
  Requests pass through normally
  Error rate monitored

OPEN state:
  Requests FAIL IMMEDIATELY (no network call made)
  This prevents overloading the struggling service
  After timeout (e.g., 30s) → move to HALF-OPEN

HALF-OPEN state:
  Let a few test requests through
  If success: close the circuit (back to normal)
  If failure: open it again (still broken)
```

---

## 18. Real-World Load Balancers: HAProxy, NGINX, Envoy, AWS ALB/NLB

### 18.1 HAProxy

The gold standard for TCP/HTTP load balancing. Battle-tested, extremely performant, minimal resource use.

```
HAPROXY ARCHITECTURE:

Single-process model with event loop
(similar to nginx):

  ┌──────────────────────────────────────────┐
  │              HAProxy Process             │
  │                                          │
  │  ┌──────────┐   ┌─────────────────────┐  │
  │  │ Frontend │   │      Backend        │  │
  │  │ (listen) │──►│  (server pool +     │  │
  │  │  :80     │   │   algorithm +       │  │
  │  │  :443    │   │   health checks)    │  │
  │  └──────────┘   └─────────────────────┘  │
  │                                          │
  │  Event loop (epoll) handles 100K+ conns  │
  └──────────────────────────────────────────┘
```

**Sample HAProxy Config (annotated):**
```
global
    maxconn 100000        # Max simultaneous connections
    nbthread 8            # Use 8 CPU threads

defaults
    mode http             # L7 HTTP mode
    timeout connect 5s    # Backend connection timeout
    timeout client  30s   # Client inactivity timeout
    timeout server  30s   # Backend inactivity timeout

frontend http_front
    bind *:80             # Listen on all IPs, port 80
    bind *:443 ssl crt /etc/ssl/cert.pem  # HTTPS with SSL termination
    
    # Content-based routing
    acl is_api path_beg /api
    use_backend api_pool if is_api
    default_backend web_pool

backend web_pool
    balance roundrobin    # Algorithm
    option httpchk GET /healthz  # Health check
    server web1 10.0.0.1:8080 check weight 1
    server web2 10.0.0.2:8080 check weight 1
    server web3 10.0.0.3:8080 check weight 2  # Gets 2x traffic

backend api_pool
    balance leastconn     # Least connections for API
    server api1 10.0.1.1:8080 check
    server api2 10.0.1.2:8080 check
```

### 18.2 NGINX as Load Balancer

NGINX is primarily a web server but also an excellent L7 LB and reverse proxy.

```
NGINX UPSTREAM CONFIGURATION:

http {
    upstream backend {
        least_conn;           # Algorithm: least connections
        
        server 10.0.0.1:8080 weight=3;
        server 10.0.0.2:8080 weight=1;
        server 10.0.0.3:8080 backup;  # Only used if others fail
    }

    server {
        listen 80;
        
        location /api/ {
            proxy_pass http://backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }
}
```

### 18.3 Envoy Proxy

Modern, cloud-native proxy written in C++. Used as the data plane in Istio service mesh.

```
ENVOY ARCHITECTURE:

  ┌─────────────────────────────────────────────────────┐
  │                    Envoy Process                    │
  │                                                     │
  │  ┌──────────┐    ┌──────────┐    ┌──────────────┐  │
  │  │Listeners │───►│ Filters  │───►│   Clusters   │  │
  │  │(frontends│    │(L3/L4/L7)│    │(backend pools│  │
  │  │ :8080)   │    │ chain    │    │ + discovery) │  │
  │  └──────────┘    └──────────┘    └──────────────┘  │
  │                                                     │
  │  xDS API: dynamically configured via control plane  │
  └─────────────────────────────────────────────────────┘
  
Key differentiator: DYNAMIC CONFIGURATION
  No need to reload/restart for config changes.
  Control plane (Istio) pushes config updates via gRPC.
```

### 18.4 AWS Application Load Balancer (ALB)

Managed L7 LB. Integrates deeply with AWS ecosystem.

```
AWS ALB FEATURES:

  ┌──────────────────────────────────────────────────┐
  │                   AWS ALB                        │
  │                                                  │
  │  Rules Engine:                                   │
  │  IF host = api.example.com → Target Group A      │
  │  IF path = /images/* → Target Group B (S3)       │
  │  IF header X-Beta = true → Target Group C (beta) │
  │  DEFAULT → Target Group D                        │
  │                                                  │
  │  Features:                                       │
  │  - Native ECS/EKS integration                   │
  │  - WAF (Web Application Firewall) integration   │
  │  - Certificate management via ACM               │
  │  - Access logs to S3                            │
  │  - CloudWatch metrics                           │
  └──────────────────────────────────────────────────┘
```

### 18.5 AWS Network Load Balancer (NLB)

Managed L4 LB. Ultra-low latency, handles millions of requests per second.

```
ALB vs NLB COMPARISON:

┌─────────────────────┬─────────────────┬──────────────────┐
│ Feature             │ ALB (L7)        │ NLB (L4)         │
├─────────────────────┼─────────────────┼──────────────────┤
│ Protocol            │ HTTP, HTTPS,    │ TCP, UDP, TLS    │
│                     │ WebSocket, HTTP2│                  │
│ Routing             │ Path, Headers,  │ IP:Port only     │
│                     │ Host, Query     │                  │
│ Latency             │ ~1ms            │ ~100μs           │
│ Static IP           │ No              │ Yes              │
│ Preserve client IP  │ Via header      │ Native (default) │
│ Use case            │ Web apps, APIs  │ TCP, gaming, IoT │
│ WebSockets          │ Yes             │ Yes              │
│ SSL termination     │ Yes             │ Yes              │
└─────────────────────┴─────────────────┴──────────────────┘
```

---

## 19. Consistent Hashing — The Elegant Algorithm

### The Problem with Naive Hashing

Suppose you have N servers and route requests using `hash(key) % N`:

```
N=3 servers: [A, B, C]
key "user_123" → hash = 456789 → 456789 % 3 = 0 → Server A

Now add a 4th server D:
key "user_123" → hash = 456789 → 456789 % 4 = 1 → Server B ← DIFFERENT!

Adding just ONE server remaps ~(N-1)/N ≈ 75% of all keys!
This kills cache hit rates and invalidates sessions.
```

### Consistent Hashing Solution

Map both servers and keys onto a **circular ring** (hash ring). A key is assigned to the first server encountered when moving clockwise on the ring.

```
CONSISTENT HASH RING (conceptual):

         0
    315 ──── 45
   /              \
  │    key_B(30)   │
270│    srv_A(60)   │90
  │    key_C(120)  │
   \    srv_B(180) /
    225 ──── 135
        180

Keys are assigned to the next server clockwise:
  key_B (30) → srv_A (60)  [next clockwise]
  key_C (120) → srv_B (180) [next clockwise]
  
Adding server srv_C at position 100:
  key_B (30) → still srv_A (60)   [unchanged!]
  key_C (120) → srv_C (100)?? No, 120 > 100, next is srv_B (180)
  
Only keys between srv_A (60) and srv_C (100) are remapped!
That's only 1/N fraction of all keys, not 75%.
```

### Virtual Nodes

A problem: with few real servers, the ring is unbalanced. Server A might own 60% of the ring, Server B only 20%.

**Solution**: Each physical server gets V *virtual nodes* spread across the ring.

```
VIRTUAL NODES (vnodes):

Without vnodes (unbalanced):
Ring: ── A ─────────────── B ─── C ──
       (A has 60%, B has 25%, C has 15%)

With vnodes (balanced):
Each server has 3 virtual nodes:
Ring: ── A1 ── C2 ── B1 ── A2 ── C1 ── B2 ── A3 ── B3 ── C3 ──
       Each server owns ~33% of ring

Adding a server: redistribute from all existing servers' vnodes
Removing a server: its vnodes' keys go to next real server's vnodes
```

### Consistent Hashing in Python

```python
import hashlib
import bisect

class ConsistentHashRing:
    def __init__(self, nodes=None, vnodes=150):
        self.vnodes = vnodes
        self.ring = {}       # hash_pos → server_name
        self.sorted_keys = []  # sorted list of hash positions
        
        if nodes:
            for node in nodes:
                self.add_node(node)
    
    def _hash(self, key: str) -> int:
        return int(hashlib.md5(key.encode()).hexdigest(), 16)
    
    def add_node(self, node: str):
        for i in range(self.vnodes):
            vnode_key = f"{node}:vnode:{i}"
            h = self._hash(vnode_key)
            self.ring[h] = node
            bisect.insort(self.sorted_keys, h)
    
    def remove_node(self, node: str):
        for i in range(self.vnodes):
            vnode_key = f"{node}:vnode:{i}"
            h = self._hash(vnode_key)
            del self.ring[h]
            self.sorted_keys.remove(h)
    
    def get_node(self, key: str) -> str:
        if not self.ring:
            return None
        h = self._hash(key)
        # Find first position >= h (clockwise)
        idx = bisect.bisect(self.sorted_keys, h)
        if idx == len(self.sorted_keys):
            idx = 0  # wrap around
        return self.ring[self.sorted_keys[idx]]

# Usage
ring = ConsistentHashRing(["server_a", "server_b", "server_c"])
print(ring.get_node("user_123"))   # e.g., "server_b"
print(ring.get_node("user_456"))   # e.g., "server_a"
ring.add_node("server_d")
print(ring.get_node("user_123"))   # still "server_b" (likely unchanged)
```

### Consistent Hashing in Go

```go
package main

import (
    "crypto/md5"
    "encoding/binary"
    "fmt"
    "sort"
    "sync"
)

type HashRing struct {
    mu       sync.RWMutex
    ring     map[uint32]string
    sortedKeys []uint32
    vnodes   int
}

func NewHashRing(vnodes int) *HashRing {
    return &HashRing{
        ring:   make(map[uint32]string),
        vnodes: vnodes,
    }
}

func (hr *HashRing) hash(key string) uint32 {
    h := md5.Sum([]byte(key))
    return binary.BigEndian.Uint32(h[:4])
}

func (hr *HashRing) AddNode(node string) {
    hr.mu.Lock()
    defer hr.mu.Unlock()
    for i := 0; i < hr.vnodes; i++ {
        key := fmt.Sprintf("%s:vnode:%d", node, i)
        h := hr.hash(key)
        hr.ring[h] = node
        hr.sortedKeys = append(hr.sortedKeys, h)
    }
    sort.Slice(hr.sortedKeys, func(i, j int) bool {
        return hr.sortedKeys[i] < hr.sortedKeys[j]
    })
}

func (hr *HashRing) GetNode(key string) string {
    hr.mu.RLock()
    defer hr.mu.RUnlock()
    if len(hr.ring) == 0 {
        return ""
    }
    h := hr.hash(key)
    idx := sort.Search(len(hr.sortedKeys), func(i int) bool {
        return hr.sortedKeys[i] >= h
    })
    if idx == len(hr.sortedKeys) {
        idx = 0 // wrap around
    }
    return hr.ring[hr.sortedKeys[idx]]
}
```

---

## 20. Load Balancing in Microservices & Service Mesh

### The Problem with Centralized LB in Microservices

In a microservices architecture, Service A might call Service B, C, D, E. If all traffic goes through a central LB:

```
CENTRALIZED LB IN MICROSERVICES:

Service A → [Central LB] → Service B
Service A → [Central LB] → Service C
Service B → [Central LB] → Service D

Problems:
1. LB becomes bottleneck for internal traffic
2. Extra network hop for every service call
3. LB doesn't understand service-specific protocols (gRPC, etc.)
4. Hard to implement service-specific policies
```

### Client-Side Load Balancing (The Microservices Way)

```
CLIENT-SIDE LB IN MICROSERVICES:

Service A has LB logic built-in:
  service_b_instances = service_discovery.lookup("service-b")
  # Returns: ["10.0.0.1:8080", "10.0.0.2:8080", "10.0.0.3:8080"]
  
  chosen = round_robin(service_b_instances)
  call(chosen, request)

Service A does LB itself — no central bottleneck!

Used by:
  - Netflix Ribbon (Java)
  - gRPC (built-in client-side LB)
  - Kubernetes kube-proxy (at pod level)
```

### Service Mesh (Sidecar Pattern)

A **service mesh** moves the LB/networking logic into a **sidecar proxy** that runs alongside each service.

```
SERVICE MESH ARCHITECTURE:

┌────────────────────────────────────┐
│  Pod / Container Group             │
│  ┌──────────────┐ ┌─────────────┐  │
│  │  Your App    │ │   Envoy     │  │
│  │  (Service A) │ │   Sidecar   │  │
│  │              │ │             │  │
│  └──────┬───────┘ └──────┬──────┘  │
│         │    localhost   │         │
│         └───────────────►│         │
└─────────────────────────┼──────────┘
                          │
                          │ mTLS, LB, retries
                          │ circuit breaking
                          ▼
┌─────────────────────────────────────┐
│  Pod / Container Group             │
│  ┌──────────────┐ ┌─────────────┐  │
│  │  Your App    │ │   Envoy     │  │
│  │  (Service B) │ │   Sidecar   │  │
│  └──────────────┘ └─────────────┘  │
└────────────────────────────────────┘

Control Plane (Istio / Linkerd) configures all sidecars:
  - Load balancing algorithms
  - Retries and timeouts
  - Circuit breakers
  - mTLS between services
  - Traffic shifting (canary)
```

### Kubernetes Load Balancing

```
KUBERNETES NETWORKING LAYERS:

External Traffic
      │
      ▼
┌─────────────────────────────────────────────────┐
│  Ingress Controller (NGINX / Traefik / Envoy)   │  ← L7 LB
│  Routes based on host/path                       │
└────────────────────┬────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────┐
│  Kubernetes Service (ClusterIP)                 │  ← L4 LB
│  kube-proxy sets up iptables/IPVS rules         │
│  Distributes to matching Pods                   │
└────────────────────┬────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
      [Pod A]     [Pod B]     [Pod C]

Service Types:
  ClusterIP:   Internal only (virtual IP within cluster)
  NodePort:    Expose on all nodes at static port
  LoadBalancer: Request cloud LB (AWS NLB, GCP LB)
  ExternalName: DNS alias
```

---

## 21. Observability: Metrics, Logs, Tracing

### Key Metrics for a Load Balancer

```
GOLDEN SIGNALS (Google SRE Book):

1. LATENCY
   - p50, p95, p99, p999 response time
   - Backend response time (separate from client)
   
2. TRAFFIC
   - Requests per second (RPS)
   - Bytes in/out per second
   - Active connections
   
3. ERRORS
   - HTTP 4xx rate (client errors)
   - HTTP 5xx rate (server errors)
   - Connection timeouts
   - Backend errors
   
4. SATURATION
   - Connection pool utilization (% of max)
   - Queue depth
   - CPU / Memory of LB process
   
LB-SPECIFIC METRICS:
   - Requests per backend (is load balanced evenly?)
   - Backend health status (up/down/unknown)
   - Health check failure rate
   - Session persistence hits/misses
   - SSL handshake time
   - Connection draining queue length
```

### Access Log Format

```
HAProxy Log Example:
  192.168.1.5:54321 [26/Mar/2026:14:23:45.123] http_front api_pool/server2
  0/0/1/52/53 200 1234 - - ---- 10/8/4/2/0 0/0
  {api.example.com} "GET /api/users HTTP/1.1"
  
Fields:
  192.168.1.5:54321  → Client IP:port
  14:23:45.123       → Timestamp
  http_front         → Frontend name
  api_pool/server2   → Backend pool / chosen server
  0/0/1/52/53        → Timings: Tq/Tw/Tc/Tr/Tt (ms)
                       Tq: Time waiting in queue
                       Tw: Time waiting for connection slot
                       Tc: Time to connect to backend
                       Tr: Time for backend to reply
                       Tt: Total time
  200                → HTTP status code
  1234               → Bytes transferred
  10/8/4/2/0         → Concurrent connections
  "GET /api/users"   → Request line
```

### Distributed Tracing with Load Balancers

```
REQUEST TRACE THROUGH LB:

Client → LB → Server A → Database

TraceID: abc-123 (injected by LB or client)
  │
  ├── Span 1: LB processing (1ms)
  │     LB adds: X-Request-ID: abc-123
  │               X-Forwarded-For: client-ip
  │
  ├── Span 2: Server A processing (50ms)
  │     Server logs TraceID: abc-123
  │
  └── Span 3: Database query (5ms)
        Database logs TraceID: abc-123

Result: Full request trace from client to DB
        Visible in Jaeger / Zipkin / AWS X-Ray
```

---

## 22. Security Considerations

### DDoS Mitigation at the LB Layer

```
DDOS ATTACK TYPES AND LB RESPONSES:

1. VOLUMETRIC ATTACK (bandwidth exhaustion):
   1,000,000 requests/sec from many IPs
   Response: Rate limiting per IP, per subnet, global limits
             Upstream scrubbing (Cloudflare, AWS Shield)

2. TCP SYN FLOOD:
   Millions of half-open TCP connections
   Response: SYN cookies (kernel feature)
             Connection rate limiting

3. HTTP FLOOD (Layer 7):
   Legitimate-looking HTTP requests, just too many
   Response: L7 rate limiting, CAPTCHAs, JavaScript challenges
             WAF with behavioral analysis

4. SLOWLORIS:
   Hold many connections open, send headers very slowly
   Exhausts connection table
   Response: connection timeout, max connection per IP limits
```

### WAF Integration

```
WAF (Web Application Firewall) at LB:

Client
  │
  ▼
[Load Balancer]
  │
  ├── WAF Rules Check:
  │     - SQL injection patterns → Block
  │     - XSS patterns → Block
  │     - Known bad IPs/ASNs → Block
  │     - OWASP Top 10 patterns → Block
  │
  ▼ (only clean traffic passes)
[Backend Servers]
```

### X-Forwarded-For Header

```
Without LB, server sees client IP directly.
With LB, server sees LB's IP.

SOLUTION: X-Forwarded-For header
  LB adds: X-Forwarded-For: <original-client-ip>
  
  If multiple LBs in chain:
  X-Forwarded-For: <client-ip>, <lb1-ip>, <lb2-ip>
  
  Rightmost IP is most recently added (most trustworthy)
  Leftmost IP is what the client claims (can be spoofed)
  
SAFER ALTERNATIVE:
  PROXY Protocol (HAProxy): Prepends binary header with
  real client IP at TCP level. Cannot be spoofed by clients
  because it's injected before the HTTP layer.
```

---

## 23. Implementing a Simple Load Balancer

### In Go (Most Production-Like)

```go
package main

import (
    "fmt"
    "log"
    "net/http"
    "net/http/httputil"
    "net/url"
    "sync/atomic"
)

// Backend represents a single server
type Backend struct {
    URL          *url.URL
    Alive        atomic.Bool
    ReverseProxy *httputil.ReverseProxy
}

// LoadBalancer manages the pool and routing
type LoadBalancer struct {
    backends []*Backend
    current  atomic.Uint64
}

func NewLoadBalancer(urls []string) *LoadBalancer {
    lb := &LoadBalancer{}
    for _, rawURL := range urls {
        u, err := url.Parse(rawURL)
        if err != nil {
            log.Fatalf("Invalid URL %s: %v", rawURL, err)
        }
        proxy := httputil.NewSingleHostReverseProxy(u)
        b := &Backend{URL: u, ReverseProxy: proxy}
        b.Alive.Store(true)
        lb.backends = append(lb.backends, b)
    }
    return lb
}

// nextBackend returns the next healthy backend using round-robin
func (lb *LoadBalancer) nextBackend() *Backend {
    n := uint64(len(lb.backends))
    for i := uint64(0); i < n; i++ {
        idx := lb.current.Add(1) % n
        if lb.backends[idx].Alive.Load() {
            return lb.backends[idx]
        }
    }
    return nil // all backends down
}

// ServeHTTP implements the http.Handler interface
func (lb *LoadBalancer) ServeHTTP(w http.ResponseWriter, r *http.Request) {
    backend := lb.nextBackend()
    if backend == nil {
        http.Error(w, "No healthy backends", http.StatusServiceUnavailable)
        return
    }
    // Forward real client IP
    r.Header.Set("X-Forwarded-For", r.RemoteAddr)
    backend.ReverseProxy.ServeHTTP(w, r)
}

func main() {
    backends := []string{
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
    }
    lb := NewLoadBalancer(backends)
    
    fmt.Println("Load Balancer running on :8080")
    log.Fatal(http.ListenAndServe(":8080", lb))
}
```

### In Python (asyncio for performance)

```python
import asyncio
import aiohttp
from aiohttp import web
import itertools

class LoadBalancer:
    def __init__(self, backends: list[str]):
        self.backends = backends
        self._cycle = itertools.cycle(backends)
    
    def next_backend(self) -> str:
        return next(self._cycle)
    
    async def handle(self, request: web.Request) -> web.Response:
        backend_url = self.next_backend()
        target_url = f"{backend_url}{request.path_qs}"
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.request(
                    method=request.method,
                    url=target_url,
                    headers={**request.headers, 
                             "X-Forwarded-For": request.remote},
                    data=await request.read()
                ) as resp:
                    body = await resp.read()
                    return web.Response(
                        status=resp.status,
                        headers=dict(resp.headers),
                        body=body
                    )
            except aiohttp.ClientError as e:
                return web.Response(status=502, text=f"Bad Gateway: {e}")

def main():
    backends = [
        "http://localhost:8081",
        "http://localhost:8082",
        "http://localhost:8083",
    ]
    lb = LoadBalancer(backends)
    app = web.Application()
    app.router.add_route("*", "/{path_info:.*}", lb.handle)
    web.run_app(app, host="0.0.0.0", port=8080)

if __name__ == "__main__":
    main()
```

### In Rust (high-performance, production-quality structure)

```rust
use std::sync::{Arc, atomic::{AtomicUsize, Ordering}};
use std::net::SocketAddr;
use tokio::net::{TcpListener, TcpStream};
use tokio::io::{self, AsyncWriteExt};

#[derive(Debug, Clone)]
struct Backend {
    addr: SocketAddr,
}

struct LoadBalancer {
    backends: Vec<Backend>,
    counter: Arc<AtomicUsize>,
}

impl LoadBalancer {
    fn new(addrs: &[&str]) -> Self {
        let backends = addrs.iter()
            .map(|a| Backend { addr: a.parse().unwrap() })
            .collect();
        Self {
            backends,
            counter: Arc::new(AtomicUsize::new(0)),
        }
    }
    
    fn next_backend(&self) -> &Backend {
        let idx = self.counter.fetch_add(1, Ordering::Relaxed);
        &self.backends[idx % self.backends.len()]
    }
}

async fn proxy_connection(
    mut client: TcpStream,
    backend_addr: SocketAddr,
) -> io::Result<()> {
    let mut server = TcpStream::connect(backend_addr).await?;
    let (mut cr, mut cw) = client.split();
    let (mut sr, mut sw) = server.split();
    
    tokio::select! {
        _ = tokio::io::copy(&mut cr, &mut sw) => {},
        _ = tokio::io::copy(&mut sr, &mut cw) => {},
    }
    Ok(())
}

#[tokio::main]
async fn main() -> io::Result<()> {
    let lb = Arc::new(LoadBalancer::new(&[
        "127.0.0.1:8081",
        "127.0.0.1:8082",
        "127.0.0.1:8083",
    ]));
    
    let listener = TcpListener::bind("0.0.0.0:8080").await?;
    println!("Load Balancer listening on :8080");
    
    loop {
        let (client, _) = listener.accept().await?;
        let backend = lb.next_backend().addr;
        tokio::spawn(async move {
            if let Err(e) = proxy_connection(client, backend).await {
                eprintln!("Proxy error: {}", e);
            }
        });
    }
}
```

### In C (TCP L4 Proxy, raw sockets)

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>

#define FRONTEND_PORT 8080
#define BUF_SIZE      65536

typedef struct {
    const char *ip;
    int         port;
} Backend;

static Backend backends[] = {
    {"127.0.0.1", 8081},
    {"127.0.0.1", 8082},
    {"127.0.0.1", 8083},
};
#define NUM_BACKENDS (sizeof(backends) / sizeof(backends[0]))
static int backend_idx = 0;

Backend *next_backend(void) {
    /* Note: not thread-safe; use __sync_fetch_and_add for safety */
    Backend *b = &backends[backend_idx % NUM_BACKENDS];
    backend_idx++;
    return b;
}

typedef struct {
    int client_fd;
    Backend *backend;
} ProxyArgs;

void forward(int src, int dst) {
    char buf[BUF_SIZE];
    int n;
    while ((n = recv(src, buf, BUF_SIZE, 0)) > 0) {
        send(dst, buf, n, 0);
    }
}

void *proxy_thread(void *arg) {
    ProxyArgs *args = (ProxyArgs *)arg;
    
    /* Connect to backend */
    int backend_fd = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port = htons(args->backend->port),
    };
    inet_pton(AF_INET, args->backend->ip, &addr.sin_addr);
    
    if (connect(backend_fd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("connect to backend");
        close(args->client_fd);
        free(args);
        return NULL;
    }
    
    /* Bidirectional proxy (simplified, blocking) */
    forward(args->client_fd, backend_fd);
    
    close(args->client_fd);
    close(backend_fd);
    free(args);
    return NULL;
}

int main(void) {
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
    
    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = INADDR_ANY,
        .sin_port = htons(FRONTEND_PORT),
    };
    bind(listen_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(listen_fd, 128);
    printf("L4 Load Balancer listening on port %d\n", FRONTEND_PORT);
    
    while (1) {
        int client_fd = accept(listen_fd, NULL, NULL);
        Backend *b = next_backend();
        printf("Routing to %s:%d\n", b->ip, b->port);
        
        ProxyArgs *args = malloc(sizeof(ProxyArgs));
        args->client_fd = client_fd;
        args->backend = b;
        
        pthread_t tid;
        pthread_create(&tid, NULL, proxy_thread, args);
        pthread_detach(tid);
    }
    return 0;
}
```

---

## 24. Interview-Level Questions & Expert Answers

### Q1: How does a load balancer handle a backend that becomes slow (not crashed)?

**Answer**: This is harder than detecting a crash. Key approaches:
1. **Passive health check via response times**: Track moving average of response times per backend. Mark as degraded if p99 exceeds threshold.
2. **Least response time algorithm**: Naturally steers traffic away from slow servers.
3. **Circuit breaker**: If error rate (including timeouts) exceeds X%, open circuit for that backend.
4. **Timeout + retry**: Set request timeouts (e.g., 5s). On timeout, retry on a different backend. This is complex — must ensure requests are **idempotent** (safe to retry), otherwise you risk double-processing.

---

### Q2: How would you design a load balancer that handles 10 million concurrent connections?

**Answer**:
1. **Use DPDK or XDP** to bypass kernel for packet processing.
2. **Connection multiplexing**: Maintain fewer backend connections using HTTP/2 or QUIC multiplexing.
3. **C10M architecture**: Single-threaded event loops (like nginx), avoid context switches.
4. **Memory**: Each TCP connection uses ~4KB of kernel memory → 10M connections = 40GB RAM minimum.
5. **Horizontal scaling**: Multiple LB instances with ECMP routing at the network layer.
6. **L4 (not L7)**: L7 parsing multiplies CPU cost per connection.

---

### Q3: What is the difference between connection-based and request-based load balancing?

```
CONNECTION-BASED (L4):
  Client opens TCP connection to LB
  LB picks a backend for this ENTIRE connection
  All requests within this connection go to same backend
  
  One TCP connection might carry:
    - 100 HTTP/1.1 requests (with keep-alive)
    - Entire gRPC stream
    - Long-lived WebSocket

  Problem: Imbalanced if some connections have many requests

REQUEST-BASED (L7 HTTP/1.1):
  Each HTTP request can go to a different backend
  Even within the same TCP connection
  
  Connection 1 from client:
    Request 1 → Server A
    Request 2 → Server B
    Request 3 → Server A
    
  More granular balancing, but requires parsing HTTP

REQUEST-BASED (HTTP/2):
  HTTP/2 streams within one connection
  Each stream can be routed independently
  LB must understand HTTP/2 framing
```

---

### Q4: Explain the split-brain problem in Active-Active load balancers.

**Answer**: When two LBs lose connectivity to each other but both remain up and connected to clients:

```
SPLIT-BRAIN SCENARIO:

       ┌──────────────┐
       │   Network    │
       │   Partition  │
       │              │
[LB-1]── ✗ ──[LB-2]
   │                 │
[Server A]       [Server B]

Both LB-1 and LB-2 think they're the primary.
Both announce the VIP.
Network is split: clients on LB-1's subnet go to LB-1,
                  clients on LB-2's subnet go to LB-2.

Problems:
- Session state on LB-1 not visible to LB-2
- Sticky sessions break (client may bounce between LBs)
- Inconsistent routing decisions

Solutions:
- Use a quorum/consensus mechanism (requires 3 nodes)
- Shared external session store (Redis)
- Fencing: when in doubt, shoot the other node (STONITH)
- VRRP with strict priority (only one wins)
```

---

### Q5: How does Cloudflare's load balancer work at a global scale?

**Answer**:
1. **Anycast**: Cloudflare announces the same IP from 300+ data centers. BGP routing sends each user to the nearest PoP (Point of Presence).
2. **Health checks from multiple locations**: Each Cloudflare PoP independently checks origin health. Decisions are based on majority consensus across regions.
3. **GSLB**: Even after reaching the nearest Cloudflare PoP, traffic may be routed to an origin in a different region based on health/latency.
4. **Weighted failover**: Can shift 0-100% of traffic per origin pool with fine granularity.
5. **Session affinity at PoP level**: Consistent hashing ensures the same user hits the same PoP (minimizing session issues with origin affinity).

---

## 25. Mental Models & Summary Cheatsheet

### The 5 Core Questions of Load Balancing

```
When designing any load balancing solution, ask:

1. WHERE should the decision be made?
   (Client-side, network, dedicated appliance, cloud)

2. WHAT information is available for routing?
   (L4: IP/port only | L7: full HTTP content)

3. WHICH algorithm minimizes hotspots for this workload?
   (Stateless RR | Variable-cost Least-Conn | Cache-friendly Consistent Hash)

4. HOW do we detect and handle failures?
   (Health checks | Circuit breakers | Retries | Draining)

5. HOW do we ensure the LB itself doesn't fail?
   (Active-Passive VRRP | Active-Active ECMP | Cloud managed)
```

### Decision Flowchart

```
START: I need to balance traffic

        │
        ▼
Is this internal service-to-service (microservices)?
        │
   ┌────┴────┐
   │YES      │NO
   ▼         ▼
Use          Is this a large enterprise with
Sidecar      money for appliances?
(Envoy/           │
Istio)       ┌────┴────┐
             │YES      │NO
             ▼         ▼
           Hardware   Cloud or
           LB (F5)    on-prem software LB
                           │
                      ┌────┴────┐
                      │Cloud    │On-prem
                      ▼         ▼
                   AWS ALB   NGINX /
                   GCP LB    HAProxy
                   Azure LB  Envoy
```

### Algorithm Selection Guide

```
Workload Type                     → Recommended Algorithm
──────────────────────────────────────────────────────────
Homogeneous servers, stateless    → Round Robin
Mixed server capacities           → Weighted Round Robin
Variable request cost (APIs, DBs) → Least Connections
Response time critical            → Least Response Time
Needs session affinity            → IP Hash or Cookie Sticky
Caching layer (Redis/Memcached)   → Consistent Hashing
Microservices, large cluster      → Random (Power of Two)
Full control per request          → Resource-Based (Adaptive)
```

### OSI Layer Decision Guide

```
Use L4 when:
  ✓ Non-HTTP protocol (database, game server, MQTT, SMTP)
  ✓ Maximum throughput / minimum latency required
  ✓ SSL passthrough needed
  ✓ Source IP preservation critical

Use L7 when:
  ✓ URL/path-based routing needed
  ✓ Cookie-based session affinity
  ✓ SSL termination at LB
  ✓ HTTP header manipulation
  ✓ Canary / A/B deployments
  ✓ WAF integration
  ✓ WebSocket support with HTTP upgrade inspection
```

### Cognitive Framework: Mental Simulation

When encountering any load balancing problem, train yourself to mentally simulate:

```
1. REQUEST JOURNEY:
   Client → Network → VIP → LB Decision Logic → Backend
   → Backend processes → Response back through LB → Client

2. FAILURE SCENARIOS:
   What if backend A crashes mid-request?
   What if LB loses 50% of its memory?
   What if network between LB and backends partitions?
   What if client is behind CGNAT?

3. SCALING SCENARIOS:
   What happens when we 10x traffic?
   What if we add 10 more backends overnight?
   What if a backend upgrade takes 5 minutes?

4. SECURITY SCENARIOS:
   What if a client sends 10K req/sec?
   What if a client spoofs its IP?
   What if a backend is compromised?
```

---

## Appendix: Reference Architecture — Production Web Application

```
COMPLETE PRODUCTION ARCHITECTURE:

Internet
   │
   ▼
[Anycast / BGP]  (Cloudflare or AWS Global Accelerator)
   │
   ▼
[DDoS Scrubbing]  (Cloudflare Magic Transit or AWS Shield)
   │
   ▼
[WAF]  (Cloudflare WAF or AWS WAF)
   │
   ▼
[Global DNS/GSLB]  (Route53 latency-based or Cloudflare LB)
   │
   ├──── Singapore Region ──────────────────────────────┐
   │         │                                          │
   │    [L4 NLB cluster]  (Active-Active, ECMP)         │
   │         │                                          │
   │    [L7 ALB cluster]  (SSL termination, L7 routing) │
   │         │                                          │
   │    ┌────┴──────────────────────┐                   │
   │    │  /api → API server pool   │                   │
   │    │  /web → Web server pool   │                   │
   │    │  /ws  → WebSocket servers │                   │
   │    └───────────────────────────┘                   │
   │         │                                          │
   │    [Service Mesh / Envoy sidecars]                 │
   │    (Internal service-to-service LB)                │
   │         │                                          │
   │    [Stateless App Servers]                         │
   │         │                                          │
   │    [Shared Redis] (session store, rate limit state)│
   │    [PostgreSQL with PgBouncer] (connection pooling)│
   └────────────────────────────────────────────────────┘
   │
   └──── Frankfurt Region (identical architecture) ─────┘

Key properties:
✓ No SPOF at any layer
✓ Horizontally scalable at every tier
✓ Stateless application servers (any can serve any request)
✓ Global failover in < 60 seconds (DNS TTL)
✓ Regional failover in < 5 seconds (VRRP/ECMP)
✓ Zero-downtime deployments via rolling update + drain
```

---

*End of Guide — Load Balancers: From First Principles to Production Mastery*

> **Deliberate Practice Note**: Understanding load balancers deeply requires you to implement them. Start with the simple Go/Python implementations above, then add health checking, then weighted algorithms, then consistent hashing. Each implementation forces your brain to confront edge cases you'd never see by reading alone. This is the deliberate practice principle — struggle is the mechanism of growth.

Now let me build this comprehensive guide for you. This will be a large, deeply detailed document.Here is your complete guide — **25 deep sections**, all in one `.md` file. Here's what's packed inside:

**Architecture & Concepts** — The OSI model and exactly where L4 vs L7 LBs live, what they can and cannot see, and why that matters for every routing decision.

**Every Algorithm Dissected** — Round Robin, Weighted RR (including the smooth NGINX algorithm), Least Connections, Least Response Time, IP Hash, Power of Two Choices, Consistent Hashing — each with a flow diagram, real code, pros/cons, and when to choose it.

**Consistent Hashing** — Full treatment including the virtual nodes problem, the ring abstraction, and working implementations in Python and Go.

**Failure Modes & HA** — Active-Passive (VRRP), Active-Active (ECMP), Split-Brain problem, Circuit Breaker state machine, Thundering Herd — with ASCII state diagrams for each.

**Real-World Systems** — Annotated HAProxy/NGINX configs, Envoy's xDS architecture, AWS ALB vs NLB comparison table, Cloudflare's Anycast model.

**Code in Your Languages** — TCP L4 proxy in **C** (raw sockets + pthreads), HTTP LB in **Go** (atomic round-robin + reverse proxy), async LB in **Python** (aiohttp), L4 proxy in **Rust** (tokio + async bidirectional copy).

**Production Reference Architecture** — A full diagram from Anycast BGP → DDoS scrubbing → WAF → GSLB → L4 NLB → L7 ALB → Service Mesh → stateless app servers → Redis/Postgres — no single point of failure at any layer.

> **One mental model to carry**: A load balancer is fundamentally a *decision engine* — its value comes entirely from the quality of the decision (which backend?), the speed of the decision (latency), and the correctness of the health model (who is actually alive?). Every feature you learn maps back to one of those three dimensions.