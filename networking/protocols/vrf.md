# Virtual Routing and Forwarding (VRF): A Comprehensive Reference

> **Scope**: This document covers VRF from first principles through production
> architecture — from the Linux kernel implementation to MPLS L3VPN control
> plane, BGP VPNv4 signaling, route leaking, security implications, and
> cloud-native relevance. Every wire format is shown with bit-exact ASCII
> diagrams. Every concept is anchored in the actual protocol specification.

---

## Table of Contents

1. [The Core Problem VRF Solves](#1-the-core-problem-vrf-solves)
2. [Mental Model: What a VRF Actually Is](#2-mental-model-what-a-vrf-actually-is)
3. [VRF Taxonomy: Lite vs. MPLS L3VPN vs. Linux](#3-vrf-taxonomy-lite-vs-mpls-l3vpn-vs-linux)
4. [The Routing Table Internals: RIB and FIB](#4-the-routing-table-internals-rib-and-fib)
5. [Linux Kernel VRF Implementation](#5-linux-kernel-vrf-implementation)
6. [VRF-Lite: VRF Without MPLS](#6-vrf-lite-vrf-without-mpls)
7. [MPLS Fundamentals (prerequisite for L3VPN)](#7-mpls-fundamentals-prerequisite-for-l3vpn)
8. [MPLS L3VPN Architecture (RFC 4364)](#8-mpls-l3vpn-architecture-rfc-4364)
9. [Route Distinguisher (RD) — Wire Format and Semantics](#9-route-distinguisher-rd--wire-format-and-semantics)
10. [Route Target (RT) — BGP Extended Community Wire Format](#10-route-target-rt--bgp-extended-community-wire-format)
11. [MP-BGP for VPNv4: RFC 4760 + RFC 4364](#11-mp-bgp-for-vpnv4-rfc-4760--rfc-4364)
12. [PE-CE Routing: Protocol Options and Their Tradeoffs](#12-pe-ce-routing-protocol-options-and-their-tradeoffs)
13. [VRF Route Leaking](#13-vrf-route-leaking)
14. [VRF and OSPF: Per-VRF Instances](#14-vrf-and-ospf-per-vrf-instances)
15. [VRF and BGP: Address Family Architecture](#15-vrf-and-bgp-address-family-architecture)
16. [Data Plane: Packet Walk Through an MPLS L3VPN](#16-data-plane-packet-walk-through-an-mpls-l3vpn)
17. [VRF in Linux: iproute2, netns, and the Kernel L3 Master Device](#17-vrf-in-linux-iproute2-netns-and-the-kernel-l3-master-device)
18. [VRF vs. Network Namespaces: When to Use Which](#18-vrf-vs-network-namespaces-when-to-use-which)
19. [VRF in Kubernetes and Cloud-Native Environments](#19-vrf-in-kubernetes-and-cloud-native-environments)
20. [VRF Security Architecture](#20-vrf-security-architecture)
21. [Failure Modes and Misconfigurations](#21-failure-modes-and-misconfigurations)
22. [Production Operational Patterns](#22-production-operational-patterns)
23. [Connection Map](#23-connection-map)

---

## 1. The Core Problem VRF Solves

### The Overlapping Address Space Problem

In classical IP routing, a router has a single global routing table. Every
interface, every prefix, every next-hop lives in that one table. This creates
an absolute constraint: **no two routes to different destinations can share the
same prefix within the same table**. The table is a function: prefix → action.

This is a hard problem in multi-tenant environments. Consider:

- **ISP providing L3VPN services**: Customer A uses 10.0.0.0/8 for their
  internal network. Customer B also uses 10.0.0.0/8 for theirs. Both are
  connected to the same PE (Provider Edge) router. Without VRF, these routes
  collide. The router cannot distinguish which 10.0.0.0/8 belongs to whom.

- **Enterprise with overlapping branch offices**: Acquired company uses
  192.168.0.0/16. So does the acquiring company. Both need to be routed
  independently until renumbering is complete (which in practice means forever).

- **Security isolation requirement**: Management plane traffic (OOB management,
  BGP sessions to route reflectors, DNS) must be completely isolated from
  customer data plane traffic. A compromised customer segment must not be
  able to reach the management network even if routing is misconfigured.

- **Regulatory isolation**: PCI-DSS scope isolation, HIPAA segment isolation —
  regulated traffic must traverse a separate routing domain entirely.

### What Breaks Without VRF

Without VRF:

1. Overlapping prefixes cause route table corruption — the last route installed
   wins, silently dropping or misdirecting traffic for the other tenant.
2. Route policy is applied globally — you cannot have different default routes,
   different next-hops, or different metric schemes per tenant.
3. A single routing daemon failure (e.g., BGP process crash) takes down ALL
   tenants simultaneously instead of being contained.
4. Traceroute and path analysis cross tenant boundaries — information leakage.
5. You cannot provide different SLAs (different QoS, different MTU policies)
   per routing domain without complex ACL hacks.

### The Invariant VRF Enforces

**A VRF is a separate routing domain with its own independent RIB (Routing
Information Base) and FIB (Forwarding Information Base), associated with
a set of interfaces, such that a packet arriving on a VRF-bound interface
is exclusively looked up in that VRF's table and forwarded only to
next-hops reachable via that same VRF — unless an explicit leak or
interconnect is configured.**

The invariant: **routing table membership is determined at ingress by
interface binding, not by packet content**.

---

## 2. Mental Model: What a VRF Actually Is

### The Namespace Analogy

**Analogy**: A VRF is to a routing table what a process namespace is to a
Linux process's view of the PID space. Each namespace thinks it owns the
entire address space. The kernel tracks which namespace a resource belongs
to and dispatches accordingly.

**This analogy breaks at**: Unlike PID namespaces, VRF "namespaces" can
have explicit, configured interconnects (route leaking). You can surgically
punch a hole between two VRFs in a way you cannot do with process namespaces
without compromising isolation.

### The Deeper Model: Three Separate Planes

To understand VRF correctly, you must understand it operates across three
distinct planes simultaneously:

```
┌─────────────────────────────────────────────────────────────────┐
│                     MANAGEMENT PLANE                             │
│  VRF definition, interface binding, policy configuration        │
│  (CLI, NETCONF, gRPC, Linux rtnetlink)                          │
└─────────────────────────┬───────────────────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────────────────┐
│                      CONTROL PLANE                               │
│  Per-VRF routing protocol instances (BGP, OSPF, IS-IS, Static) │
│  Each VRF has its own RIB — topology and reachability database  │
│  Route redistribution and import/export policies per VRF        │
└─────────────────────────┬───────────────────────────────────────┘
                          │ RIB → FIB download
┌─────────────────────────▼───────────────────────────────────────┐
│                       DATA PLANE                                 │
│  Per-VRF FIB — what hardware/kernel actually uses to forward    │
│  In MPLS L3VPN: label lookup + label push at ingress PE         │
│  In VRF-Lite: straight L3 lookup in per-VRF table              │
│  In Linux: separate routing table per VRF (RT table ID)         │
└─────────────────────────────────────────────────────────────────┘
```

### VRF as a Function

Formally:

```
vrf_lookup(interface, packet) → routing_table_id

routing_table_id → FIB_entry → { next_hop, egress_interface, labels... }
```

The key insight: **the VRF selection happens at ingress, based on which
interface the packet arrived on, before any IP lookup occurs**. The IP
destination address is only consulted after the VRF context is established.

This is why:
- Two packets to 10.0.0.1, arriving on two different VRF-bound interfaces,
  can be forwarded to two completely different destinations.
- A packet cannot "escape" its VRF by crafting a special destination address
  (absent explicit leaking).

---

## 3. VRF Taxonomy: Lite vs. MPLS L3VPN vs. Linux

Understanding which VRF variant you are working with changes everything
about how routes are signaled, how packets are forwarded, and what
failure modes apply.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VRF Variants                                  │
├─────────────────┬────────────────────────┬──────────────────────────┤
│   VRF-Lite      │   MPLS L3VPN (RFC4364) │   Linux Kernel VRF       │
│                 │                        │                          │
│ No MPLS         │ MPLS label switching   │ RT table per VRF         │
│ No RD/RT        │ RD + RT + MP-BGP       │ L3 master device         │
│ Local router    │ Distributed PE/P/CE    │ Separate FIB per table   │
│ only            │ architecture           │ ip rules for dispatch    │
│                 │                        │                          │
│ Use: enterprise │ Use: ISP L3VPN,        │ Use: Linux router/FW,    │
│ segmentation,   │ managed MPLS WAN,      │ Kubernetes node,         │
│ OOB management  │ carrier ethernet       │ VNF/container routing    │
└─────────────────┴────────────────────────┴──────────────────────────┘
```

| Property | VRF-Lite | MPLS L3VPN | Linux VRF |
|---|---|---|---|
| Overlapping prefixes | ✓ | ✓ | ✓ |
| Needs MPLS in core | ✗ | ✓ | ✗ |
| Scalability | Per-hop config | Scales via BGP RR | Per-host config |
| Route signal | Static/IGP/eBGP per link | MP-BGP VPNv4 | rtnetlink |
| CE awareness | Explicit per-PE | Only at PE | Interface binding |
| Kernel representation | N/A (IOS/NX-OS) | N/A (IOS/NX-OS) | RT table ID (u32) |

---

## 4. The Routing Table Internals: RIB and FIB

This distinction is critical and often conflated. VRF multiplies both.

### RIB: Routing Information Base

The RIB is the **routing protocol's view of the network**. It contains:

- All routes learned from all sources (BGP, OSPF, static, connected)
- Route attributes: metrics, administrative distance, next-hops, communities
- Multiple routes to the same prefix (best path selection happens here)
- Routes that may NOT be installed in the FIB (if a better AD route exists)

The RIB lives in the routing daemon's memory space (FRR, BIRD, GoBGP, IOS
routing process). It is the database of routing knowledge.

```
RIB for VRF "CUSTOMER-A":
┌─────────────────┬─────────────┬────────┬──────────┬───────────┐
│ Prefix          │ Next-hop    │ Proto  │ AD/Metric│ Status    │
├─────────────────┼─────────────┼────────┼──────────┼───────────┤
│ 10.0.0.0/8      │ 192.0.2.1   │ BGP    │ 20/100   │ Best ✓    │
│ 10.0.0.0/8      │ 192.0.2.2   │ OSPF   │ 110/20   │ Alt       │
│ 10.1.0.0/16     │ 192.0.2.3   │ Static │ 1/0      │ Best ✓    │
│ 0.0.0.0/0       │ 203.0.113.1 │ BGP    │ 20/0     │ Best ✓    │
└─────────────────┴─────────────┴────────┴──────────┴───────────┘
```

### FIB: Forwarding Information Base

The FIB is the **data plane's lookup table**. It contains:

- Only the best paths (already selected by the RIB)
- Resolved next-hops (recursive resolution completed — actual MAC addresses
  or MPLS labels, not symbolic next-hops)
- Optimized for fast lookup (radix trie, LPM hardware tables, Linux fib_trie)
- Lives in the kernel (Linux: `ip route show table <id>`) or hardware ASIC

```
FIB for VRF "CUSTOMER-A" (Linux RT table 100):
┌─────────────────┬──────────────────────────┬───────────┐
│ Prefix          │ Resolved Action           │ Interface │
├─────────────────┼──────────────────────────┼───────────┤
│ 10.0.0.0/8      │ via 192.0.2.1 dev eth1   │ eth1      │
│ 10.1.0.0/16     │ via 192.0.2.3 dev eth2   │ eth2      │
│ 0.0.0.0/0       │ via 203.0.113.1 dev eth0 │ eth0      │
└─────────────────┴──────────────────────────┴───────────┘
```

### The Download Path

```
Routing Protocol (BGP/OSPF)
        │
        │  announces prefix with attributes
        ▼
      RIB
        │
        │  best-path selection (AD, metric, BGP path attributes)
        │  recursive next-hop resolution
        ▼
      FIB (kernel / hardware)
        │
        │  packet arrives on VRF-bound interface
        │  LPM lookup → action
        ▼
    Forward / Drop / MPLS push
```

In a VRF context, **both the RIB and the FIB are per-VRF**. The routing
daemon maintains N RIBs for N VRFs. The kernel (or ASIC) maintains N FIBs.

---

## 5. Linux Kernel VRF Implementation

Linux implements VRF using a **L3 master device** — a virtual network device
that acts as the "owner" of one or more enslaved interfaces and maintains
a dedicated routing table.

### Kernel Data Structures

```
struct net_device (L3 master device: vrf0)
    │
    ├── l3mdev_ops → vrf_l3mdev_ops
    │       ├── l3mdev_fib_table()  → returns RT table ID (e.g., 100)
    │       ├── l3mdev_l3_rcv()     → called on ingress
    │       └── l3mdev_l3_out()     → called on egress
    │
    └── enslaved interfaces: eth1, eth2, eth3
            each has: dev->master = vrf0
```

### IP Rule Dispatch (ip rules / Policy-Based Routing)

Linux VRF uses the **policy routing** subsystem to dispatch packets to the
correct VRF routing table. When a packet arrives on a VRF-enslaved interface,
the kernel:

1. Checks `dev->l3mdev_ops` — is this interface enslaved to an L3 master?
2. If yes, calls `l3mdev_fib_table()` to get the routing table ID.
3. Performs LPM lookup in that table instead of the main table (table 253).

```
ip rule show (on a Linux VRF router):

0:      from all lookup local         (table 255 — loopback/local)
1000:   from all lookup [l3mdev-table]  (VRF: dynamic rule per VRF)
32766:  from all lookup main           (table 253 — global)
32767:  from all lookup default        (table 254 — empty)
```

The `[l3mdev-table]` rule at priority 1000 is inserted by the kernel when
a VRF device is created. It says: "if the packet's ingress device is enslaved
to an L3 master, look up its table before consulting main."

### Linux Routing Table Assignment

```
# Create VRF device with RT table 100
ip link add vrf-red type vrf table 100

# Enslave interface to VRF
ip link set eth1 master vrf-red
ip link set eth2 master vrf-red

# VRF device brought up
ip link set vrf-red up

# Routes in the VRF table
ip route add 10.0.0.0/8 via 192.168.1.1 vrf vrf-red
# Equivalent: ip route add 10.0.0.0/8 via 192.168.1.1 table 100

# Show VRF-specific routes
ip route show vrf vrf-red
# Equivalent: ip route show table 100
```

### Socket Binding to VRF

A process can bind a socket to a specific VRF, meaning its traffic is
looked up in that VRF's routing table:

```c
// Bind a socket to VRF "vrf-red" (index 5)
int vrf_idx = if_nametoindex("vrf-red");
setsockopt(sockfd, SOL_SOCKET, SO_BINDTODEVICE, "vrf-red", strlen("vrf-red")+1);
// Or equivalently:
setsockopt(sockfd, SOL_SOCKET, SO_BINDTOIFINDEX, &vrf_idx, sizeof(vrf_idx));
```

This is critical for routing daemons (FRR) to listen only on VRF-bound
interfaces and inject routes only into the correct VRF table.

---

## 6. VRF-Lite: VRF Without MPLS

VRF-Lite is the simplest form: a single router runs multiple independent
routing tables, each bound to a set of interfaces. There is no MPLS,
no Route Distinguisher, no BGP VPNv4 — just separate per-VRF routing
protocol instances and per-VRF FIBs.

### Topology

```
                    ┌─────────────────────┐
                    │    PE Router        │
   CE-A ──[eth0]──►│ VRF-A  │  VRF-B    │◄──[eth2]── CE-B
   10.0.0.0/8      │ table  │  table    │   172.16.0.0/12
                   │  100   │   200     │
                    └────────┴───────────┘
                    No MPLS. Each VRF has its own:
                    - Routing table
                    - BGP/OSPF instance
                    - Route policies
```

### Use Cases

1. **Out-of-Band Management VRF**: Management traffic (SSH, SNMP, syslog,
   gNMI) travels in a dedicated VRF that has no data plane routes. Even if
   the data plane is compromised, the management plane remains reachable via
   its own interfaces and routing table.

2. **Regulatory Isolation**: PCI-DSS cardholder data environment in VRF-PCI,
   corporate network in VRF-CORP. Both use 10.0.0.0/8 internally. No cross-
   VRF routing unless explicitly configured at a firewall.

3. **Multi-tenant CPE**: Small branch router serves multiple departments,
   each in its own VRF, sharing uplinks via subinterfaces.

### VRF-Lite Limitations

- **No automatic propagation**: Each PE must be configured identically.
  A route added to VRF-A on PE1 must be manually (or via per-VRF BGP
  session) redistributed to VRF-A on PE2. There is no control plane
  that propagates VRF membership across the network.
- **Sub-interface explosion**: In a large network, each VRF needs dedicated
  sub-interfaces on transit links, leading to O(VRFs × transit-links) config.
- **No MPLS efficiency**: Traffic between two CEs in the same VRF but on
  different PEs must traverse the provider core as plain IP, requiring the
  provider core to carry customer routes in its routing table.

---

## 7. MPLS Fundamentals (prerequisite for L3VPN)

MPLS (Multiprotocol Label Switching) is the forwarding mechanism that makes
scalable L3VPN possible. You must understand it to understand VRF in the
service provider context.

### The Label: Wire Format

An MPLS label is a 32-bit value prepended to a packet between the L2 header
and the L3 (IP) header.

```
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Label (20 bits)                |Exp|S|   TTL   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Label (20 bits): The label value. Range 0–1048575 (2^20 - 1).
                 Values 0–15 are reserved (implicit null=3, etc.)

Exp (3 bits):    Traffic Class / QoS marking (was "experimental")
                 Maps to DSCP in IP header on push/pop

S (1 bit):       Bottom of Stack. 1 = this is the last label in the stack.
                 0 = more labels follow (label stack, multiple levels).

TTL (8 bits):    Time To Live. Copied from IP TTL on label push.
                 Decremented at each MPLS hop. Pipe/uniform mode options.
```

### Label Stack for L3VPN

In MPLS L3VPN, packets carry a **two-label stack**:

```
┌──────────────────────────────────────┐
│  Ethernet Header (L2)                │
├──────────────────────────────────────┤
│  Outer Label (Transport/LSP label)   │  ← LDP/RSVP-TE label
│  S=0 (not bottom of stack)           │    Swapped at each P router
├──────────────────────────────────────┤
│  Inner Label (VPN label)             │  ← Assigned by egress PE
│  S=1 (bottom of stack)               │    Identifies VRF at egress PE
├──────────────────────────────────────┤
│  IP Header + Payload                 │  ← Customer packet, unchanged
└──────────────────────────────────────┘
```

The **outer label** routes the packet through the MPLS core (P routers).
P routers only look at this label — they never see the customer IP.

The **inner (VPN) label** tells the **egress PE** which VRF to look up the
customer IP in after popping the label stack. This is the mechanism that
connects MPLS forwarding to VRF lookup.

### PHP: Penultimate Hop Popping

The P router immediately before the egress PE (the penultimate hop) pops
the outer label before forwarding to the PE. This spares the PE a label
lookup — it receives a packet with only the VPN label (or bare IP if
PHP is used for VPN label too).

```
CE-A → ingress-PE → P1 → P2 → (PHP pop outer) → egress-PE → CE-B
        push(outer+vpn)  swap   swap    pop-outer → see VPN label → VRF lookup
```

### Label Distribution

Labels are distributed via:

- **LDP (Label Distribution Protocol)**: Distributes labels for all IGP
  prefixes. Simple, hop-by-hop. One label per IGP prefix per LSR.
- **RSVP-TE**: Traffic-engineered LSPs with explicit paths and bandwidth
  reservation. More complex but enables traffic engineering.
- **BGP labeled unicast (RFC 8277)**: BGP carries labels alongside prefixes
  in the labeled unicast address family. Used for inter-AS MPLS.
- **Segment Routing (SR-MPLS, RFC 8402)**: Labels are derived from node/
  adjacency SIDs. No per-flow state in the core. The future of MPLS TE.

For L3VPN, the **VPN (inner) label** is distributed via **MP-BGP** — not
LDP. This is the central mechanism described in Section 11.

---

## 8. MPLS L3VPN Architecture (RFC 4364)

RFC 4364 (formerly RFC 2547bis) defines the standard MPLS L3VPN architecture.
Understanding its components is essential.

### Node Roles

```
        Customer Site A              Provider Core            Customer Site B
   ┌──────────────────────┐    ┌──────────────────────┐    ┌──────────────────┐
   │  CE-A                │    │  PE1  P1  P2  PE2    │    │            CE-B  │
   │  (Customer Edge)     │    │  (Provider Network)   │    │  (Customer Edge) │
   │  10.0.0.0/8          │◄──►│                       │◄──►│  10.0.0.0/8      │
   └──────────────────────┘    └──────────────────────┘    └──────────────────┘

CE  = Customer Edge router. Owned by customer. No VRF awareness.
      Speaks standard routing protocol (BGP, OSPF, static) to PE.

PE  = Provider Edge router. Owns VRF instances.
      Terminates CE routing sessions per-VRF.
      Runs MP-BGP VPNv4 with other PEs (via Route Reflector).
      Pushes/pops MPLS label stack.

P   = Provider core router. Pure MPLS label switching.
      Never sees customer routes. Only knows LSPs (LDP/RSVP-TE labels).
      Massively scalable — O(core-prefixes) routing table only.

RR  = Route Reflector. BGP route reflector in the provider core.
      Reflects VPNv4 routes between PEs. Central control plane.
```

### Why P Routers Don't Need VRF Routes

This is the key scalability insight of RFC 4364:

- Without MPLS: every P router would need to carry ALL customer routes from
  ALL VRFs from ALL PEs. At ISP scale, this is millions of routes per router.
- With MPLS: P routers only carry **transport labels** for the LSP to each PE.
  O(PEs) entries, not O(customer-prefixes × VRFs × PEs).
- Customer routes are **only carried in MP-BGP between PEs** (and RRs).
  P routers are completely invisible to this exchange.

This gives the architecture its name: **ships in the night**. BGP (carrying
VPNv4 customer routes) and MPLS (carrying transport labels) run independently
on the PE, and P routers only see MPLS.

### The Route Reflector in L3VPN

```
          ┌─────────────────────────────────────┐
          │           Route Reflector (RR)      │
          │  ibgp cluster, VPNv4 address family │
          └──────┬────────────┬─────────────────┘
                 │            │   ibgp VPNv4 sessions
           ┌─────┘            └──────┐
           ▼                        ▼
         PE1                       PE2
    VRF-CUST-A                VRF-CUST-A
    VRF-CUST-B                VRF-CUST-B
    VRF-MGMT                  VRF-MGMT
```

PEs do NOT form full ibgp mesh with each other. They form ibgp sessions only
to RRs. The RR reflects VPNv4 NLRIs (with RT communities) between PEs,
filtered by RT import policy.

---

## 9. Route Distinguisher (RD) — Wire Format and Semantics

### What the RD Is

A Route Distinguisher (RD) is an **8-byte value prepended to an IPv4 prefix
to make it globally unique in the BGP VPNv4 address family**.

Without RD, two VRFs advertising 10.0.0.0/8 to the same BGP RR would
produce a collision — BGP would treat them as the same prefix and apply
best-path selection, silently discarding one. The RD prevents this by
making the prefix unique: `RD:prefix` is a globally unique tuple.

**Critical point**: **The RD does NOT control route import/export policy**.
That is the job of the Route Target (RT). The RD purely disambiguates
overlapping prefixes in the BGP table. Two VRFs CAN share the same RD
(though this is a misuse). A VRF's RD is administratively assigned.

### RD Wire Format (RFC 4364, Section 4.2)

The RD is 8 bytes (64 bits) with a 2-byte Type field followed by a
6-byte Value field. Three types are defined:

```
Type 0 (AS:nn — 2-byte ASN : 4-byte administrator number):
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Type = 0x0000 (2 bytes)    |   2-byte ASN (e.g., 65000)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|              4-byte Administrator Number (0-4294967295)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
Example: 65000:100  →  0x0000 | 0xFDE8 | 0x00000064

Type 1 (IP:nn — 4-byte IP address : 2-byte administrator number):
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Type = 0x0001 (2 bytes)    |   4-byte IP Address           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| (IP addr cont)                | 2-byte Admin Number           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
Example: 10.0.0.1:100  →  0x0001 | 0x0A000001 | 0x0064

Type 2 (4-byte ASN : 2-byte administrator number — for 4-byte ASNs):
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Type = 0x0002 (2 bytes)    |   4-byte ASN (4-byte capable) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| (ASN cont)                    |  2-byte Admin Number          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
Example: 131072:100  →  0x0002 | 0x00020000 | 0x0064
```

### RD + Prefix = VPNv4 NLRI

When a PE advertises a VRF route into MP-BGP, it prepends the RD to form
a **VPNv4 prefix** (also called a VPN-IPv4 address):

```
VPNv4 Prefix = RD (8 bytes) + IPv4 Prefix (variable length)

Example: RD 65000:100, prefix 10.0.0.0/8:
┌────────────────────────────────────────┬────────────────────┐
│  RD: 65000:100                         │  Prefix: 10.0.0.0  │
│  8 bytes                               │  Length: 8 bits     │
│  0x0000 FDE8 00000064                  │  (prefix-len = 8+64)│
└────────────────────────────────────────┴────────────────────┘
Total prefix length in BGP NLRI: 64 + 8 = 72 bits
```

The RD becomes part of the BGP best-path calculation key. Two routes with
the same IP prefix but different RDs are treated as different BGP prefixes
entirely — no best-path comparison between them.

### RD Design Conventions

| Pattern | Format | When to Use |
|---|---|---|
| Per-PE, per-VRF unique | `PE-Loopback:VRF-ID` | Best — guarantees uniqueness, enables optimal routing |
| Per-VRF shared across PEs | `ASN:VRF-ID` | Simpler config, but loses multi-path optimization |
| Customer-specific | `Customer-ASN:anything` | When customer provides their own ASN |

**The per-PE unique RD** (Type 1: `PE-loopback-IP:VRF-ID`) is the production
best practice because it ensures BGP never applies best-path selection
between two PEs' routes for the same prefix — both paths survive in the BGP
table, enabling optimal route selection based on RT import and BGP path
attributes independently.

---

## 10. Route Target (RT) — BGP Extended Community Wire Format

### What the RT Is

A Route Target is a **BGP Extended Community** that controls which VRFs
**import** and **export** routes. It is the policy mechanism for VRF.

- **Export RT**: Attached by the PE to a route when it is exported from a VRF
  into MP-BGP. "This route came from VRF with this identity."
- **Import RT**: Configured on a VRF. "Import into this VRF any BGP route
  that carries this RT value."

The import/export RT mechanism is the foundation of all VPN topology design:
hub-and-spoke, full-mesh, extranet, and inter-AS VPN.

### RT Wire Format — BGP Extended Community (RFC 4360 + RFC 4364)

BGP Extended Communities are 8 bytes. The first 2 bytes encode the type,
remaining 6 bytes encode the value.

```
Route Target Extended Community (Type 0x00 or 0x02):

0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Type (0x00)  | Sub-Type(0x02)| 2-byte Global Admin (ASN)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           4-byte Local Administrator Number                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Type byte breakdown:
  Bit 7 (IANA):   0 = IANA assigned, 1 = non-IANA
  Bit 6 (Transitive): 0 = transitive, 1 = non-transitive
  Bits 5-0: Type value
    0x00 = 2-octet ASN specific (Global Admin = 2-byte ASN)
    0x01 = IPv4 address specific (Global Admin = 4-byte IP)
    0x02 = 4-octet ASN specific (Global Admin = 4-byte ASN)

Sub-Type for Route Target:
  0x02 = Route Target

Example: RT 65000:100 (2-byte ASN type):
  Byte 0: 0x00 (Type: 2-octet ASN, transitive)
  Byte 1: 0x02 (Sub-type: Route Target)
  Bytes 2-3: 0xFDE8 (ASN 65000 in big-endian)
  Bytes 4-7: 0x00000064 (Local Admin: 100)
  Full: 00:02:FD:E8:00:00:00:64

Route Origin Extended Community (Sub-Type 0x03):
  Same format, Sub-Type byte = 0x03
  Marks the originating VPN — informational, rarely used in policy
```

### RT Import/Export Policy Architecture

```
VRF Design: Hub-and-Spoke Topology

SPOKE-VRF (Customer Branch):
  Export RT: 65000:1001  (branch identity)
  Import RT: 65000:999   (hub routes)

HUB-VRF (Corporate HQ / Internet gateway):
  Export RT: 65000:999   (hub identity)
  Import RT: 65000:1001  (branch 1)
             65000:1002  (branch 2)
             65000:1003  (branch 3)
             ... (or a wildcard range policy)

Result:
  Branches receive HUB routes (default route, shared services)
  HUB receives all branch routes (for return path)
  Branches do NOT receive each other's routes (RT 65000:1001 ≠ RT 65000:1002)
  → Spoke-to-spoke traffic must hairpin through hub (intentional)
```

```
VRF Design: Full-Mesh (Any-to-Any) Topology

ALL VRFs:
  Export RT: 65000:100  (shared community)
  Import RT: 65000:100  (same shared community)

Result: Every VRF receives every other VRF's routes.
Use case: All sites belong to same L3VPN, need full connectivity.
```

```
VRF Design: Extranet (Shared Service)

SHARED-SERVICES-VRF (DNS, NTP, AD):
  Export RT: 65000:500

CUSTOMER-A-VRF:
  Export RT: 65000:1001
  Import RT: 65000:1001, 65000:500  ← imports shared services

CUSTOMER-B-VRF:
  Export RT: 65000:1002
  Import RT: 65000:1002, 65000:500  ← imports shared services

Result: Customers A and B share access to shared services VRF,
but do NOT receive each other's routes.
```

### RT and VPN Label Binding

When a route is imported into a VRF, the PE **allocates a VPN label** bound
to that route (or per-VRF, depending on label allocation mode). When the
egress PE receives a labeled packet, it uses the VPN label to:

1. Identify which VRF to look up (label → VRF)
2. Look up the destination IP in that VRF's FIB
3. Forward to the CE

Label allocation modes:
- **Per-prefix**: One label per customer prefix. Fine-grained but label-hungry.
- **Per-VRF**: One label per VRF. All prefixes in the VRF share one label.
  PE does a FIB lookup after label pop. Most common in production.
- **Per-CE**: One label per CE interface. All routes from one CE share one label.

---

## 11. MP-BGP for VPNv4: RFC 4760 + RFC 4364

### Multiprotocol BGP Extension (RFC 4760)

Standard BGP (RFC 4271) only carries IPv4 unicast prefixes in its NLRI
(Network Layer Reachability Information) field. RFC 4760 extends BGP to
carry multiple address families via two new optional, non-transitive attributes:

- `MP_REACH_NLRI` (Type code 14): Carries reachable prefixes for an AFI/SAFI
- `MP_UNREACH_NLRI` (Type code 15): Withdraws prefixes for an AFI/SAFI

AFI (Address Family Identifier) and SAFI (Subsequent AFI) together identify
the type of routes being carried.

For VPNv4: **AFI = 1 (IPv4), SAFI = 128 (MPLS-labeled VPN)**

### MP_REACH_NLRI Wire Format (RFC 4760, Section 3)

```
MP_REACH_NLRI Attribute:
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Attr Flags   |  Type = 14    |     Length (2 or 3 bytes)     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         AFI (2 bytes)         |    SAFI (1 byte)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Next Hop Len  |        Next Hop Address (variable)            |
+-+-+-+-+-+-+-+-+                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    SNPA (1 byte = 0)          |   NLRI (variable)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

For VPNv4:
  AFI = 0x0001 (IPv4)
  SAFI = 0x80 (128 = labeled VPN unicast)
  Next Hop Len = 12 (RD 8 bytes + IPv4 next-hop 4 bytes)
              or 0  (if using loopback as next-hop directly)
  Next Hop = PE loopback address (reachable via IGP in provider core)
```

### VPNv4 NLRI Structure (RFC 4364, Section 4.3.4)

Each NLRI entry in the UPDATE carries:

```
VPNv4 NLRI entry:
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Length (bits)|  Label (20 bits)              |Exp|S|   TTL   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Route Distinguisher (8 bytes)                |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   IP Prefix (0-32 bits, variable)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Length: total prefix length in bits = 24 (label) + 64 (RD) + IP prefix len
        For 10.0.0.0/8: Length = 24 + 64 + 8 = 96 bits

Label field: 20-bit MPLS label + Exp(3) + S(1) + TTL(8)
             This is the VPN (inner) label.
             S=1 (bottom of stack) since it's the only label in NLRI.
             TTL is typically set to 0 or ignored.

RD: 8-byte Route Distinguisher (as per Section 9 above)

IP Prefix: The actual customer prefix (host bits zeroed)
```

### Full BGP UPDATE Message for VPNv4

```
BGP UPDATE Message:
┌─────────────────────────────────────────────────────────────────┐
│  BGP Header (19 bytes)                                          │
│  Marker (16 bytes all 1s) + Length (2 bytes) + Type=2 (1 byte) │
├─────────────────────────────────────────────────────────────────┤
│  Withdrawn Routes Length = 0 (VPNv4 withdrawals in MP_UNREACH) │
├─────────────────────────────────────────────────────────────────┤
│  Path Attributes Length = N                                     │
├─────────────────────────────────────────────────────────────────┤
│  ORIGIN attribute (Type 1)                                      │
│  Flags: 0x40 (transitive, well-known)                          │
│  Length: 1, Value: 0 (IGP) / 1 (EGP) / 2 (INCOMPLETE)         │
├─────────────────────────────────────────────────────────────────┤
│  AS_PATH attribute (Type 2)                                     │
│  For ibgp between PE and RR: AS_PATH = empty (same AS)         │
├─────────────────────────────────────────────────────────────────┤
│  LOCAL_PREF attribute (Type 5)                                  │
│  Used for path selection between PEs within the provider AS    │
├─────────────────────────────────────────────────────────────────┤
│  MP_REACH_NLRI attribute (Type 14)                             │
│  Flags: 0x80 (optional, non-transitive)                        │
│  AFI=1, SAFI=128                                               │
│  Next-Hop = PE2 loopback (e.g., 10.255.0.2)                   │
│  NLRI: [96 bits] label=1001, RD=65000:100, prefix=10.0.0.0/8  │
│  NLRI: [96 bits] label=1002, RD=65000:100, prefix=172.16.0.0/12│
├─────────────────────────────────────────────────────────────────┤
│  EXTENDED_COMMUNITIES attribute (Type 16)                       │
│  Flags: 0xC0 (optional, transitive)                            │
│  Value: RT 65000:100  (00:02:FD:E8:00:00:00:64)                │
│         RT 65000:200  (00:02:FD:E8:00:00:00:C8) [if extranet]  │
├─────────────────────────────────────────────────────────────────┤
│  NLRI (IPv4 unicast) = empty (for VPNv4, NLRI is in MP_REACH)  │
└─────────────────────────────────────────────────────────────────┘
```

### Address Family Negotiation

Before exchanging VPNv4 routes, PEs must negotiate the VPNv4 address family
in their BGP OPEN message via the Multiprotocol Extensions Capability
(RFC 3392 / RFC 4760):

```
BGP OPEN Capabilities (Option Type 2):
┌─────────────────────────────────────────────────────────┐
│ Capability Code = 1 (Multiprotocol Extensions, RFC 4760)│
│ Capability Length = 4                                    │
│ AFI  = 0x0001 (IPv4)                                    │
│ Res  = 0x00                                             │
│ SAFI = 0x80  (128 = labeled VPN unicast = VPNv4)        │
└─────────────────────────────────────────────────────────┘

Additionally, for route reflection:
│ Capability Code = 2 (Route Refresh, RFC 2918)           │
│ Capability Code = 65 (4-byte ASN, RFC 6793)             │
│ Capability Code = 69 (ADD-PATH, RFC 7911)               │
   ADD-PATH enables multiple paths per prefix, critical for
   fast convergence and BGP PIC (Prefix Independent Convergence)
```

---

## 12. PE-CE Routing: Protocol Options and Their Tradeoffs

The protocol between PE and CE is **per-VRF and completely independent** of
the MP-BGP running between PEs. The CE doesn't know it's connected to an
MPLS VPN — it just speaks a routing protocol to its PE.

### Option A: Static Routes (Simplest)

```
CE ─────── PE
    static    │ redistribute static into VRF BGP
```

- CE has a static default route or specific routes to PE.
- PE has static routes for CE's subnets, redistributed into VRF routing table.
- **Pro**: Zero routing protocol overhead, no adjacency to maintain.
- **Con**: No automatic failover, no prefix-level granularity without many statics.
- **When**: Small CE sites, customer-managed CPE, IPv6 with simple topology.

### Option B: eBGP PE-CE (RFC 4364 Recommended)

```
CE (AS 65001) ─── eBGP ─── PE (AS 65000, VRF instance)
```

- CE and PE run eBGP in the standard way.
- PE imports CE prefixes into its VRF RIB.
- PE exports VRF routes to CE via eBGP.
- **Pro**: Full BGP attribute control, supports complex policies, loop prevention
  via AS-PATH, scales to large CE routing tables.
- **Con**: CE must support BGP. CE has AS number (private ASN for CPE).
- **Loop prevention**: The AS-PATH will contain the provider AS, so a route
  leaked back to the customer side via another path will be rejected.
- **When**: Managed CE, enterprise with BGP-capable routers, internet gateway VRF.

### Option C: OSPF PE-CE (Sham Link for Backdoor Links)

```
CE ─── OSPF Area 0 ─── PE → [MPLS Core] → PE ─── OSPF Area 0 ─── CE
                  VRF-OSPF instance (separate per VRF)
```

OSPF on the PE-CE link runs as a dedicated OSPF process bound to the VRF.
The PE redistributes these OSPF routes into VRF BGP (VPNv4) for transport
across the MPLS core, then redistributes BGP back into OSPF on the remote PE.

**The sham link problem**: If CE-A and CE-B have a direct (backdoor) link
in OSPF Area 0, OSPF prefers intra-area routes over inter-area. The backdoor
link wins over the MPLS VPN path, even if the MPLS path is better. Solution:
configure a BGP-signaled **sham link** between PEs, which appears to OSPF
as an intra-area link, restoring the ability to prefer the VPN path.

**Down bit**: Routes redistributed from BGP into OSPF are marked with the
DN (Down) bit in the LSA Type-3 or Type-5 to prevent re-import into BGP at
the remote PE, avoiding routing loops.

```
LSA Type-3 (Summary LSA) with DN bit:
  Options field, bit 0x20 (DN bit) = 1
  Meaning: "This route came from outside OSPF (BGP) — do not redistribute
            back into BGP"
```

### Option D: RIPv2 PE-CE (Legacy)

Rarely used today. RIP is bounded to 15 hops, lacks traffic engineering,
and has slow convergence. Only seen in very old deployments.

### Option E: IS-IS PE-CE

Uncommon. IS-IS lacks natural VRF support in implementations. Only when CE
runs IS-IS natively (e.g., some IXP deployments).

---

## 13. VRF Route Leaking

Route leaking is the controlled admission of routes from one VRF into another
VRF. It is the mechanism for shared services, internet access from a VRF,
and extranet designs.

### The Leaking Invariant

**Route leaking is not a violation of VRF isolation — it is an explicit,
configured, unidirectional admission of a specific prefix from one VRF's
routing table into another VRF's routing table.**

The leak is explicit: you name the source VRF, the prefix, the target VRF.
There is no implicit leaking. A misconfiguration that allows unintended leaking
is a security failure, not a VRF design feature.

### Mechanisms for Leaking

#### 1. Static Route with VRF next-hop (Linux / IOS)

The simplest leak: a static route in VRF-B points to a next-hop that lives
in VRF-A.

```
# Linux: leak a route from vrf-red into vrf-blue
ip route add 10.0.0.0/8 vrf vrf-blue nexthop via 192.168.1.1 dev eth1

# The next-hop (192.168.1.1) is reachable via vrf-red's interfaces
# Traffic enters vrf-blue routing, matches 10.0.0.0/8, forwarded
# to 192.168.1.1 which is resolved via vrf-red
```

#### 2. RT-based Leaking in MPLS L3VPN

The most elegant mechanism: use RT import/export to pull routes from
one VRF into another VRF on the same PE (or across PEs).

```
INTERNET-VRF:
  Connected: 0.0.0.0/0 (internet uplink)
  Export RT: 65000:999

CUSTOMER-A-VRF:
  Import RT: 65000:1001 (own routes)
             65000:999  (also import internet VRF routes!)

Result: Customer-A-VRF now has a route to 0.0.0.0/0 via INTERNET-VRF.
Customer traffic hits 0.0.0.0/0 in their VRF, is forwarded to the
INTERNET-VRF gateway.
```

#### 3. BGP "Leaking" via Redistribution

On a single PE:
```
router bgp 65000
  address-family ipv4 vrf CUSTOMER-A
    redistribute bgp vpn into unicast  ! import from global BGP into VRF
  address-family ipv4 vrf INTERNET
    redistribute unicast into bgp vpn  ! export from VRF into global BGP
```

#### 4. FRR/Linux: VRF Route Leaking via BGP VRF import

FRR supports explicit VRF route leaking between local VRFs via BGP:

```
router bgp 65000 vrf vrf-red
  address-family ipv4 unicast
    import vrf vrf-blue  ! import all routes from vrf-blue into vrf-red
    import vrf route-map LEAK-FILTER  ! with policy
```

This is a local-only operation — routes are copied into the local VRF's RIB
from another local VRF, without any BGP signaling to remote peers.

### Security Implications of Route Leaking

Route leaking is one of the most common sources of security boundary violations
in VRF deployments:

1. **Unintended RT overlap**: If two VRFs accidentally share an RT value,
   their routes will be mutually imported. Overlapping prefixes will create
   forwarding ambiguity. Non-overlapping prefixes will violate isolation.

2. **Asymmetric leaking**: Leaking a route from VRF-A into VRF-B without
   leaking the return path creates a black hole. Traffic leaves via the
   leaked route but return traffic hits VRF-A's table and has no route back.

3. **Internet-to-VRF leaking without ACL**: Leaking a default route from
   an INTERNET-VRF into a CUSTOMER-VRF without firewall policy allows the
   customer to route arbitrary traffic to the internet, potentially exfiltrating
   data or accessing unintended destinations.

4. **Label confusion in hardware**: In ASICs with shared label space across
   VRFs, a software bug or hardware fault causing label aliasing can leak
   packets between VRFs at the forwarding plane level, bypassing all RT policy.

---

## 14. VRF and OSPF: Per-VRF Instances

When OSPF runs as a PE-CE protocol, it runs as a **separate OSPF process
instance bound to a VRF**. This is not just a different area — it is a
completely separate OSPF process with its own LSDB, adjacencies, SPF computation,
and RIB.

### OSPF Instance Binding (FRR syntax)

```
router ospf 1 vrf CUSTOMER-A
  router-id 10.255.0.1
  redistribute bgp        ! inject routes learned from remote PEs via BGP
  area 0
  network 10.1.0.0/30 area 0
```

```
router ospf 2 vrf CUSTOMER-B
  router-id 10.255.0.2
  redistribute bgp
  area 0
  network 172.16.0.0/30 area 0
```

Two completely separate OSPF instances with separate LSDBs. CUSTOMER-B's
OSPF has no knowledge of CUSTOMER-A's topology.

### OSPF LSA Flooding and VRF Boundary

OSPF flooding is bounded to the OSPF process. An LSA in CUSTOMER-A's OSPF
process cannot flood into CUSTOMER-B's OSPF process. The VRF binding of the
process enforces this at the socket level — OSPF packets on CUSTOMER-A's
interfaces are received only by the socket bound to CUSTOMER-A's process.

### The DN Bit — Preventing OSPF Re-Import Loops

```
Without DN bit — the loop:
CE-A → PE1 (learn via OSPF) → redistribute to VRF BGP → MP-BGP to PE2
PE2 → redistribute BGP to OSPF → CE-B learns route
CE-B → PE2 (redistributes back to OSPF LSA)
PE2 → this LSA is flooded back to PE1 via OSPF
PE1 → sees it as an OSPF intra-area route → beats the BGP route → loop!

With DN bit:
PE2 sets DN bit when redistributing BGP → OSPF (Type-3 or Type-5 LSA).
PE1 receives LSA with DN bit set.
PE1's VRF OSPF process: "DN bit set → do not redistribute this back to BGP."
Loop prevented.
```

The DN bit is set in:
- LSA Type-3 (Summary): In the Options field (bit 0x20, per RFC 4577)
- LSA Type-5 (External): In the Options field
- LSA Type-7 (NSSA External): In the Options field

---

## 15. VRF and BGP: Address Family Architecture

BGP in a VRF context runs in **per-VRF address families**. Understanding
this architecture prevents the most common BGP+VRF misconfigurations.

### BGP Process Structure in a PE

A PE router typically runs a **single BGP process** with multiple address families:

```
BGP Process (AS 65000):
├── Address Family: IPv4 Unicast (global table)
│       Neighbors: iBGP to RR, eBGP to internet peers
│       No VRF involvement — this is the global routing table
│
├── Address Family: VPNv4 Unicast (AFI=1, SAFI=128)
│       Neighbors: iBGP to RR (reflects VPNv4 routes between PEs)
│       Carries: RD+prefix + VPN label + RT communities
│
├── Address Family: IPv4 Unicast, VRF CUSTOMER-A
│       Neighbors: eBGP to CE-A (192.168.1.2)
│       Routes learned here are exported with RD+RT into VPNv4 AF
│
├── Address Family: IPv4 Unicast, VRF CUSTOMER-B
│       Neighbors: eBGP to CE-B (172.16.0.2)
│       Routes learned here are exported with RD+RT into VPNv4 AF
│
└── Address Family: IPv6 VPN (VPNv6, AFI=2, SAFI=128)
        For IPv6 customers — same architecture, different AFI
```

### The Export Process (CE → VPNv4)

```
CE-A announces 10.0.0.0/8 via eBGP to PE1, VRF CUSTOMER-A AF.

PE1 actions:
1. Install 10.0.0.0/8 in VRF CUSTOMER-A RIB (IPv4 unicast).
2. Allocate/assign VPN label (e.g., 1001) for this prefix.
3. Prepend RD (65000:100) to form VPNv4 prefix: "65000:100:10.0.0.0/8"
4. Attach RT extended community: 65000:100 (export RT of CUSTOMER-A VRF)
5. Set BGP next-hop to PE1's loopback: 10.255.0.1
6. Encode VPN label (1001) in the NLRI label field.
7. Advertise via MP-BGP VPNv4 AF to RR.

RR receives, applies RT-based outbound policy, reflects to interested PEs.

PE2 receives VPNv4 UPDATE:
1. Check RT: does 65000:100 match any local VRF import RT?
2. Yes: VRF CUSTOMER-A imports RT 65000:100.
3. Strip RD, install 10.0.0.0/8 in VRF CUSTOMER-A's RIB with:
   next-hop = 10.255.0.1 (PE1 loopback), VPN label = 1001, transport label via LDP/RSVP-TE.
4. Download to VRF CUSTOMER-A FIB.
```

### RT Filtering at the RR

Route Reflectors should filter VPNv4 routes by RT to avoid sending every PE
every VPN route (which would eliminate the scalability benefit):

```
RFC 4684 — Constrained Route Distribution (BGP RT Membership):

PEs advertise which RTs they have VRFs for (RT membership NLRI).
RRs use this to filter: only reflect VPNv4 routes with RT X to PEs
that have a VRF importing RT X.

Without RFC 4684: Every PE receives every VPNv4 route and must filter
locally. At 10,000 PEs and 100,000 VPN prefixes, this is 10^9 route
advertisements — unscalable.

With RFC 4684: Each PE receives only VPNv4 routes for RTs it imports.
Massive reduction in BGP UPDATE traffic and PE memory consumption.
```

---

## 16. Data Plane: Packet Walk Through an MPLS L3VPN

This is the complete packet lifecycle from CE to CE.

### Ingress PE (PE1) — Label Push

```
Packet arrives from CE-A on interface eth1 (enslaved to VRF CUSTOMER-A):

1. VRF selection: eth1 → VRF CUSTOMER-A
2. FIB lookup in VRF CUSTOMER-A: dest 172.16.5.1 → matches 172.16.0.0/12
   Next-hop: 10.255.0.2 (PE2 loopback), VPN label: 2001, via LSP
3. Resolve 10.255.0.2: LDP/RSVP-TE gives transport label = 3001 (to PE2)
4. Build label stack:
   ┌──────────────────────────────────────────────┐
   │ Ethernet Header (src: PE1-mac, dst: P1-mac)  │
   ├──────────────────────────────────────────────┤
   │ Transport Label: 3001, S=0, TTL=255          │  ← outer, for P router
   ├──────────────────────────────────────────────┤
   │ VPN Label: 2001, S=1, TTL=255                │  ← inner, for egress PE
   ├──────────────────────────────────────────────┤
   │ Original IP packet (src:10.0.0.1,dst:172.16.5.1) │
   └──────────────────────────────────────────────┘
5. Forward out toward P1.
```

### P Router — Label Swap

```
P1 receives labeled packet:
1. Look up top label (3001) in LFIB (Label Forwarding Information Base).
2. Action: SWAP label 3001 → 4001, forward to P2.
   (P1 does not know or care about inner label 2001 or IP header)
3. Decrement TTL in outer label.

P2 receives:
1. Look up top label (4001).
2. Action: POP (penultimate hop pop — PHP) since next hop is PE2.
   After PHP, packet has only VPN label 2001 on top.
3. Forward to PE2.
```

### Egress PE (PE2) — Label Pop + VRF Lookup

```
PE2 receives packet with only VPN label 2001:
1. Look up label 2001 in VPN LFIB.
   VPN label 2001 → VRF CUSTOMER-A, action: POP and do L3 lookup.
2. Pop label 2001. Packet is now bare IP: dst = 172.16.5.1.
3. L3 FIB lookup in VRF CUSTOMER-A: 172.16.5.1 → 172.16.0.0/12 via CE-B.
4. Forward to CE-B.
```

### Packet Transformation Summary

```
CE-A sends:    [EthHdr][IPHdr: src=10.0.0.1, dst=172.16.5.1][Payload]
At PE1:        [EthHdr][Label:3001,S=0][Label:2001,S=1][IPHdr][Payload]
At P1:         [EthHdr][Label:4001,S=0][Label:2001,S=1][IPHdr][Payload]
After PHP/P2:  [EthHdr][Label:2001,S=1][IPHdr][Payload]
At PE2:        [EthHdr][IPHdr: src=10.0.0.1, dst=172.16.5.1][Payload]
CE-B receives: [EthHdr][IPHdr: src=10.0.0.1, dst=172.16.5.1][Payload]
```

CE-A and CE-B see a normal IP network. The MPLS label stack is entirely
invisible to them. The IP TTL appears to decrement by 1 (uniform TTL mode)
or remains unchanged (pipe mode, configured on PE).

---

## 17. VRF in Linux: iproute2, netns, and the Kernel L3 Master Device

### The Linux VRF Driver

The Linux VRF driver (`net/l3mdev/`) was merged in kernel 4.3. It implements
the `l3mdev` (Layer 3 Master Device) abstraction.

### Full Implementation Reference

```bash
# ─── Create VRF devices ───────────────────────────────────────────
ip link add vrf-red  type vrf table 100
ip link add vrf-blue type vrf table 200

ip link set vrf-red  up
ip link set vrf-blue up

# ─── Enslave interfaces ───────────────────────────────────────────
ip link set eth1 master vrf-red
ip link set eth2 master vrf-red
ip link set eth3 master vrf-blue

# Connected routes are automatically installed in VRF table upon enslavement.
# Check:
ip route show table 100   # vrf-red routes
ip route show table 200   # vrf-blue routes

# ─── Add routes to VRF tables ────────────────────────────────────
ip route add 10.0.0.0/8   via 192.168.1.1 vrf vrf-red
ip route add 0.0.0.0/0    via 10.0.0.1    vrf vrf-blue

# ─── ip rule — policy routing dispatch ───────────────────────────
# Automatically inserted by kernel when VRF is created:
# 1000: from all lookup [l3mdev-table]
ip rule show
# Manually add per-source-IP rules if needed:
ip rule add from 10.0.0.0/8 lookup 100  priority 100

# ─── VRF-aware ping / traceroute ─────────────────────────────────
ping -I vrf-red 10.1.0.1
traceroute -i vrf-red 10.1.0.1
ip route get 10.1.0.1 vrf vrf-red

# ─── VRF-aware ss / netstat ──────────────────────────────────────
ss -d vrf vrf-red        # sockets bound to vrf-red

# ─── FRR daemon binding to VRF ───────────────────────────────────
# In /etc/frr/daemons:
# bgpd_vrf=vrf-red
# In FRR config:
# router bgp 65000 vrf vrf-red
#   neighbor 10.1.0.1 remote-as 65001
```

### The sysctl: net.vrf.strict_mode

```bash
# Default: strict_mode = 0
# Allows packets arriving on a VRF interface to match routes in the
# global (main) table if no match in VRF table.
# Security risk: leaks packets to global routing table unintentionally.

# Recommended: strict_mode = 1
# Packets on VRF-enslaved interfaces ONLY match routes in VRF table.
# No fallthrough to main table.
sysctl -w net.vrf.strict_mode=1
```

This is a **critical security setting** for any multi-tenant or isolation
use case. Without `strict_mode=1`, a packet arriving on a VRF-enslaved
interface with no matching route in the VRF table will fall back to the
main routing table and may be forwarded to an unintended destination.

### iptables/nftables and VRF

iptables and nftables are VRF-aware from Linux 4.11+. The `PREROUTING`
chain fires **after** VRF table lookup. To write per-VRF firewall rules:

```bash
# Match on ingress VRF (by incoming interface, which is the VRF master device)
iptables -A FORWARD -i vrf-red -j VRF-RED-POLICY
iptables -A FORWARD -i vrf-blue -j VRF-BLUE-POLICY

# Or match by routing mark / vrf table
# Note: iptables sees the VRF master device as -i, not the enslaved interface
```

In nftables:

```
table inet vrf-filter {
    chain forward {
        type filter hook forward priority 0;
        iifname "vrf-red"  jump vrf-red-policy
        iifname "vrf-blue" jump vrf-blue-policy
    }
}
```

---

## 18. VRF vs. Network Namespaces: When to Use Which

This is one of the most important architectural decisions in Linux networking.

### Network Namespaces (netns)

A network namespace provides complete isolation of:
- All network interfaces
- All routing tables (including main, local, default)
- All sockets and connections
- All iptables/nftables rules
- All netfilter state
- All ARP/ND tables

Each netns has its own kernel networking stack. Processes in netns-A cannot
see interfaces, routes, or sockets in netns-B without explicit veth pairs
or cross-namespace operations.

### VRF (L3 Master Device)

VRF provides isolation of:
- L3 routing tables (separate FIB per VRF)
- L3 forwarding decisions
- Routing protocol scope (FRR daemon per-VRF)

VRF does NOT isolate:
- L2 (interfaces share the same kernel network stack)
- iptables/nftables (requires explicit per-VRF rules)
- ARP tables (shared, though VRF-aware from kernel 4.13+)
- Sockets at the OS level (unless explicitly bound to VRF device)
- Raw socket access — a privileged process can sniff all VRFs

### Decision Matrix

```
┌──────────────────────────────┬─────────────────┬──────────────────┐
│ Requirement                  │ VRF             │ Network Namespace│
├──────────────────────────────┼─────────────────┼──────────────────┤
│ Separate routing tables only │ ✓ (preferred)   │ overkill         │
│ Separate firewall rules      │ via iif match   │ ✓ (cleaner)      │
│ Full network stack isolation │ ✗               │ ✓                │
│ Separate socket namespacing  │ ✗               │ ✓                │
│ Kubernetes pod isolation     │ ✗               │ ✓ (CNI uses)     │
│ Routing daemon per-tenant    │ ✓ (FRR VRF)     │ ✓ (separate proc)│
│ Shared physical interfaces   │ ✓               │ via veth only    │
│ MPLS L3VPN on Linux PE       │ ✓               │ awkward          │
│ Multi-tenant container host  │ partial         │ ✓                │
│ BGP per-VRF with FRR         │ ✓ (native)      │ requires netns   │
│ Security/audit separation    │ insufficient    │ ✓                │
└──────────────────────────────┴─────────────────┴──────────────────┘
```

### The Hybrid Pattern (Kubernetes EVPN/VRF Node)

In cloud-native network functions (CNFs) acting as L3VPN PEs on Kubernetes:

```
┌────────────────────────────────────────────────────────────────────┐
│  Kubernetes Node                                                    │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ VRF-RED (table 100)                                          │  │
│  │ eth1, eth2 enslaved                                          │  │
│  │ FRR bgp 65000 vrf vrf-red                                    │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Network Namespace: pod-xyz                                    │  │
│  │ veth0 ↔ veth1 (host side enslaved to vrf-red)               │  │
│  │ Pod routing table: 10.244.1.0/24 via 169.254.1.1            │  │
│  └──────────────────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

Pods get network namespace isolation (full stack). The node routing uses
VRF for per-tenant L3 separation. The veth host end is enslaved to the
correct VRF, connecting pod isolation with node-level VRF routing.

---

## 19. VRF in Kubernetes and Cloud-Native Environments

### Standard Kubernetes Networking (No VRF)

Standard Kubernetes CNI (Calico, Flannel, Cilium) creates a flat overlay
network. All pods share one routing domain. Pod-to-pod isolation is via
NetworkPolicy (iptables/eBPF rules), not routing separation.

### When VRF Matters in Kubernetes

1. **Multi-tenant Kubernetes** (namespace-level routing isolation): Each
   namespace's pods should have completely separate routing domains, including
   separate egress paths and overlapping IP ranges between tenants.

2. **Kubernetes as a network function platform**: When pods are VNFs (virtual
   network functions) acting as routers, firewalls, or PE routers themselves.

3. **BGP integration with spine-leaf fabric**: When the Kubernetes node is
   a BGP speaker advertising pod routes into a fabric that uses VRF-separated
   tenants (common in telco/NFVi environments).

4. **EVPN/VXLAN with per-VRF L3 VNI**: When the underlay uses EVPN (BGP
   signaled VXLAN) with per-VRF L3 VNIs, the Linux node needs VRF awareness
   to map L3 VNI → VRF table.

### Cilium and VRF

Cilium's eBPF datapath does not use Linux VRF directly — it manages its own
routing tables via eBPF maps. However, for EVPN integration (Cilium + BGP CP):

```
Cilium BGP Control Plane (Cilium 1.13+):
- Uses GoBGP/FRR underneath for BGP sessions
- Advertises pod CIDRs into VPNv4 address family (per-VRF)
- Maps Kubernetes namespaces to BGP VRF instances
- Route Targets derived from Kubernetes namespace labels
- EVPN L3 VNI → Linux VRF table mapping
```

### EVPN L3 VNI and VRF Mapping

EVPN (RFC 7432) uses VXLAN with per-VRF L3 VNIs for inter-subnet routing.
The L3 VNI maps directly to a Linux VRF:

```
EVPN L3 VNI 100 → VRF vrf-red (table 100)
EVPN L3 VNI 200 → VRF vrf-blue (table 200)

Configuration (FRR EVPN + VRF):
router bgp 65000
  address-family l2vpn evpn
    advertise ipv4 unicast     ! advertise VRF routes as EVPN Type-5
    vni 100 vrf vrf-red        ! map L3 VNI to VRF
    vni 200 vrf vrf-blue
```

EVPN Type-5 routes (IP prefix routes) carry the L3 VNI, which the receiving
VTEP uses to determine which VRF to install the route in.

```
EVPN Type-5 Route NLRI (BGP):
┌────────────────────────────────────────────────────────────────┐
│  Route Type = 5 (IP Prefix Route)                              │
│  Length = variable                                             │
├────────────────────────────────────────────────────────────────┤
│  Route Distinguisher (8 bytes)                                 │
├────────────────────────────────────────────────────────────────┤
│  ESI (10 bytes, all zeros for Type-5)                          │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Tag ID (4 bytes, 0 for L3VNI based)                  │
├────────────────────────────────────────────────────────────────┤
│  IP Prefix Length (1 byte)                                     │
├────────────────────────────────────────────────────────────────┤
│  IP Prefix (4 or 16 bytes, IPv4 or IPv6)                       │
├────────────────────────────────────────────────────────────────┤
│  Gateway IP (4 or 16 bytes)                                    │
├────────────────────────────────────────────────────────────────┤
│  VNI/MPLS Label (3 bytes) ← L3 VNI encoded as MPLS label      │
└────────────────────────────────────────────────────────────────┘
Extended Communities attached:
  RT: determines which VRF imports this route
  Encapsulation: 0x030C (VXLAN) or MPLS
  Router's MAC: gateway MAC for ARP suppression
```

---

## 20. VRF Security Architecture

### Threat Model

VRF provides routing-plane isolation, not a security boundary equivalent
to a firewall or physical separation. Understanding the threat model is
critical before using VRF as a security control.

**VRF does prevent**:
- Routing table contamination between tenants (without explicit leaking)
- Accidental IP-level reachability between VRFs (without a configured path)
- Routing protocol advertisements crossing VRF boundaries

**VRF does NOT prevent**:
- L2 attacks between interfaces that share the same switch fabric
- Exploitation of bugs in the routing daemon (FRR, IOS) affecting all VRFs
- Attacks on the control plane socket (shared BGP process, shared OSPF process
  except in strict per-process configurations)
- Hardware bugs causing label aliasing (ASIC-specific)
- Privileged process on the PE accessing all VRF routing tables
- Timing side channels via shared CPU/memory on the PE

### Management VRF: The OOB Security Pattern

```
Management VRF (vrf-mgmt):
  Interfaces: dedicated OOB management ports (ma0, ma1)
  Routes: management network only (192.168.100.0/24)
  No default route (cannot reach internet via this VRF)
  SSH, SNMP, gNMI, syslog bound to this VRF only
  Data plane VRFs: eth0-ethN (customer traffic)
  No route between vrf-mgmt and data VRFs (no explicit leak)

Security properties:
  Even if data plane is compromised (e.g., BGP hijack, route injection),
  management plane remains reachable only via OOB interfaces.
  An attacker who compromises a customer CE cannot reach the PE management
  plane because there is no routing path between the customer VRF and the
  management VRF.
```

```bash
# Linux management VRF setup
ip link add vrf-mgmt type vrf table 1000
ip link set vrf-mgmt up
ip link set ma0 master vrf-mgmt
ip route add default via 192.168.100.1 vrf vrf-mgmt

# Bind management daemons to management VRF
# sshd: use ListenAddress 192.168.100.x + SO_BINDTODEVICE
# snmpd: agentAddress 192.168.100.x%vrf-mgmt
# FRR: bind management sockets to vrf-mgmt

# Explicitly block cross-VRF routing (nftables)
nft add rule inet filter forward iifname "vrf-mgmt" oifname != "vrf-mgmt" drop
nft add rule inet filter forward oifname "vrf-mgmt" iifname != "vrf-mgmt" drop
```

### MPLS Label Security Considerations

1. **Label spoofing on untrusted interfaces**: CE routers should never be
   trusted to send labeled packets. PE must:
   - Strip any MPLS labels on CE-facing interfaces (MPLS disabled on CE ports)
   - Only accept labeled packets from trusted P/PE peers

2. **Label range exhaustion**: MPLS label space is 20 bits (1M labels).
   In per-prefix allocation mode with many VRFs and many prefixes, label
   space can be exhausted. Per-VRF allocation (one label per VRF) is more
   scalable but requires FIB lookup at egress PE.

3. **BGP RT communities and unauthorized import**: If an attacker can inject
   a BGP UPDATE with a forged RT value, they may cause route import into an
   unintended VRF. Always authenticate BGP sessions (BGP MD5, or preferably
   TTL Security / GTSM + TCP-AO).

4. **VPNv4 route leakage via misconfigured RR route policy**: RRs should
   have strict outbound route policies. A misconfigured RR that reflects all
   VPNv4 routes to all PEs is a privacy violation (tenants can see each
   other's prefixes in BGP table dumps, even if routing is isolated).

### TCP-AO for BGP Session Security

BGP sessions (including MP-BGP VPNv4) should use TCP-AO (RFC 5925) rather
than BGP MD5 (RFC 2385). TCP-AO:
- Uses modern HMAC algorithms (HMAC-SHA1, AES-128-CMAC)
- Supports key rotation without session reset
- Protects against sequence number attacks
- Is the IETF-recommended replacement for TCP MD5

```
For FRR/Linux BGP:
neighbor 10.255.0.2 password <md5-key>           ! old, MD5 only
! TCP-AO support in Linux kernel 6.7+, FRR 9.1+:
neighbor 10.255.0.2 ao-key <key-id> <algorithm> <key>
```

---

## 21. Failure Modes and Misconfigurations

### 1. RD Collision (Two VRFs, Same RD, Overlapping Prefixes)

**Symptom**: Routes from one VRF silently overwrite routes from another VRF
in the RR's BGP table.

**Cause**: Two different VRFs on different PEs are configured with the same RD.
When both VRFs have a route to 10.0.0.0/8, the RR performs best-path selection
between two VPNv4 prefixes with identical keys (`same-RD:10.0.0.0/8`). One
wins, the other is suppressed.

**Consequence**: One VRF's customers lose reachability to those prefixes.
No alert is generated — BGP best-path selection is silent.

**Detection**: `show bgp vpnv4 unicast all` — check for duplicate prefixes
with different next-hops. Only one next-hop will be active.

**Fix**: Ensure globally unique RD per PE per VRF. Use PE-loopback:VRF-ID
(Type 1) assignment.

### 2. RT Misconfiguration — Unintended Route Import

**Symptom**: Customer A can route to Customer B's subnets. Routing isolation
broken.

**Cause**: Customer A's import RT accidentally matches Customer B's export RT.
For example: Customer A imports `65000:100` and Customer B exports `65000:100`.

**Consequence**: Security isolation failure. Customer A sees Customer B's
routes and can initiate connections. In an ISP context, this is a data breach.

**Detection**: On PE: `show bgp vrf CUSTOMER-A ipv4 unicast` — check for
unexpected prefixes. `show bgp vrf CUSTOMER-A ipv4 unicast summary` to see
which routes are imported from BGP vs. directly connected.

**Fix**: Strict RT numbering convention. Automate RT assignment and audit
with NMS. Use distinct RT ranges per customer group.

### 3. Asymmetric Route Leaking (Black Hole)

**Symptom**: Traffic flows one way but not the other. Connections time out
in one direction.

**Cause**: Route leak from VRF-A into VRF-B was configured, but no return
path from VRF-B to VRF-A. Or return path exists but uses a different
next-hop, creating asymmetric NAT / firewall state issues.

**Consequence**: TCP sessions fail (SYN sent, SYN-ACK arrives on wrong
interface and is dropped by stateful firewall tracking the session in the
other VRF context).

**Fix**: Always configure symmetric leaks or use a firewall VRF as the
transit point with stateful inspection.

### 4. MPLS TTL Expiry — Unexpected Traceroute Behavior

In MPLS, the inner IP TTL is not decremented at P routers (only the label
TTL is). With **pipe mode** (TTL not copied to/from IP), traceroute from CE
to CE shows only the PE hops — the P router hops are invisible. This is
intentional for privacy (providers do not expose core topology to customers)
but can confuse troubleshooting.

With **uniform mode**, IP TTL is decremented at every hop (PE and P), and
traceroute reveals P router addresses. Most ISPs use pipe mode.

### 5. PHP Interaction with VPN Label Exposure

When PHP is enabled, the P router pops the outer label before forwarding to
the egress PE. The packet arrives at the egress PE with only the VPN label.
If the egress PE does not have the VPN label in its LFIB (e.g., because
the route was withdrawn but label not yet cleaned up), it may:
- Drop with ICMP Unreachable (correct behavior)
- Forward to wrong VRF (bug — label aliasing)
- Silently drop (black hole)

This is a transient condition during convergence. BGP convergence timers,
graceful restart, and BFD are used to minimize this window.

### 6. VRF Table ID Collision on Linux

**Symptom**: Routes from two VRFs appear in the same `ip route show table N`
output.

**Cause**: Two `ip link add vrf-xxx type vrf table N` commands used the same
table ID. The kernel does not prevent this. The second VRF silently reuses
the same table.

**Fix**: Maintain a centralized table ID registry. Validate with `ip rule show`
and `ip route show table N` before creating new VRFs.

### 7. FRR VRF Daemon Crash Affecting All VRFs

**Symptom**: All VRFs lose BGP routes simultaneously.

**Cause**: FRR runs a single `bgpd` process serving all VRF instances. A
crash in one VRF's BGP processing (e.g., malformed UPDATE causing assertion
failure) brings down the entire process, affecting all VRFs.

**Mitigation**: FRR supports per-VRF process isolation in newer versions.
Alternatively, use separate FRR process instances per VRF (more resource
intensive but provides process-level fault isolation).

### 8. The "It Compiles But It's Wrong" Equivalent: Correct Routing, Wrong Forwarding

In Linux, if `net.vrf.strict_mode=0` (default), a packet arriving on a VRF
interface with no matching route falls through to the main table. This can
create a situation where:

- Configuration is correct: VRF routes are installed properly.
- Traffic flows "work" because the main table has a matching route.
- But traffic is using the wrong routing domain — the VRF isolation is silently
  bypassed.
- No error is logged. The fallback is transparent.

This is equivalent to "it compiles but it's wrong" — everything appears
functional, but the semantic correctness (VRF isolation) is violated.

---

## 22. Production Operational Patterns

### Route Reflector High Availability

```
Active-Active RR Pair (Best Practice):

PE1 ──ibgp── RR1 (primary cluster)
PE1 ──ibgp── RR2 (secondary cluster)

PE2 ──ibgp── RR1
PE2 ──ibgp── RR2

Each PE has two iBGP sessions — one to each RR.
Each RR is in a separate failure domain (separate rack, power, cooling).
RR1 and RR2 do NOT peer with each other — they both receive from PEs and
reflect independently, causing each PE to receive two copies of each route
(from RR1 and RR2). ADD-PATH (RFC 7911) ensures both paths are retained.

On RR1/RR2 failure: PEs still receive routes from the surviving RR.
Reconvergence: <1s for sessions already established.
```

### BFD for Fast Convergence

BFD (Bidirectional Forwarding Detection, RFC 5880) provides sub-second
failure detection on BGP sessions and IGP adjacencies:

```
BFD Control Packet:
0                   1                   2                   3
0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Vers |  Diag   |Sta|P|F|C|A|D|M|  Detect Mult  |    Length    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       My Discriminator                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                      Your Discriminator                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Desired Min TX Interval                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Required Min RX Interval                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                 Required Min Echo RX Interval                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Vers: Version = 1
Diag: Diagnostic code (why session went down)
Sta: State (0=AdminDown, 1=Down, 2=Init, 3=Up)
Detect Mult: Failure detection multiplier
Desired Min TX / Required Min RX: negotiated hello interval (microseconds)
```

Typical production settings: TX=300ms, RX=300ms, Multiplier=3 → 900ms detection.
For high-speed links with hardware BFD offload: TX=50ms → 150ms detection.

### VRF Monitoring and Observability

```
Key metrics to export (per-VRF):

1. BGP session state per VRF:
   bgp_session_state{vrf="CUSTOMER-A", neighbor="10.1.0.1"} = 6 (Established)
   bgp_prefixes_received{vrf="CUSTOMER-A", neighbor="10.1.0.1"} = 42
   bgp_prefixes_advertised{vrf="CUSTOMER-A", neighbor="10.1.0.1"} = 18

2. FIB entry count per VRF:
   vrf_fib_entries{vrf="CUSTOMER-A"} = 47
   vrf_fib_entries{vrf="CUSTOMER-B"} = 102

3. Traffic counters per VRF (via Linux TC or eBPF):
   vrf_bytes_rx{vrf="CUSTOMER-A"} = 12345678
   vrf_bytes_tx{vrf="CUSTOMER-A"} = 9876543
   vrf_packets_dropped{vrf="CUSTOMER-A", reason="no_route"} = 0

4. Route flap detection:
   Alert: bgp_prefixes_received drops to 0 for any VRF
   Alert: vrf_fib_entries{vrf=X} decreases by >10% within 30s
```

### eBPF/XDP for Per-VRF Packet Classification

In a Linux-based PE or vRouter, eBPF can be used to:
1. Classify packets by VRF at XDP layer (before the kernel networking stack)
2. Maintain per-VRF traffic statistics in BPF maps (ring buffer or perf array)
3. Implement per-VRF rate limiting or ACLs at line rate

```c
// XDP program skeleton: VRF-aware packet counter
// Attached to each VRF-enslaved interface

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __type(key, __u32);      // RT table ID (VRF ID)
    __type(value, __u64);    // packet count
    __uint(max_entries, 256);
} vrf_pkt_count SEC(".maps");

SEC("xdp")
int vrf_counter(struct xdp_md *ctx)
{
    // Get the RT table ID for this interface from a config map
    __u32 ifindex = ctx->ingress_ifindex;
    __u32 *table_id = bpf_map_lookup_elem(&ifindex_to_vrf, &ifindex);
    if (!table_id) return XDP_PASS;  // not VRF-enslaved

    __u64 *count = bpf_map_lookup_elem(&vrf_pkt_count, table_id);
    if (count) __sync_fetch_and_add(count, 1);
    else {
        __u64 init = 1;
        bpf_map_update_elem(&vrf_pkt_count, table_id, &init, BPF_NOEXIST);
    }
    return XDP_PASS;
}
```

### Graceful Restart for VRF BGP Sessions

BGP Graceful Restart (RFC 4724) allows a PE to restart its BGP process
without withdrawing routes from the forwarding plane. During the restart:

1. Peer (RR or CE) marks routes from the restarting PE as "stale" but
   continues forwarding (label still valid in MPLS core).
2. Restarting PE re-establishes BGP session, re-announces all routes.
3. Stale routes replaced with refreshed routes.
4. If restart completes within the Restart Time (default 120s), no traffic
   is lost.

This is especially important for VRF BGP because a bgpd restart on a PE
serving hundreds of VRFs would otherwise cause all VRF routes to be withdrawn
simultaneously.

---

## 23. Connection Map

Understanding VRF fully requires connecting it to these adjacent concepts:

### Protocol Specifications

- **RFC 4364** — The primary BGP/MPLS IP VPN spec. Every concept in Section
  8–11 above traces back here.
- **RFC 4760** — MP-BGP. The extension that enables VPNv4 address family.
- **RFC 4360** — BGP Extended Communities. The wire format of Route Targets.
- **RFC 7432** — BGP EVPN. The modern evolution using Type-5 routes for L3VPN
  without traditional MPLS in the underlay.
- **RFC 5880** — BFD. Fast failure detection for VRF BGP and IGP sessions.
- **RFC 4724** — BGP Graceful Restart. VRF survivability during control plane
  restarts.
- **RFC 4684** — Constrained Route Distribution. RT-based filtering at RRs.
- **RFC 4577** — OSPF as PE-CE protocol. DN bit and sham link specification.
- **RFC 8402** — Segment Routing architecture. The modern replacement for
  LDP in the MPLS transport layer below VRF L3VPN.
- **RFC 9252** — BGP Overlay Services Based on SR over IPv6. VRF over SRv6.

### Linux Kernel References

- `net/l3mdev/` — L3 master device driver (VRF implementation)
- `net/ipv4/fib_trie.c` — FIB lookup implementation (per-VRF table)
- `net/core/filter.c` — SO_BINDTODEVICE, VRF socket binding
- `Documentation/networking/vrf.rst` — Canonical Linux VRF documentation
- `tools/testing/selftests/net/vrf_route_leaking.sh` — Kernel self-tests for
  VRF route leaking

### FRR (Free Range Routing) Implementation

- `bgpd/bgp_mplsvpn.c` — VPNv4 route import/export, RD/RT processing
- `bgpd/bgp_updatesend.c` — MP_REACH_NLRI encoding for VPNv4
- `lib/vrf.c` — FRR VRF abstraction layer
- `zebra/zebra_vrf.c` — Zebra (FIB manager) VRF handling, RIB→FIB download
- `bgpd/bgp_route.c` — BGP best-path selection, per-VRF RIB

### Security Primitives Connected to VRF

- **TCP-AO (RFC 5925)**: Authenticate BGP sessions that carry VPNv4 routes.
  A BGP hijack injecting false RT communities is a VRF boundary violation.
- **GTSM (RFC 5082)**: TTL Security Hack for BGP sessions. Sets IP TTL = 255
  on transmitted packets; receiver rejects packets with TTL < 254. Prevents
  off-link BGP session spoofing.
- **mTLS for gRPC (gNMI/gNOI)**: Management plane sessions to configure VRFs
  (via NETCONF or gNMI) should use mTLS to prevent unauthorized VRF manipulation.
- **BGP RPKI (RFC 6810)**: Origin validation for routes learned from CEs.
  A CE injecting a false prefix should be detected and rejected by the PE's
  route origin validation before it contaminates the VRF RIB.
- **eBPF/XDP**: Can enforce per-VRF ACLs and rate limits at hardware speed,
  below the kernel's IP stack, providing defense-in-depth beyond routing isolation.

### Cloud-Native Connections

- **Cilium BGP CP**: Implements VRF-aware BGP advertising pod CIDRs into
  VPNv4 address families for integration with carrier MPLS networks.
- **Metallb**: Layer 3 load balancer that uses BGP. In VRF environments,
  MetalLB can be configured per-VRF to advertise service IPs into the correct
  VRF routing domain.
- **Whereabouts / Multus**: CNI chaining that assigns pod IPs from per-VRF
  address pools, enabling multi-homed pods in separate VRFs.
- **SR-IOV + VRF**: Physical NIC SR-IOV VFs can be enslaved to VRFs, giving
  hardware-accelerated per-VRF forwarding with VF queue isolation.

---

## Appendix: Quick Reference

### VRF Operational Commands

```bash
# Linux iproute2
ip vrf show                          # list all VRFs
ip vrf exec vrf-red ping 10.0.0.1    # run command in VRF context
ip route show vrf vrf-red            # VRF routing table
ip neigh show vrf vrf-red            # VRF ARP/ND table
ip link show master vrf-red          # interfaces enslaved to VRF

# FRR vtysh
show vrf                             # list VRFs known to FRR
show bgp vrf CUSTOMER-A summary      # BGP sessions in VRF
show bgp vrf CUSTOMER-A ipv4 unicast # BGP RIB for VRF
show ip route vrf CUSTOMER-A         # Routing table (all protocols) for VRF
show mpls table                      # MPLS LFIB (label forwarding)
show bgp vpnv4 unicast all           # All VPNv4 routes across all VRFs
show bgp vpnv4 unicast rd 65000:100  # Routes with specific RD
```

### Key RFCs at a Glance

| RFC | Title | Relevance |
|---|---|---|
| 4364 | BGP/MPLS IP VPNs | The core L3VPN spec |
| 4760 | MP-BGP | VPNv4 address family transport |
| 4360 | BGP Extended Communities | Route Target wire format |
| 7432 | BGP EVPN | Modern L3VPN without MPLS core |
| 4684 | Constrained Route Distribution | RT-based RR filtering |
| 4577 | OSPF as PE-CE | DN bit, sham link |
| 5880 | BFD | Fast failure detection |
| 4724 | BGP Graceful Restart | Control plane resilience |
| 8402 | Segment Routing | Modern MPLS transport layer |
| 5925 | TCP-AO | BGP session authentication |
| 5082 | GTSM | BGP session protection |

### Label Stack Summary

```
Ingress PE pushes:
  [Transport Label (LDP/SR)] [VPN Label (MP-BGP)] [IP Packet]
  outer, S=0                  inner, S=1

P router swaps outer label only. Never sees inner label or IP.

Penultimate P (PHP) pops outer label.

Egress PE receives [VPN Label] [IP Packet].
Looks up VPN label → VRF → IP FIB lookup → forwards to CE.
```

---

*Document version: comprehensive, covering RFC 4364, RFC 4760, RFC 4360,
RFC 7432, Linux kernel VRF (4.3+), FRR implementation patterns, eBPF/XDP
integration, and cloud-native relevance. All wire formats are bit-exact
per the referenced specifications.*