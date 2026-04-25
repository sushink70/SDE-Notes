Short answer: there is no finite “complete” list—cloud-native stacks inherit the entire Internet protocol suite plus overlay, control-plane, and observability protocols. The useful way to reason about this is by OSI layer and by *who* handles it (kernel vs CNI vs service mesh vs control plane).

Below is a precise, production-oriented breakdown.

---

# L1 — Physical Layer

**Handled by:** NICs, hypervisor vSwitch, cloud provider fabric (not Kubernetes directly)

Protocols / specs:

* Ethernet PHY (1000BASE-T, 10GBASE-SR, etc.)
* Optical (DWDM)
* PCIe (device interconnect to NIC)
* Cloud provider fabric abstractions (AWS Nitro, GCP Andromeda)

👉 Cloud-native implication: you don’t control L1, but performance constraints (latency, MTU, offloads like SR-IOV) propagate upward.

---

# L2 — Data Link Layer

**Handled by:** Linux kernel, vSwitch (OVS/eBPF), CNIs

Core protocols:

* Ethernet (802.3)
* VLAN (802.1Q)
* QinQ (802.1ad)
* ARP (IPv4 resolution)
* NDP (IPv6 neighbor discovery)
* STP/RSTP (rare in cloud-native, mostly DC fabric)
* LLDP (node discovery)

Cloud-native overlays / L2 extensions:

* VXLAN (dominant overlay for Kubernetes CNIs)
* Geneve (used by Open vSwitch, OpenStack, some CNIs)
* GRE (older tunnels)
* MAC-in-MAC (rare)

Used by tools:

* Calico (VXLAN, BGP mode)
* Flannel (VXLAN)
* Cilium (can bypass overlays using eBPF)

---

# L3 — Network Layer

**Handled by:** Linux kernel routing stack, CNIs, cloud VPC

Protocols:

* IPv4 / IPv6
* ICMP / ICMPv6
* IPsec (ESP, AH)
* Routing protocols:

  * BGP (critical in cloud-native)
  * OSPF (rare inside K8s, more DC)
  * IS-IS (infra-level)

Cloud-native specifics:

* Pod CIDR routing
* VPC-native routing (AWS VPC CNI)
* BGP peering (Calico, MetalLB)

Used by:

* Kubernetes (Pod networking model)
* MetalLB (BGP/ARP)

---

# L4 — Transport Layer

**Handled by:** Linux kernel, kube-proxy, eBPF datapath

Protocols:

* TCP
* UDP
* SCTP (supported in Kubernetes but niche)
* DCCP (rare)

Cloud-native enhancements:

* QUIC (technically L4 over UDP but often treated as L7 transport)
* Connection tracking (conntrack)
* NAT (SNAT/DNAT)

Mechanisms:

* kube-proxy (iptables/IPVS)
* eBPF-based load balancing (Cilium replacing kube-proxy)

---

# L5 — Session Layer (loosely defined in practice)

**Handled by:** service mesh, application frameworks

Protocols / concepts:

* TLS session management
* gRPC streams
* HTTP keep-alive
* WebSocket sessions

Security/session:

* mTLS (mutual TLS)
* SPIFFE identities
* Session resumption (TLS tickets)

Used by:

* Istio
* Linkerd

---

# L6 — Presentation Layer

**Handled by:** app + proxies (Envoy sidecars)

Protocols / formats:

* TLS/SSL
* X.509 certificates
* JSON, Protobuf, Avro
* Compression (gzip, brotli)

Cloud-native specifics:

* Automatic certificate rotation
* Encryption policies
* Protocol translation (HTTP ↔ gRPC)

---

# L7 — Application Layer

**Handled by:** ingress controllers, service mesh, apps

Core protocols:

* HTTP/1.1
* HTTP/2
* HTTP/3 (QUIC)
* gRPC
* WebSocket
* DNS (critical!)
* REST

Infra / control-plane protocols:

* Kubernetes API (REST over HTTPS)
* etcd (Raft consensus)
* Prometheus scraping (HTTP)
* OpenTelemetry (OTLP over gRPC/HTTP)

Service discovery:

* DNS (CoreDNS)
* xDS (Envoy control plane APIs)

Used by:

* Envoy
* CoreDNS
* Prometheus

---

# Cross-Layer / Cloud-Native-Specific Protocols

These don’t fit cleanly into OSI but are critical:

### Overlay & Encapsulation

* VXLAN (L2 over L3)
* Geneve (metadata-rich overlay)
* IP-in-IP

### Security

* TLS / mTLS
* IPsec (node-to-node encryption)
* WireGuard (modern VPN used by CNIs like Cilium)

### Control Plane

* gRPC (Istio, xDS APIs)
* REST (Kubernetes API server)
* Raft (etcd clustering)

### Observability

* OTLP (OpenTelemetry)
* StatsD
* Prometheus exposition format

---

# Architecture View (Cloud-Native Networking Stack)

```
[ Application Layer ]
  HTTP/gRPC/WebSocket/DNS
        │
[ Service Mesh ]
  Envoy (xDS, mTLS, L7 routing)
        │
[ Transport ]
  TCP / UDP / QUIC
        │
[ Network ]
  IP + BGP + VPC routing
        │
[ Overlay ]
  VXLAN / Geneve / eBPF datapath
        │
[ Data Link ]
  Ethernet / ARP / VLAN
        │
[ Physical ]
  NIC / Cloud Fabric
```

---

# Reality Check (Important)

If your mental model is “OSI layers strictly separated,” that will mislead you in cloud-native:

* eBPF collapses L3–L7 logic into kernel space
* Service mesh pushes L7 into sidecars
* QUIC blurs L4/L7
* CNIs often implement routing + encapsulation simultaneously

---

# What Actually Matters in Production

Instead of memorizing all protocols, focus on:

1. **Datapath**

   * iptables vs IPVS vs eBPF
2. **Encapsulation**

   * VXLAN vs native routing
3. **Service routing**

   * kube-proxy vs mesh vs eBPF
4. **Security**

   * mTLS vs IPsec vs WireGuard
5. **Control plane**

   * Kubernetes API + etcd + xDS

---

# Next 3 Steps (practical)

1. Trace a packet:

   ```
   pod → veth → bridge/eBPF → overlay → node → underlay → remote pod
   ```
2. Compare:

   * Calico (BGP) vs Cilium (eBPF) datapath
3. Capture real traffic:

   ```
   tcpdump -i any port 8472   # VXLAN
   bpftool prog show
   ```

---

If you want, I can map this to **actual Linux kernel modules + code paths (net/ipv4, net/core, eBPF hooks)** or do a **packet walk from syscall → NIC DMA**.
