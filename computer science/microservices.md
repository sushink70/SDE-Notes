# Comprehensive Microservices Guide: Go, Python, Rust

## 1. Core Microservices Patterns

### Service Communication Patterns

#### **REST API Communication**

**Go Implementation**
```go
// With net/http (standard library)
package main

import (
    "encoding/json"
    "log"
    "net/http"
)

type User struct {
    ID   string `json:"id"`
    Name string `json:"name"`
}

func main() {
    http.HandleFunc("/users", getUsers)
    log.Fatal(http.ListenAndServe(":8080", nil))
}

func getUsers(w http.ResponseWriter, r *http.Request) {
    users := []User{{ID: "1", Name: "Alice"}}
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}
```

**Without proper error handling - INCORRECT:**
```go
func getUsersWrong(w http.ResponseWriter, r *http.Request) {
    users := fetchUsers() // might fail
    json.NewEncoder(w).Encode(users) // ignores error
}
```

**Errors:** Silent failures, no status codes, panic on nil pointers
**Warning:** Production crashes, data corruption

**Correct with error handling:**
```go
func getUsersCorrect(w http.ResponseWriter, r *http.Request) {
    users, err := fetchUsers()
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    if err := json.NewEncoder(w).Encode(users); err != nil {
        log.Printf("encoding error: %v", err)
    }
}
```

**Python Implementation**
```python
# With Flask
from flask import Flask, jsonify
import logging

app = Flask(__name__)

@app.route('/users')
def get_users():
    try:
        users = [{"id": "1", "name": "Alice"}]
        return jsonify(users), 200
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(port=8080)
```

**Without error handling - INCORRECT:**
```python
@app.route('/users')
def get_users_wrong():
    users = fetch_users()  # might fail
    return jsonify(users)  # unhandled exception
```

**Errors:** Unhandled exceptions crash the service
**Warning:** 500 errors with stack traces exposed to clients

**Rust Implementation**
```rust
// With actix-web
use actix_web::{web, App, HttpResponse, HttpServer, Result};
use serde::{Deserialize, Serialize};

#[derive(Serialize, Deserialize)]
struct User {
    id: String,
    name: String,
}

async fn get_users() -> Result<HttpResponse> {
    let users = vec![User {
        id: "1".to_string(),
        name: "Alice".to_string(),
    }];
    Ok(HttpResponse::Ok().json(users))
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    HttpServer::new(|| {
        App::new().route("/users", web::get().to(get_users))
    })
    .bind("127.0.0.1:8080")?
    .run()
    .await
}
```

**Benefit:** Rust's type system prevents common errors at compile time

---

## 2. Service Discovery

### **Consul Integration**

**Go with Consul**
```go
package main

import (
    "fmt"
    "github.com/hashicorp/consul/api"
)

func registerService() error {
    config := api.DefaultConfig()
    client, err := api.NewClient(config)
    if err != nil {
        return err
    }

    registration := &api.AgentServiceRegistration{
        ID:      "user-service-1",
        Name:    "user-service",
        Port:    8080,
        Address: "localhost",
        Check: &api.AgentServiceCheck{
            HTTP:     "http://localhost:8080/health",
            Interval: "10s",
            Timeout:  "3s",
        },
    }

    return client.Agent().ServiceRegister(registration)
}
```

**Without service discovery - INCORRECT:**
```go
// Hardcoded service addresses
const userServiceURL = "http://localhost:8080"
const orderServiceURL = "http://localhost:8081"
```

**Errors:** Service moves, application breaks; no load balancing
**Warning:** Manual configuration hell, no failover

**Python with Consul**
```python
import consul
import requests

def register_service():
    c = consul.Consul(host='localhost', port=8500)
    c.agent.service.register(
        name='user-service',
        service_id='user-service-1',
        port=8080,
        check=consul.Check.http('http://localhost:8080/health', '10s')
    )

def discover_service(service_name):
    c = consul.Consul()
    index, services = c.health.service(service_name, passing=True)
    if services:
        return f"http://{services[0]['Service']['Address']}:{services[0]['Service']['Port']}"
    return None
```

---

## 3. Circuit Breaker Pattern

### **Preventing Cascading Failures**

**Go with Circuit Breaker**
```go
package main

import (
    "errors"
    "github.com/sony/gobreaker"
    "time"
)

var cb *gobreaker.CircuitBreaker

func init() {
    settings := gobreaker.Settings{
        Name:        "UserService",
        MaxRequests: 3,
        Interval:    time.Second * 10,
        Timeout:     time.Second * 60,
        ReadyToTrip: func(counts gobreaker.Counts) bool {
            return counts.ConsecutiveFailures > 5
        },
    }
    cb = gobreaker.NewCircuitBreaker(settings)
}

func callExternalService() (interface{}, error) {
    return cb.Execute(func() (interface{}, error) {
        // Actual service call
        return makeHTTPRequest()
    })
}
```

**Without circuit breaker - INCORRECT:**
```go
func callServiceWrong() error {
    for i := 0; i < 1000; i++ {
        makeHTTPRequest() // keeps failing, exhausts resources
    }
    return nil
}
```

**Errors:** Resource exhaustion, cascading failures across services
**Warning:** Entire system collapse under load

**Python Circuit Breaker**
```python
from pybreaker import CircuitBreaker

breaker = CircuitBreaker(fail_max=5, timeout_duration=60)

@breaker
def call_external_service():
    response = requests.get('http://external-service/api')
    response.raise_for_status()
    return response.json()
```

**Rust Circuit Breaker**
```rust
use failsafe::{CircuitBreaker, Config, backoff};
use std::time::Duration;

async fn call_with_breaker() {
    let circuit_breaker = Config::new()
        .failure_rate_threshold(50.0)
        .wait_duration_in_open_state(Duration::from_secs(60))
        .build();

    match circuit_breaker.call(make_request()).await {
        Ok(result) => println!("Success: {:?}", result),
        Err(e) => eprintln!("Circuit open or failed: {:?}", e),
    }
}
```

**Benefit:** Prevents cascading failures, faster recovery, resource protection

---

## 4. Database per Service Pattern

**Go with PostgreSQL**
```go
package main

import (
    "database/sql"
    _ "github.com/lib/pq"
)

type UserRepository struct {
    db *sql.DB
}

func NewUserRepository(connStr string) (*UserRepository, error) {
    db, err := sql.Open("postgres", connStr)
    if err != nil {
        return nil, err
    }
    
    db.SetMaxOpenConns(25)
    db.SetMaxIdleConns(5)
    
    return &UserRepository{db: db}, nil
}

func (r *UserRepository) GetUser(id string) (*User, error) {
    var user User
    err := r.db.QueryRow("SELECT id, name FROM users WHERE id = $1", id).Scan(&user.ID, &user.Name)
    return &user, err
}
```

**Without connection pooling - INCORRECT:**
```go
func getUserWrong(id string) (*User, error) {
    db, _ := sql.Open("postgres", connStr) // new connection every call
    defer db.Close()
    // query...
}
```

**Errors:** Connection exhaustion, performance degradation
**Warning:** Database crashes under load

**Python with SQLAlchemy**
```python
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(String, primary_key=True)
    name = Column(String)

engine = create_engine('postgresql://user:pass@localhost/userdb', pool_size=25, max_overflow=10)
Session = sessionmaker(bind=engine)

def get_user(user_id):
    session = Session()
    try:
        return session.query(User).filter_by(id=user_id).first()
    finally:
        session.close()
```

**Rust with SQLx**
```rust
use sqlx::{PgPool, FromRow};

#[derive(FromRow)]
struct User {
    id: String,
    name: String,
}

async fn get_user(pool: &PgPool, id: &str) -> Result<User, sqlx::Error> {
    sqlx::query_as::<_, User>("SELECT id, name FROM users WHERE id = $1")
        .bind(id)
        .fetch_one(pool)
        .await
}

async fn create_pool() -> PgPool {
    PgPool::connect("postgres://user:pass@localhost/userdb")
        .await
        .expect("Failed to create pool")
}
```

---

## 5. Event-Driven Architecture

### **Message Queue Integration**

**Go with RabbitMQ**
```go
package main

import (
    "github.com/streadway/amqp"
    "log"
)

type EventPublisher struct {
    conn    *amqp.Connection
    channel *amqp.Channel
}

func NewEventPublisher(url string) (*EventPublisher, error) {
    conn, err := amqp.Dial(url)
    if err != nil {
        return nil, err
    }
    
    ch, err := conn.Channel()
    if err != nil {
        return nil, err
    }
    
    return &EventPublisher{conn: conn, channel: ch}, nil
}

func (p *EventPublisher) PublishUserCreated(userID string) error {
    return p.channel.Publish(
        "events",    // exchange
        "user.created", // routing key
        false,
        false,
        amqp.Publishing{
            ContentType: "application/json",
            Body:        []byte(`{"user_id":"` + userID + `"}`),
        },
    )
}
```

**Without acknowledgments - INCORRECT:**
```go
func consumeWrong(msgs <-chan amqp.Delivery) {
    for msg := range msgs {
        processMessage(msg) // might fail, message lost
    }
}
```

**Errors:** Message loss, no retry mechanism
**Warning:** Data inconsistency across services

**Correct with ACK:**
```go
func consumeCorrect(msgs <-chan amqp.Delivery) {
    for msg := range msgs {
        if err := processMessage(msg); err != nil {
            msg.Nack(false, true) // requeue
        } else {
            msg.Ack(false)
        }
    }
}
```

**Python with Kafka**
```python
from kafka import KafkaProducer, KafkaConsumer
import json

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

def publish_event(topic, event):
    producer.send(topic, value=event)
    producer.flush()

consumer = KafkaConsumer(
    'user-events',
    bootstrap_servers='localhost:9092',
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    enable_auto_commit=False
)

for message in consumer:
    try:
        process_event(message.value)
        consumer.commit()
    except Exception as e:
        print(f"Error: {e}")
```

**Rust with rdkafka**
```rust
use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;

async fn publish_event(topic: &str, payload: &str) {
    let producer: FutureProducer = ClientConfig::new()
        .set("bootstrap.servers", "localhost:9092")
        .create()
        .expect("Producer creation failed");

    producer
        .send(
            FutureRecord::to(topic).payload(payload).key("user"),
            Duration::from_secs(0),
        )
        .await
        .expect("Failed to send");
}
```

---

## 6. API Gateway Pattern

**Go Gateway with Chi Router**
```go
package main

import (
    "github.com/go-chi/chi/v5"
    "github.com/go-chi/chi/v5/middleware"
    "net/http"
    "net/http/httputil"
    "net/url"
)

func main() {
    r := chi.NewRouter()
    r.Use(middleware.Logger)
    r.Use(middleware.RateLimit(100))
    
    userServiceURL, _ := url.Parse("http://localhost:8081")
    orderServiceURL, _ := url.Parse("http://localhost:8082")
    
    r.Handle("/api/users/*", httputil.NewSingleHostReverseProxy(userServiceURL))
    r.Handle("/api/orders/*", httputil.NewSingleHostReverseProxy(orderServiceURL))
    
    http.ListenAndServe(":8080", r)
}
```

**Without rate limiting - INCORRECT:**
```go
func gatewayWrong() {
    http.Handle("/api/", proxy) // no protection
    http.ListenAndServe(":8080", nil)
}
```

**Errors:** DDoS vulnerability, service overwhelm
**Warning:** Complete service outage

**Python Gateway with FastAPI**
```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
)

@app.api_route("/api/users/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy_users(request: Request, path: str):
    async with httpx.AsyncClient() as client:
        url = f"http://localhost:8081/{path}"
        response = await client.request(
            method=request.method,
            url=url,
            headers=dict(request.headers),
            content=await request.body()
        )
        return response.json()
```

---

## 7. Health Checks & Observability

**Go Health Endpoint**
```go
type HealthCheck struct {
    db *sql.DB
}

func (h *HealthCheck) Handler(w http.ResponseWriter, r *http.Request) {
    status := map[string]string{"status": "healthy"}
    
    if err := h.db.Ping(); err != nil {
        status["status"] = "unhealthy"
        status["database"] = "down"
        w.WriteHeader(http.StatusServiceUnavailable)
    }
    
    json.NewEncoder(w).Encode(status)
}
```

**Without health checks - INCORRECT:**
```go
// No health endpoint
// Load balancer can't detect failures
```

**Errors:** Traffic routed to dead instances
**Warning:** Cascading failures

**Python Health Check**
```python
@app.get("/health")
async def health_check():
    try:
        # Check database
        await db.execute("SELECT 1")
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}, 503
```

**Rust Health Check**
```rust
async fn health_check(pool: web::Data<PgPool>) -> HttpResponse {
    match sqlx::query("SELECT 1").execute(pool.get_ref()).await {
        Ok(_) => HttpResponse::Ok().json(json!({"status": "healthy"})),
        Err(_) => HttpResponse::ServiceUnavailable().json(json!({"status": "unhealthy"})),
    }
}
```

---

## 8. Distributed Tracing

**Go with OpenTelemetry**
```go
import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/trace"
)

func handleRequest(w http.ResponseWriter, r *http.Request) {
    ctx := r.Context()
    tracer := otel.Tracer("user-service")
    
    ctx, span := tracer.Start(ctx, "handle-request")
    defer span.End()
    
    user, err := fetchUser(ctx, "123")
    if err != nil {
        span.RecordError(err)
    }
}
```

**Without tracing - INCORRECT:**
```go
func handleRequestWrong(w http.ResponseWriter, r *http.Request) {
    fetchUser("123") // no context, can't trace
}
```

**Errors:** Cannot debug cross-service issues
**Warning:** Mean time to resolution (MTTR) increases dramatically

**Python with OpenTelemetry**
```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

tracer = trace.get_tracer(__name__)

@app.route('/users/<user_id>')
def get_user(user_id):
    with tracer.start_as_current_span("get_user"):
        user = fetch_user(user_id)
        return jsonify(user)

FlaskInstrumentor().instrument_app(app)
```

---

## 9. Configuration Management

**Go with Environment Variables**
```go
package config

import (
    "os"
    "strconv"
)

type Config struct {
    Port       int
    DBHost     string
    DBPassword string
}

func Load() (*Config, error) {
    port, _ := strconv.Atoi(getEnv("PORT", "8080"))
    
    return &Config{
        Port:       port,
        DBHost:     getEnv("DB_HOST", "localhost"),
        DBPassword: getEnv("DB_PASSWORD", ""),
    }, nil
}

func getEnv(key, defaultVal string) string {
    if value := os.Getenv(key); value != "" {
        return value
    }
    return defaultVal
}
```

**Hardcoded configuration - INCORRECT:**
```go
const (
    dbHost = "localhost"
    dbPassword = "admin123" // security risk
)
```

**Errors:** Secrets in code, can't change without rebuild
**Warning:** Security breaches, deployment inflexibility

**Python with Pydantic**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    port: int = 8080
    db_host: str
    db_password: str
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Rust with config crate**
```rust
use config::{Config, ConfigError, File};
use serde::Deserialize;

#[derive(Deserialize)]
struct Settings {
    port: u16,
    db_host: String,
    db_password: String,
}

fn load_config() -> Result<Settings, ConfigError> {
    Config::builder()
        .add_source(File::with_name("config"))
        .add_source(config::Environment::default())
        .build()?
        .try_deserialize()
}
```

---

## 10. Benefits Summary

### **With Microservices Patterns:**
- **Scalability**: Scale individual services independently
- **Fault Isolation**: One service failure doesn't crash entire system
- **Technology Flexibility**: Use best tool per service
- **Faster Deployment**: Deploy services independently
- **Team Autonomy**: Teams own specific services

### **Without Proper Implementation:**
- **Errors**: Cascading failures, data loss, security vulnerabilities
- **Warnings**: System-wide outages, poor performance, debugging nightmares
- **Consequences**: Lost revenue, customer dissatisfaction, technical debt

### **Language-Specific Control:**

**Go:**
- Explicit error handling forces you to handle failures
- Goroutines for concurrent service calls
- Static typing prevents runtime errors
- Compiled binary for easy deployment

**Python:**
- Dynamic typing for rapid development
- Rich ecosystem (Flask, FastAPI, Django)
- Easier async/await patterns
- Slower performance, needs careful optimization

**Rust:**
- Memory safety without garbage collection
- Zero-cost abstractions
- Compile-time guarantees prevent many bugs
- Steeper learning curve but superior reliability

### **Key Takeaway:**
Microservices require proper patterns (circuit breakers, service discovery, health checks, tracing) to avoid creating a distributed monolith. Each language offers different trade-offs in safety, performance, and developer productivity.

I'll create a comprehensive microservices guide covering Go, Python, and Rust with practical implementations focusing on key concepts, patterns, and comparisons.I've created a comprehensive guide covering:

1. **REST API patterns** - correct/incorrect implementations with error handling
2. **Service Discovery** (Consul) - benefits of dynamic discovery vs hardcoded URLs
3. **Circuit Breakers** - preventing cascading failures
4. **Database per Service** - connection pooling and isolation
5. **Event-Driven Architecture** - message queues with proper acknowledgments
6. **API Gateway** - centralized routing with rate limiting
7. **Health Checks** - load balancer integration
8. **Distributed Tracing** - debugging across services
9. **Configuration Management** - secure settings handling
10. **Benefits comparison** - with/without proper patterns, language-specific strengths

Each section shows working implementations in all three languages, common mistakes, their consequences, and the control/benefits you gain by using proper patterns.