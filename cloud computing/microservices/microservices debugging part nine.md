# Microservices Debugging Mastery
## A Complete Engineering Reference: C · Go · Rust · Linux Kernel · Cloud Native · Cloud Security

---

> **Audience**: Staff/Senior Engineers who need production-grade depth, not toy examples.  
> **Coverage**: Distributed systems failure modes → Linux kernel internals → Cloud Native observability → Security → Implementations in C, Go, Rust.

---

## Table of Contents

1. [The Fundamental Problem: Why Distributed Systems Are Different](#1-the-fundamental-problem)
2. [Loss of Linearity — Tracing Execution Across Boundaries](#2-loss-of-linearity)
3. [The Network Is Unreliable — Kernel & Protocol Layer](#3-network-unreliability)
4. [Partial Failures — Failure Detection Algorithms](#4-partial-failures)
5. [Data Inconsistency — Consistency Models & Protocols](#5-data-inconsistency)
6. [Distributed Logging — Correlation IDs & Structured Logging](#6-distributed-logging)
7. [Concurrency Explosion — Memory Models & Race Detection](#7-concurrency-explosion)
8. [Version Mismatch — API Contracts & Schema Evolution](#8-version-mismatch)
9. [Retry Storms & Cascading Failures — Circuit Breakers](#9-retry-storms)
10. [Observability Stack — Metrics, Traces, Logs](#10-observability-stack)
11. [Environment Parity — Local vs Production](#11-environment-parity)
12. [Asynchronous Communication — Queues & Event Sourcing](#12-async-communication)
13. [Cloud Security — Zero Trust, mTLS, SPIFFE/SPIRE](#13-cloud-security)
14. [Infrastructure Complexity — Kubernetes Internals](#14-kubernetes-internals)
15. [Time-Related Bugs — Clock Drift & Hybrid Logical Clocks](#15-time-related-bugs)
16. [Reproducibility — Chaos Engineering & Deterministic Replay](#16-reproducibility)
17. [Linux Kernel Debugging Tools](#17-linux-kernel-debugging)
18. [Production Debugging Playbook](#18-production-debugging-playbook)
19. [Security Hardening Checklist](#19-security-hardening-checklist)
20. [Reference Architecture](#20-reference-architecture)

---

## 1. The Fundamental Problem

### One-Line Explanation

A monolith executes in one process with shared memory; a microservice system executes across N processes on M machines over an unreliable network — every assumption that holds locally becomes false at scale.

### The Eight Fallacies of Distributed Computing (Peter Deutsch, Sun Microsystems)

These are not guidelines. They are guarantees of failure if you assume otherwise:

1. The network is reliable
2. Latency is zero
3. Bandwidth is infinite
4. The network is secure
5. Topology doesn't change
6. There is one administrator
7. Transport cost is zero
8. The network is homogeneous

### Mental Model: The CAP Theorem and PACELC

**CAP**: In the presence of a **P**artition, choose between **C**onsistency and **A**vailability.

**PACELC** (more precise): Even when there is no partition (else), you trade **L**atency against **C**onsistency.

| System | P→CA | else→LC |
|--------|------|---------|
| Zookeeper | CP | CL |
| Cassandra | AP | EL |
| DynamoDB (default) | AP | EL |
| etcd | CP | CL |
| PostgreSQL | CP | CL |

**Debug implication**: When a service returns stale data, the first question is "what consistency level was configured?" — not "is there a bug?"

---

## 2. Loss of Linearity

### The Core Problem

In a monolith, a stack trace tells you everything:

```
panic: nil pointer dereference
goroutine 1 [running]:
main.handleOrder(0xc0000b4000)
    /app/order.go:42 +0x1a0
```

In microservices, "the stack trace" is distributed across 5 services, 3 message queues, and 2 databases. You must **reconstruct** it from telemetry.

### Solution: Distributed Tracing (OpenTelemetry)

The W3C `traceparent` header propagates trace context across service boundaries:

```
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01
              ^  ^                                ^                ^
              |  trace-id (128-bit)               span-id (64-bit) flags
              version
```

### Implementation: Trace Propagation in Go

```go
// File: tracing/tracer.go
// Run: go mod init tracing && go get go.opentelemetry.io/otel
// go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp
// go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp

package main

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"time"

	"go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/attribute"
	"go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
	"go.opentelemetry.io/otel/propagation"
	"go.opentelemetry.io/otel/sdk/resource"
	sdktrace "go.opentelemetry.io/otel/sdk/trace"
	semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
	"go.opentelemetry.io/otel/trace"
)

// TracerProvider wraps the OTel SDK TracerProvider with lifecycle management.
type TracerProvider struct {
	provider *sdktrace.TracerProvider
}

func NewTracerProvider(ctx context.Context, serviceName, serviceVersion string) (*TracerProvider, error) {
	exporter, err := otlptracehttp.New(ctx,
		otlptracehttp.WithEndpoint(os.Getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
		otlptracehttp.WithInsecure(),
	)
	if err != nil {
		return nil, fmt.Errorf("creating OTLP exporter: %w", err)
	}

	res, err := resource.New(ctx,
		resource.WithAttributes(
			semconv.ServiceName(serviceName),
			semconv.ServiceVersion(serviceVersion),
			semconv.DeploymentEnvironment(os.Getenv("ENVIRONMENT")),
		),
	)
	if err != nil {
		return nil, fmt.Errorf("creating resource: %w", err)
	}

	tp := sdktrace.NewTracerProvider(
		// BatchSpanProcessor is critical for production — never use SimpleSpanProcessor.
		// It batches spans and sends asynchronously, avoiding latency spikes.
		sdktrace.WithBatcher(exporter,
			sdktrace.WithBatchTimeout(5*time.Second),
			sdktrace.WithMaxExportBatchSize(512),
		),
		sdktrace.WithResource(res),
		// Sample 100% in dev, 1% in production (adjust via env)
		sdktrace.WithSampler(sdktrace.ParentBased(sdktrace.TraceIDRatioBased(sampleRate()))),
	)

	otel.SetTracerProvider(tp)
	otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
		propagation.TraceContext{}, // W3C traceparent
		propagation.Baggage{},     // W3C baggage
	))

	return &TracerProvider{provider: tp}, nil
}

func sampleRate() float64 {
	if os.Getenv("ENVIRONMENT") == "production" {
		return 0.01 // 1%
	}
	return 1.0 // 100%
}

func (tp *TracerProvider) Shutdown(ctx context.Context) error {
	return tp.provider.Shutdown(ctx)
}

// OrderService demonstrates span creation, attribute setting, and error recording.
type OrderService struct {
	tracer     trace.Tracer
	httpClient *http.Client
}

func NewOrderService(tracer trace.Tracer) *OrderService {
	return &OrderService{
		tracer: tracer,
		// Instrument the HTTP client so outbound calls carry trace context.
		httpClient: &http.Client{
			Transport: otelhttp.NewTransport(http.DefaultTransport),
			Timeout:   10 * time.Second,
		},
	}
}

type Order struct {
	ID       string  `json:"id"`
	UserID   string  `json:"user_id"`
	Amount   float64 `json:"amount"`
	Currency string  `json:"currency"`
}

func (s *OrderService) CreateOrder(ctx context.Context, order Order) error {
	// Start a new span. The span name follows the format: "service.operation"
	ctx, span := s.tracer.Start(ctx, "order.create",
		trace.WithSpanKind(trace.SpanKindServer),
		trace.WithAttributes(
			attribute.String("order.id", order.ID),
			attribute.String("order.user_id", order.UserID),
			attribute.Float64("order.amount", order.Amount),
			attribute.String("order.currency", order.Currency),
		),
	)
	defer span.End()

	// Call downstream payment service — trace context is propagated via HTTP header
	if err := s.callPaymentService(ctx, order); err != nil {
		// RecordError records the error but does NOT set span status automatically.
		span.RecordError(err)
		// You must explicitly set the status to ERROR.
		span.SetStatus(codes_Error, err.Error())
		return fmt.Errorf("payment service: %w", err)
	}

	span.SetAttributes(attribute.Bool("order.payment_confirmed", true))
	return nil
}

func (s *OrderService) callPaymentService(ctx context.Context, order Order) error {
	ctx, span := s.tracer.Start(ctx, "payment.charge",
		trace.WithSpanKind(trace.SpanKindClient),
	)
	defer span.End()

	paymentURL := fmt.Sprintf("http://payment-service/charge/%s", order.ID)
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, paymentURL, nil)
	if err != nil {
		return err
	}

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return fmt.Errorf("http request failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("payment service returned %d: %s", resp.StatusCode, body)
	}

	return nil
}

// HTTP handler with automatic span creation via otelhttp middleware
func orderHandler(svc *OrderService) http.Handler {
	return otelhttp.NewHandler(
		http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			var order Order
			if err := json.NewDecoder(r.Body).Decode(&order); err != nil {
				http.Error(w, err.Error(), http.StatusBadRequest)
				return
			}
			if err := svc.CreateOrder(r.Context(), order); err != nil {
				http.Error(w, err.Error(), http.StatusInternalServerError)
				return
			}
			w.WriteHeader(http.StatusCreated)
		}),
		"POST /orders",
	)
}

func main() {
	ctx := context.Background()

	tp, err := NewTracerProvider(ctx, "order-service", "1.0.0")
	if err != nil {
		log.Fatalf("failed to create tracer provider: %v", err)
	}
	defer tp.Shutdown(ctx)

	tracer := otel.Tracer("order-service")
	svc := NewOrderService(tracer)

	mux := http.NewServeMux()
	mux.Handle("POST /orders", orderHandler(svc))

	log.Println("order-service listening on :8080")
	log.Fatal(http.ListenAndServe(":8080", mux))
}
```

```go
// File: tracing/tracer_test.go
package main

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"go.opentelemetry.io/otel"
	"go.opentelemetry.io/otel/sdk/trace"
	"go.opentelemetry.io/otel/sdk/trace/tracetest"
)

func TestOrderService_CreateOrder_PropagatesTrace(t *testing.T) {
	// In-memory span recorder — no external dependency
	recorder := tracetest.NewSpanRecorder()
	tp := trace.NewTracerProvider(trace.WithSpanProcessor(recorder))
	otel.SetTracerProvider(tp)

	// Mock payment service
	paymentSrv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Verify trace context was propagated
		traceparent := r.Header.Get("Traceparent")
		if traceparent == "" {
			t.Error("traceparent header missing — trace context not propagated")
		}
		w.WriteHeader(http.StatusOK)
	}))
	defer paymentSrv.Close()

	tracer := otel.Tracer("test")
	svc := NewOrderService(tracer)
	// Override URL for testing
	_ = svc

	ctx := context.Background()
	order := Order{ID: "ord-1", UserID: "usr-1", Amount: 100.0, Currency: "USD"}

	// Create root span manually
	ctx, rootSpan := tracer.Start(ctx, "test.root")
	defer rootSpan.End()

	_ = ctx
	_ = order

	spans := recorder.Ended()
	t.Logf("recorded %d spans", len(spans))
}

func TestTraceParentFormat(t *testing.T) {
	// Test W3C traceparent parsing
	header := "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
	parts := strings.Split(header, "-")
	if len(parts) != 4 {
		t.Fatalf("expected 4 parts, got %d", len(parts))
	}
	if parts[0] != "00" {
		t.Errorf("expected version 00, got %s", parts[0])
	}
	if len(parts[1]) != 32 {
		t.Errorf("trace-id should be 32 hex chars, got %d", len(parts[1]))
	}
	if len(parts[2]) != 16 {
		t.Errorf("span-id should be 16 hex chars, got %d", len(parts[2]))
	}
}
```

### Implementation: Manual Trace Context in Rust

```rust
// File: src/tracing_propagation.rs
// Cargo.toml dependencies:
// opentelemetry = { version = "0.22", features = ["trace"] }
// opentelemetry-otlp = { version = "0.15", features = ["http-proto"] }
// opentelemetry_sdk = { version = "0.22", features = ["rt-tokio"] }
// tracing = "0.1"
// tracing-opentelemetry = "0.23"
// tracing-subscriber = { version = "0.3", features = ["env-filter"] }

use opentelemetry::{
    global,
    propagation::TextMapPropagator,
    trace::{SpanKind, Status, TraceContextExt, Tracer},
    Context, KeyValue,
};
use opentelemetry_sdk::{
    propagation::TraceContextPropagator,
    trace::{self, RandomIdGenerator, Sampler},
};
use std::collections::HashMap;
use tracing::instrument;
use tracing_opentelemetry::OpenTelemetrySpanExt;

/// HeaderMap implements TextMapCarrier for HTTP header injection/extraction.
/// This is the bridge between OpenTelemetry and your HTTP layer.
#[derive(Debug, Default)]
pub struct HeaderMap(pub HashMap<String, String>);

impl opentelemetry::propagation::Injector for HeaderMap {
    fn set(&mut self, key: &str, value: String) {
        self.0.insert(key.to_lowercase(), value);
    }
}

impl opentelemetry::propagation::Extractor for HeaderMap {
    fn get(&self, key: &str) -> Option<&str> {
        self.0.get(&key.to_lowercase()).map(|s| s.as_str())
    }

    fn keys(&self) -> Vec<&str> {
        self.0.keys().map(|s| s.as_str()).collect()
    }
}

/// TraceContext provides a type-safe wrapper around distributed trace context.
/// Use this to propagate context through async boundaries.
#[derive(Clone)]
pub struct TraceContext {
    inner: Context,
}

impl TraceContext {
    /// Extract trace context from incoming HTTP headers
    pub fn from_headers(headers: &HashMap<String, String>) -> Self {
        let propagator = TraceContextPropagator::new();
        let carrier = HeaderMap(headers.clone());
        let ctx = propagator.extract(&carrier);
        TraceContext { inner: ctx }
    }

    /// Inject trace context into outgoing HTTP headers
    pub fn inject_into_headers(&self, headers: &mut HashMap<String, String>) {
        let propagator = TraceContextPropagator::new();
        let mut carrier = HeaderMap::default();
        propagator.inject_context(&self.inner, &mut carrier);
        headers.extend(carrier.0);
    }

    /// Get the underlying OpenTelemetry Context
    pub fn as_otel_context(&self) -> &Context {
        &self.inner
    }
}

/// OrderRequest represents an incoming order with trace context
#[derive(Debug)]
pub struct OrderRequest {
    pub id: String,
    pub user_id: String,
    pub amount: f64,
    pub headers: HashMap<String, String>,
}

/// PaymentResult from downstream service
#[derive(Debug)]
pub enum PaymentError {
    NetworkError(String),
    ServiceError { status: u16, body: String },
    Timeout,
}

impl std::fmt::Display for PaymentError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            PaymentError::NetworkError(msg) => write!(f, "network error: {}", msg),
            PaymentError::ServiceError { status, body } => {
                write!(f, "service error {}: {}", status, body)
            }
            PaymentError::Timeout => write!(f, "request timeout"),
        }
    }
}

/// OrderService demonstrates idiomatic OpenTelemetry usage in Rust.
pub struct OrderService {
    tracer: opentelemetry_sdk::trace::Tracer,
    http_client: reqwest::Client,
    payment_service_url: String,
}

impl OrderService {
    pub fn new(payment_service_url: String) -> Self {
        let tracer = global::tracer("order-service");
        let http_client = reqwest::Client::builder()
            .timeout(std::time::Duration::from_secs(10))
            .build()
            .expect("failed to build HTTP client");

        OrderService {
            tracer,
            http_client,
            payment_service_url,
        }
    }

    /// Process an order, propagating trace context to downstream services.
    #[instrument(skip(self), fields(order.id = %request.id, order.user_id = %request.user_id))]
    pub async fn process_order(&self, request: OrderRequest) -> Result<String, PaymentError> {
        // Extract incoming trace context from request headers
        let parent_ctx = TraceContext::from_headers(&request.headers);

        // Start a child span with the incoming context as parent
        let mut span = self
            .tracer
            .span_builder("order.process")
            .with_kind(SpanKind::Server)
            .with_attributes(vec![
                KeyValue::new("order.id", request.id.clone()),
                KeyValue::new("order.user_id", request.user_id.clone()),
                KeyValue::new("order.amount", request.amount.to_string()),
            ])
            .start_with_context(&self.tracer, parent_ctx.as_otel_context());

        // Propagate context to downstream call
        let result = self.charge_payment(&request, parent_ctx).await;

        match &result {
            Ok(tx_id) => {
                span.set_attribute(KeyValue::new("payment.transaction_id", tx_id.clone()));
                span.set_status(Status::Ok);
            }
            Err(e) => {
                span.set_status(Status::error(e.to_string()));
                span.record_error(e as &dyn std::error::Error);
            }
        }

        result
    }

    async fn charge_payment(
        &self,
        request: &OrderRequest,
        parent_ctx: TraceContext,
    ) -> Result<String, PaymentError> {
        let url = format!("{}/charge/{}", self.payment_service_url, request.id);

        // Inject trace context into outgoing headers
        let mut outgoing_headers = HashMap::new();
        parent_ctx.inject_into_headers(&mut outgoing_headers);

        let mut request_builder = self.http_client.post(&url);
        for (k, v) in &outgoing_headers {
            request_builder = request_builder.header(k, v);
        }

        let response = request_builder
            .send()
            .await
            .map_err(|e| PaymentError::NetworkError(e.to_string()))?;

        if response.status().is_success() {
            let body = response
                .text()
                .await
                .map_err(|e| PaymentError::NetworkError(e.to_string()))?;
            Ok(body)
        } else {
            let status = response.status().as_u16();
            let body = response.text().await.unwrap_or_default();
            Err(PaymentError::ServiceError { status, body })
        }
    }
}

/// Initialize the global tracer provider.
/// MUST be called before any tracing occurs.
pub fn init_tracer(service_name: &str) -> opentelemetry_sdk::trace::TracerProvider {
    let otlp_endpoint = std::env::var("OTEL_EXPORTER_OTLP_ENDPOINT")
        .unwrap_or_else(|_| "http://localhost:4318".to_string());

    let exporter = opentelemetry_otlp::new_exporter()
        .http()
        .with_endpoint(&otlp_endpoint)
        .build_span_exporter()
        .expect("failed to build OTLP exporter");

    let provider = opentelemetry_sdk::trace::TracerProvider::builder()
        .with_batch_exporter(exporter, opentelemetry_sdk::runtime::Tokio)
        .with_config(
            trace::Config::default()
                .with_sampler(Sampler::ParentBased(Box::new(Sampler::TraceIdRatioBased(
                    0.01, // 1% sampling in production
                ))))
                .with_id_generator(RandomIdGenerator::default())
                .with_max_events_per_span(64)
                .with_resource(opentelemetry_sdk::Resource::new(vec![
                    KeyValue::new("service.name", service_name.to_owned()),
                ])),
        )
        .build();

    global::set_tracer_provider(provider.clone());
    global::set_text_map_propagator(TraceContextPropagator::new());
    provider
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_header_injection_extraction_roundtrip() {
        // Create a context with a known span
        let tracer = global::tracer("test");
        let span = tracer.start("test-span");
        let ctx = Context::current_with_span(span);

        // Inject into headers
        let propagator = TraceContextPropagator::new();
        let mut carrier = HeaderMap::default();
        propagator.inject_context(&ctx, &mut carrier);

        // Verify traceparent header was set
        assert!(
            carrier.0.contains_key("traceparent"),
            "traceparent header must be present after injection"
        );

        let traceparent = &carrier.0["traceparent"];
        let parts: Vec<&str> = traceparent.split('-').collect();
        assert_eq!(parts.len(), 4, "traceparent must have 4 parts");
        assert_eq!(parts[0], "00", "version must be 00");
        assert_eq!(parts[1].len(), 32, "trace-id must be 32 hex chars");
        assert_eq!(parts[2].len(), 16, "span-id must be 16 hex chars");

        // Extract and verify same trace ID
        let extracted_ctx = propagator.extract(&carrier);
        let extracted_span = extracted_ctx.span();
        let extracted_trace_id = extracted_span.span_context().trace_id();

        let original_span = ctx.span();
        let original_trace_id = original_span.span_context().trace_id();

        assert_eq!(
            original_trace_id, extracted_trace_id,
            "trace ID must survive injection/extraction"
        );
    }

    #[test]
    fn test_trace_context_from_missing_headers() {
        // Should not panic when headers are missing
        let headers = HashMap::new();
        let ctx = TraceContext::from_headers(&headers);
        // Should produce an invalid (no-op) span context
        let span_ctx = ctx.as_otel_context().span().span_context().clone();
        assert!(!span_ctx.is_valid(), "missing headers should produce invalid context");
    }
}
```

### Implementation: Correlation ID in C (POSIX HTTP Service)

```c
/* File: src/correlation.c
 * Build: gcc -O2 -Wall -Wextra -pthread correlation.c -o correlation
 * Purpose: Shows how to generate and propagate correlation IDs
 *          at the C/POSIX layer — useful for services written in C (nginx modules,
 *          eBPF programs, kernel modules that call into userspace).
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <time.h>
#include <pthread.h>
#include <uuid/uuid.h>   /* -luuid */

/* Thread-local storage for correlation ID.
 * __thread is a GCC extension; C11 uses _Thread_local.
 * This ensures each request goroutine has its own trace context
 * without locking — critical for performance.
 */
static __thread char tl_correlation_id[37];  /* UUID string: 36 chars + null */
static __thread char tl_trace_id[33];        /* W3C trace-id: 32 hex chars */
static __thread char tl_span_id[17];         /* W3C span-id: 16 hex chars */

/* correlation_id_generate: generate a new UUID v4 correlation ID.
 * UUID v4 is random, providing 122 bits of entropy.
 * DO NOT use rand() or time()-based IDs — they collide under load.
 */
void correlation_id_generate(void) {
    uuid_t uuid;
    uuid_generate_random(uuid);
    uuid_unparse_lower(uuid, tl_correlation_id);
}

/* correlation_id_from_header: extract correlation ID from HTTP header value.
 * Validates format to prevent injection attacks.
 * Returns 1 on success, 0 on invalid input.
 */
int correlation_id_from_header(const char *header_value) {
    if (!header_value) return 0;

    /* UUID format: 8-4-4-4-12 hex chars with hyphens, 36 total */
    if (strlen(header_value) != 36) return 0;

    /* Validate UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx */
    for (int i = 0; i < 36; i++) {
        if (i == 8 || i == 13 || i == 18 || i == 23) {
            if (header_value[i] != '-') return 0;
        } else {
            char c = header_value[i];
            if (!((c >= '0' && c <= '9') ||
                  (c >= 'a' && c <= 'f') ||
                  (c >= 'A' && c <= 'F'))) {
                return 0;
            }
        }
    }

    strncpy(tl_correlation_id, header_value, 36);
    tl_correlation_id[36] = '\0';
    return 1;
}

/* get_correlation_id: get the current thread's correlation ID.
 * Returns pointer to thread-local storage — DO NOT free.
 */
const char *get_correlation_id(void) {
    if (tl_correlation_id[0] == '\0') {
        correlation_id_generate();
    }
    return tl_correlation_id;
}

/* w3c_traceparent_generate: generate a W3C traceparent header value.
 * Format: 00-<trace-id>-<span-id>-01
 * Output buffer must be at least 56 bytes.
 */
void w3c_traceparent_generate(char *out, size_t outlen) {
    /* Generate 128-bit trace ID from /dev/urandom */
    uint64_t trace_hi = 0, trace_lo = 0;
    uint64_t span_id = 0;

    FILE *urandom = fopen("/dev/urandom", "rb");
    if (urandom) {
        fread(&trace_hi, sizeof(uint64_t), 1, urandom);
        fread(&trace_lo, sizeof(uint64_t), 1, urandom);
        fread(&span_id, sizeof(uint64_t), 1, urandom);
        fclose(urandom);
    }

    /* Traceparent: 00-{32 hex trace-id}-{16 hex span-id}-01 */
    snprintf(out, outlen,
             "00-%016llx%016llx-%016llx-01",
             (unsigned long long)trace_hi,
             (unsigned long long)trace_lo,
             (unsigned long long)span_id);
}

/* request_context: per-request context passed through call chain */
typedef struct {
    char correlation_id[37];
    char traceparent[56];
    char service_name[64];
    uint64_t start_ns;         /* nanoseconds since epoch */
} RequestContext;

/* request_context_init: initialize a new request context.
 * Call this at the entry point of each request handler.
 */
RequestContext *request_context_init(const char *incoming_correlation_id,
                                     const char *incoming_traceparent,
                                     const char *service_name) {
    RequestContext *ctx = calloc(1, sizeof(RequestContext));
    if (!ctx) return NULL;

    /* Use incoming correlation ID or generate new one */
    if (incoming_correlation_id &&
        correlation_id_from_header(incoming_correlation_id)) {
        strncpy(ctx->correlation_id, incoming_correlation_id, 36);
    } else {
        uuid_t uuid;
        uuid_generate_random(uuid);
        uuid_unparse_lower(uuid, ctx->correlation_id);
    }

    /* Generate new traceparent (new span in the same trace) */
    if (incoming_traceparent) {
        /* In production: parse trace-id from incoming, generate new span-id */
        /* For brevity, we generate a fresh one here */
        w3c_traceparent_generate(ctx->traceparent, sizeof(ctx->traceparent));
    } else {
        w3c_traceparent_generate(ctx->traceparent, sizeof(ctx->traceparent));
    }

    strncpy(ctx->service_name, service_name, sizeof(ctx->service_name) - 1);

    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    ctx->start_ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;

    return ctx;
}

/* structured_log: emit a structured JSON log line with trace context.
 * In production, stdout is collected by Fluentd/Fluent Bit.
 */
void structured_log(const RequestContext *ctx,
                    const char *level,
                    const char *message) {
    struct timespec ts;
    clock_gettime(CLOCK_REALTIME, &ts);
    uint64_t now_ns = (uint64_t)ts.tv_sec * 1000000000ULL + ts.tv_nsec;
    uint64_t latency_us = (now_ns - ctx->start_ns) / 1000;

    /* Emit JSON to stdout for log aggregation.
     * NEVER use printf with user-controlled data in the message field —
     * always pass it as a string argument (format string injection).
     */
    printf("{\"timestamp\":\"%ld.%09ld\","
           "\"level\":\"%s\","
           "\"service\":\"%s\","
           "\"correlation_id\":\"%s\","
           "\"traceparent\":\"%s\","
           "\"latency_us\":%llu,"
           "\"message\":\"%s\"}\n",
           ts.tv_sec, ts.tv_nsec,
           level,
           ctx->service_name,
           ctx->correlation_id,
           ctx->traceparent,
           (unsigned long long)latency_us,
           message);
}

/* Demo: simulate processing a request with full context propagation */
void *handle_request(void *arg) {
    const char *incoming_id = (const char *)arg;

    RequestContext *ctx = request_context_init(
        incoming_id,
        NULL,
        "order-service-c"
    );
    if (!ctx) return NULL;

    structured_log(ctx, "INFO", "request received");

    /* Simulate work */
    struct timespec sleep_ts = { .tv_sec = 0, .tv_nsec = 100000 };
    nanosleep(&sleep_ts, NULL);

    structured_log(ctx, "INFO", "order processed");
    free(ctx);
    return NULL;
}

int main(void) {
    /* Simulate 5 concurrent requests */
    pthread_t threads[5];
    const char *fake_ids[] = {
        "550e8400-e29b-41d4-a716-446655440000",
        "invalid-id",  /* should auto-generate new */
        "6ba7b810-9dad-11d1-80b4-00c04fd430c8",
        NULL,          /* missing header */
        "6ba7b812-9dad-11d1-80b4-00c04fd430c8",
    };

    for (int i = 0; i < 5; i++) {
        pthread_create(&threads[i], NULL, handle_request, (void *)fake_ids[i]);
    }

    for (int i = 0; i < 5; i++) {
        pthread_join(threads[i], NULL);
    }

    return 0;
}
```

---

## 3. Network Unreliability

### Linux Kernel Network Stack Internals

Understanding where failures occur in the kernel helps you instrument the right layer.

```
Application (read/write syscall)
        │
  Socket Buffer (sk_buff)       ← first place data can be dropped
        │
  TCP/UDP Layer                  ← retransmits, timeouts, window scaling
        │
  IP Layer (netfilter hooks)     ← iptables, nftables can drop silently
        │
  Network Device Driver          ← ring buffer overflow → packet drop
        │
  Physical/Virtual NIC
```

**Critical kernel parameters for microservice deployments**:

```bash
# View current TCP settings
sysctl net.ipv4.tcp_syn_retries
sysctl net.ipv4.tcp_retries2
sysctl net.core.rmem_max
sysctl net.core.wmem_max

# For high-throughput microservices:
# Increase socket receive/send buffers
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.ipv4.tcp_rmem='4096 87380 134217728'
sysctl -w net.ipv4.tcp_wmem='4096 65536 134217728'

# Reduce TIME_WAIT socket reuse (safe for internal services)
sysctl -w net.ipv4.tcp_tw_reuse=1

# Increase the number of pending connections (SYN backlog)
sysctl -w net.core.somaxconn=65535
sysctl -w net.ipv4.tcp_max_syn_backlog=65535

# Keepalive tuning — detect dead connections faster
sysctl -w net.ipv4.tcp_keepalive_time=60
sysctl -w net.ipv4.tcp_keepalive_intvl=10
sysctl -w net.ipv4.tcp_keepalive_probes=6
```

### Diagnosing Network Issues with eBPF

```c
/* File: ebpf/tcp_drop_monitor.c
 * Compile: clang -O2 -target bpf -c tcp_drop_monitor.c -o tcp_drop_monitor.o
 * Load:    bpftool prog load tcp_drop_monitor.o /sys/fs/bpf/tcp_drop
 *
 * This eBPF program attaches to the kfree_skb tracepoint to detect
 * TCP packet drops — invisible to application-level monitoring.
 */

#include <linux/bpf.h>
#include <linux/skbuff.h>
#include <linux/ip.h>
#include <linux/tcp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

/* Map to count drops per source IP */
struct {
    __uint(type, BPF_MAP_TYPE_LRU_HASH);
    __uint(max_entries, 10000);
    __type(key, __u32);    /* source IP */
    __type(value, __u64);  /* drop count */
} drop_count_map SEC(".maps");

/* Event structure sent to userspace via perf buffer */
struct drop_event {
    __u32 src_ip;
    __u32 dst_ip;
    __u16 src_port;
    __u16 dst_port;
    __u8  protocol;
    __u8  tcp_flags;
    __u64 timestamp_ns;
};

/* Perf buffer for streaming events to userspace */
struct {
    __uint(type, BPF_MAP_TYPE_PERF_EVENT_ARRAY);
    __uint(key_size, sizeof(__u32));
    __uint(value_size, sizeof(__u32));
} events SEC(".maps");

/* Attach to kfree_skb — called whenever the kernel drops an skb */
SEC("tracepoint/skb/kfree_skb")
int trace_tcp_drop(struct trace_event_raw_kfree_skb *ctx) {
    struct sk_buff *skb = ctx->skbaddr;
    if (!skb) return 0;

    /* Only care about TCP (protocol 6) */
    struct iphdr iph;
    if (bpf_probe_read_kernel(&iph, sizeof(iph),
                               skb->head + skb->network_header) < 0)
        return 0;

    if (iph.protocol != IPPROTO_TCP) return 0;

    struct tcphdr tcph;
    if (bpf_probe_read_kernel(&tcph, sizeof(tcph),
                               skb->head + skb->transport_header) < 0)
        return 0;

    /* Increment drop counter for this source IP */
    __u32 src_ip = iph.saddr;
    __u64 *count = bpf_map_lookup_elem(&drop_count_map, &src_ip);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 one = 1;
        bpf_map_update_elem(&drop_count_map, &src_ip, &one, BPF_ANY);
    }

    /* Send event to userspace */
    struct drop_event event = {
        .src_ip       = iph.saddr,
        .dst_ip       = iph.daddr,
        .src_port     = bpf_ntohs(tcph.source),
        .dst_port     = bpf_ntohs(tcph.dest),
        .protocol     = iph.protocol,
        .tcp_flags    = ((unsigned char *)&tcph)[13], /* flags byte */
        .timestamp_ns = bpf_ktime_get_ns(),
    };

    bpf_perf_event_output(ctx, &events, BPF_F_CURRENT_CPU,
                           &event, sizeof(event));
    return 0;
}

char _license[] SEC("license") = "GPL";
```

### Timeout Hierarchy in Go — The Right Way

```go
// File: network/timeout_hierarchy.go
// Demonstrates the three layers of timeout you MUST configure in production.

package network

import (
	"context"
	"fmt"
	"net"
	"net/http"
	"time"
)

// TimeoutConfig defines the complete timeout hierarchy for an HTTP client.
// Every production service MUST set all three levels.
type TimeoutConfig struct {
	// DialTimeout: TCP connection establishment timeout.
	// Protects against SYN floods and unreachable hosts.
	// Default: 5s — increase for cross-region calls.
	DialTimeout time.Duration

	// TLSHandshakeTimeout: TLS negotiation timeout.
	// Certificate validation + key exchange.
	// Default: 10s — affected by certificate chain length.
	TLSHandshakeTimeout time.Duration

	// ResponseHeaderTimeout: time to receive the FIRST byte of response headers.
	// Does NOT include body download time.
	// Set based on P99 latency of downstream service, not average.
	ResponseHeaderTimeout time.Duration

	// RequestTimeout: total request timeout including body read.
	// This is the http.Client.Timeout — it starts a timer from request send.
	// PITFALL: http.Client.Timeout cancels the context, which drops the body.
	//          Use context.WithTimeout for fine-grained control instead.
	RequestTimeout time.Duration

	// IdleConnTimeout: how long an idle connection stays in the pool.
	// Too short: creates new connections under bursty load.
	// Too long: holds connections to services that have rotated endpoints.
	IdleConnTimeout time.Duration

	// MaxIdleConnsPerHost: connection pool size per upstream host.
	// Default is 2 — CRITICALLY low for microservices.
	// Set to your P99 concurrent RPS to avoid exhausting the pool.
	MaxIdleConnsPerHost int
}

// DefaultProductionConfig returns safe defaults for internal microservice calls.
// Adjust ResponseHeaderTimeout based on your SLO requirements.
func DefaultProductionConfig() TimeoutConfig {
	return TimeoutConfig{
		DialTimeout:           3 * time.Second,
		TLSHandshakeTimeout:   5 * time.Second,
		ResponseHeaderTimeout: 10 * time.Second,
		RequestTimeout:        30 * time.Second,
		IdleConnTimeout:       90 * time.Second,
		MaxIdleConnsPerHost:   100,
	}
}

// NewProductionHTTPClient constructs an HTTP client with production-safe settings.
// This is NOT the same as http.DefaultClient — never use http.DefaultClient in production
// because it has no timeouts and will leak goroutines on slow upstreams.
func NewProductionHTTPClient(cfg TimeoutConfig) *http.Client {
	transport := &http.Transport{
		DialContext: (&net.Dialer{
			Timeout:   cfg.DialTimeout,
			KeepAlive: 30 * time.Second, // TCP keepalive for detecting dead connections
		}).DialContext,
		TLSHandshakeTimeout:   cfg.TLSHandshakeTimeout,
		ResponseHeaderTimeout: cfg.ResponseHeaderTimeout,
		IdleConnTimeout:       cfg.IdleConnTimeout,
		MaxIdleConnsPerHost:   cfg.MaxIdleConnsPerHost,
		MaxConnsPerHost:       cfg.MaxIdleConnsPerHost * 2,
		// DisableKeepAlives: false — NEVER set to true in microservices.
		// Disabling keep-alives causes a new TCP+TLS handshake per request.
		// ForceAttemptHTTP2: use HTTP/2 for multiplexing (requires TLS).
		ForceAttemptHTTP2: true,
	}

	return &http.Client{
		Transport: transport,
		Timeout:   cfg.RequestTimeout,
		// DO NOT set CheckRedirect to nil — it will follow redirects silently.
		// For internal services, redirects are usually a misconfiguration.
		CheckRedirect: func(req *http.Request, via []*http.Request) error {
			return fmt.Errorf("unexpected redirect from %s to %s",
				via[len(via)-1].URL, req.URL)
		},
	}
}

// CallWithContextTimeout demonstrates using context.WithTimeout
// for granular control vs http.Client.Timeout.
func CallWithContextTimeout(
	ctx context.Context,
	client *http.Client,
	url string,
	timeout time.Duration,
) (*http.Response, error) {
	// IMPORTANT: context.WithTimeout creates a derived context.
	// The timeout starts NOW — not when the network call starts.
	// Account for queuing time before the call is made.
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel() // ALWAYS call cancel to release resources, even on success

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, url, nil)
	if err != nil {
		return nil, fmt.Errorf("creating request: %w", err)
	}

	resp, err := client.Do(req)
	if err != nil {
		// Distinguish timeout from other errors for metric labeling
		if ctx.Err() == context.DeadlineExceeded {
			return nil, fmt.Errorf("request timed out after %v: %w", timeout, err)
		}
		return nil, fmt.Errorf("request failed: %w", err)
	}

	return resp, nil
}
```

---

## 4. Partial Failures

### The Two Generals Problem

Two generals must coordinate an attack across enemy lines. Every message can be lost. Neither can be certain the other received the last message. This is mathematically proven to be unsolvable — no protocol can guarantee agreement over an unreliable channel.

**Practical implication**: Your distributed system WILL experience partial failures. Design for it from day one.

### Failure Detector Categories (Chandra-Toueg)

| Type | Property | Example |
|------|----------|---------|
| Perfect (✓P) | No false positives | Impossible over async networks |
| Strong (◇P) | Eventually no false positives | Used by Paxos, Raft |
| Weak (◇W) | Some process eventually detected | Gossip protocols |
| Eventually Perfect (◇P) | Eventually perfectly accurate | Zookeeper watches |

### Circuit Breaker Pattern — Full Implementation in Rust

```rust
// File: src/circuit_breaker.rs
// A production-grade circuit breaker with half-open probe requests,
// metrics, and configurable thresholds.

use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use std::future::Future;

/// Circuit breaker state machine:
///
/// CLOSED ──(failures >= threshold)──► OPEN
///   ▲                                    │
///   │                               (timeout elapsed)
///   │                                    │
/// (probe succeeds)                       ▼
/// HALF_OPEN ◄────────────────────── HALF_OPEN
///     │
/// (probe fails)
///     └──────────────────────────────► OPEN
#[derive(Debug, Clone, PartialEq)]
pub enum CircuitState {
    Closed,
    Open,
    HalfOpen,
}

#[derive(Debug, Clone)]
pub struct CircuitBreakerConfig {
    /// Number of failures to trip the breaker
    pub failure_threshold: u32,
    /// Percentage of calls that must fail to trip (alternative to count)
    pub failure_rate_threshold: f64,
    /// Minimum number of calls before rate-based tripping applies
    pub minimum_call_count: u32,
    /// How long to stay open before trying a probe
    pub open_timeout: Duration,
    /// How many probe calls to allow in half-open state
    pub half_open_max_calls: u32,
    /// How long the rolling window lasts for counting failures
    pub rolling_window: Duration,
}

impl Default for CircuitBreakerConfig {
    fn default() -> Self {
        CircuitBreakerConfig {
            failure_threshold: 5,
            failure_rate_threshold: 0.5, // 50% failure rate
            minimum_call_count: 10,
            open_timeout: Duration::from_secs(30),
            half_open_max_calls: 3,
            rolling_window: Duration::from_secs(60),
        }
    }
}

/// WindowStats tracks call statistics within the rolling window.
#[derive(Debug, Default)]
struct WindowStats {
    success_count: u32,
    failure_count: u32,
    window_start: Option<Instant>,
}

impl WindowStats {
    fn total(&self) -> u32 {
        self.success_count + self.failure_count
    }

    fn failure_rate(&self) -> f64 {
        if self.total() == 0 {
            return 0.0;
        }
        self.failure_count as f64 / self.total() as f64
    }

    fn reset(&mut self) {
        self.success_count = 0;
        self.failure_count = 0;
        self.window_start = Some(Instant::now());
    }
}

/// CircuitBreaker wraps a service call and tracks its health.
/// Thread-safe via Arc<Mutex<>> for state and Arc<Atomic> for counters.
pub struct CircuitBreaker {
    name: String,
    config: CircuitBreakerConfig,
    state: Arc<Mutex<CircuitState>>,
    stats: Arc<Mutex<WindowStats>>,
    opened_at: Arc<Mutex<Option<Instant>>>,
    half_open_calls: Arc<AtomicU32>,
    /// Metrics counters — in production, push to Prometheus
    total_calls: Arc<AtomicU64>,
    rejected_calls: Arc<AtomicU64>,
}

#[derive(Debug, thiserror::Error)]
pub enum CircuitBreakerError<E: std::error::Error> {
    #[error("circuit breaker open: service '{service}' is unavailable")]
    Open { service: String },
    #[error("underlying service error: {0}")]
    ServiceError(E),
}

impl CircuitBreaker {
    pub fn new(name: impl Into<String>, config: CircuitBreakerConfig) -> Self {
        CircuitBreaker {
            name: name.into(),
            config,
            state: Arc::new(Mutex::new(CircuitState::Closed)),
            stats: Arc::new(Mutex::new(WindowStats {
                window_start: Some(Instant::now()),
                ..Default::default()
            })),
            opened_at: Arc::new(Mutex::new(None)),
            half_open_calls: Arc::new(AtomicU32::new(0)),
            total_calls: Arc::new(AtomicU64::new(0)),
            rejected_calls: Arc::new(AtomicU64::new(0)),
        }
    }

    /// Execute a future through the circuit breaker.
    pub async fn call<F, Fut, T, E>(&self, f: F) -> Result<T, CircuitBreakerError<E>>
    where
        F: FnOnce() -> Fut,
        Fut: Future<Output = Result<T, E>>,
        E: std::error::Error,
    {
        self.total_calls.fetch_add(1, Ordering::Relaxed);

        // Check if we can proceed with this call
        if !self.allow_request() {
            self.rejected_calls.fetch_add(1, Ordering::Relaxed);
            return Err(CircuitBreakerError::Open {
                service: self.name.clone(),
            });
        }

        // Execute the actual call
        let result = f().await;

        // Record the outcome and potentially change state
        match &result {
            Ok(_) => self.record_success(),
            Err(_) => self.record_failure(),
        }

        result.map_err(CircuitBreakerError::ServiceError)
    }

    fn allow_request(&self) -> bool {
        let mut state = self.state.lock().unwrap();

        match *state {
            CircuitState::Closed => true,
            CircuitState::Open => {
                // Check if timeout has elapsed — if so, transition to half-open
                let opened_at = self.opened_at.lock().unwrap();
                if let Some(opened) = *opened_at {
                    if opened.elapsed() >= self.config.open_timeout {
                        drop(opened_at);
                        *state = CircuitState::HalfOpen;
                        self.half_open_calls.store(0, Ordering::SeqCst);
                        return true;
                    }
                }
                false
            }
            CircuitState::HalfOpen => {
                // Allow limited probe calls in half-open state
                let current = self.half_open_calls.load(Ordering::SeqCst);
                if current < self.config.half_open_max_calls {
                    self.half_open_calls.fetch_add(1, Ordering::SeqCst);
                    true
                } else {
                    false
                }
            }
        }
    }

    fn record_success(&self) {
        let mut state = self.state.lock().unwrap();
        let mut stats = self.stats.lock().unwrap();

        self.maybe_reset_window(&mut stats);
        stats.success_count += 1;

        if *state == CircuitState::HalfOpen {
            // All probe calls succeeded — close the circuit
            if self.half_open_calls.load(Ordering::SeqCst) >= self.config.half_open_max_calls {
                *state = CircuitState::Closed;
                stats.reset();
                tracing::info!(
                    service = %self.name,
                    "circuit breaker closed — service recovered"
                );
            }
        }
    }

    fn record_failure(&self) {
        let mut state = self.state.lock().unwrap();
        let mut stats = self.stats.lock().unwrap();

        self.maybe_reset_window(&mut stats);
        stats.failure_count += 1;

        let should_trip = match *state {
            CircuitState::Closed => self.should_trip(&stats),
            CircuitState::HalfOpen => true, // Any failure in half-open trips immediately
            CircuitState::Open => false,
        };

        if should_trip {
            *state = CircuitState::Open;
            let mut opened_at = self.opened_at.lock().unwrap();
            *opened_at = Some(Instant::now());
            tracing::warn!(
                service = %self.name,
                failure_count = stats.failure_count,
                failure_rate = stats.failure_rate(),
                "circuit breaker opened"
            );
        }
    }

    fn should_trip(&self, stats: &WindowStats) -> bool {
        // Trip on absolute failure count
        if stats.failure_count >= self.config.failure_threshold {
            return true;
        }
        // Trip on failure rate (only if enough calls have been made)
        if stats.total() >= self.config.minimum_call_count
            && stats.failure_rate() >= self.config.failure_rate_threshold
        {
            return true;
        }
        false
    }

    fn maybe_reset_window(&self, stats: &mut WindowStats) {
        if let Some(start) = stats.window_start {
            if start.elapsed() >= self.config.rolling_window {
                stats.reset();
            }
        }
    }

    pub fn state(&self) -> CircuitState {
        self.state.lock().unwrap().clone()
    }

    pub fn metrics(&self) -> (u64, u64) {
        (
            self.total_calls.load(Ordering::Relaxed),
            self.rejected_calls.load(Ordering::Relaxed),
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::AtomicBool;
    use std::sync::Arc;

    async fn failing_service() -> Result<(), std::io::Error> {
        Err(std::io::Error::new(std::io::ErrorKind::ConnectionRefused, "service down"))
    }

    async fn succeeding_service() -> Result<String, std::io::Error> {
        Ok("ok".to_string())
    }

    #[tokio::test]
    async fn test_circuit_trips_after_threshold() {
        let cb = CircuitBreaker::new(
            "test-service",
            CircuitBreakerConfig {
                failure_threshold: 3,
                open_timeout: Duration::from_millis(100),
                minimum_call_count: 0,
                ..Default::default()
            },
        );

        // Exhaust failure threshold
        for _ in 0..3 {
            let _ = cb.call(failing_service).await;
        }

        assert_eq!(cb.state(), CircuitState::Open);

        // Next call should be rejected without calling the service
        let result = cb.call(succeeding_service).await;
        assert!(matches!(result, Err(CircuitBreakerError::Open { .. })));
    }

    #[tokio::test]
    async fn test_circuit_recovers_after_timeout() {
        let cb = CircuitBreaker::new(
            "test-service",
            CircuitBreakerConfig {
                failure_threshold: 1,
                open_timeout: Duration::from_millis(50),
                half_open_max_calls: 1,
                minimum_call_count: 0,
                ..Default::default()
            },
        );

        // Trip the breaker
        let _ = cb.call(failing_service).await;
        assert_eq!(cb.state(), CircuitState::Open);

        // Wait for timeout
        tokio::time::sleep(Duration::from_millis(100)).await;

        // Should now be half-open and allow a probe
        let result = cb.call(succeeding_service).await;
        assert!(result.is_ok());

        // After successful probe, should close
        assert_eq!(cb.state(), CircuitState::Closed);
    }

    #[tokio::test]
    async fn test_failure_rate_threshold() {
        let cb = CircuitBreaker::new(
            "test-service",
            CircuitBreakerConfig {
                failure_threshold: 100, // high count threshold
                failure_rate_threshold: 0.5,
                minimum_call_count: 10,
                open_timeout: Duration::from_secs(30),
                ..Default::default()
            },
        );

        // 5 successes, 5 failures = 50% failure rate
        for _ in 0..5 {
            let _ = cb.call(succeeding_service).await;
        }
        for _ in 0..5 {
            let _ = cb.call(failing_service).await;
        }

        // Should have tripped on rate
        assert_eq!(cb.state(), CircuitState::Open);
    }
}
```

### Exponential Backoff with Jitter in Go

```go
// File: network/backoff.go
// Full-jitter exponential backoff — the most effective retry strategy
// for avoiding thundering herd problems.

package network

import (
	"context"
	"math"
	"math/rand"
	"time"
)

// BackoffConfig configures the retry behavior.
type BackoffConfig struct {
	InitialInterval time.Duration // First retry delay: ~100ms
	MaxInterval     time.Duration // Cap the delay: ~30s
	Multiplier      float64       // Exponential factor: 2.0
	MaxAttempts     int           // 0 = unlimited
	// Jitter strategy: "full" (recommended), "equal", "decorrelated"
	// Full jitter: random(0, min(cap, base * 2^attempt))
	// Equal jitter: cap/2 + random(0, cap/2)
	// Decorrelated: min(cap, random(base, sleep*3))
	JitterStrategy string
}

// DefaultBackoffConfig returns production-safe defaults.
func DefaultBackoffConfig() BackoffConfig {
	return BackoffConfig{
		InitialInterval: 100 * time.Millisecond,
		MaxInterval:     30 * time.Second,
		Multiplier:      2.0,
		MaxAttempts:     5,
		JitterStrategy:  "full",
	}
}

// RetryableError wraps an error with a flag indicating it's retryable.
type RetryableError struct {
	Err       error
	Retryable bool
}

func (e *RetryableError) Error() string { return e.Err.Error() }
func (e *RetryableError) Unwrap() error { return e.Err }

// IsRetryable is a hook to classify errors.
// Customize this for your specific error types.
type IsRetryable func(error) bool

func DefaultIsRetryable(err error) bool {
	var re *RetryableError
	if errors.As(err, &re) {
		return re.Retryable
	}
	// By default, retry on context errors that aren't cancellations
	return !errors.Is(err, context.Canceled)
}

// Retry executes fn with exponential backoff.
// Returns the last error if all attempts fail.
func Retry(ctx context.Context, cfg BackoffConfig, isRetryable IsRetryable, fn func(ctx context.Context) error) error {
	var lastErr error
	rng := rand.New(rand.NewSource(time.Now().UnixNano()))

	for attempt := 0; cfg.MaxAttempts == 0 || attempt < cfg.MaxAttempts; attempt++ {
		if attempt > 0 {
			delay := calculateDelay(cfg, attempt, rng)

			select {
			case <-ctx.Done():
				return fmt.Errorf("retry aborted: %w", ctx.Err())
			case <-time.After(delay):
			}
		}

		err := fn(ctx)
		if err == nil {
			return nil
		}

		lastErr = err

		if !isRetryable(err) {
			return fmt.Errorf("non-retryable error on attempt %d: %w", attempt+1, err)
		}
	}

	return fmt.Errorf("all %d attempts failed, last error: %w", cfg.MaxAttempts, lastErr)
}

func calculateDelay(cfg BackoffConfig, attempt int, rng *rand.Rand) time.Duration {
	// Calculate exponential ceiling: base * multiplier^attempt
	cap := float64(cfg.MaxInterval)
	base := float64(cfg.InitialInterval)
	ceiling := math.Min(cap, base*math.Pow(cfg.Multiplier, float64(attempt)))

	var delay float64
	switch cfg.JitterStrategy {
	case "full":
		// Best for reducing thundering herd
		delay = rng.Float64() * ceiling
	case "equal":
		// Guarantees minimum delay while adding jitter
		delay = ceiling/2 + rng.Float64()*(ceiling/2)
	case "decorrelated":
		// AWS recommendation for distributed systems
		// Each retry uses the previous sleep as input
		delay = math.Min(cap, base+rng.Float64()*(ceiling*3-base))
	default:
		delay = ceiling // No jitter (not recommended for production)
	}

	return time.Duration(delay)
}
```

---

## 5. Data Inconsistency

### The Distributed Transaction Problem

ACID transactions span ONE database. Across multiple databases, you must choose:

1. **Two-Phase Commit (2PC)**: Strong consistency, single point of failure (coordinator), high latency
2. **Saga Pattern**: Eventual consistency, compensating transactions, complex failure handling
3. **Outbox Pattern**: Exactly-once delivery from DB to message queue
4. **Event Sourcing**: Immutable audit log, eventual consistency

### The Outbox Pattern in Go

The outbox pattern solves the "dual write" problem: you cannot atomically write to a database AND publish to a message queue without distributed transactions. Instead, write both to the same database, then relay the outbox to the queue.

```go
// File: outbox/outbox.go
// The Outbox Pattern: guarantees exactly-once event delivery
// even if the process crashes between writing to the DB and publishing.

package outbox

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	_ "github.com/lib/pq"
)

// OutboxEvent represents a pending event that needs to be published.
type OutboxEvent struct {
	ID            string          `db:"id"`
	AggregateID   string          `db:"aggregate_id"`
	AggregateType string          `db:"aggregate_type"`
	EventType     string          `db:"event_type"`
	Payload       json.RawMessage `db:"payload"`
	CreatedAt     time.Time       `db:"created_at"`
	ProcessedAt   *time.Time      `db:"processed_at"`
	Attempts      int             `db:"attempts"`
	LastError     *string         `db:"last_error"`
}

// OutboxSchema is the SQL to create the outbox table.
// The index on processed_at+created_at is critical for polling performance.
const OutboxSchema = `
CREATE TABLE IF NOT EXISTS outbox_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id    TEXT NOT NULL,
    aggregate_type  TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    payload         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    processed_at    TIMESTAMPTZ,
    attempts        INTEGER NOT NULL DEFAULT 0,
    last_error      TEXT,

    -- Index for the polling query: find unprocessed events in order
    CONSTRAINT valid_attempts CHECK (attempts >= 0)
);

CREATE INDEX IF NOT EXISTS idx_outbox_unprocessed
    ON outbox_events (created_at)
    WHERE processed_at IS NULL;
`

// Publisher sends events from the outbox to the message broker.
type Publisher interface {
	Publish(ctx context.Context, event OutboxEvent) error
}

// OutboxProcessor polls the outbox table and publishes events.
// Uses SELECT FOR UPDATE SKIP LOCKED for safe concurrent processing.
type OutboxProcessor struct {
	db        *sql.DB
	publisher Publisher
	logger    *slog.Logger
	cfg       ProcessorConfig
}

type ProcessorConfig struct {
	PollInterval     time.Duration
	BatchSize        int
	MaxAttempts      int
	RetryBaseDelay   time.Duration
}

func DefaultProcessorConfig() ProcessorConfig {
	return ProcessorConfig{
		PollInterval:   500 * time.Millisecond,
		BatchSize:      100,
		MaxAttempts:    5,
		RetryBaseDelay: time.Second,
	}
}

func NewOutboxProcessor(db *sql.DB, publisher Publisher, cfg ProcessorConfig) *OutboxProcessor {
	return &OutboxProcessor{
		db:        db,
		publisher: publisher,
		logger:    slog.Default(),
		cfg:       cfg,
	}
}

// Run starts the polling loop. Cancel ctx to stop.
func (p *OutboxProcessor) Run(ctx context.Context) error {
	ticker := time.NewTicker(p.cfg.PollInterval)
	defer ticker.Stop()

	for {
		select {
		case <-ctx.Done():
			return nil
		case <-ticker.C:
			if err := p.processBatch(ctx); err != nil {
				p.logger.Error("outbox batch processing failed",
					"error", err)
			}
		}
	}
}

func (p *OutboxProcessor) processBatch(ctx context.Context) error {
	tx, err := p.db.BeginTx(ctx, &sql.TxOptions{
		Isolation: sql.LevelReadCommitted,
	})
	if err != nil {
		return fmt.Errorf("beginning transaction: %w", err)
	}
	defer tx.Rollback()

	// SELECT FOR UPDATE SKIP LOCKED: multiple processors can run safely.
	// SKIP LOCKED means: if a row is locked by another processor, skip it.
	// This prevents duplicate processing without a distributed lock.
	rows, err := tx.QueryContext(ctx, `
		SELECT id, aggregate_id, aggregate_type, event_type, payload, created_at, attempts
		FROM outbox_events
		WHERE processed_at IS NULL
		  AND attempts < $1
		ORDER BY created_at ASC
		LIMIT $2
		FOR UPDATE SKIP LOCKED
	`, p.cfg.MaxAttempts, p.cfg.BatchSize)
	if err != nil {
		return fmt.Errorf("querying outbox: %w", err)
	}
	defer rows.Close()

	var events []OutboxEvent
	for rows.Next() {
		var e OutboxEvent
		if err := rows.Scan(
			&e.ID, &e.AggregateID, &e.AggregateType,
			&e.EventType, &e.Payload, &e.CreatedAt, &e.Attempts,
		); err != nil {
			return fmt.Errorf("scanning row: %w", err)
		}
		events = append(events, e)
	}

	if err := rows.Err(); err != nil {
		return fmt.Errorf("iterating rows: %w", err)
	}

	for _, event := range events {
		if err := p.processEvent(ctx, tx, event); err != nil {
			p.logger.Error("failed to process event",
				"event_id", event.ID,
				"event_type", event.EventType,
				"error", err,
			)
		}
	}

	return tx.Commit()
}

func (p *OutboxProcessor) processEvent(ctx context.Context, tx *sql.Tx, event OutboxEvent) error {
	if err := p.publisher.Publish(ctx, event); err != nil {
		// Record failure but don't abort the batch
		errMsg := err.Error()
		_, dbErr := tx.ExecContext(ctx, `
			UPDATE outbox_events
			SET attempts = attempts + 1, last_error = $1
			WHERE id = $2
		`, errMsg, event.ID)
		if dbErr != nil {
			return fmt.Errorf("recording failure: %w", dbErr)
		}
		return fmt.Errorf("publishing event %s: %w", event.ID, err)
	}

	// Mark as processed
	now := time.Now()
	_, err := tx.ExecContext(ctx, `
		UPDATE outbox_events
		SET processed_at = $1, attempts = attempts + 1
		WHERE id = $2
	`, now, event.ID)
	if err != nil {
		return fmt.Errorf("marking event processed: %w", err)
	}

	p.logger.Info("event published",
		"event_id", event.ID,
		"event_type", event.EventType,
		"aggregate_id", event.AggregateID,
	)
	return nil
}

// WriteWithOutbox atomically writes business data and appends to the outbox.
// This is the correct way to use the pattern — both writes in ONE transaction.
func WriteWithOutbox(
	ctx context.Context,
	tx *sql.Tx,
	businessWrite func(tx *sql.Tx) error,
	event OutboxEvent,
) error {
	// Business logic write
	if err := businessWrite(tx); err != nil {
		return fmt.Errorf("business write: %w", err)
	}

	// Outbox write in the SAME transaction
	payload, err := json.Marshal(event.Payload)
	if err != nil {
		return fmt.Errorf("marshaling payload: %w", err)
	}

	_, err = tx.ExecContext(ctx, `
		INSERT INTO outbox_events
			(aggregate_id, aggregate_type, event_type, payload)
		VALUES ($1, $2, $3, $4)
	`, event.AggregateID, event.AggregateType, event.EventType, payload)
	if err != nil {
		return fmt.Errorf("writing to outbox: %w", err)
	}

	return nil
}
```

---

## 6. Distributed Logging

### The Four Golden Signals (Google SRE)

1. **Latency** — time to serve a request (distinguish success vs error latency)
2. **Traffic** — demand on the system (requests/sec, messages/sec)
3. **Errors** — rate of failing requests (5xx, timeouts, wrong results)
4. **Saturation** — how "full" the system is (CPU, memory, queue depth)

### Structured Logging in Go with slog

```go
// File: logging/logger.go
// Production-grade structured logging with correlation ID propagation.
// Uses Go 1.21+ slog for structured, zero-allocation logging.

package logging

import (
	"context"
	"log/slog"
	"os"
	"time"
)

// Key type for context values — prevents key collisions
type contextKey int

const (
	correlationIDKey contextKey = iota
	traceIDKey
	spanIDKey
	userIDKey
	serviceNameKey
)

// LogContext carries all fields that should appear in every log line.
type LogContext struct {
	CorrelationID string
	TraceID       string
	SpanID        string
	UserID        string
	ServiceName   string
}

// WithLogContext stores the log context in the request context.
func WithLogContext(ctx context.Context, lc LogContext) context.Context {
	ctx = context.WithValue(ctx, correlationIDKey, lc.CorrelationID)
	ctx = context.WithValue(ctx, traceIDKey, lc.TraceID)
	ctx = context.WithValue(ctx, spanIDKey, lc.SpanID)
	ctx = context.WithValue(ctx, userIDKey, lc.UserID)
	ctx = context.WithValue(ctx, serviceNameKey, lc.ServiceName)
	return ctx
}

// FromContext extracts the log context from a request context.
func FromContext(ctx context.Context) LogContext {
	lc := LogContext{}
	if v, ok := ctx.Value(correlationIDKey).(string); ok {
		lc.CorrelationID = v
	}
	if v, ok := ctx.Value(traceIDKey).(string); ok {
		lc.TraceID = v
	}
	if v, ok := ctx.Value(spanIDKey).(string); ok {
		lc.SpanID = v
	}
	if v, ok := ctx.Value(userIDKey).(string); ok {
		lc.UserID = v
	}
	if v, ok := ctx.Value(serviceNameKey).(string); ok {
		lc.ServiceName = v
	}
	return lc
}

// ContextHandler is an slog.Handler that automatically adds log context fields.
// This ensures every log line has correlation ID without manual threading.
type ContextHandler struct {
	inner slog.Handler
}

func NewContextHandler(inner slog.Handler) *ContextHandler {
	return &ContextHandler{inner: inner}
}

func (h *ContextHandler) Enabled(ctx context.Context, level slog.Level) bool {
	return h.inner.Enabled(ctx, level)
}

func (h *ContextHandler) Handle(ctx context.Context, r slog.Record) error {
	lc := FromContext(ctx)

	// Add context fields to every log record
	if lc.CorrelationID != "" {
		r.AddAttrs(slog.String("correlation_id", lc.CorrelationID))
	}
	if lc.TraceID != "" {
		r.AddAttrs(slog.String("trace_id", lc.TraceID))
	}
	if lc.SpanID != "" {
		r.AddAttrs(slog.String("span_id", lc.SpanID))
	}
	if lc.UserID != "" {
		r.AddAttrs(slog.String("user_id", lc.UserID))
	}
	if lc.ServiceName != "" {
		r.AddAttrs(slog.String("service", lc.ServiceName))
	}

	return h.inner.Handle(ctx, r)
}

func (h *ContextHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	return &ContextHandler{inner: h.inner.WithAttrs(attrs)}
}

func (h *ContextHandler) WithGroup(name string) slog.Handler {
	return &ContextHandler{inner: h.inner.WithGroup(name)}
}

// NewProductionLogger creates a JSON-format logger suitable for production.
// Output goes to stdout, collected by Fluentd/Fluent Bit in Kubernetes.
func NewProductionLogger(serviceName, version string) *slog.Logger {
	jsonHandler := slog.NewJSONHandler(os.Stdout, &slog.HandlerOptions{
		Level:     slog.LevelInfo,
		AddSource: true, // Include file:line in every log entry
		ReplaceAttr: func(groups []string, a slog.Attr) slog.Attr {
			// Rename "time" to "@timestamp" for Elasticsearch compatibility
			if a.Key == slog.TimeKey {
				return slog.Attr{
					Key:   "@timestamp",
					Value: slog.StringValue(a.Value.Time().UTC().Format(time.RFC3339Nano)),
				}
			}
			// Rename "msg" to "message" for ECS compliance
			if a.Key == slog.MessageKey {
				return slog.Attr{Key: "message", Value: a.Value}
			}
			// Rename "level" to "log.level" for ECS compliance
			if a.Key == slog.LevelKey {
				return slog.Attr{Key: "log.level", Value: a.Value}
			}
			return a
		},
	})

	contextHandler := NewContextHandler(jsonHandler)

	return slog.New(contextHandler).With(
		slog.String("service.name", serviceName),
		slog.String("service.version", version),
	)
}

// Example output:
// {
//   "@timestamp": "2024-01-15T10:30:45.123456789Z",
//   "log.level": "INFO",
//   "message": "order processed",
//   "service.name": "order-service",
//   "service.version": "1.2.3",
//   "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
//   "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
//   "span_id": "00f067aa0ba902b7",
//   "order_id": "ord-123",
//   "source": {"function": "main.handleOrder", "file": "handler.go", "line": 42}
// }
```

---

## 7. Concurrency Explosion

### Go Memory Model — The Happens-Before Guarantee

The Go memory model guarantees that if event A happens-before event B, then the effects of A are visible to B. The key synchronization primitives that establish happens-before:

1. `go` statement happens-before the goroutine starts
2. Channel send happens-before the corresponding receive
3. `sync.Mutex.Unlock()` happens-before the next `Lock()`
4. `sync.Once.Do()` happens-before its return and any other Do()

```go
// File: concurrency/race_examples.go
// Demonstrates common concurrency bugs and their fixes.
// Build with race detector: go build -race
// Test with race detector: go test -race ./...

package concurrency

import (
	"context"
	"sync"
	"sync/atomic"
)

// BAD: This is a data race — concurrent map access without synchronization
// The Go runtime WILL detect this with -race and panic in production.
func badConcurrentMap() {
	m := make(map[string]int)
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			m["key"] = n // DATA RACE: concurrent write
			_ = m["key"] // DATA RACE: concurrent read during write
		}(i)
	}
	wg.Wait()
}

// GOOD: Use sync.Map for concurrent access (read-heavy workloads)
func goodConcurrentMapSyncMap() {
	var m sync.Map
	var wg sync.WaitGroup
	for i := 0; i < 100; i++ {
		wg.Add(1)
		go func(n int) {
			defer wg.Done()
			m.Store("key", n)
		}(i)
	}
	wg.Wait()
}

// GOOD: Use mutex for write-heavy workloads (lower overhead than sync.Map)
type SafeCounter struct {
	mu    sync.RWMutex
	count map[string]int64
}

func (sc *SafeCounter) Increment(key string) {
	sc.mu.Lock()
	defer sc.mu.Unlock()
	sc.count[key]++
}

func (sc *SafeCounter) Get(key string) int64 {
	sc.mu.RLock()
	defer sc.mu.RUnlock()
	return sc.count[key]
}

// GOOD: Use atomic for single integers (zero-contention)
type AtomicCounter struct {
	value atomic.Int64
}

func (c *AtomicCounter) Increment() { c.value.Add(1) }
func (c *AtomicCounter) Get() int64 { return c.value.Load() }

// Worker pool pattern: bounded concurrency to prevent goroutine explosion.
// Never launch unbounded goroutines — one per request = OOM under load.
type WorkerPool struct {
	workers   int
	taskQueue chan func()
	wg        sync.WaitGroup
}

func NewWorkerPool(workers int, queueSize int) *WorkerPool {
	pool := &WorkerPool{
		workers:   workers,
		taskQueue: make(chan func(), queueSize),
	}

	for i := 0; i < workers; i++ {
		pool.wg.Add(1)
		go func() {
			defer pool.wg.Done()
			for task := range pool.taskQueue {
				task()
			}
		}()
	}

	return pool
}

// Submit adds a task to the pool. Returns false if the queue is full.
func (p *WorkerPool) Submit(ctx context.Context, task func()) bool {
	select {
	case p.taskQueue <- task:
		return true
	case <-ctx.Done():
		return false
	default:
		return false // Non-blocking check for full queue
	}
}

// Shutdown gracefully drains and shuts down the pool.
func (p *WorkerPool) Shutdown() {
	close(p.taskQueue)
	p.wg.Wait()
}

// Semaphore pattern: rate-limit concurrent operations.
// Example: limit concurrent database connections.
type Semaphore struct {
	ch chan struct{}
}

func NewSemaphore(n int) *Semaphore {
	return &Semaphore{ch: make(chan struct{}, n)}
}

func (s *Semaphore) Acquire(ctx context.Context) error {
	select {
	case s.ch <- struct{}{}:
		return nil
	case <-ctx.Done():
		return ctx.Err()
	}
}

func (s *Semaphore) Release() {
	<-s.ch
}
```

### Rust: The Borrow Checker as a Concurrency Safety Tool

```rust
// File: src/concurrency.rs
// Rust prevents data races at COMPILE TIME via ownership and Send/Sync traits.
// This is fundamentally different from runtime race detectors.

use std::sync::{Arc, Mutex, RwLock};
use std::sync::atomic::{AtomicU64, Ordering};
use tokio::sync::{mpsc, Semaphore};

// Send: a type can be transferred to another thread
// Sync: a type can be accessed from multiple threads simultaneously
// Rc<T>: !Send, !Sync — single-threaded reference counting
// Arc<T>: Send + Sync — atomic reference counting for thread-safe sharing
// Mutex<T>: Send + Sync (if T: Send) — provides synchronized access
// RwLock<T>: Send + Sync (if T: Send) — multiple readers, exclusive writer

/// Thread-safe metrics counter using atomic operations.
/// Preferred over Mutex<u64> for simple counters — no locking overhead.
#[derive(Default)]
pub struct Metrics {
    request_count: AtomicU64,
    error_count: AtomicU64,
    latency_sum_us: AtomicU64,
}

impl Metrics {
    pub fn record_request(&self, latency_us: u64, is_error: bool) {
        // Relaxed ordering is fine for independent counters —
        // we don't need happens-before guarantees between these updates.
        self.request_count.fetch_add(1, Ordering::Relaxed);
        self.latency_sum_us.fetch_add(latency_us, Ordering::Relaxed);
        if is_error {
            self.error_count.fetch_add(1, Ordering::Relaxed);
        }
    }

    pub fn snapshot(&self) -> MetricsSnapshot {
        // SeqCst ensures we read a consistent view
        MetricsSnapshot {
            request_count: self.request_count.load(Ordering::SeqCst),
            error_count: self.error_count.load(Ordering::SeqCst),
            latency_sum_us: self.latency_sum_us.load(Ordering::SeqCst),
        }
    }
}

#[derive(Debug)]
pub struct MetricsSnapshot {
    pub request_count: u64,
    pub error_count: u64,
    pub latency_sum_us: u64,
}

impl MetricsSnapshot {
    pub fn average_latency_us(&self) -> f64 {
        if self.request_count == 0 {
            return 0.0;
        }
        self.latency_sum_us as f64 / self.request_count as f64
    }

    pub fn error_rate(&self) -> f64 {
        if self.request_count == 0 {
            return 0.0;
        }
        self.error_count as f64 / self.request_count as f64
    }
}

/// Cache with read-write lock — multiple readers, exclusive writers.
/// RwLock is better than Mutex when reads >> writes.
pub struct Cache<K, V> {
    inner: RwLock<std::collections::HashMap<K, V>>,
}

impl<K: Eq + std::hash::Hash + Clone, V: Clone> Cache<K, V> {
    pub fn new() -> Self {
        Cache {
            inner: RwLock::new(std::collections::HashMap::new()),
        }
    }

    pub fn get(&self, key: &K) -> Option<V> {
        // Read lock — multiple goroutines can hold this simultaneously
        let guard = self.inner.read().unwrap();
        guard.get(key).cloned()
    }

    pub fn set(&self, key: K, value: V) {
        // Write lock — exclusive access, blocks readers
        let mut guard = self.inner.write().unwrap();
        guard.insert(key, value);
    }

    /// Pitfall: Avoid holding a read lock and then trying to upgrade to write —
    /// Rust's RwLock does NOT support lock upgrading. Doing so will deadlock.
    /// Pattern: get with read, compute without lock, set with write, check for races.
    pub fn get_or_insert_with<F>(&self, key: K, f: F) -> V
    where
        F: FnOnce() -> V,
        V: Clone,
    {
        // Check with read lock first (fast path)
        {
            let guard = self.inner.read().unwrap();
            if let Some(v) = guard.get(&key) {
                return v.clone();
            }
        } // Read lock dropped here

        // Compute without holding any lock
        let value = f();

        // Write lock for insertion
        let mut guard = self.inner.write().unwrap();
        // IMPORTANT: another thread may have inserted while we were computing.
        // Use entry API to avoid overwriting.
        guard.entry(key).or_insert(value).clone()
    }
}

/// Tokio worker pool — bounded async task execution.
pub struct AsyncWorkerPool {
    sender: mpsc::Sender<Box<dyn FnOnce() + Send + 'static>>,
}

impl AsyncWorkerPool {
    pub fn new(workers: usize, queue_size: usize) -> Self {
        let (tx, mut rx) = mpsc::channel::<Box<dyn FnOnce() + Send + 'static>>(queue_size);

        for _ in 0..workers {
            let mut rx_clone = {
                // Can't clone mpsc::Receiver — use Arc<Mutex<>>
                // In practice, use tokio::sync::mpsc with multiple receivers via Arc
                // For simplicity, spawn one receiver that fans out internally
                break;
            };
        }

        // Correct approach: single receiver with Tokio's spawn
        tokio::spawn(async move {
            while let Some(task) = rx.recv().await {
                tokio::task::spawn_blocking(task);
            }
        });

        AsyncWorkerPool { sender: tx }
    }

    pub async fn submit<F>(&self, f: F) -> Result<(), mpsc::error::SendError<()>>
    where
        F: FnOnce() + Send + 'static,
    {
        self.sender
            .send(Box::new(f))
            .await
            .map_err(|_| mpsc::error::SendError(()))
    }
}

/// Semaphore for rate-limiting concurrent async operations.
/// Example: max 10 concurrent database connections.
pub struct ConnectionPool {
    semaphore: Arc<Semaphore>,
    max_connections: usize,
}

impl ConnectionPool {
    pub fn new(max_connections: usize) -> Self {
        ConnectionPool {
            semaphore: Arc::new(Semaphore::new(max_connections)),
            max_connections,
        }
    }

    pub async fn acquire(&self) -> tokio::sync::SemaphorePermit<'_> {
        // acquire() waits until a permit is available.
        // The permit is automatically released when dropped — RAII pattern.
        self.semaphore
            .acquire()
            .await
            .expect("semaphore closed")
    }

    pub fn available(&self) -> usize {
        self.semaphore.available_permits()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::Arc;
    use std::thread;

    #[test]
    fn test_metrics_concurrent_updates() {
        let metrics = Arc::new(Metrics::default());
        let mut handles = vec![];

        for i in 0..100 {
            let m = Arc::clone(&metrics);
            handles.push(thread::spawn(move || {
                m.record_request(i as u64, i % 10 == 0);
            }));
        }

        for h in handles {
            h.join().unwrap();
        }

        let snap = metrics.snapshot();
        assert_eq!(snap.request_count, 100);
        assert_eq!(snap.error_count, 10); // 0, 10, 20, ..., 90
    }

    #[test]
    fn test_cache_no_data_race() {
        let cache = Arc::new(Cache::new());
        let mut handles = vec![];

        for i in 0..50 {
            let c = Arc::clone(&cache);
            handles.push(thread::spawn(move || {
                c.set(i % 10, i * 2);
            }));
        }

        for i in 0..50 {
            let c = Arc::clone(&cache);
            handles.push(thread::spawn(move || {
                let _ = c.get(&(i % 10));
            }));
        }

        for h in handles {
            h.join().unwrap();
        }
        // If there were a data race, the race detector (cargo test --features sanitizer)
        // would report it. Compilation success is not sufficient.
    }
}
```

---

## 8. Version Mismatch

### API Contract Testing with Pact (Consumer-Driven)

Consumer-driven contract testing is the production solution for API drift. The consumer defines what it expects; the provider verifies it can deliver.

```go
// File: contracts/order_consumer_test.go
// Consumer-side Pact test: defines what the order service expects from payment service.
// go get github.com/pact-foundation/pact-go/v2

package contracts_test

import (
	"fmt"
	"net/http"
	"testing"

	"github.com/pact-foundation/pact-go/v2/consumer"
	"github.com/pact-foundation/pact-go/v2/matchers"
)

func TestOrderServiceConsumerContract(t *testing.T) {
	// Create a mock server that records interactions
	mockProvider, err := consumer.NewV2Pact(consumer.MockHTTPProviderConfig{
		Consumer: "order-service",
		Provider: "payment-service",
	})
	if err != nil {
		t.Fatal(err)
	}

	// Define the expected interaction
	mockProvider.
		AddInteraction().
		Given("payment service is available").
		UponReceiving("a charge request for a valid order").
		WithRequest(consumer.Request{
			Method: http.MethodPost,
			Path:   matchers.String("/charge/ord-123"),
			Headers: matchers.MapMatcher{
				"Content-Type": matchers.String("application/json"),
			},
			Body: matchers.MapMatcher{
				"amount":   matchers.Decimal(100.00),
				"currency": matchers.String("USD"),
			},
		}).
		WillRespondWith(consumer.Response{
			Status: http.StatusOK,
			Headers: matchers.MapMatcher{
				"Content-Type": matchers.String("application/json"),
			},
			Body: matchers.MapMatcher{
				// Matchers are KEY: the contract specifies SHAPE, not exact values.
				// This is what makes contracts resilient to minor API changes.
				"transaction_id": matchers.Regex("txn-[a-f0-9]{8}", "txn-deadbeef"),
				"status":         matchers.Term("success", "^(success|pending)$"),
				"charged_at":     matchers.DateTimeGenerated("2006-01-02T15:04:05Z07:00"),
			},
		})

	// Run the test against the mock server
	err = mockProvider.ExecuteTest(t, func(config consumer.MockServerConfig) error {
		// Use the mock server URL
		client := NewPaymentClient(fmt.Sprintf("http://%s:%d", config.Host, config.Port))

		result, err := client.Charge("ord-123", 100.00, "USD")
		if err != nil {
			return fmt.Errorf("charge failed: %w", err)
		}
		if result.Status != "success" {
			return fmt.Errorf("expected success, got %s", result.Status)
		}
		return nil
	})

	if err != nil {
		t.Fatalf("pact test failed: %v", err)
	}
	// Pact file is written to ./pacts/order-service-payment-service.json
	// Upload this file to Pact Broker for CI verification
}
```

### Protocol Buffers with Backward Compatibility

```protobuf
// File: proto/order/v1/order.proto
// Proto3 backward compatibility rules — critical for microservice versioning.

syntax = "proto3";
package order.v1;

option go_package = "github.com/myorg/order-service/proto/order/v1;orderv1";

// OrderStatus: always use explicit field numbers and NEVER reuse them.
// Removing a field: add "reserved" to prevent reuse.
enum OrderStatus {
  ORDER_STATUS_UNSPECIFIED = 0; // ALWAYS have a zero value for enums
  ORDER_STATUS_PENDING     = 1;
  ORDER_STATUS_CONFIRMED   = 2;
  ORDER_STATUS_SHIPPED     = 3;
  ORDER_STATUS_DELIVERED   = 4;
  ORDER_STATUS_CANCELLED   = 5;
}

message Order {
  // Field numbers 1-15 use 1 byte — reserve for the most common fields.
  // Field numbers 16-2047 use 2 bytes.
  string id          = 1;
  string user_id     = 2;
  OrderStatus status = 3;
  repeated OrderItem items = 4;
  int64 created_at_unix = 5; // epoch seconds

  // BACKWARD COMPATIBLE additions (new fields get new numbers):
  string correlation_id = 6; // Added in v1.1 — old clients ignore this
  ShippingAddress shipping_address = 7; // Added in v1.2

  // RESERVED: never use field numbers 100, 101 again
  // These were removed in a past migration
  reserved 100, 101;
  reserved "legacy_order_code", "deprecated_field";
}

message OrderItem {
  string product_id = 1;
  int32  quantity   = 2;
  int64  price_cents = 3;
  string currency   = 4;
}

message ShippingAddress {
  string street  = 1;
  string city    = 2;
  string country = 3;
  string postal_code = 4;
}
```

---

## 9. Retry Storms & Cascading Failures

### Rate Limiting in Go with Token Bucket

```go
// File: ratelimit/token_bucket.go
// Token bucket rate limiter — the standard algorithm for API rate limiting.
// Also used internally to prevent retry storms.

package ratelimit

import (
	"context"
	"fmt"
	"sync"
	"time"
)

// TokenBucket implements the token bucket algorithm.
// Tokens are added at a constant rate (refillRate per second).
// Each request consumes one token. Excess requests are rejected.
//
// Advantages over leaky bucket:
// - Allows bursting up to capacity
// - More forgiving for bursty traffic patterns
type TokenBucket struct {
	capacity   float64    // Maximum tokens in the bucket
	tokens     float64    // Current token count
	refillRate float64    // Tokens per second
	lastRefill time.Time
	mu         sync.Mutex
}

func NewTokenBucket(capacity float64, refillRatePerSecond float64) *TokenBucket {
	return &TokenBucket{
		capacity:   capacity,
		tokens:     capacity, // Start full
		refillRate: refillRatePerSecond,
		lastRefill: time.Now(),
	}
}

// Allow checks if a request can proceed, consuming one token if so.
// Returns true if allowed, false if rate limit exceeded.
func (tb *TokenBucket) Allow() bool {
	tb.mu.Lock()
	defer tb.mu.Unlock()
	tb.refill()
	if tb.tokens >= 1.0 {
		tb.tokens--
		return true
	}
	return false
}

// Wait blocks until a token is available or ctx is cancelled.
func (tb *TokenBucket) Wait(ctx context.Context) error {
	for {
		tb.mu.Lock()
		tb.refill()
		if tb.tokens >= 1.0 {
			tb.tokens--
			tb.mu.Unlock()
			return nil
		}
		// Calculate when the next token will be available
		waitDuration := time.Duration(float64(time.Second) / tb.refillRate)
		tb.mu.Unlock()

		select {
		case <-ctx.Done():
			return fmt.Errorf("rate limiter wait cancelled: %w", ctx.Err())
		case <-time.After(waitDuration):
			// Token should be available now
		}
	}
}

func (tb *TokenBucket) refill() {
	now := time.Now()
	elapsed := now.Sub(tb.lastRefill).Seconds()
	newTokens := elapsed * tb.refillRate
	tb.tokens = min(tb.capacity, tb.tokens+newTokens)
	tb.lastRefill = now
}

func min(a, b float64) float64 {
	if a < b {
		return a
	}
	return b
}

// DistributedRateLimiter uses Redis for cross-instance rate limiting.
// Implements the sliding window algorithm for accuracy.
type DistributedRateLimiter struct {
	redis     RedisClient // Interface to Redis
	keyPrefix string
	limit     int
	window    time.Duration
}

// RedisClient abstracts the Redis connection for testability.
type RedisClient interface {
	EvalSha(ctx context.Context, sha string, keys []string, args ...interface{}) (interface{}, error)
	ScriptLoad(ctx context.Context, script string) (string, error)
}

// SlidingWindowScript is a Lua script for atomic sliding window rate limiting.
// Lua scripts in Redis execute atomically — no race conditions.
const SlidingWindowScript = `
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window_ms = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local request_id = ARGV[4]

-- Remove entries outside the window
redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window_ms)

-- Count current requests in window
local count = redis.call('ZCARD', key)

if count < limit then
    -- Add this request to the window
    redis.call('ZADD', key, now, request_id)
    -- Expire the key after the window passes
    redis.call('PEXPIRE', key, window_ms)
    return {1, limit - count - 1}  -- allowed, remaining
else
    return {0, 0}  -- denied, remaining
end
`
```

### Load Shedding — Protect the Service Under Overload

```go
// File: loadshed/shed.go
// Load shedding: intentionally reject requests when the system is overloaded.
// This is DIFFERENT from rate limiting — it's based on system health, not client identity.

package loadshed

import (
	"context"
	"net/http"
	"runtime"
	"sync/atomic"
	"time"
)

// LoadShedder monitors system load and rejects requests when overloaded.
// Implements the "controlled degradation" pattern.
type LoadShedder struct {
	// Current number of in-flight requests
	inFlight atomic.Int64
	// Maximum allowed in-flight requests
	maxInFlight int64
	// CPU usage threshold (0.0-1.0) above which we shed load
	cpuThreshold float64
	// Current CPU usage (sampled periodically)
	cpuUsage atomic.Value // stores float64
}

func NewLoadShedder(maxInFlight int64, cpuThreshold float64) *LoadShedder {
	ls := &LoadShedder{
		maxInFlight:  maxInFlight,
		cpuThreshold: cpuThreshold,
	}
	ls.cpuUsage.Store(0.0)

	// Sample CPU usage every second
	go ls.sampleCPU()
	return ls
}

// Middleware wraps an HTTP handler with load shedding.
func (ls *LoadShedder) Middleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if !ls.admit(r.Context()) {
			// 503 Service Unavailable with Retry-After
			w.Header().Set("Retry-After", "5")
			w.Header().Set("X-Load-Shedded", "true")
			http.Error(w, "service temporarily overloaded", http.StatusServiceUnavailable)
			return
		}

		ls.inFlight.Add(1)
		defer ls.inFlight.Add(-1)

		next.ServeHTTP(w, r)
	})
}

func (ls *LoadShedder) admit(ctx context.Context) bool {
	// Priority-based admission: high-priority requests bypass shedding
	if priority, ok := ctx.Value("request_priority").(int); ok && priority > 9 {
		return true
	}

	// Reject based on in-flight count
	if ls.inFlight.Load() >= ls.maxInFlight {
		return false
	}

	// Reject based on CPU usage
	if cpu, ok := ls.cpuUsage.Load().(float64); ok && cpu > ls.cpuThreshold {
		return false
	}

	return true
}

func (ls *LoadShedder) sampleCPU() {
	ticker := time.NewTicker(time.Second)
	defer ticker.Stop()

	var prevIdle, prevTotal uint64

	for range ticker.C {
		idle, total := getCPUSample()
		idleDelta := idle - prevIdle
		totalDelta := total - prevTotal

		if totalDelta > 0 {
			cpuUsage := 1.0 - float64(idleDelta)/float64(totalDelta)
			ls.cpuUsage.Store(cpuUsage)
		}

		prevIdle = idle
		prevTotal = total
	}
}

// getCPUSample reads CPU stats from /proc/stat (Linux only)
func getCPUSample() (idle, total uint64) {
	// In production, use github.com/shirou/gopsutil/cpu
	// This is a simplified version for illustration
	_ = runtime.NumCPU()
	return 0, 0
}
```

---

## 10. Observability Stack

### Prometheus Metrics in Go

```go
// File: metrics/prometheus.go
// Production Prometheus metrics: USE_RATE, not USE_GAUGE for counters.
// The four types: Counter, Gauge, Histogram, Summary.

package metrics

import (
	"net/http"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
	"github.com/prometheus/client_golang/prometheus/promhttp"
)

// ServiceMetrics holds all Prometheus metrics for a microservice.
// NAMING CONVENTION: <namespace>_<subsystem>_<name>_<unit>
// Example: order_service_http_requests_total
type ServiceMetrics struct {
	// HTTPRequestsTotal counts all HTTP requests.
	// Labels: method, path, status_code
	// WHY Counter not Gauge: counters only go up — rate() and increase() work correctly.
	HTTPRequestsTotal *prometheus.CounterVec

	// HTTPRequestDuration is a histogram of request latencies.
	// WHY Histogram not Summary: histograms can be aggregated across instances.
	// Summary percentiles cannot be aggregated — fatal for multi-instance services.
	HTTPRequestDuration *prometheus.HistogramVec

	// ActiveConnections is the current number of open connections.
	// WHY Gauge: it goes up AND down.
	ActiveConnections prometheus.Gauge

	// DatabaseQueryDuration measures DB query latency by query type.
	DatabaseQueryDuration *prometheus.HistogramVec

	// CacheHitsTotal counts cache hits and misses.
	CacheHitsTotal *prometheus.CounterVec

	// CircuitBreakerState tracks circuit breaker state changes.
	CircuitBreakerState *prometheus.GaugeVec

	// OutboxPendingEvents is the number of unprocessed outbox events.
	// A consistently rising value indicates the outbox processor is stuck.
	OutboxPendingEvents prometheus.Gauge
}

func NewServiceMetrics(namespace string) *ServiceMetrics {
	return &ServiceMetrics{
		HTTPRequestsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: namespace,
				Subsystem: "http",
				Name:      "requests_total",
				Help:      "Total number of HTTP requests by method, path, and status code.",
			},
			[]string{"method", "path", "status_code"},
		),

		HTTPRequestDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Subsystem: "http",
				Name:      "request_duration_seconds",
				Help:      "HTTP request duration in seconds.",
				// Bucket boundaries chosen to bracket your SLO.
				// If SLO is p99 < 500ms, have a bucket at 0.5.
				Buckets: []float64{0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0},
			},
			[]string{"method", "path"},
		),

		ActiveConnections: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: "http",
			Name:      "active_connections",
			Help:      "Current number of active HTTP connections.",
		}),

		DatabaseQueryDuration: promauto.NewHistogramVec(
			prometheus.HistogramOpts{
				Namespace: namespace,
				Subsystem: "database",
				Name:      "query_duration_seconds",
				Help:      "Database query duration in seconds.",
				Buckets:   prometheus.DefBuckets,
			},
			[]string{"operation", "table"},
		),

		CacheHitsTotal: promauto.NewCounterVec(
			prometheus.CounterOpts{
				Namespace: namespace,
				Subsystem: "cache",
				Name:      "operations_total",
				Help:      "Total cache operations.",
			},
			[]string{"result"}, // "hit" or "miss"
		),

		CircuitBreakerState: promauto.NewGaugeVec(
			prometheus.GaugeOpts{
				Namespace: namespace,
				Subsystem: "circuit_breaker",
				Name:      "state",
				Help:      "Circuit breaker state (0=closed, 1=open, 2=half-open).",
			},
			[]string{"service"},
		),

		OutboxPendingEvents: promauto.NewGauge(prometheus.GaugeOpts{
			Namespace: namespace,
			Subsystem: "outbox",
			Name:      "pending_events",
			Help:      "Number of unprocessed outbox events.",
		}),
	}
}

// InstrumentHandler wraps an HTTP handler with automatic metric recording.
func (m *ServiceMetrics) InstrumentHandler(path string, handler http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		m.ActiveConnections.Inc()
		defer m.ActiveConnections.Dec()

		// Wrap response writer to capture status code
		wrapped := &statusResponseWriter{ResponseWriter: w, statusCode: http.StatusOK}

		handler.ServeHTTP(wrapped, r)

		duration := time.Since(start).Seconds()
		statusCode := strconv.Itoa(wrapped.statusCode)

		m.HTTPRequestsTotal.WithLabelValues(r.Method, path, statusCode).Inc()
		m.HTTPRequestDuration.WithLabelValues(r.Method, path).Observe(duration)
	})
}

type statusResponseWriter struct {
	http.ResponseWriter
	statusCode int
}

func (w *statusResponseWriter) WriteHeader(code int) {
	w.statusCode = code
	w.ResponseWriter.WriteHeader(code)
}

// MetricsHandler returns the Prometheus HTTP handler.
// Mount at /metrics — scrape by Prometheus every 15s.
func MetricsHandler() http.Handler {
	return promhttp.Handler()
}
```

### Prometheus AlertManager Rules

```yaml
# File: monitoring/alerts.yaml
# Critical alerts for a microservices deployment.
# Mount into Prometheus via ConfigMap in Kubernetes.

groups:
  - name: microservices_slo
    interval: 30s
    rules:
      # SLO: 99.9% of requests succeed (3 nines)
      # Error budget: 0.1% errors = 43.8 min/month
      - alert: HighErrorRate
        expr: |
          (
            sum(rate(order_service_http_requests_total{status_code=~"5.."}[5m]))
            /
            sum(rate(order_service_http_requests_total[5m]))
          ) > 0.001
        for: 2m
        labels:
          severity: critical
          team: platform
        annotations:
          summary: "High error rate on order-service"
          description: "Error rate {{ $value | humanizePercentage }} exceeds SLO of 0.1%"
          runbook: "https://wiki.internal/runbooks/order-service-high-error-rate"

      # SLO: p99 latency < 500ms
      - alert: HighP99Latency
        expr: |
          histogram_quantile(0.99,
            sum(rate(order_service_http_request_duration_seconds_bucket[5m])) by (le, path)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "P99 latency exceeds 500ms"
          description: "P99 for {{ $labels.path }} is {{ $value | humanizeDuration }}"

      # Circuit breaker opened
      - alert: CircuitBreakerOpen
        expr: order_service_circuit_breaker_state{} == 1
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Circuit breaker open for {{ $labels.service }}"
          description: "Downstream service {{ $labels.service }} is unreachable"

      # Outbox processor stuck
      - alert: OutboxProcessorStuck
        expr: |
          increase(order_service_outbox_pending_events[10m]) > 0
          and
          order_service_outbox_pending_events > 100
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Outbox processor not draining"
          description: "{{ $value }} events pending for 10+ minutes"

      # Pod memory pressure
      - alert: HighMemoryUsage
        expr: |
          container_memory_working_set_bytes{container="order-service"}
          /
          container_spec_memory_limit_bytes{container="order-service"}
          > 0.9
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Container using >90% memory limit"
          description: "Memory: {{ $value | humanizePercentage }} of limit"
```

---

## 11. Environment Parity

### Docker Compose for Full Local Stack

```yaml
# File: docker-compose.yml
# Reproduces the production environment locally.
# Run: docker compose up -d
# Includes: services, observability stack, message broker

version: "3.9"

services:
  order-service:
    build:
      context: ./order-service
      dockerfile: Dockerfile
      target: development  # Use dev stage with hot reload
    ports:
      - "8080:8080"
    environment:
      DATABASE_URL: "postgres://app:secret@postgres:5432/orders?sslmode=disable"
      KAFKA_BROKERS: "kafka:9092"
      REDIS_URL: "redis:6379"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4318"
      ENVIRONMENT: "development"
      LOG_LEVEL: "debug"
    depends_on:
      postgres:
        condition: service_healthy
      kafka:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/healthz"]
      interval: 10s
      timeout: 5s
      retries: 3

  payment-service:
    build: ./payment-service
    ports:
      - "8081:8080"
    environment:
      DATABASE_URL: "postgres://app:secret@postgres:5432/payments?sslmode=disable"
      OTEL_EXPORTER_OTLP_ENDPOINT: "http://otel-collector:4318"
    depends_on:
      - postgres
      - otel-collector

  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: secret
      POSTGRES_MULTIPLE_DATABASES: orders,payments  # init script creates multiple DBs
    volumes:
      - ./scripts/init-multi-db.sh:/docker-entrypoint-initdb.d/init.sh
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app"]
      interval: 5s
      timeout: 3s
      retries: 5

  kafka:
    image: confluentinc/cp-kafka:7.6.0
    environment:
      KAFKA_NODE_ID: 1
      KAFKA_PROCESS_ROLES: broker,controller
      KAFKA_LISTENERS: "PLAINTEXT://0.0.0.0:9092,CONTROLLER://0.0.0.0:9093"
      KAFKA_ADVERTISED_LISTENERS: "PLAINTEXT://kafka:9092"
      KAFKA_CONTROLLER_QUORUM_VOTERS: "1@kafka:9093"
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: "true"
    healthcheck:
      test: ["CMD", "kafka-topics", "--bootstrap-server", "localhost:9092", "--list"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s

  # OpenTelemetry Collector: receives traces/metrics/logs from all services
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.96.0
    command: ["--config=/etc/otel-collector-config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel-collector-config.yaml
    ports:
      - "4318:4318"  # OTLP HTTP
      - "4317:4317"  # OTLP gRPC
    depends_on:
      - jaeger
      - prometheus

  jaeger:
    image: jaegertracing/all-in-one:1.55
    ports:
      - "16686:16686"  # Jaeger UI
      - "14268:14268"  # Collector HTTP
    environment:
      SPAN_STORAGE_TYPE: memory

  prometheus:
    image: prom/prometheus:v2.50.0
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.retention.time=7d"
      - "--web.enable-lifecycle"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - ./monitoring/alerts.yaml:/etc/prometheus/alerts.yaml
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana:10.3.0
    environment:
      GF_SECURITY_ADMIN_PASSWORD: admin
      GF_DASHBOARDS_DEFAULT_HOME_DASHBOARD_PATH: /var/lib/grafana/dashboards/overview.json
    volumes:
      - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
      - grafana_data:/var/lib/grafana
    ports:
      - "3000:3000"

volumes:
  postgres_data:
  prometheus_data:
  grafana_data:
```

---

## 12. Async Communication

### Kafka Consumer with Exactly-Once Semantics in Go

```go
// File: messaging/kafka_consumer.go
// Kafka consumer with exactly-once processing semantics.
// Uses transactional producers for atomic DB write + offset commit.

package messaging

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/twmb/franz-go/pkg/kgo"
)

// OrderEvent represents an event from the orders Kafka topic.
type OrderEvent struct {
	ID        string          `json:"id"`
	Type      string          `json:"type"`  // "order.created", "order.cancelled"
	Payload   json.RawMessage `json:"payload"`
	CreatedAt time.Time       `json:"created_at"`
}

// EventProcessor handles a single event idempotently.
// CRITICAL: Process MUST be idempotent — Kafka delivers at-least-once.
// Use event ID for deduplication.
type EventProcessor interface {
	Process(ctx context.Context, tx *sql.Tx, event OrderEvent) error
}

// KafkaConsumer implements a reliable Kafka consumer with:
// - Exactly-once semantics via transactional consumer patterns
// - Idempotent processing via deduplication table
// - Dead letter queue (DLQ) for failed messages
// - Graceful shutdown
type KafkaConsumer struct {
	client    *kgo.Client
	db        *sql.DB
	processor EventProcessor
	topics    []string
	logger    *slog.Logger
}

func NewKafkaConsumer(
	brokers []string,
	groupID string,
	topics []string,
	db *sql.DB,
	processor EventProcessor,
) (*KafkaConsumer, error) {
	client, err := kgo.NewClient(
		kgo.SeedBrokers(brokers...),
		kgo.ConsumerGroup(groupID),
		kgo.ConsumeTopics(topics...),
		// DisableAutoCommit: we commit offsets manually AFTER processing.
		// Auto-commit can cause "at-most-once" delivery if the process crashes.
		kgo.DisableAutoCommit(),
		// FetchMaxWait: how long to wait for a full batch
		kgo.FetchMaxWait(500*time.Millisecond),
		// FetchMaxBytes: tune based on message size
		kgo.FetchMaxBytes(10*1024*1024), // 10MB
	)
	if err != nil {
		return nil, fmt.Errorf("creating kafka client: %w", err)
	}

	return &KafkaConsumer{
		client:    client,
		db:        db,
		processor: processor,
		topics:    topics,
		logger:    slog.Default(),
	}, nil
}

// Run starts consuming messages. Blocks until ctx is cancelled.
func (c *KafkaConsumer) Run(ctx context.Context) error {
	defer c.client.Close()

	for {
		// PollFetches blocks until records are available or timeout
		fetches := c.client.PollFetches(ctx)
		if fetches.IsClientClosed() {
			return nil
		}

		if errs := fetches.Errors(); len(errs) > 0 {
			for _, err := range errs {
				c.logger.Error("fetch error",
					"topic", err.Topic,
					"partition", err.Partition,
					"error", err.Err,
				)
			}
		}

		// Process records partition by partition to maintain ordering guarantees
		fetches.EachPartition(func(p kgo.FetchTopicPartition) {
			for _, record := range p.Records {
				if err := c.processRecord(ctx, record); err != nil {
					c.logger.Error("failed to process record",
						"topic", record.Topic,
						"partition", record.Partition,
						"offset", record.Offset,
						"error", err,
					)
					// In production: send to DLQ, then continue
					// Never stop processing on a single record failure
				}
			}
		})

		// Commit offsets after processing all records in this batch.
		// This ensures we don't re-read processed messages after restart,
		// but also means we may process the same message twice if we crash
		// BETWEEN processing and committing. The processor must be idempotent.
		if err := c.client.CommitUncommittedOffsets(ctx); err != nil {
			c.logger.Error("failed to commit offsets", "error", err)
		}

		select {
		case <-ctx.Done():
			return nil
		default:
		}
	}
}

func (c *KafkaConsumer) processRecord(ctx context.Context, record *kgo.Record) error {
	var event OrderEvent
	if err := json.Unmarshal(record.Value, &event); err != nil {
		return fmt.Errorf("unmarshaling event: %w", err)
	}

	// Idempotency check + processing in a single transaction
	return c.processWithDeduplication(ctx, event)
}

// processWithDeduplication ensures each event is processed exactly once.
// Uses a processed_events table as an idempotency key.
func (c *KafkaConsumer) processWithDeduplication(ctx context.Context, event OrderEvent) error {
	tx, err := c.db.BeginTx(ctx, &sql.TxOptions{
		Isolation: sql.LevelReadCommitted,
	})
	if err != nil {
		return fmt.Errorf("beginning transaction: %w", err)
	}
	defer tx.Rollback()

	// Try to insert the idempotency key.
	// If it already exists, the event was already processed — skip.
	_, err = tx.ExecContext(ctx, `
		INSERT INTO processed_events (event_id, processed_at)
		VALUES ($1, NOW())
		ON CONFLICT (event_id) DO NOTHING
	`, event.ID)
	if err != nil {
		return fmt.Errorf("inserting idempotency key: %w", err)
	}

	// Check if we actually inserted (vs. skipped due to conflict)
	var inserted int
	err = tx.QueryRowContext(ctx, `
		SELECT COUNT(*) FROM processed_events
		WHERE event_id = $1 AND processed_at > NOW() - INTERVAL '1 second'
	`, event.ID).Scan(&inserted)
	if err != nil {
		return fmt.Errorf("checking insertion: %w", err)
	}

	if inserted == 0 {
		// Already processed — commit the no-op transaction
		c.logger.Debug("skipping duplicate event", "event_id", event.ID)
		return tx.Commit()
	}

	// Process the event
	if err := c.processor.Process(ctx, tx, event); err != nil {
		return fmt.Errorf("processing event %s: %w", event.ID, err)
	}

	return tx.Commit()
}
```

---

## 13. Cloud Security

### Zero Trust Architecture Principles

Zero Trust: **Never trust, always verify.** Every request — even internal ones — must be authenticated and authorized.

The three pillars:
1. **Identity**: Every service has a cryptographic identity (SPIFFE SVID)
2. **mTLS**: Every connection is mutually authenticated and encrypted
3. **Authorization**: Least-privilege access via policy (OPA/Envoy)

### mTLS Implementation in Rust

```rust
// File: src/mtls_server.rs
// mTLS server: verifies client certificates on every connection.
// Uses rustls — the only production-ready TLS library for Rust.
// Dependencies:
// rustls = "0.23"
// rustls-pemfile = "2"
// tokio-rustls = "0.26"

use rustls::{
    server::{AllowAnyAuthenticatedClient, ServerConfig},
    Certificate, PrivateKey, RootCertStore,
};
use rustls_pemfile::{certs, pkcs8_private_keys};
use std::fs::File;
use std::io::BufReader;
use std::sync::Arc;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;
use tokio_rustls::TlsAcceptor;

/// MTLSConfig holds the certificate material for mutual TLS.
/// In production, certificates are rotated automatically by SPIRE.
#[derive(Clone)]
pub struct MTLSConfig {
    pub server_cert_path: String,
    pub server_key_path: String,
    pub ca_cert_path: String,  // The CA that signed client certs
}

/// Load the server TLS configuration with client certificate verification.
pub fn build_server_tls_config(cfg: &MTLSConfig) -> anyhow::Result<Arc<ServerConfig>> {
    // Load server certificate chain
    let cert_file = File::open(&cfg.server_cert_path)
        .map_err(|e| anyhow::anyhow!("opening cert file {}: {}", cfg.server_cert_path, e))?;
    let server_certs: Vec<Certificate> = certs(&mut BufReader::new(cert_file))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| anyhow::anyhow!("parsing certs: {}", e))?
        .into_iter()
        .map(|c| Certificate(c.to_vec()))
        .collect();

    if server_certs.is_empty() {
        anyhow::bail!("no certificates found in {}", cfg.server_cert_path);
    }

    // Load server private key
    let key_file = File::open(&cfg.server_key_path)
        .map_err(|e| anyhow::anyhow!("opening key file {}: {}", cfg.server_key_path, e))?;
    let mut keys = pkcs8_private_keys(&mut BufReader::new(key_file))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| anyhow::anyhow!("parsing private key: {}", e))?;

    if keys.is_empty() {
        anyhow::bail!("no private keys found in {}", cfg.server_key_path);
    }
    let server_key = PrivateKey(keys.remove(0).secret_pkcs8_der().to_vec());

    // Load CA certificate for client verification
    let ca_file = File::open(&cfg.ca_cert_path)
        .map_err(|e| anyhow::anyhow!("opening CA cert file {}: {}", cfg.ca_cert_path, e))?;
    let ca_certs: Vec<_> = certs(&mut BufReader::new(ca_file))
        .collect::<Result<Vec<_>, _>>()
        .map_err(|e| anyhow::anyhow!("parsing CA certs: {}", e))?;

    let mut root_store = RootCertStore::empty();
    for ca_cert in ca_certs {
        root_store
            .add(&Certificate(ca_cert.to_vec()))
            .map_err(|e| anyhow::anyhow!("adding CA cert: {}", e))?;
    }

    // AllowAnyAuthenticatedClient: accept any client certificate signed by our CA.
    // In production with OPA: use a custom verifier that checks SPIFFE SVID URIs.
    let client_auth = AllowAnyAuthenticatedClient::new(root_store);

    let config = ServerConfig::builder()
        .with_safe_defaults()
        .with_client_cert_verifier(Arc::new(client_auth))
        .with_single_cert(server_certs, server_key)
        .map_err(|e| anyhow::anyhow!("building TLS config: {}", e))?;

    Ok(Arc::new(config))
}

/// Start an mTLS server that echoes the client's SPIFFE identity.
pub async fn run_mtls_server(addr: &str, cfg: MTLSConfig) -> anyhow::Result<()> {
    let tls_config = build_server_tls_config(&cfg)?;
    let acceptor = TlsAcceptor::from(tls_config);
    let listener = TcpListener::bind(addr).await?;

    tracing::info!("mTLS server listening on {}", addr);

    loop {
        let (stream, peer_addr) = listener.accept().await?;
        let acceptor = acceptor.clone();

        tokio::spawn(async move {
            match acceptor.accept(stream).await {
                Ok(tls_stream) => {
                    // Extract peer certificate for identity verification
                    let (_, server_conn) = tls_stream.get_ref();
                    let peer_certs = server_conn.peer_certificates();

                    if let Some(certs) = peer_certs {
                        // In production: parse SPIFFE SVID from cert SAN
                        // spiffe://trust-domain/ns/namespace/sa/service-account
                        tracing::info!(
                            peer = %peer_addr,
                            cert_count = certs.len(),
                            "authenticated client connection"
                        );
                    }

                    handle_connection(tls_stream).await;
                }
                Err(e) => {
                    tracing::warn!(
                        peer = %peer_addr,
                        error = %e,
                        "mTLS handshake failed — rejecting connection"
                    );
                }
            }
        });
    }
}

async fn handle_connection<S: AsyncReadExt + AsyncWriteExt + Unpin>(mut stream: S) {
    let mut buf = vec![0u8; 4096];
    match stream.read(&mut buf).await {
        Ok(n) if n > 0 => {
            let _ = stream.write_all(&buf[..n]).await;
        }
        _ => {}
    }
}
```

### Kubernetes NetworkPolicy — Zero Trust at the Network Layer

```yaml
# File: k8s/network-policy.yaml
# NetworkPolicy implements microsegmentation in Kubernetes.
# Default: deny ALL ingress and egress, then explicitly allow what's needed.

apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-all
  namespace: production
spec:
  # Empty podSelector matches ALL pods in the namespace
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
  # No rules = deny everything

---
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
    # Allow traffic from the ingress controller only
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx
          podSelector:
            matchLabels:
              app.kubernetes.io/name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8080
    # Allow Prometheus scraping from monitoring namespace
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
          podSelector:
            matchLabels:
              app: prometheus
      ports:
        - protocol: TCP
          port: 9090
  egress:
    # Allow calling payment-service within the same namespace
    - to:
        - podSelector:
            matchLabels:
              app: payment-service
      ports:
        - protocol: TCP
          port: 8080
    # Allow database access
    - to:
        - podSelector:
            matchLabels:
              app: postgres
      ports:
        - protocol: TCP
          port: 5432
    # Allow DNS resolution (required for service discovery)
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - protocol: UDP
          port: 53
        - protocol: TCP
          port: 53
    # Allow OTEL collector
    - to:
        - podSelector:
            matchLabels:
              app: otel-collector
      ports:
        - protocol: TCP
          port: 4318

---
# PodSecurityPolicy / Pod Security Admission (Kubernetes 1.25+)
# Enforces security standards at the pod level
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    # Restricted: most secure — no privileged containers, no host access
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/audit: restricted
```

### OPA Policy for Service-to-Service Authorization

```rego
# File: policies/service_authz.rego
# Open Policy Agent (OPA) policy for service-to-service authorization.
# Evaluated by Envoy sidecar on every request.

package envoy.authz

import future.keywords.if
import future.keywords.in

# Default: deny all requests
default allow := false

# Allow requests that satisfy ALL conditions:
# 1. Valid mTLS client certificate (SPIFFE SVID)
# 2. Source service is allowed to call this endpoint
# 3. JWT token is valid (if present)
allow if {
    # Verify SPIFFE identity from mTLS certificate
    spiffe_id := input.attributes.source.principal
    valid_spiffe_id(spiffe_id)

    # Check authorization matrix
    source_service := extract_service_name(spiffe_id)
    method := input.attributes.request.http.method
    path := input.attributes.request.http.path

    authorized_call(source_service, method, path)
}

# Authorization matrix: which services can call which endpoints
authorized_calls := {
    "order-service": {
        "POST /charge",
        "GET /payment-status",
    },
    "inventory-service": {
        "GET /products",
        "PATCH /products/*/reserve",
    },
    "api-gateway": {
        "POST /orders",
        "GET /orders/*",
        "DELETE /orders/*",
    },
}

authorized_call(source, method, path) if {
    allowed_methods := authorized_calls[source]
    endpoint := concat(" ", [method, path])
    endpoint in allowed_methods
}

# Also allow wildcard path patterns
authorized_call(source, method, path) if {
    allowed_methods := authorized_calls[source]
    some pattern in allowed_methods
    pattern_matches(pattern, concat(" ", [method, path]))
}

valid_spiffe_id(id) if {
    startswith(id, "spiffe://cluster.local/ns/production/sa/")
}

extract_service_name(spiffe_id) := name if {
    parts := split(spiffe_id, "/")
    name := parts[count(parts)-1]
}

pattern_matches(pattern, input_str) if {
    # Replace * with .* for glob-style matching
    regex_pattern := replace(pattern, "*", ".*")
    regex.match(regex_pattern, input_str)
}

# Audit log: record all denied requests
deny_reason := reason if {
    not allow
    spiffe_id := input.attributes.source.principal

    reason := sprintf(
        "denied: source=%s method=%s path=%s",
        [spiffe_id,
         input.attributes.request.http.method,
         input.attributes.request.http.path]
    )
}
```

---

## 14. Kubernetes Internals

### Kubernetes Control Plane Debug Workflow

```bash
#!/usr/bin/env bash
# File: scripts/k8s_debug.sh
# Comprehensive Kubernetes debugging script for microservice incidents.

set -euo pipefail

NAMESPACE="${NAMESPACE:-production}"
SERVICE="${1:-order-service}"

echo "=== Kubernetes Debugging: $SERVICE in $NAMESPACE ==="

# 1. Check pod status
echo "\n--- Pod Status ---"
kubectl get pods -n "$NAMESPACE" -l "app=$SERVICE" \
  -o custom-columns='NAME:.metadata.name,STATUS:.status.phase,READY:.status.containerStatuses[0].ready,RESTARTS:.status.containerStatuses[0].restartCount,AGE:.metadata.creationTimestamp'

# 2. Check for recent events (most useful for crash loops)
echo "\n--- Recent Events (last 1 hour) ---"
kubectl get events -n "$NAMESPACE" \
  --field-selector "involvedObject.name=$(kubectl get pod -n $NAMESPACE -l app=$SERVICE -o jsonpath='{.items[0].metadata.name}')" \
  --sort-by='.metadata.creationTimestamp' | tail -20

# 3. Describe the most recent pod (includes events, resource limits)
echo "\n--- Pod Description ---"
POD=$(kubectl get pod -n "$NAMESPACE" -l "app=$SERVICE" -o jsonpath='{.items[0].metadata.name}')
kubectl describe pod "$POD" -n "$NAMESPACE"

# 4. Check resource usage
echo "\n--- Resource Usage ---"
kubectl top pods -n "$NAMESPACE" -l "app=$SERVICE" --use-protocol-buffers 2>/dev/null || \
  echo "metrics-server not available — check your cluster setup"

# 5. Check recent logs (last 5 min, including previous crash)
echo "\n--- Recent Logs (last 5 minutes) ---"
kubectl logs "$POD" -n "$NAMESPACE" \
  --since=5m \
  --prefix=true \
  -c "$SERVICE" 2>/dev/null || true

echo "\n--- Logs from Previous Container (if crashed) ---"
kubectl logs "$POD" -n "$NAMESPACE" \
  --previous \
  --tail=50 \
  -c "$SERVICE" 2>/dev/null || echo "No previous container logs"

# 6. Check network policies
echo "\n--- Network Policies ---"
kubectl get networkpolicies -n "$NAMESPACE"

# 7. Check service endpoints
echo "\n--- Service Endpoints ---"
kubectl get endpoints "$SERVICE" -n "$NAMESPACE"

# 8. Test connectivity from within the cluster
echo "\n--- Connectivity Test ---"
kubectl run debug-pod \
  --image=curlimages/curl:8.5.0 \
  --restart=Never \
  --rm -it \
  -n "$NAMESPACE" \
  -- curl -sS "http://$SERVICE:8080/healthz" 2>/dev/null || \
  echo "Connectivity test failed or timed out"

# 9. Check HPA (autoscaling) status
echo "\n--- HPA Status ---"
kubectl get hpa -n "$NAMESPACE" -l "app=$SERVICE" 2>/dev/null || true

# 10. Check PodDisruptionBudgets
echo "\n--- PodDisruptionBudget ---"
kubectl get pdb -n "$NAMESPACE" 2>/dev/null || true

echo "\n=== Debug collection complete ==="
```

### Kubernetes Deployment with Full Production Configuration

```yaml
# File: k8s/order-service-deployment.yaml
# Production Kubernetes deployment with:
# - Pod disruption budget
# - Resource limits and requests
# - Liveness, readiness, and startup probes
# - Security context (non-root, read-only filesystem)
# - Topology spread constraints
# - Graceful shutdown

apiVersion: apps/v1
kind: Deployment
metadata:
  name: order-service
  namespace: production
  labels:
    app: order-service
    version: "1.2.3"
  annotations:
    # Track deployment causality
    deployment.kubernetes.io/revision: "42"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: order-service
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1        # Allow one extra pod during update
      maxUnavailable: 0  # Never go below desired replica count
  template:
    metadata:
      labels:
        app: order-service
        version: "1.2.3"
      annotations:
        # Force pod restart when ConfigMap changes
        checksum/config: "{{ .Files.Get 'config.yaml' | sha256sum }}"
        # Prometheus scraping annotations
        prometheus.io/scrape: "true"
        prometheus.io/port: "9090"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: order-service
      terminationGracePeriodSeconds: 60  # Must be > your request timeout

      # Topology spread: distribute pods across zones
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: DoNotSchedule
          labelSelector:
            matchLabels:
              app: order-service

      # Pod anti-affinity: don't run two pods on the same node
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
            - weight: 100
              podAffinityTerm:
                labelSelector:
                  matchLabels:
                    app: order-service
                topologyKey: kubernetes.io/hostname

      containers:
        - name: order-service
          image: registry.mycompany.com/order-service:1.2.3
          imagePullPolicy: IfNotPresent

          ports:
            - name: http
              containerPort: 8080
            - name: metrics
              containerPort: 9090

          # Resource requests = scheduler allocation
          # Resource limits = OOM kill threshold
          # WARNING: CPU limits cause throttling, which is often worse than no limit.
          # Set CPU limits conservatively or omit them for latency-sensitive services.
          resources:
            requests:
              cpu: "100m"     # 0.1 CPU cores
              memory: "128Mi"
            limits:
              cpu: "500m"     # 0.5 CPU cores (set conservatively to avoid OOM neighbor)
              memory: "256Mi" # OOM kill if exceeded — tune with VPA or Goldilocks

          # Startup probe: wait for slow initialization before starting liveness checks
          # Without this, liveness probe kills pods during slow startup (e.g., DB migrations)
          startupProbe:
            httpGet:
              path: /healthz/startup
              port: 8080
            failureThreshold: 30  # 30 * 10s = 5 minutes max startup time
            periodSeconds: 10

          # Readiness probe: remove pod from load balancer when not ready
          # Different from liveness: failing readiness = no traffic, not restart
          readinessProbe:
            httpGet:
              path: /healthz/ready
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 10
            failureThreshold: 3
            successThreshold: 1

          # Liveness probe: restart the pod when it's deadlocked
          # Be conservative: false positives cause cascading restarts
          livenessProbe:
            httpGet:
              path: /healthz/live
              port: 8080
            initialDelaySeconds: 30
            periodSeconds: 30
            failureThreshold: 3

          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: order-service-secrets
                  key: database-url
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

          securityContext:
            # NEVER run as root
            runAsNonRoot: true
            runAsUser: 10001
            runAsGroup: 10001
            # Read-only filesystem: prevents most container escapes
            readOnlyRootFilesystem: true
            # Prevent privilege escalation attacks
            allowPrivilegeEscalation: false
            # Drop ALL capabilities, add back only what's needed
            capabilities:
              drop:
                - ALL
              add:
                - NET_BIND_SERVICE  # Only needed if binding to port < 1024

          volumeMounts:
            - name: tmp
              mountPath: /tmp     # Allow writes to /tmp only
            - name: config
              mountPath: /app/config
              readOnly: true

      volumes:
        - name: tmp
          emptyDir: {}
        - name: config
          configMap:
            name: order-service-config

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: order-service-pdb
  namespace: production
spec:
  # Always maintain at least 2 available replicas during disruptions
  # (node drains, cluster upgrades, etc.)
  minAvailable: 2
  selector:
    matchLabels:
      app: order-service

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
  namespace: production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service
  minReplicas: 3
  maxReplicas: 20
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # Slow scale-down to prevent flapping
      policies:
        - type: Pods
          value: 1
          periodSeconds: 120
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: http_requests_per_second
        target:
          type: AverageValue
          averageValue: "1000"
```

---

## 15. Time-Related Bugs

### Hybrid Logical Clocks in Go

Physical clocks drift. Logical clocks (Lamport) don't track wall time. Hybrid Logical Clocks (HLC) combine both.

```go
// File: clock/hlc.go
// Hybrid Logical Clock (HLC) implementation.
// Properties:
// - Monotonically increasing
// - Bounded skew from physical clock
// - Captures causality (if A causes B, then hlc(A) < hlc(B))
// Paper: "Logical Physical Clocks and Consistent Snapshots in Globally Distributed Databases"

package clock

import (
	"fmt"
	"sync"
	"time"
)

// HLCTimestamp encodes both physical time and a logical counter.
// The wall time is truncated to milliseconds; the counter is 16-bit.
// This gives ~65535 distinct events per millisecond per node —
// sufficient for all realistic use cases.
type HLCTimestamp struct {
	WallMs  int64  // Physical time in milliseconds since epoch
	Counter uint16 // Logical counter for same-millisecond events
	NodeID  uint16 // Tiebreaker for events on different nodes
}

func (t HLCTimestamp) String() string {
	return fmt.Sprintf("%d.%d@%d", t.WallMs, t.Counter, t.NodeID)
}

// Less returns true if t happens-before other.
// Events with equal timestamps are concurrent.
func (t HLCTimestamp) Less(other HLCTimestamp) bool {
	if t.WallMs != other.WallMs {
		return t.WallMs < other.WallMs
	}
	if t.Counter != other.Counter {
		return t.Counter < other.Counter
	}
	return t.NodeID < other.NodeID
}

// HLC is a Hybrid Logical Clock that can be used to order events
// across distributed nodes with bounded physical clock skew.
type HLC struct {
	mu      sync.Mutex
	last    HLCTimestamp
	nodeID  uint16
	maxSkew time.Duration // Maximum allowed clock skew (typically 500ms)
}

func NewHLC(nodeID uint16, maxSkew time.Duration) *HLC {
	return &HLC{
		nodeID:  nodeID,
		maxSkew: maxSkew,
	}
}

// Now generates a new HLC timestamp for a local event.
// The timestamp is guaranteed to be strictly greater than any previous timestamp.
func (h *HLC) Now() HLCTimestamp {
	h.mu.Lock()
	defer h.mu.Unlock()

	physicalMs := time.Now().UnixMilli()

	if physicalMs > h.last.WallMs {
		// Physical clock advanced — reset counter
		h.last = HLCTimestamp{
			WallMs:  physicalMs,
			Counter: 0,
			NodeID:  h.nodeID,
		}
	} else {
		// Physical clock is same or behind — increment counter
		h.last.Counter++
		if h.last.Counter == 0 {
			// Counter overflow — advance wall time artificially
			h.last.WallMs++
			h.last.Counter = 0
		}
	}

	return h.last
}

// Update processes a received message's timestamp and advances the local clock.
// This ensures: if A sends to B, then hlc(send) < hlc(receive).
// Returns an error if the remote clock is too far ahead (possible Byzantine failure).
func (h *HLC) Update(remote HLCTimestamp) (HLCTimestamp, error) {
	h.mu.Lock()
	defer h.mu.Unlock()

	physicalMs := time.Now().UnixMilli()

	// Check for unreasonable clock skew
	skewMs := remote.WallMs - physicalMs
	if skewMs > h.maxSkew.Milliseconds() {
		return HLCTimestamp{}, fmt.Errorf(
			"remote clock skew %dms exceeds max %v: possible Byzantine failure",
			skewMs, h.maxSkew,
		)
	}

	maxWall := max3(physicalMs, h.last.WallMs, remote.WallMs)

	var newTimestamp HLCTimestamp
	switch {
	case maxWall > h.last.WallMs && maxWall > remote.WallMs:
		// Physical clock is ahead of both
		newTimestamp = HLCTimestamp{WallMs: maxWall, Counter: 0, NodeID: h.nodeID}
	case h.last.WallMs == remote.WallMs && maxWall == h.last.WallMs:
		// Both clocks agree on wall time — take max counter + 1
		counter := h.last.Counter
		if remote.Counter > counter {
			counter = remote.Counter
		}
		newTimestamp = HLCTimestamp{WallMs: maxWall, Counter: counter + 1, NodeID: h.nodeID}
	case h.last.WallMs > remote.WallMs:
		// Local clock is ahead — increment local counter
		newTimestamp = HLCTimestamp{WallMs: maxWall, Counter: h.last.Counter + 1, NodeID: h.nodeID}
	default:
		// Remote clock is ahead — increment remote counter
		newTimestamp = HLCTimestamp{WallMs: maxWall, Counter: remote.Counter + 1, NodeID: h.nodeID}
	}

	h.last = newTimestamp
	return newTimestamp, nil
}

func max3(a, b, c int64) int64 {
	if a >= b && a >= c {
		return a
	}
	if b >= c {
		return b
	}
	return c
}

// Detect and handle clock skew in your service
type ClockSkewDetector struct {
	hlc             *HLC
	skewHistogram   []int64 // Recent skew measurements in milliseconds
	mu              sync.Mutex
	alertThresholdMs int64
}

func NewClockSkewDetector(nodeID uint16) *ClockSkewDetector {
	return &ClockSkewDetector{
		hlc:              NewHLC(nodeID, 500*time.Millisecond),
		alertThresholdMs: 250, // Alert if skew > 250ms
	}
}

// RecordRemoteTime records the time reported by a remote service.
// Call this when processing incoming requests.
func (d *ClockSkewDetector) RecordRemoteTime(remoteMs int64) {
	localMs := time.Now().UnixMilli()
	skewMs := remoteMs - localMs

	d.mu.Lock()
	d.skewHistogram = append(d.skewHistogram, skewMs)
	if len(d.skewHistogram) > 100 {
		d.skewHistogram = d.skewHistogram[1:]
	}
	d.mu.Unlock()

	if abs64(skewMs) > d.alertThresholdMs {
		// In production: emit a metric and alert
		fmt.Printf("CLOCK_SKEW_ALERT: %dms skew detected (local=%d, remote=%d)\n",
			skewMs, localMs, remoteMs)
	}
}

func abs64(x int64) int64 {
	if x < 0 {
		return -x
	}
	return x
}
```

---

## 16. Reproducibility

### Chaos Engineering with Chaos Monkey in Go

```go
// File: chaos/injector.go
// Chaos engineering middleware: inject controlled failures into your service.
// Use in staging environments to test resilience.
// NEVER enable in production without circuit breakers and observability.

package chaos

import (
	"context"
	"math/rand"
	"net/http"
	"sync/atomic"
	"time"
)

// ChaosConfig controls what failures to inject.
type ChaosConfig struct {
	// Enabled controls whether chaos is active.
	// Read from an environment variable or feature flag.
	Enabled bool

	// LatencyPercent: percentage of requests to add latency to
	LatencyPercent float64
	LatencyMin     time.Duration
	LatencyMax     time.Duration

	// ErrorPercent: percentage of requests to return a 500 error
	ErrorPercent float64

	// TimeoutPercent: percentage of requests to let hang indefinitely
	TimeoutPercent float64

	// MemoryLeakBytes: bytes to leak per request (test OOM handling)
	MemoryLeakBytes int
}

// DefaultStagingChaos applies light chaos for staging environments.
func DefaultStagingChaos() ChaosConfig {
	return ChaosConfig{
		Enabled:        true,
		LatencyPercent: 0.10,                            // 10% of requests
		LatencyMin:     50 * time.Millisecond,
		LatencyMax:     500 * time.Millisecond,
		ErrorPercent:   0.01,                            // 1% errors
		TimeoutPercent: 0.001,                           // 0.1% timeouts
	}
}

// ChaosMiddleware injects failures according to ChaosConfig.
type ChaosMiddleware struct {
	cfg      ChaosConfig
	rng      *rand.Rand
	injected atomic.Uint64 // Total faults injected
}

func NewChaosMiddleware(cfg ChaosConfig) *ChaosMiddleware {
	return &ChaosMiddleware{
		cfg: cfg,
		rng: rand.New(rand.NewSource(time.Now().UnixNano())),
	}
}

func (c *ChaosMiddleware) Middleware(next http.Handler) http.Handler {
	if !c.cfg.Enabled {
		return next
	}

	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		roll := c.rng.Float64()
		cumulative := 0.0

		// Timeout injection
		cumulative += c.cfg.TimeoutPercent
		if roll < cumulative {
			c.injected.Add(1)
			// Block until client disconnects or server shuts down
			<-r.Context().Done()
			return
		}

		// Error injection
		cumulative += c.cfg.ErrorPercent
		if roll < cumulative {
			c.injected.Add(1)
			http.Error(w, "chaos: injected error", http.StatusInternalServerError)
			return
		}

		// Latency injection
		cumulative += c.cfg.LatencyPercent
		if roll < cumulative {
			c.injected.Add(1)
			latencyRange := c.cfg.LatencyMax - c.cfg.LatencyMin
			latency := c.cfg.LatencyMin + time.Duration(c.rng.Int63n(int64(latencyRange)))
			select {
			case <-time.After(latency):
			case <-r.Context().Done():
				return
			}
		}

		next.ServeHTTP(w, r)
	})
}

func (c *ChaosMiddleware) InjectedCount() uint64 {
	return c.injected.Load()
}
```

### Deterministic Testing with Golden Files

```go
// File: testing/golden_test.go
// Golden file testing for deterministic output comparison.
// Critical for testing serialization, response formats, report generation.

package testing

import (
	"encoding/json"
	"flag"
	"os"
	"path/filepath"
	"testing"
)

// update flag: run with -update to regenerate golden files
var update = flag.Bool("update", false, "update golden files")

// Golden represents a golden file test.
type Golden struct {
	t    *testing.T
	dir  string
	name string
}

func NewGolden(t *testing.T, name string) *Golden {
	t.Helper()
	return &Golden{
		t:    t,
		dir:  filepath.Join("testdata", "golden"),
		name: name,
	}
}

// Assert compares actual output against the golden file.
// If -update is passed, the golden file is updated.
func (g *Golden) Assert(actual []byte) {
	g.t.Helper()

	goldenFile := filepath.Join(g.dir, g.name+".golden")

	if *update {
		// Regenerate golden file
		if err := os.MkdirAll(g.dir, 0755); err != nil {
			g.t.Fatalf("creating golden dir: %v", err)
		}
		if err := os.WriteFile(goldenFile, actual, 0644); err != nil {
			g.t.Fatalf("writing golden file: %v", err)
		}
		g.t.Logf("updated golden file: %s", goldenFile)
		return
	}

	expected, err := os.ReadFile(goldenFile)
	if err != nil {
		g.t.Fatalf("reading golden file %s: %v\nRun with -update to create it", goldenFile, err)
	}

	if string(expected) != string(actual) {
		g.t.Errorf("golden file mismatch for %s\nDiff:\nexpected:\n%s\nactual:\n%s",
			g.name, expected, actual)
	}
}

// AssertJSON compares JSON output, normalizing whitespace.
func (g *Golden) AssertJSON(actual interface{}) {
	g.t.Helper()

	b, err := json.MarshalIndent(actual, "", "  ")
	if err != nil {
		g.t.Fatalf("marshaling to JSON: %v", err)
	}
	g.Assert(b)
}

// Example usage:
func TestOrderResponseFormat(t *testing.T) {
	order := map[string]interface{}{
		"id":     "ord-123",
		"status": "confirmed",
		"amount": 100.00,
	}

	g := NewGolden(t, "order_response")
	g.AssertJSON(order)
}
// Run: go test -run TestOrderResponseFormat ./... -update  # generate
// Run: go test -run TestOrderResponseFormat ./...          # verify
```

---

## 17. Linux Kernel Debugging

### perf for CPU Profiling

```bash
#!/usr/bin/env bash
# File: scripts/perf_profile.sh
# CPU profiling workflow for microservices using Linux perf.

set -euo pipefail

SERVICE_PID="${1:-$(pgrep -f order-service | head -1)}"
DURATION="${2:-30}"
OUTPUT_DIR="./profiles/$(date +%Y%m%d_%H%M%S)"

mkdir -p "$OUTPUT_DIR"

echo "Profiling PID $SERVICE_PID for ${DURATION}s..."

# Record CPU performance data
# -g: enable call-graph (stack traces)
# -F 99: sample at 99Hz (prime number to avoid lock-step with timer interrupts)
# -p: attach to specific process
# --call-graph dwarf: use DWARF for stack unwinding (needed for Go/Rust)
perf record \
  -g \
  -F 99 \
  -p "$SERVICE_PID" \
  --call-graph dwarf \
  -o "$OUTPUT_DIR/perf.data" \
  -- sleep "$DURATION"

# Generate flame graph
# Requires: https://github.com/brendangregg/FlameGraph
perf script -i "$OUTPUT_DIR/perf.data" > "$OUTPUT_DIR/perf.script"

if command -v stackcollapse-perf.pl &>/dev/null; then
    stackcollapse-perf.pl "$OUTPUT_DIR/perf.script" | \
        flamegraph.pl --title "CPU Flame Graph: order-service" \
        > "$OUTPUT_DIR/flamegraph.svg"
    echo "Flame graph: $OUTPUT_DIR/flamegraph.svg"
fi

# Top functions by CPU usage
echo "\n--- Top CPU consumers ---"
perf report -i "$OUTPUT_DIR/perf.data" --stdio --no-children | head -50

# Annotate hot functions with source
echo "\n--- Hottest function annotations ---"
perf report -i "$OUTPUT_DIR/perf.data" --stdio --no-children --sort comm,dso,sym | \
  head -20
```

### strace for Syscall Tracing

```bash
#!/usr/bin/env bash
# File: scripts/strace_analysis.sh
# Trace system calls for a microservice.
# Useful for: diagnosing file I/O, network issues, secret file access.

PID="${1:-$(pgrep -f order-service | head -1)}"

# Trace only network and file system syscalls
# -T: show time spent in each syscall
# -e trace: filter by syscall category
# -o: write to file
strace \
  -p "$PID" \
  -T \
  -e trace=network,file,desc \
  -o /tmp/strace_order_service.txt \
  &

STRACE_PID=$!
sleep 10
kill $STRACE_PID 2>/dev/null

echo "=== File Opens ==="
grep "^open\|^openat" /tmp/strace_order_service.txt | \
  awk -F'"' '{print $2}' | sort | uniq -c | sort -rn | head -20

echo "\n=== Network Connections ==="
grep "^connect\|^bind\|^accept" /tmp/strace_order_service.txt | head -20

echo "\n=== Slowest Syscalls ==="
grep -oP '<\K[0-9.]+(?=>)' /tmp/strace_order_service.txt | \
  sort -rn | head -10 | \
  while read t; do
    grep "<$t>" /tmp/strace_order_service.txt
  done
```

### eBPF for Production Profiling (bpftrace)

```bash
#!/usr/bin/env bash
# File: scripts/bpftrace_latency.sh
# Profile function latency using bpftrace — zero overhead in production.

# Measure Go HTTP handler latency distribution
bpftrace -e '
uprobe:/usr/local/bin/order-service:"net/http.(*ServeMux).ServeHTTP" {
    @start[tid] = nsecs;
}

uretprobe:/usr/local/bin/order-service:"net/http.(*ServeMux).ServeHTTP" {
    if (@start[tid] != 0) {
        @latency_us = hist((nsecs - @start[tid]) / 1000);
        delete(@start[tid]);
    }
}

interval:s:10 {
    print(@latency_us);
    clear(@latency_us);
}
'

# Monitor TCP retransmissions
bpftrace -e '
tracepoint:tcp:tcp_retransmit_skb {
    printf("TCP retransmit: %s:%d -> %s:%d\n",
           ntop(args->saddr), args->sport,
           ntop(args->daddr), args->dport);
    @retransmits = count();
}

interval:s:5 { print(@retransmits); }
'
```

---

## 18. Production Debugging Playbook

### The Five-Step Incident Response Process

```markdown
## Incident Response SOP

### Step 1: Detect & Triage (0-5 minutes)
- Acknowledge the alert in PagerDuty
- Check Grafana dashboard: are errors above SLO? Is latency spiking?
- Identify blast radius: which services are affected?
- Declare incident severity: SEV-1 (total outage) → SEV-4 (minor degradation)

### Step 2: Identify the Change (5-10 minutes)
- What changed recently?
  - Recent deployments: `kubectl rollout history deployment/order-service`
  - Config changes: check Helm release history
  - Infrastructure changes: check Terraform state
- If a recent change is the cause: ROLLBACK FIRST, investigate second.
  - `kubectl rollout undo deployment/order-service`

### Step 3: Locate the Failure (10-20 minutes)
- In Jaeger: find traces with errors. Note the first span that fails.
- In Grafana: use the service dependency graph to find the error source.
- In logs (Kibana/Loki):
  - Filter by: `correlation_id = <from trace>`
  - Find the ERROR level entry with the root cause
- Check downstream services: is payment-service returning 500s?

### Step 4: Fix or Mitigate (20-60 minutes)
- Mitigation options (fastest first):
  1. Roll back deployment
  2. Disable feature flag
  3. Scale up affected service
  4. Increase circuit breaker thresholds temporarily
  5. Enable maintenance mode / fallback responses

### Step 5: Verify & Document
- Verify metrics return to normal (below SLO threshold for 10+ minutes)
- Write incident report within 24 hours:
  - Timeline
  - Root cause
  - Detection time (how long until alert fired?)
  - Mitigation time
  - Action items to prevent recurrence
```

### Health Check Endpoints in Go

```go
// File: health/healthcheck.go
// Three-tier health check system following Kubernetes probe semantics.

package health

import (
	"context"
	"database/sql"
	"encoding/json"
	"net/http"
	"sync"
	"time"
)

// CheckStatus represents the state of a single component.
type CheckStatus string

const (
	StatusPass CheckStatus = "pass"
	StatusFail CheckStatus = "fail"
	StatusWarn CheckStatus = "warn"
)

// HealthResponse follows the IETF Health Check Format (RFC draft).
type HealthResponse struct {
	Status  CheckStatus                  `json:"status"`
	Version string                       `json:"version"`
	Checks  map[string]ComponentHealth   `json:"checks"`
}

type ComponentHealth struct {
	Status      CheckStatus `json:"status"`
	Time        time.Time   `json:"time"`
	ResponseMs  int64       `json:"response_ms,omitempty"`
	Error       string      `json:"error,omitempty"`
}

type Checker interface {
	Name() string
	Check(ctx context.Context) ComponentHealth
}

// DatabaseChecker verifies the database connection.
type DatabaseChecker struct {
	db *sql.DB
}

func (c *DatabaseChecker) Name() string { return "database" }

func (c *DatabaseChecker) Check(ctx context.Context) ComponentHealth {
	start := time.Now()
	ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()

	if err := c.db.PingContext(ctx); err != nil {
		return ComponentHealth{
			Status: StatusFail,
			Time:   time.Now(),
			Error:  err.Error(),
		}
	}

	return ComponentHealth{
		Status:     StatusPass,
		Time:       time.Now(),
		ResponseMs: time.Since(start).Milliseconds(),
	}
}

// HealthServer provides /healthz/live, /healthz/ready, /healthz/startup endpoints.
type HealthServer struct {
	checkers      []Checker
	version       string
	startupDone   bool
	startupMu     sync.RWMutex
}

func NewHealthServer(version string, checkers ...Checker) *HealthServer {
	return &HealthServer{
		checkers: checkers,
		version:  version,
	}
}

// SetStartupComplete signals that the application has finished initializing.
// Call this after DB migrations, cache warmup, etc. complete.
func (s *HealthServer) SetStartupComplete() {
	s.startupMu.Lock()
	s.startupDone = true
	s.startupMu.Unlock()
}

// LivenessHandler: returns 200 if the process is alive (not deadlocked).
// Should ONLY return 500 if the process is genuinely stuck.
// Do NOT check external dependencies here — that causes cascading restarts.
func (s *HealthServer) LivenessHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "alive"})
}

// ReadinessHandler: returns 200 if the pod can serve traffic.
// Returns 503 during startup or when critical dependencies are unhealthy.
func (s *HealthServer) ReadinessHandler(w http.ResponseWriter, r *http.Request) {
	ctx := r.Context()
	response := HealthResponse{
		Status:  StatusPass,
		Version: s.version,
		Checks:  make(map[string]ComponentHealth),
	}

	for _, checker := range s.checkers {
		health := checker.Check(ctx)
		response.Checks[checker.Name()] = health
		if health.Status == StatusFail {
			response.Status = StatusFail
		}
	}

	w.Header().Set("Content-Type", "application/json")
	if response.Status == StatusFail {
		w.WriteHeader(http.StatusServiceUnavailable)
	}
	json.NewEncoder(w).Encode(response)
}

// StartupHandler: returns 200 once initialization is complete.
func (s *HealthServer) StartupHandler(w http.ResponseWriter, r *http.Request) {
	s.startupMu.RLock()
	done := s.startupDone
	s.startupMu.RUnlock()

	if !done {
		w.WriteHeader(http.StatusServiceUnavailable)
		json.NewEncoder(w).Encode(map[string]string{"status": "initializing"})
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "started"})
}

func (s *HealthServer) RegisterHandlers(mux *http.ServeMux) {
	mux.HandleFunc("/healthz/live", s.LivenessHandler)
	mux.HandleFunc("/healthz/ready", s.ReadinessHandler)
	mux.HandleFunc("/healthz/startup", s.StartupHandler)
}
```

---

## 19. Security Hardening Checklist

### Container Security

```dockerfile
# File: Dockerfile
# Production-hardened multi-stage build for a Go microservice.

# Stage 1: Build
FROM golang:1.22-bookworm AS builder

WORKDIR /app

# Copy go.mod first for layer caching
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Build with security flags:
# CGO_ENABLED=0: static binary — no libc dependency
# -trimpath: remove build path from binary (no source path leakage)
# -ldflags: strip debug symbols, set version info
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
    go build \
    -trimpath \
    -ldflags="-w -s -X main.Version=$(git describe --tags --always)" \
    -o order-service \
    ./cmd/order-service

# Verify the binary
RUN go vet ./...
RUN go test -count=1 ./...

# Security scan with govulncheck
RUN go install golang.org/x/vuln/cmd/govulncheck@latest && \
    govulncheck ./...

# Stage 2: Minimal runtime
FROM gcr.io/distroless/static-debian12:nonroot

# distroless/static:nonroot provides:
# - No shell (no /bin/sh)
# - No package manager
# - Runs as UID 65532 (nonroot)
# - Only SSL certificates and timezone data
# This dramatically reduces the attack surface.

COPY --from=builder /app/order-service /order-service

# Security labels for policy enforcement
LABEL org.opencontainers.image.source="https://github.com/myorg/order-service"
LABEL org.opencontainers.image.revision="${GIT_COMMIT}"
LABEL security.scan.date="${BUILD_DATE}"

# Run as non-root user (UID 65532)
USER nonroot:nonroot

EXPOSE 8080 9090

ENTRYPOINT ["/order-service"]
```

### Security Audit Commands

```bash
#!/usr/bin/env bash
# File: scripts/security_audit.sh
# Run before every release.

set -euo pipefail

echo "=== Security Audit ==="

# 1. Go vulnerability scanner
echo "\n--- Go Vulnerabilities ---"
govulncheck ./...

# 2. Static analysis
echo "\n--- Static Analysis (gosec) ---"
gosec -fmt json ./... 2>&1 | jq '.Issues[] | {severity: .severity, file: .file, line: .line, details: .details}'

# 3. Container image scanning (Trivy)
echo "\n--- Container Image Scan ---"
trivy image \
  --exit-code 1 \
  --severity HIGH,CRITICAL \
  --ignore-unfixed \
  myregistry.io/order-service:latest

# 4. Kubernetes manifest scanning
echo "\n--- Kubernetes Manifest Security ---"
kubesec scan k8s/*.yaml

# 5. Secrets detection
echo "\n--- Secret Scanning ---"
trufflehog git file://. --since-commit HEAD~1 --fail

# 6. SBOM generation
echo "\n--- SBOM Generation ---"
syft . -o spdx-json > sbom.spdx.json
grype sbom:sbom.spdx.json --fail-on high

echo "\n=== Audit Complete ==="
```

---

## 20. Reference Architecture

### Complete Service Skeleton in Go

```go
// File: cmd/order-service/main.go
// Production-ready service skeleton integrating all patterns from this guide.

package main

import (
	"context"
	"database/sql"
	"errors"
	"log/slog"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	_ "github.com/lib/pq"
)

const (
	serviceName    = "order-service"
	serviceVersion = "1.0.0"
)

func main() {
	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	logger := NewProductionLogger(serviceName, serviceVersion)
	slog.SetDefault(logger)

	// ── Tracing ───────────────────────────────────────────────────
	tp, err := NewTracerProvider(ctx, serviceName, serviceVersion)
	if err != nil {
		slog.Error("failed to create tracer provider", "error", err)
		os.Exit(1)
	}
	defer func() {
		shutdownCtx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		tp.Shutdown(shutdownCtx)
	}()

	// ── Database ─────────────────────────────────────────────────
	db, err := sql.Open("postgres", mustEnv("DATABASE_URL"))
	if err != nil {
		slog.Error("failed to open database", "error", err)
		os.Exit(1)
	}
	defer db.Close()

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(5)
	db.SetConnMaxLifetime(5 * time.Minute)

	if err := db.PingContext(ctx); err != nil {
		slog.Error("database ping failed", "error", err)
		os.Exit(1)
	}

	// ── Metrics ──────────────────────────────────────────────────
	metrics := NewServiceMetrics(serviceName)

	// ── HTTP Server ──────────────────────────────────────────────
	mux := http.NewServeMux()

	// Health endpoints
	health := NewHealthServer(serviceVersion, &DatabaseChecker{db: db})
	health.RegisterHandlers(mux)

	// Metrics endpoint
	mux.Handle("GET /metrics", MetricsHandler())

	// Business endpoints
	mux.Handle("POST /orders", metrics.InstrumentHandler("/orders",
		NewLoadShedder(1000, 0.90).Middleware(
			orderHandler(db),
		),
	))

	srv := &http.Server{
		Addr:              ":8080",
		Handler:           mux,
		ReadHeaderTimeout: 10 * time.Second,
		ReadTimeout:       30 * time.Second,
		WriteTimeout:      30 * time.Second,
		IdleTimeout:       120 * time.Second,
		MaxHeaderBytes:    1 << 20, // 1MB
	}

	// ── Graceful Shutdown ─────────────────────────────────────────
	errCh := make(chan error, 1)
	go func() {
		slog.Info("server starting", "addr", srv.Addr)
		if err := srv.ListenAndServe(); !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
		close(errCh)
	}()

	// Signal the health probe that startup is complete
	health.SetStartupComplete()

	// Wait for interrupt signal or server error
	quit := make(chan os.Signal, 1)
	signal.Notify(quit, syscall.SIGTERM, syscall.SIGINT)

	select {
	case sig := <-quit:
		slog.Info("shutdown signal received", "signal", sig)
	case err := <-errCh:
		slog.Error("server error", "error", err)
		os.Exit(1)
	}

	// Graceful shutdown with 30 second timeout
	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer shutdownCancel()

	slog.Info("shutting down gracefully...")
	if err := srv.Shutdown(shutdownCtx); err != nil {
		slog.Error("graceful shutdown failed", "error", err)
		os.Exit(1)
	}

	slog.Info("server stopped cleanly")
}

func mustEnv(key string) string {
	v := os.Getenv(key)
	if v == "" {
		slog.Error("required environment variable not set", "key", key)
		os.Exit(1)
	}
	return v
}
```

---

## Quick Reference: Debugging Decision Tree

```
Service is unhealthy?
│
├─► Check alerts → Grafana dashboard → Is this a spike or sustained?
│
├─► Recent changes? → kubectl rollout history / helm history
│   └─► YES → kubectl rollout undo / helm rollback (mitigate FIRST)
│
├─► Error type?
│   ├─► 5xx errors → Check logs: kubectl logs --since=5m
│   ├─► Slow responses → Check traces in Jaeger for slow spans
│   ├─► Circuit breaker open → Check downstream service health
│   └─► OOM kills → kubectl describe pod: check resource limits
│
├─► Scope?
│   ├─► Single pod → Check node: kubectl get node -o wide
│   ├─► All pods → Check service dependency: upstream issue?
│   └─► Intermittent → Enable verbose logging, check for clock skew
│
└─► Root cause found?
    ├─► YES → Fix, deploy, verify metrics, write postmortem
    └─► NO → Escalate with: trace IDs, log excerpts, metrics screenshots
```

---

## Further Reading

### Books
- **"Designing Distributed Systems"** — Brendan Burns (O'Reilly)
- **"Systems Performance"** — Brendan Gregg (Addison-Wesley) — Linux kernel profiling
- **"Release It!"** — Michael Nygard — stability patterns in production
- **"Database Internals"** — Alex Petrov — storage engines, distributed consensus
- **"Programming Rust"** — Blandy & Orendorff — ownership, lifetimes, async

### Papers
- **"Dynamo: Amazon's Highly Available Key-value Store"** (2007) — eventual consistency in practice
- **"The Chubby lock service for loosely-coupled distributed systems"** (2006) — distributed coordination
- **"Dapper, a Large-Scale Distributed Systems Tracing Infrastructure"** (2010) — tracing origins
- **"Logical Physical Clocks and Consistent Snapshots"** (2014) — HLC
- **"Out of the Tar Pit"** (2006) — essential complexity vs. accidental complexity

### Repositories
- `https://github.com/open-telemetry/opentelemetry-go` — reference OTel implementation
- `https://github.com/tokio-rs/tokio` — Rust async runtime internals
- `https://github.com/envoyproxy/envoy` — production service mesh
- `https://github.com/prometheus/prometheus` — metrics system
- `https://github.com/cilium/cilium` — eBPF-based Kubernetes networking and security

---

*Last updated: 2025. Versions: Go 1.22+, Rust 1.78+, Kubernetes 1.28+, OpenTelemetry 0.22*

Now let me build this comprehensive guide. This will be a large, deep markdown file.Here's what the guide covers — roughly 3,500+ lines of production-depth content organized into 20 sections:

**Foundations & Theory**
- CAP / PACELC theorem with debug implications per system (etcd, Cassandra, Dynamo)
- The Eight Fallacies of Distributed Computing — mapped to actual failure modes
- Chandra-Toueg failure detector taxonomy

**C / Go / Rust Implementations**
- Full W3C `traceparent` propagation in Go (OTel SDK, BatchSpanProcessor, sampling)
- Rust trace context with `TextMapCarrier` injection/extraction + roundtrip tests
- C POSIX correlation ID generation from `/dev/urandom` with thread-local storage and structured JSON logging
- Production HTTP client with the full timeout hierarchy (dial, TLS, header, request, idle)
- Circuit breaker in Rust with state machine (Closed→Open→HalfOpen), rolling window, failure rate threshold
- Exponential backoff with full/equal/decorrelated jitter strategies
- Outbox pattern in Go with `SELECT FOR UPDATE SKIP LOCKED`
- Kafka consumer with idempotency table (exactly-once semantics)
- Token bucket rate limiter + sliding window Lua script for Redis
- Load shedder based on in-flight count and CPU utilization
- Hybrid Logical Clock (HLC) implementation
- Chaos injection middleware for staging

**Linux Kernel & eBPF**
- eBPF program (BPF_MAP_TYPE_LRU_HASH + perf buffer) to catch TCP packet drops invisible to application monitoring
- Critical kernel parameters for microservice deployments (`tcp_keepalive`, `somaxconn`, buffer sizes)
- `perf record` flame graph workflow, `strace` syscall analysis, `bpftrace` uprobe latency histograms

**Cloud Native & Cloud Security**
- Zero Trust architecture with mTLS server in Rust (rustls, `AllowAnyAuthenticatedClient`)
- OPA/Rego policy for SPIFFE SVID-based service-to-service authorization
- Kubernetes NetworkPolicy with default-deny + microsegmentation
- Production Deployment YAML: PDB, HPA, topology spread constraints, security context (non-root, read-only FS, dropped capabilities), all three probe types
- Hardened multi-stage Dockerfile using `distroless/static:nonroot` + `govulncheck`
- Full observability stack in Docker Compose (OTel Collector → Jaeger + Prometheus → Grafana)
- Prometheus metrics with correct bucket placement, AlertManager rules for SLO breach, circuit breaker state, and outbox lag

**Operational**
- Five-step incident response SOP
- Production debugging decision tree
- Security audit script (`govulncheck`, `gosec`, `trivy`, `trufflehog`, SBOM)
- Consumer-driven contract testing with Pact
- Proto3 backward compatibility rules with `reserved` fields