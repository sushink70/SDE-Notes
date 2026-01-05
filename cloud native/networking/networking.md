# Cloud-Native Networking & Security: Comprehensive Guide

**Summary:** Cloud-native networking abstracts infrastructure complexity through overlay networks, service meshes, and policy-driven security, requiring deep understanding of packet flows, identity-based security, and distributed system failure modes to build production-grade platforms.

---

## 1. Foundation: Container Networking Model

### 1.1 Network Namespace Isolation

Every container runs in an isolated network namespace with its own network stack:

```
Host Network Namespace
┌─────────────────────────────────────────────────────┐
│  eth0: 10.0.1.5                                     │
│  ┌─────────────────┐  ┌─────────────────┐          │
│  │ Container NS A  │  │ Container NS B  │          │
│  │ ┌─────────────┐ │  │ ┌─────────────┐ │          │
│  │ │ eth0        │ │  │ │ eth0        │ │          │
│  │ │ 172.17.0.2  │ │  │ │ 172.17.0.3  │ │          │
│  │ └──────┬──────┘ │  │ └──────┬──────┘ │          │
│  │        │        │  │        │        │          │
│  │      veth0      │  │      veth1      │          │
│  └────────┼────────┘  └────────┼────────┘          │
│           │                    │                    │
│      ┌────┴────────────────────┴────┐               │
│      │     docker0 / cni0           │               │
│      │     172.17.0.1               │               │
│      └──────────────┬────────────────┘               │
│                     │                                │
│              iptables/nftables                       │
│                     │                                │
└─────────────────────┼────────────────────────────────┘
                      │
                  Internet
```

**Key Concepts:**
- **veth pairs:** Virtual ethernet devices connecting container namespace to host bridge
- **Bridge device:** L2 switch (docker0, cni0) connecting all local containers
- **Route tables:** Each namespace has independent routing table
- **iptables chains:** NAT, filtering, and port mapping happen at host level

### 1.2 CNI (Container Network Interface) Architecture

CNI plugins are executables that configure container networking:

```
Container Runtime (containerd/cri-o)
            │
            ├─ calls CNI plugin binary
            │
    ┌───────▼────────┐
    │  CNI Plugin    │
    │  (executable)  │
    └───────┬────────┘
            │
    ┌───────▼────────────────────────────┐
    │  Network Configuration             │
    │  • Create veth pair                │
    │  • Assign IP from IPAM             │
    │  • Configure routes                │
    │  • Setup iptables rules            │
    │  • Configure bridge/overlay        │
    └────────────────────────────────────┘
```

**CNI Plugin Types:**
- **IPAM plugins:** IP address management (host-local, dhcp, static)
- **Main plugins:** Create network interfaces (bridge, macvlan, ipvlan, ptp)
- **Meta plugins:** Modify behavior (bandwidth, portmap, firewall, tuning)

**CNI Chain Execution:**
```
ADD operation → plugin1 → plugin2 → plugin3 → success/failure
DEL operation → plugin3 → plugin2 → plugin1 → cleanup
```

---

## 2. Kubernetes Network Model

### 2.1 The Kubernetes Network Requirements

Kubernetes imposes these fundamental requirements:

1. **Pod-to-Pod:** Every pod can communicate with every other pod without NAT
2. **Node-to-Pod:** Nodes can communicate with all pods without NAT
3. **Pod IP visibility:** Pod sees same IP address that others use to reach it

```
Node 1 (10.240.0.1)              Node 2 (10.240.0.2)
┌──────────────────┐              ┌──────────────────┐
│ Pod A            │              │ Pod C            │
│ IP: 10.244.1.5   │──────────────│ IP: 10.244.2.8   │
│                  │   Direct     │                  │
│ Pod B            │   Routing    │ Pod D            │
│ IP: 10.244.1.6   │   No NAT     │ IP: 10.244.2.9   │
└──────────────────┘              └──────────────────┘
         │                                 │
         └─────────────┬───────────────────┘
                       │
               Overlay Network
              (VXLAN/GENEVE/GRE)
                  or routed
```

### 2.2 Overlay vs. Routed Networks

**Overlay (VXLAN/GENEVE):**
```
Application Packet
┌────────────────────────────┐
│ App Data                   │
└────────────────────────────┘
         ↓ encapsulation
┌────────────────────────────┐
│ Outer IP: Node1 → Node2    │
│ ┌──────────────────────────┤
│ │ UDP Header (VXLAN 4789)  │
│ ┌──────────────────────────┤
│ │ VXLAN Header (VNI)       │
│ ┌──────────────────────────┤
│ │ Inner IP: Pod A → Pod C  │
│ │ ┌────────────────────────┤
│ │ │ App Data               │
│ │ └────────────────────────┘
└─┴──────────────────────────┘
```

**Routed (BGP/Native):**
```
Each node advertises pod CIDR to network
┌──────────────────────────────────┐
│ Router / Switch                  │
│ Routes:                          │
│  10.244.1.0/24 → Node1          │
│  10.244.2.0/24 → Node2          │
│  10.244.3.0/24 → Node3          │
└──────────────────────────────────┘
         │        │        │
    ┌────┴───┐  ┌─┴────┐  ┌┴─────┐
    │ Node1  │  │Node2 │  │Node3 │
    │        │  │      │  │      │
    └────────┘  └──────┘  └──────┘
```

**Tradeoffs:**
- **Overlay:** Works on any network, MTU overhead (~50 bytes), CPU overhead for encap/decap
- **Routed:** Better performance, requires BGP/route control, cloud provider support

### 2.3 Service Networking

Services provide stable endpoints with load balancing:

```
Service: web-frontend (ClusterIP: 10.96.10.50)
           ┌──────────┐
           │ kube-proxy│  watches Service endpoints
           └─────┬─────┘
                 │ programs rules
        ┌────────▼────────┐
        │   iptables /    │
        │   IPVS / eBPF   │
        └────────┬────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
┌───▼───┐   ┌───▼───┐   ┌───▼───┐
│ Pod A │   │ Pod B │   │ Pod C │
│ :8080 │   │ :8080 │   │ :8080 │
└───────┘   └───────┘   └───────┘
 Backend      Backend     Backend
```

**Service Types & Data Path:**

**ClusterIP (iptables mode):**
```
Client Pod
    │
    │ Connect to 10.96.10.50:80
    ▼
PREROUTING chain
    │
    │ DNAT: 10.96.10.50:80 → 10.244.x.y:8080
    │ (random backend selection via statistic module)
    ▼
FORWARD chain
    │
    ▼
Backend Pod
```

**NodePort:**
```
External Client
    │
    │ Connect to NodeIP:30080
    ▼
Node iptables PREROUTING
    │
    │ DNAT: NodeIP:30080 → ClusterIP:80
    ▼
ClusterIP iptables (as above)
    │
    ▼
Backend Pod
```

**LoadBalancer:**
```
External LoadBalancer (Cloud Provider)
    │ health checks NodePort
    │ distributes traffic to healthy nodes
    ▼
Multiple Nodes with NodePort
    │
    ▼
ClusterIP → Backend Pods
```

**IPVS Mode (higher performance):**
- Uses Linux IPVS kernel module
- More efficient than iptables for large numbers of services
- Supports more load balancing algorithms (rr, lc, dh, sh, sed, nq)
- Still uses iptables for packet filtering

**eBPF Mode (Cilium):**
- Bypasses iptables/IPVS entirely
- Socket-level load balancing
- Sub-microsecond latency
- No conntrack overhead

---

## 3. Service Mesh Architecture

### 3.1 Sidecar Proxy Model

```
Pod: web-frontend
┌────────────────────────────────────┐
│                                    │
│  ┌──────────────┐  ┌────────────┐ │
│  │ App Container│  │   Envoy    │ │
│  │   :8080      │  │  Sidecar   │ │
│  │              │  │   :15001   │ │
│  └──────┬───────┘  └─────┬──────┘ │
│         │                │        │
│         └────────────────┘        │
│           localhost                │
└────────────────┬───────────────────┘
                 │ all traffic intercepted
                 │ by iptables/eBPF
                 │
    ┌────────────▼──────────────┐
    │   Encrypted mTLS tunnel   │
    │   (Certificate-based)     │
    └────────────┬──────────────┘
                 │
            Remote Pod
```

**Traffic Interception:**
```
iptables rules in pod netns:
OUTPUT chain → intercept outbound → Envoy outbound listener
INPUT chain → intercept inbound → Envoy inbound listener

Envoy listeners:
15001: Outbound passthrough
15006: Inbound interception
15000: Admin interface
15090: Prometheus metrics
```

### 3.2 Control Plane Components

```
┌─────────────────────────────────────────────────┐
│           Service Mesh Control Plane            │
│                                                 │
│  ┌─────────────┐  ┌──────────┐  ┌───────────┐ │
│  │  Pilot/     │  │  Citadel/│  │  Galley/  │ │
│  │  Istiod     │  │  Cert    │  │  Config   │ │
│  │             │  │  Manager │  │  Validator│ │
│  └──────┬──────┘  └────┬─────┘  └─────┬─────┘ │
│         │              │              │        │
└─────────┼──────────────┼──────────────┼────────┘
          │              │              │
          │ xDS API      │ CSR/Certs    │ Config
          │ (gRPC)       │              │
          │              │              │
    ┌─────▼──────────────▼──────────────▼──────┐
    │         Envoy Sidecar Proxies            │
    │  • Service discovery (EDS)               │
    │  • Routing rules (RDS, VirtualHost)      │
    │  • TLS certificates (SDS)                │
    │  • Load balancing (CDS)                  │
    └──────────────────────────────────────────┘
```

**xDS Protocol (Envoy Discovery Service):**
- **LDS:** Listener Discovery Service (inbound/outbound listeners)
- **RDS:** Route Discovery Service (HTTP routing rules)
- **CDS:** Cluster Discovery Service (upstream service clusters)
- **EDS:** Endpoint Discovery Service (backend pod IPs)
- **SDS:** Secret Discovery Service (TLS certificates)

### 3.3 mTLS and Identity

```
Certificate Hierarchy:
┌──────────────────────┐
│   Root CA (Istio)    │
│   Self-signed or     │
│   External PKI       │
└──────────┬───────────┘
           │ signs
           ▼
┌──────────────────────┐
│ Workload Certificate │
│ CN: spiffe://cluster/│
│     ns/default/      │
│     sa/frontend      │
│ Valid: 24h           │
└──────────────────────┘
           │
           │ Rotation before expiry
           ▼
```

**mTLS Handshake Flow:**
```
Pod A Envoy                    Pod B Envoy
    │                              │
    ├──── TLS ClientHello ────────>│
    │    (ALPN: istio)              │
    │                               │
    │<─── ServerHello + Cert ───────┤
    │    (SPIFFE ID in SAN)         │
    │                               │
    ├──── Client Cert ─────────────>│
    │    (SPIFFE ID)                │
    │                               │
    │<─── Finished ─────────────────┤
    │                               │
    ├═══ Encrypted App Data ═══════>│
```

**SPIFFE Identity Format:**
```
spiffe://trust-domain/namespace/serviceaccount

Example:
spiffe://cluster.local/ns/prod/sa/payment-service
         └─trust domain─┘ └ns┘ └─────────────────┘
                                service account
```

---

## 4. Network Policy

### 4.1 Policy Model and Enforcement

```
Kubernetes NetworkPolicy (API object)
           │
           │ watches
           ▼
CNI Plugin (Calico/Cilium/etc)
           │
           │ translates to
           ▼
┌──────────────────────────┐
│ Enforcement Mechanism:   │
│ • iptables rules         │
│ • eBPF programs          │
│ • OVS flows              │
└──────────────────────────┘
           │
           │ applied at
           ▼
┌──────────────────────────┐
│ Pod Network Interface    │
│ (veth device)            │
└──────────────────────────┘
```

**Default Deny Architecture:**
```
No Policy:          With Default Deny:
┌────────┐          ┌────────────────┐
│  Pod   │          │   Pod          │
│        │          │   ┌──────────┐ │
│ ┌────┐ │          │   │ iptables │ │
│ │App │ │          │   │  DROP    │ │
│ └────┘ │          │   │  ALL     │ │
└────────┘          │   └────┬─────┘ │
All traffic         │        │       │
allowed             │   ┌────▼─────┐ │
                    │   │ Allowed  │ │
                    │   │ only by  │ │
                    │   │ explicit │ │
                    │   │ policy   │ │
                    │   └──────────┘ │
                    └────────────────┘
```

### 4.2 Policy Selectors and Match Logic

```
NetworkPolicy Evaluation:
┌─────────────────────────────────────┐
│ 1. Pod Selection (podSelector)      │
│    Determines which pods policy     │
│    applies to                       │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 2. Direction (Ingress/Egress)       │
│    Separate rules for inbound/      │
│    outbound                          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 3. Peer Selection:                  │
│    • podSelector (same namespace)   │
│    • namespaceSelector              │
│    • ipBlock (CIDR ranges)          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│ 4. Port/Protocol Matching           │
│    TCP/UDP/SCTP + port numbers      │
└─────────────────────────────────────┘
```

**Policy Combination (AND/OR logic):**
```
Multiple Ingress Rules = OR
Within a Rule:
  - Multiple from[] = OR
  - Multiple ports[] = OR

Multiple NetworkPolicies = Additive (OR)
  If ANY policy allows, traffic is permitted
```

### 4.3 Layer 7 Policy (Cilium/Calico)

```
L3/L4 NetworkPolicy:
Source: 10.1.1.0/24 → Dest: Pod X, Port 80
  ✓ Allows any HTTP traffic

L7 NetworkPolicy (Cilium):
Source: 10.1.1.0/24 → Dest: Pod X
  Protocol: HTTP
  Rules:
    - Path: /api/*
    - Method: GET, POST
    - Headers: X-API-Key exists
  ✓ Only allows specific HTTP requests
  ✗ Blocks: POST /admin, DELETE /api/users
```

**eBPF L7 Enforcement:**
```
Packet Flow:
  Socket → L7 eBPF hook → Protocol parser
           (HTTP/gRPC/Kafka)
              │
              ├─ Extract fields (path, method, headers)
              ├─ Match against policy
              └─ ALLOW / DROP

Advantages:
  - Socket-level enforcement (no extra hops)
  - Protocol-aware (understands HTTP, gRPC, DNS)
  - Low overhead (<1% CPU)
```

---

## 5. Load Balancing and Traffic Management

### 5.1 Ingress Architecture

```
                    Internet
                       │
                       ▼
        ┌──────────────────────────┐
        │  External LoadBalancer   │
        │  (Cloud Provider / HW)   │
        └──────────┬───────────────┘
                   │
        ┌──────────▼───────────┐
        │  Ingress Controller  │
        │  (nginx/traefik/     │
        │   envoy/haproxy)     │
        └──────────┬───────────┘
                   │
        ┌──────────▼───────────────────────┐
        │      Routing Decision            │
        │  Host: api.example.com           │
        │  Path: /users →  Service A       │
        │  Path: /orders → Service B       │
        └──────────┬───────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    Service A  Service B  Service C
        │          │          │
        ▼          ▼          ▼
      Pods       Pods       Pods
```

**Ingress vs. Gateway API:**
```
Ingress (Legacy):
- Single resource type
- Limited expressiveness
- Controller-specific annotations

Gateway API (Modern):
┌──────────────┐
│ GatewayClass │  Infrastructure template
└──────┬───────┘
       │
┌──────▼──────┐
│  Gateway    │  Listener configuration
└──────┬──────┘
       │
┌──────▼──────┐
│ HTTPRoute   │  Routing rules (L7)
│ TCPRoute    │  
│ TLSRoute    │
└─────────────┘

Multi-resource, role-oriented, more expressive
```

### 5.2 East-West Load Balancing

```
Client Pod Request Flow:
┌────────────────────────────────────┐
│ 1. DNS Resolution                  │
│    myservice.default.svc           │
│    → CoreDNS → ClusterIP           │
└──────────────┬─────────────────────┘
               │
┌──────────────▼─────────────────────┐
│ 2. Connection Establishment        │
│    connect(ClusterIP:80)           │
│    → kube-proxy rules intercept    │
└──────────────┬─────────────────────┘
               │
┌──────────────▼─────────────────────┐
│ 3. Backend Selection               │
│    iptables statistic module       │
│    or IPVS scheduler               │
│    Randomly selects backend pod    │
└──────────────┬─────────────────────┘
               │
┌──────────────▼─────────────────────┐
│ 4. Connection Tracking             │
│    conntrack entry created         │
│    ensures session affinity        │
└──────────────┬─────────────────────┘
               │
               ▼
          Backend Pod
```

**Load Balancing Algorithms:**
- **Round Robin:** Distributes evenly across backends
- **Least Connection:** Sends to backend with fewest active connections
- **Ring Hash:** Consistent hashing for session affinity
- **Maglev:** Google's consistent hashing with faster lookup
- **Locality-aware:** Prefers same-zone/node backends

### 5.3 Service Mesh Traffic Management

```
VirtualService (Istio):
┌────────────────────────────────┐
│ reviews.default.svc            │
│                                │
│ Route Rules:                   │
│ ┌────────────────────────────┐ │
│ │ Match: headers[end-user]   │ │
│ │        == "jason"          │ │
│ │ Route: reviews-v2 (100%)   │ │
│ └────────────────────────────┘ │
│                                │
│ ┌────────────────────────────┐ │
│ │ Default:                   │ │
│ │ - reviews-v1: 90%          │ │
│ │ - reviews-v2: 10%          │ │
│ └────────────────────────────┘ │
└────────────────────────────────┘
         │
         ▼
    Envoy Proxy
         │
    ┌────┼────┐
    │    │    │
    v1   v2   v3
```

**Canary Deployment Pattern:**
```
Phase 1: Baseline
  v1: 100%

Phase 2: Canary
  v1: 95%
  v2: 5%  ← Monitor metrics

Phase 3: Expand
  v1: 50%
  v2: 50%

Phase 4: Complete
  v2: 100%
  (v1 decommissioned)
```

---

## 6. Service Discovery

### 6.1 DNS-Based Discovery

```
CoreDNS Architecture:
┌──────────────────────────────────┐
│ CoreDNS Pod (kube-system)        │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ kubernetes plugin            │ │
│ │ • Watches Services/Pods API  │ │
│ │ • Generates A/SRV records    │ │
│ └──────────────────────────────┘ │
│                                  │
│ ┌──────────────────────────────┐ │
│ │ Cache layer                  │ │
│ └──────────────────────────────┘ │
└──────────────┬───────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
App Pod    App Pod    App Pod
  │          │          │
  │ /etc/resolv.conf    │
  │ nameserver 10.96.0.10
  └──────────────────────┘
```

**DNS Record Format:**
```
Service DNS:
  <service>.<namespace>.svc.<cluster-domain>
  Example: postgres.database.svc.cluster.local
  Returns: ClusterIP

Headless Service (clusterIP: None):
  <service>.<namespace>.svc.<cluster-domain>
  Returns: Multiple A records (one per pod)
  Example:
    mysql.database.svc.cluster.local
    → 10.244.1.5
    → 10.244.2.8
    → 10.244.3.12

Pod DNS:
  <pod-ip-with-dashes>.<namespace>.pod.<cluster-domain>
  Example: 10-244-1-5.default.pod.cluster.local

SRV Records (for ports):
  _<port-name>._<protocol>.<service>.<namespace>.svc
  Example: _http._tcp.web.default.svc.cluster.local
```

### 6.2 Endpoint Slices

```
Traditional Endpoints:
┌───────────────────────┐
│ Endpoints: myservice  │
│ All 1000 pod IPs      │
│ 50KB object           │
└───────────────────────┘
    │
    │ Every update = 50KB broadcast
    │ to all watchers
    ▼
Scale issues at 1000+ pods

EndpointSlices:
┌────────────────┐ ┌────────────────┐ ┌────────────────┐
│ Slice 1        │ │ Slice 2        │ │ Slice N        │
│ 100 endpoints  │ │ 100 endpoints  │ │ 100 endpoints  │
│ 5KB            │ │ 5KB            │ │ 5KB            │
└────────────────┘ └────────────────┘ └────────────────┘
    │                  │                  │
    │ Only changed slice updated           │
    ▼                                      ▼
Better scalability, less network traffic
```

### 6.3 Service Mesh Discovery (xDS)

```
Control Plane Push Model:
┌──────────────────────┐
│ Istiod / Pilot       │
│                      │
│ Watches:             │
│ • Services           │
│ • Pods               │
│ • Endpoints          │
│ • VirtualServices    │
└──────────┬───────────┘
           │
           │ xDS gRPC streams
           │ (bidirectional)
    ┌──────┼──────┐
    │      │      │
    ▼      ▼      ▼
 Envoy  Envoy  Envoy
 (Pod1) (Pod2) (Pod3)
    │      │      │
    └──────┼──────┘
           │
   Only changed clusters
   pushed to affected proxies
```

**Incremental xDS:**
- Only changes are sent (not full state)
- Reduces bandwidth and CPU
- Faster convergence time
- Critical for large clusters (10k+ pods)

---

## 7. Network Observability

### 7.1 Metrics Collection

```
Prometheus Architecture:
┌─────────────────────────────────────┐
│ Application Pod                     │
│ ┌─────────────┐  ┌───────────────┐ │
│ │ App         │  │ Envoy Sidecar │ │
│ │ :8080       │  │ :15090/stats  │ │
│ └─────────────┘  └───────────────┘ │
└──────────────────────┬──────────────┘
                       │ scrape /metrics
                       │ (HTTP GET)
┌──────────────────────▼──────────────┐
│ Prometheus Server                   │
│ • Service discovery (K8s API)       │
│ • Scrape metrics every 15s          │
│ • Store in TSDB                     │
│ • PromQL queries                    │
└──────────────────────┬──────────────┘
                       │
┌──────────────────────▼──────────────┐
│ Grafana / Alertmanager              │
└─────────────────────────────────────┘
```

**Key Network Metrics:**
```
Envoy metrics (istio_*):
- istio_requests_total (counter)
- istio_request_duration_milliseconds (histogram)
- istio_request_bytes / response_bytes (histogram)
- istio_tcp_connections_opened/closed (counter)

CNI/kube-proxy metrics:
- container_network_transmit_bytes_total
- container_network_receive_bytes_total
- container_network_transmit_packets_dropped_total
- iptables_rules_total

Service mesh control plane:
- pilot_xds_pushes (rate of config updates)
- pilot_proxy_convergence_time (time to apply config)
- galley_validation_passed/failed
```

### 7.2 Distributed Tracing

```
Request Flow with Tracing:
┌─────────────────────────────────────────────────┐
│ Trace ID: abc-123-def                           │
│                                                 │
│ Span 1: frontend (100ms)                        │
│ ├──────────────────────────────────────────────┤
│ │ HTTP GET /api                                │
│ │ Span 2: api-gateway (80ms)                   │
│ │ ├─────────────────────────────────────────┐  │
│ │ │ Span 3: auth-service (20ms)             │  │
│ │ │ └────────────┘                           │  │
│ │ │ Span 4: product-service (40ms)          │  │
│ │ │     └──────────────────┘                 │  │
│ │ └──────────────────────────────────────────┘  │
│ └──────────────────────────────────────────────┘
└─────────────────────────────────────────────────┘

Headers propagated:
  X-B3-TraceId: abc-123-def
  X-B3-SpanId: span-456-ghi
  X-B3-ParentSpanId: span-123-jkl
```

**OpenTelemetry Architecture:**
```
Application
    │
    │ OTLP (gRPC/HTTP)
    ▼
OTel Collector (DaemonSet)
    │
    ├─ Receivers (OTLP, Jaeger, Zipkin)
    ├─ Processors (batch, filter, attributes)
    ├─ Exporters (Jaeger, Tempo, Zipkin)
    │
    ▼
Tracing Backend
```

### 7.3 Flow Logging

```
Network Flow Architecture:
┌────────────────────────────────┐
│ eBPF Programs (per pod)        │
│ • Socket attach                │
│ • Packet capture               │
│ • Connection tracking          │
└───────────┬────────────────────┘
            │ Aggregated flows
            ▼
┌────────────────────────────────┐
│ Hubble / Flow Collector        │
│ • 5-tuple flows                │
│ • L7 protocol visibility       │
│ • DNS queries                  │
│ • Policy verdicts              │
└───────────┬────────────────────┘
            │
            ▼
┌────────────────────────────────┐
│ Storage (S3/Loki/ClickHouse)   │
└────────────────────────────────┘

Flow Record:
  Source: 10.244.1.5:52341
  Dest: 10.244.2.8:8080
  Protocol: TCP
  Bytes: 1024
  Packets: 8
  Verdict: ALLOWED (policy ID 42)
  L7: HTTP GET /api/v1/users
```

---

## 8. Zero Trust Networking

### 8.1 Identity-Based Security

```
Traditional Network Security:
┌────────────────────────────────┐
│ DMZ                            │
│ ┌────┐ ┌────┐ ┌────┐          │
│ │Web │ │API │ │App │ Trusted │
│ └────┘ └────┘ └────┘   Zone   │
└────────────────────────────────┘
      │ Firewall
      │ (IP-based)
      ▼
┌────────────────────────────────┐
│ Internal Network               │
│ "Trusted" - any access allowed │
└────────────────────────────────┘

Zero Trust Model:
┌────────────────────────────────┐
│ Every Connection Verified      │
│                                │
│ ┌────┐  mTLS  ┌────┐  mTLS    │
│ │Web │◄──────►│API │◄────────►│
│ │    │  AuthZ │    │   AuthZ  │
│ └────┘        └────┘          │
│   ▲              ▲             │
│   │ Policy       │ Policy      │
│   │ Check        │ Check       │
│   └──────────────┴─────────────┤
│     Identity Provider          │
│     (SPIFFE/Workload ID)       │
└────────────────────────────────┘

Principles:
- Never trust, always verify
- Least privilege access
- Assume breach
```

### 8.2 Workload Identity

```
SPIFFE Identity Lifecycle:
┌──────────────────────────────┐
│ 1. Workload Starts           │
│    K8s creates pod with SA   │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│ 2. Identity Attestation      │
│    SPIRE Agent validates:    │
│    • Pod UID                 │
│    • Namespace               │
│    • Service Account         │
│    • Node identity           │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│ 3. Certificate Issuance      │
│    SPIRE Server issues cert: │
│    CN: spiffe://trust/ns/sa  │
│    TTL: 1 hour               │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│ 4. Certificate Rotation      │
│    Before expiry, workload   │
│    requests new certificate  │
│    Zero-downtime rotation    │
└──────────────────────────────┘
```

**Workload Attestation Methods:**
- **Kubernetes:** SA token, pod UID, node attestation
- **Unix:** Process PID, UID, parent process chain
- **TPM:** Hardware-backed attestation
- **AWS:** IAM role, instance metadata
- **GCP:** Service account, metadata server

### 8.3 Authorization Policy

```
Policy Decision Flow:
┌────────────────────────────────┐
│ Request: Pod A → Pod B         │
│ Method: GET /api/data          │
└───────────┬────────────────────┘
            │
┌───────────▼────────────────────┐
│ 1. Authentication              │
│    • Verify mTLS certificate   │
│    • Extract SPIFFE ID         │
│    Valid? Yes ─────────────────┤
└────────────────────────────────┘
            │
┌───────────▼────────────────────┐
│ 2. Authorization               │
│    Check policy:               │
│    Allow if:                   │
│      source == ns/frontend/*   │
│      AND method == GET         │
│      AND path == /api/*        │
│    Match? Yes ─────────────────┤
└────────────────────────────────┘
            │
┌───────────▼────────────────────┐
│ 3. Rate Limiting               │
│    Check quota: 100 req/min    │
│    Current: 45                 │
│    Within limit? Yes ───────────
└────────────────────────────────┘
            │
            ▼
      Request Allowed

OPA (Open Policy Agent) Integration:
Application → Envoy → OPA → Decision
                      │
                      └─ Rego policies
                         evaluate attributes
```

---

## 9. Threat Models & Security

### 9.1 Attack Surface

```
Cloud-Native Attack Vectors:
┌────────────────────────────────────────┐
│ Container Escape                       │
│ • Kernel exploits                      │
│ • Misconfigured capabilities           │
│ • Privileged containers                │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│ Network-Based Attacks                  │
│ • Pod-to-pod lateral movement          │
│ • Service account token theft          │
│ • DNS poisoning                        │
│ • Man-in-the-middle (no mTLS)          │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│ Control Plane Compromise               │
│ • API server RBAC bypass               │
│ • etcd data exfiltration               │
│ • Certificate authority compromise     │
└────────────┬───────────────────────────┘
             │
┌────────────▼───────────────────────────┐
│ Supply Chain Attacks                   │
│ • Malicious container images           │
│ • Compromised registries               │
│ • Dependency vulnerabilities           │
└────────────────────────────────────────┘
```

### 9.2 Defense in Depth

```
Security Layers:
┌─────────────────────────────────────────┐
│ Layer 7: Application                    │
│ • Input validation                      │
│ • OWASP top 10 protections              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 6: Service Mesh (mTLS)            │
│ • Encrypted traffic                     │
│ • Identity-based auth                   │
│ • Authorization policies                │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 5: Network Policy                 │
│ • L3/L4 filtering                       │
│ • Namespace isolation                   │
│ • Egress controls                       │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 4: Pod Security                   │
│ • Security contexts                     │
│ • Pod Security Standards                │
│ • Runtime protection (Falco)            │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 3: Container Runtime              │
│ • Seccomp profiles                      │
│ • AppArmor/SELinux                      │
│ • Capability dropping                   │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 2: Host Security                  │
│ • Kernel hardening                      │
│ • Node isolation                        │
│ • Immutable infrastructure              │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│ Layer 1: Physical/Cloud Infrastructure  │
│ • Network segmentation                  │
│ • Secure boot                           │
│ • Hardware attestation                  │
└─────────────────────────────────────────┘
```

### 9.3 Common Vulnerabilities

**CVE Patterns:**
```
1. Unencrypted Traffic
   Risk: MitM, credential theft
   Mitigation: mTLS everywhere, no plaintext

2. Overly Permissive Network Policies
   Risk: Lateral movement
   Mitigation: Default deny, explicit allow

3. Weak Pod Security
   Risk: Container escape
   Mitigation: Non-root, drop caps, read-only FS

4. Service Account Token Abuse
   Risk: Privilege escalation
   Mitigation: Bound tokens, minimal RBAC

5. Insecure Service Mesh Config
   Risk: AuthN/AuthZ bypass
   Mitigation: PeerAuthentication STRICT, AuthZ

6. DNS Spoofing
   Risk: Traffic redirection
   Mitigation: DNSSEC, secure CoreDNS config

7. Egress to C2 Servers
   Risk: Data exfiltration
   Mitigation: Egress filtering, allow-list only
```

---

## 10. Multi-Tenancy & Isolation

### 10.1 Namespace Isolation

```
Hard Multi-Tenancy:
┌──────────────────────────────────────┐
│ Cluster                              │
│                                      │
│ ┌─────────────┐  ┌─────────────┐    │
│ │ NS: tenant-a│  │ NS: tenant-b│    │
│ │             │  │             │    │
│ │ Network     │  │ Network     │    │
│ │ Policy:     │  │ Policy:     │    │
│ │ Default     │  │ Default     │    │
│ │ DENY ALL    │  │ DENY ALL    │    │
│ │             │  │             │    │
│ │ ResourceQ:  │  │ ResourceQ:  │    │
│ │ 10 CPU      │  │ 10 CPU      │    │
│ │ 20Gi mem    │  │ 20Gi mem    │    │
│ │             │  │             │    │
│ │ No cross-   │  │ No cross-   │    │
│ │ tenant      │  │ tenant      │    │
│ │ traffic     │  │ traffic     │    │
│ └─────────────┘  └─────────────┘    │
└──────────────────────────────────────┘
```

**Isolation Dimensions:**
1. **Network:** NetworkPolicy, separate VPCs
2. **Compute:** Node pools, pod/container limits
3. **Storage:** StorageClass, PVC per tenant
4. **API:** RBAC, admission webhooks
5. **Observability:** Separate metrics namespaces

### 10.2 Virtual Clusters

```
vCluster Architecture:
┌────────────────────────────────────┐
│ Host Cluster                       │
│                                    │
│ ┌──────────────────────────────┐  │
│ │ vCluster Namespace           │  │
│ │                              │  │
│ │ ┌─────────────────────────┐  │  │
│ │ │ vCluster Control Plane  │  │  │
│ │ │ (API, etcd, controller) │  │  │
│ │ └───────────┬─────────────┘  │  │
│ │             │                │  │
│ │    ┌────────▼────────┐       │  │
│ │    │ Syncer          │       │  │
│ │    │ Virtual → Real  │       │  │
│ │    └────────┬────────┘       │  │
│ │             │                │  │
│ │    ┌────────▼────────┐       │  │
│ │    │ Workload Pods   │       │  │
│ │    │ (in host)       │       │  │
│ │    └─────────────────┘       │  │
│ └──────────────────────────────┘  │
└────────────────────────────────────┘

Tenant sees: Full cluster
Reality: Namespace in host cluster
```

---

## 11. Performance Optimization

### 11.1 Connection Pooling

```
Without Connection Pool:
Client → [NEW TCP] → Server
Client → [NEW TCP] → Server
Client → [NEW TCP] → Server
  Overhead: 3-way handshake each time

With Connection Pool:
┌───────────────────────────┐
│ Connection Pool           │
│ ┌─────┐ ┌─────┐ ┌─────┐  │
│ │Conn1│ │Conn2│ │Conn3│  │
│ └──┬──┘ └──┬──┘ └──┬──┘  │
└───┼──────┼──────┼─────────┘
    │      │      │
    └──────┴──────┴─► Server
   Reuse existing connections
   
Envoy Cluster Configuration:
- max_connections: 1024
- max_pending_requests: 1024
- max_requests: 1024
- max_retries: 3
- connect_timeout: 5s
```

### 11.2 Circuit Breaking

```
Circuit States:
┌────────────────────────────────┐
│ CLOSED                         │
│ Normal operation               │
│ Track failures                 │
└──────────┬─────────────────────┘
           │ Threshold exceeded
           │ (5 failures)
┌──────────▼─────────────────────┐
│ OPEN                           │
│ Fail fast, don't send requests │
│ Set timeout (30s)              │
└──────────┬─────────────────────┘
           │ Timeout expires
┌──────────▼─────────────────────┐
│ HALF-OPEN                      │
│ Try limited requests           │
│ Success → CLOSED               │
│ Failure → OPEN                 │
└────────────────────────────────┘
```

### 11.3 TCP Tuning

```
Performance Parameters:
┌─────────────────────────────────────┐
│ Socket Buffers                      │
│ net.core.rmem_max = 134217728       │
│ net.core.wmem_max = 134217728       │
│ net.ipv4.tcp_rmem = 4096 87380 6M   │
│ net.ipv4.tcp_wmem = 4096 65536 4M   │
└─────────────────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│ Connection Tracking                 │
│ net.netfilter.nf_conntrack_max      │
│   = 1048576                         │
│ net.netfilter.nf_conntrack_buckets  │
│   = 262144                          │
└─────────────────────────────────────┘
           │
┌──────────▼──────────────────────────┐
│ Fast Open / Reuse                   │
│ net.ipv4.tcp_fastopen = 3           │
│ net.ipv4.tcp_tw_reuse = 1           │
└─────────────────────────────────────┘
```

---

## 12. Failure Modes

### 12.1 Split Brain Scenarios

```
Network Partition:
Zone A              Zone B
┌─────────┐        ┌─────────┐
│ Leader  │  ╳╳╳╳  │ Node    │
│ Writes  │        │ Isolated│
└─────────┘        └─────────┘
     │                  │
     │                  │ Times out
     │                  ▼
     │            Elect new leader?
     │            Data divergence!
     ▼
Quorum-based systems (etcd):
- Requires majority (N/2 + 1)
- Prevents split brain
- Zone A retains quorum (if 3 of 5 nodes)
- Zone B cannot make progress

Mitigation:
- Odd number of control plane nodes
- Distribute across failure domains
- Monitor quorum health
```

### 12.2 DNS Failure Cascades

```
DNS Outage Impact:
┌──────────────────────────────┐
│ CoreDNS Pods Crash           │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│ All Service Discovery Fails  │
│ • New connections fail       │
│ • Existing connections OK    │
└──────────┬───────────────────┘
           │
┌──────────▼───────────────────┐
│ Cascading Service Failures   │
│ • Health checks fail (DNS)   │
│ • Circuit breakers open      │
│ • Entire mesh unstable       │
└──────────────────────────────┘

Mitigations:
1. ndots optimization
(reduce DNS lookups)
2. Local DNS cache (NodeLocal DNSCache)
3. Negative TTL tuning
4. Multiple CoreDNS replicas with anti-affinity
5. DNS over TCP fallback
```

### 12.3 Control Plane Overload

```
API Server Saturation:
┌────────────────────────────────┐
│ High Pod Churn                 │
│ 1000 pods/sec created/deleted  │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ API Server Load Spike          │
│ • etcd write amplification     │
│ • Watch notification storm     │
│ • CPU/Memory exhaustion        │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Control Plane Degradation      │
│ • API requests timeout         │
│ • Controllers lag              │
│ • Webhook timeouts             │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Cluster-Wide Impact            │
│ • New pods not scheduled       │
│ • Service endpoints not updated│
│ • Network policy not enforced  │
└────────────────────────────────┘

Protection Mechanisms:
- API Priority and Fairness (APF)
- Request rate limiting
- Client-side throttling
- Event rate limiting
- Watch bookmarks for efficiency
```

---

## 13. Cross-Cluster Networking

### 13.1 Multi-Cluster Service Mesh

```
Federated Service Mesh:
┌─────────────────────┐    ┌─────────────────────┐
│ Cluster A (US-East) │    │ Cluster B (EU-West) │
│                     │    │                     │
│ ┌─────────────────┐ │    │ ┌─────────────────┐ │
│ │ Istiod          │ │    │ │ Istiod          │ │
│ │ Root CA: shared │◄┼────┼►│ Root CA: shared │ │
│ └────────┬────────┘ │    │ └────────┬────────┘ │
│          │          │    │          │          │
│    ┌─────▼──────┐   │    │   ┌──────▼─────┐   │
│    │ Service A  │   │    │   │ Service B  │   │
│    │ (4 replicas)   │    │   │ (4 replicas)   │
│    └────────────┘   │    │   └────────────┘   │
└─────────────────────┘    └─────────────────────┘
         │                          │
         └──────────────┬───────────┘
                        │
              East-West Gateway
                (mTLS tunnel)
                        
Traffic Flow:
Service A (Cluster A) → East-West GW (A)
                      → mTLS tunnel
                      → East-West GW (B)
                      → Service B (Cluster B)
```

**Service Discovery Across Clusters:**
```
ServiceEntry (Istio):
┌────────────────────────────────┐
│ hosts: service-b.cluster-b.svc │
│ endpoints:                     │
│   - address: 52.12.34.56       │
│     ports: { https: 15443 }    │
│   locality: eu-west-1          │
└────────────────────────────────┘
         │
         ▼
Envoy routes traffic to remote endpoint
with locality-aware load balancing
```

### 13.2 Cluster Mesh (Cilium)

```
Cilium Cluster Mesh Architecture:
┌─────────────────────────────────────┐
│ Cluster A                           │
│ ┌─────────────────────────────────┐ │
│ │ clustermesh-apiserver           │ │
│ │ • Exposes pod/service state     │ │
│ │ • Authenticated via certificates│ │
│ └──────────┬──────────────────────┘ │
│            │                        │
│     ┌──────▼──────┐                 │
│     │ Cilium Agent│                 │
│     │ • Syncs state                │
│     │ • Programs eBPF              │
│     └─────────────┘                 │
└────────────┬────────────────────────┘
             │ mTLS connection
┌────────────▼────────────────────────┐
│ Cluster B                           │
│     ┌─────────────┐                 │
│     │ Cilium Agent│                 │
│     │ • Receives updates           │
│     │ • Direct pod routing         │
│     └─────────────┘                 │
└─────────────────────────────────────┘

Global Service:
  service-x.namespace.svc.clusterset.local
  → Load balances across all clusters
  → Locality-aware routing
```

---

## 14. Compliance & Audit

### 14.1 Traffic Encryption Verification

```
Compliance Check Flow:
┌────────────────────────────────┐
│ Policy: All traffic must be    │
│ encrypted with TLS 1.3+        │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Monitoring Layer               │
│ • Network flow analysis        │
│ • Certificate validation       │
│ • Protocol detection           │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Violations Detected:           │
│ • Plaintext HTTP detected      │
│ • TLS 1.0/1.1 usage            │
│ • Self-signed cert without CA  │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Alerting & Remediation         │
│ • Block traffic (enforce mode) │
│ • Alert SecOps                 │
│ • Quarantine workload          │
└────────────────────────────────┘
```

**Audit Logging:**
```
Network Policy Audit:
- WHO: source workload identity
- WHAT: protocol, ports, paths
- WHEN: timestamp (nanosecond precision)
- WHERE: source/dest IPs, clusters
- WHY: policy rule ID, verdict
- HOW: encrypted? protocol version?

Storage: Immutable log (S3, GCS)
Retention: 90+ days
Format: Structured (JSON/Protocol Buffers)
```

### 14.2 PCI-DSS / HIPAA Patterns

```
Segmentation for Compliance:
┌──────────────────────────────────────┐
│ Cardholder Data Environment (CDE)    │
│                                      │
│ ┌──────────────────────────────────┐ │
│ │ payment-processing namespace     │ │
│ │                                  │ │
│ │ NetworkPolicy:                   │ │
│ │ • Ingress: Only from web-tier    │ │
│ │ • Egress: Only to DB, PSP        │ │
│ │ • Deny all other traffic         │ │
│ │                                  │ │
│ │ Service Mesh:                    │ │
│ │ • mTLS STRICT                    │ │
│ │ • AuthZ on every request         │ │
│ │ • Full request/response logging  │ │
│ └──────────────────────────────────┘ │
└──────────────────────────────────────┘
         │ Firewall (iptables/eBPF)
         │ Only specific ports
         ▼
┌──────────────────────────────────────┐
│ Non-CDE Environment                  │
│ (General applications)               │
└──────────────────────────────────────┘
```

---

## 15. IPv6 and Dual-Stack

### 15.1 Dual-Stack Architecture

```
Dual-Stack Pod:
┌────────────────────────────────┐
│ Pod                            │
│ ┌────────────────────────────┐ │
│ │ eth0:                      │ │
│ │ IPv4: 10.244.1.5           │ │
│ │ IPv6: fd00:1234::5         │ │
│ └────────────────────────────┘ │
└──────────────┬─────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
IPv4 Route  IPv6 Route  Service
10.244/16   fd00::/48   Dual IPs
```

**Service with Dual-Stack:**
```
Service: web
  ClusterIP: 10.96.10.50
  ClusterIP (IPv6): fd00:1234:5678::50
  
DNS returns:
  A record: 10.96.10.50
  AAAA record: fd00:1234:5678::50

Client prefers IPv6 (Happy Eyeballs):
  Try IPv6 first
  Fallback to IPv4 if timeout
```

---

## 16. eBPF-Based Networking

### 16.1 eBPF Program Flow

```
Packet Processing Path:
┌────────────────────────────────────┐
│ Physical NIC                       │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│ XDP (eXpress Data Path)            │
│ • Earliest hook point              │
│ • Can drop/modify/redirect         │
│ • Used for: DDoS, LB, firewall     │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│ TC (Traffic Control)               │
│ • Ingress/Egress hooks             │
│ • Network policy enforcement       │
│ • Packet encapsulation             │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│ Socket Hooks                       │
│ • Socket creation/connect          │
│ • Service load balancing           │
│ • Direct server return             │
└──────────┬─────────────────────────┘
           │
           ▼
       Application
```

**eBPF Map Architecture:**
```
User Space                 Kernel Space
┌─────────────┐           ┌──────────────┐
│ Control     │           │ eBPF Program │
│ Plane       │           │              │
│ (cilium)    │           │   reads      │
└──────┬──────┘           │      │       │
       │                  │      ▼       │
       │ updates          │ ┌──────────┐ │
       ├─────────────────►│ │ eBPF Map │ │
       │                  │ │ (hash)   │ │
       │                  │ │          │ │
       │                  │ │ Key:     │ │
       │                  │ │ PodIP    │ │
       │                  │ │ Value:   │ │
       │                  │ │ Policy   │ │
       │                  │ └──────────┘ │
       │                  └──────────────┘
       │
Fast lookups (O(1))
No syscall overhead
```

### 16.2 Service Load Balancing with eBPF

```
Socket-Level Load Balancing:
┌────────────────────────────────────┐
│ Application calls connect()        │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│ eBPF hook at socket layer          │
│ • Intercepts destination IP:port   │
│ • Looks up service in map          │
│ • Selects backend (consistent hash)│
│ • Rewrites dest to backend pod IP  │
└──────────┬─────────────────────────┘
           │
┌──────────▼─────────────────────────┐
│ Direct connection to backend       │
│ • No additional hops               │
│ • No NAT/conntrack overhead        │
│ • Sub-microsecond latency          │
└────────────────────────────────────┘

Traditional iptables:
  Application → iptables (NAT)
              → conntrack
              → routing
              → backend
  
eBPF:
  Application → eBPF (rewrite)
              → direct to backend
```

---

## 17. Chaos Engineering for Networks

### 17.1 Network Failure Injection

```
Chaos Scenarios:
┌────────────────────────────────┐
│ Latency Injection              │
│ Add 100ms delay to 10% traffic │
│ between service A → B          │
└──────────┬─────────────────────┘
           │ Implemented via:
           │ • TC qdisc (netem)
           │ • Envoy fault injection
           │ • eBPF packet delay
           │
┌──────────▼─────────────────────┐
│ Packet Loss                    │
│ Drop 5% of packets             │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Bandwidth Limitation           │
│ Throttle to 1Mbps              │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Partition Injection            │
│ Block all traffic to zone B    │
└────────────────────────────────┘

Observe:
  • Retry behavior
  • Circuit breaker activation
  • Fallback mechanisms
  • SLA impact
```

---

## 18. Performance Benchmarking

### 18.1 Network Latency Testing

```
Latency Components:
┌────────────────────────────────┐
│ Application Processing Time    │
│ ~1-10ms                        │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Service Mesh Overhead          │
│ • mTLS handshake: 1-2ms        │
│ • Envoy processing: 0.5-1ms    │
│ • Policy checks: 0.1-0.5ms     │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Network Transit                │
│ • Same node: 0.1ms             │
│ • Same zone: 0.5-1ms           │
│ • Cross-zone: 2-10ms           │
│ • Cross-region: 50-200ms       │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Total P99 Latency              │
│ • Intra-zone: 15-25ms          │
│ • Cross-zone: 25-50ms          │
└────────────────────────────────┘
```

### 18.2 Throughput Testing

```
Maximum Throughput Factors:
┌────────────────────────────────┐
│ Network Bandwidth              │
│ • Node NIC: 10-100 Gbps        │
│ • Pod limit: Share of node BW  │
│ • CNI overhead: 5-15%          │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ CPU Capacity                   │
│ • Encryption (TLS): CPU-bound  │
│ • iptables: CPU for rule eval  │
│ • eBPF: Minimal CPU            │
└──────────┬─────────────────────┘
           │
┌──────────▼─────────────────────┐
│ Connection Limits              │
│ • Envoy max_connections        │
│ • OS file descriptor limit     │
│ • conntrack table size         │
└────────────────────────────────┘

Typical Results (iperf3):
  iptables: 8-12 Gbps
  IPVS: 15-20 Gbps
  eBPF: 25-35 Gbps
  (on 40 Gbps link)
```

---

## 19. Emerging Technologies

### 19.1 Ambient Mesh (Istio)

```
Traditional Sidecar:
┌────────────────────┐
│ Pod                │
│ ┌────┐  ┌────────┐ │
│ │App │  │ Envoy  │ │
│ └────┘  └────────┘ │
└────────────────────┘
  • Memory: +50MB per pod
  • Startup: +2-3 seconds

Ambient Mesh:
┌────────────────────┐
│ Pod                │
│ ┌────────────────┐ │
│ │ App (only)     │ │
│ └────────────────┘ │
└────────────────────┘
         │
┌────────▼────────────┐
│ Node-level ztunnel  │
│ (Shared proxy)      │
└─────────────────────┘
  • No per-pod overhead
  • Zero app changes
  • Optional L7 for specific services

Traffic Flow:
App → ztunnel (node) → mTLS → ztunnel (remote) → App
```

### 19.2 SCION Internet Architecture

```
SCION Path Selection:
┌────────────────────────────────┐
│ Source chooses path:           │
│                                │
│ Path 1: ISP-A → IX1 → ISP-C    │
│   Latency: 50ms, Cost: low     │
│                                │
│ Path 2: ISP-A → ISP-B → ISP-C  │
│   Latency: 30ms, Cost: high    │
│                                │
│ Path 3: ISP-A → Backup → ISP-C │
│   Latency: 100ms, Reliable     │
└────────────────────────────────┘

Application decides based on:
  • Latency requirements
  • Trust boundaries
  • Cost constraints
  • Security properties
```

---

## 20. Production Rollout Strategy

### 20.1 Progressive Deployment

```
Phase 1: Observability (Week 1-2)
┌────────────────────────────────┐
│ Deploy monitoring only         │
│ • Install Prometheus           │
│ • Deploy flow collectors       │
│ • Establish baselines          │
└────────────────────────────────┘

Phase 2: Network Policies (Week 3-4)
┌────────────────────────────────┐
│ Deploy in audit mode           │
│ • Log violations, don't block  │
│ • Identify needed connections  │
│ • Refine policies              │
└────────────────────────────────┘

Phase 3: mTLS (Week 5-6)
┌────────────────────────────────┐
│ Enable in permissive mode      │
│ • Accept plaintext & mTLS      │
│ • Verify cert distribution     │
│ • Monitor for errors           │
└────────────────────────────────┘

Phase 4: Enforcement (Week 7-8)
┌────────────────────────────────┐
│ Enable strict mode             │
│ • Block policy violations      │
│ • Require mTLS                 │
│ • Full zero-trust enforcement  │
└────────────────────────────────┘
```

### 20.2 Rollback Plan

```
Rollback Decision Tree:
┌────────────────────────────────┐
│ Error Rate > 1% ?              │
└──────────┬─────────────────────┘
           │ YES
┌──────────▼─────────────────────┐
│ IMMEDIATE ROLLBACK             │
│ • Disable strict mode          │
│ • Revert to permissive         │
│ • Investigate offline          │
└────────────────────────────────┘
           │ NO
┌──────────▼─────────────────────┐
│ P99 Latency > 2x baseline ?    │
└──────────┬─────────────────────┘
           │ YES
┌──────────▼─────────────────────┐
│ GRADUAL ROLLBACK               │
│ • Reduce enforcement scope     │
│ • Exempt high-traffic services │
│ • Profile performance          │
└────────────────────────────────┘
```

---

## Threat Model Summary

**High-Risk Vectors:**
1. **Lateral Movement:** Attacker compromises pod, moves east-west
   - Mitigation: Default deny NetworkPolicy + mTLS + AuthZ
2. **Man-in-the-Middle:** Traffic interception between services
   - Mitigation: mTLS everywhere, no plaintext allowed
3. **Control Plane Compromise:** API server or etcd breach
   - Mitigation: RBAC, network isolation, audit logging
4. **Supply Chain:** Malicious images or dependencies
   - Mitigation: Image signing, admission control, runtime detection
5. **Data Exfiltration:** Attacker exfils data via egress
   - Mitigation: Egress filtering, DLP, anomaly detection

**Failure Modes:**
1. **Network partition:** Split-brain, quorum loss
2. **DNS failure:** Cascading service discovery failures
3. **Certificate expiry:** mTLS breakdown, traffic blocked
4. **Control plane overload:** API server saturation
5. **CNI plugin failure:** New pods cannot network

---

## Next 3 Steps

**Step 1: Audit Current State (Week 1)**
- Map all service-to-service communication flows using eBPF tools or mesh observability
- Document encryption status (plaintext vs mTLS coverage)
- Identify overly permissive network policies or lack thereof
- Baseline performance metrics (latency P50/P99, throughput, error rates)

**Step 2: Implement Foundation (Week 2-4)**
- Deploy service mesh in permissive mode or CNI with NetworkPolicy support
- Enable comprehensive observability (metrics, traces, flow logs)
- Create default-deny NetworkPolicy templates for each namespace
- Establish certificate rotation automation (SPIRE/cert-manager)

**Step 3: Progressive Hardening (Week 5-8)**
- Convert mesh to strict mTLS mode namespace-by-namespace
- Enforce NetworkPolicies with explicit allow-lists
- Implement AuthZ policies for sensitive services
- Set up continuous compliance monitoring and alerting

**References:**
- CNCF Network SIG: https://github.com/cncf/sig-network
- Kubernetes Network Model: https://kubernetes.io/docs/concepts/cluster-administration/networking/
- CNI Specification: https://github.com/containernetworking/cni
- Service Mesh Interface: https://smi-spec.io/
- eBPF Documentation: https://ebpf.io/
- SPIFFE/SPIRE: https://spiffe.io/
- Cilium Architecture: https://docs.cilium.io/en/stable/concepts/
- Istio Security: https://istio.io/latest/docs/concepts/security/