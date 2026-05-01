# BGP: Border Gateway Protocol — Complete In-Depth Guide

> **Audience**: Systems engineers, network architects, protocol implementors.
> **Scope**: RFC 4271 (BGP-4) core, extensions, security, and production implementation in C and Rust.

---

## Table of Contents

1. [History and Motivation](#1-history-and-motivation)
2. [Internet Architecture Context](#2-internet-architecture-context)
3. [BGP Fundamentals](#3-bgp-fundamentals)
4. [TCP Session Layer](#4-tcp-session-layer)
5. [BGP Message Formats — Wire Level](#5-bgp-message-formats--wire-level)
6. [BGP Finite State Machine](#6-bgp-finite-state-machine)
7. [Path Attributes — Complete Reference](#7-path-attributes--complete-reference)
8. [BGP Decision Process](#8-bgp-decision-process)
9. [Communities and Extended Communities](#9-communities-and-extended-communities)
10. [Route Reflection and Confederations](#10-route-reflection-and-confederations)
11. [BGP Capabilities Negotiation](#11-bgp-capabilities-negotiation)
12. [MP-BGP: Multiprotocol Extensions](#12-mp-bgp-multiprotocol-extensions)
13. [BGP Security](#13-bgp-security)
14. [BGP in Data Center (DC BGP)](#14-bgp-in-data-center-dc-bgp)
15. [BGP Convergence and Tuning](#15-bgp-convergence-and-tuning)
16. [Troubleshooting BGP](#16-troubleshooting-bgp)
17. [C Implementation](#17-c-implementation)
18. [Rust Implementation](#18-rust-implementation)
19. [Testing BGP Implementations](#19-testing-bgp-implementations)
20. [Production Security Checklist](#20-production-security-checklist)
21. [Further Reading](#21-further-reading)

---

## 1. History and Motivation

### 1.1 The Problem BGP Solves

The Internet is not a single network. It is a collection of independently operated networks called **Autonomous Systems (AS)**. Each AS is owned by an organization (ISP, enterprise, cloud provider, university) that makes its own routing policy decisions.

Before BGP, EGP (Exterior Gateway Protocol, RFC 888, 1984) was used. EGP was fundamentally a reachability protocol — it could announce which networks an AS could reach, but it had no loop prevention mechanism and carried no path information. It assumed a tree-shaped internet (the NSFNET backbone hierarchy), which became obsolete as the internet grew into a mesh.

**Key problems EGP could not solve:**
- No loop detection at internet scale
- No policy expression (cannot prefer one path over another)
- Cannot represent the path traversed (needed to detect and avoid loops)
- No incremental updates (full table exchange only)

### 1.2 BGP Version History

| Version | RFC       | Year | Notes                                              |
|---------|-----------|------|----------------------------------------------------|
| BGP-1   | RFC 1105  | 1989 | Kirk Lougheed, Yakov Rekhter — "Two Napkins" protocol |
| BGP-2   | RFC 1163  | 1990 | Minor refinements                                  |
| BGP-3   | RFC 1267  | 1991 | Loop detection improvements                        |
| BGP-4   | RFC 1771  | 1995 | CIDR support, path aggregation                     |
| BGP-4   | RFC 4271  | 2006 | Current authoritative RFC (obsoletes 1771)         |

**Key BGP-4 innovations:**
- **CIDR** (Classless Inter-Domain Routing): routes carry explicit prefix lengths, not class-based assumptions
- **Path Vector**: each route advertisement carries the full AS_PATH, enabling loop detection
- **Aggregation**: multiple prefixes can be summarized into one announcement
- **Policy-rich attributes**: communities, local preference, MED for flexible policy

### 1.3 BGP as "the Protocol that Runs the Internet"

As of 2024:
- ~1,000,000+ IPv4 prefixes in the global routing table (the "DFZ" — Default-Free Zone)
- ~200,000+ IPv6 prefixes
- ~80,000+ active ASNs
- Every packet you send across the internet is forwarded based on BGP-computed paths

BGP is not fast. It is not designed to be. It is designed to be **policy-correct** and **loop-free at internet scale**. Interior routing protocols (OSPF, IS-IS) handle speed inside an AS; BGP handles correctness between ASes.

---

## 2. Internet Architecture Context

### 2.1 Autonomous Systems

An Autonomous System is:
1. A set of IP prefixes
2. Under a single administrative domain
3. With a single, clearly defined routing policy to the outside world
4. Identified by a 16-bit (legacy) or 32-bit ASN

**ASN Allocation:**
```
Private 16-bit ASNs:  64512 – 65534
Private 32-bit ASNs:  4200000000 – 4294967294
Reserved:             65535, 4294967295
IANA-assigned public: everything else
```

**Notation**: 32-bit ASNs are written in "asdot" notation as `X.Y` where the 32-bit value is `X * 65536 + Y`, or in "asdot+" plain decimal. Example: AS 131072 = AS 2.0.

### 2.2 AS Relationships

BGP sessions encode business relationships. There are exactly three canonical types:

```
                    TRANSIT PROVIDER
                    (pays them)
                         |
                    [Provider AS]
                    /           \
              iBGP               iBGP
              /                     \
        [Router A] ---eBGP---  [Router B]
              \                     /
               +---[Customer AS]---+
                         |
                    CUSTOMER
                    (pays you)
              
        [Peer AS] ---eBGP--- [Your AS]
        (settlement-free, equals)
```

**Provider–Customer**: Customer pays provider for transit. Provider announces full table (or default) to customer. Provider announces customer's prefixes to everyone.

**Peer–Peer (Settlement-free)**: Two networks exchange traffic between their customers at no cost. Only announce customer routes (not provider routes) to peers.

**Sibling/Backup**: Internal redundancy between the same organization's ASNs.

### 2.3 Route Propagation Rules (Gao-Rexford Model)

The commercially-driven BGP routing converges because of the **valley-free routing** principle:
- A route learned from a customer can be announced to: providers, peers, other customers.
- A route learned from a peer can be announced to: customers only.
- A route learned from a provider can be announced to: customers only.

This ensures that traffic flows "up" toward providers, across peers, then "down" to customers — never through a peer's provider (which would provide free transit to the peer).

### 2.4 Internet Exchange Points (IXPs)

IXPs are physical facilities where networks interconnect. Examples: DE-CIX (Frankfurt), AMS-IX (Amsterdam), LINX (London), Equinix IX.

At an IXP, networks connect to a shared Layer 2 fabric (a large Ethernet switch) and peer with each other directly via BGP, avoiding transit costs. Route Servers at IXPs run BGP with all members and redistribute routes, allowing O(1) bilateral peering without O(N²) sessions.

---

## 3. BGP Fundamentals

### 3.1 eBGP vs iBGP

| Property            | eBGP                              | iBGP                               |
|---------------------|-----------------------------------|------------------------------------|
| Session type        | Between different ASes            | Within same AS                     |
| TTL default         | 1 (single hop)                    | 255 (any hop count)                |
| AS_PATH behavior    | Prepend own ASN on send           | Pass through unchanged             |
| NEXT_HOP behavior   | Set to self                       | Pass through unchanged             |
| LOCAL_PREF          | Not sent                          | Sent and respected                 |
| MED                 | Sent to neighbors                 | Passed through                     |
| Loop prevention     | AS_PATH (reject if own ASN seen)  | Split horizon (no re-advertisement)|
| Full mesh required? | No                                | Yes (or use RR/Confederation)      |
| Administrative dist | 20 (Cisco default)                | 200 (Cisco default)                |

**iBGP split horizon**: A route learned from one iBGP peer MUST NOT be re-advertised to another iBGP peer. This prevents loops but requires full mesh or route reflection.

### 3.2 BGP Speaker Requirements

A BGP speaker (router) must:
1. Maintain a TCP connection (port 179) to each peer
2. Maintain per-peer state: Adj-RIB-In, Adj-RIB-Out
3. Maintain a local best-path database: Loc-RIB
4. Apply policy (import filters on Adj-RIB-In, export filters on Adj-RIB-Out)
5. Run the Decision Process to select best paths
6. Send incremental updates (not full dumps) after initial table exchange

### 3.3 RIB Architecture

```
Peer 1 ──OPEN──> [Adj-RIB-In 1] ──import policy──> \
Peer 2 ──OPEN──> [Adj-RIB-In 2] ──import policy──> [Loc-RIB] ──export policy──> [Adj-RIB-Out] ──UPDATE──> Peers
Peer N ──OPEN──> [Adj-RIB-In N] ──import policy──> /
                                                      ^
                                                      |
                                                 Decision Process
                                                 (Best Path Selection)
```

- **Adj-RIB-In**: All routes received from a peer (before policy)
- **Loc-RIB**: Best paths after Decision Process and import policy
- **Adj-RIB-Out**: Routes prepared to send to each peer (after export policy)

---

## 4. TCP Session Layer

BGP runs over TCP port 179. This is non-trivial in its implications:

### 4.1 Why TCP?

BGP chose TCP as transport to inherit:
- **Reliability**: No packet loss handling needed in BGP itself
- **Flow control**: Prevents overwhelming a peer with updates
- **Ordering**: Updates arrive in order (critical for consistency)
- **Authentication**: TCP MD5 (RFC 2385) or TCP-AO (RFC 5925) for session security

### 4.2 Active vs Passive

Both peers may initiate the TCP connection. The one that initiates is "Active", the one that accepts is "Passive". When both initiate simultaneously, BGP handles collision detection in the OPEN exchange (higher BGP ID wins).

```
Active peer:   SYN ──────────────────────────> Passive peer
               SYN-ACK <──────────────────────
               ACK ───────────────────────────>
               OPEN ──────────────────────────>
                      <─────────────────────── OPEN
               KEEPALIVE ─────────────────────>
                      <─────────────────────── KEEPALIVE
               [ESTABLISHED — UPDATE exchange begins]
```

### 4.3 TCP MD5 Authentication (RFC 2385)

A shared secret is configured on both peers. Every TCP segment's header is signed with HMAC-MD5. The signature is placed in a TCP option (option kind 19). This prevents session hijacking but does NOT encrypt the session — it only authenticates TCP segments.

```c
// TCP option structure for MD5:
// Kind=19, Len=18, MD5[16 bytes]
struct tcp_md5_option {
    uint8_t  kind;      // 19
    uint8_t  len;       // 18
    uint8_t  digest[16]; // HMAC-MD5 of: TCP pseudo-header + TCP header + data
};
```

### 4.4 BGP over TCP Keepalive Timing

BGP has its own KEEPALIVE messages independent of TCP keepalives. The BGP Hold Timer is negotiated in the OPEN message. If no KEEPALIVE or UPDATE is received within the Hold Time, the session is torn down.

Default: Hold Time = 90s, Keepalive interval = 30s (1/3 of hold time).

---

## 5. BGP Message Formats — Wire Level

All BGP messages share a common 19-byte header followed by type-specific data.

### 5.1 BGP Common Header

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                                                               |
|                   Marker (16 bytes, all 0xFF)                 |
|                                                               |
|                                                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|          Length               |    Type       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Marker:  16 bytes of 0xFF. Was used for authentication in BGP-1/2/3.
         In BGP-4 it is always 0xFF (compatibility). MUST be verified.
Length:  Total message length including header. Min=19, Max=4096.
Type:    1=OPEN, 2=UPDATE, 3=NOTIFICATION, 4=KEEPALIVE, 5=ROUTE-REFRESH
```

**Byte-by-byte breakdown:**
```
Offset  Size  Field
------  ----  -----
0       16    Marker (0xFF * 16)
16      2     Length (big-endian uint16)
18      1     Type
19+     var   Type-specific data
```

### 5.2 OPEN Message (Type 1)

Sent immediately after TCP connection is established. Negotiates session parameters.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Version (1)  |         My Autonomous System (2)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Hold Time (2)         |   BGP Identifier (4 bytes)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+                               |
|                               +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                               |  Opt Parm Len |               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+               |
|                  Optional Parameters (variable)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Version:         Must be 4
My AS:           Sender's 2-byte ASN. For 4-byte ASN: use AS 23456 here,
                 carry real ASN in Capabilities optional parameter.
Hold Time:       Proposed hold time in seconds. Final = MIN(local, remote).
                 0 means no hold timer (not recommended).
BGP Identifier:  Chosen router ID. Must be unique within AS. Typically
                 the highest loopback IP, expressed as 4-byte value.
Opt Parm Len:    Length of optional parameters field.
```

**Optional Parameters in OPEN:**

Each optional parameter has the TLV structure:
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Parm Type(1) | Parm Length(1)|        Parm Value (var)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Parm Type 2 = Capabilities
```

**Capabilities Optional Parameter:**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Cap Code (1) |  Cap Len (1) |       Capability Value (var)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Common capability codes:
```
Code  Name
----  ----
1     Multiprotocol Extensions (RFC 4760) — AFI/SAFI pair
2     Route Refresh (RFC 2918)
5     Extended Next Hop Encoding (RFC 8950)
6     Extended Message (RFC 8654) — allows messages up to 65535 bytes
64    Graceful Restart (RFC 4724)
65    4-octet AS Number (RFC 6793)
69    ADD-PATH (RFC 7911)
70    Enhanced Route Refresh (RFC 7313)
71    Long-Lived Graceful Restart (RFC 9494)
```

**Multiprotocol Capability (Code 1):**
```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            AFI (2)            |  Reserved (1) |    SAFI (1)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

AFI:   Address Family Identifier
       1  = IPv4
       2  = IPv6
       25 = L2VPN
SAFI:  Subsequent Address Family Identifier
       1  = Unicast
       2  = Multicast
       4  = MPLS Labels (RFC 3107)
       65 = VPLS
       70 = EVPN (RFC 7432)
       128= MPLS-labeled VPN unicast (RFC 4364)
```

**4-Byte AS Capability (Code 65):**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       AS Number (4 bytes)                     |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 5.3 UPDATE Message (Type 2)

The core of BGP. Carries route withdrawals and advertisements.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Withdrawn Routes Length (2)  |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Withdrawn Routes (variable) |
|                               |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Total Path Attr Length (2)   |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+  Path Attributes (variable)  |
|                               |                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  NLRI (Network Layer Reachability Info)       |
|                          (variable)                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Withdrawn Routes: Prefixes to un-advertise (IPv4 unicast only here)
                  Uses NLRI encoding (see below).
                  Length=0 means no withdrawals.
Path Attributes:  Attributes describing the route (see section 7).
                  Length=0 means no new routes (withdrawal-only UPDATE).
NLRI:             Prefixes being advertised. Remaining bytes in message
                  after Path Attributes. Length derived from message Length.
```

**NLRI Encoding (IPv4 prefix):**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Prefix Length (1 byte)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Prefix (ceiling(len/8) bytes)|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Example: 192.168.1.0/24
  Length byte: 0x18 (24)
  Prefix bytes: 0xC0 0xA8 0x01 (3 bytes, trailing zeros omitted)

Example: 10.0.0.0/8
  Length byte: 0x08 (8)
  Prefix bytes: 0x0A (1 byte)

Example: 0.0.0.0/0 (default route)
  Length byte: 0x00
  Prefix bytes: (empty — zero bytes)
```

**UPDATE can carry multiple NLRI in one message** but only one set of path attributes. All NLRI in a single UPDATE share the same path attributes. This is why UPDATE messages may be bundled for efficiency.

### 5.4 Path Attribute Encoding

Each path attribute uses a variable-length TLV:

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Attr Flags  (1 byte)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Attr Type Code (1 byte)    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Attr Length                |
|    (1 byte if !Extended,      |
|     2 bytes if Extended flag) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|    Attr Value (variable)      |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Attribute Flags byte:**
```
Bit 7 (MSB): Optional    — 0=Well-known, 1=Optional
Bit 6:       Transitive  — 0=Non-transitive, 1=Transitive
Bit 5:       Partial     — 0=Complete, 1=Partial (only for Optional Transitive)
Bit 4:       Ext Length  — 0=1-byte length, 1=2-byte length
Bits 3-0:    Unused (must be 0)

Categorization:
  Well-known Mandatory:     Optional=0, Transitive=1, must be in every UPDATE
  Well-known Discretionary: Optional=0, Transitive=1, may be omitted
  Optional Transitive:      Optional=1, Transitive=1, forward even if unknown
  Optional Non-transitive:  Optional=1, Transitive=0, discard if unknown
```

### 5.5 NOTIFICATION Message (Type 3)

Sent when an error is detected. After sending NOTIFICATION, the TCP session is closed immediately.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Error Code(1)|  Error Subcode(1)|   Data (variable)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Error Codes and Subcodes:**

```
Code 1: Message Header Error
  Sub 1: Connection Not Synchronized (marker not all 0xFF)
  Sub 2: Bad Message Length (< 19 or > 4096)
  Sub 3: Bad Message Type (unknown type code)

Code 2: OPEN Message Error
  Sub 1: Unsupported Version Number
  Sub 2: Bad Peer AS
  Sub 3: Bad BGP Identifier
  Sub 4: Unsupported Optional Parameter
  Sub 6: Unacceptable Hold Time

Code 3: UPDATE Message Error
  Sub 1: Malformed Attribute List
  Sub 2: Unrecognized Well-known Attribute
  Sub 3: Missing Well-known Attribute
  Sub 4: Attribute Flags Error
  Sub 5: Attribute Length Error
  Sub 6: Invalid ORIGIN Attribute
  Sub 8: Invalid NEXT_HOP Attribute
  Sub 9: Optional Attribute Error
  Sub 10: Invalid Network Field
  Sub 11: Malformed AS_PATH

Code 4: Hold Timer Expired
  Sub 0: (no subcode)

Code 5: Finite State Machine Error
  Sub 0: Unspecified Error
  Sub 1: Receive Unexpected Message in OpenSent State
  Sub 2: Receive Unexpected Message in OpenConfirm State
  Sub 3: Receive Unexpected Message in Established State

Code 6: Cease (voluntary session shutdown)
  Sub 1: Maximum Number of Prefixes Reached
  Sub 2: Administrative Shutdown
  Sub 3: Peer De-configured
  Sub 4: Administrative Reset
  Sub 5: Connection Rejected
  Sub 6: Other Configuration Change
  Sub 7: Connection Collision Resolution
  Sub 8: Out of Resources
```

**CEASE Notification with Shutdown Communication (RFC 9003):**
When using Cease/Administrative Shutdown (6/2) or Administrative Reset (6/4), operators can include a human-readable UTF-8 message:
```
Data format: | Length (1 byte) | UTF-8 string (0-255 bytes) |
```

### 5.6 KEEPALIVE Message (Type 4)

Exactly 19 bytes — just the common header. No body.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Marker (all 0xFF, 16 bytes)                 |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     Length = 19 (2 bytes)     | Type = 4 (1 byte) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-------------------+
```

Sent every Keepalive Interval seconds to prevent Hold Timer expiry.

### 5.7 ROUTE-REFRESH Message (Type 5, RFC 2918)

Requests the peer to re-send their full routing table for a specific AFI/SAFI. Used after policy changes without resetting the session.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|            AFI (2 bytes)      |  Reserved (1) |    SAFI (1)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

---

## 6. BGP Finite State Machine

BGP is defined by a strict Finite State Machine (FSM). Each peer relationship is an independent FSM instance.

### 6.1 States

```
IDLE ──ConnectRetry starts──> CONNECT
       ^                          |
       |                     TCP Success
       |                          |
       +──TCP Fail──── ACTIVE <───+
                          |
                     TCP established
                          |
                       OPENSENT ──OPEN received──> OPENCONFIRM
                                                        |
                                                KEEPALIVE received
                                                        |
                                                   ESTABLISHED
```

**IDLE**
- Initial state. No resources allocated.
- Entry actions: Initialize all resources, reset ConnectRetry timer, reject all incoming TCP connections (implementation choice).
- Trigger to exit: ManualStart event or AutomaticStart event → CONNECT.

**CONNECT**
- Initiating TCP connection.
- ConnectRetry timer is running.
- If TCP succeeds → send OPEN → OPENSENT.
- If TCP fails → reset ConnectRetry timer → ACTIVE.
- If ConnectRetry expires → try again, stay in CONNECT.

**ACTIVE**
- Trying to acquire TCP connection. Previous attempt failed.
- ConnectRetry timer is running.
- Listening for incoming TCP connection (passive mode).
- If incoming TCP succeeds → send OPEN → OPENSENT.
- If ConnectRetry expires → CONNECT.
- This state represents "trying harder" — repeated reconnection attempts.

**OPENSENT**
- TCP connection established. OPEN sent. Waiting for peer's OPEN.
- If valid OPEN received → send KEEPALIVE → OPENCONFIRM.
- If invalid OPEN → send NOTIFICATION → IDLE.
- If TCP connection dropped → ACTIVE.
- If Hold Timer expires (initial value = 4 minutes) → NOTIFICATION → IDLE.

**OPENCONFIRM**
- OPEN sent and received. KEEPALIVE sent. Waiting for peer's KEEPALIVE.
- Hold Timer running (negotiated value).
- If KEEPALIVE received → ESTABLISHED.
- If NOTIFICATION received → IDLE.
- Send KEEPALIVE periodically if KeepaliveTimer fires.

**ESTABLISHED**
- Session is fully operational.
- Process UPDATE, KEEPALIVE, NOTIFICATION messages.
- Send KEEPALIVE messages.
- Send UPDATE messages as routes change.
- If Hold Timer expires → send NOTIFICATION (Hold Timer Expired) → IDLE.
- If NOTIFICATION received → IDLE.
- If error in received UPDATE → send NOTIFICATION → IDLE.

### 6.2 Events

The FSM responds to events:
```
Manual Events:
  ManualStart           — operator initiates session
  ManualStop            — operator tears down session
  ManualStart_with_PassiveTcpEstablishment

Automatic Events:
  AutomaticStart
  AutomaticStop

Timer Events:
  ConnectRetryTimer_Expires
  HoldTimer_Expires
  KeepaliveTimer_Expires

TCP Events:
  Tcp_CR_Acked          — TCP connection request acknowledged (active)
  TcpConnection_Valid   — incoming TCP (passive)
  Tcp_CR_Invalid        — TCP connection invalid/rejected
  TcpConnectionConfirmed — connection confirmed
  TcpConnectionFails    — connection failed/dropped

BGP Message Events:
  BGPOpen               — valid OPEN received
  BGPOpen_with_DelayOpenTimer_running
  BGPHeaderErr          — header error
  BGPOpenMsgErr         — OPEN error
  OpenCollisionDump     — collision resolution: dump this connection
  NotifMsgVerErr        — NOTIFICATION with version error
  NotifMsg              — NOTIFICATION received
  KeepAliveMsg          — KEEPALIVE received
  UpdateMsg             — UPDATE received
  UpdateMsgErr          — UPDATE error
```

### 6.3 ConnectRetry Timer and Exponential Backoff

The ConnectRetry timer should implement exponential backoff to avoid storms during network instability. RFC 4271 leaves the algorithm implementation-defined but requires:

```
Initial:   ConnectRetryTimer = ConnectRetryTime (default: 120 seconds)
On retry:  Jitter with ±25% randomization to avoid synchronization
```

In production, operators commonly set:
- `ConnectRetryTime`: 30–120 seconds
- With exponential backoff: 30s, 60s, 120s, 240s... capped at some maximum

### 6.4 Open Collision Detection

When both peers initiate TCP simultaneously, two connections may be established. BGP defines collision resolution:

1. Both peers send OPEN on their connection.
2. Each peer determines which connection to keep.
3. The connection initiated by the peer with the **larger BGP Identifier** (as a 4-byte unsigned integer) is kept.
4. The other connection is closed with NOTIFICATION (Cease, Connection Collision Resolution).

If BGP IDs are equal (should not happen in valid configurations), use the connection with the larger ASN.

---

## 7. Path Attributes — Complete Reference

### 7.1 ORIGIN (Type 1)

**Flags**: Well-known Mandatory (0x40, flags byte = 0x40)
**Length**: 1 byte

```
+------------------+
|  Value (1 byte)  |
+------------------+
  0 = IGP     (route originated from within the AS, e.g., redistributed from OSPF)
  1 = EGP     (route learned from EGP — legacy, rare)
  2 = INCOMPLETE (route of unknown origin, typically from static/connected)
```

Used in best path selection (IGP preferred over EGP over INCOMPLETE).

### 7.2 AS_PATH (Type 2)

**Flags**: Well-known Mandatory (0x40)
**Length**: Variable

The central loop-prevention mechanism. A sequence of AS numbers representing the path the route has traversed.

```
AS_PATH consists of one or more path segments:

+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Seg Type (1)  |  Seg Len (1)  |       AS Numbers (variable)  |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Segment Types:
  1 = AS_SET:      Unordered set of ASNs (from aggregation)
  2 = AS_SEQUENCE: Ordered sequence of ASNs (normal path)
  3 = AS_CONFED_SEQUENCE: Ordered confederation sequence (RFC 5065)
  4 = AS_CONFED_SET: Confederation set (RFC 5065)

AS Numbers: 2 bytes each (legacy), or 4 bytes each (RFC 6793 4-byte ASN mode)
```

**Example AS_PATH encoding for path 64512 65001 65002:**
```
Segment Type:   0x02 (AS_SEQUENCE)
Segment Length: 0x03 (3 ASNs)
ASN 64512:      0xFC 0x00
ASN 65001:      0xFD 0xE9
ASN 65002:      0xFD 0xEA

Wire bytes: 02 03 FC 00 FD E9 FD EA
```

**Loop detection**: Before accepting a route, a BGP speaker checks if its own ASN appears in AS_PATH. If so, the route is rejected (it came back to us — loop detected).

**AS_PATH length** is used in best path selection — shorter is preferred.

**AS_PATH prepending**: An AS can send its own ASN multiple times to artificially inflate path length and make the path less preferred. Used for traffic engineering.
```
Normal:    AS_PATH: 64512 65001
Prepended: AS_PATH: 64512 64512 64512 65001
```

**AS_SET usage in aggregation:**
When multiple routes with different AS paths are aggregated, the individual paths are combined into an AS_SET to preserve loop prevention information:
```
Contributing routes:
  10.0.0.0/24 via AS_SEQUENCE 64512 65001
  10.0.1.0/24 via AS_SEQUENCE 64512 65002

Aggregate 10.0.0.0/23:
  AS_SEQUENCE: 64512  AS_SET: {65001, 65002}
  Written as: AS_PATH 64512 {65001 65002}
```

### 7.3 NEXT_HOP (Type 3)

**Flags**: Well-known Mandatory (0x40)
**Length**: 4 bytes (IPv4 only; IPv6 uses MP_REACH_NLRI)

The IP address of the next router to forward packets to. Not necessarily the BGP peer itself.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  NEXT_HOP (IPv4 address, 4 bytes)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**NEXT_HOP rules:**
- eBGP: Set to self (the advertising router's interface IP facing the peer)
- iBGP: Passed through unchanged (the eBGP next-hop is preserved)

**iBGP NEXT_HOP issue**: When a route is learned via eBGP and propagated via iBGP, the NEXT_HOP is the external peer's IP, which may not be reachable from internal routers. Solutions:
1. `next-hop-self`: Override NEXT_HOP with self (route reflectors often do this)
2. Redistribute IGP routes to ensure external next-hops are reachable
3. Use MPLS/LDP to create tunnels to the BGP next-hop

**Third-party NEXT_HOP**: On multi-access networks (like IXPs), an eBGP speaker may set NEXT_HOP to a third router if all speakers share the same subnet. This reduces unnecessary router hops.

### 7.4 MULTI_EXIT_DISC / MED (Type 4)

**Flags**: Optional Non-transitive (0x80)
**Length**: 4 bytes

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                     MED Value (uint32, big-endian)            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

MED is a hint to external neighbors about the preferred entry point into the AS when multiple entry points exist.

**MED semantics:**
- Lower MED = preferred
- Only compared between routes from the **same neighboring AS** (by default)
- Not propagated to further ASes (non-transitive)
- If absent, treated as 0 (best) or infinity (worst), depending on implementation

**Hot Potato vs Cold Potato routing and MED:**
- Hot potato: Egress traffic ASAP (prefer shorter internal path, ignore MED from peer)
- Cold potato: Keep traffic longer internally, use MED to honor peer's preference

**always-compare-med**: Cisco/JunOS feature to compare MED even from different ASes (RFC-violating, use with care).

### 7.5 LOCAL_PREF (Type 5)

**Flags**: Well-known Discretionary (0x40), only exchanged between iBGP peers
**Length**: 4 bytes

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  LOCAL_PREF Value (uint32)                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Highest LOCAL_PREF wins.** This is the primary intra-AS traffic engineering tool.

Use cases:
```
100 = default (most implementations)
200 = prefer customer routes
150 = prefer peer routes
50  = deprioritize backup link
```

**Never sent to eBGP peers** (non-transitive in practice). Import policy sets LOCAL_PREF based on peer relationship:
```
From customer: LOCAL_PREF 200
From peer:     LOCAL_PREF 100
From provider: LOCAL_PREF 50
```

### 7.6 ATOMIC_AGGREGATE (Type 6)

**Flags**: Well-known Discretionary (0x40)
**Length**: 0 bytes (presence is the signal, no value)

Indicates that the route was aggregated and some path information was lost. Warns downstream routers that a more-specific path may be selected elsewhere.

### 7.7 AGGREGATOR (Type 7)

**Flags**: Optional Transitive (0xC0)
**Length**: 6 bytes (2-byte ASN + 4-byte IP) or 8 bytes (4-byte ASN + 4-byte IP)

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|        Last AS (2 or 4 bytes)         |  Aggregator IP (4)   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Identifies the AS and router that performed the aggregation. Informational only.

### 7.8 COMMUNITY (Type 8, RFC 1997)

**Flags**: Optional Transitive (0xC0)
**Length**: Multiple of 4 bytes

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   AS Number (2 bytes, high)   |   Value (2 bytes, low)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|   (repeated for each community)                               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Formatted as `ASN:Value` (e.g., `65000:100`). Used as route tags for policy. See Section 9 for complete community reference.

**Well-known communities (RFC 1997):**
```
0xFFFFFF01 = NO_EXPORT        (don't export to eBGP peers)
0xFFFFFF02 = NO_ADVERTISE     (don't advertise to any peer)
0xFFFFFF03 = NO_EXPORT_SUBCONFED (don't export outside confederation)
0xFFFF0000 = GRACEFUL_SHUTDOWN (RFC 8326, drain traffic before maintenance)
0xFFFFFF04 = NOPEER (don't advertise to peer ASes, only to customers/providers)
```

### 7.9 ORIGINATOR_ID (Type 9, RFC 4456)

**Flags**: Optional Non-transitive (0x80)
**Length**: 4 bytes

Added by Route Reflectors. Contains the BGP ID of the original route announcer. Used to prevent loops in RR topologies.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                   Originator ID (4 bytes, Router ID)          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 7.10 CLUSTER_LIST (Type 10, RFC 4456)

**Flags**: Optional Non-transitive (0x80)
**Length**: Multiple of 4 bytes

Added by each Route Reflector as the route passes through. Contains a list of Cluster IDs. Used for RR loop detection (if own Cluster ID is in the list, reject the route).

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Cluster ID (4 bytes)                         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             (repeated for each cluster traversed)             |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 7.11 MP_REACH_NLRI (Type 14, RFC 4760)

**Flags**: Optional Non-transitive (0x80)
**Length**: Variable

Multiprotocol Reachable NLRI — carries routes for non-IPv4 address families.

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       AFI (2 bytes)           |    SAFI (1 byte)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  NH Length(1) |          Next Hop (NH Length bytes)           |
+-+-+-+-+-+-+-+-+                                               +
|                               |  SNPA Num (1) |              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+              |
|                        NLRI (variable)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

SNPA: Subnetwork Points of Attachment (obsolete, always 0)
Next Hop: 16 bytes for IPv6 global, optionally 32 bytes for global+link-local
NLRI: IPv6 prefix encoding (same structure as IPv4 but 128-bit prefixes)
```

**IPv6 NLRI prefix encoding:**
```
+-+-+-+-+-+-+-+-+
|  Prefix Len   |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+...
|  Prefix (ceiling(len/8) bytes)|
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 7.12 MP_UNREACH_NLRI (Type 15, RFC 4760)

**Flags**: Optional Non-transitive (0x80)

Withdraws multiprotocol routes.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|       AFI (2 bytes)           |    SAFI (1 byte)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                Withdrawn Routes NLRI (variable)               |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 7.13 EXTENDED COMMUNITIES (Type 16, RFC 4360)

**Flags**: Optional Transitive (0xC0)
**Length**: Multiple of 8 bytes

8-byte communities with structured type field allowing more information density.

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Type High(1) |  Type Low (1) |        Value (6 bytes)        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Type High Bit 7: IANA authority
  0 = IANA assigned
  1 = Experimental

Type High Bit 6: Transitive
  0 = Transitive (propagate to eBGP)
  1 = Non-transitive

Common Extended Community Types:
  0x0002 = Route Target (RT):   used in VPNs to identify VRFs
  0x0003 = Route Origin (RO):   identifies originating VRF
  0x0004 = Link Bandwidth:      traffic engineering
  0x0006 = OSPF Domain ID
  0x0007 = OSPF Route Type
  0x0008 = OSPF Router ID
  0x000B = VRF Route Import
  0x0100 = Flow Spec Traffic Rate
  0x0101 = Flow Spec Traffic Action
  0x0102 = Flow Spec Redirect-to-VRF

Route Target encoding (Type 0x0002, AS:Value):
  | 0x00 | 0x02 | AS (2 bytes) | Value (4 bytes) |
  
Route Target encoding (Type 0x0102, IP:Value):
  | 0x01 | 0x02 | IP (4 bytes) | Value (2 bytes) |
```

### 7.14 AS4_PATH (Type 17, RFC 6793)

**Flags**: Optional Transitive (0xC0)

Used for 4-byte ASN backward compatibility. When a 4-byte ASN speaker communicates with a 2-byte ASN speaker, it:
- Uses AS_PATH with AS 23456 (AS_TRANS) as placeholder for 4-byte ASNs
- Carries real 4-byte AS_PATH in AS4_PATH attribute

### 7.15 LARGE_COMMUNITY (Type 32, RFC 8092)

**Flags**: Optional Transitive (0xC0)
**Length**: Multiple of 12 bytes

```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|              Global Administrator (4 bytes, ASN)              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             Local Data Part 1 (4 bytes)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|             Local Data Part 2 (4 bytes)                       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Written as: ASN:Part1:Part2
Example: 65000:1:100 (AS65000, function 1, value 100)
```

Solves the problem that standard communities cannot carry 4-byte ASNs as the high word.

---

## 8. BGP Decision Process

The BGP Decision Process (best path algorithm) selects one best path from all received paths for each prefix. This is applied to the Loc-RIB.

### 8.1 Decision Process Steps (RFC 4271 Section 9.1)

Applied in order, stop when a winner is found:

```
STEP 0:  Pre-requisite: NEXT_HOP must be reachable (resolvable in IGP/routing table)
         If NEXT_HOP is unreachable, route is ineligible.

STEP 1:  Highest LOCAL_PREF wins.
         (Only for iBGP — routes from eBGP carry LOCAL_PREF set by import policy)

STEP 2:  Locally originated route wins.
         (network statement, redistribute, aggregate > learned via BGP)

STEP 3:  Shortest AS_PATH wins.
         (AS_SET counts as 1. AS_CONFED_SEQUENCE segments ignored in count)

STEP 4:  Lowest ORIGIN wins.
         IGP (0) < EGP (1) < INCOMPLETE (2)

STEP 5:  Lowest MED wins.
         Only compared between routes from the same neighbor AS.
         Routes missing MED: treated as 0 or infinity (implementation defined).

STEP 6:  eBGP-learned route preferred over iBGP-learned route.

STEP 7:  Shortest IGP metric to NEXT_HOP wins.
         This is the "hot potato" step — prefer exit that's closest internally.

STEP 8:  (Cisco/JunOS tiebreaker) Prefer oldest eBGP route (most stable).
         This is implementation-defined, not RFC-mandated.

STEP 9:  Lowest BGP Router ID wins.

STEP 10: Lowest Cluster List Length wins. (Route Reflector tiebreaker)

STEP 11: Lowest neighbor IP address wins.
         (Final tiebreaker — always produces a winner)
```

### 8.2 ECMP (Equal-Cost Multi-Path)

BGP normally selects exactly one best path. ECMP allows multiple equal paths for load balancing:

- **iBGP multipath**: Multiple iBGP paths are eligible if they differ only in IGP cost to next-hop (all other attributes must be equal).
- **eBGP multipath**: Multiple eBGP paths are eligible if they are from different neighbors and attributes are equal (AS_PATH may differ if `as-path multipath-relax` is configured).
- **ADD-PATH (RFC 7911)**: Advertise multiple paths for the same prefix to allow downstream routers to choose. Each path gets a 4-byte Path ID prepended to NLRI.

### 8.3 Advertising the Best Path

After selecting the best path, BGP advertises it to peers with modifications:

```
For eBGP advertisement:
  1. Prepend own ASN to AS_PATH
  2. Set NEXT_HOP to self (interface IP facing the peer)
  3. Remove LOCAL_PREF
  4. Process export policy (may modify/filter)

For iBGP advertisement:
  1. Do NOT modify AS_PATH
  2. Do NOT change NEXT_HOP (third-party next-hop preserved)
  3. Include LOCAL_PREF
  4. Process export policy
```

### 8.4 Route Policy Language Concepts

Real routers use policy languages (JunOS routing-policy, Cisco route-map, FRR route-map) to:

**Import policy** (applied to Adj-RIB-In):
- Filter received routes (e.g., reject routes with your own ASN)
- Set LOCAL_PREF based on community or peer type
- Modify attributes (strip communities, set MED)

**Export policy** (applied to Adj-RIB-Out):
- Filter outgoing routes (e.g., don't send provider routes to peers)
- Prepend AS_PATH
- Set/strip communities
- Override NEXT_HOP

---

## 9. Communities and Extended Communities

### 9.1 Standard Community (RFC 1997)

Communities are carried opaquely — routers don't need to understand all communities, just pass them through (if transitive) or strip them at eBGP boundaries (implementation policy).

**Common community uses:**

```
Community         Meaning (convention, not enforced by protocol)
---------         -------
ASN:100           Customer route
ASN:200           Peer route
ASN:300           Provider route
ASN:666           Blackhole (route to null for DDoS mitigation, RFC 7999)
65535:666         Same, well-known BLACKHOLE community (RFC 7999)
ASN:9999          No-export (send only to customers)
65535:65281       NO_EXPORT
65535:65282       NO_ADVERTISE
```

**Blackhole routing with communities:**
The BLACKHOLE community (65535:666) tells transit providers to drop traffic to the specified prefix. Used during DDoS attacks to protect the upstream network:
```
Victim announces: 192.0.2.1/32 with community 65535:666
Transit providers: null-route 192.0.2.1/32 at their edge
Effect: DDoS traffic is dropped at the edge, never reaches victim
Cost: victim loses connectivity to that IP, but infrastructure survives
```

### 9.2 Extended Community (RFC 4360)

**Route Target (RT)** is the most important extended community — it enables MPLS/BGP VPNs (RFC 4364, L3VPN):

```
VRF "CustomerA" on PE1: exports routes with RT 65000:100
VRF "CustomerA" on PE2: imports routes with RT 65000:100
VRF "CustomerB" on PE2: imports routes with RT 65000:200

Result: CustomerA traffic stays in its VPN, CustomerB in its VPN.
```

**BGP Flow Specification (RFC 8955)** uses extended communities to distribute firewall rules:
```
Type 0x8006 = Traffic Rate
Type 0x8007 = Traffic Action (terminal, sample)
Type 0x8008 = Redirect to VRF
Type 0x8009 = Traffic Marking (DSCP)
```

A Flow Spec NLRI encodes a 5-tuple match:
```
NLRI components (encoded as TLVs):
  Type 1: Destination prefix
  Type 2: Source prefix
  Type 3: IP protocol (TCP=6, UDP=17, etc.)
  Type 4: Port
  Type 5: Destination port
  Type 6: Source port
  Type 7: ICMP type
  Type 8: ICMP code
  Type 9: TCP flags
  Type 10: Packet length
  Type 11: DSCP
  Type 12: Fragment
```

### 9.3 Large Community (RFC 8092)

Solves the 4-byte ASN problem:
```
Old: 65000:100  (ASN:Value — works only with 2-byte ASNs)
New: 131072:1:100  (4-byte ASN: Part1: Part2 — works with 32-bit ASNs)
```

Naming convention for Large Communities:
```
ASN:Function:Value

Functions (conventions):
  1 = Inform (informational, no action)
  2 = Control (action communities)
  3 = Scope (regional/geographic tags)

Example: 65000:2:1  = "AS65000 requests: do not export to peers"
```

---

## 10. Route Reflection and Confederations

### 10.1 The iBGP Full Mesh Problem

iBGP split horizon requires: every iBGP router must peer with every other iBGP router.
Full mesh session count: `N * (N-1) / 2`

For N=100: 4,950 sessions. For N=1000: 499,500 sessions. Unmanageable.

Two solutions: Route Reflection (RFC 4456) and Confederations (RFC 5065).

### 10.2 Route Reflection (RFC 4456)

A **Route Reflector (RR)** relaxes the split horizon rule. It can re-advertise iBGP-learned routes to iBGP peers.

**Cluster**: An RR and its clients form a cluster. The cluster has a Cluster ID (usually the RR's Router ID).

**iBGP peer types for an RR:**
- **Client**: iBGP peer that is part of the cluster. RR reflects routes between clients.
- **Non-client**: Regular iBGP peer (another RR or a non-client router). Normal iBGP rules apply.

**Reflection rules:**
```
Route received from eBGP:
  → Reflect to all clients AND all non-clients (normal BGP behavior)

Route received from a Client:
  → Reflect to: all clients (except originator) + all non-clients
  → Add ORIGINATOR_ID (= client's Router ID)
  → Add own Cluster ID to CLUSTER_LIST

Route received from a Non-client (iBGP):
  → Reflect to: all clients ONLY (not to other non-clients — split horizon)
  → Add ORIGINATOR_ID if not present
  → Add own Cluster ID to CLUSTER_LIST
```

**Loop prevention:**
- If ORIGINATOR_ID = own Router ID → discard (route came back to originator)
- If own Cluster ID is in CLUSTER_LIST → discard (route looped through this cluster)

**RR topology example:**
```
                    [RR1] ←iBGP→ [RR2]  (non-client peering between RRs)
                   / | \          / | \
             iBGP/  |  \ iBGP      |  \iBGP (client peerings)
             /     |    \         |    \
          [R1]   [R2]   [R3]   [R4]  [R5]
          client client client  client client
```

**Hierarchical Route Reflection:**
```
Level 1 RR ──── Level 2 RR ──── Leaf Clients
    |                  |
 Clients           Clients
```

Level 2 RRs are clients of Level 1 RRs and RRs to their own clients.

**RR pitfalls:**
1. **Suboptimal routing**: RR selects best path from its perspective, which may differ from what a client would select directly.
2. **RR as single point of failure**: Use redundant RR pairs with the same Cluster ID.
3. **NEXT_HOP not changed**: Clients still need IGP reachability to eBGP next-hops.

### 10.3 Confederations (RFC 5065)

Divide the AS into sub-ASes (confederation members). Each sub-AS runs iBGP internally and uses a modified eBGP between sub-ASes.

```
Confederation: AS 65000 (the "public" ASN visible externally)
  Sub-AS 65001:  routers R1, R2, R3
  Sub-AS 65002:  routers R4, R5, R6
  Sub-AS 65003:  routers R7, R8

Between sub-ASes: eBGP-like sessions but with CONFED rules:
  - AS_CONFED_SEQUENCE is used (not AS_SEQUENCE)
  - Confederation members strip CONFED segments before eBGP export
  - LOCAL_PREF is preserved across confederation boundaries
  - MED is preserved
  - NEXT_HOP behavior: like eBGP (set to self)

External peers see only AS 65000 in AS_PATH (CONFED segments stripped)
```

**Trade-off**: Confederations reduce sessions but require careful sub-AS numbering and are complex to manage. Route Reflection is more commonly deployed.

---

## 11. BGP Capabilities Negotiation

Capabilities are advertised in the OPEN message (Optional Parameter Type 2). If a peer doesn't understand a capability, it ignores it. If a capability is mandatory and unsupported, NOTIFICATION is sent.

### 11.1 Graceful Restart (RFC 4724)

When a BGP speaker restarts (software restart, process crash), without Graceful Restart, all sessions go down → massive churn in the routing table → convergence delay.

With Graceful Restart:
1. **Restarting speaker**: Advertises GR capability, declares which AFI/SAFIs it wants to preserve.
2. **Helper speaker**: When session drops, marks routes from the restarting peer as "stale" but keeps them in the RIB.
3. **Restart time**: The restarting speaker has `Restart Time` seconds to re-establish the session and re-send its routes.
4. **End-of-RIB marker**: After re-establishing, the restarting speaker sends all routes, then sends an empty UPDATE (End-of-RIB) to signal completion. Helper removes any remaining stale routes.

**GR Capability encoding:**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Restart Flags | Restart Time  |  (2 bytes)
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|     AFI (2)   | SAFI (1) |F|  |  (4 bytes per AFI/SAFI, repeated)
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Restart Flags: Bit R = Restarting (1 if currently restarting)
Restart Time: 0-4095 seconds
F flag per AFI/SAFI: Forwarding state preserved during restart
```

### 11.2 Long-Lived Graceful Restart (RFC 9494, LLGR)

Extends GR to allow stale routes to be retained for much longer (hours or days) at a lower preference. Used for planned maintenance:

```
Regular GR:  stale routes kept for Restart Time (≤4095 seconds ≈ 68 minutes)
LLGR:        stale routes kept for Long-Lived Stale Time (weeks)
             Stale routes get LLGR_STALE community (65535:6) applied
             and have local preference reduced
```

### 11.3 ADD-PATH (RFC 7911)

Normally, BGP sends only the best path for each prefix. ADD-PATH allows sending multiple paths:

```
ADD-PATH Capability per AFI/SAFI:
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  AFI (2)  | SAFI (1) | Send/Receive (1)       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

Send/Receive:
  1 = Receive (want to receive multiple paths)
  2 = Send (can send multiple paths)
  3 = Both

NLRI with ADD-PATH prepends a 4-byte Path ID:
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                  Path Identifier (4 bytes)                    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Prefix Len   |  Prefix (variable)                            |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

Use cases:
- Route reflector sends all paths to clients, clients make local best-path decision
- PIC (Prefix Independent Convergence) pre-loading backup paths
- BGP Optimal Route Reflection (ORR)

---

## 12. MP-BGP: Multiprotocol Extensions

RFC 4760 extends BGP beyond IPv4 unicast. The framework:
- New AFI/SAFI pairs for different address families
- MP_REACH_NLRI and MP_UNREACH_NLRI carry non-IPv4 routes
- Original NLRI and Withdrawn Routes fields still used for IPv4 unicast

### 12.1 IPv6 Unicast (AFI=2, SAFI=1)

IPv6 next-hops can be:
- 16 bytes: global IPv6 address
- 32 bytes: global + link-local (link-local needed for on-link next-hops)

```
Example MP_REACH_NLRI for 2001:db8::/32 via 2001:db8::1:
  AFI:       0x00 0x02 (2 = IPv6)
  SAFI:      0x01 (1 = Unicast)
  NH Len:    0x10 (16)
  Next Hop:  2001:0db8:0000:0000:0000:0000:0000:0001
  SNPA Num:  0x00
  NLRI:      0x20 (prefix-len=32) 0x20 0x01 0x0d 0xb8 (4 bytes, /32 = ceil(32/8))
```

### 12.2 EVPN (AFI=25, SAFI=70, RFC 7432)

EVPN (Ethernet VPN) uses BGP to distribute MAC/IP bindings, BUM (Broadcast, Unknown, Multicast) handling, and multi-homing information for overlay networks (VXLAN, MPLS).

EVPN Route Types:
```
Type 1: Ethernet Auto-Discovery (per-ESI/per-EVI)
Type 2: MAC/IP Advertisement
Type 3: Inclusive Multicast Ethernet Tag
Type 4: Ethernet Segment
Type 5: IP Prefix Route
```

**Type 2 (MAC/IP) NLRI encoding:**
```
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Route Distinguisher (8 bytes)         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| ESI (10 bytes)                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| Ethernet Tag (4 bytes)                |
+-+-+-+-+-+-+-+-+--+-+-+-+-+-+-+-+-+-+--+
| MAC Addr Len  |  MAC Address (6B) |
+-+-+-+-+-+-+-+-+-------------------+
| IP Addr Len   |  IP Address (4 or 16 bytes, optional) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
| MPLS Label1 (3 bytes) |
+-+-+-+-+-+-+-+-+-+-+-+-+
| MPLS Label2 (3 bytes, optional) |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### 12.3 BGP-LS (AFI=16388, SAFI=71, RFC 7752)

BGP-Link State distributes topology information from IGPs (OSPF, IS-IS) to a central controller (SDN, PCE) via BGP. The controller uses this topology to compute optimal paths without running the IGP itself.

NLRI types:
```
Type 1: Node NLRI (describes a router node)
Type 2: Link NLRI (describes a link between nodes)
Type 3: IPv4 Topology Prefix NLRI
Type 4: IPv6 Topology Prefix NLRI
```

---

## 13. BGP Security

BGP security is critical because BGP misconfigurations and attacks have caused major internet outages.

### 13.1 BGP Threat Model

**Prefix hijacking**: AS announces IP space it doesn't own. Traffic intended for the legitimate owner is redirected.
- **2008 Pakistan Telecom hijack**: Pakistani ISP hijacked YouTube's /24 prefix, dropping YouTube globally for ~2 hours.
- **2019 Rostelecom hijack**: Russian ISP accidentally (or not) hijacked routes for Google, Amazon, Cloudflare.
- **2010 China Telecom**: Chinese ISP leaked 15% of internet routes.

**Route leak**: AS announces routes it shouldn't (e.g., provider routes to another provider), creating unintended transit paths.

**BGP session attacks**: Injecting false BGP messages, RST attacks to drop sessions, replay attacks.

**Sub-prefix hijacking**: Announce a more specific prefix. BGP always prefers more specific → traffic goes to attacker even if the original /16 is also announced.

### 13.2 RPKI (Resource Public Key Infrastructure, RFC 6480)

RPKI is a cryptographic system that allows IP address holders to create signed attestations (ROAs) that authorize specific ASes to announce specific prefixes.

**ROA (Route Origin Authorization):**
```
ROA contains:
  - ASN: authorized to originate
  - Prefix: the IP prefix
  - Max Length: maximum prefix length allowed

Example: "AS64512 is authorized to announce 192.0.2.0/24 with max-length /24"
```

**RPKI validation states for a BGP route:**
```
Valid:     A ROA exists that matches (prefix, origin ASN, length ≤ max-length)
Invalid:   A ROA exists for the prefix but a different ASN is the origin,
           OR prefix length exceeds max-length
Not Found: No ROA exists covering this prefix (most common, status quo for old prefixes)
```

**ROA database hierarchy:**
```
IANA
 └── Regional Internet Registries (RIRs):
      ├── ARIN  (North America)
      ├── RIPE NCC (Europe/Middle East/Central Asia)
      ├── APNIC (Asia-Pacific)
      ├── LACNIC (Latin America)
      └── AFRINIC (Africa)
          └── ISPs/LIRs
               └── End Users
                    └── ROAs signed with private key certified by RIR
```

**Relying Party (RP) software** (e.g., Routinator, OctoRPKI, FORT, rpki-client) downloads and validates the ROA database, then exposes a VRP (Validated ROA Payload) table to the router via RTR protocol (RFC 8210).

**RTR Protocol (RPKI-to-Router):**
```
Router <──RTR/TCP──> Validation Cache (e.g., Routinator)

RTR messages:
  Serial Notify:  cache has updates
  Serial Query:   router requests delta since serial N
  Reset Query:    router requests full refresh
  Cache Response: response to query
  IPv4 Prefix:    one validated prefix record
  IPv6 Prefix:    one validated prefix record
  End of Data:    marks end of response
  Cache Reset:    cache cannot serve delta, do full reset
  Router Key:     BGPSEC router key
  Error Report:   error notification
```

**ROT (Route Origin Trust) enforcement options:**
```
Policy option 1: Prefer Valid over Not Found over Invalid (RFC 8893)
Policy option 2: Reject Invalid routes (strict RPKI enforcement)
Policy option 3: Inform only (log but don't reject)

Production best practice: Reject Invalid, prefer Valid, accept Not Found
```

### 13.3 BGPsec (RFC 8205)

BGPsec adds cryptographic signatures to AS_PATH, allowing each AS to prove it legitimately received the route from the previous AS. Protects against AS_PATH manipulation.

**BGPsec Signature:**
Each hop adds:
```
Signature segment for AS N:
  Subject Key Identifier (SKI) of AS N's key
  Signature: ECDSA-P256 over (AS N, next-hop, target peer AS, previous signature)
```

**BGPsec limitations:**
- Requires ALL ASes in path to sign (partial deployment is less useful)
- Higher computational cost per route
- Does not prevent route leaks (only AS_PATH forgery)
- Deployment has been slow; RPKI is more widely adopted

### 13.4 Prefix Filtering (IRRDB-based)

Internet Route Registry (IRR) databases (RIPE DB, ARIN IRR, RADb, APNIC WHOIS) contain routing policy objects:

```
route:    192.0.2.0/24
descr:    Example prefix
origin:   AS64512
mnt-by:   EXAMPLE-MNT

aut-num:  AS64512
import:   from AS65001 accept AS65001
export:   to AS65001 announce AS64512
```

Tools like **bgpq4** generate prefix lists and AS path access lists from IRR data:
```bash
bgpq4 -4 AS64512          # Generate prefix-list for AS64512's prefixes
bgpq4 -4 AS-EXAMPLE-SET   # Generate for an AS-SET (group of ASes)
```

### 13.5 MANRS (Mutually Agreed Norms for Routing Security)

Four actions:
1. **Filtering**: Ensure correctness of own announcements, filter customers
2. **Anti-spoofing**: Implement BCP38 unicast reverse path forwarding
3. **Coordination**: Maintain up-to-date IRR/RPKI data
4. **Global Validation**: Publish routing policy in IRR

### 13.6 BGP Session Security

**TCP MD5 (RFC 2385)**:
```
Shared key configured on both peers.
Every TCP segment signed with HMAC-MD5.
Prevents session injection but uses deprecated MD5.
```

**TCP-AO (RFC 5925)** — modern replacement:
```
Supports multiple algorithms (HMAC-SHA1, HMAC-SHA256, AES-128-CMAC)
Supports key rollover without session reset
Protects against TIME_WAIT attacks
```

**GTSM (Generalized TTL Security Mechanism, RFC 5082)**:
```
eBGP sessions: Set TTL=255 on send, require TTL≥254 on receive.
This ensures the packet traversed at most 1 hop.
Prevents off-path attacks that can't set TTL=255.

Config example (Cisco): neighbor 192.0.2.1 ttl-security hops 1
```

**Maximum Prefix Limits**:
```
Prevent a misbehaving peer from flooding your table:
  max-prefix 1000        → if peer sends >1000 prefixes, drop session
  max-prefix 1000 80     → warn at 80%, drop at 100%
  max-prefix 1000 warning-only → log but don't drop

Security value: prevents memory exhaustion and table poisoning.
```

### 13.7 BGP Hijack Detection

**Automated detection systems:**
- **BGPmon**: Real-time BGP monitoring
- **RIPE Stat**: Historical BGP data
- **Cloudflare Radar BGP**: Community tool
- **ARTEMIS** (RFC-documented framework): Automated real-time BGP hijack detection

Detection approach:
```
1. Subscribe to BGP route collectors (RIPE RIS, RouteViews, PCH)
2. Monitor for your prefixes appearing with unauthorized origin ASNs
3. Monitor for your prefixes being announced as more-specifics
4. Alert ops team and optionally auto-announce more-specific to override
```

---

## 14. BGP in Data Center (DC BGP)

### 14.1 Clos Fabric with BGP

Modern data centers use BGP where interior protocols like OSPF were traditionally used. RFC 7938 documents this pattern ("Use of BGP for Routing in Large-Scale Data Centers").

**Spine-Leaf topology:**
```
                [Spine1]    [Spine2]    [Spine3]    [Spine4]
                  / | \      / | \      / | \      / | \
                 /  |  \    /  |  \    /  |  \    /  |  \
              [L1] [L2] [L3] [L4] [L5] [L6] [L7] [L8]
              Leaf (ToR) switches, each connected to all spines

Between Leaf and Spine: eBGP peering
Between servers and Leaf: eBGP or static
Each Leaf: unique AS number (private range)
Each Spine tier: unique AS number (same AS for all spines in tier)

Example ASN assignment:
  Servers: 65535 (or per-rack)
  Leaf tier: 65001-65032 (one per leaf)
  Spine tier 1: 65100
  Spine tier 2: 65200
  Super-spines: 65300
```

**Why BGP instead of OSPF/IS-IS in DC?**
1. **Scale**: BGP handles 100,000+ routes without flooding the entire fabric
2. **Policy**: BGP policy language for traffic engineering
3. **ECMP**: BGP ECMP distributes across all spine links
4. **Independence**: Spine failure doesn't cause convergence events in unaffected pods
5. **Simplicity at scale**: BGP sessions are point-to-point, no DR/BDR election

### 14.2 Unnumbered BGP (RFC 5549)

In DC, assigning IP addresses to every link is operationally expensive. Unnumbered BGP uses:
- IPv6 Link-Local addresses for BGP peering
- Extended Next-Hop Encoding (RFC 8950) to carry IPv4 next-hops as IPv6

```
Each interface gets an auto-configured link-local IPv6 address (fe80::/10 range)
BGP sessions established using link-local IPs discovered via Router Advertisements
IPv4 NLRI carried in MP_REACH_NLRI with IPv6 next-hop (8950 capability)

Benefits:
  - No IP address management for inter-switch links
  - Auto-discovery of neighbors via ICMPv6 RA
  - Simplified configuration: just enable BGP on the interface
```

### 14.3 EVPN/VXLAN with BGP

BGP EVPN (RFC 7432) + VXLAN is the dominant overlay for DC networks:

```
VTEP (VXLAN Tunnel Endpoint) ←→ BGP EVPN ←→ VTEP

BGP EVPN distributes:
  Type 2: MAC addresses and their IP bindings
  Type 3: BUM (Broadcast, Unknown, Multicast) handling via multicast or ingress replication
  Type 5: IP prefix routes (for inter-VRF routing, EVPN-IRB)

Each VTEP is a BGP speaker announcing its locally-learned MACs/IPs.
No need for data-plane MAC flooding to learn remote MACs.
```

---

## 15. BGP Convergence and Tuning

### 15.1 Convergence Timers

BGP convergence is intentionally slow by default to ensure stability.

```
Hold Timer:         90s (session drops after 90s of silence)
KeepaliveTimer:     30s
MinRouteAdvertisementInterval (MRAI): 
  eBGP: 30s  (don't send updates to same peer more often)
  iBGP: 5s
ConnectRetryTimer:  120s

These defaults mean:
  Worst case detection: 90s (hold timer expiry)
  Worst case re-advertisement: 30s (MRAI)
  Total worst case: 90 + 30 = 120s convergence
```

### 15.2 Tuning for Fast Convergence

**Reduce timers** (common in DC environments):
```
Hold Time: 9s (3s keepalive) — requires BFD-free fast failure detection
Hold Time: 3s (1s keepalive) — aggressive, for DC-internal sessions
MRAI: 0s (instant advertisements, careful of routing oscillation)
```

**BFD (Bidirectional Forwarding Detection, RFC 5880)**:
BFD is a lightweight hello protocol that detects link failures in milliseconds:
```
BFD operates at ~1ms-10ms intervals (vs 30s BGP keepalive)
When BFD detects failure → notifies BGP immediately → session down
BGP reacts to BFD signal in <1 second vs 90 seconds
```

**PIC (Prefix Independent Convergence):**
Pre-compute backup paths so that when primary fails, forwarding switches without waiting for BGP reconvergence:
```
Primary path: Leaf → Spine1 → Remote Leaf
Backup path:  Leaf → Spine2 → Remote Leaf (pre-programmed)
On Spine1 failure: Switch forwarding entry to backup path → sub-second
BGP reconvergence continues in background
```

### 15.3 Route Dampening (RFC 2439)

Unstable routes (flapping) cause excessive BGP updates. Dampening penalizes unstable routes:

```
Each route flap adds a penalty (1000 by default)
Penalty decays over time (half-life: 15 minutes by default)
When penalty > suppress-limit (2000): route is suppressed (hidden)
When penalty < reuse-limit (750): route is re-advertised
Maximum suppression time: 4x half-life (60 minutes)

Problem: Route dampening can keep legitimate routes suppressed.
RFC 7196 recommends NOT using dampening for eBGP sessions.
Modern practice: Use BFD + fast timers instead of dampening.
```

### 15.4 BGP Best Path Change Suppression and Soft Reconfiguration

**Soft Reconfiguration Inbound**: Store a copy of all received routes before policy in Adj-RIB-In. Allows applying new import policy without resetting the session. Memory expensive.

**Route Refresh (RFC 2918)**: Ask peer to re-send routes. No need to store raw Adj-RIB-In. After applying new policy, send Route-Refresh, peer re-sends routes.

**Enhanced Route Refresh (RFC 7313)**: Adds begin/end markers around the route refresh to help the receiver know when the refresh is complete.

---

## 16. Troubleshooting BGP

### 16.1 Session Not Establishing

```
Step 1: TCP connectivity
  ping <peer-ip>                    # basic reachability
  telnet <peer-ip> 179              # TCP port 179 open?
  tcpdump -i eth0 port 179          # see TCP handshake

Step 2: Common causes
  - Firewall blocking port 179
  - Wrong peer IP configured
  - Wrong ASN configured (OPEN rejected)
  - BGP ID collision
  - TTL issue (multihop eBGP, need 'ebgp-multihop')
  - MD5 password mismatch (TCP ACK never arrives)
  - Incompatible capabilities (check NOTIFICATION code 2)

Step 3: Debug
  debug ip bgp <peer> events        # Cisco
  show bgp neighbor <peer>          # check FSM state, last error
```

### 16.2 Session Established But No Routes

```
Common causes:
  - Import policy rejecting all routes
  - NEXT_HOP not reachable (route not installed)
  - Prefix list / route-map filtering
  - Network command or redistribute not configured

Debug:
  show bgp neighbors <peer> received-routes   # what peer sent (needs soft-reconfiguration)
  show bgp neighbors <peer> routes            # what passed import policy
  show bgp neighbors <peer> advertised-routes # what we sent to peer
```

### 16.3 Route Present But Not Installed in FIB

```
Common causes:
  - NEXT_HOP not in IGP (unresolvable)
  - iBGP route with unreachable next-hop (need IGP or next-hop-self)
  - Prefix blocked by maximum-prefix
  - RPKI Invalid (if strict enforcement enabled)

show ip bgp 192.0.2.0/24    # check route status, '>' means best, installed
show ip route 192.0.2.0/24  # check FIB installation
```

### 16.4 Asymmetric Routing

If traffic takes a different path in/out:
```
Inbound path:  determined by how you announce prefixes to peers
  Tools: AS_PATH prepending, MED, selective announcement (more/less specific)

Outbound path: determined by LOCAL_PREF, AS_PATH length, MED from peer
  Tools: Set LOCAL_PREF in import policy

Common issue: "Hot potato" vs "cold potato" routing disagreement with peer
```

### 16.5 BGP Route Oscillation (Wedgies)

BGP can oscillate between paths indefinitely in certain topologies with MED (RFC 3345 "BGP Wedgies"). This occurs when:
- Routes from different ASes are compared via MED (requires always-compare-med)
- Path selection outcomes are inconsistent due to MED comparison asymmetry

Solution: Use LOCAL_PREF instead of MED for intra-AS decisions. Avoid always-compare-med.

---

## 17. C Implementation

A production-quality BGP implementation in C, implementing the FSM, message parser, and basic route management.

### 17.1 Project Structure

```
bgp_impl/
├── Makefile
├── src/
│   ├── main.c
│   ├── bgp.h
│   ├── bgp_fsm.c
│   ├── bgp_msg.c          # Message parser/builder
│   ├── bgp_attr.c         # Path attribute handling
│   ├── bgp_rib.c          # Route Information Base
│   └── bgp_io.c           # TCP/IO handling
└── tests/
    ├── test_msg_parse.c
    └── test_fsm.c
```

### 17.2 bgp.h — Core Types and Structures

```c
// File: src/bgp.h
// BGP-4 Implementation — Core types
// Implements RFC 4271

#ifndef BGP_H
#define BGP_H

#include 
#include 
#include <netinet/in.h>
#include <sys/socket.h>
#include 

// ============================================================
// Constants
// ============================================================

#define BGP_PORT              179
#define BGP_MARKER_LEN        16
#define BGP_HEADER_LEN        19
#define BGP_MAX_MSG_LEN       4096
#define BGP_EXT_MAX_MSG_LEN   65535  // RFC 8654
#define BGP_VERSION           4

// Hold timer negotiation
#define BGP_HOLD_TIME_DEFAULT     90
#define BGP_KEEPALIVE_DEFAULT     30
#define BGP_CONNECT_RETRY_TIME   120

// Message types
#define BGP_MSG_OPEN           1
#define BGP_MSG_UPDATE         2
#define BGP_MSG_NOTIFICATION   3
#define BGP_MSG_KEEPALIVE      4
#define BGP_MSG_ROUTE_REFRESH  5

// Path attribute type codes
#define BGP_ATTR_ORIGIN         1
#define BGP_ATTR_AS_PATH        2
#define BGP_ATTR_NEXT_HOP       3
#define BGP_ATTR_MED            4
#define BGP_ATTR_LOCAL_PREF     5
#define BGP_ATTR_ATOMIC_AGG     6
#define BGP_ATTR_AGGREGATOR     7
#define BGP_ATTR_COMMUNITY      8
#define BGP_ATTR_ORIGINATOR_ID  9
#define BGP_ATTR_CLUSTER_LIST  10
#define BGP_ATTR_MP_REACH      14
#define BGP_ATTR_MP_UNREACH    15
#define BGP_ATTR_EXT_COMM      16
#define BGP_ATTR_AS4_PATH      17
#define BGP_ATTR_LARGE_COMM    32

// Attribute flag bits
#define BGP_ATTR_FLAG_OPTIONAL   0x80
#define BGP_ATTR_FLAG_TRANSITIVE 0x40
#define BGP_ATTR_FLAG_PARTIAL    0x20
#define BGP_ATTR_FLAG_EXT_LEN    0x10

// ORIGIN values
#define BGP_ORIGIN_IGP        0
#define BGP_ORIGIN_EGP        1
#define BGP_ORIGIN_INCOMPLETE 2

// AS_PATH segment types
#define BGP_AS_SET            1
#define BGP_AS_SEQUENCE       2
#define BGP_AS_CONFED_SEQ     3
#define BGP_AS_CONFED_SET     4

// Error codes
#define BGP_ERR_HEADER        1
#define BGP_ERR_OPEN          2
#define BGP_ERR_UPDATE        3
#define BGP_ERR_HOLD_TIMER    4
#define BGP_ERR_FSM           5
#define BGP_ERR_CEASE         6

// Error subcodes — Header
#define BGP_ERR_HDR_SYNC      1
#define BGP_ERR_HDR_LEN       2
#define BGP_ERR_HDR_TYPE      3

// Error subcodes — OPEN
#define BGP_ERR_OPEN_VERSION  1
#define BGP_ERR_OPEN_AS       2
#define BGP_ERR_OPEN_BGP_ID   3
#define BGP_ERR_OPEN_OPT_PARM 4
#define BGP_ERR_OPEN_HOLD     6

// Error subcodes — UPDATE
#define BGP_ERR_UPD_ATTR_LIST  1
#define BGP_ERR_UPD_WELL_KNOWN 2
#define BGP_ERR_UPD_MISSING    3
#define BGP_ERR_UPD_ATTR_FLAGS 4
#define BGP_ERR_UPD_ATTR_LEN   5
#define BGP_ERR_UPD_ORIGIN     6
#define BGP_ERR_UPD_NEXT_HOP   8
#define BGP_ERR_UPD_OPT_ATTR   9
#define BGP_ERR_UPD_NETWORK   10
#define BGP_ERR_UPD_AS_PATH   11

// Cease subcodes
#define BGP_CEASE_MAX_PREFIXES  1
#define BGP_CEASE_ADMIN_SHUT    2
#define BGP_CEASE_PEER_DECONF   3
#define BGP_CEASE_ADMIN_RESET   4

// Capability codes
#define BGP_CAP_MPEXT          1   // Multiprotocol Extensions
#define BGP_CAP_ROUTE_REFRESH  2
#define BGP_CAP_GRACEFUL_REST  64
#define BGP_CAP_4BYTE_ASN      65
#define BGP_CAP_ADD_PATH       69
#define BGP_CAP_EXT_MSG        6

// AFI/SAFI
#define BGP_AFI_IPV4           1
#define BGP_AFI_IPV6           2
#define BGP_SAFI_UNICAST       1
#define BGP_SAFI_MULTICAST     2
#define BGP_SAFI_MPLS          4
#define BGP_SAFI_EVPN         70

// FSM states
typedef enum {
    BGP_STATE_IDLE        = 0,
    BGP_STATE_CONNECT     = 1,
    BGP_STATE_ACTIVE       = 2,
    BGP_STATE_OPENSENT    = 3,
    BGP_STATE_OPENCONFIRM = 4,
    BGP_STATE_ESTABLISHED = 5,
} bgp_state_t;

// FSM events
typedef enum {
    BGP_EVENT_MANUAL_START        = 1,
    BGP_EVENT_MANUAL_STOP         = 2,
    BGP_EVENT_AUTO_START          = 3,
    BGP_EVENT_CONNECT_RETRY_EXP   = 9,
    BGP_EVENT_HOLD_TIMER_EXP      = 10,
    BGP_EVENT_KEEPALIVE_TIMER_EXP = 11,
    BGP_EVENT_TCP_CR_ACKED        = 16,
    BGP_EVENT_TCP_CONN_VALID      = 17,
    BGP_EVENT_TCP_CONN_FAILS      = 18,
    BGP_EVENT_BGP_OPEN            = 19,
    BGP_EVENT_BGP_OPEN_WITH_DELAY = 20,
    BGP_EVENT_BGP_HDR_ERR         = 21,
    BGP_EVENT_BGP_OPEN_ERR        = 22,
    BGP_EVENT_NOTIF_MSG           = 25,
    BGP_EVENT_KEEPALIVE_MSG       = 26,
    BGP_EVENT_UPDATE_MSG          = 27,
    BGP_EVENT_UPDATE_ERR          = 28,
} bgp_event_t;

// ============================================================
// Data structures
// ============================================================

// IP prefix (IPv4)
typedef struct {
    struct in_addr prefix;
    uint8_t        length;
} bgp_prefix4_t;

// IP prefix (IPv6)
typedef struct {
    struct in6_addr prefix;
    uint8_t         length;
} bgp_prefix6_t;

// AS_PATH segment
typedef struct bgp_as_seg {
    uint8_t          type;     // AS_SEQUENCE or AS_SET
    uint16_t         count;
    uint32_t        *asns;     // array of ASNs (4-byte)
    struct bgp_as_seg *next;
} bgp_as_seg_t;

// Path attributes (parsed)
typedef struct {
    uint8_t   origin;
    bgp_as_seg_t *as_path;         // linked list of segments
    struct in_addr next_hop;
    uint32_t  med;
    uint8_t   med_present;
    uint32_t  local_pref;
    uint8_t   local_pref_present;
    uint8_t   atomic_aggregate;
    uint32_t *communities;
    uint16_t  community_count;
    uint32_t  originator_id;
    uint8_t   originator_id_present;
    uint8_t  *raw;                 // raw attribute bytes (for unknown attrs)
    size_t    raw_len;
} bgp_path_attrs_t;

// A single BGP route
typedef struct bgp_route {
    bgp_prefix4_t   prefix;
    bgp_path_attrs_t attrs;
    time_t          received_at;
    struct bgp_route *next;
} bgp_route_t;

// BGP message header
typedef struct {
    uint8_t  marker[BGP_MARKER_LEN];
    uint16_t length;
    uint8_t  type;
} __attribute__((packed)) bgp_header_t;

// OPEN message (body only)
typedef struct {
    uint8_t  version;
    uint16_t my_as;        // 2-byte AS field (use 23456 for 4-byte ASNs)
    uint16_t hold_time;
    uint32_t bgp_id;
    uint8_t  opt_parm_len;
    // followed by optional parameters
} __attribute__((packed)) bgp_open_t;

// Capability
typedef struct {
    uint8_t code;
    uint8_t len;
    uint8_t data[];
} __attribute__((packed)) bgp_capability_t;

// Parsed OPEN parameters
typedef struct {
    uint32_t my_as;        // actual 4-byte ASN (from capability or 2-byte field)
    uint16_t hold_time;
    uint32_t bgp_id;
    uint8_t  can_4byte_asn;
    uint8_t  can_route_refresh;
    uint8_t  can_mp_ipv4_unicast;
    uint8_t  can_mp_ipv6_unicast;
    uint8_t  can_graceful_restart;
    uint16_t gr_restart_time;
    uint8_t  can_add_path;
    uint8_t  can_ext_msg;
} bgp_open_params_t;

// Peer configuration and state
typedef struct bgp_peer {
    // Configuration
    struct in_addr local_addr;
    struct in_addr peer_addr;
    uint32_t       local_as;
    uint32_t       peer_as;       // expected peer AS (0 = any)
    uint16_t       hold_time;
    char           password[64];  // TCP MD5 password (empty = disabled)
    uint32_t       local_bgp_id;
    uint8_t        is_passive;    // don't initiate, only accept
    uint32_t       max_prefixes;
    
    // Runtime state
    bgp_state_t    state;
    int            fd;            // TCP socket
    
    // Timers (seconds since epoch)
    time_t         hold_timer;
    time_t         keepalive_timer;
    time_t         connect_retry_timer;
    
    // Negotiated parameters
    bgp_open_params_t remote_params;
    uint16_t       negotiated_hold_time;
    uint16_t       negotiated_keepalive;
    
    // Statistics
    uint64_t       msgs_in;
    uint64_t       msgs_out;
    uint64_t       updates_in;
    uint64_t       updates_out;
    uint64_t       prefixes_received;
    time_t         session_established_at;
    
    // Receive buffer
    uint8_t        rx_buf[BGP_MAX_MSG_LEN];
    size_t         rx_buf_pos;
    
    // Adj-RIB-In: routes received from peer
    bgp_route_t   *adj_rib_in;
    
    struct bgp_peer *next;
} bgp_peer_t;

// ============================================================
// Function prototypes
// ============================================================

// bgp_fsm.c
void bgp_fsm_event(bgp_peer_t *peer, bgp_event_t event);
const char *bgp_state_name(bgp_state_t state);
const char *bgp_event_name(bgp_event_t event);

// bgp_msg.c
int  bgp_msg_build_open(uint8_t *buf, size_t bufsz, bgp_peer_t *peer);
int  bgp_msg_build_keepalive(uint8_t *buf, size_t bufsz);
int  bgp_msg_build_notification(uint8_t *buf, size_t bufsz,
                                uint8_t error_code, uint8_t error_subcode,
                                const uint8_t *data, size_t data_len);
int  bgp_msg_build_route_refresh(uint8_t *buf, size_t bufsz,
                                 uint16_t afi, uint8_t safi);
int  bgp_msg_parse_header(const uint8_t *buf, size_t len,
                          uint16_t *out_length, uint8_t *out_type);
int  bgp_msg_parse_open(const uint8_t *buf, size_t len,
                        bgp_open_params_t *out);
int  bgp_msg_parse_update(const uint8_t *buf, size_t len,
                          bgp_prefix4_t **withdrawn, uint16_t *n_withdrawn,
                          bgp_path_attrs_t *attrs,
                          bgp_prefix4_t **nlri, uint16_t *n_nlri);

// bgp_attr.c
int  bgp_attr_parse(const uint8_t *buf, size_t len, bgp_path_attrs_t *attrs);
void bgp_attr_free(bgp_path_attrs_t *attrs);
int  bgp_attr_encode(const bgp_path_attrs_t *attrs, uint8_t *buf, size_t bufsz);
int  bgp_as_path_contains(const bgp_as_seg_t *path, uint32_t asn);
int  bgp_as_path_length(const bgp_as_seg_t *path);

// bgp_rib.c
bgp_route_t *bgp_rib_lookup(bgp_route_t *rib, const bgp_prefix4_t *prefix);
void bgp_rib_add(bgp_route_t **rib, bgp_route_t *route);
void bgp_rib_remove(bgp_route_t **rib, const bgp_prefix4_t *prefix);
void bgp_rib_free(bgp_route_t **rib);
bgp_route_t *bgp_decision_process(bgp_peer_t **peers, int n_peers,
                                  const bgp_prefix4_t *prefix);

// bgp_io.c
int  bgp_io_connect(bgp_peer_t *peer);
int  bgp_io_send(bgp_peer_t *peer, const uint8_t *buf, size_t len);
int  bgp_io_recv(bgp_peer_t *peer);
void bgp_io_close(bgp_peer_t *peer);
int  bgp_io_set_md5(int fd, const struct in_addr *peer_addr, const char *key);

#endif // BGP_H
```

### 17.3 bgp_msg.c — Message Parser and Builder

```c
// File: src/bgp_msg.c
// BGP message parsing and building

#include "bgp.h"
#include 
#include <arpa/inet.h>
#include 
#include 

// Canonical BGP marker (all 0xFF)
static const uint8_t BGP_MARKER[BGP_MARKER_LEN] = {
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF,
};

// ============================================================
// Message building helpers
// ============================================================

// Write BGP common header into buf
// Returns total header bytes written (BGP_HEADER_LEN = 19)
static int write_header(uint8_t *buf, size_t bufsz,
                        uint16_t total_len, uint8_t type) {
    if (bufsz < BGP_HEADER_LEN) return -1;
    memcpy(buf, BGP_MARKER, BGP_MARKER_LEN);
    uint16_t net_len = htons(total_len);
    memcpy(buf + 16, &net_len, 2);
    buf[18] = type;
    return BGP_HEADER_LEN;
}

// ============================================================
// KEEPALIVE
// ============================================================

int bgp_msg_build_keepalive(uint8_t *buf, size_t bufsz) {
    if (bufsz < BGP_HEADER_LEN) return -1;
    return write_header(buf, bufsz, BGP_HEADER_LEN, BGP_MSG_KEEPALIVE);
}

// ============================================================
// NOTIFICATION
// ============================================================

int bgp_msg_build_notification(uint8_t *buf, size_t bufsz,
                               uint8_t error_code, uint8_t error_subcode,
                               const uint8_t *data, size_t data_len) {
    size_t total = BGP_HEADER_LEN + 2 + data_len;
    if (bufsz < total || total > BGP_MAX_MSG_LEN) return -1;

    write_header(buf, bufsz, (uint16_t)total, BGP_MSG_NOTIFICATION);
    buf[19] = error_code;
    buf[20] = error_subcode;
    if (data && data_len > 0)
        memcpy(buf + 21, data, data_len);
    return (int)total;
}

// ============================================================
// ROUTE REFRESH
// ============================================================

int bgp_msg_build_route_refresh(uint8_t *buf, size_t bufsz,
                                uint16_t afi, uint8_t safi) {
    size_t total = BGP_HEADER_LEN + 4;
    if (bufsz < total) return -1;
    write_header(buf, bufsz, (uint16_t)total, BGP_MSG_ROUTE_REFRESH);
    uint16_t net_afi = htons(afi);
    memcpy(buf + 19, &net_afi, 2);
    buf[21] = 0;    // reserved
    buf[22] = safi;
    return (int)total;
}

// ============================================================
// OPEN
// ============================================================

int bgp_msg_build_open(uint8_t *buf, size_t bufsz, bgp_peer_t *peer) {
    // Build optional parameters
    uint8_t opt_params[256];
    size_t  opt_len = 0;

    // Helper: append capability to opt_params
    #define CAP_APPEND(code, cap_data, cap_data_len) do { \
        opt_params[opt_len++] = 2;           /* type = Capability */ \
        opt_params[opt_len++] = 2 + (cap_data_len); /* parm len */ \
        opt_params[opt_len++] = (code);      /* cap code */ \
        opt_params[opt_len++] = (cap_data_len); /* cap len */ \
        if ((cap_data_len) > 0) { \
            memcpy(opt_params + opt_len, (cap_data), (cap_data_len)); \
            opt_len += (cap_data_len); \
        } \
    } while(0)

    // Capability: 4-byte ASN (RFC 6793)
    {
        uint8_t cap[4];
        uint32_t net_as = htonl(peer->local_as);
        memcpy(cap, &net_as, 4);
        CAP_APPEND(BGP_CAP_4BYTE_ASN, cap, 4);
    }

    // Capability: Multiprotocol IPv4 Unicast
    {
        uint8_t cap[4] = {0, BGP_AFI_IPV4, 0, BGP_SAFI_UNICAST};
        cap[0] = 0; cap[1] = BGP_AFI_IPV4; // AFI big-endian
        CAP_APPEND(BGP_CAP_MPEXT, cap, 4);
    }

    // Capability: Route Refresh
    CAP_APPEND(BGP_CAP_ROUTE_REFRESH, NULL, 0);

    // Compute total message length
    size_t total = BGP_HEADER_LEN + 1 /*version*/ + 2 /*my_as*/ +
                   2 /*hold_time*/ + 4 /*bgp_id*/ +
                   1 /*opt_parm_len*/ + opt_len;

    if (bufsz < total || total > BGP_MAX_MSG_LEN) return -1;

    write_header(buf, bufsz, (uint16_t)total, BGP_MSG_OPEN);

    size_t off = BGP_HEADER_LEN;
    buf[off++] = BGP_VERSION;

    // 2-byte AS: use AS23456 (AS_TRANS) if 4-byte ASN
    uint16_t my_as_2b = (peer->local_as > 65535) ? 23456 :
                         (uint16_t)peer->local_as;
    uint16_t net_as = htons(my_as_2b);
    memcpy(buf + off, &net_as, 2); off += 2;

    uint16_t net_hold = htons(peer->hold_time);
    memcpy(buf + off, &net_hold, 2); off += 2;

    uint32_t net_id = htonl(peer->local_bgp_id);
    memcpy(buf + off, &net_id, 4); off += 4;

    buf[off++] = (uint8_t)opt_len;
    memcpy(buf + off, opt_params, opt_len);

    return (int)total;
}

// ============================================================
// Header parsing
// ============================================================

int bgp_msg_parse_header(const uint8_t *buf, size_t len,
                         uint16_t *out_length, uint8_t *out_type) {
    if (len < BGP_HEADER_LEN) return -1;

    // Verify marker
    if (memcmp(buf, BGP_MARKER, BGP_MARKER_LEN) != 0) {
        fprintf(stderr, "BGP: marker mismatch\n");
        return BGP_ERR_HDR_SYNC;
    }

    uint16_t msg_len;
    memcpy(&msg_len, buf + 16, 2);
    msg_len = ntohs(msg_len);

    if (msg_len < BGP_HEADER_LEN || msg_len > BGP_MAX_MSG_LEN) {
        fprintf(stderr, "BGP: bad message length %u\n", msg_len);
        return BGP_ERR_HDR_LEN;
    }

    uint8_t type = buf[18];
    if (type < 1 || type > 5) {
        fprintf(stderr, "BGP: unknown message type %u\n", type);
        return BGP_ERR_HDR_TYPE;
    }

    *out_length = msg_len;
    *out_type   = type;
    return 0;
}

// ============================================================
// OPEN parsing
// ============================================================

int bgp_msg_parse_open(const uint8_t *buf, size_t len,
                       bgp_open_params_t *out) {
    // buf points to message body AFTER the header
    // (header already consumed/verified)
    if (len < 10) return -1;

    memset(out, 0, sizeof(*out));

    size_t off = 0;
    uint8_t version = buf[off++];
    if (version != 4) {
        fprintf(stderr, "BGP OPEN: unsupported version %u\n", version);
        return BGP_ERR_OPEN_VERSION;
    }

    uint16_t my_as;
    memcpy(&my_as, buf + off, 2); off += 2;
    out->my_as = ntohs(my_as); // may be overwritten by 4-byte ASN cap

    uint16_t hold_time;
    memcpy(&hold_time, buf + off, 2); off += 2;
    out->hold_time = ntohs(hold_time);

    if (out->hold_time == 1 || out->hold_time == 2) {
        // RFC 4271: hold time of 1 or 2 is unacceptable
        return BGP_ERR_OPEN_HOLD;
    }

    uint32_t bgp_id;
    memcpy(&bgp_id, buf + off, 4); off += 4;
    out->bgp_id = ntohl(bgp_id);

    if (out->bgp_id == 0 || out->bgp_id == 0xFFFFFFFF) {
        return BGP_ERR_OPEN_BGP_ID;
    }

    uint8_t opt_parm_len = buf[off++];
    if (off + opt_parm_len > len) return -1;

    // Parse optional parameters
    size_t end = off + opt_parm_len;
    while (off < end) {
        uint8_t parm_type = buf[off++];
        uint8_t parm_len  = buf[off++];
        if (off + parm_len > end) return -1;

        if (parm_type == 2) { // Capabilities
            size_t cap_end = off + parm_len;
            while (off < cap_end) {
                uint8_t cap_code = buf[off++];
                uint8_t cap_len  = buf[off++];
                if (off + cap_len > cap_end) return -1;

                switch (cap_code) {
                case BGP_CAP_4BYTE_ASN:
                    if (cap_len >= 4) {
                        uint32_t as4;
                        memcpy(&as4, buf + off, 4);
                        out->my_as = ntohl(as4);
                        out->can_4byte_asn = 1;
                    }
                    break;
                case BGP_CAP_ROUTE_REFRESH:
                    out->can_route_refresh = 1;
                    break;
                case BGP_CAP_MPEXT:
                    if (cap_len >= 4) {
                        uint16_t afi; uint8_t safi;
                        memcpy(&afi, buf + off, 2);
                        afi  = ntohs(afi);
                        safi = buf[off + 3];
                        if (afi == BGP_AFI_IPV4 && safi == BGP_SAFI_UNICAST)
                            out->can_mp_ipv4_unicast = 1;
                        if (afi == BGP_AFI_IPV6 && safi == BGP_SAFI_UNICAST)
                            out->can_mp_ipv6_unicast = 1;
                    }
                    break;
                case BGP_CAP_GRACEFUL_REST:
                    out->can_graceful_restart = 1;
                    if (cap_len >= 2) {
                        uint16_t gr_flags;
                        memcpy(&gr_flags, buf + off, 2);
                        out->gr_restart_time = ntohs(gr_flags) & 0x0FFF;
                    }
                    break;
                case BGP_CAP_ADD_PATH:
                    out->can_add_path = 1;
                    break;
                case BGP_CAP_EXT_MSG:
                    out->can_ext_msg = 1;
                    break;
                default:
                    break; // unknown cap, ignore
                }
                off += cap_len;
            }
        } else {
            // Unknown optional parameter — if well-known, reject
            // For now, skip
            off += parm_len;
        }
    }

    return 0;
}

// ============================================================
// NLRI parsing helpers
// ============================================================

// Parse a sequence of NLRI from buf[off..off+len]
// Returns number of prefixes parsed, fills out[]
static int parse_nlri(const uint8_t *buf, size_t len,
                      bgp_prefix4_t *out, uint16_t max_out) {
    size_t off = 0;
    int count = 0;

    while (off < len && count < max_out) {
        if (off >= len) break;
        uint8_t prefix_len = buf[off++];
        if (prefix_len > 32) return -1;

        uint8_t byte_len = (prefix_len + 7) / 8; // ceiling division
        if (off + byte_len > len) return -1;

        out[count].length = prefix_len;
        memset(&out[count].prefix, 0, 4);
        memcpy(&out[count].prefix, buf + off, byte_len);
        off += byte_len;
        count++;
    }
    return count;
}

// ============================================================
// UPDATE parsing
// ============================================================

int bgp_msg_parse_update(const uint8_t *buf, size_t len,
                         bgp_prefix4_t **withdrawn, uint16_t *n_withdrawn,
                         bgp_path_attrs_t *attrs,
                         bgp_prefix4_t **nlri, uint16_t *n_nlri) {
    if (len < 4) return -1;
    size_t off = 0;

    // Initialize outputs
    *withdrawn   = NULL; *n_withdrawn = 0;
    *nlri        = NULL; *n_nlri      = 0;
    memset(attrs, 0, sizeof(*attrs));

    // Withdrawn routes length
    uint16_t wd_len;
    memcpy(&wd_len, buf + off, 2); off += 2;
    wd_len = ntohs(wd_len);
    if (off + wd_len > len) return -1;

    if (wd_len > 0) {
        // Estimate max number of withdrawn prefixes:
        // minimum NLRI is 1 byte (length=0, /0 default route)
        uint16_t max_wd = wd_len;
        *withdrawn = calloc(max_wd, sizeof(bgp_prefix4_t));
        if (!*withdrawn) return -1;

        int n = parse_nlri(buf + off, wd_len, *withdrawn, max_wd);
        if (n < 0) { free(*withdrawn); *withdrawn = NULL; return -1; }
        *n_withdrawn = (uint16_t)n;
    }
    off += wd_len;

    // Total path attribute length
    if (off + 2 > len) return 0; // withdrawal-only message
    uint16_t attr_len;
    memcpy(&attr_len, buf + off, 2); off += 2;
    attr_len = ntohs(attr_len);
    if (off + attr_len > len) return -1;

    if (attr_len > 0) {
        int rc = bgp_attr_parse(buf + off, attr_len, attrs);
        if (rc != 0) return rc;
    }
    off += attr_len;

    // NLRI (remaining bytes)
    if (off < len) {
        size_t nlri_len = len - off;
        uint16_t max_nlri = (uint16_t)nlri_len;
        *nlri = calloc(max_nlri, sizeof(bgp_prefix4_t));
        if (!*nlri) return -1;

        int n = parse_nlri(buf + off, nlri_len, *nlri, max_nlri);
        if (n < 0) { free(*nlri); *nlri = NULL; return -1; }
        *n_nlri = (uint16_t)n;
    }

    return 0;
}
```

### 17.4 bgp_attr.c — Path Attribute Parsing

```c
// File: src/bgp_attr.c
// Path attribute parsing and encoding

#include "bgp.h"
#include 
#include 
#include <arpa/inet.h>
#include 

// Free path attributes
void bgp_attr_free(bgp_path_attrs_t *attrs) {
    if (!attrs) return;

    // Free AS_PATH segments
    bgp_as_seg_t *seg = attrs->as_path;
    while (seg) {
        bgp_as_seg_t *next = seg->next;
        free(seg->asns);
        free(seg);
        seg = next;
    }

    free(attrs->communities);
    free(attrs->raw);

    memset(attrs, 0, sizeof(*attrs));
}

// Check if AS_PATH contains a given ASN (loop detection)
int bgp_as_path_contains(const bgp_as_seg_t *path, uint32_t asn) {
    for (const bgp_as_seg_t *seg = path; seg; seg = seg->next) {
        for (uint16_t i = 0; i < seg->count; i++) {
            if (seg->asns[i] == asn) return 1;
        }
    }
    return 0;
}

// Compute AS_PATH length (for best path selection)
// AS_SET counts as 1 regardless of member count
// AS_CONFED_* segments are ignored
int bgp_as_path_length(const bgp_as_seg_t *path) {
    int len = 0;
    for (const bgp_as_seg_t *seg = path; seg; seg = seg->next) {
        if (seg->type == BGP_AS_SEQUENCE) {
            len += seg->count;
        } else if (seg->type == BGP_AS_SET) {
            len += 1;
        }
        // BGP_AS_CONFED_SEQUENCE and BGP_AS_CONFED_SET: ignored per RFC 4271
    }
    return len;
}

// Parse a single AS_PATH segment
static bgp_as_seg_t *parse_as_segment(const uint8_t *buf, size_t *off,
                                      size_t len, int four_byte_asns) {
    if (*off + 2 > len) return NULL;

    uint8_t seg_type = buf[*off];
    uint8_t seg_len  = buf[*off + 1];
    *off += 2;

    int asn_size = four_byte_asns ? 4 : 2;
    if (*off + seg_len * asn_size > len) return NULL;

    bgp_as_seg_t *seg = calloc(1, sizeof(bgp_as_seg_t));
    if (!seg) return NULL;

    seg->type  = seg_type;
    seg->count = seg_len;
    seg->asns  = calloc(seg_len, sizeof(uint32_t));
    if (!seg->asns && seg_len > 0) { free(seg); return NULL; }

    for (uint16_t i = 0; i < seg_len; i++) {
        if (four_byte_asns) {
            uint32_t asn;
            memcpy(&asn, buf + *off, 4);
            seg->asns[i] = ntohl(asn);
            *off += 4;
        } else {
            uint16_t asn;
            memcpy(&asn, buf + *off, 2);
            seg->asns[i] = ntohs(asn);
            *off += 2;
        }
    }

    return seg;
}

// Parse all path attributes from the UPDATE's attribute section
int bgp_attr_parse(const uint8_t *buf, size_t len, bgp_path_attrs_t *attrs) {
    size_t off = 0;
    uint8_t seen_mandatory = 0; // bitmask: bit0=ORIGIN, bit1=AS_PATH, bit2=NEXT_HOP

    // We need to know if 4-byte ASN mode is active — assume yes for now.
    // In a real implementation, this is derived from capability negotiation.
    int four_byte_asns = 1;

    while (off < len) {
        if (off + 2 > len) return BGP_ERR_UPD_ATTR_LIST;

        uint8_t flags    = buf[off++];
        uint8_t type     = buf[off++];
        uint16_t attr_len;

        if (flags & BGP_ATTR_FLAG_EXT_LEN) {
            if (off + 2 > len) return BGP_ERR_UPD_ATTR_LEN;
            memcpy(&attr_len, buf + off, 2);
            attr_len = ntohs(attr_len);
            off += 2;
        } else {
            if (off + 1 > len) return BGP_ERR_UPD_ATTR_LEN;
            attr_len = buf[off++];
        }

        if (off + attr_len > len) return BGP_ERR_UPD_ATTR_LEN;

        const uint8_t *val = buf + off;
        off += attr_len;

        switch (type) {
        case BGP_ATTR_ORIGIN:
            if (attr_len != 1) return BGP_ERR_UPD_ATTR_LEN;
            // Validate flags: must be well-known mandatory (0x40)
            if ((flags & (BGP_ATTR_FLAG_OPTIONAL | BGP_ATTR_FLAG_TRANSITIVE))
                    != BGP_ATTR_FLAG_TRANSITIVE)
                return BGP_ERR_UPD_ATTR_FLAGS;
            if (val[0] > 2) return BGP_ERR_UPD_ORIGIN;
            attrs->origin = val[0];
            seen_mandatory |= 0x01;
            break;

        case BGP_ATTR_AS_PATH: {
            if (flags & BGP_ATTR_FLAG_OPTIONAL) return BGP_ERR_UPD_ATTR_FLAGS;
            // Parse segments
            size_t seg_off = 0;
            bgp_as_seg_t **tail = &attrs->as_path;
            while (seg_off < attr_len) {
                bgp_as_seg_t *seg = parse_as_segment(val, &seg_off, attr_len,
                                                      four_byte_asns);
                if (!seg) return BGP_ERR_UPD_AS_PATH;
                *tail = seg;
                tail = &seg->next;
            }
            seen_mandatory |= 0x02;
            break;
        }

        case BGP_ATTR_NEXT_HOP:
            if (attr_len != 4) return BGP_ERR_UPD_ATTR_LEN;
            if (flags & BGP_ATTR_FLAG_OPTIONAL) return BGP_ERR_UPD_ATTR_FLAGS;
            memcpy(&attrs->next_hop, val, 4);
            // Validate: cannot be multicast or 0.0.0.0 or loopback
            {
                uint32_t nh = ntohl(attrs->next_hop.s_addr);
                if ((nh >> 28) == 0xE ||  // 224.0.0.0/4 multicast
                    nh == 0 ||             // 0.0.0.0
                    (nh >> 24) == 127)     // 127.0.0.0/8 loopback
                    return BGP_ERR_UPD_NEXT_HOP;
            }
            seen_mandatory |= 0x04;
            break;

        case BGP_ATTR_MED:
            if (attr_len != 4) return BGP_ERR_UPD_ATTR_LEN;
            if (!(flags & BGP_ATTR_FLAG_OPTIONAL)) return BGP_ERR_UPD_ATTR_FLAGS;
            {
                uint32_t med;
                memcpy(&med, val, 4);
                attrs->med = ntohl(med);
                attrs->med_present = 1;
            }
            break;

        case BGP_ATTR_LOCAL_PREF:
            if (attr_len != 4) return BGP_ERR_UPD_ATTR_LEN;
            {
                uint32_t lp;
                memcpy(&lp, val, 4);
                attrs->local_pref = ntohl(lp);
                attrs->local_pref_present = 1;
            }
            break;

        case BGP_ATTR_ATOMIC_AGG:
            if (attr_len != 0) return BGP_ERR_UPD_ATTR_LEN;
            attrs->atomic_aggregate = 1;
            break;

        case BGP_ATTR_COMMUNITY: {
            if (attr_len % 4 != 0) return BGP_ERR_UPD_OPT_ATTR;
            uint16_t n = attr_len / 4;
            attrs->communities = calloc(n, sizeof(uint32_t));
            if (!attrs->communities && n > 0) return -1;
            for (uint16_t i = 0; i < n; i++) {
                uint32_t comm;
                memcpy(&comm, val + i * 4, 4);
                attrs->communities[i] = ntohl(comm);
            }
            attrs->community_count = n;
            break;
        }

        case BGP_ATTR_ORIGINATOR_ID:
            if (attr_len != 4) return BGP_ERR_UPD_ATTR_LEN;
            {
                uint32_t oid;
                memcpy(&oid, val, 4);
                attrs->originator_id = ntohl(oid);
                attrs->originator_id_present = 1;
            }
            break;

        default:
            // Unknown attribute
            if (!(flags & BGP_ATTR_FLAG_OPTIONAL)) {
                // Well-known attribute not recognized
                return BGP_ERR_UPD_WELL_KNOWN;
            }
            if (flags & BGP_ATTR_FLAG_TRANSITIVE) {
                // Optional transitive: forward with Partial bit set
                // Store in raw for forwarding
                // (simplified: we just skip for now)
            }
            // Optional non-transitive: silently ignore
            break;
        }
    }

    // Check mandatory attributes present for NLRI-carrying UPDATE
    // (If no NLRI, some may be absent — checked by caller)
    // Here we only validate that what's present is consistent

    return 0;
}
```

### 17.5 bgp_fsm.c — Finite State Machine

```c
// File: src/bgp_fsm.c
// BGP Finite State Machine implementation per RFC 4271 Section 8

#include "bgp.h"
#include 
#include 
#include 
#include 
#include 
#include <arpa/inet.h>

static const char *state_names[] = {
    "Idle", "Connect", "Active", "OpenSent", "OpenConfirm", "Established"
};

static const char *event_names[] = {
    "", "ManualStart", "ManualStop", "AutoStart", "", "", "", "", "",
    "ConnectRetryExp", "HoldTimerExp", "KeepaliveTimerExp", "", "", "", "",
    "TcpCrAcked", "TcpConnValid", "TcpConnFails",
    "BgpOpen", "BgpOpenDelay", "BgpHdrErr", "BgpOpenErr", "", "",
    "NotifMsg", "KeepaliveMsg", "UpdateMsg", "UpdateErr"
};

const char *bgp_state_name(bgp_state_t s) {
    if (s > BGP_STATE_ESTABLISHED) return "Unknown";
    return state_names[s];
}

const char *bgp_event_name(bgp_event_t e) {
    if (e >= 29) return "Unknown";
    return event_names[e];
}

// ============================================================
// Timer management
// ============================================================

static void timer_reset(time_t *t, uint32_t seconds) {
    *t = time(NULL) + seconds;
}

static void timer_stop(time_t *t) {
    *t = 0;
}

static int timer_expired(time_t *t) {
    return (*t != 0 && time(NULL) >= *t);
}

// ============================================================
// Session management actions
// ============================================================

// Send a NOTIFICATION and close the session
static void send_notification_and_close(bgp_peer_t *peer,
                                        uint8_t code, uint8_t subcode) {
    uint8_t buf[BGP_HEADER_LEN + 2];
    int len = bgp_msg_build_notification(buf, sizeof(buf), code, subcode, NULL, 0);
    if (len > 0) {
        bgp_io_send(peer, buf, (size_t)len);
    }
    bgp_io_close(peer);
}

// Send OPEN to peer
static int send_open(bgp_peer_t *peer) {
    uint8_t buf[BGP_MAX_MSG_LEN];
    int len = bgp_msg_build_open(buf, sizeof(buf), peer);
    if (len < 0) return -1;
    return bgp_io_send(peer, buf, (size_t)len);
}

// Send KEEPALIVE to peer
static int send_keepalive(bgp_peer_t *peer) {
    uint8_t buf[BGP_HEADER_LEN];
    int len = bgp_msg_build_keepalive(buf, sizeof(buf));
    if (len < 0) return -1;
    peer->msgs_out++;
    return bgp_io_send(peer, buf, (size_t)len);
}

// Transition to a new state
static void transition(bgp_peer_t *peer, bgp_state_t new_state) {
    if (peer->state == new_state) return;
    fprintf(stderr, "BGP [%s]: %s -> %s\n",
            inet_ntoa(peer->peer_addr),
            bgp_state_name(peer->state),
            bgp_state_name(new_state));
    peer->state = new_state;
}

// ============================================================
// Validate received OPEN against our configuration
// ============================================================
static int validate_open(bgp_peer_t *peer, const bgp_open_params_t *remote) {
    // Check AS number if configured
    if (peer->peer_as != 0 && remote->my_as != peer->peer_as) {
        fprintf(stderr, "BGP OPEN: expected AS %u, got AS %u\n",
                peer->peer_as, remote->my_as);
        return BGP_ERR_OPEN_AS;
    }

    // Check BGP ID: must not be our own
    if (remote->bgp_id == peer->local_bgp_id) {
        return BGP_ERR_OPEN_BGP_ID;
    }

    // Check hold time
    if (remote->hold_time == 1 || remote->hold_time == 2) {
        return BGP_ERR_OPEN_HOLD;
    }

    return 0;
}

// ============================================================
// Main FSM function
// ============================================================
void bgp_fsm_event(bgp_peer_t *peer, bgp_event_t event) {
    fprintf(stderr, "BGP [%s] state=%s event=%s\n",
            inet_ntoa(peer->peer_addr),
            bgp_state_name(peer->state),
            bgp_event_name(event));

    switch (peer->state) {

    // ----------------------------------------------------------
    case BGP_STATE_IDLE:
        switch (event) {
        case BGP_EVENT_MANUAL_START:
        case BGP_EVENT_AUTO_START:
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            if (!peer->is_passive) {
                bgp_io_connect(peer);
            }
            transition(peer, BGP_STATE_CONNECT);
            break;
        default:
            break; // Ignore all other events in IDLE
        }
        break;

    // ----------------------------------------------------------
    case BGP_STATE_CONNECT:
        switch (event) {
        case BGP_EVENT_TCP_CR_ACKED:
        case BGP_EVENT_TCP_CONN_VALID:
            // TCP succeeded: send OPEN, start hold timer (large initial value)
            timer_stop(&peer->connect_retry_timer);
            send_open(peer);
            timer_reset(&peer->hold_timer, 240); // Large initial hold timer (4min)
            transition(peer, BGP_STATE_OPENSENT);
            break;

        case BGP_EVENT_TCP_CONN_FAILS:
            // TCP failed: back to ACTIVE
            bgp_io_close(peer);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_ACTIVE);
            break;

        case BGP_EVENT_CONNECT_RETRY_EXP:
            // Retry the connection
            bgp_io_close(peer);
            bgp_io_connect(peer);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            break;

        case BGP_EVENT_MANUAL_STOP:
            bgp_io_close(peer);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        default:
            break;
        }
        break;

    // ----------------------------------------------------------
    case BGP_STATE_ACTIVE:
        switch (event) {
        case BGP_EVENT_TCP_CR_ACKED:
        case BGP_EVENT_TCP_CONN_VALID:
            timer_stop(&peer->connect_retry_timer);
            send_open(peer);
            timer_reset(&peer->hold_timer, 240);
            transition(peer, BGP_STATE_OPENSENT);
            break;

        case BGP_EVENT_CONNECT_RETRY_EXP:
            bgp_io_connect(peer);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_CONNECT);
            break;

        case BGP_EVENT_MANUAL_STOP:
            bgp_io_close(peer);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        default:
            break;
        }
        break;

    // ----------------------------------------------------------
    case BGP_STATE_OPENSENT:
        switch (event) {
        case BGP_EVENT_BGP_OPEN: {
            // Received OPEN from peer — validate and respond
            bgp_open_params_t *remote = &peer->remote_params;
            int rc = validate_open(peer, remote);
            if (rc != 0) {
                send_notification_and_close(peer, BGP_ERR_OPEN, (uint8_t)rc);
                timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
                transition(peer, BGP_STATE_IDLE);
                break;
            }

            // Negotiate hold time: min of local and remote
            uint16_t hold = (peer->hold_time < remote->hold_time)
                            ? peer->hold_time : remote->hold_time;
            peer->negotiated_hold_time   = hold;
            peer->negotiated_keepalive   = hold / 3;

            // Store peer info
            peer->peer_as = remote->my_as;

            // Send KEEPALIVE (confirms OPEN acceptance)
            send_keepalive(peer);

            // Reset timers with negotiated values
            if (hold > 0) {
                timer_reset(&peer->hold_timer, hold);
                timer_reset(&peer->keepalive_timer, hold / 3);
            } else {
                timer_stop(&peer->hold_timer);
                timer_stop(&peer->keepalive_timer);
            }

            transition(peer, BGP_STATE_OPENCONFIRM);
            break;
        }

        case BGP_EVENT_BGP_HDR_ERR:
            send_notification_and_close(peer, BGP_ERR_HEADER, 0);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_BGP_OPEN_ERR:
            send_notification_and_close(peer, BGP_ERR_OPEN, 0);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_HOLD_TIMER_EXP:
            send_notification_and_close(peer, BGP_ERR_HOLD_TIMER, 0);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_TCP_CONN_FAILS:
            bgp_io_close(peer);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_ACTIVE);
            break;

        case BGP_EVENT_MANUAL_STOP:
            send_notification_and_close(peer, BGP_ERR_CEASE,
                                        BGP_CEASE_ADMIN_SHUT);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        default:
            // Any other message in OPENSENT is an FSM error
            send_notification_and_close(peer, BGP_ERR_FSM, 1);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;
        }
        break;

    // ----------------------------------------------------------
    case BGP_STATE_OPENCONFIRM:
        switch (event) {
        case BGP_EVENT_KEEPALIVE_MSG:
            // Session fully established
            timer_reset(&peer->hold_timer, peer->negotiated_hold_time);
            peer->session_established_at = time(NULL);
            transition(peer, BGP_STATE_ESTABLISHED);
            // Here: trigger initial route advertisement (full table send)
            fprintf(stderr, "BGP [%s]: Session ESTABLISHED AS%u\n",
                    inet_ntoa(peer->peer_addr), peer->peer_as);
            break;

        case BGP_EVENT_KEEPALIVE_TIMER_EXP:
            send_keepalive(peer);
            timer_reset(&peer->keepalive_timer, peer->negotiated_keepalive);
            break;

        case BGP_EVENT_NOTIF_MSG:
        case BGP_EVENT_TCP_CONN_FAILS:
            bgp_io_close(peer);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_HOLD_TIMER_EXP:
            send_notification_and_close(peer, BGP_ERR_HOLD_TIMER, 0);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_MANUAL_STOP:
            send_notification_and_close(peer, BGP_ERR_CEASE,
                                        BGP_CEASE_ADMIN_SHUT);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        default:
            send_notification_and_close(peer, BGP_ERR_FSM, 2);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;
        }
        break;

    // ----------------------------------------------------------
    case BGP_STATE_ESTABLISHED:
        switch (event) {
        case BGP_EVENT_KEEPALIVE_TIMER_EXP:
            send_keepalive(peer);
            if (peer->negotiated_keepalive > 0)
                timer_reset(&peer->keepalive_timer, peer->negotiated_keepalive);
            break;

        case BGP_EVENT_HOLD_TIMER_EXP:
            send_notification_and_close(peer, BGP_ERR_HOLD_TIMER, 0);
            bgp_rib_free(&peer->adj_rib_in);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_KEEPALIVE_MSG:
            if (peer->negotiated_hold_time > 0)
                timer_reset(&peer->hold_timer, peer->negotiated_hold_time);
            peer->msgs_in++;
            break;

        case BGP_EVENT_UPDATE_MSG:
            // UPDATE received — reset hold timer, process routes
            if (peer->negotiated_hold_time > 0)
                timer_reset(&peer->hold_timer, peer->negotiated_hold_time);
            peer->updates_in++;
            // Actual route processing done by the event dispatcher
            break;

        case BGP_EVENT_UPDATE_ERR:
            send_notification_and_close(peer, BGP_ERR_UPDATE, 0);
            bgp_rib_free(&peer->adj_rib_in);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_NOTIF_MSG:
        case BGP_EVENT_TCP_CONN_FAILS:
            bgp_io_close(peer);
            bgp_rib_free(&peer->adj_rib_in);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;

        case BGP_EVENT_MANUAL_STOP:
            send_notification_and_close(peer, BGP_ERR_CEASE,
                                        BGP_CEASE_ADMIN_SHUT);
            bgp_rib_free(&peer->adj_rib_in);
            timer_stop(&peer->connect_retry_timer);
            transition(peer, BGP_STATE_IDLE);
            break;

        default:
            send_notification_and_close(peer, BGP_ERR_FSM, 3);
            bgp_rib_free(&peer->adj_rib_in);
            timer_reset(&peer->connect_retry_timer, BGP_CONNECT_RETRY_TIME);
            transition(peer, BGP_STATE_IDLE);
            break;
        }
        break;
    }
}
```

### 17.6 bgp_rib.c — Route Information Base

```c
// File: src/bgp_rib.c
// RIB management and BGP Decision Process

#include "bgp.h"
#include 
#include 
#include <arpa/inet.h>

// Compare two IPv4 prefixes
static int prefix_equal(const bgp_prefix4_t *a, const bgp_prefix4_t *b) {
    return (a->length == b->length &&
            a->prefix.s_addr == b->prefix.s_addr);
}

// Lookup a prefix in the RIB
bgp_route_t *bgp_rib_lookup(bgp_route_t *rib, const bgp_prefix4_t *prefix) {
    for (bgp_route_t *r = rib; r; r = r->next) {
        if (prefix_equal(&r->prefix, prefix)) return r;
    }
    return NULL;
}

// Add or replace a route in the RIB
void bgp_rib_add(bgp_route_t **rib, bgp_route_t *route) {
    // Remove existing route for this prefix first
    bgp_rib_remove(rib, &route->prefix);
    // Prepend new route
    route->next = *rib;
    *rib = route;
}

// Remove a route from the RIB by prefix
void bgp_rib_remove(bgp_route_t **rib, const bgp_prefix4_t *prefix) {
    bgp_route_t **prev = rib;
    bgp_route_t  *cur  = *rib;
    while (cur) {
        if (prefix_equal(&cur->prefix, prefix)) {
            *prev = cur->next;
            bgp_attr_free(&cur->attrs);
            free(cur);
            return;
        }
        prev = &cur->next;
        cur  = cur->next;
    }
}

// Free entire RIB
void bgp_rib_free(bgp_route_t **rib) {
    bgp_route_t *cur = *rib;
    while (cur) {
        bgp_route_t *next = cur->next;
        bgp_attr_free(&cur->attrs);
        free(cur);
        cur = next;
    }
    *rib = NULL;
}

// ============================================================
// BGP Decision Process (RFC 4271 Section 9.1)
// Compares two routes, returns:
//   <0 if a is better than b
//    0 if equal (use tiebreakers)
//   >0 if b is better than a
// ============================================================
static int compare_routes(const bgp_route_t *a, const bgp_route_t *b,
                           int a_is_ibgp, int b_is_ibgp) {
    // Step 1: Higher LOCAL_PREF wins
    {
        uint32_t lp_a = a->attrs.local_pref_present ? a->attrs.local_pref : 100;
        uint32_t lp_b = b->attrs.local_pref_present ? b->attrs.local_pref : 100;
        if (lp_a != lp_b) return (lp_a > lp_b) ? -1 : 1;
    }

    // Step 2: Locally originated (no AS_PATH, or AS_PATH length = 0) preferred
    {
        int len_a = bgp_as_path_length(a->attrs.as_path);
        int len_b = bgp_as_path_length(b->attrs.as_path);
        // (Locally originated: length 0, handled by checking origin = locally injected)
        // Simplified: shorter AS_PATH wins (step 3)
        if (len_a != len_b) return (len_a < len_b) ? -1 : 1;
    }

    // Step 4: Lower ORIGIN wins (IGP=0 < EGP=1 < INCOMPLETE=2)
    if (a->attrs.origin != b->attrs.origin) {
        return (a->attrs.origin < b->attrs.origin) ? -1 : 1;
    }

    // Step 5: Lower MED wins (compare only if from same neighboring AS)
    // Simplified: compare if both have MED
    if (a->attrs.med_present && b->attrs.med_present) {
        if (a->attrs.med != b->attrs.med) {
            return (a->attrs.med < b->attrs.med) ? -1 : 1;
        }
    }

    // Step 6: eBGP preferred over iBGP
    if (a_is_ibgp != b_is_ibgp) {
        return a_is_ibgp ? 1 : -1; // eBGP wins
    }

    // Step 7: Shortest IGP metric to next-hop (not implemented here — needs FIB)

    // Step 9: Lowest BGP Router ID (using next-hop IP as proxy)
    {
        uint32_t nh_a = ntohl(a->attrs.next_hop.s_addr);
        uint32_t nh_b = ntohl(b->attrs.next_hop.s_addr);
        if (nh_a != nh_b) return (nh_a < nh_b) ? -1 : 1;
    }

    return 0;
}

// Run decision process over all peers for a given prefix
// Returns the best route, or NULL if no route exists
bgp_route_t *bgp_decision_process(bgp_peer_t **peers, int n_peers,
                                   const bgp_prefix4_t *prefix) {
    bgp_route_t *best = NULL;
    int best_is_ibgp  = 0;

    for (int i = 0; i < n_peers; i++) {
        bgp_peer_t *peer = peers[i];
        if (peer->state != BGP_STATE_ESTABLISHED) continue;

        bgp_route_t *route = bgp_rib_lookup(peer->adj_rib_in, prefix);
        if (!route) continue;

        int is_ibgp = (peer->local_as == peer->peer_as);

        if (!best) {
            best = route;
            best_is_ibgp = is_ibgp;
            continue;
        }

        int cmp = compare_routes(route, best, is_ibgp, best_is_ibgp);
        if (cmp < 0) {
            best = route;
            best_is_ibgp = is_ibgp;
        }
    }

    return best;
}
```

### 17.7 Makefile

```makefile
# File: Makefile
CC      = gcc
CFLAGS  = -Wall -Wextra -Wshadow -O2 -g -std=c11 -D_POSIX_C_SOURCE=200809L
LDFLAGS =

SRC = src/bgp_fsm.c src/bgp_msg.c src/bgp_attr.c src/bgp_rib.c src/bgp_io.c
OBJ = $(SRC:.c=.o)

.PHONY: all clean test

all: bgpd libbgp.a

bgpd: $(OBJ) src/main.o
	$(CC) $(CFLAGS) -o $@ $^ $(LDFLAGS)

libbgp.a: $(OBJ)
	ar rcs $@ $^

# Tests
test_msg_parse: libbgp.a tests/test_msg_parse.c
	$(CC) $(CFLAGS) -o $@ tests/test_msg_parse.c -L. -lbgp

test_fsm: libbgp.a tests/test_fsm.c
	$(CC) $(CFLAGS) -o $@ tests/test_fsm.c -L. -lbgp

test: test_msg_parse test_fsm
	./test_msg_parse
	./test_fsm

clean:
	rm -f $(OBJ) src/main.o bgpd libbgp.a test_msg_parse test_fsm
```

---

## 18. Rust Implementation

A safe, idiomatic Rust implementation of the BGP protocol parser and FSM with async I/O.

### 18.1 Project Structure and Cargo.toml

```toml
# File: bgp_rs/Cargo.toml
[package]
name    = "bgp_rs"
version = "0.1.0"
edition = "2021"

[[bin]]
name = "bgpd"
path = "src/main.rs"

[lib]
name = "bgp_rs"
path = "src/lib.rs"

[dependencies]
tokio         = { version = "1", features = ["full"] }
bytes         = "1"
thiserror     = "1"
tracing       = "1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }

[dev-dependencies]
tokio-test    = "0.4"
proptest      = "1"         # property-based testing

[profile.release]
lto           = true
codegen-units = 1
panic         = "abort"
```

### 18.2 src/lib.rs — Module Organization

```rust
// File: src/lib.rs
pub mod error;
pub mod types;
pub mod message;
pub mod attr;
pub mod fsm;
pub mod rib;
pub mod peer;
pub mod io;

pub use error::BgpError;
pub use types::*;
pub use message::*;
```

### 18.3 src/error.rs

```rust
// File: src/error.rs
use thiserror::Error;

#[derive(Debug, Error)]
pub enum BgpError {
    // Protocol errors (map to NOTIFICATION codes)
    #[error("Marker synchronization error")]
    MarkerError,
    
    #[error("Message length error: got {got}, expected range {min}-{max}")]
    BadMessageLength { got: u16, min: u16, max: u16 },
    
    #[error("Unknown message type: {0}")]
    UnknownMessageType(u8),
    
    #[error("OPEN error: {0}")]
    OpenError(String),
    
    #[error("UPDATE error: {0}")]
    UpdateError(String),
    
    #[error("Attribute error: {0}")]
    AttributeError(String),
    
    #[error("Hold timer expired")]
    HoldTimerExpired,
    
    #[error("FSM error: unexpected event {event} in state {state}")]
    FsmError { event: String, state: String },
    
    #[error("Peer sent CEASE: {0}")]
    Cease(String),
    
    // Implementation errors
    #[error("Buffer too short: need {need}, have {have}")]
    BufferTooShort { need: usize, have: usize },
    
    #[error("Invalid prefix length: {0}")]
    InvalidPrefixLength(u8),
    
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
    
    #[error("NLRI encoding error: {0}")]
    NlriError(String),
    
    #[error("Max prefixes exceeded: limit {limit}")]
    MaxPrefixesExceeded { limit: u32 },
}

// NOTIFICATION error codes
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum NotificationCode {
    MessageHeaderError = 1,
    OpenMessageError   = 2,
    UpdateMessageError = 3,
    HoldTimerExpired   = 4,
    FsmError           = 5,
    Cease              = 6,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum CeaseSubcode {
    MaxPrefixes        = 1,
    AdminShutdown      = 2,
    PeerDeconfigured   = 3,
    AdminReset         = 4,
    ConnectionRejected = 5,
    OtherConfigChange  = 6,
    CollisionResolution= 7,
    OutOfResources     = 8,
}
```

### 18.4 src/types.rs

```rust
// File: src/types.rs
use std::net::{Ipv4Addr, Ipv6Addr};
use std::fmt;

// ============================================================
// BGP constants
// ============================================================
pub const BGP_PORT:           u16 = 179;
pub const BGP_MARKER_LEN:     usize = 16;
pub const BGP_HEADER_LEN:     usize = 19;
pub const BGP_MAX_MSG_LEN:    usize = 4096;
pub const BGP_EXT_MAX_MSG_LEN:usize = 65535;
pub const BGP_VERSION:        u8 = 4;
pub const BGP_AS_TRANS:       u32 = 23456; // placeholder for 4-byte ASN in 2-byte field

pub const HOLD_TIME_DEFAULT:   u16 = 90;
pub const KEEPALIVE_DEFAULT:   u16 = 30;
pub const CONNECT_RETRY_TIME:  u64 = 120;

// ============================================================
// Message types
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum MessageType {
    Open          = 1,
    Update        = 2,
    Notification  = 3,
    Keepalive     = 4,
    RouteRefresh  = 5,
}

impl TryFrom for MessageType {
    type Error = crate::BgpError;
    fn try_from(v: u8) -> Result {
        match v {
            1 => Ok(Self::Open),
            2 => Ok(Self::Update),
            3 => Ok(Self::Notification),
            4 => Ok(Self::Keepalive),
            5 => Ok(Self::RouteRefresh),
            _ => Err(crate::BgpError::UnknownMessageType(v)),
        }
    }
}

// ============================================================
// Path attribute type codes
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
#[repr(u8)]
pub enum AttrTypeCode {
    Origin        = 1,
    AsPath        = 2,
    NextHop       = 3,
    Med           = 4,
    LocalPref     = 5,
    AtomicAgg     = 6,
    Aggregator    = 7,
    Community     = 8,
    OriginatorId  = 9,
    ClusterList   = 10,
    MpReachNlri   = 14,
    MpUnreachNlri = 15,
    ExtCommunity  = 16,
    As4Path       = 17,
    LargeCommunity = 32,
}

// ============================================================
// ORIGIN values
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq, PartialOrd, Ord)]
#[repr(u8)]
pub enum Origin {
    Igp        = 0,
    Egp        = 1,
    Incomplete = 2,
}

impl TryFrom for Origin {
    type Error = crate::BgpError;
    fn try_from(v: u8) -> Result {
        match v {
            0 => Ok(Self::Igp),
            1 => Ok(Self::Egp),
            2 => Ok(Self::Incomplete),
            _ => Err(crate::BgpError::AttributeError(
                    format!("invalid ORIGIN value: {}", v))),
        }
    }
}

// ============================================================
// AS_PATH segment
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
#[repr(u8)]
pub enum AsPathSegmentType {
    AsSet           = 1,
    AsSequence      = 2,
    AsConfedSequence = 3,
    AsConfedSet      = 4,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AsPathSegment {
    pub seg_type: AsPathSegmentType,
    pub asns:     Vec,
}

impl AsPathSegment {
    pub fn new_sequence(asns: Vec) -> Self {
        Self { seg_type: AsPathSegmentType::AsSequence, asns }
    }
    pub fn new_set(asns: Vec) -> Self {
        Self { seg_type: AsPathSegmentType::AsSet, asns }
    }
}

// ============================================================
// BGP prefix types
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Prefix4 {
    pub addr:   Ipv4Addr,
    pub length: u8,
}

impl Prefix4 {
    pub fn new(addr: Ipv4Addr, length: u8) -> Result {
        if length > 32 {
            return Err(crate::BgpError::InvalidPrefixLength(length));
        }
        // Mask the address to remove host bits
        let masked = if length == 0 {
            0u32
        } else {
            let mask = !((1u32 << (32 - length)) - 1);
            u32::from(addr) & mask
        };
        Ok(Self { addr: Ipv4Addr::from(masked), length })
    }
    
    /// Number of bytes needed to encode the prefix
    pub fn byte_len(self) -> usize {
        (self.length as usize + 7) / 8
    }
    
    /// Encode as BGP NLRI: [length_byte] [prefix_bytes]
    pub fn encode(self, buf: &mut Vec) {
        buf.push(self.length);
        let addr_bytes = self.addr.octets();
        buf.extend_from_slice(&addr_bytes[..self.byte_len()]);
    }
    
    /// Decode from BGP NLRI bytes (starting at offset)
    pub fn decode(data: &[u8], offset: &mut usize) -> Result {
        if *offset >= data.len() {
            return Err(crate::BgpError::BufferTooShort { need: 1, have: 0 });
        }
        let length = data[*offset];
        *offset += 1;
        if length > 32 {
            return Err(crate::BgpError::InvalidPrefixLength(length));
        }
        let byte_len = (length as usize + 7) / 8;
        if *offset + byte_len > data.len() {
            return Err(crate::BgpError::BufferTooShort {
                need: byte_len, have: data.len() - *offset
            });
        }
        let mut addr = [0u8; 4];
        addr[..byte_len].copy_from_slice(&data[*offset..*offset + byte_len]);
        *offset += byte_len;
        Self::new(Ipv4Addr::from(addr), length)
    }
}

impl fmt::Display for Prefix4 {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}/{}", self.addr, self.length)
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Prefix6 {
    pub addr:   Ipv6Addr,
    pub length: u8,
}

impl Prefix6 {
    pub fn new(addr: Ipv6Addr, length: u8) -> Result {
        if length > 128 {
            return Err(crate::BgpError::InvalidPrefixLength(length));
        }
        Ok(Self { addr, length })
    }
    
    pub fn byte_len(self) -> usize {
        (self.length as usize + 7) / 8
    }
    
    pub fn encode(self, buf: &mut Vec) {
        buf.push(self.length);
        let addr_bytes = self.addr.octets();
        buf.extend_from_slice(&addr_bytes[..self.byte_len()]);
    }
    
    pub fn decode(data: &[u8], offset: &mut usize) -> Result {
        if *offset >= data.len() {
            return Err(crate::BgpError::BufferTooShort { need: 1, have: 0 });
        }
        let length = data[*offset];
        *offset += 1;
        if length > 128 {
            return Err(crate::BgpError::InvalidPrefixLength(length));
        }
        let byte_len = (length as usize + 7) / 8;
        if *offset + byte_len > data.len() {
            return Err(crate::BgpError::BufferTooShort {
                need: byte_len, have: data.len() - *offset
            });
        }
        let mut addr = [0u8; 16];
        addr[..byte_len].copy_from_slice(&data[*offset..*offset + byte_len]);
        *offset += byte_len;
        Self::new(Ipv6Addr::from(addr), length)
    }
}

// ============================================================
// BGP Communities
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct Community(pub u32);

impl Community {
    pub fn new(asn: u16, value: u16) -> Self {
        Self(((asn as u32) << 16) | value as u32)
    }
    pub fn asn(self) -> u16 { (self.0 >> 16) as u16 }
    pub fn value(self) -> u16 { self.0 as u16 }

    // Well-known communities (RFC 1997)
    pub const NO_EXPORT:        Self = Self(0xFFFFFF01);
    pub const NO_ADVERTISE:     Self = Self(0xFFFFFF02);
    pub const NO_EXPORT_SUBCONF:Self = Self(0xFFFFFF03);
    pub const BLACKHOLE:        Self = Self(0xFFFF029A); // 65535:666 = RFC 7999
    pub const GRACEFUL_SHUTDOWN:Self = Self(0xFFFF0000);
}

impl fmt::Display for Community {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}:{}", self.asn(), self.value())
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash)]
pub struct LargeCommunity {
    pub global_admin: u32,
    pub local_data1:  u32,
    pub local_data2:  u32,
}

impl fmt::Display for LargeCommunity {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        write!(f, "{}:{}:{}", self.global_admin, self.local_data1, self.local_data2)
    }
}

// ============================================================
// FSM State and Events
// ============================================================
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum FsmState {
    Idle,
    Connect,
    Active,
    OpenSent,
    OpenConfirm,
    Established,
}

impl fmt::Display for FsmState {
    fn fmt(&self, f: &mut fmt::Formatter) -> fmt::Result {
        match self {
            Self::Idle        => write!(f, "Idle"),
            Self::Connect     => write!(f, "Connect"),
            Self::Active      => write!(f, "Active"),
            Self::OpenSent    => write!(f, "OpenSent"),
            Self::OpenConfirm => write!(f, "OpenConfirm"),
            Self::Established => write!(f, "Established"),
        }
    }
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub enum FsmEvent {
    ManualStart,
    ManualStop,
    AutomaticStart,
    ConnectRetryExpired,
    HoldTimerExpired,
    KeepaliveTimerExpired,
    TcpConnectionAcked,
    TcpConnectionValid,
    TcpConnectionFailed,
    BgpOpenReceived(OpenParams),
    BgpHeaderError(u8),       // error subcode
    BgpOpenError(u8),
    NotificationReceived { code: u8, subcode: u8 },
    KeepaliveReceived,
    UpdateReceived,
    UpdateError(u8),
}

// ============================================================
// Capability types
// ============================================================
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct OpenParams {
    pub my_as:                u32,
    pub hold_time:            u16,
    pub bgp_id:               u32,
    pub can_4byte_asn:        bool,
    pub can_route_refresh:    bool,
    pub can_mp_ipv4_unicast:  bool,
    pub can_mp_ipv6_unicast:  bool,
    pub can_graceful_restart: bool,
    pub gr_restart_time:      u16,
    pub can_add_path:         bool,
    pub can_ext_msg:          bool,
}
```

### 18.5 src/message.rs — Complete Message Parser

```rust
// File: src/message.rs
// BGP message serialization and deserialization

use crate::error::BgpError;
use crate::types::*;
use crate::attr::PathAttributes;

// All-0xFF marker
pub const BGP_MARKER: [u8; BGP_MARKER_LEN] = [0xFF; BGP_MARKER_LEN];

// ============================================================
// BGP message variants
// ============================================================
#[derive(Debug, Clone)]
pub enum BgpMessage {
    Open(OpenMessage),
    Update(UpdateMessage),
    Notification(NotificationMessage),
    Keepalive,
    RouteRefresh(RouteRefreshMessage),
}

#[derive(Debug, Clone)]
pub struct OpenMessage {
    pub my_as:      u32,
    pub hold_time:  u16,
    pub bgp_id:     u32,
    pub params:     OpenParams,
}

#[derive(Debug, Clone)]
pub struct UpdateMessage {
    pub withdrawn:  Vec,
    pub attrs:      Option,
    pub nlri:       Vec,
}

#[derive(Debug, Clone)]
pub struct NotificationMessage {
    pub error_code:    u8,
    pub error_subcode: u8,
    pub data:          Vec,
}

#[derive(Debug, Clone)]
pub struct RouteRefreshMessage {
    pub afi:  u16,
    pub safi: u8,
}

// ============================================================
// Message parsing
// ============================================================
impl BgpMessage {
    /// Parse a complete BGP message from a byte slice.
    /// The slice must contain exactly one complete message.
    pub fn parse(data: &[u8]) -> Result {
        if data.len() < BGP_HEADER_LEN {
            return Err(BgpError::BufferTooShort {
                need: BGP_HEADER_LEN, have: data.len()
            });
        }

        // Verify marker
        if data[..BGP_MARKER_LEN] != BGP_MARKER {
            return Err(BgpError::MarkerError);
        }

        // Parse length
        let length = u16::from_be_bytes([data[16], data[17]]) as usize;
        if length < BGP_HEADER_LEN || length > BGP_MAX_MSG_LEN {
            return Err(BgpError::BadMessageLength {
                got: length as u16,
                min: BGP_HEADER_LEN as u16,
                max: BGP_MAX_MSG_LEN as u16,
            });
        }
        if data.len() < length {
            return Err(BgpError::BufferTooShort { need: length, have: data.len() });
        }

        let msg_type = MessageType::try_from(data[18])?;
        let body = &data[BGP_HEADER_LEN..length];

        match msg_type {
            MessageType::Open         => Ok(Self::Open(OpenMessage::parse(body)?)),
            MessageType::Update       => Ok(Self::Update(UpdateMessage::parse(body)?)),
            MessageType::Notification => Ok(Self::Notification(NotificationMessage::parse(body)?)),
            MessageType::Keepalive    => {
                if !body.is_empty() {
                    return Err(BgpError::BadMessageLength {
                        got: length as u16, min: 19, max: 19
                    });
                }
                Ok(Self::Keepalive)
            }
            MessageType::RouteRefresh => Ok(Self::RouteRefresh(RouteRefreshMessage::parse(body)?)),
        }
    }

    /// Serialize this message to bytes.
    pub fn encode(&self) -> Vec {
        let mut body = Vec::new();
        let msg_type: u8 = match self {
            Self::Open(_)         => 1,
            Self::Update(_)       => 2,
            Self::Notification(_) => 3,
            Self::Keepalive       => 4,
            Self::RouteRefresh(_) => 5,
        };

        match self {
            Self::Open(m)         => m.encode_body(&mut body),
            Self::Update(m)       => m.encode_body(&mut body),
            Self::Notification(m) => m.encode_body(&mut body),
            Self::Keepalive       => {}
            Self::RouteRefresh(m) => m.encode_body(&mut body),
        }

        let total_len = BGP_HEADER_LEN + body.len();
        let mut out = Vec::with_capacity(total_len);
        out.extend_from_slice(&BGP_MARKER);
        out.extend_from_slice(&(total_len as u16).to_be_bytes());
        out.push(msg_type);
        out.extend_from_slice(&body);
        out
    }
}

// ============================================================
// OPEN message parsing
// ============================================================
impl OpenMessage {
    pub fn parse(body: &[u8]) -> Result {
        if body.len() < 9 {
            return Err(BgpError::BufferTooShort { need: 9, have: body.len() });
        }

        let version = body[0];
        if version != BGP_VERSION {
            return Err(BgpError::OpenError(format!("unsupported version: {}", version)));
        }

        let my_as_2b   = u16::from_be_bytes([body[1], body[2]]);
        let hold_time  = u16::from_be_bytes([body[3], body[4]]);
        let bgp_id     = u32::from_be_bytes([body[5], body[6], body[7], body[8]]);
        let opt_parm_len = body[9] as usize;

        if hold_time == 1 || hold_time == 2 {
            return Err(BgpError::OpenError(format!("unacceptable hold time: {}", hold_time)));
        }
        if bgp_id == 0 || bgp_id == 0xFFFFFFFF {
            return Err(BgpError::OpenError(format!("invalid BGP ID: {:08x}", bgp_id)));
        }

        if 10 + opt_parm_len > body.len() {
            return Err(BgpError::BufferTooShort {
                need: 10 + opt_parm_len, have: body.len()
            });
        }

        let opt_data = &body[10..10 + opt_parm_len];
        let mut params = OpenParams {
            my_as:                my_as_2b as u32,
            hold_time,
            bgp_id,
            can_4byte_asn:        false,
            can_route_refresh:    false,
            can_mp_ipv4_unicast:  false,
            can_mp_ipv6_unicast:  false,
            can_graceful_restart: false,
            gr_restart_time:      0,
            can_add_path:         false,
            can_ext_msg:          false,
        };

        parse_optional_params(opt_data, &mut params)?;

        Ok(Self { my_as: params.my_as, hold_time, bgp_id, params })
    }

    pub fn encode_body(&self, out: &mut Vec) {
        out.push(BGP_VERSION);

        // 2-byte AS field
        let as_2b: u16 = if self.my_as > 65535 { BGP_AS_TRANS as u16 }
                         else { self.my_as as u16 };
        out.extend_from_slice(&as_2b.to_be_bytes());
        out.extend_from_slice(&self.hold_time.to_be_bytes());
        out.extend_from_slice(&self.bgp_id.to_be_bytes());

        // Build capabilities
        let mut caps = Vec::new();

        // 4-byte ASN capability
        caps.push(65u8);        // code
        caps.push(4u8);         // len
        caps.extend_from_slice(&self.my_as.to_be_bytes());

        // IPv4 unicast MP capability
        caps.push(1u8);         // code
        caps.push(4u8);         // len
        caps.extend_from_slice(&(1u16).to_be_bytes()); // AFI=IPv4
        caps.push(0u8);         // reserved
        caps.push(1u8);         // SAFI=unicast

        // Route Refresh capability
        caps.push(2u8);         // code
        caps.push(0u8);         // len=0

        // Wrap capabilities in optional parameter type 2
        let opt_parm_len = 2 + caps.len(); // type(1) + len(1) + caps
        out.push(opt_parm_len as u8);
        out.push(2u8);                     // parm type = Capabilities
        out.push(caps.len() as u8);
        out.extend_from_slice(&caps);
    }
}

fn parse_optional_params(data: &[u8], params: &mut OpenParams) -> Result {
    let mut off = 0;
    while off < data.len() {
        if off + 2 > data.len() {
            return Err(BgpError::OpenError("truncated optional parameter".into()));
        }
        let parm_type = data[off]; off += 1;
        let parm_len  = data[off] as usize; off += 1;
        if off + parm_len > data.len() {
            return Err(BgpError::OpenError("optional parameter length overflow".into()));
        }
        let parm_data = &data[off..off + parm_len];
        off += parm_len;

        if parm_type == 2 {
            parse_capabilities(parm_data, params)?;
        }
        // unknown parameter types: ignored per RFC
    }
    Ok(())
}

fn parse_capabilities(data: &[u8], params: &mut OpenParams) -> Result {
    let mut off = 0;
    while off < data.len() {
        if off + 2 > data.len() {
            return Err(BgpError::OpenError("truncated capability".into()));
        }
        let cap_code = data[off]; off += 1;
        let cap_len  = data[off] as usize; off += 1;
        if off + cap_len > data.len() {
            return Err(BgpError::OpenError("capability length overflow".into()));
        }
        let cap_data = &data[off..off + cap_len];
        off += cap_len;

        match cap_code {
            65 if cap_len >= 4 => { // 4-byte ASN
                let asn = u32::from_be_bytes([cap_data[0], cap_data[1],
                                              cap_data[2], cap_data[3]]);
                params.my_as = asn;
                params.can_4byte_asn = true;
            }
            2 => { params.can_route_refresh = true; }
            1 if cap_len >= 4 => { // MP Extensions
                let afi  = u16::from_be_bytes([cap_data[0], cap_data[1]]);
                let safi = cap_data[3];
                match (afi, safi) {
                    (1, 1) => params.can_mp_ipv4_unicast  = true,
                    (2, 1) => params.can_mp_ipv6_unicast  = true,
                    _      => {}
                }
            }
            64 if cap_len >= 2 => { // Graceful Restart
                let flags = u16::from_be_bytes([cap_data[0], cap_data[1]]);
                params.can_graceful_restart = true;
                params.gr_restart_time = flags & 0x0FFF;
            }
            69 => { params.can_add_path = true; }
            6  => { params.can_ext_msg  = true; }
            _  => {} // Unknown capability — ignored
        }
    }
    Ok(())
}

// ============================================================
// UPDATE message
// ============================================================
impl UpdateMessage {
    pub fn parse(body: &[u8]) -> Result {
        if body.len() < 4 {
            return Err(BgpError::BufferTooShort { need: 4, have: body.len() });
        }

        let mut off = 0;

        // Withdrawn routes
        let wd_len = u16::from_be_bytes([body[off], body[off+1]]) as usize;
        off += 2;
        if off + wd_len > body.len() {
            return Err(BgpError::UpdateError("withdrawn routes overflow".into()));
        }
        let withdrawn = parse_nlri_list(&body[off..off + wd_len])?;
        off += wd_len;

        // Path attributes
        if off + 2 > body.len() {
            return Ok(Self { withdrawn, attrs: None, nlri: vec![] });
        }
        let attr_len = u16::from_be_bytes([body[off], body[off+1]]) as usize;
        off += 2;
        if off + attr_len > body.len() {
            return Err(BgpError::UpdateError("path attribute overflow".into()));
        }

        let attrs = if attr_len > 0 {
            Some(PathAttributes::parse(&body[off..off + attr_len])?)
        } else {
            None
        };
        off += attr_len;

        // NLRI (remaining bytes)
        let nlri = parse_nlri_list(&body[off..])?;

        Ok(Self { withdrawn, attrs, nlri })
    }

    pub fn encode_body(&self, out: &mut Vec) {
        // Withdrawn routes
        let mut wd_bytes = Vec::new();
        for prefix in &self.withdrawn {
            prefix.encode(&mut wd_bytes);
        }
        out.extend_from_slice(&(wd_bytes.len() as u16).to_be_bytes());
        out.extend_from_slice(&wd_bytes);

        // Path attributes
        let attr_bytes = match &self.attrs {
            Some(attrs) => attrs.encode(),
            None        => Vec::new(),
        };
        out.extend_from_slice(&(attr_bytes.len() as u16).to_be_bytes());
        out.extend_from_slice(&attr_bytes);

        // NLRI
        for prefix in &self.nlri {
            prefix.encode(out);
        }
    }
}

fn parse_nlri_list(data: &[u8]) -> Result<Vec, BgpError> {
    let mut prefixes = Vec::new();
    let mut off = 0;
    while off < data.len() {
        let p = Prefix4::decode(data, &mut off)?;
        prefixes.push(p);
    }
    Ok(prefixes)
}

// ============================================================
// NOTIFICATION message
// ============================================================
impl NotificationMessage {
    pub fn parse(body: &[u8]) -> Result {
        if body.len() < 2 {
            return Err(BgpError::BufferTooShort { need: 2, have: body.len() });
        }
        Ok(Self {
            error_code:    body[0],
            error_subcode: body[1],
            data:          body[2..].to_vec(),
        })
    }

    pub fn encode_body(&self, out: &mut Vec) {
        out.push(self.error_code);
        out.push(self.error_subcode);
        out.extend_from_slice(&self.data);
    }
}

// ============================================================
// ROUTE-REFRESH message
// ============================================================
impl RouteRefreshMessage {
    pub fn parse(body: &[u8]) -> Result {
        if body.len() < 4 {
            return Err(BgpError::BufferTooShort { need: 4, have: body.len() });
        }
        Ok(Self {
            afi:  u16::from_be_bytes([body[0], body[1]]),
            safi: body[3],
        })
    }

    pub fn encode_body(&self, out: &mut Vec) {
        out.extend_from_slice(&self.afi.to_be_bytes());
        out.push(0); // reserved
        out.push(self.safi);
    }
}
```

### 18.6 src/attr.rs — Path Attributes

```rust
// File: src/attr.rs
// BGP path attribute handling

use std::net::Ipv4Addr;
use crate::error::BgpError;
use crate::types::*;

// Attribute flag constants
const FLAG_OPTIONAL:   u8 = 0x80;
const FLAG_TRANSITIVE: u8 = 0x40;
const FLAG_PARTIAL:    u8 = 0x20;
const FLAG_EXT_LEN:    u8 = 0x10;

#[derive(Debug, Clone, PartialEq)]
pub struct PathAttributes {
    pub origin:         Origin,
    pub as_path:        Vec,
    pub next_hop:       Option,     // None for IPv6 paths
    pub med:            Option,
    pub local_pref:     Option,
    pub atomic_agg:     bool,
    pub communities:    Vec,
    pub large_communities: Vec,
    pub originator_id:  Option,
    pub cluster_list:   Vec,
    // Unknown transitive attributes preserved for forwarding
    pub unknown_transitive: Vec)>, // (flags, type, value)
}

impl PathAttributes {
    pub fn new() -> Self {
        Self {
            origin:             Origin::Igp,
            as_path:            Vec::new(),
            next_hop:           None,
            med:                None,
            local_pref:         Some(100), // default
            atomic_agg:         false,
            communities:        Vec::new(),
            large_communities:  Vec::new(),
            originator_id:      None,
            cluster_list:       Vec::new(),
            unknown_transitive: Vec::new(),
        }
    }

    /// Parse path attributes from the attribute section of an UPDATE message
    pub fn parse(data: &[u8]) -> Result {
        let mut attrs = Self::new();
        attrs.local_pref = None; // reset — will be set if attribute present
        let mut off = 0;

        // Track which well-known mandatory attributes we've seen
        let mut seen_origin    = false;
        let mut seen_as_path   = false;
        let mut seen_next_hop  = false;

        while off < data.len() {
            if off + 2 > data.len() {
                return Err(BgpError::AttributeError("truncated attribute header".into()));
            }

            let flags     = data[off]; off += 1;
            let type_code = data[off]; off += 1;

            let attr_len: usize = if flags & FLAG_EXT_LEN != 0 {
                if off + 2 > data.len() {
                    return Err(BgpError::AttributeError("truncated extended length".into()));
                }
                let l = u16::from_be_bytes([data[off], data[off+1]]) as usize;
                off += 2;
                l
            } else {
                if off + 1 > data.len() {
                    return Err(BgpError::AttributeError("truncated length".into()));
                }
                let l = data[off] as usize;
                off += 1;
                l
            };

            if off + attr_len > data.len() {
                return Err(BgpError::AttributeError(
                    format!("attribute type {} length {} overflows buffer", type_code, attr_len)
                ));
            }

            let val = &data[off..off + attr_len];
            off += attr_len;

            match type_code {
                1 => { // ORIGIN
                    if attr_len != 1 {
                        return Err(BgpError::AttributeError("ORIGIN must be 1 byte".into()));
                    }
                    attrs.origin = Origin::try_from(val[0])?;
                    seen_origin = true;
                }
                2 => { // AS_PATH
                    attrs.as_path = parse_as_path(val, true)?;
                    seen_as_path = true;
                }
                3 => { // NEXT_HOP
                    if attr_len != 4 {
                        return Err(BgpError::AttributeError("NEXT_HOP must be 4 bytes".into()));
                    }
                    let nh = Ipv4Addr::new(val[0], val[1], val[2], val[3]);
                    // Validate: not multicast, not 0.0.0.0, not loopback
                    let nh_u32 = u32::from(nh);
                    if nh_u32 == 0 || nh_u32 >> 28 == 0xE || nh_u32 >> 24 == 127 {
                        return Err(BgpError::AttributeError(
                            format!("invalid NEXT_HOP: {}", nh)
                        ));
                    }
                    attrs.next_hop = Some(nh);
                    seen_next_hop = true;
                }
                4 => { // MED
                    if attr_len != 4 {
                        return Err(BgpError::AttributeError("MED must be 4 bytes".into()));
                    }
                    attrs.med = Some(u32::from_be_bytes([val[0], val[1], val[2], val[3]]));
                }
                5 => { // LOCAL_PREF
                    if attr_len != 4 {
                        return Err(BgpError::AttributeError("LOCAL_PREF must be 4 bytes".into()));
                    }
                    attrs.local_pref = Some(u32::from_be_bytes([val[0], val[1], val[2], val[3]]));
                }
                6 => { // ATOMIC_AGGREGATE
                    if attr_len != 0 {
                        return Err(BgpError::AttributeError("ATOMIC_AGGREGATE must be 0 bytes".into()));
                    }
                    attrs.atomic_agg = true;
                }
                8 => { // COMMUNITY
                    if attr_len % 4 != 0 {
                        return Err(BgpError::AttributeError("COMMUNITY length not multiple of 4".into()));
                    }
                    for chunk in val.chunks_exact(4) {
                        let v = u32::from_be_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]);
                        attrs.communities.push(Community(v));
                    }
                }
                9 => { // ORIGINATOR_ID
                    if attr_len != 4 {
                        return Err(BgpError::AttributeError("ORIGINATOR_ID must be 4 bytes".into()));
                    }
                    attrs.originator_id = Some(u32::from_be_bytes([val[0], val[1], val[2], val[3]]));
                }
                10 => { // CLUSTER_LIST
                    if attr_len % 4 != 0 {
                        return Err(BgpError::AttributeError("CLUSTER_LIST not multiple of 4".into()));
                    }
                    for chunk in val.chunks_exact(4) {
                        attrs.cluster_list.push(u32::from_be_bytes([chunk[0], chunk[1],
                                                                    chunk[2], chunk[3]]));
                    }
                }
                32 => { // LARGE_COMMUNITY
                    if attr_len % 12 != 0 {
                        return Err(BgpError::AttributeError("LARGE_COMMUNITY not multiple of 12".into()));
                    }
                    for chunk in val.chunks_exact(12) {
                        attrs.large_communities.push(LargeCommunity {
                            global_admin: u32::from_be_bytes([chunk[0], chunk[1], chunk[2], chunk[3]]),
                            local_data1:  u32::from_be_bytes([chunk[4], chunk[5], chunk[6], chunk[7]]),
                            local_data2:  u32::from_be_bytes([chunk[8], chunk[9], chunk[10], chunk[11]]),
                        });
                    }
                }
                _ => {
                    // Handle unknown attributes
                    if flags & FLAG_OPTIONAL == 0 {
                        // Well-known but unrecognized
                        return Err(BgpError::AttributeError(
                            format!("unrecognized well-known attribute: {}", type_code)
                        ));
                    }
                    if flags & FLAG_TRANSITIVE != 0 {
                        // Optional transitive: preserve with Partial bit set
                        let new_flags = flags | FLAG_PARTIAL;
                        attrs.unknown_transitive.push((new_flags, type_code, val.to_vec()));
                    }
                    // Optional non-transitive: silently discard
                }
            }
        }

        // Check mandatory attributes present (only if this is a route advertisement)
        // Caller is responsible for checking when NLRI is non-empty

        let _ = (seen_origin, seen_as_path, seen_next_hop); // used for validation
        Ok(attrs)
    }

    /// Validate that all mandatory attributes are present (call when NLRI is non-empty)
    pub fn validate_mandatory(&self) -> Result {
        // ORIGIN, AS_PATH: presence checked during parse
        // NEXT_HOP: required for IPv4 unicast NLRI
        if self.next_hop.is_none() {
            return Err(BgpError::UpdateError("missing mandatory attribute NEXT_HOP".into()));
        }
        Ok(())
    }

    /// Encode all attributes to bytes
    pub fn encode(&self) -> Vec {
        let mut out = Vec::new();

        // ORIGIN (well-known mandatory: flags=0x40)
        write_attr(&mut out, 0x40, 1, &[self.origin as u8]);

        // AS_PATH (well-known mandatory: flags=0x40)
        let as_path_bytes = encode_as_path(&self.as_path, true);
        write_attr(&mut out, 0x40, 2, &as_path_bytes);

        // NEXT_HOP (well-known mandatory: flags=0x40)
        if let Some(nh) = self.next_hop {
            write_attr(&mut out, 0x40, 3, &nh.octets());
        }

        // MED (optional non-transitive: flags=0x80)
        if let Some(med) = self.med {
            write_attr(&mut out, 0x80, 4, &med.to_be_bytes());
        }

        // LOCAL_PREF (well-known discretionary: flags=0x40)
        if let Some(lp) = self.local_pref {
            write_attr(&mut out, 0x40, 5, &lp.to_be_bytes());
        }

        // ATOMIC_AGGREGATE (well-known discretionary: flags=0x40)
        if self.atomic_agg {
            write_attr(&mut out, 0x40, 6, &[]);
        }

        // COMMUNITY (optional transitive: flags=0xC0)
        if !self.communities.is_empty() {
            let mut comm_bytes = Vec::with_capacity(self.communities.len() * 4);
            for c in &self.communities {
                comm_bytes.extend_from_slice(&c.0.to_be_bytes());
            }
            write_attr(&mut out, 0xC0, 8, &comm_bytes);
        }

        // ORIGINATOR_ID (optional non-transitive: flags=0x80)
        if let Some(oid) = self.originator_id {
            write_attr(&mut out, 0x80, 9, &oid.to_be_bytes());
        }

        // CLUSTER_LIST (optional non-transitive: flags=0x80)
        if !self.cluster_list.is_empty() {
            let mut cl_bytes = Vec::with_capacity(self.cluster_list.len() * 4);
            for &cl in &self.cluster_list {
                cl_bytes.extend_from_slice(&cl.to_be_bytes());
            }
            write_attr(&mut out, 0x80, 10, &cl_bytes);
        }

        // LARGE_COMMUNITY (optional transitive: flags=0xC0)
        if !self.large_communities.is_empty() {
            let mut lc_bytes = Vec::with_capacity(self.large_communities.len() * 12);
            for lc in &self.large_communities {
                lc_bytes.extend_from_slice(&lc.global_admin.to_be_bytes());
                lc_bytes.extend_from_slice(&lc.local_data1.to_be_bytes());
                lc_bytes.extend_from_slice(&lc.local_data2.to_be_bytes());
            }
            write_attr(&mut out, 0xC0, 32, &lc_bytes);
        }

        // Unknown transitive attributes
        for (flags, type_code, val) in &self.unknown_transitive {
            write_attr(&mut out, *flags, *type_code, val);
        }

        out
    }

    /// Compute AS_PATH length (for decision process)
    pub fn as_path_length(&self) -> usize {
        self.as_path.iter().map(|seg| match seg.seg_type {
            AsPathSegmentType::AsSequence      => seg.asns.len(),
            AsPathSegmentType::AsSet           => 1,
            AsPathSegmentType::AsConfedSequence |
            AsPathSegmentType::AsConfedSet     => 0,
        }).sum()
    }

    /// Check if ASN is in AS_PATH (loop detection)
    pub fn contains_asn(&self, asn: u32) -> bool {
        self.as_path.iter().any(|seg| seg.asns.contains(&asn))
    }

    /// Prepend our ASN to AS_PATH (for eBGP export)
    pub fn prepend_asn(&mut self, asn: u32) {
        if let Some(first) = self.as_path.first_mut() {
            if first.seg_type == AsPathSegmentType::AsSequence {
                first.asns.insert(0, asn);
                return;
            }
        }
        self.as_path.insert(0, AsPathSegment::new_sequence(vec![asn]));
    }
}

fn write_attr(out: &mut Vec, flags: u8, type_code: u8, value: &[u8]) {
    let use_ext = value.len() > 255;
    let actual_flags = if use_ext { flags | FLAG_EXT_LEN } else { flags };
    out.push(actual_flags);
    out.push(type_code);
    if use_ext {
        out.extend_from_slice(&(value.len() as u16).to_be_bytes());
    } else {
        out.push(value.len() as u8);
    }
    out.extend_from_slice(value);
}

fn parse_as_path(data: &[u8], four_byte: bool) -> Result<Vec, BgpError> {
    let mut segs = Vec::new();
    let mut off = 0;

    while off < data.len() {
        if off + 2 > data.len() {
            return Err(BgpError::UpdateError("truncated AS_PATH segment".into()));
        }
        let seg_type = data[off]; off += 1;
        let seg_len  = data[off] as usize; off += 1;
        let asn_size = if four_byte { 4 } else { 2 };

        if off + seg_len * asn_size > data.len() {
            return Err(BgpError::UpdateError("AS_PATH segment overflow".into()));
        }

        let seg_type_enum = match seg_type {
            1 => AsPathSegmentType::AsSet,
            2 => AsPathSegmentType::AsSequence,
            3 => AsPathSegmentType::AsConfedSequence,
            4 => AsPathSegmentType::AsConfedSet,
            _ => return Err(BgpError::UpdateError(
                    format!("unknown AS_PATH segment type: {}", seg_type))),
        };

        let mut asns = Vec::with_capacity(seg_len);
        for _ in 0..seg_len {
            let asn = if four_byte {
                let a = u32::from_be_bytes([data[off], data[off+1], data[off+2], data[off+3]]);
                off += 4;
                a
            } else {
                let a = u16::from_be_bytes([data[off], data[off+1]]) as u32;
                off += 2;
                a
            };
            asns.push(asn);
        }

        segs.push(AsPathSegment { seg_type: seg_type_enum, asns });
    }

    Ok(segs)
}

fn encode_as_path(segs: &[AsPathSegment], four_byte: bool) -> Vec {
    let mut out = Vec::new();
    for seg in segs {
        let seg_type: u8 = match seg.seg_type {
            AsPathSegmentType::AsSet            => 1,
            AsPathSegmentType::AsSequence       => 2,
            AsPathSegmentType::AsConfedSequence => 3,
            AsPathSegmentType::AsConfedSet      => 4,
        };
        out.push(seg_type);
        out.push(seg.asns.len() as u8);
        for &asn in &seg.asns {
            if four_byte {
                out.extend_from_slice(&asn.to_be_bytes());
            } else {
                out.extend_from_slice(&(asn as u16).to_be_bytes());
            }
        }
    }
    out
}
```

### 18.7 src/rib.rs — Route Information Base

```rust
// File: src/rib.rs
// BGP Route Information Base and Decision Process

use std::collections::HashMap;
use std::net::Ipv4Addr;
use std::time::Instant;
use crate::types::*;
use crate::attr::PathAttributes;

/// A single route in the RIB
#[derive(Debug, Clone)]
pub struct Route {
    pub prefix:      Prefix4,
    pub attrs:       PathAttributes,
    pub received_at: Instant,
    pub peer_id:     u32,      // BGP ID of the peer that sent this
    pub is_ibgp:     bool,
    pub igp_metric:  u32,      // IGP metric to next-hop (for step 7)
}

/// Adjacency RIB — stores routes from one peer
pub struct AdjRibIn {
    pub routes: HashMap,
}

impl AdjRibIn {
    pub fn new() -> Self {
        Self { routes: HashMap::new() }
    }

    pub fn insert(&mut self, route: Route) {
        self.routes.insert(route.prefix, route);
    }

    pub fn remove(&mut self, prefix: &Prefix4) -> Option {
        self.routes.remove(prefix)
    }

    pub fn get(&self, prefix: &Prefix4) -> Option {
        self.routes.get(prefix)
    }

    pub fn len(&self) -> usize { self.routes.len() }
}

/// Local RIB — best paths after Decision Process
pub struct LocRib {
    pub routes: HashMap,
}

impl LocRib {
    pub fn new() -> Self {
        Self { routes: HashMap::new() }
    }
}

/// BGP Decision Process (RFC 4271 Section 9.1)
/// Given multiple candidate routes for a prefix, returns the best one.
pub fn decision_process(candidates: &[&'a Route]) -> Option {
    if candidates.is_empty() { return None; }
    let mut best = candidates[0];
    for &candidate in &candidates[1..] {
        if is_better(candidate, best) {
            best = candidate;
        }
    }
    Some(best)
}

/// Returns true if `a` is better than `b`
fn is_better(a: &Route, b: &Route) -> bool {
    // Step 0: NEXT_HOP reachability — assumed by caller (both candidates are valid)

    // Step 1: Higher LOCAL_PREF wins
    let lp_a = a.attrs.local_pref.unwrap_or(100);
    let lp_b = b.attrs.local_pref.unwrap_or(100);
    if lp_a != lp_b { return lp_a > lp_b; }

    // Step 2: Locally originated — skipped (no local injection in this impl)

    // Step 3: Shorter AS_PATH wins
    let len_a = a.attrs.as_path_length();
    let len_b = b.attrs.as_path_length();
    if len_a != len_b { return len_a < len_b; }

    // Step 4: Lower ORIGIN wins (IGP < EGP < INCOMPLETE)
    if a.attrs.origin != b.attrs.origin {
        return (a.attrs.origin as u8) < (b.attrs.origin as u8);
    }

    // Step 5: Lower MED wins (only if from same neighboring AS)
    // Simplified: compare if both have MED
    match (a.attrs.med, b.attrs.med) {
        (Some(m_a), Some(m_b)) if m_a != m_b => return m_a < m_b,
        _ => {}
    }

    // Step 6: eBGP preferred over iBGP
    if a.is_ibgp != b.is_ibgp { return !a.is_ibgp; }

    // Step 7: Lowest IGP metric to NEXT_HOP
    if a.igp_metric != b.igp_metric { return a.igp_metric < b.igp_metric; }

    // Step 8: Oldest eBGP route (most stable) — implementation defined
    // Omitted for simplicity

    // Step 9: Lowest BGP Router ID
    if a.peer_id != b.peer_id { return a.peer_id < b.peer_id; }

    // Step 10: Shortest CLUSTER_LIST
    let cl_a = a.attrs.cluster_list.len();
    let cl_b = b.attrs.cluster_list.len();
    if cl_a != cl_b { return cl_a < cl_b; }

    // Step 11: Lowest neighbor IP (tiebreaker — always produces a result)
    let nh_a = a.attrs.next_hop.map(u32::from).unwrap_or(u32::MAX);
    let nh_b = b.attrs.next_hop.map(u32::from).unwrap_or(u32::MAX);
    nh_a < nh_b
}
```

### 18.8 src/fsm.rs — Async BGP FSM with Tokio

```rust
// File: src/fsm.rs
// Async BGP Finite State Machine using Tokio

use std::net::{IpAddr, SocketAddr};
use std::time::Duration;
use tokio::net::TcpStream;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::sync::mpsc;
use tokio::time::{sleep, timeout, Instant};
use tracing::{info, warn, error, debug};
use crate::error::BgpError;
use crate::types::*;
use crate::message::*;
use crate::rib::AdjRibIn;

/// Configuration for a BGP peer session
#[derive(Debug, Clone)]
pub struct PeerConfig {
    pub local_addr:  IpAddr,
    pub peer_addr:   IpAddr,
    pub local_as:    u32,
    pub peer_as:     u32,  // 0 = any
    pub local_bgp_id: u32,
    pub hold_time:   u16,
    pub password:    Option,
    pub passive:     bool,
    pub max_prefixes: u32,
}

/// Events that the FSM produces for the caller
#[derive(Debug)]
pub enum SessionEvent {
    StateChange { old: FsmState, new: FsmState },
    RouteUpdate { update: UpdateMessage },
    SessionError(BgpError),
}

/// The BGP peer session state machine
pub struct BgpSession {
    config:      PeerConfig,
    state:       FsmState,
    adj_rib_in:  AdjRibIn,
    remote_params: Option,
    negotiated_hold: u16,
    negotiated_ka:   u16,
    event_tx:    mpsc::Sender,
}

impl BgpSession {
    pub fn new(config: PeerConfig, event_tx: mpsc::Sender) -> Self {
        Self {
            config,
            state:         FsmState::Idle,
            adj_rib_in:    AdjRibIn::new(),
            remote_params: None,
            negotiated_hold: 0,
            negotiated_ka:   0,
            event_tx,
        }
    }

    async fn transition(&mut self, new_state: FsmState) {
        let old_state = self.state;
        self.state = new_state;
        info!("BGP FSM {}: {} -> {}", self.config.peer_addr, old_state, new_state);
        let _ = self.event_tx.send(SessionEvent::StateChange {
            old: old_state, new: new_state,
        }).await;
    }

    /// Main session runner — handles one complete BGP session lifecycle
    pub async fn run(&mut self) {
        loop {
            match self.state {
                FsmState::Idle => {
                    // Wait before retry
                    sleep(Duration::from_secs(CONNECT_RETRY_TIME)).await;
                    self.transition(FsmState::Connect).await;
                }
                FsmState::Connect => {
                    self.run_connect().await;
                }
                _ => {
                    // Other states handled within run_connect
                    break;
                }
            }
        }
    }

    async fn run_connect(&mut self) {
        let peer_addr = SocketAddr::new(self.config.peer_addr, BGP_PORT);

        info!("BGP: connecting to {}", peer_addr);

        let connect_result = timeout(
            Duration::from_secs(CONNECT_RETRY_TIME),
            TcpStream::connect(peer_addr)
        ).await;

        match connect_result {
            Ok(Ok(stream)) => {
                info!("BGP: TCP connected to {}", peer_addr);
                if let Err(e) = self.run_established(stream).await {
                    warn!("BGP session error: {}", e);
                }
            }
            Ok(Err(e)) => {
                warn!("BGP: TCP connect failed: {}", e);
                self.transition(FsmState::Active).await;
                sleep(Duration::from_secs(10)).await;
                self.transition(FsmState::Idle).await;
            }
            Err(_) => {
                warn!("BGP: connect timeout");
                self.transition(FsmState::Active).await;
                self.transition(FsmState::Idle).await;
            }
        }
    }

    async fn run_established(&mut self, stream: TcpStream) -> Result {
        let (mut reader, mut writer) = stream.into_split();
        let mut rx_buf = vec![0u8; BGP_MAX_MSG_LEN];

        // OPENSENT: send our OPEN
        let open_msg = self.build_open();
        writer.write_all(&open_msg.encode()).await?;
        self.transition(FsmState::OpenSent).await;

        // Wait for peer's OPEN (with large initial hold timer)
        let peer_open = timeout(
            Duration::from_secs(240),
            self.recv_message(&mut reader, &mut rx_buf)
        ).await
        .map_err(|_| BgpError::HoldTimerExpired)??;

        let remote_params = match peer_open {
            BgpMessage::Open(o) => {
                // Validate
                if self.config.peer_as != 0 && o.my_as != self.config.peer_as {
                    return Err(BgpError::OpenError(format!(
                        "expected AS {}, got AS {}", self.config.peer_as, o.my_as
                    )));
                }
                o.params.clone()
            }
            BgpMessage::Notification(n) => {
                return Err(BgpError::Cease(format!(
                    "peer sent NOTIFICATION {}/{}", n.error_code, n.error_subcode
                )));
            }
            _ => {
                return Err(BgpError::FsmError {
                    event: "non-OPEN message".into(),
                    state: "OpenSent".into(),
                });
            }
        };

        // Negotiate hold time
        self.negotiated_hold = std::cmp::min(self.config.hold_time, remote_params.hold_time);
        self.negotiated_ka   = if self.negotiated_hold > 0 { self.negotiated_hold / 3 } else { 0 };
        self.remote_params   = Some(remote_params);

        // OPENCONFIRM: send KEEPALIVE
        let ka = BgpMessage::Keepalive;
        writer.write_all(&ka.encode()).await?;
        self.transition(FsmState::OpenConfirm).await;

        // Wait for peer's KEEPALIVE
        let peer_ka = timeout(
            Duration::from_secs(self.negotiated_hold as u64),
            self.recv_message(&mut reader, &mut rx_buf)
        ).await
        .map_err(|_| BgpError::HoldTimerExpired)??;

        match peer_ka {
            BgpMessage::Keepalive => {}
            BgpMessage::Notification(n) => {
                return Err(BgpError::Cease(format!(
                    "peer NOTIFICATION {}/{}", n.error_code, n.error_subcode
                )));
            }
            _ => {
                return Err(BgpError::FsmError {
                    event: "expected KEEPALIVE".into(),
                    state: "OpenConfirm".into(),
                });
            }
        }

        // ESTABLISHED
        self.transition(FsmState::Established).await;
        info!("BGP: ESTABLISHED with AS{} BGP-ID {:08x}",
              self.remote_params.as_ref().unwrap().my_as,
              self.remote_params.as_ref().unwrap().bgp_id);

        // Main message loop
        let hold_duration = Duration::from_secs(self.negotiated_hold as u64);
        let ka_duration   = Duration::from_secs(self.negotiated_ka as u64);
        let mut hold_deadline = Instant::now() + hold_duration;
        let mut ka_deadline   = Instant::now() + ka_duration;

        loop {
            // Determine time until next timer fires
            let now = Instant::now();
            let next_timer = std::cmp::min(hold_deadline, ka_deadline);
            let wait = if next_timer > now { next_timer - now }
                       else { Duration::from_millis(1) };

            let recv_result = timeout(wait, self.recv_message(&mut reader, &mut rx_buf)).await;

            // Check timer expirations
            let now = Instant::now();
            if now >= hold_deadline && self.negotiated_hold > 0 {
                error!("BGP: hold timer expired");
                // Send HOLD TIMER EXPIRED notification
                let notif = BgpMessage::Notification(NotificationMessage {
                    error_code: 4, error_subcode: 0, data: vec![]
                });
                let _ = writer.write_all(&notif.encode()).await;
                return Err(BgpError::HoldTimerExpired);
            }
            if now >= ka_deadline && self.negotiated_ka > 0 {
                writer.write_all(&BgpMessage::Keepalive.encode()).await?;
                ka_deadline = Instant::now() + ka_duration;
                debug!("BGP: sent KEEPALIVE");
            }

            match recv_result {
                Ok(Ok(msg)) => {
                    if self.negotiated_hold > 0 {
                        hold_deadline = Instant::now() + hold_duration;
                    }
                    self.handle_message(msg).await?;
                }
                Ok(Err(e)) => {
                    return Err(e);
                }
                Err(_) => {
                    // Timeout — just loop back to check timers
                    continue;
                }
            }
        }
    }

    async fn handle_message(&mut self, msg: BgpMessage) -> Result {
        match msg {
            BgpMessage::Keepalive => {
                debug!("BGP: received KEEPALIVE");
            }
            BgpMessage::Update(update) => {
                debug!("BGP: UPDATE {} withdrawn, {} NLRI",
                       update.withdrawn.len(), update.nlri.len());

                // Check max prefix limit
                let current = self.adj_rib_in.len();
                if current + update.nlri.len() > self.config.max_prefixes as usize {
                    return Err(BgpError::MaxPrefixesExceeded {
                        limit: self.config.max_prefixes
                    });
                }

                // Forward to caller
                let _ = self.event_tx.send(SessionEvent::RouteUpdate {
                    update: update.clone()
                }).await;
            }
            BgpMessage::Notification(n) => {
                warn!("BGP: received NOTIFICATION {}/{}", n.error_code, n.error_subcode);
                return Err(BgpError::Cease(format!(
                    "peer sent NOTIFICATION {}/{}", n.error_code, n.error_subcode
                )));
            }
            BgpMessage::RouteRefresh(rr) => {
                debug!("BGP: received ROUTE-REFRESH AFI={} SAFI={}", rr.afi, rr.safi);
                // TODO: re-advertise our routes for this AFI/SAFI
            }
            BgpMessage::Open(_) => {
                return Err(BgpError::FsmError {
                    event: "OPEN in ESTABLISHED".into(),
                    state: "Established".into(),
                });
            }
        }
        Ok(())
    }

    /// Read and parse one complete BGP message from the stream
    async fn recv_message(
        &self,
        reader: &mut (impl AsyncReadExt + Unpin),
        buf: &mut Vec
    ) -> Result {
        // Read exactly BGP_HEADER_LEN bytes first
        reader.read_exact(&mut buf[..BGP_HEADER_LEN]).await?;

        // Parse header to get total length
        let length = u16::from_be_bytes([buf[16], buf[17]]) as usize;
        if length < BGP_HEADER_LEN || length > BGP_MAX_MSG_LEN {
            return Err(BgpError::BadMessageLength {
                got: length as u16,
                min: BGP_HEADER_LEN as u16,
                max: BGP_MAX_MSG_LEN as u16,
            });
        }

        // Read remaining bytes
        if length > BGP_HEADER_LEN {
            reader.read_exact(&mut buf[BGP_HEADER_LEN..length]).await?;
        }

        BgpMessage::parse(&buf[..length])
    }

    fn build_open(&self) -> BgpMessage {
        let open = OpenMessage {
            my_as:     self.config.local_as,
            hold_time: self.config.hold_time,
            bgp_id:    self.config.local_bgp_id,
            params:    OpenParams {
                my_as:                self.config.local_as,
                hold_time:            self.config.hold_time,
                bgp_id:               self.config.local_bgp_id,
                can_4byte_asn:        true,
                can_route_refresh:    true,
                can_mp_ipv4_unicast:  true,
                can_mp_ipv6_unicast:  false,
                can_graceful_restart: false,
                gr_restart_time:      0,
                can_add_path:         false,
                can_ext_msg:          false,
            },
        };
        BgpMessage::Open(open)
    }
}
```

---

## 19. Testing BGP Implementations

### 19.1 Unit Tests — Message Parsing (Rust)

```rust
// File: src/message.rs (tests module appended)
#[cfg(test)]
mod tests {
    use super::*;

    // Build a minimal valid BGP header + KEEPALIVE
    fn keepalive_bytes() -> Vec {
        let mut v = vec![0xFF; 16]; // marker
        v.extend_from_slice(&19u16.to_be_bytes()); // length
        v.push(4); // type = KEEPALIVE
        v
    }

    #[test]
    fn test_keepalive_parse() {
        let bytes = keepalive_bytes();
        let msg = BgpMessage::parse(&bytes).unwrap();
        assert!(matches!(msg, BgpMessage::Keepalive));
    }

    #[test]
    fn test_keepalive_encode_decode() {
        let msg = BgpMessage::Keepalive;
        let encoded = msg.encode();
        assert_eq!(encoded.len(), BGP_HEADER_LEN);
        let decoded = BgpMessage::parse(&encoded).unwrap();
        assert!(matches!(decoded, BgpMessage::Keepalive));
    }

    #[test]
    fn test_bad_marker() {
        let mut bytes = keepalive_bytes();
        bytes[5] = 0x00; // corrupt marker
        let err = BgpMessage::parse(&bytes).unwrap_err();
        assert!(matches!(err, BgpError::MarkerError));
    }

    #[test]
    fn test_bad_length_too_short() {
        let mut bytes = keepalive_bytes();
        bytes[16] = 0x00;
        bytes[17] = 0x05; // length = 5 (< min 19)
        let err = BgpMessage::parse(&bytes).unwrap_err();
        assert!(matches!(err, BgpError::BadMessageLength { .. }));
    }

    #[test]
    fn test_prefix4_encode_decode() {
        let prefix = Prefix4::new("192.168.1.0".parse().unwrap(), 24).unwrap();
        let mut buf = Vec::new();
        prefix.encode(&mut buf);
        // Should be: 0x18 (24) 0xC0 0xA8 0x01 (3 bytes)
        assert_eq!(buf, vec![24, 192, 168, 1]);
        let mut off = 0;
        let decoded = Prefix4::decode(&buf, &mut off).unwrap();
        assert_eq!(decoded, prefix);
    }

    #[test]
    fn test_prefix4_default_route() {
        let prefix = Prefix4::new("0.0.0.0".parse().unwrap(), 0).unwrap();
        let mut buf = Vec::new();
        prefix.encode(&mut buf);
        assert_eq!(buf, vec![0]); // just the length byte
        let mut off = 0;
        let decoded = Prefix4::decode(&buf, &mut off).unwrap();
        assert_eq!(decoded.length, 0);
    }

    #[test]
    fn test_update_roundtrip() {
        use crate::attr::PathAttributes;
        use std::net::Ipv4Addr;

        let mut attrs = PathAttributes::new();
        attrs.origin = Origin::Igp;
        attrs.as_path = vec![AsPathSegment::new_sequence(vec![64512, 65001])];
        attrs.next_hop = Some(Ipv4Addr::new(10, 0, 0, 1));
        attrs.local_pref = Some(100);

        let nlri = vec![
            Prefix4::new("10.0.0.0".parse().unwrap(), 8).unwrap(),
            Prefix4::new("192.168.0.0".parse().unwrap(), 16).unwrap(),
        ];

        let update = BgpMessage::Update(UpdateMessage {
            withdrawn: vec![],
            attrs: Some(attrs),
            nlri: nlri.clone(),
        });

        let encoded = update.encode();
        let decoded = BgpMessage::parse(&encoded).unwrap();

        match decoded {
            BgpMessage::Update(u) => {
                assert_eq!(u.nlri.len(), 2);
                assert_eq!(u.nlri[0], nlri[0]);
                assert_eq!(u.nlri[1], nlri[1]);
            }
            _ => panic!("expected UPDATE"),
        }
    }

    #[test]
    fn test_community_well_known() {
        assert_eq!(Community::NO_EXPORT.asn(), 0xFFFF);
        assert_eq!(Community::NO_EXPORT.value(), 0xFF01);
        assert_eq!(format!("{}", Community::NO_EXPORT), "65535:65281");
    }

    #[test]
    fn test_as_path_loop_detection() {
        let attrs = crate::attr::PathAttributes {
            as_path: vec![
                AsPathSegment::new_sequence(vec![64512, 65001, 65002])
            ],
            ..crate::attr::PathAttributes::new()
        };
        assert!(attrs.contains_asn(65001));
        assert!(!attrs.contains_asn(65003));
    }

    #[test]
    fn test_as_path_length() {
        let attrs = crate::attr::PathAttributes {
            as_path: vec![
                AsPathSegment::new_sequence(vec![64512, 65001]),
                AsPathSegment::new_set(vec![65002, 65003, 65004]),
                AsPathSegment { seg_type: AsPathSegmentType::AsConfedSequence,
                               asns: vec![65005, 65006] },
            ],
            ..crate::attr::PathAttributes::new()
        };
        // SEQUENCE(2) + SET(1) + CONFED_SEQUENCE(0) = 3
        assert_eq!(attrs.as_path_length(), 3);
    }

    // Property-based test: encode-decode roundtrip for random prefixes
    #[cfg(feature = "proptest")]
    proptest::proptest! {
        #[test]
        fn prop_prefix_roundtrip(addr in proptest::prelude::any::(),
                                  len in 0u8..=32) {
            let ip = std::net::Ipv4Addr::from(addr);
            let prefix = Prefix4::new(ip, len).unwrap();
            let mut buf = Vec::new();
            prefix.encode(&mut buf);
            let mut off = 0;
            let decoded = Prefix4::decode(&buf, &mut off).unwrap();
            proptest::prop_assert_eq!(decoded.length, prefix.length);
        }
    }
}
```

### 19.2 C Unit Tests

```c
// File: tests/test_msg_parse.c
#include "../src/bgp.h"
#include 
#include 
#include 
#include <arpa/inet.h>

#define TEST(name) printf("  TEST %s...", #name)
#define PASS()     printf(" PASS\n")
#define FAIL(msg)  do { printf(" FAIL: %s\n", msg); return 1; } while(0)

// ---- test helpers ----

static void build_marker(uint8_t *buf) {
    memset(buf, 0xFF, BGP_MARKER_LEN);
}

// ---- tests ----

static int test_keepalive_parse(void) {
    TEST(test_keepalive_parse);
    uint8_t buf[19];
    build_marker(buf);
    uint16_t len = htons(19);
    memcpy(buf + 16, &len, 2);
    buf[18] = BGP_MSG_KEEPALIVE;

    uint16_t out_len;
    uint8_t  out_type;
    int rc = bgp_msg_parse_header(buf, 19, &out_len, &out_type);
    if (rc != 0)           FAIL("header parse failed");
    if (out_len != 19)     FAIL("wrong length");
    if (out_type != 4)     FAIL("wrong type");
    PASS();
    return 0;
}

static int test_bad_marker(void) {
    TEST(test_bad_marker);
    uint8_t buf[19];
    memset(buf, 0xAA, BGP_MARKER_LEN); // bad marker
    uint16_t len = htons(19);
    memcpy(buf + 16, &len, 2);
    buf[18] = BGP_MSG_KEEPALIVE;
    uint16_t out_len; uint8_t out_type;
    int rc = bgp_msg_parse_header(buf, 19, &out_len, &out_type);
    if (rc != BGP_ERR_HDR_SYNC) FAIL("expected marker sync error");
    PASS();
    return 0;
}

static int test_prefix_encode_decode(void) {
    TEST(test_prefix_encode_decode);
    // 192.168.1.0/24
    uint8_t nlri[] = { 24, 192, 168, 1 };
    bgp_prefix4_t out[1];
    int n = 0; // use internal nlri parser via parse_nlri (test indirectly via parse_update)
    // Direct test: build minimal UPDATE with just NLRI
    // Header + 2 (withdrawn len=0) + 2 (attr len=0) + NLRI
    uint8_t update_buf[30];
    uint16_t z = 0;
    memcpy(update_buf, &z, 2); // withdrawn len
    memcpy(update_buf + 2, &z, 2); // attr len
    memcpy(update_buf + 4, nlri, 4); // NLRI

    bgp_prefix4_t *withdrawn = NULL, *nlri_out = NULL;
    uint16_t n_wd = 0, n_nlri = 0;
    bgp_path_attrs_t attrs = {0};
    int rc = bgp_msg_parse_update(update_buf, 8, &withdrawn, &n_wd, &attrs, &nlri_out, &n_nlri);
    if (rc != 0)                   FAIL("parse_update failed");
    if (n_nlri != 1)               FAIL("wrong nlri count");
    if (nlri_out[0].length != 24)  FAIL("wrong prefix length");
    struct in_addr expected;
    inet_aton("192.168.1.0", &expected);
    if (nlri_out[0].prefix.s_addr != expected.s_addr) FAIL("wrong prefix address");
    free(withdrawn); free(nlri_out);
    (void)n;
    PASS();
    return 0;
}

static int test_as_path_contains(void) {
    TEST(test_as_path_contains);
    bgp_as_seg_t seg = {
        .type = BGP_AS_SEQUENCE,
        .count = 3,
        .asns = (uint32_t[]){64512, 65001, 65002},
        .next = NULL,
    };
    if (!bgp_as_path_contains(&seg, 65001)) FAIL("should contain 65001");
    if ( bgp_as_path_contains(&seg, 65003)) FAIL("should not contain 65003");
    PASS();
    return 0;
}

static int test_as_path_length(void) {
    TEST(test_as_path_length);
    bgp_as_seg_t set = {
        .type = BGP_AS_SET,
        .count = 3,
        .asns = (uint32_t[]){65002, 65003, 65004},
        .next = NULL,
    };
    bgp_as_seg_t seq = {
        .type = BGP_AS_SEQUENCE,
        .count = 2,
        .asns = (uint32_t[]){64512, 65001},
        .next = &set,
    };
    int len = bgp_as_path_length(&seq);
    if (len != 3) FAIL("expected length 3 (2 seq + 1 set)");
    PASS();
    return 0;
}

int main(void) {
    printf("BGP Message Parsing Tests\n");
    printf("=========================\n");
    int failures = 0;
    failures += test_keepalive_parse();
    failures += test_bad_marker();
    failures += test_prefix_encode_decode();
    failures += test_as_path_contains();
    failures += test_as_path_length();
    printf("\n%s: %d test(s) failed\n",
           failures ? "FAIL" : "PASS", failures);
    return failures ? 1 : 0;
}
```

### 19.3 Integration Testing with GoBGP/FRR

For integration testing against real BGP daemons:

```bash
# Set up a network namespace pair
ip netns add ns1
ip netns add ns2
ip link add veth1 type veth peer name veth2
ip link set veth1 netns ns1
ip link set veth2 netns ns2
ip netns exec ns1 ip addr add 10.0.0.1/30 dev veth1
ip netns exec ns2 ip addr add 10.0.0.2/30 dev veth2
ip netns exec ns1 ip link set veth1 up
ip netns exec ns2 ip link set veth2 up

# Run GoBGP in ns1
ip netns exec ns1 gobgpd -f gobgp-ns1.toml &

# Run our implementation in ns2
ip netns exec ns2 ./bgpd --local-as 65002 --peer 10.0.0.1 --peer-as 65001

# Verify session establishment and route exchange
ip netns exec ns1 gobgp neighbor
ip netns exec ns1 gobgp global rib
```

**GoBGP config for testing:**
```toml
# File: gobgp-ns1.toml
[global.config]
  as = 65001
  router-id = "10.0.0.1"

[[neighbors]]
  [neighbors.config]
    neighbor-address = "10.0.0.2"
    peer-as = 65002
  [neighbors.timers.config]
    hold-time = 90
    keepalive-interval = 30
```

---

## 20. Production Security Checklist

### BGP Session Security
- [ ] TCP-AO or TCP MD5 password configured on all eBGP sessions
- [ ] GTSM (TTL Security) enabled for eBGP single-hop sessions (`ttl-security hops 1`)
- [ ] eBGP multihop only where strictly necessary (use loopbacks for stability, not convenience)
- [ ] Session authentication keys rotated periodically and stored in secrets management system
- [ ] All BGP session events logged (state changes, NOTIFICATION reasons)
- [ ] Alert on hold timer expiry events (may indicate attack or misconfiguration)

### Route Security
- [ ] RPKI validation enabled, Invalid routes rejected
- [ ] ROAs created for all originated prefixes with appropriate max-length
- [ ] IRR objects (route:, aut-num:) created and maintained
- [ ] Import filters: prefix-lists and AS-path filters for all eBGP peers
  - Reject: bogon prefixes, too-specific (/25+ from customers), too-short prefix len
  - Reject: bogon ASNs in AS_PATH (0, 23456, 64496-64511, 65535, 4294967295)
  - Reject: AS_PATH > configurable max length (DoS protection)
  - Reject: private address space from internet peers
- [ ] Export filters: only announce your own prefixes and customer prefixes to providers
- [ ] Never announce full table to a customer (send only default or customer's own routes back)
- [ ] Maximum prefix limits on all peers with alert threshold and automatic session drop

### Prefix Validation
- [ ] Bogon prefix list (RFC 5735, RFC 6890) maintained and applied
  ```
  0.0.0.0/8+, 10.0.0.0/8+, 100.64.0.0/10+, 127.0.0.0/8+, 169.254.0.0/16+
  172.16.0.0/12+, 192.0.0.0/24+, 192.0.2.0/24+, 192.168.0.0/16+
  198.18.0.0/15+, 198.51.100.0/24+, 203.0.113.0/24+, 240.0.0.0/4+
  ```
- [ ] Reject your own prefixes received from peers (return routes — filtering error)
- [ ] Reject prefixes with prefix length outside allowed range (e.g., < /8 or > /24 for IPv4)

### Operational Security
- [ ] BGP looking glass restricted (rate-limited, authenticated if needed)
- [ ] BGP process isolated (container/VM, minimal privileges)
- [ ] BGP configuration change auditing (git-backed, peer-reviewed)
- [ ] Route monitoring (BGPmon, RIPE stat alerts for your prefixes)
- [ ] Graceful shutdown procedure documented for planned maintenance
- [ ] MANRS compliance verified (filtering + anti-spoofing + coordination)
- [ ] FlowSpec rules tested in monitoring mode before enforcement
- [ ] Blackhole community configured for DDoS response capability

---

## 21. Further Reading

### RFCs (Foundational)
- **RFC 4271** — BGP-4: The authoritative BGP specification. Read this completely.
- **RFC 4760** — Multiprotocol Extensions for BGP-4
- **RFC 1997** — BGP Communities Attribute
- **RFC 4360** — BGP Extended Communities Attribute
- **RFC 8092** — BGP Large Communities
- **RFC 4456** — BGP Route Reflection
- **RFC 5065** — Confederations
- **RFC 6793** — BGP Support