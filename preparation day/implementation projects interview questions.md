# Coding problems

Given your background, interviewers will skew heavily toward **systems/networking coding problems** rather than generic LeetCode. Here's a breakdown by category, with the kind of company that tends to ask each type.

## Classic "systems programming" coding questions
These show up at companies like Cloudflare, Fastly, Meta, AWS, Cisco/Isovalent, Datadog:

- **TCP/UDP echo or ping-pong server+client** (your example) — often with a twist: add backpressure, graceful shutdown, connection pooling, or make it handle N concurrent clients with bounded goroutines/threads
- **Rate limiter** (token bucket / leaky bucket / sliding window) — implement from scratch, thread-safe
- **LRU / LFU cache** with concurrent access
- **Connection pool / worker pool** implementation
- **Pub-sub system** in-memory (channels in Go, or mutex+condvar in Rust/C)
- **Logging system** (your example) — usually wants: structured logging, log rotation, concurrent-safe writes, maybe a ring buffer for lock-free logging
- **Rate-limited HTTP proxy / reverse proxy** — implement basic load balancing (round robin, least connections)
- **Distributed lock** using etcd/Redis-like semantics
- **Consistent hashing ring** implementation (for sharding/load balancing — very relevant given Katran/L4 LB background)
- **Bloom filter** implementation
- **Simple key-value store** with TTL eviction
- **Circuit breaker** pattern implementation

## Concurrency-specific (Go/Rust favorite)
- Implement a **thread-safe/goroutine-safe queue** without using built-in sync primitives directly (or build your own mutex using channels)
- **Producer-consumer** with bounded buffer
- **Dining philosophers** / deadlock avoidance
- Implement `sync.WaitGroup` or a semaphore from scratch
- **Fan-out/fan-in** pipeline in Go
- Rust: implement something using `Arc<Mutex<T>>` vs lock-free with atomics — explain when you'd reach for each

## Networking/kernel-adjacent coding (rarer, but shows up at Cloudflare, Isovalent, AWS networking teams)
- Parse a raw packet (Ethernet/IP/TCP headers) from bytes — write your own minimal packet parser
- Implement a simplified **NAT table** or **conntrack**-like structure
- Given XDP/eBPF context: write a small eBPF program to drop/pass packets based on a condition, or explain/debug a CO-RE relocation issue
- Implement **BGP path selection logic** as pure logic exercise (no real BGP, just simulate route selection given attributes)
- Write a minimal **health-checker** that pings backend list and updates a load balancer's pool

## Distributed systems coding
- Implement **leader election** (bully algorithm or simplified Raft-lite)
- **Distributed counter** with eventual consistency
- **Vector clocks** / logical clocks implementation
- **Gossip protocol** simulation
- **Idempotent request handling** / dedup with request IDs
- **Two-phase commit** simulation

## System design (not coding, but paired with above)
- Design a **distributed rate limiter** across multiple nodes
- Design **Cilium-like CNI networking layer** conceptually (given your exact background, don't be surprised if this shows up almost verbatim)
- Design a **service mesh sidecar proxy**
- Design an **L4 load balancer** (Katran-style) — XDP-based, DSR (direct server return) tradeoffs
- CAP theorem tradeoffs in a real system you'd design (e.g., a distributed cache)
- Design a **zero-trust network** with mTLS between services

## Go/Rust-specific "language mastery" checks
- Go: channel-based worker pool, context cancellation propagation, avoiding goroutine leaks
- Rust: ownership/borrow-checker puzzle questions ("why doesn't this compile"), implementing a simple allocator, or safe wrapper around unsafe FFI (very relevant to your eBPF/Aya-rs work)

If you want, I can generate a **mock problem set** (with solutions in Go or Rust) tailored to say — Cloudflare/Isovalent-style networking interviews, or a general FAANG systems-track set. Want me to build one?

For Go and Rust, interviewers usually don't ask the exact same things because companies expect different strengths from developers using each language.

Go Interview Questions

Go interviews focus on:

Concurrency
Networking
Backend systems
Cloud-native development
Kubernetes ecosystem
Production engineering
1. Goroutines & Channels

Extremely common.

Example:

func main() {
    ch := make(chan int)

    go func() {
        ch <- 42
    }()

    fmt.Println(<-ch)
}


Questions:

Buffered vs unbuffered channels
Channel closing
Select statement
Deadlocks
Goroutine leaks

Follow-up:

Implement worker pool.

2. Context Package

Very common.

ctx, cancel := context.WithTimeout(...)


Questions:

Cancellation propagation
Deadlines
Request-scoped values

Example:

How would you stop 100 goroutines when request times out?

3. Mutex vs Channels

Question:

When would you use mutex instead of channels?


Expected:

Channels for communication
Mutexes for shared state
4. Worker Pool

Implement:

Submit(task)
Shutdown()


Tests:

Channels
Goroutines
Sync primitives

One of the most common Go coding questions.

5. Rate Limiter

Implement:

Allow()


Using:

Token bucket
Leaky bucket

Very popular.

6. HTTP Middleware

Implement:

Logging
Authentication
Metrics


Example:

func Logging(next http.Handler)

7. HTTP Server

Build:

GET /users
POST /users


Expected:

Routing
Middleware
Graceful shutdown
8. Connection Pool

Implement:

GetConnection()
ReleaseConnection()


Tests:

Sync
Resource management
9. Cache

Implement:

LRU
TTL cache


Concurrent version often asked.

10. Pub/Sub

Implementation:

Subscribe()
Publish()


Tests:

Fan-out
Concurrency
Go Theory Questions

These appear constantly.

What is GMP scheduler?

You should know:

G = Goroutine
M = Machine(OS Thread)
P = Processor

How does GC work?

Topics:

Concurrent GC
Tricolor marking
STW phases
Why goroutines are lightweight?

Need to explain:

Small stack
User-space scheduling

What happens when channel blocks?

Very common interview topic.

Difference:
make()
new()

Escape Analysis

Example:

func foo() *int {
    x := 1
    return &x
}


Question:

Stack or heap?

Rust Interview Questions

Rust interviews are far more language-specific.

Most companies test:

Ownership
Lifetime reasoning
Async runtime
Memory safety
Systems programming
1. Ownership

Probably the #1 Rust interview topic.

Example:

let s = String::from("hello");

let s2 = s;


Question:

Why does this fail?


Need to explain:

Move semantics
Ownership transfer

2. Borrowing

Example:

fn foo(s: &String)


Question:

Why borrow instead of move?


Need:

Immutable borrow
Mutable borrow

3. Lifetimes

Very common.

Example:

fn longest<'a>(
    x: &'a str,
    y: &'a str
) -> &'a str


Question:

Why lifetime needed?


Many senior Rust interviews include lifetime debugging.

4. Interior Mutability

Questions around:

Cell
RefCell
Mutex
RwLock


Need to know:

Compile-time borrow checking
Runtime borrow checking

5. Smart Pointers

Frequently asked:

Box<T>
Rc<T>
Arc<T>


When to use each?

6. Arc + Mutex

Classic question:

Arc<Mutex<HashMap>>


Need understanding of:

Shared ownership
Synchronization

7. Send & Sync

One of the most important Rust topics.

Questions:

Why is Arc<T> Send?
Why is Rc<T> not Send?


Need to understand:

Thread safety
Auto traits

8. Async Rust

Increasingly common.

Example:

async fn process()


Questions:

What is Future?
What is poll()?
What does .await do?
Tokio runtime?
9. Tokio

Companies using Rust backend almost always ask.

Topics:

tokio::spawn()


Need to know:

Runtime
Scheduler
Tasks
10. Pin

Senior Rust interviews.

Example:

Pin<Box<T>>


Question:

Why does async require Pin?

Rust Systems Programming Questions

Relevant to your profile.

Custom Allocator

Implement:

alloc()
free()


Conceptual discussion.

Thread Pool

Rust version.

Need:

Arc
Mutex
Condvar

Event Loop

Implement:

epoll
kqueue


Common in systems companies.

Lock-Free Queue

Senior-level systems question.

Need concepts:

Atomics
CAS
Memory ordering

Memory-Mapped File

Implement:

mmap


Questions around:

Zero copy
Page cache

Rust + eBPF Companies

If interviewing at:

Cilium
Isovalent
Cloudflare
Datadog
Red Hat
Microsoft Azure Networking

Expect:

Aya
How does Aya load programs?

CO-RE
Why is BTF required?

Maps
Hash Map
LRU Map
Per CPU Map
Ring Buffer

XDP
PASS
DROP
TX
REDIRECT

Verifier
Why verifier rejects program?

Tail Calls
BPF_PROG_ARRAY

What I'd Expect for Your Profile

For someone with:

Go
Rust
eBPF
XDP
Cilium
Cloud Networking
Distributed Systems

The most realistic coding rounds would be:

Go
Worker Pool
Rate Limiter
Pub/Sub Broker
Reverse Proxy
Load Balancer
Service Discovery
Concurrent Cache
gRPC Service
Rust
Concurrent HashMap
Thread Pool
Async TCP Server
Event Loop
Connection Tracker
Memory Pool
Lock-Free Queue
Packet Processing Pipeline
Infrastructure / Systems
TCP Chat Server
Kafka-lite
DNS Cache
Firewall Engine
NAT Gateway
Distributed Lock
DDoS Mitigator (XDP)
Mini CNI Plugin

If you're targeting senior infrastructure companies, I'd prioritize:

Go: Worker Pool → Rate Limiter → Reverse Proxy → Load Balancer → Service Discovery

Rust: Ownership → Lifetimes → Send/Sync → Async/Tokio → Thread Pool → Event Loop → Lock-Free Data Structures

Those are the areas that consistently appear in networking, cloud-platform, kernel-adjacent, and distributed-systems interviews.

Given your stack, you're not in the typical "backend CRUD engineer" interview bucket.

Companies hiring for Go/Rust systems engineers, cloud networking engineers, eBPF engineers, Cilium engineers, kernel engineers, platform engineers, service mesh engineers, security engineers, or distributed systems engineers will usually ask implementation problems that resemble real infrastructure software.

I'd categorize interview problems into tiers.

Tier 1: Must Know (Asked Everywhere)

These appear repeatedly across cloud, platform, networking, and systems roles.

1. Thread Pool

Implement:

pool.Submit(task)


Features:

Worker threads/goroutines
Graceful shutdown
Backpressure

Tests:

Concurrency
Synchronization
Producer-consumer patterns
2. Rate Limiter

Implement:

Token Bucket
Leaky Bucket
Sliding Window


Features:

Allow(ip)


Common follow-ups:

Distributed rate limiter
Redis backed rate limiter
3. LRU Cache

Implement:

Get()
Put()


O(1) operations.

Senior follow-up:

TTL support
Concurrent access
Shard cache

4. Async Logger

Implement:

logger.Info()
logger.Error()


Requirements:

Non-blocking
Batched writes
Log rotation

This is a very realistic production problem.

5. Pub/Sub Broker

Implement:

Subscribe()
Publish()
Unsubscribe()


Think:

Kafka Lite
NATS Lite
Redis PubSub Lite

Tier 2: Networking Focused

These are extremely common for your background.

6. TCP Chat Server

Implement:

Multiple clients
Broadcast messages
Disconnect handling


Tests:

Goroutines
Async IO
Select
Channels
7. Reverse Proxy

Implement:

Client -> Proxy -> Backend


Features:

Connection pooling
Retry
Timeouts

Think:

Nginx
Envoy
HAProxy


Interviewers love this.

8. Load Balancer

Implement:

Round Robin
NextBackend()


Then:

Least Connection

Then:

Consistent Hashing

This comes up everywhere in cloud networking.

9. Service Discovery

Implement:

Register
Deregister
Heartbeat
Discover


Like:

Consul
Eureka
etcd

10. DNS Resolver Cache

Implement:

Lookup
TTL
Cache
Eviction


Very common in networking interviews.

Tier 3: eBPF / Kernel / Networking Roles

These are asked by companies working on networking stacks.

Examples:

Cilium
Isovalent
Red Hat
Cloudflare
Fortinet
Palo Alto
Datadog
Microsoft Azure Networking
11. Connection Tracker

Implement:

src_ip
dst_ip
src_port
dst_port
protocol


Store flows.

Think:

Linux conntrack


Follow-up:

Flow expiration
NAT translation

12. Packet Processing Pipeline

Implement:

Parse Ethernet

Parse IPv4

Parse TCP

Apply Rules

Forward/Drop


Essentially:

Mini XDP pipeline

13. Firewall Engine

Implement:

ALLOW
DROP
DENY


Example:

drop tcp/22
allow tcp/443


Concepts:

Rule matching
Longest prefix match
CIDR
14. NAT Gateway

Implement:

private -> public translation


Tests:

Hash tables
Port allocation
Connection tracking
15. VXLAN Tunnel Manager

Implement:

Create VNI
Add endpoint
Encap
Decap


Seen in SDN-focused interviews.

Tier 4: Distributed Systems

Possibly the most important category for senior roles.

16. Distributed Lock

Implement:

Lock(key)
Unlock(key)


Follow-ups:

Lease
Expiry
Renewal

17. Leader Election

Implement simplified:

Election
Heartbeat
Failover


Inspired by:

Raft
ZooKeeper

18. Distributed Cache

Implement:

Multi-node cache


Requirements:

Replication
Sharding
Consistent hashing

19. Kafka-like Queue

Implement:

Producer
Consumer
Partition
Offset


One of the best system-engineering interview questions.

20. Job Scheduler

Implement:

RunAt(time)
Retry()
Timeout()


Like:

Airflow Lite
K8s Job Lite

Tier 5: Kubernetes & Cloud Native

Since you know Kubernetes/Cilium.

21. Mini CNI

Implement:

Create namespace
Create veth pair
Assign IP
Routing


Not coding completely, but design + partial implementation.

22. Sidecar Proxy

Implement:

Intercept request
Add mTLS
Forward


Think:

Envoy
Istio
Linkerd

23. Service Mesh

Design:

Control Plane
Data Plane


Common discussion round.

24. Admission Controller

Implement:

Validate Pod
Mutate Pod


Good Go interview project.

Tier 6: eBPF-Specific Questions

These are increasingly popular.

25. DNS Monitor with eBPF

Capture:

DNS packets


using:

XDP
tc
socket filter

26. Process Monitor

Track:

execve
fork
exit


using:

tracepoints
kprobes


Like Tetragon.

27. Network Flow Exporter

Generate:

5-tuple flow records


using:

XDP maps
Per CPU maps
Ring buffers

28. DDoS Detector

Implement:

Packet counters
Rate thresholds
Drop rules


using:

XDP
Hash maps
LRU maps

29. Mini Hubble

Track:

Pod A -> Pod B


Generate flow events.

Very realistic Cilium-style interview.

Tier 7: Rust-Specific Favorites

For Rust engineering interviews:

30. Async Runtime Components

Implement:

Future
Executor
Spawner


Simplified Tokio concepts.

31. Concurrent HashMap

Implement:

Sharded hashmap


Tests:

Arc
Mutex
RwLock
DashMap-style thinking

32. Reactor/Event Loop

Implement:

epoll
kqueue
io_uring


Simplified version.

33. Connection Pool

Implement:

pool.acquire()
pool.release()


Database style.

What FAANG+/Infra Companies Actually Like

If I interviewed someone with your resume, my top 15 questions would be:

Thread Pool
Rate Limiter
LRU Cache
Pub/Sub Broker
TCP Chat Server
Reverse Proxy
Load Balancer
Service Discovery
Connection Tracker
Firewall Engine
Kafka-lite
Distributed Lock
Job Scheduler
DNS Monitor using eBPF
DDoS Mitigation using XDP

These questions collectively test:

Go/Rust proficiency
Concurrency
Networking
Linux internals
eBPF knowledge
Distributed systems
Production engineering skills

For your profile, I'd spend most preparation time on:

Thread Pool → Rate Limiter → Reverse Proxy → Load Balancer → Connection Tracker → Kafka-lite → Distributed Lock → XDP DDoS Filter → Mini CNI → Service Discovery

Those map almost directly to the work done in cloud networking, Cilium, service mesh, platform engineering, and kernel-adjacent infrastructure teams.

If you're targeting backend, distributed systems, infrastructure, cloud, or senior software engineering roles, companies often ask "mini-system implementation" coding problems rather than just LeetCode algorithms.

The examples you mentioned (Ping-Pong server, logging system) belong to the machine coding / systems coding category.

Here's a comprehensive list of commonly asked implementation-style interview questions.

1. Networking & Server Questions
Ping-Pong Server

Build a TCP server:

Client sends PING
Server responds PONG
Support multiple clients

Concepts tested:

Sockets
Threads
Async I/O
Concurrency
Chat Server

Implement:

Multiple clients
Join/Leave room
Broadcast messages

Concepts:

Network programming
Message routing
Concurrency
HTTP Server

Implement a simple web server:

GET /users
POST /users


Concepts:

HTTP protocol
Request parsing
Routing

Frequently asked in:

Rust
Go
Java
Node.js
Rate-Limited API Server

Example:

User can send only 100 requests/minute


Implement:

Token Bucket
Sliding Window

Concepts:

Data structures
Concurrency
Distributed systems
2. Logging System Questions
Basic Logger

Implement:

logger.info("hello")
logger.error("failed")


Features:

Timestamp
Levels
Formatting
Async Logger

Requirements:

Logging shouldn't block application

Concepts:

Queue
Producer Consumer
Threading
Log Aggregator

Collect logs from:

Server A
Server B
Server C


Concepts:

Queue
Network communication
File persistence
Rolling Logger

Example:

log.txt


When file exceeds:

100 MB


Create:

log_1.txt


Concepts:

File I/O
Storage management
3. Cache Design Questions
LRU Cache

Classic interview problem.

Operations:

get()
put()


In:

O(1)


Concepts:

HashMap
Doubly Linked List
LFU Cache

Harder variant.

Concepts:

Frequency tracking
Multiple linked lists
Redis-like Cache

Implement:

SET
GET
EXPIRE
TTL


Concepts:

Hash maps
Timers
Eviction
4. Database-Style Questions
In-Memory Key Value Store

Implement:

PUT
GET
DELETE


Concepts:

Data structures
Mini SQL Database

Support:

SELECT
INSERT
DELETE


Concepts:

Parsing
Storage Engine
Transaction Manager

Implement:

BEGIN
COMMIT
ROLLBACK


Concepts:

ACID
Undo logs

Senior-level interviews love this.

5. Scheduler Questions
Task Scheduler

Example:

Run task after 10 seconds


Concepts:

Priority Queue
Timers
Cron Scheduler

Implement:

0 0 * * *


Concepts:

Time calculations
Scheduling
Job Queue

Example:

enqueue
dequeue
retry
dead-letter queue


Concepts:

Message queues
Distributed systems
6. Messaging Systems
Kafka-Like Queue

Implement:

Topic
Producer
Consumer

Concepts:

Partitions
Offsets

Very popular for senior backend roles.

Pub/Sub System

Example:

subscribe(topic)
publish(message)


Concepts:

Observer Pattern
Event-driven systems
RabbitMQ-like Broker

Features:

Routing keys
Queues
Acknowledgements
7. Storage System Questions
File Storage System

Implement:

upload
download
delete


Concepts:

Metadata
Persistence
URL Shortener

Example:

tinyurl.com/abc


Concepts:

Hashing
Encoding
Storage

Extremely common.

Dropbox/GDrive Lite

Implement:

Upload
Versioning
Sharing

Senior interviews.

8. Concurrency Questions
Producer Consumer

Classic.

Implement:

bounded queue


Concepts:

Mutex
Semaphore
Condition Variable
Reader Writer Lock

Implement:

many readers
single writer


Common in Rust, Java, C++ interviews.

Thread Pool

Implement:

submit(task)


Concepts:

Worker threads
Job queues

Very frequently asked.

9. Design Pattern Implementation
Parking Lot

Popular machine coding round.

Entities:

Vehicle
Slot
Ticket
ParkingLot


Tests:

OOP
Design Patterns
Elevator System

Implement:

request floor
schedule movement


Concepts:

State Machine
Scheduling
Vending Machine

Concepts:

State Pattern
Object-Oriented Design
10. Distributed Systems Questions
Distributed Lock

Implement:

lock(key)
unlock(key)


Concepts:

Consensus basics
Failure handling
Leader Election

Concepts:

Distributed coordination

Often discussed rather than fully coded.

Service Registry

Like:

Consul
Eureka


Implement:

register
discover
heartbeat


Concepts:

Networking
Distributed systems
11. Real Companies' Favorite Questions
Uber
Ride matching system
Location tracker
Rate limiter
Dispatch service
Amazon
LRU cache
Logger
Parking lot
Job scheduler
Inventory management
Google
RPC framework
Distributed cache
Search indexing
Task scheduler
Microsoft
Thread pool
Eventing system
File sync
Service discovery
Meta
News feed aggregator
Pub/Sub
Messaging service
Distributed cache
Stripe
Payment ledger
Transaction processing
Idempotency service
Databricks
Kafka-like queue
Distributed scheduler
Storage engine
Cloudflare
DNS server
HTTP proxy
Cache server
Rate limiter
Rust Backend-Specific Questions

Since you've been learning Axum/gRPC/Rust, these are particularly relevant:

Build a TCP Ping-Pong server
Build a mini HTTP server
Build a gRPC service with .proto
Implement LRU cache
Implement thread pool
Build async logger
Build rate limiter
Build pub/sub broker
Build task scheduler
Build service registry (Consul-lite)
Build Redis-lite
Build Kafka-lite
Build URL shortener

These are probably the top 12 implementation projects/interview questions that appear repeatedly for backend and distributed systems engineers. Mastering them gives you exposure to networking, async programming, concurrency, storage, and system design, which is exactly what many modern companies assess beyond pure algorithms.