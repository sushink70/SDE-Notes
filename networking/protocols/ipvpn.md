# IP VPN — Complete In-Depth Comprehensive Guide
> *"Understand the protocol at the byte level — then you own the network."*

---

## TABLE OF CONTENTS

```
PART I   — FOUNDATIONS & MENTAL MODEL
PART II  — NETWORK PREREQUISITES (IP, BGP, MPLS)
PART III — MPLS L3VPN (RFC 4364) — The Industry Standard IPVPN
PART IV  — IPSec VPN — Security Layer Deep Dive
PART V   — GRE TUNNELING
PART VI  — OTHER VPN TYPES (L2VPN, SSL, PPTP, L2TP)
PART VII — PACKET WALKTHROUGHS (End-to-End)
PART VIII— C IMPLEMENTATION
PART IX  — RUST IMPLEMENTATION
PART X   — COMPARISON, ATTACKS, HARDENING
```

---

# PART I — FOUNDATIONS & MENTAL MODEL

---

## 1. What Is a VPN?

**VPN = Virtual Private Network**

A VPN creates a **logically private communication channel** over a **shared public or untrusted network** (like the Internet or a service provider's backbone).

The word "virtual" is critical: the network does **not** physically exist as a separate wire. It is *emulated* using software, protocols, and cryptography layered on top of existing infrastructure.

### Mental Model

Think of the real world:
- A **highway** is like the Internet — shared by everyone.
- A **armored car with locked doors** driving on that highway is like a VPN — it uses the public road but nobody outside can see or touch what's inside.

```
WITHOUT VPN:

  Site A ──────────────────────────────── Site B
           [PLAIN TEXT VISIBLE TO ALL]


WITH VPN:

  Site A ═══════════════════════════════ Site B
           [ENCRYPTED TUNNEL — INVISIBLE]
           |||||||||||||||||||||||||||||||
           (Internet/Provider still carries
            the packets but cannot read them)
```

### What Problems Does VPN Solve?

| Problem | VPN Solution |
|---|---|
| Connecting remote offices over Internet | Site-to-site tunnel |
| Remote workers need access to corp network | Client-to-site tunnel |
| Privacy from ISP/eavesdroppers | Traffic encryption |
| Multiple customers sharing one SP backbone | Traffic isolation (MPLS VPN) |
| Geo-restrictions | IP masking via tunnel endpoint |

---

## 2. VPN Terminology Glossary

Before anything else, internalize these terms. Every concept below will be used repeatedly.

### Networking Terms

| Term | Full Form | What It Means |
|---|---|---|
| **CE** | Customer Edge | The router at the customer's premises that connects to the SP |
| **PE** | Provider Edge | The router at the SP's edge that connects to CE routers |
| **P** | Provider (core) | Core routers inside SP backbone — do not touch customer routes |
| **SP** | Service Provider | Telecom/ISP who provides the VPN service |
| **CPE** | Customer Premises Equipment | Equipment at customer site (often same as CE) |
| **AS** | Autonomous System | A network under a single administrative control with an AS number |
| **VRF** | Virtual Routing & Forwarding | A separate, isolated routing table inside a PE router |
| **RD** | Route Distinguisher | A 64-bit value prepended to IP prefix to make it globally unique |
| **RT** | Route Target | BGP extended community used to control route import/export between VRFs |
| **LSP** | Label Switched Path | A predefined path through MPLS network defined by labels |
| **LDP** | Label Distribution Protocol | Protocol that distributes MPLS labels between routers |
| **FEC** | Forwarding Equivalence Class | A group of packets forwarded the same way through MPLS |
| **LFIB** | Label Forwarding Information Base | Table mapping incoming label → outgoing label/interface |
| **FIB** | Forwarding Information Base | IP routing table optimized for fast forwarding |
| **IKE** | Internet Key Exchange | Protocol for negotiating IPSec security associations |
| **SA** | Security Association | A set of negotiated parameters for one IPSec connection direction |
| **SAD** | Security Association Database | Stores all active SAs |
| **SPD** | Security Policy Database | Defines what traffic gets encrypted/bypassed |
| **SPI** | Security Parameter Index | 32-bit identifier for an SA |
| **ESP** | Encapsulating Security Payload | IPSec protocol that provides encryption + integrity |
| **AH** | Authentication Header | IPSec protocol that provides integrity only (no encryption) |
| **GRE** | Generic Routing Encapsulation | Tunneling protocol that wraps any protocol inside IP |
| **TTL** | Time To Live | Hop count field in IP header — decremented at each router |
| **MTU** | Maximum Transmission Unit | Largest packet size a link can carry (bytes) |
| **MSS** | Maximum Segment Size | TCP-level limit on data in a segment |
| **PMTUD** | Path MTU Discovery | Mechanism to discover smallest MTU on a path |
| **ECN** | Explicit Congestion Notification | Network-layer congestion signaling |
| **QoS** | Quality of Service | Mechanisms to prioritize certain traffic |
| **MP-BGP** | Multi-Protocol BGP | BGP extension to carry non-IPv4 address families (like VPNv4) |
| **VPNv4** | VPN IPv4 | 96-bit address = 32-bit RD + 32-bit IPv4, used in BGP VPN |
| **EVPN** | Ethernet VPN | Modern L2/L3 VPN using BGP for MAC/IP distribution |
| **VPLS** | Virtual Private LAN Service | L2 VPN emulating an Ethernet LAN over MPLS |
| **PKI** | Public Key Infrastructure | Framework for certificate-based authentication |
| **DH** | Diffie-Hellman | Algorithm for key exchange over insecure channel |
| **PFS** | Perfect Forward Secrecy | Each session uses new keys — compromise of one doesn't affect others |

### Protocol Stack Terms

| Term | Meaning |
|---|---|
| **Encapsulation** | Wrapping a packet inside another packet (adding headers) |
| **Decapsulation** | Removing outer header(s) to recover original packet |
| **Tunnel** | A logical path created by encapsulation between two endpoints |
| **Overlay** | A virtual network built on top of physical network |
| **Underlay** | The physical network that carries overlay traffic |
| **Control Plane** | The part of a router that builds routing tables (BGP, OSPF runs here) |
| **Data Plane** | The part that actually forwards packets using those tables |
| **Forwarding** | Moving a packet from input interface to output interface |
| **Next-hop** | The immediately next router a packet should be sent to |
| **Prefix** | An IP network, e.g., 10.1.0.0/24 |
| **Label** | A 20-bit number in MPLS used for fast forwarding decisions |
| **Label Stack** | Multiple MPLS labels stacked — innermost is "bottom of stack" |
| **Push** | Adding a label to a packet |
| **Pop** | Removing a label from a packet |
| **Swap** | Replacing one label with another |
| **PHP** | Penultimate Hop Popping — second-to-last router removes outer label |

---

## 3. VPN Classification

VPNs are classified along multiple dimensions:

### By Layer of Operation

```
OSI Layer 7  ──  Application VPN (SSL/TLS VPN — browser-based)
OSI Layer 4  ──  Transport VPN  (SSL VPN using TLS over TCP/UDP)
OSI Layer 3  ──  Network VPN    (IPSec, MPLS L3VPN, GRE)
OSI Layer 2  ──  Data Link VPN  (VPLS, EVPN, L2TP, PPTP)
OSI Layer 1  ──  Physical VPN   (Dark fiber, DWDM — rarely called VPN)
```

### By Topology

```
SITE-TO-SITE (Hub-and-Spoke)
==============================
        Branch1 ──────┐
                       ├──── HQ (Hub)
        Branch2 ──────┘

All branch traffic goes through HQ first.
Simple to manage, HQ is single point of failure.


SITE-TO-SITE (Full Mesh)
=========================
        Branch1 ────── Branch2
           │    \   /    │
           │     \ /     │
           │      X      │
           │     / \     │
           │    /   \    │
        Branch3 ────── Branch4

Every site connects to every other site directly.
Best performance, most complex.


CLIENT-TO-SITE (Remote Access)
================================
  Laptop ──── Internet ──── VPN Gateway ──── Corp Network
  Phone  ──── Internet ──────────────────────────────────


SITE-TO-CLOUD
==============
  On-Prem ──── IPSec/MPLS ──── Cloud VPC (AWS/Azure)
```

### By Trust Model

| Type | Who Provides VPN | Customer Sees |
|---|---|---|
| **CE-based VPN** | Customer manages tunnel (IPSec) | Full control |
| **PE-based VPN** | SP manages (MPLS L3VPN) | Just routing |
| **Overlay VPN** | Customer uses software (OpenVPN, WireGuard) | Full control |

### By Service Type

| Name | Layer | Protocol | Use Case |
|---|---|---|---|
| MPLS L3VPN | L3 | MP-BGP + MPLS | Enterprise WAN, SP-managed |
| IPSec VPN | L3 | IKE + ESP/AH | Internet tunnels, security |
| GRE | L3 | GRE over IP | Simple tunneling, no encryption |
| GRE over IPSec | L3 | GRE + ESP | Tunneling + encryption |
| L2TPv3 | L2 | L2TP | L2 circuit emulation |
| VPLS | L2 | MPLS + BGP | Ethernet LAN over WAN |
| EVPN | L2/L3 | MP-BGP + MPLS/VXLAN | Modern DC fabric |
| SSL VPN | L4/L7 | TLS | Remote access via browser |
| PPTP | L2 | GRE + PPP + MPPE | Legacy (insecure) |
| WireGuard | L3 | UDP + ChaCha20/Curve25519 | Modern, fast, simple |
| OpenVPN | L3/L2 | TLS over UDP/TCP | Cross-platform, flexible |

---

## 4. The Mental Model: Every VPN Has These Components

Regardless of which VPN type, every VPN has these logical components:

```
┌─────────────────────────────────────────────────────────┐
│                    VPN COMPONENTS                        │
│                                                          │
│  ┌─────────────┐    ┌──────────────┐    ┌────────────┐  │
│  │   CONTROL   │    │     DATA     │    │  MGMT &    │  │
│  │   PLANE     │    │     PLANE    │    │  POLICY    │  │
│  │             │    │              │    │            │  │
│  │ • Route     │    │ • Encap      │    │ • Auth     │  │
│  │   Exchange  │    │ • Encrypt    │    │ • Access   │  │
│  │ • Key Nego  │    │ • Forward    │    │ • Audit    │  │
│  │ • SA Setup  │    │ • Decap      │    │ • QoS      │  │
│  └─────────────┘    └──────────────┘    └────────────┘  │
└─────────────────────────────────────────────────────────┘
```

- **Control Plane**: How routers learn about each other and exchange routing information. In MPLS VPN this is BGP. In IPSec this is IKE.
- **Data Plane**: How actual user packets are forwarded — encapsulation, encryption, label swapping.
- **Management Plane**: Configuration, monitoring, policy enforcement.

---

# PART II — NETWORK PREREQUISITES

---

## 5. IP Routing Fundamentals

### What Is Routing?

Routing is the process of deciding which **interface** to send a packet out of based on the **destination IP address**.

Every router maintains a **routing table** (also called RIB — Routing Information Base):

```
ROUTING TABLE (simplified):
┌──────────────────┬──────────────┬───────────┬──────────┐
│   Destination    │   Next Hop   │ Interface │  Metric  │
├──────────────────┼──────────────┼───────────┼──────────┤
│ 0.0.0.0/0        │ 192.168.1.1  │   eth0    │    10    │  ← default route
│ 10.1.0.0/24      │ directly     │   eth1    │     0    │  ← directly connected
│ 10.2.0.0/24      │ 10.0.0.2     │   eth0    │    20    │  ← learned via OSPF
│ 192.168.100.0/24 │ 172.16.0.1   │   eth2    │   100    │  ← learned via BGP
└──────────────────┴──────────────┴───────────┴──────────┘

Longest Prefix Match (LPM): For packet to 10.1.0.50:
  - 0.0.0.0/0  matches (0 bits)
  - 10.1.0.0/24 matches (24 bits)  ← WINNER (most specific)
```

### What Is BGP?

**BGP = Border Gateway Protocol (RFC 4271)**

BGP is the routing protocol of the Internet — it's how Autonomous Systems (AS) exchange routing information. Every major ISP, cloud provider, and large enterprise runs BGP.

```
BGP KEY CONCEPTS:
=================

AS (Autonomous System):
  A group of IP networks under one administrative control.
  Identified by an AS Number (ASN) — 16-bit (1–65535) or 32-bit.

  Example:
    AS65001 = Your company
    AS65002 = Your ISP

eBGP (External BGP):
  BGP between routers in DIFFERENT AS numbers.
  Used across the Internet.

iBGP (Internal BGP):
  BGP between routers in the SAME AS number.
  Used inside an SP backbone.
  CRITICAL RULE: iBGP routes are NOT re-advertised to other iBGP peers
                 (to prevent loops). Full mesh or route reflectors required.

BGP ATTRIBUTES (used to influence routing decisions):
  ┌───────────────────────────────────────────────────────┐
  │  AS_PATH    — List of ASes a route traversed           │
  │  NEXT_HOP   — IP to forward packets toward             │
  │  LOCAL_PREF — Preference within an AS (higher = better)│
  │  MED        — Suggestion to neighboring AS             │
  │  COMMUNITY  — Tags for grouping/filtering routes       │
  │  EXT_COMM   — Extended communities (64-bit) used in VPN│
  └───────────────────────────────────────────────────────┘

BGP SESSION (TCP port 179):

  Router A ──[TCP:179]── Router B
     │                       │
     │──── OPEN ────────────>│   (announce capabilities, ASN, BGP ID)
     │<─── OPEN ─────────────│
     │──── UPDATE ──────────>│   (send routes)
     │<─── UPDATE ────────────│
     │<──> KEEPALIVE <───────>│   (every 60s by default)
     │<──> NOTIFICATION ─────>│   (on errors, then TCP closes)
```

### BGP UPDATE Message Format (actual wire format)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Withdrawn Routes Length (2 bytes)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Withdrawn Routes (variable)                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       Total Path Attribute Length (2 bytes)                   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Path Attributes (variable)                           |
|  [Flags|Type|Length|Value] for each attribute                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Network Layer Reachability Information (NLRI)        |
|  [length in bits | prefix] per route                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### MP-BGP (Multi-Protocol BGP — RFC 4760)

Standard BGP only carries IPv4 routes. **MP-BGP** extends BGP to carry:
- IPv6 routes
- VPNv4 routes (for MPLS L3VPN)
- L2VPN routes (for EVPN, VPLS)
- VPNv6 routes

MP-BGP introduces two new attributes:

```
MP_REACH_NLRI (Type 14):
  ┌──────────────────────────────────────────────────────────┐
  │ AFI (2B) | SAFI (1B) | Next-Hop Length | Next-Hop | NLRI│
  └──────────────────────────────────────────────────────────┘
  AFI  = Address Family Identifier (1=IPv4, 2=IPv6, 25=L2VPN)
  SAFI = Subsequent AFI (1=unicast, 128=VPN, 70=EVPN)

MP_UNREACH_NLRI (Type 15):
  Used to withdraw routes for non-IPv4 families.
```

---

## 6. MPLS Fundamentals

### What Is MPLS?

**MPLS = Multi-Protocol Label Switching (RFC 3031)**

MPLS is a packet forwarding mechanism where routers make forwarding decisions based on **short fixed-length labels** instead of IP addresses. This makes forwarding **faster** (no longest prefix match — just exact label lookup) and enables **traffic engineering and VPNs**.

### Why MPLS?

Without MPLS:
- Every core router must examine IP destination of every packet.
- Must run complex routing protocols and maintain huge BGP tables.
- Cannot do traffic engineering easily.

With MPLS:
- Core (P) routers only look at labels — O(1) lookup.
- Labels carry semantic meaning (which VPN, which path).
- P routers don't need to know customer routes at all.

### MPLS Label Format

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Label (20 bits)               |Exp|S|    TTL   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^         ^ ^   ^^^^^^^^
       Label value: 0–1048575                   | |   Time to Live
  (values 0–15 reserved)                        | Bottom of Stack
       Label 3 = Implicit NULL (for PHP)        EXP = Traffic Class
       Label 0 = IPv4 Explicit NULL             (QoS marking, 3 bits)
```

- **Label** (20 bits): Forwarding identifier. Values 0–15 are reserved.
- **EXP/TC** (3 bits): Traffic Class for QoS (maps to IP DSCP).
- **S** (1 bit): **Bottom of Stack** flag. Set to 1 on the innermost label.
- **TTL** (8 bits): Same role as IP TTL — prevents loops.

The 32-bit label is placed **between** the Layer 2 header and the IP header:

```
MPLS PACKET STRUCTURE:
┌──────────────┬──────────────┬──────────────┬──────────────────┐
│  L2 Header   │ MPLS Label 1 │ MPLS Label 2 │   IP Packet      │
│  (Ethernet)  │ (outer/top)  │ (inner/bot)  │  (payload)       │
│  14 bytes    │   4 bytes    │   4 bytes    │  variable        │
└──────────────┴──────────────┴──────────────┴──────────────────┘
                                      ^
                          S=1 here (bottom of stack)
```

### MPLS Label Operations

```
PUSH:  Prepend a new label on top of existing label stack.
       Used when entering MPLS domain (at ingress PE).

  Before: [ IP Header | Payload ]
  After:  [ Label:500 | Label:200 | IP Header | Payload ]
            (outer)     (inner, S=1)

SWAP:  Replace current top label with a new label.
       Used at P (core) routers — just swap outer label.

  Before: [ Label:500 | Label:200 | IP Header | Payload ]
  After:  [ Label:750 | Label:200 | IP Header | Payload ]
            (new)        (unchanged)

POP:   Remove the top label.
       Used at egress PE or PHP router.

  Before: [ Label:750 | Label:200 | IP Header | Payload ]
  After:  [ Label:200 | IP Header | Payload ]
            (inner becomes top, S=1)
```

### MPLS Forwarding Plane: LFIB

The **Label Forwarding Information Base (LFIB)** is the table a router uses to forward labeled packets:

```
LFIB TABLE:
┌──────────────┬──────────────────┬────────────┬───────────────┐
│  In-Label    │   Operation      │ Out-Label  │  Out-Interface│
├──────────────┼──────────────────┼────────────┼───────────────┤
│     500      │  SWAP            │    750     │   eth1        │
│     200      │  POP (PHP)       │    ---     │   eth2        │
│     300      │  SWAP            │    410     │   eth0        │
└──────────────┴──────────────────┴────────────┴───────────────┘
```

### Label Distribution Protocol (LDP — RFC 5036)

LDP is how routers learn which labels their neighbors use for each FEC (destination prefix).

```
LDP SESSION ESTABLISHMENT:
===========================

Router A (10.0.0.1)                  Router B (10.0.0.2)
       │                                     │
       │──── LDP Discovery (UDP:646) ────────│
       │     Multicast Hello                 │
       │                                     │
       │──── TCP SYN ────────────────────────│  (TCP:646)
       │<─── TCP SYN-ACK ────────────────────│
       │──── TCP ACK ────────────────────────│
       │                                     │
       │──── LDP Init ───────────────────────│
       │<─── LDP Init ───────────────────────│
       │                                     │
       │──── Label Mapping ─────────────────>│
       │     "For FEC 10.1.0.0/24,           │
       │      use label 500 to reach me"     │
       │                                     │
       │<─── Label Mapping ──────────────────│
       │     "For FEC 10.2.0.0/24,           │
       │      use label 600 to reach me"     │

Now A knows: to reach 10.2.0.0/24, send packet with label 600 toward B.
```

### PHP — Penultimate Hop Popping

**Penultimate** means "second to last."

In MPLS, the **second-to-last router** on a path removes (pops) the outer transport label before forwarding to the last router. This saves the egress PE from doing two lookups.

```
PATH: CE-A ──> PE-A ──> P1 ──> P2 ──> PE-B ──> CE-B
                                  ^
                              PHP happens here
                         P2 pops the transport label
                         so PE-B only sees the VPN label
                         (and IP packet inside)
```

The reserved label value **3 = Implicit NULL** is used by egress PE to signal "do PHP for me."

---

# PART III — MPLS L3VPN (RFC 4364)

---

## 7. Architecture Overview

RFC 4364 (formerly RFC 2547bis) defines **BGP/MPLS IP VPNs** — the most widely deployed enterprise WAN VPN technology in the world. Every major service provider (AT&T, Verizon, BT, NTT, etc.) uses this.

### Network Roles

```
MPLS L3VPN TOPOLOGY:
=====================

 Customer Site A                                    Customer Site B
 ┌──────────────┐                                  ┌──────────────┐
 │  CE-A        │                                  │  CE-B        │
 │  Router      │                                  │  Router      │
 │  AS: 65001   │                                  │  AS: 65001   │
 └──────┬───────┘                                  └──────┬───────┘
        │ eBGP or static                     eBGP or static│
        │                                                   │
 ┌──────▼───────┐  iBGP + MPLS   ┌─────────┐  iBGP + MPLS ┌──────▼───────┐
 │  PE-A        │───────────────>│   P1    │──────────────>│  PE-B        │
 │  Provider    │                │  Core   │               │  Provider    │
 │  Edge Router │                │  Router │               │  Edge Router │
 │              │                └────┬────┘               │              │
 │  VRF: CustA  │                     │                    │  VRF: CustA  │
 └──────────────┘                     │                    └──────────────┘
                                 ┌────▼────┐
                                 │   P2    │
                                 │  Core   │
                                 │  Router │
                                 └─────────┘

KEY POINTS:
• CE routers: Customer-managed. Run standard IP routing.
• PE routers: SP-managed. Run BGP VPN + MPLS. Maintain VRFs.
• P routers:  SP-managed. ONLY do MPLS label switching.
              P routers DON'T know about customer routes.
              P routers DON'T run VRF.
              P routers only see MPLS labels.
```

### Why P Routers Don't Know Customer Routes

This is a key design insight:

```
P router LFIB (what it sees):
┌──────────────────────────────────────────────────────┐
│  In-Label 300 → SWAP 400, Out eth1                   │
│  In-Label 500 → SWAP 600, Out eth0                   │
│  ... (only transport labels)                          │
└──────────────────────────────────────────────────────┘

P router does NOT know:
  - 10.1.0.0/24 belongs to Customer A
  - 10.2.0.0/24 belongs to Customer B
  - Anything about customer IP space

This means:
  ✓ P routers scale beautifully — no customer route explosion
  ✓ Security by design — P routers can't leak customer routes
  ✓ Customer routes isolated from core
```

---

## 8. VRF — Virtual Routing and Forwarding

### What Is a VRF?

A **VRF** is a separate, isolated routing table (and forwarding table) inside a single physical router. It's like having multiple virtual routers inside one box.

```
PE-A WITHOUT VRF (dangerous — routes could mix):
┌──────────────────────────────────────────────────────┐
│  SINGLE GLOBAL ROUTING TABLE                          │
│  10.1.0.0/24 → CE-A (Customer A)                    │
│  10.1.0.0/24 → CE-C (Customer C) ← CONFLICT!        │
│  Customers with overlapping IPs can't coexist.       │
└──────────────────────────────────────────────────────┘

PE-A WITH VRF (correct — complete isolation):
┌──────────────────────────────────────────────────────┐
│  VRF: Customer_A                                      │
│    10.1.0.0/24 → CE-A                               │
│    10.2.0.0/24 → PE-B (via MPLS label 200)          │
├──────────────────────────────────────────────────────┤
│  VRF: Customer_B                                      │
│    10.1.0.0/24 → CE-B  ← same prefix, no conflict!  │
│    172.16.0.0/16 → PE-C (via MPLS label 300)        │
├──────────────────────────────────────────────────────┤
│  Global (default) routing table                       │
│    (SP's own infrastructure routes)                  │
└──────────────────────────────────────────────────────┘
```

### VRF Components

Each VRF has:
1. **Routing Table (RIB)**: Stores routes for this VPN.
2. **Forwarding Table (FIB)**: Fast forwarding table derived from RIB.
3. **Route Distinguisher (RD)**: Unique identifier for this VRF.
4. **Route Target (RT)**: Import/export policy.
5. **Interface bindings**: Which physical/sub-interfaces belong to this VRF.

```
VRF DEFINITION (Cisco IOS-style concept, not implementation):

ip vrf Customer_A
  rd 65000:100
  route-target export 65000:100
  route-target import 65000:100

interface GigabitEthernet0/1
  ip vrf forwarding Customer_A
  ip address 192.168.1.1 255.255.255.0
```

---

## 9. Route Distinguisher (RD)

### What Is an RD?

A **Route Distinguisher** is a **64-bit value** prepended to an IPv4 prefix to create a globally unique **VPNv4 prefix**.

**Problem it solves**: Two different VPN customers may use the same private IP space (e.g., both use 10.0.0.0/24). When PE routers exchange routes via BGP, they need to distinguish which 10.0.0.0/24 belongs to which customer.

```
WITHOUT RD:
  BGP carries: 10.0.0.0/24 (ambiguous — which customer?)

WITH RD:
  BGP carries: 65000:100:10.0.0.0/24  (Customer A's 10.0.0.0/24)
               65000:200:10.0.0.0/24  (Customer B's 10.0.0.0/24)
  Now they're distinct — no confusion!
```

### RD Wire Format

```
RD is 8 bytes (64 bits) with 3 possible formats:

TYPE 0 (2-byte AS : 4-byte Admin):
┌────────────┬────────────┬─────────────────────────────────────┐
│  Type=0    │  AS Number │       Administrator                  │
│  (2 bytes) │  (2 bytes) │         (4 bytes)                   │
└────────────┴────────────┴─────────────────────────────────────┘
Example: 65000:100  (AS 65000, distinguisher 100)

TYPE 1 (4-byte IP : 2-byte Admin):
┌────────────┬─────────────────────────┬───────────────────────┐
│  Type=1    │      IP Address          │    Administrator      │
│  (2 bytes) │      (4 bytes)          │      (2 bytes)        │
└────────────┴─────────────────────────┴───────────────────────┘
Example: 192.0.2.1:100

TYPE 2 (4-byte AS : 2-byte Admin):
┌────────────┬─────────────────────────┬───────────────────────┐
│  Type=2    │   4-byte AS Number       │    Administrator      │
│  (2 bytes) │      (4 bytes)          │      (2 bytes)        │
└────────────┴─────────────────────────┴───────────────────────┘
Example: 65536:100

VPNv4 prefix = RD (8 bytes) + IPv4 prefix (4 bytes prefix + length)
             = 96-bit address used in BGP MP-BGP
```

### RD ≠ VPN Identifier

This is a common misconception:
- **RD** makes the route unique in BGP — it's just a naming device.
- **RD does NOT determine which VPN a route belongs to.**
- **Route Target (RT)** controls which VRFs import the route.

Two VRFs can have the same RD — unusual but allowed. Two VRFs can be in the same VPN with different RDs (common for redundancy).

---

## 10. Route Target (RT)

### What Is a Route Target?

A **Route Target** is a **BGP extended community** (8 bytes) that controls which VRFs **import** and **export** routes.

Think of it as a **tag** on a route:
- When exporting: PE attaches RT tag(s) to routes.
- When importing: PE imports routes whose RT tag matches its import list.

```
ROUTE TARGET AS A VPN MEMBERSHIP MECHANISM:
=============================================

PE-A VRF_A exports routes with RT: 65000:100
PE-B VRF_A imports routes with RT: 65000:100
PE-C VRF_B imports routes with RT: 65000:200  (different VPN)

Result:
  PE-A's VRF_A routes reach PE-B's VRF_A ✓
  PE-A's VRF_A routes DON'T reach PE-C's VRF_B ✓
  (Different RT — import filter blocks them)
```

### RT Wire Format

RT is a **BGP Extended Community** (Type 0x00 or 0x01 or 0x02):

```
EXTENDED COMMUNITY (8 bytes):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│  Type (1B)   │  Sub-Type (1B) │       Value (6 bytes)         │
└──────────────┴────────────────┴───────────────────────────────┘

For Route Target:
  Sub-Type = 0x02

TYPE 0x00 (2-byte AS):  [0x00][0x02][AS:2B][Local:4B]
  Example: 65000:100 → 0x00 0x02 0xFDE8 0x00000064

TYPE 0x01 (4-byte IP):  [0x01][0x02][IP:4B][Local:2B]
  Example: 192.0.2.1:100

TYPE 0x02 (4-byte AS):  [0x02][0x02][AS:4B][Local:2B]
  Example: 65536:100
```

### VPN Topologies Using RT

**Simple VPN (all sites communicate with all)**:
```
All VRFs:
  export RT: 65000:100
  import RT: 65000:100

Result: Full mesh — everyone can reach everyone.
```

**Hub-and-Spoke VPN**:
```
Hub VRF:
  export RT: 65000:1 (hub-export)
  import RT: 65000:2 (spoke-export)

Spoke VRFs:
  export RT: 65000:2 (spoke-export)
  import RT: 65000:1 (hub-export)

Result:
  Spokes send routes to Hub (Hub imports spoke RT).
  Hub sends routes to Spokes (Spokes import hub RT).
  Spokes CANNOT directly reach each other 
  (Spoke doesn't import spoke RT).
```

**Extranet VPN (Shared Services)**:
```
Shared Services VRF:
  export RT: 65000:999

Customer VRF A:
  import RT: 65000:100  (own VPN)
  import RT: 65000:999  (shared services)

Customer VRF B:
  import RT: 65000:200  (own VPN)
  import RT: 65000:999  (shared services)

Result:
  Customers A and B both access Shared Services.
  Customer A and B CANNOT reach each other.
```

---

## 11. Control Plane — How Routes Are Distributed

The control plane uses **MP-BGP** to distribute VPNv4 routes between PE routers. P routers are NOT involved.

### Step-by-Step Control Plane Flow

```
CONTROL PLANE ROUTE DISTRIBUTION:
===================================

Step 1: CE-A learns its own routes (connected, static, or via IGP/BGP with PE-A)

Step 2: PE-A learns CE-A routes via eBGP or static
  CE-A ──eBGP──> PE-A
  PE-A puts route 10.1.0.0/24 into VRF Customer_A

Step 3: PE-A converts route to VPNv4 and advertises to PE-B via MP-BGP
  PE-A → PE-B: 
    VPNv4 prefix:  65000:100:10.1.0.0/24
    Next-hop:      PE-A's loopback (10.0.0.1)
    Label:         200  (VPN label — identifies CE-A's interface in PE-A)
    RT:            65000:100

  NOTE: This BGP session is DIRECT between PE-A and PE-B.
        P routers do NOT participate in BGP.
        iBGP session typically between PE loopbacks.

Step 4: PE-B receives VPNv4 route, checks RT
  PE-B's VRF Customer_A imports RT 65000:100 → match!
  PE-B installs 10.1.0.0/24 in VRF Customer_A
  Next-hop: PE-A's loopback (10.0.0.1)
  VPN label: 200

Step 5: PE-B needs to reach PE-A's loopback
  This is done via the MPLS transport (LDP or RSVP-TE).
  PE-A's loopback is reachable via transport label 500.

Step 6: PE-B advertises 10.2.0.0/24 (CE-B's network) to PE-A similarly.

Full Control Plane View:
========================

CE-A          PE-A                  PE-B              CE-B
10.1.0.0/24  VRF_CustA             VRF_CustA         10.2.0.0/24
   │              │    MP-BGP         │                   │
   │──eBGP───────>│<─────────────────>│<──────────────────│
   │              │ VPNv4 routes      │                   │
   │              │ with Labels & RT  │                   │
```

### BGP Route Reflector

In a large SP network, maintaining full-mesh iBGP between all PEs is O(n²) sessions. **Route Reflectors (RR)** solve this:

```
WITHOUT ROUTE REFLECTOR (n=4 PEs):
  PE-A ↔ PE-B
  PE-A ↔ PE-C
  PE-A ↔ PE-D
  PE-B ↔ PE-C
  PE-B ↔ PE-D
  PE-C ↔ PE-D
  = 6 sessions (n*(n-1)/2)

WITH ROUTE REFLECTOR:
  PE-A → RR
  PE-B → RR    (RR reflects routes to all clients)
  PE-C → RR
  PE-D → RR
  = 4 sessions (n)

        PE-A
         │  \
         │    RR
         │  /    \
        PE-B      PE-C──PE-D
                  (all connect to RR, not each other)
```

---

## 12. Data Plane — How Packets Are Forwarded

The data plane uses a **two-label stack**:
1. **Outer label (Transport label)**: Gets packet from PE-A to PE-B through P routers.
2. **Inner label (VPN label)**: Tells PE-B which VRF/interface to use for final delivery.

### The MPLS Label Stack in VPN

```
MPLS VPN LABEL STACK:
======================

Packet leaving PE-A toward P1:
┌──────────┬───────────────────┬───────────────┬────────────────┐
│ Ethernet │  Transport Label  │   VPN Label   │  IP Packet     │
│ Header   │  (outer) = 500   │  (inner)=200  │  (Customer)    │
│          │  S=0, TTL=64     │  S=1, TTL=64  │                │
└──────────┴───────────────────┴───────────────┴────────────────┘

At P1 (core router, only does label swap):
  Incoming: label 500
  LFIB says: SWAP 500 → 750, out eth1
┌──────────┬───────────────────┬───────────────┬────────────────┐
│ Ethernet │  Transport Label  │   VPN Label   │  IP Packet     │
│ Header   │  (outer) = 750   │  (inner)=200  │  (Customer)    │
└──────────┴───────────────────┴───────────────┴────────────────┘

At P2 (penultimate hop — PHP):
  Incoming: label 750
  LFIB says: POP (implicit null from PE-B), forward to PE-B
┌──────────┬───────────────────┬────────────────┐
│ Ethernet │   VPN Label       │  IP Packet     │
│ Header   │   (inner) = 200   │  (Customer)    │
└──────────┴───────────────────┴────────────────┘
  (Transport label removed — PE-B gets packet with only VPN label)

At PE-B:
  Incoming: label 200
  LFIB says: POP label, lookup VRF Customer_A, forward to CE-B
┌──────────┬────────────────────────────────────┐
│ Ethernet │  IP Packet (Customer's original)   │
│ Header   │  10.1.0.50 → 10.2.0.50            │
└──────────┴────────────────────────────────────┘
```

### Complete End-to-End Data Plane Flow

```
END-TO-END PACKET FLOW: Host-A (10.1.0.50) → Host-B (10.2.0.50)
==================================================================

  HOST-A          CE-A           PE-A          P1            P2           PE-B         CE-B         HOST-B
 10.1.0.50      (CE Router)   (VRF_CustA)   (Core)        (Core)      (VRF_CustA)  (CE Router)   10.2.0.50
    │               │              │            │              │              │            │            │
    │ IP packet     │              │            │              │              │            │            │
    │ src:10.1.0.50 │              │            │              │              │            │            │
    │ dst:10.2.0.50 │              │            │              │              │            │            │
    │──────────────>│              │            │              │              │            │            │
    │               │ Route lookup │            │              │              │            │            │
    │               │ 10.2.0.50 → PE-A         │              │              │            │            │
    │               │──────────────>            │              │              │            │            │
    │               │              │ VRF lookup │              │              │            │            │
    │               │              │ 10.2.0.0/24│              │              │            │            │
    │               │              │ next-hop:PE-B             │              │            │            │
    │               │              │ VPN label: 200            │              │            │            │
    │               │              │ Transport: 500            │              │            │            │
    │               │              │ PUSH both labels          │              │            │            │
    │               │              │──────────────────────────>│              │            │            │
    │               │              │ [Eth|L:500|L:200|IP pkt]  │              │            │            │
    │               │              │            │ SWAP 500→750 │              │            │            │
    │               │              │            │─────────────>│              │            │            │
    │               │              │            │ [Eth|L:750|L:200|IP pkt]    │            │            │
    │               │              │            │              │ PHP: POP 750 │            │            │
    │               │              │            │              │─────────────>│            │            │
    │               │              │            │              │ [Eth|L:200|IP pkt]        │            │
    │               │              │            │              │              │ POP L:200  │            │
    │               │              │            │              │              │ VRF lookup │            │
    │               │              │            │              │              │ Forward to CE-B         │
    │               │              │            │              │              │───────────>│            │
    │               │              │            │              │              │            │ Route lookup│
    │               │              │            │              │              │            │ 10.2.0.50  │
    │               │              │            │              │              │            │───────────>│
    │               │              │            │              │              │            │ [IP packet] │
```

---

## 13. VPN Label Allocation

How does PE-A know which label (200) to push as the VPN label?

PE-B **allocates VPN labels** per-VRF or per-CE interface:

```
PE-B VPN LABEL ALLOCATION:
============================

When PE-B imports CE-B's route 10.2.0.0/24 into VRF_CustA:
  PE-B allocates label 200.
  PE-B advertises to PE-A via MP-BGP:
    "For VPNv4 prefix 65000:100:10.2.0.0/24,
     next-hop = PE-B loopback,
     VPN label = 200"

When PE-B receives packet with VPN label 200:
  Lookup in per-VRF label table:
    Label 200 → VRF_CustA → forward to CE-B interface

Two allocation modes:

1. Per-VRF labeling (one label per VRF):
   All routes in VRF_CustA get same label.
   PE-B must do IP lookup in VRF after popping label.
   More scalable (fewer labels).

2. Per-prefix labeling (one label per route):
   Each route gets unique label.
   PE-B goes directly to output interface — no IP lookup.
   Uses more labels but faster forwarding.
```

---

## 14. MPLS L3VPN: Inter-AS (Option A, B, C)

When customer sites span **multiple provider AS** boundaries:

```
INTER-AS SCENARIO:
===================

Customer Site A    AS 65001         AS 65002    Customer Site B
                 (SP1 network)    (SP2 network)
CE-A ── PE-A1 ─── P1 ─── ASBR1 ── ASBR2 ─── P2 ─── PE-B2 ── CE-B

ASBR = Autonomous System Border Router
```

### Option A (Back-to-Back VRF)

```
ASBR1 and ASBR2 exchange traffic like CE-PE.
Each ASBR has VRFs, runs eBGP IPv4.

Pros: Simple, secure, each SP controls its domain.
Cons: Scalability — one sub-interface per VPN between ASBRs.

   PE-A ── ASBR1 ──[sub-if per VPN]── ASBR2 ── PE-B
              VRF_A|VRF_A               VRF_A|VRF_A
```

### Option B (ASBR to ASBR labeled BGP)

```
ASBRs redistribute labeled VPNv4 routes between AS.
MPLS labels are re-allocated at ASBR boundary.

Pros: Scalable.
Cons: ASBRs see all VPN routes.

   PE-A ──(iBGP VPNv4)── ASBR1 ──(eBGP labeled VPNv4)── ASBR2 ──(iBGP VPNv4)── PE-B
```

### Option C (Multi-hop eBGP PE-to-PE)

```
PE routers in different AS exchange VPNv4 directly via multi-hop eBGP.
Route Reflectors in each AS help.

Pros: Most scalable, ASBRs only do MPLS forwarding.
Cons: Complex, PEs need multi-hop BGP sessions.

   PE-A ────────────── multi-hop eBGP VPNv4 ──────────────── PE-B
        ──(iBGP)── RR1 ──(ASBR1)──(ASBR2)── RR2 ──(iBGP)──
```

---

# PART IV — IPSec VPN

---

## 15. IPSec Overview

**IPSec (Internet Protocol Security — RFC 4301)** is a framework of protocols providing security services (confidentiality, integrity, authentication, anti-replay) at the IP layer.

IPSec operates in two modes:
- **Transport Mode**: Protects only the payload; original IP header is preserved.
- **Tunnel Mode**: Encapsulates entire original IP packet in new IP packet with new header.

```
TRANSPORT MODE (host-to-host):
┌────────┬────────────┬────────────────────────────────────────┐
│ IP Hdr │ ESP Header │ Original Payload (encrypted)           │
│(intact)│            │                                        │
└────────┴────────────┴────────────────────────────────────────┘
Use: End-to-end between two hosts that both support IPSec.

TUNNEL MODE (gateway-to-gateway — most common for VPN):
┌─────────────┬────────────┬────────────────────────────────────┐
│ New IP Hdr  │ ESP Header │ Original IP Hdr + Payload          │
│ (GW-A→GW-B) │            │ (entirely encrypted)               │
└─────────────┴────────────┴────────────────────────────────────┘
Use: Site-to-site VPN between two gateways.
     Hosts behind gateway don't need to know about IPSec.
```

### IPSec Protocol Suite

```
IPSec Framework:
┌─────────────────────────────────────────────────────────────┐
│                     IPSec                                    │
│  ┌──────────────┐         ┌──────────────────────────────┐  │
│  │  AH (IP:51)  │         │      ESP (IP:50)             │  │
│  │ Auth Header  │         │ Encapsulating Security       │  │
│  │              │         │ Payload                      │  │
│  │ Provides:    │         │                              │  │
│  │ • Integrity  │         │ Provides:                    │  │
│  │ • Auth       │         │ • Integrity                  │  │
│  │ • Anti-replay│         │ • Auth                       │  │
│  │              │         │ • Anti-replay                │  │
│  │ NO encryption│         │ • Confidentiality (encrypt)  │  │
│  └──────────────┘         └──────────────────────────────┘  │
│                                                              │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                 IKE (UDP:500/4500)                     │  │
│  │           Internet Key Exchange                        │  │
│  │           Key negotiation and SA establishment         │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 16. Security Associations (SA)

A **Security Association (SA)** is a one-way relationship between two endpoints that specifies:
- Which algorithm to use (e.g., AES-256-GCM)
- The key to use
- The SPI (Security Parameter Index) — 32-bit identifier
- Sequence number counter (for anti-replay)
- Lifetime (time or bytes)

**SA is unidirectional** — for bidirectional communication, you need **two SAs** (one in each direction).

```
TWO SAs for one IPSec connection:

  Gateway A ────────────────────────────────── Gateway B
            SA1: A→B, SPI:1001, key:K1
            SA2: B→A, SPI:2001, key:K2

  When A sends to B:
    A uses SA1 (SPI 1001, key K1) to encrypt.
    B receives, looks up SPI 1001 in SAD, finds SA1, decrypts.

  When B sends to A:
    B uses SA2 (SPI 2001, key K2) to encrypt.
    A receives, looks up SPI 2001 in SAD, finds SA2, decrypts.
```

### SAD and SPD

**SAD (Security Association Database)**: Stores all active SAs.

```
SAD ENTRY:
┌─────────────────────────────────────────────────────────────┐
│  SPI:         1001                                           │
│  Protocol:    ESP                                            │
│  Mode:        Tunnel                                         │
│  Destination: 203.0.113.2 (remote gateway)                  │
│  Source:      198.51.100.1 (local gateway)                  │
│  Encryption:  AES-256-CBC, Key: [256-bit key]               │
│  Auth:        HMAC-SHA256, Key: [256-bit key]                │
│  Seq Num:     4821 (anti-replay counter)                     │
│  Anti-replay Window: 64 packets                              │
│  Lifetime:    3600 seconds or 4294967295 bytes               │
└─────────────────────────────────────────────────────────────┘
```

**SPD (Security Policy Database)**: Defines what to do with traffic.

```
SPD ENTRY (policy):
┌──────────────────────────────────────────────────────────────┐
│  Traffic Selector:                                            │
│    Source:      10.1.0.0/24                                  │
│    Destination: 10.2.0.0/24                                  │
│    Protocol:    any                                          │
│  Action: PROTECT (use IPSec)                                 │
│    SA: SPI 1001 (or trigger IKE to create one)              │
│                                                              │
│ Other possible actions:                                       │
│  BYPASS  → forward without IPSec                            │
│  DISCARD → drop the packet                                   │
└──────────────────────────────────────────────────────────────┘
```

---

## 17. ESP — Encapsulating Security Payload (RFC 4303)

ESP is the most used IPSec protocol. It provides encryption, integrity, authentication, and anti-replay.

### ESP Header Format (Tunnel Mode)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│               NEW IP HEADER (outer tunnel header)             │
│        Src: GW-A    Dst: GW-B    Protocol: 50 (ESP)          │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ─┐
│                Security Parameter Index (SPI)                 │  │ ESP
│                        (4 bytes)                              │  │ Header
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │ (not
│                     Sequence Number                           │  │ encrypted)
│                        (4 bytes)                              │  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ─┘
│                   Initialization Vector (IV)                  │  ┐
│         (8 or 16 bytes depending on cipher)                   │  │ ESP
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │ Encrypted
│         ORIGINAL IP HEADER (inner, complete)                  │  │ payload
│         (protected by encryption)                             │  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │
│         ORIGINAL PAYLOAD (TCP/UDP/ICMP data)                  │  │
│         (protected by encryption)                             │  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │
│                        Padding                                │  │
│         (to align payload to block size)                      │  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  │
│   Pad Length (1B)    │   Next Header (1B = 4 for IPv4)       │  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+ ─┘
│                Integrity Check Value (ICV)                    │
│         HMAC-SHA256 = 16B, HMAC-SHA1 = 12B                   │
│         (covers SPI + Seq + encrypted payload)                │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

WHAT IS ENCRYPTED: IV + Original IP + Payload + Padding + Pad Len + Next Hdr
WHAT IS AUTHENTICATED (ICV covers): SPI + Seq + all encrypted bytes
```

### AH — Authentication Header (RFC 4302)

AH provides integrity and authentication but **NO encryption**. In practice, ESP with null encryption replaces AH, so AH is rarely used today.

```
AH HEADER (inserted between IP header and upper layer):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│  Next Header  │  Payload Len  │           RESERVED            │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│                 Security Parameter Index (SPI)                │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│                     Sequence Number                           │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│                  Integrity Check Value (ICV)                  │
│         (variable — covers entire IP packet, mutable          │
│          fields zeroed out during calculation)                │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

NOTE: AH cannot traverse NAT because:
      ICV covers the entire IP packet including IP header.
      NAT changes src/dst IP → ICV becomes invalid.
      This is why ESP is preferred.
```

---

## 18. IKE — Internet Key Exchange

**IKE (RFC 7296 for IKEv2)** is the protocol used to negotiate and establish IPSec SAs. IKE runs over **UDP port 500** (and 4500 for NAT-Traversal).

### IKEv2 Exchange (most modern)

IKEv2 is simpler and more efficient than IKEv1. It uses **4 messages** to establish an IPSec tunnel:

```
IKEv2 EXCHANGE (Initial Tunnel Setup — 4 messages):
=====================================================

Initiator (GW-A)                              Responder (GW-B)
       │                                             │
       │──── IKE_SA_INIT (msg 1) ──────────────────>│
       │  Contains:                                  │
       │  • SA proposals (algorithms)                │
       │  • Key Exchange Data (DH public value)      │
       │  • Nonce (random, anti-replay)              │
       │                                             │
       │<─── IKE_SA_INIT (msg 2) ────────────────────│
       │  Contains:                                  │
       │  • Chosen SA (algorithms)                   │
       │  • Key Exchange Data (DH public value)      │
       │  • Nonce                                    │
       │  (Both sides now compute shared DH secret   │
       │   and derive IKE SA encryption keys)        │
       │                                             │
       [All subsequent messages are encrypted]
       │                                             │
       │──── IKE_AUTH (msg 3, encrypted) ──────────>│
       │  Contains:                                  │
       │  • Authentication (certificate or PSK hash) │
       │  • IDi (initiator identity)                 │
       │  • SA proposal for Child SA (ESP/AH)        │
       │  • Traffic Selectors (what to protect)      │
       │  • Key Exchange for Child SA                │
       │                                             │
       │<─── IKE_AUTH (msg 4, encrypted) ────────────│
       │  Contains:                                  │
       │  • Authentication (responder)               │
       │  • IDr (responder identity)                 │
       │  • Child SA parameters                      │
       │  • Traffic Selectors (confirmed)            │
       │  (Child SA = the actual IPSec/ESP SA)       │
       │                                             │
       [IKE SA established — used for management]
       [Child SA (ESP) established — used for data]
       │                                             │
       │==== ENCRYPTED DATA FLOW (ESP) ============>│
       │<=== ENCRYPTED DATA FLOW (ESP) =============│

Rekeying (when SA expires):
       │──── CREATE_CHILD_SA ──────────────────────>│
       │<─── CREATE_CHILD_SA ────────────────────────│
       (new keys derived, old SA retired)
```

### Key Derivation in IKE

```
DIFFIE-HELLMAN KEY EXCHANGE:
==============================
Secret math: both sides compute same value without sending it over network.

1. Agree on group (DH Group 14 = 2048-bit MODP, DH Group 20 = 384-bit ECP)
2. Initiator: random 'a', sends g^a mod p
3. Responder: random 'b', sends g^b mod p
4. Both compute: (g^b)^a = g^ab = (g^a)^b = shared_secret

From DH shared secret, IKE derives:
  SKEYSEED = PRF(Ni | Nr, g^ab)   (PRF = pseudo-random function, e.g., HMAC-SHA256)
  
  {SK_d | SK_ai | SK_ar | SK_ei | SK_er | SK_pi | SK_pr} 
           = PRF+(SKEYSEED, Ni | Nr | SPIi | SPIr)

  SK_d  = key for deriving child SA keys
  SK_ai = initiator auth key (HMAC)
  SK_ar = responder auth key (HMAC)
  SK_ei = initiator encryption key
  SK_er = responder encryption key
  SK_pi = initiator auth payload key (for AUTH message)
  SK_pr = responder auth payload key

Encryption Algorithms (IKE SA negotiation):
  AES-128-CBC, AES-256-CBC, AES-128-GCM, AES-256-GCM, ChaCha20-Poly1305

Integrity Algorithms:
  HMAC-SHA1-96, HMAC-SHA256-128, HMAC-SHA384-192, HMAC-SHA512-256

DH Groups:
  Group 14: 2048-bit MODP (minimum acceptable today)
  Group 19: 256-bit ECP (Elliptic Curve)
  Group 20: 384-bit ECP
  Group 21: 521-bit ECP
```

### IKE NAT-Traversal (NAT-T)

When gateways are behind NAT, IKE/ESP need special handling:

```
NAT-T DETECTION:
=================

During IKE_SA_INIT, both sides send NAT_DETECTION payloads:
  NAT_DETECTION_SOURCE_IP = hash(SPIs, src-IP, src-port)
  NAT_DETECTION_DEST_IP   = hash(SPIs, dst-IP, dst-port)

If received hash ≠ computed hash → NAT detected!

AFTER NAT DETECTION:
  IKE switches from UDP:500 → UDP:4500
  ESP is encapsulated in UDP:4500 (ESP-in-UDP):
  
  ┌──────────┬──────────┬──────────┬────────────────────────┐
  │ Outer IP │ UDP:4500 │ Non-ESP  │ ESP packet             │
  │ header   │ header   │ Marker   │                        │
  │          │          │ (4 zeros)│                        │
  └──────────┴──────────┴──────────┴────────────────────────┘

  The 4-zero marker distinguishes ESP-in-UDP from IKE (which also uses UDP:4500).
  IKE packets have non-zero first 4 bytes.
```

---

# PART V — GRE TUNNELING

---

## 19. GRE — Generic Routing Encapsulation (RFC 2784, RFC 2890)

**GRE** is a simple tunneling protocol that encapsulates any network layer protocol inside IP packets. Unlike IPSec, GRE provides **no encryption** and **no authentication** by itself.

### Why Use GRE?

- Tunnel non-IP protocols over IP networks.
- Create simple IP tunnels without cryptographic overhead.
- Enable multicast/broadcast over unicast networks (IPSec doesn't support multicast).
- Combined with IPSec: GRE for routing features + IPSec for security.

### GRE Header Format

```
GRE HEADER (RFC 2784):
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│C│ Reserved0 |K|S| Reserved1  │         Version               │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│         Protocol Type (EtherType of encapsulated protocol)    │
│  0x0800 = IPv4, 0x86DD = IPv6, 0x0806 = ARP, 0x8847 = MPLS  │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│        OPTIONAL: Checksum (if C=1)           │  Reserved      │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
│                OPTIONAL: Key (if K=1, 4 bytes)                │
├─────────── identifies which GRE tunnel this is ───────────────┤
│             OPTIONAL: Sequence Number (if S=1)                │
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

FLAGS:
  C = Checksum Present
  K = Key Present      (use key to identify which tunnel)
  S = Sequence Present (for ordered delivery)
  Version = 0 (always for standard GRE)

MINIMUM GRE HEADER = 4 bytes (C=0, K=0, S=0)
```

### GRE Encapsulation Flow

```
GRE PACKET STRUCTURE:
======================

Original packet (from Host-A 10.1.0.50 to Host-B 10.2.0.50):
┌──────────────────────────────────────────────────────────────┐
│ IP Hdr (10.1.0.50→10.2.0.50) │ TCP/UDP │ Payload            │
└──────────────────────────────────────────────────────────────┘

After GRE encapsulation at Tunnel Source (GW-A 203.0.113.1):
┌──────────────────┬──────────────────┬────────────────────────┐
│ Outer IP Header  │   GRE Header     │  Original IP Packet    │
│ Src: 203.0.113.1 │ Proto: 0x0800    │ (inner — intact)       │
│ Dst: 203.0.113.2 │ (IPv4 payload)   │ 10.1.0.50→10.2.0.50   │
│ Proto: 47 (GRE)  │ 4 bytes min      │                        │
└──────────────────┴──────────────────┴────────────────────────┘

GRE IP Protocol number = 47

After GRE decapsulation at Tunnel Dest (GW-B 203.0.113.2):
┌──────────────────────────────────────────────────────────────┐
│ IP Hdr (10.1.0.50→10.2.0.50) │ TCP/UDP │ Payload            │
└──────────────────────────────────────────────────────────────┘
(original packet restored — forwarded normally to 10.2.0.50)
```

### GRE over IPSec (Recommended Pattern)

This is the most common secure tunneling pattern for site-to-site VPNs:

```
GRE OVER IPSec ARCHITECTURE:
==============================

  Site A                         Internet                      Site B
┌──────────┐                                                ┌──────────┐
│          │                                                │          │
│  Hosts   │                                                │  Hosts   │
│10.1.0.0/24                                              10.2.0.0/24 │
│          │                                                │          │
│  GW-A    │─────────────────────────────────────────────── GW-B      │
│ 198.51.1 │   [Outer IP][ESP Header][Inner GRE+IP pkt]    │ 203.0.2  │
└──────────┘                                                └──────────┘

Benefits:
  • GRE carries routing protocols (OSPF, EIGRP over multicast)
  • IPSec provides encryption and authentication
  • Single tunnel interface simplifies routing configuration

Packet layers from outer to inner:
  [Ethernet][Outer IP][ESP][IV][GRE Header][Inner IP][Payload][Padding][ICV]

MTU CONCERN:
  Outer IP: 20B
  ESP Header: 8B
  IV: 16B (AES-CBC)
  GRE Header: 4B
  Inner IP: 20B
  ESP Trailer + ICV: ~22B
  ─────────────────
  Overhead: ~90 bytes

  If physical MTU = 1500:
  Available for payload = 1500 - 90 = 1410 bytes
  TCP MSS must be clamped to 1370 (accounting for TCP header)
```

### mGRE — Multipoint GRE

mGRE allows a single tunnel interface to have multiple remote endpoints — used in DMVPN:

```
mGRE IN DMVPN (Dynamic Multipoint VPN):
=========================================

                    HUB (mGRE interface)
                    203.0.113.1
                   /     |      \
                  /      |       \
           Spoke1      Spoke2    Spoke3
         198.51.1    198.51.2   198.51.3

With mGRE + NHRP (Next Hop Resolution Protocol):
  Spokes can discover each other's real IP and create
  DIRECT spoke-to-spoke GRE tunnels dynamically.
  No need for static tunnel configuration per spoke pair.
```

---

# PART VI — OTHER VPN TYPES

---

## 20. L2TPv3 — Layer 2 Tunneling Protocol v3 (RFC 3931)

L2TP tunnels Layer 2 frames over IP. Version 3 supports Ethernet, ATM, Frame Relay, PPP.

```
L2TPv3 PACKET (Ethernet pseudowire):
┌──────────────────────────────────────────────────────────────┐
│ Outer IP Header (Src: PE-A, Dst: PE-B, Proto: 115=L2TP)     │
├──────────────────────────────────────────────────────────────┤
│ L2TP Session Header:                                         │
│  Session ID (4B) | Cookie (0-8B, optional auth)             │
├──────────────────────────────────────────────────────────────┤
│ Inner Ethernet Frame (customer frame, intact)                │
└──────────────────────────────────────────────────────────────┘

Use case:
  Carrier Ethernet services — emulate an Ethernet link between
  two customer sites over a packet network.

L2TP over IPSec:
  Common for remote access VPN (Android, iOS, Windows support natively).
```

---

## 21. VPLS — Virtual Private LAN Service

VPLS emulates a **multi-point Ethernet LAN** over an MPLS/IP network. Multiple sites appear to be on the same Ethernet segment.

```
VPLS ARCHITECTURE:
===================

          CE-A                  MPLS Core               CE-B
          ──────   PE-A ─────────────────── PE-B   ──────────
  Site A  ─────── │    │ ─────────────────── │    │ ─────── Site B
  (10.1.x)        │    │     Pseudowires      │    │         (10.1.x)
          ─────── │    │ ─────────────────── │    │ ─────── Site C
                  └────┘                     └────┘

Each PE maintains a MAC forwarding table per VPLS instance.
Packets are switched based on Ethernet MAC addresses.
Flooding for unknown MAC (like real Ethernet).
Control plane: LDP signaling or BGP (RFC 4761).

FRAME STRUCTURE IN VPLS:
┌─────────────────────────────────────────────────────────────┐
│ Outer Ethernet │ Transport Label │ VC Label │ Customer Frame│
│   (PE-to-PE)   │  (MPLS tunnel) │ (VPLS ID)│              │
└─────────────────────────────────────────────────────────────┘
```

---

## 22. EVPN — Ethernet VPN (RFC 7432)

EVPN is the modern evolution of VPLS. Uses MP-BGP to distribute MAC/IP information — eliminating flooding for unknown unicast.

```
EVPN ROUTE TYPES:
==================
  Type 1: Ethernet Auto-Discovery (per-ES/per-EVI)
  Type 2: MAC/IP Advertisement (MAC + optionally IP)
  Type 3: Inclusive Multicast Ethernet Tag (BUM traffic)
  Type 4: Ethernet Segment Route (multi-homing)
  Type 5: IP Prefix Route (L3 routing in EVPN)

EVPN vs VPLS:
┌────────────────────┬─────────────────┬─────────────────────┐
│ Feature            │ VPLS            │ EVPN                │
├────────────────────┼─────────────────┼─────────────────────┤
│ Control plane      │ LDP/BGP         │ MP-BGP only         │
│ MAC learning       │ Data plane flood│ Control plane (BGP) │
│ Multi-homing       │ Basic (STP)     │ Advanced (LACP-based)│
│ L3 integration     │ Separate        │ Native (Type 5)     │
│ Unknown unicast    │ Flood           │ Suppress (BGP proxy)│
│ ARP suppression    │ No              │ Yes                 │
└────────────────────┴─────────────────┴─────────────────────┘
```

---

## 23. SSL/TLS VPN

SSL VPN operates at Layer 4/7. Uses TLS to create a secure channel. Two types:

```
TYPE 1: Clientless SSL VPN
  User opens browser, accesses HTTPS portal.
  Web applications proxied through gateway.
  No client software needed.

TYPE 2: SSL VPN with thin client (TCP tunnel only)
  Java applet or browser extension creates TCP-level tunnel.

TYPE 3: Full-tunnel SSL VPN
  Client software installs virtual NIC.
  All IP traffic tunneled via TLS.
  Examples: OpenVPN, Cisco AnyConnect, GlobalProtect.

OpenVPN PACKET (TLS tunnel):
┌──────────────────────────────────────────────────────────────┐
│ Outer IP │ UDP or TCP │ OpenVPN  │ TLS Record │ Inner IP+Data│
│ Header   │ Header     │ Header   │ (encrypted)│              │
└──────────────────────────────────────────────────────────────┘

TLS Handshake (simplified):
  Client                              Server
    │──── ClientHello ───────────────>│
    │     (TLS version, ciphers, random)
    │<─── ServerHello ────────────────│
    │     (chosen cipher, random)
    │<─── Certificate ────────────────│
    │     (server's X.509 cert)
    │<─── ServerHelloDone ────────────│
    │──── ClientKeyExchange ─────────>│
    │     (DH/ECDH pubkey)
    │──── ChangeCipherSpec ──────────>│
    │──── Finished ──────────────────>│
    │<─── ChangeCipherSpec ───────────│
    │<─── Finished ───────────────────│
    │===== ENCRYPTED DATA FLOW ======>│
```

---

## 24. WireGuard

WireGuard is a modern, minimal VPN built into the Linux kernel (5.6+). It's worth knowing as it represents the future direction.

```
WIREGUARD DESIGN PRINCIPLES:
==============================
  • Only one cipher suite: ChaCha20-Poly1305 (no negotiation)
  • Noise protocol framework for handshake
  • Curve25519 for key exchange
  • BLAKE2s for hashing
  • Uses UDP only
  • No concept of "connection state" (stateless-ish)
  • Cryptokey routing: map public key → allowed IPs

WIREGUARD HANDSHAKE (Noise_IKpsk2):
=====================================
  Initiator                              Responder
    │──── Initiation Message (148 bytes) ──>│
    │  Contains:
    │  • Sender index (4B)
    │  • Ephemeral key (32B, encrypted)
    │  • Static key (32B, encrypted)
    │  • Timestamp (12B, encrypted)
    │  • MAC1 (16B), MAC2 (16B, cookie-based)
    │
    │<─── Response Message (92 bytes) ───────│
    │  Contains:
    │  • Sender index
    │  • Receiver index
    │  • Ephemeral key (32B)
    │  • Empty payload (encrypted)
    │  • MAC1, MAC2
    │
    [Session keys derived from Noise handshake]
    │
    │══════ DATA PACKETS (encrypted) ════════│
    │  [4B type][4B receiver index]
    │  [8B counter][encrypted payload]
    │  [16B Poly1305 tag]

WireGuard handshake is only 2 messages!
Compare to IKEv2's 4 messages.
```

---

# PART VII — PACKET WALKTHROUGHS

---

## 25. Complete Packet Trace: MPLS L3VPN

```
SCENARIO:
  Host-A (10.1.0.50) at Site-A pings Host-B (10.2.0.50) at Site-B.
  SP uses MPLS L3VPN with RD 65000:100.

NETWORK TOPOLOGY:
  Host-A──CE-A──PE-A──P1──P2──PE-B──CE-B──Host-B
  10.1.0.50                              10.2.0.50
            192.168.1.x  10.0.0.x  10.0.0.x  192.168.2.x

LABELS:
  Transport label (PE-A→PE-B via P1,P2): 500 → 750 → POP
  VPN label (for CE-B): 200

STEP 1: Host-A sends ICMP Echo Request
─────────────────────────────────────
  [Eth: src=A, dst=CE-A][IP: 10.1.0.50→10.2.0.50][ICMP Echo]

STEP 2: CE-A forwards to PE-A (default route via PE-A)
─────────────────────────────────────────────────────
  [Eth: src=CE-A, dst=PE-A][IP: 10.1.0.50→10.2.0.50][ICMP Echo]

STEP 3: PE-A processes packet
─────────────────────────────
  1. Determine input interface → mapped to VRF Customer_A
  2. Lookup 10.2.0.50 in VRF Customer_A routing table
     → 10.2.0.0/24 via PE-B (next-hop learned from MP-BGP)
     → VPN label: 200, Transport label: 500
  3. PUSH both labels (VPN inner, Transport outer)
  4. Forward out toward P1

  [Eth][IP:PE-A→P1][MPLS:500,S=0,TTL=64][MPLS:200,S=1,TTL=64][IP:10.1.0.50→10.2.0.50][ICMP]
   ^outer tunnel label^                    ^VPN label (inner)^   ^original customer packet^

STEP 4: P1 processes packet
─────────────────────────────
  1. Pop Ethernet, read top MPLS label: 500
  2. LFIB lookup: 500 → SWAP 750, out eth1
  3. Decrement TTL in outer label: 64→63

  [Eth][IP:P1→P2][MPLS:750,S=0,TTL=63][MPLS:200,S=1,TTL=64][IP:10.1.0.50→10.2.0.50][ICMP]

STEP 5: P2 processes packet (Penultimate Hop Pop)
──────────────────────────────────────────────────
  1. LFIB lookup: 750 → POP (implicit null signaled by PE-B)
  2. Forward to PE-B with only VPN label

  [Eth][IP:P2→PE-B][MPLS:200,S=1,TTL=64][IP:10.1.0.50→10.2.0.50][ICMP]
   (transport label removed — PE-B only sees VPN label + IP packet)

STEP 6: PE-B processes packet
─────────────────────────────
  1. Read top MPLS label: 200
  2. LFIB lookup: 200 → POP, associated with VRF Customer_A, output → CE-B interface
  3. Remove VPN label
  4. Lookup 10.2.0.50 in VRF Customer_A
     → 10.2.0.0/24 is directly connected via CE-B interface
  5. Forward to CE-B

  [Eth][IP:10.1.0.50→10.2.0.50][ICMP Echo Request]

STEP 7: CE-B forwards to Host-B
────────────────────────────────
  Routing lookup: 10.2.0.50 is local → deliver to Host-B.

STEP 8: Host-B sends ICMP Echo Reply (reverse path, same logic)
```

---

## 26. Complete Packet Trace: IPSec VPN Tunnel Mode

```
SCENARIO:
  Host-A (10.1.0.50) → Host-B (10.2.0.50) over site-to-site IPSec tunnel.
  GW-A (198.51.100.1) → GW-B (203.0.113.1)
  SA: SPI=1001, AES-256-CBC + HMAC-SHA256

STEP 1: Host-A sends IP packet
─────────────────────────────
  [Eth][IP: 10.1.0.50→10.2.0.50][TCP][Payload]

STEP 2: GW-A receives packet, SPD lookup
─────────────────────────────────────────
  SPD: src=10.1.0.0/24, dst=10.2.0.0/24 → PROTECT (ESP tunnel)
  SAD lookup: SA for this selector, SPI=1001
  Increment sequence number: seq=4822

STEP 3: GW-A builds ESP packet
────────────────────────────────
  a) Compute padding to align payload to AES block size (16 bytes):
     Inner payload = 20(IP) + 20(TCP) + Ndata bytes
     Pad to multiple of 16, add Pad Length byte + Next Header byte (4=IPv4)
     
  b) Generate random IV (16 bytes for AES-CBC)
  
  c) Encrypt [Inner IP Header + TCP + Payload + Padding + PadLen + NextHdr]:
     Ciphertext = AES-256-CBC(key=K_enc, IV=IV, plaintext)
  
  d) Build ESP header: [SPI=1001][Seq=4822]
  
  e) Compute ICV (HMAC-SHA256-128):
     ICV = HMAC-SHA256(key=K_auth, msg=[SPI][Seq][IV][Ciphertext])[0:16]
  
  f) Build outer IP header: src=198.51.100.1, dst=203.0.113.1, proto=50(ESP)
  
  g) Final packet:

  ┌───────────────┬────────────┬────────┬──────────┬──────────┬──────────────┬─────┐
  │ Outer IP Hdr  │ESP Hdr     │   IV   │Ciphertext│Padding+  │     ICV      │     │
  │198.51.1→203.1 │SPI:1001    │(16B)   │          │PadLen+NH │  (16 bytes)  │     │
  │ proto=50      │Seq:4822    │        │          │          │HMAC-SHA256   │     │
  └───────────────┴────────────┴────────┴──────────┴──────────┴──────────────┴─────┘
    [VISIBLE/CLEAR][─────CLEAR──────][───────────── ENCRYPTED ─────────────]

  NOTE: To an eavesdropper:
    • They see GW-A and GW-B's IPs ✓ (outer IP)
    • They see SPI ✓
    • They see sequence number ✓
    • Everything else is encrypted ✗

STEP 4: Internet routing sends packet from GW-A to GW-B
──────────────────────────────────────────────────────
  Normal IP routing — routers only see outer IP header (198.51.100.1 → 203.0.113.1).

STEP 5: GW-B receives ESP packet, processes it
───────────────────────────────────────────────
  a) Extract SPI from ESP header: 1001
  b) SAD lookup by (SPI=1001, Proto=ESP, Dst=203.0.113.1) → find SA
  c) Anti-replay check: seq=4822 within window? Yes.
  d) Verify ICV: compute HMAC-SHA256(K_auth, [SPI][Seq][IV][Ciphertext])
     Compare with received ICV → match → authentic.
  e) Decrypt: plaintext = AES-256-CBC-decrypt(K_enc, IV, Ciphertext)
  f) Remove padding (read Pad Length byte)
  g) Check Next Header = 4 (IPv4)
  h) Forward inner IP packet (10.1.0.50 → 10.2.0.50) via normal routing

STEP 6: GW-B's routing table for 10.2.0.0/24 → send to Host-B
```

---

# PART VIII — C IMPLEMENTATION

---

## 27. VRF Simulation in C

```c
/*
 * ipvpn_vrf.c — VRF (Virtual Routing and Forwarding) Simulation
 *
 * Simulates multiple isolated routing tables in a PE router.
 * Demonstrates: VRF creation, route insertion, LPM lookup per VRF.
 *
 * Author: IPVPN Deep Dive Study
 * Standard: C11
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <arpa/inet.h>
#include <assert.h>

/* ─────────────────────────────────────────────────────────────────────── */
/* CONSTANTS AND LIMITS                                                     */
/* ─────────────────────────────────────────────────────────────────────── */

#define MAX_VRFS            16
#define MAX_ROUTES_PER_VRF  256
#define MAX_VRF_NAME        64
#define MAX_IFACE_NAME      32
#define INVALID_LABEL       0xFFFFFFFF

/* ─────────────────────────────────────────────────────────────────────── */
/* DATA STRUCTURES                                                          */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Route Target: BGP Extended Community (8 bytes)
 * Format: Type(1B) SubType(1B) Value(6B)
 * For RT: SubType = 0x02
 */
typedef struct {
    uint8_t  type;        /* 0x00=2B-AS, 0x01=IPv4, 0x02=4B-AS */
    uint8_t  subtype;     /* 0x02 for Route Target */
    uint32_t admin;       /* AS or IP value */
    uint16_t local;       /* local discriminator */
} RouteTarget;

/*
 * Route Distinguisher: 8 bytes prepended to IPv4 prefix
 * RD + IPv4 prefix = VPNv4 prefix
 */
typedef struct {
    uint8_t  type;        /* 0=2B-AS:4B-admin, 1=IPv4:2B-admin, 2=4B-AS:2B-admin */
    uint32_t admin;
    uint32_t local;
} RouteDistinguisher;

/*
 * A single routing entry in a VRF.
 * Represents one IP prefix → next-hop mapping.
 */
typedef struct {
    uint32_t prefix;      /* Network address (host byte order) */
    uint8_t  prefix_len;  /* Prefix length (0–32) */
    uint32_t next_hop;    /* Next-hop IP (host byte order), 0=directly connected */
    char     iface[MAX_IFACE_NAME];  /* Output interface name */
    uint32_t mpls_label;  /* MPLS VPN label for this route (INVALID_LABEL if none) */
    uint32_t metric;      /* Route metric/preference */
    bool     is_local;    /* True if directly connected */
} VrfRoute;

/*
 * VRF structure: one isolated routing domain.
 * A physical PE router holds multiple VRFs.
 */
typedef struct {
    char              name[MAX_VRF_NAME];
    RouteDistinguisher rd;
    RouteTarget        rt_import[8]; /* route targets this VRF imports */
    RouteTarget        rt_export[8]; /* route targets this VRF exports */
    uint8_t            rt_import_count;
    uint8_t            rt_export_count;
    VrfRoute           routes[MAX_ROUTES_PER_VRF];
    uint32_t           route_count;
    uint32_t           vrf_id;       /* internal VRF identifier */
} Vrf;

/*
 * PE Router: holds multiple VRFs.
 */
typedef struct {
    char   hostname[MAX_VRF_NAME];
    Vrf    vrfs[MAX_VRFS];
    uint8_t vrf_count;
} PeRouter;

/* ─────────────────────────────────────────────────────────────────────── */
/* HELPER FUNCTIONS                                                         */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Create a bitmask for a given prefix length.
 * prefix_len=24 → 0xFFFFFF00
 * prefix_len=0  → 0x00000000 (matches everything)
 */
static uint32_t prefix_mask(uint8_t prefix_len) {
    if (prefix_len == 0) return 0;
    if (prefix_len >= 32) return 0xFFFFFFFF;
    return ~((1U << (32 - prefix_len)) - 1);
}

/*
 * Check if a destination IP matches a prefix.
 * Uses LPM (Longest Prefix Match) logic.
 */
static bool prefix_match(uint32_t dest, uint32_t prefix, uint8_t plen) {
    uint32_t mask = prefix_mask(plen);
    return (dest & mask) == (prefix & mask);
}

/* Format IPv4 address as string (thread-unsafe, for display only) */
static const char *ip_to_str(uint32_t ip) {
    static char buf[INET_ADDRSTRLEN];
    uint32_t network_order = htonl(ip);
    inet_ntop(AF_INET, &network_order, buf, sizeof(buf));
    return buf;
}

/* Parse "a.b.c.d" into uint32_t (host byte order) */
static uint32_t str_to_ip(const char *s) {
    struct in_addr a;
    inet_pton(AF_INET, s, &a);
    return ntohl(a.s_addr);
}

/* ─────────────────────────────────────────────────────────────────────── */
/* VRF OPERATIONS                                                            */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Initialize a PE router with no VRFs.
 */
void pe_init(PeRouter *pe, const char *hostname) {
    memset(pe, 0, sizeof(*pe));
    strncpy(pe->hostname, hostname, MAX_VRF_NAME - 1);
}

/*
 * Create a new VRF on this PE router.
 * Returns pointer to the created VRF, or NULL on error.
 */
Vrf *pe_create_vrf(PeRouter *pe, const char *name,
                   uint8_t rd_type, uint32_t rd_admin, uint32_t rd_local) {
    if (pe->vrf_count >= MAX_VRFS) {
        fprintf(stderr, "[ERROR] Maximum VRFs (%d) reached on %s\n",
                MAX_VRFS, pe->hostname);
        return NULL;
    }

    Vrf *vrf = &pe->vrfs[pe->vrf_count];
    memset(vrf, 0, sizeof(*vrf));
    strncpy(vrf->name, name, MAX_VRF_NAME - 1);

    /* Assign Route Distinguisher */
    vrf->rd.type  = rd_type;
    vrf->rd.admin = rd_admin;
    vrf->rd.local = rd_local;
    vrf->vrf_id   = pe->vrf_count;

    pe->vrf_count++;

    printf("[VRF] Created VRF '%s' on %s  RD=%u:%u\n",
           name, pe->hostname, rd_admin, rd_local);
    return vrf;
}

/*
 * Find a VRF by name. Returns NULL if not found.
 */
Vrf *pe_find_vrf(PeRouter *pe, const char *name) {
    for (uint8_t i = 0; i < pe->vrf_count; i++) {
        if (strcmp(pe->vrfs[i].name, name) == 0) {
            return &pe->vrfs[i];
        }
    }
    return NULL;
}

/*
 * Add a Route Target to a VRF (import or export).
 */
void vrf_add_rt(Vrf *vrf, bool is_import,
                uint8_t rt_type, uint32_t rt_admin, uint16_t rt_local) {
    RouteTarget rt = {
        .type    = rt_type,
        .subtype = 0x02,
        .admin   = rt_admin,
        .local   = rt_local,
    };

    if (is_import && vrf->rt_import_count < 8) {
        vrf->rt_import[vrf->rt_import_count++] = rt;
        printf("[VRF] %s import RT %u:%u\n", vrf->name, rt_admin, rt_local);
    } else if (!is_import && vrf->rt_export_count < 8) {
        vrf->rt_export[vrf->rt_export_count++] = rt;
        printf("[VRF] %s export RT %u:%u\n", vrf->name, rt_admin, rt_local);
    }
}

/*
 * Add a route into a VRF routing table.
 * prefix_str: "10.1.0.0"
 * prefix_len: 24
 * next_hop_str: "192.168.1.1" (or NULL for directly connected)
 * label: MPLS VPN label (or INVALID_LABEL)
 */
bool vrf_add_route(Vrf *vrf, const char *prefix_str, uint8_t prefix_len,
                   const char *next_hop_str, const char *iface,
                   uint32_t label, uint32_t metric) {
    if (vrf->route_count >= MAX_ROUTES_PER_VRF) {
        fprintf(stderr, "[ERROR] Route table full in VRF %s\n", vrf->name);
        return false;
    }

    VrfRoute *r = &vrf->routes[vrf->route_count];
    memset(r, 0, sizeof(*r));

    r->prefix     = str_to_ip(prefix_str);
    r->prefix_len = prefix_len;
    r->mpls_label = label;
    r->metric     = metric;

    if (next_hop_str == NULL) {
        r->next_hop = 0;
        r->is_local = true;
    } else {
        r->next_hop = str_to_ip(next_hop_str);
        r->is_local = false;
    }

    if (iface) {
        strncpy(r->iface, iface, MAX_IFACE_NAME - 1);
    }

    vrf->route_count++;

    printf("[ROUTE] VRF=%s  %s/%u via %s  label=%u\n",
           vrf->name, prefix_str, prefix_len,
           next_hop_str ? next_hop_str : "direct",
           label);
    return true;
}

/*
 * Longest Prefix Match (LPM) lookup in a VRF.
 *
 * Mental model: Go through ALL routes and find the one
 * with the LONGEST prefix length that still matches the destination.
 *
 * Time: O(N) — in real routers, trie/TCAM makes this O(1)
 *
 * Returns pointer to best matching route, or NULL if no match.
 */
const VrfRoute *vrf_lookup(const Vrf *vrf, uint32_t dest_ip) {
    const VrfRoute *best = NULL;
    uint8_t         best_len = 0;

    for (uint32_t i = 0; i < vrf->route_count; i++) {
        const VrfRoute *r = &vrf->routes[i];

        /* Check if this prefix matches the destination */
        if (prefix_match(dest_ip, r->prefix, r->prefix_len)) {
            /* Is this match more specific (longer prefix)? */
            if (best == NULL || r->prefix_len > best_len ||
                (r->prefix_len == best_len && r->metric < best->metric)) {
                best     = r;
                best_len = r->prefix_len;
            }
        }
    }
    return best;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* RT MATCHING (VPN MEMBERSHIP LOGIC)                                        */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Check if an export RT matches any import RT in a VRF.
 * This determines if a VPNv4 route should be imported into a VRF.
 */
bool rt_matches(const Vrf *vrf, const RouteTarget *export_rt) {
    for (uint8_t i = 0; i < vrf->rt_import_count; i++) {
        const RouteTarget *imp = &vrf->rt_import[i];
        if (imp->admin == export_rt->admin &&
            imp->local == export_rt->local &&
            imp->type  == export_rt->type) {
            return true;
        }
    }
    return false;
}

/*
 * Simulate BGP VPNv4 route distribution between two PEs.
 * PE-A exports a route → check if PE-B's VRF imports it.
 */
void simulate_bgp_route_distribution(PeRouter *pe_a, const char *vrf_a_name,
                                      const char *prefix_str, uint8_t plen,
                                      const char *next_hop, uint32_t vpn_label,
                                      PeRouter *pe_b) {
    printf("\n[BGP] PE-A (%s) advertising %s/%u with VPN label %u\n",
           pe_a->hostname, prefix_str, plen, vpn_label);

    Vrf *vrf_a = pe_find_vrf(pe_a, vrf_a_name);
    if (!vrf_a) {
        printf("[BGP] VRF %s not found on %s\n", vrf_a_name, pe_a->hostname);
        return;
    }

    /* For each export RT on VRF-A, check if any VRF on PE-B imports it */
    for (uint8_t et = 0; et < vrf_a->rt_export_count; et++) {
        const RouteTarget *exp_rt = &vrf_a->rt_export[et];
        printf("[BGP] Checking export RT %u:%u\n", exp_rt->admin, exp_rt->local);

        for (uint8_t v = 0; v < pe_b->vrf_count; v++) {
            Vrf *vrf_b = &pe_b->vrfs[v];
            if (rt_matches(vrf_b, exp_rt)) {
                printf("[BGP] RT match! Importing into VRF '%s' on %s\n",
                       vrf_b->name, pe_b->hostname);
                vrf_add_route(vrf_b, prefix_str, plen, next_hop,
                              "mpls0", vpn_label, 100);
            }
        }
    }
}

/* ─────────────────────────────────────────────────────────────────────── */
/* PACKET FORWARDING SIMULATION                                              */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Simulate forwarding a customer packet through a PE router.
 * Determines VRF, performs LPM, returns MPLS labels to push.
 */
void pe_forward_packet(const PeRouter *pe, const char *vrf_name,
                        const char *dest_str,
                        uint32_t *out_vpn_label,
                        uint32_t *out_transport_label) {
    uint32_t dest = str_to_ip(dest_str);

    /* Find the VRF for this packet's ingress interface */
    Vrf *vrf = NULL;
    for (uint8_t i = 0; i < pe->vrf_count; i++) {
        if (strcmp(pe->vrfs[i].name, vrf_name) == 0) {
            vrf = (Vrf *)&pe->vrfs[i];
            break;
        }
    }
    if (!vrf) {
        printf("[FWD] No VRF '%s' found\n", vrf_name);
        return;
    }

    /* LPM lookup in the VRF */
    const VrfRoute *r = vrf_lookup(vrf, dest);
    if (!r) {
        printf("[FWD] VRF=%s DROP: no route to %s\n", vrf_name, dest_str);
        return;
    }

    if (r->is_local) {
        printf("[FWD] VRF=%s LOCAL delivery: %s via %s\n",
               vrf_name, dest_str, r->iface);
        *out_vpn_label       = INVALID_LABEL;
        *out_transport_label = INVALID_LABEL;
    } else {
        printf("[FWD] VRF=%s MPLS forward: %s via %s\n",
               vrf_name, dest_str, ip_to_str(r->next_hop));
        printf("      VPN label=%u  interface=%s\n",
               r->mpls_label, r->iface);
        *out_vpn_label       = r->mpls_label;
        /* Transport label would be resolved via LDP/LFIB lookup */
        *out_transport_label = 500; /* simplified: assume 500 */
    }
}

/* ─────────────────────────────────────────────────────────────────────── */
/* DISPLAY FUNCTIONS                                                          */
/* ─────────────────────────────────────────────────────────────────────── */

void vrf_print(const Vrf *vrf) {
    printf("\n╔══════════════════════════════════════════════════╗\n");
    printf("║  VRF: %-42s ║\n", vrf->name);
    printf("║  RD:  %-42u ║\n", vrf->rd.local);
    printf("╠══════════════════════════════════════════════════╣\n");
    printf("║  Routes (%u):                                    ║\n",
           vrf->route_count);
    printf("╠══════════════╦═════════════╦═══════════╦════════╣\n");
    printf("║ Prefix       ║ Next Hop    ║ Interface ║ Label  ║\n");
    printf("╠══════════════╬═════════════╬═══════════╬════════╣\n");

    for (uint32_t i = 0; i < vrf->route_count; i++) {
        const VrfRoute *r = &vrf->routes[i];
        char prefix_buf[32];
        snprintf(prefix_buf, sizeof(prefix_buf), "%s/%u",
                 ip_to_str(r->prefix), r->prefix_len);

        printf("║ %-12s ║ %-11s ║ %-9s ║ %-6u ║\n",
               prefix_buf,
               r->is_local ? "direct" : ip_to_str(r->next_hop),
               r->iface,
               r->mpls_label);
    }
    printf("╚══════════════╩═════════════╩═══════════╩════════╝\n");
}

void pe_print(const PeRouter *pe) {
    printf("\n════════════════════════════════════════════════════\n");
    printf("  PE Router: %s  (VRFs: %u)\n", pe->hostname, pe->vrf_count);
    printf("════════════════════════════════════════════════════\n");
    for (uint8_t i = 0; i < pe->vrf_count; i++) {
        vrf_print(&pe->vrfs[i]);
    }
}

/* ─────────────────────────────────────────────────────────────────────── */
/* DEMONSTRATION MAIN                                                         */
/* ─────────────────────────────────────────────────────────────────────── */

int main(void) {
    printf("\n");
    printf("╔════════════════════════════════════════════════╗\n");
    printf("║       MPLS L3VPN — VRF Simulation (C)         ║\n");
    printf("╚════════════════════════════════════════════════╝\n\n");

    /* ── Create PE-A ── */
    PeRouter pe_a;
    pe_init(&pe_a, "PE-A");

    /* Create VRF for Customer A on PE-A */
    Vrf *vrf_a_on_pe_a = pe_create_vrf(&pe_a, "CustA",
                                        0, 65000, 100); /* RD: 65000:100 */
    assert(vrf_a_on_pe_a != NULL);
    vrf_add_rt(vrf_a_on_pe_a, true,  0, 65000, 100); /* import RT 65000:100 */
    vrf_add_rt(vrf_a_on_pe_a, false, 0, 65000, 100); /* export RT 65000:100 */

    /* Create VRF for Customer B on PE-A (different VPN, overlapping IP space) */
    Vrf *vrf_b_on_pe_a = pe_create_vrf(&pe_a, "CustB",
                                        0, 65000, 200); /* RD: 65000:200 */
    assert(vrf_b_on_pe_a != NULL);
    vrf_add_rt(vrf_b_on_pe_a, true,  0, 65000, 200);
    vrf_add_rt(vrf_b_on_pe_a, false, 0, 65000, 200);

    /* Add routes to VRF-A on PE-A */
    printf("\n[SETUP] Adding routes to VRF CustA on PE-A\n");
    /* CE-A's local network — directly connected */
    vrf_add_route(vrf_a_on_pe_a, "10.1.0.0", 24, NULL, "eth1", INVALID_LABEL, 0);
    /* Customer B site (SAME IP — different VRF — key point!) */
    /* This will be learned from PE-B via BGP */

    /* Add routes to VRF-B on PE-A — CustB also uses 10.1.0.0/24! */
    printf("\n[SETUP] Adding routes to VRF CustB on PE-A\n");
    vrf_add_route(vrf_b_on_pe_a, "10.1.0.0", 24, NULL, "eth2", INVALID_LABEL, 0);

    /* ── Create PE-B ── */
    PeRouter pe_b;
    pe_init(&pe_b, "PE-B");

    Vrf *vrf_a_on_pe_b = pe_create_vrf(&pe_b, "CustA", 0, 65000, 101);
    assert(vrf_a_on_pe_b != NULL);
    vrf_add_rt(vrf_a_on_pe_b, true,  0, 65000, 100);
    vrf_add_rt(vrf_a_on_pe_b, false, 0, 65000, 100);
    /* CE-B's network on PE-B */
    vrf_add_route(vrf_a_on_pe_b, "10.2.0.0", 24, NULL, "eth1", INVALID_LABEL, 0);

    Vrf *vrf_b_on_pe_b = pe_create_vrf(&pe_b, "CustB", 0, 65000, 201);
    assert(vrf_b_on_pe_b != NULL);
    vrf_add_rt(vrf_b_on_pe_b, true,  0, 65000, 200);
    vrf_add_rt(vrf_b_on_pe_b, false, 0, 65000, 200);
    vrf_add_route(vrf_b_on_pe_b, "10.2.0.0", 24, NULL, "eth2", INVALID_LABEL, 0);

    /* ── BGP Route Distribution Simulation ── */
    printf("\n═══════════════════════════════════════════════════\n");
    printf("  BGP MP-BGP VPNv4 Route Distribution\n");
    printf("═══════════════════════════════════════════════════\n");

    /*
     * PE-B advertises 10.2.0.0/24 with VPN label 200 (for CustA)
     * to PE-A. PE-A checks RT, installs in matching VRF.
     */
    simulate_bgp_route_distribution(
        &pe_b, "CustA",       /* source: PE-B's CustA VRF */
        "10.2.0.0", 24,       /* the prefix being advertised */
        "10.0.0.2",           /* next-hop = PE-B's loopback */
        200,                  /* VPN label allocated by PE-B */
        &pe_a                 /* destination PE */
    );

    /* PE-A advertises 10.1.0.0/24 back to PE-B */
    simulate_bgp_route_distribution(
        &pe_a, "CustA",
        "10.1.0.0", 24,
        "10.0.0.1",
        100,
        &pe_b
    );

    /* ── Print final routing tables ── */
    pe_print(&pe_a);
    pe_print(&pe_b);

    /* ── Packet Forwarding Simulation ── */
    printf("\n═══════════════════════════════════════════════════\n");
    printf("  Packet Forwarding Simulation\n");
    printf("═══════════════════════════════════════════════════\n");

    uint32_t vpn_label = 0, transport_label = 0;

    printf("\nTest 1: CustA packet 10.1.0.50 → 10.2.0.50\n");
    pe_forward_packet(&pe_a, "CustA", "10.2.0.50", &vpn_label, &transport_label);
    if (vpn_label != INVALID_LABEL) {
        printf("      → Push VPN label %u (inner), Transport label %u (outer)\n",
               vpn_label, transport_label);
    }

    printf("\nTest 2: CustB packet 10.1.0.100 → 10.2.0.100 (same IP space, different VPN)\n");
    pe_forward_packet(&pe_a, "CustB", "10.2.0.100", &vpn_label, &transport_label);

    printf("\nTest 3: Local delivery in CustA\n");
    pe_forward_packet(&pe_a, "CustA", "10.1.0.100", &vpn_label, &transport_label);

    printf("\nTest 4: Unknown destination (should be dropped)\n");
    pe_forward_packet(&pe_a, "CustA", "192.168.99.1", &vpn_label, &transport_label);

    printf("\n[DONE] VRF isolation verified: CustA and CustB "
           "use overlapping IPs with zero route leakage.\n\n");
    return 0;
}
```

---

## 28. IPSec ESP Packet Processing in C

```c
/*
 * ipvpn_ipsec.c — IPSec ESP Tunnel Mode Implementation
 *
 * Implements:
 *   • ESP packet encapsulation (encrypt + authenticate)
 *   • ESP packet decapsulation (verify + decrypt)
 *   • SA management (SAD, SPD lookup)
 *   • Sequence number and anti-replay window
 *
 * NOTE: Uses OpenSSL for AES-256-CBC and HMAC-SHA256.
 *       Compile: gcc -o ipsec ipvpn_ipsec.c -lssl -lcrypto -O2
 *
 * Standard: C11
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <stdbool.h>
#include <time.h>
#include <arpa/inet.h>
#include <openssl/evp.h>
#include <openssl/hmac.h>
#include <openssl/rand.h>

/* ─────────────────────────────────────────────────────────────────────── */
/* CONSTANTS                                                                  */
/* ─────────────────────────────────────────────────────────────────────── */

#define AES_KEY_SIZE       32    /* AES-256 = 32 bytes */
#define AES_BLOCK_SIZE     16    /* AES block = 16 bytes */
#define AES_IV_SIZE        16    /* CBC IV = 16 bytes */
#define HMAC_SHA256_SIZE   32    /* HMAC-SHA256 output = 32 bytes */
#define ICV_SIZE           16    /* We truncate HMAC to 128 bits (16 bytes) */
#define AUTH_KEY_SIZE      32    /* HMAC-SHA256 key = 32 bytes */
#define MAX_PACKET_SIZE    65535
#define ANTI_REPLAY_WINDOW 64    /* window size in packets */

/* ESP Header: 8 bytes (SPI 4B + Seq 4B) */
#define ESP_HEADER_SIZE    8

/* IP protocol numbers */
#define IPPROTO_ESP        50
#define IPPROTO_IPV4       4

/* SA states */
#define SA_STATE_ACTIVE    1
#define SA_STATE_EXPIRED   2

/* ─────────────────────────────────────────────────────────────────────── */
/* DATA STRUCTURES                                                           */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Simplified IPv4 header (20 bytes, no options)
 */
typedef struct __attribute__((packed)) {
    uint8_t  ihl_version;   /* version (4 bits) + IHL (4 bits) */
    uint8_t  tos;
    uint16_t total_len;     /* total length (network byte order) */
    uint16_t id;
    uint16_t frag_off;
    uint8_t  ttl;
    uint8_t  protocol;      /* next protocol (50=ESP, 4=IPv4 inner) */
    uint16_t checksum;
    uint32_t src;           /* source IP (network byte order) */
    uint32_t dst;           /* destination IP (network byte order) */
} IpHeader;

/*
 * ESP Header (8 bytes)
 */
typedef struct __attribute__((packed)) {
    uint32_t spi;           /* Security Parameter Index */
    uint32_t seq;           /* Sequence number */
} EspHeader;

/*
 * ESP Trailer (appended inside encrypted payload)
 * Appears AFTER padded payload.
 */
typedef struct __attribute__((packed)) {
    uint8_t  pad_len;       /* number of padding bytes */
    uint8_t  next_header;   /* protocol of encapsulated payload (4=IPv4) */
} EspTrailer;

/*
 * Security Association (one direction of IPSec connection).
 * Stores everything needed to process ESP packets.
 */
typedef struct {
    uint32_t spi;                          /* identifies this SA */
    uint32_t src_ip;                       /* tunnel source (network order) */
    uint32_t dst_ip;                       /* tunnel destination (network order) */
    uint8_t  enc_key[AES_KEY_SIZE];        /* AES-256 encryption key */
    uint8_t  auth_key[AUTH_KEY_SIZE];      /* HMAC-SHA256 key */
    uint32_t seq_num;                      /* current sequence number (outbound) */
    uint32_t recv_seq;                     /* highest sequence number received (inbound) */
    uint64_t replay_window;                /* 64-bit sliding window bitmask */
    int      state;                        /* SA_STATE_ACTIVE or expired */
    uint64_t bytes_processed;             /* for SA lifetime tracking */
    uint64_t lifetime_bytes;              /* SA expires after this many bytes */
} SecurityAssociation;

/*
 * Security Policy entry — defines what traffic gets IPSec treatment.
 */
typedef struct {
    uint32_t src_net;                      /* source network (host order) */
    uint8_t  src_plen;                     /* source prefix length */
    uint32_t dst_net;
    uint8_t  dst_plen;
    enum { SP_PROTECT, SP_BYPASS, SP_DISCARD } action;
    uint32_t sa_spi;                       /* SPI of SA to use (for PROTECT) */
} SecurityPolicy;

/* ─────────────────────────────────────────────────────────────────────── */
/* ANTI-REPLAY WINDOW                                                        */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Anti-replay window (64-bit sliding window).
 *
 * Mental model:
 *   We maintain a 64-bit bitmap representing the last 64 received seq nums.
 *   recv_seq = highest sequence number received so far.
 *   replay_window bit N = 1 means (recv_seq - N) was received.
 *   Bit 0 = recv_seq itself.
 *
 * Returns true if packet should be ACCEPTED, false if REPLAYED.
 */
static bool anti_replay_check(SecurityAssociation *sa, uint32_t seq) {
    if (seq == 0) return false; /* seq 0 not allowed */

    if (seq > sa->recv_seq) {
        /* New sequence number ahead of window — always accept */
        uint32_t diff = seq - sa->recv_seq;
        if (diff < 64) {
            /* Shift window forward */
            sa->replay_window <<= diff;
        } else {
            /* Large jump — reset window */
            sa->replay_window = 0;
        }
        sa->replay_window |= 1ULL; /* mark current seq as received */
        sa->recv_seq = seq;
        return true;
    }

    if (sa->recv_seq >= seq) {
        uint32_t diff = sa->recv_seq - seq;
        if (diff >= 64) {
            /* Outside window — too old — REPLAY */
            return false;
        }
        uint64_t bit = 1ULL << diff;
        if (sa->replay_window & bit) {
            /* Already received — REPLAY */
            return false;
        }
        /* Within window, not seen before — accept */
        sa->replay_window |= bit;
        return true;
    }
    return true;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* HMAC-SHA256 COMPUTATION                                                   */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * Compute HMAC-SHA256 over data, write first ICV_SIZE bytes to icv.
 * Returns 0 on success, -1 on failure.
 */
static int compute_icv(const uint8_t *auth_key, size_t key_len,
                        const uint8_t *data, size_t data_len,
                        uint8_t *icv) {
    uint8_t hmac_out[HMAC_SHA256_SIZE];
    unsigned int hmac_len = 0;

    uint8_t *result = HMAC(EVP_sha256(), auth_key, (int)key_len,
                            data, data_len, hmac_out, &hmac_len);
    if (!result) return -1;

    /* Truncate to ICV_SIZE (128 bits = 16 bytes) */
    memcpy(icv, hmac_out, ICV_SIZE);
    return 0;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* AES-256-CBC ENCRYPT / DECRYPT                                             */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * AES-256-CBC encryption.
 * out_len receives the ciphertext length (always multiple of AES_BLOCK_SIZE).
 * Returns 0 on success, -1 on failure.
 */
static int aes256_cbc_encrypt(const uint8_t *key, const uint8_t *iv,
                               const uint8_t *plaintext, int pt_len,
                               uint8_t *ciphertext, int *ct_len) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;

    int len = 0, total = 0;
    if (EVP_EncryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) goto err;
    EVP_CIPHER_CTX_set_padding(ctx, 0); /* We handle padding ourselves */
    if (EVP_EncryptUpdate(ctx, ciphertext, &len, plaintext, pt_len) != 1) goto err;
    total += len;
    if (EVP_EncryptFinal_ex(ctx, ciphertext + total, &len) != 1) goto err;
    total += len;
    *ct_len = total;
    EVP_CIPHER_CTX_free(ctx);
    return 0;

err:
    EVP_CIPHER_CTX_free(ctx);
    return -1;
}

/*
 * AES-256-CBC decryption.
 */
static int aes256_cbc_decrypt(const uint8_t *key, const uint8_t *iv,
                               const uint8_t *ciphertext, int ct_len,
                               uint8_t *plaintext, int *pt_len) {
    EVP_CIPHER_CTX *ctx = EVP_CIPHER_CTX_new();
    if (!ctx) return -1;

    int len = 0, total = 0;
    if (EVP_DecryptInit_ex(ctx, EVP_aes_256_cbc(), NULL, key, iv) != 1) goto err;
    EVP_CIPHER_CTX_set_padding(ctx, 0);
    if (EVP_DecryptUpdate(ctx, plaintext, &len, ciphertext, ct_len) != 1) goto err;
    total += len;
    if (EVP_DecryptFinal_ex(ctx, plaintext + total, &len) != 1) goto err;
    total += len;
    *pt_len = total;
    EVP_CIPHER_CTX_free(ctx);
    return 0;

err:
    EVP_CIPHER_CTX_free(ctx);
    return -1;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* CHECKSUM HELPERS                                                           */
/* ─────────────────────────────────────────────────────────────────────── */

static uint16_t ip_checksum(const void *data, size_t len) {
    const uint16_t *p = (const uint16_t *)data;
    uint32_t sum = 0;
    while (len > 1) { sum += *p++; len -= 2; }
    if (len == 1) sum += *(uint8_t *)p;
    while (sum >> 16) sum = (sum & 0xFFFF) + (sum >> 16);
    return (uint16_t)~sum;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* ESP ENCAPSULATION (Tunnel Mode)                                            */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * esp_encapsulate_tunnel: Wrap inner_pkt in an ESP tunnel packet.
 *
 * Input:
 *   sa         — outbound Security Association
 *   inner_pkt  — original IP packet (complete, with IP header)
 *   inner_len  — length of inner_pkt
 *   outer_src  — outer tunnel source IP (network order) = local gateway IP
 *   outer_dst  — outer tunnel dest  IP (network order) = remote gateway IP
 *   out_buf    — output buffer for ESP packet
 *   out_maxlen — max size of output buffer
 *
 * Output:
 *   out_buf filled with complete ESP tunnel packet.
 *   Returns actual output length, or -1 on error.
 *
 * PACKET LAYOUT:
 *   [Outer IP][ESP Hdr][IV][Encrypted(Inner IP + Payload + Padding + Trailer)][ICV]
 */
int esp_encapsulate_tunnel(SecurityAssociation *sa,
                            const uint8_t *inner_pkt, int inner_len,
                            uint32_t outer_src, uint32_t outer_dst,
                            uint8_t *out_buf, int out_maxlen) {
    /*
     * Step 1: Compute required padding.
     * The payload to encrypt = inner_pkt + ESP trailer (2 bytes).
     * Total must be multiple of AES_BLOCK_SIZE.
     */
    int payload_len = inner_len + sizeof(EspTrailer);
    int pad_len     = 0;
    if (payload_len % AES_BLOCK_SIZE != 0) {
        pad_len = AES_BLOCK_SIZE - (payload_len % AES_BLOCK_SIZE);
    }
    int padded_len = payload_len + pad_len; /* must be multiple of AES_BLOCK_SIZE */

    /*
     * Step 2: Build plaintext buffer to encrypt.
     * [inner_pkt][padding bytes: 0x01,0x02,...][pad_len][next_header=IPPROTO_IPV4]
     */
    uint8_t plaintext[MAX_PACKET_SIZE];
    int     pt_offset = 0;

    memcpy(plaintext + pt_offset, inner_pkt, inner_len);
    pt_offset += inner_len;

    /* Padding: bytes 0x01, 0x02, ... 0x{pad_len} (RFC 4303 §2.4) */
    for (int i = 1; i <= pad_len; i++) {
        plaintext[pt_offset++] = (uint8_t)i;
    }

    /* ESP trailer */
    EspTrailer trailer = {
        .pad_len     = (uint8_t)pad_len,
        .next_header = IPPROTO_IPV4,
    };
    memcpy(plaintext + pt_offset, &trailer, sizeof(trailer));
    pt_offset += sizeof(trailer);

    /* pt_offset must equal padded_len */
    if (pt_offset != padded_len) {
        fprintf(stderr, "[ESP] Padding calculation error\n");
        return -1;
    }

    /*
     * Step 3: Generate random IV.
     */
    uint8_t iv[AES_IV_SIZE];
    if (RAND_bytes(iv, AES_IV_SIZE) != 1) {
        fprintf(stderr, "[ESP] RAND_bytes failed\n");
        return -1;
    }

    /*
     * Step 4: Increment sequence number.
     */
    sa->seq_num++;
    if (sa->seq_num == 0) {
        /* Sequence number wrapped — SA MUST be rekeyed before this */
        fprintf(stderr, "[ESP] CRITICAL: Sequence number overflow — SA must be rekeyed!\n");
        sa->state = SA_STATE_EXPIRED;
        return -1;
    }

    /*
     * Step 5: Encrypt the plaintext.
     */
    uint8_t ciphertext[MAX_PACKET_SIZE];
    int     ct_len = 0;
    if (aes256_cbc_encrypt(sa->enc_key, iv, plaintext, padded_len,
                            ciphertext, &ct_len) != 0) {
        fprintf(stderr, "[ESP] Encryption failed\n");
        return -1;
    }

    /*
     * Step 6: Build the output packet in out_buf.
     * [Outer IP Hdr 20B][ESP Hdr 8B][IV 16B][Ciphertext][ICV 16B]
     */
    int total_len = sizeof(IpHeader) + sizeof(EspHeader) +
                    AES_IV_SIZE + ct_len + ICV_SIZE;
    if (total_len > out_maxlen) {
        fprintf(stderr, "[ESP] Output buffer too small (%d > %d)\n",
                total_len, out_maxlen);
        return -1;
    }

    int offset = 0;

    /* Outer IP header */
    IpHeader *outer_ip = (IpHeader *)(out_buf + offset);
    memset(outer_ip, 0, sizeof(*outer_ip));
    outer_ip->ihl_version = 0x45; /* IPv4, IHL=5 (20 bytes) */
    outer_ip->ttl         = 64;
    outer_ip->protocol    = IPPROTO_ESP;
    outer_ip->src         = outer_src;
    outer_ip->dst         = outer_dst;
    outer_ip->total_len   = htons((uint16_t)total_len);
    outer_ip->checksum    = ip_checksum(outer_ip, sizeof(IpHeader));
    offset += sizeof(IpHeader);

    /* ESP header */
    EspHeader *esp = (EspHeader *)(out_buf + offset);
    esp->spi = htonl(sa->spi);
    esp->seq = htonl(sa->seq_num);
    offset += sizeof(EspHeader);

    /* IV */
    memcpy(out_buf + offset, iv, AES_IV_SIZE);
    offset += AES_IV_SIZE;

    /* Ciphertext */
    memcpy(out_buf + offset, ciphertext, ct_len);
    offset += ct_len;

    /*
     * Step 7: Compute ICV over [ESP Header + IV + Ciphertext].
     * ICV is computed over everything from ESP header to end of ciphertext.
     * (NOT including outer IP header)
     */
    const uint8_t *auth_start = out_buf + sizeof(IpHeader);
    size_t         auth_len   = sizeof(EspHeader) + AES_IV_SIZE + ct_len;
    uint8_t        icv[ICV_SIZE];

    if (compute_icv(sa->auth_key, AUTH_KEY_SIZE,
                    auth_start, auth_len, icv) != 0) {
        fprintf(stderr, "[ESP] ICV computation failed\n");
        return -1;
    }

    /* Append ICV */
    memcpy(out_buf + offset, icv, ICV_SIZE);
    offset += ICV_SIZE;

    sa->bytes_processed += (uint64_t)inner_len;

    printf("[ESP] Encapsulated: inner=%dB → outer ESP=%dB  SPI=%u  Seq=%u\n",
           inner_len, total_len, sa->spi, sa->seq_num);

    return offset;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* ESP DECAPSULATION (Tunnel Mode)                                            */
/* ─────────────────────────────────────────────────────────────────────── */

/*
 * esp_decapsulate_tunnel: Verify and decrypt an incoming ESP packet.
 *
 * Returns length of inner (decrypted) packet on success, -1 on error.
 * inner_buf must be large enough to hold the original IP packet.
 */
int esp_decapsulate_tunnel(SecurityAssociation *sa,
                            const uint8_t *esp_pkt, int esp_len,
                            uint8_t *inner_buf, int inner_maxlen) {
    /*
     * Minimum ESP packet length:
     *   Outer IP (20) + ESP Hdr (8) + IV (16) + min 1 block (16) +
     *   Trailer (2) + ICV (16) = 78 bytes minimum
     */
    int min_len = (int)(sizeof(IpHeader) + sizeof(EspHeader) +
                         AES_IV_SIZE + AES_BLOCK_SIZE + ICV_SIZE);
    if (esp_len < min_len) {
        fprintf(stderr, "[ESP] Packet too short: %d < %d\n", esp_len, min_len);
        return -1;
    }

    /* Parse outer IP header */
    const IpHeader *outer_ip = (const IpHeader *)esp_pkt;
    if ((outer_ip->ihl_version >> 4) != 4) {
        fprintf(stderr, "[ESP] Not an IPv4 packet\n");
        return -1;
    }
    if (outer_ip->protocol != IPPROTO_ESP) {
        fprintf(stderr, "[ESP] Not an ESP packet (proto=%u)\n", outer_ip->protocol);
        return -1;
    }

    int ip_hdr_len = (outer_ip->ihl_version & 0x0F) * 4;
    const uint8_t *esp_start = esp_pkt + ip_hdr_len;

    /* Parse ESP header */
    const EspHeader *esp = (const EspHeader *)esp_start;
    uint32_t spi = ntohl(esp->spi);
    uint32_t seq = ntohl(esp->seq);

    /* Verify SPI matches our SA */
    if (spi != sa->spi) {
        fprintf(stderr, "[ESP] SPI mismatch: got %u, expected %u\n", spi, sa->spi);
        return -1;
    }

    /* Anti-replay check */
    if (!anti_replay_check(sa, seq)) {
        fprintf(stderr, "[ESP] Anti-replay check failed: seq=%u\n", seq);
        return -1;
    }

    /*
     * Layout of esp_start:
     *   [ESP Hdr 8B][IV 16B][Ciphertext ...][ICV 16B]
     */
    const uint8_t *iv         = esp_start + sizeof(EspHeader);
    const uint8_t *ciphertext = iv + AES_IV_SIZE;
    int            ct_len     = esp_len - ip_hdr_len -
                                 (int)sizeof(EspHeader) - AES_IV_SIZE - ICV_SIZE;
    const uint8_t *received_icv = ciphertext + ct_len;

    if (ct_len <= 0 || ct_len % AES_BLOCK_SIZE != 0) {
        fprintf(stderr, "[ESP] Invalid ciphertext length: %d\n", ct_len);
        return -1;
    }

    /*
     * Step 1: Verify ICV (integrity check).
     * MUST check ICV BEFORE attempting decryption (RFC 4303 §3.4.4).
     * "Authenticate then decrypt" — fail fast on tampering.
     */
    size_t  auth_len   = sizeof(EspHeader) + AES_IV_SIZE + ct_len;
    uint8_t computed_icv[ICV_SIZE];
    if (compute_icv(sa->auth_key, AUTH_KEY_SIZE,
                    esp_start, auth_len, computed_icv) != 0) {
        fprintf(stderr, "[ESP] ICV computation failed\n");
        return -1;
    }

    /* Constant-time comparison to prevent timing attacks */
    uint8_t diff = 0;
    for (int i = 0; i < ICV_SIZE; i++) {
        diff |= computed_icv[i] ^ received_icv[i];
    }
    if (diff != 0) {
        fprintf(stderr, "[ESP] ICV verification FAILED — packet tampered or wrong key\n");
        return -1;
    }
    printf("[ESP] ICV verified ✓\n");

    /*
     * Step 2: Decrypt ciphertext.
     */
    uint8_t plaintext[MAX_PACKET_SIZE];
    int     pt_len = 0;
    if (aes256_cbc_decrypt(sa->enc_key, iv, ciphertext, ct_len,
                            plaintext, &pt_len) != 0) {
        fprintf(stderr, "[ESP] Decryption failed\n");
        return -1;
    }

    /*
     * Step 3: Parse ESP trailer (last 2 bytes of plaintext before removal).
     * [inner_pkt][padding][pad_len][next_header]
     */
    if (pt_len < 2) {
        fprintf(stderr, "[ESP] Decrypted payload too short\n");
        return -1;
    }
    uint8_t pad_len     = plaintext[pt_len - 2];
    uint8_t next_header = plaintext[pt_len - 1];

    if (next_header != IPPROTO_IPV4) {
        fprintf(stderr, "[ESP] Unexpected next header: %u\n", next_header);
        return -1;
    }

    /* Calculate inner packet length (remove padding and trailer) */
    int inner_len = pt_len - pad_len - 2;
    if (inner_len <= 0 || inner_len > inner_maxlen) {
        fprintf(stderr, "[ESP] Invalid inner packet length: %d\n", inner_len);
        return -1;
    }

    /* Copy inner packet to output buffer */
    memcpy(inner_buf, plaintext, inner_len);

    printf("[ESP] Decapsulated: outer=%dB → inner=%dB  SPI=%u  Seq=%u\n",
           esp_len, inner_len, spi, seq);
    return inner_len;
}

/* ─────────────────────────────────────────────────────────────────────── */
/* DEMONSTRATION MAIN                                                         */
/* ─────────────────────────────────────────────────────────────────────── */

/* Build a minimal IPv4/ICMP echo packet for testing */
static int build_test_packet(uint32_t src_ip, uint32_t dst_ip,
                               uint8_t *buf, int maxlen) {
    if (maxlen < (int)(sizeof(IpHeader) + 8)) return -1;

    /* ICMP echo payload (8 bytes: type+code+checksum+id+seq) */
    uint8_t icmp[8] = { 8, 0, 0, 0, 0x12, 0x34, 0, 1 };
    /* Compute ICMP checksum */
    uint16_t cs = ip_checksum(icmp, 8);
    icmp[2] = (uint8_t)(cs >> 8);
    icmp[3] = (uint8_t)(cs & 0xFF);

    IpHeader *ip = (IpHeader *)buf;
    memset(ip, 0, sizeof(*ip));
    ip->ihl_version = 0x45;
    ip->ttl         = 64;
    ip->protocol    = 1; /* ICMP */
    ip->src         = htonl(src_ip);
    ip->dst         = htonl(dst_ip);
    ip->total_len   = htons(sizeof(IpHeader) + 8);
    ip->checksum    = ip_checksum(ip, sizeof(IpHeader));

    memcpy(buf + sizeof(IpHeader), icmp, 8);
    return (int)(sizeof(IpHeader) + 8);
}

int main(void) {
    printf("\n");
    printf("╔═══════════════════════════════════════════════════╗\n");
    printf("║      IPSec ESP Tunnel Mode — C Implementation     ║\n");
    printf("╚═══════════════════════════════════════════════════╝\n\n");

    /* Create outbound SA (GW-A → GW-B) */
    SecurityAssociation sa_out = {
        .spi           = 0x1001,
        .src_ip        = 0xC6336401, /* 198.51.100.1 */
        .dst_ip        = 0xCB007101, /* 203.0.113.1 */
        .seq_num       = 0,
        .recv_seq      = 0,
        .replay_window = 0,
        .state         = SA_STATE_ACTIVE,
        .bytes_processed = 0,
        .lifetime_bytes  = (uint64_t)4 * 1024 * 1024 * 1024, /* 4 GB */
    };

    /* Use deterministic test keys (in production: derived from IKE) */
    memset(sa_out.enc_key,  0xAA, AES_KEY_SIZE);
    memset(sa_out.auth_key, 0xBB, AUTH_KEY_SIZE);

    /* Create inbound SA (mirror of outbound — same keys for this demo) */
    SecurityAssociation sa_in = sa_out;

    /* ── Build test inner packet ── */
    printf("[TEST] Building ICMP echo packet: 10.1.0.50 → 10.2.0.50\n");
    uint8_t inner_pkt[256];
    int inner_len = build_test_packet(
        0x0A010032, /* 10.1.0.50 */
        0x0A020032, /* 10.2.0.50 */
        inner_pkt, sizeof(inner_pkt));

    if (inner_len < 0) {
        fprintf(stderr, "Failed to build test packet\n");
        return 1;
    }
    printf("[TEST] Inner packet: %d bytes\n", inner_len);

    /* Print inner packet hex */
    printf("[TEST] Inner packet (hex):\n  ");
    for (int i = 0; i < inner_len; i++) {
        printf("%02X ", inner_pkt[i]);
        if ((i + 1) % 16 == 0) printf("\n  ");
    }
    printf("\n\n");

    /* ── Encapsulate (GW-A's outbound processing) ── */
    printf("══════════════════════════════════════════════\n");
    printf(" ENCAPSULATION (GW-A sends to GW-B)\n");
    printf("══════════════════════════════════════════════\n");

    uint8_t esp_pkt[MAX_PACKET_SIZE];
    int esp_len = esp_encapsulate_tunnel(
        &sa_out,
        inner_pkt, inner_len,
        sa_out.src_ip, sa_out.dst_ip,  /* tunnel src/dst (network order) */
        esp_pkt, sizeof(esp_pkt));

    if (esp_len < 0) {
        fprintf(stderr, "Encapsulation failed\n");
        return 1;
    }

    printf("[ESP] Output packet: %d bytes  (overhead: %d bytes)\n\n",
           esp_len, esp_len - inner_len);

    /* Print first 48 bytes of ESP packet */
    printf("[ESP] ESP packet header (first 48B):\n  ");
    for (int i = 0; i < 48 && i < esp_len; i++) {
        printf("%02X ", esp_pkt[i]);
        if ((i + 1) % 16 == 0) printf("\n  ");
    }
    printf("...\n\n");

    /* ── Decapsulate (GW-B's inbound processing) ── */
    printf("══════════════════════════════════════════════\n");
    printf(" DECAPSULATION (GW-B receives from GW-A)\n");
    printf("══════════════════════════════════════════════\n");

    uint8_t recovered_pkt[MAX_PACKET_SIZE];
    int recovered_len = esp_decapsulate_tunnel(
        &sa_in,
        esp_pkt, esp_len,
        recovered_pkt, sizeof(recovered_pkt));

    if (recovered_len < 0) {
        fprintf(stderr, "Decapsulation failed\n");
        return 1;
    }

    /* ── Verify correctness ── */
    printf("\n══════════════════════════════════════════════\n");
    printf(" VERIFICATION\n");
    printf("══════════════════════════════════════════════\n");

    if (recovered_len == inner_len &&
        memcmp(recovered_pkt, inner_pkt, inner_len) == 0) {
        printf("[✓] PASS: Inner packet perfectly recovered (%d bytes)\n",
               recovered_len);
    } else {
        printf("[✗] FAIL: Packet mismatch!\n");
        return 1;
    }

    /* ── Test anti-replay ── */
    printf("\n[TEST] Anti-replay: replaying same packet (seq=1)\n");
    uint8_t replay_buf[MAX_PACKET_SIZE];
    recovered_len = esp_decapsulate_tunnel(
        &sa_in, esp_pkt, esp_len, replay_buf, sizeof(replay_buf));
    if (recovered_len < 0) {
        printf("[✓] PASS: Replay correctly rejected\n");
    } else {
        printf("[✗] FAIL: Replay should have been rejected!\n");
    }

    /* ── Test ICV tampering ── */
    printf("\n[TEST] Tampering: flipping bit in ciphertext\n");
    uint8_t tampered[MAX_PACKET_SIZE];
    memcpy(tampered, esp_pkt, esp_len);
    /* Corrupt one byte in the encrypted payload area */
    tampered[sizeof(IpHeader) + sizeof(EspHeader) + AES_IV_SIZE + 4] ^= 0xFF;

    /* Reset anti-replay window for fresh test */
    sa_in.recv_seq      = 0;
    sa_in.replay_window = 0;

    recovered_len = esp_decapsulate_tunnel(
        &sa_in, tampered, esp_len, replay_buf, sizeof(replay_buf));
    if (recovered_len < 0) {
        printf("[✓] PASS: Tampered packet correctly rejected (ICV mismatch)\n");
    } else {
        printf("[✗] FAIL: Tampered packet should have been rejected!\n");
    }

    printf("\n[DONE] IPSec ESP simulation complete.\n\n");
    return 0;
}
```

---

# PART IX — RUST IMPLEMENTATION

---

## 29. VRF and MPLS Label Stack in Rust

```rust
// ipvpn_vrf.rs — MPLS L3VPN VRF + Label Stack Simulation in Rust
//
// Demonstrates:
//   • VRF struct with isolated routing tables
//   • Route Distinguisher and Route Target types
//   • Longest Prefix Match (LPM)
//   • MPLS label stack operations (Push, Swap, Pop)
//   • BGP VPNv4 route distribution logic
//
// Run: rustc ipvpn_vrf.rs -o ipvpn_vrf && ./ipvpn_vrf

use std::collections::HashMap;
use std::fmt;
use std::net::Ipv4Addr;

// ─────────────────────────────────────────────────────────────────────────── //
// CONSTANTS                                                                    //
// ─────────────────────────────────────────────────────────────────────────── //

const IMPLICIT_NULL_LABEL: u32 = 3;   // RFC 3032 reserved: signal PHP
const IPV4_EXPLICIT_NULL:  u32 = 0;   // RFC 3032 reserved: IPv4 explicit null
const MAX_LABEL_VALUE:     u32 = 1_048_575; // 20-bit max

// ─────────────────────────────────────────────────────────────────────────── //
// MPLS LABEL                                                                   //
// ─────────────────────────────────────────────────────────────────────────── //

/// A single MPLS label entry (32-bit wire format).
///
/// Layout:
///  [Label: 20 bits][TC/EXP: 3 bits][S (bottom-of-stack): 1 bit][TTL: 8 bits]
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct MplsLabel {
    pub label: u32,    // 20-bit label value
    pub tc:    u8,     // Traffic Class (QoS), 3 bits
    pub bos:   bool,   // Bottom of Stack flag
    pub ttl:   u8,     // Time To Live
}

impl MplsLabel {
    pub fn new(label: u32, tc: u8, bos: bool, ttl: u8) -> Self {
        assert!(label <= MAX_LABEL_VALUE, "Label value exceeds 20 bits");
        assert!(tc <= 7, "TC/EXP field exceeds 3 bits");
        MplsLabel { label, tc, bos, ttl }
    }

    /// Encode to 32-bit wire format (big-endian).
    pub fn to_wire(&self) -> u32 {
        (self.label << 12)
            | ((self.tc as u32) << 9)
            | ((self.bos as u32) << 8)
            | (self.ttl as u32)
    }

    /// Decode from 32-bit wire format.
    pub fn from_wire(raw: u32) -> Self {
        MplsLabel {
            label: (raw >> 12) & 0x000F_FFFF,
            tc:    ((raw >> 9) & 0x7) as u8,
            bos:   ((raw >> 8) & 0x1) != 0,
            ttl:   (raw & 0xFF) as u8,
        }
    }
}

impl fmt::Display for MplsLabel {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "Label={} TC={} S={} TTL={}",
               self.label, self.tc, self.bos as u8, self.ttl)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// MPLS LABEL STACK                                                             //
// ─────────────────────────────────────────────────────────────────────────── //

/// MPLS Label Stack — a stack of MPLS labels on a packet.
/// Index 0 = top of stack (outermost, processed first by routers).
/// Last element has bos=true (bottom of stack).
#[derive(Clone, Debug)]
pub struct LabelStack {
    labels: Vec<MplsLabel>,
}

impl LabelStack {
    pub fn empty() -> Self {
        LabelStack { labels: Vec::new() }
    }

    pub fn is_empty(&self) -> bool {
        self.labels.is_empty()
    }

    /// Push a new label onto the TOP of the stack.
    /// Previous top label's BOS becomes false.
    pub fn push(&mut self, label: u32, tc: u8, ttl: u8) {
        // Clear BOS on previous top (now it's no longer bottom)
        // Actually BOS is set on the BOTTOM, not the top.
        // When pushing a new inner label, the existing stack is unchanged.
        // This function pushes as the NEW outer label.
        
        // All existing labels stay — new label is inserted at index 0 (top).
        // BOS of new label = false (there are labels below it).
        // If stack was empty, BOS = true.
        let bos = self.labels.is_empty();
        let new_label = MplsLabel::new(label, tc, bos, ttl);
        self.labels.insert(0, new_label);
        
        // Update BOS flags: only the last element should have bos=true
        self.recompute_bos();
    }

    /// Push a label as the INNERMOST (bottom) entry.
    /// Used when adding VPN label (which sits below transport label).
    pub fn push_inner(&mut self, label: u32, tc: u8, ttl: u8) {
        let new_label = MplsLabel::new(label, tc, true, ttl); // BOS=true
        // Clear BOS on previous bottom
        if let Some(prev) = self.labels.last_mut() {
            prev.bos = false;
        }
        self.labels.push(new_label);
        self.recompute_bos();
    }

    /// Swap the TOP label with a new label value.
    pub fn swap(&mut self, new_label: u32) -> Option<u32> {
        if let Some(top) = self.labels.first_mut() {
            let old = top.label;
            top.label = new_label;
            Some(old)
        } else {
            None
        }
    }

    /// Pop (remove) the TOP label. Returns the popped label.
    pub fn pop(&mut self) -> Option<MplsLabel> {
        if self.labels.is_empty() {
            None
        } else {
            let popped = self.labels.remove(0);
            self.recompute_bos();
            Some(popped)
        }
    }

    /// Peek at the top label without removing it.
    pub fn top(&self) -> Option<&MplsLabel> {
        self.labels.first()
    }

    /// Decrement TTL on the top label (done at each hop).
    pub fn decrement_ttl(&mut self) {
        if let Some(top) = self.labels.first_mut() {
            top.ttl = top.ttl.saturating_sub(1);
        }
    }

    /// Recompute BOS flags — only the last label has BOS=true.
    fn recompute_bos(&mut self) {
        let len = self.labels.len();
        for (i, lbl) in self.labels.iter_mut().enumerate() {
            lbl.bos = i == len - 1;
        }
    }

    /// Wire size in bytes (4 bytes per label).
    pub fn wire_size(&self) -> usize {
        self.labels.len() * 4
    }
}

impl fmt::Display for LabelStack {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "[")?;
        for (i, lbl) in self.labels.iter().enumerate() {
            if i > 0 { write!(f, " | ")?; }
            write!(f, "L:{} S:{}", lbl.label, lbl.bos as u8)?;
        }
        write!(f, "]")
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// IP PREFIX                                                                    //
// ─────────────────────────────────────────────────────────────────────────── //

/// An IPv4 prefix (network address + prefix length).
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct Ipv4Prefix {
    pub network: u32,   // network address, host byte order
    pub len:     u8,    // prefix length 0..=32
}

impl Ipv4Prefix {
    pub fn new(network: u32, len: u8) -> Self {
        assert!(len <= 32, "Prefix length must be 0–32");
        let mask = Self::mask(len);
        Ipv4Prefix { network: network & mask, len }
    }

    pub fn from_str(s: &str, len: u8) -> Self {
        let ip: Ipv4Addr = s.parse().expect("Invalid IP address");
        let n = u32::from(ip);
        Self::new(n, len)
    }

    fn mask(len: u8) -> u32 {
        if len == 0 { 0 } else { !0u32 << (32 - len) }
    }

    /// Check if 'dest' matches this prefix.
    pub fn matches(&self, dest: u32) -> bool {
        let mask = Self::mask(self.len);
        (dest & mask) == self.network
    }
}

impl fmt::Display for Ipv4Prefix {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let ip = Ipv4Addr::from(self.network);
        write!(f, "{}/{}", ip, self.len)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// ROUTE DISTINGUISHER                                                          //
// ─────────────────────────────────────────────────────────────────────────── //

/// Route Distinguisher (8 bytes).
/// Makes VPNv4 prefixes globally unique in BGP.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct RouteDistinguisher {
    pub rd_type: u8,
    pub admin:   u32,   // AS number or IP address
    pub local:   u32,   // local discriminator
}

impl RouteDistinguisher {
    pub fn new_type0(as_number: u16, local: u32) -> Self {
        RouteDistinguisher { rd_type: 0, admin: as_number as u32, local }
    }
}

impl fmt::Display for RouteDistinguisher {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{}", self.admin, self.local)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// ROUTE TARGET                                                                 //
// ─────────────────────────────────────────────────────────────────────────── //

/// Route Target (BGP Extended Community, 8 bytes).
/// Controls VPN membership — import/export policy.
#[derive(Clone, Copy, Debug, PartialEq, Eq, Hash)]
pub struct RouteTarget {
    pub admin: u32,
    pub local: u16,
}

impl RouteTarget {
    pub fn new(admin: u32, local: u16) -> Self {
        RouteTarget { admin, local }
    }
}

impl fmt::Display for RouteTarget {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}:{}", self.admin, self.local)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// ROUTE ENTRY                                                                  //
// ─────────────────────────────────────────────────────────────────────────── //

/// A routing entry — one prefix with its forwarding information.
#[derive(Clone, Debug)]
pub struct RouteEntry {
    pub prefix:      Ipv4Prefix,
    pub next_hop:    Option<u32>,       // None = directly connected
    pub interface:   String,
    pub vpn_label:   Option<u32>,       // MPLS VPN label (inner)
    pub metric:      u32,
    pub is_bgp:      bool,              // true = learned from BGP
}

impl RouteEntry {
    pub fn new_direct(prefix: Ipv4Prefix, iface: &str) -> Self {
        RouteEntry {
            prefix,
            next_hop:  None,
            interface: iface.to_string(),
            vpn_label: None,
            metric:    0,
            is_bgp:    false,
        }
    }

    pub fn new_bgp(prefix: Ipv4Prefix, next_hop: u32, iface: &str,
                   label: u32, metric: u32) -> Self {
        RouteEntry {
            prefix,
            next_hop:  Some(next_hop),
            interface: iface.to_string(),
            vpn_label: Some(label),
            metric,
            is_bgp:    true,
        }
    }
}

impl fmt::Display for RouteEntry {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        let nh = match self.next_hop {
            Some(ip) => format!("{}", Ipv4Addr::from(ip)),
            None     => "direct".to_string(),
        };
        let lbl = match self.vpn_label {
            Some(l) => format!("{}", l),
            None    => "-".to_string(),
        };
        write!(f, "{:<18} via {:<16} iface={:<8} label={}",
               self.prefix.to_string(), nh, self.interface, lbl)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// VRF — VIRTUAL ROUTING & FORWARDING                                           //
// ─────────────────────────────────────────────────────────────────────────── //

/// A VRF represents one isolated routing domain on a PE router.
#[derive(Debug)]
pub struct Vrf {
    pub name:      String,
    pub rd:        RouteDistinguisher,
    pub rt_import: Vec<RouteTarget>,
    pub rt_export: Vec<RouteTarget>,
    routes:        Vec<RouteEntry>,
}

impl Vrf {
    pub fn new(name: &str, rd: RouteDistinguisher) -> Self {
        Vrf {
            name:      name.to_string(),
            rd,
            rt_import: Vec::new(),
            rt_export: Vec::new(),
            routes:    Vec::new(),
        }
    }

    pub fn add_import_rt(&mut self, rt: RouteTarget) {
        println!("[VRF] {} import RT {}", self.name, rt);
        self.rt_import.push(rt);
    }

    pub fn add_export_rt(&mut self, rt: RouteTarget) {
        println!("[VRF] {} export RT {}", self.name, rt);
        self.rt_export.push(rt);
    }

    /// Add a route to this VRF's routing table.
    pub fn add_route(&mut self, entry: RouteEntry) {
        println!("[ROUTE] VRF={} {}", self.name, entry);
        self.routes.push(entry);
    }

    /// Longest Prefix Match lookup.
    ///
    /// Algorithm:
    ///   Iterate all routes, find the one with:
    ///     1. Matching prefix (network & mask == dest & mask)
    ///     2. Longest prefix length (most specific)
    ///     3. Lowest metric (as tiebreaker)
    ///
    /// Returns reference to the best matching RouteEntry, or None.
    pub fn lpm_lookup(&self, dest: u32) -> Option<&RouteEntry> {
        self.routes
            .iter()
            .filter(|r| r.prefix.matches(dest))
            .max_by(|a, b| {
                // Primary: longer prefix wins
                a.prefix.len.cmp(&b.prefix.len)
                    // Secondary: lower metric wins
                    .then(b.metric.cmp(&a.metric))
            })
    }

    /// Check if a given RouteTarget is in our import list.
    pub fn imports_rt(&self, rt: &RouteTarget) -> bool {
        self.rt_import.contains(rt)
    }

    pub fn print_table(&self) {
        println!("\n┌─────────────────────────────────────────────────────┐");
        println!("│  VRF: {:44}│", self.name);
        println!("│  RD:  {:44}│", self.rd.to_string());
        println!("├─────────────────────────────────────────────────────┤");
        println!("│  Routes ({:2}):                                       │",
                 self.routes.len());
        println!("├──────────────────────────────────────────────────────");
        for r in &self.routes {
            println!("│  {}", r);
        }
        println!("└─────────────────────────────────────────────────────┘");
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// LFIB — LABEL FORWARDING INFORMATION BASE                                     //
// ─────────────────────────────────────────────────────────────────────────── //

/// Action taken by a router on an incoming labeled packet.
#[derive(Clone, Debug)]
pub enum LfibAction {
    Swap { new_label: u32, out_iface: String },
    Pop  { out_iface: String },             // PHP or egress PE
    SwapAndPush { new_outer: u32, out_iface: String }, // rare
}

impl fmt::Display for LfibAction {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            LfibAction::Swap { new_label, out_iface } =>
                write!(f, "SWAP → {} via {}", new_label, out_iface),
            LfibAction::Pop { out_iface } =>
                write!(f, "POP via {}", out_iface),
            LfibAction::SwapAndPush { new_outer, out_iface } =>
                write!(f, "SWAP+PUSH → {} via {}", new_outer, out_iface),
        }
    }
}

/// LFIB entry: incoming label → action.
#[derive(Clone, Debug)]
pub struct LfibEntry {
    pub in_label: u32,
    pub action:   LfibAction,
}

/// The LFIB (Label Forwarding Information Base).
pub struct Lfib {
    entries: HashMap<u32, LfibEntry>,
}

impl Lfib {
    pub fn new() -> Self {
        Lfib { entries: HashMap::new() }
    }

    pub fn install(&mut self, in_label: u32, action: LfibAction) {
        println!("[LFIB] Install: in={} → {}", in_label, action);
        self.entries.insert(in_label, LfibEntry { in_label, action });
    }

    /// Forward a labeled packet through this router.
    /// Modifies the label stack in place, returns the output interface.
    pub fn forward(&self, stack: &mut LabelStack) -> Option<&str> {
        let top_label = stack.top()?.label;

        match self.entries.get(&top_label)? {
            LfibEntry { action: LfibAction::Swap { new_label, out_iface }, .. } => {
                stack.decrement_ttl();
                stack.swap(*new_label);
                Some(out_iface.as_str())
            }
            LfibEntry { action: LfibAction::Pop { out_iface }, .. } => {
                stack.pop(); // remove top label
                Some(out_iface.as_str())
            }
            LfibEntry { action: LfibAction::SwapAndPush { new_outer, out_iface }, .. } => {
                stack.swap(*new_outer);
                Some(out_iface.as_str())
            }
        }
    }

    pub fn print(&self) {
        println!("\n  LFIB:");
        println!("  ┌─────────────┬─────────────────────────────────┐");
        println!("  │ In-Label    │ Action                          │");
        println!("  ├─────────────┼─────────────────────────────────┤");
        let mut labels: Vec<u32> = self.entries.keys().cloned().collect();
        labels.sort();
        for lbl in labels {
            let e = &self.entries[&lbl];
            println!("  │ {:11} │ {:31} │", e.in_label, e.action.to_string());
        }
        println!("  └─────────────┴─────────────────────────────────┘");
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// PE ROUTER                                                                    //
// ─────────────────────────────────────────────────────────────────────────── //

/// A PE router: holds multiple VRFs and an LFIB.
pub struct PeRouter {
    pub hostname: String,
    pub vrfs:     Vec<Vrf>,
    pub lfib:     Lfib,
    pub loopback: u32,    // PE's loopback IP (BGP next-hop)
}

impl PeRouter {
    pub fn new(hostname: &str, loopback: &str) -> Self {
        let lo_ip: u32 = u32::from(loopback.parse::<Ipv4Addr>().unwrap());
        PeRouter {
            hostname: hostname.to_string(),
            vrfs:     Vec::new(),
            lfib:     Lfib::new(),
            loopback: lo_ip,
        }
    }

    pub fn create_vrf(&mut self, name: &str, rd: RouteDistinguisher) -> &mut Vrf {
        println!("[PE:{}] Creating VRF '{}' RD={}", self.hostname, name, rd);
        self.vrfs.push(Vrf::new(name, rd));
        self.vrfs.last_mut().unwrap()
    }

    pub fn find_vrf(&self, name: &str) -> Option<&Vrf> {
        self.vrfs.iter().find(|v| v.name == name)
    }

    pub fn find_vrf_mut(&mut self, name: &str) -> Option<&mut Vrf> {
        self.vrfs.iter_mut().find(|v| v.name == name)
    }

    /// Simulate receiving a BGP VPNv4 update and distributing into VRFs.
    pub fn receive_bgp_vpnv4(
        &mut self,
        from_pe:    &str,
        prefix:     Ipv4Prefix,
        next_hop:   u32,
        vpn_label:  u32,
        export_rts: &[RouteTarget],
        metric:     u32,
    ) {
        println!("\n[BGP:{from}→{to}] VPNv4 {prefix} label={lbl}",
                 from = from_pe,
                 to   = self.hostname,
                 prefix = prefix,
                 lbl    = vpn_label);

        // Check each VRF for RT match
        let nh_str = Ipv4Addr::from(next_hop).to_string();
        let mut matched = Vec::new();

        for (i, vrf) in self.vrfs.iter().enumerate() {
            for rt in export_rts {
                if vrf.imports_rt(rt) {
                    matched.push((i, vrf.name.clone()));
                    println!("[BGP] RT {} matched → importing into VRF '{}'",
                             rt, vrf.name);
                    break;
                }
            }
        }

        for (idx, vrf_name) in matched {
            let entry = RouteEntry::new_bgp(prefix, next_hop, "mpls0",
                                             vpn_label, metric);
            self.vrfs[idx].add_route(entry);
            let _ = vrf_name; // suppress unused warning
        }
    }

    /// Forward a customer IP packet: VRF lookup → build label stack.
    pub fn forward_ip_packet(
        &self,
        vrf_name: &str,
        dest_str: &str,
        transport_label: u32,   // obtained from LFIB for PE-B's loopback
    ) -> Option<LabelStack> {
        let dest_ip: u32 = u32::from(dest_str.parse::<Ipv4Addr>().ok()?);

        let vrf = self.find_vrf(vrf_name)?;
        let route = vrf.lpm_lookup(dest_ip)?;

        println!("[FWD:{}] VRF={} dest={} → matched {}",
                 self.hostname, vrf_name, dest_str, route);

        if let Some(vpn_label) = route.vpn_label {
            // MPLS forward: push VPN label (inner) + transport label (outer)
            let mut stack = LabelStack::empty();

            // Push VPN label first (it becomes the inner/bottom label)
            stack.push_inner(vpn_label, 0, 64);

            // Push transport label on top (outer label)
            stack.push(transport_label, 0, 64);

            println!("[FWD:{}] Push label stack: {}", self.hostname, stack);
            Some(stack)
        } else {
            // Direct delivery
            println!("[FWD:{}] Direct delivery via {}", self.hostname, route.interface);
            None
        }
    }

    pub fn print_all(&self) {
        println!("\n╔══════════════════════════════════════════════════════╗");
        println!("║  PE Router: {:40}║", self.hostname);
        println!("╚══════════════════════════════════════════════════════╝");
        for vrf in &self.vrfs {
            vrf.print_table();
        }
        self.lfib.print();
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// P ROUTER (Core — label switching only)                                       //
// ─────────────────────────────────────────────────────────────────────────── //

pub struct PRouter {
    pub hostname: String,
    pub lfib:     Lfib,
}

impl PRouter {
    pub fn new(hostname: &str) -> Self {
        PRouter { hostname: hostname.to_string(), lfib: Lfib::new() }
    }

    /// Forward labeled packet — pure MPLS switching.
    pub fn forward(&self, stack: &mut LabelStack) -> Option<&str> {
        let top = stack.top()?.label;
        println!("[P:{}] MPLS forward: top label={} stack={}",
                 self.hostname, top, stack);
        let iface = self.lfib.forward(stack);
        println!("[P:{}]   → stack after: {}", self.hostname, stack);
        iface
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// MAIN DEMONSTRATION                                                            //
// ─────────────────────────────────────────────────────────────────────────── //

fn main() {
    println!("\n╔═══════════════════════════════════════════════════════╗");
    println!("║     MPLS L3VPN — VRF + Label Stack Simulation (Rust)  ║");
    println!("╚═══════════════════════════════════════════════════════╝\n");

    // ── Create PE-A ──────────────────────────────────────────────────── //
    let mut pe_a = PeRouter::new("PE-A", "10.0.0.1");

    {
        let vrf = pe_a.create_vrf("CustA", RouteDistinguisher::new_type0(65000, 100));
        vrf.add_import_rt(RouteTarget::new(65000, 100));
        vrf.add_export_rt(RouteTarget::new(65000, 100));
        // CE-A's directly connected network
        vrf.add_route(RouteEntry::new_direct(
            Ipv4Prefix::from_str("10.1.0.0", 24), "eth1"));
    }
    {
        let vrf = pe_a.create_vrf("CustB", RouteDistinguisher::new_type0(65000, 200));
        vrf.add_import_rt(RouteTarget::new(65000, 200));
        vrf.add_export_rt(RouteTarget::new(65000, 200));
        // CustB also uses 10.1.0.0/24 — isolated in different VRF
        vrf.add_route(RouteEntry::new_direct(
            Ipv4Prefix::from_str("10.1.0.0", 24), "eth2"));
    }

    // LFIB on PE-A: transport label 500 → swap 750 toward PE-B
    pe_a.lfib.install(500, LfibAction::Swap {
        new_label: 750,
        out_iface: "eth0".to_string(),
    });

    // ── Create P1 (core router) ───────────────────────────────────────── //
    let mut p1 = PRouter::new("P1");
    p1.lfib.install(750, LfibAction::Swap {
        new_label: 900,
        out_iface: "eth1".to_string(),
    });

    // ── Create P2 (penultimate hop) ───────────────────────────────────── //
    let mut p2 = PRouter::new("P2");
    // PHP: P2 pops the transport label (implicit null from PE-B)
    p2.lfib.install(900, LfibAction::Pop {
        out_iface: "eth0".to_string(),
    });

    // ── Create PE-B ──────────────────────────────────────────────────── //
    let mut pe_b = PeRouter::new("PE-B", "10.0.0.2");

    {
        let vrf = pe_b.create_vrf("CustA", RouteDistinguisher::new_type0(65000, 101));
        vrf.add_import_rt(RouteTarget::new(65000, 100));
        vrf.add_export_rt(RouteTarget::new(65000, 100));
        vrf.add_route(RouteEntry::new_direct(
            Ipv4Prefix::from_str("10.2.0.0", 24), "eth1"));
    }
    {
        let vrf = pe_b.create_vrf("CustB", RouteDistinguisher::new_type0(65000, 201));
        vrf.add_import_rt(RouteTarget::new(65000, 200));
        vrf.add_export_rt(RouteTarget::new(65000, 200));
        vrf.add_route(RouteEntry::new_direct(
            Ipv4Prefix::from_str("10.2.0.0", 24), "eth2"));
    }

    // VPN label 200 on PE-B: incoming label 200 → pop → forward in CustA VRF
    pe_b.lfib.install(200, LfibAction::Pop { out_iface: "eth1".to_string() });
    pe_b.lfib.install(300, LfibAction::Pop { out_iface: "eth2".to_string() });

    // ── BGP Route Distribution ────────────────────────────────────────── //
    println!("\n═══════════════════════════════════════════════════");
    println!("  BGP MP-BGP VPNv4 Route Distribution");
    println!("═══════════════════════════════════════════════════");

    // PE-B advertises 10.2.0.0/24 (CustA) to PE-A with VPN label 200
    pe_a.receive_bgp_vpnv4(
        "PE-B",
        Ipv4Prefix::from_str("10.2.0.0", 24),
        u32::from("10.0.0.2".parse::<Ipv4Addr>().unwrap()), // PE-B loopback
        200,
        &[RouteTarget::new(65000, 100)],
        100,
    );

    // PE-B advertises 10.2.0.0/24 (CustB) to PE-A with VPN label 300
    pe_a.receive_bgp_vpnv4(
        "PE-B",
        Ipv4Prefix::from_str("10.2.0.0", 24),
        u32::from("10.0.0.2".parse::<Ipv4Addr>().unwrap()),
        300,
        &[RouteTarget::new(65000, 200)],
        100,
    );

    // ── Print routing tables ──────────────────────────────────────────── //
    pe_a.print_all();
    pe_b.print_all();

    // ── Simulate end-to-end packet forwarding ────────────────────────── //
    println!("\n═══════════════════════════════════════════════════");
    println!("  Packet Forwarding Simulation");
    println!("═══════════════════════════════════════════════════");

    println!("\nTest 1: CustA packet 10.1.0.50 → 10.2.0.50");
    if let Some(mut stack) = pe_a.forward_ip_packet("CustA", "10.2.0.50", 500) {
        println!("[SIM] PE-A emits: stack={}", stack);

        // Simulate P1 processing
        let _ = p1.forward(&mut stack);
        println!("[SIM] After P1: stack={}", stack);

        // Simulate P2 PHP
        let _ = p2.forward(&mut stack);
        println!("[SIM] After P2 (PHP): stack={}", stack);

        // PE-B: pop VPN label, do VRF lookup
        if let Some(top) = stack.top() {
            println!("[SIM] PE-B: VPN label={} → pop → forward to CE-B", top.label);
            stack.pop();
        }
        println!("[SIM] PE-B: remaining stack={} → IP delivery", stack);
        println!("[SIM] Packet delivered to Host-B (10.2.0.50) ✓");
    }

    println!("\nTest 2: CustB packet 10.1.0.100 → 10.2.0.100 (same IP, different VPN)");
    if let Some(stack) = pe_a.forward_ip_packet("CustB", "10.2.0.100", 500) {
        println!("[SIM] PE-A emits: stack={}", stack);
        println!("[SIM] CustB packet uses different VPN label (300) → no mixing ✓");
    }

    println!("\nTest 3: Unknown destination in CustA");
    let result = pe_a.forward_ip_packet("CustA", "192.168.99.1", 500);
    if result.is_none() {
        println!("[SIM] No route → packet dropped ✓");
    }

    // ── Label wire format test ────────────────────────────────────────── //
    println!("\n═══════════════════════════════════════════════════");
    println!("  MPLS Label Wire Format Test");
    println!("═══════════════════════════════════════════════════");

    let lbl = MplsLabel::new(200, 5, true, 64);
    let wire = lbl.to_wire();
    let decoded = MplsLabel::from_wire(wire);
    println!("[LABEL] Original: {}", lbl);
    println!("[LABEL] Wire:     0x{:08X}", wire);
    println!("[LABEL] Decoded:  {}", decoded);
    assert_eq!(lbl, decoded, "Label encode/decode roundtrip failed");
    println!("[LABEL] Roundtrip encode/decode: PASS ✓");

    println!("\n[DONE] MPLS L3VPN simulation complete.\n");
}
```

---

## 30. IPSec ESP Encapsulation in Rust

```rust
// ipvpn_ipsec.rs — IPSec ESP Tunnel Mode in Rust
//
// Implements:
//   • ESP packet encapsulation and decapsulation (tunnel mode)
//   • Anti-replay window (64-bit sliding window)
//   • HMAC-SHA256 ICV computation
//   • AES-256-CBC encryption/decryption
//
// Dependencies (Cargo.toml):
//   [dependencies]
//   aes    = "0.8"
//   cbc    = "0.1"
//   hmac   = "0.12"
//   sha2   = "0.10"
//   rand   = "0.8"
//   hex    = "0.4"
//
// Run: cargo run

use std::fmt;
use std::net::Ipv4Addr;

// In a real project, these come from crates:
// use aes::Aes256;
// use cbc::{Decryptor, Encryptor};
// use hmac::{Hmac, Mac};
// use sha2::Sha256;
// For self-contained demonstration, we stub crypto with descriptive output.

// ─────────────────────────────────────────────────────────────────────────── //
// CONSTANTS                                                                    //
// ─────────────────────────────────────────────────────────────────────────── //

const AES_KEY_SIZE:    usize = 32;   // AES-256
const AES_BLOCK_SIZE:  usize = 16;   // AES block size
const AES_IV_SIZE:     usize = 16;   // CBC IV
const HMAC_KEY_SIZE:   usize = 32;   // HMAC-SHA256 key
const ICV_SIZE:        usize = 16;   // Truncated HMAC (128-bit)
const IPPROTO_ESP:     u8    = 50;
const IPPROTO_IPV4:    u8    = 4;

// ─────────────────────────────────────────────────────────────────────────── //
// ERROR TYPE                                                                   //
// ─────────────────────────────────────────────────────────────────────────── //

#[derive(Debug)]
pub enum EspError {
    PacketTooShort { got: usize, min: usize },
    SpiMismatch    { got: u32, expected: u32 },
    ReplayDetected { seq: u32 },
    IcvMismatch,
    DecryptionFailed,
    InvalidPadding,
    UnexpectedNextHeader(u8),
    OutputBufferTooSmall,
    SequenceNumberOverflow,
    CryptoError(String),
}

impl fmt::Display for EspError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            EspError::PacketTooShort { got, min } =>
                write!(f, "Packet too short: got {} bytes, need {}", got, min),
            EspError::SpiMismatch { got, expected } =>
                write!(f, "SPI mismatch: got {}, expected {}", got, expected),
            EspError::ReplayDetected { seq } =>
                write!(f, "Anti-replay: duplicate/old sequence {}", seq),
            EspError::IcvMismatch =>
                write!(f, "ICV verification failed — packet tampered or wrong key"),
            EspError::DecryptionFailed =>
                write!(f, "AES decryption failed"),
            EspError::InvalidPadding =>
                write!(f, "Invalid ESP padding"),
            EspError::UnexpectedNextHeader(n) =>
                write!(f, "Unexpected next header: {}", n),
            EspError::OutputBufferTooSmall =>
                write!(f, "Output buffer too small"),
            EspError::SequenceNumberOverflow =>
                write!(f, "Sequence number overflow — SA must be rekeyed"),
            EspError::CryptoError(s) =>
                write!(f, "Crypto error: {}", s),
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// IP HEADER (simplified, 20 bytes)                                             //
// ─────────────────────────────────────────────────────────────────────────── //

#[derive(Clone, Debug)]
pub struct Ipv4Header {
    pub version_ihl: u8,     // 0x45 for IPv4 with 20-byte header
    pub tos:         u8,
    pub total_len:   u16,    // big-endian on wire
    pub id:          u16,
    pub frag_off:    u16,
    pub ttl:         u8,
    pub protocol:    u8,     // 50 for ESP, 4 for inner IPv4
    pub checksum:    u16,
    pub src:         u32,    // network byte order
    pub dst:         u32,    // network byte order
}

impl Ipv4Header {
    const SIZE: usize = 20;

    pub fn new(src: u32, dst: u32, protocol: u8, payload_len: usize) -> Self {
        let total = (Self::SIZE + payload_len) as u16;
        let mut h = Ipv4Header {
            version_ihl: 0x45,
            tos:         0,
            total_len:   total.to_be(),
            id:          0,
            frag_off:    0,
            ttl:         64,
            protocol,
            checksum:    0,
            src,
            dst,
        };
        h.checksum = h.compute_checksum();
        h
    }

    /// Compute the 16-bit one's complement checksum.
    fn compute_checksum(&self) -> u16 {
        let bytes = self.to_bytes();
        let mut sum: u32 = 0;
        for i in (0..Self::SIZE).step_by(2) {
            let word = ((bytes[i] as u32) << 8) | (bytes[i + 1] as u32);
            sum = sum.wrapping_add(word);
        }
        while sum >> 16 != 0 {
            sum = (sum & 0xFFFF) + (sum >> 16);
        }
        !(sum as u16)
    }

    pub fn to_bytes(&self) -> Vec<u8> {
        let mut v = Vec::with_capacity(Self::SIZE);
        v.push(self.version_ihl);
        v.push(self.tos);
        v.push((self.total_len >> 8) as u8);
        v.push(self.total_len as u8);
        v.push((self.id >> 8) as u8);
        v.push(self.id as u8);
        v.push((self.frag_off >> 8) as u8);
        v.push(self.frag_off as u8);
        v.push(self.ttl);
        v.push(self.protocol);
        v.push((self.checksum >> 8) as u8);
        v.push(self.checksum as u8);
        v.extend_from_slice(&self.src.to_be_bytes());
        v.extend_from_slice(&self.dst.to_be_bytes());
        v
    }

    pub fn from_bytes(b: &[u8]) -> Option<Self> {
        if b.len() < Self::SIZE { return None; }
        Some(Ipv4Header {
            version_ihl: b[0],
            tos:         b[1],
            total_len:   u16::from_be_bytes([b[2], b[3]]),
            id:          u16::from_be_bytes([b[4], b[5]]),
            frag_off:    u16::from_be_bytes([b[6], b[7]]),
            ttl:         b[8],
            protocol:    b[9],
            checksum:    u16::from_be_bytes([b[10], b[11]]),
            src:         u32::from_be_bytes([b[12], b[13], b[14], b[15]]),
            dst:         u32::from_be_bytes([b[16], b[17], b[18], b[19]]),
        })
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// CRYPTO STUBS (descriptive — replace with real crate in production)           //
// ─────────────────────────────────────────────────────────────────────────── //

/// Stub: AES-256-CBC encrypt.
/// In production: use `aes` + `cbc` crates.
fn aes256_cbc_encrypt(key: &[u8; AES_KEY_SIZE],
                       iv:  &[u8; AES_IV_SIZE],
                       plaintext: &[u8]) -> Result<Vec<u8>, EspError> {
    // Plaintext must be a multiple of AES_BLOCK_SIZE (we pad externally)
    assert!(plaintext.len() % AES_BLOCK_SIZE == 0,
            "Plaintext must be block-aligned before calling encrypt");

    // STUB: XOR each block with IV chain (not real AES — for demo only)
    // Real: Aes256::new(key.into()).encrypt_block(...)
    let mut ct = plaintext.to_vec();
    let mut prev = iv.to_vec();
    for chunk in ct.chunks_mut(AES_BLOCK_SIZE) {
        for (i, b) in chunk.iter_mut().enumerate() {
            *b ^= prev[i];       // CBC: XOR with previous ciphertext block
        }
        // In real AES: encrypt the XORed block
        // For stub: just XOR with key bytes
        for (i, b) in chunk.iter_mut().enumerate() {
            *b ^= key[i % AES_KEY_SIZE];
        }
        prev = chunk.to_vec();
    }
    Ok(ct)
}

/// Stub: AES-256-CBC decrypt.
fn aes256_cbc_decrypt(key: &[u8; AES_KEY_SIZE],
                       iv:  &[u8; AES_IV_SIZE],
                       ciphertext: &[u8]) -> Result<Vec<u8>, EspError> {
    assert!(ciphertext.len() % AES_BLOCK_SIZE == 0);

    let mut pt = ciphertext.to_vec();
    let mut prev = iv.to_vec();
    for chunk in pt.chunks_mut(AES_BLOCK_SIZE) {
        let current_ct = chunk.to_vec();
        // Reverse the stub XOR with key
        for (i, b) in chunk.iter_mut().enumerate() {
            *b ^= key[i % AES_KEY_SIZE];
        }
        // Reverse the CBC XOR with previous block
        for (i, b) in chunk.iter_mut().enumerate() {
            *b ^= prev[i];
        }
        prev = current_ct;
    }
    Ok(pt)
}

/// Stub: HMAC-SHA256, truncated to ICV_SIZE.
/// In production: use `hmac` + `sha2` crates.
fn hmac_sha256_truncated(key: &[u8; HMAC_KEY_SIZE],
                          data: &[u8]) -> [u8; ICV_SIZE] {
    // STUB: simple XOR-based MAC (NOT secure — for demonstration only)
    // Real: Hmac::<Sha256>::new_from_slice(key)?.update(data).finalize()
    let mut mac = [0u8; ICV_SIZE];
    for (i, &b) in data.iter().enumerate() {
        mac[i % ICV_SIZE] ^= b ^ key[i % HMAC_KEY_SIZE];
    }
    // Add some key mixing
    for i in 0..ICV_SIZE {
        mac[i] = mac[i].wrapping_add(key[i]).wrapping_add(i as u8);
    }
    mac
}

/// Generate pseudo-random IV (not cryptographically secure stub).
fn generate_iv(seq: u32) -> [u8; AES_IV_SIZE] {
    // In production: use `rand::thread_rng().fill_bytes(&mut iv)`
    let mut iv = [0u8; AES_IV_SIZE];
    for (i, b) in iv.iter_mut().enumerate() {
        *b = ((seq.wrapping_mul(0x9E3779B9 + i as u32)) >> 16) as u8;
    }
    iv
}

/// Constant-time comparison (prevents timing side-channel attacks).
fn ct_eq(a: &[u8], b: &[u8]) -> bool {
    if a.len() != b.len() { return false; }
    let mut diff: u8 = 0;
    for (x, y) in a.iter().zip(b.iter()) {
        diff |= x ^ y;
    }
    diff == 0
}

// ─────────────────────────────────────────────────────────────────────────── //
// SECURITY ASSOCIATION                                                          //
// ─────────────────────────────────────────────────────────────────────────── //

#[derive(Debug)]
pub enum SaState {
    Active,
    Expired,
}

pub struct SecurityAssociation {
    pub spi:             u32,
    pub src_ip:          u32,    // network order
    pub dst_ip:          u32,    // network order
    pub enc_key:         [u8; AES_KEY_SIZE],
    pub auth_key:        [u8; HMAC_KEY_SIZE],
    pub seq_num:         u32,    // outbound sequence counter
    pub recv_seq:        u32,    // highest inbound seq received
    pub replay_window:   u64,    // 64-bit bitmask (bit 0 = recv_seq)
    pub state:           SaState,
    pub bytes_processed: u64,
}

impl SecurityAssociation {
    pub fn new(spi: u32, src_ip: u32, dst_ip: u32,
               enc_key: [u8; AES_KEY_SIZE],
               auth_key: [u8; HMAC_KEY_SIZE]) -> Self {
        SecurityAssociation {
            spi,
            src_ip,
            dst_ip,
            enc_key,
            auth_key,
            seq_num:         0,
            recv_seq:        0,
            replay_window:   0,
            state:           SaState::Active,
            bytes_processed: 0,
        }
    }

    /// Check and update anti-replay window for inbound sequence number.
    ///
    /// Window algorithm (RFC 6479 §2):
    ///   recv_seq = highest valid seq seen.
    ///   Bit N in window = 1 means (recv_seq - N) was received.
    ///   Bit 0 = recv_seq (MSB of window corresponds to oldest).
    pub fn anti_replay_check(&mut self, seq: u32) -> Result<(), EspError> {
        if seq == 0 {
            return Err(EspError::ReplayDetected { seq });
        }

        if seq > self.recv_seq {
            let diff = seq - self.recv_seq;
            if diff < 64 {
                self.replay_window <<= diff;
            } else {
                self.replay_window = 0;
            }
            self.replay_window |= 1u64;
            self.recv_seq = seq;
            Ok(())
        } else {
            let diff = self.recv_seq - seq;
            if diff >= 64 {
                return Err(EspError::ReplayDetected { seq });
            }
            let bit = 1u64 << diff;
            if self.replay_window & bit != 0 {
                return Err(EspError::ReplayDetected { seq });
            }
            self.replay_window |= bit;
            Ok(())
        }
    }

    /// Increment outbound sequence number.
    pub fn next_seq(&mut self) -> Result<u32, EspError> {
        let (new_seq, overflowed) = self.seq_num.overflowing_add(1);
        if overflowed || new_seq == 0 {
            self.state = SaState::Expired;
            return Err(EspError::SequenceNumberOverflow);
        }
        self.seq_num = new_seq;
        Ok(self.seq_num)
    }
}

// ─────────────────────────────────────────────────────────────────────────── //
// ESP ENCAPSULATION                                                             //
// ─────────────────────────────────────────────────────────────────────────── //

/// Result of ESP encapsulation: the complete ESP tunnel packet.
pub struct EspPacket {
    pub bytes: Vec<u8>,
    pub spi:   u32,
    pub seq:   u32,
}

impl fmt::Display for EspPacket {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "ESP Packet: {} bytes, SPI={}, Seq={}",
               self.bytes.len(), self.spi, self.seq)
    }
}

/// Build an ESP tunnel mode packet from an inner IP packet.
///
/// Packet layout:
///   [Outer IP Hdr][ESP Hdr][IV][Enc(InnerIP+Payload+Pad+Trailer)][ICV]
pub fn esp_encapsulate(
    sa:         &mut SecurityAssociation,
    inner_pkt:  &[u8],    // original IP packet to protect
) -> Result<EspPacket, EspError> {

    // Step 1: Compute padding.
    // plaintext = inner_pkt + ESP trailer (2 bytes: pad_len + next_header)
    // Must be padded to AES block size.
    let trailer_size = 2usize;
    let raw_len = inner_pkt.len() + trailer_size;
    let pad_len = if raw_len % AES_BLOCK_SIZE == 0 {
        0
    } else {
        AES_BLOCK_SIZE - (raw_len % AES_BLOCK_SIZE)
    };
    let padded_len = raw_len + pad_len;

    // Step 2: Build plaintext = [inner_pkt][padding 0x01..pad_len][pad_len][next_hdr]
    let mut plaintext = Vec::with_capacity(padded_len);
    plaintext.extend_from_slice(inner_pkt);

    // Padding bytes: 0x01, 0x02, ..., 0x{pad_len}
    for i in 1..=(pad_len as u8) {
        plaintext.push(i);
    }

    // ESP trailer
    plaintext.push(pad_len as u8);      // Pad Length
    plaintext.push(IPPROTO_IPV4);       // Next Header = inner IPv4

    assert_eq!(plaintext.len(), padded_len);

    // Step 3: Get next sequence number.
    let seq = sa.next_seq()?;

    // Step 4: Generate IV.
    let iv = generate_iv(seq);

    // Step 5: Encrypt plaintext.
    let ciphertext = aes256_cbc_encrypt(&sa.enc_key, &iv, &plaintext)?;

    // Step 6: Assemble ESP portion = [SPI][Seq][IV][Ciphertext]
    let mut esp_body = Vec::new();
    esp_body.extend_from_slice(&sa.spi.to_be_bytes());
    esp_body.extend_from_slice(&seq.to_be_bytes());
    esp_body.extend_from_slice(&iv);
    esp_body.extend_from_slice(&ciphertext);

    // Step 7: Compute ICV over [SPI][Seq][IV][Ciphertext]
    let icv = hmac_sha256_truncated(&sa.auth_key, &esp_body);
    esp_body.extend_from_slice(&icv);

    // Step 8: Build outer IP header.
    // Total = IP header (20) + ESP body
    let outer_ip = Ipv4Header::new(sa.src_ip, sa.dst_ip,
                                    IPPROTO_ESP, esp_body.len());
    let mut packet = outer_ip.to_bytes();
    packet.extend_from_slice(&esp_body);

    sa.bytes_processed += inner_pkt.len() as u64;

    println!("[ESP] Encapsulated:");
    println!("      Inner packet: {} bytes", inner_pkt.len());
    println!("      Pad: {} bytes", pad_len);
    println!("      Ciphertext: {} bytes", ciphertext.len());
    println!("      Total ESP packet: {} bytes", packet.len());
    println!("      SPI={} Seq={}", sa.spi, seq);

    Ok(EspPacket { bytes: packet, spi: sa.spi, seq })
}

// ─────────────────────────────────────────────────────────────────────────── //
// ESP DECAPSULATION                                                             //
// ─────────────────────────────────────────────────────────────────────────── //

/// Decapsulate an ESP tunnel mode packet, returning the inner IP packet.
///
/// Order of operations (RFC 4303 §3.4.4):
///   1. Parse outer IP header
///   2. Parse ESP header — get SPI and sequence number
///   3. Verify SPI matches SA
///   4. Anti-replay check
///   5. Verify ICV (AUTHENTICATE FIRST before decryption)
///   6. Decrypt ciphertext
///   7. Strip padding and trailer
///   8. Return inner IP packet
pub fn esp_decapsulate(
    sa:        &mut SecurityAssociation,
    pkt:       &[u8],    // incoming ESP packet (outer IP + ESP)
) -> Result<Vec<u8>, EspError> {

    // Minimum valid ESP packet size calculation
    let min_size = Ipv4Header::SIZE          // outer IP header
                 + 4                          // ESP SPI
                 + 4                          // ESP Seq
                 + AES_IV_SIZE               // IV
                 + AES_BLOCK_SIZE            // at least 1 block ciphertext
                 + ICV_SIZE;                 // ICV

    if pkt.len() < min_size {
        return Err(EspError::PacketTooShort { got: pkt.len(), min: min_size });
    }

    // Step 1: Parse outer IP header
    let outer_ip = Ipv4Header::from_bytes(pkt)
        .ok_or(EspError::PacketTooShort { got: pkt.len(), min: Ipv4Header::SIZE })?;
    let ip_hdr_len = ((outer_ip.version_ihl & 0x0F) as usize) * 4;

    // Step 2: Parse ESP header
    let esp_start = ip_hdr_len;
    let spi = u32::from_be_bytes([
        pkt[esp_start],     pkt[esp_start + 1],
        pkt[esp_start + 2], pkt[esp_start + 3],
    ]);
    let seq = u32::from_be_bytes([
        pkt[esp_start + 4], pkt[esp_start + 5],
        pkt[esp_start + 6], pkt[esp_start + 7],
    ]);

    // Step 3: Verify SPI
    if spi != sa.spi {
        return Err(EspError::SpiMismatch { got: spi, expected: sa.spi });
    }

    // Step 4: Anti-replay check
    // We do this before ICV to avoid expensive crypto on replays.
    // (Some implementations do ICV first for DoS protection — tradeoff.)
    sa.anti_replay_check(seq)?;

    // Layout from esp_start:
    //   [SPI:4][Seq:4][IV:16][Ciphertext:?][ICV:16]
    let iv_start  = esp_start + 8;
    let ct_start  = iv_start + AES_IV_SIZE;
    let icv_start = pkt.len() - ICV_SIZE;
    let ct_end    = icv_start;

    if ct_start >= ct_end {
        return Err(EspError::PacketTooShort { got: pkt.len(), min: min_size });
    }
    let ct_len = ct_end - ct_start;
    if ct_len % AES_BLOCK_SIZE != 0 {
        return Err(EspError::InvalidPadding);
    }

    let iv         = &pkt[iv_start..ct_start];
    let ciphertext = &pkt[ct_start..ct_end];
    let recv_icv   = &pkt[icv_start..];

    // Step 5: Verify ICV BEFORE decryption.
    // Authenticate [SPI + Seq + IV + Ciphertext]
    let auth_data = &pkt[esp_start..ct_end];
    let computed_icv = hmac_sha256_truncated(&sa.auth_key, auth_data);

    if !ct_eq(&computed_icv, recv_icv) {
        return Err(EspError::IcvMismatch);
    }
    println!("[ESP] ICV verified ✓");

    // Step 6: Decrypt
    let iv_arr: [u8; AES_IV_SIZE] = iv.try_into()
        .map_err(|_| EspError::CryptoError("IV length mismatch".into()))?;

    let plaintext = aes256_cbc_decrypt(&sa.enc_key, &iv_arr, ciphertext)
        .map_err(|_| EspError::DecryptionFailed)?;

    // Step 7: Parse ESP trailer from end of plaintext
    // [inner_pkt][padding][pad_len][next_header]
    if plaintext.len() < 2 {
        return Err(EspError::InvalidPadding);
    }
    let pad_len     = plaintext[plaintext.len() - 2] as usize;
    let next_header = plaintext[plaintext.len() - 1];

    if next_header != IPPROTO_IPV4 {
        return Err(EspError::UnexpectedNextHeader(next_header));
    }

    if 2 + pad_len > plaintext.len() {
        return Err(EspError::InvalidPadding);
    }

    let inner_len = plaintext.len() - pad_len - 2;
    let inner_pkt = plaintext[..inner_len].to_vec();

    println!("[ESP] Decapsulated: ESP={} bytes → inner={} bytes  SPI={}  Seq={}",
             pkt.len(), inner_len, spi, seq);

    Ok(inner_pkt)
}

// ─────────────────────────────────────────────────────────────────────────── //
// MAIN DEMONSTRATION                                                            //
// ─────────────────────────────────────────────────────────────────────────── //

fn build_test_icmp_packet(src: &str, dst: &str) -> Vec<u8> {
    let src_ip = u32::from(src.parse::<Ipv4Addr>().unwrap());
    let dst_ip = u32::from(dst.parse::<Ipv4Addr>().unwrap());

    // ICMP Echo (type=8, code=0, id=0x1234, seq=1)
    let icmp = [8u8, 0, 0, 0, 0x12, 0x34, 0, 1];
    // ICMP checksum
    let cs: u16 = {
        let s: u32 = icmp.chunks(2)
            .map(|c| (c[0] as u32) << 8 | c[1] as u32)
            .sum();
        let s = (s & 0xFFFF) + (s >> 16);
        !(s as u16)
    };
    let mut icmp_v = icmp.to_vec();
    icmp_v[2] = (cs >> 8) as u8;
    icmp_v[3] = cs as u8;

    let ip = Ipv4Header::new(src_ip, dst_ip, 1 /* ICMP */, icmp_v.len());
    let mut pkt = ip.to_bytes();
    pkt.extend_from_slice(&icmp_v);
    pkt
}

fn main() {
    println!("\n╔═══════════════════════════════════════════════════════╗");
    println!("║    IPSec ESP Tunnel Mode — Rust Implementation         ║");
    println!("╚═══════════════════════════════════════════════════════╝\n");

    // Create outbound SA (GW-A → GW-B)
    let enc_key:  [u8; AES_KEY_SIZE]  = [0xAAu8; AES_KEY_SIZE];
    let auth_key: [u8; HMAC_KEY_SIZE] = [0xBBu8; HMAC_KEY_SIZE];

    let src_ip = u32::from("198.51.100.1".parse::<Ipv4Addr>().unwrap());
    let dst_ip = u32::from("203.0.113.1".parse::<Ipv4Addr>().unwrap());

    let mut sa_out = SecurityAssociation::new(0x1001, src_ip, dst_ip, enc_key, auth_key);
    let mut sa_in  = SecurityAssociation::new(0x1001, src_ip, dst_ip, enc_key, auth_key);

    // ── Build inner test packet ──────────────────────────────────────── //
    println!("[TEST] Building ICMP echo: 10.1.0.50 → 10.2.0.50");
    let inner = build_test_icmp_packet("10.1.0.50", "10.2.0.50");
    println!("[TEST] Inner packet: {} bytes", inner.len());
    print!("[TEST] Hex: ");
    for b in &inner { print!("{:02X} ", b); }
    println!("\n");

    // ── Encapsulate ──────────────────────────────────────────────────── //
    println!("══════════════════════════════════════════════");
    println!(" ENCAPSULATION (GW-A → GW-B)");
    println!("══════════════════════════════════════════════");

    let esp_pkt = esp_encapsulate(&mut sa_out, &inner)
        .expect("Encapsulation failed");
    println!("[ESP] {}", esp_pkt);
    println!("[ESP] Overhead: {} bytes\n", esp_pkt.bytes.len() - inner.len());

    // ── Decapsulate ──────────────────────────────────────────────────── //
    println!("══════════════════════════════════════════════");
    println!(" DECAPSULATION (GW-B receives)");
    println!("══════════════════════════════════════════════");

    let recovered = esp_decapsulate(&mut sa_in, &esp_pkt.bytes)
        .expect("Decapsulation failed");

    // ── Verify ───────────────────────────────────────────────────────── //
    println!("\n══════════════════════════════════════════════");
    println!(" VERIFICATION");
    println!("══════════════════════════════════════════════");

    if recovered == inner {
        println!("[✓] PASS: Inner packet perfectly recovered ({} bytes)", recovered.len());
    } else {
        panic!("[✗] FAIL: Packet mismatch!");
    }

    // ── Anti-replay test ─────────────────────────────────────────────── //
    println!("\n[TEST] Anti-replay: replaying same packet (seq=1)");
    match esp_decapsulate(&mut sa_in, &esp_pkt.bytes) {
        Err(EspError::ReplayDetected { seq }) =>
            println!("[✓] PASS: Replay seq={} correctly rejected", seq),
        _ =>
            panic!("[✗] FAIL: Replay should have been rejected!"),
    }

    // ── ICV tampering test ───────────────────────────────────────────── //
    println!("\n[TEST] ICV tampering: corrupting ciphertext byte");
    let mut tampered = esp_pkt.bytes.clone();
    let tamper_idx = Ipv4Header::SIZE + 8 + AES_IV_SIZE + 4; // inside ciphertext
    tampered[tamper_idx] ^= 0xFF;

    // Reset anti-replay for fresh test
    sa_in.recv_seq      = 0;
    sa_in.replay_window = 0;

    match esp_decapsulate(&mut sa_in, &tampered) {
        Err(EspError::IcvMismatch) =>
            println!("[✓] PASS: Tampered packet correctly rejected (ICV mismatch)"),
        Err(e) =>
            println!("[?] Rejected with different error: {}", e),
        Ok(_) =>
            panic!("[✗] FAIL: Tampered packet should have been rejected!"),
    }

    // ── Multiple packets (sequence counter test) ─────────────────────── //
    println!("\n[TEST] Multiple sequential packets");
    let mut sa_out2 = SecurityAssociation::new(0x2001, src_ip, dst_ip, enc_key, auth_key);
    let mut sa_in2  = SecurityAssociation::new(0x2001, src_ip, dst_ip, enc_key, auth_key);

    for i in 1..=5u32 {
        let pkt = esp_encapsulate(&mut sa_out2, &inner).unwrap();
        let dec = esp_decapsulate(&mut sa_in2, &pkt.bytes).unwrap();
        assert_eq!(dec, inner);
        println!("[✓] Packet {} (seq={}): encap/decap success", i, pkt.seq);
    }

    println!("\n[DONE] IPSec ESP Rust simulation complete.\n");
}
```

---

# PART X — COMPARISON, ATTACKS & HARDENING

---

## 31. VPN Technology Comparison Matrix

```
COMPREHENSIVE VPN COMPARISON:
===============================

┌──────────────┬────────┬────────┬──────────┬────────┬────────┬──────────┐
│ Feature      │ MPLS   │ IPSec  │ GRE+IPSec│ L2TP   │ SSL    │ WireGuard│
│              │ L3VPN  │        │          │/IPSec  │ VPN    │          │
├──────────────┼────────┼────────┼──────────┼────────┼────────┼──────────┤
│ OSI Layer    │ L3     │ L3     │ L3       │ L2     │ L4/L7  │ L3       │
│ Encryption   │ None   │ Yes    │ Yes      │ Yes    │ TLS    │ ChaCha20 │
│ Multi-site   │ Native │ Hub/SP │ Yes      │ Yes    │ Limited│ Yes      │
│ Multicast    │ Yes    │ No     │ Yes      │ No     │ No     │ No       │
│ BGP routing  │ Yes    │ No     │ Yes      │ No     │ No     │ No       │
│ NAT traverse │ N/A    │ UDP    │ Limited  │ Yes    │ Yes    │ Yes(UDP) │
│ QoS          │ Native │ DSCP   │ DSCP     │ DSCP   │ No     │ DSCP     │
│ Management   │ SP     │ Self   │ Self     │ Self   │ Self   │ Self     │
│ Performance  │ +++++  │ +++    │ ++       │ ++     │ +      │ ++++     │
│ Complexity   │ High   │ Medium │ Medium   │ Medium │ Low    │ Low      │
│ Use case     │ MPLS SP│ Site-2 │ Site-2   │ Remote │ Remote │ Modern   │
│              │ WAN    │ site   │ site     │ access │ access │ overlay  │
└──────────────┴────────┴────────┴──────────┴────────┴────────┴──────────┘
```

---

## 32. MTU and Fragmentation Issues

Every encapsulation adds overhead — this creates MTU problems.

```
MTU OVERHEAD CALCULATION:
===========================

Physical Ethernet MTU: 1500 bytes

GRE Overhead:
  Outer IP:    20 bytes
  GRE header:   4 bytes
  ─────────────────────
  Total:       24 bytes
  Available:   1476 bytes for inner packet

IPSec ESP (AES-128-CBC + HMAC-SHA1-96) Overhead:
  Outer IP:    20 bytes
  ESP header:   8 bytes (SPI + Seq)
  IV:          16 bytes
  Padding:     up to 15 bytes
  ESP trailer:  2 bytes
  ICV:         12 bytes (HMAC-SHA1-96 truncated to 96 bits)
  ─────────────────────
  Minimum:     58 bytes overhead
  Maximum:     73 bytes overhead
  Typical MTU: 1500 - 58 = 1442 bytes (best case)

GRE + IPSec (AES-256-CBC + HMAC-SHA256-128):
  Outer IP:    20 bytes
  ESP header:   8 bytes
  IV:          16 bytes
  GRE header:   4 bytes (inside ESP)
  Padding:     up to 15 bytes
  ESP trailer:  2 bytes
  ICV:         16 bytes
  ─────────────────────
  Overhead:   ~81+ bytes
  Available:  1500 - 81 = 1419 bytes

MPLS overhead:
  Each MPLS label: 4 bytes
  2 labels (transport + VPN): 8 bytes
  Available: 1500 - 8 = 1492 bytes

TCP MSS CLAMPING:
  If MTU=1500, IP=20, TCP=20 → MSS = 1460
  With GRE+IPSec overhead=81 → effective MSS = 1379

  Solution: Set TCP MSS via firewall rule:
  iptables -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --set-mss 1360

ICMP FRAGMENTATION NEEDED:
  If router cannot fragment (DF bit set) and packet > link MTU:
  Router sends ICMP Type 3 Code 4 (Frag Needed) back to sender.
  This is how PMTU Discovery works.
  Problem: Many firewalls block ICMP → "PMTU black hole"
  Solution: Force TCP MSS clamping at VPN gateway.
```

---

## 33. VPN Attack Vectors and Mitigations

### IKEv1 Attacks (Legacy)

```
ATTACK: Aggressive Mode Information Disclosure
  • IKEv1 Aggressive Mode sends identity before encryption.
  • Attacker can capture exchange, run offline dictionary attack on PSK.
  FIX: Use IKEv2 (always encrypts identity). Never use Aggressive Mode.

ATTACK: IKEv1 Main Mode with PSK — Identity Protection Bypass
  • With PSK + certificate, identity IS protected.
  • With PSK only, XAUTH username/password can be brute-forced.
  FIX: Use certificate-based auth (X.509) instead of PSK.

ATTACK: IKEv1 Multiple Cookie Amplification (DoS)
  • Attacker spoofs source IP, causes responder to compute DH.
  FIX: IKEv2 has built-in cookie mechanism.
```

### ESP Attacks

```
ATTACK: Padding Oracle
  • If decryption error is distinguishable from MAC failure,
    attacker can recover plaintext byte by byte.
  FIX: Always verify MAC BEFORE decrypting.
       Return same error message for all failures.
       Use AES-GCM (combines encryption + auth — no padding oracle).

ATTACK: IV Reuse (AES-CBC)
  • Reusing IV + key leaks XOR of plaintexts.
  FIX: Generate cryptographically random IV per packet.
       Better: Use AES-GCM (nonce + counter, authenticated encryption).

ATTACK: Sequence Number Rollover
  • If seq reaches 2^32, SA expires — must rekey.
  • If rekey fails, either connection drops or (worse) seq wraps = replay possible.
  FIX: Extended Sequence Numbers (ESN) — 64-bit seq num (RFC 4304).
       Trigger rekey well before seq limit.

ATTACK: Traffic Analysis
  • Even with encryption, packet sizes and timing reveal information.
  FIX: Packet padding (ESP does this), fixed-rate traffic generation (expensive).
```

### MPLS VPN Attacks

```
ATTACK: Label Spoofing
  • Attacker on PE-facing link inserts packet with customer VPN label.
  FIX: PE validates ingress — only accept labeled packets from P routers.
       Customer-facing CE interfaces never receive labeled packets.

ATTACK: BGP Hijacking
  • Compromised PE advertises false routes into VRF.
  FIX: Route filtering, max-prefix limits, BGP authentication (MD5 or TCP-AO).

ATTACK: VRF Leakage via Misconfigured RT
  • Wrong RT configuration causes routes to leak between VRFs.
  FIX: Strict RT policy review, separate RDs per VRF, route filtering.

ATTACK: PHP Timing Attack
  • At penultimate hop, only VPN label visible, timing reveals VPN identity.
  FIX: Use Ultimate Hop Popping (UHP) instead of PHP.
       Configure egress PE to NOT signal implicit null.
```

### Hardening Checklist

```
IKEv2 HARDENING:
  ✓ Use IKEv2 only (never IKEv1)
  ✓ Certificate authentication (never PSK for production)
  ✓ DH Group 19 minimum (256-bit ECP) or Group 20/21
  ✓ AES-256-GCM (eliminates padding oracle — AEAD cipher)
  ✓ SHA-384 or SHA-512 for PRF and integrity
  ✓ Enable Dead Peer Detection (DPD)
  ✓ Enable Perfect Forward Secrecy (PFS) for child SAs
  ✓ Set SA lifetime: IKE = 86400s, Child = 3600s or 4GB
  ✓ Extended Sequence Numbers (ESN) enabled
  ✓ Anti-replay window = 64 or 128 packets

MPLS VPN HARDENING:
  ✓ Strict interface-based VRF assignment
  ✓ No labeled packet acceptance from CE interfaces
  ✓ BGP route filtering per VRF
  ✓ Max-prefix limits on BGP sessions
  ✓ BGP MD5 authentication or TCP-AO
  ✓ MPLS TTL propagation disabled (hide hop count from customers)
  ✓ Separate RD per VRF per PE
  ✓ RT import filters (whitelist, not wildcard)
  ✓ Audit VRF route tables for unexpected routes

GENERAL VPN HARDENING:
  ✓ Disable split tunneling for high-security deployments
  ✓ Enforce certificate revocation (CRL/OCSP)
  ✓ Log all IKE negotiations and policy changes
  ✓ Monitor for duplicate packets (replay attempts)
  ✓ Test PMTU Discovery — no ICMP black holes
  ✓ Limit VPN access by source IP where possible
  ✓ Rate-limit IKE requests (DoS protection)
```

---

## 34. Real-World Protocol Numbers and Headers Reference

```
IP PROTOCOL NUMBERS (relevant to VPN):
  4   = IPv4 in IPv4 (IP-in-IP tunneling)
  6   = TCP
  17  = UDP
  41  = IPv6 in IPv4 (6in4 tunneling)
  47  = GRE
  50  = ESP (IPSec)
  51  = AH (IPSec)
  115 = L2TP

UDP/TCP PORTS:
  UDP 500   = IKE (Internet Key Exchange)
  UDP 4500  = IKE NAT-Traversal + ESP-in-UDP
  TCP 179   = BGP
  UDP 646   = LDP (MPLS)
  TCP 646   = LDP (MPLS)
  UDP 1701  = L2TP
  TCP 1723  = PPTP
  UDP 1194  = OpenVPN (default)
  UDP 51820 = WireGuard (default)

ETHERTYPE VALUES:
  0x0800 = IPv4
  0x0806 = ARP
  0x8100 = 802.1Q VLAN
  0x8847 = MPLS unicast
  0x8848 = MPLS multicast
  0x86DD = IPv6
  0x8902 = IEEE 802.1ag (CFM)

BGP ADDRESS FAMILY IDENTIFIERS (AFI/SAFI):
  AFI 1, SAFI 1   = IPv4 unicast
  AFI 1, SAFI 2   = IPv4 multicast
  AFI 1, SAFI 128 = VPNv4 (MPLS L3VPN)
  AFI 1, SAFI 4   = IPv4 + MPLS label
  AFI 2, SAFI 1   = IPv6 unicast
  AFI 2, SAFI 128 = VPNv6
  AFI 25, SAFI 70 = EVPN
  AFI 25, SAFI 65 = VPLS (BGP-based)

MPLS RESERVED LABELS:
  0   = IPv4 Explicit NULL   (impose at ingress PE, not PHP)
  1   = Router Alert Label
  2   = IPv6 Explicit NULL
  3   = Implicit NULL        (signal PHP to penultimate hop)
  4–6 = Reserved
  7   = Entropy Label Indicator (ELI) — RFC 6790
  8–12 = Reserved
  13  = Generic Associated Channel Label (GAL)
  14  = OAM Alert Label
  15  = Extension Label (XL)
  16–1048575 = Available for use
```

---

## 35. Control Plane Protocols Summary

```
COMPLETE CONTROL PLANE PROTOCOL STACK FOR MPLS L3VPN:

Level 1: IGP (Interior Gateway Protocol) — PE and P routers
  Protocols: OSPF (RFC 2328) or IS-IS (RFC 5308)
  Purpose: Distribute loopback IP addresses of PE/P routers
  Scope: SP backbone only
  Why needed: iBGP next-hops (PE loopbacks) must be reachable

Level 2: LDP or RSVP-TE — PE and P routers
  LDP (RFC 5036): Auto-distribute labels for IGP routes
    → Creates transport LSPs for PE loopbacks
    → Simple to configure, no traffic engineering
  RSVP-TE (RFC 3209): Traffic-engineered LSPs
    → Explicit paths, bandwidth reservation
    → Used for traffic engineering

Level 3: MP-BGP VPNv4 — PE routers only (P routers excluded)
  Protocol: BGP-4 with MP extensions (RFC 4760)
  AFI/SAFI: 1/128 (VPNv4)
  Purpose: Distribute customer VPN routes + VPN labels between PEs
  Carries: VPNv4 prefixes, MPLS labels, Route Targets
  Next-hop: PE loopback IPs (reachable via LDP/RSVP-TE)

Level 4: CE-PE routing (customer ↔ SP boundary)
  Options:
    a) Static routes (simplest, no routing protocol)
    b) eBGP (most flexible, customer controls routes)
    c) OSPF (with superbackbone — complex)
    d) EIGRP (Cisco proprietary — legacy)
    e) RIPv2 (legacy — use only if nothing else possible)

SIGNALING SUMMARY:
  CE-A ──[eBGP/static]── PE-A ──[MP-BGP VPNv4]── PE-B ──[eBGP/static]── CE-B
                   ↕ (LDP labels)          ↕ (LDP labels)
                  PE-A ──────── P1 ── P2 ────── PE-B
                         (IGP distributes loopbacks)
```

---

*"Master the protocol stack from the ground up — understand why each layer exists before memorizing how it works."*

---

**End of IPVPN Complete Guide**

**Compile Commands:**
```bash
# C VRF (no external deps):
gcc -O2 -std=c11 -Wall -Wextra -o ipvpn_vrf ipvpn_vrf.c && ./ipvpn_vrf

# C IPSec (requires OpenSSL):
gcc -O2 -std=c11 -Wall -Wextra -o ipvpn_ipsec ipvpn_ipsec.c -lssl -lcrypto && ./ipvpn_ipsec

# Rust VRF:
rustc -O -o ipvpn_vrf ipvpn_vrf.rs && ./ipvpn_vrf

# Rust IPSec (as single file):
rustc -O -o ipvpn_ipsec ipvpn_ipsec.rs && ./ipvpn_ipsec
```
Claude's response could not be fully generated
