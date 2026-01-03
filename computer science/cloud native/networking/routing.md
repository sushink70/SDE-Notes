# Cloud-Native Routing & Security: Comprehensive Guide

**TL;DR:** Cloud-native routing operates across multiple layers (L3/L4/L7) with CNI plugins handling pod networking, kube-proxy managing service routing, and ingress/service mesh controlling external/internal traffic—security requires zero-trust policies, mTLS, network segmentation, and defense-in-depth at every layer.

---

## 1. Routing Architecture Layers

Cloud-native routing is stratified across network and application layers:

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL CLIENTS                              │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │   DNS / CDN     │  (Route 53, CloudFlare)
                    └────────┬────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │              EDGE LAYER               │
         │  ┌─────────────────────────────────┐  │
         │  │  Load Balancer (L4/L7)          │  │ Layer 4: TCP/UDP
         │  │  - Cloud LB (ALB/NLB/GCP LB)    │  │ Layer 7: HTTP/gRPC
         │  │  - MetalLB (bare-metal)         │  │
         │  └──────────────┬──────────────────┘  │
         └─────────────────┼─────────────────────┘
                           │
         ┌─────────────────▼─────────────────────┐
         │       INGRESS LAYER (L7)              │
         │  ┌────────────────────────────────┐   │
         │  │ Ingress Controller             │   │ - Path-based routing
         │  │ - Nginx/HAProxy/Traefik        │   │ - Host-based routing
         │  │ - Envoy (Gateway API)          │   │ - TLS termination
         │  │ - Istio/Linkerd Gateway        │   │ - Rate limiting
         │  └────────────┬───────────────────┘   │
         └───────────────┼───────────────────────┘
                         │
         ┌───────────────▼───────────────────────┐
         │    SERVICE MESH DATA PLANE (L7)       │
         │  ┌────────────────────────────────┐   │
         │  │ Sidecar Proxies (Envoy)        │   │ - Service-to-service
         │  │ - mTLS enforcement             │   │ - Retries/timeouts
         │  │ - Circuit breaking             │   │ - Telemetry
         │  │ - Traffic splitting            │   │ - Policy enforcement
         │  └────────────┬───────────────────┘   │
         └───────────────┼───────────────────────┘
                         │
         ┌───────────────▼───────────────────────┐
         │   KUBERNETES SERVICE LAYER (L4)       │
         │  ┌────────────────────────────────┐   │
         │  │ kube-proxy / eBPF              │   │ - ClusterIP routing
         │  │ - iptables/ipvs/eBPF modes     │   │ - NodePort exposure
         │  │ - Service load balancing       │   │ - ExternalIPs
         │  └────────────┬───────────────────┘   │
         └───────────────┼───────────────────────┘
                         │
         ┌───────────────▼───────────────────────┐
         │      POD NETWORK LAYER (L3)           │
         │  ┌────────────────────────────────┐   │
         │  │ CNI Plugin                     │   │ - Pod IP allocation
         │  │ - Calico/Cilium/Flannel        │   │ - Overlay/underlay
         │  │ - AWS VPC CNI / GKE CNI        │   │ - Cross-node routing
         │  │ - Network policies             │   │ - IPAM
         │  └────────────┬───────────────────┘   │
         └───────────────┼───────────────────────┘
                         │
         ┌───────────────▼───────────────────────┐
         │    INFRASTRUCTURE LAYER (L2/L3)       │
         │  - VPC routing tables                 │
         │  - BGP peering                        │
         │  - VXLANs / IP-in-IP tunnels          │
         │  - Physical network fabric            │
         └───────────────────────────────────────┘
```

---

## 2. Pod Networking & CNI (Container Network Interface)

### 2.1 CNI Fundamentals

**Purpose:** Assigns IP addresses to pods, establishes connectivity between pods across nodes.

**Key Concepts:**
- **IPAM (IP Address Management):** Allocates unique IPs from pod CIDR ranges
- **Network namespace isolation:** Each pod gets its own network stack
- **Routing modes:**
  - **Overlay:** Encapsulates pod traffic (VXLAN, IP-in-IP) — simpler but overhead
  - **Underlay:** Routes pod IPs directly via BGP — better performance, requires infrastructure control

**CNI Plugin Responsibilities:**
1. Create veth pair: one end in pod netns, one in host/bridge
2. Assign IP from IPAM pool
3. Configure routes in pod namespace (default gateway)
4. Program host routing (iptables/routes/eBPF)
5. Setup cross-node connectivity (tunnels or BGP)

**Popular CNI Plugins:**
- **Calico:** BGP-based, strong network policy, eBPF dataplane option
- **Cilium:** eBPF-native, L7 visibility, identity-based security
- **Flannel:** Simple overlay (VXLAN), minimal features
- **AWS VPC CNI:** Uses ENI IPs, native AWS routing
- **Antrea:** OVS-based, Windows support

### 2.2 CNI Security Model

**Threat:** Lateral movement between compromised pods.

**Mitigations:**
- **Network Policies:** Kubernetes API objects enforcing L3/L4 ingress/egress rules
  - Default-deny policies (whitelist approach)
  - Namespace isolation
  - Label-based selectors (pod identity)
  
- **eBPF enforcement:** Kernel-level packet filtering (Cilium, Calico eBPF)
  - Lower overhead than iptables
  - L7 protocol awareness (HTTP method filtering)
  
- **Encrypted overlays:** IPsec/WireGuard tunnels between nodes
  - Protects against node compromise or network sniffing
  - Performance impact: 5-15% depending on implementation

**Failure Mode:** Misconfigured CNI can create split-brain networks or route black holes. Always validate connectivity post-install with diagnostic pods.

---

## 3. Service Routing (kube-proxy & Alternatives)

### 3.1 Service Abstraction

Kubernetes Services provide stable virtual IPs (ClusterIP) for ephemeral pod backends.

```
Service Discovery Flow:
┌──────────┐          ┌──────────────┐
│  Client  │─────────▶│ DNS (CoreDNS)│
│   Pod    │          └──────┬───────┘
└──────────┘                 │
      │                      │ Returns ClusterIP
      │                      ▼
      │              myservice.namespace.svc.cluster.local
      │                   = 10.96.0.100
      │
      └───────▶ Request to 10.96.0.100:80
                      │
           ┌──────────▼─────────┐
           │   kube-proxy       │  (Runs on every node)
           │   iptables/IPVS    │
           └──────────┬─────────┘
                      │
          ┌───────────┴───────────┐
          │ NAT/Load Balance      │
          │ to backend pod IPs    │
          └───────────┬───────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Pod 10.244.1.5  Pod 10.244.2.8  Pod 10.244.3.2
```

### 3.2 kube-proxy Modes

**iptables mode (default):**
- Creates DNAT rules per service endpoint
- Random load balancing
- Scale limit: ~5K services (iptables rule bloat)
- Connection tracking overhead

**IPVS mode:**
- Kernel load balancer, better performance
- Multiple algorithms (rr, lc, wrr)
- Scales to 10K+ services
- Requires IPVS kernel modules

**eBPF mode (Cilium kube-proxy replacement):**
- Skips iptables entirely, uses eBPF maps
- 10x lower latency, 50%+ throughput gain
- Direct routing without conntrack overhead
- Requires kernel 4.19+

### 3.3 Service Security

**Threat:** Unauthorized access to backend pods via service IP.

**Mitigations:**
- **Network Policies:** Block traffic to service ClusterIPs unless explicitly allowed
- **Service Type restrictions:**
  - `ClusterIP`: Internal only (default)
  - `NodePort`: Exposes on node IP — avoid in production (use ingress)
  - `LoadBalancer`: Cloud LB — expensive, per-service IPs
  - `ExternalName`: DNS alias — can leak internal names
  
- **Internal traffic policies:** `internalTrafficPolicy: Local` keeps traffic on-node (reduces latency, preserves source IP)

**Failure Mode:** ExternalIPs can be abused — attacker sets arbitrary external IP to hijack traffic. Disable via admission controller or use `externalTrafficPolicy: Local` cautiously (breaks load balancing if uneven pod distribution).

---

## 4. Ingress Routing (L7 North-South Traffic)

### 4.1 Ingress Controller Pattern

Handles external HTTP/HTTPS traffic routing to internal services.

```
┌─────────────────────────────────────────────────────┐
│              Ingress Controller Pod                 │
│                                                     │
│  ┌─────────────────────────────────────────────┐   │
│  │  HTTP Router (Nginx/Envoy/HAProxy)          │   │
│  │                                              │   │
│  │  Routing Table (from Ingress resources):    │   │
│  │  ┌──────────────────────────────────────┐   │   │
│  │  │ Host: api.example.com                │   │   │
│  │  │   /users  → svc/user-svc:80          │   │   │
│  │  │   /orders → svc/order-svc:80         │   │   │
│  │  ├──────────────────────────────────────┤   │   │
│  │  │ Host: admin.example.com              │   │   │
│  │  │   /*      → svc/admin-svc:443        │   │   │
│  │  └──────────────────────────────────────┘   │   │
│  │                                              │   │
│  │  TLS Certificates (from Secrets)             │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
└─────────────────────────────────────────────────────┘
         │                    │
         ▼                    ▼
   [user-svc pods]      [order-svc pods]
```

**Key Features:**
- **Path-based routing:** `/api/*` → API service, `/static/*` → CDN
- **Host-based routing:** `api.example.com` vs `admin.example.com`
- **TLS termination:** Decrypt at ingress, plaintext to backend (or re-encrypt)
- **Rewrite rules:** Strip path prefixes, add headers
- **Rate limiting / WAF:** Protection at entry point

### 4.2 Gateway API (Next-Gen Ingress)

Kubernetes Gateway API is a modern, role-oriented replacement for Ingress:

```
GatewayClass (infra admin) ────┐
                               │
Gateway (cluster operator) ────┤── Defines listeners & TLS
                               │
HTTPRoute (app developer) ─────┘── Route rules & backends
```

**Advantages over Ingress:**
- **Role-based:** Separates infrastructure from routing concerns
- **Extensible:** First-class support for filters, policies
- **Protocol support:** HTTP, HTTPS, TCP, TLS, gRPC, UDP
- **Multi-backend:** Weighted traffic splits for canary/blue-green

**Implementations:** Istio, Envoy Gateway, Cilium, NGINX Gateway, Kong

### 4.3 Ingress Security

**Threats:**
1. **Exposure of internal services:** Misconfigured ingress rules expose admin endpoints
2. **TLS misconfiguration:** Weak ciphers, expired certs, no HSTS
3. **Header injection:** X-Forwarded-For spoofing, host header attacks
4. **DoS:** Ingress is single point of failure

**Mitigations:**
- **Authentication at ingress:**
  - OAuth2 Proxy / external auth (Envoy ext_authz)
  - mTLS for client certificates
  - Rate limiting per IP/user
  
- **TLS best practices:**
  - cert-manager for automated certificate rotation
  - TLS 1.3 only, strong cipher suites
  - HSTS headers (Strict-Transport-Security)
  - OCSP stapling
  
- **DDoS protection:**
  - Cloud WAF (AWS WAF, Cloudflare)
  - Ingress-level rate limiting
  - Connection limits
  
- **Header sanitization:**
  - Strip dangerous headers (`X-Original-URL`, `X-Rewrite-URL`)
  - Validate `Host` header
  - Set `X-Forwarded-*` only at trusted boundary

**Failure Mode:** Ingress controllers can become bottlenecks. Use horizontal pod autoscaling (HPA) with CPU/memory limits, and consider multiple ingress classes for critical vs non-critical traffic.

---

## 5. Service Mesh Routing (East-West L7)

### 5.1 Service Mesh Architecture

Service mesh adds sidecar proxies (Envoy) to every pod for L7 traffic management.

```
┌────────────────────────────────────────────────┐
│                 Control Plane                  │
│  (istiod / linkerd-controller / consul)        │
│                                                │
│  - Configuration distribution (xDS protocol)   │
│  - Certificate authority (mTLS)                │
│  - Policy enforcement                          │
│  - Telemetry aggregation                       │
└─────────────────┬──────────────────────────────┘
                  │ Push config
                  │
     ┌────────────┼────────────┐
     │            │            │
     ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│  Pod A  │  │  Pod B  │  │  Pod C  │
│┌───────┐│  │┌───────┐│  │┌───────┐│
││ App   ││  ││ App   ││  ││ App   ││
││       ││  ││       ││  ││       ││
│└───┬───┘│  │└───┬───┘│  │└───┬───┘│
│    │    │  │    │    │  │    │    │
│┌───▼───┐│  │┌───▼───┐│  │┌───▼───┐│
││Envoy  ││──┼▶│Envoy  ││──┼▶│Envoy  ││ mTLS, L7 routing
││Sidecar││  ││Sidecar││  ││Sidecar││ retries, circuit breaking
│└───────┘│  │└───────┘│  │└───────┘│
└─────────┘  └─────────┘  └─────────┘
```

### 5.2 Service Mesh Routing Capabilities

**Traffic Management:**
- **Weighted routing:** 90% v1, 10% v2 (canary)
- **Header-based routing:** `X-User: beta` → v2
- **Fault injection:** Delay/abort for chaos testing
- **Retries & timeouts:** Automatic retry on transient failures
- **Circuit breaking:** Stop sending traffic to failing backends

**Example Flow (Istio VirtualService concept):**
```
User → Envoy A (svc-a pod)
         │
         └─▶ Routing decision:
             - If header[version]=v2 → route to svc-b-v2
             - Else 80% to svc-b-v1, 20% to svc-b-v2
         │
         └─▶ Envoy B (selected pod)
             - mTLS handshake (verify svc-a identity)
             - Apply timeout (3s), retry (3x)
             - Forward to app container
```

### 5.3 Service Mesh Security

**Threat Model:**
1. **Service impersonation:** Malicious pod pretends to be trusted service
2. **MITM attacks:** Network-level eavesdropping between services
3. **Unauthorized access:** Service A shouldn't call service B
4. **Data exfiltration:** Compromised service leaks data to external endpoints

**Mitigations:**

**mTLS (Mutual TLS):**
- Every pod gets a unique certificate (identity)
- Envoy sidecars automatically negotiate TLS
- Rotating certificates (typically hourly)
- Certificate authority (CA) in control plane
- **Strict mode:** Reject plaintext connections

**Authorization Policies:**
- RBAC at service level: "svc-a can call svc-b:8080/users"
- Deny-by-default: Only explicitly allowed paths work
- Identity-based (SPIFFE IDs): `cluster.local/ns/namespace/sa/serviceaccount`
- Attribute-based: JWT claims, HTTP headers, source IP

**Egress Control:**
- Block all external traffic by default
- Explicit ServiceEntry for allowed external hosts
- TLS origination for external HTTPS services
- Certificate verification for external APIs

**Example Security Posture (Zero Trust):**
```
Default: DENY all inter-service communication
└─▶ AuthorizationPolicy: Allow frontend → backend:8080 GET /api/users
└─▶ PeerAuthentication: Require mTLS STRICT
└─▶ Egress: Allow backend → postgres.external.com:5432 (ServiceEntry)
```

### 5.4 Service Mesh Failure Modes

**Sidecar Injection Failures:**
- Forgotten namespace labels → no sidecar injected → plaintext traffic fails with STRICT mTLS
- Init container (CNI) failures block pod startup

**Control Plane Outage:**
- Data plane continues with last-known config (stale)
- New pods can't get certificates → fail to start
- **Mitigation:** Multi-region control plane, local cert caching

**Performance Overhead:**
- ~1-3ms latency per hop (Envoy processing)
- 10-20% CPU overhead per pod
- Memory: ~50MB per sidecar
- **Mitigation:** Ambient mesh (sidecar-less, node-level proxy)

**Certificate Rotation Issues:**
- Clock skew causes cert validation failures
- CA outage prevents new cert issuance
- **Mitigation:** Monitor cert expiry, use NTP

---

## 6. Network Policy Enforcement

### 6.1 Kubernetes Network Policy

L3/L4 firewall rules for pod-to-pod traffic.

```
Network Policy Enforcement:

┌─────────────────────────────────────────────────┐
│              Namespace: production              │
│                                                 │
│  ┌───────────────┐         ┌────────────────┐  │
│  │  frontend     │────X────│  database      │  │
│  │  (label: web) │         │  (label: db)   │  │
│  └───────────────┘         └────────────────┘  │
│         │                          ▲            │
│         │ ALLOW                    │ ALLOW      │
│         │ (egress to api)          │ (ingress)  │
│         │                          │            │
│         ▼                          │            │
│  ┌───────────────┐                 │            │
│  │  api          │─────────────────┘            │
│  │  (label: api) │                              │
│  └───────────────┘                              │
│                                                 │
└─────────────────────────────────────────────────┘

NetworkPolicy:
  - podSelector: {app: database}
    ingress:
      - from: [{podSelector: {app: api}}]
        ports: [{protocol: TCP, port: 5432}]
```

**Key Concepts:**
- **Selectors:** Label-based (podSelector, namespaceSelector)
- **Ingress rules:** Who can connect TO this pod
- **Egress rules:** Where this pod can connect TO
- **Default deny:** Empty policy blocks all traffic

**Enforcement Points:**
- CNI plugin (Calico, Cilium, Antrea)
- iptables, ipset, or eBPF programs
- Applied at pod creation/update

### 6.2 Advanced Policy Patterns

**Namespace Isolation:**
```
Block all cross-namespace traffic except:
- Namespace "frontend" → "backend"
- Namespace "backend" → "database"
- All pods → kube-dns (UDP 53)
```

**Egress Lockdown:**
```
Default deny egress, allow only:
- DNS (kube-dns)
- Specific external API (by CIDR or FQDN with Cilium)
- Internal services (by labels)
```

**Multi-tenancy:**
```
Tenant A namespace: Deny traffic to Tenant B namespace
Shared services namespace: Allow from any tenant
```

### 6.3 Policy Security

**Threat:** Policy bypass via label manipulation or unintended traffic paths.

**Mitigations:**
- **Admission control:** Prevent label changes (Gatekeeper/OPA)
- **RBAC:** Limit who can create/modify NetworkPolicies
- **Audit:** Log policy violations (Falco, Cilium Hubble)
- **Testing:** Use policy linting (kubectl-neat, Polaris)

**Failure Mode:** CNI failure disables policy enforcement entirely. Monitor CNI health and test with policy violation attempts.

---

## 7. Multi-Cluster Routing

### 7.1 Multi-Cluster Patterns

```
┌──────────────┐           ┌──────────────┐
│  Cluster A   │           │  Cluster B   │
│  (us-west)   │           │  (us-east)   │
│              │           │              │
│  ┌────────┐  │           │  ┌────────┐  │
│  │ svc-a  │  │◀─────────▶│  │ svc-a  │  │
│  │ (pods) │  │  Service  │  │ (pods) │  │
│  └────────┘  │   Mesh    │  └────────┘  │
│              │           │              │
└──────────────┘           └──────────────┘
       │                          │
       └──────────┬───────────────┘
                  │
          Multi-Cluster Gateway
          (Istio, Submariner, Cilium)
```

**Approaches:**

**1. Flat Network (Pod IP Routable):**
- VPN/VPC peering between clusters
- BGP propagation of pod CIDRs
- Direct pod-to-pod across clusters
- **Use case:** Low-latency, same region
- **Risk:** IP conflicts, complex routing

**2. Service-Level Federation:**
- Services discoverable across clusters
- Gateway proxies traffic between clusters
- East-West gateway pods
- **Use case:** Multi-region HA
- **Tools:** Istio multi-primary, Linkerd multi-cluster

**3. API Gateway:**
- Centralized ingress routes to multiple clusters
- Application-level load balancing
- **Use case:** Global traffic management
- **Tools:** Gloo, Kong, Ambassador

### 7.2 Multi-Cluster Security

**Threat:** Cross-cluster compromise lateral movement.

**Mitigations:**
- **mTLS across clusters:** Shared root CA or federated trust
- **Network segmentation:** Limit inter-cluster traffic to gateways only
- **Policy enforcement:** Deny by default, explicit allow per service
- **Audit:** Centralized logging for cross-cluster calls

**Failure Mode:** Gateway SPOF. Use redundant gateways per cluster with health checks.

---

## 8. DNS & Service Discovery

### 8.1 CoreDNS

Kubernetes DNS resolution for service discovery.

```
Pod DNS Resolution Flow:

Pod container:
  /etc/resolv.conf
    nameserver 10.96.0.10  ← ClusterIP of kube-dns service
    search default.svc.cluster.local svc.cluster.local cluster.local
    options ndots:5

Query: curl myservice
  ↓
Resolved to: myservice.default.svc.cluster.local
  ↓
CoreDNS looks up in Kubernetes service records
  ↓
Returns: ClusterIP (10.96.5.25)
  ↓
kube-proxy routes to backend pods
```

**CoreDNS Plugins:**
- `kubernetes`: Main plugin for svc.cluster.local records
- `forward`: Upstream DNS for external queries
- `cache`: Response caching
- `errors`: Logging
- `ready`: Health check endpoint

### 8.2 Service Discovery Security

**Threat:** DNS spoofing, cache poisoning, enumeration.

**Mitigations:**
- **DNSSEC:** Validate upstream responses (rarely used in clusters)
- **Network policies:** Only allow pods to query CoreDNS (UDP 53)
- **Rate limiting:** Prevent DNS DoS
- **Audit:** Log unusual query patterns (Falco)

**Failure Mode:** CoreDNS outage breaks service discovery. Run multiple replicas (3+) with pod anti-affinity. Consider NodeLocal DNSCache for resilience.

---

## 9. BGP in Cloud-Native

### 9.1 BGP Use Cases

**Purpose:** Propagate pod/service IPs to physical network infrastructure.

```
┌──────────────────────────────────────────────────┐
│           Kubernetes Cluster                     │
│                                                  │
│  Node 1             Node 2             Node 3    │
│  Pod CIDR:          Pod CIDR:          Pod CIDR: │
│  10.244.1.0/24      10.244.2.0/24      10.244.3.0/24
│                                                  │
│  BGP Speaker        BGP Speaker        BGP Speaker
│  (Calico/MetalLB)   (Calico/MetalLB)   (Calico/MetalLB)
└────┬────────────────────┬────────────────────┬───┘
     │ BGP Peering        │                    │
     ▼                    ▼                    ▼
┌────────────────────────────────────────────────┐
│          Top-of-Rack (ToR) Switches            │
│  - Learn pod CIDR routes via BGP               │
│  - Equal-cost multi-path (ECMP)                │
│  - Fast failover on node failure               │
└────────────────────────────────────────────────┘
```

**Scenarios:**
1. **Bare-metal LoadBalancer:** MetalLB advertises service ExternalIPs via BGP
2. **No overlay networking:** Calico BGP mode routes pod IPs without tunnels
3. **Multi-cluster:** Propagate service CIDRs between clusters

### 9.2 BGP Security

**Threat:** BGP hijacking, route poisoning.

**Mitigations:**
- **MD5 authentication:** BGP neighbor passwords
- **Route filtering:** Accept only expected CIDR ranges
- **TTL security:** GTSM (Generalized TTL Security Mechanism)
- **Prefix limits:** Prevent route table exhaustion
- **Monitoring:** Alert on unexpected route changes

**Failure Mode:** BGP flapping causes routing instability. Use route dampening and stable BGP timers.

---

## 10. eBPF-Based Routing

### 10.1 eBPF Data Plane

**Advantages:**
- Skip iptables/netfilter (10x faster)
- Programmable packet processing in kernel
- L7 protocol parsing (HTTP, gRPC, Kafka)
- Dynamic policy updates without container restarts

**Cilium eBPF Architecture:**
```
┌──────────────────────────────────────────────┐
│            Kernel Space (Linux)              │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │         eBPF Programs                  │  │
│  │  - XDP (eXpress Data Path)             │  │ ← Earliest packet processing
│  │  - TC (Traffic Control)                │  │ ← Pre-routing
│  │  - Socket filters                      │  │ ← Socket level
│  │  - kprobes/tracepoints                 │  │ ← Observability
│  └────────────────────────────────────────┘  │
│                                              │
│  ┌────────────────────────────────────────┐  │
│  │         eBPF Maps                      │  │
│  │  - Service endpoints                   │  │
│  │  - Network policies                    │  │
│  │  - Connection tracking                 │  │
│  │  - Identity maps                       │  │
│  └────────────────────────────────────────┘  │
└──────────────────────────────────────────────┘
         ▲                    ▲
         │ Update             │ Update
         │                    │
┌────────┴────────┐   ┌───────┴──────┐
│  Cilium Agent   │   │  CNI Plugin  │
│  (per node)     │   │              │
└─────────────────┘   └──────────────┘
```

**Capabilities:**
- **Identity-based policy:** SPIFFE-like IDs without mTLS overhead
- **Connection tracking:** Stateful firewalling
- **L7 visibility:** HTTP method, path, headers in policy
- **Transparent encryption:** WireGuard IPsec between nodes

### 10.2 eBPF Security Benefits

**Traditional iptables weaknesses:**
- Sequential rule processing (slow with 10K+ rules)
- No namespace isolation (global rule set)
- Limited observability

**eBPF improvements:**
- **Hash-based lookups:** O(1) policy decisions
- **Per-pod programs:** Isolation and blast radius reduction
- **Audit logging:** Every packet can be traced
- **Tamper resistance:** Verified at load time, can't be modified

**Failure Mode:** Requires kernel 4.19+, missing eBPF features on older kernels fall back to iptables. Test on target kernel versions.

---

## 11. Observability for Routing

### 11.1 Key Metrics

**Network Layer (L3/L4):**
- Packet loss rate
- RTT (round-trip time)
- Connection failures
- MTU issues (fragmentation)

**Service Layer:**
- Request rate (RPS)
- Error rate (HTTP 5xx, gRPC failures)
- Latency percentiles (p50, p99, p99.9)
- Retries and circuit breaker triggers

**Tools:**
- **Prometheus:** Metric scraping from Envoy, kube-proxy, CNI
- **Hubble (Cilium):** Network flow logs with L7 visibility
- **Kiali (Istio):** Service graph, traffic flow visualization
- **Grafana:** Dashboards for golden signals

### 11.2 Distributed Tracing

Correlate requests across service hops.

```
User Request → Ingress → Service A → Service B → Database
   trace_id: abc123
     │           │           │           │
     └─span_1────┴─span_2────┴─span_3────┴─span_4

Jaeger/Tempo reconstructs full path:
  Total latency: 450ms
    - Ingress: 10ms
    - Service A: 50ms
    - Service B: 370ms ← Bottleneck
    - Database: 20ms
```

**Implementation:**
- **Context propagation:** Inject trace headers (W3C Trace Context)
- **Span creation:** Each service creates child span
- **Sampling:** 1-10% of traces to reduce overhead

### 11.3 Security Observability

**Detection:**
- **Anomaly detection:** Unusual traffic patterns (ML-based)
- **Policy violations:** Blocked connections by NetworkPolicy
- **Certificate errors:** mTLS handshake failures
- **Unauthorized access:** 403 Forbidden spikes

**Tools:**
- **Falco:** Runtime security (syscall monitoring)
- **Cilium Hubble:** L7 network policies and flows
- **Istio Telemetry:** mTLS authentication logs

---

## 12. Threat Model & Attack Vectors

### 12.1 Comprehensive Threat Matrix

| **Attack Vector**              | **Threat**                                  | **Mitigation**                          |
|--------------------------------|---------------------------------------------|----------------------------------------|
| Pod escape                     | Compromise host network namespace           | seccomp, AppArmor, SELinux             |
| Service impersonation          | Fake service steals traffic                 | mTLS with identity validation          |
| DNS poisoning                  | Redirect traffic to malicious endpoints     | DNSSEC, CoreDNS policy                 |
| MITM (man-in-the-middle)       | Intercept pod-to-pod traffic                | mTLS, encrypted overlays (WireGuard)   |
| NetworkPolicy bypass           | Exploit policy gaps or label manipulation   | Admission control, audit                |
| BGP hijacking                  | Reroute traffic to attacker-controlled node | BGP auth, prefix filtering             |
| Ingress misconfiguration       | Expose internal services publicly           | Policy-as-code, GitOps review          |
| Service mesh control plane     | Compromise CA, issue malicious certs        | Multi-factor auth, RBAC, audit         |
| Egress data exfiltration       | Compromised pod leaks data externally       | Egress policies, DLP, network forensics|
| DDoS on ingress                | Overwhelm ingress with traffic              | Rate limiting, WAF, cloud DDoS shield  |
| Sidecar injection skip         | Pod bypasses mTLS enforcement               | MutatingWebhook validation, alerts     |
| Certificate expiry             | Service outage due to cert rotation failure | Monitoring, automated rotation         |
| kube-proxy compromise          | Manipulate iptables/IPVS rules              | Node hardening, immutable infra        |

### 12.2 Defense-in-Depth Strategy

**Layer 1 - Infrastructure:**
- VPC segmentation
- Host firewall (iptables on nodes)
- Encrypted storage/transit

**Layer 2 - CNI/Network:**
- NetworkPolicies (default-deny)
- Encrypted overlay (WireGuard/IPsec)
- IPAM restrictions

**Layer 3 - Service:**
- kube-proxy security (IPVS over iptables)
- Service type restrictions (no NodePort in prod)

**Layer 4 - Ingress:**
- TLS termination with strong ciphers
- WAF/DDoS protection
- Rate limiting

**Layer 5 - Service Mesh:**
- mTLS STRICT mode
- Authorization policies (RBAC)
- Egress lockdown

**Layer 6 - Application:**
- Input validation
- Authentication/authorization
- Secrets management (Vault, Sealed Secrets)

---

## 13. Production Rollout Considerations

### 13.1 Rollout Strategy

**Phase 1: Foundation (Weeks 1-2)**
- Deploy CNI with encrypted overlay enabled
- Configure NetworkPolicies (audit mode first)
- Validate pod connectivity across nodes

**Phase 2: Service Layer (Weeks 3-4)**
- Migrate kube-proxy to IPVS or eBPF
- Implement ingress controller with TLS
- Set up external DNS integration

**Phase 3: Service Mesh (Weeks 5-8)**
- Inject sidecars in non-prod namespaces
- Enable mTLS permissive mode
- Gradually enforce STRICT mTLS
- Deploy authorization policies

**Phase 4: Observability (Weeks 9-10)**
- Deploy Prometheus, Jaeger, Hubble
- Create dashboards and alerts
- Tune policy violations

**Phase 5: Hardening (Ongoing)**
- Security audits and penetration testing
- Chaos engineering (Chaos Mesh)
- Incident response drills

### 13.2 Rollback Plan

**Failure Scenarios:**
1. **CNI failure:** Revert to previous CNI plugin (node restart required)
2. **NetworkPolicy blocks critical traffic:** Remove policy, investigate, redeploy
3. **Service mesh breaks service:** Disable sidecar injection, restart pods
4. **Ingress certificate issue:** Use fallback cert, emergency renewal
5. **BGP route flapping:** Disable BGP, revert to overlay mode

**Rollback Commands Readiness:**
- Document exact commands for each component
- Test rollback procedures in staging
- Maintain previous config versions in Git

---

## 14. Alternatives & Tradeoffs

| **Component**       | **Option 1**           | **Option 2**          | **Tradeoff**                                  |
|---------------------|------------------------|-----------------------|-----------------------------------------------|
| CNI                 | Calico (BGP)           | Cilium (eBPF)         | BGP = simpler, eBPF = faster, requires kernel|
| kube-proxy          | iptables               | IPVS / eBPF           | iptables = compatible, IPVS/eBPF = scalable  |
| Ingress             | NGINX                  | Envoy Gateway         | NGINX = mature, Envoy = extensible           |
| Service Mesh        | Istio                  | Linkerd               | Istio = feature-rich, Linkerd = lightweight  |
| Multi-cluster       | Istio multi-primary    | Submariner            | Istio = L7, Submariner = L3 flat network     |
| Load Balancer       | Cloud LB               | MetalLB               | Cloud = managed, MetalLB = on-prem control   |
| Network Policy      | Kubernetes native      | Cilium L7 policy      | Native = L3/L4, Cilium = L7 protocol-aware   |
| Observability       | Prometheus + Grafana   | Datadog / Dynatrace   | Open-source = free, Commercial = support     |

---

## 15. Next 3 Steps

1. **Audit current routing setup:**
   - Identify CNI plugin and mode (overlay vs underlay)
   - Check kube-proxy mode (iptables/IPVS/eBPF)
   - List all ingress controllers and service mesh deployments
   - Map traffic flows (north-south, east-west, egress)

2. **Implement baseline security:**
   - Deploy default-deny NetworkPolicies per namespace
   - Enable mTLS in permissive mode (if service mesh exists)
   - Configure ingress TLS with cert-manager
   - Set up egress policies for external API calls

3. **Establish observability:**
   - Deploy Prometheus for metrics scraping
   - Enable Hubble (Cilium) or Kiali (Istio) for traffic visualization
   - Create dashboards for golden signals (latency, errors, saturation)
   - Set up alerts for policy violations and certificate expiry

---

## 16. References

**CNCF Projects:**
- Kubernetes Networking SIG: https://github.com/kubernetes/community/tree/master/sig-network
- CNI Spec: https://github.com/containernetworking/cni
- Gateway API: https://gateway-api.sigs.k8s.io/
- Cilium: https://cilium.io/
- Istio: https://istio.io/
- Linkerd: https://linkerd.io/

**Security Standards:**
- SPIFFE/SPIRE: https://spiffe.io/
- Zero Trust Architecture (NIST 800-207): https://csrc.nist.gov/publications/detail/sp/800-207/final
- Kubernetes Security Best Practices: https://kubernetes.io/docs/concepts/security/

**Performance:**
- eBPF for Networking: https://ebpf.io/
- Cilium Performance Benchmarks: https://cilium.io/blog/2021/05/11/cni-benchmark
- Service Mesh Comparison: https://layer5.io/service-mesh-landscape

**Production Guides:**
- Calico Production Checklist: https://docs.tigera.io/calico/latest/operations/
- Istio Production Deployment: https://istio.io/latest/docs/setup/install/istioctl/
- Network Policy Recipes: https://github.com/ahmetb/kubernetes-network-policy-recipes