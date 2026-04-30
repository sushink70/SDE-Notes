# Event-Driven Architecture: Complete Mastery Guide

## Table of Contents
1. [Foundational Concepts](#foundational-concepts)
2. [Core Components](#core-components)
3. [Architecture Patterns](#architecture-patterns)
4. [Implementation Strategies](#implementation-strategies)
5. [Advanced Patterns](#advanced-patterns)
6. [Trade-offs & Considerations](#trade-offs)
7. [Mental Models for Mastery](#mental-models)

---

## 1. Foundational Concepts

### What is Event-Driven Architecture?

**Event-Driven Architecture (EDA)** is a software design paradigm where the flow of the program is determined by **events** - significant changes in state or occurrences that components react to asynchronously.

**Key Mental Model:** Think of EDA like a news broadcasting system:
- Events = News happening
- Publishers = News agencies
- Subscribers = People with radios tuned to specific channels
- Event Bus = The radio waves carrying signals

### Traditional vs Event-Driven Flow

```
TRADITIONAL (SYNCHRONOUS) ARCHITECTURE:
═══════════════════════════════════════════════════

Service A ──────(1)──────> Service B
   │                          │
   │      Wait for B...       │
   │                          │
   │                      (2) Process
   │                          │
   │<──────(3)────────────────┘
   │
   │      Continue...
   ▼

Time flows linearly. A waits for B.
Tight coupling. A must know about B.


EVENT-DRIVEN (ASYNCHRONOUS) ARCHITECTURE:
═══════════════════════════════════════════════════

Service A ──(1)──> Event Bus ──(2)──> Service B
   │                   │                   │
   │                   │                   │
   │              (distribute)         (process)
   │                   │                   │
   │                   └──(2')─> Service C │
   │                                   │   │
   │              Service D <───(2'')──┘   │
   ▼                   │                   ▼
Continue             ▼                Continue
immediately      (async)

A publishes event and continues immediately.
Loose coupling. A doesn't know who listens.
Multiple services can react independently.
```

### Core Terminology (Building Blocks)

**Event**: An immutable record of something that happened
- Has a timestamp
- Contains relevant data
- Cannot be changed (immutable)
- Example: `UserRegistered`, `OrderPlaced`, `PaymentCompleted`

**Producer/Publisher**: Component that detects and publishes events
- Emits events when something significant happens
- Doesn't know who will receive the event

**Consumer/Subscriber**: Component that listens for and reacts to events
- Registers interest in specific event types
- Executes logic when matching events arrive

**Event Bus/Broker**: Middleware that routes events from producers to consumers
- Acts as intermediary
- Handles delivery guarantees
- Examples: Kafka, RabbitMQ, Redis Streams, NATS

**Channel/Topic**: Named stream where related events are published
- Logical grouping of events
- Subscribers choose which topics to listen to

---

## 2. Core Components

### Component Interaction Model

```
┌─────────────────────────────────────────────────────────────┐
│                    EVENT-DRIVEN SYSTEM                       │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐                           ┌──────────────┐ │
│  │   Producer   │                           │   Consumer   │ │
│  │   Service    │                           │   Service    │ │
│  │              │                           │              │ │
│  │  ┌────────┐  │                           │  ┌────────┐  │ │
│  │  │ Domain │  │                           │  │Handler │  │ │
│  │  │ Logic  │  │                           │  │ Logic  │  │ │
│  │  └───┬────┘  │                           │  └───▲────┘  │ │
│  │      │       │                           │      │       │ │
│  │      ▼       │                           │      │       │ │
│  │  ┌────────┐  │                           │  ┌───┴────┐  │ │
│  │  │ Event  │  │      ┌─────────────┐      │  │ Event  │  │ │
│  │  │Producer├──┼─(1)─>│  Event Bus  │─(3)─>├──┤Consumer│  │ │
│  │  └────────┘  │      │             │      │  └────────┘  │ │
│  │              │      │  (Broker)   │      │              │ │
│  └──────────────┘      │             │      └──────────────┘ │
│                        │   Topics:   │                        │
│                        │  - orders   │                        │
│                        │  - payments │      ┌──────────────┐  │
│                        │  - users    │      │   Another    │  │
│                        └─────┬───────┘      │   Consumer   │  │
│                              │              │              │  │
│                              └────(3')─────>│              │  │
│                                             └──────────────┘  │
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Event Store (Optional)                      │   │
│  │  Persists all events for replay/audit/recovery       │   │
│  │  [Event 1] [Event 2] [Event 3] ... [Event N]         │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
└───────────────────────────────────────────────────────────────┘

Legend:
(1) Publish event
(2) Store event (optional)
(3) Deliver to subscribers
```

### Event Structure

A well-designed event contains:

```
┌────────────────────────────────────────────┐
│              EVENT ANATOMY                 │
├────────────────────────────────────────────┤
│                                            │
│  Event ID:      uuid-1234-5678-abcd       │ ← Unique identifier
│  Event Type:    "OrderPlaced"              │ ← What happened
│  Timestamp:     2026-01-07T10:30:00Z       │ ← When it happened
│  Version:       1.0                        │ ← Schema version
│  Source:        "order-service"            │ ← Who published it
│  Correlation ID: trace-xyz-789            │ ← For distributed tracing
│                                            │
│  Payload (Data):                           │
│  ┌──────────────────────────────────────┐ │
│  │  order_id: "ORD-001"                 │ │
│  │  customer_id: "CUST-456"             │ │
│  │  items: [                            │ │
│  │    {product_id: "P1", qty: 2}       │ │
│  │  ]                                   │ │
│  │  total_amount: 150.00                │ │
│  │  currency: "USD"                     │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  Metadata (Optional):                      │
│  ┌──────────────────────────────────────┐ │
│  │  user_agent: "mobile-app-v2.1"       │ │
│  │  ip_address: "192.168.1.100"         │ │
│  └──────────────────────────────────────┘ │
│                                            │
└────────────────────────────────────────────┘
```

---

## 3. Architecture Patterns

### Pattern 1: Publish-Subscribe (Pub/Sub)

**Concept**: One-to-many broadcasting. Multiple subscribers receive copies of each event.

```
                    ┌──> Subscriber A (Email Service)
                    │         │
Producer ──> Topic ─┼──> Subscriber B (Analytics)
                    │         │
                    └──> Subscriber C (Notification)

Each subscriber gets its own copy of the event.
They process independently and in parallel.
```

**Use Cases:**
- Sending notifications (email, SMS, push)
- Logging and monitoring
- Analytics and reporting
- Cache invalidation

**Python Example:**

```python
# Event definition
from dataclasses import dataclass
from datetime import datetime
from typing import Any

@dataclass
class Event:
    event_id: str
    event_type: str
    timestamp: datetime
    payload: dict[str, Any]

# Simple in-memory event bus
class EventBus:
    def __init__(self):
        self.subscribers: dict[str, list[callable]] = {}
    
    def subscribe(self, event_type: str, handler: callable):
        """Register a handler for a specific event type"""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(handler)
    
    def publish(self, event: Event):
        """Publish event to all registered handlers"""
        if event.event_type in self.subscribers:
            for handler in self.subscribers[event.event_type]:
                # In production, this would be async or queued
                handler(event)

# Usage
bus = EventBus()

# Subscribe handlers
def send_email(event: Event):
    print(f"Email: Order {event.payload['order_id']} confirmed")

def update_analytics(event: Event):
    print(f"Analytics: Recording order value ${event.payload['total']}")

bus.subscribe("OrderPlaced", send_email)
bus.subscribe("OrderPlaced", update_analytics)

# Publish event
event = Event(
    event_id="evt-123",
    event_type="OrderPlaced",
    timestamp=datetime.now(),
    payload={"order_id": "ORD-001", "total": 150.00}
)
bus.publish(event)
```

### Pattern 2: Event Streaming

**Concept**: Continuous flow of events processed in real-time or near-real-time.

```
┌─────────────────────────────────────────────────────────┐
│                    EVENT STREAM                         │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Time ────────────────────────────────────────────────> │
│                                                         │
│  [E1]─[E2]────[E3]──[E4]─────[E5]──[E6]────[E7]─[E8]>  │
│   │    │       │     │        │     │       │    │     │
│   │    │       │     │        │     │       │    │     │
│  Consumer maintains offset/position in stream          │
│   │    │       │     │        │     │       │    │     │
│   └────┴───────▲─────┴────────┴─────┴───────┴────┴─    │
│                │                                        │
│         Currently reading here                         │
│                                                         │
│  Offset: 2  (has processed E1, E2)                     │
│                                                         │
└─────────────────────────────────────────────────────────┘

Features:
- Events are ordered within a partition
- Consumers track their position (offset)
- Can replay from any point
- Events are retained for configured time
```

**Use Cases:**
- Real-time analytics
- Log aggregation
- Activity tracking
- Fraud detection

**Rust Example (Conceptual Stream Processor):**

```rust
use std::collections::VecDeque;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone)]
struct StreamEvent {
    offset: u64,
    timestamp: u64,
    event_type: String,
    payload: String,
}

struct EventStream {
    events: VecDeque<StreamEvent>,
    next_offset: u64,
}

impl EventStream {
    fn new() -> Self {
        EventStream {
            events: VecDeque::new(),
            next_offset: 0,
        }
    }
    
    fn append(&mut self, event_type: String, payload: String) -> u64 {
        let timestamp = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_secs();
        
        let event = StreamEvent {
            offset: self.next_offset,
            timestamp,
            event_type,
            payload,
        };
        
        self.events.push_back(event);
        let offset = self.next_offset;
        self.next_offset += 1;
        offset
    }
    
    fn read_from(&self, offset: u64, limit: usize) -> Vec<StreamEvent> {
        self.events
            .iter()
            .skip(offset as usize)
            .take(limit)
            .cloned()
            .collect()
    }
}

// Consumer that maintains its position
struct StreamConsumer {
    current_offset: u64,
    consumer_id: String,
}

impl StreamConsumer {
    fn new(consumer_id: String) -> Self {
        StreamConsumer {
            current_offset: 0,
            consumer_id,
        }
    }
    
    fn process_batch(&mut self, stream: &EventStream, batch_size: usize) {
        let events = stream.read_from(self.current_offset, batch_size);
        
        for event in &events {
            // Process event
            println!("[{}] Processing: {:?}", self.consumer_id, event);
            self.current_offset = event.offset + 1;
        }
        
        // In production: commit offset to persistent storage
        println!("[{}] Committed offset: {}", self.consumer_id, self.current_offset);
    }
}
```

### Pattern 3: Event Sourcing

**Concept**: Store all changes as a sequence of events instead of just current state. State is derived by replaying events.

```
TRADITIONAL STORAGE (Current State Only):
═══════════════════════════════════════════════════

Database Table: Users
┌─────────┬──────────┬─────────┬─────────────┐
│ user_id │   name   │ balance │   status    │
├─────────┼──────────┼─────────┼─────────────┤
│   123   │  "Alice" │  $500   │  "active"   │
└─────────┴──────────┴─────────┴─────────────┘

Problem: Lost history! How did we get here?


EVENT SOURCING (Full History):
═══════════════════════════════════════════════════

Event Store: All events in order
┌────────┬────────────────────┬─────────────────────────┐
│ Seq#   │ Event Type         │ Payload                 │
├────────┼────────────────────┼─────────────────────────┤
│   1    │ UserCreated        │ {id:123, name:"Alice"}  │
│   2    │ DepositMade        │ {amount: 500}           │
│   3    │ EmailUpdated       │ {email: "a@example"}    │
│   4    │ WithdrawalMade     │ {amount: 100}           │
│   5    │ DepositMade        │ {amount: 100}           │
└────────┴────────────────────┴─────────────────────────┘
                    │
                    │  Replay events ──────┐
                    │                      │
                    ▼                      ▼
         ┌─────────────────┐    ┌──────────────────┐
         │ Current State   │    │  State at Seq#2  │
         │ balance: $500   │    │  balance: $500   │
         └─────────────────┘    └──────────────────┘
         
Benefits:
- Complete audit trail
- Time travel (view state at any point)
- Debugging (replay events to reproduce bugs)
- New projections (create new views from existing events)
```

**Go Example:**

```go
package main

import (
    "fmt"
    "time"
)

// Event types
type EventType string

const (
    UserCreated      EventType = "UserCreated"
    DepositMade      EventType = "DepositMade"
    WithdrawalMade   EventType = "WithdrawalMade"
)

// Event structure
type Event struct {
    ID        string
    Type      EventType
    Timestamp time.Time
    UserID    string
    Data      map[string]interface{}
}

// Aggregate (current state)
type UserAccount struct {
    ID      string
    Name    string
    Balance float64
    Version int  // Number of events applied
}

// Event Store
type EventStore struct {
    events []Event
}

func (es *EventStore) Append(event Event) {
    es.events = append(es.events, event)
}

func (es *EventStore) GetEvents(userID string) []Event {
    var userEvents []Event
    for _, event := range es.events {
        if event.UserID == userID {
            userEvents = append(userEvents, event)
        }
    }
    return userEvents
}

// Rebuild state from events
func RebuildUserAccount(events []Event) *UserAccount {
    account := &UserAccount{}
    
    for _, event := range events {
        switch event.Type {
        case UserCreated:
            account.ID = event.UserID
            account.Name = event.Data["name"].(string)
            account.Balance = 0
            
        case DepositMade:
            account.Balance += event.Data["amount"].(float64)
            
        case WithdrawalMade:
            account.Balance -= event.Data["amount"].(float64)
        }
        account.Version++
    }
    
    return account
}

func main() {
    store := &EventStore{}
    
    // Simulate events over time
    store.Append(Event{
        ID:        "evt-1",
        Type:      UserCreated,
        Timestamp: time.Now(),
        UserID:    "user-123",
        Data:      map[string]interface{}{"name": "Alice"},
    })
    
    store.Append(Event{
        ID:        "evt-2",
        Type:      DepositMade,
        Timestamp: time.Now(),
        UserID:    "user-123",
        Data:      map[string]interface{}{"amount": 500.0},
    })
    
    store.Append(Event{
        ID:        "evt-3",
        Type:      WithdrawalMade,
        Timestamp: time.Now(),
        UserID:    "user-123",
        Data:      map[string]interface{}{"amount": 100.0},
    })
    
    // Rebuild current state
    events := store.GetEvents("user-123")
    account := RebuildUserAccount(events)
    
    fmt.Printf("User: %s, Balance: $%.2f, Version: %d\n", 
        account.Name, account.Balance, account.Version)
    // Output: User: Alice, Balance: $400.00, Version: 3
}
```

### Pattern 4: CQRS (Command Query Responsibility Segregation)

**Concept**: Separate read and write operations into different models optimized for their specific purpose.

```
┌─────────────────────────────────────────────────────────────┐
│                    TRADITIONAL (Combined)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Commands ────┐                                             │
│   (writes)     │                                             │
│                ├──> Single Model ──> Single Database         │
│   Queries      │    (complex)         (normalized)           │
│   (reads)  ────┘                                             │
│                                                               │
│   Problems: Write and read needs conflict                    │
│             Complex model trying to serve both               │
└───────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                  CQRS (Separated)                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│   Commands ──> Write Model ──> Write DB                      │
│   (writes)     (domain logic)  (normalized)                  │
│                     │                                        │
│                     │ Events                                 │
│                     ▼                                        │
│                Event Bus                                     │
│                     │                                        │
│                     │ Update projections                     │
│                     ▼                                        │
│   Queries ──> Read Model ──> Read DB                        │
│   (reads)      (simple DTOs)  (denormalized,                │
│                               optimized for queries)          │
│                                                               │
│   Benefits: Each side optimized independently                │
│             Can scale reads and writes separately            │
└───────────────────────────────────────────────────────────────┘
```

**Mental Model:**
- **Write side**: Like a legal contract - careful validation, business rules
- **Read side**: Like a cached summary - fast, pre-computed, easy to query

---

## 4. Implementation Strategies

### Delivery Guarantees

Understanding message delivery semantics is crucial:

```
┌──────────────────────────────────────────────────────────┐
│           MESSAGE DELIVERY GUARANTEES                     │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  At-Most-Once (Fire and Forget)                          │
│  ────────────────────────────────────                    │
│  Producer ──[msg]──> Network ─X→ Consumer               │
│                                                           │
│  Message sent once, may be lost                          │
│  No retry, no confirmation                               │
│  Fastest, least reliable                                 │
│  Use: Metrics, logs where loss is acceptable            │
│                                                           │
│  ─────────────────────────────────────────────────       │
│                                                           │
│  At-Least-Once (Retry until acknowledged)                │
│  ────────────────────────────────────────                │
│  Producer ──[msg]──> Broker ──> Consumer                │
│      ▲         │                    │                     │
│      │         │                    │ Process             │
│      │         │                    ▼                     │
│      │         │                  [ACK]                   │
│      │         └────────────────────┘                     │
│      │                                                    │
│      └── Retry if no ACK (timeout)                       │
│                                                           │
│  Message delivered one or more times                     │
│  Guarantees delivery, may duplicate                      │
│  Consumer must be idempotent!                            │
│  Use: Most common choice                                 │
│                                                           │
│  ─────────────────────────────────────────────────       │
│                                                           │
│  Exactly-Once (Delivered precisely once)                 │
│  ────────────────────────────────────                    │
│  Producer ──[msg]──> Broker ──> Consumer                │
│      │         │                    │                     │
│      │    [Dedup Check]             │                     │
│      │         │                    │                     │
│      │    Store + ACK               Process (once)        │
│                                                           │
│  Message delivered exactly once                          │
│  Hardest to implement, most expensive                    │
│  Requires distributed transactions or deduplication      │
│  Use: Financial transactions, critical operations        │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

### Idempotency Pattern

**Idempotent**: An operation that produces the same result no matter how many times it's executed.

```python
# Non-idempotent (BAD)
def process_payment(event):
    account.balance -= event.amount  # Problem: runs twice = double charge!

# Idempotent (GOOD)
processed_events = set()

def process_payment(event):
    if event.id in processed_events:
        return  # Already processed, skip
    
    account.balance -= event.amount
    processed_events.add(event.id)  # Track processed
```

**Rust Implementation with Persistent Tracking:**

```rust
use std::collections::HashSet;

struct PaymentProcessor {
    processed_event_ids: HashSet<String>,
}

impl PaymentProcessor {
    fn new() -> Self {
        PaymentProcessor {
            processed_event_ids: HashSet::new(),
        }
    }
    
    fn process_payment(&mut self, event_id: &str, amount: f64) -> Result<(), String> {
        // Check if already processed
        if self.processed_event_ids.contains(event_id) {
            println!("Event {} already processed, skipping", event_id);
            return Ok(());
        }
        
        // Process payment
        println!("Processing payment of ${}", amount);
        
        // Mark as processed (in production: persist to database)
        self.processed_event_ids.insert(event_id.to_string());
        
        Ok(())
    }
}

fn main() {
    let mut processor = PaymentProcessor::new();
    
    // First attempt
    processor.process_payment("evt-001", 100.0).unwrap();
    
    // Duplicate delivery (simulating retry)
    processor.process_payment("evt-001", 100.0).unwrap();
    // Output: "Event evt-001 already processed, skipping"
}
```

### Error Handling Strategies

```
┌────────────────────────────────────────────────────────┐
│              ERROR HANDLING PATTERNS                    │
├────────────────────────────────────────────────────────┤
│                                                         │
│  1. Retry with Exponential Backoff                     │
│  ────────────────────────────────                      │
│  Attempt 1:  Process ──X→ [Fail]                      │
│                           Wait 1s                      │
│  Attempt 2:  Process ──X→ [Fail]                      │
│                           Wait 2s                      │
│  Attempt 3:  Process ──X→ [Fail]                      │
│                           Wait 4s                      │
│  Attempt 4:  Process ──X→ [Fail]                      │
│                           Wait 8s                      │
│  Attempt 5:  Process ──✓→ [Success]                   │
│                                                         │
│  ─────────────────────────────────────────────         │
│                                                         │
│  2. Dead Letter Queue (DLQ)                            │
│  ────────────────────────────────                      │
│  Event ──> Consumer ──X→ [Fail]                       │
│                │                                        │
│                │  After N retries                      │
│                ▼                                        │
│           [Dead Letter Queue]                          │
│                │                                        │
│                ▼                                        │
│         Manual inspection                              │
│         Fix and replay                                 │
│                                                         │
│  ─────────────────────────────────────────────         │
│                                                         │
│  3. Circuit Breaker                                    │
│  ────────────────────────────────                      │
│  [CLOSED] ──> Normal operation                         │
│      │           ▲                                      │
│      │ Failures  │ Success rate                        │
│      │ exceed    │ restored                            │
│      │ threshold │                                      │
│      ▼           │                                      │
│  [OPEN] ──────────> [HALF-OPEN]                       │
│   Reject calls      Test with                         │
│   immediately       limited traffic                    │
│                                                         │
└────────────────────────────────────────────────────────┘
```

**Go Circuit Breaker Example:**

```go
package main

import (
    "errors"
    "fmt"
    "time"
)

type CircuitState int

const (
    Closed CircuitState = iota
    Open
    HalfOpen
)

type CircuitBreaker struct {
    maxFailures     int
    resetTimeout    time.Duration
    failureCount    int
    lastFailureTime time.Time
    state           CircuitState
}

func NewCircuitBreaker(maxFailures int, resetTimeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        maxFailures:  maxFailures,
        resetTimeout: resetTimeout,
        state:        Closed,
    }
}

func (cb *CircuitBreaker) Execute(operation func() error) error {
    // Check if we should transition from Open to HalfOpen
    if cb.state == Open {
        if time.Since(cb.lastFailureTime) > cb.resetTimeout {
            cb.state = HalfOpen
            cb.failureCount = 0
            fmt.Println("Circuit: OPEN -> HALF-OPEN")
        } else {
            return errors.New("circuit breaker is OPEN")
        }
    }
    
    // Execute operation
    err := operation()
    
    if err != nil {
        cb.failureCount++
        cb.lastFailureTime = time.Now()
        
        if cb.failureCount >= cb.maxFailures {
            cb.state = Open
            fmt.Printf("Circuit: CLOSED/HALF-OPEN -> OPEN (failures: %d)\n", cb.failureCount)
        }
        return err
    }
    
    // Success
    if cb.state == HalfOpen {
        cb.state = Closed
        cb.failureCount = 0
        fmt.Println("Circuit: HALF-OPEN -> CLOSED")
    }
    
    return nil
}
```

---

## 5. Advanced Patterns

### Saga Pattern (Distributed Transactions)

**Problem**: How to maintain data consistency across multiple services without distributed transactions?

**Solution**: Saga - a sequence of local transactions, each publishing an event. If one fails, compensating transactions undo previous changes.

```
┌─────────────────────────────────────────────────────────────┐
│                    CHOREOGRAPHY SAGA                         │
│               (Event-driven coordination)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Order     Payment    Inventory    Shipping                  │
│  Service   Service    Service      Service                   │
│    │         │           │            │                       │
│    │  Create │           │            │                       │
│    │──Order  │           │            │                       │
│    │         │           │            │                       │
│    ├──[OrderCreated]──>  │            │                       │
│    │         │           │            │                       │
│    │         ├─Charge    │            │                       │
│    │         │  Card     │            │                       │
│    │         │           │            │                       │
│    │         ├───[PaymentCompleted]─>│                       │
│    │         │           │            │                       │
│    │         │           ├─Reserve    │                       │
│    │         │           │  Stock     │                       │
│    │         │           │            │                       │
│    │         │           ├────[InventoryReserved]──>         │
│    │         │           │            │                       │
│    │         │           │            ├─Ship Order           │
│    │         │           │            │                       │
│    │         │           │            ├──[OrderShipped]──>   │
│    ▼         ▼           ▼            ▼                       │
│  Done       Done        Done         Done                    │
│                                                               │
│  ───────────────────────────────────────────────────         │
│                                                               │
│  FAILURE CASE (with compensation):                           │
│                                                               │
│    │         │           │            │                       │
│    ├──[OrderCreated]──>  │            │                       │
│    │         │           │            │                       │
│    │         ├─Charge    │            │                       │
│    │         │  Card     │            │                       │
│    │         │           │            │                       │
│    │         ├───[PaymentCompleted]─>│                       │
│    │         │           │            │                       │
│    │         │           ├─Reserve    │                       │
│    │         │           │  Stock     │                       │
│    │         │           │            │                       │
│    │         │           X─[Out of Stock]──[FAIL]            │
│    │         │           │            │                       │
│    │         │           ├───[InventoryFailed]──>            │
│    │         │           │            │                       │
│    │<────[OrderFailed]───┤            │                       │
│    │         │           │            │                       │
│    │         ├<──[RefundPayment]──────┤                      │
│    │         │           │            │                       │
│    │         ├─Refund    │            │                       │
│    │         │  Card     │            │                       │
│    │         │           │            │                       │
│    │<────[OrderCancelled]─────────────┘                      │
│    ▼         ▼           ▼            ▼                       │
│ Rolled     Rolled     Failed       Not Started               │
│  Back       Back                                             │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Python Saga Orchestrator:**

```python
from enum import Enum
from typing import Callable, List
from dataclasses import dataclass

class SagaStepStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    COMPENSATED = "compensated"

@dataclass
class SagaStep:
    name: str
    action: Callable
    compensation: Callable
    status: SagaStepStatus = SagaStepStatus.PENDING

class SagaOrchestrator:
    def __init__(self):
        self.steps: List[SagaStep] = []
        self.completed_steps: List[SagaStep] = []
    
    def add_step(self, name: str, action: Callable, compensation: Callable):
        """Add a step to the saga"""
        step = SagaStep(name, action, compensation)
        self.steps.append(step)
    
    def execute(self) -> bool:
        """Execute all steps, compensate on failure"""
        try:
            for step in self.steps:
                print(f"Executing: {step.name}")
                step.action()
                step.status = SagaStepStatus.COMPLETED
                self.completed_steps.append(step)
            
            print("✓ Saga completed successfully")
            return True
            
        except Exception as e:
            print(f"✗ Saga failed at {step.name}: {e}")
            self._compensate()
            return False
    
    def _compensate(self):
        """Roll back completed steps in reverse order"""
        print("\nStarting compensation...")
        
        for step in reversed(self.completed_steps):
            try:
                print(f"  Compensating: {step.name}")
                step.compensation()
                step.status = SagaStepStatus.COMPENSATED
            except Exception as e:
                print(f"  ✗ Compensation failed for {step.name}: {e}")

# Example usage
def create_order():
    print("  → Order created")
    # Could fail here

def cancel_order():
    print("  ← Order cancelled")

def charge_payment():
    print("  → Payment charged")
    # Could fail here

def refund_payment():
    print("  ← Payment refunded")

def reserve_inventory():
    print("  → Inventory reserved")
    raise Exception("Out of stock!")  # Simulate failure

def release_inventory():
    print("  ← Inventory released")

# Run saga
saga = SagaOrchestrator()
saga.add_step("Create Order", create_order, cancel_order)
saga.add_step("Charge Payment", charge_payment, refund_payment)
saga.add_step("Reserve Inventory", reserve_inventory, release_inventory)

saga.execute()
```

### Event Replay and Time Travel

**Concept**: Reprocess historical events to rebuild state or create new projections.

```
┌──────────────────────────────────────────────────────────┐
│                  EVENT REPLAY SCENARIOS                   │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  Scenario 1: Fix Bug in Event Handler                    │
│  ──────────────────────────────────                      │
│                                                           │
│  Event Stream:  [E1][E2][E3][E4][E5][E6][E7]            │
│                                 ▲                         │
│  Bug discovered here ───────────┘                        │
│  Handler had wrong logic for E4-E7                       │
│                                                           │
│  Solution:                                               │
│  1. Deploy fixed handler                                 │
│  2. Replay from E4 → rebuilds correct state              │
│                                                           │
│  ─────────────────────────────────────────────────       │
│                                                           │
│  Scenario 2: Create New Projection                       │
│  ──────────────────────────────────                      │
│                                                           │
│  Existing: Customer balance view                         │
│  New need: Customer purchase history by category         │
│                                                           │
│  Solution:                                               │
│  1. Create new handler/projection                        │
│  2. Replay ALL events from beginning                     │
│  3. New projection populated from history                │
│                                                           │
│  ─────────────────────────────────────────────────       │
│                                                           │
│  Scenario 3: Audit and Debugging                         │
│  ──────────────────────────────────                      │
│                                                           │
│  Question: How did account end up negative?              │
│                                                           │
│  Solution:                                               │
│  1. Replay events for that account                       │
│  2. Inspect state after each event                       │
│  3. Find anomaly in event sequence                       │
│                                                           │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Trade-offs & Considerations

### When to Use EDA

```
┌─────────────────────────────────────────────────────────┐
│                DECISION FRAMEWORK                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ✓ USE EVENT-DRIVEN WHEN:                               │
│  ──────────────────────────                             │
│  • Need loose coupling between services                 │
│  • Multiple systems need to react to same event         │
│  • Scalability is critical                              │
│  • Need audit trail / event history                     │
│  • Async processing acceptable                          │
│  • Building microservices                               │
│  • Real-time data processing needed                     │
│                                                          │
│  ✗ AVOID EVENT-DRIVEN WHEN:                             │
│  ──────────────────────────                             │
│  • Need immediate consistency                           │
│  • Simple CRUD operations only                          │
│  • Tight coordination required between steps            │
│  • Team lacks distributed systems experience            │
│  • Debugging complexity unacceptable                    │
│  • Monolithic architecture sufficient                   │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Complexity Comparison

```
Aspect              Traditional    Event-Driven
─────────────────── ────────────── ──────────────────
Coupling            Tight          Loose
Scalability         Moderate       High
Debugging           Easier         Harder (distributed)
Consistency         Strong         Eventual
Development Speed   Fast (simple)  Slower (complexity)
Operational Burden  Lower          Higher (monitoring)
Failure Handling    Clear          Complex (retries, DLQ)
Data Flow           Synchronous    Asynchronous
Testing             Unit tests     Integration heavy
```

### Common Pitfalls

**1. Event Versioning**
```
Problem: Event schema changes break old consumers

Version 1:  {"user_id": 123, "name": "Alice"}
Version 2:  {"user_id": 123, "first_name": "Alice", "last_name": "Smith"}

Solution:
- Include version field in events
- Maintain backward compatibility
- Use schema evolution strategies
```

**2. Event Ordering**
```
Problem: Out-of-order events cause wrong state

Events: [Created] [Updated] [Deleted]
Arrive:  [Updated] [Created] [Deleted]  ← Wrong order!

Solutions:
- Use sequence numbers/timestamps
- Partition by key (same key → same partition → ordered)
- Use event correlation IDs
```

**3. Duplicate Events**
```
Problem: Network retry causes duplicate processing

Event "PaymentCharged" arrives twice → double charge!

Solution:
- Make handlers idempotent
- Track processed event IDs
- Use exactly-once semantics if available
```

---

## 7. Mental Models for Mastery

### The Newspaper Analogy

Think of EDA like a newspaper system:

- **Publishers** = Journalists writing articles
- **Events** = News articles
- **Topics** = Newspaper sections (Sports, Business, etc.)
- **Subscribers** = Readers who choose sections they care about
- **Event Store** = Newspaper archive

### The River Metaphor

```
   Events flow like water in a river:
   
   ╭────────────────────────────────────╮
   │  Source → Stream → Delta → Ocean  │
   ╰────────────────────────────────────╯
   
   • Source: Where events originate
   • Stream: Events flowing continuously
   • Delta: Fan-out to multiple consumers
   • Ocean: Final destinations (databases, caches)
   
   Like a river:
   - Water (events) keeps flowing
   - Can't push water backward (immutable)
   - Multiple branches (topics)
   - Predictable flow (ordered within partition)
```

### Cognitive Strategies for Mastery

**1. Think Async-First**
- Train your mind to see operations as independent
- Ask: "What can happen simultaneously?"
- Draw temporal diagrams showing parallel execution

**2. Event Storming Practice**
- Take a business process
- Break it into events (past tense verbs)
- Identify commands (what triggers events)
- Map out actors and aggregates

**3. Failure Scenario Training**
- For each design, ask: "What if this fails?"
- Design compensation logic upfront
- Practice reasoning about partial failures

**4. State Machine Thinking**
- Model aggregates as state machines
- Events = transitions between states
- Impossible states = invalid transitions

**Example State Machine:**
```
Order States:

  Created ──[PaymentCompleted]──> Paid
     │                             │
     │                             │
  [Cancelled]              [InventoryReserved]
     │                             │
     ▼                             ▼
  Cancelled                    Shipped ──[Delivered]──> Completed
                                  │
                             [ReturnRequested]
                                  │
                                  ▼
                              Returned
```

### Deliberate Practice Exercises

**Exercise 1: Event Design Kata**
- Pick a domain (e.g., library system)
- Design all events without writing code
- Review: Are events past tense? Immutable? Complete?

**Exercise 2: Saga Choreography**
- Design a distributed transaction
- Map out failure scenarios
- Implement compensation logic

**Exercise 3: Performance Analysis**
- Calculate theoretical throughput
- Identify bottlenecks
- Design scaling strategies

---

## 8. Real-World Architecture Example

### E-Commerce Platform

```
┌────────────────────────────────────────────────────────────────────┐
│                    E-COMMERCE EVENT-DRIVEN SYSTEM                   │
├────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────┐                                                   │
│  │   Web UI    │                                                   │
│  └──────┬──────┘                                                   │
│         │ HTTP                                                     │
│         ▼                                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                    API Gateway                               │  │
│  └──────────────────────┬──────────────────────────────────────┘  │
│                         │                                          │
│                         ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                   Event Bus (Kafka)                          │  │
│  │                                                               │  │
│  │  Topics:                                                     │  │
│  │  • orders          • payments       • inventory              │  │
│  │  • users           • shipping       • notifications          │  │
│  └───────┬────────────┬────────────┬──────────────┬────────────┘  │
│          │            │            │              │                │
│          ▼            ▼            ▼              ▼                │
│  ┌────────────┐ ┌───────────┐ ┌──────────┐ ┌─────────────┐       │
│  │   Order    │ │  Payment  │ │Inventory │ │ Notification│       │
│  │  Service   │ │  Service  │ │ Service  │ │  Service    │       │
│  │            │ │           │ │          │ │             │       │
│  │ ┌────────┐ │ │ ┌───────┐ │ │┌───────┐ │ │ ┌─────────┐ │       │
│  │ │ Write  │ │ │ │Process│ │ ││Reserve│ │ │ │  Email  │ │       │
│  │ │ Model  │ │ │ │Payment│ │ ││ Stock │ │ │ │   SMS   │ │       │
│  │ └───┬────┘ │ │ └───┬───┘ │ │└───┬───┘ │ │ │  Push   │ │       │
│  │     │      │ │     │     │ │    │     │ │ └─────────┘ │       │
│  │     ▼      │ │     ▼     │ │    ▼     │ │             │       │
│  │  Postgres  │ │  Postgres │ │ Postgres │ │             │       │
│  └────────────┘ └───────────┘ └──────────┘ └─────────────┘       │
│          │                                                         │
│          │ Events                                                 │
│          ▼                                                         │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │              Event Store (Append-only log)                   │  │
│  │  [All events for audit/replay]                               │  │
│  └──────────────────────┬──────────────────────────────────────┘  │
│                         │                                          │
│                         │ Stream processing                        │
│                         ▼                                          │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │                Read Models (CQRS)                            │  │
│  │                                                               │  │
│  │  • Order History     (MongoDB - Document)                    │  │
│  │  • Product Catalog   (Elasticsearch - Search)                │  │
│  │  • Analytics         (Redshift - Data Warehouse)             │  │
│  │  • Cache             (Redis - Key-Value)                     │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

Event Flow Example:

1. User places order → OrderService publishes "OrderCreated"
2. PaymentService listens → charges card → publishes "PaymentCompleted"
3. InventoryService listens → reserves items → publishes "InventoryReserved"
4. NotificationService listens → sends confirmation email
5. All events stored in Event Store for audit
6. Read models updated asynchronously for fast queries
```

---

## Summary: The Path to Mastery

### Core Principles to Internalize

1. **Events are Facts**: Immutable records of what happened
2. **Loose Coupling**: Publishers don't know consumers
3. **Eventual Consistency**: Accept that distributed systems aren't instantly consistent
4. **Idempotency is Key**: Design for retries and duplicates
5. **Design for Failure**: Assume components will fail, build resilience
6. **Separation of Concerns**: Use CQRS to optimize reads and writes
7. **Observability**: Implement logging, monitoring, and tracing from day one
8. **Evolve Your Events**: Plan for versioning and schema changes
9. **Practice Makes Perfect**: Regularly design, implement, and review EDA systems
By deeply understanding these concepts and practicing their application, you'll be well on your way to mastering event-driven architecture and building robust, scalable systems.

