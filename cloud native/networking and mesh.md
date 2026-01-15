# Networking & Mesh: Comprehensive Deep-Dive Guide

**Executive Summary (Technical Context)**  
Modern cloud-native networking spans L2–L7, integrating BGP-based routing (data-center fabrics, multi-cluster), overlay networks (VXLAN for L2-over-L3), CNI plugins (Cilium/Calico for policy enforcement), service meshes (mTLS, mutual authentication), and async messaging (NATS for event-driven architectures). Security boundaries shift from perimeter to workload identity, zero-trust overlay encryption, and API gateway policy enforcement. This guide covers BGP for underlay/inter-cluster peering, VXLAN for overlay isolation, CNI abstractions, Cilium's eBPF datapath, Calico's network policy model, NATS for decoupled pub-sub with security, mTLS for service-to-service encryption, gRPC for high-performance RPC, and Gateway API for declarative ingress/egress. Together, these form the **security-first networking stack** for Kubernetes and modern distributed systems.

---

## 1. BGP (Border Gateway Protocol)

### 1.1 Fundamentals & Role in Cloud-Native
- **Definition**: Path-vector protocol for exchanging routing information between autonomous systems (AS). Operates at L3, uses TCP/179.
- **Key Concepts**:
  - **AS (Autonomous System)**: Collection of IP prefixes under single administrative control, identified by ASN (16/32-bit).
  - **eBGP vs iBGP**: External (between ASes, TTL=1 default) vs Internal (within AS, full-mesh or route-reflectors).
  - **Attributes**: AS_PATH (loop prevention), NEXT_HOP, LOCAL_PREF, MED (multi-exit discriminator), COMMUNITY tags.
  - **Route Advertisement**: Prefixes announced with attributes; best path selected via decision process (weight, LOCAL_PREF, AS_PATH length, origin, MED, eBGP over iBGP, IGP metric, BGP ID).

### 1.2 BGP in Data-Center Fabrics (Spine-Leaf)
- **Traditional L2 Spine-Leaf**: Single broadcast domain, STP limitations, MAC table explosion.
- **BGP-EVPN (Ethernet VPN)**: Control-plane for L2/L3 overlays using VXLAN encapsulation. Distributes MAC/IP reachability via BGP, enabling IP fabric underlay.
- **Unnumbered BGP**: Uses link-local IPv6 for peering, simplifies configuration in large fabrics (RFC 5549).
- **ECMP (Equal-Cost Multi-Path)**: BGP advertises same prefix via multiple paths; underlay forwards using flow hash (5-tuple) for load distribution.
- **Security Implications**: BGP hijacking (prefix origin validation via RPKI ROA), route leaks, session authentication (TCP MD5/AO), TTL security (GTSM), max-prefix limits.

### 1.3 BGP in Kubernetes Multi-Cluster
- **MetalLB**: Announces LoadBalancer service IPs via BGP to upstream routers; L2 mode (ARP) or BGP mode (anycast).
- **Calico BGP Mode**: Each node acts as BGP speaker, peers with ToR switches or route-reflectors. Advertises pod CIDRs directly into fabric, bypassing overlay encap (flat L3 routing).
- **Cilium BGP Control Plane**: Uses `cilium-bgp-agent` to peer with upstream; integrates with BIRD/GoBGP. Enables service IP advertisement, pod CIDR leaking for hybrid connectivity.
- **Use Cases**: Bare-metal clusters (no cloud LB), multi-cluster service mesh (Istio multi-primary), hybrid cloud (on-prem ↔ cloud BGP peering over VPN/Direct Connect).

### 1.4 Security & Threat Model
- **Threats**: Prefix hijacking (malicious AS announces victim's prefix), route leaks (accidental propagation), session tampering, DoS via route flapping.
- **Mitigations**:
  - **RPKI (Resource Public Key Infrastructure)**: Cryptographic validation of prefix origin (ROA = Route Origin Authorization).
  - **BGPsec**: Path validation (still experimental, high overhead).
  - **Filtering**: Prefix lists, AS_PATH filters, bogon/martian rejection.
  - **Authentication**: TCP MD5 (legacy, weak) → TCP-AO (RFC 5925, stronger HMAC).
  - **Rate Limiting**: Prevent route flapping, max-prefix thresholds.
  - **Monitoring**: BGP anomaly detection (ARTEMIS, BGPmon), session state alerts.

---

## 2. VXLAN (Virtual Extensible LAN)

### 2.1 Fundamentals
- **Purpose**: L2 overlay over L3 underlay, enabling tenant isolation in multi-tenant data centers, extending L2 segments across IP networks.
- **Encapsulation**: Original Ethernet frame → UDP (port 4789) → outer IP header. 24-bit VNI (VXLAN Network Identifier) = 16M segments vs VLAN's 4K.
- **Components**:
  - **VTEP (VXLAN Tunnel Endpoint)**: Hypervisor/ToR switch performing encap/decap. Has underlay IP (VTEP IP) and belongs to VNI(s).
  - **VNI**: Logical segment identifier; maps to tenant/namespace/application boundary.
  - **Flood-and-Learn**: Multicast-based MAC learning (legacy); modern uses BGP-EVPN for control-plane MAC distribution.

### 2.2 VXLAN in Kubernetes CNI
- **Flannel VXLAN Backend**: Each node = VTEP. Pod traffic encapsulated in VXLAN; kernel `vxlan` device + FDB (forwarding database) entries for remote VTEPs.
- **Calico VXLAN Mode**: Alternative to BGP; uses VXLAN for pod-to-pod across nodes. Calico manages FDB via Felix agent.
- **Cilium VXLAN Mode**: Default overlay; eBPF datapath performs encap/decap in kernel bypass paths. Supports WireGuard encryption over VXLAN for double-encryption.
- **Trade-offs**: Overhead (~50 bytes/packet), MTU reduction (1450 for pods), CPU cost for encap/decap. Beneficial when BGP not feasible (cloud environments without BGP peering).

### 2.3 Security Architecture
- **Threat Model**: VXLAN unencrypted by default; on-path attacker can sniff pod-to-pod traffic, inject packets, or spoof VTEPs.
- **Mitigations**:
  - **Overlay Encryption**: IPsec (Calico) or WireGuard (Cilium) encrypts inner packets before VXLAN encap. Protects against compromised underlay.
  - **VTEP Authentication**: Restrict VTEP participation via ACLs, BGP authentication, firewall rules (UDP/4789 only from known VTEPs).
  - **Segmentation**: VNI per namespace/tenant; compromised VNI doesn't leak to others.
  - **Monitoring**: Flow logs (IPFIX/NetFlow from VTEPs), anomaly detection (unexpected VTEP peering).

### 2.4 Performance & Scale
- **Hardware Offload**: SmartNICs (Mellanox ConnectX, Intel E810) offload VXLAN encap/decap, reducing CPU overhead.
- **Jumbo Frames**: Increase underlay MTU to 9000; pod MTU = 8950 (accounting for VXLAN+IP+Ethernet overhead).
- **ECMP**: Underlay fabric load-balances VXLAN UDP flows using 5-tuple hash (outer IP+port).

---

## 3. CNI (Container Network Interface)

### 3.1 Specification & Plugin Model
- **Purpose**: Standard interface between container runtime (containerd, CRI-O) and network provider. Decouples networking from orchestrator.
- **CNI Spec (CNCF)**: JSON config passed to plugin; plugin responsible for:
  1. `ADD`: Allocate IP, create veth pair, attach to bridge/network, configure routes.
  2. `DEL`: Cleanup networking for terminated container.
  3. `CHECK`: Verify network config still valid.
- **Chaining**: Multiple plugins executed in sequence (e.g., `bridge` → `portmap` → `bandwidth`). CNI 1.0 supports `prevResult` passing.

### 3.2 CNI Plugin Types
- **Overlay Plugins**: Flannel (VXLAN/host-gw), Weave (mesh + encryption), Cilium (VXLAN/Geneve + eBPF).
- **Routed Plugins**: Calico (BGP/VXLAN), Cilium (native routing), AWS VPC CNI (assigns ENI IPs directly to pods).
- **Policy Enforcement**: Calico (iptables/eBPF), Cilium (eBPF), Weave (OVS).
- **Service Mesh Integration**: Cilium (transparent proxy via eBPF), Linkerd (iptables redirect to proxy), Istio (init container + iptables).

### 3.3 Security Design Patterns
- **Network Policy Enforcement**: CNI plugin translates Kubernetes `NetworkPolicy` into datapath rules (iptables chains, eBPF programs, OVS flows).
- **Default Deny**: Start with deny-all ingress/egress; whitelist specific traffic. Implemented via `policyTypes: [Ingress, Egress]` with empty `from`/`to`.
- **Namespace Isolation**: Use `namespaceSelector` in policies; label namespaces (`tier=frontend`) for cross-namespace communication control.
- **Pod Identity**: SPIFFE/SPIRE integration (Cilium supports SPIFFE via CRDs); mTLS at L7 using workload identity from CNI.
- **Encryption in Transit**: Cilium WireGuard (transparent, per-node key), Calico IPsec (IKEv2, per-prefix SA), Weave (NaCl encryption).

### 3.4 Threat Model & Hardening
- **Threats**: Container escape → host network access, lateral movement (pod-to-pod without policy), CNI plugin compromise (malicious IPAM), traffic interception on underlay.
- **Mitigations**:
  - **Network Policies**: Enforce at pod level; deny-by-default.
  - **eBPF Enforcement**: Cilium enforces policy at syscall/socket layer, preventing userspace bypass.
  - **CNI Plugin Integrity**: Run plugins as DaemonSets with read-only root, drop capabilities, AppArmor/SELinux profiles.
  - **IPAM Security**: Use dedicated IPAM (Calico IPAM, Cilium cluster-pool); prevent IP exhaustion attacks, validate CIDR allocations.
  - **Monitoring**: Hubble (Cilium observability), flow logs, detect policy violations in real-time.

---

## 4. Cilium (eBPF-Based Networking & Security)

### 4.1 Architecture & eBPF Datapath
- **eBPF (Extended Berkeley Packet Filter)**: In-kernel virtual machine for safe, performant packet processing. Programs attached to hooks (XDP, TC, socket ops, kprobes).
- **Cilium Components**:
  - **cilium-agent**: Runs on each node; compiles eBPF programs, loads into kernel, manages identity/policy.
  - **cilium-operator**: Cluster-wide controller (IP allocation, DNS policy, CRD management).
  - **Hubble**: Observability layer; eBPF-based flow logs, metrics, service map.
- **Datapath Flow**:
  1. Pod sends packet → veth pair → TC (Traffic Control) hook on host.
  2. Cilium eBPF program inspects packet (L3–L7), checks identity + policy.
  3. Encapsulation (VXLAN/Geneve) or direct routing, encryption (WireGuard), forwarding decision.
  4. Egress: same process in reverse.

### 4.2 Identity-Based Security Model
- **Cilium Identity**: 32-bit label derived from pod labels (e.g., `k8s:app=frontend, k8s:env=prod` → identity 12345). Stored in eBPF map.
- **Policy Enforcement**: NetworkPolicy → Cilium CiliumNetworkPolicy CRD → eBPF policy map. Decisions at L3/L4 (IP/port) + L7 (HTTP path, gRPC method).
- **SPIFFE Integration**: Cilium can map SPIFFE IDs to Cilium identities; enables mTLS at L4/L7 using workload certs.
- **Advantages**: No iptables (scales to 100K+ rules), sub-microsecond latency, per-connection policy.

### 4.3 L7 Policy & API-Aware Filtering
- **HTTP/Kafka/gRPC/DNS**: Cilium parses L7 protocols in eBPF; allows rules like "allow GET /api/v1/users from identity:frontend".
- **Envoy Integration**: Cilium embeds Envoy proxy (via `cilium-envoy` pod) for complex L7 (TLS termination, retries). eBPF redirects traffic to Envoy transparently.
- **Use Cases**: API gateway, service mesh dataplane, egress filtering (block specific DNS queries), rate limiting.

### 4.4 Encryption & Multi-Cluster
- **WireGuard**: Transparent node-to-node encryption. Cilium manages keys (rotated automatically), encrypts all pod-to-pod traffic.
- **IPsec**: Alternative to WireGuard (kernel 4.19+). Uses strongSwan for IKE; per-prefix SAs.
- **Cluster Mesh**: Connects multiple Kubernetes clusters; pod-to-pod across clusters via VXLAN/native routing. Shared identity plane; global services (replicas in multiple clusters).

### 4.5 Threat Model & Hardening
- **Threats**: eBPF program vulnerabilities (kernel compromise), identity spoofing, policy bypass via crafted packets, Hubble data exfiltration.
- **Mitigations**:
  - **eBPF Verifier**: Kernel verifies programs before load (bounds checks, no loops, memory safety).
  - **Cilium Agent Security**: Run as DaemonSet with minimal privileges; use SELinux/AppArmor for agent itself.
  - **mTLS for Hubble**: Encrypt Hubble Relay → UI communication, authenticate clients.
  - **Policy Auditing**: Enable audit mode (log policy violations without enforcement), then switch to enforce.
  - **Least Privilege**: Use `CiliumClusterwideNetworkPolicy` for global deny-all; per-namespace allow rules.

---

## 5. Calico (Policy-Driven Networking)

### 5.1 Architecture & Datapath Modes
- **Components**:
  - **Felix**: Agent on each node; programs iptables/eBPF, manages routes, enforces policy.
  - **BIRD**: BGP daemon (optional); advertises pod CIDRs to ToR switches.
  - **Typha**: API proxy (caching layer for large clusters); reduces etcd load.
  - **Calico CNI**: Configures pod network namespace.
- **Datapath Modes**:
  - **iptables**: Traditional Linux netfilter; Felix creates chains per pod/endpoint. Scalability limit ~10K rules.
  - **eBPF**: Calico eBPF dataplane (since v3.13); bypasses iptables, 10x faster policy processing.
  - **Windows**: Calico supports Windows nodes (HNS-based datapath).

### 5.2 BGP Mode vs Overlay Mode
- **BGP Mode (Native Routing)**:
  - Each node peers with fabric (full-mesh or route-reflectors).
  - Pod CIDRs advertised as /26 or /24 prefixes.
  - No encapsulation → lower latency, higher throughput.
  - **Use Case**: Bare-metal, on-prem data centers with BGP-capable switches.
- **VXLAN/IPIP Overlay**:
  - VXLAN (UDP/4789) or IP-in-IP (protocol 4) encapsulation.
  - Simpler fabric (no BGP support needed).
  - **Use Case**: Cloud environments (AWS, Azure, GCP) where BGP peering unavailable.
- **Cross-Subnet Mode**: IPIP only for traffic crossing L3 boundaries; same-subnet uses native routing.

### 5.3 Network Policy Model
- **Kubernetes NetworkPolicy**: Standard API; Calico implements as iptables/eBPF rules.
- **Calico NetworkPolicy (CRD)**: Extensions:
  - `action: Deny | Allow | Log | Pass` (Pass = skip to next tier).
  - `notSelector`, `notPorts`, `notProtocol` for negative matching.
  - ICMP type/code filtering.
- **GlobalNetworkPolicy**: Cluster-wide rules (e.g., deny-all, allow DNS to CoreDNS, allow monitoring scrapes).
- **Policy Tiers**: Ordered priority (security > platform > application); policies within tier evaluated by order field.

### 5.4 Encryption & Zero-Trust
- **WireGuard Encryption**: Transparent encryption for all pod traffic (same as Cilium). Per-node public/private keys, stored in node resource.
- **IPsec Encryption**: IKEv2 via strongSwan; per-prefix SAs. Higher overhead than WireGuard but wider kernel support.
- **Application Layer Policy (ALP)**: Calico Enterprise feature (requires license); L7 HTTP/DNS/Kafka policy.
- **Zero-Trust Architecture**:
  - Start with `GlobalNetworkPolicy` deny-all ingress/egress.
  - Explicit allow for specific workload identities (labels).
  - TLS inspection (ALP) for encrypted traffic policy.
  - Egress gateway (dedicated nodes) for external traffic with audit logs.

### 5.5 Threat Model & Hardening
- **Threats**: Policy bypass (misconfigured rules), lateral movement, CNI plugin compromise, BGP hijacking (if using BGP mode).
- **Mitigations**:
  - **Policy Preview**: Use `Log` action to test rules before `Allow`/`Deny`.
  - **Felix Security**: Run Felix with drop capabilities, read-only root, SELinux enforcing.
  - **BGP Security**: MD5/TCP-AO authentication, prefix filtering, max-prefix limits, RPKI validation (if available).
  - **Audit Logs**: Enable flow logs (send to Fluentd/Elasticsearch), alert on policy violations.
  - **Immutable Infrastructure**: Deploy Calico via GitOps (Flux/ArgoCD), sign manifests, verify integrity.

---

## 6. mTLS (Mutual TLS)

### 6.1 Fundamentals & PKI
- **mTLS**: Both client and server authenticate via X.509 certificates. Prevents MITM, ensures workload identity.
- **PKI Hierarchy**:
  - **Root CA**: Self-signed, offline, long-lived (10+ years). Signs intermediate CAs.
  - **Intermediate CA**: Issues workload certificates, shorter lifespan (1–3 years).
  - **Leaf Certificates**: Issued to workloads (pods, services), short-lived (1–24 hours).
- **Certificate Fields**:
  - `Subject`: CN (Common Name) = service identity (e.g., `spiffe://cluster.local/ns/default/sa/my-app`).
  - `SAN (Subject Alternative Name)`: DNS names, URIs, IPs.
  - `KeyUsage`: digitalSignature, keyEncipherment.
  - `ExtendedKeyUsage`: serverAuth, clientAuth.

### 6.2 mTLS in Service Mesh
- **Istio**: Envoy sidecars perform mTLS; certificates issued by Istio CA (istiod) or external CA (cert-manager, Vault).
  - **STRICT mode**: All service-to-service traffic encrypted.
  - **PERMISSIVE mode**: Accept both mTLS and plaintext (for migration).
- **Linkerd**: Lightweight proxy (linkerd2-proxy); built-in mTLS (no external CA needed). Uses ECDSA P-256 certificates, 24-hour lifespan.
- **Cilium Service Mesh**: Uses Envoy or Cilium's eBPF-based proxy; integrates with cert-manager for certificate issuance.
- **Certificate Rotation**: Automated via control-plane; proxies watch for cert updates, reload without downtime.

### 6.3 SPIFFE/SPIRE
- **SPIFFE (Secure Production Identity Framework For Everyone)**: Standard for workload identity (SVIDs = SPIFFE Verifiable Identity Documents).
- **SPIRE (SPIFFE Runtime Environment)**: Open-source implementation; server (CA), agent (issues certs to workloads).
- **Workload Registration**: Admin creates registration entries (selectors = k8s labels); agent attests workload identity, fetches SVIDs.
- **Integration**: Istio, Envoy, Linkerd, Cilium can consume SPIRE-issued certificates for mTLS.

### 6.4 Certificate Provisioning & Lifecycle
- **cert-manager**: Kubernetes controller for certificate automation. Integrates with Let's Encrypt (ACME), Vault, Venafi, self-signed CA.
  - **Issuer/ClusterIssuer**: CA backend.
  - **Certificate CRD**: Requests cert, stores in Secret.
  - **CSI Driver**: Mounts certs as volumes (auto-rotates).
- **Vault PKI**: HashiCorp Vault as CA; dynamic secrets, audit logging, fine-grained RBAC.
- **Short-Lived Certificates**: Reduce blast radius of compromise. Recommendation: ≤24 hours for workload certs, 1–3 years for intermediate CA.

### 6.5 Threat Model & Hardening
- **Threats**: Private key exfiltration, certificate theft, weak crypto (RSA-1024), expired certs, CA compromise, certificate pinning bypass.
- **Mitigations**:
  - **Hardware Security Modules (HSM)**: Store Root CA private key offline (FIPS 140-2 Level 3).
  - **Key Rotation**: Automate intermediate CA rotation (1-year validity, rotate at 6 months).
  - **Certificate Transparency (CT)**: Log all issued certs; detect rogue certificates.
  - **OCSP Stapling / CRL**: Revocation checking; prefer OCSP stapling (performance).
  - **Strong Crypto**: TLS 1.3 only, ECDSA P-256 or Ed25519, AES-GCM cipher suites, disable RSA-1024/SHA-1.
  - **Least Privilege**: cert-manager runs with minimal RBAC; separate ServiceAccount per Issuer.
  - **Monitoring**: Alert on certificate expiry (30/7/1 days before), CA signing anomalies, unauthorized cert requests.

---

## 7. gRPC (Google Remote Procedure Call)

### 7.1 Architecture & Protocol
- **Transport**: HTTP/2 (multiplexing, header compression, server push). Single TCP connection for multiple concurrent streams.
- **Serialization**: Protocol Buffers (protobuf) by default; compact binary format, backward/forward compatible.
- **Service Definition**: `.proto` files define services (RPCs) and messages. Compiler (`protoc`) generates client/server stubs.
- **RPC Types**:
  - **Unary**: Single request → single response (like REST).
  - **Server Streaming**: Single request → stream of responses (e.g., log tailing).
  - **Client Streaming**: Stream of requests → single response (e.g., file upload).
  - **Bidirectional Streaming**: Both sides stream (e.g., chat, real-time metrics).

### 7.2 Load Balancing & Service Discovery
- **Client-Side LB**: gRPC clients maintain connection pool, balance RPCs across endpoints. Requires service discovery (DNS, Consul, etcd).
  - **Lookaside LB**: Client queries separate LB (e.g., envoy-control-plane) for endpoint list.
  - **xDS Protocol**: Envoy's dynamic config API; gRPC clients can consume xDS for LB/routing/security.
- **Server-Side LB**: Proxy (Envoy, nginx) terminates gRPC, balances to backends. Simpler for clients but single point of failure.
- **Kubernetes**: Use headless Service (clusterIP: None) for client-side LB; DNS returns all pod IPs. Or use Envoy/Linkerd as sidecar proxy.

### 7.3 Security Features
- **TLS**: gRPC over HTTP/2 with TLS (port 443 or custom). Supports mTLS (client cert authentication).
- **Authentication**:
  - **Token-Based**: JWT in metadata (`authorization: Bearer <token>`).
  - **Channel Credentials**: TLS certs.
  - **Call Credentials**: Per-RPC credentials (e.g., OAuth2 token).
- **Authorization**: Interceptors (middleware) check claims (JWT sub/aud), enforce RBAC.
- **Encryption**: TLS 1.3 recommended; ALPN negotiation (application-layer protocol = `h2`).

### 7.4 Interceptors & Observability
- **Interceptors**: Middleware for cross-cutting concerns (logging, auth, metrics, tracing). Unary/stream, client/server.
- **OpenTelemetry**: Instrument gRPC for traces (gRPC span → parent span), metrics (RPC latency, error rate), logs.
- **Prometheus Metrics**: Use `grpc-prometheus` interceptor; expose `/metrics` endpoint. Key metrics: `grpc_server_handled_total`, `grpc_server_handling_seconds`.
- **Distributed Tracing**: Propagate trace context (`traceparent` header) via interceptors; integrates with Jaeger, Zipkin, Tempo.

### 7.5 Threat Model & Hardening
- **Threats**: Plaintext traffic (no TLS), token theft (JWT in logs), DoS (unary streaming attacks), service impersonation, man-in-the-middle.
- **Mitigations**:
  - **Mandatory TLS**: Disable plaintext gRPC in production; enforce TLS 1.3.
  - **mTLS for Service-to-Service**: Verify client certificates (CN, SAN); integrate with SPIRE/Istio.
  - **Rate Limiting**: Per-RPC limits (Envoy external authz, or middleware).
  - **Input Validation**: Validate protobuf messages (max size, required fields, regex checks).
  - **Timeouts & Deadlines**: Set per-RPC deadlines; prevent resource exhaustion.
  - **Logging**: Log RPC method, status, latency, user identity (from JWT). Avoid logging sensitive data (tokens, PII).
  - **Secure Defaults**: Use `grpc.WithTransportCredentials` (not `grpc.WithInsecure`), verify server cert hostname.

---

## 8. NATS (Neural Autonomic Transport System)

### 8.1 Architecture & Messaging Patterns
- **NATS Core**: Lightweight pub-sub broker; fire-and-forget, at-most-once delivery. No persistence by default.
- **NATS JetStream**: Persistence layer; streaming, at-least-once/exactly-once delivery, replay, message deduplication.
- **NATS Leaf Nodes**: Connect remote clusters/edge devices; hub-and-spoke topology.
- **Messaging Patterns**:
  - **Pub-Sub**: Publishers send to subject (topic); subscribers receive all messages.
  - **Request-Reply**: Synchronous RPC-like; publisher sends request to subject, single subscriber replies to reply-subject.
  - **Queue Groups**: Load-balanced pub-sub; one subscriber per group receives each message (like Kafka consumer groups).

### 8.2 Subjects & Wildcards
- **Subject Hierarchy**: Dot-separated tokens (e.g., `orders.us.west`). Wildcards: `*` (single token), `>` (multiple tokens).
- **Examples**:
  - `orders.*` matches `orders.us`, `orders.eu`.
  - `orders.>` matches `orders.us.west`, `orders.eu.east.retail`.
- **Security**: Subject-level ACLs; users can pub/sub to specific subjects only.

### 8.3 Security Features
- **TLS**: Encrypt client-server and server-server connections. Supports mTLS (client certs).
- **Authentication**:
  - **Token**: Shared secret (simple but insecure for multi-tenant).
  - **Username/Password**: Basic auth.
  - **NATS Accounts**: Multi-tenancy; each account has isolated subjects, separate limits.
  - **JWT-Based**: Operator (root), Account (tenant), User (workload) JWTs. Decentralized auth; NATS server validates JWTs via public key.
- **Authorization**: Subject permissions (pub/sub/deny) per user. NATS resolver (JWTs) or config file.

### 8.4 JetStream & Persistence
- **Streams**: Durable message store; configurable retention (time/size/interest-based).
- **Consumers**: Durable (state persisted) or ephemeral. Pull (fetch messages) or push (server sends).
- **Exactly-Once Semantics**: Message deduplication (via `Nats-Msg-Id` header) + idempotent consumers.
- **Replicas**: JetStream cluster (Raft consensus); 3 or 5 replicas for HA. Leader election, automatic failover.

### 8.5 Use Cases in Cloud-Native
- **Service Mesh Control Plane**: Linkerd uses NATS for tap/watch streams (observability).
- **Event-Driven Microservices**: Async communication (order-service → payment-service → shipping-service).
- **Edge Computing**: Leaf nodes connect edge devices to central NATS cluster; fan-in telemetry, fan-out commands.
- **Kubernetes Events**: NATS replaces Kafka for lightweight event sourcing (K-Native Eventing).

### 8.6 Threat Model & Hardening
- **Threats**: Unencrypted traffic, shared token leak, subject wildcard abuse (subscribe to all subjects), JetStream DoS (fill disk), NATS server compromise.
- **Mitigations**:
  - **Mandatory TLS**: Enforce TLS 1.3 for all connections; verify server certs.
  - **JWT-Based Auth**: Use NATS decentralized auth; rotate User JWTs frequently (1-hour TTL).
  - **Least Privilege**: Grant minimal subject permissions (e.g., `orders.create` pub only, `orders.>` sub deny).
  - **Rate Limiting**: Per-account connection limits, message rate limits (NATS server config).
  - **JetStream Quotas**: Limit stream/consumer count per account, max message size, retention policies.
  - **Network Policies**: Restrict NATS client connections (only from trusted namespaces); use Calico/Cilium policies.
  - **Monitoring**: Prometheus exporter for NATS; alert on high latency, connection spikes, auth failures.

---

## 9. Gateway API (Kubernetes Ingress Evolution)

### 9.1 Fundamentals & Motivation
- **Problem with Ingress**: Single resource type, limited expressiveness (no header routing, no traffic splitting), vendor-specific annotations.
- **Gateway API**: Multi-resource model (GatewayClass, Gateway, HTTPRoute, TCPRoute, TLSRoute). Role-oriented (infra admin vs app developer).
- **Key Concepts**:
  - **GatewayClass**: Infrastructure provider (e.g., Istio, Cilium, Contour). Analogous to StorageClass.
  - **Gateway**: Instance of GatewayClass; defines listeners (protocol, port, TLS). Analogous to LoadBalancer Service.
  - **HTTPRoute/TCPRoute**: Routing rules; attached to Gateway. Defines backends (Services), weights, headers, filters.

### 9.2 Architecture & Components
- **Controller**: Provider-specific (Cilium Gateway controller, Istio Gateway controller). Watches Gateway API resources, programs dataplane (Envoy, eBPF, NGINX).
- **ReferenceGrant**: Cross-namespace references; e.g., HTTPRoute in `app-ns` references Gateway in `infra-ns`.
- **Filters**: Request/response manipulation (header add/remove, redirect, URL rewrite).
- **BackendRefs**: Target services; supports weights (traffic splitting), multiple backends (A/B, canary).

### 9.3 Advanced Routing & Policy
- **Header-Based Routing**: HTTPRoute matches on headers (e.g., `X-User-Type: premium` → premium-backend).
- **Traffic Splitting**: Canary (90% stable, 10% canary) via weighted backendRefs.
- **TLS Passthrough**: TLSRoute forwards encrypted traffic to backend without termination.
- **Policy Attachment**: External CRDs (e.g., `BackendTLSPolicy`, `RateLimitPolicy`) attach to Gateway/HTTPRoute for cross-cutting concerns.

### 9.4 Multi-Cluster & Service Mesh
- **Multi-Cluster Services**: Clusterset (Submariner, Cilium Cluster Mesh) + Gateway API. HTTPRoute references Service in remote cluster via ServiceImport.
- **Service Mesh Integration**: Istio VirtualService → HTTPRoute; Linkerd HTTPRoute → Service split. Gateway API as unified API for ingress + mesh.
- **Egress Gateway**: Gateway with `type: Egress`; outbound traffic routed via dedicated nodes (audit, NAT, TLS inspection).

### 9.5 Security Model
- **RBAC**: Separate roles (GatewayClass = infra admin, Gateway = platform team, HTTPRoute = app developer).
- **TLS Termination**: Gateway spec includes TLS config (certificateRefs → Secret). Supports SNI (multiple certs per listener).
- **mTLS Upstream**: BackendTLSPolicy defines client cert for backend connection (e.g., Gateway → Service mTLS).
- **Rate Limiting**: Attach RateLimitPolicy (hypothetical CRD); e.g., 100 req/s per client IP.

### 9.6 Threat Model & Hardening
- **Threats**: Route hijacking (malicious HTTPRoute steals traffic), TLS cert theft, RBAC bypass, Gateway controller compromise, DoS (unbounded routes).
- **Mitigations**:
  - **RBAC Enforcement**: Use ReferenceGrant to prevent cross-namespace route hijacking. Namespace-scoped HTTPRoutes.
  - **TLS Best Practices**: Use cert-manager for certificate issuance; short-lived certs, automated rotation.
  - **Gateway Controller Security**: Run as least-privilege; drop capabilities, read-only root, SELinux/AppArmor.
  - **Rate Limiting & WAF**: Integrate external policy controllers (Envoy external authz, OPA).
  - **Audit Logs**: Log all route changes, TLS handshakes, backend failures. Send to SIEM.
  - **Policy Validation**: Admission webhooks (OPA Gatekeeper, Kyverno) validate Gateway API resources (e.g., no wildcard hosts in HTTPRoute).

---

## 10. Cross-Cutting Themes & Integration

### 10.1 Zero-Trust Networking
- **Principle**: Never trust, always verify. No implicit trust based on network location.
- **Implementation**:
  - **Identity-Based Access**: Cilium/Calico policies use workload identity (labels, SPIFFE), not IPs.
  - **mTLS Everywhere**: Service mesh enforces mTLS (Istio STRICT mode).
  - **Micro-Segmentation**: Per-pod NetworkPolicies; deny-all default.
  - **Continuous Verification**: Short-lived certs (24h), real-time policy evaluation (eBPF).

### 10.2 Observability Stack
- **Metrics**: Prometheus (scrape Cilium/Calico/NATS/gRPC exporters), Grafana dashboards (latency, error rate, saturation).
- **Logs**: Fluentd/Fluent Bit (collect logs), Loki (store), Grafana (query). Structured logs (JSON), correlation IDs.
- **Traces**: OpenTelemetry (instrument gRPC, Envoy), Jaeger/Tempo (backend), trace propagation (W3C Trace Context).
- **Flow Logs**: Hubble (Cilium), Calico flow logs. Network-level visibility (who talked to whom, policy violations).

### 10.3 Failure Modes & Recovery
- **CNI Plugin Failure**: Pod network unreachable; readiness/liveness probes fail, pod restarted. DaemonSet restart (Felix/cilium-agent) restores state.
- **BGP Session Down**: Route withdrawal; ECMP redistributes traffic to surviving paths. Monitor BGP session state, alert on flapping.
- **NATS Server Failure**: JetStream consumers reconnect to replica. Client libraries auto-reconnect (backoff + jitter).
- **Gateway Controller Crash**: Dataplane (Envoy) continues forwarding; control-plane reconciliation paused. HA controller (leader election).
- **Certificate Expiry**: mTLS fails; connections refused. Alerting (30/7/1 days before expiry), automated rotation (cert-manager).

### 10.4 Performance Tuning
- **eBPF Datapath**: Bypass netfilter (iptables), use XDP for line-rate packet processing. Tune eBPF map sizes (identity table, policy cache).
- **VXLAN Offload**: Enable hardware offload (NIC supports VXLAN encap/decap). Check `ethtool -k` for `tx-udp_tnl-segmentation`.
- **gRPC Connection Pooling**: Reuse HTTP/2 connections; configure max concurrent streams (default 100). Use `grpc.WithKeepalive` for long-lived connections.
- **NATS Clustering**: Use 3–5 nodes (Raft); tune heartbeat intervals (1s default). Avoid single-core bottleneck (shard subjects).
- **BGP Route Aggregation**: Summarize pod CIDRs (aggregate /26 into /24) to reduce routing table size. Balance against path diversity.

---

## 11. Threat Modeling Framework (STRIDE)

### Applied to Networking Stack
| Threat | Example | Mitigation |
|--------|---------|------------|
| **Spoofing** | Pod impersonates another pod (steal service account token) | mTLS (SPIFFE identity), Cilium identity enforcement |
| **Tampering** | On-path attacker modifies packets (VXLAN unencrypted) | WireGuard/IPsec overlay encryption, mTLS for L7 |
| **Repudiation** | Attacker denies sending malicious traffic | Flow logs (Hubble, Calico), audit logs (NATS, gRPC) |
| **Information Disclosure** | Sniff pod-to-pod traffic on compromised underlay | End-to-end encryption (WireGuard, mTLS) |
| **Denial of Service** | Flood NATS server, exhaust BGP session limits | Rate limiting (NATS), max-prefix (BGP), admission webhooks (Gateway API) |
| **Elevation of Privilege** | CNI plugin compromise → host root access | Least-privilege (drop caps, read-only root), SELinux/AppArmor, eBPF verifier |

---

## 12. References & Next Steps

### Key References
1. **BGP**: RFC 4271 (BGP-4), RFC 5549 (Unnumbered BGP), RPKI (RFC 6480), GTSM (RFC 5082).
2. **VXLAN**: RFC 7348, BGP-EVPN (RFC 7432).
3. **CNI**: CNCF CNI Spec (https://github.com/containernetworking/cni/blob/main/SPEC.md).
4. **Cilium**: Docs (https://docs.cilium.io), eBPF (https://ebpf.io).
5. **Calico**: Docs (https://docs.tigera.io/calico), BGP Design (https://www.tigera.io/learn/guides/kubernetes-networking/calico-architecture).
6. **mTLS/SPIFFE**: SPIFFE Spec (https://spiffe.io/docs), cert-manager (https://cert-manager.io/docs).
7. **gRPC**: Docs (https://grpc.io/docs), Security Guide (https://grpc.io/docs/guides/auth).
8. **NATS**: Docs (https://docs.nats.io), JetStream (https://docs.nats.io/nats-concepts/jetstream).
9. **Gateway API**: KEP (https://gateway-api.sigs.k8s.io), Implementations (https://gateway-api.sigs.k8s.io/implementations).

### Next 3 Steps (Hands-On)
1. **Deploy Cilium + Hubble in Kind/Minikube**:
   - Enable WireGuard encryption, enforce L7 HTTP policy (allow GET /api, deny POST /admin).
   - Observe flows in Hubble UI, verify encryption with tcpdump.
   - Commands: `cilium install`, `cilium hubble enable`, `cilium connectivity test`.

2. **Setup NATS JetStream with mTLS**:
   - Deploy NATS cluster (3 replicas), create stream (`orders`), consumer (`payment-processor`).
   - Configure JWT-based auth (operator → account → user), enforce TLS 1.3.
   - Test pub-sub with `nats` CLI, verify TLS handshake (Wireshark/tshark).

3. **Implement Gateway API with Cilium**:
   - Create HTTPRoute with canary split (90% stable, 10% v2), header-based routing (`X-Version: beta` → beta-backend).
   - Attach RateLimitPolicy (hypothetical), test with hey/wrk.
   - Observe route distribution in Cilium Gateway controller logs, metrics (Prometheus).

---

**Architecture ASCII (Layered Stack)**:
```
┌─────────────────────────────────────────────────────────────────┐
│  Application Layer (Workloads)                                  │
│  - Pods w/ SPIFFE identity (mTLS certificates)                  │
│  - gRPC services (client-side LB, OpenTelemetry tracing)        │
│  - NATS pub-sub (async events, JetStream persistence)           │
└─────────────────────────────────────────────────────────────────┘
                           ↓ (Service-to-Service)
┌─────────────────────────────────────────────────────────────────┐
│  Service Mesh / L7 Policy                                       │
│  - Cilium L7 policy (HTTP path, gRPC method)                    │
│  - Gateway API (HTTPRoute, traffic split, TLS termination)      │
│  - Envoy sidecar (mTLS, observability, retries)                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓ (Encrypted mTLS)
┌─────────────────────────────────────────────────────────────────┐
│  L3/L4 Policy & Routing (CNI)                                   │
│  - Cilium eBPF datapath (identity-based policy, XDP)            │
│  - Calico Felix (iptables/eBPF, BGP route advertisement)        │
│  - NetworkPolicy enforcement (deny-all default)                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓ (Encrypted WireGuard/IPsec)
┌─────────────────────────────────────────────────────────────────┐
│  Overlay Network (Encapsulation)                                │
│  - VXLAN (UDP/4789, VNI per tenant)                             │
│  - Geneve (flexible TLVs, future-proof)                         │
│  - Native routing (Calico BGP mode, no encap)                   │
└─────────────────────────────────────────────────────────────────┘
                           ↓ (IP fabric)
┌─────────────────────────────────────────────────────────────────┐
│  Underlay Network (Physical/Virtual)                            │
│  - BGP fabric (spine-leaf, ECMP, unnumbered BGP)                │
│  - ToR switches (BGP peers with Calico/Cilium)                  │
│  - Cloud VPC (AWS VPC CNI, GCP VPC-native, Azure CNI)           │
└─────────────────────────────────────────────────────────────────┘
```

**Rollout/Rollback**:
- **Rollout**: Blue-green (Gateway API traffic split 0→100%), canary (10%→50%→100% over 3 stages), feature flags (HTTPRoute header routing).
- **Rollback**: Immediate (change backendRefs weights), automated (ArgoCD health check fails → rollback), database migrations (forward-compatible schema).

This guide provides the **conceptual foundation** for understanding modern networking stacks in cloud-native environments. Pair this with hands-on labs (Cilium, Calico, NATS, gRPC) to solidify implementation knowledge. Focus on **security-first design**: deny-by-default policies, end-to-end encryption, workload identity, observability, and defense-in-depth.

# Comprehensive Guide: Networking & Mesh Technologies

**Summary:** Modern cloud-native networking spans L2-L7, combining BGP for routing, VXLAN for overlay networks, CNI for container networking, service meshes (mTLS/gRPC) for secure service-to-service communication, and high-performance messaging (NATS). This guide covers first-principles networking concepts, CNI implementations (Cilium/Calico), mesh architectures, security boundaries, and production deployment patterns. Focus: kernel networking stack, eBPF data planes, certificate management, threat models, and real-world operational trade-offs for multi-tenant Kubernetes and hybrid cloud environments.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer (L7)                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ gRPC Service │  │  HTTP/REST   │  │  NATS PubSub │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │                  │                  │                   │
│  ┌──────▼──────────────────▼──────────────────▼───────┐         │
│  │          Service Mesh (mTLS, AuthZ, Observ)        │         │
│  │    Envoy/Linkerd Proxy | Gateway API (Ingress)     │         │
│  └──────┬──────────────────────────────────────────────┘         │
└─────────┼─────────────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────────────┐
│              Transport/Network Layer (L3/L4)                      │
│  ┌─────────────────────────────────────────────────────┐         │
│  │  CNI Plugin: Cilium (eBPF) / Calico (iptables/eBPF)│         │
│  │  • Network Policies (K8s NetworkPolicy/Cilium NP)  │         │
│  │  • Service Load Balancing (kube-proxy replacement) │         │
│  │  • Encryption (IPsec/WireGuard)                    │         │
│  └─────────────────┬───────────────────────────────────┘         │
│                    │                                              │
│  ┌─────────────────▼───────────────────────────────────┐         │
│  │  Overlay Network: VXLAN/Geneve (Encapsulation)     │         │
│  │  • Tunnel Endpoints (VTEPs)                        │         │
│  │  • VNI/Segment ID for multi-tenancy               │         │
│  └─────────────────┬───────────────────────────────────┘         │
└────────────────────┼──────────────────────────────────────────────┘
                     │
┌────────────────────▼──────────────────────────────────────────────┐
│              Underlay Network (Physical L2/L3)                   │
│  ┌─────────────────────────────────────────────────────┐         │
│  │  BGP Routing (ECMP, AS-Path, Route Reflectors)     │         │
│  │  • eBGP (between AS) / iBGP (within AS)            │         │
│  │  • Leaf-Spine Topology (Data Center)               │         │
│  │  • Anycast IPs for Service Availability            │         │
│  └─────────────────────────────────────────────────────┘         │
│  ┌─────────────────────────────────────────────────────┐         │
│  │  Physical Network: ToR Switches, Spine, NIC        │         │
│  │  • SR-IOV, DPDK for high-performance              │         │
│  │  • RDMA (RoCE) for storage/HPC workloads          │         │
│  └─────────────────────────────────────────────────────┘         │
└───────────────────────────────────────────────────────────────────┘
```

---

## 1. BGP (Border Gateway Protocol)

### First Principles

BGP is the **path-vector routing protocol** that powers the Internet and data-center fabrics. It exchanges reachability information (prefixes) between Autonomous Systems (AS) or within a data center.

**Key Concepts:**
- **AS (Autonomous System):** A collection of IP prefixes under single administrative control (assigned by IANA)
- **eBGP:** Between different ASes (external, multi-hop disabled by default, TTL=1)
- **iBGP:** Within same AS (requires full mesh or route reflectors)
- **Path Attributes:** AS_PATH (loop prevention), LOCAL_PREF (outbound policy), MED (inbound hint), NEXT_HOP
- **ECMP (Equal-Cost Multi-Path):** Multiple best paths for load balancing
- **Anycast:** Same IP advertised from multiple locations for HA/geo-proximity

**Data Center Use Cases:**
- **Leaf-Spine Architecture:** Each leaf (ToR) peers with all spines via eBGP (different AS per rack or per device)
- **Kubernetes Service Advertisement:** MetalLB, Cilium BGP Control Plane advertise LoadBalancer IPs
- **Multi-cloud Hybrid:** BGP over VPN/Direct Connect to peer on-prem with AWS/GCP/Azure

### Lab: BGP with FRRouting and Kubernetes

```bash
# 1. Deploy FRR as DaemonSet for BGP routing
cat <<EOF > frr-daemonset.yaml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: frr-bgp
  namespace: kube-system
spec:
  selector:
    matchLabels:
      app: frr-bgp
  template:
    metadata:
      labels:
        app: frr-bgp
    spec:
      hostNetwork: true
      containers:
      - name: frr
        image: frrouting/frr:v8.5.0
        securityContext:
          privileged: true
          capabilities:
            add: ["NET_ADMIN", "SYS_ADMIN"]
        volumeMounts:
        - name: frr-config
          mountPath: /etc/frr
      volumes:
      - name: frr-config
        configMap:
          name: frr-config
EOF

# 2. FRR Configuration (eBGP peering with upstream router)
cat <<EOF > frr.conf
frr defaults traditional
hostname node1
log syslog informational
!
router bgp 65001
 bgp router-id 10.0.1.1
 neighbor 10.0.0.1 remote-as 65000
 neighbor 10.0.0.1 description upstream-spine
 !
 address-family ipv4 unicast
  network 192.168.100.0/24
  neighbor 10.0.0.1 route-map ALLOW-ALL out
 exit-address-family
!
route-map ALLOW-ALL permit 10
!
line vty
EOF

kubectl create configmap frr-config --from-file=frr.conf -n kube-system
kubectl apply -f frr-daemonset.yaml

# 3. Verify BGP session
kubectl exec -n kube-system frr-bgp-xxxxx -- vtysh -c "show bgp summary"
kubectl exec -n kube-system frr-bgp-xxxxx -- vtysh -c "show ip route bgp"
```

### Cilium BGP Control Plane (Kubernetes-native)

```bash
# Enable Cilium BGP (Helm values)
cat <<EOF > cilium-bgp-values.yaml
bgpControlPlane:
  enabled: true
  
# Deploy Cilium with BGP
helm upgrade --install cilium cilium/cilium \
  --namespace kube-system \
  --values cilium-bgp-values.yaml

# BGP Peering Policy CRD
cat <<EOF > bgp-peering.yaml
apiVersion: cilium.io/v2alpha1
kind: CiliumBGPPeeringPolicy
metadata:
  name: rack1-bgp
spec:
  nodeSelector:
    matchLabels:
      rack: "1"
  virtualRouters:
  - localASN: 65001
    exportPodCIDR: true
    neighbors:
    - peerAddress: "10.0.0.1/32"
      peerASN: 65000
      connectRetryTimeSeconds: 30
      holdTimeSeconds: 90
      keepAliveTimeSeconds: 30
EOF

kubectl apply -f bgp-peering.yaml
```

**Threat Model:**
- **BGP Hijacking:** Malicious AS advertises more specific prefix → mitigation: RPKI (Resource Public Key Infrastructure), prefix filtering
- **Route Leaks:** Misconfigured AS re-advertises routes → mitigation: AS-path filters, max-prefix limits
- **MD5 Auth:** TCP MD5 signature for BGP sessions (weak, migrate to TCP-AO RFC 5925)

---

## 2. VXLAN (Virtual Extensible LAN)

### First Principles

VXLAN is a **network overlay** protocol that encapsulates L2 Ethernet frames inside UDP packets (default port 4789) for transport over L3 IP networks. Solves VLAN scalability (4096 limit) and enables multi-tenancy in cloud/DC.

**Key Concepts:**
- **VNI (VXLAN Network Identifier):** 24-bit ID = 16M segments (vs 4K VLANs)
- **VTEP (VXLAN Tunnel Endpoint):** Device performing encap/decap (hypervisor vSwitch, ToR switch)
- **Unicast vs Multicast:** Head-end replication (HER) for unicast, or multicast for BUM traffic
- **BGP EVPN:** Control plane for VXLAN, distributes MAC/IP reachability via BGP

**Packet Structure:**
```
┌──────────────────────────────────────────────────────┐
│ Outer Ethernet (src=VTEP1 MAC, dst=VTEP2 MAC)      │
├──────────────────────────────────────────────────────┤
│ Outer IP (src=VTEP1 IP, dst=VTEP2 IP)              │
├──────────────────────────────────────────────────────┤
│ Outer UDP (src=random, dst=4789)                   │
├──────────────────────────────────────────────────────┤
│ VXLAN Header (8 bytes: VNI=1234567, flags)         │
├──────────────────────────────────────────────────────┤
│ Inner Ethernet (original L2 frame)                  │
├──────────────────────────────────────────────────────┤
│ Inner IP / Payload                                   │
└──────────────────────────────────────────────────────┘
```

### Lab: VXLAN with Linux Bridge

```bash
# Node1 (VTEP1: 192.168.1.10)
ip link add vxlan100 type vxlan \
  id 100 \
  dstport 4789 \
  local 192.168.1.10 \
  nolearning

ip link set vxlan100 up
ip addr add 10.100.0.1/24 dev vxlan100

# Add remote VTEP (Node2: 192.168.1.20)
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 192.168.1.20

# Node2 (VTEP2: 192.168.1.20)
ip link add vxlan100 type vxlan \
  id 100 \
  dstport 4789 \
  local 192.168.1.20 \
  nolearning

ip link set vxlan100 up
ip addr add 10.100.0.2/24 dev vxlan100
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 192.168.1.10

# Test connectivity
ping -c 3 10.100.0.2  # from Node1
tcpdump -i eth0 'port 4789' -vvv  # observe VXLAN encap
```

### Cilium VXLAN (Default CNI Mode)

```yaml
# Cilium ConfigMap (VXLAN mode)
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-config
  namespace: kube-system
data:
  tunnel: "vxlan"  # or "geneve" or "disabled" (native routing)
  enable-ipv4: "true"
  enable-ipv6: "false"
```

**Calico VXLAN:**
```bash
# Calico IPPool with VXLAN
cat <<EOF | kubectl apply -f -
apiVersion: projectcalico.org/v3
kind: IPPool
metadata:
  name: vxlan-pool
spec:
  cidr: 10.244.0.0/16
  vxlanMode: Always  # or CrossSubnet (VXLAN only for cross-subnet)
  natOutgoing: true
EOF
```

**Performance Trade-offs:**
- **Overhead:** 50 bytes (Outer Eth 14 + IP 20 + UDP 8 + VXLAN 8) → MTU considerations (set pod MTU to 1450)
- **CPU:** Encap/decap overhead (mitigated with hardware offload: NIC TSO/GSO/Checksum)
- **Latency:** +50-200µs per hop

---

## 3. CNI (Container Network Interface)

### First Principles

CNI is a **plugin specification** for configuring network interfaces in Linux containers. Kubelet invokes CNI plugins during pod creation/deletion.

**CNI Operations:**
1. **ADD:** Create network interface, assign IP, configure routes
2. **DEL:** Delete network interface, release IP
3. **CHECK:** Verify network state
4. **VERSION:** Report supported CNI spec version

**CNI Plugin Chain:**
```json
{
  "cniVersion": "1.0.0",
  "name": "k8s-pod-network",
  "plugins": [
    {
      "type": "bridge",
      "bridge": "cni0",
      "isGateway": true,
      "ipMasq": true,
      "ipam": {
        "type": "host-local",
        "subnet": "10.244.0.0/16"
      }
    },
    {
      "type": "portmap",
      "capabilities": {"portMappings": true}
    },
    {
      "type": "bandwidth",
      "ingressRate": 1000000,
      "egressRate": 1000000
    }
  ]
}
```

### Lab: Custom CNI Plugin (Go)

```go
// cni-simple/main.go
package main

import (
    "encoding/json"
    "fmt"
    "net"
    "os"

    "github.com/containernetworking/cni/pkg/skel"
    "github.com/containernetworking/cni/pkg/types"
    current "github.com/containernetworking/cni/pkg/types/100"
    "github.com/containernetworking/cni/pkg/version"
    "github.com/containernetworking/plugins/pkg/ip"
    "github.com/containernetworking/plugins/pkg/ns"
    "github.com/vishvananda/netlink"
)

type NetConf struct {
    types.NetConf
    Bridge string `json:"bridge"`
}

func cmdAdd(args *skel.CmdArgs) error {
    conf := NetConf{}
    if err := json.Unmarshal(args.StdinData, &conf); err != nil {
        return err
    }

    // Get bridge or create
    br, err := netlink.LinkByName(conf.Bridge)
    if err != nil {
        return fmt.Errorf("failed to find bridge %s: %v", conf.Bridge, err)
    }

    // Create veth pair
    vethName := fmt.Sprintf("veth%s", args.ContainerID[:8])
    veth := &netlink.Veth{
        LinkAttrs: netlink.LinkAttrs{Name: vethName},
        PeerName:  "eth0",
    }
    if err := netlink.LinkAdd(veth); err != nil {
        return err
    }

    // Attach host-side veth to bridge
    hostVeth, _ := netlink.LinkByName(vethName)
    if err := netlink.LinkSetMaster(hostVeth, br); err != nil {
        return err
    }
    netlink.LinkSetUp(hostVeth)

    // Move peer to container netns
    peerVeth, _ := netlink.LinkByName("eth0")
    netns, _ := ns.GetNS(args.Netns)
    if err := netlink.LinkSetNsFd(peerVeth, int(netns.Fd())); err != nil {
        return err
    }

    // Configure inside netns
    netns.Do(func(_ ns.NetNS) error {
        link, _ := netlink.LinkByName("eth0")
        ip.RenameLink("eth0", args.IfName)
        netlink.LinkSetUp(link)
        
        // Allocate IP (simplified - use IPAM plugin in production)
        addr, _ := netlink.ParseAddr("10.244.1.5/24")
        netlink.AddrAdd(link, addr)
        
        // Add default route
        gw := net.ParseIP("10.244.1.1")
        netlink.RouteAdd(&netlink.Route{
            LinkIndex: link.Attrs().Index,
            Dst:       nil, // default
            Gw:        gw,
        })
        return nil
    })

    // Return result
    result := &current.Result{
        CNIVersion: current.ImplementedSpecVersion,
        IPs: []*current.IPConfig{{
            Address: net.IPNet{IP: net.ParseIP("10.244.1.5"), Mask: net.CIDRMask(24, 32)},
            Gateway: net.ParseIP("10.244.1.1"),
        }},
    }
    return types.PrintResult(result, conf.CNIVersion)
}

func cmdDel(args *skel.CmdArgs) error {
    // Delete veth pair (peer auto-deleted when netns destroyed)
    vethName := fmt.Sprintf("veth%s", args.ContainerID[:8])
    link, err := netlink.LinkByName(vethName)
    if err == nil {
        netlink.LinkDel(link)
    }
    return nil
}

func main() {
    skel.PluginMain(cmdAdd, cmdCheck, cmdDel, version.All, "simple-cni")
}

func cmdCheck(args *skel.CmdArgs) error { return nil }
```

```bash
# Build and install
go mod init cni-simple
go get github.com/containernetworking/cni@v1.1.2
go get github.com/containernetworking/plugins@v1.2.0
go get github.com/vishvananda/netlink
GOOS=linux GOARCH=amd64 go build -o /opt/cni/bin/simple-cni main.go

# Test with containernetworking/cni test tool
export CNI_PATH=/opt/cni/bin
export NETCONFPATH=/etc/cni/net.d
cnitool add simple-cni /var/run/netns/test < /etc/cni/net.d/10-simple.conf
```

---

## 4. Cilium (eBPF-based CNI)

### Architecture

Cilium replaces iptables/kube-proxy with **eBPF programs** loaded into kernel for:
- **Packet filtering:** XDP (eXpress Data Path) at driver level
- **Load balancing:** Socket-level LB, connection tracking
- **Network policy:** L3-L7 enforcement (HTTP/Kafka/DNS-aware)
- **Observability:** Hubble (flow logs, service maps)

**eBPF Program Locations:**
```
┌─────────────────────────────────────┐
│  User Space: Cilium Agent           │
├─────────────────────────────────────┤
│  Kernel Space:                       │
│  • XDP (NIC driver) - DDoS/Firewall │
│  • TC (Traffic Control) - Policy    │
│  • Socket (cgroup/BPF) - L7 LB      │
│  • Tracepoint - Observability       │
└─────────────────────────────────────┘
```

### Deployment

```bash
# Install Cilium CLI
CILIUM_CLI_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/cilium-cli/main/stable.txt)
curl -L --remote-name-all https://github.com/cilium/cilium-cli/releases/download/${CILIUM_CLI_VERSION}/cilium-linux-amd64.tar.gz{,.sha256sum}
sha256sum --check cilium-linux-amd64.tar.gz.sha256sum
sudo tar xzvfC cilium-linux-amd64.tar.gz /usr/local/bin
rm cilium-linux-amd64.tar.gz{,.sha256sum}

# Install Cilium on K8s (replace kube-proxy)
cilium install \
  --version 1.14.5 \
  --set kubeProxyReplacement=strict \
  --set ipam.mode=kubernetes \
  --set encryption.enabled=true \
  --set encryption.type=wireguard \
  --set hubble.relay.enabled=true \
  --set hubble.ui.enabled=true

# Verify
cilium status --wait
cilium connectivity test
```

### Network Policies (L3-L7)

```yaml
# L3/L4 Policy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-frontend-to-backend
spec:
  endpointSelector:
    matchLabels:
      app: backend
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: frontend
    toPorts:
    - ports:
      - port: "8080"
        protocol: TCP

---
# L7 HTTP Policy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-get-only
spec:
  endpointSelector:
    matchLabels:
      app: api
  ingress:
  - fromEndpoints:
    - matchLabels:
        app: client
    toPorts:
    - ports:
      - port: "80"
        protocol: TCP
      rules:
        http:
        - method: "GET"
          path: "/api/v1/.*"
```

### Encryption (WireGuard)

```bash
# Enable WireGuard node-to-node encryption
cilium config set encryption.enabled true
cilium config set encryption.type wireguard

# Verify encryption
cilium encrypt status
cilium status | grep -i encryption

# Test with tcpdump (should see encrypted payload)
tcpdump -i cilium_wg0 -vvv
```

**Threat Model:**
- **Lateral Movement:** Compromised pod → mitigation: strict NetworkPolicies (default-deny), L7 policies
- **Data Exfiltration:** Pod communicates with C2 → mitigation: DNS policies, egress gateways, Hubble flow analysis
- **Node Compromise:** Root on node → mitigation: WireGuard encryption (prevents sniffing), Seccomp/AppArmor, immutable infra

---

## 5. Calico (Policy & Routing)

### Architecture

Calico uses **BGP** for pod route distribution (no overlay by default) or VXLAN/IP-in-IP for encapsulation. **Felix** agent programs iptables/eBPF dataplane.

**Routing Modes:**
- **BGP:** Direct routing (flat L3, requires BGP peer on ToR/router) - best performance
- **IP-in-IP:** Encapsulation when cross-subnet (20 bytes overhead)
- **VXLAN:** Full overlay (50 bytes overhead)

### Deployment

```bash
# Install Calico with Tigera operator
kubectl create -f https://raw.githubusercontent.com/projectcalico/calico/v3.27.0/manifests/tigera-operator.yaml

# Custom Installation (BGP mode, eBPF dataplane)
cat <<EOF | kubectl apply -f -
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    bgp: Enabled
    ipPools:
    - cidr: 10.244.0.0/16
      encapsulation: None  # Pure BGP
      natOutgoing: true
      nodeSelector: all()
  flexVolumePath: /usr/libexec/kubernetes/kubelet-plugins/volume/exec/
  kubeletVolumePluginPath: /var/lib/kubelet/volumeplugins/
  linuxDataplane: BPF  # eBPF dataplane (requires kernel 5.3+)
EOF

# Verify
kubectl get installation default -o yaml
calicoctl node status
```

### Network Policies (GlobalNetworkPolicy)

```yaml
# Global default-deny
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: default-deny-all
spec:
  selector: all()
  types:
  - Ingress
  - Egress

---
# Allow DNS
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: allow-dns
spec:
  selector: all()
  types:
  - Egress
  egress:
  - action: Allow
    protocol: UDP
    destination:
      ports: [53]
      selector: k8s-app == "kube-dns"

---
# Egress to external IPs (e.g., specific SaaS)
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
metadata:
  name: allow-stripe-api
  namespace: payment
spec:
  selector: app == "payment-service"
  types:
  - Egress
  egress:
  - action: Allow
    protocol: TCP
    destination:
      ports: [443]
      nets:
      - 54.187.174.169/32  # Stripe API IP
```

### BGP Peering

```yaml
# BGP Peer with ToR switch
apiVersion: projectcalico.org/v3
kind: BGPPeer
metadata:
  name: tor-switch-1
spec:
  peerIP: 10.0.0.1
  asNumber: 65000
  nodeSelector: rack == "1"

---
# BGP Configuration (node-specific ASN)
apiVersion: projectcalico.org/v3
kind: BGPConfiguration
metadata:
  name: default
spec:
  logSeverityScreen: Info
  nodeToNodeMeshEnabled: false  # Disable full mesh, use RR
  asNumber: 65001
  serviceClusterIPs:
  - cidr: 10.96.0.0/12  # Advertise ClusterIPs
  serviceExternalIPs:
  - cidr: 192.168.100.0/24  # Advertise LoadBalancer IPs
```

---

## 6. Service Mesh (mTLS, gRPC, Envoy)

### First Principles

Service mesh provides **Layer 7 traffic management, security (mTLS), and observability** without application code changes. Sidecar proxy (Envoy/Linkerd) intercepts all pod traffic.

**Components:**
- **Data Plane:** Sidecar proxies (Envoy)
- **Control Plane:** Config distribution, certificate issuance (Istiod, Linkerd control plane)
- **mTLS:** Mutual TLS for service-to-service encryption + identity

### Architecture: Istio

```
┌─────────────────────────────────────────────────────┐
│  Control Plane: Istiod (Pilot + CA + Galley)        │
│  • Service Discovery                                 │
│  • Certificate Issuance (SPIFFE/SPIRE)             │
│  • Config (VirtualService, DestinationRule)         │
└────────────┬────────────────────────────────────────┘
             │ xDS API (gRPC)
     ┌───────▼───────┐       ┌───────────────┐
     │  Pod: App A   │       │  Pod: App B   │
     │ ┌───────────┐ │       │ ┌───────────┐ │
     │ │ Envoy     │─┼───────┼─│ Envoy     │ │
     │ │ Sidecar   │ │ mTLS  │ │ Sidecar   │ │
     │ └─────┬─────┘ │       │ └─────┬─────┘ │
     │       │       │       │       │       │
     │ ┌─────▼─────┐ │       │ ┌─────▼─────┐ │
     │ │ App       │ │       │ │ App       │ │
     │ │Container  │ │       │ │Container  │ │
     │ └───────────┘ │       │ └───────────┘ │
     └───────────────┘       └───────────────┘
```

### Deployment: Istio

```bash
# Install Istio CLI
curl -L https://istio.io/downloadIstio | ISTIO_VERSION=1.20.2 sh -
cd istio-1.20.2
export PATH=$PWD/bin:$PATH

# Install with strict mTLS
istioctl install --set profile=demo \
  --set meshConfig.enableTracing=true \
  --set values.global.mtls.enabled=true \
  --set values.global.proxy.privileged=true -y

# Enable sidecar injection for namespace
kubectl label namespace default istio-injection=enabled

# Deploy sample app
kubectl apply -f samples/bookinfo/platform/kube/bookinfo.yaml

# Verify mTLS
kubectl exec -n default "$(kubectl get pod -l app=ratings -o jsonpath='{.items[0].metadata.name}')" \
  -c istio-proxy -- curl -s http://localhost:15000/config_dump | grep -i tls
```

### mTLS Policy (Strict)

```yaml
# PeerAuthentication: enforce mTLS for all workloads in namespace
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: default
spec:
  mtls:
    mode: STRICT

---
# DestinationRule: require mTLS for traffic to reviews service
apiVersion: networking.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: reviews-mtls
spec:
  host: reviews.default.svc.cluster.local
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL  # Use Istio-issued certs
```

### Authorization Policy (L7)

```yaml
# Allow only GET /reviews from productpage
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: reviews-viewer
  namespace: default
spec:
  selector:
    matchLabels:
      app: reviews
  action: ALLOW
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/default/sa/bookinfo-productpage"]
    to:
    - operation:
        methods: ["GET"]
        paths: ["/reviews/*"]
```

### Certificate Rotation

```bash
# Istio uses SPIFFE/SPIRE-style workload identities
# Default cert lifetime: 24h, rotation: 12h (50% of lifetime)

# View cert
kubectl exec -n default deployment/productpage-v1 -c istio-proxy -- \
  openssl s_client -showcerts -connect reviews:9080 < /dev/null 2>/dev/null | \
  openssl x509 -noout -text

# Force cert rotation (by restarting pods)
kubectl rollout restart deployment/productpage-v1 -n default
```

---

## 7. gRPC & HTTP/2

### First Principles

**gRPC** is a high-performance RPC framework using HTTP/2, Protocol Buffers, and bidirectional streaming.

**Benefits:**
- **Multiplexing:** Multiple streams over single TCP connection
- **Header Compression:** HPACK reduces overhead
- **Binary Protocol:** Smaller payloads than JSON/REST
- **Streaming:** Unary, server-streaming, client-streaming, bidirectional

### Lab: gRPC Service with mTLS

```protobuf
// api.proto
syntax = "proto3";
package api;

service Greeter {
  rpc SayHello (HelloRequest) returns (HelloReply);
}

message HelloRequest {
  string name = 1;
}

message HelloReply {
  string message = 1;
}
```

```bash
# Generate Go code
protoc --go_out=. --go-grpc_out=. api.proto
```

```go
// server.go
package main

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "log"
    "net"
    "os"

    pb "example.com/grpc-mtls/api"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

type server struct {
    pb.UnimplementedGreeterServer
}

func (s *server) SayHello(ctx context.Context, in *pb.HelloRequest) (*pb.HelloReply, error) {
    return &pb.HelloReply{Message: "Hello " + in.Name}, nil
}

func main() {
    // Load server cert
    cert, _ := tls.LoadX509KeyPair("server.crt", "server.key")
    
    // Load CA cert for client verification
    caCert, _ := os.ReadFile("ca.crt")
    certPool := x509.NewCertPool()
    certPool.AppendCertsFromPEM(caCert)

    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        ClientAuth:   tls.RequireAndVerifyClientCert,
        ClientCAs:    certPool,
        MinVersion:   tls.VersionTLS13,
    }

    creds := credentials.NewTLS(tlsConfig)
    grpcServer := grpc.NewServer(grpc.Creds(creds))
    pb.RegisterGreeterServer(grpcServer, &server{})

    lis, _ := net.Listen("tcp", ":50051")
    log.Println("gRPC server with mTLS on :50051")
    grpcServer.Serve(lis)
}
```

```go
// client.go
package main

import (
    "context"
    "crypto/tls"
    "crypto/x509"
    "log"
    "os"
    "time"

    pb "example.com/grpc-mtls/api"
    "google.golang.org/grpc"
    "google.golang.org/grpc/credentials"
)

func main() {
    cert, _ := tls.LoadX509KeyPair("client.crt", "client.key")
    caCert, _ := os.ReadFile("ca.crt")
    certPool := x509.NewCertPool()
    certPool.AppendCertsFromPEM(caCert)

    tlsConfig := &tls.Config{
        Certificates: []tls.Certificate{cert},
        RootCAs:      certPool,
        MinVersion:   tls.VersionTLS13,
    }

    creds := credentials.NewTLS(tlsConfig)
    conn, _ := grpc.Dial("localhost:50051", grpc.WithTransportCredentials(creds))
    defer conn.Close()

    client := pb.NewGreeterClient(conn)
    ctx, cancel := context.WithTimeout(context.Background(), time.Second)
    defer cancel()

    r, _ := client.SayHello(ctx, &pb.HelloRequest{Name: "World"})
    log.Printf("Response: %s", r.Message)
}
```

```bash
# Generate certs (cfssl or openssl)
cat > ca-csr.json <<EOF
{
  "CN": "My CA",
  "key": { "algo": "rsa", "size": 2048 }
}
EOF

cfssl gencert -initca ca-csr.json | cfssljson -bare ca

# Server cert
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem \
  -config=ca-config.json -profile=server server-csr.json | cfssljson -bare server

# Client cert
cfssl gencert -ca=ca.pem -ca-key=ca-key.pem \
  -config=ca-config.json -profile=client client-csr.json | cfssljson -bare client

# Run server & client
go run server.go &
go run client.go
```

---

## 8. NATS (Messaging)

### First Principles

**NATS** is a lightweight, high-performance pub-sub messaging system with focus on simplicity, security (TLS, NKeys), and cloud-native deployments.

**Features:**
- **Core NATS:** At-most-once delivery (fire-and-forget)
- **JetStream:** Persistence, exactly-once, replicated streams
- **Security:** TLS, NKeys (ed25519), Accounts (multi-tenancy)
- **Patterns:** Pub-sub, request-reply, queue groups

### Deployment

```bash
# Install NATS with JetStream
helm repo add nats https://nats-io.github.io/k8s/helm/charts/
helm install nats nats/nats \
  --set nats.jetstream.enabled=true \
  --set nats.jetstream.memStorage.enabled=true \
  --set nats.jetstream.memStorage.size=1Gi \
  --set nats.jetstream.fileStorage.enabled=true \
  --set nats.jetstream.fileStorage.size=10Gi \
  --set nats.tls.enabled=true \
  --set nats.tls.secretName=nats-tls-cert

# Create TLS cert (cert-manager)
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: nats-tls-cert
spec:
  secretName: nats-tls-cert
  issuerRef:
    name: ca-issuer
    kind: ClusterIssuer
  dnsNames:
  - nats.default.svc.cluster.local
  - "*.nats.default.svc.cluster.local"
EOF
```

### Go Client (TLS + JetStream)

```go
package main

import (
    "log"
    "time"

    "github.com/nats-io/nats.go"
)

func main() {
    // Connect with TLS
    nc, err := nats.Connect("tls://nats.default.svc.cluster.local:4222",
        nats.RootCAs("/etc/nats-tls/ca.crt"),
        nats.ClientCert("/etc/nats-tls/tls.crt", "/etc/nats-tls/tls.key"),
    )
    if err != nil {
        log.Fatal(err)
    }
    defer nc.Close()

    // JetStream context
    js, _ := nc.JetStream()

    // Create stream
    js.AddStream(&nats.StreamConfig{
        Name:     "EVENTS",
        Subjects: []string{"events.>"},
        Storage:  nats.FileStorage,
        Replicas: 3, // Replicated across 3 NATS servers
    })

    // Publish
    js.Publish("events.user.login", []byte(`{"user":"alice","ts":1234567890}`))

    // Subscribe (durable consumer)
    js.Subscribe("events.>", func(msg *nats.Msg) {
        log.Printf("Received: %s", string(msg.Data))
        msg.Ack()
    }, nats.Durable("processor"), nats.ManualAck())

    time.Sleep(10 * time.Second)
}
```

**Threat Model:**
- **Message Tampering:** No built-in signing → mitigation: sign payload (JWT, HMAC)
- **Unauthorized Access:** Open NATS → mitigation: NKeys auth, accounts, TLS client certs
- **Replay Attacks:** → mitigation: Include timestamp + nonce in messages

---

## 9. Gateway API (K8s Ingress v2)

### First Principles

**Gateway API** is the successor to Ingress, providing **role-oriented, extensible, and expressive** API for L4-L7 traffic routing.

**Resources:**
- **GatewayClass:** Defines controller (e.g., Istio, Cilium, Envoy Gateway)
- **Gateway:** L4 listener (ports, protocols, TLS)
- **HTTPRoute/TCPRoute/UDPRoute:** L7 routing rules
- **ReferenceGrant:** Cross-namespace resource access

### Deployment: Cilium Gateway API

```bash
# Enable Gateway API in Cilium
helm upgrade cilium cilium/cilium \
  --namespace kube-system \
  --reuse-values \
  --set gatewayAPI.enabled=true

# Install Gateway API CRDs
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.0.0/standard-install.yaml
```

### Example: Multi-host Routing with TLS

```yaml
# GatewayClass
apiVersion: gateway.networking.k8s.io/v1beta1
kind: GatewayClass
metadata:
  name: cilium
spec:
  controllerName: io.cilium/gateway-controller

---
# Gateway (HTTPS listener)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: Gateway
metadata:
  name: prod-gateway
  namespace: default
spec:
  gatewayClassName: cilium
  listeners:
  - name: https
    protocol: HTTPS
    port: 443
    tls:
      mode: Terminate
      certificateRefs:
      - name: wildcard-tls-cert
        kind: Secret
    allowedRoutes:
      namespaces:
        from: All

---
# HTTPRoute (app1.example.com -> app1-svc)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: app1-route
  namespace: default
spec:
  parentRefs:
  - name: prod-gateway
  hostnames:
  - "app1.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /
    backendRefs:
    - name: app1-svc
      port: 80

---
# HTTPRoute (app2.example.com -> app2-svc with header-based routing)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: HTTPRoute
metadata:
  name: app2-route
  namespace: default
spec:
  parentRefs:
  - name: prod-gateway
  hostnames:
  - "app2.example.com"
  rules:
  - matches:
    - path:
        type: PathPrefix
        value: /v2
      headers:
      - name: X-API-Version
        value: "2.0"
    backendRefs:
    - name: app2-v2-svc
      port: 80
  - backendRefs:
    - name: app2-v1-svc
      port: 80
```

---

## Threat Model & Mitigations

| **Threat** | **Attack Vector** | **Mitigation** |
|------------|-------------------|----------------|
| **Pod-to-Pod Snooping** | Unencrypted traffic on wire | WireGuard/IPsec (Cilium), mTLS (service mesh) |
| **Lateral Movement** | Compromised pod pivots | NetworkPolicies (default-deny), L7 policies, microsegmentation |
| **BGP Hijacking** | Malicious route advertisement | RPKI, prefix lists, AS-path filters, MD5/TCP-AO auth |
| **DNS Poisoning** | Rogue DNS responses | DNSSEC, DNS policies (Cilium/Calico), CoreDNS hardening |
| **Man-in-the-Middle** | ARP spoofing, rogue gateway | Static ARP, port security, 802.1X |
| **DDoS (L3/L4)** | SYN flood, UDP amplification | XDP eBPF filters (Cilium), rate limiting, BGP Flowspec |
| **Certificate Theft** | Stolen mTLS certs from pod | Short-lived certs (1h), SPIFFE/SPIRE, cert rotation, mount secrets read-only |
| **Unauthorized Access** | No authN/authZ on service | mTLS + AuthorizationPolicy (Istio), OPA Gatekeeper |

---

## Performance Benchmarking

```bash
# 1. Network throughput (iperf3)
kubectl run iperf-server --image=networkstatic/iperf3 -- -s
kubectl run iperf-client --image=networkstatic/iperf3 -- -c iperf-server -t 30 -P 4

# 2. Latency (qperf)
kubectl run qperf-server --image=joshuarobinson/qperf -- -lp 4000
kubectl run qperf-client --image=joshuarobinson/qperf -- qperf-server tcp_lat tcp_bw

# 3. Service mesh overhead
# Baseline: direct pod-to-pod without mesh
# With mesh: same test after injecting sidecar
# Compare latency (expect +1-5ms), throughput (expect -10-20%)

# 4. BGP convergence time
# Shut down node, measure time for routes to update
time kubectl drain node1 --ignore-daemonsets --delete-emptydir-data
# Monitor with: calicoctl node status; watch -n 1 'ip route'

# 5. VXLAN vs native routing
# Compare: encapsulation=VXLAN vs encapsulation=None (BGP)
# Expect: VXLAN +10-15% CPU, native routing lower latency
```

---

## Roll-out Plan

### Phase 1: Foundation (Week 1-2)
1. **Deploy CNI (Cilium)** with WireGuard encryption
2. **Enable Hubble** for observability
3. **Baseline NetworkPolicies** (default-deny, allow DNS/kubelet)
4. **BGP peering** with ToR switches (if applicable)

### Phase 2: Service Mesh (Week 3-4)
1. **Install Istio** control plane
2. **Enable sidecar injection** for selected namespaces (e.g., prod)
3. **mTLS PERMISSIVE** mode (allow both plaintext and mTLS)
4. **Deploy sample app** with traffic management rules
5. **Validate** with connectivity tests, cert verification

### Phase 3: Hardening (Week 5-6)
1. **mTLS STRICT** mode cluster-wide
2. **AuthorizationPolicy** for critical services (L7 rules)
3. **Egress gateways** for external traffic control
4. **Gateway API** for ingress (replace old Ingress resources)
5. **DNS policies** (Cilium DNS-aware NP)

### Rollback Plan
- **Helm rollback**: `helm rollback cilium -n kube-system`
- **Istio downgrade**: `istioctl install --set revision=1.19.5`
- **Emergency**: Disable sidecar injection, delete VirtualServices, revert to kube-proxy

---

## Testing & Validation

```bash
# 1. Connectivity test suite
cilium connectivity test --all-flows

# 2. Network policy validation
kubectl run test-pod --image=busybox -- sleep 3600
kubectl exec test-pod -- wget -qO- http://backend-svc:8080  # Should fail if NP blocks
kubectl label pod test-pod app=frontend  # Add label to match NP
kubectl exec test-pod -- wget -qO- http://backend-svc:8080  # Should succeed

# 3. mTLS verification
kubectl exec -n prod deployment/app1 -c istio-proxy -- \
  curl -v http://localhost:15000/clusters | grep -i tls_context

# 4. Certificate expiry check
kubectl get secrets -A -o json | jq -r '
  .items[] | 
  select(.type=="kubernetes.io/tls") | 
  .metadata.namespace + "/" + .metadata.name + ": " + 
  (.data."tls.crt" | @base64d | capture("Not After : (?<date>.*)").date)
'

# 5. BGP route verification
calicoctl get bgppeer -o wide
ip route show proto bird  # If using BIRD

# 6. Load test with mTLS overhead
fortio load -c 50 -qps 1000 -t 60s https://app.example.com/api
```

---

## Monitoring & Observability

```bash
# 1. Hubble UI (Cilium)
cilium hubble port-forward &
cilium hubble ui

# 2. Prometheus metrics
kubectl port-forward -n istio-system svc/prometheus 9090:9090
# Query: istio_requests_total, envoy_cluster_upstream_cx_total

# 3. Grafana dashboards
# - Cilium Network Overview
# - Istio Service Mesh
# - Node Network Traffic

# 4. Trace latency (Jaeger)
kubectl port-forward -n istio-system svc/tracing 16686:16686

# 5. Flow logs (Hubble CLI)
cilium hubble observe --protocol http --from-pod default/app1
cilium hubble observe --verdict DROPPED  # Dropped packets due to NP
```

---

## References

1. **BGP:**
   - RFC 4271 (BGP-4)
   - RFC 7938 (BGP in Data Centers)
   - [Cumulus Networks BGP guide](https://docs.nvidia.com/networking-ethernet-software/)

2. **VXLAN:**
   - RFC 7348
   - [VXLAN Deep Dive - Ivan Pepelnjak](https://www.ipspace.net/VXLAN_Technical_Deep_Dive)

3. **CNI:**
   - [CNI Specification](https://github.com/containernetworking/cni/blob/main/SPEC.md)
   - [Cilium eBPF Datapath](https://docs.cilium.io/en/stable/concepts/ebpf/)
   - [Calico Architecture](https://docs.tigera.io/calico/latest/reference/architecture/)

4. **Service Mesh:**
   - [Istio Security Model](https://istio.io/latest/docs/concepts/security/)
   - [SPIFFE/SPIRE](https://spiffe.io/docs/)
   - [Envoy Proxy Docs](https://www.envoyproxy.io/docs)

5. **Gateway API:**
   - [K8s Gateway API](https://gateway-api.sigs.k8s.io/)

6. **NATS:**
   - [NATS Security](https://docs.nats.io/running-a-nats-service/configuration/securing_nats)
   - [JetStream Guide](https://docs.nats.io/nats-concepts/jetstream)

---

## Next 3 Steps

1. **Deploy Lab Environment:**
   - 3-node K8s cluster (kind/k3s/kubeadm)
   - Install Cilium with WireGuard + Hubble
   - Test: `cilium connectivity test`

2. **Implement mTLS Service Mesh:**
   - Install Istio with strict mTLS
   - Deploy sample microservices (bookinfo)
   - Create L7 AuthorizationPolicy
   - Verify with: `istioctl analyze`, cert checks

3. **BGP + Gateway API Integration:**
   - Configure Cilium BGP Control Plane (or MetalLB)
   - Deploy Gateway API with TLS termination
   - Advertise LoadBalancer IPs via BGP
   - Test failover: drain node, verify route withdrawal (<5s)

**Commands to verify each step:**
```bash
# Step 1
kubectl get nodes; cilium status; cilium hubble observe

# Step 2
kubectl get peerauthentication -A
kubectl exec -n default deployment/productpage-v1 -c istio-proxy -- \
  pilot-agent request GET certs | jq '[.certificates[] | {subject: .ca_cert[0].subject_alt_names}]'

# Step 3
kubectl get bgppeeringpolicy -A
cilium bgp peers
kubectl get gateway,httproute -A
curl -k https://<GATEWAY_IP>/productpage
```

---

This guide covers **production-grade networking** from L2 underlay (BGP, VXLAN) through L7 service mesh (mTLS, gRPC), with emphasis on **eBPF dataplanes (Cilium), security boundaries, and operational best practices**. All configurations are **reproducible, testable, and threat-modeled** for real-world cloud-native deployments.