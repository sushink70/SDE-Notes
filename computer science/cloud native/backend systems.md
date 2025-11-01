# Comprehensive Guide to Backend Systems

I'll create an extensive guide covering backend architecture, cloud computing, security, and implementation across Rust, Go, and Python.

## 1. Backend Architecture Fundamentals

### Core Components

**API Layer**
The API layer serves as the interface between clients and backend services. Modern backends typically use REST, GraphQL, or gRPC protocols. REST remains popular for its simplicity, GraphQL offers flexible queries, and gRPC provides high-performance binary communication.

**Business Logic Layer**
This layer contains the core application logic, processing rules, data transformations, and workflow orchestration. It should be independent of the API layer and data storage implementation, following clean architecture principles.

**Data Layer**
Handles all data persistence operations. This includes relational databases (PostgreSQL, MySQL), NoSQL databases (MongoDB, Cassandra), caching layers (Redis, Memcached), and message queues (RabbitMQ, Kafka).

**Service Integration Layer**
Manages communication with external services, third-party APIs, and microservices. Implements retry logic, circuit breakers, and graceful degradation.

## 2. Cloud Native Architecture

### Principles

**Microservices**
Cloud-native applications are decomposed into small, independently deployable services. Each service owns its data, communicates via well-defined APIs, and can be scaled independently.

**Containerization**
Services run in containers (typically Docker) that package the application with its dependencies, ensuring consistency across environments.

**Orchestration**
Kubernetes has become the de facto standard for container orchestration, managing deployment, scaling, networking, and service discovery.

**Observability**
Cloud-native systems require comprehensive monitoring (Prometheus, Grafana), distributed tracing (Jaeger, Zipkin), and centralized logging (ELK Stack, Loki).

### Twelve-Factor App Methodology

1. **Codebase**: One codebase tracked in version control, many deploys
2. **Dependencies**: Explicitly declare and isolate dependencies
3. **Config**: Store configuration in environment variables
4. **Backing Services**: Treat backing services as attached resources
5. **Build, Release, Run**: Strictly separate build and run stages
6. **Processes**: Execute the app as stateless processes
7. **Port Binding**: Export services via port binding
8. **Concurrency**: Scale out via the process model
9. **Disposability**: Maximize robustness with fast startup and graceful shutdown
10. **Dev/Prod Parity**: Keep development, staging, and production similar
11. **Logs**: Treat logs as event streams
12. **Admin Processes**: Run admin tasks as one-off processes

## 3. Cloud Computing Models

### Infrastructure as a Service (IaaS)

Provides virtualized computing resources over the internet. Examples include AWS EC2, Google Compute Engine, Azure Virtual Machines.

**Use Cases:**
- Legacy application migration
- Development and testing environments
- High-performance computing
- Custom infrastructure requirements

### Platform as a Service (PaaS)

Provides a platform allowing customers to develop, run, and manage applications without infrastructure complexity. Examples: Heroku, Google App Engine, AWS Elastic Beanstalk.

**Advantages:**
- Reduced operational overhead
- Faster time to market
- Built-in scaling and load balancing
- Integrated developer tools

### Function as a Service (FaaS) / Serverless

Event-driven execution model where code runs in response to events without managing servers. Examples: AWS Lambda, Google Cloud Functions, Azure Functions.

**Benefits:**
- Pay only for execution time
- Automatic scaling
- No server management
- Built-in high availability

**Limitations:**
- Cold start latency
- Execution time limits
- Vendor lock-in concerns
- Debugging complexity

### Container as a Service (CaaS)

Manages container lifecycle with orchestration. Examples: AWS ECS/EKS, Google Kubernetes Engine, Azure Kubernetes Service.

## 4. Data Center Fundamentals

### Physical Infrastructure

**Servers and Racks**
Data centers house thousands of servers organized in racks, typically 42U high. Modern data centers use high-density configurations to maximize space efficiency.

**Networking**
Hierarchical network topology with top-of-rack (ToR) switches connecting to aggregation switches and core routers. Software-Defined Networking (SDN) enables programmable network management.

**Power and Cooling**
Redundant power supplies with UPS systems and backup generators ensure continuous operation. Cooling systems maintain optimal temperature (typically 18-27°C), with modern facilities using hot/cold aisle containment and liquid cooling for efficiency.

**Storage Systems**
Mix of SSD for performance-critical workloads and HDD for capacity. Storage Area Networks (SAN) and Network Attached Storage (NAS) provide centralized storage management.

### Virtualization and Hypervisors

**Type 1 Hypervisors** (Bare Metal)
Run directly on hardware: VMware ESXi, Microsoft Hyper-V, KVM, Xen. Offer better performance and security isolation.

**Type 2 Hypervisors** (Hosted)
Run on top of operating systems: VirtualBox, VMware Workstation. Primarily used for development and testing.

### Software-Defined Infrastructure

**Software-Defined Networking (SDN)**
Separates control plane from data plane, enabling centralized network management and programmability.

**Software-Defined Storage (SDS)**
Abstracts storage hardware from software layer, providing flexibility and easier management.

**Infrastructure as Code (IaC)**
Terraform, Ansible, CloudFormation, and Pulumi enable declarative infrastructure management, version control, and reproducible deployments.

## 5. Security Architecture

### Defense in Depth

Multiple layers of security controls throughout the system:

**Network Security**
- Firewalls and network segmentation
- DDoS protection (Cloudflare, AWS Shield)
- Virtual Private Networks (VPN) for secure access
- Network intrusion detection/prevention systems (IDS/IPS)

**Application Security**
- Input validation and sanitization
- Output encoding to prevent XSS
- Parameterized queries to prevent SQL injection
- Content Security Policy (CSP) headers
- CORS configuration
- Rate limiting and throttling

**Authentication and Authorization**
- Multi-factor authentication (MFA)
- OAuth 2.0 and OpenID Connect for delegated authentication
- JSON Web Tokens (JWT) for stateless authentication
- Role-Based Access Control (RBAC)
- Principle of least privilege

**Data Security**
- Encryption at rest using AES-256
- Encryption in transit using TLS 1.3
- Key management services (AWS KMS, HashiCorp Vault)
- Data masking and tokenization for sensitive information
- Secure key rotation policies

**Infrastructure Security**
- Regular security patches and updates
- Hardened operating systems
- Bastion hosts for administrative access
- Security groups and network ACLs
- Immutable infrastructure

### Security Best Practices

**Secrets Management**
Never hardcode secrets in code. Use environment variables or dedicated secrets management solutions like HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault.

**Security Headers**
Implement comprehensive security headers:
- `Strict-Transport-Security` for HTTPS enforcement
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `Content-Security-Policy`
- `X-XSS-Protection`

**Logging and Monitoring**
- Log all authentication attempts
- Monitor for suspicious patterns
- Implement audit trails for sensitive operations
- Use Security Information and Event Management (SIEM) systems
- Set up alerting for security events

**Dependency Management**
- Regularly scan dependencies for vulnerabilities
- Use tools like Dependabot, Snyk, or OWASP Dependency-Check
- Keep dependencies updated
- Use Software Composition Analysis (SCA)

## 6. Implementation: Language-Specific Approaches

### Python Backend Development

**Frameworks**

*FastAPI* - Modern, fast framework with automatic API documentation and type hints:
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import asyncio

app = FastAPI()

class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

@app.post("/items/")
async def create_item(item: Item):
    # Business logic here
    return {"id": 1, **item.dict()}

@app.get("/items/{item_id}")
async def read_item(item_id: int):
    # Database query
    return {"item_id": item_id, "name": "Example"}
```

*Django* - Batteries-included framework with ORM, admin interface, and security features:
```python
from django.db import models
from django.contrib.auth.models import User
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

class Product(models.Model):
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE)

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
```

**Database Access**

*SQLAlchemy* for SQL databases:
```python
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    price = Column(Float, nullable=False)

engine = create_engine('postgresql://user:pass@localhost/dbname')
SessionLocal = sessionmaker(bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()
```

**Async Python**

Python's asyncio enables high-concurrency applications:
```python
import asyncio
import aiohttp
from typing import List

async def fetch_data(session: aiohttp.ClientSession, url: str) -> dict:
    async with session.get(url) as response:
        return await response.json()

async def process_multiple_requests(urls: List[str]) -> List[dict]:
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_data(session, url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results

# Usage
urls = ["http://api1.com", "http://api2.com", "http://api3.com"]
results = asyncio.run(process_multiple_requests(urls))
```

**Caching**

Redis integration:
```python
import redis
import json
from functools import wraps
from typing import Callable

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expiration: int = 3600):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # Execute function and cache result
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key, 
                expiration, 
                json.dumps(result)
            )
            return result
        return wrapper
    return decorator

@cache_result(expiration=600)
async def get_expensive_data(user_id: int):
    # Expensive database query or API call
    await asyncio.sleep(2)  # Simulate delay
    return {"user_id": user_id, "data": "expensive result"}
```

### Go Backend Development

**Web Frameworks**

*Gin* - High-performance HTTP framework:
```go
package main

import (
    "net/http"
    "github.com/gin-gonic/gin"
)

type Item struct {
    ID          int     `json:"id"`
    Name        string  `json:"name" binding:"required"`
    Description string  `json:"description"`
    Price       float64 `json:"price" binding:"required,gt=0"`
}

func main() {
    r := gin.Default()
    
    // Middleware
    r.Use(gin.Logger())
    r.Use(gin.Recovery())
    
    // Routes
    r.POST("/items", createItem)
    r.GET("/items/:id", getItem)
    
    r.Run(":8080")
}

func createItem(c *gin.Context) {
    var item Item
    if err := c.ShouldBindJSON(&item); err != nil {
        c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
        return
    }
    
    // Save to database
    item.ID = 1 // Generated ID
    c.JSON(http.StatusCreated, item)
}

func getItem(c *gin.Context) {
    id := c.Param("id")
    // Fetch from database
    c.JSON(http.StatusOK, gin.H{"id": id, "name": "Example"})
}
```

**Database Access**

Using SQLX for better database handling:
```go
package main

import (
    "database/sql"
    "fmt"
    _ "github.com/lib/pq"
    "github.com/jmoiron/sqlx"
)

type Product struct {
    ID        int     `db:"id"`
    Name      string  `db:"name"`
    Price     float64 `db:"price"`
    CreatedAt string  `db:"created_at"`
}

type ProductRepository struct {
    db *sqlx.DB
}

func NewProductRepository(db *sqlx.DB) *ProductRepository {
    return &ProductRepository{db: db}
}

func (r *ProductRepository) Create(p *Product) error {
    query := `
        INSERT INTO products (name, price)
        VALUES ($1, $2)
        RETURNING id, created_at
    `
    return r.db.QueryRowx(query, p.Name, p.Price).
        Scan(&p.ID, &p.CreatedAt)
}

func (r *ProductRepository) GetByID(id int) (*Product, error) {
    var product Product
    query := `SELECT * FROM products WHERE id = $1`
    err := r.db.Get(&product, query, id)
    if err == sql.ErrNoRows {
        return nil, fmt.Errorf("product not found")
    }
    return &product, err
}

func (r *ProductRepository) List() ([]Product, error) {
    var products []Product
    query := `SELECT * FROM products ORDER BY created_at DESC`
    err := r.db.Select(&products, query)
    return products, err
}
```

**Concurrency Patterns**

Go's goroutines and channels enable powerful concurrent programming:
```go
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
)

// Worker pool pattern
type Job struct {
    ID   int
    Data string
}

type Result struct {
    Job   Job
    Value string
    Error error
}

func worker(ctx context.Context, id int, jobs <-chan Job, results chan<- Result) {
    for {
        select {
        case <-ctx.Done():
            return
        case job, ok := <-jobs:
            if !ok {
                return
            }
            // Process job
            time.Sleep(100 * time.Millisecond) // Simulate work
            results <- Result{
                Job:   job,
                Value: fmt.Sprintf("Worker %d processed job %d", id, job.ID),
            }
        }
    }
}

func processJobs(jobs []Job, numWorkers int) []Result {
    ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
    defer cancel()
    
    jobChan := make(chan Job, len(jobs))
    resultChan := make(chan Result, len(jobs))
    
    // Start workers
    var wg sync.WaitGroup
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            worker(ctx, workerID, jobChan, resultChan)
        }(i)
    }
    
    // Send jobs
    go func() {
        for _, job := range jobs {
            jobChan <- job
        }
        close(jobChan)
    }()
    
    // Wait for completion
    go func() {
        wg.Wait()
        close(resultChan)
    }()
    
    // Collect results
    var results []Result
    for result := range resultChan {
        results = append(results, result)
    }
    
    return results
}
```

**Middleware Pattern**

```go
package main

import (
    "log"
    "net/http"
    "time"
)

type Middleware func(http.HandlerFunc) http.HandlerFunc

func LoggingMiddleware() Middleware {
    return func(next http.HandlerFunc) http.HandlerFunc {
        return func(w http.ResponseWriter, r *http.Request) {
            start := time.Now()
            next(w, r)
            log.Printf("%s %s %v", r.Method, r.URL.Path, time.Since(start))
        }
    }
}

func AuthMiddleware(requiredRole string) Middleware {
    return func(next http.HandlerFunc) http.HandlerFunc {
        return func(w http.ResponseWriter, r *http.Request) {
            token := r.Header.Get("Authorization")
            if token == "" {
                http.Error(w, "Unauthorized", http.StatusUnauthorized)
                return
            }
            // Validate token and check role
            next(w, r)
        }
    }
}

func Chain(f http.HandlerFunc, middlewares ...Middleware) http.HandlerFunc {
    for i := len(middlewares) - 1; i >= 0; i-- {
        f = middlewares[i](f)
    }
    return f
}

func main() {
    handler := func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("Hello, World!"))
    }
    
    http.HandleFunc("/api/protected", 
        Chain(handler, LoggingMiddleware(), AuthMiddleware("admin")))
    
    http.ListenAndServe(":8080", nil)
}
```

### Rust Backend Development

**Web Frameworks**

*Axum* - Ergonomic and modular web framework:
```rust
use axum::{
    routing::{get, post},
    extract::{Path, State},
    http::StatusCode,
    response::IntoResponse,
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::sync::Arc;
use tokio::sync::RwLock;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct Item {
    id: Option<u32>,
    name: String,
    description: Option<String>,
    price: f64,
}

#[derive(Clone)]
struct AppState {
    items: Arc<RwLock<Vec<Item>>>,
}

#[tokio::main]
async fn main() {
    let state = AppState {
        items: Arc::new(RwLock::new(Vec::new())),
    };

    let app = Router::new()
        .route("/items", post(create_item))
        .route("/items/:id", get(get_item))
        .with_state(state);

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    
    axum::serve(listener, app).await.unwrap();
}

async fn create_item(
    State(state): State<AppState>,
    Json(mut item): Json<Item>,
) -> impl IntoResponse {
    let mut items = state.items.write().await;
    item.id = Some(items.len() as u32 + 1);
    items.push(item.clone());
    (StatusCode::CREATED, Json(item))
}

async fn get_item(
    State(state): State<AppState>,
    Path(id): Path<u32>,
) -> Result<Json<Item>, StatusCode> {
    let items = state.items.read().await;
    items
        .iter()
        .find(|item| item.id == Some(id))
        .cloned()
        .map(Json)
        .ok_or(StatusCode::NOT_FOUND)
}
```

**Database Access with SQLx**

SQLx provides compile-time checked SQL queries:
```rust
use sqlx::{PgPool, FromRow};
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize, FromRow)]
struct Product {
    id: i32,
    name: String,
    price: f64,
    created_at: chrono::NaiveDateTime,
}

#[derive(Debug, Deserialize)]
struct CreateProduct {
    name: String,
    price: f64,
}

struct ProductRepository {
    pool: PgPool,
}

impl ProductRepository {
    fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    async fn create(&self, product: CreateProduct) -> Result<Product, sqlx::Error> {
        let result = sqlx::query_as::<_, Product>(
            "INSERT INTO products (name, price) VALUES ($1, $2) RETURNING *"
        )
        .bind(&product.name)
        .bind(product.price)
        .fetch_one(&self.pool)
        .await?;

        Ok(result)
    }

    async fn get_by_id(&self, id: i32) -> Result<Option<Product>, sqlx::Error> {
        let product = sqlx::query_as::<_, Product>(
            "SELECT * FROM products WHERE id = $1"
        )
        .bind(id)
        .fetch_optional(&self.pool)
        .await?;

        Ok(product)
    }

    async fn list(&self) -> Result<Vec<Product>, sqlx::Error> {
        let products = sqlx::query_as::<_, Product>(
            "SELECT * FROM products ORDER BY created_at DESC"
        )
        .fetch_all(&self.pool)
        .await?;

        Ok(products)
    }

    async fn update(&self, id: i32, product: CreateProduct) -> Result<Product, sqlx::Error> {
        let result = sqlx::query_as::<_, Product>(
            "UPDATE products SET name = $1, price = $2 WHERE id = $3 RETURNING *"
        )
        .bind(&product.name)
        .bind(product.price)
        .bind(id)
        .fetch_one(&self.pool)
        .await?;

        Ok(result)
    }

    async fn delete(&self, id: i32) -> Result<bool, sqlx::Error> {
        let result = sqlx::query("DELETE FROM products WHERE id = $1")
            .bind(id)
            .execute(&self.pool)
            .await?;

        Ok(result.rows_affected() > 0)
    }
}
```

**Error Handling**

Rust's Result type enables robust error handling:
```rust
use thiserror::Error;
use axum::{
    response::{IntoResponse, Response},
    http::StatusCode,
    Json,
};
use serde_json::json;

#[derive(Error, Debug)]
enum AppError {
    #[error("Database error: {0}")]
    DatabaseError(#[from] sqlx::Error),
    
    #[error("Not found: {0}")]
    NotFound(String),
    
    #[error("Validation error: {0}")]
    ValidationError(String),
    
    #[error("Unauthorized")]
    Unauthorized,
    
    #[error("Internal server error")]
    InternalError,
}

impl IntoResponse for AppError {
    fn into_response(self) -> Response {
        let (status, error_message) = match self {
            AppError::DatabaseError(e) => {
                eprintln!("Database error: {}", e);
                (StatusCode::INTERNAL_SERVER_ERROR, "Database error")
            }
            AppError::NotFound(msg) => (StatusCode::NOT_FOUND, msg.as_str()),
            AppError::ValidationError(msg) => (StatusCode::BAD_REQUEST, msg.as_str()),
            AppError::Unauthorized => (StatusCode::UNAUTHORIZED, "Unauthorized"),
            AppError::InternalError => (StatusCode::INTERNAL_SERVER_ERROR, "Internal error"),
        };

        let body = Json(json!({
            "error": error_message,
        }));

        (status, body).into_response()
    }
}

type AppResult<T> = Result<T, AppError>;

// Usage in handlers
async fn get_product_handler(
    State(repo): State<Arc<ProductRepository>>,
    Path(id): Path<i32>,
) -> AppResult<Json<Product>> {
    let product = repo
        .get_by_id(id)
        .await?
        .ok_or_else(|| AppError::NotFound(format!("Product {} not found", id)))?;
    
    Ok(Json(product))
}
```

**Async Concurrency**

Tokio-based concurrent operations:
```rust
use tokio::time::{sleep, Duration};
use futures::future::join_all;
use std::sync::Arc;

async fn fetch_data(id: u32) -> Result<String, Box<dyn std::error::Error>> {
    sleep(Duration::from_millis(100)).await;
    Ok(format!("Data for ID {}", id))
}

async fn process_concurrent(ids: Vec<u32>) -> Vec<Result<String, Box<dyn std::error::Error>>> {
    let futures: Vec<_> = ids
        .into_iter()
        .map(|id| tokio::spawn(fetch_data(id)))
        .collect();
    
    let results = join_all(futures).await;
    
    results
        .into_iter()
        .map(|r| r.unwrap_or_else(|e| Err(Box::new(e) as Box<dyn std::error::Error>)))
        .collect()
}

// Rate limiting with semaphore
use tokio::sync::Semaphore;

async fn process_with_limit(
    ids: Vec<u32>,
    max_concurrent: usize,
) -> Vec<Result<String, Box<dyn std::error::Error>>> {
    let semaphore = Arc::new(Semaphore::new(max_concurrent));
    
    let futures: Vec<_> = ids
        .into_iter()
        .map(|id| {
            let sem = semaphore.clone();
            tokio::spawn(async move {
                let _permit = sem.acquire().await.unwrap();
                fetch_data(id).await
            })
        })
        .collect();
    
    let results = join_all(futures).await;
    
    results
        .into_iter()
        .map(|r| r.unwrap_or_else(|e| Err(Box::new(e) as Box<dyn std::error::Error>)))
        .collect()
}
```

## 7. Design Patterns for Backend Systems

### Circuit Breaker

Prevents cascading failures by stopping requests to failing services:

**Python Implementation:**
```python
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Any
import asyncio

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 5,
        timeout: int = 60,
        expected_exception: type = Exception
    ):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        if self.state == CircuitState.OPEN:
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.timeout):
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception("Circuit breaker is OPEN")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except self.expected_exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### Repository Pattern

Abstracts data access logic:

**Go Implementation:**
```go
package repository

import (
    "context"
    "database/sql"
)

type Repository interface {
    Create(ctx context.Context, entity interface{}) error
    GetByID(ctx context.Context, id int) (interface{}, error)
    Update(ctx context.Context, entity interface{}) error
    Delete(ctx context.Context, id int) error
    List(ctx context.Context, filters map[string]interface{}) ([]interface{}, error)
}

type BaseRepository struct {
    db    *sql.DB
    table string
}

func NewBaseRepository(db *sql.DB, table string) *BaseRepository {
    return &BaseRepository{
        db:    db,
        table: table,
    }
}
```

### Event Sourcing

Store state changes as a sequence of events:

**Rust Implementation:**
```rust
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
enum OrderEvent {
    Created { customer_id: Uuid, items: Vec<String> },
    ItemAdded { item: String },
    ItemRemoved { item: String },
    Confirmed,
    Cancelled,
    Shipped { tracking_number: String },
    Delivered,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
struct Event {
    id: Uuid,
    aggregate_id: Uuid,
    event_type: String,
    payload: OrderEvent,
    timestamp: DateTime<Utc>,
    version: u32,
}

#[derive(Debug, Clone)]
struct Order {
    id: Uuid,
    customer_id: Uuid,
    items: Vec<String>,
    status: OrderStatus,
    version: u32,
}

#[derive(Debug, Clone, PartialEq)]
enum OrderStatus {
    Draft,
    Confirmed,
    Cancelled,
    Shipped,
    Delivered,
}

impl Order {
    fn apply_event(&mut self, event: &OrderEvent) {
        match event {
            OrderEvent::Created { customer_id, items } => {
                self.customer_id = *customer_id;
                self.items = items.clone();
                self.status = OrderStatus::Draft;
            }
            OrderEvent::ItemAdded { item } => {
                self.items.push(item.clone());
            }
            OrderEvent::ItemRemoved { item } => {
                self.items.retain(|i| i != item);
            }
            OrderEvent::Confirmed => {
                self.status = OrderStatus::Confirmed;
            }
            OrderEvent::Cancelled => {
                self.status = OrderStatus::Cancelled;
            }
            OrderEvent::Shipped { .. } => {
                self.status = OrderStatus::Shipped;
            }
            OrderEvent::Delivered => {
                self.status = OrderStatus::Delivered;
            }
        }
        ## 7. Design Patterns for Backend Systems (Continued)

### Event Sourcing (Continued)

```rust
        self.version += 1;
    }

    fn from_events(id: Uuid, events: Vec<Event>) -> Self {
        let mut order = Order {
            id,
            customer_id: Uuid::nil(),
            items: Vec::new(),
            status: OrderStatus::Draft,
            version: 0,
        };

        for event in events {
            order.apply_event(&event.payload);
        }

        order
    }
}

struct EventStore {
    events: Vec<Event>,
}

impl EventStore {
    fn new() -> Self {
        Self {
            events: Vec::new(),
        }
    }

    fn append(&mut self, event: Event) -> Result<(), String> {
        // In production, this would write to a persistent store
        self.events.push(event);
        Ok(())
    }

    fn get_events(&self, aggregate_id: Uuid) -> Vec<Event> {
        self.events
            .iter()
            .filter(|e| e.aggregate_id == aggregate_id)
            .cloned()
            .collect()
    }

    fn rebuild_aggregate(&self, aggregate_id: Uuid) -> Order {
        let events = self.get_events(aggregate_id);
        Order::from_events(aggregate_id, events)
    }
}
```

### CQRS (Command Query Responsibility Segregation)

Separate read and write operations for better scalability:

**Python Implementation:**
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional
import asyncio

# Commands (Write Side)
@dataclass
class CreateUserCommand:
    username: str
    email: str
    password: str

@dataclass
class UpdateUserCommand:
    user_id: int
    email: Optional[str] = None
    username: Optional[str] = None

# Queries (Read Side)
@dataclass
class GetUserQuery:
    user_id: int

@dataclass
class ListUsersQuery:
    page: int = 1
    page_size: int = 20
    search: Optional[str] = None

# Command Handler
class CommandHandler(ABC):
    @abstractmethod
    async def handle(self, command):
        pass

class CreateUserCommandHandler(CommandHandler):
    def __init__(self, write_repository, event_bus):
        self.write_repository = write_repository
        self.event_bus = event_bus

    async def handle(self, command: CreateUserCommand):
        # Write to primary database
        user = await self.write_repository.create_user(
            username=command.username,
            email=command.email,
            password=command.password
        )
        
        # Publish event for read model update
        await self.event_bus.publish({
            'type': 'UserCreated',
            'data': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
        
        return user

# Query Handler
class QueryHandler(ABC):
    @abstractmethod
    async def handle(self, query):
        pass

class GetUserQueryHandler(QueryHandler):
    def __init__(self, read_repository):
        self.read_repository = read_repository

    async def handle(self, query: GetUserQuery):
        # Read from optimized read model
        return await self.read_repository.get_user(query.user_id)

class ListUsersQueryHandler(QueryHandler):
    def __init__(self, read_repository):
        self.read_repository = read_repository

    async def handle(self, query: ListUsersQuery):
        return await self.read_repository.list_users(
            page=query.page,
            page_size=query.page_size,
            search=query.search
        )

# Event Handler (Updates Read Model)
class UserCreatedEventHandler:
    def __init__(self, read_model_repository):
        self.read_model_repository = read_model_repository

    async def handle(self, event):
        # Update denormalized read model
        await self.read_model_repository.insert_user_view(
            user_id=event['data']['user_id'],
            username=event['data']['username'],
            email=event['data']['email']
        )
```

### Saga Pattern

Manage distributed transactions across microservices:

**Go Implementation:**
```go
package saga

import (
    "context"
    "fmt"
    "log"
)

type SagaStep struct {
    Name        string
    Execute     func(ctx context.Context, data interface{}) error
    Compensate  func(ctx context.Context, data interface{}) error
}

type Saga struct {
    steps       []SagaStep
    executedSteps []int
}

func NewSaga() *Saga {
    return &Saga{
        steps:       make([]SagaStep, 0),
        executedSteps: make([]int, 0),
    }
}

func (s *Saga) AddStep(step SagaStep) {
    s.steps = append(s.steps, step)
}

func (s *Saga) Execute(ctx context.Context, data interface{}) error {
    for i, step := range s.steps {
        log.Printf("Executing step: %s", step.Name)
        
        if err := step.Execute(ctx, data); err != nil {
            log.Printf("Step %s failed: %v", step.Name, err)
            s.compensate(ctx, data)
            return fmt.Errorf("saga failed at step %s: %w", step.Name, err)
        }
        
        s.executedSteps = append(s.executedSteps, i)
    }
    
    log.Println("Saga completed successfully")
    return nil
}

func (s *Saga) compensate(ctx context.Context, data interface{}) {
    log.Println("Starting compensation")
    
    // Execute compensating actions in reverse order
    for i := len(s.executedSteps) - 1; i >= 0; i-- {
        stepIndex := s.executedSteps[i]
        step := s.steps[stepIndex]
        
        log.Printf("Compensating step: %s", step.Name)
        
        if err := step.Compensate(ctx, data); err != nil {
            log.Printf("Compensation failed for step %s: %v", step.Name, err)
            // In production, this would trigger alerts and manual intervention
        }
    }
    
    log.Println("Compensation completed")
}

// Example: Order Processing Saga
type OrderData struct {
    OrderID     string
    UserID      string
    Amount      float64
    Items       []string
    PaymentID   string
    InventoryID string
}

func CreateOrderSaga() *Saga {
    saga := NewSaga()
    
    // Step 1: Reserve Inventory
    saga.AddStep(SagaStep{
        Name: "ReserveInventory",
        Execute: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            // Call inventory service
            log.Printf("Reserving inventory for order %s", orderData.OrderID)
            orderData.InventoryID = "inv-123"
            return nil
        },
        Compensate: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Releasing inventory reservation %s", orderData.InventoryID)
            // Call inventory service to release reservation
            return nil
        },
    })
    
    // Step 2: Process Payment
    saga.AddStep(SagaStep{
        Name: "ProcessPayment",
        Execute: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Processing payment of %.2f for user %s", 
                orderData.Amount, orderData.UserID)
            orderData.PaymentID = "pay-456"
            return nil
        },
        Compensate: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Refunding payment %s", orderData.PaymentID)
            // Call payment service to refund
            return nil
        },
    })
    
    // Step 3: Create Order
    saga.AddStep(SagaStep{
        Name: "CreateOrder",
        Execute: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Creating order %s", orderData.OrderID)
            // Save order to database
            return nil
        },
        Compensate: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Cancelling order %s", orderData.OrderID)
            // Mark order as cancelled
            return nil
        },
    })
    
    // Step 4: Send Notification
    saga.AddStep(SagaStep{
        Name: "SendNotification",
        Execute: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Sending order confirmation to user %s", orderData.UserID)
            // Call notification service
            return nil
        },
        Compensate: func(ctx context.Context, data interface{}) error {
            orderData := data.(*OrderData)
            log.Printf("Sending cancellation notification to user %s", orderData.UserID)
            return nil
        },
    })
    
    return saga
}
```

### Rate Limiting

Control request rates to protect backend resources:

**Rust Implementation (Token Bucket):**
```rust
use std::sync::Arc;
use tokio::sync::Mutex;
use tokio::time::{Duration, Instant};

#[derive(Clone)]
pub struct TokenBucket {
    capacity: u32,
    tokens: Arc<Mutex<u32>>,
    refill_rate: u32, // tokens per second
    last_refill: Arc<Mutex<Instant>>,
}

impl TokenBucket {
    pub fn new(capacity: u32, refill_rate: u32) -> Self {
        Self {
            capacity,
            tokens: Arc::new(Mutex::new(capacity)),
            refill_rate,
            last_refill: Arc::new(Mutex::new(Instant::now())),
        }
    }

    pub async fn try_consume(&self, tokens: u32) -> bool {
        self.refill().await;
        
        let mut current_tokens = self.tokens.lock().await;
        
        if *current_tokens >= tokens {
            *current_tokens -= tokens;
            true
        } else {
            false
        }
    }

    async fn refill(&self) {
        let mut last_refill = self.last_refill.lock().await;
        let now = Instant::now();
        let elapsed = now.duration_since(*last_refill);
        
        let tokens_to_add = (elapsed.as_secs_f64() * self.refill_rate as f64) as u32;
        
        if tokens_to_add > 0 {
            let mut current_tokens = self.tokens.lock().await;
            *current_tokens = (*current_tokens + tokens_to_add).min(self.capacity);
            *last_refill = now;
        }
    }
}

// Middleware for Axum
use axum::{
    extract::State,
    http::{Request, StatusCode},
    middleware::Next,
    response::Response,
};

pub async fn rate_limit_middleware<B>(
    State(bucket): State<TokenBucket>,
    request: Request<B>,
    next: Next<B>,
) -> Result<Response, StatusCode> {
    if bucket.try_consume(1).await {
        Ok(next.run(request).await)
    } else {
        Err(StatusCode::TOO_MANY_REQUESTS)
    }
}
```

**Go Implementation (Sliding Window):**
```go
package ratelimit

import (
    "sync"
    "time"
)

type SlidingWindowRateLimiter struct {
    requests    []time.Time
    limit       int
    window      time.Duration
    mu          sync.Mutex
}

func NewSlidingWindowRateLimiter(limit int, window time.Duration) *SlidingWindowRateLimiter {
    return &SlidingWindowRateLimiter{
        requests: make([]time.Time, 0),
        limit:    limit,
        window:   window,
    }
}

func (rl *SlidingWindowRateLimiter) Allow() bool {
    rl.mu.Lock()
    defer rl.mu.Unlock()
    
    now := time.Now()
    cutoff := now.Add(-rl.window)
    
    // Remove old requests outside the window
    validRequests := make([]time.Time, 0)
    for _, reqTime := range rl.requests {
        if reqTime.After(cutoff) {
            validRequests = append(validRequests, reqTime)
        }
    }
    rl.requests = validRequests
    
    // Check if we can allow this request
    if len(rl.requests) < rl.limit {
        rl.requests = append(rl.requests, now)
        return true
    }
    
    return false
}

// Per-user rate limiter with Redis
type RedisRateLimiter struct {
    redis  *redis.Client
    limit  int
    window time.Duration
}

func (rl *RedisRateLimiter) AllowUser(userID string) (bool, error) {
    key := fmt.Sprintf("rate_limit:%s", userID)
    now := time.Now().Unix()
    windowStart := now - int64(rl.window.Seconds())
    
    pipe := rl.redis.Pipeline()
    
    // Remove old entries
    pipe.ZRemRangeByScore(ctx, key, "0", fmt.Sprintf("%d", windowStart))
    
    // Count current requests
    pipe.ZCard(ctx, key)
    
    // Add current request
    pipe.ZAdd(ctx, key, &redis.Z{
        Score:  float64(now),
        Member: now,
    })
    
    // Set expiration
    pipe.Expire(ctx, key, rl.window)
    
    cmds, err := pipe.Exec(ctx)
    if err != nil {
        return false, err
    }
    
    count := cmds[1].(*redis.IntCmd).Val()
    return count < int64(rl.limit), nil
}
```

## 8. Message Queues and Event-Driven Architecture

### Message Queue Patterns

**RabbitMQ with Python:**
```python
import pika
import json
from typing import Callable
import asyncio

class MessageQueue:
    def __init__(self, host: str = 'localhost'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self.channel = self.connection.channel()

    def declare_queue(self, queue_name: str, durable: bool = True):
        self.channel.queue_declare(queue=queue_name, durable=durable)

    def publish(self, queue_name: str, message: dict):
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # Make message persistent
            )
        )

    def consume(self, queue_name: str, callback: Callable):
        def wrapped_callback(ch, method, properties, body):
            message = json.loads(body)
            try:
                callback(message)
                ch.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                print(f"Error processing message: {e}")
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapped_callback
        )
        
        print(f"Waiting for messages on {queue_name}...")
        self.channel.start_consuming()

# Pub/Sub with fanout exchange
class PubSubQueue:
    def __init__(self, host: str = 'localhost'):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(host=host)
        )
        self.channel = self.connection.channel()

    def declare_exchange(self, exchange_name: str):
        self.channel.exchange_declare(
            exchange=exchange_name,
            exchange_type='fanout'
        )

    def publish(self, exchange_name: str, message: dict):
        self.channel.basic_publish(
            exchange=exchange_name,
            routing_key='',
            body=json.dumps(message)
        )

    def subscribe(self, exchange_name: str, callback: Callable):
        # Create exclusive queue for this subscriber
        result = self.channel.queue_declare(queue='', exclusive=True)
        queue_name = result.method.queue
        
        self.channel.queue_bind(
            exchange=exchange_name,
            queue=queue_name
        )
        
        def wrapped_callback(ch, method, properties, body):
            message = json.loads(body)
            callback(message)

        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=wrapped_callback,
            auto_ack=True
        )
        
        self.channel.start_consuming()
```

**Kafka with Go:**
```go
package kafka

import (
    "context"
    "encoding/json"
    "log"
    "github.com/segmentio/kafka-go"
)

type Producer struct {
    writer *kafka.Writer
}

func NewProducer(brokers []string, topic string) *Producer {
    return &Producer{
        writer: &kafka.Writer{
            Addr:     kafka.TCP(brokers...),
            Topic:    topic,
            Balancer: &kafka.LeastBytes{},
        },
    }
}

func (p *Producer) Publish(ctx context.Context, key string, value interface{}) error {
    bytes, err := json.Marshal(value)
    if err != nil {
        return err
    }

    return p.writer.WriteMessages(ctx, kafka.Message{
        Key:   []byte(key),
        Value: bytes,
    })
}

func (p *Producer) Close() error {
    return p.writer.Close()
}

type Consumer struct {
    reader *kafka.Reader
}

func NewConsumer(brokers []string, topic string, groupID string) *Consumer {
    return &Consumer{
        reader: kafka.NewReader(kafka.ReaderConfig{
            Brokers:  brokers,
            Topic:    topic,
            GroupID:  groupID,
            MinBytes: 10e3, // 10KB
            MaxBytes: 10e6, // 10MB
        }),
    }
}

func (c *Consumer) Consume(ctx context.Context, handler func([]byte) error) error {
    for {
        msg, err := c.reader.ReadMessage(ctx)
        if err != nil {
            return err
        }

        log.Printf("Received message: key=%s, partition=%d, offset=%d",
            string(msg.Key), msg.Partition, msg.Offset)

        if err := handler(msg.Value); err != nil {
            log.Printf("Error handling message: %v", err)
            // In production, implement dead letter queue or retry logic
        }
    }
}

func (c *Consumer) Close() error {
    return c.reader.Close()
}

// Example usage
type OrderEvent struct {
    OrderID   string  `json:"order_id"`
    UserID    string  `json:"user_id"`
    Amount    float64 `json:"amount"`
    Status    string  `json:"status"`
    Timestamp int64   `json:"timestamp"`
}

func PublishOrderEvent(producer *Producer, event OrderEvent) error {
    return producer.Publish(
        context.Background(),
        event.OrderID,
        event,
    )
}

func ConsumeOrderEvents(consumer *Consumer) {
    consumer.Consume(context.Background(), func(data []byte) error {
        var event OrderEvent
        if err := json.Unmarshal(data, &event); err != nil {
            return err
        }

        log.Printf("Processing order: %s", event.OrderID)
        // Handle the event
        return nil
    })
}
```

### Event Sourcing with Kafka

**Rust Implementation:**
```rust
use rdkafka::{
    config::ClientConfig,
    consumer::{Consumer, StreamConsumer},
    producer::{FutureProducer, FutureRecord},
    Message,
};
use serde::{Deserialize, Serialize};
use chrono::{DateTime, Utc};
use uuid::Uuid;

#[derive(Debug, Serialize, Deserialize, Clone)]
struct DomainEvent {
    event_id: Uuid,
    aggregate_id: Uuid,
    event_type: String,
    payload: serde_json::Value,
    timestamp: DateTime<Utc>,
    version: u32,
}

struct EventPublisher {
    producer: FutureProducer,
    topic: String,
}

impl EventPublisher {
    fn new(brokers: &str, topic: String) -> Result<Self, rdkafka::error::KafkaError> {
        let producer: FutureProducer = ClientConfig::new()
            .set("bootstrap.servers", brokers)
            .set("message.timeout.ms", "5000")
            .create()?;

        Ok(Self { producer, topic })
    }

    async fn publish(&self, event: &DomainEvent) -> Result<(), Box<dyn std::error::Error>> {
        let payload = serde_json::to_string(event)?;
        let key = event.aggregate_id.to_string();

        let record = FutureRecord::to(&self.topic)
            .key(&key)
            .payload(&payload);

        self.producer
            .send(record, std::time::Duration::from_secs(0))
            .await
            .map_err(|(e, _)| e)?;

        Ok(())
    }
}

struct EventSubscriber {
    consumer: StreamConsumer,
}

impl EventSubscriber {
    fn new(
        brokers: &str,
        group_id: &str,
        topics: &[&str],
    ) -> Result<Self, rdkafka::error::KafkaError> {
        let consumer: StreamConsumer = ClientConfig::new()
            .set("group.id", group_id)
            .set("bootstrap.servers", brokers)
            .set("enable.auto.commit", "false")
            .set("auto.offset.reset", "earliest")
            .create()?;

        consumer.subscribe(topics)?;

        Ok(Self { consumer })
    }

    async fn process_events<F>(&self, mut handler: F) -> Result<(), Box<dyn std::error::Error>>
    where
        F: FnMut(DomainEvent) -> Result<(), Box<dyn std::error::Error>>,
    {
        use rdkafka::consumer::StreamConsumer;
        use futures::StreamExt;

        let mut stream = self.consumer.stream();

        while let Some(message) = stream.next().await {
            match message {
                Ok(m) => {
                    if let Some(payload) = m.payload() {
                        let event: DomainEvent = serde_json::from_slice(payload)?;
                        
                        if let Err(e) = handler(event) {
                            eprintln!("Error handling event: {}", e);
                            // Implement retry or dead letter queue logic
                        } else {
                            self.consumer.commit_message(&m, rdkafka::consumer::CommitMode::Async)?;
                        }
                    }
                }
                Err(e) => {
                    eprintln!("Kafka error: {}", e);
                }
            }
        }

        Ok(())
    }
}
```

## 9. Caching Strategies

### Cache Patterns

**Cache-Aside (Lazy Loading) - Python:**
```python
import redis
import json
from typing import Optional, Callable, Any
from functools import wraps

class CacheAside:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client

    def get(self, key: str, loader: Callable, ttl: int = 3600) -> Any:
        # Try to get from cache
        cached = self.redis.get(key)
        if cached:
            return json.loads(cached)

        # Load from source
        data = loader()
        
        # Store in cache
        self.redis.setex(key, ttl, json.dumps(data))
        
        return data

    def invalidate(self, key: str):
        self.redis.delete(key)

# Decorator for automatic caching
def cached(prefix: str, ttl: int = 3600):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{prefix}:{str(args)}:{str(kwargs)}"
            
            # Try cache
            cached = redis_client.get(cache_key)
            if cached:
                return json.loads(cached)

            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator

# Usage
@cached(prefix="user", ttl=600)
async def get_user(user_id: int):
    # Expensive database query
    return await db.fetch_user(user_id)
```

**Write-Through Cache - Go:**
```go
package cache

import (
    "context"
    "encoding/json"
    "fmt"
    "time"
    "github.com/go-redis/redis/v8"
)

type WriteThroughCache struct {
    redis *redis.Client
    db    Database
}

type Database interface {
    Save(ctx context.Context, key string, value interface{}) error
    Load(ctx context.Context, key string) (interface{}, error)
}

func NewWriteThroughCache(redisClient *redis.Client, db Database) *WriteThroughCache {
    return &WriteThroughCache{
        redis: redisClient,
        db:    db,
    }
}

func (c *WriteThroughCache) Set(ctx context.Context, key string, value interface{}, ttl time.Duration) error {
    // Write to database first
    if err := c.db.Save(ctx, key, value); err != nil {
        return fmt.Errorf("database write failed: %w", err)
    }

    // Then write to cache
    bytes, err := json.Marshal(value)
    if err != nil {
        return fmt.Errorf("marshal failed: %w", err)
    }

    if err := c.redis.Set(ctx, key, bytes, ttl).Err(); err != nil {
        // Log cache write failure, but don't fail the operation
        // since data is already in database
        fmt.Printf("cache write failed: %v\n", err)
    }

    return nil
}

func (c *WriteThroughCache) Get(ctx context.Context, key string, result interface{}) error {
    // Try cache first
    bytes, err := c.redis.Get(ctx, key).Bytes()
    if err == nil {
        return json.Unmarshal(bytes, result)
    }

    // Cache miss - load from database
    data, err := c.db.Load(ctx, key)
    if err != nil {
        return fmt.Errorf("database read failed: %w", err)
    }

    // Populate cache for next time
    bytes, _ = json.Marshal(data)
    c.redis.Set(ctx, key, bytes, 1*time.Hour)

    return json.Unmarshal(bytes, result)
}
```

**Write-Behind (Write-Back) Cache - Rust:**
```rust
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio::time::{interval, Duration};

#[derive(Clone)]
struct WriteBehindCache<K, V> {
    cache: Arc<RwLock<HashMap<K, CacheEntry<V>>>>,
    dirty: Arc<RwLock<Vec<K>>>,
    flush_interval: Duration,
}

struct CacheEntry<V> {
    value: V,
    dirty: bool,
}

impl<K, V> WriteBehindCache<K, V>
where
    K: Clone + Eq + std::hash::Hash + Send + Sync + 'static,
    V: Clone + Send + Sync + 'static,
{
    fn new(flush_interval: Duration) -> Self {
        let cache = Arc::new(RwLock::new(HashMap::new()));
        let dirty = Arc::new(RwLock::new(Vec::new()));

        Self {
            cache,
            dirty,
            flush_interval,
        }
    }

    async fn set(&self, key: K, value: V) {
        let mut cache = self.cache.write().await;
        cache.insert(
            key.clone(),
            CacheEntry {
                value,
                dirty: true,
            },
        );

        let mut dirty = self.dirty.write().await;
        if !dirty.contains(&key) {
            dirty.push(key);
        }
    }

    async fn get(&self, key: &K) -> Option<V> {
        let cache = self.cache.read().await;
        cache.get(key).map(|entry| entry.value.clone())
    }

    fn start_flush_task<F>(self, flush_fn: F)
    where
        F: Fn(Vec<(K, V)>) -> tokio::task::JoinHandle<()> + Send + Sync + 'static,
    {
        tokio::spawn(async move {
            let mut ticker = interval(self.flush_interval);

            loop {
                ticker.tick().await;

                let keys_to_flush = {
                    let mut dirty = self.dirty.write().await;
                    std::mem::take(&mut *dirty)
                };

                if keys_to_flush.is_empty() {
                    continue;
                }

                let entries_to_flush: Vec<(K, V)> = {
                    let mut cache = self.cache.write().await;
                    keys_to_flush
                        .into_iter()
                        .filter_map(|key| {
                            cache.get_mut(&key).and_then(|entry| {
                                if entry.dirty {
                                    entry.dirty = false;
                                    Some((key.clone(), entry.value.clone()))
                                } else {
                                    None
                                }
                            })
                        })
                        .collect()
                };

                if !entries_to_flush.is_empty() {
                    flush_fn(entries_to_flush).await;
                }
            }
        });
    }
}

// Example usage
async fn example_usage() {
    let cache = WriteBehindCache::new(Duration::from_secs(5));

    // Start background flush task
    let cache_clone = cache.clone();
    cache_clone.start_flush_task(|entries| {
        tokio::spawn(async move {
            // Batch write to database
            println!("Flushing {} entries to database", entries.len());
            for (key, value) in entries {
                // database.save(key, value).await;
            }
        })
    });

    // Use the cache
    cache.set("user:1".to_string(), "John Doe".to_string()).await;
    cache.set("user:2".to_string(), "Jane Smith".to_string
    ## 9. Caching Strategies (Continued)

```rust
    ).await;

    // Read from cache
    if let Some(value) = cache.get(&"user:1".to_string()).await {
        println!("Cached value: {}", value);
    }
}
```

### Multi-Level Caching

**Python Implementation with Redis and Local Cache:**
```python
import asyncio
from typing import Optional, Any
import redis.asyncio as redis
from cachetools import TTLCache
import json

class MultiLevelCache:
    def __init__(
        self,
        redis_client: redis.Redis,
        local_cache_size: int = 1000,
        local_ttl: int = 60,
        redis_ttl: int = 3600
    ):
        self.redis = redis_client
        self.local_cache = TTLCache(maxsize=local_cache_size, ttl=local_ttl)
        self.redis_ttl = redis_ttl

    async def get(self, key: str) -> Optional[Any]:
        # L1: Check local memory cache
        if key in self.local_cache:
            return self.local_cache[key]

        # L2: Check Redis
        cached = await self.redis.get(key)
        if cached:
            value = json.loads(cached)
            # Populate L1 cache
            self.local_cache[key] = value
            return value

        return None

    async def set(self, key: str, value: Any):
        # Write to both levels
        self.local_cache[key] = value
        await self.redis.setex(
            key,
            self.redis_ttl,
            json.dumps(value)
        )

    async def delete(self, key: str):
        # Invalidate both levels
        self.local_cache.pop(key, None)
        await self.redis.delete(key)

    async def get_or_fetch(
        self,
        key: str,
        fetch_fn: callable,
        *args,
        **kwargs
    ) -> Any:
        # Try cache first
        cached = await self.get(key)
        if cached is not None:
            return cached

        # Fetch from source
        value = await fetch_fn(*args, **kwargs)
        
        # Cache the result
        await self.set(key, value)
        
        return value

# Usage example
async def example():
    redis_client = await redis.from_url("redis://localhost")
    cache = MultiLevelCache(redis_client)

    # Fetch with caching
    user = await cache.get_or_fetch(
        f"user:{user_id}",
        fetch_user_from_db,
        user_id=123
    )
```

### Cache Invalidation Strategies

**Go Implementation with Cache Stampede Prevention:**
```go
package cache

import (
    "context"
    "encoding/json"
    "errors"
    "sync"
    "time"
    "github.com/go-redis/redis/v8"
)

// Prevents cache stampede using single-flight pattern
type StampedeProtectedCache struct {
    redis  *redis.Client
    flight *singleflight.Group
}

type singleflight struct {
    mu sync.Mutex
    m  map[string]*call
}

type call struct {
    wg  sync.WaitGroup
    val interface{}
    err error
}

func (g *singleflight) Do(key string, fn func() (interface{}, error)) (interface{}, error) {
    g.mu.Lock()
    if g.m == nil {
        g.m = make(map[string]*call)
    }
    if c, ok := g.m[key]; ok {
        g.mu.Unlock()
        c.wg.Wait()
        return c.val, c.err
    }
    c := new(call)
    c.wg.Add(1)
    g.m[key] = c
    g.mu.Unlock()

    c.val, c.err = fn()
    c.wg.Done()

    g.mu.Lock()
    delete(g.m, key)
    g.mu.Unlock()

    return c.val, c.err
}

func NewStampedeProtectedCache(redisClient *redis.Client) *StampedeProtectedCache {
    return &StampedeProtectedCache{
        redis:  redisClient,
        flight: &singleflight{},
    }
}

func (c *StampedeProtectedCache) GetOrLoad(
    ctx context.Context,
    key string,
    loader func() (interface{}, error),
    ttl time.Duration,
) (interface{}, error) {
    // Try cache first
    cached, err := c.redis.Get(ctx, key).Result()
    if err == nil {
        var result interface{}
        if err := json.Unmarshal([]byte(cached), &result); err == nil {
            return result, nil
        }
    }

    // Use singleflight to prevent stampede
    result, err := c.flight.Do(key, func() (interface{}, error) {
        // Check cache again (might have been populated by another goroutine)
        cached, err := c.redis.Get(ctx, key).Result()
        if err == nil {
            var result interface{}
            if err := json.Unmarshal([]byte(cached), &result); err == nil {
                return result, nil
            }
        }

        // Load from source
        data, err := loader()
        if err != nil {
            return nil, err
        }

        // Cache the result
        bytes, err := json.Marshal(data)
        if err != nil {
            return data, nil // Return data even if caching fails
        }

        c.redis.Set(ctx, key, bytes, ttl)
        return data, nil
    })

    return result, err
}

// Probabilistic early expiration to prevent stampede
func (c *StampedeProtectedCache) GetWithProbabilisticEarlyExpiration(
    ctx context.Context,
    key string,
    loader func() (interface{}, error),
    ttl time.Duration,
    beta float64, // typically 1.0
) (interface{}, error) {
    type CachedData struct {
        Value     json.RawMessage `json:"value"`
        CachedAt  int64          `json:"cached_at"`
    }

    cached, err := c.redis.Get(ctx, key).Result()
    if err == nil {
        var data CachedData
        if err := json.Unmarshal([]byte(cached), &data); err == nil {
            now := time.Now().Unix()
            age := now - data.CachedAt
            
            // Probabilistic early recomputation
            // P(recompute) = beta * age / ttl
            expiry := float64(ttl.Seconds())
            delta := beta * float64(age) / expiry
            
            if delta < 1.0 && (delta < 0 || time.Now().UnixNano()%100 > int64(delta*100)) {
                var result interface{}
                json.Unmarshal(data.Value, &result)
                return result, nil
            }
        }
    }

    // Recompute
    result, err := loader()
    if err != nil {
        return nil, err
    }

    // Cache with metadata
    valueBytes, _ := json.Marshal(result)
    cached_data := CachedData{
        Value:    valueBytes,
        CachedAt: time.Now().Unix(),
    }
    
    bytes, _ := json.Marshal(cached_data)
    c.redis.Set(ctx, key, bytes, ttl)

    return result, nil
}
```

## 10. API Design and Documentation

### RESTful API Best Practices

**Python FastAPI with Comprehensive Documentation:**
```python
from fastapi import FastAPI, HTTPException, Query, Path, Depends, status
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum

app = FastAPI(
    title="E-Commerce API",
    description="Comprehensive e-commerce backend API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Models with validation
class ProductStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONTINUED = "discontinued"

class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: float = Field(..., gt=0, description="Price must be greater than 0")
    stock: int = Field(..., ge=0, description="Stock cannot be negative")
    status: ProductStatus = ProductStatus.ACTIVE

    @validator('price')
    def price_must_have_two_decimals(cls, v):
        if round(v, 2) != v:
            raise ValueError('Price must have at most 2 decimal places')
        return v

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    price: Optional[float] = Field(None, gt=0)
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[ProductStatus] = None

class Product(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PaginatedResponse(BaseModel):
    items: List[Product]
    total: int
    page: int
    page_size: int
    total_pages: int

# Dependency for pagination
def pagination_params(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    return {"skip": (page - 1) * page_size, "limit": page_size, "page": page}

# API Endpoints
@app.post(
    "/products",
    response_model=Product,
    status_code=status.HTTP_201_CREATED,
    tags=["products"],
    summary="Create a new product",
    response_description="The created product"
)
async def create_product(product: ProductCreate):
    """
    Create a new product with the following information:
    
    - **name**: Product name (required)
    - **description**: Product description (optional)
    - **price**: Product price, must be greater than 0 (required)
    - **stock**: Available stock, cannot be negative (required)
    - **status**: Product status (default: active)
    """
    # Implementation
    pass

@app.get(
    "/products",
    response_model=PaginatedResponse,
    tags=["products"],
    summary="List all products"
)
async def list_products(
    pagination: dict = Depends(pagination_params),
    status: Optional[ProductStatus] = Query(None, description="Filter by status"),
    search: Optional[str] = Query(None, min_length=3, description="Search in name and description"),
    min_price: Optional[float] = Query(None, ge=0),
    max_price: Optional[float] = Query(None, ge=0)
):
    """
    Retrieve a paginated list of products with optional filters.
    """
    # Implementation
    pass

@app.get(
    "/products/{product_id}",
    response_model=Product,
    tags=["products"],
    responses={
        200: {"description": "Product found"},
        404: {"description": "Product not found"}
    }
)
async def get_product(
    product_id: int = Path(..., gt=0, description="The ID of the product to retrieve")
):
    """
    Get a specific product by ID.
    """
    # Implementation
    pass

@app.patch(
    "/products/{product_id}",
    response_model=Product,
    tags=["products"]
)
async def update_product(
    product_id: int = Path(..., gt=0),
    product: ProductUpdate = None
):
    """
    Update a product. Only provided fields will be updated.
    """
    # Implementation
    pass

@app.delete(
    "/products/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["products"]
)
async def delete_product(product_id: int = Path(..., gt=0)):
    """
    Delete a product by ID.
    """
    # Implementation
    pass

# Error handling
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    )
```

### GraphQL API

**Go Implementation with gqlgen:**
```go
// schema.graphql
type Query {
    user(id: ID!): User
    users(first: Int, after: String): UserConnection!
    product(id: ID!): Product
    products(filter: ProductFilter, pagination: PaginationInput): ProductConnection!
}

type Mutation {
    createUser(input: CreateUserInput!): User!
    updateUser(id: ID!, input: UpdateUserInput!): User!
    deleteUser(id: ID!): Boolean!
    createProduct(input: CreateProductInput!): Product!
}

type Subscription {
    productUpdated(productId: ID!): Product!
    orderStatusChanged(userId: ID!): Order!
}

type User {
    id: ID!
    email: String!
    name: String!
    createdAt: Time!
    orders: [Order!]!
}

type Product {
    id: ID!
    name: String!
    description: String
    price: Float!
    stock: Int!
    status: ProductStatus!
    createdAt: Time!
}

enum ProductStatus {
    ACTIVE
    INACTIVE
    DISCONTINUED
}

input ProductFilter {
    status: ProductStatus
    minPrice: Float
    maxPrice: Float
    search: String
}

input PaginationInput {
    first: Int
    after: String
}

type ProductConnection {
    edges: [ProductEdge!]!
    pageInfo: PageInfo!
    totalCount: Int!
}

type ProductEdge {
    node: Product!
    cursor: String!
}

type PageInfo {
    hasNextPage: Boolean!
    hasPreviousPage: Boolean!
    startCursor: String
    endCursor: String
}
```

```go
// resolver.go
package graph

import (
    "context"
    "fmt"
)

type Resolver struct {
    productRepo ProductRepository
    userRepo    UserRepository
}

func (r *queryResolver) Product(ctx context.Context, id string) (*model.Product, error) {
    product, err := r.productRepo.GetByID(ctx, id)
    if err != nil {
        return nil, fmt.Errorf("product not found: %w", err)
    }
    return product, nil
}

func (r *queryResolver) Products(
    ctx context.Context,
    filter *model.ProductFilter,
    pagination *model.PaginationInput,
) (*model.ProductConnection, error) {
    // Apply filters
    query := r.productRepo.Query()
    
    if filter != nil {
        if filter.Status != nil {
            query = query.Where("status = ?", *filter.Status)
        }
        if filter.MinPrice != nil {
            query = query.Where("price >= ?", *filter.MinPrice)
        }
        if filter.MaxPrice != nil {
            query = query.Where("price <= ?", *filter.MaxPrice)
        }
        if filter.Search != nil {
            query = query.Where("name LIKE ? OR description LIKE ?",
                "%"+*filter.Search+"%", "%"+*filter.Search+"%")
        }
    }

    // Apply pagination
    first := 20
    if pagination != nil && pagination.First != nil {
        first = *pagination.First
    }

    products, totalCount, err := query.Paginate(ctx, first, pagination.After)
    if err != nil {
        return nil, err
    }

    return buildProductConnection(products, totalCount), nil
}

func (r *mutationResolver) CreateProduct(
    ctx context.Context,
    input model.CreateProductInput,
) (*model.Product, error) {
    product := &model.Product{
        Name:        input.Name,
        Description: input.Description,
        Price:       input.Price,
        Stock:       input.Stock,
        Status:      model.ProductStatusActive,
    }

    if err := r.productRepo.Create(ctx, product); err != nil {
        return nil, fmt.Errorf("failed to create product: %w", err)
    }

    return product, nil
}

// Subscription resolver
func (r *subscriptionResolver) ProductUpdated(
    ctx context.Context,
    productID string,
) (<-chan *model.Product, error) {
    productChan := make(chan *model.Product, 1)

    go func() {
        subscription := r.productRepo.Subscribe(productID)
        defer subscription.Close()

        for {
            select {
            case <-ctx.Done():
                return
            case product := <-subscription.Updates():
                productChan <- product
            }
        }
    }()

    return productChan, nil
}
```

### API Versioning

**Rust Axum with URL-based versioning:**
```rust
use axum::{
    Router,
    routing::{get, post},
    extract::{Path, State},
    Json,
};

// V1 Models and Handlers
mod v1 {
    use serde::{Deserialize, Serialize};

    #[derive(Serialize, Deserialize)]
    pub struct User {
        pub id: i32,
        pub name: String,
        pub email: String,
    }

    pub async fn get_user(Path(id): Path<i32>) -> Json<User> {
        Json(User {
            id,
            name: "John Doe".to_string(),
            email: "john@example.com".to_string(),
        })
    }

    pub async fn create_user(Json(user): Json<User>) -> Json<User> {
        Json(user)
    }
}

// V2 Models and Handlers
mod v2 {
    use serde::{Deserialize, Serialize};
    use chrono::{DateTime, Utc};

    #[derive(Serialize, Deserialize)]
    pub struct User {
        pub id: i32,
        pub name: String,
        pub email: String,
        pub phone: Option<String>, // New field
        pub created_at: DateTime<Utc>, // New field
    }

    pub async fn get_user(Path(id): Path<i32>) -> Json<User> {
        Json(User {
            id,
            name: "John Doe".to_string(),
            email: "john@example.com".to_string(),
            phone: Some("+1234567890".to_string()),
            created_at: Utc::now(),
        })
    }

    pub async fn create_user(Json(user): Json<User>) -> Json<User> {
        Json(user)
    }
}

#[tokio::main]
async fn main() {
    let app = Router::new()
        // V1 routes
        .nest("/api/v1", Router::new()
            .route("/users/:id", get(v1::get_user))
            .route("/users", post(v1::create_user))
        )
        // V2 routes
        .nest("/api/v2", Router::new()
            .route("/users/:id", get(v2::get_user))
            .route("/users", post(v2::create_user))
        );

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000")
        .await
        .unwrap();
    
    axum::serve(listener, app).await.unwrap();
}
```

## 11. Monitoring and Observability

### Structured Logging

**Python with structlog:**
```python
import structlog
from datetime import datetime
import sys

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Usage
def process_order(order_id: str, user_id: str):
    log = logger.bind(order_id=order_id, user_id=user_id)
    
    log.info("processing_order_started")
    
    try:
        # Process order
        amount = calculate_total(order_id)
        log.info("order_total_calculated", amount=amount)
        
        payment_result = process_payment(user_id, amount)
        log.info("payment_processed",
                 payment_id=payment_result['id'],
                 status=payment_result['status'])
        
        log.info("processing_order_completed", duration_ms=123)
        
    except Exception as e:
        log.error("processing_order_failed",
                  error=str(e),
                  exc_info=True)
        raise

# Context manager for request logging
from contextvars import ContextVar
import uuid

request_id_var = ContextVar('request_id', default=None)

class RequestContext:
    def __init__(self):
        self.request_id = str(uuid.uuid4())
    
    def __enter__(self):
        request_id_var.set(self.request_id)
        structlog.contextvars.bind_contextvars(request_id=self.request_id)
        return self
    
    def __exit__(self, *args):
        structlog.contextvars.unbind_contextvars("request_id")
        request_id_var.set(None)

# Usage in request handler
async def handle_request(request):
    with RequestContext() as ctx:
        logger.info("request_received",
                    method=request.method,
                    path=request.path)
        # Process request
        logger.info("request_completed", status_code=200)
```

### Metrics with Prometheus

**Go Implementation:**
```go
package metrics

import (
    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "github.com/prometheus/client_golang/prometheus/promhttp"
    "net/http"
    "time"
)

var (
    httpRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests",
        },
        []string{"method", "endpoint", "status"},
    )

    httpRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "http_request_duration_seconds",
            Help:    "HTTP request latency in seconds",
            Buckets: prometheus.DefBuckets,
        },
        []string{"method", "endpoint"},
    )

    dbQueryDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "db_query_duration_seconds",
            Help:    "Database query latency in seconds",
            Buckets: []float64{.001, .005, .01, .025, .05, .1, .25, .5, 1, 2.5, 5, 10},
        },
        []string{"query_type", "table"},
    )

    activeConnections = promauto.NewGauge(
        prometheus.GaugeOpts{
            Name: "active_connections",
            Help: "Number of active connections",
        },
    )

    cacheHits = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "cache_hits_total",
            Help: "Total number of cache hits",
        },
    )

    cacheMisses = promauto.NewCounter(
        prometheus.CounterOpts{
            Name: "cache_misses_total",
            Help: "Total number of cache misses",
        },
    )
)

// Middleware to track HTTP metrics
func MetricsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()

        // Wrap response writer to capture status code
        wrapped := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}

        next.ServeHTTP(wrapped, r)

        duration := time.Since(start).Seconds()
        
        httpRequestsTotal.WithLabelValues(
            r.Method,
            r.URL.Path,
            http.StatusText(wrapped.statusCode),
        ).Inc()

        httpRequestDuration.WithLabelValues(
            r.Method,
            r.URL.Path,
        ).Observe(duration)
    })
}

type responseWriter struct {
    http.ResponseWriter
    statusCode int
}

func (rw *responseWriter) WriteHeader(code int) {
    rw.statusCode = code
    rw.ResponseWriter.WriteHeader(code)
}

// Track database operations
func TrackDBQuery(queryType, table string, fn func() error) error {
    start := time.Now()
    err := fn()
    duration := time.Since(start).Seconds()

    dbQueryDuration.WithLabelValues(queryType, table).Observe(duration)
    
    return err
}

// Setup metrics endpoint
func SetupMetrics() {
    http.Handle("/metrics", promhttp.Handler())
    go http.ListenAndServe(":9090", nil)
}
```

### Distributed Tracing

**Rust with OpenTelemetry:**
```rust
use opentelemetry::{
    global,
    trace::{Tracer, Span, SpanKind, Status},
    KeyValue,
};
use opentelemetry_sdk::{
    trace::{self, RandomIdGenerator, Sampler},
    Resource,
};
use opentelemetry_jaeger::new_agent_pipeline;
use tracing::{info, instrument};
use tracing_subscriber::{layer::SubscriberExt, Registry};

async fn init_tracer() -> Result<(), Box<dyn std::error::Error>> {
    let tracer = new_agent_pipeline()
        .with_service_name("my-service")
        .with_trace_config(
            trace::config()
                .with_sampler(Sampler::AlwaysOn)
                .with_id_generator(RandomIdGenerator::default())
                .with_resource(Resource::new(vec![
                    KeyValue::new("service.name", "my-backend"),
                    KeyValue::new("service.version", "1.0.0"),
                ])),
        )
        .install_batch(opentelemetry::runtime::Tokio)?;

    let telemetry = tracing_opentelemetry::layer().with_tracer(tracer);
    let subscriber = Registry::default().with(telemetry);
    tracing::subscriber::set_global_default(subscriber)?;

    Ok(())
}

#[instrument(
    name = "process_order",
    skip(db, cache),
    fields(
        order_id = %order_id,
        user_id = %user_id
    )
)]
async fn process_order(
    order_id: String,
    user_id: String,
    db: &Database,
    cache: &Cache,
) -> Result<Order, Error> {
    info!("Starting order processing");

    // Check cache
    let order = check_cache(&cache, &order_id).await?;
    
    // Query database
    let user = fetch_user(db, &user_id).await?;
    
    // Process payment
    let payment = process_payment(&order, &user).await?;
    
    info!("Order processed successfully");
    Ok(order)
}

#[instrument(name = "check_cache", skip(cache))]
async fn check_cache(cache: &Cache, order_id: &str) -> Result<Option<Order>, Error> {
    let tracer = global::tracer("my-service");
    let mut span = tracer.start("cache_lookup");
    
    span.set_attribute(KeyValue::new("cache.key", order_id.to_string()));
    
    let result = cache.get(order_id).await;
    
    match &result {
        Ok(Some(_)) => {
            span.set_attribute(KeyValue::new("cache.hit", true));
        }
        Ok(None) => {
            span.set_attribute(KeyValue::new("cache.hit", false));
        }
        Err(e) => {
            span.set_status(Status::error(e.to_string()));
        }
    }
    
    span.end();
    result
}

#[instrument(name = "fetch_user", skip(db))]
async fn fetch_user(db: &Database, user_id: &str) -> Result<User, Error> {
    let tracer = global::tracer("my-service");
    let mut span = tracer.start_with_context("db_query", &Context::current());
    
    span.set_attribute(KeyValue::new("db.system", "postgresql"));
    span.set_attribute(KeyValue::new("db.operation", "SELECT"));
    span.set_attribute(KeyValue::new("db.table", "users"));
    
    let result = db.query_user(user_id).await;
    
    if let Err(e) = &result {
        span.set_status(Status::error(e.to_string()));
    }
    
    span.end();
    result
}
```

## 12. Testing Strategies

### Unit Testing

**Python with pytest:**
```python
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

# Test fixtures
@pytest.fixture
def mock_database():
    db = Mock()
    db.query = AsyncMock()
    return db

@pytest.fixture
def mock_cache():
    cache = Mock()
    cache.get = AsyncMock()
    cache.set = AsyncMock()
    return cache

@pytest.fixture
def sample_user():
    return {
        "id": 1,
        "username": "testuser",
        "email": "test@example.com",
        "created_at": datetime.now()
    }

# Test class
class TestUserService:
    @pytest.mark.asyncio
    async def test_get_user_from_cache(self, mock_database, mock_cache, sample_user):
        # Arrange
        mock_cache.get.return_value = sample_user
        service = UserService(mock_database, mock_cache)
        
        # Act
        result = await service.get_user(1)
        
        # Assert
        assert result == sample_user
        mock_cache.get.assert_called_once_with("user:1")
        mock_database.query.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_user_cache_miss(self, mock_database, mock_cache, sample_user):
        # Arrange
        mock_cache.get.return_value = None
        mock_database.query.return_value = sample_user
        service = UserService(mock_database, mock_cache)
        
        # Act
        result = await service.get_user(1)
        
        # Assert
        assert result == sample_user
        mock_cache.get.assert_called_once_with("user:1")
        mock_database.query.assert_awaited_once_with("SELECT * FROM users WHERE id = $1", (1,))
        mock_cache.set.assert_awaited_once_with("user:1", sample_user, ttl=3600)
```
