# Cloud & Cloud-Native Networking: A First-Principles Comprehensive Guide

**Summary:** Cloud networking is a layered stack of abstractions — from physical hardware and hypervisor switching, through overlay encapsulation, up to container runtimes and service mesh. Every abstraction introduces its own forwarding model, failure domain, and security boundary. Understanding what happens to a packet at each hop, why each layer exists, and where trust boundaries sit is the foundation of cloud-native security engineering. This guide covers every mandatory concept with the depth needed to reason about design trade-offs, threat models, and operational behavior.

---

## 1. The Mental Model: Cloud Networking is Layered Abstraction

Before any specific concept, internalize this: cloud networking does **not** replace the physical network — it **virtualizes** it. Every "virtual" construct (VPC, subnet, security group, overlay) has a concrete mapping to real physical hardware. Your job as a cloud-native security engineer is to know both the abstraction and the physical reality, because:

- Security boundaries are only as strong as the isolation the physical layer provides
- Performance limits come from the physical layer (NIC throughput, CPU cycles, memory bandwidth)
- Failures propagate through both layers simultaneously
- Threat actors who understand the underlay can often violate the overlay's assumptions

The mental model to always hold:

```
User Workload (Pod/VM/Container)
        ↓
Virtual NIC (veth, tap, SR-IOV VF)
        ↓
Host Virtual Switch (OVS, Linux bridge, eBPF/XDP)
        ↓
Overlay Encapsulation (VXLAN, Geneve, IPIP)
        ↓
Physical NIC (SmartNIC / DPU or standard NIC)
        ↓
Physical Network Fabric (ToR → Spine → Core)
        ↓
Cloud Provider Backbone / WAN
```

Every packet traverses all or part of this stack. Every hop is a forwarding decision. Every forwarding decision is a potential security event.

---

## 2. The Physical Underlay: What Cloud is Actually Built On

### 2.1 Data Center Network Topology

Cloud providers run **Clos/Fat-Tree** topologies — a mathematically elegant structure where every server has equal-cost paths to every other server. This is not accidental; it is the physical foundation of every cloud networking guarantee.

**The Clos topology:**

```
         [Core Switches]
        /       |        \
  [Spine]   [Spine]   [Spine]
   / | \     / | \     / | \
[ToR][ToR][ToR][ToR][ToR][ToR]
 |    |    |    |    |    |
[servers][servers][servers]
```

- **ToR (Top of Rack):** First hop switch, connects 20–48 servers. Operates at L2/L3. ARP termination often happens here in modern designs.
- **Spine:** Aggregation layer. Purely L3 in modern designs. No MAC learning — everything is IP-routed.
- **Core:** Inter-pod and inter-availability-zone routing. Carrier-grade reliability, often with redundant paths in the tens.

**Why this matters for cloud security:**
- East-West traffic (server-to-server within a DC) traverses the Clos fabric. If your overlay fails open (misconfigured), traffic falls to the underlay, potentially reachable across tenant boundaries.
- Bandwidth is deterministic — the Clos topology gives every server the same bisection bandwidth, which means a noisy neighbor's traffic storm has bounded blast radius (only its ToR).

### 2.2 ECMP (Equal-Cost Multi-Path) Routing

In a Clos topology, there are multiple paths of equal cost between any two endpoints. ECMP is the forwarding mechanism that uses all of them simultaneously.

**How ECMP works:** The forwarding hardware computes a hash over a flow tuple (typically src IP, dst IP, src port, dst port, protocol) and maps the hash to one of the available equal-cost next hops. All packets of a single TCP flow always hash to the same path — this preserves ordering within flows. Different flows spread across different paths.

**Why this is critical to understand:**
- ECMP is stateless and fast (hardware-implemented), but it is blind to path state beyond next-hop reachability. A path can be degraded (high loss, high latency) but still "up" from ECMP's perspective.
- Hash polarization: if multiple tiers all use the same hash inputs, flows can concentrate on a single physical path even though multiple paths exist. Modern implementations use different hash seeds at each tier.
- TCP session symmetry: ECMP can send a TCP SYN via one path and SYN-ACK via another if asymmetric routing exists. Stateful firewalls and NAT devices require symmetric routing, which is why they are often placed at the topology edge, not the interior.
- For cloud tenants: your VPC traffic flows over the provider's ECMP fabric. Micro-bursts from ECMP hash collisions are a real source of latency jitter.

### 2.3 BGP as the Underlay Routing Protocol

Modern data center networks run **BGP (Border Gateway Protocol)** — the same protocol that routes the global Internet — as their internal routing protocol. This is called **BGP in the data center** (RFC 7938).

BGP was chosen over OSPF/IS-IS for DC use because:
- It scales to millions of routes without the flooding that link-state protocols produce
- It has fine-grained policy controls (route maps, communities, local preference)
- It is vendor-neutral
- It naturally models the Clos topology (each ToR peers with its spines; each spine peers with cores)

**What BGP advertises in a DC underlay:**
- Each server's loopback IP (used for overlay tunnel endpoints)
- Aggregate subnet prefixes per rack or pod
- EVPN (Ethernet VPN) Type-2 and Type-5 routes for overlay-aware underlay designs

**BGP communities in cloud context:** Providers tag routes with communities to express metadata — which AZ, which region, which service tier. Cloud routers (AWS Transit Gateway, GCP Cloud Router, Azure Route Server) exchange BGP with customer networks and manipulate communities to implement routing policy.

**Security angle:** BGP in the underlay is almost always protected by **TCP MD5 or TCP-AO** authentication between peers. Route filtering is applied at every peering to ensure only expected prefixes are accepted. A misconfigured BGP peer is a route injection vulnerability — this is why BGP peer authentication and prefix filters are mandatory controls.

---

## 3. IP Addressing in Cloud: VPC, CIDR, and Address Architecture

### 3.1 RFC 1918 Private Address Space

Cloud VPCs exclusively use private address space (RFC 1918) internally:
- `10.0.0.0/8` — 16.7M addresses, most flexible for large environments
- `172.16.0.0/12` — 1M addresses
- `192.168.0.0/16` — 65K addresses, too small for enterprise VPCs

The reason VPCs use private space: workloads should not be directly addressable from the Internet. NAT/gateway constructs control when and how private workloads reach the public internet and vice versa. This is a fundamental security principle — your workload's private IP is only meaningful within the routing domain that knows about it.

**IPv6 in cloud:** Cloud providers assign globally-unique IPv6 prefixes (typically /56 per VPC, /64 per subnet). IPv6 eliminates NAT, which simplifies connectivity but changes the security model — every resource potentially has a public address, so security groups/NACLs must be IPv6-aware. Many cloud services still have IPv4-only control planes, creating dual-stack complexity.

### 3.2 CIDR and Longest-Prefix Match

**CIDR (Classless Inter-Domain Routing)** is the notation `A.B.C.D/prefix-length` that defines a contiguous block of IP addresses. A `/24` contains 256 addresses. A `/16` contains 65,536.

**Longest-prefix match (LPM)** is the universal IP routing rule: when a router has multiple routes that match a destination, it uses the one with the longest (most specific) prefix.

Example:
```
Route table:
  10.0.0.0/8    → via gateway A
  10.1.0.0/16   → via gateway B  
  10.1.1.0/24   → via gateway C

Packet to 10.1.1.5 → takes /24 route (most specific)
Packet to 10.1.2.5 → takes /16 route
Packet to 10.2.0.1 → takes /8 route
```

This principle governs everything: VPC routing tables, BGP forwarding, Kubernetes cluster routing, CNI plugin routing. When debugging unexpected routing, always ask "what is the most specific matching route?"

**VPC CIDR planning matters because:**
- VPCs cannot have overlapping CIDRs if you want to peer them. Once you deploy a VPC with `10.0.0.0/16`, every VPC you want to peer with must use a non-overlapping range. This cannot be changed without rebuilding — plan for the total address space of your organization before you deploy anything.
- Subnets within a VPC divide the CIDR. Each subnet exists in exactly one AZ. Hosts in a subnet share a common L3 domain — they can reach each other without routing through a gateway (L2 reachability within a subnet is virtualized by the hypervisor).

### 3.3 Subnets: Public vs. Private

**Public subnet:** Has a route to an Internet Gateway (or equivalent). Resources with public IPs here are reachable from the internet.

**Private subnet:** No route to the internet. Resources here can only be reached from within the VPC or through controlled egress (NAT Gateway, VPN, Direct Connect).

**The security architecture principle:** Compute workloads live in private subnets. Load balancers and NAT gateways live in public subnets. This creates defense-in-depth at the network layer — a compromised workload in a private subnet cannot receive inbound connections from the internet, it can only initiate outbound.

---

## 4. Overlay Networks: The Core Technology of Cloud Networking

### 4.1 Why Overlays Exist

Physical networks are configured manually and have limited scale for L2 (MAC table sizes on switches are bounded). Cloud needs to:
1. Create millions of isolated virtual networks (one per tenant)
2. Move VMs between physical servers without changing their IP addresses
3. Span "subnets" across physical switches without L2 adjacency
4. Isolate tenant traffic cryptographically

Overlays solve this by **tunneling** virtual network packets inside physical network packets. The physical network only sees outer headers (source/dest physical IP). The inner headers carry the tenant's virtual traffic.

```
Inner packet (tenant): [IP hdr: 10.0.1.5→10.0.2.7][TCP][Payload]
                              ↓  encapsulated inside
Outer packet (physical): [IP hdr: 192.168.10.5→192.168.20.3][UDP][VNI: 5001][Inner packet]
```

The encapsulation and decapsulation is performed by the **hypervisor** (or SmartNIC/DPU) at each end. The physical network is completely unaware of the tenant addressing.

### 4.2 VXLAN (Virtual eXtensible LAN)

VXLAN (RFC 7348) is the dominant overlay protocol in cloud data centers and Kubernetes CNI plugins.

**Structure:**
- Uses **UDP** as the transport (dst port 4789)
- Carries a 24-bit **VNI (VXLAN Network Identifier)** — 16 million possible overlay segments
- The outer IP header routes to the correct VTEP (VXLAN Tunnel Endpoint)
- The VTEP is the hypervisor or host network stack that performs encap/decap

**Why UDP?** UDP is stateless and multiplexed over 65K ports. Using a different src UDP port per flow allows ECMP to hash different flows to different physical paths (ECMP hashes on the outer 5-tuple). If VXLAN used a fixed port, all VXLAN traffic would hash to the same ECMP path — one link would handle all overlay traffic.

**VTEP discovery:** VTEPs need to know which VTEP handles which inner IP/MAC. Two mechanisms:
1. **Multicast-based (traditional):** VTEPs join a multicast group. BUM (Broadcast, Unknown, Multicast) traffic is multicast to all VTEPs. VTEPs learn remote MAC-to-VTEP mappings from the outer src IP of received frames. Scales poorly.
2. **Control-plane-based (BGP EVPN):** A BGP control plane (using EVPN address families) distributes MAC-to-VTEP and IP-to-VTEP mappings. VTEPs are fully provisioned before the first packet — no flood-and-learn. This is how modern clouds and Kubernetes CNIs (Calico, Cilium in VXLAN mode) operate.

**VXLAN security weaknesses:**
- No built-in encryption or authentication. Any host that can reach UDP/4789 can inject VXLAN frames into any VNI it knows about, if not properly isolated.
- The outer UDP/IP headers are observable — an on-path attacker sees which physical hosts are communicating even if the payload is encrypted.
- VXLAN relies entirely on the control plane (VTEP configuration) for tenant isolation. A misconfigured VTEP can leak traffic between VNIs.

### 4.3 Geneve (Generic Network Virtualization Encapsulation)

Geneve (RFC 8926) is the evolution of VXLAN, designed with extensibility. It is what AWS uses internally (Nitro system) and is growing in adoption.

**Key differences from VXLAN:**
- Variable-length header with TLV (Type-Length-Value) options. Allows carrying arbitrary metadata with the packet — security labels, QoS hints, telemetry tags.
- Still UDP-based (dst port 6081)
- 24-bit VNI like VXLAN
- Designed to carry any L2 or L3 traffic (VXLAN is L2-only by original design)

The TLV extensibility is critical for cloud providers: they can embed tenant metadata, policy tags, flow labels directly in the encapsulation header, making decisions on SmartNICs/DPUs without opening the inner payload.

### 4.4 IPIP and GRE Tunnels

**IPIP (IP-in-IP):** The simplest overlay — wrap an IP packet inside another IP packet (protocol 4). No UDP, no additional identifiers. Used in Kubernetes (Flannel IPIP mode, Calico IPIP mode) for simple pod-to-pod routing across nodes.

Advantage: Low overhead (20-byte outer IP header only). Disadvantage: No VNI/tenant identifier, so it only works for single-tenant environments where node-to-node isolation is enforced at another layer.

**GRE (Generic Routing Encapsulation):** Adds a 4-byte GRE header carrying a protocol type field and optional key (32-bit, used like a VNI). More overhead than IPIP, but more flexible. Used in some CNI plugins and VPN scenarios.

**Why IPIP/GRE vs VXLAN?**
- IPIP has less encapsulation overhead but no ECMP-friendly port diversity (no UDP src port variance). On modern 25/100GbE networks with RSS (Receive Side Scaling), this matters less.
- VXLAN is more universal (L2 over IP), IPIP is L3-only.
- For high-throughput, low-latency pod networking, Cilium in native-routing mode (no overlay at all) or eBPF-based routing is preferred.

### 4.5 WireGuard as an Overlay

WireGuard is increasingly used as an encrypted overlay in Kubernetes (Calico, Cilium support it). It operates at L3, uses modern cryptography (Curve25519, ChaCha20-Poly1305, BLAKE2s), and has a tiny attack surface.

**WireGuard's mental model:** It behaves like a virtual NIC. When a packet is sent to a peer's virtual IP, WireGuard looks up the peer's public key and endpoint, encapsulates the packet in UDP with authenticated encryption, and sends it. The receiving host decrypts, authenticates, and injects the inner packet into the kernel.

**Why it matters for cloud-native:** WireGuard provides encryption and authentication in the overlay itself, which means East-West encryption (pod-to-pod) without the complexity of a service mesh. The trade-off: it is a kernel-level construct, and key rotation, peer management, and revocation require a control plane (which CNI plugins provide).

---

## 5. Virtual Networking at the Host: vSwitch, vNIC, and Kernel Plumbing

### 5.1 The Linux Network Stack Fundamentals

Every cloud VM and container runs on a Linux host (or a host using Linux kernel constructs). The kernel network stack is the foundation:

**netfilter:** The in-kernel packet processing framework. Every packet flows through a series of **hooks** at predefined points in the network stack. The hooks are:
- `PREROUTING` — packet arrives from NIC before routing decision
- `INPUT` — packet destined for local process
- `FORWARD` — packet being forwarded (routed through this host)
- `OUTPUT` — packet generated by local process leaving
- `POSTROUTING` — packet after routing decision, before NIC transmit

**iptables** is the userspace interface to netfilter. It configures rules (match → action) at each hook. `nftables` is the modern replacement. Both use the same underlying netfilter framework.

**The packet flow:**
```
NIC RX → PREROUTING (DNAT/conntrack) → routing decision
    ↓ (local)                ↓ (forward)
  INPUT hook            FORWARD hook
    ↓                        ↓
 local process          POSTROUTING (SNAT) → NIC TX
    ↓
  OUTPUT hook
    ↓
POSTROUTING (SNAT) → NIC TX
```

This flow is the basis of every cloud networking construct: security groups are iptables/nftables rules; NAT is DNAT/SNAT in netfilter; load balancers manipulate connections at PREROUTING; Kubernetes kube-proxy rewrites service IPs at PREROUTING.

### 5.2 Connection Tracking (conntrack)

**conntrack** is the Linux kernel's stateful connection tracking table. It records every active connection (5-tuple: src IP, dst IP, src port, dst port, protocol) along with its state (NEW, ESTABLISHED, RELATED, INVALID).

Why conntrack matters:
- **NAT statefulness:** When SNAT rewrites the source IP of an outgoing packet, conntrack records the mapping. When the reply arrives, conntrack uses the mapping to reverse-NAT the destination back to the original source. Without conntrack, stateful NAT is impossible.
- **Security group enforcement:** AWS security groups, GCP firewall rules, and Azure NSGs are stateful — if you allow inbound traffic on port 80, return traffic is automatically allowed. This statefulness is implemented via conntrack.
- **Performance ceiling:** conntrack has a table size limit (`nf_conntrack_max`). Under high connection rates (DDoS, microservice fan-out), conntrack table exhaustion is a common failure mode. Symptoms: new connections fail with "table full" errors even when you have bandwidth.
- **TIME_WAIT accumulation:** TCP connections in TIME_WAIT state are held in conntrack for 4 minutes by default (2 × MSL). At scale, this creates memory pressure.

### 5.3 veth Pairs: The Universal Container/VM Network Link

A **veth pair** is a pair of virtual Ethernet interfaces linked together — what goes into one end comes out the other. They are the fundamental building block of container networking.

**How containers use veth pairs:**
1. The container runtime creates a veth pair: `veth0` and `veth1`
2. `veth1` is moved into the container's network namespace — it becomes the container's `eth0`
3. `veth0` stays in the host network namespace and is connected to a bridge or routing layer

Packets from the container go: container `eth0` → `veth1` → `veth0` (on host) → bridge/routing → destination.

**Why network namespaces matter:** Linux network namespaces give each container/VM a private, isolated view of the network stack — its own routing table, its own iptables rules, its own socket table. This is the kernel-level isolation primitive that containers rely on. It is **not** a security boundary equivalent to a hypervisor VM boundary — a container with `CAP_NET_ADMIN` can manipulate its own namespace, and namespace escapes have been found in the past (though the attack surface is narrower than often perceived).

### 5.4 Linux Bridge

A **Linux bridge** is a kernel software switch — it learns MAC addresses, maintains a forwarding table, and forwards frames between connected ports. When multiple veth pairs from containers are connected to a bridge, containers can communicate L2 (as if on the same Ethernet segment).

Limitations of Linux bridge:
- No hardware offload (unlike an ASIC switch)
- O(n) learning and forwarding for large numbers of ports
- No native support for VXLAN tunneling (requires external components like VXLAN FDB configuration)
- Participates in the STP (Spanning Tree Protocol) — but STP is usually disabled in container networking since bridges are created programmatically and loops are not expected

### 5.5 Open vSwitch (OVS)

**OVS (Open vSwitch)** is a production-grade, multi-layer virtual switch designed for VM/container networking. It supports:
- **OpenFlow:** A programmatic flow-table interface. A controller (like ONOS or the cloud provider's control plane) pushes match-action rules into OVS flow tables.
- **VXLAN/Geneve/GRE tunnels:** Native encapsulation/decapsulation as port types
- **OVSDB:** The control protocol for configuring OVS (bridges, ports, tunnels, mirrors)
- **DPDK acceleration:** OVS-DPDK bypasses the kernel, moving packet processing to userspace with DPDK for dramatically higher throughput and lower latency

OVS is the switching layer in OpenStack Neutron, many Kubernetes CNI plugins (OVN-Kubernetes), and legacy SDN deployments.

**The OVS flow pipeline:**
Packets traverse a pipeline of flow tables (table 0, 1, 2…). Each table contains flows with match fields and actions. A packet matches the first (highest-priority) rule in a table. Actions include: output to port, modify header, push/pop VLAN, set tunnel ID, send to next table, send to controller (slow path).

**Fast path vs slow path:** If OVS has a matching flow (cached in the kernel datapath), forwarding happens at line rate in the kernel without userspace involvement. If no flow matches, the packet is sent to the OVS userspace daemon (vswitchd) which consults OpenFlow rules and installs a new flow in the kernel datapath. The first packet of a new flow takes the slow path; subsequent packets take the fast path.

### 5.6 eBPF/XDP: The Modern Network Fast Path

**eBPF (extended Berkeley Packet Filter)** is a Linux kernel subsystem that allows running sandboxed programs at kernel hooks without modifying kernel source code. For networking, the key attachment points are:

- **XDP (eXpress Data Path):** Runs at the NIC driver level, before any kernel network stack processing. The earliest possible point — even before skb (socket buffer) allocation. XDP programs can drop, redirect, or modify packets at NIC receive time, achieving near-line-rate packet processing in software.
- **TC (Traffic Control) eBPF:** Runs at the traffic control subsystem, after skb allocation but before/after the network stack. Can modify packets, redirect them, or apply policy.
- **Socket-level eBPF:** Intercepts socket operations — can redirect connections between sockets without packets traversing the full network stack (used by Cilium for socket-level load balancing).
- **cgroup eBPF:** Attaches to cgroups and intercepts network operations at the cgroup level — used for per-pod network policy enforcement and bandwidth limiting.

**Cilium's networking model** is built entirely on eBPF. When a packet arrives at a node:
1. XDP/TC eBPF programs classify the packet
2. eBPF maps (in-kernel hash tables) store routing information, policy rules, and NAT state — consulted in O(1) without locking
3. The packet is forwarded, policy-dropped, or DNAT'd entirely in eBPF, bypassing iptables/conntrack
4. For East-West pod-to-pod traffic on the same node, eBPF redirects at the TC layer without the packet ever reaching the IP stack

The result: Cilium can achieve 3–4× higher throughput than iptables-based CNIs for high-connection-rate workloads, and lower tail latency because the lock-heavy conntrack table is avoided.

**XDP actions:**
- `XDP_DROP` — drop the packet immediately at the driver level (most efficient DDoS mitigation possible)
- `XDP_TX` — transmit the packet back out the same interface (for load balancers doing DSR)
- `XDP_REDIRECT` — redirect to another NIC, CPU, or userspace socket (AF_XDP)
- `XDP_PASS` — pass to the normal kernel network stack
- `XDP_ABORTED` — signal an error (counted in stats, packet dropped)

### 5.7 SR-IOV and Hardware Offload

**SR-IOV (Single Root I/O Virtualization)** is a PCIe standard that allows a single physical NIC to present multiple **Virtual Functions (VFs)** — each VF appears as a separate PCIe device to the OS. A VM or container can be assigned a VF directly, giving it hardware-level access to the NIC with minimal hypervisor involvement.

**PF (Physical Function):** The real NIC, controlled by the hypervisor. Manages VF creation, bandwidth limits, and VLAN assignment.
**VF (Virtual Function):** A lightweight PCIe device exposed to a guest. Has its own TX/RX queues, its own MAC/VLAN filter, its own PCIe BAR for register access.

**Security implications of SR-IOV:**
- A VF bypasses the hypervisor virtual switch — packets go directly from VM to hardware. This means the hypervisor cannot inspect or filter East-West traffic between VF-attached VMs (unless the SmartNIC/DPU enforces policy).
- If the PF driver is compromised, all VFs are compromised.
- DMA attacks: A VM with a VF can DMA directly to/from host memory mapped to the VF. IOMMU (VT-d/AMD-Vi) is mandatory with SR-IOV to ensure the VF's DMA is confined to its assigned memory regions. Without IOMMU, a compromised VM could potentially DMA into hypervisor memory.

**DPDK (Data Plane Development Kit):** A userspace library for high-speed packet I/O. DPDK polls NIC queues directly from userspace (no interrupt, no kernel involvement), uses huge pages for packet buffers, and pins threads to CPU cores. Achieves ~100 Mpps on modern hardware. Used in virtual routers (VPP, FD.io), OVS-DPDK, Envoy's high-throughput dataplane research, and SmartNIC programming.

**SmartNICs / DPUs (Data Processing Units):** The emerging paradigm for host networking. A SmartNIC contains its own CPU cores, memory, and programmable packet processing pipeline. AWS Nitro Card, NVIDIA BlueField, Marvell Octeon, Intel IPU are examples. The hypervisor offloads virtual switching, overlay encapsulation, security group enforcement, and storage I/O to the SmartNIC. The host CPU is entirely freed from network processing — this is how AWS achieves "bare-metal-like" EC2 performance even in multi-tenant environments.

---

## 6. Cloud Provider Virtual Networking Constructs

### 6.1 VPC (Virtual Private Cloud)

A VPC is a logically isolated, private network in a cloud provider region. It is the fundamental network isolation domain for cloud workloads.

**What a VPC actually is at the implementation level:** The cloud provider assigns your VPC a unique identifier (VNI or equivalent) in their overlay network. Every packet from your VPC is encapsulated with this identifier. The provider's physical fabric routes encapsulated packets between hosts, and only the host where your VMs run decapsulates and delivers the inner packet to your VM. Tenants with different VPCs can share physical hardware — their traffic is isolated by the encapsulation and VNI.

**Key VPC properties:**
- **Spans a region** (not a single AZ). You create subnets in specific AZs within the VPC.
- **Route table per subnet:** Every subnet is associated with a route table. The route table defines where traffic for each destination CIDR goes.
- **Internet Gateway:** A horizontally-scaled, HA device that performs NAT (for public IPs) and routes between your VPC and the internet. Not a single point of failure.
- **Virtual Private Gateway / VPN Gateway:** Entry point for VPN connections from on-premises.
- **Elastic Network Interface (ENI):** The virtual NIC that attaches to VMs. Has a primary private IP, optionally a public IP, and belongs to one or more security groups.

### 6.2 Security Groups

Security groups are **stateful** L3/L4 packet filters applied to ENIs (network interfaces). They are the primary perimeter security control for cloud workloads.

**Stateful means:** If you allow inbound TCP port 443, the return traffic (ESTABLISHED packets) is automatically allowed even with no explicit outbound rule for that port/connection.

**Implementation:** Security groups are implemented as iptables/nftables rules or equivalent on the hypervisor/host, applied to the traffic path of each ENI. When you add a rule to a security group, it is pushed to every host where a resource in that security group runs.

**Security group vs NACL (Network ACL):**
- Security groups: Stateful, applied at ENI level, allow-only (no explicit deny rules; default deny all)
- NACLs: Stateless, applied at subnet level, numbered rules evaluated in order with explicit allow and deny

NACLs are a subnet-level blunt instrument — useful for CIDR-level blocking but require explicit allow for return traffic. Security groups are the primary tool. Use NACLs for: blocking known-bad CIDRs, preventing lateral movement across subnets at the subnet boundary.

**Security group referencing:** You can reference another security group as the source/destination of a rule (instead of a CIDR). This means "allow traffic from any instance that belongs to security group X." This is dynamic — as instances join/leave the group, rules update. This is the right pattern for microservice-to-microservice rules: "allow the api-service security group to reach the db security group on port 5432."

### 6.3 VPC Peering

VPC peering creates a private network connection between two VPCs. Traffic between peered VPCs stays on the provider's backbone — never traverses the public internet.

**Critical constraint:** VPC peering is **non-transitive**. If VPC-A peers with VPC-B, and VPC-B peers with VPC-C, VPC-A cannot reach VPC-C via VPC-B. You need direct peering between A and C. This becomes operationally complex at scale (n² pairings).

**Routing:** After creating a peering, you must add routes to the route tables pointing destination CIDRs at the peering connection. Peering creates the plumbing; routes provide the directions.

**Security:** Peering itself does not open traffic — security groups and NACLs still apply. You have full control over which resources in each VPC can communicate.

### 6.4 Transit Gateway / Transit VPC

Transit Gateway (AWS), Cloud Router + VPC Peering (GCP), Virtual WAN (Azure) solve the n² peering problem by providing a **hub-and-spoke** routing model.

**Transit Gateway** is a cloud-managed router. VPCs attach to it (spoke). The TGW has route tables that define what traffic it forwards between attachments. You can:
- Segment routing (different route tables for different VPCs — production VPCs can't route to dev VPCs via TGW)
- Connect to on-premises via VPN or Direct Connect through the same TGW
- Share across accounts (RAM — Resource Access Manager)
- Multicast support

**What TGW actually is:** A highly available, distributed routing infrastructure run by the provider. Packets from a VPC attachment traverse the overlay, are processed by the TGW routing logic, and are forwarded to the destination VPC attachment. TGW bandwidth scales horizontally.

**Security model:** TGW route table segmentation is your primary East-West network isolation control in multi-VPC architectures. Default behavior: all attached VPCs can talk to each other. You must explicitly configure isolated route tables to prevent unauthorized VPC-to-VPC communication.

### 6.5 PrivateLink / Private Endpoints

**PrivateLink (AWS), Private Service Connect (GCP), Private Endpoints (Azure)** allow consuming a service over private IP without exposing it to the internet or requiring peering/routing between VPCs.

**How it works (AWS PrivateLink example):**
1. Service provider creates a **NLB** in front of their service
2. Provider creates an **Endpoint Service** backed by the NLB
3. Consumer creates a **VPC Endpoint (Interface type)** in their VPC, referencing the service
4. Cloud provider creates an ENI in the consumer's VPC with a private IP
5. Consumer's workloads connect to that private IP; traffic is proxy-forwarded to the provider's NLB via the provider's overlay

Traffic never traverses a public IP. The consumer's VPC routing is unaffected. Security groups control access to the endpoint ENI. This is the right pattern for: consuming AWS services (S3, DynamoDB via Gateway Endpoints, etc.), multi-tenant SaaS architectures, and cross-account service access.

**Security advantage:** PrivateLink is unidirectional — the consumer can reach the provider's service, but the provider has no network path into the consumer's VPC. This is critical for SaaS consumption: you need the SaaS, but you don't want the SaaS vendor to have network access to your environment.

### 6.6 NAT Gateway

NAT Gateway (cloud-managed SNAT) allows resources in private subnets to initiate outbound connections to the internet while remaining unreachable from inbound internet connections.

**How it works:** NAT GW has a public IP (Elastic IP). When a private resource initiates a connection to an internet destination, the NAT GW rewrites the source IP to its own public IP and records the mapping in its connection tracking table. When the reply arrives, NAT GW reverse-maps back to the original private IP and forwards.

**NAT GW in the routing table:** The private subnet's route table has a default route (`0.0.0.0/0`) pointing to the NAT Gateway (which lives in a public subnet). The NAT Gateway's route table has a default route to the Internet Gateway.

**Failure modes:**
- NAT GW is AZ-scoped — if you have private subnets in 3 AZs, you need 3 NAT Gateways (one per AZ) for HA. Using a single NAT GW means all outbound traffic from other AZs crosses AZ boundaries (costs money and adds latency), and if that AZ fails, the other AZs lose outbound internet access.
- NAT GW has per-connection limits. At very high connection rates (IoT, batch jobs), NAT port exhaustion is a real failure mode.

### 6.7 DNS in Cloud

DNS is the service discovery mechanism for virtually everything. Understanding cloud DNS is non-optional.

**Route 53 / Cloud DNS / Azure DNS:** The cloud-managed authoritative DNS services. They serve your public and private zones.

**Private DNS / Split-horizon DNS:**
- A **private hosted zone** resolves DNS names only from within a VPC.
- The **VPC resolver** (169.254.169.253 on AWS, metadata address) is the DNS server for all queries from EC2 instances.
- Internal service names (e.g., `api.internal.example.com`) resolve to private IPs within the VPC. External resolvers get no answer (or a different answer).

**Why DNS is a security concern:**
- DNS is often completely unrestricted (UDP/TCP port 53 outbound) while other ports are blocked. DNS tunneling exfiltrates data as DNS query payloads.
- DNS cache poisoning: If you use a forwarder that is vulnerable, or if DNSSEC is not enforced, an attacker can poison cached records.
- Cloud metadata API often accessible via DNS name — `169.254.169.254` (link-local) or via a DNS name. Any workload that can poison DNS can redirect metadata API traffic.
- **Route 53 Resolver DNS Firewall** (AWS) or equivalent provides DNS filtering — block queries to known-malicious domains, allow-list specific domains for sensitive workloads.

**CoreDNS in Kubernetes:**
CoreDNS is the cluster DNS server for Kubernetes. It serves the `cluster.local` domain, resolving service names (`service.namespace.svc.cluster.local`) to ClusterIPs (virtual service IPs), and pod hostnames to pod IPs.

The CoreDNS resolution chain:
1. Pod queries CoreDNS for `api.default.svc.cluster.local`
2. CoreDNS looks up the service in its Kubernetes plugin (watches the API server)
3. Returns the ClusterIP for the service
4. Pod connects to ClusterIP; kube-proxy (iptables/IPVS) or Cilium (eBPF) DNAT's the connection to a pod IP

**CoreDNS security:** CoreDNS pods should be protected by NetworkPolicy. DNS amplification is possible — a pod can query CoreDNS with queries that generate large responses, creating a DoS vector. Rate limiting at CoreDNS (via the `ratelimit` plugin) and network-level rate limiting are mitigations.

---

## 7. Load Balancing: L4 and L7

### 7.1 Layer 4 (Transport Layer) Load Balancing

L4 load balancing operates on TCP/UDP 5-tuples. The load balancer makes forwarding decisions based on IP and port without inspecting the application payload.

**How L4 LB works:**
1. Client connects to the LB's VIP (Virtual IP)
2. LB selects a backend (using a scheduling algorithm: round-robin, least-connections, hash)
3. LB forwards the connection to the backend

**Two modes:**

**NAT/DNAT mode:** LB rewrites the destination IP of each packet from VIP to backend IP. The backend receives packets with its own IP as destination. Return traffic must come back through the LB (which reverses the NAT). Requires LB to be in the return path (stateful).

**DSR (Direct Server Return):** LB changes the destination MAC to the backend's MAC (L2 reachability required) but leaves the destination IP as the VIP. The backend processes the request and sends the response directly to the client (bypassing the LB). Only the request traffic goes through the LB; response (usually larger) goes directly. Massively increases LB throughput. Used in high-throughput scenarios (CDNs, gaming). Requires backends to have the VIP configured on a loopback (so they accept packets destined for VIP but don't respond to ARP for it).

**AWS Network Load Balancer (NLB):** Implemented using the same hypervisor infrastructure as the rest of VPC networking. Traffic from the client reaches the NLB, which selects a backend and forwards via flow hash (for TCP stickiness). NLB preserves the client source IP by default (unlike ALB which uses proxy headers).

### 7.2 Layer 7 (Application Layer) Load Balancing

L7 load balancing terminates the client connection at the LB and establishes a new connection to the backend. The LB can inspect and manipulate HTTP headers, URLs, cookies, and bodies.

**Why L7 LB?**
- Content-based routing: Route `/api/*` to the API backend, `/static/*` to a CDN or static server
- TLS termination: Decrypt TLS at the LB, forward plaintext to backends (or re-encrypt)
- Header manipulation: Add `X-Forwarded-For`, `X-Request-ID`; modify `Host`
- Session affinity (sticky sessions): Use cookie-based or source-IP-based hashing to route a client's requests to the same backend
- Health checking at the HTTP level: Check `/health` endpoints, not just TCP reachability
- Circuit breaking: Stop sending traffic to backends that return errors

**The trade-off:** L7 LB is CPU-intensive (TLS handshakes, HTTP parsing). For extremely high throughput, L4 LB scales better. The pattern: L4 LB in front for raw TCP throughput and DDoS resilience, L7 LB (reverse proxy like Envoy, nginx) behind for application-level routing.

### 7.3 IPVS (IP Virtual Server)

IPVS is a Linux kernel L4 load balancer, part of the netfilter framework. It is the backend for Kubernetes kube-proxy in IPVS mode.

IPVS maintains a connection table in the kernel hash table (O(1) lookup vs iptables O(n) linear rule traversal). It supports multiple scheduling algorithms: round-robin, weighted round-robin, least-connection, shortest expected delay, never queue.

**Why IPVS vs iptables for Kubernetes:** With thousands of services, iptables rules become a linear list — `O(n)` to evaluate, and every rule add/delete requires a full iptables lock and rewrite. IPVS uses a hash table — O(1) lookup regardless of number of services/endpoints. At 10,000+ services, IPVS mode is significantly faster for connection setup.

### 7.4 Envoy Proxy: The Universal L7 Data Plane

Envoy (CNCF project) is the dominant L7 proxy in cloud-native networking. It is the data plane for Istio, AWS App Mesh, and many other service meshes.

**Envoy's architecture:**
- **Listeners:** Network endpoints that accept connections (like a port binding). Each listener has a filter chain.
- **Filters:** Modular processing pipeline. Network filters process at TCP level (e.g., HTTP/1.1, HTTP/2, gRPC codecs). HTTP filters process at HTTP level (router, rate limiter, CORS, JWT auth).
- **Clusters:** Upstream backend groups. Each cluster has a set of endpoints (IP:port), a load balancing policy, and health checking configuration.
- **xDS API:** Envoy's control plane API. xDS (CDS, EDS, LDS, RDS) are dynamic configuration APIs — a control plane (like Istio's istiod) pushes configuration to Envoy without restart. This is how service mesh control planes manage Envoy sidecars at scale.

**Envoy's key capabilities for cloud-native security:**
- **mTLS:** Envoy can terminate and originate mTLS, validating peer certificates from the SPIFFE/X.509 certificate issued by the mesh control plane
- **RBAC filter:** Policy-based access control at the L7 layer — "allow requests from service A to path /api/v1/* with method GET"
- **Rate limiting:** Local and global rate limiting via external gRPC rate limit service
- **Circuit breaking:** Configured per cluster — max pending requests, max connections, max retries, panic threshold
- **Outlier detection:** Automatically eject unhealthy endpoints from rotation based on error rates

---

## 8. Container Networking: CNI and the Kubernetes Network Model

### 8.1 The Kubernetes Network Model

Kubernetes defines a flat networking model with three requirements:
1. **Every pod has a unique IP address** (no NAT between pods)
2. **Pods on any node can communicate with pods on any other node without NAT**
3. **Agents on a node (like kubelet) can communicate with all pods on that node**

This model simplifies application configuration — applications assume they can connect to any pod IP directly, without NAT or port mapping. The CNI plugin is responsible for implementing this model.

**What this means in practice:** A pod IP is routable to every other pod in the cluster. The question is *how* — different CNI plugins implement this differently (routes, tunnels, eBPF maps), but the pod-to-pod communication guarantee is the same.

### 8.2 CNI (Container Network Interface)

CNI is a specification and library for configuring network interfaces in Linux containers. When a pod is created:
1. kubelet creates the pod's network namespace
2. kubelet calls the CNI plugin binary (or gRPC socket) with the `ADD` command
3. The CNI plugin configures: creates veth pair, assigns IP from IPAM, sets up routes, configures iptables/eBPF rules
4. When the pod is deleted, kubelet calls the CNI plugin with `DEL`

CNI plugins are chained — you can have a main plugin (handles connectivity) and meta-plugins (handle bandwidth, port mapping, etc.).

**Major CNI plugins and their approaches:**

**Flannel:** Simplest. Uses VXLAN by default (or IPIP, or host-gw). Each node gets a /24 subnet from the cluster CIDR. Flannel daemon watches the Kubernetes API for node additions and configures VXLAN FDB entries or routes to reach pods on other nodes. No network policy support — must pair with a policy enforcer.

**Calico:** Supports both overlay (VXLAN, IPIP) and non-overlay (BGP with host routes) modes. In BGP mode, Calico runs a BGP daemon (BIRD or GoBGP) on every node and advertises pod CIDRs via BGP — routers learn how to reach pods directly. No encapsulation overhead. Calico has its own network policy engine (uses iptables/eBPF) and extends Kubernetes NetworkPolicy with `GlobalNetworkPolicy` and `NetworkSet` resources.

**Cilium:** eBPF-native. No iptables — all policy and forwarding implemented in eBPF. Supports both overlay (VXLAN, Geneve) and native routing modes. Provides:
- L3/L4/L7 network policy (HTTP, gRPC, Kafka-aware policy rules)
- Transparent encryption (WireGuard or IPsec per-node)
- Clustermesh (multi-cluster pod connectivity)
- Hubble (eBPF-based network observability)
- Replacing kube-proxy entirely (eBPF handles ClusterIP → PodIP translation)

**OVN-Kubernetes:** Based on OVN (Open Virtual Network) and OVS. Uses OVN's distributed logical network constructs (logical switches, logical routers) to implement Kubernetes networking. The northbound database holds logical topology; OVN controllers compile it to OpenFlow rules in OVS on each node.

### 8.3 IPAM (IP Address Management) in Kubernetes

IPAM is how pod IP addresses are allocated. The cluster CIDR (e.g., `10.244.0.0/16`) is divided among nodes. Each node gets a portion (e.g., `/24`). When a pod is created, the CNI plugin allocates an unused IP from the node's subnet.

**IPAM approaches:**
- **Host-local:** A simple file-based IPAM on each node. Tracks allocated IPs in `/var/lib/cni/networks/`. Fast, simple, no external dependency.
- **Centralized (Calico, Cilium):** A controller manages IP allocation across all nodes from a central store (etcd or Kubernetes CRDs). Allows for more flexible block sizes and cross-node IP reuse.
- **Cloud provider IPAM:** AWS VPC CNI, GKE's VPC-native mode allocate pod IPs from the actual VPC subnet — pods are first-class citizens in the VPC routing table. The advantage: pods are directly reachable from the VPC without any overlay. The limitation: you consume VPC IP space for every pod, requiring careful CIDR planning.

### 8.4 Kubernetes Network Policy

Kubernetes `NetworkPolicy` is the L3/L4 policy API for pod-to-pod communication. It is enforced by the CNI plugin.

**Key semantics:**
- Policies are **namespace-scoped** and **pod-selector-based**
- A pod is **isolated** in a direction (ingress or egress) once any NetworkPolicy selects it with a `policyTypes` matching that direction
- **Default-deny:** In the absence of any NetworkPolicy, all traffic is allowed. Once you apply a NetworkPolicy to a pod, only explicitly allowed traffic passes.
- Rules are **allow-only** — no explicit deny rules in the core spec

**Policy selection model:**
```
podSelector: selects which pods this policy applies to
ingress:
  - from:
      - namespaceSelector: selects source namespaces
      - podSelector: selects source pods
    ports: which ports to allow
egress:
  - to:
      - ipBlock: CIDR range
    ports: which ports to allow
```

**Critical subtlety:** Both `namespaceSelector` and `podSelector` in a single `from` entry are ANDed — "pods in namespace X AND with label Y." If specified as separate list items, they are ORed.

**Limitations of Kubernetes NetworkPolicy:**
- No L7 awareness (HTTP paths, gRPC methods) — need Cilium L7 policy or service mesh for this
- No deny rules — can't explicitly block a specific source
- No FQDN/DNS-based rules — need Calico or Cilium for egress DNS-based policy
- No cluster-scoped policies (only namespace-scoped) — need Cilium `ClusterwidNetworkPolicy` or Calico `GlobalNetworkPolicy`

### 8.5 Service Networking: ClusterIP, NodePort, LoadBalancer

**ClusterIP:** A virtual IP assigned to a Service. It is only reachable within the cluster. kube-proxy (or Cilium eBPF) programs DNAT rules — packets to the ClusterIP are DNAT'd to one of the backend pod IPs. The ClusterIP doesn't correspond to any real interface — it's a floating address implemented purely in NAT rules.

**Why ClusterIP is virtual:** The ClusterIP is in the `--service-cluster-ip-range`, a range that is never routed to any node directly. It's caught by iptables PREROUTING rules and DNAT'd before the kernel makes a routing decision. This is an elegant hack that provides stable service IPs even as pods come and go.

**NodePort:** Exposes a service on every node's IP on a static port (range 30000–32767). Traffic to `<any-node-IP>:<node-port>` is DNAT'd to the service's backend pods. NodePort is the mechanism underlying LoadBalancer-type services — the cloud load balancer sends traffic to NodePorts on the instances in the backend pool.

**LoadBalancer:** Requests a cloud provider load balancer (AWS NLB/ELB, GCP GLB) automatically provisioned and configured to forward traffic to the NodePorts of the Kubernetes cluster. The cloud LB is external to the cluster; NodePort is the cluster-internal mechanism it uses.

**Headless Services:** ClusterIP: None. No virtual IP is assigned. DNS resolution for the service returns the pod IPs directly. Used for stateful sets, databases, and any workload that needs direct pod addressing. DNS returns multiple A records — clients do their own load balancing or connection selection.

### 8.6 Service Mesh: Istio and the Sidecar Model

A service mesh provides L7 observability, traffic management, and security (mTLS) for service-to-service communication, without requiring application code changes.

**The sidecar model:**
- An Envoy proxy sidecar container is injected into every pod (via mutating webhook admission controller)
- iptables rules (via an init container) redirect all inbound and outbound traffic to the Envoy proxy
- The application sends traffic to `localhost:service-port`; iptables redirects it to Envoy's outbound listener
- Envoy applies policy, encrypts (mTLS), load balances, and forwards to the destination pod's Envoy sidecar
- The destination Envoy decrypts, applies inbound policy, and delivers to the local application

**The control plane (Istiod):**
- Watches Kubernetes API for service and endpoint changes
- Issues X.509 certificates (SVID) to sidecars via the xDS API
- Pushes routing configuration (VirtualService, DestinationRule) to sidecars as xDS updates
- Collects telemetry (Prometheus metrics, distributed traces) from sidecars

**mTLS in service mesh:**
- Both client and server present certificates during TLS handshake
- Certificates are **SPIFFE** (Secure Production Identity Framework for Everyone) format: `spiffe://<trust-domain>/ns/<namespace>/sa/<service-account>`
- The mesh CA (Istiod by default, or an external CA via cert-manager) signs these certificates
- Policy is based on the SPIFFE identity — "allow traffic from service account `api-service` to service account `db-service`"
- This is identity-based policy rather than IP-based — it is robust to pod IP churn and doesn't require network segmentation for enforcement

**Ambient mesh (Istio ambient mode):** The emerging sidecar-less model. Instead of a sidecar per pod, a per-node eBPF-based proxy (ztunnel, a Rust implementation) handles L4 mTLS. L7 processing is handled by a per-namespace waypoint proxy (full Envoy). This eliminates sidecar overhead and injection complexity while retaining security guarantees.

---

## 9. Routing Protocols and BGP in Cloud

### 9.1 BGP (Border Gateway Protocol) — Deep Dive

BGP is the routing protocol of the internet and increasingly of cloud internals. It is a path-vector protocol: routes carry the full AS path (list of Autonomous Systems traversed) as a loop-prevention mechanism.

**iBGP vs eBGP:**
- **iBGP (Internal BGP):** BGP sessions within the same AS. Used for route reflection within a data center.
- **eBGP (External BGP):** BGP sessions between different ASes. Used for internet routing and cloud provider peering.

**BGP attributes (what determines route selection):**
1. Weight (Cisco-proprietary, local to router)
2. Local Preference (iBGP, higher is preferred) — used to prefer one path over another within an AS
3. AS Path length (shorter is preferred)
4. Origin (IGP > EGP > Incomplete)
5. MED (Multi-Exit Discriminator) — hint to neighboring AS about preferred ingress point
6. eBGP over iBGP
7. IGP metric to next hop

**BGP communities:** 32-bit tags attached to route advertisements. Used to communicate policy between BGP peers. Examples:
- `NO_EXPORT` (65535:65281): Don't advertise this route to eBGP peers
- `NO_ADVERTISE` (65535:65282): Don't advertise to any peer
- Provider-defined: AWS uses communities to tag routes with origin region/AZ information

**BGP in Kubernetes (Calico BGP mode):**
Each node's Calico agent runs a BGP daemon that peers with:
- Other nodes (full mesh for small clusters, or route reflectors for large clusters)
- Top-of-rack switches (for integration with physical network)

The node advertises its pod CIDR via BGP. Physical switches learn pod CIDRs as reachable via the node's IP. No encapsulation is needed — pods are natively routable on the physical network.

### 9.2 OSPF and Its Role

OSPF (Open Shortest Path First) is a link-state IGP. Each router floods its link-state advertisements (LSAs) to all routers in the area, building an identical LSDB (Link State Database). SPF (Dijkstra's algorithm) runs locally to compute shortest paths.

**Where OSPF appears in cloud:**
- Some on-premises data centers still use OSPF internally
- VPN appliances often redistribute routes from/to OSPF ↔ BGP
- Direct Connect / ExpressRoute connectivity involves BGP with the cloud provider, but the internal enterprise network may use OSPF redistributed into BGP

OSPF is less common in modern cloud-native contexts (which prefer BGP everywhere), but you'll encounter it in hybrid connectivity scenarios.

### 9.3 Cloud Router and Hybrid Connectivity

**AWS Direct Connect / GCP Interconnect / Azure ExpressRoute** are dedicated physical connections between enterprise premises and cloud. They bypass the public internet entirely — lower latency, consistent bandwidth, no exposure to internet routing instability.

**BGP is mandatory** over these connections. The enterprise network and the cloud provider's edge router establish an eBGP session over the dedicated link:
- Enterprise advertises on-premises prefixes to the cloud
- Cloud advertises VPC/VNet prefixes to the enterprise
- Route filtering on both sides is critical — the enterprise must only accept expected cloud prefixes, and the cloud must only accept expected on-premises prefixes. A misconfigured route filter that accepts a default route from the enterprise could blackhole all cloud traffic.

**Cloud Router (GCP) / Virtual Private Gateway (AWS):** The cloud-side BGP endpoint. These are managed services — you configure the BGP ASN, neighbor IPs, and route advertisement policy; the cloud provider runs the BGP daemon.

---

## 10. Network Security Constructs

### 10.1 Defense-in-Depth Layers

```
[Internet]
    ↓
[DDoS Mitigation — AWS Shield/GCP Cloud Armor/Azure DDoS Protection]
    ↓
[WAF — Web Application Firewall — L7 filtering]
    ↓
[Load Balancer — public ALB/NLB]
    ↓
[Security Group / NSG — stateful L4 filter on ENI]
    ↓
[NACL — stateless subnet-level ACL]
    ↓
[Workload (EC2/Pod/Container)]
    ↓ (for containers)
[Kubernetes NetworkPolicy — pod-level L3/L4]
    ↓
[Service Mesh mTLS + RBAC — L7 identity-based]
```

Each layer has different granularity, statefulness, and enforcement point. The goal is that compromising one layer does not automatically compromise the next.

### 10.2 Zero Trust Network Architecture

Zero Trust is a security model based on the principle "never trust, always verify." In traditional perimeter security, traffic inside the network perimeter is trusted. In Zero Trust:
- Every request is authenticated and authorized regardless of network origin
- Lateral movement is prevented even if an attacker reaches the internal network
- Strong identity (certificates, tokens) replaces network location as the trust anchor

**How this maps to cloud-native networking:**
- **Workload identity:** Pods/VMs have cryptographic identities (SPIFFE SVIDs, IAM roles, service accounts) rather than IP addresses as their identity
- **mTLS everywhere:** All service-to-service communication is mutually authenticated and encrypted
- **Authorization at every hop:** Not just at the perimeter — each service checks whether the caller is authorized to make this specific request
- **Microsegmentation:** NetworkPolicy + service mesh policy ensures each pod can only communicate with the services it explicitly needs
- **No implicit trust:** Even pod-to-pod communication within a namespace must be explicitly authorized

**BeyondProd (Google's implementation):** Google Cloud's internal security model, which informed Cloud IAP and GKE's security features. Services have identities (via LOAS credentials), all communication is over ALTS (Application Layer Transport Security, Google's equivalent of mTLS), and service meshes enforce access control based on service identity. No service implicitly trusts another just because they're on the same network.

### 10.3 Network Encryption: In-Transit

**TLS (Transport Layer Security):** The universal standard for encrypting in-transit data. TLS 1.3 is mandatory for all new deployments — it eliminates weak cipher suites, provides forward secrecy (ephemeral key exchange), and reduces handshake round trips from 2 to 1.

**TLS termination points:**
- **Edge TLS:** Terminate at the load balancer (ALB, nginx). Traffic from LB to backend is plaintext. Easier to manage certificates, but internal traffic is unencrypted.
- **End-to-end TLS:** Backend re-encrypts to the origin service. Certificates at every hop. Higher CPU cost but encrypted even on the internal network.
- **mTLS:** Mutual — both sides present certificates. The server verifies the client's identity. Required for service mesh security.

**IPsec:** Network-layer encryption. Operates at IP layer — encrypts all traffic between hosts regardless of protocol. Two modes:
- **Transport mode:** Encrypts only the payload; IP headers remain. Used for host-to-host encryption.
- **Tunnel mode:** Encrypts the entire original IP packet and adds a new outer IP header. Used for VPN tunnels (site-to-site VPN, IPsec over Direct Connect).

IPsec has two sub-protocols:
- **AH (Authentication Header):** Provides integrity and authentication (no encryption)
- **ESP (Encapsulating Security Payload):** Provides encryption + integrity + authentication

**IKE (Internet Key Exchange):** The control protocol for IPsec. IKEv2 is current standard. Negotiates the cipher suites, exchanges keys (Diffie-Hellman), and establishes Security Associations (SAs). SAs are the agreed-upon parameters for an IPsec session.

**WireGuard:** Modern, minimal VPN protocol. ~4000 lines of code (vs ~100K for OpenVPN). Uses fixed modern crypto: Curve25519 for key exchange, ChaCha20-Poly1305 for encryption, BLAKE2s for hashing. UDP-based, stateless handshake. Used in Cilium and Calico for East-West encryption in Kubernetes.

### 10.4 DDoS Mitigation

**Volumetric attacks:** Saturate bandwidth (UDP flood, ICMP flood, amplification attacks). Mitigation requires upstream scrubbing at provider network edges — more bandwidth than any single customer can provide.

**Protocol attacks:** Exploit TCP/IP weaknesses (SYN flood, Smurf). SYN cookies is the canonical defense — the server generates a cryptographic cookie in the SYN-ACK, requiring no state until the ACK is received. This defeats SYN flood without memory exhaustion.

**Application-layer attacks (L7):** Mimic legitimate traffic (HTTP GET flood, Slowloris). Require L7 inspection to detect — WAF, rate limiting, behavioral analysis.

**Cloud DDoS protection:**
- **AWS Shield Standard:** Always-on at network edge (BGP-level filtering of known-bad traffic)
- **AWS Shield Advanced:** L7 DDoS response team, traffic engineering, cost protection
- **GCP Cloud Armor:** WAF + DDoS, rate limiting at the Google Front End (GFE) before traffic reaches your GCP resources
- **Cloudflare, Akamai:** CDN-based scrubbing — traffic routed through their global anycast network, malicious traffic dropped before reaching origin

**Anycast for DDoS resilience:** Announcing the same IP prefix from multiple geographic locations via BGP. Client traffic is naturally routed to the nearest PoP (Point of Presence). A DDoS attack is distributed across all PoPs — no single site is overwhelmed. This is how Cloudflare, AWS CloudFront, and GCP's global load balancer work.

### 10.5 Network Observability

**VPC Flow Logs (AWS) / VPC Flow Logs (GCP) / NSG Flow Logs (Azure):**
Records metadata (not payload) for every network flow: source/dest IP, port, protocol, bytes, packets, accept/reject. Stored in CloudWatch Logs, S3, or BigQuery. Used for:
- Security investigation (which source IP is making connections to port 22?)
- Traffic pattern analysis
- Compliance (demonstrating only authorized traffic reaches production)

Flow logs do **not** capture payload content — for deep packet inspection, you need a network tap or a proxy with TLS interception.

**eBPF-based observability (Hubble/Cilium):**
Hubble operates in the kernel via eBPF hooks, capturing per-flow metadata without any packet copying overhead:
- Source/destination pod identities (not just IPs — actual Kubernetes labels)
- L7 protocol information (HTTP status codes, DNS queries, gRPC method names)
- Policy verdict (allowed/dropped by which policy)
- Latency per flow

This gives you the visibility of a network tap with the context of Kubernetes metadata — you can answer "which pods are calling the payment service and getting 500 errors?"

**Packet capture and tcpdump/Wireshark:** For debugging, you need raw packet captures. In Kubernetes, this means entering the pod's network namespace (`nsenter`) and running tcpdump on the pod's `eth0`. On the host, you capture on the `veth` pair's host-side interface to see all traffic to/from a pod (including traffic that is policy-dropped, since drops happen after the packet is received).

---

## 11. Ingress, Egress, and API Gateway Patterns

### 11.1 Kubernetes Ingress

Kubernetes Ingress is the L7 HTTP/HTTPS routing API for cluster workloads. It allows a single load balancer entry point to route to multiple services based on host name and URL path.

**How it works:**
1. An Ingress controller (nginx-ingress, AWS ALB Ingress, Traefik, etc.) is deployed in the cluster
2. Ingress resources define routing rules: `host: api.example.com, path: /v1/* → service: api-service:80`
3. The Ingress controller reconciles Ingress resources and programs its proxy (nginx, Envoy) accordingly
4. External traffic hits the load balancer → Ingress controller → backend service

**Ingress is being superseded by Gateway API:** The Kubernetes Gateway API is a more expressive, extensible replacement with better role separation (cluster operator manages Gateway infrastructure; developers manage routing via HTTPRoute, TCPRoute, etc.).

### 11.2 Egress Control

Egress control — what outbound connections workloads can make — is often neglected relative to ingress. It is a critical security control:
- Data exfiltration happens via egress (DNS exfiltration, HTTP POST to external attacker server)
- Supply chain attacks often beacon home via egress
- Compromised workloads establish C2 (command and control) channels via egress

**Egress controls:**
- **NetworkPolicy egress rules:** Block pod-to-external-IP connections at the CNI level
- **DNS-based egress policy (Cilium/Calico):** Allow only specific FQDNs, block all others. Requires intercepting DNS responses to program IP-based rules dynamically.
- **Egress gateway:** Force all egress traffic through a dedicated proxy (e.g., a Squid proxy or Envoy egress gateway in Istio). The proxy enforces allowlist of external hosts.
- **NAT Gateway + Security Group:** Only allow the NAT Gateway's IP to reach the internet — but this doesn't control which external destinations are reachable, only which VPCs have internet access.
- **AWS VPC Endpoints / GCP Private Google Access / Azure Private Endpoints:** Allow workloads to reach cloud services (S3, BigQuery, etc.) without internet egress — traffic stays on the provider backbone.

---

## 12. Multicloud and Hybrid Networking

### 12.1 SD-WAN (Software-Defined WAN)

SD-WAN abstracts WAN links (MPLS, broadband, 4G/5G) into a policy-driven overlay. Traffic is routed based on application type, link quality, and policy — not static routing tables.

**Relevance for cloud:** Many enterprises use SD-WAN to connect branch offices and data centers to cloud. The SD-WAN controller programs edge devices to route different traffic types over optimal paths — e.g., SaaS traffic (Office 365, Salesforce) directly to the internet, enterprise application traffic over MPLS to data center.

### 12.2 Cloud Interconnect vs VPN

| | Site-to-site VPN | Dedicated Interconnect |
|---|---|---|
| **Transport** | Encrypted over public internet | Dedicated physical link |
| **Bandwidth** | Typically < 1.25 Gbps per tunnel | 10 Gbps or 100 Gbps |
| **Latency** | Variable (internet routing) | Consistent (dedicated path) |
| **Cost** | Low (no circuit cost) | High (circuit + port fees) |
| **Setup time** | Minutes | Weeks (physical provisioning) |
| **Security** | IPsec encryption | Link-level security (provider SLA), no encryption by default |

**When to use VPN:** Dev/test environments, low-bandwidth requirements, quick setup, budget-constrained.
**When to use Direct Connect/Interconnect:** Production data, compliance requirements (data must not traverse internet), consistent latency for latency-sensitive applications, high bandwidth (bulk data transfer, replication).

### 12.3 Multi-Cloud Networking

Connecting workloads across AWS, GCP, and Azure requires:
1. **Routing:** Each cloud has its own private addressing. You need either overlapping-free address planning and transit routing, or overlay networks that span clouds.
2. **DNS:** A unified DNS namespace that resolves names from any cloud. Often implemented with a forwarding hierarchy: each cloud's resolver forwards queries for cross-cloud names to a shared resolver (e.g., Route 53 in the middle, or a dedicated resolver like Consul).
3. **Security:** Each cloud has its own IAM, security groups, and compliance controls. Workload identity must be federated (SPIFFE trust federation allows meshes in different clouds to trust each other's certificates).
4. **Overlay:** Tools like Consul Connect, Cilium Clustermesh, and commercial platforms (Aviatrix, Alkira) provide mesh connectivity across clouds.

---

## 13. IPv6 in Cloud: Dual-Stack and the Transition

### 13.1 Why IPv6 Matters

IPv4 exhaustion is real — cloud providers allocate NAT'ed private IPs because public IPv4 addresses are scarce and expensive. IPv6 provides 2^128 addresses — every device can have a globally routable address.

**Cloud IPv6 reality:**
- GCP has had IPv6-native VPCs for years
- AWS supports dual-stack (IPv4 + IPv6) in VPCs; IPv6-only subnets are now supported
- Azure supports dual-stack as well
- Kubernetes has dual-stack support (pods get both IPv4 and IPv6 addresses)

### 13.2 Dual-Stack Complexity

**Dual-stack networking** means every interface has both an IPv4 and IPv6 address. Applications must handle both address families, and policy must be applied consistently to both.

**Security challenges:**
- Security groups and NACLs must be configured for both IPv4 and IPv6. Forgetting IPv6 rules creates security holes — an attacker can reach the service via IPv6 even if IPv4 is blocked.
- Many monitoring and logging tools don't yet have full IPv6 observability
- Link-local addresses (`fe80::/10`) exist on every IPv6 interface and are auto-configured — they can be used for local communication even if you haven't configured any global IPv6 addresses

### 13.3 NDP (Neighbor Discovery Protocol)

IPv6 replaces ARP with NDP (Neighbor Discovery Protocol), using ICMPv6 messages:
- **Router Solicitation/Advertisement:** Hosts discover routers and get prefix information
- **Neighbor Solicitation/Advertisement:** Like ARP — maps IPv6 addresses to MAC addresses
- **SLAAC (Stateless Address Autoconfiguration):** Hosts generate their own IPv6 global address using the router-advertised prefix + their interface identifier

**NDP spoofing** is the IPv6 equivalent of ARP poisoning. A malicious host can send fake Router Advertisements to redirect traffic. Mitigation: RA Guard (switch-level protection that drops Router Advertisements from non-router ports), SEND (Secure Neighbor Discovery), and cloud hypervisor-level RA/NS filtering.

---

## 14. Network Performance Engineering

### 14.1 Throughput, Latency, and the Fundamental Trade-offs

**Bandwidth:** The maximum data transfer rate. Constrained by the slowest link in the path (NIC, switch port, uplink).

**Latency:** The time for a packet to travel from source to destination. In a cloud data center, physical propagation is microseconds; kernel processing adds hundreds of microseconds. Speed of light across a continent: ~30ms.

**Jitter:** Variation in latency. Caused by: ECMP hash collisions (micro-congestion), interrupt coalescing, CPU scheduling, GC pauses. Jitter is often more damaging than raw latency for real-time applications.

**The bandwidth-delay product:** `BDP = bandwidth × RTT`. This is the amount of data "in flight" in the network for a single TCP connection. For a 10 Gbps link with 10ms RTT: BDP = 125 MB. The TCP window must be at least this large to fully utilize the link. Default TCP buffers are often too small for high-BDP paths — requires TCP window scaling and appropriate socket buffer tuning.

### 14.2 TCP Congestion Control

TCP has multiple congestion control algorithms that affect throughput on modern cloud networks:

**CUBIC (Linux default):** Increases window size cubically after loss events. Designed for high-BDP paths. Works well in data centers but can be aggressive in WAN scenarios.

**BBR (Bottleneck Bandwidth and RTT):** Google's model-based congestion control. Estimates available bandwidth and RTT, targets the pipe's bandwidth-delay product. Significantly better than CUBIC for satellite, cellular, and long-haul WAN links. Used by Google for all internal traffic and available in Linux kernel. GCP recommends BBR for inter-region traffic.

**QUIC:** A transport protocol built on UDP, developed by Google, now an IETF standard (RFC 9000). Provides:
- 0-RTT connection establishment (for repeat connections)
- Multiplexed streams without head-of-line blocking (unlike HTTP/2 over TCP)
- Connection migration (survives IP address changes — useful for mobile clients)
- Integrated TLS 1.3

QUIC is what HTTP/3 uses. It's increasingly used in cloud-native contexts for high-performance APIs.

### 14.3 RSS, RPS, RFS: Scaling Packet Processing

**RSS (Receive Side Scaling):** Hardware feature. The NIC hashes incoming packets by flow tuple and distributes them across multiple receive queues, each serviced by a different CPU core. Eliminates the single-CPU bottleneck for network I/O.

**RPS (Receive Packet Steering):** Software RSS for NICs that don't support hardware RSS. The kernel steering code hashes packets and dispatches them to the appropriate CPU's queue.

**RFS (Receive Flow Steering):** Steers packets to the CPU that is currently running the application that will process them. Improves cache locality — the packet data is more likely to be in the CPU's cache when the application processes it.

---

## 15. Cloud Network Abstractions: Putting It All Together

### 15.1 The Full Packet Journey: Pod to External Service

Trace a packet from a Kubernetes pod to an external HTTPS endpoint, through every layer:

```
1. Application writes to socket (syscall: connect/sendmsg)
2. Kernel TCP stack: creates TCP segment, assigns ephemeral port
3. Kernel IP stack: routing table lookup → next hop is node's default gateway
4. CNI eBPF/iptables: check egress NetworkPolicy → allow
5. Pod's veth pair: packet exits pod network namespace to host namespace
6. Host routing: packet to external IP → default route → NIC
7. SNAT (via NAT Gateway or node SNAT iptables rule): src IP rewritten
8. NIC: packet enqueued to hardware TX ring
9. Physical NIC: DMA from ring buffer, transmitted to ToR switch
10. ToR switch: L3 lookup, ECMP hash, forwarded to Spine
11. Spine → Core → Internet edge
12. Internet routing: BGP to destination AS
13. TLS handshake at destination: encrypted channel established
14. Data flows encrypted, responses reverse the path
```

Every step is a potential failure point, a performance bottleneck, and a security decision point.

### 15.2 The Isolation Hierarchy

```
Physical Server
  └── Hypervisor / Host OS
       ├── IOMMU: isolates DMA from physical NIC VFs
       ├── SR-IOV / Virtual Switch: isolates VM NIC traffic
       └── VM / Container Runtime
            ├── VM: hardware-enforced isolation (separate vCPU, memory, vNIC)
            └── Container: namespace/cgroup isolation (shared kernel, weaker)
                 └── Pod
                      ├── Network namespace: isolated routing, interfaces, sockets
                      ├── CNI NetworkPolicy: L3/L4 pod-to-pod rules
                      └── Service Mesh mTLS: L7 identity-based encryption + authz
```

The depth of isolation decreases as you go from physical to container. The weaker the isolation boundary, the more layers of security controls are required to compensate.

---

## Next 3 Steps

**Step 1:** Build a local Kubernetes cluster (kind or k3s) with Cilium as the CNI, enable Hubble, and trace actual packet flows between pods. Run `cilium monitor` while `curl`ing between pods — observe every network event (policy verdicts, NAT, DNS queries) in real time. This gives you hands-on intuition for everything above.

**Step 2:** Study **RFC 7348 (VXLAN)**, **RFC 8926 (Geneve)**, and **RFC 9000 (QUIC)** as primary sources. Then read the **Kubernetes Network Model** specification and the **CNI spec** (github.com/containernetworking/cni). Primary sources over blog posts — they give you the precise semantics you need for production reasoning.

**Step 3:** Implement a threat model for a multi-tier Kubernetes application using the **STRIDE** framework applied to each network segment: identify Spoofing (IP/identity), Tampering (unencrypted traffic), Repudiation (no flow logging), Information Disclosure (missing mTLS), DoS (no rate limiting, no NetworkPolicy limiting blast radius), Elevation of Privilege (permissive NetworkPolicy allowing unexpected lateral movement). Then close each gap with a specific control from the layers above.

# Step 1: Packet Flow Tracing in Kubernetes + Cilium + Hubble

**Summary:** When you run a local Kubernetes cluster with Cilium as the CNI and enable Hubble for observability, you get a live window into every network decision the kernel makes for every pod-to-pod packet. This step is about building visceral, hands-on intuition for the abstract concepts — watching the theory become real packet events with policy verdicts, identity labels, DNS interception, and NAT translations happening in sequence.

---

## The Physical Reality of a Local Kind/k3s Cluster

Before tracing any packet, understand what "local Kubernetes" actually is at the OS level. Each "node" in a kind cluster is a Linux container (a Docker container acting as a node). Each pod inside that node is a nested network namespace inside that container's namespace.

```
Your Laptop / Linux Host
│
├── Docker Engine (or containerd)
│    │
│    ├── kind-control-plane  (container = simulated k8s node)
│    │    ├── /proc/net/      ← this node's network stack
│    │    ├── veth_pod_A ──────── Pod A net namespace
│    │    │                        eth0: 10.0.0.15/32
│    │    │                        route: default → cilium_host
│    │    │
│    │    ├── veth_pod_B ──────── Pod B net namespace
│    │    │                        eth0: 10.0.0.22/32
│    │    │
│    │    └── cilium_host (veth) ← Cilium's virtual gateway interface
│    │         eBPF programs attached at TC layer
│    │
│    └── kind-worker          (container = simulated k8s node)
│         ├── veth_pod_C ──────── Pod C net namespace
│         │                        eth0: 10.0.1.10/32
│         └── cilium_host
│
└── kind bridge network (docker bridge) ← simulated physical underlay
     172.18.0.0/16
     kind-control-plane: 172.18.0.2
     kind-worker:        172.18.0.3
```

The "physical network" between nodes is the Docker bridge — just a Linux bridge on your host. Cilium's VXLAN or direct-routing overlay sits on top of this bridge, exactly as it would over a real data-center fabric.

---

## The Cilium Architecture on a Single Node

Cilium replaces kube-proxy and the traditional iptables CNI model entirely. Here is what lives on each node and how components relate:

```
┌─────────────────────────────────────────────────────────────┐
│                    Kubernetes Node                          │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │    Pod A     │    │    Pod B     │    │  cilium-agent│  │
│  │  eth0        │    │  eth0        │    │  (DaemonSet) │  │
│  │  10.0.0.15   │    │  10.0.0.22   │    │              │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         │ veth pair         │ veth pair          │          │
│  ───────┴───────────────────┴────────────────────┘          │
│         ↕ eBPF programs at TC hook (ingress + egress)       │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              eBPF Maps (kernel memory)              │    │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │    │
│  │  │ Policy Map       │  │ CT Map (Connection Track)│ │    │
│  │  │ identity→rules  │  │ 5-tuple → state + verdict│ │    │
│  │  └─────────────────┘  └──────────────────────────┘ │    │
│  │  ┌─────────────────┐  ┌──────────────────────────┐ │    │
│  │  │ NAT Map          │  │ Endpoint Map             │ │    │
│  │  │ VIP→PodIP DNAT  │  │ PodIP → identity label   │ │    │
│  │  └─────────────────┘  └──────────────────────────┘ │    │
│  └─────────────────────────────────────────────────────┘    │
│         ↕                                                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  cilium_host veth + VXLAN tunnel (cilium_vxlan)      │   │
│  │  ← packets to other nodes go here after eBPF fwd    │   │
│  └──────────────────────────────────────────────────────┘   │
│         ↕                                                    │
│       eth0 (node's physical/docker NIC)                     │
└─────────────────────────────────────────────────────────────┘
```

**cilium-agent** is the control plane on the node. It:
- Watches the Kubernetes API server for Pod, Service, and NetworkPolicy changes
- Translates Kubernetes objects into eBPF map entries (not iptables rules)
- Manages the lifecycle of eBPF programs attached to each pod's veth pair
- Assigns Cilium **security identity** numbers to pod label sets

**eBPF maps** are the data plane. The agent writes policy and routing data into kernel maps. When a packet arrives, the eBPF program reads from these maps at nanosecond speed — no userspace round trip, no lock contention, no iptables rule traversal.

---

## Cilium Identity: The Core Concept

This is the most important thing to understand about Cilium before tracing any packet.

Cilium does not use IP addresses as the identity for policy enforcement. It uses **numeric security identities** derived from pod label sets. Every unique combination of labels gets a unique identity number.

```
Pod labels:                          Cilium Security Identity
─────────────────────────────────────────────────────────────
app=frontend, env=prod          →    identity: 12345
app=backend,  env=prod          →    identity: 12346
app=database, env=prod          →    identity: 12347
app=frontend, env=staging       →    identity: 12348
reserved:host                   →    identity: 1  (always)
reserved:world                  →    identity: 2  (internet)
reserved:unmanaged              →    identity: 3
reserved:health                 →    identity: 4
```

When Pod A (identity 12345) sends a packet to Pod B (identity 12346), the eBPF program on Pod B's veth interface:
1. Reads the source IP from the packet
2. Looks up the source IP in the **ipcache** (an eBPF map mapping IP → identity)
3. Retrieves identity 12345 for the source
4. Looks up `(dst_identity=12346, src_identity=12345, dst_port=8080)` in the policy map
5. Gets verdict: ALLOW or DROP

This means policy is label-based, not IP-based. If Pod A is rescheduled to a new IP, the ipcache is updated and policy continues working — no rule rewrite needed.

---

## What Hubble Sees: The Observability Layer

Hubble is Cilium's network observability system. It attaches to the same eBPF infrastructure and exports flow records for every packet decision.

```
┌────────────────────────────────────────────────────────────┐
│                   Hubble Architecture                      │
│                                                            │
│  Kernel space:                                             │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  eBPF programs (TC hooks on every pod veth)          │ │
│  │  → write flow events to perf ring buffer             │ │
│  └──────────────────────────┬───────────────────────────┘ │
│                             │ perf events (lock-free)      │
│  Userspace:                 ↓                              │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  hubble observer (in cilium-agent process)           │ │
│  │  → reads perf buffer                                 │ │
│  │  → enriches with k8s metadata (pod name, namespace)  │ │
│  │  → exposes gRPC API (Hubble API)                     │ │
│  └──────────────────────────┬───────────────────────────┘ │
│                             │ gRPC                         │
│  ┌──────────────────────────▼───────────────────────────┐ │
│  │  hubble-relay (aggregates from all nodes)            │ │
│  └──────────────────────────┬───────────────────────────┘ │
│                             │                              │
│               ┌─────────────┴──────────────┐              │
│               ↓                            ↓              │
│      hubble CLI (TUI)              Hubble UI (web)         │
│      (your terminal)               (port-forwarded)        │
└────────────────────────────────────────────────────────────┘
```

A single Hubble flow record contains:
```
time:          2026-03-12T10:43:22.123Z
src:           namespace=default, pod=frontend-abc, ip=10.0.0.15, port=52341
dst:           namespace=default, pod=backend-xyz,  ip=10.0.0.22, port=8080
identity_src:  12345  (app=frontend, env=prod)
identity_dst:  12346  (app=backend, env=prod)
protocol:      TCP
verdict:       FORWARDED
policy_name:   allow-frontend-to-backend
l7_info:       HTTP GET /api/v1/users → 200 OK (12ms)
node:          kind-control-plane
direction:     EGRESS (from source pod's perspective)
```

This is the level of visibility you get — not just "packet passed or dropped" but full L7 application-layer context tied to Kubernetes identities, all captured at kernel speed without a sidecar proxy.

---

## Packet Flow 1: Same-Node Pod-to-Pod (No Overlay)

This is the simplest path. Pod A and Pod B are on the same Kubernetes node.

```
Pod A (10.0.0.15)                              Pod B (10.0.0.22)
net namespace A                                net namespace B
     │                                               │
     │  eth0 (container side of veth pair)           │  eth0
     │                                               │
     ▼                                               ▲
 ┌───────────────────────────────────────────────────────┐
 │                  Host Network Namespace               │
 │                                                       │
 │  lxc_pod_a (host side of veth A)                     │
 │       │                                              │
 │       │ ← eBPF TC egress hook fires here             │
 │       │   1. source identity lookup (ipcache)        │
 │       │   2. policy check: Pod A → Pod B allowed?    │
 │       │   3. if ALLOW: redirect to lxc_pod_b         │
 │       │   4. Hubble records: FORWARDED verdict        │
 │       │   if DROP: Hubble records: DROPPED + reason  │
 │       │                                              │
 │       └──────── eBPF redirect ──────────────────────►│
 │                  (kernel skb redirect,                │  lxc_pod_b
 │                   NO routing table lookup,            │  (host side of veth B)
 │                   NO IP stack traversal)              │
 │                                                       │  ↑ eBPF TC ingress hook
 │                                                       │    policy check (ingress)
 └───────────────────────────────────────────────────────┘
                                                         │
                                                         ▼
                                                    Pod B's eth0
                                                    packet delivered
```

**Key insight:** On the same node, Cilium uses `bpf_redirect()` — a kernel primitive that moves the `sk_buff` (socket buffer) directly from one interface's TX path to another's RX path. The packet never touches the IP routing table, never traverses a Linux bridge, never hits iptables. This is why Cilium's same-node latency is sub-10 microseconds.

**What Hubble sees at each point:**
```
Event 1 (egress from Pod A's veth):
  src=Pod A, dst=Pod B, verdict=FORWARDED, direction=EGRESS

Event 2 (ingress at Pod B's veth):
  src=Pod A, dst=Pod B, verdict=FORWARDED, direction=INGRESS
```

Two flow records. Two policy checks. One at source (egress NetworkPolicy applied to Pod A), one at destination (ingress NetworkPolicy applied to Pod B). Both must allow for the packet to be delivered.

---

## Packet Flow 2: Cross-Node Pod-to-Pod (VXLAN Overlay)

Pod A on Node 1 communicates with Pod C on Node 2. Now the underlay (Docker bridge or real fabric) is involved.

```
NODE 1 (172.18.0.2)                         NODE 2 (172.18.0.3)
┌──────────────────────────┐                ┌──────────────────────────┐
│  Pod A  (10.0.0.15)      │                │  Pod C  (10.0.1.10)      │
│  net ns A                │                │  net ns C                │
│  eth0                    │                │  eth0                    │
│    │                     │                │    ▲                     │
│    ▼                     │                │    │                     │
│  lxc_pod_a (veth host)   │                │  lxc_pod_c (veth host)   │
│    │                     │                │    │                     │
│    │ eBPF TC egress:      │                │    │ eBPF TC ingress:     │
│    │ - identity lookup    │                │    │ - decap outer hdrs   │
│    │ - policy check       │                │    │ - identity from      │
│    │ - dst is remote node │                │    │   tunnel src IP      │
│    │ - encapsulate VXLAN  │                │    │ - policy check       │
│    │ - redirect to        │                │    │ - deliver to pod     │
│    │   cilium_vxlan       │                │    │                     │
│    ▼                     │                │    │                     │
│  cilium_vxlan            │                │  cilium_vxlan            │
│  (VXLAN tunnel device)   │                │  (VXLAN tunnel device)   │
│    │                     │                │    ▲                     │
│    │ Outer IP hdr added:  │                │    │ Outer IP hdr:        │
│    │ src: 172.18.0.2      │                │    │ src: 172.18.0.2      │
│    │ dst: 172.18.0.3      │                │    │ dst: 172.18.0.3      │
│    │ VNI: cluster VNI     │                │    │ VNI: cluster VNI     │
│    │ Inner: Pod A→Pod C   │                │    │ Inner: Pod A→Pod C   │
│    ▼                     │                │    │                     │
│  eth0 (node NIC)         │                │  eth0 (node NIC)         │
│  172.18.0.2              │                │  172.18.0.3              │
└──────────┬───────────────┘                └──────────────────────────┘
           │                                            ▲
           │          Docker bridge / underlay          │
           └────────────────────────────────────────────┘
                     L3 routing: 172.18.0.2 → 172.18.0.3
                     (simple IP forwarding on the bridge)
```

**The VXLAN encapsulation in detail:**

```
Original inner packet (tenant):
┌──────────┬──────────┬──────────┬──────────┐
│ Eth hdr  │ IP hdr   │ TCP hdr  │ Payload  │
│ (pod MACs│ src:     │ src:     │ HTTP GET │
│  virtual)│10.0.0.15 │ port:    │ /api/    │
│          │ dst:     │ 52341    │          │
│          │10.0.1.10 │ dst: 80  │          │
└──────────┴──────────┴──────────┴──────────┘

After VXLAN encapsulation (what the physical network sees):
┌──────────┬──────────┬──────────┬──────────┬──────────┬─ inner ─┐
│ Eth hdr  │ Outer IP │ UDP hdr  │ VXLAN hdr│ [Inner   │ packet  │
│ (node    │src:      │src port: │VNI:      │  Eth+IP+ │ above   │
│  MACs)   │172.18.0.2│ (random, │ cluster  │  TCP+    │         │
│          │dst:      │ for ECMP)│ segment  │  payload]│         │
│          │172.18.0.3│dst: 4789 │          │          │         │
└──────────┴──────────┴──────────┴──────────┴──────────┴─────────┘
                       ↑
                       random src port derived from inner flow hash
                       → allows ECMP to distribute flows across paths
```

**What Hubble sees across both nodes:**

```
Node 1 events (hubble on node 1):
  Event 1: Pod A → Pod C, direction=EGRESS, verdict=FORWARDED, node=kind-control-plane

Node 2 events (hubble on node 2):
  Event 2: Pod A → Pod C, direction=INGRESS, verdict=FORWARDED, node=kind-worker

hubble-relay aggregates both → you see both events in a single stream
```

---

## Packet Flow 3: Pod to Service (ClusterIP Resolution)

This shows how Kubernetes Service abstraction works, entirely in eBPF with Cilium (no kube-proxy).

```
  Pod A wants to reach Service "backend-svc"
  ClusterIP: 10.96.0.50:8080
  Actual backend pods: 10.0.0.22:8080, 10.0.1.10:8080

  Pod A's application:
  connect(fd, {10.96.0.50, 8080})  ← app uses ClusterIP
         │
         │ Cilium intercepts at the SOCKET level
         │ (eBPF cgroup/sock hook, before packet is even formed)
         │
         ▼
  ┌──────────────────────────────────────────────────┐
  │  eBPF sock_ops / connect4 hook                   │
  │                                                  │
  │  1. Lookup 10.96.0.50:8080 in Service Map        │
  │     → found: 2 backends available                │
  │  2. Select backend (consistent hash or RR):      │
  │     → chose 10.0.0.22:8080                       │
  │  3. Rewrite destination BEFORE socket is created │
  │     dst becomes 10.0.0.22:8080                   │
  │  4. Record NAT mapping in CT map:                │
  │     PodA:52341 → 10.96.0.50:8080                 │
  │     actually connected to: 10.0.0.22:8080        │
  └──────────────────────────────────────────────────┘
         │
         │ TCP SYN sent with dst=10.0.0.22:8080
         │ (ClusterIP 10.96.0.50 never appears in packet)
         ▼
  Normal same-node or cross-node flow
  (as described in Flow 1 or Flow 2)

  Application sees:
  connect() returned success, talking to "backend-svc"
  actual connection: 10.0.0.22:8080
  app is unaware of the rewrite
```

**Why socket-level load balancing matters:**

Traditional kube-proxy does DNAT at the netfilter PREROUTING hook — the packet is formed, goes through the full IP stack, hits PREROUTING, gets DNAT'd, then is re-routed. This costs CPU cycles and conntrack state.

Cilium's socket-level LB rewrites the destination *before* the packet is created — the TCP SYN is sent directly to the backend IP. No DNAT, no conntrack entry for the service translation (only for the real connection). This is why Cilium has dramatically lower CPU overhead for high-connection-rate microservices.

```
kube-proxy path (iptables DNAT):
  app writes → socket → packet formed (dst=ClusterIP)
  → IP stack → netfilter PREROUTING → DNAT rewrite
  → conntrack records NAT → re-route → forward

Cilium path (socket-level):
  app writes → eBPF sock hook rewrites dst in-place
  → socket → packet formed (dst=PodIP directly)
  → forward (no NAT tracking needed for service)
```

---

## Packet Flow 4: DNS Resolution (CoreDNS + Cilium DNS Policy)

DNS is intercepted by Cilium for two purposes: observability (Hubble logs every DNS query) and DNS-based egress policy enforcement.

```
Pod A wants to connect to "api.external-service.com"

Step 1: DNS Resolution
─────────────────────
Pod A's resolver stub (/etc/resolv.conf: nameserver 10.96.0.10)
         │
         │ UDP query: "api.external-service.com A?"
         │ dst: 10.96.0.10:53 (CoreDNS ClusterIP)
         │
         ▼
   eBPF sock hook → Service map lookup → CoreDNS pod IP
         │
         ▼
   CoreDNS pod (in kube-system namespace)
         │ resolves: api.external-service.com → 203.0.113.45
         │
         │ DNS response sent back to Pod A
         ▼
   eBPF TC hook (on CoreDNS veth, ingress to Pod A):
   ┌─────────────────────────────────────────────────┐
   │  Cilium DNS proxy intercepts the DNS RESPONSE   │
   │  Extracts: api.external-service.com → 203.0.113.45│
   │  Updates ipcache:                               │
   │    203.0.113.45 → FQDN: api.external-service.com│
   │  Checks egress DNS policy:                      │
   │    "allow Pod A to connect to *.external-service.com"│
   │    → programs eBPF policy map to allow          │
   │      Pod A → 203.0.113.45:443                   │
   └─────────────────────────────────────────────────┘
         │
         ▼
   DNS response delivered to Pod A

Step 2: Actual Connection
─────────────────────────
Pod A connects to 203.0.113.45:443
         │
         │ eBPF egress policy check:
         │ src identity = Pod A (12345)
         │ dst = 203.0.113.45 → ipcache says "world:api.external-service.com"
         │ policy map: 12345 → world:api.external-service.com:443 = ALLOW
         ▼
   packet forwarded to node's NIC → NAT Gateway → internet
```

**What Hubble shows for this entire flow:**

```
Flow 1: Pod A → CoreDNS, L7 DNS query: "api.external-service.com A?", verdict=FORWARDED
Flow 2: CoreDNS → Pod A, L7 DNS response: 203.0.113.45, TTL=300, verdict=FORWARDED
Flow 3: Pod A → 203.0.113.45:443, verdict=FORWARDED, identity=world
```

---

## Packet Flow 5: NetworkPolicy DROP — What Dropped Packets Look Like

When a NetworkPolicy blocks traffic, Hubble captures the drop with full context. This is what you observe when you watch `cilium monitor` or Hubble's flow stream.

```
Scenario: Pod A (app=frontend) tries to connect to Pod D (app=database)
          NetworkPolicy on Pod D only allows connections from app=backend

Pod A → Pod D attempt:
         │
         │ TCP SYN: 10.0.0.15:52400 → 10.0.0.30:5432
         ▼
   lxc_pod_a (veth host side) TC egress eBPF:
   ┌─────────────────────────────────────────────────┐
   │  Source identity: 12345 (app=frontend)          │
   │  Dest identity:   12347 (app=database)          │
   │  Policy map lookup:                             │
   │  (dst=12347, src=12345, port=5432) → ?          │
   │                                                 │
   │  No matching ALLOW rule found                   │
   │  Default action: DROP                           │
   │  Increment drop counter                         │
   │  Emit perf event to Hubble                      │
   └─────────────────────────────────────────────────┘
         │
         │ packet is freed (kfree_skb)
         │ TCP SYN never reaches Pod D
         ▼
   Pod A's application:
   connect() times out (no RST is sent — silent drop)
   or receives ECONNREFUSED if Cilium sends RST

Hubble event:
  src=default/frontend-abc, dst=default/database-xyz
  protocol=TCP, dst_port=5432
  verdict=DROPPED
  drop_reason=POLICY_DENIED
  policy=<none> (no matching allow rule)
```

**The crucial debugging insight:** When a connection fails mysteriously, `cilium monitor --type drop` or Hubble filtered to `verdict=DROPPED` tells you immediately: which source identity, which destination identity, which port, and which NetworkPolicy (or lack thereof) caused the drop. This replaces hours of iptables rule archaeology with a single observable event.

---

## The Full Mental Map of What You're Observing

```
CONTROL PLANE                          DATA PLANE
─────────────────────────────────────────────────────────────────
Kubernetes API Server                  eBPF Maps (kernel memory)
      │                                        │
      │ watch Pods/Services/NetPolicies         │ O(1) lookups
      ▼                                        │
cilium-agent (per node)                        │
      │                                        │
      ├── translates k8s labels                │
      │   → identity numbers          ────────►│ ipcache map
      │                                        │ (IP → identity)
      ├── translates NetworkPolicy    ────────►│ policy map
      │   → allow/deny rules                   │ (id×id×port → verdict)
      │                                        │
      ├── translates Services         ────────►│ service map
      │   → backend pod IPs                    │ (ClusterIP → [pod IPs])
      │                                        │
      └── manages eBPF program       ────────►│ eBPF programs on
          lifecycle (attach/detach)            │ every veth TC hook
                                               │
OBSERVABILITY PLANE                            │
─────────────────                              │
eBPF perf ring buffer ◄────────────── eBPF programs emit flow events
      │
      ▼
hubble observer (reads events, enriches with k8s metadata)
      │
      ├── gRPC API → hubble CLI → you see flows in terminal
      │
      └── gRPC API → hubble-relay → hubble UI → visual flow map
```

---

## What Intuition This Step Builds

After observing live flows through this system, you internalize:

**Identity over IP:** You stop thinking about network policy as "allow 10.0.0.15 to reach 10.0.0.22" and start thinking "allow identity `app=frontend` to reach identity `app=backend` on port 8080." When pods reschedule and IPs change, your mental model stays stable because the system stays stable.

**Every dropped packet is an observable event:** In iptables-land, a dropped packet disappears silently. In the eBPF model, every drop emits a structured event with full context. Debugging goes from "why can't my pod connect?" (hours) to "find the DROPPED flow in Hubble, read the drop_reason" (seconds).

**The data plane is kernel-local:** Policy enforcement happens at the source node in the kernel — a packet that would be policy-dropped never enters the network fabric. This is fundamentally different from perimeter firewalls where the packet travels to a central inspection point. eBPF-enforced policy is zero-overhead for allowed traffic and eliminates the need for centralized firewall bottlenecks.

**L7 visibility without proxies:** Hubble gives you HTTP method, path, status code, gRPC method name, and DNS query/response all from eBPF hooks — without any sidecar proxy, without any TLS termination, without any application changes. This is the observability architecture of the future: the kernel sees everything because it processes everything.

---

## Next 3 Steps

**Step 1A:** After getting intuition from observing flows, intentionally create NetworkPolicy violations — deploy a pod that tries to connect to a database it shouldn't. Watch the DROPPED events in Hubble, read the drop reason, then write the correct NetworkPolicy and watch the verdict change from DROPPED to FORWARDED in real time. This closes the loop between policy intent and enforcement reality.

**Step 2:** Move to the cross-node flow. Run `tcpdump` on the node's physical interface (the Docker bridge interface on your host) while two pods on different nodes communicate. Observe the VXLAN-encapsulated packets — see the outer IP headers pointing to node IPs, the UDP port 4789, and the inner pod IP headers. Then correlate what tcpdump shows at the physical layer with what Hubble shows at the identity/policy layer. These are two views of the same packet.

**Step 3:** Study the Cilium eBPF source code (github.com/cilium/cilium, path `bpf/`) — specifically `bpf_lxc.c` (the per-endpoint eBPF program), `lib/policy.h` (policy map lookup logic), and `lib/nat.h` (NAT/service translation). Reading the actual C code that processes your packets converts the architecture diagrams above from abstract boxes into concrete kernel instructions. This is the level of understanding that separates a cloud-native user from a cloud-native engineer.

# Step 2: The Two-Layer View — Physical Packets vs Identity/Policy Events

**Summary:** Every cross-node pod-to-pod packet exists simultaneously in two observability planes: the physical layer (raw bytes on the wire, outer IP headers, VXLAN encapsulation visible to tcpdump) and the identity/policy layer (Kubernetes labels, Cilium security identities, policy verdicts visible to Hubble). These are two different projections of the same physical reality. The ability to mentally correlate them — to look at a raw VXLAN packet and know exactly which Hubble flow event it corresponds to — is what separates surface-level cloud networking knowledge from the engineering depth needed to debug production incidents, reason about isolation boundaries, and design secure systems.

---

## The Fundamental Duality: One Packet, Two Realities

Before anything else, internalize this split view. The same packet, at the same instant, looks completely different depending on where you observe it.

```
THE SAME PACKET — TWO SIMULTANEOUS VIEWS
══════════════════════════════════════════════════════════════════════

PHYSICAL LAYER VIEW                   IDENTITY/POLICY LAYER VIEW
(what tcpdump sees on host eth0)      (what Hubble sees at eBPF hook)
─────────────────────────────────     ──────────────────────────────
Outer Ethernet frame                  [not visible — stripped]
  src MAC: node1 NIC MAC
  dst MAC: docker bridge MAC

Outer IP header                       [not visible — underlay only]
  src: 172.18.0.2 (Node 1 IP)
  dst: 172.18.0.3 (Node 2 IP)

UDP header                            [not visible — encap only]
  src port: 54321 (flow hash)
  dst port: 4789 (VXLAN)

VXLAN header                          [not visible — encap only]
  VNI: 1 (Cilium cluster segment)

Inner Ethernet frame                  [largely ignored by Cilium]
  src MAC: pod A veth MAC
  dst MAC: cilium_host MAC

Inner IP header                       src identity: 12345
  src: 10.0.0.15 (Pod A IP)         ← (app=frontend, env=prod)
  dst: 10.0.1.10 (Pod C IP)           dst identity: 12346
                                    ← (app=backend, env=prod)

TCP header                            verdict: FORWARDED
  src port: 52341                     policy: allow-fe-to-be
  dst port: 8080                      l7: HTTP GET /api/v1

Payload                               [not captured by Hubble
  HTTP GET /api/v1/users               unless L7 policy active]

══════════════════════════════════════════════════════════════════════
tcpdump: 172.18.0.2.54321 >           Hubble: frontend → backend
         172.18.0.3.4789              FORWARDED (HTTP 200, 8ms)
         VXLAN VNI 1
```

tcpdump is blind to pod identity — it sees node IPs and UDP/VXLAN. Hubble is blind to the physical encapsulation — it sees pod labels and policy verdicts. You need both to fully understand what is happening.

---

## The Physical Topology Being Observed

Understanding where tcpdump and Hubble attach determines what each tool can and cannot see.

```
YOUR LAPTOP / LINUX HOST
═══════════════════════════════════════════════════════════════════════

  docker0 bridge  (172.18.0.1/16)  ← tcpdump here sees ALL inter-node traffic
       │                              as VXLAN-encapsulated UDP flows
       │                              (this is the "physical underlay")
       ├─────────────────────────────────────────────────────┐
       │                                                     │
       ▼                                                     ▼
┌──────────────────────────┐               ┌────────────────────────────┐
│      kind-control-plane  │               │       kind-worker          │
│      172.18.0.2          │               │       172.18.0.3           │
│                          │               │                            │
│  eth0 (172.18.0.2)       │               │  eth0 (172.18.0.3)         │
│   ↑ tcpdump here         │               │   ↑ tcpdump here           │
│     sees encapsulated    │               │     sees encapsulated      │
│     VXLAN packets        │               │     VXLAN packets          │
│     (outer headers only) │               │     (outer headers only)   │
│                          │               │                            │
│  cilium_vxlan            │               │  cilium_vxlan              │
│   ↑ tcpdump here         │               │   ↑ tcpdump here           │
│     sees decapsulated    │               │     sees decapsulated      │
│     inner pod packets    │               │     inner pod packets      │
│     (inner headers)      │               │     (inner headers)        │
│                          │               │                            │
│  lxc_pod_a (veth)        │               │  lxc_pod_c (veth)          │
│   ↑ tcpdump here         │               │   ↑ tcpdump here           │
│     sees raw pod traffic │               │     sees raw pod traffic   │
│     pre-encapsulation    │               │     post-decapsulation     │
│                          │               │                            │
│   eBPF TC hook ◄─────────┼───────────────┼──────────── eBPF TC hook   │
│   Hubble sees:           │               │            Hubble sees:    │
│   identity, verdict,     │               │            identity,       │
│   policy name, L7 data   │               │            verdict, L7     │
│                          │               │                            │
│  Pod A  (10.0.0.15)      │               │  Pod C  (10.0.1.10)        │
└──────────────────────────┘               └────────────────────────────┘
```

**The key insight about observation points:**

Each interface you could attach tcpdump to reveals a different layer of the packet:
- On `eth0` of a node → you see the VXLAN-encapsulated outer packet (underlay view)
- On `cilium_vxlan` of a node → you see inner pod packets after decap (overlay view)  
- On `lxc_pod_X` (the veth host side) → you see raw pod-to-pod packets, fully processed
- On `eth0` inside a pod network namespace → you see what the application sees

tcpdump at each point is a different X-ray of the same physical reality.

---

## The VXLAN Packet: Byte-by-Byte Structure

Understanding what you're looking at when tcpdump captures on `eth0` of a node.

```
COMPLETE VXLAN FRAME ON THE WIRE
(numbers are byte offsets from start of Ethernet frame)

Byte 0                                                      Byte N
│                                                               │
▼                                                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OUTER ETHERNET HEADER (14 bytes)             │
│  [0-5]  dst MAC: AA:BB:CC:DD:EE:FF  (docker bridge MAC)         │
│  [6-11] src MAC: 11:22:33:44:55:66  (node1 NIC MAC)             │
│  [12-13] ethertype: 0x0800 (IPv4)                               │
├─────────────────────────────────────────────────────────────────┤
│                    OUTER IP HEADER (20 bytes)                   │
│  [14]   version=4, IHL=5                                        │
│  [15]   DSCP/ECN: 0 (or ECN bits if congestion signaling)       │
│  [16-17] total length: (varies with payload)                    │
│  [18-19] identification: (per-packet ID)                        │
│  [20-21] flags + fragment offset: DF bit set (don't fragment)   │
│           ← DF is set because VXLAN relies on path MTU          │
│  [22]   TTL: 64                                                 │
│  [23]   protocol: 0x11 (UDP = 17)                               │
│  [24-25] header checksum                                        │
│  [26-29] src IP: 172.18.0.2  ← NODE 1 IP (VTEP source)         │
│  [30-33] dst IP: 172.18.0.3  ← NODE 2 IP (VTEP destination)    │
├─────────────────────────────────────────────────────────────────┤
│                    OUTER UDP HEADER (8 bytes)                   │
│  [34-35] src port: 54321   ← RANDOM, derived from inner flow    │
│           ← hash(inner src IP, dst IP, src port, dst port, proto)│
│           ← THIS IS THE ECMP ENTROPY SOURCE                     │
│  [36-37] dst port: 4789    ← VXLAN well-known port (IANA)       │
│  [38-39] UDP length: (varies)                                   │
│  [40-41] UDP checksum: 0   ← often zero for VXLAN (RFC allows)  │
├─────────────────────────────────────────────────────────────────┤
│                    VXLAN HEADER (8 bytes)                       │
│  [42]   flags: 0x08        ← VNI present flag (bit 3 set)       │
│  [43-45] reserved: 0x000000                                     │
│  [46-48] VNI: 1            ← Cilium uses VNI 1 for cluster      │
│           ← 24 bits = 16M possible segments                     │
│  [49]   reserved: 0x00                                          │
├─────────────────────────────────────────────────────────────────┤
│                    INNER ETHERNET HEADER (14 bytes)             │
│  [50-55] dst MAC: (cilium_host or lxc MAC on Node 2)            │
│  [56-61] src MAC: (lxc veth MAC on Node 1)                      │
│  [62-63] ethertype: 0x0800 (IPv4)                               │
├─────────────────────────────────────────────────────────────────┤
│                    INNER IP HEADER (20 bytes)                   │
│  [64]   version=4, IHL=5                                        │
│  [68-71] src IP: 10.0.0.15  ← POD A IP (tenant source)         │
│  [72-75] dst IP: 10.0.1.10  ← POD C IP (tenant destination)    │
├─────────────────────────────────────────────────────────────────┤
│                    INNER TCP HEADER (20 bytes)                  │
│  [76-77] src port: 52341   ← Pod A ephemeral port              │
│  [78-79] dst port: 8080    ← Pod C listening port              │
│  [80-83] sequence number                                        │
│  [84-87] acknowledgment number                                  │
│  [88]   data offset + flags (SYN=0x02, ACK=0x10, etc.)         │
├─────────────────────────────────────────────────────────────────┤
│                    APPLICATION PAYLOAD                          │
│  HTTP GET /api/v1/users HTTP/1.1                                │
│  Host: backend-svc                                              │
│  ...                                                            │
└─────────────────────────────────────────────────────────────────┘

TOTAL OVERHEAD = 14 (outer eth) + 20 (outer IP) + 8 (UDP) + 8 (VXLAN)
               + 14 (inner eth) = 64 bytes of encapsulation overhead
               on top of the original IP packet
```

**MTU implications of this overhead:**

```
Standard Ethernet MTU:           1500 bytes
VXLAN overhead:                 -  50 bytes (outer IP+UDP+VXLAN)
Inner Ethernet header:          -  14 bytes
Available for inner IP packet:  1436 bytes

Pod's effective MTU must be:    1436 bytes (not 1500)
                                      ↑
                    Cilium sets this automatically on pod veth interfaces.
                    If not set correctly: packets that fit in pod MTU
                    but exceed path MTU after encapsulation are silently
                    dropped by the underlay (because DF bit is set).
                    This is a common source of mysterious connection hangs
                    — small packets work, large packets fail.
```

---

## The Random Source UDP Port: ECMP Entropy in Detail

This single 16-bit field is the reason VXLAN works efficiently on multi-path physical networks. It deserves its own diagram.

```
WITHOUT ECMP ENTROPY (hypothetical fixed src port):

All VXLAN traffic:
  src: 172.18.0.2, dst: 172.18.0.3, UDP src: 4789, dst: 4789

ECMP hash at spine switch:
  hash(172.18.0.2, 172.18.0.3, 4789, 4789) = fixed value X
  ALL flows hash to path X

Physical links:   Path 1 ████████████████████ saturated
                  Path 2 ░░░░░░░░░░░░░░░░░░░░ idle
                  Path 3 ░░░░░░░░░░░░░░░░░░░░ idle

WITH ECMP ENTROPY (VXLAN random src port, derived from inner flow):

Pod A → Pod C: hash(10.0.0.15, 10.0.1.10, 52341, 8080) = port 54321
Pod B → Pod C: hash(10.0.0.22, 10.0.1.10, 60234, 8080) = port 31847
Pod A → Pod D: hash(10.0.0.15, 10.0.1.15, 49821, 5432) = port 47293

ECMP hash at spine switch:
  flow 1: hash(172.18.0.2, 172.18.0.3, 54321, 4789) → path 1
  flow 2: hash(172.18.0.2, 172.18.0.3, 31847, 4789) → path 2
  flow 3: hash(172.18.0.2, 172.18.0.3, 47293, 4789) → path 3

Physical links:   Path 1 ████████░░░░░░░░░░░░ balanced
                  Path 2 ████████░░░░░░░░░░░░ balanced
                  Path 3 ████████░░░░░░░░░░░░ balanced

Key property: Same inner flow always gets same outer src port
              → Same inner TCP session always takes the same physical path
              → TCP packet ordering is preserved within a flow
              → Different flows get different paths
              → Link utilization is spread evenly
```

The inner flow 5-tuple hash produces the outer UDP source port. This is deterministic for a given flow (so all packets of one TCP session take one path), but different for different flows (so bandwidth is distributed).

---

## tcpdump Observation Points: What Each Interface Reveals

```
OBSERVATION POINT COMPARISON
═══════════════════════════════════════════════════════════════════════

Point 1: docker0 on HOST (outside all containers)
──────────────────────────────────────────────────
What you see:
  - ALL inter-node traffic between kind containers
  - Outer Ethernet + outer IP + UDP/4789 + VXLAN header + inner packet
  - You can READ inner IPs if you tell tcpdump to decode VXLAN
  - You see control-plane traffic: Kubernetes API, etcd, Hubble gRPC
  - You see the raw bandwidth consumed by all pods combined
  - You CANNOT distinguish which VNI a packet belongs to (all same VNI in kind)
  - You CAN see encapsulation overhead (frame size > inner packet size)

Useful for: measuring raw bandwidth between nodes, observing all
            cross-node flows, verifying VXLAN is being used

Point 2: eth0 inside kind-control-plane (node's NIC to docker bridge)
──────────────────────────────────────────────────────────────────────
What you see:
  - Same as docker0 but from the node's perspective
  - INGRESS: VXLAN frames arriving FROM other nodes
  - EGRESS:  VXLAN frames departing TO other nodes
  - You can see retransmissions, RTT (time between SYN and SYN-ACK)
  - You see the exact outer headers that the underlay routes on

Useful for: debugging underlay reachability, measuring actual wire RTT,
            verifying outer IP src/dst are correct VTEP addresses

Point 3: cilium_vxlan inside kind-control-plane
────────────────────────────────────────────────
What you see:
  - DECAPSULATED packets AFTER VXLAN processing
  - Inner IP headers: actual pod IPs (src/dst)
  - Inner TCP/UDP with actual ports
  - NO outer VXLAN headers
  - This is the "overlay" view: what the virtual network looks like
  - Packets going OUT on this interface are being encapsulated
  - Packets coming IN on this interface have been decapsulated

Useful for: verifying correct inner pod IPs, debugging routing inside
            the overlay, seeing what pod traffic looks like pre-encap

Point 4: lxc_pod_a (veth host side) inside node
────────────────────────────────────────────────
What you see:
  - Raw traffic TO and FROM Pod A specifically
  - This is WHERE eBPF TC hooks fire
  - You see both ALLOWED and packets arriving before policy verdict
  - No encapsulation at all — raw pod IP/port packets
  - ARP is absent (Cilium uses L3-only routing, no ARP on lxc)
  - You CAN see packets that will be DROPPED (they arrive, eBPF drops)

Useful for: debugging specific pod traffic, verifying pod sends correct
            src IP, seeing what eBPF policy acts upon

Point 5: eth0 inside Pod A's network namespace
───────────────────────────────────────────────
What you see:
  - What the APPLICATION inside the pod sees
  - No encapsulation, no eBPF artifacts
  - Clean TCP streams, correct IPs
  - If connection is blocked: SYN sent, no SYN-ACK received
  - DNS queries going out to CoreDNS ClusterIP
  - Service ClusterIPs if socket-level LB has NOT rewritten them

Useful for: application-level debugging, verifying TLS handshakes,
            confirming pod's view of the network is correct

═══════════════════════════════════════════════════════════════════════

VISIBILITY SUMMARY:

Interface     | Outer VXLAN hdrs | Inner Pod IPs | Pod Identity | Policy Verdict
──────────────┼──────────────────┼───────────────┼──────────────┼──────────────
docker0       |      YES         |  YES (decode) |      NO      |     NO
eth0 (node)   |      YES         |  YES (decode) |      NO      |     NO
cilium_vxlan  |      NO          |      YES      |      NO      |     NO
lxc_pod_X     |      NO          |      YES      |      NO      |     NO
eth0 (pod ns) |      NO          |      YES      |      NO      |     NO
──────────────┼──────────────────┼───────────────┼──────────────┼──────────────
Hubble        |      NO          |      YES      |     YES      |    YES
```

---

## The Correlation: Matching tcpdump Packets to Hubble Flow Events

This is the core skill. Given a raw VXLAN packet from tcpdump, identify the exact Hubble flow event it corresponds to.

```
CORRELATION PROCEDURE
═══════════════════════════════════════════════════════════════════════

Step 1: Capture VXLAN packet on node eth0 (tcpdump):
─────────────────────────────────────────────────────
Timestamp: 10:43:22.123456

Frame:
  Outer: 172.18.0.2:54321 → 172.18.0.3:4789 (UDP, VXLAN)
  Inner: 10.0.0.15:52341  → 10.0.1.10:8080  (TCP SYN)
  Flags: [S], seq=1234567, len=0


Step 2: Decode the identities (from Cilium's ipcache):
────────────────────────────────────────────────────────

  Outer src 172.18.0.2 → this is Node 1's VTEP
  Outer dst 172.18.0.3 → this is Node 2's VTEP
  Inner src 10.0.0.15  → ipcache: identity 12345 (app=frontend, env=prod)
  Inner dst 10.0.1.10  → ipcache: identity 12346 (app=backend, env=prod)

  ┌──────────────────────────────────┐
  │  IP 10.0.0.15 → identity 12345  │
  │  Pod name: frontend-abc-xyz      │
  │  Namespace: default              │
  │  Labels: app=frontend, env=prod  │
  └──────────────────────────────────┘
              matches
  ┌──────────────────────────────────┐
  │  Hubble flow event at 10:43:22   │
  │  src: default/frontend-abc-xyz   │
  │  dst: default/backend-def-uvw    │
  │  proto: TCP, dst_port: 8080      │
  │  verdict: FORWARDED              │
  │  policy: allow-frontend-backend  │
  └──────────────────────────────────┘


Step 3: Verify the timestamp correlation:
──────────────────────────────────────────

tcpdump timestamp: 10:43:22.123456 (packet seen on Node 1 eth0 egress)
Hubble event time: 10:43:22.121000 (eBPF TC hook fired on Node 1 lxc)

Hubble fires BEFORE tcpdump sees the packet because:
  - eBPF TC hook fires when packet is in lxc_pod_a (before encapsulation)
  - tcpdump on eth0 sees the packet AFTER encapsulation + NIC TX queue
  - ~2ms difference = encapsulation time + NIC TX queue delay

This ordering is deterministic:
  Hubble egress event → encapsulation → tcpdump (Node 1 eth0 egress)
  tcpdump (Node 2 eth0 ingress) → decapsulation → Hubble ingress event


Step 4: Match the TCP flow across both tools:
──────────────────────────────────────────────

                    tcpdump (Node 1 eth0)    Hubble (Node 1 lxc)
SYN:     10:43:22.121  [policy check]     10:43:22.123  [wire]
SYN-ACK: 10:43:22.134  [wire]             10:43:22.136  [policy check Node 2]
ACK:     10:43:22.134  [wire]                  ↕
                                           RTT = 134 - 121 = 13ms (measured)

  The wire-level RTT (tcpdump: time between SYN and SYN-ACK) and the
  Hubble-level RTT should be nearly identical.
  Any large discrepancy indicates: queueing delay in the NIC TX ring,
  or scheduling delay in the eBPF program execution.

═══════════════════════════════════════════════════════════════════════
```

---

## What a TCP Three-Way Handshake Looks Like Across Both Layers

Trace the complete SYN → SYN-ACK → ACK sequence across both observation tools simultaneously.

```
CROSS-NODE TCP HANDSHAKE: DUAL-LAYER VIEW
══════════════════════════════════════════════════════════════════════════════

TIME →    T=0ms           T=1ms           T=13ms          T=14ms

          NODE 1                          NODE 2

HUBBLE:   [EGRESS]                        [INGRESS]
          Pod A→Pod C                     Pod A→Pod C
          TCP SYN                         TCP SYN
          FORWARDED                       FORWARDED
          policy:allow          ────────► policy:allow
          identity:12345→12346            identity:12345→12346

TCPDUMP   172.18.0.2→           wire     172.18.0.3→
(eth0     172.18.0.3            ────────►172.18.0.2  ← wait, this is wrong
 node1):  UDP/4789                        direction
          VNI:1
          10.0.0.15→10.0.1.10
          TCP SYN

          ┌────────────────────────────── underlay RTT ──────────────────────┐

TCPDUMP                                   ←────────  172.18.0.3→172.18.0.2
(eth0                                               UDP/4789
 node2):                                            VNI:1
                                                    10.0.1.10→10.0.0.15
                                                    TCP SYN-ACK

HUBBLE:                         [EGRESS]            [INGRESS]
                                Pod C→Pod A          Pod C→Pod A
                                TCP SYN-ACK          TCP SYN-ACK
                                FORWARDED ──────────►FORWARDED

HUBBLE:   [EGRESS]
          Pod A→Pod C
          TCP ACK
          FORWARDED ────────────────────────────────►[INGRESS]
                                                     FORWARDED

══════════════════════════════════════════════════════════════════════════════

WHAT THIS REVEALS:

1. Hubble fires slightly BEFORE the wire event at the source node
   (eBPF runs before encapsulation and NIC TX)

2. Hubble fires slightly AFTER the wire event at the destination node
   (eBPF runs after NIC RX and decapsulation)

3. The underlay RTT is measurable in tcpdump (time between
   SYN on node1 eth0 egress and SYN-ACK on node1 eth0 ingress)

4. The overlay RTT is measurable in Hubble (time between
   EGRESS SYN event on node1 and INGRESS SYN-ACK event on node1)

5. overlay RTT ≈ underlay RTT + (2 × encap/decap time)
   Difference reveals the per-packet VXLAN processing cost
```

---

## The Encapsulation and Decapsulation Path: In Full Detail

What actually happens inside the kernel on each node as the packet is processed.

```
NODE 1: EGRESS PATH (encapsulation)
═════════════════════════════════════════════════════════════════

Pod A's socket writes data
         │
         ▼
Kernel TCP stack: segment formed
  src: 10.0.0.15:52341
  dst: 10.0.1.10:8080
         │
         ▼
Kernel IP routing table lookup on Node 1:
  dst 10.0.1.10 → route: via cilium_host (Cilium installed this)
  Next hop: cilium_host interface
         │
         ▼
Packet enters lxc_pod_a (host veth side)
         │
         ├─── eBPF TC EGRESS hook fires ───────────────────────────────────┐
         │                                                                 │
         │    eBPF program executes:                                       │
         │    1. ipcache lookup: 10.0.1.10 → identity 12346               │
         │       + 10.0.1.10 is on Node 2 (VTEP: 172.18.0.3)              │
         │    2. policy map: (dst=12346, src=12345, port=8080) → ALLOW     │
         │    3. CT map: new connection, create entry                      │
         │    4. Hubble perf event: EGRESS, FORWARDED, identity info       │
         │    5. bpf_redirect → cilium_vxlan interface                     │
         │                                                                 │
         └─────────────────────────────────────────────────────────────────┘
         │
         ▼ (redirected to cilium_vxlan)
VXLAN encapsulation:
  - VXLAN device adds:
    Inner Ethernet header (cilium-generated MACs)
    Outer IP header: src=172.18.0.2, dst=172.18.0.3
    UDP header: src=hash(inner flow), dst=4789
    VXLAN header: VNI=1
         │
         ▼
Kernel IP routing for outer packet:
  dst 172.18.0.3 → route: via docker0 bridge
         │
         ▼
Outer Ethernet header added (bridge ARP: 172.18.0.3 → bridge MAC)
         │
         ▼
NIC TX ring buffer
         │
         ▼  ← tcpdump on eth0 sees packet HERE (fully encapsulated)
Physical transmission to Node 2


NODE 2: INGRESS PATH (decapsulation)
═════════════════════════════════════════════════════════════════

Physical frame arrives from Node 1
         │
         ▼  ← tcpdump on eth0 sees packet HERE (fully encapsulated)
NIC RX ring buffer → interrupt/NAPI poll
         │
         ▼
Outer Ethernet header stripped
Kernel IP stack: dst=172.18.0.3 (this node) → accept
UDP: dst port 4789 → dispatch to VXLAN socket
         │
         ▼
VXLAN decapsulation:
  Strips: outer IP, UDP, VXLAN headers, inner Ethernet header
  Delivers: inner IP packet (10.0.0.15→10.0.1.10) to cilium_vxlan interface
         │
         ▼  ← tcpdump on cilium_vxlan sees packet HERE (decapsulated inner)
cilium_vxlan → routed to lxc_pod_c
         │
         ├─── eBPF TC INGRESS hook on lxc_pod_c fires ────────────────────┐
         │                                                                 │
         │    eBPF program executes:                                       │
         │    1. Tunnel metadata: src VTEP was 172.18.0.3                  │
         │       (identity was carried in VXLAN or looked up from VTEP)    │
         │    2. ipcache: src 10.0.0.15 → identity 12345                  │
         │    3. policy map: (dst=12346, src=12345, port=8080) → ALLOW     │
         │    4. CT map: create ingress entry                              │
         │    5. Hubble perf event: INGRESS, FORWARDED                     │
         │    6. deliver to Pod C's network namespace                      │
         │                                                                 │
         └─────────────────────────────────────────────────────────────────┘
         │
         ▼
Pod C's eth0 receives inner IP packet
         │
         ▼  ← tcpdump inside Pod C namespace sees packet HERE
Pod C's TCP stack delivers to application socket
```

---

## Identifying Anomalies: What Discrepancies Between Layers Mean

The real value of dual-layer observation is diagnosing problems that are invisible to a single-layer tool.

```
ANOMALY DETECTION MATRIX
══════════════════════════════════════════════════════════════════════════

SCENARIO 1: tcpdump sees VXLAN packets, Hubble shows nothing
──────────────────────────────────────────────────────────────
tcpdump: VXLAN frames flowing between nodes ✓
Hubble:  No flow events for this traffic ✗

Possible causes:
  ┌─────────────────────────────────────────────────────────────┐
  │  a) Hubble ring buffer is full (high traffic rate)          │
  │     → events are being dropped before userspace reads them  │
  │  b) Traffic is bypassing Cilium eBPF hooks entirely         │
  │     → another CNI or iptables path is handling the traffic  │
  │  c) Hubble observer process has crashed                     │
  │  d) The pods are not managed by Cilium (unmanaged endpoint) │
  └─────────────────────────────────────────────────────────────┘

SCENARIO 2: Hubble shows FORWARDED, tcpdump shows retransmissions
─────────────────────────────────────────────────────────────────
Hubble:  Pod A → Pod C, FORWARDED, no drops ✓
tcpdump: repeated TCP retransmissions, duplicate ACKs ✗

Possible causes:
  ┌─────────────────────────────────────────────────────────────┐
  │  a) MTU mismatch — packets larger than VXLAN-adjusted MTU   │
  │     are silently dropped by underlay (DF bit set)           │
  │     Hubble sees the packet enter eBPF (FORWARDED)           │
  │     but it is dropped AFTER eBPF, at the NIC or bridge      │
  │                                                             │
  │  b) Physical link congestion — some packets are queued      │
  │     so long that TCP sender retransmits                     │
  │                                                             │
  │  c) NIC TX ring buffer overflow — packets enqueued but      │
  │     never sent (NIC drops tail of queue under load)         │
  └─────────────────────────────────────────────────────────────┘

  MTU drop signature in tcpdump:
    - SYN/SYN-ACK succeed (small packets, below MTU)
    - First large data packet: retransmit after timeout
    - Retransmit of same seq number: retransmit again
    - Eventually: ICMP Type 3 Code 4 "Fragmentation Needed" from underlay
      (if PMTUD is working correctly)
    - Without ICMP: silent blackhole, connection hangs permanently


SCENARIO 3: Hubble shows DROPPED, tcpdump shows packets leaving source
────────────────────────────────────────────────────────────────────────
Hubble:  Pod A → Pod C, DROPPED, reason=POLICY_DENIED ✓
tcpdump: VXLAN frames sent from Node 1 to Node 2 ✗ ← UNEXPECTED

Possible causes:
  ┌─────────────────────────────────────────────────────────────┐
  │  This should NOT happen if Cilium is correctly configured   │
  │  Cilium drops at the SOURCE (egress from lxc_pod_a)         │
  │  before encapsulation, so tcpdump on eth0 should see ZERO   │
  │  frames for a dropped flow.                                 │
  │                                                             │
  │  If you DO see VXLAN frames for a DROPPED flow:             │
  │  → egress NetworkPolicy is not applied at lxc_pod_a         │
  │  → only ingress policy at lxc_pod_c is dropping            │
  │  → packet traveled the network and was dropped at dest      │
  │  → this is less efficient (wasted bandwidth) and means      │
  │     egress policy is missing or misconfigured               │
  └─────────────────────────────────────────────────────────────┘

  Correct behavior:
    EGRESS drop at source: tcpdump sees NO VXLAN frame
    INGRESS drop at dest:  tcpdump sees VXLAN frame arrive, no TCP response

  Security implication: ingress-only policy enforcement wastes bandwidth
  and leaks traffic patterns (an observer on the fabric sees the packet
  even though it's dropped). Egress enforcement stops it before encap.


SCENARIO 4: tcpdump shows traffic, Hubble shows DROPPED
────────────────────────────────────────────────────────
Hubble:  DROPPED, reason=POLICY_DENIED
tcpdump: VXLAN frame arrives on Node 2 eth0

Interpretation:
  ┌─────────────────────────────────────────────────────────────┐
  │  Egress policy on Node 1 is MISSING or PERMISSIVE           │
  │  Ingress policy on Node 2 is ENFORCING                      │
  │                                                             │
  │  The packet traversed the entire underlay fabric            │
  │  and was dropped at the destination                         │
  │  This is policy working, but not optimally                  │
  │                                                             │
  │  Correct policy design: DROP at egress (source) first       │
  │  Both egress and ingress policies should be configured       │
  └─────────────────────────────────────────────────────────────┘


SCENARIO 5: Large RTT gap between tcpdump and Hubble measurements
──────────────────────────────────────────────────────────────────
tcpdump RTT (wire level):  2ms   (underlay is fast)
Hubble RTT (flow level):   45ms  (much higher)

Gap of 43ms explained:
  ┌─────────────────────────────────────────────────────────────┐
  │  eBPF program execution is delayed because:                 │
  │  a) CPU is over-scheduled — eBPF TC hook runs on the CPU    │
  │     that receives the softirq, but that CPU is busy         │
  │  b) NAPI poll budget exceeded — kernel processes only N     │
  │     packets per NAPI poll cycle, remaining queued           │
  │  c) RPS/RFS is redirecting packets across CPUs, adding      │
  │     inter-CPU latency (IPI: inter-processor interrupt)      │
  │  d) cilium-agent is under load — perf event ring buffer     │
  │     is delayed, making Hubble timestamps stale              │
  └─────────────────────────────────────────────────────────────┘
```

---

## The Security Visibility Gap: What tcpdump Alone Cannot Tell You

This is the most important lesson from this step. Without Hubble's identity layer, tcpdump leaves critical security questions unanswerable.

```
SECURITY QUESTIONS AND TOOL COVERAGE

Question                                    tcpdump    Hubble
───────────────────────────────────────────────────────────────────────
"Is this traffic authorized?"               NO ✗       YES ✓
"Which pod sent this packet?"               NO ✗       YES ✓
"Which NetworkPolicy allowed this?"         NO ✗       YES ✓
"Was this connection attempt blocked?"      PARTIAL    YES ✓
"Did the destination pod actually get it?"  NO ✗       YES ✓
"What labels does the source have?"         NO ✗       YES ✓
"Is the source identity spoofed?"           NO ✗       YES ✓
"Which protocol (HTTP/gRPC/DNS)?"           YES*       YES ✓
"What is the HTTP response code?"           YES*       YES ✓
"Is this a new flow or existing?"           YES        YES ✓
"What is the exact VXLAN VNI?"              YES ✓      NO ✗
"Is there encapsulation overhead?"          YES ✓      NO ✗
"What is the underlay RTT?"                 YES ✓      NO ✗
"Are packets being retransmitted?"          YES ✓      NO ✗
"Is there MTU fragmentation?"               YES ✓      NO ✗
"Which physical node sent this?"            YES ✓      YES ✓
"Is TLS encrypted?"                         YES ✓      PARTIAL

* tcpdump can see this only if traffic is unencrypted

───────────────────────────────────────────────────────────────────────

The critical security gap in tcpdump-only observability:

  IP 10.0.0.15 sends traffic to 10.0.1.10:5432 (PostgreSQL)
  tcpdump sees: connection attempt, allowed through
  tcpdump CANNOT say: was this authorized? who is 10.0.0.15?

  What if 10.0.0.15 was recently reassigned to a different pod?
  What if the old pod was compromised and the IP was recycled?
  tcpdump sees the same bytes either way.

  Hubble says: identity 12345 (app=compromised-pod, env=prod)
               DROPPED, reason=POLICY_DENIED
               (policy: only app=backend can reach app=database)

  This is why identity-based observability is a security primitive,
  not just an operational convenience. IP addresses are ephemeral
  and can be recycled. Cryptographic identities cannot be spoofed.
```

---

## Correlating a Complete Incident: From Wire to Identity

A worked example of what a lateral movement attempt looks like across both layers.

```
INCIDENT: Compromised frontend pod attempting to reach database

PHYSICAL LAYER (tcpdump on Node 1 eth0):
─────────────────────────────────────────
T=0.000  172.18.0.2.54440 > 172.18.0.3.4789: VXLAN VNI 1
         inner: 10.0.0.15.54923 > 10.0.1.20.5432: TCP SYN
T=0.001  (no SYN-ACK seen — packet dropped at destination)
T=3.001  172.18.0.2.54440 > 172.18.0.3.4789: VXLAN VNI 1
         inner: 10.0.0.15.54923 > 10.0.1.20.5432: TCP SYN (retransmit)
T=6.001  (retransmit again)
T=12.001 (retransmit again)
... connection eventually times out

tcpdump tells you:
  ✓ Someone at 10.0.0.15 tried to connect to 10.0.1.20:5432 (PostgreSQL)
  ✓ VXLAN frames were sent from Node 1 to Node 2
  ✗ You do NOT know who 10.0.0.15 is
  ✗ You do NOT know why the connection failed
  ✗ You do NOT know if this was authorized


IDENTITY LAYER (Hubble):
─────────────────────────
T=0.000  DROPPED
         src: default/frontend-xyz-abc (ip: 10.0.0.15)
         src_identity: 12345 (app=frontend, env=prod)
         dst: default/database-def-uvw (ip: 10.0.1.20)
         dst_identity: 12347 (app=database, env=prod)
         protocol: TCP, dst_port: 5432
         direction: INGRESS (dropped at destination ingress)
         drop_reason: POLICY_DENIED
         policy_name: <none matching>
         node: kind-worker

Hubble tells you:
  ✓ The specific pod name: frontend-xyz-abc
  ✓ Its identity and labels: app=frontend (this should NOT reach database)
  ✓ The attempt was blocked by NetworkPolicy
  ✓ The drop was at INGRESS on the destination (egress policy missing on source)
  ✓ No matching allow policy exists for this identity pair
  ✗ You do NOT know the VXLAN encapsulation details
  ✗ You do NOT know the underlay RTT


COMBINED INSIGHT:
─────────────────
tcpdump: VXLAN packets reaching Node 2 (egress policy on Node 1 is absent)
Hubble:  POLICY_DENIED at ingress on Node 2 (ingress policy is enforcing)

Conclusion: The NetworkPolicy is working correctly at the destination,
            but there is a gap — the source pod (frontend) is not subject
            to an egress NetworkPolicy, so the packet travels the entire
            network before being dropped at the destination.

Remediation indicated: Add egress NetworkPolicy to frontend namespace
                       blocking egress to database port 5432.
                       After fix: tcpdump will show NO VXLAN frames at all
                       for this flow. eBPF will drop it before encapsulation.
```

---

## The Mental Model to Carry Forward

```
CLOUD PACKET DUALITY — THE PERMANENT MENTAL MODEL

For every cross-node packet, hold two mental images simultaneously:

IMAGE 1 (Physical / Underlay):               IMAGE 2 (Identity / Overlay):
────────────────────────────────             ──────────────────────────────
Outer: node IP → node IP                     Source: pod-name, labels, identity
Encap: VXLAN, VNI, UDP entropy               Destination: pod-name, labels, identity
Wire:  bytes, frames, timing, RTT            Policy: which rule allowed/denied
Path:  ToR → Spine → Core → ToR             Verdict: FORWARDED / DROPPED
Perf:  bandwidth, retransmits, MTU           L7: protocol, method, status, latency
Trust: none (physical fabric is shared)      Trust: cryptographic identity (SPIFFE)

WHEN DEBUGGING:         start with Hubble (identity + verdict)
                        then go to tcpdump (wire + timing + MTU)

WHEN SECURITY AUDITING: start with Hubble (what is authorized?)
                        then verify with tcpdump (is encapsulation correct?)

WHEN CAPACITY PLANNING: start with tcpdump (wire-level bandwidth)
                        correlate with Hubble (which identities drive load)

THE PACKET IS BOTH THINGS AT ONCE.
Never think in only one layer.
```

---

## Next 3 Steps

**Step 2A:** Observe the MTU effect directly. Generate a large file transfer between two pods on different nodes and watch tcpdump for ICMP Type 3 Code 4 "Fragmentation Needed" messages — these are the underlay's way of telling the sender that its packets are too large after VXLAN encapsulation. Correlate the exact packet size where fragmentation begins with the MTU arithmetic shown above (1500 - 50 - 14 = 1436). This makes MTU a concrete, observable phenomenon rather than an abstract number.

**Step 2B:** Observe the ECMP entropy. Run three simultaneous pod-to-pod transfers between the same two nodes and capture on the docker bridge (`docker0` on host). Observe the outer UDP source ports — each flow should have a different source port derived from its inner 5-tuple. Verify the source ports are consistent for each flow (all packets of one TCP session use the same outer src port) but differ between flows. This validates the entropy mechanism described in the ECMP section above.

**Step 3 (the original):** Read the Cilium eBPF source — specifically `bpf/bpf_lxc.c` for the per-endpoint program that implements every decision you observed here, `bpf/lib/policy.h` for the policy map lookup that produces the FORWARDED/DROPPED verdicts, and `bpf/lib/encap.h` for the VXLAN encapsulation logic. Every diagram in this step corresponds to actual C code in those files. Reading the source converts the diagrams from conceptual models into precise, auditable implementations — which is the standard required to contribute to or evaluate production CNI security.

# Step 3: The eBPF Source — From Diagrams to Kernel Implementation

**Summary:** Reading the Cilium eBPF source converts every diagram from Steps 1 and 2 into precise, auditable kernel instructions. The three files — `bpf_lxc.c`, `lib/policy.h`, and `lib/encap.h` — together implement the complete per-packet lifecycle: identity resolution, policy verdict, connection tracking, and VXLAN encapsulation. Understanding their internal architecture, data structures, execution flow, and interdependencies gives you the implementation-level mental model needed to audit CNI security, reason about failure modes, and contribute production-grade changes. This step is about how the theory becomes verifiable kernel logic — every abstraction you learned has a concrete, inspectable implementation.

---

## The Source Tree: How the Files Relate

Before reading any single file, understand where it sits in the broader architecture and what it owns.

```
cilium/bpf/  (the entire eBPF data plane)
│
├── bpf_lxc.c          ← THE MAIN ENDPOINT PROGRAM
│   │                     Attached to every pod's veth (lxc interface)
│   │                     TC hook: ingress + egress
│   │                     Orchestrates: calls policy, NAT, encap
│   │                     This is the "main()" of per-packet processing
│   │
├── bpf_overlay.c      ← VXLAN TUNNEL ENDPOINT PROGRAM
│   │                     Attached to cilium_vxlan interface
│   │                     Handles: decapsulation on ingress
│   │                     Calls: policy for cross-node traffic
│   │
├── bpf_host.c         ← HOST NETWORK PROGRAM
│   │                     Attached to host-facing interfaces
│   │                     Handles: host-to-pod and pod-to-host traffic
│   │
├── lib/
│   ├── policy.h       ← POLICY ENGINE LIBRARY
│   │                     Implements: policy map lookup
│   │                     Owns: verdict computation (ALLOW/DROP)
│   │                     Called by: bpf_lxc.c, bpf_overlay.c
│   │
│   ├── encap.h        ← ENCAPSULATION LIBRARY
│   │                     Implements: VXLAN/Geneve encapsulation
│   │                     Owns: outer header construction
│   │                     Called by: bpf_lxc.c when dst is remote node
│   │
│   ├── conntrack.h    ← CONNECTION TRACKING LIBRARY
│   │                     Implements: CT map lookup + creation
│   │                     Owns: stateful connection state
│   │                     Called by: policy.h before rule evaluation
│   │
│   ├── nat.h          ← NAT / SERVICE LB LIBRARY
│   │                     Implements: DNAT for services, SNAT for egress
│   │                     Owns: NAT map entries
│   │
│   ├── eps.h          ← ENDPOINT MAP LIBRARY
│   │                     Implements: local endpoint lookups
│   │                     Owns: mapping PodIP → endpoint identity
│   │
│   ├── ipv4.h         ← IPv4 HEADER MANIPULATION
│   │                     Implements: checksum recalculation after rewrite
│   │
│   └── maps.h         ← MAP DEFINITIONS
│                         Declares: all eBPF map types and sizes
│                         This is the schema of the kernel data plane
│
└── include/
    └── bpf/
        └── helpers.h  ← KERNEL HELPER DECLARATIONS
                          bpf_map_lookup_elem, bpf_redirect,
                          bpf_perf_event_output, etc.
```

**The dependency graph — what calls what:**

```
                    bpf_lxc.c
                   (per-packet orchestrator)
                  /      |       |      \
                 /       |       |       \
          conntrack.h  policy.h  nat.h  encap.h
                |         |
              maps.h    maps.h
                |         |
           (CT map)  (policy map)
```

Every packet processed by Cilium flows through `bpf_lxc.c`. That file calls the libraries. The libraries read/write eBPF maps. The maps are the shared state between data plane and control plane. This is the complete architecture in one dependency graph.

---

## bpf_lxc.c: The Per-Endpoint Program Architecture

`bpf_lxc.c` is not a single function — it is a collection of TC hook entry points, each handling a specific traffic direction and address family.

```
bpf_lxc.c ENTRY POINTS
══════════════════════════════════════════════════════════════════════

TC Hook Attachment Points on a pod's lxc (veth host side):

                    lxc_pod_a  (host-side veth interface)
                         │
           ┌─────────────┴─────────────┐
           │                           │
    EGRESS direction              INGRESS direction
    (traffic LEAVING pod)         (traffic ARRIVING at pod)
           │                           │
           ▼                           ▼
  ┌─────────────────┐        ┌──────────────────┐
  │  handle_egress  │        │  handle_ingress   │
  │  entry point    │        │  entry point      │
  │                 │        │                   │
  │  Called when:   │        │  Called when:     │
  │  pod sends a    │        │  packet arrives   │
  │  packet out     │        │  destined for pod │
  └────────┬────────┘        └────────┬──────────┘
           │                          │
           │                          │
           ▼                          ▼
  ┌─────────────────┐        ┌──────────────────┐
  │  IPv4 or IPv6?  │        │  IPv4 or IPv6?   │
  └────────┬────────┘        └────────┬──────────┘
           │                          │
     ┌─────┴─────┐              ┌─────┴──────┐
     ▼           ▼              ▼            ▼
  tail_ipv4   tail_ipv6      tail_ipv4    tail_ipv6
  _egress     _egress        _ingress     _ingress

══════════════════════════════════════════════════════════════════════

WHY TAIL CALLS?

eBPF programs have a stack size limit (512 bytes) and historically had
an instruction limit (1 million verified instructions in modern kernels,
but the verifier's complexity budget can be exhausted).

Cilium uses eBPF TAIL CALLS to chain programs:

  Program A finishes → tail calls Program B
                        (stack is reset, new program starts)
                        (counts as one of 32 max chained calls)

This allows the complete packet processing pipeline to be split across
multiple eBPF programs, each staying within verifier limits.

  handle_egress → [parse headers] → tail call → tail_ipv4_egress
                                                       │
                                              [conntrack lookup]
                                                       │
                                              [policy lookup]
                                                       │
                                           [local? redirect]
                                           [remote? encap + send]
```

---

## The Egress Processing Pipeline: Every Decision Point

The complete decision tree for a packet leaving a pod, as implemented in `bpf_lxc.c` calling its libraries.

```
EGRESS PIPELINE: Pod A sends a packet
══════════════════════════════════════════════════════════════════════

STAGE 0: PACKET ARRIVAL AT TC EGRESS HOOK
──────────────────────────────────────────
Packet enters lxc_pod_a TC egress hook
         │
         ▼
  Is this an ARP packet?
  ├── YES → handle_arp() [reply with cilium_host MAC, drop original]
  └── NO  → continue

  Is this IPv4 or IPv6?
  ├── IPv4 → tail_call to ipv4_egress handler
  └── IPv6 → tail_call to ipv6_egress handler
  └── other protocol → pass through (or drop if policy requires)


STAGE 1: HEADER PARSING AND VALIDATION
────────────────────────────────────────
  Parse IPv4 header:
  - Extract src IP, dst IP, protocol, TTL
  - Validate: is packet truncated? (skb->len check)
  - Validate: is IP header checksum valid?

  Parse L4 header (TCP/UDP/ICMP):
  - Extract src port, dst port
  - For TCP: extract flags (SYN, ACK, RST, FIN)

  Build "tuple" structure:
  ┌──────────────────────────────────┐
  │  struct ipv4_ct_tuple            │
  │  ├── src IP:   10.0.0.15        │
  │  ├── dst IP:   10.0.1.10        │
  │  ├── src port: 52341            │
  │  ├── dst port: 8080             │
  │  └── proto:    TCP              │
  └──────────────────────────────────┘
  This tuple is the key for ALL subsequent map lookups


STAGE 2: SERVICE / NAT LOOKUP (before policy)
──────────────────────────────────────────────
  Is dst IP a Service ClusterIP?

  Lookup: service_map[dst IP:port]
  ├── FOUND (it's a Service):
  │    Select backend pod IP (load balancing)
  │    Rewrite dst IP in packet: ClusterIP → PodIP
  │    Rewrite dst port if needed (service port → pod port)
  │    Record NAT entry in nat_map
  │    Update tuple with new dst IP for subsequent lookups
  │    └── continue with DNAT'd dst IP
  │
  └── NOT FOUND (direct pod-to-pod):
       dst IP is already a real pod IP
       continue with original dst IP


STAGE 3: CONNECTION TRACKING LOOKUP
─────────────────────────────────────
  Lookup: ct_map[tuple] (connection tracking table)

  ┌─────────────────────────────────────────────────────────────┐
  │  CT STATES AND THEIR MEANING IN POLICY PROCESSING           │
  │                                                             │
  │  CT_NEW:          No existing entry → new connection        │
  │                   Must go through full policy check         │
  │                                                             │
  │  CT_ESTABLISHED:  Entry exists, connection established      │
  │                   Policy already allowed the SYN            │
  │                   → SKIP FULL POLICY CHECK                  │
  │                   → forward immediately (fast path)         │
  │                                                             │
  │  CT_RELATED:      ICMP error related to existing conn       │
  │                   → allow (it's a response to allowed conn) │
  │                                                             │
  │  CT_REOPENED:     Connection was half-closed, now new data  │
  │                   → re-evaluate policy                      │
  └─────────────────────────────────────────────────────────────┘

  ┌─── CT FAST PATH ──────────────────────────────────────────┐
  │  If CT_ESTABLISHED:                                        │
  │  - Update CT entry timestamp (keep-alive)                  │
  │  - Update byte/packet counters in CT entry                 │
  │  - Skip to STAGE 5 (forwarding decision)                   │
  │  - NO policy map lookup needed                             │
  │  This is why established connections have near-zero        │
  │  policy overhead: only the CT lookup (O(1) hash) needed    │
  └────────────────────────────────────────────────────────────┘

  If CT_NEW → proceed to policy check


STAGE 4: POLICY ENFORCEMENT (new connections only)
────────────────────────────────────────────────────
  [Detailed in policy.h section below]

  Inputs to policy engine:
  ├── src_identity: (from ipcache lookup of src IP)
  ├── dst_identity: (from ipcache lookup of dst IP)
  ├── dst_port:     (from tuple)
  └── protocol:     (from tuple)

  Output:
  ├── ALLOW → create CT entry as CT_ESTABLISHED, continue
  └── DROP  → emit Hubble drop event, kfree_skb, return DROP


STAGE 5: FORWARDING DECISION
──────────────────────────────
  Is dst IP on this node?

  Lookup: endpoint_map[dst IP]
  ├── FOUND (local endpoint — same node):
  │    bpf_redirect(lxc_pod_b_ifindex, BPF_F_INGRESS)
  │    Packet is redirected to dst pod's veth, ingress side
  │    → STAGE 6A (local delivery)
  │
  └── NOT FOUND (remote endpoint — different node):
       Lookup: ipcache[dst IP] → get VTEP (node IP of dst pod)
       → STAGE 6B (encapsulation + remote send)


STAGE 6A: LOCAL DELIVERY (same-node)
──────────────────────────────────────
  bpf_redirect(dst_lxc_ifindex, BPF_F_INGRESS)
  ┌─────────────────────────────────────────────┐
  │  The skb (socket buffer) is moved directly  │
  │  from src veth TX queue to dst veth RX queue │
  │  without:                                   │
  │  - IP stack traversal                       │
  │  - Routing table lookup                     │
  │  - Linux bridge forwarding                  │
  │  - Any additional memory copy               │
  │                                             │
  │  The skb pointer is handed to the ingress   │
  │  TC hook of the destination veth            │
  │  → policy check runs AGAIN (ingress policy) │
  └─────────────────────────────────────────────┘


STAGE 6B: REMOTE DELIVERY (cross-node, via encap.h)
──────────────────────────────────────────────────────
  [Detailed in encap.h section below]

  encap_and_redirect_with_nodeid(skb, tunnel_endpoint_ip, ...)
  → VXLAN encapsulation
  → bpf_redirect(cilium_vxlan_ifindex, 0)
  → packet exits via node's physical NIC toward remote node

══════════════════════════════════════════════════════════════════════
```

---

## lib/policy.h: The Policy Engine — Deep Architecture

`policy.h` implements the core security decision. Every allow/deny verdict for a new connection passes through this code.

### The Policy Map: Schema and Structure

The policy map is a **per-endpoint** eBPF map. Each pod has its own policy map, not a shared global one.

```
POLICY MAP STRUCTURE
══════════════════════════════════════════════════════════════════════

Per-endpoint map:  one map per pod, keyed by endpoint ID
Map type:          BPF_MAP_TYPE_HASH (kernel hash table)

KEY STRUCTURE (what you look up):
┌─────────────────────────────────────────────────────────────────┐
│  struct policy_key                                              │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  remote_label_id  (u32)  ← Cilium identity of the peer │    │
│  │  dst_port         (u16)  ← destination port            │    │
│  │  proto            (u8)   ← protocol (TCP=6, UDP=17...) │    │
│  │  egress           (u8)   ← 0=ingress, 1=egress         │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

VALUE STRUCTURE (what the lookup returns):
┌─────────────────────────────────────────────────────────────────┐
│  struct policy_entry                                            │
│  ┌────────────────────────────────────────────────────────┐    │
│  │  deny             (u8)   ← 0=allow, 1=deny             │    │
│  │  auth_type        (u8)   ← mutual auth required?       │    │
│  │  pad              (u16)  ← alignment                   │    │
│  │  proxy_port       (u16)  ← redirect to proxy? (L7 GW) │    │
│  │  pad2             (u16)  ← alignment                   │    │
│  │  packets          (u64)  ← matched packet counter      │    │
│  │  bytes            (u64)  ← matched byte counter        │    │
│  └────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

WILDCARD ENTRIES:
The policy map supports wildcard matching via special key values:

  remote_label_id = 0     → matches ANY identity (wildcard source)
  dst_port = 0            → matches ANY port
  proto = 0               → matches ANY protocol

Lookup algorithm evaluates MOST SPECIFIC to LEAST SPECIFIC:
  1. (exact identity, exact port, exact proto)
  2. (exact identity, exact port, wildcard proto)
  3. (exact identity, wildcard port, wildcard proto)
  4. (wildcard identity, exact port, exact proto)
  5. (wildcard identity, wildcard port, wildcard proto)
  → first match wins

══════════════════════════════════════════════════════════════════════
```

### The Policy Lookup Algorithm

```
POLICY LOOKUP EXECUTION FLOW (policy_can_access in policy.h)
══════════════════════════════════════════════════════════════════════

Inputs:
  src_identity = 12345   (app=frontend)
  dst_identity = 12347   (app=database, owns this policy map)
  dst_port     = 5432
  proto        = TCP
  direction    = INGRESS (database pod's ingress policy map)

Step 1: Build exact-match key
─────────────────────────────
  key = { remote_label_id: 12345, dst_port: 5432, proto: 6, egress: 0 }
  result = bpf_map_lookup_elem(&policy_map, &key)

  result == NULL → no exact match, try wildcards


Step 2: Try port wildcard
──────────────────────────
  key = { remote_label_id: 12345, dst_port: 0, proto: 0, egress: 0 }
  result = bpf_map_lookup_elem(&policy_map, &key)

  result == NULL → no match for this identity at all


Step 3: Try identity wildcard with exact port
──────────────────────────────────────────────
  key = { remote_label_id: 0, dst_port: 5432, proto: 6, egress: 0 }
  result = bpf_map_lookup_elem(&policy_map, &key)

  result == NULL → no rule allows any identity to port 5432


Step 4: Try full wildcard
──────────────────────────
  key = { remote_label_id: 0, dst_port: 0, proto: 0, egress: 0 }
  result = bpf_map_lookup_elem(&policy_map, &key)

  result == NULL → no catch-all allow rule


Step 5: No rule matched → DEFAULT DENY
────────────────────────────────────────
  verdict = DROP
  reason  = POLICY_DENIED
  send Hubble drop event via bpf_perf_event_output()
  return CTX_ACT_DROP


CONTRAST: What happens if only backend can reach database
──────────────────────────────────────────────────────────
  Backend identity = 12346 (app=backend)

  cilium-agent programs database's policy map with:
  key   = { remote_label_id: 12346, dst_port: 5432, proto: 6 }
  value = { deny: 0, proxy_port: 0, ... }

  Frontend (12345) lookup: key not found → DROP
  Backend  (12346) lookup: key FOUND, deny=0 → ALLOW
  World    (2)     lookup: key not found → DROP

══════════════════════════════════════════════════════════════════════
```

### The ipcache: Identity Resolution

Before the policy lookup, the eBPF program must resolve the peer IP to a security identity. This is the ipcache's job.

```
IPCACHE MAP: IP ADDRESS → SECURITY IDENTITY
══════════════════════════════════════════════════════════════════════

Map type:  BPF_MAP_TYPE_LPM_TRIE (Longest Prefix Match trie)
           ← not a flat hash, but a PREFIX-MATCH structure
           ← allows CIDR ranges, not just /32 host entries

WHY LPM TRIE?
  - Pod IPs are /32 host entries (exact match)
  - CIDR-based identities (node CIDRs, external CIDRs) are /8 to /32
  - World (internet) can be 0.0.0.0/0 (default entry)
  - The trie gives longest-prefix match semantics naturally

EXAMPLE IPCACHE CONTENT:
┌──────────────────────────────────────────────────────────────────┐
│  Prefix              │ Identity  │ Meaning                       │
│──────────────────────┼───────────┼───────────────────────────────│
│  10.0.0.15/32        │   12345   │ Pod A (app=frontend)          │
│  10.0.0.22/32        │   12346   │ Pod B (app=backend)           │
│  10.0.1.10/32        │   12347   │ Pod C (app=database)          │
│  10.0.0.0/24         │    1001   │ Node 1 pod CIDR               │
│  10.0.1.0/24         │    1002   │ Node 2 pod CIDR               │
│  172.18.0.2/32       │      1    │ Node 1 IP (reserved:host)     │
│  172.18.0.3/32       │      1    │ Node 2 IP (reserved:host)     │
│  0.0.0.0/0           │      2    │ World (reserved:world)        │
└──────────────────────────────────────────────────────────────────┘

LOOKUP EXAMPLE:
  IP: 10.0.0.15 →
    Matches: 10.0.0.15/32 (identity 12345)  ← most specific, wins
    Also matches: 10.0.0.0/24 (identity 1001)
    Also matches: 0.0.0.0/0 (identity 2)
    Result: identity 12345 (longest prefix match)

  IP: 8.8.8.8 →
    No /32 match
    No CIDR match
    Matches: 0.0.0.0/0 (identity 2 = world)
    Result: identity 2

IDENTITY PROPAGATION FOR CROSS-NODE TRAFFIC:
  How does Node 2 know that 10.0.0.15 is identity 12345?

  ┌──────────────────────────────────────────────────────────┐
  │  cilium-agent on Node 1 registers Pod A's identity       │
  │  with Cilium's KV store (etcd or CRD)                   │
  │                                                          │
  │  cilium-agent on Node 2 watches for identity changes     │
  │  and updates its LOCAL ipcache:                          │
  │  10.0.0.15/32 → identity 12345                          │
  │                                                          │
  │  For VXLAN tunnels, the identity can also be encoded     │
  │  in the tunnel metadata (Geneve TLV or VXLAN opt)        │
  │  → receiver reads identity from tunnel header            │
  │  → no ipcache lookup needed for tunnel traffic           │
  └──────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════
```

### Policy Check with Authentication (Mutual Auth)

```
WHEN auth_type IS SET IN POLICY ENTRY
══════════════════════════════════════════════════════════════════════

Standard policy check:
  bpf_map_lookup_elem → policy_entry.deny=0, auth_type=0
  → ALLOW immediately

Policy entry with auth requirement:
  bpf_map_lookup_elem → policy_entry.deny=0, auth_type=1 (mTLS required)

  ┌────────────────────────────────────────────────────────────┐
  │  Check auth_map[{src_identity, dst_identity}]              │
  │  Has this identity pair completed mTLS handshake?          │
  │                                                            │
  │  auth_map entry PRESENT and NOT EXPIRED:                   │
  │  → ALLOW (handshake previously completed)                  │
  │                                                            │
  │  auth_map entry ABSENT or EXPIRED:                         │
  │  → DROP this packet                                        │
  │  → Signal userspace (cilium-agent) via map                 │
  │  → cilium-agent initiates mTLS handshake between pods      │
  │  → On completion, auth_map entry created with expiry       │
  │  → Subsequent packets from this identity pair: ALLOW       │
  │                                                            │
  │  This is Cilium's mutual authentication mechanism          │
  │  (currently using SPIFFE/SPIRE integration)                │
  └────────────────────────────────────────────────────────────┘

  First packet of a mutually-authenticated flow: DROP + trigger auth
  After auth completes: all subsequent packets ALLOW (CT fast path)
  Auth expiry: periodic re-authentication required

══════════════════════════════════════════════════════════════════════
```

---

## lib/conntrack.h: The Stateful Connection Engine

Connection tracking in eBPF is fundamentally different from Linux conntrack (nf_conntrack). Cilium implements its own CT in eBPF maps to avoid the locking overhead of the kernel's conntrack.

```
CILIUM CT MAP: STRUCTURE AND SEMANTICS
══════════════════════════════════════════════════════════════════════

Two separate CT maps per node:
  cilium_ct4_global    ← global (cross-namespace) connections
  cilium_ct4_<ep_id>   ← per-endpoint (local connections to this pod)

Map type: BPF_MAP_TYPE_LPM_TRIE... actually BPF_MAP_TYPE_HASH
          with hash(tuple) as key

CT ENTRY KEY:
┌─────────────────────────────────────────────────────────────────┐
│  struct ipv4_ct_tuple                                           │
│  ├── addr (daddr for egress, saddr for ingress)                │
│  ├── raddr (reverse addr)                                       │
│  ├── sport                                                      │
│  ├── dport                                                      │
│  ├── nexthdr (protocol)                                         │
│  └── flags (direction: INGRESS/EGRESS/INTERNAL)                 │
└─────────────────────────────────────────────────────────────────┘

CT ENTRY VALUE:
┌─────────────────────────────────────────────────────────────────┐
│  struct ct_entry                                                │
│  ├── lifetime       (u32) ← expiry timestamp (seconds)         │
│  ├── rx_packets     (u64) ← packets in reverse direction        │
│  ├── rx_bytes       (u64) ← bytes in reverse direction          │
│  ├── tx_packets     (u64) ← packets in forward direction        │
│  ├── tx_bytes       (u64) ← bytes in forward direction          │
│  ├── proxy_port     (u16) ← if L7 proxy redirect active        │
│  ├── src_sec_id     (u32) ← identity of connection initiator   │
│  ├── rx_closing     (u1)  ← FIN received on reverse            │
│  ├── tx_closing     (u1)  ← FIN received on forward            │
│  ├── lb_loopback    (u1)  ← service loopback connection         │
│  ├── seen_non_syn   (u1)  ← non-SYN packet seen (rst protect)  │
│  └── tcp_flags_seen (u16) ← all TCP flags seen in session      │
└─────────────────────────────────────────────────────────────────┘

CT LOOKUP AND CREATION FLOW:
─────────────────────────────

  New TCP SYN arrives:
         │
         ▼
  ct_lookup4(ct_map, &tuple, CT_EGRESS)
         │
  ┌──────┴──────────────────────────────────────┐
  │  Hash tuple → bucket                         │
  │  Walk bucket linked list for exact match     │
  │                                              │
  │  FOUND → return state (ESTABLISHED/RELATED)  │
  │  NOT FOUND → return CT_NEW                   │
  └──────┬──────────────────────────────────────┘
         │
  If CT_NEW and policy ALLOWS:
         │
         ▼
  ct_create4(ct_map, &tuple, skb, ...)
  ┌──────────────────────────────────────────────┐
  │  Allocate CT entry in map                    │
  │  Set lifetime = now + CT_SYN_TIMEOUT (60s)   │
  │  Set src_sec_id = src identity               │
  │  Set state = CT_NEW (waiting for SYN-ACK)    │
  │                                              │
  │  Also create REVERSE tuple entry:            │
  │  reverse_tuple = { swap src/dst }            │
  │  → so reply packets (SYN-ACK) hit fast path  │
  └──────────────────────────────────────────────┘

  When SYN-ACK arrives (reverse direction):
         │
         ▼
  ct_lookup4(ct_map, &reverse_tuple)
  → FOUND (the reverse entry created above)
  → state updates to CT_ESTABLISHED
  → lifetime extended to CT_CONNECTION_LIFETIME (21600s default)

  Established packets (fast path):
         │
  ct_lookup4 → FOUND, CT_ESTABLISHED
  → update timestamp + counters
  → SKIP policy check
  → forward immediately


CT GARBAGE COLLECTION:
─────────────────────
eBPF maps have fixed size (max_entries). When CT map is full,
new connections cannot be tracked → policy cannot be enforced → DROP.

Cilium runs a CT GC goroutine in userspace (cilium-agent) that
periodically walks the CT map and deletes expired entries:
  - TCP TIME_WAIT entries: 10 seconds (much shorter than kernel's 4min)
  - TCP established: 6 hours (configurable)
  - UDP entries: 60 seconds
  - ICMP entries: 60 seconds

The GC is NOT done in eBPF (no iteration in old kernels).
In newer kernels: BPF_MAP_TYPE_LRU_HASH provides automatic eviction
of least-recently-used entries when map is full.

══════════════════════════════════════════════════════════════════════
```

---

## lib/encap.h: The Encapsulation Engine

`encap.h` implements the construction of VXLAN (and Geneve) outer headers and the forwarding of the encapsulated packet toward the remote VTEP.

```
ENCAP.H ARCHITECTURE
══════════════════════════════════════════════════════════════════════

The encapsulation library has one primary job:
  Take an inner packet (skb pointing to inner IP header)
  + a destination VTEP IP (remote node IP)
  + a VNI / tunnel key
  → Produce a VXLAN-encapsulated packet
  → Redirect it out the node's cilium_vxlan interface

TUNNEL MAP: Which IP lives on which VTEP
─────────────────────────────────────────
Before encapsulation, we need to know which node hosts the dst pod.

Map: cilium_tunnel_map
  Key:   dst pod IP (or CIDR)
  Value: VTEP IP (the node IP of the remote node)

┌─────────────────────────────────────────────────────────────────┐
│  Example tunnel map:                                            │
│  10.0.1.10/32 → VTEP: 172.18.0.3  (Pod C is on Node 2)        │
│  10.0.1.15/32 → VTEP: 172.18.0.3  (Pod D is on Node 2)        │
│  10.0.2.5/32  → VTEP: 172.18.0.4  (Pod E is on Node 3)        │
│                                                                 │
│  This map is maintained by cilium-agent watching Kubernetes     │
│  Node objects and updating the map when nodes join/leave        │
└─────────────────────────────────────────────────────────────────┘

ENCAPSULATION DECISION POINT IN bpf_lxc.c:
────────────────────────────────────────────

  After policy ALLOW, forwarding decision:
         │
         ▼
  Is dst IP in local endpoint map?
  ├── YES (same node) → bpf_redirect to local lxc
  └── NO  (remote)   → lookup tunnel_map[dst IP] → get VTEP IP
                               │
                               ▼
                        encap_and_redirect_with_nodeid(
                            skb,
                            tunnel_endpoint = 172.18.0.3,
                            tunnel_id = VNI,
                            src_id = src_identity  ← embedded in tunnel
                        )

══════════════════════════════════════════════════════════════════════
```

### The Encapsulation Mechanics: What encap.h Does to the skb

```
SKB (socket buffer) TRANSFORMATION DURING ENCAPSULATION
══════════════════════════════════════════════════════════════════════

BEFORE encapsulation (skb as it arrives from lxc TC hook):

skb->data points here:
       ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ [Inner Eth]  │ [Inner IP]   │ [TCP/UDP]    │ [Payload]    │
│ (may be      │ src:10.0.0.15│ sport:52341  │ HTTP data    │
│  dummy MACs) │ dst:10.0.1.10│ dport:8080   │              │
└──────────────┴──────────────┴──────────────┴──────────────┘

STEP 1: bpf_skb_adjust_room(skb, encap_size, ...)
─────────────────────────────────────────────────
  Extend skb headroom to make space for outer headers.
  encap_size = sizeof(outer_eth) + sizeof(outer_ip) +
               sizeof(udp) + sizeof(vxlan)
             = 14 + 20 + 8 + 8 = 50 bytes

  After adjustment:
  skb->data points here:
         ↓
  ┌────────────────────────────────────────────────────────────────┐
  │ [50 bytes headroom - UNINITIALIZED] │ [Inner packet as above] │
  └────────────────────────────────────────────────────────────────┘

STEP 2: Write VXLAN header (working backwards from inner packet)
──────────────────────────────────────────────────────────────────
  vxlan_hdr->vx_flags = VXLAN_VNI_FLAG  (0x08000000 big-endian)
  vxlan_hdr->vx_vni   = VNI << 8        (VNI in top 24 bits)

  ┌───────────────────────────────────────────────────────────────┐
  │ [42 bytes uninitialized] │ [VXLAN 8B] │ [Inner packet]       │
  └───────────────────────────────────────────────────────────────┘

STEP 3: Write UDP header
─────────────────────────
  udp->source = derive_src_port(inner_tuple)
    ← hash(inner src IP XOR dst IP, sport XOR dport)
    ← result in range 49152-65535 (ephemeral)
    ← DETERMINISTIC for same flow, DIFFERENT for different flows
  udp->dest   = VXLAN_PORT (4789)
  udp->len    = inner_packet_len + sizeof(vxlan) + sizeof(udp)
  udp->check  = 0  (UDP checksum optional for VXLAN, often skipped)

  ┌─────────────────────────────────────────────────────────────┐
  │ [34 bytes] │ [UDP 8B] │ [VXLAN 8B] │ [Inner packet]        │
  └─────────────────────────────────────────────────────────────┘

STEP 4: Write outer IP header
──────────────────────────────
  ip->version  = 4
  ip->ihl      = 5
  ip->tos      = inner IP TOS  (ECN bits copied for congestion signal)
  ip->tot_len  = UDP len + sizeof(outer_ip)
  ip->id       = random (or 0 with DF)
  ip->frag_off = htons(IP_DF)  ← CRITICAL: Don't Fragment set
                                  relies on PMTUD, not fragmentation
  ip->ttl      = 64
  ip->protocol = IPPROTO_UDP  (17)
  ip->saddr    = THIS_NODE_IP  (172.18.0.2)
  ip->daddr    = VTEP_IP       (172.18.0.3)
  ip->check    = ip_checksum(...)

  ┌──────────────────────────────────────────────────────────────┐
  │ [14 bytes] │ [Outer IP 20B] │ [UDP 8B] │ [VXLAN] │ [Inner] │
  └──────────────────────────────────────────────────────────────┘

STEP 5: Write outer Ethernet header
─────────────────────────────────────
  eth->h_dest   = MAC of next hop (gateway MAC, from ARP/FDB)
  eth->h_source = THIS_NODE_NIC_MAC
  eth->h_proto  = ETH_P_IP (0x0800)

  ┌─────────────────────────────────────────────────────────────┐
  │[Eth 14B]│[Outer IP 20B]│[UDP 8B]│[VXLAN 8B]│[Inner packet]│
  └─────────────────────────────────────────────────────────────┘

STEP 6: bpf_redirect(cilium_vxlan_ifindex, 0)
──────────────────────────────────────────────
  Redirect fully-encapsulated skb to cilium_vxlan TX path
  cilium_vxlan is a Linux VXLAN device → handles actual socket send
  Outer IP routing lookup routes to eth0 → NIC TX ring → wire

══════════════════════════════════════════════════════════════════════
```

### Identity Embedding in the Tunnel

```
HOW IDENTITY TRAVELS ACROSS THE TUNNEL
══════════════════════════════════════════════════════════════════════

Problem: Node 2 needs to know the IDENTITY of the packet source
         (Pod A's identity 12345) to do policy enforcement.

         It cannot just do ipcache[10.0.0.15] on Node 2
         because it might not have that entry yet,
         or IP could theoretically be recycled.

Solution: Embed the identity in the tunnel header.

TWO MECHANISMS:

Mechanism 1: VXLAN GBP (Group-Based Policy) extension
──────────────────────────────────────────────────────
  VXLAN has an optional "GBP" flag that allows a 16-bit policy tag
  to be embedded in the VXLAN header.

  Cilium can use this to carry a truncated identity:
  ┌──────────────────────────────────────────┐
  │  VXLAN header (8 bytes)                  │
  │  flags: 0x88 (I-flag + GBP-flag set)     │
  │  policy tag: <lower 16 bits of identity> │
  │  VNI: cluster VNI                        │
  └──────────────────────────────────────────┘

  Limitation: 16 bits = only 65535 unique identities in GBP field
  Cilium has 24-bit identities, so GBP can only carry local identities
  (well-known identities < 65535)

Mechanism 2: Geneve TLV Options (preferred)
─────────────────────────────────────────────
  Geneve supports variable-length TLV options in the header.
  Cilium adds a custom TLV option carrying the full 32-bit identity:

  ┌──────────────────────────────────────────────────────────────┐
  │  Geneve header                                               │
  │  ├── base header (8 bytes)                                   │
  │  │   ├── VNI (24 bits)                                       │
  │  │   └── opt_len field (length of TLV options)               │
  │  └── TLV options (variable)                                  │
  │       └── Cilium TLV:                                        │
  │           ├── class: 0x0108 (Cilium IANA enterprise number)  │
  │           ├── type:  0x01   (source identity)                │
  │           ├── len:   4      (4 bytes of data)                │
  │           └── data:  <full 32-bit Cilium identity>           │
  └──────────────────────────────────────────────────────────────┘

  On Node 2 (receiving side, in bpf_overlay.c):
    Parse Geneve TLV → extract identity from option
    Store in skb metadata (skb->cb[] scratch area)
    Pass to policy engine as src_identity
    No ipcache lookup needed for the identity resolution

Fallback: ipcache lookup at destination
────────────────────────────────────────
  If neither GBP nor Geneve TLV is available (plain VXLAN mode):
  Node 2 does: ipcache[src_pod_IP] → identity
  This requires Node 2's ipcache to be up to date
  cilium-agent's KV store sync ensures this with sub-second latency

══════════════════════════════════════════════════════════════════════
```

---

## The Verifier: Why eBPF Programs Look the Way They Do

Reading the Cilium source, you will notice patterns that seem unusual compared to normal C. These are all consequences of the eBPF verifier — the kernel component that checks every eBPF program before loading it.

```
THE eBPF VERIFIER AND ITS CONSTRAINTS
══════════════════════════════════════════════════════════════════════

The verifier performs STATIC ANALYSIS of the eBPF bytecode:
  - Simulates every possible execution path
  - Tracks the "type" and "range" of every register at every instruction
  - Ensures: no out-of-bounds memory access, no uninitialized reads,
             no unbounded loops, no invalid pointer arithmetic

WHY THIS SHAPES THE SOURCE CODE:

Constraint 1: BOUNDED LOOPS ONLY
──────────────────────────────────
  Traditional: for (int i = 0; i < n; i++) { ... }
               where n is a runtime value → REJECTED
               (verifier cannot bound loop iterations statically)

  eBPF required: for (int i = 0; i < MAX_POLICY_CHECKS; i++) { ... }
                 where MAX_POLICY_CHECKS is a compile-time constant
                 → ACCEPTED (verifier can unroll or bound iterations)

  Impact on policy.h: Wildcard lookup iteration is bounded by a
  compile-time constant (number of wildcard key variants to try).
  If you want to check N wildcards, N must be a constant.

Constraint 2: MAP VALUE POINTER VALIDATION
───────────────────────────────────────────
  After bpf_map_lookup_elem(), the returned pointer could be NULL
  (key not found). The verifier REQUIRES a NULL check before
  dereferencing the pointer.

  If the code does:
    struct policy_entry *entry = bpf_map_lookup_elem(&map, &key);
    if (entry->deny) { ... }   ← VERIFIER REJECTS (no NULL check)

  Must be:
    struct policy_entry *entry = bpf_map_lookup_elem(&map, &key);
    if (!entry) { goto deny; }
    if (entry->deny) { ... }   ← VERIFIER ACCEPTS

  This is why Cilium's source has NULL checks after every map lookup.
  They are not defensive programming — they are MANDATORY for the
  program to pass verification.

Constraint 3: STACK SIZE LIMIT (512 bytes)
──────────────────────────────────────────
  Total stack across the current eBPF program: 512 bytes.
  NOT across tail calls (stack resets on tail call).

  Impact: Large structures cannot be allocated on the stack.
  Cilium's structs (ct_tuple, policy_key) are carefully sized
  to fit within the budget alongside local variables.

  When you see per-cpu maps used to store temporary data:
  that is the workaround for the 512-byte stack limit.
  Per-cpu map values act as a larger "scratch space" accessible
  per CPU without locking.

Constraint 4: PACKET DATA BOUNDS CHECKING
──────────────────────────────────────────
  Every access to packet data (skb->data) must be bounds-checked.
  The verifier tracks the valid range [data, data_end].

  Before reading IP header:
    must verify: data + sizeof(struct iphdr) <= data_end

  Otherwise: REJECTED

  This is why you see bounds checks before every header access
  in bpf_lxc.c. They are not optional.

  After bpf_skb_adjust_room() (which changes skb->data):
    ALL previous bounds checks are INVALIDATED
    Must re-check bounds for all subsequent accesses
    This is why encap.h re-validates pointers after headroom adjustment

Constraint 5: NO KERNEL FUNCTION CALLS (except helpers)
─────────────────────────────────────────────────────────
  eBPF programs cannot call arbitrary kernel functions.
  They can only call BPF helper functions (listed in bpf_helpers.h):
    bpf_map_lookup_elem, bpf_map_update_elem, bpf_map_delete_elem
    bpf_redirect, bpf_redirect_map, bpf_skb_adjust_room
    bpf_perf_event_output, bpf_tail_call
    bpf_ktime_get_ns, bpf_get_prandom_u32
    bpf_skb_store_bytes, bpf_l4_csum_replace, bpf_l3_csum_replace
    ...

  Each helper has a defined prototype verified at load time.
  Passing wrong argument types → VERIFIER REJECTS.

  This is why eBPF checksum updates use bpf_l4_csum_replace()
  rather than manually computing checksums — it's the only
  verifier-approved way to update L4 checksums.

══════════════════════════════════════════════════════════════════════

VERIFIER COMPLEXITY BUDGET:
────────────────────────────

The verifier has a limit on the number of "states" it tracks
during analysis (complexity budget). Complex programs with many
conditional branches can exhaust this budget even if they are
logically correct.

Cilium manages this via:
  1. Tail calls: splits complex pipelines into smaller programs
  2. Pragma unroll: tells compiler to unroll loops
     (unrolled loops are simpler for verifier than loop constructs)
  3. Inlining: mark critical functions as __always_inline
     (avoids eBPF-to-eBPF calls which consume verifier budget)
  4. Early returns: return DROP as early as possible
     (fewer branches for verifier to explore)

When you read the Cilium source and see aggressive inlining,
unrolled loops, and early returns — that is verifier-driven
engineering, not premature optimization.
```

---

## The Complete Data Flow: All Three Files Together

This is the unified view showing how bpf_lxc.c, policy.h, encap.h, and conntrack.h interact for a single new cross-node connection.

```
COMPLETE NEW CONNECTION: Pod A → Pod C (different nodes)
ALL THREE SOURCE FILES IN ACTION
══════════════════════════════════════════════════════════════════════

  [bpf_lxc.c — egress TC hook on lxc_pod_a]
         │
         ├── Parse headers → build tuple {10.0.0.15, 10.0.1.10, 52341, 8080, TCP}
         │
         ├── [lib/nat.h] Service lookup: is 10.0.1.10 a ClusterIP?
         │   └── NO → continue with original dst
         │
         ├── [lib/conntrack.h] CT lookup: ct_map[tuple]?
         │   └── CT_NEW → no existing entry
         │
         ├── [lib/policy.h] Policy check:
         │   ├── ipcache[10.0.0.15] → src_identity = 12345
         │   ├── ipcache[10.0.1.10] → dst_identity = 12346
         │   ├── policy_map[{12346, 8080, TCP, EGRESS}]
         │   │   (egress policy of Pod A, keyed by dst identity)
         │   └── FOUND, deny=0 → ALLOW
         │
         ├── [lib/conntrack.h] CT create:
         │   ├── ct_map[tuple] = new entry, src_sec_id=12345
         │   └── ct_map[reverse_tuple] = new reverse entry
         │
         ├── [lib/eps.h] Endpoint lookup: endpoint_map[10.0.1.10]?
         │   └── NOT FOUND → Pod C is on a different node
         │
         ├── [lib/encap.h] Tunnel lookup: tunnel_map[10.0.1.10]
         │   └── VTEP = 172.18.0.3 (Node 2)
         │
         ├── [lib/encap.h] encap_and_redirect():
         │   ├── bpf_skb_adjust_room(skb, 50, ...)  add headroom
         │   ├── write VXLAN header (VNI=1)
         │   ├── write UDP header (sport=hash(tuple), dport=4789)
         │   ├── write outer IP (src=172.18.0.2, dst=172.18.0.3, DF=1)
         │   ├── write outer Ethernet (src=node1_MAC, dst=gw_MAC)
         │   └── bpf_redirect(cilium_vxlan_ifindex, 0)
         │
         └── [bpf_perf_event_output] Hubble EGRESS FORWARDED event
               {src_identity=12345, dst_identity=12346, verdict=FORWARDED}


  [WIRE: VXLAN packet travels from Node 1 to Node 2]


  [bpf_overlay.c — TC ingress hook on cilium_vxlan of Node 2]
         │
         ├── Parse outer VXLAN header → extract VNI, tunnel src IP
         │
         ├── Extract src_identity from:
         │   Option A: Geneve TLV → read identity 12345 directly
         │   Option B: ipcache[10.0.0.15] → identity 12345
         │
         ├── Strip outer headers (kernel VXLAN device does this)
         │
         └── Pass inner packet to...


  [bpf_lxc.c — TC ingress hook on lxc_pod_c of Node 2]
         │
         ├── Parse inner headers → tuple {10.0.0.15, 10.0.1.10, 52341, 8080}
         │
         ├── [lib/conntrack.h] CT lookup: ct_map[reverse_tuple]?
         │   (Node 2 has its own CT map — no entry yet for this flow)
         │   └── CT_NEW → proceed to policy check
         │
         ├── [lib/policy.h] Ingress policy check on Pod C:
         │   ├── src_identity = 12345 (from tunnel metadata)
         │   ├── dst_identity = 12346 (this endpoint's identity)
         │   ├── policy_map[{12345, 8080, TCP, INGRESS}]
         │   │   (ingress policy of Pod C, keyed by src identity)
         │   └── FOUND, deny=0 → ALLOW
         │
         ├── [lib/conntrack.h] CT create on Node 2:
         │   └── ct_map[tuple] = new entry for this node's tracking
         │
         ├── [lib/eps.h] Deliver to local endpoint:
         │   └── bpf_redirect(lxc_pod_c_ifindex, BPF_F_INGRESS)
         │
         └── [bpf_perf_event_output] Hubble INGRESS FORWARDED event
               {src_identity=12345, dst_identity=12346, verdict=FORWARDED}


  SUMMARY OF MAP OPERATIONS FOR ONE SYN PACKET:
  ┌──────────────────────────────────────────────────────────────┐
  │  Node 1:                                                     │
  │  1. service_map lookup          (1 hash lookup)             │
  │  2. ct_map lookup               (1 hash lookup)             │
  │  3. ipcache lookup × 2          (2 LPM trie lookups)        │
  │  4. policy_map lookup × 1-5     (1-5 hash lookups)          │
  │  5. ct_map create × 2           (2 hash inserts)            │
  │  6. endpoint_map lookup         (1 hash lookup)             │
  │  7. tunnel_map lookup           (1 hash lookup)             │
  │  8. perf_event_output           (1 ring buffer write)       │
  │                                                             │
  │  Node 2:                                                     │
  │  9. ipcache lookup              (1 LPM trie lookup)         │
  │  10. ct_map lookup              (1 hash lookup)             │
  │  11. policy_map lookup × 1-5    (1-5 hash lookups)          │
  │  12. ct_map create              (1 hash insert)             │
  │  13. endpoint_map lookup        (1 hash lookup)             │
  │  14. perf_event_output          (1 ring buffer write)       │
  │                                                             │
  │  TOTAL: ~15-25 map operations for one new connection SYN    │
  │         ALL are O(1) hash or LPM operations                 │
  │         SUBSEQUENT packets (CT_ESTABLISHED): ~3 map ops     │
  └──────────────────────────────────────────────────────────────┘

══════════════════════════════════════════════════════════════════════
```

---

## What Reading the Source Reveals That Diagrams Cannot

```
IMPLEMENTATION TRUTHS ONLY VISIBLE IN SOURCE
══════════════════════════════════════════════════════════════════════

TRUTH 1: Policy is enforced TWICE per cross-node packet
──────────────────────────────────────────────────────────
  Diagrams show policy at source and destination.
  The source shows EGRESS policy of src pod checked on Node 1.
  AND INGRESS policy of dst pod checked on Node 2.
  Both must ALLOW for the packet to be delivered.

  A policy gap at EITHER node means the packet is dropped.
  This is defense in depth at the packet processing level.

TRUTH 2: CT state is NOT shared between nodes
──────────────────────────────────────────────
  Each node has its own CT maps.
  Node 1 creates CT entry for the forward direction.
  Node 2 creates CT entry for the same flow (its own copy).
  If Node 2 restarts (cilium-agent reload), its CT map is cleared.
  Existing connections through Node 2 must re-establish via
  new SYN → re-trigger policy check on Node 2.

  This is why cilium-agent restarts can cause brief connection drops
  for cross-node established connections.

TRUTH 3: The random UDP source port is computed in eBPF
─────────────────────────────────────────────────────────
  The ECMP entropy source port is not random at all — it is a
  deterministic hash computed in encap.h from the inner 5-tuple.
  The "random" appearance is from the hash function's distribution.
  Same inner flow always produces the same outer src port.
  This is the guarantee that makes ECMP packet-ordering-safe.

TRUTH 4: ipcache is a LPM trie, not a hash map
────────────────────────────────────────────────
  Most maps in Cilium are BPF_MAP_TYPE_HASH.
  The ipcache is BPF_MAP_TYPE_LPM_TRIE.
  This enables CIDR-based identity matching (e.g., 10.0.0.0/8 → identity).
  The performance characteristic is O(log n) not O(1).
  For most deployments (< 100K entries), this is not a bottleneck.
  For extremely large clusters: ipcache lookup latency is measurable.

TRUTH 5: Checksum offload interaction with encapsulation
──────────────────────────────────────────────────────────
  Modern NICs support checksum offload: the NIC computes TCP/IP
  checksums in hardware, not the CPU.

  When Cilium modifies packet headers (DNAT, SNAT, encapsulation),
  it must interact with the NIC's offload state correctly:
  - If checksum is offloaded: Cilium updates pseudo-header checksums
    and marks the skb with the right offload flags
  - If checksum is already computed: Cilium must recompute it
    (using bpf_l4_csum_replace helper)

  Getting this wrong produces: packets with wrong checksums,
  silently dropped by the receiver's NIC.
  This is a real source of bugs in custom eBPF network programs.

TRUTH 6: bpf_redirect vs bpf_redirect_map
───────────────────────────────────────────
  bpf_redirect(ifindex, flags):
    Redirect to a specific interface by ifindex.
    Simple but requires knowing the ifindex at eBPF load time
    (or looking it up from a map at runtime).

  bpf_redirect_map(&devmap, key, flags):
    Redirect via a DEVMAP — a map of ifindex values.
    Allows the control plane to update redirect targets without
    reloading eBPF programs.
    Used for XDP-level forwarding (higher performance).

  Cilium uses bpf_redirect for lxc-to-lxc local redirects
  and bpf_redirect for cilium_vxlan (encapsulated cross-node).

TRUTH 7: The "seen_non_syn" CT field prevents RST injection
─────────────────────────────────────────────────────────────
  The CT entry has a flag: seen_non_syn.
  If a TCP packet with ACK/data arrives for a CT_NEW connection
  (before a SYN was seen), Cilium drops it.

  This prevents TCP RST injection attacks:
  Attacker sends: TCP RST to a port where a connection exists
  Without this check: CT might accept the RST as RELATED
  With seen_non_syn: RST for unknown connection is dropped silently

══════════════════════════════════════════════════════════════════════
```

---

## The Security Audit View: What to Look For When Reading the Source

```
SECURITY AUDIT CHECKLIST FOR bpf_lxc.c / policy.h / encap.h
══════════════════════════════════════════════════════════════════════

QUESTION 1: Can policy be bypassed via CT fast path?
──────────────────────────────────────────────────────
  CT fast path skips policy_map lookup for ESTABLISHED connections.
  Is this safe?

  Analysis:
  - The initial SYN goes through full policy check
  - CT entry is created ONLY if policy ALLOWS
  - Subsequent packets use CT fast path
  - If policy changes (NetworkPolicy updated), CT entries are
    NOT immediately invalidated
  - cilium-agent monitors policy changes and flushes affected
    CT entries when NetworkPolicy is tightened
  - Window: between policy tightening and CT flush, existing
    connections continue flowing
  - This is a deliberate design choice: dropping established
    connections on policy change would break running applications

  Risk: A connection established before a policy was tightened
  continues flowing briefly after the policy change.
  Mitigation: CT lifetime is bounded (6 hours for TCP);
  for immediate enforcement, cilium-agent flushes CT on policy change.


QUESTION 2: Can an attacker spoof a source identity via VXLAN?
───────────────────────────────────────────────────────────────
  VXLAN provides NO authentication. Any host that can send
  UDP to port 4789 can inject VXLAN frames with any inner src IP
  and claim any identity.

  Cilium's mitigation:
  - The VXLAN tunnel interface (cilium_vxlan) should only be
    reachable from OTHER CILIUM NODES
  - Underlay security groups / firewall rules should restrict
    UDP/4789 to the cluster node IP range
  - If an attacker can reach UDP/4789 on any node, they can
    inject packets with arbitrary src identities
  - This is WHY WireGuard/IPsec tunnel encryption is important:
    encrypted tunnels prevent injection even if UDP/4789 is reachable

  Check in source:
  - Does bpf_overlay.c validate the outer src IP of incoming VXLAN?
  - Is there a whitelist of valid VTEP IPs in tunnel_map?
  - If the outer src IP is NOT in tunnel_map, the packet should
    be treated with reserved:world identity (untrusted)


QUESTION 3: What happens if ipcache is stale?
──────────────────────────────────────────────
  Pod P gets IP 10.0.0.15, is deleted, new Pod Q gets same IP.
  If Node 2's ipcache still maps 10.0.0.15 → Pod P's identity,
  Pod Q's packets will be attributed to Pod P's identity.

  This is an IP reuse race condition.

  Cilium's mitigation:
  - Pod deletion triggers ipcache update (IP → identity mapping removed)
  - New pod creation triggers ipcache update (new IP → new identity)
  - The update propagates via Kubernetes API watch (sub-second)
  - There is a brief window (~1s) where the old mapping could be stale
  - VXLAN mode with Geneve TLV identity embedding avoids this:
    identity is carried IN the packet, not looked up at destination


QUESTION 4: Is the policy_map itself writable by a pod?
──────────────────────────────────────────────────────────
  eBPF maps are kernel objects. A pod cannot write to them unless
  it has a file descriptor pointing to the map AND write access.

  Cilium's policy maps are:
  - Created by cilium-agent (running as privileged DaemonSet)
  - Pinned at /sys/fs/bpf/tc/globals/ (on BPF filesystem)
  - Accessible only to root (or cilium-agent's UID)
  - A pod would need to escape its namespace AND be root
    to write to the host's BPF filesystem

  Risk: Privileged pods (hostPID, hostNetwork, CAP_BPF) could
  potentially modify eBPF maps. This is why admission control
  (OPA Gatekeeper, Kyverno) should restrict these capabilities.


QUESTION 5: What if the CT map is exhausted?
──────────────────────────────────────────────
  CT map has a fixed max_entries (default: 512K on 64-bit).
  When full: bpf_map_update_elem returns -E2BIG.
  cilium-agent handles this by:
  Option A: LRU_HASH map type → auto-evict LRU entries
  Option B: Return CT_NEW even when update fails → re-check policy
            (degraded mode: every packet does full policy check)

  Security implication: CT exhaustion (from high connection rate
  or deliberate DDoS) causes all connections to do full policy
  checks → CPU spikes → potential service degradation.
  This is a DoS vector targeting the eBPF data plane directly.

══════════════════════════════════════════════════════════════════════
```

---

## The Architecture at Maximum Zoom-Out

After reading the source, the complete Cilium data plane architecture resolves into this unified view:

```
CILIUM DATA PLANE: COMPLETE ARCHITECTURE
══════════════════════════════════════════════════════════════════════

CONTROL PLANE (userspace)          DATA PLANE (eBPF in kernel)
══════════════════════════         ════════════════════════════

Kubernetes API server
      │ watch
      ▼
cilium-agent
  ├── pod create/delete
  │   └─── update ipcache_map ────────────────────► ipcache_map
  │         (IP → identity)                         (LPM trie)
  │
  ├── NetworkPolicy change
  │   └─── update policy_map ────────────────────► policy_map
  │         (per endpoint)                          (hash, per-ep)
  │
  ├── Service endpoint change
  │   └─── update service_map ───────────────────► service_map
  │         (ClusterIP → pod IPs)                  (hash)
  │
  ├── Node join/leave
  │   └─── update tunnel_map ────────────────────► tunnel_map
  │         (pod CIDR → VTEP)                       (hash)
  │
  ├── eBPF program lifecycle
  │   └─── load/attach bpf_lxc.c ──────────────► TC hook on lxc
  │         to each new pod's veth               (attached at pod create)
  │
  └── CT garbage collection
      └─── scan + delete ct_map ─────────────────► ct_map
            expired entries                        (hash)


                    PACKET PROCESSING (per packet, kernel speed)
                    ════════════════════════════════════════════

                    lxc TC hook (bpf_lxc.c)
                         │
                    ┌────▼────┐
                    │ service │ service_map O(1)
                    │  DNAT   │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │   CT    │ ct_map O(1)
                    │ lookup  │
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │ policy  │ ipcache O(log n) + policy_map O(1)
                    │  check  │ (only for CT_NEW)
                    └────┬────┘
                         │
                    ┌────▼────┐
                    │  fwd    │ endpoint_map O(1)
                    │decision │ tunnel_map O(1)
                    └────┬────┘
                    ┌────┴─────────────────────┐
                    │                          │
               ┌────▼────┐              ┌──────▼──────┐
               │  local  │              │    encap    │
               │redirect │              │   (encap.h) │
               │bpf_redir│              │   VXLAN     │
               └─────────┘              └─────────────┘
                    │                          │
               pod delivers               cilium_vxlan
                                          → eth0 → wire

══════════════════════════════════════════════════════════════════════
```

---

## Next 3 Steps

**Step 3A:** Navigate to the actual Cilium source repository at `github.com/cilium/cilium` and read `bpf/bpf_lxc.c` starting from the `__section("classifier/from-container")` annotation — this is the TC egress entry point. Follow every function call into its respective header file. Draw your own version of the egress pipeline diagram above as you read, correcting it where the actual source diverges from this guide. The act of reconciling the diagram with the code is where the deep understanding forms.

**Step 3B:** Read the Cilium eBPF map definitions in `bpf/lib/maps.h` alongside the Linux kernel's BPF map type documentation (`Documentation/bpf/maps.rst` in the Linux kernel tree). For each map Cilium uses, identify its type, understand why that type was chosen over alternatives, and calculate the memory footprint at maximum entries. This is essential for capacity planning — a Cilium deployment at 100K pods uses several GB of eBPF map memory, and understanding the sizing equations requires knowing the struct sizes and map entry counts.

**Step 3C:** Study `cilium/pkg/datapath/loader/loader.go` — the Go code in cilium-agent that compiles, verifies, and loads the eBPF programs. This is the bridge between the control plane and data plane. Understanding how the agent parameterizes the eBPF programs (via `#define` constants injected at compile time), manages program versioning during rolling updates, and handles the transition from old to new eBPF programs without dropping connections — this is the operational engineering that makes Cilium production-grade, and it is entirely invisible from the eBPF source alone.