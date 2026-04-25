# Cloud-Native Networking Protocols: L1 → L7
> Complete reference of every networking protocol handled by cloud-native frameworks, CNIs, service meshes, proxies, SDNs, and orchestration stacks.  
> OSI model framing used throughout. Protocols mapped to active CNCF/cloud-native projects.

---

## Table of Contents

1. [Layer 1 — Physical / Hardware Abstraction](#layer-1--physical--hardware-abstraction)
2. [Layer 2 — Data Link](#layer-2--data-link)
3. [Layer 3 — Network](#layer-3--network)
4. [Layer 3.5 — Overlay / Encapsulation / Tunnel](#layer-35--overlay--encapsulation--tunnel)
5. [Layer 4 — Transport](#layer-4--transport)
6. [Layer 4.5 — RDMA / High-Performance Transport](#layer-45--rdma--high-performance-transport)
7. [Layer 5 — Session](#layer-5--session)
8. [Layer 6 — Presentation / Security](#layer-6--presentation--security)
9. [Layer 7 — Application](#layer-7--application)
10. [Control Plane Protocols](#control-plane-protocols)
11. [Cloud-Native Identity & Policy Protocols](#cloud-native-identity--policy-protocols)
12. [Observability Wire Protocols](#observability-wire-protocols)
13. [Protocol × Project Matrix](#protocol--project-matrix)

---

## Layer 1 — Physical / Hardware Abstraction

> Cloud-native stacks abstract physical media but interact with hardware through driver APIs, offload engines, and PCIe fabric.

```
| Protocol / Technology | RFC / Std | Cloud-Native Relevance | Projects / Tools |
|---|---|---|---|
| **Ethernet (IEEE 802.3)** | IEEE 802.3 | Universal L2 substrate; 1G/10G/25G/40G/100G/400G in data centers | All CNIs, OVS, OVN, DPDK |
| **InfiniBand (IB)** | IBTA spec | RDMA fabric; HPC and AI workloads on bare-metal k8s nodes | SR-IOV device plugin, RDMA device plugin (k8s) |
| **SR-IOV (PCIe)** | PCIe spec | Virtual Functions exposed to VMs/containers; kernel bypass | Multus CNI, SR-IOV CNI, Intel Device Plugin |
| **DPDK (Data Plane Dev Kit)** | — | Kernel-bypass userspace packet processing; OVS-DPDK | OVS-DPDK, VPP, Tungsten Fabric |
| **VPP (Vector Packet Processing)** | — | FD.io userspace fast path; replaces kernel network stack | Contiv/VPP CNI, Ligato, Calico VPP |
| **eBPF (XDP hook)** | Linux kernel | Hook at NIC driver level before kernel stack; sub-μs processing | Cilium, Katran (Meta LB), Falco |
| **XDP (eXpress Data Path)** | Linux kernel | Earliest kernel hook; raw packet processing at driver | Cilium, bpfilter, xdp-tools |
| **SmartNIC / DPU offload** | Vendor | P4 programmable NICs (Mellanox BlueField, Intel IPU) offloading OVS/IPsec | NVIDIA DOCA, OVS-TC offload, Antrea (offload mode) |
| **RDMA (generic)** | IBTA / RoCE | Zero-copy transport; used by storage and ML frameworks on k8s | Rook/Ceph RDMA, NVIDIA GPUDirect |
```

---

## Layer 2 — Data Link

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **Ethernet Frame (DIX/802.3)** | IEEE 802.3 | Base framing; src/dst MAC, EtherType | All |
| **IEEE 802.1Q VLAN** | 802.1Q | VLAN tagging; 4096 VIDs; trunk/access ports | OVS, OVN, Antrea, Cilium (host networking) |
| **IEEE 802.1ad QinQ** | 802.1ad | Double-tagged VLANs (Provider Bridges); outer + inner VLAN | OVS, large multi-tenant DC fabrics |
| **IEEE 802.1AX LACP** | 802.1AX | Link Aggregation Control Protocol; bonding NICs | Linux bonding, OVS bonding, Multus |
| **IEEE 802.1AE MACsec** | 802.1AE | L2 hop-by-hop authenticated encryption | OVS-MACsec, Linux kernel MACsec, Cilium MACsec |
| **IEEE 802.1D STP / 802.1w RSTP** | 802.1D/w | Spanning Tree; loop prevention | OVS (RSTP mode), underlay switches |
| **IEEE 802.1s MSTP** | 802.1s | Multiple Spanning Tree; per-VLAN instances | Underlay only; cloud-native avoids STP via ECMP/BGP |
| **IEEE 802.1AB LLDP** | 802.1AB | Link Layer Discovery Protocol; neighbor discovery | OVS, Antrea (node topology), ONOS |
| **IEEE 802.3ad (legacy LACP ref)** | 802.3ad | Subsumed by 802.1AX | — |
| **ARP (Address Resolution Protocol)** | RFC 826 | IPv4 MAC resolution; ARP cache, GARP | All CNIs (kube-proxy, Cilium, Calico); ARP suppression in EVPN |
| **GARP (Gratuitous ARP)** | RFC 5227 | IP conflict detection; VIP failover | keepalived, MetalLB, kube-vip |
| **IEEE 802.11 (Wi-Fi)** | 802.11 | Wireless; edge/IoT k8s nodes | K3s edge, Flannel (Wi-Fi overlay) |
| **FC (Fibre Channel)** | T11 | Block storage transport; FC fabric | Rook (FC volumes), CSI FC drivers |
| **FCoE (FC over Ethernet)** | T11 | FC frames encapsulated in Ethernet | Legacy storage CNI integration |
```

---

## Layer 3 — Network

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **IPv4** | RFC 791 | 32-bit addressing; fragmentation; TTL | All CNIs, all service meshes |
| **IPv6** | RFC 8200 | 128-bit; flow labels; extension headers; dual-stack | Cilium (full IPv6), Calico, Antrea, AWS VPC CNI |
| **ICMP v4** | RFC 792 | Echo, unreachable, redirect, time-exceeded | All (MTU path discovery, liveness probes) |
| **ICMPv6** | RFC 4443 | Echo + NDP messages (NS/NA/RS/RA) | Cilium (IPv6 NDP proxy), Calico IPv6 |
| **NDP (Neighbor Discovery Protocol)** | RFC 4861 | IPv6 MAC resolution; router discovery; replaces ARP | Cilium, Calico IPv6 |
| **SLAAC (Stateless Address Autoconfiguration)** | RFC 4862 | IPv6 auto-addressing via RA | Cilium IPv6, node IPv6 auto-config |
| **DHCPv4** | RFC 2131 | IPv4 dynamic address assignment | Multus (Whereabouts IPAM), Flannel, Canal |
| **DHCPv6** | RFC 3315/8415 | IPv6 stateful/stateless address assignment | Cilium dual-stack, Antrea IPv6 |
| **OSPF v2/v3** | RFC 2328/5340 | Link-state IGP; area-based SPF | BGP-only in cloud-native; OSPF in underlay DC fabric |
| **IS-IS** | ISO 10589 | Link-state IGP; used by large DC spine/leaf fabrics | Underlay fabric (not cloud-native directly) |
| **RIP v2** | RFC 2453 | Distance-vector; legacy | Not used in cloud-native |
| **BGP (Border Gateway Protocol) v4** | RFC 4271 | Path-vector; the cloud-native routing protocol | Calico (node-to-node mesh), Cilium BGP CP, MetalLB BGP, GoBGP |
| **BGP Multiprotocol (MP-BGP)** | RFC 4760 | AFI/SAFI extensions; VPNv4/VPNv6/EVPN/L2VPN | OVN-EVPN, Calico EVPN, Tungsten Fabric |
| **EVPN (Ethernet VPN)** | RFC 7432 | BGP control plane for L2/L3 overlays; MAC/IP advertisement | OVN+EVPN, Calico BGP EVPN, Tungsten Fabric |
| **MPLS** | RFC 3031 | Label switching; used in WAN and some DC fabrics | Not cloud-native native; SR-MPLS in Segment Routing |
| **Segment Routing (SR-MPLS / SRv6)** | RFC 8402/8986 | Source routing via label/IPv6 segment stacks | Cilium SRv6, Contiv-VPP, Linux kernel SRv6 |
| **SRv6 (Segment Routing over IPv6)** | RFC 8986 | SRv6 SIDs in IPv6 extension headers | Cilium SRv6 egress, Linux kernel iproute2 |
| **ECMP (Equal-Cost Multi-Path)** | RFC 2991 | Hash-based multi-path forwarding | Cilium, Calico, kube-proxy IPVS mode |
| **PIM-SM / PIM-SSM (Multicast)** | RFC 7761 | IP multicast routing | Antrea multicast, OVN multicast, Calico multicast |
| **IGMP v1/v2/v3** | RFC 3376 | IPv4 multicast group membership | Antrea multicast, Linux kernel |
| **MLD v1/v2** | RFC 3810 | IPv6 multicast group membership | Cilium IPv6 multicast, Antrea |
| **IP-in-IP (IPIP)** | RFC 2003 | IPv4-in-IPv4 encapsulation | Calico IPIP mode, Flannel IPIP |
| **IP-in-IPv6 / IPv6-in-IP** | RFC 2473 | Dual-stack tunnel transitional | Calico IPv4-in-IPv6 |
| **GRE (Generic Routing Encapsulation)** | RFC 2784/2890 | Protocol-agnostic L3 tunnel | OVS (GRE tunnels), Flannel (legacy), Weave |
| **NAT (Network Address Translation)** | RFC 3022 | SNAT/DNAT/masquerade | kube-proxy iptables/ipvs, Cilium eBPF NAT, Antrea |
| **SNAT / Masquerade** | — | Outbound address hiding | All CNIs (pod egress), MetalLB |
| **DNAT** | — | Inbound destination rewriting; k8s Service ClusterIP | kube-proxy, Cilium kube-proxy replacement |
| **NPTv6 (Network Prefix Translation)** | RFC 6296 | IPv6 prefix translation | Cilium |
| **Policy-Based Routing (PBR)** | Linux iproute2 | ip rule + ip route tables | Cilium (per-endpoint routing tables), Antrea |
| **VRF (Virtual Routing and Forwarding)** | RFC 4364 | Isolated routing table per tenant | OVN, Cilium VRF, Linux VRF |
```

---

## Layer 3.5 — Overlay / Encapsulation / Tunnel

> These protocols span L2–L4 but are primarily classified as network overlay/tunneling mechanisms.

```
| Protocol | RFC / Std | Key Fields | Cloud-Native Projects |
|---|---|---|---|
| **VXLAN (Virtual eXtensible LAN)** | RFC 7348 | UDP/4789; 24-bit VNI; L2 over L3 | Flannel, Calico, Cilium, Antrea, OVS, OVN, Weave |
| **Geneve (Generic Network Virtualization Encapsulation)** | RFC 8926 | UDP/6081; variable TLV options; preferred over VXLAN | OVN, OVS-Geneve, Antrea (Geneve mode), AWS VPC (Nitro) |
| **NVGRE (Network Virtualization using GRE)** | RFC 7637 | GRE key as VNI; Microsoft origin | Rare in Linux cloud-native; Azure HNS (Windows k8s) |
| **STT (Stateless Transport Tunneling)** | draft-ietf | TCP-like framing; NIC TSO offload benefit | OVS (legacy), NSX |
| **GUE (Generic UDP Encapsulation)** | RFC 8086 | UDP; FOU/GUE variants; lightweight | Linux kernel fou/gue modules, Cilium |
| **FOU (Foo-over-UDP)** | RFC 8086 | Minimal UDP encap; IP proto in UDP | Cilium (IPIP-over-UDP fallback) |
| **LISP (Locator/ID Separation Protocol)** | RFC 6830 | EID/RLOC split; overlay routing | OpenDaylight, ONOS; rare in CNCF |
| **WireGuard** | — (in-kernel since 5.6) | ChaCha20-Poly1305; Curve25519 keys; UDP | Cilium WireGuard encryption, k3s built-in, Flannel WireGuard |
| **IPsec (Tunnel mode)** | RFC 4301/4303 | ESP tunnel; IKEv2 keying | Calico IPsec, Cilium IPsec, Antrea IPsec, StrongSwan |
| **IPsec (Transport mode)** | RFC 4301 | ESP over existing IP; no outer header | Cilium (pod-to-pod IPsec transport) |
| **MPLS-over-UDP** | RFC 7510 | MPLS label stack in UDP | VPP, Segment Routing implementations |
| **SRv6 encapsulation** | RFC 8986 | IPv6 SRH extension header | Cilium SRv6, Linux iproute2 |
| **VLAN-over-VXLAN** | — | Tenant VLAN preserved inside VNI | OVN, NSX, Tungsten Fabric |
| **GRE over IPv6** | RFC 7676 | GRE tunnel using IPv6 outer | OVS, VPP |

```

---

## Layer 4 — Transport

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **TCP (Transmission Control Protocol)** | RFC 793/9293 | Reliable, ordered, connection-oriented | All (API server, etcd, Envoy, ingress) |
| **UDP (User Datagram Protocol)** | RFC 768 | Unreliable, connectionless; used by overlays and DNS | All (VXLAN, Geneve, DNS, QUIC) |
| **SCTP (Stream Control Transmission Protocol)** | RFC 4960 | Multi-stream, multi-homed; telecom / 5G | Multus+SCTP for 5G CNFs, OVS sctp offload |
| **DCCP (Datagram Congestion Control Protocol)** | RFC 4340 | Unreliable with CC; rare | Not commonly used in cloud-native |
| **QUIC** | RFC 9000 | UDP-based reliable+encrypted transport; 0-RTT | Envoy (HTTP/3), Istio (future), gRPC-QUIC, NATS |
| **RUDP (Reliable UDP variants)** | — | KCP, QUIC internals | Some service meshes, game backends |
| **MPTCP (Multipath TCP)** | RFC 8684 | Multiple subflows; redundant paths | Linux 5.6+; k8s node resilience (experimental) |
| **TCP BBR congestion control** | Google/RFC 9438 | Bandwidth-delay product model; cloud default in GCP/AWS | Linux kernel tuning for k8s nodes |
| **ECN (Explicit Congestion Notification)** | RFC 3168 | In-network congestion signaling | DPDK, high-perf k8s node tuning |
| **IPVS (IP Virtual Server)** | — | L4 load balancing in kernel; kube-proxy IPVS mode | kube-proxy, LVS-based ingress |
| **eBPF sockmap / sk_msg** | Linux kernel | L4 socket-level intercept / redirect | Cilium (L4 policy, sockmap acceleration) |
| **eBPF cgroup-sock** | Linux kernel | Per-cgroup socket hook; pod-level L4 | Cilium, Falco socket-level |
```

---

## Layer 4.5 — RDMA / High-Performance Transport

> Specialized zero-copy transports used for AI/ML workloads and high-throughput storage on cloud-native clusters.

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **RoCE v1 (RDMA over Converged Ethernet)** | IBTA | IB transport over L2 Ethernet | NVIDIA DOCA, k8s RDMA device plugin |
| **RoCE v2** | IBTA | IB transport over UDP/IPv4/IPv6 (routable) | NVIDIA BlueField, AWS EFA, Azure InfiniBand |
| **iWARP (iSCSI RDMA Protocol)** | RFC 5040-5044 | RDMA over TCP; less common | Intel RDMA NICs, Chelsio |
| **EFA (Elastic Fabric Adapter)** | AWS-proprietary | AWS custom RDMA fabric; SRD protocol | AWS EFA k8s device plugin |
| **NVMe-oF over RDMA** | NVMe spec | Block storage over RDMA fabric | Rook/Ceph NVMe-oF, Longhorn (future) |
| **NVMe-oF over TCP** | NVMe spec | Block storage over TCP | Rook/Ceph, OpenEBS NVMe-oF |
| **iSCSI** | RFC 3720 | Block storage over TCP | Rook/Ceph iSCSI, OpenEBS, CSI drivers |
| **NFS v3/v4/v4.1/v4.2** | RFC 1813/7530/8881 | File storage; pNFS in v4.1 | NFS CSI driver, Rook NFS, EFS CSI |
| **SMB3 / CIFS** | MS-SMB2 | Windows file protocol | SMB CSI driver (k8s Windows nodes) |
| **Fibre Channel over IP (FCIP)** | RFC 3821 | FC tunneling over IP WANs | Legacy CSI FC drivers |
```

---

## Layer 5 — Session

> Mostly subsumed in TCP/TLS stacks; relevant in cloud-native as protocol framing layers.

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **TLS Handshake (session establishment)** | RFC 8446 | Session negotiation within TLS 1.3 | All (Envoy, Istio, Linkerd, Nginx, cert-manager) |
| **DTLS (Datagram TLS)** | RFC 9147 | TLS over UDP; session management | Cilium (DTLS option), IoT k8s edge |
| **SOCKS5** | RFC 1928 | Proxy protocol; session-level routing | Telepresence, some sidecar egress proxies |
| **WebSocket session upgrade** | RFC 6455 | HTTP/1.1 → WS upgrade; persistent session | Nginx ingress, Envoy WS support |
| **Multiplexing streams (H2/QUIC)** | RFC 9113/9000 | Multiple logical streams over one connection | Envoy, gRPC, Istio |
| **SPIFEE Workload session** | SPIFFE spec | Attested session identity binding | SPIRE, Istio SPIFFE, cert-manager CSI |
```

---

## Layer 6 — Presentation / Security

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **TLS 1.2** | RFC 5246 | Widespread; being phased to 1.3 | Nginx, HAProxy, older Envoy configs |
| **TLS 1.3** | RFC 8446 | 0-RTT, simplified handshake, mandatory FS | Envoy (default), Istio, Linkerd, cert-manager |
| **mTLS (Mutual TLS)** | RFC 8446 + client certs | Both sides authenticate with X.509 certs | Istio, Linkerd, Consul Connect, SPIRE |
| **DTLS 1.3** | RFC 9147 | Datagram TLS 1.3 | Cilium DTLS, IoT edge |
| **X.509 / PKIX** | RFC 5280 | Certificate format; SVIDs | cert-manager, SPIRE, Vault PKI |
| **PKCS#7 / CMS** | RFC 5652 | Signed/encrypted data containers | OPA bundle signing, Vault |
| **PKCS#12** | RFC 7292 | Cert+key bundle format | Java-based k8s controllers |
| **SNI (Server Name Indication)** | RFC 6066 | TLS extension; L7 routing without decrypt | Envoy SNI routing, Istio TLS passthrough |
| **ALPN (Application-Layer Protocol Negotiation)** | RFC 7301 | TLS extension; h2/h3/grpc identification | Envoy, Istio ALPN-based routing |
| **ASN.1 / DER / PEM encoding** | ITU-T X.680 | Certificate and key encoding | All PKI in k8s ecosystem |
```

---

## Layer 7 — Application

### 7.1 HTTP Family

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **HTTP/1.0** | RFC 1945 | Per-request TCP connection | Legacy support in Nginx, HAProxy |
| **HTTP/1.1** | RFC 7230-7235 | Keep-alive, pipelining, chunked encoding | Nginx, Envoy, Traefik, Istio |
| **HTTP/2** | RFC 7540/9113 | Multiplexed streams, header compression (HPACK), server push | Envoy (default), gRPC, Istio, Linkerd, Contour |
| **HTTP/3** | RFC 9114 | HTTP over QUIC; 0-RTT; no HOL blocking | Envoy (experimental), NGINX unit, Caddy |
| **WebSocket** | RFC 6455 | Full-duplex over HTTP/1.1 upgrade | Nginx ingress, Envoy WS, Argo CD WS |
| **Server-Sent Events (SSE)** | WHATWG | Unidirectional server push over HTTP | kubectl watch, k8s API watch streams |
| **gRPC** | Google / CNCF | HTTP/2 + Protobuf; bidirectional streaming | Istio, Envoy xDS, Linkerd, etcd, OTLP |
| **gRPC-Web** | gRPC spec | gRPC over HTTP/1.1 for browsers | Envoy gRPC-Web filter, Contour |
| **GraphQL over HTTP** | GraphQL spec | Query language over HTTP/POST | Not core CNCF but used in k8s management UIs |
| **REST / JSON-RPC over HTTP** | — | Kubernetes API server, most cloud APIs | kube-apiserver, operator-sdk, client-go |
```

### 7.2 DNS Family

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **DNS (UDP/53)** | RFC 1034/1035 | Name resolution; A/AAAA/SRV/PTR/TXT | CoreDNS (default k8s DNS), ExternalDNS |
| **DNS over TCP (DNS/TCP)** | RFC 7766 | Large responses, zone transfer | CoreDNS TCP fallback |
| **DNSSEC** | RFC 4033-4035 | Signed DNS records; chain of trust | CoreDNS DNSSEC plugin |
| **DNS-SD (DNS Service Discovery)** | RFC 6763 | Service discovery via DNS SRV/TXT | Consul, k8s ExternalDNS, Linkerd |
| **mDNS (Multicast DNS)** | RFC 6762 | Zero-conf local DNS; .local domain | K3s (node discovery), edge IoT |
| **DoT (DNS over TLS)** | RFC 7858 | Encrypted DNS queries | CoreDNS DoT forward |
| **DoH (DNS over HTTPS)** | RFC 8484 | DNS over HTTP/2 | CoreDNS DoH, external resolvers |
| **DoQ (DNS over QUIC)** | RFC 9250 | DNS over QUIC transport | Experimental; CoreDNS future |
```

### 7.3 Service Discovery & Configuration

```
| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **etcd (Raft + gRPC)** | Raft paper + gRPC | Consensus KV store; k8s state backend | etcd, k8s API server, Fleet |
| **Raft consensus** | Ongaro & Ousterhout | Leader election + log replication | etcd, Consul, TiKV, CockroachDB |
| **Gossip (SWIM / Memberlist)** | MIT SWIM paper | Cluster membership + failure detection | Consul, Serf, Cilium (node discovery), Weave |
| **ZooKeeper ZAB** | Apache | Atomic broadcast for Zookeeper | Kafka, legacy; not k8s-native |
| **Consul RPC** | HashiCorp | Service registration + health check wire protocol | Consul CNI, Consul Connect |
| **NATS Core** | NATS.io | Subject-based pub-sub; at-most-once | NATS k8s operator, Dapr, Knative |
| **NATS JetStream** | NATS.io | Persistent streams over NATS | NATS JetStream operator |
| **NATS Leaf Node / Cluster** | NATS.io | Multi-cluster federation protocol | NATS super-cluster in k8s |

### 7.4 Messaging & Event Streaming

| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **AMQP 0-9-1** | AMQP WG | RabbitMQ wire protocol | RabbitMQ on k8s, Knative Eventing |
| **AMQP 1.0** | ISO/IEC 19464 | Standardized message framing | ActiveMQ Artemis, Azure Service Bus, Qpid |
| **Kafka Protocol** | Apache | Custom TCP binary; produce/fetch/metadata | Strimzi (k8s Kafka operator), Confluent |
| **MQTT 3.1.1** | OASIS | Pub-sub for IoT; lightweight | EMQX on k8s, HiveMQ, Eclipse Mosquitto |
| **MQTT 5.0** | OASIS | Enhanced MQTT with reason codes, shared subs | EMQX 5.x on k8s |
| **STOMP** | stomp.github.io | Text-based messaging over TCP | ActiveMQ on k8s; less common |
| **OpenMessaging** | Apache / CNCF | Messaging abstraction API | Dapr pub-sub |
| **CloudEvents** | CNCF spec | Event envelope schema over HTTP/AMQP/Kafka | Knative, Dapr, Argo Events |

### 7.5 Load Balancing & Proxy Protocols

| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **PROXY Protocol v1/v2** | HAProxy spec | Client IP preservation through proxies | HAProxy, Nginx, Envoy, Traefik |
| **HSTS (HTTP Strict Transport Security)** | RFC 6797 | Force HTTPS via response header | All ingress controllers |
| **HTTP CONNECT** | RFC 7231 | Tunnel establishment through HTTP proxy | Envoy CONNECT, Istio egress |
| **CORS (Cross-Origin Resource Sharing)** | WHATWG | HTTP header exchange for browser security | Envoy CORS filter, Nginx, Kong |

### 7.6 Time Synchronization

| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **NTP v4** | RFC 5905 | Time sync; critical for TLS cert validity + etcd | chrony/ntpd on k8s nodes, cluster-proportional |
| **PTP / IEEE 1588** | IEEE 1588 | Sub-microsecond precision; 5G / financial | linuxptp, PTP operator on k8s, Telecom Blueprint |

### 7.7 Remote Execution & Terminal

| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **SSH v2** | RFC 4251-4254 | Encrypted remote shell; key-based auth | kubectl exec (over SPDY/WS), Teleport, Boundary |
| **SFTP** | RFC 4253 | SSH file transfer | Argo CD Git-over-SSH, Gitea |
| **kubectl exec (SPDY)** | Google SPDY (deprecated) | k8s exec/attach/port-forward multiplex | kube-apiserver (being migrated to WS) |
| **kubectl exec (WebSocket)** | RFC 6455 | Replacement for SPDY in newer k8s | k8s 1.29+ default exec transport |

### 7.8 Object / Block / File Storage Protocols

| Protocol | RFC / Std | Description | Cloud-Native Projects |
|---|---|---|---|
| **S3 (Simple Storage Service) API** | AWS proprietary | Object storage REST API; de-facto standard | MinIO, Rook/Ceph RGW, Longhorn backups |
| **S3 Select** | AWS extension | SQL queries on S3 objects | MinIO S3 Select |
| **GCS JSON/XML API** | Google | GCS object storage REST API | GCS CSI driver |
| **Azure Blob REST API** | Microsoft | Azure object storage REST | Azure Blob CSI driver |
| **CSI (Container Storage Interface)** | CNCF spec | gRPC protocol between k8s and storage plugins | All CSI drivers (Ceph, AWS EBS, Azure Disk) |
| **Ceph RADOS** | Ceph project | Object store native protocol | Rook/Ceph, Ceph CSI |
| **Ceph RBD (RADOS Block Device)** | Ceph project | Block protocol over RADOS | Rook/Ceph RBD CSI |
| **CephFS (Ceph File System)** | Ceph project | POSIX file system protocol over RADOS | Rook/Ceph FS CSI |
| **Gluster protocol** | GlusterFS | Distributed file system protocol | Gluster CSI (legacy) |

---

## Control Plane Protocols

> Protocols used by cloud-native control planes to program data planes, distribute configuration, and synchronize state.

| Protocol | Spec / RFC | Description | Projects |
|---|---|---|---|
| **xDS (Discovery Service APIs)** | Envoy / CNCF | gRPC-based: LDS/RDS/CDS/EDS/SDS/ADS | Envoy, Istio, Consul, Contour, Cilium Envoy |
| **xDS Delta (Incremental xDS)** | Envoy spec | Incremental resource updates over bidirectional gRPC | Envoy, Istio 1.5+ |
| **SMI (Service Mesh Interface)** | CNCF | Kubernetes CRD-based mesh config; TrafficSplit/Access | Linkerd, Consul, Osm, Flagger |
| **GWAPI (Gateway API)** | CNCF / k8s-sigs | HTTPRoute/GRPCRoute/TCPRoute CRDs | Contour, Envoy Gateway, Istio, Cilium, NGINX GW |
| **CNI spec (Container Network Interface)** | CNCF | JSON stdin/stdout plugin API; ADD/DEL/CHECK verbs | Calico, Cilium, Flannel, Antrea, Weave, Multus |
| **OVS OpenFlow 1.3+** | ONF | SDN flow table programming | OVS, OVN, Antrea (OVS backend), Ryu |
| **OVSDB** | RFC 7047 | JSON-RPC protocol; OVS database management | OVN, Antrea, Neutron |
| **P4Runtime** | P4.org | P4-programmable switch control API | P4-enabled SmartNICs, Tofino switches |
| **OpenConfig (gNMI/gNOI)** | OpenConfig WG | gRPC-based network management | Stratum, ONOS, network device management |
| **NETCONF** | RFC 6241 | XML-based network config; YANG models | Network device provisioning, OpenDaylight |
| **RESTCONF** | RFC 8040 | REST-ified NETCONF | OpenDaylight, ONOS REST |
| **gNMI (gRPC Network Management Interface)** | OpenConfig | Streaming telemetry + config via gRPC | Stratum, k8s network device operators |
| **gNOI (gRPC Network Operations Interface)** | OpenConfig | Operational commands via gRPC | Stratum, OpenConfig tooling |
| **BGP (as control plane)** | RFC 4271 | Route distribution for pod CIDRs and services | Calico, Cilium BGP CP, MetalLB |
| **Kubernetes API (kube-apiserver)** | k8s spec | REST + Watch (HTTP/2 + JSON/Protobuf) | All k8s controllers, operators, CNIs |
| **Kubernetes Informer Watch** | k8s spec | Long-poll HTTP/2 stream; protobuf events | All k8s controllers |
| **Kubernetes Aggregated API** | k8s spec | Extension API server behind kube-apiserver | Metrics-server, custom API extensions |
| **Admission Webhook (Validating/Mutating)** | k8s spec | HTTPS callback from apiserver to webhook | OPA/Gatekeeper, Kyverno, Istio injection |

---

## Cloud-Native Identity & Policy Protocols

| Protocol | RFC / Spec | Description | Projects |
|---|---|---|---|
| **SPIFFE (Secure Production Identity Framework)** | SPIFFE spec | X.509 SVID + JWT SVID identity standard | SPIRE, Istio SPIFFE, Cilium SPIFFE |
| **SPIRE SVID (X.509)** | SPIFFE spec | X.509 cert with SPIFFE URI SAN | SPIRE, cert-manager SPIFFE, Consul |
| **SPIRE SVID (JWT)** | SPIFFE spec | JWT with sub=spiffe:// claim | SPIRE, OPA JWT policy |
| **OIDC (OpenID Connect)** | OpenID spec | ID token over OAuth2; k8s ServiceAccount OIDC | kube-apiserver OIDC, Dex, Vault, Pinniped |
| **OAuth2** | RFC 6749 | Authorization framework; token delegation | Dex, Hydra, Keycloak on k8s |
| **JWT (JSON Web Token)** | RFC 7519 | Signed claim token | Envoy JWT filter, Istio, kube-apiserver |
| **JWKS (JSON Web Key Set)** | RFC 7517/7518 | Public key set for JWT verification | kube-apiserver OIDC, Istio, Envoy |
| **mTLS client identity** | RFC 8446 | Certificate-based service identity in mTLS | Istio, Linkerd, Consul Connect |
| **Kerberos v5** | RFC 4120 | Ticket-based auth; enterprise/AD integration | k8s LDAP/Kerberos auth webhook (FreeIPA) |
| **LDAP / LDAPS** | RFC 4511 | Directory auth; group lookup | Dex LDAP connector, Keycloak LDAP |
| **SAML 2.0** | OASIS | XML-based SSO assertions | Dex SAML connector, Pinniped |
| **WireGuard key exchange** | Noise protocol | Curve25519 ECDH key exchange | Cilium WireGuard, k3s, Tailscale |
| **IKEv2 (Internet Key Exchange)** | RFC 7296 | IPsec SA negotiation | Calico IPsec, Antrea IPsec, StrongSwan |
| **X.509 Certificate Issuance (ACME)** | RFC 8555 | Automated cert provisioning; Let's Encrypt | cert-manager ACME, Caddy |
| **PKCS#11** | OASIS | HSM/TPM interface for key operations | Vault HSM, cert-manager PKCS11 |
| **TPM 2.0** | TCG spec | Hardware root of trust; attestation | SPIRE TPM plugin, Keylime, Confidential containers |
| **SGX Remote Attestation (ECDSA/EPID)** | Intel | Enclave attestation | Kata Containers, Confidential containers |

---

## Observability Wire Protocols

| Protocol | RFC / Spec | Description | Projects |
|---|---|---|---|
| **OTLP (OpenTelemetry Protocol)** | CNCF OTel | gRPC+Protobuf or HTTP/JSON; traces/metrics/logs | OTel Collector, Jaeger, Tempo, Prometheus |
| **Prometheus Remote Write v1** | Prometheus spec | HTTP POST protobuf; metrics ingestion | Prometheus, Thanos, Cortex, Mimir, VictoriaMetrics |
| **Prometheus Remote Write v2** | Prometheus spec | Snappy-compressed protobuf w/ metadata | Prometheus 2.x+, Alloy |
| **Prometheus Scrape (HTTP)** | Prometheus spec | GET /metrics → text/protobuf exposition format | Prometheus, VictoriaMetrics, Grafana Agent |
| **OpenMetrics** | CNCF | Prometheus exposition v2; standard text format | Prometheus, OpenTelemetry |
| **StatsD** | Etsy / OSS | UDP datagrams; counters/gauges/timers | Telegraf, Datadog agent, Fluentd StatsD |
| **DogStatsD** | Datadog | StatsD + tags extension | Datadog Cluster Agent on k8s |
| **Jaeger Thrift (UDP/HTTP)** | Jaeger spec | Distributed tracing wire format | Jaeger agent (deprecated toward OTLP) |
| **Zipkin B3 / JSON** | OpenZipkin | Trace propagation headers + HTTP API | Zipkin, Istio B3, Envoy B3 propagation |
| **W3C TraceContext** | W3C spec | traceparent/tracestate headers | Envoy, Istio, OTel (default propagator) |
| **W3C Baggage** | W3C spec | baggage header for context propagation | OTel, Envoy |
| **Fluentd Forward Protocol** | Fluentd spec | MessagePack framed log forwarding | Fluentd, Fluent Bit |
| **Fluent Bit Forward** | Fluent Bit spec | Lightweight fluentd-forward variant | Fluent Bit DaemonSet |
| **Loki Push API** | Grafana | HTTP/JSON or Protobuf log push | Promtail, Grafana Agent, Alloy |
| **syslog (UDP/TCP/TLS)** | RFC 5424 | Unix syslog; kernel + container logs | Fluentd syslog input, Vector |
| **eBPF perf ring buffer** | Linux kernel | Kernel-to-user space event transport | Falco, Cilium Hubble, Pixie |
| **eBPF ring buffer (newer)** | Linux kernel | Lock-free replacement for perf buffer | Cilium 1.12+, Falco modern probe |
| **Hubble flow protocol (gRPC)** | Cilium | Network flow export; Hubble Relay API | Cilium Hubble |
| **SNMP v2c/v3** | RFC 3411-3418 | Device metrics; legacy network monitoring | SNMP exporter (Prometheus), NetData |

---

## Protocol × Project Matrix

> ✓ = primary use  · = secondary/optional use

| Protocol | Cilium | Calico | Antrea | Flannel | Istio | Linkerd | Envoy | OVN/OVS | MetalLB | CoreDNS |
|---|---|---|---|---|---|---|---|---|---|---|
| VXLAN | ✓ | ✓ | ✓ | ✓ | · | · | · | ✓ | · | · |
| Geneve | · | · | ✓ | · | · | · | · | ✓ | · | · |
| WireGuard | ✓ | · | · | · | · | ✓ | · | · | · | · |
| IPsec (ESP) | ✓ | ✓ | ✓ | · | · | · | · | · | · | · |
| BGP | ✓ | ✓ | · | · | · | · | · | ✓ | ✓ | · |
| EVPN | · | ✓ | · | · | · | · | · | ✓ | · | · |
| IPv6 / NDP | ✓ | ✓ | ✓ | · | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| eBPF/XDP | ✓ | · | · | · | · | · | · | · | · | · |
| SR-IOV | · | · | · | · | · | · | · | · | · | · |
| mTLS | ✓ | · | · | · | ✓ | ✓ | ✓ | · | · | · |
| SPIFFE/SVID | ✓ | · | · | · | ✓ | ✓ | · | · | · | · |
| xDS (gRPC) | ✓ | · | · | · | ✓ | · | ✓ | · | · | · |
| OpenFlow | · | · | ✓ | · | · | · | · | ✓ | · | · |
| OVSDB | · | · | ✓ | · | · | · | · | ✓ | · | · |
| MACsec | ✓ | · | · | · | · | · | · | ✓ | · | · |
| OTLP | ✓ | · | · | · | ✓ | ✓ | ✓ | · | · | · |
| DNS/UDP+TCP | · | · | · | · | · | · | · | · | · | ✓ |
| Prom Scrape | ✓ | ✓ | ✓ | · | ✓ | ✓ | ✓ | · | ✓ | ✓ |
| gRPC (HTTP/2) | ✓ | ✓ | ✓ | · | ✓ | ✓ | ✓ | ✓ | · | · |
| PROXY proto | · | · | · | · | ✓ | ✓ | ✓ | · | ✓ | · |
| HTTP/3 QUIC | · | · | · | · | · | · | ✓ | · | · | · |
| Gossip/SWIM | ✓ | · | · | · | · | · | · | · | · | · |

---

## Quick OSI Summary Reference

```
┌─────────┬──────────────────────────────────────────────────────────────────────────┐
│ Layer   │ Protocols (abbreviated)                                                   │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L7 App  │ HTTP/1.1/2/3, gRPC, WebSocket, DNS/DoT/DoH, MQTT, AMQP, Kafka,          │
│         │ NATS, S3 API, CSI, etcd/Raft, xDS, Prometheus, OTLP, SPIFFE, OIDC       │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L6 Pres │ TLS 1.2/1.3, mTLS, DTLS, X.509/PKIX, ALPN, SNI, PKCS#11, ASN.1        │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L5 Sess │ TLS handshake, DTLS session, WebSocket upgrade, SOCKS5, H2 streams       │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L4 Xprt │ TCP, UDP, SCTP, QUIC, MPTCP, IPVS, eBPF sockmap, DCCP                  │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L4.5    │ RoCE v1/v2, iWARP, EFA/SRD, NVMe-oF/RDMA, iSCSI, NFS v4.2             │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L3.5    │ VXLAN, Geneve, GRE, NVGRE, WireGuard, IPsec tunnel, GUE, FOU,           │
│         │ LISP, SRv6 encap, STT                                                    │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L3 Net  │ IPv4, IPv6, ICMP, NDP, ARP, BGP, OSPF, IS-IS, ECMP, PIM, IGMP,         │
│         │ MLD, MPLS, SRv6, NAT/SNAT/DNAT, VRF, PBR, DHCP v4/v6                   │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L2 Link │ Ethernet 802.3, VLAN 802.1Q, QinQ, LACP, MACsec 802.1AE,               │
│         │ LLDP, STP/RSTP, EVPN, FC, FCoE                                          │
├─────────┼──────────────────────────────────────────────────────────────────────────┤
│ L1 Phys │ Ethernet media, InfiniBand, SR-IOV/PCIe, DPDK, VPP, XDP/eBPF,          │
│         │ SmartNIC/DPU offload, RDMA HW                                            │
└─────────┴──────────────────────────────────────────────────────────────────────────┘
```

---

## References

```
| Resource | URL |
|---|---|
| CNCF Landscape | https://landscape.cncf.io |
| Cilium Docs | https://docs.cilium.io |
| Calico Docs | https://docs.tigera.io |
| Antrea Docs | https://antrea.io/docs |
| Envoy Proxy | https://www.envoyproxy.io/docs |
| Istio Docs | https://istio.io/latest/docs |
| Linkerd Docs | https://linkerd.io/2.x/overview |
| OVN/OVS | https://www.ovn.org |
| SPIFFE/SPIRE | https://spiffe.io/docs |
| OpenTelemetry | https://opentelemetry.io/docs |
| Kubernetes Networking | https://kubernetes.io/docs/concepts/cluster-administration/networking |
| CNI Spec | https://github.com/containernetworking/cni/blob/main/SPEC.md |
| xDS API | https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol |
| Gateway API | https://gateway-api.sigs.k8s.io |
| SMI Spec | https://smi-spec.io |
| IETF RFC Index | https://www.rfc-editor.org |

```

Complete reference covering **~220+ protocols** across all OSI layers. Here's what's covered:

**Structure:**
- **L1** — Physical/hardware: SR-IOV, DPDK, VPP, XDP/eBPF hooks, SmartNIC/DPU, InfiniBand
- **L2** — Ethernet, 802.1Q/ad/AX/AE/AB, ARP/GARP, MACsec, LLDP, FCoE
- **L3** — Full routing stack: IPv4/6, BGP/MP-BGP, EVPN, OSPF, IS-IS, PIM, IGMP/MLD, SRv6, NAT variants, VRF, ECMP, DHCP
- **L3.5** — All overlay/tunnel protocols: VXLAN, Geneve, GRE, WireGuard, IPsec modes, GUE/FOU, NVGRE, STT, LISP, SRv6 encap
- **L4** — TCP, UDP, SCTP, QUIC, MPTCP, IPVS, eBPF sockmap/cgroup
- **L4.5** — RDMA family: RoCE v1/v2, iWARP, EFA/SRD, NVMe-oF (RDMA+TCP), iSCSI, NFS v4.2
- **L5/L6** — TLS 1.2/1.3, mTLS, DTLS, ALPN, SNI, PKCS#11, X.509/PKIX, TPM/SGX attestation
- **L7** — HTTP family, DNS family (DoT/DoH/DoQ/mDNS/DNSSEC), gRPC, WebSocket, messaging (AMQP/Kafka/MQTT/NATS), storage APIs (S3/CSI/Ceph/NVMe-oF), SSH/SPDY/WS exec
- **Control Plane** — xDS/ADS, CNI spec, OpenFlow, OVSDB, P4Runtime, gNMI/gNOI, NETCONF, Gateway API, SMI
- **Identity/Policy** — SPIFFE/SVID, OIDC, OAuth2, JWT/JWKS, IKEv2, ACME, Kerberos, SAML, Noise/WireGuard key exchange
- **Observability** — OTLP, Prometheus Remote Write v1/v2, OpenMetrics, StatsD, Jaeger Thrift, Zipkin B3, W3C TraceContext, Fluent protocols, Hubble gRPC, syslog, eBPF ring buffers
- **Project × Protocol matrix** for Cilium, Calico, Antrea, Flannel, Istio, Linkerd, Envoy, OVN/OVS, MetalLB, CoreDNS


# Cloud-Native Networking Protocols: L1 → L7
> Complete reference for every protocol handled by cloud-native networking frameworks, stacks, and tools  
> (CNI, eBPF/XDP, service meshes, SDN, overlay networks, control planes, data planes)

---

## Table of Contents

1. [L1 — Physical / Signal Layer](#l1--physical--signal-layer)
2. [L2 — Data Link Layer](#l2--data-link-layer)
3. [L2.5 — Pseudo-Layer (MPLS / Label Switching)](#l25--pseudo-layer-mpls--label-switching)
4. [L3 — Network Layer](#l3--network-layer)
5. [L4 — Transport Layer](#l4--transport-layer)
6. [L4 Overlay / Tunnel Protocols](#l4-overlay--tunnel-protocols)
7. [L5 — Session Layer](#l5--session-layer)
8. [L6 — Presentation / Encryption Layer](#l6--presentation--encryption-layer)
9. [L7 — Application Layer](#l7--application-layer)
10. [Cloud-Native Control-Plane Protocols](#cloud-native-control-plane-protocols)
11. [Hardware-Acceleration & Kernel-Bypass Protocols](#hardware-acceleration--kernel-bypass-protocols)
12. [Protocol Matrix: Tool ↔ Protocol Mapping](#protocol-matrix-tool--protocol-mapping)

---

## L1 — Physical / Signal Layer

Although cloud-native software does not directly manipulate photons or electrons, the physical-layer technologies below define capabilities (bandwidth, latency, SR-IOV pass-through, RDMA) that cloud-native stacks must account for in driver selection, NUMA topology, and IRQ affinity.

---

### 1.1 IEEE 802.3 Ethernet (Physical)

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.3 family |
| Speeds | 1GbE, 10GbE, 25GbE, 40GbE, 100GbE, 400GbE |
| Encoding | PAM-4, NRZ, SerDes |
| Cloud-native relevance | NIC driver selection (mlx5, i40e, ixgbe), DPDK PMD, XDP native mode |

**What it is:**  
The physical signaling standard for wired Ethernet. Defines electrical/optical encoding, auto-negotiation, and the physical medium (copper, DAC, fiber). In cloud data centers, 25GbE/100GbE NICs are the norm; 400GbE is the spine/fabric layer.

**Cloud-native interaction:**  
- `ethtool -i eth0` reveals kernel driver; XDP native mode requires mlx5/i40e/ixgbe.  
- DPDK bypasses the kernel and talks to the NIC PMD (Poll Mode Driver) directly.  
- SR-IOV creates Virtual Functions (VFs) from a single Physical Function (PF); each VF appears as a dedicated NIC inside a VM/container.  
- Kernel NIC queues (RSS/RPS/RFS) map to CPU cores — critical for eBPF/XDP performance tuning.

---

### 1.2 SR-IOV (Single Root I/O Virtualization)

| Attribute | Detail |
|-----------|--------|
| Standard | PCI-SIG SR-IOV spec |
| Relevant tools | Multus CNI, SR-IOV CNI, DPDK, OVS-DPDK |
| Key capability | Hardware-level NIC partitioning into Virtual Functions |

**What it is:**  
SR-IOV is a PCIe hardware standard allowing a single NIC to expose multiple Virtual Functions (VFs) that can be assigned directly to VMs or containers, bypassing the hypervisor/kernel network stack entirely. Each VF has its own PCIe config space, BAR regions, MSI-X interrupt vectors, and TX/RX queues.

**How it works in cloud-native:**  
1. PF driver (e.g., `mlx5_core`) creates N VFs via `echo N > /sys/bus/pci/devices/<PF>/sriov_numvfs`.  
2. VFs are bound to a passthrough driver (`vfio-pci`) for DPDK or to a guest NIC driver.  
3. Kubernetes: SR-IOV Device Plugin allocates VFs to pods; SR-IOV CNI assigns the VF into the pod network namespace.  
4. Hardware switching (NIC eSwitch / embedded switch) handles L2 between VFs without CPU involvement.

**Security considerations:**  
- VF isolation is hardware-enforced but eSwitch firmware vulnerabilities can break isolation.  
- IOMMU (Intel VT-d / AMD-Vi) must be enabled to prevent DMA attacks from rogue VF drivers.  
- MAC/VLAN spoofing protection configurable on PF via `ip link set <PF> vf <N> spoofchk on`.

---

### 1.3 DWDM / Optical Transport

| Attribute | Detail |
|-----------|--------|
| Standard | ITU-T G.694, G.709 |
| Relevance | Inter-DC backbone; cloud provider regional backbones |

**What it is:**  
Dense Wavelength-Division Multiplexing carries multiple 100G+ wavelengths on a single fiber. Cloud providers (AWS, GCP, Azure) own their own DWDM infrastructure for region-to-region links. Relevant for cloud-native networking at the topology/latency planning level (e.g., cross-AZ latency ~1–2ms, cross-region 20–80ms) — these numbers inform timeout, retry, and replication configurations.

---

### 1.4 InfiniBand (Physical)

| Attribute | Detail |
|-----------|--------|
| Standard | IBTA InfiniBand spec |
| Speeds | HDR 200Gb/s, NDR 400Gb/s |
| Relevance | HPC, AI/ML training clusters, RDMA substrate |

**What it is:**  
InfiniBand is a lossless, low-latency interconnect used in HPC and AI/ML clusters. It provides RDMA natively. In cloud-native AI infrastructure (e.g., GPU clusters on EKS, GKE), InfiniBand underlies frameworks like NCCL (NVIDIA Collective Communications Library). Cloud-native networking must account for IB when scheduling RDMA workloads.

---

## L2 — Data Link Layer

The data link layer is the foundational plane for cloud-native overlay networking. The majority of virtual networking (VXLAN, GENEVE, NVGRE) tunnels L2 frames across L3 underlay networks.

---

### 2.1 IEEE 802.3 Ethernet (Data Link)

| Attribute | Detail |
|-----------|--------|
| Frame size | 1518 bytes standard; 9000 bytes jumbo |
| Addressing | 48-bit MAC address |
| Cloud-native tools | Linux bridge, OVS, eBPF/TC, macvlan, ipvlan |

**What it is:**  
The L2 framing format. An Ethernet frame encapsulates upper-layer payloads (IPv4, IPv6, ARP) with a source MAC, destination MAC, EtherType, optional 802.1Q VLAN tag, payload, and FCS.

**Cloud-native relevance:**  
- Linux bridge: software L2 switch; used by Docker bridge mode, Flannel host-gw.  
- OVS (Open vSwitch): programmable software switch; handles L2 learning, VLAN, and tunnel encapsulation.  
- eBPF TC hooks: attach at `tc ingress/egress` to intercept/modify Ethernet frames before the kernel stack.  
- macvlan/ipvlan: create sub-interfaces sharing a physical NIC MAC for direct pod access.  
- Jumbo frames (MTU 9000) reduce CPU overhead for storage/RDMA workloads — MTU misconfiguration is a common cause of PMTUD failures in overlay networks.

---

### 2.2 IEEE 802.1Q — VLAN Tagging

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.1Q-2018 |
| Tag size | 4 bytes (TPID 0x8100 + TCI) |
| VLAN range | 1–4094 |
| Cloud-native tools | OVS, Linux VLAN sub-interfaces, Multus CNI |

**What it is:**  
802.1Q inserts a 4-byte tag into the Ethernet frame to carry a 12-bit VLAN ID, enabling L2 network segmentation on shared physical infrastructure. Access ports strip the tag; trunk ports carry it.

**Cloud-native relevance:**  
- Kubernetes VLAN-based CNIs (e.g., Multus + macvlan + 802.1Q) assign per-tenant VLANs to pod interfaces.  
- OVS maps internal flow tables to VLAN tags for tenant isolation in OpenStack/Neutron-style environments.  
- Bare-metal Kubernetes clusters use 802.1Q trunking to carry multiple tenant VLANs on a single NIC bond.

---

### 2.3 IEEE 802.1ad — QinQ (Double Tagging)

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.1ad (Provider Bridges) |
| Outer TPID | 0x88A8 |
| Use case | ISP metro Ethernet, multi-tenant L2 transport |

**What it is:**  
QinQ stacks two 802.1Q tags: an outer Service VLAN (S-VLAN) added by the provider and an inner Customer VLAN (C-VLAN) from the tenant. Extends the VLAN namespace from 4094 to ~16M combinations.

**Cloud-native relevance:**  
Used in carrier/telco cloud environments and private data center fabrics where multiple tenants each need a full VLAN namespace. OVS supports QinQ encapsulation via flow rules.

---

### 2.4 IEEE 802.1AX — Link Aggregation (LACP)

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.1AX-2014 |
| Protocol | LACP (Link Aggregation Control Protocol) |
| Modes | Active, Passive, Static |
| Linux impl | bonding driver (mode 4 = 802.3ad) |

**What it is:**  
LACP negotiates bundling of multiple physical links into a single logical interface (LAG/bond) for bandwidth aggregation and redundancy. Load balancing is based on a hash (src/dst MAC, IP, port) computed per-frame — this is hardware-level, not round-robin per-packet.

**Cloud-native relevance:**  
- Server uplinks in bare-metal Kubernetes are almost always bonded (2×25GbE → 1×50GbE logical).  
- `bond_mode=4` with `xmit_hash_policy=layer3+4` distributes flows across links.  
- Misconfigured hash policies cause flow imbalance (all flows to one link); critical to verify with `bonding/slave_utilization` metrics.

---

### 2.5 IEEE 802.1AE — MACsec

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.1AE-2018 |
| Encryption | AES-GCM-128/256 |
| Overhead | 32 bytes per frame (tag + ICV) |
| Key mgmt | MKA (MACsec Key Agreement, 802.1X-based) |
| Linux impl | `ip macsec` / `wpa_supplicant` |

**What it is:**  
MACsec provides hop-by-hop authenticated encryption at L2. It encrypts the entire Ethernet payload (everything after the EtherType). Unlike IPsec (L3), MACsec operates before IP, protecting against physical-layer attackers on the same L2 segment.

**Cloud-native relevance:**  
- Used in data-center fabric encryption (switch-to-switch, server-to-TOR) where IPsec overhead is too high.  
- Kubernetes node-to-node MACsec: Multus + MACsec CNI encrypts pod traffic at L2 before it leaves the NIC.  
- Cilium supports WireGuard and IPsec but not native MACsec; OVN has experimental MACsec support.  
- Hardware offload available on mlx5 (ConnectX-5+) and Intel E810 NICs, keeping encryption at line rate.

**Threat model:**  
Protects against: physical tap on inter-rack cabling, rogue device on the same L2 segment.  
Does NOT protect against: compromised switches (MACsec terminates at the switch port), higher-layer attacks.

---

### 2.6 IEEE 802.1D / 802.1w — STP / RSTP

| Attribute | Detail |
|-----------|--------|
| Standard | 802.1D (STP), 802.1w (RSTP), 802.1s (MSTP) |
| Purpose | L2 loop prevention |
| Convergence | STP ~30–50s, RSTP ~1–2s |

**What it is:**  
Spanning Tree Protocol prevents L2 broadcast storms by logically disabling redundant links. RSTP (Rapid STP) converges in ~1s using proposal/agreement mechanism instead of timers.

**Cloud-native relevance:**  
- Modern cloud fabrics use L3-only designs (BGP-based spine-leaf) to eliminate STP entirely.  
- OVS disables STP by default; Linux bridge enables it by default — a common misconfiguration that causes multi-second blackouts when topology changes.  
- `brctl stp <bridge> off` or `ip link set <bridge> type bridge stp_state 0`.

---

### 2.7 IEEE 802.1AB — LLDP

| Attribute | Detail |
|-----------|--------|
| Standard | IEEE 802.1AB-2016 |
| Purpose | Link-layer neighbor discovery |
| Linux impl | `lldpd`, `lldptool` |

**What it is:**  
LLDP advertises device identity, port, VLAN, and capability information to directly connected neighbors. It is the standard replacement for CDP (Cisco proprietary).

**Cloud-native relevance:**  
- Used by SR-IOV and DPDK-based CNIs to discover physical topology for NUMA-aware scheduling.  
- Network operators use LLDP data to build topology maps consumed by SDN controllers (ONOS, OpenDaylight).  
- `lldpd` daemon runs on Kubernetes nodes; LLDP data exposed via node feature discovery.

---

### 2.8 ARP — Address Resolution Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 826 |
| EtherType | 0x0806 |
| Security risk | ARP spoofing, ARP cache poisoning |

**What it is:**  
ARP resolves IPv4 addresses to MAC addresses on a local L2 segment. A host broadcasts "Who has IP X? Tell MAC Y"; the owner replies with its MAC.

**Cloud-native relevance:**  
- In overlay networks (VXLAN/GENEVE), ARP suppression is critical to prevent L2 broadcast storms at scale.  
- OVN/OVS implements ARP proxy: the local OVS instance responds to ARP on behalf of remote endpoints using its distributed control plane MAC/IP table — no broadcast crosses the physical fabric.  
- Cilium's eBPF dataplane intercepts ARP at the `bpf_redirect` level; L3-only mode eliminates ARP entirely by using `/32` host routes.  
- Gratuitous ARP (GARP) is used for virtual IP failover (keepalived, MetalLB).

**Security:**  
ARP has no authentication. Mitigation: Dynamic ARP Inspection (DAI) on switches, eBPF-based ARP filtering, or move to L3-only routing (no ARP).

---

### 2.9 NDP — Neighbor Discovery Protocol (IPv6 ARP equivalent)

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4861, RFC 4862 |
| Transport | ICMPv6 (type 135/136) |
| Functions | Neighbor discovery, router discovery, SLAAC, DAD |

**What it is:**  
NDP replaces ARP for IPv6. It uses ICMPv6 multicast (not broadcast) for:  
- **NS/NA** (Neighbor Solicitation/Advertisement): MAC resolution.  
- **RS/RA** (Router Solicitation/Advertisement): default gateway and prefix discovery.  
- **DAD** (Duplicate Address Detection): verifies IP uniqueness before use.  
- **SLAAC** (Stateless Address Auto-Configuration): derives IPv6 address from RA prefix + interface identifier.

**Cloud-native relevance:**  
- Kubernetes dual-stack (IPv4/IPv6) requires NDP to function correctly in CNI plugins.  
- Cilium handles NDP via eBPF; it responds to NS on behalf of pods using ARP/NDP proxy.  
- RA Guard (switch feature) prevents rogue RA advertisements from redirecting traffic.

---

### 2.10 FCoE — Fibre Channel over Ethernet

| Attribute | Detail |
|-----------|--------|
| Standard | T11 FC-BB-5 / IEEE 802.1Qbb |
| EtherType | 0x8906 |
| Requires | Lossless Ethernet (PFC/DCB) |

**What it is:**  
FCoE encapsulates Fibre Channel frames in Ethernet, eliminating the need for a separate FC HBA. Used in legacy SAN (Storage Area Network) environments.

**Cloud-native relevance:**  
Legacy only. Modern cloud-native storage uses iSCSI, NVMe-oF/TCP, or object storage APIs. FCoE requires Priority Flow Control (PFC / 802.1Qbb) for lossless behavior — this interacts with DCQCN (RDMA congestion control) configurations.

---

## L2.5 — Pseudo-Layer (MPLS / Label Switching)

### 3.1 MPLS — Multiprotocol Label Switching

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 3031, RFC 3032 |
| Label size | 20-bit label, 3-bit TC, 1-bit S, 8-bit TTL |
| EtherType | 0x8847 (unicast), 0x8848 (multicast) |
| Cloud-native tools | FRRouting, BIRD, Cilium (SRv6), Calico BGP |

**What it is:**  
MPLS inserts a 32-bit shim header between L2 and L3. Packets are forwarded based on labels (not IP lookup) through Label Switched Paths (LSPs). Enables Traffic Engineering (MPLS-TE), VPNs (L2/L3 MPLS VPNs), and Fast Reroute (FRR).

**Cloud-native relevance:**  
- Service provider networks (and private DC fabrics) use MPLS for WAN transport.  
- FRRouting (used in Cumulus Linux, SONiC, Calico BGP) supports MPLS/LDP/RSVP.  
- Segment Routing (SR-MPLS and SRv6) is the modern successor — used in cloud-native traffic engineering.  
- AWS uses MPLS internally on their backbone; users don't interact with it directly.

---

### 3.2 Segment Routing (SR-MPLS / SRv6)

| Attribute | Detail |
|-----------|--------|
| RFCs | RFC 8402 (SR arch), RFC 8660 (SR-MPLS), RFC 8986 (SRv6) |
| SR-MPLS | Uses MPLS label stack as segment list |
| SRv6 | Uses IPv6 Segment Routing Header (SRH) |
| Cloud-native tools | Cilium (SRv6 dataplane), FRRouting, Linux kernel 5.14+ |

**What it is:**  
Segment Routing encodes an explicit path through the network as an ordered list of "segments" (SIDs) in the packet header itself — no per-flow state on transit nodes (unlike RSVP-TE). SR-MPLS uses label stacks; SRv6 uses a new IPv6 extension header.

**SRv6 functions (SRv6 Network Programming):**  
- `End` — endpoint; process packet as per routing table  
- `End.DX4` — decap and forward to an IPv4 next-hop  
- `End.DT4/6` — decap and lookup in VPN routing table  
- `H.Encaps` — encapsulate with SRH at ingress  

**Cloud-native relevance:**  
- Cilium 1.12+ implements SRv6 L3VPN dataplane using eBPF — pods can be reachable via SRv6 SIDs across provider networks without overlay tunnels.  
- SRv6 replaces MPLS/LDP complexity with a routable, scriptable, IPv6-native mechanism.  
- FRRouting BGP-SR distributes SID mappings to all nodes.

---

## L3 — Network Layer

---

### 4.1 IPv4

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 791 |
| Address space | 32-bit (4.3B addresses) |
| Header size | 20 bytes minimum |
| Fragmentation | Supported (discouraged; use PMTUD) |

**What it is:**  
IPv4 provides connectionless, best-effort datagram delivery. Each packet carries source/destination 32-bit addresses, a TTL (hop limit), protocol field, and header checksum.

**Cloud-native relevance:**  
- All container networking is IPv4-primary; Kubernetes pods get RFC1918 addresses from the PodCIDR.  
- IPv4 address exhaustion drove NAT proliferation; cloud-native tries to minimize NAT (direct routing via BGP or SR).  
- IPv4 fragmentation is a security risk (fragment overlap attacks); MTU discipline and PMTUD Black Hole detection are critical.  
- `ip route`, `ip rule` (policy routing), and eBPF maps are the primary manipulation surfaces.

---

### 4.2 IPv6

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 8200 |
| Address space | 128-bit |
| Header size | 40 bytes fixed |
| Extension headers | Hop-by-hop, routing (SRH), fragment, ESP, auth |
| Flow Label | 20-bit; used for ECMP hashing |

**What it is:**  
IPv6 provides a 128-bit address space, mandatory IPsec support (originally; now optional in practice), stateless auto-configuration (SLAAC), and a cleaner extension header mechanism replacing IPv4 options.

**Cloud-native relevance:**  
- Kubernetes dual-stack (KEP-563) assigns both IPv4 and IPv6 addresses to pods and services.  
- Cilium's native IPv6 routing eliminates NAT entirely — each pod is globally routable.  
- SRv6 depends on IPv6.  
- IPv6 ECMP uses the Flow Label field for consistent hashing — configure with `sysctl net.ipv6.auto_flowlabels=1`.  
- GKE/EKS/AKS all support dual-stack; IPv6-only clusters are emerging.

---

### 4.3 ICMPv4 / ICMPv6

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 792 (ICMPv4), RFC 4443 (ICMPv6) |
| Protocol | IP protocol 1 (v4), IPv6 Next Header 58 (v6) |
| Critical types | Echo (ping), Dest Unreachable, TTL Exceeded, PMTUD (type 3/code 4) |

**What it is:**  
ICMP carries control messages: reachability (ping), error reporting (port unreachable, TTL exceeded), and Path MTU Discovery (PMTUD — "Fragmentation Needed" type 3 code 4).

**Cloud-native relevance:**  
- PMTUD is critical in overlay networks (VXLAN adds 50+ bytes overhead). Blocking ICMP type 3/code 4 causes silent MTU black holes — a very common misconfiguration.  
- Cilium and Calico implement PMTUD handling in eBPF.  
- ICMPv6 is integral to IPv6 (NDP, MLD, SLAAC) and must NEVER be blocked entirely in IPv6 networks.  
- `ping`, `traceroute` (ICMP/UDP/TCP modes), and MTU probing rely on ICMP.

---

### 4.4 BGP — Border Gateway Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4271 (BGP-4), RFC 7938 (BGP in DC) |
| Transport | TCP port 179 |
| Types | eBGP (between ASes), iBGP (within AS) |
| Cloud-native tools | Calico BGP, Cilium BGP (GoBGP), FRRouting, BIRD |
| Address families | IPv4 unicast, IPv6 unicast, L2VPN EVPN (RFC 7432) |

**What it is:**  
BGP is the Internet's inter-domain routing protocol. In cloud-native networking, eBGP is used as the underlay routing protocol in spine-leaf fabrics (RFC 7938 "BGP in the Data Center") and as the overlay control plane for EVPN (MAC/IP route distribution for VXLAN).

**Cloud-native usage patterns:**

1. **Calico BGP mode** — each Kubernetes node runs a BGP speaker (BIRD/GoBGP) and advertises pod CIDRs as /26 or /32 host routes directly into the fabric. No overlay, no encapsulation. Requires BGP-capable ToR switches or a route reflector.

2. **MetalLB** — uses BGP to advertise LoadBalancer Service IPs from Kubernetes nodes to upstream routers.

3. **Cilium BGP Control Plane (v1.13+)** — GoBGP embedded in Cilium, advertises pod/service CIDRs. `CiliumBGPPeeringPolicy` CRD configures peers.

4. **EVPN/VXLAN control plane** — BGP EVPN (address family L2VPN EVPN, type-2/type-5 routes) distributes MAC/IP bindings and prefix routes, replacing flood-and-learn. Used in OVN, Cumulus, SONiC.

**Key BGP attributes in cloud-native:**  
- `NO_EXPORT` community: prevent pod routes from leaking to Internet.  
- `LOCAL_PREF`: prefer direct node routes over overlay paths.  
- BFD (see below) provides fast failure detection for BGP sessions.  
- ECMP with BGP: `maximum-paths` allows multipath to load-balance across multiple uplinks.

**Security:**  
- BGP MD5 authentication (RFC 2385) or TCP-AO (RFC 5925) for session protection.  
- RPKI/ROA (Resource Public Key Infrastructure) validates BGP origin AS.  
- Prefix filtering: never accept /32 or default route from peers without explicit policy.

---

### 4.5 OSPF — Open Shortest Path First

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2328 (OSPFv2 IPv4), RFC 5340 (OSPFv3 IPv6) |
| Protocol | IP protocol 89 |
| Algorithm | Dijkstra SPF on LSDB |
| Cloud-native tools | FRRouting, BIRD |

**What it is:**  
OSPF is a link-state IGP (Interior Gateway Protocol). Each router floods Link State Advertisements (LSAs) to build a complete topology map (LSDB) and runs Dijkstra to compute shortest paths. Converges faster than BGP for intra-AS topology changes.

**Cloud-native relevance:**  
- Used in private data centers alongside or instead of BGP for underlay routing.  
- FRRouting OSPF runs on Cumulus Linux/SONiC switches as well as Linux servers (e.g., Calico with OSPF underlay).  
- Less common than BGP in modern cloud-native DC designs due to BGP's superior policy control and simpler eBGP unnumbered configuration.

---

### 4.6 IS-IS — Intermediate System to Intermediate System

| Attribute | Detail |
|-----------|--------|
| Standard | ISO 10589, RFC 1195 (IP support) |
| Transport | Runs directly over L2 (not IP) |
| Cloud-native tools | FRRouting, large provider fabrics |

**What it is:**  
IS-IS is a link-state IGP similar to OSPF but runs directly over L2 (not encapsulated in IP). It is the preferred IGP for large-scale fabrics (Google, Facebook/Meta backbone) because it avoids IP bootstrapping issues and scales to larger topologies.

**Cloud-native relevance:**  
- Used by Google's Jupiter fabric and similar hyperscaler underlay networks.  
- FRRouting supports IS-IS; can be used in SONiC-based fabrics.  
- Segment Routing with IS-IS (SR-IS-IS) is a modern combination for traffic engineering without RSVP.

---

### 4.7 BFD — Bidirectional Forwarding Detection

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 5880, RFC 5881 |
| Transport | UDP port 3784 (single-hop), 4784 (multi-hop) |
| Timers | Hello interval as low as 50ms |
| Cloud-native tools | FRRouting, Calico, Cilium BGP |

**What it is:**  
BFD is a lightweight hello protocol that detects forwarding path failures in milliseconds — far faster than BGP hold timers (default 90s) or OSPF dead timers (40s). BFD sessions run between BGP/OSPF neighbors; failure triggers immediate routing protocol convergence.

**Cloud-native relevance:**  
- Calico BGP + BFD: node failure detected in 300ms–1s vs 90s without BFD.  
- MetalLB + BFD: VIP failover in sub-second time.  
- FRRouting BFD daemon (`bfdd`) integrates with `bgpd`, `ospfd`, `isisd`.

---

### 4.8 ECMP — Equal-Cost Multi-Path

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2991, RFC 2992 |
| Kernel impl | Linux `ip route` multipath, `net.ipv4.fib_multipath_hash_policy` |
| Hash inputs | Src/Dst IP, Src/Dst port, Protocol (5-tuple) |

**What it is:**  
ECMP allows a router to install multiple equal-cost next hops for a destination and distribute traffic across them. This is the primary horizontal scaling mechanism for cloud-native services.

**Cloud-native relevance:**  
- Kubernetes Service load balancing in Calico BGP mode uses ECMP across all node IPs advertising the ClusterIP.  
- Cilium XDP-based load balancing uses Maglev consistent hashing (a form of ECMP) for connection-level affinity.  
- Linux ECMP hash policy: `sysctl net.ipv4.fib_multipath_hash_policy=1` (L4 hash, avoids polarization).  
- Hash polarization (all flows to one path) is a common failure mode — mitigation: use L3+L4 hash, or flow-aware ECMP.

---

### 4.9 PBR — Policy-Based Routing

| Attribute | Detail |
|-----------|--------|
| Linux impl | `ip rule`, `ip route table` |
| Used by | Cilium (eBPF redirect), OVS, VRF |

**What it is:**  
PBR routes packets based on criteria other than destination IP (e.g., source IP, DSCP, mark). In Linux, implemented via routing policy rules (`ip rule`) and multiple routing tables.

**Cloud-native relevance:**  
- Cilium uses PBR (`ip rule add fwmark X table Y`) to route pod-originated traffic through eBPF programs.  
- Istio (iptables mode) marks packets and uses PBR to redirect to Envoy.  
- VRF (Virtual Routing and Forwarding) — Linux VRF devices create isolated routing tables per tenant, used in multi-tenant Kubernetes deployments.

---

### 4.10 IPIP — IP-in-IP Tunneling

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2003 |
| Protocol | IP protocol 4 |
| Overhead | 20 bytes (IP header) |
| Cloud-native tools | Calico, Flannel (host-gw fallback) |

**What it is:**  
IPIP encapsulates an inner IP packet inside an outer IP packet. Minimal overhead (20 bytes). No encryption. Used to carry pod IP traffic across a routed underlay that doesn't know pod CIDRs.

**Cloud-native relevance:**  
- Calico IPIP mode: when nodes are on different L2 segments (different subnets), Calico wraps pod packets in IPIP tunnels. Simpler than VXLAN, no UDP overhead.  
- Flannel vxlan/host-gw falls back to IPIP/UDP in some configurations.  
- `ip tunnel add tunl0 mode ipip` creates the tunnel device; Calico manages this automatically.

---

### 4.11 SIT — Simple Internet Transition (IPv6-in-IPv4)

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4213 |
| Protocol | IP protocol 41 |
| Purpose | Tunnel IPv6 over IPv4 underlay |

**What it is:**  
SIT tunnels carry IPv6 packets inside IPv4 headers (protocol 41). Used during IPv6 transition when the underlay is still IPv4-only.

**Cloud-native relevance:**  
- Kubernetes dual-stack with IPv4-only underlay uses SIT-style tunnels.  
- Calico dual-stack: can use IPIP for IPv4 pods and SIT for IPv6 pods on IPv4 underlay.

---

### 4.12 GRE — Generic Routing Encapsulation

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2784, RFC 2890 |
| Protocol | IP protocol 47 |
| Features | Key field, sequence number, checksum |
| Overhead | 24 bytes |

**What it is:**  
GRE encapsulates any L3 protocol (IPv4, IPv6, MPLS) inside a GRE header, then inside an outer IP header. The optional Key field enables multiplexing multiple logical tunnels over one GRE endpoint.

**Cloud-native relevance:**  
- OVS uses GRE tunnels between compute nodes (alongside VXLAN/GENEVE); used in OpenStack Neutron deployments.  
- Kubernetes network policies can be applied at GRE tunnel decap points via OVS flow rules.  
- GRE has no native encryption; combine with IPsec (GRE-over-IPsec) or use WireGuard/VXLAN+TLS instead.

---

## L4 — Transport Layer

---

### 5.1 TCP — Transmission Control Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9293 (updated) |
| Features | Reliable, ordered, flow-controlled, congestion-controlled |
| Port range | 0–65535 |
| Cloud-native relevance | gRPC, HTTP/1.1, HTTP/2, etcd, Kubernetes API server |

**What it is:**  
TCP provides reliable, in-order, byte-stream delivery with flow control (sliding window) and congestion control (CUBIC, BBR). The three-way handshake establishes connection state; FIN/RST tears it down.

**Cloud-native relevance:**  
- Kubernetes API server, etcd, Prometheus remote write — all TCP.  
- TCP connection overhead (SYN latency) is a bottleneck for short-lived microservice calls → use HTTP/2 (multiplexing) or QUIC.  
- TCP BBR congestion control (`sysctl net.ipv4.tcp_congestion_control=bbr`) significantly improves throughput in high-BDP or lossy environments.  
- `SO_REUSEPORT` allows multiple threads/processes to accept on the same port without thundering-herd — used by Envoy, NGINX, Cilium.  
- TCP Fast Open (TFO, RFC 7413) reduces 1-RTT for repeat connections — supported in Go's net package.  
- eBPF sockops programs (`BPF_PROG_TYPE_SOCK_OPS`) can accelerate TCP: override congestion control, set socket options, implement connection-level load balancing.

---

### 5.2 UDP — User Datagram Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 768 |
| Features | Connectionless, no reliability, no ordering |
| Cloud-native relevance | DNS, VXLAN, GENEVE, QUIC, syslog, NTP, DTLS, WireGuard |

**What it is:**  
UDP provides minimal framing with source port, destination port, length, and checksum. No connection setup, no retransmission. Used where latency matters more than reliability or where the application implements its own reliability (QUIC).

**Cloud-native relevance:**  
- VXLAN (UDP 4789), GENEVE (UDP 6081), WireGuard (UDP 51820), QUIC (UDP 443) — virtually all overlay protocols use UDP.  
- DNS (UDP 53): every pod DNS query goes through CoreDNS via UDP; high DNS query rates are a common scalability issue in Kubernetes.  
- UDP checksum offload (USC) and UDP Segmentation Offload (USO) critical for VXLAN/GENEVE performance.  
- `SO_RCVBUF`/`SO_SNDBUF` tuning for UDP-based overlay performance.

---

### 5.3 SCTP — Stream Control Transmission Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9260 |
| Features | Multi-homing, multi-streaming, message-oriented |
| Cloud-native relevance | 5G core network functions (N1/N2/N3/N4 interfaces) |

**What it is:**  
SCTP combines TCP reliability with message-orientation and multi-homing (a single SCTP association can span multiple IP addresses for failover). Used extensively in telecom signaling (SS7/SIGTRAN over IP) and 5G core (NGAP uses SCTP).

**Cloud-native relevance:**  
- Kubernetes SCTP support (beta, KEP-1591): Services and NetworkPolicies support SCTP protocol field.  
- Telco/CNF (Cloud-Native Network Functions) on Kubernetes: 5G AMF/SMF/UPF use SCTP for NGAP and PFCP.  
- Multus CNI with SR-IOV often required for SCTP performance in 5G CNFs.

---

### 5.4 QUIC

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9000 (QUIC), RFC 9001 (QUIC+TLS 1.3) |
| Transport | UDP (any port; typically 443) |
| Features | 0-RTT, multiplexed streams, connection migration, built-in TLS 1.3 |
| Cloud-native tools | Envoy QUIC, gRPC QUIC, Caddy, Nginx QUIC |

**What it is:**  
QUIC is a new transport protocol that runs over UDP and subsumes TLS 1.3, HTTP/2 stream multiplexing, and connection migration. It eliminates head-of-line blocking at the transport layer (a TCP limitation for HTTP/2), provides 0-RTT connection resumption, and allows connection migration (IP change without reconnect — useful for mobile clients).

**QUIC internals:**  
- Packet number space per encryption level (Initial, Handshake, 1-RTT)  
- Connection IDs (not 4-tuple) identify connections → survives IP change  
- CRYPTO frames carry TLS handshake (not TCP TLS record layer)  
- STREAM frames carry application data with per-stream flow control  
- ACK frames: ranges with delay; no SACKs needed  
- DATAGRAM frames (RFC 9221): unreliable delivery within QUIC connections  

**Cloud-native relevance:**  
- HTTP/3 (RFC 9114) runs over QUIC — all major CDNs and cloud providers support it.  
- Envoy proxy supports QUIC upstream/downstream.  
- gRPC over QUIC: gRPC-core has experimental QUIC transport.  
- Service mesh: Istio/Envoy QUIC mode for frontend traffic.  
- MASQUE (RFC 9298): HTTP/3 tunneling for VPN-like connectivity — used in iCloud Private Relay.

---

### 5.5 DCCP — Datagram Congestion Control Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4340 |
| Use case | Real-time media with congestion control but no reliability |
| Status | Niche; rarely used in cloud-native |

**What it is:**  
DCCP adds congestion control to UDP-style datagram flows without reliability. Designed for streaming media. Largely superseded by QUIC's DATAGRAM extension.

---

## L4 Overlay / Tunnel Protocols

These protocols operate at L4 (UDP/IP encapsulation) but create virtual L2 or L3 networks — the foundation of all cloud-native multi-tenant networking.

---

### 6.1 VXLAN — Virtual eXtensible LAN

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 7348 |
| Encapsulation | UDP/IP (dst port 4789) |
| Overhead | 50 bytes (8 VXLAN + 8 UDP + 20 IP + 14 Eth outer) |
| VXLAN ID | 24-bit VNI (16M virtual networks) |
| Control plane | Flood-and-learn (basic) or BGP EVPN (production) |
| Cloud-native tools | Flannel, Calico VXLAN, Cilium, OVN/OVS, Weave |

**What it is:**  
VXLAN tunnels L2 Ethernet frames over a UDP/IP underlay. A VTEP (VXLAN Tunnel Endpoint — the OVS port, Linux vxlan device, or eBPF program on each node) encapsulates outgoing frames with outer Ethernet+IP+UDP+VXLAN headers. The 24-bit VNI identifies the virtual L2 segment, enabling tenant isolation.

**Packet walk through Cilium VXLAN mode:**
```
Pod TX
  → veth pair (container netns → host netns)
  → eBPF tc ingress program (policy check, load balance, NAT)
  → VXLAN encap: inner Eth/IP/TCP + outer UDP:4789 + VNI
  → Physical NIC TX
  → Underlay IP routing
  → Remote node UDP:4789
  → VXLAN decap
  → eBPF tc egress on remote veth
  → Pod RX
```

**Control plane options:**
- **Flood-and-learn**: VTEP floods to all VTEPs on unknown MAC → BUM (Broadcast, Unknown, Multicast) traffic. Does not scale beyond ~100 nodes.  
- **BGP EVPN**: Type-2 routes (MAC/IP) and Type-3 routes (VTEP membership) distributed via BGP; ARP suppression; no flooding. Scales to thousands of VTEPs.  
- **Static/FDB-based** (Flannel): Flannel controller writes static FDB entries (`bridge fdb add <MAC> dev vxlan0 dst <remote-IP>`) — scales but has convergence delay.

**MTU considerations:**  
Physical MTU 1500 → VXLAN overhead 50 bytes → inner MTU must be ≤ 1450. Configure pod MTU explicitly (Flannel: `--iface-mtu 1450`; Cilium: auto-detects with BPF PMTUD).

**Security:**  
VXLAN has no authentication or encryption. Attackers on the same underlay can inject VXLAN packets. Mitigations:  
- Restrict UDP 4789 to trusted node CIDRs via host firewall.  
- Use Cilium's WireGuard encryption layer over VXLAN.  
- Validate VNI at decap point.

---

### 6.2 GENEVE — Generic Network Virtualization Encapsulation

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 8926 |
| Encapsulation | UDP/IP (dst port 6081) |
| Key feature | Variable-length TLV options in GENEVE header |
| Overhead | 30+ bytes (base) |
| Cloud-native tools | OVN/OVS (primary tunnel type), Cilium |

**What it is:**  
GENEVE extends VXLAN with a flexible TLV option space in the tunnel header, allowing metadata (security labels, policy IDs, tracing context) to be carried per-packet without touching the inner payload. This is the tunnel format preferred by OVN (Open Virtual Network) and modern OVS deployments.

**GENEVE vs VXLAN:**
- Same UDP/IP encapsulation model  
- GENEVE adds a variable header (options) between the fixed header and inner Ethernet  
- OVN uses GENEVE by default for carrying inport/outport/logical network metadata in option fields  
- Hardware offload support (mlx5, i40e) available for GENEVE

**Cloud-native relevance:**  
- OVN is the default network backend for OpenStack, oVirt, and Kubernetes with OVN-Kubernetes CNI.  
- OVN-Kubernetes uses GENEVE with a custom option (TLV type 1) to carry the logical port/policy tags.  
- Cilium supports GENEVE as an alternative to VXLAN.

---

### 6.3 NVGRE — Network Virtualization using GRE

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 7637 |
| Encapsulation | GRE (IP protocol 47) |
| VSID | 24-bit Virtual Subnet Identifier |
| Cloud-native tools | Hyper-V, Azure virtual networking |

**What it is:**  
NVGRE is Microsoft's alternative to VXLAN, using GRE as the encapsulation rather than UDP. The 24-bit VSID plays the same role as VXLAN VNI. Azure's virtual network implementation historically used NVGRE; it is less common in Linux-based cloud-native stacks.

**Cloud-native relevance:**  
- Windows Server / Hyper-V containers use NVGRE for network virtualization.  
- Azure hybrid networking: Azure Stack HCI uses NVGRE internally.  
- Linux CNI plugins on Windows nodes in Kubernetes may encounter NVGRE from the Windows CNI (Host Networking Service).

---

### 6.4 STT — Stateless Transport Tunneling

| Attribute | Detail |
|-----------|--------|
| Draft | draft-davie-stt |
| Encapsulation | TCP-like header over IP (not actual TCP) |
| Purpose | Exploit TSO (TCP Segmentation Offload) for tunnel performance |

**What it is:**  
STT uses a TCP-like framing (to exploit NIC TCP Segmentation Offload hardware) to tunnel L2 frames without actually using TCP's reliability or state. It predates VXLAN/GENEVE offload support. Now largely replaced by hardware-offloaded VXLAN/GENEVE.

**Cloud-native relevance:**  
- Used historically in early OVS versions. VMware NSX used STT.  
- Effectively obsolete in modern deployments. Mentioned for completeness and legacy system awareness.

---

### 6.5 WireGuard

| Attribute | Detail |
|-----------|--------|
| RFC | Whitepaper + Linux RFC (merged kernel 5.6) |
| Encapsulation | UDP (configurable port, default 51820) |
| Crypto | Curve25519 (ECDH), ChaCha20-Poly1305, BLAKE2s, SipHash24 |
| Key exchange | Noise_IKpsk2 protocol (1-RTT handshake) |
| Cloud-native tools | Cilium WireGuard mode, Calico WireGuard, Flannel |

**What it is:**  
WireGuard is a modern, minimal, high-performance VPN tunnel built into the Linux kernel. It uses state-of-the-art cryptography with a vastly simpler codebase (~4000 LoC vs ~400K for IPsec/OpenVPN). Peers are identified by Curve25519 public keys; routing is based on allowed-IPs.

**WireGuard cryptokey routing:**
```
Peer A pubkey → allowed-IPs: 10.0.0.0/8
Peer B pubkey → allowed-IPs: 192.168.1.0/24
```
Packets sent to 10.x.x.x are encrypted with Peer A's key and sent to Peer A's endpoint.

**Cloud-native usage in Cilium:**  
- `cilium install --set encryption.enabled=true --set encryption.type=wireguard`  
- Cilium creates a WireGuard interface per node; automatically manages key distribution via CiliumNode CRD.  
- Per-node WireGuard tunnel encrypts all pod-to-pod traffic traversing node boundaries.  
- Kernel WireGuard provides ~10Gbps throughput on modern CPUs; user-space BoringTun provides fallback.

**Calico WireGuard:**  
- `calicoctl patch felixconfiguration default --patch '{"spec":{"wireguardEnabled":true}}'`  
- Felix manages WireGuard key rotation and peer configuration.

**Security:**  
- Forward secrecy: ephemeral keys per session (Noise handshake).  
- No negotiation → no downgrade attacks.  
- Replay protection: sliding window of 2000 packet IDs.  
- Identity: public key IS the identity — no PKI hierarchy needed.

---

### 6.6 IPsec (ESP / AH)

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4301 (architecture), RFC 4303 (ESP), RFC 4302 (AH) |
| Modes | Transport (L4+), Tunnel (full IP encap) |
| Key exchange | IKEv2 (RFC 7296) |
| Crypto (ESP) | AES-GCM-128/256, ChaCha20-Poly1305 |
| Cloud-native tools | Cilium IPsec, StrongSwan, Libreswan, Calico IPsec |
| Overhead | ESP tunnel ~50–60 bytes |

**What it is:**  
IPsec is the IETF standard for network-layer encryption and authentication. **ESP (Encapsulating Security Payload)** provides confidentiality + integrity; **AH (Authentication Header)** provides integrity only (no encryption; largely unused). IKEv2 handles key exchange, authentication (certificates or PSK), and SA (Security Association) negotiation.

**ESP packet structure (tunnel mode):**
```
[Outer IP][ESP Header (SPI + Seq)][IV][Encrypted: Inner IP + Payload][ESP Trailer][ICV]
```

**Cloud-native usage:**  
- Cilium IPsec mode: `--set encryption.enabled=true --set encryption.type=ipsec` — uses Linux xfrm subsystem; Cilium operator manages key rotation via Kubernetes Secret.  
- Calico IPsec: Felix configures xfrm policies for pod-to-pod encryption.  
- AWS VPC: customer-gateway IPsec VPNs use IKEv2/ESP for Site-to-Site VPN.  
- Azure VPN Gateway, GCP Cloud VPN — all IPsec IKEv2.

**IPsec vs WireGuard (cloud-native decision):**

| Factor | IPsec | WireGuard |
|--------|-------|-----------|
| Standards | IETF RFC | Whitepaper |
| Complexity | High (IKEv2, XFRM, policy DB) | Low |
| Performance | xfrm with crypto offload | Kernel module; good |
| FIPS 140-2 | Yes (with validated implementations) | Not yet |
| Hardware offload | Intel QuickAssist, mlx5 | Limited |
| Key rotation | IKEv2 rekey | Manual or automation |

---

### 6.7 VXLAN-GPE — VXLAN with Generic Protocol Extension

| Attribute | Detail |
|-----------|--------|
| Draft | draft-ietf-nvo3-vxlan-gpe |
| Extension | Adds Next Protocol field to VXLAN header |
| Protocols carried | NSH, IPv4, IPv6, Ethernet, TLS |

**What it is:**  
VXLAN-GPE extends VXLAN to carry non-Ethernet payloads. The critical use case: carrying **NSH (Network Service Header, RFC 8300)** for Service Function Chaining (SFC). NSH carries metadata (tenant, SPI/SI service path/index) through a chain of network functions.

**Cloud-native relevance:**  
- OVS + Cilium SFC: chain DPI → firewall → load balancer using NSH over VXLAN-GPE.  
- Ligato/VPP-based CNF deployments for telco use VXLAN-GPE+NSH for 5G UPF service chains.

---

## L5 — Session Layer

The session layer is thin in modern Internet protocols. TLS session management and the kernel socket layer are the primary cloud-native concerns.

---

### 7.1 TLS Session Resumption

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 8446 §2.2 (TLS 1.3 PSK), RFC 5077 (TLS 1.2 session tickets) |
| Mechanism | PSK (Pre-Shared Key) identity, session ticket |

**What it is:**  
TLS 1.3 session resumption uses a PSK identity derived from a previous session's master secret. The client offers the PSK in a new ClientHello, allowing 0-RTT or 1-RTT resumption without a full handshake.

**Cloud-native relevance:**  
- 0-RTT (Early Data) enables microservices to resume TLS without a round trip — but is vulnerable to replay attacks. Envoy disables 0-RTT by default.  
- Session tickets must be rotated frequently; in distributed deployments (multiple Envoy instances) all instances must share the same ticket key — managed via Kubernetes Secret.

---

### 7.2 SPIFFE — Secure Production Identity Framework

| Attribute | Detail |
|-----------|--------|
| Spec | SPIFFE (spiffe.io), CNCF project |
| Identity format | SPIFFE ID: `spiffe://<trust-domain>/<path>` |
| Transport | SVID (X.509 or JWT) over gRPC (Workload API) |
| Implementation | SPIRE, Istio Citadel, Linkerd |

**What it is:**  
SPIFFE defines a framework for workload identity in dynamic cloud-native environments. Instead of managing TLS certificates manually, SPIFFE-compliant systems automatically issue short-lived X.509 SVIDs (SPIFFE Verifiable Identity Documents) to workloads. This forms the foundation for mTLS between services.

**SPIFFE/SPIRE architecture:**
```
SPIRE Server (CA)
  ├── Attestation: node attestation (TPM, AWS IID, k8s SA token)
  └── SVID issuance → X.509 cert with SPIFFE ID SAN

SPIRE Agent (per node)
  ├── Workload attestation (pid, UID, k8s pod labels)
  └── Workload API (Unix socket) → delivers SVID to workload
```

**Cloud-native relevance:**  
- Istio uses SPIFFE SVIDs for all service-to-service mTLS — `spiffe://cluster.local/ns/default/sa/frontend`.  
- Cilium mTLS: experimental integration with SPIRE for eBPF-enforced mTLS.  
- SPIFFE Federation: cross-cluster, cross-cloud identity federation without shared CA.

---

## L6 — Presentation / Encryption Layer

---

### 8.1 TLS 1.3

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 8446 |
| Handshake RTT | 1-RTT (0-RTT for resumption) |
| Key exchange | ECDHE (X25519, P-256, P-384) |
| AEAD ciphers | AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305 |
| Removed | RSA key exchange, RC4, CBC, compression, renegotiation |
| Cloud-native tools | Envoy, Nginx, Go TLS, BoringSSL |

**What it is:**  
TLS 1.3 is the current standard for transport security. The handshake is redesigned: ServerHello immediately carries the key share and encrypted extensions. The server's certificate is sent encrypted. The entire handshake completes in 1 RTT (vs 2 RTT for TLS 1.2). Perfect Forward Secrecy is mandatory (ECDHE only; RSA static key exchange removed).

**TLS 1.3 handshake:**
```
Client → ServerHello + KeyShare + SupportedVersions
Client ← ServerHello + KeyShare + EncryptedExtensions + Certificate + CertVerify + Finished
Client → Finished
(Application data can begin after server Finished; or 0-RTT before)
```

**Cloud-native relevance:**  
- All Kubernetes API server, etcd, Prometheus, and service mesh traffic should use TLS 1.3.  
- Envoy: `tls_minimum_protocol_version: TLSv1_3` in DownstreamTlsContext.  
- Go 1.18+: TLS 1.3 is default and preferred; crypto/tls.Config.MinVersion.  
- BoringSSL (used in Envoy/Chromium): FIPS-validated build available — required for compliance workloads.  
- Certificate rotation: Cert-Manager + SPIRE for automated short-lived cert renewal.

---

### 8.2 mTLS — Mutual TLS

| Attribute | Detail |
|-----------|--------|
| Base | TLS 1.3 with client certificate authentication |
| Identity | X.509 certificate with SPIFFE SAN |
| Cloud-native tools | Istio, Linkerd, Cilium, Consul Connect |

**What it is:**  
mTLS extends TLS to require the client to present a certificate (in addition to the server). Both sides authenticate each other cryptographically. This is the standard authentication mechanism for zero-trust service-to-service communication.

**mTLS in Istio (sidecar model):**
```
App Pod                    Envoy Sidecar              Envoy Sidecar               App Pod
[Service A] →plain HTTP→ [Envoy A] →mTLS TLS1.3→ [Envoy B] →plain HTTP→ [Service B]
             iptables                SPIFFE SVID                iptables
             redirect                cert verify                redirect
```

**mTLS in Cilium (eBPF model — no sidecar):**  
- Cilium 1.14+: eBPF enforces mTLS policy at the socket level using SPIFFE SVIDs fetched from SPIRE agent.  
- Eliminates the sidecar overhead (~3ms latency, ~10% CPU per hop).

---

### 8.3 DTLS — Datagram TLS

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9147 (DTLS 1.3) |
| Transport | UDP |
| Use case | UDP-based applications needing TLS-equivalent security |
| Cloud-native tools | WebRTC, RADIUS over DTLS, COAP |

**What it is:**  
DTLS adapts TLS for UDP, adding message loss handling, reordering, and replay protection. Used wherever UDP is required but security is needed (WebRTC SRTP key exchange, IoT CoAP over DTLS).

**Cloud-native relevance:**  
- Kubernetes edge/IoT platforms: DTLS for device-to-cloud MQTT/CoAP.  
- WebRTC gateways in Kubernetes: DTLS-SRTP handshake.  
- RADIUS over DTLS (RFC 7360): network device authentication in cloud-native AAA stacks.

---

## L7 — Application Layer

---

### 9.1 HTTP/1.1

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9112 |
| Features | Pipelining (buggy), Keep-Alive, Host header, chunked encoding |
| Connection | 1 request/response per TCP connection (or pipeline) |

**What it is:**  
The foundational web protocol. HTTP/1.1 introduced persistent connections (Connection: keep-alive), virtual hosting (Host header), and chunked transfer encoding. Head-of-line blocking: a blocked response blocks all subsequent pipelined requests on that connection.

**Cloud-native relevance:**  
- Kubernetes liveness/readiness probes default to HTTP/1.1.  
- Legacy microservices still use HTTP/1.1; Envoy terminates and upgrades to HTTP/2.  
- Health check endpoints, metrics scraping, webhook callbacks.

---

### 9.2 HTTP/2

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9113 |
| Transport | TLS (h2) or cleartext (h2c) over TCP |
| Key features | Binary framing, stream multiplexing, header compression (HPACK), server push |
| Stream limit | Negotiated via SETTINGS_MAX_CONCURRENT_STREAMS |

**What it is:**  
HTTP/2 multiplexes multiple request-response pairs over a single TCP connection using a binary framing layer. HPACK header compression reduces overhead (critical for microservices making many small requests). Server Push allows the server to proactively send resources. However, TCP head-of-line blocking remains: a lost TCP segment stalls all HTTP/2 streams.

**Cloud-native relevance:**  
- gRPC uses HTTP/2 as its transport.  
- Kubernetes API server speaks HTTP/2 with clients (kubectl, controller-manager, kubelet).  
- Envoy uses HTTP/2 for upstream cluster connections.  
- `h2c` (HTTP/2 cleartext) is used for in-mesh traffic where TLS is handled separately (e.g., by WireGuard or IPsec at the network layer).  
- HTTP/2 stream multiplexing eliminates the "connection pool exhaustion" problem of HTTP/1.1 microservice communication.

---

### 9.3 HTTP/3

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 9114 |
| Transport | QUIC (UDP) |
| Header compression | QPACK (RFC 9204) |
| Alt-Svc | HTTP header advertises HTTP/3 availability |

**What it is:**  
HTTP/3 runs over QUIC instead of TCP, eliminating TCP head-of-line blocking (each QUIC stream is independently loss-recovered). QPACK replaces HPACK for header compression (adapted for QUIC's out-of-order delivery).

**Cloud-native relevance:**  
- Envoy 1.19+ supports HTTP/3 frontend (client-facing) and backend.  
- Nginx 1.25+ HTTP/3 support.  
- GKE, Cloudflare Load Balancers, AWS CloudFront — all support HTTP/3 at the edge.  
- Internal cluster HTTP/3: less common (adds UDP complexity to firewalls); typically only at ingress.

---

### 9.4 gRPC

| Attribute | Detail |
|-----------|--------|
| Spec | grpc.io / Google, CNCF graduated |
| Transport | HTTP/2 (mandatory) |
| Serialization | Protocol Buffers (default), JSON (grpc-gateway), FlatBuffers |
| Streaming | Unary, client-stream, server-stream, bidirectional stream |
| Metadata | HTTP/2 headers |

**What it is:**  
gRPC is a high-performance RPC framework using HTTP/2 multiplexing and Protocol Buffers serialization. It generates type-safe client/server stubs from `.proto` definitions. Supports all four streaming modes, deadline propagation, cancellation, and rich middleware (interceptors).

**Cloud-native relevance:**  
- Kubernetes: kubelet ↔ container runtime (CRI), kubelet ↔ CNI plugin communication internally uses gRPC.  
- Envoy xDS API (see below) — all control plane protocols (CDS, EDS, LDS, RDS, SDS) are gRPC.  
- Istio pilot-agent, Cilium operator, Prometheus remote write, OpenTelemetry collector — all gRPC.  
- gRPC health checking protocol (grpc.health.v1) is standard for Kubernetes liveness probes.  
- gRPC-Web: JavaScript clients bridged via Envoy or gRPC-Web proxy.  
- grpc-gateway: generates REST/JSON ↔ gRPC translation from `.proto` annotations.

**gRPC load balancing in Kubernetes:**  
HTTP/2 multiplexing means a single TCP connection carries all RPCs — Kubernetes Service kube-proxy L4 load balancing only balances at connection setup, not per-RPC. Solutions:  
- Use client-side gRPC load balancing (built-in with xDS bootstrap).  
- Use a service mesh (Istio/Linkerd) that intercepts gRPC and load-balances per-stream.  
- Use headless Kubernetes Service and client-side DNS-based load balancing.

---

### 9.5 WebSocket

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 6455 |
| Upgrade | HTTP/1.1 `Upgrade: websocket` |
| Framing | Binary/text frames, ping/pong |
| Cloud-native tools | Kubernetes API watch (`kubectl get pods -w`), many dashboards |

**What it is:**  
WebSocket upgrades an HTTP/1.1 connection to a full-duplex, low-latency binary/text framing protocol. After the HTTP upgrade handshake, both sides can send frames at any time.

**Cloud-native relevance:**  
- Kubernetes API server `Watch` requests (used by kubectl, informers) are WebSocket connections over HTTP/1.1 (or HTTP/2 streaming).  
- Kubernetes `exec`, `attach`, `port-forward` use SPDY or WebSocket multiplexing.  
- Envoy: `upgrade_configs` to proxy WebSocket connections.  
- Ingress controllers (NGINX, Traefik) must be configured for WebSocket passthrough (proxy_read_timeout, Upgrade headers).

---

### 9.6 DNS — Domain Name System

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 1034, RFC 1035, RFC 7858 (DoT), RFC 8484 (DoH) |
| Transport | UDP 53 (primary), TCP 53 (zone transfers, large responses) |
| DNSSEC | RFC 4033–4035 |
| Cloud-native tools | CoreDNS (Kubernetes default), external-dns, dnsdist |

**What it is:**  
DNS resolves names to IP addresses (A/AAAA records), and provides service discovery (SRV records), mail routing (MX), and CNAME aliasing. In cloud-native, DNS is the universal service discovery mechanism.

**CoreDNS in Kubernetes:**  
- Runs as a Deployment in kube-system; kube-dns Service IP is injected into every pod's /etc/resolv.conf.  
- Kubernetes plugin: resolves `<service>.<namespace>.svc.cluster.local` → ClusterIP.  
- Pod DNS: `<pod-ip>.<namespace>.pod.cluster.local`.  
- Negative caching, NXDOMAIN responses, and search domain explosion (ndots:5 is the default — causes 5 DNS lookups per external query).

**DNS scalability issues:**  
- High-traffic clusters: thousands of pods × high request rate → CoreDNS CPU saturation.  
- NodeLocal DNSCache (Kubernetes): caching DNS agent on each node reduces cross-node DNS traffic.  
- `ndots:5` tuning: reduce with `dnsConfig.options: [{name: ndots, value: "1"}]`.

**DNS security:**  
- DNSSEC: validates DNS responses with cryptographic signatures — rarely used inside clusters.  
- DNS over TLS (DoT, RFC 7858): encrypts DNS queries to prevent eavesdropping — CoreDNS supports DoT as forward plugin.  
- DNS over HTTPS (DoH, RFC 8484): DNS queries over HTTP/2/TLS — used in browser/edge contexts.  
- DNS exfiltration: a common data exfiltration channel; NetworkPolicy should restrict pod DNS to CoreDNS only.

---

### 9.7 DHCP — Dynamic Host Configuration Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2131 (DHCPv4), RFC 8415 (DHCPv6) |
| Transport | UDP 67 (server), 68 (client) / IPv6: UDP 546/547 |
| Cloud-native tools | Kube-DHCP (Multus), dnsmasq, ISC Kea |

**What it is:**  
DHCP automatically assigns IP addresses, subnet masks, gateways, DNS servers, and other network parameters to hosts. DORA: Discover, Offer, Request, Acknowledge.

**Cloud-native relevance:**  
- Kubernetes pods don't use DHCP (CNI assigns IPs directly); bare-metal nodes use DHCP for initial provisioning (PXE boot).  
- Multus CNI with macvlan/ipvlan can attach pods to external networks that use DHCP for IP assignment.  
- MetalLB Layer 2 mode uses ARP/NDP (not DHCP) for LoadBalancer IP advertisement.  
- cloud-init/ignition uses DHCP-provided options for VM bootstrapping.

---

### 9.8 NTP / PTP — Time Synchronization

| Attribute | Detail |
|-----------|--------|
| NTP RFC | RFC 5905 |
| PTP | IEEE 1588v2 |
| NTP transport | UDP 123 |
| PTP transport | UDP 319/320 or Ethernet (raw) |
| Cloud-native tools | chrony, linuxptp, ptpd |

**What it is:**  
NTP provides millisecond-level time synchronization over the public Internet using a hierarchical stratum model. PTP (Precision Time Protocol) provides sub-microsecond synchronization using hardware timestamping on the NIC.

**Cloud-native relevance:**  
- Kubernetes requires time synchronization across all nodes for:  
  - TLS certificate validity checking  
  - etcd Raft log ordering  
  - Distributed tracing (trace spans require synchronized clocks)  
  - Log correlation across nodes  
- Telco/5G cloud-native: 5G radio requires <1.5μs timing accuracy → PTP with hardware timestamping (IEEE 1588).  
- AWS Time Sync Service: uses Chrony pointing at 169.254.169.123 (PTP hardware clock on the hypervisor).  
- `linuxptp` / `ptp4l` for PTP grandmaster on bare-metal nodes.

---

### 9.9 LDAP — Lightweight Directory Access Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 4510–4519 |
| Transport | TCP 389 (LDAP), TCP 636 (LDAPS) |
| Cloud-native tools | Dex (OIDC bridge), Keycloak |

**What it is:**  
LDAP is a protocol for accessing and modifying directory services (X.500-based). Used for user identity stores (Active Directory, OpenLDAP). In cloud-native, LDAP is rarely used directly — instead, Dex or Keycloak bridge LDAP to OIDC/OAuth2 for Kubernetes authentication.

**Cloud-native relevance:**  
- Kubernetes RBAC + OIDC: users authenticate via OIDC (Dex/Keycloak) which internally queries LDAP/AD.  
- `kube-apiserver --oidc-issuer-url=https://dex.example.com` connects Kubernetes to the OIDC provider.

---

### 9.10 RADIUS — Remote Authentication Dial-In User Service

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 2865, RFC 2868, RFC 3579 |
| Transport | UDP 1812 (auth), 1813 (accounting) |
| Successor | DIAMETER (RFC 6733) |
| Cloud-native tools | FreeRADIUS, Radsec |

**What it is:**  
RADIUS is the traditional AAA (Authentication, Authorization, Accounting) protocol for network access. Used for 802.1X network port authentication (Wi-Fi WPA Enterprise, wired NAC), VPN authentication, and network device login.

**Cloud-native relevance:**  
- Kubernetes bare-metal clusters with 802.1X port-based access control use RADIUS for authenticating node NICs.  
- RadSec (RADIUS over TLS, RFC 6614): encrypts RADIUS traffic — required for production use.  
- Telco cloud-native: 5G core AUSF/UDM may integrate with RADIUS for MVNO roaming.

---

### 9.11 SNMP — Simple Network Management Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 3411–3418 (SNMPv3) |
| Transport | UDP 161 (queries), 162 (traps) |
| Versions | v1 (insecure), v2c (community strings), v3 (auth+priv) |
| Cloud-native replacement | gNMI/gRPC (OpenConfig), Prometheus SNMP exporter |

**What it is:**  
SNMP queries and configures network devices via MIB (Management Information Base) OIDs. Traps are asynchronous notifications from devices to the management system.

**Cloud-native relevance:**  
- Prometheus SNMP exporter translates SNMP OIDs to Prometheus metrics for switch/router monitoring.  
- Modern cloud-native network monitoring prefers gNMI (gRPC Network Management Interface, OpenConfig) over SNMP.  
- SNMPv1/v2c are insecure (community strings in plaintext); only SNMPv3 with authPriv (AES/SHA) is acceptable.

---

### 9.12 syslog — System Logging Protocol

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 5424 (syslog), RFC 6587 (TCP transport) |
| Transport | UDP 514 (legacy), TCP 514, TLS 6514 |
| Cloud-native tools | Fluentd, Fluent Bit, Vector, Loki |

**What it is:**  
Syslog is the standard log transport protocol. RFC 5424 defines the structured message format; RFC 6587 adds framing for TCP transport. In cloud-native, syslog is largely replaced by log pipelines (Fluent Bit → Loki/Elasticsearch) but kernel and network device logs still use syslog.

**Cloud-native relevance:**  
- Kubernetes node system logs (kubelet, containerd, kernel audit) emitted via syslog/journald.  
- Vector/Fluent Bit deployed as DaemonSet: collects pod logs + syslog, forwards to Loki or OpenSearch.  
- Network devices (switches, firewalls) in bare-metal clusters send syslog to central aggregators.

---

### 9.13 PROXY Protocol

| Attribute | Detail |
|-----------|--------|
| Spec | HAProxy PROXY Protocol v1 and v2 |
| Transport | TCP (prepended to connection) |
| Purpose | Preserve original client IP through L4 load balancers |

**What it is:**  
PROXY protocol is a simple header prepended to a TCP connection by a load balancer to convey the original client IP and port to the backend server. Without it, the backend sees the load balancer's IP.

**Cloud-native relevance:**  
- Kubernetes: `service.beta.kubernetes.io/aws-load-balancer-proxy-protocol: "*"` enables PROXY protocol on AWS NLB.  
- Envoy: `use_proxy_proto: true` in ListenerFilter to parse PROXY protocol.  
- NGINX Ingress: `use-proxy-protocol: "true"` annotation.  
- Critical for IP-based rate limiting, geo-filtering, and audit logging behind L4 load balancers.

---

### 9.14 OAuth 2.0 / OIDC

| Attribute | Detail |
|-----------|--------|
| OAuth 2.0 RFC | RFC 6749, RFC 6750 |
| OIDC spec | OpenID Connect Core 1.0 |
| Transport | HTTPS |
| Cloud-native tools | Dex, Keycloak, Pinniped, AWS Cognito |

**What it is:**  
OAuth 2.0 is an authorization delegation framework. OIDC (OpenID Connect) extends OAuth 2.0 to provide identity (ID tokens as JWT). The Authorization Code flow with PKCE is the standard for web apps; Client Credentials flow for service-to-service.

**Cloud-native relevance:**  
- Kubernetes API server OIDC authentication: `--oidc-issuer-url`, `--oidc-client-id`, `--oidc-username-claim`.  
- Pinniped: Kubernetes-native OIDC/LDAP authentication bridge (CNCF sandbox).  
- Istio JWT authentication: Envoy validates OIDC JWTs at the ingress sidecar.  
- AWS IAM OIDC: EKS IRSA (IAM Roles for Service Accounts) uses OIDC federation.

---

### 9.15 Prometheus Remote Write / OpenMetrics

| Attribute | Detail |
|-----------|--------|
| Spec | Prometheus Remote Write 2.0, OpenMetrics RFC draft |
| Transport | HTTP/1.1 or HTTP/2, protobuf or text |
| Port | 9090 (Prometheus), 9091 (pushgateway), configurable |

**What it is:**  
Prometheus scrape protocol: Prometheus HTTP GETs `/metrics` endpoints exposing text/openmetrics data. Remote Write: Prometheus POSTs compressed protobuf metric batches to remote storage (Thanos Receiver, Mimir, VictoriaMetrics).

**Cloud-native relevance:**  
- Every CNI, service mesh, and cloud-native tool exposes Prometheus metrics.  
- Cilium: metrics on `:9962/metrics`; Envoy: `:9901/stats/prometheus`; CoreDNS: `:9153/metrics`.  
- OpenMetrics (CNCF): standardizes Prometheus text format with exemplars (trace IDs embedded in metrics).

---

### 9.16 OpenTelemetry (OTLP)

| Attribute | Detail |
|-----------|--------|
| Spec | OpenTelemetry Protocol (OTLP) |
| Transport | gRPC (port 4317) or HTTP/1.1 (port 4318) |
| Data | Traces, metrics, logs |
| Cloud-native tools | OTel Collector, Jaeger, Zipkin, Grafana Tempo |

**What it is:**  
OTLP is the wire protocol for exporting traces, metrics, and logs from instrumented applications to observability backends. The OpenTelemetry Collector acts as a pipeline: receives OTLP, processes (sample, batch, enrich), and exports to multiple backends.

**Cloud-native relevance:**  
- gRPC-based OTLP is preferred (bidirectional streaming for acknowledgment).  
- Kubernetes: OTel Operator auto-instruments pods via admission webhook.  
- Cilium: Hubble exports L7 flow data as OTLP traces.  
- Istio Envoy: native OTLP trace export (Zipkin/Jaeger/OTLP modes).

---

### 9.17 iSCSI

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 7143 |
| Transport | TCP 3260 |
| Cloud-native tools | OpenEBS, Longhorn, Rook/Ceph iSCSI, Portworx |

**What it is:**  
iSCSI encapsulates SCSI commands over TCP/IP, enabling block storage access over standard Ethernet networks. An iSCSI initiator (client) connects to a target (storage server) and gets a block device (`/dev/sdX`).

**Cloud-native relevance:**  
- Kubernetes CSI drivers (OpenEBS, Longhorn) provision iSCSI LUNs as PersistentVolumes.  
- `iscsiadm` manages initiator sessions; multipath (`multipathd`) provides HA.  
- iSCSI requires jumbo frames (MTU 9000) and dedicated VLANs for performance isolation.  
- Security: iSCSI CHAP (Challenge Handshake Authentication Protocol) for authentication; IPsec for encryption.

---

### 9.18 NFS — Network File System

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 7530 (NFSv4), RFC 8881 (NFSv4.2) |
| Transport | TCP/UDP 2049 |
| Features (v4.2) | pNFS, RDMA (NFS/RDMA), server-side copy, sparse files |
| Cloud-native tools | NFS CSI Driver, Rook/CephFS |

**What it is:**  
NFS provides shared file system access over a network. NFSv4 is stateful (TCP-only), supports strong authentication (Kerberos, RPCSEC_GSS), and optional pNFS for parallel I/O to multiple storage nodes.

**Cloud-native relevance:**  
- Kubernetes ReadWriteMany (RWX) PersistentVolumes — NFS is the most common implementation.  
- NFS CSI Driver for Kubernetes: `csi.storage.k8s.io/provisioner: nfs.csi.k8s.io`.  
- NFSv4 over RDMA (RFC 8267): orders of magnitude higher throughput for AI/ML training workloads.  
- AWS EFS (Elastic File System): NFSv4.1 as a service.

---

### 9.19 SMB / CIFS

| Attribute | Detail |
|-----------|--------|
| Standard | MS-SMB2 (SMB 2.x/3.x) |
| Transport | TCP 445 |
| Security | SMB Signing, SMB Encryption (AES-CCM/GCM) |
| Cloud-native tools | Azure Files CSI, Windows containers |

**What it is:**  
SMB is the Windows network file system protocol. SMB 3.x adds end-to-end encryption, Multichannel (multiple TCP connections), and Direct (SMB over RDMA).

**Cloud-native relevance:**  
- Kubernetes on Windows: Azure Files CSI Driver mounts SMB shares as PersistentVolumes for Windows pods.  
- Mixed Linux/Windows clusters: SMB CSI driver supports Linux mounts via `cifs-utils`.  
- Azure Files Premium: SMB 3.0 with SSD backing for high-IOPS Windows workloads.

---

### 9.20 NVMe-oF — NVMe over Fabrics

| Attribute | Detail |
|-----------|--------|
| Standard | NVM Express over Fabrics 1.1 |
| Transports | NVMe/RDMA (RoCEv2/iWARP/IB), NVMe/TCP (RFC pending), NVMe/FC |
| Port | NVMe/TCP: TCP 4420 |
| Cloud-native tools | SPDK, Longhorn, OpenEBS Mayastor |

**What it is:**  
NVMe-oF extends the NVMe protocol (designed for PCIe SSDs) over a network fabric. NVMe/RDMA achieves near-local SSD latency (<100μs) over the network. NVMe/TCP provides broader compatibility over standard TCP/IP.

**Cloud-native relevance:**  
- OpenEBS Mayastor: NVMe-oF TCP dataplane in Kubernetes; achieves 1–2M IOPS per volume.  
- SPDK (Storage Performance Development Kit): user-space NVMe-oF target in containers for hyperscale storage.  
- Kubernetes CSI: NVMe-oF target provisions PVs with microsecond latency.

---

## Cloud-Native Control-Plane Protocols

---

### 10.1 xDS — Discovery Service API (Envoy)

| Attribute | Detail |
|-----------|--------|
| Transport | gRPC bidirectional streaming or REST/HTTP |
| API version | xDS v3 (current), v2 (legacy) |
| Sub-protocols | CDS, EDS, LDS, RDS, SDS, ADS, RTDS, ECDS |
| Cloud-native tools | Envoy, Istio, Consul Connect, Gloo Edge, Contour |

**What it is:**  
xDS is a suite of gRPC-based APIs through which a control plane (Istio Pilot/istiod, Consul, xDS management server) pushes dynamic configuration to Envoy data-plane proxies:

- **LDS** (Listener Discovery Service): Envoy listen ports and filter chains  
- **RDS** (Route Discovery Service): HTTP routing rules  
- **CDS** (Cluster Discovery Service): upstream service definitions  
- **EDS** (Endpoint Discovery Service): individual backend IPs/ports  
- **SDS** (Secret Discovery Service): TLS certificates and keys  
- **ADS** (Aggregated DS): single stream for all above — preferred for consistency  
- **RTDS** (Runtime DS): feature flags / runtime parameters  
- **ECDS** (Extension Config DS): dynamic filter configurations  

**Cloud-native relevance:**  
- The xDS protocol IS the service mesh control plane wire format.  
- Cilium Envoy config uses xDS via local Envoy management server.  
- Direct xDS clients in Go: `go-control-plane` library.  
- Universal Data Plane API (UDPA): the next evolution of xDS.

---

### 10.2 Kubernetes API (REST / protobuf / WebSocket)

| Attribute | Detail |
|-----------|--------|
| Transport | HTTPS (TLS 1.3), HTTP/2 |
| Serialization | JSON (external), protobuf (internal, faster) |
| Auth | mTLS client certs, Bearer tokens (OIDC JWT), service account tokens |
| Watch | WebSocket or HTTP/2 long poll with chunked transfer |

**What it is:**  
The Kubernetes API server exposes a RESTful API for all cluster resources. Controllers and operators use Informer pattern (Watch + List + local cache) over the API server WebSocket stream. All CNI/CSI/CRI plugins are registered via API server extensions (CRDs, admission webhooks).

**Cloud-native network relevance:**  
- CNI controllers (Cilium, Calico operators) watch Pod/Node/Namespace/NetworkPolicy objects.  
- API server webhook admission: Istio injects sidecar by mutating pod specs via `MutatingWebhookConfiguration`.  
- API server audit logging → OPA/Gatekeeper for policy enforcement.

---

### 10.3 etcd — Raft Consensus Protocol

| Attribute | Detail |
|-----------|--------|
| Algorithm | Raft (Diego Ongaro's thesis) |
| Transport | gRPC over TLS |
| Port | 2379 (client), 2380 (peer) |
| Cloud-native tools | etcd (Kubernetes backing store) |

**What it is:**  
etcd is a distributed key-value store using the Raft consensus algorithm. Raft ensures that a majority quorum of nodes agrees on every write before committing, providing linearizable reads and writes. All Kubernetes cluster state is stored in etcd.

**Cloud-native network relevance:**  
- etcd cluster communication (peer traffic on 2380) requires low latency — cross-AZ etcd causes election timeouts.  
- Network partitions that split etcd quorum cause Kubernetes API unavailability — design for quorum (3 or 5 nodes in distinct failure domains).  
- Encrypt etcd at rest (`encryption-provider-config` for envelope encryption with KMS).  
- mTLS peer and client authentication mandatory for production etcd.

---

### 10.4 CRI — Container Runtime Interface (gRPC)

| Attribute | Detail |
|-----------|--------|
| Transport | Unix socket (gRPC) |
| API | `runtime.v1.RuntimeService`, `runtime.v1.ImageService` |
| Implementations | containerd, CRI-O |

**What it is:**  
CRI is the gRPC-based interface between kubelet and the container runtime. kubelet sends `RunPodSandbox`, `CreateContainer`, `StartContainer` gRPC calls; the runtime creates namespaces, cgroups, and calls the CNI plugin.

**Network relevance:**  
- `RunPodSandbox` creates the pod network namespace; the runtime calls CNI ADD with the namespace path.  
- The CNI plugin (via `exec` or gRPC) configures the veth pair, IP address, routes, and policy.

---

### 10.5 CNI — Container Network Interface

| Attribute | Detail |
|-----------|--------|
| Spec | github.com/containernetworking/cni |
| Invocation | Binary exec by runtime (stdin JSON config, env vars) |
| Operations | ADD, DEL, CHECK, VERSION |
| Cloud-native tools | Cilium, Calico, Flannel, Weave, OVN-Kubernetes, Antrea |

**What it is:**  
CNI is not a network protocol per se, but the plugin interface through which container runtimes configure networking for pods. The runtime execs the CNI binary with JSON configuration; the CNI plugin creates the network interface, assigns an IP, and configures routes/iptables/eBPF.

**Chained CNI plugins (Multus):**  
Multus allows multiple CNI plugins to run in sequence, attaching multiple network interfaces to a pod (e.g., Cilium for primary + SR-IOV for high-throughput secondary interface).

---

### 10.6 IPAM Protocols

| Attribute | Detail |
|-----------|--------|
| Methods | Host-local (file on disk), Whereabouts (CRD-based), Calico IPAM (etcd), AWS VPC CNI IPAM |
| Transport | Internal / API server CRDs |

**What it is:**  
IP Address Management in Kubernetes is handled by CNI IPAM plugins that allocate pod IPs from a pool. Cloud provider CNIs (AWS VPC CNI, Azure CNI, GKE) allocate IPs directly from the VPC subnet.

---

### 10.7 EBPF / XDP (as a "protocol layer")

| Attribute | Detail |
|-----------|--------|
| Kernel interface | `bpf()` syscall, LLVM/clang compilation |
| Program types | XDP, TC, socket filter, sockops, cgroup, kprobe/tracepoint |
| Map types | Hash, array, LRU, perf event, ring buffer, sockmap |
| Cloud-native tools | Cilium, Katran (Facebook LB), bpfilter, Falco |

**What it is:**  
eBPF (Extended Berkeley Packet Filter) is a programmable kernel subsystem that allows safe, verified bytecode to run inside the kernel at various hook points. XDP (eXpress Data Path) runs eBPF at the NIC driver level (earliest possible kernel hook) for maximum throughput (wire-rate packet processing).

**Cloud-native eBPF network use cases:**  
- **Cilium**: replaces kube-proxy, iptables, VXLAN encap/decap, L7 policy enforcement, service load balancing — all in eBPF.  
- **Katran**: Facebook's L4 load balancer — XDP-based, replaces IPVS.  
- **Hubble**: eBPF-based network observability — reads flow data from Cilium eBPF maps.  
- **Falco**: eBPF tracepoints for syscall-level security monitoring.  
- **XDP offload**: on supported NICs (mlx5), XDP programs can run directly on NIC hardware.

**eBPF program hooks relevant to networking:**

```
NIC RX → XDP (pre-alloc, drop/redirect/pass)
        → tc ingress BPF (post-alloc, full skb)
        → netfilter/iptables
        → socket layer → socket filter BPF
                       → sockops BPF (TCP events)
                       → sk_msg BPF (socket redirect)
        → tc egress BPF
        → NIC TX
```

---

### 10.8 gNMI — gRPC Network Management Interface

| Attribute | Detail |
|-----------|--------|
| Standard | OpenConfig / gNMI spec |
| Transport | gRPC / TLS |
| Operations | Get, Set, Subscribe (STREAM/ONCE/POLL) |
| Cloud-native tools | gNMIc, OpenConfig Telemetry, Telegraf, Prometheus |

**What it is:**  
gNMI is the modern replacement for NETCONF/SNMP for network device management and streaming telemetry. Devices stream counter/state data at configurable intervals using gRPC Subscribe — far more efficient than SNMP polling.

**Cloud-native relevance:**  
- SONiC switches: gNMI telemetry streamed to Prometheus/Grafana.  
- Kubernetes cluster network health: gNMI data from TOR switches correlated with pod-level metrics.  
- gnmic CLI tool for ad-hoc gNMI queries to switches.

---

### 10.9 NETCONF / YANG

| Attribute | Detail |
|-----------|--------|
| RFC | RFC 6241 (NETCONF), RFC 7950 (YANG) |
| Transport | SSH (TCP 830) |
| Data | YANG models (XML or JSON encoding) |

**What it is:**  
NETCONF is an XML-based network configuration protocol over SSH. YANG is the data modeling language for NETCONF. Largely superseded by gNMI/OpenConfig in cloud-native environments but still used in legacy network infrastructure and some 5G core platforms.

---

## Hardware-Acceleration & Kernel-Bypass Protocols

---

### 11.1 RDMA — Remote Direct Memory Access

| Attribute | Detail |
|-----------|--------|
| Standard | IBTA InfiniBand, iWARP (RFC 5040/5041), RoCE (IBTA) |
| Transports | InfiniBand, RoCEv1 (EtherType 0x8915), RoCEv2 (UDP 4791), iWARP (TCP) |
| Key feature | Zero-copy, kernel bypass, CPU offload for network I/O |

**What it is:**  
RDMA allows a NIC to directly read/write a remote host's memory without involving the remote CPU or OS kernel. The application registers memory regions with the NIC; the NIC performs DMA directly. Verb API: post Send/Receive Work Requests to queue pairs; poll completion queues.

**RDMA variants:**
- **InfiniBand**: native RDMA, lossless, hardware fabric  
- **RoCEv1**: RDMA over Ethernet L2 (requires lossless fabric with PFC)  
- **RoCEv2**: RDMA over UDP (IP routable; requires ECN+DCQCN for congestion control)  
- **iWARP**: RDMA over TCP (loss-tolerant but higher latency; hardware-dependent)  

**Cloud-native relevance:**  
- Kubernetes AI/ML workloads: NCCL uses RDMA (RoCEv2) for all-reduce operations in GPU training.  
- SR-IOV + RDMA: VF exposed directly to pod; RDMA verb library talks to VF driver.  
- Multus CNI + SR-IOV CNI + RDMA device plugin: standard Kubernetes pattern for RDMA workloads.  
- OpenMPI + RDMA: HPC-style MPI jobs in Kubernetes (MPI Operator).

---

### 11.2 DPDK — Data Plane Development Kit

| Attribute | Detail |
|-----------|--------|
| Project | dpdk.org |
| Model | User-space poll-mode driver (PMD) |
| Bypass | Kernel network stack entirely |
| Cloud-native tools | OVS-DPDK, VPP, SPDK (storage), FD.io |

**What it is:**  
DPDK enables user-space packet processing by binding NICs to a PMD (Poll Mode Driver), bypassing the Linux kernel network stack. Applications poll the NIC RX queue directly from user space using huge pages (minimize TLB misses) and CPU pinning (avoid context switches).

**Cloud-native relevance:**  
- OVS-DPDK: replaces kernel OVS for virtual switch performance — achieves ~100Gbps forwarding vs ~10Gbps with kernel OVS.  
- FD.io/VPP: vector packet processing framework using DPDK; used in Cisco ACI, telco UPF implementations.  
- SPDK uses DPDK for NVMe-oF target implementation.  
- Kubernetes: DPDK workloads require hugepage allocation, CPU isolation (isolated CPUset), and SR-IOV VFs.

---

### 11.3 AF_XDP — User-space XDP

| Attribute | Detail |
|-----------|--------|
| Kernel | Linux 4.18+ |
| Type | Zero-copy socket between kernel XDP and user space |
| Interface | UMEM ring buffers, shared with kernel |

**What it is:**  
AF_XDP is a socket type that allows user-space applications to receive packets redirected by eBPF XDP programs, bypassing most of the kernel stack while still using standard socket semantics. Lower complexity than DPDK (no PMD, no VFIO needed) while achieving near-DPDK performance.

**Cloud-native relevance:**  
- Cilium AF_XDP mode: replaces DPDK for high-throughput packet processing without requiring kernel bypass.  
- Load balancers (Katran, Cilium XLB): use AF_XDP for line-rate L4 processing.  
- `xdpsock` tool for testing AF_XDP performance.

---

## Protocol Matrix: Tool ↔ Protocol Mapping

| Tool / Project | L1/L2 | L3 | L4 | Overlay | L7 | Control |
|---|---|---|---|---|---|---|
| **Cilium** | eBPF/TC, VLAN, MACsec | IPv4, IPv6, BGP | TCP, UDP, SCTP | VXLAN, GENEVE, WireGuard, IPsec | HTTP, gRPC, DNS, Kafka | eBPF maps, xDS, K8s API |
| **Calico** | VLAN, 802.1Q | IPv4, IPv6, BGP, OSPF | TCP, UDP | IPIP, VXLAN, WireGuard, IPsec | — | BGP, K8s API, etcd |
| **Flannel** | Ethernet | IPv4 | UDP | VXLAN, host-gw, IPIP, WireGuard | — | K8s API |
| **OVN/OVS** | Ethernet, 802.1Q, QinQ | IPv4, IPv6, ARP | TCP, UDP | VXLAN, GENEVE, STT, GRE | — | OVSDB, BGP EVPN |
| **Antrea** | Ethernet | IPv4, IPv6 | TCP, UDP | VXLAN, GENEVE, GRE, WireGuard, IPsec | — | xDS, K8s API |
| **Istio/Envoy** | — | IPv4, IPv6 | TCP, UDP, QUIC | — | HTTP/1.1, HTTP/2, HTTP/3, gRPC, WebSocket, TLS, mTLS | xDS (ADS), gRPC |
| **Linkerd** | — | IPv4, IPv6 | TCP | — | HTTP/1.1, HTTP/2, gRPC, mTLS | Kubernetes API, SMI |
| **MetalLB** | Ethernet, GARP | IPv4, IPv6 | — | — | — | BGP, L2 ARP/NDP |
| **CoreDNS** | — | IPv4, IPv6 | UDP, TCP | — | DNS, DoT, DoH | K8s API |
| **FRRouting** | LLDP | IPv4, IPv6, BGP, OSPF, IS-IS, BFD, MPLS, SR | — | — | — | gRPC (GoBGP), NETCONF |
| **Multus CNI** | SR-IOV, macvlan | IPv4, IPv6 | TCP, UDP, SCTP, RDMA | VXLAN, GENEVE (per sub-CNI) | — | K8s API, CRDs |
| **SPIRE** | — | IPv4, IPv6 | TCP | — | gRPC, mTLS, SPIFFE SVID | K8s API, Attestation |
| **OpenTelemetry** | — | IPv4, IPv6 | TCP, UDP | — | OTLP/gRPC, OTLP/HTTP | gRPC |

---

## Key MTU Reference

| Encapsulation | Overhead | Inner MTU (on 1500 physical) |
|---|---|---|
| Bare Ethernet | 0 | 1500 |
| 802.1Q VLAN | +4 | 1496 |
| IPIP | +20 | 1480 |
| GRE | +24 | 1476 |
| VXLAN | +50 | 1450 |
| GENEVE | +58+ | 1442+ |
| VXLAN + WireGuard | +50+60 | 1390 |
| VXLAN + IPsec ESP | +50+52 | 1398 |

> Always configure pod/container MTU explicitly to match the overlay MTU. PMTUD relies on ICMP type 3/code 4 — never block it.

---

## Security Reference: Protocol-Level Threat Matrix

| Protocol | Primary Threats | Mitigations |
|---|---|---|
| ARP / NDP | Spoofing, poisoning, MITM | DAI, eBPF ARP filter, L3-only routing |
| BGP | Session hijack, prefix hijack, route leak | MD5/TCP-AO, RPKI, prefix filters, TTL security |
| VXLAN | Unauthorized encap injection, VNI brute-force | Underlay firewall (UDP 4789), overlay encryption (WireGuard/IPsec) |
| DNS | Cache poisoning, amplification, exfiltration | DNSSEC, DoT/DoH, DNS NetworkPolicy, CoreDNS rate limiting |
| TLS | Downgrade, cert spoofing, MITM | TLS 1.3 min, cert pinning, mTLS, SPIFFE/SPIRE |
| gRPC | Insecure channel, unauth endpoints | mTLS mandatory, authz interceptor, RBAC |
| SNMP v1/v2c | Community string sniffing | Migrate to SNMPv3 authPriv or gNMI/TLS |
| iSCSI | Unauthorized access, data exposure | CHAP auth + IPsec, dedicated VLAN/VXLAN |
| RDMA | DMA attack from compromised VF | IOMMU enabled, SR-IOV spoofchk on |
| HTTP/1.1 | Request smuggling, HRS attacks | Consistent parsing (Envoy), disable HTTP/1.0 |

---

## References

- [RFC Index (IETF)](https://www.rfc-editor.org/)  
- [Linux Kernel Networking Documentation](https://www.kernel.org/doc/html/latest/networking/)  
- [Cilium Network Reference](https://docs.cilium.io/en/stable/network/)  
- [Calico Architecture](https://docs.tigera.io/calico/latest/reference/architecture/)  
- [OVN Architecture](https://www.ovn.org/support/dist-docs/ovn-architecture.7.html)  
- [Envoy xDS API](https://www.envoyproxy.io/docs/envoy/latest/api-docs/xds_protocol)  
- [SPIFFE Spec](https://spiffe.io/docs/latest/spiffe-about/spiffe-concepts/)  
- [RFC 7938 — BGP in the Data Center](https://datatracker.ietf.org/doc/html/rfc7938)  
- [RFC 8986 — SRv6 Network Programming](https://datatracker.ietf.org/doc/html/rfc8986)  
- [RFC 9000 — QUIC](https://datatracker.ietf.org/doc/html/rfc9000)  
- [eBPF Documentation](https://ebpf.io/what-is-ebpf/)  
- [CNCF Landscape](https://landscape.cncf.io/)  
- [OpenConfig / gNMI](https://openconfig.net/)  
- [DPDK Documentation](https://doc.dpdk.org/)  
- [WireGuard Whitepaper](https://www.wireguard.com/papers/wireguard.pdf)  
- [NVMe-oF Specification](https://nvmexpress.org/developers/nvme-of-specification/)

**Summary:** The document covers every protocol handled by cloud-native networking stacks across all OSI layers — 60+ protocols with security-first framing throughout.

**What's in it:**

- **L1** — 802.3 physical, SR-IOV, DWDM, InfiniBand
- **L2** — 802.1Q, 802.1ad QinQ, LACP, MACsec, STP/RSTP, LLDP, ARP, NDP, FCoE
- **L2.5** — MPLS, Segment Routing (SR-MPLS + SRv6)
- **L3** — IPv4, IPv6, ICMPv4/v6, BGP (including EVPN), OSPF, IS-IS, BFD, ECMP, PBR, IPIP, SIT, GRE
- **L4** — TCP, UDP, SCTP, QUIC, DCCP
- **L4 Overlay** — VXLAN, GENEVE, NVGRE, STT, WireGuard, IPsec (ESP/AH/IKEv2), VXLAN-GPE+NSH
- **L5/L6** — TLS 1.3, mTLS, DTLS, SPIFFE session identity
- **L7** — HTTP/1.1, HTTP/2, HTTP/3, gRPC, WebSocket, DNS/DoT/DoH, DHCP, NTP/PTP, LDAP, RADIUS, SNMP, syslog, PROXY Protocol, OAuth2/OIDC, Prometheus/OpenMetrics, OTLP, iSCSI, NFS, SMB, NVMe-oF
- **Control plane** — xDS full suite (LDS/RDS/CDS/EDS/SDS/ADS), Kubernetes API, etcd/Raft, CRI, CNI, IPAM, gNMI, NETCONF/YANG
- **HW accel** — RDMA (RoCEv2/iWARP/IB), DPDK, AF_XDP/eBPF
- **Bonus tables** — MTU overhead reference, protocol×tool matrix, threat model matrix per protocol