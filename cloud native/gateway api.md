# Gateway API: Complete Deep Dive
## From Linux Kernel Networking to Cloud-Native Production Systems

> **4–8 Line Summary**
> Kubernetes Gateway API (sig-network/gateway-api) is the successor to Ingress — a role-based, expressive,
> extensible API for modeling L4–L7 network traffic routing across cluster boundaries. It decouples
> infrastructure concerns (GatewayClass/Gateway owned by infra teams) from application routing
> (HTTPRoute/GRPCRoute/TCPRoute owned by app teams), enabling multi-tenant, multi-protocol, multi-cluster
> routing without annotation hacks. Underneath every Gateway implementation sits a data-plane proxy
> (Envoy, Cilium eBPF, NGINX, HAProxy, etc.) wired into the Linux kernel's networking stack via
> netfilter/iptables, eBPF/XDP, or DPDK. Understanding Gateway API requires understanding the full
> packet journey: from NIC hardware through the kernel's RX path, tc/XDP hook points, netns,
> veth pairs, kube-proxy/iptables DNAT, and finally the proxy process — all the way back up the
> OSI model to HTTP/2, gRPC framing, and TLS session management. This guide covers every layer.

---

## Table of Contents

1. [Mental Model: Why Gateway API Exists](#1-mental-model-why-gateway-api-exists)
2. [OSI/ISO 7-Layer Model — Real Cloud/Kernel Data](#2-osiiso-7-layer-model--real-cloudkernel-data)
3. [Linux Kernel Networking Deep Dive](#3-linux-kernel-networking-deep-dive)
4. [Cloud Network Substrate](#4-cloud-network-substrate)
5. [Gateway API Resource Model](#5-gateway-api-resource-model)
6. [Role-Based Access & Trust Hierarchy](#6-role-based-access--trust-hierarchy)
7. [Routing: HTTPRoute, GRPCRoute, TCPRoute, TLSRoute, UDPRoute](#7-routing-httproute-grpcroute-tcproute-tlsroute-udproute)
8. [Policy Attachment (ReferenceGrant, BackendPolicy, etc.)](#8-policy-attachment-referencegrant-backendpolicy-etc)
9. [Control Plane Architecture](#9-control-plane-architecture)
10. [Data Plane Architecture](#10-data-plane-architecture)
11. [TLS: Termination, Passthrough, mTLS](#11-tls-termination-passthrough-mtls)
12. [Implementations: Envoy/Cilium/Istio/NGINX/HAProxy/Traefik](#12-implementations-envoy--cilium--istio--nginx--haproxy--traefik)
13. [C Implementation — Raw Kernel Socket Gateway](#13-c-implementation--raw-kernel-socket-gateway)
14. [Go Implementation — Gateway Controller + L7 Proxy](#14-go-implementation--gateway-controller--l7-proxy)
15. [Rust Implementation — Async TLS-aware Gateway Proxy](#15-rust-implementation--async-tls-aware-gateway-proxy)
16. [Threat Model & Security](#16-threat-model--security)
17. [Observability: Metrics, Tracing, Logs](#17-observability-metrics-tracing-logs)
18. [Multi-Cluster & Multi-Tenancy](#18-multi-cluster--multi-tenancy)
19. [Production Deployment, Roll-out & Rollback](#19-production-deployment-roll-out--rollback)
20. [Failure Modes & Mitigations](#20-failure-modes--mitigations)
21. [Benchmarking & Fuzzing](#21-benchmarking--fuzzing)
22. [Next 3 Steps](#22-next-3-steps)
23. [References](#23-references)

---

## 1. Mental Model: Why Gateway API Exists

### The Problem with Ingress

Kubernetes `Ingress` (GA in 1.19) was designed for a single use case: HTTP/S virtual hosting with
path-based routing backed by a Service. It was deliberately minimal, pushing all advanced features
into implementation-specific annotations:

```
# Ingress problems in practice
nginx.ingress.kubernetes.io/rewrite-target: /$1          # vendor-specific
nginx.ingress.kubernetes.io/proxy-body-size: 100m        # vendor-specific
nginx.ingress.kubernetes.io/ssl-redirect: "true"         # vendor-specific
traefik.ingress.kubernetes.io/router.entrypoints: websecure  # different vendor, different key
```

This meant:
- **No portability** — NGINX Ingress configs break on Traefik
- **No role separation** — app devs need infra-level annotation knowledge
- **No L4 support** — TCP/UDP routing not expressible
- **No multi-protocol** — gRPC, WebSockets need hacks
- **Conflicting specs** — two controllers claim same Ingress, undefined winner
- **No status feedback** — Ingress status is a single IP, not per-route condition

### Gateway API Design Principles

```
┌─────────────────────────────────────────────────────────────────┐
│                   GATEWAY API DESIGN GOALS                      │
├─────────────────────────────────────────────────────────────────┤
│ 1. Role-Oriented     → 3 personas: Infra, Cluster, App Dev      │
│ 2. Portable          → Same spec across NGINX/Envoy/Cilium/etc  │
│ 3. Expressive        → L4-L7: TCP,UDP,TLS,HTTP,gRPC,WebSocket  │
│ 4. Extensible        → Policy attachment, custom filters        │
│ 5. Status-rich       → Per-route Conditions (Ready/Accepted/etc)│
│ 6. Multi-namespace   → Cross-ns routing with ReferenceGrant     │
│ 7. Shared infra      → Multiple teams, one Gateway              │
└─────────────────────────────────────────────────────────────────┘
```

### Ingress vs Gateway API Feature Matrix

```
Feature                    Ingress          Gateway API
─────────────────────────────────────────────────────────────
HTTP routing               ✓ (basic)        ✓ (full)
HTTPS termination          ✓ (annotation)   ✓ (native spec)
Header-based routing       annotation-only  ✓ HTTPRoute matches
Query param routing        annotation-only  ✓ HTTPRoute matches
Traffic weighting (A/B)    annotation-only  ✓ HTTPRoute backendRefs weights
gRPC routing               ✗               ✓ GRPCRoute (stable 1.1)
TCP routing                ✗               ✓ TCPRoute (experimental)
UDP routing                ✗               ✓ UDPRoute (experimental)
TLS passthrough            annotation-only  ✓ TLSRoute
Cross-namespace routing    ✗               ✓ ReferenceGrant
Multi-tenancy              ✗               ✓ GatewayClass/Gateway split
Per-route status           single IP        ✓ RouteStatus Conditions
Policy attachment          ✗               ✓ BackendTLSPolicy, etc.
Role RBAC                  flat            ✓ 3-tier separation
```

---

## 2. OSI/ISO 7-Layer Model — Real Cloud/Kernel Data

This is the foundational mental model. Every Gateway API resource maps to one or more layers.
Below is the full OSI stack annotated with **real kernel structures**, **real cloud entities**,
**real protocol headers with byte sizes**, and **real Kubernetes/Gateway API resource mappings**.

```
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                    OSI / ISO 7-LAYER MODEL — CLOUD + KERNEL + GATEWAY API                    │
│                        Real data sizes, structures, and kernel objects                        │
├────────┬──────────────┬───────────────────────────────┬───────────────────────────────────────┤
│ Layer  │ Name         │ Linux Kernel Structures        │ Cloud / Kubernetes Entity             │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   7    │ Application  │ sys_read/write, epoll_wait,    │ HTTPRoute, GRPCRoute                  │
│        │              │ sock_recvmsg, HTTP parser      │ Host header, path, gRPC method        │
│        │              │ struct msghdr, iovec           │ Envoy L7 filter chain                 │
│        │              │ TLS record layer (app data)    │ Istio VirtualService (equiv)          │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   6    │ Presentation │ TLS via OpenSSL/BoringSSL/     │ TLSRoute, BackendTLSPolicy            │
│        │              │ rustls in kernel space;        │ Gateway.spec.listeners[].tls          │
│        │              │ struct tls_context in ktls;    │ cert-manager, SDS (Envoy Secret       │
│        │              │ kTLS offload (>= 4.13)         │ Discovery Service)                    │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   5    │ Session      │ TCP connection state machine:  │ Gateway persistent upstreams          │
│        │              │ struct tcp_sock (2.5 KB)        │ Envoy connection pool per upstream   │
│        │              │ sk_buff → sk → tcp_sk          │ HTTP/2 stream multiplexing            │
│        │              │ TIME_WAIT, ESTABLISHED, etc.   │ gRPC keepalives                       │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   4    │ Transport    │ struct tcphdr (20 B min):       │ TCPRoute, UDPRoute                    │
│        │              │  src_port(2) dst_port(2)        │ Gateway.spec.listeners[].port         │
│        │              │  seq(4) ack(4) off(1) flg(1)   │ Service.spec.ports[].protocol         │
│        │              │  win(2) csum(2) urg(2)          │ kube-proxy DNAT rules (iptables/      │
│        │              │ struct udphdr (8 B):            │ ipvs), Cilium BPF CT map              │
│        │              │  src(2) dst(2) len(2) csum(2)  │ NLB (AWS) / L4 ILB (GCP)             │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   3    │ Network      │ struct iphdr (20 B min):        │ Pod CIDR, VPC CIDR, Service ClusterIP │
│        │              │  ver(4b) ihl(4b) tos(1)         │ AWS VPC (VXLAN/Geneve overlay)        │
│        │              │  tot_len(2) id(2) frag(2)       │ GCP VPC (Andromeda SDN)               │
│        │              │  ttl(1) proto(1) csum(2)        │ Azure VNet (SmartNIC/AccelNet)        │
│        │              │  saddr(4) daddr(4)              │ Calico BGP, Cilium eBPF routing       │
│        │              │ netfilter PREROUTING/FORWARD/   │ iptables KUBE-SVC-* chains            │
│        │              │ POSTROUTING hooks               │ ExternalIP, LoadBalancer IP           │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   2    │ Data Link    │ struct ethhdr (14 B):           │ AWS ENA (Elastic Network Adapter)     │
│        │              │  dst_mac(6) src_mac(6) etype(2) │ Azure Mellanox ConnectX-5 (RDMA)      │
│        │              │ struct sk_buff (192 B kernel)   │ GCP gVNIC / Virtio-net                │
│        │              │ net_device, napi_struct         │ SR-IOV VF (PCI passthrough to pod)    │
│        │              │ ARP cache (neigh_table)         │ VLAN tags (802.1Q: 4B extra header)   │
│        │              │ XDP hook: BPF prog on RX ring   │ VXLAN encap (outer Eth+IP+UDP+VXLAN)  │
├────────┼──────────────┼───────────────────────────────┼───────────────────────────────────────┤
│   1    │ Physical     │ NIC driver ring buffer          │ AWS c5n: up to 100 Gbps ENA           │
│        │              │ DMA descriptors (rx_ring)       │ GCP A3: 200 Gbps NIC (H100 node)      │
│        │              │ NAPI polling (softirq NET_RX)   │ Azure HBv4: 200 Gbps InfiniBand RDMA  │
│        │              │ RSS (Receive Side Scaling)      │ Bare-metal: Mellanox 400G CX-7        │
│        │              │ TSO/GSO/GRO offloads            │ PCIe 5.0 x16 = 64 GB/s bandwidth     │
└────────┴──────────────┴───────────────────────────────┴───────────────────────────────────────┘
```

### Real Packet Walk — End to End (Client → Gateway → Pod)

```
CLIENT (outside cluster)                CLOUD LOAD BALANCER           GATEWAY POD (k8s)
─────────────────────                   ────────────────────           ─────────────────

                                         ┌──────────────────┐
TCP SYN ──────────────────────────────► │  AWS ALB / NLB    │
  Eth: src=client_mac, dst=router_mac    │  GCP HTTPS LB     │
  IP:  src=1.2.3.4:58432                 │  Azure App GW     │
  TCP: SYN, seq=X                        │                   │
                                         │  ECMP hash to     │
                                         │  gateway node IP  │
                                         └────────┬─────────┘
                                                  │  DNAT: dst=10.0.1.15:443 (node)
                                                  │  (NLB preserves src IP)
                                                  ▼
                         ┌────────────────────────────────────────────────────────┐
                         │                    LINUX HOST (k8s node)               │
                         │                                                        │
                         │  NIC (ENA/gVNIC/Mellanox)                             │
                         │    └─ DMA → sk_buff allocated in RX ring               │
                         │    └─ NAPI poll (softirq, CPU pinned via RSS)          │
                         │    └─ GRO: coalesce TCP segments                       │
                         │                                                        │
                         │  XDP hook (if Cilium/BPF offload):                    │
                         │    └─ BPF prog: lookup CT map                         │
                         │    └─ XDP_TX for known flows (bypass netstack)        │
                         │                                                        │
                         │  netfilter PREROUTING (raw table, conntrack):          │
                         │    └─ nf_conntrack_in() → create ct entry             │
                         │    └─ KUBE-SERVICES iptables chain:                   │
                         │       └─ match dst=LB_IP:443                          │
                         │       └─ DNAT → PodIP:8443 (gateway pod)              │
                         │                                                        │
                         │  IP routing: fib_lookup() → route to PodIP             │
                         │                                                        │
                         │  veth pair: (host_veth ↔ pod_veth in netns)           │
                         │    └─ tc ingress BPF (optional, Cilium L4LB)          │
                         │                                                        │
                         │  Pod Network Namespace:                                │
                         │    └─ lo + eth0 (veth end)                            │
                         │    └─ iptables (pod-level, empty usually)             │
                         │    └─ Envoy/NGINX/etc listening on :8443              │
                         │       └─ accept() → new TCP socket                    │
                         │       └─ TLS handshake (BoringSSL)                   │
                         │       └─ HTTP/2 frame parsing                         │
                         │       └─ Route matching: Host + Path + Headers        │
                         │       └─ Upstream selection (weighted backend)        │
                         │       └─ New TCP conn to backend pod                  │
                         └────────────────────────────────────────────────────────┘
```

### Real Header Stack for HTTPS Request over VXLAN (Overlay Network)

```
Bytes:  │ Outer Eth │ Outer IP │ Outer UDP │ VXLAN │ Inner Eth │ Inner IP │ TCP │ TLS │ HTTP/2 │ Payload
        │    14 B   │   20 B   │    8 B    │  8 B  │    14 B   │   20 B   │ 20B │ 5B  │  9 B+  │  ...
        ├───────────┼──────────┼───────────┼───────┼───────────┼──────────┼─────┼─────┼────────┼────────
        │dst_mac[6] │ver_ihl[1]│src_p[2]   │flags  │dst_mac[6] │ver_ihl[1]│sport│type │length  │:method
        │src_mac[6] │tos[1]    │dst_p=4789 │vni[3] │src_mac[6] │tos[1]    │dport│     │streamid│:path
        │etype=0800 │tot_len[2]│len[2]     │res[1] │etype=0800 │tot_len[2]│seq  │     │flags   │:scheme
        │           │id[2]     │csum[2]    │       │           │id[2]     │ack  │     │        │headers
        │           │frag[2]   │           │       │           │frag[2]   │off  │     │        │body
        │           │ttl[1]    │           │       │           │ttl[1]    │ctrl │     │        │
        │           │proto=17  │           │       │           │proto=6   │win  │     │        │
        │           │csum[2]   │           │       │           │csum[2]   │csum │     │        │
        │           │saddr[4]  │           │       │           │saddr[4]  │urg  │     │        │
        │           │daddr[4]  │           │       │           │daddr[4]  │opts │     │        │
        ├───────────┴──────────┴───────────┴───────┴───────────┴──────────┴─────┴─────┴────────┴────────
Total overlay overhead: 14+20+8+8+14 = 64 bytes per packet
MTU implications: 1500 (physical) - 64 = 1436 bytes usable for inner IP+TCP+TLS+HTTP2
Jumbo frames (9000 MTU) → 8936 bytes inner = significantly better throughput
```

---

## 3. Linux Kernel Networking Deep Dive

Understanding this is **mandatory** for Gateway API data-plane debugging and performance tuning.

### 3.1 sk_buff — The Kernel's Packet Structure

Every packet in the Linux kernel is represented as an `sk_buff` (socket buffer). Understanding
its layout explains why header manipulation is O(1) (pointer adjustment) and where copies happen.

```
struct sk_buff (kernel/include/linux/skbuff.h) — ~220 bytes of metadata:

┌─────────────────────────────────────────────────────────────────┐
│                         sk_buff                                  │
├─────────────────────────────────────────────────────────────────┤
│ struct sk_buff *next, *prev    → doubly-linked list (8+8 B)     │
│ struct sock *sk                → owning socket (8 B)            │
│ struct net_device *dev         → receiving/sending NIC (8 B)    │
│ ktime_t tstamp                 → hardware timestamp (8 B)       │
│ unsigned int len               → total data length (4 B)        │
│ unsigned int data_len          → non-linear data len (4 B)      │
│ __u16 mac_len                  → MAC header length (2 B)        │
│ __u16 hdr_len                  → writable header len (2 B)      │
│ __u32 priority                 → QoS priority (4 B)             │
│ __u8 pkt_type:3                → PACKET_HOST, BROADCAST, etc    │
│ nf_conntrack *nfct             → conntrack entry pointer (8 B)  │
│ unsigned char *head            → start of allocated buffer      │
│ unsigned char *data            → start of valid data            │
│ unsigned char *tail            → end of valid data              │
│ unsigned char *end             → end of allocated buffer        │
│ sk_buff_data_t transport_header → L4 offset from head           │
│ sk_buff_data_t network_header   → L3 offset from head           │
│ sk_buff_data_t mac_header       → L2 offset from head           │
│ atomic_t users                 → reference count                │
└─────────────────────────────────────────────────────────────────┘

Memory layout of actual packet data:
┌────────┬──────────────────────────────────────────────────┬────────┐
│headroom│           L2 | L3 | L4 | Data                    │tailroom│
│        │←mac_header  ←network_header  ←transport_header  │        │
│        │                            data pointer here→    │        │
└────────┴──────────────────────────────────────────────────┴────────┘
  head                                                           end

skb_push(skb, len)  → moves data pointer LEFT (add header)
skb_pull(skb, len)  → moves data pointer RIGHT (consume header)
skb_put(skb, len)   → extends tail (add data at end)
```

### 3.2 Full Kernel RX Path (NIC → Socket)

```
Hardware NIC
│
│  (1) DMA: NIC writes packet to pre-allocated sk_buff in RX ring
│           driver: ena_rx_skb() / igb_clean_rx_irq() / mlx5e_handle_rx_cqe()
│
▼
NAPI Poll (softirq NET_RX_SOFTIRQ, ksoftirqd/N)
│  napi_schedule() → __napi_poll() → driver->poll()
│  GRO: napi_gro_receive() → dev_gro_receive()
│       → merges TCP segments into larger sk_buff (reduces syscall overhead)
│
▼
netif_receive_skb() → __netif_receive_skb_core()
│
├── (2) XDP hook (if loaded): BPF prog runs here, BEFORE sk_buff
│        xdp_do_generic_rx() — generic XDP (slower, sk_buff exists)
│        or native XDP in driver (fastest, no sk_buff yet)
│        Return codes: XDP_PASS, XDP_DROP, XDP_TX, XDP_REDIRECT
│
├── (3) ptype_all handlers (packet sniffers: tcpdump, AF_PACKET)
│
├── (4) VLAN stripping: skb_vlan_untag()
│
└── (5) Deliver to protocol handler: packet_type->func()
         ip_rcv() for IPv4 / ipv6_rcv() for IPv6

ip_rcv() → ip_rcv_core() → ip_rcv_finish()
│
├── (6) netfilter NF_INET_PRE_ROUTING hook:
│        nf_hook(NFPROTO_IPV4, NF_INET_PRE_ROUTING, ...)
│        → Conntrack: nf_conntrack_in() creates/lookups ct entry
│        → iptables raw table: skip conntrack if NOTRACK
│        → iptables nat table PREROUTING: DNAT rules
│           (kube-proxy installs KUBE-SERVICES → KUBE-SVC-XXX → KUBE-SEP-XXX)
│           DNAT changes skb->dst, updates skb network header
│
├── (7) Routing decision: ip_route_input_noref() → fib_lookup()
│        FIB = Forwarding Information Base (kernel routing table)
│        Result: rt_input (local delivery) or rt_forward
│
├── (8a) Local delivery: ip_local_deliver()
│         netfilter NF_INET_LOCAL_IN hook
│         → iptables filter INPUT chain
│         → Protocol demux: tcp_v4_rcv() / udp_rcv()
│
└── (8b) Forward: ip_forward()
          netfilter NF_INET_FORWARD hook
          → iptables filter FORWARD chain
          ip_output() → NF_INET_POST_ROUTING → NF_INET_LOCAL_OUT
          → dst_output() → ip_finish_output()

tcp_v4_rcv():
│  sk = __inet_lookup_skb()  → find matching struct sock by 4-tuple
│  tcp_v4_do_rcv() → tcp_rcv_established() (fast path) or tcp_rcv_state_process()
│  __sk_add_backlog() if socket busy, else tcp_queue_rcv()
│  sk->sk_data_ready() → wake up blocked recv() / epoll
│
▼
Application: recv(fd, buf, len, 0)
  → sock->ops->recvmsg() → tcp_recvmsg()
  → copy from sk_receive_queue (sk_buff list) to userspace
  → copy_to_iter() (zero-copy with MSG_ZEROCOPY or io_uring on modern kernels)
```

### 3.3 netfilter Hooks — Where iptables/nftables/BPF Intercept

```
Packet flow through netfilter framework:

INCOMING PACKET:
                      ┌─────────────────────────────────────┐
                      │           NETWORK INTERFACE          │
                      └──────────────┬──────────────────────┘
                                     │
                          NF_INET_PRE_ROUTING ◄─── DNAT (kube-proxy KUBE-SVC-*)
                          (raw, conntrack, nat)     LoadBalancer → PodIP
                                     │
                    ┌────────────────┴────────────────────┐
                    │                                     │
           [Route to local]                      [Route to forward]
                    │                                     │
         NF_INET_LOCAL_IN                      NF_INET_FORWARD
         (filter INPUT)                        (filter FORWARD)
         (mangle INPUT)                        (mangle FORWARD)
                    │                                     │
           [Application]                       NF_INET_POST_ROUTING
                                               (SNAT/MASQUERADE)
OUTGOING PACKET:
           [Application]
                    │
         NF_INET_LOCAL_OUT
         (raw, conntrack, mangle, nat, filter)
                    │
         NF_INET_POST_ROUTING
         (mangle, nat POSTROUTING: MASQUERADE)
                    │
                 [NIC TX]

kube-proxy iptables rules (what actually exists on a node):
──────────────────────────────────────────────────────────────
-A PREROUTING -m comment --comment "kubernetes service portals"
   -j KUBE-SERVICES

-A KUBE-SERVICES -d 10.96.0.1/32 -p tcp --dport 443
   -j KUBE-SVC-NPX46M4PTMTKRN6Y    # kubernetes API server

-A KUBE-SVC-NPX46M4PTMTKRN6Y      # load balance across endpoints
   -m statistic --mode random --probability 0.33333
   -j KUBE-SEP-XXXX1               # endpoint 1

-A KUBE-SEP-XXXX1                  # DNAT to pod IP
   -p tcp -j DNAT --to-destination 192.168.1.5:6443

Real numbers on a 100-node cluster:
  iptables rules: ~5000-50000 rules (O(N) lookup = problematic)
  ipvs: O(1) hash table (preferred for large clusters)
  Cilium eBPF: O(1) hash map, bypasses iptables entirely
```

### 3.4 eBPF/XDP — The Modern Fast Path

```
eBPF program attachment points relevant to Gateway API:

┌──────────────────────────────────────────────────────────────────────────────┐
│                         eBPF Hook Points                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  XDP (eXpress Data Path) — before sk_buff allocation:                        │
│  ├── Native XDP: in NIC driver RX loop (fastest, <1µs)                      │
│  │   attach: ip link set dev eth0 xdp obj prog.o                            │
│  │   use: DDoS mitigation, fast L4 LB (Cilium Maglev), packet mangling      │
│  └── Generic XDP: in netif_receive_skb (slower, any NIC)                   │
│                                                                              │
│  TC (Traffic Control) BPF — after sk_buff, on ingress/egress:               │
│  ├── tc ingress: before netfilter PREROUTING                                │
│  │   tc qdisc add dev eth0 clsact                                           │
│  │   tc filter add dev eth0 ingress bpf obj prog.o                         │
│  │   use: Cilium's kube-proxy replacement, network policy enforcement       │
│  └── tc egress: after netfilter POSTROUTING                                 │
│                                                                              │
│  Socket BPF:                                                                 │
│  ├── BPF_PROG_TYPE_SOCK_OPS: TCP state transitions, congestion control      │
│  ├── BPF_PROG_TYPE_SK_SKB: stream parsing, socket redirect                 │
│  │   use: Cilium sockmap for pod-to-pod bypass (no IP routing needed)       │
│  └── BPF_PROG_TYPE_SK_MSG: sendmsg interception                            │
│                                                                              │
│  Cgroup BPF:                                                                 │
│  ├── BPF_PROG_TYPE_CGROUP_SKB: per-cgroup packet filtering                 │
│  └── BPF_PROG_TYPE_CGROUP_SOCK_ADDR: connect() / bind() address rewrite    │
│      use: Cilium transparent proxy, pod IP assignment                        │
│                                                                              │
│  Kprobe/Tracepoint BPF (observability):                                     │
│  ├── tracepoint:net:netif_receive_skb                                       │
│  ├── tracepoint:net:net_dev_xmit                                            │
│  └── kprobe:tcp_v4_rcv (latency tracking)                                  │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘

Cilium eBPF Gateway L4LB Flow (bypasses iptables entirely):

NIC RX → XDP/TC BPF program:
  1. Parse outer headers (Ethernet + IP + TCP)
  2. Lookup 5-tuple in BPF hash map (bpf_map_type: BPF_MAP_TYPE_LRU_HASH)
  3. CT (connection tracking) in BPF map → check if established
  4. New flow: Maglev hash → select backend
  5. Write backend IP+port into packet (DNAT)
  6. Update CT map
  7. XDP_TX back out (for hairpin LB) or redirect to veth

Maps used by Cilium:
  cilium_ct4_global    BPF_MAP_TYPE_LRU_HASH  (conntrack, 512K entries default)
  cilium_lb4_services  BPF_MAP_TYPE_HASH      (service VIP → backend list)
  cilium_lb4_backends  BPF_MAP_TYPE_HASH      (backend ID → IP:port)
  cilium_ipcache       BPF_MAP_TYPE_HASH      (IP → security identity)
  cilium_policy        BPF_MAP_TYPE_HASH      (identity pair → allow/deny)
```

### 3.5 Network Namespaces — Isolation Primitive

```
Network Namespaces (netns) — what isolates pods from each other and the host:

HOST NETNS                          POD NETNS (pid=12345)
─────────────────                   ──────────────────────
lo (loopback)                       lo (own loopback)
eth0 (physical/virtual NIC)         eth0 → (veth1 inside pod netns)
  IP: 192.168.0.10                    IP: 10.244.1.15/24 (PodIP)
veth0 ← (host end of veth pair)     GW: 10.244.1.1 (routes out via veth)
  IP: 10.244.1.1/32
iptables/nftables rules
BPF programs on veth0
  
veth pair creation (what CNI does during pod start):
  ip link add veth0 type veth peer name eth0
  ip link set eth0 netns /proc/12345/ns/net
  ip addr add 10.244.1.1/32 dev veth0
  ip link set veth0 up
  nsenter -n/proc/12345/ns/net -- ip addr add 10.244.1.15/24 dev eth0
  nsenter -n/proc/12345/ns/net -- ip route add default via 10.244.1.1

Kernel syscalls:
  clone(CLONE_NEWNET)  → creates new netns
  unshare(CLONE_NEWNET)
  setns(fd, CLONE_NEWNET) → join existing netns
  open("/proc/self/ns/net", O_RDONLY) → get netns fd for persistence

Each netns has its own:
  - Routing table (fib_table)
  - iptables/nftables ruleset
  - Network devices
  - Socket table
  - conntrack table
  - sysctl parameters (net.ipv4.*, net.core.*)
```

---

## 4. Cloud Network Substrate

### 4.1 AWS VPC Networking

```
AWS VPC Architecture (what underlies EKS Gateway API):

┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS REGION                                      │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                           VPC (10.0.0.0/16)                           │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────┐  │   │
│  │  │   AZ-a (10.0.1.0/24)   │    │     AZ-b (10.0.2.0/24)          │  │   │
│  │  │                         │    │                                  │  │   │
│  │  │ ┌─────────────────────┐ │    │ ┌──────────────────────────────┐│  │   │
│  │  │ │ EKS Node (EC2)      │ │    │ │ EKS Node (EC2)               ││  │   │
│  │  │ │ ┌───────────────┐   │ │    │ │ ┌────────────────────────┐   ││  │   │
│  │  │ │ │ Gateway Pod   │   │ │    │ │ │ App Pod                │   ││  │   │
│  │  │ │ │ (Envoy)       │   │ │    │ │ │ 10.0.1.55:8080         │   ││  │   │
│  │  │ │ │ 10.0.1.20:443 │   │ │    │ │ └────────────────────────┘   ││  │   │
│  │  │ │ └───────────────┘   │ │    │ └──────────────────────────────┘│  │   │
│  │  │ │   ENI: eth0          │ │    │    ENI: eth0                    │  │   │
│  │  │ │   ENI: eth1 (pods)   │ │    │    ENI: eth1 (pods)            │  │   │
│  │  │ └─────────────────────┘ │    └─────────────────────────────────┘  │   │
│  │  └─────────────────────────┘                                          │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │              AWS Load Balancer (NLB or ALB)                      │ │   │
│  │  │  NLB (L4):                                                      │ │   │
│  │  │    - AWS Gateway API LBC creates TargetGroup per HTTPRoute       │ │   │
│  │  │    - Registers pod IPs directly (IP target mode, not instance)  │ │   │
│  │  │    - Preserves src IP (no SNAT)                                 │ │   │
│  │  │    - Connection tracking in AWS Nitro hypervisor                │ │   │
│  │  │    - ~100µs added latency                                       │ │   │
│  │  │  ALB (L7):                                                      │ │   │
│  │  │    - SSL termination in ALB                                     │ │   │
│  │  │    - X-Forwarded-For header injection                          │ │   │
│  │  │    - WAF integration                                            │ │   │
│  │  │    - ~1ms added latency (TLS + HTTP parsing)                   │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  │                                                                      │   │
│  │  ENA (Elastic Network Adapter) details:                             │   │
│  │    - Up to 100 Gbps on c5n.18xlarge                               │   │
│  │    - Interrupt coalescing: 50µs default (tunable)                  │   │
│  │    - RSS: up to 32 queues (one per vCPU)                          │   │
│  │    - ENA Express (SRD): 1M IOPS @ 8µs p99 latency                │   │
│  │    - SR-IOV: Nitro cards present as PCIe VFs                      │   │
│  │                                                                      │   │
│  │  VPC CNI (amazon-vpc-cni-k8s):                                      │   │
│  │    - Pods get secondary IPs from ENI (not overlay!)               │   │
│  │    - Pod IP = real VPC IP = routable within VPC                   │   │
│  │    - No VXLAN overhead (unlike Flannel/Calico overlay)            │   │
│  │    - ENI limit per instance type (e.g. c5.large: 3 ENI × 10 IPs) │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘

AWS Load Balancer Controller (LBC) — Gateway API integration:
  GatewayClass: controller=gateway.k8s.aws/alb or .../nlb
  Gateway: creates ALB/NLB resource via AWS APIs
  HTTPRoute: creates ALB Listener Rules (path/header matching)
  
  When you create an HTTPRoute:
    1. LBC watches HTTPRoute events
    2. Calls AWS ELBV2 CreateRule API
    3. Rule: IF host=api.example.com AND path=/v1/* THEN forward to TG-xxx
    4. TargetGroup: registers pod IPs via RegisterTargets API
    5. Health checks: ALB polls pod HTTP endpoint directly
```

### 4.2 GCP VPC Networking (Andromeda SDN)

```
GCP Andromeda SDN Architecture:

┌────────────────────────────────────────────────────────────────────────────────┐
│                              GCP PROJECT / VPC                                  │
│                                                                                │
│  Andromeda (GCP's virtual network fabric):                                    │
│  - Software-defined, runs on every physical host                              │
│  - Homa protocol (custom UDP-based, not TCP) for hypervisor-to-hypervisor     │
│  - Flow table in Andromeda agent: 5-tuple → action (forward/drop/NAT)        │
│  - Packet processing in DPDK user-space on host (not in Linux kernel)        │
│  - First packet: slow path (controller lookup), subsequent: fast path        │
│                                                                                │
│  GKE Dataplane V2 (based on Cilium eBPF):                                    │
│  - Replaces legacy kube-proxy + iptables                                      │
│  - BPF programs for service load balancing                                    │
│  - Network Policy enforcement in BPF (no iptables)                           │
│  - FQDN-based policies, L7 (HTTP method/path) in Cilium                      │
│                                                                                │
│  GCP HTTPS Load Balancer (Global / Regional):                                 │
│  - Anycast IP: single IP, routes to nearest PoP (130+ PoPs)                  │
│  - Maglev: consistent hashing for backend selection                           │
│  - Layer: sits OUTSIDE the VPC (Google Front End servers)                    │
│  - SSL termination at Google PoP (low RTT for TLS handshake)                 │
│  - Backend: NEG (Network Endpoint Group) — pod IPs directly                  │
│                                                                                │
│  Packet latency budget (same-zone pod-to-pod):                               │
│  - Physical: ~10µs (single rack)                                             │
│  - Software: ~100µs (kernel + Andromeda)                                     │
│  - Cross-zone: ~1-2ms                                                        │
│  - Cross-region: ~30-100ms (speed of light + routing)                        │
│                                                                                │
│  gVNIC (Google Virtual NIC):                                                  │
│  - Custom ASIC on Google servers                                              │
│  - Multi-queue (up to 16 TX/RX queues)                                       │
│  - Up to 100 Gbps per VM (C3 series)                                         │
│  - Jumbo frames: 8896 byte MTU                                                │
│  - GRO/GSO offload                                                            │
└────────────────────────────────────────────────────────────────────────────────┘
```

### 4.3 Azure VNet + AcceleratedNetworking

```
Azure Networking (AcceleratedNetworking = SR-IOV bypass):

Traditional path (no AccelNet):
  VM guest kernel → hypervisor vSwitch → physical NIC
  Latency: ~500µs, ~1M PPS max

With AcceleratedNetworking (SR-IOV):
  VM guest kernel → SR-IOV VF driver (Mellanox) → physical NIC
  Bypasses hypervisor vSwitch completely
  Latency: ~25µs, ~10M PPS on HBv3
  
AKS networking options:
  1. Kubenet (overlay): pods get 10.244.0.0/16, SNAT at node level
  2. Azure CNI: pods get VNet IPs (like AWS VPC CNI)
  3. Azure CNI Overlay: pods get private overlay IPs, no VNet IP exhaustion
  4. Cilium (BYOCNI): full eBPF data plane

Azure Application Gateway for Containers (AGFC):
  - New Gateway API native implementation (GA 2024)
  - GatewayClass: gateway.networking.azure.io/alb-controller  
  - Ingress: Azure Load Balancer (L4)
  - HTTPRoute → AppGW routing rules
  - BackendTLSPolicy → end-to-end TLS to pods
  - Supports: MTLS, header mutation, URL rewrite, connection draining
```

---

## 5. Gateway API Resource Model

### 5.1 Resource Hierarchy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     GATEWAY API RESOURCE HIERARCHY                           │
│                                                                             │
│  CLUSTER SCOPE:                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  GatewayClass  (cluster-scoped)                                      │  │
│  │  ─────────────                                                       │  │
│  │  .spec.controllerName: "gateway.envoyproxy.io/gatewayclass-controller"│  │
│  │  .spec.parametersRef → GatewayClassParameters (impl-specific config) │  │
│  │  .status.conditions:                                                  │  │
│  │    - type: Accepted, status: True   (controller watching this class) │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           │                                                                 │
│           │  referenced by                                                  │
│           ▼                                                                 │
│  NAMESPACE SCOPE (infra team namespace):                                    │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Gateway  (namespaced)                                               │  │
│  │  ─────────                                                           │  │
│  │  .spec.gatewayClassName: "eg"  → references GatewayClass            │  │
│  │  .spec.listeners[]:                                                  │  │
│  │    - name: http,  port: 80,  protocol: HTTP                         │  │
│  │    - name: https, port: 443, protocol: HTTPS,                       │  │
│  │        tls.mode: Terminate, certificateRefs: [{name: tls-cert}]     │  │
│  │    - name: grpc,  port: 8443, protocol: HTTPS                       │  │
│  │    - name: tcp,   port: 9000, protocol: TCP                         │  │
│  │  .spec.addresses[]:  (optional, request specific IPs)               │  │
│  │    - type: IPAddress, value: "203.0.113.50"                         │  │
│  │  .status.addresses[]: (assigned by controller)                      │  │
│  │    - type: IPAddress, value: "203.0.113.50"                         │  │
│  │  .status.listeners[].conditions:                                    │  │
│  │    - Accepted: True / False                                         │  │
│  │    - Programmed: True / False                                       │  │
│  │    - ResolvedRefs: True / False                                     │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           │                                                                 │
│           │  attached by parentRef                                          │
│           ▼                                                                 │
│  NAMESPACE SCOPE (app team namespaces):                                     │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  HTTPRoute  │  GRPCRoute  │  TCPRoute  │  TLSRoute  │  UDPRoute     │  │
│  │  ──────────────────────────────────────────────────────────────     │  │
│  │  .spec.parentRefs[]:                                                 │  │
│  │    - name: prod-gateway                                              │  │
│  │      namespace: infra  (needs ReferenceGrant if cross-ns)           │  │
│  │      sectionName: https  (which listener)                           │  │
│  │  .spec.hostnames[]: ["api.example.com"]                             │  │
│  │  .spec.rules[]:                                                     │  │
│  │    - matches[]: [{path: {type: PathPrefix, value: /v1}}]            │  │
│  │      filters[]: [{type: RequestHeaderModifier, ...}]                │  │
│  │      backendRefs[]: [{name: api-svc, port: 8080, weight: 100}]     │  │
│  │  .status.parents[].conditions:                                      │  │
│  │    - Accepted: True                                                  │  │
│  │    - ResolvedRefs: True                                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│           │                                                                 │
│           │  routes to                                                      │
│           ▼                                                                 │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  Service / ServiceImport  (Kubernetes core)                          │  │
│  │  BackendTLSPolicy (attached to Service, controls backend TLS)        │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 5.2 GatewayClass — Full Spec

```yaml
# GatewayClass: cluster-level, created by infra team, references a controller
apiVersion: gateway.networking.k8s.io/v1
kind: GatewayClass
metadata:
  name: eg                          # referenced by Gateways
  annotations:
    # Implementation-specific: describe the class
    gateway.envoyproxy.io/owning-gateway-name: "production"
spec:
  controllerName: gateway.envoyproxy.io/gatewayclass-controller
  # ^ Must match what the controller announces in its leader election
  # ^ Controller watches GatewayClasses where .spec.controllerName == its own name

  description: "Envoy Gateway - Production class with WAF and rate limiting"

  parametersRef:                    # optional, impl-specific config object
    group: gateway.envoyproxy.io
    kind: EnvoyProxy
    name: default
    namespace: envoy-gateway-system
    # Note: parametersRef can be cluster-scoped or namespaced
    # cluster-scoped: no namespace field needed

status:
  conditions:
    - type: Accepted
      status: "True"
      reason: Accepted
      message: "The gateway class has been accepted by the controller"
      observedGeneration: 1
      lastTransitionTime: "2024-01-15T10:00:00Z"
```

### 5.3 Gateway — Full Spec with All Options

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: Gateway
metadata:
  name: prod-gateway
  namespace: infra
  annotations:
    # AWS LBC example:
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  gatewayClassName: eg

  listeners:
    # ── L4 HTTP (redirect to HTTPS) ──────────────────────────────────────
    - name: http
      port: 80
      protocol: HTTP
      hostname: "*.example.com"     # wildcard hostname
      allowedRoutes:
        namespaces:
          from: Selector             # specific namespaces via label selector
          selector:
            matchLabels:
              gateway-access: "true"
        kinds:
          - group: gateway.networking.k8s.io
            kind: HTTPRoute

    # ── L7 HTTPS (TLS termination) ────────────────────────────────────────
    - name: https
      port: 443
      protocol: HTTPS
      hostname: "api.example.com"
      tls:
        mode: Terminate             # Terminate (decrypt) vs Passthrough
        certificateRefs:
          - kind: Secret
            name: api-tls-cert
            namespace: infra        # must ReferenceGrant if different ns
          # cert-manager auto-provisioned:
          # - kind: Secret
          #   name: api-tls-cert
          # supports SNI: multiple certs for multiple hostnames on same port
      allowedRoutes:
        namespaces:
          from: All                 # any namespace can attach routes

    # ── TLS Passthrough (SNI routing, no decrypt) ─────────────────────────
    - name: tls-passthrough
      port: 8443
      protocol: TLS
      tls:
        mode: Passthrough           # forward encrypted, TLSRoute matches SNI
      allowedRoutes:
        kinds:
          - kind: TLSRoute

    # ── L4 TCP ────────────────────────────────────────────────────────────
    - name: tcp-postgres
      port: 5432
      protocol: TCP
      allowedRoutes:
        kinds:
          - kind: TCPRoute

    # ── gRPC (HTTPS listener, GRPCRoute attaches) ─────────────────────────
    - name: grpc
      port: 50051
      protocol: HTTPS
      tls:
        mode: Terminate
        certificateRefs:
          - name: grpc-tls-cert

    # ── UDP ───────────────────────────────────────────────────────────────
    - name: dns-udp
      port: 53
      protocol: UDP
      allowedRoutes:
        kinds:
          - kind: UDPRoute

  # Request a specific IP from the cloud provider
  addresses:
    - type: IPAddress
      value: "203.0.113.50"     # must be pre-allocated Elastic IP (AWS) / static IP (GCP)
    - type: Hostname
      value: "gw.example.com"   # hostname-based addressing

  # Infrastructure-level settings (impl-specific via parametersRef on GatewayClass)
  # Most implementations expose these via GatewayClass parametersRef

status:
  addresses:
    - type: IPAddress
      value: "203.0.113.50"
  conditions:
    - type: Accepted
      status: "True"
      reason: Accepted
    - type: Programmed
      status: "True"
      reason: Programmed
      message: "Address assigned and data plane programmed"
  listeners:
    - name: https
      attachedRoutes: 5           # 5 HTTPRoutes attached
      conditions:
        - type: Accepted
          status: "True"
        - type: Programmed
          status: "True"
        - type: ResolvedRefs
          status: "True"
```

---

## 6. Role-Based Access & Trust Hierarchy

### 6.1 The Three Personas

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                        GATEWAY API ROLE SEPARATION                           │
│                                                                              │
│  PERSONA 1: Infrastructure Provider                                         │
│  ─────────────────────────────────                                          │
│  Who: Cloud team, platform team, SRE                                        │
│  What they own: GatewayClass                                                │
│  Concern: Which controller implementation to use, global config             │
│  RBAC:                                                                       │
│    rules:                                                                    │
│    - apiGroups: [gateway.networking.k8s.io]                                 │
│      resources: [gatewayclasses]                                            │
│      verbs: [get, list, watch, create, update, patch, delete]               │
│                                                                              │
│  PERSONA 2: Cluster Operator                                                │
│  ─────────────────────────────                                              │
│  Who: Platform engineering, infra namespace owners                          │
│  What they own: Gateway (in infra namespace)                                │
│  Concern: Which ports exposed, TLS certs, which namespaces can attach       │
│  RBAC:                                                                       │
│    rules:                                                                    │
│    - apiGroups: [gateway.networking.k8s.io]                                 │
│      resources: [gateways]                                                  │
│      verbs: [get, list, watch, create, update, patch, delete]               │
│    - apiGroups: [""]                                                         │
│      resources: [secrets]   # for TLS cert refs                            │
│      verbs: [get, list, watch]                                              │
│                                                                              │
│  PERSONA 3: Application Developer                                           │
│  ─────────────────────────────────                                          │
│  Who: Product team, dev team                                                │
│  What they own: HTTPRoute/GRPCRoute (in their app namespace)                │
│  Concern: Which paths/hosts route to my Service, traffic splitting          │
│  RBAC:                                                                       │
│    rules:                                                                    │
│    - apiGroups: [gateway.networking.k8s.io]                                 │
│      resources: [httproutes, grpcroutes]                                    │
│      verbs: [get, list, watch, create, update, patch, delete]               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 6.2 ReferenceGrant — Cross-Namespace Trust

The critical security resource: by default, a route in namespace A **cannot** reference a
backend in namespace B. ReferenceGrant explicitly permits this.

```yaml
# Problem: HTTPRoute in 'app-team-a' namespace wants to forward to
# Service in 'shared-services' namespace

# Without ReferenceGrant: REJECTED with reason=RefNotPermitted

# Solution: Apply ReferenceGrant in the TARGET namespace (shared-services)
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: allow-app-team-a
  namespace: shared-services         # ← lives in the TARGET namespace
spec:
  from:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
      namespace: app-team-a          # ← who is allowed to reference
  to:
    - group: ""
      kind: Service                  # ← what they can reference
      # name: specific-service       # optional: restrict to specific Service
      # omit 'name' to allow any Service in this namespace

---
# Also needed when Gateway references Secret in another namespace:
apiVersion: gateway.networking.k8s.io/v1beta1
kind: ReferenceGrant
metadata:
  name: allow-gateway-tls
  namespace: cert-ns
spec:
  from:
    - group: gateway.networking.k8s.io
      kind: Gateway
      namespace: infra
  to:
    - group: ""
      kind: Secret
      name: wildcard-tls-cert        # specific secret only
```

### 6.3 Gateway Listener allowedRoutes

```
Gateway controls which routes can attach — defense in depth:

spec.listeners[].allowedRoutes:
  namespaces:
    from: Same        → only routes in Gateway's own namespace
    from: All         → any namespace
    from: Selector    → namespaces matching label selector
      selector:
        matchLabels:
          environment: production
        matchExpressions:
          - key: tier
            operator: In
            values: [frontend, api]
  kinds:
    - group: gateway.networking.k8s.io
      kind: HTTPRoute
    # Can restrict to only HTTPRoute, preventing GRPCRoute from attaching
    # to an HTTP listener (important for protocol correctness)

Route attachment algorithm (controller enforces):
  1. Route.spec.parentRefs matches Gateway by name/namespace ✓
  2. Gateway listener.allowedRoutes.namespaces allows route's namespace ✓
  3. Gateway listener.allowedRoutes.kinds allows route's kind ✓
  4. Gateway listener protocol is compatible with route kind ✓
  5. If Gateway uses TLS: ReferenceGrant allows Secret access ✓
  → Result: route is ACCEPTED, listed in Gateway.status.listeners.attachedRoutes
```

---

## 7. Routing: HTTPRoute, GRPCRoute, TCPRoute, TLSRoute, UDPRoute

### 7.1 HTTPRoute — Complete Reference

```yaml
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: app-team
spec:
  parentRefs:
    - name: prod-gateway
      namespace: infra
      sectionName: https    # attach to specific listener by name
      port: 443             # optional, but explicit is better

  hostnames:
    - "api.example.com"
    - "api.example.org"
    # Wildcard: "*.example.com"  (matches sub.example.com but not example.com)

  rules:
    # ─── Rule 1: Version routing + header matching ──────────────────────
    - matches:
        - path:
            type: PathPrefix          # PathPrefix, Exact, RegularExpression
            value: /v2
          headers:
            - name: X-API-Version
              type: Exact             # Exact, RegularExpression
              value: "2"
          queryParams:
            - name: format
              type: Exact
              value: json
          method: GET                 # HTTP method matching

      filters:
        # RequestHeaderModifier: add/set/remove request headers
        - type: RequestHeaderModifier
          requestHeaderModifier:
            add:
              - name: X-Forwarded-Host
                value: "api.example.com"
              - name: X-Request-Id
                value: "${request.id}"   # impl-specific templating
            set:
              - name: X-API-Version
                value: "2.0"
            remove:
              - X-Internal-Token

        # ResponseHeaderModifier: modify response headers
        - type: ResponseHeaderModifier
          responseHeaderModifier:
            add:
              - name: Strict-Transport-Security
                value: "max-age=31536000; includeSubDomains; preload"
              - name: X-Content-Type-Options
                value: nosniff
            remove:
              - Server
              - X-Powered-By

        # RequestRedirect: HTTP redirect
        # (use for HTTP→HTTPS redirect on port 80 listener)
        # - type: RequestRedirect
        #   requestRedirect:
        #     scheme: https
        #     statusCode: 301
        #     hostname: "api.example.com"
        #     port: 443

        # URLRewrite: rewrite path/hostname before forwarding
        - type: URLRewrite
          urlRewrite:
            hostname: "internal-api.svc.cluster.local"
            path:
              type: ReplacePrefixMatch   # ReplacePrefixMatch, ReplaceFullPath
              replacePrefixMatch: /

        # RequestMirror: shadow traffic (copy to mirror backend, ignore response)
        - type: RequestMirror
          requestMirror:
            backendRef:
              name: api-v3-canary
              port: 8080
            percent: 10               # mirror 10% of traffic

        # ExtensionRef: implementation-specific (e.g., Envoy rate limit)
        # - type: ExtensionRef
        #   extensionRef:
        #     group: gateway.envoyproxy.io
        #     kind: HTTPRouteFilter
        #     name: rate-limit-policy

      backendRefs:
        - name: api-svc
          namespace: app-team
          port: 8080
          weight: 90                  # 90% to stable
        - name: api-svc-canary
          namespace: app-team
          port: 8080
          weight: 10                  # 10% canary
          # filters on backendRef (response header modifiers, etc.)
          filters:
            - type: RequestHeaderModifier
              requestHeaderModifier:
                add:
                  - name: X-Canary
                    value: "true"

      # Timeouts (Gateway API 1.0+)
      timeouts:
        request: 30s                  # total request timeout
        backendRequest: 10s           # per-backend call timeout

      # Session persistence (Gateway API 1.1+, experimental)
      sessionPersistence:
        sessionName: SESSIONID
        absoluteTimeout: 1h
        idleTimeout: 30m
        type: Cookie                  # Cookie or Header
        cookieConfig:
          lifetimeType: Permanent

    # ─── Rule 2: Static redirect ─────────────────────────────────────────
    - matches:
        - path:
            type: PathPrefix
            value: /old-api
      filters:
        - type: RequestRedirect
          requestRedirect:
            path:
              type: ReplacePrefixMatch
              replacePrefixMatch: /v2
            statusCode: 301

    # ─── Rule 3: Default backend (no match → catch-all) ──────────────────
    - backendRefs:
        - name: default-backend-svc
          port: 8080
      # No 'matches' field = matches everything not caught by previous rules
      # (Rules are evaluated in order; first match wins)
```

### 7.2 Match Priority Algorithm (Important!)

```
HTTPRoute Match Priority (per spec):
  1. Longest matching hostname (exact > wildcard > no hostname)
     "api.example.com" > "*.example.com" > ""
  2. Within same hostname: most specific path match
     Exact > PathPrefix (longer > shorter) > RegularExpression
  3. Within same path: most specific header/queryParam match
     (more matches = more specific)
  4. Multiple HTTPRoutes same hostname+path: merge if no conflict
     CONFLICT (same hostname+path+match, different backends) → 
     status.parents[].conditions: Accepted=False, reason=Conflicted

Real example:
  RouteA: host=api.example.com, path=/v2/users  → svc-users
  RouteB: host=api.example.com, path=/v2        → svc-api
  RouteC: host=*.example.com,   path=/          → svc-default

  Request: GET api.example.com/v2/users/123
  → RouteA wins (exact host + longer path prefix)

  Request: GET api.example.com/v2/products
  → RouteB wins (exact host + path prefix /v2)

  Request: GET other.example.com/anything
  → RouteC wins (wildcard host)
```

### 7.3 GRPCRoute — Full Spec

```yaml
# GRPCRoute: GA in Gateway API v1.1
# Matches on gRPC service/method (which are HTTP/2 paths like /package.Service/Method)
apiVersion: gateway.networking.k8s.io/v1
kind: GRPCRoute
metadata:
  name: user-grpc-route
  namespace: app-team
spec:
  parentRefs:
    - name: prod-gateway
      sectionName: grpc    # must be HTTPS listener (gRPC runs over HTTP/2)

  hostnames:
    - "grpc.example.com"

  rules:
    # ─── Match specific service/method ───────────────────────────────────
    - matches:
        - method:
            type: Exact        # Exact or RegularExpression
            service: "user.v1.UserService"   # gRPC service (proto package.Service)
            method: "GetUser"               # optional: specific RPC method
          headers:
            - name: x-tenant-id
              type: Exact
              value: "tenant-a"
      filters:
        - type: RequestHeaderModifier
          requestHeaderModifier:
            add:
              - name: grpc-timeout
                value: 5S         # gRPC timeout header (seconds)
      backendRefs:
        - name: user-service
          port: 50051
          weight: 100

    # ─── Match entire service (all methods) ──────────────────────────────
    - matches:
        - method:
            type: Exact
            service: "admin.v1.AdminService"
            # no 'method' field = matches all methods in this service
      backendRefs:
        - name: admin-service
          port: 50051

    # ─── Default: catch-all for other gRPC calls ─────────────────────────
    - backendRefs:
        - name: grpc-default
          port: 50051

# Under the hood: gRPC path = /user.v1.UserService/GetUser
# Gateway API GRPCRoute converts this to HTTP path match:
#   Path Exact: /user.v1.UserService/GetUser
# And adds Content-Type: application/grpc* check
```

### 7.4 TCPRoute, TLSRoute, UDPRoute

```yaml
# TCPRoute: L4 TCP forwarding (no HTTP awareness)
# Status: Experimental in Gateway API v1.2
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TCPRoute
metadata:
  name: postgres-route
spec:
  parentRefs:
    - name: prod-gateway
      sectionName: tcp-postgres
      namespace: infra
  rules:
    - backendRefs:
        - name: postgres-svc
          port: 5432
          weight: 100
      # TCPRoute has no match criteria beyond listener port
      # (routing is purely by destination port on the Gateway listener)

---
# TLSRoute: L4 TLS with SNI routing (no decrypt)
# The Gateway listener must have protocol: TLS and tls.mode: Passthrough
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: TLSRoute
metadata:
  name: internal-mtls-route
spec:
  parentRefs:
    - name: prod-gateway
      sectionName: tls-passthrough
  hostnames:
    - "db.internal.example.com"   # SNI hostname (from TLS ClientHello)
    # The gateway reads the SNI extension from TLS ClientHello
    # WITHOUT decrypting the connection
  rules:
    - backendRefs:
        - name: db-svc
          port: 5432              # backend handles TLS itself

---
# UDPRoute: L4 UDP forwarding
# Status: Experimental
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: UDPRoute
metadata:
  name: dns-route
spec:
  parentRefs:
    - name: prod-gateway
      sectionName: dns-udp
  rules:
    - backendRefs:
        - name: coredns
          port: 53
```

---

## 8. Policy Attachment (ReferenceGrant, BackendPolicy, etc.)

### 8.1 Policy Attachment Model

Gateway API defines a standard way to attach policy to resources via `targetRef`.
This is the foundation for: BackendTLSPolicy, BackendLBPolicy, and implementation-specific
policies (Envoy RateLimitPolicy, AuthPolicy, etc.)

```
Policy Attachment Hierarchy (Direct vs Inherited):

Direct attachment (most specific, highest priority):
  Policy → HTTPRoute     (applies to traffic matching that route)
  Policy → Service       (applies to traffic going to that backend)

Inherited attachment (less specific, lower priority):
  Policy → Gateway       (applies to all routes on gateway)
  Policy → GatewayClass  (applies to all gateways in the class)

Conflict resolution:
  More specific wins: HTTPRoute policy > Gateway policy > GatewayClass policy
  Within same level: first created policy wins (controllers must document this)

┌────────────────────────────────────────────────────────────────────────────┐
│  Policy Attachment Precedence (highest to lowest)                          │
├────────────────────────────────────────────────────────────────────────────┤
│  1. Service-level  BackendTLSPolicy on Service                            │
│  2. HTTPRoute-level AuthPolicy on HTTPRoute                               │
│  3. Gateway-level  RateLimitPolicy on Gateway                             │
│  4. GatewayClass-level default policy                                     │
└────────────────────────────────────────────────────────────────────────────┘
```

### 8.2 BackendTLSPolicy

```yaml
# BackendTLSPolicy: controls TLS from Gateway/proxy TO the backend Service
# This is for end-to-end encryption (gateway terminates client TLS,
# then re-encrypts to backend — "re-encryption" mode)
apiVersion: gateway.networking.k8s.io/v1alpha3
kind: BackendTLSPolicy
metadata:
  name: backend-tls
  namespace: app-team
spec:
  targetRefs:
    - group: ""
      kind: Service
      name: api-svc
      # sectionName: https-port  # optional: target specific port
  validation:
    caCertificateRefs:
      - kind: ConfigMap
        name: backend-ca-cert    # CA that signed backend's certificate
        namespace: app-team
    # OR use well-known CA (system trust store):
    # wellKnownCACertificates: System
    
    hostname: "api-svc.app-team.svc.cluster.local"
    # The hostname used for TLS SNI and certificate verification
    # Must match backend cert's SAN/CN

# What this does at data-plane level:
# Without BackendTLSPolicy: gateway → backend is plain HTTP (mTLS from service mesh aside)
# With BackendTLSPolicy:    gateway → backend is TLS, cert verified against CA
# Combined with client TLS: full end-to-end encryption (no plaintext inside cluster)
```

### 8.3 BackendLBPolicy (experimental)

```yaml
# BackendLBPolicy: controls load balancing algorithm per-backend
apiVersion: gateway.networking.k8s.io/v1alpha2
kind: BackendLBPolicy
metadata:
  name: session-stickiness
spec:
  targetRefs:
    - kind: Service
      name: stateful-app
  sessionPersistence:
    type: Cookie
    sessionName: BACKEND_SESSION
    cookieConfig:
      lifetimeType: Session     # Session cookie (deleted on browser close)
  # Note: implementation-specific (Envoy, NGINX, etc. interpret differently)
```

### 8.4 Implementation-Specific Policies (Envoy Gateway Example)

```yaml
# Envoy Gateway: SecurityPolicy (AuthN/AuthZ)
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: jwt-authn
  namespace: app-team
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: api-route
  jwt:
    providers:
      - name: auth0
        issuer: "https://example.auth0.com/"
        audiences:
          - "api.example.com"
        remoteJWKS:
          uri: "https://example.auth0.com/.well-known/jwks.json"
        claimToHeaders:
          - claim: sub
            header: X-User-Id
          - claim: email
            header: X-User-Email
  oidc:
    provider:
      issuer: "https://accounts.google.com"
    clientID: "your-client-id"
    clientSecret:
      name: google-oauth-secret
    redirectURL: "https://api.example.com/oauth2/callback"
    scopes:
      - openid
      - email
      - profile

---
# Envoy Gateway: RateLimitPolicy
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: BackendTrafficPolicy
metadata:
  name: rate-limit
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: HTTPRoute
    name: api-route
  rateLimit:
    type: Global                # Global (distributed via Redis) or Local
    global:
      rules:
        - clientSelectors:
            - headers:
                - name: X-User-Id
                  type: Distinct  # rate limit per unique X-User-Id value
          limit:
            requests: 1000
            unit: Hour
        - clientSelectors:
            - sourceCIDR:
                value: "10.0.0.0/8"
                type: Distinct  # per source IP
          limit:
            requests: 100
            unit: Minute
  circuitBreaker:
    maxConnections: 1024
    maxPendingRequests: 512
    maxParallelRequests: 256
    maxParallelRetries: 64
  timeout:
    http:
      requestTimeout: 30s
      connectionIdleTimeout: 90s
      maxConnectionDuration: 0s  # unlimited
  retry:
    numRetries: 3
    retryOn:
      - ServiceUnavailable
      - InternalServerError
    perRetry:
      timeout: 10s
      backOff:
        baseInterval: 100ms
        maxInterval: 10s
  healthCheck:
    active:
      timeout: 1s
      interval: 3s
      unhealthyThreshold: 3
      healthyThreshold: 1
      http:
        path: /healthz
        expectedStatuses:
          - statusRange:
              start: 200
              end: 299
```

---

## 9. Control Plane Architecture

### 9.1 Controller Reconciliation Loop

```
Gateway API Controller (e.g., Envoy Gateway, AWS LBC):

┌────────────────────────────────────────────────────────────────────────────┐
│                      CONTROLLER RECONCILIATION LOOP                         │
│                                                                            │
│  Kubernetes API Server                                                     │
│  ├── Watch: GatewayClass events   ──────────────────────────────────────► │
│  ├── Watch: Gateway events        ──────────────────────────────────────► │
│  ├── Watch: HTTPRoute events      ──────────────────────────────────────► │
│  ├── Watch: GRPCRoute events      ──────────────────────────────────────► │
│  ├── Watch: Secret events         ──────────────────────────────────────► │
│  ├── Watch: Service/Endpoints events ───────────────────────────────────► │
│  └── Watch: ReferenceGrant events ──────────────────────────────────────► │
│                                                                            │
│                                         Controller Work Queue              │
│  Event received ───────────────────────────────► [item: ns/name/kind]     │
│                                                         │                  │
│                                                    Reconcile()             │
│                                                         │                  │
│                                              ┌──────────┴──────────┐      │
│                                              │  1. Get current state│      │
│                                              │     (k8s resources)  │      │
│                                              │  2. Compute desired  │      │
│                                              │     state (IR)       │      │
│                                              │  3. Translate IR →   │      │
│                                              │     data plane cfg   │      │
│                                              │  4. Push cfg to DP   │      │
│                                              │  5. Update Status    │      │
│                                              └─────────────────────┘      │
│                                                                            │
│  IR = Intermediate Representation (impl-specific)                          │
│  Envoy Gateway IR: xDS resources (Listener, RouteConfiguration, Cluster)  │
│  AWS LBC IR: TargetGroup, ListenerRule API calls                           │
│  Cilium IR: BPF map updates                                                │
│                                                                            │
└────────────────────────────────────────────────────────────────────────────┘

Status reconciliation:
  After pushing config to data plane:
  1. Verify data plane has applied config (via xDS ACK, or API response)
  2. Patch resource status:
     kubectl patch httproute api-route --subresource=status --type=merge \
       --patch '{"status":{"parents":[{"parentRef":{"name":"prod-gateway"},
       "conditions":[{"type":"Accepted","status":"True","reason":"Accepted"}]}]}}'
  3. If error: set Programmed=False with descriptive message
```

### 9.2 xDS Protocol (Envoy/Envoy Gateway Data Plane Config)

```
xDS = Discovery Service APIs — how Envoy's control plane pushes config:

┌──────────────────────────────────────────────────────────────────────────┐
│                          xDS Resource Types                               │
├──────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  LDS (Listener Discovery Service):                                       │
│  → Maps to: Gateway.spec.listeners                                       │
│  → Envoy Listener: bind address, filter chain, TLS config, downstream   │
│                                                                          │
│  RDS (Route Discovery Service):                                          │
│  → Maps to: HTTPRoute.spec.rules[].matches + filters                    │
│  → Envoy RouteConfiguration: virtual hosts, routes, cluster names       │
│                                                                          │
│  CDS (Cluster Discovery Service):                                        │
│  → Maps to: HTTPRoute.spec.rules[].backendRefs → Service                │
│  → Envoy Cluster: upstream name, load balancing, health checks          │
│                                                                          │
│  EDS (Endpoint Discovery Service):                                       │
│  → Maps to: Service endpoints (pod IPs)                                 │
│  → Envoy ClusterLoadAssignment: endpoint IPs, weights, health           │
│                                                                          │
│  SDS (Secret Discovery Service):                                         │
│  → Maps to: TLS certs (from Secrets)                                    │
│  → Envoy TlsCertificate: cert, key (rotated without restart)            │
│                                                                          │
│  RTDS (Runtime Discovery Service):                                       │
│  → Feature flags, runtime parameters                                    │
│                                                                          │
│  Control plane → Envoy flow:                                             │
│                                                                          │
│  Controller ──gRPC stream──► Envoy                                      │
│     LDS: [{listener on :443, filter_chain: [...]}]                      │
│     Envoy: ACK (version_info matches)                                    │
│     RDS: [{virtual_host: api.example.com, routes: [...]}]               │
│     Envoy: ACK                                                           │
│     CDS: [{cluster: app-team/api-svc/8080, lb_policy: ROUND_ROBIN}]    │
│     Envoy: ACK                                                           │
│     EDS: [{cluster_name: ..., endpoints: [10.244.1.5:8080, ...]}]      │
│     Envoy: ACK                                                           │
│                                                                          │
│  Delta xDS (incremental):                                                │
│  - Sends only changed resources (important for large clusters)           │
│  - Envoy re-subscribes to resources it needs                            │
│  - Critical for 1000+ services (full xDS would be too large)            │
│                                                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 10. Data Plane Architecture

### 10.1 Envoy Proxy Internals

```
Envoy Data Plane Architecture (most common Gateway API data plane):

┌────────────────────────────────────────────────────────────────────────────┐
│                           ENVOY PROXY                                       │
│                                                                            │
│  ┌─────────────┐     ┌──────────────────────────────────────────────────┐ │
│  │  Listener   │     │              Filter Chain                         │ │
│  │  :443       │────►│  ┌────────────────────────────────────────────┐  │ │
│  │  (TCP accept│     │  │ Network Filters (L4):                      │  │ │
│  │   + TLS)    │     │  │  1. envoy.filters.network.http_connection  │  │ │
│  └─────────────┘     │  │     _manager (HCM) — main HTTP/gRPC filter│  │ │
│                      │  │  2. envoy.filters.network.tcp_proxy        │  │ │
│  Thread model:       │  │     (for TCPRoute)                         │  │ │
│  - Main thread:      │  │  3. envoy.filters.network.thrift_proxy     │  │ │
│    config mgmt       │  │     (Thrift RPC)                           │  │ │
│  - Worker threads:   │  │  4. envoy.filters.network.mongo_proxy      │  │ │
│    (one per vCPU)    │  └──────────────────┬─────────────────────────┘  │ │
│    each runs its own │                     │                             │ │
│    event loop        │  ┌──────────────────▼─────────────────────────┐  │ │
│    (libevent-based)  │  │ HTTP Connection Manager (HCM):             │  │ │
│  - No shared state   │  │  HTTP/1.1 parser (nghttp2)                 │  │ │
│    between workers   │  │  HTTP/2 framing (nghttp2)                  │  │ │
│    (per-worker conn  │  │  HTTP/3 (QUIC via quiche/boringssl)        │  │ │
│    pools)            │  │  HTTP Filters (L7, in order):              │  │ │
│                      │  │   1. envoy.filters.http.jwt_authn          │  │ │
│                      │  │   2. envoy.filters.http.ext_authz          │  │ │
│                      │  │      (gRPC call to OPA/authz service)      │  │ │
│                      │  │   3. envoy.filters.http.ratelimit          │  │ │
│                      │  │      (gRPC call to Lyft rate limit svc)    │  │ │
│                      │  │   4. envoy.filters.http.router             │  │ │
│                      │  │      (final filter, does actual routing)   │  │ │
│                      │  └──────────────────┬─────────────────────────┘  │ │
│                      └────────────────────┬┘                            │ │
│                                           │                              │ │
│  ┌────────────────────────────────────────▼──────────────────────────┐  │ │
│  │                        Cluster Manager                              │  │ │
│  │  Cluster: app-team/api-svc/8080                                    │  │ │
│  │  ├── Load Balancer: ROUND_ROBIN / LEAST_REQUEST / RING_HASH       │  │ │
│  │  │   (RING_HASH for session affinity)                              │  │ │
│  │  ├── Outlier Detection: eject unhealthy endpoints                 │  │ │
│  │  │   (5xx rate, latency, consecutive errors)                       │  │ │
│  │  ├── Circuit Breaker: maxConnections, maxPendingRequests           │  │ │
│  │  ├── Connection Pool: per-worker, per-upstream                     │  │ │
│  │  │   HTTP/1.1: max_connections=1024 per cluster per worker        │  │ │
│  │  │   HTTP/2: max_concurrent_streams=100 (default) per conn        │  │ │
│  │  └── Health Checker: active (HTTP GET /health) + passive (5xx)    │  │ │
│  │                                                                    │  │ │
│  │  Upstream Connection (to pod):                                     │  │ │
│  │  ├── TLS (if BackendTLSPolicy): BoringSSL, ALPN h2,http/1.1       │  │ │
│  │  └── TCP: SO_KEEPALIVE, TCP_NODELAY, SO_SNDBUF/SO_RCVBUF tuning   │  │ │
│  └────────────────────────────────────────────────────────────────────┘  │ │
│                                                                            │ │
└────────────────────────────────────────────────────────────────────────────┘
```

### 10.2 Cilium eBPF Gateway (No Envoy)

```
Cilium Gateway API (eBPF-native, no sidecar, no proxy process):

┌────────────────────────────────────────────────────────────────────────────┐
│                        CILIUM GATEWAY API ARCHITECTURE                      │
│                                                                            │
│  Gateway: creates Envoy deployment (Cilium embeds Envoy for L7)           │
│           OR uses native eBPF for L4 (TCPRoute/UDPRoute)                  │
│                                                                            │
│  L4 path (TCPRoute, UDPRoute):                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ XDP/TC BPF program on gateway node NIC:                              │ │
│  │   1. Parse TCP SYN header                                            │ │
│  │   2. Lookup bpf_map: lb4_services (VIP:port → backend list)         │ │
│  │   3. Select backend: Maglev consistent hash or round-robin          │ │
│  │   4. Write DNAT into packet (skb->data manipulation)                │ │
│  │   5. Update CT map (cilium_ct4_global)                              │ │
│  │   6. Redirect to backend veth                                       │ │
│  │   Return traffic: reverse SNAT via CT map lookup                    │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  L7 path (HTTPRoute, GRPCRoute):                                          │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ Envoy deployed as DaemonSet (one per node, not per pod):             │ │
│  │   - Cilium agent configures Envoy via local admin socket            │ │
│  │   - eBPF redirects L7 traffic to Envoy via sockmap                 │ │
│  │   - Envoy processes HTTP, applies policy                            │ │
│  │   - Envoy forwards to backend via eBPF (not kernel routing)        │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                            │
│  Comparison vs kube-proxy+iptables:                                        │
│  kube-proxy:  iptables DNAT O(N) rules, full netstack traversal           │
│  Cilium eBPF: O(1) BPF hash map, early exit (XDP skip netstack)          │
│  Latency:     kube-proxy ~100µs, Cilium ~20µs (5x improvement)           │
│  CPU:         kube-proxy ~30% at 1M pps, Cilium ~10%                     │
└────────────────────────────────────────────────────────────────────────────┘
```

---

## 11. TLS: Termination, Passthrough, mTLS

### 11.1 TLS Termination Flow

```
TLS Termination at Gateway:

Client                    Gateway (Envoy)              Backend Pod
──────                    ───────────────              ───────────
         ClientHello ──►
         (SNI: api.example.com)
                          ├─ SNI lookup → find cert
                          │   (SDS fetch from k8s Secret)
         ◄── ServerHello, Certificate, ServerHelloDone
         ClientKeyExchange ──►
         ChangeCipherSpec ──►
         Finished ──►
         ◄── ChangeCipherSpec, Finished
         [TLS handshake complete: ~1-2 RTT for TLS 1.3, ~2 RTT for TLS 1.2]

         HTTP/2 SETTINGS ──►     (new connection to backend)
                          ├─►    TCP SYN ──────────────────►
                          │      [new connection from gateway to backend]
                          │      IF BackendTLSPolicy: TLS handshake to backend
                          │      ELSE: plain HTTP/2 or HTTP/1.1

TLS 1.3 handshake (default, Gateway API implementations):
  RTTs: 1 RTT (vs TLS 1.2's 2 RTT)
  0-RTT early data: supported (with replay attack consideration)
  Key exchange: X25519 (preferred) or P-256
  Cipher: TLS_AES_256_GCM_SHA384 (preferred), TLS_CHACHA20_POLY1305_SHA256
  
  TLS 1.3 Record format:
  ┌──────────────────────────────────────────────────────────────┐
  │ Content Type: 23 (application_data) [1 byte]                │
  │ Legacy Version: 0x0303 (TLS 1.2 compat) [2 bytes]          │
  │ Length [2 bytes]                                            │
  │ Encrypted Record [N bytes]:                                 │
  │   [actual content type + application data + padding + tag] │
  └──────────────────────────────────────────────────────────────┘
  AEAD tag: 16 bytes (AES-GCM, ChaCha20-Poly1305)
  Max record size: 16384 bytes (16 KiB)
  
Session resumption at Gateway:
  TLS session tickets (encrypted by server, stored by client)
  PSK (Pre-Shared Key) for 0-RTT in TLS 1.3
  Gateway must share session ticket keys across replicas!
  → Use: Envoy session_ticket_keys_sds_secret_configs (rotated via SDS)
  → Without sharing: every failover = full handshake (latency spike)
```

### 11.2 SNI Routing (TLS Passthrough)

```
TLS Passthrough — Gateway reads SNI without decrypting:

TLS ClientHello structure (first message of TLS handshake, plaintext!):
  ┌────────────────────────────────────────────────────────────────────┐
  │ Handshake Type: 1 (ClientHello)                                   │
  │ Length: N                                                         │
  │ Version: 0x0303 (TLS 1.2 compat header even for TLS 1.3)         │
  │ Random: 32 bytes (client random)                                  │
  │ Session ID Length: 0-32 bytes                                     │
  │ Cipher Suites: list of supported                                  │
  │ Compression Methods: 1 byte (always 0 = null)                    │
  │ Extensions:                                                       │
  │   ├── server_name (SNI, type=0):                                 │
  │   │     NameType: 0 (host_name)                                  │
  │   │     Length: N                                                │
  │   │     ServerName: "db.internal.example.com"  ← PLAINTEXT!     │
  │   ├── supported_versions (type=43): [TLS 1.3, TLS 1.2]          │
  │   ├── key_share (type=51): X25519 public key                     │
  │   ├── signature_algorithms (type=13)                             │
  │   └── ALPN (type=16): ["h2", "http/1.1"]                        │
  └────────────────────────────────────────────────────────────────────┘

Gateway reads bytes 0-5 of TCP data to detect TLS:
  0x16 = TLS record type (22 = handshake)
  0x03 0x01 = legacy version (TLS 1.0 compat)
Then peeks into ClientHello to extract SNI extension.
This is how Envoy/NGINX implement passthrough routing.

Linux-level: recvfrom() with MSG_PEEK flag (no data consumed from TCP buffer)
```

### 11.3 mTLS (Mutual TLS) Configuration

```yaml
# mTLS at Gateway: verify client certificates
# Use case: B2B APIs, service-to-service, zero-trust

# Envoy Gateway: ClientTrafficPolicy
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: ClientTrafficPolicy
metadata:
  name: mtls-policy
  namespace: infra
spec:
  targetRef:
    group: gateway.networking.k8s.io
    kind: Gateway
    name: prod-gateway
    sectionName: https
  tls:
    clientValidation:
      caCertificateRefs:
        - kind: Secret
          name: client-ca-cert
          # CA that signed client certificates
      # optional: specific SANs required
    minVersion: "1.3"
    maxVersion: "1.3"
    ciphers:
      - TLS_AES_256_GCM_SHA384
      - TLS_CHACHA20_POLY1305_SHA256
    ecdhCurves:
      - X25519
    signatureAlgorithms:
      - RSA-PSS-RSAE-SHA256
      - ECDSA-SECP256R1-SHA256

# What happens in the TLS handshake with mTLS:
# Normal TLS:  Server sends cert → Client verifies
# mTLS:        Server sends cert → Client verifies
#              Server sends CertificateRequest → Client sends cert → Server verifies
#
# CertificateRequest extensions:
#   - certificate_authorities: list of acceptable CA DNs
#   - signature_algorithms
#
# After mTLS: Envoy extracts client cert info to headers:
#   x-forwarded-client-cert: By=spiffe://...;Hash=...;Subject="CN=client1"
#   (XFCC header - useful for downstream services to see client identity)
```

---

## 12. Implementations: Envoy / Cilium / Istio / NGINX / HAProxy / Traefik

### 12.1 Envoy Gateway

```
Envoy Gateway (gateway.envoyproxy.io):
  Status: GA (v1.0, 2024)
  Architecture: Controller + Envoy proxy deployment
  Data plane: Envoy proxy (C++ based, BoringSSL)
  
  Components:
    envoy-gateway (controller): watches k8s API, translates to xDS
    envoy-proxy (data plane):   DaemonSet or Deployment per Gateway
    
  Strengths:
    - Full xDS ecosystem (Envoy filters: Lua, WASM, ext_proc)
    - Best-in-class observability (stats, tracing)
    - Battle-tested at Google, Lyft, Uber scale
    - Supports all Gateway API resources + CRD extensions
  
  Weaknesses:
    - Memory: Envoy ~100-200 MB per proxy
    - Startup: slow (full xDS bootstrap)
    - Complexity: 1000+ config options
  
  Performance (typical):
    Throughput: 100K+ RPS per Envoy instance (single CPU core)
    Latency added: p50=0.5ms, p99=2ms (HTTP/1.1), p50=0.2ms, p99=1ms (HTTP/2)
    Memory: ~150 MB per instance at 10K connections
```

### 12.2 Feature Matrix Across Implementations

```
Feature                  EnvoyGW  Cilium  Istio  NGINX  HAProxy  Traefik
─────────────────────────────────────────────────────────────────────────
HTTPRoute (v1)           ✓        ✓       ✓      ✓      ✓        ✓
GRPCRoute (v1)           ✓        ✓       ✓      partial partial  ✓
TCPRoute                 ✓        ✓       ✓      ✓      ✓        ✓
TLSRoute                 ✓        ✓       ✓      ✓      ✓        ✓
UDPRoute                 ✓        ✓       ✗      ✗      ✗        ✗
BackendTLSPolicy         ✓        ✓       ✓      ✓      ✓        partial
ReferenceGrant           ✓        ✓       ✓      ✓      ✓        ✓
Traffic weighting        ✓        ✓       ✓      ✓      ✓        ✓
Header manipulation      ✓        ✓       ✓      ✓      ✓        ✓
URL rewrite              ✓        ✓       ✓      ✓      ✓        ✓
Request mirroring        ✓        ✓       ✓      ✓      partial  ✓
JWT Auth                 ✓        ✗       ✓      module ✗        ✓
Rate limiting            ✓        ✓       ✓      module module   ✓
mTLS                     ✓        ✓       ✓      ✓      ✓        ✓
WASM filters             ✓        ✗       ✓      ✗      ✗        ✗
ExtProc (ext_proc)       ✓        ✗       ✓      ✗      ✗        ✗
Multi-cluster            ✓        ✓       ✓      ✗      ✗        ✗
eBPF data plane          ✗        ✓       ✗      ✗      ✗        ✗
```

### 12.3 NGINX Gateway Fabric

```
NGINX Gateway Fabric (NGF):
  Chart: nginx-stable/nginx-gateway-fabric
  
  Architecture:
    nginxgateway (controller, Go): watches k8s, generates NGINX config
    nginx (data plane): NGINX Plus or OSS, config file based
    
  Config generation:
    HTTPRoute → nginx.conf virtual server blocks
    TLS → ssl_certificate directives
    Backend → upstream blocks with weight
    
  Performance characteristics:
    Event-driven: epoll (Linux)
    Worker processes: one per vCPU (--worker-processes auto)
    Worker connections: 4096 per worker (--worker-connections)
    Memory per worker: ~5-10 MB (much lighter than Envoy)
    
  nginx.conf excerpt (generated by NGF controller):
  
    upstream app-team_api-svc_8080 {
        zone app-team_api-svc_8080 512k;
        server 10.244.1.5:8080 weight=90;
        server 10.244.1.6:8080 weight=10;
        keepalive 32;         # upstream connection pool
        keepalive_requests 1000;
        keepalive_timeout 60s;
    }
    
    server {
        listen 443 ssl http2 reuseport;  # reuseport: kernel distributes to workers
        server_name api.example.com;
        ssl_certificate     /etc/nginx/certs/tls.crt;
        ssl_certificate_key /etc/nginx/certs/tls.key;
        ssl_protocols TLSv1.3 TLSv1.2;
        ssl_session_cache shared:SSL:10m;
        
        location /v2 {
            proxy_pass http://app-team_api-svc_8080;
            proxy_http_version 1.1;
            proxy_set_header Connection "";  # HTTP/1.1 keepalive
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }
    }
```

---

## 13. C Implementation — Raw Kernel Socket Gateway

A minimal but educational L4 TCP gateway in C showing the exact syscalls
and socket operations that production gateways build upon.

```c
// File: gateway_l4.c
// Minimal L4 TCP gateway: accepts on frontend port, proxies to backend
// Demonstrates: accept4, epoll, splice(2) (zero-copy), SO_REUSEPORT
// Build: gcc -O2 -Wall -o gateway_l4 gateway_l4.c
// Run:   ./gateway_l4 0.0.0.0 8080 127.0.0.1 8443

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <fcntl.h>
#include <signal.h>
#include <netdb.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/epoll.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>

#define MAX_EVENTS   1024
#define PIPE_BUF_SZ  (1024 * 1024)  // 1 MiB splice pipe
#define BACKLOG      1024

// Connection state for bidirectional proxy
typedef struct {
    int fd_client;     // client-side fd
    int fd_backend;    // backend-side fd
    int pipe_c2b[2];   // pipe for client→backend splice
    int pipe_b2c[2];   // pipe for backend→client splice
    int closed;
} conn_t;

// Create non-blocking socket with SO_REUSEPORT (kernel distributes across workers)
static int create_listener(const char *host, const char *port) {
    struct addrinfo hints = {0}, *res;
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;
    hints.ai_flags    = AI_PASSIVE;

    int r = getaddrinfo(host, port, &hints, &res);
    if (r != 0) { fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(r)); exit(1); }

    int fd = socket(res->ai_family, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (fd < 0) { perror("socket"); exit(1); }

    int one = 1;
    // SO_REUSEADDR: allow bind() immediately after crash (skip TIME_WAIT)
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    // SO_REUSEPORT: multiple sockets on same port → kernel load balances (RSS)
    // This allows multi-process/thread listeners without explicit accept queue sharing
    setsockopt(fd, SOL_SOCKET, SO_REUSEPORT, &one, sizeof(one));

    if (bind(fd, res->ai_addr, res->ai_addrlen) < 0) { perror("bind"); exit(1); }
    if (listen(fd, BACKLOG) < 0) { perror("listen"); exit(1); }

    freeaddrinfo(res);
    printf("[+] Listening on %s:%s (fd=%d)\n", host, port, fd);
    return fd;
}

// Connect to backend (non-blocking)
static int connect_backend(const char *host, const char *port) {
    struct addrinfo hints = {0}, *res;
    hints.ai_family   = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, port, &hints, &res) != 0) return -1;

    int fd = socket(res->ai_family, SOCK_STREAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (fd < 0) { freeaddrinfo(res); return -1; }

    // TCP performance tuning (would be kernel defaults otherwise)
    int one = 1;
    // TCP_NODELAY: disable Nagle, send immediately (reduces latency for HTTP)
    setsockopt(fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    // TCP_QUICKACK: send ACK immediately (reduces RTT)
    setsockopt(fd, IPPROTO_TCP, TCP_QUICKACK, &one, sizeof(one));

    // Non-blocking connect: returns EINPROGRESS
    int r = connect(fd, res->ai_addr, res->ai_addrlen);
    freeaddrinfo(res);
    if (r < 0 && errno != EINPROGRESS) { close(fd); return -1; }
    return fd;
}

// splice(2): zero-copy data transfer pipe→socket or socket→pipe
// Avoids kernel→userspace→kernel copies (vs read()+write())
// Data path: NIC DMA→kernel buf → pipe → NIC TX (no userspace touch)
static ssize_t do_splice(int fd_from, int fd_to_pipe_write,
                          int fd_from_pipe_read, int fd_to) {
    // Step 1: splice from socket to pipe (kernel buffers only)
    ssize_t n = splice(fd_from, NULL, fd_to_pipe_write, NULL,
                       PIPE_BUF_SZ, SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
    if (n <= 0) return n;

    // Step 2: splice from pipe to destination socket
    ssize_t sent = 0;
    while (sent < n) {
        ssize_t s = splice(fd_from_pipe_read, NULL, fd_to, NULL,
                           n - sent, SPLICE_F_MOVE | SPLICE_F_NONBLOCK);
        if (s < 0) {
            if (errno == EAGAIN) break;
            return -1;
        }
        sent += s;
    }
    return sent;
}

int main(int argc, char *argv[]) {
    if (argc != 5) {
        fprintf(stderr, "Usage: %s <bind-host> <bind-port> <backend-host> <backend-port>\n", argv[0]);
        return 1;
    }
    const char *bind_host    = argv[1];
    const char *bind_port    = argv[2];
    const char *backend_host = argv[3];
    const char *backend_port = argv[4];

    signal(SIGPIPE, SIG_IGN);  // ignore SIGPIPE from closed connections

    int listen_fd = create_listener(bind_host, bind_port);

    // epoll: scalable I/O multiplexing (O(1) per event, vs select O(N))
    int epfd = epoll_create1(EPOLL_CLOEXEC);
    if (epfd < 0) { perror("epoll_create1"); return 1; }

    struct epoll_event ev = {.events = EPOLLIN, .data.fd = listen_fd};
    epoll_ctl(epfd, EPOLL_CTL_ADD, listen_fd, &ev);

    struct epoll_event events[MAX_EVENTS];
    // conn_map indexed by fd (simplified; production would use hash map)
    conn_t *conns[65536] = {0};

    printf("[+] Gateway ready: %s:%s → %s:%s\n",
           bind_host, bind_port, backend_host, backend_port);

    for (;;) {
        // epoll_wait: block until events ready (no spinning)
        int nev = epoll_wait(epfd, events, MAX_EVENTS, -1);
        if (nev < 0) { if (errno == EINTR) continue; perror("epoll_wait"); break; }

        for (int i = 0; i < nev; i++) {
            int fd = events[i].data.fd;

            // ── New connection ───────────────────────────────────────────
            if (fd == listen_fd) {
                struct sockaddr_storage sa;
                socklen_t slen = sizeof(sa);
                // accept4: SOCK_NONBLOCK|SOCK_CLOEXEC in one syscall
                int cfd = accept4(listen_fd, (struct sockaddr*)&sa,
                                  &slen, SOCK_NONBLOCK | SOCK_CLOEXEC);
                if (cfd < 0) { continue; }

                int bfd = connect_backend(backend_host, backend_port);
                if (bfd < 0) { close(cfd); continue; }

                conn_t *c = calloc(1, sizeof(conn_t));
                c->fd_client  = cfd;
                c->fd_backend = bfd;

                // Create pipes for splice zero-copy
                if (pipe2(c->pipe_c2b, O_NONBLOCK) || pipe2(c->pipe_b2c, O_NONBLOCK)) {
                    perror("pipe2"); close(cfd); close(bfd); free(c); continue;
                }
                // Increase pipe capacity to reduce syscall frequency
                fcntl(c->pipe_c2b[0], F_SETPIPE_SZ, PIPE_BUF_SZ);
                fcntl(c->pipe_b2c[0], F_SETPIPE_SZ, PIPE_BUF_SZ);

                conns[cfd] = c;
                conns[bfd] = c;

                // Watch both fds for read events
                struct epoll_event ecl = {.events = EPOLLIN|EPOLLET, .data.fd = cfd};
                struct epoll_event ebk = {.events = EPOLLIN|EPOLLET, .data.fd = bfd};
                epoll_ctl(epfd, EPOLL_CTL_ADD, cfd, &ecl);
                epoll_ctl(epfd, EPOLL_CTL_ADD, bfd, &ebk);

                char ip[INET6_ADDRSTRLEN] = {0};
                if (sa.ss_family == AF_INET)
                    inet_ntop(AF_INET, &((struct sockaddr_in*)&sa)->sin_addr, ip, sizeof(ip));
                printf("[+] New conn: client_fd=%d backend_fd=%d src=%s\n", cfd, bfd, ip);
                continue;
            }

            // ── Proxy data ───────────────────────────────────────────────
            conn_t *c = conns[fd];
            if (!c || c->closed) continue;

            uint32_t ev_flags = events[i].events;

            if (ev_flags & (EPOLLHUP | EPOLLERR)) {
                goto close_conn;
            }

            if (ev_flags & EPOLLIN) {
                ssize_t n;
                if (fd == c->fd_client) {
                    // client → backend
                    n = do_splice(c->fd_client, c->pipe_c2b[1],
                                  c->pipe_c2b[0], c->fd_backend);
                } else {
                    // backend → client
                    n = do_splice(c->fd_backend, c->pipe_b2c[1],
                                  c->pipe_b2c[0], c->fd_client);
                }

                if (n == 0 || (n < 0 && errno != EAGAIN)) {
                    close_conn:
                    printf("[-] Closing conn: fd=%d\n", fd);
                    c->closed = 1;
                    epoll_ctl(epfd, EPOLL_CTL_DEL, c->fd_client, NULL);
                    epoll_ctl(epfd, EPOLL_CTL_DEL, c->fd_backend, NULL);
                    conns[c->fd_client] = NULL;
                    conns[c->fd_backend] = NULL;
                    close(c->pipe_c2b[0]); close(c->pipe_c2b[1]);
                    close(c->pipe_b2c[0]); close(c->pipe_b2c[1]);
                    close(c->fd_client);
                    close(c->fd_backend);
                    free(c);
                }
            }
        }
    }
    return 0;
}
```

### 13.1 HTTP/1.1 Parsing in C (L7 Gateway Header Inspection)

```c
// File: http_parse.c
// Minimal HTTP/1.1 request parser for Gateway-level header inspection
// Used to implement: host-based routing, path matching, header extraction
// Build: gcc -O2 -Wall -o http_parse http_parse.c

#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdlib.h>

#define MAX_HEADERS 64
#define MAX_METHOD  16
#define MAX_PATH    4096
#define MAX_HNAME   256
#define MAX_HVAL    8192

typedef struct {
    char name[MAX_HNAME];
    char value[MAX_HVAL];
} http_header_t;

typedef struct {
    char method[MAX_METHOD];    // GET, POST, PUT, etc.
    char path[MAX_PATH];        // /v1/users?id=123
    char version[16];           // HTTP/1.1
    http_header_t headers[MAX_HEADERS];
    int header_count;
    const char *body_start;     // pointer into original buffer
    size_t body_len;
    int complete;               // 1 if full headers parsed
} http_request_t;

// Returns bytes consumed, -1 on error, 0 if incomplete
// Gateway reads from socket into buf, calls parse_http_request
// Implements O(N) single-pass parsing
int parse_http_request(const char *buf, size_t len, http_request_t *req) {
    memset(req, 0, sizeof(*req));
    const char *p = buf;
    const char *end = buf + len;

    // ── Parse request line: METHOD SP path SP HTTP/version CRLF ──────────
    const char *method_end = memchr(p, ' ', end - p);
    if (!method_end) return 0;  // incomplete
    size_t method_len = method_end - p;
    if (method_len >= MAX_METHOD) return -1;
    memcpy(req->method, p, method_len);
    p = method_end + 1;

    const char *path_end = memchr(p, ' ', end - p);
    if (!path_end) return 0;
    size_t path_len = path_end - p;
    if (path_len >= MAX_PATH) return -1;
    memcpy(req->path, p, path_len);
    p = path_end + 1;

    const char *version_end = memmem(p, end - p, "\r\n", 2);
    if (!version_end) return 0;
    size_t ver_len = version_end - p;
    if (ver_len >= 16) return -1;
    memcpy(req->version, p, ver_len);
    p = version_end + 2;

    // ── Parse headers: Name: Value CRLF ... CRLF CRLF ───────────────────
    while (p < end && req->header_count < MAX_HEADERS) {
        // Empty line = end of headers
        if (p[0] == '\r' && p + 1 < end && p[1] == '\n') {
            p += 2;
            req->body_start = p;
            req->complete = 1;
            break;
        }

        // Header name (case-insensitive per RFC 7230)
        const char *name_end = memchr(p, ':', end - p);
        if (!name_end) return 0;
        size_t nlen = name_end - p;
        if (nlen >= MAX_HNAME) return -1;

        http_header_t *h = &req->headers[req->header_count++];
        for (size_t i = 0; i < nlen; i++)
            h->name[i] = tolower((unsigned char)p[i]);
        p = name_end + 1;

        // Skip optional whitespace after colon (RFC 7230 OWS)
        while (p < end && (*p == ' ' || *p == '\t')) p++;

        const char *val_end = memmem(p, end - p, "\r\n", 2);
        if (!val_end) return 0;
        size_t vlen = val_end - p;
        if (vlen >= MAX_HVAL) return -1;
        memcpy(h->value, p, vlen);
        p = val_end + 2;
    }

    return req->complete ? (int)(p - buf) : 0;
}

// Gateway routing decision: returns backend index or -1
int route_request(const http_request_t *req, const char **paths, int n_paths) {
    // 1. Extract Host header
    const char *host = NULL;
    for (int i = 0; i < req->header_count; i++) {
        if (strcmp(req->headers[i].name, "host") == 0) {
            host = req->headers[i].value;
            break;
        }
    }

    printf("  Method: %s\n  Path:   %s\n  Host:   %s\n",
           req->method, req->path, host ? host : "(none)");

    // 2. PathPrefix matching (longest match wins — same as Gateway API spec)
    int best_match = -1;
    size_t best_len = 0;
    for (int i = 0; i < n_paths; i++) {
        size_t plen = strlen(paths[i]);
        if (strncmp(req->path, paths[i], plen) == 0) {
            if (plen > best_len) {
                best_len = plen;
                best_match = i;
            }
        }
    }
    return best_match;
}

int main(void) {
    // Simulate what a Gateway receives from a client socket
    const char *raw_request =
        "GET /v2/users/123?format=json HTTP/1.1\r\n"
        "Host: api.example.com\r\n"
        "User-Agent: curl/7.88.1\r\n"
        "Accept: application/json\r\n"
        "X-API-Version: 2\r\n"
        "Authorization: Bearer eyJhbGciOiJSUzI1NiJ9...\r\n"
        "\r\n";

    http_request_t req;
    int consumed = parse_http_request(raw_request, strlen(raw_request), &req);

    if (consumed > 0 && req.complete) {
        printf("[+] Parsed HTTP request (%d bytes):\n", consumed);

        const char *backends[] = {"/v2", "/v1", "/"};
        int n_backends = 3;
        int backend = route_request(&req, backends, n_backends);
        if (backend >= 0)
            printf("  → Route to backend[%d] (prefix: %s)\n", backend, backends[backend]);
        else
            printf("  → No matching route (404)\n");

        printf("  Headers:\n");
        for (int i = 0; i < req.header_count; i++)
            printf("    %s: %s\n", req.headers[i].name, req.headers[i].value);
    } else {
        printf("[-] Parse failed or incomplete (consumed=%d)\n", consumed);
    }
    return 0;
}
```

---

## 14. Go Implementation — Gateway Controller + L7 Proxy

### 14.1 Gateway API Controller (Watches k8s, Programs Data Plane)

```go
// File: cmd/gateway-controller/main.go
// Minimal Gateway API controller demonstrating the reconcile loop.
// Uses controller-runtime (same as Envoy Gateway, Cilium, etc.)
// Build: go build ./cmd/gateway-controller/
// Test:  go test ./pkg/controller/...

package main

import (
	"context"
	"fmt"
	"os"

	corev1 "k8s.io/api/core/v1"
	"k8s.io/apimachinery/pkg/runtime"
	"k8s.io/apimachinery/pkg/types"
	ctrl "sigs.k8s.io/controller-runtime"
	"sigs.k8s.io/controller-runtime/pkg/client"
	"sigs.k8s.io/controller-runtime/pkg/log/zap"
	gatewayv1 "sigs.k8s.io/gateway-api/apis/v1"
)

// go.mod:
// module github.com/example/gateway-controller
//
// require (
//   sigs.k8s.io/controller-runtime v0.18.0
//   sigs.k8s.io/gateway-api v1.2.0
//   k8s.io/api v0.31.0
//   k8s.io/apimachinery v0.31.0
//   k8s.io/client-go v0.31.0
// )

// ─── Intermediate Representation ─────────────────────────────────────────────
// The IR is the internal in-memory representation of what the data plane
// should be configured to do. This decouples the k8s API types from the
// data plane config format (xDS, nginx.conf, BPF maps, etc.)

type RouteMatch struct {
	PathPrefix string
	Headers    map[string]string
	Method     string
}

type Backend struct {
	Host      string
	Port      int32
	Weight    int32
	Namespace string
	Name      string // Service name
}

type RouteRule struct {
	Matches  []RouteMatch
	Backends []Backend
}

type VirtualHost struct {
	Hostname string
	TLSSecretName string
	TLSNamespace  string
	Routes []RouteRule
}

type GatewayIR struct {
	Name      string
	Namespace string
	Listeners map[string][]VirtualHost // listenerName → virtual hosts
}

// ─── HTTPRoute Reconciler ─────────────────────────────────────────────────────

type HTTPRouteReconciler struct {
	client.Client
	Scheme       *runtime.Scheme
	DataPlane    DataPlaneClient // interface to push config to Envoy/NGINX/etc.
}

// DataPlaneClient: interface the controller uses to push config.
// Could be: xDS server, nginx config writer, BPF map updater, etc.
type DataPlaneClient interface {
	SyncGateway(ctx context.Context, ir *GatewayIR) error
}

func (r *HTTPRouteReconciler) Reconcile(ctx context.Context, req ctrl.Request) (ctrl.Result, error) {
	log := ctrl.LoggerFrom(ctx)
	log.Info("Reconciling HTTPRoute", "name", req.NamespacedName)

	// 1. Fetch the HTTPRoute
	var route gatewayv1.HTTPRoute
	if err := r.Get(ctx, req.NamespacedName, &route); err != nil {
		return ctrl.Result{}, client.IgnoreNotFound(err)
	}

	// 2. For each parentRef, find the Gateway and build IR
	for _, parentRef := range route.Spec.ParentRefs {
		gwNS := route.Namespace
		if parentRef.Namespace != nil {
			gwNS = string(*parentRef.Namespace)
		}

		var gw gatewayv1.Gateway
		gwKey := types.NamespacedName{Name: string(parentRef.Name), Namespace: gwNS}
		if err := r.Get(ctx, gwKey, &gw); err != nil {
			log.Error(err, "Gateway not found", "ref", gwKey)
			// Update route status: Accepted=False, reason=InvalidParentReference
			r.setRouteStatus(ctx, &route, parentRef, false, "InvalidParentReference",
				fmt.Sprintf("Gateway %s not found", gwKey))
			continue
		}

		// 3. Verify allowedRoutes (namespace, kind checks)
		if !r.isRouteAllowed(ctx, &gw, &route, parentRef) {
			r.setRouteStatus(ctx, &route, parentRef, false, "NotAllowedByParent",
				"Route not allowed by Gateway allowedRoutes configuration")
			continue
		}

		// 4. Build IR from route + gateway
		ir, err := r.buildIR(ctx, &gw, &route)
		if err != nil {
			log.Error(err, "Failed to build IR")
			r.setRouteStatus(ctx, &route, parentRef, false, "ResolvedRefs",
				fmt.Sprintf("Error resolving backends: %v", err))
			continue
		}

		// 5. Push IR to data plane
		if err := r.DataPlane.SyncGateway(ctx, ir); err != nil {
			log.Error(err, "Failed to sync data plane")
			r.setRouteStatus(ctx, &route, parentRef, false, "Programmed",
				fmt.Sprintf("Data plane sync failed: %v", err))
			continue
		}

		// 6. Update route status: Accepted=True, Programmed=True
		r.setRouteStatus(ctx, &route, parentRef, true, "Accepted",
			"Route accepted and programmed")

		log.Info("HTTPRoute reconciled successfully", "ir", ir.Name)
	}

	return ctrl.Result{}, nil
}

func (r *HTTPRouteReconciler) buildIR(
	ctx context.Context,
	gw *gatewayv1.Gateway,
	route *gatewayv1.HTTPRoute,
) (*GatewayIR, error) {

	ir := &GatewayIR{
		Name:      gw.Name,
		Namespace: gw.Namespace,
		Listeners: make(map[string][]VirtualHost),
	}

	for _, rule := range route.Spec.Rules {
		routeRule := RouteRule{}

		// Build match list
		for _, match := range rule.Matches {
			rm := RouteMatch{
				Headers: make(map[string]string),
			}
			if match.Path != nil && match.Path.Value != nil {
				rm.PathPrefix = *match.Path.Value
			}
			if match.Method != nil {
				rm.Method = string(*match.Method)
			}
			for _, h := range match.Headers {
				rm.Headers[string(h.Name)] = h.Value
			}
			routeRule.Matches = append(routeRule.Matches, rm)
		}

		// Resolve backends: Service → Pod IPs (via EndpointSlice)
		for _, ref := range rule.BackendRefs {
			svcNS := route.Namespace
			if ref.Namespace != nil {
				svcNS = string(*ref.Namespace)
				// Check ReferenceGrant
				if !r.checkReferenceGrant(ctx, route.Namespace, svcNS, string(ref.Name)) {
					return nil, fmt.Errorf("no ReferenceGrant for Service %s/%s", svcNS, ref.Name)
				}
			}

			// Resolve Service to get cluster-internal hostname
			var svc corev1.Service
			svcKey := types.NamespacedName{Name: string(ref.Name), Namespace: svcNS}
			if err := r.Get(ctx, svcKey, &svc); err != nil {
				return nil, fmt.Errorf("service %s not found: %w", svcKey, err)
			}

			weight := int32(1)
			if ref.Weight != nil {
				weight = *ref.Weight
			}

			routeRule.Backends = append(routeRule.Backends, Backend{
				// Use cluster-internal DNS (FQDN for cross-namespace)
				Host:      fmt.Sprintf("%s.%s.svc.cluster.local", svc.Name, svc.Namespace),
				Port:      int32(ref.Port),
				Weight:    weight,
				Namespace: svcNS,
				Name:      string(ref.Name),
			})
		}

		// Determine which listener (sectionName) this rule belongs to
		// and which hostnames to use
		listenerName := "default"
		for _, parentRef := range route.Spec.ParentRefs {
			if parentRef.SectionName != nil {
				listenerName = string(*parentRef.SectionName)
			}
		}

		hostnames := []string{"*"} // default: any hostname
		for _, h := range route.Spec.Hostnames {
			hostnames = append(hostnames[:0], string(h)) // use explicit hostnames
		}

		for _, hostname := range hostnames {
			vh := VirtualHost{Hostname: hostname}
			vh.Routes = append(vh.Routes, routeRule)
			ir.Listeners[listenerName] = append(ir.Listeners[listenerName], vh)
		}
	}

	return ir, nil
}

func (r *HTTPRouteReconciler) isRouteAllowed(
	ctx context.Context,
	gw *gatewayv1.Gateway,
	route *gatewayv1.HTTPRoute,
	parentRef gatewayv1.ParentReference,
) bool {
	for _, listener := range gw.Spec.Listeners {
		// Check sectionName matches
		if parentRef.SectionName != nil && string(*parentRef.SectionName) != string(listener.Name) {
			continue
		}
		ar := listener.AllowedRoutes
		if ar == nil {
			return true // no restriction
		}
		// Check namespace policy
		if ar.Namespaces != nil {
			switch *ar.Namespaces.From {
			case gatewayv1.NamespacesFromSame:
				if gw.Namespace != route.Namespace {
					return false
				}
			case gatewayv1.NamespacesFromAll:
				// OK
			case gatewayv1.NamespacesFromSelector:
				// Would need to fetch namespace and check labels
				// (simplified here)
			}
		}
		return true
	}
	return false
}

func (r *HTTPRouteReconciler) checkReferenceGrant(
	ctx context.Context, fromNS, toNS, toName string,
) bool {
	if fromNS == toNS {
		return true // same namespace: no grant needed
	}
	// List ReferenceGrants in the target namespace
	var grants gatewayv1.ReferenceGrantList
	if err := r.List(ctx, &grants, client.InNamespace(toNS)); err != nil {
		return false
	}
	for _, grant := range grants.Items {
		for _, from := range grant.Spec.From {
			if string(from.Group) == "gateway.networking.k8s.io" &&
				string(from.Kind) == "HTTPRoute" &&
				string(from.Namespace) == fromNS {
				for _, to := range grant.Spec.To {
					if string(to.Group) == "" && string(to.Kind) == "Service" {
						if to.Name == nil || string(*to.Name) == toName {
							return true
						}
					}
				}
			}
		}
	}
	return false
}

func (r *HTTPRouteReconciler) setRouteStatus(
	ctx context.Context,
	route *gatewayv1.HTTPRoute,
	parentRef gatewayv1.ParentReference,
	accepted bool,
	reason, message string,
) {
	// Build status condition
	condStatus := "False"
	if accepted {
		condStatus = "True"
	}

	// In real controllers, use apimachinery/pkg/api/meta SetStatusCondition
	// and patch with --subresource=status
	_ = condStatus
	_ = reason
	_ = message
	// r.Status().Patch(ctx, route, ...)
}

func (r *HTTPRouteReconciler) SetupWithManager(mgr ctrl.Manager) error {
	return ctrl.NewControllerManagedBy(mgr).
		For(&gatewayv1.HTTPRoute{}).
		// Also reconcile when referenced Gateway changes
		Watches(&gatewayv1.Gateway{}, r.enqueueForGateway()).
		// Reconcile when referenced Service changes (endpoint changes)
		Watches(&corev1.Service{}, r.enqueueForService()).
		Complete(r)
}

func (r *HTTPRouteReconciler) enqueueForGateway() handler.EventHandler {
	// Return event handler that enqueues all HTTPRoutes referencing this Gateway
	// (simplified: in production use handler.EnqueueRequestsFromMapFunc)
	return nil
}

func (r *HTTPRouteReconciler) enqueueForService() handler.EventHandler {
	return nil
}

func main() {
	ctrl.SetLogger(zap.New())

	scheme := runtime.NewScheme()
	_ = gatewayv1.Install(scheme)
	_ = corev1.AddToScheme(scheme)

	mgr, err := ctrl.NewManager(ctrl.GetConfigOrDie(), ctrl.Options{
		Scheme: scheme,
		// Metrics, health check, leader election
		MetricsBindAddress:      ":8080",
		HealthProbeBindAddress:  ":8081",
		LeaderElection:          true,
		LeaderElectionID:        "gateway-controller.example.com",
		LeaderElectionNamespace: "gateway-system",
	})
	if err != nil {
		fmt.Fprintf(os.Stderr, "unable to create manager: %v\n", err)
		os.Exit(1)
	}

	// Register reconciler
	if err := (&HTTPRouteReconciler{
		Client:    mgr.GetClient(),
		Scheme:    mgr.GetScheme(),
		DataPlane: &NoopDataPlane{}, // replace with real xDS server / nginx writer
	}).SetupWithManager(mgr); err != nil {
		fmt.Fprintf(os.Stderr, "unable to setup controller: %v\n", err)
		os.Exit(1)
	}

	if err := mgr.Start(ctrl.SetupSignalHandler()); err != nil {
		fmt.Fprintf(os.Stderr, "manager error: %v\n", err)
		os.Exit(1)
	}
}

type NoopDataPlane struct{}
func (n *NoopDataPlane) SyncGateway(ctx context.Context, ir *GatewayIR) error {
	fmt.Printf("[DataPlane] SyncGateway: %+v\n", ir)
	return nil
}
```

### 14.2 Go L7 Reverse Proxy (Production-grade)

```go
// File: cmd/l7proxy/main.go
// Production-grade L7 HTTP/1.1 + HTTP/2 reverse proxy in Go
// Implements: path routing, header manipulation, weighted backends, health checks
// Build: go build ./cmd/l7proxy/
// Run:   ./l7proxy -config config.yaml
// Bench: wrk -t4 -c100 -d30s http://localhost:8080/v2/users

package main

import (
	"context"
	"crypto/tls"
	"encoding/json"
	"flag"
	"fmt"
	"log/slog"
	"math/rand"
	"net"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"sort"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// ─── Config ──────────────────────────────────────────────────────────────────

type BackendConfig struct {
	URL    string `json:"url"`
	Weight int    `json:"weight"`
}

type RouteConfig struct {
	PathPrefix string          `json:"pathPrefix"`
	Backends   []BackendConfig `json:"backends"`
}

type ListenerConfig struct {
	Addr     string        `json:"addr"`
	TLSCert  string        `json:"tlsCert"`
	TLSKey   string        `json:"tlsKey"`
	Routes   []RouteConfig `json:"routes"`
}

// ─── Backend Health Tracking ──────────────────────────────────────────────────

type BackendHealth struct {
	mu        sync.RWMutex
	healthy   bool
	failures  int
	successes int
	lastCheck time.Time
}

func (h *BackendHealth) IsHealthy() bool {
	h.mu.RLock()
	defer h.mu.RUnlock()
	return h.healthy
}

func (h *BackendHealth) RecordResult(success bool) {
	h.mu.Lock()
	defer h.mu.Unlock()
	if success {
		h.successes++
		h.failures = 0
		if h.successes >= 2 {
			h.healthy = true
		}
	} else {
		h.failures++
		h.successes = 0
		if h.failures >= 3 {
			h.healthy = false
		}
	}
}

// ─── Weighted Backend Pool ────────────────────────────────────────────────────

type Backend struct {
	url        *url.URL
	weight     int
	health     *BackendHealth
	proxy      *httputil.ReverseProxy
	reqCount   atomic.Int64
	errCount   atomic.Int64
}

type BackendPool struct {
	backends []*Backend
	total    int // total weight of healthy backends
}

// Select backend using weighted random (matches Gateway API weight semantics)
func (p *BackendPool) Select() *Backend {
	// Build list of healthy backends
	var healthy []*Backend
	totalWeight := 0
	for _, b := range p.backends {
		if b.health.IsHealthy() {
			healthy = append(healthy, b)
			totalWeight += b.weight
		}
	}

	if len(healthy) == 0 {
		// Failopen: use all backends if all are unhealthy
		healthy = p.backends
		for _, b := range healthy {
			totalWeight += b.weight
		}
	}

	// Weighted random selection (O(N) — for large pools use weighted ring)
	r := rand.Intn(totalWeight)
	cumulative := 0
	for _, b := range healthy {
		cumulative += b.weight
		if r < cumulative {
			return b
		}
	}
	return healthy[len(healthy)-1]
}

// ─── Route Matcher ────────────────────────────────────────────────────────────

type Route struct {
	pathPrefix string
	pool       *BackendPool
}

type Router struct {
	routes []Route // sorted by pathPrefix length descending (longest match first)
}

func NewRouter(configs []RouteConfig) (*Router, error) {
	router := &Router{}

	for _, rc := range configs {
		pool := &BackendPool{}
		for _, bc := range rc.Backends {
			u, err := url.Parse(bc.URL)
			if err != nil {
				return nil, fmt.Errorf("invalid backend URL %s: %w", bc.URL, err)
			}

			health := &BackendHealth{healthy: true}

			// Custom transport: tuned for production
			transport := &http.Transport{
				// Connection pool settings
				MaxIdleConns:          1000,
				MaxIdleConnsPerHost:   100,
				MaxConnsPerHost:       0, // unlimited
				IdleConnTimeout:       90 * time.Second,

				// Timeouts
				DialContext: (&net.Dialer{
					Timeout:   5 * time.Second,
					KeepAlive: 30 * time.Second,
				}).DialContext,
				TLSHandshakeTimeout:   10 * time.Second,
				ResponseHeaderTimeout: 30 * time.Second,
				ExpectContinueTimeout: 1 * time.Second,

				// HTTP/2 to backend (if BackendTLSPolicy configured)
				ForceAttemptHTTP2: true,
				TLSClientConfig: &tls.Config{
					// In production: load CA cert from BackendTLSPolicy
					InsecureSkipVerify: false,
					MinVersion:         tls.VersionTLS13,
				},

				// Buffer sizes (match kernel SO_SNDBUF/SO_RCVBUF)
				WriteBufferSize: 64 * 1024, // 64 KiB
				ReadBufferSize:  64 * 1024,
			}

			proxy := &httputil.ReverseProxy{
				Transport: transport,
				// Director: modify request before forwarding
				Director: func(req *http.Request) {
					req.URL.Scheme = u.Scheme
					req.URL.Host   = u.Host
					// Preserve original host or set backend host
					if req.Header.Get("X-Forwarded-Host") == "" {
						req.Header.Set("X-Forwarded-Host", req.Host)
					}
					req.Header.Set("X-Forwarded-For", req.RemoteAddr)
					req.Header.Set("X-Real-IP",        req.RemoteAddr)
					// Remove internal headers
					req.Header.Del("X-Internal-Token")
					req.Header.Del("Authorization") // strip before logging
				},
				// ModifyResponse: modify response before returning to client
				ModifyResponse: func(resp *http.Response) error {
					resp.Header.Set("Strict-Transport-Security",
						"max-age=31536000; includeSubDomains; preload")
					resp.Header.Del("Server")      // don't reveal backend software
					resp.Header.Del("X-Powered-By")
					health.RecordResult(resp.StatusCode < 500)
					return nil
				},
				ErrorHandler: func(w http.ResponseWriter, r *http.Request, err error) {
					slog.Error("proxy error",
						"backend", u.Host, "path", r.URL.Path, "error", err)
					health.RecordResult(false)
					http.Error(w, "Bad Gateway", http.StatusBadGateway)
				},
				// BufferPool: reuse buffers (reduces GC pressure)
				BufferPool: newBufferPool(32 * 1024),
			}

			weight := bc.Weight
			if weight == 0 {
				weight = 1
			}

			pool.backends = append(pool.backends, &Backend{
				url:    u,
				weight: weight,
				health: health,
				proxy:  proxy,
			})
		}

		router.routes = append(router.routes, Route{
			pathPrefix: rc.PathPrefix,
			pool:       pool,
		})
	}

	// Sort by path length descending: longest prefix wins (Gateway API spec)
	sort.Slice(router.routes, func(i, j int) bool {
		return len(router.routes[i].pathPrefix) > len(router.routes[j].pathPrefix)
	})

	return router, nil
}

// Match: O(N) longest prefix match — for thousands of routes use a trie
func (r *Router) Match(path string) *BackendPool {
	for _, route := range r.routes {
		if strings.HasPrefix(path, route.pathPrefix) {
			return route.pool
		}
	}
	return nil
}

// ─── HTTP Handler ─────────────────────────────────────────────────────────────

type GatewayHandler struct {
	router *Router
}

func (h *GatewayHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	start := time.Now()

	// 1. Route matching
	pool := h.router.Match(r.URL.Path)
	if pool == nil {
		http.Error(w, "No matching route", http.StatusNotFound)
		return
	}

	// 2. Backend selection (weighted random)
	backend := pool.Select()
	backend.reqCount.Add(1)

	// 3. Add tracing headers
	if r.Header.Get("X-Request-Id") == "" {
		r.Header.Set("X-Request-Id", fmt.Sprintf("%d", time.Now().UnixNano()))
	}

	// 4. Proxy request
	rw := &responseWriter{ResponseWriter: w}
	backend.proxy.ServeHTTP(rw, r)

	// 5. Observe
	dur := time.Since(start)
	slog.Info("request",
		"method", r.Method,
		"path", r.URL.Path,
		"status", rw.status,
		"duration_ms", dur.Milliseconds(),
		"backend", backend.url.Host,
	)

	if rw.status >= 500 {
		backend.errCount.Add(1)
	}
}

// responseWriter captures status code for logging
type responseWriter struct {
	http.ResponseWriter
	status int
}

func (rw *responseWriter) WriteHeader(code int) {
	rw.status = code
	rw.ResponseWriter.WriteHeader(code)
}

// ─── Buffer Pool ──────────────────────────────────────────────────────────────

type bufferPool struct {
	pool sync.Pool
}

func newBufferPool(size int) httputil.BufferPool {
	return &bufferPool{pool: sync.Pool{New: func() any {
		buf := make([]byte, size)
		return &buf
	}}}
}

func (b *bufferPool) Get() []byte {
	return *b.pool.Get().(*[]byte)
}

func (b *bufferPool) Put(buf []byte) {
	b.pool.Put(&buf)
}

// ─── Health Check Loop ────────────────────────────────────────────────────────

func startHealthChecks(router *Router, interval time.Duration) {
	go func() {
		ticker := time.NewTicker(interval)
		defer ticker.Stop()
		client := &http.Client{Timeout: 3 * time.Second}

		for range ticker.C {
			for _, route := range router.routes {
				for _, backend := range route.pool.backends {
					b := backend
					go func() {
						healthURL := b.url.String() + "/healthz"
						resp, err := client.Get(healthURL)
						if err != nil {
							b.health.RecordResult(false)
							return
						}
						resp.Body.Close()
						b.health.RecordResult(resp.StatusCode < 500)
					}()
				}
			}
		}
	}()
}

// ─── Main ─────────────────────────────────────────────────────────────────────

func main() {
	configFile := flag.String("config", "config.json", "Config file")
	flag.Parse()

	data, err := os.ReadFile(*configFile)
	if err != nil {
		slog.Error("read config", "error", err)
		os.Exit(1)
	}

	var listeners []ListenerConfig
	if err := json.Unmarshal(data, &listeners); err != nil {
		slog.Error("parse config", "error", err)
		os.Exit(1)
	}

	var wg sync.WaitGroup
	for _, l := range listeners {
		lc := l
		router, err := NewRouter(lc.Routes)
		if err != nil {
			slog.Error("build router", "error", err)
			os.Exit(1)
		}

		startHealthChecks(router, 5*time.Second)

		handler := &GatewayHandler{router: router}

		srv := &http.Server{
			Addr:    lc.Addr,
			Handler: handler,
			// HTTP/2 enabled by default when TLS is configured
			// Tune server-level timeouts
			ReadTimeout:       30 * time.Second,
			ReadHeaderTimeout: 5 * time.Second,
			WriteTimeout:      60 * time.Second,
			IdleTimeout:       120 * time.Second,
			// TLS config
			TLSConfig: &tls.Config{
				MinVersion:               tls.VersionTLS13,
				PreferServerCipherSuites: true,
				CurvePreferences:         []tls.CurveID{tls.X25519, tls.CurveP256},
				CipherSuites: []uint16{
					tls.TLS_AES_256_GCM_SHA384,
					tls.TLS_CHACHA20_POLY1305_SHA256,
					tls.TLS_AES_128_GCM_SHA256,
				},
			},
		}

		wg.Add(1)
		go func() {
			defer wg.Done()
			slog.Info("starting listener", "addr", lc.Addr, "tls", lc.TLSCert != "")
			var err error
			if lc.TLSCert != "" {
				err = srv.ListenAndServeTLS(lc.TLSCert, lc.TLSKey)
			} else {
				err = srv.ListenAndServe()
			}
			if err != nil && err != http.ErrServerClosed {
				slog.Error("server error", "error", err)
			}
		}()
	}

	// Graceful shutdown on signal
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	_ = ctx
	wg.Wait()
}

// ─── Example config.json ─────────────────────────────────────────────────────
/*
[{
  "addr": ":8443",
  "tlsCert": "/etc/tls/tls.crt",
  "tlsKey": "/etc/tls/tls.key",
  "routes": [
    {"pathPrefix": "/v2", "backends": [
      {"url": "http://api-svc.app-team.svc.cluster.local:8080", "weight": 90},
      {"url": "http://api-svc-canary.app-team.svc.cluster.local:8080", "weight": 10}
    ]},
    {"pathPrefix": "/", "backends": [
      {"url": "http://default-svc.app-team.svc.cluster.local:8080", "weight": 100}
    ]}
  ]
}]
*/
```

---

## 15. Rust Implementation — Async TLS-aware Gateway Proxy

```rust
// File: src/main.rs
// Async L7 Gateway proxy in Rust using tokio + hyper (same stack as Linkerd)
// Features: SNI routing, TLS termination (rustls), weighted LB, health checks
//
// Cargo.toml:
// [dependencies]
// tokio        = { version = "1", features = ["full"] }
// hyper        = { version = "1", features = ["full"] }
// hyper-util   = { version = "0.1", features = ["full"] }
// http-body-util = "0.1"
// rustls       = "0.23"
// rustls-pemfile = "2"
// tokio-rustls = "0.26"
// tower        = { version = "0.4", features = ["full"] }
// tracing      = "0.1"
// tracing-subscriber = "0.3"
// rand         = "0.8"
// serde        = { version = "1", features = ["derive"] }
// serde_json   = "1"
//
// Build: cargo build --release
// Run:   RUST_LOG=info ./target/release/gateway-rs

use std::{
    collections::HashMap,
    net::SocketAddr,
    sync::{
        atomic::{AtomicUsize, Ordering},
        Arc,
    },
    time::Duration,
};

use http_body_util::{BodyExt, Full};
use hyper::{
    body::{Bytes, Incoming},
    header::{HeaderValue, HOST},
    Request, Response, StatusCode,
};
use hyper_util::{
    client::legacy::{connect::HttpConnector, Client},
    rt::TokioExecutor,
};
use rand::Rng;
use rustls::ServerConfig;
use tokio::{
    net::TcpListener,
    sync::RwLock,
};
use tokio_rustls::TlsAcceptor;
use tracing::{error, info, warn};

// ─── Types ────────────────────────────────────────────────────────────────────

#[derive(Clone, Debug)]
struct Backend {
    addr: String,    // "http://10.244.1.5:8080"
    weight: u32,
}

#[derive(Clone, Debug)]
struct RouteRule {
    path_prefix: String,
    backends: Vec<Backend>,
}

/// Shared gateway state, updated by control loop (watches k8s or config file)
#[derive(Clone, Debug)]
struct GatewayState {
    routes: Vec<RouteRule>,
}

type SharedState = Arc<RwLock<GatewayState>>;

// ─── Weighted Backend Selection ───────────────────────────────────────────────

fn select_backend(backends: &[Backend]) -> Option<&Backend> {
    if backends.is_empty() {
        return None;
    }
    let total: u32 = backends.iter().map(|b| b.weight).sum();
    if total == 0 {
        return backends.first();
    }
    let mut rng = rand::thread_rng();
    let mut r = rng.gen_range(0..total);
    for backend in backends {
        if r < backend.weight {
            return Some(backend);
        }
        r -= backend.weight;
    }
    backends.last()
}

// ─── Route Matching (longest prefix) ─────────────────────────────────────────

fn find_backend_for_path<'a>(
    routes: &'a [RouteRule],
    path: &str,
) -> Option<&'a [Backend]> {
    // Routes should be pre-sorted by prefix length descending
    routes
        .iter()
        .find(|r| path.starts_with(&r.path_prefix))
        .map(|r| r.backends.as_slice())
}

// ─── Request Handler ──────────────────────────────────────────────────────────

struct GatewayService {
    state:  SharedState,
    client: Client<HttpConnector, Incoming>,
}

impl GatewayService {
    async fn handle(
        &self,
        mut req: Request<Incoming>,
    ) -> Result<Response<Full<Bytes>>, hyper::Error> {
        let path = req.uri().path().to_string();
        let method = req.method().clone();

        // Read current routing state (RwLock read → no write contention)
        let state = self.state.read().await;

        let backends = match find_backend_for_path(&state.routes, &path) {
            Some(b) => b,
            None => {
                warn!(path = %path, "no matching route");
                return Ok(Response::builder()
                    .status(StatusCode::NOT_FOUND)
                    .body(Full::new(Bytes::from("No matching route\n")))
                    .unwrap());
            }
        };

        let backend = match select_backend(backends) {
            Some(b) => b.clone(),
            None => {
                error!("no healthy backend for path {}", path);
                return Ok(Response::builder()
                    .status(StatusCode::SERVICE_UNAVAILABLE)
                    .body(Full::new(Bytes::from("No healthy backends\n")))
                    .unwrap());
            }
        };

        drop(state); // release read lock before await

        // Rewrite URI to point to backend
        let backend_uri = format!("{}{}", backend.addr, req.uri().path_and_query()
            .map(|pq| pq.as_str()).unwrap_or("/"));

        *req.uri_mut() = backend_uri.parse().unwrap();

        // Set forwarding headers
        let original_host = req.headers()
            .get(HOST)
            .and_then(|v| v.to_str().ok())
            .unwrap_or("")
            .to_string();

        req.headers_mut().insert(
            "x-forwarded-host",
            HeaderValue::from_str(&original_host).unwrap_or(HeaderValue::from_static("")),
        );
        req.headers_mut().remove("x-internal-token");

        info!(
            method = %method,
            path = %path,
            backend = %backend.addr,
            "proxying request"
        );

        // Forward to backend using hyper client
        // hyper client handles: connection pooling, HTTP/2, keep-alive
        match self.client.request(req).await {
            Ok(resp) => {
                let (parts, body) = resp.into_parts();
                let bytes = body.collect().await?.to_bytes();
                let mut response = Response::from_parts(parts, Full::new(bytes));

                // Inject security headers
                response.headers_mut().insert(
                    "strict-transport-security",
                    HeaderValue::from_static("max-age=31536000; includeSubDomains; preload"),
                );
                response.headers_mut().remove("server");
                response.headers_mut().remove("x-powered-by");

                Ok(response)
            }
            Err(e) => {
                error!(error = %e, backend = %backend.addr, "backend error");
                Ok(Response::builder()
                    .status(StatusCode::BAD_GATEWAY)
                    .body(Full::new(Bytes::from("Bad Gateway\n")))
                    .unwrap())
            }
        }
    }
}

// ─── TLS Setup (rustls — pure Rust, no OpenSSL) ───────────────────────────────

fn build_tls_acceptor(cert_path: &str, key_path: &str) -> anyhow::Result<TlsAcceptor> {
    use rustls_pemfile::{certs, private_key};
    use std::fs::File;
    use std::io::BufReader;

    let cert_file = File::open(cert_path)?;
    let key_file  = File::open(key_path)?;

    let certs: Vec<_> = certs(&mut BufReader::new(cert_file))
        .collect::<Result<Vec<_>, _>>()?;

    let key = private_key(&mut BufReader::new(key_file))?
        .ok_or_else(|| anyhow::anyhow!("no private key found"))?;

    let config = ServerConfig::builder()
        // TLS 1.3 only (no TLS 1.2 — for maximum security)
        // In prod: allow TLS 1.2 for compatibility, enforce cipher suites
        .with_no_client_auth()      // no mTLS (add with_client_cert_verifier for mTLS)
        .with_single_cert(certs, key)?;

    Ok(TlsAcceptor::from(Arc::new(config)))
}

// ─── Listener ─────────────────────────────────────────────────────────────────

async fn run_listener(
    addr: SocketAddr,
    state: SharedState,
    tls_acceptor: Option<TlsAcceptor>,
) -> anyhow::Result<()> {
    let listener = TcpListener::bind(addr).await?;
    info!(addr = %addr, tls = tls_acceptor.is_some(), "gateway listening");

    // HTTP client for forwarding (shared across all requests on this listener)
    let mut connector = HttpConnector::new();
    connector.set_keepalive(Some(Duration::from_secs(90)));
    connector.set_connect_timeout(Some(Duration::from_secs(5)));
    connector.set_nodelay(true);

    let client: Client<HttpConnector, Incoming> = Client::builder(TokioExecutor::new())
        .pool_idle_timeout(Duration::from_secs(90))
        .pool_max_idle_per_host(100)
        .build(connector);

    let client = Arc::new(client);

    loop {
        let (stream, remote_addr) = listener.accept().await?;
        let state   = state.clone();
        let client  = client.clone();
        let acceptor = tls_acceptor.clone();

        tokio::spawn(async move {
            let service = GatewayService {
                state,
                client: (*client).clone(),
            };

            let result = if let Some(acceptor) = acceptor {
                // TLS accept: TLS handshake happens here
                // rustls runs in async context (no blocking!)
                match acceptor.accept(stream).await {
                    Ok(tls_stream) => {
                        hyper_util::server::conn::auto::Builder::new(TokioExecutor::new())
                            .serve_connection(
                                tls_stream,
                                hyper::service::service_fn(move |req| {
                                    let svc = GatewayService {
                                        state: service.state.clone(),
                                        client: service.client.clone(),
                                    };
                                    async move { svc.handle(req).await }
                                }),
                            )
                            .await
                    }
                    Err(e) => {
                        warn!(remote = %remote_addr, error = %e, "TLS handshake failed");
                        return;
                    }
                }
            } else {
                hyper_util::server::conn::auto::Builder::new(TokioExecutor::new())
                    .serve_connection(
                        stream,
                        hyper::service::service_fn(move |req| {
                            let svc = GatewayService {
                                state: service.state.clone(),
                                client: service.client.clone(),
                            };
                            async move { svc.handle(req).await }
                        }),
                    )
                    .await
            };

            if let Err(e) = result {
                warn!(remote = %remote_addr, error = %e, "connection error");
            }
        });
    }
}

// ─── Main ─────────────────────────────────────────────────────────────────────

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt::init();

    // Example routing config (in production: loaded from k8s Gateway API objects)
    let state = Arc::new(RwLock::new(GatewayState {
        routes: vec![
            RouteRule {
                path_prefix: "/v2".to_string(),
                backends: vec![
                    Backend { addr: "http://127.0.0.1:9001".to_string(), weight: 90 },
                    Backend { addr: "http://127.0.0.1:9002".to_string(), weight: 10 },
                ],
            },
            RouteRule {
                path_prefix: "/".to_string(),
                backends: vec![
                    Backend { addr: "http://127.0.0.1:9000".to_string(), weight: 100 },
                ],
            },
        ],
    }));

    // HTTP listener (port 8080)
    let state_http = state.clone();
    tokio::spawn(async move {
        if let Err(e) = run_listener(
            "0.0.0.0:8080".parse().unwrap(),
            state_http,
            None,
        ).await {
            error!("HTTP listener error: {}", e);
        }
    });

    // HTTPS listener (port 8443) — only if certs exist
    let cert = std::env::var("TLS_CERT").unwrap_or_default();
    let key  = std::env::var("TLS_KEY").unwrap_or_default();
    if !cert.is_empty() && !key.is_empty() {
        let acceptor = build_tls_acceptor(&cert, &key)?;
        tokio::spawn(async move {
            if let Err(e) = run_listener(
                "0.0.0.0:8443".parse().unwrap(),
                state,
                Some(acceptor),
            ).await {
                error!("HTTPS listener error: {}", e);
            }
        });
    }

    // Graceful shutdown (SIGTERM / SIGINT)
    tokio::signal::ctrl_c().await?;
    info!("shutting down");
    Ok(())
}

// ─── Tests ────────────────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_path_matching_longest_prefix_wins() {
        let routes = vec![
            RouteRule { path_prefix: "/".to_string(), backends: vec![
                Backend { addr: "http://default:80".to_string(), weight: 1 }
            ]},
            RouteRule { path_prefix: "/v2".to_string(), backends: vec![
                Backend { addr: "http://v2:80".to_string(), weight: 1 }
            ]},
            RouteRule { path_prefix: "/v2/users".to_string(), backends: vec![
                Backend { addr: "http://users:80".to_string(), weight: 1 }
            ]},
        ];

        // Sort by prefix length desc (as production code would)
        let mut sorted = routes.clone();
        sorted.sort_by(|a, b| b.path_prefix.len().cmp(&a.path_prefix.len()));

        assert_eq!(
            find_backend_for_path(&sorted, "/v2/users/123").unwrap()[0].addr,
            "http://users:80"
        );
        assert_eq!(
            find_backend_for_path(&sorted, "/v2/products").unwrap()[0].addr,
            "http://v2:80"
        );
        assert_eq!(
            find_backend_for_path(&sorted, "/health").unwrap()[0].addr,
            "http://default:80"
        );
    }

    #[test]
    fn test_weighted_selection_distribution() {
        let backends = vec![
            Backend { addr: "http://a:80".to_string(), weight: 90 },
            Backend { addr: "http://b:80".to_string(), weight: 10 },
        ];

        let n = 10000;
        let mut count_a = 0;
        for _ in 0..n {
            if let Some(b) = select_backend(&backends) {
                if b.addr.contains(":a:") || b.addr == "http://a:80" {
                    count_a += 1;
                }
            }
        }
        let ratio = count_a as f64 / n as f64;
        // Expect ~90% to backend a (allow ±5% for randomness)
        assert!(ratio > 0.85 && ratio < 0.95,
            "Expected ~90% to backend A, got {}%", ratio * 100.0);
    }

    #[test]
    fn test_no_backend_returns_none() {
        let backends: Vec<Backend> = vec![];
        assert!(select_backend(&backends).is_none());
    }
}
```

---

## 16. Threat Model & Security

### 16.1 STRIDE Threat Model

```
┌────────────────────────────────────────────────────────────────────────────────────┐
│              GATEWAY API THREAT MODEL (STRIDE)                                      │
├────────────────┬───────────────────────────────────────────────────────────────────┤
│ Threat Type    │ Attack Vector & Mitigation                                         │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ Spoofing       │ Rogue GatewayClass controller spoofing legitimate controller       │
│                │ Attack: attacker deploys controller claiming same controllerName   │
│                │ Effect: attacker programs their Gateway with malicious config      │
│                │ Mitigation:                                                        │
│                │  - RBAC: only platform team can create GatewayClass               │
│                │  - Audit log: watch GatewayClass create/update events             │
│                │  - controller leader election (only one active controller)        │
│                │                                                                   │
│                │ Client cert spoofing (mTLS)                                       │
│                │ Mitigation: cert pinning, short-lived certs, SPIFFE/SVID          │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ Tampering      │ HTTPRoute injection: attacker creates route to steal traffic       │
│                │ Attack: malicious dev in ns-A creates route matching prod hostname │
│                │ Effect: traffic hijacked to attacker's pod                        │
│                │ Mitigation:                                                        │
│                │  - allowedRoutes.namespaces: restrict which namespaces can attach │
│                │  - hostname uniqueness: controller rejects duplicate host+path    │
│                │  - RBAC: limit who can create HTTPRoute in sensitive namespaces   │
│                │  - Admission controller (OPA/Kyverno): prevent route conflicts   │
│                │                                                                   │
│                │ Secret tampering: attacker reads TLS private key                  │
│                │ Mitigation:                                                        │
│                │  - ReferenceGrant: only specific Gateways can access Secret       │
│                │  - RBAC on Secrets: only gateway SA has get/watch on tls Secrets  │
│                │  - Sealed Secrets / external-secrets-operator (Vault, ASM)       │
│                │  - Rotate: cert-manager auto-rotation, short-lived certs (1 day) │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ Repudiation    │ No audit trail for route changes                                  │
│                │ Mitigation:                                                        │
│                │  - K8s audit log: record all writes to gateway.networking.k8s.io │
│                │  - GitOps: all routes in Git (ArgoCD/Flux), requires PR review   │
│                │  - Falco: alert on direct kubectl edits to routes in prod         │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ Info Disclosure│ Headers exposing internal info (Server, X-Powered-By)            │
│                │ Mitigation: ResponseHeaderModifier to strip internal headers      │
│                │                                                                   │
│                │ TLS version/cipher downgrade                                      │
│                │ Mitigation: enforce TLS 1.3 minimum, disable weak ciphers        │
│                │                                                                   │
│                │ Request smuggling (HTTP/1.1 TE:chunked vs Content-Length)         │
│                │ Mitigation: use HTTP/2 to backend (eliminates smuggling), or     │
│                │  Envoy's normalize_path, reject_unsupported_upgrade option        │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ DoS            │ Slowloris: client opens many slow connections                     │
│                │ Mitigation: RequestHeaderTimeout, client_header_timeout, rate    │
│                │  limit on new connections at LB level (NLB SYN cookies)          │
│                │                                                                   │
│                │ Large bodies: 10 GB request exhausts proxy memory                │
│                │ Mitigation: max_request_bytes in Envoy, client_max_body_size in │
│                │  NGINX, BackendTrafficPolicy.rateLimit                           │
│                │                                                                   │
│                │ Route explosion: attacker creates millions of HTTPRoute objects  │
│                │ Mitigation: ResourceQuota on HTTPRoute count per namespace       │
│                │  example: kubectl create quota routes --hard=count/httproutes.gateway.networking.k8s.io=100 │
├────────────────┼───────────────────────────────────────────────────────────────────┤
│ Elevation      │ Escape from route sandbox via backendRef to host network pod      │
│                │ Attack: HTTPRoute points to svc that runs privileged pod          │
│                │ Mitigation:                                                        │
│                │  - NetworkPolicy: deny unexpected pod-to-pod traffic             │
│                │  - OPA: deny HTTPRoute pointing to non-production namespaces      │
│                │  - Audit: all backendRefs that cross namespace boundaries         │
│                │                                                                   │
│                │ SSRF via URLRewrite to internal metadata endpoint                 │
│                │ (169.254.169.254 = AWS IMDS, 169.254.170.2 = ECS creds)         │
│                │ Mitigation:                                                        │
│                │  - Admission webhook: deny URLRewrite/RequestRedirect to IMDS IP │
│                │  - IMDSv2 (token-based, harder to SSRF)                          │
│                │  - VPC firewall: block 169.254.169.254 from pod CIDR             │
└────────────────┴───────────────────────────────────────────────────────────────────┘
```

### 16.2 Zero-Trust Gateway Design

```yaml
# Zero-Trust: every request authenticated + authorized, no implicit trust

# 1. External traffic: JWT validation at gateway
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: SecurityPolicy
metadata:
  name: external-jwt
spec:
  targetRef:
    kind: HTTPRoute
    name: api-route
  jwt:
    providers:
      - name: corporate-idp
        issuer: "https://idp.corp.example.com"
        audiences: ["api.example.com"]
        remoteJWKS:
          uri: "https://idp.corp.example.com/.well-known/jwks.json"
          cacheDuration: 5m
        extractFrom:
          - headers:
              - name: authorization
                valuePrefix: "Bearer "

---
# 2. Service-to-service: mTLS with SPIFFE (Istio/cert-manager/SPIRE)
# Every pod gets a SPIFFE SVID cert:
#   URI SAN: spiffe://cluster.local/ns/app-team/sa/api-service
# Gateway verifies SPIFFE URI, not just "any cert from this CA"

# Envoy Gateway extension policy for SPIFFE validation:
apiVersion: gateway.envoyproxy.io/v1alpha1
kind: ClientTrafficPolicy
spec:
  tls:
    clientValidation:
      caCertificateRefs:
        - name: spiffe-ca-bundle
      # Implementation-specific: verify URI SAN matches expected SPIFFE ID
      spiffeValidation:
        trustDomain: "cluster.local"

---
# 3. NetworkPolicy: deny all except what's explicitly allowed
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gateway-network-policy
  namespace: infra
spec:
  podSelector:
    matchLabels:
      app: envoy-gateway
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - ipBlock:
            cidr: 0.0.0.0/0    # internet (LB forwards here)
      ports:
        - port: 443
        - port: 80
  egress:
    - to:
        - namespaceSelector: {}  # any namespace (for backend routing)
      ports:
        - port: 8080
        - port: 8443
        - port: 50051
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: kube-system
      ports:
        - port: 53   # CoreDNS
    - to:
        - namespaceSelector:
            matchLabels:
              kubernetes.io/metadata.name: cert-manager
      ports:
        - port: 443  # SDS / JWKS fetch
```

### 16.3 Supply Chain Security

```bash
# Verify Envoy Gateway container image
# All sig-network Gateway API implementations should sign with cosign

# Verify Envoy Gateway image signature (Sigstore/cosign)
cosign verify \
  --certificate-identity-regexp="https://github.com/envoyproxy/gateway" \
  --certificate-oidc-issuer="https://token.actions.githubusercontent.com" \
  docker.io/envoyproxy/gateway:v1.2.0

# Verify Gateway API CRD manifests
# (SHA256 checksums in release notes)
curl -L https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml \
  | sha256sum
# Compare with: https://github.com/kubernetes-sigs/gateway-api/releases/tag/v1.2.0

# SBOM: check for known CVEs in gateway implementation
syft docker.io/envoyproxy/gateway:v1.2.0 -o spdx-json > envoy-gateway-sbom.json
grype sbom:envoy-gateway-sbom.json
```

---

## 17. Observability: Metrics, Tracing, Logs

### 17.1 Key Metrics

```
Gateway API Observability Stack:

METRICS (Prometheus):
─────────────────────

# Envoy standard metrics exposed by Gateway:
envoy_http_downstream_rq_total{envoy_http_conn_manager_prefix="https", 
  envoy_response_code="200"} 12345

Key metrics to alert on:
┌────────────────────────────────────────────────────────────────────────────┐
│ Metric                                      Alert Threshold               │
├────────────────────────────────────────────────────────────────────────────┤
│ envoy_http_downstream_rq_5xx               > 1% of total reqs             │
│ envoy_cluster_upstream_rq_timeout          > 0.1% of reqs                 │
│ envoy_cluster_circuit_breakers_*_open      == 1 (circuit breaker open)    │
│ envoy_http_downstream_cx_active            > 80% of limit                 │
│ envoy_cluster_upstream_cx_connect_fail     > 0                            │
│ envoy_server_memory_allocated              > 1.5 GB                       │
│ envoy_http_downstream_rq_time_ms_p99       > 500ms                        │
│ gateway_route_count                        > 10000 (scale concern)        │
│ controller_reconcile_duration_seconds_p99  > 5s (control plane lagging)  │
└────────────────────────────────────────────────────────────────────────────┘

DISTRIBUTED TRACING (OpenTelemetry):
─────────────────────────────────────

Envoy generates OpenTelemetry spans:
  Span: envoy.ingress.http
    Attributes:
      http.method: GET
      http.url: https://api.example.com/v2/users/123
      http.status_code: 200
      http.request_content_length: 0
      http.response_content_length: 1234
      net.peer.ip: 1.2.3.4
      upstream_cluster: app-team/api-svc/8080
      upstream_local_address: 10.244.1.20:12345
      
    Timing:
      startTime: T0
      dns_lookup: T0 + 0ms (already resolved)
      connect: T0 + 1ms
      tls_handshake: T0 + 3ms
      request_sent: T0 + 4ms
      response_first_byte: T0 + 12ms  ← TTFB = 12ms
      response_complete: T0 + 15ms    ← total = 15ms

STRUCTURED LOGGING:
────────────────────

Envoy access log (JSON format, send to Loki/Elasticsearch):
{
  "timestamp": "2024-01-15T10:30:00.123Z",
  "method": "POST",
  "path": "/v2/users",
  "host": "api.example.com",
  "protocol": "HTTP/2",
  "response_code": 201,
  "request_duration_ms": 45,
  "bytes_sent": 256,
  "bytes_received": 1024,
  "upstream_host": "10.244.1.5:8080",
  "upstream_cluster": "app-team/api-svc/8080",
  "upstream_service_time": 42,  // X-Envoy-Upstream-Service-Time header
  "x_forwarded_for": "203.0.113.10",
  "user_agent": "MyApp/2.0",
  "request_id": "a3b9f2c1-d4e5-4f6a-b7c8-d9e0f1a2b3c4",
  "trace_id": "7b43e8f2a1c9d5b6",
  "route_name": "app-team/api-route",
  "tls_version": "TLSv1.3",
  "tls_cipher": "TLS_AES_256_GCM_SHA384"
}
```

### 17.2 ServiceMonitor for Gateway API

```yaml
# Scrape Envoy metrics with Prometheus operator
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: envoy-gateway
  namespace: envoy-gateway-system
spec:
  selector:
    matchLabels:
      app.kubernetes.io/name: envoy
  endpoints:
    - port: metrics
      path: /stats/prometheus
      interval: 15s
      scrapeTimeout: 10s
      relabelings:
        - sourceLabels: [__meta_kubernetes_pod_label_gateway_name]
          targetLabel: gateway_name
        - sourceLabels: [__meta_kubernetes_namespace]
          targetLabel: namespace
```

---

## 18. Multi-Cluster & Multi-Tenancy

### 18.1 Multi-Cluster Gateway (Gateway API for Mesh)

```
Multi-Cluster Architecture (GAMMA initiative — Gateway API for Service Mesh):

┌──────────────────────────────────────────────────────────────────────────────┐
│  Cluster A (us-east-1)              Cluster B (us-west-2)                   │
│  ──────────────────────             ──────────────────────                  │
│  Gateway: prod-gw-east              Gateway: prod-gw-west                   │
│  HTTPRoute → ServiceImport          HTTPRoute → ServiceImport                │
│                                                                              │
│         MCS (Multi-Cluster Services API):                                   │
│         ServiceExport in Cluster B: user-service                            │
│         ServiceImport in Cluster A: user-service (from B)                  │
│                                                                              │
│         ClusterSet DNS: user-service.default.svc.clusterset.local          │
│         → resolves to pod IPs in BOTH clusters                              │
│                                                                              │
│  Tools:                                                                      │
│    Submariner: cross-cluster L3 connectivity (IPsec tunnels)                │
│    Istio multi-cluster: mTLS + service discovery across clusters            │
│    Cilium Cluster Mesh: eBPF-native cross-cluster                          │
│    Admiral (Intuit): multi-cluster ServiceEntry automation                  │
│                                                                              │
│  Traffic flow with weights:                                                  │
│    HTTPRoute in Cluster A:                                                  │
│      backendRefs:                                                            │
│        - group: net.gke.io                                                  │
│          kind: ServiceImport                                                │
│          name: user-service                                                  │
│          port: 8080                                                          │
│          # weight 100: LB splits between local (A) and remote (B) pods     │
└──────────────────────────────────────────────────────────────────────────────┘
```

### 18.2 Multi-Tenancy Isolation

```yaml
# Per-team namespace isolation
# Each team gets their own namespace, routes to shared Gateway

# Team A: e-commerce
apiVersion: v1
kind: Namespace
metadata:
  name: team-ecommerce
  labels:
    gateway-access: "true"
    team: ecommerce
    environment: production

---
# ResourceQuota: limit resources per team
apiVersion: v1
kind: ResourceQuota
metadata:
  name: gateway-quota
  namespace: team-ecommerce
spec:
  hard:
    count/httproutes.gateway.networking.k8s.io: "50"
    count/grpcroutes.gateway.networking.k8s.io: "20"

---
# LimitRange: prevent resource exhaustion via large route filters
apiVersion: v1
kind: LimitRange
metadata:
  name: route-limits
  namespace: team-ecommerce

---
# Kyverno policy: enforce team prefix on hostnames
apiVersion: kyverno.io/v1
kind: ClusterPolicy
metadata:
  name: enforce-hostname-prefix
spec:
  validationFailureAction: Enforce
  rules:
    - name: check-hostname-prefix
      match:
        any:
          - resources:
              kinds: [HTTPRoute]
      validate:
        message: "HTTPRoute hostnames must start with namespace prefix"
        pattern:
          spec:
            hostnames:
              - "{{ request.object.metadata.namespace }}-*.example.com"
```

---

## 19. Production Deployment, Roll-out & Rollback

### 19.1 Installation

```bash
# Install Gateway API CRDs (standard channel — stable resources only)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/standard-install.yaml

# Install experimental channel (adds TCPRoute, UDPRoute, GRPCRoute experimental)
kubectl apply -f https://github.com/kubernetes-sigs/gateway-api/releases/download/v1.2.0/experimental-install.yaml

# Verify CRDs installed
kubectl get crd | grep gateway.networking.k8s.io
# Expected:
# gatewayclasses.gateway.networking.k8s.io
# gateways.gateway.networking.k8s.io
# httproutes.gateway.networking.k8s.io
# grpcroutes.gateway.networking.k8s.io
# tcproutes.gateway.networking.k8s.io
# tlsroutes.gateway.networking.k8s.io
# udproutes.gateway.networking.k8s.io
# referencegrants.gateway.networking.k8s.io
# backendtlspolicies.gateway.networking.k8s.io

# Install Envoy Gateway
helm install eg oci://docker.io/envoyproxy/gateway-helm \
  --version v1.2.0 \
  --namespace envoy-gateway-system \
  --create-namespace \
  --set config.envoyGateway.provider.kubernetes.rateLimitDeployment.replicas=2 \
  --set deployment.replicas=2 \
  --set podDisruptionBudget.enable=true

# Verify controller running
kubectl get pods -n envoy-gateway-system
kubectl get gatewayclass

# Apply your GatewayClass + Gateway
kubectl apply -f gateway.yaml

# Wait for Gateway to be programmed
kubectl wait gateway/prod-gateway -n infra \
  --for=condition=Programmed \
  --timeout=120s

# Check assigned address
kubectl get gateway prod-gateway -n infra -o jsonpath='{.status.addresses}'
```

### 19.2 Canary Roll-out with Traffic Splitting

```bash
# Phase 1: Deploy v2 with 0% traffic
kubectl apply -f - <<EOF
apiVersion: gateway.networking.k8s.io/v1
kind: HTTPRoute
metadata:
  name: api-route
  namespace: app-team
spec:
  parentRefs:
    - name: prod-gateway
      namespace: infra
  hostnames: ["api.example.com"]
  rules:
    - backendRefs:
        - name: api-svc-v1
          port: 8080
          weight: 100
        - name: api-svc-v2
          port: 8080
          weight: 0         # 0% initially
EOF

# Phase 2: Canary 5%
kubectl patch httproute api-route -n app-team --type=json -p='[
  {"op":"replace","path":"/spec/rules/0/backendRefs/0/weight","value":95},
  {"op":"replace","path":"/spec/rules/0/backendRefs/1/weight","value":5}
]'

# Monitor error rate (watch for 10 minutes)
watch -n5 "kubectl exec -n monitoring prometheus-0 -- \
  promtool query instant http://localhost:9090 \
  'rate(envoy_http_downstream_rq_5xx[5m]) / rate(envoy_http_downstream_rq_total[5m])'"

# Phase 3: Ramp up 5 → 25 → 50 → 100%
for weight in 25 50 100; do
  kubectl patch httproute api-route -n app-team --type=json -p="[
    {\"op\":\"replace\",\"path\":\"/spec/rules/0/backendRefs/0/weight\",\"value\":$((100-weight))},
    {\"op\":\"replace\",\"path\":\"/spec/rules/0/backendRefs/1/weight\",\"value\":${weight}}
  ]"
  echo "→ v2 at ${weight}%, sleeping 5m"
  sleep 300
done
```

### 19.3 Rollback

```bash
# Immediate rollback: set v2 weight to 0
kubectl patch httproute api-route -n app-team --type=json -p='[
  {"op":"replace","path":"/spec/rules/0/backendRefs/0/weight","value":100},
  {"op":"replace","path":"/spec/rules/0/backendRefs/1/weight","value":0}
]'

# Verify: data plane applies in <1 second (xDS push latency)
kubectl get httproute api-route -n app-team -o jsonpath='{.status.parents[0].conditions}'

# Full rollback: delete v2 backendRef entirely
kubectl patch httproute api-route -n app-team --type=json -p='[
  {"op":"remove","path":"/spec/rules/0/backendRefs/1"}
]'
```

---

## 20. Failure Modes & Mitigations

```
┌────────────────────────────────────────────────────────────────────────────────┐
│               FAILURE MODES & MITIGATIONS                                      │
├──────────────────────────────┬─────────────────────────────────────────────────┤
│ Failure                      │ Detection & Mitigation                          │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ Controller crash             │ Leader election → standby takes over (<30s)     │
│                              │ Data plane continues (last programmed config)   │
│                              │ Metric: controller_up == 0                      │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ xDS push lag                 │ HTTPRoute created but not yet in data plane     │
│                              │ Check: status.conditions[Programmed]            │
│                              │ Tune: envoy_gateway xds_push_timeout=10s        │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ Backend pod crash mid-request│ Envoy circuit breaker + retry (BackendPolicy)  │
│                              │ Active health check detects within 3s           │
│                              │ In-flight: TCP RST → Envoy retries on safe      │
│                              │ methods (GET, HEAD) only                        │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ TLS cert expiry              │ cert-manager auto-renews 30d before expiry      │
│                              │ SDS hot-reload: Envoy gets new cert without     │
│                              │ connection interruption (graceful drain)        │
│                              │ Alert: cert_expiry_days < 14                   │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ Route conflict               │ Controller sets Accepted=False on newer route   │
│                              │ reason=Conflicted in status                     │
│                              │ Older route wins (temporal priority)            │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ ReferenceGrant deleted       │ Immediately: route gets ResolvedRefs=False      │
│                              │ Backend traffic stops (fail closed)             │
│                              │ Alert on ResolvedRefs=False condition           │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ Envoy OOM                    │ K8s kills pod, new pod starts                   │
│                              │ Connection drain: 30s before SIGTERM            │
│                              │ Tune: resources.requests.memory=512Mi          │
│                              │       resources.limits.memory=1Gi              │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ kube-apiserver unavailable   │ Controller cannot reconcile (watches blocked)   │
│                              │ Data plane keeps serving with last known config │
│                              │ Controller has retry backoff (exponential)      │
├──────────────────────────────┼─────────────────────────────────────────────────┤
│ DNS resolution failure       │ Envoy cannot resolve backend Service hostname   │
│                              │ Cluster health: DEGRADED                        │
│                              │ Mitigation: use pod IPs directly (EDS) not DNS  │
└──────────────────────────────┴─────────────────────────────────────────────────┘
```

---

## 21. Benchmarking & Fuzzing

### 21.1 Throughput Benchmark

```bash
# Install wrk2 (constant-rate HTTP benchmarking tool)
git clone https://github.com/giltene/wrk2.git && cd wrk2 && make

# Benchmark: 10K RPS for 60 seconds with 100 connections
./wrk -t4 -c100 -d60s -R10000 \
  --latency \
  https://gateway-ip:443/v2/users/123

# Expected output for well-tuned Envoy Gateway:
# Latency Distribution
#    50%    1.23ms
#    75%    2.45ms
#    90%    4.12ms
#    99%    15.6ms
#   99.9%   45.2ms
#  100%    120.0ms   (Highest observed)
# Requests/sec: 9987.45

# Benchmark gRPC (ghz tool)
ghz --insecure \
  --proto user.proto \
  --call user.v1.UserService.GetUser \
  --concurrency 100 \
  --total 100000 \
  --rps 10000 \
  grpc-gateway-ip:443

# Tune Envoy Gateway for throughput:
# envoy-gateway-system/envoygateway-config ConfigMap:
#   worker_threads: 0  # use all CPUs
#   overload_manager: true
#   max_requests_per_io_cycle: 256

# Linux kernel tuning for high-throughput gateway:
# /etc/sysctl.d/99-gateway.conf:
sysctl -w net.core.somaxconn=65535            # TCP accept queue
sysctl -w net.ipv4.tcp_max_syn_backlog=65535  # SYN queue
sysctl -w net.core.netdev_max_backlog=65535   # NIC RX queue
sysctl -w net.ipv4.tcp_tw_reuse=1            # reuse TIME_WAIT sockets
sysctl -w net.ipv4.ip_local_port_range="1024 65535"  # more ephemeral ports
sysctl -w net.core.rmem_max=134217728        # 128 MiB max socket recv buffer
sysctl -w net.core.wmem_max=134217728        # 128 MiB max socket send buffer
sysctl -w net.ipv4.tcp_rmem="4096 87380 134217728"
sysctl -w net.ipv4.tcp_wmem="4096 65536 134217728"
sysctl -w net.ipv4.tcp_congestion_control=bbr  # BBR: better throughput under packet loss
sysctl -w net.core.default_qdisc=fq            # required for BBR
```

### 21.2 Fuzzing Gateway Parsing

```bash
# Fuzz HTTP request parser (using Go's built-in fuzzer)
# File: pkg/parser/fuzz_test.go

# go test -fuzz=FuzzParseHTTPRoute -fuzztime=5m ./pkg/parser/

# Content of fuzz_test.go:
cat << 'EOF' > pkg/parser/fuzz_test.go
package parser

import (
    "testing"
    "net/http"
    "strings"
)

// FuzzParseHTTPRoute: fuzz the HTTPRoute match parsing
// Finds: path traversal, header injection, integer overflow in weights
func FuzzParseHTTPRoute(f *testing.F) {
    // Seed corpus: valid paths
    f.Add("/v2/users")
    f.Add("/v2/users?id=1&format=json")
    f.Add("/../../../etc/passwd")   // path traversal
    f.Add("/v2\x00null")           // null byte injection
    f.Add(strings.Repeat("/v", 10000)) // long path

    f.Fuzz(func(t *testing.T, path string) {
        // Should not panic, should not crash, should not consume unbounded memory
        defer func() {
            if r := recover(); r != nil {
                t.Errorf("panic on input %q: %v", path, r)
            }
        }()

        req, err := http.NewRequest("GET", "http://example.com"+path, nil)
        if err != nil {
            return // invalid URL, expected
        }

        // Your parser under test
        _ = MatchRoute(req.URL.Path, testRoutes)
    })
}
EOF

# Run fuzz test
go test -fuzz=FuzzParseHTTPRoute -fuzztime=5m -fuzzminimizetime=1m ./pkg/parser/

# Run Rust fuzz (cargo-fuzz, uses libFuzzer)
cargo install cargo-fuzz
cargo fuzz init
cargo fuzz add parse_route
# Edit fuzz/fuzz_targets/parse_route.rs to call your parser
cargo fuzz run parse_route -- -max_total_time=300

# Fuzz TLS ClientHello parsing (find SNI parsing bugs):
# Using AFL++ on Envoy (requires instrumented build):
# afl-fuzz -i tls_corpus/ -o tls_findings/ -- envoy-tls-parser @@
```

---

## 22. Next 3 Steps

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              NEXT 3 STEPS                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  STEP 1: Deploy end-to-end lab (1 day)                                     │
│  ─────────────────────────────────────                                      │
│  kind create cluster --config kind-multinode.yaml                          │
│  kubectl apply -f standard-install.yaml                                    │
│  helm install eg oci://docker.io/envoyproxy/gateway-helm --version v1.2.0  │
│  Deploy: HTTPRoute with canary (90/10 split), BackendTLSPolicy,            │
│          ReferenceGrant cross-namespace                                     │
│  Observe: kubectl get events --field-selector reason=Programmed             │
│  Run:     wrk2 benchmark, capture metrics in Grafana                       │
│                                                                             │
│  STEP 2: Implement custom controller (3-5 days)                            │
│  ──────────────────────────────────────────────                             │
│  Use the Go controller skeleton in §14.1 as base                          │
│  Add: xDS gRPC server that pushes Envoy config (use go-control-plane)     │
│  Test: unit test reconcile loop with envtest framework                     │
│  Fuzz: run fuzz tests against your route parser                            │
│  Goal: understand exactly what Envoy Gateway's controller does internally  │
│                                                                             │
│  STEP 3: Deep eBPF instrumentation (1 week)                               │
│  ────────────────────────────────────────────                              │
│  Write BPF program to trace gateway packet path:                          │
│    tracepoint:net:netif_receive_skb → log sk_buff → tcp_rcv               │
│  Use bpftrace to measure latency at each hop:                              │
│    NIC RX → XDP → netfilter PREROUTING → tcp_rcv → envoy accept()        │
│  Compare: iptables vs Cilium eBPF path on same workload                   │
│  Command to start:                                                         │
│    bpftrace -e 'kretprobe:tcp_v4_connect { printf("%d\n", elapsed); }'   │
│    bpftrace -e 'tracepoint:net:netif_receive_skb { @ = hist(args->len); }'│
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 23. References

### Specifications & KEPs

- **Gateway API Spec**: https://gateway-api.sigs.k8s.io/
- **Gateway API GitHub**: https://github.com/kubernetes-sigs/gateway-api
- **KEP-1959** (Gateway API v1 GA): https://github.com/kubernetes/enhancements/tree/master/keps/sig-network/1959-service-apis
- **GAMMA Initiative** (mesh): https://gateway-api.sigs.k8s.io/mesh/
- **Multi-Cluster Services**: https://github.com/kubernetes-sigs/mcs-api

### Implementations

- **Envoy Gateway**: https://gateway.envoyproxy.io/
- **Cilium Gateway API**: https://docs.cilium.io/en/stable/network/servicemesh/gateway-api/
- **NGINX Gateway Fabric**: https://github.com/nginx/nginx-gateway-fabric
- **AWS LBC**: https://kubernetes-sigs.github.io/aws-load-balancer-controller/
- **Azure AGFC**: https://learn.microsoft.com/azure/application-gateway/for-containers/

### Linux Kernel & Networking

- **Linux Kernel Source** (sk_buff, netfilter): https://elixir.bootlin.com/linux/latest/source/include/linux/skbuff.h
- **eBPF/XDP Tutorial**: https://github.com/xdp-project/xdp-tutorial
- **Cilium BPF Docs**: https://docs.cilium.io/en/stable/bpf/
- **Linux Networking Book**: "Understanding Linux Network Internals" — Christian Benvenuti (O'Reilly)
- **TCP/IP Illustrated Vol 1**: W. Richard Stevens

### Cloud Provider Internals

- **AWS ENA Driver**: https://github.com/amzn/amzn-drivers
- **GCP Andromeda paper**: "Andromeda: Performance, Isolation, and Velocity at Scale in Cloud Network Virtualization" (NSDI 2018)
- **Azure AcceleratedNetworking**: https://learn.microsoft.com/azure/virtual-network/accelerated-networking-overview

### xDS / Envoy

- **xDS API spec**: https://github.com/envoyproxy/data-plane-api
- **go-control-plane** (xDS server in Go): https://github.com/envoyproxy/go-control-plane
- **Envoy docs**: https://www.envoyproxy.io/docs/envoy/latest/

### Security

- **SPIFFE/SPIRE**: https://spiffe.io/
- **cert-manager**: https://cert-manager.io/
- **Cosign/Sigstore**: https://docs.sigstore.dev/
- **OPA Gatekeeper**: https://open-policy-agent.github.io/gatekeeper/

### RFCs

- **RFC 7230**: HTTP/1.1 Message Syntax
- **RFC 7540**: HTTP/2
- **RFC 9114**: HTTP/3
- **RFC 8446**: TLS 1.3
- **RFC 7301**: ALPN (Application-Layer Protocol Negotiation)
- **RFC 6066**: TLS SNI extension
- **RFC 7858**: DNS over TLS

---

*Document version: Gateway API v1.2 (Kubernetes 1.31+)*
*Last updated: 2024 — covers stable + experimental channel resources*
*Kernel references: Linux 6.x (eBPF, XDP, kTLS)*