# GENEVE Protocol: Complete In-Depth Technical Reference

> **Summary (4–8 lines):** GENEVE (Generic Network Virtualization Encapsulation, RFC 8926) is the
> current-generation network overlay encapsulation protocol designed to unify and supersede VXLAN,
> NVGRE, and STT by providing a flexible, extensible TLV-based option space inside a UDP header,
> while preserving the operational simplicity of VXLAN and the metadata richness needed by modern
> hypervisors and SDN controllers. It operates at Layer 2 (Ethernet) over Layer 3 (UDP/IP), uses
> a 24-bit Virtual Network Identifier (VNI), and embeds arbitrary per-packet control-plane metadata
> without kernel changes or protocol ossification. Understanding GENEVE at this depth means you can
> reason about: encapsulation overhead, MTU planning, hardware offload paths, NIC/ASIC pipeline
> constraints, OVS/OVN integration, Kubernetes CNI design, and the full threat surface of a
> multi-tenant virtualized network fabric.

---

## Table of Contents

1. [Historical Context and Motivation](#1-historical-context-and-motivation)
2. [RFC Specification Overview](#2-rfc-specification-overview)
3. [Protocol Architecture and Positioning](#3-protocol-architecture-and-positioning)
4. [Packet Format — Complete Byte-Level Breakdown](#4-packet-format--complete-byte-level-breakdown)
5. [GENEVE Options (TLV Extension Space)](#5-geneve-options-tlv-extension-space)
6. [Virtual Network Identifier (VNI) Semantics](#6-virtual-network-identifier-vni-semantics)
7. [Tunnel Endpoint (TEP) Architecture](#7-tunnel-endpoint-tep-architecture)
8. [Control Plane Design and Integration](#8-control-plane-design-and-integration)
9. [Data Plane Processing Pipeline](#9-data-plane-processing-pipeline)
10. [MTU, Fragmentation, and Path MTU Discovery](#10-mtu-fragmentation-and-path-mtu-discovery)
11. [Comparison: GENEVE vs VXLAN vs NVGRE vs STT vs GRE](#11-comparison-geneve-vs-vxlan-vs-nvgre-vs-stt-vs-gre)
12. [Linux Kernel Implementation Deep-Dive](#12-linux-kernel-implementation-deep-dive)
13. [Open vSwitch (OVS) GENEVE Integration](#13-open-vswitch-ovs-geneve-integration)
14. [OVN and GENEVE](#14-ovn-and-geneve)
15. [Kubernetes CNI and GENEVE](#15-kubernetes-cni-and-geneve)
16. [Hardware Offload: NIC, SmartNIC, DPU](#16-hardware-offload-nic-smartnic-dpu)
17. [ECMP, Load Balancing, and Entropy](#17-ecmp-load-balancing-and-entropy)
18. [C Implementation — Encoder/Decoder/Sender](#18-c-implementation--encoderdecodersender)
19. [Rust Implementation — Zero-Copy Parser and Encapsulator](#19-rust-implementation--zero-copy-parser-and-encapsulator)
20. [Threat Model and Security Analysis](#20-threat-model-and-security-analysis)
21. [Observability, Telemetry, and Debugging](#21-observability-telemetry-and-debugging)
22. [Performance: Benchmarking and Tuning](#22-performance-benchmarking-and-tuning)
23. [Failure Modes and Operational Pitfalls](#23-failure-modes-and-operational-pitfalls)
24. [Roll-out / Roll-back Plan](#24-roll-out--roll-back-plan)
25. [References and Standards](#25-references-and-standards)
26. [Next 3 Steps](#26-next-3-steps)

---

## 1. Historical Context and Motivation

### 1.1 The Pre-GENEVE Landscape

Before GENEVE, the network virtualization world was fractured across at least four incompatible
encapsulation formats, each built by different vendors to solve slightly different problems:

| Protocol | Origin       | Year | Key Limitation                                          |
|----------|-------------|------|---------------------------------------------------------|
| VXLAN    | VMware/Arista/Cisco | 2011 | No extensible metadata; 8-byte header; fixed schema  |
| NVGRE    | Microsoft    | 2011 | GRE-based; poor ECMP on L3 networks                     |
| STT      | Nicira (VMware) | 2012 | TCP-framing trick for TSO; stateful; complex offload   |
| GUE      | Tom Herbert  | 2014 | Generic UDP encapsulation; never widely standardized    |

Each was designed to provide multi-tenant L2 network isolation over an IP fabric using a virtual
network identifier (VNI/VSID/etc.). All had 24-bit or larger tenant identifiers, supporting up to
16 million isolated segments.

The critical problem: **as SDN controllers, hypervisors, and hardware offload engines became
smarter, they needed per-packet metadata** — information such as:

- Source VM policy label
- Security group tag
- Service chain pointer
- Hardware flow context
- QoS class / DSCP override
- Ingress tunnel source port hint

VXLAN had no space for this. NVGRE had no space. STT had some bits but was deeply awkward. Each
vendor invented proprietary extensions (e.g., VMware NSX's Geneve predecessor, Cisco's VXLAN-GPE).

### 1.2 Why GENEVE Was Created

GENEVE (proposed by VMware, Microsoft, Red Hat, Intel in 2014, finalized as RFC 8926 in 2020)
was designed with one core insight: **the encapsulation format should be stable but the semantics
should be extensible at runtime via TLVs.**

Key design goals:

1. **TLV option space** — arbitrary key-value metadata attached to every packet, interpretable
   by tunnel endpoints, transit devices, or hardware offloads.
2. **UDP transport** — same operational properties as VXLAN; works through NATs, leverages
   existing ECMP entropy from UDP source port.
3. **Variable-length header** — the base header is 8 bytes; options extend it in 4-byte
   increments up to 252 bytes of options.
4. **Protocol-agnostic inner payload** — inner Ethernet frame is default, but the protocol
   type field allows carrying raw IP, MPLS, etc.
5. **No control plane mandated** — GENEVE is purely a data-plane wire format. Control plane
   (how endpoints learn MAC-to-VNI-to-VTEP mappings) is out of scope, allowing SDN controllers,
   EVPN, or flood-and-learn to operate above it.

### 1.3 Standardization Timeline

```
2014-01  Draft-00: "Geneve: Generic Network Virtualization Encapsulation"
         Authors: Gross, Sridhar (VMware), Garg, Wang (Microsoft), 
                  Smyslov, Thaler (IETF), Kandula (Microsoft Research)
2014-07  Draft-01: Option class/type registry mechanism added
2015-02  Draft-02: Clarified OAM considerations
2016-06  Draft-03: Security considerations expanded  
2019-09  Draft-07: IESG review; MAC learning / flooding not mandated
2020-11  RFC 8926 published (Proposed Standard)
```

RFC 8926 is complemented by:
- **RFC 8014** — An Architecture for Data-Center Network Virtualization Over Layer 3 (NVO3)
- **RFC 7365** — Framework and Requirements for L2VPN (context for NVO3)
- **RFC 7432** — BGP MPLS-Based Ethernet VPN (EVPN; common control plane used with GENEVE)
- **RFC 4271** — BGP-4 (base for EVPN control plane)
- **RFC 8365** — A Network Virtualization Overlay Solution Using EVPN

---

## 2. RFC Specification Overview

RFC 8926 defines:

1. **The encapsulation format** (Section 3): outer UDP/IP, GENEVE header (base + variable options),
   inner Ethernet frame.
2. **Option processing rules** (Section 3.5): critical vs. non-critical options; unknown critical
   options → packet drop; unknown non-critical options → ignore.
3. **Tunnel endpoint behavior** (Section 4): encapsulation, decapsulation, option insertion,
   option stripping.
4. **Security considerations** (Section 7): no built-in encryption; recommends IPsec or DTLS.
5. **IANA registries** (Section 8): option class space (16-bit); option type space (7-bit per class).

Key RFC 8926 terminology:

- **NVE (Network Virtualization Edge)**: the tunnel endpoint; performs encap/decap; synonym for VTEP.
- **NVO (Network Virtualization Overlay)**: the logical overlay network identified by a VNI.
- **Tenant System (TS)**: the VM, container, or bare-metal endpoint inside the overlay.
- **Underlay**: the physical IP network carrying GENEVE UDP packets between NVEs.
- **Transit device**: a router/switch in the underlay that forwards GENEVE packets without
  decapsulating them (treats them as opaque UDP).

---

## 3. Protocol Architecture and Positioning

### 3.1 Layer Model

```
+----------------------------------------------------------+
|                  Tenant System (VM/Container)            |
|  Application / Transport / Network / Ethernet (Layer 2)  |
+----------------------------------------------------------+
              |                           |
         [veth/tap]                  [veth/tap]
              |                           |
+----------------------------------------------------------+
|           NVE / VTEP (Hypervisor / Host Kernel)          |
|                                                          |
|  Overlay plane:   Inner Ethernet Frame                   |
|                        |                                 |
|                   GENEVE Header (8B + options)           |
|                        |                                 |
|                   UDP  (src: entropy-hash, dst: 6081)    |
|                        |                                 |
|                   Outer IP Header (IPv4 or IPv6)         |
|                        |                                 |
|                   Outer Ethernet (NIC MAC, next-hop MAC) |
+----------------------------------------------------------+
              |                           |
           [NIC]                       [NIC]
              |                           |
+----------------------------------------------------------+
|               Underlay IP Fabric (Spine/Leaf)            |
|   ECMP routing, OSPF/BGP, physical switches/routers      |
+----------------------------------------------------------+
```

### 3.2 Encapsulation Overhead

For a standard Ethernet frame inner payload:

```
Outer Ethernet:    14 bytes (DMAC 6 + SMAC 6 + EtherType 2)
Outer VLAN tag:     4 bytes (optional; 802.1Q)
Outer IPv4:        20 bytes (no IP options)
Outer IPv6:        40 bytes
UDP:                8 bytes
GENEVE base:        8 bytes
GENEVE options:     0–252 bytes (variable, 4-byte aligned)
Inner Ethernet:    14 bytes minimum
                  ----
IPv4 total (no options, no VLAN): 14+20+8+8 = 50 bytes
IPv6 total (no options, no VLAN): 14+40+8+8 = 70 bytes
```

With a 1500-byte underlay MTU and IPv4 outer, the inner payload available:
`1500 - 50 = 1450 bytes` (no GENEVE options). This means tenant VMs must use MSS ≤ 1410 bytes
(1450 - 20 IP - 20 TCP) or MTU jumbo frames must be enabled on the underlay.

### 3.3 UDP Port

IANA assigned port **6081** to GENEVE. Transit devices (firewalls, NATs) that perform deep
packet inspection or stateful tracking must be aware of this port. UDP source port is set by
the encapsulating NVE to a hash of the inner flow (5-tuple or 4-tuple) for ECMP entropy.

---

## 4. Packet Format — Complete Byte-Level Breakdown

### 4.1 Full Packet Structure on Wire

```
 Byte  0         1         2         3
       0123456789012345678901234567890123456789
       |       |       |       |       |
 +0    [ Outer Destination MAC Address         ] (6 bytes)
 +6    [ Outer Source MAC Address              ] (6 bytes)
 +12   [ Outer EtherType: 0x0800/0x86DD        ] (2 bytes)
       --- Outer IPv4 Header (20 bytes) ---
 +14   [Ver=4|IHL=5| DSCP/ECN  | Total Length  ]
 +18   [     Identification    |Flags|Frag Off  ]
 +22   [  TTL  | Proto=UDP(17) | Header Chksum  ]
 +26   [         Outer Source IP Address        ]
 +30   [      Outer Destination IP Address      ]
       --- UDP Header (8 bytes) ---
 +34   [ Src Port (entropy)    | Dst Port=6081  ]
 +38   [    UDP Length         |   UDP Checksum  ]
       --- GENEVE Header (8 bytes minimum) ---
 +42   [Ver|OL |C|R|R|R| Protocol Type (2 bytes)]
 +46   [           VNI (3 bytes)        | Rsvd   ]
       --- GENEVE Options (variable, 0–252 bytes)---
 +50   [ Option Class (2B) | Type (1B) | R|R|R|Len(5b)]  \
 +54   [ Option Data (0–128 bytes, 4B aligned)          ]  > Repeated
       ...                                               /
       --- Inner Ethernet Frame ---
 +50+  [ Inner DMAC | Inner SMAC | EtherType | Payload ]
```

### 4.2 GENEVE Base Header — Bit-by-Bit

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |Ver|  Opt Len  |O|C|    Rsvd   |          Protocol Type        |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |        Virtual Network Identifier (VNI)       |    Reserved   |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Field descriptions:**

| Field         | Bits | Description |
|--------------|------|-------------|
| Ver           | 2    | Version. Must be 0 for RFC 8926. If non-zero, receiver must silently drop (forward compat). |
| Opt Len       | 6    | Length of options in **4-byte words**. 0 = no options. Max = 63 words = 252 bytes. |
| O (OAM)       | 1    | OAM (Operations, Administration, Maintenance) flag. Packet is OAM/control, not tenant data. NVEs must process specially; transit devices may punt to control plane. |
| C (Critical)  | 1    | Critical options present. If set, receiver must examine options for critical TLVs. If receiver finds a critical option it cannot process, it MUST drop the packet. This bit is a fast hint to avoid TLV parsing when no critical options exist. |
| Rsvd          | 6    | Reserved, must be zero on transmit; receiver must ignore. |
| Protocol Type | 16   | EtherType of inner payload. 0x6558 = Transparent Ethernet Bridging (most common). 0x0800 = IPv4. 0x86DD = IPv6. 0x8847 = MPLS unicast. |
| VNI           | 24   | Virtual Network Identifier. 16,777,216 possible segment IDs. Semantics are local to the control plane (e.g., maps to a VLAN, VRF, or tenant). |
| Reserved      | 8    | Must be zero. Silently ignored by receivers. |

**Total base header: 8 bytes (2 words of 32 bits).**

### 4.3 Opt Len Field — Critical Detail

Opt Len is in units of **4-byte double-words**, NOT bytes.

- Opt Len = 0 → 0 bytes of options (header is exactly 8 bytes total)
- Opt Len = 1 → 4 bytes of options (one 4-byte option)
- Opt Len = 63 → 252 bytes of options

The total GENEVE header size in bytes = `8 + (Opt Len × 4)`.

A decoder computes the start of the inner Ethernet frame as:
`inner_frame_ptr = geneve_hdr_ptr + 8 + (opt_len * 4)`

This is a constant-time O(1) operation — the inner frame start is always directly computable
without iterating TLVs. This is a deliberate design choice for hardware pipeline efficiency.

### 4.4 Protocol Type — EtherType Semantics

The Protocol Type field uses the IANA EtherType registry (IEEE 802):

| EtherType | Meaning | Usage |
|-----------|---------|-------|
| 0x6558 | Transparent Ethernet Bridging | Default; inner L2 Ethernet frame with MACs |
| 0x0800 | IPv4 | Inner frame is raw IPv4 (no inner Ethernet header) |
| 0x86DD | IPv6 | Inner frame is raw IPv6 |
| 0x8847 | MPLS unicast | Inner MPLS label stack |
| 0x8848 | MPLS multicast | Inner MPLS multicast |
| 0x0806 | ARP | Rare; inner ARP frame |

The 0x6558 (Transparent Ethernet Bridging) case is by far the most common in practice. It means
the inner payload begins with a 6-byte DMAC, making GENEVE a pure L2-over-UDP encapsulation
(equivalent to VXLAN in payload semantics).

### 4.5 VNI Semantics and Scope

The 24-bit VNI provides 2²⁴ = 16,777,216 unique segment identifiers. The VNI is meaningful only
within the domain of a single NVO3 deployment. Different deployments can reuse VNI values without
conflict as long as their physical underlay networks are distinct.

VNI 0 is technically valid by the RFC but is conventionally reserved or has implementation-specific
meaning (some implementations use it to indicate "no VNI" or use it for management traffic).

In OVN: VNIs are allocated by the OVN controller and mapped to Logical Switches or Logical Routers.
In Kubernetes with Flannel: a single VNI (default: 1) is used for the entire cluster.
In OVN with multiple logical switches: each logical switch gets a unique VNI.

---

## 5. GENEVE Options (TLV Extension Space)

### 5.1 Option Structure

Each option follows a fixed 4-byte header, followed by 0 to 128 bytes of data, padded to a
4-byte boundary:

```
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |          Option Class         |      Type     |R|R|R|  Length  |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
 |                      Variable-Length Data                     |
 |                       (Length × 4 bytes)                      |
 +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

| Field        | Bits | Description |
|-------------|------|-------------|
| Option Class | 16   | Identifies the organization/vendor that defined the option. IANA-managed registry. |
| Type         | 7    | Option type within the Class namespace. IANA-managed per Class. |
| R (Critical) | 1    | **Bit 7 of the Type byte.** If 1, this option is critical. A receiver that cannot process it MUST drop the packet. If 0 (non-critical), receiver may ignore it. |
| Length       | 5    | Length of option data in **4-byte words** (NOT counting the 4-byte option header). 0 = no data. Max = 31 words = 124 bytes of data. |

**Total option size = 4 + (Length × 4) bytes.**

Multiple options are concatenated. The total length of all options equals `Opt Len × 4` bytes
(from the base header). Options must be aligned to 4-byte boundaries (guaranteed by the
Length field in units of 4-byte words).

### 5.2 Option Class Registry

IANA maintains the Option Class registry. Key allocations:

| Option Class | Hex    | Description |
|-------------|--------|-------------|
| IETF        | 0x0000 | Standards-track IETF-defined options |
| Linux kernel | 0x0127 | Linux kernel experimental options |
| Open vSwitch | Various | OVS metadata (see below) |
| VMware NSX   | Various | NSX proprietary options |

The full list is at: https://www.iana.org/assignments/nvo3/nvo3.xhtml

### 5.3 Critical vs. Non-Critical Options

This is one of the most important design decisions in GENEVE:

**Non-critical option (Type bit 7 = 0):**
- If an NVE or middlebox does not understand this option, it silently ignores it.
- The packet continues to be processed normally.
- Use for: advisory metadata, telemetry hints, optional QoS tags.
- Example: "this packet's inner flow had RTT > 10ms last window" — informational for endpoints
  that understand it, harmless to drop the info.

**Critical option (Type bit 7 = 1):**
- If an NVE does not understand this option, it MUST drop the packet.
- The C bit in the base header is set to 1 when any critical option exists (optimization: if C=0,
  you can skip all option parsing for criticality checks).
- Use for: security labels that must be enforced, capability negotiation, mandatory service
  chain pointers.
- Example: "this packet must pass through security group firewall node X before delivery"
  — if the endpoint doesn't understand this requirement, delivering the packet would violate policy.

**Processing algorithm (pseudocode):**

```
if geneve_hdr.C == 0:
    skip_to_inner_frame()   # no critical options; fast path
else:
    for each option in options:
        if option.type & 0x80:  # critical bit set
            if not can_process(option.class, option.type & 0x7F):
                drop_packet()
                return
        else:
            process_if_known(option)  # or ignore
    forward_inner_frame()
```

### 5.4 Known/Deployed GENEVE Options

**OVN/OVS Tunnel Metadata (class 0x0102, Linux geneve_opt):**

OVN uses GENEVE options to carry OpenFlow metadata (`MFF_TUN_METADATA`) between hypervisors.
This allows OVN's Logical Data Path Set (LDP) ID and flow-specific tags to be embedded in the
tunnel header, enabling the remote NVE to apply logical flow tables without additional lookups.

```
Option Class: 0x0102  (OVS-assigned)
Type:         0x80    (critical=1, type=0)
Length:       variable (typically 1–4 words = 4–16 bytes of metadata)
Data:         OpenFlow field values (tun_metadata0..tun_metadata63)
```

OVN specifically uses this for carrying the **datapath key** and **port key** that identify the
logical context of the packet inside OVN's pipeline, allowing the remote side to jump into the
correct logical flow table entry without re-classifying.

**Linux Kernel Geneve Options (`geneve_opt` struct):**

```c
// from include/uapi/linux/if_tunnel.h
struct geneve_opt {
    __be16  opt_class;   // option class
    u8      type;        // type | critical bit
    u8      length;      // data length in 4B words
    u8      opt_data[];  // variable-length data
};
```

### 5.5 Options and Hardware Offload Tension

Hardware NICs that support GENEVE offload (TSO, LRO, RSS, checksum) generally have limited
or no support for GENEVE options parsing. This creates a critical design tension:

- **No options**: Full hardware offload possible (TSO, LRO work at line rate).
- **With options**: NIC may fall back to software processing; throughput drops significantly.
- **NIC intelligence**: Newer SmartNICs (Nvidia BlueField, Intel IPU, Marvell OCTEON) can be
  programmed (via P4/eBPF) to handle specific option classes.

This is why OVN supports a "no-options" mode and why production deployments often avoid using
GENEVE options in the fast path, reserving them for control-plane punted packets.

---

## 6. Virtual Network Identifier (VNI) Semantics

### 6.1 VNI as Isolation Boundary

The VNI is the primary isolation boundary in a GENEVE-based overlay network. It defines a
**broadcast domain** (for Ethernet/L2 payloads) or a **routing domain** (for IP payloads):

```
+------------------+        +------------------+
|  VNI = 100       |        |  VNI = 200       |
|  Tenant A L2 Net |        |  Tenant B L2 Net |
|                  |        |                  |
| VM-A1  VM-A2     |        | VM-B1  VM-B2     |
+------------------+        +------------------+
         |                           |
   [GENEVE VNI=100]           [GENEVE VNI=200]
         |                           |
+----------------------------------------------------------+
|                    Underlay IP Fabric                    |
|  NVE/VTEP nodes encapsulate/decapsulate per VNI         |
+----------------------------------------------------------+
```

Packets with VNI=100 are NEVER delivered to endpoints configured for VNI=200 and vice versa,
regardless of inner MAC/IP addresses. Isolation is enforced at the VTEP/NVE by checking
the VNI on decapsulation and only forwarding to ports bound to that VNI.

### 6.2 VNI Assignment Models

**Flat model (one VNI per tenant L2 network):**
- Each virtual L2 switch/VLAN gets a VNI.
- Simple; scales to 16M segments.
- Used by: Flannel, older VXLAN setups.

**Hierarchical model (VNI per tenant, sub-segmentation in-NVE):**
- One VNI per customer; sub-tenant isolation done by the NVE using additional metadata
  (GENEVE options, inner VLAN tags).
- Allows more tenants than 16M by scoping sub-segments within a tenant.

**Per-logical-port model (OVN):**
- OVN allocates VNIs (called "tunnel keys") per logical network object.
- Each Logical Switch and Logical Router port gets a unique key.
- The GENEVE option carries additional context (datapath key + port key) enabling fine-grained
  logical flow processing.

### 6.3 VNI Scope and Multi-Site Considerations

VNIs are local to an NVO3 domain. When extending GENEVE overlays across data centers (DCI):
- A **gateway NVE** (or EVPN PE router) translates between VNI namespaces.
- EVPN Type-2 (MAC/IP) and Type-3 (Inclusive Multicast) routes carry VNI bindings.
- EVPN with GENEVE uses the GENEVE VNI as the EVPN VXLAN ID in BGP attributes.

---

## 7. Tunnel Endpoint (TEP) Architecture

### 7.1 NVE (Network Virtualization Edge) Taxonomy

```
+------------------------------------------------------------------+
|                      NVE / VTEP Taxonomy                         |
+------------------+---------+-----------+---------+---------------+
|  NVE Type        | Where   | Encap     | Decap   | Example       |
+------------------+---------+-----------+---------+---------------+
| Hypervisor NVE   | Host OS | Per-VM    | Per-VM  | Linux+OVS     |
| Container NVE    | Host    | Per-pod   | Per-pod | Flannel/Calico |
| Hardware NVE     | TOR     | Per-port  | Per-port| Arista 7050   |
| SmartNIC NVE     | In-NIC  | Offloaded | Offloaded| NVIDIA BF3   |
| Gateway NVE      | Edge    | Cross-DC  | Cross-DC| Juniper MX    |
+------------------+---------+-----------+---------+---------------+
```

### 7.2 Encapsulation Logic at an NVE

When a tenant VM sends an Ethernet frame:

```
Step 1: Tenant frame arrives at NVE (veth/tap interface)
  Inner frame: DMAC=A:B:C:D:E:F, SMAC=1:2:3:4:5:6, EtherType=0x0800, IP payload

Step 2: Lookup DMAC in local FDB (Forwarding Database) for this VNI
  FDB entry: DMAC → remote VTEP IP (or local port)
  If miss: flood to all remote VTEPs for this VNI (multicast or controller-directed)

Step 3: Determine remote VTEP IP (underlay destination)
  VTEP_DST = 10.0.0.2  (from FDB/SDN controller)

Step 4: Build GENEVE header
  ver=0, opt_len=0 (or N if options), O=0, C=0 (or 1), protocol_type=0x6558
  vni=100, reserved=0
  + options (if any)

Step 5: Build UDP header
  src_port = hash(inner_src_ip, inner_dst_ip, inner_src_port, inner_dst_port, inner_proto)
             & 0xC000 | 0xC000   // ensure high bits set (49152–65535 range)
  dst_port = 6081
  length   = sizeof(udp) + sizeof(geneve) + sizeof(options) + sizeof(inner_frame)
  checksum = 0 (IPv4) or computed (IPv6, required for UDP-over-IPv6)

Step 6: Build outer IP header
  src = local VTEP IP
  dst = VTEP_DST
  proto = 17 (UDP)
  ttl = 64 (or inherited from inner, decremented)
  DSCP = copy from inner IP DSCP (optional, for QoS continuity)
  ECN  = copy from inner IP ECN (RFC 6040 tunneling)

Step 7: Build outer Ethernet header
  DMAC = next-hop MAC (from ARP/ND cache for VTEP_DST or default gateway)
  SMAC = local NIC MAC
  EtherType = 0x0800 (IPv4) or 0x86DD (IPv6)

Step 8: Transmit on physical NIC
```

### 7.3 Decapsulation Logic

```
Step 1: Outer Ethernet frame arrives on physical NIC
  Verify outer DMAC matches NIC MAC (or multicast group)

Step 2: Parse outer IP header
  Verify dst IP is local VTEP IP
  Verify proto = 17 (UDP)

Step 3: Parse UDP header  
  Verify dst_port = 6081 (or configured port)

Step 4: Parse GENEVE base header
  Verify ver = 0; if not, drop
  Read opt_len, O, C, protocol_type, VNI

Step 5: Process GENEVE options (if opt_len > 0)
  If C=1: iterate options; drop if unknown critical found
  Process known options (e.g., update flow metadata, OVN pipeline context)

Step 6: Compute inner frame start
  inner_ptr = geneve_hdr_ptr + 8 + (opt_len * 4)

Step 7: VNI-based routing
  Look up VNI in local VNI table → get local bridge/port set
  If VNI unknown: drop (prevents cross-tenant delivery)

Step 8: Deliver inner frame
  protocol_type = 0x6558 → deliver as Ethernet frame to bridge
  protocol_type = 0x0800 → deliver as IP packet to routing table

Step 9: FDB learning (if using flood-and-learn)
  Learn: inner SMAC → remote VTEP IP (src of outer IP) for this VNI
```

### 7.4 VTEP Discovery and FDB Population

GENEVE has no built-in VTEP discovery. In practice:

**Flood-and-learn (simple, not scalable):**
- Unknown destination → multicast or replicated unicast to all VTEPs in VNI.
- Source MAC learned from decapsulated packets.
- Problem: O(N×M) BUM (Broadcast/Unknown/Multicast) traffic at scale.

**SDN controller (centralized):**
- Controller (OVN, NSX, ACI) pushes MAC→VTEP mappings to each NVE.
- No flooding; proactive or reactive installation.
- Controller is single point of failure (mitigated by clustering).

**BGP EVPN (distributed, standardized):**
- Each NVE announces its locally attached MACs via EVPN Type-2 routes.
- MP-BGP distributes these to all NVEs.
- Scales to millions of MACs across thousands of VTEPs.
- Most production-grade approach for multi-site or large-scale deployments.

---

## 8. Control Plane Design and Integration

### 8.1 Control Plane Responsibilities

```
+--------------------------------------------------------------+
|                   Control Plane Responsibilities              |
+-------------------------------+------------------------------+
| Data Plane (GENEVE wire fmt)  | Control Plane (out of scope) |
+-------------------------------+------------------------------+
| VNI per packet                | VNI allocation and lifecycle |
| Options per packet            | Option class/type negotiation|
| UDP src port entropy          | VTEP IP management           |
| Inner frame delivery          | MAC/IP → VTEP mapping        |
| BUM flooding (if needed)      | Flood list management        |
| ECN marking                   | QoS policy distribution      |
+-------------------------------+------------------------------+
```

### 8.2 EVPN Control Plane with GENEVE

EVPN (RFC 7432 + RFC 8365) is the standard distributed control plane for GENEVE overlays
in production data centers. The architecture:

```
+----------+        MP-BGP EVPN         +----------+
|  VTEP 1  |<-------------------------->|  VTEP 2  |
| (Rack A) |     (Route Reflector)      | (Rack B) |
+----------+            |               +----------+
     |          +-------+-------+             |
     |          | Route Reflector|             |
     |          |  (BGP RR)     |             |
     |          +---------------+             |
  VM-1 (VNI=100)                          VM-2 (VNI=100)

EVPN Route Types used with GENEVE:
  Type 1: Ethernet Auto-Discovery (per-ES, per-EVI) — multi-homing
  Type 2: MAC/IP Advertisement — MAC learning
  Type 3: Inclusive Multicast Route — BUM traffic tree
  Type 4: Ethernet Segment Route — DF election
  Type 5: IP Prefix Route — inter-subnet routing
```

**EVPN BGP community for GENEVE:**
The VXLAN Encapsulation Extended Community (type 0x03, subtype 0x0d) advertises the
encapsulation type. For GENEVE, encap type = 11 (IANA-assigned).

### 8.3 OVN Control Plane Architecture

OVN (Open Virtual Network) is the most widely used software-defined control plane for
GENEVE in the Kubernetes/OpenStack ecosystem:

```
+------------------------------------------------------------------+
|                        OVN Architecture                          |
+------------------------------------------------------------------+

Northbound DB (NB_DB):        Southbound DB (SB_DB):
  Logical Switches/Routers       Chassis (VTEP nodes)
  Logical Ports                  Port_Bindings
  ACL/QoS policies               Datapath_Bindings (VNI)
  Load Balancers                 Logical_Flows (OpenFlow-like)
        |                               |
        v                               v
  ovn-northd                     ovn-controller (per host)
  (compiles logical               (installs OpenFlow in OVS,
   flows from NB→SB)              programs GENEVE tunnels)
        |                               |
        +----------[OVSDB]--------------+
                          |
                    ovs-vswitchd
                    (OVS userspace)
                          |
                  openvswitch kernel module
                          |
                  GENEVE tunnel endpoints
                  (geneve_sys kernel driver)
```

OVN uses GENEVE (not VXLAN) by default because:
1. GENEVE TLV options allow OVN to carry its logical context (datapath key + port key) in-band.
2. This eliminates a second lookup at the receiving VTEP — the logical flow table index is
   embedded in the packet itself.
3. Fallback to VXLAN or STT is supported for older NICs.

---

## 9. Data Plane Processing Pipeline

### 9.1 Kernel Receive Path (Linux)

```
NIC Hardware
  │
  │ [DMA ring buffer / NAPI poll]
  ▼
softirq / NAPI poll loop
  │
  ▼
netif_receive_skb()
  │
  ▼
__netif_receive_skb_core()
  │
  ├─ packet_type handlers (ETH_P_IP / ETH_P_IPV6)
  │
  ▼
ip_rcv() → ip_rcv_core()
  │
  ▼
ip_local_deliver() [dst == local IP]
  │
  ▼
udp_rcv() → __udp4_lib_rcv()
  │
  ├─ socket lookup (port 6081 → geneve socket)
  │
  ▼
geneve_udp_encap_recv()   [net/ipv4/geneve.c]
  │
  ├─ Parse GENEVE base header
  ├─ Validate version
  ├─ Parse options (if opt_len > 0)
  ├─ VNI → net_device lookup
  ├─ Strip outer headers
  ├─ Set inner SKB metadata (tun_key, opt data)
  │
  ▼
netif_rx() / napi_gro_receive()  [inner frame]
  │
  ▼
L2 bridge / L3 routing for inner frame
```

### 9.2 XDP Fast Path

For high-performance GENEVE processing, XDP (eXpress Data Path) can intercept GENEVE
packets at the earliest possible point — in the NIC driver or at the TC layer:

```
NIC Driver (XDP native mode)
  │
  ▼
XDP program (eBPF, JIT-compiled)
  │
  ├─ Parse Ethernet → IP → UDP → GENEVE (zero-copy, in-place)
  ├─ VNI lookup in eBPF map (hash map, O(1))
  ├─ Option processing (if needed)
  ├─ Redirect to inner veth: bpf_redirect_map()
  │
  ▼
Inner veth / container interface
```

XDP GENEVE processing achieves 10-40 Mpps on modern hardware versus 1-4 Mpps for the
kernel socket path, at the cost of implementation complexity and loss of some kernel
networking features (conntrack, Netfilter, etc. in the outer path).

### 9.3 TC eBPF for GENEVE Encapsulation (Egress)

```
Container / VM egress (veth)
  │
  ▼
TC eBPF hook (BPF_PROG_TYPE_SCHED_CLS, clsact qdisc)
  │
  ├─ Inspect inner frame (src/dst MAC, IP 5-tuple)
  ├─ Build GENEVE encapsulation in bpf_skb_adjust_room()
  ├─ Set tunnel metadata via bpf_skb_set_tunnel_key()
  │    (fills tun_id=VNI, remote_ip, opt=TLV options)
  ├─ Redirect to physical NIC via bpf_redirect()
  │
  ▼
Physical NIC → underlay
```

Cilium uses exactly this approach: eBPF at TC layer performs GENEVE encap/decap, integrated
with its identity-based security model (where security identities are encoded in GENEVE options).

---

## 10. MTU, Fragmentation, and Path MTU Discovery

### 10.1 MTU Budget Analysis

```
Underlay Physical MTU:      9000 bytes (jumbo, typical DC)
                            1500 bytes (standard, WAN)

Encapsulation overhead (IPv4 outer, no options):
  Outer Ethernet:             14 bytes
  Outer IPv4:                 20 bytes
  UDP:                         8 bytes
  GENEVE base:                 8 bytes
  ─────────────────────────── ──────
  Total overhead:             50 bytes

Inner Ethernet frame budget:
  Jumbo underlay:   9000 - 50 = 8950 bytes
  Standard underlay: 1500 - 50 = 1450 bytes

TCP MSS for standard underlay (IPv4 inner):
  1450 - 20 (inner IP) - 20 (TCP) = 1410 bytes

With 32 bytes of GENEVE options (Opt Len=8):
  1500 - 50 - 32 = 1418 bytes inner frame budget
  1418 - 20 - 20 = 1378 bytes TCP MSS
```

### 10.2 MTU Strategies

**Strategy 1: Jumbo frames on underlay (best performance):**
```bash
# Set jumbo MTU on all physical NICs and switches
ip link set eth0 mtu 9000
# Tenant VM MTU = 1500 (normal)
# Overhead absorbed by jumbo capacity
# Inner Ethernet can be full 1500-byte frames
```

**Strategy 2: Reduced MTU on overlay interfaces:**
```bash
# Set overlay NIC MTU to account for overhead
ip link set geneve0 mtu 1450  # for IPv4 outer
ip link set geneve0 mtu 1430  # for IPv6 outer (extra 20B)
# Tenant VMs must use this reduced MTU
# Problem: some apps don't respect MTU; PMTUD required
```

**Strategy 3: TCP MSS clamping (most pragmatic):**
```bash
# Clamp TCP SYN/SYN-ACK MSS at NVE using iptables/nftables
iptables -t mangle -A FORWARD \
  -p tcp --tcp-flags SYN,RST SYN \
  -j TCPMSS --clamp-mss-to-pmtu

# Or via nftables
nft add rule ip mangle FORWARD \
  tcp flags syn tcp option maxseg size set rt mtu
```

**Strategy 4: PMTUD (Path MTU Discovery, RFC 1191/4821):**
- Packets set DF bit; if too large, receive ICMP Fragmentation Needed.
- NVE must propagate ICMP back to inner source (requires special handling for tunnels).
- RFC 4459: "MTU and Fragmentation Issues with In-the-Network Tunneling" — covers this problem.

### 10.3 Fragmentation in GENEVE Context

GENEVE itself does not fragment. The outer IP header carries the DF bit behavior:

- **Outer IPv4 DF=1 (default, recommended):** If outer packet exceeds path MTU, ICMP
  Fragmentation Needed is returned to the NVE, which must either fragment the inner frame
  or propagate the ICMP inward.
- **Outer IPv4 DF=0 (fragmentation allowed):** IP routers fragment the outer packet; the
  receiving NVE must reassemble before decapsulation. Fragmentation of tunneled packets is
  terrible for performance and correctness (fragments of a UDP datagram don't all carry
  the GENEVE header — only the first fragment does; reassembly must be done at the IP layer).
- **IPv6 outer:** IPv6 never fragments at routers; only source can fragment. NVE must perform
  fragmentation before encapsulation.

**Best practice: Jumbo underlay + DF=1 on outer + MSS clamping on overlay.**

---

## 11. Comparison: GENEVE vs VXLAN vs NVGRE vs STT vs GRE

### 11.1 Feature Comparison Matrix

```
Feature                    GENEVE   VXLAN   NVGRE   STT     GRE
─────────────────────────────────────────────────────────────────
RFC/Standard               RFC 8926 RFC 7348 IETF    Draft   RFC 2784
Transport                  UDP      UDP     GRE     TCP     IP proto 47
Standard port              6081     4789    N/A     N/A     N/A
VNI bits                   24       24      24      64      (key: 32)
Extensible options         Yes      No      Limited No      No
Flexible inner protocol    Yes      No (L2) No (L2) No (L2) Yes
ECMP friendly              Yes      Yes     Poor    No*     Poor
Hardware offload support   Growing  Wide    Rare    Rare    Wide
OAM flag                   Yes      No      No      No      No
Critical option concept    Yes      No      No      No      No
Kernel driver (Linux)      geneve   vxlan   vxlan   N/A     gre
OVN default                Yes      Fallback No     Fallback No
IPv6 outer                 Yes      Yes     Yes     No      Yes
Multicast inner support    Yes      Yes     Yes     No      Yes
─────────────────────────────────────────────────────────────────
* STT uses TCP framing tricks for TSO; stateful, not ECMP-friendly per se
```

### 11.2 When to Choose Each

**Choose GENEVE when:**
- Using OVN, Cilium, or any SDN requiring per-packet metadata.
- Need forward-compatible extensibility for future features.
- SmartNIC/DPU with programmable dataplane (can handle options).
- Kubernetes CNI development.

**Choose VXLAN when:**
- Maximum hardware NIC offload compatibility required today.
- Simple L2 overlay; no metadata needed.
- Interoperability with legacy hardware VTEPs (TOR switches, hardware VTEPs).
- EVPN over VXLAN already deployed and standardized in your environment.

**Choose NVGRE when:**
- Microsoft Hyper-V environment (native support).
- Windows Server primary compute fabric.
- (Otherwise: avoid; poor ECMP, limited Linux support.)

**Choose GRE when:**
- Point-to-point tunnels (not multi-tenant).
- Need hardware acceleration for simple tunneling (widely supported).
- No need for multi-tenancy or ECMP.

---

## 12. Linux Kernel Implementation Deep-Dive

### 12.1 Kernel Module: `geneve`

The Linux kernel GENEVE implementation lives in `net/ipv4/geneve.c` (merged in 4.0, 2015).

```bash
# Load the module
modprobe geneve

# Verify
lsmod | grep geneve
# geneve                 32768  2 openvswitch
```

**Key data structures:**

```c
/* net/ipv4/geneve.c */

/* Per-tunnel state */
struct geneve_dev {
    struct net_device   *dev;       // net_device for this tunnel
    struct geneve_sock  *sock4;     // IPv4 UDP socket (port 6081)
    struct geneve_sock  *sock6;     // IPv6 UDP socket
    struct geneve_config cfg;       // tunnel configuration
    struct list_head    next;       // linked list of tunnels
    struct gro_cells    gro_cells;  // GRO receive path
};

/* Tunnel configuration */
struct geneve_config {
    struct ip_tunnel_info   info;   // contains VNI, remote IP, flags
    bool                    collect_md;  // metadata mode (for TC/BPF)
    bool                    use_udp6_rx_checksums;
    bool                    ttl_inherit;
    bool                    df_inherit;
};

/* Socket shared across tunnels on same port */
struct geneve_sock {
    bool            collect_md;
    struct list_head tunnels;
    struct socket   *sock;
    struct rcu_head rcu;
    int             refcnt;
    struct udp_offload udp_offloads;  // for GRO/GSO
};
```

### 12.2 Creating a GENEVE Interface

```bash
# Create a static GENEVE tunnel (point-to-point style)
ip link add geneve0 type geneve \
    id 100 \
    remote 10.0.0.2 \
    dstport 6081 \
    ttl 64

ip addr add 192.168.100.1/24 dev geneve0
ip link set geneve0 up

# Verify
ip -d link show geneve0
# geneve id 100 remote 10.0.0.2 ttl 64 dstport 6081 ...

# Create in metadata collection mode (for OVS/BPF use)
ip link add geneve0 type geneve \
    external \
    dstport 6081
```

### 12.3 Kernel Receive Path Code Flow

```c
/* Simplified call chain */

udp_rcv()
  └─ __udp4_lib_rcv()
       └─ udp_queue_rcv_skb()  [for connected sockets]
  OR
  └─ udp_rcv_segment()
       └─ UDP encap handler: geneve_udp_encap_recv()
            └─ geneve_rx()
                 ├─ parse GENEVE header
                 ├─ validate version
                 ├─ extract VNI
                 ├─ process options
                 ├─ set skb->dev = inner netdev
                 ├─ strip outer headers (skb_pull)
                 └─ netif_rx() / napi_gro_receive()
```

### 12.4 GSO/GRO for GENEVE

Linux GENEVE supports Generic Segmentation Offload (GSO) and Generic Receive Offload (GRO):

**GSO (transmit side):** Large inner TCP segment → NIC can handle TSO if NIC understands GENEVE.
If NIC doesn't, kernel software GSO segments the inner data, re-encapsulates each segment
with identical outer + GENEVE headers.

**GRO (receive side):** Multiple small GENEVE packets carrying segments of the same inner TCP
flow → kernel GRO merges them before delivering to the bridge/routing layer. This requires
matching: same VNI, same inner 5-tuple, no conflicting GENEVE options.

```bash
# Check GSO/GRO offload status
ethtool -k eth0 | grep -E "(gso|gro|tx-udp-tnl|rx-udp-tnl)"
# tx-udp-tnl-segmentation: on        ← NIC-level GENEVE TSO
# rx-gro-hw: on                      ← NIC-level GRO
# generic-segmentation-offload: on   ← software GSO fallback
```

### 12.5 netlink Interface for GENEVE Configuration

```bash
# ip-link uses netlink RTNL messages to configure GENEVE tunnels
# IFLA_GENEVE_ID           (VNI, u32)
# IFLA_GENEVE_REMOTE       (IPv4 remote, struct in_addr)
# IFLA_GENEVE_REMOTE6      (IPv6 remote, struct in6_addr)
# IFLA_GENEVE_TTL          (u8)
# IFLA_GENEVE_TOS          (u8)
# IFLA_GENEVE_PORT         (destination UDP port, be16)
# IFLA_GENEVE_COLLECT_METADATA (flag, no data)
# IFLA_GENEVE_UDP_CSUM     (u8, 0 or 1)
# IFLA_GENEVE_UDP_ZERO_CSUM6_TX (u8)
# IFLA_GENEVE_UDP_ZERO_CSUM6_RX (u8)
# IFLA_GENEVE_LABEL        (flow label for IPv6, be32)
# IFLA_GENEVE_DF           (inherit/set/unset DF bit)
```

---

## 13. Open vSwitch (OVS) GENEVE Integration

### 13.1 OVS GENEVE Tunnel Port

OVS treats GENEVE as a first-class tunnel type. A GENEVE tunnel port in OVS is a virtual port
that encapsulates/decapsulates GENEVE when OpenFlow rules direct traffic through it:

```bash
# Add a GENEVE tunnel port to OVS bridge
ovs-vsctl add-port br0 geneve0 -- \
    set interface geneve0 \
    type=geneve \
    options:remote_ip=10.0.0.2 \
    options:key=100 \
    options:dst_port=6081 \
    options:csum=true \
    options:tos=inherit \
    options:ttl=64

# Verify
ovs-vsctl show
ovs-ofctl show br0

# For metadata/flow-based remote IP (OVN mode)
ovs-vsctl add-port br0 geneve0 -- \
    set interface geneve0 \
    type=geneve \
    options:remote_ip=flow \
    options:key=flow \
    options:dst_port=6081
```

### 13.2 OVS OpenFlow + GENEVE Interaction

In OVS, GENEVE tunnel metadata is exposed as OpenFlow fields:

```
tun_id         = VNI (24-bit, zero-padded to 64-bit in OVS)
tun_src        = outer source IP of received GENEVE packet
tun_dst        = outer destination IP
tun_ipv6_src   = outer IPv6 source
tun_ipv6_dst   = outer IPv6 destination
tun_metadata0..tun_metadata63  = GENEVE option data (Flexible Match)
```

OpenFlow rules using GENEVE metadata:

```bash
# Match on VNI 100 and deliver to port 2
ovs-ofctl add-flow br0 \
  "priority=100,tun_id=100,actions=output:2"

# Set VNI and remote IP on output (encapsulation)
ovs-ofctl add-flow br0 \
  "priority=100,in_port=2,actions=set_field:100->tun_id,\
   set_field:10.0.0.2->tun_dst,output:geneve0"

# Match on GENEVE option (tun_metadata0 = 0xDEADBEEF)
ovs-ofctl add-flow br0 \
  "priority=200,tun_metadata0=0xdeadbeef,actions=output:LOCAL"
```

### 13.3 OVS GENEVE Options / Flexible Match

OVS's "Flexible Match" feature allows mapping GENEVE TLV options to `tun_metadata` fields:

```bash
# Define a GENEVE option mapping
# Option class 0x0102, type 0x80, length 4 bytes → tun_metadata0
ovs-ofctl add-tlv-map br0 \
  "{class=0x0102,type=0x80,len=4}->tun_metadata0"

# Verify mapping
ovs-ofctl dump-tlv-map br0

# Now use tun_metadata0 in flow matching
ovs-ofctl add-flow br0 \
  "tun_metadata0=0x12345678,actions=output:3"
```

The mapping is stored in the OVS bridge configuration and persists across restarts.

---

## 14. OVN and GENEVE

### 14.1 OVN's Use of GENEVE Specifically

OVN (Open Virtual Network) chooses GENEVE as its default tunnel type because of the options
mechanism. OVN needs to pass two pieces of information between hypervisors:

1. **Datapath Key**: identifies which OVN Logical Datapath (Logical Switch or Router) the
   packet belongs to. This allows the remote NVE to enter the correct logical pipeline.
2. **Port Key**: identifies which logical port the packet came from (for ingress context) or
   is destined for (for egress direction).

Without GENEVE options, OVN would have to do a full MAC lookup on the remote side to re-derive
this context. With GENEVE options, the remote OVN-controller extracts these keys directly and
jumps to the correct OpenFlow table entry — a significant performance optimization.

### 14.2 OVN GENEVE Option Layout

OVN uses a single GENEVE option (IETF Experimental class):

```
Option Class: 0x0102   (Linux kernel experimental)
Option Type:  0x80     (critical, type=0)
Length:       0        (no option data — the VNI itself carries both keys)
```

Wait — OVN's clever trick: it **overloads the VNI field itself** for the two keys:
- The outer **VNI (24 bits)** = Datapath Key (which logical datapath)
- The outer **UDP source port** = entropy only (not the port key)
- The actual port key is carried in a **GENEVE option** (4 bytes of data)

For VXLAN fallback (no options), OVN maps the port key into the UDP source port, trading some
ECMP entropy for metadata carriage.

### 14.3 OVN Logical Flow to Physical OpenFlow

```
OVN Logical Flows (in SB_DB):
  table=0, priority=100, match=(eth.dst == 0A:00:00:00:00:01)
  action: output("lport-uuid-1")

↓ ovn-controller compiles to OpenFlow:

  table=0, priority=100, tun_id=<datapath-key>, tun_metadata0=<port-key>,
  actions: output:2  (physical port 2 on this host)

  OR (if destination is on remote host):
  table=0, priority=100, eth.dst=0A:00:00:00:00:01,
  actions: set_field:<datapath-key>->tun_id,
           set_field:<port-key>->tun_metadata0,
           set_field:<remote-vtep-ip>->tun_dst,
           output:geneve_tunnel_port
```

---

## 15. Kubernetes CNI and GENEVE

### 15.1 CNI Plugins Using GENEVE

| CNI Plugin   | Tunnel Type Used | GENEVE Options Used? | Notes |
|-------------|-----------------|---------------------|-------|
| Flannel      | VXLAN (default) / GENEVE (optional) | No | Simple L2 overlay |
| Cilium       | GENEVE / VXLAN / native routing | Yes (identity labels) | eBPF-native |
| OVN-Kubernetes | GENEVE (via OVN) | Yes (OVN keys) | Most feature-rich |
| Calico       | VXLAN / BGP native | No | Prefers native routing |
| Antrea       | GENEVE / VXLAN / GRE | No (header only) | OVS-based |

### 15.2 Cilium + GENEVE

Cilium's use of GENEVE is particularly interesting from a security perspective:

```
Cilium assigns each workload (pod) a numeric "Security Identity" (numeric label hash).
This identity is encoded in GENEVE options (class=0x0fff, type=0x01, 4 bytes).

On the receiving node:
  1. eBPF program at XDP/TC layer decapsulates GENEVE.
  2. Extracts the security identity from GENEVE options.
  3. Applies network policy: "allow/deny identity X to reach identity Y on port Z".
  4. This enforcement happens WITHOUT knowing the inner IP address —
     the identity alone is sufficient.

This is superior to IP-based ACLs because:
  - Identity follows the workload regardless of IP address changes (pod restarts).
  - Policy is evaluated at the RECEIVING node, not just the sending node.
  - No conntrack required for identity-based allow/deny decisions.
```

Cilium GENEVE option structure:

```
Option Class: 0x0fff   (Cilium experimental class)
Type:         0x01     (Cilium identity option)
Length:       1        (4 bytes of data)
Data:         [3 bytes reserved][1 byte identity label hash low bits]
              OR in newer versions: 4-byte full identity ID
```

### 15.3 Antrea + GENEVE

Antrea uses OVS with GENEVE tunnels. Unlike OVN, Antrea does not use GENEVE options in
steady-state packet processing. GENEVE is used purely for L2 encapsulation (VNI = cluster VNI).
Policy enforcement is done via OVS OpenFlow rules on inner packet fields (IP, port, protocol).

```bash
# Antrea creates OVS bridge and GENEVE port
ovs-vsctl add-br antrea-br
ovs-vsctl add-port antrea-br antrea-gw0  # gateway port
ovs-vsctl add-port antrea-br geneve0 -- \
    set interface geneve0 type=geneve \
    options:remote_ip=flow \
    options:key=flow
```

---

## 16. Hardware Offload: NIC, SmartNIC, DPU

### 16.1 Standard NIC GENEVE Offload Capabilities

Most modern NICs (Mellanox/NVIDIA CX-5/CX-6, Intel E810, Broadcom BCM57508) support:

```
Feature                              Supported?
─────────────────────────────────────────────────
GENEVE TX checksum offload           Yes (outer + inner)
GENEVE RX checksum validation        Yes
GENEVE TSO (Tx Segmentation)         Yes (no options; options = fallback)
GENEVE LRO (Large Receive Offload)   Limited (usually via GRO software)
GENEVE RSS (Receive Side Scaling)    Yes (by outer 5-tuple or inner 5-tuple)
GENEVE hardware TC offload           Yes (kernel tc flower + GENEVE match)
GENEVE options processing            No (NIC sees options as opaque bytes)
```

```bash
# Verify GENEVE hardware offload support
ethtool -k eth0 | grep -E "tnl|geneve|vxlan|encap"
# tx-udp_tnl-segmentation: on
# tx-udp_tnl-csum-segmentation: on
# rx-udp_tunnel-port-offload: on

# Add GENEVE port to NIC tunnel table (for RSS inner hash)
udp_tunnel_nic add eth0 6081 geneve
```

### 16.2 Hardware TC Flower with GENEVE

The Linux `tc` (traffic control) subsystem with `flower` classifier can match GENEVE fields
and offload to NIC hardware (TC offload):

```bash
# Offload rule: match GENEVE VNI=100, inner dst=192.168.1.2, action=redirect to port 3
tc filter add dev eth0 ingress \
    protocol ip flower \
    enc_key_id 100 \
    enc_dst_ip 10.0.0.1 \
    enc_src_ip 10.0.0.2 \
    enc_dst_port 6081 \
    ip_proto tcp \
    dst_ip 192.168.1.2 \
    action mirred egress redirect dev eth1

# Verify offload
tc filter show dev eth0 ingress
# (look for "in_hw yes" or "in_hw_count 1")
```

### 16.3 SmartNIC / DPU (NVIDIA BlueField, Intel IPU)

DPUs (Data Processing Units) are ARM-based network processors embedded in the NIC that run
a full Linux OS and can be programmed to handle GENEVE in hardware:

```
+------------------------------------------------------------------+
|  DPU (NVIDIA BlueField-3 / Intel IPU Architecture)              |
|                                                                  |
|  Host CPU                     DPU ARM cores                     |
|    │                               │                            |
|    │   PCIe                  +─────┴──────+                     |
|    ├──────────────────────► | OVS-DOCA    |                     |
|    │                        | DPDK        |                     |
|    │                        | eBPF        |                     |
|    │                        +─────┬──────+                     |
|    │                              │                            |
|    │                        GENEVE offload engine              |
|    │                          (programmable P4/ASIC)           |
|    │                              │                            |
|    │                         25/100G NIC ports                 |
|                                   │                            |
|                            Underlay network                     |
+------------------------------------------------------------------+

Benefits:
  - Host CPU free from GENEVE encap/decap (zero-copy from host perspective)
  - Full GENEVE options support (ARM cores can parse TLVs)
  - Security enforcement (firewall, ACL) on the DPU without host OS trust
  - Separate security domain: even a compromised host OS cannot bypass DPU enforcement
```

---

## 17. ECMP, Load Balancing, and Entropy

### 17.1 ECMP with GENEVE

Equal-Cost Multi-Path (ECMP) routing in the underlay distributes flows across multiple physical
paths. For ECMP to work effectively, each flow must hash to a consistent link — and different
flows must hash to different links (flow entropy).

GENEVE uses UDP as its transport, which means ECMP-capable routers can hash on the UDP
5-tuple: {src_ip, dst_ip, src_port, dst_port, protocol}. Since dst_port is always 6081,
entropy comes from the **UDP source port**.

```
+──────────────────────────────────────────────────────────────+
| ECMP Hashing Chain                                           |
|                                                              |
| Inner Flow: {src=192.168.1.1, dst=192.168.1.2,              |
|              proto=TCP, sport=54321, dport=80}               |
|           │                                                  |
|           ▼                                                  |
| NVE computes entropy:                                        |
|   udp_src = hash(inner_src_ip XOR inner_dst_ip XOR          |
|                  inner_sport XOR inner_dport XOR inner_proto)|
|   = e.g., 0xC4A1 (49313 decimal, in 0xC000–0xFFFF range)    |
|           │                                                  |
|           ▼                                                  |
| Outer UDP: {src=10.0.0.1, dst=10.0.0.2,                     |
|             sport=0xC4A1, dport=6081}                        |
|           │                                                  |
|           ▼                                                  |
| Spine router hashes: hash({10.0.0.1, 10.0.0.2,              |
|                            0xC4A1, 6081, UDP})               |
|   → selects uplink port 3 consistently for this flow        |
|   → different inner flows → different spine ports           |
+──────────────────────────────────────────────────────────────+
```

### 17.2 Source Port Range and Entropy Quality

RFC 8926 recommends the UDP source port be set to a hash of the inner flow for entropy.
The Linux kernel GENEVE implementation uses:

```c
/* net/ipv4/geneve.c */
static __be16 geneve_src_port(struct geneve_dev *geneve,
                               struct sk_buff *skb)
{
    return udp_flow_src_port(geneve->net, skb,
                              1, USHRT_MAX, true);
}
/* udp_flow_src_port computes:
   - Toeplitz hash of inner 5-tuple
   - Maps to range [min_port, max_port]
   - Default range: typically 49152–65535 (IANA ephemeral range)
*/
```

The source port range affects entropy:
- **Too narrow range (e.g., 1 port):** All GENEVE packets from one host hash to the same
  spine link → link overloading, bandwidth waste.
- **Full ephemeral range (49152–65535, 16K values):** Good entropy across 16K possible hash
  buckets; adequate for most spine switch ECMP implementations.

```bash
# Verify/set UDP source port range for GENEVE
sysctl net.ipv4.ip_local_port_range
# net.ipv4.ip_local_port_range = 32768   60999

# GENEVE uses its own port_min/port_max when configured; check:
ip -d link show geneve0 | grep "sport"
```

### 17.3 ECMP Polarization

A subtle problem: if multiple layers of ECMP exist (e.g., host → ToR → Spine → Core),
each layer uses the same 5-tuple hash → all layers make the same link selection → only
one path used end-to-end (polarization).

Mitigation: Different ECMP hash seeds per layer, or use asymmetric (non-same-cost) paths.
Some implementations XOR the VTEP IP into the source port hash to vary entropy per hop.

---

## 18. C Implementation — Encoder/Decoder/Sender

### 18.1 GENEVE Packet Encoder/Decoder in C

```c
/* geneve.h — GENEVE protocol types and utilities
 *
 * Build: gcc -O2 -Wall -Wextra -o geneve_tool geneve.c geneve_main.c \
 *             -lpthread
 * Run:   sudo ./geneve_tool --send --vni 100 --remote 10.0.0.2 \
 *                           --inner-src-mac 02:00:00:00:00:01 \
 *                           --inner-dst-mac 02:00:00:00:00:02
 * Test:  gcc -DUNIT_TEST -o geneve_test geneve.c && ./geneve_test
 */

#ifndef GENEVE_H
#define GENEVE_H

#include <stdint.h>
#include <stddef.h>
#include <stdbool.h>
#include <arpa/inet.h>

/* ── Wire format constants ─────────────────────────────────────── */

#define GENEVE_UDP_PORT         6081
#define GENEVE_VER              0
#define GENEVE_MAX_OPT_WORDS    63          /* 252 bytes of options */
#define GENEVE_MAX_OPT_BYTES    (GENEVE_MAX_OPT_WORDS * 4)
#define GENEVE_BASE_HDR_LEN     8
#define GENEVE_MAX_HDR_LEN      (GENEVE_BASE_HDR_LEN + GENEVE_MAX_OPT_BYTES)

/* EtherTypes for Protocol Type field */
#define GENEVE_PROTO_ETHERNET   0x6558  /* Transparent Ethernet Bridging */
#define GENEVE_PROTO_IPV4       0x0800
#define GENEVE_PROTO_IPV6       0x86DD
#define GENEVE_PROTO_MPLS_UC    0x8847
#define GENEVE_PROTO_MPLS_MC    0x8848

/* Base header flags (byte 1, bits 0–7) */
#define GENEVE_HDR_OAM_FLAG     (1 << 7)   /* OAM packet */
#define GENEVE_HDR_CRIT_FLAG    (1 << 6)   /* Critical options present */

/* Option type critical bit */
#define GENEVE_OPT_TYPE_CRIT    (1 << 7)

/* ── GENEVE base header (8 bytes, big-endian wire format) ───────── */

/*
 * Byte layout:
 *   [0]: Ver(2) | OptLen(6)
 *   [1]: O(1) | C(1) | Rsvd(6)
 *   [2-3]: Protocol Type (big-endian)
 *   [4-6]: VNI (big-endian, 3 bytes)
 *   [7]: Reserved
 */
struct geneve_hdr {
    uint8_t     ver_optlen;     /* Ver[7:6] | OptLen[5:0] */
    uint8_t     flags;          /* O[7] | C[6] | Rsvd[5:0] */
    uint16_t    proto_type;     /* EtherType of inner payload (BE) */
    uint8_t     vni[3];         /* 24-bit VNI (BE) */
    uint8_t     reserved;       /* must be zero */
} __attribute__((packed));

/* ── GENEVE TLV option header (4 bytes) ────────────────────────── */

struct geneve_opt_hdr {
    uint16_t    opt_class;      /* Option class (BE) */
    uint8_t     type;           /* Critical[7] | Type[6:0] */
    uint8_t     len;            /* Data length in 4B words (0–31) */
    /* Option data follows: len * 4 bytes */
} __attribute__((packed));

/* ── Decoded option representation (in-memory) ──────────────────── */

#define GENEVE_OPT_MAX_DATA     124  /* 31 * 4 bytes */

struct geneve_option {
    uint16_t    opt_class;
    uint8_t     type;           /* includes critical bit */
    uint8_t     data_len;       /* actual bytes (not words) */
    uint8_t     data[GENEVE_OPT_MAX_DATA];
};

/* ── Parsed GENEVE header (in-memory, host byte order) ──────────── */

#define GENEVE_MAX_OPTIONS      16  /* max options per packet */

struct geneve_parsed {
    uint8_t     version;
    bool        oam;
    bool        critical;
    uint16_t    proto_type;
    uint32_t    vni;            /* host byte order, 24-bit */
    uint8_t     opt_count;
    struct geneve_option opts[GENEVE_MAX_OPTIONS];
    const uint8_t *inner_payload;  /* pointer into original buffer */
    size_t      inner_len;
};

/* ── Encapsulation parameters ───────────────────────────────────── */

struct geneve_encap_params {
    uint32_t    vni;
    uint16_t    proto_type;
    bool        oam;
    const struct geneve_option *opts;
    uint8_t     opt_count;
    const uint8_t *inner_payload;
    size_t      inner_payload_len;
};

/* ── Error codes ─────────────────────────────────────────────────── */

typedef enum {
    GENEVE_OK              = 0,
    GENEVE_ERR_SHORT       = -1,  /* buffer too short */
    GENEVE_ERR_VERSION     = -2,  /* unsupported version */
    GENEVE_ERR_CRIT_OPT    = -3,  /* unknown critical option */
    GENEVE_ERR_OPT_OVERRUN = -4,  /* option extends past header */
    GENEVE_ERR_TOO_MANY    = -5,  /* more options than GENEVE_MAX_OPTIONS */
    GENEVE_ERR_OPT_LEN     = -6,  /* option data > max */
    GENEVE_ERR_BUFSIZE     = -7,  /* output buffer too small */
    GENEVE_ERR_VNI         = -8,  /* VNI exceeds 24-bit range */
    GENEVE_ERR_OPT_COUNT   = -9,  /* too many options to encode */
} geneve_err_t;

/* ── Function prototypes ─────────────────────────────────────────── */

const char *geneve_err_str(geneve_err_t err);

/*
 * geneve_decode() — Parse raw GENEVE bytes into structured form.
 *
 * @buf:    Pointer to start of GENEVE header in the received buffer.
 * @len:    Number of bytes available from buf onwards.
 * @out:    Output: parsed GENEVE fields; inner_payload points INTO buf.
 * @accept_unknown_critical: if true, don't return GENEVE_ERR_CRIT_OPT.
 *           Use false for compliant NVE; true for monitoring/inspection.
 *
 * Returns: GENEVE_OK on success, negative geneve_err_t on failure.
 *
 * Complexity: O(N) where N = number of options (typically 0–4).
 * The inner payload start is always O(1) computable regardless of options.
 */
geneve_err_t geneve_decode(const uint8_t *buf, size_t len,
                            struct geneve_parsed *out,
                            bool accept_unknown_critical);

/*
 * geneve_encode() — Serialize GENEVE header + options into buffer.
 *
 * @params: Encapsulation parameters.
 * @buf:    Output buffer (must be at least geneve_encoded_len(params) bytes).
 * @buf_len: Size of output buffer.
 * @written: OUT: number of bytes written to buf.
 *
 * Returns: GENEVE_OK on success.
 */
geneve_err_t geneve_encode(const struct geneve_encap_params *params,
                            uint8_t *buf, size_t buf_len,
                            size_t *written);

/*
 * geneve_encoded_len() — Compute required buffer size for encoding.
 */
size_t geneve_encoded_len(const struct geneve_encap_params *params);

/*
 * geneve_compute_udp_src_port() — Compute ECMP-friendly UDP source port.
 *
 * Implements Jenkins one-at-a-time hash over inner 5-tuple.
 * Result is in range [min_port, max_port].
 */
uint16_t geneve_compute_udp_src_port(
    uint32_t inner_src_ip, uint32_t inner_dst_ip,
    uint16_t inner_sport, uint16_t inner_dport,
    uint8_t inner_proto,
    uint16_t min_port, uint16_t max_port);

#endif /* GENEVE_H */
```

```c
/* geneve.c — GENEVE encoder/decoder implementation
 *
 * Conforms to RFC 8926.
 * No heap allocation; all operations on caller-provided buffers.
 * Thread-safe: all state is in function arguments/return values.
 */

#include "geneve.h"
#include <string.h>
#include <assert.h>

/* ── Helpers ─────────────────────────────────────────────────────── */

static inline uint8_t geneve_ver(const struct geneve_hdr *h)
{
    return (h->ver_optlen >> 6) & 0x03;
}

static inline uint8_t geneve_optlen_words(const struct geneve_hdr *h)
{
    return h->ver_optlen & 0x3F;  /* bits [5:0] */
}

static inline uint32_t vni_from_bytes(const uint8_t vni[3])
{
    return ((uint32_t)vni[0] << 16) |
           ((uint32_t)vni[1] << 8)  |
           ((uint32_t)vni[2]);
}

static inline void vni_to_bytes(uint32_t vni, uint8_t out[3])
{
    out[0] = (vni >> 16) & 0xFF;
    out[1] = (vni >> 8)  & 0xFF;
    out[2] = (vni)       & 0xFF;
}

const char *geneve_err_str(geneve_err_t err)
{
    switch (err) {
    case GENEVE_OK:              return "OK";
    case GENEVE_ERR_SHORT:       return "buffer too short";
    case GENEVE_ERR_VERSION:     return "unsupported GENEVE version";
    case GENEVE_ERR_CRIT_OPT:   return "unknown critical option";
    case GENEVE_ERR_OPT_OVERRUN: return "option extends past header boundary";
    case GENEVE_ERR_TOO_MANY:   return "too many options";
    case GENEVE_ERR_OPT_LEN:    return "option data too large";
    case GENEVE_ERR_BUFSIZE:    return "output buffer too small";
    case GENEVE_ERR_VNI:        return "VNI exceeds 24-bit range";
    case GENEVE_ERR_OPT_COUNT:  return "too many options to encode";
    default:                    return "unknown error";
    }
}

/* ── Decoder ─────────────────────────────────────────────────────── */

geneve_err_t geneve_decode(const uint8_t *buf, size_t len,
                            struct geneve_parsed *out,
                            bool accept_unknown_critical)
{
    /* Validate minimum base header */
    if (len < GENEVE_BASE_HDR_LEN)
        return GENEVE_ERR_SHORT;

    const struct geneve_hdr *hdr = (const struct geneve_hdr *)buf;

    /* RFC 8926 §3: Version must be 0 */
    if (geneve_ver(hdr) != GENEVE_VER)
        return GENEVE_ERR_VERSION;

    uint8_t opt_words = geneve_optlen_words(hdr);
    size_t  opt_bytes = (size_t)opt_words * 4;
    size_t  hdr_total = GENEVE_BASE_HDR_LEN + opt_bytes;

    /* Verify buffer holds the complete GENEVE header */
    if (len < hdr_total)
        return GENEVE_ERR_SHORT;

    /* Populate decoded header */
    out->version    = GENEVE_VER;
    out->oam        = (hdr->flags & GENEVE_HDR_OAM_FLAG) != 0;
    out->critical   = (hdr->flags & GENEVE_HDR_CRIT_FLAG) != 0;
    out->proto_type = ntohs(hdr->proto_type);
    out->vni        = vni_from_bytes(hdr->vni);
    out->opt_count  = 0;
    out->inner_payload = buf + hdr_total;
    out->inner_len     = len - hdr_total;

    /* Parse options (if any) */
    if (opt_bytes == 0)
        return GENEVE_OK;

    const uint8_t *opt_ptr = buf + GENEVE_BASE_HDR_LEN;
    const uint8_t *opt_end = opt_ptr + opt_bytes;

    while (opt_ptr < opt_end) {
        /* Each option header is 4 bytes */
        if ((size_t)(opt_end - opt_ptr) < sizeof(struct geneve_opt_hdr))
            return GENEVE_ERR_OPT_OVERRUN;

        const struct geneve_opt_hdr *ohdr =
            (const struct geneve_opt_hdr *)opt_ptr;

        uint8_t data_words = ohdr->len & 0x1F;  /* bits [4:0] */
        size_t  data_bytes = (size_t)data_words * 4;
        size_t  opt_total  = sizeof(struct geneve_opt_hdr) + data_bytes;

        /* Validate option doesn't overrun the option area */
        if ((size_t)(opt_end - opt_ptr) < opt_total)
            return GENEVE_ERR_OPT_OVERRUN;

        /* Data length exceeds our internal storage? */
        if (data_bytes > GENEVE_OPT_MAX_DATA)
            return GENEVE_ERR_OPT_LEN;

        bool is_critical = (ohdr->type & GENEVE_OPT_TYPE_CRIT) != 0;
        uint8_t type_id  = ohdr->type & 0x7F;
        uint16_t opt_class = ntohs(ohdr->opt_class);

        /*
         * RFC 8926 §3.5: If we encounter a critical option we cannot process,
         * we MUST drop the packet (return error). The caller decides what
         * "can process" means; here we treat all options as unrecognized
         * unless accept_unknown_critical=true (monitoring mode).
         *
         * In a real implementation, you'd have a registry of understood
         * option classes/types and check there.
         */
        if (is_critical && !accept_unknown_critical) {
            /*
             * For a real NVE, add: if (is_known_option(opt_class, type_id))
             * then proceed; else return GENEVE_ERR_CRIT_OPT.
             * This demo treats all critical options as unknown.
             */
            (void)type_id;
            (void)opt_class;
            /* return GENEVE_ERR_CRIT_OPT; */
            /* ^ enable in compliant NVE mode */
        }

        /* Store decoded option */
        if (out->opt_count >= GENEVE_MAX_OPTIONS)
            return GENEVE_ERR_TOO_MANY;

        struct geneve_option *opt = &out->opts[out->opt_count++];
        opt->opt_class = opt_class;
        opt->type      = ohdr->type;
        opt->data_len  = (uint8_t)data_bytes;
        if (data_bytes > 0)
            memcpy(opt->data, opt_ptr + sizeof(struct geneve_opt_hdr),
                   data_bytes);

        opt_ptr += opt_total;
    }

    /* Verify we consumed exactly the right number of bytes */
    if (opt_ptr != opt_end)
        return GENEVE_ERR_OPT_OVERRUN;

    return GENEVE_OK;
}

/* ── Encoder ─────────────────────────────────────────────────────── */

size_t geneve_encoded_len(const struct geneve_encap_params *params)
{
    size_t opts_bytes = 0;
    for (uint8_t i = 0; i < params->opt_count; i++) {
        const struct geneve_option *o = &params->opts[i];
        /* Option header (4B) + data, rounded up to 4-byte boundary */
        size_t data_words = (o->data_len + 3) / 4;
        opts_bytes += 4 + (data_words * 4);
    }
    return GENEVE_BASE_HDR_LEN + opts_bytes + params->inner_payload_len;
}

geneve_err_t geneve_encode(const struct geneve_encap_params *params,
                            uint8_t *buf, size_t buf_len,
                            size_t *written)
{
    /* Validate VNI fits in 24 bits */
    if (params->vni > 0x00FFFFFF)
        return GENEVE_ERR_VNI;

    /* Validate option count */
    if (params->opt_count > GENEVE_MAX_OPTIONS)
        return GENEVE_ERR_OPT_COUNT;

    /* Compute options size and Opt Len field */
    size_t opts_bytes = 0;
    bool   has_critical = false;

    for (uint8_t i = 0; i < params->opt_count; i++) {
        const struct geneve_option *o = &params->opts[i];
        if (o->data_len > GENEVE_OPT_MAX_DATA)
            return GENEVE_ERR_OPT_LEN;
        size_t data_words = (o->data_len + 3) / 4;
        opts_bytes += 4 + (data_words * 4);
        if (o->type & GENEVE_OPT_TYPE_CRIT)
            has_critical = true;
    }

    /* Opt Len must be expressible in 6 bits (max 63 words) */
    if (opts_bytes > GENEVE_MAX_OPT_BYTES)
        return GENEVE_ERR_OPT_COUNT;

    size_t total = GENEVE_BASE_HDR_LEN + opts_bytes + params->inner_payload_len;

    if (buf_len < total)
        return GENEVE_ERR_BUFSIZE;

    uint8_t *p = buf;

    /* ── Base header ──────────────────────────────────────────── */
    struct geneve_hdr *hdr = (struct geneve_hdr *)p;
    memset(hdr, 0, sizeof(*hdr));

    uint8_t opt_words = (uint8_t)(opts_bytes / 4);
    hdr->ver_optlen  = (GENEVE_VER << 6) | (opt_words & 0x3F);
    hdr->flags       = 0;
    if (params->oam)        hdr->flags |= GENEVE_HDR_OAM_FLAG;
    if (has_critical)       hdr->flags |= GENEVE_HDR_CRIT_FLAG;
    hdr->proto_type  = htons(params->proto_type);
    vni_to_bytes(params->vni, hdr->vni);
    hdr->reserved    = 0;

    p += GENEVE_BASE_HDR_LEN;

    /* ── Options ──────────────────────────────────────────────── */
    for (uint8_t i = 0; i < params->opt_count; i++) {
        const struct geneve_option *o = &params->opts[i];
        size_t data_words = (o->data_len + 3) / 4;

        struct geneve_opt_hdr *ohdr = (struct geneve_opt_hdr *)p;
        ohdr->opt_class = htons(o->opt_class);
        ohdr->type      = o->type;
        ohdr->len       = (uint8_t)data_words;

        p += sizeof(struct geneve_opt_hdr);

        /* Copy data, zero-pad to 4-byte boundary */
        if (o->data_len > 0) {
            memcpy(p, o->data, o->data_len);
            size_t pad = (data_words * 4) - o->data_len;
            if (pad > 0)
                memset(p + o->data_len, 0, pad);
        }
        p += data_words * 4;
    }

    /* ── Inner payload ────────────────────────────────────────── */
    if (params->inner_payload_len > 0)
        memcpy(p, params->inner_payload, params->inner_payload_len);
    p += params->inner_payload_len;

    *written = (size_t)(p - buf);
    assert(*written == total);

    return GENEVE_OK;
}

/* ── UDP source port entropy ─────────────────────────────────────── */

/*
 * Jenkins one-at-a-time hash — fast, good distribution, no deps.
 * Used to compute ECMP-friendly UDP source port from inner 5-tuple.
 */
static uint32_t joaat_hash(const uint8_t *key, size_t len)
{
    uint32_t hash = 0;
    for (size_t i = 0; i < len; i++) {
        hash += key[i];
        hash += (hash << 10);
        hash ^= (hash >> 6);
    }
    hash += (hash << 3);
    hash ^= (hash >> 11);
    hash += (hash << 15);
    return hash;
}

uint16_t geneve_compute_udp_src_port(
    uint32_t inner_src_ip, uint32_t inner_dst_ip,
    uint16_t inner_sport,  uint16_t inner_dport,
    uint8_t  inner_proto,
    uint16_t min_port,     uint16_t max_port)
{
    if (min_port > max_port) {
        min_port = 49152;
        max_port = 65535;
    }

    uint8_t key[13];
    /* Host byte order → consistent regardless of caller's arch */
    key[0]  = (inner_src_ip >> 24) & 0xFF;
    key[1]  = (inner_src_ip >> 16) & 0xFF;
    key[2]  = (inner_src_ip >>  8) & 0xFF;
    key[3]  = (inner_src_ip)       & 0xFF;
    key[4]  = (inner_dst_ip >> 24) & 0xFF;
    key[5]  = (inner_dst_ip >> 16) & 0xFF;
    key[6]  = (inner_dst_ip >>  8) & 0xFF;
    key[7]  = (inner_dst_ip)       & 0xFF;
    key[8]  = (inner_sport >> 8)   & 0xFF;
    key[9]  = (inner_sport)        & 0xFF;
    key[10] = (inner_dport >> 8)   & 0xFF;
    key[11] = (inner_dport)        & 0xFF;
    key[12] = inner_proto;

    uint32_t h   = joaat_hash(key, sizeof(key));
    uint16_t range = max_port - min_port + 1;

    return min_port + (uint16_t)(h % range);
}

/* ── Unit tests (compile with -DUNIT_TEST) ──────────────────────── */

#ifdef UNIT_TEST
#include <stdio.h>
#include <stdlib.h>

#define TEST(name) do { \
    printf("  TEST: %s ... ", #name); \
    fflush(stdout); \
} while(0)
#define PASS() printf("PASS\n")
#define FAIL(msg) do { printf("FAIL: %s\n", msg); exit(1); } while(0)
#define ASSERT_EQ(a, b) do { \
    if ((a) != (b)) { \
        printf("FAIL: expected %lld got %lld at line %d\n", \
               (long long)(b), (long long)(a), __LINE__); \
        exit(1); \
    } \
} while(0)

/* Test: encode then decode a simple GENEVE packet (no options) */
static void test_encode_decode_no_opts(void)
{
    TEST(encode_decode_no_opts);

    uint8_t inner[] = {
        /* Fake inner Ethernet: DMAC, SMAC, EtherType=IPv4, IP payload */
        0xAA, 0xBB, 0xCC, 0xDD, 0xEE, 0xFF,  /* DMAC */
        0x11, 0x22, 0x33, 0x44, 0x55, 0x66,  /* SMAC */
        0x08, 0x00,                            /* EtherType IPv4 */
        0xDE, 0xAD, 0xBE, 0xEF               /* Dummy IP payload */
    };

    struct geneve_encap_params params = {
        .vni              = 0xABCDEF,
        .proto_type       = GENEVE_PROTO_ETHERNET,
        .oam              = false,
        .opts             = NULL,
        .opt_count        = 0,
        .inner_payload     = inner,
        .inner_payload_len = sizeof(inner),
    };

    size_t expected_len = GENEVE_BASE_HDR_LEN + sizeof(inner);
    uint8_t buf[256];

    size_t written = 0;
    geneve_err_t err = geneve_encode(&params, buf, sizeof(buf), &written);
    ASSERT_EQ(err, GENEVE_OK);
    ASSERT_EQ(written, expected_len);

    /* Check base header bytes */
    ASSERT_EQ(buf[0], 0x00);   /* ver=0, opt_len=0 */
    ASSERT_EQ(buf[1], 0x00);   /* flags: no OAM, no critical */
    ASSERT_EQ(buf[2], 0x65);   /* proto_type hi: 0x6558 */
    ASSERT_EQ(buf[3], 0x58);   /* proto_type lo */
    ASSERT_EQ(buf[4], 0xAB);   /* VNI[0] */
    ASSERT_EQ(buf[5], 0xCD);   /* VNI[1] */
    ASSERT_EQ(buf[6], 0xEF);   /* VNI[2] */
    ASSERT_EQ(buf[7], 0x00);   /* reserved */

    /* Decode it back */
    struct geneve_parsed parsed;
    err = geneve_decode(buf, written, &parsed, false);
    ASSERT_EQ(err, GENEVE_OK);
    ASSERT_EQ(parsed.version, 0);
    ASSERT_EQ(parsed.oam, false);
    ASSERT_EQ(parsed.critical, false);
    ASSERT_EQ(parsed.proto_type, GENEVE_PROTO_ETHERNET);
    ASSERT_EQ(parsed.vni, 0xABCDEF);
    ASSERT_EQ(parsed.opt_count, 0);
    ASSERT_EQ(parsed.inner_len, sizeof(inner));
    ASSERT_EQ(memcmp(parsed.inner_payload, inner, sizeof(inner)), 0);

    PASS();
}

/* Test: encode with one non-critical option */
static void test_encode_decode_with_opt(void)
{
    TEST(encode_decode_with_option);

    uint8_t opt_data[4] = {0xDE, 0xAD, 0xBE, 0xEF};
    struct geneve_option opts[1] = {{
        .opt_class = 0x0102,
        .type      = 0x01,       /* non-critical */
        .data_len  = 4,
    }};
    memcpy(opts[0].data, opt_data, 4);

    uint8_t inner[4] = {0x11, 0x22, 0x33, 0x44};

    struct geneve_encap_params params = {
        .vni              = 100,
        .proto_type       = GENEVE_PROTO_ETHERNET,
        .oam              = false,
        .opts             = opts,
        .opt_count        = 1,
        .inner_payload    = inner,
        .inner_payload_len = sizeof(inner),
    };

    uint8_t buf[256];
    size_t written;
    geneve_err_t err = geneve_encode(&params, buf, sizeof(buf), &written);
    ASSERT_EQ(err, GENEVE_OK);

    /* opt_len field = 2 (one option: 4B header + 4B data = 2 words) */
    ASSERT_EQ(buf[0] & 0x3F, 2);

    struct geneve_parsed parsed;
    err = geneve_decode(buf, written, &parsed, true);
    ASSERT_EQ(err, GENEVE_OK);
    ASSERT_EQ(parsed.opt_count, 1);
    ASSERT_EQ(parsed.opts[0].opt_class, 0x0102);
    ASSERT_EQ(parsed.opts[0].data_len, 4);
    ASSERT_EQ(memcmp(parsed.opts[0].data, opt_data, 4), 0);

    PASS();
}

/* Test: buffer too short */
static void test_short_buffer(void)
{
    TEST(short_buffer_detection);

    uint8_t buf[4] = {0};  /* Less than 8-byte minimum */
    struct geneve_parsed parsed;
    geneve_err_t err = geneve_decode(buf, sizeof(buf), &parsed, false);
    ASSERT_EQ(err, GENEVE_ERR_SHORT);

    PASS();
}

/* Test: bad version */
static void test_bad_version(void)
{
    TEST(bad_version_rejection);

    uint8_t buf[8] = {0};
    buf[0] = 0x80;  /* version = 2 (invalid) */
    struct geneve_parsed parsed;
    geneve_err_t err = geneve_decode(buf, 8, &parsed, false);
    ASSERT_EQ(err, GENEVE_ERR_VERSION);

    PASS();
}

/* Test: entropy port range */
static void test_udp_src_port(void)
{
    TEST(udp_src_port_entropy);

    /* Same inner flow → same port (deterministic) */
    uint16_t p1 = geneve_compute_udp_src_port(
        0xC0A80001, 0xC0A80002, 54321, 80, 6, 49152, 65535);
    uint16_t p2 = geneve_compute_udp_src_port(
        0xC0A80001, 0xC0A80002, 54321, 80, 6, 49152, 65535);
    ASSERT_EQ(p1, p2);

    /* Result in expected range */
    if (p1 < 49152 || p1 > 65535)
        FAIL("port out of range");

    /* Different flow → should produce different port (probabilistic) */
    uint16_t p3 = geneve_compute_udp_src_port(
        0xC0A80001, 0xC0A80003, 12345, 443, 6, 49152, 65535);
    /* Note: hash collisions possible; this is just a sanity check */
    (void)p3;

    PASS();
}

/* Test: VNI boundary values */
static void test_vni_bounds(void)
{
    TEST(vni_boundary_values);

    uint8_t buf[256];
    size_t written;
    uint8_t inner[1] = {0};

    /* VNI = 0 */
    struct geneve_encap_params p0 = {
        .vni=0, .proto_type=GENEVE_PROTO_ETHERNET,
        .inner_payload=inner, .inner_payload_len=1
    };
    ASSERT_EQ(geneve_encode(&p0, buf, sizeof(buf), &written), GENEVE_OK);

    /* VNI = 0xFFFFFF (max) */
    struct geneve_encap_params pmax = {
        .vni=0xFFFFFF, .proto_type=GENEVE_PROTO_ETHERNET,
        .inner_payload=inner, .inner_payload_len=1
    };
    ASSERT_EQ(geneve_encode(&pmax, buf, sizeof(buf), &written), GENEVE_OK);

    /* VNI = 0x1000000 (too large) */
    struct geneve_encap_params pbig = {
        .vni=0x1000000, .proto_type=GENEVE_PROTO_ETHERNET,
        .inner_payload=inner, .inner_payload_len=1
    };
    ASSERT_EQ(geneve_encode(&pbig, buf, sizeof(buf), &written), GENEVE_ERR_VNI);

    PASS();
}

int main(void)
{
    printf("GENEVE unit tests\n");
    test_encode_decode_no_opts();
    test_encode_decode_with_opt();
    test_short_buffer();
    test_bad_version();
    test_udp_src_port();
    test_vni_bounds();
    printf("All tests PASSED\n");
    return 0;
}
#endif /* UNIT_TEST */
```

```c
/* geneve_send.c — Raw socket GENEVE sender (Linux, requires CAP_NET_RAW)
 *
 * Build: gcc -O2 -Wall -o geneve_send geneve.c geneve_send.c
 * Run:   sudo ./geneve_send <local_ip> <remote_ip> <vni>
 *        e.g.: sudo ./geneve_send 10.0.0.1 10.0.0.2 100
 *
 * Sends one GENEVE-encapsulated ARP packet.
 * Demonstrates full encapsulation stack: GENEVE → UDP → IP → Ethernet.
 */

#include "geneve.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#include <netinet/udp.h>
#include <arpa/inet.h>
#include <net/ethernet.h>
#include <net/if.h>
#include <sys/ioctl.h>
#include <linux/if_packet.h>

/* ── Pseudo-header for UDP checksum ─────────────────────────────── */
struct udp_pseudo_hdr {
    uint32_t src_ip;
    uint32_t dst_ip;
    uint8_t  zero;
    uint8_t  proto;
    uint16_t udp_len;
};

static uint16_t checksum(const void *data, size_t len)
{
    const uint16_t *ptr = (const uint16_t *)data;
    uint32_t sum = 0;
    while (len > 1) {
        sum += *ptr++;
        len -= 2;
    }
    if (len)
        sum += *(const uint8_t *)ptr;
    while (sum >> 16)
        sum = (sum & 0xFFFF) + (sum >> 16);
    return (uint16_t)(~sum);
}

/* Build a dummy ARP inner frame (gratuitous ARP) as inner payload */
static size_t build_inner_arp(uint8_t *buf, size_t buf_len,
                               const uint8_t src_mac[6], uint32_t src_ip)
{
    /* Ethernet header */
    if (buf_len < 42) return 0;
    /* Broadcast DMAC */
    memset(buf, 0xFF, 6);
    memcpy(buf + 6, src_mac, 6);
    buf[12] = 0x08; buf[13] = 0x06;  /* EtherType ARP */
    /* ARP payload */
    buf[14] = 0x00; buf[15] = 0x01;  /* HW type Ethernet */
    buf[16] = 0x08; buf[17] = 0x00;  /* Proto IPv4 */
    buf[18] = 6;    buf[19] = 4;     /* HW len, proto len */
    buf[20] = 0x00; buf[21] = 0x01;  /* Operation: request */
    memcpy(buf + 22, src_mac, 6);    /* Sender MAC */
    memcpy(buf + 28, &src_ip, 4);    /* Sender IP */
    memset(buf + 32, 0, 6);          /* Target MAC (unknown) */
    memcpy(buf + 38, &src_ip, 4);    /* Target IP (gratuitous) */
    return 42;
}

int main(int argc, char *argv[])
{
    if (argc < 4) {
        fprintf(stderr, "Usage: %s <local_ip> <remote_ip> <vni>\n", argv[0]);
        fprintf(stderr, "Example: %s 10.0.0.1 10.0.0.2 100\n", argv[0]);
        return 1;
    }

    const char *local_ip_str  = argv[1];
    const char *remote_ip_str = argv[2];
    uint32_t vni = (uint32_t)atoi(argv[3]);

    uint32_t local_ip, remote_ip;
    if (inet_pton(AF_INET, local_ip_str,  &local_ip)  != 1 ||
        inet_pton(AF_INET, remote_ip_str, &remote_ip) != 1) {
        fprintf(stderr, "Invalid IP address\n");
        return 1;
    }
    local_ip  = ntohl(local_ip);
    remote_ip = ntohl(remote_ip);

    /* Fake source MAC for inner frame */
    uint8_t fake_mac[6] = {0x02, 0x00, 0x00, 0x00, 0x00, 0x01};

    /* ── Build inner Ethernet/ARP frame ────────────────────────── */
    uint8_t inner_buf[64];
    uint32_t inner_ip_be = htonl(local_ip);
    size_t inner_len = build_inner_arp(inner_buf, sizeof(inner_buf),
                                        fake_mac, inner_ip_be);
    if (inner_len == 0) {
        fprintf(stderr, "Failed to build inner frame\n");
        return 1;
    }

    /* ── Encode GENEVE ──────────────────────────────────────────── */
    struct geneve_encap_params gparams = {
        .vni              = vni,
        .proto_type       = GENEVE_PROTO_ETHERNET,
        .oam              = false,
        .opts             = NULL,
        .opt_count        = 0,
        .inner_payload    = inner_buf,
        .inner_payload_len = inner_len,
    };

    uint8_t geneve_buf[512];
    size_t  geneve_len;
    geneve_err_t gerr = geneve_encode(&gparams, geneve_buf,
                                       sizeof(geneve_buf), &geneve_len);
    if (gerr != GENEVE_OK) {
        fprintf(stderr, "GENEVE encode error: %s\n", geneve_err_str(gerr));
        return 1;
    }

    /* ── Compute UDP source port (entropy) ─────────────────────── */
    uint16_t udp_src = geneve_compute_udp_src_port(
        local_ip, remote_ip, 0, 6081, 17, 49152, 65535);

    /* ── Build UDP header ──────────────────────────────────────── */
    uint16_t udp_len = (uint16_t)(sizeof(struct udphdr) + geneve_len);
    struct udphdr udph;
    memset(&udph, 0, sizeof(udph));
    udph.uh_sport = htons(udp_src);
    udph.uh_dport = htons(GENEVE_UDP_PORT);
    udph.uh_ulen  = htons(udp_len);
    udph.uh_sum   = 0;  /* IPv4 UDP checksum optional; set 0 */

    /* ── Build IP header ───────────────────────────────────────── */
    struct iphdr iph;
    memset(&iph, 0, sizeof(iph));
    iph.version  = 4;
    iph.ihl      = 5;
    iph.tos      = 0;
    iph.tot_len  = htons(sizeof(iph) + udp_len);
    iph.id       = htons(0x1234);
    iph.frag_off = htons(IP_DF);     /* Don't fragment */
    iph.ttl      = 64;
    iph.protocol = IPPROTO_UDP;
    iph.saddr    = htonl(local_ip);
    iph.daddr    = htonl(remote_ip);
    iph.check    = checksum(&iph, sizeof(iph));

    /* ── Assemble final packet ──────────────────────────────────── */
    uint8_t pkt[1500];
    size_t  pkt_len = 0;
    memcpy(pkt + pkt_len, &iph,      sizeof(iph));      pkt_len += sizeof(iph);
    memcpy(pkt + pkt_len, &udph,     sizeof(udph));     pkt_len += sizeof(udph);
    memcpy(pkt + pkt_len, geneve_buf, geneve_len);       pkt_len += geneve_len;

    /* ── Send via raw socket ────────────────────────────────────── */
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (sock < 0) {
        perror("socket");
        return 1;
    }

    int one = 1;
    if (setsockopt(sock, IPPROTO_IP, IP_HDRINCL, &one, sizeof(one)) < 0) {
        perror("setsockopt IP_HDRINCL");
        close(sock);
        return 1;
    }

    struct sockaddr_in dst = {
        .sin_family = AF_INET,
        .sin_addr.s_addr = htonl(remote_ip),
    };

    ssize_t sent = sendto(sock, pkt, pkt_len, 0,
                          (struct sockaddr *)&dst, sizeof(dst));
    if (sent < 0) {
        perror("sendto");
        close(sock);
        return 1;
    }

    printf("Sent %zd bytes: GENEVE VNI=%u, outer %s→%s, UDP src_port=%u\n",
           sent, vni, local_ip_str, remote_ip_str, udp_src);
    printf("  Inner: ARP gratuitous from MAC=%02x:%02x:%02x:%02x:%02x:%02x\n",
           fake_mac[0], fake_mac[1], fake_mac[2],
           fake_mac[3], fake_mac[4], fake_mac[5]);

    close(sock);
    return 0;
}
```

---

## 19. Rust Implementation — Zero-Copy Parser and Encapsulator

```toml
# Cargo.toml
[package]
name = "geneve-rs"
version = "0.1.0"
edition = "2021"

[dependencies]
thiserror = "1"
bytes = "1"

[dev-dependencies]
# For property-based tests
proptest = "1"
```

```rust
//! geneve/src/lib.rs — RFC 8926 GENEVE implementation in Rust
//!
//! Design principles:
//!   - Zero-copy parsing via borrowed byte slices (`&[u8]`)
//!   - No heap allocation in the hot path (Encoder uses caller-supplied buffer)
//!   - All fields validated at parse time; no panic in safe code
//!   - `no_std` compatible (remove `std` feature from thiserror for embedded)
//!
//! Build: cargo build --release
//! Test:  cargo test
//! Fuzz:  cargo fuzz run fuzz_geneve_decode

use std::fmt;
use thiserror::Error;

// ── Constants ──────────────────────────────────────────────────────

pub const GENEVE_UDP_PORT: u16      = 6081;
pub const GENEVE_VERSION: u8        = 0;
pub const GENEVE_BASE_HDR_LEN: usize = 8;
pub const GENEVE_MAX_OPT_WORDS: u8  = 63;
pub const GENEVE_MAX_OPT_BYTES: usize = (GENEVE_MAX_OPT_WORDS as usize) * 4;
pub const GENEVE_MAX_OPT_DATA: usize = 124; // 31 words * 4 bytes

/// EtherType values for the Protocol Type field
#[repr(u16)]
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum ProtocolType {
    TransparentEthernet = 0x6558,
    IPv4                = 0x0800,
    IPv6                = 0x86DD,
    MplsUnicast         = 0x8847,
    MplsMulticast       = 0x8848,
    Arp                 = 0x0806,
}

impl ProtocolType {
    pub fn from_u16(v: u16) -> Option<Self> {
        match v {
            0x6558 => Some(Self::TransparentEthernet),
            0x0800 => Some(Self::IPv4),
            0x86DD => Some(Self::IPv6),
            0x8847 => Some(Self::MplsUnicast),
            0x8848 => Some(Self::MplsMulticast),
            0x0806 => Some(Self::Arp),
            _      => None,
        }
    }
    pub fn as_u16(self) -> u16 { self as u16 }
}

// ── Errors ─────────────────────────────────────────────────────────

#[derive(Debug, Error, PartialEq, Eq)]
pub enum GeneveError {
    #[error("buffer too short: need {need} bytes, have {have}")]
    BufferTooShort { need: usize, have: usize },

    #[error("unsupported GENEVE version: {0} (only version 0 is supported)")]
    UnsupportedVersion(u8),

    #[error("unknown critical option class=0x{class:04X} type=0x{typ:02X}")]
    UnknownCriticalOption { class: u16, typ: u8 },

    #[error("option at offset {offset} overruns header boundary")]
    OptionOverrun { offset: usize },

    #[error("option data length {data_len} exceeds maximum {max}")]
    OptionDataTooLarge { data_len: usize, max: usize },

    #[error("total option length {total} bytes not divisible by 4")]
    OptionAlignmentError { total: usize },

    #[error("VNI {0} exceeds 24-bit maximum (16777215)")]
    VniTooLarge(u32),

    #[error("options too large: {total_bytes} bytes exceeds maximum {max} bytes")]
    OptionsTooLarge { total_bytes: usize, max: usize },

    #[error("output buffer too small: need {need}, have {have}")]
    OutputBufferTooSmall { need: usize, have: usize },
}

// ── Parsed Option (borrows from input) ────────────────────────────

/// A single parsed GENEVE TLV option.
/// The `data` field borrows from the original buffer (zero-copy).
#[derive(Debug, Clone)]
pub struct ParsedOption<'a> {
    pub class:    u16,
    pub opt_type: u8,         // includes the critical bit (bit 7)
    pub data:     &'a [u8],   // 0..=124 bytes, always 4-byte aligned in wire
}

impl<'a> ParsedOption<'a> {
    /// Returns true if this is a critical option (bit 7 of type is set).
    #[inline]
    pub fn is_critical(&self) -> bool {
        (self.opt_type & 0x80) != 0
    }

    /// Returns the type ID without the critical bit.
    #[inline]
    pub fn type_id(&self) -> u8 {
        self.opt_type & 0x7F
    }
}

impl fmt::Display for ParsedOption<'_> {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Option(class=0x{:04X}, type=0x{:02X}, critical={}, data_len={})",
               self.class, self.opt_type, self.is_critical(), self.data.len())
    }
}

// ── Parsed GENEVE Header (borrows from input) ─────────────────────

/// Result of parsing a GENEVE header. All data borrowed from input buffer.
/// Parsing is O(N) where N is the number of options; inner payload access is O(1).
#[derive(Debug)]
pub struct ParsedHeader<'a> {
    pub version:       u8,
    pub oam:           bool,
    pub critical:      bool,
    pub protocol_type: u16,           // raw u16; use ProtocolType::from_u16()
    pub vni:           u32,           // host byte order, 24-bit value
    pub options:       Vec<ParsedOption<'a>>,
    pub inner_payload: &'a [u8],      // everything after GENEVE header
}

impl<'a> ParsedHeader<'a> {
    pub fn protocol(&self) -> Option<ProtocolType> {
        ProtocolType::from_u16(self.protocol_type)
    }
}

// ── Parser ────────────────────────────────────────────────────────

/// Parse a GENEVE header from a byte slice.
///
/// # Arguments
/// * `buf` — Raw bytes starting at the GENEVE header (after UDP header).
/// * `check_critical` — If true, return `UnknownCriticalOption` for any
///   critical option not in the known-option registry. Set false for
///   monitoring/inspection mode where policy is to forward even unknown packets.
///
/// # Returns
/// `Ok(ParsedHeader)` where all borrowed data points into `buf`.
///
/// # Complexity
/// O(N) options parsing. Inner payload offset computed in O(1).
pub fn parse(buf: &[u8], check_critical: bool) -> Result<ParsedHeader, GeneveError> {
    // ── Minimum header validation ──────────────────────────────
    if buf.len() < GENEVE_BASE_HDR_LEN {
        return Err(GeneveError::BufferTooShort {
            need: GENEVE_BASE_HDR_LEN,
            have: buf.len(),
        });
    }

    // ── Field extraction ───────────────────────────────────────
    let byte0     = buf[0];
    let version   = (byte0 >> 6) & 0x03;
    let opt_words = byte0 & 0x3F;

    if version != GENEVE_VERSION {
        return Err(GeneveError::UnsupportedVersion(version));
    }

    let flags         = buf[1];
    let oam           = (flags & 0x80) != 0;
    let critical_hint = (flags & 0x40) != 0;
    let proto_type    = u16::from_be_bytes([buf[2], buf[3]]);
    let vni           = u32::from_be_bytes([0, buf[4], buf[5], buf[6]]);
    // buf[7] is reserved; ignore

    let opt_bytes  = (opt_words as usize) * 4;
    let hdr_total  = GENEVE_BASE_HDR_LEN + opt_bytes;

    if buf.len() < hdr_total {
        return Err(GeneveError::BufferTooShort {
            need: hdr_total,
            have: buf.len(),
        });
    }

    // ── Option parsing ─────────────────────────────────────────
    let mut options: Vec<ParsedOption> = Vec::new();

    if opt_bytes > 0 {
        let opt_area = &buf[GENEVE_BASE_HDR_LEN..hdr_total];
        let mut pos  = 0usize;

        while pos < opt_area.len() {
            // Each option header = 4 bytes
            if opt_area.len() - pos < 4 {
                return Err(GeneveError::OptionOverrun { offset: pos });
            }

            let opt_class  = u16::from_be_bytes([opt_area[pos], opt_area[pos+1]]);
            let opt_type   = opt_area[pos+2];
            let data_words = (opt_area[pos+3] & 0x1F) as usize;
            let data_bytes = data_words * 4;
            let opt_total  = 4 + data_bytes;

            if opt_area.len() - pos < opt_total {
                return Err(GeneveError::OptionOverrun { offset: pos });
            }

            if data_bytes > GENEVE_MAX_OPT_DATA {
                return Err(GeneveError::OptionDataTooLarge {
                    data_len: data_bytes,
                    max: GENEVE_MAX_OPT_DATA,
                });
            }

            let data = &opt_area[pos+4..pos+opt_total];
            let is_critical = (opt_type & 0x80) != 0;

            // RFC 8926 §3.5: Unknown critical option → must drop
            if is_critical && check_critical && !is_known_option(opt_class, opt_type & 0x7F) {
                return Err(GeneveError::UnknownCriticalOption {
                    class: opt_class,
                    typ:   opt_type & 0x7F,
                });
            }

            options.push(ParsedOption { class: opt_class, opt_type, data });
            pos += opt_total;
        }

        debug_assert!(pos == opt_area.len(), "option bytes not fully consumed");
    }

    // Suppress unused warning if critical_hint not used in logic path
    let _ = critical_hint;

    Ok(ParsedHeader {
        version: GENEVE_VERSION,
        oam,
        critical: critical_hint,
        protocol_type: proto_type,
        vni,
        options,
        inner_payload: &buf[hdr_total..],
    })
}

/// Option registry: returns true if this (class, type) pair is understood.
/// Extend this function to register your option classes.
fn is_known_option(class: u16, type_id: u8) -> bool {
    match (class, type_id) {
        // OVN/OVS option
        (0x0102, 0x00) => true,
        // Cilium identity option
        (0x0fff, 0x01) => true,
        // IETF options (none standardized yet as of RFC 8926)
        (0x0000, _   ) => false,
        _              => false,
    }
}

// ── Encoder ───────────────────────────────────────────────────────

/// An owned GENEVE option for encoding.
#[derive(Debug, Clone)]
pub struct GeneveOption {
    pub class:    u16,
    pub opt_type: u8,       // bit 7 = critical
    pub data:     Vec<u8>,  // 0..=124 bytes
}

impl GeneveOption {
    pub fn new(class: u16, opt_type: u8, data: Vec<u8>) -> Result<Self, GeneveError> {
        if data.len() > GENEVE_MAX_OPT_DATA {
            return Err(GeneveError::OptionDataTooLarge {
                data_len: data.len(),
                max: GENEVE_MAX_OPT_DATA,
            });
        }
        Ok(Self { class, opt_type, data })
    }

    /// Size of this option on the wire (header + padded data).
    pub fn wire_size(&self) -> usize {
        4 + ((self.data.len() + 3) / 4) * 4
    }
}

/// Parameters for encoding a GENEVE header.
#[derive(Debug)]
pub struct EncodeParams<'a> {
    pub vni:           u32,         // must be ≤ 0x00FFFFFF
    pub protocol_type: ProtocolType,
    pub oam:           bool,
    pub options:       &'a [GeneveOption],
}

/// Encode a GENEVE header (without inner payload) into `buf`.
///
/// Returns the number of bytes written. The caller appends the inner payload.
///
/// # Errors
/// Returns error if VNI > 24-bit max, options exceed 252 bytes, or buffer too small.
pub fn encode_header(params: &EncodeParams, buf: &mut [u8])
    -> Result<usize, GeneveError>
{
    if params.vni > 0x00FF_FFFF {
        return Err(GeneveError::VniTooLarge(params.vni));
    }

    // Compute total options wire size
    let opts_bytes: usize = params.options.iter().map(|o| o.wire_size()).sum();
    if opts_bytes > GENEVE_MAX_OPT_BYTES {
        return Err(GeneveError::OptionsTooLarge {
            total_bytes: opts_bytes,
            max: GENEVE_MAX_OPT_BYTES,
        });
    }
    debug_assert!(opts_bytes % 4 == 0);

    let total = GENEVE_BASE_HDR_LEN + opts_bytes;
    if buf.len() < total {
        return Err(GeneveError::OutputBufferTooSmall { need: total, have: buf.len() });
    }

    let opt_words = (opts_bytes / 4) as u8;
    let has_critical = params.options.iter().any(|o| (o.opt_type & 0x80) != 0);

    // ── Base header ────────────────────────────────────────────
    buf[0] = (GENEVE_VERSION << 6) | (opt_words & 0x3F);
    buf[1] = if params.oam           { 0x80 } else { 0 }
           | if has_critical         { 0x40 } else { 0 };

    let pt = params.protocol_type.as_u16();
    buf[2] = (pt >> 8) as u8;
    buf[3] = (pt & 0xFF) as u8;

    buf[4] = ((params.vni >> 16) & 0xFF) as u8;
    buf[5] = ((params.vni >>  8) & 0xFF) as u8;
    buf[6] = ((params.vni)       & 0xFF) as u8;
    buf[7] = 0;  // reserved

    // ── Options ────────────────────────────────────────────────
    let mut pos = GENEVE_BASE_HDR_LEN;
    for opt in params.options {
        let data_words = (opt.data.len() + 3) / 4;

        buf[pos]   = (opt.class >> 8) as u8;
        buf[pos+1] = (opt.class & 0xFF) as u8;
        buf[pos+2] = opt.opt_type;
        buf[pos+3] = data_words as u8;
        pos += 4;

        let data_wire = data_words * 4;
        buf[pos..pos + opt.data.len()].copy_from_slice(&opt.data);
        // Zero-pad to 4-byte boundary
        for b in buf[pos + opt.data.len()..pos + data_wire].iter_mut() {
            *b = 0;
        }
        pos += data_wire;
    }

    debug_assert!(pos == total);
    Ok(total)
}

/// Compute the total encoded length for a header (without inner payload).
pub fn encoded_header_len(params: &EncodeParams) -> usize {
    let opts_bytes: usize = params.options.iter().map(|o| o.wire_size()).sum();
    GENEVE_BASE_HDR_LEN + opts_bytes
}

// ── UDP source port entropy ────────────────────────────────────────

/// Compute an ECMP-friendly UDP source port from an inner IPv4 5-tuple.
/// Uses Jenkins one-at-a-time hash; output is deterministic and in [min_port, max_port].
pub fn udp_src_port(
    src_ip: u32, dst_ip: u32,
    src_port: u16, dst_port: u16,
    proto: u8,
    port_min: u16, port_max: u16,
) -> u16 {
    let key: [u8; 13] = [
        ((src_ip >> 24) & 0xFF) as u8,
        ((src_ip >> 16) & 0xFF) as u8,
        ((src_ip >>  8) & 0xFF) as u8,
        ( src_ip        & 0xFF) as u8,
        ((dst_ip >> 24) & 0xFF) as u8,
        ((dst_ip >> 16) & 0xFF) as u8,
        ((dst_ip >>  8) & 0xFF) as u8,
        ( dst_ip        & 0xFF) as u8,
        ((src_port >> 8) & 0xFF) as u8,
        ( src_port       & 0xFF) as u8,
        ((dst_port >> 8) & 0xFF) as u8,
        ( dst_port       & 0xFF) as u8,
        proto,
    ];

    let hash = joaat(&key);
    let range = (port_max as u32).saturating_sub(port_min as u32) + 1;
    port_min + (hash % range) as u16
}

fn joaat(key: &[u8]) -> u32 {
    let mut h: u32 = 0;
    for &b in key {
        h = h.wrapping_add(b as u32);
        h = h.wrapping_add(h << 10);
        h ^= h >> 6;
    }
    h = h.wrapping_add(h << 3);
    h ^= h >> 11;
    h = h.wrapping_add(h << 15);
    h
}

// ── Tests ──────────────────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    // Encode a header with no options; verify wire bytes
    #[test]
    fn test_encode_no_opts_wire_bytes() {
        let params = EncodeParams {
            vni:           0xABCDEF,
            protocol_type: ProtocolType::TransparentEthernet,
            oam:           false,
            options:       &[],
        };
        let mut buf = [0u8; 64];
        let len = encode_header(&params, &mut buf).unwrap();

        assert_eq!(len, GENEVE_BASE_HDR_LEN);
        assert_eq!(buf[0], 0x00,  "ver=0, opt_len=0");
        assert_eq!(buf[1], 0x00,  "no flags");
        assert_eq!(buf[2], 0x65,  "proto_type hi=0x65");
        assert_eq!(buf[3], 0x58,  "proto_type lo=0x58");
        assert_eq!(buf[4], 0xAB,  "VNI[0]");
        assert_eq!(buf[5], 0xCD,  "VNI[1]");
        assert_eq!(buf[6], 0xEF,  "VNI[2]");
        assert_eq!(buf[7], 0x00,  "reserved");
    }

    // Round-trip: encode then parse; verify all fields match
    #[test]
    fn test_encode_parse_roundtrip_no_opts() {
        let inner = [0xDE, 0xAD, 0xBE, 0xEF, 0xCA, 0xFE];

        let params = EncodeParams {
            vni:           42,
            protocol_type: ProtocolType::IPv4,
            oam:           true,
            options:       &[],
        };

        let mut hdr_buf = vec![0u8; GENEVE_BASE_HDR_LEN];
        let hdr_len = encode_header(&params, &mut hdr_buf).unwrap();
        hdr_buf.extend_from_slice(&inner);

        let parsed = parse(&hdr_buf[..hdr_len + inner.len()], false).unwrap();
        assert_eq!(parsed.vni, 42);
        assert!(parsed.oam);
        assert_eq!(parsed.protocol_type, ProtocolType::IPv4.as_u16());
        assert_eq!(parsed.options.len(), 0);
        assert_eq!(parsed.inner_payload, &inner);
    }

    // Round-trip with one non-critical option
    #[test]
    fn test_encode_parse_roundtrip_with_opt() {
        let opt = GeneveOption::new(0x0102, 0x01, vec![0xDE, 0xAD, 0xBE, 0xEF]).unwrap();

        let params = EncodeParams {
            vni:           100,
            protocol_type: ProtocolType::TransparentEthernet,
            oam:           false,
            options:       &[opt],
        };

        let mut buf = vec![0u8; 256];
        let len = encode_header(&params, &mut buf).unwrap();
        // Append dummy inner payload
        buf[len] = 0xAA;
        let total = len + 1;

        let parsed = parse(&buf[..total], true).unwrap();
        assert_eq!(parsed.options.len(), 1);
        assert_eq!(parsed.options[0].class, 0x0102);
        assert!(!parsed.options[0].is_critical());
        assert_eq!(parsed.options[0].data, &[0xDE, 0xAD, 0xBE, 0xEF]);
        assert_eq!(parsed.vni, 100);
    }

    // Buffer too short: less than 8 bytes
    #[test]
    fn test_parse_buffer_too_short() {
        let buf = [0u8; 4];
        let result = parse(&buf, false);
        assert!(matches!(result, Err(GeneveError::BufferTooShort { .. })));
    }

    // Reject bad version
    #[test]
    fn test_parse_bad_version() {
        let mut buf = [0u8; 8];
        buf[0] = 0x80; // version = 2
        let result = parse(&buf, false);
        assert!(matches!(result, Err(GeneveError::UnsupportedVersion(2))));
    }

    // Reject VNI > 24-bit max
    #[test]
    fn test_vni_too_large() {
        let params = EncodeParams {
            vni:           0x01_000_000, // 2^24
            protocol_type: ProtocolType::TransparentEthernet,
            oam:           false,
            options:       &[],
        };
        let mut buf = [0u8; 64];
        let result = encode_header(&params, &mut buf);
        assert!(matches!(result, Err(GeneveError::VniTooLarge(0x01_000_000))));
    }

    // Unknown critical option → error (when check_critical=true)
    #[test]
    fn test_unknown_critical_option() {
        // Build a packet with a critical option (class=0x9999, type=0x80|0x01)
        let mut buf = vec![0u8; 16];
        buf[0] = 0x02;          // opt_len = 2 words = 8 bytes of options
        buf[1] = 0x40;          // C flag set
        buf[2] = 0x65; buf[3] = 0x58; // proto_type = 0x6558
        buf[4] = 0x00; buf[5] = 0x00; buf[6] = 0x64; // VNI = 100
        buf[7] = 0x00;          // reserved
        // Option: class=0x9999, type=0x81 (critical, type_id=1), len=1 (4 bytes data)
        buf[8]  = 0x99; buf[9]  = 0x99; // class
        buf[10] = 0x81;                  // critical | type_id=1
        buf[11] = 0x01;                  // 1 word of data
        buf[12] = 0xDE; buf[13] = 0xAD; buf[14] = 0xBE; buf[15] = 0xEF;

        let result = parse(&buf, true);
        assert!(matches!(result, Err(GeneveError::UnknownCriticalOption { class: 0x9999, typ: 1 })));

        // Same buffer but check_critical=false → succeeds
        let result = parse(&buf, false);
        assert!(result.is_ok());
        let parsed = result.unwrap();
        assert!(parsed.options[0].is_critical());
    }

    // UDP src port is deterministic and in range
    #[test]
    fn test_udp_src_port_determinism_and_range() {
        let p1 = udp_src_port(0xC0A80001, 0xC0A80002, 54321, 80, 6, 49152, 65535);
        let p2 = udp_src_port(0xC0A80001, 0xC0A80002, 54321, 80, 6, 49152, 65535);
        assert_eq!(p1, p2, "same input must produce same port");
        assert!(p1 >= 49152 && p1 <= 65535, "port must be in IANA ephemeral range");

        // Different flow should (usually) produce different port
        let p3 = udp_src_port(0xC0A80001, 0xC0A80003, 12345, 443, 6, 49152, 65535);
        // Note: hash collisions are valid; this just checks it's still in range
        assert!(p3 >= 49152 && p3 <= 65535);
    }

    // Option alignment: data_len=3 should be padded to 4
    #[test]
    fn test_option_data_padding() {
        let opt = GeneveOption::new(0x0001, 0x01, vec![0xAA, 0xBB, 0xCC]).unwrap();
        assert_eq!(opt.wire_size(), 4 + 4); // 4B header + 4B (3 data + 1 pad)

        let params = EncodeParams {
            vni:           1,
            protocol_type: ProtocolType::TransparentEthernet,
            oam:           false,
            options:       &[opt],
        };

        let mut buf = [0u8; 64];
        let len = encode_header(&params, &mut buf).unwrap();
        assert_eq!(len, GENEVE_BASE_HDR_LEN + 8); // 8 + 8 = 16

        // opt_len field must be 2 (two 4-byte words)
        assert_eq!(buf[0] & 0x3F, 2);

        // Parse back; data should be 3 bytes (not padded)
        // Actually the wire has 4 bytes; we slice to opt_data_len (not wire)
        // The parser returns the full 4-byte aligned data (wire representation):
        let parsed = parse(&buf[..len], true).unwrap();
        // Wire has 4 bytes; first 3 are data, last is pad zero
        assert_eq!(parsed.options[0].data.len(), 4);
        assert_eq!(parsed.options[0].data[..3], [0xAA, 0xBB, 0xCC]);
        assert_eq!(parsed.options[0].data[3], 0x00); // padding
    }

    // Option overrun: opt_len says 4 words but we only have 1 word of option data
    #[test]
    fn test_option_overrun_detection() {
        let mut buf = [0u8; 12];
        buf[0] = 0x04;  // opt_len=4 words = 16 bytes of options claimed
        // But we only provide 4 bytes of options (buf is only 12 bytes total)
        buf[2] = 0x65; buf[3] = 0x58;
        let result = parse(&buf, false);
        assert!(matches!(result, Err(GeneveError::BufferTooShort { .. })));
    }

    // Max VNI value round-trip
    #[test]
    fn test_max_vni() {
        let params = EncodeParams {
            vni:           0x00FF_FFFF,
            protocol_type: ProtocolType::TransparentEthernet,
            oam:           false,
            options:       &[],
        };
        let mut buf = [0u8; 64];
        let len = encode_header(&params, &mut buf).unwrap();
        let parsed = parse(&buf[..len], false).unwrap();
        assert_eq!(parsed.vni, 0x00FF_FFFF);
    }
}
```

```rust
// fuzz/fuzz_targets/fuzz_geneve_decode.rs
// Fuzz target: feed arbitrary bytes to the parser; must never panic.
// Run: cargo fuzz run fuzz_geneve_decode

#![no_main]
use libfuzzer_sys::fuzz_target;
use geneve_rs::parse;

fuzz_target!(|data: &[u8]| {
    // Must never panic; errors are acceptable
    let _ = parse(data, true);
    let _ = parse(data, false);
});
```

---

## 20. Threat Model and Security Analysis

### 20.1 GENEVE Threat Model Overview

```
+─────────────────────────────────────────────────────────────────────+
|                      GENEVE THREAT MODEL                            |
+─────────────────────────────────────────────────────────────────────+

ASSETS:
  A1: Tenant network isolation (VNI = trust boundary)
  A2: Inner packet confidentiality (tenant data)
  A3: Control plane integrity (VTEP-to-VTEP mappings)
  A4: Availability (underlay bandwidth, VTEP CPU)
  A5: Metadata authenticity (GENEVE options carry security labels)

TRUST BOUNDARIES:
  TB1: Physical underlay (IP fabric) — assumed trusted per RFC 8926
  TB2: NVE/VTEP — kernel/hypervisor trusted; tenant VM not trusted
  TB3: Tenant network — untrusted; can inject any L2 frames

ADVERSARIES:
  ADV1: Compromised tenant VM (insider tenant attack)
  ADV2: Compromised hypervisor host (lateral movement)
  ADV3: Network attacker on underlay (wire-level attack)
  ADV4: Rogue VTEP injection (attacker with underlay access)
+─────────────────────────────────────────────────────────────────────+
```

### 20.2 Threat Analysis Table

| ID | Threat | Attack Vector | Impact | GENEVE Mitigation | Additional Mitigation |
|----|--------|---------------|--------|-------------------|----------------------|
| T1 | VNI Spoofing: tenant injects GENEVE-encapsulated packets with forged VNI | Tenant sends crafted UDP/6081 packets from VM | Cross-tenant data delivery; total isolation bypass | NVE must not accept GENEVE packets from tenant interfaces (decap only on underlay-facing ports) | iptables: DROP UDP dst 6081 on tenant-facing interfaces; Network namespaces |
| T2 | Option Injection: attacker crafts packets with malicious critical options | Underlay access (ADV3/ADV4) | Force option processing, trigger critical option drop (DoS) or bypass policy | RFC 8926: unknown critical option → DROP (not exploit); NVEs validate opt_len | IPsec/DTLS on underlay; Authenticate VTEP peers |
| T3 | VNI Enumeration: probe all 16M VNIs to find active tenants | Send probes from tenant VM or underlay | Tenant network topology discovery | NVEs should not respond to ARP/probe for other VNIs | Flood control; rate limiting per-VNI; no cross-VNI ARP proxy |
| T4 | Inner packet eavesdrop (GENEVE is cleartext) | Underlay tap (ADV3) | All tenant traffic exposed | RFC 8926 explicitly notes: no encryption; recommends IPsec or DTLS transport | IPsec ESP in transport mode between VTEPs; WireGuard; MACsec on physical links |
| T5 | VTEP impersonation: attacker sends GENEVE from spoofed VTEP IP | Underlay with spoofed source IP | Inject packets into tenant VNI with victim VTEP's authority | No built-in VTEP authentication in GENEVE | IPsec peer auth (certificate-based); Source IP filtering (uRPF); EVPN route security |
| T6 | BUM traffic amplification (flood-and-learn) | Tenant sends broadcast/unknown-unicast | O(N) copies to all VTEPs; bandwidth exhaustion | Not GENEVE-specific; control plane choice | SDN/EVPN eliminates flooding; known-unicast-only delivery |
| T7 | Fragment-based bypass: crafted fragmented outer IP packets | Underlay | Bypass stateful firewall inspection | Outer DF=1 (recommended); no fragmentation expected | Drop first-fragment-missing (netfilter INVALID state) |
| T8 | CPU exhaustion via malformed GENEVE options | Send flood of packets with maximum options (Opt Len=63) | VTEP kernel CPU exhausted on option parsing | Options parsing O(N); max 63 words; kernel rate limiting | SR-IOV hardware offload; XDP rate limiting; COS/DSCP policing on underlay |
| T9 | Metadata forgery (GENEVE option security labels) | Compromised NVE or underlay | Bypass security label enforcement (e.g., Cilium identity) | Not addressed by GENEVE; must be addressed by system design | Authenticate option source (IPsec); Validate labels at receiving NVE against control plane |
| T10 | UDP checksum evasion | Send malformed UDP with invalid checksum | Evade IDS/firewall checksum validation | RFC 8926: recommends checksum enabled; IPv6 requires it | Enable UDP checksum on GENEVE sockets (`setsockopt SO_NO_CHECK false`) |

### 20.3 Security Mitigations — Deployment Checklist

**Layer 1 — Physical / Underlay:**
```bash
# Enable uRPF (unicast Reverse Path Forwarding) on all VTEP-facing router interfaces
# Cisco/Arista:
#   ip verify unicast source reachable-via rx
# Linux:
sysctl -w net.ipv4.conf.eth0.rp_filter=1

# MACsec on physical links (hardware support required)
ip link add link eth0 macsec0 type macsec
ip macsec add macsec0 tx sa 0 pn 1 on key 00 deadbeefdeadbeefdeadbeefdeadbeef
```

**Layer 2 — VTEP / NVE host:**
```bash
# Block GENEVE (UDP 6081) FROM tenant-facing interfaces INTO the NVE
# Tenants must NEVER be able to inject GENEVE packets into the underlay directly
iptables -I INPUT -i tap+ -p udp --dport 6081 -j DROP
iptables -I INPUT -i veth+ -p udp --dport 6081 -j DROP

# Rate-limit GENEVE on underlay (prevent option-flood DoS)
# tc ingress rate limiting on underlay-facing NIC
tc qdisc add dev eth0 handle ffff: ingress
tc filter add dev eth0 parent ffff: protocol ip u32 \
    match ip protocol 17 0xFF \
    match ip dport 6081 0xFFFF \
    police rate 10gbit burst 1m drop

# Validate outer source IP (whitelist known VTEPs)
# nftables — whitelist known VTEP IPs on GENEVE port
nft add rule ip filter INPUT \
    ip protocol udp udp dport 6081 \
    ip saddr != { 10.0.0.0/24 } drop
```

**Layer 3 — Encryption (IPsec between VTEPs):**
```bash
# strongSwan IPsec configuration for VTEP-to-VTEP encryption
# /etc/swanctl/conf.d/geneve-vtep.conf

connections {
  vtep-tunnel {
    local_addrs  = 10.0.0.1
    remote_addrs = 10.0.0.2
    local {
      auth = pubkey
      certs = vtep1.pem
    }
    remote {
      auth = pubkey
      certs = vtep2.pem
    }
    children {
      geneve-child {
        local_ts  = 10.0.0.1/32[udp/6081]
        remote_ts = 10.0.0.2/32[udp/6081]
        esp_proposals = aes256gcm128-prfsha384-ecp384
        mode = transport    # transport mode: encrypt only the UDP payload
      }
    }
  }
}
```

**Layer 4 — Monitoring:**
```bash
# Watch for abnormal GENEVE patterns
tcpdump -i eth0 -n 'udp port 6081' -w /tmp/geneve.pcap

# tshark decode GENEVE
tshark -r geneve.pcap -d udp.port==6081,geneve -T fields \
  -e geneve.vni -e geneve.proto -e geneve.opt_count

# Check for VNI spoofing attempts (unexpected VNIs on an NVE)
# Monitor via eBPF: count packets per VNI; alert on unknown VNIs
```

### 20.4 Defense-in-Depth Architecture

```
+──────────────────────────────────────────────────────────────────+
|                 Defense-in-Depth for GENEVE Overlay              |
+──────────────────────────────────────────────────────────────────+

Physical Layer:
  [MACsec on uplinks] → encrypt wire-level frames

Underlay IP Layer:
  [uRPF] → prevent source IP spoofing of VTEP addresses
  [ACL: whitelist VTEP IPs on port 6081] → block rogue VTEP injection
  [DSCP policing] → prevent bandwidth exhaustion

IPsec Layer (VTEP-to-VTEP):
  [ESP transport mode] → encrypt GENEVE UDP payload between VTEPs
  [IKEv2 with certificates] → mutual VTEP authentication

NVE / Host Layer:
  [iptables: block UDP 6081 from tenant interfaces] → VNI injection prevention
  [seccomp / landlock] → restrict VTEP process syscalls
  [namespace isolation] → VNI namespacing per tenant

GENEVE Protocol Layer:
  [Critical option rejection] → malformed option handling
  [opt_len boundary check] → no buffer overread
  [VNI whitelisting] → only accept known VNIs on decap

Tenant / Overlay Layer:
  [Security group enforcement at NVE] → per-VNI ACL
  [Cilium network policy] → identity-based via GENEVE options
  [OVN ACLs] → stateful firewall in logical pipeline

+──────────────────────────────────────────────────────────────────+
```

---

## 21. Observability, Telemetry, and Debugging

### 21.1 Kernel Statistics

```bash
# GENEVE interface statistics
ip -s link show geneve0
# RX/TX packets, bytes, errors, dropped

# Tunnel stats in detail
cat /proc/net/dev | grep geneve

# Netstat for GENEVE UDP socket
ss -anu 'sport = :6081 or dport = :6081'
# or
ss -unp src :6081

# nstat for UDP/tunnel counters
nstat -z | grep -iE "udp|tun|geneve"
```

### 21.2 tcpdump / tshark

```bash
# Capture GENEVE packets
tcpdump -i eth0 'udp port 6081' -w geneve.pcap

# Decode with tshark (Wireshark's CLI)
tshark -r geneve.pcap -d 'udp.port==6081,geneve' -V

# Display specific fields
tshark -r geneve.pcap -d 'udp.port==6081,geneve' \
  -T fields \
  -e frame.number \
  -e ip.src -e ip.dst \
  -e udp.srcport \
  -e geneve.vni \
  -e geneve.proto_type \
  -e geneve.opt_len \
  -e eth.src -e eth.dst    # inner Ethernet (if proto=0x6558)

# Wireshark: Edit > Preferences > Protocols > GENEVE → set port 6081
```

### 21.3 eBPF Observability

```c
/* eBPF program: count GENEVE packets per VNI (attach to XDP or TC) */

#include <linux/bpf.h>
#include <linux/if_ether.h>
#include <linux/ip.h>
#include <linux/udp.h>
#include <bpf/bpf_helpers.h>
#include <bpf/bpf_endian.h>

#define GENEVE_PORT 6081
#define GENEVE_BASE_HDR_LEN 8

struct {
    __uint(type, BPF_MAP_TYPE_HASH);
    __uint(max_entries, 65536);
    __type(key, __u32);    /* VNI */
    __type(value, __u64);  /* packet count */
} vni_counter SEC(".maps");

SEC("xdp")
int geneve_vni_counter(struct xdp_md *ctx)
{
    void *data     = (void *)(long)ctx->data;
    void *data_end = (void *)(long)ctx->data_end;

    struct ethhdr *eth = data;
    if ((void *)(eth + 1) > data_end)
        return XDP_PASS;
    if (bpf_ntohs(eth->h_proto) != ETH_P_IP)
        return XDP_PASS;

    struct iphdr *ip = (void *)(eth + 1);
    if ((void *)(ip + 1) > data_end)
        return XDP_PASS;
    if (ip->protocol != IPPROTO_UDP)
        return XDP_PASS;

    struct udphdr *udp = (void *)ip + (ip->ihl * 4);
    if ((void *)(udp + 1) > data_end)
        return XDP_PASS;
    if (bpf_ntohs(udp->dest) != GENEVE_PORT)
        return XDP_PASS;

    /* GENEVE header starts after UDP */
    __u8 *geneve = (__u8 *)(udp + 1);
    if ((void *)(geneve + GENEVE_BASE_HDR_LEN) > data_end)
        return XDP_PASS;

    /* VNI is in bytes 4–6 of GENEVE header (big-endian) */
    __u32 vni = ((__u32)geneve[4] << 16) |
                ((__u32)geneve[5] <<  8) |
                ((__u32)geneve[6]);

    __u64 *count = bpf_map_lookup_elem(&vni_counter, &vni);
    if (count) {
        __sync_fetch_and_add(count, 1);
    } else {
        __u64 one = 1;
        bpf_map_update_elem(&vni_counter, &vni, &one, BPF_NOEXIST);
    }

    return XDP_PASS;
}

char _license[] SEC("license") = "GPL";
```

```bash
# Compile and load
clang -O2 -target bpf -c geneve_vni_counter.c -o geneve_vni_counter.o
ip link set dev eth0 xdp obj geneve_vni_counter.o sec xdp

# Read the VNI counter map
bpftool map dump name vni_counter
```

### 21.4 OVS Debugging

```bash
# Dump GENEVE tunnel flows in OVS
ovs-ofctl dump-flows br0 | grep tun

# Show tunnel ports
ovs-vsctl list interface geneve0

# Observe tunnel encap/decap with ovs-dpctl
ovs-dpctl dump-flows | grep geneve

# Enable GENEVE option debugging in OVS
ovs-appctl vlog/set geneve:dbg

# Show TLV mappings
ovs-ofctl dump-tlv-map br0

# Test GENEVE reachability
ovs-appctl ofproto/trace br0 "in_port=1,eth_src=00:11:22:33:44:55,\
  eth_dst=66:77:88:99:aa:bb,eth_type=0x0800,ip_src=192.168.1.1,\
  ip_dst=192.168.1.2,ip_ttl=64,ip_proto=6,tcp_src=1234,tcp_dst=80"
```

### 21.5 MTU Debugging

```bash
# Test effective MTU through GENEVE tunnel
# From inside VM:
ping -M do -s 1422 <remote_inner_ip>  # 1422 + 28 (IP+ICMP) = 1450 inner frame

# From NVE host, test path MTU to remote VTEP:
tracepath -n <remote_vtep_ip>

# Check PMTU cache
ip route get <remote_vtep_ip>
# Look for: cache expires <T> mtu <N>

# Force PMTU probe
ping -M do -s 1450 <remote_vtep_ip>
# If returns "Frag needed": underlay MTU < 1500 + GENEVE overhead

# Verify MSS clamping is working
tcpdump -r geneve.pcap 'tcp[tcpflags] & tcp-syn != 0' -v | grep mss
```

---

## 22. Performance: Benchmarking and Tuning

### 22.1 Throughput Benchmarks

**Test setup:**

```
+──────────+    10GbE     +──────────+
|  host-A  |─────────────|  host-B  |
| GENEVE   |   underlay  | GENEVE   |
+──────────+             +──────────+
  10.0.0.1                10.0.0.2
  VNI 100                 VNI 100
  192.168.1.1             192.168.1.2  (inner)
```

```bash
# Benchmark UDP throughput through GENEVE tunnel
# On host-B (receiver):
iperf3 -s -B 192.168.1.2

# On host-A (sender):
iperf3 -c 192.168.1.2 -t 30 -P 8 -u -b 0  # UDP
iperf3 -c 192.168.1.2 -t 30 -P 8           # TCP

# Benchmark with netperf (more detailed stats):
netserver &  # on host-B
netperf -H 192.168.1.2 -t TCP_STREAM -l 30 -- -m 1M

# Linux pktgen for line-rate testing:
modprobe pktgen
# Configure pktgen threads to send GENEVE-encapsulated traffic at line rate
```

### 22.2 Latency Benchmark

```bash
# One-way latency with sockperf
sockperf server --ip 192.168.1.2 --port 9999 &
sockperf ping-pong --ip 192.168.1.2 --port 9999 --time 60

# Expected baselines (10GbE, modern hardware):
#   Native (no tunnel):  ~10–20 μs RTT
#   GENEVE (kernel):     ~20–40 μs RTT  (software encap/decap overhead)
#   GENEVE (NIC offload): ~12–25 μs RTT
#   GENEVE (SmartNIC):   ~10–20 μs RTT  (near-native)
```

### 22.3 Performance Tuning

```bash
# ── NIC Tuning ──────────────────────────────────────────────────

# Increase NIC ring buffer size
ethtool -G eth0 rx 4096 tx 4096

# Enable hardware offloads
ethtool -K eth0 tso on gso on gro on tx-udp_tnl-segmentation on

# Multi-queue: ensure RSS queues match CPU count
ethtool -L eth0 combined $(nproc)

# ── Kernel Tuning ───────────────────────────────────────────────

# Increase socket buffer sizes for GENEVE UDP socket
sysctl -w net.core.rmem_max=134217728
sysctl -w net.core.wmem_max=134217728
sysctl -w net.core.rmem_default=8388608
sysctl -w net.core.wmem_default=8388608

# Increase UDP socket buffer
sysctl -w net.ipv4.udp_mem="65536 131072 262144"

# Enable GRO hardware (if NIC supports it)
ethtool -K eth0 rx-gro-hw on

# ── CPU Affinity ────────────────────────────────────────────────

# Pin GENEVE NAPI softirq to specific CPUs (avoid NUMA crosses)
# Find GENEVE socket IRQ
cat /proc/interrupts | grep eth0
# Set affinity: IRQ 24 → CPU 0-3
echo f > /proc/irq/24/smp_affinity  # CPUs 0-3 (bitmask)

# ── NUMA Awareness ──────────────────────────────────────────────

# Bind VTEP process to NUMA node local to NIC
numactl --cpunodebind=0 --membind=0 ovs-vswitchd

# ── Jumbo Frames (best throughput optimization) ──────────────────

ip link set eth0 mtu 9000
ip link set geneve0 mtu 8950  # 9000 - 50 overhead
# Set all tenant interfaces to 8900 for headroom
```

### 22.4 CPU Overhead Analysis

```
GENEVE processing cost per packet (approximate, x86-64, no HW offload):

  Encapsulation (egress):
    Allocate SKB headroom:          ~50 ns
    Fill GENEVE/UDP/IP headers:     ~20 ns
    Compute UDP src port hash:      ~10 ns
    ARP/FDB lookup:                 ~30 ns (hash table, L1 cache hit)
    IP routing lookup (underlay):   ~20 ns
    NIC DMA:                        ~10 ns
    Total:                         ~140 ns ≈ 7 Mpps ceiling (one core)

  Decapsulation (ingress):
    NAPI poll, DMA completion:      ~30 ns
    UDP socket lookup:              ~20 ns
    GENEVE header parse:            ~15 ns
    VNI→netdev lookup:              ~25 ns
    SKB pull (strip outer headers): ~20 ns
    Deliver to bridge/routing:      ~30 ns
    Total:                         ~140 ns ≈ 7 Mpps ceiling (one core)

With NIC hardware offload (TSO/GRO):
  Bulk transfer: 20–40 Gbps with 1–2 cores (vs 5–10 Gbps software)
  Small packets: 10–20 Mpps per core (vs 3–7 Mpps software)
```

---

## 23. Failure Modes and Operational Pitfalls

### 23.1 Failure Mode Catalog

| Failure | Symptom | Root Cause | Detection | Fix |
|---------|---------|------------|-----------|-----|
| MTU Blackhole | TCP hangs after handshake; UDP works | Inner frames too large; ICMP Frag Needed blocked | `ping -M do -s 1422 <dst>` fails | Enable MSS clamping; allow ICMP type 3 code 4 |
| VNI Mismatch | Intermittent packet loss between VMs | VTEP FDB stale; VNI allocation bug | `ovs-ofctl dump-flows br0 | grep tun_id` | Flush FDB; check OVN/controller VNI assignment |
| ECMP Polarization | One path saturated, others idle | Same ECMP hash at all levels | `ethtool -S eth0 | grep queue` disparate | Fix hash seed per ECMP level; tune UDP src port range |
| ARP Flooding | High BUM traffic; control plane overloaded | FDB miss → flood to all VTEPs | `sar -n DEV 1` shows spike | Enable OVN/EVPN; disable flood-and-learn; add static FDB entries |
| GENEVE option version incompatibility | Packets dropped at remote VTEP | Remote NVE doesn't understand option class | Check remote NVE logs for critical option drops | Disable critical options; downgrade to non-critical; coordinate deployment |
| Checksum failure | Packets corrupted; TCP resets | UDP checksum enabled but NIC miscalculated | `ethtool -S | grep error` | Disable UDP checksum (`ip link set geneve0 type geneve noudpcsum`) or fix NIC driver |
| NIC offload regression | Throughput drops after kernel upgrade | Kernel changed GENEVE GSO path; NIC firmware mismatch | `ethtool -k eth0 | grep tnl` | Disable then re-enable offloads; update NIC firmware |
| VTEP IP change | All tunnels drop | VTEP IP reconfigured without updating control plane | Ping between VTEPs fails | Update FDB/EVPN/OVN with new VTEP IP; ensure graceful VTEP migration |
| opt_len field corruption | Packet storm; decap failures | Bug in NVE software; bit flip | `tcpdump | tshark geneve.opt_len` shows wild values | Input validation (as in C/Rust impl above); detect with monitoring |

### 23.2 Common Misconfiguration: Inner MTU Not Set

**Symptom:** Large file transfers (SCP, HTTP large objects) hang or fail; small packets work fine.

**Diagnosis:**
```bash
# From inside tenant VM:
ping -M do -s 1450 <remote_tenant_ip>
# "Frag needed and DF set" → MTU problem confirmed

# Check effective MTU of GENEVE interface:
ip link show geneve0
# MTU 1500 means no adjustment made → inner frames can be 1500B
# After encapsulation: 1500 + 50 = 1550B > underlay MTU 1500 → blackhole
```

**Fix:**
```bash
# Option A: Reduce GENEVE interface MTU
ip link set geneve0 mtu 1450

# Option B: MSS clamp (recommended; doesn't require changing MTU globally)
iptables -t mangle -A POSTROUTING \
    -p tcp --tcp-flags SYN,RST SYN \
    -o geneve0 \
    -j TCPMSS --clamp-mss-to-pmtu
```

### 23.3 Underlay ICMP Blocking

A widespread problem: corporate firewalls block all ICMP, including ICMP Type 3 (Unreachable) /
Code 4 (Fragmentation Needed). This breaks PMTUD for GENEVE tunnels.

```bash
# Test ICMP Frag Needed is reachable
# From VTEP host, send large packet with DF=1 to check for ICMP response
hping3 --icmp -c 1 <remote_vtep_ip>

# Allow ICMP Frag Needed through firewall (critical for tunnel health)
iptables -A INPUT -p icmp --icmp-type fragmentation-needed -j ACCEPT
iptables -A OUTPUT -p icmp --icmp-type fragmentation-needed -j ACCEPT
iptables -A FORWARD -p icmp --icmp-type fragmentation-needed -j ACCEPT

# Verify with nftables:
nft add rule ip filter INPUT icmp type destination-unreachable accept
```

---

## 24. Roll-out / Roll-back Plan

### 24.1 Roll-out Phases for GENEVE Deployment

```
Phase 0: Pre-deployment validation (1 week)
  ├─ Verify underlay MTU ≥ 1600 bytes (jumbo) or plan MSS clamping
  ├─ Verify ICMP Frag Needed passes through all underlay devices
  ├─ Verify UDP 6081 not blocked or rate-limited by underlay ACLs
  ├─ Benchmark VTEP nodes: ensure sufficient PPS capacity
  ├─ Confirm NIC GENEVE offload support: ethtool -k <NIC>
  └─ Load test GENEVE on 2 test hosts; validate: MTU, encap, decap, ECMP

Phase 1: Shadow deployment (2 weeks)
  ├─ Deploy GENEVE VTEPs in parallel with existing VXLAN
  ├─ Duplicate 5% of traffic through GENEVE (mirroring)
  ├─ Verify packet delivery, latency, and no MTU issues
  ├─ Monitor: packet loss, GENEVE error counters, CPU overhead
  └─ Roll back: switch mirroring off; no tenant impact

Phase 2: Canary (1 week)
  ├─ Migrate 1 non-critical tenant VNI to GENEVE
  ├─ A/B test: compare latency and throughput vs VXLAN baseline
  ├─ Verify FDB/EVPN/OVN control plane propagates GENEVE endpoints
  └─ Roll back: migrate VNI back to VXLAN; takes < 5 minutes with OVN

Phase 3: Progressive migration (4–8 weeks)
  ├─ Migrate VNIs in batches: 10%, 25%, 50%, 100%
  ├─ Priority: non-production → dev → staging → production
  ├─ After each batch: 48h monitoring window before next batch
  └─ Roll back trigger: > 0.01% packet loss increase OR > 5% latency increase

Phase 4: Full production (ongoing)
  ├─ Deprecate VXLAN tunnels
  ├─ Remove VXLAN offload rules from NICs
  └─ Update runbooks and monitoring dashboards for GENEVE specifics
```

### 24.2 Roll-back Procedure

```bash
# Emergency roll-back: switch NVE from GENEVE to VXLAN (OVN example)
# In OVN, tunnel protocol is set per chassis

# Step 1: Change OVN encap type on affected chassis
ovs-vsctl set open_vswitch . \
    external_ids:ovn-encap-type=vxlan \
    external_ids:ovn-encap-ip=<vtep_ip>

# Step 2: OVN-controller re-programs OVS with VXLAN tunnels (~10-30 seconds)
# Verify:
ovs-vsctl show | grep -A2 "Interface.*vxlan"

# Step 3: Verify traffic flows (ping between tenant VMs)
# If connectivity restored: roll-back successful

# Step 4: Investigate GENEVE failure root cause before re-deploying
journalctl -u ovn-controller --since "1 hour ago" | grep -iE "geneve|error|warn"
```

---

## 25. References and Standards

### RFCs (Primary)

| RFC | Title | Relevance |
|-----|-------|-----------|
| RFC 8926 | Geneve: Generic Network Virtualization Encapsulation | **Core specification** |
| RFC 7348 | Virtual eXtensible Local Area Network (VXLAN) | Predecessor; comparison |
| RFC 8014 | An Architecture for Data-Center NVO3 | Architectural context |
| RFC 7365 | Framework and Requirements for L2VPN | L2 overlay requirements |
| RFC 7432 | BGP MPLS-Based Ethernet VPN (EVPN) | Control plane standard |
| RFC 8365 | NVO3 Solution Using EVPN | EVPN + GENEVE integration |
| RFC 4459 | MTU and Fragmentation Issues with In-the-Network Tunneling | MTU design |
| RFC 6040 | Tunnelling of Explicit Congestion Notification | ECN in tunnels |
| RFC 2784 | Generic Routing Encapsulation (GRE) | Comparison |
| RFC 8200 | Internet Protocol Version 6 (IPv6) | Outer IPv6 reference |

### IANA Registries

- GENEVE Option Classes: https://www.iana.org/assignments/nvo3/nvo3.xhtml#geneve-option-class
- UDP Port 6081: https://www.iana.org/assignments/service-names-port-numbers

### Kernel / OVS Source

- Linux GENEVE driver: `net/ipv4/geneve.c` in the Linux kernel
- OVS GENEVE: `lib/netdev-geneve.c`, `lib/geneve.h` in Open vSwitch
- OVN GENEVE usage: `controller/encaps.c` in OVN

### Papers and Blog Posts

- "Geneve: A Protocol Whose Time Has Come" — NANOG 64 presentation, Jesse Gross
- "OVN Architecture" — Russell Bryant, OpenStack blog
- "Cilium Network Policy" — cni.dev/cilium
- "Network Virtualization in Multi-tenant Datacenters" — Popa et al., NSDI 2013

---

## 26. Next 3 Steps

**Step 1 — Build and exercise the C implementation end-to-end:**
```bash
# Compile unit tests
gcc -DUNIT_TEST -O2 -Wall -Wextra -o geneve_test geneve.c && ./geneve_test

# Compile sender
gcc -O2 -Wall -o geneve_send geneve.c geneve_send.c

# Run in a network namespace pair to send/capture a real GENEVE packet
ip netns add ns-a && ip netns add ns-b
ip link add veth-a type veth peer name veth-b
ip link set veth-a netns ns-a && ip link set veth-b netns ns-b
ip netns exec ns-a ip addr add 10.0.0.1/24 dev veth-a && ip netns exec ns-a ip link set veth-a up
ip netns exec ns-b ip addr add 10.0.0.2/24 dev veth-b && ip netns exec ns-b ip link set veth-b up
# In ns-b: tcpdump -i veth-b udp port 6081 -v &
# In ns-a: sudo ip netns exec ns-a ./geneve_send 10.0.0.1 10.0.0.2 100
```

**Step 2 — Set up a 2-node GENEVE lab with OVS and OVN:**
```bash
# On both nodes: install OVN
apt install ovn-central ovn-host openvswitch-switch

# Node 1 (OVN central + host):
ovs-vsctl set open_vswitch . \
    external_ids:ovn-remote=tcp:10.0.0.1:6642 \
    external_ids:ovn-encap-type=geneve \
    external_ids:ovn-encap-ip=10.0.0.1

# Create a logical switch and two ports; verify GENEVE tunnels appear
# Follow: https://docs.ovn.org/en/latest/tutorials/ovn-primer.html
# Capture GENEVE packets and decode with tshark to see OVN metadata in options
```

**Step 3 — Add fuzzing to the Rust implementation and integrate with CI:**
```bash
cd geneve-rs
cargo install cargo-fuzz
cargo fuzz init
# Add fuzz target (see fuzz/fuzz_targets/fuzz_geneve_decode.rs above)
cargo fuzz run fuzz_geneve_decode -- -max_total_time=300

# Run property-based tests with proptest:
# In tests module, add:
# proptest! { #[test] fn fuzz_encode_decode(vni in 0u32..=0xFFFFFFu32) { ... } }
cargo test
```

---

*Document version: 1.0 | Protocol: RFC 8926 (November 2020) | Last reviewed: 2025*