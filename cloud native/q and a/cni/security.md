# ☁️ 100 Senior-Level Cloud CNI Security Interview Questions & Answers

> **Scope:** Container Network Interface (CNI) Security, Kubernetes Networking, Zero Trust, eBPF, mTLS, NetworkPolicy, Service Mesh, Cloud Provider CNI Plugins, Runtime Security, and Supply Chain.

---

## 📋 Table of Contents

1. [CNI Fundamentals & Architecture](#section-1-cni-fundamentals--architecture) — Q1–Q10
2. [Kubernetes NetworkPolicy Deep Dive](#section-2-kubernetes-networkpolicy-deep-dive) — Q11–Q20
3. [Service Mesh & mTLS Security](#section-3-service-mesh--mtls-security) — Q21–Q30
4. [eBPF-Based Security & Observability](#section-4-ebpf-based-security--observability) — Q31–Q40
5. [Cloud Provider CNI Plugins](#section-5-cloud-provider-cni-plugins) — Q41–Q50
6. [Zero Trust Networking in Kubernetes](#section-6-zero-trust-networking-in-kubernetes) — Q51–Q60
7. [Runtime & Pod Security](#section-7-runtime--pod-security) — Q61–Q70
8. [Network Observability & Threat Detection](#section-8-network-observability--threat-detection) — Q71–Q80
9. [Supply Chain & CNI Plugin Security](#section-9-supply-chain--cni-plugin-security) — Q81–Q90
10. [Advanced Attack Vectors & Hardening](#section-10-advanced-attack-vectors--hardening) — Q91–Q100

---

## Section 1: CNI Fundamentals & Architecture

---

### Q1. What is CNI, and how does it fit into the Kubernetes networking model?

**Answer:**

**CNI (Container Network Interface)** is a specification and a set of libraries for configuring network interfaces in Linux containers. It is a CNCF project originally created by CoreOS and Google. CNI defines a simple contract between a container runtime and a network plugin.

```
KUBERNETES NETWORKING MODEL
============================================================

  +-----------------------------------------------------------+
  | Kubernetes Node                                           |
  |                                                           |
  |  +-------------+     calls      +---------------------+  |
  |  | kubelet     |--------------->| CNI Plugin Binary   |  |
  |  | (container  |  ADD/DEL/CHECK | (e.g., calico,      |  |
  |  |  runtime)   |  commands      |  cilium, flannel)   |  |
  |  +------+------+                +----------+----------+  |
  |         |                                  |              |
  |         | creates                          | configures   |
  |         v                                  v              |
  |  +-------------+                 +-------------------+    |
  |  | Container   |<================| veth pair, bridge,|    |
  |  | (Pod netns) |  network conn.  | overlay, routes   |    |
  |  +-------------+                 +-------------------+    |
  +-----------------------------------------------------------+

CNI Contract:
  Input  → { ContainerID, Netns, IfName, Config JSON }
  Output → { IP address, Routes, DNS }
```

**The Kubernetes Networking Requirements (must satisfy all four):**

1. Every Pod gets its own unique IP address
2. Pods on the same node can communicate without NAT
3. Pods on different nodes can communicate without NAT
4. The IP a Pod sees for itself is the same IP others use to reach it

**CNI plugin invocation flow:**

```
kubelet detects new Pod
        |
        v
reads /etc/cni/net.d/*.conf
        |
        v
executes /opt/cni/bin/<plugin>
        |
        v
plugin sets up network namespace (veth pairs, IP assignment, routes)
        |
        v
returns JSON result to kubelet
        |
        v
Pod is network-ready
```

**Security Relevance:** CNI plugins operate with root or CAP_NET_ADMIN privileges. A compromised or malicious CNI binary can intercept all pod traffic, reroute flows, or bypass NetworkPolicy enforcement entirely.

---

### Q2. Explain the difference between overlay and underlay CNI networking modes, and the security trade-offs of each.

**Answer:**

**Underlay Networking (Routable/Native):**
The pod IP is directly routable on the physical network — no encapsulation.

```
UNDERLAY MODE
=============================================================
  Node A (10.0.1.10)          Node B (10.0.2.10)
  Pod IP: 192.168.1.5          Pod IP: 192.168.2.8

  +--[Pod]--+                  +--[Pod]--+
  |192.168.1.5|                |192.168.2.8|
  +-----+---+                  +-----+---+
        |                            |
  [Node eth0]--[Physical Router]--[Node eth0]
        |                            |
   Router knows: 192.168.1.0/24 → 10.0.1.10
                 192.168.2.0/24 → 10.0.2.10
```

**Overlay Networking (Encapsulated):**
Pod IPs are wrapped inside node-level packets (VXLAN, Geneve, IP-in-IP).

```
OVERLAY MODE (VXLAN)
=============================================================
  Node A (10.0.1.10)          Node B (10.0.2.10)
  Pod IP: 10.244.0.5           Pod IP: 10.244.1.8

  [Pod Packet: src=10.244.0.5 dst=10.244.1.8]
        |
  VXLAN Encapsulation:
  [Outer: src=10.0.1.10 dst=10.0.2.10 | Inner Pod Packet]
        |
  [Physical Network sees ONLY outer UDP:4789]
        |
  Node B decapsulates → delivers inner packet to Pod
```

**Security Trade-offs:**

| Dimension              | Underlay                        | Overlay                          |
|------------------------|----------------------------------|----------------------------------|
| Traffic Visibility     | Pod IPs visible to physical net  | Pod IPs hidden inside tunnel     |
| Encryption             | Requires separate IPsec/WireGuard| Can encrypt tunnel (WireGuard)   |
| Attack Surface         | Network can target Pod IPs       | Outer packet masking              |
| Performance            | Lower latency, no encap overhead | ~5-15% overhead from encapsulation|
| Multi-tenant Risk      | Pod IPs can escape VLAN boundary | Tunnel boundaries enforce isolation|
| Egress Policy          | Enforce at router/firewall       | Must enforce at node level        |

**Senior Insight:** In multi-tenant clusters, overlay mode with WireGuard encryption (Cilium/Calico support this) is preferred because even if an attacker captures packets on the physical network, they see encrypted tunnels, not pod-level payloads.

---

### Q3. What is the CNI plugin chain, and how can a malicious chained plugin attack be executed?

**Answer:**

**CNI Chaining** allows multiple plugins to run in sequence — each adding capabilities (IPAM, bandwidth limiting, firewall rules). The configuration uses a `plugins` array in the CNI config JSON.

```
CNI PLUGIN CHAIN EXECUTION
=============================================================

  /etc/cni/net.d/10-flannel.conflist:
  {
    "cniVersion": "0.3.1",
    "plugins": [
      { "type": "flannel" },          <-- 1st: assigns IP, sets up overlay
      { "type": "portmap" },          <-- 2nd: handles hostPort mappings
      { "type": "bandwidth" }         <-- 3rd: applies traffic shaping
    ]
  }

  Execution Order:
  ADD:  flannel → portmap → bandwidth   (left to right)
  DEL:  bandwidth → portmap → flannel   (right to left)

  Each plugin receives prevResult from the previous plugin
  and passes its own result forward.
```

**Malicious Chained Plugin Attack Vector:**

```
ATTACK SCENARIO: Rogue Plugin Injection
=============================================================

  Attacker gains write access to /etc/cni/net.d/
  (e.g., via node compromise, misconfigured RBAC, or supply chain)

  Injects:
  {
    "type": "legit-plugin"
  },
  {
    "type": "malicious-sniffer"     <-- inserted between plugins
  }

  What the malicious plugin can do:
  ┌─────────────────────────────────────────────────┐
  │ 1. Log all IP assignments (pod IP mapping)      │
  │ 2. Insert iptables REDIRECT rule → mirror traffic│
  │ 3. Call C2 server with env vars / secrets       │
  │ 4. Return fake prevResult to confuse next plugin│
  │ 5. Block network for specific pods (DoS)        │
  └─────────────────────────────────────────────────┘
```

**Defenses:**

- Use admission control to restrict DaemonSet access to `/etc/cni/`
- Apply file integrity monitoring (FIM) on CNI config directories
- Use a read-only filesystem for node CNI config via Kubernetes node hardening
- Validate CNI plugin binaries with cryptographic checksums on boot (SLSA / in-toto attestation)
- Restrict `hostPath` mounts in Pod Security Standards

---

### Q4. How does IPAM (IP Address Management) work in CNI, and what are the security implications of IPAM misconfiguration?

**Answer:**

**IPAM** is responsible for assigning IP addresses to pods. CNI plugins delegate to an IPAM plugin which manages IP allocation from a defined pool.

```
IPAM WORKFLOW
=============================================================

  CNI Config:
  {
    "ipam": {
      "type": "host-local",
      "ranges": [[{"subnet": "10.88.0.0/16"}]],
      "dataDir": "/var/lib/cni/networks"
    }
  }

  Allocation Process:
  ┌─────────────────────────────────────────────────────┐
  │  1. IPAM plugin reads subnet config                 │
  │  2. Scans /var/lib/cni/networks/<net-name>/         │
  │     (files named by IP = lock mechanism)            │
  │  3. Finds next available IP                         │
  │  4. Creates file: /var/lib/cni/networks/k8s/10.88.0.5│
  │     containing ContainerID                         │
  │  5. Returns IP to CNI caller                        │
  └─────────────────────────────────────────────────────┘

  Deallocation: File is deleted on CNI DEL command
```

**IPAM Types and Their Risks:**

| IPAM Type   | Mechanism                    | Security Risk                              |
|-------------|------------------------------|--------------------------------------------|
| host-local  | File-based per-node          | Files world-readable; IP exhaustion DoS    |
| dhcp        | DHCP server assignment       | Rogue DHCP server attack; IP spoofing      |
| calico-ipam | etcd/datastore backed        | etcd compromise → IP routing manipulation  |
| AWS VPC CNI | ENI attachment from AWS API  | IAM role escalation; IP exhaustion on ENI  |
| whereabouts | CRD-based across cluster     | CRD RBAC misconfiguration; stale IPs       |

**Critical Security Implications:**

1. **IP Exhaustion Attack:** An attacker pod rapidly spawns containers, consuming the IPAM pool, causing denial-of-service for legitimate workloads.

2. **IP Reuse Without Cleanup:** If a pod is force-deleted, the IPAM file may not be cleaned up. The next pod gets the same IP — stale network policies may apply incorrectly.

3. **DHCP Spoofing:** With `dhcp` IPAM, if an attacker runs a rogue DHCP server on the pod network, pods can be assigned wrong gateways (MITM).

4. **Audit Trail Loss:** `host-local` IPAM has no central audit log. Connecting Pod IP → ContainerID → Pod name requires correlation from kubelet logs and CNI state files.

---

### Q5. Explain how Calico implements NetworkPolicy enforcement — what kernel mechanisms does it use?

**Answer:**

Calico enforces NetworkPolicy using **iptables** (legacy), **eBPF** (modern), and **nftables** (upcoming). The architecture involves multiple components working in concert.

```
CALICO ARCHITECTURE (iptables mode)
=============================================================

  +----------------------------------------------------+
  | Kubernetes API Server                              |
  |  NetworkPolicy objects                             |
  +--------------------+------------------------------ +
                        |
              watches via Watch API
                        |
                        v
  +----------------------------------------------------+
  | calico-node (DaemonSet on every node)             |
  |                                                    |
  |  Felix (Policy Agent)                             |
  |  ┌──────────────────────────────────────────────┐ |
  |  │ Reads NetworkPolicy from API server          │ |
  |  │ Translates to iptables rules                 │ |
  |  │ Programs iptables chains on local node       │ |
  |  └──────────────────────────────────────────────┘ |
  |                                                    |
  |  BIRD (BGP Agent) — for underlay mode             |
  |  ┌──────────────────────────────────────────────┐ |
  |  │ Advertises pod CIDRs via BGP                 │ |
  |  │ Learns routes from other nodes               │ |
  |  └──────────────────────────────────────────────┘ |
  +----------------------------------------------------+

  iptables Chain Hierarchy for a Pod:
  ┌──────────────────────────────────────────────────────┐
  │  PREROUTING → cali-PREROUTING                        │
  │  FORWARD    → cali-FORWARD                           │
  │               → cali-from-wl-dispatch                │
  │                  → cali-fw-<interface>               │
  │                     → (ingress rules per NetworkPolicy)│
  │               → cali-to-wl-dispatch                  │
  │                  → cali-tw-<interface>               │
  │                     → (egress rules per NetworkPolicy)│
  └──────────────────────────────────────────────────────┘
```

**iptables vs eBPF Mode Comparison:**

```
iptables MODE:
  Packet → iptables rules → linear rule scan → accept/drop
  Scalability: O(n) rule lookup — degrades at 10k+ rules
  Visibility: Limited (iptables LOG target, conntrack)

eBPF MODE:
  Packet → XDP/TC hook → eBPF map lookup → accept/drop
  Scalability: O(1) hash map lookup — consistent at scale
  Visibility: High (kprobes, perf events, custom maps)
```

**Security Audit Points:**
- Verify Felix logs for policy translation errors
- Check `cali-FORWARD DROP` is the default (deny-all baseline)
- Ensure Calico's etcd/API credentials are rotated and scoped
- Monitor `felix_int_dataplane_failures_total` Prometheus metric

---

### Q6. What is the difference between Kubernetes NetworkPolicy and Calico GlobalNetworkPolicy? When do you need each?

**Answer:**

```
SCOPE COMPARISON
=============================================================

  Kubernetes NetworkPolicy:
  ┌────────────────────────────────────────────────────┐
  │  Namespace-scoped                                  │
  │  Applies only within a single namespace            │
  │  Cannot reference Pods across namespaces by label  │
  │    (only by namespaceSelector)                     │
  │  Cannot match Nodes                                │
  │  Cannot set Deny rules (implicit deny only)        │
  │  Not cluster-admin resource                        │
  └────────────────────────────────────────────────────┘

  Calico GlobalNetworkPolicy:
  ┌────────────────────────────────────────────────────┐
  │  Cluster-scoped CRD (GlobalNetworkPolicy)          │
  │  Applies across ALL namespaces                     │
  │  Can match Pods, Nodes, HostEndpoints              │
  │  Supports explicit Deny action (not just implicit) │
  │  Supports ordering via `order` field               │
  │  Requires cluster-admin to create                  │
  │  Supports GlobalNetworkSet (IP block sets)         │
  └────────────────────────────────────────────────────┘
```

**When to Use Each:**

| Use Case                                          | Use                          |
|---------------------------------------------------|------------------------------|
| Namespace-level isolation between teams           | Kubernetes NetworkPolicy      |
| Block all egress to internet cluster-wide         | Calico GlobalNetworkPolicy    |
| Deny a specific IP range for all pods everywhere  | Calico GlobalNetworkSet + GNP |
| Allow kube-system DNS to all pods                 | Calico GlobalNetworkPolicy    |
| Allow app A to talk to app B in same namespace    | Kubernetes NetworkPolicy      |
| Protect node's host network from pod access       | Calico HostEndpoint Policy    |

**Practical Example — Cluster-wide Egress Deny:**

```yaml
# Calico GlobalNetworkPolicy — deny all egress to RFC1918 from any pod
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: deny-private-egress
spec:
  order: 100
  selector: all()
  types:
    - Egress
  egress:
    - action: Deny
      destination:
        nets:
          - 10.0.0.0/8
          - 172.16.0.0/12
          - 192.168.0.0/16
```

**Senior Insight:** Use `order` carefully — lower numbers have higher priority. A GNP with `order: 1` blocks everything; a GNP with `order: 100` is evaluated after. Always maintain a "baseline deny" at a high order number and specific "allow" rules at lower order numbers.

---

### Q7. How does Cilium's eBPF-based identity model differ from IP-based policy enforcement, and why does it matter for security?

**Answer:**

**Traditional IP-Based Enforcement:**
```
IP-BASED MODEL (iptables/Calico legacy)
=============================================================
  Pod A (10.88.1.5) → send to Pod B (10.88.2.10)
  
  Rule: allow src=10.88.1.5 dst=10.88.2.10

  Problems:
  ┌─────────────────────────────────────────────────────┐
  │ 1. Pod restarts → IP changes → rule breaks         │
  │ 2. IP reuse → old policy may apply to new pod      │
  │ 3. Requires conntrack + IPset updates on every     │
  │    pod churn event                                  │
  │ 4. No cryptographic proof of identity              │
  └─────────────────────────────────────────────────────┘
```

**Cilium Identity-Based Model:**
```
CILIUM IDENTITY MODEL (eBPF)
=============================================================
  Every Endpoint (Pod) gets a numeric Security Identity
  based on its Labels hash.

  Labels: { app=frontend, env=prod, team=payments }
         ↓
  SHA hash → Identity ID: 42819

  Identity is stored in eBPF map:
  ┌─────────────────────────────────────────────────────┐
  │  BPF Map: identity_map                             │
  │  Key: Identity ID (42819)                          │
  │  Value: { policy_map_ptr, allowed_identities[] }   │
  └─────────────────────────────────────────────────────┘

  Packet forwarding:
  Pod A (ID=42819) → sends packet → eBPF hook intercepts
  eBPF reads src identity (from sock cookie or ipcache map)
  Lookups policy_map: is identity 42819 allowed to dst?
  YES → forward | NO → drop
  
  NO IP LOOKUP NEEDED — purely label/identity based
```

**Why It Matters for Security:**

| Dimension                  | IP-Based                     | Identity-Based (Cilium)            |
|----------------------------|------------------------------|------------------------------------|
| Pod restart resilience     | Policy breaks on IP change    | Identity recalculated from labels  |
| IP spoofing defense        | Attacker can spoof src IP     | Identity checked via kernel context|
| Policy granularity         | L3 only (IP/port)             | L3, L4, L7 (HTTP path, gRPC method)|
| CIDR policy latency        | IPset flush on update         | eBPF map atomic update (ns latency)|
| Audit log quality          | IPs only                      | Identity → labels → Pod name       |

**L7 Policy Example (Cilium-specific):**

```yaml
# Only allow GET /api/health — block all other HTTP
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-health-only
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
          rules:
            http:
              - method: GET
                path: /api/health
```

---

### Q8. What happens at the kernel level when a Kubernetes NetworkPolicy is applied — trace the full packet path?

**Answer:**

```
FULL PACKET PATH WITH NETWORKPOLICY (iptables/Calico)
=============================================================

  Pod A (10.244.1.5) wants to reach Pod B (10.244.2.8):

  STEP 1: Pod A writes to socket
          → kernel TCP/IP stack
          → packet enters veth pair (eth0 inside pod ↔ caliXXX on node)

  STEP 2: Packet hits NODE iptables (PREROUTING chain)
          ┌─────────────────────────────────────────┐
          │ cali-PREROUTING                         │
          │   → mark conntrack NEW connections      │
          │   → set MARK for policy processing      │
          └─────────────────────────────────────────┘

  STEP 3: Routing decision
          → kernel FIB lookup: 10.244.2.8 via tunl0 (IPIP overlay)
             OR via eth0 with BGP route (underlay)

  STEP 4: FORWARD chain (for inter-pod traffic)
          ┌─────────────────────────────────────────────────────┐
          │ cali-FORWARD                                        │
          │   → cali-from-wl-dispatch (from workload)          │
          │       → cali-fw-caliXXX (interface-specific)       │
          │           → EGRESS policy rules for Pod A          │
          │               MATCH: app=frontend allows port 8080  │
          │               → ACCEPT                             │
          │   → cali-to-wl-dispatch (to workload, on dest node)│
          │       → cali-tw-caliYYY                            │
          │           → INGRESS policy rules for Pod B         │
          │               MATCH: ingress from app=frontend OK  │
          │               → ACCEPT                             │
          └─────────────────────────────────────────────────────┘

  STEP 5: Packet sent via overlay (IPIP/VXLAN) or routed
          → encapsulated: outer src=NodeA IP, dst=NodeB IP
          → arrives Node B

  STEP 6: Node B decapsulates → PREROUTING again
          → FORWARD → cali-to-wl → policy check → Pod B veth

  STEP 7: Pod B receives packet on eth0 (10.244.2.8)

  DEFAULT: If no policy matches → cali-FORWARD DROP
           (Calico's default deny at chain end)
```

**Key Security Observation:** Kubernetes NetworkPolicy is **additive** — if no NetworkPolicy selects a pod, the pod is **non-isolated** (all traffic allowed). This is the most common misconfiguration — teams assume absence of policy = secure, but it's the opposite.

---

### Q9. Explain the host network namespace security risk in Kubernetes — how can a pod accessing hostNetwork exploit the cluster?

**Answer:**

```
HOST NETWORK NAMESPACE ATTACK
=============================================================

  Normal Pod:
  ┌────────────────────────────────────────────┐
  │  Pod Namespace                             │
  │  eth0: 10.244.1.5  (isolated)             │
  │  Can only see pod-level network            │
  └────────────────────────────────────────────┘

  hostNetwork: true Pod:
  ┌────────────────────────────────────────────┐
  │  SHARES Node's Network Namespace           │
  │  Sees: eth0 (node IP), lo, tunl0, caliXXX │
  │  Can bind to ANY port on node IP           │
  │  Can sniff node-level traffic (tcpdump)    │
  │  Can reach 127.0.0.1:10250 (kubelet API)  │
  │  Can reach 127.0.0.1:2379 (etcd if local) │
  └────────────────────────────────────────────┘

  Attack Chain:
  ┌─────────────────────────────────────────────────────┐
  │  1. Attacker deploys pod with hostNetwork: true     │
  │  2. Pod sees node's lo interface                    │
  │  3. curl http://127.0.0.1:10250/pods               │
  │     → kubelet read-only API (pre-1.16, no auth)    │
  │  4. If kubelet has --anonymous-auth=true            │
  │     → GET /exec → RCE on node                      │
  │  5. Reach cloud metadata: 169.254.169.254           │
  │     → steal IAM credentials (SSRF)                  │
  └─────────────────────────────────────────────────────┘
```

**Mitigations:**

```yaml
# Pod Security Standards - Restricted profile blocks hostNetwork
apiVersion: v1
kind: Namespace
metadata:
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: latest

---
# OPA/Gatekeeper constraint
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: K8sPSPHostNetworkingPorts
metadata:
  name: deny-host-network
spec:
  match:
    kinds:
      - apiGroups: [""]
        kinds: ["Pod"]
  parameters:
    hostNetwork: false
```

**Legitimate Uses (whitelist carefully):**
- CNI plugins themselves (must see host network)
- Node exporter (Prometheus)
- Network monitoring agents

---

### Q10. How does MTU misconfiguration in CNI lead to network-level vulnerabilities and packet drops?

**Answer:**

**MTU (Maximum Transmission Unit)** is the largest packet size that can be transmitted on a network link without fragmentation.

```
MTU CASCADE IN KUBERNETES OVERLAYS
=============================================================

  Physical NIC MTU:   1500 bytes (standard Ethernet)
  
  Overlay Encapsulation overhead:
  ┌────────────────────────────────────────┐
  │  VXLAN:    50 bytes overhead           │
  │  Geneve:   ~58 bytes overhead          │
  │  IP-in-IP: 20 bytes overhead           │
  │  WireGuard: 60 bytes overhead          │
  └────────────────────────────────────────┘

  Correct Pod MTU (VXLAN):
  1500 - 50 = 1450 bytes

  MISCONFIGURATION: Pod MTU set to 1500 (wrong)
  ┌─────────────────────────────────────────────────────┐
  │  Pod sends 1500 byte packet                         │
  │  CNI adds 50 byte VXLAN header = 1550 bytes         │
  │  Physical NIC: MTU=1500 → packet too big            │
  │  If DF (Don't Fragment) bit set → ICMP "too big"    │
  │  If ICMP blocked (firewall) → silent black hole     │
  │  Result: TCP hangs, large transfers fail            │
  │          TLS handshakes may drop mid-flight         │
  └─────────────────────────────────────────────────────┘

  Security Implications:
  ┌─────────────────────────────────────────────────────┐
  │  1. TLS/mTLS handshakes fail silently               │
  │     → operators disable mTLS "temporarily"          │
  │     → permanent security regression                 │
  │                                                     │
  │  2. ICMP black-hole detection blocked               │
  │     → PMTUD (Path MTU Discovery) fails              │
  │     → cascading connection failures                 │
  │                                                     │
  │  3. Partial packet delivery                         │
  │     → message authentication (HMAC) fails          │
  │     → spurious errors, insecure retry loops         │
  └─────────────────────────────────────────────────────┘
```

**Diagnosis Commands:**

```bash
# Check CNI-assigned MTU inside pod
kubectl exec -it <pod> -- ip link show eth0

# Test specific MTU path
kubectl exec -it <pod> -- ping -M do -s 1450 <dst-pod-ip>
# -M do = set DF bit, -s = payload size

# Verify node MTU
ip link show eth0 | grep mtu
```

**Fix (Cilium example):**

```yaml
# cilium-config ConfigMap
mtu: "1450"   # Explicitly set to 1500 - 50 (VXLAN overhead)
```

---

## Section 2: Kubernetes NetworkPolicy Deep Dive

---

### Q11. What is the "default deny all" pattern in Kubernetes NetworkPolicy, and why is implementing it incorrectly a critical security mistake?

**Answer:**

**Default Deny All** is a security baseline where you explicitly block all ingress and egress traffic to/from pods in a namespace, then selectively allow only what is needed.

```
DEFAULT DENY ALL PATTERN
=============================================================

  Step 1: Apply deny-all policy (MUST be done FIRST)
  ┌─────────────────────────────────────────────────────┐
  │  apiVersion: networking.k8s.io/v1                   │
  │  kind: NetworkPolicy                                │
  │  metadata:                                          │
  │    name: default-deny-all                           │
  │    namespace: production                            │
  │  spec:                                              │
  │    podSelector: {}    ← matches ALL pods            │
  │    policyTypes:                                     │
  │      - Ingress                                      │
  │      - Egress                                       │
  │    # No ingress/egress rules = deny all             │
  └─────────────────────────────────────────────────────┘

  Step 2: Add explicit allow policies
  ┌─────────────────────────────────────────────────────┐
  │  kind: NetworkPolicy                                │
  │  metadata:                                          │
  │    name: allow-frontend-to-backend                  │
  │  spec:                                              │
  │    podSelector:                                     │
  │      matchLabels:                                   │
  │        app: backend                                 │
  │    ingress:                                         │
  │      - from:                                        │
  │          - podSelector:                             │
  │              matchLabels:                           │
  │                app: frontend                        │
  │        ports:                                       │
  │          - port: 8080                               │
  └─────────────────────────────────────────────────────┘
```

**CRITICAL MISTAKES:**

**Mistake 1: Forgetting policyTypes: [Egress]**

```yaml
# WRONG - only declares Egress policyType, 
# Kubernetes then only enforces egress, ingress is OPEN
spec:
  podSelector: {}
  policyTypes:
    - Egress    # Ingress remains unrestricted!
```

**Mistake 2: Forgetting to allow DNS (port 53)**

```yaml
# After deny-all, pods cannot resolve DNS
# MUST add this allow:
egress:
  - to:
      - namespaceSelector:
          matchLabels:
            kubernetes.io/metadata.name: kube-system
    ports:
      - port: 53
        protocol: UDP
      - port: 53
        protocol: TCP
```

**Mistake 3: Namespace without any NetworkPolicy = fully open**

```
Namespace "staging":  NO NetworkPolicy objects
→ ALL pods in staging can talk to ALL pods in production
→ Lateral movement vector
```

**Verification:**

```bash
# Test deny-all is working
kubectl run test-pod --image=busybox --rm -it \
  --namespace=production -- wget -qO- http://backend:8080
# Expected: connection timeout (not connection refused)

# List effective policies
kubectl get networkpolicies -A
kubectl describe networkpolicy default-deny-all -n production
```

---

### Q12. Explain a NetworkPolicy that allows traffic only from a specific namespace AND specific pod label simultaneously. What is the AND vs OR logic trap?

**Answer:**

This is one of the most commonly misunderstood aspects of NetworkPolicy — the **AND vs OR semantics** between `namespaceSelector` and `podSelector` within the same `from` entry.

```
AND vs OR LOGIC IN NetworkPolicy
=============================================================

  CASE 1: AND logic (same list item — most restrictive)
  ┌──────────────────────────────────────────────────────┐
  │  ingress:                                            │
  │    - from:                                           │
  │        - namespaceSelector:          ← SAME '-' item │
  │            matchLabels:                              │
  │              env: prod                               │
  │          podSelector:                ← SAME '-' item │
  │            matchLabels:                              │
  │              app: frontend                           │
  │                                                      │
  │  Meaning: Allow from pods WHERE:                     │
  │    namespace.label[env] = prod                       │
  │    AND pod.label[app] = frontend                     │
  │                                                      │
  │  Blocks: frontend pod in staging namespace           │
  └──────────────────────────────────────────────────────┘

  CASE 2: OR logic (separate list items — more permissive)
  ┌──────────────────────────────────────────────────────┐
  │  ingress:                                            │
  │    - from:                                           │
  │        - namespaceSelector:          ← First '-'     │
  │            matchLabels:                              │
  │              env: prod                               │
  │        - podSelector:                ← Second '-'    │
  │            matchLabels:                              │
  │              app: frontend                           │
  │                                                      │
  │  Meaning: Allow from:                                │
  │    ANY pod in env=prod namespace                     │
  │    OR any pod with app=frontend in SAME namespace    │
  │                                                      │
  │  DANGER: Allows ALL pods in prod namespace           │
  │           + allows frontend from ANY namespace!      │
  └──────────────────────────────────────────────────────┘
```

**Visual Comparison:**

```
AND (secure):
  Allowed: ✅ frontend pod in prod namespace
  Blocked:  ✗ backend pod in prod namespace
  Blocked:  ✗ frontend pod in staging namespace

OR (often unintended):
  Allowed: ✅ frontend pod in prod namespace
  Allowed: ✅ backend pod in prod namespace (any pod in prod!)
  Allowed: ✅ frontend pod in staging namespace (any frontend!)
  Allowed: ✅ frontend pod in dev namespace
```

**Correct Secure Policy:**

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-prod-frontend-only
  namespace: backend-ns
spec:
  podSelector:
    matchLabels:
      app: backend
  ingress:
    - from:
        - namespaceSelector:        # AND with podSelector below
            matchLabels:
              environment: production
          podSelector:              # same list entry = AND
            matchLabels:
              app: frontend
      ports:
        - port: 8080
          protocol: TCP
```

---

### Q13. How do you implement namespace isolation in a multi-tenant Kubernetes cluster using NetworkPolicy?

**Answer:**

```
MULTI-TENANT NAMESPACE ISOLATION ARCHITECTURE
=============================================================

  Cluster with 3 tenants: Team-A, Team-B, Team-C
  
  WITHOUT isolation:
  Team-A pod → Team-B pod  ✅ (dangerous lateral movement)
  
  WITH isolation:
  Team-A pod → Team-B pod  ✗ (blocked by policy)
  Team-A pod → Team-A pod  ✅ (allowed within namespace)
  
  Label namespaces (REQUIRED for selector):
  kubectl label namespace team-a-ns team=team-a
  kubectl label namespace team-b-ns team=team-b
```

**Policy Set for Namespace Isolation:**

```yaml
---
# 1. Deny all ingress from other namespaces
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-from-other-namespaces
  namespace: team-a-ns
spec:
  podSelector: {}
  ingress:
    - from:
        - podSelector: {}     # Only pods in SAME namespace
          # Note: no namespaceSelector = same namespace only

---
# 2. Allow intra-namespace traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-same-namespace
  namespace: team-a-ns
spec:
  podSelector: {}
  ingress:
    - from:
        - podSelector: {}

---
# 3. Allow from shared services (monitoring, ingress)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-shared-services
  namespace: team-a-ns
spec:
  podSelector: {}
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: monitoring
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: ingress-nginx

---
# 4. Allow DNS egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns-egress
  namespace: team-a-ns
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP
```

**Automation with Hierarchical Namespace Controller (HNC):**
Apply policies as `SubnamespaceAnchor` — child namespaces inherit parent NetworkPolicies automatically, reducing human error.

---

### Q14. What are the limitations of Kubernetes NetworkPolicy and how do CNI-specific extensions overcome them?

**Answer:**

```
KUBERNETES NETWORKPOLICY LIMITATIONS
=============================================================

  Limitation 1: NO L7 (application layer) filtering
  ┌─────────────────────────────────────────────────────┐
  │  Can allow port 80 but CANNOT:                      │
  │  - Filter by HTTP method (GET vs POST)              │
  │  - Filter by URL path (/admin vs /api)              │
  │  - Filter by HTTP header values                     │
  │  - Filter by gRPC service/method                    │
  └─────────────────────────────────────────────────────┘
  Solution: Cilium L7 policy, Istio AuthorizationPolicy

  Limitation 2: NO deny rules
  ┌─────────────────────────────────────────────────────┐
  │  Only additive ALLOW rules                          │
  │  Cannot say "allow all EXCEPT from pod X"           │
  │  Must enumerate all allowed sources                 │
  └─────────────────────────────────────────────────────┘
  Solution: Calico GlobalNetworkPolicy with action: Deny

  Limitation 3: NO node-level policies
  ┌─────────────────────────────────────────────────────┐
  │  Cannot restrict pod→node traffic                   │
  │  Cannot protect kubelet API from pods               │
  └─────────────────────────────────────────────────────┘
  Solution: Calico HostEndpoint policies

  Limitation 4: NO external traffic matching beyond CIDR
  ┌─────────────────────────────────────────────────────┐
  │  Cannot match by FQDN (e.g., allow api.stripe.com)  │
  │  Only IP CIDR blocks for external traffic           │
  └─────────────────────────────────────────────────────┘
  Solution: Cilium FQDN policy, Calico GlobalNetworkSet

  Limitation 5: NO policy ordering
  ┌─────────────────────────────────────────────────────┐
  │  All NetworkPolicies evaluated together             │
  │  No priority/order field                            │
  │  Cannot express "this rule supersedes that"         │
  └─────────────────────────────────────────────────────┘
  Solution: Calico order field, Cilium priority
```

**CNI Extensions:**

```yaml
# Cilium FQDN-based egress policy
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
spec:
  endpointSelector:
    matchLabels:
      app: payment-service
  egress:
    - toFQDNs:
        - matchName: "api.stripe.com"
        - matchPattern: "*.amazonaws.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP

---
# Calico L7-aware policy (with Envoy)
apiVersion: projectcalico.org/v3
kind: NetworkPolicy
spec:
  selector: app == 'backend'
  ingress:
    - action: Allow
      http:
        methods: ["GET"]
        paths:
          - exact: /api/health
```

---

### Q15. How does egress traffic control differ from ingress in terms of security risk, and how do you implement a robust egress firewall in Kubernetes?

**Answer:**

```
INGRESS vs EGRESS RISK PROFILE
=============================================================

  Ingress Risk:
  External attacker → tries to reach internal pod
  Defense: Ingress controllers, WAF, NetworkPolicy ingress rules

  Egress Risk (often neglected):
  Compromised pod → connects to C2 server / exfiltrates data
  ┌─────────────────────────────────────────────────────┐
  │  Attack: Cryptominer → DNS beaconing to mine pool   │
  │  Attack: Supply chain → malicious dep → exfil creds │
  │  Attack: SSRF → pod calls cloud metadata API        │
  │  Attack: Ransomware → reaches backup storage        │
  └─────────────────────────────────────────────────────┘

  WHY EGRESS IS HARDER:
  - More dynamic (CDNs, SaaS APIs change IPs constantly)
  - FQDN matching requires DNS interception
  - Must not break legitimate outbound traffic
```

**Robust Egress Firewall Architecture:**

```
LAYERED EGRESS CONTROL
=============================================================

  Layer 1: Default Deny Egress (NetworkPolicy)
  Layer 2: Allow only specific ports/destinations
  Layer 3: FQDN filtering (Cilium/Calico DNS policy)
  Layer 4: Egress gateway (centralized NAT + audit)
  Layer 5: DLP proxy (optional — inspect payloads)

                     ┌─────────────────┐
  Pod egress packet  │  eBPF/iptables  │ Layer 1-3
  ─────────────────> │  NetworkPolicy  │ ──────────→ DROP (default)
                     └────────┬────────┘
                              │ allowed
                              v
                     ┌─────────────────┐
                     │  Egress Gateway │ Layer 4
                     │  (Cilium EG /   │
                     │   Calico EG)    │ ──────────→ Internet
                     └─────────────────┘
                              │
                     Audit log: who sent what where
```

**Implementation:**

```yaml
# Step 1: Deny all egress
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny-egress
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress

---
# Step 2: Allow DNS and specific SaaS
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: allow-specific-egress
  namespace: production
spec:
  endpointSelector: {}
  egress:
    # DNS
    - toEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
            k8s-app: kube-dns
      toPorts:
        - ports:
            - port: "53"
              protocol: ANY
    # Allowed external
    - toFQDNs:
        - matchName: "api.stripe.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP

---
# Step 3: Block cloud metadata always
apiVersion: cilium.io/v2
kind: CiliumNetworkPolicy
metadata:
  name: block-metadata-server
spec:
  endpointSelector: {}
  egressDeny:
    - toCIDR:
        - 169.254.169.254/32
```

---

### Q16. Explain how a NetworkPolicy bypass attack works and how an attacker could escape policy enforcement.

**Answer:**

```
NETWORKPOLICY BYPASS ATTACK VECTORS
=============================================================

  VECTOR 1: Targeting a pod with NO NetworkPolicy selector
  ┌─────────────────────────────────────────────────────┐
  │  Policy selects: app=backend                        │
  │  Attacker pod labels: app=legacy-backend (no policy)│
  │  Result: attacker pod is non-isolated = open        │
  └─────────────────────────────────────────────────────┘

  VECTOR 2: Node-level bypass (hostNetwork pod)
  ┌─────────────────────────────────────────────────────┐
  │  NetworkPolicy only applies to pod network          │
  │  hostNetwork:true pod → uses node network           │
  │  NetworkPolicy does NOT apply to node network       │
  │  Attacker reaches any pod on the node directly      │
  └─────────────────────────────────────────────────────┘

  VECTOR 3: CNI plugin not enforcing policy
  ┌─────────────────────────────────────────────────────┐
  │  Using Flannel alone (no NetworkPolicy support)     │
  │  NetworkPolicy objects exist but NO enforcement     │
  │  False sense of security                            │
  │  Must use Flannel + kube-router or switch to Calico │
  └─────────────────────────────────────────────────────┘

  VECTOR 4: iptables manipulation from privileged pod
  ┌─────────────────────────────────────────────────────┐
  │  Privileged pod / CAP_NET_ADMIN pod                 │
  │  Can flush iptables: iptables -F                    │
  │  Removes ALL NetworkPolicy enforcement rules        │
  │  All policies suddenly ineffective node-wide        │
  └─────────────────────────────────────────────────────┘

  VECTOR 5: Service account token → API bypass
  ┌─────────────────────────────────────────────────────┐
  │  NetworkPolicy doesn't control API server access    │
  │  Pod with mounted ServiceAccount token              │
  │  Can call kubectl/API directly (not network blocked)│
  │  Lateral movement via API, not pod-to-pod network   │
  └─────────────────────────────────────────────────────┘
```

**Defense Matrix:**

| Bypass Vector               | Defense                                               |
|-----------------------------|-------------------------------------------------------|
| Unlabeled/unselected pods   | Apply deny-all to `podSelector: {}` (all pods)       |
| hostNetwork bypass          | PSS Restricted profile, OPA deny hostNetwork         |
| CNI without enforcement     | Use Calico/Cilium/Weave with NetworkPolicy support    |
| iptables flush              | Block CAP_NET_ADMIN, use eBPF (kernel-level, no flush)|
| API server lateral movement | RBAC + separate network control plane access          |

---

### Q17. What is Cilium's ClusterwidenetworkPolicy and how does it differ from CiliumNetworkPolicy?

**Answer:**

```
CILIUM POLICY SCOPE HIERARCHY
=============================================================

  CiliumNetworkPolicy (CNP):
  ┌────────────────────────────────────────────────────┐
  │  Namespace-scoped                                  │
  │  Lives in a specific namespace                     │
  │  Namespace admin can create/modify                 │
  │  Applies to endpoints in that namespace only       │
  └────────────────────────────────────────────────────┘

  CiliumClusterwideNetworkPolicy (CCNP):
  ┌────────────────────────────────────────────────────┐
  │  Cluster-scoped (no namespace field)               │
  │  Requires cluster-admin to create                  │
  │  Applies to ALL endpoints across ALL namespaces    │
  │  Can match nodes via NodeSelector                  │
  │  Cannot be overridden by namespace-level CNP       │
  └────────────────────────────────────────────────────┘
```

**Example Use Cases:**

```yaml
# CCNP: Block access to node metadata globally
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: block-metadata-global
spec:
  endpointSelector: {}    # all pods cluster-wide
  egressDeny:
    - toCIDR:
        - 169.254.169.254/32

---
# CCNP: Allow monitoring namespace to scrape all pods
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: allow-prometheus-scrape
spec:
  endpointSelector: {}
  ingress:
    - fromEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: monitoring
            app: prometheus
      toPorts:
        - ports:
            - port: "9090"
              protocol: TCP

---
# CCNP: Node-level policy (protect host)
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: protect-node-kubelet
spec:
  nodeSelector:
    matchLabels:
      kubernetes.io/os: linux
  ingress:
    - fromEndpoints:
        - matchLabels:
            k8s:io.kubernetes.pod.namespace: kube-system
      toPorts:
        - ports:
            - port: "10250"
              protocol: TCP
```

---

### Q18. How does Kubernetes handle NetworkPolicy for StatefulSets and headless services — what are the unique security considerations?

**Answer:**

```
STATEFULSET + HEADLESS SERVICE NETWORKING
=============================================================

  StatefulSet: database (3 replicas)
  Headless Service: database-headless (clusterIP: None)
  
  DNS resolution:
  database-headless.namespace.svc.cluster.local → [IPs of all pods]
  database-0.database-headless.namespace.svc.cluster.local → Pod 0 IP
  database-1.database-headless.namespace.svc.cluster.local → Pod 1 IP
  
  Pod-to-Pod direct communication (no kube-proxy):
  database-0 ←→ database-1 ←→ database-2
  (Raft consensus, Galera cluster, etcd peer traffic)
```

**Unique Security Concerns:**

```
1. Peer traffic between StatefulSet pods
   Often needs UNRESTRICTED access between replicas
   (e.g., PostgreSQL streaming replication on port 5432)
   
   RISK: If one replica is compromised → direct access to all peers

2. Stable Network Identity Attack
   Pod name = database-0
   Attacker knows predictable DNS: database-0.db-svc.prod.svc.cluster.local
   Can target specific replica for data exfil

3. PersistentVolume side-channel
   Even with NetworkPolicy blocking network
   Shared storage paths can leak data between pods
   (separate from network security)
```

**Secure StatefulSet NetworkPolicy:**

```yaml
---
# Allow inter-replica traffic (peer replication)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-db-peer-replication
  namespace: data
spec:
  podSelector:
    matchLabels:
      app: postgresql
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: postgresql    # only from other DB pods
      ports:
        - port: 5432
          protocol: TCP

---
# Allow app layer to reach DB
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-app-to-db
  namespace: data
spec:
  podSelector:
    matchLabels:
      app: postgresql
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              environment: production
          podSelector:
            matchLabels:
              app: backend
      ports:
        - port: 5432
          protocol: TCP

---
# Deny all other ingress to DB pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-other-db-ingress
  namespace: data
spec:
  podSelector:
    matchLabels:
      app: postgresql
  policyTypes:
    - Ingress
  # No ingress rules = deny all not matched above
```

---

### Q19. Explain how Calico's Wireguard encryption works at the CNI level and how to verify it is active.

**Answer:**

**WireGuard in Calico** encrypts all pod-to-pod traffic between nodes using WireGuard tunnels, without requiring application-level changes.

```
WIREGUARD ENCRYPTION FLOW (Calico)
=============================================================

  Pod A (Node 1) → Pod B (Node 2)

  WITHOUT WireGuard:
  [Pod packet] → [IPIP tunnel] → [Node 2] → [Pod B]
  PLAINTEXT on wire

  WITH WireGuard:
  [Pod packet]
    → Felix on Node 1 routes via wireguard0 interface
    → WireGuard kernel module encrypts with ChaCha20-Poly1305
    → Encapsulates in UDP:51820
    → [Encrypted UDP packet on physical network]
    → Node 2 WireGuard decrypts
    → Delivered to Pod B

  Key Exchange:
  Felix on each node:
  1. Generates WireGuard keypair on boot
  2. Publishes public key to calico datastore (CRD/etcd)
  3. Fetches peer public keys from datastore
  4. Configures wireguard0 with peer entries
  5. WireGuard performs ECDH key exchange transparently
```

**Enabling WireGuard:**

```bash
# Enable WireGuard encryption in Calico
kubectl patch felixconfiguration default \
  --type='merge' \
  -p '{"spec":{"wireguardEnabled":true}}'

# For IPv6:
kubectl patch felixconfiguration default \
  --type='merge' \
  -p '{"spec":{"wireguardEnabledV6":true}}'
```

**Verification:**

```bash
# Check WireGuard interface on node
kubectl get node <node-name> -o jsonpath='{.metadata.annotations.projectcalico\.org/WireguardPublicKey}'

# On the node itself:
wg show
# Output shows:
# interface: wireguard.cali
# public key: <base64 pubkey>
# peers: <list of other nodes>
# transfer: X GiB received, Y GiB sent

# Verify traffic is encrypted (tcpdump on node)
tcpdump -i eth0 -n udp port 51820
# You should see UDP:51820 traffic (not IPIP or VXLAN)
# Payload is ENCRYPTED - no plaintext pod IPs visible
```

**Security Properties:**
- Forward secrecy: session keys rotate
- ChaCha20-Poly1305: AEAD cipher (authenticated encryption)
- No manual certificate management
- Transparent to pods — works with any CNI topology

---

### Q20. What is a network policy testing strategy for a production Kubernetes cluster — how do you validate policies without causing outage?

**Answer:**

```
NETWORKPOLICY TESTING STRATEGY
=============================================================

  Phase 1: Policy-as-Code & Dry Run
  ┌────────────────────────────────────────────────────┐
  │  Tools: kubectl dry-run, netpol-analyzer, conftest │
  │  Apply: kubectl apply --dry-run=server             │
  │  Lint: check for common mistakes (AND/OR, DNS)     │
  └────────────────────────────────────────────────────┘

  Phase 2: Test Environment Validation
  ┌────────────────────────────────────────────────────┐
  │  Mirror prod namespace to staging                  │
  │  Deploy netshoot pod for connectivity tests        │
  │  Use sonobuoy or cyclonus for policy conformance   │
  └────────────────────────────────────────────────────┘

  Phase 3: Canary / Shadow Mode (prod)
  ┌────────────────────────────────────────────────────┐
  │  Cilium: policy in audit/log mode (no drop)        │
  │  Observe: what WOULD be dropped?                   │
  │  Fix: address legitimate flows                     │
  │  Promote: switch to enforce mode                   │
  └────────────────────────────────────────────────────┘

  Phase 4: Progressive Rollout
  ┌────────────────────────────────────────────────────┐
  │  Apply to 1 namespace → monitor 24h               │
  │  Check: app errors, connection timeouts            │
  │  Expand to next namespace                          │
  └────────────────────────────────────────────────────┘
```

**Practical Test Commands:**

```bash
# Deploy test pod in target namespace
kubectl run netshoot --image=nicolaka/netshoot \
  --namespace=production -it --rm -- /bin/bash

# Test allowed connection (should succeed)
curl -sv http://backend:8080/health --connect-timeout 5

# Test blocked connection (should timeout)
curl -sv http://other-service:8080 --connect-timeout 5

# Use cyclonus for automated policy conformance
kubectl apply -f https://github.com/mattfenwick/cyclonus/...
kubectl logs -n cyclonus cyclonus-0

# Cilium policy audit mode
cilium policy audit-mode enable

# View what would be dropped (no actual drops)
cilium monitor --type drop

# After validation, switch to enforce
cilium policy audit-mode disable
```

---

## Section 3: Service Mesh & mTLS Security

---

### Q21. Explain how mTLS works in Istio, from certificate issuance to connection establishment.

**Answer:**

**mTLS (Mutual TLS)** means BOTH client and server authenticate each other using X.509 certificates — unlike regular TLS where only the server is authenticated.

```
mTLS CERTIFICATE LIFECYCLE IN ISTIO
=============================================================

  ISSUANCE PHASE:

  1. istiod (Pilot) runs built-in CA (Citadel)
     ┌─────────────────────────────────────────────────┐
     │  Root CA: istiod self-signed or plugged cert    │
     │  Issues intermediate CA per cluster (optional)  │
     └─────────────────────────────────────────────────┘

  2. Envoy sidecar starts with new Pod
     ┌─────────────────────────────────────────────────┐
     │  Envoy generates keypair locally                │
     │  Sends CSR to istiod via Envoy SDS API          │
     │  (SDS = Secret Discovery Service, gRPC)         │
     └─────────────────────────────────────────────────┘

  3. istiod validates CSR
     ┌─────────────────────────────────────────────────┐
     │  Checks: Pod's ServiceAccount JWT               │
     │  Verifies JWT with Kubernetes API               │
     │  Confirms pod identity = ServiceAccount         │
     └─────────────────────────────────────────────────┘

  4. istiod issues certificate
     ┌─────────────────────────────────────────────────┐
     │  Subject: spiffe://cluster.local/ns/prod/       │
     │           sa/frontend-sa                        │
     │  SAN (SPIFFE URI): same                         │
     │  TTL: 24h (default, rotated hourly)             │
     └─────────────────────────────────────────────────┘

  CONNECTION PHASE:

  Frontend Pod → Backend Pod (mTLS):
  ┌─────────────────────────────────────────────────────┐
  │  1. App writes to localhost:8080 (NO mTLS aware)    │
  │  2. iptables REDIRECT → Envoy sidecar (127.0.0.1)  │
  │  3. Frontend Envoy initiates TLS                    │
  │  4. Backend Envoy presents certificate              │
  │     SAN: spiffe://cluster.local/ns/prod/sa/backend  │
  │  5. Frontend Envoy validates cert against Trust Domain│
  │  6. Frontend Envoy presents ITS certificate         │
  │  7. Backend Envoy validates frontend cert           │
  │  8. Both validate = mTLS handshake success          │
  │  9. Encrypted data flows between Envoy sidecars     │
  │  10. Backend Envoy decrypts → sends to app:8080     │
  └─────────────────────────────────────────────────────┘

  App code sees plaintext — mTLS is TRANSPARENT to apps!
```

**SPIFFE Identity Format:**
```
spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>
spiffe://cluster.local/ns/production/sa/payment-service
```

---

### Q22. What is the difference between Istio's PERMISSIVE and STRICT mTLS modes, and what are the security risks of running in PERMISSIVE mode in production?

**Answer:**

```
mTLS MODE COMPARISON
=============================================================

  PERMISSIVE MODE:
  ┌─────────────────────────────────────────────────────┐
  │  Service accepts BOTH:                              │
  │  a) mTLS connections (from mesh services)           │
  │  b) Plaintext connections (from non-mesh/external)  │
  │                                                     │
  │  Use case: Migration period — gradual onboarding    │
  └─────────────────────────────────────────────────────┘

  STRICT MODE:
  ┌─────────────────────────────────────────────────────┐
  │  Service ONLY accepts mTLS connections              │
  │  Plaintext connections are REJECTED                 │
  │  All callers must have valid SPIFFE cert            │
  └─────────────────────────────────────────────────────┘

  Traffic Decision Matrix:

  Source → Destination      | PERMISSIVE | STRICT
  ─────────────────────────────────────────────────
  Mesh pod → Mesh pod       | mTLS ✅    | mTLS ✅
  External → Mesh pod       | Plaintext✅ | REJECTED ✗
  Legacy pod → Mesh pod     | Plaintext✅ | REJECTED ✗
  Non-sidecar pod → Mesh    | Plaintext✅ | REJECTED ✗
```

**Security Risks of PERMISSIVE in Production:**

```
RISK 1: MITM via Plaintext Downgrade
  Attacker intercepts connection
  Presents as non-mesh client
  Receives service response in PLAINTEXT
  No authentication check occurs

RISK 2: Bypassing AuthorizationPolicy
  Istio AuthorizationPolicy often uses source.principal
  (SPIFFE identity from mTLS cert)
  Plaintext connection has NO principal
  Policy: deny if no principal → plaintext bypasses it!
  ┌─────────────────────────────────────────────────────┐
  │  authorizationPolicy:                               │
  │    action: ALLOW                                    │
  │    when:                                            │
  │      - key: source.principal                        │
  │        values: ["cluster.local/ns/prod/sa/frontend"]│
  │                                                     │
  │  PERMISSIVE: Attacker sends plaintext               │
  │  → no source.principal → policy default = ALLOW     │
  │  → authorization bypassed!                          │
  └─────────────────────────────────────────────────────┘

RISK 3: Certificate Validation Gap
  PERMISSIVE won't validate peer cert even if present
  Expired/revoked certs may still work
```

**Enforcing STRICT:**

```yaml
# Global STRICT for entire mesh
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: istio-system
spec:
  mtls:
    mode: STRICT

---
# Per-namespace STRICT override
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: strict-mtls
  namespace: production
spec:
  mtls:
    mode: STRICT
```

**Migration Path:**
```
PERMISSIVE (all services)
  → Inject sidecars to all services
  → Verify all inter-service traffic is mTLS
     (check Kiali/Jaeger for mTLS lock icon)
  → Switch to STRICT namespace by namespace
  → STRICT (all namespaces)
```

---

### Q23. Explain Istio's AuthorizationPolicy and how to implement a zero-trust "allow-nothing-by-default" model.

**Answer:**

**Istio AuthorizationPolicy** is the L7 authorization layer — it controls which services can call which services, and at what HTTP paths/methods. It works AFTER mTLS authentication.

```
AUTHORIZATION FLOW
=============================================================

  Client Pod → [mTLS] → Server Envoy
                              |
                    AuthorizationPolicy
                    evaluation by Envoy
                              |
                   +----------+----------+
                   |                     |
              ALLOW rules          DENY rules
              (evaluated last)     (evaluated first)
                   |                     |
               If matched            Immediately
               → ALLOW               reject 403
```

**Zero-Trust Implementation:**

```yaml
---
# Step 1: Deny EVERYTHING by default in namespace
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-all
  namespace: production
spec:
  {}
  # Empty spec = deny all traffic to all workloads in namespace

---
# Step 2: Allow specific flows
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
              - "cluster.local/ns/production/sa/frontend-sa"
      to:
        - operation:
            methods: ["GET", "POST"]
            paths: ["/api/*"]
      when:
        - key: request.headers[x-request-id]
          notValues: [""]    # Require tracing header

---
# Step 3: Explicit DENY for sensitive endpoints
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: deny-admin-from-external
  namespace: production
spec:
  selector:
    matchLabels:
      app: backend
  action: DENY
  rules:
    - to:
        - operation:
            paths: ["/admin/*", "/internal/*"]
      from:
        - source:
            notPrincipals:
              - "cluster.local/ns/production/sa/admin-sa"
```

**Policy Evaluation Order:**

```
1. CUSTOM action (external authorizer like OPA) — first
2. DENY rules — evaluated before ALLOW
3. ALLOW rules — if matched, permit
4. Default — if no ALLOW matches → DENY (403)
```

---

### Q24. How does Istio handle certificate rotation and what happens during rotation if not configured correctly?

**Answer:**

```
CERTIFICATE ROTATION LIFECYCLE
=============================================================

  Default Config:
  - Cert TTL: 24 hours
  - Rotation starts at: 50% of TTL (12 hours before expiry)
  - SDS rotates cert transparently without restart

  ROTATION FLOW:
  ┌─────────────────────────────────────────────────────┐
  │  T=0:    Envoy cert issued (TTL 24h)                │
  │  T=12h:  Envoy requests new cert via SDS gRPC      │
  │  istiod: issues new cert (different serial)         │
  │  Envoy:  holds BOTH old and new cert                │
  │  T=24h:  Old cert expires, new cert is primary      │
  │  Connections: new TLS uses new cert                 │
  │  Existing connections: drain with old cert          │
  └─────────────────────────────────────────────────────┘

  NO RESTART REQUIRED — hot rotation via SDS
```

**Misconfiguration Problems:**

```
PROBLEM 1: istiod CA cert expires
  Root CA TTL: 10 years (default)
  If CA cert expires → ALL workload certs become invalid
  SIMULTANEOUSLY → complete mesh failure
  
  FIX: Set up CA cert renewal alerting at 90 days before expiry
  kubectl get secret istio-ca-secret -n istio-system \
    -o jsonpath='{.data.ca-cert\.pem}' | base64 -d | \
    openssl x509 -noout -enddate

PROBLEM 2: Clock skew between nodes
  Cert validity: notBefore/notAfter based on system time
  If node clock is 5 minutes fast:
  New cert issued → "not yet valid" on other nodes
  → TLS handshake fails for 5 minutes
  
  FIX: Enforce NTP sync (chrony/systemd-timesyncd)
  Monitor: node_timex_sync_status Prometheus metric

PROBLEM 3: Too-long TTL certs
  Cert TTL = 87600h (10 years) — seen in misconfigured setups
  Compromised cert stays valid for 10 years
  No rotation benefit
  
  FIX: Set workload cert TTL to maximum 24h
  kubectl patch configmap istio \
    -n istio-system \
    --type merge \
    -p '{"data":{"defaultConfig":{"proxyMetadata":{"SECRET_TTL":"86400s"}}}}'
```

---

### Q25. What is Linkerd's approach to mTLS vs Istio's — compare the security models and attack surface.

**Answer:**

```
LINKERD vs ISTIO SECURITY ARCHITECTURE
=============================================================

  LINKERD:
  ┌────────────────────────────────────────────────────┐
  │  Proxy: Rust-based linkerd2-proxy (micro-proxy)   │
  │  CA: Trust anchor (self-signed) + issuer cert     │
  │  cert-manager integration for rotation            │
  │  mTLS: Automatic for all meshed pods              │
  │  Identity: based on ServiceAccount (SPIFFE-like)  │
  │  Config: minimal — just inject annotation         │
  │  L7 policy: TrafficPolicy (newer) / SMI           │
  │  Attack surface: Smaller (no Envoy WASM plugins)  │
  │  Control plane: linkerd-control-plane (small)     │
  └────────────────────────────────────────────────────┘

  ISTIO:
  ┌────────────────────────────────────────────────────┐
  │  Proxy: Envoy (C++ — feature rich but large)      │
  │  CA: istiod built-in CA or external (Vault/AWS)   │
  │  mTLS: PERMISSIVE by default (must enable STRICT)  │
  │  Identity: SPIFFE URIs (full spec compliance)     │
  │  Config: complex (VirtualService, DR, Gateway...) │
  │  L7 policy: AuthorizationPolicy (powerful)        │
  │  Attack surface: Larger (WASM, xDS, Envoy CVEs)   │
  │  Control plane: istiod (larger binary)            │
  └────────────────────────────────────────────────────┘

  ATTACK SURFACE COMPARISON:
  
  Linkerd risks:
  - linkerd-control-plane API exposure
  - Trust anchor private key compromise
  - Proxy injection webhook misconfiguration

  Istio risks:
  - Envoy CVEs (buffer overflow, heap issues in C++)
  - istiod API exposure (xDS spoofing)
  - WASM filter supply chain attack
  - Pilot push amplification (many envoys)
  - Pilot misconfiguration → wrong certs distributed
```

**When to Choose:**

| Criteria             | Choose Linkerd            | Choose Istio                    |
|----------------------|---------------------------|---------------------------------|
| Security surface     | Smaller, Rust safety      | Accept larger for more features |
| L7 policy need       | Basic (SMI)               | Complex (AuthorizationPolicy)   |
| External CA (Vault)  | cert-manager integration  | Native Vault integration        |
| Multi-cluster        | Linkerd multi-cluster     | Istio multi-primary             |
| Operational maturity | Simpler ops               | Complex, more knobs             |

---

### Q26. How does Istio's egress gateway enforce security for outbound traffic, and how can it be bypassed?

**Answer:**

```
ISTIO EGRESS GATEWAY ARCHITECTURE
=============================================================

  Without Egress Gateway:
  Pod → [Envoy sidecar] → Direct to Internet
  
  Policy control: limited
  Audit: only sidecar logs (distributed, hard to correlate)

  With Egress Gateway:
  Pod → [Envoy sidecar] → [Egress Gateway Pod] → Internet
  
  ┌──────────────────────────────────────────────────────┐
  │  All outbound traffic funneled through central point │
  │  Apply policy, TLS inspection, logging at one place  │
  │  Egress Gateway presents fixed IP to firewall        │
  │  External firewall can whitelist gateway IP only     │
  └──────────────────────────────────────────────────────┘

  Configuration:
  1. ServiceEntry: declare external service
  2. VirtualService: route egress → gateway
  3. DestinationRule: mTLS to gateway
  4. Gateway: listen for egress traffic
```

**Configuration:**

```yaml
# 1. Declare external service
apiVersion: networking.istio.io/v1beta1
kind: ServiceEntry
metadata:
  name: stripe-api
spec:
  hosts:
    - api.stripe.com
  ports:
    - number: 443
      name: https
      protocol: HTTPS
  resolution: DNS
  location: MESH_EXTERNAL

---
# 2. Route through egress gateway
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: stripe-through-egress
spec:
  hosts:
    - api.stripe.com
  gateways:
    - mesh
    - istio-egressgateway
  http:
    - match:
        - gateways:
            - mesh
      route:
        - destination:
            host: istio-egressgateway.istio-system.svc.cluster.local
            port:
              number: 443
```

**Bypass Vectors:**

```
BYPASS 1: Pod without sidecar injection
  Namespace missing: istio-injection=enabled label
  Pod egress → direct to internet, bypasses gateway entirely

  FIX: Enforce sidecar injection via MutatingWebhook
       Use PodSecurity or Gatekeeper to deny pods without sidecar

BYPASS 2: hostNetwork pod
  Bypasses all Envoy interception
  Traffic not captured by iptables REDIRECT rules

  FIX: Block hostNetwork via PSS Restricted profile

BYPASS 3: Raw socket / UDP (Envoy doesn't proxy UDP by default)
  Attacker uses UDP to bypass TCP-based Envoy proxy

  FIX: Layer iptables rules to block non-DNS UDP egress at node level

BYPASS 4: ServiceEntry with resolution: NONE
  Misconfigured ServiceEntry allows all external IPs
  FIX: Audit ServiceEntry objects — disallow MESH_EXTERNAL without approval
```

---

### Q27. Explain how to integrate HashiCorp Vault as an external CA for Istio mTLS certificate management.

**Answer:**

```
VAULT PKI + ISTIO INTEGRATION
=============================================================

  Architecture:
  ┌─────────────────────────────────────────────────────┐
  │  HashiCorp Vault                                    │
  │  ┌─────────────────────────────────────────────┐   │
  │  │  PKI Secrets Engine                         │   │
  │  │  Root CA (offline/air-gapped)               │   │
  │  │  Intermediate CA for Kubernetes cluster     │   │
  │  │  Role: issue workload certs TTL=24h          │   │
  │  └─────────────────────────────────────────────┘   │
  └─────────────────────────────────────────────────────┘
            |
            | cert-manager Vault issuer
            v
  ┌─────────────────────────────────────────────────────┐
  │  cert-manager (in cluster)                         │
  │  VaultClusterIssuer → issues istio-ca-secret        │
  │  Automatically rotates intermediate CA cert         │
  └─────────────────────────────────────────────────────┘
            |
            | istio-ca-secret
            v
  ┌─────────────────────────────────────────────────────┐
  │  istiod (reads istio-ca-secret)                    │
  │  Acts as intermediate CA                           │
  │  Issues workload SPIFFE certs from Vault chain     │
  └─────────────────────────────────────────────────────┘
```

**Setup Steps:**

```bash
# 1. Enable PKI in Vault
vault secrets enable pki
vault secrets tune -max-lease-ttl=87600h pki

# 2. Generate Root CA (keep offline in prod)
vault write pki/root/generate/internal \
  common_name="cluster-root-ca" \
  ttl=87600h

# 3. Create intermediate CA for Kubernetes
vault secrets enable -path=pki_int pki
vault write -format=json pki_int/intermediate/generate/internal \
  common_name="istio-intermediate-ca" | \
  jq -r '.data.csr' > intermediate.csr

vault write pki/root/sign-intermediate \
  csr=@intermediate.csr \
  format=pem_bundle > signed.pem

vault write pki_int/intermediate/set-signed \
  certificate=@signed.pem

# 4. Create role for Istio
vault write pki_int/roles/istio-workload \
  allowed_domains="cluster.local" \
  allow_subdomains=true \
  max_ttl=24h \
  require_cn=false \
  allowed_uri_sans="spiffe://cluster.local/*"

# 5. cert-manager VaultClusterIssuer
kubectl apply -f - <<EOF
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: vault-istio-issuer
spec:
  vault:
    path: pki_int/sign/istio-workload
    server: https://vault.internal:8200
    auth:
      kubernetes:
        role: cert-manager
        mountPath: /v1/auth/kubernetes
        serviceAccountRef:
          name: cert-manager
EOF
```

**Security Benefits:**
- Centralized certificate audit trail in Vault
- HSM-backed root CA (Vault Enterprise)
- Automated rotation without manual intervention
- Revocation via Vault CRL (cert-manager OCSP integration)

---

### Q28. What is SPIFFE/SPIRE and how does it provide workload identity beyond Kubernetes boundaries?

**Answer:**

**SPIFFE (Secure Production Identity Framework For Everyone)** is a standard for workload identity. **SPIRE** is its reference implementation.

```
SPIFFE/SPIRE ARCHITECTURE
=============================================================

  SPIRE Server (control plane — can be outside K8s)
  ┌─────────────────────────────────────────────────────┐
  │  Maintains registry of workload identities          │
  │  Acts as CA — issues SVIDs (X.509 certs)           │
  │  Validates attestation from SPIRE Agents           │
  │  Integrates: etcd, Kubernetes, cloud metadata      │
  └─────────────────────────────────────────────────────┘
        |
        | authenticated gRPC
        v
  SPIRE Agent (DaemonSet on each node)
  ┌─────────────────────────────────────────────────────┐
  │  Attests to SPIRE Server (node attestation)        │
  │  Verifies: K8s node token, cloud instance identity │
  │  Issues SVIDs to workloads via Workload API        │
  │  Exposes UNIX socket: /run/spire/sockets/agent.sock │
  └─────────────────────────────────────────────────────┘
        |
        | Workload API (UNIX socket)
        v
  Workload (Pod / VM / Lambda / etc.)
  ┌─────────────────────────────────────────────────────┐
  │  Calls Workload API (no credentials needed)        │
  │  Receives SVID = X.509 cert with SPIFFE URI SAN    │
  │  SPIFFE URI: spiffe://example.org/ns/prod/svc/api  │
  │  Valid across: K8s, VMs, AWS Lambda, on-prem       │
  └─────────────────────────────────────────────────────┘

  Cross-Platform Identity:
  K8s Pod ←→ [SPIFFE SVID] ←→ AWS EC2 VM
  Same trust domain, different attestation plugins
```

**SVID Types:**
- **X.509-SVID:** Certificate with SPIFFE URI in SAN — used for mTLS
- **JWT-SVID:** JWT token with SPIFFE subject — used for HTTP bearer auth

**Registration Entry Example:**

```bash
# Register a Kubernetes workload
spire-server entry create \
  -spiffeID spiffe://example.org/ns/production/sa/payment-svc \
  -parentID spiffe://example.org/k8s-node/node-1 \
  -selector k8s:ns:production \
  -selector k8s:sa:payment-svc \
  -ttl 3600

# Register an EC2 workload (same trust domain)
spire-server entry create \
  -spiffeID spiffe://example.org/aws/prod/legacy-app \
  -parentID spiffe://example.org/k8s-node/aws-node \
  -selector aws_iid:account:123456789012 \
  -selector aws_iid:region:us-east-1
```

**Why Beyond Kubernetes:**
Istio's mTLS only works within the mesh. SPIRE allows:
- K8s pods ↔ on-premise VMs with same identity framework
- K8s pods ↔ serverless functions
- Federation across organizational trust domains

---

### Q29. How does Istio's telemetry affect security — what sensitive data can be leaked in traces/logs?

**Answer:**

```
TELEMETRY DATA LEAKAGE RISKS
=============================================================

  Distributed Traces (Jaeger/Zipkin):
  ┌─────────────────────────────────────────────────────┐
  │  Istio traces can contain:                         │
  │  - Full URL path: /api/users/12345?ssn=123-45-6789 │
  │  - Request headers (including Authorization: Bearer)│
  │  - gRPC method arguments (if sampled at 100%)      │
  │  - HTTP response codes (200, 401, 500)             │
  │  - Service dependency graph (attack planning info) │
  └─────────────────────────────────────────────────────┘

  Access Logs (Envoy):
  ┌─────────────────────────────────────────────────────┐
  │  Default access log format includes:               │
  │  %REQ(:METHOD)% %REQ(X-ENVOY-ORIGINAL-PATH?:PATH)% │
  │  → Logs full URL path → credential in URL leaked   │
  │  %REQ(X-FORWARDED-FOR)% → leaks client real IP     │
  │  %RESP(SET-COOKIE)%     → session cookies in log   │
  └─────────────────────────────────────────────────────┘

  Metrics (Prometheus):
  ┌─────────────────────────────────────────────────────┐
  │  HTTP response codes by path → attack surface map  │
  │  request_bytes by service → data volume patterns   │
  │  Cardinality explosion if URL params in labels     │
  └─────────────────────────────────────────────────────┘
```

**Hardening Telemetry:**

```yaml
# Redact sensitive headers from traces
apiVersion: telemetry.istio.io/v1alpha1
kind: Telemetry
metadata:
  name: secure-tracing
  namespace: production
spec:
  tracing:
    - providers:
        - name: jaeger
      customTags:
        request_id:
          header:
            name: x-request-id
      # Do NOT propagate Authorization header
  accessLogging:
    - providers:
        - name: envoy
      filter:
        # Only log errors, not all requests
        expression: "response.code >= 400"

---
# Custom access log format excluding sensitive data
apiVersion: networking.istio.io/v1alpha3
kind: EnvoyFilter
metadata:
  name: sanitize-access-logs
spec:
  configPatches:
    - applyTo: NETWORK_FILTER
      match:
        listener:
          filterChain:
            filter:
              name: "envoy.filters.network.http_connection_manager"
      patch:
        operation: MERGE
        value:
          typed_config:
            "@type": type.googleapis.com/envoy.extensions.filters.network.http_connection_manager.v3.HttpConnectionManager
            access_log_options:
              flush_access_log_on_new_request: false
```

---

### Q30. Explain the security implications of Envoy's xDS protocol — how can a compromised istiod affect the entire mesh?

**Answer:**

**xDS (any Discovery Service)** is the gRPC-based API protocol Envoy uses to receive configuration from the control plane (istiod). It includes: EDS (endpoints), CDS (clusters), LDS (listeners), RDS (routes), SDS (secrets).

```
xDS TRUST MODEL
=============================================================

  istiod → pushes xDS config → Every Envoy in cluster
  
  If istiod is compromised:
  ┌─────────────────────────────────────────────────────┐
  │  Attacker controls: (push to all Envoys)           │
  │                                                     │
  │  LDS: Add listener → intercept all traffic         │
  │  RDS: Route /payments → attacker's service         │
  │  CDS: Add new upstream = attacker's exfil server   │
  │  EDS: Poison endpoint list = MITM routing          │
  │  SDS: Issue fake certificates for any service      │
  │                                                     │
  │  Effect: COMPLETE MESH COMPROMISE                   │
  │  All inter-service traffic can be redirected/stolen │
  └─────────────────────────────────────────────────────┘

  istiod is the SINGLE POINT OF TRUST for entire mesh
```

**Hardening istiod:**

```yaml
# 1. Run istiod in dedicated namespace with strict RBAC
# 2. NetworkPolicy: restrict who can reach istiod
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-istiod-access
  namespace: istio-system
spec:
  podSelector:
    matchLabels:
      app: istiod
  ingress:
    # Only from Envoy sidecars (xDS)
    - ports:
        - port: 15010   # xDS gRPC plaintext (should be disabled)
        - port: 15012   # xDS gRPC with mTLS
    # Only from webhooks
    - from:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 15017   # Webhook

---
# 3. Disable insecure xDS port 15010
# pilot-discovery flags:
# --grpcAddr=:15012     (TLS only)
# --httpsAddr=:15017    (webhooks only)
# Remove port 15010 from service

# 4. Audit xDS push events
kubectl logs -n istio-system -l app=istiod | grep "xds push"

# 5. Enable istiod audit logging
kubectl set env deployment/istiod -n istio-system \
  PILOT_ENABLE_PROTOCOL_SNIFFING=false \
  LOG_LEVEL=info
```

---

## Section 4: eBPF-Based Security & Observability

---

### Q31. What is eBPF and why is it a game-changer for Kubernetes network security?

**Answer:**

**eBPF (extended Berkeley Packet Filter)** is a Linux kernel technology that allows running sandboxed programs in the kernel without changing kernel source code or loading kernel modules.

```
eBPF ARCHITECTURE
=============================================================

  Traditional Security (before eBPF):
  ┌─────────────────────────────────────────────────────┐
  │  User Space                                         │
  │  Security Tool (e.g., Falco) reads /proc, netlink  │
  │       ↑ (polling, latency, incomplete data)        │
  │  Kernel Space                                       │
  │  Events happen → userspace is notified late        │
  └─────────────────────────────────────────────────────┘

  eBPF Security (modern):
  ┌─────────────────────────────────────────────────────┐
  │  Kernel Space                                       │
  │  Event occurs (syscall, network packet, kprobe)    │
  │       → eBPF program executes IN KERNEL             │
  │       → Decision made in nanoseconds                │
  │       → Written to eBPF Map (shared memory)        │
  │  User Space                                         │
  │  Security Tool reads eBPF Maps (near-realtime)     │
  └─────────────────────────────────────────────────────┘

  eBPF Hook Points for Security:
  ┌─────────────────────────────────────────────────────┐
  │  XDP   → packet rx before sk_buff allocation       │
  │  TC    → traffic control ingress/egress             │
  │  Socket filter → per-socket packet inspection      │
  │  kprobe/tracepoint → kernel function interception  │
  │  LSM   → Linux Security Module hooks               │
  │  cgroup → per-cgroup network control               │
  └─────────────────────────────────────────────────────┘

  Safety:
  eBPF programs are verified by the kernel verifier:
  - No unbounded loops
  - No out-of-bounds memory access
  - No kernel crash possible (guaranteed to terminate)
```

**Why it's a game-changer:**

| Capability              | iptables/legacy           | eBPF                              |
|-------------------------|---------------------------|-----------------------------------|
| Policy lookup           | O(n) linear scan          | O(1) hash map                     |
| L7 visibility           | Cannot inspect payloads   | Can parse HTTP headers in kernel  |
| Latency                 | Microseconds (syscall)    | Nanoseconds (in-kernel)           |
| Dynamic updates         | Rules flush/reload        | Atomic map updates                |
| Container awareness     | Not native                | cgroup v2 + network namespace     |
| Process-level tracking  | Not possible              | Trace exec, file, network per PID |

---

### Q32. How does Cilium use eBPF to implement NetworkPolicy — trace the path of a packet through eBPF maps.

**Answer:**

```
CILIUM eBPF PACKET PATH
=============================================================

  Pod A (Identity=1001) → Pod B (Identity=2002)

  STEP 1: Pod A sends packet
    Pod A eth0 → veth (cali0 on node)

  STEP 2: TC Egress hook on veth cali0
    eBPF program: cilium_call_policy
    ┌─────────────────────────────────────────────────┐
    │  Look up src identity from ipcache map:         │
    │  ipcache[10.244.1.5] = Identity 1001            │
    │  Look up policy map for Pod A:                  │
    │  policy_map[1001][egress][Identity:2002][8080]  │
    │  → ALLOW                                        │
    │  Stamp packet with identity via DSR/header      │
    └─────────────────────────────────────────────────┘

  STEP 3: Packet traverses node (native routing or tunnel)

  STEP 4: TC Ingress hook on veth of Pod B (node B)
    eBPF program: from-netdev
    ┌─────────────────────────────────────────────────┐
    │  Extract src identity from packet header        │
    │  Identity 1001 (stamped by sending node)        │
    │  Look up Pod B's policy map:                    │
    │  policy_map[2002][ingress][Identity:1001][8080] │
    │  → ALLOW                                        │
    │  Forward to Pod B veth                          │
    └─────────────────────────────────────────────────┘

  STEP 5: Pod B receives packet

  eBPF MAPS INVOLVED:
  ┌───────────────┬──────────────────────────────────┐
  │ Map Name      │ Contents                          │
  ├───────────────┼──────────────────────────────────┤
  │ ipcache       │ IP → Security Identity            │
  │ policy_map    │ Identity + port → allow/deny      │
  │ ct_map        │ Connection tracking table         │
  │ lb_map        │ Service → backend endpoint        │
  │ metrics_map   │ Per-flow packet/byte counters     │
  └───────────────┴──────────────────────────────────┘
```

**Inspecting Maps:**

```bash
# View identity cache
cilium bpf ipcache list

# View policy decisions
cilium bpf policy get <endpoint-id>

# View connection tracking
cilium bpf ct list global

# Monitor policy drops in real-time
cilium monitor --type drop

# Get endpoint identity
cilium endpoint list
```

---

### Q33. Explain Tetragon — how does it implement runtime security using eBPF LSM hooks?

**Answer:**

**Tetragon** (by Cilium/Isovalent) is an eBPF-based runtime security and observability tool. Unlike Falco (which detects syscalls from userspace), Tetragon enforces security policies IN the kernel using eBPF LSM hooks.

```
TETRAGON ARCHITECTURE
=============================================================

  Policy: TracingPolicy (Kubernetes CRD)
  ┌────────────────────────────────────────────────────┐
  │  What to trace: kprobes, tracepoints, LSM hooks    │
  │  What to do: observe, override (block), notify     │
  └───────────────────────────┬────────────────────────┘
                              |
                              | compiled to eBPF bytecode
                              v
  Kernel: eBPF programs attached to hooks
  ┌────────────────────────────────────────────────────┐
  │  LSM hook: security_file_open                      │
  │  kprobe: tcp_connect                               │
  │  tracepoint: sys_execve                            │
  │                                                    │
  │  Can: BLOCK syscall (return -EPERM before exec)    │
  │  Can: Observe and emit event to ring buffer        │
  │  Can: Override return values                       │
  └───────────────────────────┬────────────────────────┘
                              |
                              v
  Tetragon Agent (DaemonSet) reads ring buffer
  → Enriches with K8s metadata (pod, namespace, labels)
  → Exports to: gRPC, Kafka, Fluentd, Prometheus

  TIMELINE COMPARISON:
  Falco:   syscall → userspace → detect → alert (AFTER the fact)
  Tetragon: syscall → eBPF LSM → BLOCK (before completion)
```

**TracingPolicy Example:**

```yaml
# Block execution of curl/wget inside any pod
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: block-curl-wget
spec:
  kprobes:
    - call: "security_bprm_check"
      syscall: false
      return: true
      args:
        - index: 0
          type: "linux_binprm"
      selectors:
        - matchArgs:
            - index: 0
              operator: "Postfix"
              values:
                - "/usr/bin/curl"
                - "/usr/bin/wget"
          matchActions:
            - action: Sigkill    # Kill the process

---
# Detect and alert on crypto miner network patterns
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-mining-ports
spec:
  kprobes:
    - call: "tcp_connect"
      syscall: false
      args:
        - index: 0
          type: "sock"
      selectors:
        - matchArgs:
            - index: 0
              operator: "DPort"
              values:
                - "4444"   # common mining pool port
                - "3333"   # stratum protocol
          matchActions:
            - action: Sigkill
              argFqdn: true
```

---

### Q34. How do you use eBPF to detect and prevent container escapes in real time?

**Answer:**

```
CONTAINER ESCAPE ATTACK VECTORS & eBPF DETECTION
=============================================================

  ESCAPE TYPE 1: runc CVE (e.g., CVE-2019-5736)
  Attack: Overwrite host /proc/self/exe via /proc/pid/exe
  eBPF Detection:
  Hook: security_file_open on /proc/*/exe
  Check: if opener is container process AND path is /proc
         AND file is executable → BLOCK + ALERT

  ESCAPE TYPE 2: Privileged container breakout
  Attack: mount -t cgroup → manipulate cgroup release_agent
  eBPF Detection:
  Hook: security_sb_mount
  Check: if mount type == cgroup AND caller != init_pid → BLOCK

  ESCAPE TYPE 3: Kernel exploit (privilege escalation)
  Attack: exploit kernel bug → change credentials → CAPABILITY gain
  eBPF Detection:
  Hook: commit_creds (when credentials change)
  Check: if uid changes from non-root to root
         AND no legitimate setuid execution → ALERT + KILL

  ESCAPE TYPE 4: /proc/self/mem write
  Attack: write to /proc/self/mem to modify process memory
  eBPF Detection:
  Hook: security_file_permission with MAY_WRITE
  Check: if path matches /proc/*/mem AND caller is container → BLOCK
```

**Falco Rule for Container Escape Detection:**

```yaml
# Falco rule: detect namespace change (container escape indicator)
- rule: Container Namespace Change
  desc: Detect process attempting to change namespaces
  condition: >
    spawned_process and
    container and
    proc.name in (nsenter, unshare) and
    not proc.pname in (bash, sh)
  output: >
    Namespace change attempted
    (user=%user.name command=%proc.cmdline
     container=%container.name pod=%k8s.pod.name)
  priority: CRITICAL
  tags: [container, escape]

---
# Tetragon TracingPolicy: monitor credential changes
apiVersion: cilium.io/v1alpha1
kind: TracingPolicy
metadata:
  name: detect-priv-escalation
spec:
  kprobes:
    - call: "commit_creds"
      syscall: false
      args:
        - index: 0
          type: "cred"
      selectors:
        - matchArgs:
            - index: 0
              operator: "Equal"
              values:
                - "0"    # uid == 0 (root)
          matchActions:
            - action: Post    # emit security event
```

---

### Q35. What is XDP (eXpress Data Path) and how is it used for high-performance DDoS mitigation in Kubernetes?

**Answer:**

**XDP** is an eBPF hook point at the **earliest possible point** in the Linux network stack — before the kernel allocates an `sk_buff` (socket buffer). This makes it extremely fast.

```
XDP PACKET PROCESSING POSITIONS
=============================================================

  Network Card (NIC)
         |
    [XDP_OFFLOAD]   ← eBPF runs ON the NIC hardware (fastest)
         |
  Driver (kernel)
         |
    [XDP_DRIVER]    ← eBPF runs in NIC driver, before sk_buff
         |
  Generic XDP
         |
    [XDP_GENERIC]   ← eBPF runs after sk_buff (fallback mode)
         |
  netfilter/iptables ← traditional stack (much slower)
         |
  Socket/Application

  XDP Actions:
  XDP_PASS   → continue to normal stack
  XDP_DROP   → drop packet immediately (fastest drop possible)
  XDP_TX     → retransmit out same interface (for reflection)
  XDP_REDIRECT → redirect to another interface or userspace

  Performance:
  iptables DROP: ~1-2 million pkts/sec
  XDP DROP:      ~14-24 million pkts/sec (per core)
  XDP_OFFLOAD:   ~100+ million pkts/sec
```

**DDoS Mitigation with XDP in Kubernetes:**

```c
// Simplified XDP program for rate limiting
// (runs in kernel, written in restricted C)
SEC("xdp")
int xdp_ddos_mitigation(struct xdp_md *ctx) {
    void *data = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;
    
    struct ethhdr *eth = data;
    if (eth + 1 > data_end) return XDP_PASS;
    
    struct iphdr *ip = data + sizeof(*eth);
    if (ip + 1 > data_end) return XDP_PASS;
    
    // Look up source IP in blocklist map
    __u32 src_ip = ip->saddr;
    __u64 *count = bpf_map_lookup_elem(&blocklist_map, &src_ip);
    
    if (count) {
        // IP is in blocklist — drop immediately
        return XDP_DROP;
    }
    
    // Rate limit: track per-IP packet count per second
    __u64 *pkt_count = bpf_map_lookup_elem(&rate_map, &src_ip);
    if (pkt_count && *pkt_count > RATE_LIMIT_PPS) {
        // Add to blocklist
        bpf_map_update_elem(&blocklist_map, &src_ip, &ONE, BPF_ANY);
        return XDP_DROP;
    }
    
    return XDP_PASS;
}
```

**Cilium's XDP Integration:**

```bash
# Enable XDP acceleration in Cilium
helm upgrade cilium cilium/cilium \
  --set loadBalancer.acceleration=native \    # XDP native mode
  --set loadBalancer.mode=dsr \              # Direct Server Return
  --set bpf.masquerade=true

# Verify XDP is active
cilium status | grep XDP
# XDP Acceleration:   Native
```

---

## Section 5: Cloud Provider CNI Plugins

---

### Q36. How does AWS VPC CNI work, and what are its specific security risks compared to overlay CNIs?

**Answer:**

**AWS VPC CNI** assigns real VPC IP addresses to pods using Elastic Network Interfaces (ENIs) attached to EC2 instances.

```
AWS VPC CNI ARCHITECTURE
=============================================================

  EC2 Node: m5.large
  ┌─────────────────────────────────────────────────────┐
  │  Primary ENI (eth0): 10.0.1.10                     │
  │  Secondary ENI (eth1): 10.0.1.20                   │
  │  Secondary ENI (eth2): 10.0.1.30                   │
  │                                                     │
  │  Each ENI has multiple secondary private IPs:       │
  │  eth1: [10.0.1.101, 10.0.1.102, 10.0.1.103...]     │
  │         ↓            ↓            ↓                 │
  │       Pod A         Pod B         Pod C             │
  │  (each pod gets a real VPC IP)                      │
  └─────────────────────────────────────────────────────┘

  Pod IP = Real VPC IP → routable from any VPC resource
  No overlay encapsulation → No performance overhead

  ENI Limits (security-critical):
  m5.large: max 3 ENIs × 10 IPs = 30 pods max
  Exhausting ENIs → pod scheduling fails
```

**VPC CNI Specific Security Risks:**

```
RISK 1: Security Group Per Pod (SGPP) misconfiguration
  VPC CNI supports assigning VPC Security Groups directly to pods
  Misconfigured SG → pod can reach RDS, ElastiCache directly
  No Kubernetes NetworkPolicy layer needed → but also no policy!

RISK 2: IAM Role Escalation via IRSA
  aws-node DaemonSet needs IAM permissions:
  ec2:AssignPrivateIpAddresses
  ec2:AttachNetworkInterface
  ec2:CreateNetworkInterface
  If node's instance role is over-permissive:
  Compromised node → attacker can create ENIs, attach to other instances

RISK 3: Pod IP directly accessible from AWS network
  RDS Security Group allows 10.0.0.0/8?
  Compromised pod (10.0.1.101) can reach RDS directly
  No NAT, no filtering — direct VPC routing

RISK 4: IP exhaustion DoS
  Attacker pod spawns many containers rapidly
  ENI secondary IPs exhausted → new pods cannot start
  Node-level DoS affecting entire workload
```

**Security Configuration:**

```bash
# Enable Security Groups for Pods (pod-level SGs)
kubectl set env daemonset aws-node -n kube-system \
  ENABLE_POD_ENI=true

# Annotate pod to use specific SG
kubectl annotate pod my-pod \
  vpc.amazonaws.com/pod-eni='[{"eniId":"eni-xxx","ifAddress":"0a:58:0a:00:01:01","privateIp":"10.0.1.101","vlanId":1,"subnetCidr":"10.0.1.0/24"}]'

# NetworkPolicy enforcement with VPC CNI
# Must install a network policy provider alongside:
kubectl apply -f https://raw.githubusercontent.com/aws/amazon-vpc-cni-k8s/main/config/master/aws-k8s-cni.yaml
# Plus: Calico or Cilium for NetworkPolicy enforcement
# VPC CNI alone does NOT enforce NetworkPolicy!
```

---

### Q37. Explain Azure CNI (Azure Container Networking Interface) and its security model compared to kubenet.

**Answer:**

```
AZURE NETWORKING COMPARISON
=============================================================

  kubenet (basic):
  ┌──────────────────────────────────────────────────────┐
  │  Nodes get Azure VNet IPs                           │
  │  Pods get RFC1918 IPs from node-local CIDR          │
  │  NAT required for pod→external communication        │
  │  Azure doesn't know about pod IPs                   │
  │  No VNet Network Security Groups per pod            │
  └──────────────────────────────────────────────────────┘

  Azure CNI (advanced):
  ┌──────────────────────────────────────────────────────┐
  │  Pods get REAL Azure VNet IPs                       │
  │  Pods visible as first-class VNet resources         │
  │  VNet NSGs can target pod IPs directly              │
  │  Private Link services can target pod IPs           │
  │  No NAT for inter-pod communication                 │
  └──────────────────────────────────────────────────────┘

  Azure CNI Overlay (newer):
  ┌──────────────────────────────────────────────────────┐
  │  Pods get private overlay IPs (not VNet IPs)        │
  │  Solves IP exhaustion problem of Azure CNI          │
  │  VNet sees only node IPs                            │
  │  Better IP efficiency for large clusters            │
  └──────────────────────────────────────────────────────┘
```

**Security Implications:**

```
Azure CNI RISKS:
1. VNet IP exhaustion
   Azure VNets have limited IPs per subnet
   Pods consume real VNet IPs → large clusters exhaust subnets

2. NSG bypass
   VNet NSG rules based on IP ranges
   Pod IP churn → NSG rules become stale
   Must update NSGs on pod lifecycle events (automation required)

3. Lateral movement risk
   Pod with VNet IP → can reach any Azure service
   Azure SQL, Storage, Key Vault on VNet → reachable from pods
   Requires: Private Endpoints + NSG + NetworkPolicy layering

4. No NetworkPolicy enforcement by default
   Azure CNI alone doesn't enforce Kubernetes NetworkPolicy
   Must enable: Azure Network Policy Manager OR Calico
   kubectl get pods -n kube-system | grep azure-npm   # Azure NPM
```

**Enabling Network Policy:**

```bash
# Create AKS cluster with Azure Network Policy
az aks create \
  --name my-cluster \
  --resource-group my-rg \
  --network-plugin azure \
  --network-policy azure \    # Azure NPM
  # OR:
  --network-policy calico     # Calico on Azure CNI

# Verify NPM is running
kubectl get pods -n kube-system -l component=azure-npm
```

---

### Q38. How does GKE Dataplane V2 (based on Cilium/eBPF) change the security model of Google Kubernetes Engine?

**Answer:**

```
GKE DATAPLANE EVOLUTION
=============================================================

  GKE Legacy (iptables-based):
  ┌────────────────────────────────────────────────────┐
  │  iptables rules for NetworkPolicy                 │
  │  kube-proxy for service routing                   │
  │  No L7 visibility                                 │
  │  Scalability limits at ~10k+ rules               │
  └────────────────────────────────────────────────────┘

  GKE Dataplane V2 (eBPF/Cilium-based):
  ┌────────────────────────────────────────────────────┐
  │  eBPF programs replace iptables for policy        │
  │  kube-proxy replaced by Cilium eBPF service map  │
  │  Full NetworkPolicy support (L3-L4)               │
  │  Built-in network visibility (flow logs)          │
  │  Scalability: consistent O(1) lookups             │
  └────────────────────────────────────────────────────┘
```

**GKE Dataplane V2 Security Features:**

```
1. Network Policy Logging
   Every NetworkPolicy drop logged with:
   - Source/dest pod, namespace
   - Policy that caused the drop
   - Timestamp, direction

   View logs:
   kubectl logs -n kube-system -l k8s-app=cilium | grep "drop"
   
   Cloud Logging integration:
   resource.type="k8s_node"
   logName=~"networkpolicy"

2. FQDN-based Policy (GKE Autopilot)
   Allow pods to reach specific FQDNs:
   Not available in standard Kubernetes NetworkPolicy

3. Multi-NIC support
   Pods with multiple network interfaces
   Different security zones per interface

4. Intranode Visibility
   See pod-to-pod traffic ON SAME NODE
   Traditional: sniffer on node can't see same-node traffic
   eBPF: full visibility including intranode flows
```

**Enabling:**

```bash
# Create GKE cluster with Dataplane V2
gcloud container clusters create my-cluster \
  --enable-dataplane-v2 \
  --enable-network-policy \
  --region us-central1

# Verify Cilium is running
kubectl get pods -n kube-system -l k8s-app=cilium

# Enable network policy logging
gcloud container clusters update my-cluster \
  --enable-network-policy-logging \
  --region us-central1
```

---

### Q39. What is Antrea CNI and how does its security model leverage Open vSwitch (OVS)?

**Answer:**

**Antrea** is a CNI plugin developed by VMware that uses **Open vSwitch (OVS)** as the data plane for both connectivity and policy enforcement.

```
ANTREA ARCHITECTURE
=============================================================

  Control Plane: antrea-controller (Deployment)
  ┌──────────────────────────────────────────────────────┐
  │  Watches: NetworkPolicy, Pod, Namespace, Node        │
  │  Computes: policy rules per node                     │
  │  Pushes: computed rules to antrea-agents             │
  └──────────────────────────────────────────────────────┘
            |
            | antrea gRPC channel
            v
  Data Plane: antrea-agent (DaemonSet on each node)
  ┌──────────────────────────────────────────────────────┐
  │  Programs OVS (Open vSwitch) flows                  │
  │  Handles: IPAM, tunnel setup, policy enforcement    │
  │  OVS Pipeline:                                      │
  │  ┌────────────────────────────────────────────────┐ │
  │  │ Table 0:  Spoofing check (src MAC/IP verify)   │ │
  │  │ Table 10: ARP handling                         │ │
  │  │ Table 20: Ingress policy                       │ │
  │  │ Table 30: Route lookup (tunnel or local)       │ │
  │  │ Table 40: Egress policy                        │ │
  │  │ Table 50: Output (to pod veth or tunnel)       │ │
  │  └────────────────────────────────────────────────┘ │
  └──────────────────────────────────────────────────────┘
```

**Antrea Security Features:**

```yaml
# Antrea ClusterNetworkPolicy (CNP) — deny specific CIDR
apiVersion: crd.antrea.io/v1alpha1
kind: ClusterNetworkPolicy
metadata:
  name: block-metadata-service
spec:
  priority: 1
  tier: SecurityOps    # Custom tier, higher priority than application tier
  appliedTo:
    - podSelector: {}  # all pods
  egress:
    - action: Drop
      to:
        - ipBlock:
            cidr: 169.254.169.254/32

---
# Antrea NetworkPolicy with L7 (Antrea-proxy integration)
apiVersion: crd.antrea.io/v1alpha1
kind: NetworkPolicy
metadata:
  name: allow-http-only
  namespace: production
spec:
  priority: 5
  appliedTo:
    - podSelector:
        matchLabels:
          app: backend
  ingress:
    - action: Allow
      from:
        - podSelector:
            matchLabels:
              app: frontend
      l7Protocols:
        - http:
            method: GET
            path: /api/*
```

**OVS Anti-Spoofing:**

```bash
# Antrea anti-spoofing via OVS pipeline
# Table 0 drops packets with unexpected src MAC or IP
# This prevents ARP spoofing within the node
ovs-ofctl dump-flows br-int table=0 | grep "drop"

# Verify OVS pipeline
ovs-ofctl dump-flows br-int | sort -t , -k 2 -n
```

---

### Q40. Compare Calico, Cilium, Flannel, and Weave from a security perspective — which would you choose for a PCI-DSS compliant cluster?

**Answer:**

```
CNI SECURITY COMPARISON MATRIX
=============================================================

  Feature              | Calico | Cilium | Flannel | Weave
  ─────────────────────────────────────────────────────────
  NetworkPolicy        |  ✅    |   ✅   |   ✗     |  ✅
  GlobalNetworkPolicy  |  ✅    |   ✅   |   ✗     |  ✗
  L7 Policy            |  ✅*   |   ✅   |   ✗     |  ✗
  mTLS/Encryption      |  WG✅  |  WG✅  |   ✗     |  ✅
  eBPF data plane      |  ✅    |   ✅   |   ✗     |  ✗
  FQDN-based policy    |  ✅    |   ✅   |   ✗     |  ✗
  HostEndpoint policy  |  ✅    |   ✅   |   ✗     |  ✗
  Flow logs/observ.    |  ✅    |   ✅   |   ✗     |  ✗
  BGP routing          |  ✅    |  ✅β   |   ✗     |  ✗
  VXLAN overlay        |  ✅    |   ✅   |   ✅     |  ✅
  Maturity             |  High  |  High  |  High   |  Med
  Community            |  Large |  Large |  Large  |  Small
  *L7 with Envoy

  WG = WireGuard encryption
```

**PCI-DSS Specific Requirements vs CNI Capabilities:**

```
PCI-DSS Req 1: Network segmentation (firewall controls)
→ Need: Fine-grained NetworkPolicy
→ Best: Calico or Cilium (both have explicit deny rules)

PCI-DSS Req 2: Default deny, remove unused protocols
→ Need: GlobalNetworkPolicy with deny-all baseline
→ Best: Calico (mature GNP) or Cilium (CCNP)

PCI-DSS Req 4: Encrypt data in transit (cardholder data)
→ Need: Pod-to-pod encryption
→ Best: Calico (WireGuard) or Cilium (WireGuard)
→ OR: Service mesh (Istio STRICT mTLS)

PCI-DSS Req 10: Log all access to network resources
→ Need: Flow logging, policy audit
→ Best: Cilium (Hubble) or Calico Enterprise
→ Export to SIEM (Splunk, Elastic)

PCI-DSS Req 11: Regularly test security systems
→ Need: Policy testing tools
→ Best: Cilium (cilium connectivity test, Hubble CLI)
```

**Recommendation for PCI-DSS:**

```
PRIMARY CHOICE: Cilium
Reasons:
1. eBPF-based (no iptables bypass risk from CAP_NET_ADMIN)
2. Hubble: built-in flow observability (satisfies Req 10)
3. WireGuard encryption (satisfies Req 4)
4. L7 policy (HTTP method-level control for card data APIs)
5. FQDN policy (allowlist payment gateway domains)
6. CiliumClusterwideNetworkPolicy (centralized deny rules)
7. Identity-based (not IP — more resilient to IP churn)

SECONDARY CHOICE: Calico
For teams already invested in Calico ecosystem,
add Calico Enterprise for:
- Compliance reporting
- Flow logs to Elasticsearch
- GUI-based policy management
```

---

## Section 6: Zero Trust Networking in Kubernetes

---

### Q41. Define Zero Trust in the context of Kubernetes networking — what are the five pillars and how do CNI plugins enable them?

**Answer:**

**Zero Trust** is a security model built on: "Never trust, always verify." In traditional networking, being inside the corporate network grants implicit trust. Zero Trust eliminates this assumption.

```
ZERO TRUST FIVE PILLARS IN KUBERNETES
=============================================================

  PILLAR 1: Identity Verification
  ┌─────────────────────────────────────────────────────┐
  │  "Who are you?" — for every request, every time    │
  │  K8s: SPIFFE-based workload identity (mTLS cert)   │
  │  CNI: Cilium identity from pod labels              │
  │  Implementation: Istio PeerAuthentication STRICT   │
  │                  + AuthorizationPolicy per service  │
  └─────────────────────────────────────────────────────┘

  PILLAR 2: Device/Workload Health
  ┌─────────────────────────────────────────────────────┐
  │  "Is your runtime environment trusted?"            │
  │  K8s: Pod Security Standards (restricted)          │
  │  Implementation: OPA Gatekeeper + Falco healthcheck│
  │                  Node attestation (SPIRE)          │
  └─────────────────────────────────────────────────────┘

  PILLAR 3: Least Privilege Access
  ┌─────────────────────────────────────────────────────┐
  │  "What's the minimum access needed?"               │
  │  K8s: RBAC + NetworkPolicy default-deny            │
  │  CNI: Cilium L7 policy (GET /health only)          │
  │  Implementation: deny-all + explicit allows        │
  └─────────────────────────────────────────────────────┘

  PILLAR 4: Micro-segmentation
  ┌─────────────────────────────────────────────────────┐
  │  "Segment at the workload level, not VLAN"         │
  │  CNI: Per-pod policy, not per-subnet               │
  │  Implementation: NetworkPolicy per app label       │
  │                  Namespace isolation               │
  └─────────────────────────────────────────────────────┘

  PILLAR 5: Continuous Monitoring
  ┌─────────────────────────────────────────────────────┐
  │  "Verify and re-verify continuously"               │
  │  CNI: Hubble flow logs, Tetragon syscall audit     │
  │  Implementation: Real-time anomaly detection       │
  │                  SIEM integration                  │
  └─────────────────────────────────────────────────────┘
```

---

### Q42. What is the BeyondProd model and how does it apply to Kubernetes workload security?

**Answer:**

**BeyondProd** is Google's Zero Trust model for production infrastructure (analogy to BeyondCorp for employees). It defines security from service-to-service perspective.

```
BEYONDPROD PRINCIPLES IN KUBERNETES
=============================================================

  Principle 1: Mutual authentication between all services
  ┌──────────────────────────────────────────────────────┐
  │  Every service call must prove identity             │
  │  No trust based on IP/network location              │
  │  Implementation: Istio mTLS STRICT + SPIFFE SVIDs   │
  └──────────────────────────────────────────────────────┘

  Principle 2: Binary authorization / Workload provenance
  ┌──────────────────────────────────────────────────────┐
  │  Only attested/signed workloads can deploy          │
  │  Implementation: Binary Authorization (GKE)         │
  │    - Every image must have attestation              │
  │    - Attestation signed by trusted authority        │
  │    - AdmissionWebhook validates before scheduling   │
  └──────────────────────────────────────────────────────┘

  Principle 3: Fine-grained authorization
  ┌──────────────────────────────────────────────────────┐
  │  Policy based on: who + what + when + context       │
  │  Implementation: Istio AuthorizationPolicy          │
  │    - source.principal (SPIFFE identity)             │
  │    - request.method, request.url_path               │
  │    - request.headers[x-custom-header]               │
  └──────────────────────────────────────────────────────┘

  Principle 4: Runtime protection
  ┌──────────────────────────────────────────────────────┐
  │  Detect and respond to runtime anomalies            │
  │  Implementation: Falco + Tetragon + SIEM            │
  └──────────────────────────────────────────────────────┘
```

**Binary Authorization Example:**

```yaml
# GKE Binary Authorization Policy
# Only allow images attested by our CI/CD pipeline
apiVersion: binaryauthorization.googleapis.com/v1
kind: Policy
metadata:
  name: prod-policy
spec:
  defaultAdmissionRule:
    evaluationMode: REQUIRE_ATTESTATION
    enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
    requireAttestationsBy:
      - projects/my-project/attestors/ci-pipeline-attestor
  clusterAdmissionRules:
    us-central1.my-prod-cluster:
      evaluationMode: REQUIRE_ATTESTATION
      enforcementMode: ENFORCED_BLOCK_AND_AUDIT_LOG
```

---

### Q43. How do you implement workload identity federation between Kubernetes and cloud provider IAM (AWS IRSA, GKE Workload Identity)?

**Answer:**

```
WORKLOAD IDENTITY FEDERATION
=============================================================

  Problem: How does a K8s pod authenticate to AWS/GCP
           WITHOUT storing long-lived credentials?

  Solution: Federate K8s ServiceAccount identity to IAM

  AWS IRSA (IAM Roles for Service Accounts):
  ┌──────────────────────────────────────────────────────┐
  │  OIDC Flow:                                         │
  │  1. EKS exposes OIDC endpoint                       │
  │     https://oidc.eks.us-east-1.amazonaws.com/id/XXX │
  │  2. Pod's ServiceAccount JWT signed by OIDC issuer  │
  │  3. Pod calls STS:AssumeRoleWithWebIdentity         │
  │     passing: JWT token + Role ARN                   │
  │  4. STS validates JWT signature with OIDC endpoint  │
  │  5. Checks IAM Trust Policy allows this SA          │
  │  6. Returns temporary credentials (15min-12h TTL)   │
  └──────────────────────────────────────────────────────┘

  IAM Trust Policy:
  {
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789:oidc-provider/oidc.eks.us-east-1.amazonaws.com/id/XXX"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "oidc.eks.us-east-1.amazonaws.com/id/XXX:sub":
            "system:serviceaccount:production:payment-service"
        }
      }
    }]
  }
```

**Setup:**

```bash
# AWS IRSA Setup
# 1. Create IAM OIDC provider
eksctl utils associate-iam-oidc-provider \
  --cluster my-cluster \
  --approve

# 2. Create IAM role with trust policy
eksctl create iamserviceaccount \
  --name payment-service \
  --namespace production \
  --cluster my-cluster \
  --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess \
  --approve \
  --role-name payment-service-role

# 3. Annotate ServiceAccount
kubectl annotate serviceaccount payment-service \
  -n production \
  eks.amazonaws.com/role-arn=arn:aws:iam::123456789:role/payment-service-role

# GKE Workload Identity
gcloud iam service-accounts add-iam-policy-binding \
  gcp-service-account@project.iam.gserviceaccount.com \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:project.svc.id.goog[production/payment-service]"

kubectl annotate serviceaccount payment-service \
  -n production \
  iam.gke.io/gcp-service-account=gcp-service-account@project.iam.gserviceaccount.com
```

**Security Hardening:**

```
1. Use condition: StringEquals (not StringLike) in trust policy
   StringLike with wildcards → any SA in namespace can assume role

2. Scope IAM permissions to minimum
   Never attach AdministratorAccess to pod roles

3. Enable audit logging
   CloudTrail: AssumeRoleWithWebIdentity events
   Alert on: unexpected role assumptions, high-frequency calls

4. Rotate OIDC provider regularly (EKS cluster recreation is disruptive)
   Monitor: expiry of OIDC thumbprint certificates
```

---

### Q44. How do you detect and prevent lateral movement in a Kubernetes cluster at the network layer?

**Answer:**

```
LATERAL MOVEMENT IN KUBERNETES
=============================================================

  Attack Chain:
  External exploit → Initial pod compromise
                          |
             ┌────────────┼────────────┐
             v            v            v
        Pod-to-pod    API server    Cloud metadata
         hopping       access         SSRF
             |            |            |
        Reach DB     Privilege      Steal IAM
         pods         escalation     credentials
             |
        Data exfiltration

  Detection Indicators:
  ┌─────────────────────────────────────────────────────┐
  │  1. Pod making connections to pods it never talked  │
  │     to before (new network edge in topology)        │
  │  2. Port scanning behavior (sequential IPs)         │
  │  3. DNS queries for all service names               │
  │  4. Connections to kube-apiserver:6443 from pods    │
  │     not expected to use API                         │
  │  5. Connections to 169.254.169.254 (metadata SSRF)  │
  └─────────────────────────────────────────────────────┘
```

**Detection with Hubble (Cilium):**

```bash
# Monitor all flows from a compromised pod
hubble observe \
  --pod production/compromised-pod \
  --follow

# Detect port scan pattern
hubble observe \
  --verdict DROPPED \
  --namespace production \
  --follow | \
  awk '{print $4}' | sort | uniq -c | sort -rn | head

# Alert on connections to kube-apiserver
hubble observe \
  --to-pod kube-system/kube-apiserver \
  --namespace production \
  --follow
```

**Prevention Policies:**

```yaml
# Deny pod-to-pod lateral movement
# Pods should only talk to their allowed dependencies
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: prevent-lateral-movement
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: frontend
  policyTypes:
    - Egress
  egress:
    # Only allowed backend
    - to:
        - podSelector:
            matchLabels:
              app: backend
      ports:
        - port: 8080
    # DNS only
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP
    # Block: database, other services, API server

---
# Calico: Block access to API server from workload pods
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: block-api-server-access
spec:
  order: 10
  selector: "!has(node-role.kubernetes.io/control-plane)"
  egress:
    - action: Deny
      destination:
        ports: [6443, 443]
        nets:
          - <control-plane-CIDR>
```

---

### Q45. What is micro-segmentation and how do you implement it for a 50-microservice Kubernetes application?

**Answer:**

**Micro-segmentation** means applying security policy at the individual workload level (per pod/service), rather than at the network perimeter or VLAN level.

```
MICRO-SEGMENTATION STRATEGY FOR 50 SERVICES
=============================================================

  Traditional (macro-segmentation):
  [Frontend VLAN] → [Backend VLAN] → [DB VLAN]
  Any service in frontend can reach any backend
  
  Micro-segmentation:
  frontend-A → backend-A (port 8080, GET /api only)
  frontend-A ✗ backend-B (blocked)
  backend-A → database-A (port 5432, only)
  backend-A ✗ database-B (blocked)

  Scale Strategy:
  ┌─────────────────────────────────────────────────────┐
  │  Phase 1: Service Map (dependency analysis)         │
  │  Tool: Hubble/Kiali → export actual flow graph     │
  │  Result: JSON map of who talks to whom              │
  │                                                     │
  │  Phase 2: Policy Generation                         │
  │  Tool: network-policy-generator (Calico/Cilium)    │
  │  Input: flow graph                                  │
  │  Output: NetworkPolicy YAML per service             │
  │                                                     │
  │  Phase 3: Audit Mode Validation                     │
  │  Apply policies in audit/log mode                  │
  │  Run for 72h, check for unexpected drops           │
  │                                                     │
  │  Phase 4: Enforcement                               │
  │  Switch to enforce mode namespace by namespace     │
  └─────────────────────────────────────────────────────┘
```

**Policy Template Pattern:**

```yaml
# Template for each microservice (fill in per service)
# service: payment-processor
# allowed-ingress: [order-service, fraud-detector]
# allowed-egress: [payment-gateway-api, database, dns]

---
# Generated NetworkPolicy for payment-processor
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: payment-processor-policy
  namespace: production
  labels:
    managed-by: policy-generator
    service: payment-processor
spec:
  podSelector:
    matchLabels:
      app: payment-processor
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: order-service
      ports:
        - port: 8080
    - from:
        - podSelector:
            matchLabels:
              app: fraud-detector
      ports:
        - port: 8080
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP
    - to:
        - podSelector:
            matchLabels:
              app: postgresql
              tier: payment
      ports:
        - port: 5432
```

---

## Section 7: Runtime & Pod Security

---

### Q46. Explain Pod Security Standards (PSS) and how they replaced PodSecurityPolicy — what are the three profiles?

**Answer:**

**PodSecurityPolicy (PSP)** was deprecated in K8s 1.21 and removed in 1.25. **Pod Security Standards (PSS)** replaced it with a simpler, built-in admission controller.

```
POD SECURITY STANDARDS PROFILES
=============================================================

  PRIVILEGED (no restrictions):
  ┌─────────────────────────────────────────────────────┐
  │  Allows everything                                  │
  │  Use: CNI plugins, storage drivers, node agents    │
  │  NOT for application workloads                     │
  └─────────────────────────────────────────────────────┘

  BASELINE (minimal restrictions):
  ┌─────────────────────────────────────────────────────┐
  │  Blocks: privileged containers                     │
  │  Blocks: hostPID, hostIPC, hostNetwork             │
  │  Blocks: hostPath volumes (dangerous subset)       │
  │  Blocks: dangerous capabilities (SYS_ADMIN, etc.) │
  │  Allows: most standard workloads                   │
  │  Use: General-purpose apps                         │
  └─────────────────────────────────────────────────────┘

  RESTRICTED (strongest):
  ┌─────────────────────────────────────────────────────┐
  │  All Baseline restrictions PLUS:                   │
  │  Requires: runAsNonRoot: true                      │
  │  Requires: seccompProfile (RuntimeDefault/Localhost)│
  │  Requires: readOnlyRootFilesystem: true            │
  │  Disallows: ALL capabilities (must drop ALL)       │
  │  Allows only: NET_BIND_SERVICE (if needed)         │
  │  Use: High-security apps (payment, auth services)  │
  └─────────────────────────────────────────────────────┘
```

**Enforcement Modes:**

```
enforce: Reject pods that violate the policy
audit:   Allow pods but log violation to audit log
warn:    Allow pods but display admission warning
```

**Implementation:**

```yaml
# Apply Restricted to namespace
apiVersion: v1
kind: Namespace
metadata:
  name: production
  labels:
    pod-security.kubernetes.io/enforce: restricted
    pod-security.kubernetes.io/enforce-version: v1.28
    pod-security.kubernetes.io/audit: restricted
    pod-security.kubernetes.io/audit-version: v1.28
    pod-security.kubernetes.io/warn: restricted
    pod-security.kubernetes.io/warn-version: v1.28

---
# Compliant pod spec for Restricted profile
apiVersion: v1
kind: Pod
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 1000
    runAsGroup: 3000
    fsGroup: 2000
    seccompProfile:
      type: RuntimeDefault
  containers:
    - name: app
      securityContext:
        allowPrivilegeEscalation: false
        readOnlyRootFilesystem: true
        capabilities:
          drop: ["ALL"]
      volumeMounts:
        - name: tmp
          mountPath: /tmp    # writable tmp for apps that need it
  volumes:
    - name: tmp
      emptyDir: {}
```

---

### Q47. What is seccomp and how do you use it to restrict system calls in Kubernetes pods?

**Answer:**

**seccomp (secure computing mode)** is a Linux kernel feature that restricts which system calls a process can make. Reducing the syscall surface dramatically limits exploit potential.

```
SYSCALL RESTRICTION MODEL
=============================================================

  Linux has ~400+ system calls
  A typical web app uses: ~50-100 system calls
  An attacker exploit may use: specific dangerous syscalls
  
  Danger syscalls an app rarely needs:
  ┌────────────────────────────────────────────────┐
  │  ptrace    → process injection                 │
  │  mount     → filesystem mount (escape risk)   │
  │  clone     → namespace creation (escape risk) │
  │  unshare   → namespace separation             │
  │  keyctl    → kernel keyring manipulation      │
  │  sethostname→ hostname change                 │
  │  pivot_root→ chroot escape                    │
  └────────────────────────────────────────────────┘

  seccomp profile types:
  RuntimeDefault: container runtime's default profile
                  (reasonable for most apps)
  Localhost:      custom JSON profile loaded from node
  Unconfined:     no restriction (default — dangerous)
```

**Custom seccomp Profile:**

```json
{
  "defaultAction": "SCMP_ACT_ERRNO",
  "architectures": ["SCMP_ARCH_X86_64", "SCMP_ARCH_AARCH64"],
  "syscalls": [
    {
      "names": [
        "accept4", "bind", "brk", "close", "connect",
        "epoll_create1", "epoll_ctl", "epoll_wait",
        "exit", "exit_group", "fcntl", "fstat", "futex",
        "getpid", "getsockname", "getsockopt", "listen",
        "lseek", "mmap", "mprotect", "munmap", "nanosleep",
        "openat", "poll", "read", "recvfrom", "sendto",
        "setsockopt", "socket", "stat", "write"
      ],
      "action": "SCMP_ACT_ALLOW"
    }
  ]
}
```

**Deploying Custom Profile:**

```bash
# Copy profile to node (via DaemonSet or node provisioning)
# Profile path: /var/lib/kubelet/seccomp/profiles/web-app.json

# Apply in pod spec
```

```yaml
spec:
  securityContext:
    seccompProfile:
      type: Localhost
      localhostProfile: profiles/web-app.json
```

**Profiling Tool — Generate Profile from Running App:**

```bash
# Use strace to capture syscalls during testing
strace -f -e trace=all -o syscalls.log ./my-app

# Or use OCI hook: container-syscall-profiler
# Or: Tetragon to capture syscalls per container

# Convert captured syscalls to seccomp JSON
# Tool: go-seccomp-bpf (Elastic)
```

---

### Q48. Explain Linux capabilities in Kubernetes containers and which ones are security-critical to drop.

**Answer:**

**Linux Capabilities** divide root privileges into distinct units. Instead of "all or nothing" root, processes can have specific subsets.

```
CAPABILITY MAP FOR KUBERNETES
=============================================================

  CRITICAL TO DROP (dangerous capabilities):
  ┌──────────────────────────────────────────────────────┐
  │  CAP_SYS_ADMIN   → "god mode" — mount, namespaces,  │
  │                    device control, cgroup management │
  │                    MOST COMMON container escape vec  │
  │                                                      │
  │  CAP_NET_ADMIN   → iptables manipulation, network   │
  │                    device config, interface create   │
  │                    Can flush NetworkPolicy rules!    │
  │                                                      │
  │  CAP_NET_RAW     → raw sockets, packet crafting     │
  │                    ARP spoofing, ICMP flooding       │
  │                    ping command uses this            │
  │                                                      │
  │  CAP_SYS_PTRACE  → debug/trace other processes      │
  │                    Can read other pod's memory       │
  │                    (on same node, shared PID ns)     │
  │                                                      │
  │  CAP_SYS_MODULE  → load kernel modules              │
  │                    Arbitrary kernel code execution   │
  │                                                      │
  │  CAP_SETUID/GID  → change user/group IDs            │
  │                    Can become root after start       │
  └──────────────────────────────────────────────────────┘

  DEFAULT CONTAINER CAPABILITIES (Docker/runc default set):
  CAP_CHOWN, CAP_DAC_OVERRIDE, CAP_FSETID, CAP_FOWNER,
  CAP_MKNOD, CAP_NET_RAW, CAP_SETGID, CAP_SETUID,
  CAP_SETFCAP, CAP_NET_BIND_SERVICE, CAP_SYS_CHROOT,
  CAP_KILL, CAP_AUDIT_WRITE
  
  Note: CAP_NET_RAW in default set → ARP spoofing possible!
  Note: CAP_SETUID in default set → setuid bit abuse possible!
```

**Best Practice: Drop ALL, Add only what's needed:**

```yaml
spec:
  containers:
    - name: web-server
      securityContext:
        capabilities:
          drop:
            - ALL           # Drop every capability first
          add:
            - NET_BIND_SERVICE   # Only if binding port < 1024
        allowPrivilegeEscalation: false
        runAsNonRoot: true
```

**Validation:**

```bash
# Check capabilities of running container
kubectl exec -it my-pod -- cat /proc/1/status | grep Cap
# CapInh: 0000000000000000
# CapPrm: 0000000000000000
# CapEff: 0000000000000000   ← all zeros = no capabilities

# Decode capability bitmask
capsh --decode=00000000a82425fb

# Check if CAP_NET_RAW is present (security risk)
kubectl exec -it my-pod -- ping -c1 8.8.8.8
# If ping works, NET_RAW is present
# Expected: Operation not permitted (with NET_RAW dropped)
```

---

### Q49. What is a container runtime sandbox (gVisor, Kata Containers) and when is it necessary for security?

**Answer:**

**Container Runtime Sandboxes** add an additional isolation layer between the container and the host kernel — addressing the fundamental risk that containers share the host kernel.

```
ISOLATION LAYERS
=============================================================

  Standard Container (runc/containerd):
  ┌──────────────────────────────────────────────────────┐
  │  Container Process                                   │
  │  ──────────────────────────────────────────────────  │
  │  Host Linux Kernel (SHARED)                          │
  │  Namespace + cgroup isolation only                   │
  │  Kernel exploit → host escape                        │
  └──────────────────────────────────────────────────────┘

  gVisor (User-space Kernel):
  ┌──────────────────────────────────────────────────────┐
  │  Container Process                                   │
  │  ──────────────────────────────────────────────────  │
  │  Sentry (Go-based user-space kernel)                 │
  │  Intercepts all syscalls                             │
  │  ──────────────────────────────────────────────────  │
  │  Host Linux Kernel                                   │
  │  Very limited syscall surface                        │
  │  Kernel exploit much harder (limited syscalls)       │
  └──────────────────────────────────────────────────────┘

  Kata Containers (Hardware VM):
  ┌──────────────────────────────────────────────────────┐
  │  Container Process                                   │
  │  ──────────────────────────────────────────────────  │
  │  Guest Linux Kernel (separate kernel per pod)        │
  │  ──────────────────────────────────────────────────  │
  │  Hardware Hypervisor (KVM/QEMU/Firecracker)          │
  │  ──────────────────────────────────────────────────  │
  │  Host Linux Kernel                                   │
  │  Guest kernel compromise ≠ host compromise          │
  └──────────────────────────────────────────────────────┘
```

**Performance vs Isolation Trade-offs:**

| Runtime     | Isolation Level | Performance Impact | Startup Time |
|-------------|----------------|-------------------|--------------|
| runc        | Namespace only  | None              | <1s          |
| gVisor      | Syscall filter  | 10-20% overhead   | <1s          |
| Kata        | Full VM kernel  | 5-15% overhead    | 1-3s         |
| Firecracker | Lightweight VM  | <5% overhead      | <125ms       |

**When to Use:**

```
USE gVisor or Kata when:
1. Multi-tenant SaaS (different customers' code on same node)
2. Processing untrusted user-submitted containers
3. High-security financial/healthcare workloads
4. CI/CD runners executing arbitrary user code
5. PCI-DSS / HIPAA requiring strong isolation

DON'T USE for:
1. Single-tenant internal workloads (overhead not justified)
2. GPU-intensive workloads (gVisor limited GPU support)
3. High-performance networking (Kata adds latency)
```

**Kubernetes RuntimeClass:**

```yaml
# RuntimeClass for gVisor
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc     # gVisor's handler name

---
# RuntimeClass for Kata
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: kata-containers
handler: kata-qemu

---
# Pod using gVisor
apiVersion: v1
kind: Pod
spec:
  runtimeClassName: gvisor
  containers:
    - name: untrusted-workload
      image: user-submitted-app:latest
```

---

### Q50. How does AppArmor integrate with Kubernetes to restrict container behavior at the OS level?

**Answer:**

**AppArmor** is a Linux Security Module (LSM) that enforces Mandatory Access Control (MAC) profiles per program — restricting what files, network, and capabilities a process can access.

```
APPARMOR PROFILE STRUCTURE
=============================================================

  Profile: restrict-web-app
  ┌──────────────────────────────────────────────────────┐
  │  /usr/bin/my-app {                                  │
  │    # Filesystem rules                               │
  │    /etc/ssl/** r,        # read SSL certs           │
  │    /tmp/** rw,           # read-write /tmp          │
  │    /proc/self/mem r,     # read own memory          │
  │    deny /proc/** rw,     # block /proc writes       │
  │    deny /sys/** rw,      # block /sys writes        │
  │    deny /etc/shadow r,   # block reading passwords  │
  │                                                     │
  │    # Network rules                                  │
  │    network inet tcp,     # allow outbound TCP       │
  │    deny network raw,     # no raw sockets           │
  │                                                     │
  │    # Capability rules                               │
  │    deny capability sys_admin,                       │
  │    deny capability net_admin,                       │
  │  }                                                  │
  └──────────────────────────────────────────────────────┘
```

**Kubernetes Integration:**

```yaml
# Load AppArmor profile on node first (via DaemonSet):
# apparmor_parser -r /etc/apparmor.d/restrict-web-app

# Apply to Pod (Kubernetes 1.30+ native field)
apiVersion: v1
kind: Pod
metadata:
  name: secure-webapp
  # Pre-1.30 annotation method:
  annotations:
    container.apparmor.security.beta.kubernetes.io/web: localhost/restrict-web-app
spec:
  containers:
    - name: web
      image: nginx:latest
      # 1.30+ native field:
      securityContext:
        appArmorProfile:
          type: Localhost
          localhostProfile: restrict-web-app
```

**Profile Modes:**

```
enforce: violations blocked + logged
complain: violations logged but NOT blocked (profiling mode)
disabled: profile not active

Development workflow:
1. Create profile in complain mode
2. Run app through all code paths
3. Review audit log: /var/log/kern.log | grep apparmor
4. Add missing rules
5. Switch to enforce mode
```

---

## Section 8: Network Observability & Threat Detection

---

### Q51. What is Hubble and how does it provide real-time network observability in Cilium-based clusters?

**Answer:**

**Hubble** is Cilium's built-in observability layer, using eBPF to capture network flows at the kernel level without any packet sampling or sniffer overhead.

```
HUBBLE ARCHITECTURE
=============================================================

  eBPF Programs (in kernel)
         |
         | capture flow events
         v
  Hubble Observer (per node, runs in cilium-agent)
  ┌─────────────────────────────────────────────────┐
  │  Receives: L3/L4/L7 flow events from eBPF      │
  │  Enriches: pod name, namespace, labels          │
  │  Stores: circular ring buffer (last N flows)    │
  │  Exposes: gRPC API (Hubble peer service)        │
  └──────────────────┬──────────────────────────────┘
                     |
         ┌───────────┴──────────┐
         v                      v
  Hubble Relay             Hubble UI
  (aggregates all          (visual flow
   node flows)              topology)
         |
  hubble CLI / Grafana dashboards / SIEM

  Data Available per Flow:
  ┌─────────────────────────────────────────────────┐
  │  source: { pod, namespace, labels, IP, port }   │
  │  destination: { pod, namespace, labels, IP }    │
  │  verdict: FORWARDED | DROPPED | ERROR           │
  │  reason: (if dropped) policy name               │
  │  l7: HTTP { method, url, status_code }          │
  │       DNS { query, response, rcode }            │
  │       Kafka { topic, api_key }                  │
  │  timestamp, node_name, trace_id (Jaeger link)   │
  └─────────────────────────────────────────────────┘
```

**Hubble CLI Examples:**

```bash
# Install hubble CLI
HUBBLE_VERSION=$(curl -s https://raw.githubusercontent.com/cilium/hubble/master/stable.txt)
curl -L --fail --remote-name-all \
  https://github.com/cilium/hubble/releases/download/$HUBBLE_VERSION/hubble-linux-amd64.tar.gz

# Port-forward Hubble Relay
kubectl port-forward -n kube-system deployment/hubble-relay 4245:4245

# Live flow monitoring
hubble observe --follow

# Monitor specific pod
hubble observe \
  --pod production/payment-service \
  --follow

# Show only dropped flows (security events)
hubble observe \
  --verdict DROPPED \
  --follow

# HTTP-level flow detail
hubble observe \
  --protocol HTTP \
  --namespace production \
  --follow

# DNS queries from a namespace
hubble observe \
  --protocol DNS \
  --from-namespace production \
  --follow

# Export to JSON for SIEM
hubble observe \
  --output json \
  --follow | \
  jq 'select(.verdict=="DROPPED")' | \
  curl -X POST https://siem.internal/ingest -d @-
```

---

### Q52. How do you detect crypto mining in Kubernetes using network signatures?

**Answer:**

```
CRYPTO MINING NETWORK SIGNATURES
=============================================================

  Mining Protocol Signatures:
  ┌─────────────────────────────────────────────────────┐
  │  Stratum Protocol (most common mining protocol):    │
  │  Port: 3333, 4444, 14444, 45560                    │
  │  JSON-RPC over TCP                                  │
  │  First message: {"method":"mining.subscribe",...}   │
  │                                                     │
  │  Monero (XMR) mining pools:                         │
  │  pool.supportxmr.com:443                           │
  │  xmrpool.eu:3333                                   │
  │                                                     │
  │  DNS queries (beaconing):                           │
  │  *.minexmr.com, *.nanopool.org, *.miningpoolhub.com│
  └─────────────────────────────────────────────────────┘

  Behavioral Indicators:
  ┌─────────────────────────────────────────────────────┐
  │  1. Sustained high CPU (>80%) over long period     │
  │  2. Outbound TCP to known mining ports             │
  │  3. Long-lived TCP connections (hours, not seconds) │
  │  4. DNS queries to known pool domains              │
  │  5. Unusual binary execution (xmrig, cgminer)      │
  └─────────────────────────────────────────────────────┘
```

**Detection Implementation:**

```yaml
# Falco rule: mining port connection
- rule: Outbound Connection to Common Miner Pool Ports
  desc: Detect connections to known cryptocurrency mining ports
  condition: >
    outbound and
    (fd.sport in (3333, 4444, 14444, 45560) or
     fd.dport in (3333, 4444, 14444, 45560)) and
    container
  output: >
    Mining connection detected
    (command=%proc.cmdline
     connection=%fd.name
     pod=%k8s.pod.name
     namespace=%k8s.ns.name)
  priority: CRITICAL
  tags: [network, crypto-mining]

---
# Cilium: block known mining ports
apiVersion: cilium.io/v2
kind: CiliumClusterwideNetworkPolicy
metadata:
  name: block-mining-ports
spec:
  endpointSelector: {}
  egressDeny:
    - toPorts:
        - ports:
            - port: "3333"
              protocol: TCP
            - port: "4444"
              protocol: TCP
            - port: "14444"
              protocol: TCP
    - toFQDNs:
        - matchPattern: "*.minexmr.com"
        - matchPattern: "*.nanopool.org"
        - matchPattern: "*.miningpoolhub.com"
      toPorts:
        - ports:
            - port: "443"
              protocol: TCP
```

**Hubble-based Detection:**

```bash
# Alert on mining port connections
hubble observe \
  --follow \
  --output json | \
jq 'select(
  .destination.port == 3333 or
  .destination.port == 4444 or
  .destination.port == 14444
)' | \
jq '{
  pod: .source.pod_name,
  ns: .source.namespace,
  dst_ip: .destination.ip,
  dst_port: .destination.port,
  time: .time
}'
```

---

### Q53. What is a CNI-level honeypot and how can it be used to detect lateral movement?

**Answer:**

```
KUBERNETES HONEYPOT ARCHITECTURE
=============================================================

  Concept: Deploy "fake" services that no legitimate
           workload should ever contact.
           Any connection to them = attack indicator.

  Implementation 1: Honeypot Service per Namespace
  ┌─────────────────────────────────────────────────────┐
  │  Deploy honeypot pod in every namespace             │
  │  Service: honeypot-svc (ClusterIP, no legitimate   │
  │           caller in architecture)                   │
  │  Any pod connecting to honeypot-svc                 │
  │  → instant HIGH priority alert                      │
  └─────────────────────────────────────────────────────┘

  Implementation 2: Fake Credentials Service
  ┌─────────────────────────────────────────────────────┐
  │  Deploy pod with fake database connection           │
  │  Fake K8s secret: "production-db-password"         │
  │  Any access to this secret → alert                  │
  │  Any connection to fake DB host → alert             │
  └─────────────────────────────────────────────────────┘

  Implementation 3: Unused IP Honeypot
  ┌─────────────────────────────────────────────────────┐
  │  Reserve CIDR range in pod network                  │
  │  No pods assigned to these IPs                      │
  │  eBPF program monitors connections to this range    │
  │  Port scan detection: rapid sequential IP hits      │
  └─────────────────────────────────────────────────────┘
```

**Honeypot Deployment:**

```yaml
---
# Honeypot pod — logs all connections
apiVersion: v1
kind: Pod
metadata:
  name: honeypot
  namespace: production
  labels:
    app: honeypot
    security.io/type: honeypot
spec:
  containers:
    - name: honeypot
      image: honeytrap/honeytrap:latest
      ports:
        - containerPort: 22    # SSH honeypot
        - containerPort: 3306  # MySQL honeypot
        - containerPort: 5432  # PostgreSQL honeypot
        - containerPort: 6379  # Redis honeypot
      env:
        - name: ALERT_WEBHOOK
          value: "https://siem.internal/honeypot-alert"

---
# NetworkPolicy: nothing should legitimately reach honeypot
# So we do NOT add any ingress-allow policy for honeypot
# But we DO monitor with Hubble:

# hubble observe --to-pod production/honeypot --follow --output json | \
#   curl -X POST https://siem.internal/alerts -d @-
```

---

### Q54. How do you implement network traffic anomaly detection for a Kubernetes cluster?

**Answer:**

```
ANOMALY DETECTION ARCHITECTURE
=============================================================

  Data Collection Layer:
  Hubble flow logs → Kafka → Stream Processing → Alerts
  
  Baseline Learning Phase (7-14 days):
  ┌─────────────────────────────────────────────────────┐
  │  Collect: all flow data (src, dst, port, bytes)    │
  │  Build:   service dependency graph                  │
  │  Learn:   normal traffic volume per edge           │
  │  Learn:   normal byte rates, connection durations  │
  │  Learn:   normal DNS query patterns                │
  └─────────────────────────────────────────────────────┘

  Detection Rules (statistical):
  ┌─────────────────────────────────────────────────────┐
  │  1. New connection edge (pod A → pod B, never seen) │
  │  2. Volume anomaly: >3σ from baseline               │
  │  3. New destination IP/FQDN                         │
  │  4. Unusual time pattern (3am spikes)               │
  │  5. Connection rate to many IPs (port scan)         │
  │  6. Large outbound data transfer (exfiltration)     │
  └─────────────────────────────────────────────────────┘
```

**Implementation Stack:**

```python
# Simplified anomaly detection using Hubble + Python

import json
import subprocess
from collections import defaultdict
from datetime import datetime
import statistics

# Collect flows via hubble CLI
def collect_flows(namespace, minutes=60):
    cmd = [
        "hubble", "observe",
        f"--namespace={namespace}",
        "--output=json",
        f"--last={minutes}m"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    flows = []
    for line in result.stdout.splitlines():
        try:
            flows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return flows

# Build baseline model
def build_baseline(flows):
    edges = defaultdict(list)
    for flow in flows:
        src = flow.get("source", {}).get("pod_name", "")
        dst = flow.get("destination", {}).get("pod_name", "")
        if src and dst:
            key = f"{src}->{dst}"
            edges[key].append(flow.get("traffic_direction"))
    return edges

# Detect anomalies
def detect_anomalies(current_flows, baseline):
    alerts = []
    current_edges = set()
    
    for flow in current_flows:
        src = flow.get("source", {}).get("pod_name", "")
        dst = flow.get("destination", {}).get("pod_name", "")
        edge = f"{src}->{dst}"
        
        if edge not in baseline:
            alerts.append({
                "type": "NEW_CONNECTION_EDGE",
                "edge": edge,
                "severity": "HIGH",
                "timestamp": flow.get("time")
            })
    
    return alerts
```

---

## Section 9: Supply Chain & CNI Plugin Security

---

### Q55. What are SLSA (Supply chain Levels for Software Artifacts) levels and how do they apply to CNI plugin security?

**Answer:**

**SLSA** (pronounced "salsa") is a framework for ensuring the integrity of software supply chains, from source to deployment.

```
SLSA LEVELS FOR CNI PLUGINS
=============================================================

  SLSA Level 0 (No guarantees):
  ┌─────────────────────────────────────────────────┐
  │  No formal process                              │
  │  Binary downloaded from internet without check │
  │  No provenance (who built this? when? how?)    │
  └─────────────────────────────────────────────────┘

  SLSA Level 1 (Documented build):
  ┌─────────────────────────────────────────────────┐
  │  Build process is scripted                     │
  │  Provenance document generated                  │
  │  Build logs available                           │
  └─────────────────────────────────────────────────┘

  SLSA Level 2 (Tamper-evident build):
  ┌─────────────────────────────────────────────────┐
  │  Build on hosted CI (GitHub Actions, etc.)      │
  │  Signed provenance by build system              │
  │  Can detect if binary was tampered post-build   │
  └─────────────────────────────────────────────────┘

  SLSA Level 3 (Hardened build, isolated):
  ┌─────────────────────────────────────────────────┐
  │  Build environment is ephemeral + reproducible  │
  │  Two-party review required                      │
  │  Cannot be influenced by build service admin    │
  │  Provenance signed with non-forgeable key       │
  └─────────────────────────────────────────────────┘

  SLSA Level 4 (Two-party source + hermetic build):
  ┌─────────────────────────────────────────────────┐
  │  Reproducible builds                            │
  │  All dependencies tracked                       │
  │  Bitwise reproducibility verification           │
  └─────────────────────────────────────────────────┘
```

**CNI Plugin Security Validation:**

```bash
# Verify Cilium CNI binary integrity (cosign)
cosign verify \
  --certificate-identity-regexp=https://github.com/cilium/cilium/.* \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  quay.io/cilium/cilium:v1.14.0

# Verify Calico SLSA provenance
cosign verify-attestation \
  --type slsaprovenance \
  --certificate-identity-regexp=.* \
  quay.io/calico/node:v3.26.0

# Check image digest before deployment
# Pinning by digest (not tag) prevents tag mutation attacks
image: quay.io/cilium/cilium@sha256:abc123...  # NOT :v1.14.0

# Verify Helm chart integrity
helm verify cilium/cilium --version 1.14.0
```

---

### Q56. Explain a CNI plugin supply chain attack and how in-toto attestation prevents it.

**Answer:**

```
CNI SUPPLY CHAIN ATTACK
=============================================================

  Attack Scenario: Typosquatting CNI Plugin
  ┌─────────────────────────────────────────────────────┐
  │  Legitimate: quay.io/cilium/cilium:v1.14.0         │
  │  Malicious:  quay.io/cillum/cilium:v1.14.0  ← typo│
  │                                                     │
  │  DevOps installs from wrong registry               │
  │  Malicious CNI binary:                             │
  │  - Backdoors iptables with secret ACCEPT rule      │
  │  - Exfiltrates pod certificates to C2              │
  │  - Installs persistence via node host filesystem   │
  └─────────────────────────────────────────────────────┘

  Attack Scenario: Compromised Build Pipeline
  ┌─────────────────────────────────────────────────────┐
  │  Attacker compromises CNI vendor's CI system       │
  │  Injects malicious code into build artifact        │
  │  Legitimate image tag: cilium:v1.14.1              │
  │  Contains: exfiltration payload in CNI binary      │
  │  Signed with valid vendor key (but compromised)    │
  └─────────────────────────────────────────────────────┘

  in-toto ATTESTATION CHAIN:
  ┌─────────────────────────────────────────────────────┐
  │  Step 1: Developer commits code                     │
  │  → Attestation: "Alice committed SHA abc123"        │
  │  → Signed by Alice's key                           │
  │                                                     │
  │  Step 2: CI builds binary                          │
  │  → Attestation: "CI built binary from SHA abc123"  │
  │  → Signed by CI system key                         │
  │  → Records: all inputs, build environment          │
  │                                                     │
  │  Step 3: Security scan                             │
  │  → Attestation: "Scanner found 0 critical CVEs"   │
  │  → Signed by scanner key                           │
  │                                                     │
  │  Step 4: Cosign/OPA validates chain at deploy time │
  │  → All steps present? All signed correctly?        │
  │  → Yes → Deploy allowed                            │
  │  → No → Deploy BLOCKED                             │
  └─────────────────────────────────────────────────────┘
```

**Implementation:**

```yaml
# Kyverno policy: require sigstore signature + SLSA
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: verify-cni-plugin-image
spec:
  rules:
    - name: verify-cilium-signature
      match:
        resources:
          kinds: ["DaemonSet"]
          namespaces: ["kube-system"]
          names: ["cilium"]
      verifyImages:
        - imageReferences:
            - "quay.io/cilium/cilium*"
          attestors:
            - entries:
                - keyless:
                    subject: "https://github.com/cilium/cilium/.github/*"
                    issuer: "https://token.actions.githubusercontent.com"
          attestations:
            - predicateType: https://slsa.dev/provenance/v0.2
              conditions:
                - all:
                    - key: "{{ builder.id }}"
                      operator: Equals
                      value: "https://github.com/slsa-framework/slsa-github-generator/.github/workflows/builder_go_slsa3.yml@refs/tags/v1.7.0"
```

---

### Q57. How does Kyverno enforce CNI-related security policies at admission time?

**Answer:**

**Kyverno** is a Kubernetes-native policy engine that validates, mutates, and generates resources at admission time (via AdmissionWebhook).

```
KYVERNO POLICY TYPES
=============================================================

  Validate: Reject non-compliant resources
  Mutate:   Automatically fix/add fields
  Generate: Create related resources (e.g., NetworkPolicy per Namespace)
  Verify:   Check image signatures/attestations

  KYVERNO IN ADMISSION FLOW:
  kubectl apply → kube-apiserver → MutatingWebhook (Kyverno)
                                        → MutatingWebhook (other)
                                  → ValidatingWebhook (Kyverno)
                                        → Resource stored in etcd
```

**CNI Security Policies with Kyverno:**

```yaml
---
# Policy 1: Block hostNetwork
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: block-host-network
spec:
  validationFailureAction: enforce
  rules:
    - name: no-host-network
      match:
        resources:
          kinds: ["Pod"]
      exclude:
        resources:
          namespaces: ["kube-system"]    # allow for CNI
      validate:
        message: "hostNetwork is not allowed"
        pattern:
          spec:
            =(hostNetwork): false

---
# Policy 2: Require NetworkPolicy for every namespace
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: generate-default-networkpolicy
spec:
  rules:
    - name: generate-deny-all
      match:
        resources:
          kinds: ["Namespace"]
      generate:
        apiVersion: networking.k8s.io/v1
        kind: NetworkPolicy
        name: default-deny-all
        namespace: "{{request.object.metadata.name}}"
        synchronize: true
        data:
          spec:
            podSelector: {}
            policyTypes:
              - Ingress
              - Egress

---
# Policy 3: Require image digest (not mutable tag)
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-image-digest
spec:
  validationFailureAction: enforce
  rules:
    - name: check-digest
      match:
        resources:
          kinds: ["Pod"]
      validate:
        message: "Images must be pinned to digest, not mutable tag"
        foreach:
          - list: "request.object.spec.containers"
            deny:
              conditions:
                - key: "{{ element.image }}"
                  operator: NotContains
                  value: "@sha256:"
```

---

### Q58. What is image signing with Cosign and how does it prevent unauthorized container images from running in your cluster?

**Answer:**

**Cosign** (part of the Sigstore project) is a tool for signing OCI container images using OIDC identity (keyless) or static keys.

```
COSIGN SIGNING FLOW
=============================================================

  KEYLESS SIGNING (using OIDC identity):
  ┌─────────────────────────────────────────────────────┐
  │  Developer / CI authenticates with OIDC             │
  │  (GitHub Actions, Google, Microsoft identity)       │
  │       |                                             │
  │       v                                             │
  │  Fulcio CA (part of Sigstore): issues short-lived   │
  │  signing certificate bound to OIDC identity         │
  │       |                                             │
  │       v                                             │
  │  Cosign signs image digest with certificate         │
  │       |                                             │
  │       v                                             │
  │  Signature + certificate stored in Rekor (public    │
  │  transparency log — immutable, append-only)         │
  │       |                                             │
  │       v                                             │
  │  Kubernetes admission: cosign verify                │
  │  → Checks: Rekor log entry exists                  │
  │  → Checks: Certificate issued to expected identity │
  │  → Checks: Digest matches (not tampered)           │
  └─────────────────────────────────────────────────────┘
```

**Workflow:**

```bash
# Sign image (keyless, in GitHub Actions)
cosign sign \
  --yes \
  quay.io/myorg/myapp@sha256:abc123...

# Sign image (with static key)
cosign generate-key-pair   # generates cosign.key + cosign.pub
cosign sign \
  --key cosign.key \
  quay.io/myorg/myapp:v1.0.0

# Verify image before deployment
cosign verify \
  --certificate-identity-regexp=https://github.com/myorg/myapp/.* \
  --certificate-oidc-issuer=https://token.actions.githubusercontent.com \
  quay.io/myorg/myapp:v1.0.0

# Admission enforcement via Kyverno (see Q57)
# or via Connaisseur:
# helm install connaisseur connaisseur/connaisseur \
#   --set validators[0].name=myorg \
#   --set validators[0].type=cosign \
#   --set validators[0].host=registry.myorg.com
```

---

### Q59. How do you perform a security audit of a Kubernetes cluster's CNI configuration?

**Answer:**

```
CNI SECURITY AUDIT CHECKLIST
=============================================================

  1. CNI PLUGIN VERSION & CVEs
  ┌───────────────────────────────────────────────────────┐
  │  Check:  Current CNI version installed               │
  │  Check:  CVE database for known vulnerabilities      │
  │  Tools:  trivy, grype on CNI container images        │
  │  Cmd:    kubectl get ds -n kube-system cilium -o yaml│
  │          | grep image                                │
  └───────────────────────────────────────────────────────┘

  2. NETWORKPOLICY COVERAGE
  ┌───────────────────────────────────────────────────────┐
  │  Check:  All namespaces have NetworkPolicy           │
  │  Check:  No namespace is fully open (no policies)    │
  │  Check:  Default deny is applied everywhere          │
  │  Cmd:    kubectl get networkpolicies --all-namespaces │
  │  Tool:   netpol-analyzer (GitHub: np-guard)          │
  └───────────────────────────────────────────────────────┘

  3. POD SECURITY CONFIGURATION
  ┌───────────────────────────────────────────────────────┐
  │  Check:  No privileged containers in prod            │
  │  Check:  No hostNetwork/hostPID/hostIPC              │
  │  Check:  All pods have seccomp: RuntimeDefault       │
  │  Cmd:    kubectl get pods --all-namespaces -o json  \│
  │            | jq '.items[].spec.containers[].         │
  │               securityContext'                        │
  └───────────────────────────────────────────────────────┘

  4. CNI CONFIGURATION FILES
  ┌───────────────────────────────────────────────────────┐
  │  Check:  /etc/cni/net.d/ file integrity              │
  │  Check:  Permissions: 600, owned by root             │
  │  Check:  No unexpected chained plugins               │
  │  Cmd:    ssh node "ls -la /etc/cni/net.d/"           │
  │          ssh node "cat /etc/cni/net.d/*.conf"        │
  └───────────────────────────────────────────────────────┘

  5. RBAC FOR CNI RESOURCES
  ┌───────────────────────────────────────────────────────┐
  │  Check:  Who can create/modify NetworkPolicy         │
  │  Check:  Who can create/modify CNI CRDs              │
  │  Cmd:    kubectl auth can-i create networkpolicies   │
  │                --as=system:serviceaccount:default:default│
  └───────────────────────────────────────────────────────┘
```

**Automated Audit Tools:**

```bash
# kube-bench: CIS Kubernetes benchmark
kube-bench run --targets node,master

# netassert: network connectivity testing
netassert -c ./test-cases.yaml

# Polaris: configuration best practices
kubectl apply -f https://github.com/FairwindsOps/polaris/releases/latest/download/dashboard.yaml
kubectl port-forward --namespace polaris svc/polaris-dashboard 8080:80

# kubescape: NSA/CISA K8s hardening scan
kubescape scan framework nsa --submit --account <account-id>

# np-guard: NetworkPolicy analysis
kubectl get networkpolicies -A -o json | npguard
```

---

### Q60. What are the security risks of using `kubectl exec` and how do you restrict and audit it?

**Answer:**

```
kubectl exec SECURITY RISKS
=============================================================

  How kubectl exec works:
  ┌─────────────────────────────────────────────────────┐
  │  kubectl exec → API server:                         │
  │  POST /api/v1/namespaces/{ns}/pods/{pod}/exec       │
  │  API server proxies to kubelet                      │
  │  kubelet exec's command inside container            │
  │  stdin/stdout/stderr streamed back via websocket    │
  └─────────────────────────────────────────────────────┘

  Risks:
  ┌─────────────────────────────────────────────────────┐
  │  1. Bypasses all NetworkPolicy                      │
  │     (traffic goes through API server, not pod net)  │
  │                                                     │
  │  2. Bypasses container runtime isolation            │
  │     (arbitrary commands inside container)           │
  │                                                     │
  │  3. Enables data exfiltration                       │
  │     kubectl cp pod:/etc/secrets . → copies out      │
  │                                                     │
  │  4. Enables credential theft                        │
  │     kubectl exec prod-db -- env | grep PASSWORD     │
  │                                                     │
  │  5. Difficult to audit in real-time               │
  │     (stream, not simple HTTP log)                   │
  └─────────────────────────────────────────────────────┘
```

**Restriction and Audit:**

```yaml
# RBAC: deny exec for most users
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRole
metadata:
  name: no-exec
rules:
  - apiGroups: [""]
    resources: ["pods/exec", "pods/attach"]
    verbs: []   # empty = deny

---
# Only allow exec for SRE team, limited to non-prod
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: sre-exec
  namespace: staging   # NOT production
rules:
  - apiGroups: [""]
    resources: ["pods/exec"]
    verbs: ["create"]

---
# OPA/Gatekeeper: prevent exec to sensitive pods
apiVersion: templates.gatekeeper.sh/v1beta1
kind: ConstraintTemplate
metadata:
  name: nopodexec
spec:
  crd:
    spec:
      names:
        kind: NoPodExec
  targets:
    - target: admission.k8s.gatekeeper.sh
      rego: |
        package nopodexec
        violation[{"msg": msg}] {
          input.review.operation == "CONNECT"
          input.review.subResource == "exec"
          input.review.object.metadata.labels["security.io/no-exec"] == "true"
          msg := "exec is disabled on this pod"
        }
```

**Audit Logging:**

```yaml
# kube-apiserver audit policy for exec
apiVersion: audit.k8s.io/v1
kind: Policy
rules:
  - level: RequestResponse
    resources:
      - group: ""
        resources: ["pods/exec", "pods/attach", "pods/portforward"]
  - level: Metadata
    resources:
      - group: ""
        resources: ["secrets", "configmaps"]
```

---

## Section 10: Advanced Attack Vectors & Hardening

---

### Q61. Explain the DNS rebinding attack in Kubernetes and how to prevent it.

**Answer:**

```
DNS REBINDING IN KUBERNETES
=============================================================

  Attack Setup:
  ┌─────────────────────────────────────────────────────┐
  │  Attacker owns domain: evil.attacker.com            │
  │  DNS TTL set to 1 second (very low)                 │
  │                                                     │
  │  Phase 1: Victim browser resolves evil.attacker.com │
  │  → DNS returns 203.0.113.1 (attacker's real IP)    │
  │  → Loads malicious JavaScript                       │
  │                                                     │
  │  Phase 2: JavaScript waits 2 seconds                │
  │  → DNS TTL expires                                  │
  │  → Attacker changes DNS to: 10.244.1.1 (pod IP!)   │
  │                                                     │
  │  Phase 3: JavaScript calls evil.attacker.com:8080   │
  │  → Browser resolves again → gets 10.244.1.1         │
  │  → Browser sends request to internal pod            │
  │  → Same-origin policy bypassed (same domain!)       │
  │  → JavaScript reads internal API response           │
  └─────────────────────────────────────────────────────┘

  In Kubernetes context:
  - Targets: internal services (ArgoCD, Grafana, metrics)
  - Exposed: non-authenticated internal endpoints
  - Result: data exfiltration from internal dashboards
```

**Prevention:**

```
1. Enable DNS rebinding protection in CoreDNS:
   Add policy plugin with local zone check

2. Require authentication on ALL internal services
   Even "internal" services must authenticate callers

3. Add Host header validation in applications
   Reject requests where Host != expected hostname

4. NetworkPolicy: block pod→pod web traffic from browser contexts
   (Complex — better to fix at application layer)

5. Egress gateway with domain validation
   Cilium FQDN policy can detect rebinding patterns
```

---

### Q62. What is an ARP spoofing attack in Kubernetes and how does Calico/Cilium prevent it?

**Answer:**

```
ARP SPOOFING IN KUBERNETES
=============================================================

  ARP (Address Resolution Protocol):
  Layer 2 protocol: IP → MAC address resolution
  Vulnerable because: no authentication in ARP

  Attack in shared L2 domain (same node):
  ┌─────────────────────────────────────────────────────┐
  │  Normal:                                            │
  │  Pod A asks: "Who has 10.244.1.5?"                 │
  │  Pod B (10.244.1.5) replies: "Me, MAC: aa:bb:cc"   │
  │  Pod A stores: 10.244.1.5 → aa:bb:cc               │
  │                                                     │
  │  After ARP Spoofing:                               │
  │  Attacker Pod sends: "10.244.1.5 is at MY MAC"     │
  │  Pod A updates: 10.244.1.5 → attacker MAC          │
  │  Pod A's traffic to 10.244.1.5 → goes to attacker  │
  │  MITM achieved!                                     │
  └─────────────────────────────────────────────────────┘

  Calico Prevention:
  ┌─────────────────────────────────────────────────────┐
  │  Calico does NOT use ARP between pods!              │
  │  Each pod gets a /32 route (host route)             │
  │  Traffic routed via proxy ARP on veth pair          │
  │  No ARP broadcast between pods                      │
  │  ARP spoofing between pods is impossible            │
  └─────────────────────────────────────────────────────┘

  Cilium Prevention:
  ┌─────────────────────────────────────────────────────┐
  │  eBPF ARP filter:                                   │
  │  Validates: does ARP reply src MAC match expected?  │
  │  If not → DROP the ARP reply                        │
  │  Unexpected ARP → alert via Hubble                 │
  └─────────────────────────────────────────────────────┘

  Antrea Prevention (OVS-based):
  ┌─────────────────────────────────────────────────────┐
  │  OVS pipeline Table 0: spoofing check               │
  │  Validates src MAC + src IP for every packet        │
  │  Mismatch → DROP at OVS level                       │
  └─────────────────────────────────────────────────────┘
```

---

### Q63. How does VXLAN packet injection work as an attack against Kubernetes overlay networks?

**Answer:**

```
VXLAN PACKET INJECTION ATTACK
=============================================================

  VXLAN Protocol:
  - UDP port 4789
  - Outer: node-level IP + UDP header
  - Inner: pod-level packet (any IP/MAC)
  - VNI (VXLAN Network Identifier): 8 bytes
  - NO AUTHENTICATION, NO ENCRYPTION (default)

  Attack Setup:
  ┌─────────────────────────────────────────────────────┐
  │  Attacker gains initial pod/node access             │
  │  Discovers: VXLAN UDP port (4789)                   │
  │  Discovers: Neighbor node IPs (from node CIDR)      │
  │  Discovers: VNI value (from CNI config)             │
  │                                                     │
  │  Attack: Craft malicious VXLAN packet               │
  │  Outer src: attacker node IP                        │
  │  Outer dst: target node IP                          │
  │  VXLAN VNI: 1 (or correct cluster VNI)             │
  │  Inner src: fake pod IP (e.g., 10.244.99.1)         │
  │  Inner dst: real target pod IP                      │
  │                                                     │
  │  Target node receives, decapsulates                 │
  │  Delivers inner packet to target pod                │
  │  Source appears as: 10.244.99.1 (fake/non-existent)│
  │  → IP spoofing attack → bypasses NetworkPolicy!     │
  └─────────────────────────────────────────────────────┘
```

**Prevention:**

```
1. eBPF source validation (Cilium)
   Cilium validates: does inner src IP exist in ipcache?
   Unknown src IP in inner packet → DROP
   
2. WireGuard encryption (Calico/Cilium)
   Encrypts VXLAN tunnel content
   Injected packets → fail WireGuard authentication
   
3. Network-level: firewall VXLAN to only known node IPs
   NodeGroup firewall rule: UDP:4789 only from cluster nodes
   
4. Calico: IPIP tunnel with source verification
   Calico validates tunnel source matches known node

5. Isolate VXLAN traffic to separate network interface
   (Node dual-NIC: management + data plane separation)
```

---

### Q64. What is a service account token attack and how does CNI/network security complement RBAC to prevent it?

**Answer:**

```
SERVICE ACCOUNT TOKEN ATTACK
=============================================================

  Every Pod gets auto-mounted ServiceAccount token:
  /var/run/secrets/kubernetes.io/serviceaccount/token
  
  Attack chain:
  ┌─────────────────────────────────────────────────────┐
  │  1. Compromise pod (SSRF, RCE via app vuln)         │
  │  2. Read SA token:                                  │
  │     cat /var/run/secrets/kubernetes.io/            │
  │          serviceaccount/token                       │
  │  3. Query API server:                               │
  │     curl -H "Authorization: Bearer $TOKEN"         │
  │          https://kubernetes.default.svc/api/v1/pods│
  │  4. If token has overpermissive RBAC:               │
  │     → List all pods (intelligence gathering)        │
  │     → Get secrets across namespaces                 │
  │     → Create privileged pods (privilege escalation) │
  └─────────────────────────────────────────────────────┘

  NETWORK + RBAC LAYERED DEFENSE:

  Layer 1 (RBAC): Minimize token permissions
  ┌─────────────────────────────────────────────────────┐
  │  Use dedicated ServiceAccount per workload          │
  │  Grant minimal RBAC (principle of least privilege)  │
  │  Disable auto-mounting if API access not needed     │
  └─────────────────────────────────────────────────────┘

  Layer 2 (Network): Block API server access from pods
  ┌─────────────────────────────────────────────────────┐
  │  Most workload pods should NEVER need API access    │
  │  Block: pod egress to kubernetes.default.svc (443)  │
  │  Block: pod egress to control-plane CIDR port 6443  │
  └─────────────────────────────────────────────────────┘
```

**Implementation:**

```yaml
# Disable automounting for default SA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: production
automountServiceAccountToken: false

---
# NetworkPolicy: block API server access from workload pods
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: block-api-server-access
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    # DNS allowed
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53
          protocol: UDP
    # Block API server (kubernetes.default.svc = 10.96.0.1)
    # All other egress blocked by policyType: Egress + no rules
    # Explicitly add only what's needed

---
# Use Bound Service Account Tokens (BSAT) - Kubernetes 1.22+
# These expire automatically and are audience-restricted
# No manual intervention needed - K8s handles rotation
```

---

### Q65. How do you implement runtime threat detection with Falco for CNI-level threats?

**Answer:**

```
FALCO ARCHITECTURE FOR CNI THREATS
=============================================================

  Kernel Driver (eBPF or kernel module):
  ┌─────────────────────────────────────────────────────┐
  │  Captures system calls + kernel events              │
  │  Passes to Falco userspace engine                   │
  └─────────────────────────────────────────────────────┘
                   |
                   v
  Falco Engine (userspace):
  ┌─────────────────────────────────────────────────────┐
  │  Evaluates rules against events                     │
  │  Enriches with K8s metadata (pod, namespace)       │
  │  Emits alerts to: stdout, gRPC, webhook, Kafka     │
  └─────────────────────────────────────────────────────┘
```

**CNI-Specific Falco Rules:**

```yaml
---
# Rule 1: Detect NetworkPolicy modification
- rule: NetworkPolicy Modified
  desc: Detect modification of NetworkPolicy objects
  condition: >
    ka.verb in (create, update, patch, delete) and
    ka.target.resource == networkpolicies
  output: >
    NetworkPolicy modified
    (user=%ka.user.name ns=%ka.target.namespace
     policy=%ka.target.name verb=%ka.verb)
  priority: WARNING
  source: k8s_audit

---
# Rule 2: Detect iptables rule flushing
- rule: iptables Flush Detected
  desc: Container flushing iptables rules (bypass NetworkPolicy)
  condition: >
    spawned_process and
    container and
    proc.name = "iptables" and
    (proc.args contains "-F" or proc.args contains "--flush")
  output: >
    iptables flush in container
    (command=%proc.cmdline pod=%k8s.pod.name ns=%k8s.ns.name)
  priority: CRITICAL

---
# Rule 3: Detect CNI config modification
- rule: CNI Config File Modified
  desc: CNI configuration file written to
  condition: >
    open_write and
    fd.name startswith "/etc/cni/" and
    not proc.name in (calico, cilium-agent, flannel)
  output: >
    CNI config modified by unexpected process
    (file=%fd.name command=%proc.cmdline user=%user.name)
  priority: CRITICAL

---
# Rule 4: Detect VXLAN raw socket usage
- rule: Raw Socket on VXLAN Port
  desc: Process opening raw socket that may inject VXLAN packets
  condition: >
    evt.type = socket and
    evt.arg.domain contains AF_PACKET and
    container
  output: >
    Raw packet socket opened in container
    (pod=%k8s.pod.name command=%proc.cmdline)
  priority: HIGH

---
# Rule 5: Detect DNS tunneling (high query rate)
- rule: Potential DNS Tunneling
  desc: High rate of DNS queries (C2 over DNS)
  condition: >
    evt.type = sendto and
    fd.l4proto = udp and
    fd.sport = 53 and
    container
  output: >
    Suspicious DNS activity (possible tunneling)
    (pod=%k8s.pod.name command=%proc.cmdline)
  priority: WARNING
  rate: 100/60    # More than 100 DNS queries in 60 seconds
```

---

### Q66. What are the top 10 Kubernetes network security hardening steps recommended by NSA/CISA?

**Answer:**

```
NSA/CISA KUBERNETES HARDENING - NETWORK FOCUS
=============================================================

  1. USE NETWORK POLICIES
  ┌─────────────────────────────────────────────────────┐
  │  Apply default-deny to all namespaces               │
  │  Explicitly allow only required flows               │
  │  Use CNI with NetworkPolicy support (not Flannel)   │
  └─────────────────────────────────────────────────────┘

  2. ENCRYPT TRAFFIC IN TRANSIT
  ┌─────────────────────────────────────────────────────┐
  │  Enable mTLS (Istio STRICT mode)                    │
  │  OR enable WireGuard at CNI level (Calico/Cilium)   │
  │  Verify: no plaintext pod-to-pod in prod            │
  └─────────────────────────────────────────────────────┘

  3. USE FIREWALLS ON WORKER NODES
  ┌─────────────────────────────────────────────────────┐
  │  Host-level firewall: iptables/nftables             │
  │  Block: inbound to kubelet port 10250 except CP     │
  │  Block: etcd port 2379-2380 except API server       │
  │  Block: VXLAN/Geneve except from cluster nodes      │
  └─────────────────────────────────────────────────────┘

  4. CONTROL PLANE NETWORK ISOLATION
  ┌─────────────────────────────────────────────────────┐
  │  API server not reachable from workload pods        │
  │  Separate management VLAN/VPC for control plane     │
  │  Use private endpoint (cloud providers)             │
  └─────────────────────────────────────────────────────┘

  5. RESTRICT CLOUD METADATA ACCESS
  ┌─────────────────────────────────────────────────────┐
  │  Block 169.254.169.254 via NetworkPolicy/iptables   │
  │  Enforce IMDS v2 (IMDSv2 required in AWS)          │
  │  Monitor: any successful metadata API calls         │
  └─────────────────────────────────────────────────────┘

  6. USE INGRESS CONTROLLERS WITH WAF
  ┌─────────────────────────────────────────────────────┐
  │  Don't expose services directly via NodePort        │
  │  Use Ingress + ModSecurity/AWS WAF                  │
  │  TLS termination at ingress (never inside cluster)  │
  └─────────────────────────────────────────────────────┘

  7. MINIMIZE CONTAINER PRIVILEGES
  ┌─────────────────────────────────────────────────────┐
  │  No CAP_NET_ADMIN, CAP_NET_RAW (for app containers)│
  │  No hostNetwork unless essential (audit exceptions) │
  │  Pod Security Standards: restricted profile         │
  └─────────────────────────────────────────────────────┘

  8. AUDIT AND LOG ALL NETWORK EVENTS
  ┌─────────────────────────────────────────────────────┐
  │  Enable API audit log for network resources         │
  │  Enable CNI flow logs (Hubble/Calico Enterprise)   │
  │  Ship to SIEM: alert on deny events, new edges      │
  └─────────────────────────────────────────────────────┘

  9. SCAN CNI IMAGES FOR VULNERABILITIES
  ┌─────────────────────────────────────────────────────┐
  │  trivy image quay.io/cilium/cilium:latest          │
  │  Pin CNI images to digest (not mutable tags)        │
  │  Subscribe to CNI vendor security advisories       │
  └─────────────────────────────────────────────────────┘

  10. IMPLEMENT EGRESS CONTROLS
  ┌─────────────────────────────────────────────────────┐
  │  Default deny egress + explicit allowlist           │
  │  FQDN-based allowlist (not CIDR — CIDRs rotate)    │
  │  Egress gateway for auditing outbound traffic       │
  └─────────────────────────────────────────────────────┘
```

---

### Q67. How does a malicious admission webhook intercept and modify pod specifications to disable security controls?

**Answer:**

```
MALICIOUS ADMISSION WEBHOOK ATTACK
=============================================================

  Kubernetes Admission Webhook Flow:
  kubectl apply Pod → API server
                          |
                    MutatingAdmissionWebhook  ← ATTACK POINT
                          |
                    ValidatingAdmissionWebhook
                          |
                    Stored in etcd

  Malicious Webhook Setup:
  ┌─────────────────────────────────────────────────────┐
  │  Attacker deploys webhook (via compromised access)  │
  │  Webhook intercepts all Pod creation/update         │
  │  Webhook MUTATES the pod spec:                      │
  │                                                     │
  │  Adds: hostNetwork: true                            │
  │  Adds: privileged: true                             │
  │  Removes: seccomp profile                           │
  │  Removes: securityContext restrictions              │
  │  Adds: volume mount of /etc (hostPath)              │
  │  Changes: image → attacker-controlled image         │
  │                                                     │
  │  All of this INVISIBLE to the original kubectl user │
  │  Pod is created with stripped security controls     │
  └─────────────────────────────────────────────────────┘
```

**Detection and Prevention:**

```bash
# List all admission webhooks
kubectl get mutatingwebhookconfigurations
kubectl get validatingwebhookconfigurations

# Inspect webhook config
kubectl get mutatingwebhookconfigurations <name> -o yaml
# Check: namespaceSelector, objectSelector, rules

# Audit: who created webhooks
kubectl get mutatingwebhookconfigurations \
  -o json | jq '.items[].metadata.annotations'

# Check API server audit log for webhook changes
grep "mutatingwebhookconfigurations" /var/log/audit.log
```

**Hardening:**

```yaml
# RBAC: restrict who can create webhooks
# Only cluster-admin should create/modify webhooks

# Kyverno policy: require webhooks to be labeled/approved
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: require-webhook-approval
spec:
  rules:
    - name: check-webhook-label
      match:
        resources:
          kinds: ["MutatingWebhookConfiguration"]
      validate:
        message: "Webhook must have approved: 'true' label"
        pattern:
          metadata:
            labels:
              security.io/approved: "true"

# Monitor webhook endpoints
# Webhook should use cluster-internal service (not external URL)
# External webhook endpoint = red flag
```

---

### Q68. Explain the concept of network micro-segmentation using Calico's tier-based policy model.

**Answer:**

```
CALICO TIERED POLICY MODEL
=============================================================

  Policies organized in tiers with priority ordering:
  
  Tier: security-platform (order: 100) ← enforced FIRST
  ┌─────────────────────────────────────────────────────┐
  │  Managed by: Security team                          │
  │  Contains: baseline deny rules, compliance rules   │
  │  Examples:                                          │
  │  - Block all metadata service access               │
  │  - Block known malicious IPs (threat intel feed)   │
  │  - Enforce PCI-DSS segmentation                    │
  └─────────────────────────────────────────────────────┘
            ↓
  Tier: network-ops (order: 200) ← enforced SECOND
  ┌─────────────────────────────────────────────────────┐
  │  Managed by: Platform/Network team                  │
  │  Contains: infrastructure policies                 │
  │  Examples:                                          │
  │  - Allow monitoring (Prometheus) to all pods       │
  │  - Allow ingress controller to all services        │
  │  - Allow logging agents                            │
  └─────────────────────────────────────────────────────┘
            ↓
  Tier: application (order: 300) ← enforced THIRD
  ┌─────────────────────────────────────────────────────┐
  │  Managed by: Application teams                      │
  │  Contains: app-specific policies                   │
  │  Examples:                                          │
  │  - frontend → backend (port 8080)                  │
  │  - backend → database (port 5432)                  │
  └─────────────────────────────────────────────────────┘
            ↓
  Default tier: Kubernetes NetworkPolicy
```

**Implementation:**

```yaml
# Create security-platform tier
apiVersion: projectcalico.org/v3
kind: Tier
metadata:
  name: security-platform
spec:
  order: 100

---
# Apply policy in tier
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: security-platform.block-metadata
spec:
  tier: security-platform
  order: 10
  selector: all()
  egress:
    - action: Deny
      destination:
        nets:
          - 169.254.169.254/32
    - action: Pass    # Pass to next tier for remaining traffic

---
# Threat intel based blocking
apiVersion: projectcalico.org/v3
kind: GlobalNetworkSet
metadata:
  name: threat-intel-blocklist
  labels:
    threat: "confirmed-malicious"
spec:
  nets:
    - "198.51.100.0/24"   # Known C2 CIDR
    - "203.0.113.0/24"

---
apiVersion: projectcalico.org/v3
kind: GlobalNetworkPolicy
metadata:
  name: security-platform.block-threat-intel
spec:
  tier: security-platform
  order: 5
  selector: all()
  egress:
    - action: Deny
      destination:
        selector: "threat == 'confirmed-malicious'"
    - action: Pass
```

---

### Q69. How do you implement network forensics capability in Kubernetes for post-incident investigation?

**Answer:**

```
KUBERNETES NETWORK FORENSICS ARCHITECTURE
=============================================================

  Evidence Sources:
  ┌─────────────────────────────────────────────────────┐
  │  1. CNI Flow Logs (Hubble/Calico)                  │
  │     Who talked to whom, when, verdict              │
  │     Retention: 30-90 days in SIEM                  │
  │                                                     │
  │  2. Kubernetes Audit Logs                          │
  │     API operations, resource changes               │
  │     Who changed NetworkPolicy? When?               │
  │                                                     │
  │  3. Container Runtime Logs                         │
  │     Image pulls, container starts/stops            │
  │     Process execution logs (if Tetragon enabled)   │
  │                                                     │
  │  4. Node-level Packet Capture                      │
  │     tcpdump on node (pre-configured)               │
  │     eBPF ring buffer (Tetragon, Falco)             │
  │                                                     │
  │  5. DNS Query Logs                                 │
  │     CoreDNS query log plugin                       │
  │     Reveals C2 domains, lateral movement           │
  └─────────────────────────────────────────────────────┘
```

**Forensics Tooling:**

```bash
# Enable CoreDNS query logging
kubectl edit configmap coredns -n kube-system
# Add: log plugin to Corefile:
# .:53 {
#   log                ← ADD THIS
#   errors
#   health
#   ...
# }

# Retrospective flow analysis with Hubble
hubble observe \
  --since=2024-01-15T10:00:00 \
  --until=2024-01-15T11:00:00 \
  --pod production/compromised-pod \
  --output json | \
jq '{src: .source.pod_name, dst: .destination.pod_name, time: .time, verdict: .verdict}'

# Node packet capture (pre-deploy tcpdump DaemonSet for forensics)
kubectl apply -f - <<EOF
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: network-capture
  namespace: security
spec:
  selector:
    matchLabels:
      app: network-capture
  template:
    spec:
      hostNetwork: true
      containers:
        - name: tcpdump
          image: nicolaka/netshoot
          command: 
            - tcpdump
            - -i any
            - -w /captures/$(NODE_NAME)-$(date +%Y%m%d).pcap
            - -G 3600    # rotate every hour
          env:
            - name: NODE_NAME
              valueFrom:
                fieldRef:
                  fieldPath: spec.nodeName
          volumeMounts:
            - name: captures
              mountPath: /captures
      volumes:
        - name: captures
          hostPath:
            path: /var/captures
EOF

# Retrieve and analyze capture
kubectl exec -n security ds/network-capture -- \
  tcpdump -r /captures/node-1-20240115.pcap -n \
  'host 10.244.1.5'
```

---

### Q70. What is the Kubernetes CNI security roadmap and what features are coming that will impact security?

**Answer:**

```
CNI SECURITY ROADMAP (2024-2026)
=============================================================

  1. Kubernetes Network Policy V2 (KEP-2091)
  ┌─────────────────────────────────────────────────────┐
  │  Adds: Deny rules (explicit deny, not just implicit)│
  │  Adds: Port ranges (not just single ports)          │
  │  Adds: FQDN-based rules (no more CIDR only)         │
  │  Adds: Namespaced AdminNetworkPolicy                │
  │  Adds: BaselineAdminNetworkPolicy (cluster-default) │
  │  Status: Alpha in Kubernetes 1.29 (2023)            │
  └─────────────────────────────────────────────────────┘

  2. Sidecarless Service Mesh (Ambient Mesh)
  ┌─────────────────────────────────────────────────────┐
  │  Istio Ambient: no sidecar injection needed         │
  │  Uses: ztunnel (per-node proxy) for mTLS L4        │
  │  Uses: waypoint proxy (per-namespace) for L7        │
  │  Reduces: attack surface (no Envoy in every pod)    │
  │  Reduces: overhead (no sidecar startup cost)        │
  │  Status: Istio 1.21 (beta)                          │
  └─────────────────────────────────────────────────────┘

  3. eBPF LSM (BPF-LSM) Mainstream Adoption
  ┌─────────────────────────────────────────────────────┐
  │  Replace AppArmor/SELinux with eBPF policies        │
  │  More flexible, Kubernetes-native enforcement       │
  │  Tetragon LSM policies: GA direction                │
  │  Allows: per-pod syscall + file + network policy    │
  └─────────────────────────────────────────────────────┘

  4. SPIFFE/SPIRE for Kubernetes (CNCF Graduation)
  ┌─────────────────────────────────────────────────────┐
  │  K8s built-in workload identity API (KEP-4193)      │
  │  Kubelet-managed SPIFFE cert issuance              │
  │  No separate SPIRE server needed for basic use     │
  │  Status: Alpha (Kubernetes 1.29)                    │
  └─────────────────────────────────────────────────────┘

  5. Confidential Containers
  ┌─────────────────────────────────────────────────────┐
  │  TEE (Trusted Execution Environment) for pods       │
  │  AMD SEV / Intel TDX                               │
  │  Network traffic encrypted even from node operator  │
  │  Use case: multi-tenant with untrusted infra owner  │
  └─────────────────────────────────────────────────────┘
```

---

### Q71. How does Cilium's Hubble integrate with SIEM systems for security event correlation?

**Answer:**

```
HUBBLE → SIEM INTEGRATION ARCHITECTURE
=============================================================

  Hubble                   Pipeline              SIEM
  ┌─────────┐    gRPC    ┌──────────┐  TCP/TLS  ┌──────────┐
  │ Hubble  │──────────→ │ Logstash │──────────→ │Elastic   │
  │ Relay   │            │  OR      │            │  Search  │
  └─────────┘            │ Fluentd  │            └──────────┘
                         │  OR      │
                         │ Vector   │
                         └──────────┘
  
  OR directly:
  ┌─────────┐  Prometheus  ┌──────────┐
  │ Hubble  │─────────────→│ Grafana  │
  │ Metrics │              │ Alerting │
  └─────────┘              └──────────┘
```

**Integration Configuration:**

```yaml
# Hubble to Elasticsearch via Fluentd
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluentd-hubble-config
  namespace: kube-system
data:
  fluent.conf: |
    <source>
      @type grpc
      port 4245
      tag hubble.flow
    </source>
    
    <filter hubble.flow>
      @type record_transformer
      <record>
        cluster_name production-cluster
        environment production
      </record>
    </filter>
    
    # Route DROPPED flows as HIGH priority to SIEM
    <match hubble.flow>
      @type elasticsearch
      host elasticsearch.logging.svc.cluster.local
      port 9200
      index_name hubble-flows-%Y.%m.%d
      <buffer>
        @type file
        path /var/log/fluentd-buffers/hubble
        flush_interval 10s
      </buffer>
    </match>
```

**Correlation Queries (Kibana/Elasticsearch):**

```json
// Detect lateral movement: pod connecting to new destinations
{
  "query": {
    "bool": {
      "must": [
        { "term": { "verdict": "FORWARDED" }},
        { "range": { "@timestamp": { "gte": "now-1h" }}}
      ],
      "must_not": [
        { "exists": { "field": "baseline_edge" }}
      ]
    }
  }
}

// Alert on any DROP from specific namespace
{
  "query": {
    "bool": {
      "must": [
        { "term": { "verdict": "DROPPED" }},
        { "term": { "source.namespace": "production" }}
      ]
    }
  }
}
```

---

### Q72. What are Kubernetes CIS Benchmark requirements for CNI security and how do you verify compliance?

**Answer:**

```
CIS KUBERNETES BENCHMARK - CNI SECURITY SECTIONS
=============================================================

  CIS Control 3.2.1: Ensure that the --kubelet-certificate-authority 
  flag is set (API server)
  
  CIS Control 5.3.1: Ensure that the CNI in use supports 
  NetworkPolicy
  ┌──────────────────────────────────────────────────────┐
  │  Verify: CNI supports NetworkPolicy                  │
  │  kubectl create -f deny-all-policy.yaml              │
  │  Test: blocked traffic is actually blocked           │
  └──────────────────────────────────────────────────────┘

  CIS Control 5.3.2: Ensure that all Namespaces have 
  NetworkPolicy defined
  ┌──────────────────────────────────────────────────────┐
  │  Check: namespaces without any NetworkPolicy         │
  │  kubectl get ns -o json | jq '.items[].metadata.name'│
  │  → for each ns, verify NetworkPolicy exists          │
  └──────────────────────────────────────────────────────┘

  CIS Control 5.4.1: Prefer using secrets as files over 
  secrets as environment variables
  (Reduces secret exposure in process environment)

  CIS Control 5.7.1: Create administrative boundaries 
  between resources using Namespaces with NetworkPolicy

  CIS Control 5.7.4: The default namespace should not 
  be used (label + NetworkPolicy it as restricted)
```

**Automated Verification:**

```bash
# kube-bench: CIS benchmark scanner
docker run --rm \
  -v $(pwd):/host \
  aquasec/kube-bench:latest \
  --targets node,master,etcd,policies

# kube-score: general best practice check
kubectl get pods --all-namespaces -o json | kube-score score -

# Specific NetworkPolicy coverage check
#!/bin/bash
echo "Namespaces without NetworkPolicy:"
for ns in $(kubectl get ns -o jsonpath='{.items[*].metadata.name}'); do
  count=$(kubectl get networkpolicies -n $ns 2>/dev/null | wc -l)
  if [ "$count" -le 1 ]; then  # 1 = just header line
    echo "  MISSING: $ns"
  fi
done

# NSA Hardening check with kubescape
kubescape scan framework nsa \
  --exclude-namespaces kube-system,kube-public \
  --format json \
  --output nsa-report.json
```

---

### Q73-Q80: Additional Advanced Topics

---

### Q73. Explain how Cilium Ingress Controller differs from Nginx Ingress from a security perspective.

**Answer:**

```
CILIUM INGRESS vs NGINX INGRESS SECURITY
=============================================================

  Nginx Ingress:
  ┌──────────────────────────────────────────────────────┐
  │  External traffic → Nginx pod → iptables DNAT → pod │
  │  Security: separate pod, standard container risks   │
  │  TLS: terminated at Nginx                           │
  │  Authentication: basic auth, OAuth (annotations)    │
  │  WAF: ModSecurity plugin                            │
  │  Observability: access logs                         │
  └──────────────────────────────────────────────────────┘

  Cilium Ingress:
  ┌──────────────────────────────────────────────────────┐
  │  External traffic → Cilium Envoy proxy → eBPF → pod │
  │  Security: L7 policy enforced at CNI level          │
  │  TLS: terminated at Envoy, certs from K8s secret    │
  │  Authentication: native with JWT/mTLS (with Envoy)  │
  │  WAF: Envoy HTTP filters (WASM)                     │
  │  Observability: Hubble + Envoy access logs           │
  │  Extra: eBPF-level DDoS protection (XDP)            │
  └──────────────────────────────────────────────────────┘

  Key Security Difference:
  Cilium Ingress traffic is policy-controlled at the
  eBPF level from the moment it enters the node —
  before it even reaches Envoy. Nginx Ingress relies
  entirely on iptables/IPVS for traffic handling.
```

---

### Q74. How does DNS-based exfiltration work in Kubernetes and how do you detect/prevent it?

**Answer:**

```
DNS EXFILTRATION ATTACK
=============================================================

  How it works:
  ┌──────────────────────────────────────────────────────┐
  │  Compromised pod cannot make TCP connections         │
  │  (NetworkPolicy blocks most egress)                  │
  │  BUT DNS (UDP:53) is almost always allowed           │
  │                                                      │
  │  Attacker encodes data in DNS queries:               │
  │  stolen-data-base64.c2.attacker.com                 │
  │  → DNS query goes to CoreDNS → forwarded to         │
  │    attacker's authoritative DNS server              │
  │  → Attacker logs all incoming DNS queries           │
  │  → Decodes base64 data from subdomains              │
  │                                                      │
  │  Bandwidth: ~50-100 bytes per query                  │
  │  Slow but stealthy                                   │
  └──────────────────────────────────────────────────────┘

  Detection Signals:
  1. High frequency DNS queries from single pod
  2. DNS queries with unusually long subdomains (>50 chars)
  3. DNS queries with high entropy in subdomains
  4. DNS queries to unfamiliar domains
  5. Many NX (non-existent) domain responses
```

**Prevention:**

```yaml
# Restrict DNS egress to internal CoreDNS only
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: restrict-dns
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - port: 53
          protocol: UDP
    # Block direct external DNS (8.8.8.8, etc.)
    # By NOT allowing egress to external IPs on port 53

---
# CoreDNS: block known exfiltration domains
# corefile plugin: hosts or rewrite
# Or use: DNS firewall (external-dns-firewall)
```

```yaml
# Falco: detect DNS exfiltration pattern
- rule: DNS Exfiltration Pattern
  desc: Detect unusually long DNS queries (data in subdomain)
  condition: >
    evt.type = sendto and
    fd.l4proto = udp and
    fd.rport = 53 and
    container and
    strlen(dns.query) > 100
  output: >
    Potential DNS exfiltration
    (query=%dns.query pod=%k8s.pod.name)
  priority: HIGH
```

---

### Q75. What is the OWASP Kubernetes Top 10 and how does CNI security address each item?

**Answer:**

```
OWASP K8S TOP 10 - CNI SECURITY MAPPING
=============================================================

  K01: Insecure Workload Configurations
  → CNI Fix: Pod Security Standards (Restricted profile)
             seccomp, no hostNetwork, drop capabilities

  K02: Supply Chain Vulnerabilities
  → CNI Fix: Sign CNI plugin images (cosign)
             Pin by digest, SLSA attestation

  K03: Overly Permissive RBAC
  → CNI Fix: Limit who can modify NetworkPolicy
             Audit webhook configurations

  K04: Lack of Centralized Policy Enforcement
  → CNI Fix: Calico GlobalNetworkPolicy / Cilium CCNP
             OPA Gatekeeper for admission policies

  K05: Inadequate Logging and Monitoring
  → CNI Fix: Hubble flow logs, Falco runtime alerts
             CoreDNS query logging, API audit logs

  K06: Broken Authentication Mechanisms
  → CNI Fix: mTLS (Istio STRICT) for all service calls
             SPIFFE-based workload identity

  K07: Missing Network Segmentation Controls
  → CNI Fix: Default-deny NetworkPolicy per namespace
             Micro-segmentation per service

  K08: Secrets Management Failures
  → CNI Fix: Block API server access from pods (NetworkPolicy)
             Block metadata service (169.254.169.254)

  K09: Misconfigured Cluster Components
  → CNI Fix: CIS Benchmark, kube-bench scans
             Restrict CNI config file permissions

  K10: Outdated and Vulnerable Components
  → CNI Fix: Subscribe to CNI CVE advisories
             Automated image scanning in CI
```

---

### Q76. Explain how to implement a security operations runbook for a CNI-level incident response.

**Answer:**

```
CNI INCIDENT RESPONSE RUNBOOK
=============================================================

  PHASE 1: DETECTION (T+0 to T+15min)
  ┌──────────────────────────────────────────────────────┐
  │  Alert Sources:                                      │
  │  - Falco: suspicious network activity               │
  │  - Hubble: unexpected flow drops / new edges        │
  │  - SIEM: correlation alert                          │
  │                                                     │
  │  Initial Questions:                                 │
  │  - Which pod/namespace is affected?                 │
  │  - What connections were made?                      │
  │  - Is the incident ongoing or historical?           │
  └──────────────────────────────────────────────────────┘

  PHASE 2: TRIAGE (T+15 to T+30min)
  ┌──────────────────────────────────────────────────────┐
  │  Commands:                                           │
  │  hubble observe --pod <ns>/<pod> --since 1h         │
  │  kubectl describe pod <pod> -n <ns>                 │
  │  kubectl get events -n <ns>                         │
  │  kubectl logs <pod> -n <ns> --previous              │
  │  Tetragon: review process execution events          │
  └──────────────────────────────────────────────────────┘

  PHASE 3: CONTAINMENT (T+30 to T+60min)
  ┌──────────────────────────────────────────────────────┐
  │  Option A: Isolate pod (emergency NetworkPolicy)    │
  │  kubectl label pod <pod> quarantine=true            │
  │  Apply: deny-all NetworkPolicy for quarantine label │
  │                                                     │
  │  Option B: Delete pod (if stateless)               │
  │  kubectl delete pod <pod> --grace-period=0          │
  │                                                     │
  │  Option C: Cordon node (if node compromised)        │
  │  kubectl cordon <node>                              │
  │  kubectl drain <node> --ignore-daemonsets           │
  └──────────────────────────────────────────────────────┘

  PHASE 4: EVIDENCE COLLECTION (T+30 to T+120min)
  ┌──────────────────────────────────────────────────────┐
  │  Collect:                                            │
  │  - Hubble flow export for affected timeframe        │
  │  - Pod describe / events                           │
  │  - Node-level packet capture (if pre-deployed)     │
  │  - Container filesystem snapshot                    │
  │  - API audit logs for affected namespace            │
  │  - Memory dump (if memory forensics tool deployed)  │
  └──────────────────────────────────────────────────────┘
```

---

### Q77. How does Kubernetes handle network policy for IPv6 and dual-stack configurations?

**Answer:**

```
DUAL STACK KUBERNETES NETWORKING
=============================================================

  Dual-stack: pods get BOTH IPv4 and IPv6 addresses
  
  Pod addresses:
  IPv4: 10.244.1.5
  IPv6: fd00::1:5
  
  Service addresses:
  IPv4: 10.96.0.100
  IPv6: fd00:96::100
  
  NetworkPolicy for Dual-stack:
  ┌──────────────────────────────────────────────────────┐
  │  NetworkPolicy ipBlock supports BOTH:               │
  │  - 10.0.0.0/8 (IPv4 CIDR)                          │
  │  - fd00::/8   (IPv6 CIDR)                           │
  │                                                     │
  │  SECURITY RISK:                                     │
  │  NetworkPolicy blocks IPv4 traffic                  │
  │  If IPv6 is enabled but policy only has IPv4 CIDR   │
  │  → IPv6 traffic bypasses the policy!                │
  └──────────────────────────────────────────────────────┘

  Example Correct Dual-stack Policy:
```

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-external-both-stacks
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    # Deny external IPv4
    - to:
        - ipBlock:
            cidr: 0.0.0.0/0
            except:
              - 10.0.0.0/8
              - 172.16.0.0/12
              - 192.168.0.0/16
    # Deny external IPv6 (must explicitly include)
    - to:
        - ipBlock:
            cidr: ::/0
            except:
              - fc00::/7   # ULA (Unique Local Addresses)
```

---

### Q78. What is a Kubernetes network policy conflict and how do you debug overlapping policies?

**Answer:**

```
NETWORKPOLICY CONFLICT DEBUG PROCESS
=============================================================

  Example Conflict:
  Policy A: allow frontend → backend (port 8080)
  Policy B: deny-all ingress to backend
  
  Which wins? → Kubernetes NetworkPolicy is ADDITIVE
               Both apply → result = ALLOW
               (Any ALLOW in any policy = allowed)
  
  CONFLICT TYPE 1: Expected block but traffic flows
  Cause: Another policy is ALLOWING what you want to block
  Debug:
  ┌──────────────────────────────────────────────────────┐
  │  kubectl get networkpolicies -n <ns> -o yaml        │
  │  → Check ALL policies selecting the pod             │
  │  → Look for unexpected 'from' / 'to' entries        │
  │  Use: hubble observe --to-pod <pod> --follow        │
  │       to see what's actually reaching the pod       │
  └──────────────────────────────────────────────────────┘
  
  CONFLICT TYPE 2: Expected allow but traffic drops
  Cause: Missing DNS egress, missing namespace selector,
         AND/OR logic confusion
  Debug:
  ┌──────────────────────────────────────────────────────┐
  │  cilium monitor --type drop  (see drop reason)      │
  │  hubble observe --verdict DROPPED --follow          │
  │  cilium endpoint list (verify endpoint exists)      │
  │  cilium policy get <endpoint-id>                    │
  └──────────────────────────────────────────────────────┘
```

**Debug Script:**

```bash
#!/bin/bash
# network-policy-debugger.sh
POD=$1
NAMESPACE=$2

echo "=== Policies selecting pod ==="
kubectl get networkpolicies -n $NAMESPACE -o json | \
  jq --arg pod "$POD" \
  '.items[] | select(.spec.podSelector.matchLabels != null) | .metadata.name'

echo "=== Pod labels ==="
kubectl get pod $POD -n $NAMESPACE \
  -o jsonpath='{.metadata.labels}' | jq

echo "=== Cilium endpoint info ==="
CILIUM_POD=$(kubectl get pods -n kube-system -l k8s-app=cilium \
  --field-selector spec.nodeName=$(kubectl get pod $POD -n $NAMESPACE \
  -o jsonpath='{.spec.nodeName}') -o name | head -1)

kubectl exec -n kube-system $CILIUM_POD -- \
  cilium endpoint list | grep $NAMESPACE

echo "=== Recent drop events ==="
hubble observe \
  --pod $NAMESPACE/$POD \
  --verdict DROPPED \
  --since 30m \
  --output json | \
jq '{reason: .drop_reason_desc, src: .source.pod_name, dst: .destination.pod_name}'
```

---

### Q79. Explain how Envoy's xDS-based traffic management (Istio VirtualService) can be misconfigured to create security holes.

**Answer:**

```
VIRTUALSERVICE SECURITY MISCONFIGURATIONS
=============================================================

  Misconfig 1: Wildcard host with no restriction
  ┌──────────────────────────────────────────────────────┐
  │  kind: VirtualService                               │
  │  spec:                                              │
  │    hosts:                                           │
  │      - "*"    ← matches ALL traffic!                │
  │    http:                                            │
  │      - route:                                       │
  │          - destination:                             │
  │              host: attacker-service                 │
  │                                                     │
  │  Effect: ALL requests in namespace → attacker svc   │
  └──────────────────────────────────────────────────────┘

  Misconfig 2: Header-based routing without validation
  ┌──────────────────────────────────────────────────────┐
  │  match:                                             │
  │    - headers:                                       │
  │        x-admin: exact: "true"                       │
  │  route:                                             │
  │    - destination: admin-backend                     │
  │                                                     │
  │  Attack: curl -H "x-admin: true" /api              │
  │  → Routes to admin backend!                        │
  │  Header can be spoofed by external caller           │
  └──────────────────────────────────────────────────────┘

  Misconfig 3: Weight-based routing exposing canary
  ┌──────────────────────────────────────────────────────┐
  │  route:                                             │
  │    - destination: stable  weight: 90               │
  │    - destination: canary  weight: 10               │
  │                                                     │
  │  Canary has: new unpatched feature                  │
  │  Attacker: retries 20 times → eventually hits canary│
  │  Exploits unpatched feature                         │
  └──────────────────────────────────────────────────────┘
```

**Secure VirtualService Patterns:**

```yaml
# Validate and strip admin headers at ingress
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: secure-routing
spec:
  hosts:
    - backend.production.svc.cluster.local  # explicit, not wildcard
  http:
    - match:
        - uri:
            prefix: /api/admin
          sourceLabels:
            app: admin-frontend   # ONLY from admin frontend
      headers:
        request:
          remove:
            - x-admin   # strip before forwarding
      route:
        - destination:
            host: admin-backend

    - route:
        - destination:
            host: backend
```

---

### Q80. What is the future of CNI security — describe the convergence of CNI, service mesh, and runtime security?

**Answer:**

```
CONVERGENCE TREND: CNI + SERVICE MESH + RUNTIME
=============================================================

  CURRENT STATE (Separate layers):
  ┌────────────────────────────────────────────────────────┐
  │  Layer 1: CNI (Calico/Cilium)                         │
  │  → L3/L4 NetworkPolicy                               │
  │  Layer 2: Service Mesh (Istio/Linkerd)               │
  │  → mTLS, L7 AuthorizationPolicy                      │
  │  Layer 3: Runtime Security (Falco/Tetragon)          │
  │  → syscall-level detection and enforcement           │
  │  Layer 4: Secret Management (Vault)                  │
  │  → credential lifecycle                              │
  │                                                      │
  │  Problem: 4 separate tools, 4 control planes,        │
  │            4 policy languages to learn               │
  └────────────────────────────────────────────────────────┘

  EMERGING CONVERGENCE:
  ┌────────────────────────────────────────────────────────┐
  │  Cilium Mesh (Cilium + Ambient-like sidecarless mTLS) │
  │  + Tetragon (runtime security via eBPF)               │
  │  + Hubble (observability)                             │
  │  = Single eBPF-based plane for:                       │
  │    - Network policy (L3-L7)                           │
  │    - mTLS (via ztunnel-like approach)                 │
  │    - Runtime security (via Tetragon)                  │
  │    - Observability (via Hubble)                       │
  │    All powered by eBPF in kernel space               │
  └────────────────────────────────────────────────────────┘

  KEY EMERGING PATTERNS:

  1. Sidecarless service mesh (Istio Ambient, Cilium Mesh)
     → Reduced attack surface
     → Better performance
     → Simpler operations

  2. eBPF replacing iptables everywhere
     → Consistent, performant policy enforcement
     → Better visibility
     → Harder to bypass (kernel-level)

  3. SPIFFE as universal identity
     → Single identity framework for K8s + VMs + serverless
     → Cross-cloud federated trust

  4. Policy-as-code with GitOps
     → NetworkPolicy, Gatekeeper, Kyverno in Git
     → Signed commits → signed policies
     → SLSA for policy changes

  5. AI/ML-based anomaly detection
     → Hubble flow baseline learning
     → Automatic new-edge alerting
     → Reduces analyst alert fatigue
```

---

## 📚 Quick Reference: Security Tools Cheat Sheet

```
TOOL              PURPOSE                      KEY COMMAND
─────────────────────────────────────────────────────────────────
cilium            CNI + eBPF policy            cilium status
hubble            Flow observability           hubble observe --follow
tetragon          Runtime security (eBPF)      tetra getevents
falco             Syscall detection            falco -r rules.yaml
kube-bench        CIS benchmark                kube-bench run
kubescape         NSA/CISA hardening           kubescape scan nsa
trivy             Image scanning               trivy image <img>
cosign            Image signing                cosign verify <img>
kyverno           Admission policies           kyverno apply
netshoot          Network debug pod            kubectl run -it netshoot
```

---

## 📖 Recommended Study Resources

| Resource | Type | Focus |
|----------|------|-------|
| Cilium Docs | Official | eBPF, NetworkPolicy, Hubble |
| Calico Docs | Official | BGP, GNP, WireGuard |
| CNCF Security Whitepaper | Paper | K8s security model |
| NSA K8s Hardening Guide | Paper | Government hardening |
| "Container Security" - Liz Rice | Book | Deep technical foundation |
| Istio Docs | Official | Service mesh, mTLS |
| SPIFFE/SPIRE Docs | Official | Workload identity |
| CIS Kubernetes Benchmark | Standard | Compliance baseline |

---

*Document version: 1.0 | Prepared for: Senior Cloud/CNI Security Engineers*
*Topics: CNI Architecture, NetworkPolicy, Service Mesh, eBPF, Zero Trust, Runtime Security*

