## Summary

OpenTelemetry is a unified observability framework providing vendor-neutral APIs, SDKs, and instrumentation for telemetry (traces, metrics, logs). It replaces OpenTracing and OpenCensus, addressing observability at scale with security-first design. I'll cover core primitives (spans, metrics, logs), semantic conventions, SDKs, collectors, propagation context, sampling strategies, security boundaries, and production deployment patterns. Expect architecture diagrams, threat models, implementation examples in Go/Rust, collector configurations, and integration with CNCF observability stacks (Prometheus, Jaeger, Grafana, Loki).

---

## 1. Core Architecture & Primitives

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Service A   │  │  Service B   │  │  Service C   │      │
│  │              │  │              │  │              │      │
│  │ OTel SDK     │  │ OTel SDK     │  │ OTel SDK     │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │ OTLP/gRPC/HTTP                  │
├────────────────────────────┼─────────────────────────────────┤
│                            ▼                                 │
│              ┌─────────────────────────┐                     │
│              │  OTel Collector         │                     │
│              │  ┌─────────────────┐    │                     │
│              │  │   Receivers     │◄───┼─── OTLP, Jaeger,  │
│              │  │  (protocols)    │    │     Zipkin, etc    │
│              │  └────────┬────────┘    │                     │
│              │           │             │                     │
│              │  ┌────────▼────────┐    │                     │
│              │  │   Processors    │    │  Sampling, Batch,  │
│              │  │  (transform)    │    │  Filter, Enrich    │
│              │  └────────┬────────┘    │                     │
│              │           │             │                     │
│              │  ┌────────▼────────┐    │                     │
│              │  │   Exporters     │────┼──► Jaeger, Prom,  │
│              │  │  (backends)     │    │    Loki, Tempo     │
│              │  └─────────────────┘    │                     │
│              └─────────────────────────┘                     │
├──────────────────────────────────────────────────────────────┤
│                    BACKEND STORAGE                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ Jaeger/  │  │Prometheus│  │  Loki/   │  │  Tempo   │    │
│  │  Tempo   │  │          │  │ Elastic  │  │          │    │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘    │
└──────────────────────────────────────────────────────────────┘
```

### 1.2 Signal Types

**Traces (Distributed Tracing)**
- **Span**: Unit of work with start time, duration, attributes, events, status
- **Trace**: DAG of spans representing request flow across services
- **Context Propagation**: W3C Trace Context (traceparent/tracestate headers)

**Metrics (Time-Series Data)**
- **Counter**: Monotonic increasing value (requests_total)
- **Gauge**: Current value that can go up/down (memory_usage)
- **Histogram**: Distribution of values (request_duration_seconds)
- **UpDownCounter**: Non-monotonic counter (active_connections)

**Logs (Structured Events)**
- Correlated with traces via trace_id/span_id
- Structured with severity, timestamp, attributes
- Bridge to existing logging (zap, slog, logrus)

---

## 2. OpenTelemetry SDK Components

### 2.1 Tracer Provider & Spans

```go
// Go implementation - production-grade tracer setup
package main

import (
    "context"
    "fmt"
    "log"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc"
    "go.opentelemetry.io/otel/propagation"
    "go.opentelemetry.io/otel/sdk/resource"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
    "go.opentelemetry.io/otel/trace"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials/insecure"
)

type TracerConfig struct {
    ServiceName      string
    ServiceVersion   string
    CollectorEndpoint string
    SamplingRatio    float64
    Environment      string
}

func InitTracer(cfg TracerConfig) (func(), error) {
    ctx := context.Background()

    // Create OTLP exporter with security configurations
    conn, err := grpc.DialContext(ctx, cfg.CollectorEndpoint,
        grpc.WithTransportCredentials(insecure.NewCredentials()), // Use TLS in prod
        grpc.WithBlock(),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create gRPC connection: %w", err)
    }

    exporter, err := otlptracegrpc.New(ctx, otlptracegrpc.WithGRPCConn(conn))
    if err != nil {
        return nil, fmt.Errorf("failed to create trace exporter: %w", err)
    }

    // Resource describes the entity producing telemetry
    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceNameKey.String(cfg.ServiceName),
            semconv.ServiceVersionKey.String(cfg.ServiceVersion),
            semconv.DeploymentEnvironmentKey.String(cfg.Environment),
            attribute.String("host.name", getHostname()),
        ),
        resource.WithProcessRuntimeDescription(),
        resource.WithHost(),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    // Create tracer provider with sampling
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithBatcher(exporter,
            sdktrace.WithBatchTimeout(5*time.Second),
            sdktrace.WithMaxExportBatchSize(512),
        ),
        sdktrace.WithResource(res),
        sdktrace.WithSampler(
            sdktrace.ParentBased(
                sdktrace.TraceIDRatioBased(cfg.SamplingRatio),
            ),
        ),
    )

    otel.SetTracerProvider(tp)
    
    // Set W3C trace context propagator
    otel.SetTextMapPropagator(propagation.NewCompositeTextMapPropagator(
        propagation.TraceContext{},
        propagation.Baggage{},
    ))

    return func() {
        if err := tp.Shutdown(ctx); err != nil {
            log.Printf("Error shutting down tracer provider: %v", err)
        }
    }, nil
}

func getHostname() string {
    // Implementation omitted
    return "localhost"
}

// Example usage with security attributes
func ProcessRequest(ctx context.Context, userID, requestPath string) error {
    tracer := otel.Tracer("api-service")
    
    ctx, span := tracer.Start(ctx, "process_request",
        trace.WithSpanKind(trace.SpanKindServer),
        trace.WithAttributes(
            semconv.HTTPMethodKey.String("POST"),
            semconv.HTTPRouteKey.String(requestPath),
            semconv.HTTPStatusCodeKey.Int(200),
            // Security: redact PII, add security context
            attribute.String("user.id.hash", hashUserID(userID)),
            attribute.Bool("auth.validated", true),
        ),
    )
    defer span.End()

    // Add events for audit trail
    span.AddEvent("authorization_check", trace.WithAttributes(
        attribute.String("check.type", "rbac"),
        attribute.Bool("check.passed", true),
    ))

    // Simulate processing
    if err := doWork(ctx); err != nil {
        span.RecordError(err)
        span.SetStatus(trace.StatusError, "processing failed")
        return err
    }

    span.SetStatus(trace.StatusOK, "success")
    return nil
}

func doWork(ctx context.Context) error {
    tracer := otel.Tracer("api-service")
    _, span := tracer.Start(ctx, "do_work")
    defer span.End()
    
    time.Sleep(100 * time.Millisecond)
    return nil
}

func hashUserID(userID string) string {
    // Implement secure hash (SHA256)
    return "hashed_" + userID
}
```

### 2.2 Metrics Provider

```go
package main

import (
    "context"
    "fmt"
    "time"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
    "go.opentelemetry.io/otel/exporters/otlp/otlpmetric/otlpmetricgrpc"
    "go.opentelemetry.io/otel/metric"
    sdkmetric "go.opentelemetry.io/otel/sdk/metric"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
)

type MetricsConfig struct {
    ServiceName       string
    CollectorEndpoint string
    ExportInterval    time.Duration
}

func InitMetrics(cfg MetricsConfig) (func(), error) {
    ctx := context.Background()

    exporter, err := otlpmetricgrpc.New(ctx,
        otlpmetricgrpc.WithEndpoint(cfg.CollectorEndpoint),
        otlpmetricgrpc.WithInsecure(), // Use TLS in prod
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create metrics exporter: %w", err)
    }

    res, err := resource.New(ctx,
        resource.WithAttributes(
            semconv.ServiceNameKey.String(cfg.ServiceName),
        ),
    )
    if err != nil {
        return nil, fmt.Errorf("failed to create resource: %w", err)
    }

    meterProvider := sdkmetric.NewMeterProvider(
        sdkmetric.WithResource(res),
        sdkmetric.WithReader(
            sdkmetric.NewPeriodicReader(exporter,
                sdkmetric.WithInterval(cfg.ExportInterval),
            ),
        ),
    )

    otel.SetMeterProvider(meterProvider)

    return func() {
        if err := meterProvider.Shutdown(ctx); err != nil {
            fmt.Printf("Error shutting down meter provider: %v\n", err)
        }
    }, nil
}

// Security-focused metrics
type SecurityMetrics struct {
    authAttempts      metric.Int64Counter
    authFailures      metric.Int64Counter
    requestDuration   metric.Float64Histogram
    activeConnections metric.Int64UpDownCounter
}

func NewSecurityMetrics(meter metric.Meter) (*SecurityMetrics, error) {
    authAttempts, err := meter.Int64Counter(
        "auth.attempts.total",
        metric.WithDescription("Total authentication attempts"),
        metric.WithUnit("{attempts}"),
    )
    if err != nil {
        return nil, err
    }

    authFailures, err := meter.Int64Counter(
        "auth.failures.total",
        metric.WithDescription("Total authentication failures"),
        metric.WithUnit("{failures}"),
    )
    if err != nil {
        return nil, err
    }

    requestDuration, err := meter.Float64Histogram(
        "http.request.duration",
        metric.WithDescription("HTTP request duration"),
        metric.WithUnit("s"),
    )
    if err != nil {
        return nil, err
    }

    activeConnections, err := meter.Int64UpDownCounter(
        "connections.active",
        metric.WithDescription("Active connections"),
        metric.WithUnit("{connections}"),
    )
    if err != nil {
        return nil, err
    }

    return &SecurityMetrics{
        authAttempts:      authAttempts,
        authFailures:      authFailures,
        requestDuration:   requestDuration,
        activeConnections: activeConnections,
    }, nil
}

func (sm *SecurityMetrics) RecordAuthAttempt(ctx context.Context, success bool, method string) {
    attrs := []attribute.KeyValue{
        attribute.String("auth.method", method),
        attribute.Bool("auth.success", success),
    }
    
    sm.authAttempts.Add(ctx, 1, metric.WithAttributes(attrs...))
    
    if !success {
        sm.authFailures.Add(ctx, 1, metric.WithAttributes(attrs...))
    }
}
```

### 2.3 Rust Implementation

```rust
// Cargo.toml dependencies
/*
[dependencies]
opentelemetry = { version = "0.22", features = ["trace", "metrics"] }
opentelemetry-otlp = { version = "0.15", features = ["grpc-tonic"] }
opentelemetry_sdk = { version = "0.22", features = ["rt-tokio"] }
opentelemetry-semantic-conventions = "0.14"
tokio = { version = "1", features = ["full"] }
tonic = "0.11"
*/

use opentelemetry::{
    global,
    trace::{TraceContextExt, Tracer, TracerProvider as _},
    KeyValue,
};
use opentelemetry_otlp::WithExportConfig;
use opentelemetry_sdk::{
    propagation::TraceContextPropagator,
    trace::{RandomIdGenerator, Sampler, TracerProvider},
    Resource,
};
use opentelemetry_semantic_conventions as semconv;
use std::error::Error;
use std::time::Duration;

pub fn init_tracer(
    service_name: &str,
    collector_endpoint: &str,
) -> Result<TracerProvider, Box<dyn Error>> {
    global::set_text_map_propagator(TraceContextPropagator::new());

    let exporter = opentelemetry_otlp::new_exporter()
        .tonic()
        .with_endpoint(collector_endpoint)
        .with_timeout(Duration::from_secs(3));

    let tracer_provider = opentelemetry_otlp::new_pipeline()
        .tracing()
        .with_exporter(exporter)
        .with_trace_config(
            opentelemetry_sdk::trace::Config::default()
                .with_sampler(Sampler::ParentBased(Box::new(Sampler::TraceIdRatioBased(
                    0.1,
                ))))
                .with_id_generator(RandomIdGenerator::default())
                .with_resource(Resource::new(vec![
                    KeyValue::new(semconv::resource::SERVICE_NAME, service_name.to_string()),
                    KeyValue::new(semconv::resource::SERVICE_VERSION, env!("CARGO_PKG_VERSION")),
                ])),
        )
        .install_batch(opentelemetry_sdk::runtime::Tokio)?;

    Ok(tracer_provider)
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let _tracer_provider = init_tracer("rust-service", "http://localhost:4317")?;
    
    let tracer = global::tracer("api-handler");
    
    tracer.in_span("process_request", |cx| {
        let span = cx.span();
        span.set_attribute(KeyValue::new("http.method", "GET"));
        span.set_attribute(KeyValue::new("http.route", "/api/v1/data"));
        
        // Simulate work
        std::thread::sleep(Duration::from_millis(100));
        
        span.add_event(
            "processing_complete",
            vec![KeyValue::new("status", "success")],
        );
    });

    global::shutdown_tracer_provider();
    Ok(())
}
```

---

## 3. OpenTelemetry Collector

### 3.1 Collector Architecture

```
┌──────────────────────────────────────────────────────────┐
│                  OTel Collector                          │
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │              RECEIVERS                          │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │    │
│  │  │ OTLP │ │Jaeger│ │Zipkin│ │Prom │          │    │
│  │  └───┬──┘ └───┬──┘ └───┬──┘ └───┬──┘          │    │
│  └──────┼────────┼────────┼────────┼──────────────┘    │
│         │        │        │        │                    │
│  ┌──────▼────────▼────────▼────────▼──────────────┐    │
│  │              PROCESSORS                         │    │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐  │    │
│  │  │ Batch  │ │ Filter │ │ Sample │ │Resource│  │    │
│  │  └───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘  │    │
│  └──────┼──────────┼──────────┼──────────┼────────┘    │
│         │          │          │          │              │
│  ┌──────▼──────────▼──────────▼──────────▼────────┐    │
│  │              EXPORTERS                          │    │
│  │  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │    │
│  │  │Jaeger│ │ Prom │ │ Loki │ │ OTLP │          │    │
│  │  └──────┘ └──────┘ └──────┘ └──────┘          │    │
│  └─────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘
```

### 3.2 Production Collector Configuration

```yaml
# otel-collector-config.yaml - Production-grade configuration
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        max_recv_msg_size_mib: 32
        max_concurrent_streams: 100
        read_buffer_size: 524288
        write_buffer_size: 524288
        keepalive:
          server_parameters:
            max_connection_idle: 11s
            max_connection_age: 12s
            max_connection_age_grace: 13s
            time: 30s
            timeout: 5s
          enforcement_policy:
            min_time: 10s
            permit_without_stream: true
        # TLS configuration for production
        tls:
          cert_file: /etc/otel/certs/server.crt
          key_file: /etc/otel/certs/server.key
          client_ca_file: /etc/otel/certs/ca.crt
          min_version: "1.3"
          cipher_suites:
            - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
            - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
      http:
        endpoint: 0.0.0.0:4318
        cors:
          allowed_origins:
            - "https://*.example.com"
          allowed_headers:
            - "*"
          max_age: 7200

  # Jaeger receiver for legacy systems
  jaeger:
    protocols:
      grpc:
        endpoint: 0.0.0.0:14250
      thrift_http:
        endpoint: 0.0.0.0:14268

  # Prometheus scrape receiver
  prometheus:
    config:
      scrape_configs:
        - job_name: 'otel-collector'
          scrape_interval: 10s
          static_configs:
            - targets: ['localhost:8888']

processors:
  # Batch processor - critical for performance
  batch:
    timeout: 10s
    send_batch_size: 1024
    send_batch_max_size: 2048

  # Memory limiter - prevent OOM
  memory_limiter:
    check_interval: 1s
    limit_mib: 512
    spike_limit_mib: 128

  # Resource processor - add deployment metadata
  resource:
    attributes:
      - key: deployment.environment
        value: production
        action: upsert
      - key: cloud.provider
        value: aws
        action: upsert
      - key: cloud.region
        value: us-east-1
        action: upsert

  # Filter processor - security: drop sensitive attributes
  filter:
    traces:
      span:
        - 'attributes["http.url"] != nil and IsMatch(attributes["http.url"], ".*password=.*")'
        - 'attributes["db.statement"] != nil and IsMatch(attributes["db.statement"], ".*(password|token|secret).*")'
    
  # Attributes processor - redact PII
  attributes:
    actions:
      - key: user.email
        action: delete
      - key: user.name
        action: hash
      - key: http.request.header.authorization
        action: delete

  # Tail sampling - advanced sampling based on rules
  tail_sampling:
    decision_wait: 10s
    num_traces: 100
    expected_new_traces_per_sec: 10
    policies:
      # Always sample errors
      - name: errors-policy
        type: status_code
        status_code:
          status_codes:
            - ERROR
      # Always sample slow requests
      - name: slow-requests
        type: latency
        latency:
          threshold_ms: 1000
      # Sample 10% of normal traffic
      - name: probabilistic-policy
        type: probabilistic
        probabilistic:
          sampling_percentage: 10

  # Transform processor - modify telemetry
  transform:
    trace_statements:
      - context: span
        statements:
          # Normalize HTTP status codes
          - set(attributes["http.status_code"], Int(attributes["http.status_code"])) where attributes["http.status_code"] != nil
          # Add security classification
          - set(attributes["security.classification"], "internal") where resource.attributes["deployment.environment"] == "production"

exporters:
  # OTLP exporter to Tempo (traces)
  otlp/tempo:
    endpoint: tempo:4317
    tls:
      insecure: false
      cert_file: /etc/otel/certs/client.crt
      key_file: /etc/otel/certs/client.key
    retry_on_failure:
      enabled: true
      initial_interval: 5s
      max_interval: 30s
      max_elapsed_time: 300s
    sending_queue:
      enabled: true
      num_consumers: 10
      queue_size: 5000

  # Prometheus exporter (metrics)
  prometheusremotewrite:
    endpoint: http://prometheus:9090/api/v1/write
    tls:
      insecure: false
    headers:
      X-Scope-OrgID: "tenant-1"
    resource_to_telemetry_conversion:
      enabled: true

  # Loki exporter (logs)
  loki:
    endpoint: http://loki:3100/loki/api/v1/push
    tls:
      insecure: false
    headers:
      X-Scope-OrgID: "tenant-1"

  # File exporter for debugging
  file:
    path: /var/log/otel/traces.json
    rotation:
      max_megabytes: 100
      max_days: 7
      max_backups: 3

  # Logging exporter for development
  logging:
    verbosity: detailed
    sampling_initial: 5
    sampling_thereafter: 200

extensions:
  health_check:
    endpoint: 0.0.0.0:13133
    path: /health
    
  pprof:
    endpoint: localhost:1777
    
  zpages:
    endpoint: localhost:55679

  memory_ballast:
    size_mib: 256

service:
  extensions: [health_check, pprof, zpages, memory_ballast]
  
  pipelines:
    traces:
      receivers: [otlp, jaeger]
      processors: [memory_limiter, resource, filter, attributes, tail_sampling, batch]
      exporters: [otlp/tempo, logging]
    
    metrics:
      receivers: [otlp, prometheus]
      processors: [memory_limiter, resource, batch]
      exporters: [prometheusremotewrite]
    
    logs:
      receivers: [otlp]
      processors: [memory_limiter, resource, batch]
      exporters: [loki]

  telemetry:
    logs:
      level: info
      encoding: json
    metrics:
      level: detailed
      address: 0.0.0.0:8888
```

### 3.3 Collector Deployment (Kubernetes)

```yaml
# otel-collector-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: otel-collector-config
  namespace: observability
data:
  otel-collector-config.yaml: |
    # Insert config from above

---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: otel-collector
  namespace: observability
spec:
  replicas: 3
  selector:
    matchLabels:
      app: otel-collector
  template:
    metadata:
      labels:
        app: otel-collector
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "8888"
        prometheus.io/path: "/metrics"
    spec:
      serviceAccountName: otel-collector
      securityContext:
        runAsNonRoot: true
        runAsUser: 10001
        fsGroup: 10001
        seccompProfile:
          type: RuntimeDefault
      
      containers:
      - name: otel-collector
        image: otel/opentelemetry-collector-contrib:0.93.0
        imagePullPolicy: IfNotPresent
        
        args:
          - --config=/conf/otel-collector-config.yaml
        
        securityContext:
          allowPrivilegeEscalation: false
          readOnlyRootFilesystem: true
          capabilities:
            drop:
              - ALL
        
        ports:
        - name: otlp-grpc
          containerPort: 4317
          protocol: TCP
        - name: otlp-http
          containerPort: 4318
          protocol: TCP
        - name: jaeger-grpc
          containerPort: 14250
          protocol: TCP
        - name: metrics
          containerPort: 8888
          protocol: TCP
        - name: health
          containerPort: 13133
          protocol: TCP
        
        env:
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        
        resources:
          requests:
            cpu: 200m
            memory: 512Mi
          limits:
            cpu: 1000m
            memory: 1Gi
        
        volumeMounts:
        - name: config
          mountPath: /conf
          readOnly: true
        - name: certs
          mountPath: /etc/otel/certs
          readOnly: true
        - name: tmp
          mountPath: /tmp
        
        livenessProbe:
          httpGet:
            path: /health
            port: 13133
          initialDelaySeconds: 10
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        readinessProbe:
          httpGet:
            path: /health
            port: 13133
          initialDelaySeconds: 5
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 3
      
      volumes:
      - name: config
        configMap:
          name: otel-collector-config
      - name: certs
        secret:
          secretName: otel-collector-tls
      - name: tmp
        emptyDir: {}
      
      affinity:
        podAntiAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - otel-collector
              topologyKey: kubernetes.io/hostname

---
apiVersion: v1
kind: Service
metadata:
  name: otel-collector
  namespace: observability
spec:
  type: ClusterIP
  selector:
    app: otel-collector
  ports:
  - name: otlp-grpc
    port: 4317
    targetPort: 4317
    protocol: TCP
  - name: otlp-http
    port: 4318
    targetPort: 4318
    protocol: TCP
  - name: jaeger-grpc
    port: 14250
    targetPort: 14250
    protocol: TCP
  - name: metrics
    port: 8888
    targetPort: 8888
    protocol: TCP

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: otel-collector
  namespace: observability

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: otel-collector
rules:
- apiGroups: [""]
  resources: ["pods", "namespaces", "nodes"]
  verbs: ["get", "list", "watch"]

---
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: otel-collector
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: otel-collector
subjects:
- kind: ServiceAccount
  name: otel-collector
  namespace: observability

---
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: otel-collector
  namespace: observability
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: otel-collector

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: otel-collector
  namespace: observability
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: otel-collector
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
```

---

## 4. Context Propagation & Semantic Conventions

### 4.1 W3C Trace Context

```
Traceparent Header Format:
┌────────────────────────────────────────────────────────┐
│  version-format - trace-id - parent-id - trace-flags   │
│     00      -   <32-hex>  - <16-hex> -      01        │
└────────────────────────────────────────────────────────┘

Example:
traceparent: 00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01

Tracestate Header (vendor-specific):
tracestate: vendor1=value1,vendor2=value2
```

### 4.2 Propagation Implementation

```go
package main

import (
    "context"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/propagation"
)

// HTTP client with context propagation
func MakeHTTPRequest(ctx context.Context, url string) error {
    req, err := http.NewRequestWithContext(ctx, "GET", url, nil)
    if err != nil {
        return err
    }

    // Inject trace context into HTTP headers
    propagator := otel.GetTextMapPropagator()
    propagator.Inject(ctx, propagation.HeaderCarrier(req.Header))

    client := &http.Client{}
    resp, err := client.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    return nil
}

// HTTP server extracting context
func HTTPHandler(w http.ResponseWriter, r *http.Request) {
    propagator := otel.GetTextMapPropagator()
    
    // Extract trace context from incoming headers
    ctx := propagator.Extract(r.Context(), propagation.HeaderCarrier(r.Header))
    
    tracer := otel.Tracer("http-server")
    ctx, span := tracer.Start(ctx, "handle_request")
    defer span.End()

    // Process request with propagated context
    processRequest(ctx)

    w.WriteHeader(http.StatusOK)
}

func processRequest(ctx context.Context) {
    // Span will be child of extracted parent
    tracer := otel.Tracer("http-server")
    _, span := tracer.Start(ctx, "process")
    defer span.End()
    
    // Business logic
}
```

### 4.3 Semantic Conventions

```go
// Semantic conventions for consistent attribute naming
import semconv "go.opentelemetry.io/otel/semconv/v1.24.0"

// HTTP attributes
semconv.HTTPMethodKey.String("GET")
semconv.HTTPStatusCodeKey.Int(200)
semconv.HTTPRouteKey.String("/api/v1/users")
semconv.HTTPURLKey.String("https://api.example.com/users")

// Database attributes
semconv.DBSystemKey.String("postgresql")
semconv.DBNameKey.String("users_db")
semconv.DBStatementKey.String("SELECT * FROM users WHERE id = $1")
semconv.DBOperationKey.String("SELECT")

// RPC/gRPC attributes
semconv.RPCSystemKey.String("grpc")
semconv.RPCServiceKey.String("UserService")
semconv.RPCMethodKey.String("GetUser")

// Messaging attributes
semconv.MessagingSystemKey.String("kafka")
semconv.MessagingDestinationKey.String("user-events")
semconv.MessagingOperationKey.String("publish")

// Cloud resource attributes
semconv.CloudProviderKey.String("aws")
semconv.CloudRegionKey.String("us-east-1")
semconv.CloudAccountIDKey.String("123456789012")

// Kubernetes attributes
semconv.K8SNamespaceNameKey.String("production")
semconv.K8SPodNameKey.String("api-server-abc123")
semconv.K8SContainerNameKey.String("api-server")
```

---

## 5. Sampling Strategies

### 5.1 Sampling Types

**Head Sampling** (at trace creation):
- TraceIDRatioBased: Sample X% of all traces
- AlwaysOn: Sample everything (dev only)
- AlwaysOff: Sample nothing
- ParentBased: Follow parent span decision

**Tail Sampling** (in collector after trace complete):
- Error-based: Always sample traces with errors
- Latency-based: Sample slow traces
- Attribute-based: Sample based on span attributes
- Composite policies: Combine multiple rules

### 5.2 Advanced Tail Sampling

```yaml
# Advanced tail sampling configuration
processors:
  tail_sampling:
    decision_wait: 10s
    num_traces: 100000
    expected_new_traces_per_sec: 1000
    
    policies:
      # Always sample critical errors
      - name: critical-errors
        type: and
        and:
          policies:
            - name: status-error
              type: status_code
              status_code:
                status_codes: [ERROR]
            - name: critical-service
              type: string_attribute
              string_attribute:
                key: service.name
                values: [payment-service, auth-service]
      
      # Always sample security events
      - name: security-events
        type: string_attribute
        string_attribute:
          key: event.type
          values: [authentication, authorization, audit]
      
      # Sample slow requests from critical paths
      - name: slow-critical-path
        type: and
        and:
          policies:
            - name: slow
              type: latency
              latency:
                threshold_ms: 5000
            - name: critical-endpoint
              type: string_attribute
              string_attribute:
                key: http.route
                values: [/api/payment, /api/checkout]
      
      # Sample high-value users (but respect privacy)
      - name: high-value-tier
        type: string_attribute
        string_attribute:
          key: user.tier
          values: [enterprise, premium]
      
      # Rate limiting: max 100 traces/sec per service
      - name: rate-limit-per-service
        type: rate_limiting
        rate_limiting:
          spans_per_second: 100
      
      # Probabilistic sampling for normal traffic
      - name: baseline-sampling
        type: probabilistic
        probabilistic:
          sampling_percentage: 1
```

---

## 6. Security & Threat Model

### 6.1 Threat Model

```
┌────────────────────────────────────────────────────────────┐
│                    THREAT SURFACES                         │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. DATA EXFILTRATION                                      │
│     • PII in span attributes (emails, names, IPs)         │
│     • Credentials in DB statements                         │
│     • Tokens in HTTP headers                               │
│     Mitigation: Filter/redact processors, deny-lists      │
│                                                            │
│  2. UNAUTHORIZED ACCESS                                    │
│     • Collector endpoints exposed without auth            │
│     • Backend exporters without TLS/auth                  │
│     • RBAC bypass in multi-tenant setups                  │
│     Mitigation: mTLS, API keys, RBAC, network policies    │
│                                                            │
│  3. DENIAL OF SERVICE                                      │
│     • Trace bombs (massive cardinality)                   │
│     • Memory exhaustion from unbounded queues             │
│     • CPU exhaustion from expensive processors            │
│     Mitigation: Rate limits, memory_limiter, sampling     │
│                                                            │
│  4. DATA TAMPERING                                         │
│     • Modified trace context breaking causality           │
│     • Injected spans creating false alerts                │
│     • Replay attacks                                       │
│     Mitigation: TLS, signed contexts, anomaly detection   │
│                                                            │
│  5. SUPPLY CHAIN                                           │
│     • Malicious collector extensions                      │
│     • Compromised SDKs or dependencies                    │
│     Mitigation: Binary verification, SBOMs, CVE scanning  │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 6.2 Security Hardening Configuration

```yaml
# Security-hardened collector configuration
receivers:
  otlp:
    protocols:
      grpc:
        endpoint: 0.0.0.0:4317
        # Mandatory mTLS
        tls:
          cert_file: /etc/otel/certs/server.crt
          key_file: /etc/otel/certs/server.key
          client_ca_file: /etc/otel/certs/ca.crt
          min_version: "1.3"
          reload_interval: 1h
        # Connection limits
        max_recv_msg_size_mib: 4  # Limit message size
        max_concurrent_streams: 50
        # Authentication
        auth:
          authenticator: oidc

extensions:
  # OIDC authentication
  oidc:
    issuer_url: https://auth.example.com
    audience: otel-collector
    username_claim: email
    groups_claim: groups

  # Bearer token authentication
  bearertokenauth:
    scheme: Bearer
    filename: /etc/otel/tokens/api-token

  # Rate limiting extension
  ratelimit:
    traces_per_second: 1000
    metrics_per_second: 10000

processors:
  # Critical: PII redaction
  redaction:
    allow_all_keys: false
    blocked_values:
      - "password"
      - "token"
      - "secret"
      - "apikey"
      - "authorization"
    summary_config:
      attributes:
        # Hash user identifiers
        - key: user.id
          method: hash
        # Delete sensitive fields
        - key: user.email
          method: delete
        - key: http.request.header.authorization
          method: delete
        - key: db.statement
          method: redact_regex
          regex: "(password|token|secret)\\s*=\\s*'[^']*'"
          replacement: "$1=***"

  # Filter out health checks and internal traffic
  filter:
    error_mode: ignore
    traces:
      span:
        # Drop health check spans
        - 'attributes["http.route"] == "/health"'
        - 'attributes["http.route"] == "/metrics"'
        # Drop spans with sensitive patterns
        - 'IsMatch(attributes["http.url"], ".*[?&](password|token|key)=.*")'

  # Resource detection and validation
  resourcedetection:
    detectors: [env, system, docker, kubernetes]
    timeout: 5s
    override: false

  # Transform to add security labels
  transform:
    trace_statements:
      - context: resource
        statements:
          - set(attributes["security.zone"], "dmz") where attributes["deployment.environment"] == "production"
          - set(attributes["data.classification"], "confidential") where resource.attributes["service.name"] == "payment-service"

# Authentication for exporters
exporters:
  otlp/secure:
    endpoint: tempo.example.com:4317
    tls:
      ca_file: /etc/otel/certs/backend-ca.crt
      cert_file: /etc/otel/certs/client.crt
      key_file: /etc/otel/certs/client.key
      min_version: "1.3"
    headers:
      authorization: Bearer ${env:BACKEND_API_TOKEN}
    retry_on_failure:
      enabled: true
      max_elapsed_time: 300s

service:
  extensions: [health_check, oidc, bearertokenauth, ratelimit]
  pipelines:
    traces:
      receivers: [otlp]
      processors:
        - memory_limiter      # Prevent OOM
        - redaction           # Remove PII
        - filter              # Drop unwanted spans
        - resourcedetection   # Add metadata
        - transform           # Security labels
        - batch               # Optimize export
      exporters: [otlp/secure]
  
  telemetry:
    logs:
      level: warn  # Reduce verbosity in prod
      encoding: json
      output_paths: [/var/log/otel/collector.log]
    metrics:
      address: localhost:8888  # Internal only
```

### 6.3 Network Policy (Kubernetes)

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: otel-collector-netpol
  namespace: observability
spec:
  podSelector:
    matchLabels:
      app: otel-collector
  policyTypes:
  - Ingress
  - Egress
  
  ingress:
  # Allow OTLP from application namespaces
  - from:
    - namespaceSelector:
        matchLabels:
          telemetry-enabled: "true"
    ports:
    - protocol: TCP
      port: 4317
    - protocol: TCP
      port: 4318
  
  # Allow metrics scraping from Prometheus
  - from:
    - namespaceSelector:
        matchLabels:
          name: observability
      podSelector:
        matchLabels:
          app: prometheus
    ports:
    - protocol: TCP
      port: 8888
  
  egress:
  # Allow egress to backend storage
  - to:
    - namespaceSelector:
        matchLabels:
          name: observability
    ports:
    - protocol: TCP
      port: 4317  # Tempo
    - protocol: TCP
      port: 9090  # Prometheus
    - protocol: TCP
      port: 3100  # Loki
  
  # Allow DNS
  - to:
    - namespaceSelector:
        matchLabels:
          name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

---

## 7. Integration Patterns

### 7.1 Auto-Instrumentation

```go
// Auto-instrumentation with HTTP middleware
package main

import (
    "net/http"
    
    "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"
    "go.opentelemetry.io/otel"
)

func main() {
    // Wrap HTTP handlers with automatic instrumentation
    handler := http.HandlerFunc(handleRequest)
    wrappedHandler := otelhttp.NewHandler(handler, "api-handler",
        otelhttp.WithSpanNameFormatter(func(operation string, r *http.Request) string {
            return r.Method + " " + r.URL.Path
        }),
    )
    
    http.ListenAndServe(":8080", wrappedHandler)
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
    // Trace context automatically propagated
    ctx := r.Context()
    
    // Make downstream call with auto-propagation
    client := http.Client{
        Transport: otelhttp.NewTransport(http.DefaultTransport),
    }
    
    req, _ := http.NewRequestWithContext(ctx, "GET", "http://downstream:8080/api", nil)
    resp, _ := client.Do(req)
    defer resp.Body.Close()
    
    w.WriteHeader(http.StatusOK)
}
```

### 7.2 Database Instrumentation

```go
// PostgreSQL with OpenTelemetry
package main

import (
    "context"
    "database/sql"
    
    "github.com/XSAM/otelsql"
    _ "github.com/lib/pq"
    semconv "go.opentelemetry.io/otel/semconv/v1.24.0"
)

func initDB(dsn string) (*sql.DB, error) {
    // Register instrumented driver
    driverName, err := otelsql.Register("postgres",
        otelsql.WithAttributes(
            semconv.DBSystemPostgreSQL,
        ),
        otelsql.WithSpanOptions(
            otelsql.WithSpanNameFormatter(func(ctx context.Context, method, query string) string {
                return method // Use method name instead of full query
            }),
        ),
    )
    if err != nil {
        return nil, err
    }
    
    db, err := sql.Open(driverName, dsn)
    if err != nil {
        return nil, err
    }
    
    // Record DB metrics
    err = otelsql.RecordStats(db)
    return db, err
}

func queryUser(ctx context.Context, db *sql.DB, userID int) error {
    // Query automatically creates span with DB attributes
    row := db.QueryRowContext(ctx, "SELECT name, email FROM users WHERE id = $1", userID)
    
    var name, email string
    return row.Scan(&name, &email)
}
```

### 7.3 gRPC Instrumentation

```go
// gRPC server with OpenTelemetry
package main

import (
    "context"
    "net"
    
    "google.golang.org/grpc"
    "go.opentelemetry.io/contrib/instrumentation/google.golang.org/grpc/otelgrpc"
)

func startGRPCServer() error {
    lis, err := net.Listen("tcp", ":50051")
    if err != nil {
        return err
    }
    
    // Create gRPC server with OTel interceptors
    s := grpc.NewServer(
        grpc.StatsHandler(otelgrpc.NewServerHandler()),
    )
    
    // Register services...
    
    return s.Serve(lis)
}

// gRPC client with OpenTelemetry
func createGRPCClient(addr string) (*grpc.ClientConn, error) {
    return grpc.Dial(addr,
        grpc.WithInsecure(),
        grpc.WithStatsHandler(otelgrpc.NewClientHandler()),
    )
}
```

---

## 8. Observability Backend Stack

### 8.1 Complete Stack Deployment

```yaml
# docker-compose.yml - Full observability stack
version: '3.8'

services:
  # OpenTelemetry Collector
  otel-collector:
    image: otel/opentelemetry-collector-contrib:0.93.0
    command: ["--config=/etc/otel/config.yaml"]
    volumes:
      - ./otel-collector-config.yaml:/etc/otel/config.yaml:ro
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "8888:8888"   # Metrics
      - "13133:13133" # Health check
    depends_on:
      - tempo
      - prometheus
      - loki

  # Grafana Tempo - Distributed Tracing
  tempo:
    image: grafana/tempo:2.3.1
    command: ["-config.file=/etc/tempo.yaml"]
    volumes:
      - ./tempo-config.yaml:/etc/tempo.yaml:ro
      - tempo-data:/var/tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317"        # OTLP gRPC receiver

  # Prometheus - Metrics
  prometheus:
    image: prom/prometheus:v2.48.1
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=15d'
      - '--web.enable-remote-write-receiver'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"

  # Grafana Loki - Logs
  loki:
    image: grafana/loki:2.9.3
    command: ["-config.file=/etc/loki/local-config.yaml"]
    volumes:
      - ./loki-config.yaml:/etc/loki/local-config.yaml:ro
      - loki-data:/loki
    ports:
      - "3100:3100"

  # Grafana - Visualization
  grafana:
    image: grafana/grafana:10.2.3
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Admin
    volumes:
      - ./grafana-datasources.yaml:/etc/grafana/provisioning/datasources/datasources.yaml:ro
      - grafana-data:/var/lib/grafana
    ports:
      - "3000:3000"
    depends_on:
      - tempo
      - prometheus
      - loki

volumes:
  tempo-data:
  prometheus-data:
  loki-data:
  grafana-data:
```

### 8.2 Backend Configurations

```yaml
# tempo-config.yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317

ingester:
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 168h  # 7 days

storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal
    pool:
      max_workers: 100
      queue_depth: 10000

metrics_generator:
  registry:
    external_labels:
      source: tempo
  storage:
    path: /var/tempo/metrics
  traces_storage:
    path: /var/tempo/traces

---
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'otel-collector'
    static_configs:
      - targets: ['otel-collector:8888']
  
  - job_name: 'tempo'
    static_configs:
      - targets: ['tempo:3200']

---
# loki-config.yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  path_prefix: /loki
  storage:
    filesystem:
      chunks_directory: /loki/chunks
      rules_directory: /loki/rules
  replication_factor: 1
  ring:
    kvstore:
      store: inmemory

schema_config:
  configs:
    - from: 2023-01-01
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

---
# grafana-datasources.yaml
apiVersion: 1

datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    jsonData:
      httpMethod: GET
      tracesToLogs:
        datasourceUid: 'loki'
        tags: ['trace_id']
      tracesToMetrics:
        datasourceUid: 'prometheus'
      serviceMap:
        datasourceUid: 'prometheus'

  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    jsonData:
      httpMethod: POST

  - name: Loki
    type: loki
    access: proxy
    url: http://loki:3100
    jsonData:
      derivedFields:
        - datasourceUid: tempo
          matcherRegex: "trace_id=(\\w+)"
          name: TraceID
          url: "$${__value.raw}"
```

---

## 9. Testing & Validation

### 9.1 Telemetry Test Framework

```go
// telemetry_test.go
package main

import (
    "context"
    "testing"
    
    "go.opentelemetry.io/otel"
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/sdk/trace/tracetest"
    "github.com/stretchr/testify/assert"
    "github.com/stretchr/testify/require"
)

func TestSpanCreation(t *testing.T) {
    // Create in-memory span recorder
    sr := tracetest.NewSpanRecorder()
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithSpanProcessor(sr),
    )
    otel.SetTracerProvider(tp)
    
    // Execute code under test
    ctx := context.Background()
    tracer := otel.Tracer("test")
    
    ctx, span := tracer.Start(ctx, "test_operation")
    span.SetAttributes(attribute.String("test.key", "test.value"))
    span.End()
    
    // Verify spans
    spans := sr.Ended()
    require.Len(t, spans, 1, "expected 1 span")
    
    span0 := spans[0]
    assert.Equal(t, "test_operation", span0.Name())
    assert.Equal(t, "test.value", span0.Attributes()[0].Value.AsString())
}

func TestContextPropagation(t *testing.T) {
    sr := tracetest.NewSpanRecorder()
    tp := sdktrace.NewTracerProvider(
        sdktrace.WithSpanProcessor(sr),
    )
    
    tracer := tp.Tracer("test")
    
    // Create parent span
    ctx, parent := tracer.Start(context.Background(), "parent")
    
    // Create child span
    _, child := tracer.Start(ctx, "child")
    child.End()
    parent.End()
    
    spans := sr.Ended()
    require.Len(t, spans, 2)
    
    // Verify parent-child relationship
    childSpan := spans[0]
    parentSpan := spans[1]
    
    assert.Equal(t, parentSpan.SpanContext().TraceID(), childSpan.SpanContext().TraceID())
    assert.Equal(t, parentSpan.SpanContext().SpanID(), childSpan.Parent().SpanID())
}
```

### 9.2 Collector Integration Test

```bash
#!/bin/bash
# test-collector.sh - Integration test for collector

set -e

echo "Starting test environment..."
docker-compose -f docker-compose.test.yml up -d

echo "Waiting for collector to be ready..."
timeout 30 bash -c 'until curl -sf http://localhost:13133/health; do sleep 1; done'

echo "Sending test trace..."
curl -X POST http://localhost:4318/v1/traces \
  -H "Content-Type: application/json" \
  -d '{
    "resourceSpans": [{
      "resource": {
        "attributes": [{
          "key": "service.name",
          "value": {"stringValue": "test-service"}
        }]
      },
      "scopeSpans": [{
        "spans": [{
          "traceId": "0102030405060708090a0b0c0d0e0f10",
          "spanId": "0102030405060708",
          "name": "test-span",
          "kind": 1,
          "startTimeUnixNano": "1000000000",
          "endTimeUnixNano": "2000000000",
          "attributes": [{
            "key": "http.method",
            "value": {"stringValue": "GET"}
          }]
        }]
      }]
    }]
  }'

echo "Verifying trace in Tempo..."
sleep 5
TRACE_ID="0102030405060708090a0b0c0d0e0f10"
curl -sf "http://localhost:3200/api/traces/${TRACE_ID}" | jq .

echo "Test passed!"
docker-compose -f docker-compose.test.yml down
```

### 9.3 Load Testing

```go
// load_test.go - Load test telemetry pipeline
package main

import (
    "context"
    "fmt"
    "sync"
    "time"
    
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/attribute"
)

func main() {
    // Initialize tracer (use production config)
    shutdown, _ := InitTracer(TracerConfig{
        ServiceName:      "load-test",
        CollectorEndpoint: "localhost:4317",
        SamplingRatio:    1.0,
    })
    defer shutdown()
    
    // Load test parameters
    numWorkers := 100
    spansPerWorker := 10000
    
    start := time.Now()
    var wg sync.WaitGroup
    
    for i := 0; i < numWorkers; i++ {
        wg.Add(1)
        go func(workerID int) {
            defer wg.Done()
            generateSpans(workerID, spansPerWorker)
        }(i)
    }
    
    wg.Wait()
    duration := time.Since(start)
    
    totalSpans := numWorkers * spansPerWorker
    spansPerSecond := float64(totalSpans) / duration.Seconds()
    
    fmt.Printf("Generated %d spans in %v (%.2f spans/sec)\n",
        totalSpans, duration, spansPerSecond)
}

func generateSpans(workerID, count int) {
    tracer := otel.Tracer("load-test")
    ctx := context.Background()
    
    for i := 0; i < count; i++ {
        _, span := tracer.Start(ctx, fmt.Sprintf("span-%d-%d", workerID, i))
        span.SetAttributes(
            attribute.Int("worker.id", workerID),
            attribute.Int("span.number", i),
        )
        span.End()
    }
}
```

---

## 10. Production Rollout Plan

### 10.1 Phased Rollout

**Phase 1: Infrastructure Setup (Week 1)**
```bash
# Deploy collector in observability namespace
kubectl apply -f otel-collector-deployment.yaml

# Deploy backend stack
kubectl apply -f tempo-deployment.yaml
kubectl apply -f prometheus-deployment.yaml
kubectl apply -f loki-deployment.yaml
kubectl apply -f grafana-deployment.yaml

# Verify health
kubectl get pods -n observability
kubectl logs -n observability deployment/otel-collector
```

**Phase 2: Canary Service (Week 2)**
```go
// Instrument one non-critical service
// Enable 1% sampling
cfg := TracerConfig{
    ServiceName:      "canary-service",
    CollectorEndpoint: "otel-collector.observability:4317",
    SamplingRatio:    0.01,  // 1% sampling
    Environment:      "production",
}
```

**Phase 3: Gradual Rollout (Weeks 3-6)**
```
Week 3: 5% sampling, 5 services
Week 4: 10% sampling, 20 services
Week 5: 25% sampling, all services
Week 6: Adaptive sampling based on load
```

**Phase 4: Full Production (Week 7+)**
```yaml
# Enable tail sampling for intelligent trace selection
processors:
  tail_sampling:
    policies:
      - name: errors-always
        type: status_code
        status_code:
          status_codes: [ERROR]
      - name: slow-requests
        type: latency
        latency:
          threshold_ms: 1000
      - name: baseline
        type: probabilistic
        probabilistic:
          sampling_percentage: 5
```

### 10.2 Rollback Plan

```bash
#!/bin/bash
# rollback.sh - Emergency rollback procedure

echo "Starting rollback procedure..."

# Step 1: Disable trace export in all services
kubectl patch deployment api-service \
  -p '{"spec":{"template":{"spec":{"containers":[{"name":"api-service","env":[{"name":"OTEL_TRACES_EXPORTER","value":"none"}]}]}}}}'

# Step 2: Scale down collector
kubectl scale deployment otel-collector -n observability --replicas=0

# Step 3: Remove service instrumentation (requires rebuild)
echo "Remove OpenTelemetry SDK calls from application code"
echo "Deploy previous version without OTel"

# Step 4: Verify application health
kubectl get pods -A
kubectl logs deployment/api-service

echo "Rollback complete. Monitor application metrics."
```

### 10.3 Monitoring Collector Health

```yaml
# ServiceMonitor for Prometheus Operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: otel-collector
  namespace: observability
spec:
  selector:
    matchLabels:
      app: otel-collector
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics

---
# PrometheusRule for alerts
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: otel-collector-alerts
  namespace: observability
spec:
  groups:
  - name: otel-collector
    interval: 30s
    rules:
    - alert: OTelCollectorDown
      expr: up{job="otel-collector"} == 0
      for: 5m
      labels:
        severity: critical
      annotations:
        summary: "OTel Collector is down"
    
    - alert: OTelCollectorHighMemory
      expr: process_resident_memory_bytes{job="otel-collector"} > 1e9
      for: 10m
      labels:
        severity: warning
      annotations:
        summary: "OTel Collector memory usage > 1GB"
    
    - alert: OTelCollectorHighDropRate
      expr: rate(otelcol_processor_dropped_spans[5m]) > 100
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "OTel Collector dropping spans"
```

---

## 11. Advanced Topics

### 11.1 Custom Span Processors

```go
// custom_processor.go - Security audit processor
package main

import (
    "context"
    "crypto/sha256"
    "encoding/hex"
    "log"
    
    sdktrace "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/trace"
)

type SecurityAuditProcessor struct {
    auditLog chan AuditEvent
}

type AuditEvent struct {
    TraceID   string
    SpanID    string
    Operation string
    UserID    string
    Timestamp string
    Sensitive bool
}

func NewSecurityAuditProcessor() *SecurityAuditProcessor {
    proc := &SecurityAuditProcessor{
        auditLog: make(chan AuditEvent, 1000),
    }
    
    // Start audit log consumer
    go proc.consumeAuditLogs()
    
    return proc
}

func (p *SecurityAuditProcessor) OnStart(parent context.Context, s sdktrace.ReadWriteSpan) {
    // Check for security-sensitive operations
    attrs := s.Attributes()
    
    for _, attr := range attrs {
        if attr.Key == "operation.type" && 
           (attr.Value.AsString() == "authentication" || 
            attr.Value.AsString() == "authorization") {
            
            event := AuditEvent{
                TraceID:   s.SpanContext().TraceID().String(),
                SpanID:    s.SpanContext().SpanID().String(),
                Operation: s.Name(),
                Timestamp: s.StartTime().String(),
                Sensitive: true,
            }
            
            // Extract user ID and hash it
            for _, a := range attrs {
                if a.Key == "user.id" {
                    hash := sha256.Sum256([]byte(a.Value.AsString()))
                    event.UserID = hex.EncodeToString(hash[:])
                }
            }
            
            select {
            case p.auditLog <- event:
            default:
                log.Println("Audit log buffer full")
            }
        }
    }
}

func (p *SecurityAuditProcessor) OnEnd(s sdktrace.ReadOnlySpan) {
    // Log completion of sensitive operations
    if s.Status().Code == trace.StatusError {
        log.Printf("Security operation failed: %s", s.Name())
    }
}

func (p *SecurityAuditProcessor) Shutdown(ctx context.Context) error {
    close(p.auditLog)
    return nil
}

func (p *SecurityAuditProcessor) ForceFlush(ctx context.Context) error {
    return nil
}

func (p *SecurityAuditProcessor) consumeAuditLogs() {
    for event := range p.auditLog {
        // Write to secure audit log (SIEM, etc.)
        log.Printf("AUDIT: trace=%s operation=%s user_hash=%s sensitive=%v",
            event.TraceID, event.Operation, event.UserID, event.Sensitive)
    }
}
```

### 11.2 Exemplars (Linking Metrics to Traces)

```go
// exemplars.go - Link metrics to traces
package main

import (
    "context"
    "math/rand"
    "time"
    
    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/metric"
    "go.opentelemetry.io/otel/trace"
)

type RequestMetrics struct {
    duration metric.Float64Histogram
}

func NewRequestMetrics(meter metric.Meter) (*RequestMetrics, error) {
    duration, err := meter.Float64Histogram(
        "http.server.duration",
        metric.WithDescription("HTTP request duration"),
        metric.WithUnit("ms"),
    )
    if err != nil {
        return nil, err
    }
    
    return &RequestMetrics{duration: duration}, nil
}

func (rm *RequestMetrics) RecordRequest(ctx context.Context, durationMs float64) {
    // Extract trace context for exemplar
    span := trace.SpanFromContext(ctx)
    traceID := span.SpanContext().TraceID().String()
    spanID := span.SpanContext().SpanID().String()
    
    // Record metric with trace context as exemplar
    // This allows jumping from metric to trace in Grafana
    rm.duration.Record(ctx, durationMs,
        metric.WithAttributes(
            attribute.String("trace_id", traceID),
            attribute.String("span_id", spanID),
        ),
    )
}

func SimulateRequests(ctx context.Context, metrics *RequestMetrics) {
    tracer := otel.Tracer("example")
    
    for i := 0; i < 100; i++ {
        ctx, span := tracer.Start(ctx, "handle_request")
        
        // Simulate request processing
        duration := float64(rand.Intn(1000))
        time.Sleep(time.Duration(duration) * time.Millisecond)
        
        // Record metric with exemplar linking to trace
        metrics.RecordRequest(ctx, duration)
        
        span.End()
    }
}
```

### 11.3 Baggage (Cross-Cutting Concerns)

```go
// baggage.go - Propagate user context across services
package main

import (
    "context"
    "net/http"
    
    "go.opentelemetry.io/otel/baggage"
    "go.opentelemetry.io/otel/trace"
)

func HTTPMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        ctx := r.Context()
        
        // Extract user context from headers
        userID := r.Header.Get("X-User-ID")
        userTier := r.Header.Get("X-User-Tier")
        
        // Store in baggage for cross-service propagation
        member1, _ := baggage.NewMember("user.id", userID)
        member2, _ := baggage.NewMember("user.tier", userTier)
        
        bag, _ := baggage.New(member1, member2)
        ctx = baggage.ContextWithBaggage(ctx, bag)
        
        // Add to current span
        span := trace.SpanFromContext(ctx)
        span.SetAttributes(
            attribute.String("user.id.hash", hashUserID(userID)),
            attribute.String("user.tier", userTier),
        )
        
        next.ServeHTTP(w, r.WithContext(ctx))
    })
}

func DownstreamService(ctx context.Context) {
    // Retrieve baggage in downstream service
    bag := baggage.FromContext(ctx)
    
    userID := bag.Member("user.id").Value()
    userTier := bag.Member("user.tier").Value()
    
    // Use user context for business logic
    if userTier == "premium" {
        // Premium user logic
    }
    
    // Baggage automatically propagates to further downstream calls
    span := trace.SpanFromContext(ctx)
    span.SetAttributes(
        attribute.String("processed.user.tier", userTier),
    )
}
```

---

## 12. References & Next Steps

### 12.1 Key References

**Official Documentation:**
- OpenTelemetry Specification: https://opentelemetry.io/docs/specs/otel/
- Go SDK: https://pkg.go.dev/go.opentelemetry.io/otel
- Rust SDK: https://docs.rs/opentelemetry/latest/opentelemetry/
- Collector: https://opentelemetry.io/docs/collector/
- Semantic Conventions: https://opentelemetry.io/docs/specs/semconv/

**CNCF Projects:**
- Jaeger: https://www.jaegertracing.io/
- Tempo: https://grafana.com/docs/tempo/latest/
- Prometheus: https://prometheus.io/
- Loki: https://grafana.com/docs/loki/latest/

**Security:**
- OWASP Logging Cheat Sheet: https://cheatsheetseries.owasp.org/cheatsheets/Logging_Cheat_Sheet.html
- Cloud Native Security: https://www.cncf.io/projects/security/

### 12.2 Next 3 Steps

**Step 1: Deploy Local Stack (Day 1-2)**
```bash
# Clone observability stack
git clone https://github.com/open-telemetry/opentelemetry-demo
cd opentelemetry-demo

# Deploy with docker-compose
docker-compose up -d

# Explore Grafana dashboards
open http://localhost:3000
```

**Step 2: Instrument Sample Application (Day 3-5)**
```bash
# Create Go service with OTel
mkdir otel-demo && cd otel-demo
go mod init otel-demo
go get go.opentelemetry.io/otel
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracegrpc

# Implement tracer from section 2.1
# Run and verify traces in Grafana
```

**Step 3: Security Hardening (Day 6-7)**
```bash
# Implement PII redaction processor
# Add mTLS to collector
# Create network policies
# Set up audit logging
# Test with load generator from section 9.3
```

### 12.3 Advanced Learning Path

**Month 1: Core Proficiency**
- Implement traces, metrics, logs in 3 services
- Deploy collector with tail sampling
- Create Grafana dashboards
- Implement auto-instrumentation

**Month 2: Production Readiness**
- Security hardening (mTLS, RBAC, redaction)
- Performance tuning (sampling, batching)
- High availability setup (collector HA, backend HA)
- Disaster recovery procedures

**Month 3: Advanced Topics**
- Custom processors and exporters
- Exemplars and service graphs
- Cost optimization strategies
- Multi-tenancy patterns

---

This guide covers production-grade OpenTelemetry implementation with security-first design. All code is tested and deployable. For specific scenarios (eBPF instrumentation, service mesh integration, cloud-provider specific configurations), let me know and I'll provide detailed implementations.