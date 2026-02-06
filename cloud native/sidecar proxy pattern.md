# Sidecar Proxy Pattern: Comprehensive Deep-Dive

**Summary**: The sidecar proxy pattern deploys a secondary process alongside an application container in the same execution context (pod/VM/host) to handle cross-cutting concerns like observability, security, traffic management, and protocol translation without modifying application code. It's foundational to service mesh architectures (Envoy in Istio/Linkerd, Consul Connect), zero-trust networking, and mTLS enforcement at scale. The sidecar intercepts all network traffic via iptables/eBPF, terminates TLS, enforces policy, emits metrics, and proxies requests. Trade-offs include added latency (p99: 1-5ms), memory overhead (50-200MB/sidecar), and operational complexity (version skew, injection failures). Production deployments require careful CPU/memory tuning, circuit breaking, and fault injection testing.

---

## Architecture & Execution Model

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│  Kubernetes Pod / VM / Systemd Unit Boundary                │
│                                                               │
│  ┌──────────────────┐          ┌──────────────────┐         │
│  │  Application     │          │  Sidecar Proxy   │         │
│  │  Container       │◄────────►│  (Envoy/Linkerd) │         │
│  │                  │  lo/veth │                  │         │
│  │  :8080 (app)     │          │  :15001 (inbound)│         │
│  │                  │          │  :15000 (outbound│         │
│  └────────┬─────────┘          │  :15020 (admin)  │         │
│           │                     └────────┬─────────┘         │
│           │                              │                   │
│           │      ┌───────────────────────┘                   │
│           │      │   Traffic Interception Layer              │
│           │      │   (iptables PREROUTING/OUTPUT)            │
│           │      │   or eBPF sockops/redir                   │
│           └──────┼───────────────────────────────────────────┤
│                  │                                            │
└──────────────────┼────────────────────────────────────────────┘
                   │
                   ▼
          Network (eth0/CNI interface)
          ┌─────────────────────────────┐
          │ mTLS to peer sidecars       │
          │ L7 protocol translation     │
          │ Circuit breaking/retries    │
          └─────────────────────────────┘
```

### Traffic Flow: Outbound Request

1. **Application initiates**: `curl http://backend-svc:8080/api`
2. **iptables intercept** (OUTPUT chain):
   ```bash
   -A OUTPUT -p tcp -j REDIRECT --to-port 15001
   ```
3. **Sidecar receives**: Envoy listener on `0.0.0.0:15001`
4. **Service discovery**: Query control plane (Istiod/Linkerd controller) for `backend-svc` endpoints
5. **Load balancing**: Select endpoint via LEAST_REQUEST/ROUND_ROBIN
6. **mTLS handshake**: Establish TLS 1.3 session using SPIFFE X.509-SVID from workload identity
7. **L7 routing**: Apply HTTP header-based routing, retries (max 3, exp backoff), timeouts (30s)
8. **Forward**: Proxy to upstream sidecar on peer pod
9. **Observability**: Emit metrics (request count, latency histograms), distributed trace span (Jaeger/Zipkin), access logs

### Traffic Flow: Inbound Request

1. **Peer sidecar sends**: mTLS-encrypted HTTP/2 stream to `pod-ip:15001`
2. **iptables PREROUTING**: Redirect to local sidecar inbound listener
3. **mTLS termination**: Validate peer certificate against CA root, extract identity
4. **AuthZ check**: Evaluate policy (e.g., "allow backend-svc if JWT scope=read")
5. **Protocol translation**: HTTP/2 → HTTP/1.1 if app expects it
6. **Forward to app**: Plain HTTP to `localhost:8080`
7. **Response path**: Reverse flow, re-encrypt for peer

---

## Network Traffic Interception Mechanisms

### 1. iptables REDIRECT (Legacy, Universal)

**Init container** (`istio-init`, `linkerd-init`) runs with `NET_ADMIN` capability:

```bash
# Redirect all outbound TCP to Envoy outbound port
iptables -t nat -A OUTPUT -p tcp -j REDIRECT --to-port 15001

# Redirect inbound traffic (excluding sidecar ports)
iptables -t nat -A PREROUTING -p tcp -j REDIRECT --to-port 15006 \
  -m tcp ! --dport 15001 ! --dport 15020

# Exclude control plane traffic, health checks, Prometheus scrapes
iptables -t nat -I OUTPUT -p tcp --dport 15012 -j RETURN  # xDS gRPC
iptables -t nat -I OUTPUT -p tcp --dport 9090 -j RETURN   # Prometheus
```

**Trade-offs**:
- ✅ Works on any kernel ≥3.10
- ❌ NAT conntrack table overhead (~200K connections max, tunable via `nf_conntrack_max`)
- ❌ Breaks `SO_ORIGINAL_DST` for some apps (workaround: Envoy `use_original_dst`)

### 2. eBPF sockops + sk_msg (Modern, High-Performance)

**Cilium, Istio 1.10+ CNI mode**:

```c
// eBPF program attached to cgroup/sock_ops
SEC("sockops")
int bpf_sockops(struct bpf_sock_ops *skops) {
    if (skops->family == AF_INET && skops->remote_port == 8080) {
        // Redirect to sidecar socket map
        bpf_sock_ops_cb_flags_set(skops, BPF_SOCK_OPS_ALL_CB_FLAGS);
        return 1;
    }
    return 0;
}

// sk_msg program for zero-copy redirect
SEC("sk_msg")
int bpf_redir(struct sk_msg_md *msg) {
    return bpf_msg_redirect_hash(msg, &sock_map, &key, BPF_F_INGRESS);
}
```

**Attach**:
```bash
bpftool prog load sockops.o /sys/fs/bpf/sockops type sockops
bpftool cgroup attach /sys/fs/cgroup/unified/kubepods/pod-uid sock_ops \
  pinned /sys/fs/bpf/sockops
```

**Benefits**:
- ✅ Bypass netfilter stack → 30-50% lower CPU, sub-microsecond latency
- ✅ No conntrack pollution
- ❌ Requires kernel ≥4.19, `CONFIG_BPF_STREAM_PARSER`
- ❌ Limited to same-host optimization (inter-pod on same node)

### 3. Transparent Proxy via `TPROXY` (UDP Support)

```bash
# Mark packets for policy routing
iptables -t mangle -A PREROUTING -p tcp -j TPROXY \
  --tproxy-mark 0x1/0x1 --on-port 15001

# Route marked packets to local
ip rule add fwmark 1 lookup 100
ip route add local 0.0.0.0/0 dev lo table 100
```

Envoy listens with `transparent: true`:
```yaml
listeners:
- address:
    socket_address:
      address: 0.0.0.0
      port_value: 15001
  transparent: true  # Preserve original dest IP
```

---

## Sidecar Proxy Implementations

### Envoy (C++, CNCF Graduated)

**Why Envoy**:
- L7 protocol support: HTTP/1.1, HTTP/2, HTTP/3, gRPC, Thrift, MongoDB, Redis, MySQL
- Dynamic config via xDS APIs (Listener/Route/Cluster/Endpoint Discovery Service)
- Extensible via WASM filters (custom authz, rate limiting, header manipulation)
- Battle-tested: Google/Lyft production, 100K+ RPS per instance

**Config Example** (static for simplicity):
```yaml
static_resources:
  listeners:
  - name: outbound_listener
    address:
      socket_address: { address: 0.0.0.0, port_value: 15001 }
    filter_chains:
    - filters:
      - name: envoy.filters.network.http_connection_manager
        typed_config:
          "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
          stat_prefix: outbound
          route_config:
            virtual_hosts:
            - name: backend
              domains: ["backend-svc:8080"]
              routes:
              - match: { prefix: "/" }
                route:
                  cluster: backend_cluster
                  timeout: 30s
                  retry_policy:
                    retry_on: 5xx
                    num_retries: 3
          http_filters:
          - name: envoy.filters.http.router

  clusters:
  - name: backend_cluster
    type: STRICT_DNS
    lb_policy: LEAST_REQUEST
    load_assignment:
      cluster_name: backend_cluster
      endpoints:
      - lb_endpoints:
        - endpoint:
            address: { socket_address: { address: backend-svc, port_value: 8080 }}
    transport_socket:
      name: envoy.transport_sockets.tls
      typed_config:
        "@type": type.googleapis.com/envoy.extensions.transport_sockets.tls.v3.UpstreamTlsContext
        common_tls_context:
          tls_certificates:
          - certificate_chain: { filename: /etc/certs/cert-chain.pem }
            private_key: { filename: /etc/certs/key.pem }
          validation_context:
            trusted_ca: { filename: /etc/certs/root-cert.pem }

admin:
  address:
    socket_address: { address: 127.0.0.1, port_value: 15000 }
```

**Dynamic Config (xDS)**:
```go
// Control plane implements xDS gRPC server
import (
    discoveryv3 "github.com/envoyproxy/go-control-plane/envoy/service/discovery/v3"
    cachev3 "github.com/envoyproxy/go-control-plane/pkg/cache/v3"
)

cache := cachev3.NewSnapshotCache(false, cachev3.IDHash{}, nil)
server := xds.NewServer(ctx, cache, nil)

// Push config on endpoint change
snapshot := cachev3.NewSnapshot("v1",
    map[resource.Type][]types.Resource{
        resource.EndpointType: endpoints,  // CLA updates
        resource.ClusterType:  clusters,
        resource.RouteType:    routes,
    },
)
cache.SetSnapshot(ctx, nodeID, snapshot)
```

**Memory footprint**: 50MB base + 2KB per connection + 10KB per cluster

### Linkerd2-proxy (Rust, CNCF Graduated)

**Design philosophy**:
- Zero-config: Auto-injection, no CRDs for basic use
- Rust: Memory-safe, no GC pauses (critical for p99 latency)
- HTTP/2 native: Multiplexing, flow control, server push
- Lightweight: 10MB memory base, <1ms p99 overhead

**Key differentiator**: **Tap** (live request introspection):
```bash
linkerd tap deploy/frontend --to deploy/backend --path /checkout
# Real-time stream of requests with headers, duration, status
```

**Metrics**:
```
request_total{direction="outbound",target_addr="backend:8080",tls="true"} 1523
response_latency_ms_bucket{le="5"} 1450  # 95% < 5ms
```

### Consul Connect (Go)

**Integrated service mesh** with Consul's service catalog:
```hcl
service {
  name = "web"
  port = 8080
  connect {
    sidecar_service {
      proxy {
        upstreams = [
          { destination_name = "db", local_bind_port = 5432 }
        ]
      }
    }
  }
}
```

**Proxy**: Envoy (default) or built-in Go proxy (lighter but fewer features)

---

## Control Plane Integration

### Service Discovery

**Problem**: Sidecar needs real-time endpoint list for `backend-svc`

**Solutions**:

1. **Kubernetes Endpoints API**:
   ```bash
   kubectl get endpoints backend-svc -o json | jq '.subsets[].addresses[].ip'
   ```
   Control plane (Istiod) watches Endpoints, pushes CLA (Cluster Load Assignment) to Envoy via xDS.

2. **Consul DNS**:
   ```bash
   dig @consul backend-svc.service.consul SRV
   # Returns IP:port list
   ```

3. **Custom registry** (etcd, Eureka): Control plane adapter translates to xDS.

### Certificate Management (mTLS)

**SPIFFE/SPIRE** (production standard):

```
┌─────────────────────────────────────────────────────────┐
│  Control Plane (Istiod / SPIRE Server)                  │
│  ┌──────────────────────────────────────────────────┐   │
│  │  CA (intermediate signed by root)                │   │
│  │  Issues X.509-SVIDs to workloads                 │   │
│  └──────────────────────────────────────────────────┘   │
│           │ gRPC (SDS - Secret Discovery Service)       │
└───────────┼─────────────────────────────────────────────┘
            │
            ▼
┌───────────────────────────────────────────────────────┐
│  Sidecar (Envoy SDS Client)                           │
│  1. Prove identity via K8s Service Account JWT        │
│  2. Receive cert: CN=spiffe://cluster/ns/sa/backend   │
│  3. Auto-rotate before expiry (default 1h TTL)        │
└───────────────────────────────────────────────────────┘
```

**Envoy SDS config**:
```yaml
transport_socket:
  name: envoy.transport_sockets.tls
  typed_config:
    common_tls_context:
      tls_certificate_sds_secret_configs:
      - name: default
        sds_config:
          api_config_source:
            api_type: GRPC
            grpc_services:
            - envoy_grpc:
                cluster_name: sds-grpc
```

**SPIRE Agent** (runs as DaemonSet):
```bash
# Attest workload via K8s kubelet API
spire-agent api fetch x509 -socketPath /run/spire/sockets/agent.sock
# Returns SVID + trust bundle
```

---

## Real-World Use Cases

### 1. Zero-Trust Networking

**Scenario**: Enforce mTLS + L7 AuthZ for PCI-compliant payment service

```yaml
# Istio AuthorizationPolicy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-authz
  namespace: prod
spec:
  selector:
    matchLabels:
      app: payment-svc
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/prod/sa/checkout-svc"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/v1/charge"]
    when:
    - key: request.auth.claims[scope]
      values: ["payment.write"]
```

**Enforcement**: Sidecar validates JWT (via JWKS from OIDC provider), checks principal, allows/denies before forwarding.

### 2. Protocol Translation (gRPC ↔ REST)

**Legacy REST client** → **gRPC backend**:

```yaml
# Envoy HTTP filter: grpc_json_transcoder
http_filters:
- name: envoy.filters.http.grpc_json_transcoder
  typed_config:
    proto_descriptor: /etc/envoy/proto.pb
    services: ["backend.v1.BackendService"]
    print_options:
      add_whitespace: true
```

Client sends: `POST /v1/users {"name": "alice"}`  
Sidecar translates to gRPC: `backend.v1.BackendService/CreateUser`

### 3. Circuit Breaking

**Prevent cascading failures**:

```yaml
clusters:
- name: backend_cluster
  circuit_breakers:
    thresholds:
    - priority: DEFAULT
      max_connections: 1000        # TCP connections
      max_pending_requests: 100    # Queued HTTP requests
      max_requests: 1000           # Concurrent HTTP/2 streams
      max_retries: 3
  outlier_detection:
    consecutive_5xx: 5             # Eject after 5 errors
    interval: 10s
    base_ejection_time: 30s        # Eject for 30s, then exponential
```

**Behavior**:
- After 1000 concurrent requests, return `503 Service Unavailable` immediately.
- If backend returns 5× 5xx in 10s, eject endpoint for 30s → 60s → 120s.

### 4. Traffic Shadowing (Dark Launch)

```yaml
routes:
- match: { prefix: "/" }
  route:
    cluster: prod_v1
    request_mirror_policies:
    - cluster: prod_v2_canary
      runtime_fraction:
        default_value:
          numerator: 10
          denominator: 100  # Mirror 10% traffic
```

**Use**: Test v2 with production traffic load, compare error rates, discard responses.

### 5. Egress Control (Data Exfiltration Prevention)

**Block all external traffic except approved destinations**:

```yaml
# Istio ServiceEntry for allowed egress
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: external-api
spec:
  hosts:
  - api.partner.com
  ports:
  - number: 443
    name: https
    protocol: HTTPS
  location: MESH_EXTERNAL
  resolution: DNS

# Block all other external traffic via sidecar outbound policy
---
apiVersion: networking.istio.io/v1beta1
kind: Sidecar
metadata:
  name: default
  namespace: prod
spec:
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY  # Block unregistered external hosts
```

---

## Threat Model & Mitigations

### Threats

| Threat | Attack Vector | Impact |
|--------|---------------|--------|
| **Sidecar compromise** | CVE in Envoy, memory corruption | Full pod network control, credential theft |
| **iptables bypass** | App binds raw socket, skips NAT | Unencrypted egress, policy evasion |
| **Control plane MITM** | Attacker intercepts xDS gRPC | Inject malicious routes, redirect traffic |
| **Certificate theft** | Read `/etc/certs` from app container | Impersonate service, decrypt mTLS |
| **Metadata API abuse** | Query IMDSv2 for cloud credentials | Lateral movement to cloud resources |

### Mitigations

1. **Immutable sidecar image** + **Distroless base**:
   ```dockerfile
   FROM gcr.io/distroless/cc-debian11
   COPY --from=builder /envoy /usr/local/bin/envoy
   USER 1337:1337
   ENTRYPOINT ["/usr/local/bin/envoy"]
   ```

2. **SELinux/AppArmor** to block raw sockets:
   ```bash
   # AppArmor profile
   deny network raw,
   deny network packet,
   ```

3. **mTLS for control plane** (xDS over TLS):
   ```yaml
   static_resources:
     clusters:
     - name: xds-grpc
       transport_socket:
         name: envoy.transport_sockets.tls
         typed_config:
           common_tls_context:
             tls_certificates:
             - certificate_chain: { filename: /etc/xds-certs/cert.pem }
   ```

4. **Secret volume mount with short TTL** (1h rotation):
   ```yaml
   volumeMounts:
   - name: certs
     mountPath: /etc/certs
     readOnly: true
   volumes:
   - name: certs
     projected:
       sources:
       - serviceAccountToken:
           path: token
           expirationSeconds: 3600
   ```

5. **NetworkPolicy** to block IMDS:
   ```yaml
   apiVersion: networking.k8s.io/v1
   kind: NetworkPolicy
   spec:
     podSelector: {}
     policyTypes:
     - Egress
     egress:
     - to:
       - ipBlock:
           cidr: 0.0.0.0/0
           except:
           - 169.254.169.254/32  # AWS IMDS
           - 169.254.170.2/32    # EKS IMDS
   ```

---

## Performance Tuning

### CPU Allocation

**Problem**: Sidecar competes with app for CPU, throttles at 100m limit.

**Solution**: Requests = 100m, Limits = 2000m (burst for handshakes).

```yaml
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 2000m
    memory: 1Gi
```

**Benchmarks** (Envoy 1.28, 10K RPS, HTTP/2):
- 100m CPU → p99 latency = 15ms (CPU throttled)
- 500m CPU → p99 latency = 3ms
- 1000m CPU → p99 latency = 2ms (diminishing returns)

### Memory Tuning

**Envoy heap growth**:
```
Base (50MB) + Connections (2KB each) + Clusters (10KB each) + Routes (5KB each)
```

For 10K connections, 100 clusters: `50 + 20 + 1 + 0.5 = 71.5MB`

**Overload manager** (OOMKill prevention):
```yaml
overload_manager:
  refresh_interval: 0.25s
  resource_monitors:
  - name: envoy.resource_monitors.fixed_heap
    typed_config:
      max_heap_size_bytes: 536870912  # 512MB
  actions:
  - name: envoy.overload_actions.shrink_heap
    triggers:
    - name: envoy.resource_monitors.fixed_heap
      threshold:
        value: 0.9  # At 90%, start GC
  - name: envoy.overload_actions.stop_accepting_requests
    triggers:
    - name: envoy.resource_monitors.fixed_heap
      threshold:
        value: 0.95  # At 95%, reject new connections
```

### Connection Pooling

**HTTP/2 multiplexing** (reduce connection overhead):

```yaml
clusters:
- name: backend
  http2_protocol_options:
    max_concurrent_streams: 100  # 100 requests per connection
  max_requests_per_connection: 10000  # Rotate after 10K requests
```

**vs HTTP/1.1**:
- HTTP/1.1: 100 concurrent requests = 100 TCP connections = 200KB memory
- HTTP/2: 100 concurrent requests = 1 TCP connection = 2KB memory

---

## Observability

### Metrics (Prometheus)

**Envoy exposes** `/stats/prometheus`:

```prometheus
# Request rate
rate(envoy_cluster_upstream_rq_total{cluster="backend"}[1m])

# Latency (histogram)
histogram_quantile(0.99,
  rate(envoy_cluster_upstream_rq_time_bucket{cluster="backend"}[1m])
)

# Circuit breaker triggers
envoy_cluster_circuit_breakers_default_rq_open{cluster="backend"}

# mTLS validation failures
envoy_listener_ssl_fail_verify_error{listener="0.0.0.0_15006"}
```

**SLO alerting**:
```yaml
- alert: HighErrorRate
  expr: |
    sum(rate(envoy_cluster_upstream_rq_xx{envoy_response_code_class="5"}[5m]))
    / sum(rate(envoy_cluster_upstream_rq_total[5m])) > 0.01
  for: 2m
  annotations:
    summary: "5xx error rate > 1% for 2 minutes"
```

### Distributed Tracing

**Envoy propagates** `x-request-id`, `x-b3-traceid`, `traceparent` headers:

```yaml
http_connection_manager:
  tracing:
    provider:
      name: envoy.tracers.zipkin
      typed_config:
        collector_cluster: jaeger
        collector_endpoint: /api/v2/spans
        trace_id_128bit: true
```

**App instruments**:
```go
import "go.opentelemetry.io/otel"

ctx = otel.GetTextMapPropagator().Extract(ctx, r.Header)  // Extract trace
span := tracer.Start(ctx, "db-query")
defer span.End()
```

**Result**: End-to-end trace across app → sidecar → peer sidecar → peer app.

### Access Logs

```yaml
http_filters:
- name: envoy.filters.http.router
access_log:
- name: envoy.access_loggers.file
  typed_config:
    path: /dev/stdout
    format: |
      [%START_TIME%] "%REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% %PROTOCOL%"
      %RESPONSE_CODE% %RESPONSE_FLAGS% %BYTES_RECEIVED% %BYTES_SENT% %DURATION%
      "%REQ(X-FORWARDED-FOR)%" "%REQ(USER-AGENT)%" "%REQ(X-REQUEST-ID)%"
      "%UPSTREAM_HOST%" "%DOWNSTREAM_REMOTE_ADDRESS%"
```

**Example log**:
```
[2024-02-06T10:15:30.123Z] "GET /api/users HTTP/2" 200 - 0 1234 45 "10.0.1.5"
"curl/7.68.0" "a3f2-4b1e-9c8d" "backend-pod-ip:8080" "10.0.2.3:15001"
```

---

## Deployment & Lifecycle

### Automatic Injection (Kubernetes)

**MutatingWebhookConfiguration**:
```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: MutatingWebhookConfiguration
metadata:
  name: istio-sidecar-injector
webhooks:
- name: sidecar-injector.istio.io
  clientConfig:
    service:
      name: istiod
      namespace: istio-system
      path: /inject
    caBundle: <base64-ca-cert>
  rules:
  - operations: ["CREATE"]
    apiGroups: [""]
    apiVersions: ["v1"]
    resources: ["pods"]
  namespaceSelector:
    matchLabels:
      istio-injection: enabled
```

**Injection logic** (istiod):
1. Receive pod spec via webhook
2. Check annotation `sidecar.istio.io/inject: "true"`
3. Inject init container (iptables), sidecar container, volumes (certs, config)
4. Return mutated pod spec

**Manual injection** (CI/CD):
```bash
istioctl kube-inject -f deploy.yaml | kubectl apply -f -
```

### Rollout Strategy

**Blue-Green** (zero-downtime):

1. Deploy new sidecar version to 10% pods:
   ```yaml
   spec:
     template:
       metadata:
         annotations:
           sidecar.istio.io/proxyImage: "istio/proxyv2:1.20.0"
   ```

2. Monitor error rates, latency for 1 hour.

3. If p99 < 5ms and errors < 0.1%, scale to 50% → 100%.

**Canary with Flagger** (automated):
```yaml
apiVersion: flagger.app/v1beta1
kind: Canary
metadata:
  name: backend
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: backend
  progressDeadlineSeconds: 60
  service:
    port: 8080
  analysis:
    interval: 1m
    threshold: 5
    maxWeight: 50
    stepWeight: 10
    metrics:
    - name: request-success-rate
      thresholdRange:
        min: 99
      interval: 1m
```

### Rollback

**Scenario**: New sidecar version causes 5xx spike.

```bash
# Immediate rollback
kubectl set image deployment/backend \
  istio-proxy=istio/proxyv2:1.19.0

# Verify
kubectl rollout status deployment/backend

# Check logs for root cause
kubectl logs -l app=backend -c istio-proxy --tail=100 | grep ERROR
```

---

## Testing & Validation

### Fault Injection

**Chaos engineering** (inject 500ms latency to 10% requests):

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: backend-fault
spec:
  hosts:
  - backend-svc
  http:
  - fault:
      delay:
        percentage:
          value: 10
        fixedDelay: 500ms
    route:
    - destination:
        host: backend-svc
```

**Validation**:
```bash
# Generate load
hey -z 60s -c 10 http://frontend-svc/api

# Observe p99 latency increase by ~500ms
kubectl exec -it deploy/frontend -c istio-proxy -- \
  curl localhost:15000/stats | grep upstream_rq_time
```

### mTLS Verification

```bash
# Check if mTLS is enforced
istioctl authn tls-check deploy/backend

# Expected output:
# HOST:PORT          STATUS     SERVER     CLIENT     AUTHN POLICY
# backend.prod.svc   OK         mTLS       mTLS       default/

# Packet capture to verify encryption
kubectl exec -it deploy/backend -c istio-proxy -- \
  tcpdump -i eth0 -s0 -w /tmp/capture.pcap port 8080

# Download and inspect in Wireshark
kubectl cp backend-pod:/tmp/capture.pcap ./capture.pcap
# Should see TLS handshake, encrypted Application Data
```

### Load Testing

**Envoy benchmark** (single instance):

```bash
# Compile Envoy with optimizations
bazel build -c opt //source/exe:envoy-static

# Run nighthawk (Envoy's load tester)
nighthawk_client \
  --duration 60 \
  --connections 100 \
  --rps 10000 \
  --concurrency 4 \
  http://localhost:15001/

# Observe:
# - p50: 0.5ms
# - p99: 3ms# - p99.9: 15ms
# - Max RPS: 50K (CPU-bound on 4 cores)
```

---

## Production Deployment Example (Kubernetes + Istio)

### 1. Install Istio

```bash
# Download Istio 1.20
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.0 sh -
cd istio-1.20.0

# Install with production profile
bin/istioctl install --set profile=production \
  --set values.global.proxy.resources.requests.cpu=200m \
  --set values.global.proxy.resources.requests.memory=128Mi \
  --set values.pilot.autoscaleEnabled=true \
  --set values.pilot.autoscaleMin=2 \
  --set values.pilot.resources.requests.cpu=500m
```

### 2. Enable Injection

```bash
kubectl create namespace prod
kubectl label namespace prod istio-injection=enabled
```

### 3. Deploy Application

```yaml
# backend-deploy.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend
  namespace: prod
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
        version: v1
    spec:
      serviceAccountName: backend
      containers:
      - name: app
        image: myregistry/backend:v1.0.0
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: 500m
            memory: 512Mi
        livenessProbe:
          httpGet:
            path: /healthz
            port: 8080
          initialDelaySeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: backend-svc
  namespace: prod
spec:
  selector:
    app: backend
  ports:
  - port: 8080
    targetPort: 8080
```

```bash
kubectl apply -f backend-deploy.yaml

# Verify sidecar injection
kubectl get pod -n prod -o jsonpath='{.items[0].spec.containers[*].name}'
# Output: app istio-proxy
```

### 4. Configure mTLS

```yaml
# peer-auth.yaml
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: prod
spec:
  mtls:
    mode: STRICT  # Enforce mTLS for all services
```

```bash
kubectl apply -f peer-auth.yaml

# Verify
istioctl authn tls-check deploy/backend -n prod
```

### 5. Apply AuthZ Policy

```yaml
# authz.yaml
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: backend-authz
  namespace: prod
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/prod/sa/frontend"]
    to:
    - operation:
        methods: ["GET", "POST"]
```

```bash
kubectl apply -f authz.yaml

# Test unauthorized access (should fail)
kubectl run test --rm -it --image=curlimages/curl -- \
  curl backend-svc.prod.svc.cluster.local:8080/api
# RBAC: access denied
```

### 6. Configure Observability

```yaml
# telemetry.yaml
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: default
  namespace: prod
spec:
  tracing:
  - providers:
    - name: jaeger
    randomSamplingPercentage: 1.0  # 1% sampling
  metrics:
  - providers:
    - name: prometheus
```

```bash
# Deploy Prometheus + Grafana
kubectl apply -f https://raw.githubusercontent.com/istio/istio/1.20.0/samples/addons/prometheus.yaml
kubectl apply -f https://raw.githubusercontent.com/istio/istio/1.20.0/samples/addons/grafana.yaml

# Access Grafana
istioctl dashboard grafana
# Import Istio dashboards (pre-configured)
```

---

## Advanced: eBPF-Accelerated Sidecar (Cilium + Istio)

**Combine** Cilium CNI (eBPF datapath) + Istio (L7 policy):

```bash
# Install Cilium with sidecar acceleration
cilium install \
  --set kubeProxyReplacement=strict \
  --set bpf.monitorAggregation=maximum \
  --set sockops.enabled=true

# Install Istio in ambient mode (no sidecar, eBPF L4)
istioctl install --set profile=ambient

# For services needing L7 policy, add sidecar
kubectl label namespace prod istio-injection=enabled
```

**Result**:
- Cilium handles L3/L4 (routing, LB, network policy) in kernel
- Istio sidecar handles L7 (HTTP routing, JWT, retries) in userspace
- **30% lower CPU** vs pure Istio, **50% lower latency** vs pure iptables

---

## Common Pitfalls & Debugging

### Issue 1: Sidecar Not Injected

**Symptom**: `kubectl get pod` shows only 1 container (app).

**Debug**:
```bash
# Check namespace label
kubectl get namespace prod --show-labels
# Missing: istio-injection=enabled

# Check webhook
kubectl get mutatingwebhookconfigurations istio-sidecar-injector -o yaml
# Ensure namespaceSelector matches

# Manual injection to test
istioctl kube-inject -f deploy.yaml | kubectl apply -f -
```

### Issue 2: mTLS Handshake Failures

**Symptom**: `503 UC` (Upstream Connect Failure) in logs.

**Debug**:
```bash
# Check certificate
kubectl exec -it deploy/backend -c istio-proxy -- \
  openssl s_client -connect backend-svc:8080 -showcerts

# Verify SPIFFE ID in cert
# CN=spiffe://cluster.local/ns/prod/sa/backend

# Check CA trust
kubectl get cm -n istio-system istio-ca-root-cert -o yaml
# Ensure root cert matches

# Restart pods to refresh certs
kubectl rollout restart deployment/backend -n prod
```

### Issue 3: High Latency (p99 > 100ms)

**Debug**:
```bash
# Check CPU throttling
kubectl top pod -n prod -l app=backend --containers
# If istio-proxy CPU > limit, increase limit

# Inspect Envoy stats
kubectl exec -it deploy/backend -c istio-proxy -- \
  curl localhost:15000/stats | grep -E 'rq_time|pending'

# Check connection pool exhaustion
# upstream_rq_pending_overflow > 0 → increase max_connections

# Profile Envoy
kubectl exec -it deploy/backend -c istio-proxy -- \
  curl -X POST localhost:15000/cpuprofiler?enable=y
# Generate load, then:
kubectl exec -it deploy/backend -c istio-proxy -- \
  curl localhost:15000/cpuprofiler?enable=n > /tmp/profile
# Analyze with pprof
```

---

## Comparison: Sidecar vs Alternatives

| Approach | Pros | Cons | Use Case |
|----------|------|------|----------|
| **Sidecar** | Language-agnostic, granular policy, no code changes | Overhead (memory, CPU, latency), version skew | Polyglot services, strict isolation |
| **Library (SDK)** | Low overhead, native integration | Language lock-in, code changes, update burden | Homogeneous stack (e.g., all Go) |
| **Node agent** (Linkerd ambient, Cilium) | Lower overhead (shared per node) | Coarser isolation, harder per-pod policy | Cost-sensitive, non-critical workloads |
| **API Gateway** (Envoy Gateway, Kong) | Centralized policy, N-S traffic | Not for E-W mesh, single point of failure | Ingress, external-facing APIs |

---

## Next 3 Steps

1. **Deploy Istio in test cluster**:
   ```bash
   kind create cluster --config kind-config.yaml
   istioctl install --set profile=demo -y
   kubectl label namespace default istio-injection=enabled
   kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml
   ```

2. **Implement custom Envoy WASM filter** (Rust):
   ```bash
   cargo new --lib my-filter
   # Add proxy-wasm SDK, compile to WASM
   cargo build --target wasm32-unknown-unknown --release
   # Deploy via WasmPlugin CRD
   ```

3. **Benchmark sidecar overhead**:
   ```bash
   # Baseline (no sidecar)
   hey -z 60s -c 100 http://backend-svc:8080
   # Enable sidecar, re-run
   # Compare p50/p99 latency, CPU usage
   ```

---

## References

- **Envoy Docs**: https://www.envoyproxy.io/docs/envoy/latest/
- **Istio Concepts**: https://istio.io/latest/docs/concepts/
- **SPIFFE Spec**: https://github.com/spiffe/spiffe/blob/main/standards/SPIFFE.md
- **xDS Protocol**: https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol
- **eBPF Sockops**: https://docs.cilium.io/en/stable/gettingstarted/sockmap/
- **Linkerd Architecture**: https://linkerd.io/2.14/reference/architecture/
- **CNCF Service Mesh Landscape**: https://landscape.cncf.io/card-mode?category=service-mesh

