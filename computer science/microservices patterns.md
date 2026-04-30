# Comprehensive Guide to Microservices Patterns

I'll guide you through the complete landscape of microservices architecture—from foundational concepts to advanced patterns. This is a substantial domain, so let's build your mental model systematically.

---

## Part 1: Foundation - What Are Microservices?

### Core Concept
**Microservices Architecture** is a software design approach where an application is composed of small, independent services that communicate over well-defined APIs. Each service is:
- **Autonomous** (independently deployable)
- **Focused** (single responsibility)
- **Loosely coupled** (minimal dependencies)
- **Technology agnostic** (can use different tech stacks)

### Monolith vs Microservices

```
MONOLITHIC ARCHITECTURE
┌─────────────────────────────────────┐
│     Single Application Unit         │
│                                     │
│  ┌──────────┐  ┌──────────┐       │
│  │   User   │  │ Payment  │       │
│  │ Service  │  │ Service  │       │
│  └──────────┘  └──────────┘       │
│  ┌──────────┐  ┌──────────┐       │
│  │ Inventory│  │  Order   │       │
│  │ Service  │  │ Service  │       │
│  └──────────┘  └──────────┘       │
│                                     │
│      Shared Database                │
│  ┌───────────────────────────┐     │
│  │     Single Database       │     │
│  └───────────────────────────┘     │
└─────────────────────────────────────┘

MICROSERVICES ARCHITECTURE
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   User       │  │   Payment    │  │  Inventory   │
│   Service    │  │   Service    │  │   Service    │
│              │  │              │  │              │
│   ┌─────┐   │  │   ┌─────┐   │  │   ┌─────┐   │
│   │ DB  │   │  │   │ DB  │   │  │   │ DB  │   │
│   └─────┘   │  │   └─────┘   │  │   └─────┘   │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │
       └─────────────────┴─────────────────┘
              API Gateway / Message Bus
```

---

## Part 2: Decomposition Patterns

### Pattern 1: Decompose by Business Capability

**Concept**: Organize services around business functions (what the business *does*).

**Mental Model**: Think of your organization's departments—each handles a distinct business capability.

```
E-COMMERCE BUSINESS CAPABILITIES

┌─────────────────────────────────────────────┐
│           E-Commerce Platform               │
└─────────────────────────────────────────────┘
         │
         ├─── Customer Management
         │    ├─── Registration
         │    ├─── Profile
         │    └─── Authentication
         │
         ├─── Product Catalog
         │    ├─── Browsing
         │    ├─── Search
         │    └─── Recommendations
         │
         ├─── Order Management
         │    ├─── Cart
         │    ├─── Checkout
         │    └─── Order Tracking
         │
         ├─── Payment Processing
         │    ├─── Payment Gateway
         │    ├─── Refunds
         │    └─── Billing
         │
         └─── Inventory Management
              ├─── Stock Control
              ├─── Warehousing
              └─── Suppliers
```

**Implementation Example (Rust)**:

```rust
// Customer Service - Owns customer domain
pub struct CustomerService {
    db: Database,
}

impl CustomerService {
    pub async fn register_customer(&self, data: CustomerData) -> Result<CustomerId> {
        // Business logic for customer registration
        let customer = Customer::new(data);
        self.db.save(customer).await
    }
    
    pub async fn get_profile(&self, id: CustomerId) -> Result<CustomerProfile> {
        self.db.find_customer(id).await
    }
}

// Order Service - Owns order domain
pub struct OrderService {
    db: Database,
    customer_client: CustomerServiceClient, // External service call
}

impl OrderService {
    pub async fn create_order(&self, customer_id: CustomerId, items: Vec<OrderItem>) -> Result<OrderId> {
        // Verify customer exists (cross-service call)
        self.customer_client.verify_customer(customer_id).await?;
        
        let order = Order::new(customer_id, items);
        self.db.save(order).await
    }
}
```

---

### Pattern 2: Decompose by Subdomain (Domain-Driven Design)

**Concept**: Use DDD (Domain-Driven Design) to identify **bounded contexts**—cohesive areas of the business domain.

**Key Terms**:
- **Domain**: The entire business problem space
- **Subdomain**: A smaller, focused area within the domain
- **Bounded Context**: A boundary within which a particular model applies
- **Aggregate**: A cluster of domain objects treated as a single unit

```
DOMAIN-DRIVEN DESIGN DECOMPOSITION

┌───────────────────────────────────────────────────┐
│              E-Commerce Domain                     │
└───────────────────────────────────────────────────┘

Core Subdomain (Critical, unique)
┌────────────────────┐
│  Order Processing  │ ← High value, competitive advantage
│  - Order aggregate │
│  - Payment logic   │
└────────────────────┘

Supporting Subdomain (Important, not differentiating)
┌────────────────────┐
│  Inventory Mgmt    │ ← Necessary but not unique
│  - Stock tracking  │
└────────────────────┘

Generic Subdomain (Common, can be outsourced)
┌────────────────────┐
│  Notifications     │ ← Email/SMS (use 3rd party)
│  Authentication    │ ← OAuth (use Auth0, etc.)
└────────────────────┘
```

**Python Example**:

```python
# Order Service - Bounded Context for Orders
class Order:
    """Aggregate root for Order bounded context"""
    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items: List[OrderItem] = []
        self.status = OrderStatus.PENDING
        
    def add_item(self, product_id: str, quantity: int):
        """Business rule: Can only add items when pending"""
        if self.status != OrderStatus.PENDING:
            raise InvalidOrderState("Cannot modify non-pending order")
        self.items.append(OrderItem(product_id, quantity))
    
    def submit(self):
        """Business rule: Must have items to submit"""
        if not self.items:
            raise EmptyOrderError("Order must have items")
        self.status = OrderStatus.SUBMITTED

# Inventory Service - Separate Bounded Context
class StockItem:
    """Aggregate root for Inventory bounded context"""
    def __init__(self, product_id: str, quantity: int):
        self.product_id = product_id
        self.quantity = quantity
    
    def reserve(self, amount: int):
        """Business rule: Cannot reserve more than available"""
        if amount > self.quantity:
            raise InsufficientStockError()
        self.quantity -= amount
```

---

## Part 3: Communication Patterns

### Pattern 3: API Gateway

**Concept**: A single entry point that routes requests to appropriate microservices. Think of it as a **receptionist** directing visitors to different departments.

```
API GATEWAY PATTERN

Client (Mobile/Web)
       │
       ▼
┌─────────────────┐
│   API Gateway   │ ← Single entry point
│                 │ ← Routing, authentication, rate limiting
└─────────────────┘
       │
       ├──────┬──────┬──────┬──────┐
       ▼      ▼      ▼      ▼      ▼
    ┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────┐
    │User│ │Prod│ │Ordr│ │Pay │ │Ship│
    │Svc │ │Svc │ │Svc │ │Svc │ │Svc │
    └────┘ └────┘ └────┘ └────┘ └────┘
```

**Go Implementation**:

```go
// API Gateway in Go
type APIGateway struct {
    userService    *UserServiceClient
    orderService   *OrderServiceClient
    productService *ProductServiceClient
}

func (gw *APIGateway) HandleGetOrderDetails(w http.ResponseWriter, r *http.Request) {
    orderID := r.URL.Query().Get("orderId")
    
    // Orchestrate multiple service calls
    var wg sync.WaitGroup
    var order Order
    var user User
    var products []Product
    
    // Parallel calls for better performance
    wg.Add(3)
    
    go func() {
        defer wg.Done()
        order, _ = gw.orderService.GetOrder(orderID)
    }()
    
    go func() {
        defer wg.Done()
        user, _ = gw.userService.GetUser(order.UserID)
    }()
    
    go func() {
        defer wg.Done()
        products, _ = gw.productService.GetProducts(order.ProductIDs)
    }()
    
    wg.Wait()
    
    // Aggregate response
    response := OrderDetailsResponse{
        Order:    order,
        Customer: user,
        Products: products,
    }
    
    json.NewEncoder(w).Encode(response)
}
```

---

### Pattern 4: Service Mesh

**Concept**: Infrastructure layer that handles service-to-service communication, providing features like load balancing, service discovery, encryption, and observability.

```
SERVICE MESH ARCHITECTURE

┌──────────────────────────────────────────────┐
│              Control Plane                   │
│  (Manages proxies, policies, certificates)   │
└──────────────────────────────────────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
┌───────▼─────┐ ┌──▼────────┐ ┌▼──────────┐
│   Service A │ │ Service B │ │ Service C │
│   ┌─────┐   │ │  ┌─────┐  │ │  ┌─────┐  │
│   │ App │   │ │  │ App │  │ │  │ App │  │
│   └──┬──┘   │ │  └──┬──┘  │ │  └──┬──┘  │
│      │      │ │     │     │ │     │     │
│   ┌──▼──┐   │ │  ┌──▼──┐  │ │  ┌──▼──┐  │
│   │Proxy│◄──┼─┼─►│Proxy│◄─┼─┼─►│Proxy│  │
│   │(Envoy)  │ │  │(Envoy) │ │  │(Envoy) │
│   └─────┘   │ │  └─────┘  │ │  └─────┘  │
└─────────────┘ └───────────┘ └───────────┘

Data Plane (Proxies handle actual traffic)
```

---

### Pattern 5: Synchronous Communication (REST/gRPC)

**REST Decision Flow**:

```
Should I use REST or gRPC?
           │
           ▼
    [Need human-readable?]
           │
     Yes ──┴── No
     │          │
   [REST]    [High performance needed?]
                │
          Yes ──┴── No
          │          │
        [gRPC]    [Either]
```

**Rust gRPC Example**:

```rust
// Using tonic for gRPC in Rust
use tonic::{Request, Response, Status};

// Proto definition would be in .proto file:
// service OrderService {
//   rpc CreateOrder(CreateOrderRequest) returns (CreateOrderResponse);
// }

pub struct OrderServiceImpl {
    db: Database,
}

#[tonic::async_trait]
impl OrderService for OrderServiceImpl {
    async fn create_order(
        &self,
        request: Request<CreateOrderRequest>,
    ) -> Result<Response<CreateOrderResponse>, Status> {
        let req = request.into_inner();
        
        // Validate request
        if req.items.is_empty() {
            return Err(Status::invalid_argument("Order must have items"));
        }
        
        // Process order
        let order = Order {
            id: generate_id(),
            customer_id: req.customer_id,
            items: req.items,
            status: OrderStatus::Created,
        };
        
        self.db.save(order.clone()).await
            .map_err(|e| Status::internal(e.to_string()))?;
        
        Ok(Response::new(CreateOrderResponse {
            order_id: order.id,
            status: "created".to_string(),
        }))
    }
}
```

---

### Pattern 6: Asynchronous Communication (Message Queue/Event-Driven)

**Concept**: Services communicate through messages, not direct calls. Think of it as leaving a note rather than making a phone call—the recipient processes it when ready.

**Key Terms**:
- **Producer**: Service that sends messages
- **Consumer**: Service that receives/processes messages
- **Queue**: FIFO buffer holding messages (point-to-point)
- **Topic**: Broadcast channel (publish-subscribe)
- **Event**: A notification that something happened (past tense: "OrderCreated")

```
EVENT-DRIVEN ARCHITECTURE

Order Service                Message Broker              Other Services
     │                            │                           │
     │  1. Create Order          │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │  2. Publish "OrderCreated" │                           │
     ├───────────────────────────►│                           │
     │                            │                           │
     │                            │  3. Notify subscribers    │
     │                            ├──────────────────────────►│
     │                            │         │                 │
     │                            │         ├─► Inventory Svc │
     │                            │         ├─► Payment Svc   │
     │                            │         └─► Shipping Svc  │
     │                            │                           │
     
Each service processes event independently and asynchronously
```

**Python with RabbitMQ Example**:

```python
import pika
import json

# Producer (Order Service)
class OrderService:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='orders', exchange_type='fanout')
    
    def create_order(self, customer_id: str, items: list):
        order = {
            'order_id': generate_id(),
            'customer_id': customer_id,
            'items': items,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to database
        self.db.save(order)
        
        # Publish event (fire and forget)
        event = {
            'event_type': 'OrderCreated',
            'data': order
        }
        
        self.channel.basic_publish(
            exchange='orders',
            routing_key='',
            body=json.dumps(event)
        )
        
        return order['order_id']

# Consumer (Inventory Service)
class InventoryService:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters('localhost')
        )
        self.channel = self.connection.channel()
        self.channel.exchange_declare(exchange='orders', exchange_type='fanout')
        
        # Create exclusive queue for this service
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        self.channel.queue_bind(exchange='orders', queue=queue_name)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self.handle_order_event,
            auto_ack=True
        )
    
    def handle_order_event(self, ch, method, properties, body):
        event = json.loads(body)
        
        if event['event_type'] == 'OrderCreated':
            order_data = event['data']
            # Reserve inventory
            for item in order_data['items']:
                self.reserve_stock(item['product_id'], item['quantity'])
    
    def start(self):
        print('Inventory service listening for events...')
        self.channel.start_consuming()
```

---

## Part 4: Data Management Patterns

### Pattern 7: Database per Service

**Concept**: Each microservice has its own database. **No shared database access**.

**Why?**: Loose coupling, independent scaling, technology flexibility.

```
DATABASE PER SERVICE

┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐
│  Order Service  │      │ Customer Service│      │ Product Service │
│                 │      │                 │      │                 │
│  Business Logic │      │  Business Logic │      │  Business Logic │
└────────┬────────┘      └────────┬────────┘      └────────┬────────┘
         │                        │                        │
         │ ONLY this service      │ ONLY this service      │ ONLY this service
         │ can access             │ can access             │ can access
         ▼                        ▼                        ▼
    ┌─────────┐              ┌─────────┐              ┌─────────┐
    │ Order DB│              │Customer │              │ Product │
    │(Postgres│              │  DB     │              │  DB     │
    └─────────┘              │(MongoDB)│              │ (Elastic│
                             └─────────┘              │  Search)│
                                                      └─────────┘
```

**Challenge**: How do you query data across services?

---

### Pattern 8: Saga Pattern (Distributed Transactions)

**Concept**: A saga is a sequence of local transactions where each transaction updates data within a single service. If one step fails, compensating transactions undo previous steps.

**Key Terms**:
- **Local Transaction**: Transaction within a single service
- **Compensating Transaction**: Undoes the effect of a previous transaction
- **Orchestrator**: Centralized component that coordinates saga steps
- **Choreography**: Decentralized approach where services emit events

```
SAGA PATTERN - ORDER PROCESSING FLOW

Choreography-based Saga (Event-driven):

Order Service    Inventory Svc    Payment Svc    Shipping Svc
     │                │               │               │
     │ OrderCreated   │               │               │
     ├───────────────►│               │               │
     │                │ StockReserved │               │
     │                ├──────────────►│               │
     │                │               │ PaymentSuccess│
     │                │               ├──────────────►│
     │                │               │               │
     │                │               │   ◄─Success──►│
     │                │               │               │
     
If Payment Fails (Compensating Actions):
     │                │  PaymentFailed│               │
     │                │◄───────────────┤               │
     │ StockReleased  │               │               │
     │◄───────────────┤               │               │
     │ OrderCancelled │               │               │
```

**Go Orchestrator Example**:

```go
// Orchestrator-based Saga
type OrderSaga struct {
    orderService     *OrderService
    inventoryService *InventoryService
    paymentService   *PaymentService
    shippingService  *ShippingService
}

type SagaStep struct {
    Name       string
    Execute    func() error
    Compensate func() error
}

func (s *OrderSaga) ExecuteOrderSaga(orderData OrderData) error {
    var completedSteps []SagaStep
    
    // Define saga steps
    steps := []SagaStep{
        {
            Name: "CreateOrder",
            Execute: func() error {
                return s.orderService.CreateOrder(orderData)
            },
            Compensate: func() error {
                return s.orderService.CancelOrder(orderData.OrderID)
            },
        },
        {
            Name: "ReserveInventory",
            Execute: func() error {
                return s.inventoryService.ReserveStock(orderData.Items)
            },
            Compensate: func() error {
                return s.inventoryService.ReleaseStock(orderData.Items)
            },
        },
        {
            Name: "ProcessPayment",
            Execute: func() error {
                return s.paymentService.Charge(orderData.CustomerID, orderData.Total)
            },
            Compensate: func() error {
                return s.paymentService.Refund(orderData.CustomerID, orderData.Total)
            },
        },
        {
            Name: "CreateShipment",
            Execute: func() error {
                return s.shippingService.CreateShipment(orderData)
            },
            Compensate: func() error {
                return s.shippingService.CancelShipment(orderData.OrderID)
            },
        },
    }
    
    // Execute steps sequentially
    for _, step := range steps {
        if err := step.Execute(); err != nil {
            log.Printf("Step %s failed: %v", step.Name, err)
            
            // Compensate in reverse order
            for i := len(completedSteps) - 1; i >= 0; i-- {
                if compErr := completedSteps[i].Compensate(); compErr != nil {
                    log.Printf("Compensation failed for %s: %v", 
                        completedSteps[i].Name, compErr)
                    // This is critical - may need manual intervention
                }
            }
            
            return fmt.Errorf("saga failed at step %s: %w", step.Name, err)
        }
        
        completedSteps = append(completedSteps, step)
    }
    
    return nil
}
```

---

### Pattern 9: CQRS (Command Query Responsibility Segregation)

**Concept**: Separate read and write operations into different models. Commands modify data, queries read data.

**Why?**: Optimize reads and writes independently.

```
CQRS PATTERN

Write Side (Command)                Read Side (Query)
┌────────────────────┐             ┌────────────────────┐
│  Command Handler   │             │   Query Handler    │
│                    │             │                    │
│  ┌──────────────┐  │             │  ┌──────────────┐  │
│  │ Create Order │  │             │  │Get Order List│  │
│  │ Update Order │  │             │  │Get Dashboard │  │
│  └──────────────┘  │             │  └──────────────┘  │
└─────────┬──────────┘             └─────────┬──────────┘
          │                                   │
          ▼                                   ▼
    ┌──────────┐                        ┌──────────┐
    │ Write DB │                        │  Read DB │
    │(Postgres)│                        │ (MongoDB)│
    └────┬─────┘                        └────▲─────┘
         │                                   │
         │      ┌──────────────┐             │
         └─────►│ Event Stream ├─────────────┘
                │ (Kafka/RMQ)  │
                └──────────────┘
                
Write model optimized for consistency
Read model optimized for query performance
```

**Rust CQRS Example**:

```rust
// Command side - handles writes
pub struct OrderCommandHandler {
    event_store: EventStore,
}

#[derive(Debug, Clone)]
pub enum OrderCommand {
    CreateOrder { customer_id: String, items: Vec<OrderItem> },
    AddItem { order_id: String, item: OrderItem },
    SubmitOrder { order_id: String },
}

#[derive(Debug, Clone)]
pub enum OrderEvent {
    OrderCreated { order_id: String, customer_id: String },
    ItemAdded { order_id: String, item: OrderItem },
    OrderSubmitted { order_id: String, timestamp: DateTime },
}

impl OrderCommandHandler {
    pub async fn handle(&self, command: OrderCommand) -> Result<Vec<OrderEvent>> {
        match command {
            OrderCommand::CreateOrder { customer_id, items } => {
                let order_id = generate_id();
                let events = vec![
                    OrderEvent::OrderCreated {
                        order_id: order_id.clone(),
                        customer_id,
                    },
                ];
                
                // Items added as separate events
                let item_events: Vec<_> = items
                    .into_iter()
                    .map(|item| OrderEvent::ItemAdded {
                        order_id: order_id.clone(),
                        item,
                    })
                    .collect();
                
                let all_events = [events, item_events].concat();
                
                // Persist events
                self.event_store.append(&order_id, &all_events).await?;
                
                Ok(all_events)
            }
            OrderCommand::SubmitOrder { order_id } => {
                // Load current state from events
                let events = self.event_store.load(&order_id).await?;
                let order = Order::from_events(events);
                
                // Business validation
                if order.items.is_empty() {
                    return Err(Error::EmptyOrder);
                }
                
                let event = OrderEvent::OrderSubmitted {
                    order_id,
                    timestamp: Utc::now(),
                };
                
                self.event_store.append(&order_id, &[event.clone()]).await?;
                
                Ok(vec![event])
            }
            _ => todo!(),
        }
    }
}

// Query side - handles reads
pub struct OrderQueryHandler {
    read_db: ReadDatabase,
}

#[derive(Debug, Serialize)]
pub struct OrderView {
    pub order_id: String,
    pub customer_id: String,
    pub items: Vec<OrderItem>,
    pub status: String,
    pub total: f64,
}

impl OrderQueryHandler {
    pub async fn get_order(&self, order_id: &str) -> Result<OrderView> {
        // Query optimized read model
        self.read_db.find_order(order_id).await
    }
    
    pub async fn get_customer_orders(&self, customer_id: &str) -> Result<Vec<OrderView>> {
        // This query would be expensive on write model
        // But read model can have denormalized data
        self.read_db.find_orders_by_customer(customer_id).await
    }
}

// Event handler keeps read model in sync
pub struct OrderViewProjection {
    read_db: ReadDatabase,
}

impl OrderViewProjection {
    pub async fn handle_event(&self, event: OrderEvent) {
        match event {
            OrderEvent::OrderCreated { order_id, customer_id } => {
                let view = OrderView {
                    order_id,
                    customer_id,
                    items: vec![],
                    status: "created".to_string(),
                    total: 0.0,
                };
                self.read_db.insert(view).await;
            }
            OrderEvent::ItemAdded { order_id, item } => {
                // Update existing view
                self.read_db.add_item_to_order(&order_id, item).await;
            }
            OrderEvent::OrderSubmitted { order_id, .. } => {
                self.read_db.update_status(&order_id, "submitted").await;
            }
        }
    }
}
```

---

### Pattern 10: Event Sourcing

**Concept**: Store state changes as a sequence of events rather than storing current state. Current state is derived by replaying events.

**Key Terms**:
- **Event**: Immutable fact about something that happened
- **Event Store**: Append-only log of events
- **Projection**: Deriving current state from events
- **Snapshot**: Cached state at a point in time (performance optimization)

```
EVENT SOURCING

Traditional Approach:
┌────────────────┐
│  Current State │
│  Order #123    │
│  Status: PAID  │
│  Total: $100   │
└────────────────┘
     (overwrites previous state)

Event Sourcing Approach:
┌──────────────────────────────────────────┐
│          Event Store (Append-Only)        │
├──────────────────────────────────────────┤
│ 1. OrderCreated(#123, customer: Alice)   │
│ 2. ItemAdded(#123, product: Book, $50)   │
│ 3. ItemAdded(#123, product: Pen, $10)    │
│ 4. DiscountApplied(#123, -$10)           │
│ 5. OrderSubmitted(#123)                  │
│ 6. PaymentProcessed(#123, $100)          │
└──────────────────────────────────────────┘
              │
              │ Replay events to get current state
              ▼
        ┌────────────────┐
        │  Current State │
        │  Order #123    │
        │  Status: PAID  │
        │  Total: $100   │
        └────────────────┘
```

**Benefits**:
- Complete audit trail
- Time travel (replay to any point)
- Event-driven architecture naturally
- Can project into multiple views

**Python Event Sourcing Example**:

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Any
from enum import Enum

# Events are immutable facts
@dataclass(frozen=True)
class Event:
    event_id: str
    aggregate_id: str
    timestamp: datetime
    event_type: str
    data: dict

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PAID = "paid"
    SHIPPED = "shipped"

# Aggregate reconstructed from events
class Order:
    def __init__(self, order_id: str):
        self.order_id = order_id
        self.customer_id = None
        self.items = []
        self.status = OrderStatus.PENDING
        self.total = 0.0
        self.version = 0  # For optimistic concurrency
    
    def apply_event(self, event: Event):
        """Mutate state based on event"""
        self.version += 1
        
        if event.event_type == "OrderCreated":
            self.customer_id = event.data['customer_id']
        
        elif event.event_type == "ItemAdded":
            item = event.data['item']
            self.items.append(item)
            self.total += item['price'] * item['quantity']
        
        elif event.event_type == "OrderSubmitted":
            self.status = OrderStatus.SUBMITTED
        
        elif event.event_type == "PaymentProcessed":
            self.status = OrderStatus.PAID
    
    @classmethod
    def from_events(cls, events: List[Event]) -> 'Order':
        """Reconstruct aggregate from event history"""
        if not events:
            raise ValueError("Cannot create order from empty event list")
        
        order = cls(events[0].aggregate_id)
        for event in events:
            order.apply_event(event)
        
        return order

# Event Store
class EventStore:
    def __init__(self):
        self.events: dict[str, List[Event]] = {}
    
    def append(self, aggregate_id: str, events: List[Event], expected_version: int = None):
        """Append events with optimistic concurrency check"""
        if aggregate_id not in self.events:
            self.events[aggregate_id] = []
        
        current_version = len(self.events[aggregate_id])
        
        if expected_version is not None and current_version != expected_version:
            raise ConcurrencyError(
                f"Expected version {expected_version}, but current is {current_version}"
            )
        
        self.events[aggregate_id].extend(events)
    
    def load(self, aggregate_id: str) -> List[Event]:
        """Load all events for an aggregate"""
        return self.events.get(aggregate_id, [])

# Command handler using event sourcing
class OrderService:
    def __init__(self, event_store: EventStore):
        self.event_store = event_store
    
    def create_order(self, customer_id: str) -> str:
        order_id = generate_id()
        
        event = Event(
            event_id=generate_id(),
            aggregate_id=order_id,
            timestamp=datetime.now(),
            event_type="OrderCreated",
            data={'customer_id': customer_id}
        )
        
        self.event_store.append(order_id, [event])
        return order_id
    
    def add_item(self, order_id: str, product_id: str, quantity: int, price: float):
        # Load current state
        events = self.event_store.load(order_id)
        order = Order.from_events(events)
        
        # Business validation
        if order.status != OrderStatus.PENDING:
            raise InvalidOrderState("Cannot add items to non-pending order")
        
        # Create new event
        event = Event(
            event_id=generate_id(),
            aggregate_id=order_id,
            timestamp=datetime.now(),
            event_type="ItemAdded",
            data={
                'item': {
                    'product_id': product_id,
                    'quantity': quantity,
                    'price': price
                }
            }
        )
        
        # Append with optimistic concurrency
        self.event_store.append(order_id, [event], expected_version=order.version)
    
    def submit_order(self, order_id: str):
        events = self.event_store.load(order_id)
        order = Order.from_events(events)
        
        if not order.items:
            raise EmptyOrderError("Cannot submit order without items")
        
        event = Event(
            event_id=generate_id(),
            aggregate_id=order_id,
            timestamp=datetime.now(),
            event_type="OrderSubmitted",
            data={}
        )
        
        self.event_store.append(order_id, [event], expected_version=order.version)
```

---

## Part 5: Resilience Patterns

### Pattern 11: Circuit Breaker

**Concept**: Prevent cascading failures by stopping requests to a failing service. Think of it like an electrical circuit breaker—it "trips" when there's a problem.

**States**:
1. **Closed**: Normal operation, requests pass through
2. **Open**: Service is failing, requests fail immediately (fail fast)
3. **Half-Open**: Testing if service recovered

```
CIRCUIT BREAKER STATE MACHINE

                 ┌─────────────┐
                 │   CLOSED    │ ← Normal operation
                 │ (Pass calls)│
                 └──────┬──────┘
                        │
         Failure threshold reached
                        │
                        ▼
                 ┌─────────────┐
                 │    OPEN     │ ← Fail fast
                 │ (Reject all)│
                 └──────┬──────┘
                        │
                Timeout expires
                        │
                        ▼
                 ┌─────────────┐
                 │ HALF-OPEN   │ ← Testing
                 │(Allow some) │
                 └──────┬──────┘
                        │
            ┌───────────┴───────────┐
            │                       │
      Success (N calls)       More failures
            │                       │
            ▼                       ▼
        [CLOSED]                 [OPEN]
```

**Rust Circuit Breaker Example**:

```rust
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

#[derive(Debug, Clone, PartialEq)]
enum CircuitState {
    Closed,
    Open,
    HalfOpen,
}

pub struct CircuitBreaker {
    state: Arc<Mutex<CircuitBreakerState>>,
    failure_threshold: usize,
    success_threshold: usize,
    timeout: Duration,
}

struct CircuitBreakerState {
    state: CircuitState,
    failures: usize,
    successes: usize,
    last_failure_time: Option<Instant>,
}

impl CircuitBreaker {
    pub fn new(failure_threshold: usize, success_threshold: usize, timeout: Duration) -> Self {
        Self {
            state: Arc::new(Mutex::new(CircuitBreakerState {
                state: CircuitState::Closed,
                failures: 0,
                successes: 0,
                last_failure_time: None,
            })),
            failure_threshold,
            success_threshold,
            timeout,
        }
    }
    
    pub async fn call<F, T, E>(&self, operation: F) -> Result<T, CircuitBreakerError<E>>
    where
        F: std::future::Future<Output = Result<T, E>>,
    {
        // Check if we should allow the call
        {
            let mut state = self.state.lock().unwrap();
            
            match state.state {
                CircuitState::Open => {
                    // Check if timeout has expired
                    if let Some(last_failure) = state.last_failure_time {
                        if last_failure.elapsed() > self.timeout {
                            // Transition to half-open
                            state.state = CircuitState::HalfOpen;
                            state.failures = 0;
                            state.successes = 0;
                        } else {
                            // Still open, reject immediately
                            return Err(CircuitBreakerError::CircuitOpen);
                        }
                    }
                }
                CircuitState::Closed | CircuitState::HalfOpen => {
                    // Allow the call
                }
            }
        }
        
        // Execute the operation
        match operation.await {
            Ok(result) => {
                self.on_success();
                Ok(result)
            }
            Err(err) => {
                self.on_failure();
                Err(CircuitBreakerError::OperationFailed(err))
            }
        }
    }
    
    fn on_success(&self) {
        let mut state = self.state.lock().unwrap();
        
        match state.state {
            CircuitState::HalfOpen => {
                state.successes += 1;
                if state.successes >= self.success_threshold {
                    // Recovered! Close the circuit
                    state.state = CircuitState::Closed;
                    state.failures = 0;
                    state.successes = 0;
                }
            }
            CircuitState::Closed => {
                // Reset failure counter on success
                state.failures = 0;
            }
            CircuitState::Open => {
                // Shouldn't happen, but reset if it does
            }
        }
    }
    
    fn on_failure(&self) {
        let mut state = self.state.lock().unwrap();
        
        state.failures += 1;
        state.last_failure_time = Some(Instant::now());
        
        match state.state {
            CircuitState::Closed => {
                if state.failures >= self.failure_threshold {
                    // Trip the circuit
                    state.state = CircuitState::Open;
                }
            }
            CircuitState::HalfOpen => {
                // Any failure in half-open reopens the circuit
                state.state = CircuitState::Open;
                state.successes = 0;
            }
            CircuitState::Open => {
                // Already open
            }
        }
    }
}

// Usage example
async fn call_external_service_with_protection() -> Result<String, Box<dyn std::error::Error>> {
    let circuit_breaker = CircuitBreaker::new(
        5,                           // Open after 5 failures
        3,                           // Close after 3 successes
        Duration::from_secs(30),     // Try again after 30 seconds
    );
    
    let result = circuit_breaker.call(async {
        // Your actual service call
        make_http_request("https://api.example.com/data").await
    }).await?;
    
    Ok(result)
}
```

---

### Pattern 12: Retry Pattern

**Concept**: Automatically retry failed operations with backoff strategy.

**Strategies**:
1. **Fixed Delay**: Wait same time between retries
2. **Exponential Backoff**: Wait 1s, 2s, 4s, 8s...
3. **Exponential Backoff with Jitter**: Add randomness to prevent thundering herd

```
RETRY STRATEGIES

Fixed Delay:
Attempt 1 ──[fail]──► Wait 1s ──► Attempt 2 ──[fail]──► Wait 1s ──► Attempt 3

Exponential Backoff:
Attempt 1 ──[fail]──► Wait 1s ──► Attempt 2 ──[fail]──► Wait 2s ──► Attempt 3 ──[fail]──► Wait 4s

Exponential with Jitter (prevents thundering herd):
Attempt 1 ──[fail]──► Wait 0.8s ──► Attempt 2 ──[fail]──► Wait 2.3s ──► Attempt 3 ──[fail]──► Wait 3.7s
                       (random)                             (random)                             (random)
```

**Python Retry Implementation**:

```python
import asyncio
import random
from functools import wraps
from typing import TypeVar, Callable, Type

T = TypeVar('T')

class RetryExhausted(Exception):
    pass

def retry_with_backoff(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential: bool = True,
    jitter: bool = True,
    retry_on: tuple[Type[Exception], ...] = (Exception,)
):
    """
    Decorator for retrying async functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay cap
        exponential: Use exponential backoff
        jitter: Add random jitter to delays
        retry_on: Tuple of exception types to retry on
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e
                    
                    if attempt == max_attempts - 1:
                        # Last attempt failed
                        raise RetryExhausted(
                            f"Failed after {max_attempts} attempts: {str(e)}"
                        ) from e
                    
                    # Calculate delay
                    if exponential:
                        delay = base_delay * (2 ** attempt)
                    else:
                        delay = base_delay
                    
                    # Apply max delay cap
                    delay = min(delay, max_delay)
                    
                    # Add jitter (randomness)
                    if jitter:
                        delay = delay * (0.5 + random.random())
                    
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    await asyncio.sleep(delay)
            
            # This shouldn't be reached, but for type safety
            raise last_exception
        
        return wrapper
    return decorator

# Usage example
@retry_with_backoff(
    max_attempts=5,
    base_delay=1.0,
    exponential=True,
    jitter=True,
    retry_on=(ConnectionError, TimeoutError)
)
async def call_unreliable_service(url: str) -> dict:
    """This service might fail intermittently"""
    response = await http_client.get(url)
    return response.json()

# Example with manual retry logic
async def fetch_with_retry(url: str, max_retries: int = 3) -> str:
    for attempt in range(max_retries):
        try:
            response = await fetch(url)
            return response
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            delay = (2 ** attempt) * (0.5 + random.random())
            await asyncio.sleep(delay)
```

---

### Pattern 13: Bulkhead Pattern

**Concept**: Isolate resources so failure in one area doesn't bring down the entire system. Think of ship bulkheads that prevent flooding from spreading.

```
BULKHEAD PATTERN

Without Bulkhead (Shared Thread Pool):
┌──────────────────────────────────────┐
│     Single Thread Pool (10 threads)  │
├──────────────────────────────────────┤
│ ████████░░ Service A (8 threads)     │
│ █░░░░░░░░░ Service B (1 thread)      │ ← Service B starved!
│ █░░░░░░░░░ Service C (1 thread)      │ ← Service C starved!
└──────────────────────────────────────┘
   Service A is slow and consuming all resources

With Bulkhead (Isolated Pools):
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│ Service A    │ │ Service B    │ │ Service C    │
│ Pool (4)     │ │ Pool (3)     │ │ Pool (3)     │
├──────────────┤ ├──────────────┤ ├──────────────┤
│ ████░░░░░░   │ │ ███░░░░░░░   │ │ ██░░░░░░░░   │
└──────────────┘ └──────────────┘ └──────────────┘
   A is still slow,        B unaffected        C unaffected
   but isolated
```

**Go Bulkhead Implementation**:

```go
package main

import (
    "context"
    "errors"
    "sync"
)

// Bulkhead manages resource isolation
type Bulkhead struct {
    semaphore chan struct{}
    name      string
}

func NewBulkhead(name string, maxConcurrent int) *Bulkhead {
    return &Bulkhead{
        semaphore: make(chan struct{}, maxConcurrent),
        name:      name,
    }
}

// Execute runs operation with resource limits
func (b *Bulkhead) Execute(ctx context.Context, operation func() error) error {
    select {
    case b.semaphore <- struct{}{}:
        // Acquired slot
        defer func() { <-b.semaphore }()
        return operation()
    case <-ctx.Done():
        return ctx.Err()
    default:
        // No slots available
        return errors.New("bulkhead capacity exceeded")
    }
}

// Service with bulkhead protection
type OrderService struct {
    bulkhead *Bulkhead
}

func NewOrderService(maxConcurrentOrders int) *OrderService {
    return &OrderService{
        bulkhead: NewBulkhead("OrderService", maxConcurrentOrders),
    }
}

func (s *OrderService) ProcessOrder(ctx context.Context, orderID string) error {
    return s.bulkhead.Execute(ctx, func() error {
        // Simulate order processing
        // e.g., validate, charge payment, update inventory
        return nil
    })
}
```