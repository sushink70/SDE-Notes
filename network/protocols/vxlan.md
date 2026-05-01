# VXLAN: Virtual eXtensible Local Area Network — Complete In-Depth Guide

> **Summary (4–8 lines):**  
> VXLAN (RFC 7348) is a MAC-in-UDP tunneling protocol that extends Layer-2 segments over Layer-3 underlay networks, solving the 4094-VLAN scalability wall in multi-tenant data centers by using a 24-bit VNI (16M+ segments). A VTEP (VXLAN Tunnel Endpoint) performs encapsulation/decapsulation, either in software (Linux kernel, Open vSwitch) or in hardware (ASIC offload). The control plane choices — flood-and-learn, head-end replication, or BGP EVPN (RFC 7432) — define scalability, ARP behavior, and operational model. BGP EVPN is the production-grade choice at scale, providing MAC/IP advertisement, ARP suppression, and multi-homing. Symmetric IRB with distributed anycast gateways enables optimal east-west routing without hairpinning. Security posture demands underlay isolation, VTEP authentication, encrypted overlays (IPsec/WireGuard per tunnel), and BUM traffic control. This guide covers every layer: wire format, kernel internals, BGP EVPN route types, IRB models, C and Rust VTEP implementations, threat model, and production operation.

---

## Table of Contents

1. [Motivation and Problem Space](#1-motivation-and-problem-space)
2. [VXLAN Fundamentals](#2-vxlan-fundamentals)
3. [RFC 7348 Protocol Specification](#3-rfc-7348-protocol-specification)
4. [Wire Format — Exact Packet Layout](#4-wire-format--exact-packet-layout)
5. [VTEP: VXLAN Tunnel Endpoint](#5-vtep-vxlan-tunnel-endpoint)
6. [Control Plane Models](#6-control-plane-models)
7. [BGP EVPN — RFC 7432 In Depth](#7-bgp-evpn--rfc-7432-in-depth)
8. [Data Plane: BUM Traffic, ARP Suppression, MAC Learning](#8-data-plane-bum-traffic-arp-suppression-mac-learning)
9. [Routing Models: Asymmetric vs Symmetric IRB](#9-routing-models-asymmetric-vs-symmetric-irb)
10. [Distributed Anycast Gateway](#10-distributed-anycast-gateway)
11. [VXLAN Gateway Types](#11-vxlan-gateway-types)
12. [Linux Kernel VXLAN Implementation](#12-linux-kernel-vxlan-implementation)
13. [Hardware Offload and ASIC Integration](#13-hardware-offload-and-asic-integration)
14. [C Implementation: Software VTEP](#14-c-implementation-software-vtep)
15. [Rust Implementation: Software VTEP](#15-rust-implementation-software-vtep)
16. [Underlay Network Design](#16-underlay-network-design)
17. [Threat Model and Security Design](#17-threat-model-and-security-design)
18. [Performance: Tuning, Benchmarks, Profiling](#18-performance-tuning-benchmarks-profiling)
19. [VXLAN in Kubernetes and CNI Context](#19-vxlan-in-kubernetes-and-cni-context)
20. [Operational Troubleshooting](#20-operational-troubleshooting)
21. [Failure Modes and Mitigations](#21-failure-modes-and-mitigations)
22. [Roll-out and Rollback Plan](#22-roll-out-and-rollback-plan)
23. [References](#23-references)
24. [Next 3 Steps](#24-next-3-steps)

---

## 1. Motivation and Problem Space

### 1.1 The Layer-2 Scaling Problem

Traditional data center networks used VLANs (IEEE 802.1Q) to segment tenants. IEEE 802.1Q supports a 12-bit VLAN ID → 4094 maximum VLANs. In hyperscale and multi-tenant clouds, this limit is hit almost immediately:

- A single cloud region may host tens of thousands of tenants
- Each tenant requires network isolation
- VMs and containers migrate between physical hosts while retaining their IP and MAC addresses
- Classic STP (Spanning Tree Protocol) does not scale across large L2 domains

### 1.2 The MAC Table Explosion Problem

In a large flat L2 network, every switch must learn every MAC address for every VM. With millions of VMs, MAC table sizes exceed the TCAM capacity of commodity switches. Spanning tree blocks redundant links. Broadcast domains become unwieldy. ARP storms on a large L2 segment can saturate switch control planes.

### 1.3 The VM Mobility Problem

When a VM live-migrates between physical hosts, it must retain its IP and MAC. If the underlay uses pure L3 routing, the VM's default gateway changes and connections break. If the underlay uses pure L2, STP reconvergence causes downtime.

### 1.4 What VXLAN Solves

VXLAN decouples the tenant overlay from the physical underlay:

```
Tenant Overlay (L2):     VM1 <—— Ethernet frames ——> VM2
                            [VNI 10001]
                         |                          |
                      VTEP-A                     VTEP-B
                         |                          |
Underlay (L3 IP/UDP):  10.0.0.1 ——UDP——> 10.0.0.2
                        [any routed path]
```

Key properties VXLAN provides:
- **24-bit VNI**: ~16.7 million unique overlay segments vs 4094 VLANs
- **IP underlay**: Any routed L3 network serves as transport; no STP, ECMP works naturally
- **MAC-in-UDP**: Standard UDP means existing load balancers, firewalls, and ECMP devices handle it without protocol knowledge
- **VM mobility**: Move a VM to any host; update VTEP→MAC mapping; VM retains IP/MAC
- **L2 or L3 gateway**: Can terminate at L2 (extend VLANs) or L3 (route between VNIs)

### 1.5 Predecessor Technologies Compared

| Technology | Segment Limit | Underlay | Notes |
|---|---|---|---|
| VLAN (802.1Q) | 4,094 | L2 switch | STP dependent |
| QinQ (802.1ad) | 4,094 × 4,094 | L2 switch | Still STP, complex |
| MPLS L2VPN | Millions (label) | L3 MPLS | Requires MPLS-capable hardware |
| NVGRE | 24-bit VSID | L3 IP/GRE | GRE breaks ECMP (no src port entropy) |
| STT | 64-bit Context ID | L3 TCP-like | TCP framing, stateful, complex |
| **VXLAN** | **~16.7 million VNI** | **L3 IP/UDP** | **UDP → ECMP, simple, widely implemented** |
| Geneve | Variable metadata | L3 IP/UDP | Extensible, replacing VXLAN |

---

## 2. VXLAN Fundamentals

### 2.1 Core Concepts

**VNI (VXLAN Network Identifier):**
A 24-bit integer uniquely identifying an overlay segment. All VTEPs that belong to the same VNI participate in the same L2 broadcast domain. VNI 0 is reserved. VNI is analogous to VLAN ID but in 24-bit space.

**VTEP (VXLAN Tunnel Endpoint):**
Any network entity that encapsulates or decapsulates VXLAN frames. A VTEP has:
- An underlay IP address (the VTEP IP, used as outer IP src/dst)
- A set of VNIs it participates in
- A forwarding database (FDB) mapping {VNI, inner-MAC} → outer-VTEP-IP

**Inner Frame:**
The original Ethernet frame from the tenant (VM, container), including inner Ethernet header, inner IP header, inner payload.

**Outer Frame:**
The VXLAN-encapsulated packet: outer Ethernet + outer IP + outer UDP + VXLAN header + inner Ethernet frame.

**Overlay Network:**
The logical L2 (or L3) network formed by VTEPs that share VNIs. Tenant VMs see a flat L2 broadcast domain regardless of physical topology.

**Underlay Network:**
The physical routed IP network interconnecting VTEPs. Can be any IP network: data center fabric, WAN, Internet. VTEPs communicate using standard UDP/IP.

### 2.2 Fundamental Operational Principle

```
VM-A (MAC: aa:bb, IP: 10.1.0.1) on Host-1 (VTEP IP: 192.168.1.1)
  sends Ethernet frame to
VM-B (MAC: cc:dd, IP: 10.1.0.2) on Host-2 (VTEP IP: 192.168.1.2)

Step 1: VM-A sends normal Ethernet frame (aa:bb → cc:dd)
Step 2: Host-1 VTEP intercepts frame (tun/tap, kernel, OVS)
Step 3: VTEP looks up: {VNI=10001, dst-MAC=cc:dd} → VTEP-IP=192.168.1.2
Step 4: VTEP encapsulates: adds VXLAN hdr, UDP hdr, IP hdr, Eth hdr
Step 5: Sends UDP packet 192.168.1.1:sport → 192.168.1.2:4789
Step 6: Host-2 VTEP receives on UDP:4789, strips outer headers
Step 7: VTEP delivers inner Ethernet frame to VM-B's virtual NIC
Step 8: VM-B receives original Ethernet frame — identical to non-tunneled
```

### 2.3 IANA and Standards

- **RFC 7348**: VXLAN specification (August 2014)
- **RFC 7432**: BGP MPLS-Based Ethernet VPN (EVPN) — control plane for VXLAN
- **RFC 8365**: A Network Virtualization Overlay Solution Using Ethernet VPN (EVPN)
- **UDP Destination Port**: 4789 (IANA assigned; original implementations used 8472, still seen in Linux default)
- **Linux default**: Port 8472 (historical, pre-IANA assignment) — explicitly set 4789 in production

---

## 3. RFC 7348 Protocol Specification

### 3.1 Architecture Overview

RFC 7348 defines VXLAN as a simple encapsulation protocol with minimal control plane. The spec intentionally leaves the control plane open, allowing implementations to use multicast, static config, or distributed control protocols.

```
                      RFC 7348 VXLAN Architecture

  +-----------+         +-----------+         +-----------+
  |  Tenant   |         |  VXLAN    |         |  Tenant   |
  |  VM / Pod |         |  Overlay  |         |  VM / Pod |
  +-----+-----+         |  Segment  |         +-----+-----+
        |               +-----------+               |
        | (inner frame)                             | (inner frame)
  +-----+-----+                             +-------+-----+
  |   VTEP-A  |<====== UDP/IP underlay =====>|   VTEP-B  |
  | 192.168.1 |                             | 192.168.1.2 |
  +-----+-----+                             +-----+-------+
        |                                         |
  +-----+-----+                             +-----+-----+
  | Underlay  |                             | Underlay  |
  | NIC/Bond  |                             | NIC/Bond  |
  +-----------+                             +-----------+
```

### 3.2 RFC Requirements

From RFC 7348, the key mandates:

1. **Encapsulation**: Inner Ethernet frame (including FCS optional) wrapped in VXLAN+UDP+IP+Ethernet
2. **Destination UDP port**: 4789 (IANA; Linux historically 8472)
3. **VNI**: 24-bit in VXLAN header, carried in every packet
4. **Source UDP port**: SHOULD be selected to maximize ECMP entropy (hash of inner headers)
5. **TTL**: Outer IP TTL SHOULD be set to 255 (or a configurable value ≥ 1)
6. **IP checksum**: Outer UDP checksum SHOULD be set to zero (IPv4); MUST be handled for IPv6
7. **MTU**: Outer packet adds 50 bytes overhead (IPv4) or 70 bytes (IPv6); underlay MTU must accommodate
8. **VTEP**: Must participate in ARP/neighbor discovery for inner addresses
9. **Multicast**: Used for BUM (Broadcast, Unknown unicast, Multicast) traffic delivery in basic mode
10. **FDB**: VTEP maintains a forwarding database of {MAC, VNI} → VTEP-IP

### 3.3 MTU Considerations

```
Inner Ethernet frame (standard):
  Inner Eth header: 14 bytes (src+dst MAC + EtherType)
  Inner IP header:  20 bytes (IPv4) or 40 bytes (IPv6)
  Inner payload:    up to 1460 bytes (TCP with 1500 MTU path)

VXLAN overhead (IPv4 underlay):
  Outer Ethernet:   14 bytes
  Outer IPv4:       20 bytes
  Outer UDP:         8 bytes
  VXLAN header:      8 bytes
  Total overhead:   50 bytes

For tenant to use 1500 byte MTU:
  Underlay MTU must be: 1500 + 50 = 1550 bytes
  Recommended underlay MTU: 9000 (jumbo frames) for headroom
  Or: set tenant MTU to 1450 (1500 - 50) if underlay is 1500

IPv6 underlay overhead:
  Outer Ethernet:   14 bytes
  Outer IPv6:       40 bytes
  Outer UDP:         8 bytes
  VXLAN header:      8 bytes
  Total overhead:   70 bytes
```

---

## 4. Wire Format — Exact Packet Layout

### 4.1 Complete VXLAN Packet (IPv4 Underlay)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  <- byte 0
|                                                               |     OUTER
|              Outer Destination MAC Address (6 bytes)          |     ETHERNET
|                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  HEADER
|                               |                               |   (14 bytes)
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|              Outer Source MAC Address (6 bytes)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       EtherType (0x0800 IPv4 / 0x86DD IPv6)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  <- byte 14
|Version|  IHL  |Type of Service|          Total Length         |     OUTER
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+     IPv4
|         Identification        |Flags|      Fragment Offset    |     HEADER
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+   (20 bytes)
|  Time to Live |Protocol=0x11  |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source IP (VTEP-A)                      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination IP (VTEP-B)                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  <- byte 34
|     Source Port (entropy)     |  Dest Port = 4789 (0x12B5)   |     OUTER
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+     UDP
|          UDP Length           |        UDP Checksum=0         |     HEADER
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+   (8 bytes)
|R|R|R|R|I|R|R|R|               Reserved                       |  <- byte 42
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+     VXLAN
|                    VNI (24 bits)              |   Reserved    |     HEADER
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+   (8 bytes)
|                                                               |  <- byte 50
|              Inner Destination MAC Address (6 bytes)          |     INNER
|                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+     ETHERNET
|                               |                               |     FRAME
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |     (variable)
|              Inner Source MAC Address (6 bytes)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   Inner EtherType (0x0800)    |  Inner IPv4 Version+IHL+TOS  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Inner IPv4 Total Length                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             Inner IPv4 ID     |Flags+Fragment Offset          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Inner TTL    | Inner Proto   |    Inner IPv4 Header Checksum |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Inner Source IP Address                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Inner Destination IP Address                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Inner TCP/UDP/ICMP Payload                 |
|                    (variable length)                          |
|  [optional inner FCS — 4 bytes if included]                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 4.2 VXLAN Header Detail

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|R|R|R|R|I|R|R|R|              Reserved (24 bits)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       VNI (24 bits)                           |  Reserved (8) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  ^         ^
  |         |
  bit 3     bit 4 = I-flag
  (MSB=0)   (MUST be 1 for valid VNI)

Byte 0:  Flags = 0x08 (bit 4 set → I flag = VNI valid)
         Bits 7,6,5: Reserved = 0
         Bit 4: I = 1 (VXLAN Network Identifier is valid)
         Bits 3,2,1,0: Reserved = 0
Bytes 1-3: Reserved = 0x000000
Bytes 4-6: VNI (24-bit, network byte order)
Byte 7:    Reserved = 0x00

Example (VNI = 10001 = 0x002711):
  Byte 0: 0x08
  Byte 1: 0x00
  Byte 2: 0x00
  Byte 3: 0x00
  Byte 4: 0x00
  Byte 5: 0x27
  Byte 6: 0x11
  Byte 7: 0x00
```

### 4.3 VXLAN-GPE (Generic Protocol Extension) Header

RFC 8926 extends VXLAN with a Next Protocol field:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|R|R|Ver|I|P|B|O|    Reserved   |          Reserved             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         VNI (24 bits)                         |Next Protocol  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  I = VNI valid; P = Next Protocol valid; B = BUM packet
  O = OAM; Ver = version (MUST = 0)

Next Protocol values:
  0x01 = IPv4
  0x02 = IPv6
  0x03 = Ethernet (standard VXLAN inner)
  0x04 = NSH (Network Service Header)
  0x05 = MPLS
```

### 4.4 Outer UDP Source Port — Entropy Field

The outer source port is not a real port number in the traditional sense. RFC 7348 specifies it SHOULD be computed as a hash of the inner frame headers to provide entropy for ECMP load balancing:

```
Source Port = hash(inner_src_ip, inner_dst_ip, inner_src_port, inner_dst_port, proto)
            = typically a 16-bit value in range [49152, 65535] (ephemeral range)
            OR range [1024, 65535]

Why this matters for ECMP:
  Without entropy: All VXLAN flows between two VTEPs use same src/dst IP → same ECMP hash
                   → All traffic goes to ONE uplink → No load balancing

  With entropy:    Different inner flows get different src ports → different ECMP hashes
                   → Traffic distributed across all uplinks → Full bandwidth utilization

ECMP hash key (typically):
  Outer SrcIP + DstIP + SrcPort(entropy) + DstPort(4789) + Protocol(UDP=17)
  → Different flows → different src port → different uplinks chosen
```

### 4.5 Byte-Level Example: Minimal VXLAN Packet

```
Scenario: ARP Request from VM (10.1.0.1, MAC aa:aa:aa:11:22:33) on VTEP-A (192.168.10.1)
          to broadcast, VNI = 100 (0x000064)
          VTEP-B is at 239.1.1.1 (multicast) or unicast peer

Outer Ethernet (14 bytes):
  00 50 56 a1 b2 c3      <- Outer DST MAC (VTEP-B's router MAC or next-hop)
  00 50 56 a1 b2 c4      <- Outer SRC MAC (VTEP-A's interface MAC)
  08 00                  <- EtherType = IPv4

Outer IPv4 (20 bytes):
  45                     <- Version=4, IHL=5
  00                     <- DSCP/ECN=0
  00 5e                  <- Total Length = 94 bytes
  00 00                  <- Identification
  40 00                  <- DF=1, Fragment Offset=0
  40                     <- TTL=64
  11                     <- Protocol=17 (UDP)
  xx xx                  <- Header Checksum (computed)
  c0 a8 0a 01            <- Src IP = 192.168.10.1 (VTEP-A)
  ef 01 01 01            <- Dst IP = 239.1.1.1 (multicast for BUM)

Outer UDP (8 bytes):
  c3 52                  <- Src Port = 50002 (entropy hash)
  12 b5                  <- Dst Port = 4789 (0x12B5, VXLAN)
  00 4a                  <- UDP Length = 74
  00 00                  <- Checksum = 0

VXLAN Header (8 bytes):
  08 00 00 00            <- Flags: I=1, Reserved=0
  00 00 64 00            <- VNI = 100 (0x000064), Reserved=0

Inner Ethernet + ARP (28 bytes):
  ff ff ff ff ff ff      <- Inner DST MAC = broadcast
  aa aa aa 11 22 33      <- Inner SRC MAC = VM's MAC
  08 06                  <- EtherType = ARP
  00 01                  <- Hardware Type = Ethernet
  08 00                  <- Protocol Type = IPv4
  06                     <- Hardware Size = 6
  04                     <- Protocol Size = 4
  00 01                  <- Opcode = Request
  aa aa aa 11 22 33      <- Sender MAC
  0a 01 00 01            <- Sender IP = 10.1.0.1
  00 00 00 00 00 00      <- Target MAC = unknown
  0a 01 00 02            <- Target IP = 10.1.0.2
```

---

## 5. VTEP: VXLAN Tunnel Endpoint

### 5.1 VTEP Architecture

A VTEP is the fundamental building block of VXLAN. Every host, switch, or appliance that participates in VXLAN operates as a VTEP.

```
                        VTEP Internal Architecture
  ┌──────────────────────────────────────────────────────────────┐
  │                          VTEP                                │
  │                                                              │
  │  ┌─────────────────────────────────────────────────────┐    │
  │  │                  FDB (Forwarding DB)                 │    │
  │  │   {VNI=100, MAC=aa:bb} → VTEP-IP=10.0.0.2           │    │
  │  │   {VNI=100, MAC=cc:dd} → VTEP-IP=10.0.0.3           │    │
  │  │   {VNI=200, MAC=ee:ff} → VTEP-IP=10.0.0.4           │    │
  │  │   {VNI=100, MAC=*}     → multicast 239.1.1.1 (BUM)  │    │
  │  └─────────────────────────────────────────────────────┘    │
  │                            │                                 │
  │  ┌───────────────┐   ┌─────┴──────┐   ┌───────────────┐    │
  │  │  Encapsulator │   │   VNI      │   │  Decapsulator │    │
  │  │               │   │  Mapping   │   │               │    │
  │  │ inner→outer   │   │  Table     │   │ outer→inner   │    │
  │  │ add UDP/IP/Eth│   │ ifindex↔VNI│   │ strip headers │    │
  │  └───────┬───────┘   └─────┬──────┘   └───────┬───────┘    │
  │          │                 │                   │             │
  │  ┌───────┴─────────────────┴───────────────────┴───────┐    │
  │  │              Local MAC/ARP Cache                     │    │
  │  │   {VNI=100, IP=10.1.0.1} → MAC=aa:bb (local VM)     │    │
  │  └──────────────────────────────────────────────────────┘    │
  │                                                              │
  │   ┌──────────────────────┐    ┌────────────────────────┐    │
  │   │   Overlay Interfaces │    │   Underlay Interface    │    │
  │   │   vxlan100, vxlan200 │    │   eth0 (IP: 10.0.0.1)  │    │
  │   └──────────────────────┘    └────────────────────────┘    │
  └──────────────────────────────────────────────────────────────┘
                │                              │
         [to VMs/Pods]                 [to IP network]
```

### 5.2 VTEP Identification

Each VTEP is identified by its **VTEP IP** — the IP address of its underlay interface (or a loopback IP). This is the outer source/destination IP in encapsulated packets.

In production:
- Use a **loopback IP** as VTEP IP (not tied to a specific physical interface)
- Loopback IP is advertised via underlay routing (BGP, OSPF) → reachable from any uplink
- Loopback survives physical link failures if underlay reroutes

```
# Linux: Set up VTEP using loopback
ip link add lo0 type dummy
ip addr add 10.0.0.1/32 dev lo0
ip link set lo0 up
# Advertise 10.0.0.1/32 via underlay BGP
```

### 5.3 VTEP FDB (Forwarding Database)

The FDB is the VTEP's equivalent of a switch MAC table, extended with VNI:

```
Key:   {VNI, inner-MAC}
Value: {remote-VTEP-IP, flags}

Special entries:
  {VNI, FF:FF:FF:FF:FF:FF} → multicast-IP or unicast-list  (BUM flooding)
  {VNI, 00:00:00:00:00:00} → default → use BUM mechanism

Linux FDB example:
  bridge fdb show dev vxlan100
  aa:bb:cc:11:22:33 dev vxlan100 dst 10.0.0.2 self permanent
  00:00:00:00:00:00 dev vxlan100 dst 239.1.1.100 self permanent  ← BUM
  ff:ff:ff:ff:ff:ff dev vxlan100 dst 239.1.1.100 self permanent  ← broadcast
```

### 5.4 VTEP Realization Options

**Software VTEP (Linux kernel):**
- `ip link add vxlan100 type vxlan id 100 dstport 4789 ...`
- Handled in net/vxlan.c kernel module
- Performance: ~5-10 Gbps per core without offload

**Open vSwitch (OVS) VTEP:**
- Used in OpenStack, VMware, older Kubernetes CNI
- OVSDB protocol for control; dpdk-enabled for performance
- Supports flow-based encap with classifier

**Hardware VTEP (ToR Switch, SmartNIC):**
- ASIC-offloaded encapsulation at line rate (100 Gbps+)
- Managed via OVSDB Hardware VTEP schema or vendor API
- Mellanox/NVIDIA, Broadcom Tomahawk, Cisco Nexus 9k

**SmartNIC/DPU VTEP:**
- NVIDIA BlueField, Intel IPU: offloads VXLAN from host CPU
- Host OS sees native Ethernet; DPU performs encap/decap
- Host CPU free for application workloads

---

## 6. Control Plane Models

The control plane determines how VTEPs learn: which MAC addresses are behind which remote VTEPs.

### 6.1 Flood-and-Learn (Multicast-based)

The original RFC 7348 method. Uses IP multicast for BUM (Broadcast, Unknown unicast, Multicast) traffic.

```
              Flood-and-Learn with Multicast

VTEP-A             IP Multicast            VTEP-B    VTEP-C
  |                 (239.1.1.1)              |         |
  |--- ARP Req ---> [multicast group] ------->|-------->|
  |                                           |         |
  |                                    VTEP-B and VTEP-C
  |                                    both receive it,
  |                                    both learn:
  |                                    {VNI=100, MAC=vm-a-mac} → VTEP-A
  |
  |<------------- ARP Reply (unicast) ---------| 
  |                                            |
  VTEP-A learns: {VNI=100, MAC=vm-b-mac} → VTEP-B

State learned from data plane:
  - No separate control plane protocol needed
  - Requires PIM multicast in underlay
  - Each VNI maps to a multicast group
  - BUM traffic hits ALL VTEPs in the multicast group
  - Scales poorly: O(N) BUM for N VTEPs
```

**Multicast group assignment:**
- One multicast group per VNI: 239.x.x.x per VNI (precise isolation)
- Multiple VNIs per multicast group: more scalable, some cross-VNI BUM flooding
- One multicast group for all VNIs: simplest, worst isolation

**Requirements:**
- PIM-SM or PIM-SSM in underlay
- IGMP snooping on switches
- Rendezvous Points (RP) for PIM-SM

**Pros:** Simple, no control plane software  
**Cons:** Requires multicast underlay (often disabled in DCs), BUM flooding scales as O(N), all VTEPs receive all BUM for shared groups

### 6.2 Ingress Replication (Head-End Replication)

Eliminates multicast requirement. VTEP maintains a list of all remote VTEPs per VNI and replicates BUM traffic as N unicast copies.

```
              Head-End Replication (Unicast)

  For VNI 100, VTEP-A knows: [VTEP-B=10.0.0.2, VTEP-C=10.0.0.3, VTEP-D=10.0.0.4]

  BUM Frame arrives from local VM:
  VTEP-A makes 3 copies:
    Copy 1 → encapsulate → send to 10.0.0.2 (VTEP-B)
    Copy 2 → encapsulate → send to 10.0.0.3 (VTEP-C)
    Copy 3 → encapsulate → send to 10.0.0.4 (VTEP-D)

  No multicast needed in underlay.
  MAC learning still happens from data plane (flood → learn).
  VTEP list is statically configured or learned from BGP EVPN.
```

**Config (Linux static):**
```bash
ip link add vxlan100 type vxlan id 100 dstport 4789 local 10.0.0.1 nolearning
# Add each remote VTEP for flooding
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.2
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.3
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.4
```

**Pros:** No multicast; works on pure L3 underlay  
**Cons:** BUM replication load on ingress VTEP; VTEP list must be maintained; still floods unknown unicast

### 6.3 BGP EVPN Control Plane (Production Standard)

BGP EVPN (RFC 7432 + RFC 8365) is the production-grade control plane. VTEPs use BGP to advertise MAC/IP routes, eliminating flooding for known unicast and enabling ARP suppression.

```
                BGP EVPN Control Plane

  ┌─────────┐   BGP UPDATE   ┌─────────────┐   BGP UPDATE  ┌─────────┐
  │ VTEP-A  │ <----------->  │ Route       │ <-----------> │ VTEP-B  │
  │Leafswitch│               │ Reflector   │               │Leafswitch│
  └────┬────┘               │ (RR/Spine)  │               └────┬────┘
       |                    └─────────────┘                    |
  [VM-A learns]                                          [VM-B learns]
  VTEP-A advertises:                                    VTEP-B advertises:
  EVPN Type-2: {VNI=100, MAC=vm-a-mac, IP=10.1.0.1}    EVPN Type-2: {VNI=100, MAC=vm-b-mac}

  VTEP-B receives Type-2 from VTEP-A:
    Installs FDB: {VNI=100, vm-a-mac} → VTEP-A
    Installs ARP: {VNI=100, 10.1.0.1} → vm-a-mac (ARP suppression)
  
  When VM-B ARPs for 10.1.0.1:
    VTEP-B responds locally! (ARP proxy) — no flooding needed
    VTEP-B responds: "10.1.0.1 is at vm-a-mac"
```

---

## 7. BGP EVPN — RFC 7432 In Depth

### 7.1 EVPN Overview

EVPN (Ethernet VPN) is an address family in BGP (AFI=25, SAFI=70). It carries Ethernet MAC/IP reachability information as BGP routes. Originally designed for MPLS-based Ethernet VPNs (RFC 7432), it was extended for VXLAN overlays (RFC 8365).

Key NLRI (Network Layer Reachability Information) types:

```
EVPN Route Types:
  Type 1: Ethernet Auto-discovery (A-D) Route
  Type 2: MAC/IP Advertisement Route  ← most important for VXLAN
  Type 3: Inclusive Multicast Ethernet Tag (IMET) Route  ← BUM tree
  Type 4: Ethernet Segment Route
  Type 5: IP Prefix Route  ← L3 VXLAN routing
```

### 7.2 BGP EVPN Session Architecture

```
                    BGP EVPN Topology (Spine-Leaf)

        ┌─────────────────────────────────────────┐
        │             Route Reflectors             │
        │         (Spine-1 and Spine-2)            │
        │   eBGP or iBGP with EVPN AF              │
        └───────┬──────────────┬───────────────────┘
                │ iBGP         │ iBGP
        ┌───────┴────┐    ┌────┴────────┐
        │  Leaf-1    │    │   Leaf-2    │
        │ (VTEP-A)   │    │  (VTEP-B)  │
        │ AS 65001   │    │  AS 65001  │
        └────────────┘    └────────────┘
             │                   │
         [VM-A]              [VM-B]

BGP sessions carry:
  AFI=25, SAFI=70 (EVPN)
  Extended Communities: Route Target, Encapsulation Type=VXLAN

Route Target convention:
  VNI 100  → RT: 65001:100
  VNI 200  → RT: 65001:200
  L3 VNI   → RT: 65001:50000 (L3 routing VRF)
```

### 7.3 EVPN Route Type 2: MAC/IP Advertisement

This is the workhorse of VXLAN BGP EVPN. Every VTEP advertises the MAC addresses (and optionally IP addresses) of locally attached VMs.

```
EVPN Type-2 Route (MAC/IP Advertisement):
┌────────────────────────────────────────────────────────────────┐
│  Route Distinguisher (8 bytes)                                 │
│    Format: VTEP-IP:VNI (e.g., 10.0.0.1:100)                  │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Segment Identifier (ESI, 10 bytes)                   │
│    For single-homed VTEP: 00:00:00:00:00:00:00:00:00:00       │
│    For multi-homed: system-id based value                      │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Tag ID (4 bytes)                                     │
│    For VXLAN: 0 (VNI carried separately)                       │
├────────────────────────────────────────────────────────────────┤
│  MAC Address Length (1 byte) = 48                              │
├────────────────────────────────────────────────────────────────┤
│  MAC Address (6 bytes) = VM's MAC                              │
├────────────────────────────────────────────────────────────────┤
│  IP Address Length (1 byte) = 0 (MAC-only) or 32/128          │
├────────────────────────────────────────────────────────────────┤
│  IP Address (4 or 16 bytes) = VM's IP (for ARP suppression)   │
├────────────────────────────────────────────────────────────────┤
│  MPLS Label 1 (3 bytes) = VNI (encoded as MPLS label format)  │
│    VNI=100 → Label = 100 << 4 = 0x640 (with BoS=1)           │
├────────────────────────────────────────────────────────────────┤
│  MPLS Label 2 (3 bytes) = L3 VNI (for symmetric IRB)          │
│    Optional, for inter-VNI routing                             │
└────────────────────────────────────────────────────────────────┘

BGP Extended Communities attached:
  Route Target: 65001:100        (import/export policy)
  Encapsulation: VXLAN (0x030c)  (tunnel type = 8)
  Router MAC: aa:bb:cc:11:22:33  (for L3 routing, VTEP's MAC)
```

### 7.4 EVPN Route Type 3: IMET (Inclusive Multicast Ethernet Tag)

Type-3 routes advertise how a VTEP handles BUM traffic for a given VNI. This replaces static VTEP lists for ingress replication.

```
EVPN Type-3 Route (IMET):
┌────────────────────────────────────────────────────────────────┐
│  Route Distinguisher (8 bytes): VTEP-IP:VNI                   │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Tag ID (4 bytes) = 0                                 │
├────────────────────────────────────────────────────────────────┤
│  IP Address Length = 32 (IPv4) or 128 (IPv6)                   │
├────────────────────────────────────────────────────────────────┤
│  Originating Router's IP Address = VTEP-IP                     │
└────────────────────────────────────────────────────────────────┘

PMSI Tunnel Attribute:
  Flags: Leaf Information Required = 0
  Tunnel Type: 6 (Ingress Replication)
  MPLS Label: VNI
  Tunnel Endpoint: VTEP-IP

Effect:
  Every VTEP in VNI 100 receives Type-3 routes from all other VTEPs.
  Each VTEP builds its BUM replication list from received Type-3 routes.
  No static configuration needed for new VTEPs in the VNI.
```

### 7.5 EVPN Route Type 5: IP Prefix Route

Used for L3 VXLAN (routing between VNIs). Advertises IP prefixes reachable via a VTEP.

```
EVPN Type-5 Route (IP Prefix):
┌────────────────────────────────────────────────────────────────┐
│  Route Distinguisher (8 bytes)                                 │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Segment Identifier (10 bytes) = 0                    │
├────────────────────────────────────────────────────────────────┤
│  Ethernet Tag ID (4 bytes) = 0                                 │
├────────────────────────────────────────────────────────────────┤
│  IP Prefix Length (1 byte)                                     │
├────────────────────────────────────────────────────────────────┤
│  IP Prefix (4 or 16 bytes)                                     │
├────────────────────────────────────────────────────────────────┤
│  Gateway IP Address (4 or 16 bytes)                            │
├────────────────────────────────────────────────────────────────┤
│  MPLS Label (3 bytes) = L3 VNI                                 │
└────────────────────────────────────────────────────────────────┘

Use cases:
  - Advertise VM subnet prefixes (e.g., 10.1.0.0/24) into BGP
  - Route between VNIs via L3 VNI
  - Connect to external networks (WAN, Internet) via BGP
  - DC gateway routes (external prefixes → overlay VMs)
```

### 7.6 EVPN Route Type 1: Ethernet Auto-discovery

Used primarily for multi-homing (EVPN-MH or EVPN-LAG). Signals ESI reachability and enables fast convergence.

```
Type-1 Per-ESI route: advertised by each PE attached to a multihomed CE
  → Used for mass MAC withdrawal on link failure
  
Type-1 Per-EVI route: per ESI per EVPN instance
  → Carries MPLS label for split-horizon filtering
  → Enables Aliasing (load balancing to multi-homed CE)
```

### 7.7 BGP EVPN with FRRouting

FRRouting (FRR) is the most common open-source BGP EVPN implementation:

```
# /etc/frr/frr.conf (Leaf/VTEP node)

frr defaults datacenter
hostname leaf-1

ip route 0.0.0.0/0 Null0  # blackhole for safety

interface lo
  ip address 10.0.0.1/32   # VTEP loopback

interface eth0
  ip address 192.168.1.1/30  # underlay uplink to spine

router bgp 65001
  bgp router-id 10.0.0.1
  no bgp ebgp-requires-policy
  
  neighbor 192.168.1.2 remote-as 65000  # spine peer
  neighbor 192.168.1.2 description SPINE-1
  neighbor 192.168.1.2 bfd
  
  address-family ipv4 unicast
    neighbor 192.168.1.2 activate
    redistribute connected route-map LOOPBACK-ONLY
  exit-address-family
  
  address-family l2vpn evpn
    neighbor 192.168.1.2 activate
    neighbor 192.168.1.2 send-community extended
    advertise-all-vni
    advertise-svi-ip      # advertise VTEP SVI IPs as Type-2
  exit-address-family

# VNI to VRF mapping
vrf TENANT-A
  vni 50001        # L3 VNI for symmetric IRB

router bgp 65001 vrf TENANT-A
  address-family ipv4 unicast
    redistribute connected
    import vpn
    export vpn
    rd vpn export 10.0.0.1:50001
    rt vpn both 65001:50001
  exit-address-family
  address-family l2vpn evpn
    advertise ipv4 unicast
  exit-address-family

# VNI definitions (maps to bridge/vxlan interfaces)
# Done via zebra/kernel, not here
```

---

## 8. Data Plane: BUM Traffic, ARP Suppression, MAC Learning

### 8.1 BUM Traffic Definition

BUM = **B**roadcast, **U**nknown unicast, **M**ulticast

- **Broadcast**: ARP requests, DHCP discovers, spanning-tree BPDUs
- **Unknown unicast**: Frames to MACs not in the VTEP's FDB
- **Multicast**: Application multicast, router solicitations

BUM traffic is the primary scaling challenge in VXLAN networks. Every BUM frame must be delivered to all VTEPs in the VNI.

```
BUM Delivery Methods (in order of maturity):
  1. IP Multicast (RFC 7348 default)
     VTEP → multicast group → all VTEPs in group
     Requires PIM in underlay; cheap but requires multicast support

  2. Head-End Replication (Ingress Replication)
     VTEP → N unicast copies → each remote VTEP
     No multicast; CPU intensive on sending VTEP
     VTEP list from static config or BGP EVPN Type-3

  3. ARP Suppression + BGP EVPN (eliminates most BUM)
     Known IP → respond locally; unknown → flood
     BUM reduced to: new VMs (before learning), true broadcasts
     Production standard: >95% BUM eliminated
```

### 8.2 ARP Suppression

With BGP EVPN Type-2 routes carrying MAC+IP, the local VTEP can answer ARP requests on behalf of remote VMs without flooding.

```
Without ARP Suppression:
  VM-B ARPs: "Who has 10.1.0.1?"
  VTEP-B floods to all VTEPs in VNI 100
  VTEP-A delivers to VM-A
  VM-A replies: "10.1.0.1 is at aa:bb:cc:11:22:33"
  VTEP-A sends unicast reply back
  2x underlay traffic per ARP

With ARP Suppression:
  VTEP-A received Type-2 route: {VNI=100, IP=10.1.0.1, MAC=aa:bb}
  VTEP-B received this route and installed ARP entry:
    10.1.0.1 → aa:bb:cc:11:22:33 (VTEP-A proxy entry)
  
  VM-B ARPs: "Who has 10.1.0.1?"
  VTEP-B intercepts ARP request
  VTEP-B checks local ARP suppression table
  VTEP-B generates ARP reply: "10.1.0.1 is at aa:bb:cc:11:22:33"
  VTEP-B delivers reply directly to VM-B
  Zero underlay traffic! No flooding!

Linux kernel ARP suppression:
  ip link add vxlan100 type vxlan id 100 ... proxy arp_proxy
  # 'proxy' enables ARP proxy mode
  # FDB entries with neigh_suppress flag handle this
```

### 8.3 MAC Learning Modes

**Data-plane learning (flood-and-learn):**
```
When VTEP-B receives a VXLAN packet from VTEP-A:
  outer src IP = VTEP-A's IP
  inner src MAC = VM-A's MAC
  VNI = 100
  VTEP-B installs: {VNI=100, MAC=VM-A-MAC} → VTEP-A
  (Same as traditional switch MAC learning, but in VTEP FDB)
```

**Control-plane learning (BGP EVPN):**
```
VTEP-A locally learns VM-A's MAC (when VM-A sends its first frame)
VTEP-A advertises BGP EVPN Type-2: {VNI=100, MAC=VM-A-MAC, IP=VM-A-IP}
All other VTEPs install FDB entry without seeing any data traffic
Advantage: No flooding of unknown unicast required
```

**Linux kernel data-plane learning:**
```bash
# Learning enabled (default): VTEP learns MACs from received packets
ip link add vxlan100 type vxlan id 100 dstport 4789 \
    local 10.0.0.1 learning

# Learning disabled (for BGP EVPN control plane):
ip link add vxlan100 type vxlan id 100 dstport 4789 \
    local 10.0.0.1 nolearning
# FDB entries added by BGP daemon (FRR/bird)
```

### 8.4 VXLAN FDB Operations

```bash
# Show VXLAN FDB
bridge fdb show dev vxlan100

# Add static FDB entry (unicast MAC)
bridge fdb add aa:bb:cc:11:22:33 dev vxlan100 dst 10.0.0.2 vni 100 self permanent

# Add BUM flooding entry (head-end replication)
bridge fdb append 00:00:00:00:00:00 dev vxlan100 dst 10.0.0.2 self permanent

# Delete FDB entry  
bridge fdb del aa:bb:cc:11:22:33 dev vxlan100 dst 10.0.0.2

# Linux kernel FDB (in netlink format) - what BGP daemons use:
# ip neigh add 10.1.0.1 lladdr aa:bb:cc:11:22:33 dev vxlan100 nud permanent
# (for ARP suppression table)
```

---

## 9. Routing Models: Asymmetric vs Symmetric IRB

IRB = **I**ntegrated **R**outing and **B**ridging — the ability to both bridge (L2) within a VNI and route (L3) between VNIs.

### 9.1 Asymmetric IRB

In asymmetric IRB, routing happens at the **ingress** VTEP only. The egress VTEP only bridges (L2 delivery into the destination VNI).

```
              Asymmetric IRB

  VNI-100: 10.1.0.0/24     VNI-200: 10.2.0.0/24
  VM-A: 10.1.0.1            VM-B: 10.2.0.1
    │                            │
  VTEP-A                       VTEP-B
  (has VNI-100 AND VNI-200)   (has VNI-100 AND VNI-200)

  Traffic: VM-A (VNI-100) → VM-B (VNI-200)

  Step 1: VM-A sends frame to default GW (VTEP-A's IRB interface for VNI-100)
  Step 2: VTEP-A routes: 10.2.0.0/24 is in VNI-200
  Step 3: VTEP-A looks up VM-B's MAC in VNI-200 FDB
          → VTEP-A must have VM-B's MAC in its VNI-200 FDB
  Step 4: VTEP-A encapsulates with VNI=200 (destination VNI!)
          outer: VTEP-A → VTEP-B
          inner: VTEP-A-MAC → VM-B-MAC (L3 routed inner MACs)
          VNI=200 (egress VTEP bridges into VNI-200)
  Step 5: VTEP-B receives VNI-200 packet, bridges to VM-B

  Return path: symmetric
  VM-B → VTEP-B routes in VNI-100 → sends VNI=100 to VTEP-A
  VTEP-A bridges to VM-A

Characteristics:
  + No dedicated L3 VNI needed
  + Simple, less VNI state
  - EVERY VTEP must have ALL VNIs (for both src and dst)
  - Does not scale with many VNIs
  - Every leaf must be in every VNI even if no local VMs exist
  - ARP suppression must work across VNIs
```

### 9.2 Symmetric IRB

In symmetric IRB, routing happens at BOTH ingress AND egress VTEPs, through a dedicated **L3 VNI** (also called transit VNI or routing VNI).

```
              Symmetric IRB

  VNI-100: 10.1.0.0/24     L3VNI-5000: (routing)   VNI-200: 10.2.0.0/24
  VM-A: 10.1.0.1                                     VM-B: 10.2.0.1
    │                                                      │
  VTEP-A                                               VTEP-B
  (has VNI-100, L3VNI-5000)                           (has VNI-200, L3VNI-5000)

  Traffic: VM-A (VNI-100) → VM-B (VNI-200)

  Step 1: VM-A sends frame to default GW (VTEP-A's SVI for VNI-100)
  Step 2: VTEP-A routes: 10.2.0.0/24 via BGP EVPN Type-5 → next-hop=VTEP-B
  Step 3: VTEP-A encapsulates with L3VNI=5000 (NOT VNI-200!)
          inner dst MAC = VTEP-B's Router MAC (received via BGP extended community)
          inner src MAC = VTEP-A's Router MAC
  Step 4: Packet travels through underlay to VTEP-B
  Step 5: VTEP-B receives on L3VNI-5000
  Step 6: VTEP-B routes: 10.2.0.1 is in VNI-200 (local)
  Step 7: VTEP-B bridges to VM-B in VNI-200

  Return path: VTEP-B routes through L3VNI-5000 → VTEP-A → bridges to VM-A

L3 VNI packet format:
  outer: VTEP-A → VTEP-B
  inner Eth: VTEP-A-RMAC → VTEP-B-RMAC  ← Router MACs, not VM MACs
  VNI: 5000 (L3 VNI, same for all inter-VNI traffic in same VRF)
  inner IP: VM-A-IP → VM-B-IP  ← original VM IPs preserved

Characteristics:
  + Each VTEP only needs its local VNIs + L3 VNI(s)
  + Scales well: VTEP-B doesn't need VNI-100 at all
  + Optimal for large-scale deployments
  + Required for EVPN multi-VRF scenarios
  - Requires L3 VNI infrastructure
  - BGP EVPN Type-5 routes needed for prefix advertisement
  - Router MAC community needed for RMAC distribution
```

### 9.3 Comparison Table

```
Feature               Asymmetric IRB     Symmetric IRB
─────────────────────────────────────────────────────
L3 VNI needed         No                 Yes
VNI scope per VTEP    All VNIs           Local VNIs + L3 VNI
Scalability           Poor (many VNIs)   Excellent
ARP suppression       Cross-VNI needed   Per-VNI (simpler)
EVPN routes needed    Type-2, 3          Type-2, 3, 5
Router MAC needed     No                 Yes
Multi-tenant VRF      Difficult          Native (per-VRF L3VNI)
Production use        Legacy, small DC   Standard, large DC
```

---

## 10. Distributed Anycast Gateway

### 10.1 Problem with Centralized Gateway

In traditional networks, VMs in a VLAN have a single default gateway. If the gateway is on a separate router:
- North-south traffic must hairpin through the gateway
- Gateway becomes a bottleneck and single point of failure
- VM mobility means gateway may be far from the VM

### 10.2 Anycast Gateway Concept

Every VTEP (leaf switch) acts as the default gateway for locally attached VMs, using the **same** IP and MAC address across all VTEPs.

```
              Distributed Anycast Gateway

         VNI 100: 10.1.0.0/24
         Anycast GW IP:  10.1.0.254  (same on ALL VTEPs)
         Anycast GW MAC: 00:00:5e:00:01:01  (same on ALL VTEPs, VRRP-like)

  VTEP-A                  VTEP-B                  VTEP-C
  SVI vxlan100:           SVI vxlan100:           SVI vxlan100:
    IP: 10.1.0.254          IP: 10.1.0.254          IP: 10.1.0.254
    MAC: 00:00:5e:00:01:01  MAC: 00:00:5e:00:01:01  MAC: 00:00:5e:00:01:01

  VM-A (on VTEP-A):
    GW = 10.1.0.254 → ARP → gets 00:00:5e:00:01:01
    Sends frame to VTEP-A (local!) — no traffic leaves host for default GW
    VTEP-A routes the packet

  After VM-A migrates to VTEP-C:
    Same GW IP, same GW MAC — VM doesn't notice migration
    ARP cache still valid
    VTEP-C now handles routing for VM-A

Benefits:
  - Optimal routing: first hop gateway is always local
  - No hairpinning for east-west traffic
  - VM mobility transparent to applications
  - No VRRP, HSRP, or gateway redundancy protocols needed
  - Gateway failure = VTEP failure (already handled by underlay)
```

### 10.3 Implementation

```bash
# On every VTEP leaf, configure same IP/MAC for SVI
# Linux/FRR approach:
ip link add vxlan100 type vxlan id 100 dstport 4789 local 10.0.0.1 nolearning
ip link add br100 type bridge
ip link set vxlan100 master br100
ip link set br100 up
ip link set vxlan100 up

# SVI (bridge interface as default gateway)
ip addr add 10.1.0.254/24 dev br100
# Set SAME MAC on all VTEPs' SVI
ip link set dev br100 address 00:00:5e:00:01:01

# FRR redistributes this into BGP:
# router bgp → advertise-svi-ip → advertises SVI IP as EVPN Type-2
```

---

## 11. VXLAN Gateway Types

### 11.1 L2 Gateway (VXLAN-VLAN Bridging)

Bridges traffic between a VXLAN overlay and a traditional VLAN segment. Common for connecting legacy physical servers into the overlay.

```
  VXLAN Overlay (VNI 100) <──> L2 Gateway <──> VLAN 100 (legacy LAN)

  Gateway actions:
    VXLAN→VLAN: strip VXLAN header, retag with VLAN 100, forward
    VLAN→VXLAN: strip VLAN tag, add VXLAN header (VNI=100), forward
    Same L2 domain: MACs visible in both segments
```

### 11.2 L3 Gateway (VXLAN Router)

Routes traffic between VXLAN VNIs or between overlay and external networks.

```
  VNI-100 (10.1.0.0/24) <──> L3 GW (IRB) <──> VNI-200 (10.2.0.0/24)
                                  │
                               External
                               Network
                             (BGP/OSPF)
```

### 11.3 External Connectivity Gateway

```
DC Fabric (VXLAN overlay) <──> Border Leaf <──> WAN/Internet

Border Leaf:
  - Participates in VXLAN fabric (VTEP)
  - Also connects to external router via BGP
  - Redistributes:
    External prefixes → EVPN Type-5 (into overlay)
    Overlay prefixes  → External BGP (to WAN)
  - NAT for overlapping IP spaces
  - Policy enforcement point
```

---

## 12. Linux Kernel VXLAN Implementation

### 12.1 Kernel Module and Code Path

The Linux VXLAN implementation lives in `net/vxlan.c` (kernel). Key structures:

```c
/* Simplified - actual in include/net/vxlan.h */
struct vxlan_dev {
    struct net_device   *dev;           /* vxlan netdev */
    struct vxlan_sock   *vn4_sock;      /* UDP socket (IPv4) */
    struct vxlan_sock   *vn6_sock;      /* UDP socket (IPv6) */
    struct hlist_head   fdb_head[FDB_HASH_SIZE]; /* FDB hash table */
    __be32              vni;            /* VNI */
    union vxlan_addr    remote_ip;      /* default remote VTEP */
    union vxlan_addr    saddr;          /* source VTEP IP */
    __be16              dst_port;       /* UDP dst port */
    u32                 flags;          /* VXLAN_F_* flags */
    /* ... */
};

struct vxlan_fdb {
    struct hlist_node   hlist;    /* hash bucket list */
    struct rcu_head     rcu;
    unsigned long       updated;
    unsigned long       used;
    struct list_head    remotes;  /* list of remote_ip */
    u8                  eth_addr[ETH_ALEN];
    u16                 state;
    u8                  flags;
};
```

### 12.2 Kernel RX Path (Decapsulation)

```
UDP packet arrives on port 4789
  └─→ vxlan_udp_encap_recv()      [registered via setup_udp_tunnel_sock]
        └─→ vxlan_rcv()
              ├─ validate VXLAN header (I-flag set, VNI valid)
              ├─ extract VNI from header
              ├─ find vxlan_dev by VNI
              ├─ strip VXLAN+UDP+IP+Eth headers
              ├─ if learning: vxlan_snoop() → update FDB with src MAC/VTEP-IP
              ├─ lookup inner dst MAC in local bridge FDB
              └─ netif_rx() / napi_gro_receive() → deliver to bridge/VM
```

### 12.3 Kernel TX Path (Encapsulation)

```
Ethernet frame from VM/bridge to vxlan0
  └─→ vxlan_xmit()
        ├─ dst MAC lookup in FDB: vxlan_find_mac()
        │   ├─ found: use stored VTEP-IP
        │   └─ not found: use BUM (multicast / head-end replication list)
        ├─ vxlan_xmit_one()
        │   ├─ build VXLAN header: set I-flag, VNI
        │   ├─ build UDP header: src=entropy_hash(inner), dst=4789
        │   ├─ build IP header: src=VTEP-IP, dst=remote-VTEP-IP
        │   ├─ if GSO enabled: vxlan_gso_segment() for segmentation offload
        │   └─ ip_route_output() → route lookup → send to underlay NIC
        └─ for BUM: iterate remote list, send copy to each
```

### 12.4 Creating VXLAN Interfaces

```bash
# Basic VXLAN (multicast BUM):
ip link add vxlan100 type vxlan \
    id 100 \
    dstport 4789 \
    local 10.0.0.1 \
    group 239.1.1.100 \
    dev eth0 \
    ttl 64

# Unicast (head-end replication, for BGP EVPN):
ip link add vxlan100 type vxlan \
    id 100 \
    dstport 4789 \
    local 10.0.0.1 \
    nolearning \
    proxy \
    ttl 255

# With IPv6 underlay:
ip link add vxlan100 type vxlan \
    id 100 \
    dstport 4789 \
    local6 fd00::1 \
    nolearning

# Verify:
ip -d link show vxlan100

# Bridge integration:
ip link add br100 type bridge
ip link set vxlan100 master br100
ip link set vm-veth0 master br100
ip link set br100 up
ip link set vxlan100 up
```

### 12.5 FDB Management via Netlink

```bash
# Add unicast MAC → VTEP mapping
bridge fdb add aa:bb:cc:11:22:33 \
    dev vxlan100 \
    dst 10.0.0.2 \
    self permanent

# Add BUM flooding target
bridge fdb append 00:00:00:00:00:00 \
    dev vxlan100 \
    dst 10.0.0.2 \
    self permanent

# ARP suppression (neighbor entry for proxy ARP):
ip neigh add 10.1.0.2 \
    lladdr aa:bb:cc:11:22:33 \
    dev vxlan100 \
    nud permanent

# List FDB
bridge fdb show dev vxlan100
# List ARP suppression table
ip neigh show dev vxlan100
```

### 12.6 VXLAN Kernel Flags

```c
/* From include/net/vxlan.h */
#define VXLAN_F_LEARN          0x01  /* data-plane MAC learning */
#define VXLAN_F_PROXY          0x02  /* ARP proxy / suppression */
#define VXLAN_F_RSC            0x04  /* Route Short Circuit (L3 miss) */
#define VXLAN_F_L2MISS         0x08  /* upcall to userspace on FDB miss */
#define VXLAN_F_L3MISS         0x10  /* upcall to userspace on ARP miss */
#define VXLAN_F_IPV6           0x20  /* IPv6 underlay */
#define VXLAN_F_UDP_ZERO_CSUM6_TX 0x40  /* zero checksum TX (IPv6) */
#define VXLAN_F_UDP_ZERO_CSUM6_RX 0x80  /* accept zero checksum RX */
#define VXLAN_F_COLLECT_METADATA  0x100 /* metadata mode (OVS/BPF) */
#define VXLAN_F_GBP            0x800  /* Group Based Policy extension */
#define VXLAN_F_GPE            0x4000 /* VXLAN-GPE extension */
```

### 12.7 VXLAN Collect Metadata Mode

Used by Open vSwitch (OVS) and TC eBPF for external FDB management:

```bash
# Create VXLAN in metadata mode (no VNI bound to interface)
ip link add vxlan0 type vxlan \
    dstport 4789 \
    external  # 'external' = collect metadata mode

# In this mode:
# - Single vxlan0 interface handles ALL VNIs
# - VNI/VTEP info passed via skb metadata (TC/BPF tunnel_key)
# - Used by: OVS datapath, Cilium, Flannel (older), Calico
```

---

## 13. Hardware Offload and ASIC Integration

### 13.1 NIC Offload

Modern NICs (Mellanox/NVIDIA ConnectX-5+, Intel X710, Broadcom P4) support VXLAN offload:

```
TX Offload (Encapsulation):
  Driver provides: inner Ethernet frame + VXLAN tunnel parameters
  NIC adds: outer Ethernet + IP + UDP + VXLAN headers at line rate
  Also: TX checksum offload for outer UDP/IP
  Also: TSO (TCP Segmentation Offload) through VXLAN (inner TCP segments)

RX Offload (Decapsulation):
  NIC strips outer headers, delivers inner frame to kernel
  Populates skb tunnel metadata
  RSS (Receive Side Scaling) on INNER 5-tuple for VXLAN
    → critical: without inner-RSS, all VXLAN traffic to one CPU
  RX checksum verification of inner packet

Checking NIC VXLAN offload support:
  ethtool -k eth0 | grep vxlan
  tx-udp_tnl-segmentation: on          ← VXLAN TSO
  tx-udp_tnl-csum-segmentation: on
  rx-udp_tunnel-port-lookup: on        ← HW port detection

Registering VXLAN UDP port with NIC:
  NIC must know VXLAN port (4789 or 8472) to apply offloads
  Linux: udp_tunnel_push_rx_port() notifies drivers
```

### 13.2 ASIC (Hardware VTEP)

Top-of-Rack switches with VXLAN-capable ASICs:

```
Broadcom Trident 3/4, Tomahawk 3/4:
  - Hardware VTEP at line rate (100G per port)
  - FDB in TCAM (typically 128K-512K entries)
  - Encap/decap in forwarding pipeline
  - OVSDB Hardware VTEP schema for control
  - Supports: BGP EVPN (via routing software like FRR on switch CPU)
  - Supports: ARP suppression, BUM replication
  - ECMP for underlay with inner-packet hashing

Cisco Nexus 9000 (Cloud Scale ASIC):
  - 12.8 Tbps switching capacity
  - vPC with VXLAN for dual-homed access
  - BGP EVPN control plane built-in
  - FDB entries: 512K MAC, 256K ARP suppression entries

Mellanox Spectrum 2/3:
  - Ultra-low latency (300ns VXLAN)
  - VXLAN offload + RDMA over VXLAN
  - Onebox: switch runs Cumulus/SONiC with FRR

SmartNIC (NVIDIA BlueField-3):
  - ARM cores run full network stack
  - VXLAN encap/decap offloaded from host CPU
  - OVS-DPDK runs on BlueField
  - Host CPU completely free
  - Programmable via P4/eBPF
```

### 13.3 SR-IOV with VXLAN

```
Physical NIC (ConnectX-5)
  │
  ├─ PF (Physical Function) — managed by hypervisor/host
  │   └─ VXLAN offload config, tunnel metadata
  │
  ├─ VF-0 (Virtual Function) → VM-0
  │   Frame from VM-0 → PF applies VXLAN encap → wire
  │   Wire → PF VXLAN decap → VF-0 delivers to VM-0
  │
  └─ VF-1 (Virtual Function) → VM-1

  SR-IOV + VXLAN offload:
    Each VF associated with a VNI
    Hardware VXLAN encap/decap per VF
    Near-zero CPU overhead for network I/O
```

---

## 14. C Implementation: Software VTEP

This is a working simplified VTEP in C. It uses raw sockets and the Linux tun/tap interface to demonstrate the full encapsulation pipeline.

### 14.1 Project Layout

```
vxlan-vtep/
├── CMakeLists.txt
├── src/
│   ├── main.c
│   ├── vtep.c / vtep.h        ← VTEP core
│   ├── fdb.c / fdb.h          ← Forwarding Database
│   ├── encap.c / encap.h      ← Packet encapsulation
│   ├── tuntap.c / tuntap.h    ← TUN/TAP interface
│   └── checksum.c / checksum.h
└── tests/
    └── test_fdb.c
```

### 14.2 Protocol Headers

```c
/* File: src/proto.h */
#ifndef VXLAN_PROTO_H
#define VXLAN_PROTO_H

#include <stdint.h>
#include <arpa/inet.h>

/* ─── Ethernet Header ─── */
#define ETH_ALEN 6
#define ETHERTYPE_IP    0x0800
#define ETHERTYPE_ARP   0x0806
#define ETHERTYPE_IPV6  0x86DD

struct eth_hdr {
    uint8_t  dst[ETH_ALEN];
    uint8_t  src[ETH_ALEN];
    uint16_t ethertype;         /* network byte order */
} __attribute__((packed));

/* ─── IPv4 Header ─── */
struct ipv4_hdr {
    uint8_t  ver_ihl;           /* version (4) | IHL (5) = 0x45 */
    uint8_t  tos;
    uint16_t tot_len;
    uint16_t id;
    uint16_t frag_off;
    uint8_t  ttl;
    uint8_t  protocol;          /* 17 = UDP */
    uint16_t checksum;
    uint32_t src_ip;
    uint32_t dst_ip;
} __attribute__((packed));

/* ─── UDP Header ─── */
struct udp_hdr {
    uint16_t src_port;
    uint16_t dst_port;
    uint16_t length;
    uint16_t checksum;          /* 0 for VXLAN over IPv4 (RFC 7348) */
} __attribute__((packed));

/* ─── VXLAN Header ─── */
#define VXLAN_FLAG_I        0x08    /* VNI valid flag */
#define VXLAN_PORT_IANA     4789    /* IANA assigned */
#define VXLAN_PORT_LINUX    8472    /* Linux historical default */

struct vxlan_hdr {
    uint8_t  flags;             /* bit 3 (0x08) must be set = I flag */
    uint8_t  reserved1[3];
    uint8_t  vni[3];            /* 24-bit VNI, network byte order */
    uint8_t  reserved2;
} __attribute__((packed));

/* ─── ARP Header ─── */
#define ARP_HTYPE_ETH   1
#define ARP_PTYPE_IP    0x0800
#define ARP_OP_REQUEST  1
#define ARP_OP_REPLY    2

struct arp_hdr {
    uint16_t htype;
    uint16_t ptype;
    uint8_t  hlen;
    uint8_t  plen;
    uint16_t oper;
    uint8_t  sha[ETH_ALEN];    /* sender MAC */
    uint32_t spa;               /* sender IP */
    uint8_t  tha[ETH_ALEN];    /* target MAC */
    uint32_t tpa;               /* target IP */
} __attribute__((packed));

/* Helper: encode VNI into 3-byte field */
static inline void vxlan_set_vni(struct vxlan_hdr *h, uint32_t vni) {
    h->vni[0] = (vni >> 16) & 0xFF;
    h->vni[1] = (vni >>  8) & 0xFF;
    h->vni[2] = (vni      ) & 0xFF;
}

/* Helper: decode VNI from 3-byte field */
static inline uint32_t vxlan_get_vni(const struct vxlan_hdr *h) {
    return ((uint32_t)h->vni[0] << 16) |
           ((uint32_t)h->vni[1] <<  8) |
           ((uint32_t)h->vni[2]      );
}

#define VXLAN_OVERHEAD  (sizeof(struct eth_hdr) + sizeof(struct ipv4_hdr) + \
                         sizeof(struct udp_hdr) + sizeof(struct vxlan_hdr))

#endif /* VXLAN_PROTO_H */
```

### 14.3 Forwarding Database

```c
/* File: src/fdb.h */
#ifndef VXLAN_FDB_H
#define VXLAN_FDB_H

#include <stdint.h>
#include <time.h>
#include <pthread.h>
#include "proto.h"

#define FDB_HASH_SIZE       1024
#define FDB_MAX_ENTRIES     65536
#define FDB_ENTRY_TTL_SEC   300     /* 5 minutes aging */

typedef struct fdb_entry {
    uint8_t  mac[ETH_ALEN];
    uint32_t vni;
    uint32_t remote_vtep_ip;    /* 0 = local */
    time_t   last_seen;
    int      is_static;         /* static entries don't age */
    struct fdb_entry *next;     /* hash chaining */
} fdb_entry_t;

typedef struct fdb {
    fdb_entry_t   *buckets[FDB_HASH_SIZE];
    uint32_t       count;
    pthread_rwlock_t lock;
} fdb_t;

fdb_t *fdb_create(void);
void   fdb_destroy(fdb_t *fdb);
int    fdb_insert(fdb_t *fdb, uint32_t vni, const uint8_t *mac,
                  uint32_t remote_vtep_ip, int is_static);
fdb_entry_t *fdb_lookup(fdb_t *fdb, uint32_t vni, const uint8_t *mac);
void   fdb_delete(fdb_t *fdb, uint32_t vni, const uint8_t *mac);
void   fdb_age(fdb_t *fdb);

#endif
```

```c
/* File: src/fdb.c */
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "fdb.h"

/* FNV-1a hash over {VNI, MAC} */
static uint32_t fdb_hash(uint32_t vni, const uint8_t *mac) {
    uint32_t h = 2166136261u; /* FNV offset basis */
    h = (h ^ ((vni >> 16) & 0xFF)) * 16777619u;
    h = (h ^ ((vni >>  8) & 0xFF)) * 16777619u;
    h = (h ^ ((vni      ) & 0xFF)) * 16777619u;
    for (int i = 0; i < ETH_ALEN; i++)
        h = (h ^ mac[i]) * 16777619u;
    return h & (FDB_HASH_SIZE - 1);
}

fdb_t *fdb_create(void) {
    fdb_t *fdb = calloc(1, sizeof(fdb_t));
    if (!fdb) return NULL;
    pthread_rwlock_init(&fdb->lock, NULL);
    return fdb;
}

void fdb_destroy(fdb_t *fdb) {
    if (!fdb) return;
    pthread_rwlock_wrlock(&fdb->lock);
    for (int i = 0; i < FDB_HASH_SIZE; i++) {
        fdb_entry_t *e = fdb->buckets[i];
        while (e) {
            fdb_entry_t *next = e->next;
            free(e);
            e = next;
        }
    }
    pthread_rwlock_unlock(&fdb->lock);
    pthread_rwlock_destroy(&fdb->lock);
    free(fdb);
}

int fdb_insert(fdb_t *fdb, uint32_t vni, const uint8_t *mac,
               uint32_t remote_vtep_ip, int is_static) {
    uint32_t idx = fdb_hash(vni, mac);
    pthread_rwlock_wrlock(&fdb->lock);

    /* check existing entry */
    fdb_entry_t *e = fdb->buckets[idx];
    while (e) {
        if (e->vni == vni && memcmp(e->mac, mac, ETH_ALEN) == 0) {
            /* update existing */
            e->remote_vtep_ip = remote_vtep_ip;
            e->last_seen = time(NULL);
            if (is_static) e->is_static = 1;
            pthread_rwlock_unlock(&fdb->lock);
            return 0;
        }
        e = e->next;
    }

    if (fdb->count >= FDB_MAX_ENTRIES) {
        pthread_rwlock_unlock(&fdb->lock);
        return -1; /* FDB full */
    }

    fdb_entry_t *ne = calloc(1, sizeof(fdb_entry_t));
    if (!ne) {
        pthread_rwlock_unlock(&fdb->lock);
        return -1;
    }
    memcpy(ne->mac, mac, ETH_ALEN);
    ne->vni = vni;
    ne->remote_vtep_ip = remote_vtep_ip;
    ne->last_seen = time(NULL);
    ne->is_static = is_static;
    ne->next = fdb->buckets[idx];
    fdb->buckets[idx] = ne;
    fdb->count++;

    pthread_rwlock_unlock(&fdb->lock);
    return 0;
}

fdb_entry_t *fdb_lookup(fdb_t *fdb, uint32_t vni, const uint8_t *mac) {
    uint32_t idx = fdb_hash(vni, mac);
    pthread_rwlock_rdlock(&fdb->lock);
    fdb_entry_t *e = fdb->buckets[idx];
    while (e) {
        if (e->vni == vni && memcmp(e->mac, mac, ETH_ALEN) == 0) {
            pthread_rwlock_unlock(&fdb->lock);
            return e; /* NOTE: caller must NOT free; lock released */
        }
        e = e->next;
    }
    pthread_rwlock_unlock(&fdb->lock);
    return NULL;
}

/* Remove aged entries */
void fdb_age(fdb_t *fdb) {
    time_t now = time(NULL);
    pthread_rwlock_wrlock(&fdb->lock);
    for (int i = 0; i < FDB_HASH_SIZE; i++) {
        fdb_entry_t **pp = &fdb->buckets[i];
        fdb_entry_t  *e  = *pp;
        while (e) {
            if (!e->is_static && (now - e->last_seen) > FDB_ENTRY_TTL_SEC) {
                *pp = e->next;
                free(e);
                e = *pp;
                fdb->count--;
            } else {
                pp = &e->next;
                e  = e->next;
            }
        }
    }
    pthread_rwlock_unlock(&fdb->lock);
}
```

### 14.4 IP Checksum

```c
/* File: src/checksum.c */
#include <stdint.h>
#include <stddef.h>

uint16_t ip_checksum(const void *data, size_t len) {
    const uint16_t *p = data;
    uint32_t sum = 0;

    while (len > 1) {
        sum += *p++;
        len -= 2;
    }
    if (len == 1)
        sum += *(const uint8_t *)p;

    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);

    return (uint16_t)(~sum);
}
```

### 14.5 VTEP Core — Encapsulation and Decapsulation

```c
/* File: src/vtep.h */
#ifndef VXLAN_VTEP_H
#define VXLAN_VTEP_H

#include <stdint.h>
#include "fdb.h"
#include "proto.h"

#define MAX_PKT_SIZE        9216    /* jumbo frame support */
#define VTEP_BUM_LIST_MAX   256

typedef struct bum_peer {
    uint32_t vtep_ip;
} bum_peer_t;

typedef struct vtep_config {
    uint32_t    local_ip;           /* VTEP underlay IP */
    uint8_t     local_mac[ETH_ALEN];/* VTEP underlay MAC */
    uint32_t    vni;                /* this VTEP's VNI */
    uint16_t    udp_port;           /* VXLAN UDP dst port */
    char        tap_name[16];       /* tap interface name */
    char        underlay_iface[16]; /* underlay eth interface */
    uint8_t     inner_mac[ETH_ALEN];/* SVI/bridge MAC for ARP proxy */
    uint32_t    inner_ip;           /* SVI IP (anycast GW) */
    bum_peer_t  bum_list[VTEP_BUM_LIST_MAX];
    int         bum_count;
} vtep_config_t;

typedef struct vtep {
    vtep_config_t  cfg;
    fdb_t         *fdb;
    int            tap_fd;          /* TAP interface fd */
    int            raw_fd;          /* raw socket fd (underlay) */
    int            udp_fd;          /* UDP socket for recv */
} vtep_t;

vtep_t *vtep_create(const vtep_config_t *cfg);
void    vtep_destroy(vtep_t *vtep);
int     vtep_run(vtep_t *vtep);     /* main event loop */

/* Packet processing */
int vtep_encap_send(vtep_t *vtep, const uint8_t *inner_frame,
                    size_t inner_len, uint32_t dst_vtep_ip);
int vtep_decap_recv(vtep_t *vtep, const uint8_t *outer_pkt, size_t outer_len);

#endif
```

```c
/* File: src/vtep.c */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <sys/select.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <linux/if_tun.h>
#include <fcntl.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include "vtep.h"
#include "checksum.h"

/* ─── TUN/TAP setup ─── */
static int tuntap_open(const char *name) {
    struct ifreq ifr = {0};
    int fd = open("/dev/net/tun", O_RDWR);
    if (fd < 0) return -1;

    ifr.ifr_flags = IFF_TAP | IFF_NO_PI;   /* TAP = Ethernet frames, no packet info header */
    strncpy(ifr.ifr_name, name, IFNAMSIZ - 1);

    if (ioctl(fd, TUNSETIFF, &ifr) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

/* ─── UDP recv socket ─── */
static int udp_recv_socket(uint16_t port) {
    int fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd < 0) return -1;

    int one = 1;
    setsockopt(fd, SOL_SOCKET, SO_REUSEADDR, &one, sizeof(one));
    /* Enable recvfrom to get source IP */

    struct sockaddr_in addr = {
        .sin_family = AF_INET,
        .sin_port   = htons(port),
        .sin_addr   = { .s_addr = INADDR_ANY },
    };
    if (bind(fd, (struct sockaddr *)&addr, sizeof(addr)) < 0) {
        close(fd);
        return -1;
    }
    return fd;
}

/* ─── Compute source port for ECMP entropy ─── */
static uint16_t entropy_src_port(const uint8_t *inner_frame, size_t inner_len) {
    /* Hash inner Ethernet+IP+transport headers */
    if (inner_len < sizeof(struct eth_hdr) + sizeof(struct ipv4_hdr))
        return 49152; /* fallback */

    const struct eth_hdr  *eth = (const struct eth_hdr *)inner_frame;
    if (ntohs(eth->ethertype) != ETHERTYPE_IP)
        return 50000;

    const struct ipv4_hdr *ip = (const struct ipv4_hdr *)(inner_frame + sizeof(*eth));
    uint16_t src_port = 0, dst_port = 0;

    size_t ip_hdr_len = (ip->ver_ihl & 0x0F) * 4;
    const uint8_t *transport = inner_frame + sizeof(*eth) + ip_hdr_len;
    size_t transport_avail = inner_len - sizeof(*eth) - ip_hdr_len;

    if (transport_avail >= 4) {
        /* First 4 bytes of TCP/UDP = src+dst port */
        memcpy(&src_port, transport, 2);
        memcpy(&dst_port, transport + 2, 2);
    }

    /* FNV-1a over src_ip, dst_ip, src_port, dst_port, proto */
    uint32_t h = 2166136261u;
    h = (h ^ ((ip->src_ip >> 24) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->src_ip >> 16) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->src_ip >>  8) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->src_ip      ) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->dst_ip >> 24) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->dst_ip >> 16) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->dst_ip >>  8) & 0xFF)) * 16777619u;
    h = (h ^ ((ip->dst_ip      ) & 0xFF)) * 16777619u;
    h = (h ^ (src_port & 0xFF)) * 16777619u;
    h = (h ^ (src_port >> 8))   * 16777619u;
    h = (h ^ (dst_port & 0xFF)) * 16777619u;
    h = (h ^ (dst_port >> 8))   * 16777619u;
    h = (h ^ ip->protocol)      * 16777619u;

    /* Map to ephemeral range [49152, 65535] */
    return 49152 + (h & 0x3FFF);
}

/* ─── Encapsulate and send inner frame ─── */
int vtep_encap_send(vtep_t *vtep, const uint8_t *inner_frame,
                    size_t inner_len, uint32_t dst_vtep_ip) {
    uint8_t pkt[MAX_PKT_SIZE];
    size_t  pkt_len = VXLAN_OVERHEAD + inner_len;

    if (pkt_len > sizeof(pkt)) return -1;

    uint8_t *p = pkt;

    /* ── Outer Ethernet ── */
    struct eth_hdr *outer_eth = (struct eth_hdr *)p;
    /* In a real system: ARP lookup dst_vtep_ip → next-hop MAC */
    /* Here: fill in preconfigured gateway MAC (simplified) */
    memset(outer_eth->dst, 0xFF, ETH_ALEN);        /* placeholder: broadcast */
    memcpy(outer_eth->src, vtep->cfg.local_mac, ETH_ALEN);
    outer_eth->ethertype = htons(ETHERTYPE_IP);
    p += sizeof(struct eth_hdr);

    /* ── Outer IPv4 ── */
    struct ipv4_hdr *outer_ip = (struct ipv4_hdr *)p;
    outer_ip->ver_ihl  = 0x45;                      /* IPv4, IHL=5 (20 bytes) */
    outer_ip->tos      = 0;
    outer_ip->tot_len  = htons(pkt_len - sizeof(struct eth_hdr));
    outer_ip->id       = 0;
    outer_ip->frag_off = htons(0x4000);             /* DF bit set */
    outer_ip->ttl      = 255;                       /* RFC 7348 recommendation */
    outer_ip->protocol = 17;                        /* UDP */
    outer_ip->checksum = 0;
    outer_ip->src_ip   = htonl(vtep->cfg.local_ip);
    outer_ip->dst_ip   = htonl(dst_vtep_ip);
    outer_ip->checksum = ip_checksum(outer_ip, sizeof(*outer_ip));
    p += sizeof(struct ipv4_hdr);

    /* ── Outer UDP ── */
    struct udp_hdr *outer_udp = (struct udp_hdr *)p;
    outer_udp->src_port = htons(entropy_src_port(inner_frame, inner_len));
    outer_udp->dst_port = htons(vtep->cfg.udp_port);
    outer_udp->length   = htons(sizeof(*outer_udp) + sizeof(struct vxlan_hdr) + inner_len);
    outer_udp->checksum = 0;                        /* RFC 7348: set to zero for IPv4 */
    p += sizeof(struct udp_hdr);

    /* ── VXLAN Header ── */
    struct vxlan_hdr *vxhdr = (struct vxlan_hdr *)p;
    memset(vxhdr, 0, sizeof(*vxhdr));
    vxhdr->flags = VXLAN_FLAG_I;                    /* set I-flag: VNI valid */
    vxlan_set_vni(vxhdr, vtep->cfg.vni);
    p += sizeof(struct vxlan_hdr);

    /* ── Inner Ethernet Frame ── */
    memcpy(p, inner_frame, inner_len);

    /* Send via UDP socket */
    struct sockaddr_in remote = {
        .sin_family = AF_INET,
        .sin_port   = htons(vtep->cfg.udp_port),
        .sin_addr   = { .s_addr = htonl(dst_vtep_ip) },
    };

    /* Skip outer Ethernet for UDP socket (kernel adds it) */
    size_t udp_payload_offset = sizeof(struct eth_hdr) + sizeof(struct ipv4_hdr);
    ssize_t sent = sendto(vtep->udp_fd,
                          pkt + udp_payload_offset,
                          pkt_len - udp_payload_offset,
                          0,
                          (struct sockaddr *)&remote,
                          sizeof(remote));
    return (sent < 0) ? -1 : 0;
}

/* ─── BUM: send to all peers ─── */
static int vtep_bum_flood(vtep_t *vtep, const uint8_t *inner_frame, size_t inner_len) {
    int ok = 0;
    for (int i = 0; i < vtep->cfg.bum_count; i++) {
        if (vtep_encap_send(vtep, inner_frame, inner_len,
                            vtep->cfg.bum_list[i].vtep_ip) < 0) {
            fprintf(stderr, "BUM flood to peer %d failed\n", i);
            ok = -1;
        }
    }
    return ok;
}

/* ─── Receive from TAP (inner frame from VM) → encapsulate ─── */
static int handle_tap_rx(vtep_t *vtep) {
    uint8_t buf[MAX_PKT_SIZE];
    ssize_t n = read(vtep->tap_fd, buf, sizeof(buf));
    if (n <= 0) return -1;
    if (n < (ssize_t)sizeof(struct eth_hdr)) return 0;

    const struct eth_hdr *eth = (const struct eth_hdr *)buf;

    /* MAC learning: record src MAC → local (no remote VTEP IP = 0) */
    fdb_insert(vtep->fdb, vtep->cfg.vni, eth->src, 0 /* local */, 0);

    /* Check if broadcast/multicast */
    int is_bum = (eth->dst[0] & 0x01) != 0 ||      /* multicast/broadcast bit */
                 memcmp(eth->dst, "\xff\xff\xff\xff\xff\xff", ETH_ALEN) == 0;

    if (is_bum) {
        return vtep_bum_flood(vtep, buf, (size_t)n);
    }

    /* Unicast: lookup FDB */
    fdb_entry_t *entry = fdb_lookup(vtep->fdb, vtep->cfg.vni, eth->dst);
    if (!entry || entry->remote_vtep_ip == 0) {
        /* Unknown unicast or local: flood */
        return vtep_bum_flood(vtep, buf, (size_t)n);
    }

    return vtep_encap_send(vtep, buf, (size_t)n, entry->remote_vtep_ip);
}

/* ─── Decapsulate: receive from UDP → deliver to TAP ─── */
int vtep_decap_recv(vtep_t *vtep, const uint8_t *outer_pkt, size_t outer_len) {
    /* outer_pkt here is UDP payload (after kernel strips UDP header) */
    if (outer_len < sizeof(struct vxlan_hdr) + sizeof(struct eth_hdr))
        return -1;

    const struct vxlan_hdr *vxhdr = (const struct vxlan_hdr *)outer_pkt;

    /* Validate I-flag */
    if (!(vxhdr->flags & VXLAN_FLAG_I)) {
        fprintf(stderr, "VXLAN: I-flag not set, dropping\n");
        return -1;
    }

    uint32_t vni = vxlan_get_vni(vxhdr);
    if (vni != vtep->cfg.vni) {
        /* Not our VNI — in a full VTEP, dispatch to correct VNI handler */
        return 0;
    }

    const uint8_t *inner_frame = outer_pkt + sizeof(struct vxlan_hdr);
    size_t inner_len = outer_len - sizeof(struct vxlan_hdr);

    /* Deliver to TAP (inner frame to VM) */
    ssize_t n = write(vtep->tap_fd, inner_frame, inner_len);
    return (n < 0) ? -1 : 0;
}

/* ─── Main event loop ─── */
int vtep_run(vtep_t *vtep) {
    fd_set rfds;
    int maxfd = (vtep->tap_fd > vtep->udp_fd) ? vtep->tap_fd : vtep->udp_fd;
    maxfd++;

    uint8_t udp_buf[MAX_PKT_SIZE];

    fprintf(stderr, "VTEP running: VNI=%u local_ip=%u port=%u\n",
            vtep->cfg.vni, vtep->cfg.local_ip, vtep->cfg.udp_port);

    for (;;) {
        FD_ZERO(&rfds);
        FD_SET(vtep->tap_fd, &rfds);
        FD_SET(vtep->udp_fd, &rfds);

        struct timeval tv = { .tv_sec = 5, .tv_usec = 0 };
        int ret = select(maxfd, &rfds, NULL, NULL, &tv);
        if (ret < 0) {
            if (errno == EINTR) continue;
            perror("select");
            break;
        }

        if (ret == 0) {
            fdb_age(vtep->fdb);     /* periodic FDB aging */
            continue;
        }

        if (FD_ISSET(vtep->tap_fd, &rfds)) {
            handle_tap_rx(vtep);
        }

        if (FD_ISSET(vtep->udp_fd, &rfds)) {
            struct sockaddr_in sender;
            socklen_t slen = sizeof(sender);
            ssize_t n = recvfrom(vtep->udp_fd, udp_buf, sizeof(udp_buf), 0,
                                 (struct sockaddr *)&sender, &slen);
            if (n > 0) {
                /* MAC learning from outer src IP */
                const uint8_t *inner = udp_buf + sizeof(struct vxlan_hdr);
                size_t inner_len = (size_t)n - sizeof(struct vxlan_hdr);
                if (inner_len >= sizeof(struct eth_hdr)) {
                    const struct eth_hdr *eth = (const struct eth_hdr *)inner;
                    uint32_t src_vtep = ntohl(sender.sin_addr.s_addr);
                    fdb_insert(vtep->fdb, vtep->cfg.vni, eth->src, src_vtep, 0);
                }
                vtep_decap_recv(vtep, udp_buf, (size_t)n);
            }
        }
    }
    return 0;
}

vtep_t *vtep_create(const vtep_config_t *cfg) {
    vtep_t *v = calloc(1, sizeof(vtep_t));
    if (!v) return NULL;
    memcpy(&v->cfg, cfg, sizeof(*cfg));

    v->fdb = fdb_create();
    if (!v->fdb) { free(v); return NULL; }

    v->tap_fd = tuntap_open(cfg->tap_name);
    if (v->tap_fd < 0) { fdb_destroy(v->fdb); free(v); return NULL; }

    v->udp_fd = udp_recv_socket(cfg->udp_port);
    if (v->udp_fd < 0) {
        close(v->tap_fd);
        fdb_destroy(v->fdb);
        free(v);
        return NULL;
    }
    return v;
}

void vtep_destroy(vtep_t *vtep) {
    if (!vtep) return;
    close(vtep->tap_fd);
    close(vtep->udp_fd);
    fdb_destroy(vtep->fdb);
    free(vtep);
}
```

### 14.6 Main Entry Point

```c
/* File: src/main.c */
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include "vtep.h"

int main(int argc, char **argv) {
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <local_ip> <vni> <peer_ip> [peer_ip ...]\n", argv[0]);
        return 1;
    }

    vtep_config_t cfg = {0};
    cfg.udp_port = VXLAN_PORT_IANA;
    cfg.vni = (uint32_t)atoi(argv[2]);
    snprintf(cfg.tap_name, sizeof(cfg.tap_name), "tap-vni%u", cfg.vni);
    snprintf(cfg.underlay_iface, sizeof(cfg.underlay_iface), "eth0");

    struct in_addr ia;
    if (!inet_aton(argv[1], &ia)) {
        fprintf(stderr, "Invalid local IP\n");
        return 1;
    }
    cfg.local_ip = ntohl(ia.s_addr);

    /* Add BUM peers */
    for (int i = 3; i < argc && cfg.bum_count < VTEP_BUM_LIST_MAX; i++) {
        if (!inet_aton(argv[i], &ia)) continue;
        cfg.bum_list[cfg.bum_count++].vtep_ip = ntohl(ia.s_addr);
    }

    /* Fake local MAC (use real NIC MAC in production) */
    uint8_t fake_mac[] = {0x02, 0x00, 0x00, 0x00, 0x00, 0x01};
    memcpy(cfg.local_mac, fake_mac, ETH_ALEN);

    vtep_t *vtep = vtep_create(&cfg);
    if (!vtep) {
        fprintf(stderr, "vtep_create failed\n");
        return 1;
    }

    int ret = vtep_run(vtep);
    vtep_destroy(vtep);
    return ret;
}
```

### 14.7 Build

```bash
# CMakeLists.txt
cmake_minimum_required(VERSION 3.16)
project(vxlan_vtep C)
set(CMAKE_C_STANDARD 11)
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -Wall -Wextra -O2 -g -fsanitize=address")
add_executable(vxlan_vtep
    src/main.c src/vtep.c src/fdb.c src/checksum.c)
target_include_directories(vxlan_vtep PRIVATE src)
target_link_libraries(vxlan_vtep pthread)

# Build:
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run (requires root for TUN/TAP):
sudo ./vxlan_vtep 192.168.10.1 100 192.168.10.2 192.168.10.3
```

---

## 15. Rust Implementation: Software VTEP

### 15.1 Cargo.toml

```toml
[package]
name = "vxlan-vtep"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio = { version = "1", features = ["full"] }
bytes = "1"
thiserror = "1"
tracing = "0.1"
tracing-subscriber = "0.3"
dashmap = "5"        # concurrent hashmap for FDB
fnv = "1"            # FNV hasher

[dev-dependencies]
tokio-test = "0.4"
```

### 15.2 Protocol Types

```rust
// src/proto.rs
use std::fmt;

pub const ETH_ALEN: usize = 6;
pub const VXLAN_PORT_IANA: u16 = 4789;
pub const VXLAN_PORT_LINUX: u16 = 8472;
pub const VXLAN_FLAG_I: u8 = 0x08;     // VNI valid flag
pub const VXLAN_HDR_SIZE: usize = 8;
pub const ETH_HDR_SIZE: usize = 14;
pub const IPV4_HDR_SIZE: usize = 20;
pub const UDP_HDR_SIZE: usize = 8;
pub const VXLAN_OVERHEAD: usize = ETH_HDR_SIZE + IPV4_HDR_SIZE + UDP_HDR_SIZE + VXLAN_HDR_SIZE;

#[derive(Clone, Copy, PartialEq, Eq, Hash, Debug)]
pub struct MacAddr(pub [u8; ETH_ALEN]);

impl MacAddr {
    pub const BROADCAST: MacAddr = MacAddr([0xFF; ETH_ALEN]);
    pub const ZERO: MacAddr = MacAddr([0x00; ETH_ALEN]);

    pub fn is_broadcast(&self) -> bool { self.0 == [0xFF; ETH_ALEN] }
    pub fn is_multicast(&self) -> bool { self.0[0] & 0x01 != 0 }
    pub fn is_bum(&self) -> bool { self.is_broadcast() || self.is_multicast() }
}

impl fmt::Display for MacAddr {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{:02x}:{:02x}:{:02x}:{:02x}:{:02x}:{:02x}",
            self.0[0], self.0[1], self.0[2], self.0[3], self.0[4], self.0[5])
    }
}

/// VXLAN header (8 bytes)
/// Byte 0:   flags (bit 3 = I flag, must be set)
/// Bytes 1-3: reserved
/// Bytes 4-6: VNI (24-bit, big-endian)
/// Byte 7:   reserved
#[derive(Debug, Clone, Copy)]
pub struct VxlanHeader {
    pub flags: u8,
    pub vni: u32,   // 24-bit VNI (stored as u32, top byte unused)
}

impl VxlanHeader {
    pub fn new(vni: u32) -> Self {
        assert!(vni <= 0xFFFFFF, "VNI must be 24-bit");
        VxlanHeader { flags: VXLAN_FLAG_I, vni }
    }

    /// Parse from 8-byte slice
    pub fn parse(raw: &[u8]) -> Option<Self> {
        if raw.len() < VXLAN_HDR_SIZE { return None; }
        if raw[0] & VXLAN_FLAG_I == 0 { return None; } // I-flag required
        let vni = ((raw[4] as u32) << 16) | ((raw[5] as u32) << 8) | (raw[6] as u32);
        Some(VxlanHeader { flags: raw[0], vni })
    }

    /// Serialize into 8-byte array
    pub fn to_bytes(&self) -> [u8; VXLAN_HDR_SIZE] {
        let mut b = [0u8; VXLAN_HDR_SIZE];
        b[0] = self.flags;
        // bytes 1-3: reserved = 0
        b[4] = ((self.vni >> 16) & 0xFF) as u8;
        b[5] = ((self.vni >>  8) & 0xFF) as u8;
        b[6] = ((self.vni      ) & 0xFF) as u8;
        // byte 7: reserved = 0
        b
    }
}

/// Parse MAC from Ethernet frame
pub fn parse_eth_src_dst(frame: &[u8]) -> Option<(MacAddr, MacAddr)> {
    if frame.len() < ETH_HDR_SIZE { return None; }
    let mut dst = [0u8; ETH_ALEN];
    let mut src = [0u8; ETH_ALEN];
    dst.copy_from_slice(&frame[0..6]);
    src.copy_from_slice(&frame[6..12]);
    Some((MacAddr(dst), MacAddr(src)))
}

/// FNV-1a hash of inner Ethernet frame headers for UDP src port entropy
pub fn entropy_src_port(inner_frame: &[u8]) -> u16 {
    if inner_frame.len() < ETH_HDR_SIZE + IPV4_HDR_SIZE {
        return 49152;
    }
    let ethertype = u16::from_be_bytes([inner_frame[12], inner_frame[13]]);
    if ethertype != 0x0800 { return 50000; } // not IPv4

    let ip_start = ETH_HDR_SIZE;
    let ihl = (inner_frame[ip_start] & 0x0F) as usize * 4;
    let proto = inner_frame[ip_start + 9];
    let src_ip = u32::from_be_bytes(inner_frame[ip_start+12..ip_start+16].try_into().unwrap());
    let dst_ip = u32::from_be_bytes(inner_frame[ip_start+16..ip_start+20].try_into().unwrap());

    let (sport, dport) = {
        let t = ip_start + ihl;
        if t + 4 <= inner_frame.len() {
            let s = u16::from_be_bytes([inner_frame[t], inner_frame[t+1]]);
            let d = u16::from_be_bytes([inner_frame[t+2], inner_frame[t+3]]);
            (s, d)
        } else { (0, 0) }
    };

    // FNV-1a
    let mut h: u32 = 2166136261;
    let mix = |h: u32, b: u8| (h ^ b as u32).wrapping_mul(16777619);
    let h = [src_ip >> 24, src_ip >> 16, src_ip >> 8, src_ip,
             dst_ip >> 24, dst_ip >> 16, dst_ip >> 8, dst_ip]
        .iter().fold(h, |h, &b| mix(h, b as u8));
    let h = mix(mix(h, (sport >> 8) as u8), (sport & 0xFF) as u8);
    let h = mix(mix(h, (dport >> 8) as u8), (dport & 0xFF) as u8);
    let h = mix(h, proto);

    49152u16.wrapping_add((h & 0x3FFF) as u16)
}
```

### 15.3 Forwarding Database

```rust
// src/fdb.rs
use std::net::Ipv4Addr;
use std::time::{Duration, Instant};
use dashmap::DashMap;
use crate::proto::MacAddr;

pub const FDB_TTL: Duration = Duration::from_secs(300);

#[derive(Debug, Clone)]
pub struct FdbEntry {
    pub remote_vtep_ip: Option<Ipv4Addr>,   // None = local
    pub last_seen: Instant,
    pub is_static: bool,
}

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct FdbKey {
    pub vni: u32,
    pub mac: MacAddr,
}

/// Lock-free concurrent Forwarding Database
pub struct Fdb {
    table: DashMap<FdbKey, FdbEntry>,
}

impl Fdb {
    pub fn new() -> Self {
        Fdb { table: DashMap::new() }
    }

    pub fn insert(&self, vni: u32, mac: MacAddr, remote_vtep_ip: Option<Ipv4Addr>, is_static: bool) {
        let key = FdbKey { vni, mac };
        self.table.insert(key, FdbEntry {
            remote_vtep_ip,
            last_seen: Instant::now(),
            is_static,
        });
    }

    pub fn lookup(&self, vni: u32, mac: &MacAddr) -> Option<Option<Ipv4Addr>> {
        let key = FdbKey { vni, mac: *mac };
        self.table.get(&key).map(|e| e.remote_vtep_ip)
    }

    pub fn remove(&self, vni: u32, mac: &MacAddr) {
        let key = FdbKey { vni, mac: *mac };
        self.table.remove(&key);
    }

    /// Remove aged dynamic entries
    pub fn age(&self) {
        self.table.retain(|_, v| {
            v.is_static || v.last_seen.elapsed() < FDB_TTL
        });
    }

    pub fn len(&self) -> usize { self.table.len() }
}
```

### 15.4 VTEP Core

```rust
// src/vtep.rs
use std::net::{Ipv4Addr, SocketAddrV4, UdpSocket};
use std::io;
use std::sync::Arc;
use bytes::BytesMut;
use tracing::{debug, warn, error, info};

use crate::proto::*;
use crate::fdb::Fdb;

pub struct VtepConfig {
    pub local_ip: Ipv4Addr,
    pub vni: u32,
    pub udp_port: u16,
    pub bum_peers: Vec<Ipv4Addr>,
}

pub struct Vtep {
    config: VtepConfig,
    fdb: Arc<Fdb>,
    udp: UdpSocket,
}

impl Vtep {
    pub fn new(config: VtepConfig) -> io::Result<Self> {
        let bind_addr = SocketAddrV4::new(Ipv4Addr::UNSPECIFIED, config.udp_port);
        let udp = UdpSocket::bind(bind_addr)?;
        info!("VTEP bound to {:?}", bind_addr);

        Ok(Vtep {
            config,
            fdb: Arc::new(Fdb::new()),
            udp,
        })
    }

    /// Encapsulate inner Ethernet frame and send to remote VTEP
    pub fn encap_send(&self, inner_frame: &[u8], dst_vtep: Ipv4Addr) -> io::Result<()> {
        let total_len = VXLAN_HDR_SIZE + inner_frame.len();
        let mut buf = BytesMut::with_capacity(total_len);

        // VXLAN header
        let vxhdr = VxlanHeader::new(self.config.vni);
        buf.extend_from_slice(&vxhdr.to_bytes());

        // Inner frame
        buf.extend_from_slice(inner_frame);

        let dst = SocketAddrV4::new(dst_vtep, self.config.udp_port);
        self.udp.send_to(&buf, dst)?;
        debug!("encap_send: VNI={} dst={} len={}", self.config.vni, dst_vtep, buf.len());
        Ok(())
    }

    /// BUM flood to all configured peers
    pub fn bum_flood(&self, inner_frame: &[u8]) {
        for &peer in &self.config.bum_peers {
            if let Err(e) = self.encap_send(inner_frame, peer) {
                warn!("BUM flood to {} failed: {}", peer, e);
            }
        }
    }

    /// Process an inner frame from the local VM (TAP → VXLAN)
    pub fn process_from_vm(&self, frame: &[u8]) {
        let (dst_mac, src_mac) = match parse_eth_src_dst(frame) {
            Some(x) => x,
            None => { warn!("frame too short"); return; }
        };

        // Learn source MAC → local
        self.fdb.insert(self.config.vni, src_mac, None, false);

        if dst_mac.is_bum() {
            debug!("BUM frame from VM, flooding");
            self.bum_flood(frame);
            return;
        }

        // Unicast: FDB lookup
        match self.fdb.lookup(self.config.vni, &dst_mac) {
            Some(Some(remote_vtep)) => {
                debug!("FDB hit: {} → {}", dst_mac, remote_vtep);
                if let Err(e) = self.encap_send(frame, remote_vtep) {
                    error!("encap_send failed: {}", e);
                }
            }
            Some(None) => {
                // Local MAC — shouldn't arrive at VTEP, but handle gracefully
                debug!("FDB: local MAC, ignoring");
            }
            None => {
                debug!("FDB miss for {}, flooding", dst_mac);
                self.bum_flood(frame);
            }
        }
    }

    /// Process a received VXLAN packet from underlay (UDP → TAP)
    /// Returns the decapsulated inner frame if successful
    pub fn process_from_underlay(&self, udp_payload: &[u8], src_vtep: Ipv4Addr) -> Option<Vec<u8>> {
        let vxhdr = VxlanHeader::parse(udp_payload)?;

        if vxhdr.vni != self.config.vni {
            debug!("VNI mismatch: got {} expected {}", vxhdr.vni, self.config.vni);
            return None;
        }

        let inner_frame = &udp_payload[VXLAN_HDR_SIZE..];
        if inner_frame.len() < ETH_HDR_SIZE {
            warn!("Inner frame too short");
            return None;
        }

        // MAC learning from received frame
        let (_, src_mac) = parse_eth_src_dst(inner_frame)?;
        self.fdb.insert(self.config.vni, src_mac, Some(src_vtep), false);
        debug!("Learned {} → {} (VNI={})", src_mac, src_vtep, self.config.vni);

        Some(inner_frame.to_vec())
    }

    /// Receive loop: blocks on UDP socket
    pub fn recv_loop<F>(&self, mut deliver: F) -> io::Result<()>
    where
        F: FnMut(&[u8]),   // delivers inner frame to TAP/VM
    {
        let mut buf = vec![0u8; 9216];
        loop {
            let (n, from) = self.udp.recv_from(&mut buf)?;
            let src_vtep = match from {
                std::net::SocketAddr::V4(a) => *a.ip(),
                _ => continue,
            };

            if let Some(inner) = self.process_from_underlay(&buf[..n], src_vtep) {
                deliver(&inner);
            }
        }
    }

    pub fn fdb(&self) -> Arc<Fdb> { Arc::clone(&self.fdb) }
}
```

### 15.5 Main with Tokio Async

```rust
// src/main.rs
use std::net::Ipv4Addr;
use std::str::FromStr;
use tracing_subscriber;
use crate::vtep::{Vtep, VtepConfig};

mod proto;
mod fdb;
mod vtep;

fn main() {
    tracing_subscriber::fmt::init();

    let args: Vec<String> = std::env::args().collect();
    if args.len() < 3 {
        eprintln!("Usage: {} <local_ip> <vni> [peer_ip...]", args[0]);
        std::process::exit(1);
    }

    let local_ip = Ipv4Addr::from_str(&args[1]).expect("Invalid local IP");
    let vni: u32 = args[2].parse().expect("Invalid VNI");
    let bum_peers: Vec<Ipv4Addr> = args[3..]
        .iter()
        .filter_map(|s| Ipv4Addr::from_str(s).ok())
        .collect();

    let cfg = VtepConfig {
        local_ip,
        vni,
        udp_port: proto::VXLAN_PORT_IANA,
        bum_peers,
    };

    let vtep = Vtep::new(cfg).expect("Failed to create VTEP");
    tracing::info!("VTEP started: local={} vni={}", local_ip, vni);

    // In production: spawn TAP reader thread + recv_loop thread
    // Here: simplified recv only (no TAP without root)
    vtep.recv_loop(|inner_frame| {
        if let Some((dst, src)) = proto::parse_eth_src_dst(inner_frame) {
            tracing::info!("Inner frame: {} → {} ({} bytes)", src, dst, inner_frame.len());
        }
    }).expect("recv_loop failed");
}
```

### 15.6 Tests

```rust
// src/tests/test_proto.rs
#[cfg(test)]
mod tests {
    use crate::proto::*;

    #[test]
    fn test_vxlan_header_roundtrip() {
        let vni = 100u32;
        let hdr = VxlanHeader::new(vni);
        let bytes = hdr.to_bytes();

        // Verify I-flag
        assert_eq!(bytes[0], VXLAN_FLAG_I);
        // Verify reserved bytes
        assert_eq!(bytes[1], 0);
        assert_eq!(bytes[2], 0);
        assert_eq!(bytes[3], 0);
        // Verify VNI bytes
        assert_eq!(bytes[4], 0x00);  // vni=100=0x64, byte4=0
        assert_eq!(bytes[5], 0x00);  // byte5=0
        assert_eq!(bytes[6], 0x64);  // byte6=100
        assert_eq!(bytes[7], 0);

        // Parse back
        let parsed = VxlanHeader::parse(&bytes).unwrap();
        assert_eq!(parsed.vni, vni);
    }

    #[test]
    fn test_vxlan_header_max_vni() {
        let vni = 0xFFFFFF;  // max 24-bit
        let hdr = VxlanHeader::new(vni);
        let bytes = hdr.to_bytes();
        let parsed = VxlanHeader::parse(&bytes).unwrap();
        assert_eq!(parsed.vni, vni);
    }

    #[test]
    fn test_vxlan_header_i_flag_required() {
        let mut bytes = [0u8; 8];
        bytes[0] = 0x00; // I-flag NOT set
        bytes[4] = 0x00;
        bytes[5] = 0x00;
        bytes[6] = 0x64; // VNI=100
        assert!(VxlanHeader::parse(&bytes).is_none());
    }

    #[test]
    fn test_mac_broadcast() {
        let mac = MacAddr::BROADCAST;
        assert!(mac.is_broadcast());
        assert!(mac.is_bum());
    }

    #[test]
    fn test_mac_multicast() {
        let mac = MacAddr([0x01, 0x00, 0x5e, 0x00, 0x00, 0x01]);
        assert!(mac.is_multicast());
        assert!(mac.is_bum());
        assert!(!mac.is_broadcast());
    }

    #[test]
    fn test_entropy_port_range() {
        // Build a minimal IPv4/TCP inner frame
        let mut frame = vec![0u8; 14 + 20 + 4];
        frame[12] = 0x08;  // EtherType = 0x0800 (IPv4)
        frame[13] = 0x00;
        frame[14] = 0x45;  // IPv4, IHL=5
        frame[23] = 6;     // TCP
        // src IP 10.0.0.1, dst IP 10.0.0.2
        frame[26] = 10; frame[27] = 0; frame[28] = 0; frame[29] = 1;
        frame[30] = 10; frame[31] = 0; frame[32] = 0; frame[33] = 2;
        // src port 1234, dst port 80
        frame[34] = 0x04; frame[35] = 0xD2;  // 1234
        frame[36] = 0x00; frame[37] = 0x50;  // 80

        let port = entropy_src_port(&frame);
        assert!(port >= 49152, "Port {} < 49152", port);
        assert!(port <= 65535, "Port {} > 65535", port);
    }

    #[test]
    fn test_fdb_insert_lookup() {
        use crate::fdb::Fdb;
        use std::net::Ipv4Addr;

        let fdb = Fdb::new();
        let mac = MacAddr([0xaa, 0xbb, 0xcc, 0x11, 0x22, 0x33]);
        let vtep_ip = Ipv4Addr::new(10, 0, 0, 2);

        fdb.insert(100, mac, Some(vtep_ip), false);

        let result = fdb.lookup(100, &mac);
        assert!(result.is_some());
        assert_eq!(result.unwrap(), Some(vtep_ip));

        // Different VNI should miss
        assert!(fdb.lookup(200, &mac).is_none());
    }

    #[test]
    fn test_fdb_aging() {
        use crate::fdb::{Fdb, FDB_TTL};
        use crate::fdb::FdbKey;
        use std::net::Ipv4Addr;
        use dashmap::DashMap;

        // Aging is time-based; test that static entries survive
        let fdb = Fdb::new();
        let mac = MacAddr([0x01, 0x02, 0x03, 0x04, 0x05, 0x06]);
        fdb.insert(100, mac, Some(Ipv4Addr::new(10, 0, 0, 1)), true /* static */);

        fdb.age();  // static entries should survive

        assert!(fdb.lookup(100, &mac).is_some());
    }
}
```

### 15.7 Build and Run

```bash
# Build
cargo build --release

# Run tests
cargo test

# Fuzz testing with cargo-fuzz
cargo install cargo-fuzz
cargo fuzz init
# Create fuzz target for VXLAN header parsing:
cat > fuzz/fuzz_targets/fuzz_vxlan_parse.rs << 'EOF'
#![no_main]
use libfuzzer_sys::fuzz_target;
use vxlan_vtep::proto::VxlanHeader;

fuzz_target!(|data: &[u8]| {
    let _ = VxlanHeader::parse(data);
});
EOF
cargo fuzz run fuzz_vxlan_parse

# Benchmark with criterion
cargo bench
```

---

## 16. Underlay Network Design

### 16.1 Physical Topology: Spine-Leaf

The spine-leaf (Clos) topology is the standard for VXLAN deployments:

```
                    Spine-Leaf Topology for VXLAN

    Spine-1 (AS 65000)         Spine-2 (AS 65000)
    [Route Reflector]           [Route Reflector]
         │    │                      │    │
         │    └──────────────────────┘    │
         │                               │
    ┌────┴────┐  ┌─────────┐  ┌─────────┴────┐
    │ Leaf-1  │  │ Leaf-2  │  │   Leaf-3     │
    │ VTEP-A  │  │ VTEP-B  │  │   VTEP-C     │
    │ AS 65001│  │ AS 65001│  │   AS 65001   │
    └────┬────┘  └────┬────┘  └────┬─────────┘
         │            │            │
      [VM-A]       [VM-B]       [VM-C]
      VNI 100      VNI 100      VNI 200

Underlay IP plan:
  Spine-1 loopback: 10.0.0.10/32
  Spine-2 loopback: 10.0.0.11/32
  Leaf-1  loopback: 10.0.0.1/32  ← VTEP-A IP
  Leaf-2  loopback: 10.0.0.2/32  ← VTEP-B IP
  Leaf-3  loopback: 10.0.0.3/32  ← VTEP-C IP

  Point-to-point links: /31 subnets (RFC 3021)
    Leaf-1 ↔ Spine-1: 192.168.1.0/31 and 192.168.1.2/31 (two uplinks)
    Leaf-1 ↔ Spine-2: 192.168.2.0/31
```

### 16.2 Underlay Routing: eBGP vs OSPF

**eBGP Unnumbered (recommended for modern DC):**
```bash
# FRR: eBGP unnumbered (uses IPv6 link-local for peering)
# No IP config needed on point-to-point links
router bgp 65001
  bgp router-id 10.0.0.1
  neighbor SPINE interface remote-as external   # all interfaces
  neighbor SPINE bfd                            # BFD for fast detection

  address-family ipv4 unicast
    neighbor SPINE activate
    redistribute connected route-map LOOPBACK
  exit-address-family
  
  address-family l2vpn evpn
    neighbor SPINE activate
    advertise-all-vni
  exit-address-family
```

**OSPF (single-area for small deployments):**
```bash
router ospf
  ospf router-id 10.0.0.1
  network 0.0.0.0/0 area 0   # all interfaces in area 0
  passive-interface default  # don't send OSPF on access ports
  no passive-interface eth0  # uplink to spine
```

### 16.3 ECMP Configuration

```bash
# Enable ECMP (Linux kernel)
echo 1 > /proc/sys/net/ipv4/fib_multipath_hash_policy  # L4 hashing
echo 2 > /proc/sys/net/ipv4/fib_multipath_hash_policy  # L4 with inner headers

# FRR: ECMP
router bgp 65001
  maximum-paths 8          # up to 8 ECMP paths to spine
  maximum-paths ibgp 8
```

### 16.4 BFD (Bidirectional Forwarding Detection)

BFD provides sub-second failure detection for BGP sessions:

```bash
# FRR BFD config
bfd
  peer 192.168.1.0
    detect-multiplier 3
    receive-interval 300    # 300ms
    transmit-interval 300   # 300ms
  !

router bgp 65001
  neighbor 192.168.1.0 bfd  # enable BFD for this peer
```

---

## 17. Threat Model and Security Design

### 17.1 Threat Model (STRIDE)

```
VXLAN Threat Surface:

  [Physical]         [Underlay]         [VTEP]         [Overlay]
      │                  │                │                │
  Physical            UDP:4789           FDB              VMs
  Access              Spoofing          Poisoning       Escape

STRIDE Analysis:
┌────────────────┬──────────────────────────────────────────────────────┐
│ Spoofing       │ Attacker forges outer src IP → VTEP accepts as       │
│                │ legitimate VTEP; MAC learning poisoned                │
│                │ Mitigation: IPsec/WireGuard tunnel authentication    │
├────────────────┼──────────────────────────────────────────────────────┤
│ Tampering      │ Modify inner frames in transit (no auth in VXLAN)    │
│                │ Mitigation: Encrypt underlay (IPsec ESP, WireGuard)  │
├────────────────┼──────────────────────────────────────────────────────┤
│ Repudiation    │ No audit trail for VTEP-to-VTEP communication        │
│                │ Mitigation: NetFlow/IPFIX logging, eBPF audit        │
├────────────────┼──────────────────────────────────────────────────────┤
│ Info Disclosure│ Inner frames (tenant data) transmitted cleartext     │
│                │ over underlay; eavesdrop if underlay compromised     │
│                │ Mitigation: per-tunnel encryption, PTP-level auth    │
├────────────────┼──────────────────────────────────────────────────────┤
│ DoS            │ UDP:4789 open; BUM amplification; FDB flooding       │
│                │ Mitigation: rate-limit, ACL, anti-spoofing, port ACL │
├────────────────┼──────────────────────────────────────────────────────┤
│ Elevation      │ VM escape → host network access → rogue VTEP         │
│                │ Mitigation: strict VTEP source IP allowlist, BGP auth│
└────────────────┴──────────────────────────────────────────────────────┘
```

### 17.2 Attack Vectors and Mitigations

**Attack 1: VXLAN Packet Injection**

Any host in the underlay can craft VXLAN UDP packets on port 4789 and inject arbitrary Ethernet frames into any VNI. Standard VXLAN has NO authentication.

```
Mitigation:
  Option A: IPsec (ESP) for all VTEP-to-VTEP traffic
    kernel-level, transparent to VXLAN
    IKEv2 with certificate auth per VTEP
    xfrm policies: require ESP for src/dst VTEP IP pairs

  Option B: WireGuard (preferred, simpler)
    Each VTEP gets a WireGuard keypair
    VXLAN UDP traffic sent over WireGuard tunnel
    WireGuard handles: auth, encryption, replay protection

  Option C: Underlay ACLs
    Only allow UDP:4789 from known VTEP IPs
    uRPF (Unicast Reverse Path Forwarding) on underlay
    Less secure (no crypto), but better than nothing
```

**Setting up WireGuard overlay for VTEP-to-VTEP:**
```bash
# On VTEP-A (10.0.0.1):
wg genkey | tee vtep-a-private.key | wg pubkey > vtep-a-public.key
ip link add wg0 type wireguard
ip addr add 172.30.0.1/32 dev wg0          # WireGuard underlay-of-underlay IP
wg set wg0 private-key vtep-a-private.key listen-port 51820

# Add peer (VTEP-B):
wg set wg0 peer <VTEP-B-pubkey> \
    allowed-ips 172.30.0.2/32 \
    endpoint 10.0.0.2:51820

# Route VXLAN traffic over WireGuard:
ip route add 10.0.0.2/32 dev wg0    # VTEP-B's VTEP IP routed through WireGuard
# Now VXLAN UDP to 10.0.0.2:4789 goes through encrypted WireGuard tunnel
```

**Attack 2: FDB Poisoning**

In flood-and-learn mode, attacker crafts VXLAN packets with spoofed inner-src-MAC → VTEP learns wrong MAC→VTEP mapping → traffic hijacked.

```
Mitigation:
  - Use BGP EVPN control plane (disable data-plane learning: nolearning)
  - Only BGP-authenticated sources can update FDB
  - BGP sessions authenticated with MD5 or TCP-AO
  - Static FDB entries for critical MACs

ip link add vxlan100 type vxlan ... nolearning  ← disable data-plane learning

# BGP MD5 auth (FRR):
router bgp 65001
  neighbor 10.0.0.2 password StrongBGPPassword123!
```

**Attack 3: BUM Amplification**

Attacker sends BUM frames to flood all VTEPs (amplification attack if multicast used).

```
Mitigation:
  - Rate-limit BUM traffic per VNI at VTEP ingress
  - Use ARP suppression to eliminate most BUM
  - Set VM-to-VM BUM rate limits:
    tc qdisc add dev tap0 root tbf rate 100mbit burst 1mb latency 50ms
  - Disable multicast on underlay; use head-end replication with explicit peer list
  - IGMP snooping on all L2 switches
```

**Attack 4: VM Escape / Rogue VTEP**

Compromised VM uses raw sockets to inject VXLAN packets directly from the host.

```
Mitigation:
  - seccomp-bpf: block socket(AF_PACKET) and socket(AF_RAW) inside containers
  - Network namespaces: VMs/containers in separate netns cannot access host UDP:4789
  - Egress ACL: only allow UDP:4789 from VTEP process user/netns
  - IPtables rule to drop VXLAN from VM interfaces:
    iptables -I FORWARD -i vm0 -p udp --dport 4789 -j DROP
    iptables -I FORWARD -i vm0 -p udp --sport 4789 -j DROP
```

### 17.3 BGP EVPN Security

```bash
# BGP session security:
router bgp 65001
  neighbor 10.0.0.10 password <strong-password>    # MD5 auth
  # Or better: TCP-AO (kernel 5.14+)
  neighbor 10.0.0.10 ao-key-chain MY_CHAIN

# RPKI for BGP route origin validation:
# Prevents route hijacking in the underlay
rpki
  server 192.168.1.200 port 3323 preference 1
  polling-period 300
route-map RPKI-VALIDATE permit 10
  match rpki valid

# Route filtering: only accept EVPN routes with our own RTs
router bgp 65001
  address-family l2vpn evpn
    neighbor 10.0.0.10 route-map EVPN-IMPORT in
route-map EVPN-IMPORT permit 10
  match evpn route-type 2
  match community 65001:100
```

### 17.4 Encryption in Transit

For multi-tenant clouds where tenants cannot trust the underlay:

```
                  Encryption Architecture

  Tenant VM ──── (plaintext inner frame) ──── VTEP
                                               │
                    WireGuard / IPsec tunnel   │
                    (outer: authenticated,     │
                     encrypted)                │
                                               │
  Remote VTEP ──── (decrypted outer) ─────────┘
                         │
                    (plaintext inner frame delivered to remote VM)

  Per-VNI vs Per-VTEP-pair encryption:
    Per-VTEP-pair: one WireGuard tunnel per VTEP pair; simpler, less keys
    Per-VNI:       separate key per tenant VNI; stronger isolation; complex key mgmt
                   implemented as: IPsec with VNI in SPD selector
```

### 17.5 Underlay Hardening

```bash
# uRPF (anti-spoofing):
# On all VTEP-facing interfaces:
sysctl -w net.ipv4.conf.eth0.rp_filter=1   # strict mode

# Port-based ACL (iptables/nftables):
nft add table ip vxlan_filter
nft add chain ip vxlan_filter input { type filter hook input priority 0; }
# Only allow VXLAN UDP from known VTEP IPs:
nft add rule ip vxlan_filter input \
    ip protocol udp udp dport 4789 \
    ip saddr != { 10.0.0.2, 10.0.0.3, 10.0.0.4 } \
    drop

# Block VXLAN from VM-facing interfaces entirely:
nft add rule ip vxlan_filter input \
    iifname "tap*" udp dport 4789 drop
```

---

## 18. Performance: Tuning, Benchmarks, Profiling

### 18.1 Overhead Analysis

```
VXLAN per-packet overhead:
  50 bytes outer headers (IPv4) or 70 bytes (IPv6)
  
CPU operations per packet (software VTEP, no offload):
  TX path: FDB lookup + entropy hash + header construction + udp sendmsg
    ≈ 2-5 µs per packet on modern CPU
    ≈ 200K-500K pps per core for 1500-byte frames
    ≈ 5-10 Gbps per core

  RX path: UDP recv + VXLAN validate + strip + deliver to netdev
    ≈ 2-4 µs per packet
    ≈ 250K-500K pps per core

With NIC offload (ConnectX-5/6):
  TX: CPU builds inner frame; NIC applies VXLAN encap in hardware
  RX: NIC strips VXLAN; CPU sees inner frame directly
  Throughput: 25-100 Gbps per port at line rate
  CPU overhead: <5% for VXLAN (vs ~80% without offload)
```

### 18.2 Linux Kernel Tuning

```bash
# Increase socket buffer sizes for high throughput:
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.core.rmem_default=67108864
sysctl -w net.core.netdev_max_backlog=250000

# Enable RX multi-queue / RSS for VXLAN:
# Ensure NIC does inner-packet RSS for VXLAN:
ethtool -K eth0 ntuple on          # flow director rules
# Some NICs need explicit VXLAN port registration:
# Kernel does this via udp_tunnel API

# Enable GRO (Generic Receive Offload) — coalesces VXLAN packets:
ethtool -K eth0 gro on

# Tune VXLAN device:
ip link set vxlan100 txqueuelen 10000

# Enable NAPI for high-throughput:
# (automatic on modern kernels with proper driver)

# Jumbo frames on underlay (critical for performance):
ip link set eth0 mtu 9000
ip link set vxlan100 mtu 8950   # 9000 - 50 VXLAN overhead

# CPU affinity for vxlan process:
taskset -c 2,3 ./vxlan_vtep 10.0.0.1 100

# IRQ affinity for NIC queues:
cat /proc/interrupts | grep eth0
echo 4 > /proc/irq/<IRQ>/smp_affinity_list   # pin to CPU 4
```

### 18.3 Benchmarking VXLAN Throughput

```bash
# Test 1: Baseline throughput with iperf3
# On receiver (VTEP-B side, inside VM-B):
iperf3 -s -B 10.1.0.2

# On sender (inside VM-A):
iperf3 -c 10.1.0.2 -t 30 -P 8 -M 1450   # 8 parallel streams, MSS=1450

# Test 2: PPS with pktgen (kernel packet generator)
modprobe pktgen
pgset "pkt_size 64"        # minimum size frames for max PPS
pgset "dst_mac aa:bb:cc:dd:ee:ff"
pgset "dst 10.0.0.2"
pgset "count 10000000"
pgset "start"

# Test 3: latency with qperf
qperf 10.1.0.2 tcp_lat udp_lat    # inside VXLAN overlay

# Expected results (software VTEP, no offload, 10GbE):
#   Large frame (1450B): ~9.5 Gbps (limited by 10GbE)
#   Small frame (64B):   ~2-5 Mpps (CPU-limited)
#   Latency vs native:   +20-40µs additional RTT
```

### 18.4 eBPF/XDP Acceleration

XDP (eXpress Data Path) can accelerate VXLAN decapsulation at line rate before the kernel networking stack:

```c
/* XDP VXLAN decapsulation sketch (simplified) */
SEC("xdp")
int xdp_vxlan_decap(struct xdp_md *ctx) {
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end) return XDP_DROP;
    if (eth->h_proto != htons(ETH_P_IP)) return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end) return XDP_DROP;
    if (ip->protocol != IPPROTO_UDP) return XDP_PASS;

    struct udphdr *udp = (void *)ip + (ip->ihl * 4);
    if ((void *)(udp + 1) > data_end) return XDP_DROP;
    if (udp->dest != htons(4789)) return XDP_PASS;  // not VXLAN

    struct vxlan_hdr *vxlan = (void *)(udp + 1);
    if ((void *)(vxlan + 1) > data_end) return XDP_DROP;
    if (!(vxlan->flags & VXLAN_FLAG_I)) return XDP_DROP;

    /* Adjust packet to remove outer headers */
    size_t outer_len = sizeof(*eth) + (ip->ihl * 4) + sizeof(*udp) + sizeof(*vxlan);
    if (bpf_xdp_adjust_head(ctx, outer_len) != 0) return XDP_DROP;

    /* Packet now starts at inner Ethernet frame */
    return XDP_PASS;  /* deliver inner frame to kernel */
}
```

---

## 19. VXLAN in Kubernetes and CNI Context

### 19.1 Kubernetes Network Model

Kubernetes requires every Pod to have a routable IP (RFC 2460). CNI plugins implement this using VXLAN overlays:

```
                Kubernetes VXLAN CNI

  Node-1 (10.0.0.1)                 Node-2 (10.0.0.2)
  ┌────────────────────┐            ┌────────────────────┐
  │ Pod-A: 10.244.1.2  │            │ Pod-B: 10.244.2.2  │
  │ Pod-C: 10.244.1.3  │            │ Pod-D: 10.244.2.3  │
  │      │              │            │      │              │
  │   cni0 bridge       │            │   cni0 bridge       │
  │   10.244.1.1        │            │   10.244.2.1        │
  │      │              │            │      │              │
  │   flannel.1/vxlan0  │            │   flannel.1/vxlan0  │
  │   VTEP: 10.0.0.1    │====UDP====>│   VTEP: 10.0.0.2   │
  └────────────────────┘            └────────────────────┘

  Pod-A → Pod-B:
    Pod-A sends to 10.244.2.2 → cni0 → flannel.1 (VXLAN)
    flannel.1 looks up: 10.244.2.0/24 → VTEP 10.0.0.2
    Encapsulates: outer IP 10.0.0.1 → 10.0.0.2, VNI = 1 (single overlay)
    Node-2 receives → flannel.1 decapsulates → cni0 → Pod-B
```

### 19.2 Flannel VXLAN

Flannel is the simplest Kubernetes VXLAN CNI:

```yaml
# kube-flannel ConfigMap
net-conf.json: |
  {
    "Network": "10.244.0.0/16",
    "Backend": {
      "Type": "vxlan",
      "VNI": 1,
      "Port": 8472,
      "GBP": false,
      "DirectRouting": false
    }
  }
```

Flannel stores its routing table in etcd. Each node learns other nodes' VTEP IPs and pod subnets from etcd.

### 19.3 Calico VXLAN

Calico uses VXLAN in `vxlan` mode, with BGP control plane replaced by bird/gobgp:

```yaml
# Calico installation with VXLAN
apiVersion: operator.tigera.io/v1
kind: Installation
metadata:
  name: default
spec:
  calicoNetwork:
    ipPools:
    - blockSize: 26
      cidr: 10.244.0.0/16
      encapsulation: VXLAN     # or VXLANCrossSubnet
      natOutgoing: Enabled
      nodeSelector: all()
```

`VXLANCrossSubnet`: only uses VXLAN for cross-subnet traffic; same-subnet uses direct routing.

### 19.4 Cilium eBPF with VXLAN

Cilium replaces iptables with eBPF and uses VXLAN via its own kernel bypass:

```yaml
# Cilium with VXLAN (Helm values)
tunnel: vxlan           # overlay mode
autoDirectNodeRoutes: false
nativeRoutingCIDR: ""

# Cilium uses:
# - BPF maps for FDB (not kernel bridge FDB)
# - XDP/TC BPF programs for encap/decap
# - cilium_vxlan netdev (metadata mode, external VNI routing)
# - L3 per-pod identity enforcement via VNI/mark
```

### 19.5 Network Policy Enforcement in VXLAN

```
Cilium/Calico enforcement points:

  Pod-A ──> [BPF egress TC hook] ──> vxlan0 ──> Node-2 ──> [BPF ingress TC hook] ──> Pod-B
              │ enforce policy              encap/decap     │ enforce policy
              │ check identity                              │ check identity (from VNI or BPF map)
              │ allow/deny                                  │ allow/deny

  Identity in VXLAN:
    Option 1: VNI per security group (Calico GBP, Cilium identity via VNI)
    Option 2: Out-of-band BPF map lookup using (src_pod_ip, dst_pod_ip)
    Option 3: VXLAN-GPE with NSH carrying security group ID
```

---

## 20. Operational Troubleshooting

### 20.1 Diagnostic Commands

```bash
# ── VTEP state ──
ip -d link show type vxlan          # all VXLAN interfaces
ip link show vxlan100               # specific VNI interface

# ── FDB ──
bridge fdb show dev vxlan100        # VXLAN FDB
bridge fdb show | grep permanent    # static entries only

# ── ARP suppression table ──
ip neigh show dev vxlan100

# ── Underlay routing ──
ip route show                        # routing table
ip route get 10.0.0.2               # verify path to remote VTEP
traceroute -U -p 4789 10.0.0.2     # trace VXLAN UDP path

# ── BGP EVPN (FRR) ──
vtysh -c "show bgp l2vpn evpn"               # all EVPN routes
vtysh -c "show bgp l2vpn evpn vni 100"      # routes for VNI 100
vtysh -c "show bgp l2vpn evpn route"         # detailed NLRI
vtysh -c "show evpn vni detail"              # VNI state
vtysh -c "show evpn mac vni 100"            # MAC table
vtysh -c "show evpn arp-cache vni 100"      # ARP suppression table
vtysh -c "show bgp l2vpn evpn route type 2" # Type-2 MAC/IP routes

# ── Packet capture ──
# Capture VXLAN packets on underlay:
tcpdump -i eth0 -n 'udp port 4789' -w vxlan.pcap
# Capture and decode (tshark):
tshark -i eth0 -f 'udp port 4789' -d udp.port==4789,vxlan \
    -T fields -e frame.number -e ip.src -e ip.dst \
    -e vxlan.vni -e eth.src_resolved -e eth.dst_resolved

# Capture inside overlay (on VXLAN interface):
tcpdump -i vxlan100 -n

# ── UDP socket ──
ss -u -n -l | grep 4789             # verify VXLAN socket open
ss -u -n | grep 4789                # active VXLAN UDP flows

# ── Tunnel stats ──
ip -s link show vxlan100            # TX/RX packet/byte counts
ethtool -S eth0 | grep -i vxlan    # NIC VXLAN offload counters
```

### 20.2 Common Issues

**Issue: VM-A cannot ping VM-B across VTEPs**

```bash
# Step 1: verify VTEP reachability
ping 10.0.0.2 -c3   # VTEP-A to VTEP-B underlay

# Step 2: verify VXLAN interface is up
ip link show vxlan100   # should show UP,LOWER_UP

# Step 3: check FDB
bridge fdb show dev vxlan100   # is VM-B's MAC present?

# Step 4: capture on VTEP-A's vxlan100 (overlay)
tcpdump -i vxlan100 host 10.1.0.2

# Step 5: capture on eth0 (underlay)
tcpdump -i eth0 udp port 4789

# Step 6: check MTU
ping 10.0.0.2 -s 1472 -M do   # test with full-size packet (1500 - 28 headers)
# If this fails but small ping succeeds → MTU issue
```

**Issue: ARP resolution fails**

```bash
# With BGP EVPN ARP suppression:
vtysh -c "show evpn arp-cache vni 100"  # is 10.1.0.2 in cache?
ip neigh show dev vxlan100               # ARP suppression entries

# If missing: check BGP Type-2 route was received:
vtysh -c "show bgp l2vpn evpn route type 2 rd 10.0.0.2:100"

# Without ARP suppression: check flood list
bridge fdb show dev vxlan100 | grep 00:00:00:00:00:00   # BUM entries
```

**Issue: BGP EVPN session not up**

```bash
vtysh -c "show bgp summary"              # is peer established?
vtysh -c "show bgp l2vpn evpn neighbor 10.0.0.10"  # per-peer state
# Common cause: EVPN AF not negotiated
vtysh -c "show bgp neighbor 10.0.0.10"  # check "l2vpn evpn" in capabilities
# Fix: both sides must have 'address-family l2vpn evpn' configured
```

**Issue: Asymmetric traffic (packets arrive, but replies don't return)**

```bash
# This usually means FDB miss on one side
# VTEP-B has FDB entry for VM-A but VTEP-A doesn't have VM-B

# Check VTEP-A's FDB:
bridge fdb show dev vxlan100 | grep vm-b-mac

# Check BGP Type-2 from VTEP-B:
vtysh -c "show bgp l2vpn evpn route type 2" | grep vm-b-mac

# Check route-target matches:
vtysh -c "show bgp l2vpn evpn import-rt"   # what RTs are we importing?
```

### 20.3 eBPF Observability

```bash
# Trace VXLAN packet events in kernel
bpftrace -e '
kprobe:vxlan_rcv {
  printf("VXLAN RX: proto=%d\n", arg2);
}'

# Count VXLAN TX/RX via tracepoints
bpftrace -e '
tracepoint:net:netif_receive_skb /
    strncmp(args->name, "vxlan", 5) == 0/ {
  @rx_bytes[args->name] = sum(args->len);
}'

# Use perf to profile VXLAN CPU usage
perf top -e cycles:k --kallsyms=/proc/kallsyms
# Look for: vxlan_rcv, vxlan_xmit, vxlan_encap
```

---

## 21. Failure Modes and Mitigations

### 21.1 Failure Mode Analysis

```
Failure Mode 1: Underlay Link Failure
  Impact: VXLAN traffic between VTEPs on that path drops
  Detection: BFD detects in <100ms; BGP reconverges
  Mitigation: ECMP multipath; at least 2 uplinks per leaf; BFD 300ms
  Recovery: BGP convergence ~1-3s; BFD-assisted: <500ms

Failure Mode 2: VTEP Software Crash
  Impact: All VMs on that host lose connectivity
  Detection: BFD session drops immediately; BGP hold-timer expires
  Mitigation: Systemd watchdog; process supervisor; BGP GRACEFUL-RESTART
  Recovery: Process restart ~5-30s; BGP reconverge ~30s without GR

Failure Mode 3: FDB Table Full
  Impact: Unknown unicast flooding increases; performance degrades
  Detection: Monitor 'bridge fdb show | wc -l' vs FDB_MAX_ENTRIES
  Mitigation: Correct FDB sizing; FDB aging; BGP EVPN (reduces learned entries)
  Recovery: Remove aged entries; increase kernel FDB limit

Failure Mode 4: MTU Black-hole
  Impact: Large packets silently dropped; TCP connections work but slowly
           (TCP falls back to smaller MSS after PMTUD, but not always)
  Detection: ping with -M do -s 1472 fails; MTR shows packet loss
  Mitigation: Set underlay MTU ≥ 1600 (prefer 9000 jumbo); set VM MTU to 1450
  Recovery: Fix MTU on underlay switches/interfaces

Failure Mode 5: BGP EVPN Route Withdrawal Flood
  Impact: Mass MAC withdrawal during maintenance causes traffic drops
  Detection: BGP update flood in logs; FDB entries disappearing
  Mitigation: EVPN graceful-restart; BGP LLGR (Long-Lived Graceful Restart)
  Recovery: BGP reconverge and re-advertise MACs

Failure Mode 6: ARP Storm
  Impact: CPU high on VTEPs handling ARP flooding
  Detection: High interrupt rate; tcpdump shows ARP storm
  Mitigation: Enable ARP suppression; limit ARP rate per VNI; BGP EVPN
  Recovery: Enable suppression; filter at VTEP ingress

Failure Mode 7: Split Brain (two VTEPs claim same MAC)
  Impact: Traffic bounces between VTEPs; VM-to-VM communication broken
  Scenario: VM migrated but old VTEP still advertising MAC
  Mitigation: BGP withdraw old Type-2 route on VM deregistration
              MAC mobility extended community increments sequence counter
  Recovery: Force BGP withdraw; sequence number resolves which is current
```

### 21.2 MAC Mobility (VM Migration)

EVPN handles VM migration via the MAC Mobility Extended Community:

```
MAC Mobility Extended Community:
  Type: 0x06, Sub-type: 0x00
  Flags: S (sticky) bit
  Sequence Number: monotonically increasing counter

When VM-A migrates from VTEP-1 to VTEP-2:
  VTEP-2 detects VM-A's MAC (via gratuitous ARP or local learning)
  VTEP-2 advertises Type-2 with MAC Mobility Community, seq=1
  VTEP-1 sees route with higher seq number from VTEP-2
  VTEP-1 withdraws its Type-2 for VM-A's MAC
  All VTEPs update FDB: VM-A's MAC → VTEP-2
  Migration complete; no traffic disruption after BGP convergence (~100-500ms)
```

---

## 22. Roll-out and Rollback Plan

### 22.1 Phased Roll-out

```
Phase 1: Lab Validation (2-4 weeks)
  □ Deploy spine-leaf fabric with test VTEPs
  □ Test flood-and-learn → BGP EVPN migration
  □ Validate ARP suppression behavior
  □ Test VM migration (live migration across VTEPs)
  □ Load test: measure throughput, latency, PPS
  □ Fault injection: link failures, VTEP crashes, BGP session drops

Phase 2: Canary (1-2 weeks)
  □ Deploy 2-3 leaf switches as VTEPs
  □ Migrate 5-10% of VMs to VXLAN overlay
  □ Monitor: BGP sessions, FDB table sizes, BUM rate, latency
  □ Validate policy (security groups) still enforced
  □ Verify L3 gateway function (inter-VNI routing)

Phase 3: Progressive Roll-out (4-8 weeks)
  □ Migrate by tenant or by rack
  □ Each leaf: drain → VXLAN config → BGP EVPN → undrain
  □ Monitor control plane convergence time
  □ Validate underlay MTU at each hop

Phase 4: Full Production
  □ All VTEPs running BGP EVPN
  □ Decommission old VLAN infrastructure
  □ Enable ARP suppression everywhere
  □ Enable WireGuard/IPsec for multi-tenant security
```

### 22.2 Rollback Plan

```bash
# Rollback: revert a VTEP to flat VLAN mode

# Step 1: Drain VTEP (migrate VMs away)
# (cloud orchestration layer)

# Step 2: Withdraw BGP EVPN VNI advertisements
vtysh -c "conf t"
vtysh -c "router bgp 65001"
vtysh -c "no address-family l2vpn evpn"  # stop advertising

# Step 3: Remove VXLAN interfaces
for vni in 100 200 300; do
    ip link set vxlan${vni} down
    ip link del vxlan${vni}
    ip link del br${vni}
done

# Step 4: Restore VLAN trunks to ToR switch
ip link set eth0.100 up  # re-enable VLAN subinterfaces

# Step 5: Restore VM network config
# (cloud orchestration layer)

# Automated rollback check:
# - Monitor BGP session count; if drops below threshold → auto-rollback
# - Monitor VM-to-VM packet loss; if > 0.1% for >5s → alert → manual rollback
```

---

## 23. References

### Standards and RFCs

- **RFC 7348** — Virtual eXtensible Local Area Network (VXLAN)  
  https://www.rfc-editor.org/rfc/rfc7348
- **RFC 7432** — BGP MPLS-Based Ethernet VPN (BGP EVPN)  
  https://www.rfc-editor.org/rfc/rfc7432
- **RFC 8365** — A Network Virtualization Overlay Solution Using EVPN  
  https://www.rfc-editor.org/rfc/rfc8365
- **RFC 8926** — VXLAN Generic Protocol Extension (VXLAN-GPE)  
  https://www.rfc-editor.org/rfc/rfc8926
- **RFC 9014** — Interconnect Solution for EVPN Overlay Networks  
  https://www.rfc-editor.org/rfc/rfc9014
- **RFC 7209** — Requirements for Ethernet VPN  
  https://www.rfc-editor.org/rfc/rfc7209

### Linux Kernel

- `net/vxlan.c` — Linux VXLAN implementation
- `include/net/vxlan.h` — VXLAN kernel headers
- `tools/testing/selftests/net/` — VXLAN kernel selftests
- Documentation: https://docs.kernel.org/networking/vxlan.html

### Software

- **FRRouting (FRR)**: https://docs.frrouting.org/en/latest/evpn.html
- **Open vSwitch**: https://docs.openvswitch.org/en/latest/tutorials/ovs-advanced/
- **Cumulus Linux VXLAN**: https://docs.nvidia.com/networking-ethernet-software/
- **Linux `ip` and `bridge` commands**: `man 8 ip-link`, `man 8 bridge`

### Academic and Technical

- "A Scalable, Commodity Data Center Network Architecture" (Al-Fares et al., SIGCOMM 2008)
- "VL2: A Scalable and Flexible Data Center Network" (Greenberg et al., SIGCOMM 2009)
- Arista Networks EVPN Deployment Guide
- Cisco VXLAN EVPN Multi-Site Design

---

## 24. Next 3 Steps

1. **Build and test the C VTEP**: Compile the vtep-c code, create two network namespaces, wire them with veth pairs, run the VTEP in each namespace, verify encapsulation with tcpdump on the outer interface and ping across the VXLAN overlay. Add the `--sanitize=address` build flag and fuzz the `vtep_decap_recv` path with AFL++ targeting malformed VXLAN headers.

   ```bash
   # Quick test with network namespaces:
   ip netns add ns-vtep-a
   ip netns add ns-vtep-b
   ip link add veth-a type veth peer name veth-b
   ip link set veth-a netns ns-vtep-a
   ip link set veth-b netns ns-vtep-b
   ip netns exec ns-vtep-a ip addr add 10.0.0.1/24 dev veth-a
   ip netns exec ns-vtep-b ip addr add 10.0.0.2/24 dev veth-b
   # Run VTEP in each namespace and test
   ```

2. **Deploy BGP EVPN lab with FRR**: Spin up 4 VMs (2 spine, 2 leaf) using QEMU/KVM. Configure FRR BGP EVPN per Section 7.7 on each leaf. Create VXLAN interfaces with `nolearning`. Attach VMs to each leaf. Verify: `show evpn mac vni 100` shows remote MACs; ping between VMs; capture tcpdump to confirm ARP suppression is active (no ARP flooding after initial learning).

3. **Implement WireGuard-secured VTEP**: Take the Rust VTEP from Section 15, add WireGuard tunnels between VTEPs using the `boringtun` crate or system WireGuard. Route all VXLAN UDP through WireGuard tunnels. Verify with Wireshark that outer UDP packets on port 4789 are encrypted (appear as WireGuard UDP on port 51820). Measure the latency impact of encryption vs plaintext VXLAN using `qperf` inside the overlay.

---

*Document generated for production-grade deep understanding of VXLAN. Treat as a living reference; validate all configs against your specific kernel version (`uname -r`) and FRR version (`vtysh -c "show version"`) before production deployment.*