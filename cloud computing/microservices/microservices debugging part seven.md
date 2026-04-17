# The Definitive Guide to Debugging Microservices
## Distributed Systems · C · Go · Rust · Linux Kernel · Cloud Security · Cloud Native

> **Scope**: This guide is written for engineers who already understand software fundamentals and need a precise, deep, production-grade reference for every layer of distributed system debugging — from the Linux kernel network stack to multi-cloud service meshes. No hand-holding. No beginner detours.

---

## Table of Contents

1. [Why Distributed Debugging Is a Different Discipline](#1-why-distributed-debugging-is-a-different-discipline)
2. [The Anatomy of a Distributed Failure](#2-the-anatomy-of-a-distributed-failure)
3. [Observability: The Three Pillars and Beyond](#3-observability-the-three-pillars-and-beyond)
4. [Distributed Tracing: Theory and Implementation](#4-distributed-tracing-theory-and-implementation)
5. [Metrics: Collection, Cardinality, and Alerting](#5-metrics-collection-cardinality-and-alerting)
6. [Structured Logging at Scale](#6-structured-logging-at-scale)
7. [Implementing Correlation IDs and Context Propagation](#7-implementing-correlation-ids-and-context-propagation)
8. [Go: Debugging Microservices in Production](#8-go-debugging-microservices-in-production)
9. [Rust: Debugging Microservices in Production](#9-rust-debugging-microservices-in-production)
10. [C: Systems-Level Debugging for Microservice Infrastructure](#10-c-systems-level-debugging-for-microservice-infrastructure)
11. [Linux Kernel Internals and Microservice Debugging](#11-linux-kernel-internals-and-microservice-debugging)
12. [eBPF: Kernel-Level Observability Without Patching](#12-ebpf-kernel-level-observability-without-patching)
13. [Network Stack Debugging: TCP, UDP, and Beyond](#13-network-stack-debugging-tcp-udp-and-beyond)
14. [Partial Failures, Retries, and Cascading Failures](#14-partial-failures-retries-and-cascading-failures)
15. [Data Consistency Debugging Across Service Boundaries](#15-data-consistency-debugging-across-service-boundaries)
16. [Concurrency, Race Conditions, and Distributed Deadlocks](#16-concurrency-race-conditions-and-distributed-deadlocks)
17. [API Versioning, Schema Drift, and Contract Testing](#17-api-versioning-schema-drift-and-contract-testing)
18. [Asynchronous Communication: Queues, Events, and Message Brokers](#18-asynchronous-communication-queues-events-and-message-brokers)
19. [Cloud Native Debugging: Kubernetes Deep Dive](#19-cloud-native-debugging-kubernetes-deep-dive)
20. [Service Mesh Debugging: Istio, Linkerd, Cilium](#20-service-mesh-debugging-istio-linkerd-cilium)
21. [Cloud Security: Debugging Auth, mTLS, and Policy Failures](#21-cloud-security-debugging-auth-mtls-and-policy-failures)
22. [Multi-Cloud and Hybrid Debugging Challenges](#22-multi-cloud-and-hybrid-debugging-challenges)
23. [Chaos Engineering: Proactive Debugging Before Production](#23-chaos-engineering-proactive-debugging-before-production)
24. [Production Debugging Workflows](#24-production-debugging-workflows)
25. [Clock Drift, Time-Ordering, and Causality](#25-clock-drift-time-ordering-and-causality)
26. [Reproducing Production Failures Locally](#26-reproducing-production-failures-locally)
27. [Post-Mortem Culture and Failure Documentation](#27-post-mortem-culture-and-failure-documentation)
28. [Tooling Reference](#28-tooling-reference)

---

## 1. Why Distributed Debugging Is a Different Discipline

### The Fundamental Shift

When you debug a monolith, you're reasoning about a **single process** with a **single memory space**, a **single call stack**, and **deterministic execution order**. The OS scheduler is your only adversary.

When you debug microservices, you're reasoning about a **distributed system** — a set of processes communicating over an unreliable network, each with independent state, independent failure modes, and independent clocks. The rules change completely.

The eight fallacies of distributed computing (Peter Deutsch, Sun Microsystems, 1994) remain as relevant today as when they were written. Every one of them produces a category of bugs you will encounter:

| Fallacy | Reality | Bug Category |
|--------|---------|-------------|
| The network is reliable | Packets drop, links flap, connections timeout | Intermittent failures, phantom timeouts |
| Latency is zero | P99 latency can be 100x P50 | Cascading slowdowns, thread pool exhaustion |
| Bandwidth is infinite | Saturation causes head-of-line blocking | Throughput collapse under load |
| The network is secure | MITM, replay, injection | Security-class failures |
| Topology doesn't change | Pod restarts, node evictions, rolling deploys | Connection reset storms |
| There is one administrator | Multiple teams, multiple orgs | Config drift, firewall mismatches |
| Transport cost is zero | Serialization, compression, encoding overhead | Unexplained latency |
| The network is homogeneous | Mixed protocols, MTU differences, NIC firmware bugs | Silent data corruption |

### Why Traditional Debugging Tools Fail

A debugger (gdb, dlv, lldb) attaches to a single process. Stepping through code line-by-line works when execution is local and synchronous. In a distributed system:

- The "bug" may be a sequence of events across **five services** separated by **network hops** and **time**
- By the time you observe the symptom, the cause may have disappeared from memory
- Pausing a single service with a breakpoint may cause **timeouts in upstream callers**, cascading the failure differently
- Production load is irreproducible in a debugger session

The mental model shift: **you are no longer debugging code, you are reconstructing the history of a distributed system**. The primary tools are not debuggers — they are **traces, metrics, logs, and probes**.

---

## 2. The Anatomy of a Distributed Failure

### Failure Taxonomy

Understanding failure types lets you apply the right investigative technique:

#### 2.1 Crash Failures
A service terminates unexpectedly. The easiest class of failure. Symptoms: connection refused, pod in CrashLoopBackOff, process exit code non-zero. Root cause: panic/exception, OOM kill, segfault.

#### 2.2 Omission Failures
A service stops responding to some (or all) requests without crashing. The hardest to detect quickly. Symptoms: increasing latency, timeout counters rising, but the service appears "up" in health checks. Root cause: goroutine leak, thread pool exhaustion, deadlock on a lock that health check doesn't touch.

#### 2.3 Timing Failures
A service responds, but too slowly. Symptoms: P99 latency SLO breaches, upstream timeouts. Root cause: GC pressure, slow query, lock contention, CPU throttling in cgroups (a Kubernetes-specific trap).

#### 2.4 Byzantine Failures
A service responds with **incorrect data** without crashing. The most dangerous class. Symptoms: data corruption downstream, silent bad state, assertion failures elsewhere. Root cause: memory corruption, race condition, integer overflow, incorrect deserialization, clock skew in time-ordered logic.

#### 2.5 Cascade Failures
A localized failure amplifies across the system. Service A slows → B's connection pool fills → B's health check starts failing → load balancer removes B → remaining B instances get hammered → they slow → C's connection pool fills → repeat.

```
Initial trigger: DB latency spike (50ms → 500ms)
t+0s:  DB query timeout at 95th percentile in Service C
t+2s:  Service C thread pool at 80% utilization
t+5s:  Service B's calls to C start timing out
t+8s:  Service B's circuit breaker opens → returns fallback (stale data)
t+10s: Service A's calls to B succeed but receive wrong data
t+12s: Downstream fraud detection triggers on wrong data
t+30s: Customer-visible impact: orders failing validation
```

Note: the observable failure (fraud detection, order failures) is **30 seconds and 4 hops removed** from the actual cause (DB latency). This is the core challenge.

#### 2.6 Gray Failures
Partial availability — a service works for some requests, fails for others, based on which instance handles the request, which shard of the database is queried, or which code path is taken. Extremely hard to detect because aggregate metrics look healthy.

### The Failure Space Model

To systematically debug, model failure across three dimensions:

```
Dimension 1: WHERE     → Which service/component/resource?
Dimension 2: WHAT      → Crash / Omission / Timing / Byzantine / Cascade?
Dimension 3: WHEN      → Permanent / Transient / Intermittent / Load-correlated?
```

Intersecting these gives you a 3D search space. Good observability lets you reduce the space quickly. Poor observability means random walk.

---

## 3. Observability: The Three Pillars and Beyond

Observability is the property of a system that allows you to understand its internal state from external outputs. It is distinct from monitoring (checking if the system is up) and debugging (interactive investigation).

### The Three Pillars

**Logs**: Timestamped, structured records of discrete events. High information density per record, high storage cost. Best for: "what exactly happened at this moment?"

**Metrics**: Numeric measurements aggregated over time. Low storage cost, lossy (aggregation discards detail). Best for: "what is the system's current rate/count/gauge, and how has it trended?"

**Traces**: Causal chains linking spans of work across service boundaries. Moderate storage cost, requires instrumentation. Best for: "which service, in which function, for which request, is slow or failing?"

### The Missing Pillars

These are increasingly recognized as essential:

**Profiles (Continuous Profiling)**: CPU flame graphs, heap allocations, goroutine stacks collected continuously in production. Tools: Pyroscope, Parca, Google Cloud Profiler. Best for: "why is this service consuming 80% CPU under normal load?"

**Events**: High-cardinality, structured events (distinct from logs — think Honeycomb's model). Every request generates a single richly-attributed event. Best for: debugging rare conditions correlated with arbitrary combinations of attributes.

**Exceptions**: Structured error tracking with stack traces, breadcrumbs, and context. Tools: Sentry, Rollbar, Bugsnag. Best for: finding unknown unknowns — exceptions you didn't know to alert on.

### Observability vs. Monitoring: The Cardinality Argument

Traditional monitoring is based on **known failure modes**: you write alerts for things you anticipate. Observability is about debugging **unknown failure modes**: questions you didn't know to ask in advance.

The critical technical differentiator is **cardinality**. Traditional time-series databases (Prometheus, Graphite) handle low-cardinality dimensions well (e.g., service name, HTTP method — 50 combinations). They break at high-cardinality dimensions (user ID, request ID, session ID — millions of combinations).

High-cardinality observability requires columnar storage engines designed for it: Honeycomb, Tempo + Loki, ClickHouse-backed systems, or OpenTelemetry-compatible backends.

---

## 4. Distributed Tracing: Theory and Implementation

### Concepts

**Trace**: A complete record of the processing of a single request as it propagates through a distributed system.

**Span**: A single unit of work within a trace. Has a start time, duration, service name, operation name, status, and attributes. Spans form a tree (or DAG for async work).

**Trace Context**: Metadata propagated in-band with the request (HTTP headers, message metadata) that allows spans in different services to be correlated into a single trace. The W3C Trace Context specification standardizes: `traceparent` and `tracestate` headers.

**Sampling**: Because tracing every request is expensive, you sample. Head-based sampling (decide at trace entry) is simple but loses rare failures. Tail-based sampling (buffer spans, decide at trace completion based on outcome) is complex but captures all errors. Tools: OpenTelemetry Collector's tail sampling processor.

### W3C Trace Context Header Format

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              ^^ version
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ trace-id (128-bit)
                                                  ^^^^^^^^^^^^^^^^ parent-span-id (64-bit)
                                                                   ^^ flags (sampled=01)
```

### OpenTelemetry: The Unified Standard

OpenTelemetry (OTel) is the CNCF standard for instrumentation. It provides:
- **API**: Language-specific interfaces for creating spans, metrics, and log records
- **SDK**: Implementation of the API with exporters and processors
- **OTLP**: OpenTelemetry Protocol — a gRPC/HTTP protocol for exporting telemetry
- **Collector**: A vendor-agnostic proxy/aggregator that receives, processes, and exports telemetry

The Collector pipeline:

```
Application (OTLP) → Receiver → Processor(s) → Exporter → Backend
                                  ↑
                            (sampling, filtering,
                             attribute enrichment,
                             batching, transformation)
```

### Implementing Tracing in Go

```go
// main.go — bootstrapping OTel tracing in a Go service
package main

import (
    "context"
    "fmt"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
    "go.opentelemetry.io/otel/trace"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
)

// initTracer initializes the OTel tracing pipeline.
// Returns a shutdown function that must be called to flush spans.
func initTracer(ctx context.Context, serviceName, serviceVersion, collectorAddr string) (func(context.Context) error, error) {
    // gRPC connection to OTel Collector
    conn, err := grpc.DialContext(ctx, collectorAddr,
        grpc.WithTransportCredentials(insecure.NewCredentials()),
        grpc.WithBlock(),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to connect to collector: %w", err)
    }

    // OTLP gRPC exporter
    exporter, err := otlptracegrpc.New(ctx, otlptracegrpc.WithGRPCConn(conn))
    if err != nil {
        return nil, fmt.Errorf("failed to create exporter: %w", err)
    }

    // Resource describes this service instance
    res, err := resource.Merge(
        resource.Default(),
        resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName(serviceName),
            semconv.ServiceVersion(serviceVersion),
            attribute.String("deployment.environment", "production"),
        ),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // TracerProvider with batch span processor
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter),
        sdktrace.WithResource(res),
        // Tail-based sampling handled at Collector level.
        // Head-based: sdktrace.WithSampler(sdktrace.TraceIDRatioBased(0.1))
        sdktrace.WithSampler(sdktrace.AlwaysSample()),
    )

    // Set global propagator: W3C TraceContext + Baggage
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))
    otel.SetTracerProvider(tp)

    return tp.Shutdown, nil
}

// instrumentedHTTPClient wraps http.Client to propagate trace context
func instrumentedHTTPClient() *http.Client {
    // Use go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp
    // which automatically injects W3C trace headers into outgoing requests
    return &http.Client{
        Transport: otelhttp.NewTransport(http.DefaultTransport),
    }
}
```

```go
// handler.go — manual span creation and attribute annotation
package handlers

import (
    "context"
    "fmt"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/codes"
)

var tracer = otel.Tracer("order-service")

type OrderService struct {
    db         Database
    paymentSvc PaymentClient
    inventorySvc InventoryClient
}

func (s *OrderService) CreateOrder(ctx context.Context, req CreateOrderRequest) (*Order, error) {
    // Start a span. This is a child of whatever span is in ctx (from HTTP middleware).
    ctx, span := tracer.Start(ctx, "CreateOrder")
    defer span.End()

    // Annotate with business-level attributes — critical for debugging gray failures.
    // These become searchable dimensions in your trace backend.
    span.SetAttributes(
        attribute.String("order.customer_id", req.CustomerID),
        attribute.String("order.product_id", req.ProductID),
        attribute.Int("order.quantity", req.Quantity),
        attribute.String("order.region", req.Region),
    )

    // Check inventory — creates a child span
    available, err := s.inventorySvc.CheckAvailability(ctx, req.ProductID, req.Quantity)
    if err != nil {
        // Record the error on the span. This allows trace backends to
        // filter on error=true and show the exception details.
        span.RecordError(err)
        span.SetStatus(codes.Error, fmt.Sprintf("inventory check failed: %v", err))
        return nil, fmt.Errorf("inventory check: %w", err)
    }

    if !available {
        span.SetAttributes(attribute.Bool("order.inventory_available", false))
        span.SetStatus(codes.Error, "insufficient inventory")
        return nil, ErrInsufficientInventory
    }

    // Process payment — creates a child span
    paymentRef, err := s.paymentSvc.Charge(ctx, req.CustomerID, req.Amount)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "payment failed")
        return nil, fmt.Errorf("payment: %w", err)
    }

    span.SetAttributes(attribute.String("order.payment_ref", paymentRef))

    // Persist order — creates a child span
    order, err := s.db.InsertOrder(ctx, req, paymentRef)
    if err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "db insert failed")
        // Critical: payment succeeded but order save failed.
        // This span now contains enough context to trigger a saga compensation.
        span.SetAttributes(attribute.String("saga.payment_ref", paymentRef))
        return nil, fmt.Errorf("order persistence: %w", err)
    }

    span.SetAttributes(
        attribute.String("order.id", order.ID),
        attribute.Bool("order.inventory_available", true),
    )
    span.SetStatus(codes.Ok, "")

    return order, nil
}
```

### Implementing Tracing in Rust

```rust
// Cargo.toml dependencies:
// opentelemetry = { version = "0.21", features = ["rt-tokio"] }
// opentelemetry-otlp = { version = "0.14", features = ["grpc-tonic"] }
// opentelemetry_sdk = { version = "0.21", features = ["rt-tokio"] }
// tracing = "0.1"
// tracing-opentelemetry = "0.22"
// tracing-subscriber = { version = "0.3", features = ["env-filter"] }

use opentelemetry::global;
use opentelemetry::trace::TraceError;
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::{
    runtime,
    trace::{self, RandomIdGenerator, Sampler},
    Resource,
};
use opentelemetry::KeyValue;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

/// Initialize the OTel pipeline.
/// The tracing crate integrates with OTel via tracing-opentelemetry,
/// meaning tracing::instrument spans become OTel spans automatically.
pub fn init_tracer(service_name: &str) -> Result<(), TraceError> {
    let tracer = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(
            opentelemetry_otlp::new_exporter()
                .tonic()
                .with_endpoint("http://otel-collector:4317"),
        )
        .with_trace_config(
            trace::config()
                .with_sampler(Sampler::AlwaysOn)
                .with_id_generator(RandomIdGenerator::default())
                .with_resource(Resource::new(vec![
                    KeyValue::new("service.name", service_name.to_string()),
                    KeyValue::new("service.version", env!("CARGO_PKG_VERSION")),
                ])),
        )
        .install_batch(runtime::Tokio)?;

    let telemetry_layer = tracing_opentelemetry::layer().with_tracer(tracer);

    tracing_subscriber::registry()
        .with(tracing_subscriber::EnvFilter::from_default_env())
        .with(tracing_subscriber::fmt::layer().json()) // structured logs
        .with(telemetry_layer)                          // OTel spans
        .init();

    Ok(())
}

/// Service handler with automatic span instrumentation.
/// The #[tracing::instrument] macro creates a span for the function call,
/// capturing all arguments as span attributes.
#[tracing::instrument(
    name = "process_payment",
    skip(payment_client, card_details), // skip sensitive fields from span attributes
    fields(
        customer.id = %customer_id,
        payment.amount = amount,
        payment.currency = %currency,
    )
)]
pub async fn process_payment(
    customer_id: &str,
    amount: f64,
    currency: &str,
    card_details: &CardDetails,
    payment_client: &PaymentClient,
) -> Result<PaymentResult, PaymentError> {
    // Add dynamic attributes to the current span
    let current_span = tracing::Span::current();

    let result = payment_client
        .charge(customer_id, amount, currency, card_details)
        .await;

    match &result {
        Ok(payment) => {
            current_span.record("payment.transaction_id", &payment.transaction_id.as_str());
            current_span.record("payment.status", "succeeded");
            tracing::info!(
                transaction_id = %payment.transaction_id,
                "Payment processed successfully"
            );
        }
        Err(e) => {
            current_span.record("payment.status", "failed");
            current_span.record("error.code", &e.code().as_str());
            // tracing::error automatically marks the span as error in OTel
            tracing::error!(
                error.code = %e.code(),
                error.message = %e,
                "Payment processing failed"
            );
        }
    }

    result
}
```

### Implementing Tracing in C

C lacks the rich ecosystem of Go and Rust. The primary approach is the OpenTelemetry C++ SDK or direct OTLP integration via HTTP/gRPC with a library like libcurl/grpc-c.

```c
/*
 * Minimal W3C traceparent propagation in C.
 * Used in C-based microservice infrastructure (e.g., nginx modules,
 * Envoy extensions via C ABI, legacy C services in a service mesh).
 *
 * For production: use opentelemetry-cpp SDK or instrument at the
 * sidecar (Envoy) level to avoid C instrumentation complexity.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>

/* 128-bit trace ID stored as two uint64_t values */
typedef struct {
    uint64_t hi;
    uint64_t lo;
} trace_id_t;

/* 64-bit span ID */
typedef uint64_t span_id_t;

typedef struct {
    trace_id_t  trace_id;
    span_id_t   span_id;
    span_id_t   parent_span_id; /* 0 if root span */
    uint8_t     flags;          /* 0x01 = sampled */
    char        operation_name[128];
    struct timespec start_time;
    struct timespec end_time;
    int         status_code;    /* 0=unset, 1=ok, 2=error */
    char        status_message[256];
} otel_span_t;

/*
 * Generate a cryptographically weak random ID.
 * In production: use /dev/urandom or getrandom(2) syscall.
 */
static uint64_t generate_id(void) {
    /* getrandom is the correct approach on Linux 3.17+ */
    uint64_t id;
    FILE *f = fopen("/dev/urandom", "rb");
    if (f) {
        fread(&id, sizeof(id), 1, f);
        fclose(f);
    } else {
        /* Fallback: bad entropy, not for production */
        id = (uint64_t)rand() << 32 | rand();
    }
    return id;
}

/* Start a new span, optionally as a child of an existing span */
otel_span_t *otel_span_start(
    const char *operation_name,
    const otel_span_t *parent  /* NULL for root span */
) {
    otel_span_t *span = calloc(1, sizeof(otel_span_t));
    if (!span) return NULL;

    if (parent) {
        /* Inherit trace_id from parent */
        span->trace_id = parent->trace_id;
        span->parent_span_id = parent->span_id;
        span->flags = parent->flags;
    } else {
        /* New trace: generate fresh trace_id */
        span->trace_id.hi = generate_id();
        span->trace_id.lo = generate_id();
        span->parent_span_id = 0;
        span->flags = 0x01; /* sampled */
    }

    span->span_id = generate_id();
    strncpy(span->operation_name, operation_name,
            sizeof(span->operation_name) - 1);
    clock_gettime(CLOCK_REALTIME, &span->start_time);

    return span;
}

/*
 * Format the W3C traceparent header value.
 * Buffer must be at least 56 bytes.
 * Format: 00-{trace-id-32hex}-{span-id-16hex}-{flags-2hex}
 */
int otel_format_traceparent(const otel_span_t *span, char *buf, size_t bufsz) {
    return snprintf(buf, bufsz,
        "00-%016llx%016llx-%016llx-%02x",
        (unsigned long long)span->trace_id.hi,
        (unsigned long long)span->trace_id.lo,
        (unsigned long long)span->span_id,
        span->flags
    );
}

/*
 * Parse an incoming traceparent header into a span context.
 * Use this to continue a trace from an upstream service.
 */
int otel_parse_traceparent(const char *header, otel_span_t *out_parent_ctx) {
    if (!header || !out_parent_ctx) return -1;

    unsigned long long tid_hi, tid_lo, sid;
    unsigned int flags;

    int parsed = sscanf(header,
        "00-%16llx%16llx-%16llx-%02x",
        &tid_hi, &tid_lo, &sid, &flags
    );

    if (parsed != 4) return -1;

    out_parent_ctx->trace_id.hi = (uint64_t)tid_hi;
    out_parent_ctx->trace_id.lo = (uint64_t)tid_lo;
    out_parent_ctx->span_id     = (uint64_t)sid;
    out_parent_ctx->flags       = (uint8_t)flags;

    return 0;
}

/* End span and emit to collector via OTLP/HTTP (simplified) */
void otel_span_end(otel_span_t *span, int status_code, const char *message) {
    if (!span) return;

    clock_gettime(CLOCK_REALTIME, &span->end_time);
    span->status_code = status_code;
    if (message) {
        strncpy(span->status_message, message,
                sizeof(span->status_message) - 1);
    }

    /* Calculate duration in microseconds */
    long duration_us = (span->end_time.tv_sec - span->start_time.tv_sec) * 1000000L
                     + (span->end_time.tv_nsec - span->start_time.tv_nsec) / 1000L;

    /*
     * In a real implementation, you would:
     * 1. Serialize to OTLP protobuf format
     * 2. POST to http://otel-collector:4318/v1/traces
     * Using libcurl or a dedicated OTLP sender.
     *
     * For high-throughput C services: batch spans in a ring buffer
     * and flush asynchronously from a dedicated sender thread.
     */
    fprintf(stderr,
        "[SPAN] trace=%016llx%016llx span=%016llx parent=%016llx "
        "op=\"%s\" duration_us=%ld status=%d\n",
        (unsigned long long)span->trace_id.hi,
        (unsigned long long)span->trace_id.lo,
        (unsigned long long)span->span_id,
        (unsigned long long)span->parent_span_id,
        span->operation_name,
        duration_us,
        span->status_code
    );

    free(span);
}
```

---

## 5. Metrics: Collection, Cardinality, and Alerting

### Metrics Types

**Counter**: Monotonically increasing value. Reset on restart. Used for: requests_total, errors_total, bytes_sent_total. Always expose as rate over time window: `rate(requests_total[5m])`.

**Gauge**: Point-in-time value that goes up and down. Used for: active_connections, queue_depth, memory_bytes, goroutines.

**Histogram**: Distribution of values with configurable bucket boundaries. Used for: request_latency_seconds, payload_size_bytes. Enables percentile calculation: `histogram_quantile(0.99, rate(latency_bucket[5m]))`.

**Summary**: Pre-computed quantiles on the client. Cheaper for the query backend, but quantiles cannot be aggregated across instances (fundamental limitation — never use summaries for services with multiple replicas).

### The USE Method (Brendan Gregg)

For every resource in the system, measure:
- **Utilization**: % of time the resource is busy
- **Saturation**: Amount of work queued waiting for the resource
- **Errors**: Error rate on operations against the resource

Apply to: CPUs, memory, network interfaces, disk I/O, file descriptors, thread pools, connection pools, database connections.

### The RED Method (Tom Wilkie)

For every service endpoint, measure:
- **Rate**: Requests per second
- **Errors**: Failed requests per second
- **Duration**: Distribution of request latencies

RED is what you expose per-service. USE is what you measure per-resource.

### Golden Signals (Google SRE Book)

- **Latency**: Time to serve a request (separate success vs. error latency)
- **Traffic**: Request rate
- **Errors**: Error rate (distinguish 5xx from 4xx — 4xx is often caller's fault)
- **Saturation**: How full the service is (queue depth, thread pool utilization)

### Prometheus Metrics in Go

```go
// metrics.go — production-grade metrics with exemplars for trace correlation
package metrics

import (
    "net/http"
    "strconv"
    "time"

    "github.com/prometheus/client_golang/prometheus"
    "github.com/prometheus/client_golang/prometheus/promauto"
    "go.opentelemetry.io/otel/trace"
)

// Metrics registry for the order service
var (
    // Histogram with good bucket selection for a web service.
    // Buckets should cover the expected distribution of your latencies.
    // Rule of thumb: start at your SLO target, work outward.
    HTTPRequestDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name: "http_request_duration_seconds",
            Help: "HTTP request duration in seconds.",
            // Cover: <5ms (fast), 5-50ms (normal), 50-500ms (slow), 500ms+ (very slow)
            Buckets: []float64{0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10},
            // Exemplars allow linking a high-latency histogram observation to a trace ID.
            // Requires Prometheus >= 2.26 and native histograms or OpenMetrics format.
            NativeHistogramBucketFactor: 1.1,
        },
        []string{"method", "path", "status_code", "service"},
    )

    // Counter — ALWAYS use With() to avoid cardinality explosion.
    // Never add user IDs, request IDs as label values.
    HTTPRequestsTotal = promauto.NewCounterVec(
        prometheus.CounterOpts{
            Name: "http_requests_total",
            Help: "Total number of HTTP requests.",
        },
        []string{"method", "path", "status_code"},
    )

    // Gauge for active requests (in-flight)
    HTTPActiveRequests = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "http_active_requests",
            Help: "Number of in-flight HTTP requests.",
        },
        []string{"method", "path"},
    )

    // Circuit breaker state gauge
    CircuitBreakerState = promauto.NewGaugeVec(
        prometheus.GaugeOpts{
            Name: "circuit_breaker_state",
            Help: "Circuit breaker state: 0=closed, 1=half-open, 2=open",
        },
        []string{"upstream_service"},
    )

    // Downstream call duration — critical for identifying which upstream is slow
    UpstreamCallDuration = promauto.NewHistogramVec(
        prometheus.HistogramOpts{
            Name:    "upstream_call_duration_seconds",
            Help:    "Duration of outgoing calls to upstream services.",
            Buckets: prometheus.DefBuckets,
        },
        []string{"upstream", "method", "status"},
    )
)

// ObservabilityMiddleware instruments HTTP handlers with metrics AND exemplars.
// Exemplars link a high-latency histogram observation to the trace ID that caused it.
func ObservabilityMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        start := time.Now()
        path := r.URL.Path // normalize this in production to avoid cardinality explosion

        HTTPActiveRequests.WithLabelValues(r.Method, path).Inc()
        defer HTTPActiveRequests.WithLabelValues(r.Method, path).Dec()

        rw := &responseWriter{ResponseWriter: w, statusCode: http.StatusOK}
        next.ServeHTTP(rw, r)

        duration := time.Since(start).Seconds()
        statusStr := strconv.Itoa(rw.statusCode)

        HTTPRequestsTotal.WithLabelValues(r.Method, path, statusStr).Inc()

        // Attach exemplar: links this latency observation to the active trace.
        // In Grafana, you can click a slow histogram bucket and jump directly
        // to the Jaeger trace that caused it.
        span := trace.SpanFromContext(r.Context())
        if span.SpanContext().IsValid() {
            HTTPRequestDuration.WithLabelValues(
                r.Method, path, statusStr, "order-service",
            ).(prometheus.ExemplarObserver).ObserveWithExemplar(
                duration,
                prometheus.Labels{
                    "traceID": span.SpanContext().TraceID().String(),
                    "spanID":  span.SpanContext().SpanID().String(),
                },
            )
        } else {
            HTTPRequestDuration.WithLabelValues(
                r.Method, path, statusStr, "order-service",
            ).Observe(duration)
        }
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
```

### Prometheus Metrics in Rust

```rust
use prometheus::{
    register_histogram_vec, register_counter_vec, register_gauge_vec,
    HistogramVec, CounterVec, GaugeVec, Encoder, TextEncoder,
};
use once_cell::sync::Lazy;

// Lazily initialized global metrics registry
static HTTP_REQUEST_DURATION: Lazy<HistogramVec> = Lazy::new(|| {
    register_histogram_vec!(
        "http_request_duration_seconds",
        "HTTP request duration in seconds",
        &["method", "endpoint", "status_code"],
        vec![0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
    )
    .expect("Failed to register HTTP duration histogram")
});

static UPSTREAM_ERRORS_TOTAL: Lazy<CounterVec> = Lazy::new(|| {
    register_counter_vec!(
        "upstream_errors_total",
        "Total errors from upstream service calls",
        &["upstream", "error_type"]
    )
    .expect("Failed to register upstream errors counter")
});

static DB_POOL_UTILIZATION: Lazy<GaugeVec> = Lazy::new(|| {
    register_gauge_vec!(
        "db_pool_utilization_ratio",
        "Fraction of DB pool connections in use (0.0 to 1.0)",
        &["pool_name"]
    )
    .expect("Failed to register DB pool gauge")
});

/// Tower middleware layer for automatic HTTP metrics collection.
/// Integrates with Axum, Actix-web, or any Tower-compatible framework.
pub async fn metrics_middleware<B>(
    req: axum::http::Request<B>,
    next: axum::middleware::Next<B>,
) -> axum::response::Response {
    let method = req.method().to_string();
    let path = req.uri().path().to_string();
    let start = std::time::Instant::now();

    let response = next.run(req).await;

    let duration = start.elapsed().as_secs_f64();
    let status = response.status().as_u16().to_string();

    HTTP_REQUEST_DURATION
        .with_label_values(&[&method, &path, &status])
        .observe(duration);

    response
}

/// Export metrics in Prometheus text format for scraping.
pub async fn metrics_handler() -> impl axum::response::IntoResponse {
    let encoder = TextEncoder::new();
    let metric_families = prometheus::gather();
    let mut buffer = Vec::new();
    encoder.encode(&metric_families, &mut buffer)
        .expect("Failed to encode metrics");

    (
        axum::http::StatusCode::OK,
        [(axum::http::header::CONTENT_TYPE, "text/plain; version=0.0.4")],
        buffer,
    )
}
```

---

## 6. Structured Logging at Scale

### Why Structured Logging

Free-form text logs are designed for human eyes reading a single terminal. At scale:
- **Searching**: You need `grep` or full-text search. Both are slow and imprecise.
- **Correlation**: Finding all log lines for a single request requires the request ID to appear literally in every line.
- **Alerting**: You cannot write a reliable alert on a regex over unstructured text.

Structured logging emits machine-parseable records (JSON, logfmt, CBOR) that can be indexed, queried, and aggregated efficiently.

### Log Levels and When to Use Them

| Level | Use Case | Production Default |
|-------|---------|-------------------|
| TRACE | Step-by-step execution path | Never — volume is too high |
| DEBUG | Values of variables, intermediate state | Disabled, but dynamically enableable |
| INFO  | Business events: order created, user authenticated | Yes |
| WARN  | Recoverable anomalies: retry succeeded, fallback used | Yes |
| ERROR | Request failed, error returned to caller | Yes |
| FATAL/PANIC | Unrecoverable: startup failure, data corruption | Yes (triggers alert) |

**Key rule**: ERROR should be defined as "a human needs to investigate this within X hours." If it triggers no action, it should be WARN or INFO. Alert fatigue from ERROR-level noise is a debugging anti-pattern.

### Structured Logging in Go (slog)

```go
// logger.go — production-grade structured logging with trace correlation
package logger

import (
    "context"
    "io"
    "log/slog"
    "os"

    "go.opentelemetry.io/otel/trace"
)

type traceContextHandler struct {
    inner slog.Handler
}

// Handle enriches every log record with the active trace and span ID.
// This is the critical link between logs and traces — without it,
// you cannot correlate a log line to a specific trace in Jaeger/Tempo.
func (h *traceContextHandler) Handle(ctx context.Context, r slog.Record) error {
    if span := trace.SpanFromContext(ctx); span.SpanContext().IsValid() {
        r.AddAttrs(
            slog.String("trace_id", span.SpanContext().TraceID().String()),
            slog.String("span_id", span.SpanContext().SpanID().String()),
            slog.Bool("trace_sampled", span.SpanContext().IsSampled()),
        )
    }
    return h.inner.Handle(ctx, r)
}

func (h *traceContextHandler) Enabled(ctx context.Context, level slog.Level) bool {
    return h.inner.Enabled(ctx, level)
}
func (h *traceContextHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
    return &traceContextHandler{inner: h.inner.WithAttrs(attrs)}
}
func (h *traceContextHandler) WithGroup(name string) slog.Handler {
    return &traceContextHandler{inner: h.inner.WithGroup(name)}
}

// NewLogger creates the production logger.
// Output: JSON to stdout (captured by the container runtime and forwarded to log aggregator).
func NewLogger(serviceName, serviceVersion string) *slog.Logger {
    opts := &slog.HandlerOptions{
        Level:     slog.LevelInfo,
        AddSource: false, // Enable in debug builds: adds file:line to every record
    }

    baseHandler := slog.NewJSONHandler(os.Stdout, opts)
    tracingHandler := &traceContextHandler{inner: baseHandler}

    return slog.New(tracingHandler).With(
        slog.String("service", serviceName),
        slog.String("version", serviceVersion),
    )
}

// Example log output (JSON):
// {
//   "time": "2024-11-15T14:23:01.123456Z",
//   "level": "ERROR",
//   "msg": "payment processing failed",
//   "service": "order-service",
//   "version": "1.4.2",
//   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
//   "span_id": "00f067aa0ba902b7",
//   "trace_sampled": true,
//   "customer_id": "cust_1234",
//   "payment_provider": "stripe",
//   "error_code": "card_declined",
//   "attempt": 2
// }
```

### Log Levels as Dynamic Runtime Configuration

Hard-coding log levels at startup means you cannot get DEBUG logs from a running production service without a restart (and a redeployment). The correct approach is a dynamic log level endpoint:

```go
// Enable debug logging for 5 minutes without restarting the service.
// Access-controlled endpoint — should require service-level auth.

var logLevelVar = new(slog.LevelVar) // Atomic, safe for concurrent use

func init() {
    logLevelVar.Set(slog.LevelInfo)
}

func LogLevelHandler(w http.ResponseWriter, r *http.Request) {
    if r.Method == http.MethodPut {
        var body struct{ Level string }
        json.NewDecoder(r.Body).Decode(&body)

        var level slog.Level
        if err := level.UnmarshalText([]byte(body.Level)); err != nil {
            http.Error(w, "invalid level", http.StatusBadRequest)
            return
        }
        logLevelVar.Set(level)

        // Auto-reset after 5 minutes to prevent permanent debug noise
        go func() {
            time.Sleep(5 * time.Minute)
            logLevelVar.Set(slog.LevelInfo)
        }()
    }
    json.NewEncoder(w).Encode(map[string]string{
        "level": logLevelVar.Level().String(),
    })
}
```

---

## 7. Implementing Correlation IDs and Context Propagation

### The Problem

Without a correlation ID threading through every log line, log line, and metric, you have:
- Logs from 10 services for thousands of concurrent requests, all interleaved
- No way to reconstruct the timeline of a single request

### Correlation ID Strategy

```
correlation_id  — external: provided by the API gateway or client, identifies the
                  end-to-end business transaction. Stable across retries.
                  
trace_id        — internal: OTel trace ID. Identifies a single attempt to process
                  a request. Changes on retry.
                  
request_id      — per-service: identifies a single RPC call. Changes at each hop.

session_id      — identifies a user session. Optional, for auth debugging.
```

### Go: Context Propagation with Middleware Chain

```go
// middleware/correlation.go
package middleware

import (
    "context"
    "net/http"

    "github.com/google/uuid"
)

type contextKey string

const (
    CorrelationIDKey contextKey = "correlation_id"
    RequestIDKey     contextKey = "request_id"
)

// CorrelationMiddleware extracts or generates the correlation ID.
// The correlation ID is provided by the caller (API Gateway, frontend, partner).
// If absent, generate one (we're the entry point for this transaction).
func CorrelationMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        correlationID := r.Header.Get("X-Correlation-ID")
        if correlationID == "" {
            correlationID = uuid.New().String()
        }

        requestID := uuid.New().String() // Always fresh per request

        // Store in context for use by handlers and outgoing calls
        ctx := context.WithValue(r.Context(), CorrelationIDKey, correlationID)
        ctx = context.WithValue(ctx, RequestIDKey, requestID)

        // Reflect correlation ID in response so clients can include it in bug reports
        w.Header().Set("X-Correlation-ID", correlationID)
        w.Header().Set("X-Request-ID", requestID)

        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

// InjectCorrelationHeaders injects correlation headers into outgoing HTTP requests.
// Call this when constructing requests to downstream services.
func InjectCorrelationHeaders(ctx context.Context, req *http.Request) {
    if correlationID, ok := ctx.Value(CorrelationIDKey).(string); ok {
        req.Header.Set("X-Correlation-ID", correlationID)
    }
    // The trace context (W3C traceparent) is injected separately by OTel propagator
}
```

---

## 8. Go: Debugging Microservices in Production

### Go's Debugging Advantages

Go was designed with observability in mind:
- `net/http/pprof`: Built-in profiling endpoint (CPU, heap, goroutine, mutex, block)
- `runtime/debug`: Stack traces, GC stats, build info
- `expvar`: Exported variables for runtime state
- `dlv` (Delve): Go-aware debugger with goroutine support
- Race detector: Built-in with `-race` flag
- `trace` package: Execution tracer showing goroutine lifecycle, GC, syscalls

### pprof: The Essential Production Profiler

**Never deploy a Go service in production without a pprof endpoint.** The overhead is negligible when not actively profiling, and it can save hours of debugging.

```go
// Register pprof handlers.
// CRITICAL: Protect this endpoint. It reveals implementation details
// and can consume significant CPU when profiling is active.
// Use an internal-only port or require service-level mTLS.

import _ "net/http/pprof" // Side-effect import registers handlers on DefaultServeMux

// Or register on a dedicated internal server:
func startDebugServer() {
    mux := http.NewServeMux()
    mux.Handle("/debug/pprof/", http.DefaultServeMux)

    // Expose Go runtime stats via expvar
    mux.Handle("/debug/vars", expvar.Handler())

    // Go execution tracer (produces trace.out files for go tool trace)
    mux.HandleFunc("/debug/trace", func(w http.ResponseWriter, r *http.Request) {
        duration := 5 * time.Second
        if d := r.URL.Query().Get("duration"); d != "" {
            if parsed, err := time.ParseDuration(d); err == nil {
                duration = parsed
            }
        }
        w.Header().Set("Content-Type", "application/octet-stream")
        w.Header().Set("Content-Disposition", `attachment; filename="trace.out"`)
        if err := goruntime_trace.Start(w); err != nil {
            http.Error(w, err.Error(), 500)
            return
        }
        time.Sleep(duration)
        goruntime_trace.Stop()
    })

    log.Fatal(http.ListenAndServe(":6060", mux))
}
```

#### Common pprof Investigations

```bash
# 30-second CPU profile — captures what functions consume CPU
go tool pprof http://service:6060/debug/pprof/profile?seconds=30

# Heap profile — shows live allocations
go tool pprof http://service:6060/debug/pprof/heap

# Goroutine dump — critical for diagnosing goroutine leaks
# A goroutine leak is an omission failure: service appears healthy but
# goroutines accumulate until OOM.
curl http://service:6060/debug/pprof/goroutine?debug=2 > goroutines.txt

# Mutex contention profile — identifies lock contention
# Enable first: runtime.SetMutexProfileFraction(5)
go tool pprof http://service:6060/debug/pprof/mutex

# Block profile — shows goroutines blocked on channel operations, syscalls
# Enable first: runtime.SetBlockProfileRate(1)
go tool pprof http://service:6060/debug/pprof/block

# Interactive flamegraph in browser
go tool pprof -http=:8080 http://service:6060/debug/pprof/profile?seconds=30
```

### Diagnosing Goroutine Leaks

A goroutine leak is one of the most common omission failures in Go services. The service's memory grows monotonically, response times degrade, and eventually OOM kills the pod.

```go
// antipattern.go — this leaks goroutines when ctx is cancelled
func handleRequestBAD(ctx context.Context, ids []string) []Result {
    results := make(chan Result, len(ids))

    for _, id := range ids {
        go func(id string) {
            // If ctx is cancelled before this goroutine starts,
            // it will still block on db.Query indefinitely.
            // The goroutine is leaked — nothing signals it to stop.
            result, err := db.Query(ctx, id) // may block forever if no timeout
            results <- Result{ID: id, Data: result, Err: err}
        }(id)
    }

    // ... collect results
}

// correct.go — goroutines respect context cancellation
func handleRequestGOOD(ctx context.Context, ids []string) []Result {
    g, ctx := errgroup.WithContext(ctx) // errgroup cancels ctx on first error

    results := make([]Result, len(ids))
    for i, id := range ids {
        i, id := i, id // capture loop variables
        g.Go(func() error {
            // Use context with timeout for each sub-operation
            queryCtx, cancel := context.WithTimeout(ctx, 2*time.Second)
            defer cancel()

            result, err := db.Query(queryCtx, id)
            if err != nil {
                return fmt.Errorf("query %s: %w", id, err)
            }
            results[i] = Result{ID: id, Data: result}
            return nil
        })
    }

    if err := g.Wait(); err != nil {
        // All goroutines have returned — no leak
        return nil, err
    }
    return results, nil
}
```

### Go Race Detector

The race detector instruments memory accesses at runtime and reports when two goroutines access the same memory location without synchronization, with at least one write.

```bash
# Build with race detector — 2-20x slower, 5-10x more memory.
# Use in: local testing, CI, staging. Never in prod (overhead too high).
go build -race ./...
go test -race ./...

# Race detector output:
# WARNING: DATA RACE
# Write at 0x00c0001b4010 by goroutine 7:
#   main.(*Cache).Set()
#       /app/cache.go:42 +0x68
#
# Previous read at 0x00c0001b4010 by goroutine 6:
#   main.(*Cache).Get()
#       /app/cache.go:31 +0x44
```

### Delve: Attaching to a Running Go Process

```bash
# Attach Delve to a running service (PID-based or container)
dlv attach <PID>

# Inside dlv:
(dlv) goroutines          # list all goroutines
(dlv) goroutine 15 bt     # backtrace of goroutine 15
(dlv) goroutines -with running  # only show running goroutines
(dlv) goroutines -with waiting  # goroutines waiting on sync primitive

# Set conditional breakpoint: only break when condition is true
(dlv) break order.go:89 (order.CustomerID == "cust_5678")

# Watch a variable across all goroutines
(dlv) watch -r variable_name   # break on read
(dlv) watch -w variable_name   # break on write
```

---

## 9. Rust: Debugging Microservices in Production

### Rust's Debugging Characteristics

Rust eliminates entire classes of bugs at compile time:
- **No data races** (enforced by the borrow checker)
- **No null pointer dereferences** (Option<T> must be explicitly handled)
- **No use-after-free, dangling pointers** (ownership system)
- **No buffer overflows** (bounds checking in debug builds; explicit unsafe in release)

The bugs that remain in Rust microservices are different in character:
- **Logic errors** (wrong business logic, incorrect algorithm)
- **Async runtime bugs** (task starvation, deadlock in async context)
- **Panic in production** (explicit `.unwrap()`, `.expect()`, index out of bounds)
- **Performance issues** (unexpected allocations, false sharing, lock contention)
- **FFI bugs** in unsafe blocks

### panic! Handling in Production

```rust
// Set a panic hook to log panics as structured errors before the process aborts.
// Without this, a panic in production generates only a cryptic stderr dump.

use std::panic;

pub fn install_panic_handler() {
    panic::set_hook(Box::new(|panic_info| {
        let payload = if let Some(s) = panic_info.payload().downcast_ref::<&str>() {
            s.to_string()
        } else if let Some(s) = panic_info.payload().downcast_ref::<String>() {
            s.clone()
        } else {
            "non-string panic payload".to_string()
        };

        let location = panic_info.location().map(|l| {
            format!("{}:{}:{}", l.file(), l.line(), l.column())
        }).unwrap_or_else(|| "unknown".to_string());

        // Emit a structured error log. The panic will still terminate the process,
        // but at least Loki/Elasticsearch will have a parseable record.
        tracing::error!(
            panic.payload = %payload,
            panic.location = %location,
            "PANIC: service is terminating due to an unhandled panic"
        );

        // Flush telemetry before exit
        // global::shutdown_tracer_provider() should be called here
        // if you have access to it in this context.
    }));
}
```

### Async Debugging: tokio-console

`tokio-console` is an interactive debugger for async Rust applications. It shows:
- Every task in the Tokio runtime, with state (running, idle, waiting)
- Task wakeup patterns
- Which tasks are long-running (potential starvation sources)
- Lock acquisitions

```toml
# Cargo.toml
[dependencies]
console-subscriber = "0.2"
```

```rust
// main.rs
fn main() {
    // Must be initialized BEFORE the Tokio runtime
    console_subscriber::init();

    let rt = tokio::runtime::Runtime::new().unwrap();
    rt.block_on(async_main());
}
```

```bash
# Install and run tokio-console CLI
cargo install tokio-console
tokio-console http://localhost:6669
```

### LLDB/GDB for Rust Crash Investigation

```bash
# Build with debug symbols (do not strip in staging)
# In Cargo.toml:
# [profile.release]
# debug = 1  # line number info without full debug info

# Analyze a core dump from a production crash
# First, ensure core dumps are enabled:
ulimit -c unlimited
# Or in Kubernetes: set terminationMessagePolicy to FallbackToLogsOnError

# Open the core with rust-gdb (GDB with Rust pretty-printers)
rust-gdb ./target/release/my-service core

# Inside GDB:
(gdb) bt full          # full backtrace with local variables
(gdb) thread apply all bt  # backtrace of all threads
(gdb) info registers   # register state at crash point
(gdb) x/32xb $rsp      # examine 32 bytes from stack pointer

# LLDB alternative (preferred on macOS, also works on Linux)
rust-lldb ./target/release/my-service -c core
(lldb) thread backtrace all
(lldb) frame variable  # show local variables in current frame
```

### Cargo Flamegraph for Performance Debugging

```bash
# CPU flamegraph directly from cargo
cargo install flamegraph
sudo cargo flamegraph --bin my-service -- --config config.toml

# Or profile an existing binary
sudo flamegraph -o flamegraph.svg -- ./target/release/my-service

# For async Rust, use async-aware profiling (perf + flamegraph)
sudo perf record -F 999 -g -- ./target/release/my-service
sudo perf script | stackcollapse-perf.pl | flamegraph.pl > flamegraph.svg
```

### Rust: Custom Diagnostic Endpoints

```rust
// debug_routes.rs — internal diagnostic endpoints for a production Rust service
use axum::{routing::get, Router, Json};
use serde_json::{json, Value};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

static REQUESTS_PROCESSED: AtomicU64 = AtomicU64::new(0);
static REQUESTS_FAILED: AtomicU64 = AtomicU64::new(0);
static SERVICE_START_TIME: std::sync::OnceLock<u64> = std::sync::OnceLock::new();

pub fn debug_router() -> Router {
    Router::new()
        .route("/internal/health/live", get(liveness_handler))
        .route("/internal/health/ready", get(readiness_handler))
        .route("/internal/debug/stats", get(stats_handler))
        .route("/internal/debug/config", get(config_handler))
}

/// Liveness: Is the process alive? Minimal check.
/// Kubernetes uses this to decide whether to KILL the pod.
/// NEVER check database connectivity here — if DB is down, you
/// don't want to kill all pods, you want them alive to serve cached data.
async fn liveness_handler() -> (axum::http::StatusCode, Json<Value>) {
    (axum::http::StatusCode::OK, Json(json!({"status": "alive"})))
}

/// Readiness: Is the service ready to accept traffic?
/// Kubernetes uses this to decide whether to ROUTE traffic to this pod.
/// Check database connectivity, cache warmup, config loading.
async fn readiness_handler(
    axum::extract::State(state): axum::extract::State<AppState>,
) -> (axum::http::StatusCode, Json<Value>) {
    let db_ok = state.db_pool.acquire().await.is_ok();
    let cache_ok = state.cache.ping().await.is_ok();

    if db_ok && cache_ok {
        (axum::http::StatusCode::OK, Json(json!({
            "status": "ready",
            "checks": { "database": "ok", "cache": "ok" }
        })))
    } else {
        (axum::http::StatusCode::SERVICE_UNAVAILABLE, Json(json!({
            "status": "not_ready",
            "checks": {
                "database": if db_ok { "ok" } else { "failed" },
                "cache": if cache_ok { "ok" } else { "failed" }
            }
        })))
    }
}

async fn stats_handler() -> Json<Value> {
    let uptime_secs = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs()
        - SERVICE_START_TIME.get().copied().unwrap_or(0);

    Json(json!({
        "uptime_seconds": uptime_secs,
        "requests_processed": REQUESTS_PROCESSED.load(Ordering::Relaxed),
        "requests_failed": REQUESTS_FAILED.load(Ordering::Relaxed),
        "error_rate": calculate_error_rate(),
    }))
}
```

---

## 10. C: Systems-Level Debugging for Microservice Infrastructure

C is not typically used to write microservices themselves, but it underlies the **infrastructure** that runs them: sidecar proxies (Envoy), service meshes, database engines, message brokers (Kafka C clients, RabbitMQ), kernel modules, eBPF programs, and container runtimes.

### GDB for Multi-Process C Debugging

```bash
# Debug a forking server (nginx, Apache model):
# Follow child processes after fork
(gdb) set follow-fork-mode child
(gdb) set detach-on-fork off   # Keep parent in gdb too

# Debug multiple inferiors (processes) simultaneously
(gdb) info inferiors
(gdb) inferior 2     # switch to process 2
(gdb) thread 3       # switch to thread 3

# Catch system calls (useful for debugging IPC, socket behavior)
(gdb) catch syscall read
(gdb) catch syscall connect
(gdb) catch syscall clone    # catch fork/thread creation

# Set watchpoint on memory address (detect unauthorized writes)
(gdb) watch *0x7fffffff1234
(gdb) rwatch *ptr    # break on read
(gdb) awatch *ptr    # break on read or write
```

### Valgrind for Memory Error Detection

```bash
# Memcheck: detect use-after-free, buffer overflows, uninitialized reads
valgrind --tool=memcheck \
         --leak-check=full \
         --show-leak-kinds=all \
         --track-origins=yes \
         --verbose \
         ./my-c-service

# Helgrind: detect data races in POSIX thread programs
valgrind --tool=helgrind ./my-c-service

# Callgrind: call graph and instruction-level profiling
valgrind --tool=callgrind \
         --callgrind-out-file=callgrind.out \
         ./my-c-service
callgrind_annotate callgrind.out

# Massif: heap profiler
valgrind --tool=massif \
         --pages-as-heap=yes \
         ./my-c-service
ms_print massif.out.12345
```

### AddressSanitizer (ASan) for C/C++

```bash
# Compile with ASan — finds memory errors at runtime, much faster than Valgrind
# ~2x slowdown, ~3x memory overhead — acceptable for CI and staging
gcc -g -fsanitize=address,undefined \
    -fno-omit-frame-pointer \
    -O1 \
    my-service.c -o my-service

# ThreadSanitizer: detect data races (similar to Go's -race)
gcc -g -fsanitize=thread \
    -fno-omit-frame-pointer \
    -O1 \
    my-service.c -o my-service

# Use in Docker containers for testing infrastructure components:
FROM ubuntu:22.04
ENV ASAN_OPTIONS=abort_on_error=0:detect_leaks=1:log_path=/tmp/asan
```

### strace: System Call Tracing

`strace` is invaluable for debugging C infrastructure components when you cannot modify the source or attach a debugger.

```bash
# Trace all syscalls of a running process
strace -p <PID>

# Follow forks (for multi-process servers)
strace -f -p <PID>

# Filter to specific syscalls: network and file I/O
strace -e trace=network,file -f -p <PID>

# Show timing information — critical for latency debugging
strace -T -e trace=network -p <PID>

# Count syscall frequency and time (syscall profiling)
strace -c -p <PID>

# Trace a specific operation: connect() syscall with timing
# Useful for debugging: "why does service startup take 30 seconds?"
strace -T -e trace=connect ./my-service 2>&1 | grep -A1 "connect("

# Example output showing DNS resolution timeout:
# connect(3, {sa_family=AF_INET, sin_port=htons(53), sin_addr=inet_addr("8.8.8.8")}, 16) = 0 <0.000231>
# connect(4, {sa_family=AF_INET, sin_port=htons(6379), sin_addr=inet_addr("10.0.1.5")}, 16) = -1 ECONNREFUSED <0.000104>
```

---

## 11. Linux Kernel Internals and Microservice Debugging

### How the Kernel Affects Microservice Performance

Understanding kernel internals is essential for debugging performance issues that don't appear in application-level metrics.

#### 11.1 The Network Stack

A packet arriving at a microservice pod traverses:

```
NIC → IRQ → Softirq (ksoftirqd) → netif_receive_skb()
  → Network Layer (IP routing, conntrack) 
  → Transport Layer (TCP: segment reassembly, flow control)
  → Socket receive buffer (sk_buff)
  → Application (recv()/read() syscall)
```

Performance issues at each layer:

**NIC/Driver level**: IRQ affinity mismatch — all network interrupts handled by CPU 0, causing single-CPU bottleneck.
```bash
# View IRQ affinity
cat /proc/irq/*/smp_affinity_list
# Distribute network IRQs across CPUs
echo "0-7" > /proc/irq/<NIC_IRQ>/smp_affinity_list
```

**TCP Buffer Level**: Default socket buffers too small for high-bandwidth connections.
```bash
# Check and tune TCP buffers
sysctl net.core.rmem_max    # socket receive buffer max
sysctl net.core.wmem_max    # socket send buffer max
sysctl net.ipv4.tcp_rmem    # TCP receive buffer min/default/max
sysctl net.ipv4.tcp_wmem    # TCP send buffer min/default/max

# For high-throughput services (Kafka brokers, etc.)
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
```

**Connection Tracking (conntrack)**: `nf_conntrack` tracks all TCP connections for NAT and firewall purposes. Under high connection rates, the conntrack table fills up, dropping new connections silently.
```bash
# Check conntrack table utilization
cat /proc/sys/net/netfilter/nf_conntrack_count
cat /proc/sys/net/netfilter/nf_conntrack_max

# If count approaches max, increase it
sysctl -w net.netfilter.nf_conntrack_max=1048576

# In Kubernetes: this is a common cause of mysterious connection failures
# at high scale — pods see "connection refused" but the target pod is healthy
```

**TIME_WAIT Socket Exhaustion**: Short-lived connections (HTTP/1.1 without keep-alive) accumulate sockets in TIME_WAIT state, exhausting the ephemeral port range.
```bash
# Count sockets in each state
ss -s

# Count TIME_WAIT sockets to a specific destination
ss -tn state time-wait | grep 10.0.1.5 | wc -l

# Fix: enable TCP reuse (safe for outgoing connections)
sysctl -w net.ipv4.tcp_tw_reuse=1

# Or use HTTP keep-alive (preferred — reduces connections entirely)
```

#### 11.2 CPU Scheduler and cgroup CPU Throttling

In Kubernetes, CPU limits are implemented via `cgroup v1/v2 cpu.cfs_quota_us`. When a container's CPU usage exceeds its limit within a 100ms scheduling period, it is **throttled** — all threads are paused until the next period.

This causes **latency spikes that are invisible in application metrics** because the application is literally stopped.

```bash
# Check CPU throttling in a Kubernetes pod
# Get the cgroup path for the container
cat /proc/self/cgroup

# Read throttling stats (cgroup v1)
cat /sys/fs/cgroup/cpu/kubepods/.../cpu.stat
# Key field: throttled_time (nanoseconds the container was throttled)

# In Go: expose cgroup stats via a custom metric
func getCPUThrottlingRatio() float64 {
    // Read /sys/fs/cgroup/cpu/cpu.stat and parse:
    // nr_throttled / nr_periods = throttling ratio
    // If this is > 0.05 (5%), CPU limits are too low
}

# Fix: increase CPU limits, or switch to BestEffort/Burstable
# class by removing cpu limits (controversial but sometimes correct)
```

#### 11.3 Memory: OOM Killer and Memory Pressure

```bash
# Check if processes are being OOM killed
dmesg | grep -i "killed process"
# Or in Kubernetes:
kubectl describe pod <pod-name> | grep -A 5 "OOM"

# Check memory pressure (cgroup v2)
cat /sys/fs/cgroup/memory.pressure
# Format: avg10=X avg60=Y avg300=Z total=Z

# View memory stats per cgroup
cat /sys/fs/cgroup/memory/kubepods/.../memory.stat
# Important: rss, cache, mapped_file, pgmajfault (major page faults = disk I/O)

# Huge pages: if your service allocates large amounts of memory,
# THP (Transparent HugePage) may cause latency spikes during compaction
cat /sys/kernel/mm/transparent_hugepage/enabled
# For latency-sensitive services: disable THP
echo never > /sys/kernel/mm/transparent_hugepage/enabled
```

#### 11.4 File Descriptor Limits

```bash
# Check per-process file descriptor usage (crucial for connection-heavy services)
ls /proc/<PID>/fd | wc -l   # Count open file descriptors
cat /proc/<PID>/limits       # View current limits

# System-wide file descriptor usage
cat /proc/sys/fs/file-nr     # open / free / max

# Increase limits for production services
# In /etc/security/limits.conf:
# myservice soft nofile 1048576
# myservice hard nofile 1048576

# Or via systemd service unit:
# [Service]
# LimitNOFILE=1048576

# In Kubernetes: set in pod spec
# securityContext:
#   sysctls:
#   - name: fs.file-max
#     value: "1048576"
```

### 11.5 epoll: Understanding Event-Driven I/O

Most Go, Rust, and Node.js servers use epoll under the hood for I/O multiplexing. Understanding its behavior helps debug I/O-bound performance issues.

```c
/*
 * Minimal epoll event loop — the pattern used by virtually every
 * high-performance network server (nginx, Redis, Node.js libuv,
 * Go netpoller, Tokio mio).
 *
 * Understanding this helps you interpret strace output and kernel
 * perf profiles for your service infrastructure.
 */

#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>

#define MAX_EVENTS 1024
#define TIMEOUT_MS 100   /* wake up even without events — for timeouts */

int run_event_loop(int listen_fd) {
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) {
        perror("epoll_create1");
        return -1;
    }

    /* Watch for incoming connections on the listen socket */
    struct epoll_event ev = {
        .events = EPOLLIN,
        .data.fd = listen_fd,
    };
    if (epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev) < 0) {
        perror("epoll_ctl: listen_fd");
        return -1;
    }

    struct epoll_event events[MAX_EVENTS];

    for (;;) {
        int n = epoll_wait(epfd, events, MAX_EVENTS, TIMEOUT_MS);
        if (n < 0) {
            if (errno == EINTR) continue; /* Signal interrupted — not an error */
            perror("epoll_wait");
            break;
        }

        if (n == 0) {
            /* Timeout: process pending timers, check for stale connections */
            process_timers();
            continue;
        }

        for (int i = 0; i < n; i++) {
            if (events[i].data.fd == listen_fd) {
                /* Accept new connection */
                int conn_fd = accept4(listen_fd, NULL, NULL,
                                      SOCK_NONBLOCK | SOCK_CLOEXEC);
                if (conn_fd < 0) {
                    if (errno == EAGAIN || errno == EWOULDBLOCK) continue;
                    perror("accept4");
                    continue;
                }

                /* Add new connection to epoll in edge-triggered mode.
                 * EPOLLET: only notify on state change (fd becomes readable),
                 * not repeatedly while data is available. More efficient but
                 * requires draining the socket buffer completely on each event. */
                struct epoll_event conn_ev = {
                    .events = EPOLLIN | EPOLLET | EPOLLRDHUP,
                    .data.fd = conn_fd,
                };
                epoll_ctl(epfd, EPOLL_CTL_ADD, conn_fd, &conn_ev);
            } else {
                int fd = events[i].data.fd;

                if (events[i].events & (EPOLLHUP | EPOLLERR | EPOLLRDHUP)) {
                    /* Connection closed or error — clean up */
                    epoll_ctl(epfd, EPOLL_CTL_DEL, fd, NULL);
                    close(fd);
                    continue;
                }

                if (events[i].events & EPOLLIN) {
                    handle_readable(fd);
                }
                if (events[i].events & EPOLLOUT) {
                    handle_writable(fd);
                }
            }
        }
    }

    close(epfd);
    return 0;
}
```

---

## 12. eBPF: Kernel-Level Observability Without Patching

eBPF (extended Berkeley Packet Filter) allows running sandboxed programs inside the Linux kernel in response to events. For microservice debugging, it provides:

- **Network-level tracing**: Observe packets, connection events, socket operations without modifying services
- **Syscall tracing**: Track every syscall by every process in the node, with full context
- **Profiling**: CPU profiling across the entire node, including kernel time
- **Security**: Detect anomalous behavior (unexpected binary execution, network connections)

eBPF programs are safe: the kernel verifier checks them for safety (no infinite loops, no memory access out of bounds) before loading.

### bpftrace: High-Level eBPF Scripting

```bash
# Trace all connect() syscalls in the cluster — immediately see which
# service is making unexpected outbound connections
bpftrace -e '
  tracepoint:syscalls:sys_enter_connect {
    printf("PID: %d COMM: %s\n", pid, comm);
  }
'

# Measure HTTP response latency without touching the application.
# Attaches to write() syscalls and correlates with read() calls.
bpftrace -e '
  kretprobe:tcp_sendmsg {
    @latency[pid] = nsecs;
  }
  kretprobe:tcp_recvmsg /@latency[pid]/ {
    $lat = (nsecs - @latency[pid]) / 1000;
    printf("PID %d latency: %d us\n", pid, $lat);
    delete(@latency[pid]);
  }
'

# Find processes causing high context switch rates (CPU scheduler pressure)
bpftrace -e '
  software:context-switches:1000 {
    @[comm] = count();
  }
  interval:s:10 {
    print(@);
    clear(@);
  }
'

# Detect slow disk I/O — find which operations take >10ms
bpftrace -e '
  kprobe:blk_start_request { @start[arg0] = nsecs; }
  kprobe:blk_mq_start_request { @start[arg0] = nsecs; }
  kretprobe:blk_account_io_done
  /@start[arg0]/ {
    $latency_ms = (nsecs - @start[arg0]) / 1000000;
    if ($latency_ms > 10) {
      printf("Slow I/O: %d ms, comm: %s\n", $latency_ms, comm);
    }
    delete(@start[arg0]);
  }
'

# Trace DNS queries across all containers — no service modification needed
bpftrace -e '
  uprobe:/lib/x86_64-linux-gnu/libc.so.6:getaddrinfo {
    printf("DNS query by %s (PID %d): %s\n", comm, pid, str(arg0));
  }
'
```

### BCC Tools for Microservice Debugging

```bash
# Install bcc-tools on the node (not in containers)
apt-get install bpfcc-tools

# tcpconnect: trace all TCP connect() calls in real time
tcpconnect-bpfcc

# tcpretrans: show TCP retransmissions (network instability indicator)
tcpretrans-bpfcc

# tcplife: show TCP connection lifetime and bytes transferred
tcplife-bpfcc -T    # include timestamps

# runqlat: measure CPU run queue latency (scheduler saturation)
# High values = CPUs are saturated, goroutines/threads waiting to run
runqlat-bpfcc 1 5   # 1 second interval, 5 samples

# offcputime: show time processes spend off-CPU (blocked on I/O, locks, etc.)
offcputime-bpfcc -p <PID> 10   # profile PID for 10 seconds

# biolatency: disk I/O latency distribution
biolatency-bpfcc 1

# cachestat: page cache hit/miss ratio
cachestat-bpfcc 1

# memleak: detect memory leaks in C programs (attach to malloc/free)
memleak-bpfcc -p <PID>

# funclatency: measure latency of any kernel or user-space function
funclatency-bpfcc 'go:runtime.mallocgc'  # Go allocation latency
funclatency-bpfcc 'libpthread:pthread_mutex_lock'  # Mutex acquisition latency
```

### Writing eBPF Programs in Go (cilium/ebpf)

```go
// network_probe.go — eBPF program to trace HTTP requests at the kernel level
// Uses cilium/ebpf library for type-safe eBPF interaction from Go.
// Attach to kernel TCP send/recv hooks to observe traffic without
// modifying the application or using a sidecar proxy.

//go:generate go run github.com/cilium/ebpf/cmd/bpf2go NetworkProbe ./bpf/network_probe.c

package probe

import (
    "encoding/binary"
    "net"
    "os"
    "time"

    "github.com/cilium/ebpf"
    "github.com/cilium/ebpf/link"
    "github.com/cilium/ebpf/ringbuf"
)

// NetworkEvent mirrors the struct defined in the eBPF C program
type NetworkEvent struct {
    PID       uint32
    SrcIP     [4]byte
    DstIP     [4]byte
    SrcPort   uint16
    DstPort   uint16
    Bytes     uint32
    LatencyNs uint64
    Comm      [16]byte
}

type NetworkProbe struct {
    objs    NetworkProbeObjects
    links   []link.Link
    reader  *ringbuf.Reader
    events  chan NetworkEvent
}

func NewNetworkProbe() (*NetworkProbe, error) {
    objs := NetworkProbeObjects{}
    if err := LoadNetworkProbeObjects(&objs, nil); err != nil {
        return nil, err
    }

    reader, err := ringbuf.NewReader(objs.NetworkEvents)
    if err != nil {
        return nil, err
    }

    probe := &NetworkProbe{
        objs:   objs,
        reader: reader,
        events: make(chan NetworkEvent, 1024),
    }

    // Attach to kprobe: tcp_sendmsg — fires on every TCP send
    l, err := link.Kprobe("tcp_sendmsg", objs.TraceTcpSendmsg, nil)
    if err != nil {
        return nil, err
    }
    probe.links = append(probe.links, l)

    go probe.readEvents()

    return probe, nil
}

func (p *NetworkProbe) readEvents() {
    for {
        record, err := p.reader.Read()
        if err != nil {
            return
        }

        var event NetworkEvent
        if err := binary.Read(
            bytes.NewReader(record.RawSample),
            binary.LittleEndian,
            &event,
        ); err != nil {
            continue
        }

        select {
        case p.events <- event:
        default:
            // Drop if channel full — prefer dropping to blocking the kernel ring buffer
        }
    }
}

func (p *NetworkProbe) Events() <-chan NetworkEvent {
    return p.events
}

func (p *NetworkProbe) Close() {
    for _, l := range p.links {
        l.Close()
    }
    p.reader.Close()
    p.objs.Close()
}
```

---

## 13. Network Stack Debugging: TCP, UDP, and Beyond

### Essential Network Debugging Commands

```bash
# ss (socket statistics) — modern replacement for netstat
# Show all TCP connections with process info
ss -tnp

# Count connections by state
ss -s

# Show connections to a specific service
ss -tnp dst 10.0.1.5:5432

# Show send/receive queue sizes (large rcv queue = app not reading fast enough)
ss -tnp | awk '{print $3, $4}' | sort -n | tail

# tcpdump: capture and analyze packets
# Capture HTTP traffic on port 8080
tcpdump -i any -A port 8080

# Capture traffic to/from specific IP, save to file for Wireshark analysis
tcpdump -i eth0 -w /tmp/capture.pcap host 10.0.1.5

# Capture and decode HTTP requests (no SSL — use mitmproxy or Wireshark for TLS)
tcpdump -i any -A -s 0 'tcp port 8080 and (((ip[2:2] - ((ip[0]&0xf)<<2)) - ((tcp[12]&0xf0)>>2)) != 0)'

# Analyze MTU and fragmentation issues
# Large packets getting fragmented causes latency and potential reassembly failures
ping -M do -s 1472 10.0.1.5  # Test with max Ethernet payload (1500 - 20 IP - 8 ICMP)

# Check for packet loss on a specific network path
mtr --report --report-cycles 100 10.0.1.5

# Diagnose TCP retransmissions
netstat -s | grep -i retransmit
# Or with nstat (kernel counters):
nstat -az | grep -i retransmit

# Check TCP congestion control algorithm in use
sysctl net.ipv4.tcp_congestion_control

# ip route: diagnose routing issues (packets going to wrong interface)
ip route get 10.0.1.5

# arp: diagnose layer 2 issues (wrong MAC addresses after pod migration)
arp -n
```

### Diagnosing Kubernetes Network Issues

```bash
# Check kube-proxy iptables rules for a service
iptables-save | grep <SERVICE_NAME>

# Verify service endpoints are populated
kubectl get endpoints <service-name>
# If endpoints are empty: pod labels don't match service selector

# Check DNS resolution inside a pod
kubectl exec -it <pod> -- nslookup kubernetes.default.svc.cluster.local
kubectl exec -it <pod> -- nslookup <service-name>.<namespace>.svc.cluster.local

# Check CoreDNS health
kubectl -n kube-system get pods -l k8s-app=kube-dns
kubectl -n kube-system logs -l k8s-app=kube-dns

# Trace a packet from pod A to pod B (Cilium)
cilium policy trace -s <source-pod> -d <dest-pod> --dport 8080

# Network Policy debugging: is traffic being dropped by policy?
kubectl get networkpolicy -A
# Test connectivity with a debug pod
kubectl run debug --image=nicolaka/netshoot --rm -it -- bash
# Inside debug pod:
curl http://<service>:8080
traceroute <pod-ip>

# Check CNI plugin logs (Calico, Flannel, Cilium, WeaveNet)
kubectl -n kube-system logs -l k8s-app=cilium --tail=100

# Diagnose pod-to-pod connectivity failures
# Create a packet capture on both pods simultaneously
kubectl exec -it <pod-a> -- tcpdump -i eth0 -w /tmp/pod-a.pcap &
kubectl exec -it <pod-b> -- tcpdump -i eth0 -w /tmp/pod-b.pcap &
# Make the failing request
# Kill tcpdump, copy pcap files, analyze in Wireshark
```

---

## 14. Partial Failures, Retries, and Cascading Failures

### Circuit Breakers

The circuit breaker pattern prevents a failing downstream service from causing resource exhaustion in the caller. Three states:

**Closed**: Normal operation. Requests flow through. Track failure rate.
**Open**: Downstream is failing. Reject requests immediately (return error or fallback). No load sent to downstream.
**Half-open**: After a timeout, allow a limited number of probe requests. If they succeed, close the circuit. If they fail, re-open.

```go
// circuitbreaker.go — production circuit breaker implementation
package cb

import (
    "errors"
    "sync"
    "time"

    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

type State int

const (
    StateClosed   State = iota // Normal: requests flow through
    StateHalfOpen              // Probing: limited requests allowed
    StateOpen                  // Tripped: fast fail all requests
)

var ErrCircuitOpen = errors.New("circuit breaker is open")

type CircuitBreaker struct {
    mu sync.Mutex

    name           string
    state          State
    failureCount   int
    successCount   int
    lastFailureAt  time.Time
    openedAt       time.Time

    // Configuration
    failureThreshold int           // failures before opening
    successThreshold int           // successes in half-open before closing
    openDuration     time.Duration // how long to stay open before half-open
    halfOpenRequests int           // max concurrent requests in half-open
    activeHalfOpen   int
}

func NewCircuitBreaker(name string) *CircuitBreaker {
    return &CircuitBreaker{
        name:             name,
        state:            StateClosed,
        failureThreshold: 5,
        successThreshold: 2,
        openDuration:     30 * time.Second,
        halfOpenRequests: 3,
    }
}

func (cb *CircuitBreaker) Execute(ctx context.Context, fn func(context.Context) error) error {
    span := trace.SpanFromContext(ctx)

    cb.mu.Lock()
    state := cb.currentState()
    span.SetAttributes(
        attribute.String("circuit_breaker.name", cb.name),
        attribute.String("circuit_breaker.state", stateString(state)),
    )

    switch state {
    case StateOpen:
        cb.mu.Unlock()
        span.SetAttributes(attribute.Bool("circuit_breaker.rejected", true))
        return ErrCircuitOpen

    case StateHalfOpen:
        if cb.activeHalfOpen >= cb.halfOpenRequests {
            cb.mu.Unlock()
            return ErrCircuitOpen
        }
        cb.activeHalfOpen++
        cb.mu.Unlock()

        err := fn(ctx)

        cb.mu.Lock()
        cb.activeHalfOpen--
        if err != nil {
            cb.onFailure()
        } else {
            cb.onSuccess()
        }
        cb.mu.Unlock()
        return err

    default: // Closed
        cb.mu.Unlock()
        err := fn(ctx)
        cb.mu.Lock()
        if err != nil {
            cb.onFailure()
        } else {
            cb.resetFailures()
        }
        cb.mu.Unlock()
        return err
    }
}

func (cb *CircuitBreaker) currentState() State {
    if cb.state == StateOpen {
        if time.Since(cb.openedAt) > cb.openDuration {
            cb.state = StateHalfOpen
            cb.successCount = 0
        }
    }
    return cb.state
}

func (cb *CircuitBreaker) onFailure() {
    cb.failureCount++
    cb.lastFailureAt = time.Now()
    if cb.state == StateHalfOpen || cb.failureCount >= cb.failureThreshold {
        cb.state = StateOpen
        cb.openedAt = time.Now()
    }
}

func (cb *CircuitBreaker) onSuccess() {
    if cb.state == StateHalfOpen {
        cb.successCount++
        if cb.successCount >= cb.successThreshold {
            cb.state = StateClosed
            cb.failureCount = 0
            cb.successCount = 0
        }
    }
}

func (cb *CircuitBreaker) resetFailures() { cb.failureCount = 0 }
```

### Retry Strategies

```go
// retry.go — exponential backoff with jitter
package retry

import (
    "context"
    "math"
    "math/rand"
    "time"
)

type Config struct {
    MaxAttempts     int
    InitialInterval time.Duration
    MaxInterval     time.Duration
    Multiplier      float64
    // Jitter prevents retry storms: when 1000 clients retry simultaneously,
    // jitter spreads their retries over a time window instead of a synchronized spike.
    JitterFactor float64
}

var DefaultConfig = Config{
    MaxAttempts:     4,
    InitialInterval: 100 * time.Millisecond,
    MaxInterval:     30 * time.Second,
    Multiplier:      2.0,
    JitterFactor:    0.5,
}

// IsRetryable defines which errors should trigger a retry.
// NEVER retry on:
//   - 4xx errors (client error — retrying won't help)
//   - Business logic failures (insufficient funds, invalid input)
//   - Timeout errors if the operation is NOT idempotent
// DO retry on:
//   - 503 Service Unavailable
//   - 429 Too Many Requests (with respect to Retry-After header)
//   - Connection refused / reset
//   - Timeout on idempotent operations
type IsRetryable func(error) bool

func Do(ctx context.Context, cfg Config, fn func(ctx context.Context) error, isRetryable IsRetryable) error {
    var lastErr error

    for attempt := 0; attempt < cfg.MaxAttempts; attempt++ {
        if err := ctx.Err(); err != nil {
            return err // Context cancelled — don't retry
        }

        lastErr = fn(ctx)
        if lastErr == nil {
            return nil
        }

        if !isRetryable(lastErr) {
            return lastErr // Non-retryable error — fail immediately
        }

        if attempt == cfg.MaxAttempts-1 {
            break // Last attempt — don't sleep
        }

        sleep := backoffDuration(cfg, attempt)
        select {
        case <-time.After(sleep):
        case <-ctx.Done():
            return ctx.Err()
        }
    }

    return fmt.Errorf("all %d attempts failed, last error: %w", cfg.MaxAttempts, lastErr)
}

func backoffDuration(cfg Config, attempt int) time.Duration {
    // Exponential: initial * multiplier^attempt
    exp := cfg.InitialInterval.Seconds() * math.Pow(cfg.Multiplier, float64(attempt))
    maxSecs := cfg.MaxInterval.Seconds()

    if exp > maxSecs {
        exp = maxSecs
    }

    // Full jitter: random value between 0 and computed backoff
    // "Full Jitter" (AWS blog) outperforms "Equal Jitter" in practice
    jittered := exp * (1 - cfg.JitterFactor*rand.Float64())

    return time.Duration(jittered * float64(time.Second))
}
```

### Bulkhead Pattern

The bulkhead isolates failures to one part of the system, preventing a slow downstream from exhausting all resources and affecting unrelated functionality.

```go
// bulkhead.go — isolate resource usage per downstream dependency
type Bulkhead struct {
    sem chan struct{} // counting semaphore
    name string
}

func NewBulkhead(name string, maxConcurrent int) *Bulkhead {
    return &Bulkhead{
        name: name,
        sem:  make(chan struct{}, maxConcurrent),
    }
}

func (b *Bulkhead) Execute(ctx context.Context, fn func(context.Context) error) error {
    // Try to acquire a slot
    select {
    case b.sem <- struct{}{}:
        defer func() { <-b.sem }()
        return fn(ctx)
    case <-ctx.Done():
        return ctx.Err()
    default:
        // Bulkhead full — shed load immediately rather than queuing
        // Record metric: bulkhead_rejected_total{name=b.name}
        return fmt.Errorf("bulkhead %q at capacity (%d concurrent)", b.name, cap(b.sem))
    }
}
```

---

## 15. Data Consistency Debugging Across Service Boundaries

### The Distributed Transaction Problem

When a business operation spans multiple services, each with its own database, you cannot use a single ACID transaction. Partial failures leave the system in inconsistent states.

### Two-Phase Commit (2PC) — Why It's Problematic

2PC provides distributed atomicity via a coordinator. Phase 1 (Prepare): all participants vote on whether they can commit. Phase 2 (Commit/Rollback): coordinator issues the decision.

Problems:
- **Blocking protocol**: If coordinator fails after Phase 1 but before Phase 2, participants are blocked in prepared state, holding locks
- **Single point of failure**: The coordinator's log is critical
- **Performance**: Two network round trips per transaction
- **Not cloud-native**: Requires persistent coordinator state, hard to scale

### Saga Pattern

A saga is a sequence of local transactions where each transaction publishes events or messages that trigger the next step. Failures are handled by compensating transactions (semantic rollbacks).

```
Order Saga:
  1. Create Order (Pending)      → publish OrderCreated
  2. Reserve Inventory            → publish InventoryReserved
  3. Process Payment              → publish PaymentProcessed
  4. Confirm Order (Confirmed)   → publish OrderConfirmed

Failure at step 3 (Payment fails):
  3C. Compensate: Refund Payment  (no-op if not charged)
  2C. Compensate: Release Inventory
  1C. Compensate: Cancel Order
```

```go
// saga.go — orchestration-based saga (vs choreography-based)
// Orchestration: central coordinator drives the saga (easier to debug)
// Choreography: services react to events (less coupling, harder to debug)

type SagaStep struct {
    Name        string
    Execute     func(ctx context.Context, state *SagaState) error
    Compensate  func(ctx context.Context, state *SagaState) error
}

type Saga struct {
    steps []SagaStep
}

func (s *Saga) Execute(ctx context.Context, state *SagaState) error {
    executed := make([]int, 0, len(s.steps))

    for i, step := range s.steps {
        ctx, span := tracer.Start(ctx, fmt.Sprintf("saga.%s", step.Name))

        if err := step.Execute(ctx, state); err != nil {
            span.RecordError(err)
            span.SetStatus(codes.Error, fmt.Sprintf("saga step %s failed", step.Name))
            span.End()

            // Execute compensations in reverse order
            // Compensations must be idempotent: they may be called multiple times
            // if the saga coordinator crashes during compensation.
            for j := len(executed) - 1; j >= 0; j-- {
                compStep := s.steps[executed[j]]
                compCtx, compSpan := tracer.Start(ctx,
                    fmt.Sprintf("saga.compensate.%s", compStep.Name))

                if compErr := compStep.Compensate(compCtx, state); compErr != nil {
                    // Compensation failed — this requires human intervention.
                    // Log with high severity, alert on-call, mark saga as "stuck".
                    slog.ErrorContext(compCtx, "saga compensation failed",
                        slog.String("saga_id", state.ID),
                        slog.String("failed_step", step.Name),
                        slog.String("compensation_step", compStep.Name),
                        slog.Any("error", compErr),
                    )
                    compSpan.RecordError(compErr)
                }
                compSpan.End()
            }

            return fmt.Errorf("saga failed at step %s: %w", step.Name, err)
        }

        span.End()
        executed = append(executed, i)
    }

    return nil
}
```

### Debugging Eventual Consistency Issues

```go
// Debugging pattern: outbox table for reliable event publishing.
// Problem: writing to DB and publishing to message queue cannot be atomic.
// If the service crashes between DB commit and queue publish, the event is lost.
//
// Solution: write events to an "outbox" table in the same DB transaction as
// the business data. A separate relay process polls the outbox and publishes.
// This ensures at-least-once delivery.

// In a single DB transaction:
func (s *OrderService) CreateOrder(ctx context.Context, req CreateOrderRequest) error {
    return s.db.WithTransaction(ctx, func(tx *sql.Tx) error {
        // 1. Write the order
        orderID, err := insertOrder(ctx, tx, req)
        if err != nil {
            return err
        }

        // 2. Write the event to the outbox table (same transaction = atomic)
        event := OutboxEvent{
            ID:          uuid.New().String(),
            AggregateID: orderID,
            EventType:   "order.created",
            Payload:     mustMarshal(OrderCreatedEvent{OrderID: orderID, ...}),
            CreatedAt:   time.Now(),
            Published:   false,
        }
        return insertOutboxEvent(ctx, tx, event)
        // If this transaction commits: order AND event are written atomically.
        // If it fails: neither is written.
        // The relay process will find the unpublished event and publish it.
    })
}
```

---

## 16. Concurrency, Race Conditions, and Distributed Deadlocks

### Distributed Deadlocks

A distributed deadlock occurs when service A holds a resource and waits for service B, while service B holds a resource and waits for service A. In a microservice context, "resources" are often database row locks.

**Detection approach**: implement a wait-for graph. Each node is a transaction; each edge represents "transaction X is waiting for transaction Y to release a lock." A cycle in this graph = deadlock.

PostgreSQL detects deadlocks automatically within a single instance (default: 1 second `deadlock_timeout`). Across multiple PostgreSQL instances, no automatic detection exists — you must implement it in application logic.

```sql
-- PostgreSQL: view current lock waits
SELECT
    blocked.pid        AS blocked_pid,
    blocked.query      AS blocked_query,
    blocking.pid       AS blocking_pid,
    blocking.query     AS blocking_query,
    blocked.wait_event AS wait_event
FROM pg_catalog.pg_locks AS blocked_locks
JOIN pg_catalog.pg_stat_activity AS blocked
    ON blocked.pid = blocked_locks.pid
JOIN pg_catalog.pg_locks AS blocking_locks
    ON blocking_locks.locktype = blocked_locks.locktype
    AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
    AND blocking_locks.granted
    AND NOT blocked_locks.granted
JOIN pg_catalog.pg_stat_activity AS blocking
    ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted;

-- View long-running transactions (potential deadlock participants)
SELECT pid, now() - xact_start AS duration, state, query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
ORDER BY duration DESC
LIMIT 20;

-- Kill a blocking query (use with care in production)
SELECT pg_terminate_backend(<blocking_pid>);
```

### Race Condition Patterns in Distributed Systems

#### Check-Then-Act Without Atomicity

```go
// WRONG: race condition between check and act
func (s *InventoryService) ReserveItem(ctx context.Context, itemID string, qty int) error {
    available, _ := s.db.GetAvailableQty(ctx, itemID) // SELECT available FROM inventory
    if available < qty {
        return ErrInsufficientStock
    }
    // Another request may execute here, also seeing available >= qty
    s.db.DecrementQty(ctx, itemID, qty) // UPDATE inventory SET available = available - qty
    return nil
}

// CORRECT: atomic check-and-update with conditional UPDATE
func (s *InventoryService) ReserveItem(ctx context.Context, itemID string, qty int) error {
    result, err := s.db.ExecContext(ctx, `
        UPDATE inventory
        SET available = available - $2,
            reserved  = reserved  + $2
        WHERE item_id = $1
          AND available >= $2  -- Atomic check: only update if stock is sufficient
    `, itemID, qty)

    rows, _ := result.RowsAffected()
    if rows == 0 {
        return ErrInsufficientStock // Either item not found or stock insufficient
    }
    return err
}
```

#### Optimistic Locking for Concurrent Updates

```go
// Use a version counter to detect concurrent modifications.
// Read the current version, include it in the UPDATE condition.
// If another writer updated between your read and write, the version
// won't match and you'll get 0 rows affected — retry.

type Account struct {
    ID      string
    Balance int64
    Version int64
}

func (s *AccountService) Debit(ctx context.Context, accountID string, amount int64) error {
    const maxRetries = 3
    for attempt := 0; attempt < maxRetries; attempt++ {
        account, err := s.db.GetAccount(ctx, accountID)
        if err != nil {
            return err
        }
        if account.Balance < amount {
            return ErrInsufficientFunds
        }

        result, err := s.db.ExecContext(ctx, `
            UPDATE accounts
            SET balance = balance - $2,
                version = version + 1
            WHERE id = $1
              AND version = $3   -- Optimistic lock: only update if version matches
        `, accountID, amount, account.Version)
        if err != nil {
            return err
        }

        rows, _ := result.RowsAffected()
        if rows == 1 {
            return nil // Success
        }
        // Version mismatch = concurrent modification — retry
        time.Sleep(time.Duration(attempt+1) * 10 * time.Millisecond)
    }
    return ErrConcurrentModification
}
```

---

## 17. API Versioning, Schema Drift, and Contract Testing

### The Schema Drift Problem

Services evolve independently. When Service A deploys a new API version but Service B hasn't been updated, subtle failures occur:
- Missing required fields (B sends a request A now requires fields for)
- Type changes (B sends int, A now expects string)
- Enum value additions (A sends new enum value B doesn't handle)
- Semantic changes (field meaning changed without renaming)

### Consumer-Driven Contract Testing with Pact

```go
// pact_test.go — consumer side: defines expected interactions
// Consumer: Order Service (calls Payment Service)
// Provider: Payment Service
// Contract: a JSON file committed to a broker (Pact Broker)

func TestPaymentServiceContract(t *testing.T) {
    pact := dsl.Pact{
        Consumer: "OrderService",
        Provider: "PaymentService",
    }

    defer pact.Teardown()

    // Define expected interaction
    pact.
        AddInteraction().
        Given("Customer cust_123 exists with valid payment method").
        UponReceiving("A charge request for $99.99").
        WithRequest(dsl.Request{
            Method: "POST",
            Path:   dsl.String("/v1/charges"),
            Headers: dsl.MapMatcher{
                "Content-Type": dsl.String("application/json"),
            },
            Body: map[string]interface{}{
                "customer_id": dsl.String("cust_123"),
                "amount":      dsl.Like(9999), // "Like" = match type, not value
                "currency":    dsl.Term("USD", `^[A-Z]{3}$`), // regex match
            },
        }).
        WillRespondWith(dsl.Response{
            Status: 200,
            Body: map[string]interface{}{
                "transaction_id": dsl.Like("txn_abc123"),
                "status":         dsl.Term("succeeded", `succeeded|pending|failed`),
                "amount":         dsl.Like(9999),
            },
        })

    // Run the test against the mock
    err := pact.Verify(func() error {
        client := NewPaymentClient(fmt.Sprintf("http://localhost:%d", pact.Server.Port))
        result, err := client.Charge(context.Background(), ChargeRequest{
            CustomerID: "cust_123",
            Amount:     9999,
            Currency:   "USD",
        })
        if err != nil {
            return err
        }
        assert.Equal(t, "succeeded", result.Status)
        return nil
    })

    assert.NoError(t, err)
    // Publish contract to Pact Broker
    pact.PublishPacts(PublishOptions{
        PactBroker: "https://pact-broker.internal",
        Tags:       []string{"main", version},
    })
}
```

### Protobuf Schema Evolution Rules

```protobuf
// payment.proto — rules for safe schema evolution

syntax = "proto3";

message ChargeRequest {
  string customer_id = 1;  // Field numbers are permanent — never reuse them
  int64  amount_cents = 2;
  string currency     = 3;
  // Safe additions:
  // - New optional fields (proto3 all fields are optional)
  // - New enum values (receivers must handle unknown enum values)
  string idempotency_key = 4;  // Added in v2 — backward compatible
  
  // NEVER do:
  // - Change field number (1, 2, 3...) — breaks wire format
  // - Change field type (int64 → int32) — breaks deserialization
  // - Remove a field and reuse its number — silent data corruption
  // - Rename a field number reservation to a different semantic meaning
  
  // Mark removed fields as reserved to prevent reuse:
  // reserved 5, 6;
  // reserved "old_field_name";
}
```

---

## 18. Asynchronous Communication: Queues, Events, and Message Brokers

### The Challenges of Async Debugging

Asynchronous communication introduces dimensions that synchronous debugging doesn't have:
- **Delayed execution**: Message published now, processed in 5 seconds — the trace is disconnected
- **Duplicate messages**: At-least-once delivery means consumers must be idempotent
- **Out-of-order processing**: Messages from the same producer may arrive in different order
- **Dead letter queues**: Failed messages accumulate silently
- **Poison pill messages**: One malformed message blocks queue processing

### Propagating Trace Context Through Message Queues

```go
// kafka_tracing.go — trace context propagation through Kafka
// Without this, every consumer creates a new root trace, and you cannot
// link the producer's trace to the consumer's trace.

import (
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
    kafkago "github.com/segmentio/kafka-go"
)

// HeaderCarrier adapts Kafka message headers to the OTel TextMapCarrier interface.
// This allows the OTel propagator to inject/extract trace context from Kafka headers.
type KafkaHeaderCarrier struct {
    headers *[]kafkago.Header
}

func (c KafkaHeaderCarrier) Get(key string) string {
    for _, h := range *c.headers {
        if strings.EqualFold(h.Key, key) {
            return string(h.Value)
        }
    }
    return ""
}

func (c KafkaHeaderCarrier) Set(key string, value string) {
    *c.headers = append(*c.headers, kafkago.Header{
        Key: key, Value: []byte(value),
    })
}

func (c KafkaHeaderCarrier) Keys() []string {
    keys := make([]string, len(*c.headers))
    for i, h := range *c.headers {
        keys[i] = h.Key
    }
    return keys
}

// ProduceWithTracing publishes a Kafka message with injected trace context.
func ProduceWithTracing(ctx context.Context, writer *kafkago.Writer, msg kafkago.Message) error {
    ctx, span := tracer.Start(ctx, "kafka.produce",
        trace.WithSpanKind(trace.SpanKindProducer),
        trace.WithAttributes(
            semconv.MessagingSystem("kafka"),
            semconv.MessagingDestinationName(msg.Topic),
            attribute.String("messaging.kafka.partition", fmt.Sprintf("%d", msg.Partition)),
        ),
    )
    defer span.End()

    // Inject trace context into message headers
    carrier := KafkaHeaderCarrier{headers: &msg.Headers}
    otel.GetTextMapPropagator().Inject(ctx, carrier)

    if err := writer.WriteMessages(ctx, msg); err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "kafka produce failed")
        return err
    }
    return nil
}

// ConsumeWithTracing extracts trace context from a Kafka message and creates
// a linked span. We use a Link (not parent-child) because the producer and
// consumer traces are causally related but temporally separated.
func ConsumeWithTracing(ctx context.Context, msg kafkago.Message, fn func(context.Context) error) error {
    // Extract upstream trace context from message headers
    carrier := KafkaHeaderCarrier{headers: &msg.Headers}
    producerCtx := otel.GetTextMapPropagator().Extract(ctx, carrier)
    producerSpanCtx := trace.SpanContextFromContext(producerCtx)

    // Create a new span for the consumer, linked to the producer's span.
    // This creates a cross-trace link in Jaeger/Tempo, allowing navigation
    // from consumer trace to producer trace and vice versa.
    opts := []trace.SpanStartOption{
        trace.WithSpanKind(trace.SpanKindConsumer),
        trace.WithAttributes(
            semconv.MessagingSystem("kafka"),
            semconv.MessagingSourceName(msg.Topic),
            attribute.Int("messaging.kafka.partition", msg.Partition),
            attribute.Int64("messaging.kafka.offset", msg.Offset),
        ),
    }

    if producerSpanCtx.IsValid() {
        opts = append(opts, trace.WithLinks(trace.Link{SpanContext: producerSpanCtx}))
    }

    ctx, span := tracer.Start(ctx, "kafka.consume", opts...)
    defer span.End()

    if err := fn(ctx); err != nil {
        span.RecordError(err)
        span.SetStatus(codes.Error, "message processing failed")
        return err
    }
    return nil
}
```

### Dead Letter Queue Monitoring

```go
// dlq_monitor.go — monitor dead letter queues and alert on accumulation
// DLQ messages indicate processing failures that need investigation.
// A growing DLQ is a silent service failure.

func (m *DLQMonitor) CollectMetrics(ctx context.Context) {
    for _, topic := range m.dlqTopics {
        lag, err := m.getConsumerGroupLag(ctx, topic)
        if err != nil {
            continue
        }

        dlqDepthGauge.WithLabelValues(topic).Set(float64(lag))

        if lag > m.config.AlertThreshold {
            slog.WarnContext(ctx, "DLQ depth exceeds threshold",
                slog.String("topic", topic),
                slog.Int64("depth", lag),
                slog.Int64("threshold", m.config.AlertThreshold),
            )
        }
    }
}
```

---

## 19. Cloud Native Debugging: Kubernetes Deep Dive

### The Kubernetes Debugging Toolkit

#### Pod-Level Debugging

```bash
# Inspect pod status and events — always start here
kubectl describe pod <pod-name> -n <namespace>
# Pay attention to:
# - Events section: scheduling failures, image pull errors, probe failures
# - Conditions: PodScheduled, PodInitialized, ContainersReady, Ready
# - Container states: Waiting/Reason, Running/StartedAt, Terminated/ExitCode

# Get logs
kubectl logs <pod-name> -n <namespace>
kubectl logs <pod-name> -n <namespace> --previous  # Logs from crashed container
kubectl logs <pod-name> -n <namespace> -c <container>  # Multi-container pod
kubectl logs -l app=order-service -n <namespace> --tail=100  # All pods matching label

# Stream logs from multiple pods simultaneously
kubectl logs -l app=order-service -n <namespace> --follow --prefix

# Execute commands inside a running container
kubectl exec -it <pod-name> -n <namespace> -- bash

# Debug a crashed/non-starting container with ephemeral debug container (K8s 1.23+)
# This creates a new container in the pod's namespaces without modifying the pod spec
kubectl debug -it <pod-name> \
  --image=nicolaka/netshoot \
  --target=<container-name> \
  -n <namespace>

# Copy files from a pod (for post-mortem analysis)
kubectl cp <pod-name>:/tmp/heapdump.hprof ./heapdump.hprof -n <namespace>

# Port-forward to access internal service endpoints (for pprof, metrics, etc.)
kubectl port-forward pod/<pod-name> 6060:6060 -n <namespace>
# Now access http://localhost:6060/debug/pprof/goroutine
```

#### Resource and Scheduling Debugging

```bash
# Check resource requests/limits and actual usage
kubectl top pods -n <namespace>
kubectl top nodes

# Find pods that are OOM killed
kubectl get pods -n <namespace> -o json | \
  jq '.items[] | select(.status.containerStatuses[]?.lastState.terminated.reason == "OOMKilled") | .metadata.name'

# Check if CPU throttling is causing latency
# Get the container's cgroup path from inside the pod, then:
kubectl exec -it <pod> -- cat /sys/fs/cgroup/cpu/cpu.stat
# Look for: throttled_time > 0

# Node pressure conditions
kubectl describe node <node-name> | grep -A 5 "Conditions:"
# MemoryPressure, DiskPressure, PIDPressure — any True = problems

# Check evictions
kubectl get events --field-selector reason=Evicted -n <namespace>

# Pod pending debug
kubectl describe pod <pending-pod>
# Common reasons:
# "Insufficient cpu" — no node has enough CPU
# "node(s) had untolerated taint" — nodes have taints pod doesn't tolerate
# "pod has unbound immediate PersistentVolumeClaims" — PVC not bound

# Check scheduler events
kubectl get events --field-selector reason=FailedScheduling -n <namespace>
```

#### Kubernetes Service and Networking Debugging

```bash
# Verify service selectors match pod labels
kubectl get service <svc> -n <namespace> -o yaml | grep -A 5 selector
kubectl get pods -n <namespace> --show-labels | grep <relevant-label>

# Check endpoints (if empty, selector doesn't match any pods)
kubectl get endpoints <svc> -n <namespace>
kubectl describe endpoints <svc> -n <namespace>

# Test service DNS resolution
kubectl run dns-test --image=busybox:1.28 --rm -it --restart=Never -- \
  nslookup <service>.<namespace>.svc.cluster.local

# Test service connectivity
kubectl run curl-test --image=curlimages/curl --rm -it --restart=Never -- \
  curl -v http://<service>.<namespace>.svc.cluster.local:8080/health

# Check kube-proxy rules for a service
kubectl -n kube-system get pods -l k8s-app=kube-proxy
iptables -t nat -L KUBE-SERVICES | grep <service-name>

# Trace packet path for Kubernetes Services (iptables-based routing)
# When a pod connects to a ClusterIP, iptables DNAT rewrites to a real pod IP
iptables -t nat -L KUBE-SVC-<hash> -n -v
```

#### CrashLoopBackOff Investigation

```bash
# Get logs from the crashing container
kubectl logs <pod> --previous

# Check exit code
kubectl get pod <pod> -o json | jq '.status.containerStatuses[].lastState.terminated'
# Exit code meanings:
# 0 = clean exit (but container should stay running — missing CMD?)
# 1 = application error
# 137 = SIGKILL (OOM kill: 128 + 9)
# 139 = SIGSEGV (segfault: 128 + 11)
# 143 = SIGTERM (graceful shutdown: 128 + 15)
# 255 = unspecified error

# Debug interactively — override entrypoint
kubectl run debug-pod --image=<your-image> \
  --rm -it \
  --command -- /bin/sh
# Or override the crashing pod's command to prevent crash:
# Add to deployment spec:
# command: ["sleep", "infinity"]
```

#### Kubernetes RBAC Debugging

```bash
# Check if a service account can perform an action
kubectl auth can-i get pods \
  --as=system:serviceaccount:<namespace>:<serviceaccount> \
  -n <namespace>

# List all rules for a role
kubectl describe role <role-name> -n <namespace>
kubectl describe clusterrole <role-name>

# Find which roles are bound to a service account
kubectl get rolebindings,clusterrolebindings -A -o json | \
  jq '.items[] | select(.subjects[]? | select(.name == "<serviceaccount>" and .namespace == "<namespace>"))'

# Audit log: find who made which API calls
# Configure kube-apiserver with --audit-log-path and audit policy
# Then query the audit log for suspicious or failing operations
grep '"code":403' /var/log/kubernetes/audit.log | jq '.user.username, .requestURI'
```

### Kubernetes Resource Limits and QoS Classes

Understanding QoS classes is essential for debugging unexpected pod evictions and scheduling failures.

```yaml
# QoS Classes:
#
# Guaranteed: requests == limits for ALL containers (both CPU and memory)
# → Highest priority, never throttled or evicted due to resource pressure
# → Use for: latency-sensitive production services
#
# Burstable: at least one container has requests != limits
# → Can burst above request, evicted under memory pressure if above requests
# → Use for: most production workloads
#
# BestEffort: no requests or limits set
# → First evicted under any resource pressure
# → Use for: batch jobs, non-critical background work

apiVersion: v1
kind: Pod
spec:
  containers:
  - name: order-service
    resources:
      requests:
        cpu: "500m"      # 0.5 CPU cores — guaranteed scheduling
        memory: "512Mi"  # guaranteed memory
      limits:
        cpu: "1000m"     # 1 CPU core — can burst, but will be throttled above this
        memory: "512Mi"  # Same as request → Guaranteed QoS for memory
        # Note: CPU limit causes CPU throttling (not eviction)
        # Memory limit causes OOM kill (kernel kills the container)
```

---

## 20. Service Mesh Debugging: Istio, Linkerd, Cilium

### Service Mesh Architecture

A service mesh intercepts all service-to-service communication via sidecar proxies (Envoy in Istio, micro-proxy in Linkerd). This provides:
- Mutual TLS (mTLS) automatically
- Traffic management (retries, circuit breaking, traffic shifting)
- Observability (metrics, traces from the proxy layer)
- Policy enforcement (authorization policies, rate limiting)

The sidecar creates an **additional failure surface**: a correctly written service can fail due to a misconfigured mesh policy, a proxy crash, or a certificate rotation failure.

### Istio Debugging

```bash
# Check if Envoy sidecar is injected and running
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[*].name}'
# Should include "istio-proxy"

# Check Envoy proxy status
istioctl proxy-status

# Analyze configuration for a pod — shows all Istio configuration applied
istioctl analyze -n <namespace>

# Debug Envoy configuration for a specific pod
# View all clusters (upstream services) Envoy knows about
istioctl proxy-config cluster <pod-name>.<namespace>

# View all listeners (ports Envoy is listening on)
istioctl proxy-config listener <pod-name>.<namespace>

# View all routes
istioctl proxy-config route <pod-name>.<namespace>

# View endpoints (actual pod IPs for each upstream service)
istioctl proxy-config endpoint <pod-name>.<namespace>

# Check if mTLS is properly enforced
istioctl authn tls-check <pod-name>.<namespace> <service>.<namespace>.svc.cluster.local

# Increase Envoy log level for a specific component temporarily
# NEVER do this for extended periods — volume is extremely high
kubectl exec <pod-name> -n <namespace> -c istio-proxy -- \
  curl -s -X POST http://localhost:15000/logging?http=debug

# Access Envoy admin API (port 15000 is the admin port)
kubectl port-forward <pod-name> 15000:15000 -n <namespace>
# Then: curl http://localhost:15000/stats | grep "upstream_rq_retry"
# Critical stats:
#   upstream_rq_retry: retry count
#   upstream_rq_timeout: timeout count
#   upstream_cx_connect_fail: connection failure count
#   circuit_breakers.default.rq_open: circuit breaker state

# Istio access logs — every request through the mesh
kubectl logs <pod-name> -n <namespace> -c istio-proxy | tail -100

# Kiali: Istio's graph-based service mesh visualization
kubectl port-forward svc/kiali 20001:20001 -n istio-system
```

### Istio AuthorizationPolicy Debugging

Authorization policy failures are a common source of mysterious 403 errors.

```yaml
# authorization-policy.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: order-service-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: order-service
  action: ALLOW
  rules:
  - from:
    - source:
        # Only allow calls from services with these identities (SPIFFE)
        principals:
          - "cluster.local/ns/production/sa/payment-service"
          - "cluster.local/ns/production/sa/inventory-service"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/orders*"]
```

```bash
# Debug: why is a request getting 403?
# 1. Check the authorization policy covers the source
kubectl get authorizationpolicy -A

# 2. Enable RBAC debug logging in the target pod's Envoy
kubectl exec <target-pod> -n production -c istio-proxy -- \
  curl -s -X POST http://localhost:15000/logging?rbac=debug

# 3. Check Envoy logs for RBAC deny reason
kubectl logs <target-pod> -n production -c istio-proxy | grep "rbac"

# 4. Verify the source service account matches the policy
kubectl get pod <source-pod> -n production -o yaml | grep serviceAccountName
```

### Cilium Network Policy Debugging

```bash
# Cilium is a CNI plugin that uses eBPF for network policy enforcement.
# Policy violations are dropped silently at the kernel level — no logs by default.

# Check Cilium agent status on a node
kubectl -n kube-system exec -it ds/cilium -- cilium status

# View all active network policies
kubectl -n kube-system exec -it ds/cilium -- cilium policy get

# Test connectivity: will this traffic be allowed?
kubectl -n kube-system exec -it ds/cilium -- \
  cilium policy trace \
  --src-k8s-pod production/order-service-abc123 \
  --dst-k8s-pod production/payment-service-xyz456 \
  --dport 8080/TCP

# Monitor dropped packets in real time (shows reason for each drop)
kubectl -n kube-system exec -it ds/cilium -- \
  cilium monitor --type drop

# View endpoint details (each pod is a Cilium endpoint)
kubectl -n kube-system exec -it ds/cilium -- cilium endpoint list
kubectl -n kube-system exec -it ds/cilium -- cilium endpoint get <endpoint-id>

# Show Cilium policy verdicts for a specific endpoint
kubectl -n kube-system exec -it ds/cilium -- \
  cilium monitor -t policy-verdict --related-to <endpoint-id>
```

---

## 21. Cloud Security: Debugging Auth, mTLS, and Policy Failures

### mTLS Certificate Debugging

```bash
# Inspect a TLS certificate
openssl x509 -in /path/to/cert.pem -text -noout

# Check certificate chain validity
openssl verify -CAfile ca-bundle.crt server.crt

# Test TLS handshake to a service
openssl s_client -connect service.internal:8443 \
  -CAfile ca.crt \
  -cert client.crt \
  -key client.key

# Check certificate expiry (in production: alert when < 30 days from expiry)
openssl x509 -in /path/to/cert.pem -noout -enddate

# Scan service's TLS configuration
nmap --script ssl-enum-ciphers -p 8443 service.internal

# Debug TLS with curl
curl -v --cacert ca.crt \
        --cert client.crt \
        --key client.key \
        https://service.internal:8443/health 2>&1 | grep -E "TLS|SSL|certificate|error"

# Common mTLS errors and causes:
# SSL_ERROR_HANDSHAKE_FAILURE_ALERT → Client cert not sent or wrong CA
# certificate verify failed → Server cert signed by unknown CA
# SSL_ERROR_NO_CYPHER_OVERLAP → TLS version/cipher mismatch (update TLS config)
# certificate has expired → Auto-rotate certs with cert-manager
```

### JWT Debugging

```bash
# Decode a JWT without verification (for debugging only — never trust unverified JWTs)
echo -n "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyXzEyMyJ9.signature" \
  | cut -d'.' -f2 \
  | base64 --decode 2>/dev/null \
  | python3 -m json.tool

# Common JWT debugging issues:
# 1. Clock skew: "nbf" or "exp" check fails due to server clock drift
#    Fix: allow 30-60 second leeway in JWT validation
# 2. Wrong audience: "aud" claim doesn't match what the service expects
#    Fix: ensure token is issued for the correct service
# 3. Wrong issuer: "iss" claim doesn't match JWKS endpoint base URL
# 4. Token in wrong header: Authorization: "JWT token" vs "Bearer token"
# 5. JWKS caching: fetching rotated keys — cache JWKS but also allow rotation
```

```go
// jwt_validator.go — robust JWT validation with debugging
package auth

import (
    "context"
    "fmt"
    "time"

    "github.com/golang-jwt/jwt/v5"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/trace"
)

type ValidationError struct {
    Reason  string
    Details map[string]interface{}
}

func (e *ValidationError) Error() string {
    return fmt.Sprintf("JWT validation failed: %s", e.Reason)
}

func ValidateJWT(ctx context.Context, tokenString string, validator *JWTValidator) (*Claims, error) {
    span := trace.SpanFromContext(ctx)

    token, err := jwt.ParseWithClaims(tokenString, &Claims{}, validator.keyFunc,
        jwt.WithAudience(validator.expectedAudience),
        jwt.WithIssuer(validator.expectedIssuer),
        jwt.WithLeeway(30*time.Second), // Allow 30s clock skew
        jwt.WithValidMethods([]string{"RS256", "ES256"}), // Only allow secure algorithms
        // NEVER allow "none" algorithm — classic JWT security bypass
    )
    if err != nil {
        // Emit span attributes for JWT errors — enables filtering in trace backend
        // "find all requests that failed due to expired tokens this hour"
        span.SetAttributes(
            attribute.String("auth.error_type", classifyJWTError(err)),
            attribute.Bool("auth.success", false),
        )

        // Log enough detail to debug, but never log the token itself
        slog.WarnContext(ctx, "JWT validation failed",
            slog.String("error_type", classifyJWTError(err)),
            slog.String("error", err.Error()),
            // Don't log the token — it's a credential
        )

        return nil, &ValidationError{
            Reason:  classifyJWTError(err),
            Details: extractJWTErrorDetails(err),
        }
    }

    claims, ok := token.Claims.(*Claims)
    if !ok || !token.Valid {
        return nil, &ValidationError{Reason: "invalid_claims"}
    }

    span.SetAttributes(
        attribute.Bool("auth.success", true),
        attribute.String("auth.subject", claims.Subject),
        attribute.StringSlice("auth.scopes", claims.Scopes),
    )

    return claims, nil
}

func classifyJWTError(err error) string {
    switch {
    case errors.Is(err, jwt.ErrTokenExpired):
        return "token_expired"
    case errors.Is(err, jwt.ErrTokenNotValidYet):
        return "token_not_yet_valid"
    case errors.Is(err, jwt.ErrTokenSignatureInvalid):
        return "invalid_signature"
    case errors.Is(err, jwt.ErrTokenMalformed):
        return "malformed_token"
    case errors.Is(err, jwt.ErrTokenUnverifiable):
        return "unverifiable_token" // JWKS fetch failed
    default:
        return "unknown_error"
    }
}
```

### Secrets Management Debugging

```bash
# Kubernetes Secrets debugging
# Check if a secret exists and has the expected keys (never print values in logs)
kubectl get secret <secret-name> -n <namespace> -o jsonpath='{.data}' | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(list(d.keys()))"

# Check if a secret is correctly mounted in a pod
kubectl exec <pod> -- env | grep -i "password\|token\|key\|secret" | \
  sed 's/=.*/=REDACTED/'  # Show variable names but not values

# Check Vault-injected secrets (HashiCorp Vault with agent injector)
kubectl logs <pod> -c vault-agent-init
kubectl logs <pod> -c vault-agent

# Detect secret leakage in logs — should return nothing
kubectl logs <pod> -n <namespace> | \
  grep -E "password=|secret=|token=|apikey=|authorization:" | \
  head -5

# Check cert-manager certificate status
kubectl describe certificate <cert-name> -n <namespace>
kubectl get certificaterequest -n <namespace>
# CertificateRequest Failed → check ACME challenge, DNS records, or CA config
```

### OPA/Gatekeeper Policy Debugging

```bash
# OPA Gatekeeper enforces admission policies in Kubernetes.
# When a deployment fails, it may be due to a policy violation.

# Check for constraint violations
kubectl get constraints -A
kubectl describe constraint <constraint-name>

# Check why a deployment was rejected
kubectl get events --field-selector reason=FailedCreate -n <namespace>

# List all constraint templates
kubectl get constrainttemplate

# Test a policy locally without Kubernetes
opa eval \
  --input input.json \
  --data policy.rego \
  'data.kubernetes.admission.deny'

# Check Gatekeeper audit results (violations on existing resources)
kubectl get constrainttemplate -A
kubectl get <constraint-kind> -A -o json | jq '.items[].status.violations'
```

---

## 22. Multi-Cloud and Hybrid Debugging Challenges

### Cross-Cloud Latency and Routing

```bash
# Measure latency between cloud regions with realistic payloads
for region in us-east-1 eu-west-1 ap-southeast-1; do
  echo "Testing latency to $region:"
  curl -o /dev/null -s -w "Connect: %{time_connect}s TTFB: %{time_starttransfer}s Total: %{time_total}s\n" \
    https://api.${region}.myservice.com/health
done

# Check BGP routing paths between cloud providers
traceroute -T -p 443 api.service.com  # TCP traceroute (bypasses ICMP blocks)

# Diagnose asymmetric routing (packets take different paths in each direction)
# This causes TCP performance issues and confusing latency measurements
mtr --report -T -P 443 api.service.com > forward_path.txt
# Ask provider to traceroute from their end for reverse path

# AWS: check VPC flow logs for dropped packets
# Logs format: version account-id interface-id srcaddr dstaddr srcport dstport protocol packets bytes start end action log-status
grep "REJECT" vpc-flow-logs.txt | awk '{print $4, $5, $8, $13}' | sort | uniq -c | sort -rn
```

### Service Mesh Federation

In multi-cluster deployments, service meshes must federate trust to allow mTLS across clusters.

```yaml
# Istio multi-cluster debugging
# Check if remote cluster is reachable
kubectl get secret istio-remote-secret-<cluster-name> -n istio-system

# Verify ServiceEntry for remote services
kubectl get serviceentry -n <namespace>

# Check that endpoint discovery is working for remote services
istioctl proxy-config endpoint <pod>.<namespace> | grep <remote-service>

# Debug: remote service endpoints should show IPs from the remote cluster
# If empty: IstioOperator federation config or remote secret is wrong
```

---

## 23. Chaos Engineering: Proactive Debugging Before Production

Chaos engineering is the practice of intentionally injecting failures into a system to discover weaknesses before production incidents do.

### Principles

1. **Form a hypothesis**: "If the payment service becomes unavailable, orders will queue and retry gracefully, not fail"
2. **Minimize blast radius**: Start with a small percentage of traffic or a single instance
3. **Observe with metrics**: Confirm your observability captures the failure correctly
4. **Roll back quickly**: Have a kill switch for every experiment
5. **Run in production**: Staging doesn't have the same traffic patterns, dependencies, and data

### Chaos Mesh: Kubernetes-Native Chaos Engineering

```yaml
# Inject network latency into a specific service
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: payment-service-latency
  namespace: production
spec:
  action: delay
  mode: percent
  value: "20"       # Affect 20% of pods
  selector:
    namespaces: ["production"]
    labelSelectors:
      app: payment-service
  delay:
    latency: "500ms"
    correlation: "25"   # 25% correlation between consecutive delays (more realistic)
    jitter: "100ms"
  duration: "5m"        # Auto-stop after 5 minutes
  scheduler:
    cron: "@every 1h"   # Run hourly (for resilience validation)

---
# Simulate pod failure (OOM kill scenario)
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: inventory-pod-kill
  namespace: production
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces: ["production"]
    labelSelectors:
      app: inventory-service
  scheduler:
    cron: "0 */6 * * *"  # Every 6 hours

---
# CPU stress to trigger throttling
apiVersion: chaos-mesh.org/v1alpha1
kind: StressChaos
metadata:
  name: order-service-cpu-stress
  namespace: staging
spec:
  mode: one
  selector:
    namespaces: ["staging"]
    labelSelectors:
      app: order-service
  stressors:
    cpu:
      workers: 2      # 2 CPU-intensive goroutines
      load: 80        # 80% CPU load
  duration: "2m"
```

### litmus chaos: Cloud-Native Fault Injection in Go

```go
// Custom chaos experiment: test database connection pool exhaustion
// Run this experiment to verify your service handles pool exhaustion gracefully

package chaos

import (
    "context"
    "database/sql"
    "sync"
    "time"
)

// ExhaustDBPool opens and holds all connections in the pool for a duration.
// Purpose: verify that your service returns 503 (not 500) when pool is exhausted,
//          that circuit breakers trip correctly, and that logs show useful context.
func ExhaustDBPool(ctx context.Context, db *sql.DB, duration time.Duration) error {
    stats := db.Stats()
    maxConns := stats.MaxOpenConnections
    if maxConns <= 0 {
        maxConns = 25 // Default assumption
    }

    held := make([]*sql.Conn, 0, maxConns)
    var mu sync.Mutex

    // Acquire all connections
    for i := 0; i < maxConns; i++ {
        conn, err := db.Conn(ctx)
        if err != nil {
            break
        }
        // Begin a transaction to hold the connection
        if _, err := conn.ExecContext(ctx, "BEGIN"); err != nil {
            conn.Close()
            break
        }
        mu.Lock()
        held = append(held, conn)
        mu.Unlock()
    }

    // Hold for the specified duration
    select {
    case <-time.After(duration):
    case <-ctx.Done():
    }

    // Release all connections
    mu.Lock()
    defer mu.Unlock()
    for _, conn := range held {
        conn.ExecContext(context.Background(), "ROLLBACK")
        conn.Close()
    }

    return nil
}
```

---

## 24. Production Debugging Workflows

### The Structured Debugging Process

When a production incident occurs, resist the urge to immediately start changing things. Use this structured process:

#### Phase 1: Triage (0-5 minutes)

**Objective**: Establish scope and severity. Is this affecting all users or some? Is it getting worse or stable?

```
Questions to answer:
1. Which services are in error state? (Check service RED metrics dashboard)
2. When did it start? (Correlate with deployments, config changes, traffic changes)
3. What is the customer impact? (Error rate × active users)
4. Is it trending better or worse?
5. Does rolling back the last deployment fix it?
```

#### Phase 2: Hypothesis Formation (5-10 minutes)

Form 2-3 specific, falsifiable hypotheses. Bad hypothesis: "something is broken." Good hypothesis: "the payment service is timing out because the database connection pool is exhausted."

Each hypothesis should suggest a specific metric or log query that would confirm or deny it.

#### Phase 3: Investigation (10-60 minutes)

```bash
# Step 1: Identify affected services from the error budget / error rate dashboard
# Step 2: Find the root-cause service (trace high-error-rate spans to their origin)
# Step 3: Examine logs at the error time for that service

# Practical query sequence in a typical Grafana/Loki/Tempo stack:

# 1. Find error rate spike in Grafana (Prometheus)
# Query: sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service)

# 2. Jump from metric to trace using exemplar link
# The exemplar embeds a trace_id in the histogram bucket that was slow/erroring

# 3. In Jaeger/Tempo: open the trace
# → Find the span with status=error
# → Look at span attributes: error.code, error.message, db.statement, etc.
# → Find which service generated the error

# 4. In Loki: search logs for that service at that time with the trace_id
# LogQL: {app="payment-service"} |= "4bf92f3577b34da6a3ce929d0e0e4736"

# 5. In the logs: find the error message, the stack trace
# 6. Form a conclusion about root cause
```

#### Phase 4: Mitigation (time-critical)

Mitigation ≠ fix. It's stopping the bleeding:
- Roll back the deployment
- Redirect traffic away from the failing region
- Increase resource limits
- Disable the feature flag
- Scale up the service

#### Phase 5: Fix

After the incident is mitigated and pressure is off, do the actual root cause fix, with a proper test.

#### Phase 6: Post-Mortem

See [Section 27](#27-post-mortem-culture-and-failure-documentation).

### Runbooks as Code

```markdown
# Runbook: Payment Service High Error Rate

## Symptoms
- payment-service HTTP 5xx rate > 1%
- Alert: `PaymentServiceHighErrorRate`

## Investigation Steps

### Step 1: Check the trace
1. Open Grafana → Payment Service dashboard
2. Click the error spike exemplar → opens Jaeger trace
3. Identify the failing span

### Step 2: If span is `db.query` (database issue)
```bash
kubectl exec -it $(kubectl get pod -l app=payment-service -o name | head -1) \
  -- sh -c 'PGPASSWORD=$DB_PASSWORD psql -h $DB_HOST -U $DB_USER -d $DB_NAME \
  -c "SELECT pid, now()-xact_start as age, state, query FROM pg_stat_activity WHERE state != '\''idle'\'' ORDER BY age DESC LIMIT 10;"'
```
- If you see long-running transactions: check for deadlocks (pg_stat_locks)
- If connection count is high: check pool size vs. max_connections

### Step 3: If span is `http.client` (upstream dependency issue)
Check the upstream service's health: `kubectl top pod -l app=<upstream-service>`

## Escalation
- After 10 minutes without progress: page backend on-call lead
- After 20 minutes without mitigation: invoke rollback procedure

## Rollback Procedure
```bash
kubectl rollout undo deployment/payment-service -n production
kubectl rollout status deployment/payment-service -n production
```
```

---

## 25. Clock Drift, Time-Ordering, and Causality

### Why Clock Drift Matters

Each node in a Kubernetes cluster has its own hardware clock. Even with NTP synchronization, clocks can drift by 10-200ms between nodes. This causes:

- **Log ordering confusion**: Log lines appear in wrong order when aggregated
- **Timeout bugs**: Service A and B use local time for timeout calculation; drift causes timeout before the actual deadline
- **Distributed locking bugs**: Redis SETNX with TTL on two different nodes can create split-brain if clocks differ
- **Event ordering failures**: An event timestamped before its cause (due to clock drift) confuses causality-dependent logic

### Logical Clocks vs. Physical Clocks

**Lamport Timestamps**: A logical clock that guarantees causal ordering. Each message increments the sender's counter; the receiver takes max(sender, receiver) + 1.

```go
// lamport.go — Lamport clock for ordering events across services
type LamportClock struct {
    mu    sync.Mutex
    value uint64
}

func (c *LamportClock) Tick() uint64 {
    c.mu.Lock()
    defer c.mu.Unlock()
    c.value++
    return c.value
}

// Called when receiving a message with a Lamport timestamp
func (c *LamportClock) Update(received uint64) uint64 {
    c.mu.Lock()
    defer c.mu.Unlock()
    if received > c.value {
        c.value = received
    }
    c.value++ // Always increment on receive
    return c.value
}
```

**Vector Clocks**: Extend Lamport clocks to detect concurrent events. Each node maintains a vector of counters, one per node. Two events are concurrent if neither's vector "happens-before" the other's.

### NTP and PTP in Kubernetes

```bash
# Check NTP synchronization status on a node
timedatectl show --property=NTPSynchronized
chronyc tracking   # If using chrony

# Check clock offset between nodes (requires network access)
ntpdate -q <ntp-server>

# For high-precision requirements (financial services, distributed databases):
# Use PTP (Precision Time Protocol) for sub-microsecond synchronization
# Hardware: requires PTP-capable NICs and switches
# AWS: EC2 Nitro instances support PTP natively
# GKE: GKE nodes support PTP on supported machine types

# Configure Kubernetes to sync with hardware clock via PTP
# This is often done at the node level via the linuxptp daemonset
```

---

## 26. Reproducing Production Failures Locally

### Traffic Capture and Replay

```bash
# GoReplay: capture and replay production HTTP traffic
# 1. Capture traffic from production
goreplay \
  --input-raw :8080 \
  --output-file requests.gor \
  --output-file-append

# 2. Replay against a local/staging instance at reduced rate
goreplay \
  --input-file requests.gor \
  --output-http http://localhost:8081 \
  --output-http-stats \
  --output-http-timeout 5s

# 3. Shadow traffic: send copies of production traffic to staging simultaneously
goreplay \
  --input-raw :8080 \
  --output-http http://localhost:8080 \
  --output-http http://staging-service:8080 \
  --split-output true

# tcpdump + tcpreplay: lower-level traffic replay
sudo tcpdump -i eth0 -w capture.pcap port 8080
# Edit/anonymize capture.pcap if needed
sudo tcpreplay --intf1=lo --multiplier=0.1 capture.pcap  # 10% speed
```

### Docker Compose for Multi-Service Local Debugging

```yaml
# docker-compose.debug.yml — minimal reproduction of production failure
version: '3.8'

services:
  order-service:
    build: ./services/order
    environment:
      - LOG_LEVEL=debug
      - OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4317
      - DB_HOST=postgres
      - PAYMENT_SERVICE_URL=http://payment-service:8080
    depends_on: [postgres, kafka, payment-service, otel-collector]
    # Enable pprof
    ports:
      - "6060:6060"

  payment-service:
    build: ./services/payment
    environment:
      - FAILURE_RATE=0.3  # Inject 30% failure rate for debugging
      - LOG_LEVEL=debug
    ports:
      - "6061:6060"

  postgres:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: debug
    # Enable slow query logging
    command: >
      postgres
      -c log_min_duration_statement=100
      -c log_connections=on
      -c log_lock_waits=on
      -c deadlock_timeout=1s

  kafka:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
    
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.89.0
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml
    command: --config /etc/otel/config.yaml
    ports:
      - "4317:4317"
      - "16686:16686"  # Jaeger UI (when using jaeger exporter)

  # Toxiproxy: inject network failures programmatically
  toxiproxy:
    image: shopify/toxiproxy
    ports:
      - "8474:8474"  # Admin API
      - "8080:8080"  # Proxied payment-service
```

```bash
# Toxiproxy: programmatic network failure injection
# After starting docker-compose, configure toxiproxy:

# Create proxy: all traffic to payment-service goes through toxiproxy
curl -X POST http://localhost:8474/proxies \
  -H "Content-Type: application/json" \
  -d '{"name":"payment-service","listen":"0.0.0.0:8080","upstream":"payment-service:8080"}'

# Add 500ms latency with 100ms jitter
curl -X POST http://localhost:8474/proxies/payment-service/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"latency","type":"latency","attributes":{"latency":500,"jitter":100}}'

# Simulate 20% packet loss
curl -X POST http://localhost:8474/proxies/payment-service/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"packet_loss","type":"limit_data","attributes":{"bytes":0}}'

# Cut the connection completely (simulate full service outage)
curl -X POST http://localhost:8474/proxies/payment-service/toxics \
  -H "Content-Type: application/json" \
  -d '{"name":"down","type":"timeout","attributes":{"timeout":0}}'

# Remove toxic to restore normal operation
curl -X DELETE http://localhost:8474/proxies/payment-service/toxics/latency
```

---

## 27. Post-Mortem Culture and Failure Documentation

### Blameless Post-Mortems

A blameless post-mortem attributes failures to **systems and processes**, not individuals. The goal is learning and systemic improvement, not accountability theater.

Key principles:
- **Assume good intent**: Everyone involved was doing their best with the information and tools available at the time
- **Find systemic causes**: "Why did the system allow this to happen?" not "who made this mistake?"
- **Timeline reconstruction**: Build a factual, chronological timeline before forming conclusions
- **Action items**: Every learning should produce a specific, assigned, time-bounded action

### Post-Mortem Template

```markdown
# Incident Post-Mortem: [Brief title]
**Date**: YYYY-MM-DD
**Severity**: SEV-1 (Complete outage) / SEV-2 (Partial) / SEV-3 (Degraded)
**Duration**: HH:MM
**Impact**: X% of users affected; Y requests failed; $Z revenue impact

## Summary
[2-3 sentence description of what happened, what the impact was, and what resolved it]

## Timeline (all times UTC)
| Time  | Event |
|-------|-------|
| 14:23 | Alert fired: PaymentServiceHighErrorRate > 1% |
| 14:25 | On-call engineer acknowledged |
| 14:31 | Identified payment-service error in traces — DB connection pool exhausted |
| 14:38 | Root cause identified: new code change increased query count 3x without pool resize |
| 14:40 | Mitigation: rolled back deployment |
| 14:42 | Error rate returned to normal |
| 14:50 | Confirmed no data corruption |

## Root Cause Analysis
[Use the "5 Whys" technique — drill down until you reach a systemic cause]

Why did the service fail?
→ Database connection pool was exhausted

Why was the pool exhausted?
→ Each request now makes 3x more queries than before

Why wasn't this caught in testing?
→ Load tests use 10% of production query volume

Why do load tests use 10% volume?
→ Staging environment has limited DB connections and would OOM at full load

Why does staging have limited DB?
→ Cost. No budget approval process for staging DB scaling.

**Root Cause**: Staging environment resources are insufficient to validate production-equivalent load patterns. This is a systemic gap.

## Contributing Factors
- No query count metrics were tracked pre/post deployment
- No performance regression test in CI
- Code review didn't catch the N+1 query pattern introduced

## What Went Well
- Alert fired within 3 minutes of impact
- On-call was able to identify root cause within 8 minutes using traces
- Rollback took < 2 minutes and was effective

## Action Items
| Action | Owner | Due Date | Priority |
|--------|-------|----------|----------|
| Add query count metric per endpoint | @engineer-a | 2024-12-01 | P1 |
| Add N+1 query detection to CI (nplusone, sqlcommenter) | @engineer-b | 2024-12-07 | P1 |
| Document DB pool sizing runbook | @engineer-c | 2024-12-15 | P2 |
| Propose staging resource parity budget | @manager | 2025-01-01 | P2 |
```

---

## 28. Tooling Reference

### Observability Stack

| Tool | Purpose | Best For |
|------|---------|----------|
| Jaeger | Distributed tracing backend | Self-hosted, open source |
| Tempo | Distributed tracing backend | Grafana ecosystem, object storage |
| Zipkin | Distributed tracing backend | Lightweight, simple |
| Prometheus | Metrics collection and storage | Short-term metrics, alerting |
| Thanos / Cortex | Prometheus at scale | Multi-cluster, long-term storage |
| Loki | Log aggregation | Grafana ecosystem, log queries |
| Elasticsearch / OpenSearch | Log aggregation | Full-text search, complex queries |
| Grafana | Dashboards and visualization | All of the above |
| OpenTelemetry Collector | Telemetry pipeline | Vendor-agnostic collection |
| Honeycomb | High-cardinality observability | Complex debugging, SaaS |
| Datadog | Full observability suite | Enterprise, SaaS |
| Pyroscope | Continuous profiling | CPU/memory profiling |

### Kubernetes Debugging Tools

| Tool | Purpose |
|------|---------|
| `kubectl` | Core K8s CLI |
| `k9s` | Terminal UI for K8s |
| `lens` | Desktop GUI for K8s |
| `stern` | Multi-pod log tailing |
| `kubectx/kubens` | Context and namespace switching |
| `kube-capacity` | Resource usage summary |
| `popeye` | K8s cluster sanitizer |
| `kube-score` | Static analysis of K8s manifests |
| `istioctl` | Istio CLI |
| `cilium CLI` | Cilium network debugging |

### Network Debugging Tools

| Tool | Purpose |
|------|---------|
| `tcpdump` | Packet capture |
| `Wireshark` | Packet analysis GUI |
| `mtr` | Network path analysis |
| `nmap` | Port/service scanning |
| `curl -v` | HTTP debugging |
| `grpcurl` | gRPC debugging |
| `Toxiproxy` | Network fault injection |
| `tc` (traffic control) | Kernel-level traffic shaping |

### Language-Specific Tools

| Language | Profiling | Debugging | Race Detection |
|----------|-----------|-----------|----------------|
| Go | pprof, trace | Delve (dlv) | -race flag |
| Rust | cargo flamegraph, perf | rust-gdb, LLDB, tokio-console | Compiler (borrow checker) |
| C/C++ | Valgrind/callgrind, perf | GDB | ASan, TSan |

### Chaos Engineering

| Tool | Scope |
|------|-------|
| Chaos Mesh | Kubernetes-native (network, pod, CPU, IO) |
| LitmusChaos | Kubernetes-native, GitOps |
| Gremlin | Enterprise SaaS |
| Toxiproxy | Network-level (local + K8s) |
| tc (Linux) | Kernel-level network shaping |
| fault | Go fault injection library |

---

## Conclusion

Debugging microservices is fundamentally different from debugging monolithic applications because it requires reasoning about an entire distributed system — not just one process. The discipline combines:

- **Systems thinking**: Understanding failure modes, cascades, and emergent behavior
- **Kernel knowledge**: Understanding how the OS actually runs your code
- **Observability engineering**: Designing systems to be debuggable from the start
- **Language internals**: Go's runtime, Rust's ownership model, C's memory model
- **Cloud native operations**: Kubernetes, service mesh, and cloud provider primitives

The most important insight is that **observability is not an afterthought**. It must be designed in from day one. A service that emits well-structured traces, metrics, and logs with proper context propagation can be debugged in minutes. A service without them can take days.

Invest in:
1. **Uniform instrumentation standards** across all services (OTel)
2. **Correlation IDs** flowing through every layer
3. **Exemplars** linking metrics to traces
4. **Health endpoints** that reflect real readiness, not just liveness
5. **Runbooks** that encode debugging knowledge
6. **Blameless post-mortems** that generate systemic improvements

The system will fail. The question is whether you'll be able to understand why — and how quickly.

Now I'll create this comprehensive guide. This will be a very large, in-depth document covering all topics.Here's the complete guide — **28 sections**, covering every layer of the stack. Here's a structural summary of what's inside:

**Foundations**
- Distributed failure taxonomy (crash, omission, timing, Byzantine, cascade, gray failures)
- The 8 fallacies of distributed computing mapped to actual bug categories
- Observability pillars including continuous profiling and high-cardinality events

**Instrumentation (Go, Rust, C)**
- Full OTel bootstrap in all three languages — tracers, exporters, resource attribution
- Prometheus metrics with exemplars for trace correlation
- Structured logging (`slog` in Go, `tracing` crate in Rust) with trace ID injection
- C-level W3C `traceparent` header parsing/generation for infrastructure components

**Linux Kernel & eBPF**
- conntrack table exhaustion, cgroup CPU throttling, TIME_WAIT exhaustion, epoll internals
- `bpftrace` one-liners for DNS, TCP connects, slow disk I/O, context switches
- `cilium/ebpf` Go library for writing kernel probes from application code
- `BCC` tools reference (`tcpretrans`, `runqlat`, `offcputime`, `funclatency`)

**Resilience Patterns**
- Circuit breaker with OTel span annotation and state metrics
- Exponential backoff with full jitter (the correct algorithm)
- Bulkhead isolation
- Saga orchestration with compensation and structured error logging

**Cloud Native / Security**
- Kubernetes: CrashLoopBackOff, OOMKill, scheduling failures, RBAC, NetworkPolicy
- Istio/Envoy: proxy-config introspection, mTLS cert debugging, AuthorizationPolicy
- Cilium: eBPF-level policy tracing and drop monitoring
- JWT classification errors, secrets hygiene, OPA/Gatekeeper policy failures

**Operations**
- Structured production debugging workflow (triage → hypothesis → investigate → mitigate)
- Chaos Mesh YAML, Toxiproxy programmatic fault injection, GoReplay traffic replay
- Blameless post-mortem template with 5 Whys analysis
- Full tooling reference table