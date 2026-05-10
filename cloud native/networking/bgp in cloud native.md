


# BGP: A Complete In-Depth Reference
## Border Gateway Protocol in Cloud-Native, Data Center, and Cloud Networking

> **Scope**: This document covers BGP from the wire format up through kernel internals, data-center fabric design, cloud-native integration (Calico, Cilium, MetalLB), cloud provider connectivity, EVPN, RPKI, and real C/Rust implementations. ASCII protocol diagrams are exact byte-level representations from the RFCs.

---

## Table of Contents

1. [BGP History and RFC Evolution](#1-bgp-history-and-rfc-evolution)
2. [BGP Fundamentals — Mental Model](#2-bgp-fundamentals--mental-model)
3. [BGP Message Formats (Wire Level)](#3-bgp-message-formats-wire-level)
4. [BGP Finite State Machine (FSM)](#4-bgp-finite-state-machine-fsm)
5. [BGP Attributes — Complete Reference](#5-bgp-attributes--complete-reference)
6. [BGP Decision Process (Path Selection)](#6-bgp-decision-process-path-selection)
7. [iBGP vs eBGP — Deep Dive](#7-ibgp-vs-ebgp--deep-dive)
8. [BGP Route Reflection and Confederations](#8-bgp-route-reflection-and-confederations)
9. [BGP Communities (Standard, Extended, Large)](#9-bgp-communities-standard-extended-large)
10. [BGP in Data Centers — RFC 7938 and Clos Fabrics](#10-bgp-in-data-centers--rfc-7938-and-clos-fabrics)
11. [BGP Unnumbered](#11-bgp-unnumbered)
12. [BGP ECMP and Multipath](#12-bgp-ecmp-and-multipath)
13. [BFD with BGP](#13-bfd-with-bgp)
14. [BGP EVPN (RFC 7432)](#14-bgp-evpn-rfc-7432)
15. [BGP MPLS/VPN (RFC 4364 / L3VPN)](#15-bgp-mplsvpn-rfc-4364--l3vpn)
16. [BGP Flowspec (RFC 5575)](#16-bgp-flowspec-rfc-5575)
17. [BGP-LS — Link State Distribution](#17-bgp-ls--link-state-distribution)
18. [BGP ADD-PATH (RFC 7911)](#18-bgp-add-path-rfc-7911)
19. [BGP in Cloud-Native Networking](#19-bgp-in-cloud-native-networking)
20. [Calico BGP Deep Dive](#20-calico-bgp-deep-dive)
21. [Cilium BGP Deep Dive](#21-cilium-bgp-deep-dive)
22. [MetalLB BGP Mode](#22-metallb-bgp-mode)
23. [BGP in Cloud Provider Networking](#23-bgp-in-cloud-provider-networking)
24. [BGP Security — RPKI, BGPsec, Filtering](#24-bgp-security--rpki-bgpsec-filtering)
25. [Linux Kernel BGP Internals](#25-linux-kernel-bgp-internals)
26. [FRRouting (FRR) — Architecture and Internals](#26-frrouting-frr--architecture-and-internals)
27. [C Implementation — BGP State Machine and Parser](#27-c-implementation--bgp-state-machine-and-parser)
28. [Rust Implementation — BGP Speaker](#28-rust-implementation--bgp-speaker)
29. [BGP Monitoring, Troubleshooting, and Observability](#29-bgp-monitoring-troubleshooting-and-observability)
30. [Operational Best Practices](#30-operational-best-practices)

---

## 1. BGP History and RFC Evolution

BGP was invented to replace EGP (Exterior Gateway Protocol, RFC 904) which could not scale and had no loop prevention. The Internet was transitioning from a single-backbone NSFnet model to a multi-provider model.

```
Timeline of BGP RFCs:

 1989  BGP-1  RFC 1105  — Initial specification by Kirk Lougheed & Yakov Rekhter
 1990  BGP-2  RFC 1163  — Clarifications and fixes
 1991  BGP-3  RFC 1267  — Added AGGREGATOR attribute
 1995  BGP-4  RFC 1771  — CIDR support, NLRI encoding, path aggregation (THE version)
 2006  BGP-4  RFC 4271  — Updated/clarified BGP-4 (current baseline)

Key Extensions (RFCs):
 RFC 2545  — Use of BGP Multiprotocol Extensions for IPv6
 RFC 2796  — BGP Route Reflection
 RFC 3107  — Carrying Label Information in BGP-4
 RFC 4360  — BGP Extended Communities
 RFC 4364  — BGP/MPLS IP Virtual Private Networks (VPNs)
 RFC 4456  — BGP Route Reflection (obsoletes 2796)
 RFC 4760  — Multiprotocol Extensions for BGP-4 (MP-BGP)
 RFC 5065  — Autonomous System Confederations for BGP
 RFC 5575  — Dissemination of Flow Specification Rules (Flowspec)
 RFC 6286  — Autonomous-System-Wide Unique BGP Identifier
 RFC 6793  — BGP Support for Four-Octet Autonomous System (AS) Numbers
 RFC 7311  — The PMSI Tunnel Attribute
 RFC 7432  — BGP MPLS-Based Ethernet VPN (EVPN)
 RFC 7606  — Revised Error Handling for BGP UPDATE Messages
 RFC 7911  — Advertisement of Multiple Paths in BGP (ADD-PATH)
 RFC 7938  — Use of BGP for Routing in Large-Scale Data Centers
 RFC 8092  — BGP Large Communities Attribute
 RFC 8205  — BGPsec Protocol Specification
 RFC 9003  — Extended BGP Administrative Shutdown Communication
 RFC 9072  — Extended Optional Parameters Length for BGP OPEN
 RFC 9234  — Route Leak Prevention and Detection
```

**The Core Design Philosophy:** BGP is a *path-vector* protocol. Unlike distance-vector protocols (RIP) that only advertise distance (hop count), or link-state protocols (OSPF/IS-IS) that flood the entire topology, BGP advertises the full AS-PATH. This solves loop detection trivially: if your own AS number appears in the path, reject it. It also enables *policy* — every AS can apply policy based on the full path.

---

## 2. BGP Fundamentals — Mental Model

### 2.1 The Three Tables

Every BGP speaker maintains three distinct tables:

```
┌─────────────────────────────────────────────────────────────┐
│                      BGP Speaker                            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │  Adj-RIB-In  │    │   Loc-RIB    │    │  Adj-RIB-Out │  │
│  │              │    │  (Best Path  │    │              │  │
│  │ Per-neighbor │───▶│   Selected)  │───▶│ Per-neighbor │  │
│  │ raw received │    │              │    │ after outbound│  │
│  │   prefixes   │    │  Main BGP    │    │    policy    │  │
│  │              │    │  table       │    │              │  │
│  └──────────────┘    └──────┬───────┘    └──────────────┘  │
│                             │                               │
│                      Inbound Policy                         │
│                      applied here                          │
│                             │                               │
│                      ┌──────▼───────┐                       │
│                       │  FIB / RIB  │  ← Forwarding Table   │
│                       │  (kernel)   │    programmed via      │
│                       └─────────────┘    Netlink             │
└─────────────────────────────────────────────────────────────┘
```

- **Adj-RIB-In**: Raw NLRI received from each peer, before any local policy. In FRR, stored in memory as `struct bgp_adj_in`.
- **Loc-RIB**: The best path table after running the decision process. This is the "BGP table" you see with `show ip bgp`.
- **Adj-RIB-Out**: What you actually advertise to each peer after outbound policy. In FRR, computed on-demand or cached per `struct peer`.

### 2.2 Autonomous Systems

An **Autonomous System (AS)** is a collection of IP prefixes under a single administrative domain with a single routing policy, identified by a 16-bit (legacy) or 32-bit (RFC 6793) ASN.

```
16-bit ASNs:  0 – 65535
  Public:       1 – 64495
  Reserved:  64496 – 64511  (documentation, RFC 5398)
  Private:   64512 – 65534  (RFC 6996)
  Reserved:  65535

32-bit ASNs:  0 – 4294967295 (0 to 2^32 - 1)
  Public:       0.0 – 64495.65535 (dotted notation) 
  Private:  64512.0 – 65534.65535
  Also:      4200000000 – 4294967294 (private, RFC 6996)

Dotted notation (asdot+):  65536 = 1.0, 131072 = 2.0
```

When 32-bit ASNs are used with peers that only support 16-bit, the AS_TRANS value (23456) is used in AS_PATH and the real 4-byte ASN is carried in AS4_PATH and AS4_AGGREGATOR attributes.

### 2.3 BGP Session Types

```
eBGP (External BGP):
  - Between routers in DIFFERENT autonomous systems
  - Typically directly connected (TTL=1 by default)
  - AD (Administrative Distance) = 20 in Cisco/FRR
  - AS_PATH is prepended with local AS on advertisement
  - NEXT_HOP is set to the advertising router's interface IP

iBGP (Internal BGP):
  - Between routers in the SAME autonomous system
  - Typically over loopback addresses (multi-hop)
  - AD = 200 in Cisco/FRR
  - AS_PATH is NOT modified on iBGP advertisement
  - NEXT_HOP is NOT changed by default (iBGP next-hop behavior)
  - Full mesh OR route reflectors OR confederations required
  - Split-horizon rule: routes learned from iBGP not re-advertised to iBGP
```

### 2.4 TCP Foundation

BGP runs over TCP port 179. This is fundamental to understanding BGP behavior:

- **Reliability**: TCP guarantees ordered, reliable delivery — BGP does not need its own retransmission
- **Session**: BGP has a persistent TCP session; loss of TCP = loss of BGP session = routes withdrawn
- **Active/Passive**: One side must listen (passive) on port 179; the other connects (active). Both sides can attempt simultaneously — collision detection uses BGP ID comparison
- **Keepalives**: BGP sends KEEPALIVE messages (not TCP keepalives) every Hold-Time/3 seconds
- **MD5 Authentication**: TCP MD5 (RFC 2385) is used for BGP session security — the kernel signs/verifies TCP segments

```
BGP TCP Session Establishment:

  Router A (ASN 65001)          Router B (ASN 65002)
  192.168.1.1                   192.168.1.2

       TCP SYN ────────────────────────────▶
       ◀──────────────────────────── TCP SYN-ACK
       TCP ACK ────────────────────────────▶
       [TCP session established on port 179]
       
       BGP OPEN ───────────────────────────▶
       ◀─────────────────────────── BGP OPEN
       BGP KEEPALIVE ──────────────────────▶
       ◀────────────────────────── BGP KEEPALIVE
       [BGP session: ESTABLISHED]
       
       BGP UPDATE (prefixes) ──────────────▶
       BGP UPDATE (prefixes) ◀─────────────
       
       BGP KEEPALIVE (every Hold-Time/3) ──▶  (periodic)
```

---

## 3. BGP Message Formats (Wire Level)

### 3.1 BGP Message Header (RFC 4271 Section 4.1)

Every BGP message begins with a fixed 19-byte header:

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                  Marker (16 octets, all 0xFF)                 |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Total Length         |    Type       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Fields:
  Marker   (128 bits): All bits set to 1. Used for synchronization
                       and compatibility detection.
  Length   (16 bits):  Total message length including header.
                       19 (header only) to 4096 bytes.
                       Extended: up to 65535 with RFC 8654.
  Type     (8 bits):   1 = OPEN
                       2 = UPDATE
                       3 = NOTIFICATION
                       4 = KEEPALIVE
                       5 = ROUTE-REFRESH (RFC 2918)
```

### 3.2 OPEN Message (RFC 4271 Section 4.2)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  [19-byte BGP header: Marker + Length + Type=1]               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Version    |     My Autonomous System      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Hold Time           |         BGP Identifier        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         BGP Identifier (cont) |Opt Param Len  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Optional Parameters (variable) ...                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Fields:
  Version          (8 bits):  BGP version = 4
  My AS            (16 bits): Sender's ASN (or AS_TRANS=23456 for 4-byte ASN)
  Hold Time        (16 bits): Proposed hold time in seconds.
                               0 = no hold timer. Minimum 3 seconds.
                               Negotiated to min(local, peer).
  BGP Identifier   (32 bits): Router ID. Usually highest loopback IP.
                               Must be unique within the AS.
  Opt Param Len    (8 bits):  Length of Optional Parameters field.

Optional Parameters Format:
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Param Type   |  Param Length | Param Value ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

  Type 2 = Capabilities Advertisement (RFC 5492)
  
Capability TLV:
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Cap Code     |  Cap Length   | Cap Value ...
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Common Capabilities:
  Code 1  = Multiprotocol Extensions (MP-BGP, RFC 4760)
            Value: AFI (2 bytes) + Reserved (1 byte) + SAFI (1 byte)
            AFI=1 SAFI=1  → IPv4 Unicast
            AFI=1 SAFI=4  → IPv4 Labeled Unicast (MPLS)
            AFI=1 SAFI=128→ IPv4 VPN (L3VPN)
            AFI=2 SAFI=1  → IPv6 Unicast
            AFI=25 SAFI=70→ EVPN
  Code 2  = Route Refresh (RFC 2918)
  Code 5  = Extended Next Hop Encoding (RFC 8950)
  Code 64 = Graceful Restart (RFC 4724)
  Code 65 = 4-octet AS Number Support (RFC 6793)
            Value: 4-byte ASN
  Code 69 = ADD-PATH (RFC 7911)
            Value: AFI(2)+SAFI(1)+Send/Receive(1)
  Code 70 = Enhanced Route Refresh (RFC 7313)
  Code 71 = Long-Lived Graceful Restart (LLGR)
```

### 3.3 UPDATE Message (RFC 4271 Section 4.3)

The UPDATE message is the workhorse of BGP — it carries route advertisements and withdrawals.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  [19-byte BGP header: Marker + Length + Type=2]               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Withdrawn Routes Length (2B) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Withdrawn Routes (variable) ...                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Total Path Attribute Length  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Path Attributes (variable) ...                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Network Layer Reachability Information (NLRI, variable) ...  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Withdrawn Routes and NLRI use the same encoding:
  +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+-+
  |  Prefix Len   |  | Prefix (ceil(   |
  |  (8 bits)     |  |  PrefixLen/8)   |
  +-+-+-+-+-+-+-+-+  +-+-+-+-+-+-+-+-+-+
  
  Example: 192.168.1.0/24
  Length = 24 (0x18)
  Prefix = 0xC0 0xA8 0x01 (only 3 bytes needed for /24)
  
  Example: 10.0.0.0/8  
  Length = 8 (0x08)
  Prefix = 0x0A (only 1 byte needed for /8)
  
  Example: 0.0.0.0/0 (default route)
  Length = 0 (0x00)
  Prefix = (empty)

Path Attribute TLV:
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Attr Flags    | Attr Type     | Attr Length   |  <- if length < 256
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-++-+-+-+-+-+-+-+
| Attr Flags    | Attr Type     | Attr Length (2 bytes)         |  <- Extended-length
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Attribute Value (variable) ...                                |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Attribute Flags byte:
  Bit 0 (high): Optional   (0=well-known, 1=optional)
  Bit 1:        Transitive (0=non-transitive, 1=transitive)
  Bit 2:        Partial    (0=complete, 1=partial — used for optional transitive)
  Bit 3:        Ext-Length (0=1-byte length, 1=2-byte length)
  Bits 4-7:     Unused (must be 0)
```

### 3.4 NOTIFICATION Message (RFC 4271 Section 4.5)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  [19-byte BGP header: Marker + Length + Type=3]               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Error Code   |  Error Sub.   |  Data (variable) ...          
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+...

Error Codes and Subcodes:
  1 = Message Header Error
      1: Connection Not Synchronized
      2: Bad Message Length
      3: Bad Message Type
  2 = OPEN Message Error
      1: Unsupported Version Number (data = supported version)
      2: Bad Peer AS
      3: Bad BGP Identifier
      4: Unsupported Optional Parameter
      6: Unacceptable Hold Time
      7: Unsupported Capability (RFC 5492)
  3 = UPDATE Message Error
      1: Malformed Attribute List
      2: Unrecognized Well-Known Attribute
      3: Missing Well-Known Attribute
      4: Attribute Flags Error
      5: Attribute Length Error
      6: Invalid ORIGIN Attribute
      8: Invalid NEXT_HOP Attribute
      9: Optional Attribute Error
      10: Invalid Network Field
      11: Malformed AS_PATH
  4 = Hold Timer Expired
  5 = Finite State Machine Error (RFC 6608)
      1: Unexpected Message in OpenSent State
      2: Unexpected Message in OpenConfirm State
      3: Unexpected Message in Established State
  6 = Cease (RFC 4486)
      1: Maximum Number of Prefixes Reached
      2: Administrative Shutdown (can carry message, RFC 9003)
      3: Peer De-configured
      4: Administrative Reset
      5: Connection Rejected
      6: Other Configuration Change
      7: Connection Collision Resolution
      8: Out of Resources
  7 = ROUTE-REFRESH Message Error (RFC 7313)
```

### 3.5 KEEPALIVE Message

```
The KEEPALIVE is simply a 19-byte BGP header with Type=4 and no body:

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|         Marker (16 bytes, all 0xFF)                           |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Length = 19 (0x00 0x13)    |  Type = 4 (0x04)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Hex representation:
  FF FF FF FF FF FF FF FF  FF FF FF FF FF FF FF FF
  00 13 04
```

### 3.6 ROUTE-REFRESH Message (RFC 2918)

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  [19-byte BGP header: Type=5]                                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           AFI             | Res |       SAFI              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+----+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  AFI (16 bits) + Reserved (8 bits) + SAFI (8 bits)
  
Meaning: "Please re-send me all routes for this AFI/SAFI"
Used after policy changes so you can reprocess without session reset.
```

### 3.7 Complete UPDATE Example — Wire Bytes Annotated

```
Advertising 10.1.0.0/16 with ORIGIN=IGP, AS_PATH=65001, NEXT_HOP=192.168.1.1,
MED=100, LOCAL_PREF=100

Hex dump (with annotations):

Header:
  FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF  <- Marker (16 bytes)
  00 3B                                            <- Length = 59 bytes
  02                                               <- Type = UPDATE

Withdrawn Routes Length:
  00 00                                            <- No withdrawals

Total Path Attributes Length:
  00 1C                                            <- 28 bytes of attributes

Path Attribute 1: ORIGIN
  40                  <- Flags: 0100 0000 = well-known, transitive
  01                  <- Type = 1 (ORIGIN)
  01                  <- Length = 1
  00                  <- Value = 0 (IGP)

Path Attribute 2: AS_PATH
  40                  <- Flags: well-known, transitive
  02                  <- Type = 2 (AS_PATH)
  06                  <- Length = 6
  02                  <- Segment type = AS_SEQUENCE
  01                  <- Number of ASes = 1
  00 00 FD E9         <- ASN 65001 (4-byte encoding, RFC 6793 not used here)
                         Note: 16-bit encoding would be: FD E9

  Actually with 16-bit ASNs:
  40 02 04 02 01 FD E9  (4 bytes: type=SEQ, count=1, as=65001)

Path Attribute 3: NEXT_HOP
  40                  <- Flags: well-known, transitive
  03                  <- Type = 3 (NEXT_HOP)
  04                  <- Length = 4
  C0 A8 01 01         <- 192.168.1.1

Path Attribute 4: MULTI_EXIT_DISC
  80                  <- Flags: 1000 0000 = optional, non-transitive
  04                  <- Type = 4 (MED)
  04                  <- Length = 4
  00 00 00 64         <- Value = 100

Path Attribute 5: LOCAL_PREF
  40                  <- Flags: well-known, transitive
  05                  <- Type = 5 (LOCAL_PREF)
  04                  <- Length = 4
  00 00 00 64         <- Value = 100

NLRI:
  10                  <- Prefix length = 16
  0A 01               <- Prefix = 10.1.0.0/16 (only first 2 bytes needed)
```

---

## 4. BGP Finite State Machine (FSM)

The BGP FSM is defined in RFC 4271 Section 8. It governs state transitions based on events (TCP events, BGP message events, timer events).

### 4.1 States and Transitions

```
                         ┌─────────────────────────────────────────────────┐
                         │              BGP FSM States                     │
                         └─────────────────────────────────────────────────┘

    ┌──────────┐  ManualStart/     ┌──────────────┐  TCP connection    ┌──────────┐
    │          │  AutomaticStart   │              │  initiated         │          │
    │   IDLE   │──────────────────▶│   CONNECT    │───────────────────▶│  ACTIVE  │
    │          │                   │              │                    │          │
    └──────────┘                   └──────┬───────┘                   └────┬─────┘
          ▲                               │                                │
          │ NotifMsg/                     │ TCP connection                  │ TCP connection
          │ Hold Timer Exp/               │ confirmed                       │ confirmed
          │ TcpConnectionFails            ▼                                │
          │                       ┌──────────────┐                        │
          └───────────────────────│   OPENSENT   │◀───────────────────────┘
          ▲                       │              │
          │                       └──────┬───────┘
          │ NotifMsg/                     │ BGP OPEN
          │ HoldTimerExpired              │ received and valid
          │ OpenMsg Error                 ▼
          │                       ┌──────────────┐
          └───────────────────────│ OPENCONFIRM  │
          ▲                       │              │
          │ NotifMsg/             └──────┬───────┘
          │ HoldTimerExpired             │ KEEPALIVE received
          │                              ▼
          │                       ┌──────────────┐
          └───────────────────────│ ESTABLISHED  │
                                  │              │
                                  └──────────────┘
```

### 4.2 Detailed State Descriptions

**IDLE**
- Initial state on startup or after session failure
- BGP is not attempting any connections
- Resources are released
- ConnectRetryCounter is not zero → timer before retry
- `AutomaticStartWithPassiveTcpEstablishment` can move to ACTIVE (listen-only)

**CONNECT**
- Initiating a TCP connection
- Waiting for TCP session to complete
- ConnectRetryTimer running
- If TCP succeeds → send OPEN → move to OPENSENT
- If TCP fails → move to ACTIVE
- If ConnectRetry timer expires → restart TCP, stay in CONNECT

**ACTIVE**
- TCP failed; trying again
- BGP is actively trying to acquire a peer by listening AND initiating
- If TCP established → send OPEN → OPENSENT
- If ConnectRetry timer expires → move back to CONNECT

**OPENSENT**
- TCP established, local OPEN sent
- Waiting for remote OPEN
- If valid OPEN received → send KEEPALIVE → move to OPENCONFIRM
- Hold timer started (typically initial value 240 seconds or from OPEN)
- Checks:
  - Version must be 4
  - My AS must match configured remote AS
  - BGP ID must be valid
  - Capabilities negotiated

**OPENCONFIRM**
- Both OPENs exchanged
- Waiting for KEEPALIVE
- HoldTimer running
- KeepaliveTimer started (sends periodic KEEPALIVEs)
- If KEEPALIVE received → ESTABLISHED
- If NOTIFICATION received → IDLE

**ESTABLISHED**
- Fully operational session
- UPDATEs, KEEPALIVEs processed normally
- HoldTimer reset on each KEEPALIVE or UPDATE
- KeepaliveTimer fires → send KEEPALIVE
- NOTIFICATION or TCP close → IDLE with delay

### 4.3 Important FSM Events

```
Event  1: ManualStart
Event  2: ManualStop
Event  3: AutomaticStart
Event  4: ManualStart_with_PassiveTcpEstablishment
Event  5: AutomaticStart_with_PassiveTcpEstablishment
Event  6: AutomaticStart_with_DampPeerOscillations
Event  7: AutomaticStart_with_DampPeerOscillations_and_PassiveTcpEstablishment
Event  8: AutomaticStop
Event  9: ConnectRetryTimer_Expires
Event 10: HoldTimer_Expires
Event 11: KeepaliveTimer_Expires
Event 12: DelayOpenTimer_Expires
Event 13: IdleHoldTimer_Expires
Event 14: TcpConnection_Valid
Event 15: Tcp_CR_Invalid
Event 16: Tcp_CR_Acked / TcpConnectionConfirmed
Event 17: TcpConnectionFails
Event 18: BGPOpen
Event 19: BGPOpen with DelayOpenTimer running
Event 20: BGPHeaderErr
Event 21: BGPOpenMsgErr
Event 22: OpenCollisionDump
Event 23: NotifMsgVerErr
Event 24: NotifMsg
Event 25: KeepAliveMsg
Event 26: UpdateMsg
Event 27: UpdateMsgErr
```

### 4.4 Session Collision Detection

When two BGP speakers both try to actively open a connection to each other, two TCP connections are established simultaneously. BGP resolves this with collision detection:

```
Both routers initiate:

Router A (BGP-ID: 10.0.0.1)                 Router B (BGP-ID: 10.0.0.2)
    │                                              │
    │────── TCP SYN ──────────────────────────────▶│  Connection 1: A→B
    │◀───────────────────────────────── TCP SYN ───│  Connection 2: B→A
    │                                              │
    │────── BGP OPEN ─────────────────────────────▶│  on Connection 1
    │◀────────────────────────────────── BGP OPEN ─│  on Connection 2
    │                                              │
    Both routers: compare BGP Identifiers
    Higher ID (10.0.0.2) wins.
    The connection initiated by the LOWER ID is closed.
    
    Router A closes Connection 2 (B→A).
    Router B closes Connection 2 (B→A) too (same decision).
    
    Result: Connection 1 (A→B) survives.
```

### 4.5 BGP Timers

```
Timer                Default    Configurable?   Notes
──────────────────────────────────────────────────────────────────
HoldTime             90s        Yes             Negotiated to minimum
KeepaliveInterval    30s        Yes             = HoldTime/3
ConnectRetryTimer    120s       Yes             Before retry
MinRouteAdvertisement 30s       Yes (MRAI)      Minimum time between UPDATEs per prefix
IdleHoldTimer        variable   Yes             Exponential backoff for flapping peers
MinASOriginationInterval 15s    Yes             Before re-originating own routes
```

**MRAI (Minimum Route Advertisement Interval)**: Prevents excessive UPDATE flooding. For eBGP peers: 30s default. For iBGP: 5s. In modern DC BGP (RFC 7938), MRAI is typically set to 0 for fast convergence.

---

## 5. BGP Attributes — Complete Reference

BGP attributes are carried in UPDATE messages. They control path selection and policy.

### 5.1 Attribute Classification Matrix

```
Attribute            Type  Well-Known  Transitive  Mandatory  
──────────────────────────────────────────────────────────────
ORIGIN               1     Yes         Yes         Yes        
AS_PATH              2     Yes         Yes         Yes        
NEXT_HOP             3     Yes         Yes         Yes (IPv4) 
MULTI_EXIT_DISC      4     No          No          No         
LOCAL_PREF           5     Yes         No          No (iBGP)  
ATOMIC_AGGREGATE     6     Yes         Yes         No         
AGGREGATOR           7     No          Yes         No         
COMMUNITY            8     No          Yes         No         
ORIGINATOR_ID        9     No          No          No         
CLUSTER_LIST         10    No          No          No         
MP_REACH_NLRI        14    No          No          No (MP-BGP)
MP_UNREACH_NLRI      15    No          No          No (MP-BGP)
EXTENDED_COMMUNITIES 16    No          Yes         No         
AS4_PATH             17    No          Yes         No         
AS4_AGGREGATOR       18    No          Yes         No         
PMSI_TUNNEL          22    No          Yes         No         
TUNNEL_ENCAP         23    No          Yes         No         
TRAFFIC_ENGINEERING  24    No          Yes         No         
IPV6_EXT_COMMUNITIES 25    No          Yes         No         
AIGP                 26    No          No          No         
PE_DISTINGUISHER_LABELS 27 No          Yes         No         
BGP-LS               29    No          No          No         
LARGE_COMMUNITY      32    No          Yes         No         
BGP_PREFIX_SID       40    No          Yes         No         
ATTR_SET             128   No          Yes         No         
```

### 5.2 ORIGIN (Type 1)

```
Values:
  0 = IGP       — Network was learned via an interior routing protocol
                  or was statically configured. Most preferred.
  1 = EGP       — Learned via the old EGP protocol (obsolete but still valid)
  2 = INCOMPLETE — Learned via redistribution from another protocol (e.g., static,
                   connected, OSPF) that didn't set IGP. Least preferred.

Wire format:
  [Flags: 0x40][Type: 0x01][Length: 0x01][Value: 0x00|0x01|0x02]

In practice:
  - network command in FRR/IOS: ORIGIN=IGP
  - redistribute: ORIGIN=INCOMPLETE
  - You rarely change this manually but policy can set it
```

### 5.3 AS_PATH (Type 2)

```
AS_PATH contains a sequence of AS path segments. Each segment is:
  [Segment Type (1B)][Segment Length (1B)][AS numbers (2B or 4B each)]

Segment Types:
  1 = AS_SET       — Unordered set (used in aggregation)
  2 = AS_SEQUENCE  — Ordered list (normal BGP propagation)
  3 = AS_CONFED_SEQUENCE — Ordered set of confederation member AS numbers
  4 = AS_CONFED_SET      — Set of confederation member AS numbers

Example path: AS 65001 → AS 65002 → AS 65003 advertises to AS 65004
AS_PATH seen by AS 65004: [AS_SEQUENCE: 65003, 65002, 65001]
                           (leftmost = most recent)

Wire format (16-bit ASNs, path: 65003 65002 65001):
  02      ← AS_SEQUENCE type
  03      ← 3 ASes in segment
  FD EB   ← 65003
  FD EA   ← 65002
  FD E9   ← 65001

AS_PATH manipulation:
  - Prepending: Advertise with own ASN multiple times to make path look longer
  - Example: prepend 65001 twice → AS_PATH: [65001, 65001, 65001, 65003, 65002]
  - This makes the path less preferred (longer AS_PATH = worse in selection step 7)

4-byte AS wire format (RFC 6793) — same structure but 4 bytes per ASN:
  02      ← AS_SEQUENCE
  01      ← 1 AS
  00 00 FD E9   ← 65001 as 4-byte
```

### 5.4 NEXT_HOP (Type 3)

```
For IPv4 unicast, NEXT_HOP is a mandatory 4-byte IPv4 address:
  [Flags: 0x40][Type: 0x03][Length: 0x04][4-byte IP]

eBGP NEXT_HOP behavior:
  - Set to the advertising router's interface IP toward the peer
  - Peer can directly reach it (connected)

iBGP NEXT_HOP behavior:
  - NOT changed when re-advertising within AS (next-hop-self is off by default)
  - iBGP routers must have IGP reachability to eBGP next-hops
  - "next-hop-self" overrides this: RR or ABR sets NH to itself

Third-party NEXT_HOP (on multi-access networks):
  - When both peers are on the same subnet as the route originator
  - BGP can set NEXT_HOP to the originator directly
  - Optimization: traffic goes directly, not through BGP speaker

MP-BGP NEXT_HOP is in MP_REACH_NLRI (see below) — supports IPv6 and MPLS labels.
```

### 5.5 MULTI_EXIT_DISC / MED (Type 4)

```
MED is optional, non-transitive. It suggests to an external peer which 
entry point into your AS to use when there are multiple connections.

Wire format:
  [Flags: 0x80][Type: 0x04][Length: 0x04][4-byte unsigned integer]
  
  Lower MED = preferred

Rules:
  - Only compared between routes from the SAME neighboring AS (by default)
  - Not propagated to other ASes (non-transitive)
  - "bgp always-compare-med" in FRR allows comparison across ASes
  - "bgp deterministic-med" ensures consistent comparison
  - Missing MED treated as 0 (lowest, best) by some implementations
  - Missing MED treated as 2^32-1 (highest, worst) by others
  
Example:
                    ┌──────────────────┐
  AS 65001 ────────▶│ 10.0.0.1         │
  MED=100           │    AS 65002      │
  AS 65001 ────────▶│ 10.0.0.2         │
  MED=200           └──────────────────┘
  
  AS 65002 prefers entry point 10.0.0.1 (lower MED)
```

### 5.6 LOCAL_PREF (Type 5)

```
LOCAL_PREF is well-known, transitive within AS but NOT propagated to eBGP peers.
It is used to influence outbound traffic — which exit point leaves the AS.

Wire format:
  [Flags: 0x40][Type: 0x05][Length: 0x04][4-byte unsigned integer]
  
  Higher LOCAL_PREF = preferred. Default = 100.

Only sent in iBGP updates. Stripped before advertising to eBGP peers.

Example:
  AS 65001 has two connections to the Internet:
  
  Router A (NYC) → sets LOCAL_PREF=200 on routes learned from upstream
  Router B (LA)  → sets LOCAL_PREF=100 on routes learned from upstream
  
  All iBGP routers in AS 65001 prefer exit through Router A (higher LP).
  This makes NYC the preferred exit regardless of AS_PATH length.
```

### 5.7 ATOMIC_AGGREGATE (Type 6) and AGGREGATOR (Type 7)

```
ATOMIC_AGGREGATE (no value, just the flag):
  Set when a route was aggregated and the more-specific information was lost.
  Signals that the aggregate may hide more-specific paths.
  
AGGREGATOR (optional, transitive):
  [Flags: 0xC0][Type: 0x07][Length: 0x06][2-byte ASN][4-byte Router ID]
  With 4-byte ASNs: Length = 8, with 4-byte ASN
  
  Identifies the AS and router that performed the aggregation.
  
Example:
  10.0.0.0/8 aggregated from 10.1.0.0/24, 10.2.0.0/24, 10.3.0.0/24
  → ATOMIC_AGGREGATE present
  → AGGREGATOR = {AS 65001, Router 10.0.0.1}
```

### 5.8 COMMUNITY (Type 8, RFC 1997)

```
Standard community: 4 bytes = AS_number(2 bytes) : value(2 bytes)
Multiple communities can be in one attribute.

Wire format:
  [Flags: 0xC0][Type: 0x08][Length: N*4][Community 1][Community 2]...
  
Well-known Communities:
  0xFFFF0000 = NO_EXPORT        — Don't advertise to eBGP peers
  0xFFFF0001 = NO_ADVERTISE     — Don't advertise to ANY peer
  0xFFFF0002 = NO_EXPORT_SUBCONFED — Don't advertise outside confederation
  0xFFFF0003 = NOPEER (RFC 3765) — Don't re-advertise to peers (non-paying)

String notation: 65001:100 = 0xFDE90064

Usage examples:
  65001:100  → Customer route
  65001:200  → Peer route  
  65001:300  → Transit route
  65001:666  → Blackhole community (commonly used)
  65001:0    → Prepend this route N times when advertising to AS X

These are conventions — meaning is operator-defined.
```

### 5.9 ORIGINATOR_ID (Type 9) and CLUSTER_LIST (Type 10)

```
Used by Route Reflectors (RFC 4456):

ORIGINATOR_ID (optional, non-transitive):
  [Flags: 0x80][Type: 0x09][Length: 0x04][4-byte Router ID]
  Set by RR to the BGP ID of the route originator (the client that originated).
  Prevents routing loops: if router receives route with its own ID as ORIGINATOR_ID,
  it rejects the route.

CLUSTER_LIST (optional, non-transitive):
  [Flags: 0x80][Type: 0x0A][Length: N*4][Cluster ID 1][Cluster ID 2]...
  Each RR prepends its Cluster ID when reflecting routes.
  Loop detection: if my Cluster ID is in the CLUSTER_LIST, discard.
```

### 5.10 MP_REACH_NLRI (Type 14) and MP_UNREACH_NLRI (Type 15)

```
Multiprotocol BGP extensions (RFC 4760) — carry non-IPv4 reachability.

MP_REACH_NLRI:
  [Flags: 0x80][Type: 0x0E][Length][
    AFI (2B) | SAFI (1B) |
    Next Hop Length (1B) | Next Hop Address (var) |
    Reserved (1B = 0x00) |
    NLRI (variable, same prefix encoding as IPv4 NLRI)
  ]

Example: IPv6 prefix 2001:db8::/32, NH=fe80::1:2:3:4
  AFI = 0x0002 (IPv6)
  SAFI = 0x01 (Unicast)
  NH Length = 0x10 (16 bytes for IPv6)
  NH = 0x20 0x01 0x0d 0xb8 ... (full IPv6 address)
  NLRI:
    0x20 (= 32, prefix len)
    0x20 0x01 0x0d 0xb8 (first 4 bytes of 2001:db8::/32)

For BGP Unnumbered (RFC 5549):
  AFI=1 (IPv4) SAFI=1 (Unicast) but NH is IPv6 link-local
  This allows IPv4 routes to be advertised with IPv6 next-hops
  (The "extended next hop" capability must be negotiated, RFC 8950)

MP_UNREACH_NLRI:
  [AFI (2B) | SAFI (1B) | Withdrawn NLRI (variable)]
  Used to withdraw MP-BGP routes (no next hop needed).

EVPN (AFI=25, SAFI=70) NLRI encoding is different:
  Each NLRI = [Route Type (1B)][Length (1B)][Type-specific fields]
```

### 5.11 EXTENDED COMMUNITIES (Type 16, RFC 4360)

```
8 bytes per community. More structure than standard communities.

Wire format:
  [Flags: 0xC0][Type: 0x10][Length: N*8][Community 1 (8B)]...

Extended Community structure:
  Byte 0: Type high
    Bits 7-6: IANA authority
      00 = IANA-assigned (2-octet AS specific)
      01 = IANA-assigned (IPv4-address specific)
      10 = IANA-assigned (4-octet AS specific)
      11 = Experimental
    Bit 5: Transitive (0=transitive, 1=non-transitive)
    Bits 4-0: Sub-type high
  Byte 1: Type low / sub-type
  Bytes 2-7: Value

Important Extended Community Types:
  Route Target (RT): 0x00 0x02 (2-byte AS) or 0x01 0x02 (IPv4) or 0x02 0x02 (4-byte AS)
    Used in MPLS VPN and EVPN to identify which VRF a route belongs to
    Format: ASN:value or IP:value
    Example: 65001:100 = 0x00 0x02 0xFD 0xE9 0x00 0x00 0x00 0x64
    
  Route Origin (RO): 0x00 0x03 / 0x01 0x03 / 0x02 0x03
    Identifies the originator of the VPN route
    
  BGP Encapsulation: 0x03 0x0C
    Specifies tunnel type for route (e.g., VXLAN, NVGRE, MPLSoGRE)
    Value byte 7: 1=L2TPv3, 2=GRE, 7=IP-in-IP, 8=VXLAN, 9=NVGRE, 10=MPLS, 11=MPLS-in-GRE
    
  EVPN ESI Label: 0x06 0x01
  EVPN ES-Import RT: 0x06 0x02
  MAC Mobility: 0x06 0x00
  
  Color Community (SR Policy): 0x03 0x0B
  
  BGP Cost Community: 0x43 0x01  (non-standard, Cisco)
  
  OSPF Route Type: 0x03 0x06
  
  Traffic Rate: 0x80 0x06  (Flowspec action)
  Traffic Action: 0x80 0x07
  Redirect VRF: 0x80 0x08
  Traffic Marking: 0x80 0x09
```

### 5.12 LARGE COMMUNITIES (Type 32, RFC 8092)

```
12 bytes per community: Global Administrator (4B) + Local Data 1 (4B) + Local Data 2 (4B)

Wire format:
  [Flags: 0xC0][Type: 0x20][Length: N*12][Community 1 (12B)]...

String notation: ASN:LD1:LD2
  65001:1:100 = "Global AS 65001, meaning: type 1, value 100"
  
Advantages over standard:
  - Supports 4-byte ASNs natively (no truncation)
  - Much larger value space
  - Clear structure: who:what:value
  
Example usage:
  65001:1:1   → Route learned from customer in region 1
  65001:2:50  → Set LOCAL_PREF to 50
  65001:3:1   → Prepend once to all peers
  65001:4:65002 → Don't advertise to AS 65002
```

---

## 6. BGP Decision Process (Path Selection)

The BGP decision process selects the single best path for each prefix. It runs the following steps **in order**, stopping as soon as a tiebreaker is found.

```
BGP Best Path Selection (RFC 4271 Section 9.1):

For each prefix, compare all candidate paths:

Step 0:  Validity Check (pre-decision filter)
         ├─ Route is accessible (NEXT_HOP is reachable via IGP)
         └─ Route passes inbound policy

Step 1:  Prefer route with highest WEIGHT
         (Cisco-proprietary, local to router, not advertised)
         FRR equivalent: "weight" command on peer

Step 2:  Prefer route with highest LOCAL_PREF
         Default = 100
         Higher = better
         "bgp default local-preference <value>"

Step 3:  Prefer locally originated routes
         (network statement > aggregate > redistribute)
         Locally originated > received from peer

Step 4:  Prefer SHORTEST AS_PATH
         Count segments (AS_SET counts as 1 regardless of members)
         "bgp bestpath as-path ignore" to skip this step
         Confederation segments (AS_CONFED_*) excluded from count

Step 5:  Prefer lowest ORIGIN
         IGP (0) > EGP (1) > INCOMPLETE (2)

Step 6:  Prefer lowest MED
         Only compared if paths from same neighboring AS (default)
         "bgp always-compare-med" changes this
         Missing MED treatment varies by implementation

Step 7:  Prefer eBGP routes over iBGP routes
         External (eBGP) > Internal (iBGP)
         (confederation eBGP > confederation iBGP > iBGP)

Step 8:  Prefer route with lowest IGP cost to NEXT_HOP
         Hot-potato routing: exit AS as quickly as possible
         Ties in IGP cost → multiple equal-cost paths possible (ECMP)

Step 9:  If "bgp bestpath as-path multipath-relax" configured:
         Allow ECMP even if AS paths differ

Step 10: Prefer oldest received route (for eBGP paths)
         Stability preference: avoid route flap
         "bgp bestpath compare-routerid" disables this

Step 11: Prefer route from peer with lowest BGP Router ID (BGP Identifier)
         Tiebreaker using router identity

Step 12: If paths have ORIGINATOR_ID, prefer lowest ORIGINATOR_ID

Step 13: Prefer route with shortest CLUSTER_LIST length

Step 14: Prefer route from peer with lowest neighbor IP address
         Final tiebreaker — deterministic but arbitrary

Winner = BEST PATH → installed in Loc-RIB → propagated to peers
```

### 6.1 Understanding Hot-Potato vs Cold-Potato Routing

```
Hot-Potato (default IGP metric comparison):
  AS 65001 exits toward destination via the nearest exit point.
  Traffic leaves AS 65001 ASAP, even if this increases total path length.
  
  ┌─────────────────────────────────┐
  │         AS 65001                │
  │  NYC────────────────────LA      │
  │   │                      │      │
  │   ▼                      ▼      │
  │  eBGP Peer A          eBGP Peer B│
  └─────────────────────────────────┘
  
  Traffic from NYC → Destination:
  Hot-potato: Use Peer A (NYC exit, lower IGP cost to NEXT_HOP)
  Cold-potato: Carry traffic internally to LA, exit via Peer B if Peer B
               is closer to the destination (requires policy override)

Cold-Potato:
  Achieved by using LOCAL_PREF to override the IGP metric comparison.
  Common in ISP peering where you want to minimize transit costs.
```

---

## 7. iBGP vs eBGP — Deep Dive

### 7.1 The Split-Horizon Problem and Full Mesh Requirement

iBGP has a fundamental rule: **routes learned from an iBGP peer must not be re-advertised to another iBGP peer**. This prevents routing loops within an AS (unlike eBGP where AS_PATH provides loop prevention).

```
Split-horizon in iBGP:

  R1 ──iBGP── R2 ──iBGP── R3
  
  R1 learns 10.0.0.0/8 from eBGP
  R1 advertises 10.0.0.0/8 to R2 via iBGP ✓
  R2 CANNOT re-advertise 10.0.0.0/8 to R3 via iBGP ✗
  
  Therefore: R3 never learns 10.0.0.0/8
  
Solution: Full iBGP mesh
  Every iBGP router peers with every other iBGP router.
  
  For N routers: N*(N-1)/2 sessions
  10 routers = 45 sessions
  100 routers = 4950 sessions  ← Not scalable
  
  Alternatives: Route Reflection, Confederations (see Section 8)
```

### 7.2 NEXT_HOP Behavior Differences

```
eBGP:  
  Advertising router ALWAYS changes NEXT_HOP to its own interface IP.

iBGP (default):  
  NEXT_HOP is NOT changed. This is the iBGP next-hop behavior.
  
  Problem: iBGP router learns route with NEXT_HOP = eBGP peer's IP.
  That eBGP peer's IP must be reachable via IGP for the route to be usable.
  
  ┌────────────────────────────────────────────┐
  │         AS 65001 (iBGP full mesh)          │
  │                                            │
  │  R1(eBGP peer: 203.0.113.1)                │
  │    │ learns 8.8.8.0/24, NH=203.0.113.1     │
  │    │                                        │
  │    ├──iBGP──▶ R2: sees NH=203.0.113.1      │
  │    │                  R2 must reach 203.x   │
  │    │                  via IGP (R1's loopback)│
  │    └──iBGP──▶ R3: same problem             │
  │                                             │
  └────────────────────────────────────────────┘
  
"next-hop-self":
  Forces iBGP speaker to set NEXT_HOP to itself when advertising to iBGP peers.
  Eliminates need for IGP to carry eBGP peer IPs.
  Standard practice on border routers.

"next-hop-unchanged":
  On eBGP sessions: don't change NEXT_HOP even for eBGP.
  Used in route server configurations (IXPs).
```

### 7.3 AS_PATH in iBGP vs eBGP

```
eBGP advertisement:
  AS 65001 router prepends "65001" to AS_PATH before sending to eBGP peer.
  AS_PATH grows with each AS hop.

iBGP advertisement:
  AS_PATH is NOT modified.
  The AS number is NOT prepended within the AS.
  This allows the receiving iBGP router to know the FULL external AS_PATH.

LOCAL_PREF:
  Added by the first iBGP router (border) when receiving from eBGP.
  Propagated to all iBGP peers unchanged.
  Removed before advertising to eBGP peers.

MED:
  Received from eBGP peers.
  Propagated to iBGP peers unchanged (for comparison within AS).
  NOT propagated to other eBGP peers (non-transitive).
```

---

## 8. BGP Route Reflection and Confederations

### 8.1 Route Reflection (RFC 4456)

Route reflection eliminates the full iBGP mesh requirement. One or more routers act as Route Reflectors (RR). Clients peer only with the RR (and possibly other non-clients).

```
Cluster design:

  ┌──────────────────────────────────────────┐
  │              AS 65001                    │
  │                                          │
  │   Cluster 1          Cluster 2           │
  │ ┌──────────────┐   ┌──────────────┐      │
  │ │    RR1       │   │    RR2       │      │
  │ │  (10.0.0.1)  │   │  (10.0.0.2)  │      │
  │ │   /   \      │   │   /   \      │      │
  │ │ C1     C2    │   │ C3     C4    │      │
  │ │(10.1.1) (10.1.2) │ (10.2.1) (10.2.2)  │
  │ └──────────────┘   └──────────────┘      │
  │          │                │              │
  │          └──────iBGP──────┘              │
  │          (RR1 and RR2 peer with each other)
  └──────────────────────────────────────────┘

RR Advertisement Rules:
  1. Routes from eBGP peers → advertise to ALL iBGP peers (clients AND non-clients)
  2. Routes from RR clients → reflect to ALL other clients AND non-clients
  3. Routes from non-client iBGP peers → advertise to ALL clients only
     (non-clients still need full mesh among themselves or their own RR)

Loop Prevention:
  ORIGINATOR_ID: Set to BGP-ID of route originator (first time reflected).
                 If I receive a route with my own BGP-ID as ORIGINATOR_ID → discard.
  
  CLUSTER_LIST: Each RR prepends its CLUSTER_ID when reflecting.
                If I receive a route with my own CLUSTER_ID in the list → discard.

Cluster ID:
  Set per RR. Default = Router ID.
  Can be set explicitly: "bgp cluster-id X.X.X.X"
  For redundancy: two RRs in same cluster should have SAME cluster ID.
  This way CLUSTER_LIST deduplication works correctly.
```

### 8.2 RR Limitations and Optimal Design

```
RR is NOT policy-transparent:
  The RR runs its own decision process and only reflects the BEST PATH.
  Clients only see what the RR considers best — they can't do independent path selection.
  
  Solution: ADD-PATH (RFC 7911) — RR can advertise multiple paths per prefix.

Suboptimal routing problem:
  Client C1 (close to RR1) learns a route via RR1.
  The best path from RR1's perspective may not be best from C1's perspective.
  
  Mitigation: Place RRs on routers with similar topology position as clients.
              "BGP optimal route reflection" (Cisco/Nokia feature).

Hierarchical RR:
  RR1 is a client of RR0 (super-reflector).
  Used in very large ASes (Tier-1 ISPs).
  
  RR0 (Super)
  ├── RR1 (client of RR0, RR for Cluster 1)
  │   ├── C1, C2, C3
  └── RR2 (client of RR0, RR for Cluster 2)
      ├── C4, C5, C6
```

### 8.3 Confederations (RFC 5065)

Confederations split a large AS into sub-ASes (member ASes). From outside, the entire confederation looks like a single AS.

```
Example: AS 65001 is externally visible. Internally split into:
  Sub-AS 65101, Sub-AS 65102, Sub-AS 65103

                    ┌─────────────────────────────────────────────────┐
  External AS 65000 │                 AS 65001 (Confederation)        │ External AS 65002
         │          │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │         │
         └──eBGP────┼─▶│ Sub-AS   │  │ Sub-AS   │  │ Sub-AS   │──────┼─eBGP───▶│
                    │  │ 65101    │  │ 65102    │  │ 65103    │      │
                    │  │  R1  R2  │  │  R3  R4  │  │  R5  R6  │      │
                    │  └──┬───────┘  └──┬───────┘  └──┬───────┘      │
                    │     │Confed-eBGP  │Confed-eBGP  │               │
                    └─────────────────────────────────────────────────┘

Between sub-ASes: Confederation eBGP (confed-eBGP)
  - NEXT_HOP is updated (like regular eBGP)
  - LOCAL_PREF is preserved (unlike regular eBGP)
  - MED is preserved
  - AS_PATH uses AS_CONFED_SEQUENCE for sub-AS path
  - Confederation AS numbers stripped from AS_PATH before advertising externally

Externally AS_PATH looks like: [65001, 65000_prepend]
Internally AS_PATH looks like: [AS_CONFED_SEQ: 65103 65102, AS_SEQ: 65000]

Benefits over RR:
  - Full eBGP-style loop prevention within the confederation
  - True policy can be applied at sub-AS boundaries
  
Drawbacks:
  - More complex configuration
  - Still need full mesh or RRs within each sub-AS
  - Operational complexity
  - Rarely used in modern networks (RR with ADD-PATH preferred)
```

---

## 9. BGP Communities (Standard, Extended, Large)

### 9.1 Community Use Cases and Patterns

```
Communities are the "tags" of BGP routing policy. They allow:
1. Coloring routes with metadata
2. Triggering policy actions at other routers
3. Customer-controlled routing
4. Blackhole signaling
5. Traffic engineering

Common Industry Patterns:

Informational communities (read-only tags):
  65001:100  → Learned from customer
  65001:200  → Learned from peer  
  65001:300  → Learned from upstream provider
  65001:400  → Originated locally
  
Action communities (trigger policy):
  65001:666  → Blackhole (set NH to null0, advertise to peers as /32)
  65001:1000 → No-export to any eBGP peer
  65001:2000 → Prepend 1x to all peers
  65001:2001 → Prepend 2x to all peers
  65001:2002 → Prepend 3x to all peers
  65001:3065002 → Prepend when advertising to AS 65002

Regional tagging:
  65001:101  → Customer in North America
  65001:102  → Customer in Europe
  65001:103  → Customer in Asia

FRR Community Configuration:
  ! Set community on received routes from customer
  route-map CUSTOMER_IN permit 10
    set community 65001:100
  
  ! Match on community and apply local-pref
  ip community-list standard CUSTOMER seq 5 permit 65001:100
  route-map SET_LOCPREF permit 10
    match community CUSTOMER
    set local-preference 200
  
  ! Blackhole matching
  ip community-list standard BLACKHOLE seq 5 permit 65001:666
  route-map BLACKHOLE_OUT permit 10
    match community BLACKHOLE
    set community no-export
    set ip next-hop 192.0.2.1  ! null route IP
```

### 9.2 Large Community Operations (RFC 8092)

```
Structure: Global_Administrator:Local_Data_1:Local_Data_2
           (32-bit)              (32-bit)       (32-bit)

This solves the ASN truncation problem in standard communities.
Standard community: only 16 bits for ASN → can't encode 4-byte ASNs.
Large community: full 32-bit ASN + two 32-bit fields.

Recommended encoding by RFC 8195:
  ASN:function:parameter

Functions (operator-defined):
  ASN:1:X   → Informational (origin X)
  ASN:2:X   → Action: set local-preference to X
  ASN:3:X   → Action: prepend X times
  ASN:4:X   → Action: don't advertise to ASN X
  ASN:5:X   → Action: only advertise to ASN X

Example FRR config:
  bgp large-community-list standard NO_EXPORT_TO_PEER seq 5 permit 65001:4:65002
  
  route-map EXPORT_TO_65002 deny 10
    match large-community NO_EXPORT_TO_PEER
  route-map EXPORT_TO_65002 permit 20
```

---

## 10. BGP in Data Centers — RFC 7938 and Clos Fabrics

### 10.1 The Data Center Fabric Problem

Traditional OSPF/ISIS-based DC networks had several problems at scale:
- OSPF/ISIS flooding with thousands of nodes causes CPU/memory issues
- Link-state databases are large and convergence is slow at scale
- Equal-Cost Multi-Path (ECMP) across all spines requires careful IGP tuning
- Operational model differs from WAN (no area design needed)
- Hard to express routing policy (communities, filtering)

RFC 7938 (2016) codified what hyperscalers had already been doing: running eBGP as the ONLY routing protocol in the data center.

### 10.2 Clos / Fat-Tree Topology

The Clos topology was invented by Charles Clos in 1953 for telephone switching. In DC networking it provides:
- Non-blocking forwarding if properly designed
- Linear scalability (add spine/super-spine for more bandwidth)
- All paths are equal-cost (perfect for ECMP)
- Simple, uniform design — no STP, no VLANs in the fabric

```
3-Tier Clos (Leaf-Spine-Super-Spine):

                ┌─────────────────────────────────────────────────────┐
  Tier 3        │  SS1     SS2     SS3     SS4  (Super-Spine)         │
  (Super-Spine) │   │  ╲  ╱  │     │  ╲  ╱  │                       │
                │   │   ╲╱   │     │   ╲╱   │                       │
                └───┼───╱╲───┼─────┼───╱╲───┼───────────────────────┘
                    │  ╱  ╲  │     │  ╱  ╲  │
                ┌───┼──────────────────────────┐
  Tier 2        │  SP1     SP2     SP3     SP4  │ (Spine)
  (Spine)       │   │╲    ╱│╲    ╱│╲    ╱│    │
                │   │ ╲  ╱ │ ╲  ╱ │ ╲  ╱ │    │
                └───┼──╲╱──┼──╲╱──┼──╲╱──┼───┘
                    │  ╱╲  │  ╱╲  │  ╱╲  │
                ┌───┼──────────────────────────┐
  Tier 1        │  L1      L2      L3      L4  │  (Leaf / ToR)
  (Leaf/ToR)    │  │       │       │       │   │
                └──────────────────────────────┘
                   │       │       │       │
                 Servers Servers Servers Servers

2-Tier (Leaf-Spine) — most common for single DC pod:

       ┌───────────────────────────────────────────────────┐
       │    SP1               SP2               SP3        │  Spine
       │   / │ \             / │ \             / │ \       │
       └──────────────────────────────────────────────────┘
          /  │  \           /  │  \           /  │  \
       ┌──────────────────────────────────────────────────┐
       │  L1       L2       L3       L4       L5       L6 │  Leaf (ToR)
       └──────────────────────────────────────────────────┘
          │         │         │         │         │
       Servers   Servers   Servers   Servers   Servers
```

### 10.3 BGP ASN Assignment in Clos

RFC 7938 recommends private ASNs with specific assignment strategies:

```
Strategy 1: Unique ASN per device (most common)
  
  Each device gets a unique private ASN. eBGP between all tiers.
  
  Spines:    65100, 65101, 65102, 65103
  Leaves:    65000, 65001, 65002, ..., 65063
  
  Leaf-Spine eBGP sessions:
    L1(65000) ── eBGP ── SP1(65100)
    L1(65000) ── eBGP ── SP2(65101)
    L1(65000) ── eBGP ── SP3(65102)
    
  AS_PATH for server traffic:
    Server on L1 → SP1 → L2:
    AS_PATH: [65000, 65100, 65001]
    
  Unique ASN per device = no AS_PATH loop issues for any path.

Strategy 2: Shared ASN per tier (RFC 7938 recommendation for simplicity)
  
  All spines share one ASN. All leaves share one ASN (or per-pod ASN).
  
  Spines all: ASN 65000
  Leaves all: ASN 65001 (or each pod has its own)
  
  Problem: AS_PATH loop detection!
  L1 (ASN 65001) advertises 10.0.1.0/24
  SP1 (ASN 65000) receives it
  SP1 advertises to L2 (ASN 65001)
  L2 sees 65001 in AS_PATH (its own ASN) → REJECTS (loop detection)!
  
  Solution: "allowas-in" or "as-override"
  
  allowas-in [count]:
    neighbor SP1 allowas-in 1  ← Accept routes even if own ASN appears once
    Dangerous: can hide real loops. Use carefully.
  
  as-override:
    neighbor L2 as-override  ← SP1 replaces 65001 in AS_PATH with 65000 (its own)
    L2 receives AS_PATH [65000, 65000] — no 65001 — accepted.
    Still suboptimal: loses original path info.
    
  Best practice: unique ASN per leaf (or per ToR), shared ASN per spine tier is OK
  because spines are transit devices and don't originate routes.
```

### 10.4 BGP Configuration for DC Fabric (FRR)

```
Complete leaf switch configuration (FRR/Cumulus Linux):

! /etc/frr/frr.conf on Leaf L1 (ASN 65000)

frr version 8.0
frr defaults datacenter
!
hostname leaf01
!
! Enable required daemons
router bgp 65000
 bgp router-id 10.0.0.1
 bgp log-neighbor-changes
 !
 ! Timers: fast convergence for DC
 ! Hold time 9s, keepalive 3s (instead of 90/30)
 bgp timers 3 9
 !
 ! No synchronization (default in BGP4)
 no bgp ebgp-requires-policy
 !
 neighbor SPINES peer-group
 neighbor SPINES remote-as external       ! eBGP to any AS (for RFC 7938)
 neighbor SPINES bfd                      ! BFD for fast failure detection
 neighbor SPINES timers 3 9
 neighbor SPINES timers connect 10
 neighbor SPINES advertisement-interval 0 ! MRAI=0 for fast convergence
 neighbor SPINES capability extended-nexthop  ! For BGP unnumbered
 !
 neighbor swp1 interface peer-group SPINES  ! BGP unnumbered on interface
 neighbor swp2 interface peer-group SPINES
 neighbor swp3 interface peer-group SPINES
 !
 address-family ipv4 unicast
  neighbor SPINES activate
  neighbor SPINES next-hop-self            ! Set NH to self for iBGP-like behavior
  !
  ! Advertise connected routes (server subnets)
  redistribute connected route-map CONNECTED_TO_BGP
  !
  ! Maximum prefix protection
  neighbor SPINES maximum-prefix 1000 warning-only
 exit-address-family
 !
 address-family l2vpn evpn
  neighbor SPINES activate
  advertise-all-vni                        ! Advertise all local VNIs
 exit-address-family
!
! Only redistribute server-facing interfaces
route-map CONNECTED_TO_BGP permit 10
 match interface swp10 swp11 swp12 swp13 swp14 swp15 swp16
!
route-map CONNECTED_TO_BGP deny 99
!
line vty
!
```

```
Spine switch configuration:

router bgp 65100
 bgp router-id 10.0.1.1
 bgp log-neighbor-changes
 bgp timers 3 9
 no bgp ebgp-requires-policy
 !
 neighbor LEAVES peer-group
 neighbor LEAVES remote-as external
 neighbor LEAVES bfd
 neighbor LEAVES timers 3 9
 neighbor LEAVES advertisement-interval 0
 neighbor LEAVES capability extended-nexthop
 !
 ! Connect to all leaves via unnumbered BGP
 neighbor swp1 interface peer-group LEAVES
 neighbor swp2 interface peer-group LEAVES
 ... (all leaf-facing interfaces)
 !
 ! Connect to super-spines (if 3-tier)
 neighbor SUPERSPINES peer-group
 neighbor SUPERSPINES remote-as external
 neighbor swp49 interface peer-group SUPERSPINES
 neighbor swp50 interface peer-group SUPERSPINES
 !
 address-family ipv4 unicast
  neighbor LEAVES activate
  neighbor SUPERSPINES activate
  !
  ! IMPORTANT: Spines are transit — do NOT redistribute connected
  ! They only carry routes learned from BGP
  !
  ! Maximum ECMP paths
  maximum-paths 64
  maximum-paths ibgp 64
 exit-address-family
 !
 address-family l2vpn evpn
  neighbor LEAVES activate
  neighbor SUPERSPINES activate
 exit-address-family
!
```

### 10.5 ECMP in DC BGP

```
In a 2-tier Clos with 4 spines, traffic from L1 to L4 has 4 equal paths:
  L1→SP1→L4
  L1→SP2→L4
  L1→SP3→L4
  L1→SP4→L4

BGP ECMP requirements (FRR):
  maximum-paths 64          ! Up to 64 equal-cost BGP paths
  maximum-paths ibgp 64     ! Same for iBGP paths

For ECMP to work, paths must be equal in the decision process up to step 8.
In DC eBGP:
  - AS_PATH length is equal (all spines are 1 hop away from any leaf)
  - ORIGIN is equal (all redistributed connected)
  - MED is not set (equal)
  - All routes are eBGP (equal)
  - IGP cost to NEXT_HOP = 0 (directly connected via BGP unnumbered)
  → All 4 paths survive to final tiebreaker → ECMP

"bgp bestpath as-path multipath-relax":
  Normally ECMP requires IDENTICAL AS_PATH.
  In DC with unique ASNs per leaf, traffic from L1 to L2 via different spines:
    Path 1: AS_PATH [65100, 65001]  (via SP1 ASN 65100)
    Path 2: AS_PATH [65101, 65001]  (via SP2 ASN 65101)
  These AS_PATHs differ! → No ECMP by default.
  
  "bgp bestpath as-path multipath-relax" allows ECMP even with different AS_PATHs
  as long as all other criteria are equal.

Kernel ECMP:
  Linux kernel uses ECMP via multiple nexthops in a route:
  
  $ ip route show 10.0.2.0/24
  10.0.2.0/24 
    nexthop via 169.254.0.1 dev swp1 weight 1
    nexthop via 169.254.0.2 dev swp2 weight 1
    nexthop via 169.254.0.3 dev swp3 weight 1
    nexthop via 169.254.0.4 dev swp4 weight 1
  
  Flow hashing (ECMP hash):
  Linux kernel hashes on: src-IP + dst-IP + protocol + src-port + dst-port
  Result is used to select one of the equal-cost nexthops.
  This is called "per-flow ECMP" — all packets of a TCP flow use same nexthop.
```

---

## 11. BGP Unnumbered

BGP Unnumbered (RFC 5549, implemented by Cumulus/FRR) eliminates the need for numbered point-to-point IP addresses between BGP speakers.

### 11.1 How BGP Unnumbered Works

```
Traditional BGP:
  Need /30 or /31 IP addresses on every link:
    L1 swp1: 10.1.1.0/31
    SP1 swp1: 10.1.1.1/31
    L1 swp2: 10.1.2.0/31
    SP2 swp1: 10.1.2.1/31
    ... 
    100 leaf × 4 spines = 400 /31 subnets = IP address management nightmare

BGP Unnumbered:
  Use IPv6 link-local addresses (auto-configured, fe80::/10) as:
  1. BGP peer address (TCP session established to fe80:: address)
  2. NEXT_HOP for IPv4 routes (via RFC 5549 extended next hop encoding)

Step-by-step:
  1. IPv6 Router Advertisement (RA) is used by FRR to discover neighbors
     (via "neighbor <iface> interface" — no IP configured on interface)
  
  2. FRR sends RA on each interface — the peer's fe80:: address is discovered
  
  3. BGP session is established to the peer's link-local IPv6 address
     (TCP connects to [fe80::xxxx]:179 on that interface)
  
  4. In OPEN, both sides advertise:
     Capability: Extended Next Hop (Code 5, RFC 8950)
     AFI=1 (IPv4), SAFI=1 (Unicast), Next-hop AFI=2 (IPv6)
     = "I can use IPv6 next-hops for IPv4 routes"
  
  5. IPv4 routes are advertised with IPv6 link-local NEXT_HOP in MP_REACH_NLRI
     (AFI=1, SAFI=1, but NH encoded as 16-byte IPv6 address)
  
  6. Receiving router installs:
     10.0.0.0/24 via fe80::1:2:3:4 dev swp1
     Linux kernel supports this natively via IPv6 nexthop

Interface auto-discovery via RFC 5549:
  FRR uses /proc/net/if_inet6 and netlink to discover neighbor IPv6 addresses.
  No manual IP configuration needed anywhere in the fabric!
```

### 11.2 BGP Unnumbered FRR Configuration

```
! Minimal FRR config for BGP unnumbered
router bgp 65000
 bgp router-id 10.0.0.1          ! Still need a router-id (loopback IP)
 !
 neighbor swp1 interface remote-as external
 neighbor swp2 interface remote-as external
 !
 address-family ipv4 unicast
  neighbor swp1 activate
  neighbor swp2 activate
  redistribute connected
 exit-address-family
!

! Verify:
# show bgp neighbors swp1
BGP neighbor on swp1: fe80::202:ff:fe01:0102, remote AS 65100
...
  Hostname: spine01
  BGP version 4, remote router ID 10.0.1.1
  BGP state = Established, up for 01:23:45
  ...
  Neighbor capabilities:
    4 Byte AS: advertised and received
    Extended nexthop: advertised and received
      Address families by peer:
                       IPv4 Unicast
  ...

# ip route
10.0.2.0/24 nhid 25 via inet6 fe80::202:ff:fe01:0304 dev swp1 proto bgp metric 20
10.0.3.0/24 nhid 26 via inet6 fe80::202:ff:fe01:0506 dev swp2 proto bgp metric 20
```

---

## 12. BGP ECMP and Multipath

### 12.1 Nexthop Objects in Linux Kernel

Modern Linux (4.14+) introduced nexthop objects which improve ECMP:

```
Traditional ECMP (embedded nexthops):
  ip route add 10.0.0.0/24 
    nexthop via 1.1.1.1 dev eth0 weight 1
    nexthop via 2.2.2.2 dev eth1 weight 1
  
  Every prefix with same ECMP group duplicates the nexthop data.
  100,000 prefixes × 4 nexthops = huge memory and update cost.

Nexthop Objects (ip nexthop):
  ip nexthop add id 100 via 1.1.1.1 dev eth0
  ip nexthop add id 101 via 2.2.2.2 dev eth1
  ip nexthop add id 200 group 100/101   ← ECMP group
  
  ip route add 10.0.0.0/24 nhid 200    ← Reference by ID
  ip route add 10.0.1.0/24 nhid 200    ← Same group, no duplication
  ip route add 10.0.2.0/24 nhid 200
  
  When a nexthop changes (link down), update ONCE the nexthop object.
  All routes referencing it are immediately updated.
  
  FRR uses nexthop objects automatically when kernel supports them.
  sysctl net.ipv4.nexthop_compat_mode=0 to disable legacy behavior.

Checking nexthop objects:
  $ ip nexthop list
  id 100 via 1.1.1.1 dev eth0 scope link
  id 101 via 2.2.2.2 dev eth1 scope link
  id 200 group 100/101

  $ ip route show 10.0.0.0/24
  10.0.0.0/24 nhid 200 proto bgp metric 20
```

### 12.2 ECMP Hash Tuning

```
Linux kernel ECMP hashing (kernel/net/ipv4/route.c):

Default hash fields: src-IP, dst-IP, protocol
With ip_forward_use_pmtu_blackhole=0 and fib_multipath_use_neigh=1:
  Also considers: src-port, dst-port (for TCP/UDP)

sysctl controls:
  net.ipv4.fib_multipath_hash_policy:
    0 = Layer 3 only (src-IP, dst-IP, protocol)
    1 = Layer 3 + 4 (includes src/dst ports) ← recommended for DC
    2 = Layer 3 + 4 + inner headers (for GRE/VXLAN)

  net.ipv4.fib_multipath_hash_fields (kernel 5.3+):
    Bitmask of fields to include in hash:
    bit 0: src addr
    bit 1: dst addr
    bit 2: IP protocol
    bit 3: fwmark
    bit 4: src port
    bit 5: dst port
    bit 6: inner src addr
    bit 7: inner dst addr
    bit 8: inner IP protocol
    bit 9: inner fwmark
    bit 10: inner src port
    bit 11: inner dst port
    
    Typical DC: 0b111 (src+dst addr + protocol) or 0b110011 (all L3+L4)

ECMP hash polarization problem:
  In multi-tier Clos, if all tiers use the same hash algorithm,
  traffic can concentrate on one path (all hash to same bucket).
  
  Solution: Seed the hash differently at each tier.
  Linux: randomized per-boot seed, generally good entropy.
  
  RTNETLINK / Netlink verification:
  # ip -s -d route show 10.0.0.0/24
  (Shows per-nexthop statistics with multipath info)
```

---

## 13. BFD with BGP

BFD (Bidirectional Forwarding Detection, RFC 5880) provides sub-second failure detection, far faster than BGP hold timer expiry.

### 13.1 BFD Fundamentals

```
Without BFD:
  BGP hold timer = 90s (default)
  After link failure, BGP detects it after 90s maximum (next missed keepalive cycle)
  
  For HA-sensitive applications: 90s is unacceptable.

With BFD:
  BFD control packets sent every 300ms (configurable down to 50ms)
  3 missed packets = failure detected: 900ms worst case
  In practice: 150-300ms typical failure detection
  BGP is notified immediately → convergence in <1 second

BFD Protocol:
  UDP port 3784 (single-hop) or 4784 (multi-hop)
  Two modes:
    Asynchronous: both sides send periodic Hello packets
    Demand: only send when needed (rarely used)
  
  BFD Control Packet:
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |Vers |  Diag   |Sta|P|F|C|A|D|M|  Detect Mult  |    Length     |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                 My Discriminator                               |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                 Your Discriminator                             |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                 Desired Min TX Interval                        |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                 Required Min RX Interval                       |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                 Required Min Echo RX Interval                  |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  
  Vers: version = 1
  Diag: reason for session state change
  State: 00=AdminDown, 01=Down, 10=Init, 11=Up
  P: Poll bit
  F: Final bit
  Detect Mult: detection multiplier (e.g., 3 = 3 missed packets = down)
  My/Your Discriminator: session identifiers
  
BFD State Machine: AdminDown → Down → Init → Up

FRR BFD configuration:
  ! BFD profile definition
  bfd
   profile FAST_LINK
    detect-multiplier 3
    transmit-interval 100   ! 100ms TX interval
    receive-interval 100    ! 100ms RX interval
  !
  router bgp 65000
   neighbor swp1 interface remote-as external
   neighbor swp1 bfd profile FAST_LINK
  !

Kernel interaction:
  BFD runs in userspace (FRR's bfdd daemon).
  Uses raw socket or UDP socket.
  For lowest latency, some implementations use kernel bypass (DPDK).
  FRR bfdd runs with SO_PRIORITY socket option for scheduling priority.
  
  BFD sessions tracked per (local-IP, remote-IP, interface):
  # show bfd peers
  BFD Peers:
      peer 169.254.0.1 interface swp1
          ID: 837021
          Remote ID: 298765
          Active mode
          Status: up
          Uptime: 1 hour 23 minutes
          Diagnostics: ok
          Remote diagnostics: ok
          Message interval: 100ms
          Minimum RX interval: 100ms
          Detection threshold: 300ms (100ms * 3)
```

---

## 14. BGP EVPN (RFC 7432)

EVPN (Ethernet VPN) is a BGP address family that extends BGP to carry Ethernet/MAC information, enabling VXLAN fabric control planes, multi-site connectivity, and Layer-2 VPNs.

### 14.1 EVPN Overview

```
Traditional VXLAN issues without EVPN (flood-and-learn):
  - BUM (Broadcast, Unknown unicast, Multicast) traffic floods to ALL VTEPs
  - No central MAC/IP database — learn by data plane flooding
  - ARP flooding across fabric
  - No IP mobility detection
  - Hard to do multi-homing

EVPN solves this by using BGP as control plane:
  - MAC and IP addresses are distributed via BGP UPDATE messages
  - ARP suppression: VTEP responds to ARP locally (no flooding)
  - Layer-2 stretch with loop prevention
  - Multi-homing (RFC 7432 ESI-based)
  - IP prefix routing via Type-5 routes

EVPN runs as: AFI=25 (L2VPN), SAFI=70 (EVPN)
```

### 14.2 EVPN Route Types

```
Type 1: Ethernet Auto-Discovery (AD) Route
  Purpose: Multi-homing — announce a site is reachable via this PE
  Key fields: ESI (Ethernet Segment ID, 10 bytes), Ethernet Tag ID
  Used for: Fast failover, aliasing (load balancing for multi-homed hosts)
  
  Format:
  [1][RD][ESI][Ethernet Tag ID]
  
  Two sub-types:
  - Per-ESI: Announce entire segment (bulk withdrawal on failure)
  - Per-EVI: Per VLAN (fine-grained)

Type 2: MAC/IP Advertisement Route
  Purpose: Distribute MAC and optionally IP address of hosts
  Key fields: MAC address, IP address (optional), MPLS/VNI labels
  Used for: MAC learning, ARP suppression
  
  Format:
  [2][RD][ESI][Ethernet Tag][MAC Length][MAC][IP Length][IP][Label1][Label2]
  
  Example: Host 00:11:22:33:44:55, IP 10.1.1.100, on VTEP 10.0.0.1, VNI 100
  R1 advertises:
    Route: [2][65000:100][00:00:00:00:00:00][0][48][00:11:22:33:44:55][32][10.1.1.100][VNI:100]
    Extended Community: RT 65000:100, Router MAC 00:aa:bb:cc:dd:ee, Encap VXLAN
  
  R2 receives this, installs:
    ARP table: 10.1.1.100 → 00:11:22:33:44:55
    VXLAN FDB: 00:11:22:33:44:55 → VTEP 10.0.0.1
  R2 can now answer ARP for 10.1.1.100 locally (ARP suppression)

Type 3: Inclusive Multicast Ethernet Tag Route (IMET)
  Purpose: Announce participation in a VNI (for BUM traffic)
  Key fields: Ethernet Tag ID (VNI), IP of originating VTEP
  Used for: Multicast group discovery, underlay multicast or ingress replication
  PMSI Tunnel attribute: specifies how BUM is handled
    - Ingress Replication: unicast copy to each VTEP
    - P-Multicast: underlay multicast group
  
  Format:
  [3][RD][Ethernet Tag][IP Length][Originating Router IP]

Type 4: Ethernet Segment Route
  Purpose: Discover which PE nodes share an Ethernet Segment (multi-homing)
  Key fields: ESI, Originating Router IP
  Used for: Designated Forwarder election for BUM traffic per segment
  
  Format:
  [4][RD][ESI][IP Length][Originating Router IP]

Type 5: IP Prefix Route (RFC 9136)
  Purpose: Distribute IP prefixes (routes) in the EVPN fabric
  Key fields: IP prefix, prefix length, GW IP, MPLS/VNI label
  Used for: Inter-subnet routing, layer-3 EVPN
  
  This is the key route type for cloud-native DC routing:
  Instead of redistributing into separate BGP IPv4 unicast, prefixes are
  carried natively in EVPN, associated with VRFs via Route Target.
  
  Format:
  [5][RD][ESI][Ethernet Tag][IP Prefix Length][IP Prefix][GW IP][Label]

Type 6: Selective Multicast Ethernet Tag Route (SMET)
  Purpose: Optimized multicast (IGMP snooping via BGP)
  
Type 7/8: IGMP Join/Leave Synch Routes
  Purpose: Sync IGMP membership across multi-homed PEs
```

### 14.3 VXLAN EVPN Architecture

```
Physical topology:
  ┌──────────────────────────────────────────────────────────────┐
  │                        BGP RR                                │
  │                     (or spine with RR)                       │
  │                     10.0.0.254                               │
  └──────────┬─────────────────────────────────┬────────────────┘
             │ iBGP EVPN                        │ iBGP EVPN
  ┌──────────▼────────┐             ┌──────────▼────────────────┐
  │   VTEP / Leaf 1   │             │      VTEP / Leaf 2         │
  │   VXLAN Tunnel    │             │      VXLAN Tunnel          │
  │   10.0.0.1        │  Underlay   │      10.0.0.2              │
  │                   │◀───────────▶│                            │
  │  VNI 100: VLAN 10 │   IP fabric │   VNI 100: VLAN 10        │
  │  VNI 200: VLAN 20 │             │   VNI 200: VLAN 20        │
  └──────────┬────────┘             └──────────┬────────────────┘
             │                                  │
           Host A                             Host B
           10.1.1.1                           10.1.1.2
           VLAN 10                            VLAN 10

Control Plane Flow (Host A pings Host B for first time):

1. Host A sends ARP: "Who has 10.1.1.2?"

2. VTEP1 (Leaf 1):
   - Checks local ARP suppression cache → miss
   - Checks EVPN Type-2 routes for 10.1.1.2 → found! (VTEP2 advertised it)
   - Responds to ARP directly: "10.1.1.2 is at 00:bb:bb:bb:bb:bb"
   - No flood to other VTEPs!

3. Host A sends ICMP to 00:bb:bb:bb:bb:bb
   VTEP1 encapsulates: [Outer-IP: src=10.0.0.1, dst=10.0.0.2]
                       [UDP: src=random, dst=4789]
                       [VXLAN: VNI=100]
                       [Inner-Eth: dst=00:bb:bb:bb:bb:bb]
                       [Inner-IP: dst=10.1.1.2]

4. Underlay routes via BGP IPv4 unicast:
   10.0.0.2/32 via <spine> (unicast routing)

VXLAN Header:
  0                   1                   2                   3
  0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |R|R|R|R|I|R|R|R|            Reserved                           |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  |                VXLAN Network Identifier (VNI) |   Reserved    |
  +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
  I bit = 1: VNI is valid
  VNI: 24-bit identifier (16M VNIs vs 4K VLANs)
```

### 14.4 Asymmetric vs Symmetric EVPN Routing

```
Asymmetric IRB (Inter-Subnet Routing in Bridge — legacy):
  - Route and bridge on ingress VTEP
  - All VNIs for both source and destination must be local
  - Simple but doesn't scale (every VTEP needs every VNI)
  
  Host A (VLAN10) → Host C (VLAN20):
  VTEP1: route 10.1.1.x → 10.1.2.x, bridge to VLAN20, send to VTEP2 in VNI200
  VTEP2: bridge into VLAN20 directly
  Return: VTEP2 routes back to 10.1.1.x, bridges into VNI100
  
  Asymmetric = inbound and outbound paths use different VNIs.

Symmetric IRB (with L3 VNI — modern/recommended):
  - L3 VNI: dedicated VNI for inter-subnet routed traffic
  - Each VRF gets an L3 VNI (not per VLAN)
  - Scales better: each VTEP only needs the VNIs for its attached hosts
  
  Host A (VLAN10) → Host C (VLAN20):
  VTEP1: route to L3-VNI (e.g., VNI 9999, "tenant VRF")
  VTEP2: receive on L3-VNI, route into VLAN20 locally
  
  Traffic: [VXLAN VNI=9999][Inner-Eth: router-MAC to router-MAC]
  EVPN Type-2 carries "RMAC" (Router MAC) extended community.
  
  FRR symmetric IRB:
  vrf TENANT
   vni 9999
  !
  interface vlan10 vrf TENANT
  interface vlan20 vrf TENANT
  !
  router bgp 65000 vrf TENANT
   address-family l2vpn evpn
    advertise ipv4 unicast        ! Advertise Type-5 routes
    advertise-default-gw          ! Advertise default GW MAC/IP
   exit-address-family
  !
```

### 14.5 Multi-Homing with EVPN ESI

```
ESI (Ethernet Segment Identifier): 10-byte value identifying a multi-home segment.

Multi-homing topology:
  CE (customer edge device / server with LAG/bond)
         │
    ┌────┴────┐
    │  LAG    │  Bond / Port-channel
    ├────┬────┤
    │    │    │
  PE1   PE2   (both EVPN PEs)
  
  ESI = 00:01:00:00:00:00:00:00:00:01  (configured on both PE1 and PE2)
  
  Types of multi-homing:
  All-Active: Both PE1 and PE2 forward traffic (load balancing)
  Single-Active: Only one PE forwards at a time (failover only)

Type-1 (AD) route per ESI announces the segment on both PEs:
  PE1 and PE2 both advertise Type-1 with same ESI.
  Remote PEs see two VTEPs for that ESI → load balance (aliasing).
  
  Aliasing: Remote PE can send traffic to either PE1 or PE2 even if
  the MAC was only learned behind PE1. The Type-1 route enables this.

Designated Forwarder (DF) election:
  For BUM (broadcast/unknown/multicast) traffic on a segment,
  only ONE PE should forward to avoid duplicates.
  Type-4 routes are used to elect the DF per ESI per VLAN.
  Default algorithm: PE with lowest IP address is DF.
  Algorithms: default, modulo, preference-based (RFC 8584)
  
  FRR config:
  interface bond0
   evpn mh es-id 1
   evpn mh es-df-pref 50000    ! Higher = more likely to be DF
   evpn mh es-sys-mac 44:38:39:ff:ff:01
  !
  evpn mh startup-delay 30     ! Wait before electing DF after boot
```

---

## 15. BGP MPLS/VPN (RFC 4364 / L3VPN)

### 15.1 L3VPN Architecture

```
BGP/MPLS IP VPNs are the backbone of enterprise MPLS networks and cloud DX services.

Components:
  PE (Provider Edge): Runs BGP VPNv4, maintains per-VPN VRFs
  P (Provider): MPLS core, label switching only, no VPN knowledge
  CE (Customer Edge): Connected to PE, runs routing protocol or static

VPN Routing and Forwarding (VRF):
  Each customer/tenant gets their own VRF (routing table).
  VRFs are completely isolated — overlapping IP addresses supported.
  
  Isolation: VRF A has 10.0.0.0/8, VRF B has 10.0.0.0/8 → no conflict

Route Distinguisher (RD):
  Makes VPN routes globally unique in the BGP table.
  Prepended to IPv4 prefix: RD + IPv4 prefix = VPNv4 prefix
  
  Format: Type:Value
  Type 0: 2-byte AS : 4-byte value (e.g., 65001:100)
  Type 1: 4-byte IP : 2-byte value (e.g., 10.0.0.1:100)
  Type 2: 4-byte AS : 2-byte value (e.g., 65001:100)
  
  RD purpose: distinguish 10.0.0.0/8 in VRF-A vs 10.0.0.0/8 in VRF-B
  VPNv4 route: [65001:100]10.0.0.0/8  vs  [65001:200]10.0.0.0/8

Route Target (RT):
  Determines which VRFs import which routes.
  RT is an Extended Community.
  PE exports routes with a set of RTs, imports routes matching import RT.
  
  Hub-and-Spoke VPN:
    Hub PE: export RT 65001:1000, import RT 65001:2000
    Spoke PE: export RT 65001:2000, import RT 65001:1000
  
  Full-mesh (any-to-any):
    All PEs: export RT 65001:100, import RT 65001:100

MPLS Label Stack:
  PE-to-PE traffic uses TWO labels:
  [Transport Label][VPN Label]
  
  Transport label: distributed by LDP or RSVP-TE, gets packet to egress PE
  VPN label: distributed by BGP (per VRF or per prefix), 
             tells egress PE which VRF to deliver to
  
  PHP (Penultimate Hop Popping):
    Last P-router before egress PE pops the transport label.
    Egress PE only sees VPN label → direct to VRF.
  
  Forwarding:
  CE-A → PE1 → [VPN-L][Transport-L] → P1 → P2 → PE2 (PHP) → [VPN-L] → CE-B
```

### 15.2 VPNv4 BGP Route (Wire Level)

```
VPNv4 is carried in MP_REACH_NLRI with:
  AFI = 1 (IPv4)
  SAFI = 128 (VPN)

NLRI encoding for VPNv4:
  ┌──────────────────────────────────────────────────────────────┐
  │ Label Stack (3 bytes per label, bottom-of-stack bit)         │
  │ Route Distinguisher (8 bytes: Type(2) + Value(6))           │
  │ IPv4 Prefix (variable, ceil(prefixlen/8) bytes)             │
  └──────────────────────────────────────────────────────────────┘
  
  Total prefix length in bits = 
    24 (label) + 64 (RD) + IPv4-prefix-length
  
  Example: RD=65001:100, prefix=10.1.0.0/24, label=1024
  Prefix length bits: 24 + 64 + 24 = 112
  
  Wire bytes:
  70             ← prefix length = 112 bits
  00 04 01       ← MPLS label 1024 (label<<4 | BoS=1 → 0x004010 but label in 20 bits)
                   More precisely: (1024 << 4) | 1 = 0x004001 → 00 40 01
  00 00 FD E9 00 00 00 64   ← RD: type=0(2B) + AS=65001(2B) + value=100(4B)
                              0x00 0x00 0xFD 0xE9 0x00 0x00 0x00 0x64
  0A 01 00       ← 10.1.0.0 (3 bytes for /24)
  
  Route Target extended community:
  0x00 0x02 0xFD 0xE9 0x00 0x00 0x00 0x64
  (type=0x0002 RT, ASN=65001, value=100)
```

---

## 16. BGP Flowspec (RFC 5575)

Flowspec distributes traffic filtering rules (ACLs/QoS) via BGP. Used for DDoS mitigation, traffic steering, and RTBH (Remotely Triggered Black Hole).

### 16.1 Flowspec Route Format

```
AFI = 1 (IPv4) or 2 (IPv6), SAFI = 133 (Flowspec) or 134 (VPN Flowspec)

Each Flowspec NLRI is a set of match criteria:
  Type 1: Destination Prefix (IP prefix to match)
  Type 2: Source Prefix
  Type 3: IP Protocol (operator + value encoding)
  Type 4: Port (operator + value)
  Type 5: Destination Port
  Type 6: Source Port
  Type 7: ICMP Type
  Type 8: ICMP Code
  Type 9: TCP Flags (bit mask)
  Type 10: Packet Length
  Type 11: DSCP
  Type 12: Fragment (DF, IsF, FF, LF bits)

Operator encoding for numeric fields:
  Bit 7: end-of-list (0 = more operators follow)
  Bit 6: AND/OR (0 = OR, 1 = AND)
  Bits 5-4: operator (00=false, 01=<, 10=>, 11=== equals, +others)
  Bit 3: NOT
  Bits 2-1: value length (00=1B, 01=2B, 10=4B, 11=reserved)
  Bit 0: end-of-list for value

Actions (Extended Communities):
  traffic-rate: 0x8006 — rate limit in bytes/second (0 = drop/blackhole)
  traffic-action: 0x8007 — terminal-action, sample
  redirect-VRF: 0x8008 — redirect to VRF
  traffic-marking: 0x8009 — set DSCP

Example: Block all UDP traffic to 203.0.113.0/24
  NLRI Type 1: 203.0.113.0/24
  NLRI Type 3: protocol UDP (value=17, operator=equals)
  Extended Community: traffic-rate 0 (drop)

FRR Flowspec:
  router bgp 65000
   address-family ipv4 flowspec
    neighbor 10.0.0.2 activate
    local-install swp1      ! Apply flowspec rules on this interface
   exit-address-family
  !
```

---

## 17. BGP-LS — Link State Distribution

BGP-LS (RFC 7752) distributes the IGP topology (OSPF/IS-IS link-state database) via BGP. Used by SDN controllers to get a network-wide view.

### 17.1 BGP-LS Overview

```
Problem: SDN controller (e.g., OpenDaylight, ONOS, SR-PCE) needs to 
         know the full network topology to compute traffic-engineered paths.
         
Solution: Run BGP-LS on a route reflector that also participates in IGP.
          The RR distributes the IGP LSDB via BGP to the controller.

BGP-LS AFI = 16388, SAFI = 71

Node NLRI: Represents a router (node descriptor: BGP Router ID, IGP Router ID)
Link NLRI: Represents a link (local/remote node descriptors + link attributes)
Prefix NLRI: Represents a prefix (node descriptor + prefix attributes)

Link attributes carried:
  TE metric, admin group (color), max bandwidth, max reservable bandwidth,
  unreserved bandwidth (8 priority classes), SRLG, delay, loss, jitter

Application: Segment Routing PCE
  Controller receives BGP-LS topology
  Computes optimal SR-TE paths
  Programs headend via PCEP or BGP (SR Policy)

FRR configuration:
  router bgp 65000
   address-family link-state
    neighbor 10.0.0.100 activate   ! 10.0.0.100 = SDN controller
   exit-address-family
  !
  router ospf
   redistribute bgp-ls              ! Export OSPF LSDB to BGP-LS
  !
```

---

## 18. BGP ADD-PATH (RFC 7911)

### 18.1 The Problem ADD-PATH Solves

```
With route reflection, an RR only sends the BEST path to clients.
Clients can't make independent path selections or see backup paths.
This causes:
  - Suboptimal ECMP (only one path visible to clients)
  - Slow convergence (backup path not pre-installed)
  - Policy conflicts (client can't distinguish paths)

ADD-PATH allows advertising MULTIPLE paths for the same prefix.

Capability negotiation (OPEN message):
  Code 69 (ADD-PATH):
  Per AFI/SAFI: Send=1, Receive=2, Send+Receive=3
  
  Meaning:
  - "I can SEND multiple paths per prefix" (RR to client)
  - "I can RECEIVE multiple paths per prefix" (client to RR)

Path identifier:
  ADD-PATH adds a 4-byte Path-ID before each NLRI.
  This makes each (prefix, path-id) unique.
  
  NLRI with ADD-PATH:
  [Path-ID (4B)][Prefix-Length (1B)][Prefix (variable)]
  
  Example: 3 paths for 10.0.0.0/24, path IDs 1, 2, 3:
  00 00 00 01  18  0A 00 00  ← Path 1: 10.0.0.0/24
  00 00 00 02  18  0A 00 00  ← Path 2: same prefix, different path
  00 00 00 03  18  0A 00 00  ← Path 3: same prefix, third path

FRR ADD-PATH config:
  router bgp 65000
   neighbor CLIENTS peer-group
   address-family ipv4 unicast
    neighbor CLIENTS addpath-tx-all-paths      ! Send all paths
    ! OR:
    neighbor CLIENTS addpath-tx-bestpath-per-AS ! Best per originating AS
   exit-address-family
  !
```

---

## 19. BGP in Cloud-Native Networking

### 19.1 Kubernetes Networking and the CNI Model

```
Kubernetes pod networking requirements (CNI spec):
  1. Every pod gets its own IP address
  2. All pods can communicate with each other without NAT
  3. Pods on the same node communicate locally
  4. Pods on different nodes communicate via routing

CNI (Container Network Interface):
  Plugin-based: kubelet calls CNI plugin at pod creation/deletion
  Plugin adds/removes veth pairs, configures routes
  
  Pod networking stack:
  
  ┌────────────────────────────────────────────┐
  │              Linux Node                    │
  │                                            │
  │  eth0: 10.0.0.1/24  (node IP, to fabric)  │
  │                                            │
  │  ┌───────────┐   ┌───────────┐             │
  │  │  Pod A    │   │  Pod B    │             │
  │  │ eth0:     │   │ eth0:     │             │
  │  │ 10.1.1.2  │   │ 10.1.1.3  │             │
  │  └────┬──────┘   └────┬──────┘             │
  │       │veth pair      │veth pair            │
  │  ┌────┴──────────────┴──────────────────┐  │
  │  │    cni0 / bridge (10.1.1.1)           │  │
  │  └───────────────────────────────────────┘  │
  │          │ IP routing                        │
  │  eth0: 10.0.0.1                             │
  └────────────────────────────────────────────┘
  
  Route on node: 10.1.1.0/24 dev cni0 (local pod CIDR)
  Route to reach other nodes' pod CIDRs:
    Option A: Overlay (VXLAN, Geneve, WireGuard)
    Option B: BGP routing (Calico, Cilium, Antrea)

BGP-based pod networking:
  Each node runs a BGP daemon (BIRD, GoBGP, FRR internal)
  Node advertises its pod CIDR (/24 or /26 per node typically)
  All nodes learn all pod CIDRs via BGP
  Native routing — no encapsulation overhead
```

### 19.2 IP Address Management (IPAM) with BGP

```
Pod CIDR allocation:
  Kubernetes allocates a pod CIDR per node from the cluster CIDR.
  Cluster CIDR: 10.0.0.0/8 (typical)
  Node 1 pod CIDR: 10.1.1.0/24
  Node 2 pod CIDR: 10.1.2.0/24
  Node 3 pod CIDR: 10.1.3.0/24
  
  BGP advertises each node's pod CIDR to TOR/fabric switches.
  Fabric installs routes: 10.1.1.0/24 → Node1, 10.1.2.0/24 → Node2, etc.
  
  External access:
  Service IPs (ClusterIP, LoadBalancer) also advertised via BGP.
  LoadBalancer IP → announced from node running the endpoint.
```

---

## 20. Calico BGP Deep Dive

### 20.1 Calico Architecture

```
Calico uses Felix (dataplane agent) + BIRD (BGP daemon) on each node.

Components:
  Felix:    Calico's policy agent. Programs iptables/eBPF, routes, ARP.
            Runs on every node.
  BIRD:     BGP daemon (open source). Calico bundles a customized version.
            Runs on every node (or on dedicated route reflectors).
  Typha:    Aggregation layer between API server and Felix/BIRD.
            Reduces API server load in large clusters (100+ nodes).
  confd:    Template engine. Watches Calico config in etcd/API server,
            generates BIRD configuration files. Felix then signals BIRD to reload.

Data flow:
  ┌─────────────────────────────────────────────────────────────────┐
  │  Kubernetes API Server / etcd                                   │
  │  (stores BGP peers, IPPools, nodes, BGPConfiguration)           │
  └──────────┬──────────────────────────────────────┬──────────────┘
             │ Watch (via Typha)                     │ Watch
             │                                       │
  ┌──────────▼────────────┐               ┌──────────▼────────────┐
  │     Node 1            │               │     Node 2            │
  │  ┌────────────────┐   │               │  ┌────────────────┐   │
  │  │  confd         │   │               │  │  confd         │   │
  │  │  (watches CRDs)│   │               │  │  (watches CRDs)│   │
  │  │  ↓ generates   │   │               │  └────────────────┘   │
  │  │  /etc/calico/  │   │               │                       │
  │  │  bird/bird.cfg │   │               │                       │
  │  └────────────────┘   │               │                       │
  │  ┌────────────────┐   │  BGP sessions │  ┌────────────────┐   │
  │  │  BIRD          │◀──┼───────────────┼─▶│  BIRD          │   │
  │  │  (BGP daemon)  │   │               │  │  (BGP daemon)  │   │
  │  └────────────────┘   │               │  └────────────────┘   │
  │  ┌────────────────┐   │               │                       │
  │  │  Felix         │   │               │  ┌────────────────┐   │
  │  │  (dataplane)   │   │               │  │  Felix         │   │
  │  │  iptables/eBPF │   │               │  │  iptables/eBPF │   │
  │  └────────────────┘   │               │  └────────────────┘   │
  └───────────────────────┘               └───────────────────────┘
```

### 20.2 Calico BGP Modes

```
Mode 1: Full mesh (default for <50 nodes)
  Every node BGP-peers with every other node.
  Simple, no RR needed.
  Scales to ~50 nodes (N*(N-1)/2 sessions).

Mode 2: Route Reflectors
  Designate some nodes as RRs (via BGP node label).
  Other nodes peer only with RRs.
  
  In-cluster RR:
  kubectl label node rr01 projectcalico.org/bgp-rr="true"
  
  External RR:
  BGPPeer resource pointing to external router.

Mode 3: ToR (Top of Rack) BGP
  Nodes peer with physical TOR switches.
  No overlay — native routing.
  Best for latency-sensitive workloads.
  
  BGPPeer resource:
  apiVersion: projectcalico.org/v3
  kind: BGPPeer
  metadata:
    name: tor-switch
  spec:
    peerIP: 192.168.1.1
    asNumber: 65100
    nodeSelector: all()  # All nodes peer with this TOR

Mode 4: VXLAN (no BGP)
  Calico can also use VXLAN (without BGP) for environments where BGP is blocked.
  Uses Calico's own control plane instead of BIRD.

Calico BGP Configuration Resources:
  BGPConfiguration: Global BGP settings
    asNumber: 65000
    logSeverityScreen: Info
    nodeToNodeMeshEnabled: true  # Full mesh toggle
    serviceClusterIPs:  # Advertise service IPs
    - cidr: 10.96.0.0/12
    serviceExternalIPs:
    - cidr: 0.0.0.0/0
    serviceLoadBalancerIPs:
    - cidr: 100.64.0.0/10
  
  BGPPeer: Per-node or global peer configuration
  IPPool: IP address pools with BGP advertise options
    apiVersion: projectcalico.org/v3
    kind: IPPool
    metadata:
      name: default-ipv4-ippool
    spec:
      cidr: 10.244.0.0/16
      ipipMode: Never          # No IPIP overlay
      vxlanMode: Never         # No VXLAN
      natOutgoing: true
      nodeSelector: all()
      blockSize: 26            # /26 per node (64 IPs)
      disabled: false
```

### 20.3 Calico Dataplane Deep Dive

```
Calico programs the Linux routing table directly for pod routing:

Per-node setup:
  blackhole 10.244.1.0/26 proto bird    # Aggregate, traffic to unallocated IPs dropped
  10.244.1.2 dev cali5a6f3c2b9d0 scope link   # Pod route
  10.244.1.3 dev cali9d1e4f8a2c1 scope link
  10.244.2.0/26 via 10.0.0.2 dev eth0 proto bird  # Remote node's pod CIDR

Pod veth interface naming: cali + hash of pod name
  Each pod gets a veth pair:
  - Inside pod: eth0 with pod IP
  - On host: cali<hash> with IP 169.254.1.1 (dummy proxy ARP)
  
  Route inside pod:
    default via 169.254.1.1 dev eth0
    169.254.1.1 dev eth0 scope link
  
  The host side (cali<hash>) has proxy ARP enabled.
  All traffic from pod goes to host → host routes it.

iptables/eBPF policy enforcement:
  Felix programs iptables chains per network policy:
  
  Chain cali-INPUT:
    Jump to per-endpoint chains based on source IP
  
  Chain cali-to-wl-dispatch:  (to workload/pod)
    Match pod IP → jump to cali-tw-<endpoint-hash>
  
  Chain cali-tw-<endpoint-hash>:
    Match rules based on NetworkPolicy
    ACCEPT matching traffic
    DROP unmatched traffic (default deny)

eBPF dataplane (Calico 3.13+):
  Felix programs eBPF programs instead of iptables.
  eBPF TC (Traffic Control) programs on pod veth interfaces.
  Faster, lower CPU overhead than iptables for large policy sets.
  Preserves source IP through NodePort (avoids SNAT).
  
  # Check eBPF mode
  calicoctl get felixconfiguration default -o yaml | grep bpf
  # BPFEnabled: true
  
  eBPF maps used:
  - cali_v4_ct: connection tracking table
  - cali_v4_rt: routing table
  - cali_v4_fps: policy map per endpoint
  - cali_v4_wep: workload endpoints
```

---

## 21. Cilium BGP Deep Dive

### 21.1 Cilium Architecture

```
Cilium uses eBPF for everything — network policy, load balancing, 
observability — and added BGP support via GoBGP library (Cilium 1.10+)
and a dedicated BGP control plane (Cilium 1.12+).

Components:
  cilium-agent: runs on every node, manages eBPF programs
  cilium-operator: cluster-wide operations (IPAM, CiliumNode CRDs)
  Hubble: observability layer (uses eBPF ring buffers)
  BGP Control Plane: embedded GoBGP speaker in cilium-agent

Cilium BGP Control Plane (BGPCP):
  Introduced to handle CiliumLoadBalancerIPPool and BGPPeeringPolicy.
  Each node's cilium-agent runs its own BGP speaker.
  Peering configured via CiliumBGPPeeringPolicy CRD.
  
  apiVersion: cilium.io/v2alpha1
  kind: CiliumBGPPeeringPolicy
  metadata:
    name: rack0
  spec:
    nodeSelector:
      matchLabels:
        rack: rack0
    virtualRouters:
    - localASN: 65001
      exportPodCIDR: true          # Advertise pod CIDRs
      neighbors:
      - peerAddress: 10.0.0.1/32  # TOR switch
        peerASN: 65100
        peerPort: 179
        connectRetryTimeSeconds: 120
        holdTimeSeconds: 90
        keepAliveTimeSeconds: 30
        gracefulRestart:
          enabled: true
          restartTimeSeconds: 120
        families:
        - afi: ipv4
          safi: unicast
          advertisements:
            matchLabels:
              advertise: bgp
      serviceSelector:             # Advertise services
        matchExpressions:
        - key: somekey
          operator: NotIn
          values:
          - never-advertise

LoadBalancer IP Pool:
  apiVersion: cilium.io/v2alpha1
  kind: CiliumLoadBalancerIPPool
  metadata:
    name: pool1
    labels:
      advertise: bgp
  spec:
    cidrs:
    - cidr: 100.64.0.0/24   # Pool of IPs for LoadBalancer services
    disabled: false
  
  Cilium allocates IPs from this pool for LoadBalancer services,
  then announces them via BGP to TOR switches.
```

### 21.2 Cilium eBPF Dataplane

```
Cilium eBPF programs:
  
  TC (Traffic Control) programs:
    bpf_lxc.c: attached to each pod's veth (lxc side — lxc = Linux Container)
               handles pod-to-pod, pod-to-service, policy enforcement
    bpf_host.c: attached to host interface
               handles host-to-pod and service load balancing (kube-proxy replacement)
    bpf_overlay.c: attached to VXLAN/Geneve tunnel interface
    bpf_xdp.c: optional XDP program for ultra-fast packet processing at NIC driver level
  
  eBPF Maps (key-value stores):
    cilium_ipcache: maps pod IPs to node IPs + identity labels (security identity)
    cilium_lxc: veth interface info per pod (MAC, IP, ifindex)
    cilium_ct4_global: global IPv4 connection tracking
    cilium_ct4_any: per-pod connection tracking (local only)
    cilium_policy_v2: policy map per security identity
    cilium_lb4_services_v2: service VIP to backend mapping (kube-proxy replacement)
    cilium_lb4_backends_v2: backend pod IPs
    cilium_snat_v4: SNAT state table
    cilium_tunnel_map: overlay tunnel endpoints

Security identity:
  Cilium assigns a numeric identity to each unique combination of pod labels.
  Network policy is enforced based on identity, not IP address.
  This allows policy to work even as pods scale up/down and IPs change.
  
  Identity is encoded in:
  - VXLAN VNI field (for inter-node traffic in overlay mode)
  - Or via ipcache lookup (native routing mode)
  
  Example policy enforcement in eBPF:
  1. Packet arrives from pod A (identity: 12345) to pod B (identity: 67890)
  2. TC eBPF program on pod B's veth checks cilium_policy_v2[67890]
  3. Map returns allowed ingress identities
  4. If 12345 in allowed set → PASS, else → DROP

Kube-proxy replacement:
  Cilium completely replaces kube-proxy:
  - Service ClusterIPs handled in eBPF (not iptables)
  - NodePort implemented in XDP (wire speed for external traffic)
  - Much lower latency: direct conntrack in eBPF vs iptables traversal
  
  # Verify
  cilium status | grep "Kube-proxy replacement"
  # Kube-proxy replacement: Strict
```

---

## 22. MetalLB BGP Mode

MetalLB provides LoadBalancer service IPs for bare-metal Kubernetes clusters.

### 22.1 MetalLB BGP Architecture

```
Problem: Cloud providers (AWS/GCP/Azure) automatically provision LoadBalancer IPs.
On-premises clusters have no such mechanism.
MetalLB fills this gap.

BGP mode operation:
  1. User creates LoadBalancer service with annotation or pool selector
  2. MetalLB controller allocates IP from configured address pool
  3. MetalLB speaker on all (or selected) nodes announces the IP via BGP
  4. Multiple nodes announce the same /32 → ECMP from TOR switches
  5. TOR distributes traffic across all nodes advertising the IP
  6. Node receives packet, kube-proxy/eBPF delivers to pod endpoint
  
  Architecture:
  ┌──────────────────────────────────────────────────────┐
  │                Kubernetes Cluster                    │
  │                                                      │
  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │
  │  │   Node 1    │  │   Node 2    │  │   Node 3    │  │
  │  │  MetalLB    │  │  MetalLB    │  │  MetalLB    │  │
  │  │  Speaker    │  │  Speaker    │  │  Speaker    │  │
  │  │    BGP      │  │    BGP      │  │    BGP      │  │
  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │
  │         │                │                │          │
  └─────────┼────────────────┼────────────────┼──────────┘
            │ eBGP sessions  │                │
  ┌─────────▼────────────────▼────────────────▼──────────┐
  │                    TOR Switch                         │
  │         Receives /32 announcements from all nodes     │
  │         Installs ECMP route to all nodes              │
  └──────────────────────────────────────────────────────┘

MetalLB CRD configuration (FRR mode):

IPAddressPool:
  apiVersion: metallb.io/v1beta1
  kind: IPAddressPool
  metadata:
    name: production-pool
    namespace: metallb-system
  spec:
    addresses:
    - 203.0.113.0/24        # External IPs to advertise
    autoAssign: true
    avoidBuggyIPs: true     # Skip .0 and .255

BGPAdvertisement:
  apiVersion: metallb.io/v1beta1
  kind: BGPAdvertisement
  metadata:
    name: main
    namespace: metallb-system
  spec:
    ipAddressPools:
    - production-pool
    communities:
    - 65001:200             # Tag with community
    aggregationLength: 32   # Advertise as /32
    aggregationLengthV6: 128
    localPref: 100

BGPPeer:
  apiVersion: metallb.io/v1beta1
  kind: BGPPeer
  metadata:
    name: tor-switch
    namespace: metallb-system
  spec:
    myASN: 65000
    peerASN: 65100
    peerAddress: 10.0.0.1
    peerPort: 179
    holdTime: 90s
    keepaliveTime: 30s
    password: "bgp-secret"
    bfdProfile: fast
    routerID: 10.0.0.10

MetalLB FRR mode (default since 0.13):
  MetalLB embeds FRR as its BGP implementation.
  FRR containers run alongside speaker pods.
  Configuration generated dynamically from CRDs.
  
  Supports: BFD, VRFs, EVPN (experimental), IPv6, BGP communities.
```

---

## 23. BGP in Cloud Provider Networking

### 23.1 AWS BGP — Direct Connect and Transit Gateway

```
AWS Direct Connect (DX):
  Physical dedicated connection from customer to AWS.
  BGP runs between customer router and AWS router (DX router).
  
  Connection types:
  Dedicated: 1G or 10G physical port directly to AWS DX location
  Hosted: Shared port via AWS Partner (50M to 10G)
  
  Virtual Interfaces (VIFs):
  Private VIF: Connect to VPC via Virtual Private Gateway (VGW) or DX Gateway
  Public VIF: Access AWS public services (S3, DynamoDB) with public IPs
  Transit VIF: Connect to Transit Gateway
  
  BGP session parameters for Direct Connect:
  - Amazon ASN: 7224 (or private ASN 64512 for VGW)
  - Customer ASN: customer's own ASN or private ASN
  - BGP auth: MD5 optional but recommended
  - Prefix limit per VIF: 100 (private), 1000 (public)
  - Max prefixes advertised by Amazon: depends on VPC CIDR
  
  Private VIF BGP:
  ┌──────────────────────────────────────────────────────────────────┐
  │  Customer Network                                                │
  │  ASN: 65000                                                      │
  │    Router ──────────────────────────── DX Port ──────────────▶  │
  └─────────────────────────────────────────────────────────────────┘
                                               │ BGP Session
                                               ▼
  ┌──────────────────────────────────────────────────────────────────┐
  │  AWS                                                             │
  │  DX Router (ASN 7224)                                           │
  │    │                                                             │
  │    ▼                                                             │
  │  VGW/DX Gateway                                                  │
  │    │                                                             │
  │    ▼                                                             │
  │  VPC (10.0.0.0/16)                                               │
  └──────────────────────────────────────────────────────────────────┘
  
  Route propagation:
  Customer advertises: 192.168.0.0/16 (on-prem)
  AWS advertises: 10.0.0.0/16 (VPC CIDR)
  
  Communities accepted by AWS DX:
  7224:9100 = Advertise to all AWS DX locations in region
  7224:9200 = Advertise to all DX locations in continent
  7224:9300 = Advertise globally
  
  AWS Transit Gateway (TGW):
  Centralized hub for connecting VPCs and DX/VPN connections.
  BGP runs between DX Transit VIF and TGW (ASN 64512 or custom).
  ECMP: TGW supports ECMP with multiple DX connections.
  
  Site-to-Site VPN BGP:
  AWS VPN supports BGP over IPsec.
  Two tunnels per VPN connection (HA).
  BGP over each tunnel (ASN 65000 ↔ AWS ASN).
  AWS announces VPC CIDR, customer announces on-prem.
  
  Prefix advertisement limits:
  VPN: 100 customer-side prefixes per connection
  DX: 100 private, 1000 public
  TGW: 20 static + 1000 dynamic
  
  VPC Route Tables:
  BGP learned routes appear as "propagated" routes in VPC route tables.
  You can control which route tables receive propagated routes.

AWS BGP best practices:
  1. Use unique ASNs per DX connection (avoid conflicts)
  2. Enable BFD on DX: AWS supports 300ms intervals
  3. Advertise more-specific prefixes to prefer DX over VPN
  4. Use communities for traffic engineering
  5. Consider DX Gateway + TGW for multi-region connectivity
```

### 23.2 Azure BGP — ExpressRoute and VPN

```
Azure ExpressRoute:
  Similar to AWS DX — dedicated private connection to Azure.
  
  Circuit: Provider connection to Azure MSEE (Microsoft Enterprise Edge) routers
  Two physical connections to two MSEEs (HA by default)
  
  BGP sessions:
  - Primary: Customer PE ↔ MSEE Primary (ASN 12076)
  - Secondary: Customer PE ↔ MSEE Secondary (ASN 12076)
  
  Peering types:
  Private: Connect to Azure VNets (VNet ASN: private, e.g., 65515)
  Microsoft: Access Microsoft 365, Azure PaaS public IPs
  
  BGP attributes on ExpressRoute:
  Microsoft uses LOCAL_PREF and MED:
  - Primary connection: LOCAL_PREF 100 (default)
  - Secondary: LOCAL_PREF 100 (equal, use AS_PATH prepend or MED to prefer primary)
  
  Route limits:
  Private peering: 4000 prefixes from Azure (Standard), 10000 (Premium)
  Customer can advertise: 200 prefixes (private routes from on-prem to Azure)
  
  ExpressRoute Communities (well-known):
  12076:5010 = Routes for EastUS
  12076:5020 = Routes for WestUS
  12076:5030 = Routes for NorthEurope
  etc. (geographic tagging of Azure prefixes)
  
  Bidirectional Forwarding Detection:
  Azure supports BFD on ExpressRoute (min interval: 300ms)
  
  Azure VPN Gateway BGP:
  BGP over IKEv2/IPsec
  Azure ASN: 65515 (default) or custom
  BGP endpoint: 169.254.21.1/169.254.22.1 (link-local inside tunnel)
  
  VNet Peering and BGP:
  VNet-to-VNet peering does NOT use BGP internally.
  For hub-spoke with ExpressRoute, use route server:
  
  Azure Route Server:
  Runs BGP inside Azure VNet.
  NVA (Network Virtual Appliance) peers with Route Server.
  Route Server programs VNet routes from NVA.
  Route Server ASN: 65515 (fixed)
  
  NVA (e.g., FRR VM) peers with Route Server:
  router bgp 65100  ! NVA ASN
   neighbor 10.0.0.4 remote-as 65515  ! Route Server IP 1
   neighbor 10.0.0.5 remote-as 65515  ! Route Server IP 2
   address-family ipv4 unicast
    neighbor 10.0.0.4 activate
    neighbor 10.0.0.5 activate
    network 10.1.0.0/16  ! Advertise to VNet
   exit-address-family
  !
```

### 23.3 GCP BGP — Cloud Interconnect and Cloud Router

```
Google Cloud Router:
  Fully managed BGP service that runs inside GCP.
  Used with: Cloud Interconnect (Dedicated/Partner), HA VPN.
  
  ASN: 16550 (Interconnect), 65500-65535 (configurable)
  
  Cloud Interconnect BGP:
  Dedicated Interconnect: 10G or 100G physical cross-connect at colocation
  Partner Interconnect: Through service provider, 50M to 10G
  
  VLAN Attachment (Interconnect Attachment):
  BGP session per VLAN attachment.
  Each attachment has a unique BGP peer IP (Link-local: 169.254.0.0/16).
  
  Cloud Router BGP session:
  Customer router (ASN: yours) ↔ Cloud Router (ASN: 16550)
  
  Route advertisement:
  GCP advertises: VPC subnet CIDRs automatically
  Customer advertises: on-prem subnets
  
  Multi-exit / HA:
  Two VLAN attachments (two BGP sessions) for 99.9% SLA.
  Four attachments (two locations) for 99.99% SLA.
  
  Traffic path selection:
  GCP uses MED to prefer specific attachment.
  Set MED=100 on primary, MED=200 on backup VLAN attachment.
  
  BGP Custom Learned Routes:
  Custom routes learned via BGP can be imported to VPC.
  Or you can have Cloud Router only import specific prefixes.
  
  Cloud Router prefix limits:
  Advertise to GCP: 1000 prefixes per VPN tunnel
  Receive from GCP: 100 prefixes per VPN tunnel, more for interconnect
  
  Dynamic routing modes:
  Regional: BGP routes apply only to region containing the router
  Global: BGP routes apply to all regions (requires Premium network tier)
  
  Bidirectional Forwarding Detection:
  Cloud Router supports BFD for Interconnect (99 ms min interval)
  For VPN: BFD not supported (VPN doesn't need it — VPN failure detection is fast)
  
  GKE (Google Kubernetes Engine) BGP:
  GKE Dataplane V2 (Cilium-based) handles internal BGP.
  External BGP via Cloud Router (for LoadBalancer IPs and Interconnect).
  GKE also supports "Network Endpoint Groups" (NEGs) for direct pod routing.
```

---

## 24. BGP Security — RPKI, BGPsec, Filtering

### 24.1 BGP Vulnerabilities

```
BGP was designed for mutual trust. Internet-scale BGP has no authentication
for route origin or path. This leads to:

1. Route Hijacking:
   Any AS can announce any prefix.
   Pakistan Telecom hijacked YouTube (2008): 
   Announced 208.65.153.0/24 (YouTube's /24) — more specific than YouTube's /22.
   Millions of users globally redirected.

2. Route Leaks:
   AS accidentally re-advertises routes it shouldn't.
   Cloudflare outage (2019): Verizon accepted leaked routes from small ISP.
   Traffic for major Internet services went through a small network.

3. BGP Path Manipulation:
   Inserting false AS numbers in AS_PATH.
   Making traffic transit through specific ASes.

4. Prefix de-aggregation attacks:
   Announce more-specific prefixes to attract traffic.
```

### 24.2 RPKI (Resource Public Key Infrastructure)

```
RPKI provides cryptographic attestation of:
  "AS X is authorized to originate prefix P"
  
This is done via ROAs (Route Origin Authorizations).

RPKI Architecture:
  ┌──────────────────────────────────────────────────────────────┐
  │  IANA                                                        │
  │  (Trust Anchor)                                              │
  └──────────┬───────────────────────────────────────┬──────────┘
             │                                        │
  ┌──────────▼──────────┐                  ┌──────────▼──────────┐
  │  ARIN (Americas)    │                  │  RIPE NCC (Europe)  │
  │  (Regional RIR)     │                  │  (Regional RIR)     │
  └──────────┬──────────┘                  └──────────┬──────────┘
             │                                        │
  ┌──────────▼──────────┐                  ┌──────────▼──────────┐
  │  ISP/LIR            │                  │  ISP/LIR            │
  │  Signs ROAs         │                  │  Signs ROAs         │
  └──────────┬──────────┘                  └──────────┬──────────┘
             │ RPKI Publication Point                  │
             │ (rsync / RRDP)                          │
  ┌──────────▼──────────────────────────────▼──────────┐
  │              RPKI Cache Validator                   │
  │  (Routinator, OctoRPKI, Fort, RPKI-client)         │
  └──────────────────────────┬─────────────────────────┘
                             │ RTR Protocol (RFC 8210)
  ┌──────────────────────────▼─────────────────────────┐
  │              BGP Router (FRR, BIRD, IOS-XR)         │
  │  Validates routes against RPKI database             │
  └────────────────────────────────────────────────────┘

ROA (Route Origin Authorization):
  Signed object containing:
  - Holder ASN (who can originate)
  - IP prefix
  - Max prefix length
  - Validity period
  
  Signed with holder's private key (certified by parent RIR in the chain).
  
  Example ROA:
  ASN: 15169 (Google)
  Prefix: 8.8.8.0/24
  Max Length: 24
  
  Meaning: AS 15169 may originate 8.8.8.0/24 or more-specific up to /24.

ROA Validation States:
  Valid:    Route's origin AS and prefix match a ROA.
  Invalid:  A ROA exists for this prefix but origin AS doesn't match,
            OR prefix is more specific than ROA max length.
  Not Found: No ROA exists for this prefix (unknown).
  
  RPKI-based BGP Origin Validation (RFC 6811):
  Routers can filter Invalid routes (highest security)
  Or just mark routes with validation state.

RTR Protocol (RPKI to Router, RFC 8210):
  The validated RPKI data is pushed from cache to routers via RTR.
  
  RTR PDU types:
  Serial Notify: Cache tells router new data is available
  Serial Query: Router requests updates since last serial number
  Reset Query: Router requests full table
  Cache Response: Start of cache data transfer
  IPv4 Prefix: A validated ROA entry
  IPv6 Prefix: Same for IPv6
  End of Data: End of transfer
  Cache Reset: Cache can't serve, reset needed
  
  RTR runs over TCP port 323 (or TLS for security).

FRR RPKI configuration:
  rpki
   rpki polling_period 3600
   rpki cache 10.0.0.10 3323 preference 1   ! Routinator instance
   rpki cache 10.0.0.11 3323 preference 2   ! Backup cache
  !
  router bgp 65000
   address-family ipv4 unicast
    bgp bestpath prefix-validate allow-invalid  ! Don't filter invalids, just tag
    ! OR:
    ! bgp bestpath prefix-validate                ! Filter invalids
   exit-address-family
  !
  route-map RPKI_FILTER deny 10
   match rpki invalid
  route-map RPKI_FILTER permit 20
  !
  router bgp 65000
   neighbor 10.0.0.1 route-map RPKI_FILTER in
  !
  
  Show commands:
  # show rpki prefix-table
  # show rpki cache-connection
  # show bgp ipv4 unicast 8.8.8.0/24 rpki

Routinator (NLnet Labs):
  Most popular RPKI validator.
  Written in Rust.
  Runs as daemon, serves RTR protocol and HTTP API.
  
  # Install and run
  routinator -v vrps       # Print all validated ROAs
  routinator server --rtr 0.0.0.0:3323 --http 0.0.0.0:8080
  
  # Query
  curl http://localhost:8080/metrics
  curl http://localhost:8080/api/v1/validity/15169/8.8.8.0/24
```

### 24.3 BGPsec (RFC 8205)

```
BGPsec goes further than RPKI — it protects the entire AS_PATH, not just origin.

BGPsec signs each AS_PATH segment as a route traverses the Internet.

Architecture:
  AS A originates prefix P.
  A signs: (prefix P, ASN_A, next-AS_B)
  Signature includes the path so far.
  
  B re-signs: (prefix P, ASN_A, ASN_B, next-AS_C)
  Each AS signs the accumulated path.
  
  C validates the full chain of signatures.

Deployment requirements:
  - Every AS in the path must support BGPsec
  - BGPsec must be deployed end-to-end for full protection
  - Partial deployment = partial security (best security when fully deployed)
  - Performance overhead: crypto operations per path segment
  
BGPsec OPEN capability:
  Code: not yet standardized in capability code space (uses existing mechanism)
  Negotiated per AFI/SAFI
  
BGPsec UPDATE format:
  Extended format — replaces AS_PATH with BGPsec_Path attribute
  Contains: list of (AS number, signature) pairs
  
  Each entry signed with BGPsec Router Key (separate from RPKI certificate).
  BGPsec Router Keys are also published in RPKI.
  
Status (2024):
  RFC published (RFC 8205) but minimal deployment.
  Operational complexity and performance concerns limit adoption.
  RPKI Origin Validation is the practical deployed solution today.
  BGPsec may gain traction as hardware improves.
```

### 24.4 Route Filtering Best Practices

```
MANRS (Mutually Agreed Norms for Routing Security) principles:
  1. Filter based on IRR (Internet Routing Registry) data
  2. Prevent IP spoofing (ingress filtering / BCP38)
  3. Facilitate global communication (contacts, policies published)
  4. Facilitate validation of routing information (RPKI)

IRR Filtering:
  IRR databases (RIPE, RADB, ARIN, etc.) contain:
  - route: objects (which ASN can originate which prefix)
  - as-set: objects (groups of ASNs)
  - route-set: groups of prefixes
  - aut-num: AS routing policy
  
  Tools: bgpq3/bgpq4 generate prefix-lists from IRR data
  
  $ bgpq4 -A -4 -J AS-CLOUDFLARE > cloudflare_prefixes.txt
  
  BGP prefix filters generated from IRR:
  neighbor 10.0.0.1 prefix-list CUSTOMER_PREFIXES in
  
  Bogon filtering (RFC 5735, RFC 6890):
  Always filter:
  - 0.0.0.0/8
  - 10.0.0.0/8 (private)
  - 100.64.0.0/10 (shared address space)
  - 127.0.0.0/8 (loopback)
  - 169.254.0.0/16 (link-local)
  - 172.16.0.0/12 (private)
  - 192.0.0.0/24 (IETF protocol assignments)
  - 192.168.0.0/16 (private)
  - 198.18.0.0/15 (benchmarking)
  - 198.51.100.0/24 (documentation)
  - 203.0.113.0/24 (documentation)
  - 240.0.0.0/4 (reserved)
  - 255.255.255.255/32 (broadcast)
  
  Maximum prefix length:
  Filter prefixes longer than /24 for IPv4 (deaggregation waste)
  Filter prefixes longer than /48 for IPv6
  
  FRR prefix-list for bogons:
  ip prefix-list BOGONS deny 0.0.0.0/8 le 32
  ip prefix-list BOGONS deny 10.0.0.0/8 le 32
  ip prefix-list BOGONS deny 100.64.0.0/10 le 32
  ip prefix-list BOGONS deny 127.0.0.0/8 le 32
  ip prefix-list BOGONS deny 169.254.0.0/16 le 32
  ip prefix-list BOGONS deny 172.16.0.0/12 le 32
  ip prefix-list BOGONS deny 192.0.2.0/24 le 32
  ip prefix-list BOGONS deny 192.168.0.0/16 le 32
  ip prefix-list BOGONS deny 198.18.0.0/15 le 32
  ip prefix-list BOGONS deny 198.51.100.0/24 le 32
  ip prefix-list BOGONS deny 203.0.113.0/24 le 32
  ip prefix-list BOGONS deny 240.0.0.0/4 le 32
  ip prefix-list BOGONS deny 255.255.255.255/32
  ip prefix-list BOGONS deny 0.0.0.0/0 ge 25     ! Block too-specific
  ip prefix-list BOGONS permit 0.0.0.0/0 le 24   ! Allow normal routes
  
  Graceful Shutdown (RFC 9003):
  When taking down a BGP session gracefully:
  1. Send NOTIFICATION with Cease/Administrative Shutdown (code 6/2)
     with optional text message (max 128 UTF-8 bytes)
  2. Or: Set LOCAL_PREF=0, drain traffic, then shut
  3. RFC 9003: "GRACEFUL_SHUTDOWN" community (65535:0)
     Receiving routers should set LOCAL_PREF=0 for routes tagged with it.
     
  FRR:
  neighbor 10.0.0.1 shutdown message "Maintenance window 2024-01-01"
  
  BGP Route Leak Prevention (RFC 9234):
  New attribute: ONLY_TO_CUSTOMER (OTC)
  Set when advertising to a customer.
  If received from a customer and already has OTC → discard (it was leaked).
```

---

## 25. Linux Kernel BGP Internals

### 25.1 Linux Networking Stack Overview for BGP

```
BGP sits entirely in userspace. The kernel provides:
1. TCP/IP stack for BGP sessions
2. Routing table (FIB - Forwarding Information Base)
3. Netlink interface for route management
4. Policy routing (multiple routing tables, rules)

Kernel routing architecture:

  ┌────────────────────────────────────────────────────────────────┐
  │  Userspace                                                     │
  │  FRR (bgpd, zebra, staticd, bfdd, ...)                        │
  │                 │ Netlink socket (NETLINK_ROUTE)               │
  └─────────────────┼──────────────────────────────────────────────┘
                    │ AF_NETLINK, NETLINK_ROUTE
  ┌─────────────────▼──────────────────────────────────────────────┐
  │  Kernel                                                        │
  │                                                                │
  │  ┌────────────────────────────────────┐                        │
  │  │  Routing subsystem                  │                        │
  │  │                                    │                        │
  │  │  FIB (Forwarding Information Base)  │                        │
  │  │  ┌─────────────────────────────┐  │                        │
  │  │  │ Main table (table 254)       │  │  ← BGP routes go here  │
  │  │  │ Local table (table 255)      │  │                        │
  │  │  │ Default table (table 253)    │  │                        │
  │  │  │ Custom tables (1-252)        │  │                        │
  │  │  └─────────────────────────────┘  │                        │
  │  │                                    │                        │
  │  │  ip rules → table lookup order     │                        │
  │  └────────────────────────────────────┘                        │
  │                                                                │
  │  ┌────────────────────────────────────┐                        │
  │  │  TC (Traffic Control)               │                        │
  │  │  eBPF programs                     │                        │
  │  └────────────────────────────────────┘                        │
  └────────────────────────────────────────────────────────────────┘
```

### 25.2 Netlink Interface for Route Management

```c
/* How FRR (zebra) installs a BGP route into the kernel via Netlink */

#include <linux/netlink.h>
#include <linux/rtnetlink.h>
#include <net/if.h>

/* Netlink message structure for route addition:
   
   ┌─────────────────────────────────────────────────┐
   │ nlmsghdr (16 bytes)                             │
   │   nlmsg_len: total message length               │
   │   nlmsg_type: RTM_NEWROUTE                      │
   │   nlmsg_flags: NLM_F_REQUEST | NLM_F_CREATE    │
   │   nlmsg_seq: sequence number                    │
   │   nlmsg_pid: 0 (kernel) or our PID             │
   ├─────────────────────────────────────────────────┤
   │ rtmsg (12 bytes)                                │
   │   rtm_family: AF_INET                           │
   │   rtm_dst_len: 24 (prefix length)               │
   │   rtm_src_len: 0                                │
   │   rtm_tos: 0                                    │
   │   rtm_table: RT_TABLE_MAIN (254)                │
   │   rtm_protocol: RTPROT_BGP (186)               │
   │   rtm_scope: RT_SCOPE_UNIVERSE (0)              │
   │   rtm_type: RTN_UNICAST (1)                     │
   │   rtm_flags: 0                                  │
   ├─────────────────────────────────────────────────┤
   │ RTA_DST (prefix address as inet)                │
   │   rtattr: rta_len, RTA_DST, value=10.0.1.0      │
   ├─────────────────────────────────────────────────┤
   │ RTA_GATEWAY (next-hop)                          │
   │   rtattr: rta_len, RTA_GATEWAY, value=10.0.0.1  │
   ├─────────────────────────────────────────────────┤
   │ RTA_OIF (output interface index)                │
   │   rtattr: rta_len, RTA_OIF, value=    │
   ├─────────────────────────────────────────────────┤
   │ RTA_PRIORITY (metric)                           │
   │   rtattr: rta_len, RTA_PRIORITY, value=20      │
   └─────────────────────────────────────────────────┘
*/

/* Simplified Netlink route add */
int netlink_route_add(int sock_fd, uint32_t prefix, uint8_t prefix_len,
                      uint32_t nexthop, int oif) {
    struct {
        struct nlmsghdr nlh;
        struct rtmsg    rtm;
        char            attrs[256];
    } req = {};
    
    req.nlh.nlmsg_len   = NLMSG_LENGTH(sizeof(struct rtmsg));
    req.nlh.nlmsg_type  = RTM_NEWROUTE;
    req.nlh.nlmsg_flags = NLM_F_REQUEST | NLM_F_CREATE | NLM_F_REPLACE;
    req.nlh.nlmsg_seq   = 1;
    
    req.rtm.rtm_family   = AF_INET;
    req.rtm.rtm_dst_len  = prefix_len;
    req.rtm.rtm_table    = RT_TABLE_MAIN;
    req.rtm.rtm_protocol = RTPROT_BGP;   /* 186 = BGP */
    req.rtm.rtm_scope    = RT_SCOPE_UNIVERSE;
    req.rtm.rtm_type     = RTN_UNICAST;
    
    /* Add RTA_DST attribute */
    struct rtattr *rta = (struct rtattr *)
        ((char *)&req + NLMSG_ALIGN(req.nlh.nlmsg_len));
    rta->rta_type = RTA_DST;
    rta->rta_len  = RTA_LENGTH(4);
    memcpy(RTA_DATA(rta), &prefix, 4);
    req.nlh.nlmsg_len = NLMSG_ALIGN(req.nlh.nlmsg_len) + rta->rta_len;
    
    /* Add RTA_GATEWAY */
    rta = (struct rtattr *)((char *)&req + NLMSG_ALIGN(req.nlh.nlmsg_len));
    rta->rta_type = RTA_GATEWAY;
    rta->rta_len  = RTA_LENGTH(4);
    memcpy(RTA_DATA(rta), &nexthop, 4);
    req.nlh.nlmsg_len = NLMSG_ALIGN(req.nlh.nlmsg_len) + rta->rta_len;
    
    /* Add RTA_OIF (output interface) */
    rta = (struct rtattr *)((char *)&req + NLMSG_ALIGN(req.nlh.nlmsg_len));
    rta->rta_type = RTA_OIF;
    rta->rta_len  = RTA_LENGTH(4);
    memcpy(RTA_DATA(rta), &oif, 4);
    req.nlh.nlmsg_len = NLMSG_ALIGN(req.nlh.nlmsg_len) + rta->rta_len;
    
    struct iovec iov = { &req, req.nlh.nlmsg_len };
    struct sockaddr_nl sa = { .nl_family = AF_NETLINK };
    struct msghdr msg = { &sa, sizeof(sa), &iov, 1, NULL, 0, 0 };
    
    return sendmsg(sock_fd, &msg, 0);
}
```

### 25.3 Linux FIB Internals

```
Linux kernel routing table structure (kernel/net/ipv4/fib_trie.c):

The FIB (Forwarding Information Base) uses an LC-trie (Level Compressed trie).
This provides O(log n) or better lookup for prefix matching.

Key structures:
  struct fib_table:          Per routing table (main, local, custom)
  struct trie:               LC-trie root
  struct tnode:              Internal trie node
  struct leaf:               Leaf node (contains actual route info)
  struct fib_alias:          Route alias (multiple routes per prefix, by TOS/priority)
  struct fib_info:           Next-hop information (nexthop IPs, interfaces)
  struct fib_nh:             Individual nexthop entry
  struct fib_result:         Result of FIB lookup

FIB lookup path:
  ip_route_input() →
  fib_lookup() →
  fib_table_lookup() →
    trie_lookup() → O(prefix bits) comparisons
  Returns: struct fib_result

Route installation:
  RTM_NEWROUTE netlink message →
  inet_rtm_newroute() →
  fib_table_insert() →
    trie_insert() → updates LC-trie

ECMP in the kernel:
  fib_info with multiple fib_nh entries:
  
  struct fib_info {
      ...
      int fib_nhs;          /* number of nexthops */
      struct fib_nh fib_nh[0]; /* variable-length array */
  };
  
  struct fib_nh {
      struct net_device *nh_dev;    /* output interface */
      unsigned int nh_flags;
      unsigned char nh_scope;
      int nh_weight;                /* ECMP weight */
      __be32 nh_gw;                 /* gateway IP */
      ...
  };
  
  ECMP flow selection:
  fib_select_multipath() → hash on (src, dst, proto) → select nh
  
Linux kernel route protocols (rtm_protocol field):
  RTPROT_UNSPEC   = 0
  RTPROT_KERNEL   = 2   (kernel installs automatically)
  RTPROT_BOOT     = 3   (installed during boot)
  RTPROT_STATIC   = 4   (admin installed)
  RTPROT_GATED    = 8   (historic)
  RTPROT_RA       = 9   (ICMP Router Advertisement)
  RTPROT_MRT      = 10  (Merit MRT)
  RTPROT_ZEBRA    = 11  (Zebra/FRR)
  RTPROT_BIRD     = 12  (BIRD)
  RTPROT_DNROUTED = 13
  RTPROT_XORP     = 14
  RTPROT_NTK      = 15  (Netsukuku)
  RTPROT_DHCP     = 16  (DHCP)
  RTPROT_MROUTED  = 17  (multicast)
  RTPROT_KEEPALIVED = 18
  RTPROT_BABEL    = 42
  RTPROT_BGP      = 186 (RFC 8202)
  RTPROT_ISIS     = 187
  RTPROT_OSPF     = 188
  RTPROT_RIP      = 189
  RTPROT_EIGRP    = 192

VRF in Linux:
  Linux VRF (Virtual Routing and Forwarding) uses a separate routing table per VRF.
  
  # Create VRF device (links to table 10)
  ip link add vrf-mgmt type vrf table 10
  ip link set vrf-mgmt up
  
  # Add interface to VRF
  ip link set eth1 master vrf-mgmt
  
  # Routes in VRF table
  ip route add 192.168.1.0/24 via 10.0.0.1 table 10
  
  # IP rule: packets with vrf mark use table 10
  ip rule add oif vrf-mgmt table 10
  ip rule add iif vrf-mgmt table 10
  
  FRR VRF integration:
  FRR creates vrf instances and uses the kernel VRF device.
  Each VRF gets its own routing table.
  BGP VRFs use separate BGP instances.
  
  router bgp 65000 vrf customer-a
   neighbor 10.1.0.1 remote-as 65100
   address-family ipv4 unicast
    redistribute connected
   exit-address-family
  !
```

### 25.4 TCP MD5 for BGP Sessions (Linux Kernel)

```
BGP uses TCP MD5 signature option (RFC 2385) for peer authentication.
This is a TCP-level mechanism — the kernel signs/verifies each TCP segment.

How it works:
  1. Both BGP peers configured with same password
  2. Kernel computes MD5 over: TCP pseudo-header + TCP header + data + password
  3. MD5 digest placed in TCP option (kind=19, length=18, 16 bytes of MD5)
  4. Receiving kernel recomputes and verifies before accepting segment

Linux kernel implementation:
  tcp_v4_md5_hash_skb() in net/ipv4/tcp_ipv4.c
  Uses TCP_MD5SIG socket option
  
  /* How FRR sets MD5 password */
  int bgp_md5_set(int sock, union sockunion *su, const char *password) {
      struct tcp_md5sig md5;
      memset(&md5, 0, sizeof(md5));
      
      memcpy(&md5.tcpm_addr, &su->sin, sizeof(struct sockaddr_in));
      md5.tcpm_prefixlen = 32; /* exact match */
      md5.tcpm_keylen = strlen(password);
      memcpy(md5.tcpm_key, password, md5.tcpm_keylen);
      
      return setsockopt(sock, IPPROTO_TCP, TCP_MD5SIG,
                        &md5, sizeof(md5));
  }
  
  Note: MD5 has weaknesses. RFC 5925 defines TCP-AO (Authentication Option)
  as a replacement with stronger algorithms (HMAC-SHA1, AES-CMAC).
  Linux kernel supports TCP-AO since 6.7.

TCP session behavior for BGP:
  SO_KEEPALIVE: NOT used for BGP sessions (BGP has its own keepalive)
  TCP_NODELAY: YES — BGP needs immediate delivery, no Nagle
  IP_TTL: 1 (eBGP, EBGP multihop=2+), 255 (GTSM)
  
  GTSM (Generalized TTL Security Mechanism, RFC 5082):
  For directly-connected eBGP: set TTL=255 outbound, reject if received TTL<254
  Prevents spoofed TCP packets from remote hosts (they can't set TTL=255 and have it arrive at 254+)
  
  FRR: neighbor X.X.X.X ttl-security hops 1
  Linux: IP_MINTTL socket option
    int ttl = 254; /* minimum acceptable TTL */
    setsockopt(sock, IPPROTO_IP, IP_MINTTL, &ttl, sizeof(ttl));
```

---

## 26. FRRouting (FRR) — Architecture and Internals

### 26.1 FRR Architecture

```
FRR is the most widely-deployed open-source routing suite (Linux, BSD).
Used in: Cumulus Linux, SONiC, OpenWRT, network appliances, Kubernetes CNIs.

Process architecture:
  ┌─────────────────────────────────────────────────────────────────┐
  │                     FRR Process Suite                           │
  │                                                                 │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
  │  │  bgpd    │  │  ospfd   │  │  isisd   │  │  ldpd    │       │
  │  │ (BGP)    │  │ (OSPF)   │  │ (IS-IS)  │  │ (LDP)    │       │
  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
  │       │             │             │              │              │
  │       └─────────────┴─────────────┴──────────────┘             │
  │                              │ ZAPI (Zebra API)                 │
  │                     ┌────────▼───────┐                          │
  │                     │    zebra       │  ← Route manager        │
  │                     │  (RIB manager) │     Netlink to kernel    │
  │                     └────────────────┘                          │
  │                                                                 │
  │  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
  │  │  bfdd    │  │  staticd │  │  vtysh   │  ← CLI               │
  │  │  (BFD)   │  │ (Static) │  │          │                      │
  │  └──────────┘  └──────────┘  └──────────┘                      │
  └─────────────────────────────────────────────────────────────────┘
                              │ Netlink
  ┌───────────────────────────▼───────────────────────────────────┐
  │                   Linux Kernel                                │
  └───────────────────────────────────────────────────────────────┘

ZAPI (Zebra API):
  Unix socket between daemons and zebra.
  Protocol: custom binary (not Netlink).
  Messages: ZAPI_ROUTE_ADD, ZAPI_ROUTE_DELETE, ZAPI_REDISTRIBUTE_ADD, etc.
  
  Zebra acts as the RIB (Routing Information Base):
  - Receives routes from all protocol daemons
  - Applies administrative distance to select best routes
  - Installs best routes into kernel via Netlink
  - Distributes routes between protocols (redistribution)

bgpd internal threads:
  FRR uses event-driven I/O (not traditional threads per connection).
  
  Event loop: thread.c / event.c (FRR's own event library, not libevent)
  
  Events:
  - Socket readable: process incoming BGP message
  - Socket writable: flush output buffer
  - Timer: keepalive, hold timer, ConnectRetry
  - Signal: configuration reload, shutdown
  
  Per-peer state:
  struct peer {
      struct bgp *bgp;          /* BGP instance */
      union sockunion su;       /* peer address */
      int fd;                   /* TCP socket */
      int status;               /* FSM state */
      
      /* Buffers */
      struct stream *ibuf;      /* input buffer */
      struct stream *obuf;      /* output buffer */
      struct stream_fifo *obuf_work; /* write queue */
      
      /* Timers */
      struct event *t_holdtime;
      struct event *t_keepalive;
      struct event *t_connect;
      
      /* BGP table pointers */
      struct bgp_table *rib[AFI_MAX][SAFI_MAX];
      
      /* Attributes */
      uint32_t weight;
      uint32_t local_pref;
      ...
  };
```

### 26.2 bgpd Route Processing Pipeline

```
Incoming UPDATE message processing:

bgp_read() [io.c]
  ↓ read from socket into ibuf
bgp_process_reads() [io.c]
  ↓ 
bgp_read_packet() [packet.c]
  ↓ validate header (marker, length, type)
bgp_process_packet() [packet.c]
  ↓ dispatch by type
bgp_update_receive() [update.c]
  ↓ parse UPDATE:
    - Parse withdrawn routes
    - Parse path attributes (loop: parse each attribute TLV)
    - Parse NLRI
  ↓
bgp_update_main() [update.c]
  For each prefix in NLRI:
  ↓
bgp_update() [update.c]
  ↓ Apply inbound route-map policy
bgp_adj_in_set() [update.c]
  ↓ Store in Adj-RIB-In (if soft-reconfiguration-inbound)
bgp_process() [route.c]  ← DECISION PROCESS
  ↓ Run decision process for this prefix
  ↓ Select best path (bgp_best_selection)
  ↓ Update Loc-RIB
  ↓ Mark for advertisement to peers
bgp_process_queue_work() [route.c]
  ↓ Batched processing of changed prefixes
bgp_zebra_announce() [zebra.c]
  ↓ Install/withdraw route via ZAPI to zebra
bgp_adj_out_set_bypass() [update.c]
  ↓ Update Adj-RIB-Out for each peer
bgp_generate_updates() [update.c]
  ↓ Generate UPDATE messages for peers (apply outbound policy)
bgp_write_update() [packet.c]
  ↓ Serialize UPDATE
bgp_write() [io.c]
  ↓ Send via TCP socket

Key data structures:
  struct bgp_node:     An entry in the BGP routing table (per prefix)
  struct bgp_path_info: A path (candidate route) for a prefix
  struct attr:         BGP path attributes
  struct bgp_table:    The routing table (uses patricia trie / rn_table)
  
  bgp_path_info flags:
  BGP_PATH_VALID     = route is usable
  BGP_PATH_SELECTED  = this is the best path  
  BGP_PATH_STALE     = route-refresh pending, route is stale
  BGP_PATH_HISTORY   = historical (for dampening)
  BGP_PATH_DAMP_SUPPRESSED = suppressed by route dampening
  BGP_PATH_REMOVED   = marked for removal
```

### 26.3 FRR BGP Route Dampening

```
BGP route dampening suppresses flapping routes (RFC 2439).

Concept:
  Each route gets a "figure of merit" (penalty).
  Each flap (withdraw+readvertise): penalty += 1000
  Penalty decays exponentially over time.
  When penalty > suppress-limit → route suppressed
  When penalty < reuse-limit → route re-advertised

Parameters:
  Half-life:       Time for penalty to decay by half (default: 15min)
  Reuse limit:     Penalty below which route is unsuppressed (default: 750)
  Suppress limit:  Penalty above which route is suppressed (default: 2000)
  Max suppress time: Maximum suppression duration (default: 60min)

FRR config:
  router bgp 65000
   bgp dampening 15 750 2000 60

Show commands:
  show ip bgp dampened-paths
  show ip bgp flap-statistics

Note: Dampening is disabled by default in modern FRR.
RFC 7196 ("Why Filtering BGP Routes from Customers is a Good Idea")
suggests dampening is often counterproductive for Internet BGP.
It's more useful in specific environments (DC, WAN edge).
```

---

## 27. C Implementation — BGP State Machine and Parser

### 27.1 Complete BGP FSM in C

```c
/* bgp_fsm.c — Complete BGP FSM implementation */
/* Demonstrates the FSM, message parsing, and session management */

#include 
#include 
#include 
#include 
#include 
#include <sys/socket.h>
#include <sys/time.h>
#include <netinet/in.h>
#include <netinet/tcp.h>
#include <arpa/inet.h>
#include 

/* BGP FSM States */
typedef enum {
    BGP_STATE_IDLE         = 0,
    BGP_STATE_CONNECT      = 1,
    BGP_STATE_ACTIVE        = 2,
    BGP_STATE_OPENSENT     = 3,
    BGP_STATE_OPENCONFIRM  = 4,
    BGP_STATE_ESTABLISHED  = 5,
    BGP_STATE_MAX
} bgp_state_t;

static const char *bgp_state_str[] = {
    "Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"
};

/* BGP Message Types */
#define BGP_MSG_OPEN         1
#define BGP_MSG_UPDATE       2
#define BGP_MSG_NOTIFICATION 3
#define BGP_MSG_KEEPALIVE    4
#define BGP_MSG_ROUTE_REFRESH 5

/* BGP Header */
#define BGP_MARKER_SIZE  16
#define BGP_HEADER_SIZE  19

/* Error codes */
#define BGP_ERR_HEADER      1
#define BGP_ERR_OPEN        2
#define BGP_ERR_UPDATE      3
#define BGP_ERR_HOLD_TIMER  4
#define BGP_ERR_FSM         5
#define BGP_ERR_CEASE       6

/* BGP attribute types */
#define BGP_ATTR_ORIGIN       1
#define BGP_ATTR_AS_PATH      2
#define BGP_ATTR_NEXT_HOP     3
#define BGP_ATTR_MED          4
#define BGP_ATTR_LOCAL_PREF   5
#define BGP_ATTR_COMMUNITY    8

/* Attribute flags */
#define BGP_ATTR_FLAG_OPTIONAL    0x80
#define BGP_ATTR_FLAG_TRANSITIVE  0x40
#define BGP_ATTR_FLAG_PARTIAL     0x20
#define BGP_ATTR_FLAG_EXTLEN      0x10

/* Default timers (seconds) */
#define BGP_DEFAULT_HOLD_TIME      90
#define BGP_DEFAULT_KEEPALIVE      30
#define BGP_DEFAULT_CONNECT_RETRY  120
#define BGP_DEFAULT_OPEN_HOLD      240

/* BGP header structure */
typedef struct {
    uint8_t  marker[BGP_MARKER_SIZE];
    uint16_t length;
    uint8_t  type;
} __attribute__((packed)) bgp_header_t;

/* BGP OPEN message */
typedef struct {
    uint8_t  version;
    uint16_t my_as;
    uint16_t hold_time;
    uint32_t bgp_id;
    uint8_t  opt_len;
    uint8_t  opt_params[];
} __attribute__((packed)) bgp_open_t;

/* BGP NOTIFICATION message */
typedef struct {
    uint8_t  error_code;
    uint8_t  error_subcode;
    uint8_t  data[];
} __attribute__((packed)) bgp_notification_t;

/* BGP path attribute */
typedef struct {
    uint8_t  flags;
    uint8_t  type;
    union {
        uint8_t  len1;         /* 1-byte length (normal) */
        uint16_t len2;         /* 2-byte length (extended) */
    };
} __attribute__((packed)) bgp_attr_t;

/* BGP route: prefix + attributes */
typedef struct bgp_route {
    struct in_addr prefix;
    uint8_t        prefix_len;
    uint32_t       nexthop;
    uint32_t       local_pref;
    uint32_t       med;
    uint8_t        origin;
    uint8_t        as_path[256];
    int            as_path_len;
    struct bgp_route *next;
} bgp_route_t;

/* BGP session / peer */
typedef struct {
    int           fd;             /* TCP socket */
    bgp_state_t   state;
    
    /* Configuration */
    uint32_t      local_asn;
    uint32_t      remote_asn;
    uint32_t      local_bgp_id;
    struct in_addr remote_addr;
    uint16_t      hold_time;      /* negotiated */
    uint16_t      keepalive_time;
    
    /* Timers (expiry time as epoch seconds) */
    time_t        hold_timer;
    time_t        keepalive_timer;
    time_t        connect_retry_timer;
    
    /* I/O buffers */
    uint8_t       ibuf[65536];
    int           ibuf_len;
    uint8_t       obuf[65536];
    int           obuf_len;
    
    /* Routes */
    bgp_route_t  *routes;
    
    /* Statistics */
    uint64_t      msg_sent;
    uint64_t      msg_recv;
    uint64_t      updates_in;
    uint64_t      updates_out;
} bgp_peer_t;

/* ─── Utility functions ─── */

static time_t bgp_now(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return ts.tv_sec;
}

static int bgp_send(bgp_peer_t *peer, const uint8_t *buf, int len) {
    int ret = send(peer->fd, buf, len, MSG_NOSIGNAL);
    if (ret > 0) peer->msg_sent++;
    return ret;
}

/* Build a BGP header */
static void bgp_build_header(uint8_t *buf, uint16_t length, uint8_t type) {
    bgp_header_t *hdr = (bgp_header_t *)buf;
    memset(hdr->marker, 0xFF, BGP_MARKER_SIZE);
    hdr->length = htons(length);
    hdr->type   = type;
}

/* ─── Message builders ─── */

/* Build and send KEEPALIVE */
static int bgp_send_keepalive(bgp_peer_t *peer) {
    uint8_t buf[BGP_HEADER_SIZE];
    bgp_build_header(buf, BGP_HEADER_SIZE, BGP_MSG_KEEPALIVE);
    return bgp_send(peer, buf, BGP_HEADER_SIZE);
}

/* Build and send OPEN message */
static int bgp_send_open(bgp_peer_t *peer) {
    uint8_t buf[256];
    int pos = BGP_HEADER_SIZE;
    
    buf[pos++] = 4;  /* BGP version 4 */
    
    /* My AS (16-bit for simplicity — use AS_TRANS=23456 for 32-bit ASNs) */
    uint16_t my_as = (peer->local_asn > 65535) ? 23456 : (uint16_t)peer->local_asn;
    buf[pos++] = (my_as >> 8) & 0xFF;
    buf[pos++] = my_as & 0xFF;
    
    /* Hold time */
    uint16_t hold = BGP_DEFAULT_HOLD_TIME;
    buf[pos++] = (hold >> 8) & 0xFF;
    buf[pos++] = hold & 0xFF;
    
    /* BGP Router ID */
    uint32_t id = htonl(peer->local_bgp_id);
    memcpy(&buf[pos], &id, 4);
    pos += 4;
    
    /* Optional parameters: capability for 4-byte ASN */
    uint8_t opt_start = pos;
    buf[pos++] = 0;   /* placeholder for opt_len */
    
    /* Capability: 4-byte AS number (code=65, len=4, value=ASN) */
    buf[pos++] = 2;   /* param type = capabilities */
    buf[pos++] = 6;   /* param len = 6 */
    buf[pos++] = 65;  /* capability code = 4-byte ASN */
    buf[pos++] = 4;   /* capability data length */
    uint32_t asn = htonl(peer->local_asn);
    memcpy(&buf[pos], &asn, 4);
    pos += 4;
    
    /* Update opt_len */
    buf[opt_start] = pos - opt_start - 1;
    
    /* Fill header */
    bgp_build_header(buf, pos, BGP_MSG_OPEN);
    
    return bgp_send(peer, buf, pos);
}

/* Build and send NOTIFICATION */
static int bgp_send_notification(bgp_peer_t *peer, uint8_t code, uint8_t subcode,
                                  const uint8_t *data, int data_len) {
    uint8_t buf[256];
    int pos = BGP_HEADER_SIZE;
    
    buf[pos++] = code;
    buf[pos++] = subcode;
    if (data && data_len > 0) {
        memcpy(&buf[pos], data, data_len);
        pos += data_len;
    }
    
    bgp_build_header(buf, pos, BGP_MSG_NOTIFICATION);
    int ret = bgp_send(peer, buf, pos);
    
    /* After NOTIFICATION, session is over */
    peer->state = BGP_STATE_IDLE;
    close(peer->fd);
    peer->fd = -1;
    
    return ret;
}

/* ─── Message parsers ─── */

/* Validate BGP header. Returns 0 on success, -1 on error */
static int bgp_parse_header(bgp_peer_t *peer, const uint8_t *buf, int buf_len,
                              uint16_t *msg_len, uint8_t *msg_type) {
    if (buf_len < BGP_HEADER_SIZE) return -1;
    
    const bgp_header_t *hdr = (const bgp_header_t *)buf;
    
    /* Validate marker */
    for (int i = 0; i < BGP_MARKER_SIZE; i++) {
        if (hdr->marker[i] != 0xFF) {
            bgp_send_notification(peer, BGP_ERR_HEADER, 1, NULL, 0);
            return -1;
        }
    }
    
    *msg_len  = ntohs(hdr->length);
    *msg_type = hdr->type;
    
    /* Validate length */
    if (*msg_len < BGP_HEADER_SIZE || *msg_len > 4096) {
        uint8_t err_data[2];
        err_data[0] = (*msg_len >> 8) & 0xFF;
        err_data[1] = *msg_len & 0xFF;
        bgp_send_notification(peer, BGP_ERR_HEADER, 2, err_data, 2);
        return -1;
    }
    
    /* Validate type */
    if (*msg_type < 1 || *msg_type > 5) {
        bgp_send_notification(peer, BGP_ERR_HEADER, 3, msg_type, 1);
        return -1;
    }
    
    return 0;
}

/* Parse OPEN message */
static int bgp_parse_open(bgp_peer_t *peer, const uint8_t *buf, int len) {
    if (len < BGP_HEADER_SIZE + (int)sizeof(bgp_open_t)) {
        bgp_send_notification(peer, BGP_ERR_OPEN, 0, NULL, 0);
        return -1;
    }
    
    const bgp_open_t *open = (const bgp_open_t *)(buf + BGP_HEADER_SIZE);
    
    /* Version check */
    if (open->version != 4) {
        uint8_t supported = 4;
        bgp_send_notification(peer, BGP_ERR_OPEN, 1, &supported, 1);
        return -1;
    }
    
    uint16_t peer_as = ntohs(open->my_as);
    uint16_t peer_hold = ntohs(open->hold_time);
    uint32_t peer_bgp_id = ntohl(open->bgp_id);
    
    printf("OPEN received: version=%d, AS=%u, hold=%u, BGP-ID=%08x\n",
           open->version, peer_as, peer_hold, peer_bgp_id);
    
    /* Validate peer AS (if not using 4-byte, might be AS_TRANS=23456) */
    if (peer_as != (peer->remote_asn & 0xFFFF) && peer_as != 23456) {
        bgp_send_notification(peer, BGP_ERR_OPEN, 2, NULL, 0);
        return -1;
    }
    
    /* Negotiate hold time: minimum of both */
    peer_hold = (peer_hold < BGP_DEFAULT_HOLD_TIME) ? peer_hold : BGP_DEFAULT_HOLD_TIME;
    if (peer_hold > 0 && peer_hold < 3) {
        bgp_send_notification(peer, BGP_ERR_OPEN, 6, NULL, 0);
        return -1;
    }
    peer->hold_time     = peer_hold;
    peer->keepalive_time = peer_hold / 3;
    
    /* Parse optional parameters for capabilities */
    const uint8_t *opt = open->opt_params;
    int opt_len = open->opt_len;
    int i = 0;
    while (i < opt_len) {
        uint8_t param_type = opt[i++];
        uint8_t param_len  = opt[i++];
        if (param_type == 2) { /* capabilities */
            int j = 0;
            while (j < param_len) {
                uint8_t cap_code = opt[i + j++];
                uint8_t cap_len  = opt[i + j++];
                if (cap_code == 65 && cap_len == 4) { /* 4-byte ASN */
                    uint32_t peer_asn4;
                    memcpy(&peer_asn4, &opt[i + j], 4);
                    peer_asn4 = ntohl(peer_asn4);
                    printf("  Capability: 4-byte ASN = %u\n", peer_asn4);
                    /* Override peer AS with 4-byte value */
                    /* peer->remote_asn = peer_asn4; (would validate here) */
                }
                j += cap_len;
            }
            i += param_len;
        } else {
            i += param_len; /* skip unknown param */
        }
    }
    
    return 0;
}

/* Parse a single path attribute. Returns bytes consumed or -1 on error */
static int bgp_parse_attr(bgp_peer_t *peer, const uint8_t *buf, int buf_len,
                           bgp_route_t *route) {
    if (buf_len < 3) return -1;
    
    uint8_t flags = buf[0];
    uint8_t type  = buf[1];
    int     pos   = 2;
    uint16_t attr_len;
    
    if (flags & BGP_ATTR_FLAG_EXTLEN) {
        if (buf_len < 4) return -1;
        attr_len = (buf[pos] << 8) | buf[pos+1];
        pos += 2;
    } else {
        attr_len = buf[pos++];
    }
    
    if (buf_len < pos + attr_len) return -1;
    
    const uint8_t *val = buf + pos;
    
    switch (type) {
    case BGP_ATTR_ORIGIN:
        if (attr_len >= 1) route->origin = val[0];
        break;
        
    case BGP_ATTR_AS_PATH:
        memcpy(route->as_path, val, attr_len < 255 ? attr_len : 255);
        route->as_path_len = attr_len;
        break;
        
    case BGP_ATTR_NEXT_HOP:
        if (attr_len == 4) memcpy(&route->nexthop, val, 4);
        break;
        
    case BGP_ATTR_MED:
        if (attr_len == 4) {
            route->med = (val[0] << 24) | (val[1] << 16) | (val[2] << 8) | val[3];
        }
        break;
        
    case BGP_ATTR_LOCAL_PREF:
        if (attr_len == 4) {
            route->local_pref = (val[0] << 24) | (val[1] << 16) | 
                                (val[2] << 8)  | val[3];
        }
        break;
        
    default:
        /* Unknown optional attribute: ignore if optional, error if mandatory */
        if (!(flags & BGP_ATTR_FLAG_OPTIONAL)) {
            bgp_send_notification(peer, BGP_ERR_UPDATE, 2, &type, 1);
            return -1;
        }
        break;
    }
    
    return pos + attr_len;
}

/* Parse UPDATE message */
static int bgp_parse_update(bgp_peer_t *peer, const uint8_t *buf, int len) {
    int pos = BGP_HEADER_SIZE;
    
    if (len - pos < 2) return -1;
    
    /* Withdrawn routes */
    uint16_t withdrawn_len = (buf[pos] << 8) | buf[pos+1];
    pos += 2;
    
    printf("UPDATE: withdrawn_len=%u\n", withdrawn_len);
    
    /* Parse withdrawn prefixes */
    int wd_end = pos + withdrawn_len;
    while (pos < wd_end) {
        uint8_t plen = buf[pos++];
        int nbytes = (plen + 7) / 8;  /* ceil(plen/8) */
        if (pos + nbytes > wd_end) return -1;
        
        uint32_t prefix = 0;
        memcpy(&prefix, &buf[pos], nbytes);
        prefix = ntohl(prefix);
        
        struct in_addr addr = { .s_addr = prefix };
        printf("  Withdraw: %s/%u\n", inet_ntoa(addr), plen);
        pos += nbytes;
    }
    
    if (pos + 2 > len) return -1;
    
    /* Total path attributes length */
    uint16_t attr_len = (buf[pos] << 8) | buf[pos+1];
    pos += 2;
    
    if (pos + attr_len > len) return -1;
    
    /* Parse path attributes */
    bgp_route_t route = {0};
    route.local_pref = 100; /* default */
    
    int attr_pos = pos;
    int attr_end = pos + attr_len;
    while (attr_pos < attr_end) {
        int consumed = bgp_parse_attr(peer, &buf[attr_pos],
                                       attr_end - attr_pos, &route);
        if (consumed < 0) return -1;
        attr_pos += consumed;
    }
    pos += attr_len;
    
    /* Parse NLRI (reachable prefixes) */
    while (pos < len) {
        uint8_t plen = buf[pos++];
        int nbytes = (plen + 7) / 8;
        if (pos + nbytes > len) return -1;
        
        uint32_t prefix = 0;
        memcpy(&prefix, &buf[pos], nbytes);
        pos += nbytes;
        
        /* prefix is in network byte order already */
        memcpy(&route.prefix, &prefix, 4);
        route.prefix_len = plen;
        
        char pfx_str[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &route.prefix, pfx_str, sizeof(pfx_str));
        
        struct in_addr nh = { .s_addr = route.nexthop };
        printf("  NLRI: %s/%u via %s (LP=%u, MED=%u, origin=%u)\n",
               pfx_str, plen, inet_ntoa(nh),
               route.local_pref, route.med, route.origin);
        
        /* Add to route table (simplified) */
        bgp_route_t *new_route = malloc(sizeof(bgp_route_t));
        if (new_route) {
            memcpy(new_route, &route, sizeof(bgp_route_t));
            new_route->next = peer->routes;
            peer->routes = new_route;
        }
        
        peer->updates_in++;
    }
    
    return 0;
}

/* ─── FSM transition functions ─── */

static void bgp_fsm_to_state(bgp_peer_t *peer, bgp_state_t new_state) {
    printf("FSM: %s → %s\n",
           bgp_state_str[peer->state],
           bgp_state_str[new_state]);
    peer->state = new_state;
}

/* Process a complete BGP message */
static int bgp_process_message(bgp_peer_t *peer, const uint8_t *buf, int len) {
    uint16_t msg_len;
    uint8_t  msg_type;
    
    if (bgp_parse_header(peer, buf, len, &msg_len, &msg_type) < 0) {
        return -1;
    }
    
    peer->msg_recv++;
    
    /* Reset hold timer on any message */
    if (peer->hold_time > 0) {
        peer->hold_timer = bgp_now() + peer->hold_time;
    }
    
    switch (peer->state) {
    case BGP_STATE_OPENSENT:
        if (msg_type == BGP_MSG_OPEN) {
            if (bgp_parse_open(peer, buf, len) < 0) return -1;
            bgp_send_keepalive(peer);
            bgp_fsm_to_state(peer, BGP_STATE_OPENCONFIRM);
        } else if (msg_type == BGP_MSG_NOTIFICATION) {
            bgp_fsm_to_state(peer, BGP_STATE_IDLE);
            return -1;
        } else {
            bgp_send_notification(peer, BGP_ERR_FSM, 1, NULL, 0);
            return -1;
        }
        break;
        
    case BGP_STATE_OPENCONFIRM:
        if (msg_type == BGP_MSG_KEEPALIVE) {
            bgp_fsm_to_state(peer, BGP_STATE_ESTABLISHED);
            printf("BGP session ESTABLISHED with AS%u\n", peer->remote_asn);
            peer->keepalive_timer = bgp_now() + peer->keepalive_time;
        } else if (msg_type == BGP_MSG_NOTIFICATION) {
            bgp_fsm_to_state(peer, BGP_STATE_IDLE);
            return -1;
        } else {
            bgp_send_notification(peer, BGP_ERR_FSM, 2, NULL, 0);
            return -1;
        }
        break;
        
    case BGP_STATE_ESTABLISHED:
        switch (msg_type) {
        case BGP_MSG_KEEPALIVE:
            /* Timer already reset above */
            break;
            
        case BGP_MSG_UPDATE:
            if (bgp_parse_update(peer, buf, len) < 0) return -1;
            break;
            
        case BGP_MSG_NOTIFICATION:
            printf("NOTIFICATION received — session closed\n");
            bgp_fsm_to_state(peer, BGP_STATE_IDLE);
            return -1;
            
        case BGP_MSG_ROUTE_REFRESH:
            /* Would trigger re-advertisement of Adj-RIB-Out */
            printf("ROUTE-REFRESH received\n");
            break;
            
        default:
            bgp_send_notification(peer, BGP_ERR_FSM, 3, NULL, 0);
            return -1;
        }
        break;
        
    default:
        /* Unexpected message in this state */
        bgp_send_notification(peer, BGP_ERR_FSM, 0, NULL, 0);
        return -1;
    }
    
    return 0;
}

/* ─── I/O event loop ─── */

static int bgp_run(bgp_peer_t *peer) {
    struct pollfd pfd = { .fd = peer->fd, .events = POLLIN };
    
    /* Initial connection: send OPEN */
    bgp_send_open(peer);
    bgp_fsm_to_state(peer, BGP_STATE_OPENSENT);
    peer->hold_timer = bgp_now() + BGP_DEFAULT_OPEN_HOLD;
    
    while (peer->state != BGP_STATE_IDLE) {
        time_t now = bgp_now();
        
        /* Check hold timer */
        if (peer->hold_time > 0 && peer->hold_timer > 0 && now >= peer->hold_timer) {
            printf("Hold timer expired!\n");
            bgp_send_notification(peer, BGP_ERR_HOLD_TIMER, 0, NULL, 0);
            break;
        }
        
        /* Check keepalive timer */
        if (peer->state == BGP_STATE_ESTABLISHED &&
            peer->keepalive_time > 0 &&
            now >= peer->keepalive_timer) {
            bgp_send_keepalive(peer);
            peer->keepalive_timer = now + peer->keepalive_time;
        }
        
        /* Calculate time until next timer event */
        int timeout_ms = 1000;  /* 1 second default */
        if (peer->hold_timer > 0) {
            long remaining = (peer->hold_timer - now) * 1000;
            if (remaining < timeout_ms && remaining > 0) timeout_ms = (int)remaining;
        }
        
        int ret = poll(&pfd, 1, timeout_ms);
        if (ret < 0) {
            if (errno == EINTR) continue;
            perror("poll");
            break;
        }
        
        if (ret == 0) continue; /* timeout, loop to check timers */
        
        if (pfd.revents & (POLLERR | POLLHUP)) {
            printf("TCP connection error/closed\n");
            bgp_fsm_to_state(peer, BGP_STATE_IDLE);
            break;
        }
        
        if (pfd.revents & POLLIN) {
            /* Read data */
            int n = recv(peer->fd, peer->ibuf + peer->ibuf_len,
                         sizeof(peer->ibuf) - peer->ibuf_len, 0);
            if (n <= 0) {
                if (n == 0) printf("TCP connection closed by peer\n");
                else perror("recv");
                bgp_fsm_to_state(peer, BGP_STATE_IDLE);
                break;
            }
            peer->ibuf_len += n;
            
            /* Process all complete messages in buffer */
            while (peer->ibuf_len >= BGP_HEADER_SIZE) {
                uint16_t msg_len = (peer->ibuf[16] << 8) | peer->ibuf[17];
                
                if (peer->ibuf_len < msg_len) break; /* incomplete message */
                
                /* Process the complete message */
                if (bgp_process_message(peer, peer->ibuf, msg_len) < 0) {
                    bgp_fsm_to_state(peer, BGP_STATE_IDLE);
                    goto done;
                }
                
                /* Remove processed message from buffer */
                peer->ibuf_len -= msg_len;
                if (peer->ibuf_len > 0) {
                    memmove(peer->ibuf, peer->ibuf + msg_len, peer->ibuf_len);
                }
            }
        }
    }
    
done:
    return 0;
}

/* ─── Main: connect to BGP peer ─── */

int bgp_connect_peer(const char *peer_ip, uint16_t peer_port,
                      uint32_t local_asn, uint32_t remote_asn,
                      uint32_t local_bgp_id) {
    bgp_peer_t peer = {0};
    peer.local_asn    = local_asn;
    peer.remote_asn   = remote_asn;
    peer.local_bgp_id = local_bgp_id;
    peer.state        = BGP_STATE_CONNECT;
    
    inet_aton(peer_ip, &peer.remote_addr);
    
    /* Create TCP socket */
    peer.fd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (peer.fd < 0) { perror("socket"); return -1; }
    
    /* Set TCP_NODELAY: disable Nagle for low latency */
    int one = 1;
    setsockopt(peer.fd, IPPROTO_TCP, TCP_NODELAY, &one, sizeof(one));
    
    /* Set TTL = 1 for eBGP (can be bypassed with GTSM) */
    int ttl = 1;
    setsockopt(peer.fd, IPPROTO_IP, IP_TTL, &ttl, sizeof(ttl));
    
    /* Connect to peer */
    struct sockaddr_in sa = {
        .sin_family = AF_INET,
        .sin_port   = htons(peer_port),
        .sin_addr   = peer.remote_addr
    };
    
    if (connect(peer.fd, (struct sockaddr *)&sa, sizeof(sa)) < 0) {
        perror("connect");
        close(peer.fd);
        return -1;
    }
    
    printf("TCP connected to %s:%u\n", peer_ip, peer_port);
    bgp_fsm_to_state(&peer, BGP_STATE_CONNECT);
    
    bgp_run(&peer);
    
    /* Cleanup */
    bgp_route_t *r = peer.routes;
    while (r) {
        bgp_route_t *next = r->next;
        free(r);
        r = next;
    }
    
    if (peer.fd >= 0) close(peer.fd);
    
    return 0;
}
```

### 27.2 BGP UPDATE Builder in C

```c
/* Build a BGP UPDATE advertising one prefix */
int bgp_build_update(uint8_t *buf, int buf_size,
                      uint32_t prefix, uint8_t prefix_len,
                      uint32_t nexthop, uint32_t local_pref,
                      uint32_t med, const uint32_t *as_path, int as_path_len) {
    int pos = BGP_HEADER_SIZE;
    
    /* Withdrawn routes length = 0 */
    buf[pos++] = 0;
    buf[pos++] = 0;
    
    /* Path attributes */
    int attr_len_pos = pos;
    buf[pos++] = 0;  /* attr len MSB placeholder */
    buf[pos++] = 0;  /* attr len LSB placeholder */
    int attr_start = pos;
    
    /* ORIGIN: IGP (0x40 0x01 0x01 0x00) */
    buf[pos++] = BGP_ATTR_FLAG_TRANSITIVE;          /* flags */
    buf[pos++] = BGP_ATTR_ORIGIN;                    /* type */
    buf[pos++] = 1;                                  /* length */
    buf[pos++] = 0;                                  /* IGP */
    
    /* AS_PATH: sequence of AS numbers */
    int asp_len = 2 + as_path_len * 4;  /* type + count + 4 bytes per AS */
    buf[pos++] = BGP_ATTR_FLAG_TRANSITIVE;
    buf[pos++] = BGP_ATTR_AS_PATH;
    buf[pos++] = (uint8_t)asp_len;
    buf[pos++] = 2;                    /* AS_SEQUENCE */
    buf[pos++] = (uint8_t)as_path_len; /* number of ASes */
    for (int i = 0; i < as_path_len; i++) {
        uint32_t asn = htonl(as_path[i]);
        memcpy(&buf[pos], &asn, 4);
        pos += 4;
    }
    
    /* NEXT_HOP */
    buf[pos++] = BGP_ATTR_FLAG_TRANSITIVE;
    buf[pos++] = BGP_ATTR_NEXT_HOP;
    buf[pos++] = 4;
    uint32_t nh_net = htonl(nexthop);
    memcpy(&buf[pos], &nh_net, 4);
    pos += 4;
    
    /* MULTI_EXIT_DISC (optional) */
    if (med > 0) {
        buf[pos++] = BGP_ATTR_FLAG_OPTIONAL;  /* optional, non-transitive */
        buf[pos++] = BGP_ATTR_MED;
        buf[pos++] = 4;
        uint32_t med_net = htonl(med);
        memcpy(&buf[pos], &med_net, 4);
        pos += 4;
    }
    
    /* LOCAL_PREF (iBGP only — for eBGP skip or strip) */
    buf[pos++] = BGP_ATTR_FLAG_TRANSITIVE;
    buf[pos++] = BGP_ATTR_LOCAL_PREF;
    buf[pos++] = 4;
    uint32_t lp_net = htonl(local_pref);
    memcpy(&buf[pos], &lp_net, 4);
    pos += 4;
    
    /* Update path attribute length */
    int attr_len = pos - attr_start;
    buf[attr_len_pos]   = (attr_len >> 8) & 0xFF;
    buf[attr_len_pos+1] = attr_len & 0xFF;
    
    /* NLRI: one prefix */
    buf[pos++] = prefix_len;
    int prefix_bytes = (prefix_len + 7) / 8;
    uint32_t prefix_net = htonl(prefix);
    memcpy(&buf[pos], &prefix_net, prefix_bytes);
    pos += prefix_bytes;
    
    /* Fill BGP header */
    bgp_build_header(buf, pos, BGP_MSG_UPDATE);
    
    return pos;
}
```

---

## 28. Rust Implementation — BGP Speaker

### 28.1 BGP State Machine in Rust

```rust
// bgp_speaker.rs
// A minimal BGP speaker demonstrating type-safe FSM and async I/O
// Dependencies: tokio, bytes

use std::net::{IpAddr, Ipv4Addr};
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::time::{sleep, timeout};
use bytes::{Bytes, BytesMut, BufMut, Buf};

// ─── Constants ───

const BGP_PORT: u16 = 179;
const BGP_MARKER: [u8; 16] = [0xFF; 16];
const BGP_HEADER_SIZE: usize = 19;
const BGP_MAX_MSG_SIZE: usize = 4096;

// ─── Message types ───

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum BgpMsgType {
    Open          = 1,
    Update        = 2,
    Notification  = 3,
    Keepalive     = 4,
    RouteRefresh  = 5,
}

impl TryFrom<u8> for BgpMsgType {
    type Error = BgpError;
    fn try_from(v: u8) -> Result<Self, Self::Error> {
        match v {
            1 => Ok(Self::Open),
            2 => Ok(Self::Update),
            3 => Ok(Self::Notification),
            4 => Ok(Self::Keepalive),
            5 => Ok(Self::RouteRefresh),
            _ => Err(BgpError::InvalidMessageType(v)),
        }
    }
}

// ─── FSM States ───

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum BgpState {
    Idle,
    Connect,
    Active,
    OpenSent,
    OpenConfirm,
    Established,
}

impl std::fmt::Display for BgpState {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{:?}", self)
    }
}

// ─── BGP Errors ───

#[derive(Debug)]
pub enum BgpError {
    Io(std::io::Error),
    InvalidMarker,
    InvalidMessageLength(u16),
    InvalidMessageType(u8),
    InvalidOpen(String),
    NotificationReceived { code: u8, subcode: u8 },
    HoldTimerExpired,
    SessionClosed,
    ParseError(String),
}

impl From<std::io::Error> for BgpError {
    fn from(e: std::io::Error) -> Self {
        BgpError::Io(e)
    }
}

// ─── BGP Attributes ───

#[derive(Debug, Clone, Default)]
pub struct BgpAttributes {
    pub origin: u8,           // 0=IGP, 1=EGP, 2=INCOMPLETE
    pub as_path: Vec<u32>,    // list of ASNs in AS_SEQUENCE
    pub next_hop: Ipv4Addr,
    pub med: Option<u32>,
    pub local_pref: u32,
    pub communities: Vec<u32>,
}

// ─── NLRI (prefix) ───

#[derive(Debug, Clone, PartialEq, Eq, Hash)]
pub struct Nlri {
    pub prefix: Ipv4Addr,
    pub length: u8,
}

impl Nlri {
    pub fn new(prefix: Ipv4Addr, length: u8) -> Self {
        Self { prefix, length }
    }
}

impl std::fmt::Display for Nlri {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}/{}", self.prefix, self.length)
    }
}

// ─── BGP Messages ───

#[derive(Debug)]
pub struct BgpHeader {
    pub length: u16,
    pub msg_type: BgpMsgType,
}

#[derive(Debug)]
pub struct BgpOpen {
    pub version: u8,
    pub my_asn: u32,       // 4-byte ASN
    pub hold_time: u16,
    pub bgp_id: Ipv4Addr,
    pub capabilities: Vec<BgpCapability>,
}

#[derive(Debug)]
pub enum BgpCapability {
    FourByteAsn(u32),
    RouteRefresh,
    AddPath { afi: u16, safi: u8, mode: u8 },
    Multiprotocol { afi: u16, safi: u8 },
    Unknown { code: u8, data: Vec<u8> },
}

#[derive(Debug)]
pub struct BgpUpdate {
    pub withdrawn: Vec<Nlri>,
    pub attributes: BgpAttributes,
    pub nlri: Vec<Nlri>,
}

#[derive(Debug)]
pub struct BgpNotification {
    pub error_code: u8,
    pub error_subcode: u8,
    pub data: Vec<u8>,
}

impl BgpNotification {
    pub fn hold_timer_expired() -> Self {
        Self { error_code: 4, error_subcode: 0, data: vec![] }
    }
    pub fn open_error(subcode: u8) -> Self {
        Self { error_code: 2, error_subcode: subcode, data: vec![] }
    }
    pub fn cease_admin_shutdown(msg: &str) -> Self {
        Self {
            error_code: 6,
            error_subcode: 2,
            data: msg.as_bytes().to_vec(),
        }
    }
}

// ─── Message encoder ───

pub struct BgpEncoder;

impl BgpEncoder {
    fn header(msg_type: BgpMsgType, body_len: usize) -> BytesMut {
        let total_len = BGP_HEADER_SIZE + body_len;
        let mut buf = BytesMut::with_capacity(total_len);
        buf.put_slice(&BGP_MARKER);
        buf.put_u16(total_len as u16);
        buf.put_u8(msg_type as u8);
        buf
    }
    
    pub fn keepalive() -> Bytes {
        Self::header(BgpMsgType::Keepalive, 0).freeze()
    }
    
    pub fn notification(notif: &BgpNotification) -> Bytes {
        let mut buf = Self::header(BgpMsgType::Notification, 2 + notif.data.len());
        buf.put_u8(notif.error_code);
        buf.put_u8(notif.error_subcode);
        buf.put_slice(&notif.data);
        buf.freeze()
    }
    
    pub fn open(local_asn: u32, hold_time: u16, bgp_id: Ipv4Addr) -> Bytes {
        // Build capabilities
        let mut caps = BytesMut::new();
        
        // 4-byte ASN capability
        caps.put_u8(65);    // code
        caps.put_u8(4);     // length
        caps.put_u32(local_asn);
        
        // Route Refresh capability
        caps.put_u8(2);     // code
        caps.put_u8(0);     // length
        
        // Multiprotocol IPv4 Unicast
        caps.put_u8(1);     // code
        caps.put_u8(4);     // length
        caps.put_u16(1);    // AFI = IPv4
        caps.put_u8(0);     // reserved
        caps.put_u8(1);     // SAFI = unicast
        
        // Wrap in optional parameter type 2 (capabilities)
        let mut opt_params = BytesMut::new();
        opt_params.put_u8(2);               // param type = capabilities
        opt_params.put_u8(caps.len() as u8); // param len
        opt_params.put_slice(&caps);
        
        let body_len = 1 + 2 + 2 + 4 + 1 + opt_params.len();
        let mut buf = Self::header(BgpMsgType::Open, body_len);
        buf.put_u8(4);          // BGP version 4
        // If ASN > 65535, send AS_TRANS = 23456
        let as16 = if local_asn > 65535 { 23456u16 } else { local_asn as u16 };
        buf.put_u16(as16);
        buf.put_u16(hold_time);
        buf.put_slice(&bgp_id.octets());
        buf.put_u8(opt_params.len() as u8);
        buf.put_slice(&opt_params);
        buf.freeze()
    }
    
    pub fn update(withdrawn: &[Nlri], attrs: &BgpAttributes, nlri: &[Nlri]) -> Bytes {
        let mut body = BytesMut::new();
        
        // Withdrawn routes
        let mut wd = BytesMut::new();
        for prefix in withdrawn {
            let bytes_needed = ((prefix.length + 7) / 8) as usize;
            wd.put_u8(prefix.length);
            let octets = prefix.prefix.octets();
            wd.put_slice(&octets[..bytes_needed]);
        }
        body.put_u16(wd.len() as u16);
        body.put_slice(&wd);
        
        // Path attributes
        let mut pa = BytesMut::new();
        
        // ORIGIN
        pa.put_u8(0x40);  // transitive
        pa.put_u8(1);
        pa.put_u8(1);
        pa.put_u8(attrs.origin);
        
        // AS_PATH
        let asp_data_len = 2 + attrs.as_path.len() * 4;
        pa.put_u8(0x40);  // transitive
        pa.put_u8(2);
        pa.put_u8(asp_data_len as u8);
        pa.put_u8(2);  // AS_SEQUENCE
        pa.put_u8(attrs.as_path.len() as u8);
        for &asn in &attrs.as_path {
            pa.put_u32(asn);
        }
        
        // NEXT_HOP
        pa.put_u8(0x40);
        pa.put_u8(3);
        pa.put_u8(4);
        pa.put_slice(&attrs.next_hop.octets());
        
        // MED (optional)
        if let Some(med) = attrs.med {
            pa.put_u8(0x80);  // optional, non-transitive
            pa.put_u8(4);
            pa.put_u8(4);
            pa.put_u32(med);
        }
        
        // LOCAL_PREF
        pa.put_u8(0x40);
        pa.put_u8(5);
        pa.put_u8(4);
        pa.put_u32(attrs.local_pref);
        
        // Communities
        if !attrs.communities.is_empty() {
            pa.put_u8(0xC0);  // optional, transitive
            pa.put_u8(8);
            pa.put_u8((attrs.communities.len() * 4) as u8);
            for &c in &attrs.communities {
                pa.put_u32(c);
            }
        }
        
        body.put_u16(pa.len() as u16);
        body.put_slice(&pa);
        
        // NLRI
        for prefix in nlri {
            let bytes_needed = ((prefix.length + 7) / 8) as usize;
            body.put_u8(prefix.length);
            let octets = prefix.prefix.octets();
            body.put_slice(&octets[..bytes_needed]);
        }
        
        Self::header(BgpMsgType::Update, body.len())
            .chain(body)
            .copy_to_bytes(BGP_HEADER_SIZE + body.len())
    }
}

// ─── Message decoder ───

pub struct BgpDecoder;

impl BgpDecoder {
    pub fn decode_header(buf: &[u8]) -> Result<BgpHeader, BgpError> {
        if buf.len() < BGP_HEADER_SIZE {
            return Err(BgpError::ParseError("Header too short".into()));
        }
        
        // Validate marker
        if &buf[..16] != &BGP_MARKER {
            return Err(BgpError::InvalidMarker);
        }
        
        let length = u16::from_be_bytes([buf[16], buf[17]]);
        let msg_type_raw = buf[18];
        
        if (length as usize) < BGP_HEADER_SIZE || (length as usize) > BGP_MAX_MSG_SIZE {
            return Err(BgpError::InvalidMessageLength(length));
        }
        
        Ok(BgpHeader {
            length,
            msg_type: BgpMsgType::try_from(msg_type_raw)?,
        })
    }
    
    pub fn decode_open(body: &[u8]) -> Result<BgpOpen, BgpError> {
        if body.len() < 10 {
            return Err(BgpError::ParseError("OPEN too short".into()));
        }
        
        let version   = body[0];
        let as16      = u16::from_be_bytes([body[1], body[2]]);
        let hold_time = u16::from_be_bytes([body[3], body[4]]);
        let bgp_id    = Ipv4Addr::new(body[5], body[6], body[7], body[8]);
        let opt_len   = body[9] as usize;
        
        if version != 4 {
            return Err(BgpError::InvalidOpen(format!("Version {} != 4", version)));
        }
        
        let mut my_asn = as16 as u32;
        let mut capabilities = Vec::new();
        
        // Parse optional parameters
        let mut pos = 10;
        while pos < 10 + opt_len {
            if pos + 2 > body.len() { break; }
            let param_type = body[pos];
            let param_len  = body[pos + 1] as usize;
            pos += 2;
            
            if param_type == 2 {  // Capabilities
                let mut cap_pos = pos;
                let cap_end = pos + param_len;
                while cap_pos + 2 <= cap_end {
                    let cap_code = body[cap_pos];
                    let cap_len  = body[cap_pos + 1] as usize;
                    cap_pos += 2;
                    
                    let cap_data = &body[cap_pos..cap_pos + cap_len.min(body.len() - cap_pos)];
                    
                    let cap = match cap_code {
                        65 if cap_len == 4 => {
                            let asn = u32::from_be_bytes([
                                cap_data[0], cap_data[1], cap_data[2], cap_data[3]
                            ]);
                            my_asn = asn;  // Override with 4-byte ASN
                            BgpCapability::FourByteAsn(asn)
                        }
                        2 => BgpCapability::RouteRefresh,
                        1 if cap_len >= 4 => BgpCapability::Multiprotocol {
                            afi: u16::from_be_bytes([cap_data[0], cap_data[1]]),
                            safi: cap_data[3],
                        },
                        _ => BgpCapability::Unknown {
                            code: cap_code,
                            data: cap_data.to_vec(),
                        },
                    };
                    capabilities.push(cap);
                    cap_pos += cap_len;
                }
            }
            pos += param_len;
        }
        
        Ok(BgpOpen { version, my_asn, hold_time, bgp_id, capabilities })
    }
    
    pub fn decode_update(body: &[u8]) -> Result<BgpUpdate, BgpError> {
        if body.len() < 4 { 
            return Err(BgpError::ParseError("UPDATE too short".into()));
        }
        
        let mut pos = 0;
        
        // Withdrawn routes
        let wd_len = u16::from_be_bytes([body[pos], body[pos+1]]) as usize;
        pos += 2;
        let mut withdrawn = Vec::new();
        
        let wd_end = pos + wd_len;
        while pos < wd_end {
            let plen = body[pos] as usize;
            pos += 1;
            let bytes_needed = (plen + 7) / 8;
            
            let mut octets = [0u8; 4];
            octets[..bytes_needed.min(4)].copy_from_slice(
                &body[pos..pos + bytes_needed.min(4)]);
            withdrawn.push(Nlri::new(Ipv4Addr::from(octets), plen as u8));
            pos += bytes_needed;
        }
        
        // Path attributes
        if pos + 2 > body.len() {
            return Err(BgpError::ParseError("Missing attr length".into()));
        }
        let attr_len = u16::from_be_bytes([body[pos], body[pos+1]]) as usize;
        pos += 2;
        
        let mut attributes = BgpAttributes::default();
        attributes.local_pref = 100;
        
        let attr_end = pos + attr_len;
        while pos < attr_end {
            if pos + 3 > body.len() { break; }
            let flags   = body[pos];
            let attr_t  = body[pos + 1];
            let ext_len = (flags & 0x10) != 0;
            pos += 2;
            
            let a_len = if ext_len {
                let l = u16::from_be_bytes([body[pos], body[pos+1]]) as usize;
                pos += 2; l
            } else {
                let l = body[pos] as usize;
                pos += 1; l
            };
            
            let val = &body[pos..pos + a_len.min(body.len() - pos)];
            
            match attr_t {
                1 => attributes.origin = val.first().copied().unwrap_or(2),
                2 => {
                    // AS_PATH: parse AS_SEQUENCE segments
                    let mut ap = 0;
                    while ap + 2 <= val.len() {
                        let seg_type = val[ap];
                        let seg_count = val[ap + 1] as usize;
                        ap += 2;
                        if seg_type == 2 {  // AS_SEQUENCE
                            for _ in 0..seg_count {
                                if ap + 4 <= val.len() {
                                    let asn = u32::from_be_bytes([
                                        val[ap], val[ap+1], val[ap+2], val[ap+3]
                                    ]);
                                    attributes.as_path.push(asn);
                                    ap += 4;
                                }
                            }
                        } else {
                            ap += seg_count * 4;
                        }
                    }
                }
                3 if a_len == 4 => {
                    attributes.next_hop = Ipv4Addr::new(val[0], val[1], val[2], val[3]);
                }
                4 if a_len == 4 => {
                    attributes.med = Some(u32::from_be_bytes([val[0], val[1], val[2], val[3]]));
                }
                5 if a_len == 4 => {
                    attributes.local_pref = u32::from_be_bytes([val[0], val[1], val[2], val[3]]);
                }
                8 => {
                    let mut ci = 0;
                    while ci + 4 <= val.len() {
                        attributes.communities.push(
                            u32::from_be_bytes([val[ci], val[ci+1], val[ci+2], val[ci+3]]));
                        ci += 4;
                    }
                }
                _ => {}  // Unknown/unhandled attribute
            }
            pos += a_len;
        }
        
        // NLRI
        let mut nlri = Vec::new();
        while pos < body.len() {
            let plen = body[pos] as usize;
            pos += 1;
            let bytes_needed = (plen + 7) / 8;
            
            let mut octets = [0u8; 4];
            octets[..bytes_needed.min(4)].copy_from_slice(
                &body[pos..pos + bytes_needed.min(4)]);
            nlri.push(Nlri::new(Ipv4Addr::from(octets), plen as u8));
            pos += bytes_needed;
        }
        
        Ok(BgpUpdate { withdrawn, attributes, nlri })
    }
}

