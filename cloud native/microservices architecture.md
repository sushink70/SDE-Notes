# Microservices Architecture: Comprehensive Deep-Dive

A distributed systems paradigm where applications decompose into independently deployable, loosely coupled services that communicate over network boundaries. Each service owns its data, exposes well-defined APIs, and can fail, scale, and evolve autonomously. The architecture trades monolithic simplicity for operational flexibility, fault isolation, and organizational scalability—at the cost of distributed systems complexity, network unreliability, and sophisticated observability requirements.

**Core trade-off**: You gain deployment independence, technology heterogeneity, and blast-radius containment but inherit consistency challenges, latency penalties, debugging complexity, and the need for mature DevOps/SRE practices. Success demands strong infrastructure automation, comprehensive monitoring, and cultural readiness for decentralized ownership.

**Security implication**: Every service boundary is now a trust boundary requiring authentication, authorization, encrypted transport, input validation, and audit. Attack surface expands exponentially with service count—defense requires zero-trust networking, identity-aware proxies, and runtime security policies.

**Production reality**: Microservices are not inherently better than monoliths. They're an organizational scaling tool that makes sense when team size, deployment frequency, or domain complexity justifies the operational overhead.

---

## Table of Contents

1. **Foundational Principles & Domain-Driven Design**
2. **Service Boundaries & Decomposition Strategies**
3. **Communication Patterns: Synchronous vs Asynchronous**
4. **Data Management & Distributed Transactions**
5. **Service Discovery & Load Balancing**
6. **API Gateway & Edge Security**
7. **Resilience, Fault Tolerance & Failure Modes**
8. **Observability: Logging, Metrics, Tracing**
9. **Security Architecture & Zero-Trust Networking**
10. **Deployment Models & Infrastructure**
11. **Testing Strategies Across Boundaries**
12. **Organizational & Cultural Considerations**
13. **Anti-Patterns & Failure Modes**
14. **Migration Strategies from Monoliths**
15. **Production Operations & Incident Response**

---

## 1. Foundational Principles & Domain-Driven Design

### Core Tenets

**Service Autonomy**: Each service must be independently deployable without coordinating releases with other teams. This requires backward-compatible API evolution, feature flags for progressive rollout, and versioning strategies that don't create tight coupling.

**Single Responsibility Principle at Service Level**: A service should have one reason to change—mapped to a bounded context in domain-driven design terms. It owns all business logic, data, and operations within that context. Violating this creates distributed monoliths where services share databases or require synchronized deployments.

**Decentralized Data Management**: Each service owns its persistent state and exposes it only through APIs. Direct database sharing is forbidden—it creates hidden coupling, prevents independent scaling, and breaks encapsulation. Services become the authoritative source for their domain entities.

**Design for Failure**: In distributed systems, failure is guaranteed. Networks partition, processes crash, dependencies time out. Services must implement defensive patterns: timeouts, retries with exponential backoff, circuit breakers, bulkheads, and graceful degradation. Every synchronous call is a potential failure point.

**Infrastructure Automation**: Manual operations don't scale beyond 3-5 services. You need Infrastructure-as-Code for provisioning, CI/CD pipelines for deployment, automated testing at every layer, and self-service environments for developers. Toil elimination is mandatory.

### Domain-Driven Design (DDD) Integration

**Bounded Contexts**: These define the semantic boundaries of your services. Within a bounded context, a term like "Customer" has precise, unambiguous meaning. Across contexts, the same entity may have different representations—a "Customer" in billing is not identical to "Customer" in support. Context boundaries prevent model pollution.

**Ubiquitous Language**: Teams develop a shared vocabulary with domain experts that appears identically in code, APIs, documentation, and conversations. This reduces translation errors and makes the codebase self-documenting. If your code says `PlaceOrder()` but the business says "submit order request," you've introduced cognitive overhead.

**Aggregates & Consistency Boundaries**: An aggregate is a cluster of domain objects treated as a transactional unit. The aggregate root is the only entry point—external services can only reference it by ID, never hold direct pointers to internal entities. This enforces consistency rules and defines your transaction scope in a distributed system. Each aggregate maps naturally to a service or a closely related set of operations within one service.

**Anti-Corruption Layers (ACL)**: When integrating with legacy systems or external services with poor models, the ACL translates their concepts into your domain language. This prevents "bad" models from infecting your clean architecture. The ACL is bidirectional—it also translates your model when calling the external system.

**Context Mapping**: Explicitly document relationships between bounded contexts: Shared Kernel (common code shared by teams, high coordination cost), Customer-Supplier (downstream depends on upstream's API), Conformist (downstream accepts upstream's model as-is), Partnership (mutual dependency requiring coordinated evolution). Understanding these relationships prevents surprise breakages during refactoring.

---

## 2. Service Boundaries & Decomposition Strategies

### Identifying Service Boundaries

**Business Capability Decomposition**: Organize around what the business does, not how. Capabilities like "Order Management," "Inventory," "Customer Profile," and "Recommendations" map to services. This aligns technical structure with business organization and makes ownership clear.

**Subdomain Analysis**: Separate core domains (competitive differentiators), supporting domains (necessary but not unique), and generic domains (off-the-shelf solutions). Core domains get the most engineering investment and the cleanest implementations. Generic domains might use SaaS or open-source tools. Supporting domains are candidates for simplification or eventual outsourcing.

**Team Topology Alignment**: Conway's Law states that system architecture mirrors organizational communication patterns. If you have three teams, you'll build three major components. Use reverse Conway: design team boundaries to match desired service boundaries. A team should own 1-3 related services—more than that and cognitive load becomes unsustainable.

**Volatility-Based Decomposition**: Separate stable components from frequently changing ones. If billing logic changes quarterly but user authentication is stable, isolate them. This prevents deployment risk from rippling across the entire system.

**Scalability Requirements**: Services with different load profiles should separate. A recommendation engine handling millions of requests per second doesn't belong in the same process as an admin panel serving 10 requests per minute. Separate services allow independent horizontal scaling.

### Granularity Trade-offs

**Too Fine-Grained (Nanoservices)**: Services with 50-100 lines of code create explosion of operational complexity. You spend more time managing network calls, service discovery, and deployment than writing business logic. Common symptoms: every function becomes a service, excessive inter-service chattiness, distributed spaghetti code.

**Too Coarse-Grained (Distributed Monolith)**: Services that must deploy together, share databases, or make dozens of synchronous calls per request defeat the purpose. You've inherited distributed systems complexity without gaining deployment independence. Symptoms: coordinated releases, shared transaction scopes, tight coupling.

**Right-Sizing Heuristics**: A service should be small enough that a new team member can understand it in 1-2 weeks, large enough to deliver a complete business capability, and independently deployable within a sprint. Team size usually caps at 2-pizza rule (6-10 people), each owning 1-3 services.

### Technical Boundaries

**Shared-Nothing Architecture**: No shared memory, no shared disk, no shared databases. Communication happens exclusively over network APIs. This enables polyglot persistence, independent scaling, and true fault isolation.

**API Contracts as Boundaries**: The API (REST, gRPC, GraphQL, message schemas) is the **only** contract. Internal implementation details—language, framework, database—are completely hidden. This enables technology heterogeneity and independent evolution.

**Separate Build Artifacts**: Each service has its own repository (or mono-repo with clear module boundaries), independent CI/CD pipeline, versioned releases, and deployment schedule. Build times should be sub-5 minutes to enable rapid iteration.

---

## 3. Communication Patterns: Synchronous vs Asynchronous

### Synchronous Communication

**Request-Response Over HTTP/gRPC**: Client blocks waiting for server response. Simple mental model, easy debugging with distributed tracing, natural for user-facing APIs where immediate feedback is required.

**Protocol Choices**:
- **REST over HTTP/1.1 or HTTP/2**: Human-readable, ubiquitous tooling, well-understood semantics. Inefficient for high-throughput scenarios due to text encoding and header overhead.
- **gRPC over HTTP/2**: Binary protocol buffers, multiplexing, streaming support, code generation from schemas. 5-10x more efficient than JSON/REST for internal service mesh communication. Requires HTTP/2 infrastructure and careful schema evolution.
- **GraphQL**: Client-specified queries reduce over-fetching and under-fetching. Excellent for BFF (Backend-for-Frontend) patterns where different UIs need different data shapes. Complexity comes from query planning, N+1 problems, and authorization at the field level.

**Failure Modes**: Cascading failures when upstream services slow or crash, tight coupling between caller and callee availability, amplification of latency (each hop adds network RTT), potential for distributed deadlocks in circular dependencies.

**Mitigation**: Timeouts on every call (default 1-3 seconds for internal services, 100-500ms for latency-critical paths), circuit breakers to fail fast when downstream is degraded, retries with exponential backoff and jitter, request hedging for P99 latency improvement.

### Asynchronous Communication

**Event-Driven Messaging**: Services publish events to a message broker (Kafka, RabbitMQ, NATS, Pulsar) when state changes. Consumers process events at their own pace without blocking the publisher. Decouples services in both time and space—publisher doesn't know or care who consumes events.

**Message Patterns**:
- **Publish-Subscribe**: One event, multiple consumers. Used for fanout scenarios like "OrderPlaced" triggering inventory, shipping, and notification services.
- **Point-to-Point Queues**: One message, one consumer. Work distribution pattern for background jobs or task processing.
- **Event Sourcing**: State changes are stored as immutable event log. Current state is derived by replaying events. Enables time-travel debugging, audit trails, and CQRS (Command Query Responsibility Segregation).

**Broker Selection Criteria**:
- **Kafka**: High throughput (millions of messages/sec), durable log-based storage, ordering guarantees per partition, complex operational model. Best for event streaming, analytics pipelines, and high-volume data integration.
- **RabbitMQ**: Flexible routing, rich queuing semantics, lower throughput than Kafka, simpler operations. Good for task queues, RPC patterns, and moderate-scale messaging.
- **NATS**: Lightweight, low latency, designed for cloud-native environments, limited persistence (JetStream adds durability). Excellent for ephemeral messaging and service mesh data planes.

**Eventual Consistency Challenges**: Data is temporarily inconsistent across services. A "Customer" created in one service may not be visible in another for milliseconds to seconds. UIs must handle this—show "processing" states, avoid immediate read-after-write assumptions, implement idempotency to handle duplicate events.

**Ordering and Causality**: Messages may arrive out of order. If you process "OrderCancelled" before "OrderPlaced," your state is corrupted. Solutions: version vectors, logical clocks (Lamport, vector clocks), partition keys to guarantee ordering within a stream, idempotent consumers that can handle replays.

**Delivery Guarantees**:
- **At-Most-Once**: Message may be lost. Unacceptable for most business logic.
- **At-Least-Once**: Message may be delivered multiple times. Requires idempotent consumers—processing the same event twice produces the same result.
- **Exactly-Once**: Holy grail, extremely difficult in distributed systems. Kafka achieves this through transactional writes and consumer offset management, but it's expensive and has edge cases.

### Hybrid Approaches

**Command Query Responsibility Segregation (CQRS)**: Writes go to a command service, which publishes events. Read services consume events and maintain optimized, denormalized views. This separates write models (normalized, transactional) from read models (denormalized, eventually consistent, query-optimized).

**Saga Pattern for Distributed Transactions**: Long-running business processes spanning multiple services. Each step is a local transaction publishing an event. If a step fails, compensating transactions undo previous steps. Two styles:
- **Choreography**: Services react to events autonomously. Decentralized, hard to reason about global state, prone to cyclic dependencies.
- **Orchestration**: Central coordinator service manages the saga. Easier to understand, single point of failure, coordinator becomes a bottleneck.

**Backend-for-Frontend (BFF)**: Each client type (web, mobile, IoT) gets a dedicated API gateway service that aggregates downstream microservices. Prevents mobile apps from making 20 HTTP calls to render one screen, allows client-specific optimizations, and isolates client protocol changes from core services.

---

## 4. Data Management & Distributed Transactions

### Database-per-Service Pattern

**Rationale**: Shared databases create tight coupling. Changes to schema, indexes, or query patterns in one service can break others. Database contention becomes a scaling bottleneck. Security is compromised—services can bypass APIs and access data directly.

**Implementation**: Each service has its own database instance (logical or physical), schema, and migration process. No direct SQL queries across service boundaries—data access happens exclusively through APIs or events.

**Polyglot Persistence**: Different services use different database technologies based on their access patterns:
- **Relational (PostgreSQL, MySQL)**: Transactional consistency, complex joins, strong schema enforcement. Good for financial transactions, user management, inventory.
- **Document Stores (MongoDB, CouchDB)**: Flexible schema, nested documents, horizontal scalability. Fits content management, product catalogs, session storage.
- **Key-Value (Redis, DynamoDB)**: Ultra-low latency, simple data model, horizontal scaling. Cache layers, session stores, rate limiting.
- **Graph Databases (Neo4j, Amazon Neptune)**: Relationship queries, traversals, fraud detection. Social networks, recommendation engines, identity graphs.
- **Time-Series (InfluxDB, TimescaleDB)**: Optimized for time-stamped data, downsampling, retention policies. Metrics, IoT telemetry, application performance monitoring.

### Data Consistency Models

**Strong Consistency**: Reads always return the most recent write. Requires coordination (distributed locks, consensus protocols like Paxos/Raft), sacrifices availability during partitions (CAP theorem), limits scalability.

**Eventual Consistency**: Replicas converge to the same state given enough time without writes. Allows high availability and partition tolerance, requires application-level conflict resolution, complicates UI/UX.

**Causal Consistency**: Preserves cause-effect relationships. If write A causally precedes write B, all processes see A before B. Weaker than strong consistency, stronger than eventual. Implements via vector clocks or Conflict-Free Replicated Data Types (CRDTs).

### Distributed Transaction Patterns

**Two-Phase Commit (2PC)**: Coordinator asks all participants to prepare, then commit if all succeed or abort if any fail. Guarantees ACID properties but is blocking—if coordinator crashes during commit phase, participants are stuck. Not suitable for high-availability systems. Rarely used in microservices due to availability cost.

**Saga Pattern (Detailed)**:
- **Example**: Book flight, reserve hotel, charge card. If card charge fails, cancel hotel reservation and flight booking via compensating transactions.
- **Choreography Implementation**: FlightService publishes "FlightBooked" event. HotelService listens, reserves room, publishes "HotelReserved." PaymentService listens, charges card. If charge fails, publishes "PaymentFailed." HotelService and FlightService listen for this and execute compensations.
- **Orchestration Implementation**: TripOrchestratorService calls FlightService, then HotelService, then PaymentService. If PaymentService fails, orchestrator explicitly calls compensating APIs on HotelService and FlightService.
- **Challenges**: Compensating transactions aren't true rollbacks—if you sent a confirmation email, you can't unsend it. Some actions are non-compensable. Need to design idempotent operations and handle partial failures gracefully.

**Event Sourcing as Alternative**: Store every state change as an immutable event. Current state is the sum of all events. To "undo" an action, append a new compensating event. Provides complete audit trail, enables time-travel debugging, supports complex event-driven workflows. Downside: queries require event replay (mitigated by snapshotting), eventual consistency, and increased storage.

### Data Denormalization and Replication

**Command-Query Separation**: Write path appends events, read path maintains materialized views. Read models can be highly denormalized—duplicating data across services to optimize query performance. Example: OrderService stores order details; WarehouseService maintains a local copy of product metadata to avoid querying ProductService on every pick operation.

**Change Data Capture (CDC)**: Database transaction log becomes event stream. Tools like Debezium watch database binlogs and publish row-level changes to Kafka. Downstream services consume these to maintain local replicas. Keeps services decoupled while enabling near-real-time data sync.

**Cache Invalidation**: Hardest problem in distributed systems. Options: time-based TTL (eventual consistency), event-based invalidation (publish cache-bust events when data changes), read-through caches that query source-of-truth on miss, write-through caches that update source and cache atomically.

---

## 5. Service Discovery & Load Balancing

### Service Discovery Patterns

**Client-Side Discovery**: Client queries a service registry (Consul, Eureka, etcd), gets list of healthy instances, selects one via load-balancing algorithm, makes direct call. Gives client control over load balancing but couples client to registry technology and requires client libraries.

**Server-Side Discovery (Service Mesh)**: Client makes request to a local proxy (sidecar), which handles discovery, load balancing, retries, and encryption. Client is unaware of service topology. Implemented by Envoy-based meshes (Istio, Linkerd). Adds operational complexity but centralizes cross-cutting concerns.

**DNS-Based Discovery**: Services registered as DNS records. Kubernetes uses this—each service gets a stable DNS name. Simple, ubiquitous, but DNS caching and TTL propagation delays can cause stale routing.

### Service Registry Requirements

**Health Checking**: Registry must track instance health via active probes (HTTP health endpoints, TCP connections) or passive monitoring (traffic success rates). Unhealthy instances are removed from routing pool automatically.

**Heartbeat Mechanism**: Instances periodically report liveness. If heartbeats stop, instance is marked down. Prevents routing to crashed processes or partitioned nodes.

**Consistency vs Availability Trade-off**: Using a CP (Consistent-Partition tolerant) registry like Consul with Raft means registry becomes unavailable during network partitions. Using an AP (Available-Partition tolerant) system means you might route to a dead instance temporarily. Choose based on failure mode tolerance.

### Load Balancing Strategies

**Round-Robin**: Equal distribution, simple, ignores instance load. Problematic if instances have heterogeneous capacity or request costs vary.

**Least-Connections**: Route to instance with fewest active connections. Better for long-lived connections but requires tracking state.

**Weighted Round-Robin**: Assign weights based on instance capacity. Useful for canary deployments (route 5% traffic to new version) or heterogeneous hardware.

**Latency-Aware (P2C - Power of Two Choices)**: Randomly select two instances, route to the one with lower latency. Balances load better than round-robin with minimal overhead.

**Consistent Hashing**: Map requests to instances via hash ring. Adding/removing instances only affects 1/N of keys. Essential for cache services to minimize cache misses during scaling.

**Zone/Region Awareness**: Prefer instances in the same availability zone to reduce latency and data transfer costs. Fall back to cross-zone only if local capacity is exhausted.

---

## 6. API Gateway & Edge Security

### API Gateway Responsibilities

**Routing & Aggregation**: Single entry point for external clients. Routes requests to backend services, aggregates multiple service calls into single response (reduces client round trips), handles protocol translation (REST to gRPC, HTTP/1.1 to HTTP/2).

**Authentication & Authorization**: Validates client credentials (OAuth2, JWT, API keys), enforces rate limits per client, verifies scopes/permissions before forwarding requests. Offloads this from individual services.

**TLS Termination**: Handles HTTPS encryption at the edge, re-encrypts traffic to backend services (mTLS), manages certificate rotation, enforces minimum TLS versions (1.2+).

**Request Transformation**: Rewrites URLs, modifies headers, transforms request/response formats to maintain backward compatibility while evolving backend APIs.

**Caching**: Stores frequently requested responses at the edge, reducing load on backend services. Implements cache-control headers, surrogate keys for fine-grained invalidation.

**Observability**: Centralized logging of all external requests, distributed tracing headers injection, metrics on error rates, latencies, and traffic patterns.

### Security Architecture at the Edge

**DDoS Protection**: Rate limiting per IP, CAPTCHA challenges for suspicious traffic, geographic blocking, integration with CDNs (CloudFlare, Fastly) for volumetric attack mitigation.

**Input Validation**: Schema validation (OpenAPI, Protobuf), size limits on payloads, sanitization of user input, blocking of known attack patterns (SQL injection, XSS).

**CORS (Cross-Origin Resource Sharing)**: Controlled via gateway policies. Define allowed origins, methods, headers. Prevents unauthorized cross-site requests.

**OAuth2/OIDC Integration**: Gateway acts as OAuth2 resource server, validates access tokens with authorization server, extracts user identity and scopes, forwards claims to backend services via headers or JWT propagation.

**API Versioning**: Gateway routes based on version headers or URL prefixes, maintains multiple backend versions during migration periods, enforces deprecation timelines.

### Gateway Deployment Patterns

**Centralized Gateway**: Single gateway for all APIs. Simpler operations, single point of failure, potential bottleneck. Mitigate with horizontal scaling and health checks.

**Decentralized Gateway per Team/Domain**: Each team operates their own gateway. Reduces blast radius, allows independent evolution, increases operational overhead, requires strong governance to prevent inconsistencies.

**BFF (Backend-for-Frontend) Gateways**: Separate gateways for web, mobile, partner APIs. Optimizes for client-specific needs, reduces payload sizes, enables client-specific caching and rate limits.

---

## 7. Resilience, Fault Tolerance & Failure Modes

### Failure Modes in Distributed Systems

**Network Partitions**: Two parts of the system can't communicate. Services must decide whether to prioritize consistency (reject requests) or availability (serve potentially stale data). CAP theorem forces this choice.

**Byzantine Failures**: Components behave arbitrarily—sending corrupted data, lying about state, or acting maliciously. Mitigated by cryptographic signatures, input validation, and zero-trust architectures.

**Cascading Failures**: Failure in one service triggers failures in dependent services. Example: database slowdown causes app server thread pool exhaustion, which causes load balancer health checks to fail, which triggers autoscaling that launches more unhealthy instances.

**Thundering Herd**: Many clients retry failed requests simultaneously, overwhelming the recovering service. Mitigate with exponential backoff, jitter in retry timings, and circuit breakers.

**Poison Messages**: A message that crashes the consumer every time it's processed. If the queue redelivers it repeatedly, the consumer never makes progress. Solutions: dead-letter queues, message introspection before full processing, separate retry/poison-handling pipelines.

### Resilience Patterns

**Timeouts**: Every network call must have a deadline. Default to conservative values (1-3 seconds for internal services), shorter for user-facing requests (100-500ms). Prevents threads/goroutines from blocking indefinitely.

**Retries with Exponential Backoff**: Retry failed requests with increasing delays (100ms, 200ms, 400ms, 800ms). Add jitter (random offset) to prevent synchronized retries. Limit total retry count to prevent infinite loops.

**Circuit Breaker**: Tracks failure rate. If failures exceed threshold (e.g., 50% over 10 seconds), the circuit "opens"—subsequent requests fail immediately without calling the unhealthy service. After a timeout, the circuit enters "half-open" state, allowing a few test requests. If they succeed, circuit closes; if they fail, circuit re-opens. Prevents wasting resources on doomed requests.

**Bulkheads**: Isolate resources so failure in one area doesn't consume all capacity. Example: separate thread pools for different downstream dependencies. If database calls are slow, they exhaust their dedicated pool but don't block API calls that don't need the database.

**Rate Limiting**: Prevent abuse and protect services from overload. Token bucket algorithm (refill tokens at fixed rate, requests consume tokens), leaky bucket (process requests at fixed rate, drop excess), fixed/sliding window counters. Implement both client-side (prevent self-DOS) and server-side (protect against malicious clients).

**Graceful Degradation**: When dependencies fail, serve reduced functionality rather than total failure. Example: e-commerce site shows product catalog from cache when recommendations service is down. Clearly communicate degraded state to users.

**Load Shedding**: When overloaded, reject low-priority requests to preserve capacity for critical work. Implement via priority queues, request classification, and adaptive admission control. Reject work at the edge to avoid wasting backend resources.

**Chaos Engineering**: Intentionally inject failures (kill instances, introduce latency, partition networks) in production to validate resilience. Netflix's Chaos Monkey randomly terminates instances. Ensures teams build fault-tolerant systems from day one.

### Idempotency

**Definition**: An operation produces the same result whether executed once or multiple times. Essential for safe retries in distributed systems.

**Implementation Strategies**:
- **Idempotency Keys**: Client generates a unique ID (UUID) per request, includes it in the request. Server stores completed request IDs, ignores duplicates.
- **Natural Idempotency**: Operations like "SET" or "DELETE" are naturally idempotent. "Add $10 to balance" is not; "Set balance to $100" is.
- **Conditional Writes**: Use version numbers or ETags. Update only if current version matches expected version. Prevents lost updates and enables safe retries.

---

## 8. Observability: Logging, Metrics, Tracing

### Three Pillars of Observability

**Logs**: Immutable, timestamped records of discrete events. Useful for debugging specific incidents, auditing, and understanding system behavior. Challenges: volume (high-traffic systems generate terabytes per day), cost (storage and indexing), retention policies.

**Metrics**: Aggregated numeric data over time (counters, gauges, histograms). Efficient for monitoring trends, alerting, and capacity planning. Examples: request rate, error rate, latency percentiles (P50, P95, P99), resource utilization (CPU, memory, disk).

**Traces**: End-to-end request flows through distributed systems. Each request gets a unique trace ID, each service operation becomes a span. Visualizes latency breakdown, identifies bottlenecks, reveals cross-service dependencies.

### Logging Best Practices

**Structured Logging**: Emit JSON or other machine-parseable formats. Include correlation IDs (request ID, user ID, session ID), severity levels, timestamps in ISO8601, contextual metadata. Avoid unstructured text—makes aggregation and searching painful.

**Log Levels**: ERROR (requires immediate action), WARN (potential issue), INFO (significant business events), DEBUG (detailed diagnostic info, disabled in production). Never log sensitive data (passwords, tokens, PII) even at DEBUG level.

**Centralized Log Aggregation**: Ship logs to a central system (ELK stack, Loki, Splunk). Enables cross-service search, correlation, alerting. Use log shippers (Fluentd, Fluent Bit, Vector) that handle buffering, retries, and batching.

**Sampling**: In high-throughput systems, log every request at INFO level is prohibitive. Sample based on error conditions, user IDs (log 1% of users fully), or adaptive sampling (always log errors, sample successes).

### Metrics Collection

**Metric Types**:
- **Counter**: Monotonically increasing value (total requests, errors). Query rate of change.
- **Gauge**: Point-in-time value that can go up or down (current memory usage, queue depth).
- **Histogram**: Distribution of values, bucketed (request latency, response sizes). Enables percentile calculations.
- **Summary**: Similar to histogram but calculates percentiles client-side. Lower query cost, higher ingestion cost.

**Cardinality Management**: Metrics with high-cardinality labels (user IDs, IP addresses) explode storage and query costs. Use low-cardinality dimensions (service, region, status code). If you need high-cardinality analysis, use logs or traces.

**Prometheus Model**: Pull-based scraping, time-series database, PromQL query language, built-in alerting. Industry standard for cloud-native metrics. Integrates with Kubernetes via service discovery.

**Alerting Philosophy**: Alert on symptoms, not causes. "Response time P99 > 500ms" is better than "CPU > 80%." Alert on user-facing impact. Use SLO-based alerts—trigger when error budget is at risk. Avoid alert fatigue by tuning thresholds and using proper aggregation windows.

### Distributed Tracing

**Trace Propagation**: Inject trace context (trace ID, span ID, sampling decision) into request headers. Each service extracts context, creates child spans for its operations, injects updated context when calling downstream services. Standards: W3C Trace Context, B3 (Zipkin).

**Sampling Strategies**:
- **Head-Based Sampling**: Decision made at trace origin (1% of all traces). Simple, biased—may miss rare errors.
- **Tail-Based Sampling**: Decision made after trace completes, based on properties (errors, high latency). Captures interesting traces but requires buffering entire trace before deciding.
- **Adaptive Sampling**: Adjust sample rate dynamically based on traffic volume, error rates, or specific user cohorts.

**Span Enrichment**: Add tags for error status, user ID, database query, HTTP method/path. Enables filtering and aggregation in trace analysis tools (Jaeger, Zipkin, Tempo).

**Tracing as a Service**: OpenTelemetry provides vendor-neutral instrumentation. Backends: Jaeger (open-source), Tempo (Grafana's backend), Lightstep, Honeycomb, Datadog APM. Choose based on retention needs, query capabilities, cost.

### Unified Observability

**Correlation**: Link logs, metrics, and traces via shared identifiers (trace ID in logs, trace ID as metric label). Enables jumping from an alert to traces to detailed logs in one click.

**Dashboards**: Build service-level dashboards showing RED metrics (Rate, Errors, Duration), resource utilization, dependency health. Use tools like Grafana, which integrates Prometheus, Loki, Tempo.

**Service-Level Objectives (SLOs)**: Define acceptable performance (99.9% availability, P95 latency < 200ms). Track error budgets—how much failure is allowed before breaching SLO. Prioritize work based on error budget consumption.

---

## 9. Security Architecture & Zero-Trust Networking

### Zero-Trust Principles

**Never Trust, Always Verify**: No implicit trust based on network location. Every service-to-service call requires authentication and authorization, even within the same data center. Prevents lateral movement after perimeter breach.

**Least Privilege Access**: Services get minimum permissions needed. A frontend service shouldn't have database admin rights. Use role-based access control (RBAC) or attribute-based access control (ABAC).

**Assume Breach**: Design as if attackers are already inside your network. Encrypt all traffic, monitor for anomalous behavior, segment networks, implement runtime threat detection.

### Service-to-Service Authentication

**Mutual TLS (mTLS)**: Both client and server present certificates, verify each other's identity. Provides strong authentication, encryption in transit, and non-repudiation. Challenges: certificate lifecycle management (issuance, rotation, revocation), performance overhead (CPU cost of TLS handshakes), PKI complexity.

**Service Mesh Implementation**: Sidecars (Envoy proxies) handle mTLS transparently. Control plane (Istio, Linkerd) issues short-lived certificates (hours, not years), auto-rotates them, enforces policy. Application code sees plaintext, sidecar handles crypto.

**JWT-Based Authentication**: Services issue and verify JSON Web Tokens. Tokens contain claims (user ID, roles, expiration). Stateless—no need to query auth service per request. Risks: token theft (mitigate with short expiration), secret management (rotate signing keys), size overhead (large tokens increase request size).

**SPIFFE/SPIRE**: Open standard for service identity. SPIRE (SPIFFE Runtime Environment) issues X.509 SVIDs (SPIFFE Verifiable Identity Documents) to workloads based on attestation (kernel, kubelet, cloud provider identity). Interoperable with any system supporting X.509.

### Authorization Patterns

**Centralized Policy Enforcement (API Gateway)**: Gateway validates tokens, checks permissions, forwards authorized requests with user context. Simplifies service logic but gateway becomes a high-value target and potential bottleneck.

**Decentralized Policy Enforcement**: Each service validates tokens and enforces its own authorization rules. More resilient, harder to maintain consistency. Mitigate with shared policy libraries or external policy engines.

**Policy-as-Code (Open Policy Agent)**: Define authorization rules in Rego language, deploy policies alongside services, evaluate policies on every request. Decouples policy logic from application code, enables policy versioning and auditing.

**OAuth2/OIDC for User Delegation**: OAuth2 provides delegated authorization (user grants service limited access to their data), OIDC adds identity layer (user authentication). Authorization server issues accesstokens (short-lived, scoped), refresh tokens (long-lived, used to obtain new access tokens). Prevents long-lived credentials from leaking.

### Network Security

**Network Segmentation**: Isolate services into network zones based on trust level. DMZ for public-facing services, internal network for business logic, restricted network for databases/secrets. Use VPCs, subnets, security groups, network policies (Kubernetes NetworkPolicy).

**Egress Control**: Restrict outbound connections. Services should only connect to known, approved destinations. Prevents data exfiltration and command-and-control channels after compromise. Implement via egress gateways, firewall rules, service mesh policies.

**DDoS Mitigation**: Rate limiting at multiple layers (edge CDN, API gateway, service level), connection limits, SYN cookies, anycast routing to distribute attack traffic. Cloud providers offer DDoS protection services (AWS Shield, Cloudflare).

**Service Mesh Security**: Meshes enforce encrypted communication (mTLS), traffic policies (allow/deny rules), and observability. Istio's authorization policies define who can call what, based on service identity, JWT claims, request attributes.

### Secrets Management

**Never Hardcode Secrets**: No passwords, API keys, or tokens in code or config files checked into version control. Use environment variables as a minimum, secrets managers as best practice.

**Secrets Vaults**: HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager. Store encrypted secrets, provide fine-grained access control, audit all access, rotate secrets automatically, support dynamic secret generation (generate database credentials on-demand, expire after use).

**Secret Injection**: Inject secrets at runtime via environment variables, mounted volumes (Kubernetes secrets), or sidecar containers. Secrets never touch disk in plaintext except in memory.

**Rotation Strategy**: Rotate secrets on a schedule (quarterly, monthly) and immediately after suspected compromise. Implement dual-write (both old and new secrets valid during rotation window) to prevent downtime.

### Threat Modeling

**STRIDE Framework**: Categorize threats—Spoofing (impersonation), Tampering (data modification), Repudiation (denying actions), Information Disclosure (data leaks), Denial of Service (availability attacks), Elevation of Privilege (unauthorized access).

**Attack Surface Analysis**: Identify all external interfaces (APIs, message queues, admin panels), authentication mechanisms, data stores, third-party integrations. Each is a potential entry point. Document trust boundaries, data flows, privilege levels.

**Threat Scenarios**: "Attacker compromises API service—what data can they access?" "Insider exfiltrates customer data—what controls would detect it?" "Service certificate expires—what breaks?" Build threat trees, assign probabilities, prioritize mitigations.

**Defense in Depth**: Layer multiple controls. If one fails, others provide backup. Example: API authentication (layer 1) + authorization (layer 2) + input validation (layer 3) + audit logging (layer 4) + anomaly detection (layer 5).

### Data Protection

**Encryption at Rest**: Encrypt databases, object storage, message queues at rest. Use platform-provided encryption (AWS RDS encryption, Azure Storage Service Encryption) or application-level encryption. Manage keys separately from encrypted data.

**Encryption in Transit**: TLS 1.2+ for all network communication. Disable older protocols (SSLv3, TLS 1.0/1.1). Use strong cipher suites (AES-GCM), enforce forward secrecy (ECDHE).

**Data Classification**: Label data based on sensitivity (public, internal, confidential, restricted). Apply controls based on classification—restricted data requires encryption, access logging, geographic restrictions.

**Tokenization & Masking**: Replace sensitive data with non-sensitive tokens (credit card numbers become random IDs). Store mapping in secure vault. Prevents sensitive data exposure in logs, caches, error messages. Masking shows partial data (last 4 digits of card).

### Compliance & Auditing

**Audit Trails**: Log all access to sensitive data (who, what, when, from where). Immutable logs stored separately from application infrastructure. Required for SOC2, PCI-DSS, HIPAA.

**Regulatory Requirements**:
- **GDPR**: Data residency (EU data stays in EU), right to deletion, consent management, breach notification (72 hours).
- **PCI-DSS**: Cardholder data encryption, network segmentation, access controls, regular penetration testing.
- **SOC2**: Security, availability, processing integrity, confidentiality, privacy controls documented and tested.

**Runtime Security**: Detect anomalies in production—unexpected process execution, file modifications, network connections. Tools: Falco (Kubernetes), Aqua Security, Twistlock. Alert on deviations from known-good behavior.

---

## 10. Deployment Models & Infrastructure

### Containerization

**Container Benefits**: Immutable artifacts, consistent environments (dev/staging/prod), fast startup times (seconds vs minutes for VMs), efficient resource utilization (pack more workloads per host), portable across clouds.

**Image Building**: Multi-stage builds (compile in builder image, copy binary to minimal runtime image), layer caching (order Dockerfile instructions from least to most frequently changing), minimal base images (Alpine, distroless), vulnerability scanning (Trivy, Clair).

**Image Security**: Don't run as root (use USER directive), read-only root filesystem, drop unnecessary capabilities (NET_RAW, SYS_ADMIN), scan for CVEs, sign images (Docker Content Trust, Sigstore Cosign), verify signatures before deployment.

### Orchestration: Kubernetes Deep Dive

**Control Plane Components**:
- **API Server**: Front-end for control plane, validates and processes API requests, stores state in etcd.
- **etcd**: Distributed key-value store, source of truth for cluster state. Consistency via Raft consensus.
- **Scheduler**: Assigns pods to nodes based on resource requirements, affinity rules, taints/tolerations.
- **Controller Manager**: Runs control loops (ReplicaSet ensures desired pod count, Deployment handles rolling updates).

**Node Components**:
- **kubelet**: Ensures containers are running per pod spec, reports node status, performs liveness/readiness probes.
- **kube-proxy**: Implements service networking, load balancing via iptables or IPVS.
- **Container Runtime**: CRI-compliant runtime (containerd, CRI-O) manages container lifecycle.

**Workload Resources**:
- **Pod**: Smallest deployable unit, one or more containers sharing network namespace and storage.
- **ReplicaSet**: Maintains desired number of pod replicas, self-heals on pod failures.
- **Deployment**: Manages ReplicaSets, handles rolling updates, rollbacks.
- **StatefulSet**: For stateful workloads requiring stable network identity, persistent storage, ordered deployment/scaling.
- **DaemonSet**: Runs one pod per node (logging agents, monitoring collectors, network plugins).
- **Job/CronJob**: Batch processing, scheduled tasks.

**Networking Models**:
- **Flat Network**: Every pod gets an IP, can communicate with every other pod without NAT. Implemented by CNI plugins (Calico, Cilium, Flannel).
- **Service**: Stable virtual IP for a set of pods, load balancing, service discovery via DNS (ClusterIP, NodePort, LoadBalancer types).
- **Ingress**: HTTP/HTTPS routing to services, TLS termination, virtual hosting. Controllers: Nginx, Traefik, Istio Gateway.

**Storage Abstraction**:
- **PersistentVolume (PV)**: Cluster resource representing storage (EBS volume, NFS share).
- **PersistentVolumeClaim (PVC)**: Request for storage by a pod. Dynamic provisioning creates PVs on-demand.
- **StorageClass**: Defines storage types (SSD, HDD), provisioners (AWS EBS, GCP Persistent Disk), reclaim policies.

**Security Features**:
- **RBAC**: Define roles (permissions on resources), bind roles to users/service accounts. Principle of least privilege.
- **Pod Security Standards**: Restricted, Baseline, Privileged profiles. Enforce via admission controllers (Pod Security Admission, OPA Gatekeeper).
- **Network Policies**: Firewall rules at pod level. Default deny, explicitly allow traffic between pods/namespaces.
- **Secrets & ConfigMaps**: Secrets for sensitive data (encoded, not encrypted by default—use encryption at rest), ConfigMaps for configuration.

### Deployment Strategies

**Blue-Green Deployment**: Run two identical environments. Blue is production, green is staging. Deploy new version to green, test, then switch traffic. Instant rollback by switching back to blue. Doubles infrastructure cost, requires traffic switching mechanism (DNS, load balancer).

**Canary Deployment**: Deploy new version to small subset of instances (5-10%), monitor metrics, gradually increase traffic (25%, 50%, 100%). Rollback if error rates spike. Kubernetes supports via weighted routing (Flagger, Argo Rollouts, Istio traffic splitting).

**Rolling Update**: Gradually replace old instances with new. Specify max unavailable (number of pods down during update) and max surge (extra pods during update). Kubernetes Deployment default. Zero downtime if health checks are correct.

**Feature Flags**: Decouple deployment from release. Deploy new code with feature disabled, enable for specific users/regions via runtime flag. Allows testing in production, gradual rollout, instant rollback without redeployment. Tools: LaunchDarkly, Unleash, split.io.

### Infrastructure as Code (IaC)

**Declarative vs Imperative**: Declarative (Terraform, Kubernetes YAML) specifies desired state, system converges to it. Imperative (scripts, Ansible) specifies steps to execute. Declarative is idempotent, easier to reason about.

**Terraform**: Provision cloud resources, manage state in backend (S3, GCS), plan before apply (preview changes), modules for reusability. Challenges: state file management, concurrent modification, drift between actual and desired state.

**GitOps**: Desired state lives in Git. Automation watches Git, syncs cluster state to match. Tools: ArgoCD, Flux. Benefits: audit trail (Git history), rollback (Git revert), disaster recovery (recreate cluster from Git).

### Multi-Cloud and Hybrid Architectures

**Multi-Cloud Rationale**: Avoid vendor lock-in, leverage best-of-breed services (AWS for compute, GCP for ML, Azure for enterprise integration), geographic coverage, regulatory compliance (data residency).

**Challenges**: Operational complexity (multiple CLIs, IAM systems, monitoring tools), data transfer costs (egress fees between clouds), network latency (inter-cloud communication), consistency (different APIs for identical services).

**Abstraction Layers**: Kubernetes as common control plane, service mesh for cross-cloud networking, Terraform for infrastructure, unified observability (Datadog, New Relic). Accept that some services (managed databases, ML platforms) won't abstract cleanly.

**Hybrid Cloud**: On-prem data centers + cloud. Reasons: data gravity (large datasets expensive to move), regulatory (some data can't leave country), legacy systems (can't migrate immediately). Challenges: network connectivity (VPN, Direct Connect), latency, security boundaries.

---

## 11. Testing Strategies Across Boundaries

### Test Pyramid

**Unit Tests (Bottom)**: Test individual functions/methods in isolation. Mock external dependencies. Fast (milliseconds), run on every commit, high code coverage (70-90%). Focus on business logic, edge cases, error handling.

**Integration Tests (Middle)**: Test service with real dependencies (databases, message queues), but isolated from other services. Slower (seconds), run on every commit or PR. Validate data access patterns, transaction boundaries, external API integrations (with test doubles for external services).

**End-to-End Tests (Top)**: Test entire system across multiple services. Slowest (minutes), brittle (many failure points), expensive to maintain. Run on every deploy or scheduled (nightly). Focus on critical user journeys, not exhaustive coverage.

**Ratio**: 70% unit, 20% integration, 10% end-to-end. Avoid inverted pyramid (heavy E2E, sparse unit tests)—it's slow and fragile.

### Contract Testing

**Problem**: Integration tests between services require coordinating deployments, managing test environments, slow feedback loops. Mocking doesn't catch breaking changes.

**Consumer-Driven Contracts**: Consumer defines expectations (contract) for provider's API. Provider verifies it meets contracts from all consumers. Tools: Pact, Spring Cloud Contract. Workflow: consumer generates contract file, shares with provider, provider runs tests against contract, both can deploy independently if tests pass.

**Benefits**: Fast feedback (no need for full integration environments), decoupled deployments, prevents breaking changes from reaching production.

**Schema Validation**: For gRPC, validate protobuf schema changes for backward/forward compatibility (breaking: removing fields, changing field numbers; safe: adding optional fields). For REST, use OpenAPI/Swagger, run compatibility checks in CI.

### Chaos Engineering

**Principles**: Hypothesis (system should remain healthy during failure), inject failures (kill pods, add latency, partition networks), measure impact (error rates, latency, throughput), automate (continuous chaos in production).

**Failure Injection**:
- **Infrastructure**: Kill random instances (Chaos Monkey), terminate availability zones (simulate AZ failure).
- **Network**: Add latency, drop packets, partition services, limit bandwidth.
- **Application**: Inject exceptions, simulate slow dependencies, exhaust resource pools.

**Observability Requirements**: Must have metrics/alerts to detect impact. If you can't measure degradation, you can't validate resilience.

**Progressive Rollout**: Start in staging, low-traffic production environments, gradually increase blast radius. Run during business hours initially (so team can respond), eventually 24/7 automated.

### Performance Testing

**Load Testing**: Simulate expected traffic, validate system meets SLAs. Tools: k6, Locust, Gatling. Ramp traffic gradually, sustain peak for duration (30-60 minutes), measure P50/P95/P99 latency, error rates, resource utilization.

**Stress Testing**: Exceed expected load until system breaks. Find breaking point, understand failure modes, validate graceful degradation and recovery.

**Soak Testing**: Sustained load for extended period (hours, days). Detect memory leaks, file descriptor exhaustion, connection pool saturation, disk space growth.

**Spike Testing**: Sudden traffic surge (10x baseline). Validate autoscaling responsiveness, connection pool limits, queue depths, circuit breaker effectiveness.

### Test Data Management

**Anonymization**: Production data contains PII. Anonymize before using in test environments (hash emails, randomize names, mask credit cards). Preserve referential integrity, maintain statistical properties for realistic testing.

**Synthetic Data Generation**: Create realistic test data programmatically. Libraries: Faker, Mimesis. Useful for load testing, privacy compliance, edge case scenarios.

**Test Environments**: Dedicated environments per team (reduces conflicts), ephemeral environments per PR (isolated testing), production-like staging (validate deployments), canary environments (subset of production traffic).

---

## 12. Organizational & Cultural Considerations

### Conway's Law

**Statement**: "Organizations which design systems are constrained to produce designs which are copies of the communication structures of these organizations."

**Implication**: If you have three teams, you'll build three major components. Microservices architecture requires organizing teams around business capabilities, not technical layers (no separate "frontend team," "backend team," "database team"). Each team owns services end-to-end.

**Reverse Conway**: Design team structure to match desired architecture. Want modular, decoupled services? Create small, autonomous teams with clear ownership boundaries.

### Team Ownership & Autonomy

**You Build It, You Run It**: Teams own their services in production. On-call for incidents, responsible for SLAs, make architecture decisions, choose technology stack. Incentivizes building reliable, operable systems.

**Cognitive Load Management**: A team shouldn't own more services than they can hold in working memory. Limit to 1-3 services, or consolidate related functionality. Excessive ownership leads to burnout, context switching, degraded quality.

**Inner Source**: Teams can contribute to other teams' services, but require approval from owners. Prevents silos while maintaining clear accountability.

### Communication Overhead

**Coordination Cost**: N teams require N(N-1)/2 communication channels. 5 teams = 10 channels, 10 teams = 45 channels. Microservices reduce this via API contracts—teams agree on interfaces, work independently.

**API Governance**: Without standards, teams invent incompatible solutions (one uses REST, another gRPC, another GraphQL). Establish lightweight governance: style guides, schema registries, automated compatibility checks, design reviews for new APIs.

**Documentation Culture**: Code is the source of truth, but APIs need human-readable documentation. OpenAPI/Swagger, gRPC protobufs, AsyncAPI for events. Automate documentation generation, require examples, document error conditions.

### Skill Distribution

**Full-Stack Ownership**: Teams need diverse skills—backend development, infrastructure (Kubernetes, Terraform), observability (Prometheus, Grafana), security (TLS, secrets management), databases (SQL, NoSQL). Either hire generalists or build cross-functional teams.

**Platform Teams**: Build shared infrastructure (CI/CD, service mesh, monitoring) that product teams consume. Platform team creates "golden path"—opinionated, well-tested way to deploy services. Product teams get autonomy within platform guardrails.

**Knowledge Sharing**: Cross-team guilds (security guild, observability guild), internal tech talks, runbooks for common operations, post-mortem reviews after incidents. Prevents knowledge silos.

### Decision-Making Authority

**Centralized vs Decentralized**: Centralized (architecture review board approves all designs) provides consistency but slows innovation. Decentralized (teams decide independently) enables speed but risks fragmentation. Hybrid: centralized for cross-cutting concerns (security, observability), decentralized for service internals.

**Architecture Decision Records (ADRs)**: Document significant decisions, context, alternatives considered, trade-offs. Store in version control alongside code. Makes decisions auditable, helps new team members understand rationale.

---

## 13. Anti-Patterns & Failure Modes

### Distributed Monolith

**Symptoms**: Services must deploy together, share database schema, make synchronous calls for every operation, tightly coupled via shared libraries, coordinated releases across teams.

**Root Cause**: Decomposed for wrong reasons (team structure, not business capabilities), insufficient attention to service boundaries, shared database used as integration mechanism.

**Remediation**: Re-evaluate service boundaries using domain-driven design, introduce message queues to decouple services, migrate to database-per-service, version APIs and support backward compatibility.

### Chatty Services

**Symptom**: Single user request triggers dozens of inter-service calls. Network becomes bottleneck, latency accumulates (each hop adds 10-50ms), failure probability multiplies.

**Root Cause**: Over-granular service decomposition, lack of data locality, synchronous communication where async would suffice.

**Remediation**: Consolidate related services, introduce caching layers, use async messaging for non-critical paths, implement BFF pattern to aggregate data at the edge, denormalize data where appropriate.

### Data Hotspots

**Symptom**: Single database instance becomes bottleneck, all services wait on it, can't scale horizontally because every service needs access.

**Root Cause**: Shared database pattern, lack of data partitioning, monolithic schema.

**Remediation**: Separate databases per service, introduce caching (Redis), partition data by tenant/region, use CQRS to separate read and write models.

### Cascading Failures

**Symptom**: One service's failure triggers chain reaction across system. Example: database slowdown → connection pool exhaustion → service crashes → dependent services fail.

**Root Cause**: Lack of resilience patterns (timeouts, circuit breakers, bulkheads), unbounded queues, no backpressure mechanisms.

**Remediation**: Implement timeouts on all network calls, deploy circuit breakers, isolate resources with bulkheads, implement graceful degradation, monitor dependency health and fail fast when downstream is unhealthy.

### Premature Microservices

**Symptom**: Young startup with 3 developers and 20 microservices. Excessive operational overhead, slow feature development, context switching between services, infrastructure costs exceed productivity gains.

**Root Cause**: Cargo-culting (copying Netflix/Amazon without their scale), resume-driven development, misunderstanding trade-offs.

**Remediation**: Start with modular monolith (clear internal boundaries, can extract services later), deploy services when pain points emerge (independent scaling needs, team autonomy, deployment frequency), ensure team has operational maturity (automation, monitoring) before adopting microservices.

### Versioning Nightmares

**Symptom**: Service V2 breaks all consumers, coordinated "flag day" deployments required, backward compatibility impossible.

**Root Cause**: No versioning strategy, breaking changes deployed without migration path, insufficient testing of version compatibility.

**Remediation**: Semantic versioning for APIs, support multiple versions concurrently (V1 and V2 coexist), deprecation policy (announce 6 months ahead, provide migration guide), automated compatibility testing.

### Observability Gaps

**Symptom**: Incident occurs, no one knows which service failed or why. Logs are scattered, no correlation IDs, metrics don't match reality, tracing is partial.

**Root Cause**: Ad-hoc observability, each team implements differently, no standardization, insufficient investment in monitoring infrastructure.

**Remediation**: Mandate structured logging with correlation IDs, deploy distributed tracing across all services, standardize metrics (use Prometheus conventions), centralize collection (ELK, Grafana stack), SLO-based alerting.

---

## 14. Migration Strategies from Monoliths

### Strangler Fig Pattern

**Concept**: Gradually replace monolith functionality by building new microservices around it. Metaphor: strangler fig tree grows around host tree, eventually replacing it.

**Process**:
1. Identify a bounded context suitable for extraction (recommendation engine, user authentication, billing).
2. Build new microservice implementing that functionality.
3. Route traffic through proxy/API gateway—send subset of requests to new service, rest to monolith.
4. Gradually increase traffic to new service, monitor errors/latency.
5. Once fully migrated, delete monolith code for that context.
6. Repeat for next context.

**Benefits**: Incremental risk, always have working system, can abort if issues arise, teams learn microservices patterns gradually.

**Challenges**: Running two systems simultaneously (operational overhead), data synchronization between monolith and service, maintaining consistency during migration.

### Anti-Corruption Layer (ACL)

**Purpose**: Protect new services from monolith's data model and legacy constraints. ACL translates between monolith's API/database schema and clean service API.

**Implementation**: Service doesn't directly query monolith database. ACL module makes API calls or database queries, maps results to service's domain model. This isolates service from monolith changes.

**Trade-off**: Additional layer adds latency and complexity, but preserves service autonomy and enables independent evolution.

### Data Migration Strategies

**Dual-Write Phase**: Application writes to both monolith database and new service database. Ensures data consistency during migration. Challenges: transaction boundaries (both writes must succeed or fail together), latency (two write operations), potential for divergence if writes fail partially.

**Change Data Capture (CDC)**: Stream database changes from monolith to new service via CDC tool (Debezium). Service consumes stream, updates its database. Avoids dual-write code changes, eventual consistency acceptable.

**Batch Migration**: Copy historical data from monolith to service database, then switch to real-time replication. Useful for large datasets where real-time sync is impractical initially.

**Backward Compatibility**: New service must support monolith's API format during migration. Add adapter/facade layer that exposes old API while internally using new model. Remove after monolith is retired.

### Rollback Planning

**Feature Flags**: Control traffic routing to new service via runtime flag. Instant rollback by flipping flag to route all traffic back to monolith.

**Parallel Run**: Both monolith and service process requests simultaneously, compare results. If discrepancies detected, monolith's result is returned (it's the source of truth), but team investigates why service differs.

**Monitoring & Alerting**: During migration, monitor new service's error rates, latency, resource usage. Set conservative alerts—any degradation triggers investigation.

---

## 15. Production Operations & Incident Response

### Site Reliability Engineering (SRE) Principles

**Error Budgets**: SLO defines acceptable failure rate (e.g., 99.9% uptime = 43 minutes downtime/month). Error budget is the allowed failure. If budget is consumed, freeze feature work, focus on reliability. If budget remains, invest in features.

**Toil Reduction**: Toil is manual, repetitive, automatable work without enduring value. Example: manually restarting services, running deployment scripts. Goal: <50% of SRE time on toil, >50% on engineering (automation, platform improvements).

**On-Call Rotation**: Distribute on-call load across team. Typical rotation: 1 week primary, 1 week secondary (backup), 4-6 weeks off. Limits: no more than 2 incidents per shift, no more than 25% of time on-call over a quarter.

### Incident Management

**Incident Severity Levels**:
- **SEV-1**: Critical impact—site down, data loss, security breach. Page immediately, assemble war room, executive notification.
- **SEV-2**: Major impact—degraded performance, subset of users affected. Page on-call, incident commander assigned.
- **SEV-3**: Minor impact—non-critical feature broken, workaround available. Ticket created, handled during business hours.

**Roles During Incident**:
- **Incident Commander**: Coordinates response, makes decisions, communicates with stakeholders, delegates tasks. Doesn't debug—focuses on orchestration.
- **Technical Lead**: Investigates root cause, proposes mitigation, executes fixes.
- **Communications Lead**: Updates status page, sends customer emails, coordinates PR responses.
- **Scribe**: Documents timeline, actions taken, decisions made. Critical for post-mortem.

**Mitigation vs Resolution**: Mitigation restores service quickly (rollback deployment, restart service, redirect traffic). Resolution addresses root cause (fix bug, scale infrastructure, improve monitoring). During incident, prioritize mitigation—users need service restored. Investigation continues after.

**Blameless Post-Mortems**: Document what happened, why, how it was detected, how it was mitigated, what's being done to prevent recurrence. Focus on systems/processes, not individuals. Goal: learning, not punishment. Template: timeline, root cause analysis, action items (with owners and deadlines), what went well.

### Disaster Recovery

**Backup Strategy**: Regular backups of databases (daily full, hourly incremental), test restoration quarterly, encrypt backups, store in separate region from production.

**Recovery Time Objective (RTO)**: Maximum acceptable downtime. Example: database failure, RTO = 1 hour. Must restore from backup and resume operations within 1 hour.

**Recovery Point Objective (RPO)**: Maximum acceptable data loss. Example: RPO = 15 minutes. Can lose up to 15 minutes of transactions. Determines backup frequency.

**Multi-Region Architecture**: Active-active (both regions serve traffic, complex data replication), active-passive (secondary region on standby, simpler but wastes capacity), read replicas (writes to primary, reads from both).

**Failover Testing**: Quarterly chaos drills—simulate entire region failure, execute failover procedures, measure RTO/RPO, document gaps, update runbooks.

### Capacity Planning

**Traffic Forecasting**: Historical trends (seasonality, weekly patterns), planned launches (marketing campaigns, new features), growth projections (user base increasing 10% per quarter).

**Headroom**: Never run at 100% capacity. Maintain 30-50% headroom to handle spikes, failures (when instance fails, remaining instances absorb load), growth.

**Autoscaling Strategies**:
- **Reactive**: Scale based on current metrics (CPU > 70%, add instances). Lags demand spikes, may not scale fast enough.
- **Predictive**: Scale based on forecasts (traffic doubles at 9am, pre-scale at 8:45am). Requires accurate models, avoids lag.
- **Schedule-Based**: Known patterns (retail traffic spikes on Cyber Monday). Pre-scale for event.

**Cost Optimization**: Right-size instances (don't over-provision), use spot instances for batch jobs, reserved instances for baseline load, shutdown non-production environments off-hours, archive old data to cheaper storage tiers.

---

## Next 3 Steps for Mastery

1. **Build a Reference Implementation**: Design and implement a multi-service system (e.g., e-commerce platform with catalog, cart, payment, fulfillment services). Focus on service boundaries, inter-service communication (REST + async messaging), distributed tracing, security (mTLS), and resilience patterns. Deploy on Kubernetes, instrument with Prometheus/Grafana, inject chaos, document architectural decisions.

2. **Study Real-World Architectures**: Analyze open-source microservices examples—CNCF landscape projects (Jaeger, Linkerd, Flagger), tech company engineering blogs (Uber, Netflix, Spotify architecture posts), distributed systems papers (Google's Borg, Amazon's Dynamo, Facebook's Cassandra). Understand trade-offs, failure modes, operational lessons.

3. **Operational Deep-Dive**: Run services in production-like environments. Implement on-call rotation, respond to simulated incidents, write runbooks, conduct post-mortems. Operate message brokers (Kafka cluster), service mesh (Istio/Linkerd), secrets management (Vault). Measure SLOs, manage error budgets, tune autoscaling, optimize costs. Theory crystallizes through operational pain.

---

## References for Deeper Study

- **Books**: "Building Microservices" (Sam Newman), "Designing Data-Intensive Applications" (Martin Kleppmann), "Site Reliability Engineering" (Google), "Domain-Driven Design" (Eric Evans), "Release It!" (Michael Nygard)
- **Distributed Systems Papers**: "Brewer's CAP Theorem," "Paxos Made Simple," "Raft Consensus," "Dynamo: Amazon's Highly Available Key-Value Store," "Spanner: Google's Globally-Distributed Database"
- **Security Resources**: OWASP API Security Top 10, NIST Cybersecurity Framework, CIS Benchmarks for container/Kubernetes security, SPIFFE/SPIRE documentation
- **CNCF Projects**: Study landscape.cncf.io—each graduated project (Kubernetes, Prometheus, Envoy) has extensive documentation, design docs, and architectural rationale
- **Industry Patterns**: AWS Well-Architected Framework, Google Cloud Architecture Center, Azure Architecture Center—cloud vendors document microservices patterns extensively

# Microservices Architecture: Comprehensive Deep-Dive

This guide covers microservices from first principles through production deployment. We'll examine service decomposition, inter-service communication patterns, data consistency strategies, observability, security boundaries, failure modes, and operational considerations. The focus is on security-first design, distributed systems theory, and production-grade trade-offs rather than superficial patterns.

**Key takeaways:** Microservices trade monolithic simplicity for independent scaling/deployment at the cost of distributed systems complexity (network partitions, eventual consistency, observability overhead). Success requires strong isolation boundaries, explicit service contracts, sophisticated observability, and defense-in-depth security. Most failures stem from inadequate service boundaries, missing circuit breakers, or insufficient distributed tracing.

---

## 1. Foundational Concepts & Theory

### 1.1 Core Principles

**Microservices** decompose applications into small, independently deployable services that:
- Own their data (database-per-service pattern)
- Communicate via well-defined APIs (gRPC, REST, async messaging)
- Deploy/scale/fail independently
- Align with business capabilities (bounded contexts from DDD)

**Contrast with Monolith:**
```
Monolith                    Microservices
├─ Single deployment unit   ├─ Multiple deployment units
├─ Shared database          ├─ Database per service
├─ In-process calls         ├─ Network calls (RPC/HTTP)
├─ ACID transactions        ├─ Eventual consistency + Sagas
└─ Simple ops, hard scale   └─ Complex ops, easy scale
```

**CAP Theorem Implications:**
- You cannot have Consistency + Availability + Partition tolerance simultaneously
- In microservices, network partitions are inevitable → choose CP or AP per service
- Payment service: CP (consistency over availability)
- Product catalog: AP (availability over consistency)

### 1.2 When NOT to Use Microservices

**Anti-patterns:**
- Small teams (<10 engineers) → operational overhead exceeds benefits
- Unclear domain boundaries → premature decomposition causes distributed monolith
- Low traffic (<1000 RPS) → complexity not justified
- Greenfield projects → start monolith, extract services when boundaries clear

**Migration trigger points:**
- Team size >15-20 engineers (Conway's Law)
- Independent scaling needs (CPU-bound vs I/O-bound services)
- Different tech stack requirements (ML models vs CRUD)
- Regulatory boundaries (PCI-DSS isolated services)

---

## 2. Service Decomposition Strategies

### 2.1 Domain-Driven Design (DDD)

**Bounded Contexts** define service boundaries:

```
E-commerce Domain:
┌─────────────────────────────────────────────────────┐
│                                                     │
│  ┌──────────────┐    ┌──────────────┐             │
│  │   Identity   │    │   Catalog    │             │
│  │  (Users,     │    │ (Products,   │             │
│  │   Auth)      │    │  Inventory)  │             │
│  └──────────────┘    └──────────────┘             │
│                                                     │
│  ┌──────────────┐    ┌──────────────┐             │
│  │   Orders     │    │   Payment    │             │
│  │ (Cart,       │    │ (Billing,    │             │
│  │  Checkout)   │    │  Ledger)     │             │
│  └──────────────┘    └──────────────┘             │
│         │                    │                     │
│         └────────┬───────────┘                     │
│                  ▼                                 │
│          ┌──────────────┐                          │
│          │  Shipping    │                          │
│          │ (Fulfillment)│                          │
│          └──────────────┘                          │
└─────────────────────────────────────────────────────┘
```

**Service sizing heuristics:**
- Single business capability (can explain in <2 sentences)
- Team ownership: 2-pizza team (6-10 engineers)
- Data model: 5-15 tables max per service
- Lines of code: <50k LoC (guideline, not rule)

### 2.2 Strangler Fig Pattern (Monolith Migration)

```
Phase 1: Proxy Layer          Phase 2: Extract Service       Phase 3: Complete
┌─────────────┐               ┌─────────────┐                ┌─────────────┐
│   Monolith  │               │  Monolith   │                │  Service A  │
│             │               │   (Less)    │                └─────────────┘
│  ┌────┐     │               │  ┌────┐     │                        │
│  │ A  │     │               │  │ B  │     │                        ▼
│  ├────┤     │               │  ├────┤     │                ┌─────────────┐
│  │ B  │     │  ────────────▶│  │ C  │     │  ────────────▶ │  Service B  │
│  ├────┤     │               │  └────┘     │                └─────────────┘
│  │ C  │     │               └─────────────┘                        │
│  └────┘     │                      │                               ▼
└─────────────┘                      ▼                        ┌─────────────┐
       │                     ┌─────────────┐                 │  Service C  │
       ▼                     │  Service A  │                 └─────────────┘
   [Proxy]                   └─────────────┘
```

**Reference:** Shopify's modular monolith → microservices (https://github.com/Shopify/example-ruby-app, look at `app/services/` for service boundaries)

---

## 3. Inter-Service Communication

### 3.1 Synchronous: gRPC vs REST

**gRPC Advantages:**
- Binary protocol (Protobuf) → 5-10x smaller payloads than JSON
- HTTP/2 multiplexing → single TCP connection for multiple streams
- Strongly typed contracts → compile-time validation
- Bi-directional streaming

**gRPC Blueprint:**

```protobuf
// api/order/v1/order.proto
syntax = "proto3";
package order.v1;

import "google/protobuf/timestamp.proto";

service OrderService {
  rpc CreateOrder(CreateOrderRequest) returns (Order);
  rpc GetOrder(GetOrderRequest) returns (Order);
  rpc ListOrders(ListOrdersRequest) returns (stream Order); // Server streaming
}

message Order {
  string id = 1;
  string user_id = 2;
  repeated OrderItem items = 3;
  OrderStatus status = 4;
  google.protobuf.Timestamp created_at = 5;
}

message CreateOrderRequest {
  string user_id = 1;
  repeated OrderItem items = 2;
}

enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0;
  ORDER_STATUS_PENDING = 1;
  ORDER_STATUS_CONFIRMED = 2;
  ORDER_STATUS_SHIPPED = 3;
}
```

**Code reference:** https://github.com/grpc/grpc-go/tree/master/examples/helloworld (client/server stubs)

**REST when:**
- Public APIs (browser compatibility)
- Human-readable debugging (JSON)
- Simple CRUD with existing tooling

### 3.2 Asynchronous: Event-Driven Architecture

**Message Broker Comparison:**

| Broker | Ordering | Durability | Throughput | Use Case |
|--------|----------|------------|------------|----------|
| Kafka | Per-partition | Disk + replication | 1M+ msgs/sec | Event sourcing, logs |
| NATS | No | Optional JetStream | 10M+ msgs/sec | Low-latency RPC |
| RabbitMQ | Per-queue | Disk | 100k msgs/sec | Task queues |
| Pulsar | Per-partition | Tiered storage | 1M+ msgs/sec | Multi-tenancy |

**Event Schema (CloudEvents standard):**

```go
// internal/events/order_event.go
package events

import "time"

type OrderCreated struct {
    CloudEventsVersion string    `json:"specversion"`
    Type               string    `json:"type"` // "com.company.order.created"
    Source             string    `json:"source"` // "/order-service"
    ID                 string    `json:"id"`
    Time               time.Time `json:"time"`
    DataContentType    string    `json:"datacontenttype"`
    Data               OrderData `json:"data"`
}

type OrderData struct {
    OrderID  string  `json:"order_id"`
    UserID   string  `json:"user_id"`
    Total    float64 `json:"total"`
    Items    []Item  `json:"items"`
}
```

**Kafka Producer (Go):**

```go
// Reference: https://github.com/segmentio/kafka-go
// cmd/producer/main.go
package main

import (
    "context"
    "github.com/segmentio/kafka-go"
)

func publishOrderCreated(ctx context.Context, orderID string) error {
    w := kafka.NewWriter(kafka.WriterConfig{
        Brokers:  []string{"kafka:9092"},
        Topic:    "orders.created",
        Balancer: &kafka.Hash{}, // Key-based partitioning
    })
    defer w.Close()

    return w.WriteMessages(ctx, kafka.Message{
        Key:   []byte(orderID), // Orders from same user → same partition
        Value: orderEventJSON,
        Headers: []kafka.Header{
            {Key: "trace-id", Value: []byte(traceID)},
        },
    })
}
```

---

## 4. Data Management Patterns

### 4.1 Database-Per-Service

**Problem:** Shared database couples services, breaks independent deployment.

**Solution:** Each service owns its data schema + access.

```
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ Order Service│      │ User Service │      │Payment Service│
└──────┬───────┘      └──────┬───────┘      └──────┬────────┘
       │                     │                     │
       ▼                     ▼                     ▼
  ┌─────────┐           ┌─────────┐          ┌─────────┐
  │ Orders  │           │  Users  │          │Payments │
  │   DB    │           │   DB    │          │   DB    │
  └─────────┘           └─────────┘          └─────────┘
```

**Joining data across services:**
1. **API Composition:** Order service calls User service (adds latency)
2. **CQRS + Read Replicas:** Materialized views in Order DB (eventual consistency)
3. **Event Sourcing:** Rebuild state from event log

### 4.2 Saga Pattern (Distributed Transactions)

**Problem:** No ACID across services. How to handle order → payment → shipping sequence?

**Choreography (Event-Driven):**

```
Order Service        Payment Service      Shipping Service
     │                     │                     │
     ├─► OrderCreated ────►│                     │
     │                     ├─► PaymentProcessed ─►│
     │                     │                     ├─► ShipmentCreated
     │                     │                     │
     │◄── PaymentFailed ───┤                     │
     ├─► OrderCancelled    │                     │
```

**Orchestration (Central Coordinator):**

```go
// internal/saga/order_saga.go
type OrderSaga struct {
    orderID   string
    state     SagaState
    compensations []CompensationFunc
}

func (s *OrderSaga) Execute(ctx context.Context) error {
    // Step 1: Create order
    if err := s.createOrder(ctx); err != nil {
        return err
    }
    s.compensations = append(s.compensations, s.cancelOrder)

    // Step 2: Process payment
    if err := s.processPayment(ctx); err != nil {
        s.rollback(ctx)
        return err
    }
    s.compensations = append(s.compensations, s.refundPayment)

    // Step 3: Reserve inventory
    if err := s.reserveInventory(ctx); err != nil {
        s.rollback(ctx)
        return err
    }

    return nil
}

func (s *OrderSaga) rollback(ctx context.Context) {
    for i := len(s.compensations) - 1; i >= 0; i-- {
        s.compensations[i](ctx) // Execute in reverse
    }
}
```

**Reference:** https://github.com/uber-go/cadence (workflow orchestration), temporal.io

---

## 5. Service Mesh & Traffic Management

### 5.1 Sidecar Proxy Architecture

**Envoy as data plane:**

```
Pod: Order Service
┌──────────────────────────────────┐
│  ┌─────────────────┐              │
│  │  Order App      │              │
│  │  :8080          │              │
│  └────────┬────────┘              │
│           │ localhost             │
│  ┌────────▼────────┐              │
│  │  Envoy Proxy    │◄─────────────┼─── Ingress (TLS, AuthN)
│  │  :15001 (in)    │              │
│  │  :15000 (out)   │──────────────┼──► Payment Service
│  └─────────────────┘              │        (mTLS, retry, CB)
└──────────────────────────────────┘
```

**Istio Configuration (mTLS enforcement):**

```yaml
# config/istio/peer-authentication.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Reject non-mTLS traffic

---
# config/istio/authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: order-service-authz
spec:
  selector:
    matchLabels:
      app: order-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/api-gateway"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/v1/orders"]
```

**Circuit Breaker (Envoy):**

```yaml
# config/istio/destination-rule.yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: payment-service
spec:
  host: payment-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

**Alternative:** Linkerd (Rust-based, lighter than Istio), Cilium (eBPF service mesh)

---

## 6. Observability: Metrics, Logs, Traces

### 6.1 The Three Pillars

**Metrics (Prometheus + Grafana):**

```go
// internal/metrics/metrics.go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    OrdersCreated = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "orders_created_total",
            Help: "Total orders created",
        },
        []string{"status"}, // Labels: success, failed
    )

    OrderProcessingDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "order_processing_duration_seconds",
            Help:    "Order processing latency",
            Buckets: prometheus.ExponentialBuckets(0.01, 2, 10), // 10ms to 5s
        },
        []string{"operation"},
    )
)
```

**Distributed Tracing (OpenTelemetry):**

```go
// cmd/order-service/main.go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/sdk/trace"
)

func initTracer() (*trace.TracerProvider, error) {
    exporter, err := jaeger.New(jaeger.WithCollectorEndpoint(
        jaeger.WithEndpoint("http://jaeger:14268/api/traces"),
    ))
    if err != nil {
        return nil, err
    }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithSampler(trace.TraceIDRatioBased(0.1)), // Sample 10%
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}

// In handler:
tracer := otel.Tracer("order-service")
ctx, span := tracer.Start(ctx, "CreateOrder")
defer span.End()

// Propagate context to downstream calls
paymentClient.ProcessPayment(ctx, req) // Context carries trace ID
```

**Reference:** https://github.com/open-telemetry/opentelemetry-go/tree/main/example (full setup)

**Structured Logging (zerolog):**

```go
import "github.com/rs/zerolog/log"

log.Info().
    Str("trace_id", traceID).
    Str("order_id", orderID).
    Dur("duration", elapsed).
    Msg("Order created successfully")
```

### 6.2 Observability Stack

```
Application
     │
     ├─► Metrics  ──► Prometheus ──► Grafana
     ├─► Logs    ──► Loki/ES    ──► Grafana
     └─► Traces  ──► Tempo/Jaeger ──► Grafana
```

**Deployment:** https://github.com/grafana/intro-to-mltp (Mimir, Loki, Tempo, Pyroscope stack)

---

## 7. Security Architecture

### 7.1 Zero Trust Principles

```
Defense Layers:
┌─────────────────────────────────────────────────┐
│ L7: API Gateway (AuthN, rate limit, WAF)        │
├─────────────────────────────────────────────────┤
│ L4: Service Mesh (mTLS, AuthZ policies)         │
├─────────────────────────────────────────────────┤
│ L3: Network Policies (CNI: Cilium, Calico)      │
├─────────────────────────────────────────────────┤
│ L2: Pod Security Standards (restricted)         │
├─────────────────────────────────────────────────┤
│ L1: Runtime Security (Falco, Tetragon)          │
└─────────────────────────────────────────────────┘
```

**Network Policy (Deny all, allow specific):**

```yaml
# config/k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: order-service-netpol
spec:
  podSelector:
    matchLabels:
      app: order-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: payment-service
    ports:
    - protocol: TCP
      port: 8080
  - to:  # DNS
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

### 7.2 Secrets Management

**Vault Integration (Go):**

```go
// internal/vault/client.go
import "github.com/hashicorp/vault/api"

func GetDatabaseCredentials(ctx context.Context) (*DBCreds, error) {
    client, err := api.NewClient(&api.Config{
        Address: "https://vault.local:8200",
    })
    if err != nil {
        return nil, err
    }

    // Kubernetes auth
    jwt, _ := os.ReadFile("/var/run/secrets/kubernetes.io/serviceaccount/token")
    resp, err := client.Logical().Write("auth/kubernetes/login", map[string]interface{}{
        "role": "order-service",
        "jwt":  string(jwt),
    })

    client.SetToken(resp.Auth.ClientToken)

    // Dynamic secrets (auto-rotated)
    secret, err := client.Logical().Read("database/creds/order-db-role")
    return &DBCreds{
        Username: secret.Data["username"].(string),
        Password: secret.Data["password"].(string),
    }, nil
}
```

**Reference:** https://github.com/hashicorp/vault-k8s (Vault Agent injector)

---

## 8. Deployment Strategies

### 8.1 Blue-Green Deployment

```yaml
# config/k8s/service.yaml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
    version: blue  # Switch to 'green' for cutover
  ports:
  - port: 80
    targetPort: 8080
---
# Green deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service-green
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
      version: green
  template:
    metadata:
      labels:
        app: order-service
        version: green
    spec:
      containers:
      - name: order-service
        image: order-service:v2.0.0
```

**Rollback:** Update Service selector to `version: blue`.

### 8.2 Canary with Flagger (Istio)

```yaml
# config/flagger/canary.yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: order-service
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  service:
    port: 8080
  analysis:
    interval: 1m
    threshold: 5  # Max failed checks before rollback
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
    - name: request-duration
      thresholdRange:
        max: 500  # milliseconds
      interval: 1m
    webhooks:
    - name: load-test
      url: http://flagger-loadtester/
      metadata:
        cmd: "hey -z 1m -c 10 -q 5 http://order-service-canary:8080/health"
```

**Progressive traffic shift:** 0% → 10% → 20% → ... → 50% (auto-rollback on metric breach).

---

## 9. Failure Modes & Mitigations

### 9.1 Cascading Failures

**Scenario:** Payment service slow → Order service thread pool exhausted → API gateway timeouts → entire system down.

**Mitigation: Bulkhead Pattern (Go):**

```go
// internal/bulkhead/pool.go
type BulkheadPool struct {
    semaphore chan struct{}
    timeout   time.Duration
}

func NewBulkhead(maxConcurrent int, timeout time.Duration) *BulkheadPool {
    return &BulkheadPool{
        semaphore: make(chan struct{}, maxConcurrent),
        timeout:   timeout,
    }
}

func (b *BulkheadPool) Execute(ctx context.Context, fn func() error) error {
    select {
    case b.semaphore <- struct{}{}: // Acquire
        defer func() { <-b.semaphore }() // Release
        
        resultCh := make(chan error, 1)
        go func() { resultCh <- fn() }()

        select {
        case err := <-resultCh:
            return err
        case <-time.After(b.timeout):
            return ErrTimeout
        }
    case <-ctx.Done():
        return ctx.Err()
    default:
        return ErrBulkheadFull
    }
}
```

### 9.2 Thundering Herd

**Problem:** Cache expires → 10k requests hit database simultaneously.

**Solution: Request Coalescing (singleflight):**

```go
import "golang.org/x/sync/singleflight"

var g singleflight.Group

func GetUser(userID string) (*User, error) {
    v, err, _ := g.Do(userID, func() (interface{}, error) {
        // Only one goroutine executes this
        return db.GetUser(userID)
    })
    return v.(*User), err
}
```

---

## 10. Testing Strategy

### 10.1 Contract Testing (Pact)

**Consumer (Order Service):**

```go
// test/pact/order_consumer_test.go
pact := dsl.Pact{
    Consumer: "OrderService",
    Provider: "PaymentService",
}

pact.AddInteraction().
    Given("payment method exists").
    UponReceiving("a payment request").
    WithRequest(dsl.Request{
        Method: "POST",
        Path:   dsl.String("/v1/payments"),
        Body: map[string]interface{}{
            "order_id": "123",
            "amount":   100.50,
        },
    }).
    WillRespondWith(dsl.Response{
        Status: 200,
        Body: map[string]interface{}{
            "transaction_id": dsl.Like("txn_456"),
            "status":         "success",
        },
    })

pact.Verify(t) // Generates pact file
```

**Provider verification:** Payment service verifies it honors contract.

**Reference:** https://github.com/pact-foundation/pact-go

### 10.2 Chaos Engineering (Litmus)

```yaml
# config/chaos/network-latency.yaml
apiVersion: litmuschaos.io/v1alpha1
kind: ChaosEngine
metadata:
  name: payment-chaos
spec:
  appinfo:
    appns: default
    applabel: "app=payment-service"
  chaosServiceAccount: litmus-admin
  experiments:
  - name: pod-network-latency
    spec:
      components:
        env:
        - name: NETWORK_LATENCY
          value: "2000"  # 2s delay
        - name: TARGET_CONTAINER
          value: "payment-service"
```

**Blast radius:** Start with dev, then staging, finally prod (1% pods).

---

## 11. Architecture Diagram (Full Stack)

```
                         ┌─────────────────┐
                         │   API Gateway   │
                         │  (Kong/Nginx)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
          ┌─────────▼─────┐ ┌────▼──────┐ ┌───▼────────┐
          │ Order Service │ │User Service│ │Catalog Svc │
          │  (Go/gRPC)    │ │  (Rust)    │ │  (Python)  │
          └───────┬───────┘ └─────┬──────┘ └─────┬──────┘
                  │               │              │
         ┌────────┼───────────────┼──────────────┘
         │        │               │
         │   ┌────▼──────┐   ┌───▼───────┐
         │   │PostgreSQL │   │  Redis    │
         │   │(Orders DB)│   │  (Cache)  │
         │   └───────────┘   └───────────┘
         │
         │ Events
         ▼
  ┌─────────────┐      ┌──────────────┐
  │Kafka Cluster│─────►│Payment Service│
  │(3 brokers)  │      │   (Go/gRPC)   │
  └─────────────┘      └───────┬───────┘
         │                     │
         ▼                     ▼
  ┌─────────────┐      ┌──────────────┐
  │Shipping Svc │      │ Stripe API   │
  │  (Event-    │      │ (External)   │
  │   driven)   │      └──────────────┘
  └─────────────┘

Observability Stack:
  Prometheus ──► Grafana
  Jaeger     ──► Grafana
  Loki       ──► Grafana

Service Mesh: Istio (Envoy sidecars, mTLS)
```

---

## 12. Threat Model

| Threat | Attack Vector | Mitigation |
|--------|---------------|------------|
| MITM | Unencrypted inter-service | mTLS (Istio PeerAuthentication STRICT) |
| Lateral Movement | Compromised pod → DB | NetworkPolicy deny-all + allowlist |
| Credential Theft | Secrets in env vars | Vault dynamic secrets, short TTL |
| API Abuse | DDoS, scraping | Rate limiting (Envoy local_rate_limit) |
| Injection | SQL/Command injection | Parameterized queries, input validation |
| Supply Chain | Malicious image | Image scanning (Trivy), admission webhook |
| Data Exfiltration | Unauthorized DB access | Row-level security, audit logs |

**Defense-in-depth layers:** See Section 7.1 (L1-L7).

---

## 13. Operational Runbook

### 13.1 Rollout Plan

1. **Pre-deployment:**
   ```bash
   # Run integration tests
   make test-integration
   
   # Build & scan image
   docker build -t order-service:v1.2.0 .
   trivy image order-service:v1.2.0 --severity HIGH,CRITICAL
   
   # Push to registry
   docker push registry.local/order-service:v1.2.0
   ```

2. **Canary deployment:**
   ```bash
   kubectl apply -f config/k8s/deployment-v1.2.0.yaml
   kubectl apply -f config/flagger/canary.yaml
   
   # Monitor metrics (5-10 min)
   kubectl logs -f deploy/flagger -n istio-system
   ```

3. **Full rollout (if canary succeeds):**
   ```bash
   kubectl set image deploy/order-service \
     order-service=registry.local/order-service:v1.2.0
   ```

### 13.2 Rollback Plan

```bash
# Immediate rollback
kubectl rollout undo deployment/order-service

# Or specify revision
kubectl rollout history deployment/order-service
kubectl rollout undo deployment/order-service --to-revision=2
```

# Microservice Architecture: Security-First, Production-Grade Design

**Summary**: Microservices decompose monoliths into isolated services communicating via APIs, enabling independent deployment, technology diversity, and fault isolation. Security-first design requires: strong service identity (mTLS), zero-trust networking, defense-in-depth at API gateways, data planes, and runtimes, encrypted storage/transit, and comprehensive observability. Production-grade patterns include: circuit breakers, distributed tracing, chaos engineering, gradual rollouts, and automated rollback. Trade-offs: operational complexity vs. deployment velocity, eventual consistency vs. strong ACID, network latency vs. isolation boundaries. This guide covers: architecture principles, communication patterns, service mesh, observability, security controls, deployment strategies, and failure modes with actionable configs/code.

---

## 1. Core Architecture Principles

### 1.1 Decomposition Strategy

**Domain-Driven Design (DDD)**: Align services with bounded contexts:
- **Aggregates**: Service owns complete lifecycle of domain entities
- **Anti-corruption layers**: Translate between service boundaries
- **Event sourcing**: Append-only event log for state changes

**Bounded Context Example**:
```
Order Service owns: Order, OrderLine, Payment
Inventory Service owns: Product, Stock, Reservation
Communication: Events (OrderPlaced) or API calls (ReserveStock)
```

**Decomposition anti-patterns**:
- **Distributed monolith**: Tight coupling via synchronous calls
- **Data coupling**: Sharing databases across services
- **Chatty services**: N+1 query problem across network

### 1.2 Service Design Patterns

**Single Responsibility**: Each service has one reason to change
```
✓ AuthService: authentication, token issuance
✗ AuthService: authentication, user profile, billing
```

**Database per Service**: Strict data ownership
```
OrderDB ─┐
         ├─ Order Service
OrderCache ┘

ProductDB ─┐
           ├─ Product Service  
ProductCache ┘
```

**API Gateway Pattern**: Single entry point
```
Client → API Gateway → [Auth, Rate Limit, Transform] → Service A/B/C
```

---

## 2. Communication Patterns

### 2.1 Synchronous Communication (Request/Response)

**HTTP/REST**:
```go
// Go: Secure HTTP client with retry, timeout, circuit breaker
package httpclient

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "net/http"
    "time"
    
    "github.com/sony/gobreaker"
)

type SecureClient struct {
    client  *http.Client
    breaker *gobreaker.CircuitBreaker
}

func NewSecureClient(caCert, clientCert, clientKey []byte) (*SecureClient, error) {
    // Load CA cert for server verification
    caCertPool := x509.NewCertPool()
    if !caCertPool.AppendCertsFromPEM(caCert) {
        return nil, errors.New("failed to append CA cert")
    }
    
    // Load client mTLS cert
    cert, err := tls.X509KeyPair(clientCert, clientKey)
    if err != nil {
        return nil, err
    }
    
    tlsConfig := &tls.Config{
        RootCAs:      caCertPool,
        Certificates: []tls.Certificate{cert},
        MinVersion:   tls.VersionTLS13,
        CipherSuites: []uint16{
            tls.TLS_AES_256_GCM_SHA384,
            tls.TLS_CHACHA20_POLY1305_SHA256,
        },
    }
    
    transport := &http.Transport{
        TLSClientConfig:     tlsConfig,
        MaxIdleConns:        100,
        MaxIdleConnsPerHost: 10,
        IdleConnTimeout:     90 * time.Second,
        DisableKeepAlives:   false,
    }
    
    client := &http.Client{
        Transport: transport,
        Timeout:   10 * time.Second,
    }
    
    // Circuit breaker settings
    cb := gobreaker.NewCircuitBreaker(gobreaker.Settings{
        Name:        "http-client",
        MaxRequests: 3,
        Interval:    10 * time.Second,
        Timeout:     60 * time.Second,
        ReadyToTrip: func(counts gobreaker.Counts) bool {
            failureRatio := float64(counts.TotalFailures) / float64(counts.Requests)
            return counts.Requests >= 3 && failureRatio >= 0.6
        },
    })
    
    return &SecureClient{client: client, breaker: cb}, nil
}

func (sc *SecureClient) Get(ctx context.Context, url string, headers map[string]string) (*http.Response, error) {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return nil, err
    }
    
    // Add headers (auth token, trace ID, etc.)
    for k, v := range headers {
        req.Header.Set(k, v)
    }
    req.Header.Set("User-Agent", "secure-client/1.0")
    
    // Execute through circuit breaker
    resp, err := sc.breaker.Execute(func() (interface{}, error) {
        return sc.client.Do(req)
    })
    
    if err != nil {
        return nil, err
    }
    return resp.(*http.Response), nil
}
```

**gRPC with mTLS**:
```go
// gRPC server with mTLS
package grpcserver

import (
    "crypto/tls"
    "crypto/x509"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

func NewSecureServer(caCert, serverCert, serverKey []byte) (*grpc.Server, error) {
    cert, err := tls.X509KeyPair(serverCert, serverKey)
    if err != nil {
        return nil, err
    }
    
    caCertPool := x509.NewCertPool()
    caCertPool.AppendCertsFromPEM(caCert)
    
    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientAuth:   tls.RequireAndVerifyClientCert,
        ClientCAs:    caCertPool,
        MinVersion:   tls.VersionTLS13,
    }
    
    creds := credentials.NewTLS(tlsConfig)
    
    return grpc.NewServer(
        grpc.Creds(creds),
        grpc.MaxRecvMsgSize(4<<20), // 4MB
        grpc.MaxSendMsgSize(4<<20),
    ), nil
}
```

### 2.2 Asynchronous Communication (Events)

**Event-Driven with NATS/Kafka**:
```go
// NATS JetStream producer
package events

import (
    "context"
    "encoding/json"
    "github.com/nats-io/nats.go"
)

type OrderEvent struct {
    OrderID   string    `json:"order_id"`
    UserID    string    `json:"user_id"`
    Total     float64   `json:"total"`
    Timestamp time.Time `json:"timestamp"`
}

type EventPublisher struct {
    js nats.JetStreamContext
}

func NewEventPublisher(nc *nats.Conn) (*EventPublisher, error) {
    js, err := nc.JetStream()
    if err != nil {
        return nil, err
    }
    
    // Create stream if not exists
    _, err = js.AddStream(&nats.StreamConfig{
        Name:       "ORDERS",
        Subjects:   []string{"orders.*"},
        Retention:  nats.WorkQueuePolicy,
        MaxAge:     24 * time.Hour,
        Storage:    nats.FileStorage,
        Replicas:   3,
    })
    if err != nil && err != nats.ErrStreamNameAlreadyInUse {
        return nil, err
    }
    
    return &EventPublisher{js: js}, nil
}

func (ep *EventPublisher) PublishOrderCreated(ctx context.Context, event OrderEvent) error {
    data, err := json.Marshal(event)
    if err != nil {
        return err
    }
    
    _, err = ep.js.Publish("orders.created", data, nats.Context(ctx))
    return err
}

// Consumer with at-least-once delivery
func (ep *EventPublisher) ConsumeOrders(ctx context.Context, handler func(OrderEvent) error) error {
    sub, err := ep.js.PullSubscribe("orders.*", "order-processor", nats.ManualAck())
    if err != nil {
        return err
    }
    
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        default:
            msgs, err := sub.Fetch(10, nats.MaxWait(5*time.Second))
            if err != nil {
                continue
            }
            
            for _, msg := range msgs {
                var event OrderEvent
                if err := json.Unmarshal(msg.Data, &event); err != nil {
                    msg.Nak()
                    continue
                }
                
                if err := handler(event); err != nil {
                    msg.Nak()
                    continue
                }
                
                msg.Ack()
            }
        }
    }
}
```

**Saga Pattern (Distributed Transactions)**:
```
Order Service: CreateOrder() → OrderCreated event
                ↓
Inventory: ReserveStock() → StockReserved event
                ↓ (failure)
Inventory: ReleaseStock() → Compensating transaction
                ↓
Order Service: CancelOrder() → OrderCancelled event
```

---

## 3. Service Mesh Architecture

### 3.1 Control Plane vs Data Plane

```
┌─────────────────────────────────────────────────────┐
│              Control Plane (Istiod)                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐         │
│  │  Pilot   │  │  Citadel │  │  Galley  │         │
│  │(Config)  │  │  (Certs) │  │ (Config) │         │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘         │
└───────┼────────────┼─────────────┼─────────────────┘
        │            │             │
        ├────────────┼─────────────┤
        ↓            ↓             ↓
┌────────────────────────────────────────┐
│         Data Plane (Envoy Proxies)     │
│  ┌─────────────┐      ┌──────────────┐│
│  │  Service A  │      │  Service B   ││
│  │  ┌───────┐  │      │  ┌────────┐  ││
│  │  │ App   │  │      │  │  App   │  ││
│  │  └───┬───┘  │      │  └───┬────┘  ││
│  │  ┌───┴───┐  │      │  ┌───┴────┐  ││
│  │  │Envoy  │◄─┼──────┼─►│ Envoy  │  ││
│  │  │Sidecar│  │ mTLS │  │Sidecar │  ││
│  │  └───────┘  │      │  └────────┘  ││
│  └─────────────┘      └──────────────┘│
└────────────────────────────────────────┘
```

### 3.2 Istio Configuration

**PeerAuthentication (Enforce mTLS)**:
```yaml
# istio-mtls.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT  # Reject plaintext traffic
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: order-service-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-service
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/api-gateway"]
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/orders/*"]
```

**DestinationRule (Circuit Breaking, TLS)**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: inventory-service
spec:
  host: inventory-service.production.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL  # Use Istio-managed mTLS certs
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutiveErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
```

**VirtualService (Traffic Splitting)**:
```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: order-service
spec:
  hosts:
  - order-service.production.svc.cluster.local
  http:
  - match:
    - headers:
        x-version:
          exact: "v2"
    route:
    - destination:
        host: order-service.production.svc.cluster.local
        subset: v2
      weight: 100
  - route:
    - destination:
        host: order-service.production.svc.cluster.local
        subset: v1
      weight: 90
    - destination:
        host: order-service.production.svc.cluster.local
        subset: v2
      weight: 10
```

---

## 4. Observability Stack

### 4.1 Three Pillars

**Metrics (Prometheus)**:
```yaml
# prometheus-servicemonitor.yaml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: order-service
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-service
  endpoints:
  - port: metrics
    interval: 15s
    path: /metrics
    scheme: https
    tlsConfig:
      caFile: /etc/prometheus/secrets/tls-ca/ca.crt
      certFile: /etc/prometheus/secrets/tls-client/tls.crt
      keyFile: /etc/prometheus/secrets/tls-client/tls.key
```

**Application Metrics (Go)**:
```go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
)

var (
    httpDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "http_request_duration_seconds",
        Help:    "HTTP request latency",
        Buckets: prometheus.DefBuckets,
    }, []string{"method", "path", "status"})
    
    dbQueryDuration = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "db_query_duration_seconds",
        Help:    "Database query latency",
        Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1},
    }, []string{"operation", "table"})
    
    activeConnections = promauto.NewGauge(prometheus.GaugeOpts{
        Name: "db_active_connections",
        Help: "Active database connections",
    })
    
    orderTotal = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "orders_total",
        Help: "Total orders processed",
    }, []string{"status"})
)

func RecordHTTPMetrics(method, path string, status int, duration float64) {
    httpDuration.WithLabelValues(method, path, fmt.Sprintf("%d", status)).Observe(duration)
}
```

**Tracing (OpenTelemetry)**:
```go
package tracing

import (
    "context"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/jaeger"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.4.0"
    "go.opentelemetry.io/otel/trace"
)

func InitTracer(serviceName, jaegerURL string) (func(), error) {
    exporter, err := jaeger.New(jaeger.WithCollectorEndpoint(jaeger.WithEndpoint(jaegerURL)))
    if err != nil {
        return nil, err
    }
    
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceNameKey.String(serviceName),
        )),
        sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.TraceIDRatioBased(0.1))), // 10% sampling
    )
    
    otel.SetTracerProvider(tp)
    
    return func() { tp.Shutdown(context.Background()) }, nil
}

// Usage in HTTP handler
func HandleOrder(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("order-service")
    
    ctx, span := tracer.Start(ctx, "HandleOrder")
    defer span.End()
    
    // Add attributes
    span.SetAttributes(
        attribute.String("order.id", orderID),
        attribute.Float64("order.total", total),
    )
    
    // Call downstream service with propagated context
    if err := callInventory(ctx, orderID); err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, err.Error())
    }
}
```

**Logging (Structured)**:
```go
package logging

import (
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

func NewLogger(level string) (*zap.Logger, error) {
    config := zap.Config{
        Level:            zap.NewAtomicLevelAt(getLevel(level)),
        Encoding:         "json",
        OutputPaths:      []string{"stdout"},
        ErrorOutputPaths: []string{"stderr"},
        EncoderConfig: zapcore.EncoderConfig{
            TimeKey:        "timestamp",
            LevelKey:       "level",
            MessageKey:     "msg",
            StacktraceKey:  "stacktrace",
            EncodeTime:     zapcore.ISO8601TimeEncoder,
            EncodeLevel:    zapcore.LowercaseLevelEncoder,
            EncodeDuration: zapcore.SecondsDurationEncoder,
        },
    }
    
    return config.Build(zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel))
}

// Usage
logger, _ := NewLogger("info")
logger.Info("order created",
    zap.String("order_id", orderID),
    zap.String("user_id", userID),
    zap.Float64("total", total),
    zap.Duration("processing_time", duration),
)
```

---

## 5. Security Controls

### 5.1 Defense-in-Depth Layers

```
┌─────────────────────────────────────────────────┐
│  1. Network Perimeter: WAF, DDoS, TLS           │
├─────────────────────────────────────────────────┤
│  2. API Gateway: Auth, Rate Limit, Validation   │
├─────────────────────────────────────────────────┤
│  3. Service Mesh: mTLS, AuthZ Policy            │
├─────────────────────────────────────────────────┤
│  4. Application: Input Validation, AuthN/AuthZ  │
├─────────────────────────────────────────────────┤
│  5. Data: Encryption at Rest, Key Rotation      │
├─────────────────────────────────────────────────┤
│  6. Runtime: Seccomp, AppArmor, Read-only FS    │
└─────────────────────────────────────────────────┘
```

### 5.2 Identity and Access Management

**SPIFFE/SPIRE (Workload Identity)**:
```yaml
# spire-server.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: spire-server
  namespace: spire
data:
  server.conf: |
    server {
      bind_address = "0.0.0.0"
      bind_port = "8081"
      trust_domain = "production.example.com"
      data_dir = "/run/spire/data"
      log_level = "INFO"
      ca_ttl = "24h"
      default_svid_ttl = "1h"
    }
    
    plugins {
      DataStore "sql" {
        plugin_data {
          database_type = "postgres"
          connection_string = "dbname=spire user=spire password=*** host=postgres"
        }
      }
      
      KeyManager "disk" {
        plugin_data {
          keys_path = "/run/spire/data/keys.json"
        }
      }
      
      NodeAttestor "k8s_psat" {
        plugin_data {
          clusters = {
            "production-cluster" = {
              service_account_allow_list = ["spire:spire-agent"]
            }
          }
        }
      }
    }
```

**OAuth2/OIDC Integration**:
```go
package auth

import (
    "context"
    "github.com/coreos/go-oidc/v3/oidc"
    "golang.org/x/oauth2"
)

type Authenticator struct {
    provider *oidc.Provider
    verifier *oidc.IDTokenVerifier
    config   oauth2.Config
}

func NewAuthenticator(issuerURL, clientID, clientSecret string) (*Authenticator, error) {
    ctx := context.Background()
    provider, err := oidc.NewProvider(ctx, issuerURL)
    if err != nil {
        return nil, err
    }
    
    verifier := provider.Verifier(&oidc.Config{
        ClientID:          clientID,
        SkipExpiryCheck:   false,
        SkipIssuerCheck:   false,
        SupportedSigningAlgs: []string{oidc.RS256},
    })
    
    config := oauth2.Config{
        ClientID:     clientID,
        ClientSecret: clientSecret,
        Endpoint:     provider.Endpoint(),
        Scopes:       []string{oidc.ScopeOpenID, "profile", "email"},
    }
    
    return &Authenticator{
        provider: provider,
        verifier: verifier,
        config:   config,
    }, nil
}

func (a *Authenticator) VerifyToken(ctx context.Context, rawToken string) (*oidc.IDToken, error) {
    return a.verifier.Verify(ctx, rawToken)
}
```

### 5.3 Secrets Management

**Vault Integration**:
```go
package secrets

import (
    "context"
    vault "github.com/hashicorp/vault/api"
)

type VaultClient struct {
    client *vault.Client
}

func NewVaultClient(addr, token string) (*VaultClient, error) {
    config := vault.DefaultConfig()
    config.Address = addr
    
    client, err := vault.NewClient(config)
    if err != nil {
        return nil, err
    }
    
    client.SetToken(token)
    
    return &VaultClient{client: client}, nil
}

func (vc *VaultClient) GetDatabaseCreds(ctx context.Context, role string) (string, string, error) {
    secret, err := vc.client.Logical().ReadWithContext(ctx, "database/creds/"+role)
    if err != nil {
        return "", "", err
    }
    
    username := secret.Data["username"].(string)
    password := secret.Data["password"].(string)
    
    // Start renewal goroutine
    go vc.renewLease(secret.LeaseID, secret.LeaseDuration)
    
    return username, password, nil
}

func (vc *VaultClient) renewLease(leaseID string, duration int) {
    ticker := time.NewTicker(time.Duration(duration/2) * time.Second)
    defer ticker.Stop()
    
    for range ticker.C {
        _, err := vc.client.Sys().Renew(leaseID, duration)
        if err != nil {
            log.Error("failed to renew lease", zap.Error(err))
            return
        }
    }
}
```

### 5.4 Network Policies (Zero-Trust)

```yaml
# k8s-networkpolicy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: order-service-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: order-service
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: api-gateway
    ports:
    - protocol: TCP
      port: 8080
  egress:
  - to:
    - podSelector:
        matchLabels:
          app: inventory-service
    ports:
    - protocol: TCP
      port: 8080
  - to:
    - podSelector:
        matchLabels:
          app: postgres
    ports:
    - protocol: TCP
      port: 5432
  - to:  # Allow DNS
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

---

## 6. Data Management

### 6.1 Database Patterns

**Database per Service with Replication**:
```
┌──────────────┐     ┌──────────────┐
│ Order Service│     │ Inventory Svc│
└──────┬───────┘     └──────┬───────┘
       │                    │
   ┌───▼────┐          ┌────▼───┐
   │OrderDB │          │ProdDB  │
   │(Primary)│         │(Primary)│
   └───┬────┘          └────┬───┘
       │                    │
    ┌──┴──┐              ┌──┴──┐
    │Repli│              │Repli│
    │ca-1 │              │ca-1 │
    └─────┘              └─────┘
```

**Outbox Pattern (Transactional Event Publishing)**:
```go
package outbox

import (
    "context"
    "database/sql"
    "encoding/json"
)

type OutboxEvent struct {
    ID        string
    EventType string
    Payload   json.RawMessage
    CreatedAt time.Time
    Published bool
}

func PublishOrderCreated(ctx context.Context, tx *sql.Tx, order Order) error {
    // Insert into orders table
    _, err := tx.ExecContext(ctx, 
        "INSERT INTO orders (id, user_id, total, status) VALUES ($1, $2, $3, $4)",
        order.ID, order.UserID, order.Total, order.Status,
    )
    if err != nil {
        return err
    }
    
    // Insert into outbox table (same transaction)
    event := OrderCreatedEvent{OrderID: order.ID, Total: order.Total}
    payload, _ := json.Marshal(event)
    
    _, err = tx.ExecContext(ctx,
        "INSERT INTO outbox (id, event_type, payload, created_at, published) VALUES ($1, $2, $3, $4, $5)",
        uuid.New().String(), "order.created", payload, time.Now(), false,
    )
    
    return err
}

// Background worker polls outbox and publishes to message broker
func RunOutboxPublisher(ctx context.Context, db *sql.DB, publisher EventPublisher) error {
    ticker := time.NewTicker(1 * time.Second)
    defer ticker.Stop()
    
    for {
        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-ticker.C:
            tx, err := db.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
            if err != nil {
                continue
            }
            
            rows, err := tx.QueryContext(ctx,
                "SELECT id, event_type, payload FROM outbox WHERE published = false ORDER BY created_at LIMIT 100 FOR UPDATE SKIP LOCKED",
            )
            if err != nil {
                tx.Rollback()
                continue
            }
            
            var eventIDs []string
            for rows.Next() {
                var event OutboxEvent
                if err := rows.Scan(&event.ID, &event.EventType, &event.Payload); err != nil {
                    continue
                }
                
                if err := publisher.Publish(ctx, event.EventType, event.Payload); err != nil {
                    continue
                }
                
                eventIDs = append(eventIDs, event.ID)
            }
            rows.Close()
            
            if len(eventIDs) > 0 {
                _, err = tx.ExecContext(ctx,
                    "UPDATE outbox SET published = true WHERE id = ANY($1)",
                    pq.Array(eventIDs),
                )
            }
            
            tx.Commit()
        }
    }
}
```

### 6.2 Caching Strategy

**Multi-Level Cache**:
```go
package cache

import (
    "context"
    "encoding/json"
    "github.com/allegro/bigcache/v3"
    "github.com/redis/go-redis/v9"
)

type MultiLevelCache struct {
    l1 *bigcache.BigCache  // In-memory
    l2 *redis.Client       // Distributed
}

func NewMultiLevelCache(redisAddr string) (*MultiLevelCache, error) {
    // L1: In-memory cache (per-instance)
    l1, err := bigcache.New(context.Background(), bigcache.Config{
        Shards:           1024,
        LifeWindow:       10 * time.Minute,
        MaxEntriesInWindow: 1000 * 10 * 60,
        MaxEntrySize:     500,
        HardMaxCacheSize: 256, // MB
    })
    if err != nil {
        return nil, err
    }
    
    // L2: Redis (cluster-wide)
    l2 := redis.NewClient(&redis.Options{
        Addr:     redisAddr,
        Password: "", // no password
        DB:       0,
    })
    return &MultiLevelCache{l1: l1, l2: l2}, nil
}
func (mc *MultiLevelCache) Get(ctx context.Context, key string, dest interface{}) error {
    // Try L1
    if entry, err := mc.l1.Get(key); err == nil {
        return json.Unmarshal(entry, dest)
    }
    // Try L2
    val, err := mc.l2.Get(ctx, key).Result()
    if err == nil {
        mc.l1.Set(key, []byte(val)) // Populate L1
        return json.Unmarshal([]byte(val), dest)
    }
    return err
}
func (mc *MultiLevelCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    data, err := json.Marshal(value)
    if err != nil {
        return err
    }
    // Set L1
    mc.l1.Set(key, data)
    // Set L2
    return mc.l2.Set(ctx, key, data, ttl).Err()
} 
```