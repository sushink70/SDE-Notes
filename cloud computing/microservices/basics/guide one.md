# Microservices: A Complete Engineering Guide
## From Linux Kernel Internals to Cloud-Scale Production Systems - security focused development. 

> Reference: *Building Microservices: Designing Fine-Grained Systems* — Sam Newman (O'Reilly)  
> Kernel Source: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git  
> Kernel Version Context: v6.8+ unless stated otherwise

---

## Table of Contents

1. [Philosophy & First Principles](#1-philosophy--first-principles)
2. [Service Decomposition & Domain Modeling](#2-service-decomposition--domain-modeling)
3. [Linux Kernel Isolation Primitives](#3-linux-kernel-isolation-primitives)
4. [Inter-Process & Inter-Service Communication](#4-inter-process--inter-service-communication)
5. [Networking Protocol Stack Deep Dive](#5-networking-protocol-stack-deep-dive)
6. [Service-to-Service Communication Patterns](#6-service-to-service-communication-patterns)
7. [Data Management & Persistence Patterns](#7-data-management--persistence-patterns)
8. [Service Discovery & Load Balancing](#8-service-discovery--load-balancing)
9. [Security Architecture](#9-security-architecture)
10. [Observability: Tracing, Metrics, Logging](#10-observability-tracing-metrics-logging)
11. [Container Internals & Orchestration](#11-container-internals--orchestration)
12. [Cloud Infrastructure & Deployment](#12-cloud-infrastructure--deployment)
13. [Resilience Patterns](#13-resilience-patterns)
14. [Testing Strategies](#14-testing-strategies)
15. [Event-Driven Architecture & CQRS](#15-event-driven-architecture--cqrs)

---

## 1. Philosophy & First Principles

### 1.1 What is a Microservice?

A microservice is a **cohesive, independently deployable unit of functionality** organized around a business capability. The definition per Sam Newman:

> *"Microservices are small, autonomous services that work together, modeled around a business domain."*

The operative constraints are:
- **Small**: Bounded by a single team's ownership (Two-Pizza Rule: 6-8 engineers)
- **Autonomous**: Can be deployed, scaled, and failed independently
- **Business domain aligned**: Not technical layer aligned (anti-pattern: "database service")

### 1.2 Monolith → SOA → Microservices Evolution

```
MONOLITH                    SOA                      MICROSERVICES
+-----------------+         +------------------+      +--------+  +--------+
|  Web Layer      |         | ESB (Enterprise  |      | Order  |  | User   |
|  Business Logic |  ---->  | Service Bus)     | ---> | Svc    |  | Svc    |
|  Data Layer     |         | +Service A       |      +--------+  +--------+
|  [Single DB]    |         | +Service B       |      +--------+  +--------+
+-----------------+         | +Service C       |      | Pay    |  | Notify |
                            +------------------+      | Svc    |  | Svc    |
                                                      +--------+  +--------+
                                                      [Each has own DB/store]
```

**Key failure modes of each:**
- Monolith: Deployment coupling, scaling limitations, tech lock-in
- SOA/ESB: Smart bus = business logic leakage, the bus becomes a monolith
- Microservices: Distributed system complexity, network failures, eventual consistency

### 1.3 The CAP Theorem in Microservices Context

```
               Consistency (C)
                     /\
                    /  \
                   /    \
                  /  CA  \
                 /--------\
                /    |     \
               / CP  |  AP  \
              /      |       \
             /-------+--------\
    Availability (A)    Partition Tolerance (P)

CA = Traditional RDBMS (single node)
CP = HBase, Zookeeper, etcd (prefer correctness over availability)
AP = Cassandra, CouchDB, DynamoDB (prefer availability over consistency)

In a microservices network: P is not optional (networks always partition).
You choose between C and A per-service, per-operation.
```

### 1.4 Twelve-Factor App Principles (Kernel-aware mapping)

| Factor | Description | Linux Mechanism |
|--------|-------------|-----------------|
| Codebase | One repo, many deploys | git, OCI images |
| Dependencies | Explicit manifest | ld-linux, rpath, containers |
| Config | Store in environment | `environ[]`, `/proc/<pid>/environ` |
| Backing services | Treat as attached resources | Unix domain sockets, TCP |
| Build/release/run | Strict separation | OCI layers, immutable rootfs |
| Processes | Stateless, share-nothing | `clone()`, namespaces |
| Port binding | Self-contained HTTP | `bind()`, `SO_REUSEPORT` |
| Concurrency | Scale via process model | `fork()`, cgroups CPU shares |
| Disposability | Fast startup/shutdown | `SIGTERM` handling, init systems |
| Dev/prod parity | Keep environments similar | containerization |
| Logs | Treat as event streams | `stdout` → journald → aggregator |
| Admin processes | One-off admin tasks | `nsenter`, `kubectl exec` |

---

## 2. Service Decomposition & Domain Modeling

### 2.1 Domain-Driven Design (DDD) Fundamentals

DDD is the primary decomposition strategy for microservices. Key building blocks:

```
STRATEGIC DDD
=============

+-----------------------------+    +-----------------------------+
|   Bounded Context: Orders   |    |  Bounded Context: Shipping  |
|                             |    |                             |
|  +--------+  +----------+  |    |  +---------+  +----------+  |
|  | Order  |  | LineItem |  |    |  | Package |  | Route    |  |
|  | Agg.   |  | Entity   |  |    |  | Agg.    |  | Value Obj|  |
|  +--------+  +----------+  |    |  +---------+  +----------+  |
|       |                     |    |       |                     |
|  [OrderRepository]          |    |  [PackageRepository]        |
+-----------------------------+    +-----------------------------+
            |                                  |
            +---------> Context Map <----------+
                        (Anti-Corruption Layer)
```

**Aggregate**: Cluster of entities treated as a unit. Single transactional boundary.  
**Entity**: Has identity that persists over time (OrderID=123 is always "that order")  
**Value Object**: Immutable, defined by its attributes (Money{100, USD})  
**Bounded Context**: Explicit boundary within which a model applies  
**Context Map**: Relationship between bounded contexts

### 2.2 Decomposition Strategies

#### By Business Capability

```
E-COMMERCE CAPABILITY MAP
==========================

+----------------------------------------------------------+
|                    Customer-Facing                        |
|  [Product Catalog]  [Search]  [Reviews]  [Pricing]       |
+----------------------------------------------------------+
|                    Order Management                       |
|  [Cart]  [Checkout]  [Orders]  [Fulfillment]             |
+----------------------------------------------------------+
|                    Customer Management                    |
|  [Accounts]  [Profiles]  [Authentication]  [Addresses]   |
+----------------------------------------------------------+
|                    Financial                              |
|  [Payments]  [Invoicing]  [Refunds]  [Tax]               |
+----------------------------------------------------------+
|                    Logistics                              |
|  [Inventory]  [Warehouse]  [Shipping]  [Returns]         |
+----------------------------------------------------------+
```

Each box above is a candidate microservice. The boundaries come from the business, not the tech.

#### By Subdomain (Core/Supporting/Generic)

```
SUBDOMAIN CLASSIFICATION
========================

Core Subdomain         Supporting Subdomain    Generic Subdomain
(Competitive edge,     (Necessary, not         (Commodity,
 build in-house)       differentiating,         buy/use OSS)
                       build in-house)

[Pricing Engine]       [Order Processing]      [Email Notifications]
[Recommendation]       [Inventory Mgmt]        [Authentication (OAuth)]
[Risk Scoring]         [Returns Mgmt]          [Logging/Monitoring]
```

**Rule**: Never outsource your core subdomains. Buy generic. Build supporting.

### 2.3 The Strangler Fig Pattern

Migration path from monolith to microservices:

```
PHASE 1: Intercept
===================
         HTTP
Client ---------> [Facade/Proxy]
                        |
                        v
                  [Monolith]

PHASE 2: Extract Service
=========================
         HTTP
Client ---------> [Facade/Proxy]
                    /        \
                   /          \
            [New Svc]    [Monolith]
         (new feature)  (legacy features)

PHASE 3: Redirect
==================
         HTTP
Client ---------> [Facade/Proxy]
                    /        \
                   /          \
         [New Svc]         [Monolith]
      (migrated feature,   (remaining,
       strangled branch)    shrinking)

PHASE 4: Complete
==================
Client ---------> [API Gateway] ---------> [Microservices]
                                           [No Monolith]
```

In Linux terms: The Facade is an `iptables`/`nftables` DNAT rule or an nginx `proxy_pass` that redirects traffic.

### 2.4 Service Granularity

**Too fine-grained (nanoservices):**
```
[GetUser] [SetUserName] [SetUserEmail] [DeleteUser]
     |           |              |            |
     +-----all---+----call------+----each----+
                    other for basic ops

Problem: chatty network, distributed transaction hell
```

**Too coarse-grained (minimonolith):**
```
[UserService]
  - manages users
  - manages authentication
  - manages authorization
  - manages sessions
  - manages preferences
  - manages notifications
  - manages billing profiles

Problem: still deployment coupling, single team bottleneck
```

**Just right:**
```
[UserService]           [AuthService]          [BillingService]
  - CRUD user profile     - sessions             - payment methods
  - preferences           - MFA                  - invoices
  - addresses             - OAuth tokens          - subscriptions

Single team owns each. ~1000-5000 LOC per service is a reasonable heuristic.
```

### 2.5 Go Implementation: Service Skeleton

```go
// cmd/ordersvc/main.go
// Order Service — Clean Architecture skeleton
package main

import (
    "context"
    "fmt"
    "net"
    "net/http"
    "os"
    "os/signal"
    "syscall"
    "time"

    "go.opentelemetry.io/otel"
    "go.uber.org/zap"
    "google.golang.org/grpc"

    "github.com/yourorg/ordersvc/internal/adapters/grpchandler"
    "github.com/yourorg/ordersvc/internal/adapters/httphandler"
    "github.com/yourorg/ordersvc/internal/adapters/repository"
    "github.com/yourorg/ordersvc/internal/domain"
    "github.com/yourorg/ordersvc/internal/ports"
)

// Hexagonal Architecture (Ports & Adapters)
//
//  +--------------------------------------------------+
//  |                  ORDER SERVICE                    |
//  |  +-----------+  +-----------+  +-------------+  |
//  |  | HTTP Port |  | gRPC Port |  | Events Port |  |
//  |  +-----------+  +-----------+  +-------------+  |
//  |        |               |               |         |
//  |  +-----v---------------v---------------v------+  |
//  |  |            Application Layer               |  |
//  |  |  OrderUseCase, CreateOrder, ListOrders     |  |
//  |  +---------------------------------------------+  |
//  |  |            Domain Layer                    |  |
//  |  |  Order, OrderItem, OrderStatus, Events     |  |
//  |  +---------------------------------------------+  |
//  |  +-----------+  +-----------+  +-------------+  |
//  |  | Postgres  |  | Redis     |  | Kafka       |  |
//  |  | Adapter   |  | Adapter   |  | Adapter     |  |
//  |  +-----------+  +-----------+  +-------------+  |
//  +--------------------------------------------------+

func main() {
    logger, _ := zap.NewProduction()
    defer logger.Sync()

    cfg := loadConfig()

    // Initialize tracing
    tp := initTracer(cfg.JaegerEndpoint)
    defer func() { _ = tp.Shutdown(context.Background()) }()
    otel.SetTracerProvider(tp)

    // Initialize repositories (adapters)
    orderRepo, err := repository.NewPostgresOrderRepository(cfg.DatabaseURL)
    if err != nil {
        logger.Fatal("failed to connect to database", zap.Error(err))
    }
    defer orderRepo.Close()

    // Initialize domain services
    inventoryClient := ports.NewInventoryClient(cfg.InventoryServiceAddr)
    pricingClient   := ports.NewPricingClient(cfg.PricingServiceAddr)

    // Initialize use cases
    orderUseCase := domain.NewOrderUseCase(
        orderRepo,
        inventoryClient,
        pricingClient,
        logger,
    )

    // Start HTTP server
    httpSrv := &http.Server{
        Addr:         fmt.Sprintf(":%d", cfg.HTTPPort),
        Handler:      httphandler.NewRouter(orderUseCase, logger),
        ReadTimeout:  10 * time.Second,
        WriteTimeout: 10 * time.Second,
        IdleTimeout:  60 * time.Second,
    }

    // Start gRPC server
    lis, err := net.Listen("tcp", fmt.Sprintf(":%d", cfg.GRPCPort))
    if err != nil {
        logger.Fatal("failed to listen", zap.Error(err))
    }
    grpcSrv := grpc.NewServer(
        grpc.UnaryInterceptor(grpchandler.UnaryInterceptor(logger)),
        grpc.StreamInterceptor(grpchandler.StreamInterceptor(logger)),
    )
    grpchandler.RegisterOrderServiceServer(grpcSrv, orderUseCase)

    // Graceful shutdown
    ctx, stop := signal.NotifyContext(context.Background(),
        syscall.SIGINT, syscall.SIGTERM)
    defer stop()

    go func() {
        logger.Info("HTTP server starting", zap.Int("port", cfg.HTTPPort))
        if err := httpSrv.ListenAndServe(); err != http.ErrServerClosed {
            logger.Fatal("HTTP server error", zap.Error(err))
        }
    }()

    go func() {
        logger.Info("gRPC server starting", zap.Int("port", cfg.GRPCPort))
        if err := grpcSrv.Serve(lis); err != nil {
            logger.Fatal("gRPC server error", zap.Error(err))
        }
    }()

    <-ctx.Done()
    logger.Info("shutdown signal received")

    shutdownCtx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
    defer cancel()

    if err := httpSrv.Shutdown(shutdownCtx); err != nil {
        logger.Error("HTTP shutdown error", zap.Error(err))
    }
    grpcSrv.GracefulStop()
    logger.Info("server exited cleanly")
}
```

```go
// internal/domain/order.go
// Domain layer: pure business logic, no framework dependencies
package domain

import (
    "errors"
    "time"
    "github.com/google/uuid"
)

// OrderStatus is a value object
type OrderStatus string

const (
    OrderStatusPending    OrderStatus = "PENDING"
    OrderStatusConfirmed  OrderStatus = "CONFIRMED"
    OrderStatusShipping   OrderStatus = "SHIPPING"
    OrderStatusDelivered  OrderStatus = "DELIVERED"
    OrderStatusCancelled  OrderStatus = "CANCELLED"
)

// Money value object: immutable, comparable by value
type Money struct {
    Amount   int64  // cents, avoid float
    Currency string // ISO 4217
}

func (m Money) Add(other Money) (Money, error) {
    if m.Currency != other.Currency {
        return Money{}, errors.New("currency mismatch")
    }
    return Money{Amount: m.Amount + other.Amount, Currency: m.Currency}, nil
}

// OrderItem entity
type OrderItem struct {
    ProductID string
    Quantity  int
    UnitPrice Money
}

func (i OrderItem) Subtotal() Money {
    return Money{Amount: i.UnitPrice.Amount * int64(i.Quantity), Currency: i.UnitPrice.Currency}
}

// Order aggregate root
type Order struct {
    ID         string
    CustomerID string
    Items      []OrderItem
    Status     OrderStatus
    Total      Money
    CreatedAt  time.Time
    UpdatedAt  time.Time

    // Domain events — not persisted, dispatched after commit
    events []DomainEvent
}

func NewOrder(customerID string, items []OrderItem) (*Order, error) {
    if len(items) == 0 {
        return nil, errors.New("order must have at least one item")
    }
    if customerID == "" {
        return nil, errors.New("customerID is required")
    }

    var total Money
    for i, item := range items {
        if i == 0 {
            total = item.Subtotal()
            continue
        }
        var err error
        total, err = total.Add(item.Subtotal())
        if err != nil {
            return nil, err
        }
    }

    o := &Order{
        ID:         uuid.New().String(),
        CustomerID: customerID,
        Items:      items,
        Status:     OrderStatusPending,
        Total:      total,
        CreatedAt:  time.Now().UTC(),
        UpdatedAt:  time.Now().UTC(),
    }

    // Record domain event
    o.AddEvent(OrderCreatedEvent{
        OrderID:    o.ID,
        CustomerID: o.CustomerID,
        Total:      o.Total,
        OccurredAt: o.CreatedAt,
    })

    return o, nil
}

func (o *Order) Confirm() error {
    if o.Status != OrderStatusPending {
        return fmt.Errorf("cannot confirm order in status %s", o.Status)
    }
    o.Status = OrderStatusConfirmed
    o.UpdatedAt = time.Now().UTC()
    o.AddEvent(OrderConfirmedEvent{OrderID: o.ID, OccurredAt: o.UpdatedAt})
    return nil
}

func (o *Order) Cancel(reason string) error {
    if o.Status == OrderStatusDelivered || o.Status == OrderStatusCancelled {
        return fmt.Errorf("cannot cancel order in status %s", o.Status)
    }
    o.Status = OrderStatusCancelled
    o.UpdatedAt = time.Now().UTC()
    o.AddEvent(OrderCancelledEvent{OrderID: o.ID, Reason: reason, OccurredAt: o.UpdatedAt})
    return nil
}

func (o *Order) AddEvent(e DomainEvent) { o.events = append(o.events, e) }
func (o *Order) PullEvents() []DomainEvent {
    evts := o.events
    o.events = nil
    return evts
}
```

---

## 3. Linux Kernel Isolation Primitives

Understanding microservice isolation requires deep knowledge of the kernel mechanisms containers are built on.

### 3.1 Linux Namespaces

Namespaces partition kernel resources. A process sees only the resources in its namespace.

```
NAMESPACE TYPES (kernel/nsproxy.c, include/linux/nsproxy.h)
============================================================

struct nsproxy {             /* One per process group sharing namespaces */
    atomic_t count;
    struct uts_namespace    *uts_ns;   /* hostname, domainname */
    struct ipc_namespace    *ipc_ns;   /* SysV IPC, POSIX MQ */
    struct mnt_namespace    *mnt_ns;   /* mount points (VFS) */
    struct pid_namespace    *pid_ns_for_children;
    struct net              *net_ns;   /* network stack */
    struct time_namespace   *time_ns;  /* clock offsets (v5.6+) */
    struct cgroup_namespace *cgroup_ns;/* cgroup root view */
    struct user_namespace   *user_ns;  /* UID/GID mapping */
};

NAMESPACE HIERARCHY
===================

Host Process (PID 1)
│
│  uts_ns: hostname="host"
│  net_ns: eth0, lo
│  pid_ns: PID 1
│  mnt_ns: /proc, /sys, /dev, /
│  user_ns: UID 0 = real UID 0
│
├── Container A (clone(CLONE_NEWUTS|CLONE_NEWNET|CLONE_NEWPID|...))
│   │  uts_ns: hostname="container-a"
│   │  net_ns: veth0 (172.17.0.2/16), lo
│   │  pid_ns: PID 1 (mapped to host PID 3421)
│   │  mnt_ns: /proc (container), overlayfs rootfs
│   │  user_ns: UID 0 = host UID 100000 (user ns mapping)
│   │
│   └── Process in Container A (PID 42 in container = 3463 on host)
│
└── Container B
    │  uts_ns: hostname="container-b"
    │  net_ns: veth0 (172.17.0.3/16), lo
    └── ...
```

**Kernel source files:**
- `kernel/nsproxy.c` — namespace proxy management
- `include/linux/nsproxy.h` — `struct nsproxy`
- `net/core/net_namespace.c` — network namespace lifecycle
- `kernel/pid_namespace.c` — PID namespace
- `fs/namespace.c` — mount namespace
- `kernel/user_namespace.c` — user namespace (UID mapping)

```c
/* Simplified: how clone(2) creates a new namespace */
/* kernel/fork.c: copy_process() -> copy_namespaces() */

int copy_namespaces(unsigned long flags, struct task_struct *tsk)
{
    struct nsproxy *old_ns = tsk->nsproxy;
    struct nsproxy *new_ns;

    /* If no CLONE_NEW* flags, share parent namespaces */
    if (!(flags & (CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC |
                   CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWUSER |
                   CLONE_NEWCGROUP | CLONE_NEWTIME))) {
        get_nsproxy(old_ns);
        return 0;
    }

    /* Allocate new nsproxy, copying or creating per flag */
    new_ns = create_new_namespaces(flags, tsk, user_ns, tsk->fs);
    if (IS_ERR(new_ns))
        return PTR_ERR(new_ns);

    tsk->nsproxy = new_ns;
    return 0;
}
```

**Userspace manipulation:**
```bash
# Create a new network namespace for a microservice
ip netns add svc-order

# Move a veth pair endpoint into it
ip link add veth-order type veth peer name veth-host
ip link set veth-order netns svc-order

# Configure inside the namespace
ip netns exec svc-order ip addr add 10.0.1.2/24 dev veth-order
ip netns exec svc-order ip link set veth-order up

# Run process in existing namespace
nsenter --net=/var/run/netns/svc-order --pid --mount -- /bin/ordersvc

# Inspect namespaces of a running process
ls -la /proc/$(pidof ordersvc)/ns/
# lrwxrwxrwx net -> net:[4026532345]
# lrwxrwxrwx pid -> pid:[4026532346]
```

### 3.2 Control Groups (cgroups v2)

cgroups enforce resource limits. In microservices, each service gets a cgroup subtree.

```
CGROUP V2 HIERARCHY (unified hierarchy, kernel >= 4.5, default >= 5.2)
=======================================================================

/sys/fs/cgroup/              (cgroup root)
├── system.slice/
│   ├── docker.service/
│   │   ├── container-abc123/   ← Order Service container
│   │   │   ├── cpu.max         "200000 100000" = 2 CPU cores
│   │   │   ├── memory.max      "268435456"     = 256MB
│   │   │   ├── io.max          "8:0 rbps=max wbps=104857600"
│   │   │   ├── pids.max        "512"
│   │   │   └── cpu.stat        (accounting)
│   │   │
│   │   └── container-def456/   ← Payment Service container
│   │       ├── cpu.max         "100000 100000" = 1 CPU core
│   │       ├── memory.max      "536870912"     = 512MB
│   │       └── ...
│   │
│   └── containerd.service/
│
└── user.slice/
```

**Key cgroup v2 controllers:**
- `cpu`: `cpu.max` = `$QUOTA $PERIOD`, `cpu.weight` (1–10000)
- `memory`: `memory.max`, `memory.high` (soft limit, triggers reclaim)
- `io`: `io.max` (BPS/IOPS limits per device)
- `pids`: `pids.max` (fork bomb protection)
- `cpuset`: `cpuset.cpus` (CPU affinity)

**Kernel source:**
- `kernel/cgroup/cgroup.c` — core cgroup implementation
- `kernel/cgroup/cgroup-v2.c` — v2 semantics
- `kernel/sched/core.c` — CPU controller hooks
- `mm/memcontrol.c` — memory controller

```c
/* C program demonstrating cgroup v2 resource enforcement */
/* compile with: gcc -o cgtest cgtest.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <sys/stat.h>
#include <sys/types.h>

#define CGROUP_ROOT "/sys/fs/cgroup"
#define SVC_CGROUP  CGROUP_ROOT "/svc-order"

static int write_file(const char *path, const char *value) {
    int fd = open(path, O_WRONLY);
    if (fd < 0) {
        perror(path);
        return -1;
    }
    ssize_t n = write(fd, value, strlen(value));
    close(fd);
    return n < 0 ? -1 : 0;
}

int create_service_cgroup(const char *svc_name,
                          long mem_bytes, long cpu_quota_us) {
    char path[256];
    char val[64];

    /* Create cgroup directory */
    snprintf(path, sizeof(path), "%s/%s", CGROUP_ROOT, svc_name);
    if (mkdir(path, 0755) < 0 && errno != EEXIST) {
        perror("mkdir");
        return -1;
    }

    /* Set memory limit */
    snprintf(path, sizeof(path), "%s/%s/memory.max", CGROUP_ROOT, svc_name);
    snprintf(val, sizeof(val), "%ld", mem_bytes);
    write_file(path, val);

    /* Set CPU quota: cpu.max = "$QUOTA $PERIOD"
     * quota=200000 period=100000 means 2 CPUs */
    snprintf(path, sizeof(path), "%s/%s/cpu.max", CGROUP_ROOT, svc_name);
    snprintf(val, sizeof(val), "%ld 100000", cpu_quota_us);
    write_file(path, val);

    /* Set PID limit */
    snprintf(path, sizeof(path), "%s/%s/pids.max", CGROUP_ROOT, svc_name);
    write_file(path, "512");

    /* Move current process into cgroup */
    snprintf(path, sizeof(path), "%s/%s/cgroup.procs", CGROUP_ROOT, svc_name);
    snprintf(val, sizeof(val), "%d", getpid());
    write_file(path, val);

    printf("cgroup '%s' created: mem=%ldMB cpu_quota=%ldus\n",
           svc_name, mem_bytes / (1024*1024), cpu_quota_us);
    return 0;
}

int main(void) {
    /* 256MB RAM, 2 CPU cores (200000us / 100000us period) */
    return create_service_cgroup("svc-order", 256 * 1024 * 1024, 200000);
}
```

### 3.3 Seccomp-BPF: System Call Filtering

Each microservice should have a minimal syscall allowlist. This is implemented via `seccomp(2)` + BPF programs.

```
SECCOMP-BPF FILTER MECHANISM
==============================

Process                  Kernel
  |                         |
  | syscall(write, ...)     |
  +------------------------>|
                            | seccomp hook (arch/x86/kernel/ptrace.c)
                            | __secure_computing() in kernel/seccomp.c
                            |
                            | Load BPF filter:
                            | struct seccomp_data {
                            |   int   nr;           /* syscall number */
                            |   __u32 arch;         /* AUDIT_ARCH_X86_64 */
                            |   __u64 instruction_pointer;
                            |   __u64 args[6];      /* syscall args */
                            | }
                            |
                            | BPF program returns:
                            |   SECCOMP_RET_ALLOW  → proceed
                            |   SECCOMP_RET_KILL   → SIGSYS
                            |   SECCOMP_RET_TRAP   → SIGSYS with si_code=SYS_SECCOMP
                            |   SECCOMP_RET_ERRNO  → return -errno
                            |   SECCOMP_RET_TRACE  → notify tracer (ptrace)
                            |   SECCOMP_RET_LOG    → allow + log
```

**Kernel source:** `kernel/seccomp.c`, `include/uapi/linux/seccomp.h`

```c
/* seccomp_filter.c — minimal syscall allowlist for a Go HTTP service */
/* Based on: https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html */
#include <linux/seccomp.h>
#include <linux/filter.h>
#include <linux/audit.h>
#include <sys/prctl.h>
#include <sys/syscall.h>
#include <stdio.h>
#include <stdlib.h>
#include <stddef.h>  /* offsetof */
#include <errno.h>
#include <string.h>

/* BPF helper macros for seccomp filters */
#define VALIDATE_ARCH \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, \
             offsetof(struct seccomp_data, arch)), \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, AUDIT_ARCH_X86_64, 1, 0), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL)

#define ALLOW_SYSCALL(name) \
    BPF_STMT(BPF_LD | BPF_W | BPF_ABS, \
             offsetof(struct seccomp_data, nr)), \
    BPF_JUMP(BPF_JMP | BPF_JEQ | BPF_K, SYS_##name, 0, 1), \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_ALLOW)

#define DENY_ALL \
    BPF_STMT(BPF_RET | BPF_K, SECCOMP_RET_KILL)

/*
 * Minimal syscall allowlist for an HTTP microservice:
 * read, write, close, fstat, mmap, mprotect, munmap, brk,
 * rt_sigaction, rt_sigprocmask, rt_sigreturn,
 * nanosleep, getpid, socket, connect, accept, sendto, recvfrom,
 * sendmsg, recvmsg, bind, listen, getsockname, getpeername,
 * setsockopt, getsockopt, clone, wait4, exit, exit_group,
 * futex, epoll_create1, epoll_ctl, epoll_wait,
 * openat, stat, lstat, poll, select
 */
static struct sock_filter microservice_filter[] = {
    VALIDATE_ARCH,
    ALLOW_SYSCALL(read),
    ALLOW_SYSCALL(write),
    ALLOW_SYSCALL(close),
    ALLOW_SYSCALL(fstat),
    ALLOW_SYSCALL(mmap),
    ALLOW_SYSCALL(mprotect),
    ALLOW_SYSCALL(munmap),
    ALLOW_SYSCALL(brk),
    ALLOW_SYSCALL(rt_sigaction),
    ALLOW_SYSCALL(rt_sigprocmask),
    ALLOW_SYSCALL(rt_sigreturn),
    ALLOW_SYSCALL(nanosleep),
    ALLOW_SYSCALL(socket),
    ALLOW_SYSCALL(connect),
    ALLOW_SYSCALL(accept4),
    ALLOW_SYSCALL(sendto),
    ALLOW_SYSCALL(recvfrom),
    ALLOW_SYSCALL(sendmsg),
    ALLOW_SYSCALL(recvmsg),
    ALLOW_SYSCALL(bind),
    ALLOW_SYSCALL(listen),
    ALLOW_SYSCALL(getsockname),
    ALLOW_SYSCALL(getpeername),
    ALLOW_SYSCALL(setsockopt),
    ALLOW_SYSCALL(getsockopt),
    ALLOW_SYSCALL(clone),
    ALLOW_SYSCALL(futex),
    ALLOW_SYSCALL(epoll_create1),
    ALLOW_SYSCALL(epoll_ctl),
    ALLOW_SYSCALL(epoll_pwait),
    ALLOW_SYSCALL(openat),
    ALLOW_SYSCALL(exit),
    ALLOW_SYSCALL(exit_group),
    ALLOW_SYSCALL(getpid),
    ALLOW_SYSCALL(getppid),
    ALLOW_SYSCALL(gettid),
    ALLOW_SYSCALL(tgkill),
    ALLOW_SYSCALL(clock_gettime),
    ALLOW_SYSCALL(getrandom),
    DENY_ALL,
};

int install_microservice_seccomp(void) {
    struct sock_fprog prog = {
        .len = sizeof(microservice_filter) / sizeof(microservice_filter[0]),
        .filter = microservice_filter,
    };

    /* Prevent privilege escalation via setuid */
    if (prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) < 0) {
        perror("prctl PR_SET_NO_NEW_PRIVS");
        return -1;
    }

    /* Install the filter */
    if (prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, &prog) < 0) {
        perror("prctl SECCOMP_MODE_FILTER");
        return -1;
    }

    return 0;
}
```

### 3.4 Linux Capabilities

Microservices should run with minimal capabilities (not as full root):

```
CAPABILITY MODEL FOR MICROSERVICES
====================================

Traditional Root Process: ALL 41 capabilities
[CAP_SYS_ADMIN, CAP_NET_ADMIN, CAP_SYS_PTRACE, ... everything]

Microservice (principle of least privilege):
+-----------------------------+----------------------------+
| Capability                  | Needed For                 |
+-----------------------------+----------------------------+
| CAP_NET_BIND_SERVICE        | Bind port < 1024 (avoid!)  |
| CAP_SYS_NICE                | Priority adjustment        |
| (none)                      | HTTP service on port 8080  |
+-----------------------------+----------------------------+

Docker default dropped caps:
  CAP_AUDIT_WRITE, CAP_CHOWN, CAP_DAC_OVERRIDE,
  CAP_FOWNER, CAP_FSETID, CAP_KILL, CAP_MKNOD,
  CAP_NET_BIND_SERVICE, CAP_NET_RAW, CAP_SETFCAP,
  CAP_SETGID, CAP_SETPCAP, CAP_SETUID, CAP_SYS_CHROOT

Kubernetes SecurityContext:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    allowPrivilegeEscalation: false
    capabilities:
      drop: ["ALL"]
    readOnlyRootFilesystem: true
```

**Kernel source:** `include/uapi/linux/capability.h`, `security/commoncap.c`

### 3.5 Linux Network Namespaces & Virtual Networking

The network topology for microservices on a single host uses veth pairs and bridges:

```
SINGLE-HOST MICROSERVICE NETWORK (Docker bridge network)
=========================================================

+--------------------------- HOST KERNEL --------------------------+
|                                                                    |
|  [docker0 bridge: 172.17.0.1/16]                                  |
|         |              |              |                            |
|      [veth_a]       [veth_b]       [veth_c]                      |
|         |              |              |                            |
| +-------+--+   +-------+--+   +------+---+                       |
| |Net NS: A |   |Net NS: B |   |Net NS: C |                       |
| |eth0:     |   |eth0:     |   |eth0:     |                       |
| |172.17.0.2|   |172.17.0.3|   |172.17.0.4|                       |
| |          |   |          |   |          |                       |
| |[ordersvc]|   |[usersvc] |   |[paymentsv|                       |
| +----------+   +----------+   +----------+                       |
|                                                                    |
|  iptables/nftables:                                               |
|  DOCKER chain → DNAT for published ports                          |
|  DOCKER-ISOLATION → inter-network isolation                       |
|                                                                    |
|  [eth0: 192.168.1.100/24] ← physical NIC (host)                  |
+--------------------------------------------------------------------+

Packet flow: Client → eth0 → PREROUTING (DNAT) → docker0 →
             veth → container eth0 → service process
```

**veth pair internals:**

```c
/*
 * veth driver: drivers/net/veth.c
 * Each veth pair is two net_device structs linked together.
 * TX on one side = RX on the other.
 */

/* How Docker creates veth pairs (simplified netlink) */
/* ip link add veth0 type veth peer name veth1 */
/* Then: ip link set veth1 netns <container_ns> */

/* In kernel: veth_xmit() */
static netdev_tx_t veth_xmit(struct sk_buff *skb, struct net_device *dev)
{
    struct veth_priv *rcv_priv, *priv = netdev_priv(dev);
    struct veth_rq *rq = NULL;
    struct net_device *rcv;
    int length = skb->len;

    /* Get the peer device */
    rcv = rcu_dereference(priv->peer);
    if (unlikely(!rcv)) {
        kfree_skb(skb);
        return NETDEV_TX_OK;
    }

    /* Repoint skb to peer device, then enqueue to its RX */
    skb->dev = rcv;
    /* ... enqueue to RX queue of peer ... */
    netif_rx(skb);  /* simplified; actually uses NAPI in modern kernels */
    return NETDEV_TX_OK;
}
```

---

## 4. Inter-Process & Inter-Service Communication

### 4.1 IPC Mechanisms: A Taxonomy

```
IPC MECHANISMS — LATENCY CHARACTERISTICS
==========================================

Mechanism          Latency       Throughput    Use Case
------------------------------------------------------------------
Shared Memory      ~50ns         Very High     Same-host, same-trust
Unix Domain Socket ~1-5us        High          Same-host, different process
TCP Loopback       ~5-15us       High          Same-host or local net
TCP (LAN)          ~100-500us    Medium        Service-to-service
HTTP/1.1 (LAN)     ~500us-2ms    Medium        REST APIs
HTTP/2 (LAN)       ~200us-1ms    Medium-High   gRPC, multiplexed
gRPC (LAN)         ~200us-800us  High          Internal RPC
Message Queue      ~1-10ms       High          Async, decoupled
(local Kafka)
Message Queue      ~5-50ms       High          Cross-DC, async
(remote Kafka)
```

**Data path through kernel for Unix domain socket:**

```
UNIX DOMAIN SOCKET DATA PATH
==============================

Writer Process              Kernel                  Reader Process
     |                        |                           |
     | write(fd, buf, n)       |                           |
     +------------------------>|                           |
                            sys_write()                    |
                            sock->ops->sendmsg()           |
                            unix_stream_sendmsg()          |
                            skb = sock_alloc_send_skb()    |
                            memcpy(skb, buf)               |
                            skb_queue_tail(&peer->sk_receive_queue, skb)
                            sk_data_ready(peer)            |
                                                       wake up
                                                           |
                                                    read(fd, buf, n)
                                                    unix_stream_recvmsg()
                                                    skb = skb_dequeue()
                                                    memcpy(buf, skb)
                                                    kfree_skb(skb)
                                                           |
                                                       return n

Zero-copy optimization: MSG_ZEROCOPY or io_uring for high-throughput
Kernel source: net/unix/af_unix.c
```

### 4.2 io_uring for High-Performance Service Communication

`io_uring` (merged in 5.1) provides a ring-buffer-based async I/O interface with minimal syscall overhead — ideal for high-throughput microservice servers.

```
io_uring ARCHITECTURE
======================

User Space                      Kernel Space
+-------------------+           +-------------------+
| Submission Queue  |           | io_uring instance |
| (SQ Ring)         |           |                   |
| +---+---+---+---+ |  mmap()   | +---------------+ |
| |SQE|SQE|SQE|   | +-------->>| | SQ Ring       | |
| +---+---+---+---+ |           | +---------------+ |
|  sq_head  sq_tail |           | | CQ Ring       | |
+-------------------+           | +---------------+ |
                                | | SQE Array     | |
+-------------------+           | +---------------+ |
| Completion Queue  |           |                   |
| (CQ Ring)         |  mmap()   | io_uring_enter()  |
| +---+---+---+---+ |<<--------+| submits + waits   |
| |CQE|CQE|CQE|   | |           +-------------------+
| +---+---+---+---+ |
|  cq_head  cq_tail |
+-------------------+

SQE (Submission Queue Entry): what to do (READ/WRITE/ACCEPT/RECV/SEND)
CQE (Completion Queue Entry): result (res = return value, user_data)

Key: shared mmap means zero syscall for batch submission
     io_uring_enter() batches N operations in ONE syscall
```

```c
/* io_uring HTTP server — high performance microservice I/O */
/* Kernel source: io_uring/io_uring.c, include/uapi/linux/io_uring.h */
#include <liburing.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <netinet/in.h>
#include <sys/socket.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>

#define QUEUE_DEPTH  256
#define MAX_CONNS    1024
#define BUF_SIZE     4096

enum op_type { OP_ACCEPT, OP_READ, OP_WRITE };

struct conn_info {
    int fd;
    enum op_type type;
    char buf[BUF_SIZE];
};

static struct io_uring ring;

static void add_accept(int server_fd, struct sockaddr_in *client_addr,
                       socklen_t *client_len)
{
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    struct conn_info *ci = calloc(1, sizeof(*ci));
    ci->fd   = server_fd;
    ci->type = OP_ACCEPT;

    io_uring_prep_accept(sqe, server_fd,
                         (struct sockaddr *)client_addr, client_len, 0);
    io_uring_sqe_set_data(sqe, ci);
}

static void add_read(int fd)
{
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    struct conn_info *ci = calloc(1, sizeof(*ci));
    ci->fd   = fd;
    ci->type = OP_READ;

    io_uring_prep_recv(sqe, fd, ci->buf, BUF_SIZE, 0);
    io_uring_sqe_set_data(sqe, ci);
}

static const char http_200[] =
    "HTTP/1.1 200 OK\r\n"
    "Content-Length: 2\r\n"
    "Content-Type: text/plain\r\n"
    "\r\n"
    "OK";

static void add_write(int fd)
{
    struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
    struct conn_info *ci = calloc(1, sizeof(*ci));
    ci->fd   = fd;
    ci->type = OP_WRITE;
    memcpy(ci->buf, http_200, sizeof(http_200));

    io_uring_prep_send(sqe, fd, ci->buf, sizeof(http_200) - 1, 0);
    io_uring_sqe_set_data(sqe, ci);
}

int main(void)
{
    int server_fd;
    struct sockaddr_in server_addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(8080),
        .sin_addr.s_addr = INADDR_ANY,
    };
    struct sockaddr_in client_addr;
    socklen_t client_len = sizeof(client_addr);

    /* Setup socket */
    server_fd = socket(AF_INET, SOCK_STREAM | SOCK_NONBLOCK, 0);
    int yes = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEPORT, &yes, sizeof(yes));
    bind(server_fd, (struct sockaddr *)&server_addr, sizeof(server_addr));
    listen(server_fd, SOMAXCONN);

    /* Initialize io_uring with SQPOLL for kernel-side polling
     * IORING_SETUP_SQPOLL: kernel thread polls SQ, zero-syscall submit */
    struct io_uring_params params = {
        .flags = IORING_SETUP_SQPOLL,
        .sq_thread_idle = 2000, /* ms before kernel thread sleeps */
    };
    if (io_uring_queue_init_params(QUEUE_DEPTH, &ring, &params) < 0) {
        /* Fallback without SQPOLL if insufficient privileges */
        io_uring_queue_init(QUEUE_DEPTH, &ring, 0);
    }

    /* Register server fd for fixed files optimization */
    io_uring_register_files(&ring, &server_fd, 1);

    /* Prime the accept */
    add_accept(server_fd, &client_addr, &client_len);
    io_uring_submit(&ring);

    /* Event loop */
    while (1) {
        struct io_uring_cqe *cqe;
        io_uring_wait_cqe(&ring, &cqe);

        struct conn_info *ci = io_uring_cqe_get_data(cqe);
        int res = cqe->res;
        io_uring_cqe_seen(&ring, cqe);

        if (res < 0) {
            if (ci->type != OP_ACCEPT)
                close(ci->fd);
            free(ci);
            if (ci->type == OP_ACCEPT)
                add_accept(server_fd, &client_addr, &client_len);
            continue;
        }

        switch (ci->type) {
        case OP_ACCEPT:
            add_read(res);          /* res = new client fd */
            add_accept(server_fd, &client_addr, &client_len); /* re-arm */
            break;
        case OP_READ:
            if (res > 0)
                add_write(ci->fd);
            else
                close(ci->fd);
            break;
        case OP_WRITE:
            close(ci->fd);          /* HTTP/1.0 close after response */
            break;
        }

        free(ci);
        io_uring_submit(&ring);
    }

    io_uring_queue_exit(&ring);
    close(server_fd);
    return 0;
}
```

---

## 5. Networking Protocol Stack Deep Dive

### 5.1 Linux Kernel Network Stack Path

```
FULL TX PATH: microservice write() → wire
===========================================

Application (ordersvc)
  |
  | write(sockfd, buf, len)  / sendmsg()
  v
[syscall entry: arch/x86/entry/syscalls/syscall_64.tbl]
  |
  v
[net/socket.c: sock_write_iter() → sock_sendmsg()]
  |
  v
[Protocol Layer: net/ipv4/tcp.c: tcp_sendmsg()]
  |
  | tcp_push() → tcp_write_xmit()
  | Build TCP segment (MSS, Nagle, TSO)
  | tcp_transmit_skb()
  v
[net/ipv4/ip_output.c: ip_queue_xmit()]
  |
  | Add IP header (TTL, DSCP, frag)
  | ip_local_out() → dst_output()
  v
[net/netfilter/nf_tables_core.c (nftables) or
 net/netfilter/iptable_filter.c (iptables)]
  |
  | POSTROUTING hook
  v
[net/ipv4/ip_output.c: ip_output() → ip_finish_output()]
  |
  | Fragmentation if needed
  v
[net/core/dev.c: dev_queue_xmit()]
  |
  | Select TX queue (RSS/RPS)
  | qdisc enqueue (tc/sch)
  v
[drivers/net/ethernet/intel/e1000e/ (or similar NIC driver)]
  |
  | DMA descriptor ring
  | Hardware offload: checksum, TSO, GSO
  v
[Physical wire / veth / tun/tap]
```

```
RX PATH: wire → microservice read()
=====================================

[NIC interrupt / NAPI poll]
  |
  | DMA into sk_buff from rx ring
  v
[net/core/dev.c: netif_receive_skb()]
  |
  | RPS/RFS (Receive Packet Steering)
  v
[nftables PREROUTING hook]
  |
  v
[net/ipv4/ip_input.c: ip_rcv() → ip_rcv_finish()]
  |
  | Routing decision: ip_route_input()
  v
[net/ipv4/tcp_input.c: tcp_v4_rcv()]
  |
  | TCP state machine: ESTABLISHED → seq check
  | tcp_data_queue() → receive buffer
  v
[Socket wake up: sk_data_ready()]
  |
  v
Application read(sockfd, buf, len)
```

### 5.2 HTTP/2 Over TLS (gRPC Transport)

```
HTTP/2 FRAME STRUCTURE
========================

+-----------------------------------------------+
|                 Length (24 bits)               |
+---------------+---------------+---------------+
|   Type (8)    |   Flags (8)   |
+-+-------------+---------------+-------------------------------+
|R|                 Stream Identifier (31)                      |
+=+=============================================================+
|                   Frame Payload (0...2^24-1 octets)           |
+---------------------------------------------------------------+

Frame Types:
  0x0 DATA         - request/response body
  0x1 HEADERS      - HTTP headers (HPACK compressed)
  0x3 RST_STREAM   - stream error
  0x4 SETTINGS     - connection parameters
  0x6 PING         - keepalive
  0x7 GOAWAY       - connection shutdown
  0x8 WINDOW_UPDATE- flow control

HTTP/2 MULTIPLEXING
====================

Single TCP Connection
+----------------------------------------------+
| Stream 1: GET /orders/123                    |
|   [HEADERS] [DATA]                           |
+----------------------------------------------+
| Stream 3: POST /orders                       |
|   [HEADERS] [DATA] [DATA] [DATA]             |
+----------------------------------------------+
| Stream 5: GET /users/456                     |
|   [HEADERS]                                  |
+----------------------------------------------+
| Stream 7: (not started yet)                  |
+----------------------------------------------+

All streams interleaved on one TCP conn, no head-of-line blocking
(HTTP/2 HOL at TCP level solved by HTTP/3/QUIC)
```

### 5.3 gRPC Protocol

```
gRPC MESSAGE FRAMING (Length-Prefixed)
=======================================

+-----+--------------------+
|  0  | Compressed flag    | 1 byte (0=not compressed, 1=compressed)
+-----+--------------------+
|  1  |                    |
|  2  | Message Length     | 4 bytes, big-endian uint32
|  3  |                    |
|  4  |                    |
+-----+--------------------+
|  5+ | Protobuf payload   | $MessageLength bytes
+-----------------------------+

gRPC over HTTP/2:
  :method = POST
  :path = /ordersvc.OrderService/CreateOrder
  :authority = orders.internal:50051
  content-type = application/grpc
  grpc-encoding = gzip (optional)
  te = trailers

  [5-byte length-prefix][protobuf body]

  [TRAILERS]
  grpc-status = 0 (OK)
  grpc-message = ""
```

### 5.4 eBPF for Network Observability

eBPF programs attached to `tc` or XDP hooks give per-packet visibility into microservice traffic without any code changes.

```
eBPF HOOK POINTS FOR MICROSERVICE MONITORING
=============================================

NIC RX ──────> [XDP hook] ──────> [tc ingress hook]
                  |                      |
               (earliest,             (after skb
                pre-skb)              allocated)
                  |                      |
                  v                      v
              DROP/TX/PASS          iptables/nftables
                                         |
                                         v
                                   [socket filter]
                                   (per-socket BPF)
                                         |
                                         v
                                   [Application]
                                         |
NIC TX <───── [tc egress hook] <─────────+
                  |
              BPF can: count pkts, measure latency,
                       sample headers, drop/redirect
```

```c
/* eBPF program: track per-service HTTP request latency */
/* Attach to: tc qdisc on veth interface of each container */
/* Build: clang -O2 -target bpf -c svc_latency.bpf.c -o svc_latency.bpf.o */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* Map: dst_port → {count, total_bytes, last_seen_ns} */
struct svc_stats {
    __u64 pkt_count;
    __u64 total_bytes;
    __u64 last_ts_ns;
};

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key,  __u16);          /* dst port */
    __type(value, struct svc_stats);
    __uint(max_entries, 256);
} svc_stats_map SEC(".maps");

/* Histogram map for latency distribution (power-of-2 buckets) */
struct {
    __uint(type, BPF_MAP_TYPE_ARRAY);
    __type(key,  __u32);          /* bucket index */
    __type(value, __u64);         /* count */
    __uint(max_entries, 64);
} latency_hist SEC(".maps");

/* Track SYN timestamps for RTT measurement */
struct flow_key {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
};

struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __type(key,  struct flow_key);
    __type(value, __u64);         /* SYN timestamp ns */
    __uint(max_entries, 65536);
} syn_ts_map SEC(".maps");

SEC("tc")
int track_svc_traffic(struct __sk_buff *skb)
{
    void *data     = (void *)(long)skb->data;
    void *data_end = (void *)(long)skb->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return TC_ACT_OK;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return TC_ACT_OK;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return TC_ACT_OK;
    if (ip->protocol != IPPROTO_TCP)
        return TC_ACT_OK;

    struct tcphdr *tcp = (void *)ip + (ip->ihl * 4);
    if ((void *)(tcp + 1) > data_end)
        return TC_ACT_OK;

    __u16 dst_port = bpf_ntohs(tcp->dest);

    /* Update per-port stats */
    struct svc_stats *stats = bpf_map_lookup_elem(&svc_stats_map, &dst_port);
    if (stats) {
        __sync_fetch_and_add(&stats->pkt_count, 1);
        __sync_fetch_and_add(&stats->total_bytes, skb->len);
        stats->last_ts_ns = bpf_ktime_get_ns();
    } else {
        struct svc_stats new_stats = {
            .pkt_count   = 1,
            .total_bytes = skb->len,
            .last_ts_ns  = bpf_ktime_get_ns(),
        };
        bpf_map_update_elem(&svc_stats_map, &dst_port, &new_stats, BPF_ANY);
    }

    /* Track SYN for RTT measurement */
    if (tcp->syn && !tcp->ack) {
        struct flow_key key = {
            .src_ip   = ip->saddr,
            .dst_ip   = ip->daddr,
            .src_port = bpf_ntohs(tcp->source),
            .dst_port = dst_port,
        };
        __u64 ts = bpf_ktime_get_ns();
        bpf_map_update_elem(&syn_ts_map, &key, &ts, BPF_ANY);
    }

    /* On SYN-ACK, compute RTT and bucket into histogram */
    if (tcp->syn && tcp->ack) {
        struct flow_key key = {
            .src_ip   = ip->daddr,     /* reverse for lookup */
            .dst_ip   = ip->saddr,
            .src_port = dst_port,
            .dst_port = bpf_ntohs(tcp->source),
        };
        __u64 *syn_ts = bpf_map_lookup_elem(&syn_ts_map, &key);
        if (syn_ts) {
            __u64 rtt_ns = bpf_ktime_get_ns() - *syn_ts;
            /* Log2 bucket: rtt_ns in microseconds */
            __u64 rtt_us = rtt_ns / 1000;
            __u32 bucket = 0;
            /* Find highest set bit → log2 approximation */
            if (rtt_us > 0) {
                bucket = 63 - __builtin_clzll(rtt_us);
                if (bucket >= 64) bucket = 63;
            }
            __u64 *cnt = bpf_map_lookup_elem(&latency_hist, &bucket);
            if (cnt)
                __sync_fetch_and_add(cnt, 1);
            bpf_map_delete_elem(&syn_ts_map, &key);
        }
    }

    return TC_ACT_OK;
}

char _license[] SEC("license") = "GPL";
```

---

## 6. Service-to-Service Communication Patterns

### 6.1 Synchronous vs Asynchronous Communication

```
SYNCHRONOUS (REQUEST-RESPONSE)
================================

Caller          Network        Callee
  |                |             |
  |--[HTTP/gRPC]-->|------------>|
  |  (blocked)     |             | (processing)
  |                |<------------|
  |<[response]-----|             |
  | (unblocked)    |             |

Problems:
  - Temporal coupling (callee must be up)
  - Performance cascade (slow callee = slow caller)
  - Amplified failure (chain of 5 = 5 failure points)

ASYNCHRONOUS (EVENT/MESSAGE)
==============================

Producer       Message Broker      Consumer
  |                 |                 |
  |--[publish]----->|                 |
  | (returns        | (durable store) |
  |  immediately)   |                 |
  |                 |--[deliver]----->|
  |                 |                 | (processing)
  |                 |<--[ack]---------|
  |                 | (delete msg)    |

Benefits:
  - Temporal decoupling (consumer can be down)
  - Load leveling (broker buffers spikes)
  - Independent scaling
```

### 6.2 REST API Design for Microservices

```
REST RESOURCE HIERARCHY
========================

/orders                          ← Collection
/orders/{id}                     ← Resource
/orders/{id}/items               ← Sub-collection
/orders/{id}/items/{item_id}     ← Sub-resource

HTTP Method Semantics:
  GET    /orders          → List (200, 206 for partial)
  POST   /orders          → Create (201 + Location header)
  GET    /orders/{id}     → Read (200, 404)
  PUT    /orders/{id}     → Replace (200, 404)
  PATCH  /orders/{id}     → Update (200, 404)  [JSON Patch RFC 6902]
  DELETE /orders/{id}     → Delete (204, 404)

Idempotency:
  GET, PUT, DELETE = idempotent (safe to retry)
  POST             = NOT idempotent (use Idempotency-Key header)

PAGINATION
===========
GET /orders?cursor=abc123&limit=20
Response:
{
  "data": [...],
  "pagination": {
    "next_cursor": "def456",
    "has_more": true
  }
}

VERSIONING STRATEGIES
======================
  URL:    /v1/orders, /v2/orders   (most common, cache-friendly)
  Header: Accept: application/vnd.company.v2+json
  Param:  /orders?version=2
```

```go
// internal/adapters/httphandler/order_handler.go
package httphandler

import (
    "encoding/json"
    "net/http"
    "strconv"

    "github.com/go-chi/chi/v5"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.uber.org/zap"

    "github.com/yourorg/ordersvc/internal/domain"
)

type OrderHandler struct {
    useCase domain.OrderUseCase
    logger  *zap.Logger
}

func (h *OrderHandler) CreateOrder(w http.ResponseWriter, r *http.Request) {
    ctx, span := otel.Tracer("ordersvc").Start(r.Context(), "CreateOrder")
    defer span.End()

    // Idempotency key
    idempotencyKey := r.Header.Get("Idempotency-Key")
    if idempotencyKey == "" {
        writeError(w, http.StatusBadRequest, "Idempotency-Key header required")
        return
    }

    var req CreateOrderRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        writeError(w, http.StatusBadRequest, "invalid request body")
        return
    }

    if err := req.Validate(); err != nil {
        writeError(w, http.StatusUnprocessableEntity, err.Error())
        return
    }

    span.SetAttributes(
        attribute.String("customer.id", req.CustomerID),
        attribute.Int("items.count", len(req.Items)),
    )

    order, err := h.useCase.CreateOrder(ctx, req.ToCommand(idempotencyKey))
    if err != nil {
        switch {
        case domain.IsNotFoundError(err):
            writeError(w, http.StatusNotFound, err.Error())
        case domain.IsConflictError(err):
            // Idempotency: same key, same result
            w.Header().Set("Content-Type", "application/json")
            w.WriteHeader(http.StatusOK)
            json.NewEncoder(w).Encode(ToOrderResponse(order))
        default:
            h.logger.Error("create order failed", zap.Error(err))
            writeError(w, http.StatusInternalServerError, "internal error")
        }
        return
    }

    w.Header().Set("Content-Type", "application/json")
    w.Header().Set("Location", "/v1/orders/"+order.ID)
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(ToOrderResponse(order))
}

func (h *OrderHandler) GetOrder(w http.ResponseWriter, r *http.Request) {
    ctx, span := otel.Tracer("ordersvc").Start(r.Context(), "GetOrder")
    defer span.End()

    orderID := chi.URLParam(r, "id")
    span.SetAttributes(attribute.String("order.id", orderID))

    order, err := h.useCase.GetOrder(ctx, orderID)
    if err != nil {
        if domain.IsNotFoundError(err) {
            writeError(w, http.StatusNotFound, "order not found")
            return
        }
        writeError(w, http.StatusInternalServerError, "internal error")
        return
    }

    // ETag for conditional GETs (caching)
    etag := `"` + order.UpdatedAt.Format("20060102150405") + `"`
    if r.Header.Get("If-None-Match") == etag {
        w.WriteHeader(http.StatusNotModified)
        return
    }
    w.Header().Set("ETag", etag)
    w.Header().Set("Cache-Control", "private, max-age=30")
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(ToOrderResponse(order))
}
```

### 6.3 gRPC Deep Dive

```
gRPC SERVICE TYPES
===================

// Unary RPC (request-response)
rpc GetOrder(GetOrderRequest) returns (Order);

// Server-Streaming RPC (one request, N responses)
rpc ListOrderUpdates(ListRequest) returns (stream OrderEvent);

// Client-Streaming RPC (N requests, one response)
rpc BatchCreateOrders(stream CreateOrderRequest) returns (BatchResult);

// Bidirectional Streaming
rpc OrderStream(stream OrderCommand) returns (stream OrderEvent);

gRPC INTERCEPTOR CHAIN
=======================

Client                                Server
  |                                     |
  | Unary call                          |
  +--[ClientInterceptor 1]-------->-----+
  |  (auth header injection)    |       |
  +--[ClientInterceptor 2]----->-+       |
  |  (retry logic)      |               |
  +--[transport]------->+               |
                                        +--[ServerInterceptor 1]
                                        |  (auth validation)
                                        +--[ServerInterceptor 2]
                                        |  (rate limiting)
                                        +--[ServerInterceptor 3]
                                        |  (tracing/metrics)
                                        +--[Handler]
```

```go
// proto/orders/v1/orders.proto
syntax = "proto3";
package orders.v1;
option go_package = "github.com/yourorg/ordersvc/proto/orders/v1;ordersv1";

import "google/protobuf/timestamp.proto";

service OrderService {
    rpc CreateOrder(CreateOrderRequest) returns (Order);
    rpc GetOrder(GetOrderRequest) returns (Order);
    rpc ListOrders(ListOrdersRequest) returns (ListOrdersResponse);
    rpc UpdateOrderStatus(UpdateOrderStatusRequest) returns (Order);
    rpc WatchOrder(WatchOrderRequest) returns (stream OrderEvent); // server streaming
}

message CreateOrderRequest {
    string  customer_id    = 1;
    repeated OrderItem items = 2;
    string  idempotency_key = 3;
}

message Order {
    string id          = 1;
    string customer_id = 2;
    repeated OrderItem items = 3;
    OrderStatus status = 4;
    Money total        = 5;
    google.protobuf.Timestamp created_at = 6;
    google.protobuf.Timestamp updated_at = 7;
}

message Money {
    int64  amount   = 1; // in cents
    string currency = 2; // ISO 4217
}

enum OrderStatus {
    ORDER_STATUS_UNSPECIFIED = 0;
    ORDER_STATUS_PENDING     = 1;
    ORDER_STATUS_CONFIRMED   = 2;
    ORDER_STATUS_SHIPPING    = 3;
    ORDER_STATUS_DELIVERED   = 4;
    ORDER_STATUS_CANCELLED   = 5;
}
```

```go
// internal/adapters/grpchandler/interceptors.go
package grpchandler

import (
    "context"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/codes"
    "go.uber.org/zap"
    "google.golang.org/grpc"
    "google.golang.org/grpc/metadata"
    "google.golang.org/grpc/status"
    "google.golang.org/grpc/codes" as grpccodes
)

// UnaryInterceptor chains: auth + tracing + logging + metrics
func UnaryInterceptor(logger *zap.Logger) grpc.UnaryServerInterceptor {
    return func(
        ctx context.Context,
        req interface{},
        info *grpc.UnaryServerInfo,
        handler grpc.UnaryHandler,
    ) (interface{}, error) {
        start := time.Now()

        // Extract tracing context from metadata
        md, _ := metadata.FromIncomingContext(ctx)
        ctx, span := otel.Tracer("ordersvc").Start(ctx, info.FullMethod)
        defer span.End()

        // Auth validation
        if err := validateAuth(ctx, md); err != nil {
            span.SetStatus(codes.Error, err.Error())
            return nil, status.Error(grpccodes.Unauthenticated, "invalid credentials")
        }

        // Call handler
        resp, err := handler(ctx, req)

        // Logging
        duration := time.Since(start)
        if err != nil {
            span.SetStatus(codes.Error, err.Error())
            logger.Error("gRPC call failed",
                zap.String("method", info.FullMethod),
                zap.Duration("duration", duration),
                zap.Error(err),
            )
        } else {
            logger.Info("gRPC call completed",
                zap.String("method", info.FullMethod),
                zap.Duration("duration", duration),
            )
        }

        return resp, err
    }
}
```

### 6.4 Service Mesh (Envoy/Istio Architecture)

```
SERVICE MESH ARCHITECTURE
==========================

+---------------------------+    +---------------------------+
|   Order Service Pod       |    |   User Service Pod        |
|                           |    |                           |
|  +-----------------+      |    |  +-----------------+      |
|  | ordersvc:8080   |      |    |  | usersvc:8080    |      |
|  | (app container) |      |    |  | (app container) |      |
|  +------|----------+      |    |  +------|----------+      |
|         | localhost        |    |         | localhost        |
|  +------|----------+      |    |  +------|----------+      |
|  | Envoy Proxy     |      |    |  | Envoy Proxy     |      |
|  | :15001 (egress) |      |    |  | :15001 (egress) |      |
|  | :15006 (ingress)|      |    |  | :15006 (ingress)|      |
|  | :15090 (metrics)|      |    |  | :15090 (metrics)|      |
|  +-----------------+      |    |  +-----------------+      |
|         |                 |    |         |                 |
+---------|-----------------+    +---------|-----------------+
          |                                |
          |    mTLS (Envoy-to-Envoy)       |
          +--------------------------------+
                       |
          +------------+-----------+
          |    Control Plane       |
          |  Istiod (Pilot+CA+     |
          |   Galley+Citadel)      |
          |                        |
          | xDS APIs:              |
          | LDS (Listeners)        |
          | RDS (Routes)           |
          | CDS (Clusters)         |
          | EDS (Endpoints)        |
          | SDS (Secrets/certs)    |
          +------------------------+

iptables REDIRECT rules (injected by istio-init container):
  PREROUTING: all inbound TCP → port 15006 (Envoy ingress)
  OUTPUT:     all outbound TCP → port 15001 (Envoy egress)
              except traffic from Envoy itself (UID 1337)

This means: apps think they talk directly to each other,
            but ALL traffic goes through Envoy proxies.
            mTLS, retries, circuit breakers = transparent.
```

---

## 7. Data Management & Persistence Patterns

### 7.1 Database Per Service

```
DATABASE-PER-SERVICE PATTERN
==============================

+-------------+    +-------------+    +-------------+
| Order Svc   |    | User Svc    |    | Payment Svc |
|             |    |             |    |             |
| [PostgreSQL]|    | [PostgreSQL]|    | [PostgreSQL]|
| orders      |    | users       |    | payments    |
| order_items |    | profiles    |    | invoices    |
+-------------+    +-------------+    +-------------+
      |                  |                  |
      v                  v                  v
  Different DB        Different DB       Different DB
  instance/schema     instance/schema    instance/schema

NO SHARED DATABASE — this is the #1 rule.

Why? If services share a DB:
  - Schema change in one service breaks another
  - One service's query can take down shared DB
  - Deployment coupling returns
  - No independent scaling

Data composition strategies:
  1. API Composition (query multiple services, join in memory)
  2. CQRS + Read Models (denormalized views via events)
  3. GraphQL Federation (schema stitching at gateway)
```

### 7.2 Saga Pattern for Distributed Transactions

```
SAGA: CHOREOGRAPHY-BASED
=========================

OrderSvc    PaymentSvc    InventorySvc    ShippingSvc
   |             |              |               |
   |--OrderCreated event------->|               |
   |             |              |               |
   |             |<-PaymentInitiated event       |
   |<--PaymentProcessed---------|               |
   |             |              |               |
   |--OrderConfirmed event----->|               |
   |             |              |               |
   |             |              |--InventoryReserved event->
   |             |              |               |
   |<-----ShipmentScheduled event---------------|
   |             |              |               |

COMPENSATING TRANSACTIONS (on failure):
   If ShippingSvc fails → InventoryReleased → PaymentRefunded → OrderCancelled

SAGA: ORCHESTRATION-BASED
==========================

                [Saga Orchestrator]
                      |
         +------------+------------+
         |            |            |
         v            v            v
    PaymentSvc   InventorySvc  ShippingSvc
         |            |            |
         |--reply---->|            |
    (success/failure) |            |
                      |--reply---->|
                                   |
                             (success/failure)

Orchestrator holds the saga state and drives the sequence.
Easier to reason about, but adds a bottleneck service.
```

```go
// Saga orchestrator using outbox pattern
// internal/saga/create_order_saga.go
package saga

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/google/uuid"
)

type SagaState string

const (
    SagaStateStarted           SagaState = "STARTED"
    SagaStatePaymentProcessing SagaState = "PAYMENT_PROCESSING"
    SagaStatePaymentConfirmed  SagaState = "PAYMENT_CONFIRMED"
    SagaStateInventoryReserved SagaState = "INVENTORY_RESERVED"
    SagaStateShipmentScheduled SagaState = "SHIPMENT_SCHEDULED"
    SagaStateCompleted         SagaState = "COMPLETED"
    SagaStateFailed            SagaState = "FAILED"
    SagaStateCompensating      SagaState = "COMPENSATING"
)

type CreateOrderSagaData struct {
    SagaID       string
    OrderID      string
    CustomerID   string
    Amount       int64
    Currency     string
    PaymentID    string
    ShipmentID   string
    FailureReason string
    State        SagaState
    CreatedAt    time.Time
    UpdatedAt    time.Time
}

type SagaStep interface {
    Execute(ctx context.Context, data *CreateOrderSagaData) error
    Compensate(ctx context.Context, data *CreateOrderSagaData) error
    Name() string
}

type CreateOrderSaga struct {
    steps []SagaStep
    repo  SagaRepository
}

func NewCreateOrderSaga(
    paymentSvc PaymentService,
    inventorySvc InventoryService,
    shippingSvc ShippingService,
    repo SagaRepository,
) *CreateOrderSaga {
    return &CreateOrderSaga{
        repo: repo,
        steps: []SagaStep{
            &ProcessPaymentStep{paymentSvc},
            &ReserveInventoryStep{inventorySvc},
            &ScheduleShipmentStep{shippingSvc},
        },
    }
}

func (s *CreateOrderSaga) Execute(ctx context.Context, data *CreateOrderSagaData) error {
    data.SagaID    = uuid.New().String()
    data.State     = SagaStateStarted
    data.CreatedAt = time.Now().UTC()
    data.UpdatedAt = time.Now().UTC()

    if err := s.repo.Save(ctx, data); err != nil {
        return fmt.Errorf("save saga: %w", err)
    }

    var completedSteps []SagaStep

    for _, step := range s.steps {
        if err := step.Execute(ctx, data); err != nil {
            data.State         = SagaStateCompensating
            data.FailureReason = fmt.Sprintf("step %s failed: %v", step.Name(), err)
            data.UpdatedAt     = time.Now().UTC()
            _ = s.repo.Save(ctx, data)

            // Compensate in reverse order
            for i := len(completedSteps) - 1; i >= 0; i-- {
                if cerr := completedSteps[i].Compensate(ctx, data); cerr != nil {
                    // Log but continue compensating
                    // In production: use retry with exponential backoff
                }
            }

            data.State     = SagaStateFailed
            data.UpdatedAt = time.Now().UTC()
            _ = s.repo.Save(ctx, data)
            return fmt.Errorf("saga failed at %s: %w", step.Name(), err)
        }
        completedSteps = append(completedSteps, step)
        _ = s.repo.Save(ctx, data)
    }

    data.State     = SagaStateCompleted
    data.UpdatedAt = time.Now().UTC()
    return s.repo.Save(ctx, data)
}
```

### 7.3 CQRS Pattern

```
CQRS: COMMAND QUERY RESPONSIBILITY SEGREGATION
================================================

                        [API Gateway]
                              |
               +--------------+--------------+
               |                             |
         [Commands]                     [Queries]
          (writes)                       (reads)
               |                             |
               v                             v
    +--------------------+      +----------------------+
    | Command Handler    |      | Query Handler        |
    | - CreateOrder      |      | - GetOrder           |
    | - UpdateStatus     |      | - SearchOrders       |
    | - CancelOrder      |      | - GetOrdersByCustomer|
    +--------------------+      +----------------------+
               |                             |
               v                             v
    +--------------------+      +----------------------+
    | Write Model        |      | Read Model           |
    | (normalized,       |      | (denormalized,       |
    |  transactional)    |      |  optimized for query)|
    | [PostgreSQL]       |      | [Elasticsearch]      |
    | orders table       |      | orders index         |
    | order_items table  |      | (flat, pre-joined)   |
    +--------------------+      +----------------------+
               |
               | Events (via CDC or domain events)
               v
    +--------------------+
    | Event Processor    |
    | (updates read model|
    |  asynchronously)   |
    +--------------------+
```

### 7.4 Transactional Outbox Pattern

The outbox pattern ensures atomicity between DB write and event publish:

```
TRANSACTIONAL OUTBOX
======================

WITHOUT OUTBOX (dual-write problem):
  BEGIN TX
    INSERT order
    Commit
  PUBLISH event to Kafka  ← Can fail! Order exists but event not sent.

WITH OUTBOX:
  BEGIN TX
    INSERT order (orders table)
    INSERT event (outbox table)  ← Same transaction!
  COMMIT
  
  [Outbox Poller / CDC (Debezium)] reads outbox table
  → Publishes to Kafka
  → Marks outbox row as published
  
  Guarantee: event published if and only if order persisted.

Outbox Table Schema:
  CREATE TABLE outbox (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id VARCHAR(255) NOT NULL,
    event_type   VARCHAR(255) NOT NULL,
    payload      JSONB        NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    published_at TIMESTAMPTZ  -- NULL = not yet published
  );
  CREATE INDEX idx_outbox_unpublished ON outbox(created_at)
    WHERE published_at IS NULL;
```

```rust
// Rust: Transactional Outbox implementation with sqlx + tokio
// src/repository/order_repository.rs

use sqlx::{PgPool, Transaction, Postgres};
use uuid::Uuid;
use serde_json::Value;
use chrono::{DateTime, Utc};
use anyhow::Result;

#[derive(Debug, sqlx::FromRow)]
pub struct Order {
    pub id:          Uuid,
    pub customer_id: Uuid,
    pub status:      String,
    pub total_cents: i64,
    pub currency:    String,
    pub created_at:  DateTime<Utc>,
    pub updated_at:  DateTime<Utc>,
}

#[derive(Debug)]
pub struct OutboxEntry {
    pub aggregate_id: String,
    pub event_type:   String,
    pub payload:      Value,
}

pub struct OrderRepository {
    pool: PgPool,
}

impl OrderRepository {
    pub fn new(pool: PgPool) -> Self {
        Self { pool }
    }

    /// Create order AND enqueue domain event in same transaction.
    /// Atomicity guaranteed by the ACID properties of PostgreSQL.
    pub async fn create_order_with_event(
        &self,
        order: &Order,
        event: OutboxEntry,
    ) -> Result<()> {
        let mut tx: Transaction<'_, Postgres> = self.pool.begin().await?;

        // Insert order
        sqlx::query!(
            r#"
            INSERT INTO orders (id, customer_id, status, total_cents, currency, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            "#,
            order.id,
            order.customer_id,
            order.status,
            order.total_cents,
            order.currency,
            order.created_at,
            order.updated_at,
        )
        .execute(&mut *tx)
        .await?;

        // Insert outbox event (same transaction)
        sqlx::query!(
            r#"
            INSERT INTO outbox (aggregate_id, event_type, payload)
            VALUES ($1, $2, $3)
            "#,
            event.aggregate_id,
            event.event_type,
            event.payload,
        )
        .execute(&mut *tx)
        .await?;

        // Commit: both order and event persisted atomically
        tx.commit().await?;
        Ok(())
    }
}

// src/outbox/poller.rs
// Outbox relay: polls DB, publishes to Kafka, marks published

use rdkafka::producer::{FutureProducer, FutureRecord};
use rdkafka::ClientConfig;
use std::time::Duration;
use tokio::time::interval;

pub struct OutboxPoller {
    pool:     PgPool,
    producer: FutureProducer,
    topic:    String,
}

impl OutboxPoller {
    pub async fn run(&self) {
        let mut tick = interval(Duration::from_millis(100));
        loop {
            tick.tick().await;
            if let Err(e) = self.process_batch().await {
                tracing::error!("outbox batch error: {:?}", e);
            }
        }
    }

    async fn process_batch(&self) -> Result<()> {
        // SELECT FOR UPDATE SKIP LOCKED — safe for multiple poller instances
        let rows = sqlx::query!(
            r#"
            SELECT id, aggregate_id, event_type, payload::text as payload
            FROM outbox
            WHERE published_at IS NULL
            ORDER BY created_at
            LIMIT 100
            FOR UPDATE SKIP LOCKED
            "#
        )
        .fetch_all(&self.pool)
        .await?;

        for row in &rows {
            let record = FutureRecord::to(&self.topic)
                .key(&row.aggregate_id)
                .payload(row.payload.as_deref().unwrap_or("{}"));

            self.producer
                .send(record, Duration::from_secs(5))
                .await
                .map_err(|(e, _)| e)?;

            // Mark as published
            sqlx::query!(
                "UPDATE outbox SET published_at = NOW() WHERE id = $1",
                row.id
            )
            .execute(&self.pool)
            .await?;
        }

        Ok(())
    }
}
```

---

## 8. Service Discovery & Load Balancing

### 8.1 Service Discovery Patterns

```
CLIENT-SIDE DISCOVERY
======================

Service Registry (etcd/Consul/Eureka)
  +----------------------------------+
  | Service: ordersvc                |
  | Instances:                       |
  |   10.0.1.2:8080 (healthy)        |
  |   10.0.1.3:8080 (healthy)        |
  |   10.0.1.4:8080 (draining)       |
  +----------------------------------+

Client (usersvc):
  1. Query registry: "give me ordersvc instances"
  2. Apply load balancing (round-robin/least-conn/P2C)
  3. Connect directly to chosen instance

Pros: No extra hop, client controls LB algorithm
Cons: Every client needs registry SDK, language-specific

SERVER-SIDE DISCOVERY (DNS-based in K8s)
==========================================

[Client] --> DNS: ordersvc.orders.svc.cluster.local
         <-- [10.96.45.23] (ClusterIP = kube-proxy VIP)
         --> TCP connect to 10.96.45.23:8080
         
kube-proxy (iptables/ipvs mode):
  PREROUTING: 10.96.45.23:8080 → DNAT to one of:
    10.0.1.2:8080 (pod 1)
    10.0.1.3:8080 (pod 2)
    10.0.1.4:8080 (pod 3)

DNS-based service discovery — Kubernetes CoreDNS:
  ordersvc.orders.svc.cluster.local
        ^        ^    ^       ^
     Service  Namespace  Type  Cluster domain
```

### 8.2 Load Balancing Algorithms

```
LOAD BALANCING ALGORITHMS
==========================

Round Robin:
  Requests: 1  2  3  4  5  6
  Backend:  A  B  C  A  B  C

Weighted Round Robin:
  Weights: A=5, B=3, C=2
  Requests: A A A A A B B B C C (per 10)

Least Connections:
  A: 5 conns  B: 2 conns  C: 8 conns
  New request → B (least loaded)

Power of Two Choices (P2C):
  Pick 2 random backends, send to least loaded of the 2.
  Better than random, O(1) per decision, avoids thundering herd.
  Used by: Envoy, gRPC client-side LB, Finagle

Consistent Hashing:
  hash(request_key) → backend
  Used for: cache affinity, stateful services
  
  Ring:
  0                          2^32
  |--A--|--B--|--C--|--A--|--B--|
       ^
       hash("order-123") → maps to B

  Virtual nodes prevent hot spots: each physical node has
  150+ virtual nodes on the ring.
```

```go
// Consistent hashing implementation (used for cache routing)
// pkg/lb/consistent_hash.go
package lb

import (
    "crypto/sha256"
    "encoding/binary"
    "fmt"
    "sort"
    "sync"
)

type ConsistentHash struct {
    mu           sync.RWMutex
    replicas     int
    ring         []uint32          // sorted hash ring
    hashToNode   map[uint32]string // hash → node
    nodes        map[string]bool
}

func NewConsistentHash(replicas int) *ConsistentHash {
    return &ConsistentHash{
        replicas:   replicas,
        hashToNode: make(map[uint32]string),
        nodes:      make(map[string]bool),
    }
}

func (c *ConsistentHash) hash(key string) uint32 {
    h := sha256.Sum256([]byte(key))
    return binary.BigEndian.Uint32(h[:4])
}

func (c *ConsistentHash) Add(node string) {
    c.mu.Lock()
    defer c.mu.Unlock()

    c.nodes[node] = true
    for i := 0; i < c.replicas; i++ {
        vnode := fmt.Sprintf("%s#%d", node, i)
        h := c.hash(vnode)
        c.ring = append(c.ring, h)
        c.hashToNode[h] = node
    }
    sort.Slice(c.ring, func(i, j int) bool { return c.ring[i] < c.ring[j] })
}

func (c *ConsistentHash) Remove(node string) {
    c.mu.Lock()
    defer c.mu.Unlock()

    delete(c.nodes, node)
    newRing := c.ring[:0]
    for _, h := range c.ring {
        if c.hashToNode[h] != node {
            newRing = append(newRing, h)
        } else {
            delete(c.hashToNode, h)
        }
    }
    c.ring = newRing
}

func (c *ConsistentHash) Get(key string) (string, bool) {
    c.mu.RLock()
    defer c.mu.RUnlock()

    if len(c.ring) == 0 {
        return "", false
    }

    h := c.hash(key)
    // Binary search for first ring position >= h
    idx := sort.Search(len(c.ring), func(i int) bool {
        return c.ring[i] >= h
    })
    // Wrap around
    if idx == len(c.ring) {
        idx = 0
    }
    return c.hashToNode[c.ring[idx]], true
}
```

---

## 9. Security Architecture

### 9.1 Zero Trust Security Model

```
ZERO TRUST NETWORK ARCHITECTURE
=================================

Traditional (Castle-and-Moat):
  INTERNET → [Firewall] → INTERNAL NETWORK (trusted)
             Everything inside = trusted
             One breach = full lateral movement

Zero Trust:
  INTERNET → [Identity Proxy] → SERVICE
  INTERNAL → [Identity Proxy] → SERVICE
             Nothing trusted by default
             Every request authenticated + authorized
             Least privilege for every principal

ZERO TRUST PILLARS FOR MICROSERVICES
======================================

1. IDENTITY
   - Every service has a cryptographic identity (SPIFFE/SPIRE)
   - Workload certificates: X.509 SVIDs (SPIFFE Verifiable Identity Documents)
   - Certificate rotation: every 1 hour (short-lived)

2. MUTUAL TLS (mTLS)
   - Both client AND server present certificates
   - Defense against MITM even inside the cluster
   - Implemented by: Istio, Linkerd, Consul Connect

3. AUTHORIZATION
   - Per-RPC authorization policies (not just network-level)
   - RBAC/ABAC enforced at service boundary
   - OPA (Open Policy Agent) for policy evaluation

4. OBSERVABILITY
   - Every request logged with identity metadata
   - Anomaly detection on request patterns
```

### 9.2 mTLS Implementation

```
mTLS HANDSHAKE
===============

Client (ordersvc)              Server (usersvc)
     |                               |
     |----ClientHello--------------->|
     |    (supported ciphers,        |
     |     TLS version, random)      |
     |                               |
     |<---ServerHello----------------|
     |<---Certificate----------------|  ← server cert (SPIFFE ID)
     |<---CertificateRequest---------|  ← demand client cert
     |<---ServerHelloDone------------|
     |                               |
     | Verify server cert:           |
     |   - CA chain valid?           |
     |   - SPIFFE URI SAN matches    |
     |     expected service?         |
     |   - Not expired/revoked?      |
     |                               |
     |----Certificate--------------->|  ← client cert (SPIFFE ID)
     |----ClientKeyExchange--------->|
     |----CertificateVerify--------->|  ← prove private key ownership
     |----ChangeCipherSpec---------->|
     |----Finished (encrypted)------>|
     |                               | Verify client cert:
     |                               |   - CA chain valid?
     |                               |   - SPIFFE URI SAN is
     |                               |     authorized service?
     |<---ChangeCipherSpec-----------|
     |<---Finished (encrypted)-------|
     |                               |
     |====== Encrypted channel ======|

SPIFFE ID format: spiffe://cluster.local/ns/orders/sa/ordersvc
```

```rust
// Rust: mTLS server with rustls
// src/tls/server.rs

use std::sync::Arc;
use std::io::BufReader;
use std::fs::File;
use rustls::{ServerConfig, Certificate, PrivateKey};
use rustls::server::AllowAnyAuthenticatedClient;
use tokio_rustls::TlsAcceptor;
use tokio::net::TcpListener;

pub async fn create_mtls_server(
    bind_addr: &str,
    cert_path: &str,
    key_path:  &str,
    ca_path:   &str,
) -> anyhow::Result<TlsAcceptor> {
    // Load server certificate chain
    let cert_file = File::open(cert_path)?;
    let certs: Vec<Certificate> = rustls_pemfile::certs(&mut BufReader::new(cert_file))?
        .into_iter()
        .map(Certificate)
        .collect();

    // Load server private key
    let key_file = File::open(key_path)?;
    let keys: Vec<PrivateKey> = rustls_pemfile::pkcs8_private_keys(
        &mut BufReader::new(key_file)
    )?
    .into_iter()
    .map(PrivateKey)
    .collect();

    // Load CA certificate for client verification
    let ca_file = File::open(ca_path)?;
    let mut root_store = rustls::RootCertStore::empty();
    for cert in rustls_pemfile::certs(&mut BufReader::new(ca_file))? {
        root_store.add(&Certificate(cert))?;
    }

    // Build server config requiring client certificate
    let client_auth = AllowAnyAuthenticatedClient::new(root_store);

    let config = ServerConfig::builder()
        .with_safe_defaults()
        .with_client_cert_verifier(Arc::new(client_auth))
        .with_single_cert(certs, keys.into_iter().next().unwrap())?;

    Ok(TlsAcceptor::from(Arc::new(config)))
}

// SPIFFE ID validation in certificate
pub fn extract_spiffe_id(cert: &Certificate) -> Option<String> {
    use x509_parser::prelude::*;
    let (_, x509) = X509Certificate::from_der(&cert.0).ok()?;

    for ext in x509.extensions() {
        // OID 2.5.29.17 = Subject Alternative Name
        if ext.oid == oid_registry::OID_X509_EXT_SUBJECT_ALT_NAME {
            let san = SubjectAlternativeName::from_der(ext.value).ok()?;
            for name in &san.1.general_names {
                if let GeneralName::URI(uri) = name {
                    if uri.starts_with("spiffe://") {
                        return Some(uri.to_string());
                    }
                }
            }
        }
    }
    None
}
```

### 9.3 JWT Authentication

```
JWT FLOW IN MICROSERVICES
==========================

User → [API Gateway] → [Auth Service] → JWT issued
                |
                | Validate JWT (signature + claims)
                v
         [Order Service]
         [User Service]
         [Payment Service]
         (all validate JWT independently — no central check)

JWT STRUCTURE
==============

Header.Payload.Signature
   |       |        |
base64  base64    HMAC-SHA256 or RS256

Header: {"alg":"RS256","typ":"JWT","kid":"key-2024-01"}
Payload: {
  "sub":  "user-123",
  "iss":  "https://auth.example.com",
  "aud":  ["orders-api", "users-api"],
  "exp":  1700000000,
  "iat":  1699996400,
  "jti":  "unique-token-id",  ← for revocation
  "roles": ["customer"],
  "scopes": ["orders:read", "orders:write"]
}

VALIDATION STEPS (each microservice):
  1. Decode header, verify alg is RS256 (reject HS256 — symmetric key sharing)
  2. Verify signature using public key (from JWKS endpoint)
  3. Verify exp (not expired)
  4. Verify iss (expected issuer)
  5. Verify aud (this service is in audience list)
  6. Check jti against revocation list (if implemented)
  7. Check scopes for this specific endpoint
```

```go
// JWT validation middleware for Go microservices
// pkg/middleware/jwt.go
package middleware

import (
    "context"
    "crypto/rsa"
    "encoding/json"
    "fmt"
    "net/http"
    "strings"
    "sync"
    "time"

    "github.com/golang-jwt/jwt/v5"
)

type Claims struct {
    jwt.RegisteredClaims
    Roles  []string `json:"roles"`
    Scopes []string `json:"scopes"`
}

type JWKSCache struct {
    mu      sync.RWMutex
    keys    map[string]*rsa.PublicKey
    fetchAt time.Time
    jwksURL string
}

func (c *JWKSCache) GetKey(kid string) (*rsa.PublicKey, error) {
    c.mu.RLock()
    key, ok := c.keys[kid]
    expired := time.Since(c.fetchAt) > 5*time.Minute
    c.mu.RUnlock()

    if ok && !expired {
        return key, nil
    }

    // Refresh JWKS
    c.mu.Lock()
    defer c.mu.Unlock()

    resp, err := http.Get(c.jwksURL)
    if err != nil {
        return nil, fmt.Errorf("fetch JWKS: %w", err)
    }
    defer resp.Body.Close()

    var jwks struct {
        Keys []struct {
            Kid string `json:"kid"`
            N   string `json:"n"`
            E   string `json:"e"`
        } `json:"keys"`
    }
    if err := json.NewDecoder(resp.Body).Decode(&jwks); err != nil {
        return nil, fmt.Errorf("decode JWKS: %w", err)
    }

    c.keys    = make(map[string]*rsa.PublicKey)
    c.fetchAt = time.Now()

    for _, k := range jwks.Keys {
        pubKey, err := parseRSAPublicKey(k.N, k.E)
        if err != nil {
            continue
        }
        c.keys[k.Kid] = pubKey
    }

    if key, ok := c.keys[kid]; ok {
        return key, nil
    }
    return nil, fmt.Errorf("kid %s not found in JWKS", kid)
}

func JWTMiddleware(jwksCache *JWKSCache, audience string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            authHeader := r.Header.Get("Authorization")
            if !strings.HasPrefix(authHeader, "Bearer ") {
                http.Error(w, "missing bearer token", http.StatusUnauthorized)
                return
            }
            tokenStr := strings.TrimPrefix(authHeader, "Bearer ")

            token, err := jwt.ParseWithClaims(
                tokenStr,
                &Claims{},
                func(t *jwt.Token) (interface{}, error) {
                    if _, ok := t.Method.(*jwt.SigningMethodRSA); !ok {
                        return nil, fmt.Errorf("unexpected signing method: %v", t.Header["alg"])
                    }
                    kid, _ := t.Header["kid"].(string)
                    return jwksCache.GetKey(kid)
                },
                jwt.WithAudience(audience),
                jwt.WithIssuer("https://auth.example.com"),
                jwt.WithExpirationRequired(),
            )

            if err != nil || !token.Valid {
                http.Error(w, "invalid token", http.StatusUnauthorized)
                return
            }

            claims := token.Claims.(*Claims)
            ctx := context.WithValue(r.Context(), claimsKey{}, claims)
            next.ServeHTTP(w, r.WithContext(ctx))
        })
    }
}

// RequireScope middleware for endpoint-level authorization
func RequireScope(scope string) func(http.Handler) http.Handler {
    return func(next http.Handler) http.Handler {
        return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
            claims, ok := r.Context().Value(claimsKey{}).(*Claims)
            if !ok {
                http.Error(w, "no claims in context", http.StatusForbidden)
                return
            }
            for _, s := range claims.Scopes {
                if s == scope {
                    next.ServeHTTP(w, r)
                    return
                }
            }
            http.Error(w, "insufficient scope", http.StatusForbidden)
        })
    }
}
```

### 9.4 Secrets Management

```
SECRETS MANAGEMENT FLOW
=========================

BAD (secrets in env vars baked into image):
  Dockerfile:
    ENV DB_PASSWORD=supersecret   ← NEVER DO THIS

BETTER (env from K8s secret):
  kubectl create secret generic db-creds \
    --from-literal=password=supersecret
  
  Pod spec: envFrom: secretRef: name: db-creds
  Problem: secret value still in etcd (base64, not encrypted by default)

BEST (dynamic secrets from Vault):
  +------------+   AppRole auth   +----------+
  | Microservice|---------------->| HashiCorp|
  |   (at boot) |                 | Vault    |
  |             |<--lease+creds---|          |
  |             |   (TTL: 1h)     | [Dynamic |
  | Connect to  |                 |  Secrets]|
  | DB with     |   renew lease   |          |
  | temp creds  |<--------------->|          |
  +------------+                  +----------+
                                        |
                                  PostgreSQL:
                                  CREATE ROLE svc_order_abc123
                                    LOGIN PASSWORD 'dynpw'
                                    VALID UNTIL '2024-01-01 13:00';
                                  GRANT SELECT, INSERT ON orders
                                    TO svc_order_abc123;

  After TTL: Vault revokes the DB role automatically.
  Even if leaked, credential is worthless after 1 hour.

Kubernetes: Use Vault Agent Injector or ESO (External Secrets Operator)
  Injects secrets as in-memory tmpfs volumes, not env vars.
```

---

## 10. Observability: Tracing, Metrics, Logging

### 10.1 The Three Pillars of Observability

```
OBSERVABILITY PILLARS
======================

METRICS (aggregated, dimensional)
  "P99 latency of /orders endpoint = 45ms"
  "Error rate of payment service = 0.1%"
  
  Tools: Prometheus, VictoriaMetrics, Grafana
  Format: OpenMetrics / Prometheus exposition format
  Cardinality: LOW (pre-aggregated)

TRACES (distributed request tracking)
  "This specific request took 234ms:
    - API Gateway: 5ms
    - Order Service: 220ms
      - DB query: 180ms  ← SLOW!"
  
  Tools: Jaeger, Zipkin, Tempo, Honeycomb
  Format: OpenTelemetry (OTLP)
  Cardinality: HIGH (per-request)

LOGS (discrete events)
  "2024-01-15 10:23:45 ERROR order-service [trace=abc123]
   failed to reserve inventory: product SKU-123 out of stock"
  
  Tools: Loki, Elasticsearch, CloudWatch
  Format: JSON structured logs
  Correlation: trace_id in every log line

THE CORRELATION KEY:
  trace_id propagated via HTTP header (traceparent: W3C TraceContext)
  → links metrics, traces, and logs for a single request
```

### 10.2 OpenTelemetry Implementation

```
OPENTELEMETRY ARCHITECTURE
============================

Service A            OTel Collector          Backends
   |                       |
   | OTLP gRPC/HTTP        |
   +---------------------->| Receivers:     +--> Jaeger (traces)
   |  traces               |  OTLP, Zipkin, +--> Prometheus (metrics)
   |  metrics              |  Prometheus,   +--> Loki (logs)
   |  logs                 |  Fluent Bit    +--> CloudWatch
                           |                +--> Datadog
                           | Processors:
                           |  batch, memory_limiter,
                           |  tail_sampling, k8sattributes
                           |
                           | Exporters: OTLP, Jaeger,
                           |  Prometheus, Loki

W3C TraceContext propagation:
  traceparent: 00-{trace-id}-{parent-span-id}-{flags}
  Example:
  traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
                  ^  trace-id (128-bit hex)   ^parent (64-bit) ^sampled
```

```go
// pkg/telemetry/setup.go
package telemetry

import (
    "context"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/exporters/prometheus"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"
    "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
)

func InitTelemetry(ctx context.Context, serviceName, version, otelEndpoint string) (func(), error) {
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceName(serviceName),
            semconv.ServiceVersion(version),
            semconv.DeploymentEnvironment("production"),
        ),
    )
    if err != nil {
        return nil, err
    }

    // Trace exporter (OTLP → Jaeger/Tempo)
    traceExporter, err := otlptracegrpc.New(ctx,
        otlptracegrpc.WithEndpoint(otelEndpoint),
        otlptracegrpc.WithInsecure(), // use TLS in prod
    )
    if err != nil {
        return nil, err
    }

    // Tail sampling: keep 100% of error traces, 1% of OK traces
    sampler := trace.ParentBased(
        trace.TraceIDRatioBased(0.01),
    )

    tp := trace.NewTracerProvider(
        trace.WithBatcher(traceExporter,
            trace.WithBatchTimeout(5*time.Second),
            trace.WithMaxExportBatchSize(512),
        ),
        trace.WithResource(res),
        trace.WithSampler(sampler),
    )

    // Metrics exporter (Prometheus scrape endpoint)
    promExporter, err := prometheus.New()
    if err != nil {
        return nil, err
    }

    mp := metric.NewMeterProvider(
        metric.WithReader(promExporter),
        metric.WithResource(res),
    )

    // Set global providers
    otel.SetTracerProvider(tp)
    otel.SetMeterProvider(mp)
    otel.SetTextMapPropagator(
        propagation.NewCompositeTextMapPropagator(
            propagation.TraceContext{},  // W3C traceparent
            propagation.Baggage{},       // W3C baggage
        ),
    )

    shutdown := func() {
        ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
        defer cancel()
        _ = tp.Shutdown(ctx)
        _ = mp.Shutdown(ctx)
    }

    return shutdown, nil
}

// Instrument an HTTP handler with spans and metrics
func InstrumentedHandler(
    tracer trace.Tracer,
    meter metric.Meter,
    next http.Handler,
) http.Handler {
    requestCounter, _ := meter.Int64Counter("http.requests.total",
        metric.WithDescription("Total HTTP requests"),
    )
    requestDuration, _ := meter.Float64Histogram("http.request.duration_seconds",
        metric.WithDescription("HTTP request duration"),
        metric.WithUnit("s"),
        metric.WithExplicitBucketBoundaries(
            0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0,
        ),
    )

    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx, span := tracer.Start(
            r.Context(),
            fmt.Sprintf("%s %s", r.Method, r.URL.Path),
            oteltrace.WithSpanKind(oteltrace.SpanKindServer),
            oteltrace.WithAttributes(
                semconv.HTTPMethod(r.Method),
                semconv.HTTPURL(r.URL.String()),
                semconv.NetPeerIP(r.RemoteAddr),
            ),
        )
        defer span.End()

        rw := &responseWriter{ResponseWriter: w, statusCode: 200}
        start := time.Now()

        next.ServeHTTP(rw, r.WithContext(ctx))

        duration := time.Since(start).Seconds()
        attrs := []attribute.KeyValue{
            semconv.HTTPMethod(r.Method),
            semconv.HTTPStatusCode(rw.statusCode),
            attribute.String("http.route", chi.RouteContext(ctx).RoutePattern()),
        }

        requestCounter.Add(ctx, 1, metric.WithAttributes(attrs...))
        requestDuration.Record(ctx, duration, metric.WithAttributes(attrs...))

        span.SetAttributes(semconv.HTTPStatusCode(rw.statusCode))
        if rw.statusCode >= 500 {
            span.SetStatus(codes.Error, http.StatusText(rw.statusCode))
        }
    })
}
```

### 10.3 Prometheus Metrics for Microservices

```
KEY METRICS PER MICROSERVICE (USE + RED + Four Golden Signals)
===============================================================

USE (for resources):
  Utilization = cpu_usage_percent, memory_usage_bytes
  Saturation  = request_queue_depth, goroutines_total
  Errors      = error_rate_total

RED (for services):
  Rate    = http_requests_total (counter)
  Errors  = http_requests_total{status=~"5.."}
  Duration = http_request_duration_seconds (histogram)

Four Golden Signals (Google SRE):
  Latency   = P50/P95/P99 of request duration
  Traffic   = requests per second
  Errors    = error rate %
  Saturation = CPU %, memory %, queue depth

PROMETHEUS SCRAPE CONFIG
=========================

# prometheus.yml
scrape_configs:
  - job_name: 'microservices'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      # Only scrape pods with annotation prometheus.io/scrape=true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: 'true'
      # Use custom port from annotation
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: (.+)
        replacement: ${1}
      # Add k8s metadata as labels
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: service
```

### 10.4 Structured Logging

```go
// Structured logging with Zap + trace correlation
// pkg/logging/logger.go
package logging

import (
    "context"
    "go.opentelemetry.io/otel/trace"
    "go.uber.org/zap"
    "go.uber.org/zap/zapcore"
)

// ctxLogger extracts trace context and adds it to every log entry
func FromContext(ctx context.Context, base *zap.Logger) *zap.Logger {
    span := trace.SpanFromContext(ctx)
    if !span.IsRecording() {
        return base
    }
    sc := span.SpanContext()
    return base.With(
        zap.String("trace_id", sc.TraceID().String()),
        zap.String("span_id",  sc.SpanID().String()),
        zap.Bool("trace_sampled", sc.IsSampled()),
    )
}

// NewProductionLogger creates a JSON logger for production
func NewProductionLogger(serviceName, version string) (*zap.Logger, error) {
    cfg := zap.NewProductionConfig()
    cfg.EncoderConfig.TimeKey    = "timestamp"
    cfg.EncoderConfig.EncodeTime = zapcore.RFC3339NanoTimeEncoder
    cfg.EncoderConfig.MessageKey = "message"
    cfg.EncoderConfig.LevelKey   = "level"
    cfg.EncoderConfig.CallerKey  = "caller"

    logger, err := cfg.Build(
        zap.Fields(
            zap.String("service",  serviceName),
            zap.String("version",  version),
        ),
    )
    return logger, err
}

// Usage in handler:
// log := logging.FromContext(ctx, h.logger)
// log.Info("order created",
//     zap.String("order_id", order.ID),
//     zap.String("customer_id", order.CustomerID),
//     zap.Int64("total_cents", order.Total.Amount),
// )
//
// Output:
// {
//   "timestamp": "2024-01-15T10:23:45.123Z",
//   "level": "info",
//   "service": "ordersvc",
//   "version": "v1.2.3",
//   "message": "order created",
//   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
//   "span_id": "00f067aa0ba902b7",
//   "trace_sampled": true,
//   "order_id": "order-uuid",
//   "customer_id": "cust-uuid",
//   "total_cents": 4999,
//   "caller": "httphandler/order_handler.go:87"
// }
```

---

## 11. Container Internals & Orchestration

### 11.1 OCI Container Internals

```
OCI IMAGE STRUCTURE
====================

Image = Manifest + Config + Layers

Manifest (manifest.json):
  {
    "schemaVersion": 2,
    "mediaType": "application/vnd.oci.image.manifest.v1+json",
    "config": { "digest": "sha256:abc...", "size": 7023 },
    "layers": [
      { "digest": "sha256:layer1...", "size": 32654000 },
      { "digest": "sha256:layer2...", "size":   123456 },
      { "digest": "sha256:layer3...", "size":    12345 }
    ]
  }

Layer = tar.gz of filesystem diff
Each Dockerfile instruction (RUN, COPY, ADD) = one layer

OVERLAYFS (how layers are mounted)
=====================================

  Layer 3 (upperdir): /var/lib/docker/overlay2/abc123/diff
    (writable, container-specific)
  ──────────────────────────────────────
  Layer 2 (lowerdir): /var/lib/docker/overlay2/def456/diff
    (read-only, shared between containers using same image)
  ──────────────────────────────────────
  Layer 1 (lowerdir): /var/lib/docker/overlay2/ghi789/diff
    (read-only, base layer)

  Merged view (workdir): /var/lib/docker/overlay2/abc123/merged
    → Presented as rootfs to the container

  Kernel: fs/overlayfs/  (in-tree since 3.18)
  Mount: mount -t overlay overlay
           -o lowerdir=/l2:/l1,upperdir=/upper,workdir=/work /merged

COPY-ON-WRITE:
  Read: check upperdir → lowerdir top-to-bottom
  Write: copy file from lowerdir to upperdir (copy-up), then modify
```

### 11.2 Kubernetes Architecture for Microservices

```
KUBERNETES CONTROL PLANE
=========================

+------------------------------------------+
|           Control Plane Node             |
|                                          |
|  +----------+    +-------------------+   |
|  | kube-API |    | etcd (v3)         |   |
|  | server   |<-->| key-value store   |   |
|  |          |    | cluster state     |   |
|  +----------+    +-------------------+   |
|       |                                  |
|  +----+----+    +-------------------+   |
|  |kube-    |    |kube-controller-   |   |
|  |scheduler|    |manager            |   |
|  |         |    | - Node controller |   |
|  +---------+    | - Deploy ctrl     |   |
|                 | - Service ctrl    |   |
|                 | - Job controller  |   |
|                 +-------------------+   |
+------------------------------------------+

WORKER NODE
============
+------------------------------------------+
|              Worker Node                 |
|                                          |
|  +----------+    +-------------------+   |
|  | kubelet  |    | kube-proxy        |   |
|  | (PodSpec |    | (iptables/ipvs    |   |
|  |  mgmt)   |    |  rules for Svc)   |   |
|  +----------+    +-------------------+   |
|       |                                  |
|  +----v------------------------------+   |
|  |  Container Runtime (containerd)   |   |
|  |  +-----------+  +-----------+     |   |
|  |  | Pod: A    |  | Pod: B    |     |   |
|  |  | [ordersvc]|  | [usersvc] |     |   |
|  |  | [envoy]   |  | [envoy]   |     |   |
|  |  +-----------+  +-----------+     |   |
|  +-----------------------------------+   |
|                                          |
|  CNI Plugin (Calico/Cilium/Flannel)      |
|  Pod CIDR: 10.244.1.0/24                 |
+------------------------------------------+

POD NETWORKING (with Cilium eBPF)
===================================

Pod A (10.244.1.2) → Pod B (10.244.2.5)

  Pod A → veth → Cilium eBPF (tc hook) → 
  If same node: redirect to destination veth (no kernel routing)
  If different node: encapsulate (VXLAN/Geneve) → NodeIP routing
  
  Cilium replaces kube-proxy entirely with eBPF maps:
    CT map (connection tracking): 4-tuple → backend
    LB map: ServiceIP:Port → backend pods
```

### 11.3 Kubernetes Deployment for Microservices

```yaml
# k8s/ordersvc/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ordersvc
  namespace: orders
  labels:
    app: ordersvc
    version: v1.2.3
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ordersvc
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0   # zero-downtime: never take pods down before new ones up
      maxSurge: 1         # at most 1 extra pod during rollout
  template:
    metadata:
      labels:
        app: ordersvc
        version: v1.2.3
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port:   "9090"
        prometheus.io/path:   "/metrics"
    spec:
      serviceAccountName: ordersvc
      
      # Security: hardened pod spec
      securityContext:
        runAsNonRoot: true
        runAsUser:    10001
        runAsGroup:   10001
        fsGroup:      10001
        seccompProfile:
          type: RuntimeDefault   # seccomp filter
      
      # Graceful termination
      terminationGracePeriodSeconds: 60
      
      # Spread across zones for HA
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: ordersvc
      
      containers:
        - name: ordersvc
          image: registry.example.com/ordersvc:v1.2.3
          imagePullPolicy: Always
          
          ports:
            - name: http
              containerPort: 8080
            - name: grpc
              containerPort: 9090
            - name: metrics
              containerPort: 9091
          
          # Security context per-container
          securityContext:
            allowPrivilegeEscalation: false
            readOnlyRootFilesystem: true
            capabilities:
              drop: ["ALL"]
          
          # Resource limits (enforced by cgroups)
          resources:
            requests:
              cpu:    "100m"    # 0.1 CPU (scheduler hint)
              memory: "128Mi"
            limits:
              cpu:    "500m"    # 0.5 CPU (cgroup cpu.max)
              memory: "512Mi"   # cgroup memory.max
          
          # Environment (non-secret config)
          env:
            - name: SERVICE_NAME
              value: ordersvc
            - name: LOG_LEVEL
              value: info
            - name: OTLP_ENDPOINT
              value: otel-collector.monitoring.svc.cluster.local:4317
            # Pod metadata injection
            - name: POD_NAME
              valueFrom:
                fieldRef:
                  fieldPath: metadata.name
            - name: POD_NAMESPACE
              valueFrom:
                fieldRef:
                  fieldPath: metadata.namespace
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          
          # Secrets from Vault via ESO
          envFrom:
            - secretRef:
                name: ordersvc-db-credentials
          
          # Writable tmpfs for temp files (root FS is read-only)
          volumeMounts:
            - name: tmp
              mountPath: /tmp
          
          # Health checks
          livenessProbe:
            httpGet:
              path: /healthz/live
              port: 8080
            initialDelaySeconds: 10
            periodSeconds: 15
            failureThreshold: 3
            timeoutSeconds: 5
          
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
            failureThreshold: 3
          
          startupProbe:
            httpGet:
              path: /healthz/startup
              port: 8080
            failureThreshold: 30
            periodSeconds: 2
          
          # Graceful shutdown: handle SIGTERM
          lifecycle:
            preStop:
              exec:
                command: ["/bin/sleep", "5"]  # drain in-flight requests
      
      volumes:
        - name: tmp
          emptyDir:
            medium: Memory    # tmpfs, not disk
```

---

## 12. Cloud Infrastructure & Deployment

### 12.1 Infrastructure as Code with Terraform

```hcl
# infra/terraform/modules/microservice/main.tf
# Generic module for deploying a microservice on AWS EKS

terraform {
  required_providers {
    aws        = { source = "hashicorp/aws",        version = "~> 5.0" }
    kubernetes = { source = "hashicorp/kubernetes",  version = "~> 2.0" }
    helm       = { source = "hashicorp/helm",        version = "~> 2.0" }
  }
}

# Variables
variable "service_name"    { type = string }
variable "service_version" { type = string }
variable "namespace"       { type = string }
variable "replicas"        { type = number; default = 3 }
variable "cpu_request"     { type = string; default = "100m" }
variable "cpu_limit"       { type = string; default = "500m" }
variable "memory_request"  { type = string; default = "128Mi" }
variable "memory_limit"    { type = string; default = "512Mi" }
variable "image_repository"{ type = string }
variable "db_instance_class" { type = string; default = "db.t3.medium" }

# RDS PostgreSQL per service (database-per-service pattern)
resource "aws_db_instance" "service_db" {
  identifier        = "${var.service_name}-db"
  engine            = "postgres"
  engine_version    = "16.1"
  instance_class    = var.db_instance_class
  allocated_storage = 20
  storage_encrypted = true
  kms_key_id        = aws_kms_key.db_key.arn

  db_name  = replace(var.service_name, "-", "_")
  username = var.service_name
  password = random_password.db_password.result

  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = aws_db_subnet_group.private.name

  backup_retention_period = 7
  deletion_protection     = true
  skip_final_snapshot     = false
  final_snapshot_identifier = "${var.service_name}-final"

  performance_insights_enabled = true
  monitoring_interval          = 60
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn

  tags = {
    Service     = var.service_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}

# IAM Role for IRSA (IAM Roles for Service Accounts)
# Allows K8s pods to assume AWS IAM roles without static creds
resource "aws_iam_role" "service_role" {
  name = "${var.service_name}-k8s-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = var.eks_oidc_provider_arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "${var.eks_oidc_provider}:sub" = "system:serviceaccount:${var.namespace}:${var.service_name}"
          "${var.eks_oidc_provider}:aud" = "sts.amazonaws.com"
        }
      }
    }]
  })
}

# Service-specific S3 access (example)
resource "aws_iam_role_policy" "service_s3" {
  name = "${var.service_name}-s3-policy"
  role = aws_iam_role.service_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = ["s3:GetObject", "s3:PutObject"]
      Resource = "arn:aws:s3:::${var.service_name}-bucket/*"
    }]
  })
}

# Kubernetes resources
resource "kubernetes_namespace" "service_ns" {
  metadata {
    name = var.namespace
    labels = {
      "istio-injection" = "enabled"
    }
  }
}

resource "kubernetes_service_account" "service_sa" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
    annotations = {
      "eks.amazonaws.com/role-arn" = aws_iam_role.service_role.arn
    }
  }
}

# Horizontal Pod Autoscaler
resource "kubernetes_horizontal_pod_autoscaler_v2" "service_hpa" {
  metadata {
    name      = var.service_name
    namespace = var.namespace
  }
  spec {
    min_replicas = var.replicas
    max_replicas = var.replicas * 10

    scale_target_ref {
      api_version = "apps/v1"
      kind        = "Deployment"
      name        = var.service_name
    }

    metric {
      type = "Resource"
      resource {
        name = "cpu"
        target {
          type                = "Utilization"
          average_utilization = 70
        }
      }
    }

    metric {
      type = "Pods"
      pods {
        metric { name = "http_requests_per_second" }
        target {
          type          = "AverageValue"
          average_value = "1000"  # 1000 RPS per pod
        }
      }
    }

    behavior {
      scale_up {
        stabilization_window_seconds = 60
        select_policy                = "Max"
        policy {
          type           = "Percent"
          value          = 100  # double replicas per scaling event
          period_seconds = 60
        }
      }
      scale_down {
        stabilization_window_seconds = 300  # 5min cooldown
        select_policy                = "Min"
        policy {
          type           = "Percent"
          value          = 10
          period_seconds = 60
        }
      }
    }
  }
}
```

### 12.2 CI/CD Pipeline

```
CI/CD PIPELINE FOR MICROSERVICES
==================================

[Developer] → git push → [GitHub/GitLab]
                               |
                    +----------v-----------+
                    |     CI Pipeline      |
                    |                      |
                    | 1. Unit tests         |
                    | 2. Integration tests  |
                    | 3. Security scan      |
                    |    (Trivy, Snyk,      |
                    |     gosec, cargo-     |
                    |     audit)            |
                    | 4. Build OCI image    |
                    | 5. Sign image         |
                    |    (cosign + Sigstore)|
                    | 6. Push to registry   |
                    | 7. Update GitOps repo |
                    +----------+-----------+
                               |
                    +----------v-----------+
                    |  GitOps (Argo CD /   |
                    |  Flux)               |
                    |                      |
                    | Watches manifests    |
                    | in git               |
                    | Reconciles K8s       |
                    | cluster state        |
                    |                      |
                    | Progressive delivery:|
                    | [10%] → [25%] →      |
                    | [50%] → [100%]       |
                    | (Argo Rollouts /     |
                    |  Flagger canary)     |
                    +----------------------+

IMAGE SIGNING SUPPLY CHAIN
============================

Build → Sign with cosign (ECDSA P-256) → Push to OCI registry
  |         |
  |    Key stored in KMS (AWS KMS / GCP KMS)
  |    Attestation stored in Rekor (Sigstore transparency log)
  |
Deploy → Kubernetes Admission Webhook verifies signature
           (Kyverno policy / Connaisseur)
           Rejects unsigned or unverified images
```

---

## 13. Resilience Patterns

### 13.1 Circuit Breaker

```
CIRCUIT BREAKER STATE MACHINE
==============================

         failure_threshold exceeded
CLOSED ─────────────────────────────> OPEN
  |  ^                                   |
  |  |  success_threshold exceeded       |
  |  +──────────────────────────────     |
  |                         HALF-OPEN <──+
  |                         (probe)      timeout elapsed
  |                              |
  |                              | first request passes through
  +──────────────────────────────+

CLOSED:  Normal operation. Track failures.
         If failures >= threshold in window → OPEN

OPEN:    Fail fast. Return error immediately.
         No requests reach downstream.
         After timeout (e.g., 30s) → HALF-OPEN

HALF-OPEN: Allow single probe request through.
           Success → CLOSED
           Failure → OPEN (reset timer)

Prevents:
  - Cascading failures
  - Resource exhaustion (no waiting for dead service)
  - Gives failing service time to recover
```

```go
// pkg/resilience/circuit_breaker.go
package resilience

import (
    "errors"
    "sync"
    "time"
)

var ErrCircuitOpen = errors.New("circuit breaker is open")

type State int

const (
    StateClosed   State = iota
    StateHalfOpen
    StateOpen
)

type CircuitBreaker struct {
    mu sync.RWMutex

    name             string
    maxFailures      int
    timeout          time.Duration
    halfOpenMaxCalls int

    state            State
    failures         int
    successes        int
    lastFailureTime  time.Time
    halfOpenCalls    int
}

func NewCircuitBreaker(name string, maxFailures int, timeout time.Duration) *CircuitBreaker {
    return &CircuitBreaker{
        name:             name,
        maxFailures:      maxFailures,
        timeout:          timeout,
        halfOpenMaxCalls: 1,
        state:            StateClosed,
    }
}

func (cb *CircuitBreaker) Execute(fn func() error) error {
    cb.mu.Lock()
    state := cb.currentState()

    switch state {
    case StateOpen:
        cb.mu.Unlock()
        return ErrCircuitOpen

    case StateHalfOpen:
        if cb.halfOpenCalls >= cb.halfOpenMaxCalls {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
        cb.halfOpenCalls++
    }
    cb.mu.Unlock()

    err := fn()

    cb.mu.Lock()
    defer cb.mu.Unlock()

    if err != nil {
        cb.onFailure()
        return err
    }
    cb.onSuccess()
    return nil
}

func (cb *CircuitBreaker) currentState() State {
    switch cb.state {
    case StateOpen:
        if time.Since(cb.lastFailureTime) > cb.timeout {
            cb.state        = StateHalfOpen
            cb.halfOpenCalls = 0
            return StateHalfOpen
        }
        return StateOpen
    default:
        return cb.state
    }
}

func (cb *CircuitBreaker) onFailure() {
    cb.failures++
    cb.lastFailureTime = time.Now()

    switch cb.state {
    case StateClosed:
        if cb.failures >= cb.maxFailures {
            cb.state = StateOpen
        }
    case StateHalfOpen:
        cb.state = StateOpen
    }
}

func (cb *CircuitBreaker) onSuccess() {
    switch cb.state {
    case StateHalfOpen:
        cb.successes++
        if cb.successes >= cb.halfOpenMaxCalls {
            cb.state    = StateClosed
            cb.failures = 0
            cb.successes = 0
        }
    case StateClosed:
        cb.failures = 0
    }
}
```

### 13.2 Retry with Exponential Backoff + Jitter

```go
// pkg/resilience/retry.go
package resilience

import (
    "context"
    "errors"
    "math/rand"
    "time"
)

type RetryConfig struct {
    MaxAttempts     int
    InitialInterval time.Duration
    MaxInterval     time.Duration
    Multiplier      float64
    Jitter          float64           // 0.0 to 1.0
    RetryableErrors []error           // nil = retry all
}

var DefaultRetryConfig = RetryConfig{
    MaxAttempts:     3,
    InitialInterval: 100 * time.Millisecond,
    MaxInterval:     10 * time.Second,
    Multiplier:      2.0,
    Jitter:          0.3,
}

func WithRetry(ctx context.Context, cfg RetryConfig, fn func(ctx context.Context) error) error {
    var lastErr error
    interval := cfg.InitialInterval

    for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
        if err := ctx.Err(); err != nil {
            return err // context cancelled
        }

        lastErr = fn(ctx)
        if lastErr == nil {
            return nil
        }

        // Check if error is retryable
        if !isRetryable(lastErr, cfg.RetryableErrors) {
            return lastErr
        }

        if attempt == cfg.MaxAttempts-1 {
            break
        }

        // Calculate next interval with jitter
        // Full jitter: sleep = random(0, min(cap, base * 2^attempt))
        // Decorrelated jitter (AWS): sleep = random(base, sleep * 3)
        jitter := 1.0 + cfg.Jitter*(rand.Float64()*2-1) // ±jitter%
        sleep := time.Duration(float64(interval) * jitter)
        if sleep > cfg.MaxInterval {
            sleep = cfg.MaxInterval
        }

        select {
        case <-ctx.Done():
            return ctx.Err()
        case <-time.After(sleep):
        }

        interval = time.Duration(float64(interval) * cfg.Multiplier)
        if interval > cfg.MaxInterval {
            interval = cfg.MaxInterval
        }
    }

    return lastErr
}

func isRetryable(err error, retryableErrors []error) bool {
    if len(retryableErrors) == 0 {
        return true // retry everything
    }
    for _, re := range retryableErrors {
        if errors.Is(err, re) {
            return true
        }
    }
    return false
}
```

### 13.3 Bulkhead Pattern

```
BULKHEAD PATTERN
=================

Without bulkhead:
  All service calls share one connection pool.
  Slow UserService drains all connections → OrderService starved.

  [Thread Pool: 100 threads]
  ├── 80 threads stuck waiting on slow UserService
  └── 20 threads for everything else (starved)

With bulkhead:
  Separate resource pools per downstream dependency.

  [Pool: 30 threads for UserService]
  ├── UserService slow → only this pool affected
  └── Other pools unaffected

  [Pool: 30 threads for PaymentService]
  [Pool: 40 threads for InventoryService]

Implementation: semaphore per downstream service.
```

```go
// pkg/resilience/bulkhead.go
package resilience

import (
    "context"
    "errors"
    "time"
)

var ErrBulkheadFull = errors.New("bulkhead: at capacity")

type Bulkhead struct {
    sem chan struct{}
    name string
}

func NewBulkhead(name string, maxConcurrent int) *Bulkhead {
    return &Bulkhead{
        name: name,
        sem:  make(chan struct{}, maxConcurrent),
    }
}

func (b *Bulkhead) Execute(ctx context.Context, timeout time.Duration, fn func() error) error {
    // Try to acquire a slot
    select {
    case b.sem <- struct{}{}:
        // Acquired
    case <-time.After(timeout):
        return ErrBulkheadFull
    case <-ctx.Done():
        return ctx.Err()
    }

    defer func() { <-b.sem }()
    return fn()
}

func (b *Bulkhead) Available() int {
    return cap(b.sem) - len(b.sem)
}
```

---

## 14. Testing Strategies

### 14.1 Testing Pyramid for Microservices

```
TESTING PYRAMID (Sam Newman's Microservice Testing)
=====================================================

                    /\
                   /  \
                  / UI  \          Slow, expensive, brittle
                 / E2E   \         Few: smoke tests only
                /----------\
               / Integration \     Medium: test service boundaries
              / (Contract)    \    Consumer-Driven Contract Tests
             /------------------\  (Pact)
            /     Unit Tests     \ Fast, isolated, many
           /  (Domain + Use Case) \
          /_______________________ \

Unit:        Test domain logic in isolation. Mock ports.
Contract:    Verify service API contracts between teams.
Integration: Test adapter implementations (DB, messaging).
E2E:         Full system smoke tests. Minimal.
```

### 14.2 Consumer-Driven Contract Testing (Pact)

```
PACT CONTRACT TESTING
======================

CONSUMER (OrderService needs UserService):
  1. Write consumer test defining expected interactions
  2. Run test → generates pact file (contract)
  3. Publish pact to Pact Broker

PROVIDER (UserService):
  1. Fetches pact from Pact Broker
  2. Verifies it can fulfill the contract
  3. Publishes verification result

[Order Svc]──writes──>[Pact File]──publish──>[Pact Broker]
                                                    |
                                            [User Svc]──verifies──>✓

Benefits:
  - No shared test environment needed
  - Consumer controls API expectations
  - Provider knows who depends on what
  - Safe to refactor: failing pact = breaking change

WORKFLOW IN CI:
  Consumer PR: run consumer tests → publish pact
  Provider PR: can-i-deploy? checks all consumer pacts pass
```

```go
// consumer_test.go — OrderService consuming UserService
// Using pact-go v2
package integration_test

import (
    "fmt"
    "net/http"
    "testing"

    "github.com/pact-foundation/pact-go/v2/consumer"
    "github.com/pact-foundation/pact-go/v2/matchers"
)

func TestOrderServiceUserClient(t *testing.T) {
    pact, err := consumer.NewV4Pact(consumer.MockHTTPProviderConfig{
        Consumer: "ordersvc",
        Provider: "usersvc",
    })
    if err != nil {
        t.Fatal(err)
    }

    // Define the interaction
    err = pact.
        AddInteraction().
        Given("user 123 exists").
        UponReceiving("a request for user 123").
        WithCompleteRequest(consumer.Request{
            Method: http.MethodGet,
            Path:   matchers.String("/v1/users/123"),
            Headers: matchers.MapMatcher{
                "Authorization": matchers.Regex("Bearer .+", "Bearer test-token"),
            },
        }).
        WithCompleteResponse(consumer.Response{
            Status: 200,
            Headers: matchers.MapMatcher{
                "Content-Type": matchers.String("application/json"),
            },
            Body: matchers.MatchV2(map[string]interface{}{
                "id":    matchers.UUID(),
                "email": matchers.Email(),
                "name":  matchers.Regex("[A-Za-z ]+", "John Doe"),
            }),
        }).
        ExecuteTest(t, func(config consumer.MockServerConfig) error {
            // Use the mock server URL in the client under test
            userClient := NewUserServiceClient(
                fmt.Sprintf("http://%s:%d", config.Host, config.Port),
            )

            user, err := userClient.GetUser(t.Context(), "123", "test-token")
            if err != nil {
                return err
            }
            if user.ID == "" {
                return fmt.Errorf("expected user ID to be set")
            }
            return nil
        })

    if err != nil {
        t.Fatal(err)
    }
}
```

### 14.3 Integration Testing with Testcontainers

```go
// integration/order_repository_test.go
package integration_test

import (
    "context"
    "testing"
    "time"

    "github.com/testcontainers/testcontainers-go"
    "github.com/testcontainers/testcontainers-go/modules/postgres"
    "github.com/jackc/pgx/v5/pgxpool"
    "github.com/stretchr/testify/require"

    "github.com/yourorg/ordersvc/internal/adapters/repository"
)

func TestOrderRepository_Integration(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping integration test")
    }

    ctx := context.Background()

    // Spin up real PostgreSQL in Docker
    pgContainer, err := postgres.RunContainer(ctx,
        testcontainers.WithImage("postgres:16-alpine"),
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        postgres.WithInitScripts("../../migrations/001_create_orders.sql"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready to accept connections").
                WithOccurrence(2).
                WithStartupTimeout(30*time.Second),
        ),
    )
    require.NoError(t, err)
    defer pgContainer.Terminate(ctx)

    connStr, err := pgContainer.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)

    pool, err := pgxpool.New(ctx, connStr)
    require.NoError(t, err)
    defer pool.Close()

    repo := repository.NewPostgresOrderRepository(pool)

    t.Run("CreateAndRetrieveOrder", func(t *testing.T) {
        order, err := domain.NewOrder("customer-123", []domain.OrderItem{
            {ProductID: "prod-1", Quantity: 2, UnitPrice: domain.Money{Amount: 1000, Currency: "USD"}},
        })
        require.NoError(t, err)

        err = repo.Save(ctx, order)
        require.NoError(t, err)

        retrieved, err := repo.FindByID(ctx, order.ID)
        require.NoError(t, err)
        require.Equal(t, order.ID, retrieved.ID)
        require.Equal(t, order.CustomerID, retrieved.CustomerID)
        require.Equal(t, order.Total, retrieved.Total)
    })

    t.Run("OutboxEntryCreated", func(t *testing.T) {
        // Verify transactional outbox pattern
        var count int
        err := pool.QueryRow(ctx,
            "SELECT COUNT(*) FROM outbox WHERE published_at IS NULL").
            Scan(&count)
        require.NoError(t, err)
        require.Equal(t, 1, count) // from previous test
    })
}
```

---

## 15. Event-Driven Architecture & CQRS

### 15.1 Apache Kafka for Microservices

```
KAFKA ARCHITECTURE
===================

Producer (OrderSvc)         Kafka Cluster              Consumer (ShippingSvc)
       |                          |                            |
       | ProduceRecord            |                            |
       +------------------------->|                            |
                                  | Topic: order-events        |
                                  | Partition 0: [msg0][msg2]  |
                                  | Partition 1: [msg1][msg3]  |
                                  | Partition 2: [msg4][msg5]  |
                                  |                            |
                                  |  Consumer Group: shipping  |
                                  |  P0 → ShippingSvc inst 0   |
                                  |  P1 → ShippingSvc inst 1   |
                                  |  P2 → ShippingSvc inst 2   |
                                  |                   <--------+
                                  |               FetchRecords |
                                  |                            |

KEY CONCEPTS:
  Topic: logical stream of events
  Partition: ordered, immutable log. Unit of parallelism.
  Consumer Group: set of consumers sharing partition ownership.
    Each partition assigned to exactly one consumer per group.
    Scale consumers = add partitions.
  Offset: position in partition log. Consumer tracks its own.
  Retention: events kept for configurable time (default 7 days).
    Unlike queues, events can be re-read (replay).

ORDERING GUARANTEE:
  Within a partition: strict ordering by offset
  Across partitions: NO ordering guarantee
  Design: use business key as partition key
    ProducerRecord("order-events", orderID, payload)
    → hash(orderID) % numPartitions → deterministic partition
    → all events for order-123 go to same partition → ordered
```

```go
// pkg/messaging/kafka_producer.go
package messaging

import (
    "context"
    "encoding/json"
    "fmt"
    "time"

    "github.com/IBM/sarama"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
)

type KafkaProducer struct {
    producer sarama.AsyncProducer
    topic    string
}

func NewKafkaProducer(brokers []string, topic string) (*KafkaProducer, error) {
    cfg := sarama.NewConfig()
    cfg.Version            = sarama.V3_0_0_0
    cfg.Producer.Return.Successes = true
    cfg.Producer.Return.Errors    = true

    // Exactly-once semantics (requires Kafka >= 0.11, transactions)
    cfg.Producer.Idempotent = true
    cfg.Net.MaxOpenRequests = 1  // required for idempotent producer

    // Compression
    cfg.Producer.Compression = sarama.CompressionSnappy

    // Batching for throughput
    cfg.Producer.Flush.Bytes    = 64 * 1024  // 64KB
    cfg.Producer.Flush.Frequency = 10 * time.Millisecond

    // ACK from all in-sync replicas
    cfg.Producer.RequiredAcks = sarama.WaitForAll

    producer, err := sarama.NewAsyncProducer(brokers, cfg)
    if err != nil {
        return nil, fmt.Errorf("create producer: %w", err)
    }

    p := &KafkaProducer{producer: producer, topic: topic}

    // Handle delivery reports in background
    go p.handleResults()

    return p, nil
}

type Event struct {
    EventID   string          `json:"event_id"`
    EventType string          `json:"event_type"`
    OccurredAt time.Time      `json:"occurred_at"`
    AggregateID string        `json:"aggregate_id"`
    Payload   json.RawMessage `json:"payload"`
    TraceHeaders map[string]string `json:"trace_headers,omitempty"`
}

func (p *KafkaProducer) PublishEvent(ctx context.Context, partitionKey string, event Event) error {
    // Inject trace context into event for distributed tracing across async boundary
    carrier := make(propagation.MapCarrier)
    otel.GetTextMapPropagator().Inject(ctx, carrier)
    event.TraceHeaders = map[string]string(carrier)

    payload, err := json.Marshal(event)
    if err != nil {
        return fmt.Errorf("marshal event: %w", err)
    }

    msg := &sarama.ProducerMessage{
        Topic:     p.topic,
        Key:       sarama.StringEncoder(partitionKey),  // ensures ordering
        Value:     sarama.ByteEncoder(payload),
        Timestamp: time.Now(),
        Headers: []sarama.RecordHeader{
            {Key: []byte("event-type"), Value: []byte(event.EventType)},
            {Key: []byte("content-type"), Value: []byte("application/json")},
        },
    }

    select {
    case p.producer.Input() <- msg:
        return nil
    case <-ctx.Done():
        return ctx.Err()
    }
}

func (p *KafkaProducer) handleResults() {
    for {
        select {
        case success := <-p.producer.Successes():
            _ = success // could record metrics here
        case err := <-p.producer.Errors():
            // Log + alert; producer will retry automatically for retryable errors
            // For permanent failures, DLQ or manual intervention needed
            fmt.Printf("producer error: %v\n", err)
        }
    }
}
```

```go
// pkg/messaging/kafka_consumer.go
package messaging

import (
    "context"
    "encoding/json"
    "fmt"

    "github.com/IBM/sarama"
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
    "go.uber.org/zap"
)

type EventHandler func(ctx context.Context, event Event) error

type KafkaConsumerGroup struct {
    group    sarama.ConsumerGroup
    topics   []string
    handlers map[string]EventHandler
    logger   *zap.Logger
}

// cgHandler implements sarama.ConsumerGroupHandler
type cgHandler struct {
    handlers map[string]EventHandler
    logger   *zap.Logger
}

func (h *cgHandler) Setup(sarama.ConsumerGroupSession) error   { return nil }
func (h *cgHandler) Cleanup(sarama.ConsumerGroupSession) error { return nil }

func (h *cgHandler) ConsumeClaim(
    session sarama.ConsumerGroupSession,
    claim sarama.ConsumerGroupClaim,
) error {
    for msg := range claim.Messages() {
        var event Event
        if err := json.Unmarshal(msg.Value, &event); err != nil {
            h.logger.Error("unmarshal event", zap.Error(err),
                zap.String("topic", msg.Topic),
                zap.Int32("partition", msg.Partition),
                zap.Int64("offset", msg.Offset),
            )
            // Commit offset even on unmarshal error to avoid poison pill
            session.MarkMessage(msg, "")
            continue
        }

        // Extract trace context from event headers (cross-process propagation)
        carrier := propagation.MapCarrier(event.TraceHeaders)
        ctx := otel.GetTextMapPropagator().Extract(context.Background(), carrier)
        ctx, span := otel.Tracer("consumer").Start(ctx, "consume."+event.EventType)

        handler, ok := h.handlers[event.EventType]
        if !ok {
            span.End()
            session.MarkMessage(msg, "")
            continue
        }

        if err := handler(ctx, event); err != nil {
            span.RecordError(err)
            span.End()
            h.logger.Error("handle event failed",
                zap.String("event_type", event.EventType),
                zap.String("event_id", event.EventID),
                zap.Error(err),
            )
            // Don't MarkMessage → will be reprocessed after rebalance
            // In production: implement dead letter queue for repeated failures
            continue
        }

        span.End()
        // At-least-once: commit only after successful processing
        session.MarkMessage(msg, "")
    }
    return nil
}
```

### 15.2 Event Sourcing

```
EVENT SOURCING
===============

Traditional (state-based):
  orders table: id=123, status=SHIPPED, total=49.99
  ← only current state. History lost.

Event Sourcing (event-based):
  order_events stream for aggregate order-123:
    [0] OrderCreated  {customer:456, items:[...], total:49.99}  t=10:00
    [1] PaymentTaken  {payment_id:pay-789, amount:49.99}        t=10:01
    [2] OrderConfirmed {}                                       t=10:01
    [3] ItemShipped   {tracking:1Z999...}                       t=10:30
    [4] OrderDelivered {}                                       t=11:45

  Current state = apply all events in order (fold/reduce)

Benefits:
  - Complete audit log
  - Time travel: reconstruct state at any point in time
  - Event replay: rebuild read models, debug, analytics
  - Natural pub/sub: other services subscribe to events

Drawbacks:
  - Eventual consistency of read models
  - Schema evolution complexity (event versioning)
  - Performance: need snapshots for aggregates with many events

SNAPSHOT OPTIMIZATION:
  Every N events (e.g., 50), persist current state as snapshot.
  Load: find latest snapshot + events after it.

Event Store: EventStoreDB, Apache Kafka (with compaction disabled),
             PostgreSQL (events table per aggregate type)
```

```rust
// Rust: Event sourcing with aggregate
// src/domain/order_aggregate.rs

use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use std::fmt;

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(tag = "type", rename_all = "SCREAMING_SNAKE_CASE")]
pub enum OrderEvent {
    OrderCreated {
        customer_id: Uuid,
        items: Vec<OrderItemData>,
        total_cents: i64,
        currency: String,
        occurred_at: DateTime<Utc>,
    },
    PaymentTaken {
        payment_id: Uuid,
        amount_cents: i64,
        occurred_at: DateTime<Utc>,
    },
    OrderConfirmed {
        occurred_at: DateTime<Utc>,
    },
    ItemShipped {
        tracking_number: String,
        carrier: String,
        occurred_at: DateTime<Utc>,
    },
    OrderDelivered {
        occurred_at: DateTime<Utc>,
    },
    OrderCancelled {
        reason: String,
        occurred_at: DateTime<Utc>,
    },
}

#[derive(Debug, Clone, PartialEq)]
pub enum OrderStatus {
    Pending,
    PaymentPending,
    Confirmed,
    Shipped,
    Delivered,
    Cancelled,
}

#[derive(Debug, Clone)]
pub struct OrderState {
    pub id:          Uuid,
    pub customer_id: Uuid,
    pub status:      OrderStatus,
    pub total_cents: i64,
    pub currency:    String,
    pub version:     u64,  // optimistic concurrency
}

/// Apply a single event to produce new state (pure function)
pub fn apply_event(state: Option<OrderState>, event: &OrderEvent) -> Option<OrderState> {
    match event {
        OrderEvent::OrderCreated { customer_id, total_cents, currency, .. } => {
            // State must be None (first event)
            assert!(state.is_none(), "OrderCreated on existing aggregate");
            Some(OrderState {
                id:          Uuid::new_v4(), // set from stream ID externally
                customer_id: *customer_id,
                status:      OrderStatus::Pending,
                total_cents: *total_cents,
                currency:    currency.clone(),
                version:     1,
            })
        }
        OrderEvent::PaymentTaken { .. } => {
            state.map(|mut s| {
                s.status  = OrderStatus::PaymentPending;
                s.version += 1;
                s
            })
        }
        OrderEvent::OrderConfirmed { .. } => {
            state.map(|mut s| {
                s.status  = OrderStatus::Confirmed;
                s.version += 1;
                s
            })
        }
        OrderEvent::ItemShipped { .. } => {
            state.map(|mut s| {
                s.status  = OrderStatus::Shipped;
                s.version += 1;
                s
            })
        }
        OrderEvent::OrderDelivered { .. } => {
            state.map(|mut s| {
                s.status  = OrderStatus::Delivered;
                s.version += 1;
                s
            })
        }
        OrderEvent::OrderCancelled { .. } => {
            state.map(|mut s| {
                s.status  = OrderStatus::Cancelled;
                s.version += 1;
                s
            })
        }
    }
}

/// Reconstruct current state by folding events
pub fn reconstitute(events: &[OrderEvent]) -> Option<OrderState> {
    events.iter().fold(None, |state, event| apply_event(state, event))
}

/// Command handler: validate command against current state, produce events
pub fn handle_confirm_order(state: &OrderState) -> Result<Vec<OrderEvent>, OrderError> {
    if state.status != OrderStatus::PaymentPending {
        return Err(OrderError::InvalidTransition {
            from: format!("{:?}", state.status),
            to:   "Confirmed".to_string(),
        });
    }

    Ok(vec![OrderEvent::OrderConfirmed {
        occurred_at: Utc::now(),
    }])
}

#[derive(Debug)]
pub enum OrderError {
    InvalidTransition { from: String, to: String },
    NotFound,
    ConcurrencyConflict { expected: u64, actual: u64 },
}

impl fmt::Display for OrderError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidTransition { from, to } =>
                write!(f, "cannot transition from {} to {}", from, to),
            Self::NotFound =>
                write!(f, "aggregate not found"),
            Self::ConcurrencyConflict { expected, actual } =>
                write!(f, "concurrency conflict: expected version {}, got {}", expected, actual),
        }
    }
}
```

---

## Appendix A: Kernel Tuning for Microservices

```bash
#!/bin/bash
# kernel_tuning.sh — Production kernel tuning for microservice hosts
# Apply via: sysctl -p or /etc/sysctl.d/90-microservices.conf

# NETWORK: increase connection handling capacity

# Maximum socket receive/send buffers
net.core.rmem_max = 134217728          # 128MB
net.core.wmem_max = 134217728
net.core.rmem_default = 16777216       # 16MB
net.core.wmem_default = 16777216

# TCP-specific buffer sizing (min, default, max)
net.ipv4.tcp_rmem = 4096 87380 134217728
net.ipv4.tcp_wmem = 4096 65536 134217728

# Increase connection queue depths
net.core.somaxconn = 65535             # max listen() backlog
net.ipv4.tcp_max_syn_backlog = 65535   # SYN queue

# TIME_WAIT: microservices create many short-lived connections
net.ipv4.tcp_tw_reuse = 1             # reuse TIME_WAIT sockets (safe)
net.ipv4.tcp_fin_timeout = 15         # reduce FIN_WAIT2 timeout

# TCP keepalive: detect dead connections faster
net.ipv4.tcp_keepalive_time = 30      # first probe after 30s
net.ipv4.tcp_keepalive_intvl = 10     # probe interval
net.ipv4.tcp_keepalive_probes = 3     # max probes before giving up

# Increase local port range (important for services making many outbound conns)
net.ipv4.ip_local_port_range = 1024 65535

# Congestion control: BBR for datacenter
net.ipv4.tcp_congestion_control = bbr
net.core.default_qdisc = fq           # required for BBR

# MEMORY: tune for many small processes

# Virtual memory
vm.swappiness = 1                      # minimize swap for latency
vm.dirty_ratio = 10                    # % RAM before synchronous writeback
vm.dirty_background_ratio = 5         # % RAM before background writeback
vm.overcommit_memory = 1              # allow overcommit (for Go runtime)

# Huge pages for high-throughput services
# vm.nr_hugepages = 1024              # 2MB huge pages

# FILE DESCRIPTORS: each connection = 1 fd
fs.file-max = 2097152                  # system-wide limit
fs.nr_open = 1048576                   # per-process limit
# Also set in /etc/security/limits.d/90-microservices.conf:
#   * soft nofile 1048576
#   * hard nofile 1048576

# NUMA (if multi-socket): prevent cross-NUMA memory access
# kernel.numa_balancing = 1           # auto-balancing (or pin explicitly)
```

## Appendix B: eBPF-based Network Policy (Cilium)

```
CILIUM IDENTITY-BASED NETWORK POLICY
======================================

Traditional: IP-based firewall rules
  Allow: 10.0.1.2 → 10.0.2.3:5432
  Problem: Pod IPs change on reschedule

Cilium: Identity-based (Kubernetes labels)
  Allow: app=ordersvc → app=postgres
  Implementation: eBPF maps keyed by security identity (uint32)

  When pod starts:
    1. Cilium agent assigns identity: hash(labels)
    2. Identity propagates via KVStore (etcd) to all nodes
    3. eBPF map updated: identity → allowed identities

  On packet arrival:
    eBPF ingress hook:
      src_identity = extract_from_packet_metadata(skb)
      if !policy_map.lookup(dst_identity, src_identity):
          drop packet
      else:
          pass

CiliumNetworkPolicy:
  apiVersion: cilium.io/v2
  kind: CiliumNetworkPolicy
  metadata:
    name: ordersvc-policy
    namespace: orders
  spec:
    endpointSelector:
      matchLabels:
        app: ordersvc

    # Ingress: only allow from API gateway and other specific services
    ingress:
      - fromEndpoints:
          - matchLabels:
              app: api-gateway
        toPorts:
          - ports:
              - port: "8080"
                protocol: TCP
            rules:
              http:
                - method: "POST"
                  path: "/v1/orders"
                - method: "GET"
                  path: "/v1/orders/.*"

    # Egress: only allow to specific services + DNS
    egress:
      - toEndpoints:
          - matchLabels:
              app: usersvc
        toPorts:
          - ports: [{ port: "8080", protocol: TCP }]
      - toEndpoints:
          - matchLabels:
              app: postgres
              svc: ordersvc-db
        toPorts:
          - ports: [{ port: "5432", protocol: TCP }]
      - toEndpoints:
          - matchLabels:
              k8s:io.kubernetes.pod.namespace: kube-system
              k8s-app: kube-dns
        toPorts:
          - ports: [{ port: "53", protocol: UDP }]
```

## Appendix C: Service Template Makefile

```makefile
# Makefile — microservice development workflow
SERVICE_NAME := ordersvc
REGISTRY     := registry.example.com
VERSION      := $(shell git describe --tags --always --dirty)
COMMIT       := $(shell git rev-parse --short HEAD)
BUILD_TIME   := $(shell date -u +%Y-%m-%dT%H:%M:%SZ)

LDFLAGS := -ldflags "-X main.Version=$(VERSION) \
                     -X main.Commit=$(COMMIT) \
                     -X main.BuildTime=$(BUILD_TIME) \
                     -w -s"

.PHONY: all build test lint proto docker security clean

all: lint test build

# Build binary (Linux/AMD64 for container)
build:
	CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
	    go build $(LDFLAGS) -o bin/$(SERVICE_NAME) ./cmd/$(SERVICE_NAME)

# Run all tests
test:
	go test -race -cover -coverprofile=coverage.out ./...

# Integration tests (requires Docker)
test-integration:
	go test -tags integration -race -v -timeout 120s ./integration/...

# Benchmarks
bench:
	go test -bench=. -benchmem -benchtime=10s ./...

# Lint
lint:
	golangci-lint run --enable-all ./...
	staticcheck ./...

# Generate protobuf
proto:
	buf generate
	buf lint

# Security scanning
security:
	gosec -severity medium -confidence medium ./...
	trivy fs --security-checks vuln,config .
	go list -json -m all | nancy sleuth

# Build OCI image
docker:
	docker buildx build \
	    --platform linux/amd64,linux/arm64 \
	    --build-arg VERSION=$(VERSION) \
	    --build-arg COMMIT=$(COMMIT) \
	    --build-arg BUILD_TIME=$(BUILD_TIME) \
	    --label "org.opencontainers.image.version=$(VERSION)" \
	    --label "org.opencontainers.image.revision=$(COMMIT)" \
	    --label "org.opencontainers.image.created=$(BUILD_TIME)" \
	    -t $(REGISTRY)/$(SERVICE_NAME):$(VERSION) \
	    -t $(REGISTRY)/$(SERVICE_NAME):latest \
	    --push \
	    .

# Sign image with cosign
sign:
	cosign sign --key gcpkms://projects/myproject/locations/global/keyRings/cosign/cryptoKeys/signing \
	    $(REGISTRY)/$(SERVICE_NAME):$(VERSION)

# Local development
dev:
	docker compose up -d postgres kafka redis jaeger prometheus grafana
	go run ./cmd/$(SERVICE_NAME)

# Database migrations
migrate-up:
	migrate -path migrations -database "$(DATABASE_URL)" up

migrate-down:
	migrate -path migrations -database "$(DATABASE_URL)" down 1

# eBPF compilation (for custom BPF programs)
bpf:
	clang -O2 -g -target bpf \
	    -D__TARGET_ARCH_x86 \
	    -I/usr/include/x86_64-linux-gnu \
	    -c pkg/ebpf/svc_latency.bpf.c \
	    -o pkg/ebpf/svc_latency.bpf.o
	go generate ./pkg/ebpf/...

clean:
	rm -rf bin/ coverage.out

# Help
help:
	@echo "Targets:"
	@echo "  build            Build binary"
	@echo "  test             Run unit tests"
	@echo "  test-integration Run integration tests (requires Docker)"
	@echo "  lint             Run linters"
	@echo "  proto            Generate protobuf code"
	@echo "  security         Run security scanners"
	@echo "  docker           Build and push OCI image"
	@echo "  sign             Sign image with cosign"
	@echo "  dev              Start local dev environment"
	@echo "  migrate-up/down  Run DB migrations"
	@echo "  bpf              Compile eBPF programs"
```

---

*Document version: 1.0 | Kernel reference: v6.8 | Last updated: 2024*

*Key references:*
- *Building Microservices, 2nd Ed — Sam Newman (O'Reilly)*
- *Designing Distributed Systems — Brendan Burns*
- *Production Kubernetes — Josh Rosso et al.*
- *Linux Kernel Development, 3rd Ed — Robert Love*
- *BPF Performance Tools — Brendan Gregg*
- *kernel.org/doc/html/latest/*
- *LWN.net*

