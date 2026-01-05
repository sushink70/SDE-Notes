# Comprehensive Guide to Service Meshes in Cloud-Native Environments

**Summary:** Service meshes provide a dedicated infrastructure layer for managing service-to-service communication in microservices architectures, offering traffic management, observability, security (mTLS), and policy enforcement without modifying application code.

---

## 1. Core Concepts & Architecture

### What is a Service Mesh?

A service mesh is a configurable infrastructure layer that handles inter-service communication through sidecar proxies deployed alongside each service instance. It separates network concerns from application logic.

**Key Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                    Control Plane                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Config     │  │  Certificate │  │  Telemetry   │      │
│  │   Manager    │  │   Authority  │  │  Aggregator  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                   ┌────────┴────────┐
                   │   xDS APIs      │
                   └────────┬────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
┌───────▼──────┐    ┌───────▼──────┐    ┌──────▼──────┐
│  Pod/Node 1  │    │  Pod/Node 2  │    │  Pod/Node 3 │
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐│
│ │  App     │ │    │ │  App     │ │    │ │  App     ││
│ │Container │ │    │ │Container │ │    │ │Container ││
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘│
│ ┌──────────┐ │    │ ┌──────────┐ │    │ ┌──────────┐│
│ │ Sidecar  │◄┼────┼►│ Sidecar  │◄┼────┼►│ Sidecar  ││
│ │  Proxy   │ │    │ │  Proxy   │ │    │ │  Proxy   ││
│ └──────────┘ │    │ └──────────┘ │    │ └──────────┘│
└──────────────┘    └──────────────┘    └──────────────┘
     Data Plane          Data Plane          Data Plane
```

**Architecture Layers:**

1. **Data Plane**: Sidecar proxies (Envoy, Linkerd-proxy) handle actual traffic
2. **Control Plane**: Configuration distribution, certificate management, policy enforcement
3. **Management Plane**: User interfaces, CLI tools, observability dashboards

---

## 2. Major Service Mesh Implementations

### Comparison Matrix

| Feature | Istio | Linkerd | Consul Connect | Cilium Service Mesh | Kuma |
|---------|-------|---------|----------------|---------------------|------|
| **Proxy** | Envoy | linkerd2-proxy (Rust) | Envoy/native | Envoy | Envoy |
| **Protocol** | HTTP/gRPC/TCP | HTTP/gRPC/TCP | HTTP/gRPC/TCP | HTTP/gRPC/TCP | HTTP/gRPC/TCP |
| **mTLS** | SPIFFE/SPIRE | Built-in | Consul CA | Cert-manager | Built-in |
| **Memory/Pod** | ~50-100MB | ~10-20MB | ~30-50MB | ~25-40MB | ~40-60MB |
| **Complexity** | High | Low | Medium | Medium | Medium |
| **Multi-cluster** | Yes | Yes | Yes | Yes | Yes |
| **VM Support** | Yes | Limited | Yes | Limited | Yes |
| **eBPF** | No | No | No | Yes (native) | No |

### Istio (CNCF Graduated)

**Install & Test:**

```bash
# Install istioctl
curl -L https://istio.io/downloadIstio | sh -
cd istio-*
export PATH=$PWD/bin:$PATH

# Install with minimal profile for production
istioctl install --set profile=minimal -y

# Verify control plane
kubectl get pods -n istio-system

# Enable sidecar injection for namespace
kubectl label namespace default istio-injection=enabled

# Deploy sample app
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml

# Verify sidecars injected
kubectl get pods -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[*].name}{"\n"}'

# Apply traffic routing
kubectl apply -f - <<EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: reviews-route
spec:
  hosts:
  - reviews
  http:
  - match:
    - headers:
        end-user:
          exact: jason
    route:
    - destination:
        host: reviews
        subset: v2
  - route:
    - destination:
        host: reviews
        subset: v1
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-destination
spec:
  host: reviews
  subsets:
  - name: v1
    labels:
      version: v1
  - name: v2
    labels:
      version: v2
EOF

# Test traffic split
kubectl exec -it $(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}') \
  -c ratings -- curl -H "end-user: jason" http://reviews:9080/reviews/1
```

**Istio Configuration Deep Dive:**

```yaml
# istio-config.yaml - Production-grade configuration
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: production-istio
spec:
  profile: default
  meshConfig:
    # Enable access logging
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON
    
    # Trace sampling (adjust for production load)
    defaultConfig:
      tracing:
        sampling: 1.0  # 100% for staging, 1-5% for prod
    
    # Enable strict mTLS
    enableAutoMtls: true
    
    # Protocol detection timeout
    protocolDetectionTimeout: 5s
    
  components:
    pilot:
      k8s:
        resources:
          requests:
            cpu: 500m
            memory: 2Gi
          limits:
            cpu: 2000m
            memory: 4Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 5
          metrics:
          - type: Resource
            resource:
              name: cpu
              target:
                type: Utilization
                averageUtilization: 80
    
    ingressGateways:
    - name: istio-ingressgateway
      enabled: true
      k8s:
        resources:
          requests:
            cpu: 1000m
            memory: 1Gi
          limits:
            cpu: 2000m
            memory: 2Gi
        hpaSpec:
          minReplicas: 2
          maxReplicas: 10
        service:
          type: LoadBalancer
```

### Linkerd (CNCF Graduated)

**Install & Test:**

```bash
# Install CLI
curl --proto '=https' --tlsv1.2 -sSfL https://run.linkerd.io/install | sh
export PATH=$PATH:$HOME/.linkerd2/bin

# Pre-flight checks
linkerd check --pre

# Install control plane with HA
linkerd install --ha | kubectl apply -f -

# Verify installation
linkerd check

# Install viz extension for observability
linkerd viz install | kubectl apply -f -

# Inject application
kubectl get deploy -o yaml | linkerd inject - | kubectl apply -f -

# Verify mesh status
linkerd viz stat deployment

# Check top routes by request volume
linkerd viz top deployment/webapp

# Enable retries and timeouts
kubectl annotate deployment webapp \
  config.linkerd.io/retry-budget='{"retryRatio": 0.2, "minRetriesPerSecond": 10, "ttl": "10s"}' \
  config.linkerd.io/timeout=10s
```

**Linkerd vs Istio Trade-offs:**

| Aspect | Linkerd | Istio |
|--------|---------|-------|
| Resource overhead | Lower (~20MB/pod) | Higher (~50-100MB/pod) |
| Complexity | Simpler, opinionated | Flexible, complex |
| Protocol support | HTTP/1.1, HTTP/2, gRPC, TCP | HTTP/1.1, HTTP/2, gRPC, TCP, MongoDB, MySQL |
| Extensibility | Limited | High (Wasm, Lua filters) |
| Feature velocity | Stable, conservative | Rapid, extensive |
| Learning curve | Easier | Steeper |

---

## 3. Traffic Management Capabilities

### Traffic Routing Patterns

```yaml
# Canary Deployment (Istio)
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: canary-rollout
spec:
  hosts:
  - myapp.example.com
  http:
  - match:
    - headers:
        x-canary:
          exact: "true"
    route:
    - destination:
        host: myapp
        subset: v2
      weight: 100
  - route:
    - destination:
        host: myapp
        subset: v1
      weight: 90
    - destination:
        host: myapp
        subset: v2
      weight: 10
---
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: myapp-destination
spec:
  host: myapp
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 100
      http:
        http1MaxPendingRequests: 50
        http2MaxRequests: 100
        maxRequestsPerConnection: 2
    outlierDetection:
      consecutive5xxErrors: 5
      interval: 30s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 40
  subsets:
  - name: v1
    labels:
      version: v1
    trafficPolicy:
      loadBalancer:
        simple: ROUND_ROBIN
  - name: v2
    labels:
      version: v2
    trafficPolicy:
      loadBalancer:
        consistentHash:
          httpCookie:
            name: session
            ttl: 3600s
```

### Circuit Breaking & Retries

```yaml
# Advanced circuit breaking (Istio)
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: circuit-breaker
spec:
  host: backend-service
  trafficPolicy:
    connectionPool:
      tcp:
        maxConnections: 1000
        connectTimeout: 30ms
        tcpKeepalive:
          time: 7200s
          interval: 75s
      http:
        http1MaxPendingRequests: 100
        http2MaxRequests: 1000
        maxRequestsPerConnection: 10
        idleTimeout: 3600s
    
    outlierDetection:
      consecutive5xxErrors: 5
      consecutiveGatewayErrors: 3
      interval: 10s
      baseEjectionTime: 30s
      maxEjectionPercent: 50
      minHealthPercent: 40
      splitExternalLocalOriginErrors: true
    
    loadBalancer:
      simple: LEAST_REQUEST
      warmupDurationSecs: 60
    
    tls:
      mode: ISTIO_MUTUAL
      
---
# Retry policy
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: retry-policy
spec:
  hosts:
  - backend-service
  http:
  - retries:
      attempts: 3
      perTryTimeout: 2s
      retryOn: 5xx,reset,connect-failure,refused-stream
      retryRemoteLocalities: true
    timeout: 10s
    route:
    - destination:
        host: backend-service
```

### Request Mirroring (Shadow Traffic)

```yaml
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: mirror-testing
spec:
  hosts:
  - api-service
  http:
  - route:
    - destination:
        host: api-service
        subset: v1
      weight: 100
    mirror:
      host: api-service
      subset: v2
    mirrorPercentage:
      value: 10.0  # Mirror 10% of traffic
```

---

## 4. Security: mTLS, Authorization, Certificates

### Automatic mTLS (Istio)

```yaml
# Mesh-wide strict mTLS
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

---
# Per-namespace override (permissive for migration)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: legacy-namespace
  namespace: legacy-apps
spec:
  mtls:
    mode: PERMISSIVE

---
# Per-service selective port configuration
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: myapp-mtls
  namespace: production
spec:
  selector:
    matchLabels:
      app: myapp
  mtls:
    mode: STRICT
  portLevelMtls:
    8080:
      mode: DISABLE  # Health check port
```

### Authorization Policies (Zero Trust)

```yaml
# Deny-by-default policy
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}  # Empty spec = deny all

---
# Allow specific service-to-service communication
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: allow-frontend-to-backend
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: ALLOW
  rules:
  - from:
    - source:
        principals:
        - "cluster.local/ns/production/sa/frontend"
    to:
    - operation:
        methods: ["GET", "POST"]
        paths: ["/api/v1/*"]
    when:
    - key: request.headers[x-api-version]
      values: ["v1", "v2"]

---
# JWT-based authorization (external auth)
apiVersion: security.istio.io/v1beta1
kind: RequestAuthentication
metadata:
  name: jwt-auth
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  jwtRules:
  - issuer: "https://auth.example.com"
    jwksUri: "https://auth.example.com/.well-known/jwks.json"
    audiences:
    - "api.example.com"
    forwardOriginalToken: true
---
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: jwt-authz
  namespace: production
spec:
  selector:
    matchLabels:
      app: api-gateway
  action: ALLOW
  rules:
  - from:
    - source:
        requestPrincipals: ["*"]
    when:
    - key: request.auth.claims[role]
      values: ["admin", "user"]
    - key: request.auth.claims[iss]
      values: ["https://auth.example.com"]
```

### Certificate Management (SPIFFE/SPIRE Integration)

```bash
# Install SPIRE for Istio
kubectl apply -f https://raw.githubusercontent.com/istio/istio/master/samples/security/spire/spire-quickstart.yaml

# Configure Istio to use SPIRE
istioctl install --set profile=default \
  --set meshConfig.trustDomain=example.org \
  --set meshConfig.defaultConfig.proxyMetadata.ISTIO_META_CERT_PROVIDER=spire \
  --set components.pilot.k8s.env[0].name=ENABLE_CA_SERVER \
  --set components.pilot.k8s.env[0].value="false"

# Verify SPIFFE identities
kubectl exec -it <pod-name> -c istio-proxy -- \
  openssl s_client -showcerts -connect backend:8080 -servername backend
```

**Certificate Rotation Testing:**

```bash
# Force certificate rotation (Istio)
kubectl delete secret istio-ca-secret -n istio-system

# Monitor rotation
kubectl logs -n istio-system -l app=istiod -f | grep "CSR signing"

# Verify new certificates
istioctl proxy-config secret <pod-name> -o json | jq -r \
  '.dynamicActiveSecrets[0].secret.tlsCertificate.certificateChain.inlineBytes' | \
  base64 -d | openssl x509 -text -noout
```

---

## 5. Observability: Metrics, Logs, Traces

### Metrics Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Prometheus/Grafana                      │
│              (Metrics Aggregation & Viz)                 │
└────────────────────▲────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐      ┌─────────▼────────┐
│  Control Plane │      │   Data Plane     │
│    Metrics     │      │   (Envoy Stats)  │
│  (istiod, etc) │      │                  │
└────────────────┘      └──────────────────┘
                               │
                    ┌──────────┴──────────┐
                    │  Standard Metrics:  │
                    │  - Request rate     │
                    │  - Error rate       │
                    │  - Duration (p50,   │
                    │    p95, p99)        │
                    │  - Connection pool  │
                    └─────────────────────┘
```

**Key Metrics to Monitor:**

```promql
# Request rate (per second)
rate(istio_requests_total{reporter="source"}[1m])

# Error rate (%)
sum(rate(istio_requests_total{response_code=~"5.*"}[1m])) /
sum(rate(istio_requests_total[1m])) * 100

# P99 latency
histogram_quantile(0.99,
  sum(rate(istio_request_duration_milliseconds_bucket[1m])) by (le, destination_service_name))

# Connection pool exhaustion
envoy_cluster_upstream_cx_active / envoy_cluster_circuit_breakers_default_cx_open

# Sidecar resource usage
container_memory_working_set_bytes{container="istio-proxy"}
rate(container_cpu_usage_seconds_total{container="istio-proxy"}[1m])
```

### Distributed Tracing (Jaeger/Tempo)

```yaml
# Enable tracing in Istio
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  meshConfig:
    enableTracing: true
    defaultConfig:
      tracing:
        sampling: 100.0  # 100% for testing, 1-5% for production
        max_path_tag_length: 256
        custom_tags:
          environment:
            literal:
              value: production
          version:
            environment:
              name: APP_VERSION
    extensionProviders:
    - name: jaeger
      opentelemetry:
        service: jaeger-collector.observability.svc.cluster.local
        port: 4317
```

**Install Jaeger:**

```bash
# Using Jaeger operator
kubectl create namespace observability
kubectl create -n observability -f https://github.com/jaegertracing/jaeger-operator/releases/download/v1.51.0/jaeger-operator.yaml

# Deploy Jaeger instance
kubectl apply -f - <<EOF
apiVersion: jaegertracing.io/v1
kind: Jaeger
metadata:
  name: jaeger-prod
  namespace: observability
spec:
  strategy: production
  storage:
    type: elasticsearch
    options:
      es:
        server-urls: http://elasticsearch:9200
        index-prefix: jaeger
  query:
    replicas: 2
  collector:
    replicas: 3
    resources:
      requests:
        cpu: 500m
        memory: 1Gi
      limits:
        cpu: 1000m
        memory: 2Gi
EOF
```

### Access Logs (JSON Format)

```yaml
# Configure structured access logs
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: mesh-default
  namespace: istio-system
spec:
  accessLogging:
  - providers:
    - name: envoy
    filter:
      expression: response.code >= 400
  - providers:
    - name: custom-json-log
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio
  namespace: istio-system
data:
  mesh: |
    accessLogFile: /dev/stdout
    accessLogEncoding: JSON
    accessLogFormat: |
      {
        "start_time": "%START_TIME%",
        "method": "%REQ(:METHOD)%",
        "path": "%REQ(X-ENVOY-ORIGINAL-PATH?:PATH)%",
        "protocol": "%PROTOCOL%",
        "response_code": "%RESPONSE_CODE%",
        "response_flags": "%RESPONSE_FLAGS%",
        "bytes_received": "%BYTES_RECEIVED%",
        "bytes_sent": "%BYTES_SENT%",
        "duration": "%DURATION%",
        "upstream_service_time": "%RESP(X-ENVOY-UPSTREAM-SERVICE-TIME)%",
        "x_forwarded_for": "%REQ(X-FORWARDED-FOR)%",
        "user_agent": "%REQ(USER-AGENT)%",
        "request_id": "%REQ(X-REQUEST-ID)%",
        "authority": "%REQ(:AUTHORITY)%",
        "upstream_host": "%UPSTREAM_HOST%",
        "upstream_cluster": "%UPSTREAM_CLUSTER%",
        "upstream_local_address": "%UPSTREAM_LOCAL_ADDRESS%",
        "downstream_local_address": "%DOWNSTREAM_LOCAL_ADDRESS%",
        "downstream_remote_address": "%DOWNSTREAM_REMOTE_ADDRESS%",
        "route_name": "%ROUTE_NAME%"
      }
```

---

## 6. Multi-Cluster & Multi-Tenancy

### Multi-Cluster Deployment Models

```
1. Replicated Control Plane (Isolated)
┌──────────────────┐    ┌──────────────────┐
│   Cluster A      │    │   Cluster B      │
│  ┌────────────┐  │    │  ┌────────────┐  │
│  │Control Plane│ │    │  │Control Plane│ │
│  └────────────┘  │    │  └────────────┘  │
│  ┌────────────┐  │    │  ┌────────────┐  │
│  │ Data Plane │◄─┼────┼─►│ Data Plane │  │
│  └────────────┘  │    │  └────────────┘  │
└──────────────────┘    └──────────────────┘

2. Shared Control Plane (Primary-Remote)
┌──────────────────┐    ┌──────────────────┐
│ Primary Cluster  │    │ Remote Cluster   │
│  ┌────────────┐  │    │                  │
│  │Control Plane│──┼────┼─► (Config Only) │
│  └────────────┘  │    │                  │
│  ┌────────────┐  │    │  ┌────────────┐  │
│  │ Data Plane │◄─┼────┼─►│ Data Plane │  │
│  └────────────┘  │    │  └────────────┘  │
└──────────────────┘    └──────────────────┘
```

**Multi-Cluster Setup (Istio Primary-Remote):**

```bash
# Generate certs for multi-cluster
mkdir -p certs
cd certs

# Create root CA
openssl req -x509 -sha256 -nodes -days 365 -newkey rsa:2048 \
  -subj '/O=example Inc./CN=example.com' \
  -keyout root-ca.key -out root-ca.crt

# Create intermediate CAs for each cluster
for CLUSTER in cluster1 cluster2; do
  openssl req -newkey rsa:2048 -nodes \
    -keyout ${CLUSTER}-ca.key \
    -subj "/O=example Inc./CN=${CLUSTER}" \
    -out ${CLUSTER}-ca.csr
  
  openssl x509 -req -days 365 -CA root-ca.crt -CAkey root-ca.key \
    -set_serial 0 -in ${CLUSTER}-ca.csr -out ${CLUSTER}-ca.crt
done

# Install on primary cluster (cluster1)
kubectl create namespace istio-system --context=cluster1
kubectl create secret generic cacerts -n istio-system \
  --from-file=ca-cert.pem=cluster1-ca.crt \
  --from-file=ca-key.pem=cluster1-ca.key \
  --from-file=root-cert.pem=root-ca.crt \
  --from-file=cert-chain.pem=cluster1-ca.crt \
  --context=cluster1

istioctl install --context=cluster1 -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster1
      network: network1
EOF

# Install on remote cluster (cluster2)
kubectl create namespace istio-system --context=cluster2
kubectl create secret generic cacerts -n istio-system \
  --from-file=ca-cert.pem=cluster2-ca.crt \
  --from-file=ca-key.pem=cluster2-ca.key \
  --from-file=root-cert.pem=root-ca.crt \
  --from-file=cert-chain.pem=cluster2-ca.crt \
  --context=cluster2

# Get remote secret from cluster2
istioctl create-remote-secret \
  --context=cluster2 \
  --name=cluster2 | \
  kubectl apply -f - --context=cluster1

istioctl install --context=cluster2 -f - <<EOF
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
spec:
  values:
    global:
      meshID: mesh1
      multiCluster:
        clusterName: cluster2
      network: network1
      remotePilotAddress: <CLUSTER1_ISTIOD_IP>
  profile: remote
EOF

# Enable east-west gateway for cross-cluster traffic
kubectl apply -f samples/multicluster/expose-services.yaml --context=cluster1
kubectl apply -f samples/multicluster/expose-services.yaml --context=cluster2
```

### Multi-Tenancy Isolation

```yaml
# Namespace-scoped control plane (Istio)
apiVersion: install.istio.io/v1alpha1
kind: IstioOperator
metadata:
  name: tenant-a-control-plane
  namespace: tenant-a-system
spec:
  profile: default
  values:
    global:
      istioNamespace: tenant-a-system
    pilot:
      env:
        PILOT_SCOPE_GATEWAY_TO_NAMESPACE: "true"
  meshConfig:
    discoverySelectors:
    - matchLabels:
        tenant: tenant-a

---
# Network policy isolation between tenants
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-cross-tenant
  namespace: tenant-a
spec:
  podSelector: {}
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          tenant: tenant-a
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          tenant: tenant-a
  - to:  # Allow DNS
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - protocol: UDP
      port: 53
```

---

## 7. Performance Optimization & Resource Tuning

### Sidecar Resource Limits

```yaml
# Right-size sidecar resources
apiVersion: v1
kind: ConfigMap
metadata:
  name: istio-sidecar-injector
  namespace: istio-system
data:
  values: |
    global:
      proxy:
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 2000m
            memory: 1024Mi
      proxy_init:
        resources:
          requests:
            cpu: 10m
            memory: 10Mi
          limits:
            cpu: 100m
            memory: 50Mi

---
# Per-workload override via annotation
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-throughput-service
spec:
  template:
    metadata:
      annotations:
        sidecar.istio.io/proxyCPU: "500m"
        sidecar.istio.io/proxyCPULimit: "4000m"
        sidecar.istio.io/proxyMemory: "512Mi"
        sidecar.istio.io/proxyMemoryLimit: "2Gi"
```

### Sidecar Scoping (Reduce Config Size)

```yaml
# Scope sidecar to only necessary services
apiVersion: networking.istio.io/v1beta1
kind: Sidecar
metadata:
  name: optimized-sidecar
  namespace: production
spec:
  workloadSelector:
    labels:
      app: frontend
  egress:
  - hosts:
    - "production/*"  # Only services in same namespace
    - "istio-system/*"  # System services
    - "external/*"  # External services
  - hosts:
    - "*/*.example.com"  # Specific external domains
    port:
      number: 443
      protocol: TLS
  outboundTrafficPolicy:
    mode: REGISTRY_ONLY  # Block unconfigured egress
```