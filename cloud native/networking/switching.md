## Cloud Native Switching: Security-First Architecture Guide

**Summary:** Switching in cloud native spans physical underlay (datacenter fabric), overlay networks (VXLAN/Geneve), CNI implementations, and eBPF-based data planes—each layer presenting distinct security boundaries, threat surfaces, and performance tradeoffs.

---

## 1. Switching Layers in Cloud Native

### Traditional vs Cloud Native Model

```
┌─────────────────────────────────────────────────────────────────┐
│                    CLOUD NATIVE STACK                            │
├─────────────────────────────────────────────────────────────────┤
│ Application Layer (L7)                                           │
│  ├─ Service Mesh Proxy (Envoy/Linkerd) - L7 filtering          │
│  └─ mTLS, AuthZ, Rate Limiting                                  │
├─────────────────────────────────────────────────────────────────┤
│ Container Network Interface (CNI) Layer                          │
│  ├─ Policy Engine (NetworkPolicy/Calico/Cilium)                │
│  ├─ Overlay Switching (VXLAN VNI, Geneve)                      │
│  └─ Pod-to-Pod routing decisions                                │
├─────────────────────────────────────────────────────────────────┤
│ Kernel Network Stack                                             │
│  ├─ eBPF Programs (XDP, TC hooks)                               │
│  ├─ Linux Bridge / OVS / IPvlan                                 │
│  ├─ Netfilter (iptables/nftables)                               │
│  └─ Routing tables, ARP/NDP                                     │
├─────────────────────────────────────────────────────────────────┤
│ Physical/Virtual NIC                                             │
│  ├─ SR-IOV VF assignment                                        │
│  ├─ Hardware offload (TSO, checksum, RSS)                      │
│  └─ NIC-level ACLs (SmartNIC scenarios)                        │
├─────────────────────────────────────────────────────────────────┤
│ Underlay Network (Datacenter Fabric)                             │
│  ├─ Top-of-Rack (ToR) switches                                  │
│  ├─ Spine/Leaf topology                                         │
│  ├─ BGP EVPN, MPLS, or routed L3                               │
│  └─ Physical security (802.1X, MACsec)                         │
└─────────────────────────────────────────────────────────────────┘
```

**Key Insight:** Each layer performs "switching" decisions—from Ethernet frame forwarding (L2) to connection steering (L4/L7). Security boundaries exist at every transition.

---

## 2. Switching Concepts by OSI Layer

### L2 Switching (Data Link Layer)

**What it is:** MAC address-based frame forwarding within a broadcast domain.

**Cloud Native Context:**
- **Linux Bridge:** Traditional kernel bridge connecting veth pairs (pod interfaces)
- **OVS (Open vSwitch):** Software-defined switch with OpenFlow support
- **Hardware switches:** ToR switches in the physical underlay

**Security Properties:**
- Broadcast domain = security domain (ARP spoofing risk)
- MAC filtering can limit pod communication but breaks with dynamic IPs
- Layer 2 provides no encryption; relies on physical security or MACsec

**Threat Model:**
```
Attacker in same broadcast domain can:
├─ ARP spoofing → MITM pod-to-pod traffic
├─ MAC flooding → switch fails open to hub mode
├─ VLAN hopping → access isolated segments
└─ Broadcast storms → DoS

Mitigations:
├─ Overlay networks isolate L2 per tenant (VXLAN VNI)
├─ Network policies block unauthorized flows
├─ Rate limiting at switch level
└─ Pod Security Standards prevent hostNetwork
```

### L3 Switching (Network Layer)

**What it is:** IP-based routing, typically in hardware via ASIC on switches.

**Cloud Native Context:**
- **Direct routing:** BGP announces pod CIDRs (Calico, Cilium kube-router mode)
- **No overlay:** Packets routed at underlay with native performance
- **L3 VPN:** MPLS/VRF for tenant isolation in multi-tenant clusters

**Security Properties:**
- Routing policies control reachability (BGP filters)
- No broadcast domain → no ARP-based attacks
- Encryption requires overlay (WireGuard, IPsec) or application-level TLS

**Tradeoff:**
- **Pro:** Line-rate performance, no encap overhead
- **Con:** Requires physical network integration (BGP peering, IP allocation)

### L4-L7 Switching (Transport/Application Layer)

**What it is:** Connection proxying, load balancing based on ports/URLs/headers.

**Cloud Native Context:**
- **kube-proxy:** iptables/IPVS NAT for Service ClusterIPs
- **Service mesh data plane:** Envoy/Linkerd sidecars intercept TCP connections
- **Ingress controllers:** HAProxy/NGINX for HTTP routing

**Security Properties:**
- Connection tracking enables stateful firewalling
- L7 proxies terminate connections → can inspect/modify traffic
- mTLS enforcement point (service mesh)

**Performance Impact:**
```
Path without proxy:  Pod A → Pod B
    ├─ 1 hop, kernel bypass possible (eBPF sockmap)
    └─ ~10-20 μs latency

Path with L7 proxy: Pod A → Sidecar A → Sidecar B → Pod B
    ├─ 3 context switches, TLS termination 2x
    └─ ~500 μs - 2ms latency (justify with security requirements)
```

---

## 3. CNI Switching Architectures

### Overlay vs Underlay Model

```
┌─────────────────────────────────────────────────────────────────┐
│                      OVERLAY (VXLAN)                             │
├─────────────────────────────────────────────────────────────────┤
│  Pod A (10.244.1.5)              Pod B (10.244.2.10)            │
│       │                                 │                        │
│       │ veth0                           │ veth0                  │
│       ├──────► cni0 bridge              ├──────► cni0 bridge    │
│       │                                 │                        │
│       │ VXLAN encap                     │ VXLAN decap            │
│       │ [Outer: 192.168.1.10 → 192.168.1.11]                    │
│       │ [Inner: 10.244.1.5 → 10.244.2.10]                       │
│       │                                 │                        │
│       └────────► Physical NIC ──────────┘                        │
│                        │                                         │
│                  Underlay Router                                 │
│         (sees only 192.168.1.x addresses)                        │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    UNDERLAY (Direct Routing)                     │
├─────────────────────────────────────────────────────────────────┤
│  Pod A (10.244.1.5)              Pod B (10.244.2.10)            │
│       │                                 │                        │
│       │ veth0                           │ veth0                  │
│       ├──────► Host routing table       ├──────► Host routing   │
│       │                                 │                        │
│       │ No encap - native IP            │                        │
│       │ [10.244.1.5 → 10.244.2.10]      │                        │
│       │                                 │                        │
│       └────────► Physical NIC ──────────┘                        │
│                        │                                         │
│                  ToR Switch (BGP)                                │
│         Knows route: 10.244.1.0/24 via Node1                    │
│                     10.244.2.0/24 via Node2                     │
└─────────────────────────────────────────────────────────────────┘
```

### Major CNI Implementations

**Calico:**
- Default: BGP + IP-in-IP encap (fallback when BGP not possible)
- Security: NetworkPolicy via iptables or eBPF, per-node/pod policies
- Use case: Multi-region with selective encryption

**Cilium:**
- eBPF-based switching at TC/XDP hooks
- VXLAN/Geneve overlay or native routing
- Security: Identity-based policies (not IP-based), L7 aware
- Use case: High-performance microsegmentation

**Flannel:**
- Simple VXLAN overlay with etcd backend
- No built-in policy enforcement (combine with Calico)
- Use case: Simplicity over features

**Weave:**
- Mesh overlay with optional IPsec encryption
- Slower than Cilium/Calico but simpler ops
- Use case: Small clusters, easy encryption

---

## 4. eBPF-Based Switching Security Model

### Why eBPF Matters

Traditional iptables path:
```
Packet arrives → Netfilter hooks → Iterate rules → Accept/Drop
  └─ O(n) complexity, 10K+ rules = significant latency
```

eBPF path:
```
Packet arrives → XDP/TC hook → BPF map lookup → Action
  └─ O(1) hash lookup, bypasses full netfilter stack
```

**Architecture:**

```
┌────────────────────────────────────────────────────────────────┐
│  User Space                                                     │
│  ├─ Cilium Agent                                                │
│  │   ├─ Watches K8s NetworkPolicy                              │
│  │   ├─ Compiles eBPF programs                                 │
│  │   └─ Updates BPF maps (endpoints, policies)                 │
│  │                                                              │
│  └─ BPF maps (shared memory)                                   │
│      ├─ cilium_policy_v4 (IP→Policy ID)                        │
│      ├─ cilium_lxc (Pod ID→SecurityIdentity)                   │
│      └─ cilium_ipcache (IP→Identity)                           │
├────────────────────────────────────────────────────────────────┤
│  Kernel Space                                                   │
│  ├─ TC Ingress (veth host side)                                │
│  │   ├─ BPF program attached                                   │
│  │   ├─ Lookup: src_IP → Identity                              │
│  │   ├─ Lookup: (src_Identity, dst_Identity) → Allow/Deny      │
│  │   └─ Action: Pass to pod or DROP                            │
│  │                                                              │
│  ├─ XDP (physical NIC) - optional                              │
│  │   └─ Drop malicious traffic before sk_buff allocation       │
│  │                                                              │
│  └─ sockmap (L4 switching)                                     │
│      └─ Redirect socket-to-socket (bypass TCP/IP stack)        │
└────────────────────────────────────────────────────────────────┘
```

**Security Advantages:**
1. **Kernel-enforced:** Policies applied before packets reach containers
2. **Immutable at runtime:** BPF verifier ensures safety
3. **Identity-based:** Survives IP changes (pod reschedules)
4. **L7 visibility:** Can parse HTTP/gRPC/Kafka protocols in kernel

**Threat: eBPF Privilege Escalation**
- Loading BPF requires CAP_BPF or CAP_SYS_ADMIN
- Malicious BPF program could read arbitrary kernel memory
- **Mitigation:** Restrict BPF loading to CNI agents only, use Seccomp to block bpf() syscall in containers

---

## 5. Network Policy Switching Logic

### How NetworkPolicy Affects Switching

```
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
  podSelector: {app: database}
  ingress:
  - from:
    - podSelector: {app: backend}
    ports: [5432]
```

**Switching decision tree:**

```
Packet arrives at node hosting database pod
  │
  ├─ Source IP: 10.244.3.15
  ├─ Dest IP: 10.244.1.20 (database pod)
  ├─ Dest Port: 5432
  │
  ▼
Check 1: Dest IP in local pods?
  ├─ Yes → Continue
  └─ No → Route to other node
  │
  ▼
Check 2: Any NetworkPolicy selects dest pod (app=database)?
  ├─ Yes → Enforce policy
  └─ No → Allow all (default)
  │
  ▼
Check 3: Policy has ingress rules?
  ├─ Yes → Match source against rules
  └─ No → DENY all ingress (default deny)
  │
  ▼
Check 4: Source pod has label app=backend?
  ├─ Yes → Check port
  │   └─ Port 5432? → ALLOW
  └─ No → DROP
```

**Default Deny Pattern:**
```
Empty NetworkPolicy = Deny all
  + Explicit ingress rule = Allow only matched
  + No egress rules = Allow all egress (implicit)

Security best practice: Start with deny-all, add allowlist rules
```

**Implementation Variations:**
- **Calico:** Creates iptables chains per policy, ~100 rules/policy
- **Cilium:** Compiles policies into eBPF, constant-time lookup
- **Antrea:** OVS flow rules with conjunction matching

---

## 6. Service Mesh Data Plane Switching

### Sidecar vs Ambient Models

**Sidecar (Istio/Linkerd classic):**
```
┌────────────────────────────────────────────────────┐
│  Pod                                                │
│  ┌──────────────┐        ┌──────────────┐          │
│  │ Application  │        │  Envoy Proxy │          │
│  │ Container    │◄──────►│  (sidecar)   │          │
│  │ :8080        │  lo    │  :15001      │          │
│  └──────────────┘        └───────┬──────┘          │
│                                  │                  │
│                                  │ veth0            │
└──────────────────────────────────┼──────────────────┘
                                   │
                          iptables REDIRECT
                          dst=ClusterIP → 127.0.0.1:15001
                                   │
                                   ▼
                            Envoy does L7 switching:
                            ├─ mTLS termination
                            ├─ AuthZ check
                            ├─ Load balancing
                            └─ Forward to actual backend
```

**Ambient (Istio 1.15+):**
```
┌────────────────────────────────────────────────────┐
│  Pod (no sidecar)                                   │
│  ┌──────────────┐                                   │
│  │ Application  │                                   │
│  │ :8080        │                                   │
│  └──────┬───────┘                                   │
│         │ veth0                                     │
└─────────┼─────────────────────────────────────────┘
          │
          │ eBPF redirect (sockmap)
          │
          ▼
┌──────────────────────────────────┐
│  ztunnel (per-node daemonset)    │
│  ├─ L4 proxy (mTLS only)         │
│  └─ No L7 parsing                │
└──────────────────────────────────┘
          │
  L7 policies? Send to waypoint proxy
          │
          ▼
┌──────────────────────────────────┐
│  Waypoint Proxy (shared Envoy)   │
│  ├─ HTTP filtering               │
│  └─ Per-namespace or per-service │
└──────────────────────────────────┘
```

**Security Tradeoffs:**
- **Sidecar:** Strong isolation (per-pod proxy), higher resource cost
- **Ambient:** Lower overhead, but shared L7 proxy = cross-tenant risk if waypoint compromised

---

## 7. Threat Model: Switching Attacks

### Attack Surface by Layer

```
┌─────────────────────────────────────────────────────────────┐
│ ATTACK                    │ LAYER   │ MITIGATION            │
├─────────────────────────────────────────────────────────────┤
│ ARP Spoofing              │ L2      │ Overlay networks      │
│ MAC Flooding              │ L2      │ Port security         │
│ VLAN Hopping              │ L2      │ Disable DTP/802.1Q    │
├─────────────────────────────────────────────────────────────┤
│ IP Spoofing               │ L3      │ BCP38 egress filter   │
│ Route Hijacking (BGP)     │ L3      │ RPKI, BGP sec         │
│ ICMP Redirect             │ L3      │ Drop redirects        │
├─────────────────────────────────────────────────────────────┤
│ SYN Flood                 │ L4      │ SYN cookies, rate lim │
│ Connection Hijacking      │ L4      │ TCP seq randomization │
│ Port Scanning             │ L4      │ NetworkPolicy         │
├─────────────────────────────────────────────────────────────┤
│ HTTP Request Smuggling    │ L7      │ Strict parsing (Envoy)│
│ Protocol Confusion        │ L7      │ TLS enforcement       │
│ DoS via malformed req     │ L7      │ Request validation    │
├─────────────────────────────────────────────────────────────┤
│ CNI Plugin Compromise     │ Control │ Verify binary sigs    │
│ NetworkPolicy Bypass      │ Control │ Admission webhooks    │
│ BPF Program Injection     │ Kernel  │ CAP_BPF restrictions  │
└─────────────────────────────────────────────────────────────┘
```

### East-West Attack Scenarios

**Scenario 1: Compromised Pod → Lateral Movement**
```
Attacker gains shell in web pod
  ├─ Scans 10.244.0.0/16 (pod CIDR)
  ├─ Finds database pod without NetworkPolicy
  ├─ Dumps credentials
  └─ Exfiltrates via allowed egress

Prevention:
  ├─ Default-deny NetworkPolicy
  ├─ Egress filtering (only allow DNS, known APIs)
  └─ Runtime detection (Falco: unexpected connections)
```

**Scenario 2: Node Compromise → Pod Sniffing**
```
Attacker has root on node
  ├─ Attaches tcpdump to cni0 bridge
  ├─ Captures pod-to-pod traffic (plaintext!)
  └─ Extracts secrets from HTTP headers

Prevention:
  ├─ Overlay encryption (WireGuard, IPsec)
  ├─ Service mesh mTLS (encrypts even on same node)
  └─ Node attestation (TPM-based)
```

---

## 8. Performance & Security Tradeoffs

### Switching Latency by Method

```
Method                    | Latency  | Security           | CPU
─────────────────────────────────────────────────────────────
Direct veth routing       | 5 μs     | None               | Minimal
Linux bridge              | 10 μs    | L2 isolation       | Low
VXLAN overlay             | 25 μs    | Tenant isolation   | Moderate
IPsec encryption          | 50 μs    | Confidentiality    | High
eBPF redirect (sockmap)   | 2 μs     | Policy-aware       | Low
Sidecar proxy (no mTLS)   | 500 μs   | L7 inspection      | Very high
Sidecar proxy (mTLS)      | 1-2 ms   | AuthN/AuthZ/Crypto | Very high
```

**Decision Matrix:**
- **Low latency required (<100 μs):** eBPF direct routing, no service mesh
- **Multi-tenancy:** VXLAN with NetworkPolicy
- **Compliance (encryption at rest & transit):** IPsec overlay + mTLS mesh
- **Zero Trust:** Service mesh with mTLS, accept latency cost

---

## 9. Failure Modes & Resilience

### CNI Plugin Crashes

```
Normal operation:
  kubelet → CNI plugin → Setup pod network → Pod running

CNI plugin crash:
  ├─ Existing pods: Continue working (network already configured)
  ├─ New pods: Stuck in ContainerCreating
  └─ Deleted pods: Orphaned veth pairs (memory leak)

Detection:
  ├─ CNI plugin health endpoint (/healthz)
  ├─ Pod creation latency spikes
  └─ Unreachable pods (if plugin manages routes)

Mitigation:
  ├─ DaemonSet with restartPolicy=Always
  ├─ Init container preloads BPF maps
  └─ Fail-open vs fail-closed policy (define in advance)
```

### NetworkPolicy Consistency

```
Problem: Policy replication lag
  ├─ New pod scheduled
  ├─ Policy not yet applied to all nodes
  └─ Brief window where traffic allowed/denied incorrectly

Timeline:
  T+0ms: Pod created on Node A
  T+50ms: CNI notices, updates local policy
  T+200ms: Controller syncs policy to other nodes (etcd lag)
  T+500ms: Eventual consistency achieved

Risk window: 0-500ms
  └─ Attacker could connect if they detect pod IP immediately

Mitigation:
  ├─ Delay pod readiness until policy sync confirmed
  ├─ Default-deny at admission time (enforce before scheduling)
  └─ Use identity-based policies (Cilium) - no IP dependency
```

---

## 10. Alternatives & Justification

### When NOT to Use Overlay Networks

**Use underlay (direct routing) if:**
- Physical network is fully controlled (on-prem datacenter)
- BGP integration is feasible (network team cooperation)
- Maximum performance required (trading ops complexity for speed)

**Use overlay (VXLAN/Geneve) if:**
- Cloud environment with limited network control (AWS, Azure)
- Need tenant isolation without physical VLANs
- Simplified ops (no BGP, works anywhere)

### When NOT to Use Service Mesh

**Skip service mesh if:**
- All apps are trusted (single-tenant cluster)
- Latency budget <100 μs (financial trading, HPC)
- Apps already do mTLS natively (Go gRPC with certs)

**Use service mesh if:**
- Zero Trust mandate (encrypt all traffic)
- Need L7 metrics per-service (Prometheus labels)
- Gradual TLS migration (mesh handles certificates)

---

## 11. Next 3 Steps

1. **Benchmark current CNI performance:**
   - Deploy netperf pods, measure pod-to-pod latency baseline
   - Capture metrics: p50/p99 latency, throughput, packet loss
   - Document acceptable degradation for security features

2. **Threat model workshop:**
   - Map all network paths (pod→pod, pod→external, ingress→service)
   - Identify crown jewels (database pods, auth services)
   - Design NetworkPolicies: default-deny ingress/egress, explicit allowlist

3. **Test failover scenarios:**
   - Kill CNI plugin DaemonSet, observe pod creation behavior
   - Inject iptables rule to drop packets, verify monitoring alerts
   - Simulate node compromise: attempt tcpdump, verify encryption prevents sniffing

---

## Key References

- **CNI Spec:** github.com/containernetworking/cni/blob/main/SPEC.md
- **Kubernetes NetworkPolicy:** k8s.io/docs/concepts/services-networking/network-policies
- **Cilium Architecture:** docs.cilium.io/en/stable/network/concepts/routing/
- **Calico Security:** projectcalico.docs.tigera.io/security/
- **eBPF Docs:** ebpf.io/what-is-ebpf/
- **NIST Zero Trust:** csrc.nist.gov/publications/detail/sp/800-207/final

---

**Assumptions justified:** Cloud-native switching primarily concerns K8s pod networking (not bare-metal L2 switching). Security focus assumes multi-tenant or Zero Trust requirements. Performance numbers based on 25GbE NICs, modern kernels (5.10+), and x86_64 architecture.