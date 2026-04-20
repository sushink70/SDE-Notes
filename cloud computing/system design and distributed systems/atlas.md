# System Design, Distributed Systems & Core Infrastructure — Complete Knowledge Atlas

> **Goal:** A structured, dependency-ordered map of every topic you must master to reach the top 1% in system design and distributed systems engineering.

---

## How to Read This Atlas

This is not a flat list — it is a **dependency graph**. Each section builds on the previous. Study in layer order:

```
LAYER 0 — Vocabulary & Mental Models      (Sections 01, 02)
     ↓
LAYER 1 — Storage & Caching               (Sections 03, 04)
     ↓
LAYER 2 — Distributed Theory              (Sections 05, 11)
     ↓
LAYER 3 — Messaging & Architecture        (Sections 06, 07)
     ↓
LAYER 4 — Infrastructure & Ops            (Sections 08, 09, 10, 12)
     ↓
LAYER 5 — Practice through Case Studies   (Section 13)
     ↓
LAYER 6 — Advanced / Niche               (Section 14)
```

---

## The 5 Load-Bearing Concepts (Master These First)

Every other topic depends on these. Do not skip them.

| # | Concept | Why it matters |
|---|---------|---------------|
| 1 | **CAP Theorem + PACELC** | Forces reasoning about every design under failure. Without this, your designs are naive. |
| 2 | **Consistent Hashing** | Key algorithm behind sharding, distributed caching, load balancing. Appears in Cassandra, Redis Cluster, DynamoDB. |
| 3 | **Raft / Paxos Consensus** | How distributed nodes *agree* despite crashes and network splits. Leader election, distributed locks, and replicated logs all click once you internalize this. |
| 4 | **Write-Ahead Log (WAL) + LSM-Tree** | The engine behind nearly every modern database (RocksDB, Cassandra, LevelDB). The physical foundation beneath all database discussions. |
| 5 | **Replication Strategies** | The spectrum from strong consistency to eventual consistency made concrete. Amazon's Dynamo paper is the canonical text. |

---

## The Expert's Design Checklist

When facing any system design problem, run this mental loop:

```
1. What are the read/write ratios?        → Choose storage type
2. What consistency is required?          → Choose replication model
3. Where will bottlenecks be?             → Apply caching / sharding
4. What happens when a node fails?        → Apply fault-tolerance patterns
5. How does it scale 10x? 100x?           → Revisit every choice above
```

---

## Section 01 — Foundations of System Design

### Core Vocabulary

- Scalability (vertical vs horizontal)
- Availability (uptime, SLA, SLO, SLI)
- Reliability and fault tolerance
- Latency vs throughput
- Consistency models overview
- Durability
- Idempotency
- Atomicity

### Estimation Skills

- Back-of-envelope math
- QPS / RPS calculation
- Storage estimation
- Bandwidth estimation
- Powers of 2 and latency numbers every engineer should know
- Traffic spike modeling
- Read/write ratio analysis

### Design Process

- Requirements clarification (functional vs non-functional)
- High-level design (HLD)
- Low-level design (LLD)
- API-first design approach
- Trade-off reasoning framework
- Bottleneck identification
- Capacity planning mindset

### Networking Basics

- TCP vs UDP — when to use each
- HTTP/1.1, HTTP/2, HTTP/3 (QUIC)
- WebSockets and long polling
- Server-sent events (SSE)
- DNS resolution flow
- IP routing, NAT, subnets
- TLS/SSL handshake
- gRPC and Protobuf

---

## Section 02 — Load Balancing & Traffic Management

### Load Balancers

- L4 (transport layer) vs L7 (application layer) load balancing
- Round robin algorithm
- Least connections algorithm
- Weighted routing
- IP-hash routing
- Consistent hashing for load balancing
- Sticky sessions
- Health checks and heartbeats
- Hardware vs software load balancers
- Global vs local load balancing

### Rate Limiting

- Token bucket algorithm
- Leaky bucket algorithm
- Fixed window counter
- Sliding window log
- Sliding window counter
- Distributed rate limiters (Redis-based)
- Per-user vs global limits
- Throttling vs rate limiting

### Proxies & API Gateways

- Forward proxy vs reverse proxy
- API gateway responsibilities (auth, routing, rate-limit, logging)
- Service mesh (Istio, Envoy, Linkerd)
- Sidecar proxy pattern
- mTLS between services
- Circuit breaker pattern
- Bulkhead isolation pattern

### CDN & Edge

- CDN push vs pull model
- Edge caching strategies
- Points of presence (PoP)
- Anycast routing
- Origin shield
- Edge computing
- Cache invalidation at the edge

---

## Section 03 — Caching Systems

### Caching Strategies

- Cache-aside (lazy loading)
- Write-through cache
- Write-back (write-behind) cache
- Read-through cache
- Refresh-ahead (pre-fetching)
- Cache stampede / thundering herd problem
- Negative caching (caching misses)

### Eviction Policies & Invalidation

- LRU (Least Recently Used)
- LFU (Least Frequently Used)
- MRU (Most Recently Used)
- TTL-based expiry
- Event-driven invalidation
- Cache versioning and namespacing
- Tag-based invalidation
- Consistent hashing for distributed cache

### Cache Technologies

- Redis (strings, hashes, sorted sets, pub/sub, streams)
- Memcached
- In-process L1 cache (local memory)
- Redis Cluster (distributed)
- CPU L1/L2/L3 cache intuition (locality)
- Browser caching (ETag, Cache-Control, Last-Modified)

### Advanced Cache Patterns

- Two-tier caching (L1 local + L2 distributed)
- Bloom filters as a pre-cache guard
- Hot key problem and mitigation
- Cache warming strategies
- Session store design
- Distributed session management

---

## Section 04 — Databases & Storage

### Relational (SQL) Databases

- ACID transaction properties (Atomicity, Consistency, Isolation, Durability)
- Normalization forms (1NF, 2NF, 3NF, BCNF)
- Denormalization trade-offs
- Indexing types: B-Tree, Hash, Bitmap, Full-text, Partial
- Query optimization and EXPLAIN/ANALYZE
- Join types and their computational cost
- Connection pooling (PgBouncer, HikariCP)
- PostgreSQL and MySQL internals
- Write-ahead log (WAL)

### NoSQL Databases

- Document stores (MongoDB)
- Key-value stores (DynamoDB, Redis)
- Wide-column stores (Apache Cassandra, HBase)
- Graph databases (Neo4j, Amazon Neptune)
- Time-series databases (InfluxDB, TimescaleDB)
- Search engines (Elasticsearch, OpenSearch)
- BASE properties (Basically Available, Soft state, Eventually consistent)

### Scaling Databases

- Read replicas
- Primary-replica (leader-follower) replication
- Multi-primary (multi-master) replication
- Horizontal sharding (range, hash, directory-based)
- Shard key selection strategies
- Consistent hashing for shard distribution
- Federation / functional partitioning
- Cross-shard queries and scatter-gather

### Storage Internals

- LSM-tree (Log-Structured Merge-tree)
- B-tree and B+ tree
- SSTables and compaction strategies
- Bloom filters in storage engines
- MVCC (Multi-Version Concurrency Control)
- Two-phase locking (2PL)
- Object storage (S3 model, MinIO)
- Block vs file vs object storage distinction
- OLTP vs OLAP vs HTAP workloads

### Data Warehouse & Analytics

- Column-oriented storage (Parquet, ORC)
- Snowflake and BigQuery architecture
- ETL vs ELT pipelines
- Data lake vs data warehouse vs data lakehouse
- Lambda architecture (batch + speed layer)
- Kappa architecture (stream-only)
- Materialized views
- Partition strategies: range, hash, list

### Transactions & Isolation Levels

- Read uncommitted
- Read committed
- Repeatable read
- Serializable isolation
- Phantom reads, dirty reads, non-repeatable reads
- Optimistic locking (compare-and-swap)
- Pessimistic locking (SELECT FOR UPDATE)
- Distributed transactions overview
- Saga pattern (choreography and orchestration)

---

## Section 05 — Distributed Systems: Core Theory

### Fundamental Theorems

- CAP theorem (Consistency, Availability, Partition Tolerance)
- PACELC theorem (adds Latency vs Consistency tradeoff)
- FLP impossibility result (consensus in async systems with failures)
- Brewer's conjecture history
- Two Generals' problem (impossibility of agreement over unreliable links)
- Byzantine Generals' problem (agreement with malicious nodes)

### Consistency Models (ordered weakest to strongest)

- Eventual consistency
- Monotonic reads
- Read-your-writes (session consistency)
- Causal consistency
- Sequential consistency
- Linearizability (strict / strong consistency)
- Serializability (transaction-level)
- Strict serializability (external consistency — Google Spanner)
- Tunable consistency (Cassandra)

### Consensus Algorithms

- Paxos: single-decree and multi-Paxos
- Raft: leader election, log replication, membership changes
- Zab: ZooKeeper Atomic Broadcast protocol
- Viewstamped Replication
- PBFT (Practical Byzantine Fault Tolerance)
- Tendermint (BFT for blockchains)
- Quorum-based reads and writes (W + R > N)

### Clocks & Event Ordering

- Physical clocks and clock drift
- Network Time Protocol (NTP)
- Lamport timestamps (logical clocks)
- Vector clocks
- Version vectors
- Causal ordering of events
- Total order broadcast
- TrueTime API (Google Spanner — atomic clocks + GPS)
- Hybrid Logical Clocks (HLC)

### Replication Strategies

- Single-leader (primary-replica) replication
- Multi-leader replication
- Leaderless replication (Dynamo-style)
- Synchronous vs asynchronous replication
- Replication lag and its consequences
- State machine replication
- Chain replication
- Quorums: sloppy quorum, hinted handoff

### Distributed Coordination

- Leader election algorithms
- Distributed locking (Redlock, etcd, ZooKeeper)
- Fencing tokens (preventing split-brain writes)
- Distributed semaphores
- ZooKeeper internals (znodes, watches, sessions)
- etcd (Raft-based key-value store)
- Gossip protocols mechanics
- Epidemic / anti-entropy algorithms
- CRDT: Conflict-free Replicated Data Types
  - G-Counter, PN-Counter
  - LWW-Register, MV-Register
  - OR-Set, RGA (sequence CRDTs)

---

## Section 06 — Messaging, Queues & Streaming

### Message Queue Concepts

- Producer / consumer model
- Point-to-point messaging
- Publish-subscribe (pub/sub) model
- At-most-once delivery semantics
- At-least-once delivery semantics
- Exactly-once delivery semantics
- Dead-letter queues (DLQ)
- Message ordering guarantees (FIFO, partition-ordered)
- Backpressure handling
- Fan-out pattern
- Competing consumers pattern

### Queue Technologies

- Apache Kafka (partitions, offsets, consumer groups, retention)
- RabbitMQ (exchanges, routing keys, bindings)
- AWS SQS / SNS
- NATS and NATS JetStream
- Apache Pulsar
- Redis Streams
- Google Cloud Pub/Sub

### Stream Processing

- Kafka Streams
- Apache Flink
- Apache Spark Structured Streaming
- Windowing: tumbling, sliding, session windows
- Watermarks and late-arriving data handling
- Stateful stream processing
- Event sourcing pattern
- CQRS (Command Query Responsibility Segregation)

### Async & Job Patterns

- Task queues (Celery, Sidekiq, BullMQ)
- Priority queues
- Delayed queues (scheduled / cron jobs)
- Inbox / outbox pattern
- Transactional outbox pattern
- Choreography-based sagas
- Orchestration-based sagas
- Idempotent consumers

---

## Section 07 — Architecture Patterns

### Service Architecture Styles

- Monolith (single deployable unit)
- Modular monolith
- Service-Oriented Architecture (SOA)
- Microservices architecture
- Serverless / Function-as-a-Service (FaaS)
- Cell-based architecture
- Domain-Driven Design (DDD)
- Bounded contexts and aggregates
- Strangler fig migration pattern

### Resilience Patterns

- Circuit breaker (closed, open, half-open states)
- Retry with exponential backoff
- Jitter in retry delays
- Timeout pattern
- Bulkhead / resource isolation
- Fallback and graceful degradation
- Health endpoint monitoring pattern
- Chaos engineering principles (Netflix Chaos Monkey)

### Communication Patterns

- REST (stateless, uniform interface, HATEOAS)
- GraphQL (schema, resolvers, N+1 problem)
- gRPC (unary, server-streaming, client-streaming, bidirectional)
- WebSocket (full-duplex, real-time)
- Async messaging between services
- Request-response vs event-driven
- Service discovery: client-side vs server-side
- Sidecar pattern, Ambassador pattern

### Data Architecture Patterns

- CQRS: separate read and write models
- Event sourcing: events as the source of truth
- API composition (aggregator pattern)
- Shared database anti-pattern
- Database per service pattern
- Two-phase commit (2PC)
- Three-phase commit (3PC)
- Transactional outbox + polling publisher

---

## Section 08 — Core Infrastructure

### Compute Layer

- Bare metal vs virtual machines vs containers
- Hypervisors: Type 1 (KVM, VMware ESXi) vs Type 2 (VirtualBox)
- Docker internals: Linux namespaces, cgroups, union filesystems
- Container image layers and overlay filesystems
- Kubernetes: pods, services, ingress, volumes
- Kubernetes control plane: API server, etcd, scheduler, controller manager
- Horizontal Pod Autoscaler (HPA), Vertical Pod Autoscaler (VPA)
- KEDA (event-driven autoscaling)
- Serverless compute: AWS Lambda, Google Cloud Run
- WebAssembly (WASM) as a compute runtime

### Storage Infrastructure

- SAN (Storage Area Network) vs NAS vs DAS
- Distributed file systems: HDFS, Google GFS
- Object storage: S3, Google Cloud Storage, MinIO
- RAID levels (0, 1, 5, 6, 10)
- Persistent Volumes and PVCs in Kubernetes
- NVMe and SSD internals (wear leveling, NAND types)
- Tiered storage: hot / warm / cold data

### Networking Infrastructure

- VPC, subnets, security groups, NACLs
- BGP routing and autonomous systems
- Software-Defined Networking (SDN)
- eBPF (extended Berkeley Packet Filter — kernel programmability)
- VXLAN and overlay networks
- Service mesh networking
- Kubernetes Network Policies
- Zero-trust networking model

### Operating Systems Concepts

- Process vs thread vs coroutine vs goroutine vs async task
- Kernel space vs user space
- System calls and context switching cost
- Virtual memory, page tables, page faults
- File descriptors and epoll (event-driven I/O)
- I/O models: blocking, non-blocking, multiplexed (select/poll/epoll), async
- Linux signals and process management
- Linux namespaces: PID, net, mnt, uts, ipc, user
- cgroups: CPU, memory, I/O accounting and limits

---

## Section 09 — Observability & Reliability Engineering

### The Three Pillars of Observability

- Metrics: counters, gauges, histograms, summaries
- Structured logging (JSON logs, log levels, correlation IDs)
- Distributed tracing: spans, trace context propagation
- OpenTelemetry standard (unified instrumentation)
- Prometheus + Grafana (metrics and dashboards)
- Jaeger / Zipkin (distributed tracing backends)
- ELK Stack: Elasticsearch, Logstash, Kibana
- EFK Stack: Elasticsearch, Fluentd, Kibana

### Site Reliability Engineering (SRE) Concepts

- SLI: Service Level Indicator (what you measure)
- SLO: Service Level Objective (the target)
- SLA: Service Level Agreement (the contract)
- Error budgets and how to use them
- Toil: manual, repetitive, automatable work
- Incident management lifecycle
- Blameless postmortems
- On-call practices and alerting fatigue
- Runbooks and playbooks

### Performance Engineering

- CPU, memory, and I/O profiling
- Flame graphs (on-CPU and off-CPU)
- Load testing tools: k6, Locust, wrk, hey
- Percentile latency: p50, p95, p99, p999
- Little's Law: L = λW (throughput, latency, concurrency)
- Amdahl's Law (limits of parallelism)
- Universal Scalability Law (USL)
- Queuing theory basics (M/M/1, M/M/c queues)
- Capacity planning methodology

### Fault Tolerance & Disaster Recovery

- Active-passive failover
- Active-active multi-region deployment
- RTO: Recovery Time Objective
- RPO: Recovery Point Objective
- Backup strategies: full, incremental, differential
- Geo-redundancy and geographic distribution
- Cross-region data replication
- Chaos engineering: fault injection principles

---

## Section 10 — Security & Authentication

### Authentication & Authorization

- Authentication (who are you?) vs Authorization (what can you do?)
- OAuth 2.0 flows: Authorization Code, Client Credentials, Device, PKCE
- OpenID Connect (OIDC) on top of OAuth 2.0
- JWT: structure (header.payload.signature), signing algorithms (HS256, RS256)
- Session tokens vs bearer tokens
- Refresh token rotation
- SAML 2.0 (enterprise federation)
- Single Sign-On (SSO)

### Security Patterns

- Defense in depth (multiple security layers)
- Principle of least privilege
- Zero-trust architecture (never trust, always verify)
- Secrets management (HashiCorp Vault, AWS Secrets Manager)
- mTLS (mutual TLS) for service-to-service auth
- API key management and rotation
- RBAC: Role-Based Access Control
- ABAC: Attribute-Based Access Control
- Encryption at rest (AES-256)
- Encryption in transit (TLS 1.3)

### Attack Surface & Protection

- DDoS protection (rate limiting, scrubbing centers)
- SQL injection prevention (parameterized queries)
- XSS (Cross-Site Scripting) prevention
- CSRF (Cross-Site Request Forgery) tokens
- Man-in-the-middle attack prevention
- Side-channel attack awareness
- Supply chain attacks (dependencies, CI/CD)
- Container escape vulnerabilities

---

## Section 11 — Distributed Data Algorithms

### Hashing Algorithms

- Consistent hashing (ring topology)
- Rendezvous hashing (highest random weight)
- Jump consistent hash (Google)
- Virtual nodes (vnodes) for load balancing
- Maglev hashing (Google load balancer)
- Hashing for shard assignment

### Probabilistic Data Structures

- Bloom filter: space-efficient set membership test
- Count-min sketch: frequency estimation
- HyperLogLog: cardinality (unique count) estimation
- MinHash: approximate set similarity (Jaccard)
- Cuckoo filter: deletion-supporting Bloom filter
- Skip lists: probabilistic sorted structure

### Conflict Resolution

- Last-Write-Wins (LWW) — timestamp-based
- Vector clock merging
- CRDTs: G-Counter, PN-Counter, LWW-Register, OR-Set
- Operational Transformation (OT) — Google Docs
- Read repair (Cassandra)
- Anti-entropy with Merkle trees (detecting divergence)
- Hinted handoff (temporary storage for unavailable nodes)

### Gossip Protocols & Membership

- Gossip protocol mechanics (epidemic dissemination)
- SWIM membership protocol
- Failure detection with heartbeats
- Phi-accrual failure detector
- Ring membership (Cassandra token ring)
- Consistent membership changes (Joint consensus in Raft)

---

## Section 12 — Cloud & DevOps

### Cloud Concepts

- IaaS / PaaS / SaaS distinctions
- Regions and availability zones (AZs)
- Multi-cloud and hybrid cloud strategies
- Cloud-native design principles (12-factor app)
- FinOps: cloud cost optimization
- Spot / preemptible instances
- Reserved vs on-demand capacity planning

### CI/CD & Deployment Strategies

- Blue-green deployment
- Canary deployments (traffic percentage shifting)
- Rolling updates
- Feature flags (progressive delivery)
- GitOps: ArgoCD, Flux
- Infrastructure as Code: Terraform, Pulumi
- Immutable infrastructure principle
- Build once, deploy many

### Container Orchestration (Kubernetes Deep Dive)

- Kubernetes control plane: API server, etcd, scheduler, controller manager, cloud-controller
- Worker node components: kubelet, kube-proxy, container runtime
- Deployment, StatefulSet, DaemonSet, Job, CronJob
- ConfigMaps and Secrets management
- Helm charts for packaging
- Service meshes: Istio, Linkerd
- Kubernetes Operators pattern
- Custom Resource Definitions (CRDs)

---

## Section 13 — Real-World Case Studies (Design Practice)

### Classic Design Problems

| System | Key Concepts Practiced |
|--------|----------------------|
| URL shortener (Bitly) | Hashing, KV store, redirection, analytics |
| Pastebin | Object storage, expiry, unique IDs |
| Web crawler | BFS/DFS, distributed queues, deduplication |
| Key-value store | Consistent hashing, replication, quorums |
| Distributed cache (Memcached/Redis) | Eviction, partitioning, hot keys |
| Rate limiter service | Token bucket, Redis, sliding window |
| Unique ID generator | Snowflake ID, timestamp + machine ID + sequence |

### Social & Communication Systems

| System | Key Concepts Practiced |
|--------|----------------------|
| Twitter timeline | Push vs pull fan-out, celebrity problem |
| WhatsApp / chat | WebSocket, message ordering, receipts |
| Instagram | CDN, object storage, feed generation |
| Facebook newsfeed | Ranking, aggregation, caching |
| Notification service | Push, pub/sub, delivery guarantees |
| Presence system | Heartbeats, TTL, gossip |
| Google Docs | OT / CRDT, real-time sync, versioning |

### Platform & Infrastructure Systems

| System | Key Concepts Practiced |
|--------|----------------------|
| YouTube / video streaming | Transcoding, CDN, chunked upload |
| Netflix CDN (Open Connect) | ISP peering, edge caching, ABR |
| Uber / ride sharing | Geo-indexing, matching, surge pricing |
| Airbnb search | ElasticSearch, geo-search, availability |
| Google Search index | Inverted index, MapReduce, PageRank |
| Amazon checkout | Distributed transactions, inventory |
| Dropbox / Google Drive | Chunking, deduplication, sync protocol |
| Stock exchange | Order book, low-latency, matching engine |

### Landmark System Papers

| Paper / System | What to Learn |
|---------------|---------------|
| Amazon Dynamo | Consistent hashing, quorums, eventual consistency, vector clocks |
| Google Bigtable | Wide-column, SSTable, compaction |
| Google GFS | Chunk servers, master-slave, large file append |
| Google Spanner | TrueTime, external consistency, Paxos across DCs |
| Apache Kafka | Log-based messaging, partitioning, consumer groups |
| Apache Cassandra | Leaderless, gossip, tunable consistency, LSM |
| Redis | Single-threaded event loop, data structures, replication |
| Elasticsearch | Inverted index, sharding, near-real-time search |

---

## Section 14 — Advanced & Emerging Topics

### Distributed Tracing Internals

- W3C TraceContext propagation standard
- Head-based vs tail-based sampling
- Sampling strategies (probabilistic, rate-limiting)
- Correlation IDs and request tracing
- Baggage propagation across service boundaries
- Exemplars: linking metrics to traces

### eBPF & Kernel-Level Engineering

- eBPF: safe, sandboxed programs run in the Linux kernel
- XDP (eXpress Data Path): high-performance packet processing
- eBPF-based networking: Cilium
- Kprobes and tracepoints for dynamic instrumentation
- BPFTrace and bcc toolkit
- eBPF for security (runtime threat detection)
- eBPF for observability (Pixie, Parca)

### AI / ML Infrastructure

- Model serving: TorchServe, NVIDIA Triton Inference Server
- Feature stores (Feast, Tecton)
- ML pipelines: Kubeflow, MLflow, Metaflow
- Inference at scale: batching, caching, quantization
- Vector databases: Pinecone, Weaviate, Qdrant, pgvector
- RAG (Retrieval-Augmented Generation) architecture
- Embedding pipelines and chunking strategies

### Edge & Emerging Patterns

- Edge computing patterns
- WebAssembly (WASM) and WASI as a universal runtime
- WebRTC for peer-to-peer communication
- 5G and Multi-access Edge Computing (MEC)
- IoT data ingestion patterns (MQTT, CoAP)
- Confidential computing and Trusted Execution Environments (TEE)

---

## Recommended Book Canon

| Book | Author | What It Masters |
|------|--------|----------------|
| *Designing Data-Intensive Applications* | Martin Kleppmann | DB internals, replication, consensus, stream processing — the single most important book |
| *Google SRE Book* (free online) | Google SRE Team | Reliability, SLO, capacity planning, postmortems |
| *Distributed Systems* 3rd ed. (free PDF) | Tanenbaum & Van Steen | Academic foundations: clocks, consistency, coordination |
| *Database Internals* | Alex Petrov | LSM-trees, B-trees, consensus algorithms deep dive |
| *Understanding Distributed Systems* | Roberto Vitillo | Practical modern distributed patterns |
| *Systems Performance* | Brendan Gregg | Linux internals, profiling, flame graphs, BPF |
| *The Art of Capacity Planning* | John Allspaw | Capacity planning methodology |

---

## Key Academic Papers

| Paper | Year | Why It Matters |
|-------|------|---------------|
| Amazon Dynamo | 2007 | Foundational paper on eventual consistency and leaderless replication |
| Google Bigtable | 2006 | Wide-column storage model and SSTable design |
| Google GFS | 2003 | Distributed file system design for commodity hardware |
| Google Spanner | 2012 | Globally consistent database using TrueTime |
| Raft Consensus | 2014 | Understandable consensus algorithm (alternative to Paxos) |
| CAP Theorem (Brewer) | 2000 | Fundamental trade-off in distributed systems |
| FLP Impossibility | 1985 | Theoretical limits of consensus in async systems |
| CRDT survey (Shapiro) | 2011 | Conflict-free replicated data types |
| Kafka (LinkedIn) | 2011 | Log-based message broker architecture |
| Consistent Hashing | 1997 | Karger et al. — distributed hash tables |

---

*This atlas covers 200+ topics across 14 sections. Revisit earlier sections as your depth grows — the strongest engineers continuously refine their mental models rather than just accumulating new topics.*