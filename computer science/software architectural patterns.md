# Software Architectural Patterns: A Comprehensive Guide

Architecture is the art of making decisions you cannot easily reverse. Understanding architectural patterns is understanding *how systems think* — the skeleton upon which all logic, data flow, and behavior hangs. This guide will take you from foundational concepts through every major pattern with the rigor of an engineering architect and the clarity of a master teacher.

---

## What Is Software Architecture?

Software architecture is the set of **significant design decisions** that define a system's structure, behavior, and quality attributes. These decisions are "significant" precisely because they are expensive to change. Architecture answers three fundamental questions: how is the system decomposed, how do the parts communicate, and how does the system respond to change and failure?

The key insight is that architecture is not about code — it is about *constraints*. Every architectural pattern is essentially a set of rules that restrict what is possible in exchange for making certain quality attributes achievable. A monolith restricts independent deployment but makes transactional consistency trivial. Microservices enable independent deployment but make consistency costly. You are always trading.

---

## The Quality Attribute Vocabulary

Before patterns, you must internalize the attributes patterns optimize for. These are the measurable dimensions of system quality:

**Scalability** is the ability to handle increased load by adding resources. Horizontal scaling (adding more machines) is generally preferable to vertical scaling (adding bigger machines) because it has no upper bound. **Performance** is about latency and throughput under a given load. **Availability** is the percentage of time a system can serve requests — often expressed as "nines" (99.9% = ~8.7 hours downtime/year, 99.999% = ~5 minutes/year). **Reliability** is the probability of correct behavior over time. **Maintainability** measures how easily the system can be changed. **Testability** measures how easily correctness can be verified. **Security** encompasses confidentiality, integrity, and availability of data and functions.

Every pattern is a specific answer to the question: "Which of these attributes matter most to you, and what are you willing to sacrifice?"

---

## Tier-Based Patterns: The Foundational Decomposition

### Monolithic Architecture

A monolith is a single deployable unit where all components — UI, business logic, data access — compile and deploy together. This is the natural starting point for any system, and it is far more powerful than the industry's microservices enthusiasm suggests.

The strength of a monolith is **co-location**: all modules share memory, can call each other directly as function calls (nanoseconds), and participate in a single database transaction. Testing is simple. Debugging is straightforward. Deployment is atomic. For a team of under 20 engineers building a product under 5 years old, a well-structured monolith almost always outperforms a distributed system in development velocity.

The failure mode of a monolith is **coupling**. When modules can see each other freely, they tend to become entangled. A change in the payment module breaks the notification module. The solution is not to immediately decompose the monolith, but to enforce architectural boundaries *within* it — which is the modular monolith.

A **Modular Monolith** divides the application into clearly bounded modules with explicit public APIs and zero direct access to each other's internals. In Rust, this maps naturally to crates with controlled `pub` visibility. In Go, it maps to packages where internal types are unexported. The discipline is the architecture — the modules could theoretically be extracted into services later if needed.

```rust
// mod payment — public API surface
pub mod payment {
    pub struct PaymentService { /* ... */ }
    pub struct PaymentResult { /* ... */ }
    
    impl PaymentService {
        pub fn charge(&self, amount: Money, method: PaymentMethod) -> Result<PaymentResult, PaymentError> {
            // internal details hidden
            self.validate_method(&method)?;
            self.process_charge(amount, method)
        }
        
        fn validate_method(&self, method: &PaymentMethod) -> Result<(), PaymentError> { /* private */ }
        fn process_charge(&self, amount: Money, method: PaymentMethod) -> Result<PaymentResult, PaymentError> { /* private */ }
    }
}
```

### N-Tier / Layered Architecture

The layered pattern organizes code into horizontal layers where each layer only depends on the layer directly below it. The classic three-tier structure is Presentation → Business Logic → Data Access.

The key constraint is the **dependency rule**: upper layers know about lower layers; lower layers never know about upper layers. This creates a one-directional flow that makes each layer independently testable and replaceable.

The pathology of layered architecture is the **anemic domain model**: when business logic bleeds into every layer because the "business logic" layer becomes just a thin pass-through, and real logic lives in stored procedures, in the presentation layer, and in the data access layer simultaneously. The cure is a rich domain model — discussed under DDD below.

---

## Distributed Architectural Patterns

### Service-Oriented Architecture (SOA)

SOA predates microservices and shares its core premise: decompose a system into services that communicate over a network. The distinguishing feature of classical SOA is the **Enterprise Service Bus (ESB)** — a centralized integration hub responsible for message routing, transformation, orchestration, and protocol mediation.

SOA solved real problems in the early 2000s: heterogeneous systems (COBOL, Java, .NET) that couldn't share code could share messages. The ESB translated between them. The failure mode was the ESB itself becoming an object — a centralized bottleneck where business logic migrated because it was "convenient" to do the transformation there. When the ESB fails, everything fails.

### Microservices Architecture

Microservices is SOA with the ESB removed and replaced by a philosophy: **smart endpoints, dumb pipes**. Services communicate directly over lightweight protocols (HTTP/REST, gRPC, message queues). Each service is independently deployable, independently scalable, and owned by a small autonomous team.

The theoretical foundation is Conway's Law: *a system's architecture mirrors the communication structure of the organization that builds it*. Microservices is Conway's Law deliberately weaponized — you design the team boundaries first, then the service boundaries follow.

The **defining characteristics** of a true microservice are: single responsibility (it does one thing extremely well), independent deployability (no coordinated releases), decentralized data management (each service owns its database and no other service touches it directly), and design for failure (it assumes its dependencies will fail).

The cost is **distributed systems complexity**. Network calls fail. They have latency. They can partially succeed. Transactions that were trivially atomic in a monolith now require careful design. Data that was a simple join is now a cross-service call or a denormalized copy. **This complexity is real, non-trivial, and often underestimated.**

```go
// Go microservice: clean HTTP handler with explicit error handling
type OrderService struct {
    repo        OrderRepository
    paymentClient PaymentClient  // interface — the real implementation is a network call
    events      EventPublisher
}

func (s *OrderService) CreateOrder(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    // validate
    if err := req.Validate(); err != nil {
        return nil, fmt.Errorf("validation: %w", err)
    }
    
    // create order in pending state
    order := NewOrder(req.CustomerID, req.Items)
    if err := s.repo.Save(ctx, order); err != nil {
        return nil, fmt.Errorf("saving order: %w", err)
    }
    
    // charge — this can fail; we need compensation logic (saga pattern)
    if _, err := s.paymentClient.Charge(ctx, order.ID, order.Total()); err != nil {
        // compensate: cancel the order
        order.Cancel()
        _ = s.repo.Save(ctx, order)
        return nil, fmt.Errorf("payment: %w", err)
    }
    
    order.Confirm()
    if err := s.repo.Save(ctx, order); err != nil {
        return nil, fmt.Errorf("confirming order: %w", err)
    }
    
    s.events.Publish(ctx, OrderConfirmedEvent{OrderID: order.ID})
    return order, nil
}
```

### Event-Driven Architecture (EDA)

In EDA, services communicate by emitting and consuming events rather than making direct calls. An event is an immutable record of something that happened: `OrderPlaced`, `PaymentProcessed`, `InventoryReserved`. Events are facts, not commands.

The critical distinction is between **commands** ("ProcessPayment" — a request directed at a specific service, expecting a response), **events** ("PaymentProcessed" — a broadcast of something that happened, with no expectation of response), and **queries** ("GetOrderStatus" — a request for data). Getting this distinction wrong leads to event-driven systems that are actually just synchronous RPC with extra steps.

The power of EDA is **temporal decoupling**: the producer does not wait for the consumer. The inventory service does not need to be running when the order service emits `OrderPlaced`. The consumer processes it when it can. This enables extreme resilience and scalability.

The cost is **eventual consistency** and **debugging complexity**. Following the causal chain of a business transaction across dozens of events in different services requires dedicated tooling (distributed tracing, event sourcing, correlation IDs).

**Event Sourcing** is a closely related pattern where the state of an entity is not stored directly, but reconstructed by replaying its event history. Instead of updating a row in a database, you append an event to an event log: `[AccountOpened, MoneyDeposited(100), MoneyWithdrawn(30), MoneyDeposited(50)]`. The current balance (120) is a projection of that log.

This is powerful: you have a complete audit trail, you can reconstruct state at any point in time, and you can build new projections retroactively. The cost is that reads require projection, eventual consistency between the event log and projections, and the unfamiliarity of the pattern for most engineers.

```rust
// Event sourcing: account aggregate
#[derive(Debug, Clone)]
enum AccountEvent {
    Opened { initial_balance: Money },
    Deposited { amount: Money, transaction_id: Uuid },
    Withdrawn { amount: Money, transaction_id: Uuid },
    Frozen { reason: String },
}

#[derive(Debug, Default)]
struct Account {
    id: Uuid,
    balance: Money,
    is_frozen: bool,
    version: u64,
}

impl Account {
    fn apply(&mut self, event: &AccountEvent) {
        match event {
            AccountEvent::Opened { initial_balance } => {
                self.balance = *initial_balance;
            }
            AccountEvent::Deposited { amount, .. } => {
                self.balance += *amount;
            }
            AccountEvent::Withdrawn { amount, .. } => {
                self.balance -= *amount;
            }
            AccountEvent::Frozen { .. } => {
                self.is_frozen = true;
            }
        }
        self.version += 1;
    }

    fn from_events(id: Uuid, events: &[AccountEvent]) -> Self {
        let mut account = Account { id, ..Default::default() };
        for event in events {
            account.apply(event);
        }
        account
    }
    
    fn withdraw(&self, amount: Money) -> Result<AccountEvent, DomainError> {
        if self.is_frozen {
            return Err(DomainError::AccountFrozen);
        }
        if self.balance < amount {
            return Err(DomainError::InsufficientFunds);
        }
        Ok(AccountEvent::Withdrawn { amount, transaction_id: Uuid::new_v4() })
    }
}
```

---

## Data Management Patterns

### CQRS (Command Query Responsibility Segregation)

CQRS separates the write model (commands that change state) from the read model (queries that return data). At its simplest, this is just having separate objects for reads and writes. At its most sophisticated, it involves entirely separate databases optimized for each concern — a normalized relational store for writes, a denormalized document store or read cache for reads.

The insight is that the optimal data model for writes (transactional integrity, normalization) is rarely the optimal model for reads (pre-joined, denormalized, shaped to the exact needs of the UI). By separating them, you can optimize each independently.

CQRS almost always pairs with Event Sourcing: the write side appends events, the read side listens to those events and updates its projections. This combination is sometimes called **CQRS/ES** and represents one of the most powerful patterns for complex domains with heavy read load.

### Saga Pattern

A saga manages a long-running business transaction that spans multiple services, without using a distributed transaction (which are costly and brittle). There are two implementations:

**Choreography-based sagas** have no central coordinator. Each service listens for events and emits new events in response. `OrderService` emits `OrderPlaced` → `PaymentService` consumes it, charges the card, emits `PaymentProcessed` → `InventoryService` reserves stock, emits `StockReserved` → etc. If `PaymentService` fails, it emits `PaymentFailed` and each prior service that already succeeded must listen and execute a **compensating transaction** (cancel the order).

**Orchestration-based sagas** have a central coordinator (the saga orchestrator) that tells each service what to do and handles failures. The orchestrator is stateful — it knows which steps have completed and which compensations need to run.

Choreography scales better and has no single point of failure but is harder to reason about. Orchestration is easier to understand and debug but centralizes logic. The choice depends on your team's discipline and tooling.

---

## Domain-Centric Patterns

### Domain-Driven Design (DDD)

DDD is not just an architectural pattern — it is a philosophy of how software should model reality. Its central premise is that the complexity of software comes from the domain, not the technology, and that the domain model should be the centerpiece of the architecture.

**Ubiquitous Language** is the most important concept: developers and domain experts speak the same language, and that language is encoded in the code. The class is not `OrderRecord` — it is `Order`. The method is not `updateOrderStatusToShipped` — it is `order.ship()`. When the code reads like the business speaks, the gap between requirements and implementation narrows to near-zero.

**Bounded Contexts** are explicit boundaries within which a particular model applies. "Product" in the catalog context means something with a name, description, and photos. "Product" in the inventory context means something with a SKU, quantity, and location. These are different models, and trying to unify them creates an object that satisfies neither context perfectly. Bounded contexts are the DDD answer to the service boundary question in microservices.

**Aggregates** are clusters of domain objects (entities and value objects) that are treated as a single unit for the purpose of data changes. An `Order` aggregate contains `OrderLine` entities and a `ShippingAddress` value object. The `Order` is the **aggregate root** — the only entry point. Nothing outside the aggregate may hold a direct reference to `OrderLine`; they must go through `Order`. This enforces invariants: you cannot add an order line to a cancelled order, because you can only add lines through `order.addItem()` which enforces that rule.

```rust
// Rich domain model — behavior lives on the aggregate
pub struct Order {
    id: OrderId,
    customer_id: CustomerId,
    lines: Vec<OrderLine>,
    status: OrderStatus,
    total: Money,
}

impl Order {
    pub fn add_item(&mut self, product: &Product, quantity: Quantity) -> Result<(), OrderError> {
        if self.status != OrderStatus::Draft {
            return Err(OrderError::CannotModifyNonDraftOrder);
        }
        if quantity.is_zero() {
            return Err(OrderError::QuantityMustBePositive);
        }
        
        // check if line exists, update or create
        match self.lines.iter_mut().find(|l| l.product_id == product.id) {
            Some(line) => line.quantity += quantity,
            None => self.lines.push(OrderLine::new(product, quantity)),
        }
        
        self.total = self.calculate_total();
        Ok(())
    }
    
    pub fn submit(&mut self) -> Result<OrderSubmittedEvent, OrderError> {
        if self.lines.is_empty() {
            return Err(OrderError::CannotSubmitEmptyOrder);
        }
        if self.status != OrderStatus::Draft {
            return Err(OrderError::AlreadySubmitted);
        }
        self.status = OrderStatus::Submitted;
        Ok(OrderSubmittedEvent { order_id: self.id, total: self.total })
    }
}
```

**Domain Services** handle operations that don't naturally belong to any single entity — for example, a `TransferService` that moves money between two `Account` aggregates. **Repositories** are abstractions over persistence — the domain layer defines the interface, the infrastructure layer implements it. This is the Dependency Inversion Principle at the architectural level.

### Hexagonal Architecture (Ports and Adapters)

Coined by Alistair Cockburn, hexagonal architecture places the domain at the center and all I/O at the periphery. The domain has no dependencies on any framework, database, or external service. It defines **ports** (interfaces) for what it needs, and **adapters** implement those ports for specific technologies.

A `PaymentPort` interface in the domain says "I need something that can charge a card." A `StripeAdapter` implements that interface using the Stripe API. A `MockPaymentAdapter` implements it for testing. The domain never imports Stripe's SDK — it cannot even know it exists.

```go
// port — defined in the domain layer
type PaymentPort interface {
    Charge(ctx context.Context, amount Money, token string) (ChargeID, error)
    Refund(ctx context.Context, chargeID ChargeID, amount Money) error
}

// adapter — defined in the infrastructure layer
type StripeAdapter struct {
    client *stripe.Client
}

func (a *StripeAdapter) Charge(ctx context.Context, amount Money, token string) (ChargeID, error) {
    params := &stripe.ChargeParams{
        Amount:   stripe.Int64(amount.Cents()),
        Currency: stripe.String("usd"),
        Source:   &stripe.SourceParams{Token: stripe.String(token)},
    }
    charge, err := a.client.Charges.New(params)
    if err != nil {
        return "", fmt.Errorf("stripe charge: %w", err)
    }
    return ChargeID(charge.ID), nil
}

// test adapter — zero external dependencies
type MockPaymentAdapter struct {
    charges []ChargeRecord
    failNext bool
}

func (m *MockPaymentAdapter) Charge(_ context.Context, amount Money, token string) (ChargeID, error) {
    if m.failNext {
        return "", errors.New("payment declined")
    }
    id := ChargeID(fmt.Sprintf("mock_%d", len(m.charges)))
    m.charges = append(m.charges, ChargeRecord{ID: id, Amount: amount})
    return id, nil
}
```

This pattern makes the domain completely portable and independently testable. Swap Stripe for Braintree? Write a new adapter. Move from PostgreSQL to DynamoDB? Write a new repository adapter. The domain code doesn't change.

### Clean Architecture

Robert Martin's Clean Architecture is a generalization of hexagonal architecture with explicit concentric circles: **Entities** (innermost — pure domain objects with no dependencies), **Use Cases** (application logic — orchestrates entities to fulfill a user's intent), **Interface Adapters** (converts between use case format and external format — controllers, presenters, gateways), and **Frameworks & Drivers** (outermost — the database, web framework, UI).

The dependency rule is absolute: source code dependencies may only point *inward*. A use case may depend on an entity. An adapter may depend on a use case. Nothing inner ever knows about something outer.

The practical benefit is that use cases can be tested without a web framework, database, or any external service. A use case is pure logic — input goes in, output comes out. The adapter wires it to HTTP; the test wires it directly.

---

## Resilience and Scalability Patterns

### Circuit Breaker

Named after the electrical device, a circuit breaker monitors calls to an external service. When failures exceed a threshold, the circuit "opens" — subsequent calls immediately return an error without attempting the network call, giving the failing service time to recover. After a timeout, the circuit transitions to "half-open" and allows a probe request through. If it succeeds, the circuit closes; if it fails, it opens again.

This is essential in microservices because **cascading failures** are the primary cause of system-wide outages. If Service A calls Service B and B is slow (not failing, just slow), A's threads/goroutines pile up waiting. Soon A is out of threads and starts failing. C calls A and starts accumulating slow calls. The entire system degrades despite only one service having a problem.

```go
type CircuitBreaker struct {
    mu           sync.Mutex
    state        State  // Closed, Open, HalfOpen
    failures     int
    threshold    int
    lastFailure  time.Time
    timeout      time.Duration
}

func (cb *CircuitBreaker) Call(fn func() error) error {
    cb.mu.Lock()
    
    switch cb.state {
    case Open:
        if time.Since(cb.lastFailure) > cb.timeout {
            cb.state = HalfOpen
        } else {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
    }
    
    cb.mu.Unlock()
    
    err := fn()
    
    cb.mu.Lock()
    defer cb.mu.Unlock()
    
    if err != nil {
        cb.failures++
        cb.lastFailure = time.Now()
        if cb.failures >= cb.threshold || cb.state == HalfOpen {
            cb.state = Open
        }
        return err
    }
    
    // success
    cb.failures = 0
    cb.state = Closed
    return nil
}
```

### Bulkhead

The bulkhead pattern (from ship compartmentalization) isolates failures to a subset of the system. In practice, this means giving different consumers or different operations separate thread pools or connection pools. If one pool exhausts, others are unaffected.

In Go, this translates to having separate goroutine workers or separate rate limiters per client or operation class. In a web server, you might give `POST /payments` a separate connection pool to the payment database than `GET /products` uses for the product database.

### Retry with Exponential Backoff and Jitter

Never retry immediately. If a service is overwhelmed, immediate retries make it worse. Exponential backoff doubles the wait time on each retry (100ms, 200ms, 400ms, 800ms...). Jitter adds randomness to prevent the **thundering herd problem** where hundreds of services all back off and retry simultaneously at the same interval.

```rust
async fn call_with_retry<F, Fut, T, E>(
    mut operation: F,
    max_retries: u32,
    base_delay: Duration,
) -> Result<T, E>
where
    F: FnMut() -> Fut,
    Fut: Future<Output = Result<T, E>>,
    E: std::error::Error,
{
    let mut delay = base_delay;
    
    for attempt in 0..=max_retries {
        match operation().await {
            Ok(result) => return Ok(result),
            Err(e) if attempt == max_retries => return Err(e),
            Err(_) => {
                // jitter: random between 50% and 150% of delay
                let jitter = rand::thread_rng().gen_range(0.5..1.5);
                let actual_delay = delay.mul_f64(jitter);
                tokio::time::sleep(actual_delay).await;
                delay = (delay * 2).min(Duration::from_secs(30)); // cap at 30s
            }
        }
    }
    unreachable!()
}
```

### Sidecar Pattern

In container-based environments, a sidecar is a secondary container that runs alongside the primary service container in the same pod/host. The sidecar handles cross-cutting concerns: service discovery, TLS termination, circuit breaking, distributed tracing, log collection. The service itself knows nothing about these concerns.

Service meshes (Istio, Linkerd) are built entirely on the sidecar pattern — a proxy sidecar intercepts all network traffic in and out of each service, providing observability and resilience transparently.

---

## Messaging and Communication Patterns

### Publish-Subscribe

Publishers emit messages to a topic without knowledge of subscribers. Subscribers express interest in topics without knowledge of publishers. The broker mediates. This achieves temporal and spatial decoupling — neither party needs to know about the other or be running simultaneously.

The critical design decision in pub-sub is **message durability** (messages persisted so late-starting consumers don't miss them — Kafka, Pulsar), **delivery guarantees** (at-most-once, at-least-once, exactly-once), and **consumer groups** (multiple instances of the same service share a partition, providing parallel consumption without duplicate processing).

### Request-Reply over Messaging

Sometimes you need synchronous behavior over an asynchronous transport. The pattern: the requester sends a message with a `reply-to` address and a `correlation-id`. The responder sends the reply to that address with the same `correlation-id`. The requester matches the reply by ID. This gives you the reliability benefits of a message broker with the semantic simplicity of RPC.

### Outbox Pattern

The most insidious problem in event-driven systems: you update the database *and* publish an event in the same business operation. What if the event publish fails after the database update succeeds? You have state that no one knows about. What if you publish before saving and the save fails? You have an event for something that didn't happen.

The outbox pattern solves this atomically. Instead of publishing the event directly, you write it to an `outbox` table in the same database transaction as your domain changes. A separate process polls the outbox table and publishes pending events to the message broker, deleting them after confirmation. The domain transaction is atomic (either both the domain change and the outbox row commit, or neither does). The eventual publication is handled separately and can be retried safely.

---

## Deployment and Infrastructure Patterns

### API Gateway

A single entry point for all client requests into a microservices cluster. The gateway handles routing (which service receives this request), authentication (validate the JWT here, pass claims downstream), rate limiting, SSL termination, and request aggregation (combine three service calls into one response to reduce client round trips).

The **Backend for Frontend (BFF)** pattern extends this: instead of one generic gateway, create a dedicated gateway per client type (mobile BFF, web BFF, partner BFF). Each BFF is optimized for its client's specific data shape and latency requirements.

### Service Mesh

A dedicated infrastructure layer for service-to-service communication, implemented as sidecars. A service mesh provides mutual TLS (mTLS) between all services, retries, circuit breaking, load balancing, and distributed tracing — all without any application code changes. The trade-off is operational complexity: running Istio correctly requires deep expertise.

### Strangler Fig

The pattern for migrating a legacy monolith to microservices without a risky "big bang" rewrite. Named after the strangler fig plant that grows around and eventually replaces its host tree.

A facade sits in front of the monolith. As you extract functionality into new services, you update the facade to route those requests to the new service instead of the monolith. The monolith gradually shrinks. Eventually, you remove it. At no point do you need a hard cutover.

---

## Frontend Architecture Patterns

### Micro-Frontends

The frontend equivalent of microservices: different teams own different sections of the UI end-to-end, deploying independently. Implemented via module federation (webpack), iframes, or web components. The trade-off is the same as microservices — distributed complexity for independent deployability.

### Backend for Frontend (BFF)

Each client type (web, iOS, Android, third-party) has a dedicated API backend. The mobile BFF returns compact payloads optimized for cellular bandwidth. The web BFF returns richer data for desktop displays. This avoids the "Swiss army knife API" that satisfies no client well.

---

## Data Patterns at Scale

### CQRS with Read Replicas

The write database serves consistency requirements; read replicas serve scale requirements. All writes go to the primary; reads (which are typically 10x-100x more frequent than writes) are distributed across replicas. Replication lag means reads are eventually consistent — you must design the user experience to tolerate this, or route "read your own writes" queries to the primary.

### Sharding

Partitioning data horizontally across multiple database instances. Each shard holds a subset of the data determined by a **shard key** (e.g., `user_id % num_shards`). Reads and writes for a given key always go to the same shard.

Choosing the shard key is the most critical decision. A bad key causes **hotspots** (all traffic goes to one shard). A shard key that doesn't align with query patterns forces **scatter-gather** queries (query all shards and aggregate). The ideal shard key distributes load evenly and aligns with the most common access pattern.

### Polyglot Persistence

Different services use different databases optimized for their access patterns. The user profile service uses a document store (MongoDB, DynamoDB). The recommendation engine uses a graph database (Neo4j). The analytics service uses a columnar store (ClickHouse). The session service uses Redis. Each tool chosen for the job, rather than forcing all data into a single relational database.

---

## Security Architecture Patterns

### Zero Trust Architecture

Traditional security assumed a trusted internal network — anything inside the perimeter was trusted, anything outside was not. Zero trust eliminates the perimeter: **never trust, always verify**. Every request, regardless of source, must be authenticated and authorized. Services communicate using mTLS so that both sides verify each other's identity. Access is granted with minimal privilege.

### OAuth2 / OIDC

The standard pattern for authorization and authentication in distributed systems. OAuth2 is an authorization framework (you are authorized to act on behalf of a user). OIDC extends OAuth2 with identity (you know who the user is). The API gateway validates the JWT token on every request; downstream services receive the validated claims without needing to contact the identity provider again.

---

## Observability Patterns

Observability is the ability to understand a system's internal state from its external outputs. The three pillars are **metrics** (aggregated numerical measurements over time — request rate, error rate, latency percentiles), **logs** (immutable records of discrete events — structured JSON logs with correlation IDs), and **traces** (the record of a single request's journey across multiple services — a tree of spans with timing).

The **RED method** for services: **R**ate (requests per second), **E**rrors (error rate), **D**uration (latency distribution — p50, p95, p99). These three metrics tell you whether a service is healthy.

The **USE method** for resources: **U**tilization (% busy), **S**aturation (queue length), **E**rrors (error events). These tell you whether your infrastructure is healthy.

---

## Choosing the Right Pattern: The Decision Framework

The most important architectural skill is not knowing patterns — it is knowing which pattern to apply, when, and at what cost. Here is the mental model:

Start with **Conway's Law**: before choosing an architectural pattern, understand your organization. A small team with shared ownership cannot maintain microservices. A large organization with dozens of teams cannot share a monolith. Architecture must match organizational structure.

Apply **the complexity test**: does the complexity of this pattern buy you something you actually need right now? Microservices are not inherently better than monoliths — they are better for *specific* problems (independent scaling, independent deployment, team autonomy at scale). If you don't have those problems, you pay the cost without the benefit.

Use **the failure mode test**: what happens when this component fails? What happens when this service is slow? Design for the worst case. A monolith has one failure domain. Microservices have many. EDA can buffer failures. Synchronous RPC propagates them.

Think in **evolutionary architecture**: design systems that can change. The strangler fig pattern is not just for legacy migrations — it is a mental model for all architectural change. Introduce the new alongside the old, shift traffic gradually, remove the old when confident. This requires feature flags, canary deployments, and a culture of small, frequent changes.

---

## The Meta-Principle: Architecture as Conversation

The most profound insight about software architecture is that it is not a technical discipline — it is a *communication* discipline. Architecture is how you make the structure of the system legible to the humans who must work within it and extend it. A well-chosen pattern makes the right way to add new features obvious. A poorly-chosen pattern means every extension requires fighting the structure.

The patterns covered here are not recipes — they are a vocabulary for thinking about structure. When you encounter a problem, the question is not "which pattern should I use?" but "what are the forces acting on this system, what trade-offs am I making, and which pattern best expresses the solution in a way my team will understand and sustain?"

Architecture is mastered not by memorizing patterns but by developing the intuition to see which forces are in play in any given situation — the same chunking and pattern recognition that separates a grandmaster chess player from an expert. Study real systems. Read architecture post-mortems. Build things, then rebuild them differently. The pattern vocabulary is the foundation; judgment is the discipline that only time and reflection develops.