# Data Structures & Algorithms in Networking, Linux Net, Network Security & Cloud Network Security

A comprehensive map of what's actively used today — from foundational to modern.

---

## 🌐 1. NETWORKING (General / Protocol Stack)

### Data Structures

| Data Structure | Where Used |
|---|---|
| **Patricia Trie / Radix Trie** | IP routing table — Longest Prefix Match (LPM) |
| **Hash Table** | ARP cache, MAC address tables, flow tables |
| **Priority Queue / Min-Heap** | QoS scheduling, timer management |
| **Ring Buffer (Circular Buffer)** | NIC TX/RX queues, packet I/O |
| **Linked List** | Packet queues, socket buffer chains |
| **Bitmap** | Port availability, VLAN membership |
| **Bloom Filter** | Route filtering, packet deduplication |
| **Interval / Segment Tree** | Port-range matching in ACLs |
| **Red-Black Tree** | Timer wheels, ordered flow tracking |
| **Queue (FIFO / weighted)** | Packet scheduling |

### Algorithms

| Algorithm | Where Used |
|---|---|
| **Dijkstra's** | OSPF, IS-IS shortest path routing |
| **Bellman-Ford** | BGP, RIP distance-vector routing |
| **ECMP (Equal-Cost Multi-Path)** | Load spreading across multiple routes |
| **Spanning Tree (STP/RSTP)** | Loop prevention in L2 switching |
| **Longest Prefix Match (LPM)** | IP forwarding decisions |
| **AIMD (Additive Increase / Multiplicative Decrease)** | TCP congestion control base |
| **CUBIC** | Default TCP congestion control (Linux) |
| **BBR (Bottleneck Bandwidth & RTT)** | Modern TCP CC (Google; YouTube, cloud) |
| **Token Bucket / Leaky Bucket** | Traffic shaping & rate limiting |
| **Weighted Fair Queuing (WFQ)** | QoS bandwidth fairness |
| **Weighted Round Robin** | Load balancing, scheduler |
| **CRC-32** | Ethernet frame error detection |
| **Fletcher / Adler checksum** | UDP-lite, SCTP |
| **Consistent Hashing** | Flow-aware load balancing (L4 LB) |
| **ECMP Hash (5-tuple)** | Multi-path hashing for flows |

---

## 🐧 2. LINUX NETWORKING (Kernel & eBPF Layer)

### Data Structures

| Data Structure | Where Used |
|---|---|
| **sk_buff (socket buffer)** | The core packet structure in Linux kernel |
| **Radix Tree (FIB trie)** | Linux FIB (Forwarding Information Base) routing lookup |
| **Hash Table** | conntrack (connection tracking), neighbor/ARP tables |
| **Red-Black Tree** | epoll fd management, timer management |
| **LRU Hash Map (eBPF)** | Per-flow state in XDP/TC programs |
| **LPM Trie (eBPF)** | IP prefix matching in eBPF programs |
| **Per-CPU Array (eBPF)** | Lock-free high-perf packet counters/stats |
| **Ring Buffer (eBPF)** | Streaming events from kernel to userspace |
| **Perf Event Array (eBPF)** | Telemetry & tracing |
| **Linked List** | Socket queues, netdev queue chains |
| **XSKMAP (eBPF)** | AF_XDP socket maps for zero-copy networking |

### Algorithms

| Algorithm | Where Used |
|---|---|
| **XDP (eXpress Data Path)** | Line-rate packet processing before sk_buff allocation |
| **eBPF JIT compilation** | Safe kernel programmability for net, security, observability |
| **NAPI (New API)** | Interrupt coalescing for high-speed NICs |
| **GRO (Generic Receive Offload)** | Merging incoming packets to reduce CPU overhead |
| **GSO / TSO (Segmentation Offload)** | Offloading TCP segmentation to NIC/software |
| **RSS (Receive Side Scaling)** | Multi-queue NIC hashing to distribute load across CPUs |
| **RPS / RFS (Receive Packet Steering)** | Software multi-core distribution of packet processing |
| **Netfilter hook chain** | iptables/nftables packet filtering pipeline |
| **Conntrack state machine** | Stateful connection tracking (TCP/UDP/ICMP) |
| **FIB lookup (trie-based)** | Kernel routing table lookup |
| **SO_REUSEPORT hashing** | Load balancing across multiple sockets |
| **TC (Traffic Control) qdisc** | Packet scheduling subsystem (HTB, FQ, FQ-CoDel) |
| **FQ-CoDel** | Active queue management; reduces bufferbloat |

---

## 🔐 3. NETWORK SECURITY

### Data Structures

| Data Structure | Where Used |
|---|---|
| **Aho-Corasick Automaton (DFA)** | Multi-pattern matching in IDS/IPS (Snort, Suricata) |
| **DFA / NFA** | Deep Packet Inspection (DPI) regex engines |
| **Bloom Filter** | IP/domain blacklist fast lookups |
| **Radix Trie / Patricia Trie** | IP blacklist/whitelist, ACL rule lookup |
| **Hash Table** | Session tracking, certificate cache, blacklist |
| **Interval Tree** | Port-range rules in firewall ACLs |
| **Merkle Tree** | Certificate Transparency logs, TLS cert validation |
| **Red-Black Tree** | Ordered session/flow management |
| **LRU Cache** | TLS session resumption cache |
| **Bitmap** | Port scan detection, flag tracking |

### Algorithms

| Algorithm | Where Used |
|---|---|
| **Aho-Corasick** | Snort, Suricata — multi-pattern payload matching |
| **Boyer-Moore-Horspool** | Fast single-pattern string matching in DPI |
| **Hyperscan (Intel)** | SIMD-accelerated regex; used in Suricata, L7 firewalls |
| **SYN Cookies** | SYN flood DDoS protection (stateless TCP handshake) |
| **Rate Limiting (Token Bucket / Sliding Window)** | DDoS mitigation, brute-force protection |
| **HMAC (SHA-256/SHA-3)** | Packet/message authentication |
| **AES-GCM / ChaCha20-Poly1305** | Symmetric encryption (TLS 1.3, IPSec, WireGuard) |
| **ECDH / X25519** | TLS 1.3 key exchange |
| **RSA / ECDSA** | Certificate signing and verification |
| **SHA-256 / SHA-3 / BLAKE2/3** | Hashing — integrity, fingerprinting |
| **TLS 1.3 Handshake** | Secure channel establishment |
| **X.509 chain validation** | Certificate path verification |
| **DNSSEC validation (chain of trust)** | DNS integrity verification |
| **Diffie-Hellman (ECDH)** | Forward-secret key exchange |
| **Port scan detection heuristics** | Stateful scan detection (threshold + time window) |
| **Anomaly detection (statistical)** | Baseline + deviation alerts in IDS/SIEM |
| **Random Early Detection (RED)** | Congestion-based DDoS backpressure |
| **BGP route validation (RPKI)** | Preventing BGP hijacking |

---

## ☁️ 4. CLOUD NETWORK SECURITY

### Data Structures

| Data Structure | Where Used |
|---|---|
| **LPM Trie (eBPF)** | Security group / pod CIDR enforcement (Cilium, Calico) |
| **Hash Map (eBPF)** | Per-flow policy enforcement in kernel |
| **Consistent Hash Ring** | Stateful LB, sticky sessions across replicas |
| **Bloom Filter** | Fast deny-list checking in WAF, CDN edge |
| **Merkle Tree** | Image signing (Docker Notary, Sigstore), supply chain |
| **CRDT** | Distributed firewall rule state (eventual consistency) |
| **Radix Trie** | VPC CIDR routing, security group IP ranges |
| **DAG (Directed Acyclic Graph)** | Policy dependency graphs (OPA/Rego, Terraform security) |
| **LRU Map** | mTLS session cache, JWT token cache |
| **Interval Tree** | Port range rules in cloud SG/NACL |

### Algorithms

| Algorithm | Where Used |
|---|---|
| **eBPF-based policy enforcement** | Cilium CNI — identity-aware L3/L4/L7 policy |
| **mTLS (mutual TLS)** | Zero Trust service-to-service auth (Istio, Linkerd, Envoy) |
| **SPIFFE/SPIRE (X.509 SVID)** | Workload identity in cloud-native zero trust |
| **JWT validation (RS256 / ES256)** | API gateway auth; stateless token verification |
| **OAuth2 / OIDC flows** | Cloud IAM, service auth |
| **RBAC / ABAC policy evaluation** | Kubernetes RBAC, AWS IAM, OPA policy decisions |
| **WireGuard (ChaCha20 + Poly1305 + X25519)** | Modern VPN used in cloud overlay networks |
| **VXLAN / Geneve encapsulation** | Overlay networking in cloud (AWS VPC, k8s CNI) |
| **BGP (with RPKI validation)** | Cloud provider peering, anti-hijack |
| **ECMP + consistent hashing** | Cloud load balancer flow distribution |
| **eBPF XDP DDoS mitigation** | Cloudflare, AWS Shield — line-rate drop before kernel |
| **Sigstore / cosign (Merkle + transparency log)** | Container image signing & verification |
| **HNSW (vector search)** | ML-based anomaly detection (cloud SIEM, GuardDuty-like) |
| **Sliding window rate limiting** | API gateways, WAF (Kong, AWS WAF, Cloudflare) |
| **TLS 1.3 with 0-RTT** | Low-latency cloud API connections (with replay protection) |
| **OPA Rego policy evaluation** | Cloud-native policy-as-code engine |
| **Certificate Transparency (Merkle)** | Public audit log for TLS certs; enforced in Chrome |

---

## 🗺️ Big Picture Map

```
LAYER              KEY DSA
─────────────────────────────────────────────────────
Hardware/NIC    →  Ring buffers, RSS hashing, offload algorithms
Linux Kernel    →  sk_buff, radix trie FIB, eBPF maps, conntrack, NAPI
Protocol Stack  →  LPM, Dijkstra/BGP, TCP CC (CUBIC/BBR), CRC
Security        →  Aho-Corasick, AES-GCM, TLS 1.3, SYN cookies
Cloud Native    →  eBPF+XDP, mTLS, SPIFFE, consistent hashing, OPA
```

---

## ⭐ The Most Critical Ones (Used Absolutely Everywhere)

| DSA | Why It's Irreplaceable |
|---|---|
| **Radix / Patricia Trie** | Every IP lookup in every router/OS |
| **Hash Table** | ARP, conntrack, flow tables — core of networking |
| **Aho-Corasick** | Every IDS/IPS/DPI engine |
| **AES-GCM + ECDH** | Every encrypted connection on the internet |
| **eBPF Maps (LPM + Hash)** | The future of all Linux net & security |
| **Consistent Hashing** | Every load balancer and cloud service |
| **Merkle Tree** | TLS cert transparency, container supply chain |
| **Token Bucket** | Every rate limiter and traffic shaper |